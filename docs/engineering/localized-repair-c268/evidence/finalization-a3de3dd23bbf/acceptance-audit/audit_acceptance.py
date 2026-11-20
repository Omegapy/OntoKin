#!/usr/bin/env python3
"""Read-only identity and receipt audit; does not execute the candidate cohort."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone
import zipfile

REPO = Path('/workspace/scratch/014048e883e4/OntoKin')
OUT = Path('/workspace/scratch/a3de3dd23bbf/evidence/acceptance-audit')
CANDIDATE = 'e6f55b73fa71953aa648bcd34711a6796a7346b6'
ACCEPTED = 'ffb912cce59ccfe7d0d82ab4349de9b12271cc03'
ROOT = Path('docs/engineering/localized-repair-c268/evidence/finalization-20261119')
COHORT = REPO / ROOT / 'candidate-published'
REVIEW = REPO / ROOT / 'review'
assertions = []

def git(*args):
    return subprocess.check_output(['git', *args], cwd=REPO)

def identity(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

def check(label, ok, detail=None):
    assertions.append({'check': label, 'passed': bool(ok), 'detail': detail})

def get_json(path):
    return json.loads(path.read_text())

def expect_identity(label, raw, expected):
    actual = identity(raw)
    check(label, all(actual[k] == expected[k] for k in ('bytes', 'sha256')), {'expected': expected, 'actual': actual})
    return actual

receipt = get_json(COHORT / 'CHECKS.json')
review = get_json(REVIEW / 'REVIEW.json')
manifest = get_json(REVIEW / 'ARTIFACTS.json')
read_set = get_json(REVIEW / 'READ-SET.json')
audit = get_json(REVIEW / 'COHORT-AUDIT.json')
check('working_head', git('rev-parse', 'HEAD').decode().strip() == ACCEPTED)
check('working_tree_clean', not git('status', '--porcelain').strip())
check('candidate_tree', git('rev-parse', CANDIDATE + '^{tree}').decode().strip() == review['tree'])
check('candidate_ancestor_of_accepted', subprocess.run(['git', 'merge-base', '--is-ancestor', CANDIDATE, ACCEPTED], cwd=REPO).returncode == 0)
check('review_candidate', review['published_candidate'] == CANDIDATE)
check('review_eligible', review['verdict'] == 'eligible' and not review['required_findings'])
check('review_requirements_R01_R05', {x['id']: x['disposition'] for x in review['requirements'] if x['id'] <= 'R05'} == {f'R0{x}': 'eligible' for x in range(1, 6)})
expect_identity('review_markdown_receipt', (REVIEW / 'REVIEW.md').read_bytes(), review['review_md'])
expect_identity('cohort_receipt', (COHORT / 'CHECKS.json').read_bytes(), review['fresh_cohort']['receipt'])
check('source_before_after_equal', receipt['source_before'] == receipt['source_after'])
check('receipt_exact_candidate', receipt['source_before']['commit'] == CANDIDATE and receipt['source_before']['tree'] == review['tree'])
check('receipt_source_clean', receipt['source_before']['tracked_dirty_status'] == receipt['source_before']['all_dirty_status'] == '')
check('input_inventory_stable', receipt['input_files_before'] == receipt['input_files_after'] and receipt['input_identity_unchanged'])
check('complete_cohort', receipt['complete'] and receipt['passed'] and receipt['completed_check_count'] == receipt['planned_check_count'] == 12 and receipt['total_methods'] == receipt['expected_total_methods'] == 282 and not receipt['remaining_checks'])

accepted_input_deltas = []
for row in receipt['input_files_before']:
    path = row['path']
    raw_candidate = git('show', CANDIDATE + ':' + path)
    expect_identity('candidate_input:' + path, raw_candidate, row)
    raw_accepted = git('show', ACCEPTED + ':' + path)
    if raw_accepted != raw_candidate:
        accepted_input_deltas.append({'path': path, 'candidate': identity(raw_candidate), 'accepted': identity(raw_accepted)})
    if path.endswith('.py') or path.endswith('.ok') or path.endswith('.glb'):
        check('executable_fixture_continuity:' + path, raw_candidate == raw_accepted)
check('input_delta_only_current_records', {r['path'] for r in accepted_input_deltas} == {'STATUS.md', 'docs/workflow/CURRENT.json', 'docs/workflow/tasks/C268/task.json', 'docs/engineering/localized-repair-c268/RESULTS.md'})

for source, records in [('review_code', review['code_test_fixture_dependency_identities']), ('review_controls', review['independent_control_inputs'])]:
    for path, expected in records.items():
        expect_identity(source + ':candidate:' + path, git('show', CANDIDATE + ':' + path), expected)
        expect_identity(source + ':accepted:' + path, git('show', ACCEPTED + ':' + path), expected)

for scope in (260, 268):
    pins = get_json(REPO / f'docs/engineering/localized-repair-c{scope}/INPUTS.json')
    for row in pins['files']:
        expect_identity(f'C{scope}_pin:' + row['path'], (REPO / row['path']).read_bytes(), row)

for row in receipt['output_files']:
    expect_identity('cohort_output:' + row['path'], (COHORT / row['path']).read_bytes(), row)
check('cohort_output_inventory', {p.relative_to(COHORT).as_posix() for p in COHORT.rglob('*') if p.is_file()} == {r['path'] for r in receipt['output_files']} | {'CHECKS.json'})
for row in manifest['files']:
    expect_identity('review_artifact:' + row['path'], (REVIEW / row['path']).read_bytes(), row)

groups = []
for group in receipt['checks']:
    check('group_pass:' + group['name'], group['result'] == 'passed' and group['exit_code'] == 0 and group['failure'] is None and all(group['assertions'].values()))
    text = (COHORT / group['log']['path']).read_text()
    if group['expected_methods'] is not None:
        found = re.findall(r'(?m)^Ran (\d+) tests? in ', text)
        check('group_log_count:' + group['name'], bool(found) and int(found[-1]) == group['expected_methods'] == group['methods'] and bool(re.search(r'(?m)^OK\r?$', text)))
    groups.append({'name': group['name'], 'methods': group['methods'], 'result': group['result'], 'command': group['command']})
check('group_sum', sum(g['methods'] or 0 for g in groups) == 282)
corpus = json.loads((COHORT / 'c253-corpus.log').read_text())
check('corpus_bindings', corpus['passed'] and corpus['boundFiles'] == 14 and corpus['tasks'] == 3)
controls = get_json(COHORT / 'c268-controls/results.json')
check('endpoint_accounting', controls['testMethods'] == 35 and controls['apiCalls'] == 131 and controls['historicalCalls'] == 121 and controls['rawCalls'] == 10 and controls['admittedCalls'] == 12 and controls['rawSuccessfulCalls'] == 9 and controls['typedRefusals'] == 110 and controls['untypedExceptions'] == 0 and controls['passed'] and not controls['failures'] and not controls['errors'] and not controls['skipped'])
check('review_audit_passed', audit['passed'] and all(v if isinstance(v, bool) else v.get('passed', False) for v in audit['assertions'].values()))
zip_inventory = []
for path in sorted(COHORT.rglob('*.zip')):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        safe = len(names) == len(set(names)) and all(not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts and '\\' not in n for n in names)
        check('preserved_fixture_archive:' + path.relative_to(COHORT).as_posix(), safe and archive.testzip() is None)
        zip_inventory.append({'path': path.relative_to(COHORT).as_posix(), 'entries': len(names), **identity(path.read_bytes())})

python_binary = Path(receipt['environment']['resolved_executable']['path'])
expect_identity('available_pinned_interpreter', python_binary.read_bytes(), receipt['environment']['resolved_executable'])
runner_path = 'docs/engineering/localized-repair-c268/evidence/run_checks.py'
expect_identity('available_runner', (REPO / runner_path).read_bytes(), receipt['runner'])
current_environment = {'python': sys.version, 'platform': platform.platform(), 'runtime_bundle_version': os.environ.get('CODEX_PRIMARY_RUNTIME_BUNDLE_VERSION'), 'python_executable': str(Path(sys.executable).resolve()), 'python_identity': identity(Path(sys.executable).resolve().read_bytes())}
check('current_pinned_environment', current_environment['python'] == receipt['environment']['python'] and current_environment['platform'] == receipt['environment']['platform'] and current_environment['runtime_bundle_version'] == receipt['environment']['runtime_bundle_version'])
check('source_still_clean', not git('status', '--porcelain').strip())

diff = git('diff', '--name-status', CANDIDATE, ACCEPTED).decode().splitlines()
report = {
    'schema': 'ontokin.c268.recovery-acceptance-audit/1',
    'auditor': '/root/remote_audit',
    'at_utc': datetime.now(timezone.utc).isoformat(),
    'accepted_checkpoint': ACCEPTED,
    'candidate': CANDIDATE,
    'candidate_tree': review['tree'],
    'accepted_tree': git('rev-parse', ACCEPTED + '^{tree}').decode().strip(),
    'passed': all(a['passed'] for a in assertions),
    'assertion_count': len(assertions),
    'failures': [a for a in assertions if not a['passed']],
    'assertions': assertions,
    'candidate_input_count': len(receipt['input_files_before']),
    'accepted_input_deltas': accepted_input_deltas,
    'candidate_output_count': len(receipt['output_files']),
    'review_artifact_count': len(manifest['files']),
    'changed_paths': diff,
    'groups': groups,
    'fixture_archives': zip_inventory,
    'reviewer': review['reviewer'],
    'optional_suggestions': review['optional_suggestions'],
    'recorded_environment': receipt['environment'],
    'current_environment': current_environment,
    'resulting_main_command': [str(python_binary), '-B', runner_path, '--repo', 'ACTUAL_CLEAN_MAIN_CHECKOUT', '--phase', 'main-integration', '--output', 'NEW_EXTERNAL_OUTPUT_DIRECTORY', '--c268-methods', '35'],
    'reuse_conditions': ['Publish and read back identical payload blobs, including binary archives and raw logs', 'Retain original candidate identities; do not relabel earlier execution as a new commit execution', 'Only current record/evidence changes occurred since the candidate; run applicable documentation/workflow checks after publication', 'Run the complete existing affected runner freshly on actual resulting main and preserve exact source/input/environment/output receipt', 'Any changed implementation, test, dependency, fixture, runner or environment requires affected re-evaluation'],
    'limits': review['not_run'] + review['nonclaims'],
    'no_cohort_execution': True,
    'no_repository_or_remote_mutations': True,
}
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'ACCEPTANCE-AUDIT.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: report[k] for k in ['passed', 'assertion_count', 'failures', 'candidate_input_count', 'candidate_output_count', 'review_artifact_count', 'accepted_input_deltas']}, indent=2))
