// Replay focused hermes-dec state machines from the supplied APK using synthetic data.
// This is a decompiler-output replay, not execution of the Android APK or firmware.
// No network operations or SD-card writes are performed.
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';

const directory = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../docs/evidence/android');
const logs = [];
const registers = Array.from({length: 64}, (_, i) => `r${i}`).join(',');
const globals = {Object, Date, parseInt, isNaN,
  HermesInternal: {concat: function (...parts) { return String(this) + parts.join(''); }}};
function loadDependency(id) {
  if (id === 10) return {Buffer};
  if (id === 9) return {default: {decode: (data, encoding) => new TextDecoder(encoding).decode(data)}};
  if (id === 5) return {default: {i: (...args) => logs.push(args)}};
  throw new Error(`Unexpected dependency ${id}`);
}
function method(id) {
  const original = fs.readFileSync(path.join(directory, `function-${id}.pseudo.js`), 'utf8');
  // Declare registers in every function's own frame; otherwise nested maps would share them.
  let code = original.replace(/function\([^)]*\)\s*\{/g, match => `${match}\nvar ${registers};`);
  // hermes-dec's variadic Call rendering is invalid for this logging branch.
  // Raw #9292 instruction 0x17a calls function register r20, with r28 as this.
  // Repair only that call target; the diagnostic string has no effect on returned files.
  code = code.replace('r28[r20](', 'r20.bind(r28)(');
  return vm.runInNewContext(`(${code})`, {global: globals,
    _closure1_slot0: loadDependency, _closure1_slot1: Array.from({length: 11}, (_, i) => i),
    _closure1_slot5: loadDependency(5), _closure1_slot9: loadDependency(9)});
}
const parser = method(9292);
const notify = method(9293);
const formatter = method(9132);
function client() {
  return {fileList: [], events: [], model: '', usedIdentifierSet: new Set(),
    _parseModel: flag => flag === '7' ? 'F-MINI11' : 'F1',
    _parseFileList: parser, _parseNotify: notify,
    onUpdateFileListBlock(value) { this.events.push(value); }};
}
function format(names) {
  const state = {usedIdentifierSet: new Set(), onFileListChangedBlock(value) { this.result = value; }};
  formatter.call(state, names.map((name, index) => ({name, index})));
  return Array.from(state.result, x => ({index: x.index, name: x.name, displayName: x.displayName}));
}
function packet(names) {
  // A synthetic packet satisfying this decoder's offsets; NOT a captured firmware response.
  // Each record has decimal length/index and a three-byte placeholder before the name.
  const records = names.map((name, index) => {
    const bytes = Buffer.from(name, 'ascii');
    const length = String(bytes.length + 5).padStart(2, '0');
    return Buffer.concat([Buffer.from(length + String(index).padStart(2, '0') + '---'), bytes]);
  });
  return Buffer.concat([Buffer.from('c30c38abc'), ...records, Buffer.from('00711a4a8c2e3')]);
}
const names = ['00_B.bin', '13_TRA~1.bin', '14_CD.bin'];
const complete = packet(names);
const state = client();
notify.call(state, complete);
assert.deepEqual(Array.from(state.fileList, x => x.name), names);
const formatted = format(['00_B.bin', '01_LC.bin', '13_tractor.bin', '13_TRA~1.bin', '13_TRA~1.BIN', '14_CD.bin']);
assert.equal(formatted[0].displayName, '00.B');
assert.equal(formatted[1].displayName, '01.LC');
assert.equal(formatted[2].displayName, '13.tractor');
assert.equal(formatted[3].displayName, '13.TRA~1');
assert.equal(formatted[4].displayName, '13_TRA~1.BIN');
// A chunk boundary anywhere inside a valid response leaves neither chunk with both markers.
const split = client();
const middle = Math.floor(complete.length / 2);
notify.call(split, complete.subarray(0, middle));
notify.call(split, complete.subarray(middle));
assert.equal(split.events.length, 0);
// Malformed record length aborts the parser, preserving only the earlier parsed prefix.
const malformed = Buffer.from(complete);
const secondOffset = 9 + 7 + names[0].length;
malformed.write('XX', secondOffset, 'ascii');
const partial = client();
notify.call(partial, malformed);
assert.equal(partial.fileList.length, 1);
const coalesced = client();
notify.call(coalesced, Buffer.concat([complete, complete]));
// A valid list with an unrecognized status/model tail resets its model to F1.
const malformedTail = Buffer.from(complete);
malformedTail.write('xxxxx', malformedTail.length - 13, 'ascii');
const fallback = client();
notify.call(fallback, malformedTail);
assert.equal(fallback.fileList.length, 3);
assert.equal(fallback.model, 'F1');
console.log(JSON.stringify({
  authority: 'controlled replay of extracted decompiler state machines using synthetic packets',
  limitations: ['No actual device response captured', 'No original APK bytecode executed',
    'Three-byte record prefix is a placeholder satisfying observed parser offsets',
    'Buffer/GBK/log dependencies and model decoding are local harness substitutes',
    'Invalid hermes-dec variadic logging call was repaired using raw instruction 0x17a'],
  function_ids: [9132, 9133, 9292, 9293],
  formatted_names: formatted,
  complete_response: {hex: complete.toString('hex'), events: state.events.length, files: state.fileList, model: state.model},
  split_response: {chunk_bytes: [middle, complete.length - middle], events: split.events.length, files: split.fileList},
  invalid_length_response: {hex: malformed.toString('hex'), events: partial.events.length, files: partial.fileList},
  coalesced_responses: {bytes: complete.length * 2, events: coalesced.events.length, files: coalesced.fileList},
  invalid_model_tail: {hex: malformedTail.toString('hex'), events: fallback.events.length,
                       files: fallback.fileList, model: fallback.model},
  logs, assertions: 'passed',
}, null, 2));
