"""Retain exact upload-related Hermes functions without executing APK code."""

import hashlib
import json
from pathlib import Path
import re


def main():
    bundle = Path("analysis/android/index.android.bundle").read_bytes()
    digest = hashlib.sha256(bundle).hexdigest()
    expected = "8389750af87d60e75bbd7d93ba57d1bd239008812c8c5ef7ecc84cf2a46777e2"
    if digest != expected:
        raise ValueError("Selectors require the exact supplied APK Hermes bundle")
    assembly = Path("analysis/android/bundle.hasm").read_text()
    pattern = re.compile(r'^=> \[Function #(\d+) "([^"\n]*)" of (\d+) bytes\].*?@ offset 0x([0-9a-fA-F]+)$', re.M)
    matches = list(pattern.finditer(assembly))
    selected = {5334, 9265, 9266, 9290, *range(9329, 9350)}
    manifest, snippets = [], []
    for i, match in enumerate(matches):
        fid = int(match[1])
        if fid not in selected:
            continue
        offset, size = int(match[4], 16), int(match[3])
        code = bundle[offset:offset + size]
        if len(code) != size:
            raise ValueError("Function range exceeds source bundle")
        manifest.append({"function_id": fid, "name": match[2],
                         "bytecode_file_offset": offset, "bytecode_bytes": size,
                         "raw_bytecode_sha256": hashlib.sha256(code).hexdigest()})
        snippets.append(assembly[match.start():matches[i + 1].start() if i + 1 < len(matches) else len(assembly)])
    if {item["function_id"] for item in manifest} != selected:
        raise ValueError("Missing selected function")
    output = Path("docs/evidence/android/comms")
    output.mkdir(parents=True, exist_ok=True)
    (output / "legacy-upload-bytecode.hasm").write_text(
        "Source: assets/index.android.bundle in 5D-Holo-android.apk\n"
        f"Hermes bundle SHA256: {digest}\n"
        "Tool: hermes-dec 0.1.6; Hermes bytecode 96; no APK execution.\n\n" + "".join(snippets))
    lines = Path("analysis/android/bundle.pseudo.js").read_text().splitlines(keepends=True)
    slices = [(335509, 336259)]
    text = "".join(f"// Original pseudo.js lines {start}..{end}\n" + "".join(lines[start - 1:end])
                   for start, end in slices)
    (output / "legacy-upload.pseudo.js.txt").write_text(text)
    (output / "legacy-upload-functions.json").write_text(json.dumps({
        "apk_sha256": "8a83b1f128beb43341eefd2b4ad743512d0193ff6dd4e7b56feba138fb4b63c9",
        "bundle_sha256": digest, "functions": manifest,
        "pseudo_source_slices": [{"path": "analysis/android/bundle.pseudo.js", "start_line": a, "end_line": b}
                                 for a, b in slices],
        "limitations": ["Static disassembly/decompiler output; target APK not executed.",
                        "Function IDs and byte offsets are specific to this artifact."]}, indent=2) + "\n")
    names = ["_recvAckOfSendFileInfo", "_recvAckOfIntervalPkgs", "_waitSendFileInfoAck",
             "_waitSendPackagesIntervalAck", "_connectUploadSocket", "_disconnectUploadSocket"]
    hits = {name: [] for name in names}
    for lineno, line in enumerate(assembly.splitlines(), 1):
        for name in names:
            if f"String: '{name}'" in line:
                hits[name].append({"hasm_line": lineno, "instruction": line})
    (output / "legacy-upload-reference-search.json").write_text(json.dumps({
        "bundle_sha256": digest,
        "search_boundary": "All property-identifier instruction references in complete bundle.hasm",
        "hits": hits,
        "limitation": "Does not exclude indirect dynamic lookup or code outside this artifact."}, indent=2) + "\n")
    print(f"Retained {len(manifest)} exact function ranges")


if __name__ == "__main__":
    main()
