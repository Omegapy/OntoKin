"""P22 independent predecessor audit. Only parses bytes and reads Git objects.

No archived or repository program is imported or executed. Outputs are confined to
the assigning Director's disjoint archive_audit directory.
"""
from __future__ import annotations

import base64
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import platform
import re
import stat
import subprocess
import sys
import zipfile
import zlib

ROOT = Path('/workspace/scratch/aa6113404163')
OUT = ROOT / 'phase-p22/archive_audit'
REPO = ROOT / 'OntoKin'
ZIP = ROOT / 'incoming/OntoKin_C271_P21_H0_Plan_Handoff_2026-11-22.zip'
EXTRACTED = ROOT / 'incoming/extracted'
RECEIPT = ROOT / 'prior-receipt/OntoKin/OntoKin_C271_P21_Delivery_Receipt_2026-11-22.json'
CORE = 'b5adba434e14d4448fce6fbc195a4c3729c2855a'
RCOMMIT = '527368bd5195c439762b43e2cc836ff9822213f8'
MAIN = '70ca7e68ff95df876f801137369d176fe5b2bab3'
BASE = 'b99f7e3bd33e6d2796d2732f97f21cdc3d04aaf9'
CANONICAL = 'docs/engineering/localized-repair-c271/h0-plan-p21/P21-DELIVERY.json'
AT = datetime.now(timezone.utc).isoformat()
OUT.mkdir(parents=True, exist_ok=True)
READS = []
CHECKS = {}
DETAILS = {}
FINDINGS = []


def sha(data):
    return hashlib.sha256(data).hexdigest()


def ident(data):
    return {'bytes': len(data), 'sha256': sha(data)}


def no_duplicate_keys(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError('Duplicate JSON key: ' + key)
        result[key] = value
    return result


def parse(data):
    return json.loads(data, object_pairs_hook=no_duplicate_keys)


def read(path, purpose='parsed_as_evidence'):
    data = path.read_bytes()
    READS.append({'path': str(path.relative_to(ROOT)), **ident(data), 'inspection': purpose})
    return data


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def check(name, result, details=None):
    CHECKS[name] = bool(result)
    if details is not None:
        DETAILS[name] = details
    if not result:
        FINDINGS.append(name)


def safe_name(name):
    if not name or '\\' in name or '\x00' in name or name.startswith('/'):
        return False
    if any(p in ('', '.', '..') for p in name.split('/')):
        return False
    if re.match(r'^[A-Za-z]:', name):
        return False
    return str(PurePosixPath(name)) == name


def git(*args):
    result = subprocess.run(['git', '-C', str(REPO), *args], capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr.decode('utf-8', 'replace').strip())
    return result.stdout


def git_commit(revision):
    raw = git('cat-file', 'commit', revision)
    computed = hashlib.sha1(b'commit ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
    headers = raw.split(b'\n\n', 1)[0].decode().splitlines()
    return {'revision': revision, 'computed_revision': computed,
            'tree': next(s[5:] for s in headers if s.startswith('tree ')),
            'parents': [s[7:] for s in headers if s.startswith('parent ')]}


def marker(body):
    matches = re.findall(r'<!-- C271-P21-TERMINAL-RECEIPT:\s*(.*?)\s*-->', body, re.S)
    if len(matches) != 1:
        raise ValueError(f'Expected exactly one P21 terminal marker, got {len(matches)}')
    return parse(matches[0])


governing = ['AGENTS.md', 'ROLE.md', 'docs/workflow/PROTOCOL.md',
             'docs/workflow/HANDOFF.md', 'docs/workflow/templates/WORKER.md']
for path in governing:
    data = read(REPO / path, 'full_text_read_once_before_audit; hash_recorded_now')
    READS[-1]['revision'] = RCOMMIT

archive_bytes = read(ZIP, 'full_archive_crc_inventory_byte_hash_audit')
check('incoming_zip_exact_identity', len(archive_bytes) == 9327161 and
      sha(archive_bytes) == 'ba03995347ed65a5a37b4283211841daf4da74fe4a04dbe0617f9e833e9bb64f', ident(archive_bytes))
with zipfile.ZipFile(ZIP) as archive:
    infos = archive.infolist()
    names = [i.filename for i in infos]
    check('zip_crc', archive.testzip() is None)
    check('zip_safe_unique_regular_inert_members',
          len(names) == len(set(names)) and all(safe_name(n) for n in names) and
          all(not i.is_dir() and not (i.flag_bits & 1) and
              stat.S_IFMT(i.external_attr >> 16) == stat.S_IFREG and
              stat.S_IMODE(i.external_attr >> 16) == 0o644 for i in infos),
          {'members': len(names), 'duplicates': [n for n, c in Counter(names).items() if c > 1],
           'unsafe': [n for n in names if not safe_name(n)],
           'modes': dict(Counter(oct(i.external_attr >> 16) for i in infos))})
    members = {name: archive.read(name) for name in names}

required = ['README-START-HERE.md', 'CHECKPOINT.json', 'HANDOFF.md', 'NEXT-TASK.md',
            'RECOVERY-STATUS.md', 'PROMPT-1-CONTINUE.md', 'PROMPT-2-RECOVER.md',
            'HISTORICAL-DEPENDENCIES.json', 'MANIFEST-SHA256.json']
check('required_root_files', all(n in members for n in required))
manifest = parse(members['MANIFEST-SHA256.json'])['files']
manifest_names = [f['path'] for f in manifest]
check('manifest_exact_unique_inventory', len(manifest_names) == len(set(manifest_names)) and
      set(manifest_names) == set(names) - {'MANIFEST-SHA256.json'})
manifest_errors = []
inventory = []
for item in manifest:
    actual = ident(members[item['path']])
    ok = actual == {'bytes': item['bytes'], 'sha256': item['sha256']}
    inventory.append({'path': item['path'], **actual, 'manifest_equal': ok})
    if not ok:
        manifest_errors.append(item['path'])
check('all_manifest_bytes_and_hashes', not manifest_errors, manifest_errors)
extracted_paths = [p for p in EXTRACTED.rglob('*') if p.is_file() or p.is_symlink()]
check('provided_extraction_exact_inventory_no_links',
      set(p.relative_to(EXTRACTED).as_posix() for p in extracted_paths) == set(names) and
      not any(p.is_symlink() for p in extracted_paths))
extraction_errors = [n for n in names if (EXTRACTED / n).read_bytes() != members[n]]
check('provided_extraction_every_byte_equal', not extraction_errors, extraction_errors)
save(OUT / 'PREDECESSOR-INVENTORY.json', inventory)

source = parse(members['SOURCE-MANIFEST.json'])['files']
source_names = [i['member'] for i in source]
check('source_manifest_exact_unique_snapshot_inventory',
      len(source_names) == len(set(source_names)) and
      set(source_names) == {n for n in names if n.startswith(('repository/', 'observed-main/'))})
source_results = []
missing_objects = set()
for item in source:
    data = members[item['member']]
    blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    result = {'member': item['member'], 'revision': item['revision'], 'path': item['path'],
              'declared_git_blob': item['git_blob'], 'computed_git_blob': blob,
              'package_fields_equal': ident(data) == {'bytes': item['bytes'], 'sha256': item['sha256']} and blob == item['git_blob']}
    try:
        entry = git('ls-tree', item['revision'], '--', item['path']).decode().strip()
        entry_head, entry_path = entry.split('\t', 1)
        mode, kind, object_id = entry_head.split(' ')
        git_data = git('cat-file', 'blob', item['revision'] + ':' + item['path'])
        result['git_fields_equal'] = entry_path == item['path'] and mode == item['source_mode'] and kind == 'blob' and object_id == item['git_blob'] and git_data == data
    except (RuntimeError, ValueError) as error:
        result['git_fields_equal'] = False
        result['error'] = str(error)
        missing_objects.add(item['revision'])
    source_results.append(result)
check('all_source_bindings_match_git_objects_modes_and_bytes',
      all(i['package_fields_equal'] and i['git_fields_equal'] for i in source_results),
      {'count': len(source_results), 'missing_revisions': sorted(missing_objects),
       'errors': [x for x in source_results if not (x['package_fields_equal'] and x['git_fields_equal'])]})
save(OUT / 'PREDECESSOR-SOURCE-BINDINGS.json', source_results)

recovery = parse(members['RECOVERY-FILE-MAP.json'])
recovery_names = [f['member'] for f in recovery['files']]
historical = parse(members['HISTORICAL-DEPENDENCIES.json'])
separate_predecessor = 'recovery/predecessor/P20-TERMINAL-RECEIPT.json'
predecessor_identity = historical['p20_terminal_receipt']
check('recovery_map_exact_unique_inventory', len(recovery_names) == len(set(recovery_names)) and
      set(recovery_names) == {n for n in names if n.startswith('recovery/')} - {separate_predecessor},
      {'mapped_session_files': len(recovery_names), 'separate_explicit_dependency': separate_predecessor,
       'partition_basis': 'RECOVERY-FILE-MAP maps session evidence. The separately preserved predecessor receipt is bound by HISTORICAL-DEPENDENCIES.p20_terminal_receipt; all paths remain covered by the whole-ZIP manifest.'})
check('separate_predecessor_receipt_exact_dependency_identity',
      ident(members[separate_predecessor]) == {'bytes': predecessor_identity['bytes'], 'sha256': predecessor_identity['sha256']})
check('recovery_map_all_bytes_hashes', all(ident(members[f['member']]) ==
      {'bytes': f['bytes'], 'sha256': f['sha256']} for f in recovery['files']))
wheels = parse(members['WHEEL-INPUTS.json'])['files']
check('wheel_inputs_exact_inventory_and_bytes', {f['member'] for f in wheels} ==
      {n for n in names if n.startswith('inputs/wheels/')} and all(ident(members[f['member']]) ==
      {'bytes': f['bytes'], 'sha256': f['sha256']} for f in wheels))

receipt_bytes = read(RECEIPT, 'full_json_postfreeze_blob_recoverability_audit')
receipt = parse(receipt_bytes)
check('terminal_receipt_exact_identity', len(receipt_bytes) == 222162 and
      sha(receipt_bytes) == '02d7987249a106b7f205e09f490fe2f35006ffdbf0f37da3dca91e21503082fe', ident(receipt_bytes))
postfreeze = receipt['postfreeze_recovery']
check('postfreeze_bound_to_actual_archive', postfreeze['base_archive_sha256'] == sha(archive_bytes))
blobs = {}
blob_results = []
for key, item in postfreeze['blobs'].items():
    compressed = base64.b64decode(item['data'], validate=True)
    decoder = zlib.decompressobj()
    data = decoder.decompress(compressed, item['bytes'] + 1)
    data += decoder.flush()
    valid = item['encoding'] == 'zlib+base64' and len(data) == item['bytes'] and sha(data) == key and decoder.eof and not decoder.unused_data and not decoder.unconsumed_tail
    blobs[key] = data
    blob_results.append({'sha256': key, 'declared_bytes': item['bytes'], 'actual_bytes': len(data), 'verified': valid})
check('all_embedded_blobs_decode_exactly', all(r['verified'] for r in blob_results), blob_results)
record_names = [r['session_path'] for r in postfreeze['files']]
check('postfreeze_records_safe_unique', len(record_names) == len(set(record_names)) and all(safe_name(n) for n in record_names))
record_results = []
post = {}
for item in postfreeze['files']:
    data = blobs[item['blob_sha256']]
    post[item['session_path']] = data
    equal = ident(data) == {'bytes': item['bytes'], 'sha256': item['sha256']}
    prior = members.get('recovery/session/' + item['session_path'])
    changed = prior is None or prior != data
    result = {'path': item['session_path'], **ident(data), 'record_equal': equal,
              'base_archive_state': 'new' if prior is None else 'changed' if changed else 'identical'}
    record_results.append(result)
    if equal and safe_name(item['session_path']):
        dest = OUT / 'recovered-postfreeze' / item['session_path']
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        dest.chmod(0o644)
check('all_postfreeze_records_recover_exact_bytes', all(r['record_equal'] for r in record_results), record_results)
check('postfreeze_records_only_new_or_changed', all(r['base_archive_state'] != 'identical' for r in record_results))
check('no_unreferenced_embedded_blobs', set(blobs) == {f['blob_sha256'] for f in postfreeze['files']})
save(OUT / 'POSTFREEZE-RECOVERABILITY.json', {'blob_count': len(blobs), 'files': record_results,
     'boundary': 'Exact byte recovery demonstrated. No recovered code was executed. Original entire predecessor filesystem is unavailable, so historical inventory completeness is supported by the separately preserved independent terminal review rather than newly re-observed.'})

canonical_bytes = read(REPO / CANONICAL)
canonical = parse(canonical_bytes)
check('terminal_final_save_equals_canonical_delivery', receipt['final_save'] == canonical)
check('canonical_delivery_equals_postfreeze_saved_receipt', canonical_bytes == post['state/FINAL-SAVE-RECEIPT.json'])
checkpoint = parse(members['CHECKPOINT.json'])
check('core_receipt_checkpoint_identities_agree',
      checkpoint['source_revision'] == receipt['source_revision'] == canonical['source_revision'] == CORE and
      checkpoint['source_tree'] == receipt['source_tree'] == canonical['source_tree'] and receipt['receipt_commit'] == RCOMMIT)
check('archive_saved_record_matches_actual_bytes',
      canonical['archive']['bytes'] == len(archive_bytes) and canonical['archive']['sha256'] == sha(archive_bytes) and
      canonical['archive']['status'] == 'succeeded' and canonical['archive']['saved_bytes_readback_equal'] is True)
check('matching_prompt_records_match_archive_members', all(
      ident(members[p['zip_member']]) == {'bytes': p['bytes'], 'sha256': p['sha256']} and
      p['saved_bytes_readback_equal'] is True and p['zip_member_equal'] is True for p in canonical['matching_prompts']))

commits = {}
for revision in (CORE, RCOMMIT, MAIN, BASE):
    try:
        commits[revision] = git_commit(revision)
    except RuntimeError as error:
        commits[revision] = {'revision': revision, 'unavailable': str(error)}
check('core_receipt_main_exact_git_commit_tree_chain',
      commits.get(CORE, {}).get('tree') == checkpoint['source_tree'] and
      commits.get(CORE, {}).get('parents') == [BASE] and
      commits.get(RCOMMIT, {}).get('tree') == receipt['receipt_tree'] and
      commits.get(RCOMMIT, {}).get('parents') == [CORE] and
      commits.get(MAIN, {}).get('tree') == checkpoint['observed_main']['tree'] and
      all(commits[c].get('computed_revision') == c for c in (CORE, RCOMMIT, MAIN)), commits)
try:
    check('canonical_delivery_equals_receipt_git_object', canonical_bytes == git('cat-file', 'blob', RCOMMIT + ':' + CANONICAL))
except RuntimeError as error:
    check('canonical_delivery_equals_receipt_git_object', False, str(error))

pr_input = parse(read(ROOT / 'state/initial-3.json'))
issue_input = parse(read(ROOT / 'state/reconcile-0.json'))
pr = pr_input['structuredContent']['issues'][0]
issue = issue_input['structuredContent']['issue']
pr_marker = marker(pr['body'])
issue_marker = marker(issue['body'])
check('both_live_p21_terminal_markers_exactly_equal', pr_marker == issue_marker)
check('live_terminal_identities_match_actual_receipt_archive_and_commits',
      ident(receipt_bytes) == {'bytes': pr_marker['terminal_receipt']['bytes'], 'sha256': pr_marker['terminal_receipt']['sha256']} and
      pr_marker['archive'] == canonical['archive'] and pr_marker['matching_prompts'] == canonical['matching_prompts'] and
      pr_marker['core_source_revision'] == CORE and pr_marker['core_source_tree'] == checkpoint['source_tree'] and
      pr_marker['receipt_revision'] == RCOMMIT and pr_marker['receipt_tree'] == receipt['receipt_tree'])
check('live_completion_resolves_only_delivery',
      pr_marker['phase_complete'] is True and pr_marker['parent_complete'] is False and
      pr_marker['parent_status'] == 'blocked' and pr_marker['h0_accepted'] is False and
      pr_marker['requirements'] == receipt['requirements'] and
      pr_marker['first_remaining_action'] == receipt['next_fresh_action'] == checkpoint['first_next_phase_action'])
check('live_pr_issue_retained_open_unmerged', pr['number'] == 274 and pr['state'] == 'open' and
      pr['draft'] is True and pr['merged'] is False and pr['head_sha'] == RCOMMIT and
      issue['issue_number'] == 273 and issue['state'] == 'open')
marker_artifacts = []
for item in pr_marker['exact_terminal_review_artifacts']:
    data = item['content_utf8'].encode()
    valid = safe_name(item['path']) and ident(data) == {'bytes': item['bytes'], 'sha256': item['sha256']}
    marker_artifacts.append({'path': item['path'], **ident(data), 'verified': valid})
    if valid:
        dest = OUT / 'recovered-terminal-marker' / item['path']
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        dest.chmod(0o644)
        if item['path'].endswith('TERMINAL-REVIEW.json'):
            check('inline_terminal_review_equals_structured_review', parse(data) == pr_marker['independent_terminal_review'])
check('all_terminal_review_artifact_bytes_recoverable', all(i['verified'] for i in marker_artifacts), marker_artifacts)
check('terminal_review_targets_actual_receipt', pr_marker['independent_terminal_review']['artifact'] ==
      {'file_name': RECEIPT.name, **ident(receipt_bytes)} and pr_marker['independent_terminal_review']['verdict'] == 'accepted_for_save')
check('saved_terminal_receipt_live_record_confirmed',
      pr_marker['terminal_receipt']['status'] == 'succeeded' and
      pr_marker['terminal_receipt']['saved_bytes_readback_equal'] is True and
      pr_marker['terminal_receipt']['version'] == 0)
save(OUT / 'P21-TERMINAL-MARKER.json', pr_marker)

final_review = parse(post['recovery_audit/FINAL-REVIEW.json'])
save_review = parse(post['recovery_audit/SAVE-READBACK-REVIEW.json'])
check('final_archive_review_exactly_bound', sha(post['recovery_audit/FINAL-REVIEW.json']) ==
      canonical['package_review']['sha256'] == pr_marker['independent_terminal_review']['reused_evidence']['final_archive_review_sha256'])
check('saved_readback_review_exactly_bound', sha(post['recovery_audit/SAVE-READBACK-REVIEW.json']) ==
      pr_marker['independent_terminal_review']['reused_evidence']['save_readback_review_sha256'])
check('final_archive_and_save_reviews_accepted',
      final_review['verdict'] == 'accepted_for_save' and not final_review['required_findings'] and
      all(c['passed'] is True for c in final_review['checks']) and
      save_review['verdict'] == 'accepted_confirmed_saved_artifacts_and_readback' and
      all(c['passed'] is True for c in save_review['checks']))
check('preserved_initial_final_review_failure_retained',
      'recovery_audit/FINAL-REVIEW.before-name-normalization.json' in post and
      bool(final_review.get('initial_observation_disposition')))

publication_checks = []
for label, commit in [('core', CORE), ('receipt', RCOMMIT)]:
    prefix = 'publication/' + label + '/'
    getdata = (lambda path: members['recovery/session/' + path]) if label == 'core' else (lambda path: post[path])
    payload_bytes = getdata(prefix + 'PAYLOAD.json')
    payload = parse(payload_bytes)
    intent = parse(getdata(prefix + 'INTENT.json'))
    readback = parse(getdata(prefix + 'READBACK.json'))
    entries = payload['tree_elements']
    entry_paths = [e['path'] for e in entries]
    entry_results = []
    by_path = {e['path']: e for e in intent['files']}
    for entry in entries:
        content = entry['content'].encode()
        git_entry = git('ls-tree', commit, '--', entry['path']).decode().strip()
        metadata, path = git_entry.split('\t', 1)
        mode, kind, blob_id = metadata.split(' ')
        descriptor = by_path.get(entry['path'], {})
        valid = (git('cat-file', 'blob', commit + ':' + entry['path']) == content and
                 mode == entry['mode'] == descriptor.get('mode') and kind == entry['type'] == 'blob' and
                 blob_id == descriptor.get('blob') and
                 ident(content) == {'bytes': descriptor.get('bytes'), 'sha256': descriptor.get('sha256')})
        entry_results.append({'path': path, 'verified': valid, **ident(content)})
    equal = (len(entry_paths) == len(set(entry_paths)) == (63 if label == 'core' else 4) and
             set(entry_paths) == set(by_path) and
             all(e['verified'] for e in entry_results) and
             ident(payload_bytes) == {'bytes': intent['payload_bytes'], 'sha256': intent['payload_sha256']} and
             intent['conditional_update'] is True and intent['force'] is False and
             readback == receipt['core_publication' if label == 'core' else 'receipt_publication'] and
             readback['source_revision'] == commit and readback['all_published_bytes_equal'] is True)
    publication_checks.append({'publication': label, 'commit': commit, 'verified': equal, 'files': entry_results})
check('both_preserved_publication_payloads_exactly_match_git_and_receipt',
      all(p['verified'] for p in publication_checks), publication_checks)

def tree_entries(revision):
    entries = {}
    for row in git('ls-tree', '-r', '-z', revision).split(b'\0'):
        if row:
            metadata, name = row.split(b'\t', 1)
            entries[name.decode()] = metadata.decode()
    return entries

core_tree, receipt_tree = tree_entries(CORE), tree_entries(RCOMMIT)
actual_receipt_delta = sorted(p for p in set(core_tree) | set(receipt_tree) if core_tree.get(p) != receipt_tree.get(p))
receipt_payload_paths = sorted(e['path'] for e in parse(post['publication/receipt/PAYLOAD.json'])['tree_elements'])
check('receipt_commit_exact_four_file_delta', actual_receipt_delta == receipt_payload_paths, actual_receipt_delta)

log_checks = []
for label in ['core', 'receipt']:
    descriptor = receipt['published_' + label + '_checks']
    session_prefix = 'checks/published-' + label + '/'
    getdata = (lambda path: members['recovery/session/' + path]) if label == 'core' else (lambda path: post[path])
    actual_result = parse(getdata(session_prefix + 'RESULT.json'))
    group_ok = actual_result == descriptor and descriptor['all_passed'] is True and descriptor['source_revision'] == (CORE if label == 'core' else RCOMMIT)
    for command in descriptor['checks']:
        command_ok = command['exit_code'] == 0
        for stream in ['stdout', 'stderr']:
            log_descriptor = command[stream]
            session_path = log_descriptor['path'].split('/phase-p21/', 1)[1]
            command_ok = command_ok and ident(getdata(session_path)) == {'bytes': log_descriptor['bytes'], 'sha256': log_descriptor['sha256']}
        log_checks.append({'publication': label, 'check': command['name'], 'command_and_all_logs_bound': command_ok})
        group_ok = group_ok and command_ok
    check('published_' + label + '_record_check_results_and_logs_bound', group_ok)
DETAILS['published_check_logs'] = log_checks
check('source_time_pending_fields_resolved_by_later_terminal_only',
      checkpoint['delivery_state_at_freeze'] == 'save_pending' and checkpoint['phase_complete'] is False and
      canonical['phase_complete_at_receipt_freeze'] is False and receipt['phase_complete_at_freeze'] is False and
      pr_marker['phase_complete'] is True and pr_marker['parent_complete'] is False)

check('postfreeze_additional_exclusion_is_exact_archive_derivative',
      postfreeze['additional_derived_exclusion']['source_archive_sha256'] == sha(archive_bytes) and
      postfreeze['additional_derived_exclusion']['files_verified'] == len(names) and
      postfreeze['additional_derived_exclusion']['inventory_and_every_hash_equal'] is True)

for name in required + ['SOURCE-MANIFEST.json', 'RECOVERY-FILE-MAP.json', 'RECOVERY-EXCLUSIONS.json', 'WHEEL-INPUTS.json']:
    READS.append({'path': 'incoming/extracted/' + name, **ident(members[name]),
                  'inspection': 'full_bytes_checked; structured_fields_or_scope_text_inspected',
                  'archive_sha256': sha(archive_bytes)})

result = {
    'schema': 'ontokin.c271.p22-predecessor-review/1',
    'reviewer': '/root/archive_audit', 'at_utc': AT,
    'verdict': 'accepted_predecessor_delivery_reconciled' if not FINDINGS else 'findings_require_resolution',
    'archive': {'path': str(ZIP), **ident(archive_bytes)},
    'terminal_receipt': {'path': str(RECEIPT), **ident(receipt_bytes)},
    'counts': {'archive_members': len(names), 'manifest_files': len(manifest),
               'source_bindings': len(source), 'recovery_files': len(recovery['files']),
               'wheels': len(wheels), 'postfreeze_files': len(record_results),
               'postfreeze_blobs': len(blobs), 'terminal_review_artifacts': len(marker_artifacts),
               'check_groups': len(CHECKS), 'passed': sum(CHECKS.values())},
    'checks': CHECKS, 'findings': FINDINGS, 'details': DETAILS,
    'missing_source_objects': sorted(missing_objects),
    'scope_and_limits': [
        'Read-only independent archive, receipt, Git object and live-state-evidence audit. No technical programs or recovered scripts executed.',
        'Git objects were read only after the Director explicitly allowed cat-file/ls-tree/show. No fetch, ref/index/canonical mutation, upload, package build or publication performed.',
        'All declared 39 postfreeze records and both later terminal-review artifacts are byte recoverable; predecessor filesystem completeness is not newly provable from this new workspace.',
        'Confirmed live markers and actual materialized ZIP/receipt bytes reconcile source-time delivery-pending fields only. H0/H1, full-routine, integration and parent task completion remain unmet.',
        'Current user authorization, fresh phase selection, accepted operation plan and early saved recovery remain Director-owned gates before new technical execution.'
    ],
    'parent_status': 'blocked', 'parent_complete': False, 'h0_accepted': False,
    'next_action': 'Director may treat P21 saved-delivery reconciliation as passed if all review checks pass; continue only the authorized P22 prerequisite phase after its other startup and early-save gates.'
}
save(OUT / 'PREDECESSOR-REVIEW.json', result)
save(OUT / 'READSET.json', {'schema': 'ontokin.c271.p22-worker-readset/1',
     'worker': '/root/archive_audit', 'at_utc': AT,
     'base_revision': RCOMMIT, 'global_startup': 'Director owned; not repeated',
     'governing_instructions_full_read_once': governing,
     'reads': READS,
     'environment': {'python': sys.version, 'platform': platform.platform()},
     'command': 'python3 phase-p22/archive_audit/audit_predecessor.py',
     'unresolved_required_gaps': sorted(missing_objects)})
summary = f'''# P21 predecessor delivery review

**{result['verdict']}.** {sum(CHECKS.values())}/{len(CHECKS)} substantive check groups passed.

The exact {len(archive_bytes):,}-byte ZIP has SHA-256 `{sha(archive_bytes)}`. Its {len(names)} inert regular members pass CRC, unique safe-path, exact inventory and every manifest size/hash check. All {len(source)} repository snapshot bindings are checked against exact Git commit/path/blob/mode and bytes. The {len(recovery['files'])} recovery entries and seven wheel inputs match their declared identities.

The separate {len(receipt_bytes):,}-byte terminal receipt has SHA-256 `{sha(receipt_bytes)}`. All {len(blobs)} compressed blobs and {len(record_results)} postfreeze records are byte recoverable. The two later terminal-review artifacts are also recovered exactly from the matching live PR274 and issue273 marker copies. The published canonical receipt, immutable ZIP, separate receipt and live markers agree on source/receipt commits, archive identity, prompt identities and the delivery boundary.

Parent C271 remains blocked/open, H0 unaccepted, and R03–R05 remain not_done. This audit reconciles P21 delivery; it does not accept a new operation plan or satisfy P22's early saved-recovery gate. The original predecessor workspace is unavailable, so exact recovery of every declared preserved byte is verified here; its historical complete-inventory claim remains supported by the exact preserved independent review.

Findings: {', '.join(FINDINGS) if FINDINGS else 'none'}.

No technical program, recovered script, package build, upload, Git mutation, canonical mutation or publication was performed. Detailed checks and identities are in PREDECESSOR-REVIEW.json; source bindings, inventory and postfreeze details are separate adjacent evidence files.
'''
(OUT / 'PREDECESSOR-REVIEW.md').write_text(summary)
print(json.dumps({'verdict': result['verdict'], 'counts': result['counts'],
                  'findings': FINDINGS, 'missing_source_objects': sorted(missing_objects)}))
