/** Explicit controlled CPU destination for the finite .22 torque recording.
 * The arithmetic is imported unchanged from the identified .6 module.
 * This attachment admits native .22 metadata without rewriting any bytes.
 */
import { ArithmeticBudget, sampleControlled } from './reach_destination.mjs';
export { ArithmeticBudget, sampleControlled } from './reach_destination.mjs';
export const DESTINATION_NAME = 'ontokin-controlled-three-recording';
export const DESTINATION_VERSION = '0.2.0';
export const THREE_REVISION = '180';
const MAX_POSES = 250000;
const MAX_COMPONENTS = 64 * 1024 * 1024 / 4;

function identityTransform(object) {
  return object.position.x === 0 && object.position.y === 0 && object.position.z === 0
    && object.quaternion.x === 0 && object.quaternion.y === 0 && object.quaternion.z === 0
    && Math.abs(object.quaternion.w) === 1
    && object.scale.x === 1 && object.scale.y === 1 && object.scale.z === 1;
}

function identitySceneChain(scene, work) {
  const chain = [], seen = new Set();
  for (let parent = scene; parent; parent = parent.parent) {
    work.tick();
    if (seen.has(parent) || chain.length >= MAX_POSES)
      throw new Error('reach_destination_parent_domain');
    if (!identityTransform(parent)) throw new Error('reach_destination_nonidentity_parent');
    seen.add(parent); chain.push(parent);
  }
  return chain;
}

function admitSceneChain(scene, chain) {
  // The entire traversal was charged before the final callback. Read only
  // the captured bounded chain, so a new/cyclic parent cannot add uncharged
  // work or hide a changed world transform during publication.
  if (chain[0] !== scene) throw new Error('reach_destination_scene_identity');
  for (let i = 0; i < chain.length; i++) {
    if (chain[i].parent !== (chain[i + 1] ?? null)
        || !identityTransform(chain[i]))
      throw new Error('reach_destination_nonidentity_parent');
  }
}

export async function attachTorquePlayback(gltf, { threeRevision, check = null } = {}) {
  if (String(threeRevision) !== THREE_REVISION) throw new Error('reach_destination_three_identity');
  const json = gltf.parser.json;
  const scene = gltf.scene;
  const metadata = json.extras?.ontokin;
  if (metadata?.target_contract !== 'ontokin.glb/0.22' || metadata?.schema_version !== '0.22'
      || metadata?.profile !== 'torque-0.1') throw new Error('torque_destination_contract');
  const profile = metadata.torque_profile;
  const expected = {
    schema_version: 'ontokin.torque-recording/0.1', source_profile: 'torque-0.1',
    motion_model: 'finite_cartesian_world_axis_external_couple_on_free_own_sphere',
    axis_domain: ['world_x', 'world_y', 'world_z'], descendants: 'fixed_rigid_massless_visual_markers',
    transform_policy: 'all_nodes_are_roots_with_baked_world_poses',
    quantization_contract: 'ontokin.torque-quantization/0.1', live_solver_embedded: false,
  };
  if (!profile || typeof profile !== 'object' || Array.isArray(profile)
      || Object.keys(profile).length !== Object.keys(expected).length
      || Object.entries(expected).some(([key, value]) => Array.isArray(value)
        ? !Array.isArray(profile[key]) || profile[key].length !== value.length
          || value.some((item, index) => item !== profile[key][index])
        : profile[key] !== value)) throw new Error('torque_destination_profile');
  const quantization = metadata.reach_quantization;
  if (!quantization || quantization.schema_version !== 'ontokin.torque-quantization/0.1'
      || quantization.rotation_interpolation !== 'shortest_arc_slerp'
      || quantization.clock_conversion !== 'binary32_rne_ties_to_even_from_exact_rational'
      || quantization.destination_numeric_bound_basis?.name !== DESTINATION_NAME
      || quantization.destination_numeric_bound_basis?.version !== DESTINATION_VERSION)
    throw new Error('torque_destination_quantization');
  if (!identityTransform(gltf.scene)) throw new Error('reach_destination_scene_transform');
  if (json.animations?.length !== 1) throw new Error('reach_destination_clip_count');
  const work = new ArithmeticBudget(check), animation = json.animations[0], groups = new Map();
  if (!Array.isArray(animation.channels) || !Array.isArray(animation.samplers)
      || !Array.isArray(json.accessors)) throw new Error('reach_destination_channel_shape');
  let components = 0, poses = 0, commonClock = null;
  // Count repeated channel references before asking GLTFLoader for arrays.
  for (const channel of animation.channels) {
    work.tick();
    const sampler = animation.samplers[channel.sampler];
    const input = sampler && json.accessors[sampler.input], output = sampler && json.accessors[sampler.output];
    const arity = channel.target?.path === 'rotation' ? 4 : channel.target?.path === 'translation' ? 3 : 0;
    if (!arity || !sampler || !input || !output || sampler.interpolation !== 'LINEAR'
        || input.type !== 'SCALAR' || input.componentType !== 5126
        || output.type !== (arity === 4 ? 'VEC4' : 'VEC3') || output.componentType !== 5126
        || !Number.isInteger(channel.target.node) || channel.target.node < 0
        || !Number.isInteger(input.count)
        || input.count <= 0 || input.count > 10000 || output.count !== input.count)
      throw new Error('reach_destination_channel_shape');
    if (commonClock === null) commonClock = sampler.input;
    if (commonClock !== sampler.input) throw new Error('torque_destination_common_clock');
    components += input.count + output.count * arity;
    if (components > MAX_COMPONENTS) throw new Error('reach_destination_component_budget');
    if (!groups.has(channel.target.node)) { groups.set(channel.target.node, {}); poses += input.count; }
    if (poses > MAX_POSES) throw new Error('reach_destination_pose_budget');
    const group = groups.get(channel.target.node);
    if (group[channel.target.path]) throw new Error('reach_destination_duplicate_channel');
    group[channel.target.path] = sampler;
  }
  const objects = new Map();
  for (const [object, association] of gltf.parser.associations) {
    work.tick();
    if (groups.has(association.nodes)) objects.set(association.nodes, object);
  }
  const tracks = [];
  for (const [index, group] of groups) {
    work.tick();
    const object = objects.get(index);
    if (!object || !group.translation || !group.rotation || group.translation.input !== group.rotation.input)
      throw new Error('reach_destination_missing_carrier');
    // Recorded transforms are world carriers. Even an identity-at-zero
    // animated ancestor would invalidate that meaning at a later sample.
    if (object.parent !== gltf.scene) throw new Error('reach_destination_nonroot_carrier');
    identitySceneChain(gltf.scene, work);
    const clock = await gltf.parser.getDependency('accessor', group.translation.input);
    const position = await gltf.parser.getDependency('accessor', group.translation.output);
    const rotation = await gltf.parser.getDependency('accessor', group.rotation.output);
    work.tick();
    if (clock.itemSize !== 1 || position.itemSize !== 3 || rotation.itemSize !== 4
        || clock.count !== position.count || clock.count !== rotation.count)
      throw new Error('torque_destination_accessor_shape');
    let previous = -Infinity;
    for (let i = 0; i < clock.count; i++) {
      work.tick();
      const time = clock.getX(i);
      if (!Number.isFinite(time) || time < 0 || time <= previous)
        throw new Error('torque_destination_clock_order');
      previous = time;
    }
    tracks.push({ object, clock, position, rotation });
  }
  const values = (attribute, i, size) => [attribute.getX(i), attribute.getY(i), attribute.getZ(i),
    size === 4 ? attribute.getW(i) : undefined].slice(0, size);
  return {
    name: DESTINATION_NAME, version: DESTINATION_VERSION, carrierCount: tracks.length,
    setTime(time) {
      const sampling = new ArithmeticBudget(check);
      if (!Number.isFinite(time)) throw new Error('reach_destination_nonfinite_time');
      if (gltf.scene !== scene) throw new Error('reach_destination_scene_identity');
      const sceneChain = identitySceneChain(scene, sampling);
      const updates = [];
      for (const track of tracks) {
        sampling.tick();
        const { object, clock, position, rotation } = track;
        if (object.parent !== gltf.scene) throw new Error('reach_destination_nonroot_carrier');
        let low = 0, high = clock.count - 1;
        while (low + 1 < high) {
          sampling.tick();
          const middle = Math.floor((low + high) / 2);
          if (clock.getX(middle) <= time) low = middle; else high = middle;
        }
        if (clock.count === 1) { low = 0; high = 0; }
        const first = clock.getX(low), last = high === low ? first + 1 : clock.getX(high);
        const sample = sampleControlled(values(position, low, 3), values(position, high, 3),
          values(rotation, low, 4), values(rotation, high, 4), high === low ? first : time,
          first, last, sampling);
        updates.push({ object, sample });
      }
      // Precharge every bounded write before publishing any scene component.
      // A budget or callback failure leaves all carriers at their prior time.
      for (const parent of sceneChain) sampling.tick();
      for (const update of updates) sampling.tick();
      // Final source/parent admission is callback-free. A mutation at the last
      // charged operation cannot publish poses into a changed world graph.
      if (gltf.scene !== scene) throw new Error('reach_destination_scene_identity');
      admitSceneChain(scene, sceneChain);
      for (const { object } of updates) {
        if (object.parent !== scene) throw new Error('reach_destination_nonroot_carrier');
      }
      for (const { object, sample } of updates) {
        object.position.fromArray(sample.position);
        object.quaternion.fromArray(sample.quaternion);
        object.scale.set(1, 1, 1);
        object.updateMatrix();
      }
      scene.updateMatrixWorld(true);
      return { operations: sampling.operations };
    },
  };
}
