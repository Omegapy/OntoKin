"""Authorized focused-run entry point; this file is inert until explicitly run.

Install process guards before importing the candidate or any project helper.
The root records exact code, environment, command, complete logs and fixture
trees for each run. Only the focused new test module may be selected here.
"""
from contextlib import ExitStack
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch


def main():
    root = Path(__file__).resolve().parents[1] / 'OntoKin'
    retained = os.environ.get('ONTOKIN_HI_RETAIN_ROOT')
    if not retained or not Path(retained).is_absolute() or Path(retained).exists():
        raise RuntimeError('A fresh absolute ONTOKIN_HI_RETAIN_ROOT is required')
    Path(retained).mkdir(parents=True, mode=0o700)
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(root))
    selected = sys.argv[1:] or ['tests.test_current_host_inspection_v01']
    if any(name != 'tests.test_current_host_inspection_v01' and not name.startswith('tests.test_current_host_inspection_v01.HostInspectionControls.test_') for name in selected):
        raise RuntimeError('Only the bounded focused module or its exact tests are allowed')
    guards = []
    with ExitStack() as stack:
        for module, names in ((subprocess, ('Popen', 'run', 'check_output', 'call', 'check_call')),
                              (os, ('system', 'fork', 'forkpty', 'posix_spawn', 'posix_spawnp', 'kill', 'killpg', 'wait', 'waitpid', 'wait3', 'wait4'))):
            for name in names:
                if hasattr(module, name):
                    guard = stack.enter_context(patch.object(module, name, side_effect=AssertionError('Actual process operation forbidden: ' + name)))
                    guards.append((module.__name__ + '.' + name, guard))
        suite = unittest.defaultTestLoader.loadTestsFromNames(selected)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        calls = {name: guard.call_count for name, guard in guards}
        report = {'selected': selected, 'tests_run': result.testsRun, 'failures': len(result.failures),
                  'errors': len(result.errors), 'skipped': len(result.skipped),
                  'outer_process_guard_calls': calls, 'actual_project_process_operations': 0,
                  'passed': result.wasSuccessful() and not any(calls.values())}
        target = Path(retained).parent / (Path(retained).name + '-result.json')
        target.write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, sort_keys=True))
        return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
