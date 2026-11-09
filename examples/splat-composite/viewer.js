import * as THREE from 'three/webgpu';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { GLTFGaussianSplatLoaderExtension } from 'three/addons/loaders/GLTFGaussianSplatLoaderExtension.js';

const $ = id => document.getElementById(id);
let rendererFailure;
const report = (message, error = false) => {
  $('status').textContent = rendererFailure || message;
  $('status').dataset.error = String(Boolean(rendererFailure) || error);
};
const params = new URLSearchParams(location.search);
const extension = 'KHR_gaussian_splatting';
const MB = 1024 * 1024;
const decoder = new TextDecoder('utf-8', { fatal: true });
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x23343e);
const backgroundRoot = new THREE.Group();
const authoredRoot = new THREE.Group();
scene.add(backgroundRoot, authoredRoot);
scene.add(new THREE.HemisphereLight(0xffffff, 0x859399, 2.1));
const sun = new THREE.DirectionalLight(0xfff2d8, 2.2);
sun.position.set(-2, 5, 3);
scene.add(sun);
const camera = new THREE.PerspectiveCamera(36, 1, .02, 100);
const controls = new OrbitControls(camera, $('canvas'));
// The first demonstration consumes checked, uncompressed, self-contained GLBs.
const manager = new THREE.LoadingManager();
manager.setURLModifier(() => { throw Error('GLB requested a secondary resource'); });
const loader = new GLTFLoader(manager);
loader.register(parser => new GLTFGaussianSplatLoaderExtension(parser));
let renderer, mixer, action, admission, authoredScene, selected, environmentKey, previousFrame, playing = false;
let frameSamples = [], metrics = {}, firstFrameAt, sceneTime = 0;
const capturedSite = Boolean($('campus'));
let needsRender = true;
controls.addEventListener('change', () => { needsRender = true; });

function relative(path, base) {
  if (typeof path !== 'string' || !path.split('/').every(s => /^[A-Za-z0-9_-][A-Za-z0-9_.-]*$/.test(s))) {
    throw Error('Asset paths must be simple local names relative to the manifest');
  }
  return new URL(path, base);
}

async function readBytes(url, limit, expectedHash) {
  const response = await fetch(url, { redirect: 'error', cache: 'no-store' });
  if (!response.ok) throw Error(url.pathname + ' returned HTTP ' + response.status);
  if (Number(response.headers.get('content-length')) > limit) throw Error('File exceeds byte budget');
  const reader = response.body.getReader();
  const chunks = [];
  let size = 0;
  while (true) {
    const {done, value} = await reader.read();
    if (done) break;
    size += value.byteLength;
    if (size > limit) { await reader.cancel(); throw Error('File exceeds byte budget'); }
    chunks.push(value);
  }
  const bytes = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.length; }
  if (expectedHash !== undefined) {
    const sum = await crypto.subtle.digest('SHA-256', bytes);
    const actual = [...new Uint8Array(sum)].map(b => b.toString(16).padStart(2, '0')).join('');
    if (actual !== expectedHash) throw Error('SHA-256 mismatch for ' + url.pathname);
  }
  return bytes;
}

function inspectGLB(bytes, splat, sourceHash) {
  const view = new DataView(bytes.buffer);
  if (bytes.length < 28 || view.getUint32(0,true) !== 0x46546c67 ||
      view.getUint32(4,true) !== 2 || view.getUint32(8,true) !== bytes.length ||
      view.getUint32(16,true) !== 0x4e4f534a) throw Error('Invalid GLB container');
  const size = view.getUint32(12,true);
  if (size > 4 * MB || size + 28 > bytes.length) throw Error('Invalid GLB JSON size');
  const doc = JSON.parse(decoder.decode(bytes.subarray(20, 20 + size)));
  if (doc.asset?.version !== '2.0' || doc.buffers?.length !== 1 || 'uri' in doc.buffers[0] ||
      doc.images?.length || doc.textures?.length) throw Error('Expected a self-contained, texture-free GLB');
  if ((doc.extensionsUsed || []).some(name => !splat || ![extension, 'KHR_materials_unlit'].includes(name))) throw Error('Unsupported GLB extension');
  if ((doc.nodes?.length ?? 0) > 4096 || (doc.meshes?.length ?? 0) > 512 ||
      (doc.accessors?.length ?? 0) > 8192 || !doc.accessors?.every(a =>
        !a.sparse && Number.isSafeInteger(a.count) && a.count > 0 && a.count <= 1000000)) throw Error('GLB exceeds scene budget');
  if (!splat) {
    if (doc.extras?.ontokin?.source?.entry_revision !== 'sha256:' + sourceHash) throw Error('GLB source revision mismatch');
    return 0;
  }
  if (!doc.extensionsUsed?.includes(extension)) throw Error('Missing splat capability');
  let count = 0;
  for (const mesh of doc.meshes || []) for (const p of mesh.primitives) {
    if (p.mode !== 0 || p.extensions?.[extension]?.kernel !== 'ellipse') throw Error('Expected uncompressed ellipse splats');
    count += doc.accessors[p.attributes.POSITION].count;
  }
  if (!count || count > 1000000) throw Error('Splat count outside viewer budget');
  return count;
}

function checkedAsset(base, asset, limit) {
  if (typeof asset?.sha256 !== 'string' || !/^[a-f0-9]{64}$/.test(asset.sha256)) throw Error('Missing SHA-256');
  return readBytes(relative(asset.path, base), limit, asset.sha256);
}

function setCamera(eye, target, far, fov = 36) {
  controls.target.set(...target);
  camera.position.set(...eye);
  camera.far = far;
  camera.fov = fov;
  camera.updateProjectionMatrix();
  controls.update();
}

function fixedView(screen) {
  if (capturedSite) {
    if (screen) setCamera([0.07, 0.55, 3.45], [0, 0.31, -0.34], 600);
    else setCamera([8, 4, 4], [0, 0.7, 0], 600);
    return;
  }
  // Only authored geometry influences the orbit target and overview.
  const box = new THREE.Box3().setFromObject(authoredRoot);
  if (box.isEmpty()) return;
  const focus = box.getCenter(new THREE.Vector3());
  const distance = Math.max(1.7, box.getSize(new THREE.Vector3()).length());
  if (screen) {
    controls.target.set(0, .31, -.34);
    camera.position.set(.07, .48, 3.45);
  } else {
    controls.target.copy(focus);
    camera.position.copy(focus).addScaledVector(new THREE.Vector3(1.6, .85, .9).normalize(), distance * 2);
  }
  controls.update();
}

function setTime(value) {
  needsRender = true;
  sceneTime = value;
  $('time').value = String(value);
  $('seconds').textContent = value.toFixed(3) + ' s';
  if (action) action.paused = false;
  mixer?.setTime(value);
}

function updateMetrics() {
  const sorted = [...frameSamples].sort((a, b) => a - b);
  const q = pct => sorted.length ? +sorted[Math.ceil(sorted.length * pct) - 1].toFixed(2) : null;
  $('metrics').textContent = JSON.stringify({...metrics, frameSamples: sorted.length,
    medianFrameIntervalMs: q(.50), p95FrameIntervalMs: q(.95)}, null, 2);
}

function disposeAuthored(root) {
  const geometries = new Set(), materials = new Set();
  root.traverse(o => {
    if (o.geometry) geometries.add(o.geometry);
    if (o.material) for (const m of [].concat(o.material)) materials.add(m);
  });
  for (const geo of geometries) geo.dispose();
  for (const mat of materials) mat.dispose();
}

async function load(which) {
  const start = performance.now();
  $('baseline').disabled = $('widened').disabled = true;
  report('Checking the ' + which + ' manifest and asset hashes…');
  try {
    const url = relative('demo/' + which + '.json', location.href);
    const receipt = admission.manifests[which];
    const m = JSON.parse(decoder.decode(await checkedAsset(location.href, {path: 'demo/' + which + '.json', sha256: receipt.sha256}, 65536)));
    if (m.schema !== 'ontokin-composite/1' || m.environment?.authority !== 'visual-only' ||
        m.environment.requiredExtension !== extension || m.registration?.worldUnit !== 'metre' ||
        !['rigid','similarity'].includes(m.registration.kind) || m.collisionProxy !== null ||
        m.registration.matrix?.length !== 16 || !m.registration.matrix.every(Number.isFinite)) throw Error('Unsupported manifest');
    const backgroundKey = JSON.stringify([m.environment,m.registration]);
    if (environmentKey && environmentKey !== backgroundKey) throw Error('Edit must retain environment bytes and registration');
    await checkedAsset(url, m.authored.source, 4 * MB);
    const authoredBytes = await checkedAsset(url, m.authored.glb, 32 * MB);
    inspectGLB(authoredBytes, false, m.authored.source.sha256);
    const t0 = performance.now();
    const authored = await loader.parseAsync(authoredBytes.buffer, '');
    const nodes = [];
    authored.scene.traverse(o => { if (o.userData.ontokin?.kind === 'object') nodes.push(o.name); });
    if (!nodes.length || !authored.animations.length) throw Error('Expected an animated OntoKin scene with named objects');
    const authoredParseMs = +(performance.now() - t0).toFixed(2);
    if (!environmentKey) {
      const bytes = await checkedAsset(url, m.environment, 64 * MB);
      const count = inspectGLB(bytes, true);
      if (count !== receipt.storedSplats || !Number.isSafeInteger(receipt.sceneSplats) ||
          receipt.sceneSplats < 1 || receipt.sceneSplats > 1000000) throw Error('Splat budget or receipt mismatch');
      const t1 = performance.now();
      const background = await loader.parseAsync(bytes.buffer, '');
      let found = false;
      background.scene.traverse(o => { if (o.isGaussianSplat) found = true; });
      if (!found) throw Error('Renderer loader did not produce a GaussianSplat');
      backgroundRoot.matrixAutoUpdate = false;
      backgroundRoot.matrix.fromArray(m.registration.matrix);
      backgroundRoot.matrixWorldNeedsUpdate = true;
      backgroundRoot.add(background.scene);
      environmentKey = backgroundKey;
      metrics = {backend: renderer.backend.isWebGPUBackend ? 'WebGPU' : 'WebGL2',
        requestedBackend: params.get('backend') === 'webgpu' ? 'WebGPU (allow fallback)' : 'WebGL2',
        environmentName: m.environment.name, environmentSha256: m.environment.sha256,
        environmentLoads: 1, environmentBytes: bytes.length, splatCount: receipt.sceneSplats, storedSplatCount: count,
        environmentParseMs: +(performance.now() - t1).toFixed(2)};
    }
    const time = sceneTime;
    if (authoredScene) {
      mixer.stopAllAction(); mixer.uncacheRoot(authoredScene);
      authoredRoot.remove(authoredScene); disposeAuthored(authoredScene);
    }
    authoredScene = authored.scene;
    authoredRoot.add(authoredScene);
    mixer = new THREE.AnimationMixer(authoredScene);
    const clip = authored.animations[0];
    action = mixer.clipAction(clip);
    action.setLoop(THREE.LoopOnce, 1); action.clampWhenFinished = true; action.play();
    $('time').max = String(clip.duration);
    $('play').disabled = $('time').disabled = false;
    setTime(Math.min(time, clip.duration));
    if (!selected) fixedView(false);
    selected = which;
    $('baseline').setAttribute('aria-pressed', String(which === 'baseline'));
    $('widened').setAttribute('aria-pressed', String(which === 'widened'));
    Object.assign(metrics, {variant: which, authoredSha256: m.authored.glb.sha256, authoredBytes: authoredBytes.length,
      authoredParseMs, authoredObjects: nodes, clipSeconds: clip.duration});
    frameSamples = []; previousFrame = undefined; firstFrameAt = start;
    report((which === 'baseline' ? 'Original' : 'Widened') + ' cart loaded · ' + countText(metrics.splatCount) + ' splats · visual context only');
    updateMetrics();
  } catch (error) {
    report('Could not load ' + which + '. ' + error.message, true);
  } finally {
    $('baseline').disabled = $('widened').disabled = false;
  }
}

function countText(n) { return n.toLocaleString('en-US'); }

function failedRenderer(message) {
  rendererFailure = 'Rendering stopped. ' + message + ' Reopen the default viewer to use WebGL2.';
  report(rendererFailure, true);
}

async function start() {
  if (!window.isSecureContext) throw Error('Open the viewer on localhost or HTTPS');
  admission = JSON.parse(decoder.decode(await readBytes(relative('demo/viewer-receipt.json', location.href), 8192)));
  if (admission.schema !== 'ontokin-composite-viewer/1') throw Error('Run the Python viewer preflight on this demo');
  renderer = new THREE.WebGPURenderer({canvas: $('canvas'), antialias: true, forceWebGL: params.get('backend') !== 'webgpu'});
  const onLost = renderer.onDeviceLost.bind(renderer);
  renderer.onDeviceLost = info => { onLost(info); failedRenderer(info.api + ' device lost: ' + info.message); };
  renderer.onError = info => failedRenderer(info.api + ' ' + info.type + ': ' + info.message);
  window.addEventListener('unhandledrejection', event => {
    const message = String(event.reason?.message || event.reason);
    if (/popErrorScope|GPUDeviceLost/i.test(message)) failedRenderer(message);
  });
  await renderer.init();
  renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
  new ResizeObserver(([entry]) => {
    const {width, height} = entry.contentRect;
    renderer.setSize(width, height, false);
    needsRender = true;
    camera.aspect = width / Math.max(1,height); camera.updateProjectionMatrix();
  }).observe($('canvas').parentElement);
  $('time').oninput = () => setTime(Number($('time').value));
  $('play').onclick = () => { playing = !playing; $('play').textContent = playing ? 'Pause' : 'Play'; };
  $('environment').onchange = () => {
    backgroundRoot.visible = $('environment').checked;
    needsRender = true;
  };
  $('overview').onclick = () => fixedView(false);
  $('screen').onclick = () => fixedView(true);
  if (capturedSite) {
    $('assembly').onchange = () => { authoredRoot.visible = $('assembly').checked; needsRender = true; };
    $('campus').onclick = () => setCamera([45, 145, 120], [0, 0, -20], 600);
    $('reverse').onclick = () => setCamera([-4, 1.7, -1.5], [0, .45, 0], 600);
    $('foreground').onclick = () => setCamera([11.177, 4.727, .567], [0, .22, 0], 600, 14);
    $('low').onclick = () => setCamera([7.449, .693, 5.015], [0, .22, 0], 600, 14);
  }
  $('baseline').onclick = () => load('baseline');
  $('widened').onclick = () => load('widened');
  await load('baseline');
  renderer.setAnimationLoop(now => {
    if (rendererFailure) return;
    // The larger capture has no changing pixels while paused and the camera is stationary.
    if (capturedSite && !playing && !needsRender) { previousFrame = undefined; return; }
    if (previousFrame !== undefined && authoredScene) {
      const dt = now - previousFrame;
      if (frameSamples.length < 120 && dt > 0) { frameSamples.push(dt); if (frameSamples.length % 10 === 0) updateMetrics(); }
      if (playing) setTime((sceneTime + dt / 1000) % Number($('time').max));
    }
    previousFrame = now;
    renderer.render(scene, camera);
    needsRender = false;
    if (firstFrameAt !== undefined) {
      metrics.firstCompositeSubmitMs = +(performance.now() - firstFrameAt).toFixed(2);
      firstFrameAt = undefined; updateMetrics();
    }
  });
}
start().catch(error => report('Composite rendering unavailable. ' + error.message, true));
