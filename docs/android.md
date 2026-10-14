# Android APK evidence and the missing tractor entry

The separate [design-feature report](android-features.md) traces Text Ball,
Box, Marquee, 360 Text and Gallery, including preserved renderer scripts,
offline rendered samples and their connection to the device-family converter.
The [communication report](android-protocol.md) additionally traces discovery,
connection setup, legacy ASCII controls, HTTP/WebSocket operations and the native
upload boundary.

The supplied APK is `com.sp.holographic`, version **1.0.85**, version code **105**.
Its React Native application logic is compiled into a **Hermes 96** bytecode
bundle. The investigated receive/display path does not discard tractor-style
filenames. The SD copy of `13_tractor.bin` is structurally valid and matches the
local file byte-for-byte. The later live notification contains the tractor entry but a malformed earlier
record causes the recovered APK parser to stop before reaching it. Its subsequent
unanchored status match also produces the false F1. [Exact captured bytes and
parser replays](evidence/android/live/packet-findings.md) establish both failures.
The CLI now recovers those later entries and reads the real final Mini11 field.

The sections below retain the initial static investigation and its then-open
questions. The later [live report](evidence/android/live/device-findings.md) and
[operational CLI](device.md) supersede statements that runtime captures or network
functions were unavailable. The card was subsequently formatted at the user's
explicit request; clean listings and successful protocol uploads followed.

The user clarified that **neither `13…` nor `14…` appears** after reconnecting;
the app shows only the earlier reported labels (`00.B`, `01CHRI~1`, `01.LC`,
`02FATH~1`, and `04in171212.`). That is a broader incomplete-list symptom.

## Artifact identity, tools, and scope

| Artifact | SHA-256 |
| --- | --- |
| `5D-Holo-android.apk` | `8a83b1f128beb43341eefd2b4ad743512d0193ff6dd4e7b56feba138fb4b63c9` |
| `assets/index.android.bundle` | `8389750af87d60e75bbd7d93ba57d1bd239008812c8c5ef7ecc84cf2a46777e2` |

[artifact-manifest.json](evidence/android/artifact-manifest.json) records all ZIP
members and selected DEX/native/bundle identities. The decoded
[AndroidManifest.xml](evidence/android/AndroidManifest.xml) declares min SDK 24,
target SDK 35. REA/JADX package inspection is retained in
[rea-package.json](evidence/android/rea-package.json), evidence
`ev_3752373f87d75ea7839bdf6aeeb3985a776f766242fb6617fda171ffcbbfbd53`.
The provider reports 14,384 classes and 2,109 package resources. Signature
verification and Android execution were not performed.

The connected REA server initially lacked its JADX provider. Analysis continued
through the existing REA CLI with a local `jadx-headless-mcp` 0.7.1 JAR and the
supplied JDK 25.0.4.1. Package inspection and exact class/method inspection
succeeded. A broad class-name inventory failed REA's duplicate/count consistency
check; [the limitation](evidence/android/rea-class-search-limitation.json) is
preserved rather than treating that inventory as complete evidence.

Hermes was disassembled/decompiled using **hermes-dec 0.1.6**. This tool's
[documentation](https://github.com/P1sec/hermes-dec) describes its pseudocode
limitations. Behavior claims are anchored to focused instructions and source
byte ranges in [file-list-bytecode.hasm](evidence/android/file-list-bytecode.hasm)
and [file-list-functions.json](evidence/android/file-list-functions.json).
These are independent shell-tool observations, not REA-produced Android method
records. Function IDs/offsets are specific to the exact bundle hash above.

No Android app was launched, no network command was sent to the display, and no
SD-card files were renamed, uploaded, deleted, or modified during this pass.
Scope covers device presets, conversion dispatch, file-list receive/parsing,
filename formatting, and the list's state/rendering path. It does not claim a
complete reconstruction of every app subsystem or native conversion routine.

## What the APK adds to the device-family knowledge

The detailed [family findings](evidence/android/family-findings.md),
[24-profile table](evidence/android/family-profiles.json), and
[family instructions](evidence/android/family-bytecode.hasm) establish:

- Legacy `_parseModel`, function **#9291**, maps the response flag **`7` to
  `F-MINI11`**. `getConfigByModle`, **#8259**, supplies **48 LEDs, 300 lines,
  five color bits**, matching the CLI's tested type-7 profile.
- `F-MINI12` uses the same dimensions but supplies **17 per-LED brightness
  factors**. Mini11 supplies none. This explains how the manual and connected
  app can use different Mini labels without requiring different sampling geometry;
  it does not establish that the names are universally interchangeable.
- Conversion **#8328** uses **20 fps BGR24** video and **32 kHz unsigned 8-bit
  mono** audio. This independently corroborates the CLI's 1,600 audio bytes per
  frame. Android uses a raw audio intermediate; desktop uses a WAV intermediate.
- **#8332** forwards geometry and media paths, audio presence, optional per-LED
  correction, and zero-valued gamma/brightness parameters to native conversion
  through `NativeModules.Middle`. Native packing/gamma/header/trailer behavior
  is not established by these JavaScript calls alone.
- The native bridge's [getConstants REA record](evidence/android/rea-middle-constants.json)
  and [callNativeWithPromise record](evidence/android/rea-middle-dispatch.json)
  corroborate the dispatch boundary. Their evidence IDs are
  `ev_0f7d1c25824b6fd989c559586eea623b13df3a835e363cc398a4bfbd6dd3956f`
  and `ev_a1463a14f0fc983724b921ee3e7e93cfaba889a1ca69ee11789331367c1bee77`.
- Legacy defaults are **192.168.4.1**, command port **5233**, upload port **5499**.
  Newer devices use an HTTP `/DCIM` listing path, `/DCIM/upload`, and a WebSocket
  on port **9000**. Runtime connection state selects which path is active.

Some Android model names have different geometry from the desktop legacy
encoder: F3, F4, Mini20, 360B, and 360C. The report keeps those Android presets
separate. The established CLI mappings were not changed based on table order
or model-name similarity.

## The tractor file passes the recovered format checks

[tractor-file.json](evidence/android/tractor-file.json) records a direct read-only
comparison of the card's files with local outputs and preloaded files.
[tractor-findings.md](evidence/android/tractor-findings.md) gives the interpretation.

| Check | `13_tractor.bin` | Working `14_cd.bin` |
| --- | ---: | ---: |
| Header/profile | valid type 7 | valid type 7 |
| Header bytes | 764 | 772 |
| Complete records | 238 | 9 |
| Record bytes | 28600 | 28600 |
| Duration at 20 fps | 11.9 s | 0.45 s |
| Zero trailer bytes | 100000 | 100000 |
| Total bytes | 6907564 | 358172 |
| Matches local source | yes | yes |

Tractor SHA-256 is
`7267a68ae34cb2da2166befafa806b5526a863445c640d444ca1e8003ce9c3c5`.
Its size satisfies `764 + 238*(27000+1600) + 100000`. Ten preloaded videos pass
the same standard-format checks; some are larger than tractor. Thus neither
an incomplete copy, wrong type marker, malformed header, missing trailer, nor
misaligned records is supported by this evidence. Structural validity alone
does not prove how firmware enumerates files or validates playback.

## Filename shortening and punctuation are separate operations

The [earlier VFAT snapshot](evidence/sd-card-filenames.json) directly established
that the card stores `13_tractor.bin` with short alias **`13_TRA~1.BIN`**.
The APK adds the explanation for punctuation such as **`00.B`**:

1. ConnectionManager's **#9132** `_handleDeviceFileList`, bundle offset
   `0x0029d5d9`, maps every input entry and calls the file-list callback.
   It contains no filename-based `filter` in this receive/display path.
2. Its mapper **#9133**, offset `0x0029d631`, matches
   `^(.{2})[-_](.*)\.bin$` with **no case-insensitive flag**. Matching names
   become `prefix + '.' + remainder`; the prefix also enters usedIdentifierSet.
3. Otherwise a lowercase `.bin` suffix is removed; other names are retained.

| Incoming name | App displayName |
| --- | --- |
| `00_B.bin` | `00.B` |
| `01_LC.bin` | `01.LC` |
| `13_tractor.bin` | `13.tractor` |
| `13_TRA~1.bin` | `13.TRA~1` |
| `13_TRA~1.BIN` | `13_TRA~1.BIN` |
| `14_CD.bin` | `14.CD` |

Uppercase `.BIN` changes formatting, but **does not drop the entry**. The exact
case returned by the user's display has not been captured. Therefore the FAT
alias alone does not explain omission of tractor and CD. Short filenames can
improve labels; renaming is not yet a demonstrated fix for the missing entries.

The traced screen update also retains the received array: **#12343–#12345**
compare old/new entries to avoid unnecessary state updates, and otherwise set
the complete new list. **#12253** DevicePage supplies that state to SwipeListView;
**#12323** renders `item.displayName`. **#12360** uses `item.index` as the UI key.
Corrupted/duplicate indices are an additional possible issue, but no actual
duplicate indices or React runtime failure were observed.

## A concrete weakness in the legacy response parser

### Why the model label can change to F1, and why tapping it does nothing

The user subsequently reported that the model header changed from F-Mini11
to **F1**, and that the apparent selector does nothing when tapped.
Both behaviors are explained by the inspected code, with the precise live
trigger for F1 still requiring a response/log capture:

- **#7128 HeaderViewHome**, bundle base `0x00267fc8`, renders the model title
  inside TouchableOpacity and assigns `props.onLeftPress` to its onPress.
  **#12253 DevicePage** passes the current `CONN.getModel()`-derived model as
  `leftTitle` and supplies **#12359 onLeftPress** as the handler. That handler,
  base `0x001a6f5b`, is only four bytes: `LoadConstUndefined r0; Ret r0`.
  It opens no picker, changes no state, and sends no model-setting command.
  The model heading on this page therefore has a pressable appearance with
  an explicitly empty action, rather than functioning as a manual model selector.
- The legacy constructor **#9266** initially sets `model='F1'`. Connection reset
  **#9280**, base `0x002a1743`, also restores F1. ConnectionManager **#9142**
  returns F1 when no usable device model is available. F1 can thus appear during
  disconnect/reconnect without any decoded model flag being received.
- **#9292 _parseFileList** initializes its model result to F1 at relative
  `0x250`. If the status/model-tail regex does not match, it publishes that
  default at `0x2a6` and stores it on the client at `0x2bc`. If a tail matches
  but its flag is unrecognized, **#9291 _parseModel** also returns F1.
  The valid flag `7` returns F-MINI11; flag `1` explicitly returns F1.

The controlled replay now includes a complete synthetic three-file list with
an unrecognized five-byte status/model tail. It retains all three names but
publishes **model=F1**. This establishes the fallback mechanism, not that those
exact bytes arrived from the user's display.

Inference: given the prior Mini11 identification, successful type-7 playback,
and malformed/incomplete list, the new F1 label is consistent with unavailable
or misparsed device status. It is not sufficient evidence to change the CLI's
verified device type 7 to type 1. The live reset/parser/flag trigger remains
unobserved.

The legacy path is:

```text
TCP socket 'data' callback (#9276)
  -> _handleData (#9290)
  -> _parseNotify (#9293)
  -> _parseFileList (#9292)
  -> ConnectionManager callback (#9083)
  -> name mapper (#9132 / #9133)
  -> screen state (#12343–#12345)
  -> SwipeListView / displayName
```

**#9290**, offset `0x002a1b04`, directly forwards the current receive buffer.
There is no receive accumulator in that function or its socket callback.
**#9293**, offset `0x002a1e91`, accepts only a buffer of at least 17 bytes with
ASCII **`c30c38` at its beginning** and **`a4a8c2e3` at its end**. It passes that
whole buffer to **#9292**, offset `0x002a1bb9`.

TCP supplies a byte stream, so response boundaries cannot be assumed to match
receive-callback boundaries. [RFC 9293](https://www.rfc-editor.org/rfc/rfc9293.html#section-2.2)
defines that transport model. Consequently, split responses can fail both
marker checks, and coalesced responses can be treated as one response.

The file-list parser's observed mechanics are:

```text
parseLimit = buffer.length - 12
offset = 9
length = parseInt(buffer[offset:offset+2] as UTF-8, 10)
index  = parseInt(buffer[offset+2:offset+4] as UTF-8, 10)
nameEnd = offset + length + 2
name = GBK_decode(buffer[offset+7:nameEnd])
next offset = nameEnd
```

It stops when a length/index cannot be parsed or a name range exceeds the
limit. It then **publishes the entries already parsed**, rather than rejecting
an incomplete list and retaining a known-good complete list. This behavior is
visible at #9292 relative offsets `0x95`, `0xef`, `0xfd`, and publication around
`0x295` onward. The tail is also searched for current index/model/play state.
The three skipped bytes and tail layout are parser assumptions; their actual
firmware contents have not been captured.

## Controlled offline replay

[replay_android_file_list.mjs](../tools/replay_android_file_list.mjs) executes the
selected **decompiler state machines** against local synthetic inputs.
[file-list-replay.json](evidence/android/file-list-replay.json) records inputs,
outputs, logs, and limitations. This is not execution of APK bytecode or a
recording of a real display response.

The source snippets are retained verbatim. The harness supplies local Buffer,
GBK, logging, and model-decoding dependencies; registers are declared per
function. One invalid variadic logging-call rendering from hermes-dec is repaired
using #9292's raw `Call` instruction at `0x17a`. That repair concerns diagnostics,
not the returned file list. The synthetic three-byte record prefix is a placeholder.

Observed replay results:

| Input condition | Result |
| --- | --- |
| Complete synthetic response containing B, tractor alias, CD | all three entries retained |
| Same response split into two 36-byte receives | zero list updates |
| Invalid length field before tractor | publishes only the earlier B entry |
| Two complete responses combined into one receive | appends a spurious entry `{index:71,name:''}` |
| Tractor/alias/uppercase-extension formatter inputs | every entry retained |

These demonstrate mechanisms that can explain an incomplete or odd-looking
list. They do not identify which mechanism produced `04in171212.` or establish
that the real response contains tractor at all.

## Remaining evidence needed and a prepared capture tool

The unresolved distinction is **firmware returns an incomplete/indexed list**
versus **the APK loses or misparses entries present in the response**. During the
card comparison, the SD card was mounted on the computer. At the final check
it was no longer mounted; the computer remained on its normal LAN, with
192.168.4.1 routed through the LAN gateway. No display connection was attempted.

A prepared [capture tool](../tools/capture_legacy_file_list.py) sends only the
exact heartbeat observed in APK **#9294** (`c31c38abca4a8c2e3`) to its declared
legacy endpoint. It saves both original receive chunks and the joined stream.
After returning the SD card to the display and connecting the computer to the
display's Wi-Fi, run:

```bash
python3 tools/capture_legacy_file_list.py --output analysis/android/file-list-capture.json
```

This does not upload files, delete files, format the card, or issue playback
controls. It has not yet been run against the display. Its receive boundaries
will belong to the computer's connection, not necessarily the Android app's.
Raw responses can still establish whether names such as `13_TRA~1` and `14_CD`
are returned and whether their lengths/indices match the APK's assumptions.
If a complete computer response parses correctly while Android still truncates,
an Android-side log/network capture would be needed to prove the precise failure.

The provided APK's version is known; equality with the currently installed phone
app version has not been independently checked. Repeated Wi-Fi upload failure
also remains undiagnosed. The current free-space observation does not support
a presently full SD card.

## Reproduction

```bash
.venv/bin/pip install hermes-dec==0.1.6
python3 - <<'PY'
from pathlib import Path
import zipfile
directory = Path('analysis/android')
directory.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile('5D-Holo-android.apk') as apk:
    (directory / 'index.android.bundle').write_bytes(apk.read('assets/index.android.bundle'))
PY
.venv/bin/hbc-disassembler analysis/android/index.android.bundle analysis/android/bundle.hasm
.venv/bin/hbc-decompiler analysis/android/index.android.bundle analysis/android/bundle.pseudo.js
python3 tools/select_hermes_evidence.py
node tools/replay_android_file_list.mjs
```

The local JADX JAR comes from its
[official 0.7.1 release](https://github.com/1013503897/jadx-headless-mcp/releases/tag/v0.7.1),
SHA-256 `6e5eacf500b64292bfb73c49797c1958f6ee44646e43e868039ae7feb573ff75`.
For REA CLI package inspection, set `JAVA_HOME` to the supplied JDK path and
`REA_JADX_MCP_JAR` to that local JAR, then run `rea inspect-android-package`
with the exact APK path and JSON output. The retained REA records include all
provider/tool identities, raw responses, coverage, and limitations.

## Question audit

| Question | Status |
| --- | --- |
| APK identity and application architecture | answered from artifact |
| Mini11/Mini12 geometry and family presets | answered from focused bytecode |
| Android media intermediate formats and native dispatch | answered; native encoder internals unexamined |
| Why tildes and `00.B` appear | aliases observed; app punctuation transform answered |
| Whether tractor was copied incompletely or has a standard-format defect | checked; no such defect found |
| Whether the traced app list path filters tractor by its filename | checked; no such filter found |
| Concrete legacy parser failure mechanisms | demonstrated statically and in bounded synthetic replay |
| Exact reason this display's real list omits tractor and CD | captured malformed record + original-parser replay explain omitted later entries; upstream corruption cause unknown |
