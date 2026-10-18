// Three.js reads the GLB. All displayed motion comes from its animation tracks.
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';

const $ = id => document.getElementById(id);
const demos = window.ONTOKIN_DEMOS || [];
const viewport = $('viewport');
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(38, 1, 0.001, 10000);
let renderer, controls;
let content = null, mixer = null, action = null, duration = 0, time = 0;
let playing = !matchMedia('(prefers-reduced-motion: reduce)').matches;
let selected = null, objects = [], helperNodes = [], current = null, loadId = 0;
let data = new Uint8Array(), trails = new THREE.Group(), selection = null;
let bounds = new THREE.Box3(), loaded = false;
const raycaster = new THREE.Raycaster();

function error(message) { $('error').textContent = message; $('error').classList.remove('hidden'); $('load-status').textContent = 'Could not load the animation'; }
function decoded(base64) { return Uint8Array.from(atob(base64), c => c.charCodeAt(0)); }
function dispose(group) { group?.traverse(node => { node.geometry?.dispose(); const materials = Array.isArray(node.material) ? node.material : [node.material]; materials.forEach(m => m?.dispose()); }); }
function setPlaying(value) { playing = value; $('play').textContent = value ? 'Pause' : 'Play'; $('play').setAttribute('aria-label', value ? 'Pause animation' : 'Play animation'); }
function setTime(value) {
  time = Math.max(0, Math.min(duration, Number(value) || 0));
  if (action) { action.enabled = true; action.paused = false; }
  mixer?.setTime(time);
  content?.updateMatrixWorld(true);
  $('timeline').value = time;
  $('time').textContent = time.toFixed(3);
  const event = current?.events?.filter(event => event.time <= time + 1e-8).at(-1);
  $('event-label').textContent = event?.label || (current ? 'Baked animation playback' : 'Local GLB playback');
  if (selected) {
    const p = selected.getWorldPosition(new THREE.Vector3());
    ['x','y','z'].forEach(axis => $('position-' + axis).textContent = (Math.abs(p[axis]) < 0.0005 ? 0 : p[axis]).toFixed(3));
    selection?.update();
  }
}
function fit() {
  if (bounds.isEmpty()) return;
  const size = bounds.getSize(new THREE.Vector3());
  const centre = bounds.getCenter(new THREE.Vector3());
  const radius = Math.max(size.length() * 0.5, 0.25);
  const limitingFov = Math.min(camera.fov * Math.PI / 180, 2 * Math.atan(Math.tan(camera.fov * Math.PI / 360) * camera.aspect));
  const distance = radius / Math.sin(limitingFov * 0.5) * 1.10;
  camera.position.copy(centre).add(new THREE.Vector3(0.42, 0.28, 1).normalize().multiplyScalar(distance));
  camera.near = Math.max(0.0001, distance / 1000); camera.far = Math.max(distance * 100, 100);
  camera.updateProjectionMatrix(); controls.target.copy(centre); controls.update();
}
function chooseObject(path) {
  selected = objects.find(node => node.userData.ontokin?.path === path || node.name === path) || objects[0] || null;
  if (selection) { scene.remove(selection); dispose(selection); selection = null; }
  if (selected) {
    $('object-select').value = selected.userData.ontokin?.path || selected.name;
    selection = new THREE.BoxHelper(selected, 0xf3bf76); selection.material.transparent = true; selection.material.opacity = 0.60;
    scene.add(selection);
    const meta = selected.userData.ontokin;
    $('object-status').textContent = meta ? 'OntoKin object · ' + (meta.class_name || meta.path || selected.name) : 'Imported scene node';
  }
  setTime(time);
}
function updateHelpers() { helperNodes.forEach(node => node.visible = $('show-helpers').checked); }
function ensureEmbedded(bytes) {
  // Keep the offline viewer local even when the user opens a different asset.
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  if (bytes.length < 20 || view.getUint32(0, true) !== 0x46546c67 || view.getUint32(4, true) !== 2) throw new Error('Choose a glTF 2.0 binary (.glb) file.');
  const size = view.getUint32(12, true);
  const document = JSON.parse(new TextDecoder().decode(bytes.subarray(20, 20 + size)));
  if ([...(document.buffers || []), ...(document.images || [])].some(item => item.uri && !item.uri.startsWith('data:'))) throw new Error('This offline viewer requires a self-contained GLB without external asset URLs.');
}
async function load(bytes, demo, label) {
  const request = ++loadId; loaded = false; $('error').classList.add('hidden'); $('load-status').textContent = 'Reading animation tracks…';
  ensureEmbedded(bytes);
  const gltf = await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength), '');
  if (request !== loadId) { dispose(gltf.scene); return; }
  if (content) { scene.remove(content); dispose(content); }
  if (selection) { scene.remove(selection); dispose(selection); selection = null; }
  scene.remove(trails); dispose(trails); trails = new THREE.Group(); scene.add(trails);
  content = gltf.scene; scene.add(content); current = demo; data = bytes;
  objects = []; helperNodes = [];
  content.traverse(node => {
    if (node.userData.ontokin?.kind === 'object') objects.push(node);
    if (node.userData.ontokin?.kind === 'visual_helper') helperNodes.push(node);
  });
  if (!objects.length) content.traverse(node => { if (node.isMesh) objects.push(node); });
  mixer = new THREE.AnimationMixer(content);
  const clip = gltf.animations[0]; duration = clip?.duration || 0; action = null;
  if (clip) { action = mixer.clipAction(clip); action.setLoop(THREE.LoopOnce, 1); action.clampWhenFinished = true; action.play(); }
  bounds = new THREE.Box3();
  const paths = new Map(objects.map(object => [object, []]));
  for (let i = 0; i <= 120; i++) {
    if (action) { action.enabled = true; action.paused = false; }
    mixer.setTime(duration * i / 120); content.updateMatrixWorld(true);
    bounds.union(new THREE.Box3().setFromObject(content));
    for (const object of objects) paths.get(object).push(object.getWorldPosition(new THREE.Vector3()));
  }
  objects.forEach((object, index) => {
    const points = paths.get(object);
    if (points.every(p => p.distanceTo(points[0]) < 1e-9)) return;
    const geometry = new THREE.BufferGeometry().setFromPoints(points);
    const material = new THREE.LineBasicMaterial({color: index % 2 ? 0x84bdfa : 0x76dfbf, transparent: true, opacity: 0.34});
    trails.add(new THREE.Line(geometry, material));
  });
  trails.visible = $('show-trails').checked; updateHelpers();
  $('object-select').replaceChildren(...objects.map(node => { const option = document.createElement('option'); option.value = node.userData.ontokin?.path || node.name; option.textContent = option.value; return option; }));
  $('scene-title').textContent = demo?.title || label;
  $('scene-description').textContent = demo?.description || 'Local GLB loaded with Three.js. No evaluator comparison is available for this file.';
  $('duration').textContent = duration.toFixed(3); $('timeline').max = duration;
  $('ticks').replaceChildren(...Array.from({length: 5}, (_, i) => { const span = document.createElement('span'); span.textContent = (duration * i / 4).toFixed(2) + ' s'; return span; }));
  $('source-code').textContent = demo?.source || 'The editable source is not embedded in this imported GLB.';
  $('export-report').textContent = demo ? JSON.stringify(demo.report, null, 2) : 'No export report was supplied. Loading a file does not establish numerical conformance.';
  $('download-source').disabled = !demo;
  $('asset-badge').textContent = demo ? 'Actual OntoKin GLB playback' : 'Local GLB · numerical status unknown';
  $('load-status').textContent = demo ? '✓ Export report included · Three.js loaded' : 'Three.js loaded · no conformance report';
  $('position-tolerance').textContent = demo ? '1 mm' : 'Unknown';
  $('rotation-tolerance').textContent = demo ? '0.001 rad' : 'Unknown';
  $('time-tolerance').textContent = demo ? '1 µs' : 'Unknown';
  $('evidence-note').textContent = demo ? 'The encoded animation is checked against the reference evaluator at keys, events, and interior samples.' : 'This file has not been compared with an OntoKin source program.';
  $('scope-note').textContent = demo?.id === 'gravity-and-release' ? 'The grid is a viewing reference, with no collision response. After release the sphere continues below zero height. Joint markers and paths are display aids.' : 'Joint markers and motion paths are viewing aids. The animation contains calculated transforms; the viewer does not run physics.';
  chooseObject(demo?.focus); setTime(0); fit(); loaded = true; setPlaying(playing);
}
function download(bytes, filename, type) { const url = URL.createObjectURL(new Blob([bytes], {type})); const a = document.createElement('a'); a.href = url; a.download = filename; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); }
async function chooseDemo(index) {
  if (!demos[index]) throw new Error('The demo data is missing. Run python3 tools/build_visual_demos.py from the repository root.');
  document.querySelectorAll('.demo-tab').forEach((button,i) => button.setAttribute('aria-pressed', String(i === index)));
  await load(decoded(demos[index].glb), demos[index], demos[index].title);
}

try {
  renderer = new THREE.WebGLRenderer({antialias: true, alpha: true}); renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace; renderer.toneMapping = THREE.NoToneMapping;
  viewport.prepend(renderer.domElement);
  controls = new OrbitControls(camera, renderer.domElement); controls.enableDamping = true; controls.dampingFactor = 0.08;
  scene.add(new THREE.HemisphereLight(0xc2e3ff, 0x385144, 2.25));
  const key = new THREE.DirectionalLight(0xffecd3, 3.2); key.position.set(3, 6, 5); scene.add(key);
  const fill = new THREE.DirectionalLight(0xafd9ff, 1.6); fill.position.set(-4, 2, -3); scene.add(fill);
  const grid = new THREE.GridHelper(20, 40, 0x708894, 0x3b535e); grid.material.transparent = true; grid.material.opacity = 0.20; scene.add(grid);
  scene.add(trails);
  const resize = new ResizeObserver(() => { const w = viewport.clientWidth, h = viewport.clientHeight; renderer.setSize(w,h); camera.aspect = w/h; camera.updateProjectionMatrix(); }); resize.observe(viewport);
  $('demo-0').onclick = () => chooseDemo(0).catch(exc => error(exc.message));
  $('demo-1').onclick = () => chooseDemo(1).catch(exc => error(exc.message));
  $('play').onclick = () => { if (time >= duration) setTime(0); setPlaying(!playing); };
  $('restart').onclick = () => setTime(0);
  $('fit').onclick = fit;
  $('timeline').oninput = event => { setPlaying(false); setTime(event.target.value); };
  $('object-select').onchange = event => chooseObject(event.target.value);
  $('show-helpers').onchange = updateHelpers;
  $('show-trails').onchange = () => trails.visible = $('show-trails').checked;
  $('show-grid').onchange = () => grid.visible = $('show-grid').checked;
  $('download-glb').onclick = () => download(data, current?.file.replace(/\.ok$/, '.glb') || 'animation.glb', 'model/gltf-binary');
  $('download-source').onclick = () => current && download(current.source, current.file, 'text/plain');
  $('local-file').onchange = async event => {
    const file = event.target.files[0]; if (!file) return;
    if (file.size > 64 * 1024 * 1024) { error('The local preview limit is 64 MiB. Choose a smaller GLB.'); return; }
    document.querySelectorAll('.demo-tab').forEach(button => button.setAttribute('aria-pressed','false'));
    try { await load(new Uint8Array(await file.arrayBuffer()), null, file.name); } catch (exc) { error(exc.message); }
  };
  let press = null;
  renderer.domElement.addEventListener('pointerdown', event => press = [event.clientX,event.clientY]);
  renderer.domElement.addEventListener('pointerup', event => {
    if (!press || Math.hypot(event.clientX-press[0],event.clientY-press[1]) > 5) return;
    const rect = renderer.domElement.getBoundingClientRect();
    raycaster.setFromCamera(new THREE.Vector2((event.clientX-rect.left)/rect.width*2-1, -(event.clientY-rect.top)/rect.height*2+1), camera);
    const hit = raycaster.intersectObjects(objects,true)[0]; if (!hit) return;
    let node = hit.object; while (node && !objects.includes(node)) node = node.parent;
    if (node) chooseObject(node.userData.ontokin?.path || node.name);
  });
  let last = performance.now();
  renderer.setAnimationLoop(now => {
    const delta = Math.min((now-last)/1000,0.1); last = now;
    if (loaded && playing && duration > 0) { const next = time+delta*Number($('speed').value); setTime(next>duration ? next%duration : next); }
    controls.update(); renderer.render(scene,camera);
  });
  window.ontokinViewer = {
    get ready() { return loaded; },
    get state() { return {time, duration, playing, demo: current?.id || null,
      objects: Object.fromEntries(objects.map(node => [node.userData.ontokin?.path || node.name,
        {position_m: node.getWorldPosition(new THREE.Vector3()).toArray(), orientation_xyzw: node.getWorldQuaternion(new THREE.Quaternion()).toArray()}]))}; },
    pause: () => setPlaying(false), setTime, chooseDemo,
  };
  chooseDemo(0).catch(exc => error(exc.message));
} catch (exc) { error('A WebGL-capable browser is required. ' + exc.message); }
