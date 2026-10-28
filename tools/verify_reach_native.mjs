#!/usr/bin/env node
// Actual-byte native reach checks. This tool never creates source expectations.
import {open, realpath, stat, writeFile} from 'node:fs/promises';
import {constants} from 'node:fs';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {
  LIMITS, NativeVerificationError, requireThat, sha256, digest, finite, integer, vector, sameArray,
  parseJson, canonical, parseGlb, requiredPlan, checkSampleCoverage, parseRational, fromNumber,
  compare, square, subtract, exactText, enclosure, positionSquaredError, quaternionAngleSquaredUpper,
  errorUpperNumber, floatTransformEnclosure, transformedPointBounds, floatPositionSquaredUpper,
  numberInterval, ZERO,
} from './reach_native_support.mjs';

export const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const SCHEMA = 'ontokin.reach-native-validation/0.1';
const SOURCE_IMPLEMENTATION = ['ontokin/reach_numeric.py', 'ontokin/reach_kinematics.py',
  'ontokin/reach_pose.py', 'ontokin/reach_phase.py', 'ontokin/reach_runtime.py', 'ontokin/reach_export.py'];
const SOURCE_DERIVATION = ['docs/engineering/reach-numeric-kernel.md', 'docs/engineering/reach-source-kernel.md'];
const DESTINATION_IMPLEMENTATION = 'tools/reach_destination.mjs';
const DESTINATION_DERIVATION = 'docs/engineering/reach-destination-numerics.md';
const SELF_INPUTS = ['tools/verify_reach_native.mjs', 'tools/reach_native_support.mjs',
  'tools/package.json', 'tools/package-lock.json', DESTINATION_IMPLEMENTATION, DESTINATION_DERIVATION];
const OMITTED_SCOPES = [
  'Independent source lifecycle, histories, continuous interval certificates and the complete source conformance gate.',
  'Agent protocol execution, transport provenance and release corpus or R/Q mapping completeness.',
  'Browser rendering, screenshot review, lighting and GPU arithmetic.',
  'Compatibility, inherited gates, resulting-main checks and complete reach or full-product release acceptance.',
];
function equal(a, b, label) {
  requireThat(canonical(a) === canonical(b), 'identity', label + ' differs.', {actual: a, expected: b});
}
function object(value, label) {
  requireThat(value && typeof value === 'object' && !Array.isArray(value), 'shape', label + ' must be an object.'); return value;
}
function identityString(value, label) {
  requireThat(typeof value === 'string' && value.length > 0 && value.length <= 4096, 'identity', label + ' must be a bounded nonempty string.');
  return value;
}

export async function containedPath(directory, relative) {
  identityString(relative, 'Input path');
  requireThat(!relative.includes('\\') && !relative.includes('\0') && !path.posix.isAbsolute(relative) &&
    path.posix.normalize(relative) === relative && relative !== '.' &&
    relative.split('/').every(part => part !== '..' && part !== '.' && part !== ''),
    'input_path', 'Input paths must be normalized relative paths without traversal.', {path: relative});
  const base = await realpath(directory), resolved = await realpath(path.join(base, relative));
  const remainder = path.relative(base, resolved);
  requireThat(remainder && remainder !== '..' && !remainder.startsWith('..' + path.sep) && !path.isAbsolute(remainder),
    'input_path', 'An input symlink escapes its declared directory.', {path: relative});
  return resolved;
}

// A bounded read does not allocate from a claimed accessor count or an
// unverified size descriptor, and a growing file cannot grow the allocation.
export async function boundedRead(filename, maximum = LIMITS.bytes) {
  const handle = await open(filename, constants.O_RDONLY | (constants.O_NOFOLLOW ?? 0));
  try {
    const before = await handle.stat();
    requireThat(before.isFile(), 'input_file', 'An input must be a regular file.');
    integer(before.size, 0, maximum, 'Input byte length');
    const bytes = Buffer.alloc(before.size); let offset = 0;
    while (offset < bytes.length) {
      const read = await handle.read(bytes, offset, Math.min(1048576, bytes.length - offset), offset);
      requireThat(read.bytesRead > 0, 'input_changed', 'An input was truncated while reading.'); offset += read.bytesRead;
    }
    const extra = await handle.read(Buffer.alloc(1), 0, 1, bytes.length), after = await handle.stat();
    requireThat(extra.bytesRead === 0 && before.size === after.size && before.mtimeMs === after.mtimeMs,
      'input_changed', 'An input changed while reading.'); return bytes;
  } finally { await handle.close(); }
}

async function readDescriptor(directory, descriptor, observed, maximum = LIMITS.bytes) {
  object(descriptor, 'File descriptor'); const filename = await containedPath(directory, descriptor.path);
  integer(descriptor.bytes, 0, maximum, 'Declared input size');
  const expectedHash = digest(descriptor.sha256), bytes = await boundedRead(filename, maximum);
  requireThat(bytes.length === descriptor.bytes && sha256(bytes) === expectedHash,
    'input_identity', 'Input bytes do not match their descriptor.', {path: descriptor.path});
  const previous = observed.get(filename);
  requireThat(!previous || (previous.sha256 === expectedHash && previous.bytes === bytes.length),
    'input_identity', 'A shared input has conflicting identities.');
  observed.set(filename, {path: descriptor.path, sha256: expectedHash, bytes: bytes.length, maximum});
  return bytes;
}
async function implementationInput(relative, observed) {
  const filename = await containedPath(root, relative), bytes = await boundedRead(filename);
  const descriptor = {path: relative, sha256: sha256(bytes), bytes: bytes.length, maximum: LIMITS.bytes};
  observed.set(filename, descriptor); return descriptor;
}
async function assertStable(observed) {
  for (const [filename, expected] of observed) {
    const actual = await boundedRead(filename, expected.maximum);
    requireThat(actual.length === expected.bytes && sha256(actual) === expected.sha256,
      'input_changed', 'An identified input changed during native verification.', {path: expected.path});
  }
}
async function checkBasis(metadata, observed) {
  async function aggregate(names) {
    let text = '';
    for (const name of names) {
      const value = await implementationInput(name, observed); text += name + '\0' + value.sha256.slice(7) + '\n';
    }
    return sha256(Buffer.from(text, 'ascii'));
  }
  const quantization = object(metadata.reach_quantization, 'Reach numerical basis');
  const source = object(quantization.source_numeric_bound_basis, 'Source numerical basis');
  requireThat(source.name === 'OntoKin controlled source poses' && source.version === '0.2' &&
    source.method === 'ontokin.source-pose-projective-dyadic/0.2' &&
    digest(source.implementation_sha256) === await aggregate(SOURCE_IMPLEMENTATION) &&
    digest(source.derivation_sha256) === await aggregate(SOURCE_DERIVATION),
    'source_basis', 'The artifact numerical basis does not identify the current source implementation and derivation.');
  const destination = object(quantization.destination_numeric_bound_basis, 'Destination numerical basis');
  requireThat(destination.name === 'ontokin-controlled-three-recording' && destination.version === '0.1.0' &&
    digest(destination.implementation_sha256) === (await implementationInput(DESTINATION_IMPLEMENTATION, observed)).sha256 &&
    digest(destination.derivation_sha256) === (await implementationInput(DESTINATION_DERIVATION, observed)).sha256,
    'destination_basis', 'The artifact does not identify the actual controlled player and its derivation.');
  return {source, destination};
}

function checkedTolerances(reference, metadata, plan) {
  const tolerances = object(reference.tolerances, 'Reference tolerances'), limits = {
    position_m: .001, rotation_rad: .001, time_s: .000001, local_vertex_m: .00001,
  }, result = {};
  for (const [key, limit] of Object.entries(limits)) {
    const value = parseRational(tolerances[key]);
    requireThat(compare(value, ZERO) > 0 && compare(value, fromNumber(limit)) <= 0,
      'tolerance', 'An acceptance tolerance is missing or weakened.', {key, maximum: limit}); result[key] = value;
  }
  requireThat(compare(result.local_vertex_m, result.position_m) <= 0, 'tolerance', 'Local vertex tolerance exceeds the position tolerance.');
  const recorded = metadata.reach_quantization;
  for (const [key, recordedKey] of [['position_m', 'position_tolerance_m'], ['rotation_rad', 'rotation_tolerance_rad'], ['time_s', 'time_tolerance_s']])
    requireThat(compare(result[key], parseRational(recorded[recordedKey])) <= 0,
      'tolerance', 'Reference tolerance exceeds the artifact requested tolerance.', {key});
  let timeSquared = ZERO;
  plan.times.forEach((time, index) => {
    const error = square(subtract(fromNumber(time), plan.exactTimes[index]));
    requireThat(compare(error, square(result.time_s)) <= 0, 'clock_tolerance', 'A stored key exceeds the allowed exact source-clock error.');
    if (compare(error, timeSquared) > 0) timeSquared = error;
  });
  return {...result, max_time_error_squared: timeSquared};
}

async function checkSourceIdentity(item, reference, metadata, directory, observed) {
  const manifest = object(metadata.program?.manifest, 'Source bundle manifest');
  requireThat(manifest.schema_version === 'ontokin.bundle/0.1' && manifest.entry_source_id === 'entry' &&
    Array.isArray(manifest.units) && manifest.units.length > 0 && manifest.units.length <= 256,
    'source_identity', 'A complete bounded source bundle manifest is required.');
  const revision = sha256(Buffer.from('ontokin.bundle/0.1\0' + canonical(manifest), 'utf8'));
  requireThat(digest(item.program_revision) === revision && digest(reference.program_revision) === revision &&
    digest(metadata.program.revision) === revision, 'source_identity', 'Program identities do not match the exact source bundle manifest.');
  requireThat(Array.isArray(item.sources) && item.sources.length === manifest.units.length, 'source_identity', 'All source units must be supplied.');
  const units = new Map(), sourcePaths = new Set([item.artifact.path, item.reference.path]);
  requireThat(sourcePaths.size === 2, 'input_path', 'Artifact and reference files must be distinct.');
  for (const unit of manifest.units) {
    identityString(unit.source_id, 'Source ID');
    requireThat(!units.has(unit.source_id), 'source_identity', 'Source unit identities must be unique.');
    units.set(unit.source_id, unit);
  }
  const supplied = new Map();
  for (const descriptor of item.sources) {
    const unit = units.get(descriptor.source_id);
    requireThat(unit && !supplied.has(descriptor.source_id) && !sourcePaths.has(descriptor.path),
      'source_identity', 'Source files require unique complete source IDs and paths.'); sourcePaths.add(descriptor.path);
    const bytes = await readDescriptor(directory, descriptor, observed, LIMITS.sourceBytes);
    requireThat(digest(unit.source_revision) === sha256(bytes), 'source_identity', 'Source bytes differ from the pinned source revision.');
    try { new TextDecoder('utf-8', {fatal: true}).decode(bytes); }
    catch { throw new NativeVerificationError('source_identity', 'Source bytes must be valid UTF-8.'); }
    supplied.set(descriptor.source_id, {...unit, bytes: bytes.length});
  }
  const oracle = object(reference.oracle, 'Reference oracle provenance');
  requireThat(oracle.method === 'independent_reach_reference', 'reference', 'Expectations must identify the independent ReachReference path.');
  const inputs = object(oracle.inputs, 'Reference oracle implementation inputs');
  requireThat(Object.hasOwn(inputs, 'ontokin/reach_reference.py') && Object.keys(inputs).length <= 256,
    'reference', 'The independent reference implementation must be identified.');
  const oracleInputs = {};
  for (const [name, expectedHash] of Object.entries(inputs)) {
    const actual = await implementationInput(name, observed);
    requireThat(actual.sha256 === digest(expectedHash), 'reference_identity', 'Reference implementation input differs from the identified file.', {path: name});
    oracleInputs[name] = actual.sha256;
  }
  return {revision, units: supplied, oracleInputs};
}

function checkOccurrence(node, expected, identity) {
  const metadata = node.extras.ontokin;
  requireThat(metadata.path === expected.path && digest(metadata.program_revision) === identity.revision,
    'carrier_identity', 'Native carrier source identity differs.');
  equal(metadata.element_id, expected.element_id, 'Carrier element identity');
  const mapping = object(metadata.source_mapping, 'Carrier source mapping');
  equal(mapping.element_id, expected.element_id, 'Carrier source mapping element identity');
  for (const kind of ['definition', 'declaration']) {
    const span = object(mapping[kind], 'Source ' + kind + ' mapping'), unit = identity.units.get(span.source_id);
    requireThat(unit && digest(span.source_revision) === digest(unit.source_revision) && span.filename === unit.filename,
      'carrier_identity', 'Carrier source span does not identify a pinned source unit.');
    integer(span.start_byte, 0, unit.bytes, 'Source span start'); integer(span.end_byte, span.start_byte, unit.bytes, 'Source span end');
  }
}

function materialExpectation(actual, expected, primitive, carrier, revision) {
  object(expected, 'Source material'); vector(expected.base_color, 4, 'Source base color');
  [...expected.base_color, expected.metallic, expected.roughness].forEach(value =>
    requireThat(Number.isFinite(value) && value >= 0 && value <= 1, 'reference', 'Material factors must lie in [0,1].'));
  requireThat(actual && !actual.extensions && !actual.normalTexture && !actual.occlusionTexture &&
    !actual.emissiveTexture && !actual.emissiveFactor && !actual.doubleSided && !actual.alphaCutoff,
    'material_subset', 'Unexpected native material behavior is not covered by the source oracle.');
  const pbr = object(actual.pbrMetallicRoughness, 'Native PBR factors');
  requireThat(!pbr.baseColorTexture && !pbr.metallicRoughnessTexture, 'material_subset', 'Textures are not part of this reach native adapter.');
  sameArray(pbr.baseColorFactor, expected.base_color, 'Native linear RGBA');
  requireThat(pbr.metallicFactor === expected.metallic && pbr.roughnessFactor === expected.roughness,
    'material', 'Native metallic or roughness factor differs from source.');
  requireThat((actual.alphaMode ?? 'OPAQUE') === (expected.base_color[3] < 1 ? 'BLEND' : 'OPAQUE'),
    'material', 'Native alpha mode differs from source opacity.');
  const region = expected.region_key;
  requireThat(region === null || typeof region === 'string', 'reference', 'Source material region must be a string or null.');
  if (region === null) requireThat(primitive.extras?.ontokin?.region_key === undefined &&
    actual.extras?.ontokin?.source_region_key === undefined, 'material', 'An unregional source material gained a region identity.');
  else {
    const metadata = object(actual.extras?.ontokin, 'Native region identity');
    requireThat(primitive.extras?.ontokin?.region_key === region && metadata.source_region_key === region &&
      metadata.occurrence_path === carrier.path && digest(metadata.program_revision) === revision,
      'material', 'Native region ownership differs from source.');
    equal(metadata.element_id, carrier.element_id, 'Region carrier identity');
  }
}

function prepareGeometry(parsed, reference, identity, tolerances) {
  const {document, accessor} = parsed;
  requireThat(Array.isArray(reference.expected_nodes) && reference.expected_nodes.length === document.nodes.length,
    'carrier_inventory', 'Reference must include every actual source object carrier.');
  const expected = new Map(), sites = new Map(), records = [], usedMeshes = new Set(), usedMaterials = new Set();
  let vertexCount = 0, repeatedComponents = 0, triangleCount = 0, primitiveCount = 0, maxLocalError = ZERO;
  for (const node of reference.expected_nodes) {
    identityString(node.path, 'Source object path');
    requireThat(!expected.has(node.path), 'carrier_inventory', 'Source object paths must be unique.'); expected.set(node.path, node);
    requireThat(Array.isArray(node.sites), 'reference', 'Every source carrier requires its complete site array.');
    for (const site of node.sites) {
      identityString(site.path, 'Source site path'); vector(site.position_m, 3, 'Source carrier-local site');
      requireThat(!sites.has(site.path), 'site_inventory', 'Source site paths must be unique.'); sites.set(site.path, {carrier: node.path, ...site});
    }
  }
  const seen = new Set();
  for (let nodeIndex = 0; nodeIndex < document.nodes.length; nodeIndex++) {
    const native = document.nodes[nodeIndex], source = expected.get(native.extras.ontokin.path);
    requireThat(source && !seen.has(source.path), 'carrier_inventory', 'Actual carrier inventory differs from the independent source.'); seen.add(source.path);
    checkOccurrence(native, source, identity);
    const record = {nodeIndex, source, primitives: []}; records.push(record);
    if (source.geometry === null) {
      requireThat(native.mesh === undefined, 'geometry', 'An empty source carrier acquired native geometry.'); continue;
    }
    const geometry = object(source.geometry, 'Source geometry');
    requireThat(Array.isArray(geometry.positions) && geometry.positions.length > 0 &&
      Array.isArray(geometry.normals) && geometry.normals.length === geometry.positions.length &&
      Array.isArray(geometry.primitives) && geometry.primitives.length > 0,
      'reference', 'Source geometry requires positions, normals, and indexed material primitives.');
    vertexCount += geometry.positions.length;
    requireThat(vertexCount <= LIMITS.vertices, 'geometry_budget', 'Aggregate occurrence vertices exceed the inherited bound.');
    const meshIndex = integer(native.mesh, 0, (document.meshes?.length ?? 0) - 1, 'Native mesh index'); usedMeshes.add(meshIndex);
    const mesh = document.meshes[meshIndex];
    requireThat(!mesh.weights && !mesh.extensions && mesh.primitives?.length === geometry.primitives.length,
      'geometry', 'Native primitive inventory differs from source.');
    const regionMaterials = new Set();
    for (let primitiveIndex = 0; primitiveIndex < geometry.primitives.length; primitiveIndex++) {
      const primitive = mesh.primitives[primitiveIndex], target = geometry.primitives[primitiveIndex];
      requireThat((primitive.mode ?? 4) === 4 && !primitive.targets && !primitive.extensions,
        'geometry', 'Only native indexed rigid triangles are supported.');
      sameArray(Object.keys(primitive.attributes ?? {}).sort(), ['NORMAL', 'POSITION'], 'Native geometry attributes');
      const positions = accessor(primitive.attributes.POSITION, 'VEC3', 5126), normals = accessor(primitive.attributes.NORMAL, 'VEC3', 5126);
      const indices = accessor(primitive.indices, 'SCALAR');
      requireThat([5123, 5125].includes(indices.componentType) && positions.count === geometry.positions.length &&
        normals.count === positions.count && Array.isArray(target.indices) && indices.count === target.indices.length && indices.count % 3 === 0,
        'geometry', 'Native vertex, normal, or triangle inventory differs.');
      repeatedComponents += positions.values.length + normals.values.length + indices.values.length;
      requireThat(repeatedComponents <= LIMITS.repeatedComponents, 'geometry_budget', 'Repeated native primitive components exceed the verifier bound.');
      for (let i = 0; i < positions.count; i++) {
        const point = vector(geometry.positions[i], 3, 'Source local vertex'), normal = vector(geometry.normals[i], 3, 'Source local normal');
        const observed = [];
        for (let axis = 0; axis < 3; axis++) {
          const vertex = positions.values[i * 3 + axis]; observed.push(vertex);
          requireThat(vertex === Math.fround(point[axis]) && normals.values[i * 3 + axis] === Math.fround(normal[axis]),
            'geometry', 'Native vertex or normal bytes differ from source binary32 encoding.', {path: source.path, vertex: i, axis});
        }
        const error = positionSquaredError(observed, point.map(value => [fromNumber(value), fromNumber(value)]));
        requireThat(compare(error, square(tolerances.local_vertex_m)) <= 0, 'local_vertex_tolerance', 'Local source/native vertex error exceeds tolerance.');
        if (compare(error, maxLocalError) > 0) maxLocalError = error;
      }
      for (let i = 0; i < indices.count; i++) {
        integer(target.indices[i], 0, positions.count - 1, 'Source triangle index');
        requireThat(indices.values[i] === target.indices[i], 'geometry', 'Native triangle order, winding, or region membership differs.');
      }
      const materialIndex = integer(primitive.material, 0, (document.materials?.length ?? 0) - 1, 'Native material index'); usedMaterials.add(materialIndex);
      materialExpectation(document.materials[materialIndex], target.material, primitive, source, identity.revision);
      if (target.material.region_key !== null) {
        requireThat(!regionMaterials.has(materialIndex), 'material', 'Distinct source regions must retain distinct native materials.'); regionMaterials.add(materialIndex);
      }
      triangleCount += indices.count / 3; primitiveCount++;
      record.primitives.push({primitiveIndex, materialIndex, positions, normals, indices, source: target});
    }
  }
  requireThat(usedMeshes.size === (document.meshes?.length ?? 0) && usedMaterials.size === (document.materials?.length ?? 0),
    'geometry_inventory', 'Unreferenced extra meshes or materials are not source geometry.');
  return {records, sites, vertexCount, primitiveCount, triangleCount, maxLocalError, repeatedComponents};
}

function checkNativeAttribute(attribute, decoded, label) {
  requireThat(attribute && attribute.count === decoded.count && attribute.itemSize === decoded.size,
    'native_geometry', label + ' native attribute shape differs from its actual bytes.');
  const readers = ['getX', 'getY', 'getZ', 'getW'];
  for (let row = 0; row < decoded.count; row++) for (let column = 0; column < decoded.size; column++)
    requireThat(attribute[readers[column]](row) === decoded.values[row * decoded.size + column],
      'native_geometry', label + ' native attribute differs from decoded bytes.');
}
function identityTransform(object) {
  return object.position.toArray().every(x => x === 0) && object.quaternion.toArray().every((x, i) => x === (i === 3 ? 1 : 0)) &&
    object.scale.toArray().every(x => x === 1);
}
async function bindNativeGeometry(gltf, geometry) {
  for (const record of geometry.records) {
    const carrier = await gltf.parser.getDependency('node', record.nodeIndex);
    requireThat(carrier && carrier.parent === gltf.scene, 'native_carrier', 'An actual loaded carrier is not a flat scene root.');
    record.carrier = carrier;
    const meshes = []; carrier.traverse(child => { if (child.isMesh) meshes.push(child); });
    requireThat(meshes.length === record.primitives.length, 'native_geometry', 'Loaded primitive count differs from native triangles.');
    const used = new Set();
    for (const primitive of record.primitives) {
      const matches = meshes.filter(mesh => {
        const association = gltf.parser.associations.get(mesh);
        return association?.primitives === primitive.primitiveIndex;
      });
      // Single-primitive GLTFLoader nodes can carry only their node association.
      const mesh = matches.length === 1 ? matches[0] : meshes.length === 1 ? meshes[0] : undefined;
      requireThat(mesh && !used.has(mesh), 'native_geometry', 'Loaded primitive associations are not unambiguous.'); used.add(mesh);
      for (let child = mesh; child !== carrier; child = child.parent)
        requireThat(child && identityTransform(child), 'native_geometry', 'A child transform applies visual placement more than once.');
      checkNativeAttribute(mesh.geometry.getAttribute('position'), primitive.positions, 'Position');
      checkNativeAttribute(mesh.geometry.getAttribute('normal'), primitive.normals, 'Normal');
      checkNativeAttribute(mesh.geometry.index, primitive.indices, 'Index');
      requireThat(!Array.isArray(mesh.material) && mesh.material?.isMeshStandardMaterial,
        'native_material', 'A loaded primitive must use the actual glTF standard PBR material.');
      const source = primitive.source.material;
      sameArray([...mesh.material.color.toArray(), mesh.material.opacity], source.base_color, 'Loaded Three linear RGBA');
      requireThat(mesh.material.metalness === source.metallic && mesh.material.roughness === source.roughness &&
        mesh.material.transparent === (source.base_color[3] < 1), 'native_material', 'Loaded Three PBR factors differ from source.');
      primitive.native = mesh;
    }
  }
}

function sampleReferences(reference, geometry, plan) {
  checkSampleCoverage(reference.samples, plan, reference.source_boundary_times_seconds);
  const paths = geometry.records.map(record => record.source.path).sort(), sitePaths = [...geometry.sites.keys()].sort();
  requireThat(reference.samples.length * (paths.length + sitePaths.length) <= LIMITS.observations,
    'observation_budget', 'The declared pose/site observations exceed the inherited one-million bound.');
  // Primitive geometry can repeat its shared POSITION attribute. Charge the
  // actual repeated native point work before running a destination module.
  const verticesPerSample = geometry.records.reduce((total, record) => total +
    record.primitives.reduce((sum, primitive) => sum + primitive.positions.count, 0), 0);
  requireThat(reference.samples.length * verticesPerSample <= LIMITS.worldVertices,
    'observation_budget', 'The declared world-vertex work exceeds the verifier bound.');
  for (const sample of reference.samples) {
    sameArray(Object.keys(object(sample.poses, 'Source pose observations')).sort(), paths, 'Complete source pose observation inventory');
    sameArray(Object.keys(object(sample.sites, 'Source site observations')).sort(), sitePaths, 'Complete source site observation inventory');
  }
}

function observe(THREE, player, reference, geometry, tolerances) {
  let carrierPoses = 0, sitePoints = 0, worldVertices = 0, maxPosition = ZERO, maxRotation = ZERO, maxSite = ZERO, maxWorld = 0;
  const squaredPosition = square(tolerances.position_m), squaredRotation = square(tolerances.rotation_rad);
  const worldThreshold = numberInterval(squaredPosition)[0], point = new THREE.Vector3(), quaternion = new THREE.Quaternion();
  const errors = [];
  for (const sample of reference.samples) {
    player.setTime(sample.time_seconds);
    const sampleMax = {sample_id: sample.sample_id, kind: sample.kind, time_seconds: sample.time_seconds, side: sample.side,
      position_error_upper_m: 0, rotation_error_upper_rad: 0, site_error_upper_m: 0, world_vertex_error_upper_m: 0};
    if (sample.source_time_seconds !== undefined) sampleMax.source_time_seconds = sample.source_time_seconds;
    for (const record of geometry.records) {
      const expected = object(sample.poses[record.source.path], 'Source pose enclosure');
      const position = enclosure(expected.position_m, 3, 'Source position'), orientation = enclosure(expected.orientation_wxyz, 4, 'Source proper orientation');
      const nativePosition = record.carrier.getWorldPosition(point).toArray(), nativeQuaternion = record.carrier.getWorldQuaternion(quaternion);
      const p2 = positionSquaredError(nativePosition, position), r2 = quaternionAngleSquaredUpper(
        [nativeQuaternion.w, nativeQuaternion.x, nativeQuaternion.y, nativeQuaternion.z], orientation);
      requireThat(compare(p2, squaredPosition) <= 0, 'native_position', 'Actual native carrier position exceeds the source enclosure tolerance.',
        {sample_id: sample.sample_id, path: record.source.path, error_squared_upper: exactText(p2)});
      requireThat(compare(r2, squaredRotation) <= 0, 'native_rotation', 'Actual native proper orientation exceeds the source enclosure tolerance.',
        {sample_id: sample.sample_id, path: record.source.path, error_squared_upper: exactText(r2)});
      carrierPoses++; if (compare(p2, maxPosition) > 0) maxPosition = p2; if (compare(r2, maxRotation) > 0) maxRotation = r2;
      sampleMax.position_error_upper_m = Math.max(sampleMax.position_error_upper_m, errorUpperNumber(p2));
      sampleMax.rotation_error_upper_rad = Math.max(sampleMax.rotation_error_upper_rad, errorUpperNumber(r2));
      for (const site of record.source.sites) {
        const nativePoint = point.fromArray(site.position_m).applyMatrix4(record.carrier.matrixWorld).toArray();
        const s2 = positionSquaredError(nativePoint, enclosure(sample.sites[site.path], 3, 'Source world site'));
        requireThat(compare(s2, squaredPosition) <= 0, 'native_site', 'Actual native world site exceeds the source enclosure tolerance.',
          {sample_id: sample.sample_id, path: site.path, error_squared_upper: exactText(s2)});
        sitePoints++; if (compare(s2, maxSite) > 0) maxSite = s2;
        sampleMax.site_error_upper_m = Math.max(sampleMax.site_error_upper_m, errorUpperNumber(s2));
      }
      if (record.primitives.length) {
        const transform = floatTransformEnclosure(position, orientation);
        for (const primitive of record.primitives) {
          const attribute = primitive.native.geometry.getAttribute('position');
          for (let index = 0; index < attribute.count; index++) {
            const actual = point.fromBufferAttribute(attribute, index).applyMatrix4(primitive.native.matrixWorld).toArray();
            const bound = transformedPointBounds(transform, record.source.geometry.positions[index]);
            const error = floatPositionSquaredUpper(actual, bound);
            requireThat(error <= worldThreshold, 'native_world_vertex', 'Actual native world vertex exceeds the source enclosure tolerance.',
              {sample_id: sample.sample_id, path: record.source.path, primitive: primitive.primitiveIndex, vertex: index,
                error_squared_upper: error, tolerance_squared_lower: worldThreshold});
            worldVertices++; maxWorld = Math.max(maxWorld, error);
            // Display roots are outward-enclosed with exact arithmetic too.
            sampleMax.world_vertex_error_upper_m = Math.max(sampleMax.world_vertex_error_upper_m, error);
          }
        }
      }
    }
    sampleMax.world_vertex_error_upper_m = errorUpperNumber(fromNumber(sampleMax.world_vertex_error_upper_m));
    errors.push(sampleMax);
  }
  return {samples: reference.samples.length, carrier_poses: carrierPoses, world_sites: sitePoints, world_vertices: worldVertices,
    max_position_error_upper_m: errorUpperNumber(maxPosition), max_rotation_error_upper_rad: errorUpperNumber(maxRotation),
    max_site_error_upper_m: errorUpperNumber(maxSite), max_world_vertex_error_upper_m: errorUpperNumber(fromNumber(maxWorld)),
    exact_position_error_squared_upper: exactText(maxPosition), exact_rotation_error_squared_upper: exactText(maxRotation),
    exact_site_error_squared_upper: exactText(maxSite), observations: errors};
}

export async function verifyCase(item, directory, dependencies, observed = new Map()) {
  identityString(item.case_id, 'Case ID');
  const bytes = await readDescriptor(directory, item.artifact, observed), referenceBytes = await readDescriptor(directory, item.reference, observed);
  const reference = parseJson(referenceBytes, 'Independent native reference');
  requireThat(reference.schema_version === 'ontokin.reach-native-reference/0.1' && digest(reference.artifact_sha256) === sha256(bytes),
    'reference_identity', 'The source reference does not identify the supplied actual artifact bytes.');
  const parsed = parseGlb(bytes), plan = requiredPlan(parsed), metadata = parsed.document.extras.ontokin;
  const identity = await checkSourceIdentity(item, reference, metadata, directory, observed);
  const basis = await checkBasis(metadata, observed), tolerances = checkedTolerances(reference, metadata, plan);
  const geometry = prepareGeometry(parsed, reference, identity, tolerances);
  sampleReferences(reference, geometry, plan);
  const {THREE, GLTFLoader, validator, attachReachPlayback} = dependencies;
  requireThat(THREE.REVISION === '180', 'dependency_identity', 'Actual Three.js revision must be 180.');
  const validation = await validator.validateBytes(new Uint8Array(bytes), {uri: item.case_id + '.glb', maxIssues: 1000,
    externalResourceFunction: async uri => { throw new NativeVerificationError('external_resource', 'External glTF resource access is forbidden.', {uri}); }});
  requireThat(validation.issues?.numErrors === 0 && validation.issues?.numWarnings === 0 && !validation.issues?.truncated,
    'khronos', 'Actual Khronos validation did not pass with zero errors and warnings.', {issues: validation.issues});
  const exactBuffer = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
  const gltf = await new GLTFLoader().parseAsync(exactBuffer, '');
  requireThat(gltf.scene && gltf.scenes.length === 1 && gltf.scene.children.length === parsed.document.nodes.length && identityTransform(gltf.scene),
    'native_carrier', 'The actual loaded scene hierarchy differs from the flat source carriers.');
  await bindNativeGeometry(gltf, geometry);
  const player = await attachReachPlayback(gltf, {threeRevision: THREE.REVISION});
  requireThat(player.carrierCount === geometry.records.length && player.name === basis.destination.name && player.version === basis.destination.version,
    'destination_identity', 'The actual controlled player does not match the identified native destination.');
  const observations = observe(THREE, player, reference, geometry, tolerances);
  return {case_id: item.case_id, status: 'passed', program_revision: identity.revision, artifact: item.artifact, reference: item.reference,
    sources: item.sources, oracle_inputs: identity.oracleInputs, source_geometry_method: reference.oracle.geometry_method ?? 'source-provided canonical mesh arrays; construction reuse must be disclosed by the producer',
    numerical_basis: basis, khronos: validation, controlled_player: {name: player.name, version: player.version, carrier_count: player.carrierCount},
    schedule: {stored_keys: plan.stored_key_count, intervals: plan.interval_count, interiors_per_interval: 8,
      source_boundaries: plan.source_boundary_count, source_boundary_sides: 2, required_samples: plan.required_samples.length,
      fixture_samples: reference.samples.length - plan.required_samples.length},
    geometry: {carriers: geometry.records.length, occurrence_vertices: geometry.vertexCount, primitives: geometry.primitiveCount,
      triangles: geometry.triangleCount, source_sites: geometry.sites.size, max_local_vertex_error_upper_m: errorUpperNumber(geometry.maxLocalError)},
    max_stored_clock_error_upper_s: errorUpperNumber(tolerances.max_time_error_squared), tolerances: reference.tolerances, ...observations};
}

async function dependencies() {
  const [THREE, loader, validatorModule, player] = await Promise.all([
    import('three'), import('three/addons/loaders/GLTFLoader.js'), import('gltf-validator'), import('./reach_destination.mjs'),
  ]);
  const validator = validatorModule.default ?? validatorModule;
  const validatorVersion = typeof validator.version === 'function' ? validator.version() : validator.version;
  requireThat(validatorVersion === '2.0.0-dev.3.10', 'dependency_identity', 'The actual Khronos validator version differs from the pinned version.', {actual: validatorVersion});
  return {THREE, GLTFLoader: loader.GLTFLoader, validator, attachReachPlayback: player.attachReachPlayback,
    versions: {three: THREE.REVISION, gltf_validator: validatorVersion}};
}

function failure(error) { return {code: error.code ?? 'exception', message: error.message ?? String(error), details: error.details ?? {}}; }
export async function verifyManifest(filename) {
  const observed = new Map(), report = {schema_version: SCHEMA, status: 'running', started_at: new Date().toISOString(),
    scope: 'Actual supplied bytes in Khronos and Three.js with the identified controlled reach player and independently supplied source enclosures.',
    unverified_scopes: OMITTED_SCOPES, release_acceptance: false, agent_transport_audited: false,
    execution: {node: process.version, platform: process.platform, architecture: process.arch,
      required_release_node_major: 22, release_node_major_matches: Number(process.versions.node.split('.')[0]) === 22}, cases: []};
  try {
    const absolute = await realpath(filename), directory = path.dirname(absolute), bytes = await boundedRead(absolute), manifest = parseJson(bytes, 'Native input manifest');
    observed.set(absolute, {path: path.basename(absolute), sha256: sha256(bytes), bytes: bytes.length, maximum: LIMITS.bytes});
    requireThat(manifest.schema_version === 'ontokin.reach-native-input/0.1' &&
      ['source_component', 'agent_retrieved_artifact'].includes(manifest.source_kind) &&
      Array.isArray(manifest.cases) && manifest.cases.length > 0 && manifest.cases.length <= LIMITS.cases,
      'manifest', 'A bounded explicit source/Agent native input manifest is required.');
    for (const key of ['source_commit', 'source_tree'])
      requireThat(typeof manifest[key] === 'string' && /^[0-9a-f]{40}$/.test(manifest[key]), 'manifest', 'A source Git ' + key + ' identity is required.');
    report.source_kind = manifest.source_kind; report.producer_source_commit = manifest.source_commit; report.producer_source_tree = manifest.source_tree;
    report.source_git_identity_audited = false; report.manifest = {sha256: sha256(bytes), bytes: bytes.length};
    const ids = new Set();
    for (const item of manifest.cases) {
      requireThat(!ids.has(item.case_id), 'manifest', 'Case IDs must be unique.'); ids.add(item.case_id);
    }
    report.implementation_inputs = {};
    for (const name of SELF_INPUTS) report.implementation_inputs[name] = await implementationInput(name, observed);
    const packages = parseJson(await boundedRead(await containedPath(root, 'tools/package.json')), 'Pinned tool package');
    requireThat(packages.devDependencies?.three === '0.180.0' && packages.devDependencies?.['gltf-validator'] === '2.0.0-dev.3.10',
      'dependency_identity', 'The checked tool package does not retain the adopted dependency pins.');
    const loaded = await dependencies(); report.execution.dependencies = loaded.versions;
    for (const item of manifest.cases) {
      try { report.cases.push(await verifyCase(item, directory, loaded, observed)); }
      catch (error) { report.cases.push({case_id: item.case_id, status: 'failed', failure: failure(error)}); }
    }
    await assertStable(observed);
    report.status = report.cases.every(item => item.status === 'passed') ? 'passed' : 'failed';
  } catch (error) { report.status = 'failed'; report.failure = failure(error); }
  report.inputs = [...observed.values()].map(({maximum, ...value}) => value);
  report.passed_cases = report.cases.filter(item => item.status === 'passed').length;
  report.failed_cases = report.cases.filter(item => item.status !== 'passed').length;
  report.finished_at = new Date().toISOString(); return report;
}

export async function planArtifact(filename) {
  const bytes = await boundedRead(filename), plan = requiredPlan(parseGlb(bytes));
  return {schema_version: plan.schema_version, artifact_sha256: sha256(bytes), artifact_bytes: bytes.length,
    program_revision: plan.program_revision, stored_key_count: plan.stored_key_count, interval_count: plan.interval_count,
    source_boundary_count: plan.source_boundary_count, required_samples: plan.required_samples};
}

async function main(args) {
  if (args.length === 1 && args[0] === '--help') {
    process.stdout.write('Usage: node tools/verify_reach_native.mjs --manifest native-input.json --output fresh-report.json\n' +
      '       node tools/verify_reach_native.mjs --plan scene.glb [--output fresh-plan.json]\n'); return;
  }
  const options = new Map();
  for (let i = 0; i < args.length; i += 2) {
    requireThat(['--manifest', '--plan', '--output'].includes(args[i]) && args[i + 1] && !options.has(args[i]), 'arguments', 'Invalid or repeated command option.');
    options.set(args[i], args[i + 1]);
  }
  requireThat(options.has('--manifest') !== options.has('--plan') && (options.has('--plan') || options.has('--output')),
    'arguments', 'Choose either --plan or --manifest; verification requires a fresh output path.');
  if (options.has('--output')) {
    try { await stat(options.get('--output')); throw new NativeVerificationError('output_exists', 'The output path already exists; preserve prior evidence.'); }
    catch (error) { if (error.code !== 'ENOENT') throw error; }
  }
  const result = options.has('--plan') ? await planArtifact(options.get('--plan')) : await verifyManifest(options.get('--manifest'));
  const encoded = JSON.stringify(result, null, 2) + '\n';
  if (options.has('--output')) await writeFile(options.get('--output'), encoded, {flag: 'wx'});
  else process.stdout.write(encoded);
  if (result.status === 'failed') process.exitCode = 1;
  if (options.has('--output')) process.stdout.write(JSON.stringify({schema_version: result.schema_version, status: result.status ?? 'planned',
    output: options.get('--output'), passed_cases: result.passed_cases, failed_cases: result.failed_cases}) + '\n');
}
if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href)
  main(process.argv.slice(2)).catch(error => { process.stderr.write(JSON.stringify(failure(error)) + '\n'); process.exitCode = 1; });
