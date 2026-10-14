# MISSYOU POV display tools

Convert videos to `.bin` files for compatible MISSYOU 3D hologram / persistence
of vision displays, then upload and control playback from Python or the command
line. Connect directly over the computer's Wi-Fi/network, or through an
ADB-connected Android phone.

## Install

Requires **Python 3.10+** and **FFmpeg** (`ffmpeg` and `ffprobe` on PATH).
ADB is optional and only needed for the phone connection.

```bash
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/povbin --help
```

On Linux, install FFmpeg with your distribution's package manager, for example
`sudo apt install ffmpeg`. Android platform tools provide `adb` if you use a
phone. Activate the environment with `source .venv/bin/activate` to use `povbin`
without the `.venv/bin/` prefix. `python -m povbin` is also supported.

## Quick start: convert, upload, play

Choose the profile that matches your display. **F-Mini11 uses `--device-type 7`**;
run `profiles` to list all supported conversion profiles.

```bash
.venv/bin/povbin profiles
.venv/bin/povbin convert input.mp4 CLIP.BIN --device-type 7
.venv/bin/povbin inspect CLIP.BIN --device-type 7 --preview preview.png
```

Connect the computer to the display's Wi-Fi hotspot, then:

```bash
.venv/bin/povbin device info
.venv/bin/povbin device upload CLIP.BIN
.venv/bin/povbin device play CLIP.BIN
```

The default display address is **192.168.4.1**. Direct mode uses your computer's
network routing, so Ethernet also works if it can reach the display. Use
`device --host ADDRESS ...` for a different IP. No phone is needed in direct mode.

To use a USB phone instead, authorize it for ADB and connect the phone to the
display's Wi-Fi. Add `--adb` before the operation:

```bash
.venv/bin/povbin device --adb upload CLIP.BIN
.venv/bin/povbin device --adb play CLIP.BIN
```

You can also copy the converted file to the SD card manually. Use short ASCII
names such as `CLIP.BIN`: up to eight characters before the extension avoids FAT
short-name aliases such as `LONGNA~1.BIN` in legacy display lists.

## Common tasks

```bash
# Preserve the whole picture instead of cropping to fill the square.
.venv/bin/povbin convert input.mp4 CLIP.BIN --device-type 7 --fit contain

# Convert five seconds, starting two seconds into the source.
.venv/bin/povbin convert input.mp4 SHORT.BIN --device-type 7 --start 2 --duration 5

# Replace an existing local output or an existing file on the display.
.venv/bin/povbin convert input.mp4 CLIP.BIN --device-type 7 --overwrite
.venv/bin/povbin device upload CLIP.BIN --overwrite

.venv/bin/povbin device files
.venv/bin/povbin device pause
.venv/bin/povbin device resume
.venv/bin/povbin device next
.venv/bin/povbin device loop single
.venv/bin/povbin device loop all
```

Connection options go **before** the device operation, for example
`device --host 192.168.4.1 --protocol legacy upload CLIP.BIN`.

## Usage and compatibility

- [Conversion options, inspection and Python API](docs/usage.md)
- [Connections, uploads, playback, settings and troubleshooting](docs/device.md)
- [BIN format and device compatibility](docs/format.md)

Conversion supports eleven legacy profiles, audio, cropping/letterboxing and
mirroring. F-Mini11 conversion and legacy network operations have been tested
on hardware. Other conversion profiles have original-method parity tests;
HTTP-family operations have local wire tests and have not been tested on hardware.
Some settings and controls depend on the display's firmware. An upload's filename
listing does not prove stored-byte equality or physical video/audio playback.

## Development

The runtime package and regression tests are on `main`. Detailed reverse-engineering
reports, extracted evidence and analysis utilities are archived on the
[`reverse-engineering` branch](https://github.com/nmz787/missyou_3d_hologram_pov/tree/reverse-engineering).
Large vendor packages, SDKs and personal media are excluded from Git.

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Tests use local stand-ins and generated media; they do not require a connected
display or Android phone.
