#!/usr/bin/env node
// C082: pinned Khronos validation and real Three.js GLTFLoader/ImageBitmap
// decoding in Chromium. No mocked image decoder, patched loader or fake canvas.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {readFile,writeFile,mkdir,stat} from 'node:fs/promises';
import {createRequire} from 'node:module';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const sha=data=>createHash('sha256').update(data).digest('hex');
const save=async(file,value)=>writeFile(file,JSON.stringify(value,null,2)+'\n');
const PACKAGES={three:'0.180.0','gltf-validator':'2.0.0-dev.3.10',playwright:'1.56.1',esbuild:'0.25.10'};
const DEFAULT_MODULES=path.join(ROOT,'tools/node_modules');
const DEFAULT_BROWSERS=process.env.PLAYWRIGHT_BROWSERS_PATH;
const CAPTURE_CASES=new Set(['panel-task','panel-task-repaired','panel-identity','panel-task-higher-budget']);

function argumentsForRun(args){
 const values={};
 for(let i=0;i<args.length;i+=2){
  assert.ok(['--input','--output','--fixtures','--node-modules','--browser-cache','--python'].includes(args[i])&&args[i+1],`Unknown/incomplete argument ${args[i]}`);
  assert.equal(values[args[i]],undefined,'Options must not repeat');values[args[i]]=args[i+1];
 }
 assert.ok(values['--input']&&values['--output'],'--input and --output are required');
 return values;
}

function ordinary(root,relative){
 assert.equal(typeof relative,'string');assert.ok(relative&&!path.isAbsolute(relative)&&!relative.includes('\\'));
 assert.ok(relative.split('/').every(x=>x&&x!=='.'&&x!=='..'));
 const result=path.resolve(root,relative);assert.ok(result.startsWith(root+path.sep));return result;
}

const browserSource=String.raw`
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
const expected=globalThis.EXPECTED;
const check=(v,m)=>{if(!v)throw new Error(m);};
const near=(a,b,t=1e-5)=>{check(a.length===b.length,'Vector shape');for(let i=0;i<a.length;i++)check(Number.isFinite(a[i])&&Math.abs(a[i]-b[i])<=t,'Vector difference '+JSON.stringify({a,b,t}));};
function hex32(values){const buffer=new ArrayBuffer(values.length*4),view=new DataView(buffer);values.forEach((v,i)=>view.setFloat32(4*i,v,true));return Array.from(new Uint8Array(buffer),v=>v.toString(16).padStart(2,'0')).join('');}
function float32UlpDistance(a,b){const data=new DataView(new ArrayBuffer(8));data.setFloat32(0,a===0?0:a,true);data.setFloat32(4,b===0?0:b,true);check(a>=0&&b>=0,'Color ULP comparison requires nonnegative channels');return Math.abs(data.getUint32(0,true)-data.getUint32(4,true));}
async function hash(bytes){return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),x=>x.toString(16).padStart(2,'0')).join('');}
const data=Uint8Array.from(atob(globalThis.BYTES),c=>c.charCodeAt(0));
const loader=new GLTFLoader();
const gltf=await loader.parseAsync(data.buffer,'');
const contract=gltf.parser.json.extras?.ontokin;
check(contract?.target_contract===expected.target_contract&&contract?.profile===expected.source_profile&&contract?.schema_version==='0.15','Loaded explicit .15 source/target contract differs');
check(contract.program.revision===expected.program_revision,'Loaded immutable source revision differs');
check(gltf.animations.length===1,'Exactly one native recorded animation');
const scene=new THREE.Scene();scene.background=new THREE.Color(0xe6edf2);scene.add(gltf.scene);
scene.add(new THREE.AmbientLight(0xffffff,1.45));
for(const [x,y,z,intensity] of [[5,-5,9,2.5],[-4,4,6,1.3]]){const light=new THREE.DirectionalLight(0xffffff,intensity);light.position.set(x,y,z);scene.add(light);}
const renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});renderer.setPixelRatio(1);renderer.setSize(1100,720);renderer.outputColorSpace=THREE.SRGBColorSpace;
renderer.toneMapping=THREE.NoToneMapping;document.querySelector('#view').append(renderer.domElement);
const camera=new THREE.PerspectiveCamera(35,1100/720,.001,10000),mixer=new THREE.AnimationMixer(gltf.scene),action=mixer.clipAction(gltf.animations[0]);
function seek(t){action.reset().setLoop(THREE.LoopOnce,1).play();action.clampWhenFinished=true;mixer.setTime(t);gltf.scene.updateMatrixWorld(true);}
const bounds=new THREE.Box3();for(const t of [0,.5,1]){seek(t);bounds.union(new THREE.Box3().setFromObject(gltf.scene));}
const center=bounds.getCenter(new THREE.Vector3()),radius=Math.max(.1,bounds.getSize(new THREE.Vector3()).length()/2),distance=radius/Math.sin(35*Math.PI/360)*1.28;
function observe(t,view='front'){
 seek(t);
 const direction=view==='oblique'?new THREE.Vector3(.7,-.8,1.1):view==='underside'?new THREE.Vector3(0,0,-1):view==='label-face'?new THREE.Vector3(1,0,0):new THREE.Vector3(0,0,1);
 direction.normalize();camera.position.copy(center).addScaledVector(direction,distance);camera.near=Math.max(.001,distance-radius*1.6);camera.far=distance+radius*3+1;camera.lookAt(center);camera.updateProjectionMatrix();camera.updateMatrixWorld(true);renderer.render(scene,camera);
 document.querySelector('#clock').textContent=t+' s | '+view;
 const objects={};let maxNdc=0,triangles=0;
 gltf.scene.traverse(node=>{
  if(node.userData.ontokin?.kind==='object'){
   const key=node.userData.ontokin.path;check(!(key in objects),'Duplicate loaded carrier');
   check(JSON.stringify(node.userData.ontokin.element_id)===JSON.stringify(expected.nodes[key]?.element_id),'Loaded ordinary/generated identity differs');
   objects[key]={position:node.getWorldPosition(new THREE.Vector3()).toArray(),rotation:node.getWorldQuaternion(new THREE.Quaternion()).toArray(),scale:node.getWorldScale(new THREE.Vector3()).toArray()};
  }
  if(node.isMesh){
   triangles+=(node.geometry.index?.count??node.geometry.attributes.position.count)/3;
   node.geometry.computeBoundingBox();const box=node.geometry.boundingBox;
   for(const x of [box.min.x,box.max.x])for(const y of [box.min.y,box.max.y])for(const z of [box.min.z,box.max.z]){
    const p=new THREE.Vector3(x,y,z).applyMatrix4(node.matrixWorld).project(camera);maxNdc=Math.max(maxNdc,Math.abs(p.x),Math.abs(p.y));
   }
  }
 });
 check(JSON.stringify(Object.keys(objects).sort())===JSON.stringify(Object.keys(expected.nodes).sort()),'Loaded carrier inventory differs');
 for(const [key,wanted] of Object.entries(expected.nodes)){
  near(objects[key].position,wanted.origin.map((v,i)=>v+t*wanted.velocity[i]),.001);
  near(objects[key].scale,[1,1,1],1e-6);
  const q=new THREE.Quaternion(...objects[key].rotation);near([q.length()],[1],1e-5);
  check(q.angleTo(new THREE.Quaternion())<=.001,'Recorded orientation exceeds unchanged .001-radian tolerance');
 }
 check(triangles===Object.values(expected.nodes).reduce((n,v)=>n+v.triangle_count,0),'Loaded triangle count differs from source');
 check(maxNdc<=1&&renderer.info.render.calls>0,'Actual rendered model is clipped or has no draw calls');
 return {time_seconds:t,objects,max_abs_ndc_xy:maxNdc,triangles,render_calls:renderer.info.render.calls};
}
const primitiveReports=[],mapEntries=[],assetTextures=new Map(),usedImages=new Set();
gltf.scene.traverse(node=>{
 if(!node.isMesh)return;
 check(!Array.isArray(node.material),'Native regional primitive unexpectedly merged materials');
 const material=node.material,identity=material.userData.ontokin;
 check(identity&&identity.program_revision===expected.program_revision,'Loaded material source provenance differs');
 const path=identity.occurrence_path,region=identity.source_region_key,wanted=expected.nodes[path];
 check(wanted&&!wanted.empty,'Loaded mesh has absent/empty source carrier');
 const geometry=node.geometry,position=geometry.getAttribute('position'),normal=geometry.getAttribute('normal'),uv=geometry.getAttribute('uv');
 check(position&&normal&&position.count===normal.count,'Loaded native position/normal cardinality');
 const indices=geometry.index?Array.from(geometry.index.array):Array.from({length:position.count},(_,i)=>i),selected=new Set(indices);
 const corners=new Set(wanted.position_keys);
 for(const i of selected)check(corners.has(hex32([position.getX(i),position.getY(i),position.getZ(i)])),'Loaded corner absent from independent source coordinates');
 const factors=wanted.materials[region];check(factors,'Loaded material region absent from frozen source');
 near(material.color.toArray(),factors.baseColorFactor.slice(0,3),1e-12);
 check(material.opacity===factors.baseColorFactor[3]&&material.metalness===factors.metallicFactor&&material.roughness===factors.roughnessFactor,'Loaded PBR factors differ');
 check(indices.length/3===wanted.region_triangle_counts[region],'Loaded regional triangle count differs');
 check(material.side===THREE.FrontSide&&!material.transparent,'Opacity/back-face behavior changed');
 const binding=wanted.bindings[region];
 if(!binding){check(material.map===null&&!uv,'Untextured region acquired appearance');primitiveReports.push({path,region,textured:false,triangles:indices.length/3});return;}
 const map=material.map;check(map&&uv&&uv.count===position.count&&uv.itemSize===2,'Missing native loaded UV/texture');
 check(map.minFilter===THREE.NearestFilter&&map.magFilter===THREE.NearestFilter&&map.wrapS===THREE.ClampToEdgeWrapping&&map.wrapT===THREE.ClampToEdgeWrapping,'Native loaded sampler differs');
 check(map.flipY===false&&map.colorSpace===THREE.SRGBColorSpace,'Native loaded image orientation/color space differs');
 const association=gltf.parser.associations.get(map);check(association&&Number.isInteger(association.textures),'Loaded texture lacks actual GLTFLoader reference association');
 const texture=gltf.parser.json.textures[association.textures],sourceIndex=texture.source,source=gltf.parser.json.images[sourceIndex];
 check(source.extras.ontokin.asset_id===binding.asset_id,'Actual GLTFLoader selected another image');
 usedImages.add(sourceIndex);
 if(assetTextures.has(binding.asset_id))check(assetTextures.get(binding.asset_id).sourceIndex===sourceIndex,'Same asset ID loaded through multiple image references');
 else assetTextures.set(binding.asset_id,{map,sourceIndex,asset:expected.assets[binding.asset_id]});
 for(let i=0;i<uv.count;i++){
  const actual=hex32([uv.getX(i),uv.getY(i)]);
  if(!selected.has(i)){check(actual==='0000000000000000','Loaded unreferenced UV is not exact positive zero');continue;}
  const key=hex32([position.getX(i),position.getY(i),position.getZ(i)]);
  check(actual===binding.uv_by_position[key],'Native loaded UV differs from exact independently computed affine map');
 }
 mapEntries.push({path,region,map,material,asset:expected.assets[binding.asset_id]});
 primitiveReports.push({path,region,textured:true,asset_id:binding.asset_id,uv_rows:selected.size,triangles:indices.length/3,
  min_filter:map.minFilter,mag_filter:map.magFilter,wrap_s:map.wrapS,wrap_t:map.wrapT,flip_y:map.flipY,color_space:map.colorSpace});
});
check(JSON.stringify([...assetTextures.keys()].sort())===JSON.stringify(expected.used_asset_ids),'Native loaded used image set differs');
check(usedImages.size===(gltf.parser.json.images??[]).length,'Native loader document has dangling images');
const imageReports=[];
for(const [id,{map,asset,sourceIndex}] of assetTextures){
 const image=map.image;
 check(image instanceof ImageBitmap||image instanceof HTMLImageElement,'Texture image must be a real native decoded image');
 check(image.width===asset.width&&image.height===asset.height,'Native image dimensions differ');
 const canvas=document.createElement('canvas');canvas.width=image.width;canvas.height=image.height;
 const context=canvas.getContext('2d',{willReadFrequently:true});context.drawImage(image,0,0);
 const rgba=context.getImageData(0,0,image.width,image.height).data,actualHash=await hash(rgba);
 check(actualHash===asset.rgba_sha256,'Native PNG decode changed exact top-to-bottom RGBA pixels');
 imageReports.push({asset_id:id,source_index:sourceIndex,width:image.width,height:image.height,
  image_class:image.constructor.name,rgba_sha256:actualHash,expected_png_sha256:asset.png_sha256});
}
// This diagnostic samples the actual GLTFLoader texture and exported factor,
// before lighting. It creates no replacement image or product geometry.
const colorProbes=[];
if(mapEntries.length){
 const gl=renderer.getContext();check(gl.getExtension('EXT_color_buffer_float'),'Float32 color readback extension required');
 const target=new THREE.WebGLRenderTarget(1,1,{type:THREE.FloatType,format:THREE.RGBAFormat,depthBuffer:false,stencilBuffer:false});
 target.texture.colorSpace=THREE.LinearSRGBColorSpace;
 const probeScene=new THREE.Scene(),probeCamera=new THREE.OrthographicCamera(-1,1,1,-1,.1,10);probeCamera.position.z=1;
 const seen=new Set();
 for(const entry of mapEntries){
  const factor=entry.material.color.toArray(),signature=entry.asset.asset_id+'/'+factor.join(',');if(seen.has(signature))continue;seen.add(signature);
  const geometry=new THREE.PlaneGeometry(2,2),material=new THREE.MeshBasicMaterial({map:entry.map,color:entry.material.color.clone(),toneMapped:false});
  const plane=new THREE.Mesh(geometry,material);probeScene.add(plane);
  for(const sample of entry.asset.pixel_probes){
   const attribute=geometry.getAttribute('uv');for(let i=0;i<attribute.count;i++)attribute.setXY(i,...sample.uv);attribute.needsUpdate=true;
   renderer.setRenderTarget(target);renderer.render(probeScene,probeCamera);
   const actual=new Float32Array(4);renderer.readRenderTargetPixels(target,0,0,1,1,actual);
   const expectedLinear=sample.rgba.slice(0,3).map((byte,i)=>{const x=byte/255;return(x<=.04045?x/12.92:((x+.055)/1.055)**2.4)*factor[i];});
   check(Array.from(actual).every(Number.isFinite)&&Math.abs(actual[3]-1)<=1e-12,'Actual Float32 color probe is invalid/nonopaque');
   const expectedFloat32=sample.rgba.slice(0,3).map((byte,i)=>{const x=byte/255,linear=x<=.04045?x/12.92:((x+.055)/1.055)**2.4;return Math.fround(Math.fround(linear)*Math.fround(factor[i]));});
   const ulps=expectedFloat32.map((value,i)=>float32UlpDistance(value,actual[i]));
   const endpoint=sample.rgba.slice(0,3).every(x=>x===0||x===255);
   // GPU uniforms and render-target channels are binary32. For endpoints the
   // transfer is exactly0/1; one binary32 ULP bounds storage/multiplication
   // rounding. This is separate from the unchanged1e-12 CPU formula gate.
   if(endpoint)check(ulps.every(value=>value<=1),'Actual endpoint color differs by more than one binary32 ULP');
   colorProbes.push({asset_id:entry.asset.asset_id,path:entry.path,region:entry.region,xy:sample.xy,
    factor_linear_rgb:factor,source_srgb_bytes:sample.rgba.slice(0,3),expected_binary64_linear_rgb:expectedLinear,
    expected_float32_linear_rgb:expectedFloat32,float32_ulp_delta:ulps,endpoint_maximum_float32_ulps:endpoint?1:null,
    actual_float32_linear_rgba:Array.from(actual),absolute_delta:expectedLinear.map((v,i)=>Math.abs(v-actual[i])),
    exact_endpoint_gate:endpoint,midtone_precision_scope:endpoint?null:'Measured Float32 GPU sampling; not a claim to satisfy the separate 1e-12 binary64 CPU formula tolerance.'});
  }
  probeScene.remove(plane);geometry.dispose();material.dispose();
 }
 renderer.setRenderTarget(null);target.dispose();
}
globalThis.textureObserver={observe};
globalThis.DECODE_REPORT={three_revision:THREE.REVISION,primitive_reports:primitiveReports,images:imageReports,color_probes:colorProbes,
 color_probe_scope:'Actual GLTFLoader texture sampled by MeshBasicMaterial with the exact exported linear factor before lighting. Native scene captures retain original GLTFLoader PBR materials.'};
observe(0);globalThis.READY=true;
`;

async function browserCheck(browser,script,bytes,expected,output,capture){
 const html='<!doctype html><meta charset="utf-8"><title>OntoKin native keyed reduction evidence</title><style>body{margin:0;background:#e6edf2;color:#20313f;font:18px system-ui}header{padding:16px 24px;display:flex;justify-content:space-between}canvas{display:block}</style><header><strong>OntoKin | '+expected.name+'</strong><span id="clock"></span></header><div id="view"></div><script>globalThis.BYTES='+JSON.stringify(bytes.toString('base64'))+';globalThis.EXPECTED='+JSON.stringify(expected)+'</script><script type="module" src="/observer.js"></script>';
 const report={browser_version:browser.version(),page_errors:[],failed_requests:[],console_errors:[],observations:[],captures:[],visual_review:'pending_actual_image_inspection'};
 const page=await browser.newPage({viewport:{width:1100,height:780},deviceScaleFactor:1});
 try{
  page.on('pageerror',error=>report.page_errors.push(String(error)));
  page.on('console',message=>{if(message.type()==='error')report.console_errors.push(message.text());});
  page.on('requestfailed',request=>report.failed_requests.push(request.url()));
  await page.route('**/*',route=>{
   const url=route.request().url();
   if(url==='https://ontokin-textures.invalid/')return route.fulfill({contentType:'text/html',body:html});
   if(url==='https://ontokin-textures.invalid/observer.js')return route.fulfill({contentType:'text/javascript',body:script});
   return route.abort();
  });
  await page.goto('https://ontokin-textures.invalid/');
  await page.waitForFunction(()=>globalThis.READY===true,{},{timeout:45000});
  report.native_decode=await page.evaluate(()=>globalThis.DECODE_REPORT);
  assert.equal(report.native_decode.three_revision,'180');
  for(const time of [0,.25,.5,.75,1])report.observations.push(await page.evaluate(time=>globalThis.textureObserver.observe(time),time));
  if(capture){
   const views=['front','oblique'];
   for(const view of views){
    const observation=await page.evaluate(view=>globalThis.textureObserver.observe(.5,view),view);
    const filename=view+'.png';await page.screenshot({path:path.join(output,filename)});
    report.captures.push({path:filename,view,time_seconds:.5,sha256:sha(await readFile(path.join(output,filename))),max_abs_ndc_xy:observation.max_abs_ndc_xy});
   }
  }
  assert.deepEqual(report.page_errors,[]);assert.deepEqual(report.failed_requests,[]);assert.deepEqual(report.console_errors,[]);
  report.status='passed';
 }catch(error){report.status='failed';report.failure={name:error.name,message:error.message,stack:error.stack};}
 finally{await page.close();}
 return report;
}

async function main(){
 const args=argumentsForRun(process.argv.slice(2)),input=path.resolve(args['--input']),output=path.resolve(args['--output']);
 assert.ok(!output.startsWith(ROOT+path.sep),'Evidence output must be outside the checkout');
 assert.equal(process.version,'v22.16.0','Use the actually pinned Node 22.16.0 executable');
 await mkdir(output,{recursive:false});
 const modules=path.resolve(args['--node-modules']??DEFAULT_MODULES);
 process.env.PLAYWRIGHT_BROWSERS_PATH=path.resolve(args['--browser-cache']??DEFAULT_BROWSERS);
 const require=createRequire(path.join(path.dirname(modules),'package.json'));
 const dependencies=[];
 for(const [name,version] of Object.entries(PACKAGES)){
  const file=path.join(modules,name,'package.json'),raw=await readFile(file),value=JSON.parse(raw);
  assert.equal(value.version,version,'Pinned dependency differs: '+name);dependencies.push({name,version,package_json_sha256:sha(raw)});
 }
 const {build}=require('esbuild'),{chromium}=require('playwright'),validator=require('gltf-validator');
 const browserManifest=JSON.parse(await readFile(path.join(modules,'playwright-core/browsers.json')));
 const chromiumPin=browserManifest.browsers.find(item=>item.name==='chromium');
 const expectedFile=path.join(output,'independent-source-expectations.json');
 const referenceCommand=[path.join(ROOT,'tools/keyed_reduction_destination_expectations.py'),'--fixtures',path.resolve(args['--fixtures']??path.join(ROOT,'examples/keyed-reduction')),'--output',expectedFile];
 const referenceStdout=execFileSync(args['--python']??'python3',['-B',...referenceCommand],{cwd:ROOT,encoding:'utf8',maxBuffer:1024*1024});
 const expected=JSON.parse(await readFile(expectedFile)),summary=JSON.parse(await readFile(path.join(input,'summary.json')));
 assert.equal(expected.frozen_input_commit,summary.frozen_input_commit,'Published input freeze commit differs');
 assert.equal(expected.frozen_manifest_sha256,summary.frozen_manifest_sha256,'Published input freeze bytes differ');
 assert.equal(summary.status,'produced_as_expected','Actual producer must complete before independent destination acceptance');
 const byRevision=new Map();
 for(const item of Object.values(expected.cases)){
  const previous=byRevision.get(item.program_revision);
  if(previous){
   const {name:an,id:ai,...a}=previous,{name:bn,id:bi,...b}=item;
   assert.deepEqual(a,b,'Named source aliases have conflicting independent destination expectations');
  }else byRevision.set(item.program_revision,item);
 }
 assert.equal(byRevision.size,expected.unique_delivered_bundles);
 const artifacts=[...summary.cases.filter(item=>item.delivered).map(item=>({...item,scope:'source'})),
  ...summary.agent_artifacts.map(item=>({...item,name:item.project_id+'-'+item.name,scope:'agent'}))];
 assert.deepEqual(artifacts.filter(item=>item.scope==='source').map(item=>item.name).sort(),Object.keys(expected.cases).sort(),
  'All four distinct frozen delivered case names must be supplied exactly once');
 const built=await build({stdin:{contents:browserSource,resolveDir:path.dirname(modules),sourcefile:'c082-native-texture-observer.mjs'},nodePaths:[modules],bundle:true,write:false,format:'esm',platform:'browser',target:'es2022'});
 const script=Buffer.from(built.outputFiles[0].contents);await writeFile(path.join(output,'observer.js'),script);
 const report={schema_version:'ontokin.c082-destination-readback/0.1',status:'running',started_utc:new Date().toISOString(),
  command:[process.execPath,...process.argv.slice(1)],node:process.version,dependencies,chromium_pin:chromiumPin,
  input_git:summary.git,frozen_input_commit:expected.frozen_input_commit,
  frozen_manifest_sha256:expected.frozen_manifest_sha256,expected_inputs_sha256:sha(await readFile(expectedFile)),
  expected_inputs_command:[args['--python']??'python3','-B',...referenceCommand],expected_inputs_stdout:referenceStdout,
  observer_sha256:sha(script),gltf_loader_sha256:sha(await readFile(path.join(modules,'three/examples/jsm/loaders/GLTFLoader.js'))),
  artifacts:[],release_acceptance:false,visual_review:'pending_actual_image_inspection',
  scope:'Pinned Khronos and real native-image Three.js/Chromium source-derived rectangular-prism geometry, stable keys, UV/pixel/material/pose readback, with finite captured views. No claim of Unreal import or live contact physics.'};
 const browser=await chromium.launch({headless:true,args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 try{
  report.actual_browser_version=browser.version();assert.equal(browser.version(),chromiumPin.browserVersion,'Pinned actual Chromium version differs');
  for(let index=0;index<artifacts.length;index++){
   const item=artifacts[index],directory=path.join(output,String(index+1).padStart(3,'0')+'-'+item.scope+'-'+item.name);await mkdir(directory);
   const observation={name:item.name,scope:item.scope,path:item.glb,program_revision:item.program_revision};
   try{
    const bytes=await readFile(ordinary(input,item.glb));assert.equal(sha(bytes),item.sha256);assert.equal(bytes.length,item.bytes);
    const spec=item.scope==='source'?expected.cases[item.name]:byRevision.get(item.program_revision);
    assert.ok(spec,'Actual artifact revision lacks frozen source expectations');
    assert.equal(item.program_revision,spec.program_revision,'Named actual artifact revision differs from its frozen source');
    const validation=await validator.validateBytes(new Uint8Array(bytes),{uri:path.basename(item.glb),maxIssues:1000,
      externalResourceFunction:()=>Promise.reject(new Error('External resources are forbidden for self-contained GLB'))});
    await save(path.join(directory,'khronos.json'),validation);
    observation.khronos={errors:validation.issues.numErrors,warnings:validation.issues.numWarnings,infos:validation.issues.numInfos,
                         report:path.relative(output,path.join(directory,'khronos.json'))};
    assert.equal(validation.issues.numErrors,0,'Khronos errors');assert.equal(validation.issues.numWarnings,0,'Khronos warnings');
    observation.browser=await browserCheck(browser,script,bytes,spec,directory,CAPTURE_CASES.has(spec.name));
    await save(path.join(directory,'browser.json'),observation.browser);
    observation.status=observation.browser.status;
    observation.sha256=sha(bytes);observation.bytes=bytes.length;
   }catch(error){observation.status='failed';observation.failure={name:error.name,message:error.message,stack:error.stack};}
   report.artifacts.push(observation);await save(path.join(output,'report.json'),report);
   process.stdout.write(JSON.stringify({artifact:item.name,scope:item.scope,status:observation.status,completed:index+1,total:artifacts.length})+'\n');
  }
 }finally{await browser.close();}
 report.status=report.artifacts.every(item=>item.status==='passed')?'passed':'failed';report.finished_utc=new Date().toISOString();
 report.coverage={source_artifacts:report.artifacts.filter(item=>item.scope==='source').length,agent_artifacts:report.artifacts.filter(item=>item.scope==='agent').length,
  unique_delivered_bundles:byRevision.size,unique_supplied_glbs:new Set(report.artifacts.filter(item=>item.sha256).map(item=>item.sha256)).size,
  browser_images:report.artifacts.reduce((n,item)=>n+(item.browser?.native_decode?.images.length??0),0),
  captured_views:report.artifacts.reduce((n,item)=>n+(item.browser?.captures.length??0),0),
  recorded_pose_times_per_artifact:5};
 await save(path.join(output,'report.json'),report);
 process.stdout.write(JSON.stringify({status:report.status,...report.coverage,visual_review:report.visual_review})+'\n');
 process.exitCode=report.status==='passed'?0:1;
}

main().catch(error=>{process.stderr.write(error.stack+'\n');process.exitCode=1;});
