#!/usr/bin/env python3
"""Independent final-input delivery and quaternion oracle audit, stdlib only.

No corpus author module, production evaluator, candidate output or libm trig is
imported. The supplied reference intervals are checked using a separate exact
recurrence at a higher polynomial degree and Hamilton product expansion.
"""
import argparse
from fractions import Fraction as F
import hashlib
import json
import math
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--freeze', type=Path, required=True)
parser.add_argument('--oracle', default='evidence/INDEPENDENT-INPUT-CHECK-04.json')
parser.add_argument('--report', type=Path, required=True)
args = parser.parse_args()
assert not args.report.exists()
root = args.freeze
rows = []

def load(name):
    return json.loads((root / name).read_text())

def check(name, actual, expected=True):
    row = {'name': name, 'passed': actual == expected}
    if not row['passed']:
        row.update(actual=str(actual), expected=str(expected))
    rows.append(row)

def trigonometric_pair(x, sine):
    # Exact Taylor recurrence through degree 220, with a uniform Lagrange
    # bound on degree 221. This is distinct from the author's degree-180 sum.
    assert abs(x) <= 16
    term = x if sine else F(1)
    total = term
    degree = 1 if sine else 0
    while degree + 2 <= 220:
        term = -term * x * x / ((degree + 1) * (degree + 2))
        total += term
        degree += 2
    radius = abs(x) ** 221 / math.factorial(221)
    return total - radius, total + radius

def add(left, right):
    return left[0] + right[0], left[1] + right[1]

def scale(pair, coefficient):
    a, b = pair[0] * coefficient, pair[1] * coefficient
    return min(a, b), max(a, b)

def enclosure_in_report(name, actual, report):
    low = F(report['lower_decimal'])
    high = F(report['upper_decimal'])
    check(name + '/ordered', low <= high)
    check(name + '/contains-independent-enclosure', low <= actual[0] <= actual[1] <= high)
    check(name + '/useful-oracle-width', high - low <= F(1, 2**150))

physics = {c['id']: c for c in load('physics-cases.json')['cases']}
oracle = load(args.oracle)
check('oracle/author-observation-status', oracle['status'], 'passed')
check('oracle/no-candidate', oracle['candidate_output_used'], False)
check('oracle/no-production', oracle['production_imported'], False)
reference_rows = oracle['trigonometric_reference']
expected_samples = {(c['id'], str(F(sample[0]))) for c in physics.values() for sample in c['samples']}
check('oracle/complete-sample-membership', {(r['case'], str(F(r['time']))) for r in reference_rows}, expected_samples)
check('oracle/no-duplicate-samples', len(reference_rows), len(expected_samples))
for record in reference_rows:
    case = physics[record['case']]
    name = record['case'] + '/' + record['time']
    table = next(r for r in case['samples'] if F(r[0]) == F(record['time']))
    theta = F(table[1])
    check(name + '/literal-phase', F(record['unwrapped_phase']), theta)
    check(name + '/literal-speed', F(record['signed_speed']), F(table[2]))
    cosine = trigonometric_pair(theta / 2, False)
    sine = trigonometric_pair(theta / 2, True)
    enclosure_in_report(name + '/increment-w', cosine, record['increment_quaternion_w'])
    enclosure_in_report(name + '/increment-axis', sine, record['increment_quaternion_axis'])
    enclosure_in_report(name + '/full-cosine', trigonometric_pair(theta, False), record['full_cos'])
    enclosure_in_report(name + '/full-sine', trigonometric_pair(theta, True), record['full_sin'])
    increment = [(F(0), F(0)) for _ in range(4)]
    increment[0] = cosine
    increment[{'world_x': 1, 'world_y': 2, 'world_z': 3}[case['axis']]] = sine
    initial = [F(x) for x in case.get('initial_quaternion', ['1', '0', '0', '0'])]
    # Each output explicitly expands left-factor increment * right-factor q0.
    terms = [((0, 0, 1), (1, 1, -1), (2, 2, -1), (3, 3, -1)),
             ((0, 1, 1), (1, 0, 1), (2, 3, 1), (3, 2, -1)),
             ((0, 2, 1), (1, 3, -1), (2, 0, 1), (3, 1, 1)),
             ((0, 3, 1), (1, 2, 1), (2, 1, -1), (3, 0, 1))]
    for component, products in enumerate(terms):
        value = (F(0), F(0))
        for left, right, sign in products:
            value = add(value, scale(increment[left], initial[right] * sign))
        enclosure_in_report(name + '/world-left-q' + str(component), value, record['quaternion_wxyz'][component])

delivery = load('delivery-cases.json')
check('delivery/no-runtime-claim', delivery['execution_claim'], False)
check('delivery/complete-physics-membership', {c['physics_case'] for c in delivery['cases']}, set(physics))
check('delivery/fixed-budget', delivery['allocation_decision']['source_operations'], 1000000)
line = b'execution { max_operations = 1000000; max_elapsed = 30[s]; }\n'
for case in delivery['cases']:
    key = case['id']
    prior = physics[case['physics_case']]
    raw = (root / 'sources' / (key + '.ok')).read_bytes()
    original = (root / 'sources' / (prior['id'] + '.ok')).read_bytes()
    check(key + '/only-source-allocation-addition', raw.replace(line, b'', 1), original)
    check(key + '/one-source-allocation', raw.count(line), 1)
    check(key + '/same-horizon', F(case['options']['end']), F(prior['horizon']))
    check(key + '/fixed-fps-and-tolerances', [case['options'][k] for k in ('fps', 'position_tolerance_m', 'rotation_tolerance_rad', 'time_tolerance_s')], [4, .001, .001, 1e-6])
    check(key + '/fixed-host', case['host_policy'], {'max_operations': 1000000, 'max_elapsed_ms': 30000})
    check(key + '/old-artifact-availability', case['actual_predecessor_artifact_available'],
          prior['id'] not in {'p03-braking-reversal', 'p19-torque-then-impulse', 'p20-impulse-then-torque', 'p28-release-then-torque'})
    for record in case['source_records']:
        check(key + '/' + record['torque_key'] + '/program', record['program_revision'], case['identity']['program_revision'])
        for field in ('source_location', 'operand_location', 'duration_location'):
            location = record[field]
            check(key + '/' + record['torque_key'] + '/' + field + '/source', location['source_revision'], 'sha256:' + hashlib.sha256(raw).hexdigest())
            check(key + '/' + record['torque_key'] + '/' + field + '/positive-span', 0 <= location['start_byte'] < location['end_byte'] <= len(raw))
        text = raw[record['source_location']['start_byte']:record['source_location']['end_byte']].decode()
        check(key + '/' + record['torque_key'] + '/statement-key', '@ "' + record['torque_key'] + '"' in text)
        check(key + '/' + record['torque_key'] + '/statement-axis', 'about ' + record['axis'] in text)

geometry = delivery['geometry_and_landmarks']
vertices = [[F(x) for x in row] for row in geometry['marker_vertices_local_m']]
check('landmarks/local-radius-squared', max(sum(x*x for x in row) for row in vertices), F(geometry['marker_local_radius_squared']))
offset = [F(x) for x in geometry['nested_tip_origin_offset']]
check('landmarks/nested-origin-squared', sum(x*x for x in offset), F(geometry['nested_tip_origin_radius_squared']))
check('landmarks/local-L1-maximum', max(sum(abs(x) for x in row) for row in vertices), F(7, 8))
check('landmarks/nested-path-L1', sum(abs(x) for x in offset), F(9, 8))

workflow = load('agent/workflow-repairs.json')
base = (root / 'sources/workflow-agent-base.ok').read_bytes()
for repair in workflow['repairs']:
    patch = repair['patch']
    check(repair['id'] + '/actual-old-patch', base[patch['start_byte']:patch['end_byte']].decode(), patch['expected_text'])
    changed = base[:patch['start_byte']] + patch['replacement'].encode() + base[patch['end_byte']:]
    check(repair['id'] + '/actual-new-source', changed, (root / 'sources' / (repair['id'] + '.ok')).read_bytes())

result = {'schema_version': 'ontokin.independent-corpus-delivery-oracle-review/1',
          'outcome': 'passed' if all(r['passed'] for r in rows) else 'failed',
          'checks': len(rows), 'complete_quaternion_samples': len(reference_rows),
          'author_oracle_path': args.oracle,
          'author_oracle_sha256': hashlib.sha256((root / args.oracle).read_bytes()).hexdigest(),
          'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'production_imported_or_executed': False, 'candidate_output_used': False,
          'runtime_or_release_acceptance': False,
          'failures': [r for r in rows if not r['passed']], 'rows': rows}
args.report.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
print(json.dumps({k: v for k, v in result.items() if k != 'rows'}, indent=2))
raise SystemExit(0 if result['outcome'] == 'passed' else 1)
