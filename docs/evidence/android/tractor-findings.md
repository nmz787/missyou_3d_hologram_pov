# SD-card structure comparison for the missing tractor video

Direct, read-only inspection on the client date 2026-10-13 found no structural
defect in `13_tractor.bin` under the original F-Mini11 offline export format.
No SD-card files were changed and no commands were sent to the display.
The complete byte-level observations, hashes, and boundary samples are in
[tractor-file.json](tractor-file.json).

| Field | `13_tractor.bin` | Working `14_cd.bin` |
| --- | ---: | ---: |
| Marker | ASCII `7` | ASCII `7` |
| Header prefix | `ee 37 db 44` | `ee 37 e7 d1` |
| Header length | 764 | 772 |
| Frame count | 238 | 9 |
| Video bytes per frame | 27,000 | 27,000 |
| Audio bytes per frame | 1,600 | 1,600 |
| Payload bytes | 6,806,800 | 257,400 |
| Zero trailer bytes | 100,000 | 100,000 |
| File bytes | 6,907,564 | 358,172 |
| Duration at the export path's 20 fps | 11.9 seconds | 0.45 seconds |

Both headers reproduce the recovered original header algorithm exactly,
including every filler byte. Both payloads contain an integral number of
28,600-byte records and have the complete zero trailer. Every tractor video
slot contains nonzero data; every audio slot contains nonzero data. These byte
checks do not establish perceptual video or audio quality.

The tractor file on the card is byte-identical to the local
`/home/nathan/git/5d_pov/13_tractor.bin`; its SHA-256 is
`7267a68ae34cb2da2166befafa806b5526a863445c640d444ca1e8003ce9c3c5`.
The CD file on the card is likewise byte-identical to local `cd.bin`; its
SHA-256 is `9313725e3f4aa0a866255fb102871786ce1599a4c7521c391e04417d2b25d404`.
The user previously reported successful video and audio playback of the CD
export. Tractor playback was not observed during this investigation.

Ten other preloaded card files pass the same complete offline-export checks,
all with type marker `7`. For example, `04count.bin` has 940 records and is
26,984,416 bytes. The tractor is within the size range of these preloaded
files. `00_B.bin`, `01_LC.bin`, and `11cc30e49.bin` have valid recovered type-7
headers but fail the standard trailer/length checks; this establishes a
difference from the reconstructed export format, not that firmware rejects
them. They might be special, padded, or incomplete files. Their acceptance
and roles remain unobserved.

The format basis is the existing original C# method evidence:

- [`Bin::.ctor`, token `0x060003e6`](../conversion.cil.txt#L429): type-7 geometry.
- [`Bin::getHeader`, token `0x060003e8`](../conversion.cil.txt#L682): marker,
  variable header length, and filler sequence.
- [`TcpServer::ConvertToFTLVWork`, token `0x06000628`](../conversion.cil.txt#L3872):
  frame payload, 1,600-byte audio slots, and 100,000-byte zero trailer.
- [Original-method replay](../original-replay.json): independent original
  isolated-method results used to validate the Python reconstruction.
- [Existing FAT filename observation](../sd-card-filenames.json):
  `13_tractor.bin` is stored with the short alias `13_TRA~1.BIN`.

Wrong device type, malformed header filler, partial frame data, a missing
trailer, and corruption during the local-to-card copy are therefore unsupported
explanations for the missing app entry. Whether firmware enumerates the short
alias, how the app parses that response, and whether a stale list was shown
require separate protocol/app evidence. File validity alone cannot settle them.
