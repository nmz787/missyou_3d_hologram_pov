"""Retain exact Hermes byte ranges for shared design/export/conversion behavior."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SELECTED = {7783, 7784, 7785, 8259, 8292, 8328, 8332, 8358, 8359, 8360, 8361,
            8370, 8371, 8372, 12337, 15440, 15441, 15442, 15443, 15444, 15445,
            17402, 17405, 17406, 17407, 17268, 17269}
EXPECTED = "8389750af87d60e75bbd7d93ba57d1bd239008812c8c5ef7ecc84cf2a46777e2"


def main():
    bundle = (ROOT / "analysis/android/index.android.bundle").read_bytes()
    assert hashlib.sha256(bundle).hexdigest() == EXPECTED
    assembly = (ROOT / "analysis/android/bundle.hasm").read_text()
    pattern = re.compile(r'^=> \[Function #(\d+) "([^"\n]*)" of (\d+) bytes\].*?@ offset 0x([0-9a-fA-F]+)$', re.M)
    matches = list(pattern.finditer(assembly))
    records, excerpts = [], []
    for i, match in enumerate(matches):
        fid = int(match[1])
        if fid not in SELECTED:
            continue
        offset, size = int(match[4], 16), int(match[3])
        assert offset + size <= len(bundle)
        records.append({"function_id": fid, "name": match[2], "bytecode_file_offset": offset,
                        "bytecode_bytes": size,
                        "raw_bytecode_sha256": hashlib.sha256(bundle[offset:offset+size]).hexdigest()})
        excerpts.append(assembly[match.start():matches[i+1].start() if i+1 < len(matches) else len(assembly)])
    assert {r["function_id"] for r in records} == SELECTED
    folder = ROOT / "docs/evidence/android/features"
    (folder / "common-bytecode.hasm").write_text(
        "Static Hermes96 disassembly from exact supplied APK bundle; no APK execution.\n"
        + "Bundle SHA256: " + EXPECTED + "\n\n" + "".join(excerpts))
    (folder / "common-functions.json").write_text(
        json.dumps({"bundle_sha256": EXPECTED, "functions": records}, indent=2) + "\n")
    print(f"Retained {len(records)} artifact-qualified shared feature functions.")


if __name__ == "__main__":
    main()
