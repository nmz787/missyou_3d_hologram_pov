# Android discovery and initial connection

This pass statically traces the supplied APK. It does not contact a display, launch Android, or observe a physical Ethernet connection. APK SHA-256 is `8a83b1f128beb43341eefd2b4ad743512d0193ff6dd4e7b56feba138fb4b63c9`. [discovery-index.json](discovery-index.json) records original Hermes function bytes, absolute bundle offsets, byte lengths, SHA-256 hashes, and retained native REA Evidence IDs. [discovery-bytecode.hasm](discovery-bytecode.hasm) retains the actual instruction excerpts; [discovery-extract.py](discovery-extract.py) reproduces them from the existing full disassembly and extracted bundle.

## What the app actually searches

The home page starts `searchLocalNetDeivce(false)` when mounted and when its `research` event arrives (#12353 at bundle offset `0x002edf4b`, #12354 at `0x002edfb5`). This leads to `searchLocalDevices` and `scanLANForInfo`; their generator bodies are #12444 (`0x002f0c36`) and #12433 (`0x002f073f`).

Observed search order:

1. Check the default direct-connection IP **192.168.4.1** by requesting **GET http://192.168.4.1/info**. #12420 (`0x002f03b3`) loads the app's IP constant and calls `checkInfo`. If it returns an IP, #12433 stores a singleton result and returns; it does not scan the LAN afterward.
2. Load cached IPs from storage key **search-foundDevices** and test them with the same `/info` request. #12427 (`0x002f0548`) checks cached addresses in groups of **10** with `Promise.all`, retaining non-null results. If any cached addresses answer, #12433 returns those results and skips the subnet scan.
3. Obtain the phone's local IPv4 address, take its first three octets, and generate **prefix.1 through prefix.254**, excluding its own IP. #12412 (`0x002f016c`) calls NetworkInfo.getIPV4Address; #12408 `guessSubnet` (`0x002f00fe`) performs `split('.')`, `slice(0,3)`, `join('.')`, and appends `.`. #12412's loop uses 1 and 255 as bounds. This is a guessed **/24**, not a subnet derived from the interface's actual netmask. For example, local `192.168.1.40` generates `192.168.1.1`–`192.168.1.254`, excluding `.40`.

`checkInfo` is generator #12416 at `0x002f0280`. Relative `0x44`–`0x66` constructs `http://` + candidate IP + `/info`, passes a **2000ms timeout**, and disables request logging. The shared `fetchWithTimeout` (#7530 at `0x00274cfc`) uses GET by default, sets `Content-Type: application/json`, calls fetch with an AbortController signal, and aborts when the timeout fires. Its response handler #7532 (`0x00274e96`) requires HTTP `response.ok` and parses JSON.

Discovery accepts a non-null JSON result whose **code is the number 0 or 1** and returns only the candidate IP. Other codes, transport failures, invalid JSON, and thrown exceptions yield null. It does **not** check model, manufacturer, device name, MAC address, or file-list content at this stage. The discovered results used by the UI are therefore IP strings, not named/modelled device records. The default HTTP port is **80** because the discovery URL contains no explicit port.

## Wi-Fi versus Ethernet

The JavaScript NetworkInfo wrapper #12468 (`0x002f0f40`) first awaits native **getWIFIIPV4Address**. If its result is falsy or exactly `0.0.0.0`, it awaits generic **getIPV4Address** instead; otherwise it returns the Wi-Fi address. This means a valid Wi-Fi address takes precedence even when another interface is present.

The native methods independently establish what the fallback can return:

| Native method | Observed implementation | REA evidence |
| --- | --- | --- |
| RNNetworkInfo.getWIFIIPV4Address | Reads WifiManager connectionInfo.ipAddress and formats its four octets; exceptions resolve null. | [discovery-native-wifi-ipv4.json](discovery-native-wifi-ipv4.json), `ev_d65bbcc01fb968a41ad2908d081314edc59015ed38679c4d1980cda464d31c7a` |
| RNNetworkInfo.getInetAddresses | Enumerates NetworkInterface.getNetworkInterfaces() and appends every InterfaceAddress from every interface. | [discovery-native-interfaces.json](discovery-native-interfaces.json), `ev_f3e3b9489dbd85e5243a0818d50443b7b3ace9ca0419861dbf27b995411a59da` |
| RNNetworkInfo.getIPV4Address | Iterates those addresses, skips loopback and non-IPv4 values, skips addresses in DSLITE_LIST, and overwrites its result with each qualifying address; therefore the last qualifying address wins. Exceptions resolve null. | [discovery-native-ipv4.json](discovery-native-ipv4.json), `ev_b5f742aad770e273496dd6510565307faaa67443f135362844ec8d8fcb176b48` |
| RNNetworkInfo.inDSLITERange | Checks exact `DSLITE_LIST.contains(address)` membership. The list contents were outside this focused pass; this is not evidence of a general CIDR exclusion. | [discovery-native-excluded-range.json](discovery-native-excluded-range.json), `ev_c51aaa77103f4d2ec71444935235fa2b3c821b77146527bed8fae5533b6e5509` |

Derived implication: with Wi-Fi unavailable, a wired interface's IPv4 address can supply the scan prefix. There is no Ethernet-specific discovery protocol in the traced path; probes use ordinary HTTP to IP addresses through the OS network stack. These functions use the phone's existing IP connectivity; they do not join a Wi-Fi SSID, negotiate an Ethernet link, or assign interface addresses. A display reachable through a router can be found by this path if it provides the accepted `/info` service. The code does not establish whether a particular display has Ethernet hardware, which interface the OS will route requests through, or whether the user's F-Mini11 offers this newer HTTP service. On multiple active interfaces, the generic fallback does not explicitly select Ethernet, check interface names, or use the default route.

## Scan completion has a race

#12433 sets a nominal group size of **20** at relative `0x1d7` and starts the slice's probes through #12434 (`0x002f0b2e`). #12435 (`0x002f0b62`) sets the shared found flag/result when a probe resolves to a non-null IP. Failed probes resolve null, including #12436's catch handler. The main loop awaits **Promise.any**, selected at relative `0x260`.

Derived from standard Promise.any semantics and these instructions: the first *fulfilled null* can finish the group wait before its other probes finish. The loop can then start the next group while earlier requests remain pending, so 20 is not a strict limit on in-flight requests. The code stops starting groups when the shared valid-result flag is set, but may reach its final null check before slower valid probes finish. Thus the implementation can report an empty search prematurely; this is a static explanation of possible missed discovery, not an observed failure on the user's network.

The subnet scan records at most one successful IP and caches that singleton under `search-foundDevices`. Cached-IP checking can return several IPs. The UI handles several results with a selection dialog, although a fresh subnet scan is programmed to stop after finding one.

## Initialization also happens before successful discovery

DevicePage registers an independent mount effect: #12253 (`0x002ea99d`) loads useEffect at relative `0x415`, creates callback **#12328** at `0x41a`, constructs an empty dependency array at `0x41f`, and calls useEffect at `0x423`. Callback #12328 (`0x002ed601`) gets **CONN** at relative `0x3a`, gets **init** at `0x40`, and calls it at `0x46` (absolute instruction offset **0x002ed647**). There is no success-result conditional in this callback. Its cleanup #12329 (`0x002ed687`) calls destroyAll.

Therefore **successful HTTP discovery is not a prerequisite for starting legacy TCP**. On the initial DevicePage mount, CONN.init starts both the HTTP connection-check timer and the fixed legacy TCPClient. The separate discovery mount effect #12353 then searches for HTTP addresses. Calling init again from a successful discovery callback sees the existing timer and logs `already initialized` (#9082), while setHost can still update the HTTP target.

A scan of every full-disassembly instruction body for direct `CONN` and `init` property references finds three caller bodies: #12328 (mount), #12262 (one search result), and #12264 (selected multiple-result IP). This is coverage of direct property call sites, not a claim about hypothetical computed-property calls. Module 784's body #9050 (`0x0029abf1`) constructs/exports a singleton ConnectionManager at relative `0x113`–`0x127`; it does not call init there. Constructor #9052 (`0x0029b126`) initializes timer=null, gotSession=false, and host=the default IP. The initial active calls originate from the mount effect.

## From selected IP to communication

#12262 (`0x002eb8c6`) handles the search results. For one IP it calls **CONN.setHost(result[0])**, then **CONN.init()**. Several IPs produce a `select_your_device` dialog whose confirmation handler #12264 (`0x002eba5a`) calls the same two methods for the selected IP. An empty result optionally shows `searching_not_found` and schedules another search after **7000ms**; it does not invent a target address (#12262 relative `0x174`).

The newer HTTP path then performs:

1. **setHost**, #9079 (`0x0029bf5b`), sets ConnectionManager.host, calls API.setHttpInfo(host, getHttpPort()), and immediately calls requestSession. getHttpPort #9081 (`0x0029bfa0`) returns app PORT, **80**.
2. **requestSession**, #9065 (`0x0029b95b`), performs GET **http://host:80/ctrl/session**. Callback #9066 (`0x0029b9b8`) requires a successful request with numeric code **0** before it calls requestInfo. Failure clears gotSession.
3. **requestInfo**, #9063 (`0x0029b7df`), performs GET **http://host:80/info**. Callback #9064 (`0x0029b83c`) requires a successful request and non-null response; it accepts responses with a falsy code or a code **not strictly equal to numeric 1**, copies the complete JSON object into **deviceInfo**, updates the heartbeat timestamp and connected state, and calls its success callback. Numeric **code 1** calls resetToDefault at relative `0x2b`–`0x38`, then fails at `0x88`; the decisive comparison at relative `0x5b` is `JStrictEqual(code,1)` to failure. This post-session admission differs from discovery, which accepts only numeric 0 or 1; other code values are handled permissively by this callback. #9067 (`0x0029baa5`) sets gotSession from that callback result. No discovery-time model or name parsing occurs; getModel later reads a nonempty **deviceInfo.model** for a new device, falling back to F1 (#9142 at `0x0029da47`). The session/data field semantics are inferred from the code's use, not a captured display response.
4. **init**, #9082 (`0x0029bfc1`), starts ConnectionManager's timer and the separate legacy TCPClient. startTimer #9087 (`0x0029c178`) calls checkConnect immediately and every **3000ms**. Once gotSession is true, checkConnect #9072 (`0x0029bc5c`) starts/checks the WebSocket. startWebsocket #9054 (`0x0029b264`) opens **ws://host:9000**, whose on-open path requests play status. checkConnect sends JSON heartbeats when 15000ms have elapsed since its last send, and marks the newer connection disconnected if its last received heartbeat is over 20000ms old.

The shared API.GET implementation (#7516/#7517 at `0x00274742`/`0x0027476c`) queues requests and supplies a **3000ms** timeout. Session cookies/token storage and device-side session behavior are not reconstructed here; no cookies or credentials are invented by this report.

## Legacy F-Mini11 remains a separate path

#9264 (`0x002a0cc1`, relative `0x103`–`0x13b`) constructs the legacy TCPClient singleton with **OLD_DEVICE_IP** and **OLD_DEVICE_COMMAND_PORT**. #5334 (`0x0023377a`) assigns these constants **192.168.4.1** and **5233**. TCPClient constructor #9266 (`0x002a1226`) stores host and port. Its start #9267 (`0x002a12f5`) begins reconnecting and repeats every 3000ms; _connectAction #9274 (`0x002a14f6`) calls TCP createConnection with those host/port fields.

ConnectionManager.setHost updates the manager and its HTTP API; its complete body does not change the legacy TCPClient host. ConnectionManager.init starts that fixed legacy client in addition to the HTTP connection timer, including from the unconditional DevicePage mount effect even if every `/info` discovery probe fails. Therefore the recovered APK's subnet discovery/selection does **not establish legacy TCP support at arbitrary Ethernet/LAN addresses**. The legacy parser maps flag `7` to F-Mini11, but the newer path can also display F-Mini11 if `/info` supplies that model string. The user's label and successful type-7 playback therefore do not identify the transport generation. Claiming that this particular unit will be discovered over Ethernet requires device evidence. A Python client could deliberately permit an explicit host for legacy TCP, but that would be a project design choice pending a real response, not behavior established by this APK path.

## Coverage and provenance

The 52 retained Hermes functions in [discovery-index.json](discovery-index.json) are tied to original byte ranges and hashes; generator wrappers preserve the chain to the anonymous implementation bodies. The four native method results are complete JADX Java representations with no fallback markers. REA reports that exact native DEX instruction offsets/descriptors are unavailable and that method signatures are provider display types. Native details are derived from static decompilation, while Hermes branch/data-flow claims use actual bytecode instructions. Neither evidence type observes networking at runtime.
