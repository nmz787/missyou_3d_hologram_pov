# Device connections and operations

These examples use `povbin` from an activated virtual environment. See the
[README](../README.md) for installation and a complete quick start.

## Connect directly from a computer

Connect the computer to the display's Wi-Fi hotspot. Direct mode is the default:

```bash
povbin device info
povbin device files
```

The default address is 192.168.4.1. Ordinary network routing determines the
interface, so a Wi-Fi or Ethernet connection works whenever it can reach that
address. The CLI does not change your network connection or require a display
Ethernet port. Choose a different reachable IP with `--host`:

```bash
povbin device --host 192.168.4.1 --protocol legacy info
```

The address must be a hostname/IP, not a URL. Automatic mode tries HTTP first,
then legacy TCP. Force `legacy` for compatible older firmware or `http` for
HTTP-family firmware. Connection failure is not proof that the device is absent
if you are connected to the wrong network.

## Connect through an Android phone

The phone must be connected to the display's Wi-Fi, attached over USB and
already authorized for ADB. Android platform tools must provide `adb` on PATH.
The computer can remain on its ordinary network.

```bash
adb devices
povbin device --adb info
povbin device --adb upload CLIP.BIN
```

`--adb` selects the sole authorized phone. For multiple phones, use
`--serial SERIAL`; this also enables the phone transport. ADB mode uses the
phone's network through its Toybox netcat utility, rather than USB file copying.

## Connection options

Put these **before** the operation: `device [OPTIONS] OPERATION ...`.

| Option | Default | Effect |
| --- | --- | --- |
| `--host ADDRESS` | `192.168.4.1` | Target display hostname/IP. |
| `--protocol auto\|legacy\|http` | `auto` | Automatic fallback or an explicit protocol. |
| `--adb` | Off | Connect through the sole authorized USB phone. |
| `--serial SERIAL` | None | Select an ADB phone and enable phone transport. |
| `--timeout SECONDS` | `5` | Positive network timeout. |
| `--raw` | Off | Include raw notification bytes in JSON for diagnostics. |

## Upload and select a file

```bash
povbin device upload CLIP.BIN
povbin device upload local-output.bin --name CLIP.BIN
povbin device play CLIP.BIN
```

`--name` changes only the destination filename; it does not rename the local
file or encode it again. Use ASCII 8.3 names such as `CLIP.BIN` to avoid tilde
aliases in legacy directories. Legacy filenames must be representable in GBK;
the client also checks filename/size limits.

Uploads refuse existing names and possible short-name collisions. Add
`--overwrite` to authorize replacement. If the device returns an incomplete
list, replacement cannot be ruled out and upload also refuses to proceed
without `--overwrite`. Check `files` and its `issues` before using that override.

Upload reports distinguish transferred bytes, protocol completion and repeated
filename listing. `verified:false` and the content/persistence/playback flags
mean the client has not read stored bytes back, power-cycled the hardware or
observed physical video/audio playback. A listed name alone is not that proof.

A playback target can be a listed filename or a decimal firmware index:

```bash
povbin device files
povbin device play 1
```

Use the returned `index`, which can differ from a filename's number. Legacy
lists may contain FAT short aliases rather than the original long filenames.
Recovered entries in an incomplete directory carry diagnostics.

## Playback, power and loop controls

| Operation | Effect |
| --- | --- |
| `info` | Identify the connected display/protocol. |
| `status` | Read playback state and diagnostics. |
| `files` | Read filenames and firmware indices. |
| `play TARGET` | Select a listed name or index. |
| `pause` | Pause playback. |
| `resume` | Resume playback; unsupported on the HTTP family. |
| `next` | Advance; unsupported on the HTTP family. |
| `previous` | Select the previous file. |
| `power on` / `power off` | Set display power state. |
| `loop all` | Loop the playlist. |
| `loop single` | Repeat one file. |

```bash
povbin device pause
povbin device resume
povbin device power off
povbin device power on
povbin device loop single
```

Legacy controls have no explicit success ACK. `sent:true` reports transmission;
`requested_state_observed` reports a later matching playback/directory state
where available. Firmware can apply controls asynchronously, so the client
spaces requests and polls status. Not every setting has readback.

## Settings

```bash
povbin device settings
povbin device set ble off
povbin device set switcher on
povbin device set loop all
```

| Legacy key | Accepted values | Effect |
| --- | --- | --- |
| `ble` | `on`, `off`, `true`, `false` | Bluetooth setting. |
| `switcher` | `on`, `off`, `true`, `false` | Display power. |
| `loop` | `all`, `one` | Playlist or single-file looping. |

Legacy `settings` returns null values because current-value readback is not
available. Null means unknown. Legacy brightness, volume and Wi-Fi settings
are unsupported.

HTTP-family `settings` reads the firmware's configuration. `set KEY VALUE`
submits a key/value supported by that firmware; available keys are device-specific.
Values are parsed as JSON when possible, otherwise as text. Use quoted strings
for values containing spaces. Boolean power/BLE/loop values are mapped to the
corresponding firmware strings. Do not assume a key shown by another model works
on yours.

## Delete or format

```bash
povbin device delete CLIP.BIN --yes
povbin device format-card --yes
```

Deletion removes one file. Formatting **erases every file on the display's SD
card**. Both commands require `--yes`; formatting is not part of normal uploads.
The legacy format result includes `directory_empty_observed`, based on a complete
empty directory response. A sent command is insufficient evidence of formatting.

## Troubleshooting

- Cannot connect: verify the computer/phone is on the display network, then check
  `--host`. Try `--protocol legacy` if automatic detection is unsuitable.
- ADB phone unavailable: check `adb devices`, USB authorization and `--serial`.
- Slow replies: try a larger `--timeout`, for example `device --timeout 10 files`.
- Missing entries or wrong app model: read CLI `files`/`info` diagnostics. The client
  can recover later entries from some malformed legacy lists, but an incomplete
  response cannot establish the full directory.
- Upload status 0000: the client stops because observed transfers with this field
  did not retain their listings. Its firmware meaning is unknown. Check the card
  and directory rather than treating the sender's transmission as proof of success.
- Repeated upload failures: preserve needed files and inspect the card. Formatting
  resolved a malformed-directory case in hardware tests, but is destructive and
  is not a diagnosis or required fix for every failure.

Hardware tests cover F-Mini11 legacy connection, listing, upload, playback,
deletion and formatting. Direct sockets, HTTP operations and other control
packets have local wire tests. Physical effects of power, loop and BLE commands,
and HTTP-family hardware behavior, have not been verified.

## Python API

```python
from povbin import DeviceClient

# Omit adb_serial for a direct network connection.
with DeviceClient(host="192.168.4.1", protocol="legacy") as display:
    print(display.info())
    print(display.files())
    print(display.upload("CLIP.BIN"))
    print(display.play("CLIP.BIN"))
```

For phone transport, add `adb_serial="YOUR_DEVICE_SERIAL"`. Other methods include
`status()`, `settings()`, `set_setting(key, value)`, `pause()`, `resume()`,
`next()`, `previous()`, `power(bool)`, `loop(bool)`, `delete(target)` and
`format_card()`. The Python API does not require the CLI's `--yes` flags; calling
a destructive method directly is explicit intent. `upload(..., overwrite=True)`
authorizes replacement. Network/protocol errors raise `DeviceError` subclasses;
input validation can raise `ValueError` or `FileExistsError`.
