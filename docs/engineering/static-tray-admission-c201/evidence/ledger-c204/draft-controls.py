"""Independent CPU probes for the first C201 ledger draft; no child starts."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
from unittest.mock import patch

ROOT = Path('/workspace/scratch/26f8cd6fa278/OntoKin')
sys.path.insert(0, str(ROOT))
from prototypes.static_tray_admission_c201 import ledger as module
from prototypes.static_tray_admission_c201.schedule import SLOTS, canonical, expected_schedule


EVIDENCE = 'a' * 64
RESULTS = []
SOURCE = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
          for p in (ROOT / 'prototypes/static_tray_admission_c201').glob('*.py')}


def begin(root):
    authority, output = root / 'authority', root / 'output'
    authority.mkdir()
    output.mkdir()
    return module.Ledger.begin(authority, output, expected_schedule()), authority


def slot_pass(ledger, slot):
    for stage in ['construction', 'receiving']:
        receipt = ledger.reserve(slot.name, slot.route, stage, references=slot.references())
        ledger.finish(receipt, 'passed', cleanup_passed=True, evidence_sha256=EVIDENCE)
    ledger.record_promotion(slot.name, slot.route, references=slot.references(),
                            outcome='passed', cleanup_passed=True,
                            conditional_promotion_passed=True, evidence_sha256=EVIDENCE)
    receipt = ledger.reserve(slot.name, slot.route, 'node', references=slot.references())
    ledger.finish(receipt, 'passed', cleanup_passed=True, evidence_sha256=EVIDENCE)


with tempfile.TemporaryDirectory(prefix='c201-review-draft-') as temp:
    root = Path(temp)
    case = root / 'structural-control'; case.mkdir()
    ledger, authority = begin(case)
    slot_pass(ledger, SLOTS[0])
    ledger.record_control('D01', source_slot='A01', outcome='passed', findings=['CLEARANCE'],
                          accepted_closure_unchanged=True, evidence_sha256=EVIDENCE)
    ledger.record_control('D03', source_slot='A01', outcome='passed', findings=['SIBLING', 'STRUCTURE'],
                          accepted_closure_unchanged=True, evidence_sha256=EVIDENCE)
    snapshot = ledger.snapshot()
    RESULTS.append({'probe': 'D03_STRUCTURE_does_not_advance',
                    'passed': snapshot['stopped'] and snapshot['next_item'] is None,
                    'observed': snapshot})

    case = root / 'interrupted-reserve'; case.mkdir()
    ledger, authority = begin(case)
    original = ledger._append
    interrupted = [False]

    def append_then_interrupt(event):
        original(event)
        if event.get('type') == 'RESERVED' and not interrupted[0]:
            interrupted[0] = True
            raise KeyboardInterrupt('controlled signal after durable append')

    with patch.object(ledger, '_append', append_then_interrupt):
        try:
            ledger.reserve('A01', 'ontokin', 'construction', references=SLOTS[0].references())
        except KeyboardInterrupt:
            pass
        first = ledger.snapshot()
        try:
            ledger.reserve('A01', 'ontokin', 'construction', references=SLOTS[0].references())
            second_rejected = False
        except module.LedgerError:
            second_rejected = True
    observed = module.inspect(authority)
    reservations = [row for row in observed['events'] if row.get('type') == 'RESERVED']
    RESULTS.append({'probe': 'interruption_poison_live_capability',
                    'passed': first['stopped'] and second_rejected and len(reservations) == 1,
                    'after_interrupt': first, 'second_reservation_rejected': second_rejected,
                    'durable_reservations': reservations})

    case = root / 'semantic-inspection'; case.mkdir()
    ledger, authority = begin(case)
    path = authority / module.JOURNAL
    first = json.loads(path.read_bytes().splitlines()[0])
    event = {'type': 'LEDGER_COMPLETE', 'native_readiness': False, 'admission_completed': False}
    body = {'sequence': 1, 'previous_sha256': first['sha256'], 'event': event}
    forged = canonical({**body, 'sha256': hashlib.sha256(canonical(body)).hexdigest()}) + b'\n'
    with path.open('ab') as out:
        out.write(forged)
    observed = module.inspect(authority)
    RESULTS.append({'probe': 'inspection_rejects_impossible_complete_event',
                    'passed': observed.get('journal_valid') is not True,
                    'observed': observed})

    for target in [module.MARKER, module.JOURNAL]:
        case = root / ('fifo-' + target); case.mkdir()
        ledger, authority = begin(case)
        path = authority / target
        path.unlink()
        os.mkfifo(path)
        received = []

        def inspect_fifo():
            received.append(module.inspect(authority))

        thread = threading.Thread(target=inspect_fifo)
        thread.start()
        thread.join(0.15)
        blocked = thread.is_alive()
        if blocked:
            descriptor = os.open(path, os.O_WRONLY | os.O_NONBLOCK)
            os.close(descriptor)
        thread.join(1.0)
        RESULTS.append({'probe': 'FIFO_kind_rejection_is_nonblocking', 'target': target,
                        'passed': not blocked and not thread.is_alive(),
                        'blocked_before_controlled_unblock': blocked, 'observed': received})

report = {'scope': 'Independent CPU-only draft review; no native readiness claim',
          'source_sha256': SOURCE, 'child_starts': 0, 'probes': RESULTS,
          'passed': all(row['passed'] for row in RESULTS)}
destination = Path(__file__).with_suffix('.json')
destination.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'report': str(destination), 'probes': len(RESULTS),
                  'passed': sum(row['passed'] for row in RESULTS), 'child_starts': 0}))
