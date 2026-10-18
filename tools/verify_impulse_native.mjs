// Independent Khronos/Three.js checks of exact Agent/0.4 source artifacts.
import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import validator from 'gltf-validator';
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {root,sha256,quat,comparePose,rotationError,vectorError,readAccessor,verifyGeometry} from './verify_surface_native.mjs';

export {root,sha256,comparePose,vectorError};
const json=bytes=>JSON.parse(bytes.toString('utf8'));
const canonical=value=>Array.isArray(value)?value.map(canonical):value&&typeof value==='object'
  ?Object.fromEntries(Object.keys(value).sort().map(k=>[k,canonical(value[k])])):value;
const stable=value=>JSON.stringify(canonical(value));
const acceptanceBytes=await readFile(path.join(root,'docs/language-design/impulse-v0.1/acceptance.json'));
const acceptance=json(acceptanceBytes),cases=new Map(acceptance.source_cases.map(c=>[c.id,c]));
const bounds={P01:0,P02:5,P03:5,P04:7,P07:0,P08:7.5,P09:5,P10:3.75,P11:40};
const turn=(axis,angle)=>new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(...axis),angle);

export function expectedPose(object,time) {
  const id=object.motion.fixture,t=Number(time),dt=Math.max(0,t-1);
  let position=[0,0,0],rotation=new THREE.Quaternion();
  if(id==='P04') {
    if(object.path==='carrier') {position=[Math.min(t,1),0,0];rotation=turn([0,0,1],-2+2*Math.min(t,1));}
    else if(t<1) {const a=-2+2*t;position=[t+.5*Math.cos(a),.5*Math.sin(a),0];rotation=turn([0,0,1],a);}
    else {position=[1.5+dt,2*dt-5*dt*dt,0];rotation=turn([0,0,1],7*dt);}
  } else if(['P08','P09','P10'].includes(id)) {
    if(object.path!=='rack') {
      const first=object.path==='rack.props["first"]',speed=first?(id==='P09'?.5:1):.5;
      const spin=first?{P08:5,P09:2.5,P10:1.25}[id]:2.5;
      position=[first?0:3,speed*dt,0];rotation=turn([0,0,1],spin*dt);
    }
  } else if(id==='P01')position=[3*dt,0,0];
  else if(id==='P02') {position=[0,dt,0];rotation=turn([0,0,1],5*dt);}
  else if(id==='P03') {position=[0,dt,0];rotation=turn([1,0,0],5*dt).multiply(turn([0,1,0],Math.PI/2));}
  else if(id==='P07')position=[0,t<1?5-5*t*t:-5*dt*dt,0];
  else {assert.equal(id,'P11');position=[0,8*dt,0];rotation=turn([0,0,1],40*dt);}
  return {position_m:position,orientation_xyzw:rotation.toArray()};
}

function checkGeometryOracle(oracle) {
  // Fixed scalar reading of the unchanged, hash-pinned surface library.
  const sections=[
    {key:'foot',station_m:0,center_xy_m:[0,0],radii_xy_m:[.5,.35],region:'clay'},
    {key:'neck',station_m:1,center_xy_m:[.15,0],radii_xy_m:[.3,.2],region:'paint'},
    {key:'tip',station_m:1.5,center_xy_m:[.15,0],radii_xy_m:[.2,.1],region:'paint'}];
  const materials={clay:{rgba:[.6,.3,.2,1],metallic:0,roughness:.8},paint:{rgba:[.1,.4,.8,1],metallic:.2,roughness:.4}};
  const generated=['P08','P09','P10'].includes(oracle.fixture);
  assert.deepEqual(oracle.shapes.map(s=>s.path),generated?['rack.props["first"]','rack.props["second"]']:['ball']);
  assert.deepEqual(oracle.empty_objects.map(s=>s.path),generated?['rack']:oracle.fixture==='P04'?['carrier']:[]);
  for(const shape of oracle.shapes) {
    assert.deepEqual(shape.sections,sections);assert.deepEqual(shape.materials,materials);
    assert.equal(shape.facets,16);assert.equal(shape.caps,'flat');
    assert.deepEqual(shape.local_position_m,[0,0,.1]);assert.deepEqual(shape.local_rotation_wxyz,[1,0,0,0]);
    const second=shape.path==='rack.props["second"]';
    assert.equal(shape.body_mass_kg,second||oracle.fixture==='P09'?4:2);
    assert.equal(shape.body_radius_m,!second&&oracle.fixture==='P10'?1:.5);
  }
}

export async function loadCase(directory) {
  const names={bundle:'program.bundle.json',glb:'scene.glb',export:'scene.export.json',reference:'scene.reference.json',oracle:'oracle.json'};
  const inputs=Object.fromEntries(await Promise.all(Object.entries(names).map(async ([key,file])=>[key,await readFile(path.join(directory,file))])));
  const provenance=Object.fromEntries(Object.entries(names).map(([key,file])=>[key,{file,sha256:sha256(inputs[key]),byte_length:inputs[key].length}]));
  const payload=json(inputs.bundle),exportReport=json(inputs.export),reference=json(inputs.reference),oracle=json(inputs.oracle);
  const fixture=cases.get(oracle.fixture);assert.ok(fixture?.delivery_required);
  assert.equal(payload.schema_version,'ontokin.bundle/0.1');
  assert.equal(oracle.schema_version,'ontokin.impulse-fixture-oracle/0.1');
  assert.equal(oracle.acceptance_manifest_sha256,sha256(acceptanceBytes));
  assert.deepEqual(oracle.frozen_expected,fixture.expected);checkGeometryOracle(oracle);
  const units=[{source_id:'entry',package_id:null,version:null,filename:payload.entry.filename,source_revision:sha256(Buffer.from(payload.entry.source))},
    ...payload.modules.map(m=>({source_id:`package:${m.package_id}@${m.version}`,package_id:m.package_id,version:m.version,
      filename:m.filename,source_revision:sha256(Buffer.from(m.source))}))].sort((a,b)=>a.source_id<b.source_id?-1:a.source_id>b.source_id?1:0);
  assert.deepEqual(units,fixture.sources,'Every exported source byte belongs to the frozen complete closure');
  const manifest={schema_version:'ontokin.bundle/0.1',entry_source_id:'entry',units};
  const revision=sha256(Buffer.concat([Buffer.from('ontokin.bundle/0.1\0'),Buffer.from(stable(manifest))]));
  assert.equal(revision,fixture.program_revision);assert.equal(oracle.program_revision,revision);
  for(const [index,source] of [payload.entry,...payload.modules].entries()) {
    assert.equal(path.basename(source.filename),source.filename);
    const raw=await readFile(path.join(directory,source.filename));assert.equal(raw.toString('utf8'),source.source);
    provenance['source_'+index]={file:source.filename,sha256:sha256(raw),byte_length:raw.length};
  }
  const bytes=inputs.glb;
  assert.equal(bytes.readUInt32LE(0),0x46546c67);assert.equal(bytes.readUInt32LE(4),2);
  assert.equal(bytes.readUInt32LE(8),bytes.length);assert.equal(bytes.readUInt32LE(16),0x4e4f534a);
  const jsonLength=bytes.readUInt32LE(12),document=json(bytes.subarray(20,20+jsonLength)),offset=20+jsonLength;
  assert.equal(bytes.readUInt32LE(offset+4),0x004e4942);assert.equal(offset+8+bytes.readUInt32LE(offset),bytes.length);
  const binary=bytes.subarray(offset+8),metadata=document.extras.ontokin;
  assert.equal(exportReport.schema_version,'ontokin.glb-report/0.4');assert.equal(exportReport.target_contract,'ontokin.glb/0.4');
  assert.equal(exportReport.validation.status,'passed');assert.equal(metadata.target_contract,'ontokin.glb/0.4');
  assert.equal(metadata.profile,'impulse-0.1');assert.equal(metadata.program.revision,revision);
  assert.deepEqual(metadata.program.manifest,manifest);assert.deepEqual(exportReport.program.manifest,manifest);
  assert.equal(exportReport.program_revision,revision);assert.equal(reference.program_revision,revision);
  assert.deepEqual(reference.source_manifest,manifest);
  assert.equal(reference.schema_version,'ontokin.impulse-native-reference/0.1');
  assert.equal(reference.artifact_sha256,provenance.glb.sha256);assert.equal(exportReport.artifact.sha256,provenance.glb.sha256);
  assert.equal(exportReport.artifact.byte_length,bytes.length);assert.deepEqual(reference.tolerances,exportReport.tolerances);
  const tolerances={position_m:.001,rotation_rad:.001,time_seconds:.000001};
  for(const [key,limit] of Object.entries(tolerances)) {
    const actual=reference.tolerances[key];assert.ok(Number.isFinite(actual)&&actual>0&&actual<=limit);tolerances[key]=actual;
  }
  const expectedSamples=fixture.expected.samples.map(s=>[s.time_seconds,s.side]);
  for(const [time,side] of expectedSamples)assert.ok(reference.samples.some(s=>s.time_seconds===time&&s.side===side),'A frozen source sample is missing');
  return {directory,bytes,document,binary,metadata,exportReport,reference,oracle,manifest,revision,
    provenance,tolerances,artifactHash:provenance.glb.sha256,fixture};
}

function assertClock(document,binary,bound) {
  const animation=document.animations[0],first=readAccessor(document,binary,animation.samplers[0].input).flat();
  assert.equal(first[0],0);assert.equal(first.at(-1),2);
  for(const sampler of animation.samplers)assert.deepEqual(readAccessor(document,binary,sampler.input).flat(),first);
  for(let i=1;i<first.length;i++) {
    assert.ok(first[i]>first[i-1]);assert.ok((first[i]-first[i-1])*bound<Math.PI/2,'Authored impulse spin aliases between decoded keys');
  }
  assert.ok(first.includes(1),'The exact source impulse boundary must survive');
  return first;
}

function verifyInfluences(state) {
  const records=state.metadata.boundary_states,objects=[...state.oracle.shapes,...state.oracle.empty_objects];
  assert.deepEqual(records.map(r=>r.source_seconds),['0','1','2']);
  let applications=0;
  for(const record of records) {
    const sample=state.reference.samples.find(s=>s.time_seconds===record.source_seconds&&s.side==='after');
    assert.ok(sample,'Exact after-side source state is missing');
    assert.deepEqual(Object.keys(record.impulse_states_after).sort(),objects.map(o=>o.path).sort());
    for(const object of objects) {
      const actual=record.impulse_states_after[object.path],reference=sample.objects[object.path];
      assert.deepEqual(actual,reference.impulses,'Source influence metadata differs from actual Agent inspection');
      const statements=(state.fixture.source_impulse_statements??[]).filter(s=>s.target_path_spelling===object.path);
      const expectedCount=Number(record.source_seconds)<1?0:statements.length;
      assert.equal(actual.applied_count,expectedCount);assert.equal(actual.last_applications.length,expectedCount);
      assert.equal(actual.last_application_time_seconds,expectedCount?'1':null);
      for(const [index,application] of actual.last_applications.entries()) {
        const statement=statements[index];assert.equal(application.sequence_index,statement.sequence_index);
        assert.deepEqual(application.source_location,statement.source_location);assert.deepEqual(application.target_element_id,object.element_id);
        assert.equal(application.target_path,object.path);
        // A retained record describes the original application boundary, even
        // after its target has translated and rotated on the later free arc.
        const appliedSample=state.reference.samples.find(s=>s.time_seconds===actual.last_application_time_seconds&&s.side==='after');
        assert.ok(appliedSample,'The actual application-time source pose must be retained');
        const appliedPose=appliedSample.objects[object.path];
        const rotation=quat(appliedPose.orientation_wxyz),lever=new THREE.Vector3(...application.application_point_self_m).applyQuaternion(rotation);
        vectorError(lever.toArray(),application.lever_arm_world_m,1e-9,'Rotated source lever arm');
        vectorError(lever.clone().add(new THREE.Vector3(...appliedPose.position_m)).toArray(),application.application_point_world_m,1e-9,'World application point');
        const angular=lever.clone().cross(new THREE.Vector3(...application.impulse_world_n_s));
        vectorError(angular.toArray(),application.angular_impulse_world_n_m_s,1e-9,'Off-center angular impulse');
        const inertia=.4*object.body_mass_kg*object.body_radius_m**2;
        vectorError(application.linear_velocity_before_world_m_per_s.map((v,i)=>v+application.impulse_world_n_s[i]/object.body_mass_kg),
          application.linear_velocity_after_world_m_per_s,1e-9,'Linear momentum update');
        vectorError(application.angular_velocity_before_world_rad_per_s.map((v,i)=>v+angular.getComponent(i)/inertia),
          application.angular_velocity_after_world_rad_per_s,1e-9,'Angular momentum update');
        applications++;
      }
    }
  }
  assert.equal(state.metadata.impulse_profile.source_impulses,'instantaneous_world_momentum_at_target_self_point');
  assert.equal(state.metadata.impulse_profile.continuous_external_torques,'absent');
  return {status:'passed',boundary_count:records.length,retained_application_comparisons:applications};
}

function rejectCoarsenedTrack(state,samples) {
  // Adversarially remove intermediate clock keys from a copy of the actual
  // binary. The source-bound clock check must reject its hidden full turns.
  const coarseDocument=structuredClone(state.document),coarseBinary=Buffer.from(state.binary);
  for(const index of new Set(coarseDocument.animations[0].samplers.map(s=>s.input))) {
    const accessor=coarseDocument.accessors[index],view=coarseDocument.bufferViews[accessor.bufferView];
    assert.equal(accessor.componentType,5126);assert.equal(accessor.type,'SCALAR');assert.ok(accessor.count>3);
    const offset=(view.byteOffset??0)+(accessor.byteOffset??0),stride=view.byteStride??4;
    [0,1,2].forEach((value,i)=>coarseBinary.writeFloatLE(value,offset+i*stride));accessor.count=3;
  }
  assert.throws(()=>assertClock(coarseDocument,coarseBinary,bounds.P11),/spin aliases/);
  // Use decoded destination endpoints for a deliberately coarse slerp. A
  // midpoint alone aliases for this fixture; the quarter-time exposes it.
  const at=time=>samples.find(s=>s.time_seconds===time&&s.side==='after').objects.ball;
  const start=at('1').orientation_xyzw,end=at('2').orientation_xyzw;
  const coarse=new THREE.Quaternion(...start).slerp(new THREE.Quaternion(...end),.25).toArray();
  const expected=expectedPose(state.oracle.shapes[0],1.25),error=rotationError(coarse,expected.orientation_xyzw);
  assert.ok(error>state.tolerances.rotation_rad,'A coarsened full-turn trap must actually fail its independent pose oracle');
  assert.throws(()=>comparePose({position_m:expected.position_m,orientation_xyzw:coarse},expected,state.tolerances,'Coarsened P11'),/rotation error/);
  return {status:'passed',clock_alias_rejected:true,coarse_rotation_rejected:true,
    probe_time_seconds:'1.25',coarse_rotation_error_rad:error,tolerance_rad:state.tolerances.rotation_rad,
    removed_intermediate_keys:true,endpoint_source:'Actual decoded GLB/0.4 carrier poses'};
}

export async function verifyCase(directory) {
  const state=await loadCase(directory);
  const format=await validator.validateBytes(new Uint8Array(state.bytes),{uri:'scene.glb',maxIssues:1000});
  assert.equal(format.issues.numErrors,0,JSON.stringify(format.issues.messages));
  assert.equal(format.issues.numWarnings,0,JSON.stringify(format.issues.messages));
  const gltf=await new GLTFLoader().parseAsync(state.bytes.buffer.slice(state.bytes.byteOffset,state.bytes.byteOffset+state.bytes.byteLength),'');
  const expectedObjects=[...state.oracle.shapes,...state.oracle.empty_objects??[]];
  assert.equal(state.document.nodes.length,expectedObjects.length,'No second carrier or hidden motion node');
  // GLTFLoader attaches node extras to generated child primitives too. Use
  // the declared source carrier index, not a traversal count of copied extras.
  const objects=new Map();
  for(const object of expectedObjects) {
    const index=state.document.nodes.findIndex(n=>n.extras?.ontokin?.path===object.path);
    assert.ok(index>=0);const node=await gltf.parser.getDependency('node',index);objects.set(object.path,node);
    assert.deepEqual(state.document.nodes[index].extras.ontokin.element_id,object.element_id);
    if(!object.sections)assert.ok(!('mesh' in state.document.nodes[index]),'Empty carriers retain no authored mesh');
  }
  const clockTimes=assertClock(state.document,state.binary,bounds[state.oracle.fixture]);
  const influences=verifyInfluences(state);
  const geometry=state.oracle.shapes.map(shape=>verifyGeometry(state,shape));
  for(const shape of state.oracle.shapes) {
    const physical=state.document.nodes.find(n=>n.extras.ontokin.path===shape.path).extras.ontokin.physical;
    assert.equal(physical.mass,shape.body_mass_kg);assert.equal(physical.radius,shape.body_radius_m);
    assert.ok(Math.abs(physical.inertia-.4*shape.body_mass_kg*shape.body_radius_m**2)<1e-12);
  }
  const decodedMaterials=[];
  for(const shape of state.oracle.shapes) {
    const carrier=objects.get(shape.path),children=[];carrier.traverse(node=>{if(node.isMesh)children.push(node);});
    assert.equal(children.length,geometry.find(g=>g.path===shape.path).regions.length);
    for(const child of children) {
      const region=child.userData.ontokin?.region_key??child.material.userData.ontokin?.source_region_key;
      assert.ok(region in shape.materials);const material=shape.materials[region];
      vectorError([...child.material.color.toArray(),child.material.opacity],material.rgba,1e-12,'Three.js decoded linear PBR color');
      assert.equal(child.material.metalness,material.metallic);assert.equal(child.material.roughness,material.roughness);
      decodedMaterials.push({path:shape.path,region,triangles:child.geometry.index.count/3,
        rgba:[...child.material.color.toArray(),child.material.opacity],metallic:child.material.metalness,roughness:child.material.roughness});
    }
  }
  assert.equal(gltf.animations.length,1);const mixer=new THREE.AnimationMixer(gltf.scene);
  const action=mixer.clipAction(gltf.animations[0]);action.setLoop(THREE.LoopOnce,1);action.clampWhenFinished=true;action.play();
  const samples=[];
  for(const sample of state.reference.samples) {
    const time=Number(sample.time_seconds);action.reset().play();mixer.setTime(time);gltf.scene.updateMatrixWorld(true);
    assert.deepEqual(Object.keys(sample.objects).sort(),expectedObjects.map(o=>o.path).sort());
    const poses={};
    for(const object of expectedObjects) {
      const node=objects.get(object.path),actual={position_m:node.getWorldPosition(new THREE.Vector3()).toArray(),
        orientation_xyzw:node.getWorldQuaternion(new THREE.Quaternion()).toArray()};
      const oracle=expectedPose(object,time),reference=sample.objects[object.path];
      const analytical=comparePose(actual,oracle,state.tolerances,object.path+' independent at '+time);
      const evaluator=comparePose(actual,{position_m:reference.position_m,orientation_xyzw:quat(reference.orientation_wxyz).toArray()},
        state.tolerances,object.path+' evaluator at '+time);
      const landmarks=[];
      if(object.sections) {
        const child=[];node.traverse(n=>{if(n.isMesh)child.push(n);});
        for(const mesh of child) {
          const positions=mesh.geometry.attributes.position;
          for(const index of [mesh.geometry.index.getX(0),mesh.geometry.index.getX(mesh.geometry.index.count-1)]) {
            const local=new THREE.Vector3().fromBufferAttribute(positions,index),world=local.clone().applyMatrix4(mesh.matrixWorld);
            // Local mesh topology was checked independently above. This probe
            // catches extra child transforms or double-applied local placement.
            const wanted=local.clone().applyQuaternion(new THREE.Quaternion(...oracle.orientation_xyzw)).add(new THREE.Vector3(...oracle.position_m));
            const error=vectorError(world.toArray(),wanted.toArray(),state.tolerances.position_m,'Three.js world surface point');
            landmarks.push({local_m:local.toArray(),world_m:world.toArray(),error_m:error});
          }
        }
      }
      poses[object.path]={...actual,independent:analytical,evaluator,landmarks};
    }
    samples.push({time_seconds:sample.time_seconds,side:sample.side,objects:poses});
  }
  // A dense clock alone cannot establish that its stored values are correct.
  // Decode and inspect every actual key plus three interior interpolation
  // points, independently of the fixed Agent reference sample schedule.
  const decodedTimes=new Set(clockTimes);
  for(let i=1;i<clockTimes.length;i++) {
    const start=clockTimes[i-1],width=clockTimes[i]-start;
    for(const fraction of [.25,.5,.75])decodedTimes.add(start+fraction*width);
  }
  const decodedSamples=[];
  for(const time of [...decodedTimes].sort((a,b)=>a-b)) {
    action.reset().play();mixer.setTime(time);gltf.scene.updateMatrixWorld(true);
    const poses={};
    for(const object of expectedObjects) {
      const node=objects.get(object.path),actual={position_m:node.getWorldPosition(new THREE.Vector3()).toArray(),
        orientation_xyzw:node.getWorldQuaternion(new THREE.Quaternion()).toArray()};
      const independent=comparePose(actual,expectedPose(object,time),state.tolerances,
        object.path+' decoded clock independent at '+time);
      poses[object.path]={...actual,independent};
    }
    decodedSamples.push({time_seconds:time,objects:poses});
  }
  return {fixture:state.oracle.fixture,status:'passed',case_ids:state.oracle.case_ids,
    program_revision:state.revision,artifact_sha256:state.artifactHash,provenance:state.provenance,
    exporter_source_code_sha256:state.exportReport.source_code_sha256,
    khronos:{version:validator.version(),errors:format.issues.numErrors,warnings:format.issues.numWarnings,
      infos:format.issues.numInfos,hints:format.issues.numHints,messages:format.issues.messages},
    impulse_boundaries:influences,
    clock:{key_count:clockTimes.length,authored_angular_speed_bound_rad_per_s:bounds[state.oracle.fixture],
      maximum_interval_seconds:Math.max(...clockTimes.slice(1).map((t,i)=>t-clockTimes[i])),source_boundaries_retained:true},
    ...(state.oracle.fixture==='P11'?{coarsened_track_rejected:rejectCoarsenedTrack(state,samples)}:{}),
    geometry,three_js:{version:THREE.REVISION,materials:decodedMaterials,world_pose_comparisons:samples.length*expectedObjects.length,samples,
      decoded_clock_pose_comparisons:decodedSamples.length*expectedObjects.length,decoded_clock_samples:decodedSamples}};
}

async function main() {
  const args=process.argv.slice(2);let demoDir,output;
  for(let i=0;i<args.length;i++) {
    if(args[i]==='--help') {console.log('Usage: node tools/verify_impulse_native.mjs --demo-dir DIR --output FILE');return;}
    assert.ok(['--demo-dir','--output'].includes(args[i]));assert.ok(args[i+1]);
    const option=args[i],value=path.resolve(args[++i]);if(option==='--demo-dir')demoDir=value;else output=value;
  }
  assert.ok(demoDir&&output,'Both --demo-dir and --output are required');
  const buildBytes=await readFile(path.join(demoDir,'native-build.json')),build=json(buildBytes);
  assert.equal(build.schema_version,'ontokin.impulse-native-build/0.1');assert.equal(build.status,'built');
  assert.equal(build.acceptance_manifest_sha256,sha256(acceptanceBytes));
  const required=acceptance.source_cases.filter(c=>c.delivery_required).map(c=>c.id).sort();
  assert.deepEqual(build.fixtures.map(f=>f.fixture).sort(),required,'Every predetermined D1 fixture must be independently decoded');
  const tooling=json(await readFile(path.join(root,'tools/package.json')));
  assert.equal(validator.version(),tooling.devDependencies['gltf-validator']);
  assert.equal(json(await readFile(path.join(root,'tools/node_modules/three/package.json'))).version,tooling.devDependencies.three);
  const results=[],report={schema_version:'ontokin.impulse-native-destination-validation/0.1',status:'running',
    generated_at_utc:new Date().toISOString(),implementation:build.implementation,
    build_sha256:sha256(buildBytes),acceptance_manifest_sha256:sha256(acceptanceBytes),
    git_revision:build.git_revision,working_tree_changes:build.working_tree_changes,
    verifier_sha256:sha256(await readFile(fileURLToPath(import.meta.url))),
    surface_verifier_sha256:sha256(await readFile(path.join(root,'tools/verify_surface_native.mjs'))),
    tooling_lock_sha256:sha256(await readFile(path.join(root,'tools/package-lock.json'))),
    environment:{node:process.version,platform:process.platform,architecture:process.arch,
      three:tooling.devDependencies.three,khronos_gltf_validator:validator.version()},fixtures:results,
    limits:['This independently checks the named actual source-built impulse GLBs, fixed poses, every decoded key and three interior points per interval.',
      'Finite pose samples and declared local float32 tolerances do not establish every continuous time or arbitrary programs.',
      'GLB is recorded motion; contacts, live impulses, Blender, external engine physics and authoring-productivity benchmarks were not executed.']};
  try {
    for(const item of build.fixtures) {
      const result=await verifyCase(path.join(demoDir,item.fixture));
      assert.equal(result.program_revision,item.program_revision);assert.equal(result.artifact_sha256,item.artifact_sha256);
      assert.equal('sha256:'+result.exporter_source_code_sha256,build.implementation.source_code_sha256);
      results.push(result);
    }
    const baseline=results.find(r=>r.fixture==='P08');report.physical_repairs=[];
    for(const fixture of ['P09','P10']) {
      const changed=results.find(r=>r.fixture===fixture);assert.notEqual(changed.program_revision,baseline.program_revision);
      for(const original of baseline.geometry) {
        const edited=changed.geometry.find(g=>g.path===original.path);
        assert.equal(edited.positions_sha256,original.positions_sha256);assert.equal(edited.topology_sha256,original.topology_sha256);
        assert.deepEqual(edited.regions,original.regions,'Physical-only edits preserve actual decoded regional materials');
      }
      const sibling='rack.props["second"]',target='rack.props["first"]';
      for(const sample of baseline.three_js.samples) {
        const other=changed.three_js.samples.find(s=>s.time_seconds===sample.time_seconds&&s.side===sample.side);assert.ok(other);
        assert.deepEqual(other.objects[sibling],sample.objects[sibling],'A scoped physical edit cannot alter the sibling pose or geometry');
      }
      const before=baseline.three_js.samples.find(s=>s.time_seconds==='1.5'&&s.side==='after').objects[target];
      const after=changed.three_js.samples.find(s=>s.time_seconds==='1.5'&&s.side==='after').objects[target];
      assert.ok(rotationError(before.orientation_xyzw,after.orientation_xyzw)>.001,'The targeted physical response must visibly change');
      report.physical_repairs.push({before_fixture:'P08',after_fixture:fixture,status:'passed',target_path:target,
        sibling_path:sibling,geometry_and_pbr_unchanged:true,sibling_pose_unchanged:true,target_angular_response_changed:true});
    }
    report.status='passed';
  } catch(error) {report.status='failed';report.failure={name:error.name,message:error.message};throw error;}
  // Keep every decoded pose within the inherited bounded JSON reader.
  finally {await mkdir(path.dirname(output),{recursive:true});await writeFile(output,JSON.stringify(report)+'\n');}
  console.log(JSON.stringify({status:report.status,fixtures:results.length,
    world_pose_comparisons:results.reduce((s,r)=>s+r.three_js.world_pose_comparisons,0),
    decoded_clock_pose_comparisons:results.reduce((s,r)=>s+r.three_js.decoded_clock_pose_comparisons,0),output},null,2));
}

if(process.argv[1]&&pathToFileURL(path.resolve(process.argv[1])).href===import.meta.url)await main();
