#!/usr/bin/env python3
"""Read-only integrity and receipt audit of the supplied C271 P28 R02 package."""
from __future__ import annotations

import collections
import datetime as dt
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import platform
import re
import stat
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path('/workspace/scratch/2eb33b59a678')
OUT = ROOT / 'reviews/input-audit'
ZIP = ROOT / 'inputs/OntoKin/OntoKin_C271_P28_R02_Recovery_Checkpoint_2026-11-23.zip'
RECEIPT = ROOT / 'inputs/OntoKin/OntoKin_C271_P28_R02_Delivery_Receipt_2026-11-23.json'
EXTRACTED = ROOT / 'inputs/checkpoint'
REPO = ROOT / 'repository'
checks: list[dict] = []


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def check(name: str, passed: bool, **details) -> None:
    checks.append({'check': name, 'status': 'passed' if passed else 'failed', **details})


def safe(name: str) -> bool:
    value = name[:-1] if name.endswith('/') else name
    return bool(value) and not any((
        '\\' in value, '\x00' in value, value.startswith('/'),
        bool(PureWindowsPath(value).drive),
        any(part in ('', '.', '..') for part in value.split('/')),
        str(PurePosixPath(value)) != value,
    ))


def git(*args: str) -> bytes:
    env = {**os.environ, 'GIT_OPTIONAL_LOCKS': '0'}
    return subprocess.run(['git', '-C', str(REPO), *args], check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env).stdout


def identity(path: Path) -> dict:
    data = path.read_bytes()
    return {'path': str(path.relative_to(ROOT)), 'file_name': path.name,
            'bytes': len(data), 'sha256': sha(data)}


OUT.mkdir(parents=True, exist_ok=True)
archive_identity = identity(ZIP)
receipt_identity = identity(RECEIPT)
receipt = json.loads(RECEIPT.read_bytes())
check('outer_archive_matches_saved_receipt', all(
    archive_identity[k] == receipt['archive'][k] for k in ('file_name', 'bytes', 'sha256')),
    actual=archive_identity, receipt_archive=receipt['archive'])

with zipfile.ZipFile(ZIP) as z:
    members = z.infolist()
    names = [x.filename for x in members]
    files = [x for x in members if not x.is_dir()]
    file_names = {x.filename for x in files}
    unsafe = [x.filename for x in members if not safe(x.filename)]
    duplicates = [name for name, n in collections.Counter(names).items() if n != 1]
    special = [x.filename for x in members
               if stat.S_IFMT(x.external_attr >> 16) not in (0, stat.S_IFREG, stat.S_IFDIR)]
    check('zip_crc', z.testzip() is None, members=len(members))
    check('zip_safe_relative_paths', not unsafe, unsafe=unsafe)
    check('zip_no_duplicate_members', not duplicates, duplicates=duplicates)
    check('zip_no_links_or_special_members', not special, special=special)
    check('zip_no_encrypted_members', not any(x.flag_bits & 1 for x in members))
    manifest = json.loads(z.read('MANIFEST-SHA256.json'))
    sources = json.loads(z.read('SOURCE-MANIFEST.json'))
    checkpoint = json.loads(z.read('CHECKPOINT.json'))
    manifest_schema = isinstance(manifest, list) and all(
        isinstance(x, dict) and set(x) == {'path', 'bytes', 'sha256'}
        and isinstance(x['path'], str) and safe(x['path'])
        and type(x['bytes']) is int and x['bytes'] >= 0
        and bool(re.fullmatch('[0-9a-f]{64}', x['sha256'])) for x in manifest)
    source_keys = {'archive_path', 'git_path', 'commit', 'git_blob', 'git_mode', 'bytes', 'sha256'}
    source_schema = isinstance(sources, list) and all(
        isinstance(x, dict) and set(x) == source_keys
        and safe(x['archive_path']) and safe(x['git_path'])
        and bool(re.fullmatch('[0-9a-f]{40}', x['commit']))
        and bool(re.fullmatch('[0-9a-f]{40}', x['git_blob']))
        and x['git_mode'] == '100644' and type(x['bytes']) is int and x['bytes'] >= 0
        and bool(re.fullmatch('[0-9a-f]{64}', x['sha256'])) for x in sources)
    check('payload_manifest_observed_schema', manifest_schema,
          root_type=type(manifest).__name__, entries=len(manifest), keys=sorted(manifest[0]))
    check('source_manifest_observed_schema', source_schema,
          root_type=type(sources).__name__, entries=len(sources), keys=sorted(sources[0]))
    manifest_names = [x['path'] for x in manifest]
    check('payload_manifest_unique_paths', len(manifest_names) == len(set(manifest_names)))
    expected_inventory = set(manifest_names) | {'MANIFEST-SHA256.json'}
    check('zip_exact_inventory', file_names == expected_inventory,
          missing=sorted(expected_inventory - file_names), extra=sorted(file_names - expected_inventory),
          members=len(members), files=len(files), directories=len(members)-len(files), payloads=len(manifest))
    required = {'README-START-HERE.md', 'CHECKPOINT.json', 'HANDOFF.md', 'NEXT-TASK.md',
                'RECOVERY-STATUS.md', 'PROMPT-1-CONTINUE.md', 'PROMPT-2-RECOVER.md',
                'HISTORICAL-DEPENDENCIES.json', 'MANIFEST-SHA256.json', 'HOST-ENVIRONMENT.md'}
    check('required_handoff_root_files', required <= file_names, missing=sorted(required-file_names))
    for entry in manifest:
        data = z.read(entry['path'])
        check('payload_size_sha256', len(data) == entry['bytes'] and sha(data) == entry['sha256'],
              path=entry['path'], bytes=len(data), sha256=sha(data))

    extracted_names = {p.relative_to(EXTRACTED).as_posix() for p in EXTRACTED.rglob('*') if p.is_file()}
    extracted_links = [p.relative_to(EXTRACTED).as_posix() for p in EXTRACTED.rglob('*') if p.is_symlink()]
    check('supplied_extraction_exact_inventory', extracted_names == file_names and not extracted_links,
          missing=sorted(file_names-extracted_names), extra=sorted(extracted_names-file_names), symlinks=extracted_links)
    for name in sorted(file_names):
        p = EXTRACTED / name
        check('supplied_extraction_matches_zip', p.is_file() and p.read_bytes() == z.read(name), path=name)
    if not (unsafe or duplicates or special):
        with tempfile.TemporaryDirectory(prefix='fresh-extract-', dir=OUT) as tmp:
            z.extractall(tmp)
            fresh = Path(tmp)
            fresh_names = {p.relative_to(fresh).as_posix() for p in fresh.rglob('*') if p.is_file()}
            mismatch = [name for name in sorted(file_names)
                        if not (fresh / name).is_file() or (fresh / name).read_bytes() != z.read(name)]
            check('fresh_safe_extraction_exact_inventory_and_bytes', fresh_names == file_names and not mismatch,
                  files=len(fresh_names), mismatch=mismatch, temporary_extraction_removed_after_audit=True)

    source_names = [x['archive_path'] for x in sources]
    frozen_names = {name for name in file_names if name.startswith(('repository/', 'branch-state/'))}
    check('source_manifest_unique_paths', len(source_names) == len(set(source_names)))
    check('source_manifest_covers_frozen_git_snapshots', set(source_names) == frozen_names,
          missing=sorted(frozen_names-set(source_names)), extra=sorted(set(source_names)-frozen_names))
    source_results = []
    for entry in sources:
        data = z.read(entry['archive_path'])
        blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        tree_record = git('ls-tree', '-z', entry['commit'], '--', entry['git_path'])
        expected_record = f"{entry['git_mode']} blob {entry['git_blob']}\t{entry['git_path']}\0".encode()
        committed_data = git('cat-file', 'blob', entry['git_blob'])
        info = z.getinfo(entry['archive_path'])
        zip_permissions = stat.S_IMODE(info.external_attr >> 16)
        ok = (len(data) == entry['bytes'] and sha(data) == entry['sha256']
              and blob == entry['git_blob'] and tree_record == expected_record
              and committed_data == data and zip_permissions == 0o644)
        check('frozen_source_exact_git_binding', ok, archive_path=entry['archive_path'],
              git_path=entry['git_path'], commit=entry['commit'], git_blob=blob,
              git_mode=entry['git_mode'], zip_permissions=oct(zip_permissions), bytes=len(data), sha256=sha(data),
              exact_path_mode_blob_at_commit=tree_record == expected_record, committed_bytes_equal=committed_data == data)
        source_results.append({**entry, 'verified': ok})
    check('declared_source_commits', set(x['commit'] for x in sources) ==
          {checkpoint['source_commit'], checkpoint['observed_main']})
    for field, tree_field in [('source_commit', 'source_tree'), ('observed_main', 'observed_main_tree')]:
        actual_tree = git('rev-parse', checkpoint[field] + '^{tree}').decode().strip()
        check('checkpoint_commit_tree_binding', actual_tree == checkpoint[tree_field],
              commit=checkpoint[field], declared_tree=checkpoint[tree_field], actual_tree=actual_tree)
    check('checkpoint_matches_external_receipt_identity', all([
        checkpoint['source_commit'] == receipt['source_commit'], checkpoint['source_tree'] == receipt['source_tree'],
        checkpoint['observed_main'] == receipt['main'], checkpoint['branch'] == receipt['branch'],
        checkpoint['pull_request'] == receipt['pr'], checkpoint['scope_issue'] == receipt['issue'],
        checkpoint['phase'] == receipt['phase']]))
    check('source_time_pending_delivery_is_explicit', checkpoint['phase_complete'] is False
          and checkpoint['parent_complete'] is False and 'pending' in checkpoint['library_save_state']
          and receipt['phase_complete'] is True and receipt['parent_complete'] is False)
    for prompt, declared in zip(['PROMPT-1-CONTINUE.md', 'PROMPT-2-RECOVER.md'], receipt['prompts']):
        data = z.read(prompt)
        check('packaged_prompt_matches_saved_receipt', len(data) == declared['bytes'] and sha(data) == declared['sha256'],
              archive_path=prompt, saved_name=declared['file_name'], bytes=len(data), sha256=sha(data))

terminal_records = []
comment_inputs = []
for relative in ['session/issue273_comments.json', 'session/pr274_comments.json']:
    path = ROOT / relative
    data = json.loads(path.read_bytes())
    comment_inputs.append({**identity(path), 'comments': len(data['comments'])})
    latest = max(data['comments'], key=lambda x: x['id'])
    block = re.search(r'<!-- ONTOKIN-C271-P28-R02-TERMINAL:BEGIN -->\s*```json\s*(.*?)\s*```\s*<!-- ONTOKIN-C271-P28-R02-TERMINAL:END -->', latest['body'], re.S)
    check('latest_supplied_comment_has_r02_terminal', block is not None, input=relative, id=latest['id'], url=latest['url'])
    terminal = json.loads(block.group(1)) if block else {}
    terminal_records.append({'input': relative, 'id': latest['id'], 'url': latest['url'], 'terminal': terminal})
    check('terminal_archive_matches_receipt', all(terminal['archive'][k] == receipt['archive'][k]
          for k in ['library_file_id', 'version', 'bytes', 'sha256']), input=relative)
    check('terminal_external_receipt_exact_bytes', all(terminal['external_receipt'][k] == receipt_identity[k]
          for k in ['file_name', 'bytes', 'sha256']), input=relative, actual=receipt_identity)
    check('terminal_identity_matches_receipt_and_checkpoint', all([
        terminal['source_commit'] == checkpoint['source_commit'],
        terminal['receipt_commit'] == receipt['receipt_publication']['commit'],
        terminal['branch'] == receipt['branch'], terminal['main'] == receipt['main'],
        terminal['pr'] == receipt['pr'], terminal['issue'] == receipt['issue'],
        terminal['phase'] == receipt['phase'], terminal['owner'] == receipt['ownership']['owner']]), input=relative)
    check('terminal_resolves_delivery_only', all([
        terminal['phase_complete'] is True, terminal['parent_complete'] is False,
        terminal['parent_status'] == 'blocked', terminal['blocker'] == 'P28-RECOVERY-BYTES-001',
        terminal['original_p28_implementation_verified'] is False,
        terminal['original_597_tests'] == 'reported_unverified', terminal['original_uploads'] == 'unresolved_not_replayed',
        terminal['main_lease_held'] is False, terminal['branch_retained'] is True,
        terminal['pr_state'] == 'draft_open_unmerged', terminal['issue_state'] == 'open',
        terminal['ownership'] == 'released_after_both_matching_terminal_readbacks',
        terminal['requirements'] == {'R01': 'done', 'R02': 'done', 'R03': 'not_done', 'R04': 'not_done', 'R05': 'not_done'},
        terminal['plan'] == {'P01': 'done', 'P02': 'in_progress'},
        'resolve only' in terminal['terminal_effect'], 'do not recover original P28' in terminal['terminal_effect']]),
        input=relative, terminal_effect=terminal['terminal_effect'])
check('issue_and_pr_terminals_exactly_match', terminal_records[0]['terminal'] == terminal_records[1]['terminal'])
check('historical_product_test_claim_remains_unverified', receipt['original_p28_implementation_verified'] is False
      and receipt['product_tests_executed'] == 0 and checkpoint['original_p28_implementation_verified'] is False
      and checkpoint['product_tests_executed'] == 0
      and '597/597 original P28 tests' in checkpoint['reported_but_not_reverified'])

failed = [x for x in checks if x['status'] == 'failed']
result = {
    'schema': 'ontokin.c271.supplied-r02-input-audit/1',
    'reviewer': '/root/handoff_audit',
    'recorded_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
    'verdict': 'pass_with_original_p28_missing' if not failed else 'failed',
    'scope': 'Supplied outer R02 package, external receipt, declared frozen Git snapshots, and supplied live comment snapshots only.',
    'environment': {'python': sys.version, 'platform': platform.platform(), 'git': git('--version').decode().strip()},
    'command': 'python3 reviews/input-audit/audit.py',
    'archive': archive_identity,
    'external_receipt': receipt_identity,
    'counts': {'zip_members': len(members), 'zip_files': len(files), 'zip_directories': len(members)-len(files),
               'manifest_payloads': len(manifest), 'source_bindings': len(sources),
               'source_bindings_by_commit': dict(collections.Counter(x['commit'] for x in sources)),
               'passed_checks': len(checks)-len(failed), 'failed_checks': len(failed),
               'issue_comments_supplied': comment_inputs[0]['comments'], 'pr_comments_supplied': comment_inputs[1]['comments'],
               'product_tests_executed': 0},
    'comment_inputs': comment_inputs,
    'terminal_records': terminal_records,
    'missing_inputs': [
        'Exact original P28 final uploaded tree SHA with complete publication manifest/group inventory, or a saved implementation/fixtures/tests/review artifact.',
        'Alternatively, an explicit bounded reconstruction decision under adopted P27; this audit does not supply that decision.'
    ],
    'limits': [
        'No product code or product tests executed; the historical 597/597 claim remains unverified.',
        'No recursive reconstruction or qualification of predecessor archives; they are verified only as outer-package payload bytes.',
        'Latest terminal means greatest supplied comment ID; comment snapshots have no pagination-completeness metadata or creation timestamps. Director owns live GitHub reconciliation.',
        'No fresh Library save/readback was performed by this worker; exact supplied bytes match the saved receipt and matching supplied terminal identities.',
        'Source path, mode, blob, content and commit trees were checked against the freshly cloned authentic repository objects; no branch/index/ref was modified.'
    ],
    'read_paths': [
        'governing-main/AGENTS.md', 'governing-main/ROLE.md', 'governing-main/docs/workflow/PROTOCOL.md',
        'governing-main/docs/workflow/HANDOFF.md', 'governing-main/docs/workflow/templates/WORKER.md',
        'governing-main/docs/workflow/EPHEMERAL-HOST.md',
        'governing-main/docs/engineering/OK-ENG-006-local-validation-and-hosted-ci-policy.md',
        'inputs/checkpoint/SOURCE-MANIFEST.json', 'inputs/checkpoint/MANIFEST-SHA256.json',
        'inputs/checkpoint/CHECKPOINT.json', 'inputs/checkpoint/README-START-HERE.md',
        'inputs/checkpoint/HANDOFF.md', 'inputs/checkpoint/NEXT-TASK.md',
        'inputs/checkpoint/RECOVERY-STATUS.md', 'inputs/checkpoint/HOST-ENVIRONMENT.md',
        str(RECEIPT.relative_to(ROOT)), *[x['path'] for x in comment_inputs]
    ],
    'checks': checks,
    'source_bindings': source_results,
    'discrepancies': failed,
    'publication_or_integration': 'none',
    'workers_or_unknown_operations_remaining': [],
}
(OUT / 'CHECKS.json').write_text(json.dumps(result, indent=2) + '\n')
report = f'''# Supplied recovery input audit

Verdict: **{'PASS within the supplied-input scope' if not failed else 'FAIL; inspect CHECKS.json'}**. The ZIP is {archive_identity['bytes']:,} bytes, SHA-256 `{archive_identity['sha256']}`; its filename, size and hash match the saved external receipt. The receipt is {receipt_identity['bytes']:,} bytes, SHA-256 `{receipt_identity['sha256']}`, matching both terminal records.

Verified {len(members)} ZIP members ({len(files)} files, {len(members)-len(files)} directories), {len(manifest)} payload manifest entries and {len(sources)} frozen Git bindings: 39 at `942096d22248fd84b7ac3a638e02aa1e66340519`, 19 at `e43cc6c5777874101a40559e4058ad6826b07e51`. CRC, safe paths, uniqueness, complete inventory, fresh extraction, supplied extraction, sizes/hashes, Git paths/modes/blobs/content and declared commit trees passed. {len(checks)-len(failed)} checks passed; {len(failed)} failed.

The latest supplied issue/PR terminals (`7115412292` / `7115411913`) match exactly and resolve R02 delivery/publication/ownership only. C271 remains blocked; PR274 stays draft/unmerged, issue273 open, branch retained. Original P28 uploads remain unresolved and unreplayed.

Missing: exact original P28 final tree plus complete publication inventory, or a saved implementation/fixtures/tests/review artifact; alternatively, an explicit bounded reconstruction decision. The **597 reported original tests remain unverified**; this worker ran zero product tests.

No byte discrepancy found. Comment pagination completeness was not supplied. Predecessor internals were not recursively audited; no fresh Library operation occurred. Evidence: `CHECKS.json`, reproducible audit: `audit.py`. No repository mutation, publication, prior-host access or outstanding operation. Return to Director; stop.
'''
(OUT / 'REPORT.md').write_text(report)
print(json.dumps({'verdict': result['verdict'], 'counts': result['counts'],
                  'report_words': len(report.split()), 'failures': failed}, indent=2))
sys.exit(1 if failed else 0)
