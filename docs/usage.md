# Conversion and inspection reference

Install the project as described in the [README](../README.md). These examples
use `povbin` from an activated virtual environment; `.venv/bin/povbin` works too.

## Select a device profile

```bash
povbin profiles
```

| Device type | Model |
| ---: | --- |
| 1 | F1 |
| 2 | F2 |
| 3 | F3 |
| 4 | F-Mini18 |
| 5 | F-360A |
| 6 | F-360B |
| 7 | F-Mini11 |
| 8 | F-360C |
| 9 | F-Mini20 |
| 10 | F4 |
| 11 | F5 |

Choose the profile for the actual device, rather than guessing from a BIN header.
Types 1, 10 and 11 share a header marker and can be ambiguous on inspection.
Paper model names may differ from app/firmware names; F-Mini11 corresponds to
conversion type 7. A legacy app's incorrect model label can also result from a
malformed file-list response; `device info` reports the parsed firmware model
and list diagnostics.

## Convert a video

```bash
povbin convert INPUT OUTPUT --device-type TYPE [OPTIONS]
```

| Option | Default | Effect |
| --- | --- | --- |
| `--device-type TYPE` | Required | Select the device's LED geometry and packing. |
| `--fit cover` | `cover` | Fill the square frame, cropping edges. |
| `--fit contain` | | Preserve the whole image with black margins. |
| `--fit stretch` | | Stretch the image to a square. |
| `--start SECONDS` | `0` | Skip the beginning of the source. |
| `--duration SECONDS` | Whole remaining video | Limit the converted segment. |
| `--no-audio` | Audio enabled | Write silent audio slots. |
| `--flip-x` | Off | Mirror horizontally. |
| `--flip-y` | Off | Mirror vertically. |
| `--size PIXELS` | `672` | Set square working size; a multiple of four. This does not change physical LED count. |
| `--overwrite` | Off | Allow replacement of an existing local output. |
| `--header-nonce HEX` | Random | Advanced: fix the two header bytes for repeatable output; four hex digits, each byte 00–FE. |

```bash
povbin convert input.mp4 CLIP.BIN --device-type 7 --fit contain
povbin convert input.mp4 SHORT.BIN --device-type 7 --start 10 --duration 3 --no-audio
povbin convert input.mp4 MIRROR.BIN --device-type 7 --flip-x
```

FFmpeg decodes the source. Output uses 20fps and 32kHz unsigned 8-bit mono audio.
The final report includes profile, frames, duration and byte sizes. Progress
appears on stderr; JSON output appears on stdout. Exit code0 means the command
completed; exit code1 reports a conversion/validation error. Invalid CLI syntax
uses argparse's exit code2.

## Inspect a BIN file

```bash
povbin inspect CLIP.BIN --device-type 7
povbin inspect CLIP.BIN --device-type 7 --preview preview.png --frame 10
```

Inspection reports header information, compatible profiles, frame counts and
duration at 20fps. `--device-type` resolves ambiguous candidates. `--frame` is
zero-based and selects a frame only when saving a preview; its default is 0.
A preview must be a new file, distinct from the input.

Previews reconstruct sampled LED colors after gamma and quantization. They can
look sparse; they are a diagnostic view of LED samples rather than a photograph
of the spinning display. Inspection checks the file layout, not the device's
ability to play it.

## Python API

```python
from povbin import convert_video, inspect_file

result = convert_video(
    "input.mp4", "CLIP.BIN", device_type=7,
    fit="contain", start=2, duration=5,
)
print(result)
print(inspect_file("CLIP.BIN", device_type=7))
```

Use `audio=False`, `flip_x=True`, `flip_y=True` or `overwrite=True` as needed.
See [device operations](device.md) for the `DeviceClient` API.

## Troubleshooting conversion

- Missing FFmpeg: install it and check `ffmpeg -version` and `ffprobe -version`.
- Existing output: choose a new filename or add `--overwrite`.
- Ambiguous inspection: provide the intended `--device-type`.
- Wrong image shape: try `--fit contain` or select a shorter segment to preview.
- Video plays incorrectly: confirm the model/profile first. BIN inspection alone
  cannot establish hardware compatibility.
