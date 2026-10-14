"""Verify retained feature byte ranges against the original APK bundle; index files."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "docs/evidence/android/features"
EXPECTED = "8389750af87d60e75bbd7d93ba57d1bd239008812c8c5ef7ecc84cf2a46777e2"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(name):
    return json.loads((FOLDER / name).read_text())


def main():
    bundle = (ROOT / "analysis/android/index.android.bundle").read_bytes()
    assert sha(bundle) == EXPECTED
    functions = {}
    total_records = 0
    for name in ["common-functions.json", "spinning-box-functions.json",
                 "text-ball-360-functions.json", "marquee-gallery-index.json"]:
        manifest = read(name)
        assert manifest["bundle_sha256"] == EXPECTED
        for item in manifest.get("functions", manifest.get("function_ids", [])):
            fid = item.get("function_id", item.get("id"))
            offset = item.get("bytecode_file_offset", item.get("bundle_offset", item.get("offset")))
            offset = int(offset, 16) if isinstance(offset, str) else offset
            size = item["bytecode_bytes"]
            digest = item.get("raw_bytecode_sha256", item.get("bytecode_sha256"))
            assert 0 <= offset < offset+size <= len(bundle)
            assert sha(bundle[offset:offset+size]) == digest, (name, fid)
            current = (offset, size, digest)
            assert fid not in functions or functions[fid] == current
            functions[fid] = current
            total_records += 1
    assert {17401, 17644, 17578, 18769, 17694}.issubset(functions)
    string_records = 0
    for item in read("spinning-box-strings.json")["strings"]:
        offset, size = item["raw_file_offset"], item["raw_bytes"]
        assert sha(bundle[offset:offset+size]) == item["raw_sha256"]
        string_records += 1
    for item in read("marquee-gallery-strings.json"):
        offset, size = int(item["offset"], 16), item["bytes"]
        assert sha(bundle[offset:offset+size]) == item["raw_sha256"]
        string_records += 1
    for item in read("text-ball-360-fragment-offsets.json"):
        assert item["direct_bundle_matches"]
        for match in item["direct_bundle_matches"]:
            offset, size = int(match["bundle_offset"], 16), match["byte_count"]
            assert sha(bundle[offset:offset+size]) == match["sha256"]
            string_records += 1
    videos = []
    for path in sorted(FOLDER.glob("browser-*.mp4")):
        result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                 "stream=width,height,avg_frame_rate,nb_frames", "-show_entries",
                                 "format=duration", "-of", "json", str(path)],
                                capture_output=True, text=True, check=True)
        metadata = json.loads(result.stdout)
        stream = metadata["streams"][0]
        assert (stream["width"], stream["height"]) == (720, 720)
        assert stream["avg_frame_rate"] == "20/1" and stream["nb_frames"] == "200"
        assert float(metadata["format"]["duration"]) == 10
        videos.append({"file": path.name, "ffprobe": metadata})
    assert len(videos) == 4
    records = [{"file": path.name, "bytes": path.stat().st_size, "sha256": sha(path.read_bytes())}
               for path in sorted(FOLDER.iterdir()) if path.is_file() and path.name != "evidence-index.json"]
    index = {"apk_sha256": "8a83b1f128beb43341eefd2b4ad743512d0193ff6dd4e7b56feba138fb4b63c9",
             "bundle_sha256": EXPECTED, "operation": "Static feature tracing and offline extracted-source replay",
             "verification": {"function_records_checked": total_records,
                              "unique_function_ids_checked": len(functions),
                              "raw_string_ranges_checked": string_records,
                              "all_five_feature_entries_present": True,
                              "rendered_demo_video_checks": videos},
             "records": records,
             "supporting_tools": [{"file": str(path.relative_to(ROOT)), "sha256": sha(path.read_bytes())}
                                  for path in [ROOT / "tools/select_android_feature_common.py",
                                               ROOT / "tools/replay_android_renderers.py",
                                               Path(__file__).resolve()]],
             "remaining_unknowns": ["Installed phone version and Android UI/render equivalence",
                                    "Android native capture, FFmpeg and media save execution",
                                    "Native BIN encoder packing and hardware-specific 360 mapping",
                                    "Playback/upload of generated designs on the physical display",
                                    "Actual device file-list notifications and cause of missing tractor entry"]}
    (FOLDER / "evidence-index.json").write_text(json.dumps(index, indent=2) + "\n")
    print(f"Verified {total_records} function records ({len(functions)} unique IDs), "
          f"{string_records} string ranges and four 200-frame, 10-second videos.")


if __name__ == "__main__":
    main()
