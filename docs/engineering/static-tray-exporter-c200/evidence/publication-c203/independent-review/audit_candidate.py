"""Independent read-only checks of the exact C200 publication candidate."""
from pathlib import Path
import collections
import datetime
import hashlib
import json
import stat
import subprocess
import tarfile

ROOT = Path('/workspace/scratch/a4d9132036d4/candidate')
OUT = Path('/workspace/scratch/a4d9132036d4/work-c203/integration-review')
BASE = '2cad7ecfece83295a3534d8afc97ab127a665ded'
CANDIDATE = '125353836119e50215287c27d80e99cef6d85e8f'
TREE = 'b0e62bdefcb9afd1ea0708ba2b5ab459f457fbcd'
EXECUTED = '62b2316cc3f88db187f69fbd7fdb2cf0997a97de'
PREFIX = 'docs/engineering/static-tray-exporter-c200/'
OLD_ROOT = '/workspace/scratch/ef5ae272e66e/ontokin/'
OUT.mkdir(parents=True, exist_ok=True)

def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args], text=True).strip()

def read_json(path):
    return json.loads(Path(path).read_bytes())

def file_hash(path):
    path = Path(path)
    if not path.is_file() or path.is_symlink():
        raise ValueError('Expected regular file: ' + str(path))
    data = path.read_bytes()
    return {'sha256': hashlib.sha256(data).hexdigest(), 'size_bytes': len(data)}

def check(condition, reason):
    if not condition:
        raise ValueError(reason)

check(git('rev-parse', 'HEAD') == CANDIDATE, 'Candidate HEAD moved')
check(git('rev-parse', CANDIDATE + '^{tree}') == TREE, 'Candidate tree differs')
check(not git('status', '--porcelain', '--untracked-files=all'), 'Candidate is not clean')
lock_path = ROOT / PREFIX / 'EXECUTABLE-INPUTS.json'
lock = read_json(lock_path)
lock_hash = file_hash(lock_path)['sha256']
check(lock_hash == 'e22d12703926740c2c4cb8596781192b9f0412836e3fba7c6f353bedfc60e0e0', 'Historical lock changed')
locked = []
for relative, binding in sorted(lock['repository_files'].items()):
    actual = file_hash(ROOT / relative)
    check(actual == {'sha256': binding['sha256'], 'size_bytes': binding['size_bytes']}, 'Locked input changed: ' + relative)
    locked.append({'path': relative, **actual})
check(len(locked) == 301, 'Unexpected locked input count')
tested_dir = ROOT / PREFIX / 'evidence/publication-c203/checks'
tested = read_json(tested_dir / 'TESTED-SOURCE-MANIFEST.json')
check(tested['count'] == 301 and tested['files'] == locked, 'Fresh-tested source differs from final candidate')

protected_paths = ['ontokin', 'tools', 'fixtures', 'schemas', 'grammar', '.github',
                   'pyproject.toml', 'setup.cfg', 'setup.py', 'requirements.txt', '.gitignore']
protected_diff = git('diff', '--name-status', BASE, CANDIDATE, '--', *protected_paths)
check(not protected_diff, 'Legacy runtime/workflow or fixture inputs changed')
changed_rows = git('diff', '--name-status', '--no-renames', BASE, CANDIDATE).splitlines()
allowed_modified = {'README.md', 'docs/README.md', 'STATUS.md',
                    'prototypes/static_tray_v01/worker.py',
                    'prototypes/static_tray_v01/export-settings.json',
                    'prototypes/static_tray_v01/qualification.py'}
for row in changed_rows:
    status, relative = row.split('\t', 1)
    check((status == 'M' and relative in allowed_modified)
          or (status == 'A' and (relative.startswith(PREFIX)
              or relative == 'tests/test_static_tray_exporter_c200.py')),
          'Out-of-scope cumulative change: ' + row)
executed_diff = git('diff', '--name-status', EXECUTED, CANDIDATE, '--',
                    'ontokin', 'prototypes', 'tools', 'fixtures', 'schemas', 'grammar', '.github', 'tests',
                    ':(glob)' + PREFIX + '*.py')
check(not executed_diff, 'Execution source changed beyond documentation/evidence')

overlay_path = Path('/workspace/scratch/a4d9132036d4/c202/inherited/c201/source/untracked-manifest.json')
overlay = read_json(overlay_path)
for row in overlay['files']:
    actual = file_hash(ROOT / row['path'])
    check(actual == {'sha256': row['sha256'], 'size_bytes': row['bytes']}, 'Overlay bytes changed: ' + row['path'])
    check(stat.S_IMODE((ROOT / row['path']).stat().st_mode) == row['mode'], 'Overlay mode changed')

evidence_dir = ROOT / PREFIX / 'evidence/native-execution'
archive_manifest = read_json(evidence_dir / 'MANIFEST.json')
archive_path = evidence_dir / 'captured-native-execution.tar.gz'
check(file_hash(archive_path) == {'sha256': archive_manifest['archive']['sha256'],
                                'size_bytes': archive_manifest['archive']['bytes']}, 'Archive binding differs')
archived = {}
archive_paths_by_source = {}
members_count = 0
regular_bytes = 0
with tarfile.open(archive_path) as archive:
    for member in archive:
        members_count += 1
        info = archive_manifest['entries'][member.name]
        check(member.mode == int(info['mode'], 8), 'Archived mode changed')
        if member.isfile():
            data = archive.extractfile(member).read()
            check(len(data) == info['size_bytes'] and hashlib.sha256(data).hexdigest() == info['sha256'],
                  'Archived bytes differ: ' + member.name)
            archived[member.name] = data
            archive_paths_by_source[info['source_path']] = member.name
            regular_bytes += len(data)
        else:
            check(member.isdir() and info['type'] == 'directory', 'Unexpected nonregular archive member')
check(members_count == len(archive_manifest['entries']) == 2565, 'Archive member count differs')
check(len(archived) == 1704 and regular_bytes == 60009373, 'Archive regular-file inventory differs')
for row in archive_manifest['direct_receipt_copies']:
    check((evidence_dir / row['path']).read_bytes() == archived[row['archive_path']], 'Direct receipt/archive differs')

review_path = ROOT / PREFIX / 'evidence/result-review/RESULT-REVIEW.json'
review = read_json(review_path)
bindings = []
def visit(value, context='root'):
    if isinstance(value, dict):
        if {'path', 'sha256', 'size_bytes'} <= set(value):
            path = value['path']
            if path.startswith(OLD_ROOT):
                data = (ROOT / path.removeprefix(OLD_ROOT)).read_bytes()
                location = path.removeprefix(OLD_ROOT)
            else:
                member = archive_paths_by_source[path]
                data = archived[member]
                location = 'captured-native-execution.tar.gz::' + member
            check(len(data) == value['size_bytes'] and hashlib.sha256(data).hexdigest() == value['sha256'],
                  'Final review binding changed: ' + context)
            bindings.append({'context': context, 'source_path': path, 'resolved_candidate_location': location,
                             'sha256': value['sha256'], 'size_bytes': value['size_bytes']})
        for key, child in value.items():
            visit(child, context + '.' + key)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            visit(child, context + '[' + str(index) + ']')
visit(review)
check(len(bindings) == 26, 'Unexpected final-review binding count')
check(review['qualified'] is True and review['decision'] == 'FINITE_STATIC_TRAY_QUALIFICATION_PASSED', 'Final disposition differs')
check(review['implementation'] == lock['implementation'], 'Historical reviewed implementation differs')
raw = json.loads(archived['c200-native/qualification-result.json'])
ledger = [json.loads(line) for line in archived['c200-native/attempts.jsonl'].splitlines() if line]
states = dict(collections.Counter(row['state'] for row in ledger))
check(states == {name: 12 for name in ['RESERVED', 'STARTED', 'BUILT_PENDING_RECEIVING', 'RECEIVING', 'ACCEPTED']}, 'Actual ledger differs')
check(raw['qualified'] is False and raw['measured_gates_passed'] is True, 'Raw chronology changed')
check(raw['native_starts'] == raw['receiving_starts'] == raw['read_only_checker_starts'] == 12, 'Raw start count differs')
check(len(raw['transactions']) == len(raw['external_readbacks']) == 12 and len(raw['delivered_controls']) == 9, 'Qualification count differs')
for slot in lock['slots']:
    result = json.loads(archived['c200-native/results/' + slot['slot'] + '.json'])
    check(result['state'] == 'ACCEPTED' and result['native_starts'] == result['receiving_starts'] == 1, 'Actual transaction not accepted once')
    check(result['input_lock_sha256'] == lock_hash and result['implementation'] == lock['implementation'], 'Transaction identity changed')
check(all(row['passed'] for row in raw['external_readbacks'] + raw['delivered_controls']), 'Recorded required gate failed')

checks = read_json(tested_dir / 'CHECKS-SUMMARY.json')
cohort_observations = {}
for name, expected in [('focused', 107), ('compiler', 47)]:
    result = read_json(tested_dir / name / 'RESULTS.json')
    check(result['status'] == 'PASS' and result['tests_run'] == expected and not result['errors']
          and not result['failures'] and not result['skipped'], 'Fresh cohort failed')
    check(len(set(result['passed_ids'])) == len(result['unique_planned_ids']) == expected, 'Fresh method inventory differs')
    log = file_hash(tested_dir / name / 'tests.log')
    check(log == {k: result['log'][k] for k in ['sha256', 'size_bytes']}, 'Fresh test log binding differs')
    cohort_observations[name] = {'passed': expected, 'skipped': 0, 'source_commit': result['implementation_commit']}
protocol_command = read_json(tested_dir / 'protocol-command.json')
protocol_log = (tested_dir / 'protocol.stderr.log').read_text()
check(protocol_command['exit_code'] == 0 and 'Ran 10 tests' in protocol_log and protocol_log.rstrip().endswith('OK'), 'Fresh protocol check failed')
core = read_json(tested_dir / 'core-conformance.json')
check(core['summary']['passed'] == 43 and core['summary']['failed'] == 0 and core['summary']['assertions'] == 694, 'Fresh core cohort differs')
documentation = read_json(ROOT / PREFIX / 'evidence/publication-c203/DOCUMENTATION-CHECK.json')
check(documentation['status'] == 'passed' and not documentation['failures'], 'Documentation gate failed')

fresh_log_recovery = read_json(ROOT / PREFIX / 'evidence/publication-c203/FRESH-LOG-RECOVERY.json')
for row in fresh_log_recovery['files']:
    check(file_hash(ROOT / row['destination_path']) == {'sha256': row['recovered_sha256'], 'size_bytes': row['recovered_size_bytes']},
          'Recovered log differs from new recovery binding')
check(fresh_log_recovery['recovered_count'] == 9 and fresh_log_recovery['recovered_total_bytes'] == 2707,
      'Fresh log inventory differs')
check(git('rev-parse', 'HEAD') == CANDIDATE and not git('status', '--porcelain', '--untracked-files=all'), 'Candidate changed during review')

record = {
    'schema': 'ontokin.c203.independent-integration-content-audit/0.1',
    'reviewed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'candidate_commit': CANDIDATE, 'candidate_tree': TREE, 'observed_main_base': BASE,
    'candidate_parent': git('rev-parse', CANDIDATE + '^'), 'candidate_clean_before_and_after': True,
    'passed': True, 'scope': 'Exact committed source/evidence identities, code containment, recorded outcomes and fresh check receipts; no new product execution',
    'cumulative_changed_paths': changed_rows, 'locked_inputs_verified': locked,
    'historical_lock_sha256': lock_hash, 'fresh_tested_manifest_equal': True,
    'legacy_runtime_workflow_fixture_diff': [], 'code_diff_from_executed_c200': [],
    'original_overlay_files_verified': len(overlay['files']), 'original_overlay_bytes': overlay['bytes'],
    'archive': {'members': members_count, 'regular_files': len(archived), 'regular_bytes': regular_bytes,
                'direct_receipt_copies_equal': len(archive_manifest['direct_receipt_copies']), **file_hash(archive_path)},
    'final_review_bindings_verified': bindings, 'ledger_states': states,
    'raw_qualified_false_preserved': True, 'later_review_qualified_true_preserved': True,
    'historical_counts': review['counts'],
    'fresh_cohorts': {**cohort_observations, 'protocol': {'passed': 10}, 'core': core['summary']},
    'fresh_process_observations': checks['observed_test_child_processes'],
    'documentation': {'status': documentation['status'], 'sources': documentation['sources_verified'],
                      'sections': documentation['sections_verified'], 'local_links': documentation['links']['local_links'], 'failures': []},
    'fresh_log_recovery': {'count': 9, 'bytes': 2707, 'historical_individual_hashes': 1,
                           'new_individual_stream_hashes': 8, 'prior_package_missingness_unchanged': True},
    'reviewer_role_disclosure': 'Reviewer did not author candidate implementation or historical qualification. Reviewer authored the new log-recovery manifest and preliminary admission design; their identity checks are self-checks, not independent approval of that authorship.',
    'new_product_runs': 0, 'new_native_runs': 0, 'new_receiving_runs': 0, 'new_node_runs': 0,
    'full_legacy_suite_rerun_by_reviewer': False,
    'full_legacy_suite_remains': {'status': 'FAILED', 'distinct_passing_methods': 4239, 'torque_read_methods_not_run': 13, 'unchanged_timeout_ms': 30000}
}
(OUT / 'CONTENT-AUDIT.json').write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')
print(json.dumps({'passed': True, 'candidate_commit': CANDIDATE, 'candidate_tree': TREE,
                  'locked_inputs': len(locked), 'overlay_files': len(overlay['files']),
                  'review_bindings': len(bindings), 'archive_members': members_count,
                  'changed_paths': len(changed_rows), 'record': str(OUT / 'CONTENT-AUDIT.json')}))
