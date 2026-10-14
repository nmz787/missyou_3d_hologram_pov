import argparse
import json
from pathlib import Path
import sys
import time

from .codec import Encoder, PROFILES
from .media import convert_video, inspect_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert video to 5DDisplayer legacy POV .bin files")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("profiles", help="List original device names and encoder settings")
    convert = commands.add_parser("convert", help="Convert a video; choose the original application's device type")
    convert.add_argument("input", type=Path)
    convert.add_argument("output", type=Path)
    convert.add_argument("--device-type", type=int, choices=PROFILES, required=True)
    convert.add_argument("--size", type=int, default=672, help="Square working size, multiple of four (default: 672)")
    convert.add_argument("--fit", choices=("cover", "contain", "stretch"), default="cover")
    convert.add_argument("--start", type=float, default=0, help="Start time in seconds")
    convert.add_argument("--duration", type=float, help="Clip length in seconds")
    convert.add_argument("--no-audio", action="store_true", help="Write original zero-filled audio slots")
    convert.add_argument("--flip-x", action="store_true")
    convert.add_argument("--flip-y", action="store_true")
    convert.add_argument("--overwrite", action="store_true")
    convert.add_argument("--header-nonce", help="Two bytes in hex for reproducible output (each 00..fe)")
    inspect = commands.add_parser("inspect", help="Validate a .bin file and report frame boundaries")
    inspect.add_argument("input", type=Path)
    inspect.add_argument("--device-type", type=int, choices=PROFILES)
    inspect.add_argument("--preview", type=Path, help="Save a reconstruction of sampled LED colors as PNG")
    inspect.add_argument("--frame", type=int, default=0, help="Zero-based frame to preview")
    args = parser.parse_args(argv)
    try:
        if args.command == "profiles":
            print("Type  Model       Rows  LEDs  Bits  Mapping  Video bytes/frame")
            for p in PROFILES.values():
                print(f"{p.device_type:>4}  {p.name:<10} {p.rows:>4}  {p.leds:>4}  {p.bits:>4}  {'polar' if p.rotate else 'strip':<7}  {p.video_bytes:>10}")
            return 0
        if args.command == "convert":
            previous = 0.0
            def progress(frames: int):
                nonlocal previous
                now = time.monotonic()
                if now - previous >= 1:
                    print(f"Encoded {frames} frames ({frames / 20:.2f}s)", file=sys.stderr)
                    previous = now
            nonce = bytes.fromhex(args.header_nonce) if args.header_nonce is not None else None
            result = convert_video(args.input, args.output, device_type=args.device_type, size=args.size,
                                   fit=args.fit, start=args.start, duration=args.duration,
                                   audio=not args.no_audio, flip_x=args.flip_x, flip_y=args.flip_y,
                                   overwrite=args.overwrite, nonce=nonce, progress=progress)
        else:
            result = inspect_file(args.input, args.device_type)
            if args.preview:
                if args.preview.resolve() == args.input.resolve() or args.preview.exists():
                    raise ValueError("Preview output must be a new file distinct from the input")
                if len(result["candidates"]) != 1:
                    raise ValueError("Choose --device-type for this ambiguous file before previewing")
                candidate = result["candidates"][0]
                if not 0 <= args.frame < candidate["frames"]:
                    raise ValueError("Preview frame is outside this file")
                p = PROFILES[candidate["device_type"]]
                with args.input.open("rb") as stream:
                    stream.seek(result["header_bytes"] + args.frame * p.frame_bytes)
                    video = stream.read(p.video_bytes)
                from PIL import Image
                Image.fromarray(Encoder(p).preview(video)).save(args.preview, format="PNG")
                result["preview"] = str(args.preview)
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError) as error:
        print(f"povbin: {error}", file=sys.stderr)
        return 1
