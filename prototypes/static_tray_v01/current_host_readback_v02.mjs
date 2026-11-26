/* Read-only Khronos/Three.js inspection of one retained static-tray GLB.
 * This imports actual delivered bytes. It never builds or exports geometry.
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';

const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const stable = value => JSON.stringify(canonical(value));
function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (value && typeof value === 'object') return Object.fromEntries(Object.keys(value).sort().map(k => [k, canonical(value[k])]));
  return value;
}
function readBound(filename, maximum) {
  const info = fs.lstatSync(filename);
  if (!info.isFile() || info.size > maximum) throw Error('Unsafe or over-limit input: ' + filename);
  const fd = fs.openSync(filename, 'r');
  try {
    const buffer = Buffer.alloc(maximum + 1);
    const length = fs.readSync(fd, buffer, 0, buffer.length, 0);
    if (length > maximum) throw Error('Input exceeds its byte limit');
    return buffer.subarray(0, length);
  } finally { fs.closeSync(fd); }
}
function output(filename, value) {
  const data = Buffer.from(JSON.stringify(value, null, 2) + '\n');
  if (data.length > 4 * 1024 * 1024) throw Error('Readback result exceeds 4 MiB');
  const fd = fs.openSync(filename, 'wx');
  try { fs.writeFileSync(fd, data); fs.fsyncSync(fd); } finally { fs.closeSync(fd); }
}
function finite(values) { return values.every(Number.isFinite); }
function matrixRows(matrix) {
  return [0, 1, 2, 3].map(i => [0, 1, 2, 3].map(j => matrix.elements[j * 4 + i]));
}

// Gate I bootstrap adaptation. The approved digest is a caller authority input,
// never a value inferred from the configuration or its surrounding manifest.
import { fileURLToPath } from 'node:url';
import os from 'node:os';

const CONTRACT = 'ontokin.current-host-readback/0.2.0';
const CONFIG_SCHEMA = 'ontokin.current-host-readback-config/0.2.0';
const MANIFEST_SCHEMA = 'ontokin.current-host-readback-lock/0.2.0';
const OWN_PROBE = fileURLToPath(import.meta.url);
const OWN_ROOT = path.dirname(path.dirname(path.dirname(OWN_PROBE)));
const PROVIDER_RELATIVE = 'prototypes/static_tray_v01/current_host_readback_v02.py';
const PROBE_RELATIVE = 'prototypes/static_tray_v01/current_host_readback_v02.mjs';
const CONTRACT_RELATIVE = 'docs/engineering/localized-repair-c271/macos-contract-design-p31/CONTRACT.md';
const MAP_RELATIVE = 'docs/engineering/localized-repair-c271/current-host-p05/mapping/MAP-EVIDENCE.zip';
const CONTRACT_SHA = '42db98dc6099ee605b0963f3734f7bff2d68c019ff6c00a0ee97bd753c03fdc9';
// Design revision 4: the adopted 0.2.0 contract as amended by P33-AMENDMENT-001 (decisions D-03 and D-12).
const PROFILE = 'darwin-arm64-v1';
const EXECUTOR = 'macos-arm64-local';
const DESIGN_REVISION = 4;
const AMENDMENTS = ['P33-AMENDMENT-001'];
// The amendment's adoption record, bound by path and by this SHA-256 of its adopted bytes.
const AMENDMENT_ADOPTION_RELATIVE = 'docs/engineering/localized-repair-c271/macos-implementation-p33/ADOPTION-AMENDMENT-001.json';
const AMENDMENT_ADOPTION_SHA = '872312ed80a63fbb196c17ace42e786b7fe757b710eff41139b125dfaa507937';
// The official darwin-arm64 archive pin (S1). The executable's own pin is frozen at preparation and read from HOST.
const NODE_ARCHIVE = 'node-v24.22.1-darwin-arm64.tar.gz';
const NODE_ARCHIVE_SHA = '89c682593d76cd44233fa53b1563264e7de9cbb189cad169135c5b4fadfbc0a7';
const DEPENDENCY_ARCHIVE_SHA = 'b1e54a6cfef133f7004b1988c90bc718fc954409843c2bcac3772d42e904a0c9';
const NODE_FLAGS = ['--no-addons', '--max-old-space-size=256'];
const ENVIRONMENT = {PATH:'/usr/bin:/bin', LANG:'C.UTF-8', LC_ALL:'C.UTF-8', TZ:'UTC', UV_THREADPOOL_SIZE:'2'};
const LIMITS = {maximum_checks:12, host_ms:30000, child_work_ms:28000, cleanup_ms:2000,
  glb_bytes:8388608, result_bytes:4194304, log_bytes:4194304};
const VALIDATOR_OPTIONS = {format:'glb', writeTimestamp:false, maxIssues:1000,
  allowed_errors:0, allowed_warnings:0, ignoredIssues:[], external_resources:'rejected'};
const THREE_OPTIONS = {position_tolerance_m:0.000005, matrix_tolerance:0.000001,
  node_count:14, mesh_count:12, animation_count:0, external_resources:'rejected'};
const SOURCE_TREES = ['ontokin', 'tests', 'prototypes/static_tray_v01', 'tools/static_tray_reader_v01'];
const SOURCE_OPTIONAL = ['prototypes/__init__.py', 'tools/__init__.py', 'tests/__init__.py'];
// The /0.2.0 source inventory: the 0.1.0 roles plus the macOS lock and the adopted 0.2.0 contract files,
// the same set as current_host_observation_v02.SOURCE_FILES.
const SOURCE_REQUIRED = ['tools/check_local.py', 'tools/prepare_current_host_readback.py', 'tools/storage_identity.py',
  'tools/force-agent-verification-requirements.txt', 'tools/native-reader-verification-linux-cp312.lock',
  'tools/native-reader-verification-macos-arm64-cp312.lock', 'pyproject.toml',
  'docs/engineering/static-tray-mapping-c198/CONTROLS.json',
  'docs/engineering/static-tray-qualification-c199/EXTERNAL-INPUTS.json',
  'docs/engineering/localized-repair-c271/current-host-p05/CONTRACT.md',
  'docs/engineering/localized-repair-c271/current-host-p05/CONTRACT.json',
  'docs/engineering/localized-repair-c271/current-host-p05/ADOPTION.json', MAP_RELATIVE,
  CONTRACT_RELATIVE, 'docs/engineering/localized-repair-c271/macos-contract-design-p31/CONTRACT.json',
  'docs/engineering/localized-repair-c271/macos-contract-design-p31/ADOPTION.json'];
const CONFIG_KEYS = ['schema','contract','contract_source','amendment_adoption','source','host','dependencies','runtime','methods','evidence_root','parent'];
const MANIFEST_KEYS = ['schema','contract','design_revision','amendments','labels','profile','schedule_root','cohort_root','dependencies_root','scope','limits',
  'environment','files','runtime','validator_version','three_version','validator_entry','three_package','three_entry',
  'gltf_loader_entry','module_loader','probe','validator_options','three_options','slots','selection','source','host','methods','dependencies'];
const WORKSPACE_KEYS = ['schema','contract','design_revision','amendments','identity','parent_config','source_root','workspace_root',
  'commit','tree','source_inventory','source_before','workspace_inventory','immutable_inventory_sha256','provider','probe'];
const HOST_KEYS = ['schema','contract','design_revision','amendments','profile','executor','observed_at_utc','plan','observer',
  'platform','os','environment','python','runtime','git','dependencies','source','inspections','starts','labels','claims'];
const MACOS_LOCK_RELATIVE = 'tools/native-reader-verification-macos-arm64-cp312.lock';
const SYSTEM_VERSION_PATH = '/System/Library/CoreServices/SystemVersion.plist';
const CF_NAME = '__CF_USER_TEXT_ENCODING';
const GIT_ENVIRONMENT = {...ENVIRONMENT, GIT_CONFIG_NOSYSTEM:'1', GIT_CONFIG_GLOBAL:'/dev/null', GIT_TERMINAL_PROMPT:'0',
  GIT_ATTR_NOSYSTEM:'1', GIT_OPTIONAL_LOCKS:'0', GIT_NO_REPLACE_OBJECTS:'1'};
const GIT_VERSION_PATTERN = /^git version [\x20-\x7e]{1,200}$/;
const JOB_KEYS = ['slot','case','manifest','supplemental_manifest_sha256','input_lock_sha256','artifact','artifact_sha256','audit','audit_sha256','result'];
const SHA_PATTERN = /^[0-9a-f]{64}$/;
const GIT_PATTERN = /^(?:[0-9a-f]{40}|[0-9a-f]{64})$/;
const ORIGINAL_BODIES = {
  'ReadbackCoordinatorSeams.run_seam':'2f39cde2f0f4a18eb54b003e2628b22c47d49495d862d25e38223b5a056817a5',
  'ReadbackCoordinatorSeams.test_result_write_failure_leaves_predecessor_gate_blocked':'222b654a8da505965f0821be4e7b61eefeb1a5f12e767c72e6123feba909f06d',
  'ReadbackCoordinatorSeams.test_host_alarm_cannot_interrupt_supervisor_cleanup':'29665028886624307beacb4debb33b8582f91bf60951149c0160ae957ed68f98',
  'ReadbackCoordinatorSeams.test_success_finalization_uses_remaining_outer_alarm':'f4a5d8242e91d3792039b94f2f75c8002b7cc5e1b432ce3cc91d46d65d3f1f55',
  'ReadbackCoordinatorSeams.test_uncertain_marker_removal_recreates_pending':'5e3041a6f1e57db4c4c03e97927e1aa88c6d8dfe2b431e71b38319e3851b75bc',
  'ReadbackCPUControls.check_case':'53a03c60a7473af90ba88f2fddf225713036d417cf3c13a0c1e8a6a3105946a4',
  'ReadbackCPUControls.test_q01_actual_synthetic_meshes_load_in_both_libraries':'e7793b38ebedd196c228ce6841642c2546c8ef1f5db552b1b1f824a30087fd34',
  'ReadbackCPUControls.test_q03_actual_synthetic_rotations_load_in_both_libraries':'e09a9c173e4879558da9206549f085a840639a314c22e525fccabc498c7e3dd4',
  'ReadbackCPUControls.test_three_rejects_changed_synthetic_reference':'8b2de031c533e1308efeef130047b0a2b4fcfc1cb6cd2f576e7b3ef832ec05d9'
};
const ORIGINAL_METHOD_IDS = Object.keys(ORIGINAL_BODIES).filter(name => name.includes('.test_')).map(name => 'test_static_tray_readback_v01.' + name).sort();

function requireValue(condition, message) {
  if (!condition) throw Error('Current-host binding: ' + message);
}
function requireSelection(condition, message) {
  if (!condition) {
    const error = Error('CH-SELECTION: ' + message);
    error.name = 'CurrentHostBindingError';
    error.code = 'CH-SELECTION';
    throw error;
  }
}
function plainObject(value, name) {
  requireValue(value !== null && typeof value === 'object' && !Array.isArray(value), name + ' must be an object');
  return value;
}
function exactKeys(value, keys, name) {
  plainObject(value, name);
  requireValue(stable(Object.keys(value).sort()) === stable(keys.slice().sort()), name + ' has unknown, missing or extra fields');
}
function same(actual, expected, name) {
  requireValue(stable(actual) === stable(expected), name + ' differs');
}
function digest(value, name) {
  requireValue(typeof value === 'string' && SHA_PATTERN.test(value), name + ' is not a lowercase SHA-256');
  return value;
}
function timestamp(value, name) {
  requireValue(typeof value === 'string' && /(?:Z|[+-][0-9]{2}:[0-9]{2})$/.test(value) &&
    Number.isFinite(Date.parse(value)), name + ' is not a zoned timestamp');
  return Date.parse(value);
}
function absolute(value, name) {
  requireValue(typeof value === 'string' && value.length > 1 && !value.includes('\0') &&
    path.isAbsolute(value) && path.resolve(value) === value, name + ' is not an absolute normalized path');
  return value;
}
function relative(value) {
  requireValue(typeof value === 'string' && value.length > 0 && !value.includes('\\') && !value.includes('\0') &&
    !path.isAbsolute(value) && !value.split('/').some(p => p === '' || p === '.' || p === '..'), 'unsafe relative path');
  return value;
}
function inside(value, root, name) {
  absolute(value, name); absolute(root, name + ' root');
  requireValue(value.startsWith(root + '/'), name + ' escapes its bound parent');
  return value;
}
function present(filename) {
  try { fs.lstatSync(filename); return true; }
  catch (error) { if (error.code === 'ENOENT') return false; throw error; }
}
function canonicalDirectory(filename) {
  absolute(filename, 'directory');
  const info = fs.lstatSync(filename);
  requireValue(info.isDirectory() && !info.isSymbolicLink() && fs.realpathSync(filename) === filename,
    'directory is absent, aliased or unsafe: ' + filename);
  return filename;
}
function validateBinding(binding, withPath = false) {
  exactKeys(binding, withPath ? ['path','sha256','size_bytes','mode'] : ['sha256','size_bytes','mode'], 'file binding');
  digest(binding.sha256, 'file digest');
  requireValue(Number.isSafeInteger(binding.size_bytes) && binding.size_bytes >= 0, 'file size is invalid');
  requireValue(typeof binding.mode === 'string' && /^0o[0-7]{3,4}$/.test(binding.mode), 'file mode is invalid');
  if (withPath) absolute(binding.path, 'descriptor path');
}
function fileBytes(filename, maximum, binding = null, retain = true, rejectHardlink = false) {
  absolute(filename, 'file path');
  if (binding) validateBinding(binding, Object.hasOwn(binding, 'path'));
  const before = fs.lstatSync(filename);
  requireValue(before.isFile() && !before.isSymbolicLink() && fs.realpathSync(filename) === filename,
    'file is not canonical and regular: ' + filename);
  requireValue(!rejectHardlink || before.nlink === 1, 'hardlinked source or dependency: ' + filename);
  requireValue(Number.isSafeInteger(before.size) && before.size <= maximum, 'file exceeds its bound: ' + filename);
  if (binding) {
    requireValue(before.size === binding.size_bytes && '0o' + (before.mode & 0o7777).toString(8) === binding.mode,
      'file size or mode differs: ' + filename);
  }
  const fd = fs.openSync(filename, fs.constants.O_RDONLY | fs.constants.O_NOFOLLOW | fs.constants.O_NONBLOCK);
  const parts = [], hash = crypto.createHash('sha256');
  let total = 0;
  try {
    const opened = fs.fstatSync(fd);
    requireValue(opened.isFile() && (!rejectHardlink || opened.nlink === 1) &&
      opened.dev === before.dev && opened.ino === before.ino && opened.size === before.size &&
      opened.mode === before.mode && opened.nlink === before.nlink &&
      opened.mtimeMs === before.mtimeMs && opened.ctimeMs === before.ctimeMs,
      'file changed while opening: ' + filename);
    const block = Buffer.alloc(1024 * 1024);
    for (;;) {
      const size = fs.readSync(fd, block, 0, block.length, null);
      if (size === 0) break;
      total += size;
      requireValue(total <= maximum && total <= before.size, 'file grew while reading: ' + filename);
      hash.update(block.subarray(0, size));
      if (retain) parts.push(Buffer.from(block.subarray(0, size)));
    }
    const after = fs.fstatSync(fd), named = fs.lstatSync(filename);
    requireValue(total === before.size && after.isFile() && named.isFile() &&
      after.nlink === before.nlink && named.nlink === before.nlink &&
      after.dev === before.dev && after.ino === before.ino &&
      after.size === before.size && after.mode === before.mode && after.mtimeMs === before.mtimeMs &&
      after.ctimeMs === before.ctimeMs && named.dev === before.dev && named.ino === before.ino &&
      named.size === before.size && named.mode === before.mode && named.mtimeMs === before.mtimeMs &&
      named.ctimeMs === before.ctimeMs &&
      !named.isSymbolicLink() && fs.realpathSync(filename) === filename, 'file changed during read: ' + filename);
  } finally { fs.closeSync(fd); }
  const observed = hash.digest('hex');
  if (binding) requireValue(observed === binding.sha256, 'file hash differs: ' + filename);
  return retain ? Buffer.concat(parts, total) : observed;
}
function boundJSON(descriptor, maximum) {
  validateBinding(descriptor, true);
  return strictJSON(fileBytes(descriptor.path, maximum, descriptor), descriptor.path);
}

// JSON.parse alone loses duplicate object names. This bounded grammar validates
// names before constructing an object; JSON.parse decodes individual string tokens.
function strictJSON(bytes, name) {
  const text = new TextDecoder('utf-8', {fatal:true}).decode(bytes);
  let index = 0;
  const white = () => { while (index < text.length && /[\x20\t\r\n]/.test(text[index])) index++; };
  function string() {
    const start = index++;
    let escaped = false;
    while (index < text.length) {
      const c = text[index++];
      if (!escaped && c === '"') return JSON.parse(text.slice(start, index));
      if (!escaped && c === '\\') escaped = true;
      else escaped = false;
    }
    throw Error('Unterminated JSON string: ' + name);
  }
  function value(depth) {
    requireValue(depth <= 64, 'JSON nesting exceeds limit: ' + name);
    white();
    const c = text[index];
    if (c === '"') return string();
    if (c === '{') {
      index++; white();
      const result = Object.create(null), names = new Set();
      if (text[index] === '}') { index++; return result; }
      for (;;) {
        white(); requireValue(text[index] === '"', 'expected JSON object name: ' + name);
        const key = string();
        requireValue(!names.has(key), 'duplicate JSON object name: ' + name);
        names.add(key); white(); requireValue(text[index++] === ':', 'expected JSON colon: ' + name);
        result[key] = value(depth + 1); white();
        const next = text[index++];
        if (next === '}') return result;
        requireValue(next === ',', 'expected JSON object separator: ' + name);
      }
    }
    if (c === '[') {
      index++; white(); const result = [];
      if (text[index] === ']') { index++; return result; }
      for (;;) {
        result.push(value(depth + 1)); white(); const next = text[index++];
        if (next === ']') return result;
        requireValue(next === ',', 'expected JSON array separator: ' + name);
      }
    }
    for (const [token, decoded] of [['true',true],['false',false],['null',null]]) {
      if (text.startsWith(token, index)) { index += token.length; return decoded; }
    }
    const match = /^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?/.exec(text.slice(index));
    requireValue(match !== null, 'invalid JSON value: ' + name);
    index += match[0].length;
    const number = Number(match[0]);
    requireValue(Number.isFinite(number), 'nonfinite JSON number: ' + name);
    return number;
  }
  const result = value(0); white();
  requireValue(index === text.length, 'trailing JSON content: ' + name);
  return result;
}

function walkFiles(root, relativeRoot = '', {rejectCache = false} = {}) {
  canonicalDirectory(path.join(root, relativeRoot));
  const files = {}, directories = {};
  function walk(name) {
    const directory = path.join(root, name);
    for (const child of fs.readdirSync(directory).sort()) {
      const rel = name ? name + '/' + child : child;
      relative(rel);
      requireValue(!rejectCache || !rel.split('/').includes('__pycache__') && !/\.py[co]$/.test(rel), 'unbound source bytecode/cache');
      const filename = path.join(root, rel), info = fs.lstatSync(filename);
      requireValue(!info.isSymbolicLink(), 'symlink in complete file inventory: ' + filename);
      if (info.isDirectory()) { directories[rel] = '0o' + (info.mode & 0o7777).toString(8); walk(rel); }
      else { requireValue(info.isFile() && info.nlink === 1, 'nonregular or hardlinked inventory input'); files[rel] = filename; }
      requireValue(Object.keys(files).length + Object.keys(directories).length <= 50000, 'file inventory exceeds entry bound');
    }
  }
  walk(relativeRoot);
  return {files, directories};
}

function verifySource(config) {
  exactKeys(config.source, ['root','commit','tree','inventory'], 'source');
  requireValue(config.source.root === OWN_ROOT && fs.realpathSync(OWN_ROOT) === OWN_ROOT &&
    OWN_PROBE === path.join(OWN_ROOT, PROBE_RELATIVE), 'probe is outside its bound checkout');
  requireValue(typeof config.source.commit === 'string' && typeof config.source.tree === 'string' &&
    GIT_PATTERN.test(config.source.commit) && GIT_PATTERN.test(config.source.tree) &&
    config.source.commit.length === config.source.tree.length, 'invalid source commit/tree identity');
  const inventory = boundJSON(config.source.inventory, 16 * 1024 * 1024);
  exactKeys(inventory, ['schema','files'], 'source inventory');
  requireValue(inventory.schema === 'ontokin.current-host-readback-source/0.2.0', 'wrong source inventory schema');
  plainObject(inventory.files, 'source inventory files');
  const actual = {};
  for (const tree of SOURCE_TREES) Object.assign(actual, walkFiles(OWN_ROOT, tree, {rejectCache:true}).files);
  for (const rel of [...SOURCE_REQUIRED, ...SOURCE_OPTIONAL.filter(p => present(path.join(OWN_ROOT, p)))]) actual[rel] = path.join(OWN_ROOT, rel);
  same(Object.keys(actual).sort(), Object.keys(inventory.files).sort(), 'complete source file inventory');
  for (const [rel, binding] of Object.entries(inventory.files)) {
    relative(rel); validateBinding(binding);
    fileBytes(actual[rel], binding.size_bytes, binding, false, true);
  }
  validateBinding(config.contract_source, true);
  requireValue(config.contract_source.path === path.join(OWN_ROOT, CONTRACT_RELATIVE) &&
    config.contract_source.sha256 === CONTRACT_SHA, 'adopted contract source differs');
  fileBytes(config.contract_source.path, 1024 * 1024, config.contract_source, false, true);
  same({sha256:config.contract_source.sha256, size_bytes:config.contract_source.size_bytes, mode:config.contract_source.mode},
    inventory.files[CONTRACT_RELATIVE], 'contract source inventory binding');
  validateBinding(config.amendment_adoption, true);
  requireValue(config.amendment_adoption.path === path.join(OWN_ROOT, AMENDMENT_ADOPTION_RELATIVE) &&
    config.amendment_adoption.sha256 === AMENDMENT_ADOPTION_SHA, 'adopted amendment record differs');
  fileBytes(config.amendment_adoption.path, 1024 * 1024, config.amendment_adoption, false, true);
  return inventory;
}

function verifyDependencies(config, sourceInventory) {
  exactKeys(config.dependencies, ['root','inventory'], 'dependencies');
  const root = canonicalDirectory(config.dependencies.root);
  requireValue(root !== OWN_ROOT && !root.startsWith(OWN_ROOT + '/'), 'dependencies are not external');
  const inventory = boundJSON(config.dependencies.inventory, 1024 * 1024);
  exactKeys(inventory, ['schema','files','directories','archive'], 'dependency inventory');
  requireValue(inventory.schema === 'ontokin.current-host-readback-dependencies/0.2.0', 'wrong dependency inventory schema');
  validateBinding(inventory.archive, true);
  requireValue(inventory.archive.sha256 === DEPENDENCY_ARCHIVE_SHA, 'dependency archive identity differs');
  fileBytes(inventory.archive.path, inventory.archive.size_bytes, inventory.archive, false);
  const historicalPath = 'docs/engineering/static-tray-qualification-c199/EXTERNAL-INPUTS.json';
  const historical = strictJSON(fileBytes(path.join(OWN_ROOT, historicalPath), 1024 * 1024,
    sourceInventory.files[historicalPath]), 'historical dependency binding');
  requireValue(sourceInventory.files[historicalPath].sha256 === '21fd6bad8738ed51d4ced8036a0fcde5dd046823f55f71de52b9b81df659ccd5',
    'historical dependency manifest changed');
  const expected = {};
  for (const [filename, binding] of Object.entries(historical.files)) {
    if (filename.startsWith(historical.dependencies_root + '/')) expected[filename.slice(historical.dependencies_root.length + 1)] = binding;
  }
  requireValue(Object.keys(expected).length === 24, 'historical dependency inventory is not exactly 24 files');
  same(Object.keys(inventory.files).sort(), Object.keys(expected).sort(), 'exact retained dependency paths');
  const actual = walkFiles(root);
  same(Object.keys(actual.files).sort(), Object.keys(expected).sort(), 'installed dependency files');
  same(actual.directories, inventory.directories, 'installed dependency directory paths and modes');
  const necessary = new Set();
  for (const [rel, binding] of Object.entries(inventory.files)) {
    relative(rel); validateBinding(binding);
    requireValue(binding.sha256 === expected[rel].sha256 && binding.size_bytes === expected[rel].size_bytes,
      'retained dependency bytes changed');
    fileBytes(path.join(root, rel), binding.size_bytes, binding, false, true);
    let parent = path.posix.dirname(rel);
    while (parent !== '.') { necessary.add(parent); parent = path.posix.dirname(parent); }
  }
  same([...necessary].sort(), Object.keys(inventory.directories).sort(), 'necessary dependency directories');
  for (const [rel, version] of [['validator/package/package.json','2.0.0-dev.3.10'], ['indexer-view/three/package.json','0.186.1']]) {
    const info = strictJSON(fileBytes(path.join(root, rel), 32768, inventory.files[rel]), 'dependency package');
    requireValue(info.version === version, 'dependency package version differs');
  }
  return inventory;
}

// 0.2.0 host binding (contract sections 7 and 10, S7 and S10, decision D-10). The ELF interpreter and the
// alias closure of 0.1.0 have no Darwin analogue; the boot identity is bound by the provider, not here.
function environmentAdmitted(observed, declared, recordedCf) {
  // The twin of current_host_observation_v02.environment_admitted: exactly declared, or declared plus
  // __CF_USER_TEXT_ENCODING with the recorded non-empty value; declared never holds that name.
  if (observed === null || typeof observed !== 'object' || Array.isArray(observed) ||
    declared === null || typeof declared !== 'object' || Array.isArray(declared)) return false;
  const entries = [...Object.entries(observed), ...Object.entries(declared)];
  if (!entries.every(([name, value]) => typeof name === 'string' && typeof value === 'string')) return false;
  if (Object.hasOwn(declared, CF_NAME)) return false;
  if (stable(observed) === stable(declared)) return true;
  return typeof recordedCf === 'string' && recordedCf !== '' && stable(observed) === stable({...declared, [CF_NAME]:recordedCf});
}

function osLabel(identity) {
  const system = identity.system_version, cryptex = identity.cryptex;
  return {product_version:system.product_version, product_build_version:system.product_build_version,
    product_version_extra:system.product_version_extra,
    cryptex:cryptex.state === 'absent' ? {state:'absent'} : {state:'present', product_version:cryptex.product_version,
      product_build_version:cryptex.product_build_version, product_version_extra:cryptex.product_version_extra}};
}

function verifyOsIdentity(identity) {
  // SystemVersion.plist and the OS cryptex copy, by bytes. The copy is bound by its canonical path; its
  // conventional name and every recorded link hop are followed again, so a retargeted hop refuses.
  exactKeys(identity, ['system_version','cryptex'], 'host OS identity');
  const fields = ['state','path','sha256','size_bytes','mode','product_name','product_version','product_build_version','product_version_extra'];
  const system = identity.system_version;
  exactKeys(system, fields, 'OS build file');
  requireValue(system.state === 'present' && system.path === SYSTEM_VERSION_PATH, 'OS build file differs');
  fileBytes(system.path, 65536, {sha256:system.sha256, size_bytes:system.size_bytes, mode:system.mode}, false);
  const cryptex = identity.cryptex;
  plainObject(cryptex, 'OS cryptex copy');
  requireValue(Array.isArray(cryptex.hops), 'OS cryptex link hops are missing');
  for (const hop of cryptex.hops) {
    exactKeys(hop, ['path','target'], 'OS cryptex link hop');
    requireValue(fs.lstatSync(absolute(hop.path, 'OS cryptex link hop')).isSymbolicLink() && fs.readlinkSync(hop.path) === hop.target,
      'OS cryptex link hop changed');
  }
  if (cryptex.state === 'absent') {
    exactKeys(cryptex, ['state','path','hops'], 'absent OS cryptex copy');
    requireValue(!present(absolute(cryptex.path, 'OS cryptex copy')), 'the OS cryptex copy appeared');
    return;
  }
  exactKeys(cryptex, [...fields, 'link_path', 'hops'], 'OS cryptex copy');
  requireValue(cryptex.state === 'present' && fs.realpathSync(absolute(cryptex.link_path, 'OS cryptex name')) === cryptex.path,
    'the OS cryptex copy is not at its bound canonical path');
  fileBytes(cryptex.path, 65536, {sha256:cryptex.sha256, size_bytes:cryptex.size_bytes, mode:cryptex.mode}, false);
}

function expectedLabels(host) {
  // Contract section 10 with P33-AMENDMENT-001 row 13: the labels that the provider's manifest states.
  return {executor:EXECUTOR, contract:CONTRACT, design_revision:DESIGN_REVISION, amendments:AMENDMENTS, profile:PROFILE,
    os:host.labels.os, node:host.labels.node, python_inventory_sha256:host.python.inventory_sha256,
    git:{path:host.git.path, sha256:host.git.sha256}, run_kind:'qualifying', boundary:'real'};
}

function reportLabels(envelope) {
  // The approved manifest's labels for the result; verifyBootstrap checks them against HOST before any reader import.
  try {
    const labels = strictJSON(envelope.manifestBytes, 'manifest').labels;
    return labels !== null && typeof labels === 'object' && !Array.isArray(labels) ? labels : null;
  } catch (error) { return null; }
}

function verifyInspection(descriptor, argv, environment) {
  const receipt = boundJSON(descriptor, 8 * 1024 * 1024);
  exactKeys(receipt, ['schema','contract','design_revision','amendments','argv','environment','timeout_ms','started_at_utc',
    'finished_at_utc','process','stdout','stderr'], 'inspection receipt');
  requireValue(receipt.schema === 'ontokin.current-host-readback-inspection/0.2.0' && receipt.timeout_ms === 5000 &&
    receipt.contract === CONTRACT && receipt.design_revision === DESIGN_REVISION && stable(receipt.amendments) === stable(AMENDMENTS),
    'inspection schema/deadline differs');
  same(receipt.argv, argv, 'inspection argv'); same(receipt.environment, environment, 'inspection environment');
  requireValue(typeof receipt.stdout === 'string' && typeof receipt.stderr === 'string' &&
    Buffer.byteLength(receipt.stdout) + Buffer.byteLength(receipt.stderr) <= 4194304, 'inspection combined streams exceed bound');
  const record = plainObject(receipt.process, 'inspection process');
  same(record.argv, argv, 'inspection process argv'); same(record.environment, environment, 'inspection process environment');
  requireValue(Number.isSafeInteger(record.pid) && record.pid > 0 && record.process_group === record.pid &&
    record.returncode === 0 && record.handles_closed === true && record.error === null &&
    record.cleanup?.passed === true && record.cleanup.process_group_absent === true && record.cleanup.reaped === true,
    'inspection has missing, failed or unknown process evidence');
  requireValue(Number.isFinite(record.start_monotonic) && Number.isFinite(record.end_monotonic) &&
    record.end_monotonic >= record.start_monotonic && (record.end_monotonic - record.start_monotonic) * 1000 <= 5000,
    'inspection elapsed time exceeds bound');
  requireValue(timestamp(receipt.finished_at_utc, 'inspection finish') >= timestamp(receipt.started_at_utc, 'inspection start') &&
    timestamp(receipt.finished_at_utc, 'inspection finish') <= Date.now(), 'inspection wall-clock record is invalid');
  return receipt;
}

function verifyHost(config) {
  const host = boundJSON(config.host, 8 * 1024 * 1024);
  exactKeys(host, HOST_KEYS, 'host');
  requireValue(host.schema === 'ontokin.current-host-readback-host/0.2.0' && host.contract === CONTRACT &&
    host.design_revision === DESIGN_REVISION && stable(host.amendments) === stable(AMENDMENTS) &&
    host.profile === PROFILE && host.executor === EXECUTOR &&
    timestamp(host.observed_at_utc, 'host observation') <= Date.now(), 'invalid host schema/contract/design revision/time');
  // S10: exactly the declared environment, optionally plus __CF_USER_TEXT_ENCODING with HOST's recorded value.
  exactKeys(host.environment, ['declared','cf_user_text_encoding'], 'host environment');
  same(host.environment.declared, ENVIRONMENT, 'host environment');
  const recordedCf = host.environment.cf_user_text_encoding;
  requireValue(recordedCf === null || (typeof recordedCf === 'string' && recordedCf !== ''), 'recorded __CF_USER_TEXT_ENCODING is malformed');
  requireValue(environmentAdmitted({...process.env}, ENVIRONMENT, recordedCf), 'actual Node environment differs');
  // S7: native Darwin arm64 at HOST's kernel release and OS build; the boot is the provider's binding (E19).
  exactKeys(host.platform, ['system','release','version','machine','proc_translated','boot_session_uuid'], 'host platform');
  requireValue(host.platform.system === os.type() && host.platform.system === 'Darwin' &&
    host.platform.release === os.release() && host.platform.machine === os.machine() && host.platform.machine === 'arm64' &&
    host.platform.proc_translated === 0, 'actual host platform differs');
  verifyOsIdentity(host.os);
  exactKeys(host.python, ['launcher','venv','framework','interpreter','selection','inventory','inventory_sha256','packages','records','lock'], 'host Python');
  digest(host.python.inventory_sha256, 'Python installation inventory digest');
  const requirements = fileBytes(path.join(OWN_ROOT, MACOS_LOCK_RELATIVE), 32768).toString('utf8');
  const pins = {};
  for (const raw of requirements.split(/\r?\n/)) {
    const line = raw.trim(); if (!line || line.startsWith('#')) continue;
    const match = /^([A-Za-z0-9][A-Za-z0-9_.-]*)==([A-Za-z0-9][A-Za-z0-9.!+_-]*) --hash=sha256:[0-9a-f]{64}$/.exec(line);
    requireValue(match !== null && !Object.hasOwn(pins, match[1]), 'verification package pin is invalid'); pins[match[1]] = match[2];
  }
  requireValue(Object.keys(pins).length > 0, 'missing verification package pins');
  same(host.python.packages, pins, 'host verification package pins');
  exactKeys(host.runtime, ['directory','executable','version','binding','archive','node_source','layout','macho','install'], 'host runtime');
  requireValue(host.runtime.executable === config.runtime.executable && host.runtime.version === 'v24.22.1' &&
    host.runtime.executable === path.join(host.runtime.directory, 'bin/node'), 'selected Node build differs');
  validateBinding(host.runtime.binding);
  validateBinding(host.runtime.archive, true);
  requireValue(host.runtime.archive.sha256 === NODE_ARCHIVE_SHA && path.basename(host.runtime.archive.path) === NODE_ARCHIVE,
    'retained Node archive identity differs');
  fileBytes(host.runtime.archive.path, host.runtime.archive.size_bytes, host.runtime.archive, false);
  // S1: the running executable, by its bytes, against HOST's pin frozen at preparation.
  requireValue(process.execPath === config.runtime.executable && fs.realpathSync(process.execPath) === config.runtime.executable,
    'actual executable path differs');
  fileBytes(process.execPath, host.runtime.binding.size_bytes, host.runtime.binding, false, true);
  exactKeys(host.git, ['path','sha256','size_bytes','mode','version'], 'host Git');
  requireValue(typeof host.git.version === 'string' && GIT_VERSION_PATTERN.test(host.git.version), 'host Git version is not one version line');
  exactKeys(host.inspections, ['git_version','node_version'], 'host inspections');
  const version = verifyInspection(host.inspections.node_version, [config.runtime.executable, '--version'], ENVIRONMENT);
  requireValue(version.stdout === 'v24.22.1\n' && version.stderr === '', 'observed Node version differs');
  const git = verifyInspection(host.inspections.git_version, [host.git.path, '--version'], GIT_ENVIRONMENT);
  requireValue(git.stdout === host.git.version + '\n' && git.stderr === '', 'observed Git version differs');
  requireValue([version, git].every(receipt => Date.parse(receipt.finished_at_utc) <= Date.parse(host.observed_at_utc)),
    'host observation predates fresh inspection receipts');
  // Contract section 10: HOST's labels name its own bindings and a real boundary.
  same(host.labels, {executor:EXECUTOR, contract:CONTRACT, design_revision:DESIGN_REVISION, amendments:AMENDMENTS,
    profile:PROFILE, os:osLabel(host.os),
    node:{archive:NODE_ARCHIVE, archive_sha256:NODE_ARCHIVE_SHA, executable:host.runtime.binding,
      signature_check:host.runtime.node_source?.content?.signature_check?.status},
    python_inventory_sha256:host.python.inventory_sha256, git:{path:host.git.path, sha256:host.git.sha256},
    run_kind:'host-observation', boundary:'real'}, 'host labels');
  return host;
}

function verifyMethods(config, sourceInventory) {
  const methods = boundJSON(config.methods, 1024 * 1024);
  exactKeys(methods, ['schema','source_test','original_bodies','discovery'], 'methods');
  requireValue(methods.schema === 'ontokin.current-host-readback-methods/0.2.0' &&
    methods.source_test === 'tests/test_static_tray_readback_v01.py', 'wrong method source/schema');
  same(methods.original_bodies, ORIGINAL_BODIES, 'nine original method/helper body identities');
  const discovery = boundJSON(methods.discovery, 8 * 1024 * 1024);
  exactKeys(discovery, ['schema','method_ids','baseline_map'], 'discovery');
  requireValue(discovery.schema === 'ontokin.current-host-readback-discovery/0.2.0' && Array.isArray(discovery.method_ids), 'invalid discovery schema/IDs');
  requireValue(discovery.method_ids.every(id => typeof id === 'string'), 'invalid discovery ID');
  same(discovery.method_ids, [...new Set(discovery.method_ids)].sort(), 'sorted unique discovery IDs');
  requireValue(ORIGINAL_METHOD_IDS.every(id => discovery.method_ids.includes(id)), 'missing original method identity');
  validateBinding(discovery.baseline_map, true);
  const mapRoot = config.parent === null ? OWN_ROOT : config.parent.source_root;
  requireValue(discovery.baseline_map.path === path.join(mapRoot, MAP_RELATIVE), 'baseline map belongs to an unbound source');
  const binding = sourceInventory.files[MAP_RELATIVE];
  same({sha256:discovery.baseline_map.sha256, size_bytes:discovery.baseline_map.size_bytes, mode:discovery.baseline_map.mode}, binding, 'baseline source-map identity');
  fileBytes(discovery.baseline_map.path, binding.size_bytes, discovery.baseline_map, false);
  fileBytes(path.join(OWN_ROOT, MAP_RELATIVE), binding.size_bytes, binding, false);
  return methods;
}

const GENERATED_EXAMPLES = new Set(['examples/visual/demo-data.js','examples/visual/viewer.bundle.js','examples/visual/THREE-LICENSE.txt',
  'examples/agent/workflow.json','examples/agent/repaired.ok','examples/agent/rejected-candidate.ok',
  ...['workflow.json','authoring.ok','rejected-candidate.ok','main.ok','hinges.ok','program.bundle.json','program.files.json'].map(n => 'examples/construction/' + n)]);
function driverInventory(record) {
  exactKeys(record, ['sha256','file_count','files'], 'driver inventory');
  requireValue(Array.isArray(record.files) && record.file_count === record.files.length, 'driver inventory count differs');
  const seen = new Set();
  for (const row of record.files) {
    exactKeys(row, ['path','sha256','bytes'], 'driver inventory row'); relative(row.path);
    requireValue(!seen.has(row.path) && /^sha256:[0-9a-f]{64}$/.test(row.sha256) && Number.isSafeInteger(row.bytes) && row.bytes >= 0,
      'invalid driver file identity'); seen.add(row.path);
  }
  requireValue(record.sha256 === 'sha256:' + sha(Buffer.from(stable(record.files), 'utf8')), 'driver full inventory digest differs');
  const immutable = record.files.filter(row => !GENERATED_EXAMPLES.has(row.path) &&
    !(/^(?:examples\/visual\/|examples\/agent\/|examples\/construction\/)/.test(row.path) && /(?:\.glb|\.export\.json|\.reference\.json)$/.test(row.path)));
  return {files:immutable, sha256:'sha256:' + sha(Buffer.from(stable(immutable), 'utf8')), file_count:immutable.length};
}
function verifyWorkspace(config) {
  if (config.parent === null) return;
  exactKeys(config.parent, ['config','source_root','workspace_binding'], 'derived configuration parent');
  const parent = boundJSON(config.parent.config, 1024 * 1024);
  exactKeys(parent, CONFIG_KEYS, 'parent configuration');
  requireValue(parent.parent === null && parent.source.root === config.parent.source_root && parent.source.root !== OWN_ROOT,
    'invalid or recursively derived parent');
  const expected = structuredClone(parent);
  expected.source.root = OWN_ROOT;
  expected.contract_source.path = path.join(OWN_ROOT, CONTRACT_RELATIVE);
  expected.amendment_adoption.path = path.join(OWN_ROOT, AMENDMENT_ADOPTION_RELATIVE);
  expected.parent = config.parent;
  same(config, expected, 'explicit derived configuration');
  const workspace = boundJSON(config.parent.workspace_binding, 16 * 1024 * 1024);
  exactKeys(workspace, WORKSPACE_KEYS, 'workspace binding');
  requireValue(workspace.schema === 'ontokin.current-host-readback-workspace/0.2.0' && /^[0-9a-f]{32}$/.test(workspace.identity) &&
    workspace.contract === CONTRACT && workspace.design_revision === DESIGN_REVISION &&
    stable(workspace.amendments) === stable(AMENDMENTS), 'invalid workspace schema/identity/design revision');
  same(workspace.parent_config, config.parent.config, 'workspace parent descriptor');
  same(workspace.source_inventory, config.source.inventory, 'workspace source inventory');
  requireValue(workspace.source_root === parent.source.root && workspace.workspace_root === OWN_ROOT &&
    workspace.commit === config.source.commit && workspace.tree === config.source.tree &&
    workspace.provider === path.join(OWN_ROOT, PROVIDER_RELATIVE) && workspace.probe === OWN_PROBE, 'workspace/source relation differs');
  const beforeRecord = boundJSON(workspace.source_before, 32 * 1024 * 1024);
  const afterRecord = boundJSON(workspace.workspace_inventory, 32 * 1024 * 1024);
  same(beforeRecord, afterRecord, 'original complete driver copy inventories');
  const before = driverInventory(beforeRecord);
  const after = driverInventory(afterRecord);
  same(before, after, 'complete immutable workspace copy');
  requireValue(workspace.immutable_inventory_sha256 === before.sha256, 'workspace immutable digest differs');
  for (const row of after.files) {
    const target = path.join(OWN_ROOT, row.path);
    requireValue(fileBytes(target, row.bytes, null, false, true) === row.sha256.slice(7), 'actual copied immutable source differs');
  }
}

function approvedEnvelope(args) {
  requireSelection(args.length === 4 && args[0] === '--expected-config-sha256' && args[2] === '--job',
    'expected exactly --expected-config-sha256 DIGEST --job FILE');
  const expectedDigest = args[1];
  requireSelection(typeof expectedDigest === 'string' && SHA_PATTERN.test(expectedDigest),
    'externally selected configuration digest is not a lowercase SHA-256');
  const jobPath = absolute(args[3], 'job');
  const job = strictJSON(fileBytes(jobPath, 32768), 'job');
  exactKeys(job, JOB_KEYS, 'job');
  digest(job.supplemental_manifest_sha256, 'job manifest digest');
  digest(job.artifact_sha256, 'job GLB digest'); digest(job.audit_sha256, 'job audit digest');
  const manifestBytes = fileBytes(absolute(job.manifest, 'manifest'), 1024 * 1024);
  requireValue(sha(manifestBytes) === job.supplemental_manifest_sha256, 'job manifest bytes differ');
  const manifest = strictJSON(manifestBytes, 'manifest');
  exactKeys(manifest.selection, ['path','sha256'], 'manifest selection');
  requireSelection(manifest.selection.sha256 === expectedDigest, 'manifest digest is not external approval');
  const configPath = absolute(manifest.selection.path, 'configuration');
  const configBytes = fileBytes(configPath, 1024 * 1024);
  requireSelection(sha(configBytes) === expectedDigest, 'configuration is not approved by the external digest');
  const config = strictJSON(configBytes, 'configuration');
  exactKeys(config, CONFIG_KEYS, 'configuration');
  requireValue(config.schema === CONFIG_SCHEMA && config.contract === CONTRACT, 'wrong configuration contract/schema');
  const outputRoot = canonicalDirectory(config.evidence_root);
  requireValue(outputRoot !== OWN_ROOT && !outputRoot.startsWith(OWN_ROOT + '/'), 'evidence is not external');
  const cohort = inside(canonicalDirectory(manifest.cohort_root), outputRoot, 'cohort');
  const routes = {'CPU-Q01-positive':['Q01','Q01-positive'], 'CPU-Q03-positive':['Q03','Q03-positive'],
    'CPU-Q01-changed-reference':['Q01','Q01-changed-reference']};
  requireValue(Object.hasOwn(routes, job.slot), 'job is not an admitted synthetic CPU case');
  const [expectedCase, label] = routes[job.slot], stage = path.join(cohort, label);
  canonicalDirectory(stage);
  requireValue(job.case === expectedCase && job.input_lock_sha256 === 'CPU-ONLY-SYNTHETIC-NOT-NATIVE' &&
    jobPath === path.join(stage, 'job.json') && process.cwd() === stage &&
    job.artifact === path.join(stage, 'synthetic.glb') && job.audit === path.join(stage, 'synthetic-audit.json') &&
    job.result === path.join(stage, 'probe.json') && path.dirname(job.manifest) === cohort && !present(job.result),
    'job paths, case, output freshness or actual stage differ');
  return {expectedDigest, configPath, config, jobPath, job, manifestBytes, stage};
}

function verifyBootstrap(envelope, manifest) {
  const {config, expectedDigest} = envelope;
  requireSelection(sha(fileBytes(envelope.configPath, 1024 * 1024)) === expectedDigest, 'configuration changed after selection');
  exactKeys(manifest, MANIFEST_KEYS, 'manifest');
  requireValue(manifest.schema === MANIFEST_SCHEMA && manifest.contract === CONTRACT && manifest.profile === 'ontokin.static-tray/0.1.0' &&
    manifest.scope === 'Three original synthetic CPU cases only; twelve native slots are structural, never execution authority',
    'manifest schema/profile/scope differs');
  requireSelection(stable(manifest.selection) === stable({path:envelope.configPath, sha256:expectedDigest}),
    'manifest approval selection differs');
  for (const field of ['source','host','methods','dependencies']) same(manifest[field], config[field], 'manifest ' + field);
  same(manifest.limits, LIMITS, 'manifest limits'); same(manifest.environment, ENVIRONMENT, 'manifest environment');
  same(manifest.validator_options, VALIDATOR_OPTIONS, 'validator options'); same(manifest.three_options, THREE_OPTIONS, 'Three options');
  exactKeys(config.runtime, ['executable','version'], 'configured runtime');
  requireValue(config.runtime.version === 'v24.22.1', 'unsupported configured Node version');
  const sourceInventory = verifySource(config);
  verifyWorkspace(config);
  const dependencies = verifyDependencies(config, sourceInventory), host = verifyHost(config);
  verifyMethods(config, sourceInventory);
  const expectedFiles = {};
  for (const [rel, binding] of Object.entries(dependencies.files)) expectedFiles[path.join(config.dependencies.root, rel)] = binding;
  for (const rel of [PROVIDER_RELATIVE, PROBE_RELATIVE]) expectedFiles[path.join(OWN_ROOT, rel)] = sourceInventory.files[rel];
  same(manifest.files, expectedFiles, 'manifest complete executable-file bindings');
  same(manifest.runtime, {executable:config.runtime.executable, version:'v24.22.1', binding:host.runtime.binding}, 'manifest runtime');
  requireValue(manifest.design_revision === DESIGN_REVISION && stable(manifest.amendments) === stable(AMENDMENTS),
    'manifest design revision or amendments differ');
  same(manifest.labels, expectedLabels(host), 'manifest labels');
  requireValue(manifest.dependencies_root === config.dependencies.root && manifest.probe === OWN_PROBE &&
    manifest.validator_version === '2.0.0-dev.3.10' && manifest.three_version === '0.186.1', 'manifest runtime/dependency identity differs');
  const roles = {validator_entry:'validator/package/index.js', three_package:'indexer-view/three/package.json',
    three_entry:'indexer-view/three/build/three.webgpu.js', gltf_loader_entry:'indexer-view/three/examples/jsm/loaders/GLTFLoader.js',
    module_loader:'tools/three_loader.mjs'};
  for (const [role, rel] of Object.entries(roles)) {
    requireValue(manifest[role] === path.join(config.dependencies.root, rel) && Object.hasOwn(manifest.files, manifest[role]), 'unbound executable role: ' + role);
  }
  same(process.execArgv, [...NODE_FLAGS, '--experimental-loader', manifest.module_loader], 'actual Node flags/loader');
  requireValue(process.argv[0] === config.runtime.executable && process.argv[1] === OWN_PROBE, 'actual process argv source differs');
  requireValue(manifest.schedule_root === path.join(manifest.cohort_root, 'unused-native-schedule') && !present(manifest.schedule_root), 'native schedule exists or differs');
  const controlsPath = 'docs/engineering/static-tray-mapping-c198/CONTROLS.json';
  const controls = strictJSON(fileBytes(path.join(OWN_ROOT, controlsPath), 1024 * 1024, sourceInventory.files[controlsPath]), 'original controls');
  const originalSlots = controls.future_qualification_native_slots;
  requireValue(Array.isArray(originalSlots) && originalSlots.length === 12 && Array.isArray(manifest.slots) && manifest.slots.length === 12, 'original twelve structural slots differ');
  for (let i = 0; i < originalSlots.length; i++) {
    const slot = originalSlots[i], row = manifest.slots[i];
    exactKeys(row, ['slot','case','route','maximum_starts','stage','result','argv'], 'manifest slot');
    const stage = path.join(manifest.schedule_root, 'external-readback', slot.slot);
    const argv = [config.runtime.executable, ...NODE_FLAGS, '--experimental-loader', manifest.module_loader, OWN_PROBE,
      '--expected-config-sha256', expectedDigest, '--job', path.join(stage, 'job.json')];
    same(row, {slot:slot.slot, case:slot.case, route:slot.route, maximum_starts:slot.maximum_starts,
      stage, result:path.join(stage, 'result.json'), argv}, 'exact ordered manifest slot');
  }
  const actualArgv = [process.execPath, ...process.execArgv, ...process.argv.slice(1)];
  same(actualArgv, [...manifest.slots[0].argv.slice(0, -1), envelope.jobPath], 'actual checker argv');
}

const args = process.argv.slice(2);
const envelope = approvedEnvelope(args);
const job = envelope.job;
const report = { schema: 'ontokin.current-host-readback-result/0.2.0', contract: CONTRACT, design_revision: DESIGN_REVISION,
  amendments: AMENDMENTS, labels: reportLabels(envelope), passed: false,
  slot: job.slot, case: job.case, input_lock_sha256: job.input_lock_sha256,
  supplemental_manifest_sha256: job.supplemental_manifest_sha256,
  artifact_sha256: job.artifact_sha256, audit_sha256: job.audit_sha256,
  node: process.version, native_starts: 0, exports: 0,
  scope: 'Khronos format validation and Three.js CPU importer readback; no browser, GPU, simulation or render claim' };
try {
  if (process.version !== 'v24.22.1') throw Error('Node runtime version differs from the selected executable');
  const manifestBytes = readBound(job.manifest, 1024 * 1024);
  if (sha(manifestBytes) !== job.supplemental_manifest_sha256) throw Error('Supplemental manifest identity differs');
  const manifest = strictJSON(manifestBytes, 'manifest');
  if (manifest.schema !== 'ontokin.current-host-readback-lock/0.2.0') throw Error('Wrong supplemental manifest');
  verifyBootstrap(envelope, manifest);
  const bytes = readBound(job.artifact, 8 * 1024 * 1024);
  const auditBytes = readBound(job.audit, 4 * 1024 * 1024);
  if (sha(bytes) !== job.artifact_sha256 || sha(auditBytes) !== job.audit_sha256) throw Error('Actual input identity differs');
  const audit = JSON.parse(auditBytes);
  if (audit.passed !== true || audit.artifact_sha256 !== sha(bytes) || audit.case !== job.case) throw Error('Independent passed audit does not bind this actual GLB');

  // No external fetch is an admitted part of this finite static delivery.
  globalThis.fetch = async () => { throw Error('External resource fetch is forbidden'); };
  const require = createRequire(import.meta.url);
  const validator = require(manifest.validator_entry);
  if (validator.version() !== '2.0.0-dev.3.10') throw Error('Khronos validator version differs');
  const khronos = await validator.validateBytes(new Uint8Array(bytes), {
    uri: 'final.glb', format: 'glb', writeTimestamp: false, maxIssues: 1000,
    externalResourceFunction: async () => { throw Error('External resources are forbidden'); }
  });
  report.khronos = { version: validator.version(), passed: khronos.issues.numErrors === 0 && khronos.issues.numWarnings === 0 && !khronos.issues.truncated,
    report: khronos };
  if (!report.khronos.passed) throw Error('Khronos validation reported an error, warning or truncated result');

  const THREE = await import(pathToFileURL(manifest.three_entry).href);
  const { GLTFLoader } = await import(pathToFileURL(manifest.gltf_loader_entry).href);
  const packageInfo = JSON.parse(readBound(manifest.three_package, 32768));
  if (packageInfo.version !== '0.186.1' || THREE.REVISION !== '186') throw Error('Three.js dependency version differs');
  const manager = new THREE.LoadingManager();
  manager.setURLModifier(() => { throw Error('External Three.js resource resolution is forbidden'); });
  const gltf = await new GLTFLoader(manager).parseAsync(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength), '');
  if (gltf.scenes.length !== 1 || gltf.animations.length || gltf.cameras.length) throw Error('Unexpected imported scenes, animation or cameras');
  gltf.scene.updateMatrixWorld(true);
  const nodes = {}, objects = [], findings = [], measurements = [];
  const exact = (id, field, actual, expected) => {
    if (stable(actual) !== stable(expected)) findings.push({ semantic_id: id, field, actual, expected });
  };
  const near = (id, field, actual, expected, threshold) => {
    const difference = Math.abs(actual - expected);
    const passed = Number.isFinite(actual) && Number.isFinite(expected) && difference <= threshold;
    measurements.push({ semantic_id: id, field, actual, expected, difference, threshold, passed });
    if (!passed) findings.push({ semantic_id: id, field, actual, expected, difference, threshold });
  };
  const idOf = object => Array.isArray(object.userData?.semantic_id) ? object.userData.semantic_id.join('/') : null;
  gltf.scene.traverse(object => {
    if (object === gltf.scene) return;
    const id = idOf(object);
    if (!id || nodes[id]) throw Error('Unbound or duplicate Three.js object identity');
    nodes[id] = object;
    objects.push(id);
  });
  exact('', 'node_identity_inventory', Object.keys(nodes).sort(), Object.keys(audit.nodes).sort());
  exact('', 'node_count', objects.length, 14);
  let meshes = 0;
  const retained = {};
  for (const id of objects.sort()) {
    const object = nodes[id], reference = audit.nodes[id];
    if (!reference) continue;
    if (object.isLight || object.isCamera || object.isSkinnedMesh || object.morphTargetInfluences?.length) throw Error('Unsupported Three.js object');
    const extras = { ...object.userData };
    const originalName = extras.name;
    delete extras.name;
    exact(id, 'original_name', originalName, id);
    exact(id, 'semantic_role_relationships', extras, reference.extras);
    exact(id, 'children', object.children.map(idOf).sort(), reference.children.slice().sort());
    exact(id, 'parent', object.parent === gltf.scene ? null : idOf(object.parent), reference.extras.role === 'tray-root' ? null : reference.extras.owner_id.join('/'));
    const worldMatrix = matrixRows(object.matrixWorld);
    for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) near(id, `matrix_${i}_${j}`, worldMatrix[i][j], reference.world_matrix[i][j], j === 3 && i < 3 ? 0.000005 : 0.000001);
    const data = retained[id] = { original_name: originalName, importer_name: object.name, extras, world_matrix: worldMatrix,
      children: object.children.map(idOf).sort(), parent: object.parent === gltf.scene ? null : idOf(object.parent) };
    if (!reference.world_vertices) {
      exact(id, 'empty_root', Boolean(object.isMesh), false);
      continue;
    }
    meshes++;
    if (!object.isMesh || Array.isArray(object.material)) throw Error('Expected one mesh and material per tray part');
    const geometry = object.geometry, position = geometry.getAttribute('position'), normal = geometry.getAttribute('normal'), index = geometry.getIndex();
    if (!position || !normal || !index || position.count > 4096 || normal.count !== position.count || index.count !== 36) throw Error('Unsupported imported vertex/index layout');
    exact(id, 'vertex_count', position.count, reference.world_vertices.length);
    const positions = [], normals = [], vertices = [];
    for (let i = 0; i < position.count; i++) {
      const p = [position.getX(i), position.getY(i), position.getZ(i)], n = [normal.getX(i), normal.getY(i), normal.getZ(i)];
      if (!finite(p) || !finite(n)) throw Error('Nonfinite imported geometry');
      const world = new THREE.Vector3(...p).applyMatrix4(object.matrixWorld).toArray();
      positions.push(p); normals.push(n); vertices.push(world);
      for (let axis = 0; axis < 3; axis++) {
        near(id, `world_vertex_${i}_${axis}`, world[axis], reference.world_vertices[i][axis], 0.000005);
        near(id, `normal_${i}_${axis}`, n[axis], reference.normals[i][axis], 0.000001);
      }
    }
    const indices = Array.from({ length: index.count }, (_, i) => index.getX(i));
    exact(id, 'actual_triangle_indices', indices, reference.indices);
    const material = { name: object.material.name, baseColorFactor: [...object.material.color.toArray(), object.material.opacity],
      metallicFactor: object.material.metalness, roughnessFactor: object.material.roughness,
      alphaMode: object.material.transparent ? 'BLEND' : object.material.alphaTest > 0 ? 'MASK' : 'OPAQUE',
      doubleSided: object.material.side === THREE.DoubleSide };
    exact(id, 'material', material, reference.material);
    for (const name of ['map', 'normalMap', 'roughnessMap', 'metalnessMap', 'alphaMap', 'emissiveMap', 'aoMap']) if (object.material[name]) throw Error('Unexpected imported texture');
    const bounds = [0, 1].map(upper => [0, 1, 2].map(axis => (upper ? Math.max : Math.min)(...vertices.map(v => v[axis]))));
    const expectedBounds = [0, 1].map(upper => [0, 1, 2].map(axis => (upper ? Math.max : Math.min)(...reference.world_vertices.map(v => v[axis]))));
    for (let axis = 0; axis < 3; axis++) {
      near(id, `world_min_${axis}`, bounds[0][axis], expectedBounds[0][axis], 0.000005);
      near(id, `world_max_${axis}`, bounds[1][axis], expectedBounds[1][axis], 0.000005);
      near(id, `world_size_${axis}`, bounds[1][axis] - bounds[0][axis], expectedBounds[1][axis] - expectedBounds[0][axis], 0.000005);
    }
    Object.assign(data, { positions, normals, world_vertices: vertices, indices, material, world_bounds: bounds });
  }
  exact('', 'mesh_count', meshes, 12);
  findings.sort((a, b) => a.semantic_id.localeCompare(b.semantic_id) || a.field.localeCompare(b.field));
  report.three = { version: packageInfo.version, revision: THREE.REVISION, passed: findings.length === 0,
    node_count: objects.length, mesh_count: meshes, animations: gltf.animations.length, findings, measurements, nodes: retained,
    position_tolerance_m: 0.000005, matrix_tolerance: 0.000001,
    naming: 'Three.js sanitizes Object3D.name; original names and semantic IDs remain checked without normalization' };
  report.input_preserved = sha(readBound(job.artifact, 8 * 1024 * 1024)) === job.artifact_sha256 && sha(readBound(job.audit, 4 * 1024 * 1024)) === job.audit_sha256;
  report.passed = report.khronos.passed && report.three.passed && report.input_preserved;
} catch (error) { report.error = { code: 'OTRAY-E-DELIVERY', message: String(error.message || error) }; }
output(job.result, report);
console.log(JSON.stringify({ passed: report.passed, slot: job.slot, artifact_sha256: job.artifact_sha256,
  validator: report.khronos?.version, three: report.three?.version }));
process.exitCode = report.passed ? 0 : 1;
