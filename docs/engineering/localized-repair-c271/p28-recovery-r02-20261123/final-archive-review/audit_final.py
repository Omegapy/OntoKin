#!/usr/bin/env python3
"""Independent read-only review of the frozen P28 R02 final handoff.

Only audit artifacts under this script's own directory are written. Archived
code and product checks are not executed. Git commands read existing objects.
"""
from __future__ import annotations
import collections
import datetime
import hashlib
import io
import json
import os
import pathlib
import platform
import stat
import subprocess
import sys
import zipfile

ROOT = pathlib.Path('/workspace/scratch/002c49ccf480')
OUT = pathlib.Path(__file__).resolve().parent
REPO = ROOT / 'OntoKin'
ARCHIVE = ROOT / 'packages/OntoKin_C271_P28_R02_Recovery_Checkpoint_2026-11-23.zip'
COMMIT = '942096d22248fd84b7ac3a638e02aa1e66340519'
TREE = '3f8eba2e0de338a76fdb39aac373ed618c633c3c'
PARENT = '46b0fce68afb65cfbfcaba64f1276408d93ee85d'
MAIN = 'e43cc6c5777874101a40559e4058ad6826b07e51'
EXPECTED_SHA256 = '113cf92489c6579168c57f816b8347ab99f8874f187de74b8434bb10ef701f3b'
EVIDENCE = 'repository/docs/engineering/localized-repair-c271/p28-recovery-r02-20261123/'
checks = []

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def blob(raw):
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()

def check(name, passed, detail=None):
    checks.append({'name': name, 'passed': bool(passed), 'detail': detail})

def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + '\n')

def git(*args):
    env = os.environ.copy()
    env['GIT_OPTIONAL_LOCKS'] = '0'
    return subprocess.run(['git', '-C', str(REPO), *args], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout

def safe(name):
    return bool(name) and not name.startswith('/') and '\\' not in name and '\x00' not in name and ':' not in name and all(part not in ('', '.', '..') for part in name.rstrip('/').split('/'))

raw = ARCHIVE.read_bytes()
check('frozen ZIP exact byte identity', len(raw) == 9962453 and sha(raw) == EXPECTED_SHA256)
with zipfile.ZipFile(io.BytesIO(raw)) as z:
    infos = z.infolist()
    names = [entry.filename for entry in infos]
    check('ZIP CRC integrity', z.testzip() is None)
    check('149 exact distinct member names', len(names) == len(set(names)) == 149)
    check('safe relative paths', all(safe(name) for name in names))
    check('no symlinks or special files', all(stat.S_IFMT(entry.external_attr >> 16) in (0, stat.S_IFREG, stat.S_IFDIR) for entry in infos))
    check('no directory or encrypted entries', all(not entry.is_dir() and not entry.flag_bits & 1 for entry in infos))
    if any(not c['passed'] for c in checks):
        save('AUDIT.json', {'verdict': 'unsafe-or-unexpected-archive', 'checks': checks})
        raise SystemExit(1)
    payload = {entry.filename: z.read(entry) for entry in infos}
    inventory = [{'path': entry.filename, 'bytes': entry.file_size, 'sha256': sha(payload[entry.filename]), 'archive_mode': oct(entry.external_attr >> 16)} for entry in infos]

manifest = json.loads(payload['MANIFEST-SHA256.json'])
manifest_names = [row['path'] for row in manifest]
check('148 manifest entries, unique and safe', len(manifest_names) == len(set(manifest_names)) == 148 and all(safe(name) for name in manifest_names))
check('manifest exact payload inventory', set(manifest_names) == set(payload) - {'MANIFEST-SHA256.json'})
for row in manifest:
    check('manifest size/hash: ' + row['path'], len(payload[row['path']]) == row['bytes'] and sha(payload[row['path']]) == row['sha256'])

dest = OUT / 'extracted'
dest.mkdir(parents=True, exist_ok=False)
for name, data in payload.items():
    target = dest / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
extracted = {str(path.relative_to(dest)): path.read_bytes() for path in dest.rglob('*') if path.is_file()}
check('fresh extraction exact inventory and all bytes', extracted == payload)

check('authentic checkout inspected exact HEAD', git('rev-parse', 'HEAD').decode().strip() == COMMIT)
check('checkout clean', git('status', '--porcelain=v1') == b'')
check('commit exact tree and sole parent', git('show', '-s', '--format=%T %P', COMMIT).decode().strip() == TREE + ' ' + PARENT)
sources = json.loads(payload['SOURCE-MANIFEST.json'])
check('58 distinct source bindings', len(sources) == len({r['archive_path'] for r in sources}) == 58)
check('source commits are exact main/core', dict(collections.Counter(row['commit'] for row in sources)) == {COMMIT: 39, MAIN: 19})
check('all repository and branch-state snapshots source-bound', {row['archive_path'] for row in sources} == {name for name in payload if name.startswith(('repository/', 'branch-state/'))})
source_results = []
for row in sources:
    data = payload[row['archive_path']]
    entry = git('ls-tree', '-z', row['commit'], '--', row['git_path']).split(b'\0')
    check('source exact one tree entry: ' + row['archive_path'], len(entry) == 2 and entry[1] == b'')
    metadata, path = entry[0].split(b'\t', 1)
    mode, kind, oid = metadata.decode().split(' ')
    check('source commit/path/mode/blob: ' + row['archive_path'], path.decode() == row['git_path'] and kind == 'blob' and mode == row['git_mode'] and oid == row['git_blob'])
    check('source blob/size/SHA-256/exact Git bytes: ' + row['archive_path'], len(data) == row['bytes'] and sha(data) == row['sha256'] and blob(data) == oid and data == git('cat-file', 'blob', oid))
    source_results.append({**row, 'actual_git_mode': mode, 'actual_git_blob': oid, 'verified_exact_tree_and_blob_bytes': True})

required = ['README-START-HERE.md','CHECKPOINT.json','HANDOFF.md','NEXT-TASK.md','RECOVERY-STATUS.md','PROMPT-1-CONTINUE.md','PROMPT-2-RECOVER.md','HISTORICAL-DEPENDENCIES.json','MANIFEST-SHA256.json','HOST-ENVIRONMENT.md']
check('all mandatory root handoff files present', all(name in payload for name in required))
snapshot_files = ['CHATGPT-START-HERE.md','AGENTS.md','GOAL.md','STATUS.md','ROLE.md','docs/workflow/registry.json','docs/workflow/CURRENT.json','docs/workflow/PROTOCOL.md','docs/workflow/HANDOFF.md','docs/workflow/BROWSER-PROMPTS.md']
check('all required governing snapshots present', all('repository/' + name in payload for name in snapshot_files))
for task in ['C270', 'C271']:
    check('complete task snapshot ' + task, all('repository/docs/workflow/tasks/' + task + '/' + name in payload for name in ['REQUIREMENTS.md','PLAN.md','task.json']))
check('selected skill files included', all('repository/.agents/skills/' + name + '/SKILL.md' in payload for name in ['ontokin-session','ontokin-delivery','ontokin-learning']))

cp = json.loads(payload['CHECKPOINT.json'])
check('checkpoint source/tree/main/head agree', cp['source_commit'] == cp['branch_head_at_freeze'] == COMMIT and cp['source_tree'] == TREE and cp['observed_main'] == MAIN)
check('checkpoint parent/start agree', cp['starting_branch_head'] == PARENT and cp['starting_branch_tree'] == 'e5d8dc89b9e6fba4315a3386f43e13e758b33c0e')
check('honest incomplete blocked original phase', cp['parent_status'] == 'blocked' and cp['parent_complete'] is False and cp['phase_complete'] is False and cp['original_p28_implementation_verified'] is False)
check('R03-R05 remain unmet and original parent plan retained', cp['requirements'] == {'R01':'done','R02':'done','R03':'not_done','R04':'not_done','R05':'not_done'} and cp['parent_plan'] == {'P01':'done','P02':'in_progress'})
check('no runtime/product/main acceptance asserted', cp['runtime_changes'] == cp['product_tests_executed'] == 0 and cp['main_integration'] is False and cp['main_lease_held'] is False)
check('597 tests explicitly unverified', '597/597 original P28 tests' in cp['reported_but_not_reverified'] and 'unverified' in payload['HANDOFF.md'].decode())
check('original upload unknown identities and no replay retained', cp['current_unknown_operations'] == [{'operation':'Original P28 immutable blob/tree uploads','intended_parent':'360c80062e769230199602326fa8de25660df714','tree_sha':None,'commit_sha':None,'replayed':False}])
check('historical unknowns preserved', cp['historical_unknown_operations'] == ['C270 ancillary broad-driver completion','Global prior-process termination','P13 read-only difflib completion; do not retry'])
check('unfinished branch and issue retained', cp['branch_disposition'] == 'retained_for_unfinished_C271' and cp['issue_state'] == 'open' and cp['pr_state'] == 'draft_open_unmerged')
check('delivery honestly pending at freeze', cp['library_save_state'].startswith('pending_at_immutable_freeze') and cp['status'] == 'documentary_checkpoint_published_final_save_pending' and not (EVIDENCE + 'DELIVERY.json') in payload)
check('final review and receipts explicitly postfreeze', 'Final package review and saved-delivery steps occur after this freeze' in payload['RECOVERY-STATUS.md'].decode())

for name in ['README-START-HERE.md','PROMPT-1-CONTINUE.md','PROMPT-2-RECOVER.md','HOST-ENVIRONMENT.md']:
    text = payload[name].decode()
    check('fresh host rule: ' + name, 'different disposable execution host' in text and 'historical evidence' in text)
for member, filename in [('PROMPT-1-CONTINUE.md','OntoKin_C271_P28_R02_Continue_2026-11-23.md'),('PROMPT-2-RECOVER.md','OntoKin_C271_P28_R02_Recover_2026-11-23.md')]:
    separate = ROOT / 'packages' / filename
    check('separate prompt exact: ' + filename, separate.read_bytes() == payload[member])
    check('prompt bounded no-repeat stop: ' + member, 'Do not repeat this same recovery phase' in payload[member].decode() and 'Do not begin another phase' in payload[member].decode())
check('recovery prompt includes delivery-only reconciliation', 'Reconcile delivery-only pending fields through the exact external receipt' in payload['PROMPT-2-RECOVER.md'].decode())
check('next-action requires new exact input or reconstruction decision', 'Supply the exact original P28 final uploaded tree SHA plus complete publication manifest/group inventory' in cp['next_action'] and 'explicit bounded reconstruction decision' in cp['next_action'] and 'Do not repeat this same recovery phase' in cp['next_action'])
proposal = payload[EVIDENCE + 'RECONSTRUCTION-OPTION.md'].decode()
check('reconstruction explicit proposal and pinned P27 design', 'Status: proposal only. No reconstruction is authorized or started by this record.' in proposal and '105ac7c5f247fc1a01c1073266763f16e6587757' in proposal and '116 declared obligations' in proposal)
check('online continuation limits explicit', cp['package_type'] == 'browser-session handoff for online GitHub continuation' and 'not full offline repository restoration' in payload['README-START-HERE.md'].decode())

main_current = json.loads(payload['repository/docs/workflow/CURRENT.json'])
branch_current = json.loads(payload['branch-state/docs/workflow/CURRENT.json'])
task = json.loads(payload['repository/docs/workflow/tasks/C271/task.json'])
outcome = json.loads(payload[EVIDENCE + 'OUTCOME.json'])
check('separate main and branch current with active blocked C271', main_current['active_task'] is None and branch_current['active_task'] == 'C271' and branch_current['next_action']['status'] == 'blocked' and task['status'] == 'blocked')
check('same next-action across checkpoint/branch/task/outcome', cp['next_action'] == branch_current['next_action']['summary'] == task['next_action'] == outcome['next_action'])
check('canonical outcome retains blocked original and zero tests', outcome['parent_status'] == 'blocked' and outcome['original_p28_implementation_verified'] is False and outcome['product_tests_executed'] == outcome['runtime_changes'] == 0)

for filename in ['OntoKin_C271_P28_Recovery_Handoff_2026-11-23.zip','OntoKin_C271_P28_Recovery_Delivery_Receipt_2026-11-23.json']:
    check('predecessor unchanged: ' + filename, payload['predecessor/' + filename] == (ROOT / 'inputs/OntoKin' / filename).read_bytes())
with zipfile.ZipFile(io.BytesIO(payload['predecessor/OntoKin_C271_P28_Recovery_Handoff_2026-11-23.zip'])) as previous:
    check('historical dependencies byte-for-byte preserved', payload['HISTORICAL-DEPENDENCIES.json'] == previous.read('HISTORICAL-DEPENDENCIES.json'))
deps = json.loads(payload['CURRENT-DEPENDENCIES.json'])
for field in ['early_recovery', 'publication_archive_identity']:
    item = deps[field]
    data = (ROOT / 'packages' / item['file_name']).read_bytes()
    check('current portable dependency identity ' + field, len(data) == item['bytes'] and sha(data) == item['sha256'])
check('early save and publication dependencies have durable identities', deps['early_recovery']['saved_bytes_readback_equal'] is True and deps['early_recovery']['library_file_id'].startswith('libfile_') and deps['publication_recovery']['library_file_id'].startswith('libfile_'))

intent = json.loads(payload['recovery/PUBLICATION-INTENT.json'])
changes = git('diff', '--name-only', '-z', PARENT, COMMIT).decode().rstrip('\0').split('\0')
check('published intent agrees exact parent/tree and no replay', intent['expected_head'] == PARENT and intent['expected_result_tree'] == TREE and intent['original_upload_replayed'] is False)
check('39 actual changed paths exactly equal publication intent', len(changes) == len(intent['files']) == 39 and set(changes) == {row['path'] for row in intent['files']})
check('actual change contains documentary paths only', all(path.startswith('docs/') for path in changes))
for row in intent['files']:
    archive_path = 'branch-state/' + row['path'] if row['path'] == 'docs/workflow/CURRENT.json' else 'repository/' + row['path']
    data = payload[archive_path]
    check('complete published intent bytes: ' + row['path'], len(data) == row['bytes'] and sha(data) == row['sha256'] and blob(data) == row['git_blob'])
readback = json.loads(payload['recovery/CORE-COMMIT-READBACK.json'])
ref_readback = json.loads(json.loads(payload['recovery/CORE-REF-READBACK.json'])['content'])
check('retained GitHub commit/ref readbacks match exact local object', readback['sha'] == COMMIT and readback['tree']['sha'] == TREE and [x['sha'] for x in readback['parents']] == [PARENT] and ref_readback['object']['sha'] == COMMIT)

check_record = json.loads(payload[EVIDENCE + 'checks/CHECKS.json'])
disposition = json.loads(payload[EVIDENCE + 'reviews/checkpoint_review/WHITESPACE-DISPOSITION.json'])
diff = payload[EVIDENCE + 'reviews/checkpoint_review/candidate.diff']
check('full staged whitespace remains recorded failed', check_record['full_staged_whitespace']['exit_code'] == 2 and check_record['full_staged_whitespace']['status'] == 'failed_preserved' and disposition['full_staged_whitespace']['exit_code'] == 2)
check('full staged failure exact log retained', payload[EVIDENCE + 'checks/whitespace-full-staged.stdout'].decode() == disposition['full_staged_whitespace']['stdout'])
check('authored whitespace separately passed', check_record['authored_whitespace']['exit_code'] == 0 and disposition['scoped_authored_whitespace']['exit_code'] == 0 and payload[EVIDENCE + 'checks/whitespace-authored.stdout'] == b'')
check('preserved raw diff exact independent binding', len(diff) == disposition['original_candidate_diff']['bytes'] and sha(diff) == disposition['original_candidate_diff']['sha256'])
check('both flagged raw lines are exact unified-diff context markers', all(diff.splitlines(keepends=True)[row['diff_line'] - 1] == b' \n' for row in disposition['observed_lines']) and len(disposition['observed_lines']) == 2)
check('initial workflow failure retained', check_record['failures'][0]['exit_code'] == 1 and bool(payload[EVIDENCE + 'checks/workflow-attempt001.txt']))
check('both stopped publication-preparation failures retained', len(check_record['preparation_incidents']) == 2 and all(row['exit_code'] == 1 and row['immutable_remote_writes'] == 0 for row in check_record['preparation_incidents']))
published_checks = json.loads(payload['recovery/published-checks/CHECKS.json'])
doc_result = json.loads(payload['recovery/published-checks/documentation.stdout'])
check('published checks pinned to exact source with zero product execution', published_checks['source_revision'] == COMMIT and published_checks['source_tree'] == TREE and published_checks['published_files_verified'] == 39 and published_checks['product_tests'] == 0)
check('published workflow and documentation exited zero', all(row['exit_code'] == 0 for row in published_checks['checks']) and 'Workflow structure passed (12 tasks).' in payload['recovery/published-checks/workflow.stdout'].decode() and doc_result['status'] == 'passed')
check('published documentation counts agree', published_checks['checks'][1]['source_count'] == 29 and published_checks['checks'][1]['links']['documents'] == 1647 and published_checks['checks'][1]['links']['local_links'] == 6334)
check('published check record equals checkpoint embedded record', published_checks == cp['published_checks'])

check('frozen ZIP unchanged after audit', ARCHIVE.read_bytes() == raw)
check('checkout still clean and pinned after audit', git('status', '--porcelain=v1') == b'' and git('rev-parse', 'HEAD').decode().strip() == COMMIT)
save('INVENTORY.json', inventory)
save('SOURCE-BINDINGS.json', source_results)
failed = [row for row in checks if not row['passed']]
result = {
    'schema': 'ontokin.c271.p28-r02-final-archive-review/1',
    'reviewer': '/root/artifact_audit',
    'observed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'verdict': 'ACCEPTED_FROZEN_RECOVERY_HANDOFF_FOR_SAVE' if not failed else 'REJECTED_WITH_FINDINGS',
    'archive': {'path': str(ARCHIVE), 'bytes': len(raw), 'sha256': sha(raw), 'members': len(names), 'manifest_payloads': len(manifest), 'source_bindings': len(sources)},
    'source_commit': COMMIT, 'source_tree': TREE, 'source_parent': PARENT, 'governing_main': MAIN,
    'command': 'python3 session/reviews/final_archive/audit_final.py',
    'environment': {'python': sys.version, 'platform': platform.platform()},
    'checks_passed': len(checks) - len(failed), 'checks_failed': len(failed),
    'count_definition': 'Individual archive integrity, inventory, byte/hash/Git-object, snapshot-completeness, preserved-evidence and handoff-semantics assertions. These are not product tests.',
    'checks': checks, 'mandatory_findings': failed,
    'scope': 'Final delivery review within the same bounded R02 phase; no new technical phase.',
    'limits': ['No original P28 implementation recovered, accepted, reconstructed or executed.', '597 tests remain a historical unverified report.', 'Raw full staged whitespace failure remains failed with exact independently dispositioned evidence; its passing preservation check does not convert that command to passed.', 'Exact local Git objects and archived GitHub readbacks were verified; this worker performed no live remote mutation or lookup.', 'Acceptance permits saving these frozen bytes only; confirmed Library save, external receipt and terminal reconciliation remain subsequent Director responsibilities.', 'Source-time omission of later save/receipt/review outcomes is intentional and explicitly documented.', 'Full extracted copy is reproducible and may be excluded from later receipt evidence.'],
    'next_action': 'Save and verify the exact frozen ZIP and its exact separate prompts, preserve this independent review in external receipt evidence, reconcile delivery/ownership, and stop. Original P28 remains blocked pending new exact recovery input or explicit bounded reconstruction authority.',
    'mutations': {'canonical_files': False, 'GitHub': False, 'Library': False, 'archive': False, 'only_owned_audit_directory': True},
    'worker_state': 'stopped; no pending writes or jobs'
}
save('AUDIT.json', result)
print(json.dumps({key: result[key] for key in ['verdict','checks_passed','checks_failed','archive','mandatory_findings']}))
if failed:
    raise SystemExit(1)
