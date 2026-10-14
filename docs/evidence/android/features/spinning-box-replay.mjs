// Controlled offline execution of the exact extracted renderer script with synthetic
// DOM/WebGL/Image/timer interfaces. This validates control/math/export messages;
// it neither runs the APK nor renders pixels, loads images, or makes requests.
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import {fileURLToPath} from 'node:url';
const folder=path.dirname(fileURLToPath(import.meta.url));
const template=fs.readFileSync(path.join(folder,'spinning-box-renderer-template.html'),'utf8');
const results=[];
for(const type of [0,1,2]){
  const jobs=[],messages=[],frames=[],glCalls=[];
  const gl=new Proxy({}, {get(_,k){
    if(k==='getShaderParameter')return ()=>true;
    if(k==='getExtension')return ()=>({loseContext(){}});
    if(k==='bufferSubData')return (...a)=>{glCalls.push([...a[2]]);};
    if(k==='createBuffer'||k==='createTexture'||k==='createShader'||k==='createProgram')return ()=>({});
    if(/^[A-Z_0-9]+$/.test(k))return 0;
    return ()=>{};
  }});
  let context;
  function canvas(){return {style:{},getContext(){return gl;},toDataURL(format,quality){frames.push({index:frames.length,angleY:context.angleY,dist:context.dist,width:this.width,height:this.height,format,quality});return 'data:image/jpeg;base64,SYNTHETIC';}};}
  const c=canvas();
  class ImageMock {set src(value){this.value=value;jobs.push(()=>this.onload?.());}}
  const sandbox={console,Float32Array,Uint16Array,Uint8Array,Math,JSON,Image:ImageMock,document:{getElementById(){return c;},createElement(){return canvas();},addEventListener(){}},setInterval(){return 1;},clearInterval(){},setTimeout(fn){jobs.push(fn);}};
  sandbox.window={innerWidth:500,innerHeight:500,devicePixelRatio:1,ReactNativeWebView:{postMessage(s){messages.push(JSON.parse(s));}}};
  context=vm.createContext(sandbox);
  const html=template.replace('__TYPE__',String(type)).replace('__DIST__',type===1?'30':'20').replace('__IMAGE_SRCS__',JSON.stringify(['a','b','c','d','e','f']));
  const script=html.match(/<script>([\s\S]*)<\/script>/)[1];
  vm.runInContext(script,context,{timeout:1000});
  for(let i=0;jobs.length;i++){if(i>1000)throw Error('Queue limit');jobs.shift()();}
  const initial={angleY:context.angleY,dist:context.dist,face0_vertices:glCalls[0]};
  context.window.stepFrame(1);
  const stepped={angleY:context.angleY,dist:context.dist};
  context.window.exportFrames(200);
  for(let i=0;jobs.length;i++){if(i>1000)throw Error('Queue limit');jobs.shift()();}
  if(frames.length!==200||messages.filter(x=>x.t==='b').length!==20||messages.at(-1).n!==200)throw Error('Export mismatch');
  results.push({type,initial,after_stepFrame_1:stepped,getTotalSteps:context.window.getTotalSteps(),first_export_frame:frames[0],last_export_frame:frames.at(-1),min_export_dist:Math.min(...frames.map(f=>f.dist)),max_export_dist:Math.max(...frames.map(f=>f.dist)),message_types:messages.map(m=>m.t),batch_sizes:messages.filter(m=>m.t==='b').map(m=>m.f.length),completion:messages.at(-1)});
}
const result={evidence_type:'controlled extracted-source execution against mocked DOM/WebGL, not Android runtime or rendered pixels',source:'spinning-box-renderer-template.html, exact packaged string bodies with type/dist/image JSON substitutions',limits:['No GL rasterization or image decoding','No native Android capture, FFmpeg, save or device upload','Textures synthetic; dimensions and JPEG options observed as calls'],results};
fs.writeFileSync(path.join(folder,'spinning-box-replay.json'),JSON.stringify(result,null,2)+'\n');
console.log('Three packaged renderer styles replayed: 200 frames and 20 batches each.');
