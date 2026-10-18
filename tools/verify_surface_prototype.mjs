// Independent Khronos and Three.js verification of *prototype-only* multi-PBR GLB.
import {readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import validator from 'gltf-validator';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';

const args=process.argv.slice(2);
const file=args[0];
if(!file) throw new Error('Supply a .glb path');
const outIndex=args.indexOf('--output');
const output=outIndex===-1?null:args[outIndex+1];
const bytes=await readFile(file);
const docLength=bytes.readUInt32LE(12);
const doc=JSON.parse(bytes.subarray(20,20+docLength).toString('utf8'));
if(doc.extras?.ontokin?.prototype_only!==true || doc.extras.ontokin.not_ontokin_glb_0_3!==true)
  throw new Error('This validator is only for explicitly labeled research prototypes.');
const format=await validator.validateBytes(new Uint8Array(bytes),{uri:'offset-taper.glb',maxIssues:500});
const gltf=await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'');
const meshes=[];
gltf.scene.traverse(node => {if(node.isMesh) meshes.push(node);});
const actual=meshes.map(node=>({
  name:node.name,
  triangles:node.geometry.index?node.geometry.index.count/3:node.geometry.attributes.position.count/3,
  color:node.material.color.toArray(),
  metallic:node.material.metalness,roughness:node.material.roughness
}));
const triangleCounts=actual.map(x=>x.triangles).sort((a,b)=>a-b);
const materialRecords=doc.meshes[0].primitives.map(p=>({
  name:p.extras?.ontokin?.region_key,
  rgba:doc.materials[p.material].pbrMetallicRoughness.baseColorFactor,
  metallic:doc.materials[p.material].pbrMetallicRoughness.metallicFactor,
  roughness:doc.materials[p.material].pbrMetallicRoughness.roughnessFactor
}));
const expected=["base","middle","tip"];
if(format.issues.numErrors || format.issues.numWarnings) throw new Error(JSON.stringify(format.issues.messages));
if(actual.length!==3 || JSON.stringify(triangleCounts)!==JSON.stringify([16,32,48]))
  throw new Error('Three.js decoded incorrect regional meshes/counts: '+JSON.stringify(actual));
if(JSON.stringify(materialRecords.map(r=>r.name))!==JSON.stringify(expected))
  throw new Error('glTF primitive region keys differ from expected source recipe.');
if(JSON.stringify(materialRecords.map(r=>r.rgba))!==
  JSON.stringify([[0.6,0.3,0.2,1],[0.1,0.4,0.8,1],[0.8,0.8,0.8,1]]))
  throw new Error('Decoded per-primitive PBR factors are incorrect.');
const report={
 schema:"ontokin.surface-prototype-validation/0.1",
 status:"passed",native_source_support:false,
 artifact_sha256:"sha256:"+createHash('sha256').update(bytes).digest('hex'),
 khronos:{errors:format.issues.numErrors,warnings:format.issues.numWarnings},
 three_js:{decoded_meshes:actual.length,triangles:triangleCounts},
 material_records:materialRecords
};
if(output)await writeFile(output,JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
