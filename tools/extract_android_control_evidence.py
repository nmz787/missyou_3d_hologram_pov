"""Retain exact legacy TCP control functions and focused readable state machines."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "docs/evidence/android/comms"
EXPECTED = "8389750af87d60e75bbd7d93ba57d1bd239008812c8c5ef7ecc84cf2a46777e2"
METHODS = {9294: "heartBeat", 9298: None, 9304: None, 9305: "playFile",
           9307: "playPrevious", 9308: "playNext", 9309: "playPause",
           9310: "playPlay", 9311: "bytesToHex", 9316: None,
           9320: None, 9324: None, 9328: None}


def main():
    bundle = (ROOT / "analysis/android/index.android.bundle").read_bytes()
    assert hashlib.sha256(bundle).hexdigest() == EXPECTED
    hasm = (ROOT / "analysis/android/bundle.hasm").read_text()
    pattern = re.compile(r'^=> \[Function #(\d+) "([^"\n]*)" of (\d+) bytes\].*?@ offset 0x([0-9a-fA-F]+)$', re.M)
    matches = list(pattern.finditer(hasm))
    records, excerpts = [], []
    for i, match in enumerate(matches):
        fid = int(match[1])
        if not 9266 <= fid <= 9328:
            continue
        offset, size = int(match[4], 16), int(match[3])
        records.append({"function_id": fid, "name": match[2], "bytecode_file_offset": offset,
                        "bytecode_bytes": size,
                        "raw_bytecode_sha256": hashlib.sha256(bundle[offset:offset+size]).hexdigest()})
        excerpts.append(hasm[match.start():matches[i+1].start()])
    assert len(records) == 63
    FOLDER.mkdir(parents=True, exist_ok=True)
    (FOLDER / "legacy-control-bytecode.hasm").write_text(
        "Static Hermes96 disassembly, no APK execution.\nBundle SHA256: " + EXPECTED + "\n\n" + "".join(excerpts))
    (FOLDER / "legacy-control-functions.json").write_text(
        json.dumps({"bundle_sha256": EXPECTED, "functions": records}, indent=2) + "\n")
    pseudo = (ROOT / "analysis/android/bundle.pseudo.js").read_text()
    scope_start, scope_end = pseudo.index("Original name: TCPClient,"), pseudo.index("_waitSendFileInfoAck")
    for fid, name in METHODS.items():
        needle = f"Original name: {name}," if name else f"_fun{fid}: for("
        position = pseudo.index(needle, scope_start, scope_end)
        start = pseudo.rfind("function", 0, position)
        # All selected bodies have balanced braces in their strings. This selector
        # is deliberately scoped to this bundle and is not a general JS parser.
        depth, seen = 0, False
        for end in range(start, len(pseudo)):
            if pseudo[end] == "{":
                depth += 1
                seen = True
            elif pseudo[end] == "}":
                depth -= 1
            if seen and depth == 0:
                break
        (FOLDER / f"legacy-control-{fid}.pseudo.js").write_text(pseudo[start:end+1] + "\n")
    print("Retained 63 raw functions and 13 focused command state machines.")


if __name__ == "__main__":
    main()
