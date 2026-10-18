// Offline WebGL evidence for exact native .ok / GLB/0.3 source identities.
import assert from 'node:assert/strict';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {build} from 'esbuild';
import {chromium} from 'playwright';
import {root,sha256,loadCase,expectedPose,comparePose,vectorError} from './verify_surface_native.mjs';

const args=process.argv.slice(2);let demoDir,outputDir;
for(let i=0;i<args.length;i++) {
  if(args[i]==='--help') {console.log('Usage: node tools/verify_surface_viewer.mjs --demo-dir DIR --output-dir DIR');process.exit(0);}
  assert.ok(['--demo-dir','--output-dir'].includes(args[i]));assert.ok(args[i+1]);
  const option=args[i],value=path.resolve(args[++i]);if(option==='--demo-dir')demoDir=value;else outputDir=value;
}
assert.ok(demoDir&&outputDir,'Both --demo-dir and --output-dir are required');
await mkdir(outputDir,{recursive:true});
const cases=await Promise.all(['studio','rotated-animation'].map(name=>loadCase(path.join(demoDir,name))));
const tooling=JSON.parse(await readFile(path.join(root,'tools/package.json')));
for(const dependency of ['playwright','three','esbuild'])
  assert.equal(JSON.parse(await readFile(path.join(root,'tools/node_modules',dependency,'package.json'))).version,tooling.devDependencies[dependency]);
const datasets=cases.map(c=>({name:c.oracle.fixture,revision:c.revision,artifact:c.artifactHash,glb:c.bytes.toString('base64')}));
const browserSource=`
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
const datasets=${JSON.stringify(datasets)};
const $=id=>document.getElementById(id),scene=new THREE.Scene();
scene.background=new THREE.Color(0xe5e9ed);
const camera=new THREE.PerspectiveCamera(35,1,.001,10000);camera.up.set(0,0,1);
const renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});
renderer.setPixelRatio(1);renderer.setSize(1100,750);renderer.outputColorSpace=THREE.SRGBColorSpace;
$('viewport').appendChild(renderer.domElement);camera.aspect=1100/750;camera.updateProjectionMatrix();
scene.add(new THREE.AmbientLight(0xffffff,1.3));
for(const [position,intensity] of [[[5,-5,8],3],[[-4,3,5],2]]) {
 const light=new THREE.DirectionalLight(0xffffff,intensity);light.position.set(...position);scene.add(light);
}
const grid=new THREE.GridHelper(20,20,0xa8b1bb,0xcad1d8);grid.rotation.x=Math.PI/2;scene.add(grid);
let current=null,content=null,mixer=null,action=null,objects=new Map(),ready=false,time=0,playing=false,view='front';
let last=performance.now();
function seek(value) {
 time=Math.max(0,Math.min(2,value));action.reset().play();mixer.setTime(time);content.updateMatrixWorld(true);
 $('timeline').value=String(time);$('time').textContent=time.toFixed(3)+' s';
 renderer.render(scene,camera);
}
function setView(next) {
 view=next;const bounds=new THREE.Box3().setFromObject(content),center=bounds.getCenter(new THREE.Vector3());
 const size=bounds.getSize(new THREE.Vector3()),distance=Math.max(size.length(),1)*1.8;
 camera.position.copy(center).add(next==='side'?new THREE.Vector3(distance,0,distance*.12):new THREE.Vector3(0,-distance,distance*.12));
 camera.near=Math.max(distance/1000,.0001);camera.far=Math.max(distance*100,100);camera.lookAt(center);camera.updateProjectionMatrix();
 renderer.render(scene,camera);
}
async function load(name) {
 ready=false;playing=false;$('play').textContent='Play';if(content)scene.remove(content);
 current=datasets.find(d=>d.name===name);const raw=Uint8Array.from(atob(current.glb),x=>x.charCodeAt(0));
 const gltf=await new GLTFLoader().parseAsync(raw.buffer,'');content=gltf.scene;scene.add(content);
 mixer=new THREE.AnimationMixer(content);action=mixer.clipAction(gltf.animations[0]);action.setLoop(THREE.LoopOnce,1);action.clampWhenFinished=true;
 objects=new Map();
 for(let i=0;i<gltf.parser.json.nodes.length;i++) {
  const meta=gltf.parser.json.nodes[i].extras?.ontokin;
  if(meta?.kind==='object')objects.set(meta.path,await gltf.parser.getDependency('node',i));
 }
 $('program').textContent=current.name;$('revision').textContent=current.revision;$('artifact').textContent=current.artifact;
 $('materials').textContent=gltf.parser.json.materials.map(m=>m.extras.ontokin.source_region_key+' · metallic '+m.pbrMetallicRoughness.metallicFactor+' · roughness '+m.pbrMetallicRoughness.roughnessFactor).join(' | ');
 $('fixture').value=name;seek(0);setView('front');ready=true;
}
for(const data of datasets) {const option=document.createElement('option');option.value=data.name;option.textContent=data.name;$('fixture').appendChild(option);}
$('fixture').onchange=event=>load(event.target.value);
$('timeline').oninput=event=>{playing=false;$('play').textContent='Play';seek(Number(event.target.value));};
$('front').onclick=()=>setView('front');$('side').onclick=()=>setView('side');
$('play').onclick=()=>{if(time>=2)seek(0);playing=!playing;$('play').textContent=playing?'Pause':'Play';};
function frame(now) {requestAnimationFrame(frame);const elapsed=Math.min((now-last)/1000,.1);last=now;
 if(ready&&playing){seek(time+elapsed);if(time>=2){playing=false;$('play').textContent='Play';}}
 if(ready)renderer.render(scene,camera);
}
requestAnimationFrame(frame);
window.surfaceViewer={load,get ready(){return ready;},get state(){
 const entries=[...objects.entries()].map(([name,node])=>{
  const probes=[];node.traverse(child=>{if(child.isMesh){const index=child.geometry.index.getX(0);
   const local=new THREE.Vector3().fromBufferAttribute(child.geometry.attributes.position,index);
   probes.push({local_m:local.toArray(),world_m:local.clone().applyMatrix4(child.matrixWorld).toArray()});}});
  return [name,{position_m:node.getWorldPosition(new THREE.Vector3()).toArray(),orientation_xyzw:node.getWorldQuaternion(new THREE.Quaternion()).toArray(),probes}];
 });return {fixture:current.name,time,playing,view,revision:current.revision,artifact:current.artifact,objects:Object.fromEntries(entries)};
}};
load(datasets[0].name);
`;
const compiled=await build({stdin:{contents:browserSource,resolveDir:path.join(root,'tools'),sourcefile:'surface-viewer-harness.js'},
  bundle:true,minify:true,format:'esm',target:['es2020'],write:false});
const html=`<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>OntoKin native surface validation</title><style>
*{box-sizing:border-box}body{margin:0;background:#f4f6f8;color:#233041;font:16px system-ui,sans-serif}main{width:1160px;margin:22px auto;background:white;border:1px solid #d6dde4;border-radius:12px;padding:24px}
h1{font-size:25px;margin:0 0 6px}p{margin:5px 0 12px}.subtitle{color:#526175}#viewport{margin:18px 0;border-radius:7px;overflow:hidden;width:1100px;height:750px}
.controls{display:flex;gap:12px;align-items:center}button,select{font:inherit;padding:8px 14px;background:#fff;border:1px solid #aab7c4;border-radius:5px}input{flex:1}code{font-size:11px;overflow-wrap:anywhere}dt{font-weight:600;font-size:12px;color:#526175}dd{margin:2px 0 8px}#materials{font-size:12px;color:#526175}
</style><main><h1>Native OntoKin surfaces</h1><p class="subtitle">Compiled .ok geometry, regional materials, and recorded rigid animation</p>
<div class="controls"><label for="fixture">Source fixture</label><select id="fixture"></select><button id="front">Front view</button><button id="side">Side view</button><strong id="program"></strong></div>
<div id="viewport"></div><div class="controls"><button id="play">Play</button><input id="timeline" aria-label="Animation time" type="range" min="0" max="2" step=".001" value="0"><output id="time">0.000 s</output></div>
<p id="materials"></p><dl><dt>Program revision</dt><dd><code id="revision"></code></dd><dt>GLB SHA-256</dt><dd><code id="artifact"></code></dd></dl>
<p class="subtitle">This capture records the identified artifact in Three.js/WebGL2. Numerical and source checks are retained in the accompanying validation reports.</p>
</main><script type="module">${compiled.outputFiles[0].text}</script></html>`;
const harness=path.join(outputDir,'surface-viewer.html');await writeFile(harness,html);
const report={schema_version:'ontokin.surface-native-browser-validation/0.1',status:'running',
  generated_at_utc:new Date().toISOString(),harness_sha256:sha256(Buffer.from(html)),
  verifier_sha256:sha256(await readFile(fileURLToPath(import.meta.url))),
  tooling_lock_sha256:sha256(await readFile(path.join(root,'tools/package-lock.json'))),
  source_fixtures:cases.map(c=>({fixture:c.oracle.fixture,program_revision:c.revision,artifact_sha256:c.artifactHash,
    provenance:c.provenance,exporter_source_code_sha256:c.exportReport.source_code_sha256})),
  environment:{node:process.version,platform:process.platform,architecture:process.arch,
    playwright:tooling.devDependencies.playwright,three:tooling.devDependencies.three,esbuild:tooling.devDependencies.esbuild,
    renderer:'Headless Chromium WebGL2 / ANGLE SwiftShader'},
  samples:[],captures:[],playback:[],page_errors:[],console_errors:[],failed_requests:[],network_requests:[],
  limits:['The two captured source programs establish bounded native destination evidence, not complete M01--M12 acceptance.',
    'The harness is an identified offline validation destination, not a replacement of the existing production viewer.',
    'Screenshots require human or visual review; numerical topology/material checks are in verify_surface_native.mjs.',
    'No Blender, external engine, deformation or live physics support is claimed.']};
let browser;
try {
  browser=await chromium.launch({headless:true,args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  report.browser=await browser.version();
  const page=await browser.newPage({viewport:{width:1220,height:1160},deviceScaleFactor:1,reducedMotion:'reduce'});
  page.on('pageerror',e=>report.page_errors.push(e.message));
  page.on('console',message=>{if(message.type()==='error')report.console_errors.push(message.text());});
  page.on('request',r=>{if(/^https?:/.test(r.url()))report.network_requests.push(r.url());});
  page.on('requestfailed',r=>report.failed_requests.push({url:r.url(),error:r.failure()?.errorText}));
  await page.route(/^https?:\/\//,route=>route.abort());await page.goto(pathToFileURL(harness).href);
  await page.waitForFunction(()=>window.surfaceViewer?.ready);
  for(const state of cases) {
    await page.selectOption('#fixture',state.oracle.fixture);
    await page.waitForFunction(name=>window.surfaceViewer.ready&&window.surfaceViewer.state.fixture===name,state.oracle.fixture);
    assert.equal(await page.locator('#revision').textContent(),state.revision);assert.equal(await page.locator('#artifact').textContent(),state.artifactHash);
    for(const sample of state.reference.samples) {
      const time=Number(sample.time_seconds);await page.locator('#timeline').fill(String(time));
      const observed=await page.evaluate(()=>window.surfaceViewer.state);
      assert.equal(observed.playing,false);assert.ok(Math.abs(observed.time-time)<=state.tolerances.time_seconds);
      assert.equal(observed.revision,state.revision);assert.equal(observed.artifact,state.artifactHash);
      const wanted=[...state.oracle.shapes,...state.oracle.empty_objects??[]];
      assert.deepEqual(Object.keys(observed.objects).sort(),wanted.map(o=>o.path).sort());
      const objects={};
      for(const object of wanted) {
        const actual=observed.objects[object.path],expected=expectedPose(object,time);
        const errors=comparePose(actual,expected,state.tolerances,object.path+' browser at '+time);
        // Use the carrier pose to independently rotate each decoded local
        // probe; copied primitive transforms would show a disagreement.
        for(const probe of actual.probes) {
          const [qx,qy,qz,qw]=expected.orientation_xyzw,[x,y,z]=probe.local_m;
          const tx=2*(qy*z-qz*y),ty=2*(qz*x-qx*z),tz=2*(qx*y-qy*x);
          const world=[x+qw*tx+qy*tz-qz*ty,y+qw*ty+qz*tx-qx*tz,z+qw*tz+qx*ty-qy*tx]
            .map((v,i)=>v+expected.position_m[i]);
          vectorError(probe.world_m,world,state.tolerances.position_m,'Browser world surface point');
        }
        objects[object.path]={...actual,...errors};
      }
      report.samples.push({fixture:state.oracle.fixture,time_seconds:time,objects});
    }
    for(const capture of [{name:'front',view:'front',time:0},{name:'side',view:'side',time:0},{name:'animated',view:'front',time:1.5}]) {
      await page.locator('#timeline').fill(String(capture.time));await page.click('#'+capture.view);
      await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
      const filename=state.oracle.fixture+'-'+capture.name+'.png',file=path.join(outputDir,filename);
      await page.screenshot({path:file,fullPage:true});
      report.captures.push({file:filename,sha256:sha256(await readFile(file)),fixture:state.oracle.fixture,
        view:capture.view,time_seconds:capture.time,program_revision:state.revision,artifact_sha256:state.artifactHash});
    }
    await page.locator('#timeline').fill('0.5');await page.click('#play');
    await page.waitForFunction(()=>window.surfaceViewer.state.playing&&window.surfaceViewer.state.time>.5);
    await page.click('#play');const paused=await page.evaluate(()=>window.surfaceViewer.state);
    assert.ok(paused.time>.5&&paused.time<2);assert.equal(paused.playing,false);
    const later=await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve(window.surfaceViewer.state)))));
    assert.equal(later.time,paused.time);assert.deepEqual(later.objects,paused.objects);
    report.playback.push({fixture:state.oracle.fixture,started_at_seconds:.5,paused_at_seconds:paused.time,stable_across_frames:true});
  }
  report.webgl=await page.evaluate(()=>{const gl=document.querySelector('canvas').getContext('webgl2');if(!gl)return null;
    const debug=gl.getExtension('WEBGL_debug_renderer_info');return {version:gl.getParameter(gl.VERSION),renderer:gl.getParameter(gl.RENDERER),
      unmasked_renderer:debug?gl.getParameter(debug.UNMASKED_RENDERER_WEBGL):null};});
  assert.ok(report.webgl);for(const key of ['page_errors','console_errors','failed_requests','network_requests'])assert.deepEqual(report[key],[],key);
  report.world_pose_comparisons=report.samples.reduce((n,s)=>n+Object.keys(s.objects).length,0);report.status='passed';
} catch(error) {report.status='failed';report.failure={name:error.name,message:error.message};throw error;}
finally {if(browser)await browser.close();await writeFile(path.join(outputDir,'browser-results.json'),JSON.stringify(report,null,2)+'\n');}
console.log(JSON.stringify({status:report.status,fixtures:cases.length,world_pose_comparisons:report.world_pose_comparisons,
  screenshots:report.captures.length,browser:report.browser,output_dir:outputDir},null,2));
