/** Independent resource/cancellation probes; no Three, GLB or browser fixture. */
import assert from 'node:assert/strict';
import test from 'node:test';
import { ArithmeticBudget, attachReachPlayback, sampleControlled } from '../tools/reach_destination.mjs';

function transform(parent = null) {
  const object = { parent, writes: 0, worldWrites: 0 };
  object.position = { x: 0, y: 0, z: 0, fromArray(values) {
    [this.x, this.y, this.z] = values; object.writes++;
  } };
  object.quaternion = { x: 0, y: 0, z: 0, w: 1, fromArray(values) {
    [this.x, this.y, this.z, this.w] = values; object.writes++;
  } };
  object.scale = { x: 1, y: 1, z: 1, set(x, y, z) {
    Object.assign(this, { x, y, z }); object.writes++;
  } };
  object.updateMatrix = () => { object.writes++; };
  object.updateMatrixWorld = () => { object.worldWrites++; };
  return object;
}

function attribute(rows, onRead = null) {
  const get = (index, component) => { if (onRead) onRead(); return rows[index][component]; };
  return { count: rows.length, getX: i => get(i, 0), getY: i => get(i, 1),
    getZ: i => get(i, 2), getW: i => get(i, 3) };
}

function fixture(count = 1, secondClockRead = null) {
  const scene = transform(), carriers = [], channels = [], samplers = [], accessors = [], attributes = [];
  const associations = new Map();
  for (let i = 0; i < count; i++) {
    const carrier = transform(scene), offset = attributes.length;
    carriers.push(carrier); associations.set(carrier, { nodes: i });
    attributes.push(attribute([[0], [1]], i === 1 ? secondClockRead : null),
      attribute([[0, 0, 0], [1, 2, 3]]), attribute([[0, 0, 0, 1], [0, 0, 0, 1]]));
    accessors.push({ count: 2 }, { count: 2 }, { count: 2 });
    for (const [path, output] of [['translation', offset + 1], ['rotation', offset + 2]]) {
      channels.push({ sampler: samplers.length, target: { node: i, path } });
      samplers.push({ input: offset, output, interpolation: 'LINEAR' });
    }
  }
  const result = { scene, carriers, dependencyCalls: 0 };
  result.parser = { json: { extras: { ontokin: { target_contract: 'ontokin.glb/0.6' } },
    animations: [{ channels, samplers }], accessors }, associations,
    async getDependency(kind, index) {
      assert.equal(kind, 'accessor'); result.dependencyCalls++; return attributes[index];
    } };
  return result;
}

test('growth guards reject product, carry and shift before allocation', () => {
  const work = new ArithmeticBudget(), maximum = (1n << 32768n) - 1n;
  assert.throws(() => work.product(1n << 20000n, 1n << 20000n), /operand_budget/);
  assert.throws(() => work.sum(maximum, 1n), /operand_budget/);
  assert.throws(() => work.shift(1n, 32768), /operand_budget/);
  assert.throws(() => work.shift(1n, Number.MAX_VALUE), /operand_budget/);
});

test('oversized external integers are rejected before string conversion', () => {
  const enormous = 1n << 40000n, original = BigInt.prototype.toString;
  BigInt.prototype.toString = () => { throw new Error('unexpected string allocation'); };
  try {
    assert.throws(() => new ArithmeticBudget().product(enormous, 1n), /operand_budget/);
  } finally { BigInt.prototype.toString = original; }
});

test('large-operation return preserves the original cancellation object', () => {
  const interruption = new Error('original cancellation');
  let calls = 0;
  const work = new ArithmeticBudget(() => { if (++calls === 2) throw interruption; });
  assert.throws(() => work.product(3n, 7n), error => error === interruption);
  assert.equal(work.operations, 1);
});

test('bounded typed arrays retain exact rational interpolation', () => {
  const sample = sampleControlled(new Float64Array([0, 1, 2]), new Float32Array([3, 4, 5]),
    new Float32Array([0, 0, 0, 1]), new Float64Array([0, 0, 0, 1]), 1, 0, 3);
  assert.deepEqual(sample.position, [1, 2, 3]);
  assert.deepEqual(sample.quaternion, [0, 0, 0, 1]);
  assert.ok(sample.operations > 0 && sample.operations < 100000);
});

test('vector shape is checked before copying its elements', () => {
  const oversized = new Proxy([0, 0, 0], { get(target, key) {
    if (key === 'length') return 1000000;
    if (key === Symbol.iterator) throw new Error('unexpected vector copy');
    return Reflect.get(target, key);
  } });
  assert.throws(() => sampleControlled(oversized, [0, 0, 0], [0, 0, 0, 1], [0, 0, 0, 1],
    0, 0, 1), /vector_arity/);
});

test('identity-at-start ancestors cannot disguise a nonroot world carrier', async () => {
  const gltf = fixture();
  gltf.carriers[0].parent = transform(gltf.scene);
  await assert.rejects(attachReachPlayback(gltf, { threeRevision: '180' }), /nonroot_carrier/);
  assert.equal(gltf.dependencyCalls, 0);
});

test('ancestor transforms are rechecked at each sampled scene', async () => {
  const gltf = fixture(), ancestor = transform();
  gltf.scene.parent = ancestor;
  const player = await attachReachPlayback(gltf, { threeRevision: '180' });
  ancestor.position.x = 1;
  assert.throws(() => player.setTime(0.5), /nonidentity_parent/);
  assert.equal(gltf.carriers[0].writes, 0);
  assert.equal(gltf.scene.worldWrites, 0);
});

test('cancellation during a later carrier leaves every previous pose untouched', async () => {
  let cancel = false;
  const interruption = new Error('cancel the sampled scene');
  const gltf = fixture(2, () => { cancel = true; });
  const player = await attachReachPlayback(gltf, { threeRevision: '180',
    check: () => { if (cancel) throw interruption; } });
  assert.throws(() => player.setTime(0.5), error => error === interruption);
  assert.deepEqual(gltf.carriers.map(object => object.writes), [0, 0]);
  assert.equal(gltf.scene.worldWrites, 0);
});
