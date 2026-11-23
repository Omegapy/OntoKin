"""Independent, read-only audit of the supplied P22 amended handoff.

Only this newly authored reviewer script executes. Archive code remains inert.
All writes stay within the assigned reviewer directory.
"""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import platform
import stat
import subprocess
import sys
import unicodedata
import zipfile

BASE = Path('/workspace/scratch/f8d879d19e34')
OWN = BASE / 'phase-p23/reviews/archive'
REPO = BASE / 'OntoKin'
INPUT = BASE / 'input/OntoKin'
EXISTING = BASE / 'handoff-input'
ARCHIVE = INPUT / 'OntoKin_C271_P22_Ephemeral_Host_Amended_Handoff_2026-11-22.zip'
RECEIPT = INPUT / 'OntoKin_C271_P22_Ephemeral_Host_Amendment_Delivery_Receipt_2026-11-22.json'
MAIN = 'e43cc6c5777874101a40559e4058ad6826b07e51'
EXTRACT = OWN / 'scratch-extraction-v1'
checks, failures = [], []


def sha(data):
    return hashlib.sha256(data).hexdigest()


def check(name, passed, detail=None):
    row = {'check': name, 'passed': bool(passed)}
    if detail is not None:
        row['detail'] = detail
    checks.append(row)
    if not passed:
        failures.append(row)
    return bool(passed)


def save(name, obj):
    with (OWN / name).open('x') as stream:
        json.dump(obj, stream, indent=2)
        stream.write('\n')


def git(*args, data=None):
    cmd = ['git', '-C', str(REPO), *args]
    p = subprocess.run(cmd, input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode:
        raise RuntimeError(json.dumps({'command': cmd, 'returncode': p.returncode, 'stderr': p.stderr.decode(errors='replace')}))
    return p.stdout


def safe(name):
    p = PurePosixPath(name)
    return bool(name) and not p.is_absolute() and '\\' not in name and '\x00' not in name and ':' not in p.parts[0] and all(part not in ('', '.', '..') for part in name.split('/')) and str(p) == name


def descriptor(data):
    return {'bytes': len(data), 'sha256': sha(data)}


started = datetime.now(timezone.utc).isoformat()
receipt = json.loads(RECEIPT.read_bytes())
archive_bytes = ARCHIVE.read_bytes()
zip_receipt = next(row for row in receipt['new_files'] if row['filename'] == ARCHIVE.name)
check('archive_receipt_bytes', len(archive_bytes) == zip_receipt['bytes'])
check('archive_receipt_sha256', sha(archive_bytes) == zip_receipt['sha256'])
saved_files = []
for row in receipt['new_files']:
    local = INPUT / row['filename']
    data = local.read_bytes()
    passed = check('adjacent_saved_file:' + row['filename'], len(data) == row['bytes'] and sha(data) == row['sha256'])
    saved_files.append({'filename': row['filename'], **descriptor(data), 'receipt_match': passed})

with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
    infos = archive.infolist()
    names = [info.filename for info in infos]
    check('zip_crc', archive.testzip() is None)
    check('zip_member_count', len(names) == receipt['verify']['safe_unique_paths'], len(names))
    check('zip_unique_names', len(names) == len(set(names)))
    check('zip_safe_paths', all(safe(name) for name in names))
    check('zip_unicode_case_collision_free', len({unicodedata.normalize('NFC', name).casefold() for name in names}) == len(names))
    check('zip_no_directory_members', all(not info.is_dir() for info in infos))
    check('zip_no_symlink_or_special_members', all(stat.S_IFMT(info.external_attr >> 16) in (0, stat.S_IFREG) for info in infos))
    check('zip_no_encrypted_members', all(not info.flag_bits & 1 for info in infos))
    names_set = set(names)
    check('zip_no_file_ancestor_collisions', all(not any(str(parent) in names_set for parent in PurePosixPath(name).parents if str(parent) != '.') for name in names))
    data_by_name = {info.filename: archive.read(info) for info in infos}
    modes = {info.filename: stat.S_IMODE(info.external_attr >> 16) for info in infos}

manifest = json.loads(data_by_name['MANIFEST-SHA256.json'])
source = json.loads(data_by_name['SOURCE-MANIFEST.json'])
recovery = json.loads(data_by_name['RECOVERY-FILE-MAP.json'])
original = json.loads(data_by_name['ORIGINAL-HANDOFF-IDENTITY.json'])
checkpoint = json.loads(data_by_name['CHECKPOINT.json'])
amendment = json.loads(data_by_name['AMENDMENT-CHECKPOINT.json'])
canonical = json.loads(data_by_name['repository/docs/engineering/localized-repair-c271/retained-input-p22/CANONICAL-MAP.json'])
required = ['README-START-HERE.md', 'CHECKPOINT.json', 'HANDOFF.md', 'NEXT-TASK.md', 'RECOVERY-STATUS.md', 'PROMPT-1-CONTINUE.md', 'PROMPT-2-RECOVER.md', 'HISTORICAL-DEPENDENCIES.json', 'MANIFEST-SHA256.json', 'HOST-ENVIRONMENT.md']
check('required_root_files', all(name in names_set for name in required))
manifest_names = [row['path'] for row in manifest]
check('manifest_count', len(manifest) == receipt['verify']['payload_hashes_verified'], len(manifest))
check('manifest_unique_paths', len(manifest_names) == len(set(manifest_names)))
check('manifest_exact_inventory', set(manifest_names) == names_set - {'MANIFEST-SHA256.json'})
EXTRACT.mkdir(exist_ok=False)
member_rows = []
manifest_by_path = {row['path']: row for row in manifest}
for name, data in data_by_name.items():
    p = EXTRACT / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    readback = p.read_bytes()
    row = manifest_by_path.get(name)
    passed = True if row is None else len(data) == row['bytes'] and sha(data) == row['sha256']
    check('payload:' + name, passed)
    check('fresh_extraction:' + name, data == readback)
    check('supplied_extraction:' + name, (EXISTING / name).is_file() and (EXISTING / name).read_bytes() == data)
    member_rows.append({'path': name, **descriptor(data), 'zip_mode': oct(modes[name]), 'manifest_match': passed, 'fresh_extraction_match': data == readback})
existing_names = {str(p.relative_to(EXISTING)) for p in EXISTING.rglob('*') if p.is_file()}
check('supplied_extraction_exact_inventory', existing_names == names_set)

source_paths = [row['package_path'] for row in source]
check('source_manifest_count', len(source) == receipt['verify']['source_git_blob_bindings_preserved'], len(source))
check('source_manifest_unique_package_paths', len(set(source_paths)) == len(source_paths))
check('source_manifest_exact_coverage', set(source_paths) == {name for name in names if name.startswith(('repository/', 'observed-main/'))})
groups = defaultdict(list)
for row in source:
    groups[row['git_revision']].append(row)
tree_entries = {}
for revision, rows in groups.items():
    check('source_revision_is_commit:' + revision, git('cat-file', '-t', revision).strip() == b'commit')
    output = git('ls-tree', '-r', '-z', revision, '--', *sorted({row['git_path'] for row in rows}))
    for entry in output.split(b'\0'):
        if not entry:
            continue
        left, path = entry.split(b'\t', 1)
        mode, kind, blob = left.decode().split()
        tree_entries[(revision, path.decode())] = {'mode': mode, 'type': kind, 'blob': blob}
batch_input = ''.join(row['git_revision'] + ':' + row['git_path'] + '\n' for row in source).encode()
batch = io.BytesIO(git('cat-file', '--batch', data=batch_input))
source_rows = []
for row in source:
    name = row['package_path']
    data = data_by_name[name]
    header = batch.readline().decode().strip().split()
    if len(header) != 3 or header[1] != 'blob':
        raise RuntimeError('Missing source blob: ' + repr(header))
    blob, kind, length = header
    live_bytes = batch.read(int(length))
    if batch.read(1) != b'\n':
        raise RuntimeError('Unexpected cat-file framing')
    entry = tree_entries.get((row['git_revision'], row['git_path']))
    computed_blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    passed = check('source_binding:' + name, len(data) == row['bytes'] and sha(data) == row['sha256'] and blob == row['git_blob'] == computed_blob and live_bytes == data and entry == {'mode': row['git_mode'], 'type': 'blob', 'blob': row['git_blob']})
    source_rows.append({**row, 'git_commit_path_mode_and_bytes_match': passed})
check('source_batch_consumed', batch.read() == b'')

recovery_names = [row['path'] for row in recovery]
check('recovery_count', len(recovery) == receipt['verify']['recovery_files_unchanged'], len(recovery))
check('recovery_unique_paths', len(recovery_names) == len(set(recovery_names)))
check('recovery_unique_session_paths', len({row['session_path'] for row in recovery}) == len(recovery))
check('recovery_exact_coverage', set(recovery_names) == {name for name in names if name.startswith('recovery/')})
recovery_by_session = {row['session_path']: row for row in recovery}
recovery_rows = []
for row in recovery:
    data = data_by_name[row['path']]
    passed = check('recovery_mapping:' + row['path'], row['path'] == 'recovery/session/' + row['session_path'] and safe(row['session_path']) and len(data) == row['bytes'] and sha(data) == row['sha256'] and modes[row['path']] == int(row['archive_mode'], 8))
    recovery_rows.append({**row, 'payload_and_path_and_archive_mode_match': passed})
canonical_rows = []
for row in canonical:
    package_path = 'repository/' + row['canonical_path']
    recovery_path = 'recovery/session/' + row['session_path']
    package_data, recovery_data = data_by_name[package_path], data_by_name[recovery_path]
    passed = check('canonical_recovery_equivalence:' + row['session_path'], package_data == recovery_data and len(package_data) == row['bytes'] and sha(package_data) == row['sha256'] and row['original_mode'] == recovery_by_session[row['session_path']]['original_mode'])
    canonical_rows.append({**row, 'canonical_and_recovery_match': passed})

for filename, key in [('SOURCE-MANIFEST.json', 'original_source_manifest_sha256'), ('RECOVERY-FILE-MAP.json', 'original_recovery_file_map_sha256'), ('CHECKPOINT.json', 'original_checkpoint_sha256')]:
    check('frozen_original_identity:' + filename, sha(data_by_name[filename]) == original[key])
check('original_zip_identity_crossreferences', original['original_sha256'] == amendment['historical_handoff_sha256'] == receipt['original_p22_zip_sha256'])
check('policy_revision_consistency', MAIN == amendment['policy_main_commit'] == original['policy_main_sha'] == receipt['repository_main_policy_commit'])
check('frozen_pending_delivery_retained', checkpoint['delivery_state_at_freeze'] == 'save_pending' and next(row for row in checkpoint['phase_table'] if row['gate'] == 'A05')['state'] == 'pending')
check('no_h0_or_parent_acceptance', checkpoint['h0_accepted'] is False and amendment['h0_accepted'] is False and amendment['c271_parent_complete'] is False and checkpoint['parent_complete'] is False)
check('amendment_denies_prior_host_availability', amendment['p22_installations_exist_on_new_host'] is False and amendment['prior_host_absolute_paths'] == 'historical_only_nonportable')
frozen = checkpoint['frozen_preparation_source']
inventory_data = data_by_name['recovery/session/preparation/SOURCE-INVENTORY.json']
inventory = json.loads(inventory_data)
check('frozen_inventory_descriptor', len(inventory_data) == frozen['inventory']['size_bytes'] and sha(inventory_data) == frozen['inventory']['sha256'])
check('frozen_inventory_file_count', len(inventory['files']) == 626, len(inventory['files']))
revision_trees = [(checkpoint['source_revision'], checkpoint['source_tree']), (checkpoint['observed_main']['sha'], checkpoint['observed_main']['tree']), (frozen['commit'], frozen['tree'])]
for revision, expected_tree in revision_trees:
    check('commit_tree:' + revision, git('rev-parse', revision + '^{tree}').decode().strip() == expected_tree)
for saved_name, package_name in [('OntoKin_C271_P22_Ephemeral_Host_Continue_2026-11-22.md', 'PROMPT-1-CONTINUE.md'), ('OntoKin_C271_P22_Ephemeral_Host_Recover_2026-11-22.md', 'PROMPT-2-RECOVER.md')]:
    check('saved_prompt_equivalence:' + package_name, (INPUT / saved_name).read_bytes() == data_by_name[package_name])

metadata_path = BASE / 'state/input-library-metadata.json'
metadata_bytes = metadata_path.read_bytes()
metadata = json.loads(metadata_bytes)
xattrs = {key: os.getxattr(ARCHIVE, key).decode() for key in os.listxattr(ARCHIVE)}
check('library_stable_identity', metadata['library_file_id'] == zip_receipt['library_file_id'] == xattrs['user.library-file-id'])
check('library_backing_identity', metadata['file_id'] == zip_receipt['backing_file_id'])
check('library_version_identity', str(metadata['version_id']) == str(zip_receipt['version']) == xattrs['user.library-file-version'])
check('library_list_size', metadata['size_bytes'] == len(archive_bytes))

terminal_receipt_path = INPUT / 'OntoKin_C271_P22_Delivery_Receipt_2026-11-22.json'
terminal_bytes = terminal_receipt_path.read_bytes()
check('original_terminal_receipt_identity', sha(terminal_bytes) == amendment['historical_delivery_receipt_sha256'] == receipt['original_p22_receipt_sha256'])
terminal_marker_path = BASE / 'state/p22-terminal.json'
terminal_marker_bytes = terminal_marker_path.read_bytes()
terminal_marker = json.loads(terminal_marker_bytes)

readset = []
for path in ['AGENTS.md', 'ROLE.md', 'docs/workflow/PROTOCOL.md', 'docs/workflow/HANDOFF.md', 'docs/workflow/EPHEMERAL-HOST.md', 'docs/workflow/templates/WORKER.md', 'docs/engineering/OK-ENG-006-local-validation-and-hosted-ci-policy.md']:
    data = git('show', MAIN + ':' + path)
    local = BASE / 'current-main' / path
    if local.exists():
        check('governing_snapshot_binding:' + path, local.read_bytes() == data)
    readset.append({'path': path, 'git_revision': MAIN, **descriptor(data), 'read_in_full': True, 'access': 'current-main exact snapshot or Git object read'})

save('PREDECESSOR-MEMBER-CHECKS.json', member_rows)
save('PREDECESSOR-SOURCE-BINDINGS.json', source_rows)
save('PREDECESSOR-RECOVERY-CHECKS.json', {'recovery': recovery_rows, 'canonical_equivalences': canonical_rows})
save('PREDECESSOR-READSET.json', readset)
save('PREDECESSOR-CHECKS.json', checks)
summary = {
    'schema': 'ontokin.c271.p23.predecessor-archive-review/1',
    'reviewer': '/root/archive_audit',
    'verdict': 'PASS' if not failures else 'FAIL',
    'started_at_utc': started,
    'completed_at_utc': datetime.now(timezone.utc).isoformat(),
    'scope': 'Startup read-only verification of amended P22 online handoff; no archived code or product tests executed.',
    'archive': {'path': str(ARCHIVE), **descriptor(archive_bytes)},
    'adjacent_receipt': {'path': str(RECEIPT), **descriptor(RECEIPT.read_bytes())},
    'counts': {'zip_members': len(names), 'payloads': len(manifest), 'source_bindings': len(source), 'recovery_mappings': len(recovery), 'canonical_recovery_equivalences': len(canonical), 'frozen_inventory_files': len(inventory['files']), 'checks': len(checks), 'failed_checks': len(failures)},
    'saved_files_verified': saved_files,
    'library_metadata': {'source_path': str(metadata_path), **descriptor(metadata_bytes), 'version': metadata['version_id'], 'receipt_version': zip_receipt['version'], 'xattr_version': xattrs['user.library-file-version'], 'file_id': metadata['file_id'], 'library_file_id': metadata['library_file_id'], 'discrepancies': []},
    'original_terminal_receipt': {'path': str(terminal_receipt_path), **descriptor(terminal_bytes)},
    'live_terminal_marker_as_supplied_by_director': {'path': str(terminal_marker_path), **descriptor(terminal_marker_bytes), 'content': terminal_marker},
    'checkpoint_interpretation': 'P22 CHECKPOINT remains the exact original pre-save freeze. The later original terminal receipt resolves only P22 delivery; the amendment changes continuation instructions and does not accept H0 or complete C271.',
    'host_rule_interpretation': 'P22 INSTALLED_EXACT reports describe its former host. Reconstruct only needed current-host inputs from pinned source and verified artifacts. Never search for or run old-host paths.',
    'external_limits': ['The original unamended ZIP was not separately materialized or compared byte for byte; its unchanged checkpoint/source/recovery manifest digests were verified against ORIGINAL-HANDOFF-IDENTITY, and all 193 source bindings and 208 recovery descriptors were checked.', 'Saved Library metadata and terminal-marker observations were supplied by Director; this worker independently inspected the materialized bytes and their descriptors, but did not make remote writes or API observations.', 'This review does not accept H0, H1, original-seven/full routine, C271 integration, or product release.'],
    'writes_and_processes': {'git_mutations': False, 'external_writes': False, 'archive_code_executed': False, 'active_jobs_after_completion': [], 'owned_outputs_only': str(OWN)},
    'scratch_extraction': {'path': str(EXTRACT), 'purpose': 'Independent fresh extraction for byte checks; redundant transient copies, exclude from delivery payload.'},
    'failures': failures,
}
save('PREDECESSOR-AUDIT.json', summary)
if failures:
    save('PREDECESSOR-FAILED-CHECKS.json', failures)
print(json.dumps({'verdict': summary['verdict'], 'counts': summary['counts'], 'archive': summary['archive'], 'library_version': metadata['version_id'], 'report': str(OWN / 'PREDECESSOR-AUDIT.json')}, indent=2))
sys.exit(0 if not failures else 1)
