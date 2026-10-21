#!/usr/bin/env node
// Focused hostile probes derived from an actual independently valid GLB.
// Recompute transport identities while retaining unrelated source answers.
import assert from 'node:assert/strict';
import {mkdir, realpath, writeFile} from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {boundedRead, containedPath, verifyManifest} from './verify_reach_native.mjs';
import {LIMITS, parseJson, parseGlb, sha256, canonical} from './reach_native_support.mjs';

function repack(document, binary) {
  const json = Buffer.from(JSON.stringify(document)), aligned = Buffer.alloc((json.length + 3) & ~3, 0x20); json.copy(aligned);
  const result = Buffer.alloc(28 + aligned.length + binary.length);
  result.writeUInt32LE(0x46546c67, 0); result.writeUInt32LE(2, 4); result.writeUInt32LE(result.length, 8);
  result.writeUInt32LE(aligned.length, 12); result.writeUInt32LE(0x4e4f534a, 16); aligned.copy(result, 20);
  result.writeUInt32LE(binary.length, 20 + aligned.length); result.writeUInt32LE(0x004e4942, 24 + aligned.length);
  binary.copy(result, 28 + aligned.length); return result;
}
function inputIdentity(raw, filename) { return {path: filename, sha256: sha256(raw), bytes: raw.length}; }
const encode = value => Buffer.from(JSON.stringify(value, null, 2) + '\n');

export async function probeArtifact(manifestFile, caseId, output) {
  const absolute = await realpath(manifestFile), directory = path.dirname(absolute), rawManifest = await boundedRead(absolute);
  const manifest = parseJson(rawManifest); assert.equal(manifest.schema_version, 'ontokin.reach-native-input/0.1');
  const item = manifest.cases.find(row => row.case_id === caseId); assert.ok(item, 'An identified native case is required');
  const observed = new Map([[absolute, sha256(rawManifest)]]);
  async function readDescriptor(descriptor) {
    const filename = await containedPath(directory, descriptor.path), raw = await boundedRead(filename);
    assert.equal(raw.length, descriptor.bytes); assert.equal(sha256(raw), descriptor.sha256);
    observed.set(filename, descriptor.sha256); return raw;
  }
  const rawArtifact = await readDescriptor(item.artifact), originalReference = parseJson(await readDescriptor(item.reference));
  const sources = await Promise.all(item.sources.map(async source => ({source, raw: await readDescriptor(source)})));
  const parsed = parseGlb(rawArtifact), sourceAnswer = canonical({...originalReference, artifact_sha256: null});
  output = path.resolve(output); await mkdir(output, {recursive: false});
  const report = {schema_version: 'ontokin.reach-native-actual-artifact-probes/0.1', status: 'running',
    started_at: new Date().toISOString(), source_manifest: inputIdentity(rawManifest, path.basename(absolute)),
    original_artifact: item.artifact, original_reference: item.reference, case_id: caseId,
    execution: {node: process.version, platform: process.platform, architecture: process.arch},
    release_acceptance: false, probes: []};
  async function execute(name, bytes, reference, expectedCode = null, change = null) {
    const destination = path.join(output, name); await mkdir(destination);
    const artifact = inputIdentity(bytes, 'scene.glb');
    reference.artifact_sha256 = artifact.sha256;
    if (name !== 'missing-observation') assert.equal(canonical({...reference, artifact_sha256: null}), sourceAnswer,
      'A geometry/motion probe must retain its complete independent source answer');
    const referenceBytes = encode(reference), referenceDescriptor = inputIdentity(referenceBytes, 'native-reference.json'), copiedSources = [];
    await writeFile(path.join(destination, artifact.path), bytes, {flag: 'wx'});
    await writeFile(path.join(destination, referenceDescriptor.path), referenceBytes, {flag: 'wx'});
    for (const [index, {source, raw}] of sources.entries()) {
      const descriptor = {...inputIdentity(raw, 'source-' + index + '.ok'), source_id: source.source_id};
      await writeFile(path.join(destination, descriptor.path), raw, {flag: 'wx'}); copiedSources.push(descriptor);
    }
    const input = {...manifest, cases: [{...item, artifact, reference: referenceDescriptor, sources: copiedSources}]};
    const filename = path.join(destination, 'native-input.json'); await writeFile(filename, encode(input), {flag: 'wx'});
    const result = await verifyManifest(filename), resultBytes = encode(result);
    await writeFile(path.join(destination, 'native-validation.json'), resultBytes, {flag: 'wx'});
    const actualCode = result.cases[0]?.failure?.code ?? result.failure?.code ?? null;
    const passed = expectedCode === null ? result.status === 'passed' : result.status === 'failed' && actualCode === expectedCode;
    report.probes.push({name, status: passed ? 'passed' : 'failed', expected_native_status: expectedCode === null ? 'passed' : 'failed',
      expected_rejection_code: expectedCode, actual_native_status: result.status, actual_rejection_code: actualCode,
      artifact, reference: referenceDescriptor, native_report: inputIdentity(resultBytes, name + '/native-validation.json'), change,
      complete_carrier_inventory_preserved: true, unrelated_source_expectations_preserved: true,
      artifact_transport_identity_recomputed: true});
    assert.ok(passed, name + ' did not reach its intended independent comparison: ' + actualCode);
  }
  try {
    assert.equal(Number(process.versions.node.split('.')[0]), 22, 'Native release probes require Node 22');
    await execute('baseline', rawArtifact, structuredClone(originalReference));
    const firstMesh = parsed.document.meshes[0].primitives[0], position = parsed.accessor(firstMesh.attributes.POSITION);
    let binary = Buffer.from(parsed.binary), old = binary.readFloatLE(position.start);
    binary.writeFloatLE(old + .02, position.start);
    await execute('local-vertex', repack(parsed.document, binary), structuredClone(originalReference), 'geometry',
      {accessor: firstMesh.attributes.POSITION, vertex: 0, component: 0, before: old, after: binary.readFloatLE(position.start)});

    binary = Buffer.from(parsed.binary); const indices = parsed.accessor(firstMesh.indices);
    const reader = indices.componentType === 5123 ? 'readUInt16LE' : 'readUInt32LE', writer = indices.componentType === 5123 ? 'writeUInt16LE' : 'writeUInt32LE';
    old = binary[reader](indices.start); binary[writer]((old + 1) % position.count, indices.start);
    await execute('triangle-membership', repack(parsed.document, binary), structuredClone(originalReference), 'geometry',
      {accessor: firstMesh.indices, index: 0, before: old, after: binary[reader](indices.start)});

    let document = structuredClone(parsed.document); const pbr = document.materials[firstMesh.material].pbrMetallicRoughness;
    old = pbr.metallicFactor; pbr.metallicFactor = old === .5 ? .25 : .5;
    await execute('pbr-factor', repack(document, parsed.binary), structuredClone(originalReference), 'material',
      {material: firstMesh.material, factor: 'metallicFactor', before: old, after: pbr.metallicFactor});

    const animation = parsed.document.animations[0], translationChannel = animation.channels.find(row => row.target.path === 'translation');
    const translationIndex = animation.samplers[translationChannel.sampler].output, translation = parsed.accessor(translationIndex);
    assert.ok(translation.count > 1, 'A motion probe requires a noninitial retained key');
    const translationOffset = translation.start + translation.stride;
    binary = Buffer.from(parsed.binary); old = binary.readFloatLE(translationOffset); binary.writeFloatLE(old + .05, translationOffset);
    await execute('recorded-position', repack(parsed.document, binary), structuredClone(originalReference), 'native_position',
      {accessor: translationIndex, key: 1, component: 0, before: old, after: binary.readFloatLE(translationOffset)});

    const rotationChannel = animation.channels.find(row => row.target.path === 'rotation'), rotationIndex = animation.samplers[rotationChannel.sampler].output;
    const rotation = parsed.accessor(rotationIndex), previous = [...rotation.values.slice(4, 8)];
    assert.ok(rotation.count > 1, 'An orientation probe requires a noninitial retained key');
    // Compose a 0.05-radian world-Z rotation with the original unit quaternion.
    // Host trig constructs hostile input; it supplies no expected source pose.
    const s = Math.sin(.025), c = Math.cos(.025), [x, y, z, w] = previous;
    const replacement = [c * x - s * y, c * y + s * x, c * z + s * w, c * w - s * z];
    binary = Buffer.from(parsed.binary); replacement.forEach((value, index) => binary.writeFloatLE(value, rotation.start + rotation.stride + index * 4));
    await execute('recorded-orientation', repack(parsed.document, binary), structuredClone(originalReference), 'native_rotation',
      {accessor: rotationIndex, key: 1, before: previous, after: replacement.map(Math.fround)});

    const missing = structuredClone(originalReference), absent = missing.samples.findIndex(row => row.sample_id === 'key:0');
    assert.ok(absent >= 0); missing.samples.splice(absent, 1);
    await execute('missing-observation', rawArtifact, missing, 'sample_coverage', {removed_sample_id: 'key:0'});

    document = structuredClone(parsed.document); old = document.accessors[firstMesh.attributes.POSITION].count;
    document.accessors[firstMesh.attributes.POSITION].count = LIMITS.components + 1;
    await execute('oversized-accessor', repack(document, parsed.binary), structuredClone(originalReference), 'resource',
      {accessor: firstMesh.attributes.POSITION, before: old, after: LIMITS.components + 1, expected_stage: 'before_native_loader'});
    for (const [filename, expected] of observed) assert.equal(sha256(await boundedRead(filename)), expected, 'Original identified input changed');
    report.status = 'passed';
  } catch (error) { report.status = 'failed'; report.failure = {name: error.name, message: error.message}; }
  report.finished_at = new Date().toISOString(); report.inputs = [...observed].map(([filename, hash]) => ({path: filename, sha256: hash}));
  await writeFile(path.join(output, 'probe-results.json'), encode(report), {flag: 'wx'}); return report;
}
async function main(args) {
  if (args.length === 1 && args[0] === '--help') {
    console.log('Usage: node tools/probe_reach_native_artifact.mjs --manifest native-input.json --case P01 --output-dir FRESH_DIR'); return;
  }
  const options = new Map();
  for (let index = 0; index < args.length; index += 2) {
    assert.ok(['--manifest', '--case', '--output-dir'].includes(args[index]) && args[index + 1] && !options.has(args[index]), 'Invalid or repeated option');
    options.set(args[index], args[index + 1]);
  }
  assert.equal(options.size, 3);
  const report = await probeArtifact(options.get('--manifest'), options.get('--case'), options.get('--output-dir'));
  console.log(JSON.stringify({status: report.status, probes: report.probes.length, failure: report.failure, output: path.resolve(options.get('--output-dir'))}));
  if (report.status !== 'passed') process.exitCode = 1;
}
if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href)
  main(process.argv.slice(2)).catch(error => { console.error(error.message); process.exitCode = 1; });
