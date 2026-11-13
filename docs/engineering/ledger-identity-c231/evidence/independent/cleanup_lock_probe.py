#!/usr/bin/env python3
"""Bounded interrupted-cleanup-acquire seam; no descriptor-close uncertainty."""
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

p = argparse.ArgumentParser()
p.add_argument('--source', type=Path, required=True)
p.add_argument('--expected-ledger-sha256', required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
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
from prototypes.static_tray_admission_c201 import ledger as m
from prototypes.static_tray_admission_c201.schedule import LedgerError, SLOTS, expected_schedule
cases = []
with mock.patch('subprocess.Popen', side_effect=AssertionError('Child forbidden')), \
     mock.patch('os.fork', side_effect=AssertionError('Fork forbidden')), \
     mock.patch('os.system', side_effect=AssertionError('Shell forbidden')):
    for prior_failure in (False, True):
        with tempfile.TemporaryDirectory(prefix='c231-lock-review-') as temporary:
            base = Path(temporary)
            authority, output = base / 'authority', base / 'output'
            authority.mkdir()
            output.mkdir()
            ledger = m.Ledger.begin(authority, output, expected_schedule())
            fds = tuple(ledger._pins.values())
            real_lock = m._FORK_LOCK
            class InterruptedAcquire:
                calls = 0
                def acquire(self, *args, **kwargs):
                    self.calls += 1
                    if self.calls == 1:
                        raise KeyboardInterrupt('Independent interrupted cleanup lock acquisition')
                    return real_lock.acquire(*args, **kwargs)
                def release(self):
                    return real_lock.release()
                def __enter__(self):
                    self.acquire()
                    return self
                def __exit__(self, *args):
                    self.release()
            interrupted = InterruptedAcquire()
            observed = None
            with mock.patch.object(m, '_FORK_LOCK', interrupted):
                try:
                    if prior_failure:
                        slot = SLOTS[0]
                        ledger.reserve(slot.name, slot.route, 'node', references=slot.references())
                    else:
                        ledger.close()
                except BaseException as exc:
                    observed = exc
            def live():
                count = 0
                for fd in fds:
                    try:
                        os.fstat(fd)
                    except OSError as exc:
                        if exc.errno != errno.EBADF:
                            raise
                    else:
                        count += 1
                return count
            open_after_interrupt = live()
            finalizer_alive_after_interrupt = ledger._pin_finalizer.alive
            # No descriptor-close operation was attempted during the interrupted acquisition.
            # Release remaining owned handles through the public method after restoring the lock.
            ledger.close()
            remaining_after_close = live()
            current = ledger.snapshot()
            original_preserved = (isinstance(observed, LedgerError) and observed.code == 'ORDER') if prior_failure else isinstance(observed, KeyboardInterrupt)
            case = {'priorMutationFailure': prior_failure,
                    'observedException': type(observed).__name__,
                    'observedLedgerCode': getattr(observed, 'code', None),
                    'expectedExceptionPreserved': original_preserved,
                    'openPinsAfterInterruptedAcquire': open_after_interrupt,
                    'finalizerAliveAfterInterruptedAcquire': finalizer_alive_after_interrupt,
                    'remainingOpenPinsAfterPublicClose': remaining_after_close,
                    'ownershipPreservedOrAlreadyReleased': finalizer_alive_after_interrupt or open_after_interrupt == 0,
                    'stopped': current['stopped'], 'uncertain': current['persistence_or_interruption_uncertain'],
                    'complete': current['ledger_complete'],
                    'manualFixtureCleanupRequired': remaining_after_close != 0}
            # Preserve the defect observation, then prevent the fixture from leaking in this worker.
            for fd in fds:
                try:
                    os.close(fd)
                except OSError as exc:
                    if exc.errno != errno.EBADF:
                        raise
            cases.append(case)
report = {'schema': 'ontokin.c231.cleanup-lock-review/0.1', 'sourceCommit': commit,
          'sourceTree': tree, 'sourceStatus': status, 'ledgerSha256': sha,
          'sourceUnchanged': hashlib.sha256(source.read_bytes()).hexdigest() == sha,
          'harnessSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'cases': cases, 'passed': all(c['expectedExceptionPreserved'] and c['ownershipPreservedOrAlreadyReleased']
              and c['remainingOpenPinsAfterPublicClose'] == 0 and c['stopped'] and c['uncertain'] and not c['complete'] for c in cases),
          'productChildStarts': 0, 'python': sys.version}
a.output.parent.mkdir(parents=True, exist_ok=True)
a.output.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'passed': report['passed'], 'cases': cases}))
raise SystemExit(0 if report['passed'] else 1)
