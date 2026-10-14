# Newer HTTP/WebSocket display protocol

The APK contains a second device protocol alongside the legacy TCP protocol. Its JavaScript `ConnectionManager` talks HTTP to port **80**, exchanges JSON playback/heartbeat messages over WebSocket port **9000**, and uploads files to `/DCIM/upload`. The default host is **192.168.4.1**. These are shipped-code observations; no connection to a display was attempted, and this report does not establish that the user's Mini11 supports these endpoints.

Target identity: APK SHA-256 `8a83b1f128beb43341eefd2b4ad743512d0193ff6dd4e7b56feba138fb4b63c9`; Hermes96 bundle SHA-256 `8389750af87d60e75bbd7d93ba57d1bd239008812c8c5ef7ecc84cf2a46777e2`. Original selected function disassembly is in [http-bytecode.hasm](http-bytecode.hasm); [http-index.json](http-index.json) retains **167 function IDs, offsets, sizes, and hashes of exact raw bytecode**. [http-strings.json](http-strings.json) retains **559 referenced strings**, each with physical bundle range and hash. [http-commands.json](http-commands.json) supplies the structured command/payload/response table and per-row raw-byte anchors.

## Connection and initial status

Constants module 490, function **5334**, assigns IP `192.168.4.1` and PORT `80`. ConnectionManager module **784**, constructor **9052** (`0x29b126`), initializes `gotSession=false`, separate newer/legacy connection flags, timestamps, host, and callbacks. `getHttpPort` **9081** (`0x29bfa0`) reads that constant; it does not select a different HTTP port by model. `setHost` **9079** (`0x29bf5b`) stores the supplied host, calls API.setHttpInfo(host,port), and immediately calls requestSession. LAN discovery/host selection is traced separately.

1. `requestSession` **9065** (`0x29b95b`) constructs `http://HOST:80/ctrl/session` and calls generic API.GET directly, bypassing the ConnectionManager session gate. Callback **9066** (`0x29b9b8`) requires transport success, a response object, and `response.code === 0`.
2. On that success it calls `requestInfo` **9063** (`0x29b7df`), another direct API.GET to `http://HOST:80/info`. Callback **9064** (`0x29b83c`) copies accepted response to `deviceInfo`, timestamps receipt, and announces newer connection. Its admission rule is permissive: transport success, truthy response, and response code falsy or unequal to 1. A response with `code===1` invokes resetToDefault and fails admission. Thus `/info` is not checked identically to other commands.
3. Callback **9067** (`0x29baa5`) makes `gotSession` equal to requestInfo's success. Session success alone is insufficient.
4. The timer path starts immediately, then repeats `checkConnect` every **3000 ms** (9087 `0x29c178`). When session is missing, **9072** (`0x29bc5c`) requests it; on success **9073** starts/checks WebSocket. When session exists, checkWebsocketConnect **9070** (`0x29bbc6`) starts a missing socket or, for a non-OPEN/non-CONNECTING socket, stops it and schedules restart in **2000 ms**.
5. `startWebsocket` **9054** (`0x29b264`) refuses to start without gotSession, then constructs `new WebSocket('ws://'+host+':9000')`. It supplies no path, subprotocol, token, or custom header argument in this retained constructor. The 5000 ms timer **9055** only logs timeout; it does not abort a stalled CONNECTING socket. `onopen` **9056** clears that timer, resets heartbeat timestamps to 0, and calls `requestPlayInfo`.
6. `requestPlayInfo` **9061** (`0x29b6ec`) calls session-gated GET `/ctrl/play?action=status`; callback **9062** copies a `code===0` response into playInfo and notifies listener. Unlike the WS update handler, this HTTP callback does not GBK-decode `current`.

No explicit session token is read from `/ctrl/session` or attached to subsequent commands in the examined JavaScript; `gotSession` is a client boolean. This does not prove how the server identifies sessions or what platform HTTP cookie behavior does.

## File-list request and filename encoding

`requestDeviceDCIM` **9134** (`0x29d6ed`) first chooses newer HTTP versus legacy getFileList using getIsOldDevice. The HTTP branch calls GET **`/DCIM`**. Callback **9135** (`0x29d73e`) requires transport success, response, `code===0`, and truthy `files`; it treats `response.files` as an array of encoded strings. Map callback **9136** (`0x29d7ea`) produces `{index:arrayIndex,name:Utils.decodeGBKHexString(encodedName)}`. Failure sends an empty list to the formatting callback. This is not directory scanning inside the app: the device's response supplies the filenames.

`decodeGBKHexString` **7839** (`0x27bc77`) iterates the string in steps of 2, applies `parseInt(substr(i,2),16)`, creates Buffer.from(byteArray), then uses iconv.decode(buffer,'gbk'). Its counterpart **7837** (`0x27bbb3`) calls iconv.encode(name,'gbk'); map callback **7838** (`0x27bc52`) uses byte.toString(16).padStart(2,'0'), joined without separators. Hex is lowercase. The helpers return `''` for falsy input and do not validate even length or hex characters explicitly.

An independent Python GBK reference gives `13_tractor.bin` → **`31335f74726163746f722e62696e`**. This example demonstrates the recovered algorithm, not a captured message. ASCII names retain every character through this encoding; it does not impose an 8.3 filename limit.

The UI calls this list route after connecting: DevicePage registers callbacks in **12340** (`0x2eda54`); connection listener **12341** (`0x2edb6e`) calls `loadConfig(true,false)`. `loadConfig` **12254** (`0x2eb6ee`) checks `CONN.isConnected()`, invokes its getDCIM closure when its first argument is true, and loads all settings. `getDCIM` **12268** (`0x2ebbd5`) checks connectivity again and calls requestDeviceDCIM. File-list callback **12343** (`0x2edc9b`) feeds the displayed state; equality callback **12344/12345** suppresses a redundant update only when every item's index, name, and displayName match. This supplies a real caller chain for initial listing rather than merely a declared endpoint.

Shared formatter **9132/9133** (`0x29d5d9` / `0x29d631`) maps names without filtering entries: matching `^(.{2})[-_](.*)\.bin$` becomes `PREFIX.REST`, otherwise a lowercase `.bin` suffix is removed. It also records matching two-character identifiers. Thus an HTTP response containing the encoded tractor name would produce **`13.tractor`**. Existing short aliases from a device remain whatever names the device reported; this decoder does not reconstruct a long FAT name.

## Commands constructed by the app

All paths below use `http://ConnectionManager.host:80`. State-changing operations often use GET, exactly as shipped. These are protocol descriptions; none were sent during analysis.

| Operation | Method and route | Important payload/result |
|---|---|---|
| Obtain session | GET `/ctrl/session` | `code===0`, then `/info` |
| Device info/model | GET `/info` | Stores full accepted response; later getModel reads `.model` |
| Quit | GET `/ctrl/session?action=quit` | `code===0` clears newer connection state |
| Playback status | GET `/ctrl/play?action=status` | Copies full `code===0` response |
| Files | GET `/DCIM` | `files` array contains GBK hex filename strings |
| Play file | GET `/DCIM/HEX?act=play` | HEX is GBK hex of file.name |
| Delete file | GET `/DCIM/HEX?act=rm` | Same filename encoding |
| Previous | GET `/ctrl/play?action=previous` | Does not construct a next route in this helper |
| Pause | GET `/ctrl/play?action=pause` | No resume route in this helper |
| All config | GET `/ctrl/get?k=all` | `data` passed as configuration array |
| One config | GET `/ctrl/get?k=KEY` | SettingsPage consumes returned fields/value |
| Write config | GET `/ctrl/set?KEY=VALUE` | Direct concatenation; neither key nor value URL-encoded here |
| SD format | GET `/ctrl/card?action=format` | SettingsPage's format confirmation action sends it |
| File upload | POST `/DCIM/upload` | Multipart name and file, details below |

Anchors: play **9112** `0x29cfc9`; previous **9116** `0x29d115`; pause **9120** `0x29d21a`; delete **9124** `0x29d2d1`; setConfig **9128** `0x29d3cf`; loadAllConfig **9137** `0x29d813`. SettingsPage's direct set/get callers are **15346** `0x33cf25` and **15349** `0x33d095`; format URL is selected by **15354** `0x33d25a` and sent by confirmed action **15356** `0x33d40d`. That format response callback merely dismisses the loading overlay; it does not check `.code` itself.

Normal ConnectionManager GET/POST wrappers (**9092/9095**) refuse requests without gotSession; response `code===1` resets connection state, and most success paths require `code===0`. Session/info/quit bypass these wrappers intentionally. Generic API module **729** runs queued fetch helpers with `Content-Type:application/json`, JSON-stringifies truthy bodies, demands HTTP `response.ok`, and parses response.json(). GET timeout is **3000 ms**; generic POST timeout **5000 ms**, using AbortController. API.GET callbacks receive `(true,parsedJson)` or `(false,localized network error)`. No concrete generic JSON POST device-control route is called in the retained ConnectionManager; its concrete POST use is multipart upload. The generic API.POST success callback **7522** accesses global `response.data` rather than its resolved argument, a static defect in that unused generic path.

The configuration schema is driven by returned config objects (`key`, `code`, `desc`, `type`, `ro`, `value`, optionally `opts` or numeric `min/max/step`). Hardcoded legacy fallback objects include `ble`, `switcher`, `loop`, `brightness`, **`volum`** (spelling preserved), `angle`, and `ssid`; those fallback objects are not evidence that every newer firmware exposes the same keys/ranges.

## Upload variants

`uploadFile` **9105** (`0x29cb84`) routes to legacy upload for an old device, otherwise ConnectionManager.POST_UPLOAD_FILE **9098** (`0x29c6b1`). This checks gotSession and builds `http://host:80/DCIM/upload`, passing filename through encodeGBKToHexString to generic API.POST_UPLOAD_FILE **7525** (`0x274941`).

The helper creates XMLHttpRequest and FormData:

```text
POST /DCIM/upload
FormData:
  name = GBK_HEX_FILENAME
  file = {uri: LOCAL_URI, type: application/octet-stream,
          name: GBK_HEX_FILENAME}
Headers: Cache-Control: no-cache; Pragma: no-cache; Expires: 0
XHR timeout: 3600000 ms
```

`onprogress` **7526** passes `round(loaded/total*100)` when lengthComputable. `onload` **7527** requires HTTP **200**, parses responseText as JSON, and yields `(true,json)`; non-200, malformed JSON, network error, or timeout reports failure. ConnectionManager's callback **9099** additionally requires `json.code===0`, otherwise fails and reacquires session on code 1. `uploadFileToDevice` **9103** (`0x29c9ac`) targets an explicit host argument using the same multipart helper and callbacks. This is useful for multiple discovered displays, but does not establish their grouping/discovery rules.

A separate **native V2** path **9109** (`0x29cc3b`) strips leading `file://`, builds the same `/DCIM/upload` URL, and calls:

```text
MIDDLE.callNativeWithPromise(
  MEDIA_MODULE + MIDDLE.MEDIA_FUNC_UPLOAD_V2,
  JSON.stringify({url: URL, name: GBK_HEX_FILENAME, path: LOCAL_PATH}),
  0)
```

The JS `MEDIA_EVENT` listener **9110** forwards `event.progress || 0`; promise result's `.result` goes to postResult **9111**, defaulting false when missing. Listener removal is present on success and error. This generator does not perform the same explicit gotSession check as XHR wrapper 9098. The JSON above is **bridge input, not an HTTP JSON body**. Native V2's exact wire body is not proven by the JS trace; the multipart format above is independently established for XHR. Focused REA native dispatcher inspection returned a provider prerequisite error (`REA_JADX_MCP_JAR` absent from MCP environment), retained in [http-native-provider-unavailable.json](http-native-provider-unavailable.json). Existing APK identity/manifest/REA evidence was reused; no tooling registration or target execution was changed.

## WebSocket messages and connection decisions

The one retained outgoing WS message is:

```json
{"msgId":"<String(Utils.getRandomTime8())>","cmd":"heartbeat"}
```

checkConnect **9072** sends it only while OPEN and elapsed time since last send is **greater than 15000 ms**. With the 3000 ms polling interval, observed timing would be quantized by polling; this is not a captured timing measurement. A previously nonzero receive timestamp older than **20000 ms** marks newer connection false, preserving legacy connectivity.

Receiver **9057** (`0x29b44c`) immediately JSON.parse(event.data), without a try/catch in this function. It recognizes exactly two cmd strings:

- **`heartbeat`**: refreshes lastHeartBeatRecvTs, announces newer connection true, preserves legacy status. It does not validate response code or msgId.
- **`onPlayInfoUpdate`**: copies the message, overrides `code` to **0**, replaces `current` with GBK-decoded message.current, stores playInfo, refreshes receive timestamp, and invokes play-info callback. Other fields are preserved. `current`, `progress`, `state`, and `total` are consumed elsewhere; synthetic legacy compatibility status uses state `ing`/`idle`. Their entire newer-server schema is not established by a retained real reply.

Other cmd values are ignored here. `onerror` and `onclose` handlers log only; timer checks recover connection later. resetToDefault **9074** closes/nulls WS, clears both booleans/session/model/current/timestamps, and posts connection/playback updates. getIsOldDevice **9141** returns false when newer connected, else uses legacy connection status; newer protocol therefore takes precedence when both are connected. getModel **9142** returns deviceInfo.model when newer connected and nonempty, otherwise **F1** (or the legacy model when legacy is selected).

## What this adds to the missing-file investigation

The APK supports two genuinely different file-list transports. In the newer path, the device explicitly returns encoded filenames via HTTP JSON; the app decodes all returned names and forwards them without extension/model filtering. In the legacy path, another report establishes binary framing defects. A captured reply or known active transport remains necessary to attribute the user's missing tractor entry to a specific mechanism. The newer path's GBK hex and display-name formatting themselves do not omit `13_tractor.bin`.

## Coverage and limits

Answered statically: newer initial handshake, request wrappers, WS handshake/heartbeat/status messages, all ConnectionManager file/control routes, direct SettingsPage config/format routes, XHR upload wire construction, native V2 bridge input, and filename encoding. Exact bytes and hashes are retained, rather than merely matching endpoint strings. No model-specific filename filtering occurs in examined list handlers.

Bounded unknowns: actual firmware support and live responses; server session binding/cookies; newer server's full info/config/event schema; native V2 HTTP implementation; protocol traffic outside these modules; BLE/AP/UDP discovery/provisioning and legacy TCP internals covered separately. `/DCIM/album.json` exists as a **local app storage path** in Utils and is not an observed device HTTP endpoint. Media-to-bin encoding happens in app/native conversion code; no device-side encode/transcode HTTP endpoint was found in the retained ConnectionManager/SettingsPage/API route construction. This is a bounded negative result, not proof that firmware has no such endpoint.
