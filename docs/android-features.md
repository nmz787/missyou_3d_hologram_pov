# Android design features: behavior and evidence

All five features in the supplied `5D-Holo-android.apk` have reachable editor,
renderer and export implementations. They generate ordinary video on the phone;
the editor save handlers name an `.MP4`, check for a duplicate and move it to
DCIM. They do not directly generate a device `.bin` or upload it.

| Feature | Controls and behavior proved from shipped code | Export |
| --- | --- | --- |
| **3D Text Ball** | Text and color; repeats characters across latitude rings on a sphere. CSS 3D preview, separate WebGL frame renderer; 1.8° rotation per 50 ms. | 200 square 720×720 JPEG frames → 10-second, 20 fps MP4. |
| **3D Box** | Six photo slots, cropped to 500×500; three styles: closed cube, separated faces, and opening/closing faces. Own WebGL shaders; −25° X tilt and rotating Y axis. Selected photos repeat across faces when fewer than six are supplied. | 200 square 720×720 JPEG frames → 10-second, 20 fps MP4. |
| **Marquee** | Text, color and size (10–120, default 42); repeated horizontal text scrolling left over black, with a 60-pixel gap. Canvas rendering. | 200 square 720×720 JPEG frames → 10-second, 20 fps MP4. Export rounds its movement step, so its phase can differ from preview. |
| **360 Text** | One to three centered text rows with independent text, color and size; wide 3:1 React Native view. | A single screenshot repeated into a 10-second, 20 fps MP4. The editor export contains no rotation or scrolling. |
| **Gallery** | Six photo slots, cropped to 800×600. Preview scales and fades photos; unfilled slots show packaged samples. | Selected photos produce square 720×720 video with 0.5-second `smoothdown` transitions, targeting 10 seconds. With no photos selected, it saves a still snapshot of the sample preview. |

The menu links are actual navigation calls, not unused labels. `DesignPage`
function **15440** builds the five cards; functions **15441–15445** invoke
`navigate` with their respective design routes. These functions and the shared
export code are retained in [common-bytecode.hasm](evidence/android/features/common-bytecode.hasm),
with original byte ranges and hashes in [common-functions.json](evidence/android/features/common-functions.json).

## Evidence for each feature

| Feature | Entry function and bundle file offset | Detailed evidence |
| --- | --- | --- |
| Text Ball | `17401`, `0x00376012` | [Controls, sphere math, renderer, export and save](evidence/android/features/text-ball-360.md#3d-text-ball) |
| Box | `17644`, `0x0037dcde` | [Photo assignment, three styles, WebGL and save](evidence/android/features/spinning-box.md) |
| Marquee | `17578`, `0x0037bc53` | [Controls, Canvas movement and export](evidence/android/features/marquee-gallery.md#marquee) |
| 360 Text | `18769`, `0x0039be70` | [Rows, dimensions, static capture and save](evidence/android/features/text-ball-360.md#360-text) |
| Gallery | `17694`, `0x0037f5b6` | [Selection, preview worklet and FFmpeg transitions](evidence/android/features/marquee-gallery.md#gallery) |

Each report follows call instructions and data changes through the implementation.
The retained disassembly is the underlying evidence; readable decompiler output
was used to find the relevant functions. Extracted renderer strings have physical
bundle offsets and hashes, and their interpolation order is established by the
calling bytecode. The renderers used here do not depend on the APK's Three.js asset:
Text Ball/Box implement their own WebGL, and Marquee uses Canvas 2D.

## Offline rendering corroboration

The exact recovered Text Ball and Box templates were run in local desktop Chrome,
with page network requests blocked and a local `ReactNativeWebView.postMessage`
receiver. Text Ball used demonstration text `HELLO`; Box used the packaged fallback
JPEG on all six faces. All four cases produced 200 ordered, nonempty 720×720 JPEGs,
20 batches and a completion message. Pixel differences between sampled frames
confirm that these outputs animate. The exported frames were encoded locally into
these reviewable clips:

- [Text Ball](evidence/android/features/browser-text-ball.mp4)
- [Closed Box](evidence/android/features/browser-box-0.mp4)
- [Separated Box faces](evidence/android/features/browser-box-1.mp4)
- [Opening/closing Box faces](evidence/android/features/browser-box-2.mp4)

Representative exported images are retained for [Text Ball](evidence/android/features/browser-text-ball-frame-050.jpg)
and [Box](evidence/android/features/browser-box-2-frame-050.jpg). The
[browser replay record](evidence/android/features/browser-renderer-replay.json)
records source hashes, substitutions, browser version, frame indices, dimensions,
pixel statistics, output hashes and desktop FFmpeg commands.

Marquee was independently run with its exact assembled HTML in desktop Chrome:
200 frames completed, and sampled JPEGs decoded as 720×720 with thousands of
nonblack pixels. See its [browser replay record](evidence/android/features/marquee-gallery-browser-replay.json)
and [runnable HTML](evidence/android/features/marquee-gallery-marquee.html).

These are extracted-source executions, **not execution of the Android app**.
Desktop fonts, device pixel ratio and SwiftShader can change the appearance.
React Native state, picker permissions, phone media save, Android FFmpeg/native
encoding, device upload and hardware playback were not exercised. Gallery's
FFmpeg commands and 360 Text's native view capture are established statically;
neither was executed on a phone during this investigation.

## Connection to the device family and Python converter

The shared animation helper **8360** collects the bridge JPEGs, writes
`frame_%06d.jpg`, awaits writes, resumes preview animation and runs:

```text
-framerate 20 -i "<cache>/frame_%06d.jpg" -c:v libx264 -preset ultrafast -crf 23 -r 20 -threads 4 -pix_fmt yuv420p <output.mp4>
```

The static helper **8372** captures a JPEG with `captureRef` and loops it with
`-loop 1 ... -t 10 -r 20`. Gallery uses helper **8366**, producing individual
segments then chaining `xfade=transition=smoothdown:duration=0.5`.
The generation commands have no audio input.

Save completion invokes `moveVideoToDCIM`; its async implementation **7785** calls
the common file mover and reports success. A misleading cancellation log says
“convert and upload,” but the actual editor handlers save a local MP4. Later media
selection in DevicePage **12337** chooses `PAGE_EDIT_MEDIA_360` when
`getConfigByModle(...).is_360` is true, otherwise `PAGE_EDIT_MEDIA`.
The special converter **8292** supplies `is_360:true`, per-item frame dimensions
and centers, destination geometry, LED counts and color depth to
`MEDIA_FUNC_CONVERT`. The ordinary converter **8332** also calls that native
boundary. This connects generated media to the already recovered family presets;
it does not establish the native library's precise packing implementation.

No feature-specific device-model check appears in the retained design menu and
editor generation paths. The Android preset for **F-MINI11** has 48 LEDs,
300 angular lines and five color bits, matching the desktop converter's type 7
geometry; it is not marked `is_360`. The name “360 Text” alone does not switch
conversion into the special 360 device format. Device presets and Android/desktop
differences remain documented in [the family investigation](android.md).

The square demonstration MP4 files can already feed the existing converter:

```bash
.venv/bin/povbin convert \
  docs/evidence/android/features/browser-box-2.mp4 box.bin --device-type 7
```

For a wide 3:1 video, `--fit contain` preserves all its text with black margins
in this converter's square image. That is ordinary F-Mini11 image conversion;
physical wraparound mapping for the Android 360-device path is not implemented
or validated by this investigation.

## Defects and differences worth preserving

- Text Ball inserts text unescaped into a single-quoted script literal. Controlled
  execution reproduces syntax errors for `O'Reilly` and literal newline input.
- Box's readiness receiver treats any `t:'r'` message as ready, even when its
  `ready` value is false. This is a static weakness, not an observed phone failure.
- Gallery preview and export use different transitions. Empty Gallery exports a
  still image; selected-photo export omits the fallback samples. Failed segment
  encodes can be omitted, shortening the result.
- 360 Text size parsing can produce zero and has no numeric clamp in its input
  handler. Its name and animation-themed attributes do not establish animated
  export.

These feature findings do not supply the device notification bytes still needed
to identify why `13_tractor` and `14_cd` are absent from the app's list.

## Reproduction and identity

The target is `com.sp.holographic` 1.0.85 / code 105:

```text
APK SHA256:    8a83b1f128beb43341eefd2b4ad743512d0193ff6dd4e7b56feba138fb4b63c9
Bundle SHA256: 8389750af87d60e75bbd7d93ba57d1bd239008812c8c5ef7ecc84cf2a46777e2
```

The original REA/JADX package record is
[rea-package.json](evidence/android/rea-package.json), Evidence
`ev_3752373f87d75ea7839bdf6aeeb3985a776f766242fb6617fda171ffcbbfbd53`.
Feature HASM, string extraction and local renderer runs are independent tool
observations, rather than REA Android runtime records.

The preserved bundle/disassembly under `analysis/android` came from this exact
APK, using `hermes-dec 0.1.6` for Hermes 96. From the project root:

```bash
.venv/bin/python tools/select_android_feature_common.py
.venv/bin/python docs/evidence/android/features/text-ball-360-extract.py
.venv/bin/python docs/evidence/android/features/spinning-box-extract.py
node docs/evidence/android/features/text-ball-360-replay.cjs
node docs/evidence/android/features/spinning-box-replay.mjs
node docs/evidence/android/features/marquee-gallery-replay.cjs

# Optional desktop raster corroboration: playwright, Pillow, installed Chrome and FFmpeg.
.venv/bin/python tools/replay_android_renderers.py
.venv/bin/python docs/evidence/android/features/marquee-gallery-browser-replay.py
.venv/bin/python tools/verify_android_feature_evidence.py
```

[Feature evidence index](evidence/android/features/evidence-index.json) records
artifact hashes, retained evidence files, validation and remaining unknowns.
All five functionality questions are answered at the static implementation level;
Text Ball, Box and Marquee also have offline rendered-image corroboration.
