#!/usr/bin/env node
// Actual Chromium/WebGL evidence for supplied, independently checked GLB/0.6.
import assert from 'node:assert/strict';
import {mkdir, open, readFile, realpath, writeFile} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {build} from 'esbuild';
import {chromium} from 'playwright';
import {root, boundedRead, containedPath} from './verify_reach_native.mjs';
import {LIMITS, parseJson, parseGlb, requiredPlan, checkSampleCoverage, sha256, canonical,
  parseRational, fromNumber, compare, square, enclosure, positionSquaredError, quaternionAngleSquaredUpper,
  errorUpperNumber, floatTransformEnclosure, transformedPointBounds, floatPositionSquaredUpper, numberInterval} from './reach_native_support.mjs';

export const SOURCE_CASES = ['P01', 'P11', 'P20', 'P16', 'P18', 'P19', 'L01', 'L02', 'L03'];
export const AGENT_CASES = ['P01', 'P11', 'P13', 'P20', 'P16', 'P17', 'L01', 'L02', 'L03'];
const SELF_INPUTS = ['tools/verify_reach_viewer.mjs', 'tools/reach_viewer_harness.mjs', 'tools/reach_destination.mjs',
  'tools/reach_native_support.mjs', 'tools/verify_reach_native.mjs', 'tools/package.json', 'tools/package-lock.json',
  'docs/language-design/planar-reach-v0.1/release-contract.md'];
const SCHEMA = 'ontokin.reach-browser-validation/0.1';
const identity = () => ({commit: execFileSync('git', ['-C', root, 'rev-parse', 'HEAD'], {encoding: 'utf8'}).trim(),
  tree: execFileSync('git', ['-C', root, 'rev-parse', 'HEAD^{tree}'], {encoding: 'utf8'}).trim(),
  status: execFileSync('git', ['-C', root, 'status', '--porcelain=v1', '--untracked-files=all'], {encoding: 'utf8'}).trim()});

export function captureSamples(caseId, samples, end) {
  const start = samples.find(row => row.time_seconds === 0 && row.side === 'after');
  assert.ok(start, 'A native initial after-side sample is required');
  const choose = (target, predicate) => {
    const available = samples.filter(row => row.side === 'after' && row.time_seconds > 0 && row.time_seconds < end && predicate(row.time_seconds));
    available.sort((a, b) => Math.abs(a.time_seconds - target) - Math.abs(b.time_seconds - target) || a.sample_id.localeCompare(b.sample_id));
    assert.ok(available.length, 'An action-specific native reference sample is required for ' + caseId); return available[0];
  };
  let moving, extra = [];
  if (caseId === 'L01') {
    moving = choose(1, t => t > .5 && t < 1.5);
    extra = [{purpose: 'resumed moving action', sample: choose(2, t => t > 1.5)}];
  } else if (caseId === 'L02') moving = choose(1, t => t > .5);
  else if (caseId === 'L03' || caseId === 'P16') moving = choose(2.5, t => t > 2);
  else moving = choose(end / 2, () => true);
  return {captures: [{view: 'front', camera: 'front', sample: start}, {view: 'side', camera: 'side', sample: start},
    {view: 'intermediate', camera: 'front', sample: moving}], extra};
}

export function compareReadback(state, observed, sample) {
  assert.equal(observed.case_id, state.item.case_id); assert.equal(observed.artifact_sha256, state.item.artifact.sha256);
  assert.equal(observed.decoded.program_revision, state.item.program_revision);
  assert.equal(observed.decoded.target_contract, 'ontokin.glb/0.6'); assert.equal(observed.decoded.schema_version, '0.6');
  assert.equal(observed.decoded.three_revision, '180');
  assert.deepEqual(observed.decoded.source_manifest, state.document.extras.ontokin.program.manifest);
  assert.deepEqual(observed.decoded.player, state.native.controlled_player);
  const tolerance = state.reference.tolerances, p2 = square(parseRational(tolerance.position_m)), r2 = square(parseRational(tolerance.rotation_rad));
  const local2 = square(parseRational(tolerance.local_vertex_m)), worldLimit = numberInterval(p2)[0];
  assert.ok(Math.abs(observed.time_seconds - sample.time_seconds) <= tolerance.time_s, 'Actual UI seek time exceeds its tolerance');
  assert.equal(observed.displayed_time, String(observed.time_seconds) + ' s');
  assert.deepEqual(observed.camera.up, [0, 1, 0]);
  assert.equal(observed.camera.fit_policy, 'all_recorded_translation_keys_plus_native_carrier_radii/0.1');
  assert.equal(observed.camera.fit_stored_key_count, state.plan.stored_key_count);
  assert.ok(observed.camera.near_m > 0 && observed.camera.far_m > observed.camera.near_m);
  for (const field of ['position_m', 'orientation_xyzw', 'target_m', 'bounds_min_m', 'bounds_max_m'])
    assert.ok(observed.camera[field].every(Number.isFinite), 'Finite fitted camera ' + field);
  const nodes = state.reference.expected_nodes;
  assert.deepEqual(Object.keys(observed.objects).sort(), nodes.map(node => node.path).sort());
  assert.equal(observed.render.triangles, state.native.geometry.triangles, 'Every native triangle must be drawn');
  assert.ok(observed.render.calls > 0);
  const maxima = {position_error_upper_m: 0, rotation_error_upper_rad: 0, site_error_upper_m: 0,
    world_probe_error_upper_m: 0, carriers: nodes.length, sites: 0, world_probes: 0};
  for (const expected of nodes) {
    const actual = observed.objects[expected.path], sourcePose = sample.poses[expected.path];
    assert.deepEqual(actual.element_id, expected.element_id); assert.equal(actual.path, expected.path); assert.equal(actual.kind, 'object');
    const nativeNode = state.document.nodes.find(node => node.extras.ontokin.path === expected.path);
    assert.deepEqual(actual.source_mapping, nativeNode.extras.ontokin.source_mapping);
    const position = enclosure(sourcePose.position_m, 3, 'Independent browser source position');
    const orientation = enclosure(sourcePose.orientation_wxyz, 4, 'Independent browser source orientation');
    const positionError = positionSquaredError(actual.position_m, position), rotationError = quaternionAngleSquaredUpper(actual.orientation_wxyz, orientation);
    assert.ok(compare(positionError, p2) <= 0, 'Browser carrier position differs: ' + expected.path);
    assert.ok(compare(rotationError, r2) <= 0, 'Browser carrier orientation differs: ' + expected.path);
    maxima.position_error_upper_m = Math.max(maxima.position_error_upper_m, errorUpperNumber(positionError));
    maxima.rotation_error_upper_rad = Math.max(maxima.rotation_error_upper_rad, errorUpperNumber(rotationError));
    assert.equal(actual.matrix_world.length, 16); assert.ok(actual.matrix_world.every(Number.isFinite));
    for (const site of expected.sites) {
      const m = actual.matrix_world, [x, y, z] = site.position_m;
      const point = [m[0] * x + m[4] * y + m[8] * z + m[12], m[1] * x + m[5] * y + m[9] * z + m[13], m[2] * x + m[6] * y + m[10] * z + m[14]];
      const error = positionSquaredError(point, enclosure(sample.sites[site.path], 3, 'Independent browser source site'));
      assert.ok(compare(error, p2) <= 0, 'Browser matrix site differs: ' + site.path);
      maxima.site_error_upper_m = Math.max(maxima.site_error_upper_m, errorUpperNumber(error)); maxima.sites++;
    }
    if (expected.geometry === null) { assert.deepEqual(actual.primitives, []); continue; }
    const geometry = expected.geometry, transform = floatTransformEnclosure(position, orientation);
    assert.equal(actual.primitives.length, geometry.primitives.length);
    for (let index = 0; index < geometry.primitives.length; index++) {
      const wanted = geometry.primitives[index], primitive = actual.primitives[index];
      assert.equal(primitive.region_key, wanted.material.region_key); assert.deepEqual(primitive.base_color, wanted.material.base_color);
      assert.equal(primitive.metallic, wanted.material.metallic); assert.equal(primitive.roughness, wanted.material.roughness);
      assert.equal(primitive.vertices, geometry.positions.length); assert.equal(primitive.indices, wanted.indices.length);
      assert.equal(primitive.triangles, wanted.indices.length / 3); assert.ok(primitive.probes.length > 0);
      for (const probe of primitive.probes) {
        assert.ok(Number.isSafeInteger(probe.vertex_index) && probe.vertex_index >= 0 && probe.vertex_index < geometry.positions.length);
        const local = geometry.positions[probe.vertex_index], localIntervals = local.map(value => [fromNumber(value), fromNumber(value)]);
        assert.ok(compare(positionSquaredError(probe.local_m, localIntervals), local2) <= 0, 'Browser local vertex differs');
        const error = floatPositionSquaredUpper(probe.world_m, transformedPointBounds(transform, local));
        assert.ok(error <= worldLimit, 'Browser world surface differs');
        assert.ok(probe.camera_ndc.every(value => Number.isFinite(value) && Math.abs(value) <= 1 + 1e-9), 'Native surface is clipped');
        maxima.world_probe_error_upper_m = Math.max(maxima.world_probe_error_upper_m, errorUpperNumber(fromNumber(error))); maxima.world_probes++;
      }
    }
  }
  return maxima;
}

async function run(options) {
  const output = path.resolve(options.output), selected = options.cases;
  assert.ok(!path.relative(root, output).split(path.sep).every(part => part !== '..'), 'Evidence belongs outside the checkout');
  await mkdir(output, {recursive: false});
  const git = identity(), report = {schema_version: SCHEMA, status: 'running', started_at: new Date().toISOString(),
    source_git: git, release_acceptance: false, visual_review: 'pending_actual_image_inspection', agent_transport_audited: false,
    environment: {node: process.version, platform: process.platform, architecture: process.arch,
      required_node_major: 22, viewport: {width: 1220, height: 1140}, device_scale_factor: 1,
      renderer: 'Chromium WebGL2 / ANGLE SwiftShader', timeline_input: 'actual range value and input event'},
    cases: [], captures: [], playback: [], page_errors: [], console_errors: [], failed_requests: [], network_requests: [],
    limitations: ['Every retained capture still requires separate actual visual review.',
      'Browser site comparisons apply source local offsets to actual browser matrix readbacks on the host.',
      'Random playback pause clocks establish control behavior; numeric source comparisons use the exact identified seek schedule.',
      'Native and source certificates, Agent transport, compatibility, inherited workflows and complete release acceptance remain separate roles.']};
  const observed = new Map(); let browser;
  const read = async filename => {
    const resolved = await realpath(filename), raw = await boundedRead(resolved);
    const descriptor = {sha256: sha256(raw), bytes: raw.length};
    if (observed.has(resolved)) assert.deepEqual(observed.get(resolved), descriptor);
    observed.set(resolved, descriptor); return raw;
  };
  try {
    assert.equal(git.status, '', 'Execute browser evidence from a clean committed checkout');
    assert.equal(Number(process.versions.node.split('.')[0]), 22, 'Reach release browser checks require Node 22');
    const manifestPath = await realpath(options.manifest), directory = path.dirname(manifestPath), manifestRaw = await read(manifestPath);
    const manifest = parseJson(manifestRaw), nativeRaw = await read(options.native), native = parseJson(nativeRaw);
    assert.equal(manifest.schema_version, 'ontokin.reach-native-input/0.1');
    assert.equal(native.schema_version, 'ontokin.reach-native-validation/0.1'); assert.equal(native.status, 'passed');
    assert.deepEqual(native.manifest, {sha256: sha256(manifestRaw), bytes: manifestRaw.length});
    assert.equal(native.source_kind, manifest.source_kind); assert.equal(native.failed_cases, 0);
    report.source_kind = manifest.source_kind; report.native_report = {sha256: sha256(nativeRaw), bytes: nativeRaw.length};
    report.manifest = native.manifest; report.producer_source_commit = manifest.source_commit; report.producer_source_tree = manifest.source_tree;
    const required = manifest.source_kind === 'source_component' ? SOURCE_CASES : AGENT_CASES;
    assert.ok(['source_component', 'agent_retrieved_artifact'].includes(manifest.source_kind));
    const names = selected.length ? selected : required;
    assert.equal(new Set(names).size, names.length); assert.ok(names.length > 0 && names.length <= LIMITS.cases);
    report.selected_cases = names; report.complete_browser_corpus = names.length === required.length && required.every(name => names.includes(name));
    report.implementation_inputs = {};
    for (const relative of SELF_INPUTS) {
      const raw = await read(await containedPath(root, relative)); report.implementation_inputs[relative] = {sha256: sha256(raw), bytes: raw.length};
    }
    for (const [relative, descriptor] of Object.entries(native.implementation_inputs))
      assert.equal(sha256(await read(await containedPath(root, relative))), descriptor.sha256, 'Native verifier implementation changed');
    const packages = parseJson(await read(path.join(root, 'tools/package.json')));
    for (const [dependency, version] of Object.entries({three: '0.180.0', playwright: '1.56.1', esbuild: '0.25.10'})) {
      assert.equal(packages.devDependencies[dependency], version);
      assert.equal(JSON.parse(await readFile(path.join(root, 'tools/node_modules', dependency, 'package.json'), 'utf8')).version, version);
    }
    report.environment.dependencies = {three: '0.180.0', playwright: '1.56.1', esbuild: '0.25.10'};
    const states = [], datasets = []; let totalArtifactBytes = 0;
    for (const name of names) {
      assert.match(name, /^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$/);
      const item = manifest.cases.find(row => row.case_id === name), accepted = native.cases.find(row => row.case_id === name);
      assert.ok(item && accepted?.status === 'passed', 'Missing independently checked actual artifact ' + name);
      assert.deepEqual(item.artifact, accepted.artifact); assert.deepEqual(item.reference, accepted.reference); assert.deepEqual(item.sources, accepted.sources);
      const descriptorRead = async descriptor => {
        const raw = await read(await containedPath(directory, descriptor.path));
        assert.equal(raw.length, descriptor.bytes); assert.equal(sha256(raw), descriptor.sha256); return raw;
      };
      const artifact = await descriptorRead(item.artifact), reference = parseJson(await descriptorRead(item.reference));
      for (const source of item.sources) await descriptorRead(source);
      for (const [relative, expected] of Object.entries(reference.oracle.inputs))
        assert.equal(sha256(await read(await containedPath(root, relative))), expected, 'Independent reference source changed');
      totalArtifactBytes += artifact.length; assert.ok(totalArtifactBytes <= LIMITS.bytes, 'Split browser manifests before exceeding the bounded aggregate GLB bytes');
      const parsed = parseGlb(artifact), plan = requiredPlan(parsed); checkSampleCoverage(reference.samples, plan, reference.source_boundary_times_seconds);
      const end = plan.times.at(-1), captures = captureSamples(name, reference.samples, end);
      states.push({item, reference, native: accepted, document: parsed.document, plan, end, captures});
      datasets.push({case_id: name, artifact_sha256: item.artifact.sha256, end, glb: artifact.toString('base64')});
    }
    const harnessSource = (await read(path.join(root, 'tools/reach_viewer_harness.mjs'))).toString('utf8');
    const compiled = await build({stdin: {contents: harnessSource, resolveDir: path.join(root, 'tools'), sourcefile: 'reach-browser-harness.mjs'},
      bundle: true, minify: true, format: 'esm', target: ['es2022'], write: false});
    const script = Buffer.from(compiled.outputFiles[0].text).toString('base64');
    const data = JSON.stringify(datasets).replaceAll('<', '\\u003c');
    const html = `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>OntoKin reach playback review</title><style>*{box-sizing:border-box}body{margin:0;background:#f3f6f8;color:#243549;font:16px system-ui,sans-serif}main{width:1160px;margin:22px auto;background:white;border:1px solid #d4dde5;border-radius:12px;padding:24px}h1{font-size:25px;margin:0 0 8px}p{margin:6px 0 12px;color:#526477}#viewport{margin:18px 0;width:1100px;height:750px;border-radius:7px;overflow:hidden}.controls{display:flex;gap:12px;align-items:center}button,select{font:inherit;padding:8px 14px;background:white;border:1px solid #a6b6c4;border-radius:5px}input{flex:1}output{min-width:130px}code{font-size:11px;overflow-wrap:anywhere}dt{font-size:12px;font-weight:600;color:#526477}dd{margin:2px 0 8px}</style>
<main><h1>OntoKin reach playback review</h1><p>Source surfaces, materials and recorded articulated motion</p><div class="controls"><label for="fixture">Artifact</label><select id="fixture"></select><button id="front">Front view</button><button id="side">Side view</button></div><div id="viewport"></div><div class="controls"><button id="play">Play</button><input id="timeline" aria-label="Animation time" type="range" min="0" max="1" step="any" value="0"><output id="time">0 s</output></div><dl><dt>Source program revision</dt><dd><code id="revision"></code></dd><dt>Recorded GLB SHA-256</dt><dd><code id="artifact"></code></dd></dl><p>Y-up views keep the complete recorded trajectory within the same frame.</p></main><script>globalThis.REACH_ARTIFACTS=${data};</script><script type="module" src="data:text/javascript;base64,${script}"></script></html>`;
    const harness = path.join(output, 'reach-viewer.html'); await writeFile(harness, html, {flag: 'wx'});
    report.harness = {path: 'reach-viewer.html', sha256: sha256(Buffer.from(html)), bytes: Buffer.byteLength(html)};
    browser = await chromium.launch({headless: true, args: ['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader']});
    report.environment.browser = await browser.version();
    const page = await browser.newPage({viewport: report.environment.viewport, deviceScaleFactor: 1, reducedMotion: 'reduce', serviceWorkers: 'block'});
    page.on('pageerror', error => report.page_errors.push(error.message));
    page.on('console', message => { if (message.type() === 'error') report.console_errors.push(message.text()); });
    page.on('request', request => { if (/^https?:/.test(request.url())) report.network_requests.push(request.url()); });
    page.on('requestfailed', request => report.failed_requests.push({url: request.url(), error: request.failure()?.errorText}));
    await page.route(/^https?:\/\//, route => route.abort()); await page.goto(pathToFileURL(harness).href);
    await page.waitForFunction(() => globalThis.reachViewer?.ready);
    const seek = async time => {
      const accepted = await page.locator('#timeline').evaluate((input, value) => {
        input.value = String(value); input.dispatchEvent(new Event('input', {bubbles: true})); return Number(input.value);
      }, time);
      assert.ok(Number.isFinite(accepted) && Math.abs(accepted - time) <= 1e-6, 'Actual range control changed the requested clock');
    };
    for (const state of states) {
      const name = state.item.case_id; await page.selectOption('#fixture', name);
      await page.waitForFunction(value => globalThis.reachViewer.ready && globalThis.reachViewer.state.case_id === value, name);
      const initial = await page.evaluate(() => globalThis.reachViewer.state);
      assert.equal(initial.time_seconds, 0); assert.equal(initial.view, 'front'); assert.equal(initial.playing, false);
      assert.equal(await page.locator('#timeline').getAttribute('max'), String(state.end));
      assert.equal(await page.locator('#timeline').getAttribute('step'), 'any');
      const filename = name + '-readback.jsonl', handle = await open(path.join(output, filename), 'wx'), hash = createHash('sha256');
      let bytes = 0, count = 0; const caseReport = {case_id: name, artifact: state.item.artifact, reference: state.item.reference,
        program_revision: state.item.program_revision, status: 'running', comparisons: [], action_checks: []}; report.cases.push(caseReport);
      try {
        for (const sample of state.reference.samples) {
          await seek(sample.time_seconds); const actual = await page.evaluate(() => globalThis.reachViewer.state);
          assert.equal(actual.playing, false); assert.deepEqual(actual.camera, initial.camera, 'Seeking must retain the fitted front camera');
          const comparison = compareReadback(state, actual, sample), raw = Buffer.from(JSON.stringify({sample_id: sample.sample_id,
            kind: sample.kind, time_seconds: sample.time_seconds, source_time_seconds: sample.source_time_seconds, side: sample.side, actual, comparison}) + '\n');
          bytes += raw.length; assert.ok(bytes <= LIMITS.bytes, 'Actual per-case browser readback exceeds its byte bound');
          await handle.write(raw); hash.update(raw); count++;
          caseReport.comparisons.push({sample_id: sample.sample_id, time_seconds: sample.time_seconds, side: sample.side, ...comparison});
        }
      } finally { await handle.close(); caseReport.readback = {path: filename, sha256: 'sha256:' + hash.digest('hex'), bytes, samples: count}; }
      for (const extra of state.captures.extra) {
        await seek(extra.sample.time_seconds); const actual = await page.evaluate(() => globalThis.reachViewer.state);
        caseReport.action_checks.push({purpose: extra.purpose, sample_id: extra.sample.sample_id,
          time_seconds: extra.sample.time_seconds, ...compareReadback(state, actual, extra.sample)});
      }
      for (const capture of state.captures.captures) {
        await seek(capture.sample.time_seconds); await page.click('#' + capture.camera);
        await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
        const actual = await page.evaluate(() => globalThis.reachViewer.state), comparison = compareReadback(state, actual, capture.sample);
        assert.equal(actual.view, capture.camera); assert.equal(actual.playing, false);
        if (capture.camera === 'front') assert.deepEqual(actual.camera, initial.camera);
        const file = name + '-' + capture.view + '.png'; await page.screenshot({path: path.join(output, file), fullPage: true});
        report.captures.push({path: file, sha256: sha256(await boundedRead(path.join(output, file))), case_id: name,
          source_kind: manifest.source_kind, program_revision: state.item.program_revision, artifact_sha256: state.item.artifact.sha256,
          view: capture.view, sample_id: capture.sample.sample_id, time_seconds: capture.sample.time_seconds,
          source_time_seconds: capture.sample.source_time_seconds, side: capture.sample.side, actual, comparison});
      }
      await seek(.2 * state.end); await page.click('#play');
      await page.waitForFunction(start => globalThis.reachViewer.state.time_seconds > start, .2 * state.end);
      await page.click('#play'); const paused = await page.evaluate(() => globalThis.reachViewer.state);
      assert.equal(paused.playing, false); assert.ok(paused.time_seconds > .2 * state.end && paused.time_seconds < state.end);
      const later = await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(() => resolve(globalThis.reachViewer.state)))));
      assert.deepEqual(later, paused, 'Pause must preserve every observed state and the camera');
      await seek(state.end - Math.min(.02, state.end / 100)); await page.click('#play');
      await page.waitForFunction(end => !globalThis.reachViewer.state.playing && globalThis.reachViewer.state.time_seconds === end, state.end);
      const completed = await page.evaluate(() => globalThis.reachViewer.state), finalSample = state.reference.samples.find(row => row.time_seconds === state.end && row.side === 'after');
      assert.ok(finalSample); compareReadback(state, completed, finalSample); assert.deepEqual(completed.camera, initial.camera);
      report.playback.push({case_id: name, started_at_seconds: .2 * state.end, paused_at_seconds: paused.time_seconds,
        stopped_at_seconds: completed.time_seconds, stable_pause_across_frames: true, end_comparison_sample: finalSample.sample_id});
      caseReport.status = 'passed';
    }
    report.webgl = await page.evaluate(() => { const gl = document.querySelector('canvas').getContext('webgl2'), debug = gl?.getExtension('WEBGL_debug_renderer_info');
      return gl ? {version: gl.getParameter(gl.VERSION), renderer: gl.getParameter(gl.RENDERER),
        unmasked_renderer: debug ? gl.getParameter(debug.UNMASKED_RENDERER_WEBGL) : null} : null; });
    assert.ok(report.webgl);
    for (const key of ['page_errors', 'console_errors', 'failed_requests', 'network_requests']) assert.deepEqual(report[key], [], key);
    assert.equal(report.captures.length, names.length * 3); assert.equal(report.playback.length, names.length);
    for (const [filename, descriptor] of observed) {
      const raw = await boundedRead(filename); assert.deepEqual({sha256: sha256(raw), bytes: raw.length}, descriptor, 'Input changed during actual browser validation');
    }
    assert.deepEqual(identity(), git, 'Git source changed during browser validation'); report.status = 'passed';
  } catch (error) { report.status = 'failed'; report.failure = {name: error.name, message: error.message, stack: error.stack}; }
  finally {
    if (browser) await browser.close(); report.finished_at = new Date().toISOString();
    report.inputs = [...observed].map(([filename, descriptor]) => ({path: filename, ...descriptor}));
    await writeFile(path.join(output, 'browser-validation.json'), JSON.stringify(report, null, 2) + '\n', {flag: 'wx'});
  }
  return report;
}

async function main(args) {
  if (args.length === 1 && args[0] === '--help') {
    console.log('Usage: node tools/verify_reach_viewer.mjs --manifest native-input.json --native-report passed-native-report.json --output-dir FRESH_DIR [--case P01 ...]'); return;
  }
  const options = {cases: []};
  for (let index = 0; index < args.length; index += 2) {
    assert.ok(['--manifest', '--native-report', '--output-dir', '--case'].includes(args[index]) && args[index + 1], 'Invalid command option');
    const key = {'--manifest': 'manifest', '--native-report': 'native', '--output-dir': 'output', '--case': 'case'}[args[index]];
    if (key === 'case') options.cases.push(args[index + 1]);
    else { assert.equal(options[key], undefined, 'Duplicate command option'); options[key] = args[index + 1]; }
  }
  assert.ok(options.manifest && options.native && options.output, 'Manifest, actual native report and fresh output directory are required');
  const report = await run(options);
  console.log(JSON.stringify({status: report.status, cases: report.cases.length, captures: report.captures.length,
    complete_browser_corpus: report.complete_browser_corpus, output: path.resolve(options.output), failure: report.failure?.message}));
  if (report.status !== 'passed') process.exitCode = 1;
}
if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href)
  main(process.argv.slice(2)).catch(error => { console.error(error.message); process.exitCode = 1; });
