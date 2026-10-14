"""Offline reconstruction of field writes in old_dev_tcp_upload; no network I/O.

This models observed native assembly. It does not invoke the original native
function, establish device acceptance, or model the ACK helper's timing.
"""

import hashlib
import json
from pathlib import Path
import struct


def main():
    native = Path("analysis/android/libSPCore.so").read_bytes()
    expected = "20d90219ddf46083844ace9bb225f583f44802d78d05e2f409cd189f0654645b"
    if hashlib.sha256(native).hexdigest() != expected:
        raise ValueError("Native constants require the exact APK library member")
    constants = {name: native[offset:offset + size] for name, offset, size in [
        ("file_info_header", 0x272498, 6), ("file_info_tail", 0x27249e, 8),
        ("chunk_header", 0x2724a6, 9), ("chunk_tail", 0x2724af, 11)]}
    samples = []
    for path, name in [(Path("13_tractor.bin"), "13_tractor.bin"), (Path("cd.bin"), "14_cd.bin")]:
        if not path.is_file():
            continue
        payload = path.read_bytes()
        encoded = name.encode("gbk")
        blocks = (len(payload) + 1439) // 1440
        padded = blocks * 1440
        info = (constants["file_info_header"] + b"DF" + bytes([(len(encoded) + 61) & 255]) +
                struct.pack(">I", padded & 0xffffffff) + encoded + constants["file_info_tail"])
        records = []
        for index in sorted({0, blocks - 1}):
            body = payload[index * 1440:(index + 1) * 1440].ljust(1440, b"\0")
            packet = constants["chunk_header"] + body + constants["chunk_tail"]
            records.append({"zero_based_block": index, "packet_bytes": len(packet),
                            "header_hex": packet[:9].hex(), "tail_hex": packet[-11:].hex(),
                            "packet_sha256": hashlib.sha256(packet).hexdigest(),
                            "body_sha256": hashlib.sha256(body).hexdigest()})
        samples.append({"local_source": str(path), "source_sha256": hashlib.sha256(payload).hexdigest(),
                        "filename": name, "filename_gbk_hex": encoded.hex(), "file_bytes": len(payload),
                        "chunk_body_bytes": 1440, "chunk_packet_bytes": 1460, "chunks": blocks,
                        "padded_file_bytes": padded, "padding_bytes": padded - len(payload),
                        "file_info_bytes": len(info), "file_info_hex": info.hex(),
                        "file_info_size_field_hex": info[9:13].hex(),
                        "interval_ack_requests": (blocks + 19) // 20,
                        "file_info_ack_requests": 1,
                        "chunk_samples": records,
                        "completion_ascii": "d31d88DEFa4a8c2e3", "completion_bytes": 17})
    ack_token, ack_tail = b"d30d66", constants["file_info_tail"]
    def acceptance(parts):
        buffer = b""
        results = []
        for part in parts:
            buffer += part[:128 - len(buffer)]
            results.append({"accumulated_bytes": len(buffer),
                            "acceptance": len(buffer) >= 14 and buffer[:6] == ack_token and buffer[-8:] == ack_tail})
        return results
    minimal = ack_token + ack_tail
    ack_examples = [{"scenario": name, "read_parts_hex": [part.hex() for part in parts],
                     "after_each_read": acceptance(parts)} for name, parts in [
                         ("minimal ACK", [minimal]),
                         ("fragmented ACK", [minimal[:5], minimal[5:]]),
                         ("leading unexpected byte", [b"!" + minimal]),
                         ("trailing unexpected byte", [minimal + b"!"]),
                         ("unchecked middle bytes", [ack_token + b"arbitrary" + ack_tail]),
                         ("coalesced duplicate ACKs", [minimal + minimal]),
                         ("buffer filled with wrong prefix", [b"!" * 128, minimal])]]
    output = {"authority": "Analyst reconstruction of observed native field writes and ACK comparisons; not original-method execution",
              "native_member_sha256": expected,
              "native_evidence_id": "ev_e192f9195ec436822d2a54b62d100f0eeeea6b3071541258e89227a881107b4c",
              "constants": {name: {"ascii": value.decode("ascii"), "hex": value.hex()}
                            for name, value in constants.items()}, "samples": samples,
              "ack_evidence_id": "ev_9e44881b9dec968e439e468593da0cb13f23b004b8bfbc37cb0a4e903b6f9461",
              "ack_examples": ack_examples,
              "limitations": ["No network connection, APK execution, or device upload performed.",
                              "This derived model does not establish firmware acceptance or ACK timing."]}
    destination = Path("docs/evidence/android/comms/legacy-upload-layout-replay.json")
    destination.write_text(json.dumps(output, indent=2) + "\n")
    print(destination)


if __name__ == "__main__":
    main()
