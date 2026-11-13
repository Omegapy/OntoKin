#!/usr/bin/env python3
"""Finite C231 independent CPU controls; new temporary authorities only."""
from __future__ import annotations
import argparse
import errno
import gc
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time
import traceback
import weakref
from contextlib import contextmanager
from unittest import mock


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--expected-ledger-sha256', required=True)
    parser.add_argument('--expect', choices=('defect', 'repair'), required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = args.source.resolve()
    output = args.output.resolve()
    if output.exists():
        raise SystemExit('Fresh output required')
    source_file = root / 'prototypes/static_tray_admission_c201/ledger.py'
    source_bytes = source_file.read_bytes()
    source_sha = hashlib.sha256(source_bytes).hexdigest()
    if source_sha != args.expected_ledger_sha256:
        raise SystemExit('Source binding mismatch')
    git = lambda *a: subprocess.check_output(['git', '-C', str(root), *a], text=True).strip()
    revision, tree, status = git('rev-parse', 'HEAD'), git('rev-parse', 'HEAD^{tree}'), git('status', '--porcelain=v1')
    sys.path.insert(0, str(root))
    from prototypes.static_tray_admission_c201 import ledger as m
    from prototypes.static_tray_admission_c201.schedule import LedgerError, SLOTS, expected_schedule
    rows, assertions = [], 0
    clock = time.monotonic()
    by_name = {slot.name: slot for slot in SLOTS}
    evidence = hashlib.sha256(b'C231 independent CPU supplied observation').hexdigest()

    def check(value, detail):
        nonlocal assertions
        assertions += 1
        if not value:
            raise AssertionError(detail)

    def rejected(operation, code=None):
        try:
            operation()
        except LedgerError as exc:
            check(code is None or exc.code == code, f'Expected {code}, observed {exc.code}')
            return exc.code
        raise AssertionError('Expected ledger rejection')

    @contextmanager
    def fresh():
        with tempfile.TemporaryDirectory(prefix='c231-independent-') as temporary:
            base = Path(temporary)
            authority, output_dir = base / 'authority', base / 'output'
            authority.mkdir()
            output_dir.mkdir()
            created = []
            raw_open = os.open
            def opened(name, flags, *a, **kw):
                fd = raw_open(name, flags, *a, **kw)
                if flags & os.O_CREAT and Path(name).name in (m.MARKER, m.JOURNAL):
                    created.append({'name': Path(name).name, 'fd': fd})
                return fd
            with mock.patch.object(m.os, 'open', side_effect=opened):
                yield authority, output_dir, created

    def begin(authority, output_dir):
        return m.Ledger.begin(authority, output_dir, expected_schedule())

    def reserve(ledger, slot='A01', stage='construction'):
        row = by_name[slot]
        return ledger.reserve(slot, row.route, stage, references=row.references())

    def finish(ledger, receipt, outcome='passed'):
        ledger.finish(receipt, outcome, cleanup_passed=True, evidence_sha256=evidence)

    def promotion(ledger, slot='A01', outcome='passed'):
        row = by_name[slot]
        ledger.record_promotion(slot, row.route, references=row.references(), outcome=outcome,
                                cleanup_passed=True, conditional_promotion_passed=True,
                                evidence_sha256=evidence)

    def complete_slot(ledger, slot='A01'):
        for stage in ('construction', 'receiving'):
            finish(ledger, reserve(ledger, slot, stage))
        promotion(ledger, slot)
        finish(ledger, reserve(ledger, slot, 'node'))

    def control(ledger, which='D01', outcome='passed'):
        ledger.record_control(which, source_slot='A01', outcome=outcome,
            findings=[{'D01': 'CLEARANCE', 'D03': 'SIBLING'}[which]],
            accepted_closure_unchanged=True, evidence_sha256=evidence)

    def open_pins(created, authority):
        check(len(created) == 2, 'Both authority files created exactly once')
        check(len({r['fd'] for r in created}) == 2, 'Live original file handles distinct')
        for row in created:
            actual = os.fstat(row['fd'])
            named = (authority / row['name']).stat()
            check((actual.st_dev, actual.st_ino) == (named.st_dev, named.st_ino), 'Original handle pins named file')
            check(not os.get_inheritable(row['fd']), 'Authority handle non-inheritable across exec')

    def closed(created):
        for row in created:
            try:
                os.fstat(row['fd'])
            except OSError as exc:
                check(exc.errno == errno.EBADF, 'Owned descriptor closed')
            else:
                raise AssertionError('Authority descriptor remains open')

    def stopped(ledger):
        check(ledger.snapshot()['stopped'], 'Stopped state visible')
        rejected(lambda: reserve(ledger), 'STOPPED')

    def record(name, fn):
        before = assertions
        try:
            detail = fn()
        except BaseException as exc:
            rows.append({'control': name, 'passed': False, 'assertions': assertions - before,
                         'errorType': type(exc).__name__, 'error': str(exc), 'traceback': traceback.format_exc()})
        else:
            rows.append({'control': name, 'passed': True, 'assertions': assertions - before, 'detail': detail})

    def replacement(name):
        with fresh() as (authority, output_dir, created):
            ledger = begin(authority, output_dir)
            if args.expect == 'repair':
                open_pins(created, authority)
            path = authority / name
            data = path.read_bytes()
            before = path.stat()
            original_identity = before.st_dev, before.st_ino
            path.unlink()
            path.write_bytes(data)
            recreated_bytes_identical = path.read_bytes() == data
            check(recreated_bytes_identical, 'Recreated authority content is exactly original bytes')
            after = path.stat()
            replacement_identity = after.st_dev, after.st_ino
            identity = m._identity
            def reused(info):
                observed = identity(info)
                return original_identity if observed == replacement_identity else observed
            held_unlinked = None
            if args.expect == 'repair':
                held = next(r['fd'] for r in created if r['name'] == name)
                held_unlinked = os.fstat(held).st_nlink
                check(held_unlinked == 0, 'Retained original is independently observed unlinked')
            with mock.patch.object(m, '_identity', side_effect=reused):
                if args.expect == 'defect':
                    receipt = reserve(ledger)
                    check(receipt.stage == 'construction', 'Baseline wrongly accepted replaced authority file')
                    check(not ledger.snapshot()['stopped'], 'Baseline incorrectly remains live')
                else:
                    rejected(lambda: reserve(ledger))
            if args.expect == 'repair':
                stopped(ledger)
                closed(created)
            elif hasattr(ledger, 'close'):
                ledger.close()
            return {'recreatedBytesIdentical': recreated_bytes_identical,
                    'originalIdentity': original_identity, 'actualReplacementIdentity': replacement_identity,
                    'numericIdentityObservationForcedEqual': True, 'retainedOriginalLinkCount': held_unlinked}

    with mock.patch('subprocess.Popen', side_effect=AssertionError('Child start forbidden')), \
         mock.patch('os.fork', side_effect=AssertionError('Fork forbidden in independent controls')), \
         mock.patch('os.system', side_effect=AssertionError('Shell forbidden')):
        for name in (m.MARKER, m.JOURNAL):
            record('forced-numeric-identity-reuse:' + name, lambda name=name: replacement(name))
        if args.expect == 'repair':
            for route in ('explicit-stop', 'invalid-order', 'stage-failed', 'promotion-failed', 'control-failed', 'complete'):
                def terminal(route=route):
                    with fresh() as (authority, output_dir, created):
                        ledger = begin(authority, output_dir)
                        open_pins(created, authority)
                        if route == 'explicit-stop':
                            ledger.stop('Independent explicit abandonment')
                        elif route == 'invalid-order':
                            rejected(lambda: reserve(ledger, 'A02'))
                        elif route == 'stage-failed':
                            finish(ledger, reserve(ledger), 'failed')
                        elif route == 'promotion-failed':
                            for stage in ('construction', 'receiving'):
                                finish(ledger, reserve(ledger, stage=stage))
                            promotion(ledger, outcome='failed')
                        else:
                            complete_slot(ledger)
                            control(ledger, outcome='failed' if route == 'control-failed' else 'passed')
                            if route == 'complete':
                                control(ledger, 'D03')
                                for slot in ('A02', 'A03', 'A04'):
                                    complete_slot(ledger, slot)
                        closed(created)
                        if route == 'complete':
                            check(ledger.snapshot()['ledger_complete'], 'Completed accounting reported')
                            rejected(lambda: reserve(ledger), 'STOPPED')
                        else:
                            stopped(ledger)
                        check(not ledger.snapshot()['native_readiness'], 'No native readiness granted')
                record('terminal-release:' + route, terminal)
            for failed_sync in range(1, 6):
                def partial(failed_sync=failed_sync):
                    with fresh() as (authority, output_dir, created):
                        raw_sync, calls = os.fsync, 0
                        def sync(fd):
                            nonlocal calls
                            calls += 1
                            if calls == failed_sync:
                                raise OSError('Independent partial-creation persistence fault')
                            return raw_sync(fd)
                        with mock.patch.object(m.os, 'fsync', side_effect=sync):
                            rejected(lambda: begin(authority, output_dir))
                        check((authority / m.MARKER).exists(), 'Partial authority retained')
                        closed(created)
                        rejected(lambda: begin(authority, output_dir), 'REPLAY')
                record('partial-begin-sync:' + str(failed_sync), partial)
            def interrupted():
                with fresh() as (authority, output_dir, created):
                    ledger = begin(authority, output_dir)
                    original = ledger._append
                    def append(event):
                        original(event)
                        raise KeyboardInterrupt('Independent interruption after durable append')
                    with mock.patch.object(ledger, '_append', side_effect=append):
                        try:
                            reserve(ledger)
                        except KeyboardInterrupt:
                            check(True, 'Original interruption preserved')
                        else:
                            raise AssertionError('Interruption swallowed')
                    closed(created)
                    stopped(ledger)
                    check(ledger.snapshot()['persistence_or_interruption_uncertain'], 'Uncertainty disclosed')
                    check(ledger.snapshot()['consumed']['construction'] == 1, 'Consumed attempt retained')
            record('interrupt-after-durable-append', interrupted)
            def dispose():
                with fresh() as (authority, output_dir, created):
                    ledger = begin(authority, output_dir)
                    reference = weakref.ref(ledger)
                    del ledger
                    gc.collect()
                    check(reference() is None, 'Cleanup does not retain Ledger object')
                    closed(created)
                    check(m.inspect(authority)['consumed'], 'Disposal preserves consumed authority')
            record('garbage-collection-release', dispose)
            def idempotent():
                with fresh() as (authority, output_dir, created):
                    ledger = begin(authority, output_dir)
                    ledger.close()
                    closed(created)
                    stopped(ledger)
                    sentinel = os.open(authority.parent / 'caller-file', os.O_WRONLY | os.O_CREAT, 0o600)
                    try:
                        ledger.close()
                        check(os.fstat(sentinel).st_nlink == 1, 'Repeated close preserves caller fd even if number reused')
                    finally:
                        os.close(sentinel)
            record('idempotent-close-preserves-unrelated-fd', idempotent)
            def process_guard():
                with fresh() as (authority, output_dir, created):
                    ledger = begin(authority, output_dir)
                    class InheritedMutex:
                        def __enter__(self):
                            raise AssertionError('Inherited locked mutex touched before process rejection')
                        def __exit__(self, *a):
                            return False
                    ledger._mutex = InheritedMutex()
                    with mock.patch.object(m.os, 'getpid', return_value=os.getpid() + 1):
                        rejected(lambda: reserve(ledger), 'STOPPED')
                    closed(created)
            record('process-identity-before-inherited-lock', process_guard)
    final_source_sha = hashlib.sha256(source_file.read_bytes()).hexdigest()
    check(final_source_sha == source_sha, 'Source stayed unchanged')
    report = {'schema': 'ontokin.c231.independent-controls/0.1', 'expectation': args.expect,
              'source': str(root), 'sourceCommit': revision, 'sourceTree': tree, 'sourceStatus': status,
              'ledgerSha256': source_sha, 'sourceUnchanged': source_sha == final_source_sha,
              'harnessSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'python': sys.version, 'platform': platform.platform(), 'elapsedSeconds': time.monotonic() - clock,
              'controls': rows, 'controlCount': len(rows), 'assertionCount': assertions,
              'passed': all(row['passed'] for row in rows), 'productChildStarts': 0,
              'provenanceGitCommandsBeforeControls': 3,
              'meaning': 'Controlled CPU observations; no aggregate, native start or admission authority'}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('passed', 'controlCount', 'assertionCount', 'elapsedSeconds')}))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
