# Display operations from Python and the CLI

`povbin device` implements the operational functions recovered from
`5D-Holo-android.apk` 1.0.85: information, files, playback, upload, deletion,
looping, power, BLE, card formatting and HTTP-family settings. It uses Python's
standard library; ADB is needed only for the phone transport.

## Use the phone's Wi-Fi connection

Keep the authorized USB phone connected to the display Wi-Fi. The computer
can use its regular network. Put connection options **before** the operation:

```bash
.venv/bin/povbin device --adb info
.venv/bin/povbin device --adb files
.venv/bin/povbin device --adb play 1
.venv/bin/povbin device --adb pause
.venv/bin/povbin device --adb resume
.venv/bin/povbin device --adb upload cd.bin --name CD.BIN
```

For multiple phones, use `--serial SERIAL` instead of `--adb`. For a computer
connected directly to the display Wi-Fi, omit `--adb`. The default target is
`192.168.4.1`. `--host ADDRESS` selects another target. Automatic protocol
selection tries HTTP, then legacy TCP; `--protocol legacy` forces the family
confirmed on this unit. `--raw` includes the original notification bytes.

A playback target can be a returned filename or the firmware's **index**.
An index does not mean the number at the start of a filename. For example,
`13_TRA~1.bin` was returned at index15 before the card was formatted.
Legacy commands have no explicit success ACK; `sent` reports transmission and
`requested_state_observed` reports a later matching playback state. Controls
are separated from following heartbeats and polled because firmware can apply
them asynchronously.

Additional operations:

```bash
.venv/bin/povbin device --adb next
.venv/bin/povbin device --adb previous
.venv/bin/povbin device --adb loop single
.venv/bin/povbin device --adb loop all
.venv/bin/povbin device --adb power off
.venv/bin/povbin device --adb power on
.venv/bin/povbin device --adb settings
.venv/bin/povbin device --adb set ble off
.venv/bin/povbin device --adb delete CD.BIN --yes
.venv/bin/povbin device --adb format-card --yes
```

Formatting erases the whole card. Its result includes
`directory_empty_observed`; this checks a complete empty firmware listing.
Deletion and formatting require explicit `--yes`. Upload refuses a filename
collision unless `--overwrite` is supplied. It also refuses an incomplete
listing unless `--overwrite` authorizes proceeding despite that uncertainty.
FAT alias collisions are checked conservatively; ASCII 8.3 names are useful.

Legacy settings readback has not been recovered: `settings` returns null for
`ble`, `switcher` and `loop`, meaning unknown current values. Those three
settings are writable; `switcher` maps to power. Legacy brightness, volume and
Wi-Fi changes are not implemented because no corresponding command has been
established. The HTTP family supports recovered `/ctrl/get` and `/ctrl/set`
settings, cookies, GBK-hex names and multipart uploads; it has local wire tests
but has not been observed on this display. Unsupported operations fail clearly.

## Upload behavior and live limits

Legacy uploads reproduce the APK's native framing: a GBK filename and padded
length, 1440-byte data blocks, ACKs every20 blocks and at the last block, then
completion. The original ARM64 library was also executed in an analysis harness
on the phone: all249 data packets for `cd.bin` matched the Python construction
byte-for-byte. The harness suppresses logging and bypasses JNI setup; it is
separate from execution of the full app.

Before formatting, ACK middle fields changed from `ffff` to `0000`, a scratch
filename appeared temporarily, and the directory later lost that entry. The
original native sender still reported success because it ignores ACK middle
fields. The Python client stops on `0000` based on those failed live observations;
the firmware definition of that value remains unknown. After the user-requested
format, uploads received `ffff` throughout and retained the filename in delayed
checks. The clean directory also removed the malformed list response.

Upload JSON distinguishes transfer completion, repeated filename listing,
content verification, persistence and actual playback. A listing alone does
not establish stored-byte equality, survival across a power cycle, or visible
video/audio playback. No legacy download API was recovered for readback.

## Python API

```python
from povbin import DeviceClient

with DeviceClient(adb_serial="YOUR_ADB_SERIAL", protocol="legacy") as display:
    print(display.info())
    print(display.files())
    print(display.upload("cd.bin", name="CD.BIN"))
    print(display.play("CD.BIN"))
```

The transport uses `adb shell -T ... toybox nc` with binary pipes. On the tested
ADB version, `exec-out` did not forward input; `-T` avoids terminal translation.

See [live findings and retained captures](evidence/android/live/device-findings.md),
[the missing-file parser evidence](evidence/android/live/packet-findings.md),
[the exact control path](evidence/android/live/control-path-findings.md), and
[the native upload call chain](evidence/android/live/native-upload-path-findings.md).
