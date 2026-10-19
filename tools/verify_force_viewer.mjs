// Offline WebGL evidence for actual source-built recorded GLB/0.5 artifacts.
// The browser receives GLB bytes and a timeline horizon, never host geometry or
// trajectories. Source and analytical expectations are used only for readback.
import assert from 'node:assert/strict';
import {mkdir,readFile,readdir,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {build} from 'esbuild';
import {chromium} from 'playwright';
import {root,sha256,loadCase,loadWorkflow,expectedPose,comparePose,vectorError,deliveryCases,agentDeliveryCases} from './verify_force_native.mjs';

const args=process.argv.slice(2),fixtureNames=[];
let demoDir,outputDir,agentAudit,agentWorkflow=false;
for(let i=0;i<args.length;i++) {
  if(args[i]==='--help') {
    console.log('Usage: node tools/verify_force_viewer.mjs --demo-dir DIR --output-dir DIR [--fixture NAME ...] [--agent-workflow --agent-audit FILE]');
    process.exit(0);
  }
  const option=args[i];
  if(option==='--agent-workflow'){assert.equal(agentWorkflow,false);agentWorkflow=true;continue;}
  assert.ok(['--demo-dir','--output-dir','--fixture','--agent-audit'].includes(option),`Unknown option ${option}`);
  assert.ok(args[i+1]&&!args[i+1].startsWith('--'),`${option} requires a value`);
  const value=args[++i];
  if(option==='--fixture')fixtureNames.push(value);
  else if(option==='--demo-dir') {assert.equal(demoDir,undefined,'Duplicate --demo-dir');demoDir=path.resolve(value);}
  else if(option==='--agent-audit') {assert.equal(agentAudit,undefined,'Duplicate --agent-audit');agentAudit=path.resolve(value);}
  else {assert.equal(outputDir,undefined,'Duplicate --output-dir');outputDir=path.resolve(value);}
}
assert.ok(demoDir&&outputDir,'Both --demo-dir and --output-dir are required');
if(!fixtureNames.length)fixtureNames.push(...(agentWorkflow?agentDeliveryCases:['P02','P07','P09','P10','P11','P12','P13','held-out-oblique','held-out-spin']));
assert.equal(new Set(fixtureNames).size,fixtureNames.length,'Each browser fixture must be selected once');
const availableCases=agentWorkflow?agentDeliveryCases:deliveryCases;
assert.ok(fixtureNames.length<=availableCases.length);
for(const name of fixtureNames)assert.ok(availableCases.includes(name),'Unknown delivery fixture '+name);
await mkdir(outputDir,{recursive:true});
assert.deepEqual(await readdir(outputDir),[],'Use an empty output directory so captures cannot mix runs');

const loaded=await loadWorkflow(demoDir,{agentWorkflow,agentAudit});
const {bytes:workflowBytes,workflow,fixtures}=loaded;
assert.match(loaded.gitIdentity.head,/^[0-9a-f]{40}$/);assert.match(loaded.gitIdentity.tree,/^[0-9a-f]{40}$/);
const acceptanceHash=sha256(await readFile(path.join(root,'docs/language-design/force-v0.1/acceptance.json')));
const cases=await Promise.all(fixtureNames.map(name=>{
  const item=fixtures.find(f=>f.fixture===name);assert.ok(item,'Requested fixture is absent from the recorded workflow');
  return loadCase(path.join(demoDir,item.directory));
}));
for(const [index,state] of cases.entries()) {
  assert.equal(state.oracle.fixture,fixtureNames[index],'The requested directory contains another source case');
  assert.deepEqual(state.reference.implementation,workflow.implementation,'Browser source and workflow implementation differ');
  assert.deepEqual(state.oracle.fixture_inputs,loaded.fixtureInputs,'Browser adopted fixture inputs differ');
  assert.match(workflow.implementation.source_code_sha256,/^sha256:[0-9a-f]{64}$/);
  assert.equal(state.exportReport.source_code_sha256,workflow.implementation.source_code_sha256.slice(7));
  const built=fixtures.find(f=>f.fixture===state.oracle.fixture);
  assert.ok(built,'Source delivery is absent from the retained component workflow');
  assert.equal(built.directory,(agentWorkflow?'cases/':'')+state.oracle.fixture);assert.equal(built.program_revision,state.revision);
  assert.equal(built.artifact_sha256,state.artifactHash);assert.equal(built.glb_bytes,state.bytes.length);
  assert.equal(built.end_seconds,state.oracle.end_seconds);assert.equal(built.fixed_samples,state.reference.samples.length);
  assert.ok(Number.isFinite(Number(state.oracle.end_seconds))&&Number(state.oracle.end_seconds)>0);
}
const tooling=JSON.parse(await readFile(path.join(root,'tools/package.json')));
for(const dependency of ['playwright','three','esbuild'])
  assert.equal(JSON.parse(await readFile(path.join(root,'tools/node_modules',dependency,'package.json'))).version,tooling.devDependencies[dependency]);
const datasets=cases.map(c=>({name:c.oracle.fixture,revision:c.revision,artifact:c.artifactHash,
  end:Number(c.oracle.end_seconds),end_seconds:c.oracle.end_seconds,glb:c.bytes.toString('base64')}));

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
let current=null,content=null,mixer=null,action=null,objects=new Map(),decoded=null,ready=false;
let time=0,playing=false,view='front',fit=null,last=performance.now();
function seek(value) {
 if(!Number.isFinite(value))throw new Error('Animation time must be finite');
 time=Math.max(0,Math.min(current.end,value));action.reset().play();mixer.setTime(time);content.updateMatrixWorld(true);
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
 const bounds=new THREE.Box3(),sampleTimes=Array.from({length:17},(_,i)=>current.end*i/16);
 for(const seconds of sampleTimes){seek(seconds);bounds.union(new THREE.Box3().setFromObject(content,true));}
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
 if(content){
  mixer.stopAllAction();mixer.uncacheRoot(content);scene.remove(content);
  content.traverse(child=>{if(child.isMesh){child.geometry.dispose();
   for(const material of Array.isArray(child.material)?child.material:[child.material])material.dispose();}});
 }
 current=datasets.find(d=>d.name===name);if(!current)throw new Error('Unknown fixture');
 const raw=Uint8Array.from(atob(current.glb),x=>x.charCodeAt(0));
 const gltf=await new GLTFLoader().parseAsync(raw.buffer,'');
 if(gltf.animations.length!==1)throw new Error('The exact recorded animation is missing');
 const metadata=gltf.parser.json.extras?.ontokin;
 if(metadata?.target_contract!=='ontokin.glb/0.5'||metadata.schema_version!=='0.5')throw new Error('Unexpected decoded delivery contract');
 decoded={target_contract:metadata.target_contract,schema_version:metadata.schema_version,profile:metadata.profile,
  program_revision:metadata.program.revision,source_manifest:metadata.program.manifest,
  animation_duration_seconds:gltf.animations[0].duration};
 content=gltf.scene;scene.add(content);mixer=new THREE.AnimationMixer(content);
 action=mixer.clipAction(gltf.animations[0]);action.setLoop(THREE.LoopOnce,1);action.clampWhenFinished=true;
 objects=new Map();
 for(let i=0;i<gltf.parser.json.nodes.length;i++) {
  const meta=gltf.parser.json.nodes[i].extras?.ontokin;
  if(meta?.kind==='object'){
   if(objects.has(meta.path))throw new Error('Duplicate decoded source object');
   objects.set(meta.path,{node:await gltf.parser.getDependency('node',i),identity:meta});
  }
 }
 $('program').textContent=current.name;$('revision').textContent=decoded.program_revision;$('artifact').textContent=current.artifact;
 $('materials').textContent=gltf.parser.json.materials.map(m=>m.extras.ontokin.source_region_key+' · metallic '+m.pbrMetallicRoughness.metallicFactor+' · roughness '+m.pbrMetallicRoughness.roughnessFactor).join(' | ');
 $('duration').textContent=current.end_seconds+' seconds';$('timeline').max=String(current.end);
 $('fixture').value=name;fitMotion();ready=true;
}
for(const data of datasets){const option=document.createElement('option');option.value=data.name;option.textContent=data.name;$('fixture').appendChild(option);}
$('fixture').onchange=event=>load(event.target.value);
$('timeline').oninput=event=>{playing=false;$('play').textContent='Play';seek(Number(event.target.value));};
$('front').onclick=()=>setView('front');$('side').onclick=()=>setView('side');
$('play').onclick=()=>{if(time>=current.end)seek(0);playing=!playing;$('play').textContent=playing?'Pause':'Play';};
function frame(now){requestAnimationFrame(frame);const elapsed=Math.min((now-last)/1000,.1);last=now;
 if(ready&&playing){seek(time+elapsed);if(time>=current.end){playing=false;$('play').textContent='Play';}}
 if(ready)renderer.render(scene,camera);
}
requestAnimationFrame(frame);
window.forceViewer={load,get ready(){return ready;},get state(){
 const entries=[...objects.entries()].map(([name,{node,identity}])=>{
  const probes=[],primitives=[];
  node.traverse(child=>{if(child.isMesh){
   const positions=child.geometry.attributes.position,index=child.geometry.index,count=index?index.count:positions.count;
   for(const offset of [...new Set([0,Math.floor(count/2),count-1])]){
    const local=new THREE.Vector3().fromBufferAttribute(positions,index?index.getX(offset):offset);
    const world=local.clone().applyMatrix4(child.matrixWorld);
    probes.push({local_m:local.toArray(),world_m:world.toArray(),camera_ndc:world.clone().project(camera).toArray()});
   }
   const material=child.material;
   primitives.push({region:material.userData.ontokin.source_region_key,rgba:[...material.color.toArray(),material.opacity],
     metallic:material.metalness,roughness:material.roughness,triangles:count/3});
  }});
  return [name,{element_id:identity.element_id,kind:identity.kind,path:identity.path,source_mapping:identity.source_mapping,
   position_m:node.getWorldPosition(new THREE.Vector3()).toArray(),
   orientation_xyzw:node.getWorldQuaternion(new THREE.Quaternion()).toArray(),probes,primitives}];
 });
 const cameraState={position_m:camera.position.toArray(),orientation_xyzw:camera.quaternion.toArray(),
  target_m:fit.center.toArray(),up:camera.up.toArray(),fov_degrees:camera.fov,aspect:camera.aspect,
  near_m:camera.near,far_m:camera.far,bounds_min_m:fit.bounds.min.toArray(),bounds_max_m:fit.bounds.max.toArray(),
  fit_sample_times_seconds:fit.sampleTimes,fit_policy:'union_of_actual_geometry_over_16_equal_intervals/0.1'};
 return {fixture:current.name,time,playing,view,revision:current.revision,artifact:current.artifact,
  end_seconds:current.end_seconds,decoded,objects:Object.fromEntries(entries),camera:cameraState,
  render:{calls:renderer.info.render.calls,triangles:renderer.info.render.triangles}};
}};
load(datasets[0].name);
`;
const compiled=await build({stdin:{contents:browserSource,resolveDir:path.join(root,'tools'),sourcefile:'force-viewer-harness.js'},
  bundle:true,minify:true,format:'esm',target:['es2020'],write:false});
const html=`<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>OntoKin source force validation</title><style>
*{box-sizing:border-box}body{margin:0;background:#f3f6f8;color:#243549;font:16px system-ui,sans-serif}main{width:1160px;margin:22px auto;background:white;border:1px solid #d4dde5;border-radius:12px;padding:24px}
h1{font-size:25px;margin:0 0 6px}p{margin:5px 0 12px}.subtitle{color:#526477}#viewport{margin:18px 0;border-radius:7px;overflow:hidden;width:1100px;height:750px}
.controls{display:flex;gap:12px;align-items:center}button,select{font:inherit;padding:8px 14px;background:white;border:1px solid #a6b6c4;border-radius:5px}input{flex:1}code{font-size:11px;overflow-wrap:anywhere}dt{font-weight:600;font-size:12px;color:#526477}dd{margin:2px 0 8px}#materials{font-size:12px;color:#526477}
</style><main><h1>Source forces in OntoKin</h1><p class="subtitle">Native surfaces, regional materials and recorded source-driven rigid motion</p>
<div class="controls"><label for="fixture">Source fixture</label><select id="fixture"></select><button id="front">Front view</button><button id="side">Side view</button><strong id="program"></strong></div>
<div id="viewport"></div><div class="controls"><button id="play">Play</button><input id="timeline" aria-label="Animation time" type="range" min="0" max="1" step="any" value="0"><output id="time">0.000 s</output></div>
<p id="materials"></p><dl><dt>Source program revision</dt><dd><code id="revision"></code></dd><dt>Recorded GLB SHA-256</dt><dd><code id="artifact"></code></dd></dl>
<p class="subtitle">Y-up cameras keep the same framing throughout <span id="duration"></span> of recorded motion. Source identities and numerical checks accompany these captures.</p>
</main><script type="module">${compiled.outputFiles[0].text}</script></html>`;
const harnessFile='force-viewer.html',harness=path.join(outputDir,harnessFile);
await writeFile(harness,html);
const report={schema_version:agentWorkflow?'ontokin.force-delivery-browser-validation/0.1':'ontokin.force-browser-validation/0.1',status:'running',
  generated_at_utc:new Date().toISOString(),target_contract:'ontokin.glb/0.5',
  implementation:workflow.implementation,git_identity:loaded.gitIdentity,
  workflow_schema_version:workflow.schema_version,source_kind:loaded.sourceKind,agent_audit_sha256:loaded.agentAuditHash,
  acceptance_manifest_sha256:acceptanceHash,fixture_inputs:loaded.fixtureInputs,workflow_sha256:sha256(workflowBytes),
  builder_sha256:loaded.builderHash,oracle_sha256:loaded.oracleHash,
  harness_file:harnessFile,harness_sha256:sha256(Buffer.from(html)),
  verifier_sha256:sha256(await readFile(fileURLToPath(import.meta.url))),
  native_verifier_sha256:sha256(await readFile(path.join(root,'tools/verify_force_native.mjs'))),
  surface_verifier_sha256:sha256(await readFile(path.join(root,'tools/verify_surface_native.mjs'))),
  tooling_lock_sha256:sha256(await readFile(path.join(root,'tools/package-lock.json'))),
  selected_fixtures:fixtureNames,source_workflow_complete_component_corpus:workflow.complete_component_corpus??false,
  source_workflow_complete_agent_delivery_corpus:agentWorkflow,
  complete_browser_corpus:fixtureNames.length===availableCases.length,
  source_fixtures:cases.map(c=>({fixture:c.oracle.fixture,program_revision:c.revision,artifact_sha256:c.artifactHash,
    end_seconds:c.oracle.end_seconds,provenance:c.provenance,exporter_source_code_sha256:c.exportReport.source_code_sha256})),
  environment:{node:process.version,platform:process.platform,architecture:process.arch,
    playwright:tooling.devDependencies.playwright,three:tooling.devDependencies.three,esbuild:tooling.devDependencies.esbuild,
    renderer:'Headless Chromium WebGL2 / ANGLE SwiftShader',camera_up:[0,1,0],viewport:{width:1220,height:1160},device_scale_factor:1,
    timeline_input:'native_range_value_and_input_event_with_time_readback'},
  samples:[],captures:[],playback:[],page_errors:[],console_errors:[],failed_requests:[],network_requests:[],
  limits:['Screenshots require separate identified visual review; finite numerical readback alone cannot certify appearance.',
    agentWorkflow?'This browser role uses the exact artifact bytes reconstructed in the separately audited Agent delivery workflow.':
      'This component role validates source-built GLB bytes. It does not establish Agent transport, artifact retrieval or repair protocol acceptance.',
    'The independent native decoder separately checks full topology, winding, materials, force histories and dense intermediate motion of these artifacts.',
    'The offline browser plays recorded transforms; it does not run live force, impulse, contact or torque physics.',
    'Complete F01-F12 acceptance, inherited regression, compatibility and provider-neutral release evidence remain separately executed gates.']};

function validateReadback(state,observed,time,label) {
  assert.equal(observed.fixture,state.oracle.fixture);assert.equal(observed.revision,state.revision);
  assert.equal(observed.artifact,state.artifactHash);assert.equal(observed.end_seconds,state.oracle.end_seconds);
  assert.equal(observed.decoded.target_contract,'ontokin.glb/0.5');assert.equal(observed.decoded.schema_version,'0.5');
  assert.equal(observed.decoded.profile,state.metadata.profile);assert.equal(observed.decoded.program_revision,state.revision);
  assert.deepEqual(observed.decoded.source_manifest,state.manifest);
  assert.ok(Math.abs(observed.decoded.animation_duration_seconds-Number(state.oracle.end_seconds))<=state.tolerances.time_seconds);
  assert.ok(Math.abs(observed.time-time)<=state.tolerances.time_seconds,label+' time');
  assert.deepEqual(observed.camera.up,[0,1,0]);
  assert.deepEqual(observed.camera.fit_sample_times_seconds,Array.from({length:17},(_,i)=>Number(state.oracle.end_seconds)*i/16));
  assert.equal(observed.camera.fit_policy,'union_of_actual_geometry_over_16_equal_intervals/0.1');
  assert.ok(Number.isFinite(observed.camera.near_m)&&Number.isFinite(observed.camera.far_m));
  assert.ok(observed.camera.near_m>0&&observed.camera.far_m>observed.camera.near_m);
  for(const field of ['position_m','orientation_xyzw','target_m','bounds_min_m','bounds_max_m'])
    assert.ok(observed.camera[field].every(Number.isFinite),'Finite camera '+field);
  const wanted=[...state.oracle.shapes,...state.oracle.empty_objects],objects={};
  assert.deepEqual(Object.keys(observed.objects).sort(),wanted.map(o=>o.path).sort());
  assert.equal(observed.render.triangles,state.oracle.shapes.reduce((n,s)=>n+s.expected.triangles,0),'Every native triangle is rendered');
  assert.ok(observed.render.calls>0);
  for(const object of wanted) {
    const actual=observed.objects[object.path],expected=expectedPose(object,time);
    assert.equal(actual.path,object.path);assert.equal(actual.kind,'object');assert.deepEqual(actual.element_id,object.element_id);
    const sourceNode=state.document.nodes.find(node=>node.extras?.ontokin?.kind==='object'&&node.extras.ontokin.path===object.path);
    assert.ok(sourceNode);assert.deepEqual(actual.source_mapping,sourceNode.extras.ontokin.source_mapping);
    const errors=comparePose(actual,expected,state.tolerances,object.path+' '+label);
    let maximumProbeError=0;
    for(const probe of actual.probes) {
      const [qx,qy,qz,qw]=expected.orientation_xyzw,[x,y,z]=probe.local_m;
      const tx=2*(qy*z-qz*y),ty=2*(qz*x-qx*z),tz=2*(qx*y-qy*x);
      const world=[x+qw*tx+qy*tz-qz*ty,y+qw*ty+qz*tx-qx*tz,z+qw*tz+qx*ty-qy*tx].map((v,i)=>v+expected.position_m[i]);
      maximumProbeError=Math.max(maximumProbeError,vectorError(probe.world_m,world,state.tolerances.position_m,'Browser world surface point'));
      assert.ok(probe.camera_ndc.every(value=>Number.isFinite(value)&&Math.abs(value)<=1+1e-9),'Source surface probe is outside the fitted camera');
    }
    if(object.materials) {
      assert.deepEqual(actual.primitives.map(p=>p.region).sort(),Object.keys(object.materials).sort());
      assert.equal(actual.probes.length,actual.primitives.length*3,'Every primitive supplies independent world probes');
      for(const material of actual.primitives) {
        const wantedMaterial=object.materials[material.region];
        vectorError(material.rgba,wantedMaterial.rgba,1e-12,'Actual browser PBR color');
        assert.equal(material.metallic,wantedMaterial.metallic);assert.equal(material.roughness,wantedMaterial.roughness);
        assert.equal(material.triangles,object.expected.triangles_per_region[material.region]);
      }
    } else {
      assert.deepEqual(actual.primitives,[],'An empty carrier acquired visible geometry');
      assert.deepEqual(actual.probes,[],'An empty carrier acquired surface probes');
    }
    objects[object.path]={...actual,...errors,maximum_world_probe_error_m:maximumProbeError};
  }
  return objects;
}

let browser;
try {
  browser=await chromium.launch({headless:true,args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  report.browser=await browser.version();
  const page=await browser.newPage({viewport:{width:1220,height:1160},deviceScaleFactor:1,reducedMotion:'reduce',serviceWorkers:'block'});
  page.on('pageerror',e=>report.page_errors.push(e.message));
  page.on('console',message=>{if(message.type()==='error')report.console_errors.push(message.text());});
  page.on('request',r=>{if(/^https?:/.test(r.url()))report.network_requests.push(r.url());});
  page.on('requestfailed',r=>report.failed_requests.push({url:r.url(),error:r.failure()?.errorText}));
  await page.route(/^https?:\/\//,route=>route.abort());
  await page.goto(pathToFileURL(harness).href);await page.waitForFunction(()=>window.forceViewer?.ready);
  const setTimeline=async value=>{
    assert.ok(Number.isFinite(value));
    // Chromium canonicalizes range values such as 2.0999999999999996 to 2.1.
    // Exercise the actual range input and its UI handler, then check its
    // accepted value and the resulting decoded pose at the original request.
    const accepted=await page.locator('#timeline').evaluate((input,seconds)=>{
      input.value=String(seconds);input.dispatchEvent(new Event('input',{bubbles:true}));return Number(input.value);
    },value);
    assert.ok(Number.isFinite(accepted)&&Math.abs(accepted-value)<=1e-6,'Native range input changed the requested time');
  };
  for(const state of cases) {
    const end=Number(state.oracle.end_seconds);
    await page.selectOption('#fixture',state.oracle.fixture);
    await page.waitForFunction(name=>window.forceViewer.ready&&window.forceViewer.state.fixture===name,state.oracle.fixture);
    const initial=await page.evaluate(()=>window.forceViewer.state);
    assert.equal(initial.time,0);assert.equal(initial.view,'front');assert.equal(initial.playing,false);
    assert.equal(await page.locator('#timeline').getAttribute('max'),String(end));
    assert.equal(await page.locator('#timeline').getAttribute('step'),'any');
    for(const sample of state.reference.samples) {
      const time=Number(sample.time_seconds);
      await setTimeline(time);
      const observed=await page.evaluate(()=>window.forceViewer.state);
      assert.equal(observed.playing,false);assert.deepEqual(observed.camera,initial.camera,'Seeking must not refit the camera');
      const objects=validateReadback(state,observed,time,'browser at '+sample.time_seconds+' '+sample.side);
      for(const [name,actual] of Object.entries(objects)) {
        const reference=sample.objects[name],q=reference.orientation_wxyz;
        const errors=comparePose(actual,{position_m:reference.position_m,orientation_xyzw:[q[1],q[2],q[3],q[0]]},state.tolerances,name+' source evaluator state');
        actual.source_position_error_m=errors.position_error_m;actual.source_rotation_error_rad=errors.rotation_error_rad;
      }
      report.samples.push({fixture:state.oracle.fixture,time_seconds:sample.time_seconds,side:sample.side,
                          camera:observed.camera,objects});
    }
    let frontCamera;
    for(const capture of [{view:'front',cameraView:'front',time:0},{view:'side',cameraView:'side',time:0},{view:'animated',cameraView:'front',time:.7*end}]) {
      await setTimeline(capture.time);await page.click('#'+capture.cameraView);
      await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
      const observed=await page.evaluate(()=>window.forceViewer.state);
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
    const start=.35*end;
    await setTimeline(start);await page.click('#play');
    await page.waitForFunction(start=>window.forceViewer.state.playing&&window.forceViewer.state.time>start,start);
    await page.click('#play');const paused=await page.evaluate(()=>window.forceViewer.state);
    assert.ok(paused.time>start&&paused.time<end);assert.equal(paused.playing,false);
    const objects=validateReadback(state,paused,paused.time,'paused playback');
    const later=await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve(window.forceViewer.state)))));
    assert.equal(later.time,paused.time);assert.deepEqual(later.objects,paused.objects);assert.deepEqual(later.camera,paused.camera);
    // Drive the real control to its end as well: it must stop without wrapping.
    await setTimeline(end-Math.min(.02,end/100));await page.click('#play');
    await page.waitForFunction(end=>!window.forceViewer.state.playing&&window.forceViewer.state.time===end,end);
    const finished=await page.evaluate(()=>window.forceViewer.state);
    validateReadback(state,finished,end,'automatic playback completion');
    assert.deepEqual(finished.camera,paused.camera,'Playback must retain camera framing');
    report.playback.push({fixture:state.oracle.fixture,started_at_seconds:start,paused_at_seconds:paused.time,
      stopped_at_seconds:finished.time,stopped_at_end:true,stable_across_frames:true,camera:paused.camera,objects});
  }
  report.webgl=await page.evaluate(()=>{const gl=document.querySelector('canvas').getContext('webgl2');if(!gl)return null;
    const debug=gl.getExtension('WEBGL_debug_renderer_info');return {version:gl.getParameter(gl.VERSION),renderer:gl.getParameter(gl.RENDERER),
      unmasked_renderer:debug?gl.getParameter(debug.UNMASKED_RENDERER_WEBGL):null};});
  assert.ok(report.webgl);for(const key of ['page_errors','console_errors','failed_requests','network_requests'])assert.deepEqual(report[key],[],key);
  report.world_pose_comparisons=report.samples.reduce((n,s)=>n+Object.keys(s.objects).length,0);
  report.capture_pose_comparisons=report.captures.reduce((n,s)=>n+Object.keys(s.objects).length,0);
  assert.equal(report.captures.length,cases.length*3);assert.equal(report.playback.length,cases.length);
  report.status='passed';
} catch(error) {
  report.status='failed';report.failure={name:error.name,message:error.message};throw error;
} finally {
  if(browser)await browser.close();
  await writeFile(path.join(outputDir,'browser-validation.json'),JSON.stringify(report,null,2)+'\n');
}
console.log(JSON.stringify({status:report.status,fixtures:cases.length,world_pose_comparisons:report.world_pose_comparisons,
  screenshots:report.captures.length,browser:report.browser,output_dir:outputDir},null,2));
