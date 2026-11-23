"""Independently verify P22 installed bytes and receipts without product imports."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess

BASE = Path('/workspace/scratch/aa6113404163')
OUT = BASE / 'phase-p22/prep_review'
PREP = BASE / 'phase-p22/preparation'
SOURCE = BASE / 'prepared-source'
ENV = {'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8', 'TZ': 'UTC', 'UV_THREADPOOL_SIZE': '2'}
EXPECTED_REPORTS = {'NODE': '5ec8bb9c9ed0fdfd0079caef6ca91113fbab0302e5f0c6db1b96b2e7cd75ec6a',
                    'DEPENDENCIES': '0069be7182b608de2559d6c816380c6bf8fe4ed9e98eb0871b0133e9a96c0bbc'}
result = {'schema': 'ontokin.c271.p22-independent-outcome-data-audit/1', 'reviewer': '/root/prep_review',
          'started_at_utc': datetime.now(timezone.utc).isoformat(), 'passed': False, 'assertions': 0,
          'groups': [], 'inputs': {}, 'installed': {}, 'git_reads': [],
          'scope': 'Only static receipt/tree/source/archive-hash checks; no preparer, H0 validator, target or library execution.'}


def require(condition, message):
    result['assertions'] += 1
    if not condition:
        raise AssertionError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode('ascii')


def safe_path(path):
    p = Path(path)
    require(p.is_absolute() and str(p) == str(path) and '..' not in p.parts, 'absolute normalized path')
    for ancestor in (p, *p.parents):
        try:
            st = ancestor.lstat()
        except FileNotFoundError:
            continue
        require(not stat.S_ISLNK(st.st_mode), 'symlink component: ' + str(ancestor))
    return p


def identity(st):
    return (st.st_dev, st.st_ino, st.st_mode, st.st_nlink, st.st_size, st.st_mtime_ns, st.st_ctime_ns)


def describe(path, maximum=512 * 1024 * 1024):
    p = safe_path(path)
    fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= maximum, 'bounded private regular file')
        digest, count = hashlib.sha256(), 0
        while True:
            block = os.read(fd, 1024 * 1024)
            if not block:
                break
            count += len(block)
            require(count <= maximum, 'file grew beyond limit')
            digest.update(block)
        require(count == before.st_size and identity(before) == identity(os.fstat(fd)) == identity(p.lstat()), 'file changed during read')
        return {'path': str(p), 'sha256': digest.hexdigest(), 'size_bytes': count, 'mode': oct(stat.S_IMODE(before.st_mode))}
    finally:
        os.close(fd)


def bound(descriptor):
    require(set(descriptor) == {'path', 'sha256', 'size_bytes', 'mode'}, 'descriptor keys')
    require(describe(descriptor['path']) == descriptor, 'descriptor mismatch: ' + descriptor['path'])


def decode(raw):
    def pairs(rows):
        value = {}
        for key, item in rows:
            require(key not in value, 'duplicate JSON key')
            value[key] = item
        return value
    return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def document(path, canonical_required=True):
    d = describe(path, 16 * 1024 * 1024)
    raw = Path(path).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == d['sha256'], 'document changed after authentication')
    value = decode(raw)
    if canonical_required:
        require(canonical(value) == raw, 'noncanonical document')
    result['inputs'][str(path)] = d
    return value


def absent(path):
    try:
        safe_path(path).lstat()
    except FileNotFoundError:
        return True
    return False


def git_read(*args):
    env = ENV | {'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null', 'GIT_TERMINAL_PROMPT': '0',
                 'GIT_ATTR_NOSYSTEM': '1', 'GIT_OPTIONAL_LOCKS': '0', 'GIT_NO_REPLACE_OBJECTS': '1',
                 'GIT_NO_LAZY_FETCH': '1', 'GIT_CEILING_DIRECTORIES': str(SOURCE.parent)}
    argv = ['/usr/bin/git', '-c', 'core.fsmonitor=false', '-C', str(SOURCE), *args]
    r = subprocess.run(argv, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       timeout=5, check=False)
    result['git_reads'].append({'argv': argv, 'environment': env, 'returncode': r.returncode,
                                'stdout': r.stdout.decode(), 'stderr': r.stderr.decode()})
    require(r.returncode == 0, 'Git read failed')
    return r.stdout.decode().rstrip('\n')


def verify_tree(plan):
    root = safe_path(plan['destination'])
    root_info = root.lstat()
    require(stat.S_ISDIR(root_info.st_mode) and oct(stat.S_IMODE(root_info.st_mode)) == plan['root_mode'], 'root type/mode differs')
    files, directories = set(), set()
    for parent, dirs, names in os.walk(root, followlinks=False):
        for name in dirs:
            path = safe_path(Path(parent) / name)
            st = path.lstat()
            require(stat.S_ISDIR(st.st_mode), 'unexpected directory type')
            directories.add(path.relative_to(root).as_posix())
        for name in names:
            path = safe_path(Path(parent) / name)
            require(stat.S_ISREG(path.lstat().st_mode), 'unexpected installed file type')
            files.add(path.relative_to(root).as_posix())
    require(files == set(plan['files']) and directories == set(plan['directories']), 'complete installed inventory differs')
    necessary = {str(parent) for name in files for parent in PurePosixPath(name).parents if str(parent) != '.'}
    require(directories == necessary, 'necessary directory set differs')
    observed_files = {}
    for name, expected in plan['files'].items():
        actual = describe(root / name)
        require({key: actual[key] for key in ('sha256', 'size_bytes', 'mode')} == expected, 'installed binding differs: ' + name)
        observed_files[name] = actual
    for name, expected in plan['directories'].items():
        require(oct(stat.S_IMODE((root / name).lstat().st_mode)) == expected, 'directory mode differs')
    return {'root': str(root), 'root_mode': plan['root_mode'], 'device': root_info.st_dev, 'inode': root_info.st_ino,
            'files': observed_files, 'directories': plan['directories'], 'file_count': len(files),
            'directory_count': len(directories), 'total_bytes': sum(row['size_bytes'] for row in observed_files.values())}


try:
    acceptance = document(OUT / 'PLAN-REVIEW.json', False)
    require(acceptance['approved'] is True and not acceptance['mandatory_findings_remaining'], 'plan not approved')
    approved = acceptance['approved_inputs']
    for key in ('source_inventory', 'node_plan', 'dependency_plan', 'dependency_inventory', 'launch_plan', 'launcher', 'execution_request'):
        bound(approved[key])
    prior_audit = document(acceptance['static_audit']['report']['path'], False)
    bound(acceptance['static_audit']['report'])
    require(prior_audit['passed'] is True, 'prior membership audit not passing')
    source = approved['source']
    launch = document(approved['launch_plan']['path'])
    actual = document(PREP / 'LAUNCH-RESULT.json')
    actual_d = result['inputs'][str(PREP / 'LAUNCH-RESULT.json')]
    require(actual_d['sha256'] == '5b9867f305978503a67701057d55cf56d8601dbba7f4a587eb54f443ba3f57c8' and actual_d['size_bytes'] == 4277, 'assigned actual launch result differs')
    require(actual['schema'] == 'ontokin.c271.p22-preparation-result/1' and actual['passed'] is True
            and actual['status'] == 'preparation_complete_pending_independent_outcome_review'
            and actual['unknown_operations'] == [], 'launch result not complete')
    require(actual['source'] == source == launch['source'], 'actual/preparation source objects differ')
    require(actual['launch_plan'] == approved['launch_plan'] and actual['launcher'] == approved['launcher'], 'actual launcher/plan differ from approved candidate')
    require([row['name'] for row in actual['commands']] == ['NODE', 'DEPENDENCIES'], 'actual command order/count')
    intent = document(launch['outer_outputs']['intent'])
    require(intent['source'] == source and intent['commands'] == launch['commands']
            and intent['launcher'] == approved['launcher'] and intent['launch_plan'] == approved['launch_plan'], 'outer intent mismatch')
    result['groups'].append('actual launch, exact approved source/plan/launcher and outer intent agree')
    receipts = {}
    for expected_command, actual_command in zip(launch['commands'], actual['commands']):
        label = expected_command['name']
        plan = document(expected_command['plan']['path'])
        require(plan['source'] == source, label + ' full source object equality')
        require(actual_command['argv'] == expected_command['argv'] and actual_command['cwd'] == launch['cwd']
                and actual_command['environment'] == ENV and actual_command['exit_code'] == 0, label + ' actual command mismatch')
        require(type(actual_command['pid']) is int and actual_command['pid'] > 0 and actual_command['process_group'] == actual_command['pid'], label + ' actual child identity')
        for key in ('report', 'installation_index', 'stdout', 'stderr'):
            bound(actual_command[key])
        report = document(actual_command['report']['path'])
        require(actual_command['report']['sha256'] == EXPECTED_REPORTS[label] and actual_command['report']['mode'] == '0o600', label + ' original report descriptor')
        require(set(report) == {'schema', 'passed', 'apply_requested', 'execution_counts', 'operations', 'state', 'archive', 'before', 'after'}, label + ' report closed keys')
        require(report['schema'] == 'ontokin.current-host-readback-install-result/0.1.0' and report['passed'] is True
                and report['state'] == 'INSTALLED_EXACT' and report['apply_requested'] is True, label + ' successful actual install state')
        require(report['execution_counts'] == {'node': 0, 'ldd': 0, 'checkers': 0}, label + ' target starts nonzero')
        require(report['before'] == {'state': 'absent'} and report['after'] == {'state': 'complete_exact', 'files': len(plan['files']), 'directories': len(plan['directories'])}, label + ' before/after tree summary')
        require(report['archive'] == {'members': len(plan['members']), 'expanded_bytes': sum(row['size_bytes'] for row in plan['members'].values())}, label + ' full archive count binding')
        index = document(actual_command['installation_index']['path'])
        require(set(index) == {'schema', 'plan', 'report'} and index['schema'] == 'ontokin.current-host-readback-inspection-installation/0.1.0', label + ' index schema')
        require(index['plan'] == expected_command['plan'] and index['report'] == actual_command['report']
                and plan['report'] == index['report']['path'], label + ' exact plan/report index binding')
        for descriptor in (index['plan'], index['report'], plan['archive']):
            bound(descriptor)
        require(plan['archive'] == prior_audit['archives'][label]['descriptor'], label + ' archive changed since complete membership audit')
        result['installed'][label] = verify_tree(plan)
        tree = result['installed'][label]
        require(len(report['operations']) == 1 and report['operations'][0]['operation'] == 'created_owned_stage', label + ' unexpected operations')
        operation = report['operations'][0]
        require(operation['device'] == tree['device'] and operation['inode'] == tree['inode'], label + ' published root not original owned stage')
        require(absent(operation['path']), label + ' old stage still exists')
        publication = document(plan['report'] + '.publication.json')
        require(publication == {'source': operation['path'], 'destination': plan['destination'], 'owned_stage': [operation['device'], operation['inode']], 'mode': 'RENAME_NOREPLACE', 'state': 'INTENT_RECORDED'}, label + ' publication intent differs')
        preflight = document(plan['report'] + '.preflight.json')
        require(preflight == {'schema': report['schema'], 'passed': False, 'apply_requested': True,
                              'execution_counts': report['execution_counts'], 'operations': [], 'state': 'REJECTED',
                              'archive': report['archive'], 'before': {'state': 'absent'}}, label + ' preflight intermediate record differs')
        child_intent = document(expected_command['process_journal']['intent'])
        started = document(expected_command['process_journal']['started'])
        completed = document(expected_command['process_journal']['completed'])
        require(child_intent['command'] == expected_command and child_intent['environment'] == ENV and child_intent['cwd'] == launch['cwd'], label + ' child intent')
        require(started['pid'] == completed['pid'] == actual_command['pid'] and started['process_group'] == completed['process_group'] == actual_command['process_group'], label + ' child journal identities')
        require(completed['exit_code'] == 0 and completed['state'] == 'completed_wait_observed', label + ' completed wait evidence')
        require(absent(expected_command['process_journal']['exception']), label + ' exception journal present')
        stamps = [datetime.fromisoformat(row) for row in (actual_command['started_at_utc'], started['at_utc'], completed['at_utc'], actual_command['finished_at_utc'])]
        require(stamps == sorted(stamps) and all(item.tzinfo is not None for item in stamps)
                and 0 <= (stamps[-1] - stamps[0]).total_seconds() <= launch['per_command_timeout_seconds'], label + ' time ordering/bound')
        require(actual_command['stderr']['size_bytes'] == 0, label + ' stderr not empty')
        stdout = decode(Path(actual_command['stdout']['path']).read_bytes())
        require(stdout == {'passed': True, 'state': 'INSTALLED_EXACT', 'report': plan['report']}, label + ' stdout result differs')
        receipts[label] = {'purpose': plan['purpose'], 'plan': expected_command['plan'], 'report': actual_command['report'],
                           'index': actual_command['installation_index'], 'destination': plan['destination'],
                           'accepted_state': report['state'], 'source': plan['source'], 'archive': plan['archive'],
                           'child_pid_in_execution_namespace': actual_command['pid'], 'completed_wait_exit_code': 0,
                           'duration_seconds': (stamps[-1] - stamps[0]).total_seconds()}
    result['receipts'] = receipts
    result['groups'].append('both original reports and canonical indexes meet exact installation receipt predicates')
    result['groups'].append('26 installed files and 14 necessary subdirectories match bytes/modes/root inventories; published stage identities reconcile')
    result['groups'].append('complete archive membership audit reused after exact unchanged archive descriptor/hash checks')
    result['groups'].append('both actual child journals, successful waits, empty stderr and publication/preflight records agree')
    dependencies = document(approved['dependency_inventory']['path'])
    dependency_plan = document(approved['dependency_plan']['path'])
    require(dependencies == {'schema': 'ontokin.current-host-readback-dependencies/0.1.0',
                             'files': dependency_plan['files'], 'directories': dependency_plan['directories'], 'archive': dependency_plan['archive']}, 'dependency inventory differs')
    inventory = document(source['inventory']['path'])
    requirements = document(OUT / 'PREPARATION-REQUIREMENTS.json', False)
    names = set(requirements['source_predicates']['explicit_files'])
    for directory in requirements['source_predicates']['source_trees']:
        for parent, dirs, files in os.walk(SOURCE / directory, followlinks=False):
            for name in dirs:
                require(not (Path(parent) / name).is_symlink() and name != '__pycache__', 'source directory changed')
            for name in files:
                path = Path(parent) / name
                require(path.suffix not in ('.pyc', '.pyo'), 'source bytecode appeared')
                names.add(path.relative_to(SOURCE).as_posix())
    names.update(name for name in requirements['source_predicates']['optional_existing_files'] if (SOURCE / name).exists())
    require(names == set(inventory['files']) and len(names) == 626, 'source inventory set/count changed')
    for name, binding in inventory['files'].items():
        bound({'path': str(SOURCE / name), **binding})
    require((SOURCE / '.git').is_dir() and not (SOURCE / '.git').is_symlink(), 'ordinary .git changed')
    require(git_read('rev-parse', '--show-toplevel') == source['root'], 'source Git root changed')
    require(git_read('rev-parse', '--verify', 'HEAD^{commit}') == source['commit'], 'source Git commit changed')
    require(git_read('rev-parse', '--verify', source['commit'] + '^{tree}') == source['tree'], 'source Git tree changed')
    require(git_read('status', '--porcelain=v1', '--untracked-files=no') == '', 'source tracked changes')
    require(git_read('ls-files', '--others', '--exclude-standard', '-z') == '', 'source untracked changes')
    for key in ('python', 'git', 'preparer'):
        bound(launch[key])
    for path, expected in launch['destination_and_evidence_ancestors'].items():
        info = safe_path(path).lstat()
        require(stat.S_ISDIR(info.st_mode) and {'device': info.st_dev, 'inode': info.st_ino, 'mode': oct(stat.S_IMODE(info.st_mode))} == expected, 'ancestor changed')
    result['source'] = source
    result['source_files_verified'] = len(names)
    result['groups'].append('all 626 source bindings, clean ordinary Git identity, prerequisite tools and ancestors unchanged')
    require(describe(launch['outer_outputs']['stderr'])['size_bytes'] == 0, 'outer stderr not empty')
    outer_stdout = decode(Path(launch['outer_outputs']['stdout']).read_bytes())
    require(outer_stdout == {'passed': True, 'status': actual['status'], 'commands': 2, 'result': actual_d, 'unknown_operations': []}, 'outer stdout differs')
    result['outer_stdout'] = describe(launch['outer_outputs']['stdout'])
    result['outer_stderr'] = describe(launch['outer_outputs']['stderr'])
    result['groups'].append('outer capture agrees with actual result; no unresolved operation in this retained attempt')
    result['passed'] = True
finally:
    result['finished_at_utc'] = datetime.now(timezone.utc).isoformat()
    path = OUT / 'OUTCOME-STATIC-AUDIT.json'
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(json.dumps(result, indent=2, sort_keys=True).encode() + b'\n')
    print(json.dumps({'passed': result['passed'], 'assertions': result['assertions'], 'groups': result['groups'],
                      'installed': {name: {key: tree[key] for key in ('file_count', 'directory_count', 'total_bytes')} for name, tree in result['installed'].items()},
                      'audit': str(path)}))
