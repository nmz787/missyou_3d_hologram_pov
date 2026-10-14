"""Extract exact artifact-specific 3D Box functions/strings; never executes APK/JS."""
import base64, hashlib, json, re
from pathlib import Path
from hermes_dec.parsers.hbc_file_parser import HBCReader
ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
BUNDLE = ROOT / 'analysis/android/index.android.bundle'
bundle = BUNDLE.read_bytes()
digest = hashlib.sha256(bundle).hexdigest()
assert digest == '8389750af87d60e75bbd7d93ba57d1bd239008812c8c5ef7ecc84cf2a46777e2'
assembly = (ROOT / 'analysis/android/bundle.hasm').read_text()
pattern = re.compile(r'^=> \[Function #(\d+) "([^"\n]*)" of (\d+) bytes\].*?@ offset 0x([0-9a-fA-F]+)$', re.M)
matches = list(pattern.finditer(assembly))
selected = set(range(17444,17467)) | set(range(17641,17691))
manifest, sections = [], []
for i, match in enumerate(matches):
    fid = int(match[1])
    if fid not in selected: continue
    offset,size = int(match[4],16),int(match[3])
    manifest.append(dict(function_id=fid,name=match[2],bytecode_file_offset=offset,bytecode_bytes=size,raw_bytecode_sha256=hashlib.sha256(bundle[offset:offset+size]).hexdigest()))
    sections.append(assembly[match.start():matches[i+1].start() if i+1<len(matches) else len(assembly)])
assert len(manifest)==len(selected)
(OUT/'spinning-box-bytecode.hasm').write_text('Static Hermes96 disassembly; hermes-dec0.1.6; no APK execution.\nBundle SHA256: '+digest+'\n\n'+''.join(sections))
class Reader(HBCReader):
    def read_string_storage(self):
        self.align_over_padding()
        self.string_storage_file_offset = self.file_buffer.tell()
        super().read_string_storage()
reader=Reader()
with BUNDLE.open('rb') as f: reader.read_whole_file(f)
strings=[]
for sid in [3419,2491,2499,9490,576]:
    info=reader.small_string_table[sid]
    utf16=bool(info.isUTF16)
    if info.length==255: info=reader.overflow_string_table[info.offset]
    offset=reader.string_storage_file_offset+info.offset
    size=info.length*(2 if utf16 else 1)
    raw=bundle[offset:offset+size]
    value=reader.strings[sid]
    assert value == (raw.decode('utf-16-le',errors='surrogatepass') if utf16 else raw.decode('latin1'))
    strings.append(dict(string_id=sid,raw_file_offset=offset,raw_bytes=size,is_utf16=utf16,raw_sha256=hashlib.sha256(raw).hexdigest(),value=value))
(OUT/'spinning-box-strings.json').write_text(json.dumps(dict(bundle_sha256=digest,strings=strings),indent=2,ensure_ascii=False)+'\n')
html=reader.strings[3419]+'__TYPE__'+reader.strings[2491]+'__DIST__'+reader.strings[2499]+'__IMAGE_SRCS__'+reader.strings[9490]
(OUT/'spinning-box-renderer-template.html').write_text(html)
(OUT/'spinning-box-default.jpg').write_bytes(base64.b64decode(reader.strings[576].split(',',1)[1]))
(OUT/'spinning-box-functions.json').write_text(json.dumps(dict(bundle_sha256=digest,functions=manifest,renderer_assembly='fn17447 +0x200, +0x204, +0x208, +0x20c loads string3419,2491,2499,9490; +0x216 variadic concat(type,dist,JSON images)',strings=[{k:v for k,v in s.items() if k!='value'} for s in strings],extracted_artifacts={name:hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in ['spinning-box-renderer-template.html','spinning-box-default.jpg','spinning-box-bytecode.hasm']}),indent=2)+'\n')
print(f'Extracted {len(manifest)} functions and {len(strings)} strings')
