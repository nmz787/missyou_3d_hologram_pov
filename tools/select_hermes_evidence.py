"""Select artifact-qualified Hermes functions from hermes-dec's disassembly.

Defaults reproduce the Android file-list evidence in docs/evidence/android.
Run hbc-disassembler and hbc-decompiler first; this script never executes APK code.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re

SELECTED = {7128, 9082, 9083, 9132, 9133, 9134, 9135, 9136, 9141, 9142, 9266,
            9274, 9276, 9280, 9290, 9291, 9292, 9293, 9294, 12253,
            12322, 12323, 12343, 12344, 12345, 12359, 12360}
EXPECTED_BUNDLE = "8389750af87d60e75bbd7d93ba57d1bd239008812c8c5ef7ecc84cf2a46777e2"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, default=Path("analysis/android/index.android.bundle"))
    parser.add_argument("--disassembly", type=Path, default=Path("analysis/android/bundle.hasm"))
    parser.add_argument("--pseudo", type=Path, default=Path("analysis/android/bundle.pseudo.js"))
    parser.add_argument("--output", type=Path, default=Path("docs/evidence/android"))
    args = parser.parse_args()
    bundle = args.bundle.read_bytes()
    digest = hashlib.sha256(bundle).hexdigest()
    if digest != EXPECTED_BUNDLE:
        parser.error("Function selectors are specific to the supplied APK's exact Hermes bundle hash")
    assembly = args.disassembly.read_text()
    pattern = re.compile(r'^=> \[Function #(\d+) "([^"\n]*)" of (\d+) bytes\].*?@ offset 0x([0-9a-fA-F]+)$', re.M)
    matches = list(pattern.finditer(assembly))
    manifest, output = [], []
    for i, match in enumerate(matches):
        fid = int(match[1])
        if fid not in SELECTED:
            continue
        offset, size = int(match[4], 16), int(match[3])
        if offset + size > len(bundle):
            raise ValueError("Disassembler function range exceeds source bytes")
        manifest.append({"function_id": fid, "name": match[2], "bytecode_file_offset": offset,
                         "bytecode_bytes": size,
                         "raw_bytecode_sha256": hashlib.sha256(bundle[offset:offset + size]).hexdigest()})
        output.append(assembly[match.start():matches[i + 1].start() if i + 1 < len(matches) else len(assembly)])
    if {item["function_id"] for item in manifest} != SELECTED:
        raise ValueError("Not all selected functions were found")
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "file-list-bytecode.hasm").write_text(
        "Source: assets/index.android.bundle in supplied APK\nHermes bundle SHA256: " + digest +
        "\nTool: hermes-dec 0.1.6, Hermes bytecode 96; static disassembly, no APK execution.\n\n" + "".join(output))
    (args.output / "file-list-functions.json").write_text(
        json.dumps({"bundle_sha256": digest, "functions": manifest}, indent=2) + "\n")
    lines = args.pseudo.read_text().splitlines(keepends=True)
    for fid in [9292, 9293, 9132, 9290]:
        switch = (next(i for i, line in enumerate(lines) if f'_fun{fid}: for(' in line)
                  if fid != 9290 else next(i for i, line in enumerate(lines) if 'Original name: _handleData,' in line))
        start = switch
        while ' = function(' not in lines[start]:
            start -= 1
        depth = 0
        for end in range(start, len(lines)):
            depth += lines[end].count('{') - lines[end].count('}')
            if depth == 0:
                break
        # These four selected bodies have balanced braces in strings/regexes;
        # this selector is intentionally scoped to this exact artifact, not a JS parser.
        snippet = ''.join(lines[start:end + 1])
        snippet = snippet[snippet.index('function('):].strip().removesuffix(';')
        (args.output / f"function-{fid}.pseudo.js").write_text(snippet + "\n")
    print(f"Retained {len(manifest)} exact function ranges and four decompiled state machines.")


if __name__ == "__main__":
    main()
