#!/usr/bin/env python3
"""Run the selected C231 affected cohort with complete method accounting."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import unittest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    root = options.repo.resolve()
    output = options.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    os.chdir(root)
    sys.path.insert(0, str(root))
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=root, text=True).strip()
    def identity():
        files = git('ls-files').splitlines()
        return {'commit': git('rev-parse', 'HEAD'), 'tree': git('rev-parse', 'HEAD^{tree}'),
                'status': git('status', '--porcelain', '--untracked-files=all'),
                'file_sha256': {name: hashlib.sha256((root/name).read_bytes()).hexdigest()
                                for name in files if (root/name).is_file()}}
    before = identity()
    (output/'source-before.json').write_text(json.dumps(before, indent=2)+'\n')
    loader = unittest.TestLoader()
    suite = unittest.TestSuite([
        loader.discover(str(root/'tests'), pattern='test_static_tray_admission_c201_*.py'),
        loader.discover(str(root/'tests'), pattern='test_static_tray_admission_c231_ledger_identity.py')])
    def flatten(tests):
        for item in tests:
            if isinstance(item, unittest.TestSuite):
                yield from flatten(item)
            else:
                yield item
    inventory = [test.id() for test in flatten(suite)]
    (output/'inventory.json').write_text(json.dumps(inventory, indent=2)+'\n')
    states = {test_id: 'unrun' for test_id in inventory}
    events = []
    started = time.monotonic()
    class Result(unittest.TextTestResult):
        def startTest(self, test):
            states[test.id()] = 'running'
            super().startTest(test)
        def addSuccess(self, test):
            states[test.id()] = 'passed'
            super().addSuccess(test)
        def addFailure(self, test, err):
            states[test.id()] = 'failed'
            super().addFailure(test, err)
        def addError(self, test, err):
            if test.id() in states:
                states[test.id()] = 'error'
            events.append({'kind': 'error' if test.id() in inventory else 'setup_or_import_error',
                           'id': test.id(), 'exception': type(err[1]).__name__, 'message': str(err[1])})
            super().addError(test, err)
        def addSkip(self, test, reason):
            states[test.id()] = 'skipped'
            events.append({'kind': 'skip', 'id': test.id(), 'reason': reason})
            super().addSkip(test, reason)
        def addExpectedFailure(self, test, err):
            states[test.id()] = 'expected_failure'
            super().addExpectedFailure(test, err)
        def addUnexpectedSuccess(self, test):
            states[test.id()] = 'unexpected_success'
            super().addUnexpectedSuccess(test)
        def addSubTest(self, test, subtest, err):
            if err:
                states[test.id()] = 'failed' if issubclass(err[0], test.failureException) else 'error'
                events.append({'kind': 'subtest_failure' if issubclass(err[0], test.failureException) else 'subtest_error',
                               'id': subtest.id(), 'parent': test.id(),
                               'exception': type(err[1]).__name__, 'message': str(err[1])})
            super().addSubTest(test, subtest, err)
    run_result = None
    error = None
    with (output/'unittest.log').open('w') as stream:
        try:
            run_result = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=Result).run(suite)
        except BaseException as exc:
            error = {'type': type(exc).__name__, 'message': str(exc)}
        finally:
            after = identity()
            (output/'source-after.json').write_text(json.dumps(after, indent=2)+'\n')
            counts = {value: sum(state == value for state in states.values()) for value in
                      ['passed','failed','error','skipped','expected_failure','unexpected_success','unrun','running']}
            report = {'schema': 'ontokin.c231.affected-cpu-checks/0.1', 'command': sys.argv,
                      'python': sys.version, 'executable': sys.executable, 'platform': platform.platform(),
                      'elapsed_seconds': time.monotonic()-started, 'inventory_methods': len(inventory),
                      'unique_inventory_methods': len(set(inventory)), 'executed_methods': run_result.testsRun if run_result else None,
                      'counts': counts, 'events': events, 'method_outcomes': states,
                      'runner_exception': error, 'run_completed': run_result is not None,
                      'source_unchanged': before == after, 'commit': before['commit'], 'tree': before['tree'],
                      'source_clean_before_after': not before['status'] and not after['status'],
                      'passed': bool(run_result and run_result.wasSuccessful() and all(s=='passed' for s in states.values()) and before==after)}
            (output/'RESULT.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['method_outcomes','events','command']}, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
