// Browser-only observation harness. Receives actual GLBs and their identities,
// never source geometry arrays, reference poses, or expected trajectories.
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {attachReachPlayback} from './reach_destination.mjs';

const datasets = globalThis.REACH_ARTIFACTS;
const $ = id => document.getElementById(id), scene = new THREE.Scene();
scene.background = new THREE.Color(0xe7edf2);
const camera = new THREE.PerspectiveCamera(35, 1100 / 750, .001, 1000);
const renderer = new THREE.WebGLRenderer({antialias: true, preserveDrawingBuffer: true});
renderer.setPixelRatio(1); renderer.setSize(1100, 750); renderer.outputColorSpace = THREE.SRGBColorSpace;
$('viewport').appendChild(renderer.domElement);
scene.add(new THREE.AmbientLight(0xffffff, 1.2));
for (const [position, intensity] of [[[6, 10, 8], 2.5], [[-5, 4, -7], 1.8]]) {
  const light = new THREE.DirectionalLight(0xffffff, intensity); light.position.set(...position); scene.add(light);
}
const grid = new THREE.GridHelper(30, 30, 0x94a5b4, 0xc3cfd9); scene.add(grid);
let current, content, player, decoded, fit, keyTimes, objects = new Map();
let ready = false, playing = false, time = 0, view = 'front', last = performance.now();

function seek(value) {
  if (!Number.isFinite(value)) throw new Error('Animation time must be finite');
  time = Math.max(0, Math.min(current.end, value)); player.setTime(time);
  $('timeline').value = String(time); $('time').textContent = String(time) + ' s'; renderer.render(scene, camera);
}
function setView(next) {
  if (!['front', 'side'].includes(next)) throw new Error('Unknown camera view');
  view = next;
  const direction = (next === 'side' ? new THREE.Vector3(1, .12, 0) : new THREE.Vector3(.12, .12, 1)).normalize();
  camera.position.copy(fit.center).addScaledVector(direction, fit.distance);
  camera.near = Math.max(.001, fit.distance - fit.radius * 1.7); camera.far = fit.distance + fit.radius * 3;
  camera.up.set(0, 1, 0); camera.lookAt(fit.center); camera.updateProjectionMatrix(); camera.updateMatrixWorld(true);
  renderer.render(scene, camera);
}
function fitMotion() {
  // Native carriers are flat roots. Each rotated local vertex remains within
  // its decoded carrier radius. Linear translation remains inside adjacent
  // recorded endpoint bounds. The enlarged union therefore covers rotations
  // between observations too; no source trajectory is supplied to the browser.
  const bounds = new THREE.Box3(), radii = new Map(), point = new THREE.Vector3();
  player.setTime(0);
  for (const [name, {node}] of objects) {
    const center = node.getWorldPosition(new THREE.Vector3()); let radius = 0;
    node.traverse(child => { if (child.isMesh) {
      const positions = child.geometry.getAttribute('position');
      for (let index = 0; index < positions.count; index++)
        radius = Math.max(radius, point.fromBufferAttribute(positions, index).applyMatrix4(child.matrixWorld).distanceTo(center));
    }});
    radii.set(name, radius * (1 + 1e-12) + 1e-9);
  }
  for (const sampleTime of keyTimes) {
    player.setTime(sampleTime);
    for (const [name, {node}] of objects) {
      const center = node.getWorldPosition(new THREE.Vector3()), radius = radii.get(name);
      bounds.expandByPoint(center.clone().addScalar(radius)); bounds.expandByPoint(center.clone().addScalar(-radius));
    }
  }
  if (bounds.isEmpty() || ![...bounds.min, ...bounds.max].every(Number.isFinite)) throw new Error('Invalid native motion bounds');
  const center = bounds.getCenter(new THREE.Vector3()), radius = Math.max(bounds.getSize(new THREE.Vector3()).length() / 2, .5);
  const vertical = THREE.MathUtils.degToRad(camera.fov), horizontal = 2 * Math.atan(Math.tan(vertical / 2) * camera.aspect);
  fit = {bounds, center, radius, radii: Object.fromEntries(radii), distance: radius / Math.sin(Math.min(vertical, horizontal) / 2) * 1.15};
  grid.position.y = bounds.min.y - .02; seek(0); setView('front');
}
async function load(name) {
  ready = false; playing = false; $('play').textContent = 'Play';
  if (content) {
    scene.remove(content);
    content.traverse(child => { if (child.isMesh) {
      child.geometry.dispose();
      for (const material of Array.isArray(child.material) ? child.material : [child.material]) material.dispose();
    }});
  }
  current = datasets.find(item => item.case_id === name); if (!current) throw new Error('Unknown artifact');
  const raw = Uint8Array.from(atob(current.glb), char => char.charCodeAt(0));
  const gltf = await new GLTFLoader().parseAsync(raw.buffer, '');
  const document = gltf.parser.json, metadata = document.extras?.ontokin;
  if (metadata?.target_contract !== 'ontokin.glb/0.6' || metadata.schema_version !== '0.6') throw new Error('Unexpected delivery contract');
  player = await attachReachPlayback(gltf, {threeRevision: THREE.REVISION});
  content = gltf.scene; scene.add(content); objects = new Map();
  for (let index = 0; index < document.nodes.length; index++) {
    const identity = document.nodes[index].extras?.ontokin;
    if (!identity || objects.has(identity.path)) throw new Error('Missing or duplicate native carrier');
    objects.set(identity.path, {node: await gltf.parser.getDependency('node', index), identity});
  }
  const clock = await gltf.parser.getDependency('accessor', document.animations[0].samplers[0].input);
  keyTimes = Array.from({length: clock.count}, (_, index) => clock.getX(index));
  if (keyTimes.at(-1) !== current.end) throw new Error('Timeline horizon differs from actual stored keys');
  decoded = {target_contract: metadata.target_contract, schema_version: metadata.schema_version,
    profile: metadata.profile, program_revision: metadata.program.revision, source_manifest: metadata.program.manifest,
    player: {name: player.name, version: player.version, carrier_count: player.carrierCount}, three_revision: THREE.REVISION};
  $('revision').textContent = decoded.program_revision; $('artifact').textContent = current.artifact_sha256;
  $('fixture').value = name; $('timeline').max = String(current.end); fitMotion(); ready = true;
}
for (const item of datasets) {
  const option = document.createElement('option'); option.value = item.case_id; option.textContent = item.case_id; $('fixture').appendChild(option);
}
$('fixture').onchange = event => load(event.target.value).catch(error => { setTimeout(() => { throw error; }); });
$('timeline').oninput = event => { playing = false; $('play').textContent = 'Play'; seek(Number(event.target.value)); };
$('front').onclick = () => setView('front'); $('side').onclick = () => setView('side');
$('play').onclick = () => { if (time >= current.end) seek(0); playing = !playing; $('play').textContent = playing ? 'Pause' : 'Play'; };
function frame(now) {
  requestAnimationFrame(frame); const elapsed = Math.min((now - last) / 1000, .1); last = now;
  if (ready && playing) { seek(time + elapsed); if (time >= current.end) { playing = false; $('play').textContent = 'Play'; } }
  if (ready) renderer.render(scene, camera);
}
requestAnimationFrame(frame);
globalThis.reachViewer = {load, get ready() { return ready; }, get state() {
  const entries = [];
  for (const [name, {node, identity}] of objects) {
    const primitives = [];
    node.traverse(child => { if (child.isMesh) {
      const positions = child.geometry.getAttribute('position'), indices = child.geometry.index;
      const count = indices ? indices.count : positions.count, probes = [];
      for (const offset of [...new Set([0, Math.floor(count / 2), count - 1])]) {
        const index = indices ? indices.getX(offset) : offset;
        const local = new THREE.Vector3().fromBufferAttribute(positions, index), world = local.clone().applyMatrix4(child.matrixWorld);
        probes.push({vertex_index: index, local_m: local.toArray(), world_m: world.toArray(), camera_ndc: world.clone().project(camera).toArray()});
      }
      const material = child.material;
      primitives.push({region_key: material.userData?.ontokin?.source_region_key ?? null,
        base_color: [...material.color.toArray(), material.opacity], metallic: material.metalness, roughness: material.roughness,
        vertices: positions.count, indices: count, triangles: count / 3, probes});
    }});
    const q = node.getWorldQuaternion(new THREE.Quaternion());
    entries.push([name, {path: identity.path, kind: identity.kind, element_id: identity.element_id,
      source_mapping: identity.source_mapping, position_m: node.getWorldPosition(new THREE.Vector3()).toArray(),
      orientation_wxyz: [q.w, q.x, q.y, q.z], matrix_world: node.matrixWorld.toArray(), primitives}]);
  }
  return {case_id: current.case_id, artifact_sha256: current.artifact_sha256, time_seconds: time,
    displayed_time: $('time').textContent, playing, view, decoded, objects: Object.fromEntries(entries),
    camera: {position_m: camera.position.toArray(), orientation_xyzw: camera.quaternion.toArray(), target_m: fit.center.toArray(),
      up: camera.up.toArray(), fov_degrees: camera.fov, aspect: camera.aspect, near_m: camera.near, far_m: camera.far,
      bounds_min_m: fit.bounds.min.toArray(), bounds_max_m: fit.bounds.max.toArray(), carrier_radii_m: fit.radii,
      fit_stored_key_count: keyTimes.length, fit_policy: 'all_recorded_translation_keys_plus_native_carrier_radii/0.1'},
    render: {calls: renderer.info.render.calls, triangles: renderer.info.render.triangles}};
}};
await load(datasets[0].case_id);
