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
const MAX_OPERATIONS = 100000;
const MAX_POSES = 250000;
const MAX_COMPONENTS = 64 * 1024 * 1024 / 4;
const buffer = new ArrayBuffer(8);
const view = new DataView(buffer);

export class ArithmeticBudget {
  constructor(check = null) { this.operations = 0; this.check = check; }
  tick() {
    if (this.check) this.check();
    if (++this.operations > MAX_OPERATIONS) throw new Error('reach_destination_work_budget');
  }
  bits(...values) {
    for (const value of values) {
      if (bitLength(value) > MAX_BITS) throw new Error('reach_destination_operand_budget');
    }
  }
  product(a, b) {
    this.tick();
    if (bitLength(a) + bitLength(b) > MAX_BITS) throw new Error('reach_destination_operand_budget');
    return a * b;
  }
}

function bitLength(n) { return (n < 0n ? -n : n).toString(2).length; }
function gcd(a, b, work) {
  a = a < 0n ? -a : a;
  while (b) { work.tick(); const next = a % b; a = b; b = next; }
  return a;
}
function ratio(n, d, work) {
  work.tick(); work.bits(n, d);
  if (d === 0n) throw new Error('reach_destination_zero_denominator');
  if (d < 0n) { n = -n; d = -d; }
  if (n === 0n) return { n: 0n, d: 1n };
  const common = gcd(n, d, work);
  return { n: n / common, d: d / common };
}
const ZERO = Object.freeze({ n: 0n, d: 1n });
const ONE = Object.freeze({ n: 1n, d: 1n });
function add(a, b, work) {
  return ratio(work.product(a.n, b.d) + work.product(b.n, a.d), work.product(a.d, b.d), work);
}
function negate(a) { return { n: -a.n, d: a.d }; }
function sub(a, b, work) { return add(a, negate(b), work); }
function mul(a, b, work) { return ratio(work.product(a.n, b.n), work.product(a.d, b.d), work); }
function div(a, b, work) { return ratio(work.product(a.n, b.d), work.product(a.d, b.n), work); }
function compare(a, b, work) {
  const difference = work.product(a.n, b.d) - work.product(b.n, a.d);
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
  return ratio((negative ? -mantissa : mantissa) << BigInt(Math.max(shift, 0)),
               1n << BigInt(Math.max(-shift, 0)), work);
}

function floorLogRatio(n, d) {
  let exponent = bitLength(n) - bitLength(d);
  if (exponent >= 0 ? n < (d << BigInt(exponent)) : (n << BigInt(-exponent)) < d) exponent--;
  return exponent;
}
function nearestEven(n, d) {
  const q = n / d, remainder = n % d, twice = 2n * remainder;
  return q + BigInt(twice > d || (twice === d && Boolean(q & 1n)));
}
function roundedNumber(value, work) {
  work.tick();
  if (value.n === 0n) return 0;
  const negative = value.n < 0n;
  const n = negative ? -value.n : value.n;
  let exponent = floorLogRatio(n, value.d);
  if (exponent > 1023) throw new Error('reach_destination_nonfinite_output');
  const shift = exponent < -1022 ? 1074 : 52 - exponent;
  const numerator = n << BigInt(Math.max(shift, 0));
  const denominator = value.d << BigInt(Math.max(-shift, 0));
  work.bits(numerator, denominator);
  let q = nearestEven(numerator, denominator), bits;
  if (exponent < -1022) bits = q;
  else {
    if (q === 1n << 53n) { q >>= 1n; exponent++; }
    if (exponent > 1023) throw new Error('reach_destination_nonfinite_output');
    bits = (BigInt(exponent + 1023) << 52n) | (q - (1n << 52n));
  }
  if (negative && bits) bits |= 1n << 63n;
  view.setBigUint64(0, bits, false);
  return view.getFloat64(0, false);
}

function isqrt(n, work) {
  work.tick(); work.bits(n);
  if (n < 0n) throw new Error('reach_destination_negative_radicand');
  if (n < 2n) return n;
  let x = 1n << BigInt(Math.ceil(bitLength(n) / 2));
  for (;;) {
    work.tick();
    const next = (x + n / x) >> 1n;
    if (next >= x) return x;
    x = next;
  }
}

function normalizedComponent(component, squareNorm, work) {
  work.tick();
  if (component.n === 0n) return 0;
  const square = div(mul(component, component, work), squareNorm, work);
  if (compare(square, ONE, work) > 0) throw new Error('reach_destination_invalid_norm');
  const exponent = Math.floor(floorLogRatio(square.n, square.d) / 2);
  const shift = exponent < -1022 ? 1074 : 52 - exponent;
  if (bitLength(square.n) + 2 * shift > MAX_BITS) throw new Error('reach_destination_operand_budget');
  const n = square.n << BigInt(2 * shift);
  let q = isqrt(n / square.d, work);
  const midpoint = 2n * q + 1n;
  const right = work.product(square.d, work.product(midpoint, midpoint));
  if (4n * n > right || (4n * n === right && Boolean(q & 1n))) q++;
  return roundedNumber(ratio(component.n < 0n ? -q : q, 1n << BigInt(shift), work), work);
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
  if (dot.n < 0n) last = last.map(negate);
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

export async function attachReachPlayback(gltf, { threeRevision, check = null } = {}) {
  if (String(threeRevision) !== THREE_REVISION) throw new Error('reach_destination_three_identity');
  const json = gltf.parser.json;
  if (json.extras?.ontokin?.target_contract !== 'ontokin.glb/0.6') throw new Error('reach_destination_contract');
  if (!identityTransform(gltf.scene)) throw new Error('reach_destination_scene_transform');
  if (json.animations?.length !== 1) throw new Error('reach_destination_clip_count');
  const work = new ArithmeticBudget(check), animation = json.animations[0], groups = new Map();
  let components = 0, poses = 0;
  // Count repeated channel references before asking GLTFLoader for arrays.
  for (const channel of animation.channels) {
    work.tick();
    const sampler = animation.samplers[channel.sampler];
    const input = json.accessors[sampler.input], output = json.accessors[sampler.output];
    const arity = channel.target.path === 'rotation' ? 4 : channel.target.path === 'translation' ? 3 : 0;
    if (!arity || sampler.interpolation !== 'LINEAR' || !Number.isInteger(input.count)
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
    if (association.nodes !== undefined) objects.set(association.nodes, object);
  }
  const tracks = [];
  for (const [index, group] of groups) {
    work.tick();
    const object = objects.get(index);
    if (!object || !group.translation || !group.rotation || group.translation.input !== group.rotation.input)
      throw new Error('reach_destination_missing_carrier');
    for (let parent = object.parent; parent; parent = parent.parent) {
      if (!identityTransform(parent)) throw new Error('reach_destination_nonidentity_parent');
    }
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
      for (const track of tracks) {
        sampling.tick();
        const { object, clock, position, rotation } = track;
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
