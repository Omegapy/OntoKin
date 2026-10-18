// Independently decode native .ok-produced GLB/0.3 with Khronos and Three.js.
import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import validator from 'gltf-validator';
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';

export const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
export const sha256=bytes=>'sha256:'+createHash('sha256').update(bytes).digest('hex');
const json=bytes=>JSON.parse(bytes.toString('utf8'));
const stable=value=>JSON.stringify(canonical(value));
function canonical(value) {
  if(Array.isArray(value)) return value.map(canonical);
  if(value&&typeof value==='object') return Object.fromEntries(Object.keys(value).sort().map(k=>[k,canonical(value[k])]));
  return value;
}
function unit(q) {const n=Math.hypot(...q);assert.ok(Number.isFinite(n)&&n>0);return q.map(v=>v/n);}
export function quat(q) {const [w,x,y,z]=unit(q);return new THREE.Quaternion(x,y,z,w);}
function transform(point,rotation,translation) {
  return new THREE.Vector3(...point).applyQuaternion(quat(rotation)).add(new THREE.Vector3(...translation)).toArray();
}
export function expectedPose(object,time) {
  const motion=object.motion;
  const position=motion.position_m.map((p,i)=>p+time*motion.velocity_m_per_s[i]);
  if(motion.kind==='affine') return {position_m:position,orientation_xyzw:quat(motion.rotation_wxyz).toArray()};
  if(motion.kind==='released_uniform_gravity') {
    assert.ok(Number.isFinite(motion.release_time_s)&&motion.release_time_s>=0);
    assert.equal(motion.gravity_m_per_s2.length,3);
    assert.ok(motion.gravity_m_per_s2.every(Number.isFinite));
    const elapsed=Math.max(0,time-motion.release_time_s);
    return {position_m:position.map((p,i)=>p+.5*motion.gravity_m_per_s2[i]*elapsed*elapsed),
      orientation_xyzw:quat(motion.rotation_wxyz).toArray()};
  }
  assert.equal(motion.kind,'hinge_y_on_translating_z90_parent');
  const parent=new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0,0,1),Math.PI/2);
  const local=new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0,1,0),motion.angle_rad_per_second*time);
  return {position_m:new THREE.Vector3(...motion.mount_position_m).applyQuaternion(parent)
    .add(new THREE.Vector3(...position)).toArray(),orientation_xyzw:parent.multiply(local).toArray()};
}
export function vectorError(actual,expected,tolerance,label) {
  assert.equal(actual.length,expected.length,label);
  assert.ok([...actual,...expected].every(Number.isFinite),label+' must be finite');
  const error=Math.max(...actual.map((n,i)=>Math.abs(n-expected[i])));
  assert.ok(error<=tolerance,`${label}: error ${error} exceeds ${tolerance}; ${actual} / ${expected}`);
  return error;
}
export function rotationError(actual,expected) {
  const a=unit(actual),b=unit(expected);
  const minus=Math.hypot(...a.map((n,i)=>n-b[i])),plus=Math.hypot(...a.map((n,i)=>n+b[i]));
  return 4*Math.atan2(Math.min(minus,plus),Math.max(minus,plus));
}
export function comparePose(actual,expected,tolerances,label) {
  const p=vectorError(actual.position_m,expected.position_m,tolerances.position_m,label+' position');
  const r=rotationError(actual.orientation_xyzw,expected.orientation_xyzw);
  assert.ok(r<=tolerances.rotation_rad,label+` rotation error ${r}`);
  return {position_error_m:p,rotation_error_rad:r};
}
export function readAccessor(document,binary,index) {
  const accessor=document.accessors[index],view=document.bufferViews[accessor.bufferView];
  assert.ok(!accessor.sparse,'Sparse buffers are outside this native adapter');
  const dimensions={SCALAR:1,VEC2:2,VEC3:3,VEC4:4}[accessor.type];
  const widths={5123:2,5125:4,5126:4},width=widths[accessor.componentType];
  assert.ok(dimensions&&width);
  const stride=view.byteStride??dimensions*width;
  const start=(view.byteOffset??0)+(accessor.byteOffset??0);
  assert.ok(start>=0&&start+(accessor.count-1)*stride+dimensions*width<=binary.length);
  const read=accessor.componentType===5126?'readFloatLE':accessor.componentType===5123?'readUInt16LE':'readUInt32LE';
  return Array.from({length:accessor.count},(_,i)=>Array.from({length:dimensions},(__,j)=>binary[read](start+i*stride+j*width)));
}

export async function loadCase(directory) {
  const files={bundle:'program.bundle.json',glb:'scene.glb',export:'scene.export.json',
    reference:'scene.reference.json',oracle:'oracle.json'};
  const input=Object.fromEntries(await Promise.all(Object.entries(files).map(async ([k,v])=>[k,await readFile(path.join(directory,v))])));
  const provenance=Object.fromEntries(Object.entries(files).map(([k,v])=>[k,{file:v,sha256:sha256(input[k]),byte_length:input[k].length}]));
  const payload=json(input.bundle),exportReport=json(input.export),reference=json(input.reference),oracle=json(input.oracle);
  assert.equal(payload.schema_version,'ontokin.bundle/0.1');
  const units=[{source_id:'entry',package_id:null,version:null,filename:payload.entry.filename,source_revision:sha256(Buffer.from(payload.entry.source))},
    ...payload.modules.map(m=>({source_id:`package:${m.package_id}@${m.version}`,package_id:m.package_id,version:m.version,
      filename:m.filename,source_revision:sha256(Buffer.from(m.source))}))].sort((a,b)=>a.source_id<b.source_id?-1:a.source_id>b.source_id?1:0);
  const manifest={schema_version:'ontokin.bundle/0.1',entry_source_id:'entry',units};
  const revision=sha256(Buffer.concat([Buffer.from('ontokin.bundle/0.1\0'),Buffer.from(stable(manifest))]));
  for(const [i,source] of [payload.entry,...payload.modules].entries()) {
    assert.match(source.source,/ontokin "0\.3";/); assert.match(source.source,/profile "surface-0\.1";/);
    assert.ok(source.filename===path.basename(source.filename),'Fixture source files stay within their directory');
    const raw=await readFile(path.join(directory,source.filename));
    assert.equal(raw.toString('utf8'),source.source);
    provenance['source_'+i]={file:source.filename,sha256:sha256(raw),byte_length:raw.length};
  }
  const bytes=input.glb;
  assert.equal(bytes.readUInt32LE(0),0x46546c67);assert.equal(bytes.readUInt32LE(4),2);
  assert.equal(bytes.readUInt32LE(8),bytes.length);assert.equal(bytes.readUInt32LE(16),0x4e4f534a);
  const length=bytes.readUInt32LE(12),document=json(bytes.subarray(20,20+length));
  const binaryOffset=20+length;
  assert.equal(bytes.readUInt32LE(binaryOffset+4),0x004e4942);
  assert.equal(binaryOffset+8+bytes.readUInt32LE(binaryOffset),bytes.length);
  const binary=bytes.subarray(binaryOffset+8),metadata=document.extras.ontokin;
  assert.equal(exportReport.schema_version,'ontokin.glb-report/0.3');
  assert.equal(exportReport.target_contract,'ontokin.glb/0.3');
  assert.equal(exportReport.validation.status,'passed');
  assert.equal(metadata.target_contract,'ontokin.glb/0.3'); assert.equal(metadata.profile,'surface-0.1');
  assert.equal(metadata.program.revision,revision);
  assert.deepEqual(metadata.program.manifest,manifest); assert.deepEqual(exportReport.program.manifest,manifest);
  assert.equal(exportReport.program_revision,revision); assert.equal(reference.program_revision,revision);
  assert.deepEqual(reference.source_manifest,manifest);
  assert.equal(reference.schema_version,'ontokin.surface-native-reference/0.1');
  assert.equal(reference.artifact_sha256,provenance.glb.sha256); assert.equal(exportReport.artifact.sha256,provenance.glb.sha256);
  assert.equal(exportReport.artifact.byte_length,bytes.length);
  assert.deepEqual(reference.tolerances,exportReport.tolerances);
  const tolerances={position_m:.001,rotation_rad:.001,time_seconds:.000001};
  for(const [key,limit] of Object.entries(tolerances)) {
    const actual=reference.tolerances[key];assert.ok(Number.isFinite(actual)&&actual>0&&actual<=limit);
    tolerances[key]=actual;
  }
  const acceptance=await readFile(path.join(root,'docs/language-design/surface-v0.1/acceptance.json'));
  assert.equal(oracle.acceptance_manifest_sha256,sha256(acceptance));
  if(oracle.frozen_source_bytes) {
    for(const source of [payload.entry,...payload.modules])
      assert.equal(source.source,(await readFile(path.join(root,'docs/language-design/surface-v0.1',source.filename))).toString('utf8'));
  }
  return {directory,bytes,document,binary,metadata,exportReport,reference,oracle,manifest,revision,
    provenance,tolerances,artifactHash:provenance.glb.sha256};
}

function triangleKey(indices) {
  return [indices,indices.slice(1).concat(indices[0]),indices.slice(2).concat(indices.slice(0,2))]
    .map(v=>v.join(':')).sort()[0];
}
function addCount(map,key) {map.set(key,(map.get(key)??0)+1);}
export function analyticMesh(shape) {
  const sections=[...shape.sections].sort((a,b)=>a.station_m-b.station_m),n=shape.facets;
  const points=sections.flatMap(s=>Array.from({length:n},(_,j)=>[
    s.center_xy_m[0]+s.radii_xy_m[0]*Math.cos(2*Math.PI*j/n),
    s.center_xy_m[1]+s.radii_xy_m[1]*Math.sin(2*Math.PI*j/n),s.station_m]));
  const triangles=[];
  for(let s=0;s<sections.length-1;s++) for(let j=0;j<n;j++) {
    const a=s*n+j,b=s*n+(j+1)%n,c=(s+1)*n+j,d=(s+1)*n+(j+1)%n;
    triangles.push({region:sections[s].region,indices:[a,b,c]},{region:sections[s].region,indices:[b,d,c]});
  }
  if(shape.caps==='flat') {
    const lo=sections[0],hi=sections.at(-1),l=points.length,u=l+1;
    points.push([...lo.center_xy_m,lo.station_m],[...hi.center_xy_m,hi.station_m]);
    for(let j=0;j<n;j++) {
      triangles.push({region:lo.region,indices:[l,(j+1)%n,j]},
        {region:hi.region,indices:[u,(sections.length-1)*n+j,(sections.length-1)*n+(j+1)%n]});
    }
  }
  return {sections,triangles,points:points.map(p=>transform(p,shape.local_rotation_wxyz,shape.local_position_m))};
}

export function verifyGeometry(state,shape) {
  const {document,binary}=state,expected=analyticMesh(shape),tolerance=1e-5;
  const nodes=document.nodes.filter(n=>n.extras?.ontokin?.kind==='object'&&n.extras.ontokin.path===shape.path);
  assert.equal(nodes.length,1,shape.path+' one carrier identity'); const node=nodes[0],metadata=node.extras.ontokin;
  assert.deepEqual(metadata.element_id,shape.element_id);
  const physicalKind=shape.physical_kind??'no_body';
  assert.ok(['no_body','sphere_body'].includes(physicalKind));
  assert.equal(metadata.physical.kind,physicalKind);
  assert.equal(metadata.program_revision,state.revision);
  assert.deepEqual(metadata.source_mapping.element_id,shape.element_id);
  for(const part of ['definition','declaration']) {
    const mapping=metadata.source_mapping[part],source=state.manifest.units.find(u=>u.source_id===mapping.source_id);
    assert.ok(source);assert.equal(mapping.source_revision,source.source_revision);
    assert.ok(Number.isInteger(mapping.start_byte)&&mapping.end_byte>mapping.start_byte);
  }
  const mesh=document.meshes[node.mesh],primitives=mesh.primitives;
  const regions=[...new Set(expected.triangles.map(t=>t.region))].sort();
  assert.equal(primitives.length,regions.length,'One logical mesh has all used material regions');
  assert.deepEqual(primitives.map(p=>p.extras?.ontokin?.region_key).sort(),regions);
  assert.equal(new Set(primitives.map(p=>p.material)).size,regions.length,'Source region identities cannot merge by equal PBR factors');
  const surface=metadata.surface;
  assert.equal(surface.physical_participation,'none','A native visual cannot add physical matter');
  assert.equal(surface.profile,'surface-0.1');assert.deepEqual(surface.section_keys,expected.sections.map(s=>s.key));
  assert.deepEqual(surface.stations_m,expected.sections.map(s=>s.station_m));
  assert.equal(surface.facets,shape.facets);assert.equal(surface.caps,shape.caps);
  assert.equal(surface.triangle_count,expected.triangles.length);assert.equal(surface.vertex_count,expected.triangles.length*3);
  assert.equal(surface.local_visual_placement.frame,'carrier_self_frame');
  vectorError(surface.local_visual_placement.position_m,shape.local_position_m,1e-12,'Declared local visual position');
  assert.ok(rotationError(quat(surface.local_visual_placement.orientation_wxyz).toArray(),quat(shape.local_rotation_wxyz).toArray())<=1e-12);
  assert.ok(state.manifest.units.some(u=>u.source_id===surface.source_location.source_id));
  assert.ok(surface.source_location.start_byte>=0&&surface.source_location.end_byte>surface.source_location.start_byte);
  assert.equal(state.metadata.surface_delivery.material_policy,'one_primitive_per_used_source_region');
  assert.equal(state.metadata.surface_delivery.placement_policy,'baked_once_in_carrier_local_vertices_and_normals');
  assert.ok(state.metadata.surface_delivery.local_vertex_tolerance_m<=tolerance);
  const buckets=new Map(),key=p=>p.map(n=>Math.floor(n/tolerance)).join(',');
  expected.points.forEach((p,i)=>{const k=key(p);buckets.set(k,[...(buckets.get(k)??[]),i]);});
  let maxPositionError=0,maxNormalLengthError=0,volume=0,expectedVolume=0,volumeErrorBound=0;
  const positionIds=new Set(),usedCorners=new Set(),positionPayload=[],materialRecords=[],triangleRecords=[],decodedPoints=new Map();
  function identify(point) {
    const bin=point.map(n=>Math.floor(n/tolerance)),matches=[];
    for(let x=-1;x<=1;x++)for(let y=-1;y<=1;y++)for(let z=-1;z<=1;z++)
      for(const i of buckets.get([bin[0]+x,bin[1]+y,bin[2]+z].join(','))??[]) {
        const error=Math.max(...point.map((v,axis)=>Math.abs(v-expected.points[i][axis])));
        if(error<=tolerance) matches.push([i,error]);
      }
    assert.equal(matches.length,1,`Each decoded vertex must match exactly one independent analytic ring/cap point: ${point}`);
    maxPositionError=Math.max(maxPositionError,matches[0][1]);decodedPoints.set(matches[0][0],point);return matches[0][0];
  }
  const wanted=new Map();for(const triangle of expected.triangles)addCount(wanted,triangle.region+'|'+triangleKey(triangle.indices));
  const observed=new Map();
  for(const primitive of primitives) {
    const region=primitive.extras.ontokin.region_key,material=document.materials[primitive.material];
    const pbr=material.pbrMetallicRoughness,authored=shape.materials[region];
    assert.equal(material.extras.ontokin.source_region_key,region);
    assert.equal(material.extras.ontokin.occurrence_path,shape.path);
    assert.deepEqual(material.extras.ontokin.element_id,shape.element_id);
    assert.equal(material.extras.ontokin.program_revision,state.revision);
    assert.deepEqual(pbr.baseColorFactor,authored.rgba);assert.equal(pbr.metallicFactor,authored.metallic);
    assert.equal(pbr.roughnessFactor,authored.roughness);
    const positions=readAccessor(document,binary,primitive.attributes.POSITION);
    const normals=readAccessor(document,binary,primitive.attributes.NORMAL);
    const indices=readAccessor(document,binary,primitive.indices).flat();
    assert.equal(indices.length%3,0);assert.equal(normals.length,positions.length);
    if(!positionIds.has(primitive.attributes.POSITION)) {
      positionIds.add(primitive.attributes.POSITION);positionPayload.push(positions);
    }
    materialRecords.push({region,material_index:primitive.material,triangles:indices.length/3,...authored});
    const normalVectors=normals.map(n=>new THREE.Vector3(...n));
    const ids=positions.map(identify);
    for(let i=0;i<indices.length;i+=3) {
      const corners=indices.slice(i,i+3),labels=corners.map(i=>ids[i]);
      for(const corner of corners) {const id=primitive.attributes.POSITION+':'+corner;assert.ok(!usedCorners.has(id),'Flat shaded corner used exactly once');usedCorners.add(id);}
      addCount(observed,region+'|'+triangleKey(labels));
      const [a,b,c]=corners.map(i=>new THREE.Vector3(...positions[i]));
      const cross=b.clone().sub(a).cross(c.clone().sub(a));
      assert.ok(cross.length()>0,'Every decoded triangle has positive area');cross.normalize();
      for(const corner of corners) {
        const normal=normalVectors[corner],error=Math.abs(normal.length()-1);
        maxNormalLengthError=Math.max(maxNormalLengthError,error);assert.ok(error<=1e-6,'Float32 normal unit length');
        assert.ok(normal.dot(cross)>1-1e-6,'Triangle winding agrees with its outward flat normal');
      }
      volume+=a.dot(b.clone().cross(c))/6;
      const [ea,eb,ec]=labels.map(i=>new THREE.Vector3(...expected.points[i]));
      expectedVolume+=ea.dot(eb.clone().cross(ec))/6;
      const da=a.distanceTo(ea),db=b.distanceTo(eb),dc=c.distanceTo(ec);
      volumeErrorBound+=(da*eb.length()*ec.length()+ea.length()*db*ec.length()+ea.length()*eb.length()*dc+
        da*db*ec.length()+da*eb.length()*dc+ea.length()*db*dc+da*db*dc)/6;
      triangleRecords.push([region,labels]);
    }
  }
  assert.deepEqual([...observed.entries()].sort(),[...wanted.entries()].sort(),'Exact regional topology and outward winding');
  const corners=positionPayload.reduce((n,p)=>n+p.length,0);
  assert.equal(corners,expected.triangles.length*3);assert.equal(usedCorners.size,corners);
  if(shape.expected.triangles!==undefined)assert.equal(expected.triangles.length,shape.expected.triangles);
  if(shape.expected.vertices!==undefined)assert.equal(corners,shape.expected.vertices);
  if(shape.expected.triangles_per_region)assert.deepEqual(Object.fromEntries(materialRecords.map(r=>[r.region,r.triangles])),shape.expected.triangles_per_region);
  assert.deepEqual(surface.regions.map(r=>({key:r.key,material_key:r.material_key,triangle_count:r.triangle_count})),
    materialRecords.map(r=>({key:r.region,material_key:r.region,triangle_count:r.triangles})));
  const result={path:shape.path,triangles:expected.triangles.length,vertices:corners,
    ordered_keys:expected.sections.map(s=>s.key),regions:materialRecords,
    max_local_float32_error_m:maxPositionError,max_float32_normal_length_error:maxNormalLengthError,
    positions_sha256:sha256(Buffer.from(stable(positionPayload))),topology_sha256:sha256(Buffer.from(stable(triangleRecords))),
    local_placement_applied_once:true,physical_kind:metadata.physical.kind};
  if(shape.caps==='flat') {
    assert.ok(volume>0);assert.ok(Math.abs(volume-expectedVolume)<=volumeErrorBound+1e-12);
    if(shape.expected.volume_m3!==undefined)assert.ok(Math.abs(expectedVolume-shape.expected.volume_m3)<=1e-9);
    result.closed_volume={decoded_m3:volume,analytic_polygon_m3:expectedVolume,error_m3:Math.abs(volume-expectedVolume),
      float32_perturbation_bound_m3:volumeErrorBound,note:'The frozen 1e-9 m3 unencoded oracle is checked independently; float32 delivery uses its measured determinant perturbation bound.'};
  }
  if(shape.expected.radial_sagitta_m!==undefined) {
    const s=expected.sections[0],radius=s.radii_xy_m[0],midpoint=new THREE.Vector3(...expected.points[0])
      .add(new THREE.Vector3(...expected.points[1])).multiplyScalar(.5);
    const sagitta=radius-Math.hypot(midpoint.x-s.center_xy_m[0],midpoint.y-s.center_xy_m[1]);
    assert.ok(Math.abs(sagitta-shape.expected.radial_sagitta_m)<=1e-12);assert.ok(sagitta<=.01);
    const decodedMidpoint=new THREE.Vector3(...decodedPoints.get(0)).add(new THREE.Vector3(...decodedPoints.get(1)))
      .multiplyScalar(.5).sub(new THREE.Vector3(...shape.local_position_m)).applyQuaternion(quat(shape.local_rotation_wxyz).invert());
    const decodedSagitta=radius-Math.hypot(decodedMidpoint.x-s.center_xy_m[0],decodedMidpoint.y-s.center_xy_m[1]);
    assert.ok(Math.abs(decodedSagitta-sagitta)<=Math.sqrt(2)*maxPositionError+1e-12);
    result.circle_sagitta={analytic_m:sagitta,decoded_m:decodedSagitta,error_m:Math.abs(decodedSagitta-sagitta),
      float32_perturbation_bound_m:Math.sqrt(2)*maxPositionError};
  }
  return result;
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
  const geometry=state.oracle.shapes.map(shape=>verifyGeometry(state,shape));
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
    samples.push({time_seconds:time,objects:poses});
  }
  return {fixture:state.oracle.fixture,status:'passed',case_ids:state.oracle.case_ids,
    program_revision:state.revision,artifact_sha256:state.artifactHash,provenance:state.provenance,
    exporter_source_code_sha256:state.exportReport.source_code_sha256,
    khronos:{version:validator.version(),errors:format.issues.numErrors,warnings:format.issues.numWarnings,
      infos:format.issues.numInfos,hints:format.issues.numHints,messages:format.issues.messages},
    geometry,three_js:{version:THREE.REVISION,materials:decodedMaterials,world_pose_comparisons:samples.length*expectedObjects.length,samples}};
}

async function main() {
  const args=process.argv.slice(2);let demoDir,output;
  for(let i=0;i<args.length;i++) {
    if(args[i]==='--help') {console.log('Usage: node tools/verify_surface_native.mjs --demo-dir DIR --output FILE');return;}
    assert.ok(['--demo-dir','--output'].includes(args[i]));assert.ok(args[i+1]);
    const option=args[i],value=path.resolve(args[++i]);if(option==='--demo-dir')demoDir=value;else output=value;
  }
  assert.ok(demoDir&&output,'Both --demo-dir and --output are required');
  const buildBytes=await readFile(path.join(demoDir,'build.json')),build=json(buildBytes);
  const tooling=json(await readFile(path.join(root,'tools/package.json')));
  assert.equal(validator.version(),tooling.devDependencies['gltf-validator']);
  assert.equal(json(await readFile(path.join(root,'tools/node_modules/three/package.json'))).version,tooling.devDependencies.three);
  const results=[],report={schema_version:'ontokin.surface-native-destination-validation/0.1',status:'running',
    generated_at_utc:new Date().toISOString(),build_sha256:sha256(buildBytes),git_revision:build.git_revision,
    working_tree_changes:build.working_tree_changes,verifier_sha256:sha256(await readFile(fileURLToPath(import.meta.url))),
    tooling_lock_sha256:sha256(await readFile(path.join(root,'tools/package-lock.json'))),
    environment:{node:process.version,platform:process.platform,architecture:process.arch,
      three:tooling.devDependencies.three,khronos_gltf_validator:validator.version()},fixtures:results,
    limits:['These source/export checks cover named fixture aspects, not complete M01--M12 or agent/0.3 acceptance.',
      'Sampled poses and declared local float32 tolerances do not certify all programs or every continuous time.',
      'Blender, external game engines, live physics and authoring-productivity benchmarks were not executed.']};
  try {
    for(const item of build.fixtures) {
      const result=await verifyCase(path.join(demoDir,item.fixture));
      assert.equal(result.program_revision,item.program_revision);assert.equal(result.artifact_sha256,item.artifact_sha256);
      results.push(result);
    }
    const paletteEdits=build.palette_edits??[{before_fixture:'regional-materials',
      after_fixture:'regional-materials-edited',path:'shell',region:'middle'}];
    assert.ok(Array.isArray(paletteEdits)&&paletteEdits.length>0);
    report.palette_edits=[];
    for(const edit of paletteEdits) {
      const before=results.find(r=>r.fixture===edit.before_fixture),after=results.find(r=>r.fixture===edit.after_fixture);
      assert.ok(before&&after,'Both independently decoded palette revisions must be present');
      assert.notEqual(before.program_revision,after.program_revision);
      assert.deepEqual(before.geometry.map(g=>g.path).sort(),after.geometry.map(g=>g.path).sort());
      let changed=false;
      for(const oldShape of before.geometry) {
        const newShape=after.geometry.find(g=>g.path===oldShape.path);
        assert.equal(oldShape.positions_sha256,newShape.positions_sha256);
        assert.equal(oldShape.topology_sha256,newShape.topology_sha256);
        assert.deepEqual(oldShape.regions.map(r=>r.region).sort(),newShape.regions.map(r=>r.region).sort());
        for(const previous of oldShape.regions) {
          const current=newShape.regions.find(r=>r.region===previous.region);
          if(oldShape.path===edit.path&&previous.region===edit.region) {
            const factors=r=>({rgba:r.rgba,metallic:r.metallic,roughness:r.roughness});
            assert.notDeepEqual(factors(current),factors(previous),'The authored target PBR region must actually change');
            assert.equal(current.triangles,previous.triangles);changed=true;
          } else assert.deepEqual(current,previous,'Untargeted sibling and regional material must remain unchanged');
        }
      }
      assert.ok(changed,'The isolated palette target must name an actual source region');
      report.palette_edits.push({...edit,status:'passed',geometry_unchanged:true,only_target_material_changed:true});
    }
    report.palette_variant={status:'passed',geometry_unchanged:true,
      ...(paletteEdits.length===1&&paletteEdits[0].region==='middle'
        ?{only_middle_material_changed:true}:{only_target_materials_changed:true}),
      note:'Source/decoded-artifact comparison; actual atomic edit and request evidence is retained separately.'};
    report.status='passed';
  } catch(error) {report.status='failed';report.failure={name:error.name,message:error.message};throw error;}
  finally {await mkdir(path.dirname(output),{recursive:true});await writeFile(output,JSON.stringify(report,null,2)+'\n');}
  console.log(JSON.stringify({status:report.status,fixtures:results.length,
    world_pose_comparisons:results.reduce((s,r)=>s+r.three_js.world_pose_comparisons,0),output},null,2));
}

if(process.argv[1]&&pathToFileURL(path.resolve(process.argv[1])).href===import.meta.url)await main();
