# Live display operations and the formatting experiment

## Result

At the user's explicit request, the card was formatted through the recovered
legacy API. The directory became **empty and complete**. A subsequent Python
CLI upload of **cd.bin → 90USB.bin** completed with **ffff** in the information
ACK and all 13 data ACKs. The new entry remained present and reported as playing
through eight checks spanning **21 seconds**, beyond the earlier disappearance
interval. The display was left with this clip and playback enabled. The Android app
also visibly shows **F-MINI11**, the **90USB** row and its pause icon in the
[post-format screenshot](app-after-format.png); compare the
[earlier F1/broken-list screenshot](app-before-format.png).

[cli-format-card-final.json](cli-format-card-final.json),
[cli-upload-final.json](cli-upload-final.json),
[cli-play-final.json](cli-play-final.json) and
[cli-final-persistence.json](cli-final-persistence.json) retain the final results.
[python-final-operations.json](python-final-operations.json) additionally records
successful play, pause, resume, deletion of the newly created scratch file,
then a fresh upload and delayed listing checks. Original files were erased only
by the subsequently authorized card-format command; earlier deletion tests
were restricted to the scratch file.

This supports a **card/directory-state problem**, but does not identify which
file caused it or whether it was a filename, directory entry, fragmentation,
filesystem corruption, or another firmware condition. The pre-format SD-card
inspection showed roughly3.6GiB free; that is a historical mounted-card reading,
not a current capacity response from firmware.

## Connection and commands

Authorized USB phone serial 5007TF1010003531 was on display Wi-Fi with wlan0
192.168.4.2/24; the display answered at 192.168.4.1. HTTP 80 and WebSocket 9000
refused connections; legacy TCP 5233(control) and 5499(upload) were open. The
installed app reported package com.sp.holographic version 1.0.85/code 105,
matching the investigated APK.

The computer used binary pipes through `adb shell -T exec toybox nc`. A raw
2920-byte two-packet echo through non-PTY ADB matched its input; on this ADB
build `exec-out` did not forward stdin. This rules out terminal translations
for the tested transport, rather than assuming every ADB invocation is duplex.

The original app successfully selected the 01.LC row on screen. Offline tracing
then proved that the index reaches a direct Java socket write unchanged; no
hidden handshake, cryptography, hexadecimal index conversion or index offset
was found in that path. See [control-path-findings.md](control-path-findings.md).
Raw decimal selection 15 and 12 also worked after allowing device processing.

Immediate heartbeat queries after controls sometimes left the previous state
or prevented the action taking effect. A format followed immediately by status
did not clear the list over 18seconds. A separated format request did clear it.
The final client spaces commands and heartbeats by 750ms and polls matching
states. This is an observed workaround, not a claim about firmware's internal
TCP parser. There is no explicit legacy control success ACK.

Format wire bytes are **c31c88abca4a8c2e3** (17ASCII bytes), recovered from
Hermes #9304. The APK resets its local list optimistically after sending; the
Python implementation checks the actual returned directory. The final CLI
format reported `directory_empty_observed:true`.

## Why tractor and F1 were wrong

The captured 194-byte notification contains tractor at index 15. An earlier
record's declared length overlaps the next record, making the APK publish only
six rows. It then matches text inside a later filename as status and falls back
to F1. The real final field is 15H711, identifying F-Mini11. The project parser
recovers nine bounded records while explicitly marking the list incomplete.
[packet-findings.md](packet-findings.md) contains byte offsets, original-function
hashes and bounded parser replays. After formatting, live listings were complete
and no overlapping-record issue remained.

## Original native uploader runtime comparison

[Native JNI tracing](native-upload-path-findings.md) proves the original app
reaches the recovered exported old_dev_tcp_upload routine. NativeInit contains
no observed writes to its framing arrays; a byte-by-byte cross-reference search
found reads, with indirect initialization effects left outside that claim.

For runtime comparison, an Android ARM64 analysis executable loaded the
**unmodified APK library** via dlopen and called that export synchronously.
It interposed f_log to suppress logging, and sendto/recvfrom to retain their
bytes while forwarding the same kernel calls. It bypassed JNI, access checks,
Java callbacks and the full app; it did not reproduce those lifecycle details.
The harness source is [native-upload-probe.c](native-upload-probe.c).
[The first capture](native-upload-capture.dat) and
[comparison summary](native-upload-summary.json) retain all 249 data packets:
every 1460-byte packet was **byte-equal** to the Python construction, including
payload, padding, header and trailer. The source was 358172-byte cd.bin,
SHA-256 recorded in the local evidence index. The capture includes two 4-byte
non-upload receive records during library startup; only framed upload replies
are attributed to the uploader's device exchange.

Before format the native routine returned NATIVE_RESULT0 despite firstffff and
later0000 ACK fields. The scratch filename appeared, then disappeared from
returned lists around 15seconds later. A run with the app stopped also reproduced
that listing disappearance; an attempted pause had not taken effect in that
probe. Thus that probe does not establish a genuinely paused transfer.
[native-upload-paused-checks.json](native-upload-paused-checks.json) preserves
that limitation rather than labeling it a successful paused upload.

After formatting, the first adaptive-ACK Python attempt stalled: an early ACK
was misinterpreted as per-block cadence. The subsequent native request received
88 replies while waiting for66, consistent with a transfer still in progress;
its exact firmware state is unknown. A later retry using original 20-block
cadence succeeded with one 66ffff and thirteen 88ffff replies.
[native-upload-after-format-retry.dat](native-upload-after-format-retry.dat)
retains that run. The final Python default uses the recovered **20-block cadence**,
not adaptive inference. Subsequent CLI transfers succeeded with the same fields.

The firmware meaning of ffff/0000 has not been extracted. The original ACK
helper ignores them. Based on the observed failed transfers, the client rejects
0000 as **unconfirmed**, with that uncertainty in the error. No checksum or
sequence-field conjecture was added to framing. Per-block, 100ms-paced and
incremented-footer probes before formatting did not fix the issue.

## What these results do and do not verify

Confirmed on this unit: connection/model/files; clean empty listing after
format; protocol-complete upload; stable delayed listing; matching playback
index and play/pause state; removal of the scratch entry. The user had earlier
confirmed physical video and audio playback of the same type7 cd.bin copied
via SD. The latest Wi-Fi-uploaded clip has **not yet received a new user
confirmation of visible video and audible sound**.

No recovered legacy download API provides stored-byte readback. Listing and
playback status therefore do not prove content equality or survival through a
physical power cycle. Upload JSON retains content_verified:false,
persistence_verified:false and playback_verified:false. Short delayed checks
are documented separately. Power, looping and BLE packets have original-byte
construction tests; their physical effects were not tested in this pass.
HTTP-family operations have local wire tests, not live-device validation.

Recheck recorded hashes and packet equality with:

```bash
.venv/bin/python tools/verify_device_evidence.py
```

This verifier is offline and requires the retained cd.bin source. It sends no requests.
