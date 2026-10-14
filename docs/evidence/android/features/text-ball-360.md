# 3D Text Ball and 360 Text: shipped APK evidence

Target: `5D-Holo-android.apk`, package `com.sp.holographic`, version 1.0.85 / 105.
APK SHA-256: `8a83b1f128beb43341eefd2b4ad743512d0193ff6dd4e7b56feba138fb4b63c9`.
Hermes v96 `assets/index.android.bundle` SHA-256: `8389750af87d60e75bbd7d93ba57d1bd239008812c8c5ef7ecc84cf2a46777e2`.

These findings are static call-flow evidence, with one explicitly controlled offline JavaScript replay. No Android app, phone, display, Wi-Fi command or network request was executed for this report. Hermes decompiler pseudocode supplied navigation seeds; claims below were checked against raw Hermes instruction listings. The recovered sphere script and HTML are exact APK string fragments joined in the instruction-proven order, with explicit placeholders where the APK interpolates runtime values. They are not guessed reconstructions or separate HTML files found in the APK.

## What the two features actually produce

| Feature | Editor / renderer | Generated media |
| --- | --- | --- |
| 3D Text Ball | One text string, one color; repeated characters positioned on a rotating sphere. CSS 3D live preview; separate bespoke WebGL export renderer. | 200 JPEG frames at 720 × 720, H.264 MP4 at 20 fps: ten seconds / one full revolution. |
| 360 Text | One to three independent, centered text rows with text, color and font size. React Native views, black background, 3:1 preview. | One screenshot looped into a ten-second H.264 MP4 at 20 fps. The inspected editor itself contains no rotation or marquee animation. |

Both design pages save generated MP4 media through `Utils.moveVideoToDCIM`, after a name dialog and duplicate-name check. This editor path does not emit LED-packed BIN bytes directly. The later local-media conversion/upload flow is a separate stage, covered by the shared feature investigation. “360 Text” is the user-facing name; static evidence here does not prove a particular physical 360-degree display appearance.

## 3D Text Ball

`DesignSphereTextPage` is function **17401**, absolute bytecode offset **0x00376012**, length **1220** bytes. It initializes the color with `#25fc11` at relative **+0xb2** and text with `strings('welcome_use')` at **+0xf9**. The English packaged locale maps that key to “Welcome to the 5D HOLO.” The editor binds text and color to the child at **+0x3c6** onward. Its settings UI is `renderItems` **17437**, **0x003771be**, containing text input and color selection. `onChangeText` **17439**, **0x00377701**, stores input as-is and sets the unsaved-edit flag. The color picker uses **17421 / 17434 / 17436**. Text/color changes trigger child `reloadWebView` through **17426**, **0x00376e85**, and **17479**, **0x00378559**.

The child is exported by the module wrapper **17467**, **0x003780f3**, which installs a React `forwardRef` component with closure **17470**. Function **17470**, **0x00378229**, builds the injected script and HTML and renders a `WebView`. Important raw sites:

- **+0x05–0x11**: child fallback color `#13386C`; the editor normally passes its green color.
- **+0x38–0x44**: child fallback text `你好，欢迎使用`; empty editor input therefore falls back rather than becoming an empty sphere.
- **+0x61–0x7e**: color replaces every `0x` with `#`.
- **+0x8b–0xa1**: script concatenates string IDs **693, 786, 9457, 9458**, with raw text, platform and normalized color inserted between them. It does not JSON-escape the text.
- **+0xcd–0xd5**: HTML concatenates string IDs **9459, 565**, with color between them.
- **+0x16c–0x189**: `WebView` receives `source: {html: ...}`. **17475** calls the injection closure on load end; **17473** invokes the WebView's native `injectJavaScript` method.

The exact recovered resources are [sphere script](text-ball-360-sphere-script.template.js), [HTML](text-ball-360-sphere-html.template.html), and [individual string fragments](text-ball-360-sphere-fragments.json). [Fragment offsets](text-ball-360-fragment-offsets.json) locate the string bytes directly inside the bundle, including encoding and SHA-256. The extractor verified every large fragment occurs verbatim in the packaged bytes.

The script repeats Unicode code points from the text until the character pool contains at least 170 characters. It calculates a layer count from `4*i*i + 2*i - 1` for `i = 3..12`, then increasing/decreasing ring populations. It skips ring zero when emitting glyphs. For the tested short texts, this gives 155 positioned glyphs; the “170” threshold is not a promise of 170 visible glyphs.

The sphere radius is half the 80%-width box. Coordinates for latitude ring `i` and glyph `j` are:

```text
theta = pi / ring_count
phi   = 2*pi / glyph_count_in_ring
x = r*sin(theta*i)*sin(phi*j)
y = -r*cos(theta*i)
z = r*sin(theta*i)*cos(phi*j)
```

`applyTransform` rotates x/z around Y, sets each glyph's `translate3D`, `rotateY`, and `rotateX`, and clamps depth-dependent opacity into **[0.2, 1]**. A 50 ms timer decrements `angleY` by **1.8°**. One revolution is 200 steps. Touch handlers accumulate horizontal/vertical drag, but the inspected transform uses `tX` only; `tY` is unused, and each timer tick resets `tX` from `angleY`. Thus the code does not establish persistent two-axis drag control. Preview CSS has `preserve-3d` and visible backs of glyphs, without a CSS perspective term.

Export pauses the preview, remembers its angle, resets angle to zero and creates a **720 × 720** offscreen WebGL canvas. Its radius is **288 px**, with glyph dimensions scaled from the preview, including `devicePixelRatio`. Each glyph becomes a **128 × 128** canvas texture drawn in sans-serif. Glyph quads use orthographic projection, depth testing and alpha blending. Preview and export are different rendering engines; exact visual equality is not established, and comments about Y flipping conflict with the actual unflipped projection matrix.

The exporter advances the angle before each rasterization: frame zero is **−1.8°**, frame 199 is **−360°**. It sends batches of **10** JPEG data URLs at quality **0.85** through `window.ReactNativeWebView.postMessage`:

```json
{"t":"b","f":[{"i":0,"d":"data:image/jpeg;base64,..."}]}
{"t":"d","n":200}
{"t":"e","m":"error message"}
```

Functions **17482 / 17483**, **0x00378600 / 0x0037862c**, install a Promise listener then inject `exportFrames(200);true;`. **17484**, **0x0037868f**, parses event JSON, delivers batches through **17485**, resolves on `d.n`, and rejects on `e.m`. **17486**, **0x00377f8c**, rejects if export has not settled after **60,000 ms**. JSON/listener exceptions are caught. The progress UI's 90-second timeout is separate from this export Promise's 60-second timeout.

Save activates composition through **17431**, **0x00376ef8**, calling `MediaUtil.generateVideoFromWebGL`. Its implementation **8360**, **0x00290d03**, writes numbered `frame_%06d.jpg` files from the base64 batches, waits for pending writes, resumes preview animation and executes:

```text
-framerate 20 -i "<cache>/frame_%06d.jpg" -c:v libx264 -preset ultrafast -crf 23 -r 20 -threads 4 -pix_fmt yuv420p <output.mp4>
```

It checks FFmpeg's return code and reports success/failure. It treats zero frames or export exceptions as failures, and attempts to resume animation after capture failure. Individual frame-write failures are logged and caught before the Promise aggregation; they do not independently reject that aggregation. FFmpeg remains the later success check. There is no audio input in this generation command.

## 360 Text

`DesignText360Page` is **18769**, **0x0039be70**, **1255** bytes. At **+0xb2–0x128** it constructs three `{text: strings('hey'), color: '#25fc11', size: 42}` row objects. The English locale's `hey` is “Hello, Welcome!” The preview container at **+0x375** has `width:'100%'`, `aspectRatio:3` and black background. The mapped renderer **18821**, **0x0039dc5e**, emits React Native `Text`, with `numberOfLines:1`, centered horizontally, `verticalAlign:'middle'`, and each row's font size/color.

The editor supports **one to three rows**: `addOneTextLine` **18806**, **0x0039d09d**, only adds while length is less than three; **18807** creates the default green 42-size greeting row. `delteOneTextLine` (the spelling in the binary) **18808**, **0x0039d127**, only deletes when more than one remains and **18809** drops the last row. **18804 / 18805** update text, color and size by row index. Settings renderer **18811**, **0x0039d406**, includes a number-pad size field with **maxLength 3**. Size handler **18815**, **0x0039db9b**, uses `parseFloat`; NaN becomes **0**, with no numeric clamp in this handler. The clear-size handler also stores zero. The renderer may therefore receive size zero; no minimum font-size validation is demonstrated.

The right save handler **18820** invokes compose via **18798**, **0x0039cd2f**. Raw sites **+0x62–0x76** load `MediaUtil.generateStaticVideo`, retrieve the preview ref, and call it with **10 seconds** and a callback. `generateStaticVideo` implementation **8372**, **0x002918a6**, calls `captureRef` with `{format:'jpg', quality:0.9, result:'tmpfile'}`, then runs:

```text
-loop 1 -i "<screenshot.jpg>" -c:v libx264 -preset ultrafast -crf 23 -t 10 -r 20 -pix_fmt yuv420p <output.mp4>
```

It checks FFmpeg's return code, deletes the temporary screenshot on the successful path and reports failure on exceptions. No `WebView`, rotating HTML, scrolling step, Three.js dependency or animated capture occurs along this inspected feature's editor/export path. Its preview has an animation-themed `dataSet` attribute, but the called export method captures one still image; that attribute is insufficient evidence of generated animation.

## Saving, constraints, corroboration and limits

Save completion for Text Ball is **17402 → 17405 → 17406 → 17407**; corresponding 360 Text functions are **18770 → 18773 → 18774 → 18775**. Generated paths are offered to a name dialog. Cancel deletes the temporary output. Confirm appends **`.MP4`**, checks `Utils.isMediaFileExist`, repeats the name dialog on collision, and calls `Utils.moveVideoToDCIM` otherwise. Move failure shows `export_failed`; success shows `export_success` and returns after a one-second delay. This gives preserved local media for later BIN conversion/upload.

The editors and these media-generation methods do not inspect model IDs, LED counts or device geometry. This is a bounded statement about the retained feature call paths, not a claim that every device supports the 360 Text format. Menu gating and shared downstream conversion constraints must be read separately.

[Controlled replay](text-ball-360-replay.json) executes the exact assembled sphere JavaScript using Node VM and mock DOM/WebGL/timers. `HELLO` and a Chinese greeting produced 155 glyph positions and exactly 20 bridge batches of 10 frame indices, followed by `{t:'d',n:200}`. Doubling DPR doubled the computed font size while keeping coordinates unchanged. It also reproduces **syntax failure for `O'Reilly` and literal newline input** because raw text is placed inside a single-quoted JavaScript literal. This proves a script-construction defect for those inputs, not an observed phone failure. The harness stubs image encoding and does not draw pixels or validate browser GPU behavior. The child empty-text fallback prevents the direct-script empty-string repeat loop during normal component use.

Replay and extraction are reproducible from the project root:

```bash
python3 docs/evidence/android/features/text-ball-360-extract.py
node docs/evidence/android/features/text-ball-360-replay.cjs
```

[Curated raw HASM](text-ball-360-functions.hasm) includes the editor, component, bridge, save, and media-generation functions. [Function manifest](text-ball-360-functions.json) gives exact absolute bundle offsets, byte lengths, bytecode hashes and source HASM lines. Hashes identify the shipped functions even where Hermes deduplicates identical bytecode and several function IDs share an offset. No exact-pixel Android/GPU equivalence, physical playback of either generated design, font availability on the phone or hardware-specific 360 mapping is claimed.
