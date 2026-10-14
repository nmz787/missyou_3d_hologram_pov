"""Device networking recovered from the shipped 5D-Holo APK.

Legacy commands are ASCII, file names are raw GBK, and upload uses 1440-byte
blocks. Modern HTTP file names are hex-encoded GBK. Successful local writes do
not establish physical playback. See docs/android-protocol.md for evidence.
"""
from __future__ import annotations

import http.client
from http.cookies import SimpleCookie
import io
import math
import os
from pathlib import Path
import re
import select
import socket
import struct
import subprocess
import time
from typing import Callable
from urllib.parse import urlencode


class DeviceError(RuntimeError):
    """A device operation could not be completed or verified."""


class DeviceConnectionError(DeviceError):
    """The selected transport is unavailable or disconnected."""


class DeviceProtocolError(DeviceError):
    """The response does not satisfy the recovered protocol."""


class UnsupportedOperation(DeviceError):
    """No request for this operation is established by APK evidence."""


HEARTBEAT = b"c31c38abca4a8c2e3"
NOTIFY_HEADER = b"c30c38"
TAIL = b"a4a8c2e3"
UPLOAD_BLOCK = 1440
COMMANDS = {
    "next": b"c31c32abca4a8c2e3", "previous": b"c31c33abca4a8c2e3",
    "pause": b"c31c34abca4a8c2e3", "resume": b"c31c35abca4a8c2e3",
    "loop_all": b"c31c36abca4a8c2e3", "loop_one": b"c31c37abca4a8c2e3",
    "power_on": b"c31c45abca4a8c2e3", "power_off": b"c31c89abca4a8c2e3",
    "ble_on": b"c31c44abca4a8c2e3", "ble_off": b"c31c43abca4a8c2e3",
    "format": b"c31c88abca4a8c2e3",
}
MODELS = {"1": "F1", "2": "F2", "Z": "F5", "4": "F-MINI18", "7": "F-MINI11"}
MAX_REPLY = 16 * 1024 * 1024


def _display_name(name: str) -> str:
    match = re.fullmatch(r"(.{2})[-_](.*)\.bin", name)
    return f"{match[1]}.{match[2]}" if match else name[:-4] if name.endswith(".bin") else name


def _parse_notification(packet: bytes) -> dict:
    """Decode one accumulated frame, recovering only structurally anchored rows.

    Actual firmware can advertise a corrupt row length overlapping later rows.
    Resynchronization requires LEN2 INDEX2 INDEX2 '.' filename metadata;
    all such recovery remains incomplete and carries a warning.
    """
    if not packet.startswith(NOTIFY_HEADER) or not packet.endswith(TAIL) or len(packet) < 17:
        raise DeviceProtocolError("Invalid legacy notification framing")
    body = packet[:-len(TAIL)]
    issues: list[str] = []
    status_match = None
    records_end = len(body)
    raw_tail = ""
    for count in (6, 5):
        if len(body) >= 9 + count:
            candidate = body[-count:].decode("ascii", errors="replace")
            match = re.fullmatch(r"(\d{2})(.{1,2})(1[01])", candidate)
            if match:
                status_match, records_end, raw_tail = match, len(body) - count, candidate
                break
    if status_match is None:
        # Retain the unrecognized suffix, without claiming a complete directory.
        records_end = max(9, len(body) - 5)
        raw_tail = body[records_end:].decode("utf-8", errors="replace")
        issues.append("Unrecognized legacy status tail")

    def row_at(offset: int, strong: bool = False):
        if offset + 7 > records_end:
            return None
        length_b, index_b = body[offset:offset+2], body[offset+2:offset+4]
        if not length_b.isdigit() or not index_b.isdigit():
            return None
        length, index = int(length_b), int(index_b)
        end = offset + length + 2
        metadata = body[offset+4:offset+7]
        if length < 6 or end > records_end:
            return None
        if strong and metadata != index_b + b".":
            return None
        name_bytes = body[offset+7:end]
        try:
            name = name_bytes.decode("gbk")
        except UnicodeDecodeError:
            return None
        if not name or "\x00" in name or any(ord(c) < 32 for c in name):
            return None
        return end, {"index": index, "name": name, "displayName": _display_name(name)}

    def recover_after(offset: int):
        for position in range(offset, records_end):
            row = row_at(position, strong=True)
            if row:
                end, _ = row
                # A recovered row must terminate at another plausible row or tail.
                if end == records_end or row_at(end, strong=True):
                    return position
        return None

    files, offset = [], 9
    recovered = False
    while offset < records_end:
        row = row_at(offset)
        if row:
            end, item = row
            overlap = None
            # Detect a corrupt length swallowing the beginning of the next row.
            for position in range(offset + 7, end):
                other = row_at(position, strong=True)
                if other and other[0] > end and (other[0] == records_end or row_at(other[0], strong=True)):
                    overlap = position
                    break
            if overlap is None:
                if recovered:
                    item["recovered"] = True
                files.append(item)
                offset = end
                continue
            issues.append(f"Record at byte {offset} overlaps a later record; discarded")
            offset, recovered = overlap, True
            continue
        new_offset = recover_after(offset + 1)
        issues.append(f"Malformed record at byte {offset}" + (f"; resumed at {new_offset}" if new_offset is not None else ""))
        if new_offset is None:
            break
        offset, recovered = new_offset, True
    indices = [item["index"] for item in files]
    if len(set(indices)) != len(indices):
        issues.append("Duplicate file indices in notification")
    flag = status_match[2] if status_match else None
    lookup = flag[-1] if flag else None
    current = int(status_match[1]) if status_match else None
    return {
        "protocol": "legacy", "files": files, "complete": not issues,
        "issues": issues, "current_index": current,
        "current": next((f["name"] for f in files if f["index"] == current), None),
        "model": MODELS.get(lookup), "model_flag": flag,
        "model_recognized": lookup in MODELS if lookup else False,
        "is_playing": status_match[3] == "11" if status_match else None,
        "raw_tail": raw_tail, "raw_frame_hex": packet.hex(),
    }


class _Framer:
    def __init__(self):
        self.buffer = bytearray()

    def feed(self, chunk: bytes) -> list[bytes]:
        self.buffer.extend(chunk)
        frames = []
        while True:
            start = self.buffer.find(NOTIFY_HEADER)
            if start < 0:
                # Retain a possibly split header, dropping unrelated traffic.
                self.buffer[:] = self.buffer[-(len(NOTIFY_HEADER)-1):]
                break
            if start:
                del self.buffer[:start]
            end = self.buffer.find(TAIL, 9)
            if end < 0:
                break
            end += len(TAIL)
            frames.append(bytes(self.buffer[:end]))
            del self.buffer[:end]
        if len(self.buffer) > MAX_REPLY:
            raise DeviceProtocolError("Legacy response exceeded the receive limit")
        return frames


class _Stream:
    """Socket or binary, non-PTY adb shell nc stream, with bounded I/O."""
    def __init__(self, host: str, port: int, timeout: float, adb_serial: str | None):
        self.timeout, self.socket, self.process = timeout, None, None
        try:
            if adb_serial is None:
                self.socket = socket.create_connection((host, port), timeout=timeout)
                self.socket.settimeout(timeout)
            else:
                # exec-out does not forward stdin on the user's tested adb build.
                # -T avoids PTY byte translations; no shell text is interpolated.
                duration = str(max(1, math.ceil(timeout)))
                self.process = subprocess.Popen(
                    ["adb", "-s", adb_serial, "shell", "-T", "exec", "toybox", "nc",
                     "-w", duration, "-W", duration, host, str(port)],
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    bufsize=0,
                )
                os.set_blocking(self.process.stdin.fileno(), False)
                os.set_blocking(self.process.stdout.fileno(), False)
        except (OSError, subprocess.SubprocessError) as exc:
            self.close()
            raise DeviceConnectionError(f"Cannot connect to {host}:{port}: {exc}") from exc

    def _ended(self) -> str:
        if self.process and self.process.poll() is not None:
            detail = self.process.stderr.read(4096).decode(errors="replace").strip()
            return detail or f"adb nc exited with status {self.process.returncode}"
        return "Device closed the connection"

    def readable(self, timeout: float = 0) -> bool:
        source = self.socket if self.socket else self.process.stdout
        try:
            return bool(select.select([source], [], [], max(0, timeout))[0])
        except (OSError, ValueError) as exc:
            raise DeviceConnectionError(str(exc)) from exc

    def recv(self, count: int, timeout: float | None = None) -> bytes:
        timeout = self.timeout if timeout is None else timeout
        try:
            if self.socket:
                self.socket.settimeout(max(0.001, timeout))
                return self.socket.recv(count)
            if not self.readable(timeout):
                raise DeviceConnectionError("Timed out waiting for device response over adb")
            return os.read(self.process.stdout.fileno(), count)
        except socket.timeout as exc:
            raise DeviceConnectionError("Timed out waiting for device response") from exc
        except OSError as exc:
            raise DeviceConnectionError(self._ended() + f": {exc}") from exc

    def sendall(self, data: bytes):
        deadline, offset = time.monotonic() + self.timeout, 0
        try:
            if self.socket:
                self.socket.settimeout(self.timeout)
                self.socket.sendall(data)
                return
            pipe = self.process.stdin
            while offset < len(data):
                remaining = deadline - time.monotonic()
                if remaining <= 0 or not select.select([], [pipe], [], max(0, remaining))[1]:
                    raise DeviceConnectionError("Timed out writing device data over adb")
                try:
                    written = os.write(pipe.fileno(), memoryview(data)[offset:])
                except BlockingIOError:
                    continue
                if written <= 0:
                    raise DeviceConnectionError(self._ended())
                offset += written
        except (OSError, socket.timeout) as exc:
            raise DeviceConnectionError(self._ended() + f": {exc}") from exc

    def _drain_upload(self, quiet=1.0):
        output = bytearray()
        deadline = time.monotonic() + math.ceil(self.timeout) + 2
        quiet_deadline = time.monotonic() + quiet
        peer_closed = False
        while time.monotonic() < min(deadline, quiet_deadline):
            remaining = min(deadline, quiet_deadline) - time.monotonic()
            if not self.readable(max(0, remaining)):
                break
            chunk = self.recv(65536, max(0.001, deadline - time.monotonic()))
            if not chunk:
                peer_closed = True
                break
            output.extend(chunk)
            if len(output) > MAX_REPLY:
                raise DeviceProtocolError("Unexpectedly large upload completion response")
            quiet_deadline = time.monotonic() + quiet
        return output, peer_closed

    def finish_upload(self):
        """Drain completion traffic before half-closing or stopping the relay.

        Unread incoming data can turn a TCP close into a reset. For ADB, a local
        pipe write also does not establish that nc consumed the final marker.
        There is no recovered acknowledgment for the completion marker itself.
        """
        output, peer_closed = self._drain_upload()
        if self.socket:
            write_eof_sent = not peer_closed
            if not peer_closed:
                try:
                    self.socket.shutdown(socket.SHUT_WR)
                except OSError as exc:
                    raise DeviceConnectionError(f"Could not finish upload writes: {exc}") from exc
                remaining, peer_closed = self._drain_upload(quiet=0.2)
                output.extend(remaining)
            return {"write_eof_sent": write_eof_sent, "transport": "socket", "peer_closed": peer_closed,
                    "drained_bytes": len(output), "completion_response_hex": output.hex(),
                    "completion_acknowledged": False}
        process = self.process
        process.stdin.close()
        deadline = time.monotonic() + math.ceil(self.timeout) + 2
        while time.monotonic() < deadline:
            if self.readable(min(0.1, max(0, deadline - time.monotonic()))):
                chunk = os.read(process.stdout.fileno(), 4096)
                if not chunk:
                    try:
                        process.wait(timeout=max(0.01, deadline - time.monotonic()))
                    except subprocess.TimeoutExpired:
                        raise DeviceConnectionError("ADB upload relay did not exit after write EOF; delivery is uncertain")
                    break
                output.extend(chunk)
                if len(output) > MAX_REPLY:
                    raise DeviceProtocolError("Unexpectedly large completion response")
            elif process.poll() is not None:
                break
        if process.poll() is None:
            raise DeviceConnectionError("ADB upload relay did not finish gracefully; completion delivery is uncertain")
        if process.returncode != 0:
            raise DeviceConnectionError("ADB upload relay failed after completion: " + self._ended())
        return {"write_eof_sent": True, "transport": "adb-shell", "relay_exit_code": process.returncode,
                "drained_bytes": len(output), "completion_response_hex": output.hex(),
                "completion_acknowledged": False}

    def close(self):
        if self.socket:
            self.socket.close()
            self.socket = None
        if self.process:
            process, self.process = self.process, None
            for pipe in (process.stdin, process.stdout):
                if pipe:
                    pipe.close()
            try:
                process.wait(timeout=0.5)
            except subprocess.TimeoutExpired:
                process.terminate()
                try:
                    process.wait(timeout=0.5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            if process.stderr:
                process.stderr.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class _ResponseReader(io.RawIOBase):
    def __init__(self, stream: _Stream):
        super().__init__()
        self.stream = stream

    def readable(self):
        return True

    def readinto(self, buffer):
        data = self.stream.recv(len(buffer))
        buffer[:len(data)] = data
        return len(data)


class _ResponseSocket:
    def __init__(self, stream: _Stream):
        self.stream = stream

    def makefile(self, mode):
        return io.BufferedReader(_ResponseReader(self.stream))


class DeviceClient:
    def __init__(self, host="192.168.4.1", protocol="auto", adb_serial=None, timeout=5,
                 *, control_port=5233, upload_port=5499, http_port=80):
        if not isinstance(host, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.-]*", host):
            raise ValueError("Host must be an IPv4 address or hostname")
        protocol = {"tcp": "legacy", "modern": "http"}.get(protocol, protocol)
        if protocol not in ("auto", "legacy", "http"):
            raise ValueError("Protocol must be auto, legacy, or http")
        if not math.isfinite(float(timeout)) or float(timeout) <= 0:
            raise ValueError("Timeout must be positive and finite")
        for port in (control_port, upload_port, http_port):
            if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
                raise ValueError("Ports must be integers between 1 and 65535")
        if adb_serial is not None and (not isinstance(adb_serial, str) or not adb_serial):
            raise ValueError("ADB serial must be a nonempty string")
        self.host, self.requested_protocol = host, protocol
        self.protocol, self.adb_serial, self.timeout = None, adb_serial, float(timeout)
        self.control_port, self.upload_port, self.http_port = control_port, upload_port, http_port
        self._control, self._framer, self._snapshot = None, _Framer(), None
        self._cookies, self._http_info, self._session = {}, None, False

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        if self._control:
            self._control.close()
        self._control, self.protocol, self._session = None, None, False
        self._framer = _Framer()

    def _stream(self, port):
        return _Stream(self.host, port, self.timeout, self.adb_serial)

    def connect(self):
        if self.protocol:
            return self
        http_error = None
        if self.requested_protocol in ("auto", "http"):
            try:
                info = self._http("GET", "/info")
                if type(info.get("code")) is not int or info["code"] not in (0, 1):
                    raise DeviceProtocolError("/info is not a recognized device response")
            except DeviceError as exc:
                http_error = exc
                if self.requested_protocol == "http":
                    raise
            else:
                self.protocol = "http"
                try:
                    self._http_result("GET", "/ctrl/session")
                    self._http_info = self._http_result("GET", "/info")
                    self._session = True
                except DeviceError:
                    self.protocol = None
                    raise
                return self
        try:
            self._control = self._stream(self.control_port)
            self.protocol = "legacy"
            self._legacy_snapshot()
            return self
        except DeviceError as exc:
            self.close()
            detail = f"HTTP: {http_error}; legacy: {exc}" if http_error else str(exc)
            raise DeviceConnectionError(f"No responding display at {self.host}: {detail}") from exc

    def _ensure(self):
        if self.protocol is None:
            self.connect()

    def _http(self, method, route, *, body=None, headers=None, chunks=None):
        import json
        if "\r" in route or "\n" in route:
            raise ValueError("Invalid HTTP route")
        extra = dict(headers or {})
        if body is not None:
            body = json.dumps(body).encode() if not isinstance(body, bytes) else body
            extra.setdefault("Content-Type", "application/json")
            extra["Content-Length"] = str(len(body))
        else:
            extra.setdefault("Content-Type", "application/json")
        extra.update({"Host": f"{self.host}:{self.http_port}", "Connection": "close"})
        if self._cookies:
            extra["Cookie"] = "; ".join(f"{k}={v}" for k, v in self._cookies.items())
        request = f"{method} {route} HTTP/1.1\r\n" + "".join(f"{k}: {v}\r\n" for k, v in extra.items()) + "\r\n"
        try:
            with self._stream(self.http_port) as stream:
                stream.sendall(request.encode("ascii"))
                if body:
                    stream.sendall(body)
                if chunks is not None:
                    for chunk in chunks:
                        stream.sendall(chunk)
                response = http.client.HTTPResponse(_ResponseSocket(stream))
                response.begin()
                for key, value in response.getheaders():
                    if key.lower() == "set-cookie":
                        cookie = SimpleCookie()
                        cookie.load(value)
                        self._cookies.update({k: morsel.value for k, morsel in cookie.items()})
                payload = response.read(MAX_REPLY + 1)
                code = response.status
                response.close()
            if len(payload) > MAX_REPLY:
                raise DeviceProtocolError("HTTP response exceeded the receive limit")
            if not 200 <= code < 300:
                raise DeviceProtocolError(f"Device returned HTTP {code}")
            result = json.loads(payload)
            if not isinstance(result, dict):
                raise DeviceProtocolError("Device HTTP reply must be a JSON object")
            return result
        except DeviceError:
            raise
        except (OSError, ValueError, http.client.HTTPException) as exc:
            raise DeviceProtocolError(f"Invalid or interrupted HTTP device response: {exc}") from exc

    def _http_result(self, method, route, **kwargs):
        result = self._http(method, route, **kwargs)
        if type(result.get("code")) is not int or result["code"] != 0:
            raise DeviceProtocolError(f"Device rejected {route}: {result}")
        return result

    def _legacy_snapshot(self):
        # The ADB nc process may expire while an upload uses its separate socket.
        # Retry only this read-only request, never an indexed/mutating command.
        for attempt in range(2):
            try:
                return self._read_legacy_snapshot()
            except DeviceConnectionError:
                if attempt:
                    raise
                if self._control:
                    self._control.close()
                self._control = self._stream(self.control_port)
                self._framer = _Framer()

    def _read_legacy_snapshot(self):
        self._control.sendall(HEARTBEAT)
        deadline, latest = time.monotonic() + self.timeout, None
        while time.monotonic() < deadline:
            chunk = self._control.recv(65536, max(0.001, deadline - time.monotonic()))
            if not chunk:
                raise DeviceConnectionError("Legacy control connection closed")
            for frame in self._framer.feed(chunk):
                latest = _parse_notification(frame)
            if latest is not None and not self._control.readable(min(0.03, max(0, deadline - time.monotonic()))):
                self._snapshot = latest
                return latest
        raise DeviceConnectionError("Timed out waiting for a complete legacy notification frame")

    def info(self):
        self._ensure()
        if self.protocol == "http":
            self._http_info = self._http_result("GET", "/info")
            return {**self._http_info, "protocol": "http", "host": self.host}
        return {**self._legacy_snapshot(), "host": self.host}

    def status(self):
        self._ensure()
        if self.protocol == "legacy":
            return self._legacy_snapshot()
        return {**self._http_result("GET", "/ctrl/play?action=status"), "protocol": "http"}

    def files(self):
        self._ensure()
        if self.protocol == "legacy":
            snapshot = self._legacy_snapshot()
            return {k: snapshot[k] for k in ("protocol", "files", "complete", "issues")}
        result = self._http_result("GET", "/DCIM")
        if not isinstance(result.get("files"), list):
            raise DeviceProtocolError("Device /DCIM reply lacks a filename array")
        files = []
        for index, encoded in enumerate(result["files"]):
            try:
                if not isinstance(encoded, str) or len(encoded) % 2 or not re.fullmatch(r"[0-9a-fA-F]*", encoded):
                    raise ValueError("Filename is not hexadecimal text")
                name = bytes.fromhex(encoded).decode("gbk")
            except (ValueError, UnicodeDecodeError) as exc:
                raise DeviceProtocolError(f"Invalid filename at /DCIM index {index}: {exc}") from exc
            files.append({"index": index, "name": name, "displayName": _display_name(name)})
        return {"protocol": "http", "files": files, "complete": True, "issues": []}

    def settings(self):
        self._ensure()
        if self.protocol == "legacy":
            return {"ble": None, "switcher": None, "loop": None}
        data = self._http_result("GET", "/ctrl/get?k=all").get("data")
        if isinstance(data, dict):
            return {k: v.get("value") if isinstance(v, dict) and "value" in v else v for k, v in data.items()}
        if isinstance(data, list) and all(isinstance(v, dict) and "key" in v for v in data):
            return {str(v["key"]): v.get("value") for v in data}
        raise DeviceProtocolError("Device settings reply has no supported configuration data")

    def _legacy_command(self, operation, packet, expected=None):
        self._control.sendall(packet)
        result = {"protocol": "legacy", "operation": operation, "sent": True, "acknowledged": False}
        try:
            # Keep a subsequent heartbeat out of the command's write burst.
            # The tested firmware ignored controls followed immediately by it.
            time.sleep(min(0.75, self.timeout))
            result["status"] = self._legacy_snapshot()
            if expected is not None:
                # The tested firmware applies controls asynchronously. An
                # immediate heartbeat often returns the previous state.
                deadline = time.monotonic() + min(2, self.timeout)
                while not expected(result["status"]) and time.monotonic() < deadline:
                    time.sleep(0.15)
                    result["status"] = self._legacy_snapshot()
                result["requested_state_observed"] = bool(expected(result["status"]))
        except DeviceError as exc:
            result["status_error"] = str(exc)
        return result

    def set_setting(self, key, value):
        self._ensure()
        if not isinstance(key, str) or not key:
            raise ValueError("Setting key must be a nonempty string")
        if self.protocol == "http":
            if isinstance(value, bool):
                if key in ("ble", "switcher"):
                    wire_value = "on" if value else "off"
                elif key == "loop":
                    wire_value = "all" if value else "one"
                else:
                    wire_value = "true" if value else "false"
            else:
                wire_value = str(value)
            result = self._http_result("GET", "/ctrl/set?" + urlencode({key: wire_value}))
            return {**result, "protocol": "http", "key": key, "requested_value": value}
        if key not in ("ble", "switcher", "loop"):
            raise UnsupportedOperation(f"Legacy protocol has no recovered setting command for {key!r}")
        if key == "loop":
            if value not in ("all", "one"):
                raise ValueError("Loop value must be all or one")
            return self.loop(value == "all")
        if value not in ("on", "off", True, False):
            raise ValueError(f"{key} value must be on or off")
        on = value in ("on", True)
        if key == "switcher":
            return self.power(on)
        return self._legacy_command("set_ble", COMMANDS["ble_on" if on else "ble_off"])

    def _target(self, target):
        if isinstance(target, bool) or not isinstance(target, (str, int)):
            raise ValueError("Target must be a filename or a device index")
        if isinstance(target, int) and self.protocol == "legacy":
            if not 0 <= target <= 99:
                raise ValueError("Legacy device index must be between 0 and 99")
            return {"index": target, "name": None}
        listing = self.files()
        matches = [f for f in listing["files"] if f["index"] == target] if isinstance(target, int) else [f for f in listing["files"] if f["name"].casefold() == target.casefold()]
        if len(matches) != 1:
            raise DeviceError(f"Target {target!r} is not uniquely present in the device's returned list")
        return matches[0]

    def play(self, target):
        self._ensure()
        item = self._target(target)
        if self.protocol == "http":
            return {**self._http_result("GET", f"/DCIM/{item['name'].encode('gbk').hex()}?act=play"), "protocol": "http"}
        # APK resumes first if its last status says playback is paused.
        if self._snapshot and self._snapshot["is_playing"] is False:
            self._control.sendall(COMMANDS["resume"])
            time.sleep(min(0.25, self.timeout))
        return self._legacy_command("play", f"c31c40abe{item['index']:02d}a4a8c2e3".encode(),
                                    lambda s: s["current_index"] == item["index"] and s["is_playing"] is True)

    def delete(self, target):
        self._ensure()
        item = self._target(target)
        if self.protocol == "http":
            return {**self._http_result("GET", f"/DCIM/{item['name'].encode('gbk').hex()}?act=rm"), "protocol": "http"}
        return self._legacy_command("delete", f"c31c39abe{item['index']:02d}a4a8c2e3".encode(),
                                    lambda s: s["complete"] and not any(f["index"] == item["index"] for f in s["files"]))

    def pause(self):
        self._ensure()
        if self.protocol == "http":
            return {**self._http_result("GET", "/ctrl/play?action=pause"), "protocol": "http"}
        return self._legacy_command("pause", COMMANDS["pause"], lambda s: s["is_playing"] is False)

    def resume(self):
        self._ensure()
        if self.protocol == "http":
            raise UnsupportedOperation("No modern HTTP resume endpoint is established by the APK")
        return self._legacy_command("resume", COMMANDS["resume"], lambda s: s["is_playing"] is True)

    def next(self):
        self._ensure()
        if self.protocol == "http":
            raise UnsupportedOperation("No modern HTTP next endpoint is established by the APK")
        return self._legacy_command("next", COMMANDS["next"])

    def previous(self):
        self._ensure()
        if self.protocol == "http":
            return {**self._http_result("GET", "/ctrl/play?action=previous"), "protocol": "http"}
        return self._legacy_command("previous", COMMANDS["previous"])

    def power(self, on):
        self._ensure()
        if not isinstance(on, bool):
            raise ValueError("Power requires a boolean")
        if self.protocol == "http":
            return self.set_setting("switcher", "on" if on else "off")
        return self._legacy_command("power_on" if on else "power_off", COMMANDS["power_on" if on else "power_off"])

    def loop(self, all):
        self._ensure()
        if not isinstance(all, bool):
            raise ValueError("Loop mode requires a boolean")
        if self.protocol == "http":
            return self.set_setting("loop", "all" if all else "one")
        return self._legacy_command("loop_all" if all else "loop_one", COMMANDS["loop_all" if all else "loop_one"])

    def format_card(self):
        self._ensure()
        if self.protocol == "http":
            return {**self._http_result("GET", "/ctrl/card?action=format"), "protocol": "http"}
        result = self._legacy_command("format", COMMANDS["format"])
        deadline = time.monotonic() + max(5, self.timeout)
        while time.monotonic() < deadline:
            status = result.get("status", {})
            if status.get("complete") and not status.get("files"):
                result["directory_empty_observed"] = True
                return result
            time.sleep(0.5)
            try:
                result["status"] = self._legacy_snapshot()
            except DeviceError as exc:
                result["status_error"] = str(exc)
                break
        result["directory_empty_observed"] = False
        return result

    def _upload_ack(self, stream, prefix):
        buffer = getattr(stream, "_ack_buffer", None)
        if buffer is None:
            buffer = stream._ack_buffer = bytearray()
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            end = buffer.find(TAIL)
            if end >= 0:
                end += len(TAIL)
                frame = bytes(buffer[:end])
                del buffer[:end]
                if len(frame) < 14 or not frame.startswith(prefix):
                    raise DeviceProtocolError(f"Unexpected upload acknowledgment: {frame.hex()}")
                middle = frame[6:-8]
                status = middle[3:].decode("ascii", errors="replace") if len(middle) == 7 and middle.startswith(b"DEJ") else None
                if status == "0000":
                    raise DeviceProtocolError(f"Unconfirmed upload status 0000: {frame.decode('ascii', errors='replace')}. Live transfers with this status did not persist; transfer aborted. The firmware meaning of this field is unknown.")
                return {"prefix": prefix.decode(), "status": status, "raw_hex": frame.hex()}
            chunk = stream.recv(4096, max(0.001, deadline - time.monotonic()))
            if not chunk:
                raise DeviceConnectionError("Upload connection closed before acknowledgment")
            buffer.extend(chunk)
            if len(buffer) > MAX_REPLY:
                raise DeviceProtocolError("Upload acknowledgment exceeded the receive limit")
        raise DeviceConnectionError("Timed out waiting for upload acknowledgment")

    @staticmethod
    def _ambiguous_alias(name, existing):
        base, _, extension = name.rpartition(".")
        if not base:
            base, extension = name, ""
        if len(base) <= 8 and len(extension) <= 3 and re.fullmatch(r"[A-Za-z0-9_-]+", base):
            return False
        alias_base, _, alias_extension = existing.rpartition(".")
        match = re.fullmatch(r"(.+)~\d+", alias_base)
        cleaned = re.sub(r"[ .]", "", base).upper()
        return bool(match and extension[:3].casefold() == alias_extension.casefold() and cleaned.startswith(match[1].upper()))

    def upload(self, path, name=None, overwrite=False, progress: Callable[[int], None] | None = None):
        self._ensure()
        path = Path(path)
        if not path.is_file():
            raise ValueError(f"Upload source is not a regular file: {path}")
        name = path.name if name is None else name
        if not isinstance(name, str) or not name or name in (".", "..") or any(c in name for c in ("/", "\\")) or any(ord(c) < 32 or ord(c) == 127 for c in name):
            raise ValueError("Upload name must be a filename without path separators/control bytes")
        try:
            encoded = name.encode("gbk")
        except UnicodeEncodeError as exc:
            raise ValueError("The device filename cannot be represented in GBK") from exc
        if self.protocol == "legacy" and len(encoded) > 194:
            raise ValueError("Legacy name exceeds 194 GBK bytes; this client avoids wrapping the recovered biased one-byte field, whose firmware limit is unknown")
        size = path.stat().st_size
        if size <= 0:
            raise ValueError("Cannot upload an empty file")
        blocks = (size + UPLOAD_BLOCK - 1) // UPLOAD_BLOCK
        padded = blocks * UPLOAD_BLOCK
        if self.protocol == "legacy" and padded > 0xffffffff:
            raise ValueError("Upload exceeds the legacy protocol's 32-bit padded size field")
        before = self.files()
        if not before["complete"] and not overwrite:
            raise DeviceError("Device returned an incomplete file list; overwrite cannot be ruled out. Use an explicit overwrite authorization or repair the directory.")
        collisions = [f for f in before["files"] if f["name"].casefold() == name.casefold()]
        ambiguous = [f for f in before["files"] if self._ambiguous_alias(name, f["name"])]
        if collisions and not overwrite:
            raise FileExistsError(f"Device already contains {name!r}; use overwrite explicitly")
        if ambiguous and not overwrite:
            raise DeviceError("A returned FAT short alias could represent this filename; choose an ASCII 8.3 name or authorize overwrite explicitly")
        if progress:
            progress(0)
        if self.protocol == "legacy":
            with self._stream(self.upload_port) as stream, path.open("rb") as source:
                info = b"d31d66DF" + bytes([(len(encoded) + 61) & 255]) + struct.pack(">I", padded) + encoded + TAIL
                stream.sendall(info)
                info_ack = self._upload_ack(stream, b"d30d66")
                data_acks = []
                for number in range(1, blocks + 1):
                    payload = source.read(UPLOAD_BLOCK)
                    expected = min(UPLOAD_BLOCK, size - (number - 1) * UPLOAD_BLOCK)
                    if len(payload) != expected:
                        raise DeviceError("Upload source changed or could not be read completely")
                    stream.sendall(b"d31d88JMP" + payload.ljust(UPLOAD_BLOCK, b"\x00") + b"000" + TAIL)
                    if number % 20 == 0 or number == blocks:
                        data_acks.append(self._upload_ack(stream, b"d30d88"))
                    if progress:
                        progress(min(99, int(number / blocks * 100)))
                if source.read(1):
                    raise DeviceError("Upload source grew during transfer")
                stream.sendall(b"d31d88DEF" + TAIL)
                completion = stream.finish_upload()
                pending = bytes(getattr(stream, "_ack_buffer", b"")) + bytes.fromhex(completion.get("completion_response_hex", ""))
                if b"d30d88DEJ0000" in pending or b"d30d66DEJ0000" in pending:
                    raise DeviceProtocolError("Unconfirmed upload status 0000 during completion; live transfers with this status did not persist")
                completion["buffered_ack_bytes"] = len(getattr(stream, "_ack_buffer", b""))
        else:
            boundary = "povbin-" + os.urandom(16).hex()
            hex_name = encoded.hex()
            prefix = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"name\"\r\n\r\n{hex_name}\r\n"
                      f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{hex_name}\"\r\n"
                      "Content-Type: application/octet-stream\r\n\r\n").encode("ascii")
            suffix = f"\r\n--{boundary}--\r\n".encode("ascii")
            def chunks():
                yield prefix
                sent = 0
                with path.open("rb") as source:
                    while sent < size:
                        part = source.read(min(65536, size - sent))
                        if not part:
                            raise DeviceError("Upload source changed during transfer")
                        sent += len(part)
                        yield part
                        if progress:
                            progress(min(99, int(sent / size * 100)))
                    if source.read(1):
                        raise DeviceError("Upload source grew during transfer")
                yield suffix
            self._http_result("POST", "/DCIM/upload", chunks=chunks(), headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Content-Length": str(len(prefix) + size + len(suffix)),
                "Cache-Control": "no-cache", "Pragma": "no-cache", "Expires": "0",
            })
        if progress:
            progress(100)
        result = {"protocol": self.protocol, "name": name, "bytes": size, "transferred": True,
                  "verified": False, "overwrite_authorized": bool(overwrite),
                  "before_count": len(before["files"]), "before_complete": before["complete"]}
        if self.protocol == "legacy":
            statuses = {}
            for ack in data_acks:
                key = ack["status"] or "unspecified"
                statuses[key] = statuses.get(key, 0) + 1
            result.update({"padded_bytes": padded, "blocks": blocks, "completion": completion,
                           "ack_mode": "native-batch", "acknowledgments": {"info": info_ack, "data_count": len(data_acks), "data_statuses": statuses},
                           "ack_sequence_correlated": False})
        checks, stable, consecutive, first_seen = [], False, 0, None
        started = time.monotonic()
        latest_matches = []
        for attempt in range(5):
            if attempt:
                time.sleep(0.5)
            try:
                after = self.files()
                latest_matches = [f for f in after["files"] if f["name"].casefold() == name.casefold()]
                elapsed = time.monotonic() - started
                checks.append({"seconds": round(elapsed, 3), "name_listed": bool(latest_matches),
                               "count": len(after["files"]), "complete": after["complete"]})
                result.update({"after_count": len(after["files"]), "after_complete": after["complete"], "issues": after["issues"]})
                if latest_matches:
                    if consecutive == 0:
                        first_seen = elapsed
                    consecutive += 1
                    if consecutive >= 3 and elapsed - first_seen >= 1:
                        stable = True
                        break
                else:
                    consecutive, first_seen = 0, None
            except DeviceError as exc:
                checks.append({"seconds": round(time.monotonic() - started, 3), "error": str(exc)})
                result["verification_error"] = str(exc)
                latest_matches, consecutive, first_seen = [], 0, None
        result["verification_checks"] = checks
        result["listing_stable"] = stable
        result["name_listed"] = bool(latest_matches)
        # A directory entry alone did not prove persistence on the tested unit.
        result["verified"] = False
        result["verification"] = (
            "filename_listed_in_repeated_responses_content_unverified" if stable and not collisions else
            "existing_filename_stable_content_unverified" if stable else
            "filename_listing_not_stable" if any(c.get("name_listed") for c in checks) else
            "file_list_unavailable_after_transfer" if all("error" in c for c in checks) else
            "uploaded_filename_not_listed"
        )
        if latest_matches:
            result["file"] = latest_matches[0]
        result["content_verified"] = False
        result["persistence_verified"] = False
        result["playback_verified"] = False
        return result
