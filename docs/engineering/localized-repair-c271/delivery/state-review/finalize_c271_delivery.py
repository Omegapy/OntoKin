"""Record confirmed P01 delivery; invoked only after successful final uploads."""
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT = Path('/workspace/scratch/cce28e2b3ca4')
REPO = ROOT / 'OntoKin'
SOURCE = 'e0b73f7d6ce49631e598d1378a0ddba717726524'
TREE = '9ab0d4dfcb21735fed4c019f85f8f450ebfaa7b4'
MAIN = 'e1a48f7d0635e9aa4f4b6d6a586e7305eb81999d'
BASE = 'docs/engineering/localized-repair-c271'
DEST = REPO / BASE / 'delivery'

def git(*args):
    return subprocess.check_output(['git', *args], cwd=REPO, text=True).strip()

def read(path):
    return json.loads(Path(path).read_text())

def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')

def copy(src, dst):
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    assert Path(src).read_bytes() == dst.read_bytes()

def unique_append(seq, value):
    if value not in seq:
        seq.append(value)

assert git('rev-parse', 'HEAD') == SOURCE
assert git('status', '--porcelain=v1') == ''
uploads = read(ROOT / 'recon/c271-final-save-normalized.json')
assert uploads['status'] == 'saved'
assert uploads['directory_id'] == 'libdir_fde3_dl-6ad29e65bf148191aef327539199fc34_2ab2a24d43748191957f9bcc356b59de'
assert len(uploads['files']) == 3
expected_files = {
    'OntoKin_C271_Control_Candidate_Handoff_2026-11-20.zip': (12003931, '9bdb8ec134fbf8facc1b1f52aa9b7171de16f35593ddf7ad61930e521f4495df'),
    'OntoKin_C271_Prompt_1_Continue_2026-11-20.md': (3559, '60252a3177831711fdbc34c60d735b16cf31162bd89efa250269d9275bab893d'),
    'OntoKin_C271_Prompt_2_Recover_2026-11-20.md': (3785, '09192571ddcaae69ad91fbb51872cc18087a973bd4fd551075fde43f62b93c89'),
}
assert {x['file_name'] for x in uploads['files']} == set(expected_files)
assert len({x['library_file_id'] for x in uploads['files']}) == 3
assert len({x['file_id'] for x in uploads['files']}) == 3
for item in uploads['files']:
    path = ROOT / 'artifacts' / item['file_name']
    assert item['local_metadata_applied'] is True
    assert item['path'] == '/OntoKin/' + item['file_name']
    assert item['bytes'] == path.stat().st_size
    assert item['sha256'] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert item['library_file_id'].startswith('libfile_')
    assert item['file_id'].startswith('file_')
    assert isinstance(item['version'], int)
    assert (item['bytes'], item['sha256']) == expected_files[item['file_name']]
archive = next(x for x in uploads['files'] if x['file_name'].endswith('.zip'))
assert archive['sha256'] == '9bdb8ec134fbf8facc1b1f52aa9b7171de16f35593ddf7ad61930e521f4495df'
prompts = [x for x in uploads['files'] if x['file_name'].endswith('.md')]
assert len(prompts) == 2
builder_path = ROOT / 'artifacts/OntoKin_C271_Control_Candidate_Handoff_2026-11-20_Verification.json'
audit_path = ROOT / 'reviews/c271-final-package-audit/AUDIT.json'
builder = read(builder_path)
assert builder['passed'] is True
assert builder['source_revision'] == SOURCE and builder['source_tree'] == TREE
assert builder['archive']['filename'] == archive['file_name']
assert (builder['archive']['bytes'], builder['archive']['sha256']) == (archive['bytes'], archive['sha256'])
assert len(builder['standalone_prompts']) == 2
assert {Path(x['local_path']).name for x in builder['standalone_prompts']} == {x['file_name'] for x in prompts}
with zipfile.ZipFile(ROOT / 'artifacts' / archive['file_name']) as z:
    checkpoint = json.loads(z.read('CHECKPOINT.json'))
    assert checkpoint['source_revision'] == SOURCE and checkpoint['source_tree'] == TREE
    for spec in builder['standalone_prompts']:
        item = next(x for x in prompts if x['file_name'] == Path(spec['local_path']).name)
        data = z.read(spec['archive_path'])
        assert data == (ROOT / 'artifacts' / item['file_name']).read_bytes()
        assert (len(data), hashlib.sha256(data).hexdigest()) == (item['bytes'], item['sha256'])
        assert (spec['bytes'], spec['sha256']) == (item['bytes'], item['sha256'])
audit = read(audit_path)
assert audit['passed'] is True
assert audit['source_revision'] == SOURCE and audit['source_tree'] == TREE
assert (audit['archive']['bytes'], audit['archive']['sha256']) == (archive['bytes'], archive['sha256'])
checks = read(ROOT / 'c271-final-record-checks/CHECKS.json')
assert checks['passed'] is True and checks['source']['commit'] == SOURCE
assert checks['source']['dirty_before'] == checks['source']['dirty_after'] == ''
assert not DEST.exists()
DEST.mkdir(parents=True)
copy(builder_path, DEST / 'PACKAGE-VERIFICATION.json')
for p in (ROOT / 'reviews/c271-final-package-audit').iterdir():
    if p.is_file():
        copy(p, DEST / 'package-review' / p.name)
for p in (ROOT / 'c271-final-record-checks').iterdir():
    if p.is_file():
        copy(p, DEST / 'record-checks' / p.name)
copy(ROOT / 'reviews/c271/FINAL-STATE-REVIEW.json', DEST / 'FINAL-STATE-REVIEW.json')
copy(ROOT / 'recon/c271-final-save-normalized.json', DEST / 'UPLOAD-RECEIPTS.json')

now = datetime.datetime.now(datetime.timezone.utc).isoformat()
receipt_rel = BASE + '/delivery/P01-DELIVERY.json'
receipt = {
    'schema': 'ontokin.c271.p01-delivery/1',
    'task': 'C271', 'phase': 'C271-P01-control-candidate',
    'status': 'saved', 'partial': True,
    'saved_at_utc': uploads['saved_at_utc'], 'recorded_at_utc': now,
    'folder': 'OntoKin', 'directory_id': uploads['directory_id'],
    'archive': archive, 'prompts': prompts,
    'source_revision': SOURCE, 'source_tree': TREE,
    'executed_revision': '067392f2b5f592a5c3104fa8848cc0030ba1117b',
    'observed_main': MAIN,
    'branch': 'work/c271-missing-import-digest-control',
    'pull_request': 'https://github.com/Omegapy/OntoKin/pull/274',
    'pull_request_state': 'open_draft_unmerged',
    'scope_issue': 'https://github.com/Omegapy/OntoKin/issues/273',
    'scope_issue_state': 'open', 'branch_disposition': 'retained_unmerged',
    'main_lease': 'not_held', 'merge_commit': None,
    'verification': {
        'archive_passed': True, 'members': 160, 'payloads': 159, 'git_snapshots': 88,
        'preserved_session_files': 58,
        'builder': BASE + '/delivery/PACKAGE-VERIFICATION.json',
        'independent_package_review': BASE + '/delivery/package-review/AUDIT.json',
        'final_source_review': BASE + '/delivery/FINAL-STATE-REVIEW.json',
        'clean_source_record_checks': BASE + '/delivery/record-checks/CHECKS.json',
        'upload_receipts': BASE + '/delivery/UPLOAD-RECEIPTS.json',
        'standalone_prompts_match_zip': True,
    },
    'phase_status': 'complete_partial_delivery',
    'parent_status': 'in_progress',
    'requirements': {'R01': 'done', 'R02': 'done', 'R03': 'not_done', 'R04': 'not_done', 'R05': 'not_done'},
    'next_action': 'Stop this chat. In a fresh parent chat reconcile live state and resume C271 P02 at R03: required routine driver, complete affected regression cohort and independent integration review.',
    'publication_boundary': 'The containing receipt-only Git commit postdates the frozen ZIP. It records confirmed saves, verification and P01 phase state; it changes no implementation, oracle, original evidence or recovery instructions. Verify its actual head in live GitHub. No rebuild is needed for this declared external receipt boundary.',
    'limits': ['No C271 merge or integration approval', 'No routine driver, complete affected cohort or actual-main validation in P01', 'No complete H22/C260 or product qualification', 'Historical broad-driver final completion remains unknown'],
}
write(DEST / 'P01-DELIVERY.json', receipt)

task_path = REPO / 'docs/workflow/tasks/C271/task.json'
task = read(task_path)
assert task['status'] == 'in_progress'
assert {x['id']: x['status'] for x in task['requirements']} == receipt['requirements']
for item in task['requirements']:
    if item['id'] == 'R03':
        unique_append(item['evidence'], BASE + '/delivery/record-checks/CHECKS.json')
        unique_append(item['evidence'], BASE + '/delivery/FINAL-STATE-REVIEW.json')
    elif item['id'] == 'R05':
        unique_append(item['evidence'], BASE + '/EARLY-RECOVERY-RECEIPT.json')
        unique_append(item['evidence'], receipt_rel)
for item in task['plan']:
    if item['id'] == 'P01':
        item['status'] = 'done'
        unique_append(item['artifacts'], receipt_rel)
for item in task['checks']:
    if item['name'] == 'clean published-candidate documentation and workflow records':
        item['result'] = 'passed'
        item['evidence'] = [BASE + '/delivery/record-checks/CHECKS.json']
task['checks'].append({
    'name': 'P01 partial handoff archive and independent package review',
    'command': 'Recorded builder and independent archive audits; no behavioral replay',
    'result': 'passed', 'required': True,
    'evidence': [BASE + '/delivery/PACKAGE-VERIFICATION.json', BASE + '/delivery/package-review/AUDIT.json', receipt_rel],
})
task['next_action'] = receipt['next_action']
task['session_phase'].update({
    'status': 'complete_partial_delivery', 'delivery_confirmed': True,
    'source_revision': SOURCE, 'source_tree': TREE,
    'delivery_receipt': receipt_rel, 'completed_at_utc': now,
    'record_checks': {'result': 'passed', 'source_revision': SOURCE, 'report': BASE + '/delivery/record-checks/CHECKS.json'},
    'package_review': {'result': 'passed', 'report': BASE + '/delivery/package-review/AUDIT.json'},
})
task['session_phase']['focused_review'].update({'final_source_candidate': SOURCE, 'final_state_checks': 58, 'final_source_review': BASE + '/delivery/FINAL-STATE-REVIEW.json'})
task['delivery'].update({'status': 'saved', 'partial': True, 'receipt': receipt_rel, 'archive': archive, 'prompts': prompts, 'source_revision': SOURCE})
unique_append(task['completion']['evidence'], receipt_rel)
write(task_path, task)

current_path = REPO / 'docs/workflow/CURRENT.json'
current = read(current_path)
assert current['active_task'] == 'C271'
old_previous = current['previous_handoff']
if not any(x.get('library_file_id') == old_previous.get('library_file_id') for x in current['older_handoffs']):
    current['older_handoffs'].append(old_previous)
current['previous_handoff'] = current['latest_handoff']
current['latest_handoff'] = {
    'task': 'C271', 'kind': 'online_browser_session', 'phase': 'C271-P01-control-candidate', 'partial': True,
    **{k:archive[k] for k in ['file_name','url','library_file_id','file_id','version','bytes','sha256']},
    'source_revision': SOURCE, 'source_tree': TREE, 'delivery_receipt': receipt_rel,
}
current['previous_recovery'] = current['latest_recovery']
current['latest_recovery'] = read(REPO / BASE / 'EARLY-RECOVERY-RECEIPT.json')
current['latest_recovery']['receipt'] = BASE + '/EARLY-RECOVERY-RECEIPT.json'
current['snapshot_date'] = now
current['next_action'].update({
    'status': 'ready',
    'summary': 'C271 P01 is delivered with verified ZIP/prompts and separate receipt. Stop this chat. A fresh chat resumes P02 at R03 integration verification on the retained branch.',
    'suggested_task': 'Continue C271 P02 on work/c271-missing-import-digest-control / draft PR274: required local driver, complete affected cohort and independent integration review before any main lease/integration.',
})
unique_append(current['next_action']['sources'], receipt_rel)
write(current_path, current)

for relative, text in [
    ('docs/workflow/tasks/C271/PLAN.md', '\n## P01 delivery checkpoint\n\nP01 is complete with a verified saved partial ZIP, matching prompts and a separate [delivery receipt](../../../engineering/localized-repair-c271/delivery/P01-DELIVERY.json). P02 remains not done and belongs to a fresh parent chat. Parent R03, R04 and R05 remain open. This receipt-only checkpoint does not change the frozen candidate.\n'),
    ('docs/workflow/tasks/C271/SESSION.md', '\n## Confirmed P01 partial delivery\n\nThe final package freezes candidate `' + SOURCE + '` and its exact Git tree. Fresh workflow/documentation checks passed on that clean source; the final source review passed 58 checks. Builder and independent archive review passed. ZIP and matching prompts are saved; exact identities and results are in the separate [P01 delivery receipt](../../../engineering/localized-repair-c271/delivery/P01-DELIVERY.json). Earlier pending statements above remain historical checkpoints. The receipt-only publication changes no implementation, oracle or original evidence.\n\nP01 is complete; parent R03/R04/R05 and P02 remain open. Draft PR274 is retained and unmerged; issue273 remains open. No main write, merge, integration lease or branch deletion occurred. Stop this chat; a fresh chat resumes R03 verification on the same branch.\n'),
]:
    path = REPO / relative
    path.write_text(path.read_text() + text)

assert git('rev-parse', 'HEAD') == SOURCE
print(json.dumps({'recorded': receipt_rel, 'source': SOURCE, 'phase': 'complete_partial_delivery', 'parent': 'in_progress', 'archive_sha256': archive['sha256']}, indent=2))
