"""Audit saved P19 evidence only. Never opens the recorded host input paths."""
from pathlib import Path
from email.parser import BytesHeaderParser
import ast
import datetime
import hashlib
import json
import re

ROOT = Path('/workspace/scratch/816157c5a30b')
OUT = ROOT / 'operational_review'
T = ROOT / 'technical'
A = T / 'attempt001'
CHECKS = []
FILES = []


def read(path):
    raw = path.read_bytes()
    FILES.append({'path': str(path.relative_to(ROOT)), 'bytes': len(raw),
                  'sha256': hashlib.sha256(raw).hexdigest()})
    return raw


def document(path):
    return json.loads(read(path))


def check(name, condition, evidence=None):
    CHECKS.append({'id': name, 'passed': bool(condition), 'evidence': evidence})


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


plan_raw = read(T / 'OBSERVATION-PLAN.json')
plan = json.loads(plan_raw)
script = read(T / 'observe_inputs.py')
approval_raw = read(OUT / 'PREEXEC-REVIEW-003.json')
approval = json.loads(approval_raw)
wrapper = read(T / 'run_observation_once.py')
launch = document(T / 'LAUNCH-INTENT.json')
completion = document(T / 'LAUNCH-RESULT.json')
intent = document(A / 'INTENT.json')
result = document(A / 'RESULT.json')
stdout = read(T / 'observation.stdout')
stderr = read(T / 'observation.stderr')
summary = json.loads(stdout)
operations = document(ROOT / 'state/OPERATIONS.json')
source = read(ROOT / 'OntoKin/prototypes/static_tray_v01/current_host_inspection_v01.py')
lock_raw = read(ROOT / 'OntoKin/tools/native-reader-verification-linux-cp312.lock')

check('A01_exact_plan', digest(plan_raw) == '946fd14dc1022ddb1e9cc4d8f22a0c0a2746efb3b0b9c08db62cd70c17945aab')
check('A02_exact_script', len(script) == 12873 and digest(script) == 'c14b171df87d47dbd78d6a73946c72c32add8891d6d52b0a7e1da697cdd1e287')
check('A03_exact_source', len(source) == 196305 and digest(source) == 'e14542e45deb200bb97f2a591c94bdd19916a1d33dcb3ce9f631816b98e0c206')
check('A04_exact_lock', len(lock_raw) == 779 and digest(lock_raw) == 'a7f17491000c2e139ccc5d213ca0e8a6f917e5befb4b878fef29f5ff72ae780f')
check('A05_independent_approval', approval['candidate'] == 'candidate003' and approval['verdict'] == 'accepted_for_one_bounded_raw_actual_input_observation' and approval['mandatory_findings'] == [])
check('A06_approval_candidate_identities', {x['sha256'] for x in approval['candidate_files']} == {digest(script), digest(plan_raw)})
check('A07_launch_identities', launch['plan_sha256'] == digest(plan_raw) and launch['review_sha256'] == digest(approval_raw) and launch['wrapper_sha256'] == digest(wrapper))
check('A08_frozen_invocation', launch['argv'] == plan['command'] and launch['environment'] == plan['environment'] and launch['cwd'] == plan['cwd'] and launch['timeout_seconds'] == 60)
check('A09_completed_blocked_attempt', completion['completed'] is True and completion['returncode'] == 2 and completion['retry'] is False and launch['actual_invocation_retries'] == 0)
check('A10_stream_identity', completion['stdout_sha256'] == digest(stdout) and completion['stderr_sha256'] == digest(stderr) and not stderr)
check('A11_intent_identity', intent['script_sha256'] == digest(script) and intent['source_sha256'] == digest(source) and intent['argv'] == [plan['script']['path']])
check('A12_result_identity', result['script_sha256'] == digest(script) and result['source_sha256'] == digest(source) and result['source_revision'] == plan['source_revision'])

pins = []
for line in lock_raw.decode('ascii').splitlines():
    if not line or line.startswith('#'):
        continue
    requirement, wheel_hash = line.split(' --hash=sha256:')
    name, version = requirement.split('==')
    pins.append({'name': name, 'version': version, 'wheel_sha256': wheel_hash})
check('A13_lock_pins_equal_retained', len(pins) == 7 and result['raw']['pin_lock']['pins'] == pins and result['raw']['pin_lock']['sha256'] == digest(lock_raw))
packages = result['package_metadata']
check('A14_exact_first_five_order', len(packages) == 5 and [r['name'] for r in packages] == [r['name'] for r in pins[:5]])
metadata_rows = []
normalize = lambda text: re.sub(r'[-_.]+', '-', text).lower()
for index, row in enumerate(packages):
    path = A / ('METADATA-' + normalize(row['name']) + '.txt')
    raw = read(path)
    headers = BytesHeaderParser().parsebytes(raw)
    names, versions = headers.get_all('Name'), headers.get_all('Version')
    matches = names is not None and len(names) == 1 and normalize(names[0]) == normalize(pins[index]['name']) and versions == [pins[index]['version']]
    metadata_rows.append({'package': row['name'], 'expected_version': pins[index]['version'],
                          'observed_names': names, 'observed_versions': versions,
                          'matches_pin': matches, 'retained_path': str(path.relative_to(ROOT)),
                          'bytes': len(raw), 'sha256': digest(raw)})
    check('M%02d_retained_bytes' % (index + 1), len(raw) == row['identity']['size_bytes'] and digest(raw) == row['metadata_sha256'])
    check('M%02d_independent_headers' % (index + 1), names == row['observed_names'] and versions == row['observed_versions'] and row['expected_version'] == pins[index]['version'])
check('A15_first_four_match_fifth_differs', [r['matches_pin'] for r in metadata_rows] == [True, True, True, True, False])
check('A16_exact_mismatch', metadata_rows[4]['package'] == 'rpds-py' and metadata_rows[4]['expected_version'] == '2026.5.1' and metadata_rows[4]['observed_versions'] == ['2026.6.3'])
check('A17_first_blocker_is_fifth_record', result['first_blocker']['type'] == 'InputBlocker' and result['first_blocker']['code'] == 'PACKAGE_METADATA_PIN_MISMATCH' and result['first_blocker']['details'] == packages[4])
actual_metadata_files = {p.name for p in A.iterdir() if p.name.startswith('METADATA-')}
check('A18_no_later_metadata_artifacts', actual_metadata_files == {'METADATA-' + normalize(r['name']) + '.txt' for r in packages} and not any(r['name'] in [p['name'] for p in packages] for r in pins[5:]))

reads = result['raw']['metadata_observations']
check('A19_raw_reader_scope_and_order', [(r['role'], r['reader'], r['outcome']) for r in reads] == [('python', '_read_origin_elf_metadata', 'metadata_returned'), ('loader', 'read_elf_metadata', 'metadata_returned'), ('libc', '_read_libc_static_tls_elf_metadata', 'metadata_returned')] and all(r['route'] == 'raw_metadata_primitive_only' and r['operational_policy_admitted'] is False for r in reads))
keys = {'class', 'endian', 'machine', 'type', 'interpreter', 'needed', 'soname', 'rpath', 'runpath'}
check('A20_metadata_shape', all(set(r['metadata']) == keys and r['metadata']['class'] == 64 and r['metadata']['endian'] == 'little' and r['metadata']['machine'] == 62 for r in reads))
check('A21_limited_relation', result['raw']['limited_relation'] == {'actual_python_needed_includes_libc': True, 'actual_python_interpreter_resolves_to_pinned_loader': True, 'complete_loader_selection_proved': False} and 'libc.so.6' in reads[0]['metadata']['needed'] and reads[0]['metadata']['rpath'] == ['$ORIGIN/../lib'])
expected_pins = {
    'python': (30894944, 'fa67443527ed9647f760d807e2a38f26340757123e643c4639cf273ed15d5ea7'),
    'loader': (225672, 'c8438e4fde1934e61c88311633f00949ff645d5c04cdb8671fa3d78164d2f307'),
    'libc': (1995216, '9792e3cbb541c8f44c7acf5f14f4022ea62998ecc787d326bed4d8b6547dfd92'),
}
check('A22_observed_fixed_inputs', [r['role'] for r in result['observations']] == list(expected_pins) and all((r['size_bytes'], r['sha256']) == expected_pins[r['role']] and r['mode'] == '0o755' and r['canonical_path'] == r['path'] for r in result['observations']))
maps_ok = True
for row in result['observations']:
    matches = [line.split(None, 5) for line in result['raw']['selected_process_maps'] if line.split(None, 5)[5] == row['path']]
    maps_ok &= bool(matches) and all(int(m[4]) == row['inode'] and int(m[3].split(':')[0], 16) == 0 and int(m[3].split(':')[1], 16) == row['device'] for m in matches)
check('A23_retained_map_witnesses', maps_ok)
expected_rechecks = {r['path'] for r in result['observations']} | {plan['source']['path'], plan['lock']['path']} | {r['metadata_path'] for r in packages}
check('A24_exact_recheck_set', len(result['post_read_rechecks']) == 10 and {r['path'] for r in result['post_read_rechecks']} == expected_rechecks)
check('A25_all_rechecks_equal', all(r['identity_unchanged'] is True and r['bytes_unchanged'] is True for r in result['post_read_rechecks']) and result['postflight_failures'] == [])
check('A26_no_recorded_target_attempts', result['process_operation_attempts'] == [] and result['direct_target_starts'] == 0)
check('A27_honest_gates', result['status'] == 'input_blocked' and all(result[k] is False for k in ['h0_accepted', 'operational_plan_created', 'operational_policy_admitted', 'h1_approved']) and result['N57'] == 'external_only_not_evaluated')
check('A28_stdout_agrees', summary['status'] == result['status'] and summary['first_blocker'] == result['first_blocker'] and summary['packages_checked'] == 5 and summary['forbidden_attempts'] == 0 and summary['post_read_equal'] is True)
times = [datetime.datetime.fromisoformat(launch['at_utc']), datetime.datetime.fromisoformat(intent['recorded_at_utc']), datetime.datetime.fromisoformat(result['at_utc'])]
check('A29_times_bounded_and_ordered', times == sorted(times) and 0 <= result['elapsed_seconds'] <= completion['elapsed_seconds'] < 60)
tree = ast.parse(wrapper)
calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name) and n.func.value.id == 'subprocess' and n.func.attr == 'run']
check('A30_one_source_launch_site_no_shell', len(calls) == 1 and all(k.arg != 'shell' for k in calls[0].keywords))
prelaunch = [r for r in operations['completed_nonproduct_failures'] if r['operation'] == 'P19 prelaunch wrapper attempt001']
check('A31_preserved_prelaunch_failure', len(prelaunch) == 1 and prelaunch[0]['target_invocation_started'] is False and prelaunch[0]['unknown'] is False and operations['current_unknown'] == [])

audit = {'schema': 'ontokin.c271.p19-retained-outcome-audit/1',
         'reviewer': '/root/operational_review', 'kind': 'retained_artifact_checks_not_product_tests',
         'checks': CHECKS, 'passed': sum(c['passed'] for c in CHECKS),
         'failed': sum(not c['passed'] for c in CHECKS), 'files': FILES,
         'independent_metadata_rows': metadata_rows,
         'host_inputs_reopened': False, 'product_imports_or_runs': False,
         'later_package_metadata_read': False,
         'limits': ['Raw parser results are audited as retained source-bound observations, not rerun.',
                    'No complete loader selection or H0/operational-plan acceptance.',
                    'Prelaunch absence/no-start reconciliation is retained Director evidence; reviewer inspected ordering and identity.']}
with (OUT / 'OUTCOME-AUDIT.json').open('x') as stream:
    json.dump(audit, stream, indent=2)
    stream.write('\n')
print(json.dumps({'passed': audit['passed'], 'failed': audit['failed'], 'metadata': metadata_rows}))
raise SystemExit(0 if audit['failed'] == 0 else 1)
