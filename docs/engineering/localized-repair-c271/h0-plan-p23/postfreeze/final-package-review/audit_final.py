"""Independent data-only audit of the frozen P23 final handoff."""
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import platform
import stat
import subprocess
import sys
import tempfile
import unicodedata
import zipfile

BASE = Path('/workspace/scratch/f8d879d19e34')
OWN = BASE / 'phase-p23/reviews/archive/final-package'
PHASE = BASE / 'phase-p23'
REPO = BASE / 'OntoKin'
ARCHIVE = BASE / 'packages/OntoKin_C271_P23_H0_Path_Blocker_Handoff_2026-11-22.zip'
CORE = '182d36d957d93161e351f41839bf2a6157fed3df'
TREE = 'cc31ed24df11b7fb5a15720cd735ca4f68f2f7a4'
MAIN = 'e43cc6c5777874101a40559e4058ad6826b07e51'
FROZEN = '527368bd5195c439762b43e2cc836ff9822213f8'
checks = []


def digest(data):
    return hashlib.sha256(data).hexdigest()


def identity(data):
    return {'bytes': len(data), 'sha256': digest(data)}


def check(name, passed, detail=None):
    row = {'check': name, 'passed': bool(passed)}
    if detail is not None:
        row['detail'] = detail
    checks.append(row)
    return bool(passed)


def git(*args, data=None):
    return subprocess.check_output(['git', '-C', str(REPO), *args], input=data)


def safe(name):
    path = PurePosixPath(name)
    return bool(name) and name == str(path) and not path.is_absolute() and '\\' not in name and '\x00' not in name and ':' not in path.parts[0] and all(p not in ('', '.', '..') for p in name.split('/'))


def save(name, obj):
    with (OWN / name).open('x') as stream:
        json.dump(obj, stream, indent=2)
        stream.write('\n')


raw = ARCHIVE.read_bytes()
check('expected_archive_identity', len(raw) == 3107286 and digest(raw) == '241e31741879b81eaa85c9705941f282347ab3cebf9db60bc08dd7cd52aa8761')
with zipfile.ZipFile(io.BytesIO(raw)) as z:
    infos = z.infolist()
    names = z.namelist()
    check('zip_crc', z.testzip() is None)
    check('zip_safe_unique_names', len(names) == len(set(names)) and all(safe(n) for n in names))
    check('zip_case_unicode_collision_free', len({unicodedata.normalize('NFC', n).casefold() for n in names}) == len(names))
    check('zip_regular_unencrypted_files', all(not i.is_dir() and stat.S_IFMT(i.external_attr >> 16) in (0, stat.S_IFREG) and not i.flag_bits & 1 for i in infos))
    check('no_file_ancestor_collision', all(not any(str(p) in names for p in PurePosixPath(n).parents if str(p) != '.') for n in names))
    data = {n: z.read(n) for n in names}

manifest = json.loads(data['MANIFEST-SHA256.json'])['files']
sources = json.loads(data['SOURCE-MANIFEST.json'])['files']
recovery = json.loads(data['RECOVERY-MANIFEST.json'])['files']
check('expected_counts', (len(names), len(manifest), len(sources), len(recovery)) == (208, 207, 181, 141))
check('manifest_exact_unique_inventory', len({r['path'] for r in manifest}) == len(manifest) and {r['path'] for r in manifest} == set(names) - {'MANIFEST-SHA256.json'})
payload_rows = []
for row in manifest:
    d = data[row['path']]
    passed = check('payload:' + row['path'], len(d) == row['bytes'] and digest(d) == row['sha256'])
    payload_rows.append({**row, 'passed': passed})
with tempfile.TemporaryDirectory(prefix='fresh-extraction-', dir=OWN) as location:
    root = Path(location)
    for name, d in data.items():
        p = root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(d)
        check('fresh_extraction:' + name, p.read_bytes() == d)

check('source_exact_unique_coverage', len({r['member'] for r in sources}) == len(sources) and {r['member'] for r in sources} == {n for n in names if n.startswith('repository/')})
groups = defaultdict(list)
for row in sources:
    groups[row['commit']].append(row)
check('source_revision_set', set(groups) == {MAIN, FROZEN, CORE})
entries = {}
for revision, rows in groups.items():
    check('source_commit:' + revision, git('cat-file', '-t', revision).strip() == b'commit')
    for record in git('ls-tree', '-r', '-z', revision, '--', *sorted({r['path'] for r in rows})).split(b'\0'):
        if record:
            left, path = record.split(b'\t', 1)
            mode, kind, blob = left.decode().split()
            entries[(revision, path.decode())] = {'mode': mode, 'kind': kind, 'blob': blob}
batch = io.BytesIO(git('cat-file', '--batch', data=''.join(r['commit'] + ':' + r['path'] + '\n' for r in sources).encode()))
source_rows = []
for row in sources:
    blob, kind, length = batch.readline().decode().strip().split()
    actual = batch.read(int(length))
    assert batch.read(1) == b'\n'
    d = data[row['member']]
    tree_entry = entries[(row['commit'], row['path'])]
    passed = check('source_binding:' + row['member'], kind == 'blob' and actual == d and blob == row['git_blob'] == tree_entry['blob'] and len(d) == row['bytes'] and digest(d) == row['sha256'])
    source_rows.append({**row, 'actual_git_mode': tree_entry['mode'], 'passed': passed})
check('source_batch_consumed', batch.read() == b'')
check('core_commit_tree', git('rev-parse', CORE + '^{tree}').decode().strip() == TREE)

allowed_tools = {BASE / n for n in ['build_final_p23.py', 'reconcile_p23_outcome.py', 'build_early.py', 'prepare_git_publication.py']}
check('recovery_unique_originals', len({r['original_path'] for r in recovery}) == len(recovery))
recovery_rows = []
for row in recovery:
    path = Path(row['original_path'])
    permitted = path.is_relative_to(PHASE) or path in allowed_tools
    check('recovery_path_scope:' + row['original_path'], permitted)
    assert permitted
    d = data[row['member']]
    passed = check('recovery_binding:' + row['original_path'], len(d) == row['bytes'] and digest(d) == row['sha256'] and not path.is_symlink() and path.read_bytes() == d and oct(stat.S_IMODE(path.stat().st_mode)) == row['mode'])
    recovery_rows.append({**row, 'passed': passed})
current_included, excluded = set(), []
for path in PHASE.rglob('*'):
    if not path.is_file():
        continue
    parts = path.relative_to(PHASE).parts
    if any('extraction' in p or p == '__pycache__' for p in parts) or path.name.startswith('FINAL-') or 'final-package' in path.parts:
        excluded.append(str(path.relative_to(PHASE)))
    else:
        current_included.add(str(path))
check('recovery_exact_current_prefreeze_coverage', {r['original_path'] for r in recovery} == current_included | {str(p) for p in allowed_tools})
check('physical_recovery_members_all_mapped', {n for n in names if n.startswith('recovery/')} <= {r['member'] for r in recovery})
by_original = {r['original_path']: r for r in recovery}


def recovered(relative):
    return data[by_original[str(PHASE / relative)]['member']]


predecessor_review = json.loads((PHASE / 'reviews/archive/PREDECESSOR-AUDIT.json').read_bytes())
history_names = {n for n in names if n.startswith('history/')}
expected_history = {
    'history/OntoKin_C271_P22_Ephemeral_Host_Amended_Handoff_2026-11-22.zip': predecessor_review['archive'],
    'history/OntoKin_C271_P22_Ephemeral_Host_Amendment_Delivery_Receipt_2026-11-22.json': predecessor_review['adjacent_receipt'],
    'history/OntoKin_C271_P22_Delivery_Receipt_2026-11-22.json': predecessor_review['original_terminal_receipt'],
}
check('exact_history_member_set', history_names == set(expected_history))
for member, expected in expected_history.items():
    d = data[member]
    check('immutable_predecessor:' + member, len(d) == expected['bytes'] and digest(d) == expected['sha256'] and Path(expected['path']).read_bytes() == d)

required = {'README-START-HERE.md', 'CHECKPOINT.json', 'HANDOFF.md', 'NEXT-TASK.md', 'RECOVERY-STATUS.md', 'PROMPT-1-CONTINUE.md', 'PROMPT-2-RECOVER.md', 'HISTORICAL-DEPENDENCIES.json', 'MANIFEST-SHA256.json', 'HOST-ENVIRONMENT.md'}
check('required_root_files', required <= set(names))
checkpoint = json.loads(data['CHECKPOINT.json'])
outcome = json.loads(data['PHASE-OUTCOME.json'])
deps = json.loads(data['HISTORICAL-DEPENDENCIES.json'])
branch_root = 'repository/branch/docs/engineering/localized-repair-c271/h0-plan-p23/'
canonical_phase = json.loads(data[branch_root + 'PHASE.json'])
check('checkpoint_source_identity', checkpoint['source_commit'] == CORE and checkpoint['source_tree'] == TREE and checkpoint['observed_main'] == MAIN)
check('root_outcome_matches_published_outcome', outcome == json.loads(data[branch_root + 'OUTCOME.json']))
check('technical_stop_without_acceptance', checkpoint['technical_phase_complete'] is True and checkpoint['technical_outcome'] == 'H0-RTLD-ABSENT-PARENT-001' and checkpoint['h0_accepted'] is False and checkpoint['h0_plan_accepted'] is False and checkpoint['parent_complete'] is False)
check('pending_save_is_explicit', checkpoint['phase_complete'] is False and checkpoint['delivery_state'] == 'immutable_source_snapshot_before_final_save' and 'finish delivery only' in checkpoint['recovery_next'])
check('checkpoint_phase_consistency', all(checkpoint[k] == canonical_phase[k] for k in ['phase', 'branch', 'requirements', 'parent_plan', 'pr', 'issue', 'historical_unknown_operations']))
check('recorded_execution_counts_consistent', checkpoint['execution_counts'] == outcome['execution_counts'] == canonical_phase['actual_execution_counts'] and checkpoint['execution_counts']['raw_observation_python_processes'] == 2 and all(v == 0 for k, v in checkpoint['execution_counts'].items() if k != 'raw_observation_python_processes'))
check('parent_branch_boundaries', checkpoint['requirements'] == {'R01': 'done', 'R02': 'done', 'R03': 'not_done', 'R04': 'not_done', 'R05': 'not_done'} and checkpoint['pr']['draft'] and not checkpoint['pr']['merged'] and checkpoint['issue']['state'] == 'open' and not checkpoint['main_lease_held'])
check('historical_unknowns_preserved_current_empty', checkpoint['current_unknown_operations'] == [] and len(checkpoint['historical_unknown_operations']) == 3)
independent = outcome['independent_review']
review_bytes = data['repository/branch/' + independent['repository_path']]
check('blocker_independent_review_exact_descriptor', len(review_bytes) == independent['bytes'] and digest(review_bytes) == independent['sha256'])
check('both_observations_have_packaged_evidence_and_reviews', len(outcome['actual_observations']) == 2 and all('repository/branch/' + r['evidence'] in data and 'repository/branch/' + r['review'] in data and r['returncode'] == 0 for r in outcome['actual_observations']))
check('two_path_representations_preserved', outcome['primary_blocker']['id'] == 'H0-RTLD-ABSENT-PARENT-001' and '/libx32' in outcome['primary_blocker']['observed'] and outcome['related_constraint_from_same_observation']['observed_symlink_target'] == '../lib/x86_64-linux-gnu/ld-linux-x86-64.so.2')
check('portable_inputs_exact_record', deps['portable_inputs_verified_in_P23'] == json.loads(recovered('state/RETAINED-INPUT-AVAILABILITY.json')))
check('inherited_dependency_record_unchanged', deps['inherited_unchanged'] == json.loads((BASE / 'handoff-input/HISTORICAL-DEPENDENCIES.json').read_bytes()))
expected_portable = {'OntoKin_C271_P05_Node_Candidate_2026-11-20.tar.gz': (45186132, '100ae976555b388472c3e875aeda67bd7d8c9229a968a11661fb852624adaeb5'), 'OntoKin_C271_P21_H0_Plan_Handoff_2026-11-22.zip': (9327161, 'ba03995347ed65a5a37b4283211841daf4da74fe4a04dbe0617f9e833e9bb64f')}
check('Node_P21_external_identities', {r['file_name']: (r['bytes'], r['sha256']) for r in deps['portable_inputs_verified_in_P23']['artifacts']} == expected_portable)
c262 = deps['inherited_unchanged']['inherited']['inherited_p20_dependencies']['inherited']['C262']
check('C262_external_identity', c262['bytes'] == 532260846 and c262['sha256'] == 'b8af544f730a4d1f741d47b56eb3fcf76147ed392a9ebb020f3d966f2f305c90')

published = json.loads(recovered('checks/published-core/RESULT.json'))
check('published_core_checks_passed', published['commit'] == CORE and set(published['results']) == {'workflow', 'documentation', 'whitespace'} and all(r['returncode'] == 0 for r in published['results'].values()))
for name, row in published['results'].items():
    for stream in ['stdout', 'stderr']:
        check('published_check_log:' + name + ':' + stream, digest(recovered('checks/published-core/' + name + '.' + stream + '.log')) == row[stream + '_sha256'])
docs = json.loads(recovered('checks/published-core/documentation.stdout.log'))
check('published_documentation_counts', docs['status'] == 'passed' and (docs['links']['documents'], docs['links']['local_links'], docs['links']['anchors'], docs['sources_verified']) == (1603, 6239, 113, 29))
check('published_workflow_count', 'Workflow structure passed (12 tasks).' in recovered('checks/published-core/workflow.stdout.log').decode())
publication = json.loads(recovered('state/CORE-PUBLICATION.json'))
check('publication_record_consistency', publication['commit'] == CORE and publication['tree'] == TREE and publication['all_changed_files_read_back'] and publication['remote_head_readback_equal'] and publication['changed_file_count'] == 142 and not publication['main_updated'])
early = json.loads(recovered('state/EARLY-RECOVERY-RECEIPT.json'))
check('early_recovery_receipt_consistency', early['bytes'] == 218583 and early['sha256'] == 'ea7d0abfc8b9fa726054305b3d24369e8f572092e08912c2c1df03202e28afd7' and early['saved_bytes_readback_equal'] and checkpoint['early_recovery_confirmed'])

prompt_rows = []
for filename, member in [('OntoKin_C271_P23_Continue_Prompt_2026-11-22.md', 'PROMPT-1-CONTINUE.md'), ('OntoKin_C271_P23_Recover_Prompt_2026-11-22.md', 'PROMPT-2-RECOVER.md')]:
    path = BASE / 'packages' / filename
    d = path.read_bytes()
    check('external_prompt_exact:' + filename, d == data[member])
    prompt_rows.append({'path': str(path), 'filename': filename, 'member': member, **identity(d)})
check('manual_root_semantics', True, 'Read all eight root prose/prompt files and checkpoint/outcome. Host portability, delivery-only recovery, source-time pending save, H0/parent nonacceptance, and one future bounded design/adoption decision are explicit. No second P23 technical phase is authorized.')
check('archive_unchanged_after_audit', ARCHIVE.read_bytes() == raw)

failures = [r for r in checks if not r['passed']]
save('PAYLOAD-CHECKS.json', payload_rows)
save('SOURCE-BINDINGS.json', source_rows)
save('RECOVERY-BINDINGS.json', recovery_rows)
save('CHECKS.json', checks)
summary = {
    'schema': 'ontokin.c271.p23.final-archive-review/1',
    'reviewer': '/root/archive_audit',
    'verdict': 'ACCEPTED_FOR_SAVE' if not failures else 'FAIL',
    'reviewed_at_utc': datetime.now(timezone.utc).isoformat(),
    'archive': {'path': str(ARCHIVE), 'filename': ARCHIVE.name, **identity(raw)},
    'prompts': prompt_rows,
    'counts': {'members': len(names), 'payloads': len(manifest), 'source_bindings': len(sources), 'source_revision_counts': {k: len(v) for k, v in groups.items()}, 'recovery_mappings': len(recovery), 'distinct_recovery_targets': len({r['member'] for r in recovery}), 'physical_recovery_members': sum(n.startswith('recovery/') for n in names), 'history_members': len(history_names), 'checks': len(checks), 'failed_checks': len(failures)},
    'source_commit': CORE, 'source_tree': TREE, 'observed_main': MAIN,
    'environment': {'python': sys.version, 'platform': platform.platform()},
    'command': 'python -I -B ' + str(Path(__file__)),
    'audit_script': {'path': str(Path(__file__)), **identity(Path(__file__).read_bytes())},
    'readback_readiness': 'This exact ZIP and both exact prompt files are accepted for save. The future save needs distinct stable/backing IDs, known versions, actual save outcome, and byte readback matching the identities above. Final availability/completion is not yet claimed.',
    'semantic_disposition': 'P23 technical work stopped at the two documented path-representation limits. The archive preserves source-time pending delivery, historical failures and unknowns; H0/H1/full-routine/integration/parent gates remain unaccepted. New work is limited to the separately selected future design/adoption phase after delivery.',
    'limits': ['Remote publication and early-save observations are exact packaged Director evidence, not fresh API observations by this reviewer.', 'No original technical observation, H0 program, product test, or historical code was executed.', 'Unchanged embedded predecessor identity reuses the exact earlier independent predecessor audit; no recursive predecessor rebuild or requalification was performed.', 'Fresh extraction occurred in an isolated temporary subdirectory and was removed after successful byte checks.'],
    'read_incident': 'READ-INCIDENT.json preserves a corrected reviewer assumption that workflow stdout was JSON; it is plain text and its recorded hash is verified.',
    'failures': failures,
    'execution_boundary': {'git_mutations': False, 'library_writes': False, 'immutable_package_edits': False, 'canonical_edits': False, 'historical_code_executed': False, 'active_jobs': []},
}
save('FINAL-ARCHIVE-REVIEW.json', summary)
if failures:
    save('FAILED-CHECKS.json', failures)
print(json.dumps({'verdict': summary['verdict'], 'archive': summary['archive'], 'counts': summary['counts'], 'prompts': prompt_rows, 'failed': failures, 'report': str(OWN / 'FINAL-ARCHIVE-REVIEW.json')}, indent=2))
sys.exit(1 if failures else 0)
