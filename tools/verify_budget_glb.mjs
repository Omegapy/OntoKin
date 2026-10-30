#!/usr/bin/env node
// Independent C073 checks against frozen geometry and analytic motion samples.
// The browser receives the GLB only; expected observations stay in this process.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {mkdir, readFile, stat, writeFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import validator from 'gltf-validator';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {AnimationMixer, Box3, LoopOnce, Matrix4, Quaternion, REVISION, Vector3} from 'three';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const MAX_BYTES = 64 * 1024 * 1024;
const sha = data => 'sha256:' + createHash('sha256').update(data).digest('hex');
const canonicalJSON = value => JSON.stringify(value && typeof value === 'object'
  ? Array.isArray(value) ? value.map(item => JSON.parse(canonicalJSON(item)))
    : Object.fromEntries(Object.keys(value).sort().map(key => [key, JSON.parse(canonicalJSON(value[key]))]))
  : value);
const near = (actual, expected, tolerance, label) => {
  assert.equal(actual.length, expected.length, label + ' arity');
  const error = Math.max(...actual.map((v, i) => Math.abs(v - expected[i])));
  assert.ok(Number.isFinite(error) && error <= tolerance, `${label}: error ${error} exceeds ${tolerance}`);
  return error;
};
function vector(value, size, label) {
  assert.ok(Array.isArray(value) && value.length === size && value.every(Number.isFinite), label);
  return value;
}
function angle(actual, expected) {
  let a = actual.map(v => v / Math.hypot(...actual));
  let b = expected.map(v => v / Math.hypot(...expected));
  if (a.reduce((sum, v, i) => sum + v * b[i], 0) < 0) b = b.map(v => -v);
  return 4 * Math.atan2(Math.hypot(...a.map((v, i) => v - b[i])), Math.hypot(...a.map((v, i) => v + b[i])));
}
async function boundedRead(filename, maximum) {
  assert.ok((await stat(filename)).size <= maximum, 'Input exceeds the checker byte cap');
  const bytes = await readFile(filename);
  assert.ok(bytes.length <= maximum, 'Input grew beyond the checker byte cap');
  return bytes;
}
function options(args) {
  const result = {browser: false};
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--browser') { assert.equal(result.browser, false); result.browser = true; continue; }
    assert.ok(['--artifact', '--expected', '--output-dir'].includes(args[i]) && args[i + 1], 'Invalid command option');
    const key = {'--artifact': 'artifact', '--expected': 'expected', '--output-dir': 'output'}[args[i]];
    assert.equal(result[key], undefined, 'Repeated command option');
    result[key] = path.resolve(args[++i]);
  }
  assert.ok(result.artifact && result.expected && result.output, 'Artifact, expected file and fresh output directory are required');
  assert.ok(!result.output.startsWith(ROOT + path.sep) && result.output !== ROOT, 'Write evidence outside the checkout');
  return result;
}
function checkExpected(expected) {
  assert.equal(expected.schema_version, 'ontokin.execution-budget-expected/0.1');
  assert.ok(typeof expected.case_id === 'string' && expected.case_id.length <= 128);
  assert.ok(Number.isFinite(expected.duration_seconds) && expected.duration_seconds > 0);
  for (const [field, ceiling] of Object.entries({position_m: .001, rotation_rad: .001, geometry_m: .00001})) {
    assert.ok(Number.isFinite(expected.tolerances?.[field]) && expected.tolerances[field] > 0 && expected.tolerances[field] <= ceiling, field);
  }
  assert.ok(Array.isArray(expected.nodes) && expected.nodes.length > 0 && expected.nodes.length <= 256);
  assert.equal(new Set(expected.nodes.map(n => n.path)).size, expected.nodes.length);
  let count = 0;
  for (const node of expected.nodes) {
    assert.ok(typeof node.path === 'string' && node.path.length > 0 && node.path.length <= 4096);
    assert.ok(['box', 'sphere', 'loft'].includes(node.geometry?.kind));
    if (node.geometry.kind === 'loft') assert.ok(Number.isSafeInteger(node.geometry.triangle_count) &&
      node.geometry.triangle_count > 0 && node.geometry.triangle_count <= 32768, 'Bounded expected loft triangles');
    assert.ok(Array.isArray(node.samples) && node.samples.length >= 3);
    const times = node.samples.map(sample => {
      vector(sample.position_m, 3, 'Expected position');
      vector(sample.orientation_wxyz, 4, 'Expected rotation');
      assert.ok(Math.abs(Math.hypot(...sample.orientation_wxyz) - 1) < 1e-12);
      assert.ok(Number.isFinite(sample.time_seconds) && sample.time_seconds >= 0 && sample.time_seconds <= expected.duration_seconds);
      return sample.time_seconds;
    });
    assert.ok(times.includes(0) && times.includes(expected.duration_seconds) && times.some(t => t > 0 && t < expected.duration_seconds));
    assert.equal(new Set(times).size, times.length);
    count += times.length;
  }
  assert.ok(count <= 8192, 'Expected observation cap');
}
function carriers(scene) {
  const found = new Map();
  scene.traverse(node => {
    if (node.userData.ontokin?.kind !== 'object') return;
    const name = node.userData.ontokin.path;
    assert.ok(typeof name === 'string' && !found.has(name), 'Unique source carrier identity');
    found.set(name, node);
  });
  return found;
}
function analyticLoft(shape) {
  if (!shape.sections) return null;
  assert.ok(Array.isArray(shape.sections) && shape.sections.length >= 2 && shape.sections.length <= 64);
  assert.ok(Number.isInteger(shape.facets) && shape.facets >= 3 && shape.facets <= 256);
  assert.equal(shape.caps, 'flat');
  const sections = [...shape.sections].sort((a, b) => a.station_m - b.station_m), n = shape.facets;
  const points = sections.flatMap(section => {
    vector(section.center_xy_m, 2, 'Loft center'); vector(section.radii_xy_m, 2, 'Loft radius');
    assert.ok(Number.isFinite(section.station_m) && section.radii_xy_m.every(v => v > 0));
    return Array.from({length: n}, (_, j) => [section.center_xy_m[0] + section.radii_xy_m[0] * Math.cos(2 * Math.PI * j / n),
      section.center_xy_m[1] + section.radii_xy_m[1] * Math.sin(2 * Math.PI * j / n), section.station_m]);
  });
  const triangles = [];
  for (let s = 0; s < sections.length - 1; s++) for (let j = 0; j < n; j++) {
    const a = s * n + j, b = s * n + (j + 1) % n, c = (s + 1) * n + j, d = (s + 1) * n + (j + 1) % n;
    triangles.push({region: sections[s].region, vertices: [a, b, c]}, {region: sections[s].region, vertices: [b, d, c]});
  }
  const lo = points.length, hi = lo + 1;
  points.push([...sections[0].center_xy_m, sections[0].station_m], [...sections.at(-1).center_xy_m, sections.at(-1).station_m]);
  for (let j = 0; j < n; j++) {
    triangles.push({region: sections[0].region, vertices: [lo, (j + 1) % n, j]},
      {region: sections.at(-1).region, vertices: [hi, (sections.length - 1) * n + j, (sections.length - 1) * n + (j + 1) % n]});
  }
  const offset = vector(shape.local_position_m ?? [0, 0, 0], 3, 'Local placement');
  const [w, x, y, z] = vector(shape.local_orientation_wxyz ?? [1, 0, 0, 0], 4, 'Local orientation');
  assert.ok(Math.abs(Math.hypot(w, x, y, z) - 1) < 1e-12);
  return {points: points.map(p => new Vector3(...p).applyQuaternion(new Quaternion(x, y, z, w)).add(new Vector3(...offset)).toArray()), triangles};
}
function triangleKey(region, vertices) {
  return region + ':' + [vertices, [vertices[1], vertices[2], vertices[0]], [vertices[2], vertices[0], vertices[1]]]
    .map(values => values.join(',')).sort()[0];
}
function verifyGeometry(carrier, wanted, tolerance) {
  const bounds = new Box3(), materials = new Map(), triangles = [];
  const inverse = new Matrix4().copy(carrier.matrixWorld).invert();
  carrier.traverse(mesh => {
    if (!mesh.isMesh) return;
    assert.ok(!Array.isArray(mesh.material), 'One material per decoded primitive');
    const geometry = mesh.geometry, positions = geometry.getAttribute('position');
    const triangleLimit = wanted.geometry.kind === 'loft' ? wanted.geometry.triangle_count : 32768;
    assert.ok(positions && positions.count > 0 && positions.count <= triangleLimit * 3 && geometry.index);
    assert.equal(geometry.index.count % 3, 0);
    assert.ok(triangles.length + geometry.index.count / 3 <= triangleLimit, 'Decoded triangle work exceeds the frozen geometry');
    const matrix = new Matrix4().multiplyMatrices(inverse, mesh.matrixWorld);
    const points = Array.from({length: positions.count}, (_, i) => new Vector3().fromBufferAttribute(positions, i).applyMatrix4(matrix));
    for (const p of points) { vector(p.toArray(), 3, 'Decoded vertex'); bounds.expandByPoint(p); }
    const region = mesh.userData.ontokin?.region_key ?? mesh.material.userData.ontokin?.source_region_key ?? 'ordinary';
    assert.ok(!materials.has(region), 'One decoded primitive per material region');
    materials.set(region, {key: region, rgba: [...mesh.material.color.toArray(), mesh.material.opacity],
      metallic: mesh.material.metalness, roughness: mesh.material.roughness});
    for (let i = 0; i < geometry.index.count; i += 3) {
      triangles.push({region, points: [0, 1, 2].map(j => {
        const index = geometry.index.getX(i + j);
        assert.ok(Number.isSafeInteger(index) && index >= 0 && index < points.length);
        return points[index].toArray();
      })});
    }
  });
  assert.ok(!bounds.isEmpty() && triangles.length > 0);
  const shape = wanted.geometry, observed = {path: wanted.path, kind: shape.kind, bounds_min_m: bounds.min.toArray(),
    bounds_max_m: bounds.max.toArray(), triangle_count: triangles.length, materials: [...materials.values()]};
  if (shape.kind === 'loft') {
    near(observed.bounds_min_m, vector(shape.bounds_min_m, 3, 'Expected minimum'), tolerance, wanted.path + ' minimum');
    near(observed.bounds_max_m, vector(shape.bounds_max_m, 3, 'Expected maximum'), tolerance, wanted.path + ' maximum');
    assert.equal(triangles.length, shape.triangle_count, 'Triangle count');
    assert.ok(Array.isArray(shape.materials) && shape.materials.length > 0 && shape.materials.length <= 64);
    assert.deepEqual([...materials.keys()].sort(), shape.materials.map(m => m.key).sort());
    for (const material of shape.materials) {
      const actual = materials.get(material.key);
      near(actual.rgba, vector(material.rgba, 4, 'Expected color'), 1e-7, 'Material RGBA');
      near([actual.metallic, actual.roughness], [material.metallic, material.roughness], 1e-7, 'Material PBR');
    }
    const analytic = analyticLoft(shape);
    if (analytic) {
      const expectedKeys = analytic.triangles.map(t => triangleKey(t.region, t.vertices)).sort();
      const actualKeys = triangles.map(t => triangleKey(t.region, t.points.map(p => {
        const matches = analytic.points.flatMap((q, i) => Math.hypot(...p.map((v, j) => v - q[j])) <= tolerance ? [i] : []);
        assert.equal(matches.length, 1, 'Every decoded vertex maps to one independent loft point');
        return matches[0];
      }))).sort();
      assert.deepEqual(actualKeys, expectedKeys, 'Oriented loft topology and per-triangle material region');
      observed.analytic_topology = 'passed';
    } else observed.analytic_topology = 'not_requested';
  } else {
    const size = shape.kind === 'box' ? vector(shape.size_m, 3, 'Box dimensions') : Array(3).fill(2 * shape.radius_m);
    near(bounds.getSize(new Vector3()).toArray(), size, tolerance, 'Primitive dimensions');
  }
  observed.status = 'passed';
  return observed;
}
function observe(scene, byPath, mixer, action, time) {
  action.reset().setLoop(LoopOnce, 1).play(); action.clampWhenFinished = true;
  mixer.setTime(time); scene.updateMatrixWorld(true);
  return Object.fromEntries([...byPath].map(([key, node]) => [key, {position_m: node.getWorldPosition(new Vector3()).toArray(),
    orientation_xyzw: node.getWorldQuaternion(new Quaternion()).toArray()}]));
}
function comparePoses(actual, expected, time) {
  const rows = [];
  for (const node of expected.nodes) {
    const wanted = node.samples.find(sample => sample.time_seconds === time);
    if (!wanted) continue;
    const pose = actual[node.path]; assert.ok(pose, 'Missing observed source object');
    vector(pose.position_m, 3, 'Observed position');
    const positionError = Math.hypot(...pose.position_m.map((value, i) => value - wanted.position_m[i]));
    assert.ok(Number.isFinite(positionError) && positionError <= expected.tolerances.position_m,
      `${node.path} position at ${time}: Euclidean error ${positionError} exceeds ${expected.tolerances.position_m}`);
    const [w, x, y, z] = wanted.orientation_wxyz;
    const rotationError = angle(vector(pose.orientation_xyzw, 4, 'Observed rotation'), [x, y, z, w]);
    assert.ok(Number.isFinite(rotationError) && rotationError <= expected.tolerances.rotation_rad, node.path + ' rotation at ' + time);
    rows.push({path: node.path, time_seconds: time, position_error_m: positionError, rotation_error_rad: rotationError, observed: pose});
  }
  return rows;
}

const BROWSER_SOURCE = `
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
const bytes=Uint8Array.from(atob(globalThis.BUDGET_BYTES), c=>c.charCodeAt(0));
const gltf=await new GLTFLoader().parseAsync(bytes.buffer,'');
const scene=new THREE.Scene();scene.background=new THREE.Color(0xe7edf2);scene.add(gltf.scene);
scene.add(new THREE.AmbientLight(0xffffff,1.6));
for(const [x,y,z,power] of [[6,10,8,2.6],[-6,4,-8,1.8]]){const l=new THREE.DirectionalLight(0xffffff,power);l.position.set(x,y,z);scene.add(l);}
const renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});
renderer.setPixelRatio(1);renderer.setSize(1200,760);renderer.outputColorSpace=THREE.SRGBColorSpace;document.querySelector('#viewport').append(renderer.domElement);
const camera=new THREE.PerspectiveCamera(35,1200/760,.001,10000),mixer=new THREE.AnimationMixer(gltf.scene),clip=gltf.animations[0],action=mixer.clipAction(clip);
function seek(t){action.reset().setLoop(THREE.LoopOnce,1).play();action.clampWhenFinished=true;mixer.setTime(t);gltf.scene.updateMatrixWorld(true);}
const bounds=new THREE.Box3();for(const t of [0,clip.duration/2,clip.duration]){seek(t);bounds.union(new THREE.Box3().setFromObject(gltf.scene));}
const center=bounds.getCenter(new THREE.Vector3()),radius=bounds.getSize(new THREE.Vector3()).length()/2;
const distance=Math.max(radius,.1)/Math.sin(35*Math.PI/360)*1.2;
function observe(t,view='front'){
 seek(t);const direction=view==='side'?new THREE.Vector3(1,.2,0):new THREE.Vector3(.12,.16,1);direction.normalize();
 camera.position.copy(center).addScaledVector(direction,distance);camera.near=Math.max(.001,distance-radius*1.6);camera.far=distance+radius*3+1;camera.lookAt(center);camera.updateProjectionMatrix();camera.updateMatrixWorld(true);
 renderer.render(scene,camera);document.querySelector('#clock').textContent=t+' s · '+view;
 const objects={};let maxNdc=0;gltf.scene.traverse(n=>{if(n.userData.ontokin?.kind==='object')objects[n.userData.ontokin.path]={position_m:n.getWorldPosition(new THREE.Vector3()).toArray(),orientation_xyzw:n.getWorldQuaternion(new THREE.Quaternion()).toArray()};
  if(n.isMesh){n.geometry.computeBoundingBox();const b=n.geometry.boundingBox;for(const x of [b.min.x,b.max.x])for(const y of [b.min.y,b.max.y])for(const z of [b.min.z,b.max.z]){const p=new THREE.Vector3(x,y,z).applyMatrix4(n.matrixWorld).project(camera);maxNdc=Math.max(maxNdc,Math.abs(p.x),Math.abs(p.y));}}
 });
 return {objects,time_seconds:t,view,canvas_pixels:renderer.domElement.width*renderer.domElement.height,max_abs_ndc_xy:maxNdc};
}
globalThis.budgetObserver={observe,duration:clip.duration};observe(0);globalThis.BUDGET_READY=true;
`;
async function browserCheck(bytes, expected, times, output) {
  const {build} = await import('esbuild');
  const {chromium} = await import('playwright');
  const bundled = await build({stdin: {contents: BROWSER_SOURCE, resolveDir: path.join(ROOT, 'tools'), sourcefile: 'budget-observer.mjs'},
    bundle: true, write: false, format: 'esm', platform: 'browser', target: 'es2022'});
  const script = bundled.outputFiles[0].contents;
  const html = '<!doctype html><meta charset="utf-8"><title>OntoKin execution budgets</title>' +
    '<style>body{margin:0;background:#e7edf2;color:#20313f;font:18px system-ui}header{padding:18px 30px;display:flex;justify-content:space-between}canvas{display:block}</style>' +
    '<header><strong>OntoKin · larger workload</strong><span id="clock"></span></header><div id="viewport"></div>' +
    '<script>globalThis.BUDGET_BYTES=' + JSON.stringify(bytes.toString('base64')) + '</script><script type="module" src="/observer.js"></script>';
  const browser = await chromium.launch({headless: true, args: ['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader']});
  const result = {status: 'running', browser_version: browser.version(), observations: [], captures: [], page_errors: [], failed_requests: [],
    artifact_sha256: sha(bytes), observer_bundle_sha256: sha(script), visual_review: 'pending_actual_image_inspection'};
  try {
    const page = await browser.newPage({viewport: {width: 1200, height: 820}, deviceScaleFactor: 1});
    page.on('pageerror', error => result.page_errors.push(String(error)));
    page.on('requestfailed', request => result.failed_requests.push({url: request.url(), error: request.failure()?.errorText}));
    await page.route('**/*', route => {
      const url = route.request().url();
      if (url === 'https://ontokin-budget.invalid/') return route.fulfill({contentType: 'text/html', body: html});
      if (url === 'https://ontokin-budget.invalid/observer.js') return route.fulfill({contentType: 'text/javascript', body: Buffer.from(script)});
      return route.abort();
    });
    await page.goto('https://ontokin-budget.invalid/');
    await page.waitForFunction(() => globalThis.BUDGET_READY === true);
    for (const time of times) {
      const observation = await page.evaluate(t => globalThis.budgetObserver.observe(t), time);
      assert.ok(observation.max_abs_ndc_xy <= 1, 'Loaded scene must fit inside the browser viewport');
      result.observations.push(...comparePoses(observation.objects, expected, time));
    }
    for (const view of ['front', 'side']) for (const [label, time] of [['start', 0], ['middle', expected.duration_seconds / 2], ['end', expected.duration_seconds]]) {
      const observation = await page.evaluate(({time, view}) => globalThis.budgetObserver.observe(time, view), {time, view});
      assert.ok(observation.max_abs_ndc_xy <= 1, 'Capture must contain the full loaded geometry');
      const filename = `${view}-${label}.png`, target = path.join(output, filename);
      await page.screenshot({path: target});
      result.captures.push({path: filename, view, time_seconds: time, max_abs_ndc_xy: observation.max_abs_ndc_xy, sha256: sha(await readFile(target))});
    }
    assert.deepEqual(result.page_errors, []); assert.deepEqual(result.failed_requests, []);
    result.status = 'passed';
  } catch (error) {
    result.status = 'failed';
    result.failure = {name: error.name, message: error.message, stack: error.stack};
  } finally { await browser.close(); }
  return result;
}

async function main(args) {
  if (args.includes('--help')) {
    console.log('node tools/verify_budget_glb.mjs --artifact FILE --expected FROZEN_JSON --output-dir FRESH_DIR [--browser]');
    return;
  }
  const opts = options(args);
  await mkdir(opts.output, {recursive: false});
  const report = {schema_version: 'ontokin.execution-budget-native-validation/0.1', status: 'running', started_at: new Date().toISOString(),
    environment: {node: process.version, three_revision: REVISION, platform: process.platform, architecture: process.arch},
    release_acceptance: false, browser_requested: opts.browser,
    limitations: ['Checks the frozen supplied workload, not every GLB/0.7 program.',
      'Expected physical samples are supplied independently; this checker never invokes OntoKin evaluation.',
      'Native and browser pose decoding use pinned Three.js; actual screenshot review remains separate.',
      'Execution budget metadata is descriptive and grants this checker no authority.']};
  try {
    assert.equal(Number(process.versions.node.split('.')[0]), 22, 'Use the required Node 22 major');
    const expectedPins = {three: '0.180.0', 'gltf-validator': '2.0.0-dev.3.10', playwright: '1.56.1', esbuild: '0.25.10'};
    for (const [name, version] of Object.entries(expectedPins)) {
      const installed = JSON.parse(await readFile(path.join(ROOT, 'tools/node_modules', name, 'package.json'), 'utf8'));
      assert.equal(installed.version, version, 'Verification dependency pin: ' + name);
    }
    report.environment.dependencies = expectedPins;
    report.source_git = {commit: execFileSync('git', ['-C', ROOT, 'rev-parse', 'HEAD'], {encoding: 'utf8'}).trim(),
      tree: execFileSync('git', ['-C', ROOT, 'rev-parse', 'HEAD^{tree}'], {encoding: 'utf8'}).trim(),
      tracked_status: execFileSync('git', ['-C', ROOT, 'status', '--porcelain', '--untracked-files=no'], {encoding: 'utf8'}).trim()};
    report.checker_sha256 = sha(await readFile(fileURLToPath(import.meta.url)));
    const bytes = await boundedRead(opts.artifact, MAX_BYTES), expectedBytes = await boundedRead(opts.expected, 2 * 1024 * 1024);
    report.artifact = {path: opts.artifact, sha256: sha(bytes), bytes: bytes.length};
    report.expected = {path: opts.expected, sha256: sha(expectedBytes), bytes: expectedBytes.length};
    const expected = JSON.parse(expectedBytes); checkExpected(expected); report.case_id = expected.case_id;
    assert.ok(bytes.length >= 28); assert.equal(bytes.readUInt32LE(0), 0x46546c67); assert.equal(bytes.readUInt32LE(4), 2);
    assert.equal(bytes.readUInt32LE(8), bytes.length); assert.equal(bytes.readUInt32LE(16), 0x4e4f534a);
    const jsonLength = bytes.readUInt32LE(12); assert.ok(20 + jsonLength + 8 <= bytes.length);
    const document = JSON.parse(bytes.subarray(20, 20 + jsonLength).toString('utf8'));
    const metadata = document.extras?.ontokin;
    assert.equal(metadata?.target_contract, 'ontokin.glb/0.7'); assert.equal(metadata.profile, 'planar-reach-budget-0.1');
    assert.equal(metadata.schema_version, '0.7');
    assert.ok(document.buffers?.length === 1 && document.buffers[0].uri === undefined);
    assert.ok(!document.images?.length && !document.extensionsRequired?.length, 'Only embedded geometry is in this frozen workload scope');
    assert.ok(Array.isArray(document.nodes) && document.nodes.length === expected.nodes.length);
    assert.ok(document.nodes.every(node => node.extras?.ontokin?.kind === 'object' && !node.children?.length &&
      node.matrix === undefined && node.skin === undefined && node.camera === undefined), 'Only the frozen flat source carriers are allowed');
    for (const node of document.nodes) if (node.scale !== undefined) assert.deepEqual(node.scale, [1, 1, 1]);
    assert.equal(document.scene, 0); assert.equal(document.scenes?.length, 1);
    assert.deepEqual(document.scenes[0].nodes, document.nodes.map((_, index) => index), 'No extra or omitted scene nodes');
    report.program_revision = metadata.program?.revision;
    if (expected.program_revision !== undefined) assert.equal(report.program_revision, expected.program_revision);
    const manifest = metadata.program?.manifest;
    assert.equal(manifest?.schema_version, 'ontokin.bundle/0.1');
    assert.equal(manifest.entry_source_id, 'entry');
    assert.ok(Array.isArray(manifest.units) && manifest.units.length > 0 && manifest.units.length <= 17);
    assert.equal(report.program_revision, sha(Buffer.concat([Buffer.from('ontokin.bundle/0.1\0'), Buffer.from(canonicalJSON(manifest))])),
      'Program identity must bind the actual source manifest');
    if (expected.source_sha256 !== undefined) {
      assert.match(expected.source_sha256, /^[0-9a-f]{64}$/);
      const entry = manifest.units.filter(unit => unit.source_id === 'entry');
      assert.equal(entry.length, 1);
      assert.equal(entry[0].source_revision, 'sha256:' + expected.source_sha256, 'Artifact entry must identify the frozen source bytes');
      report.source_sha256 = expected.source_sha256;
    }
    const format = await validator.validateBytes(new Uint8Array(bytes), {uri: path.basename(opts.artifact), maxIssues: 200});
    report.khronos = {version: validator.version(), errors: format.issues.numErrors, warnings: format.issues.numWarnings, messages: format.issues.messages};
    assert.equal(format.issues.numErrors, 0); assert.equal(format.issues.numWarnings, 0);
    const gltf = await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength), '');
    assert.equal(gltf.animations.length, 1); const clip = gltf.animations[0];
    near([clip.duration], [expected.duration_seconds], .000001, 'Recorded duration');
    const objects = carriers(gltf.scene);
    assert.deepEqual([...objects.keys()].sort(), expected.nodes.map(node => node.path).sort(), 'Complete carrier inventory');
    gltf.scene.updateMatrixWorld(true);
    report.geometry = expected.nodes.map(node => verifyGeometry(objects.get(node.path), node, expected.tolerances.geometry_m));
    const mixer = new AnimationMixer(gltf.scene), action = mixer.clipAction(clip);
    const times = [...new Set(expected.nodes.flatMap(node => node.samples.map(sample => sample.time_seconds)))].sort((a, b) => a - b);
    report.native_observations = times.flatMap(time => comparePoses(observe(gltf.scene, objects, mixer, action, time), expected, time));
    if (opts.browser) {
      report.browser = await browserCheck(bytes, expected, times, opts.output);
      assert.equal(report.browser.status, 'passed', 'Browser observations or capture failed');
    }
    assert.equal(sha(await boundedRead(opts.artifact, MAX_BYTES)), report.artifact.sha256);
    assert.equal(sha(await boundedRead(opts.expected, 2 * 1024 * 1024)), report.expected.sha256);
    report.status = 'passed';
  } catch (error) {
    report.status = 'failed'; report.failure = {name: error.name, message: error.message, stack: error.stack}; process.exitCode = 1;
  }
  report.finished_at = new Date().toISOString();
  await writeFile(path.join(opts.output, 'validation.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({status: report.status, case_id: report.case_id, artifact: report.artifact?.sha256,
    native_observations: report.native_observations?.length, browser: report.browser?.status,
    output: opts.output, failure: report.failure?.message}, null, 2));
}
await main(process.argv.slice(2));
