"""Verify retained live observations and original-native packet comparison."""
import hashlib
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT / 'docs/evidence/android/live'


def main():
    index = json.loads((LIVE / 'device-index.json').read_text())
    for row in index['files']:
        data = (ROOT / row['path']).read_bytes()
        assert len(data) == row['bytes']
        assert hashlib.sha256(data).hexdigest() == row['sha256'], row['path']
    source = (ROOT / 'cd.bin').read_bytes()
    assert hashlib.sha256(source).hexdigest() == index['upload_source']['sha256']
    raw = (LIVE / 'native-upload-capture.dat').read_bytes()
    offset, chunks, info, complete = 0, [], [], []
    while offset < len(raw):
        assert offset + 5 <= len(raw)
        direction, length = chr(raw[offset]), struct.unpack_from('<I', raw, offset + 1)[0]
        data = raw[offset + 5:offset + 5 + length]
        assert len(data) == length
        offset += 5 + length
        if direction == 'S' and length == 1460:
            chunks.append(data)
        elif direction == 'S' and data.startswith(b'd31d66'):
            info.append(data)
        elif direction == 'S' and data.startswith(b'd31d88DEF'):
            complete.append(data)
    assert len(chunks) == (len(source) + 1439) // 1440 == 249
    for number, data in enumerate(chunks):
        payload = source[number * 1440:(number + 1) * 1440].ljust(1440, b'\0')
        assert data == b'd31d88JMP' + payload + b'000a4a8c2e3'
    name = b'90USB.bin'
    assert info == [b'd31d66DF' + bytes([len(name) + 61]) + struct.pack('>I', 249 * 1440) + name + b'a4a8c2e3']
    assert complete == [b'd31d88DEFa4a8c2e3']
    formatted = json.loads((LIVE / 'cli-format-card-final.json').read_text())
    assert formatted['directory_empty_observed'] and not formatted['status']['files']
    uploaded = json.loads((LIVE / 'cli-upload-final.json').read_text())
    assert uploaded['transferred'] and uploaded['acknowledgments']['data_statuses'] == {'ffff': 13}
    checks = json.loads((LIVE / 'cli-final-persistence.json').read_text())
    assert checks[-1]['seconds'] >= 21
    for row in checks:
        assert row['status']['complete'] and row['status']['current'] == '90USB.bin'
        assert row['status']['is_playing']
    print(f"Verified {len(index['files'])} retained files, 249 original-native packets, format/upload and 21-second listing checks.")


if __name__ == '__main__':
    main()
