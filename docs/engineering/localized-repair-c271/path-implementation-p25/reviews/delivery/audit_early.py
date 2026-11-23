"""Independent P25 early-package and documentary audit; no product execution."""
import datetime
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import tempfile
import zipfile

ROOT = Path('/workspace/scratch/bd99261bd84d')
REPO = ROOT / 'OntoKin'
OUT = Path(__file__).resolve().parent
P25 = OUT.parent.parent
START = 'ce411b12e601036a33698aa7c3290722e602ea75'
MAIN = 'e43cc6c5777874101a40559e4058ad6826b07e51'
NAME = 'OntoKin_C271_P25_RTLD_Path_Early_Recovery_2026-11-23.zip'
ARCHIVE = ROOT / 'packages/early' / NAME
READBACK = ROOT / 'readback/early' / NAME
checks = []
readset = []


def sha(data):
    return hashlib.sha256(data).hexdigest()


def check(name, condition, detail=None):
    checks.append({'check': name, 'status': 'passed' if condition else 'failed', 'detail': detail})
    return bool(condition)


def read(path, coverage='mechanical full bytes'):
    data = path.read_bytes()
    readset.append({'path': str(path), 'bytes': len(data), 'sha256': sha(data), 'coverage': coverage})
    return data


def git_bytes(path, revision=START):
    return subprocess.check_output(['git', 'show', revision + ':' + path], cwd=REPO)


def objid(revision):
    return subprocess.check_output(['git', 'rev-parse', revision], cwd=REPO, text=True).strip()


receipt_bytes = read(ROOT / 'state/EARLY-RECOVERY-RECEIPT.json', 'full semantic read and mechanical checks')
receipt = json.loads(receipt_bytes)
saved = json.loads(read(ROOT / 'state/early-save.json', 'full semantic read and mechanical checks'))
archive_bytes = read(ARCHIVE)
readback_bytes = read(READBACK)
check('saved_archive_exact_readback', archive_bytes == readback_bytes)
check('receipt_bytes_sha256', len(archive_bytes) == receipt['bytes'] == receipt['file_size_bytes'] and sha(archive_bytes) == receipt['sha256'])
check('saved_service_metadata', all(saved[k] == receipt[k] for k in ['file_id', 'library_file_id', 'file_name', 'current_version_number', 'directory_id', 'mime_type', 'file_size_bytes']) and receipt['library_path'] == saved['path'])
check('saved_receipt_version', receipt['current_version_number'] == receipt['version'] == 0)
attrs = {}
for path in [ARCHIVE, READBACK]:
    attrs[str(path)] = {name: os.getxattr(path, name).decode() for name in os.listxattr(path)}
    check('saved_xattrs_' + path.parent.name, attrs[str(path)].get('user.library-file-id') == receipt['library_file_id'] and attrs[str(path)].get('user.library-file-version') == str(receipt['version']))

with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
    infos = archive.infolist()
    names = [entry.filename for entry in infos]
    safe = all(not name.startswith('/') and '\\' not in name and '\x00' not in name and all(part not in ['', '.', '..'] for part in name.split('/')) and ':' not in name.split('/')[0] and PurePosixPath(name).as_posix() == name for name in names)
    check('safe_relative_member_names', safe)
    check('unique_member_names', len(names) == len(set(names)))
    check('no_encrypted_or_special_members', all(not (entry.flag_bits & 1) and not entry.is_dir() and stat.S_IFMT(entry.external_attr >> 16) in [0, stat.S_IFREG] for entry in infos))
    check('zip_crc', archive.testzip() is None)
    check('receipt_member_count', len(names) == receipt['members'] == 42)
    required = ['README-START-HERE.md', 'CHECKPOINT.json', 'HANDOFF.md', 'NEXT-TASK.md', 'RECOVERY-STATUS.md', 'PROMPT-1-CONTINUE.md', 'PROMPT-2-RECOVER.md', 'HISTORICAL-DEPENDENCIES.json', 'MANIFEST-SHA256.json', 'HOST-ENVIRONMENT.md', 'SOURCE-MANIFEST.json']
    check('required_root_members', all(name in names for name in required))
    payload = {name: archive.read(name) for name in names}
    manifest = json.loads(payload['MANIFEST-SHA256.json'])['files']
    manifest_names = [entry['path'] for entry in manifest]
    check('manifest_exact_inventory', len(manifest_names) == len(set(manifest_names)) and set(manifest_names) == set(names) - {'MANIFEST-SHA256.json'})
    check('manifest_every_size_and_hash', all(len(payload[entry['path']]) == entry['bytes'] and sha(payload[entry['path']]) == entry['sha256'] for entry in manifest))
    sources = json.loads(payload['SOURCE-MANIFEST.json'])['files']
    check('source_manifest_exact_inventory', len(sources) == receipt['source_bindings'] == 27 and len({entry['member'] for entry in sources}) == len(sources) and {entry['member'] for entry in sources} == {name for name in names if name.startswith('repository/')} and all(entry['member'] == 'repository/' + entry['path'] for entry in sources))
    source_results = []
    for entry in sources:
        actual = payload[entry['member']]
        frozen = git_bytes(entry['path'], entry['commit'])
        source_results.append({**entry, 'exact_git_bytes': frozen == actual, 'identity_matches': entry['bytes'] == len(actual) and entry['sha256'] == sha(actual)})
    check('all_source_bindings_exact', all(entry['exact_git_bytes'] and entry['identity_matches'] for entry in source_results))
    check('only_declared_main_and_start_sources', {entry['commit'] for entry in sources} == {MAIN, START})
    mandatory_snapshots = ['CHATGPT-START-HERE.md', 'AGENTS.md', 'GOAL.md', 'STATUS.md', 'ROLE.md', 'docs/workflow/registry.json', 'docs/workflow/CURRENT.json', 'docs/workflow/PROTOCOL.md', 'docs/workflow/HANDOFF.md', 'docs/workflow/BROWSER-PROMPTS.md', 'docs/workflow/EPHEMERAL-HOST.md', 'docs/workflow/tasks/C271/task.json', 'docs/workflow/tasks/C271/REQUIREMENTS.md', 'docs/workflow/tasks/C271/PLAN.md', '.agents/skills/ontokin-session/SKILL.md', '.agents/skills/ontokin-delivery/SKILL.md', '.agents/skills/ontokin-learning/SKILL.md']
    check('mandatory_repository_snapshots', set(mandatory_snapshots) <= {entry['path'] for entry in sources})
    checkpoint = json.loads(payload['CHECKPOINT.json'])
    check('checkpoint_commit_trees', checkpoint['source_commit'] == START and checkpoint['source_tree'] == objid(START + '^{tree}') and checkpoint['observed_main'] == MAIN and checkpoint['observed_main_tree'] == objid(MAIN + '^{tree}'))
    check('early_checkpoint_honest_pending_state', checkpoint['substantial_work_started'] is False and checkpoint['phase_complete'] is False and checkpoint['delivery_state'] == 'early_recovery_save_pending' and checkpoint['active_worker']['identity'] == '/root/reconcile' and 'Complete independent startup reconciliation' in checkpoint['incomplete_steps'])
    check('parent_and_runtime_gates_remain_open', checkpoint['parent_complete'] is False and checkpoint['parent_status'] == 'in_progress' and checkpoint['h0_accepted'] is False and checkpoint['h1_executed'] is False and checkpoint['main_lease_held'] is False and checkpoint['requirements'] == {'R01': 'done', 'R02': 'done', 'R03': 'not_done', 'R04': 'not_done', 'R05': 'not_done'} and checkpoint['parent_plan'] == {'P01': 'done', 'P02': 'in_progress'} and checkpoint['pr']['draft'] is True and checkpoint['pr']['merged'] is False and checkpoint['issue']['state'] == 'open')
    check('ephemeral_rule_in_required_prose', all(b'disposable' in payload[name] for name in ['README-START-HERE.md', 'HOST-ENVIRONMENT.md', 'PROMPT-1-CONTINUE.md', 'PROMPT-2-RECOVER.md']))
    p24_name = 'history/OntoKin_C271_P24_H0_Path_Design_Handoff_2026-11-23.zip'
    p24_bytes = payload[p24_name]
    check('p24_archive_identity', len(p24_bytes) == 10847033 and sha(p24_bytes) == '5b1886184add5644e1272c31c22f4f9232a8e76433d8f2f867fd826d8bf18e4e')
    receipt_name = 'history/OntoKin_C271_P24_Delivery_Receipt_2026-11-23.json'
    external = read(ROOT / 'incoming-receipt/OntoKin/OntoKin_C271_P24_Delivery_Receipt_2026-11-23.json')
    check('p24_external_receipt_exact', payload[receipt_name] == external and sha(external) == '7e0dc98c21df0b20022a787985ef2da1ccbf914b8e7697e1c103a9c9e952c3c7')
    marker = read(ROOT / 'state/startup/p24-terminal.json')
    check('p24_terminal_marker_exact', payload['history/P24-TERMINAL.json'] == marker)
    dependencies = json.loads(payload['HISTORICAL-DEPENDENCIES.json'])
    p23 = dependencies['immediate_predecessor']
    with zipfile.ZipFile(io.BytesIO(p24_bytes)) as prior:
        prior_bytes = prior.read(p23['archive_member'])
        inherited_dependency_doc = prior.read('HISTORICAL-DEPENDENCIES.json') == payload['HISTORICAL-DEPENDENCIES.json']
        check('inherited_p23_archive_preserved_exact_inside_p24', len(prior_bytes) == p23['bytes'] and sha(prior_bytes) == p23['sha256'])
    check('historical_dependencies_correct_for_p25_root', p23['archive_member'] in names, {'actual': 'Unchanged P24 dependency document; declared P23 member is inside included P24 ZIP, not P25 root.', 'inherited_document_exact': inherited_dependency_doc, 'p24_container': p24_name, 'nested_p23_member': p23['archive_member']})
    check('historical_c262_identity_retained', b'libfile_fde3_f-99755' in payload['HISTORICAL-DEPENDENCIES.json'] and b'532260846' in payload['HISTORICAL-DEPENDENCIES.json'])
    extraction_results = []
    if safe and len(names) == len(set(names)) and all(stat.S_IFMT(entry.external_attr >> 16) in [0, stat.S_IFREG] for entry in infos):
        with tempfile.TemporaryDirectory(prefix='early-extract-', dir=OUT) as target:
            target_path = Path(target)
            for entry in infos:
                destination = target_path / entry.filename
                destination.parent.mkdir(parents=True, exist_ok=True)
                with destination.open('xb') as stream:
                    stream.write(payload[entry.filename])
                os.chmod(destination, 0o600)
            for entry in manifest:
                data = (target_path / entry['path']).read_bytes()
                extraction_results.append({'path': entry['path'], 'bytes_match': len(data) == entry['bytes'], 'sha256_matches': sha(data) == entry['sha256']})
            check('fresh_extraction_exact_inventory', {str(p.relative_to(target_path)) for p in target_path.rglob('*') if p.is_file()} == set(names))
            check('fresh_extraction_all_payloads_verified', all(entry['bytes_match'] and entry['sha256_matches'] for entry in extraction_results) and (target_path / 'MANIFEST-SHA256.json').read_bytes() == payload['MANIFEST-SHA256.json'])
            check('fresh_extracted_sources_match_git', all((target_path / entry['member']).read_bytes() == git_bytes(entry['path'], entry['commit']) for entry in sources))
    inventory = [{'path': entry.filename, 'bytes': len(payload[entry.filename]), 'sha256': sha(payload[entry.filename]), 'zip_mode': oct(entry.external_attr >> 16)} for entry in infos]

canonical = {}
for relative in ['docs/workflow/tasks/C271/task.json', 'docs/workflow/CURRENT.json']:
    before = json.loads(git_bytes(relative))
    after_bytes = read(REPO / relative, 'full historical content via startup report; all new or changed top-level semantic content reviewed')
    after = json.loads(after_bytes)
    changed = sorted(key for key in set(before) | set(after) if before.get(key) != after.get(key))
    canonical[relative] = {'changed_keys': changed, 'old_sha256': sha(git_bytes(relative)), 'new_sha256': sha(after_bytes)}
    if relative.endswith('/task.json'):
        task = after
        check('task_changes_bounded', set(changed) <= {'owner', 'next_action', 'session_phase', 'delivery', 'prior_session_phases', 'prior_phase_deliveries', 'phase_reconciliations'})
        check('task_prior_history_preserved', after['prior_session_phases'] == before['prior_session_phases'] + [before['session_phase']] and after['prior_phase_deliveries'] == before['prior_phase_deliveries'] + [before['delivery']] and after['phase_reconciliations'][:len(before.get('phase_reconciliations', []))] == before.get('phase_reconciliations', []))
        check('task_parent_acceptance_unchanged', all(after[key] == before[key] for key in ['status', 'requirements', 'plan', 'checks', 'completion', 'authorization', 'historical_checks', 'blocked_reason_history', 'remaining_h0_constraint', 'prior_h0_constraints']))
        check('task_current_owner_corrected', after['owner'] == after['session_phase']['owner'] == 'c271-p25-bd99261bd84d')
    else:
        check('current_changes_bounded', set(changed) <= {'snapshot_date', 'next_action', 'latest_recovery', 'older_recoveries', 'pending_phase_delivery'})
        check('current_prior_recovery_preserved', after['older_recoveries'] == before['older_recoveries'] + [before['latest_recovery']])
        check('current_p25_delivery_pending', after['pending_phase_delivery']['status'] == 'early_confirmed_final_pending' and after['pending_phase_delivery']['phase_complete'] is False)
        check('current_receipt_matches_original_saved_identity', all(after['latest_recovery'][key] == receipt[key] for key in after['latest_recovery']))

for relative in ['docs/workflow/tasks/C271/REQUIREMENTS.md', 'docs/workflow/tasks/C271/PLAN.md']:
    before = git_bytes(relative)
    after = read(REPO / relative, 'full historic content via startup; complete appended P25 section read')
    check('append_only_' + Path(relative).name, after.startswith(before))
    canonical[relative] = {'old_bytes': len(before), 'old_sha256': sha(before), 'new_bytes': len(after), 'new_sha256': sha(after), 'appended_text': after[len(before):].decode()}

records = {}
for name in ['PHASE.json', 'SESSION.json', 'WORKERS.json', 'OWNERSHIP.json', 'EARLY-RECOVERY-RECEIPT.json', 'P24-TERMINAL-RECONCILIATION.json']:
    records[name] = json.loads(read(P25 / name, 'full semantic read and mechanical checks'))
phase = records['PHASE.json']
check('phase_matches_task_session_phase', phase == task['session_phase'])
check('phase_retains_start_main_no_lease', phase['starting_head'] == START and phase['observed_main'] == MAIN and phase['main_lease_held'] is False)
check('phase_receipt_exact', records['EARLY-RECOVERY-RECEIPT.json'] == receipt)
check('phase_p24_reconciliation_exact', records['P24-TERMINAL-RECONCILIATION.json'] == json.loads(marker))
session = records['SESSION.json']
check('session_read_sources_match_git', all(entry['sha256'] == sha(git_bytes(entry['path'], entry['revision'])) for entry in session['read_set']), 'Source identity verification; not an independent assertion that Director read each source.')
check('session_completion_time_corrected', session['active_record_read_coverage']['completed_at_utc'] == '2026-11-23T14:07:05.431593+00:00' and session['declaration_at_utc'] < session['active_record_read_coverage']['completed_at_utc'] <= session['updated_at_utc'])
workers = records['WORKERS.json']['workers']
own = next(worker for worker in workers if worker['identity'] == '/root/reconcile')
check('worker_current_assignment_preserves_startup', own['writes'] == ['docs/engineering/localized-repair-c271/path-implementation-p25/reviews/delivery/'] and own['status'] == 'active' and own['completed_assignments'][0]['role'] == 'startup investigator' and own['completed_assignments'][0]['status'] == 'completed')
ownership = records['OWNERSHIP.json']
check('ownership_identity_and_no_lease', ownership['owner'] == task['owner'] and ownership['head'] == START and ownership['main_lease'] is False)
check('local_main_reference_unchanged', objid('refs/remotes/origin/main') == MAIN, 'Local observed main reference; no fresh network read performed by this auditor.')
protected_diff = subprocess.check_output(['git', 'diff', '--name-only', START, '--', 'docs/engineering/localized-repair-c271/path-design-p24'], cwd=REPO, text=True)
check('p24_design_bytes_unchanged', not protected_diff.strip())

result = {
    'schema': 'ontokin.c271.p25-independent-early-delivery-audit/1',
    'auditor': '/root/reconcile',
    'at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'scope': 'Saved early ZIP/readback and exact documentary P25 records; no product execution, implementation or adapter review in this report.',
    'starting_revision': START,
    'observed_main': MAIN,
    'archive': {'path': str(ARCHIVE), 'readback_path': str(READBACK), 'bytes': len(archive_bytes), 'sha256': sha(archive_bytes), 'library_file_id': receipt['library_file_id'], 'version': receipt['version']},
    'checks': checks,
    'summary': {'passed': sum(entry['status'] == 'passed' for entry in checks), 'failed': sum(entry['status'] == 'failed' for entry in checks)},
    'known_limits': ['Ownership PR/issue exact-body observations are Director claims pending retained readback reference; this script does not access the network.', 'Mechanical full-byte coverage does not mean semantic reading of every historical nested archive.', 'Historical P23 dependency member validated only at its declared nested P24 location, not unpacked or executed.', 'Fresh extraction is audit-only and removed after all exact byte/source comparisons.'],
    'inventory': inventory,
    'source_checks': source_results,
    'extracted_payload_checks': extraction_results,
    'canonical_preservation': canonical,
    'read_set': readset,
    'xattrs': attrs,
}
(OUT / 'EARLY-AUDIT.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'summary': result['summary'], 'failed': [entry for entry in checks if entry['status'] == 'failed'], 'report': str(OUT / 'EARLY-AUDIT.json')}, indent=2))
