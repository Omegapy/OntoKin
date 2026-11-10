"""Read-only review of C192 .ok evidence; all review writes stay beside this file."""
import ast
import copy
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np

ROOT = Path('/workspace/scratch/d52b43d02a92')
REPO = ROOT / 'OntoKin'
OK_REPO = ROOT / 'participants/ok'
SCOPE = Path('docs/engineering/contact-comparison-c192')
OUT = Path(__file__).resolve().parent
FREEZE_COMMIT = '9d1118f63195c8458aa804f2a99922cc780365aa'
FREEZE_TREE = '5a5b22ddc1763d876c6f10339f20112977ee699d'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def run(argv):
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    done = subprocess.run(argv, cwd=REPO, capture_output=True, text=True)
    commands.append({'argv': argv, 'cwd': str(REPO), 'started_utc': started,
                     'finished_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                     'returncode': done.returncode, 'stdout': done.stdout, 'stderr': done.stderr})
    save('commands.json', commands)
    assert done.returncode == 0, commands[-1]
    return done.stdout


commands = []
results_bytes = (REPO / SCOPE / 'results.json').read_bytes()
(OUT / 'results-reviewed.json').write_bytes(results_bytes)
results = json.loads(results_bytes)
freeze_bytes = (REPO / SCOPE / 'frozen/INPUT-FREEZE.json').read_bytes()
frozen = json.loads(freeze_bytes)
assert freeze_bytes == subprocess.check_output(
    ['git', 'show', FREEZE_COMMIT + ':' + str(SCOPE / 'frozen/INPUT-FREEZE.json')], cwd=REPO)
assert subprocess.check_output(['git', 'rev-parse', FREEZE_COMMIT + '^{tree}'], cwd=REPO, text=True).strip() == FREEZE_TREE
freeze_checks = []
for repo in (REPO, OK_REPO):
    differences = [rel for rel, meta in frozen['files'].items()
                   if not (repo / rel).is_file() or sha(repo / rel) != meta['sha256']
                   or (repo / rel).stat().st_size != meta['bytes']]
    assert not differences, differences
    freeze_checks.append({'repo': str(repo), 'files_checked': len(frozen['files']),
                          'all_exact': True, 'differences': differences})

scope = REPO / SCOPE
source_dir = OK_REPO / SCOPE / 'participants/ok/sources'
starter = (scope / 'starters/design.ok').read_bytes()
assert starter.count(b'at = [380, 130, -220][mm];') == 1
assert (source_dir / '00-starter.ok').read_bytes() == starter
source_rows = []
for name, target in (('01-edit.ok', '362.5'), ('02-reuse.ok', '372.5')):
    source = source_dir / name
    expected = starter.replace(b'at = [380, 130, -220][mm];',
                               f'at = [{target}, 130, -220][mm];'.encode())
    assert source.read_bytes() == expected
    source_rows.append({'source': str(source), 'sha256': sha(source), 'stop_mm': float(target),
                        'exact_single_literal_change_from_frozen_starter': True})
assert (source_dir / '02-reuse.ok').read_bytes() == (source_dir / '01-edit.ok').read_bytes().replace(
    b'at = [362.5, 130, -220][mm];', b'at = [372.5, 130, -220][mm];')

sys.path.insert(0, str(REPO / 'docs/engineering/guided-contact-c191/independent/checker'))
from c190_glb_difference import array, decode

builds = [
    ('ok-edit-submitted', 'edit', ROOT / 'c192-runs/ok/edit-build-01',
     ROOT / 'c192-audit/first-reproduction/ok-edit', 'submitted'),
    ('ok-edit-rebuilt', 'edit', ROOT / 'c192-audit/first-reproduction/ok-edit/rebuild',
     ROOT / 'c192-audit/first-reproduction/ok-edit', 'rebuilt'),
    ('ok-reuse-submitted', 'reuse', ROOT / 'c192-runs/ok/reuse-build-01',
     ROOT / 'c192-audit/reuse-reproduction/ok-reuse', 'submitted'),
    ('ok-reuse-rebuilt', 'reuse', ROOT / 'c192-audit/reuse-reproduction/ok-reuse/rebuild',
     ROOT / 'c192-audit/reuse-reproduction/ok-reuse', 'rebuilt'),
    ('ok-edit-regenerated', 'edit', ROOT / 'c192-runs/ok/edit-regeneration-01',
     ROOT / 'c192-audit/reuse-reproduction/ok-edit-regenerated', 'submitted'),
]
rows = []
artifacts = {}
sample_times = (np.arange(481, dtype=float) / 240).astype('<f4').astype(float)
all_parts = {'base', 'left_carriage', 'left_shoe', 'left_stop', 'right_carriage', 'right_shoe', 'right_stop'}
for label, case, build, audit_root, kind in builds:
    found = list(build.rglob('raw.glb'))
    assert len(found) == 1
    artifact = found[0].parent
    artifacts[label] = artifact
    delivery = read(build / 'delivery.json')
    original_score = read(audit_root / (kind + '-score/score.json'))
    source = artifact / 'source.ok'
    current_source = source_dir / ('01-edit.ok' if case == 'edit' else '02-reuse.ok')
    assert source.read_bytes() == current_source.read_bytes() == (build / 'submitted-source.ok').read_bytes()
    assert sha(source) == delivery['source_sha256'] == original_score['source_sha256']
    assert delivery['source_unchanged_during_build'] and not delivery['successful']
    assert delivery['returncode'] == 1
    transaction = read(artifact.parent / 'result.json')
    assert transaction['successful'] is False and transaction['committed'] is False
    assert transaction['accepted_revision'] is None and transaction['artifact_directory'] is None
    assert transaction['levels'] == {'constructed': True, 'destination_validated': False,
                                      'evaluated': True, 'exported': False, 'represented': True}
    assert [v['code'] for v in transaction['diagnostics']] == ['C191_E_MAPPING']
    assert transaction['cost']['requested_operations'] == 1000000
    assert transaction['cost']['requested_elapsed_ms'] == 80000
    implementation = read(artifact / 'implementation-manifest.json')
    for rel, meta in implementation['files'].items():
        pin = frozen['files']['prototypes/guided_contact_v01/' + rel]
        assert meta == pin
        assert sha(artifact / 'implementation' / rel) == pin['sha256']
    assert sha(artifact / 'backend.json') == frozen['files']['docs/language-design/guided-contact-v0.1/backend.json']['sha256']
    backend = read(artifact / 'backend.json')
    assert transaction['runtime']['executable_sha256'] == backend['runtime']['executable_sha256']

    fresh_score_dir = OUT / ('score-' + label)
    run([sys.executable, '-B', str(scope / 'tools/score_submission.py'), '--repo', str(REPO),
         '--build', str(build), '--case', case, '--out', str(fresh_score_dir)])
    fresh = read(fresh_score_dir / 'score.json')
    for key in ('source_localization_pass', 'canonical_only_target_field_changed', 'build_successful',
                'playback_pass', 'mapping_pass', 'pass', 'maximum_native_to_final_mm',
                'maximum_continuous_raw_to_final_mm', 'hashes', 'left_travel_mm', 'right_gap_mm'):
        assert fresh[key] == original_score[key], (label, key)
    assert fresh['source_localization_pass'] and fresh['playback_pass']
    assert fresh['mapping_pass'] is False and fresh['pass'] is False and fresh['build_successful'] is False
    assert fresh['maximum_native_to_final_mm'] > .2 and fresh['maximum_continuous_raw_to_final_mm'] > .2
    playback = read(fresh_score_dir / 'playback.json')
    assert playback['recording']['keys'] == 481 and playback['recording']['common_key_grid_verified']
    assert playback['clearance']['certified_unrelated_pairs'] == 20

    native = read(artifact / 'native-transforms.json')
    reopened = read(audit_root / (kind + '-reopen/native-transforms.json'))
    assert len(native) == len(reopened) == 481 and native == reopened
    assert all(row['frame'] == i and row['time_s'] == i / 240 for i, row in enumerate(native))
    assert all(set(row['matrices_blender_m']) == all_parts and set(row['bounds_gltf_mm']) == all_parts for row in native)
    reopen_summary = read(audit_root / (kind + '-reopen/summary.json'))
    reopen_command = read(audit_root / (kind + '-reopen.command.json'))
    assert reopen_command['returncode'] == 0
    assert '--factory-startup' in reopen_command['argv'] and '--python-exit-code' in reopen_command['argv']
    assert reopen_command['argv'][reopen_command['argv'].index('-b') + 1] == str(artifact / 'scene.blend')
    assert reopen_summary['pass'] and reopen_summary['configuration_unchanged'] and reopen_summary['cache_clear_completed']
    assert not reopen_summary['reconstructed_or_repaired']
    assert reopen_summary['opened_scene_sha256'] == sha(artifact / 'scene.blend') == fresh['hashes']['scene.blend']
    assert reopen_summary['source_sha256'] == sha(source)
    assert reopen_summary['canonical_input_sha256'] == sha(artifact / 'canonical-input.json')
    configuration = read(audit_root / (kind + '-reopen/configuration-before.json'))
    world = configuration['world']
    objects = configuration['objects']
    assert len(objects) == 13
    assert sum(obj['type'] == 'MESH' and not obj['hide_render'] for obj in objects.values()) == 7
    assert world['substeps_per_frame'] == 10 and world['solver_iterations'] == 100
    assert world['fps'] == 240 and world['frame_start'] == 0 and world['frame_end'] == 480
    assert world['gravity'] == [0., 0., 0.]
    roots = [name for name, obj in objects.items() if obj['rigid_body'] and
             obj['rigid_body']['type'] == 'ACTIVE' and obj['parent'] is None]
    assert set(roots) == {'left_carriage', 'right_carriage'}
    assert all(objects[name]['rigid_body']['mass'] == 1 for name in roots)
    assert all(obj['action'] is None for obj in objects.values())
    for lane, speed in (('left', 125), ('right', 150)):
        car = objects[lane + '_carriage']
        assert car['properties']['motion_authority'] == 'solver' and car['properties']['speed_mm_s'] == speed
        assert not car['drivers'] and not objects[lane + '_shoe']['drivers']
        motor = objects['_' + lane + '_motor']
        assert motor['constraint']['type'] == 'MOTOR' and motor['constraint']['use_motor_lin']
        assert abs(motor['constraint']['motor_lin_target_velocity'] + speed / 1000) < 1e-7
        assert motor['constraint']['solver_iterations'] == 100
    assert objects['left_stop']['properties']['near_face_mm'] == (362.5 if case == 'edit' else 372.5)

    raw_doc, raw_bin = decode(artifact / 'raw.glb')
    final_doc, final_bin = decode(artifact / 'final.glb')
    time_checks = 0
    for doc, blob in ((raw_doc, raw_bin), (final_doc, final_bin)):
        for sampler in doc['animations'][0]['samplers']:
            assert np.array_equal(array(doc, blob, sampler['input'])[:, 0], sample_times)
            time_checks += 1
    x_checks = []
    for channel in raw_doc['animations'][0]['channels']:
        if channel['target']['path'] != 'translation':
            continue
        name = raw_doc['nodes'][channel['target']['node']]['name']
        output = raw_doc['animations'][0]['samplers'][channel['sampler']]['output']
        actual = array(raw_doc, raw_bin, output)
        expected = np.array([[r['matrices_blender_m'][name][0][3], r['matrices_blender_m'][name][2][3],
                              -r['matrices_blender_m'][name][1][3]] for r in native], dtype='<f4').astype(float)
        assert np.array_equal(actual, expected)
        assert np.array_equal(actual[:, 0], array(final_doc, final_bin, output)[:, 0])
        x_checks.append(name)
    assert set(x_checks) == {'left_carriage', 'right_carriage'}
    rows.append({'id': label, 'case': case, 'build': str(build), 'artifact': str(artifact),
                 'source_sha256': sha(source), 'hashes': fresh['hashes'],
                 'implementation_files_exact_to_freeze': len(implementation['files']),
                 'score_recomputed_and_exact': True, 'build_successful': False, 'playback_pass': True,
                 'mapping_pass': False, 'overall_pass': False,
                 'maximum_native_to_final_mm': fresh['maximum_native_to_final_mm'],
                 'maximum_continuous_raw_to_final_mm': fresh['maximum_continuous_raw_to_final_mm'],
                 'reopened_native_rows_exact': 481, 'reopened_parts_per_row': 7,
                 'configuration_verified': True, 'all_raw_final_sampler_times_preserved': True,
                 'sampler_arrays_checked': time_checks, 'raw_native_xyz_and_final_x_exact': x_checks,
                 'transaction_exported': False, 'transaction_destination_validated': False})

comparisons = []
for left, right in [('ok-edit-submitted', 'ok-edit-rebuilt'), ('ok-reuse-submitted', 'ok-reuse-rebuilt'),
                    ('ok-edit-submitted', 'ok-edit-regenerated')]:
    names = ['source.ok', 'canonical-input.json', 'native-transforms.json', 'native-trace.csv', 'raw.glb', 'final.glb']
    equal = {name: (artifacts[left] / name).read_bytes() == (artifacts[right] / name).read_bytes() for name in names}
    assert all(equal.values())
    comparisons.append({'left': left, 'right': right, 'byte_identity': equal,
                        'blend_byte_identity_required': False,
                        'blend_byte_identical': (artifacts[left] / 'scene.blend').read_bytes() ==
                                                (artifacts[right] / 'scene.blend').read_bytes()})

for row in results['native_verification']:
    if not row['id'].startswith('ok-'):
        continue
    assert row['verification_completed'] is True and row['experimental_delivery_pass'] is False
    assert row['submitted']['pass'] is False and row['submitted']['build_successful'] is False
    assert row['submitted']['mapping_pass'] is False and row['submitted']['playback_pass'] is True
assert results['accepted_first_edit_deliveries'] == results['accepted_second_target_deliveries'] == 0
assert results['mapping_pass'] is False
for case in ('edit', 'reuse'):
    row = next(r for r in rows if r['id'] == 'ok-' + case + '-submitted')
    assert results['cases'][case]['pass'] is False
    assert results['cases'][case]['maximum_native_to_final_mm'] == row['maximum_native_to_final_mm']
    assert results['cases'][case]['maximum_continuous_raw_to_final_mm'] == row['maximum_continuous_raw_to_final_mm']

blender = ROOT / 'deps/blender-4.5.3-linux-x64/blender'
expected_blender = read(REPO / 'docs/language-design/guided-contact-v0.1/backend.json')['runtime']['executable_sha256']
assert sha(blender) == expected_blender
reviewed_files = [SCOPE / 'results.json', SCOPE / 'frozen/BRIEF.md', SCOPE / 'frozen/INPUT-FREEZE.json',
                  SCOPE / 'tools/score_submission.py', SCOPE / 'tools/verify_builds.py',
                  SCOPE / 'shared/inspect_native_c192.py',
                  Path('docs/engineering/guided-contact-c191/independent/checker/audit_mapping.py'),
                  Path('docs/engineering/guided-contact-c191/independent/checker/inspect_native.py'),
                  Path('docs/engineering/guided-contact-c191/independent/checker/c190_glb_difference.py')]
file_hashes = {str(p): sha(REPO / p) for p in reviewed_files}
file_hashes[str(SCOPE / 'results.json')] = hashlib.sha256(results_bytes).hexdigest()
record = {'review_role': 'Independent numerical-record and coordinator-harness review of the .ok route only',
          'prior_participant_role': 'Direct Python participant; own route excluded from independent review',
          'started_utc': '2026-11-10T15:04:30Z',
          'checks_finished_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'new_native_runs': 0, 'existing_ok_native_builds_inspected': 5,
          'existing_ok_reopens_inspected': 5, 'replayed_sample_rows_compared': 2405,
          'freeze_commit': FREEZE_COMMIT, 'freeze_tree': FREEZE_TREE,
          'freeze_checks': freeze_checks, 'source_checks': source_rows,
          'pinned_blender_sha256': expected_blender, 'reviewed_files_sha256': file_hashes,
          'artifact_checks': rows, 'byte_comparisons': comparisons,
          'all_review_checks_pass': True, 'evidence_integration_recommendation': 'APPROVE_WITH_NONBLOCKING_CLARITY_NOTE',
          'rejected_outputs_approved': False, 'blocking_issues': [],
          'nonblocking_issues': [{'id': 'N1', 'severity': 'low',
            'location': 'tools/verify_builds.py result.rebuild_exact; results.json ok-edit-regenerated',
            'finding': 'rebuild_exact copies the rebuild request flag. For ok-edit-regenerated it is false because no additional coordinator rebuild was requested, not because the regenerated output mismatched.',
            'impact': 'The existing field name is ambiguous for readers; acceptance remains false and all required compared bytes do match.',
            'suggestion': 'Use a separate rebuild_performed field and reserve rebuild_exact for an observed equality result, or document that false here means not performed.'}],
          'limits': ['No independent endorsement of the Python participant route or its artifact records.',
                     'Cross-route aggregate claims require the complementary route review.',
                     'No new native process was started; this review inspected saved replay data, commands, scripts, and hashes.',
                     'Receiving-application playback and Khronos/Three.js validation are outside this numerical review.',
                     'The unchanged mapping audit rejects before some later checks; this review separately checked common sampler times and native/raw/final X preservation.',
                     'This approves evidence integration only; every reviewed delivery remains rejected.']}
save('findings.json', record)
print(json.dumps({'all_review_checks_pass': True, 'ok_builds': len(rows), 'ok_reopens': 5,
                  'new_native_runs': 0, 'blocking_issues': 0, 'nonblocking_issues': 1,
                  'findings': str(OUT / 'findings.json')}, indent=2))
