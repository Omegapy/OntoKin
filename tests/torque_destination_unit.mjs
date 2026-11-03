import assert from 'node:assert/strict';
import { attachTorquePlayback, DESTINATION_VERSION } from '../tools/torque_destination.mjs';
import { attachReachPlayback } from '../tools/reach_destination.mjs';

const profile = {
  schema_version: 'ontokin.torque-recording/0.1', source_profile: 'torque-0.1',
  motion_model: 'finite_cartesian_world_axis_external_couple_on_free_own_sphere',
  axis_domain: ['world_x', 'world_y', 'world_z'], descendants: 'fixed_rigid_massless_visual_markers',
  transform_policy: 'all_nodes_are_roots_with_baked_world_poses',
  quantization_contract: 'ontokin.torque-quantization/0.1', live_solver_embedded: false,
};
function vector(values) {
  return {
    x: values[0], y: values[1], z: values[2], ...(values.length === 4 ? { w: values[3] } : {}),
    fromArray(values) { this.x = values[0]; this.y = values[1]; this.z = values[2]; if (values.length === 4) this.w = values[3]; },
    set(x, y, z) { this.x = x; this.y = y; this.z = z; },
  };
}
function fixture() {
  const scene = { position: vector([0, 0, 0]), quaternion: vector([0, 0, 0, 1]), scale: vector([1, 1, 1]),
    parent: null, updateMatrixWorld() {} };
  const carrier = { position: vector([0, 0, 0]), quaternion: vector([0, 0, 0, 1]), scale: vector([1, 1, 1]),
    parent: scene, updateMatrix() {} };
  const arrays = [[0, 1], [0, 0, 0, 2, 0, 0], [0, 0, 0, 1, 0, 0, 1, 0]];
  const sizes = [1, 3, 4];
  const attributes = arrays.map((values, index) => ({ itemSize: sizes[index], count: 2,
    getX(i) { return values[i * sizes[index]]; }, getY(i) { return values[i * sizes[index] + 1]; },
    getZ(i) { return values[i * sizes[index] + 2]; }, getW(i) { return values[i * sizes[index] + 3]; } }));
  let loads = 0;
  const json = { extras: { ontokin: { target_contract: 'ontokin.glb/0.22', schema_version: '0.22',
    profile: 'torque-0.1', torque_profile: structuredClone(profile), reach_quantization: {
      schema_version: 'ontokin.torque-quantization/0.1', rotation_interpolation: 'shortest_arc_slerp',
      clock_conversion: 'binary32_rne_ties_to_even_from_exact_rational',
      destination_numeric_bound_basis: { name: 'ontokin-controlled-three-recording', version: '0.2.0' },
    } } },
    accessors: [{ type: 'SCALAR', componentType: 5126, count: 2 },
      { type: 'VEC3', componentType: 5126, count: 2 }, { type: 'VEC4', componentType: 5126, count: 2 }],
    animations: [{ samplers: [{ input: 0, output: 1, interpolation: 'LINEAR' },
      { input: 0, output: 2, interpolation: 'LINEAR' }],
      channels: [{ sampler: 0, target: { node: 0, path: 'translation' } },
        { sampler: 1, target: { node: 0, path: 'rotation' } }] }],
  };
  return { scene, carrier, json, arrays, attributes,
    get loads() { return loads; },
    gltf: { scene, parser: { json, associations: new Map([[carrier, { nodes: 0 }]]),
      async getDependency(kind, index) { loads++; return attributes[index]; } } },
  };
}

let checks = 0;
const original = fixture();
const playback = await attachTorquePlayback(original.gltf, { threeRevision: 180 });
assert.equal(playback.version, DESTINATION_VERSION); checks++;
assert.equal(playback.carrierCount, 1); checks++;
playback.setTime(0.5);
assert.equal(original.carrier.position.x, 1); checks++;
assert.ok(Math.abs(original.carrier.quaternion.z - Math.SQRT1_2) <= 2 ** -52); checks++;
assert.ok(Math.abs(original.carrier.quaternion.w - Math.SQRT1_2) <= 2 ** -52); checks++;
await assert.rejects(attachReachPlayback(original.gltf, { threeRevision: 180 }), /reach_destination_contract/); checks++;
for (const mutate of [
  f => { f.json.extras.ontokin.target_contract = 'ontokin.glb/0.6'; },
  f => { delete f.json.extras.ontokin.torque_profile.axis_domain; },
  f => { f.json.extras.ontokin.torque_profile.extra = true; },
  f => { f.json.extras.ontokin.torque_profile.axis_domain.reverse(); },
  f => { f.json.extras.ontokin.reach_quantization.schema_version = 'ontokin.reach-quantization/0.1'; },
  f => { f.json.extras.ontokin.reach_quantization.destination_numeric_bound_basis.version = '0.1.0'; },
]) {
  const f = fixture(); mutate(f);
  await assert.rejects(attachTorquePlayback(f.gltf, { threeRevision: 180 }));
  assert.equal(f.loads, 0); checks += 2;
}
{
  const f = fixture(); f.carrier.parent = { ...f.scene };
  await assert.rejects(attachTorquePlayback(f.gltf, { threeRevision: 180 }), /nonroot/); checks++;
}
{
  const f = fixture(); f.json.accessors.push({ ...f.json.accessors[0] });
  f.json.animations[0].samplers[1].input = 3;
  await assert.rejects(attachTorquePlayback(f.gltf, { threeRevision: 180 }), /common_clock/); checks++;
  assert.equal(f.loads, 0); checks++;
}
{
  const f = fixture(); let armed = false; const cancellation = new Error('original cancellation');
  const player = await attachTorquePlayback(f.gltf, { threeRevision: 180,
    check() { if (armed) throw cancellation; } });
  armed = true;
  assert.throws(() => player.setTime(0.5), error => error === cancellation); checks++;
  assert.equal(f.carrier.position.x, 0); checks++;
  assert.equal(f.carrier.quaternion.w, 1); checks++;
}
{
  const f = fixture(); let armed = false; let calls = 0;
  const player = await attachTorquePlayback(f.gltf, { threeRevision: 180,
    check() { if (armed) calls++; } });
  armed = true; player.setTime(.5);
  const lastCallback = calls;
  for (const mutation of ['scene_translation', 'carrier_reparent', 'scene_replacement', 'late_cancellation']) {
    const current = fixture(); let on = false; let count = 0; let changed = false;
    const cancellation = new Error('original final cancellation');
    const actual = await attachTorquePlayback(current.gltf, { threeRevision: 180,
      check() { if (on && ++count === lastCallback) {
        changed = true;
        if (mutation === 'scene_translation') current.scene.position.x = 10;
        else if (mutation === 'carrier_reparent') current.carrier.parent = { ...current.scene };
        else if (mutation === 'scene_replacement') current.gltf.scene = { ...current.scene };
        else throw cancellation;
      } } });
    on = true;
    assert.throws(() => actual.setTime(.5), error => mutation === 'late_cancellation'
      ? error === cancellation : /reach_destination_/.test(error.message)); checks++;
    assert.equal(changed, true); checks++;
    assert.equal(count, lastCallback); checks++;
    assert.equal(current.carrier.position.x, 0); checks++;
    assert.equal(current.carrier.quaternion.w, 1); checks++;
  }
}
console.log(JSON.stringify({ status: 'passed', checks, scope: 'Native wrapper unit controls; not actual GLTFLoader or browser acceptance' }));
