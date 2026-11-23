"""Record actual post-freeze saves while leaving terminal confirmation explicit."""
from pathlib import Path
import datetime
import hashlib
import json
import shutil
import subprocess

BASE = Path('/workspace/scratch/f8d879d19e34')
REPO = BASE / 'OntoKin'
WORK = BASE / 'phase-p23'
REL = 'docs/engineering/localized-repair-c271/h0-plan-p23'
DEST = REPO / REL

def read(path):
    return json.loads(path.read_text())

def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n')

assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip() == '182d36d957d93161e351f41839bf2a6157fed3df'
assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=REPO)
saves = read(WORK / 'state/FINAL-SAVE-RECEIPTS.json')
assert saves['saved_and_readback_verified'] and len(saves['files']) == 3
audit_path = WORK / 'reviews/archive/final-package/FINAL-ARCHIVE-REVIEW.json'
audit = read(audit_path)
assert audit['verdict'] == 'ACCEPTED_FOR_SAVE' and not audit['failures']
assert saves['files'][0]['sha256'] == '241e31741879b81eaa85c9705941f282347ab3cebf9db60bc08dd7cd52aa8761'
post = DEST / 'postfreeze'
post.mkdir(exist_ok=False)
for name in ('FINAL-IDENTITY.json', 'FINAL-UPLOAD-INTENT.json', 'FINAL-UPLOAD-RESULT.json',
             'FINAL-UPLOAD.stderr.log', 'FINAL-MATERIALIZE-METADATA.json',
             'FINAL-READBACK-INCIDENT.json', 'FINAL-SAVE-RECEIPTS.json',
             'CORE-PUBLICATION.json', 'PUBLICATION-PREP-INCIDENT.json'):
    shutil.copyfile(WORK / 'state' / name, post / name)
for path in (WORK / 'reviews/archive/final-package').iterdir():
    if path.is_file():
        target = post / 'final-package-review' / path.name
        target.parent.mkdir(exist_ok=True)
        shutil.copyfile(path, target)
shutil.copytree(WORK / 'checks/published-core', post / 'published-core-checks')

task_path = REPO / 'docs/workflow/tasks/C271/task.json'
task = read(task_path)
old_delivery = task['delivery']
receipt = {
    'schema': 'ontokin.c271.p23-delivery/1', 'phase': task['session_phase']['phase'],
    'status': 'zip_and_prompts_saved_verified_terminal_receipt_pending',
    'recorded_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'confirmed_at_utc': saves['confirmed_at_utc'],
    'technical_phase_complete': True, 'phase_complete': False, 'parent_complete': False,
    'source_commit': saves['source_commit'], 'source_tree': saves['source_tree'],
    'archive': saves['files'][0], 'matching_prompts': saves['files'][1:],
    'early_receipt': REL + '/EARLY-RECOVERY-RECEIPT.json',
    'independent_package_review': {
        'path': REL + '/postfreeze/final-package-review/FINAL-ARCHIVE-REVIEW.json',
        'sha256': hashlib.sha256(audit_path.read_bytes()).hexdigest(),
        'checks_passed': 931, 'verdict': audit['verdict'],
    },
    'published_core_checks': REL + '/postfreeze/published-core-checks/RESULT.json',
    'source_snapshot_before_save': old_delivery,
    'readback_guard_incident': REL + '/postfreeze/FINAL-READBACK-INCIDENT.json',
    'current_unknown_operations': [],
    'h0_plan_accepted': False, 'h0_accepted': False, 'main_integration': False,
    'requirements': {'R01': 'done', 'R02': 'done', 'R03': 'not_done', 'R04': 'not_done', 'R05': 'not_done'},
    'branch': task['branch'], 'pr': {'number': 274, 'state': 'open', 'draft': True, 'merged': False},
    'issue': {'number': 273, 'state': 'open'}, 'main_lease_held': False,
    'external_receipt_file_name': 'OntoKin_C271_P23_Delivery_Receipt_2026-11-22.json',
    'receipt_publication': 'Pending conditional receipt commit/readback and separately saved external receipt at this source snapshot.',
    'terminal_resolution': 'Only the separately saved exact P23 receipt and matching live PR274/issue273 P23 terminal markers can resolve remaining delivery-only pending fields. Their ZIP hash, core source commit, receipt commit and receipt identity must agree. They cannot accept H0 or complete C271.',
    'next_action': 'Finish receipt-only review/checks/publication, save the separate actual receipt, verify it and publish/read back matching terminal markers; then stop. No technical work or second phase.',
}
write(DEST / 'P23-DELIVERY.json', receipt)
task['delivery'] = {
    'required': True, 'kind': 'browser-session', 'folder': 'OntoKin', 'partial': True,
    'phase': receipt['phase'], 'status': receipt['status'], 'technical_phase_complete': True,
    'phase_complete': False, 'early_receipt': receipt['early_receipt'],
    'receipt': REL + '/P23-DELIVERY.json', 'archive': receipt['archive'],
    'matching_prompts': receipt['matching_prompts'], 'source_revision': receipt['source_commit'],
    'source_tree': receipt['source_tree'], 'source_snapshot_before_save': old_delivery,
    'receipt_publication': receipt['receipt_publication'], 'terminal_resolution': receipt['terminal_resolution'],
}
task['session_phase'].update({'status': receipt['status'], 'phase_complete': False,
                              'technical_phase_complete': True, 'delivery_receipt': REL + '/P23-DELIVERY.json'})
task['next_action'] = receipt['next_action']
task['completion']['evidence'].append(REL + '/P23-DELIVERY.json')
write(task_path, task)

current_path = REPO / 'docs/workflow/CURRENT.json'
current = read(current_path)
if current.get('previous_handoff'):
    current['older_handoffs'].append(current['previous_handoff'])
current['previous_handoff'] = current['latest_handoff']
current['latest_handoff'] = {
    **receipt['archive'], 'phase': receipt['phase'], 'partial': True,
    'source_revision': receipt['source_commit'], 'source_tree': receipt['source_tree'],
    'receipt': REL + '/P23-DELIVERY.json', 'matching_prompts': receipt['matching_prompts'],
    'confirmed_at_utc': receipt['confirmed_at_utc'], 'phase_complete': False,
    'receipt_publication': receipt['receipt_publication'], 'terminal_resolution': receipt['terminal_resolution'],
}
current['pending_phase_delivery'] = {'phase': receipt['phase'], 'state': receipt['status'],
                                     'receipt': REL + '/P23-DELIVERY.json', 'technical_phase_complete': True,
                                     'phase_complete': False, 'terminal_resolution': receipt['terminal_resolution']}
current['snapshot_date'] = receipt['recorded_at_utc']
current['next_action']['summary'] = 'P23 ZIP and matching prompts are saved and byte-read-back. Finish separate receipt/terminal confirmation only, then stop. H0 remains blocked on H0-RTLD-ABSENT-PARENT-001 and its related alias constraint.'
current['next_action']['sources'].append(REL + '/P23-DELIVERY.json')
write(current_path, current)

text = '''
### P23 saved package boundary

The immutable P23 ZIP and both matching prompts are saved and byte-read-back. The independent archive review passed 931 checks. [P23 delivery](../../../engineering/localized-repair-c271/h0-plan-p23/P23-DELIVERY.json) records exact saved identities and preserves the source-time checkpoint. The final readback guard initially assumed a backing-file-ID attribute that the materializer does not provide; the corrected check verifies the actual stable-ID/version attributes and the exact returned backing ID, with no repeated upload or materialization. Both records remain preserved.

Only receipt publication, the separately saved actual receipt and matching live terminal confirmation remain at this source snapshot. Resolve those delivery-only pending fields using exact later evidence; never reinterpret them as H0 acceptance. C271 remains open, R03-R05 not_done, PR274 draft/unmerged and issue273 open. No further technical work or second phase follows in this chat.
'''
for name in ('PLAN.md', 'REQUIREMENTS.md', 'P23-SESSION.md'):
    path = REPO / 'docs/workflow/tasks/C271' / name
    path.write_text(path.read_text() + text)
print(json.dumps({'delivery': str(DEST / 'P23-DELIVERY.json'), 'saved_files': 3,
                  'immutable_zip_unchanged': True, 'terminal_confirmation': 'pending'}))
