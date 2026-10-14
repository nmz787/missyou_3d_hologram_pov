# Actual APK control route and upload preparation

This is a bounded static trace plus offline replay of extracted methods. It does not launch Android or contact a device. [control-path-bytecode.hasm](control-path-bytecode.hasm) retains the instructions; [control-path-index.json](control-path-index.json) records original function offsets/byte hashes and native REA Evidence IDs.

## A file row sends its wire index unchanged

DevicePage renderItem **#12323**, base `0x002ed060`, captures the complete row object. The row's outer TouchableOpacity handler **#12324**, base `0x002ed456`, calls **handlePlay(item)**, #12317 at `0x002ecec5`. That handler calls **CONN.playFile(item, callback)**. It does not derive the index from the display label, array position, filename prefix, or current playing index.

ConnectionManager.playFile **#9112**, base `0x0029cfc9`, extracts **item.index** and **item.name**, then calls getIsOldDevice. In the legacy branch at relative `0x6e`, it calls **TCPClient.playFile(item.index)**. The numeric index is passed without adding/subtracting 1 or converting to hexadecimal. The newer branch instead uses GBK-hex filename in `/DCIM/{name}?act=play`; that branch is not replayed here.

TCPClient.playFile **#9305**, base `0x002a2279`, checks its isPlaying flag. If false, it calls playPlay immediately at relative `0x0b`–`0x11`. It then builds **String(index).padStart(2,'0')**, maps the characters to their character codes, and puts the first two into the 19-byte command. There is no explicit wait between optional resume and play; both enter the common send queue.

| Entry | Exact bytes before native bridge |
| --- | --- |
| Play wire index 3 | `c31c40abe03a4a8c2e3` |
| Play wire index 15 | `c31c40abe15a4a8c2e3` |
| Resume when isPlaying=false | `c31c35abca4a8c2e3`, followed by the indexed play command |
| Pause | `c31c34abca4a8c2e3` |

The UI success callback schedules dismissal of its loading indicator after **500ms**. That delay is after the send result; it does not delay construction of the command.

## The play/pause icon differs from tapping the row

Icon handler **#12325**, base `0x002ed46d`, calls handlePause(item) only when **playInfo.current equals item.name** and **playInfo.state equals ing**. Otherwise it calls handlePlay(item). The outer row handler always calls handlePlay. handlePause **#12320** (`0x002ecf93`) calls CONN.playPause(callback); ConnectionManager.playPause **#9120** (`0x0029d21a`) chooses the legacy TCPClient.playPause method **#9309** (`0x002a235c`) or the newer HTTP pause route.

Thus an outer row tap selects a file even when its icon would show pause. The icon logic uses name/state from the displayed playInfo object. A malformed directory/status parser can make those UI conditions stale or incorrect without changing the pause/play command literals themselves.

## No hidden command encoding changes the bytes

TCPClient.send **#9282/#9283** uses **Buffer.from(array)** for the numeric command arrays and queues the resulting Buffer. `_processQueue` generator **#9288** passes that packet directly to **socket.write(packet)** and resolves its send Promise with **OK** after the local write call. This is not a firmware acknowledgment. It yields through a zero-delay timer before processing another queued send.

react-native-tcp-socket **Socket._generateSendBuffer #9456** (`0x002a5abf`) returns an existing Buffer unchanged. **Socket.write #9439** (`0x002a5353`) converts it to Base64 and calls **NativeModules.TcpSockets.write(socketId, base64, messageId)**. That Base64 is bridge serialization, not bytes sent to the display.

Native shipped-artifact evidence completes the chain:

- **TcpSocketModule.write** performs **Base64.decode(str,2)** and passes the decoded byte array to its TcpSocketClient. [control-path-native-TcpSocketModule.json](control-path-native-TcpSocketModule.json), `ev_fdae5b568c205f16d5c892797f59026a87a273adc10ca58b959dd23426e02e82`.
- **TcpSocketClient.write** submits a Runnable to its writeExecutor, which calls **socket.getOutputStream().write(byteArray)**. It then emits the local written event. [control-path-native-TcpSocketClient.json](control-path-native-TcpSocketClient.json), `ev_f5febab9c9dd05bf86ed79c94788f0b60559eeb6a9402cb7c634d79a13e86807`.

No extra checksum, XOR, line ending, ASCII-to-hex conversion, or index transformation appears in this path. The shown ASCII commands are the actual bytes supplied to the socket output stream by these methods. Static analysis does not prove when firmware acts on them.

## Connection options and initialization

Legacy TCPClient._connectAction #9274 supplies only **host** and **port** to createConnection. Socket.connect #9424 copies those options, normalizes host/port, and calls native TcpSockets.connect. Native **TcpSocketClient.connect** defaults local bind to **0.0.0.0:0**, defaults reuseAddress to **true**, defaults connect timeout to **0**, optionally binds the OS-selected Network, connects the socket, and starts listening. It does **not** force TCP_NODELAY in this method. [control-path-native-TcpSocketClient-connect.json](control-path-native-TcpSocketClient-connect.json), `ev_a660ea363ebdb96f7a5512e1b991acf0ca624eb95cd50ad4919a778f3d282463`.

The native module chooses a Network before constructing the client; its full network-selection helper was outside this bounded pass. [control-path-native-TcpSocketModule-connect.json](control-path-native-TcpSocketModule-connect.json), `ev_457b71684f8effb0042260b759b5a2004ccdc01a65af66dc1a5aedda8bff21b6`.

The legacy on-connect callback #9275 marks connected=true, starts the heartbeat timer, reports connection state, and processes pending sends. startHeartBeatTimer #9271 defaults to **1000ms**; its interval callback sends **c31c38abca4a8c2e3**. No special control-session or authentication packet appears in these inspected startup methods. The app keeps a persistent connection and continues polling; a short-lived client may observe status before a command has taken effect. Timing differences require runtime evidence; no timing is invented by the offline replay.

## Upload call sites: filename generation, no recovered pre-upload pause

In the normal EditMedia path, name input **#17190 truncateGBK** limits the label to **five GBK bytes**. Its changed-name callback #17192 applies that truncated result. Conversion callback **#17199**, on conversion success, calls **CONN.generateFilename(label)** and then **uploadMedia(file://localOutputPath, generatedName)**.

**generateFilename #9090**, base `0x0029c20d`, chooses the first unused decimal identifier from **00 through 99**, adds it to usedIdentifierSet, and constructs **NN_label.bin** (extension defaults to bin). With a five-byte label, the base occupies at most **eight GBK bytes**. This is distinct from wire file indices: the prefix identifies an app-generated filename, while play commands use the separate item.index received in device records. Identifiers are populated from names matching the UI formatter's two-character underscore/hyphen pattern, so a partially parsed list can leave existing identifiers unrepresented.

Upload generator **#17204** calls **CONN.uploadFile(name,path,{onProgress,onResult})**. ConnectionManager.uploadFile **#9105** takes the legacy branch to **TCPClient.uploadFile(name,path,callbacks)**. Generator **#9347** sets up progress events, removes `file://` from the local path, and passes JSON **{name,path}** to **MEDIA_MODULE + MEDIA_FUNC_UPLOAD**. It forwards the legacy filename unchanged; it does not GBK-hex-encode it in JavaScript. The native upload's framing and acknowledgment behavior belong to the separate JNI/native evidence.

None of these complete inspected functions—#17190/#17192/#17197/#17198/#17199/#17204/#9105/#9347—calls playPause, playPlay, shutdown, or a device stop operation before upload. The 360 edit path uploadMedia **#17271** also calls CONN.uploadFile directly. This is a bounded negative finding about those actual call paths, not a claim about every native side effect or every upload UI in the APK. A device pause before upload is not established by this evidence. Success/failure callbacks can delete local conversion/temp files; they do not issue remote deletion commands in these functions.

## Controlled replay and limits

[control-path-replay.mjs](control-path-replay.mjs) and [control-path-replay.json](control-path-replay.json) replay six cases from row/icon handlers through ConnectionManager, the original command builders, and original Socket Buffer/Base64 methods. A local native-write recorder decodes Base64 and retains exact socket byte sequences. Cases cover index3, index15, optional resume-before-play, and current/noncurrent icon behavior.

The relay replaces send-queue execution with an immediate Buffer.from/Socket.write recorder; the real queue is established by retained instructions. Native Java methods are statically decompiled, not executed. Per-function register declarations and UI module/loading/timer stubs are listed in the replay result. Firmware responses, scheduling, Android UI execution, and real networking are outside this offline replay. The source proves decimal index15 construction; it does not infer a firmware acceptance rule from a temporarily stale status snapshot.
