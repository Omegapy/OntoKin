"""Independent P22 data-only plan/archive/source review. Imports no project code."""
from datetime import datetime, timezone
import ast
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import tarfile

BASE = Path('/workspace/scratch/aa6113404163')
OUT = BASE / 'phase-p22/prep_review'
PLANS = BASE / 'phase-p22/preparation'
SOURCE = BASE / 'prepared-source'
EXPECTED = {
    'NODE-INSTALL-PLAN.json': '9eba7e35c16a6a74666dbba24cb111e6ebb4bc3062d4e19010c5125086994e3c',
    'DEPENDENCIES-INSTALL-PLAN.json': '97d90b6bfa510261b89b03c46e979b3d67d38b81b06e8eff17d1f093422d7d3d',
    'SOURCE-INVENTORY.json': '19ae4101657ed8542f06dac14603578108dc8986cb639c17106300ef29d8abd2',
    'LAUNCH-PLAN.json': 'b9c2c92d176b216f554cc599f10317738fca619124d9e25188e49d248ab0f4c8',
}
ENVIRONMENT = {'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8', 'TZ': 'UTC', 'UV_THREADPOOL_SIZE': '2'}
result = {'schema': 'ontokin.c271.p22-independent-plan-data-audit/1',
          'reviewer': '/root/prep_review', 'started_at_utc': datetime.now(timezone.utc).isoformat(),
          'passed': False, 'assertions': 0, 'groups': [], 'inputs': {}, 'archives': {}, 'git_reads': [],
          'scope': 'Data-only archive/source/plan checks; no project import, preparer, target execution or installation.'}


def require(condition, message):
    result['assertions'] += 1
    if not condition:
        raise AssertionError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode('ascii')


def safe_path(path):
    p = Path(path)
    require(p.is_absolute() and str(p) == str(path) and '..' not in p.parts, 'normalized absolute path: ' + str(p))
    for ancestor in (p, *p.parents):
        try:
            info = ancestor.lstat()
        except FileNotFoundError:
            continue
        require(not stat.S_ISLNK(info.st_mode), 'symlink component: ' + str(ancestor))
    return p


def identity(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mode, info.st_nlink, info.st_mtime_ns, info.st_ctime_ns)


def describe(path, maximum=512 * 1024 * 1024):
    p = safe_path(path)
    fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1, 'private regular file: ' + str(p))
        require(before.st_size <= maximum, 'file size limit: ' + str(p))
        digest = hashlib.sha256()
        length = 0
        while True:
            data = os.read(fd, 1024 * 1024)
            if not data:
                break
            digest.update(data)
            length += len(data)
            require(length <= maximum, 'file grew beyond limit')
        require(identity(before) == identity(os.fstat(fd)) == identity(p.lstat()), 'file changed while read: ' + str(p))
        require(length == before.st_size, 'file read length mismatch')
        return {'path': str(p), 'sha256': digest.hexdigest(), 'size_bytes': length, 'mode': oct(stat.S_IMODE(before.st_mode))}
    finally:
        os.close(fd)


def bound(descriptor):
    require(set(descriptor) == {'path', 'sha256', 'size_bytes', 'mode'}, 'descriptor keys')
    require(describe(descriptor['path']) == descriptor, 'descriptor differs: ' + descriptor['path'])


def decode(raw):
    def pairs(rows):
        value = {}
        for key, item in rows:
            require(key not in value, 'duplicate JSON key')
            value[key] = item
        return value
    return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
                      parse_constant=lambda text: (_ for _ in ()).throw(ValueError(text)))


def document(path, canonical_required=True):
    descriptor = describe(path, 16 * 1024 * 1024)
    raw = Path(path).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == descriptor['sha256'], 'document changed on second read')
    value = decode(raw)
    if canonical_required:
        require(canonical(value) == raw, 'noncanonical JSON: ' + str(path))
    result['inputs'][str(path)] = descriptor
    return value


def absent(path):
    p = safe_path(path)
    try:
        p.lstat()
    except FileNotFoundError:
        return True
    return False


def git_read(*args):
    env = ENVIRONMENT | {'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null',
                         'GIT_TERMINAL_PROMPT': '0', 'GIT_ATTR_NOSYSTEM': '1', 'GIT_OPTIONAL_LOCKS': '0',
                         'GIT_NO_REPLACE_OBJECTS': '1', 'GIT_NO_LAZY_FETCH': '1',
                         'GIT_CEILING_DIRECTORIES': str(SOURCE.parent)}
    argv = ['/usr/bin/git', '-c', 'core.fsmonitor=false', '-C', str(SOURCE), *args]
    observed = subprocess.run(argv, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, timeout=5, check=False)
    result['git_reads'].append({'argv': argv, 'environment': env, 'returncode': observed.returncode,
                                'stdout': observed.stdout.decode('utf-8'), 'stderr': observed.stderr.decode('utf-8')})
    require(observed.returncode == 0, 'Git read failed')
    return observed.stdout.decode('utf-8').rstrip('\n')


def mode(value):
    require(type(value) is str and value in {oct(number) for number in range(0o1000)}, 'invalid mode')
    parsed = int(value, 8)
    require(parsed & 0o7022 == 0, 'privileged or writable mode')
    return parsed


def relative(name):
    require(type(name) is str and bool(name) and '\\' not in name, 'invalid relative name')
    path = PurePosixPath(name)
    require(not path.is_absolute() and str(path) == name and '..' not in path.parts and name != '.', 'unsafe relative name')
    return path


def verify_archive(label, plan, historical, expected_targets):
    descriptor = plan['archive']
    bound(descriptor)
    path = Path(descriptor['path'])
    expected_members = historical['members']
    require(set(plan['members']) == set(expected_members), label + ' full historical member set differs')
    observed = {}
    package_data = {}
    opened = path.lstat()
    with path.open('rb') as stream, tarfile.open(fileobj=stream, mode='r:*') as archive:
        for member in archive:
            name = member.name[:-1] if member.name.endswith('/') else member.name
            relative(name)
            require(name not in observed and len(observed) < 32768, label + ' duplicate or excessive member')
            require(member.isfile() and not member.sparse and not member.linkname, label + ' nonregular/sparse/link member')
            mode(oct(member.mode))
            require(member.size >= 0, 'negative member size')
            digest, length, chunks = hashlib.sha256(), 0, []
            retain = name in ('SOURCE.json', 'c195-validation/receiving/indexer-view/three/package.json',
                              'c195-validation/receiving/validator/package/package.json')
            source = archive.extractfile(member)
            require(source is not None, 'unreadable archive file')
            with source:
                while True:
                    block = source.read(1024 * 1024)
                    if not block:
                        break
                    length += len(block)
                    require(length <= member.size, 'member grew beyond header size')
                    digest.update(block)
                    if retain:
                        chunks.append(block)
            require(length == member.size, 'member size mismatch')
            actual = {'kind': 'file', 'size_bytes': length, 'sha256': digest.hexdigest(),
                      'mode': oct(member.mode), 'target': expected_targets.get(name)}
            require(actual == plan['members'].get(name), label + ' operational member binding mismatch: ' + name)
            require(actual | {'target': None} == expected_members[name], label + ' P09 member mismatch: ' + name)
            observed[name] = actual
            if retain:
                package_data[name] = decode(b''.join(chunks))
    require(identity(opened) == identity(path.lstat()), label + ' archive changed during streaming')
    bound(descriptor)
    require(set(observed) == set(plan['members']), label + ' missing members')
    require(len(observed) == historical['counts']['members'], label + ' member count mismatch')
    total = sum(row['size_bytes'] for row in observed.values())
    require(total == historical['counts']['logical_bytes'] and total <= 1024 * 1024 * 1024, label + ' expanded bytes mismatch')
    selected = {row['target']: {key: row[key] for key in ('sha256', 'size_bytes', 'mode')}
                for row in observed.values() if row['target'] is not None}
    require(selected == plan['files'], label + ' archive-to-target tree mismatch')
    if label == 'NODE':
        require(package_data['SOURCE.json']['supported_version_predeclared'] == 'v24.22.1', 'Node metadata version differs')
        require(package_data['SOURCE.json']['source_observation']['sha256'] == plan['files']['bin/node']['sha256'], 'Node metadata digest differs')
    else:
        require(package_data['c195-validation/receiving/indexer-view/three/package.json']['version'] == '0.186.1', 'Three package version differs')
        require(package_data['c195-validation/receiving/validator/package/package.json']['version'] == '2.0.0-dev.3.10', 'Validator package version differs')
    result['archives'][label] = {'descriptor': descriptor, 'members_verified': len(observed),
                                 'expanded_bytes': total, 'selected_files': len(selected),
                                 'all_plan_rows_equal_actual_and_p09': True, 'no_extraction_performed': True,
                                 'member_map_sha256': hashlib.sha256(canonical(observed)).hexdigest()}


try:
    requirements = document(OUT / 'PREPARATION-REQUIREMENTS.json', False)
    early = document(BASE / 'phase-p22/state/EARLY-RECOVERY-RECEIPT.json', False)
    early_review = document(BASE / 'phase-p22/archive_audit/EARLY-SAVE-READBACK-REVIEW.json', False)
    require(early['status'] == 'confirmed_saved_and_byte_read_back' and early['saved_bytes_readback_equal'] is True, 'early save not confirmed')
    require(early_review['verdict'] == 'accepted_confirmed_saved_and_exact_readback' and
            early_review['archive']['sha256'] == early['sha256'], 'independent early readback not accepted')
    result['groups'].append('confirmed early recovery evidence accepted')
    docs = {name: document(PLANS / name) for name in EXPECTED}
    for name, digest in EXPECTED.items():
        require(result['inputs'][str(PLANS / name)]['sha256'] == digest, 'assigned exact document identity: ' + name)
    launch = docs['LAUNCH-PLAN.json']
    source = document(PLANS / 'SOURCE.json')
    require(source == launch['source'], 'source sidecar and launch source differ')
    require(source['root'] == str(SOURCE) and source['commit'] == '527368bd5195c439762b43e2cc836ff9822213f8'
            and source['tree'] == 'e8844be5189b65d1bc17af40861fac672b189b25', 'source identity differs')
    require((SOURCE / '.git').is_dir() and not (SOURCE / '.git').is_symlink(), 'ordinary .git required')
    require(git_read('rev-parse', '--show-toplevel') == source['root'], 'Git root mismatch')
    require(git_read('rev-parse', '--verify', 'HEAD^{commit}') == source['commit'], 'Git HEAD mismatch')
    require(git_read('rev-parse', '--verify', source['commit'] + '^{tree}') == source['tree'], 'Git tree mismatch')
    require(git_read('status', '--porcelain=v1', '--untracked-files=no') == '', 'dirty source')
    require(git_read('ls-files', '--others', '--exclude-standard', '-z') == '', 'untracked source')
    bound(source['inventory'])
    inventory = docs['SOURCE-INVENTORY.json']
    require(set(inventory) == {'schema', 'files'} and inventory['schema'] == 'ontokin.current-host-readback-source/0.1.0', 'source schema')
    names = set(requirements['source_predicates']['explicit_files'])
    for directory in requirements['source_predicates']['source_trees']:
        require((SOURCE / directory).is_dir(), 'required source directory missing')
        for root, directories, files in os.walk(SOURCE / directory, followlinks=False):
            for name in directories:
                path = Path(root) / name
                require(not path.is_symlink() and name != '__pycache__', 'unbound source directory')
            for name in files:
                path = Path(root) / name
                require(path.suffix not in ('.pyc', '.pyo'), 'bytecode source input')
                names.add(path.relative_to(SOURCE).as_posix())
    names.update(name for name in requirements['source_predicates']['optional_existing_files'] if (SOURCE / name).exists())
    require(names == set(inventory['files']) and len(names) == 626, 'source inventory path set/count differs')
    for name, expected in inventory['files'].items():
        relative(name)
        bound({'path': str(SOURCE / name), **expected})
    for key in ('preparer', 'provider', 'inspector'):
        reference = requirements['source_predicates'][key]
        actual = describe(SOURCE / reference['path'])
        require(actual['sha256'] == reference['sha256'] and actual['size_bytes'] == reference['size_bytes'], 'changed implementation: ' + key)
    result['source'] = source
    result['source_file_count'] = len(names)
    result['groups'].append('exact ordinary clean source, 626 file bindings, unchanged implementation')
    require(launch['environment'] == ENVIRONMENT and launch['cwd'] == str(SOURCE), 'launch environment/cwd')
    require(launch['command_order'] == ['NODE', 'DEPENDENCIES'] and [row['name'] for row in launch['commands']] == ['NODE', 'DEPENDENCIES'], 'command order')
    require(launch['per_command_timeout_seconds'] == 120, 'outer bound differs')
    for key in ('python', 'git', 'preparer'):
        bound(launch[key])
    require({key: launch['python'][key] for key in ('sha256', 'size_bytes', 'mode')} == requirements['host_and_launch_boundary']['python_pin_for_later_h0'], 'Python pin')
    require(launch['git']['path'] == '/usr/bin/git', 'fixed PATH Git differs')
    require(launch['preparer']['path'] == str(SOURCE / 'tools/prepare_current_host_readback.py'), 'preparer belongs to another source')
    necessary_ancestors = set()
    for path in (BASE / 'prepared-inputs', PLANS):
        necessary_ancestors.update(str(p) for p in (path, *path.parents))
    require(set(launch['destination_and_evidence_ancestors']) == necessary_ancestors, 'ancestor set differs')
    for path, expected in launch['destination_and_evidence_ancestors'].items():
        p = safe_path(path)
        info = p.lstat()
        require(stat.S_ISDIR(info.st_mode), 'non-directory ancestor')
        require({'device': info.st_dev, 'inode': info.st_ino, 'mode': oct(stat.S_IMODE(info.st_mode))} == expected, 'ancestor identity changed')
    result['groups'].append('fixed interpreter/Git/preparer, environment, command order, 120 second bound and ancestors')
    all_outputs = []
    for command in launch['commands']:
        label = command['name']
        plan = docs[label + '-INSTALL-PLAN.json']
        bound(command['plan'])
        require(plan['source'] == source, label + ' source object equality')
        require(set(plan) == set(requirements['plan_contract']['keys']), label + ' plan closed keys')
        require(plan['schema'] == 'ontokin.current-host-readback-install/0.1.0', label + ' plan schema')
        require(plan['purpose'] == ('selected-node' if label == 'NODE' else 'retained-dependencies'), label + ' purpose')
        require(plan['destination'] == str(BASE / 'prepared-inputs' / ('node' if label == 'NODE' else 'readback-dependencies')), label + ' destination')
        require(command['destination'] == plan['destination'] and absent(plan['destination']), label + ' destination must be absent')
        require(plan['root_mode'] == '0o755', label + ' selected root mode')
        mode(plan['root_mode'])
        required_dirs = {str(parent) for name in plan['files'] for parent in relative(name).parents if str(parent) != '.'}
        require(plan['directories'] == {name: '0o755' for name in required_dirs}, label + ' exact necessary directories/modes')
        require(plan['report'] == str(PLANS / (label + '-INSTALL-REPORT.json')), label + ' report location')
        expected_argv = [launch['python']['path'], '-I', '-S', '-B', launch['preparer']['path'], '--plan', command['plan']['path'], '--plan-sha256', command['plan']['sha256'], '--apply']
        require(command['argv'] == expected_argv and command['expected_preparation_state'] == 'INSTALLED_EXACT', label + ' invocation')
        expected_outputs = [plan['report'], plan['report'] + '.preflight.json', plan['report'] + '.publication.json',
                            str(PLANS / (label + '-INSTALLATION-INDEX.json')), str(PLANS / (label + '.stdout.log')), str(PLANS / (label + '.stderr.log'))]
        expected_journal = {name.lower(): str(PLANS / (label + '-PROCESS-' + name + '.json'))
                            for name in ('INTENT', 'STARTED', 'COMPLETED', 'EXCEPTION')}
        require(command['process_journal'] == expected_journal, label + ' child journal paths differ')
        expected_outputs.extend(expected_journal.values())
        require(command['fresh_outputs'] == expected_outputs, label + ' fresh output set')
        all_outputs.extend(expected_outputs)
        for path in expected_outputs:
            require(absent(path), label + ' fresh output exists: ' + path)
        name = 'node' if label == 'NODE' else 'dependencies'
        req = requirements['archives'][name]
        historical = document(SOURCE / req['raw_inventory']['path'], False)
        require(plan['archive']['sha256'] == req['sha256'] and plan['archive']['size_bytes'] == req['size_bytes'], label + ' archive immutable pin')
        rows = req['member_mapping'] if label == 'NODE' else req['target_files']
        expected_targets = {row['archive_member']: row['target'] for row in rows}
        require(plan['files'] == {row['target']: {key: row[key] for key in ('sha256', 'size_bytes', 'mode')} for row in rows}, label + ' immutable target pins')
        verify_archive(label, plan, historical, expected_targets)
    require(len(all_outputs) == len(set(all_outputs)), 'overlapping command output names')
    node = docs['NODE-INSTALL-PLAN.json']
    deps = docs['DEPENDENCIES-INSTALL-PLAN.json']
    deps_inventory = document(PLANS / 'DEPENDENCY-INVENTORY.json')
    require(deps_inventory == {'schema': 'ontokin.current-host-readback-dependencies/0.1.0',
                              'files': deps['files'], 'directories': deps['directories'], 'archive': deps['archive']}, 'dependency inventory and plan differ')
    pins = document(SOURCE / 'docs/engineering/static-tray-qualification-c199/EXTERNAL-INPUTS.json')
    prefix = pins['dependencies_root'] + '/'
    immutable = {name[len(prefix):]: binding for name, binding in pins['files'].items() if name.startswith(prefix)}
    require(immutable == {name: {key: binding[key] for key in ('sha256', 'size_bytes')} for name, binding in deps['files'].items()}, 'independent original C199 pins differ')
    result['groups'].append('both complete archive byte/member inventories, immutable target pins and dependency inventory')
    request = document(PLANS / 'EXECUTION-REQUEST.json', False)
    bound(request['launch_plan'])
    bound(request['launcher'])
    require(request['launcher']['sha256'] == '676c24af7e0402ccc2971bc41a8a25e4409ac8c47eeb8b914cb45079e24a69d1', 'candidate003 launcher changed')
    require(result['inputs'][str(PLANS / 'EXECUTION-REQUEST.json')]['sha256'] == '8d231f29ad1fdedb356033e2d8e9cdc34940f56d32532353eb97a8725b503ba6', 'candidate003 outer request changed')
    require(request['launch_plan']['sha256'] == EXPECTED['LAUNCH-PLAN.json'], 'request launch plan differs')
    require(request['environment'] == ENVIRONMENT and request['cwd'] == str(BASE) and request['invocation_count'] == 1, 'outer environment/cwd/count')
    require(request['argv'] == [launch['python']['path'], '-I', '-S', '-B', request['launcher']['path'], '--launch-plan', request['launch_plan']['path'], '--launch-sha256', request['launch_plan']['sha256']], 'outer argv differs')
    require(request['stdout'] == launch['outer_outputs']['stdout'] and request['stderr'] == launch['outer_outputs']['stderr'], 'outer log paths differ')
    for path in launch['outer_outputs'].values():
        require(absent(path), 'outer output already exists: ' + path)
    require(set(launch['outer_outputs'].values()).isdisjoint(all_outputs), 'outer output overlap')
    result['launcher'] = request['launcher']
    result['execution_request'] = result['inputs'][str(PLANS / 'EXECUTION-REQUEST.json')]
    result['groups'].append('exact outer request, one invocation, absent exclusive log/intent/result paths')
    result['passed'] = True
finally:
    result['finished_at_utc'] = datetime.now(timezone.utc).isoformat()
    path = OUT / 'PLAN-STATIC-AUDIT-candidate003.json'
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
    with os.fdopen(fd, 'wb') as output:
        output.write(json.dumps(result, indent=2, sort_keys=True).encode() + b'\n')
    print(json.dumps({'passed': result['passed'], 'assertions': result['assertions'], 'groups': result['groups'],
                      'archives': result['archives'], 'audit': str(path)}))
