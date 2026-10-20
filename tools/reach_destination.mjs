/** Identified, bounded CPU playback for recorded OntoKin reach artifacts.
 *
 * Exact short-arc SLERP remains the format/reference interpolant. This player
 * uses the explicitly certified normalized-chord approximation. It never calls
 * host trigonometry or sqrt to choose a position or quaternion component.
 */
export const DESTINATION_NAME = 'ontokin-controlled-three-recording';
export const DESTINATION_VERSION = '0.1.0';
export const THREE_REVISION = '180';
const MAX_BITS = 32768;
const MAX_INTEGER = ((1n << BigInt(MAX_BITS - 1)) - 1n) * 2n + 1n;
const MIN_INTEGER = -MAX_INTEGER;
const MAX_OPERATIONS = 100000;
const MAX_POSES = 250000;
const MAX_COMPONENTS = 64 * 1024 * 1024 / 4;
const buffer = new ArrayBuffer(8);
const view = new DataView(buffer);

export class ArithmeticBudget {
  constructor(check = null) { this.operations = 0; this.check = check; }
  poll() { if (this.check) this.check(); }
  tick() {
    this.poll();
    if (this.operations >= MAX_OPERATIONS) throw new Error('reach_destination_work_budget');
    this.operations++;
  }
  bits(...values) {
    for (const value of values) {
      // Reject before toString can allocate a representation of an oversized
      // externally supplied BigInt. The fixed sentinel is only 4096 bytes.
      if (typeof value !== 'bigint' || value > MAX_INTEGER || value < MIN_INTEGER)
        throw new Error('reach_destination_operand_budget');
    }
  }
  width(value) {
    if (!Number.isSafeInteger(value) || value < 0 || value > MAX_BITS)
      throw new Error('reach_destination_operand_budget');
  }
  product(a, b) {
    this.tick(); this.bits(a, b); this.width(bitLength(a) + bitLength(b));
    const result = a * b; this.poll(); return result;
  }
  sum(a, b) {
    this.tick(); this.bits(a, b); this.width(Math.max(bitLength(a), bitLength(b)) + 1);
    const result = a + b; this.poll(); return result;
  }
  shift(value, amount) {
    this.tick(); this.bits(value); this.width(amount);
    this.width(bitLength(value) + amount);
    const result = value << BigInt(amount); this.poll(); return result;
  }
  quotient(n, d) {
    this.tick(); this.bits(n, d);
    if (d === 0n) throw new Error('reach_destination_zero_denominator');
    const result = n / d; this.poll(); return result;
  }
  divrem(n, d) {
    this.tick(); this.bits(n, d);
    if (d === 0n) throw new Error('reach_destination_zero_denominator');
    const result = [n / d, n % d]; this.poll(); return result;
  }
}

function bitLength(n) {
  if (typeof n !== 'bigint' || n > MAX_INTEGER || n < MIN_INTEGER)
    throw new Error('reach_destination_operand_budget');
  return (n < 0n ? -n : n).toString(2).length;
}
function gcd(a, b, work) {
  a = a < 0n ? -a : a;
  work.bits(a, b);
  while (b) { work.tick(); const next = a % b; a = b; b = next; }
  work.poll();
  return a;
}
function ratio(n, d, work) {
  work.tick(); work.bits(n, d);
  if (d === 0n) throw new Error('reach_destination_zero_denominator');
  if (d < 0n) { n = -n; d = -d; }
  if (n === 0n) return { n: 0n, d: 1n };
  const common = gcd(n, d, work);
  return { n: work.quotient(n, common), d: work.quotient(d, common) };
}
const ZERO = Object.freeze({ n: 0n, d: 1n });
const ONE = Object.freeze({ n: 1n, d: 1n });
function add(a, b, work) {
  return ratio(work.sum(work.product(a.n, b.d), work.product(b.n, a.d)), work.product(a.d, b.d), work);
}
function negate(a, work) { work.tick(); work.bits(a.n, a.d); return { n: -a.n, d: a.d }; }
function sub(a, b, work) { return add(a, negate(b, work), work); }
function mul(a, b, work) { return ratio(work.product(a.n, b.n), work.product(a.d, b.d), work); }
function div(a, b, work) { return ratio(work.product(a.n, b.d), work.product(a.d, b.n), work); }
function compare(a, b, work) {
  const difference = work.sum(work.product(a.n, b.d), -work.product(b.n, a.d));
  return difference < 0n ? -1 : difference > 0n ? 1 : 0;
}

function exactNumber(value, work) {
  work.tick();
  if (!Number.isFinite(value)) throw new Error('reach_destination_nonfinite_input');
  if (value === 0) return ZERO;
  view.setFloat64(0, value, false);
  const bits = view.getBigUint64(0, false);
  const exponent = Number((bits >> 52n) & 2047n);
  const negative = Boolean(bits >> 63n);
  const mantissa = (bits & ((1n << 52n) - 1n)) + (exponent ? 1n << 52n : 0n);
  const shift = (exponent || 1) - 1023 - 52;
  return ratio(work.shift(negative ? -mantissa : mantissa, Math.max(shift, 0)),
               work.shift(1n, Math.max(-shift, 0)), work);
}

function floorLogRatio(n, d, work) {
  work.tick(); work.bits(n, d);
  let exponent = bitLength(n) - bitLength(d);
  if (exponent >= 0 ? n < work.shift(d, exponent) : work.shift(n, -exponent) < d) exponent--;
  return exponent;
}
function nearestEven(n, d, work) {
  const [q, remainder] = work.divrem(n, d), twice = work.shift(remainder, 1);
  return twice > d || (twice === d && Boolean(q & 1n)) ? work.sum(q, 1n) : q;
}
function roundedNumber(value, work) {
  work.tick();
  if (value.n === 0n) return 0;
  const negative = value.n < 0n;
  const n = negative ? -value.n : value.n;
  let exponent = floorLogRatio(n, value.d, work);
  if (exponent > 1023) throw new Error('reach_destination_nonfinite_output');
  const shift = exponent < -1022 ? 1074 : 52 - exponent;
  const numerator = work.shift(n, Math.max(shift, 0));
  const denominator = work.shift(value.d, Math.max(-shift, 0));
  let q = nearestEven(numerator, denominator, work), bits;
  if (exponent < -1022) bits = q;
  else {
    if (q === 1n << 53n) { q >>= 1n; exponent++; }
    if (exponent > 1023) throw new Error('reach_destination_nonfinite_output');
    bits = (BigInt(exponent + 1023) << 52n) | (q - (1n << 52n));
  }
  if (negative && bits) bits |= 1n << 63n;
  work.tick();
  view.setBigUint64(0, bits, false);
  return view.getFloat64(0, false);
}

function isqrt(n, work) {
  work.tick(); work.bits(n);
  if (n < 0n) throw new Error('reach_destination_negative_radicand');
  if (n < 2n) return n;
  let x = work.shift(1n, Math.ceil(bitLength(n) / 2));
  for (;;) {
    work.tick();
    const next = work.sum(x, work.quotient(n, x)) >> 1n;
    if (next >= x) { work.poll(); return x; }
    x = next;
  }
}

function normalizedComponent(component, squareNorm, work) {
  work.tick();
  if (component.n === 0n) return 0;
  const square = div(mul(component, component, work), squareNorm, work);
  if (compare(square, ONE, work) > 0) throw new Error('reach_destination_invalid_norm');
  const exponent = Math.floor(floorLogRatio(square.n, square.d, work) / 2);
  const shift = exponent < -1022 ? 1074 : 52 - exponent;
  const n = work.shift(square.n, 2 * shift);
  let q = isqrt(work.quotient(n, square.d), work);
  const midpoint = work.sum(work.shift(q, 1), 1n);
  const right = work.product(square.d, work.product(midpoint, midpoint));
  const left = work.shift(n, 2);
  if (left > right || (left === right && Boolean(q & 1n))) q = work.sum(q, 1n);
  return roundedNumber(ratio(component.n < 0n ? -q : q, work.shift(1n, shift), work), work);
}

function normalize(values, work) {
  if (values.length !== 4) throw new Error('reach_destination_quaternion_arity');
  let squareNorm = ZERO;
  for (const value of values) squareNorm = add(squareNorm, mul(value, value, work), work);
  if (squareNorm.n <= 0n) throw new Error('reach_destination_zero_quaternion');
  return values.map(value => normalizedComponent(value, squareNorm, work));
}

export function sampleControlled(firstPosition, lastPosition, firstQuaternion,
                                  lastQuaternion, time, start, end, check = null) {
  const work = check instanceof ArithmeticBudget ? check : new ArithmeticBudget(check);
  for (const [values, size] of [[firstPosition, 3], [lastPosition, 3], [firstQuaternion, 4], [lastQuaternion, 4]]) {
    work.tick();
    if ((!Array.isArray(values) && !ArrayBuffer.isView(values)) || values.length !== size)
      throw new Error('reach_destination_vector_arity');
  }
  // TypedArray.map coerces its result back to a number; fractions require
  // ordinary arrays. The dimensions are proved before these bounded copies.
  work.tick(); firstPosition = Array.from(firstPosition);
  work.tick(); lastPosition = Array.from(lastPosition);
  work.tick(); firstQuaternion = Array.from(firstQuaternion);
  work.tick(); lastQuaternion = Array.from(lastQuaternion);
  const t = exactNumber(time, work), a = exactNumber(start, work), b = exactNumber(end, work);
  if (compare(a, b, work) >= 0) throw new Error('reach_destination_clock_order');
  let amount = div(sub(t, a, work), sub(b, a, work), work);
  if (compare(amount, ZERO, work) < 0) amount = ZERO;
  if (compare(amount, ONE, work) > 0) amount = ONE;
  const complement = sub(ONE, amount, work);
  const first = normalize(firstQuaternion.map(value => exactNumber(value, work)), work)
    .map(value => exactNumber(value, work));
  let last = normalize(lastQuaternion.map(value => exactNumber(value, work)), work)
    .map(value => exactNumber(value, work));
  let dot = ZERO;
  for (let i = 0; i < 4; i++) dot = add(dot, mul(first[i], last[i], work), work);
  if (dot.n < 0n) last = last.map(value => negate(value, work));
  const quaternion = normalize(first.map((value, i) => add(mul(complement, value, work),
    mul(amount, last[i], work), work)), work);
  const position = firstPosition.map((value, i) => roundedNumber(add(
    mul(complement, exactNumber(value, work), work),
    mul(amount, exactNumber(lastPosition[i], work), work), work), work));
  return { position, quaternion, operations: work.operations };
}

function identityTransform(object) {
  return object.position.x === 0 && object.position.y === 0 && object.position.z === 0
    && object.quaternion.x === 0 && object.quaternion.y === 0 && object.quaternion.z === 0
    && Math.abs(object.quaternion.w) === 1
    && object.scale.x === 1 && object.scale.y === 1 && object.scale.z === 1;
}

function identitySceneChain(scene, work) {
  for (let parent = scene; parent; parent = parent.parent) {
    work.tick();
    if (!identityTransform(parent)) throw new Error('reach_destination_nonidentity_parent');
  }
}

export async function attachReachPlayback(gltf, { threeRevision, check = null } = {}) {
  if (String(threeRevision) !== THREE_REVISION) throw new Error('reach_destination_three_identity');
  const json = gltf.parser.json;
  if (json.extras?.ontokin?.target_contract !== 'ontokin.glb/0.6') throw new Error('reach_destination_contract');
  if (!identityTransform(gltf.scene)) throw new Error('reach_destination_scene_transform');
  if (json.animations?.length !== 1) throw new Error('reach_destination_clip_count');
  const work = new ArithmeticBudget(check), animation = json.animations[0], groups = new Map();
  if (!Array.isArray(animation.channels) || !Array.isArray(animation.samplers)
      || !Array.isArray(json.accessors)) throw new Error('reach_destination_channel_shape');
  let components = 0, poses = 0;
  // Count repeated channel references before asking GLTFLoader for arrays.
  for (const channel of animation.channels) {
    work.tick();
    const sampler = animation.samplers[channel.sampler];
    const input = sampler && json.accessors[sampler.input], output = sampler && json.accessors[sampler.output];
    const arity = channel.target?.path === 'rotation' ? 4 : channel.target?.path === 'translation' ? 3 : 0;
    if (!arity || !sampler || !input || !output || sampler.interpolation !== 'LINEAR' || !Number.isInteger(input.count)
        || input.count <= 0 || input.count > 10000 || output.count !== input.count)
      throw new Error('reach_destination_channel_shape');
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
    tracks.push({ object, clock, position, rotation });
  }
  const values = (attribute, i, size) => [attribute.getX(i), attribute.getY(i), attribute.getZ(i),
    size === 4 ? attribute.getW(i) : undefined].slice(0, size);
  return {
    name: DESTINATION_NAME, version: DESTINATION_VERSION, carrierCount: tracks.length,
    setTime(time) {
      const sampling = new ArithmeticBudget(check);
      if (!Number.isFinite(time)) throw new Error('reach_destination_nonfinite_time');
      identitySceneChain(gltf.scene, sampling);
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
      for (const update of updates) sampling.tick();
      for (const { object, sample } of updates) {
        object.position.fromArray(sample.position);
        object.quaternion.fromArray(sample.quaternion);
        object.scale.set(1, 1, 1);
        object.updateMatrix();
      }
      gltf.scene.updateMatrixWorld(true);
      return { operations: sampling.operations };
    },
  };
}
