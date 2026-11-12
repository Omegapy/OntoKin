"""Run the predefined C210 affected gate against an immutable actual-main checkout."""
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import unittest

ROOT = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2]).resolve()
OUT.mkdir(exist_ok=True, parents=True)
os.chdir(ROOT)
sys.dont_write_bytecode = True
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
sys.path[:0] = [str(ROOT / 'tests'), str(ROOT)]
def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()
def identity(path):
    raw = path.read_bytes()
    return {'bytes': len(raw), 'sha256': 'sha256:' + hashlib.sha256(raw).hexdigest()}
def flatten(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item
inventory_path = ROOT / 'docs/engineering/semantic-export-c210/evidence/independent-review/AFFECTED-REGRESSION.json'
inventory = json.loads(inventory_path.read_text())
modules = inventory['modules'] + [inventory['new_sidecar_module']]
expected = sorted(test['test_id'] for module in modules for test in module['tests'])
before = {'head': git('rev-parse', 'HEAD'), 'tree': git('rev-parse', 'HEAD^{tree}'), 'status': git('status', '--porcelain')}
assert before['head'] == 'adfb43c5ab1d7750abfa5e5c74ab62e18a6879e7' and not before['status'], before
eligible_paths = ['ontokin', 'tests', 'tools', 'examples', 'fixtures', 'docs/language-design', '.github', 'pyproject.toml']
changed = git('diff', '--name-only', '7feb0dc501d3a6995732637f38c3c3b651914f4b', 'HEAD', '--', *eligible_paths)
assert not changed, changed
bindings = [{'path': m['path'], 'expected': m['sha256'], 'actual': identity(ROOT / m['path'])['sha256']} for m in modules]
assert all(x['expected'] == x['actual'] for x in bindings)
loader = unittest.TestLoader()
suite = loader.loadTestsFromNames([Path(m['path']).stem for m in modules])
actual = sorted(t.id().removeprefix('tests.') for t in flatten(suite))
assert not loader.errors and actual == expected, {'loader_errors': loader.errors, 'missing': sorted(set(expected)-set(actual)), 'extra': sorted(set(actual)-set(expected))}
events = []
class BoundResult(unittest.TextTestResult):
    def startTest(self, test):
        self.started = time.monotonic()
        super().startTest(test)
    def record(self, test, status):
        events.append({'test_id': test.id().removeprefix('tests.'), 'status': status, 'seconds': round(time.monotonic()-getattr(self, 'started', time.monotonic()), 6)})
    def addSuccess(self, test):
        self.record(test, 'passed'); super().addSuccess(test)
    def addError(self, test, err):
        self.record(test, 'error'); super().addError(test, err)
    def addFailure(self, test, err):
        self.record(test, 'failed'); super().addFailure(test, err)
    def addSkip(self, test, reason):
        self.record(test, 'skipped'); super().addSkip(test, reason)
    def addExpectedFailure(self, test, err):
        self.record(test, 'expected_failure'); super().addExpectedFailure(test, err)
    def addUnexpectedSuccess(self, test):
        self.record(test, 'unexpected_success'); super().addUnexpectedSuccess(test)
started = time.monotonic()
with (OUT / 'affected-tests.log').open('w') as stream:
    result = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=BoundResult).run(suite)
tests_ok = result.wasSuccessful() and result.testsRun == len(expected) and sorted(x['test_id'] for x in events) == expected and all(x['status'] == 'passed' for x in events)
tests = {'passed': tests_ok, 'required': len(expected), 'tests_run': result.testsRun, 'seconds': round(time.monotonic()-started, 6), 'events': events, 'module_bindings': bindings, 'inventory': identity(inventory_path), 'log': identity(OUT / 'affected-tests.log')}
(OUT / 'affected-results.json').write_text(json.dumps(tests, indent=2)+'\n')
steps = []
for name, args in [('core', ['-m', 'ontokin', 'conformance', '--output', str(OUT / 'core.json')]), ('documentation', ['docs/maintenance/reorganization-2026-10-17/verify_reorganization.py'])]:
    command = [sys.executable, '-B', *args]
    began = time.monotonic()
    with (OUT / (name+'.log')).open('w') as stream:
        process = subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, timeout=900)
    steps.append({'name': name, 'command': command, 'returncode': process.returncode, 'seconds': round(time.monotonic()-began, 6), 'log': identity(OUT / (name+'.log'))})
after = {'head': git('rev-parse', 'HEAD'), 'tree': git('rev-parse', 'HEAD^{tree}'), 'status': git('status', '--porcelain')}
stable = before == after and all(identity(ROOT / x['path'])['sha256'] == x['actual'] for x in bindings)
summary = {'schema': 'ontokin.c210.actual-main-checks/0.1', 'passed': tests_ok and stable and all(s['returncode'] == 0 for s in steps), 'before': before, 'after': after, 'source_stable': stable, 'eligible_paths': eligible_paths, 'eligible_diff_from_executed_candidate': changed, 'affected': {'required': len(expected), 'passed': sum(x['status']=='passed' for x in events), 'seconds': tests['seconds']}, 'steps': steps, 'environment': {'python': sys.version, 'platform': platform.platform(), 'bytecode_writes': False}, 'limitations': ['Actual affected development scope only; the separate broad driver remains failed.', 'No new receiver or native admission executed; artifact/browser evidence reused only through exact input equality.']}
(OUT / 'SUMMARY.json').write_text(json.dumps(summary, indent=2)+'\n')
print(json.dumps(summary, indent=2), flush=True)
raise SystemExit(0 if summary['passed'] else 1)
