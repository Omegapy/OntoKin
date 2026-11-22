"""Independent finite P18 review harness. Execute only after frozen identities exist."""
from pathlib import Path
from contextlib import ExitStack
from unittest.mock import patch
import argparse
import datetime
import hashlib
import importlib
import io
import json
import os
import stat
import subprocess
import sys
import time
import unittest

parser = argparse.ArgumentParser()
parser.add_argument('--repo', required=True)
parser.add_argument('--freeze', required=True)
parser.add_argument('--out', required=True)
parser.add_argument('--group', choices=('frozen', 'inherited', 'compatibility', 'all'), required=True)
args = parser.parse_args()
repo, out = Path(args.repo).resolve(), Path(args.out).resolve()
freeze = json.loads(Path(args.freeze).read_bytes())
out.mkdir(mode=0o700, parents=True, exist_ok=False)

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def put(name, value):
    path = out / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')

def identity(path):
    raw = path.read_bytes()
    return {'sha256': digest(raw), 'size_bytes': len(raw),
            'mode': oct(stat.S_IMODE(path.stat().st_mode))}

expected = {row['path']: row for row in freeze['files']}
for name, row in expected.items():
    assert identity(repo / name)['sha256'] == row['sha256'], ('candidate changed before review', name)

before = {}
for path in sorted(repo.rglob('*.py')):
    if '.git' in path.relative_to(repo).parts or '__pycache__' in path.parts:
        continue
    relative = path.relative_to(repo).as_posix()
    raw = path.read_bytes()
    before[relative] = identity(path)
    snapshot = out / 'source-snapshot' / relative
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    with snapshot.open('xb') as stream:
        stream.write(raw)
put('SOURCE-INVENTORY-BEFORE.json', before)

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
sys.dont_write_bytecode = True
for key, name in [('ONTOKIN_HI_RETAIN_ROOT', 'inherited-inspector'),
                  ('ONTOKIN_ELF_RETAIN_ROOT', 'inherited-mapping'),
                  ('ONTOKIN_LP_RETAIN_ROOT', 'inherited-origin'),
                  ('ONTOKIN_LIBC_RETAIN_ROOT', 'frozen-libc'),
                  ('TMPDIR', 'temporary')]:
    os.environ[key] = str(out / name)
(out / 'inherited-mapping').mkdir()
(out / 'temporary').mkdir()
# New adapters may use their own retained-root convention; all temporary files
# still live within this review directory, and imported fixtures are snapshotted.
import tempfile
tempfile.tempdir = str(out / 'temporary')

blocked_events = []
def audit(event, values):
    if event in {'subprocess.Popen', 'os.system', 'os.fork', 'os.forkpty',
                 'os.posix_spawn', 'os.exec', 'os.spawn', 'os.kill', 'os.killpg'}:
        blocked_events.append({'event': event, 'arguments': repr(values)[:1000]})
        raise AssertionError('Independent review forbids actual process operation: ' + event)
sys.addaudithook(audit)

sys.path[:0] = [str(repo / 'tests'), str(repo)]
modules, selected = [], []
loader = unittest.TestLoader()
if args.group in ('frozen', 'all'):
    for name in ['test_current_host_libc_plt_metadata_v01', 'test_current_host_libc_static_tls_flags_v01']:
        module = importlib.import_module(name)
        modules.append(module)
        selected.append(loader.loadTestsFromModule(module))
if args.group in ('inherited', 'all'):
    for name in ['test_current_host_inspection_v01', 'test_current_host_elf_mapping_v01',
                 'test_current_host_loader_path_v01']:
        module = importlib.import_module(name)
        modules.append(module)
        selected.append(loader.loadTestsFromModule(module))
if args.group in ('compatibility', 'all'):
    obligations = json.loads((Path(__file__).resolve().parent / 'REVIEW-OBLIGATIONS.json').read_bytes())
    for name in obligations['compatibility_selected_methods']:
        selected.append(loader.loadTestsFromName(name))

suite = unittest.TestSuite(selected)
def flatten(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item.id()
ids = list(flatten(suite))
expected_count = {'frozen': 114, 'inherited': 271, 'compatibility': 27, 'all': 412}[args.group]
assert len(ids) == expected_count and len(set(ids)) == expected_count, (len(ids), expected_count)
assert not any('test_explicit_pair_reaches_real_python_child' in value for value in ids)
assert not any('SafeArchiveInstallation' in value for value in ids)
put('REQUEST.json', {'command': sys.argv, 'cwd': str(Path.cwd()), 'repository': str(repo),
                     'group': args.group, 'method_ids': ids, 'count': len(ids),
                     'source_attribution': freeze,
                     'python': {'executable': sys.executable, 'version': sys.version},
                     'bytecode_disabled': sys.dont_write_bytecode,
                     'process_guard': 'Python audit hook installed before any product/test import',
                     'retained_environment': {key: os.environ[key] for key in
                        ('ONTOKIN_HI_RETAIN_ROOT', 'ONTOKIN_ELF_RETAIN_ROOT', 'ONTOKIN_LP_RETAIN_ROOT', 'ONTOKIN_LIBC_RETAIN_ROOT', 'TMPDIR')},
                     'not_selected': ['test_current_host_readback_driver.CurrentHostDriverBindingTests.test_explicit_pair_reaches_real_python_child_without_ambient_override',
                                      'test_current_host_readback_provider.SafeArchiveInstallation',
                                      'test_local_checks', 'original-seven/full routine', 'H0', 'H1']})
start = time.monotonic()
with (out / 'UNITTEST.log').open('x') as stream:
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)

loaded = {}
for name, module in tuple(sys.modules.items()):
    filename = getattr(module, '__file__', None)
    if filename and Path(filename).resolve().is_relative_to(repo):
        path = Path(filename).resolve()
        if path.is_file():
            relative = path.relative_to(repo).as_posix()
            loaded[name] = {'path': relative, **identity(path)}
            if path.suffix == '.py':
                assert before.get(relative) == identity(path), ('loaded source changed', relative)

after = {name: identity(repo / name) for name in before}
changes = [name for name in before if before[name] != after[name]]
put('SOURCE-INVENTORY-AFTER.json', after)
put('LOADED-REPO-MODULES.json', loaded)
report = {'started_after_source_freeze': True,
          'group': args.group, 'tests_run': result.testsRun,
          'was_successful': result.wasSuccessful(),
          'failures': [{'test': test.id(), 'traceback': trace} for test, trace in result.failures],
          'errors': [{'test': test.id(), 'traceback': trace} for test, trace in result.errors],
          'skipped': [{'test': test.id(), 'reason': reason} for test, reason in result.skipped],
          'expected_failures': len(result.expectedFailures), 'unexpected_successes': len(result.unexpectedSuccesses),
          'elapsed_seconds': time.monotonic() - start,
          'forbidden_actual_process_attempts': blocked_events,
          'source_changes_during_run': changes,
          'target_process_starts': 0,
          'operational_host_qualification': False,
          'finished_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
put('RESULT.json', report)
print(json.dumps(report, indent=2))
raise SystemExit(0 if result.wasSuccessful() and not changes and not blocked_events and not result.skipped else 1)
