// Pure verifier regressions. No Three, writer, or source runtime is imported.
// Run explicitly: node tests/reach_native_resources.mjs (all nine named tests).
import assert from 'node:assert/strict';
import {test} from 'node:test';
import {mkdtemp, mkdir, writeFile, symlink, rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {
  parseJson, parseGlb, requiredPlan, checkSampleCoverage, rational, parseRational,
  fromNumber, nearestNumber, nearestFloat32, compare, square, add, subtract,
  positionSquaredError, quaternionAngleSquaredUpper, enclosure, floatTransformEnclosure,
  transformedPointBounds, floatPositionSquaredUpper, numberInterval,
} from '../tools/reach_native_support.mjs';
import {containedPath, boundedRead} from '../tools/verify_reach_native.mjs';

function rejects(code, callback) {
  assert.throws(callback, error => error.code === code, 'Expected rejection ' + code);
}
function pack(document, binary) {
  const raw = Buffer.from(JSON.stringify(document)), json = Buffer.alloc(Math.ceil(raw.length / 4) * 4, 0x20); raw.copy(json);
  const padded = Buffer.alloc(Math.ceil(binary.length / 4) * 4); binary.copy(padded);
  const header = Buffer.alloc(12), jh = Buffer.alloc(8), bh = Buffer.alloc(8);
  header.writeUInt32LE(0x46546c67); header.writeUInt32LE(2, 4); header.writeUInt32LE(28 + json.length + padded.length, 8);
  jh.writeUInt32LE(json.length); jh.writeUInt32LE(0x4e4f534a, 4); bh.writeUInt32LE(padded.length); bh.writeUInt32LE(0x004e4942, 4);
  return Buffer.concat([header, jh, json, bh, padded]);
}
function fixture() {
  const binary = Buffer.alloc(64); binary.writeFloatLE(1, 4); binary.writeFloatLE(1, 44); binary.writeFloatLE(1, 60);
  const document = {asset: {version: '2.0'}, scene: 0, scenes: [{nodes: [0]}],
    nodes: [{translation: [0, 0, 0], rotation: [0, 0, 0, 1], extras: {ontokin: {kind: 'object', path: 'body'}}}],
    buffers: [{byteLength: 64}], bufferViews: [{buffer: 0, byteOffset: 0, byteLength: 8},
      {buffer: 0, byteOffset: 8, byteLength: 24}, {buffer: 0, byteOffset: 32, byteLength: 32}],
    accessors: [{bufferView: 0, componentType: 5126, count: 2, type: 'SCALAR'},
      {bufferView: 1, componentType: 5126, count: 2, type: 'VEC3'}, {bufferView: 2, componentType: 5126, count: 2, type: 'VEC4'}],
    animations: [{channels: [{sampler: 0, target: {node: 0, path: 'translation'}}, {sampler: 1, target: {node: 0, path: 'rotation'}}],
      samplers: [{input: 0, output: 1, interpolation: 'LINEAR'}, {input: 0, output: 2, interpolation: 'LINEAR'}],
      extras: {ontokin: {target_contract: 'ontokin.glb/0.6', exact_times_seconds: [{numerator: '0', denominator: '1'}, {numerator: '1', denominator: '1'}],
        boundary_times_seconds: ['0', '1']}}}],
    extras: {ontokin: {target_contract: 'ontokin.glb/0.6', profile: 'planar-reach-0.1', program: {revision: 'sha256:' + '0'.repeat(64)}}}};
  return {document, binary, bytes: () => pack(document, binary)};
}

test('strict JSON rejects duplicate semantic keys, overflow, depth and invalid UTF-8', () => {
  rejects('json_duplicate_key', () => parseJson(Buffer.from('{"a":1,"\\u0061":2}')));
  rejects('finite', () => parseJson(Buffer.from('{"x":1e999}')));
  rejects('resource', () => parseJson(Buffer.from('['.repeat(130) + '0' + ']'.repeat(130))));
  rejects('json', () => parseJson(Buffer.from([0xff])));
  rejects('json', () => parseJson(Buffer.from('"\\ud800"')));
  assert.deepEqual(parseJson(Buffer.from('{"a":[1,true,null,"x"]}')), {a: [1, true, null, 'x']});
});

test('GLB checks accessor-local spans and total counts before accessor allocation', () => {
  const a = fixture(); a.document.accessors[1].byteOffset = 4;
  rejects('accessor_span', () => parseGlb(a.bytes()));
  const b = fixture(); b.document.accessors[1].count = 2000000;
  rejects('accessor_budget', () => parseGlb(b.bytes()));
  const c = fixture(); c.document.buffers[0].uri = 'file:///etc/passwd';
  rejects('glb', () => parseGlb(c.bytes()));
  const d = fixture(); d.document.bufferViews[1].byteStride = 10;
  rejects('accessor_span', () => parseGlb(d.bytes()));
});

test('required schedule binds every key, eight interiors, and both source boundary sides', () => {
  const a = fixture(), plan = requiredPlan(parseGlb(a.bytes()));
  assert.equal(plan.required_samples.length, 14);
  assert.equal(plan.required_samples.filter(s => s.kind === 'interval_interior').length, 8);
  assert.deepEqual(plan.required_samples.filter(s => s.kind === 'interval_interior').map(s => s.time_seconds),
    [1 / 16, 1 / 8, 1 / 4, 3 / 8, 1 / 2, 5 / 8, 3 / 4, 7 / 8]);
  checkSampleCoverage(plan.required_samples, plan, ['0', '1']);
  rejects('sample_coverage', () => checkSampleCoverage(plan.required_samples.slice(1), plan, ['0', '1']));
  rejects('sample_coverage', () => checkSampleCoverage([...plan.required_samples, plan.required_samples[0]], plan, ['0', '1']));
  rejects('source_boundaries', () => checkSampleCoverage(plan.required_samples, plan, ['0']));
  const changed = structuredClone(plan.required_samples); changed[2].time_seconds += .01;
  rejects('sample_coverage', () => checkSampleCoverage(changed, plan, ['0', '1']));
});

test('flat complete carriers and one pose authority are independently checked', () => {
  const a = fixture(); a.document.nodes[0].children = [0];
  rejects('carrier_inventory', () => requiredPlan(parseGlb(a.bytes())));
  const b = fixture(); b.document.animations[0].channels[1].target.path = 'translation';
  rejects('accessor_type', () => requiredPlan(parseGlb(b.bytes())));
  const c = fixture(); c.binary.writeFloatLE(.25, 8);
  rejects('identity', () => requiredPlan(parseGlb(c.bytes())));
});

test('binary64 and binary32 conversions round exact rationals without double rounding', () => {
  for (const value of [0, -0, 1, -1, Number.MIN_VALUE, 2 ** -1022, Number.MAX_VALUE, .1, -.003])
    assert.equal(nearestNumber(fromNumber(value)), value === 0 ? 0 : value);
  const halfway = add(rational(1n), rational(1n, 1n << 24n));
  assert.equal(nearestFloat32(halfway), 1);
  const above = add(halfway, rational(1n, 1n << 80n));
  assert.equal(Math.fround(nearestNumber(above)), 1, 'The binary64 intermediate loses which side of the binary32 midpoint this is.');
  assert.equal(nearestFloat32(above), 1 + 2 ** -23);
  assert.equal(nearestFloat32(subtract(halfway, rational(1n, 1n << 80n))), 1);
  assert.equal(nearestFloat32(rational(1n, 1n << 150n)), 0);
  assert.equal(nearestFloat32(rational(3n, 1n << 150n)), 2 ** -148);
});

test('position uses full Euclidean enclosure error without a tolerance epsilon', () => {
  const expected = enclosure([['0', '0'], ['0', '0'], ['0', '0']], 3, 'Point');
  const limit = square(parseRational('1/1000'));
  assert.equal(compare(positionSquaredError([.0005, .0005, 0], expected), limit), -1);
  assert.equal(compare(positionSquaredError([.0008, .0008, 0], expected), limit), 1);
  const exact = enclosure([['1/1000', '1/1000'], ['0', '0'], ['0', '0']], 3, 'Point');
  assert.equal(compare(positionSquaredError([0, 0, 0], exact), limit), 0);
});

test('proper orientation comparison is normalized and sign invariant', () => {
  const expected = enclosure([['1', '1'], ['0', '0'], ['0', '0'], ['0', '0']], 4, 'Rotation');
  assert.equal(quaternionAngleSquaredUpper([-1, 0, 0, 0], expected).n, 0n);
  assert.equal(quaternionAngleSquaredUpper([1.01, 0, 0, 0], expected).n, 0n);
  const limit = square(parseRational('1/1000'));
  assert.equal(compare(quaternionAngleSquaredUpper([1, 0, 0, .0001], expected), limit), -1);
  assert.equal(compare(quaternionAngleSquaredUpper([1, 0, 0, .001], expected), limit), 1);
  // Parse valid exact endpoints before asserting the semantic rejection, so a
  // malformed rational cannot mask the unit-quaternion guard under test.
  const nonUnit = enclosure([['1/2', '1/2'], ['0', '0'], ['0', '0'], ['0', '0']], 4, 'Bad rotation');
  rejects('reference', () => quaternionAngleSquaredUpper([1, 0, 0, 0], nonUnit));
});

test('outward world-vertex arithmetic includes pose and local placement error', () => {
  const p = enclosure([['2', '2'], ['3', '3'], ['4', '4']], 3, 'Translation');
  const q = enclosure([['1', '1'], ['0', '0'], ['0', '0'], ['0', '0']], 4, 'Rotation');
  const bounds = transformedPointBounds(floatTransformEnclosure(p, q), [.2, .3, .4]);
  const threshold = numberInterval(square(parseRational('1/1000')))[0];
  assert.ok(floatPositionSquaredUpper([2.2, 3.3, 4.4], bounds) < threshold);
  assert.ok(floatPositionSquaredUpper([2.202, 3.3, 4.4], bounds) > threshold);
});

test('paths reject traversal and symlink escape; reads enforce actual size', async () => {
  const directory = await mkdtemp(path.join(tmpdir(), 'ontokin-native-resource-'));
  try {
    await mkdir(path.join(directory, 'inputs')); await writeFile(path.join(directory, 'outside'), 'outside');
    await writeFile(path.join(directory, 'inputs', 'source.ok'), 'source');
    await symlink('../outside', path.join(directory, 'inputs', 'escaped.ok'));
    await assert.rejects(containedPath(path.join(directory, 'inputs'), '../outside'), error => error.code === 'input_path');
    await assert.rejects(containedPath(path.join(directory, 'inputs'), 'escaped.ok'), error => error.code === 'input_path');
    const filename = await containedPath(path.join(directory, 'inputs'), 'source.ok');
    await assert.rejects(boundedRead(filename, 5), error => error.code === 'resource');
    assert.equal((await boundedRead(filename, 6)).toString(), 'source');
  } finally { await rm(directory, {recursive: true, force: true}); }
});
