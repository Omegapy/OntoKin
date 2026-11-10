import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import * as THREE from 'three';
import {GLTFLoader} from '../indexer-view/three/examples/jsm/loaders/GLTFLoader.js';
const [kit,manifest,destination]=process.argv.slice(2);
const root=path.resolve(kit), entries=JSON.parse(fs.readFileSync(manifest,'utf8'));
const expected=['base','left_carriage','left_shoe','left_stop','right_carriage','right_shoe','right_stop'].sort();
const reports=[];
for(const entry of entries) {
  const data=fs.readFileSync(path.join(root,entry.path));
  const gltf=await new GLTFLoader().parseAsync(data.buffer.slice(data.byteOffset,data.byteOffset+data.byteLength),'');
  const meshes={};
  gltf.scene.traverse(o=>{if(o.isMesh)meshes[o.name]=o});
  if(JSON.stringify(Object.keys(meshes).sort())!==JSON.stringify(expected))throw Error('Unexpected mesh identities '+entry.id);
  const mixer=new THREE.AnimationMixer(gltf.scene);
  const actions=gltf.animations.map(clip=>{const a=mixer.clipAction(clip);a.setLoop(THREE.LoopOnce,1);a.clampWhenFinished=true;return a});
  const duration=Math.max(...gltf.animations.map(c=>c.duration));
  if(duration!==2)throw Error('Unexpected duration');
  const poses=[];
  for(const time of [0,entry.idealContactS,2]) {
    actions.forEach(a=>a.reset().play());mixer.setTime(time);gltf.scene.updateMatrixWorld(true);
    const bounds={};
    for(const [name,mesh] of Object.entries(meshes)) {
      mesh.geometry.computeBoundingBox();
      const b=mesh.geometry.boundingBox.clone().applyMatrix4(mesh.matrixWorld);
      bounds[name]=[b.min.toArray().map(x=>1000*x),b.max.toArray().map(x=>1000*x)];
    }
    const gaps={left:bounds.left_stop[0][0]-bounds.left_shoe[1][0],right:bounds.right_stop[0][0]-bounds.right_shoe[1][0]};
    if(time===2&&Math.abs(gaps.right-15)>.001)throw Error('Wrong right clearance');
    if(time===2&&Math.abs(gaps.left-entry.expectedLeftFinalGapMm)>.5)throw Error('Wrong final left gap for '+entry.id);
    poses.push({time,boundsMm:bounds,gapsMm:gaps});
  }
  reports.push({...entry,sha256:crypto.createHash('sha256').update(data).digest('hex'),meshNames:Object.keys(meshes).sort(),duration,poses});
}
fs.writeFileSync(destination,JSON.stringify({threeRevision:THREE.REVISION,node:process.version,scope:'Independent Three.js decoder and animation mixer; no browser or GPU-rendering claim',pass:true,reports},null,2)+'\n');
console.log(JSON.stringify({threeRevision:THREE.REVISION,clips:reports.length,poses:reports.length*3,pass:true}));
