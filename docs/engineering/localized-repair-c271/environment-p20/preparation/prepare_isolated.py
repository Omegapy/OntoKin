"""One reviewed, bounded wheel-only environment preparation; no product execution."""
import base64
import csv
import datetime
import email.parser
import hashlib
import io
import json
import os
import re
import signal
import stat
import subprocess
import sys
import time
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REPO = ROOT / 'repo'
PLAN_PATH = HERE / 'PREPARATION-PLAN.json'
if (HERE / 'RESULT.json').exists():
    raise SystemExit('An attempt already exists; reconcile it without replay or overwrite')
PLAN = json.loads(PLAN_PATH.read_text())
INVENTORY = json.loads((HERE / 'INPUT-INVENTORY.json').read_text())
RESULT = {'schema': 'ontokin.c271.p20-preparation-result/1', 'started_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'plan_sha256': hashlib.sha256(PLAN_PATH.read_bytes()).hexdigest(), 'source_revision': PLAN['source_revision'],
          'steps': [], 'status': 'in_progress', 'product_commands_invoked': [], 'seven_package_imports_by_controller': False,
          'h0_accepted': False, 'h1_executed': False, 'full_routine_executed': False}

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def save():
    (HERE / 'RESULT.json').write_text(json.dumps(RESULT, indent=2) + '\n')

def require(condition, code, detail=None):
    if not condition:
        raise RuntimeError(json.dumps({'code': code, 'detail': detail}))

def normalize(name):
    return re.sub(r'[-_.]+', '-', name).lower()

def identity(path):
    path = Path(path)
    s = path.stat()
    return {'path': str(path), 'bytes': s.st_size, 'sha256': sha(path), 'mode': oct(stat.S_IMODE(s.st_mode))}

def check_inputs():
    rows = [INVENTORY['python'], *INVENTORY['pip_source_tree'], *INVENTORY['pip_metadata'],
            *INVENTORY['shared_package_metadata'], *INVENTORY['shared_pth_files'], PLAN['lock']]
    failures = []
    for row in rows:
        path = Path(row['path'])
        if not path.is_file():
            failures.append({'path': str(path), 'reason': 'not_file'})
            continue
        actual = identity(path)
        for key in ['sha256', 'bytes', 'mode']:
            if key in row and actual[key] != row[key]:
                failures.append({'path': str(path), 'field': key, 'expected': row[key], 'actual': actual[key]})
    return {'checked': len(rows), 'failures': failures}

def run_command(index, env):
    command = PLAN['commands'][index]
    row = {'name': command['name'], 'argv': command['argv'], 'cwd': command['cwd'],
           'timeout_seconds': command['timeout_seconds'], 'started_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'status': 'launch_intent', 'stdout': str(HERE / (command['name'] + '.stdout.log')),
           'stderr': str(HERE / (command['name'] + '.stderr.log'))}
    RESULT['steps'].append(row)
    save()
    with Path(row['stdout']).open('xb') as stdout, Path(row['stderr']).open('xb') as stderr:
        process = subprocess.Popen(command['argv'], cwd=command['cwd'], env=env, stdout=stdout, stderr=stderr, start_new_session=True)
        row.update({'pid': process.pid, 'status': 'running'})
        save()
        try:
            code = process.wait(timeout=command['timeout_seconds'])
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            code = process.wait(timeout=10)
            row['timed_out'] = True
        row.update({'returncode': code, 'status': 'completed', 'finished_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()})
    row['stdout_sha256'] = sha(row['stdout'])
    row['stderr_sha256'] = sha(row['stderr'])
    save()
    require(not row.get('timed_out') and code == 0, 'PREPARATION_COMMAND_FAILED', {'step': command['name'], 'returncode': code, 'timed_out': row.get('timed_out', False)})
    require(not Path(PLAN['pycache_prefix']).exists(), 'UNEXPECTED_PYCACHE_CREATED')

def inspect_wheels():
    expected = {normalize(row['name']): row for row in PLAN['pins']}
    found = {}
    paths = sorted(Path(PLAN['wheelhouse']).iterdir())
    require(len(paths) == 7 and all(p.is_file() and p.suffix == '.whl' and not p.is_symlink() for p in paths), 'WHEEL_INVENTORY_MISMATCH', [str(x) for x in paths])
    for path in paths:
        record = identity(path)
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            require(len(names) == len(set(names)) and archive.testzip() is None, 'WHEEL_INTEGRITY', str(path))
            require(all(not Path(n).is_absolute() and '..' not in Path(n).parts and '\\' not in n for n in names), 'UNSAFE_WHEEL_PATH', str(path))
            require(not any(stat.S_ISLNK(i.external_attr >> 16) for i in archive.infolist()), 'WHEEL_SYMLINK', str(path))
            require(not any(n.endswith('.pth') or Path(n).name in {'sitecustomize.py', 'usercustomize.py'} for n in names), 'WHEEL_STARTUP_HOOK', str(path))
            metadata = [n for n in names if n.endswith('.dist-info/METADATA')]
            require(len(metadata) == 1, 'WHEEL_METADATA_COUNT', str(path))
            message = email.parser.BytesParser().parsebytes(archive.read(metadata[0]))
            name = normalize(message['Name'])
            require(name in expected and name not in found, 'WHEEL_NAME', name)
            require(message['Version'] == expected[name]['version'] and record['sha256'] == expected[name]['sha256'], 'WHEEL_PIN', record)
            record.update({'name': message['Name'], 'version': message['Version'], 'members': len(names), 'metadata_member': metadata[0]})
            found[name] = record
    require(set(found) == set(expected), 'WHEEL_NAMES_INCOMPLETE')
    RESULT['wheels'] = list(found.values())
    save()

def inspect_installed():
    envroot = Path(PLAN['venv'])
    site = envroot / 'lib/python3.12/site-packages'
    expected = {normalize(x['name']): x['version'] for x in PLAN['pins']}
    observed = {}
    files = []
    recorded = set()
    for metadata in sorted(site.glob('*.dist-info/METADATA')):
        message = email.parser.BytesParser().parsebytes(metadata.read_bytes())
        name = normalize(message['Name'])
        require(name in expected and name not in observed and message['Version'] == expected[name], 'INSTALLED_METADATA_PIN', str(metadata))
        record_path = metadata.parent / 'RECORD'
        require(record_path.is_file(), 'MISSING_RECORD', str(record_path))
        checked = 0
        for rel, encoded_hash, size in csv.reader(io.StringIO(record_path.read_text())):
            path = (site / rel).resolve()
            require(path.is_relative_to(envroot.resolve()) and path.is_file(), 'RECORD_PATH', rel)
            require(not (site / rel).is_symlink(), 'RECORD_SYMLINK', rel)
            b = path.read_bytes()
            if encoded_hash:
                algo, encoded = encoded_hash.split('=', 1)
                require(algo == 'sha256', 'RECORD_HASH_ALGORITHM', algo)
                expected_hash = base64.urlsafe_b64decode(encoded + '=' * (-len(encoded) % 4)).hex()
                require(hashlib.sha256(b).hexdigest() == expected_hash and len(b) == int(size), 'RECORD_CONTENT', rel)
            else:
                require(path == record_path.resolve(), 'UNHASHED_INSTALLED_FILE', rel)
            recorded.add(path)
            checked += 1
        observed[name] = {'name': message['Name'], 'version': message['Version'], 'metadata': identity(metadata), 'record': identity(record_path), 'record_rows_verified': checked}
    require(observed.keys() == expected.keys(), 'INSTALLED_NAMES_INCOMPLETE')
    for path in sorted(site.rglob('*')):
        require(not path.is_symlink(), 'INSTALLED_SYMLINK', str(path))
        if path.is_file():
            require(path.suffix != '.pth' and path.name not in {'sitecustomize.py', 'usercustomize.py'}, 'INSTALLED_STARTUP_HOOK', str(path))
            require(path.resolve() in recorded, 'UNRECORDED_INSTALLED_FILE', str(path))
    for path in sorted(recorded):
        row = identity(path)
        row['relative_to_venv'] = str(path.relative_to(envroot))
        row['native_artifact'] = path.suffix in {'.so', '.dll', '.dylib'} or '.so.' in path.name
        files.append(row)
    RESULT['installed'] = {'site_root': str(site), 'packages': list(observed.values()), 'files': files,
                           'native_artifacts_hashed_as_data': sum(x['native_artifact'] for x in files), 'package_imports': False}
    save()

def main():
    require(not (HERE / 'RESULT.json').exists(), 'ATTEMPT_ALREADY_EXISTS')
    approval = json.loads((HERE.parent / 'environment_review/PREPARATION-REVIEW.json').read_text())
    require(approval['verdict'] == 'accepted_for_one_preparation_attempt', 'REVIEW_NOT_ACCEPTED')
    require(approval['plan_sha256'] == RESULT['plan_sha256'] and approval['script_sha256'] == sha(__file__), 'REVIEW_BINDING_MISMATCH')
    require(sha(HERE / 'INPUT-INVENTORY.json') == PLAN['installer_inventory_sha256'], 'INPUT_INVENTORY_BINDING_MISMATCH')
    early = json.loads((HERE.parent / 'state/EARLY-RECOVERY-RECEIPT.json').read_text())
    require(early['status'] == 'confirmed' and early['saved_bytes_readback_equal'], 'EARLY_SAVE_REQUIRED')
    require(Path(sys.executable).resolve() == Path(INVENTORY['python']['path']), 'PYTHON_PATH_CHANGED')
    require(sys.pycache_prefix == PLAN['pycache_prefix'] and sys.dont_write_bytecode, 'CONTROLLER_CACHE_POLICY')
    require(not Path(PLAN['pycache_prefix']).exists() and not Path(PLAN['pycache_prefix']).is_symlink(), 'PYCACHE_PREFIX_NOT_FRESH')
    before = check_inputs()
    require(not before['failures'] and INVENTORY['python_pin_matches'], 'PREPARATION_INPUT_CHANGED', before)
    RESULT['input_checks_before'] = before
    for raw in [PLAN['venv'], PLAN['wheelhouse'], PLAN['work']]:
        path = Path(raw)
        require(not path.exists() and not path.is_symlink() and path.parent.resolve() == ROOT, 'DESTINATION_NOT_FRESH', raw)
    env = {key: os.environ[key] for key in PLAN['inherited_environment_keys'] if key in os.environ}
    env.update(PLAN['fixed_environment'])
    Path(PLAN['work']).mkdir(mode=0o700)
    Path(PLAN['wheelhouse']).mkdir(mode=0o700)
    (Path(PLAN['work']) / 'tmp').mkdir(mode=0o700)
    save()
    run_command(0, env)
    inspect_wheels()
    run_command(1, env)
    envroot = Path(PLAN['venv'])
    cfg = (envroot / 'pyvenv.cfg').read_text()
    require('include-system-site-packages = false' in cfg, 'SYSTEM_SITE_ENABLED')
    require((envroot / 'bin/python').resolve() == Path(INVENTORY['python']['path']), 'VENV_PYTHON_CHANGED')
    site = envroot / 'lib/python3.12/site-packages'
    require(site.is_dir() and not list(site.iterdir()), 'VENV_NOT_EMPTY_BEFORE_INSTALL')
    RESULT['venv'] = {'cfg': identity(envroot / 'pyvenv.cfg'), 'cfg_text': cfg, 'python_alias': str(envroot / 'bin/python'), 'resolved_python': str((envroot / 'bin/python').resolve()), 'site_empty_before_install': True}
    save()
    run_command(2, env)
    inspect_installed()
    RESULT['status'] = 'prepared_static_identity_verified'

try:
    main()
except Exception as error:
    RESULT['status'] = 'blocked'
    RESULT['first_blocker'] = {'type': type(error).__name__, 'message': str(error)}
finally:
    RESULT['input_checks_after'] = check_inputs()
    if RESULT['input_checks_after']['failures']:
        RESULT['status'] = 'blocked'
        RESULT['preservation_failure'] = RESULT['input_checks_after']['failures']
    RESULT['finished_at_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    RESULT['fresh_pycache_prefix_absent_after'] = not Path(PLAN['pycache_prefix']).exists()
    if not RESULT['fresh_pycache_prefix_absent_after']:
        RESULT['status'] = 'blocked'
        RESULT['cache_policy_failure'] = 'The reviewed fresh cache destination was unexpectedly created'
    RESULT['limits'] = 'Preparation and static identities only; no H0/H1, ordinary-provider agreement, product regression, integration or release qualification'
    save()
    print(json.dumps({'status': RESULT['status'], 'direct_preparation_commands': len(RESULT['steps']), 'first_blocker': RESULT.get('first_blocker'), 'result': str(HERE / 'RESULT.json')}))
sys.exit(0 if RESULT['status'] == 'prepared_static_identity_verified' else 2)
