// Controlled offline relay of focused APK decompiler methods. No sockets or Android.
import fs from 'node:fs';
import vm from 'node:vm';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
const out=path.dirname(fileURLToPath(import.meta.url));
const registers=Array.from({length:64},(_,i)=>`r${i}`).join(',');
const digest=b=>crypto.createHash('sha256').update(b).digest('hex');
const ids=[9112,9120,9305,9309,9310,9439,9456,12317,12320,12324,12325];
const sources=Object.fromEntries(ids.map(id=>[id,fs.readFileSync(path.join(out,`control-path-${id}.pseudo.js`),'utf8')]));
const cases=[];
const globals={Object,Date,String,Number,Array,Uint8Array,JSON,Promise,
 HermesInternal:{concat:function(...parts){return String(this)+parts.join('');}}};
function method(id,context){
 const code=sources[id].replace(/function\([^)]*\)\s*\{/g,match=>`${match}\nvar ${registers};`);
 return vm.runInNewContext(`(${code})`,{global:globals,...context});
}
async function run(label,index,isPlaying,entry,current,state){
 const calls=[],packets=[],delays=[];
 const native={write(id,base64,msgId){const decoded=Buffer.from(base64,'base64');packets.push({socket_id:id,msg_id:msgId,bridge_base64:base64,ascii:decoded.toString('ascii'),hex:decoded.toString('hex'),bytes:decoded.length});}};
 const socketCtx={_closure1_slot8:{NativeModules:{TcpSockets:native}},
  _closure1_slot0:id=>{assert.equal(id,9);return{Buffer};},_closure1_slot1:Array.from({length:16},(_,i)=>i)};
 const socket={_pending:false,_destroyed:false,_writeBufferSize:0,_msgId:0,_id:4,
  _bytesWritten:0,writableHighWaterMark:16384,_msgEvtEmitter:{on(){}},
  _generateSendBuffer:method(9456,socketCtx),write:method(9439,socketCtx)};
 const legacy={isPlaying,
  send(value){const buffer=Buffer.from(value);calls.push({method:'TCPClient.send recorder',buffer_hex:buffer.toString('hex')});socket.write(buffer);return Promise.resolve('OK');},
  playFile:method(9305,{}),playPause:method(9309,{}),playPlay:method(9310,{})};
 const managerCtx={_closure1_slot9:{default:legacy}};
 const manager={getIsOldDevice(){calls.push({method:'getIsOldDevice',value:true});return true;},
  playFile:method(9112,managerCtx),playPause:method(9120,managerCtx)};
 const central={Log:{i(){}},EasyLoading:{show(){},dismis(){}},CONN:manager};
 const uiCtx={_closure1_slot0:id=>id===9?{strings:()=>''}:central,
  _closure1_slot1:Array.from({length:20},(_,i)=>i),_closure1_slot9:'DevicePage'};
 const oldSetTimeout=globals.setTimeout;
 globals.setTimeout=(fn,delay)=>{delays.push(delay);return 1;};
 const item={index,name:index===15?'13_TRA~1.bin':'01_LC.bin'};
 const play=method(12317,uiCtx),pause=method(12320,uiCtx);
 const pressCtx={_closure2_slot26:play,_closure2_slot27:pause,_closure3_slot0:item,
  _closure2_slot4:{current:current?item.name:'different.bin',state}};
 if(entry==='row')method(12324,pressCtx)();
 else if(entry==='icon')method(12325,pressCtx)();
 else if(entry==='pause')pause(item);
 else throw new Error('Unknown entry');
 await Promise.resolve();await Promise.resolve();
 globals.setTimeout=oldSetTimeout;
 const result={label,item,index,is_playing_before:isPlaying,entry,current,state,
  native_bridge_packets:packets,calls,ui_callback_delays_ms:delays};cases.push(result);
 return packets.map(p=>p.ascii);
}
assert.deepEqual(await run('row index3 while playing',3,true,'row',false,'ing'),['c31c40abe03a4a8c2e3']);
assert.deepEqual(await run('row index15 while playing',15,true,'row',false,'ing'),['c31c40abe15a4a8c2e3']);
assert.deepEqual(await run('row index3 while paused',3,false,'row',false,'idle'),['c31c35abca4a8c2e3','c31c40abe03a4a8c2e3']);
assert.deepEqual(await run('current row icon while playing',3,true,'icon',true,'ing'),['c31c34abca4a8c2e3']);
assert.deepEqual(await run('noncurrent row icon while playing',3,true,'icon',false,'ing'),['c31c40abe03a4a8c2e3']);
assert.deepEqual(await run('current row icon while idle',3,false,'icon',true,'idle'),['c31c35abca4a8c2e3','c31c40abe03a4a8c2e3']);
fs.writeFileSync(path.join(out,'control-path-replay.json'),JSON.stringify({
 authority:'Controlled replay of extracted UI, ConnectionManager, packet builders and Socket encoding methods with local native-write recorder',
 sources_sha256:Object.fromEntries(Object.entries(sources).map(([id,s])=>[id,digest(s)])),
 substitutions:['Function-local register declarations','UI module/translation/loading stubs',
  'Legacy getIsOldDevice fixed true','TCPClient.send replaced by Buffer.from+immediate Socket.write recorder; queue is established statically, not replayed',
  'NativeModules.TcpSockets.write replaced by local Base64 decoder/byte recorder','UI setTimeout collects delays without running timer callbacks'],
 cases,assertions:'passed',limitations:['No actual APK bytecode, native Android code, network or device execution',
  'Recorded Base64 decode matches inspected Java write method; Java method is not executed',
  'Promise queue lifecycle, platform scheduling and firmware admission are not reproduced']},null,2)+'\n');
console.log(`Verified ${cases.length} UI-to-native-recorder cases without device access.`);
