# Legacy upload path in APK 1.0.85

This is static evidence from the supplied APK, not observed device traffic.
The APK was not executed and no upload or control commands were sent.
The JavaScript upload enters a native bridge. The APK's named legacy native
sender has the packet construction recovered below, including its separately
analyzed ACK helper; exact JNI caller/callback wiring remains a stated limit.

## Observed JavaScript and Java boundary

The artifact constants in Hermes function **5334** define
`OLD_DEVICE_IP = "192.168.4.1"`, `OLD_DEVICE_COMMAND_PORT = 5233`, and
`OLD_DEVICE_UPLOAD_PORT = 5499`. These declare separate endpoints; declaring
a port does not prove that a particular method opens it.

The active `TCPClient.uploadFile` implementation is generator function **9347**
(public wrapper **9345**). It removes a leading `file://` prefix from the local
path and sends `JSON.stringify({name, path})` to
`MIDDLE.callNativeWithPromise(MEDIA_MODULE + MEDIA_FUNC_UPLOAD, json, 0)`.
It subscribes to `MEDIA_EVENT` to relay native progress to `options.onProgress`
and relays the native response's `result` field to `options.onResult`.
A thrown error reports false. The event listener is removed on exit.
The normal JavaScript generator returns undefined, so a caller should not
interpret its resolved value as the upload success boolean.

The original Java dispatch method
`com.sp.holographic.react.MiddleNativeModule.handleCmd` reads the JSON `name`
and `path`, encodes the filename using **GBK**, and calls:

```java
byte[] bytes = name.getBytes("GBK");
NativeCore.oldDevUploadFile(bytes, bytes.length, path, progress, result);
```

The progress callback parses an integer string and emits `{progress: value}`
on `MEDIA_EVENT`; the result callback resolves a map containing the native
boolean `result`. The method `NativeCore.oldDevUploadFile` is declared native
and has no Java implementation body. This is the main legacy upload path,
not evidence of a fallback after a JavaScript upload fails.

Sources:

- [Exact Hermes functions, offsets, and hashes](legacy-upload-functions.json).
- [Raw Hermes disassembly](legacy-upload-bytecode.hasm), functions 5334,
  9345–9349, and constructor 9266.
- [Decompiler excerpt](legacy-upload.pseudo.js.txt), original pseudo.js lines
  335509–336259.
- [REA Java dispatch evidence](legacy-upload-native-dispatch.json),
  `MiddleNativeModule.handleCmd` and its `MEDIA_FUNC_UPLOAD` branch.
- [REA JNI declaration evidence](legacy-upload-jni-method.json),
  `NativeCore.oldDevUploadFile`.

## JavaScript helpers do not describe the active transfer

`_waitSendFileInfoAck` (**9329**) and `_waitSendPackagesIntervalAck` (**9333**)
poll their respective boolean flags every 1 ms, default to a 5-second deadline,
reset a true flag to false, then resolve. They reject when their deadlines
expire. The constructor initializes both flags false. Within the complete
Hermes disassembly, the flags are only accessed by those initializations and
the polling/reset helpers; no setter to true or ACK-byte parser is present.

`_connectUploadSocket` (**9338**, nested callbacks **9339–9343**) accepts a host,
port, and optional timeout defaulting to 5 seconds. It calls the bundled
TCP socket implementation and handles connection, error, close, and timeout.
Its timeout error text says "10 seconds" even though the computed default
deadline is 5 seconds. `_disconnectUploadSocket` (**9337**) destroys a socket.

These helpers are published as methods on the class, but a full-bundle
disassembly search found no direct `GetById` call references to them. The
active upload generator does not call them. Consequently their default
timeouts cannot be claimed as the active native upload's ACK deadlines.
Dynamic property lookup or external use outside this artifact was not ruled
out by that bounded static search.

## Native target

The exact APK member `lib/arm64-v8a/libSPCore.so` has SHA-256
`20d90219ddf46083844ace9bb225f583f44802d78d05e2f409cd189f0654645b`.
Its dynamic symbols include:

| Symbol | ELF address | Size |
| --- | --- | ---: |
| `old_dev_tcp_upload` | `0xf64e0` | 1,788 bytes |
| `old_dev_tcp_upload_async` | `0xf6d38` | 224 bytes |
| `FILE_INFO_HEADER` | `0x274498` | 6 bytes |
| `FILE_INFO_TAIL` | `0x27449e` | 8 bytes |
| `CHUNK_HEADER` | `0x2744a6` | 9 bytes |
| `CHUNK_TAIL` | `0x2744af` | 11 bytes |

Addresses, file mappings, exact data bytes, and hashes are in
[native-symbols.json](legacy-upload-native-symbols.json).

The first REA/Ghidra request by symbol name reported ambiguity between the
real code entry and a PLT thunk. Its returned exact real-code address
`0x1f64e0` accounts for Ghidra's `0x100000` analysis image base; it does not
change the ELF address or original file offset. The rejected request is
retained in [native-function.json](legacy-upload-native-function.json).

## Native packet construction

The corrected [REA/Ghidra dossier](legacy-upload-native-function-address.json),
Evidence ID `ev_e192f9195ec436822d2a54b62d100f0eeeea6b3071541258e89227a881107b4c`,
covers the complete 1,788-byte function body at `0x1f64e0..0x1f6bdb`.
Readable extracts preserve its [decompiler output](legacy-upload-native.c.txt)
and [assembly](legacy-upload-native.asm.txt). These are analysis
representations, not recovered original source.

The native sender opens the input file with `fopen(path, "rb")`, determines its
length with `ftell`, then connects an IPv4 stream socket to the hardcoded
**192.168.4.1:5499**. The `sockaddr` port bytes are `15 7b` (5499), distinct
from the JavaScript control client's declared port 5233. The transfer does not
use the JavaScript control socket.

Let `L` be file length, `N = strlen(GBK_filename)`, and
`B = ceil(L / 1440)`. The sender advertises `P = B * 1440`, zero-pads the last
payload block to 1440 bytes, and uses the following layouts:

| Message | Byte construction | Total bytes |
| --- | --- | ---: |
| File info | ASCII `d31d66DF` + one byte `(N+61)&255` + four-byte big-endian `P` + `N` raw GBK filename bytes + ASCII `a4a8c2e3` | `N+21` |
| Data block | ASCII `d31d88JMP` + 1440 raw file bytes + ASCII `000a4a8c2e3` | 1460 |
| Completion | ASCII `d31d88DEFa4a8c2e3` | 17 |

The framing tokens are **ASCII strings**, not hex-decoded byte strings. For
example, `d31d66` is six bytes `64 33 31 64 36 36`, not three bytes
`d3 1d 66`. The payload is the unmodified file byte stream, with final zero
padding. It includes whatever file-level header and trailer the source file
contains.

The one-byte file-info control field is demonstrably `N+61` modulo 256. Its
firmware interpretation is unknown; it is not simply the `N+21` transmitted
packet length. The native sender does not enforce an explicit filename length
limit before allocating `N+21` bytes and copying all `N` bytes. The advertised
size is a four-byte field and the native writes cast the padded size to
32 bits. These observations do not establish a safe firmware filename or
maximum file-size limit.

No sequence number or calculated checksum is written in the data block's
20 bytes of overhead. The 9-byte prefix and 11-byte suffix remain constant
for every block. The apparent checksum text `000` is three literal ASCII zero
characters, not the result of a sum or CRC calculation in this sender.

After file info, the sender calls `FUN_001f6bdc(fd, "d30d66")`. It calls the
same helper with `"d30d88"` after every twentieth block and after the final
block. A zero helper return causes the transfer failure path. There is no
block retransmission in this complete sender body; failing a required ACK
ends it. The exact ACK comparison and deadline are established separately
from the helper; the unused JavaScript helpers' five-second values do not
establish the native deadline.

Each `sendto` loop advances by the returned count, permitting a partial socket
write to finish on subsequent calls. File-info and data-block write failure
enter the failure path. After all required block ACKs, the completion loop
attempts the 17-byte marker but sets the success path even if that write
returns zero or an error before sending all 17 bytes. No completion ACK is
read in this function. This means a native success result is not proof the
device received its completion marker. The internal result callback status
is zero on this success path and one on failure; the Java/JNI result mapping
to a boolean is a separate boundary.

Progress is derived from sent block count divided by total block count,
reported about once a second and on the final block. The file handle,
allocated packet buffers, and upload socket are released at exit.

The [offline field-layout replay](legacy-upload-layout-replay.json) uses actual
local source bytes and the exact library constants, but does not invoke the
native routine or create sockets. Under this recovered layout:

- `13_tractor.bin`: 4,797 blocks, 116 zero-padding bytes, advertised size
  6,907,680, one file-info ACK and 240 block-interval/final ACK waits.
- `14_cd.bin`: 249 blocks, 388 zero-padding bytes, advertised size 358,560,
  one file-info ACK and 13 block-interval/final ACK waits.

## Native ACK acceptance and deadlines

The separate [ACK dossier](legacy-upload-native-ack-function.json), Evidence
ID `ev_9e44881b9dec968e439e468593da0cb13f23b004b8bfbc37cb0a4e903b6f9461`,
covers the complete 348-byte helper at `0x1f6bdc..0x1f6d37`. Its readable
[decompiler output](legacy-upload-native-ack.c.txt) and
[assembly](legacy-upload-native-ack.asm.txt) preserve the evidence. The
decompiler renders its return type as void; the assembly's `mov w0,#1` and
`mov w0,wzr` establish the actual true/false result used by its caller.

Each invocation starts with an empty 128-byte accumulator and a
`CLOCK_MONOTONIC` timestamp. It repeatedly calls `recvfrom` with
`MSG_DONTWAIT = 0x40`, appending positive received bytes. It accepts only when:

1. The accumulated length is at least 14 bytes.
2. The first six bytes match the requested ASCII token (`d30d66` after file
   info, or `d30d88` after block intervals/final block).
3. The last eight accumulated bytes match ASCII `a4a8c2e3`.

Thus the minimal accepted ACKs are the 14-byte ASCII strings
`d30d66a4a8c2e3` and `d30d88a4a8c2e3`. Bytes between the six-byte prefix and
eight-byte suffix are not checked. The helper returns false after elapsed
milliseconds are **greater than 5,000**, sleeping 5,000 microseconds (5 ms)
between unsuccessful reads/checks. Socket EOF and negative reads are not
distinguished into an earlier failure; it continues until the deadline.

This helper handles a single ACK split across TCP reads, but it neither scans
for a later valid prefix nor clears unexpected bytes. Leading junk permanently
prevents that invocation from accepting. Trailing noise prevents acceptance
until the cumulative buffer again ends in the expected suffix. If the 128-byte
buffer fills without acceptance, further requested read length becomes zero,
so the helper waits out the deadline. Coalesced messages may be accepted if
their combined first/last markers match, since middle bytes remain unchecked.
These are bounded static consequences, not observed upload failures.

## Remaining limits

The connection uses blocking `connect`; no connect deadline
is configured in this sender body. Whether another layer establishes one is
unknown. The firmware's file-info control-byte interpretation, filename and
file-size limits, treatment of the constant `000` field, JNI caller wiring,
and actual traffic remain unobserved. The lack of a completion-send check is a
concrete client behavior, not a demonstrated cause of earlier Wi-Fi failures.

To reproduce the Hermes evidence selection without running APK code:

```bash
python3 tools/select_legacy_upload_evidence.py
python3 tools/replay_legacy_upload_layout.py
```
