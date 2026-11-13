#!/usr/bin/env python3
"""Check original-exception preservation when context cleanup also fails."""
import argparse
import errno
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest import mock

parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--expected-ledger-sha256', required=True)
parser.add_argument('--output', type=Path, required=True)
a = parser.parse_args()
root = a.source.resolve()
if a.output.exists():
    raise SystemExit('Fresh output required')
source = root / 'prototypes/static_tray_admission_c201/ledger.py'
sha = hashlib.sha256(source.read_bytes()).hexdigest()
if sha != a.expected_ledger_sha256:
    raise SystemExit('Source binding mismatch')
git = lambda *v: subprocess.check_output(['git', '-C', str(root), *v], text=True).strip()
commit, tree, status = git('rev-parse', 'HEAD'), git('rev-parse', 'HEAD^{tree}'), git('status', '--porcelain=v1')
sys.path.insert(0, str(root))
from prototypes.static_tray_admission_c201.ledger import Ledger
from prototypes.static_tray_admission_c201.schedule import expected_schedule
cases = []
with mock.patch('subprocess.Popen', side_effect=AssertionError('Child forbidden')), \
     mock.patch('os.fork', side_effect=AssertionError('Fork forbidden')), \
     mock.patch('os.system', side_effect=AssertionError('Shell forbidden')):
    for exception_type in (ValueError, KeyboardInterrupt):
        with tempfile.TemporaryDirectory(prefix='c231-context-review-') as temporary:
            base = Path(temporary)
            authority, output = base / 'authority', base / 'output'
            authority.mkdir()
            output.mkdir()
            ledger = Ledger.begin(authority, output, expected_schedule())
            fds = tuple(ledger._pins.values())
            raw_close = os.close
            attempts = []
            original = exception_type('Original independent context body failure')
            def lost_close_result(fd):
                raw_close(fd)
                if fd in fds:
                    attempts.append(fd)
                    raise OSError('Independent lost close reply')
            observed = None
            with mock.patch('os.close', side_effect=lost_close_result):
                try:
                    with ledger:
                        raise original
                except BaseException as exc:
                    observed = exc
            closed = []
            for fd in fds:
                try:
                    os.fstat(fd)
                except OSError as exc:
                    closed.append(exc.errno == errno.EBADF)
                else:
                    closed.append(False)
            state = ledger.snapshot()
            cases.append({'bodyException': exception_type.__name__,
                          'observedException': type(observed).__name__,
                          'originalExceptionObjectPreserved': observed is original,
                          'bothCloseAttempts': set(attempts) == set(fds) and len(attempts) == 2,
                          'pinsClosed': all(closed), 'stopped': state['stopped'],
                          'uncertain': state['persistence_or_interruption_uncertain'],
                          'complete': state['ledger_complete']})
report = {'schema': 'ontokin.c231.context-exit-review/0.1', 'sourceCommit': commit,
          'sourceTree': tree, 'sourceStatus': status, 'ledgerSha256': sha,
          'sourceUnchanged': hashlib.sha256(source.read_bytes()).hexdigest() == sha,
          'harnessSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'cases': cases, 'passed': all(c['originalExceptionObjectPreserved'] and c['bothCloseAttempts']
              and c['pinsClosed'] and c['stopped'] and c['uncertain'] and not c['complete'] for c in cases),
          'productChildStarts': 0, 'python': sys.version}
a.output.parent.mkdir(parents=True, exist_ok=True)
a.output.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'passed': report['passed'], 'cases': cases}))
raise SystemExit(0 if report['passed'] else 1)
