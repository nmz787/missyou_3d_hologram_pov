# How 5DDisplayer converts video into offline `.bin` files

The supplied `5DDisplayer.exe` is an Advanced Installer self-extracting package.
Its embedded application is a .NET Framework 4.6.1 assembly, version 1.0.2.0.
The offline export is a header followed by fixed-size LED/audio records and
a zero trailer. It uses the `F20AD.Utils.Bin` encoder. The separately recovered
`FTLV` JPEG container and configurable `Connect.BinTool` encoder are other paths.

This report distinguishes static artifact observations, controlled replay of
isolated original methods, and the playback assumptions in the Python feature.
Initial binary reconstruction did not involve a connected physical display.
The user subsequently confirmed successful video and audio playback of a
type-7 export on their display; see the hardware validation below.

The user reports a paper manual labeled **MS2 (Mini12)** and a connected phone
app identifying the unit as **F-Mini11**. The recovered application's F-Mini11
selection is **type 7**, making it the initial profile used in the project examples.
That label is user-provided runtime context, not independent hardware inspection.
The reported Wi-Fi upload failures remain undiagnosed. A subsequent read-only
inspection found the mounted SD card only 7% used, with about 3.6 GiB free.

## Artifact identity and extraction

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| Supplied installer | 106498403 | `8bee60df3fe0b039dff1633999b1ae23e20663d0799e62f040651fed97ac2e07` |
| Extracted application | 2433024 | `678a03614e6f25819c15a2a5d90d7637fddf79f12efd38f9d924482af27868be` |

The footer ends in `ADVINSTSFX`. Its UTF-16 file-table entry
`75166CB\FILES.7z` identifies offset `0x252e00` and length `0x2459225`.
The archive's first 512 bytes are XORed with `0xff`. Undoing that transform
recovers a valid 7z archive; extraction verifies member CRCs. It includes the
managed application, FFmpeg DLLs, TurboJPEG, and framework dependencies.
The separate `75166CB\5DDisplayer.7z` entry at `0x26ac025`, length `0x7a282`,
contains MSI packages. The much larger .NET prerequisite occupies another region.

As an independent extraction check, the original installer was invoked under
an isolated Wine prefix with extraction switches. Its resulting application
matched the independently recovered member byte-for-byte; that limited runtime
observation is recorded in [installer-extraction-replay.json](evidence/installer-extraction-replay.json).
The converter GUI was never launched. Duplicate extraction files and the
temporary Wine prefix were removed after recording this check.

The reproducible [extractor](../tools/extract_installer.py) checks both artifact
hashes and records the archive offset, transformation, member list, and hashes.
REA's [saved evidence bundle](evidence/rea-evidence.json) contains complete
managed artifact identity (`ev_6876a1602c41731d3d6624822580f08d346eb52e25796d635b1cb0c60efbdd01`).
Its managed-member request exceeded a 64 MiB representation budget and returned
**unavailable coverage** (`ev_6f800d142072c8d8c2d43c1990afeb1f86f86ba75db8590d6e4f4d939850594d`).
Method behavior below is established independently using dnfile/dncil and ILSpy,
then corroborated by controlled replay. The payload's managed code made native
Ghidra analysis unnecessary for this conversion path.

## Observed conversion chain

The [full CIL listing](evidence/conversion.cil.txt) gives each method's token,
RVA, file offset, signature, raw IL SHA-256, and code-relative IL offsets.
Tokens are specific to the extracted application's hash and MVID
`74a69eeb-4027-4f36-9516-a409bdfb74bf`.

1. `TransformWindow.SendWork` (`0x0600024b`) starts frame extraction and cropping.
   `YTPlayer.GetFrames` (`0x0600053d`) decodes through FFmpeg into BGR24, selects
   frames using source-FPS/output-FPS arithmetic, applies optional mirrors,
   and saves intermediate JPEGs. `DrawTool.ImageClip` (`0x06000415`) crops/resizes
   the selected device region into a square JPEG; the default working width is 672.
2. `VideoStreamDecoder.extractAudio` (`0x06000513`) resamples audio to mono,
   32,000 samples/second, `AV_SAMPLE_FMT_U8`, and saves a WAV with a 44-byte header.
3. `TcpServer.SendFile` (`0x06000619`) calls `ExportVideo` (`0x06000627`) when
   an export directory is set. This selects `ConvertToFTLVWork` (`0x06000628`).
   Despite that method's name, it constructs `Utils.Bin`, not `Utils.FTLV`.
4. `ConvertToFTLVWork` writes `Bin.getHeader()` once. For every cropped JPEG
   it calls `bitmapToBin(bitmap, width/2, width/2, width)`, writes that pixel
   payload, then writes a 1,600-byte audio slot. With audio, it skips the WAV's
   first 44 bytes and reads successive samples; without audio the slot stays zero.
   It appends **100,000 zero bytes** after the final record.

For direct evidence, search the listing for `ConvertToFTLVWork`: its constants
`1600` and `100000`, calls to `getHeader` and `bitmapToBin`, and consecutive
`FileStream.Write` calls establish the actual layout. The trailing bytes do not
contain an index, checksum, frame count, or duration.

## File layout

```text
offset 0                 variable header (4..1024 bytes)
offset H                 frame 0 packed LED video
offset H + V             frame 0 audio (1600 bytes)
offset H + (V+1600)       frame 1 packed LED video
...                      remaining fixed-size records
offset H + N*(V+1600)     100000 zero bytes
```

`V = angular_rows * ceil(3 * LEDs / 8) * bits_per_channel`.
Total file size is `H + N * (V + 1600) + 100000`. For F1, `V=137280`, so each
record is 138880 bytes. Frame count can be recovered from file length after
selecting a profile. Neither FPS nor an audio-presence flag is recorded.

### Header

`Bin.getHeader` (`0x060003e8`) and `TypeConversion.GetBytes(string,int)`
(`0x060004b4`) establish:

```python
type_byte = ord(str(device_type)[0])
a, b = random_byte_0_through_254(), random_byte_0_through_254()
H = (offset_image[type_byte ^ a ^ b] + 1) * 4
header[0:4] = bytes([0xEE, type_byte, a, b])
for i in range(4, H):
    header[i] = header[i-1] ^ offset_image[i % 255]
```

The type is **ASCII**, not a numeric byte. Types 10 and 11 both become `0x31`
(`'1'`), also used by type 1. This reproduces the original bug and means the
header cannot uniquely distinguish these profiles. Filler uses `%255`, not
`%256`. There is no encryption of the subsequent frame payload.

The complete 256-byte `offset_image` table is recorded in [luts.json](evidence/luts.json),
from FieldRVA `0x250010`, file offset `0x24e210`, SHA-256
`2f1ee281848602f6204161d2571044c5ef136c0d6e609643b9a8074bca4f1b44`.
For nonce `01 02` and F1, the header starts `EE 31 01 02` and is 856 bytes long.

### Sampling and gamma

`Bin.makeModel` (`0x060003ec`) samples angular rows around the image center.
At angle zero, it starts on the right edge and walks inward. Positive angles
move upward in the top-down image. Outer radius is `(diameter-4)/2` and radial
step is `radius/LEDs`. For every sample:

```text
x = trunc(radius_at_LED * cos(angle) + center_x)
y = trunc(center_y - radius_at_LED * sin(angle))
source_pixel = (x-1, y-1)
```

Samples outside `0<x<width` and `0<y<height` are black. Radius is reduced by
repeated subtraction, and angle grows by repeated addition of `360/rows`.
Those floating-point operations matter at pixel boundaries. The original uses
24-bit BGR memory and preserves B,G,R order in this path.

Each color byte passes through the **exact** `gamma_tab` lookup table from
FieldRVA `0x250110`, file offset `0x24e310`, SHA-256
`4fe1cdb64658f8dcf02c2507a1085b12abe75f5efc089cb120e213b6253620ec`.
For example, input 31 maps to 1, input 128 to 68, and input 255 to 255.
It is not replaced with a guessed gamma exponent in Python.

Types 5, 6, and 8 instead select `makeModelNotRotate` (`0x060003eb`). Output
rows run across x; LEDs run vertically down a central strip of height `width/3`.
The original extra one-pixel y offset and strict bounds are reproduced for
square, aligned input. See [pixel-findings.md](evidence/pixel-findings.md) for
the full strip formula and the other, device-configured encoder's behavior.

### Packing

`Bin.bgrToBin` (`0x060003ea`) emits, in order:

1. Angular row.
2. Bitplane: input bit 7 down through bit `8-bits_per_channel`.
3. Radial LED, outermost to innermost.
4. Channel: B, G, R.

Output bits are MSB-first. Every row/bitplane takes `ceil(3*LEDs/8)` bytes.
Padding is **at the beginning of the first byte** of each plane. F1 has four
leading zero bits, F4 seven, and F5 one. Lower color bits are discarded after
the gamma lookup. This is a planar LED drive representation, not RGB565 or JPEG.

## Original device profiles

`Bin::.ctor` (`0x060003e6`) provides geometry and bit depth. Names and IDs are
established by `TransformWindow::.ctor` (`0x0600022d`) and
`Device_SelectionChanged` (`0x06000247`); UI order differs from type order.

| CLI type | Original label | Rows | LEDs | Bits | Mapping | Video bytes/frame |
| ---: | --- | ---: | ---: | ---: | --- | ---: |
| 1 | F1 | 520 | 116 | 6 | polar | 137280 |
| 2 | F2 | 520 | 144 | 6 | polar | 168480 |
| 3 | F3 | 520 | 200 | 6 | polar | 234000 |
| 4 | F-Mini18 | 360 | 80 | 5 | polar | 54000 |
| 5 | F-360A | 520 | 80 | 6 | strip | 93600 |
| 6 | F-360B | 520 | 144 | 6 | strip | 168480 |
| 7 | F-Mini11 | 300 | 48 | 5 | polar | 27000 |
| 8 | F-360C | 520 | 200 | 6 | strip | 234000 |
| 9 | F-Mini20 | 360 | 96 | 5 | polar | 64800 |
| 10 | F4 | 450 | 171 | 6 | polar | 175500 |
| 11 | F5 | 520 | 133 | 6 | polar | 156000 |

## Reconstruction and validation

The implementation in [codec.py](../povbin/codec.py) preserves the original
tables, header, sampling coordinates, channel order, quantization, and leading
padding. [media.py](../povbin/media.py) supplies FFmpeg decoding, cropping,
resampling, and a streaming writer. Output is published only after successful
conversion; failures remove the temporary output. FAT filesystems, such as SD
cards, use exclusive creation and copy the completed conversion when hard links
are unavailable. Existing files require an
explicit overwrite option. Inspection verifies the header, frame alignment,
and zero trailer and reports candidates rather than silently resolving a type alias.

The [replay harness](../tools/replay_original/Program.cs) loads the extracted
original assembly and invokes its constructor, `makeModel`/`makeModelNotRotate`,
`bgrToBin`, and `getHeader` by reflection. It does not start the original GUI,
entry point, network methods, or bitmap APIs. This ran under **.NET 8.0.32 on
Linux**, not the original Windows .NET Framework runtime.

For each of the eleven profiles, the following matched byte-for-byte:

- Sampling of a 672×672 synthetic BGR image defined by
  `channel[x,y,c] = (17*x + 31*y + 73*c) & 255`.
- Complete bit packing of that sampled image.
- Packing of an independent channel pattern
  `sample[i] = (37*i + 11*floor(i/256)) & 255`.
- Full original headers regenerated using their recorded nonce bytes.

Hashes and original header bytes are recorded in [original-replay.json](evidence/original-replay.json).
The normal Python test suite consumes these original-method goldens. Integration
tests also convert a real 30 fps video into 20 fps records, verify PCM against
decoded source audio, check all frame boundaries and trailer bytes, and test
trimming, absent audio, bad input, and output preservation.

One additional test video with audio was converted successfully: 0.6 seconds,
12 frames, F1, 856-byte header, total file length 1,767,416 bytes. The generated
files are `analysis/sample.mp4`, `analysis/sample.bin`, and `analysis/preview.png`.
An additional F-Mini11 demo is generated at `analysis/mini11-demo.bin`; it uses
the same 12-frame clip with zero-filled audio slots and the exact type-7 layout.

### Hardware validation and filename observations

The user converted `VID_20260928_174649_506.mp4` with type 7, copied the resulting
file to the SD card, reinstalled the card, and powered on the display. They
reported that **both video and audio played successfully**. The recorded export
has 9 frames (0.45 seconds at 20 fps), a 772-byte header, and total size 358172
bytes: `772 + 9*(27000+1600) + 100000`. This is user-observed validation of the
tested clip and physical F-Mini11 unit, not hardware coverage for all profiles.

The app's tilde filenames were investigated by opening the mounted VFAT root
directory read-only and using `VFAT_IOCTL_READDIR_BOTH`, defined in the local
Linux header `/usr/include/linux/msdos_fs.h`. This returns both stored short and
long names without changing files. [The snapshot](evidence/sd-card-filenames.json)
contains the complete root-name pairs and filesystem capacity:

| Long filename on card | Observed short filename |
| --- | --- |
| `01Christmas.bin` | `01CHRI~1.BIN` |
| `02Father Christmas.bin` | `02FATH~1.BIN` |
| `13_tractor.bin` | `13_TRA~1.BIN` |
| `14_cd.bin` | `14_CD.BIN` |

The observed aliases match the user's app labels. FAT short names support eight
base-name characters and a three-character extension; tildes commonly appear in
aliases of long names. [Microsoft's filename documentation](https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-file)
describes these aliases. The inference is that the display/app path exposes the
stored short name. The exact layer selecting that name, any extension removal,
and any firmware-side name changes remain unobserved. The subsequent
[Android APK analysis](android.md) establishes an app-side punctuation transform:
`00_B.bin` becomes `00.B`. The mapper retains all entries, so aliasing alone
does not explain the missing tractor and CD files. That report documents the
legacy list parser, controlled failure replays, and the remaining response-capture gap.

Use names of at most eight uppercase ASCII letters/digits before `.BIN` for
readable labels, for example `CD.BIN` or `CHRIS01.BIN`. This concerns the filesystem
name, not the encoded header or video data. No existing SD files were renamed.

### Playback assumptions and differences

- The MISSYOU branding does not establish a hardware profile. Use the selection
  that works in the supplied application; type-7 playback has now been confirmed
  by the user for one clip. Firmware requiring the other configurable/JPEG paths is
  outside this implementation's scope.
- Fixed 1,600-byte audio slots and 32 kHz U8 mono imply a consistent **20 fps**
  cadence. Python enforces that cadence; the original GUI can choose lower
  source FPS yet still writes 1,600 bytes per frame, creating a possible timing
  mismatch. Physical firmware timing is not established by the application code.
- FFmpeg preprocessing replaces the original GUI crop controls, Windows GDI
  resizing, and two intermediate JPEG passes. Pixel encoding is reproduced;
  complete video output need not be identical after those different preprocessing
  steps or across decoder versions.
- Python safely handles missing audio and fills exhausted real audio with U8
  midpoint silence (`0x80`). The original reuses a 1,600-byte buffer across reads
  and can leave stale bytes at a short read; it also calls `Close()` on a null
  audio stream after writing files without audio. Those defects are not reproduced.
- Square working sizes must be multiples of four. The original's pixel indexing
  ignores stride, so non-aligned widths are unsuitable for byte compatibility.

## Reproduce the analysis

```bash
# Analysis-only dependencies; the converter itself needs neither .NET nor Ghidra.
.venv/bin/pip install py7zr dnfile dncil
.venv/bin/python tools/extract_installer.py 5DDisplayer.exe --output analysis/reextracted
.venv/bin/python docs/evidence/dump_cil.py analysis/reextracted/5DDisplayer.exe --output-dir analysis/rechecked-cil

# Optional: ILSpy 9.1.0.7988 was used to generate readable C# in analysis/decompiled.
DOTNET_ROOT="$PWD/tools/dotnet" tools/ilspy/ilspycmd -p -o analysis/decompiled-copy analysis/reextracted/5DDisplayer.exe

# Replay only isolated original conversion methods; writes fixtures/manifest.
DOTNET_ROOT="$PWD/tools/dotnet" tools/dotnet/dotnet run --project tools/replay_original -- analysis/reextracted/5DDisplayer.exe analysis/replayed

.venv/bin/python -m unittest discover -s tests -v
```

The locally installed .NET SDK and ILSpy are analysis helpers under `tools/`;
the supplied Ghidra and JDK are preserved. Source binary bytes are unchanged.
