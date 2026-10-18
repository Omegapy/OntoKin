// Independent format validation and Three.js animation loading for real GLBs.
import {readFile, readdir, writeFile} from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import validator from 'gltf-validator';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {AnimationMixer, LoopOnce, Vector3, Quaternion, REVISION} from 'three';

const args = process.argv.slice(2);
const outputIndex = args.indexOf('--output');
const output = outputIndex === -1 ? null : args[outputIndex + 1];
if (outputIndex !== -1) args.splice(outputIndex, 2);
const directory = args[0] || path.resolve('examples/visual');
const files = (await readdir(directory)).filter(name => name.endsWith('.glb')).sort();
if (!files.length) throw new Error(`No GLB files in ${directory}`);
const reports = [];
function orientationError(a, b) {
  a = a.map(v => v/Math.hypot(...a)); b = b.map(v => v/Math.hypot(...b));
  if (a.reduce((dot,v,i) => dot+v*b[i],0)<0) b = b.map(v => -v);
  return 4*Math.atan2(Math.hypot(...a.map((v,i) => v-b[i])),Math.hypot(...a.map((v,i) => v+b[i])));
}
for (const file of files) {
  const bytes = await readFile(path.join(directory, file));
  const reference = JSON.parse(await readFile(path.join(directory,file.replace(/\.glb$/,'.reference.json')),'utf8'));
  const sha256 = createHash('sha256').update(bytes).digest('hex');
  if (reference.artifact_sha256 !== 'sha256:' + sha256) throw new Error(`Reference/artifact hash mismatch: ${file}`);
  const jsonSize = bytes.readUInt32LE(12);
  const document = JSON.parse(bytes.subarray(20,20+jsonSize).toString('utf8'));
  const metadata = document.extras.ontokin;
  const program = reference.schema_version === 'ontokin.viewer-reference/0.2';
  if (program) {
    if (metadata.target_contract !== 'ontokin.glb/0.2' || metadata.profile !== 'construction-0.1' || metadata.program.revision !== reference.program_revision ||
        JSON.stringify(metadata.program.manifest) !== JSON.stringify(reference.source_manifest)) throw new Error(`Program/source manifest mismatch: ${file}`);
  } else if (metadata.source.revision !== reference.source_revision) throw new Error(`Source revision mismatch: ${file}`);
  const format = await validator.validateBytes(new Uint8Array(bytes), {uri: file, maxIssues: 200});
  const gltf = await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength), '');
  const clip = gltf.animations[0];
  const mixer = new AnimationMixer(gltf.scene);
  if (clip) mixer.clipAction(clip).setLoop(LoopOnce, 1).play().clampWhenFinished = true;
  const geometry = [];
  if (program) {
    for (const expected of reference.geometry) {
      const matches = [];
      gltf.scene.traverse(node => {if(node.userData.ontokin?.kind==='object' && node.userData.ontokin.path===expected.path) matches.push(node);});
      if (matches.length!==1) throw new Error(`Missing/ambiguous geometry occurrence: ${expected.path}`);
      const node=matches[0];
      if (!node.geometry) throw new Error(`Expected a real loaded mesh: ${expected.path}`);
      node.geometry.computeBoundingBox();
      const size=node.geometry.boundingBox.getSize(new Vector3()).toArray();
      const wanted=expected.geometry.kind==='box'?expected.geometry.size_m:Array(3).fill(2*expected.geometry.radius_m);
      const error=Math.max(...size.map((v,i)=>Math.abs(v-wanted[i])));
      if(error>1e-6) throw new Error(`Decoded mesh dimensions differ for ${expected.path}: ${size} versus ${wanted}`);
      if(JSON.stringify(node.userData.ontokin.element_id)!==JSON.stringify(expected.element_id)) throw new Error(`Decoded occurrence identity mismatch: ${expected.path}`);
      geometry.push({path:expected.path,kind:expected.geometry.kind,decoded_full_size_m:size,expected_full_size_m:wanted,max_dimension_error_m:error,status:'passed'});
    }
  }
  const samples = [];
  let maxPosition = 0, maxRotation = 0, comparisons = 0;
  const failures = [];
  for (const expected of reference.samples) {
    const time = Number(expected.time_seconds);
    mixer.setTime(time);
    gltf.scene.updateMatrixWorld(true);
    const objects = {};
    gltf.scene.traverse(node => {
      const metadata = node.userData.ontokin;
      if (metadata?.kind !== 'object') return;
      const position = node.getWorldPosition(new Vector3());
      const rotation = node.getWorldQuaternion(new Quaternion());
      objects[metadata.path || node.name] = {position_m: position.toArray(), orientation_xyzw: rotation.toArray()};
    });
    if (JSON.stringify(Object.keys(objects).sort()) !== JSON.stringify(Object.keys(expected.objects).sort())) throw new Error(`Object mapping mismatch in ${file}`);
    for (const [name, object] of Object.entries(objects)) {
      const actualPositionError = Math.max(...object.position_m.map((value,i) => Math.abs(value-expected.objects[name].position_m[i])));
      const [w,x,y,z] = expected.objects[name].orientation_wxyz;
      const actualRotationError = orientationError(object.orientation_xyzw,[x,y,z,w]);
      maxPosition = Math.max(maxPosition,actualPositionError); maxRotation = Math.max(maxRotation,actualRotationError); comparisons++;
      if (actualPositionError > reference.tolerances.position_m || actualRotationError > reference.tolerances.rotation_rad) failures.push({object:name,time_seconds:time,position_error_m:actualPositionError,rotation_error_rad:actualRotationError});
    }
    samples.push({time_seconds: time, objects});
  }
  reports.push({file, sha256, ...(program?{program_revision:reference.program_revision,source_manifest:reference.source_manifest,geometry}:{source_revision:reference.source_revision}),
    validator: {version: validator.version(), errors: format.issues.numErrors, warnings: format.issues.numWarnings,
      infos: format.issues.numInfos, hints: format.issues.numHints, messages: format.issues.messages},
    three_js: {revision: REVISION, loaded: true, animation_count: gltf.animations.length,
      duration_seconds: clip?.duration || 0, comparison: {status:failures.length?'failed':'passed',
        sample_count:samples.length,object_pose_comparisons:comparisons,max_position_error_m:maxPosition,max_rotation_error_rad:maxRotation,
        tolerances:reference.tolerances,failures}, samples}});
}
const report = {schema_version: 'ontokin.external-validation/0.1',
  scope: 'Khronos structural validation and independently decoded Three.js playback compared with fresh evaluator reference samples; no Blender result is claimed.',
  files: reports};
if (output) await writeFile(output, JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify({files: reports.length, errors: reports.reduce((n,r) => n+r.validator.errors,0),
  warnings: reports.reduce((n,r) => n+r.validator.warnings,0), loaded_in_three: reports.every(r => r.three_js.loaded),
  numerical_comparisons:reports.reduce((n,r) => n+r.three_js.comparison.object_pose_comparisons,0),
  numerical_passed:reports.every(r => r.three_js.comparison.status === 'passed'),output}, null, 2));
if (reports.some(report => report.validator.errors || report.validator.warnings || report.three_js.comparison.status !== 'passed')) process.exitCode = 1;
