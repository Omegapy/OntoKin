"""Inspect prepared blocked records without executing checks or changing source."""
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

B = Path('/workspace/scratch/c219bb61a617')
R = B / 'OntoKin'
O = B / 'integration-review'
F = R / 'docs/engineering/localized-repair-c271/finalization-20261120'
PARENT = '15b1dd985b59cf037ebbeae733c16a54ca87f83d'
CANDIDATE = '88bc8b51b3963b7072375edac6400b6e6a4532e4'
checks = []
reads = []

def sha(data):
    return hashlib.sha256(data).hexdigest()

def read(path):
    data = path.read_bytes()
    reads.append({'path': str(path), 'bytes': len(data), 'sha256': sha(data)})
    return data

def check(name, ok):
    checks.append({'name': name, 'passed': bool(ok)})

def git(*args):
    return subprocess.check_output(['git', '-C', str(R), *args])

task = json.loads(read(R / 'docs/workflow/tasks/C271/task.json'))
current = json.loads(read(R / 'docs/workflow/CURRENT.json'))
outcome = json.loads(read(F / 'PHASE-OUTCOME.json'))
old_task = json.loads(git('show', PARENT + ':docs/workflow/tasks/C271/task.json'))
summary = json.loads(read(B / 'validation/routine-candidate/summary.json'))
check('working base remains expected published checkpoint', git('rev-parse', 'HEAD').decode().strip() == PARENT)
check('task and CURRENT blocked/open on C271', task['status'] == 'blocked' and current['active_task'] == current['latest_task'] == 'C271' and current['next_action']['status'] == 'blocked')
check('R01/R02 done and R03/R04/R05 remain not_done', {x['id']: x['status'] for x in task['requirements']} == dict(R01='done', R02='done', R03='not_done', R04='not_done', R05='not_done'))
check('P01 done P02 still in_progress', {x['id']: x['status'] for x in task['plan']} == dict(P01='done', P02='in_progress'))
check('requirement acceptance text unchanged', [(x['id'], x['acceptance']) for x in task['requirements']] == [(x['id'], x['acceptance']) for x in old_task['requirements']])
named = {x['name']: x for x in task['checks']}
for old in old_task['checks']:
    new = named[old['name']]
    check('existing check requirement preserved: ' + old['name'], new['required'] == old['required'] and new['command'] == old['command'])
check('routine remains required and failed', named['required routine local driver before integration']['result'] == 'failed' and named['required routine local driver before integration']['required'] is True)
check('affected cohort accurately passed', named['complete affected observer regression before integration']['result'] == 'passed' and named['complete affected observer regression before integration']['methods'] == 282 and named['complete affected observer regression before integration']['groups'] == 12)
check('historical review is scope-limited', 'Historical P01' in named['independent candidate review']['scope'] and 'does not approve P02' in named['independent candidate review']['scope'])
check('prior phases/deliveries preserved', task['prior_session_phases'] == old_task['prior_session_phases'] and task['prior_phase_deliveries'] == old_task['prior_phase_deliveries'])
check('delivery pending partial and not asserted saved', task['delivery']['status'] == 'pending' and task['delivery']['partial'] is True and task['session_phase']['delivery_confirmed'] is False)
check('no merge or lease asserted', task['completion']['merge_commit'] is None and task['session_phase']['main_lease'] == 'not_held' and outcome['integration_performed'] is False and outcome['main_lease'] == 'not_held')
check('draft PR and open issue retained', outcome['pull_request'] == dict(number=274, state='open', draft=True) and outcome['scope_issue'] == dict(number=273, state='open') and outcome['branch_disposition'] == 'retained_unmerged')
check('exact tested source and no integration approval', outcome['source_commit'] == CANDIDATE and outcome['source_tree'] == '755f366d1091beb71b5421b14fdac0b9b868cfb0' and outcome['integration_eligible'] is False)
check('all seven routine outcomes exact', [(x['id'], x['status'], x['returncode'], x['seconds']) for x in outcome['routine']['steps']] == [(x['id'], x['status'], x['returncode'], x['duration_seconds']) for x in summary['steps']])
check('timeout has no complete count and no waiver', outcome['blocking_findings'][0]['complete_suite_count'] is None and outcome['routine']['unittest_footer_present'] is False and outcome['blocking_findings'][1]['waiver'] is False)
check('all five absent targets retained', len(outcome['blocking_findings'][1]['missing_paths']) == 5 and outcome['blocking_findings'][1]['changed_from_main'] is False and outcome['blocking_findings'][1]['baseline_execution_performed'] is False)
check('no active/unknown current operation invented', outcome['active_processes'] == [] and outcome['unknown_current_operations'] == [])
check('next action consistently defers repair and preserves per-source caps', outcome['next_action'] == task['next_action'] == current['next_action']['suggested_task'] and 'fresh chat' in task['next_action'] and '100000-operation/30000-ms' in task['next_action'])
for name in ('PLAN.md', 'REQUIREMENTS.md', 'P02-SESSION.md'):
    data = read(R / 'docs/workflow/tasks/C271' / name).decode()
    check(name + ' retains historical text before appended blocked boundary', data.startswith(git('show', PARENT + ':docs/workflow/tasks/C271/' + name).decode()))
    check(name + ' records two failures and open requirements', '21 links to five instruction files' in data and 'unit stage exceeded 900 seconds' in data and 'R03–R05 remain not_done' in data and 'No completed unit-suite total is available' in data)
learning = read(R / 'docs/workflow/tasks/C271/LEARNING-P02.md').decode()
check('scoped lesson preserves failure and no repair claim', 'demonstrated workspace-preparation defect' in learning and 'No copy repair, timeout change, dependency adjustment or behavioral replay was performed' in learning)
for name in ('ACTIVE-OPERATIONS.json', 'DOCUMENTS-FAILURE-INSPECTION.json', 'PARTIAL-UNIT-LOG-ACCOUNTING.json', 'RAW-EVIDENCE-MANIFEST.json', 'RAW-EVIDENCE-VERIFICATION.json', 'RAW-EVIDENCE.zip', 'REPORT.md', 'RESULTS.json'):
    check('canonical validation evidence equals original: ' + name, read(F / 'verification' / name) == read(B / 'validation' / name))
preflight = json.loads(read(B / 'session/blocked-record-preflight/CHECKS.json'))
check('working preflight is passed and scope-limited', preflight['passed'] is True and preflight['source_parent'] == PARENT and 'final clean published candidate' in preflight['scope'])
for step in preflight['checks']:
    data = read(B / 'session/blocked-record-preflight' / step['log'])
    check('preflight log/result exact: ' + step['name'], step['exit_code'] == 0 and sha(data) == step['sha256'])
    check('canonical preflight copy exact: ' + step['name'], read(F / 'blocked-record-preflight' / step['log']) == data)
tracked = git('diff', '--name-only', '-z', PARENT).decode().strip('\0').split('\0')
allowed = {'docs/workflow/CURRENT.json', 'docs/workflow/tasks/C271/task.json', 'docs/workflow/tasks/C271/P02-SESSION.md', 'docs/workflow/tasks/C271/PLAN.md', 'docs/workflow/tasks/C271/REQUIREMENTS.md', 'docs/engineering/localized-repair-c271/finalization-20261120/READ-SET.json'}
check('tracked delta contains only declared phase records', set(tracked) <= allowed)
untracked = git('ls-files', '--others', '--exclude-standard', '-z').decode().strip('\0').split('\0')
check('untracked delta limited to phase evidence and scoped learning', all(p.startswith('docs/engineering/localized-repair-c271/finalization-20261120/') or p == 'docs/workflow/tasks/C271/LEARNING-P02.md' for p in untracked))
report = {'schema': 'ontokin.c271.p02-blocked-working-record-review/1', 'reviewer': '/root/intake_audit', 'reviewed_at_utc': datetime.now(timezone.utc).isoformat(), 'verdict': 'passed' if all(x['passed'] for x in checks) else 'failed', 'record_readiness': 'suitable blocked partial state, subject to materializing declared review and clean published validation', 'integration_approved': False, 'parent_closure_approved': False, 'reviewed_parent': PARENT, 'working_bytes': reads, 'tracked_changes': tracked, 'untracked_changes': untracked, 'checks': checks, 'check_count': len(checks), 'failed_count': sum(not x['passed'] for x in checks), 'root_declared_pending_changes': ['Materialize independent-review directory using original report filenames', 'Correct PHASE-OUTCOME review link to independent-review/REPORT.md', 'Add separate required integration-review check with failed result and eligibility false'], 'limits': ['Working records are not an immutable published source tree', 'Preflight receipt identifies parent and logs but does not bind every working source byte; exact final clean-published record checks remain required', 'Pending intended edits are appropriate in scope but their final bytes are not yet observed', 'Library final save and receipt remain pending'], 'suggested_next_action_detail': 'Retain explicit preparation of pinned packages and historical ReadbackCPUControls dependency/host inputs in recovery instructions; do not convert predicted skips into observed skips.', 'behavioral_reexecution': False}
(O / 'BLOCKED-WORKING-RECORD-REVIEW.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'checks': len(checks), 'failed': [x for x in checks if not x['passed']], 'verdict': report['verdict']}))
