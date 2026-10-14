"""Retain focused discovery/connection bytecode with original byte hashes. No app execution."""
from pathlib import Path
import hashlib
import json
import re

root = Path(__file__).resolve().parents[4]
out = Path(__file__).resolve().parent
hasm = root / 'analysis/android/bundle.hasm'
bundle_path = root / 'analysis/android/index.android.bundle'
apk_path = root / '5D-Holo-android.apk'
source = hasm.read_text()
bundle = bundle_path.read_bytes()
functions = {
    int(m.group(1)): m.group(0)
    for m in re.finditer(r'^=> \[Function #(\d+) .*?(?=^=> \[Function #|\Z)', source, re.M | re.S)
}
selected = [
    5334, 7516, 7517, 7530, 7531, 7532, 7534,
    9050, 9051, 9052, 9054, 9063, 9064, 9065, 9066, 9067, 9072, 9079, 9081, 9082, 9087, 9088, 9141, 9142,
    9264, 9266, 9267, 9274,
    12253, 12261, 12262, 12264, 12328, 12329, 12353, 12354,
    12407, 12408, 12412, 12416, 12420, 12427, 12428,
    12433, 12434, 12435, 12436, 12437, 12444, 12447, 12448, 12468,
]
records = []
retained = []
for function_id in selected:
    disassembly = functions[function_id]
    header = re.match(r'=> \[Function #\d+ "(.*?)" of (\d+) bytes\].*?@ offset 0x([0-9a-f]+)', disassembly)
    name, length, offset = header.groups()
    length, offset = int(length), int(offset, 16)
    original = bundle[offset:offset + length]
    assert len(original) == length
    records.append({
        'function_id': function_id,
        'name': name,
        'bundle_file_offset': hex(offset),
        'code_length': length,
        'original_code_sha256': hashlib.sha256(original).hexdigest(),
        'disassembly_sha256': hashlib.sha256(disassembly.encode()).hexdigest(),
    })
    retained.append(disassembly)
(out / 'discovery-bytecode.hasm').write_text(''.join(retained))
native = []
for path in sorted(out.glob('discovery-native-*.json')):
    record = json.loads(path.read_text())
    native.append({
        'file': path.name,
        'file_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'evidence_id': record.get('evidence_id'),
        'parameters': record.get('parameters'),
        'source_sha256': hashlib.sha256(record.get('normalized_result', {}).get('source', {}).get('text', '').encode()).hexdigest(),
        'limitations': record.get('limitations'),
    })
(out / 'discovery-index.json').write_text(json.dumps({
    'scope': 'Static Android/Hermes discovery and initial connection; no app or network execution',
    'apk': {'path': str(apk_path), 'sha256': hashlib.sha256(apk_path.read_bytes()).hexdigest()},
    'bundle': {'path': str(bundle_path), 'sha256': hashlib.sha256(bundle).hexdigest()},
    'full_disassembly': {'path': str(hasm), 'sha256': hashlib.sha256(hasm.read_bytes()).hexdigest()},
    'retained_disassembly': {'file': 'discovery-bytecode.hasm', 'sha256': hashlib.sha256((out / 'discovery-bytecode.hasm').read_bytes()).hexdigest()},
    'hermes_functions': records,
    'native_evidence': native,
}, indent=2) + '\n')
print(f'Retained {len(records)} Hermes functions and {len(native)} native evidence records')
