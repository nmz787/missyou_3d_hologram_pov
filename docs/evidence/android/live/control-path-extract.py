"""Retain bounded UI->legacy TCP->native bridge evidence without target execution."""
from pathlib import Path
import re,json,hashlib
ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
source=(ROOT/'analysis/android/bundle.pseudo.js').read_text()
ids=[9090,9105,9347,17190,17192,17197,17198,17199,17204,17271,17264,17269,17273,9112,9120,9141,9305,9306,9309,9310,9282,9283,9288,9294,9271,9275,9274,9366,9424,9439,9456,12317,12320,12323,12324,12325]
seeds={9112:'_fun9112: for(',9120:'_fun9120: for(',9305:'_fun9305: for(',
  9439:'_fun9439: for(',9456:'_fun9456: for(',12317:'Original name: handlePlay,',12320:'Original name: handlePause,',12325:'_fun12325: for('}
def extract_at(position):
 start=source.rfind('function',0,position)
 depth=0;seen=False
 for end in range(start,len(source)):
  if source[end]=='{':depth+=1;seen=True
  elif source[end]=='}':depth-=1
  if seen and depth==0:return source[start:end+1]+'\n'
 raise RuntimeError('unbalanced selected function')
for fid,seed in seeds.items():
 pos=source.index(seed);(OUT/f'control-path-{fid}.pseudo.js').write_text(extract_at(pos))
# The first row onPress inside renderItem #12323 is closure #12324.
pos=source.index('_fun12323: for(')
pos=source.index('function() { // Original name: onPress,',pos)
(OUT/'control-path-12324.pseudo.js').write_text(extract_at(pos+len('function')))
for fid in [9309,9310]:
 (OUT/f'control-path-{fid}.pseudo.js').write_bytes((ROOT/f'docs/evidence/android/comms/legacy-control-{fid}.pseudo.js').read_bytes())
hasm=(ROOT/'analysis/android/bundle.hasm').read_text();bundle=(ROOT/'analysis/android/index.android.bundle').read_bytes()
records=[];parts=[]
for m in re.finditer(r'^=> \[Function #(\d+) .*?(?=^=> \[Function #|\Z)',hasm,re.M|re.S):
 if int(m[1]) not in ids:continue
 text=m[0];h=re.match(r'=> \[Function #(\d+) "(.*?)" of (\d+) bytes\].*?@ offset 0x([0-9a-f]+)',text)
 fid,name,length,offset=h.groups();offset=int(offset,16);length=int(length)
 records.append({'function_id':int(fid),'name':name,'bundle_file_offset':hex(offset),'code_bytes':length,'original_code_sha256':hashlib.sha256(bundle[offset:offset+length]).hexdigest()});parts.append(text)
(OUT/'control-path-bytecode.hasm').write_text(''.join(parts))
native=[]
for p in sorted(OUT.glob('control-path-native-*.json')):
 if not p.stat().st_size:continue
 j=json.loads(p.read_text());native.append({'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'evidence_id':j.get('evidence_id'),'parameters':j.get('parameters')})
(OUT/'control-path-index.json').write_text(json.dumps({'scope':'Static APK/UI/index/send/socket encoding trace with controlled offline recorder replay','apk_sha256':hashlib.sha256((ROOT/'5D-Holo-android.apk').read_bytes()).hexdigest(),'bundle_sha256':hashlib.sha256(bundle).hexdigest(),'functions':records,'native_evidence':native},indent=2)+'\n')
print('Retained',len(records),'functions and',len(native),'native method records')
