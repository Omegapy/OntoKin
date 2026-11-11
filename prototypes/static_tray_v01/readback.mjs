/* Read-only Khronos/Three.js inspection of one retained static-tray GLB.
 * This imports actual delivered bytes. It never builds or exports geometry.
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';

const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const stable = value => JSON.stringify(canonical(value));
function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (value && typeof value === 'object') return Object.fromEntries(Object.keys(value).sort().map(k => [k, canonical(value[k])]));
  return value;
}
function readBound(filename, maximum) {
  const info = fs.lstatSync(filename);
  if (!info.isFile() || info.size > maximum) throw Error('Unsafe or over-limit input: ' + filename);
  const fd = fs.openSync(filename, 'r');
  try {
    const buffer = Buffer.alloc(maximum + 1);
    const length = fs.readSync(fd, buffer, 0, buffer.length, 0);
    if (length > maximum) throw Error('Input exceeds its byte limit');
    return buffer.subarray(0, length);
  } finally { fs.closeSync(fd); }
}
function output(filename, value) {
  const data = Buffer.from(JSON.stringify(value, null, 2) + '\n');
  if (data.length > 4 * 1024 * 1024) throw Error('Readback result exceeds 4 MiB');
  const fd = fs.openSync(filename, 'wx');
  try { fs.writeFileSync(fd, data); fs.fsyncSync(fd); } finally { fs.closeSync(fd); }
}
function finite(values) { return values.every(Number.isFinite); }
function matrixRows(matrix) {
  return [0, 1, 2, 3].map(i => [0, 1, 2, 3].map(j => matrix.elements[j * 4 + i]));
}

const args = process.argv.slice(2);
if (args.length !== 2 || args[0] !== '--job') throw Error('Expected exactly --job FILE');
const job = JSON.parse(readBound(args[1], 32768));
const report = { schema: 'ontokin.static-tray.external-readback/0.1.0', passed: false,
  slot: job.slot, case: job.case, input_lock_sha256: job.input_lock_sha256,
  supplemental_manifest_sha256: job.supplemental_manifest_sha256,
  artifact_sha256: job.artifact_sha256, audit_sha256: job.audit_sha256,
  node: process.version, native_starts: 0, exports: 0,
  scope: 'Khronos format validation and Three.js CPU importer readback; no browser, GPU, simulation or render claim' };
try {
  if (process.version !== 'v24.22.1') throw Error('Node runtime version differs from the selected executable');
  const manifestBytes = readBound(job.manifest, 1024 * 1024);
  if (sha(manifestBytes) !== job.supplemental_manifest_sha256) throw Error('Supplemental manifest identity differs');
  const manifest = JSON.parse(manifestBytes);
  if (manifest.schema !== 'ontokin.static-tray.external-readback-lock/0.1.0') throw Error('Wrong supplemental manifest');
  const bytes = readBound(job.artifact, 8 * 1024 * 1024);
  const auditBytes = readBound(job.audit, 4 * 1024 * 1024);
  if (sha(bytes) !== job.artifact_sha256 || sha(auditBytes) !== job.audit_sha256) throw Error('Actual input identity differs');
  const audit = JSON.parse(auditBytes);
  if (audit.passed !== true || audit.artifact_sha256 !== sha(bytes) || audit.case !== job.case) throw Error('Independent passed audit does not bind this actual GLB');

  // No external fetch is an admitted part of this finite static delivery.
  globalThis.fetch = async () => { throw Error('External resource fetch is forbidden'); };
  const require = createRequire(import.meta.url);
  const validator = require(manifest.validator_entry);
  if (validator.version() !== '2.0.0-dev.3.10') throw Error('Khronos validator version differs');
  const khronos = await validator.validateBytes(new Uint8Array(bytes), {
    uri: 'final.glb', format: 'glb', writeTimestamp: false, maxIssues: 1000,
    externalResourceFunction: async () => { throw Error('External resources are forbidden'); }
  });
  report.khronos = { version: validator.version(), passed: khronos.issues.numErrors === 0 && khronos.issues.numWarnings === 0 && !khronos.issues.truncated,
    report: khronos };
  if (!report.khronos.passed) throw Error('Khronos validation reported an error, warning or truncated result');

  const THREE = await import(pathToFileURL(manifest.three_entry).href);
  const { GLTFLoader } = await import(pathToFileURL(manifest.gltf_loader_entry).href);
  const packageInfo = JSON.parse(readBound(manifest.three_package, 32768));
  if (packageInfo.version !== '0.186.1' || THREE.REVISION !== '186') throw Error('Three.js dependency version differs');
  const manager = new THREE.LoadingManager();
  manager.setURLModifier(() => { throw Error('External Three.js resource resolution is forbidden'); });
  const gltf = await new GLTFLoader(manager).parseAsync(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength), '');
  if (gltf.scenes.length !== 1 || gltf.animations.length || gltf.cameras.length) throw Error('Unexpected imported scenes, animation or cameras');
  gltf.scene.updateMatrixWorld(true);
  const nodes = {}, objects = [], findings = [], measurements = [];
  const exact = (id, field, actual, expected) => {
    if (stable(actual) !== stable(expected)) findings.push({ semantic_id: id, field, actual, expected });
  };
  const near = (id, field, actual, expected, threshold) => {
    const difference = Math.abs(actual - expected);
    const passed = Number.isFinite(actual) && Number.isFinite(expected) && difference <= threshold;
    measurements.push({ semantic_id: id, field, actual, expected, difference, threshold, passed });
    if (!passed) findings.push({ semantic_id: id, field, actual, expected, difference, threshold });
  };
  const idOf = object => Array.isArray(object.userData?.semantic_id) ? object.userData.semantic_id.join('/') : null;
  gltf.scene.traverse(object => {
    if (object === gltf.scene) return;
    const id = idOf(object);
    if (!id || nodes[id]) throw Error('Unbound or duplicate Three.js object identity');
    nodes[id] = object;
    objects.push(id);
  });
  exact('', 'node_identity_inventory', Object.keys(nodes).sort(), Object.keys(audit.nodes).sort());
  exact('', 'node_count', objects.length, 14);
  let meshes = 0;
  const retained = {};
  for (const id of objects.sort()) {
    const object = nodes[id], reference = audit.nodes[id];
    if (!reference) continue;
    if (object.isLight || object.isCamera || object.isSkinnedMesh || object.morphTargetInfluences?.length) throw Error('Unsupported Three.js object');
    const extras = { ...object.userData };
    const originalName = extras.name;
    delete extras.name;
    exact(id, 'original_name', originalName, id);
    exact(id, 'semantic_role_relationships', extras, reference.extras);
    exact(id, 'children', object.children.map(idOf).sort(), reference.children.slice().sort());
    exact(id, 'parent', object.parent === gltf.scene ? null : idOf(object.parent), reference.extras.role === 'tray-root' ? null : reference.extras.owner_id.join('/'));
    const worldMatrix = matrixRows(object.matrixWorld);
    for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) near(id, `matrix_${i}_${j}`, worldMatrix[i][j], reference.world_matrix[i][j], j === 3 && i < 3 ? 0.000005 : 0.000001);
    const data = retained[id] = { original_name: originalName, importer_name: object.name, extras, world_matrix: worldMatrix,
      children: object.children.map(idOf).sort(), parent: object.parent === gltf.scene ? null : idOf(object.parent) };
    if (!reference.world_vertices) {
      exact(id, 'empty_root', Boolean(object.isMesh), false);
      continue;
    }
    meshes++;
    if (!object.isMesh || Array.isArray(object.material)) throw Error('Expected one mesh and material per tray part');
    const geometry = object.geometry, position = geometry.getAttribute('position'), normal = geometry.getAttribute('normal'), index = geometry.getIndex();
    if (!position || !normal || !index || position.count > 4096 || normal.count !== position.count || index.count !== 36) throw Error('Unsupported imported vertex/index layout');
    exact(id, 'vertex_count', position.count, reference.world_vertices.length);
    const positions = [], normals = [], vertices = [];
    for (let i = 0; i < position.count; i++) {
      const p = [position.getX(i), position.getY(i), position.getZ(i)], n = [normal.getX(i), normal.getY(i), normal.getZ(i)];
      if (!finite(p) || !finite(n)) throw Error('Nonfinite imported geometry');
      const world = new THREE.Vector3(...p).applyMatrix4(object.matrixWorld).toArray();
      positions.push(p); normals.push(n); vertices.push(world);
      for (let axis = 0; axis < 3; axis++) {
        near(id, `world_vertex_${i}_${axis}`, world[axis], reference.world_vertices[i][axis], 0.000005);
        near(id, `normal_${i}_${axis}`, n[axis], reference.normals[i][axis], 0.000001);
      }
    }
    const indices = Array.from({ length: index.count }, (_, i) => index.getX(i));
    exact(id, 'actual_triangle_indices', indices, reference.indices);
    const material = { name: object.material.name, baseColorFactor: [...object.material.color.toArray(), object.material.opacity],
      metallicFactor: object.material.metalness, roughnessFactor: object.material.roughness,
      alphaMode: object.material.transparent ? 'BLEND' : object.material.alphaTest > 0 ? 'MASK' : 'OPAQUE',
      doubleSided: object.material.side === THREE.DoubleSide };
    exact(id, 'material', material, reference.material);
    for (const name of ['map', 'normalMap', 'roughnessMap', 'metalnessMap', 'alphaMap', 'emissiveMap', 'aoMap']) if (object.material[name]) throw Error('Unexpected imported texture');
    const bounds = [0, 1].map(upper => [0, 1, 2].map(axis => (upper ? Math.max : Math.min)(...vertices.map(v => v[axis]))));
    const expectedBounds = [0, 1].map(upper => [0, 1, 2].map(axis => (upper ? Math.max : Math.min)(...reference.world_vertices.map(v => v[axis]))));
    for (let axis = 0; axis < 3; axis++) {
      near(id, `world_min_${axis}`, bounds[0][axis], expectedBounds[0][axis], 0.000005);
      near(id, `world_max_${axis}`, bounds[1][axis], expectedBounds[1][axis], 0.000005);
      near(id, `world_size_${axis}`, bounds[1][axis] - bounds[0][axis], expectedBounds[1][axis] - expectedBounds[0][axis], 0.000005);
    }
    Object.assign(data, { positions, normals, world_vertices: vertices, indices, material, world_bounds: bounds });
  }
  exact('', 'mesh_count', meshes, 12);
  findings.sort((a, b) => a.semantic_id.localeCompare(b.semantic_id) || a.field.localeCompare(b.field));
  report.three = { version: packageInfo.version, revision: THREE.REVISION, passed: findings.length === 0,
    node_count: objects.length, mesh_count: meshes, animations: gltf.animations.length, findings, measurements, nodes: retained,
    position_tolerance_m: 0.000005, matrix_tolerance: 0.000001,
    naming: 'Three.js sanitizes Object3D.name; original names and semantic IDs remain checked without normalization' };
  report.input_preserved = sha(readBound(job.artifact, 8 * 1024 * 1024)) === job.artifact_sha256 && sha(readBound(job.audit, 4 * 1024 * 1024)) === job.audit_sha256;
  report.passed = report.khronos.passed && report.three.passed && report.input_preserved;
} catch (error) { report.error = { code: 'OTRAY-E-DELIVERY', message: String(error.message || error) }; }
output(job.result, report);
console.log(JSON.stringify({ passed: report.passed, slot: job.slot, artifact_sha256: job.artifact_sha256,
  validator: report.khronos?.version, three: report.three?.version }));
process.exitCode = report.passed ? 0 : 1;
