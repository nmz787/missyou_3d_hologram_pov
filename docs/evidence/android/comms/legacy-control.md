# Legacy TCP connection and control protocol

Static evidence is bound to supplied APK `com.sp.holographic` 1.0.85/code105,
SHA256 `8a83b1f128beb43341eefd2b4ad743512d0193ff6dd4e7b56feba138fb4b63c9`;
Hermes96 bundle SHA256
`8389750af87d60e75bbd7d93ba57d1bd239008812c8c5ef7ecc84cf2a46777e2`.
No Android execution, network connection or device operation was performed.

[Raw disassembly](legacy-control-bytecode.hasm) retains functions9266–9328;
[manifest](legacy-control-functions.json) identifies their exact original byte
ranges and hashes. Function-relative instruction offsets below are added to those
file offsets. The prior [file-list evidence](../file-list-bytecode.hasm) and
[parser replay](../file-list-replay.json) remain applicable.

## Connection and startup

The singleton is constructed with the APK's `OLD_DEVICE_IP=192.168.4.1` and
`OLD_DEVICE_COMMAND_PORT=5233`. See the discovery report for the separate HTTP
host selection: changing the manager's HTTP host does not retarget this TCP
singleton. These are ordinary IP sockets over an existing network connection.

`TCPClient.start`, function9267, first stops the previous connection, clears
`manualDisconnect`, calls `_reconnect` immediately and installs a3000ms reconnect
timer. `_reconnect`9281 connects when not manually stopped and either disconnected
or lacking a socket. `_connectAction`9274 creates the TCP connection with
`{host:this.host,port:this.port}`. Connection callback9275:

1. Sets `lastHeartBeatTs=0` and `connected=true`.
2. Starts the heartbeat timer.
3. Reports connection state and drains queued sends.

Data callback9276 calls `_handleData`9290, which calls `_parseNotify`9293 directly.
Error/close callbacks9277/9278 call `_disconnectAction`9279. Disconnect resets
file/status settings, stops heartbeat, reports disconnected and clears the flag.
The model resets to `F1` in9280; that default is not hardware identification.

`startHeartBeatTimer`9271 defaults to1000ms. Callback9272 sends heartbeat and,
when a receive timestamp exists, disconnects after more than20000ms without
incoming data. `_parseNotify`9293 updates that timestamp **before validating the
message**, so unrelated/invalid data can count as liveness. Before any receive
timestamp exists, this particular watchdog condition does not trigger.

## Exact outbound bytes

These are **ASCII characters**, not binary hex-decoded packets. For example,
heartbeat is17 bytes beginning `63 33 31 63` in hexadecimal, representing the
text `c31c`. Function9294 uses the numeric array
`[99,51,49,99,51,56,97,98,99,97,52,97,56,99,50,101,51]`.
Send executor9283 converts arrays with `Buffer.from(array)`; queue body9288 calls
`socket.write(packet)` directly. No hex decoding occurs on this path.

| Operation | ASCII wire message | Function |
| --- | --- | --- |
| Heartbeat/status request | `c31c38abca4a8c2e3` |9294|
| Previous | `c31c33abca4a8c2e3` |9307|
| Next | `c31c32abca4a8c2e3` |9308|
| Pause | `c31c34abca4a8c2e3` |9309|
| Resume play | `c31c35abca4a8c2e3` |9310|
| Play file index13 | `c31c40abe13a4a8c2e3` |9305|
| Delete file index13 | `c31c39abe13a4a8c2e3` |9298|
| Loop all / false alternative | `c31c36abca4a8c2e3` / `c31c37abca4a8c2e3` |9316|
| Open/display on | `c31c45abca4a8c2e3` |9320|
| Shutdown/display off | `c31c89abca4a8c2e3` |9324|
| BLE switch true / false | `c31c44abca4a8c2e3` / `c31c43abca4a8c2e3` |9328|
| Format SD card | `c31c88abca4a8c2e3` |9304|

This table documents encoded requests; it is not an observation of firmware
acceptance or physical behavior. All commands, including destructive commands,
were captured only by an in-memory recorder and never sent.

Indexed commands use `String(index).padStart(2,'0')`, map characters to byte
values, then include the first two characters in the array. The index is the
device's list index, not necessarily the number at the beginning of a filename.
`playFile`9305 calls `playPlay` first when `isPlaying` is false.

`send`9282 has a5000ms queue timeout by default. Executor9283 installs a task
timer, stores the packet, resolves/rejects and starts queue processing. Body9288
clears the timer when the task leaves the queue, writes the socket and immediately
resolves `OK`. This means send success establishes a local write attempt; it
does not wait for a firmware acknowledgment. Some operation methods update local
state optimistically after that promise resolves.

## Incoming list/status decoder

`_parseNotify`9293 accepts a buffer of at least17 bytes only when its first six
bytes are ASCII `c30c38` and its last eight are ASCII `a4a8c2e3`; it passes that
buffer and its length to `_parseFileList`9292. This receive handler recognizes
only that notification family. Separate upload helpers do not broaden this
handler into a general decoder for all possible firmware messages.

The decoder starts file records at byte9, with a loop boundary of `N-12`:

| Relative field | Decoder interpretation |
| --- | --- |
|0..1|two-byte ASCII decimal record length `L`|
|2..3|two-byte ASCII decimal file index|
|4..6|three bytes skipped by the decoder; meaning unestablished here|
|7..`L+1`|filename bytes decoded asGBK|

The next record begins at `offset+L+2`. Invalid decimal fields or an out-of-range
name stop the loop, after which earlier decoded files can still be published.
The remaining tail is decoded asUTF8, trimmed and searched using
`/(\d{2})(.{1,2})(1[01])/`: first capture is playing index; second goes to the
model decoder; `11` means playing and `10` means not playing. The regex is not
anchored. `_parseModel`9291 recognizes model flags `1→F1`, `2→F2`, `Z→F5`,
`4→F-MINI18`, `7→F-MINI11`, with `F1` fallback for unknown or missing flags.
For a two-character model field it uses its second character.

There is **no receive accumulator** between TCP data callbacks and the parser.
The previous controlled replay demonstrates split responses being ignored,
malformed records publishing only a prefix, and coalesced responses producing
spurious entries. These results help explain why the observed file list could
be incomplete, but actual notification bytes from the user's display are still
required to distinguish an app parsing failure from a firmware omission.

## Controlled packet-construction replay

[legacy-control-replay.json](legacy-control-replay.json) records15 cases, including
zero-padded index7 and index13. [The harness](../../../../tools/replay_android_legacy_controls.mjs)
runs retained decompiler bodies with a local `send` recorder. It declares registers
per frame, replaces generator bookkeeping and stops at the first send; it does
not execute Hermes bytecode, the send queue, native sockets, replies or firmware.
The raw HASM is authoritative for constants, branches and call relationships.

From the project root:

```bash
.venv/bin/python tools/extract_android_control_evidence.py
node tools/replay_android_legacy_controls.mjs
```

The native legacy upload wire format is investigated separately in the upload
report; the existence of a5499 constant or unused JavaScript ACK helper is not
sufficient evidence of native upload framing.
