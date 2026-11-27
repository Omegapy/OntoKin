"""W3 freeze review 001, script 04: replay the probe's bootstrap for every frozen probe row, from the source.

It mirrors current_host_readback_v02.mjs at C (approvedEnvelope, verifyBootstrap, verifySource,
verifyDependencies, verifyHost, environmentAdmitted, verifyMethods and the main block up to the first
reader import), reading the row's own fixtures from the freeze (the prepared copies do not exist yet:
each prepared path is mapped to its frozen source by the preparation entries). Node is never started.
For each row it reports the first refusal, as the probe would raise it, under each assumption about
Node's process.env: declared only, or declared plus __CF_USER_TEXT_ENCODING with HOST's value.
Reads only; writes one record into OUT/records.
"""
import hashlib
import json
import os
import re
import stat
import sys
import time
from datetime import datetime

FREEZE = sys.argv[1]
OUT = sys.argv[2]
WT = "<worktree>"
OWN_PROBE = WT + "/prototypes/static_tray_v01/current_host_readback_v02.mjs"
OWN_ROOT = WT
with open(FREEZE, "rb") as f:
    FZ = json.loads(f.read())
PREP = {e["path"]: e for e in FZ["preparation"]["entries"]}

CONTRACT = 'ontokin.current-host-readback/0.2.0'
CONFIG_SCHEMA = 'ontokin.current-host-readback-config/0.2.0'
MANIFEST_SCHEMA = 'ontokin.current-host-readback-lock/0.2.0'
PROVIDER_RELATIVE = 'prototypes/static_tray_v01/current_host_readback_v02.py'
PROBE_RELATIVE = 'prototypes/static_tray_v01/current_host_readback_v02.mjs'
CONTRACT_RELATIVE = 'docs/engineering/localized-repair-c271/macos-contract-design-p31/CONTRACT.md'
MAP_RELATIVE = 'docs/engineering/localized-repair-c271/current-host-p05/mapping/MAP-EVIDENCE.zip'
CONTRACT_SHA = '42db98dc6099ee605b0963f3734f7bff2d68c019ff6c00a0ee97bd753c03fdc9'
PROFILE = 'darwin-arm64-v1'
EXECUTOR = 'macos-arm64-local'
DESIGN_REVISION = 4
AMENDMENTS = ['P33-AMENDMENT-001']
AMENDMENT_ADOPTION_RELATIVE = 'docs/engineering/localized-repair-c271/macos-implementation-p33/ADOPTION-AMENDMENT-001.json'
AMENDMENT_ADOPTION_SHA = '872312ed80a63fbb196c17ace42e786b7fe757b710eff41139b125dfaa507937'
NODE_ARCHIVE = 'node-v24.22.1-darwin-arm64.tar.gz'
NODE_ARCHIVE_SHA = '89c682593d76cd44233fa53b1563264e7de9cbb189cad169135c5b4fadfbc0a7'
DEPENDENCY_ARCHIVE_SHA = 'b1e54a6cfef133f7004b1988c90bc718fc954409843c2bcac3772d42e904a0c9'
NODE_FLAGS = ['--no-addons', '--max-old-space-size=256']
ENVIRONMENT = {"PATH": '/usr/bin:/bin', "LANG": 'C.UTF-8', "LC_ALL": 'C.UTF-8', "TZ": 'UTC', "UV_THREADPOOL_SIZE": '2'}
LIMITS = {"maximum_checks": 12, "host_ms": 30000, "child_work_ms": 28000, "cleanup_ms": 2000,
          "glb_bytes": 8388608, "result_bytes": 4194304, "log_bytes": 4194304}
VALIDATOR_OPTIONS = {"format": 'glb', "writeTimestamp": False, "maxIssues": 1000,
                     "allowed_errors": 0, "allowed_warnings": 0, "ignoredIssues": [], "external_resources": 'rejected'}
THREE_OPTIONS = {"position_tolerance_m": 0.000005, "matrix_tolerance": 0.000001,
                 "node_count": 14, "mesh_count": 12, "animation_count": 0, "external_resources": 'rejected'}
SOURCE_TREES = ['ontokin', 'tests', 'prototypes/static_tray_v01', 'tools/static_tray_reader_v01']
SOURCE_OPTIONAL = ['prototypes/__init__.py', 'tools/__init__.py', 'tests/__init__.py']
SOURCE_REQUIRED = ['tools/check_local.py', 'tools/prepare_current_host_readback.py', 'tools/storage_identity.py',
                   'tools/force-agent-verification-requirements.txt', 'tools/native-reader-verification-linux-cp312.lock',
                   'tools/native-reader-verification-macos-arm64-cp312.lock', 'pyproject.toml',
                   'docs/engineering/static-tray-mapping-c198/CONTROLS.json',
                   'docs/engineering/static-tray-qualification-c199/EXTERNAL-INPUTS.json',
                   'docs/engineering/localized-repair-c271/current-host-p05/CONTRACT.md',
                   'docs/engineering/localized-repair-c271/current-host-p05/CONTRACT.json',
                   'docs/engineering/localized-repair-c271/current-host-p05/ADOPTION.json', MAP_RELATIVE,
                   CONTRACT_RELATIVE, 'docs/engineering/localized-repair-c271/macos-contract-design-p31/CONTRACT.json',
                   'docs/engineering/localized-repair-c271/macos-contract-design-p31/ADOPTION.json']
CONFIG_KEYS = ['schema', 'contract', 'contract_source', 'amendment_adoption', 'source', 'host', 'dependencies', 'runtime', 'methods', 'evidence_root', 'parent']
MANIFEST_KEYS = ['schema', 'contract', 'design_revision', 'amendments', 'labels', 'profile', 'schedule_root', 'cohort_root', 'dependencies_root', 'scope', 'limits',
                 'environment', 'files', 'runtime', 'validator_version', 'three_version', 'validator_entry', 'three_package', 'three_entry',
                 'gltf_loader_entry', 'module_loader', 'probe', 'validator_options', 'three_options', 'slots', 'selection', 'source', 'host', 'methods', 'dependencies']
HOST_KEYS = ['schema', 'contract', 'design_revision', 'amendments', 'profile', 'executor', 'observed_at_utc', 'plan', 'observer',
             'platform', 'os', 'environment', 'python', 'runtime', 'git', 'dependencies', 'source', 'inspections', 'starts', 'labels', 'claims']
MACOS_LOCK_RELATIVE = 'tools/native-reader-verification-macos-arm64-cp312.lock'
SYSTEM_VERSION_PATH = '/System/Library/CoreServices/SystemVersion.plist'
CF_NAME = '__CF_USER_TEXT_ENCODING'
GIT_ENVIRONMENT = dict(ENVIRONMENT, GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null', GIT_TERMINAL_PROMPT='0',
                       GIT_ATTR_NOSYSTEM='1', GIT_OPTIONAL_LOCKS='0', GIT_NO_REPLACE_OBJECTS='1')
GIT_VERSION_PATTERN = re.compile(r'^git version [\x20-\x7e]{1,200}$')
JOB_KEYS = ['slot', 'case', 'manifest', 'supplemental_manifest_sha256', 'input_lock_sha256', 'artifact', 'artifact_sha256', 'audit', 'audit_sha256', 'result']
SHA_PATTERN = re.compile(r'^[0-9a-f]{64}$')
GIT_PATTERN = re.compile(r'^(?:[0-9a-f]{40}|[0-9a-f]{64})$')
ORIGINAL_BODIES = {
    'ReadbackCoordinatorSeams.run_seam': '2f39cde2f0f4a18eb54b003e2628b22c47d49495d862d25e38223b5a056817a5',
    'ReadbackCoordinatorSeams.test_result_write_failure_leaves_predecessor_gate_blocked': '222b654a8da505965f0821be4e7b61eefeb1a5f12e767c72e6123feba909f06d',
    'ReadbackCoordinatorSeams.test_host_alarm_cannot_interrupt_supervisor_cleanup': '29665028886624307beacb4debb33b8582f91bf60951149c0160ae957ed68f98',
    'ReadbackCoordinatorSeams.test_success_finalization_uses_remaining_outer_alarm': 'f4a5d8242e91d3792039b94f2f75c8002b7cc5e1b432ce3cc91d46d65d3f1f55',
    'ReadbackCoordinatorSeams.test_uncertain_marker_removal_recreates_pending': '5e3041a6f1e57db4c4c03e97927e1aa88c6d8dfe2b431e71b38319e3851b75bc',
    'ReadbackCPUControls.check_case': '53a03c60a7473af90ba88f2fddf225713036d417cf3c13a0c1e8a6a3105946a4',
    'ReadbackCPUControls.test_q01_actual_synthetic_meshes_load_in_both_libraries': 'e7793b38ebedd196c228ce6841642c2546c8ef1f5db552b1b1f824a30087fd34',
    'ReadbackCPUControls.test_q03_actual_synthetic_rotations_load_in_both_libraries': 'e09a9c173e4879558da9206549f085a840639a314c22e525fccabc498c7e3dd4',
    'ReadbackCPUControls.test_three_rejects_changed_synthetic_reference': '8b2de031c533e1308efeef130047b0a2b4fcfc1cb6cd2f576e7b3ef832ec05d9'}
ORIGINAL_METHOD_IDS = sorted('test_static_tray_readback_v01.' + n for n in ORIGINAL_BODIES if '.test_' in n)


class ProbeError(Exception):
    pass


def require_value(cond, msg):
    if not cond:
        raise ProbeError('Current-host binding: ' + msg)


def require_selection(cond, msg):
    if not cond:
        raise ProbeError('CH-SELECTION: ' + msg)


def plain_dict(v, name):
    require_value(isinstance(v, dict), name + ' must be an object')
    return v


def exact_keys(v, keys, name):
    plain_dict(v, name)
    require_value(sorted(v.keys()) == sorted(keys), name + ' has unknown, missing or extra fields')


def jsame(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a == b
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(jsame(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return set(a) == set(b) and all(jsame(a[k], b[k]) for k in a)
    return type(a) is type(b) and a == b


def same(a, b, name):
    require_value(jsame(a, b), name + ' differs')


def digest(v, name):
    require_value(isinstance(v, str) and SHA_PATTERN.match(v) is not None, name + ' is not a lowercase SHA-256')
    return v


def parse_ts(v):
    try:
        return datetime.fromisoformat(v.replace('Z', '+00:00')).timestamp() * 1000
    except Exception:
        return None


def timestamp(v, name):
    ok = isinstance(v, str) and re.search(r'(?:Z|[+-][0-9]{2}:[0-9]{2})$', v) is not None and parse_ts(v) is not None
    require_value(ok, name + ' is not a zoned timestamp')
    return parse_ts(v)


def absolute(v, name):
    require_value(isinstance(v, str) and len(v) > 1 and '\0' not in v and v.startswith('/') and os.path.normpath(v) == v,
                  name + ' is not an absolute normalized path')
    return v


def relative(v):
    require_value(isinstance(v, str) and len(v) > 0 and '\\' not in v and '\0' not in v and not v.startswith('/')
                  and not any(p in ('', '.', '..') for p in v.split('/')), 'unsafe relative path')
    return v


def inside(v, root, name):
    absolute(v, name)
    absolute(root, name + ' root')
    require_value(v.startswith(root + '/'), name + ' escapes its bound parent')
    return v


# The prepared filesystem: prepared directories exist (with their frozen entries), prepared files are their frozen
# sources; everything else is the real filesystem. Before D01 none of the prepared paths exists.
def p_isdir(path):
    if path in PREP:
        return PREP[path]['kind'] == 'directory'
    return os.path.isdir(path) and not os.path.islink(path)


def p_present(path):
    if path in PREP:
        return True
    if path.startswith(FZ['places']['evidence_parent'] + '/s7-001-'):
        return False  # every other S7 path is absent before its command (checked by P01/D02)
    return os.path.lexists(path)


def p_real(path):
    return PREP[path]['copied_from'] if path in PREP and PREP[path]['kind'] == 'file' else path


def canonical_directory(path):
    absolute(path, 'directory')
    require_value(p_isdir(path) and (path in PREP or os.path.realpath(path) == path),
                  'directory is absent, aliased or unsafe: ' + path)
    return path


def mode_text(m):
    return '0o' + format(m & 0o7777, 'o')


def file_bytes(path, maximum, binding=None, retain=True, reject_hardlink=False):
    absolute(path, 'file path')
    if binding:
        validate_binding(binding, 'path' in binding)
    real = p_real(path)
    st = os.lstat(real)
    require_value(stat.S_ISREG(st.st_mode) and (path in PREP or os.path.realpath(path) == path),
                  'file is not canonical and regular: ' + path)
    require_value(not reject_hardlink or st.st_nlink == 1, 'hardlinked source or dependency: ' + path)
    require_value(st.st_size <= maximum, 'file exceeds its bound: ' + path)
    mode = mode_text(st.st_mode)
    if path in PREP:
        mode = PREP[path]['mode']  # the prepared copy's frozen mode (D02 verifies it)
    if binding:
        require_value(st.st_size == binding['size_bytes'] and mode == binding['mode'], 'file size or mode differs: ' + path)
    with open(real, 'rb') as f:
        data = f.read()
    if binding:
        require_value(hashlib.sha256(data).hexdigest() == binding['sha256'], 'file hash differs: ' + path)
    return data if retain else hashlib.sha256(data).hexdigest()


def validate_binding(b, with_path=False):
    exact_keys(b, ['path', 'sha256', 'size_bytes', 'mode'] if with_path else ['sha256', 'size_bytes', 'mode'], 'file binding')
    digest(b['sha256'], 'file digest')
    require_value(isinstance(b['size_bytes'], int) and not isinstance(b['size_bytes'], bool) and b['size_bytes'] >= 0, 'file size is invalid')
    require_value(isinstance(b['mode'], str) and re.match(r'^0o[0-7]{3,4}$', b['mode']) is not None, 'file mode is invalid')
    if with_path:
        absolute(b['path'], 'descriptor path')


def strict_json(data, name):
    def pairs(items):
        out = {}
        for k, v in items:
            require_value(k not in out, 'duplicate JSON member in ' + name)
            out[k] = v
        return out
    try:
        return json.loads(data.decode('utf-8'), object_pairs_hook=pairs)
    except ProbeError:
        raise
    except Exception as exc:
        raise ProbeError('Current-host binding: invalid JSON in ' + name + ': ' + str(exc))


def bound_json(desc, maximum):
    validate_binding(desc, True)
    return strict_json(file_bytes(desc['path'], maximum, desc), desc['path'])


def walk_files(root, rel_root='', reject_cache=False):
    canonical_directory(os.path.join(root, rel_root) if rel_root else root)
    files, dirs = {}, {}

    def walk(name):
        directory = os.path.join(root, name) if name else root
        for child in sorted(os.listdir(directory)):
            rel = name + '/' + child if name else child
            relative(rel)
            require_value(not reject_cache or ('__pycache__' not in rel.split('/') and not re.search(r'\.py[co]$', rel)), 'unbound source bytecode/cache')
            fn = os.path.join(root, rel)
            info = os.lstat(fn)
            require_value(not stat.S_ISLNK(info.st_mode), 'symlink in complete file inventory: ' + fn)
            if stat.S_ISDIR(info.st_mode):
                dirs[rel] = mode_text(info.st_mode)
                walk(rel)
            else:
                require_value(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, 'nonregular or hardlinked inventory input')
                files[rel] = fn
    walk(rel_root)
    return files, dirs


def verify_source(config):
    exact_keys(config['source'], ['root', 'commit', 'tree', 'inventory'], 'source')
    require_value(config['source']['root'] == OWN_ROOT and os.path.realpath(OWN_ROOT) == OWN_ROOT, 'probe is outside its bound checkout')
    require_value(GIT_PATTERN.match(config['source']['commit']) and GIT_PATTERN.match(config['source']['tree'])
                  and len(config['source']['commit']) == len(config['source']['tree']), 'invalid source commit/tree identity')
    inv = bound_json(config['source']['inventory'], 16 * 1024 * 1024)
    exact_keys(inv, ['schema', 'files'], 'source inventory')
    require_value(inv['schema'] == 'ontokin.current-host-readback-source/0.2.0', 'wrong source inventory schema')
    actual = {}
    for tree in SOURCE_TREES:
        actual.update(walk_files(OWN_ROOT, tree, reject_cache=True)[0])
    for rel in SOURCE_REQUIRED + [p for p in SOURCE_OPTIONAL if os.path.lexists(os.path.join(OWN_ROOT, p))]:
        actual[rel] = os.path.join(OWN_ROOT, rel)
    same(sorted(actual), sorted(inv['files']), 'complete source file inventory')
    for rel, b in inv['files'].items():
        relative(rel)
        validate_binding(b)
        file_bytes(actual[rel], b['size_bytes'], b, False, True)
    validate_binding(config['contract_source'], True)
    require_value(config['contract_source']['path'] == os.path.join(OWN_ROOT, CONTRACT_RELATIVE) and config['contract_source']['sha256'] == CONTRACT_SHA, 'adopted contract source differs')
    file_bytes(config['contract_source']['path'], 1024 * 1024, config['contract_source'], False, True)
    same({k: config['contract_source'][k] for k in ('sha256', 'size_bytes', 'mode')}, inv['files'][CONTRACT_RELATIVE], 'contract source inventory binding')
    validate_binding(config['amendment_adoption'], True)
    require_value(config['amendment_adoption']['path'] == os.path.join(OWN_ROOT, AMENDMENT_ADOPTION_RELATIVE) and config['amendment_adoption']['sha256'] == AMENDMENT_ADOPTION_SHA, 'adopted amendment record differs')
    file_bytes(config['amendment_adoption']['path'], 1024 * 1024, config['amendment_adoption'], False, True)
    return inv


def verify_dependencies(config, src):
    exact_keys(config['dependencies'], ['root', 'inventory'], 'dependencies')
    root = canonical_directory(config['dependencies']['root'])
    require_value(root != OWN_ROOT and not root.startswith(OWN_ROOT + '/'), 'dependencies are not external')
    inv = bound_json(config['dependencies']['inventory'], 1024 * 1024)
    exact_keys(inv, ['schema', 'files', 'directories', 'archive'], 'dependency inventory')
    require_value(inv['schema'] == 'ontokin.current-host-readback-dependencies/0.2.0', 'wrong dependency inventory schema')
    validate_binding(inv['archive'], True)
    require_value(inv['archive']['sha256'] == DEPENDENCY_ARCHIVE_SHA, 'dependency archive identity differs')
    file_bytes(inv['archive']['path'], inv['archive']['size_bytes'], inv['archive'], False)
    hp = 'docs/engineering/static-tray-qualification-c199/EXTERNAL-INPUTS.json'
    hist = strict_json(file_bytes(os.path.join(OWN_ROOT, hp), 1024 * 1024, src['files'][hp]), 'historical dependency binding')
    require_value(src['files'][hp]['sha256'] == '21fd6bad8738ed51d4ced8036a0fcde5dd046823f55f71de52b9b81df659ccd5', 'historical dependency manifest changed')
    expected = {}
    for fn, b in hist['files'].items():
        if fn.startswith(hist['dependencies_root'] + '/'):
            expected[fn[len(hist['dependencies_root']) + 1:]] = b
    require_value(len(expected) == 24, 'historical dependency inventory is not exactly 24 files')
    same(sorted(inv['files']), sorted(expected), 'exact retained dependency paths')
    afiles, adirs = walk_files(root)
    same(sorted(afiles), sorted(expected), 'installed dependency files')
    same(adirs, inv['directories'], 'installed dependency directory paths and modes')
    necessary = set()
    for rel, b in inv['files'].items():
        relative(rel)
        validate_binding(b)
        require_value(b['sha256'] == expected[rel]['sha256'] and b['size_bytes'] == expected[rel]['size_bytes'], 'retained dependency bytes changed')
        file_bytes(os.path.join(root, rel), b['size_bytes'], b, False, True)
        parent = os.path.dirname(rel)
        while parent not in ('', '.'):
            necessary.add(parent)
            parent = os.path.dirname(parent)
    same(sorted(necessary), sorted(inv['directories']), 'necessary dependency directories')
    for rel, version in (('validator/package/package.json', '2.0.0-dev.3.10'), ('indexer-view/three/package.json', '0.186.1')):
        info = strict_json(file_bytes(os.path.join(root, rel), 32768, inv['files'][rel]), 'dependency package')
        require_value(info['version'] == version, 'dependency package version differs')
    return inv


def environment_admitted(observed, declared, recorded_cf):
    if not isinstance(observed, dict) or not isinstance(declared, dict):
        return False
    if not all(isinstance(k, str) and isinstance(v, str) for k, v in list(observed.items()) + list(declared.items())):
        return False
    if CF_NAME in declared:
        return False
    if observed == declared:
        return True
    return isinstance(recorded_cf, str) and recorded_cf != '' and observed == dict(declared, **{CF_NAME: recorded_cf})


def os_label(identity):
    s, c = identity['system_version'], identity['cryptex']
    return {"product_version": s['product_version'], "product_build_version": s['product_build_version'],
            "product_version_extra": s['product_version_extra'],
            "cryptex": {"state": 'absent'} if c['state'] == 'absent' else {"state": 'present', "product_version": c['product_version'],
                                                                         "product_build_version": c['product_build_version'], "product_version_extra": c['product_version_extra']}}


def verify_os_identity(identity):
    exact_keys(identity, ['system_version', 'cryptex'], 'host OS identity')
    fields = ['state', 'path', 'sha256', 'size_bytes', 'mode', 'product_name', 'product_version', 'product_build_version', 'product_version_extra']
    s = identity['system_version']
    exact_keys(s, fields, 'OS build file')
    require_value(s['state'] == 'present' and s['path'] == SYSTEM_VERSION_PATH, 'OS build file differs')
    file_bytes(s['path'], 65536, {"sha256": s['sha256'], "size_bytes": s['size_bytes'], "mode": s['mode']}, False)
    c = identity['cryptex']
    plain_dict(c, 'OS cryptex copy')
    require_value(isinstance(c.get('hops'), list), 'OS cryptex link hops are missing')
    for hop in c['hops']:
        exact_keys(hop, ['path', 'target'], 'OS cryptex link hop')
        require_value(os.path.islink(absolute(hop['path'], 'OS cryptex link hop')) and os.readlink(hop['path']) == hop['target'], 'OS cryptex link hop changed')
    if c['state'] == 'absent':
        exact_keys(c, ['state', 'path', 'hops'], 'absent OS cryptex copy')
        require_value(not os.path.lexists(absolute(c['path'], 'OS cryptex copy')), 'the OS cryptex copy appeared')
        return
    exact_keys(c, fields + ['link_path', 'hops'], 'OS cryptex copy')
    require_value(c['state'] == 'present' and os.path.realpath(absolute(c['link_path'], 'OS cryptex name')) == c['path'], 'the OS cryptex copy is not at its bound canonical path')
    file_bytes(c['path'], 65536, {"sha256": c['sha256'], "size_bytes": c['size_bytes'], "mode": c['mode']}, False)


def expected_labels(host):
    return {"executor": EXECUTOR, "contract": CONTRACT, "design_revision": DESIGN_REVISION, "amendments": AMENDMENTS, "profile": PROFILE,
            "os": host['labels']['os'], "node": host['labels']['node'], "python_inventory_sha256": host['python']['inventory_sha256'],
            "git": {"path": host['git']['path'], "sha256": host['git']['sha256']}, "run_kind": 'qualifying', "boundary": 'real'}


def verify_inspection(desc, argv, environment):
    r = bound_json(desc, 8 * 1024 * 1024)
    exact_keys(r, ['schema', 'contract', 'design_revision', 'amendments', 'argv', 'environment', 'timeout_ms', 'started_at_utc',
                   'finished_at_utc', 'process', 'stdout', 'stderr'], 'inspection receipt')
    require_value(r['schema'] == 'ontokin.current-host-readback-inspection/0.2.0' and r['timeout_ms'] == 5000 and r['contract'] == CONTRACT
                  and r['design_revision'] == DESIGN_REVISION and r['amendments'] == AMENDMENTS, 'inspection schema/deadline differs')
    same(r['argv'], argv, 'inspection argv')
    same(r['environment'], environment, 'inspection environment')
    require_value(isinstance(r['stdout'], str) and isinstance(r['stderr'], str), 'inspection combined streams exceed bound')
    rec = plain_dict(r['process'], 'inspection process')
    same(rec['argv'], argv, 'inspection process argv')
    same(rec['environment'], environment, 'inspection process environment')
    cl = rec.get('cleanup') or {}
    require_value(isinstance(rec.get('pid'), int) and rec['pid'] > 0 and rec.get('process_group') == rec['pid'] and rec.get('returncode') == 0
                  and rec.get('handles_closed') is True and rec.get('error') is None and cl.get('passed') is True
                  and cl.get('process_group_absent') is True and cl.get('reaped') is True, 'inspection has missing, failed or unknown process evidence')
    require_value(isinstance(rec.get('start_monotonic'), (int, float)) and isinstance(rec.get('end_monotonic'), (int, float))
                  and rec['end_monotonic'] >= rec['start_monotonic'] and (rec['end_monotonic'] - rec['start_monotonic']) * 1000 <= 5000, 'inspection elapsed time exceeds bound')
    fin, sta = timestamp(r['finished_at_utc'], 'inspection finish'), timestamp(r['started_at_utc'], 'inspection start')
    require_value(fin >= sta and fin <= time.time() * 1000, 'inspection wall-clock record is invalid')
    return r


def verify_host(config, observed_env, trace):
    host = bound_json(config['host'], 8 * 1024 * 1024)
    exact_keys(host, HOST_KEYS, 'host')
    require_value(host['schema'] == 'ontokin.current-host-readback-host/0.2.0' and host['contract'] == CONTRACT and host['design_revision'] == DESIGN_REVISION
                  and host['amendments'] == AMENDMENTS and host['profile'] == PROFILE and host['executor'] == EXECUTOR
                  and timestamp(host['observed_at_utc'], 'host observation') <= time.time() * 1000, 'invalid host schema/contract/design revision/time')
    exact_keys(host['environment'], ['declared', 'cf_user_text_encoding'], 'host environment')
    same(host['environment']['declared'], ENVIRONMENT, 'host environment')
    rcf = host['environment']['cf_user_text_encoding']
    require_value(rcf is None or (isinstance(rcf, str) and rcf != ''), 'recorded __CF_USER_TEXT_ENCODING is malformed')
    trace.append('verifyHost: reached the environment check with recorded CF %r' % (rcf,))
    require_value(environment_admitted(observed_env, ENVIRONMENT, rcf), 'actual Node environment differs')
    trace.append('verifyHost: environment admitted')
    exact_keys(host['platform'], ['system', 'release', 'version', 'machine', 'proc_translated', 'boot_session_uuid'], 'host platform')
    un = os.uname()
    require_value(host['platform']['system'] == un.sysname == 'Darwin' and host['platform']['release'] == un.release
                  and host['platform']['machine'] == un.machine == 'arm64' and host['platform']['proc_translated'] == 0, 'actual host platform differs')
    verify_os_identity(host['os'])
    exact_keys(host['python'], ['launcher', 'venv', 'framework', 'interpreter', 'selection', 'inventory', 'inventory_sha256', 'packages', 'records', 'lock'], 'host Python')
    digest(host['python']['inventory_sha256'], 'Python installation inventory digest')
    req = file_bytes(os.path.join(OWN_ROOT, MACOS_LOCK_RELATIVE), 32768).decode('utf-8')
    pins = {}
    for raw in re.split(r'\r?\n', req):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        m = re.match(r'^([A-Za-z0-9][A-Za-z0-9_.-]*)==([A-Za-z0-9][A-Za-z0-9.!+_-]*) --hash=sha256:[0-9a-f]{64}$', line)
        require_value(m is not None and m.group(1) not in pins, 'verification package pin is invalid')
        pins[m.group(1)] = m.group(2)
    require_value(len(pins) > 0, 'missing verification package pins')
    same(host['python']['packages'], pins, 'host verification package pins')
    exact_keys(host['runtime'], ['directory', 'executable', 'version', 'binding', 'archive', 'node_source', 'layout', 'macho', 'install'], 'host runtime')
    require_value(host['runtime']['executable'] == config['runtime']['executable'] and host['runtime']['version'] == 'v24.22.1'
                  and host['runtime']['executable'] == os.path.join(host['runtime']['directory'], 'bin/node'), 'selected Node build differs')
    validate_binding(host['runtime']['binding'])
    validate_binding(host['runtime']['archive'], True)
    require_value(host['runtime']['archive']['sha256'] == NODE_ARCHIVE_SHA and os.path.basename(host['runtime']['archive']['path']) == NODE_ARCHIVE, 'retained Node archive identity differs')
    file_bytes(host['runtime']['archive']['path'], host['runtime']['archive']['size_bytes'], host['runtime']['archive'], False)
    exec_path = config['runtime']['executable']  # process.execPath of the bound Node, as the row's argv[0]
    require_value(os.path.realpath(exec_path) == config['runtime']['executable'], 'actual executable path differs')
    file_bytes(exec_path, host['runtime']['binding']['size_bytes'], host['runtime']['binding'], False, True)
    exact_keys(host['git'], ['path', 'sha256', 'size_bytes', 'mode', 'version'], 'host Git')
    require_value(isinstance(host['git']['version'], str) and GIT_VERSION_PATTERN.match(host['git']['version']), 'host Git version is not one version line')
    exact_keys(host['inspections'], ['git_version', 'node_version'], 'host inspections')
    v = verify_inspection(host['inspections']['node_version'], [config['runtime']['executable'], '--version'], ENVIRONMENT)
    require_value(v['stdout'] == 'v24.22.1\n' and v['stderr'] == '', 'observed Node version differs')
    g = verify_inspection(host['inspections']['git_version'], [host['git']['path'], '--version'], GIT_ENVIRONMENT)
    require_value(g['stdout'] == host['git']['version'] + '\n' and g['stderr'] == '', 'observed Git version differs')
    require_value(all(parse_ts(x['finished_at_utc']) <= parse_ts(host['observed_at_utc']) for x in (v, g)), 'host observation predates fresh inspection receipts')
    sig = ((host['runtime'].get('node_source') or {}).get('content') or {}).get('signature_check') or {}
    same(host['labels'], {"executor": EXECUTOR, "contract": CONTRACT, "design_revision": DESIGN_REVISION, "amendments": AMENDMENTS,
                          "profile": PROFILE, "os": os_label(host['os']),
                          "node": {"archive": NODE_ARCHIVE, "archive_sha256": NODE_ARCHIVE_SHA, "executable": host['runtime']['binding'],
                                   "signature_check": sig.get('status')},
                          "python_inventory_sha256": host['python']['inventory_sha256'], "git": {"path": host['git']['path'], "sha256": host['git']['sha256']},
                          "run_kind": 'host-observation', "boundary": 'real'}, 'host labels')
    return host


def verify_methods(config, src):
    m = bound_json(config['methods'], 1024 * 1024)
    exact_keys(m, ['schema', 'source_test', 'original_bodies', 'discovery'], 'methods')
    require_value(m['schema'] == 'ontokin.current-host-readback-methods/0.2.0' and m['source_test'] == 'tests/test_static_tray_readback_v01.py', 'wrong method source/schema')
    same(m['original_bodies'], ORIGINAL_BODIES, 'nine original method/helper body identities')
    d = bound_json(m['discovery'], 8 * 1024 * 1024)
    exact_keys(d, ['schema', 'method_ids', 'baseline_map'], 'discovery')
    require_value(d['schema'] == 'ontokin.current-host-readback-discovery/0.2.0' and isinstance(d['method_ids'], list), 'invalid discovery schema/IDs')
    same(d['method_ids'], sorted(set(d['method_ids'])), 'sorted unique discovery IDs')
    require_value(all(i in d['method_ids'] for i in ORIGINAL_METHOD_IDS), 'missing original method identity')
    validate_binding(d['baseline_map'], True)
    require_value(d['baseline_map']['path'] == os.path.join(OWN_ROOT, MAP_RELATIVE), 'baseline map belongs to an unbound source')
    b = src['files'][MAP_RELATIVE]
    same({k: d['baseline_map'][k] for k in ('sha256', 'size_bytes', 'mode')}, b, 'baseline source-map identity')
    file_bytes(d['baseline_map']['path'], b['size_bytes'], d['baseline_map'], False)
    return m


def approved_envelope(args, cwd, trace):
    require_selection(len(args) == 4 and args[0] == '--expected-config-sha256' and args[2] == '--job', 'expected exactly --expected-config-sha256 DIGEST --job FILE')
    expected = args[1]
    require_selection(SHA_PATTERN.match(expected) is not None, 'externally selected configuration digest is not a lowercase SHA-256')
    job_path = absolute(args[3], 'job')
    job = strict_json(file_bytes(job_path, 32768), 'job')
    exact_keys(job, JOB_KEYS, 'job')
    digest(job['supplemental_manifest_sha256'], 'job manifest digest')
    digest(job['artifact_sha256'], 'job GLB digest')
    digest(job['audit_sha256'], 'job audit digest')
    mbytes = file_bytes(absolute(job['manifest'], 'manifest'), 1024 * 1024)
    require_value(hashlib.sha256(mbytes).hexdigest() == job['supplemental_manifest_sha256'], 'job manifest bytes differ')
    manifest = strict_json(mbytes, 'manifest')
    exact_keys(manifest['selection'], ['path', 'sha256'], 'manifest selection')
    trace.append('approvedEnvelope: reached the selection check (manifest selection %s..., expected %s...)' % (manifest['selection']['sha256'][:12], expected[:12]))
    require_selection(manifest['selection']['sha256'] == expected, 'manifest digest is not external approval')
    config_path = absolute(manifest['selection']['path'], 'configuration')
    cbytes = file_bytes(config_path, 1024 * 1024)
    require_selection(hashlib.sha256(cbytes).hexdigest() == expected, 'configuration is not approved by the external digest')
    config = strict_json(cbytes, 'configuration')
    exact_keys(config, CONFIG_KEYS, 'configuration')
    trace.append('approvedEnvelope: reached the configuration schema check (schema %r)' % (config.get('schema'),))
    require_value(config['schema'] == CONFIG_SCHEMA and config['contract'] == CONTRACT, 'wrong configuration contract/schema')
    out_root = canonical_directory(config['evidence_root'])
    require_value(out_root != OWN_ROOT and not out_root.startswith(OWN_ROOT + '/'), 'evidence is not external')
    cohort = inside(canonical_directory(manifest['cohort_root']), out_root, 'cohort')
    routes = {'CPU-Q01-positive': ['Q01', 'Q01-positive'], 'CPU-Q03-positive': ['Q03', 'Q03-positive'], 'CPU-Q01-changed-reference': ['Q01', 'Q01-changed-reference']}
    require_value(job['slot'] in routes, 'job is not an admitted synthetic CPU case')
    case, label = routes[job['slot']]
    stage = os.path.join(cohort, label)
    canonical_directory(stage)
    require_value(job['case'] == case and job['input_lock_sha256'] == 'CPU-ONLY-SYNTHETIC-NOT-NATIVE' and job_path == os.path.join(stage, 'job.json')
                  and cwd == stage and job['artifact'] == os.path.join(stage, 'synthetic.glb') and job['audit'] == os.path.join(stage, 'synthetic-audit.json')
                  and job['result'] == os.path.join(stage, 'probe.json') and os.path.dirname(job['manifest']) == cohort and not p_present(job['result']),
                  'job paths, case, output freshness or actual stage differ')
    trace.append('approvedEnvelope: passed')
    return {"expected": expected, "config_path": config_path, "config": config, "job_path": job_path, "job": job, "manifest_bytes": mbytes, "stage": stage}


def verify_bootstrap(env, manifest, exec_argv, argv_tail, observed_env, trace):
    config, expected = env['config'], env['expected']
    require_selection(hashlib.sha256(file_bytes(env['config_path'], 1024 * 1024)).hexdigest() == expected, 'configuration changed after selection')
    exact_keys(manifest, MANIFEST_KEYS, 'manifest')
    require_value(manifest['schema'] == MANIFEST_SCHEMA and manifest['contract'] == CONTRACT and manifest['profile'] == 'ontokin.static-tray/0.1.0'
                  and manifest['scope'] == 'Three original synthetic CPU cases only; twelve native slots are structural, never execution authority', 'manifest schema/profile/scope differs')
    require_selection(jsame(manifest['selection'], {"path": env['config_path'], "sha256": expected}), 'manifest approval selection differs')
    for field in ('source', 'host', 'methods', 'dependencies'):
        same(manifest[field], config[field], 'manifest ' + field)
    same(manifest['limits'], LIMITS, 'manifest limits')
    same(manifest['environment'], ENVIRONMENT, 'manifest environment')
    same(manifest['validator_options'], VALIDATOR_OPTIONS, 'validator options')
    same(manifest['three_options'], THREE_OPTIONS, 'Three options')
    exact_keys(config['runtime'], ['executable', 'version'], 'configured runtime')
    require_value(config['runtime']['version'] == 'v24.22.1', 'unsupported configured Node version')
    trace.append('verifyBootstrap: manifest checks before the source passed')
    src = verify_source(config)
    trace.append('verifySource: passed')
    require_value(config['parent'] is None, 'derived configuration (not replayed)')
    deps = verify_dependencies(config, src)
    trace.append('verifyDependencies: passed')
    host = verify_host(config, observed_env, trace)
    trace.append('verifyHost: passed')
    verify_methods(config, src)
    trace.append('verifyMethods: passed')
    expected_files = {}
    for rel, b in deps['files'].items():
        expected_files[os.path.join(config['dependencies']['root'], rel)] = b
    for rel in (PROVIDER_RELATIVE, PROBE_RELATIVE):
        expected_files[os.path.join(OWN_ROOT, rel)] = src['files'][rel]
    same(manifest['files'], expected_files, 'manifest complete executable-file bindings')
    same(manifest['runtime'], {"executable": config['runtime']['executable'], "version": 'v24.22.1', "binding": host['runtime']['binding']}, 'manifest runtime')
    require_value(manifest['design_revision'] == DESIGN_REVISION and manifest['amendments'] == AMENDMENTS, 'manifest design revision or amendments differ')
    same(manifest['labels'], expected_labels(host), 'manifest labels')
    require_value(manifest['dependencies_root'] == config['dependencies']['root'] and manifest['probe'] == OWN_PROBE
                  and manifest['validator_version'] == '2.0.0-dev.3.10' and manifest['three_version'] == '0.186.1', 'manifest runtime/dependency identity differs')
    roles = {"validator_entry": 'validator/package/index.js', "three_package": 'indexer-view/three/package.json',
             "three_entry": 'indexer-view/three/build/three.webgpu.js', "gltf_loader_entry": 'indexer-view/three/examples/jsm/loaders/GLTFLoader.js',
             "module_loader": 'tools/three_loader.mjs'}
    for role, rel in roles.items():
        require_value(manifest[role] == os.path.join(config['dependencies']['root'], rel) and manifest[role] in manifest['files'], 'unbound executable role: ' + role)
    same(exec_argv, NODE_FLAGS + ['--experimental-loader', manifest['module_loader']], 'actual Node flags/loader')
    require_value(argv_tail[0] == OWN_PROBE, 'actual process argv source differs')
    require_value(manifest['schedule_root'] == os.path.join(manifest['cohort_root'], 'unused-native-schedule') and not p_present(manifest['schedule_root']), 'native schedule exists or differs')
    cp = 'docs/engineering/static-tray-mapping-c198/CONTROLS.json'
    controls = strict_json(file_bytes(os.path.join(OWN_ROOT, cp), 1024 * 1024, src['files'][cp]), 'original controls')
    slots = controls['future_qualification_native_slots']
    require_value(isinstance(slots, list) and len(slots) == 12 and isinstance(manifest['slots'], list) and len(manifest['slots']) == 12, 'original twelve structural slots differ')
    for i, slot in enumerate(slots):
        row = manifest['slots'][i]
        exact_keys(row, ['slot', 'case', 'route', 'maximum_starts', 'stage', 'result', 'argv'], 'manifest slot')
        stg = os.path.join(manifest['schedule_root'], 'external-readback', slot['slot'])
        argv = [config['runtime']['executable']] + NODE_FLAGS + ['--experimental-loader', manifest['module_loader'], OWN_PROBE,
                                                                 '--expected-config-sha256', expected, '--job', os.path.join(stg, 'job.json')]
        same(row, {"slot": slot['slot'], "case": slot['case'], "route": slot['route'], "maximum_starts": slot['maximum_starts'],
                   "stage": stg, "result": os.path.join(stg, 'result.json'), "argv": argv}, 'exact ordered manifest slot')
    actual = [config['runtime']['executable']] + exec_argv + argv_tail
    same(actual, manifest['slots'][0]['argv'][:-1] + [env['job_path']], 'actual checker argv')
    trace.append('verifyBootstrap: passed')


def replay(row, observed_env):
    trace = []
    argv = row['argv']
    node, exec_argv, probe, args = argv[0], argv[1:5], argv[5], argv[6:]
    try:
        env = approved_envelope(args, row['stage'], trace)
    except ProbeError as exc:
        return {"refusal": str(exc), "where": "approvedEnvelope (outside the try: uncaught, stderr, no probe.json)", "trace": trace}
    job = env['job']
    try:
        manifest_bytes = open(p_real(job['manifest']), 'rb').read()
        if hashlib.sha256(manifest_bytes).hexdigest() != job['supplemental_manifest_sha256']:
            raise ProbeError('Supplemental manifest identity differs')
        manifest = strict_json(manifest_bytes, 'manifest')
        if manifest['schema'] != 'ontokin.current-host-readback-lock/0.2.0':
            raise ProbeError('Wrong supplemental manifest')
        verify_bootstrap(env, manifest, exec_argv, [probe] + args, observed_env, trace)
        glb = open(p_real(job['artifact']), 'rb').read()
        aud = open(p_real(job['audit']), 'rb').read()
        if hashlib.sha256(glb).hexdigest() != job['artifact_sha256'] or hashlib.sha256(aud).hexdigest() != job['audit_sha256']:
            raise ProbeError('Actual input identity differs')
        audit = json.loads(aud)
        if audit.get('passed') is not True or audit.get('artifact_sha256') != hashlib.sha256(glb).hexdigest() or audit.get('case') != job['case']:
            raise ProbeError('Independent passed audit does not bind this actual GLB')
        trace.append('input identity passed: the next statement imports the readers')
        return {"refusal": None, "where": "REACHES THE READERS", "trace": trace}
    except ProbeError as exc:
        return {"refusal": str(exc), "where": "inside the try: probe.json error.message", "trace": trace,
                "stdout_line": json.dumps({"passed": False, "slot": job['slot'], "artifact_sha256": job['artifact_sha256']}, separators=(',', ':')) + "\n"}


report = {"rows": {}}
host_cf = FZ['host']['facts']['cf_user_text_encoding']
envs = {"declared_only": dict(ENVIRONMENT), "declared_plus_cf_host_value": dict(ENVIRONMENT, **{CF_NAME: host_cf})}
for rows_file in ('rows-r1.json', 'rows-r2.json'):
    with open(os.path.join(FZ['places']['freeze'], 'probe', rows_file), 'rb') as f:
        doc = json.loads(f.read())
    for row in doc['rows']:
        if row['id'] == 'probe-syntax-check':
            continue
        report["rows"][row['id']] = {k: replay(row, v) for k, v in envs.items()}
# The approved cohort configuration, as the positive starts would see it (only the bootstrap; its manifest is written at run time)
with open(os.path.join(OUT, "records", "04-probe-replay.json"), "x", encoding="utf-8") as f:
    json.dump(report, f, indent=1)
    f.write("\n")
for rid, v in report["rows"].items():
    for k, r in v.items():
        print(rid, k, "->", r["where"], "|", r["refusal"])
        for t in r["trace"]:
            print("     ", t)
        if r.get("stdout_line"):
            print("      stdout:", r["stdout_line"].strip())
