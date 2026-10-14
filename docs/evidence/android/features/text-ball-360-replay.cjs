// Controlled offline execution of extracted APK JavaScript fragments.
// DOM/WebGL/timers are stubs; this verifies math and bridge messages, not pixels.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const crypto = require('node:crypto');
const templatePath = path.join(__dirname, 'text-ball-360-sphere-script.template.js');
const template = fs.readFileSync(templatePath, 'utf8');
function assemble(text) {
  // Exactly the unescaped interpolation observed at function 17470 +0x8b..0xa1.
  return template.replace('{{TEXT}}', () => text)
    .replace('{{PLATFORM}}', 'android').replace('{{COLOR}}', '#25fc11');
}
function replay(text, dpr = 1) {
  const script = assemble(text);
  const row = {text, dpr, script_sha256: crypto.createHash('sha256').update(script).digest('hex')};
  try { new vm.Script(script); row.syntax = 'valid'; }
  catch (err) { row.syntax = err.name; row.error = err.message; return row; }
  const chars = [], timeouts = [], intervals = [], messages = [], matrices = [];
  let draws = 0;
  const gl = new Proxy({}, {get: (_, key) => {
    if (key === 'drawElements') return () => {draws++;};
    if (key === 'uniformMatrix4fv') return (_, __, m) => { if (matrices.length < 2) matrices.push(Array.from(m)); };
    if (key === 'getExtension') return () => ({loseContext() {}});
    if (/^[A-Z_]+$/.test(String(key))) return 1;
    return () => ({});
  }});
  const ctx2d = new Proxy({}, {get: () => () => {}});
  const ul = {getElementsByTagName: () => chars, appendChild: x => chars.push(x)};
  const box = {offsetWidth: 576, style: {}};
  const middle = {getElementsByTagName: x => x === 'ul' ? [ul] : [{}, box]};
  const doc = {
    body: {addEventListener() {}},
    getElementById: x => x === 'box' ? box : {},
    getElementsByClassName: () => [middle],
    createElement: x => x === 'li' ? {style: {}} : {
      getContext: x => x === '2d' ? ctx2d : gl,
      toDataURL: () => 'data:image/jpeg;base64,STUB',
    },
  };
  const win = {devicePixelRatio: dpr, ReactNativeWebView: {postMessage: msg => messages.push(JSON.parse(msg))}};
  const sandbox = {document: doc, window: win, console: {log() {}},
    setInterval: (fn, ms) => { intervals.push({fn, ms}); return intervals.length; },
    clearInterval() {}, setTimeout: fn => timeouts.push(fn)};
  vm.runInNewContext(script, sandbox, {timeout: 2000});
  row.characters = chars.length;
  row.first_characters = chars.slice(0, 12).map(x => x.innerHTML).join('');
  row.font_size_css = chars[0].style['font-size'];
  row.sphere_radius = Math.hypot(chars[0].oriX, chars[0].oriY, chars[0].oriZ);
  row.intervals_ms = intervals.map(x => x.ms);
  row.total_steps = win.getTotalSteps();
  row.coordinates_sha256 = crypto.createHash('sha256').update(JSON.stringify(chars.map(x => [x.oriX,x.oriY,x.oriZ,x.circleTheta,x.circlePhi]))).digest('hex');
  win.exportFrames(200);
  while (timeouts.length) timeouts.shift()();
  row.bridge_message_types = messages.map(x => x.t);
  row.batch_sizes = messages.filter(x => x.t === 'b').map(x => x.f.length);
  row.first_frame_index = messages[0].f[0].i;
  row.last_frame_index = messages[messages.length - 2].f.at(-1).i;
  row.completion = messages.at(-1);
  row.draw_calls = draws;
  row.first_matrices = matrices;
  return row;
}
const output = {
  evidence_type: 'controlled offline source execution; APK fragment concatenation reproduced; DOM, WebGL and timers mocked; no raster rendering, Android runtime or device observed',
  template_sha256: crypto.createHash('sha256').update(template).digest('hex'),
  cases: [replay('HELLO'), replay('你好，欢迎使用', 2), replay("O'Reilly"), replay('line one\nline two')],
};
process.stdout.write(JSON.stringify(output, null, 2) + '\n');
