// Offline WebGL evidence for exact Agent/0.4 source-to-GLB/0.4 artifacts.
import assert from 'node:assert/strict';
import {mkdir,readFile,readdir,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {build} from 'esbuild';
import {chromium} from 'playwright';
import {root,sha256,loadCase,expectedPose,comparePose,vectorError} from './verify_impulse_native.mjs';

const args=process.argv.slice(2),fixtureNames=[];
let demoDir,outputDir;
for(let i=0;i<args.length;i++) {
  if(args[i]==='--help') {
    console.log('Usage: node tools/verify_impulse_viewer.mjs --demo-dir DIR --output-dir DIR [--fixture Pxx ...]');
    process.exit(0);
  }
  const option=args[i];assert.ok(['--demo-dir','--output-dir','--fixture'].includes(option),`Unknown option ${option}`);
  assert.ok(args[i+1]&&!args[i+1].startsWith('--'),`${option} requires a value`);
  const value=args[++i];
  if(option==='--fixture')fixtureNames.push(value);
  else if(option==='--demo-dir')demoDir=path.resolve(value);
  else outputDir=path.resolve(value);
}
assert.ok(demoDir&&outputDir,'Both --demo-dir and --output-dir are required');
if(!fixtureNames.length)fixtureNames.push('P02','P04','P08','P11');
assert.equal(new Set(fixtureNames).size,fixtureNames.length,'Each browser fixture must be selected once');
assert.ok(fixtureNames.length<=9);
for(const name of fixtureNames)assert.ok(['P01','P02','P03','P04','P07','P08','P09','P10','P11'].includes(name),'Unknown delivery fixture '+name);
await mkdir(outputDir,{recursive:true});
assert.deepEqual(await readdir(outputDir),[],'Use an empty output directory so captures cannot mix runs');
const workflowBytes=await readFile(path.join(demoDir,'workflow.json'));
const buildBytes=await readFile(path.join(demoDir,'native-build.json'));
const workflow=JSON.parse(workflowBytes),nativeBuild=JSON.parse(buildBytes);
assert.equal(workflow.schema_version,'ontokin.impulse-agent-demo/0.1');assert.equal(workflow.status,'passed');
assert.equal(nativeBuild.schema_version,'ontokin.impulse-native-build/0.1');assert.equal(nativeBuild.status,'built');
assert.deepEqual(workflow.implementation,nativeBuild.implementation);
const acceptanceHash=sha256(await readFile(path.join(root,'docs/language-design/impulse-v0.1/acceptance.json')));
assert.equal(workflow.acceptance_manifest_sha256,acceptanceHash);assert.equal(nativeBuild.acceptance_manifest_sha256,acceptanceHash);
const cases=await Promise.all(fixtureNames.map(name=>loadCase(path.join(demoDir,name))));
for(const [index,state] of cases.entries()) {
  assert.equal(state.oracle.fixture,fixtureNames[index],'The requested fixture directory contains another source case');
  assert.deepEqual(state.reference.implementation,workflow.implementation,'Browser source and workflow implementation differ');
  assert.equal(state.exportReport.source_code_sha256,workflow.implementation.source_code_sha256.slice(7));
  const artifact=workflow.artifacts.find(a=>a.fixture===state.oracle.fixture);
  assert.ok(artifact,'Source delivery is absent from the retained Agent workflow');
  assert.equal(artifact.program_revision,state.revision);assert.equal(artifact.artifact_sha256,state.artifactHash);
  assert.equal(artifact.byte_length,state.bytes.length);
  const built=nativeBuild.fixtures.find(f=>f.fixture===state.oracle.fixture);
  assert.ok(built);assert.equal(built.program_revision,state.revision);assert.equal(built.artifact_sha256,state.artifactHash);
  assert.equal(built.glb_bytes,state.bytes.length);
}
const tooling=JSON.parse(await readFile(path.join(root,'tools/package.json')));
for(const dependency of ['playwright','three','esbuild'])
  assert.equal(JSON.parse(await readFile(path.join(root,'tools/node_modules',dependency,'package.json'))).version,tooling.devDependencies[dependency]);
const datasets=cases.map(c=>({name:c.oracle.fixture,revision:c.revision,artifact:c.artifactHash,glb:c.bytes.toString('base64')}));
const browserSource=`
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
const datasets=${JSON.stringify(datasets)};
const $=id=>document.getElementById(id),scene=new THREE.Scene();
scene.background=new THREE.Color(0xe7edf2);
const camera=new THREE.PerspectiveCamera(35,1100/750,.001,1000);camera.up.set(0,1,0);
const renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});
renderer.setPixelRatio(1);renderer.setSize(1100,750);renderer.outputColorSpace=THREE.SRGBColorSpace;
$('viewport').appendChild(renderer.domElement);
scene.add(new THREE.AmbientLight(0xffffff,1.2));
for(const [position,intensity] of [[[6,10,8],2.5],[[-5,4,-7],1.8]]) {
 const light=new THREE.DirectionalLight(0xffffff,intensity);light.position.set(...position);scene.add(light);
}
const grid=new THREE.GridHelper(30,30,0x94a5b4,0xc3cfd9);scene.add(grid);
let current=null,content=null,mixer=null,action=null,objects=new Map(),ready=false;
let time=0,playing=false,view='front',fit=null,last=performance.now();
function seek(value) {
 time=Math.max(0,Math.min(2,value));action.reset().play();mixer.setTime(time);content.updateMatrixWorld(true);
 $('timeline').value=String(time);$('time').textContent=time.toFixed(3)+' s';renderer.render(scene,camera);
}
function setView(next) {
 if(next!=='front'&&next!=='side')throw new Error('Unsupported camera view');
 view=next;
 const direction=(next==='side'?new THREE.Vector3(1,.12,0):new THREE.Vector3(.12,.12,1)).normalize();
 camera.position.copy(fit.center).addScaledVector(direction,fit.distance);
 camera.near=Math.max(.001,fit.distance-fit.radius*1.7);camera.far=fit.distance+fit.radius*3;
 camera.up.set(0,1,0);camera.lookAt(fit.center);camera.updateProjectionMatrix();camera.updateMatrixWorld(true);
 renderer.render(scene,camera);
}
function fitMotion() {
 const bounds=new THREE.Box3();
 const sampleTimes=Array.from({length:9},(_,i)=>i/4);
 for(const seconds of sampleTimes){seek(seconds);bounds.union(new THREE.Box3().setFromObject(content));}
 if(bounds.isEmpty())throw new Error('The source scene has no visible geometry');
 const center=bounds.getCenter(new THREE.Vector3()),size=bounds.getSize(new THREE.Vector3());
 const radius=Math.max(size.length()/2,.5);
 const vertical=THREE.MathUtils.degToRad(camera.fov),horizontal=2*Math.atan(Math.tan(vertical/2)*camera.aspect);
 fit={bounds,center,radius,distance:radius/Math.sin(Math.min(vertical,horizontal)/2)*1.15,sampleTimes};
 grid.position.y=bounds.min.y-.02;
 seek(0);setView('front');
}
async function load(name) {
 ready=false;playing=false;$('play').textContent='Play';
 if(content){mixer.stopAllAction();scene.remove(content);}
 current=datasets.find(d=>d.name===name);if(!current)throw new Error('Unknown fixture');
 const raw=Uint8Array.from(atob(current.glb),x=>x.charCodeAt(0));
 const gltf=await new GLTFLoader().parseAsync(raw.buffer,'');
 if(gltf.animations.length!==1)throw new Error('The exact recorded animation is missing');
 content=gltf.scene;scene.add(content);mixer=new THREE.AnimationMixer(content);
 action=mixer.clipAction(gltf.animations[0]);action.setLoop(THREE.LoopOnce,1);action.clampWhenFinished=true;
 objects=new Map();
 for(let i=0;i<gltf.parser.json.nodes.length;i++) {
  const meta=gltf.parser.json.nodes[i].extras?.ontokin;
  if(meta?.kind==='object')objects.set(meta.path,await gltf.parser.getDependency('node',i));
 }
 $('program').textContent=current.name;$('revision').textContent=current.revision;$('artifact').textContent=current.artifact;
 $('materials').textContent=gltf.parser.json.materials.map(m=>m.extras.ontokin.source_region_key+' · metallic '+m.pbrMetallicRoughness.metallicFactor+' · roughness '+m.pbrMetallicRoughness.roughnessFactor).join(' | ');
 $('fixture').value=name;fitMotion();ready=true;
}
for(const data of datasets){const option=document.createElement('option');option.value=data.name;option.textContent=data.name;$('fixture').appendChild(option);}
$('fixture').onchange=event=>load(event.target.value);
$('timeline').oninput=event=>{playing=false;$('play').textContent='Play';seek(Number(event.target.value));};
$('front').onclick=()=>setView('front');$('side').onclick=()=>setView('side');
$('play').onclick=()=>{if(time>=2)seek(0);playing=!playing;$('play').textContent=playing?'Pause':'Play';};
function frame(now){requestAnimationFrame(frame);const elapsed=Math.min((now-last)/1000,.1);last=now;
 if(ready&&playing){seek(time+elapsed);if(time>=2){playing=false;$('play').textContent='Play';}}
 if(ready)renderer.render(scene,camera);
}
requestAnimationFrame(frame);
window.impulseViewer={load,get ready(){return ready;},get state(){
 const entries=[...objects.entries()].map(([name,node])=>{
  const probes=[],primitives=[];
  node.traverse(child=>{if(child.isMesh){
   const positions=child.geometry.attributes.position,index=child.geometry.index,count=index?index.count:positions.count;
   for(const offset of [...new Set([0,Math.floor(count/2),count-1])]){
    const local=new THREE.Vector3().fromBufferAttribute(positions,index?index.getX(offset):offset);
    probes.push({local_m:local.toArray(),world_m:local.clone().applyMatrix4(child.matrixWorld).toArray()});
   }
   const material=child.material;
   primitives.push({region:material.userData.ontokin.source_region_key,rgba:[...material.color.toArray(),material.opacity],
     metallic:material.metalness,roughness:material.roughness,triangles:count/3});
  }});
  return [name,{position_m:node.getWorldPosition(new THREE.Vector3()).toArray(),
   orientation_xyzw:node.getWorldQuaternion(new THREE.Quaternion()).toArray(),probes,primitives}];
 });
 const cameraState={position_m:camera.position.toArray(),orientation_xyzw:camera.quaternion.toArray(),
  target_m:fit.center.toArray(),up:camera.up.toArray(),fov_degrees:camera.fov,aspect:camera.aspect,
  near_m:camera.near,far_m:camera.far,bounds_min_m:fit.bounds.min.toArray(),bounds_max_m:fit.bounds.max.toArray(),
  fit_sample_times_seconds:fit.sampleTimes,fit_policy:'union_of_actual_geometry_over_quarter_seconds/0.1'};
 return {fixture:current.name,time,playing,view,revision:current.revision,artifact:current.artifact,
  objects:Object.fromEntries(entries),camera:cameraState,render:{calls:renderer.info.render.calls,triangles:renderer.info.render.triangles}};
}};
load(datasets[0].name);
`;
const compiled=await build({stdin:{contents:browserSource,resolveDir:path.join(root,'tools'),sourcefile:'impulse-viewer-harness.js'},
  bundle:true,minify:true,format:'esm',target:['es2020'],write:false});
const html=`<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>OntoKin source impulse validation</title><style>
*{box-sizing:border-box}body{margin:0;background:#f3f6f8;color:#243549;font:16px system-ui,sans-serif}main{width:1160px;margin:22px auto;background:white;border:1px solid #d4dde5;border-radius:12px;padding:24px}
h1{font-size:25px;margin:0 0 6px}p{margin:5px 0 12px}.subtitle{color:#526477}#viewport{margin:18px 0;border-radius:7px;overflow:hidden;width:1100px;height:750px}
.controls{display:flex;gap:12px;align-items:center}button,select{font:inherit;padding:8px 14px;background:white;border:1px solid #a6b6c4;border-radius:5px}input{flex:1}code{font-size:11px;overflow-wrap:anywhere}dt{font-weight:600;font-size:12px;color:#526477}dd{margin:2px 0 8px}#materials{font-size:12px;color:#526477}
</style><main><h1>Source impulses in OntoKin</h1><p class="subtitle">Native surfaces, regional materials and recorded source-driven rigid motion</p>
<div class="controls"><label for="fixture">Source fixture</label><select id="fixture"></select><button id="front">Front view</button><button id="side">Side view</button><strong id="program"></strong></div>
<div id="viewport"></div><div class="controls"><button id="play">Play</button><input id="timeline" aria-label="Animation time" type="range" min="0" max="2" step=".001" value="0"><output id="time">0.000 s</output></div>
<p id="materials"></p><dl><dt>Accepted program revision</dt><dd><code id="revision"></code></dd><dt>Retrieved GLB SHA-256</dt><dd><code id="artifact"></code></dd></dl>
<p class="subtitle">Y-up cameras use the same framing throughout the two-second recording. Numerical checks and exact source identities accompany these captures.</p>
</main><script type="module">${compiled.outputFiles[0].text}</script></html>`;
const harnessFile='impulse-viewer.html',harness=path.join(outputDir,harnessFile);
await writeFile(harness,html);
const report={schema_version:'ontokin.impulse-browser-validation/0.1',status:'running',
  generated_at_utc:new Date().toISOString(),implementation:workflow.implementation,
  acceptance_manifest_sha256:acceptanceHash,workflow_sha256:sha256(workflowBytes),native_build_sha256:sha256(buildBytes),
  harness_file:harnessFile,harness_sha256:sha256(Buffer.from(html)),
  verifier_sha256:sha256(await readFile(fileURLToPath(import.meta.url))),
  native_verifier_sha256:sha256(await readFile(path.join(root,'tools/verify_impulse_native.mjs'))),
  surface_verifier_sha256:sha256(await readFile(path.join(root,'tools/verify_surface_native.mjs'))),
  tooling_lock_sha256:sha256(await readFile(path.join(root,'tools/package-lock.json'))),
  source_fixtures:cases.map(c=>({fixture:c.oracle.fixture,program_revision:c.revision,artifact_sha256:c.artifactHash,
    provenance:c.provenance,exporter_source_code_sha256:c.exportReport.source_code_sha256})),
  environment:{node:process.version,platform:process.platform,architecture:process.arch,
    playwright:tooling.devDependencies.playwright,three:tooling.devDependencies.three,esbuild:tooling.devDependencies.esbuild,
    renderer:'Headless Chromium WebGL2 / ANGLE SwiftShader',camera_up:[0,1,0],viewport:{width:1220,height:1160},device_scale_factor:1},
  samples:[],captures:[],playback:[],page_errors:[],console_errors:[],failed_requests:[],network_requests:[],
  limits:['Screenshots still require identified visual review; a numerical report alone cannot complete D02.',
    'The independent native decoder verifies exact geometry, winding, materials and influence metadata of these same artifacts.',
    'This offline harness plays recorded GLB transforms; it does not simulate a live impulse or physics engine.',
    'Current inherited regression/conformance and identified CI remain separate mandatory release gates.']};

function validateReadback(state,observed,time,label) {
  assert.equal(observed.fixture,state.oracle.fixture);assert.equal(observed.revision,state.revision);assert.equal(observed.artifact,state.artifactHash);
  assert.ok(Math.abs(observed.time-time)<=state.tolerances.time_seconds,label+' time');
  assert.deepEqual(observed.camera.up,[0,1,0]);assert.deepEqual(observed.camera.fit_sample_times_seconds,Array.from({length:9},(_,i)=>i/4));
  assert.equal(observed.camera.fit_policy,'union_of_actual_geometry_over_quarter_seconds/0.1');
  assert.ok(observed.camera.near_m>0&&observed.camera.far_m>observed.camera.near_m);
  const wanted=[...state.oracle.shapes,...state.oracle.empty_objects],objects={};
  assert.deepEqual(Object.keys(observed.objects).sort(),wanted.map(o=>o.path).sort());
  assert.equal(observed.render.triangles,state.oracle.shapes.reduce((n,s)=>n+s.expected.triangles,0),'Every native triangle is rendered');
  for(const object of wanted) {
    const actual=observed.objects[object.path],expected=expectedPose(object,time);
    const errors=comparePose(actual,expected,state.tolerances,object.path+' '+label);
    for(const probe of actual.probes) {
      const [qx,qy,qz,qw]=expected.orientation_xyzw,[x,y,z]=probe.local_m;
      const tx=2*(qy*z-qz*y),ty=2*(qz*x-qx*z),tz=2*(qx*y-qy*x);
      const world=[x+qw*tx+qy*tz-qz*ty,y+qw*ty+qz*tx-qx*tz,z+qw*tz+qx*ty-qy*tx].map((v,i)=>v+expected.position_m[i]);
      vectorError(probe.world_m,world,state.tolerances.position_m,'Browser world surface point');
    }
    if(object.materials) {
      assert.deepEqual(actual.primitives.map(p=>p.region).sort(),Object.keys(object.materials).sort());
      for(const material of actual.primitives) {
        const wantedMaterial=object.materials[material.region];
        vectorError(material.rgba,wantedMaterial.rgba,1e-12,'Actual browser PBR color');
        assert.equal(material.metallic,wantedMaterial.metallic);assert.equal(material.roughness,wantedMaterial.roughness);
        assert.equal(material.triangles,object.expected.triangles_per_region[material.region]);
      }
    } else assert.deepEqual(actual.primitives,[],'An empty carrier acquired visible geometry');
    objects[object.path]={...actual,...errors};
  }
  return objects;
}

let browser;
try {
  browser=await chromium.launch({headless:true,args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  report.browser=await browser.version();
  const page=await browser.newPage({viewport:{width:1220,height:1160},deviceScaleFactor:1,reducedMotion:'reduce'});
  page.on('pageerror',e=>report.page_errors.push(e.message));
  page.on('console',message=>{if(message.type()==='error')report.console_errors.push(message.text());});
  page.on('request',r=>{if(/^https?:/.test(r.url()))report.network_requests.push(r.url());});
  page.on('requestfailed',r=>report.failed_requests.push({url:r.url(),error:r.failure()?.errorText}));
  await page.route(/^https?:\/\//,route=>route.abort());
  await page.goto(pathToFileURL(harness).href);await page.waitForFunction(()=>window.impulseViewer?.ready);
  for(const state of cases) {
    await page.selectOption('#fixture',state.oracle.fixture);
    await page.waitForFunction(name=>window.impulseViewer.ready&&window.impulseViewer.state.fixture===name,state.oracle.fixture);
    const initial=await page.evaluate(()=>window.impulseViewer.state);
    assert.equal(initial.time,0);assert.equal(initial.view,'front');assert.equal(initial.playing,false);
    for(const sample of state.reference.samples) {
      const time=Number(sample.time_seconds);
      await page.locator('#timeline').fill(String(time));
      const observed=await page.evaluate(()=>window.impulseViewer.state);
      assert.equal(observed.playing,false);assert.deepEqual(observed.camera,initial.camera,'Seeking must not refit the camera');
      const objects=validateReadback(state,observed,time,'browser at '+sample.time_seconds+' '+sample.side);
      for(const [name,actual] of Object.entries(objects)) {
        const reference=sample.objects[name],q=reference.orientation_wxyz;
        const errors=comparePose(actual,{position_m:reference.position_m,orientation_xyzw:[q[1],q[2],q[3],q[0]]},state.tolerances,name+' actual Agent state');
        actual.agent_position_error_m=errors.position_error_m;actual.agent_rotation_error_rad=errors.rotation_error_rad;
      }
      report.samples.push({fixture:state.oracle.fixture,time_seconds:sample.time_seconds,side:sample.side,
                          camera:observed.camera,objects});
    }
    let frontCamera;
    for(const capture of [{view:'front',cameraView:'front',time:0},{view:'side',cameraView:'side',time:0},{view:'animated',cameraView:'front',time:1.5}]) {
      await page.locator('#timeline').fill(String(capture.time));await page.click('#'+capture.cameraView);
      await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
      const observed=await page.evaluate(()=>window.impulseViewer.state);
      assert.equal(observed.view,capture.cameraView);assert.equal(observed.playing,false);
      if(capture.view==='front')frontCamera=observed.camera;
      if(capture.view==='animated')assert.deepEqual(observed.camera,frontCamera,'Animated capture must retain the exact original front camera');
      const objects=validateReadback(state,observed,capture.time,capture.view+' capture');
      const filename=state.oracle.fixture+'-'+capture.view+'.png',file=path.join(outputDir,filename);
      await page.screenshot({path:file,fullPage:true});
      report.captures.push({file:filename,sha256:sha256(await readFile(file)),fixture:state.oracle.fixture,
        view:capture.view,camera_view:capture.cameraView,time_seconds:capture.time,
        program_revision:state.revision,artifact_sha256:state.artifactHash,camera:observed.camera,objects});
    }
    await page.locator('#timeline').fill('1.05');await page.click('#play');
    await page.waitForFunction(()=>window.impulseViewer.state.playing&&window.impulseViewer.state.time>1.05);
    await page.click('#play');const paused=await page.evaluate(()=>window.impulseViewer.state);
    assert.ok(paused.time>1.05&&paused.time<2);assert.equal(paused.playing,false);
    const objects=validateReadback(state,paused,paused.time,'paused playback');
    const later=await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve(window.impulseViewer.state)))));
    assert.equal(later.time,paused.time);assert.deepEqual(later.objects,paused.objects);assert.deepEqual(later.camera,paused.camera);
    report.playback.push({fixture:state.oracle.fixture,started_at_seconds:1.05,paused_at_seconds:paused.time,
                         stable_across_frames:true,camera:paused.camera,objects});
  }
  report.webgl=await page.evaluate(()=>{const gl=document.querySelector('canvas').getContext('webgl2');if(!gl)return null;
    const debug=gl.getExtension('WEBGL_debug_renderer_info');return {version:gl.getParameter(gl.VERSION),renderer:gl.getParameter(gl.RENDERER),
      unmasked_renderer:debug?gl.getParameter(debug.UNMASKED_RENDERER_WEBGL):null};});
  assert.ok(report.webgl);for(const key of ['page_errors','console_errors','failed_requests','network_requests'])assert.deepEqual(report[key],[],key);
  report.world_pose_comparisons=report.samples.reduce((n,s)=>n+Object.keys(s.objects).length,0);
  report.capture_pose_comparisons=report.captures.reduce((n,s)=>n+Object.keys(s.objects).length,0);
  report.status='passed';
} catch(error) {
  report.status='failed';report.failure={name:error.name,message:error.message};throw error;
} finally {
  if(browser)await browser.close();
  await writeFile(path.join(outputDir,'browser-validation.json'),JSON.stringify(report,null,2)+'\n');
}
console.log(JSON.stringify({status:report.status,fixtures:cases.length,world_pose_comparisons:report.world_pose_comparisons,
  screenshots:report.captures.length,browser:report.browser,output_dir:outputDir},null,2));
