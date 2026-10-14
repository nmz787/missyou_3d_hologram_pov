# 3D Box / DesignSpinningBoxPage

## Evidence identity and scope

Supplied APK `5D-Holo-android.apk`, package `com.sp.holographic`, version1.0.85/code105, SHA256 `8a83b1f128beb43341eefd2b4ad743512d0193ff6dd4e7b56feba138fb4b63c9`. Hermes96 member `assets/index.android.bundle`, SHA256 `8389750af87d60e75bbd7d93ba57d1bd239008812c8c5ef7ecc84cf2a46777e2`.

This is artifact-bound static disassembly plus controlled execution of extracted renderer source against synthetic DOM/WebGL APIs. It is **not Android runtime observation, actual rasterized imagery, phone media-library verification, or physical-device playback**. The raw HASM is authoritative for UI/call relationships; decompiled pseudocode only guides reading. Selected instructions are retained in [spinning-box-bytecode.hasm](spinning-box-bytecode.hasm); [spinning-box-functions.json](spinning-box-functions.json) gives exact function byte ranges and raw SHA256 values. All function-relative offsets below can be added to their manifest's file offset.

## Proven UI and image behavior

Metro module1479 is the screen. Its module initializer is function17641 (`0x37db57`); screen function17644 (`0x37dcde`) imports module1467 as its renderer through dependency index8. The module's dependency array at its registration is `[1,6,340,38,171,2,1002,1467,781,215,478,730,1005,495,1251,1465,613,1476]` in function0's registration stream. Renderer module1467 initializer is function17444 (`0x377779`); its component is function17447 (`0x37789a`).

The screen initializes six empty image slots (`fn17644 +0xa3`, six-string array passed to `useState`), style/type0 (`+0xdd`, `useState(0)`), an unchanged/dirty flag false, and the name ref to localized `name`. It displays six image tiles in a three-column list. Empty tiles call `selectImage(index)` (`fn17682`); filled tiles have a remove button calling `removeImage(index)` (`fn17683`). `removeImage` and its updater (`fn17679/17680`) replace that slot with an empty string. Photo selection (`fn17673 +0x38/+0x3e onward`) calls crop-picker `openPicker` with:

```json
{"mediaType":"photo","cropping":true,"width":500,"height":500,"includeBase64":true}
```

Its success handler `fn17676` marks the screen dirty; if the returned `path` is truthy, updater `fn17677` assigns `data:<mime>;base64,<data>` to the selected slot. Its rejection handler logs the error (`fn17678`). The screen's actual renderer props are `images=slots.filter(image=>image.length>0)` and `type=selectedStyle` (`fn17644 +0x34b..0x363; fn17686` is the predicate). Thus empty slots disappear before assigning cube faces: tile number is **not a fixed face identity** when intervening slots are empty.

Three buttons call the state setter with0,1,2 respectively (`fn17687`,17688,17689), with matching selection colors. There are no per-face text, speed, duration, camera, or audio controls in this complete screen function.

Renderer `fn17447 +0x75..0x1db` filters images again, then fills six faces as follows. Letters denote the compacted selected-image order; renderer source draws faces in front,back,right,left,top,bottom order.

| Number of selected images | Six assigned textures |
|---|---|
|0|packaged default JPEG repeated six times|
|1|A,A,A,A,A,A|
|2|A,A,B,B,A,B|
|3|A,A,B,B,C,C|
|4|A,B,C,D,A,D|
|5|A,B,C,D,E,E|
|6 or more|first six selected images|

This mapping follows actual branch/GetByVal/PutOwnByIndex/Array.fill instructions, not inferred labels. The packaged fallback texture is string576 loaded by module1468 initializer `fn17466 +0x2b`; its decoded bytes are retained as [spinning-box-default.jpg](spinning-box-default.jpg).

## Renderer functionality

The actual WebView source is assembled by `fn17447 +0x200/+0x204/+0x208/+0x20c` loading strings3419,2491,2499,9490; `+0x216` invokes variadic concat with selected type, distance and `JSON.stringify` of mapped images. `+0x2a2/+0x2a7` places the resulting HTML in `WebView.source.html`. This establishes reachability and use; raw HTML string presence alone would not.

[spinning-box-strings.json](spinning-box-strings.json) preserves those full strings plus exact string-table byte offsets, encodings and raw hashes. [spinning-box-renderer-template.html](spinning-box-renderer-template.html) assembles their exact bodies with explicit `__TYPE__`, `__DIST__`, `__IMAGE_SRCS__` substitution points. This renderer directly uses WebGL, its own shaders and matrix functions; the complete assembled document contains no Three.js import or remote script.

It paints six textured square planes on black, each40% of viewport size. Half-face-size is `h=S*0.2` and center distance from origin is `d=S*dist/100`, where `S=min(innerWidth,innerHeight)`. Vertex buffers contain position and UV for four vertices per face; indices `[0,1,2,0,2,3]` form two triangles. The fragment shader multiplies texture alpha by0.8. Rendering enables depth testing and SRC_ALPHA/ONE_MINUS_SRC_ALPHA blending. It uses a3000-unit camera distance, perspective fov `2*atan((S/2)/3000)`, aspect1, near1, far5000; model matrix is `rotateY(angleY)*rotateX(-25°)`. Actual math uses-25° although an adjacent comment says-30°.

| UI choice | Actual geometry/animation |
|---|---|
|Style1 / type0|`dist=20`, so planes meet to form a cube; rotates1.8° aroundY every50ms|
|Style2 / type1|`dist=30`, separating faces; same rotation|
|Style3 / type2|each tick increases phase by0.0314 and sets `dist=25+5*sin(phase)`, oscillating approximately20..30; same rotation|

The initial angle is0. Preview uses device pixel ratio and viewport size. Touchmove computes horizontal delta and adds `dx*0.3` degrees; vertical delta is calculated but unused. This produces a raster perspective animation suitable for a POV display; it does not create an actual volumetric object.

## Export and save

The header's right button (`fn17685`) calls `composeVideo`; async body `fn17670` shows an export-loading state with90000ms timeout and invokes `MediaUtil.generateVideoFromWebGL(rendererRef, callback)`. Its callback `fn17671` dismisses that state and forwards result/path to `handleSaveVideo` (`fn17645`). Common `MediaUtil` details are investigated separately; its body `fn8360` writes numbered JPEG files, encodes them through FFmpeg at20fps and emits a cached MP4. Therefore200 Box frames imply10seconds at this media path's20fps.

The renderer exposes pause/step/resume/getTotalSteps/getWebViewRef/exportAllFrames through `useImperativeHandle` (`fn17450`). `getTotalSteps` returns200 (`fn17455`). `exportAllFrames` builds a Promise (`fn17457/17458`) and injects `window.exportFrames(200)` after readiness (`fn17461 +0xb3 onward`). The actual embedded exporter:

- Stops the preview timer and resets angle to0, phase to0, and distance to30 for type1 or20 otherwise.
- Creates a separate **720×720** WebGL canvas. A comment says480×480, but assignments and viewport are720.
- Creates separate shaders, buffers and textures. Reloads all six image sources; image decode failures still increment the loaded counter, keeping the initial gray placeholder texture.
- Produces200 frames, stepping angle1.8° **before** each frame: first1.8°, last360°. Type2 also steps its sinusoidal phase before each frame.
- Encodes canvas with `toDataURL('image/jpeg',0.85)`, returns index/data pairs in batches of10 as `{t:'b',f:[{i,d},...]}` through `ReactNativeWebView.postMessage`, and finishes with `{t:'d',n:200}` after releasing the offscreen GL context.
- Catches export errors and posts `{t:'e',m:error.message}`. The caller dispatches each frame to the supplied callback (`fn17459/17460`), resolves on completion and rejects on error.

Successful `handleSaveVideo` opens a filename input dialog, adds `.MP4` (`fn17648 +0x111/+0x115`), checks `Utils.isMediaFileExist` (`+0x13c/+0x147`), then calls `Utils.moveVideoToDCIM` (`fn17649`) with destination name, cached source and result callback. A duplicate name shows `name_exist` and reopens the name dialog; failure shows `export_failed`; success shows `export_success` and calls navigation.goBack after1second (`fn17650/17651`). Cancelling deletes the cached video (`fn17648 +0x3f/+0x4c`). The log text says “cancel to convert and upload,” but the traced success code here **saves MP4 locally**; that string alone does not prove immediate device upload or .bin creation. The common media/gallery pipeline covers later conversion.

## Failure checks and limits

The screen has no device-model check in its complete function/callback subtree; it constructs ordinary images/WebGL/MP4. No special firmware command for “3D Box” is proven. Device-family specifics enter a later media converter, not this renderer.

`tryStart` polls readiness up to200 attempts with100ms retries, then rejects with `webview not ready` (`fn17461`); a separate60000ms timeout rejects with `timeout` (`fn17462`). WebView `onError` logs its native error (`fn17465`). The readiness handlers set their ref true for any message whose `t` is`r`; they do not inspect the `ready` Boolean in the polling message (`fn17464 +0x30; fn17459 +0x145`). Because the polling JavaScript posts `{t:'r',ready:!!window.__spinningBoxReady}`, an `r` with false can set the caller's readiness ref true. Injection still checks the HTML-side readiness and can return `not_ready`, so this is a statically demonstrated weakness, not evidence that it occurred on the user's phone.

The image-picker dirty flag controls a confirmation on leaving (`fn17684/17656`). Style changes alone do not set that dirty flag in the traced button callbacks. Image readiness, WebGL availability, actual Android media permissions, FFmpeg success, and physical playback remain runtime-dependent.

## Controlled source execution

[spinning-box-replay.mjs](spinning-box-replay.mjs) runs the exact extracted inline renderer for types0,1,2 with synthetic DOM/WebGL/Image/timer interfaces; [spinning-box-replay.json](spinning-box-replay.json) retains outputs. All three cases emit20 batches of10 frames and completion200; calls carry720×720 and JPEG quality0.85, first angle1.8°, final angle approximately360°. Type2 distances range approximately20.000..30.000. Initialization and one explicit step also verify the actual vertex/angle calculations. The GL API is mocked, so these results establish control flow and numeric parameters only, **not pixel output or visual quality**.

Reproduce offline extraction and this controlled probe:

```bash
.venv/bin/python docs/evidence/android/features/spinning-box-extract.py
node docs/evidence/android/features/spinning-box-replay.mjs
```

The extractor verifies the exact bundle hash and retains73 function ranges plus five original strings. It executes no APK or renderer. The Node probe executes extracted renderer source within a fresh synthetic VM; it performs no image fetch, Android operation, or network request.
