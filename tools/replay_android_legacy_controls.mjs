// Capture packet construction from focused Hermes decompiler output offline.
// No sockets, device operations, or Android execution. Async state machines run
// only through their first send; acknowledgment/state changes are not exercised.
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';

const folder = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../docs/evidence/android/comms');
const registers = Array.from({length: 64}, (_, i) => `r${i}`).join(',');
const log = {default: {i() {}}};
const globals = {Object, Date, String, HermesInternal: {
  concat: function(...parts) { return String(this) + parts.join(''); }
}};
const sources = [];
function method(id) {
  const file = `legacy-control-${id}.pseudo.js`;
  const original = fs.readFileSync(path.join(folder, file), 'utf8');
  sources.push({file, sha256: crypto.createHash('sha256').update(original).digest('hex')});
  let code = original.replace(/function\*/g, 'function');
  code = code.replace(/function\([^)]*\)\s*\{/g, match => `${match}\nvar ${registers};`);
  code = code.replace(/StartGenerator\(\);/g, '')
    .replace(/ResumeGenerator\(result_out_reg=(\d+), return_bool_out_reg=(\d+)\);/g,
             (_, value, done) => `r${value}=undefined;r${done}=false;`)
    .replace(/SaveGenerator\(address=\d+\);/g, '');
  return vm.runInNewContext(`(${code})`, {global: globals, _closure1_slot5: log});
}
const methods = new Map([9294,9298,9304,9305,9307,9308,9309,9310,9311,9316,9320,9324,9328]
  .map(id => [id, method(id)]));
const cases = [
  ['heartbeat',9294,[],['c31c38abca4a8c2e3']],
  ['previous',9307,[],['c31c33abca4a8c2e3']],
  ['next',9308,[],['c31c32abca4a8c2e3']],
  ['pause',9309,[],['c31c34abca4a8c2e3']],
  ['resume',9310,[],['c31c35abca4a8c2e3']],
  ['play index 13',9305,[13],['c31c40abe13a4a8c2e3']],
  ['play index 7',9305,[7],['c31c40abe07a4a8c2e3']],
  ['delete index 13',9298,[13],['c31c39abe13a4a8c2e3']],
  ['loop all true',9316,[true],['c31c36abca4a8c2e3']],
  ['loop all false',9316,[false],['c31c37abca4a8c2e3']],
  ['open',9320,[],['c31c45abca4a8c2e3']],
  ['shutdown',9324,[],['c31c89abca4a8c2e3']],
  ['BLE true',9328,[true],['c31c44abca4a8c2e3']],
  ['BLE false',9328,[false],['c31c43abca4a8c2e3']],
  ['format SD',9304,[],['c31c88abca4a8c2e3']],
];
const results = [];
for (const [label, id, args, expected] of cases) {
  const packets = [];
  const client = {isPlaying: true, bytesToHex: methods.get(9311),
    send(value) { packets.push(Buffer.from(value)); return true; },
    playPlay: methods.get(9310)};
  methods.get(id).apply(client, args);
  assert.deepEqual(packets.map(b => b.toString('ascii')), expected);
  results.push({label, function_id: id, arguments: args,
    packets: packets.map(b => ({ascii: b.toString('ascii'), hex: b.toString('hex'), bytes: b.length}))});
}
const result = {evidence_type: 'controlled replay of extracted decompiler state machines with a local send recorder',
  source_sha256: sources, transformations: ['Registers declared per function frame',
    'Generator bodies treated as plain functions through first send only',
    'Start/SaveGenerator removed; ResumeGenerator initialized undefined/false'],
  limits: ['Not Hermes bytecode or Android execution', 'No network requests or device commands sent',
    'No queue, native socket, response acknowledgment, or firmware behavior exercised'], results};
fs.writeFileSync(path.join(folder, 'legacy-control-replay.json'), JSON.stringify(result,null,2)+'\n');
console.log(`Captured and checked ${results.length} command-construction cases without network access.`);
