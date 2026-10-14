"""FFmpeg front end and streaming writer for the recovered offline format."""

from contextlib import contextmanager
import errno
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Callable

import numpy as np

from .codec import AUDIO_BYTES, AUDIO_RATE, FPS, TRAILER_BYTES, Encoder, PROFILES, make_header, parse_header


def _tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise ValueError(f"{name} is required; install FFmpeg and put it on PATH")
    return path


def probe_video(path: Path) -> dict:
    result = subprocess.run(
        [_tool("ffprobe"), "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        capture_output=True, text=True, check=False,
    )
    if result.returncode:
        raise ValueError(f"Cannot read video: {result.stderr.strip()}")
    info = json.loads(result.stdout)
    video = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"
                  and not s.get("disposition", {}).get("attached_pic")), None)
    if video is None:
        raise ValueError("Input has no video stream")
    return {"video_index": video["index"], "audio": any(s.get("codec_type") == "audio" for s in info["streams"]),
            "duration": float(info.get("format", {}).get("duration", video.get("duration", 0)) or 0)}


def _input_args(source: Path, start: float, duration: float | None) -> list[str]:
    args = ["-nostdin", "-hide_banner", "-loglevel", "error"]
    if start:
        args += ["-ss", str(start)]
    args += ["-i", str(source)]
    if duration is not None:
        args += ["-t", str(duration)]
    return args


@contextmanager
def _decode_frames(command: list[str], frame_bytes: int):
    # File-backed stderr cannot fill a pipe while Python reads raw frames.
    with tempfile.TemporaryFile() as errors:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=errors)
        try:
            def frames():
                assert process.stdout is not None
                while True:
                    data = bytearray()
                    while len(data) < frame_bytes:
                        chunk = process.stdout.read(frame_bytes - len(data))
                        if not chunk:
                            break
                        data.extend(chunk)
                    if not data:
                        break
                    if len(data) != frame_bytes:
                        raise ValueError("FFmpeg returned an incomplete video frame")
                    yield data
                if process.wait():
                    errors.seek(0)
                    raise ValueError("FFmpeg video conversion failed: " + errors.read().decode(errors="replace").strip())
            yield frames()
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            if process.stdout is not None:
                process.stdout.close()


def convert_video(source: str | Path, destination: str | Path, *, device_type: int,
                  size: int = 672, fit: str = "cover", start: float = 0,
                  duration: float | None = None, audio: bool = True,
                  flip_x: bool = False, flip_y: bool = False, overwrite: bool = False,
                  nonce: bytes | None = None, progress: Callable[[int], None] | None = None) -> dict:
    """Convert video at 20 fps, with 32 kHz U8 mono audio or legacy zero audio slots.

    Sampling/packing matches original byte-array methods; FFmpeg cropping replaces
    the original GUI/JPEG intermediate workflow. No device upload is performed.
    """
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if not source.is_file():
        raise ValueError(f"Input file does not exist: {source}")
    if source == destination:
        raise ValueError("Input and output must have different paths")
    if destination.exists() and not overwrite:
        raise ValueError(f"Output already exists: {destination}; use --overwrite to replace it")
    if device_type not in PROFILES:
        raise ValueError("Device type must be 1..11")
    if not np.isfinite(start) or start < 0 or (duration is not None and (not np.isfinite(duration) or duration <= 0)):
        raise ValueError("Start must be nonnegative and duration must be positive")
    if fit not in ("cover", "contain", "stretch"):
        raise ValueError("Fit must be cover, contain, or stretch")
    profile = PROFILES[device_type]
    encoder = Encoder(profile, size)
    info = probe_video(source)
    if info["duration"] and start >= info["duration"]:
        raise ValueError("Start is at or beyond the end of the video")
    base = _input_args(source, start, duration)
    if fit == "cover":
        resize = f"scale={size}:{size}:force_original_aspect_ratio=increase,crop={size}:{size}"
    elif fit == "contain":
        resize = f"scale={size}:{size}:force_original_aspect_ratio=decrease,pad={size}:{size}:(ow-iw)/2:(oh-ih)/2:black"
    else:
        resize = f"scale={size}:{size}"
    filters = [f"fps={FPS}", resize, "setsar=1"]
    if flip_x:
        filters.append("hflip")
    if flip_y:
        filters.append("vflip")
    video_command = [_tool("ffmpeg"), *base, "-map", f"0:{info['video_index']}", "-an",
                     "-vf", ",".join(filters), "-pix_fmt", "rgb24", "-f", "rawvideo", "pipe:1"]
    header = make_header(profile, nonce)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.TemporaryDirectory(prefix="povbin-") as work:
            audio_path = Path(work) / "audio.u8"
            has_audio = audio and info["audio"]
            if has_audio:
                result = subprocess.run([_tool("ffmpeg"), *base, "-map", "0:a:0", "-vn",
                                         "-ac", "1", "-ar", str(AUDIO_RATE), "-acodec", "pcm_u8",
                                         "-f", "u8", str(audio_path)], capture_output=True, check=False)
                if result.returncode:
                    raise ValueError("FFmpeg audio conversion failed: " + result.stderr.decode(errors="replace").strip())
            else:
                audio_path.write_bytes(b"")
            with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=".povbin-", delete=False) as output:
                temporary = Path(output.name)
                output.write(header)
                count = 0
                with audio_path.open("rb") as sound, _decode_frames(video_command, size * size * 3) as frames:
                    for frame in frames:
                        rgb = np.frombuffer(frame, dtype=np.uint8).reshape(size, size, 3)
                        output.write(encoder.encode(rgb))
                        samples = sound.read(AUDIO_BYTES) if has_audio else b""
                        # Real U8 audio uses midpoint silence; absent audio matches original zero slots.
                        output.write(samples.ljust(AUDIO_BYTES, b"\x80" if has_audio else b"\x00"))
                        count += 1
                        if progress is not None:
                            progress(count)
                if not count:
                    raise ValueError("No video frames were decoded for the selected interval")
                output.write(bytes(TRAILER_BYTES))
            if overwrite:
                os.replace(temporary, destination)
            else:
                # Atomically refuse overwrite even if another process creates the destination.
                try:
                    os.link(temporary, destination)
                except OSError as error:
                    if error.errno not in (errno.EPERM, errno.EXDEV, errno.ENOSYS, errno.EOPNOTSUPP, errno.EINVAL):
                        raise
                    # FAT SD cards cannot create hard links. Exclusive creation
                    # still refuses overwrites; copy only the completed conversion.
                    published = destination.open("xb")
                    try:
                        with published:
                            with temporary.open("rb") as completed:
                                shutil.copyfileobj(completed, published)
                    except BaseException:
                        destination.unlink(missing_ok=True)
                        raise
                temporary.unlink()
            temporary = None
        return {"path": str(destination), "device_type": device_type, "profile": profile.name,
                "frames": count, "fps": FPS, "duration_seconds": count / FPS,
                "header_bytes": len(header), "video_bytes_per_frame": profile.video_bytes,
                "audio_bytes_per_frame": AUDIO_BYTES, "audio": has_audio,
                "trailer_bytes": TRAILER_BYTES, "file_bytes": destination.stat().st_size}
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def inspect_file(path: str | Path, device_type: int | None = None) -> dict:
    path = Path(path)
    length = path.stat().st_size
    with path.open("rb") as stream:
        header = parse_header(stream.read(1024))
        if length < header["header_bytes"] + TRAILER_BYTES:
            raise ValueError("File is too short for its header and trailer")
        stream.seek(-TRAILER_BYTES, os.SEEK_END)
        if any(stream.read(TRAILER_BYTES)):
            raise ValueError("Expected 100000 zero trailer bytes")
    payload = length - header["header_bytes"] - TRAILER_BYTES
    candidates = [p for p in PROFILES.values() if p.device_type in header["device_types"]
                  and payload > 0 and payload % p.frame_bytes == 0]
    if device_type is not None:
        if device_type not in PROFILES or PROFILES[device_type] not in candidates:
            raise ValueError("File marker or frame size does not match the selected device type")
        candidates = [PROFILES[device_type]]
    if not candidates:
        raise ValueError("Payload length does not contain complete frames for its device marker")
    result = {"path": str(path.resolve()), "file_bytes": length, **header, "trailer_bytes": TRAILER_BYTES,
              "candidates": [{"device_type": p.device_type, "profile": p.name,
                              "frames": payload // p.frame_bytes, "frame_bytes": p.frame_bytes,
                              "duration_at_20fps": payload / p.frame_bytes / FPS} for p in candidates]}
    # A decimal first-digit marker cannot distinguish types 1/10/11 by itself.
    result["ambiguous_type_marker"] = len(header["device_types"]) > 1
    return result
