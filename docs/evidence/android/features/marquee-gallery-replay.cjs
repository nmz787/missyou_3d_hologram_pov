// Offline probe of the exact shipped renderer string. Canvas metrics/drawing/JPEG,
// WebView messaging, and timers are mocked; this does not execute Android or a GPU.
const fs = require('fs');
const vm = require('vm');
const path = require('path');
const crypto = require('crypto');
const dir = __dirname;
const strings = JSON.parse(fs.readFileSync(path.join(dir,'marquee-gallery-strings.json')));
const source = strings.find(s=>s.string_id===9488).text;
function run(S, measuredTextWidth) {
  const messages = [], exported = [], queue = [];
  let pendingDraw = [];
  const ctx = isExport=>({save(){},restore(){},scale(){},setTransform(){},
    font:'',fillRect(){if(isExport)pendingDraw=[];},
    measureText(){return {width:measuredTextWidth*(isExport?720/S:1)};},
    fillText(t,x,y){if(isExport) pendingDraw.push({text:t,x,y});}});
  const preview={style:{},getContext(){return ctx(false);}};
  const scope={TEXT:'Hello',COLOR:'#25fc11',FONTSIZE:42,Math,JSON,
    window:{innerWidth:S,innerHeight:S,devicePixelRatio:1,
      ReactNativeWebView:{postMessage(s){messages.push(JSON.parse(s));}}},
    document:{body:{style:{}},getElementById(){return preview;},createElement(){return{
      getContext(){return ctx(true);},toDataURL(format,quality){exported.push({format,quality,draw:pendingDraw});return 'data:image/jpeg;base64,MOCK';}};}},
    requestAnimationFrame(){return 1;},cancelAnimationFrame(){},setTimeout(f){queue.push(f);}};
  vm.createContext(scope);
  // String starts with ';' after FONTSIZE and ends with try/catch + HTML tags.
  vm.runInContext('try{'+source.slice(0,source.indexOf('</script>')),scope);
  scope.window.exportFrames(200);
  while(queue.length) queue.shift()();
  return {S,measuredTextWidth,preview_segmentWidth:scope.segmentWidth,preview_stepSize:scope.stepSize,
    preview_pixels_per_ms:scope.speed,export_frames:exported.length,batch_lengths:messages.filter(m=>m.t==='b').map(m=>m.f.length),
    final_message:messages.at(-1),first_frame:exported[0],last_frame:exported.at(-1)};
}
const galleryMath=Array.from({length:6},(_,i)=>{
  const n=i+1, seg=10/n+0.5*(n-1)/n;
  return {picked_images:n,segment_seconds:seg,transition_seconds:0.5,
    ideal_final_duration:n*seg-(n-1)*0.5,
    transition_offsets:Array.from({length:n-1},(_,j)=>((j+1)*(seg-0.5)).toFixed(2))};
});
const output={evidence_kind:'offline replay with mocked Canvas/JPEG/WebView; Gallery duration algebra evaluated separately',
  source_string_id:9488,source_sha256:utf8hash(source),renderer_probes:[run(360,120),run(400,137)],gallery_duration_math:galleryMath,
  limitations:['No browser font rasterization or JPEG encoding occurs.','Text widths and viewport sizes are explicit probe inputs, not phone measurements.','Gallery results verify duration algebra, not FFmpeg execution or final frame counts.']};
function utf8hash(s){return crypto.createHash('sha256').update(s).digest('hex');}
fs.writeFileSync(path.join(dir,'marquee-gallery-replay.json'),JSON.stringify(output,null,2)+'\n');
console.log(JSON.stringify({probes:output.renderer_probes.map(p=>({S:p.S,frames:p.export_frames,done:p.final_message})),gallery_cases:galleryMath.length}));
