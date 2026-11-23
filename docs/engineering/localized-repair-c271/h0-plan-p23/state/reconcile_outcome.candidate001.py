"""Record the reviewed P23 endpoint without changing executable project behavior."""
from pathlib import Path
import datetime
import hashlib
import json
import shutil

BASE = Path('/workspace/scratch/f8d879d19e34')
REPO = BASE / 'OntoKin'
WORK = BASE / 'phase-p23'
REL = 'docs/engineering/localized-repair-c271/h0-plan-p23'
DEST = REPO / REL
START = '51a00f21013386df6ee4ce3c3560c902b32c6af5'
FROZEN = '527368bd5195c439762b43e2cc836ff9822213f8'

def read(path):
    return json.loads(path.read_text())

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')

def descriptor(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

reviews = sorted((WORK / 'reviews/h0').glob('*BLOCKER*REVIEW.json'))
assert len(reviews) == 1, [str(p) for p in reviews]
review_path = reviews[0]
review = read(review_path)
assert 'H0-RTLD-ABSENT-PARENT-001' in review_path.read_text()
assert 'confirmed' in str(review.get('verdict', ''))
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
review_rel = REL + '/reviews/h0/' + review_path.name

phase_path = WORK / 'state/PHASE.json'
phase = read(phase_path)
declaration = WORK / 'state/PHASE-DECLARATION.json'
assert not declaration.exists()
shutil.copyfile(phase_path, declaration)
current_path = REPO / 'docs/workflow/CURRENT.json'
shutil.copyfile(current_path, WORK / 'state/CURRENT.initial-candidate.json')
phase.update({
    'status': 'technical_boundary_reached_documentary_delivery_pending',
    'technical_phase_complete': True, 'phase_complete': False,
    'technical_stop_at_utc': now,
    'technical_outcome': 'H0-RTLD-ABSENT-PARENT-001',
    'h0_accepted': False, 'h0_plan_accepted': False,
    'independent_endpoint_review': review_rel,
    'delivery_state': 'final_save_pending',
    'next_action': 'Complete documentary review/checks, conditional retained-branch publication and verified handoff with separate receipt; no further technical work in this chat.',
    'next_fresh_phase': 'Review a bounded versioned representation for absent loader-candidate ancestors and parent-traversing loader aliases, or retain the existing refusal. No implementation is selected in P23.',
    'date_convention': 'User-facing date 2026-11-22 America/Denver; recorded evidence timestamps use UTC.',
    'actual_execution_counts': {'raw_observation_python_processes': 2, 'public_H0_inspector': 0, 'H1': 0, 'Node': 0, 'ldd': 0, 'direct_loader': 0, 'original_CPU_checkers': 0, 'product_tests': 0, 'preparer': 0, 'package_installations': 0},
    'acceptance_state': {'A01': 'passed', 'A02': 'passed', 'A03': 'passed_blocker_independently_confirmed', 'A04': 'pending', 'A05': 'pending'},
})
for worker in phase['workers']:
    worker['status'] = 'Technical assignments stopped; documentary review or final package review only'
write(phase_path, phase)

outcome = {
    'schema': 'ontokin.c271.p23-outcome/1', 'phase': phase['phase'],
    'recorded_at_utc': now, 'status': 'blocked_H0_plan_technical_boundary_reached',
    'technical_phase_complete': True, 'phase_complete': False, 'parent_complete': False,
    'owner': phase['owner'], 'starting_branch_revision': START,
    'frozen_implementation': {'commit': FROZEN, 'tree': 'e8844be5189b65d1bc17af40861fac672b189b25', 'path': 'prototypes/static_tray_v01/current_host_inspection_v01.py', 'sha256': 'e14542e45deb200bb97f2a591c94bdd19916a1d33dcb3ce9f631816b98e0c206', 'bytes': 196305},
    'primary_blocker': {
        'id': 'H0-RTLD-ABSENT-PARENT-001',
        'observed': 'The mandatory literal /usr/bin/ldd RTLDLIST contains /libx32/ld-linux-x32.so.2; both this candidate and immediate parent /libx32 were absent in two matching metadata observations.',
        'required': 'The closed absent-candidate row requires parent == str(path.parent), path.parent.is_dir(), not path.exists(), and not path.is_symlink(). The full ordered literal candidate list must be declared.',
        'consequence': 'No admitted file or absent row can represent this required path under the unchanged implementation. Omitting the candidate would violate the literal-list binding.',
        'classification': 'Independently confirmed source-backed plan-representation blocker; no public H0 inspector was invoked and no runtime refusal is claimed.',
    },
    'related_constraint_from_same_observation': {
        'observed_path': '/lib64/ld-linux-x86-64.so.2',
        'observed_symlink_target': '../lib/x86_64-linux-gnu/ld-linux-x86-64.so.2',
        'required': 'The unchanged _existing_chain rejects any symlink target with a .. path component.',
        'consequence': 'The mandatory loader alias also needs an explicit future traversal-model decision; no diagnostic ordering or additional runtime test is inferred.',
    },
    'actual_observations': [
        {'name': 'necessary Python/libc/loader pins', 'result': 'all three exact SHA-256/size/mode tuples matched', 'returncode': 0, 'evidence': REL + '/readiness/run001.stdout.json', 'review': REL + '/reviews/h0/READINESS-OUTCOME-REVIEW.json'},
        {'name': 'current ldd literal candidates and immediate parents', 'result': 'bounded raw observation completed; first concrete plan blocker identified', 'returncode': 0, 'evidence': REL + '/readiness/ldd001.stdout.json', 'review': review_rel},
    ],
    'recovered_input_evidence': {
        'source': 'Fresh ordinary Git checkout at the frozen commit/tree; all 626 execution source files exactly match the preserved inventory; clean status.',
        'portable_inputs': 'Exact Node archive and P21 archive/seven wheel payloads available and hash verified. C195 source archive is materialized at its frozen Git path. No current installation or H0 receipt was created.',
        'history': 'Original P22 source object and installation receipts remain unchanged historical evidence. Current paths are disposable and never serve as old-host recovery instructions.',
    },
    'independent_review': {'repository_path': review_rel, **descriptor(review_path)},
    'execution_counts': phase['actual_execution_counts'],
    'h0_plan_accepted': False, 'h0_accepted': False,
    'requirements': phase['requirements'], 'parent_plan': phase['parent_plan'],
    'branch': phase['branch'], 'pr': phase['pr'], 'issue': phase['issue'],
    'main_lease_held': False, 'main_integration': False,
    'current_unknown_operations': [], 'historical_unknown_operations': phase['historical_unknown_operations'],
    'preserved_failures': 'All 75 prior check records remain unchanged. Reviewer denominator/anchor/import-list corrections and initial documentary candidate defects remain in evidence; none is relabeled a product-test failure or pass.',
    'delivery': {'state': 'pending', 'future_external_receipt': REL + '/P23-DELIVERY.json'},
    'next_action_this_chat': phase['next_action'], 'first_remaining_action_fresh_chat': phase['next_fresh_phase'],
}
write(WORK / 'state/OUTCOME.json', outcome)
write(WORK / 'state/LEARNING-DECISION.json', {
    'schema': 'ontokin.c271.p23-learning/1',
    'decision': 'Retain the exact path-representation finding as task evidence; no general workflow-policy or skill edit in this phase.',
    'reason': 'This is a narrow existing inspector-contract limitation. Any new path semantics require a separately selected design, independent review and controls. Main already contains the mandatory disposable-host rule.',
    'source': review_rel,
})

# Copy unique current-session evidence. Derived extraction trees and runtime inputs are excluded.
for folder in ('readiness', 'reviews', 'state'):
    source = WORK / folder
    for path in sorted(source.rglob('*')):
        if not path.is_file() or any('extraction' in x or x == '__pycache__' for x in path.relative_to(source).parts):
            continue
        if path.name == 'inspection-source.py':
            continue
        target = DEST / folder / path.relative_to(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
for name in ('PHASE.json', 'OUTCOME.json', 'LEARNING-DECISION.json', 'EARLY-RECOVERY-RECEIPT.json'):
    shutil.copyfile(WORK / 'state' / name, DEST / name)
shutil.copyfile(BASE / 'input/OntoKin/OntoKin_C271_P22_Ephemeral_Host_Amendment_Delivery_Receipt_2026-11-22.json', DEST / 'state/P22-AMENDMENT-DELIVERY.json')

task_path = REPO / 'docs/workflow/tasks/C271/task.json'
task = read(task_path)
assert all(c['name'] != 'P23 necessary image-pin observation' for c in task['checks'])
task['prior_phase_deliveries'].append(task['delivery'])
task['prior_h0_constraints'].append(task['remaining_h0_constraint'])
task['remaining_h0_constraint'] = {
    'status': 'H0-RTLD-ABSENT-PARENT-001', 'evidence': review_rel,
    'source_commit': FROZEN, 'h0_accepted': False,
    'next_phase_action': phase['next_fresh_phase'],
    'related_observed_constraint': outcome['related_constraint_from_same_observation'],
    'prior_source_objects': 'Preserved unchanged in prior_h0_constraints and P22 evidence; do not probe historical temporary paths.',
}
task['blocked_reason'] = outcome['primary_blocker']['observed'] + ' ' + outcome['primary_blocker']['consequence']
task['next_action'] = phase['next_action']
task['session_phase'].update({
    'status': phase['status'], 'technical_phase_complete': True, 'phase_complete': False,
    'technical_outcome': outcome['primary_blocker']['id'], 'h0_plan_accepted': False,
    'h0_accepted': False, 'outcome': REL + '/OUTCOME.json', 'independent_review': review_rel,
    'source_revision': START, 'frozen_implementation_revision': FROZEN,
})
task['delivery'] = {
    'required': True, 'kind': 'browser-session', 'folder': 'OntoKin', 'partial': True,
    'phase': phase['phase'], 'status': 'final_save_pending', 'phase_complete': False,
    'technical_phase_complete': True, 'early_receipt': REL + '/EARLY-RECOVERY-RECEIPT.json',
    'future_external_receipt': REL + '/P23-DELIVERY.json', 'source_snapshot_before_save': True,
}
task['checks'] += [
    {'name': 'P23 necessary image-pin observation', 'command': 'One independently reviewed READINESS-LAUNCH.json through exclusive capture', 'result': 'passed', 'required': True, 'evidence': [REL + '/readiness/run001.capture.json', REL + '/readiness/run001.stdout.json', REL + '/reviews/h0/READINESS-OUTCOME-REVIEW.json'], 'scope': 'Three necessary exact pins only; no H0 acceptance'},
    {'name': 'P23 raw ldd path observation and independent blocker review', 'command': 'One independently reviewed LDD-CANDIDATE-LAUNCH.json through exclusive capture; no ldd execution', 'result': 'passed', 'required': True, 'evidence': [REL + '/readiness/ldd001.capture.json', REL + '/readiness/ldd001.stdout.json', review_rel], 'scope': 'Raw observation/review passed and confirmed a blocker. No public H0 pass or refusal claimed'},
]
write(task_path, task)

current = read(current_path)
current['snapshot_date'] = now
current['next_action'] = {'status': 'blocked', 'summary': task['blocked_reason'] + ' P23 technical work stopped; documentary delivery only.', 'suggested_task': 'Complete P23 delivery, then a fresh bounded loader-path design decision', 'sources': ['docs/workflow/tasks/C271/task.json', REL + '/OUTCOME.json', review_rel]}
current['older_handoffs'].append(current['latest_handoff'])
amendment = read(DEST / 'state/P22-AMENDMENT-DELIVERY.json')
current['latest_handoff'] = {**amendment['new_files'][0], 'phase': 'P22 ephemeral-host documentary amendment', 'source_snapshot_before_P23_save': True, 'receipt': REL + '/state/P22-AMENDMENT-DELIVERY.json', 'matching_prompts': amendment['new_files'][1:]}
current['older_recoveries'].append(current['latest_recovery'])
current['latest_recovery'] = {'phase': phase['phase'], 'receipt': REL + '/EARLY-RECOVERY-RECEIPT.json', 'confirmed_saved_and_read_back': True}
current['pending_phase_delivery'] = {'phase': phase['phase'], 'technical_phase_complete': True, 'phase_complete': False, 'future_external_receipt': REL + '/P23-DELIVERY.json'}
write(current_path, current)

ending = '''
### P23 technical endpoint

The independently reviewed raw observations confirmed `H0-RTLD-ABSENT-PARENT-001`. The fixed `ldd` literal list includes `/libx32/ld-linux-x32.so.2`, while its immediate parent `/libx32` is absent. The frozen inspector requires an existing immediate parent for an absent-candidate row. The same observation retains the required `/lib64/ld-linux-x86-64.so.2` alias with a `../lib/...` target, which the existing guard traversal rejects. These are source-backed plan constraints; no public H0 inspector or runtime refusal was observed.

All three preliminary Python/libc/loader pins matched. The frozen source and exact Node/P21 portable inputs were recovered and verified, but no installer, package installation, Node, ldd, direct loader, H1, original CPU checker or full routine ran. Technical work stopped at the first blocking observation. See [outcome](../../../engineering/localized-repair-c271/h0-plan-p23/OUTCOME.json).

Finish only documentary review/checks, conditional publication on the retained branch and verified saved handoff with separate receipt, then stop. In a fresh chat, select a bounded design/review decision for the two required path shapes, or retain the refusal; P23 changes no product code, tests, pins or contracts. R01/R02 remain done, R03-R05 not_done, P02 in_progress; PR274 remains draft/unmerged and issue273 open. User-facing date is November 22, 2026 in America/Denver; evidence timestamps use UTC.
'''
for name in ('REQUIREMENTS.md', 'PLAN.md', 'P23-SESSION.md'):
    path = REPO / 'docs/workflow/tasks/C271' / name
    path.write_text(path.read_text() + ending)

(DEST / 'README.md').write_text('''# C271 P23 current-host H0 plan checkpoint

H0 remains unaccepted. The first blocking observation exposed an absent immediate loader-candidate parent under the frozen plan format. The same observation preserved a mandatory parent-traversing loader alias rejected by the existing path guards. No product code or contract changed.

The [outcome](OUTCOME.json), [phase](PHASE.json) and independent review in `reviews/h0` distinguish exact observations from source-backed conclusions. `readiness` retains both reviewed one-shot collectors, their launch plans, raw stdout/stderr and exclusive capture records. These scripts are historical evidence; a fresh chat must not execute their old absolute paths.

The current Python, libc and loader pins matched. All 626 frozen source files matched the preserved source inventory; exact Node and P21 archives and seven wheel payloads were verified. No current installation receipt, complete H0 plan, H1 observation or product-test pass resulted.

The parent remains open with R03-R05 unmet. Only documentary review/publication and verified delivery remain in this chat. The next fresh bounded phase is a design/review decision for the missing-parent and parent-traversing-alias representations, or an explicit decision to retain refusal. The [early receipt](EARLY-RECOVERY-RECEIPT.json) confirms recovery was saved before technical work. A separate P23 delivery receipt will resolve this pre-save checkpoint without rewriting its history.
''')
print(json.dumps({'outcome': str(DEST / 'OUTCOME.json'), 'review': review_rel, 'task_check_count': len(task['checks']), 'technical_work_stopped': True}))
