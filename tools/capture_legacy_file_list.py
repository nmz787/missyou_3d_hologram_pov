"""Capture the legacy app's read-only heartbeat/file-list responses.

Put the SD card back into the display and connect this computer to its Wi-Fi.
Uses the APK's declared 192.168.4.1:5233 endpoint and exact heartbeat bytes.
Preserves TCP receive chunk boundaries as well as the full stream, so a
later analysis can distinguish missing device entries from app parser losses.
No upload, deletion, formatting, or playback command is sent.
"""

import argparse
import json
import math
from pathlib import Path
import socket
import time

HOST = "192.168.4.1"
PORT = 5233
# APK Hermes function #9294 heartBeat; this asks for state/file-list notification.
HEARTBEAT = b"c31c38abca4a8c2e3"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("analysis/android/file-list-capture.json"))
    parser.add_argument("--duration", type=float, default=6)
    args = parser.parse_args()
    if not math.isfinite(args.duration) or not 0 < args.duration <= 60:
        parser.error("Duration must be between 0 and 60 seconds")
    if args.output.exists():
        parser.error("Capture output already exists; choose a new output path")
    chunks, sent = [], []
    began = time.monotonic()
    try:
        with socket.create_connection((HOST, PORT), timeout=3) as connection:
            connection.settimeout(0.2)
            next_heartbeat = 0.0
            while time.monotonic() - began < args.duration:
                elapsed = time.monotonic() - began
                if elapsed >= next_heartbeat:
                    connection.sendall(HEARTBEAT)
                    sent.append({"seconds": elapsed, "hex": HEARTBEAT.hex()})
                    next_heartbeat = elapsed + 1
                try:
                    data = connection.recv(65536)
                except socket.timeout:
                    continue
                if not data:
                    break
                chunks.append({"seconds": time.monotonic() - began, "bytes": len(data),
                               "hex": data.hex(), "ascii": data.decode("ascii", errors="replace")})
    except OSError as error:
        parser.exit(1, f"Capture failed: {error}\nConnect the computer to the display's Wi-Fi before retrying.\n")
    stream = b"".join(bytes.fromhex(chunk["hex"]) for chunk in chunks)
    record = {"authority": "live device responses to read-only legacy heartbeat",
              "endpoint": {"host": HOST, "port": PORT}, "sent": sent, "chunks": chunks,
              "stream_hex": stream.hex(), "bytes_received": len(stream),
              "limitations": ["Receive boundaries belong to this connection, not the Android connection",
                              "No conclusion about missing files is made by this capture tool"]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as output:
        json.dump(record, output, indent=2)
        output.write("\n")
    print(f"Captured {len(stream)} bytes in {len(chunks)} receive chunks: {args.output}")


if __name__ == "__main__":
    main()
