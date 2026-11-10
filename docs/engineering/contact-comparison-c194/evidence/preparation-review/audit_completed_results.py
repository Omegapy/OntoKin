"""Independently audit completed C194 receipts without any native execution."""
from pathlib import Path
import argparse
import datetime
import json
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--repo', type=Path, required=True)
parser.add_argument('--run', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
repo, run, out = args.repo.resolve(), args.run.resolve(), args.out.resolve()
kit = repo / 'docs/engineering/contact-preparation-c194'
receiving = run / 'receiving'
sys.path.insert(0, str(kit))
from common import digest, verify_freeze

def read(path):
    return json.loads(path.read_text())

freeze = verify_freeze()
results = read(run / 'RESULTS.json')
ledger = read(run / 'EXECUTION-LEDGER.json')
assert results['automated_gates_passed'] and 'finished_utc' in results
assert ledger['results_sha256'] == digest(run / 'RESULTS.json')
assert ledger['freeze_sha256'] == freeze['freeze_sha256']
assert ledger == read(kit / 'EXECUTION-LEDGER.json')
expected = ['ok-G', 'python-G', 'ok-H', 'python-H']
assert ledger['planned_builds'] == expected
assert [r['id'] for r in ledger['started_builds']] == expected
assert ledger['automatic_retry_allowed'] is False
assert len(list((run / 'builds').iterdir())) == 4
frozen = read(kit / 'FREEZE.json')
assert frozen['created_utc'] < ledger['reserved_utc'] <= results['started_utc']
assert all(r['started_utc'] >= ledger['reserved_utc'] for r in ledger['started_builds'])
commands = {p.stem: read(p) for p in (run / 'commands').glob('*.json')}
assert set(commands) == {a + '-' + i for a in ['build', 'reopen'] for i in expected} | {'receiving'}
assert all(r['passed'] and r['completed'] and r['returncode'] == 0 for r in commands.values())

summary = read(receiving / 'summary.json')
assert summary == results['receiving']['summary'] and results['receiving']['passed']
assert results['receiving']['summary_sha256'] == digest(receiving / 'summary.json')
assert summary['pass_for_executed_receiving_checks']
assert summary['glb_paths'] == 8 and summary['three_poses'] == 24 and summary['blender_import_jobs'] == 4
identities = read(receiving / 'artifact-identities.json')
expected_paths = {f'deliveries/{i}/{name}.glb' for i in expected for name in ['raw', 'final']}
assert len(identities) == 8 and {r['path'] for r in identities} == expected_paths
for row in identities:
    path = receiving / row['path']
    assert path.stat().st_size == row['bytes']
    assert digest(path) == row['sha256'] == digest(Path(row['source']))

khronos = read(receiving / 'khronos.json')
assert set(khronos) == expected_paths
errors = sum(r['report']['issues']['numErrors'] for r in khronos.values())
warnings = sum(r['report']['issues']['numWarnings'] for r in khronos.values())
infos = sum(r['report']['issues']['numInfos'] for r in khronos.values())
assert errors == warnings == 0
assert errors == summary['khronos_errors'] and warnings == summary['khronos_warnings']
assert infos == summary['khronos_infos']
assert all(r['sha256'] == digest(receiving / p) for p, r in khronos.items())
three = read(receiving / 'three.json')
assert three['pass'] and len(three['reports']) == 8
assert {r['path'] for r in three['reports']} == expected_paths
assert sum(len(r['poses']) for r in three['reports']) == 24
for row in three['reports']:
    assert row['sha256'] == digest(receiving / row['path'])
    case = row['id'].split('-')[1]
    contact = 1.48 if case == 'G' else 1.56
    assert [p['time'] for p in row['poses']] == [0, contact, 2]
    assert len(row['meshNames']) == 7 and row['duration'] == 2
    assert abs(row['poses'][-1]['gapsMm']['left']) <= .5
    assert abs(row['poses'][-1]['gapsMm']['right'] - 15) <= .5

renders = []
for identifier in expected:
    directory = receiving / 'renders' / identifier
    record = read(directory / 'receipt.json')
    assert record['input_sha256'] == digest(receiving / 'deliveries' / identifier / 'final.glb')
    assert record['all_sampled_imports_match_glb'] and len(record['frames']) == 3
    assert len(list(directory.glob('*.png'))) == 3
    renders.append({'id': identifier, 'input_sha256': record['input_sha256'], 'frames': 3,
        'max_import_bounds_error_mm': max(f['maximum_import_vs_glb_bounds_error_m'] for f in record['frames']) * 1000})
assert len(list((receiving / 'renders').rglob('*.png'))) == 12

report = {
    'version': 'C194-independent-completed-preparation-review-1', 'passed': True,
    'reviewer': 'c194_review', 'at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'implementation_revision': results['implementation_revision'],
    'freeze_sha256': freeze['freeze_sha256'],
    'input_manifest_sha256': freeze['input_manifest_sha256'],
    'results_sha256': digest(run / 'RESULTS.json'),
    'ledger_sha256': digest(run / 'EXECUTION-LEDGER.json'),
    'actual_constructors': 4, 'independent_scene_replays': 4,
    'four_reserved_builds_only': True, 'freeze_preceded_native_execution': True,
    'frozen_inputs_unchanged': True,
    'artifact_review_sha256': digest(out / 'ARTIFACT-REPLAY-REVIEW.json'),
    'automated_gates_passed': True,
    'khronos': {'paths': 8, 'errors': errors, 'warnings': warnings, 'infos': infos},
    'three': {'clips': 8, 'poses': 24, 'revision': three['threeRevision']},
    'blender': {'imports': 4, 'original_panels': 12, 'jobs': renders},
    'visual_review': 'Parent coordinator owns direct visual inspection; not claimed by this audit',
    'qualified_for_author_dispatch': 'Pending bound visual receipt and final QUALIFICATION.json',
    'new_native_executions_by_reviewer': 0,
    'no_full_release_or_comparative_advantage_claim': True,
    'review_harness_note': 'An earlier unexecuted inline version had a conditional-expression syntax error; corrected before any audit execution. No native or product work repeated.',
    'next_action': 'After passing visual finalization, freeze the C194 public comparison protocol and dispatch exactly two fresh default authors with empty histories'
}
(out / 'RESULTS-REVIEW.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'passed': True, 'review': str(out / 'RESULTS-REVIEW.json'),
    'actual_builds': 4, 'khronos_errors': errors, 'khronos_warnings': warnings,
    'khronos_infos': infos, 'three_poses': 24, 'original_panels': 12}))
