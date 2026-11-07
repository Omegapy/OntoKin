#!/usr/bin/env node
// A bounded JSON-lines bridge to actual pinned GLTFLoader + controlled .22 CPU playback.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {createRequire} from 'node:module';
import {createInterface} from 'node:readline';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const args=Object.fromEntries(process.argv.slice(2).reduce((all,v,i,values)=>i%2?all:[...all,[v,values[i+1]]],[]));
const root=path.resolve(args['--checkout']??path.join(path.dirname(fileURLToPath(import.meta.url)),'..'));
const modules=path.resolve(args['--node-modules']??'/tmp/c088-verification-deps/tools/node_modules');
process.env.PLAYWRIGHT_BROWSERS_PATH=path.resolve(args['--browser-cache']??'/tmp/c088-verification-deps/browsers');
const require=createRequire(path.join(path.dirname(modules),'package.json'));
const {build}=require('esbuild'),{chromium}=require('playwright'),validator=require('gltf-validator');
const sha=data=>createHash('sha256').update(data).digest('hex');
const save=(file,value)=>writeFile(file,JSON.stringify(value,null,2)+'\n');
const dependencies={};
for(const[name,version]of Object.entries({three:'0.180.0',playwright:'1.56.1',esbuild:'0.25.10','gltf-validator':'2.0.0-dev.3.10'})){
 const raw=await readFile(path.join(modules,name,'package.json'));assert.equal(JSON.parse(raw).version,version);
 dependencies[name]={version,package_json_sha256:sha(raw)};
}
const code=String.raw`
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {attachTorquePlayback} from ${JSON.stringify(path.join(root,'tools/torque_destination.mjs'))};
const check=(v,m)=>{if(!v)throw new Error(m);};
const raw=Uint8Array.from(atob(globalThis.GLB),c=>c.charCodeAt(0));
const gltf=await new GLTFLoader().parseAsync(raw.buffer,'');
const player=await attachTorquePlayback(gltf,{threeRevision:THREE.REVISION});
const objects=new Map();
for(const node of gltf.scene.children){const id=node.userData.ontokin;const key=id?.path??(id?.kind==='visual_helper'?'helper:'+id.frame_path+':'+id.helper_kind:null);check(key&&!objects.has(key),'Missing/duplicate carrier');objects.set(key,node);}
const images=[],meshes=[];const imageSet=new Set();
for(const [path,carrier]of objects){
 carrier.traverse(node=>{
  if(!node.isMesh)return;
  const attrs={};for(const name of ['position','normal','uv'])if(node.geometry.attributes[name]){
   const a=node.geometry.attributes[name];attrs[name]={itemSize:a.itemSize,count:a.count,normalized:a.normalized,values:Array.from(a.array)};
  }
  const materials=(Array.isArray(node.material)?node.material:[node.material]).map(m=>({name:m.name,color:m.color.toArray(),opacity:m.opacity,metalness:m.metalness,roughness:m.roughness,texture:!!m.map,colorSpace:m.map?.colorSpace??null}));
  meshes.push({carrier:path,name:node.name,association:gltf.parser.associations.get(node)??null,attributes:attrs,indices:node.geometry.index?Array.from(node.geometry.index.array):null,materials,local_matrix:node.matrix.toArray()});
  for(const m of Array.isArray(node.material)?node.material:[node.material])if(m.map&&!imageSet.has(m.map.image)){
   const im=m.map.image;check(im instanceof ImageBitmap,'Actual native ImageBitmap required');imageSet.add(im);
   const canvas=document.createElement('canvas');canvas.width=im.width;canvas.height=im.height;const c=canvas.getContext('2d');c.drawImage(im,0,0);
   images.push({width:im.width,height:im.height,rgba:Array.from(c.getImageData(0,0,im.width,im.height).data),colorSpace:m.map.colorSpace});
  }
 });
}
const scene=new THREE.Scene();scene.background=new THREE.Color(0xe8edf2);scene.add(gltf.scene);
scene.add(new THREE.AmbientLight(0xffffff,1.6));
for(const p of [[5,-5,9],[-5,4,5]]){const l=new THREE.DirectionalLight(0xffffff,2);l.position.set(...p);scene.add(l);}
const renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});renderer.setPixelRatio(1);renderer.setSize(1000,700);renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.NoToneMapping;document.body.append(renderer.domElement);
const camera=new THREE.PerspectiveCamera(35,1000/700,.001,100000);
function sample(time){const budget=player.setTime(time);const carriers={};for(const [name,node]of objects)carriers[name]={matrix:node.matrixWorld.toArray(),position:node.getWorldPosition(new THREE.Vector3()).toArray(),quaternion:node.getWorldQuaternion(new THREE.Quaternion()).toArray(),element_id:node.userData.ontokin.element_id??node.userData.ontokin.related_element_id};return {time,carriers,operations:budget.operations};}
function capture(time,view){sample(time);const box=new THREE.Box3().setFromObject(gltf.scene);const center=box.getCenter(new THREE.Vector3()),radius=Math.max(.1,box.getSize(new THREE.Vector3()).length()/2),distance=radius/Math.sin(35*Math.PI/360)*1.25;
 const direction=(view==='front'?new THREE.Vector3(0,-.15,1):view==='back'?new THREE.Vector3(0,0,-1):new THREE.Vector3(.9,-.8,1.1)).normalize();camera.position.copy(center).addScaledVector(direction,distance);camera.near=Math.max(.001,distance-radius*1.6);camera.far=distance+radius*3+1;camera.lookAt(center);camera.updateProjectionMatrix();camera.updateMatrixWorld(true);renderer.render(scene,camera);
 return {time,view,bounds:{min:box.min.toArray(),max:box.max.toArray()},render_calls:renderer.info.render.calls,triangles:renderer.info.render.triangles};}
globalThis.TORQUE={sample,capture,metadata:gltf.parser.json.extras.ontokin,inventory:{three_revision:THREE.REVISION,player:{name:player.name,version:player.version,carriers:player.carrierCount},objects:Array.from(objects,([path,n])=>({path,ontokin:n.userData.ontokin})),images,meshes}};globalThis.READY=true;
`;
const built=await build({stdin:{contents:code,sourcefile:'torque-native-probe.mjs',resolveDir:path.dirname(modules)},nodePaths:[modules],bundle:true,write:false,format:'esm',platform:'browser',target:'es2022'});
const script=Buffer.from(built.outputFiles[0].contents);const browser=await chromium.launch({headless:true,args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const pins=JSON.parse(await readFile(path.join(modules,'playwright-core/browsers.json'))).browsers.find(x=>x.name==='chromium');assert.equal(browser.version(),pins.browserVersion);
let page=null,current=null,errors=[];const rl=createInterface({input:process.stdin,crlfDelay:Infinity});
try{for await(const line of rl){let result;try{
 const request=JSON.parse(line);assert.ok(line.length<1024*1024);
 if(request.operation==='load'){
  if(page)await page.close();errors=[];const bytes=await readFile(request.artifact);assert.ok(bytes.length<=64*1024*1024);assert.equal(sha(bytes),request.sha256);
  await mkdir(request.output,{recursive:true});const validation=await validator.validateBytes(new Uint8Array(bytes),{uri:path.basename(request.artifact),maxIssues:1000,externalResourceFunction:()=>Promise.reject(new Error('External resource'))});
  await save(path.join(request.output,'khronos.json'),validation);assert.equal(validation.issues.numErrors,0);assert.equal(validation.issues.numWarnings,0);
  const html='<html><head><meta charset="utf-8"><style>body{margin:0;background:#e8edf2}canvas{display:block}</style></head><body><script>globalThis.GLB='+JSON.stringify(bytes.toString('base64'))+';</script><script type="module" src="/probe.js"></script></body></html>';
  page=await browser.newPage({viewport:{width:1000,height:700}});page.on('pageerror',e=>errors.push(String(e)));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
  await page.route('**/*',route=>{const u=route.request().url();return u==='https://ontokin-torque.invalid/'?route.fulfill({contentType:'text/html',body:html}):u==='https://ontokin-torque.invalid/probe.js'?route.fulfill({contentType:'text/javascript',body:script}):route.abort();});
  await page.goto('https://ontokin-torque.invalid/');await page.waitForFunction(()=>globalThis.READY===true,{},{timeout:45000});
  const inventory=await page.evaluate(()=>globalThis.TORQUE.inventory);assert.deepEqual(errors,[]);current=request;
  const identity={node:process.version,dependencies,browser:browser.version(),chromium_pin:pins,gltf_loader_sha256:sha(await readFile(path.join(modules,'three/examples/jsm/loaders/GLTFLoader.js'))),wrapper_sha256:sha(await readFile(path.join(root,'tools/torque_destination.mjs'))),inherited_arithmetic_sha256:sha(await readFile(path.join(root,'tools/reach_destination.mjs'))),observer_sha256:sha(script),artifact_sha256:sha(bytes),artifact_bytes:bytes.length};
  await save(path.join(request.output,'native-inventory.json'),{identity,inventory});
  const shared=request.shared_output??request.output;await mkdir(shared,{recursive:true});
  const observer=path.join(shared,'observer-'+sha(script)+'.js');
  try{await writeFile(observer,script,{flag:'wx'});}catch(error){if(error.code!=='EEXIST')throw error;assert.equal(sha(await readFile(observer)),sha(script));}
  result={status:'passed',identity,inventory};
 }else if(request.operation==='sample'){
  assert.ok(page&&Array.isArray(request.times)&&request.times.length<=128&&request.times.every(Number.isFinite));
  const samples=await page.evaluate(times=>times.map(t=>globalThis.TORQUE.sample(t)),request.times);assert.deepEqual(errors,[]);result={status:'passed',samples};
 }else if(request.operation==='captures'){
  assert.ok(page&&request.times.length<=8);const captures=[];
  for(let i=0;i<request.times.length;i++){const time=request.times[i],view=['front','oblique','back'][i%3];const info=await page.evaluate(({time,view})=>globalThis.TORQUE.capture(time,view),{time,view});const name='capture-'+i+'-'+view+'.png';await page.screenshot({path:path.join(current.output,name)});captures.push({...info,path:name,sha256:sha(await readFile(path.join(current.output,name)))});}
  assert.deepEqual(errors,[]);await save(path.join(current.output,'captures.json'),captures);result={status:'passed',captures};
 }else if(request.operation==='close'){result={status:'passed'};process.stdout.write(JSON.stringify(result)+'\n');break;}
 else throw new Error('Unknown operation');
 }catch(error){result={status:'failed',error:{name:error.name,message:error.message,stack:error.stack},page_errors:errors};}
 process.stdout.write(JSON.stringify(result)+'\n');
}}finally{rl.close();if(page)await page.close();await browser.close();}
