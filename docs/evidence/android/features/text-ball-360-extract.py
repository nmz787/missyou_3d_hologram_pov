#!/usr/bin/env python3
"""Recover exact sphere strings and audit selected raw Hermes function ranges."""
import ast
import bisect
import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[4]
OUT = pathlib.Path(__file__).resolve().parent
SOURCE = ROOT / "analysis/android/bundle.hasm"
data = SOURCE.read_text()
bundle = (ROOT / "analysis/android/index.android.bundle").read_bytes()
headers = list(re.finditer(r'^=> \[Function #(\d+) "(.*?)" of (\d+) bytes\].*?@ offset (0x[0-9a-f]+)', data, re.M))
newlines = [i for i, ch in enumerate(data) if ch == "\n"]
functions = {int(h[1]): (h, data[h.start():headers[i + 1].start()] if i + 1 < len(headers) else data[h.start():]) for i, h in enumerate(headers)}
ids = list(range(17397, 17444)) + list(range(17467, 17490)) + list(range(18765, 18823)) + list(range(8355, 8380))
rows, parts = [], []
for ident in ids:
    if ident not in functions:
        continue
    h, text = functions[ident]
    offset, count = int(h[4], 16), int(h[3])
    rows.append(dict(id=ident, name=h[2], bundle_offset=h[4], bytecode_bytes=count,
                     bytecode_sha256=hashlib.sha256(bundle[offset:offset + count]).hexdigest(),
                     hasm_lines=[bisect.bisect_left(newlines, h.start()) + 1, bisect.bisect_left(newlines, h.start() + len(text))]))
    parts.append(text)
(OUT / "text-ball-360-functions.hasm").write_text("".join(parts))
manifest = dict(apk_sha256=hashlib.sha256((ROOT / "5D-Holo-android.apk").read_bytes()).hexdigest(),
                bundle_sha256=hashlib.sha256(bundle).hexdigest(), disassembler="hermes-dec 0.1.6, Hermes v96",
                offset_scope="absolute bytecode offsets in extracted APK assets/index.android.bundle", functions=rows)
(OUT / "text-ball-360-functions.json").write_text(json.dumps(manifest, indent=2) + "\n")
strings = {}
for line in functions[17470][1].splitlines():
    if "<LoadConstString>" not in line:
        continue
    match = re.search(r'string_id: (\d+)>  # String: (.*) \((?:String|Identifier)\)$', line)
    if match:
        strings[int(match[1])] = ast.literal_eval(match[2])
(OUT / "text-ball-360-sphere-fragments.json").write_text(json.dumps(strings, ensure_ascii=False, indent=2) + "\n")
(OUT / "text-ball-360-sphere-script.template.js").write_text(strings[693] + "{{TEXT}}" + strings[786] + "{{PLATFORM}}" + strings[9457] + "{{COLOR}}" + strings[9458])
(OUT / "text-ball-360-sphere-html.template.html").write_text(strings[9459] + "{{COLOR}}" + strings[565])
fragments = []
for ident in [693, 786, 9457, 9458, 9459, 565]:
    value = strings[ident]
    matches = []
    for encoding in ["utf-8", "utf-16le"]:
        payload = value.encode(encoding)
        offset = bundle.find(payload)
        if offset >= 0:
            matches.append(dict(encoding=encoding, bundle_offset=f"0x{offset:08x}", byte_count=len(payload), sha256=hashlib.sha256(payload).hexdigest()))
    if not matches:
        raise RuntimeError(f"Decoded string {ident} was not found verbatim in bundle")
    fragments.append(dict(string_id=ident, source_function=17470, direct_bundle_matches=matches))
(OUT / "text-ball-360-fragment-offsets.json").write_text(json.dumps(fragments, indent=2) + "\n")
