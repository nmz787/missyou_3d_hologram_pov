"""Validate communication evidence byte ranges and build a retained-file index."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "docs/evidence/android/comms"
EXPECTED = "8389750af87d60e75bbd7d93ba57d1bd239008812c8c5ef7ecc84cf2a46777e2"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    bundle = (ROOT / "analysis/android/index.android.bundle").read_bytes()
    assert sha(bundle) == EXPECTED
    unique, total = {}, 0
    for name in ["legacy-control-functions.json", "legacy-upload-functions.json", "http-index.json"]:
        manifest = json.loads((FOLDER / name).read_text())
        assert manifest["bundle_sha256"] == EXPECTED
        for item in manifest["functions"]:
            fid = item["function_id"]
            offset = item.get("bytecode_file_offset", item.get("offset"))
            offset = int(offset, 16) if isinstance(offset, str) else offset
            size, digest = item["bytecode_bytes"], item["raw_bytecode_sha256"]
            assert sha(bundle[offset:offset+size]) == digest, (name, fid)
            value = (offset, size, digest)
            assert fid not in unique or unique[fid] == value
            unique[fid] = value
            total += 1
    manifest = json.loads((FOLDER / "discovery-index.json").read_text())
    assert manifest["bundle"]["sha256"] == EXPECTED
    for item in manifest["hermes_functions"]:
        fid, offset = item["function_id"], int(item["bundle_file_offset"], 16)
        size, digest = item["code_length"], item["original_code_sha256"]
        assert sha(bundle[offset:offset+size]) == digest, fid
        value = (offset, size, digest)
        assert fid not in unique or unique[fid] == value
        unique[fid] = value
        total += 1
    strings = json.loads((FOLDER / "http-strings.json").read_text())
    for item in strings:
        offset, size = int(item["offset"], 16), item["bytes"]
        assert sha(bundle[offset:offset+size]) == item["raw_sha256"], item["string_id"]
    symbols = json.loads((FOLDER / "legacy-upload-native-symbols.json").read_text())
    with zipfile.ZipFile(ROOT / "5D-Holo-android.apk") as archive:
        native = archive.read(symbols["apk_member"])
    assert len(native) == symbols["member_bytes"]
    assert sha(native) == symbols["member_sha256"]
    native_ranges = []
    for item in symbols["selected_symbols"]:
        offset, size = item["file_offset"], item["bytes"]
        assert sha(native[offset:offset+size]) == item["sha256"], item["name"]
        native_ranges.append(item)
    sender_manifest = json.loads((FOLDER / "legacy-upload-evidence-manifest.json").read_text())
    for item in sender_manifest["files"]:
        data = (ROOT / item["path"]).read_bytes()
        assert len(data) == item["bytes"] and sha(data) == item["sha256"], item["path"]
    records = []
    rea_records = []
    for path in sorted(FOLDER.iterdir()):
        if not path.is_file() or path.name == "evidence-index.json":
            continue
        data = path.read_bytes()
        assert data, f"Incomplete evidence file: {path}"
        if path.suffix == ".json":
            value = json.loads(data)
            if isinstance(value, dict) and "evidence_id" in value:
                rea_records.append({"file": path.name, "evidence_id": value["evidence_id"],
                                    "operation": value.get("operation"),
                                    "limitations": value.get("limitations", [])})
        records.append({"file": path.name, "bytes": len(data), "sha256": sha(data)})
    index = {"bundle_sha256": EXPECTED,
             "operation": "Static APK networking reconstruction and offline control construction replay",
             "verification": {"function_records_checked": total, "unique_function_ids": len(unique),
                              "http_string_ranges_checked": len(strings),
                              "native_library_sha256": sha(native),
                              "native_symbol_ranges_checked": native_ranges,
                              "control_construction_cases": 15},
             "records": records, "rea_records": rea_records,
             "supporting_tools": [{"file": str(path.relative_to(ROOT)), "sha256": sha(path.read_bytes())}
                                  for path in [ROOT / "tools/extract_android_control_evidence.py",
                                               ROOT / "tools/replay_android_legacy_controls.mjs",
                                               Path(__file__).resolve()]],
             "limits": ["No Android runtime, display connection or upload execution",
                        "User's active transport generation unobserved",
                        "Device-side session/firmware semantics unobserved",
                        "Native V2 HTTP upload body unverified",
                        "Missing file entries still require actual notification capture"]}
    (FOLDER / "evidence-index.json").write_text(json.dumps(index, indent=2) + "\n")
    print(f"Verified {total} function records ({len(unique)} unique IDs), {len(strings)} raw strings "
          f"and {len(native_ranges)} original native symbol ranges.")


if __name__ == "__main__":
    main()
