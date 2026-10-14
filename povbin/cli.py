import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

from .codec import Encoder, PROFILES
from .media import convert_video, inspect_file


def _device_commands(commands):
    device = commands.add_parser("device", help="List, upload, play and configure a connected display")
    device.add_argument("--host", default="192.168.4.1", help="Display IP (default: 192.168.4.1)")
    device.add_argument("--protocol", choices=("auto", "legacy", "http"), default="auto")
    device.add_argument("--adb", action="store_true", help="Use the connected Android phone's network over USB")
    device.add_argument("--serial", help="ADB serial; also enables the phone transport")
    device.add_argument("--timeout", type=float, default=5, help="Network timeout in seconds (default: 5)")
    device.add_argument("--raw", action="store_true", help="Include raw notification bytes in JSON output")
    operations = device.add_subparsers(dest="operation", required=True)
    operations.add_parser("info", help="Identify the display and protocol")
    operations.add_parser("status", help="Read playback state and file-list diagnostics")
    operations.add_parser("files", help="Read filenames and device indices")
    operations.add_parser("settings", help="Read available device settings")
    setting = operations.add_parser("set", help="Change a supported setting")
    setting.add_argument("key")
    setting.add_argument("value", help="JSON value or plain text (examples: true, 50, MyDisplay)")
    play = operations.add_parser("play", help="Play a device index or listed filename")
    play.add_argument("target")
    for operation, help_text in [("pause", "Pause playback"), ("resume", "Resume playback"),
                                 ("next", "Play the next file"), ("previous", "Play the previous file")]:
        operations.add_parser(operation, help=help_text)
    power = operations.add_parser("power", help="Turn the display on or off")
    power.add_argument("state", choices=("on", "off"))
    loop = operations.add_parser("loop", help="Choose all-file or single-file looping")
    loop.add_argument("mode", choices=("all", "single"))
    upload = operations.add_parser("upload", help="Upload a file without replacing an existing name by default")
    upload.add_argument("input", type=Path)
    upload.add_argument("--name", help="Destination basename (default: source basename); short .bin names suit legacy firmware")
    upload.add_argument("--overwrite", action="store_true", help="Allow replacement or upload when the device list is incomplete")
    delete = operations.add_parser("delete", help="Delete one listed file")
    delete.add_argument("target")
    delete.add_argument("--yes", action="store_true", help="Confirm deletion of this file")
    format_card = operations.add_parser("format-card", help="Erase every file on the display's SD card")
    format_card.add_argument("--yes", action="store_true", help="Confirm erasing the entire card")


def _adb_serial(args):
    if args.serial:
        return args.serial
    if not args.adb:
        return None
    result = subprocess.run(["adb", "devices"], capture_output=True, text=True, check=False)
    if result.returncode:
        raise ValueError("Cannot list ADB devices: " + result.stderr.strip())
    serials = [fields[0] for line in result.stdout.splitlines()
               if len(fields := line.split()) >= 2 and fields[1] == "device"]
    if len(serials) != 1:
        raise ValueError("Connect one authorized ADB phone, or choose it with --serial")
    return serials[0]


def _device_operation(args):
    def target(value):
        return int(value) if value.isdecimal() else value

    # Validate destructive command intent before opening a device connection.
    if args.operation in {"delete", "format-card"} and not args.yes:
        raise ValueError(f"{args.operation} requires --yes")
    from .device import DeviceClient
    with DeviceClient(host=args.host, protocol=args.protocol,
                      adb_serial=_adb_serial(args), timeout=args.timeout) as client:
        if args.operation == "upload":
            previous = 0.0
            def progress(value):
                nonlocal previous
                now = time.monotonic()
                if now - previous >= 1 or value == 100:
                    print(f"Uploaded {value:.0f}%", file=sys.stderr)
                    previous = now
            return client.upload(args.input, name=args.name, overwrite=args.overwrite, progress=progress)
        if args.operation == "play":
            return client.play(target(args.target))
        if args.operation == "delete":
            return client.delete(target(args.target))
        if args.operation == "format-card":
            return client.format_card()
        if args.operation == "set":
            try:
                value = json.loads(args.value)
            except json.JSONDecodeError:
                value = args.value
            return client.set_setting(args.key, value)
        if args.operation == "power":
            return client.power(args.state == "on")
        if args.operation == "loop":
            return client.loop(args.mode == "all")
        return getattr(client, args.operation)()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert POV videos and manage a MISSYOU display")
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
    _device_commands(commands)
    args = parser.parse_args(argv)
    try:
        if args.command == "profiles":
            print("Type  Model       Rows  LEDs  Bits  Mapping  Video bytes/frame")
            for p in PROFILES.values():
                print(f"{p.device_type:>4}  {p.name:<10} {p.rows:>4}  {p.leds:>4}  {p.bits:>4}  {'polar' if p.rotate else 'strip':<7}  {p.video_bytes:>10}")
            return 0
        if args.command == "device":
            result = _device_operation(args)
            if not args.raw:
                def compact(value):
                    if isinstance(value, dict):
                        return {k: compact(v) for k, v in value.items() if k != "raw_frame_hex"}
                    if isinstance(value, list):
                        return [compact(v) for v in value]
                    return value
                result = compact(result)
        elif args.command == "convert":
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
    except (ValueError, OSError, RuntimeError) as error:
        print(f"povbin: {error}", file=sys.stderr)
        return 1
