# Android device-family findings

Evidence scope: static inspection of the APK's actual Hermes bytecode, not an Android runtime capture. APK SHA-256: `8a83b1f128beb43341eefd2b4ad743512d0193ff6dd4e7b56feba138fb4b63c9`. The extracted `assets/index.android.bundle` uses Hermes bytecode version 96. [family-profiles.json](family-profiles.json) records its hash and exact return offsets; [family-bytecode.hasm](family-bytecode.hasm) retains focused instruction excerpts. Function-relative offsets below refer to that bytecode; absolute bundle offset is function base plus relative offset. Pseudocode was used to navigate, while claims below are tied to instructions and decoded constant buffers.

## F-Mini11 and the manual's Mini12 label

Observed: Hermes function #9291 `_parseModel`, base `0x002a1b18`, compares the model flag with ASCII `7` at relative `0x75` and returns `F-MINI11` at `0x83`. It accepts a one-character flag directly or takes character index 1 of a longer string. Other supported legacy flags are `1` → F1, `2` → F2, `Z` → F5, `4` → F-MINI18. Unknown flags default to F1. This is a legacy response-to-model decoder, not a complete numeric profile enum.

Observed: function #8259 `getConfigByModle`, base `0x0028e3dc`, uppercases its input, compares F-MINI11 at relative `0x101`–`0x105`, branches to `0x143` (absolute `0x0028e51f`), and returns `lights=48`, `lines=300`, `colorDeep=5`, `brightnessN=0`, `brightnessValues=[]`. This corroborates the existing CLI's type-7 geometry. F-MINI12 branches at `0x6d`–`0x71` to `0x279` (absolute `0x0028e655`) and returns the same geometry, with `brightnessN=17` and the 17-value array listed below. The function is passed an `isOldDevice` second argument by its callers, but its body only loads the first argument.

Inference: Mini11 and Mini12 presets share sampling dimensions in this app; the paper label alone does not establish a different required frame geometry. The user's reported F-Mini11 app label and confirmed type-7 playback support choosing Mini11. No model-response bytes were captured: that label can come from the legacy flag decoder or the newer HTTP deviceInfo.model field, so it does not identify the active transport. This does not prove that every product sold as Mini12 has identical firmware or output format. See [discovery and connection evidence](comms/discovery-findings.md).

## Conversion path

Observed: function #8328, base `0x0028ffb7`, is the generator body of `convertOneMedia`. Relative `0x1d3` onward constructs video FFmpeg arguments; `0x248`–`0x25c` add `-r 20`, `-pix_fmt bgr24`, `-f rawvideo`; `0x2d4` calls FFmpegKit.execute. The audio command at `0x317` onward adds `-vn`, `-c:a pcm_u8`, `-ar 32000`, `-ac 1`, `-f u8` and executes FFmpegKit at `0x3f2`. Thus video intermediates are BGR24 at 20fps, and audio intermediates are unsigned 8-bit mono 32000Hz. Arithmetic gives 1600 audio samples per 20fps frame, independently agreeing with the desktop converter. The intermediate audio is raw u8, unlike the desktop WAV intermediate.

Observed: #8332, base `0x00290424`, is the generator body of `handleAndConvertMedia`. It obtains the model config and writes a JSON object containing `have_audio`, `is_360`, `frames_resized_file`, input dimensions, audio/output paths, radius/center, lights/lines/colorDeep, gamma/min_brightness/change_brightness_lights. It initializes the last three fields to zero. `brightnessN` and its array are checked at `0x21a`–`0x289`; a positive preset adds `per_led_brightness` at `0x44a`. F-S20PRO additionally forwards `spiWays=7`. Relative `0x4cb`–`0x509` selects MIDDLE.callNativeWithPromise and calls it with `MEDIA_MODULE + MEDIA_FUNC_CONVERT`, JSON.stringify(config), and 0.

Observed: #5326, base `0x002333b9`, reads NativeModules.Middle. #5328, base `0x0023348c`, constructs MEDIA_MODULE from Middle.PROTOCOL + Middle.MODULE_MEDIA + '/'. These are native bridge calls. This focused Hermes pass establishes inputs and dispatch; it does not reconstruct native header construction, BGR packing/gamma internals, trailer, or actual native upload behavior. In particular, geometry agreement does not establish byte-for-byte Android/desktop export equivalence.

The per-LED factors are `[0.46, 0.47, 0.48, 0.49, 0.5, 0.55, 0.6, 0.75, 0.8, 0.85, 0.88, 0.9, 0.92, 0.95, 0.98, 0.98, 0.98]`.

## Presets retained in Android

All entries are exact returned constant objects in #8259; `lines`/`lights`/`colorDeep` are app-native names. `brightnessN=17` means the factors above are forwarded, while zero means no factors are forwarded. The existing Python CLI intentionally reproduces the desktop legacy encoder. Several same-named presets differ between the two supplied applications, so this table should remain separate from the desktop's numeric type mapping.

| Android model | Lights | Lines | Color depth | Brightness factors | Additional config |
| --- | ---: | ---: | ---: | ---: | --- |
| F1 | 116 | 520 | 6 | 0 |  |
| F2 | 144 | 520 | 6 | 0 |  |
| F3 | 176 | 700 | 6 | 0 |  |
| F4 | 192 | 920 | 6 | 17 |  |
| F5 | 133 | 520 | 6 | 0 |  |
| F6 | 224 | 700 | 6 | 0 |  |
| F7 | 256 | 700 | 6 | 0 |  |
| F-384 | 192 | 800 | 6 | 17 |  |
| F-MINI12 | 48 | 300 | 5 | 17 |  |
| F-S12+ | 85 | 400 | 6 | 17 |  |
| F-MINI20 | 80 | 360 | 5 | 17 |  |
| F-MINI20+ | 101 | 360 | 6 | 0 |  |
| F-MINI23 | 96 | 520 | 6 | 0 |  |
| F-S12 | 64 | 520 | 6 | 0 |  |
| F-S15 | 85 | 650 | 6 | 17 |  |
| F-S20 | 106 | 600 | 6 | 17 |  |
| F-S20PRO | 147 | 800 | 6 | 17 | spiWays=7 |
| F-S25 | 128 | 520 | 6 | 17 |  |
| F-360A | 80 | 520 | 6 | 0 | is_360=true |
| F-S360A | 128 | 520 | 6 | 0 | is_360=true |
| F-360B | 192 | 920 | 6 | 0 | is_360=true |
| F-360C | 200 | 900 | 6 | 0 | is_360=true |
| F-MINI11 | 48 | 300 | 5 | 0 |  |
| F-MINI18 | 80 | 360 | 5 | 0 |  |

Same-named differences from the desktop legacy CLI: F3 is 176/700 in Android vs 200/520 in the CLI (lights/lines); F4 192/920 vs 171/450; F-MINI20 80/360 vs 96/360; F-360B 192/920 vs 144/520; F-360C 200/900 vs 200/520. F1/F2/F5/F-MINI11/F-MINI18/F-360A sampling dimensions agree. No Android numeric IDs for the added presets are inferred from table order.

## Network generations

The subsequent [communication report](../../android-protocol.md) traces discovery,
initialization, commands and native upload. Its Ghidra evidence establishes the
legacy sender's actual use of192.168.4.1:5499 and packet framing, beyond the
Hermes-only boundary described in this original pass.

Observed: #5334, base `0x0023377a`, writes constants IP and OLD_DEVICE_IP as `192.168.4.1`, port 80, OLD_DEVICE_UPLOAD_PORT=5499 and OLD_DEVICE_COMMAND_PORT=5233 at relative `0x1bd`–`0x1f2`. In the legacy TCPClient module constructor (full bundle disassembly), those IP and command-port constants are passed to TCPClient. The upload port is a declared constant; this Hermes pass does not establish its use by native code.

Observed: new-generation #9054 `startWebsocket`, base `0x0029b264`, constructs `ws://` + host + `:9000`, creates a WebSocket, and stores it as websocket. #9141 `getIsOldDevice`, base `0x0029da18`, returns false if newModelConnected is true; otherwise it returns whether the legacy TCP client is connected. #9142 `getModel`, base `0x0029da47`, returns the legacy client's parsed model for an old device, otherwise deviceInfo.model for a new connected device, with F1 fallback.

Observed: legacy upload generator #9347, base `0x002a2c3c`, forwards JSON `{name,path}` to MEDIA_MODULE + MEDIA_FUNC_UPLOAD, relative `0x109`–`0x17d`. New upload #9109, base `0x0029cc3b`, constructs `http://host:getHttpPort()/DCIM/upload`, converts name with encodeGBKToHexString, and forwards JSON `{url,name,path}` to MEDIA_MODULE + MEDIA_FUNC_UPLOAD_V2, relative `0xb8`–`0x16f`. This demonstrates two distinct transport paths; no device was contacted to establish which uploads succeed or why uploads fail.
