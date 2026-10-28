// Verification-only parsing and arithmetic. No production pose/writer imports.
import {createHash} from 'node:crypto';

export const LIMITS = Object.freeze({
  bytes: 64 * 1024 * 1024, sourceBytes: 2 * 1024 * 1024, cases: 256,
  nodes: 250000, keys: 10000, bakedPoses: 250000, vertices: 250000,
  components: 4760000, repeatedComponents: 16777216, samples: 100000,
  observations: 1000000, worldVertices: 16000000, rationalBits: 32768,
  jsonDepth: 128, jsonValues: 5000000,
});
export class NativeVerificationError extends Error {
  constructor(code, message, details = {}) {
    super(message); this.name = 'NativeVerificationError'; this.code = code; this.details = details;
  }
}
export function requireThat(condition, code, message, details) {
  if (!condition) throw new NativeVerificationError(code, message, details);
}
export const sha256 = bytes => 'sha256:' + createHash('sha256').update(bytes).digest('hex');
export function digest(value) {
  requireThat(typeof value === 'string' && /^(?:sha256:)?[0-9a-f]{64}$/.test(value),
    'identity', 'A lowercase SHA-256 identity is required.');
  return value.startsWith('sha256:') ? value : 'sha256:' + value;
}
export function finite(value, label) {
  requireThat(typeof value === 'number' && Number.isFinite(value), 'finite', label + ' must be finite.');
  return value;
}
export function integer(value, minimum, maximum, label) {
  requireThat(Number.isSafeInteger(value) && value >= minimum && value <= maximum,
    'resource', label + ' is outside its bounded integer range.', {value, minimum, maximum});
  return value;
}
export function vector(value, length, label) {
  requireThat(Array.isArray(value) && value.length === length, 'shape', label + ' has the wrong arity.');
  value.forEach(x => finite(x, label)); return value;
}
export function sameArray(a, b, label) {
  requireThat(Array.isArray(a) && Array.isArray(b) && a.length === b.length &&
    a.every((v, i) => v === b[i]), 'identity', label + ' differs.', {actual: a, expected: b});
}

// Scan before JSON.parse: duplicate keys, excessive depth, invalid UTF-8 and
// nonfinite numeric literals must not acquire a second meaning in another tool.
export function parseJson(bytes, label = 'JSON') {
  requireThat(bytes.byteLength <= LIMITS.bytes, 'resource', label + ' exceeds the byte limit.');
  let source;
  try { source = new TextDecoder('utf-8', {fatal: true}).decode(bytes); }
  catch { throw new NativeVerificationError('json', label + ' is not UTF-8.'); }
  let cursor = 0, count = 0;
  const whitespace = () => { while (/\s/.test(source[cursor] ?? '') && cursor < source.length) {
    requireThat(' \t\r\n'.includes(source[cursor]), 'json', 'Only JSON whitespace is accepted.'); cursor++;
  } };
  function string() {
    const start = cursor++;
    while (cursor < source.length) {
      const char = source[cursor++];
      if (char === '"') {
        let value;
        try { value = JSON.parse(source.slice(start, cursor)); }
        catch { throw new NativeVerificationError('json', label + ' has an invalid string.'); }
        for (const point of value) {
          const cp = point.codePointAt(0);
          requireThat(cp < 0xd800 || cp > 0xdfff, 'json', label + ' has an unpaired surrogate.');
        }
        return value;
      }
      if (char === '\\') cursor++;
    }
    throw new NativeVerificationError('json', label + ' has an unfinished string.');
  }
  function value(depth) {
    requireThat(depth <= LIMITS.jsonDepth && ++count <= LIMITS.jsonValues,
      'resource', label + ' exceeds JSON depth/value limits.');
    whitespace(); const char = source[cursor];
    if (char === '"') { string(); return; }
    if (char === '{') {
      cursor++; whitespace(); const keys = new Set();
      if (source[cursor] === '}') { cursor++; return; }
      while (true) {
        whitespace(); requireThat(source[cursor] === '"', 'json', label + ' has a nonstring object key.');
        const key = string();
        requireThat(!keys.has(key), 'json_duplicate_key', label + ' repeats an object key.', {key}); keys.add(key);
        whitespace(); requireThat(source[cursor++] === ':', 'json', label + ' has no key/value separator.');
        value(depth + 1); whitespace(); const separator = source[cursor++];
        if (separator === '}') return;
        requireThat(separator === ',', 'json', label + ' has an invalid object separator.');
      }
    }
    if (char === '[') {
      cursor++; whitespace(); if (source[cursor] === ']') { cursor++; return; }
      while (true) {
        value(depth + 1); whitespace(); const separator = source[cursor++];
        if (separator === ']') return;
        requireThat(separator === ',', 'json', label + ' has an invalid array separator.');
      }
    }
    const token = /^(?:true|false|null|-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?)/.exec(source.slice(cursor));
    requireThat(token, 'json', label + ' has an invalid value.'); cursor += token[0].length;
    if (!['true', 'false', 'null'].includes(token[0])) finite(Number(token[0]), label + ' number');
  }
  value(0); whitespace(); requireThat(cursor === source.length, 'json', label + ' has trailing content.');
  return JSON.parse(source);
}

export function canonical(value) {
  if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
  if (value && typeof value === 'object') return '{' + Object.keys(value)
    .sort((a, b) => Buffer.compare(Buffer.from(a), Buffer.from(b)))
    .map(key => JSON.stringify(key) + ':' + canonical(value[key])).join(',') + '}';
  return JSON.stringify(value);
}

const bits = x => (x < 0n ? -x : x).toString(2).length;
function gcd(a, b) { a = a < 0n ? -a : a; while (b) [a, b] = [b, a % b]; return a; }
function boundInteger(x) {
  requireThat(bits(x) <= LIMITS.rationalBits, 'rational_resource', 'An exact operand exceeds its bit limit.');
  return x;
}
export function rational(n, d = 1n) {
  boundInteger(n); boundInteger(d);
  requireThat(d !== 0n, 'rational', 'A rational denominator must be nonzero.');
  if (d < 0n) { n = -n; d = -d; }
  const common = gcd(n, d); return {n: n / common, d: d / common};
}
export const ZERO = rational(0n), ONE = rational(1n);
const buffer = new ArrayBuffer(8), view = new DataView(buffer);
export function fromNumber(value) {
  finite(value, 'Exact binary64 input'); if (value === 0) return ZERO;
  view.setFloat64(0, value, false); const raw = view.getBigUint64(0, false);
  const sign = raw >> 63n ? -1n : 1n, exponent = Number((raw >> 52n) & 2047n);
  const mantissa = (raw & ((1n << 52n) - 1n)) + (exponent ? 1n << 52n : 0n);
  const shift = (exponent || 1) - 1023 - 52;
  return shift >= 0 ? rational(sign * (mantissa << BigInt(shift))) : rational(sign * mantissa, 1n << BigInt(-shift));
}
export function parseRational(value) {
  if (typeof value === 'number') return fromNumber(value);
  requireThat(typeof value === 'string' && value.length <= 12000, 'rational', 'A bounded exact rational is required.');
  if (/^-?[0-9]+\/[0-9]+$/.test(value)) { const [n, d] = value.split('/'); return rational(BigInt(n), BigInt(d)); }
  const match = /^(-?)([0-9]+)(?:\.([0-9]+))?(?:[eE]([+-]?[0-9]+))?$/.exec(value);
  requireThat(match, 'rational', 'An exact decimal or n/d string is required.');
  const exponent = Number(match[4] ?? 0) - (match[3]?.length ?? 0);
  integer(exponent, -9000, 9000, 'Decimal exponent');
  const n = BigInt((match[1] || '') + match[2] + (match[3] ?? ''));
  return exponent >= 0 ? rational(n * 10n ** BigInt(exponent)) : rational(n, 10n ** BigInt(-exponent));
}
function product(a, b) {
  requireThat(bits(a) + bits(b) <= LIMITS.rationalBits, 'rational_resource', 'A prospective exact product exceeds its bit limit.');
  return a * b;
}
export const add = (a, b) => rational(boundInteger(product(a.n, b.d) + product(b.n, a.d)), product(a.d, b.d));
export const neg = a => ({n: -a.n, d: a.d});
export const subtract = (a, b) => add(a, neg(b));
export const multiply = (a, b) => rational(product(a.n, b.n), product(a.d, b.d));
export const divide = (a, b) => rational(product(a.n, b.d), product(a.d, b.n));
export const compare = (a, b) => { const d = product(a.n, b.d) - product(b.n, a.d); return d < 0n ? -1 : d > 0n ? 1 : 0; };
export const square = a => multiply(a, a);
export const exactText = a => a.n + '/' + a.d;
const maximum = (a, b) => compare(a, b) >= 0 ? a : b;
function roundedQuotient(n, d) {
  const q = n / d, r = n % d;
  return q + ((2n * r > d || (2n * r === d && (q & 1n))) ? 1n : 0n);
}
function nearestBinary(value, precision, maximumExponent, minimumNormal, minimumExponent) {
  if (value.n === 0n) return 0;
  const sign = value.n < 0n ? -1 : 1, n = value.n < 0n ? -value.n : value.n, d = value.d;
  let exponent = bits(n) - bits(d);
  if (exponent >= 0 ? n < (d << BigInt(exponent)) : (n << BigInt(-exponent)) < d) exponent--;
  requireThat(exponent <= maximumExponent, 'finite', 'An exact value is outside the finite binary format.');
  const shift = exponent < minimumNormal ? -minimumExponent : precision - exponent;
  const q = shift >= 0 ? roundedQuotient(n << BigInt(shift), d) : roundedQuotient(n, d << BigInt(-shift));
  const result = finite(sign * Number(q) * 2 ** (exponent < minimumNormal ? minimumExponent : exponent - precision), 'Rounded rational');
  requireThat(Math.abs(result) <= (2 - 2 ** -precision) * 2 ** maximumExponent,
    'finite', 'Rounding overflows the finite binary format.');
  return result;
}
export const nearestNumber = value => nearestBinary(value, 52, 1023, -1022, -1074);
export const nearestFloat32 = value => nearestBinary(value, 23, 127, -126, -149);
export function nextUp(value) {
  finite(value, 'Outward rounding input'); if (value === 0) return Number.MIN_VALUE;
  view.setFloat64(0, value, false); let raw = view.getBigUint64(0, false);
  raw += value > 0 ? 1n : -1n; view.setBigUint64(0, raw, false); return finite(view.getFloat64(0, false), 'Outward rounding output');
}
export const nextDown = value => -nextUp(-value);
export function numberInterval(value) {
  const result = nearestNumber(value), order = compare(fromNumber(result), value);
  return order === 0 ? [result, result] : order < 0 ? [result, nextUp(result)] : [nextDown(result), result];
}
function isqrt(n) {
  requireThat(n >= 0n, 'rational', 'Square root requires a nonnegative value.');
  if (n < 2n) return n;
  let x = 1n << BigInt(Math.ceil(bits(n) / 2));
  while (true) { const y = (x + n / x) / 2n; if (y >= x) return x; x = y; }
}
export function sqrtInterval(value) {
  requireThat(value.n >= 0n, 'rational', 'Square root requires a nonnegative value.');
  const scale = 1n << 128n, shifted = product(value.n, scale * scale);
  const root = isqrt(shifted / value.d), lo = rational(root, scale);
  return [lo, compare(square(lo), value) === 0 ? lo : rational(root + 1n, scale)];
}
export function enclosure(value, length, label) {
  requireThat(Array.isArray(value) && value.length === length, 'reference', label + ' enclosure has the wrong arity.');
  return value.map(pair => {
    requireThat(Array.isArray(pair) && pair.length === 2, 'reference', label + ' requires endpoint pairs.');
    const result = pair.map(parseRational);
    requireThat(compare(...result) <= 0, 'reference', label + ' enclosure endpoints are reversed.'); return result;
  });
}
export function intervalAdd(a, b) { return [add(a[0], b[0]), add(a[1], b[1])]; }
export function intervalNeg(a) { return [neg(a[1]), neg(a[0])]; }
export function intervalMultiply(a, b) {
  const values = a.flatMap(x => b.map(y => multiply(x, y)));
  return [values.reduce((x, y) => compare(x, y) < 0 ? x : y), values.reduce(maximum)];
}
function intervalSquare(a) {
  return [compare(a[0], ZERO) <= 0 && compare(a[1], ZERO) >= 0 ? ZERO :
    compare(square(a[0]), square(a[1])) < 0 ? square(a[0]) : square(a[1]), maximum(square(a[0]), square(a[1]))];
}
export function positionSquaredError(actual, expected) {
  vector(actual, expected.length, 'Observed position');
  return actual.reduce((total, value, index) => {
    const q = fromNumber(value), bounds = expected[index];
    return add(total, maximum(square(subtract(q, bounds[0])), square(subtract(q, bounds[1]))));
  }, ZERO);
}
export function quaternionAngleSquaredUpper(actualWxyz, expected) {
  vector(actualWxyz, 4, 'Observed quaternion');
  const actual = actualWxyz.map(fromNumber), normSquared = actual.map(square).reduce(add, ZERO);
  requireThat(compare(normSquared, rational(1n, 4n)) >= 0 && compare(normSquared, rational(4n)) <= 0,
    'rotation', 'Observed quaternion is outside the normalization domain.');
  const sourceNorm = expected.map(intervalSquare).reduce(intervalAdd, [ZERO, ZERO]);
  requireThat(compare(sourceNorm[0], ONE) <= 0 && compare(sourceNorm[1], ONE) >= 0,
    'reference', 'Source orientation enclosure does not contain a unit quaternion.');
  const norm = sqrtInterval(normSquared);
  const normalized = actual.map(q => {
    const a = divide(q, norm[0]), b = divide(q, norm[1]);
    return compare(a, b) <= 0 ? [a, b] : [b, a];
  });
  const chord = sign => normalized.reduce((total, q, index) => {
    const r = sign > 0 ? expected[index] : intervalNeg(expected[index]);
    return add(total, maximum(square(subtract(q[0], r[1])), square(subtract(q[1], r[0]))));
  }, ZERO);
  const a = chord(1), b = chord(-1), d2 = compare(a, b) <= 0 ? a : b;
  requireThat(compare(d2, rational(4n)) < 0, 'rotation', 'No finite local angular bound is established.');
  // theta = 4 asin(d/2) <= 2 d / sqrt(1-d^2/4). This is a
  // conservative physical-angle upper bound, with no host trig or epsilon.
  return divide(multiply(rational(4n), d2), subtract(ONE, divide(d2, rational(4n))));
}
export function errorUpperNumber(squared) { return numberInterval(sqrtInterval(squared)[1])[1]; }
export function rotationMatrixEnclosure(q) {
  const [w, x, y, z] = q, one = [ONE, ONE], two = [rational(2n), rational(2n)];
  const twice = x => intervalMultiply(two, x), plus = intervalAdd;
  const minus = (a, b) => plus(a, intervalNeg(b)), mul = intervalMultiply;
  return [minus(one, twice(plus(mul(y, y), mul(z, z)))), twice(minus(mul(x, y), mul(w, z))), twice(plus(mul(x, z), mul(w, y))),
    twice(plus(mul(x, y), mul(w, z))), minus(one, twice(plus(mul(x, x), mul(z, z)))), twice(minus(mul(y, z), mul(w, x))),
    twice(minus(mul(x, z), mul(w, y))), twice(plus(mul(y, z), mul(w, x))), minus(one, twice(plus(mul(x, x), mul(y, y))))];
}
export function floatTransformEnclosure(position, orientation) {
  const convert = interval => [numberInterval(interval[0])[0], numberInterval(interval[1])[1]];
  return {position: position.map(convert), rotation: rotationMatrixEnclosure(orientation).map(convert)};
}
function floatMultiply(a, b) {
  const values = a.flatMap(x => b.map(y => finite(x * y, 'Interval product')));
  return [nextDown(Math.min(...values)), nextUp(Math.max(...values))];
}
function floatAdd(a, b) { return [nextDown(a[0] + b[0]), nextUp(a[1] + b[1])]; }
export function transformedPointBounds(transform, point) {
  vector(point, 3, 'Source local point');
  return transform.position.map((p, row) => point.reduce((sum, value, column) =>
    floatAdd(sum, floatMultiply(transform.rotation[row * 3 + column], [value, value])), p));
}
export function floatPositionSquaredUpper(actual, expected) {
  vector(actual, 3, 'Native world point');
  let sum = 0;
  for (let i = 0; i < 3; i++) {
    const error = Math.max(Math.abs(nextDown(actual[i] - expected[i][1])), Math.abs(nextUp(actual[i] - expected[i][0])));
    sum = nextUp(sum + nextUp(error * error));
  }
  return sum;
}

const dimensions = {SCALAR: 1, VEC2: 2, VEC3: 3, VEC4: 4};
const widths = {5123: 2, 5125: 4, 5126: 4};
export function parseGlb(bytes) {
  requireThat(Buffer.isBuffer(bytes) && bytes.length >= 28 && bytes.length <= LIMITS.bytes,
    'glb', 'GLB byte length is outside the bounded format.');
  requireThat(bytes.readUInt32LE(0) === 0x46546c67 && bytes.readUInt32LE(4) === 2 && bytes.readUInt32LE(8) === bytes.length,
    'glb', 'GLB header or declared byte length differs.');
  const jsonLength = bytes.readUInt32LE(12), binaryHeader = 20 + jsonLength;
  requireThat(jsonLength % 4 === 0 && binaryHeader + 8 <= bytes.length && bytes.readUInt32LE(16) === 0x4e4f534a,
    'glb', 'GLB must start with one aligned JSON chunk.');
  requireThat(bytes.readUInt32LE(binaryHeader + 4) === 0x004e4942 &&
    binaryHeader + 8 + bytes.readUInt32LE(binaryHeader) === bytes.length,
    'glb', 'GLB must contain exactly one final BIN chunk.');
  const document = parseJson(bytes.subarray(20, binaryHeader), 'GLB JSON'), binary = bytes.subarray(binaryHeader + 8);
  requireThat(document && document.asset?.version === '2.0' && document.buffers?.length === 1 &&
    !Object.hasOwn(document.buffers[0], 'uri'), 'glb', 'Only one embedded glTF 2.0 buffer is accepted.');
  const bufferLength = integer(document.buffers[0].byteLength, 0, binary.length, 'Embedded buffer length');
  requireThat(binary.length - bufferLength <= 3 && binary.subarray(bufferLength).every(x => x === 0),
    'glb', 'The BIN chunk has invalid padding.');
  for (const key of ['skins', 'images', 'textures', 'cameras', 'extensionsUsed', 'extensionsRequired'])
    requireThat(!document[key]?.length, 'glb_subset', 'The native reach checker does not accept ' + key + '.');
  requireThat(Array.isArray(document.bufferViews) && Array.isArray(document.accessors), 'glb', 'Accessor arrays are required.');
  for (const b of document.bufferViews) {
    requireThat(b.buffer === 0 && !b.extensions, 'glb_subset', 'A bufferView must use the embedded buffer.');
    integer(b.byteOffset ?? 0, 0, bufferLength, 'bufferView offset');
    integer(b.byteLength, 1, bufferLength, 'bufferView length');
    requireThat((b.byteOffset ?? 0) + b.byteLength <= bufferLength, 'accessor_span', 'A bufferView escapes the embedded buffer.');
    if (b.byteStride !== undefined) {
      integer(b.byteStride, 4, 252, 'bufferView stride');
      requireThat(b.byteStride % 4 === 0, 'accessor_span', 'An interleaved stride must be four-byte aligned.');
    }
  }
  let components = 0;
  const layouts = document.accessors.map(a => {
    requireThat(!a.sparse && !a.normalized && !a.extensions && dimensions[a.type] && widths[a.componentType],
      'glb_subset', 'An accessor uses an unsupported representation.');
    const b = document.bufferViews[integer(a.bufferView, 0, document.bufferViews.length - 1, 'Accessor bufferView')];
    const count = integer(a.count, 1, LIMITS.components, 'Accessor count'), size = dimensions[a.type], width = widths[a.componentType];
    components += count * size;
    requireThat(components <= LIMITS.components, 'accessor_budget', 'Declared decoded components exceed the budget.');
    const offset = integer(a.byteOffset ?? 0, 0, b.byteLength, 'Accessor offset'), stride = b.byteStride ?? size * width;
    const start = (b.byteOffset ?? 0) + offset, span = (count - 1) * stride + size * width;
    requireThat(start % width === 0 && stride >= size * width && offset + span <= b.byteLength,
      'accessor_span', 'An accessor is misaligned or escapes its own bufferView.');
    return {count, size, width, start, stride, componentType: a.componentType};
  });
  const cache = new Map();
  function accessor(index, type, componentType) {
    integer(index, 0, layouts.length - 1, 'Accessor index');
    const descriptor = document.accessors[index], layout = layouts[index];
    requireThat((type === undefined || descriptor.type === type) && (componentType === undefined || descriptor.componentType === componentType),
      'accessor_type', 'An accessor does not have the required native type.');
    if (!cache.has(index)) {
      const values = new Float64Array(layout.count * layout.size), method = {5123: 'readUInt16LE', 5125: 'readUInt32LE', 5126: 'readFloatLE'}[layout.componentType];
      for (let i = 0; i < layout.count; i++) for (let j = 0; j < layout.size; j++)
        values[i * layout.size + j] = finite(binary[method](layout.start + i * layout.stride + j * layout.width), 'Decoded accessor');
      cache.set(index, values);
    }
    return {values: cache.get(index), ...layout};
  }
  return {document, binary, accessor, components};
}

export const INTERIOR_FRACTIONS = Object.freeze([[1, 16], [1, 8], [1, 4], [3, 8], [1, 2], [5, 8], [3, 4], [7, 8]]);
export function requiredPlan(parsed) {
  const {document, accessor} = parsed, nodes = document.nodes;
  requireThat(document.extras?.ontokin?.target_contract === 'ontokin.glb/0.6' &&
    document.extras.ontokin.profile === 'planar-reach-0.1', 'contract', 'The artifact is not recorded reach GLB/0.6.');
  requireThat(Array.isArray(nodes) && nodes.length > 0 && nodes.length <= LIMITS.nodes && document.scene === 0 &&
    document.scenes?.length === 1, 'carrier_inventory', 'One nonempty flat scene is required.');
  sameArray(document.scenes[0].nodes, nodes.map((_, index) => index), 'Complete root carrier inventory');
  for (const node of nodes) {
    requireThat(!node.children?.length && node.matrix === undefined && node.skin === undefined && node.camera === undefined &&
      node.weights === undefined && !node.extensions && node.extras?.ontokin?.kind === 'object',
      'carrier_inventory', 'Only flat source object carriers are supported; visual helpers are outside this checker.');
    vector(node.translation, 3, 'Initial carrier translation'); vector(node.rotation, 4, 'Initial carrier rotation');
    if (node.scale !== undefined) sameArray(node.scale, [1, 1, 1], 'Carrier scale');
  }
  requireThat(document.animations?.length === 1, 'animation', 'Exactly one recorded clip is required.');
  const animation = document.animations[0], metadata = animation.extras?.ontokin;
  requireThat(Array.isArray(animation.channels) && Array.isArray(animation.samplers) &&
    animation.channels.length === nodes.length * 2 && animation.samplers.length === nodes.length * 2,
    'animation', 'Each carrier requires exactly one translation and one rotation channel.');
  const groups = new Map(), samplers = new Set(); let clockIndex, repeatedComponents = 0;
  for (const channel of animation.channels) {
    const nodeIndex = integer(channel.target?.node, 0, nodes.length - 1, 'Animation target'), target = channel.target.path;
    requireThat(['translation', 'rotation'].includes(target), 'animation', 'Only translation and rotation are accepted.');
    const samplerIndex = integer(channel.sampler, 0, animation.samplers.length - 1, 'Animation sampler');
    requireThat(!samplers.has(samplerIndex), 'animation', 'Every recorded channel must identify its own sampler.'); samplers.add(samplerIndex);
    const sampler = animation.samplers[samplerIndex];
    requireThat(sampler.interpolation === 'LINEAR', 'animation', 'Recorded carriers require LINEAR tracks.');
    clockIndex ??= sampler.input;
    requireThat(sampler.input === clockIndex, 'animation', 'All carriers must share the exact stored clock accessor.');
    const clock = accessor(sampler.input, 'SCALAR', 5126), output = accessor(sampler.output, target === 'rotation' ? 'VEC4' : 'VEC3', 5126);
    integer(clock.count, 1, LIMITS.keys, 'Stored key count');
    requireThat(clock.count === output.count, 'animation', 'Clock and pose key counts differ.');
    repeatedComponents += clock.count + output.count * output.size;
    requireThat(repeatedComponents <= LIMITS.repeatedComponents && clock.count * nodes.length <= LIMITS.bakedPoses,
      'animation_budget', 'Repeated channel decoding or baked poses exceed the budget.');
    const group = groups.get(nodeIndex) ?? {};
    requireThat(!group[target], 'animation', 'A carrier has duplicate pose authority.'); group[target] = sampler; groups.set(nodeIndex, group);
    sameArray(nodes[nodeIndex][target], Array.from(output.values.subarray(0, output.size)), 'Initial carrier and first stored key');
  }
  requireThat(groups.size === nodes.length && [...groups.values()].every(x => x.translation && x.rotation),
    'animation', 'A carrier is missing a complete pose track.');
  const times = Array.from(accessor(clockIndex).values);
  requireThat(times[0] === 0 && times.every((t, index) => index === 0 || t > times[index - 1]), 'clock', 'Stored clocks must start at zero and strictly increase.');
  requireThat(metadata?.target_contract === 'ontokin.glb/0.6' && metadata.exact_times_seconds?.length === times.length &&
    Array.isArray(metadata.boundary_times_seconds) && metadata.boundary_times_seconds.length > 0 && metadata.boundary_times_seconds.length <= LIMITS.keys,
    'clock', 'Exact source clocks and source boundaries are required.');
  const exactTimes = metadata.exact_times_seconds.map((v, index) => {
    requireThat(v && typeof v.numerator === 'string' && typeof v.denominator === 'string', 'clock', 'Exact clocks require rational records.');
    const q = parseRational(v.numerator + '/' + v.denominator);
    requireThat(nearestFloat32(q) === times[index], 'clock', 'A stored key is not the identified binary32 clock.'); return q;
  });
  const boundaries = metadata.boundary_times_seconds.map(v => {
    requireThat(typeof v === 'string' && /^-?[0-9]+(?:\.[0-9]+)?$/.test(v), 'clock', 'Source boundaries require decimal strings.');
    return parseRational(v);
  });
  const retainedTimes = new Set(exactTimes.map(exactText));
  requireThat(boundaries.every((q, index) => compare(q, ZERO) >= 0 && (!index || compare(q, boundaries[index - 1]) > 0)) &&
    boundaries.every(q => retainedTimes.has(exactText(q))), 'clock', 'Every ordered source boundary must have an exact retained key.');
  const required_samples = times.map((t, index) => ({sample_id: 'key:' + index, kind: 'recorded_key', time_seconds: t, side: 'after'}));
  for (let index = 0; index + 1 < times.length; index++) {
    const seen = new Set();
    for (const [n, d] of INTERIOR_FRACTIONS) {
      const time = times[index] + (times[index + 1] - times[index]) * n / d;
      requireThat(time > times[index] && time < times[index + 1] && !seen.has(time), 'clock', 'An interior sample is not distinct.'); seen.add(time);
      required_samples.push({sample_id: `interval:${index}:fraction:${n}-${d}`, kind: 'interval_interior', time_seconds: time, side: 'after'});
    }
  }
  metadata.boundary_times_seconds.forEach((value, index) => {
    for (const side of ['before', 'after']) required_samples.push({sample_id: `boundary:${index}:${side}`, kind: 'source_boundary',
      time_seconds: nearestNumber(boundaries[index]), side, source_time_seconds: value});
  });
  requireThat(required_samples.length <= LIMITS.samples, 'sample_budget', 'The required schedule exceeds its sample budget.');
  return {schema_version: 'ontokin.reach-native-plan/0.1', program_revision: document.extras.ontokin.program?.revision,
    stored_key_count: times.length, interval_count: Math.max(0, times.length - 1), source_boundary_count: boundaries.length,
    required_samples, exactTimes, times, groups, boundaries, repeatedComponents};
}

export function checkSampleCoverage(samples, plan, sourceBoundaries) {
  requireThat(Array.isArray(samples) && samples.length <= LIMITS.samples, 'sample_coverage', 'Reference samples must be a bounded array.');
  requireThat(Array.isArray(sourceBoundaries) && sourceBoundaries.length === plan.boundaries.length &&
    sourceBoundaries.every((v, i) => compare(parseRational(v), plan.boundaries[i]) === 0),
    'source_boundaries', 'Independent source boundaries differ from the recorded boundary inventory.');
  const byId = new Map();
  for (const sample of samples) {
    requireThat(typeof sample.sample_id === 'string' && !byId.has(sample.sample_id), 'sample_coverage', 'Sample IDs must be unique.');
    finite(sample.time_seconds, 'Sample clock');
    requireThat(['before', 'after'].includes(sample.side), 'sample_coverage', 'Each observation requires its source side.'); byId.set(sample.sample_id, sample);
  }
  const required = new Set();
  for (const expected of plan.required_samples) {
    required.add(expected.sample_id); const actual = byId.get(expected.sample_id);
    requireThat(actual && Object.keys(expected).every(key => actual[key] === expected[key]),
      'sample_coverage', 'A mandatory key, interior, or source boundary observation is missing or changed.', {expected});
  }
  for (const sample of samples) if (!required.has(sample.sample_id))
    requireThat(sample.sample_id.startsWith('fixture:') && sample.kind === 'fixture', 'sample_coverage', 'Extra observations require a fixture: identity.');
  return byId;
}
