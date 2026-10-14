// Offline replay of focused APK decompiler state machines on a captured response.
// This does not execute Android/firmware, contact a device, or use ADB.
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
const out = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(out, '../../../..');
const evidence = path.join(root, 'docs/evidence/android');
const packetPath = path.join(root, 'analysis/device-live/legacy-notification.bin');
const packet = fs.readFileSync(packetPath);
const digest = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const logs = [];
const registers = Array.from({length:64}, (_,i) => `r${i}`).join(',');
const globals = {Object, Date, parseInt, isNaN,
  HermesInternal:{concat:function(...parts){return String(this)+parts.join('');}}};
function dependency(id) {
  if(id===10) return {Buffer};
  if(id===9) return {default:{decode:(data,encoding)=>new TextDecoder(encoding).decode(data)}};
  if(id===5) return {default:{i:(...args)=>logs.push(args)}};
  throw new Error(`Unexpected dependency ${id}`);
}
function modelSource() {
  const bundleSource=fs.readFileSync(path.join(root,'analysis/android/bundle.pseudo.js'),'utf8');
  const seed='function(a0) { // Original name: _parseModel, environment: r5';
  const start=bundleSource.indexOf(seed);
  assert.ok(start>=0);
  const end=bundleSource.indexOf("            r4['value'] = r6;",start);
  assert.ok(end>start);
  return bundleSource.slice(start,end).trim().replace(/;$/,'');
}
const sources={9291:modelSource(),9292:fs.readFileSync(path.join(evidence,'function-9292.pseudo.js'),'utf8'),
  9293:fs.readFileSync(path.join(evidence,'function-9293.pseudo.js'),'utf8'),
  9132:fs.readFileSync(path.join(evidence,'function-9132.pseudo.js'),'utf8')};
fs.writeFileSync(path.join(out,'packet-function-9291.pseudo.js'),sources[9291]);
function method(id) {
  let code=sources[id].replace(/function\([^)]*\)\s*\{/g,match=>`${match}\nvar ${registers};`);
  // Same narrowly documented decompiler Call repair as the existing synthetic replay.
  // Raw #9292 +0x17a uses r20 as function and r28 as this for logging only.
  code=code.replace('r28[r20](','r20.bind(r28)(');
  return vm.runInNewContext(`(${code})`,{global:globals,
    _closure1_slot0:dependency,_closure1_slot1:Array.from({length:11},(_,i)=>i),
    _closure1_slot5:dependency(5),_closure1_slot9:dependency(9)});
}
const state={fileList:[],events:[],model:'',usedIdentifierSet:new Set(),
  _parseModel:method(9291),_parseFileList:method(9292),_parseNotify:method(9293),
  onUpdateFileListBlock(value){this.events.push(value);}};
state._parseNotify(packet);
const ui={usedIdentifierSet:new Set(),onFileListChangedBlock(value){this.result=value;}};
method(9132).call(ui,state.fileList);
const originalFiles=Array.from(state.fileList,record=>({index:record.index,name:record.name}));
assert.equal(originalFiles.length,6);
assert.equal(originalFiles[5].name,'04in131212.');
assert.equal(state.playingFileIndex,31);
assert.equal(state.isPlaying,true);
assert.equal(state.model,'F1');
assert.equal(state.events.length,1);
assert.equal(originalFiles.some(record=>record.name==='13_TRA~1.bin'),false);
const tailStart=packet.length-8-6;
assert.equal(packet.subarray(tailStart,packet.length-8).toString(),'15H711');
const originalTail=packet.subarray(115,packet.length-6).toString('utf8').trim();
const falseTailMatch=originalTail.match(/(\d{2})(.{1,2})(1[01])/);
assert.deepEqual(falseTailMatch.slice(1),['31','3.','11']);
const sourceHashes=Object.fromEntries(Object.entries(sources).map(([id,source])=>[id,digest(source)]));
const sequentialRecords=[];
let offset=9;
while(offset+4<packet.length-12) {
  const declaredLength=parseInt(packet.subarray(offset,offset+2).toString(),10);
  const indexText=packet.subarray(offset+2,offset+4).toString();
  const index=parseInt(indexText,10);
  if(Number.isNaN(declaredLength)||Number.isNaN(index))break;
  const end=offset+declaredLength+2;
  sequentialRecords.push({offset,declared_length:declaredLength,index,
    skipped_prefix:packet.subarray(offset+4,offset+7).toString(),
    name:packet.subarray(offset+7,end).toString(),end});
  offset=end;
}
assert.equal(offset,115);
// Independent bounded recovery oracle: locate embedded length/index/index. prefixes,
// require duplicate two-digit index plus exact .bin filename boundary.
// This is an analyst strategy, not recovered APK behavior or the project's final parser.
const candidates=[];
for(let start=9;start+7<=tailStart;start++) {
  const prefix=packet.subarray(start,start+7).toString('ascii');
  const match=prefix.match(/^(\d{2})(\d{2})(\d{2})\.$/);
  if(!match||match[2]!==match[3])continue;
  const length=Number(match[1]),end=start+length+2;
  if(end>tailStart||length<6)continue;
  const name=packet.subarray(start+7,end).toString('utf8');
  if(!/^[\x20-\x7e]+\.bin$/.test(name))continue;
  candidates.push({offset:start,declared_length:length,index:Number(match[2]),name,end});
}
assert.equal(candidates.length,9);
assert.equal(candidates.at(-1).name,'13_TRA~1.bin');
assert.deepEqual(candidates.slice(5).map(record=>record.index),[12,13,14,15]);
const correctedTailMatch=packet.subarray(tailStart,packet.length-8).toString().match(/^(\d{2})(.{1,2})(1[01])$/);
const recoveryState={current_file_index:Number(correctedTailMatch[1]),
  model:state._parseModel(correctedTailMatch[2]),is_playing:correctedTailMatch[3]==='11'};
assert.deepEqual(recoveryState,{current_file_index:15,model:'F-MINI11',is_playing:true});
const report={
  authority:'Controlled replay of extracted APK decompiler state machines on a separately captured device response',
  apk_sha256:digest(fs.readFileSync(path.join(root,'5D-Holo-android.apk'))),
  packet:{path:packetPath,bytes:packet.length,sha256:digest(packet),ascii:packet.toString('utf8'),contains_nul:packet.includes(0)},
  function_ids:[9291,9292,9293,9132,9133],decompiled_source_sha256:sourceHashes,
  replay_substitutions:['Node Buffer and TextDecoder(GBK) dependencies','No-op captured logging and host Date',
    'Function-local register declarations injected',
    'Decompiler variadic logging call repaired from r28[r20](...) to r20.bind(r28)(...) using raw #9292 +0x17a'],
  original_parser:{events:state.events.length,files:originalFiles,playing_file_index:state.playingFileIndex,
    is_playing:state.isPlaying,model:state.model,sequential_records:sequentialRecords,
    stop_offset:offset,failed_length_text:packet.subarray(offset,offset+2).toString(),
    failed_index_text:packet.subarray(offset+2,offset+4).toString(),
    tail_regex_input_offset:offset,tail_regex_first_match:{packet_offset:offset+falseTailMatch.index,
      matched:falseTailMatch[0],groups:Array.from(falseTailMatch.slice(1))},
    formatted_ui_files:Array.from(ui.result,x=>({index:x.index,name:x.name,displayName:x.displayName}))},
  independent_recovery:{strategy:'Scan duplicate index prefixes and require exact bounded .bin names; anchor status to final six bytes before known eight-byte footer',
    files:candidates,additional_later_records:candidates.slice(5),valid_tail:{packet_offset:tailStart,ascii:'15H711',...recoveryState},
    malformed_entry:{offset:97,declared_length:16,claimed_end:115,next_valid_record_offset:108,unrecovered_name_fragment:'04in'}},
  logs,assertions:'passed',
  limitations:['This replay does not execute the original APK bytecode or Android UI',
    'The capture proves device response bytes, not the phone app actual in-memory parsing state',
    'Independent recovery is an analyst strategy; inspect the project parser separately',
    'The malformed wire segment does not reveal the omitted original filename or why firmware emitted it'],
};
fs.writeFileSync(path.join(out,'packet-original-replay.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({packet_sha256:report.packet.sha256,original_files:originalFiles.length,
 original_model:state.model,original_current_index:state.playingFileIndex,recovered_files:candidates.length,
 recovered_model:recoveryState.model,assertions:'passed'}));
