# MISSYOU POV video converter

Python CLI for the **offline `.bin` format in the supplied 5DDisplayer 1.0.2 installer**.
Supports all eleven original device profiles, video trimming, square cropping or
letterboxing, audio, file inspection, and a sampled-frame preview.

Your connected phone app reports **F-Mini11**, which maps to **device type 7**.
Use that as the initial profile even though the paper manual says MS2 (Mini12).

The sampling, gamma, bit packing, and header logic match isolated original
assembly methods byte-for-byte for all eleven profiles in the recorded tests.
You confirmed successful video **and audio** playback on your MISSYOU unit with
device type 7. That validates the tested clip on this display; the other profiles
have original-method parity tests but have not been tested on hardware.

## Install and convert

Requires Python 3.10+ and `ffmpeg`/`ffprobe` on PATH.

```bash
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/povbin profiles

# F-Mini11, as reported by your connected phone app.
.venv/bin/povbin convert input.mp4 output.bin --device-type 7
.venv/bin/povbin inspect output.bin --device-type 7 --preview preview.png
```

Run from an activated environment as `povbin`, or use `python -m povbin`.
`--fit contain` preserves the entire image with black margins; the default
`cover` fills the square and crops the edges. `--start 2 --duration 5` exports
a five-second clip starting at two seconds. `--no-audio` keeps zero audio slots.
`--flip-x` and `--flip-y` mirror the image. Output replacement requires
`--overwrite`. `--header-nonce 0102` makes the otherwise random header repeatable.

Conversion uses 20 fps and 32 kHz unsigned 8-bit mono PCM, yielding exactly
1,600 audio bytes per frame. No frame-rate field exists in this format; 20 fps
is the consistent cadence inferred from the original audio slot and sample rate.
FFmpeg decodes directly into frames; the original application's intermediate
JPEG compression and GUI resizing are replaced by direct cropping/resizing.

```python
from povbin import convert_video

result = convert_video("input.mp4", "output.bin", device_type=7,
                       fit="contain", start=2, duration=5)
print(result)
```

## SD-card filenames

The connected app shows FAT **8.3 short filename aliases**, including tilde names
such as `01CHRI~1` for `01Christmas.bin`. The full long filename still exists on
the card. This was confirmed by reading both filename forms from your mounted
VFAT card; see [the recorded names](docs/evidence/sd-card-filenames.json).

For readable names in the app, use at most **eight characters before `.BIN`**.
Uppercase ASCII letters and digits are the simplest choice: `CD.BIN`,
`CHRIS01.BIN`, or `TRACTOR.BIN`. Spaces and long descriptive names can produce
short aliases. Renaming files does not require re-encoding their video content.
The subsequent [Android APK investigation](docs/android.md)
found the app's own punctuation transform: `00_B.bin` becomes `00.B`, and
`13_TRA~1.bin` would become `13.TRA~1`. This mapper retains every entry.
It also found legacy response parsing defects that can lose lists or publish
only a prefix; the actual response is still needed to explain your missing
tractor/CD entries. Short names improve labels but are not a confirmed fix
for those omissions.

```bash
.venv/bin/povbin convert input.mp4 CD.BIN --device-type 7
```

On inspection the card had about 3.6 GiB free (7% used); its earlier Wi-Fi upload
failures have not been diagnosed. No SD-card files were changed during this check.

## Evidence and verification

- [Conversion report and file-format specification](docs/format.md)
- [Recovered methods with metadata tokens, CIL offsets, and hashes](docs/evidence/conversion.cil.txt)
- [Recorded replay of original assembly methods](docs/evidence/original-replay.json)
- [Detailed pixel analysis](docs/evidence/pixel-findings.md)
- [Android app, device-family presets, and missing-file investigation](docs/android.md)
- [Android Text Ball, Box, Marquee, 360 Text and Gallery behavior, evidence and sample clips](docs/android-features.md)
- [APK network discovery, TCP controls, HTTP/WebSocket protocol and upload evidence](docs/android-protocol.md)

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Tests compare every profile against hashes recorded from the original assembly,
exercise the unusual leading bitplane padding and ambiguous type markers, and
convert a real video while checking frame boundaries, PCM payload, and trailer.
See the report for reproduction commands; analysis tools are optional for using
the converter. A preview reconstructs sampled LED colors, so it appears sparse
and approximates the original image after gamma correction and quantization.
