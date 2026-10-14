# Why the captured list omits the tractor in the recovered APK parser

The captured **194-byte** reply explicitly contains **13_TRA~1.bin**, indexed **15**, at byte offset **161**. Its final status is **15H711**, identifying current index 15, model flag H7 → F-MINI11, and playing state 11. Thus this capture demonstrates that the display returned a tractor entry. An app filename filter is not needed to explain why it disappears from the parsed list.

[packet-response.bin](packet-response.bin) preserves the bytes, SHA-256 **533d3e7a224c8050812071f315001048fc408e8c2a043feb961999597404303e**. They were supplied from the root agent's separate authorized phone/network capture. This analysis only reads the saved file; it makes no ADB/network/device requests.

## The malformed row moves the original parser to the wrong offset

The first five rows parse normally. Row 6 starts at **97**, declares length **16**, and claims to end at **115**. Applying the APK's fixed record arithmetic produces the name **04in131212.**. However, a structurally valid next row actually starts at **108**; the declared row overlaps its length/index prefix.

| Wire offset | Index | Bounded filename | Original parser outcome |
| ---: | ---: | --- | --- |
| 9 | 1 | 00_B.bin | Published |
| 24 | 2 | 01CHRI~1.bin | Published |
| 43 | 3 | 01_LC.bin | Published |
| 59 | 4 | 02FATH~1.bin | Published |
| 78 | 5 | 03FATH~1.bin | Published |
| 97 | 6 | Declared row overlaps the next row | Publishes malformed 04in131212. |
| 108 | 12 | 10CD.bin | Missed |
| 123 | 13 | 11CC30~1.bin | Missed |
| 142 | 14 | 12E8F9~1.bin | Missed |
| 161 | 15 | 13_TRA~1.bin | Missed |

The original parser advances to **115**, where bytes are `10CD.bin`: it reads length `10` and attempts to parse index **CD**. It logs **Invalid index at offset 115: CD**, then exits the record loop while keeping its parsed prefix. `_parseFileList` is Hermes function **#9292**, bundle base **0x002a1bb9**: relative **0xef** branches to the invalid-index handler **0x18d**, then **0x1f9** starts tail parsing. [packet-parser-bytecode.hasm](packet-parser-bytecode.hasm) retains the exact instructions and related methods; [packet-index.json](packet-index.json) pins their original byte hashes.

## The malformed tail also corrupts model and current-index parsing

Because the loop stops early, the tail regex scans from offset 115 through 188, which includes later filenames. Its first unanchored match is **313.11** at **126**, split into groups **31**, **3.**, and **11**. `_parseModel` #9291 takes the second character of `3.`—the dot—and falls back to **F1**. The controlled replay therefore publishes **six rows**, **current index 31**, **isPlaying=true**, and **model F1**, even though the real final tail says index15/F-MINI11. This is the exact parser state produced by the recovered method on these captured bytes; it is not a dump of the running Android app's memory.

[packet-original-replay.json](packet-original-replay.json) records these results, original-to-UI formatting, diagnostics, offsets, source hashes and assertions. [packet-replay.mjs](packet-replay.mjs) repeats the offline replay using the extracted decompiler state machines. It supplies local Buffer/GBK/log dependencies, injects per-function register declarations, and applies the previously documented logging-only variadic-call repair using raw #9292 relative 0x17a. It does not execute APK bytecode or launch Android.

## Project recovery on the same bytes

The project's pure `_parse_notification` function detects the overlap, discards the malformed row, and resumes at **108**. It returns **nine valid rows**, including all four later rows and the tractor; status parsing anchors to **15H711** at offset180. It reports **complete=false** with **Record at byte 97 overlaps a later record; discarded**, preserving the incomplete-list distinction.

[packet-project-replay.json](packet-project-replay.json) records the project module hash and result from that offline call. The independent bounded recovery oracle inside the original replay also identifies nine `.bin` records and the same final status; that oracle is an analyst strategy, separate from APK behavior and the final project implementation.

The malformed wire bytes do not establish the full original name behind fragment `04in`, why firmware emitted the conflicting length, or whether additional directory entries were omitted upstream. The response contains no NUL bytes. Names returned by firmware are short aliases; this replay neither renames files nor reconverts media. The captured corruption and recovered parser behavior supply a concrete explanation for missing later UI entries, including the tractor, while physical app execution remains outside this replay's evidence.
