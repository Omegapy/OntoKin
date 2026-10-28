"""Static retained-data/source audit; never imports or executes OntoKin."""
from pathlib import Path
import ast
import hashlib
import json

ROOT = Path('/workspace/scratch/73029ed6994e/c043-evidence-inputs')
OUT = Path('/workspace/scratch/73029ed6994e/c043-reviews/angular-evidence.json')
PREFIX = 'docs/engineering/reach-recording-validation-2026-10-23/'
RET = PREFIX + 'checkpoint-042-retained/'

def read(path):
    return json.loads((ROOT / path).read_text())

def identity(path):
    data = path.read_bytes()
    return {'path': str(path.relative_to(ROOT)), 'bytes': len(data),
            'sha256': hashlib.sha256(data).hexdigest(),
            'git_blob': hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()}

def function(path, name, class_name=None):
    tree = ast.parse((ROOT / path).read_text())
    if class_name is not None:
        tree = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name)
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    return {'start_line': node.lineno, 'end_line': node.end_lineno,
            'ast_sha256': hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()}

historical = read(RET + '020/execution/p23-sampling-observer-001/P23.json')
current = read(RET + '035/execution/original28-002/P23/request-result.json')
historical_inputs = read(RET + '020/execution/p23-sampling-observer-001/inputs-before.json')
current_inputs = read(RET + '035/execution/original28-002/inputs-before.json')
historical_files = {row['path']: row for row in historical_inputs['files']}
current_files = {row['path']: row for row in current_inputs['files']}
tree = {row['path']: row for row in json.loads(Path('/workspace/scratch/73029ed6994e/c043-evidence-inputs-tree.json').read_text())}
checks = []

def check(name, result):
    checks.append({'check': name, 'passed': bool(result)})
    if not result:
        raise AssertionError(name)

identities = [identity(p) for p in sorted(ROOT.rglob('*')) if p.is_file()]
for row in identities:
    path = row['path']
    if path in tree:
        check('published blob/size: ' + path,
              (row['bytes'], row['git_blob']) == (tree[path]['size'], tree[path]['sha']))
    if path.startswith('historical-88473124/'):
        original = path.split('/', 1)[1]
        check('historical executed input: ' + path,
              row['sha256'] == historical_files[original]['sha256']
              and row['git_blob'] == historical_files[original]['git_blob_sha1'])
    elif 'source-88473124/' in path:
        original = path.split('source-88473124/', 1)[1]
        check('historical executed input: ' + path,
              row['sha256'] == historical_files[original]['sha256']
              and row['git_blob'] == historical_files[original]['git_blob_sha1'])
    elif path.startswith('ontokin/'):
        check('held executed input: ' + path,
              row['sha256'] == current_files[path]['sha256'].removeprefix('sha256:'))

key = 'reach_recording_fast.py:recording_float_excess'
stats = historical['stats'][key]
scoped = [row for row in historical['scoped_stats'] if row['function'] == key]
charges = [row for row in historical['charge_stats'] if row['function'] == key]
details = [row for row in historical['calls'] if row['function'] == key]
expected = {'recording_float_excess_domain': 32, 'cache_lookup': 32,
            'exact_add': 320, 'exact_mul': 448, 'exact_compare': 64,
            'cache_insert': 32, 'cache_evict': 32}
check('exact historical calls and inclusive/self work', stats == {
    'calls': 32, 'request_operations': 960, 'self_request_operations': 960,
    'reach_operations': 960, 'self_reach_operations': 960})
check('single sampling scope', len(scoped) == 1 and scoped[0]['scope'] == 'recording_sampling')
check('exact attributed charge map', len(charges) == 1 and charges[0]['kinds'] == expected)
check('30 charges each aggregate', sum(expected.values()) == 960 and 960 == 32 * 30)
check('no individual excess records', details == [])
check('no radius charge', historical['work']['counts'].get('recording_cell_radius_domain', 0) == 0)
check('no phase restart', all('restart' not in k for k in historical['work']['counts']))
check('no scalar planar sampler invocation', 'reach_recording_fast.py:_sample_planar_frames' not in historical['stats'])
check('no observer anomalies/unreturned frames', historical['observer_anomalies'] == []
      and historical['unreturned_selected_frames'] == 0 and historical['unreturned_work_charges'] == 0)
first = next(row for row in historical['calls'] if row['function'] == 'reach_recording_capture.py:_CapturedPhase.sample')
check('first captured sample window', (first['call_id'], first['parameters']['time'], first['request_start'], first['request_end'])
      == (459229, '1/26', 79732, 82476) and first['returned_none'] is False)
check('51 captured sample calls', historical['stats']['reach_recording_capture.py:_CapturedPhase.sample']['calls'] == 51)
finish = next(row for row in historical['calls'] if row['function'] == 'reach_recording_capture.py:_CapturedPhase.finish')
check('finish before later failure', finish['request_end'] == 95308
      and historical['operations'] == 100001 and 'work.charge("binary64_round")' in historical['traceback'])
check('historical/current request limits preserved', historical['options'] == current['options']
      and historical['max_operations'] == current['max_operations'] == 100000)
check('current prefix remains failure', current['operations'] == 100001
      and current['work']['operations'] == 80801 and current['status'] == 'failed')
check('current domain occurrences', current['work']['counts']['recording_float_excess_domain'] == 32)

pairs = {}
for name, class_name, current_path, historical_path in [
    ('recording_float_excess', None, 'ontokin/reach_recording_fast.py', RET+'source-88473124/ontokin/reach_recording_fast.py'),
    ('__init__', '_CapturedPhase', 'ontokin/reach_recording_capture.py', 'historical-88473124/ontokin/reach_recording_capture.py'),
    ('sample', '_CapturedPhase', 'ontokin/reach_recording_capture.py', 'historical-88473124/ontokin/reach_recording_capture.py'),
    ('finish', '_CapturedPhase', 'ontokin/reach_recording_capture.py', 'historical-88473124/ontokin/reach_recording_capture.py'),
    ('begin_captured_phase', None, 'ontokin/reach_recording_capture.py', 'historical-88473124/ontokin/reach_recording_capture.py'),
    ('_sample_graph', None, 'ontokin/reach_recording_capture.py', 'historical-88473124/ontokin/reach_recording_capture.py'),
]:
    old = function(historical_path, name, class_name)
    new = function(current_path, name, class_name)
    label = (class_name + '.' if class_name else '') + name
    pairs[label] = {'historical': old, 'current': new, 'ast_equal': old['ast_sha256'] == new['ast_sha256']}
check('target function structurally unchanged', pairs['recording_float_excess']['ast_equal'])
check('captured envelope lifecycle structurally unchanged', all(pairs['_CapturedPhase.' + name]['ast_equal'] for name in ('__init__', 'sample', 'finish')))
check('surrounding sampled graph differs', not pairs['_sample_graph']['ast_equal'])
check('phase source byte-identical', (ROOT/'ontokin/reach_phase.py').read_bytes() == (ROOT/'historical-88473124/ontokin/reach_phase.py').read_bytes())

result = {
    'schema': 'ontokin.checkpoint043-independent-retained-review/0.1',
    'reviewer': '/root/angular_evidence', 'scope': 'static JSON/text/AST review only',
    'published_parent': '00606a16be62631179b50255d4de8daa34f8f196',
    'historical_runtime': historical['source_commit'], 'historical_tree': historical['source_tree'],
    'current_runtime': current_inputs['git']['commit'], 'current_tree': current_inputs['git']['tree'],
    'input_identities': identities, 'checks': checks,
    'historical_sampling': {'stats': stats, 'charge_map': expected, 'individual_entries': len(details),
        'cold_whole_result_calls': 32, 'warm_whole_result_calls': 0,
        'include_cell_radii': False, 'dynamic': False,
        'selector_basis': 'native-source reconciliation of complete attributed charges and captured caller',
        'all_envelopes_completed_during_first_captured_sample': True,
        'first_captured_sample': first, 'exact_angular_and_spatial_values_retained': False,
        'per_bound_path_and_order_retained': False, 'eligible_angular_repeat_count': None},
    'source_comparisons': pairs,
    'current': {'domain_occurrences': 32, 'shared_operations': 100001, 'reach_operations': 80801,
        'status': 'failed', 'cold_warm_sequence': None, 'actual_angular_spatial_tuples': None,
        'eligible_angular_repeat_count': None},
    'missing_datum': 'Ordered current per-call exact angular/spatial tuples, selectors, frame/phase origin, whole-cache membership result/completion, and intervening shared-cache state sufficient to establish eligible repeats and added cache effects.',
    'executed_product_requests': 0, 'runtime_tests': 0, 'numerical_replays': 0,
    'qualification': 'No new product measurement or completed full execution checkout; original failure and historical omitted archives remain unchanged.'
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'checks_passed': len(checks), 'output': str(OUT), 'runtime_imports': 0, 'product_requests': 0}))
