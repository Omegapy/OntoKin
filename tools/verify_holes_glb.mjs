#!/usr/bin/env node
// Independent Khronos/Three.js decoding and actual browser playback for C076.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import validator from 'gltf-validator';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {AnimationMixer,LoopOnce,Vector3,Quaternion,Matrix4,REVISION} from 'three';
import {build} from 'esbuild';
import {chromium} from 'playwright';
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const sha=data=>createHash('sha256').update(data).digest('hex');
function near(a,b,t=1e-5){assert.equal(a.length,b.length);for(let i=0;i<a.length;i++)assert.ok(Number.isFinite(a[i])&&Math.abs(a[i]-b[i])<=t,`${a} vs ${b}`);}
function compare(objects,expected,t){
  assert.deepEqual(Object.keys(objects).sort(),Object.keys(expected.nodes).sort());
  return Object.entries(expected.nodes).map(([name,n])=>{const p=n.origin.map((x,i)=>x+t*n.velocity[i]);near(objects[name].position,p,.001);near(objects[name].rotation,[0,0,0,1],.001);near(objects[name].scale,[1,1,1],1e-6);return {path:name,time_seconds:t,position:objects[name].position,rotation:objects[name].rotation,scale:objects[name].scale};});
}
const browserSource=`
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
const bytes=Uint8Array.from(atob(globalThis.BYTES),c=>c.charCodeAt(0));
const gltf=await new GLTFLoader().parseAsync(bytes.buffer,'');
const scene=new THREE.Scene();scene.background=new THREE.Color(0xe7edf2);scene.add(gltf.scene);scene.add(new THREE.AmbientLight(0xffffff,1.5));
for(const [x,y,z,power] of [[6,8,10,2.5],[-4,3,-8,1.8]]){const l=new THREE.DirectionalLight(0xffffff,power);l.position.set(x,y,z);scene.add(l);}
const renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});renderer.setPixelRatio(1);renderer.setSize(1100,720);renderer.outputColorSpace=THREE.SRGBColorSpace;document.querySelector('#view').append(renderer.domElement);
const camera=new THREE.PerspectiveCamera(35,1100/720,.001,10000),mixer=new THREE.AnimationMixer(gltf.scene),action=mixer.clipAction(gltf.animations[0]);
function seek(t){action.reset().setLoop(THREE.LoopOnce,1).play();action.clampWhenFinished=true;mixer.setTime(t);gltf.scene.updateMatrixWorld(true);}
const bounds=new THREE.Box3();for(const t of [0,.5,1]){seek(t);bounds.union(new THREE.Box3().setFromObject(gltf.scene));}
const center=bounds.getCenter(new THREE.Vector3()),radius=Math.max(.1,bounds.getSize(new THREE.Vector3()).length()/2),distance=radius/Math.sin(35*Math.PI/360)*1.25;
function observe(t,view='front'){
 seek(t);const direction=view==='oblique'?new THREE.Vector3(.7,-.6,1):new THREE.Vector3(0,0,1);direction.normalize();camera.position.copy(center).addScaledVector(direction,distance);camera.near=Math.max(.001,distance-radius*1.6);camera.far=distance+radius*3+1;camera.lookAt(center);camera.updateProjectionMatrix();camera.updateMatrixWorld(true);renderer.render(scene,camera);
 document.querySelector('#clock').textContent=t+' s | '+view;const objects={};let maxNdc=0,triangles=0;
 gltf.scene.traverse(n=>{if(n.userData.ontokin?.kind==='object')objects[n.userData.ontokin.path]={position:n.getWorldPosition(new THREE.Vector3()).toArray(),rotation:n.getWorldQuaternion(new THREE.Quaternion()).toArray(),scale:n.getWorldScale(new THREE.Vector3()).toArray()};if(n.isMesh){triangles+=(n.geometry.index?.count??n.geometry.attributes.position.count)/3;n.geometry.computeBoundingBox();const b=n.geometry.boundingBox;for(const x of [b.min.x,b.max.x])for(const y of [b.min.y,b.max.y])for(const z of [b.min.z,b.max.z]){const p=new THREE.Vector3(x,y,z).applyMatrix4(n.matrixWorld).project(camera);maxNdc=Math.max(maxNdc,Math.abs(p.x),Math.abs(p.y));}}});return {objects,maxNdc,triangles,renderCalls:renderer.info.render.calls};
}
globalThis.holesObserver={observe};observe(0);globalThis.READY=true;
`;
async function browserCheck(bytes,expected,output){
 const bundled=await build({stdin:{contents:browserSource,resolveDir:path.join(ROOT,'tools'),sourcefile:'holes-observer.mjs'},bundle:true,write:false,format:'esm',platform:'browser',target:'es2022'});
 const script=bundled.outputFiles[0].contents;
 const html='<!doctype html><meta charset="utf-8"><title>OntoKin polygon holes</title><style>body{margin:0;background:#e7edf2;color:#20313f;font:18px system-ui}header{padding:16px 24px;display:flex;justify-content:space-between}canvas{display:block}</style><header><strong>OntoKin | '+expected.case_id+'</strong><span id="clock"></span></header><div id="view"></div><script>globalThis.BYTES='+JSON.stringify(bytes.toString('base64'))+'</script><script type="module" src="/observer.js"></script>';
 const browser=await chromium.launch({headless:true,args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const report={version:browser.version(),observations:[],captures:[],page_errors:[],failed_requests:[],visual_review:'pending_actual_image_inspection',observer_sha256:sha(script)};
 try{
  const page=await browser.newPage({viewport:{width:1100,height:780},deviceScaleFactor:1});page.on('pageerror',e=>report.page_errors.push(String(e)));page.on('requestfailed',r=>report.failed_requests.push(r.url()));
  await page.route('**/*',route=>{const u=route.request().url();if(u==='https://ontokin-holes.invalid/')return route.fulfill({contentType:'text/html',body:html});if(u==='https://ontokin-holes.invalid/observer.js')return route.fulfill({contentType:'text/javascript',body:Buffer.from(script)});return route.abort();});
  await page.goto('https://ontokin-holes.invalid/');await page.waitForFunction(()=>globalThis.READY===true);
  const triangles=Object.values(expected.nodes).reduce((n,x)=>n+(x.geometry?.triangle_count??0),0);
  for(const t of [0,.25,.5,.75,1]){const obs=await page.evaluate(t=>globalThis.holesObserver.observe(t),t);assert.ok(obs.maxNdc<=1&&obs.renderCalls>0);assert.equal(obs.triangles,triangles);report.observations.push(...compare(obs.objects,expected,t));}
  for(const view of ['front','oblique']){const t=expected.case_id==='agent-repaired'?1:.5;const obs=await page.evaluate(({t,view})=>globalThis.holesObserver.observe(t,view),{t,view});assert.ok(obs.maxNdc<=1);const filename=view+'.png';await page.screenshot({path:path.join(output,filename)});report.captures.push({path:filename,time_seconds:t,view,max_abs_ndc_xy:obs.maxNdc,sha256:sha(await readFile(path.join(output,filename)))});}
  assert.deepEqual(report.page_errors,[]);assert.deepEqual(report.failed_requests,[]);report.status='passed';
 }finally{await browser.close();}
 return report;
}
async function main(){
 const [inputDir,outputDir]=process.argv.slice(2);assert.ok(inputDir&&outputDir);const input=path.resolve(inputDir),output=path.resolve(outputDir);assert.ok(!output.startsWith(ROOT+path.sep));await mkdir(output,{recursive:false});
 const report={schema_version:'ontokin.holes-destination-check/0.1',status:'running',started_utc:new Date().toISOString(),source_git:{commit:execFileSync('git',['-C',ROOT,'rev-parse','HEAD'],{encoding:'utf8'}).trim(),tree:execFileSync('git',['-C',ROOT,'rev-parse','HEAD^{tree}'],{encoding:'utf8'}).trim(),tracked_status:execFileSync('git',['-C',ROOT,'status','--porcelain','--untracked-files=no'],{encoding:'utf8'}).trim()},node:process.version,three_revision:REVISION,checker_sha256:sha(await readFile(fileURLToPath(import.meta.url))),artifacts:[],release_acceptance:false};
 try{
  assert.equal(Number(process.versions.node.split('.')[0]),22);
  const pins={three:'0.180.0','gltf-validator':'2.0.0-dev.3.10',playwright:'1.56.1',esbuild:'0.25.10'};
  for(const [n,v]of Object.entries(pins))assert.equal(JSON.parse(await readFile(path.join(ROOT,'tools/node_modules',n,'package.json'))).version,v);report.dependencies=pins;
  const acceptance=JSON.parse(await readFile(path.join(input,'summary.json')));assert.equal(acceptance.status,'passed');
  for(const item of acceptance.artifacts){
   const data=await readFile(path.join(input,item.path)),expectedBytes=await readFile(path.join(input,item.name+'.expected.json')),expected=JSON.parse(expectedBytes);assert.equal(sha(data),item.sha256);assert.equal(expected.program_revision,item.program_revision);
   const check={name:item.name,sha256:sha(data),bytes:data.length,expected_sha256:sha(expectedBytes)};report.artifacts.push(check);
   const format=await validator.validateBytes(new Uint8Array(data),{uri:item.path,maxIssues:200});check.khronos={errors:format.issues.numErrors,warnings:format.issues.numWarnings,messages:format.issues.messages};assert.equal(format.issues.numErrors,0);assert.equal(format.issues.numWarnings,0);
   const gltf=await new GLTFLoader().parseAsync(data.buffer.slice(data.byteOffset,data.byteOffset+data.byteLength),'');assert.equal(gltf.parser.json.extras.ontokin.target_contract,'ontokin.glb/0.9');assert.equal(gltf.parser.json.extras.ontokin.program.revision,expected.program_revision);
   const objects=new Map();gltf.scene.traverse(n=>{if(n.userData.ontokin?.kind==='object')objects.set(n.userData.ontokin.path,n)});assert.deepEqual([...objects.keys()].sort(),Object.keys(expected.nodes).sort());gltf.scene.updateMatrixWorld(true);
   check.geometry=[];
   for(const [name,w]of Object.entries(expected.nodes)){
    let triangles=0;const regions={};const carrier=objects.get(name);const inverse=new Matrix4().copy(carrier.matrixWorld).invert();
    carrier.traverse(n=>{if(!n.isMesh)return;let owner=n.parent;while(owner&&owner.userData.ontokin?.kind!=='object')owner=owner.parent;if(owner!==carrier)return;assert.ok(w.geometry);const g=n.geometry,region=n.material.userData.ontokin.source_region_key;assert.ok(!Array.isArray(n.material));regions[region]=(regions[region]??0)+g.index.count/3;triangles+=g.index.count/3;near([...n.material.color.toArray(),n.material.opacity],w.geometry.palette[region],1e-6);near([n.material.metalness,n.material.roughness],[w.geometry.metallic,w.geometry.roughness],1e-6);
     const matrix=new Matrix4().multiplyMatrices(inverse,n.matrixWorld),offset=new Vector3(...(w.geometry.local_position_m??[0,0,0])),q=w.geometry.local_orientation_wxyz??[1,0,0,0],rotation=new Quaternion(q[1],q[2],q[3],q[0]);
     const corners=w.geometry.rings.flatMap(r=>r.vertices.map(v=>v.point_m)).flatMap(([x,y])=>[0,w.geometry.depth_m].map(z=>new Vector3(x,y,z).applyQuaternion(rotation).add(offset)));
     for(let i=0;i<g.attributes.position.count;i++){const v=new Vector3().fromBufferAttribute(g.attributes.position,i).applyMatrix4(matrix);assert.ok(Math.min(...corners.map(c=>c.distanceTo(v)))<=1e-5,'Decoded source corner');}
    });
    assert.equal(triangles,w.geometry?.triangle_count??0);if(w.geometry)assert.deepEqual(regions,w.geometry.region_triangle_counts);check.geometry.push({path:name,triangles,regions});
   }
   assert.equal(gltf.animations.length,1);near([gltf.animations[0].duration],[1],1e-6);const mixer=new AnimationMixer(gltf.scene),action=mixer.clipAction(gltf.animations[0]);check.native_observations=[];
   for(const t of [0,.25,.5,.75,1]){action.reset().setLoop(LoopOnce,1).play();action.clampWhenFinished=true;mixer.setTime(t);gltf.scene.updateMatrixWorld(true);const obs={};for(const [name,n]of objects)obs[name]={position:n.getWorldPosition(new Vector3()).toArray(),rotation:n.getWorldQuaternion(new Quaternion()).toArray(),scale:n.getWorldScale(new Vector3()).toArray()};check.native_observations.push(...compare(obs,expected,t));}
   if(['square-hole','two-holes','concave-outer','slotted-bracket','placed-slot','generated','agent-repaired'].includes(item.name)){const dir=path.join(output,item.name);await mkdir(dir);check.browser=await browserCheck(data,expected,dir);}
   check.status='passed';
  }
  report.status='passed';
 }catch(error){report.status='failed';report.failure={type:error.name,message:error.message,stack:error.stack};process.exitCode=1;}
 report.finished_utc=new Date().toISOString();await writeFile(path.join(output,'summary.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,artifacts:report.artifacts.length,failure:report.failure}));
}
await main();
