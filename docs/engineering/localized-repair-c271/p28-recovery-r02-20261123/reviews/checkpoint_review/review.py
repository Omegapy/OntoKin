"""Independent read-only review of the bounded C271 P28 R02 checkpoint.

Only writes in this worker's directory. Does not execute candidate audit scripts,
product tests, Git writes, remote mutations, or a new recovery phase.
"""
from __future__ import annotations

import ast
import datetime
import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess
import sys

ROOT = Path('/workspace/scratch/002c49ccf480')
REPO = ROOT / 'OntoKin'
OUT = ROOT / 'session/reviews/checkpoint_review'
EVIDENCE = 'docs/engineering/localized-repair-c271/p28-recovery-r02-20261123'
BASE = '46b0fce68afb65cfbfcaba64f1276408d93ee85d'
MAIN = 'e43cc6c5777874101a40559e4058ad6826b07e51'
OWNER = 'c271-p28-r02-002c49ccf480'

def j(path):
    return json.loads(Path(path).read_bytes())

def git(*args):
    return subprocess.check_output(['git', *args], cwd=REPO)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def blob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()

def identity(path, relative):
    data = path.read_bytes()
    return {'path': relative, 'bytes': len(data), 'sha256': digest(data), 'git_blob': blob(data), 'mode': oct(path.stat().st_mode & 0o777)}

checks = []
def check(name, passed, detail=None):
    checks.append({'name': name, 'passed': bool(passed), 'detail': detail})

head = git('rev-parse', 'HEAD').decode().strip()
tree = git('rev-parse', 'HEAD^{tree}').decode().strip()
tracked = git('diff', '--name-only', BASE).decode().splitlines()
untracked = git('ls-files', '--others', '--exclude-standard').decode().splitlines()
paths = sorted(set(tracked + untracked))
manifest = [identity(REPO / p, p) for p in paths]
(OUT / 'CANDIDATE-MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n')
diff = git('diff', '--no-ext-diff', BASE)
(OUT / 'candidate.diff').write_bytes(diff)
check('authentic_base', head == BASE and tree == 'e5d8dc89b9e6fba4315a3386f43e13e758b33c0e', {'commit': head, 'tree': tree})
expected_tracked = {'docs/workflow/CURRENT.json', 'docs/workflow/tasks/C271/task.json', 'docs/workflow/tasks/C271/PLAN.md', 'docs/workflow/tasks/C271/REQUIREMENTS.md'}
check('bounded_documentary_files_only', set(tracked) == expected_tracked and all(p.startswith(EVIDENCE + '/') for p in untracked), {'tracked': tracked, 'new_files': len(untracked)})
check('no_staged_writes', not git('diff', '--cached', '--name-only').strip(), 'Reviewer does not change index or commits.')
for name in ['PLAN.md', 'REQUIREMENTS.md']:
    rel = 'docs/workflow/tasks/C271/' + name
    before = git('show', BASE + ':' + rel)
    after = (REPO / rel).read_bytes()
    check('append_only_' + name, after.startswith(before), {'previous_bytes': len(before), 'new_bytes': len(after)})

task = j(REPO / 'docs/workflow/tasks/C271/task.json')
old_task = json.loads(git('show', BASE + ':docs/workflow/tasks/C271/task.json'))
current = j(REPO / 'docs/workflow/CURRENT.json')
old_current = json.loads(git('show', BASE + ':docs/workflow/CURRENT.json'))
task_allowed = {'owner', 'next_action', 'session_phase', 'delivery'}
current_allowed = {'snapshot_date', 'next_action', 'latest_recovery'}
task_changed = [k for k in old_task if old_task[k] != task.get(k)]
current_changed = [k for k in old_current if old_current[k] != current.get(k)]
check('task_history_preserved', set(task_changed) == task_allowed and all(k in task for k in old_task), {'changed_fields': task_changed, 'unchanged_fields': [k for k in old_task if k not in task_allowed], 'added_fields': [k for k in task if k not in old_task]})
check('current_history_preserved', set(current_changed) == current_allowed and all(k in current for k in old_current), {'changed_fields': current_changed, 'unchanged_fields': [k for k in old_current if k not in current_allowed], 'added_fields': [k for k in current if k not in old_current]})
check('parent_acceptance_unchanged', task['requirements'] == old_task['requirements'] and task['plan'] == old_task['plan'] and task['status'] == 'blocked', {'requirements': {x['id']: x['status'] for x in task['requirements']}, 'plan': {x['id']: x['status'] for x in task['plan']}})
outcome = j(REPO / EVIDENCE / 'OUTCOME.json')
check('operative_outcome_matches_task', task['session_phase'] == outcome)
check('scope_and_completion_honest', outcome['parent_complete'] is False and outcome['phase_complete'] is False and outcome['main_lease_held'] is False and outcome['main_integration'] is False and outcome['runtime_changes'] == 0 and outcome['product_tests_executed'] == 0 and outcome['issue_state'] == 'open' and outcome['pr_state'] == 'draft_open_unmerged' and task['delivery']['status'] == 'final_save_pending')
check('missing_candidate_unknown_preserved', outcome['original_p28_implementation_verified'] is False and outcome['current_unknown_operations'] == [{'operation': 'Original P28 immutable blob/tree uploads', 'intended_parent': '360c80062e769230199602326fa8de25660df714', 'tree_sha': None, 'commit_sha': None, 'replayed': False}] and outcome['historical_unknown_operations'] == old_task['session_phase']['historical_unknown_operations'])
check('historical_reports_not_promoted', '597/597 original P28 tests' in outcome['reported_but_not_reverified'] and '945 protected files' in outcome['reported_but_not_reverified'])
check('previous_operational_fields_recoverable', task['p28_r02_prior_state_reference']['commit'] == BASE and BASE in outcome['previous_state'], 'Old current phase/delivery fields remain at the exact existing base commit and in retained historical recovery records.')
check('next_gate_consistent', task['next_action'] == current['next_action']['summary'] == outcome['next_action'] and current['next_action']['status'] == 'blocked' and current['active_task'] == 'C271')

proposal = (REPO / EVIDENCE / 'RECONSTRUCTION-OPTION.md').read_text()
adoption = j(REPO / 'docs/engineering/localized-repair-c271/required-image-design-p27/ADOPTION.json')
check('reconstruction_is_only_proposal', 'Status: proposal only. No reconstruction is authorized or started by this record.' in proposal and '116 declared obligations' in proposal and adoption['declarative_control_count'] == 116 and '105ac7c5f247fc1a01c1073266763f16e6587757' in proposal)
ownership = j(REPO / EVIDENCE / 'OWNERSHIP-READBACK.json')
check('actual_phase_ownership', ownership['id'] == outcome['ownership_comment'] == 7114912816 and OWNER in ownership['body'] and BASE in ownership['body'] and 'no main lease is held' in ownership['body'] and task['owner'] == OWNER)
check('ownership_readback_unchanged', (REPO / EVIDENCE / 'OWNERSHIP-READBACK.json').read_bytes() == (ROOT / 'session/evidence/ownership-comment.json').read_bytes())
session = j(REPO / EVIDENCE / 'SESSION.json')
check('actual_workers_recorded', session['workers'] == ['/root/artifact_audit', '/root/state_audit', '/root/checkpoint_review'] and set(session['worker_dispositions']) == set(session['workers']), session['worker_dispositions'])
check('worker_count_consistent', 'three' in session['capabilities']['independent_subagents'] or 'startup' in session['capabilities']['independent_subagents'].lower(), session['capabilities']['independent_subagents'])

early = j(REPO / EVIDENCE / 'EARLY-RECOVERY-RECEIPT.json')
save = j(ROOT / 'session/EARLY-SAVE-RESULT.json')
early_data = (ROOT / 'session/early-readback/OntoKin_C271_P28_R02_Early_Recovery_2026-11-23.zip').read_bytes()
local_early = (ROOT / 'packages/OntoKin_C271_P28_R02_Early_Recovery_2026-11-23.zip').read_bytes()
check('early_save_identity_and_byte_readback', save['status'] == 'succeeded' and save['library_file_id'] == early['library_file_id'] == 'libfile_fde3_f-98436e2b5fbc819194c15ecf6560a6d3_2ab2a24d43748191957f9bcc356b59de' and early_data == local_early and len(early_data) == early['bytes'] == 9373123 and digest(early_data) == early['sha256'] == 'dc773f0036463c58df22545339f12255c7aefc915adc571ecb70979bc6778713')
for who, count in [('artifact_audit', 1229), ('state_audit', 31)]:
    copied = REPO / EVIDENCE / 'reviews' / who
    original = ROOT / 'session/reviews' / who
    audit = j(copied / 'AUDIT.json')
    check(who + '_all_checks_recorded_pass', len(audit['checks']) == count == audit['checks_passed'] and audit['checks_failed'] == 0 and all(c['passed'] is True for c in audit['checks']))
    check(who + '_copied_evidence_exact', all(p.read_bytes() == (original / p.name).read_bytes() for p in copied.iterdir() if p.is_file()))
    ast.parse((copied / 'audit.py').read_text())

recorded_checks = j(REPO / EVIDENCE / 'checks/CHECKS.json')
check('required_documentary_checks_recorded', all(c['exit_code'] == 0 for c in recorded_checks['checks']) and {c['name'] for c in recorded_checks['checks']} == {'workflow', 'documentation', 'whitespace'} and recorded_checks['product_tests'] == 0)
check('initial_failed_check_preserved', recorded_checks['failures'][0]['exit_code'] == 1 and recorded_checks['failures'][0]['resolved'] is True and 'Workflow check failed:' in (REPO / EVIDENCE / 'checks/workflow-attempt001.txt').read_text())
check('workflow_result_supported_by_log', 'Workflow structure passed (12 tasks).' in (REPO / EVIDENCE / 'checks/workflow.stdout').read_text())
docs = j(REPO / EVIDENCE / 'checks/documentation.stdout')
check('documentation_result_supported_by_log', docs['status'] == 'passed' and docs['source_count'] == 29 and docs['links']['documents'] == 1646 and docs['links']['local_links'] == 6334 and docs['failures'] == [])
all_json = [p for p in paths if p.endswith('.json')]
for p in all_json:
    j(REPO / p)
check('all_candidate_json_parse', True, {'files': len(all_json)})

governing = []
for p in ['AGENTS.md', 'ROLE.md', 'docs/workflow/PROTOCOL.md', 'docs/workflow/HANDOFF.md', 'docs/workflow/EPHEMERAL-HOST.md']:
    row = identity(ROOT / 'session/governing' / p, p)
    row['declared_source_commit'] = MAIN
    governing.append(row)
report = {
    'schema': 'ontokin.c271.p28-r02-independent-checkpoint-review/1',
    'reviewer': '/root/checkpoint_review',
    'role': 'Independent Reviewer; no integration authority',
    'recorded_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'candidate_base': {'commit': head, 'tree': tree, 'governing_main': MAIN},
    'candidate_manifest': {'path': 'CANDIDATE-MANIFEST.json', 'sha256': digest((OUT / 'CANDIDATE-MANIFEST.json').read_bytes()), 'files': len(manifest), 'scope': 'All tracked changes and untracked candidate files present at review time; later review copies and final disposition/check evidence require final inventory reconciliation.'},
    'candidate_files': manifest,
    'tracked_diff_sha256': digest(diff),
    'governing_full_reads': governing,
    'worker_template_read': 'docs/workflow/templates/WORKER.md at candidate base',
    'command': 'python3 session/reviews/checkpoint_review/review.py',
    'environment': {'python': sys.version, 'platform': platform.platform()},
    'checks': checks,
    'checks_passed': sum(c['passed'] for c in checks),
    'checks_failed': sum(not c['passed'] for c in checks),
    'verdict': 'PASS_DOCUMENTARY_CHECKPOINT_ONLY' if all(c['passed'] for c in checks) else 'CORRECTION_REQUIRED',
    'original_implementation_accepted': False,
    'product_tests_executed_by_reviewer': 0,
    'delivery_accepted': False,
    'read_coverage': {
        'full_text': ['Complete tracked diff', 'All new Markdown documents', 'Both new audit Python scripts', 'New operative JSON, ownership readback and check logs', 'All state audit check details and metadata', 'Artifact audit metadata, substantive checks and details'],
        'machine_checked': ['All 1,229 artifact audit check records/counts/categories', 'All candidate JSON syntax', 'Every candidate file size/hash/mode', 'Both audit copies against worker originals', 'All old task/CURRENT fields for exact structural preservation except documented current-field changes'],
        'not_claimed': ['A fresh global startup', 'Live remote observations by this reviewer', 'Full semantic reread of every unchanged historical task field', 'Re-execution of product or archive audits', 'Final publication or saved-delivery validation']
    },
    'findings': [
        {'id': 'R02-REVIEW-001', 'severity': 'minor', 'topic': 'Actual worker identity/count', 'status': 'resolved' if checks[[c['name'] for c in checks].index('worker_count_consistent')]['passed'] else 'pending', 'detail': 'Initial SESSION listed only the two source auditors. Current session must include the independent checkpoint reviewer and distinguish any historical startup count. Worker completion may be recorded after this return.'}
    ],
    'remaining_director_gates': ['Copy the review evidence and mark the reviewer stopped; reconcile exact staged payload including ignored files.', 'Run applicable final documentary/workflow checks after evidence copies.', 'Conditionally publish only the documentary checkpoint on the retained branch; read back exact objects and current state.', 'Verify/freeze/save the final browser-session ZIP and prompts, then publish/save external receipt and release only this phase ownership.', 'Keep C271/issue273 open, PR274 draft/unmerged, branch retained, and original upload uncertainty unresolved; stop.'],
    'limits': ['The negative finding is bounded to inspected durable artifacts and retained live-response evidence; unreferenced original Git objects may still exist.', 'The 597/597 product-test claim remains historical and unverified.', 'A reconstruction option is not authorization and no next technical phase is selected.', 'This review does not attest future publication, save, release, or final package contents.'],
    'disposition': 'Stopped after producing review evidence; no child workers, canonical writes, remote mutations, pending writes or active jobs.'
}
(OUT / 'REVIEW.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: report[k] for k in ['verdict', 'checks_passed', 'checks_failed', 'candidate_manifest']}, indent=2))
if report['checks_failed']:
    print(json.dumps([c for c in checks if not c['passed']], indent=2))
    raise SystemExit(1)
