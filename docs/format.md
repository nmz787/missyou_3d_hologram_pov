# BIN format and compatibility

The converter writes the legacy offline BIN format used by 5DDisplayer 1.0.2.
It supports the eleven profiles listed by `povbin profiles`. Use the display's
correct profile when converting and inspecting files.

## Layout

A file contains:

1. A variable-length header with a model marker and two random header bytes.
2. Fixed-size frame records: packed LED video followed by 1600 audio bytes.
3. A 100,000-byte zero trailer.

Video is sampled onto the selected display's LED geometry, gamma corrected and
packed into bitplanes. Different profiles use different geometry, color depth
and video record sizes. The default working image is 672×672; changing `--size`
changes the sampling input, not the display's physical resolution.

Output cadence is 20fps. Audio is unsigned 8-bit mono PCM at 32kHz. There is no
frame-rate or audio-present field in the header; silent conversions retain zero
filled audio slots. Duration is therefore interpreted at the 20fps output cadence.
Some profiles share a header marker; provide `--device-type` when inspection
cannot determine a unique profile.

```bash
povbin inspect CLIP.BIN --device-type 7
```

## Compatibility

F-Mini11 uses conversion type 7 and has confirmed video/audio playback on hardware.
All eleven profiles have regression hashes recorded from isolated original
conversion methods; that does not establish physical compatibility with every
model or firmware variant. The original application's JPEG intermediate step is
replaced with direct FFmpeg decoding and resizing, so this CLI is not intended
to reproduce its intermediate JPEG artifacts.

This is a packed LED/audio format, not a renamed video or JPEG container. Copying
an MP4 to a `.bin` filename does not convert it. Network protocol selection
(`legacy` versus `http`) is separate from choosing the video conversion profile.
Newer device families or other vendor container formats may need another encoder.

The [conversion guide](usage.md) explains all export/inspection options. Technical
reconstruction reports and original-method evidence are available on the
[`reverse-engineering` branch](https://github.com/nmz787/missyou_3d_hologram_pov/tree/reverse-engineering).
