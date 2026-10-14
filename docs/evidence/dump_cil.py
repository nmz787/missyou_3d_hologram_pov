"""Reproduce focused static CIL evidence; does not load or execute target code."""
from pathlib import Path
import hashlib
import json
import argparse
import dnfile
from dncil.cil.body.reader import read_method_body_from_bytes

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('target', type=Path, nargs='?', default=Path('analysis/application/5DDisplayer.exe'))
parser.add_argument('--output-dir', type=Path, default=Path(__file__).parent)
args = parser.parse_args()
TARGET = args.target
args.output_dir.mkdir(parents=True, exist_ok=True)
p = dnfile.dnPE(str(TARGET))
owners = {}
for t in p.net.mdtables.TypeDef:
    for x in t.MethodList:
        owners[(6, x.row_index)] = f'{t.TypeNamespace}.{t.TypeName}'
    for x in t.FieldList:
        owners[(4, x.row_index)] = f'{t.TypeNamespace}.{t.TypeName}'
tables = {1: p.net.mdtables.TypeRef, 2: p.net.mdtables.TypeDef,
          4: p.net.mdtables.Field, 6: p.net.mdtables.MethodDef,
          10: p.net.mdtables.MemberRef, 27: p.net.mdtables.TypeSpec,
          43: p.net.mdtables.MethodSpec, 17: p.net.mdtables.StandAloneSig}
def indexed_name(index):
    row = index.row
    if hasattr(row, 'TypeName'):
        return f'{row.TypeNamespace}.{row.TypeName}'
    if hasattr(row, 'Signature') and not hasattr(row, 'Name'):
        return 'signature:' + row.Signature.value.hex()
    return str(getattr(row, 'Name', ''))
def resolve(ins, header):
    value = ins.operand
    kind = ins.opcode.operand_type.name
    if kind in ('InlineBrTarget', 'ShortInlineBrTarget'):
        return f'IL_{value-header:04x}'
    if kind == 'InlineSwitch':
        return ', '.join(f'IL_{v-header:04x}' for v in value)
    if hasattr(value, 'value'):
        token = value.value
        table, rid = token >> 24, token & 0xFFFFFF
        if table == 0x70:
            return f'0x{token:08x} {p.net.user_strings.get(rid).value!r}'
        if table in tables and rid:
            row = tables[table].rows[rid-1]
            name = str(getattr(row, 'Name', getattr(row, 'TypeName', '')))
            owner = owners.get((table, rid), str(getattr(row, 'TypeNamespace', '')))
            if table == 10:
                owner = indexed_name(row.Class)
            if table == 43:
                name = indexed_name(row.Method) + '<instantiation:' + row.Instantiation.value.hex() + '>'
            if table in (17, 27):
                name = 'signature:' + row.Signature.value.hex()
            return f'0x{token:08x} {owner}::{name}'
    return '' if value is None else str(value)

out = [f'Artifact: {TARGET.resolve()}', f'Artifact SHA-256: {hashlib.sha256(TARGET.read_bytes()).hexdigest()}',
       f'Module MVID: {p.net.mdtables.Module.rows[0].Mvid}',
       'Evidence: decoded static CIL, no target execution. IL labels are code-relative (method header excluded).']
for t in p.net.mdtables.TypeDef:
    name = str(t.TypeName)
    selected = {'Bin': None, 'BinTool': None, 'TypeConversion': {'GetBytes'},
                'TransformWindow': {'.ctor', 'Device_SelectionChanged', 'SendWork'},
                'TcpServer': {'SendFile', 'ExportVideo', 'ConvertToFTLVWork'},
                'YTPlayer': {'GetFrames'}, 'VideoStreamDecoder': {'extractAudio'},
                'DrawTool': {'ImageClip'}}
    if name not in selected:
        continue
    for x in t.MethodList:
        m = x.row
        if selected[name] is not None and str(m.Name) not in selected[name]:
            continue
        body = read_method_body_from_bytes(p.get_data(m.Rva))
        raw_il = p.get_data(m.Rva + body.header_size, body.code_size)
        out.extend(['', f'{t.TypeNamespace}.{name}::{m.Name} token 0x{0x06000000+x.row_index:08x}',
                    f'RVA=0x{m.Rva:x} file_offset=0x{p.get_offset_from_rva(m.Rva):x} header_size={body.header_size} IL_size={body.code_size}',
                    f'IL_SHA256={hashlib.sha256(raw_il).hexdigest()} signature_blob={m.Signature.value.hex()}'])
        for ins in body.instructions:
            out.append(f'  IL_{ins.offset-body.header_size:04x}: {ins.opcode.name} {resolve(ins, body.header_size)}'.rstrip())

luts = {}
for init in p.net.mdtables.FieldRva:
    if init.Field.row_index in (0x4b7, 0x4b8):
        name = 'offset_image' if init.Field.row_index == 0x4b7 else 'gamma_tab'
        data = p.get_data(init.Rva, 256)
        luts[name] = list(data)
        out.extend(['', f'{name}: source-field-token=0x{0x04000000+init.Field.row_index:08x} RVA=0x{init.Rva:x} file_offset=0x{p.get_offset_from_rva(init.Rva):x}',
                    f'bytes=256 SHA256={hashlib.sha256(data).hexdigest()}', 'hex='+data.hex()])
(args.output_dir / 'conversion.cil.txt').write_text('\n'.join(out)+'\n')
(args.output_dir / 'luts.json').write_text(json.dumps(luts, indent=2)+'\n')
