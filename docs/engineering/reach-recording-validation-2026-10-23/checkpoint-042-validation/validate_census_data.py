"""Validate C042 source identities and retained data without importing OntoKin.

This reads old reports, manifests, source text and abstract syntax trees. It is
not a product request, recording replay, numerical probe or runtime test suite.
"""
import ast
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
DOC = HERE.parent
ROOT = HERE.parents[3]
RAW = DOC / 'checkpoint-042-retained'
checks = []


def check(name, condition):
    checks.append({'name': name, 'passed': bool(condition)})
    if not condition:
        raise AssertionError(name)


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def function(path, qualified_name):
    node = ast.parse(path.read_text())
    for part in qualified_name.split('.'):
        node = next(x for x in node.body if isinstance(x, (ast.ClassDef, ast.FunctionDef)) and x.name == part)
    return node


def signature(node):
    return ast.dump(node, include_attributes=False)


def complete_tree_hash(entries):
    nested = {}
    for row in entries:
        if row['type'] == 'tree':
            continue
        parts = row['path'].split('/')
        cursor = nested
        for part in parts[:-1]:
            cursor = cursor.setdefault(part, {})
        cursor[parts[-1]] = (row['mode'], row['sha'])

    def pack(branch):
        rows = []
        for name, value in branch.items():
            if isinstance(value, dict):
                mode, digest, sort_key = '40000', pack(value), (name + '/').encode()
            else:
                mode, digest = value
                sort_key = name.encode()
            rows.append((sort_key, mode.encode() + b' ' + name.encode() + b'\0' + bytes.fromhex(digest)))
        data = b''.join(v for _, v in sorted(rows))
        return hashlib.sha1(b'tree ' + str(len(data)).encode() + b'\0' + data).hexdigest()

    return pack(nested)


def main():
    parent = read(HERE / 'parent-tree.json')
    binding = read(DOC / 'checkpoint-042-source-binding.json')
    entries = {x['path']: x for x in parent['tree'] if x['type'] == 'blob'}
    check('complete_parent_metadata_reconstructs_exact_tree', complete_tree_hash(parent['tree']) == binding['parent_tree'])
    check('parent_file_count', len(entries) == binding['parent_file_count'] == 2172)
    for row in binding['focused_inputs']:
        data = (ROOT / row['path']).read_bytes()
        check('focused_source:' + row['path'], len(data) == row['bytes'] and hashlib.sha256(data).hexdigest() == row['sha256'] and git_blob(data) == row['git_blob'] == entries[row['path']]['sha'])

    manifests = {c: {x['path']: x for x in read(DOC / ('checkpoint-' + c + '-manifest.json'))['members']} for c in ['020','035']}
    index = read(RAW / 'index.json')
    for row in index['records']:
        path = DOC / row['path']; data = path.read_bytes()
        check('retained_copy:' + row['path'], len(data) == row['bytes'] and hashlib.sha256(data).hexdigest() == row['sha256'] and git_blob(data) == row['git_blob'])
        if 'member' in row:
            expected = manifests[row['checkpoint']][row['member']]
            check('original_manifest:' + row['member'], row['bytes'] == expected['bytes'] and row['sha256'] == expected['sha256'])

    old_dir = RAW / '020/execution/p23-sampling-observer-001'
    current_dir = RAW / '035/execution/original28-002'
    check('C020_inventory_stable', (old_dir/'inputs-before.json').read_bytes() == (old_dir/'inputs-after.json').read_bytes())
    check('C035_inventory_stable', (current_dir/'inputs-before.json').read_bytes() == (current_dir/'inputs-after.json').read_bytes())
    old_inventory = read(old_dir/'inputs-before.json')
    new_inventory = read(current_dir/'inputs-before.json')
    old_files = {x['path']:x for x in old_inventory['files']}
    new_files = {x['path']:x for x in new_inventory['files']}
    check('C020_runtime_identity', old_inventory['git_commit'] == '88473124cc058f7e2926a04d79ab38e340ab4407' and old_inventory['git_tree'] == '02efa05c691ff31258e39c16b98044d2a47fda20')
    for row in binding['historical_source_bindings']:
        old = RAW / 'source-88473124' / row['path']
        current = ROOT / row['path']
        check('old_executed_source:' + row['path'], sha(old) == row['C020_sha256'] == old_files[row['path']]['sha256'])
        check('current_executed_source:' + row['path'], sha(current) == row['C035_C041_sha256'] == new_files[row['path']]['sha256'].removeprefix('sha256:'))
    runtime = binding['runtime_file_identity_comparison']['entries']
    check('all_65_current_runtime_blobs', len(runtime) == 65 and all(entries[x['path']]['sha'] == x['git_blob'] and entries[x['path']]['mode'] == x['mode'] and new_files[x['path']]['bytes'] == entries[x['path']]['size'] for x in runtime))

    census = read(DOC / 'checkpoint-042-census.json')
    for name, expected in census['function_ast_comparisons'].items():
        filename, qualified_name = name.split(':',1)
        old_node = function(RAW/'source-88473124/ontokin'/filename, qualified_name)
        current_node = function(ROOT/'ontokin'/filename, qualified_name)
        check('AST_applicability:' + name, (signature(old_node) == signature(current_node)) == expected['ast_equal'])

    old = read(old_dir/'P23.json'); current = read(current_dir/'P23/request-result.json'); report = read(current_dir/'report.json')
    fn = 'reach_runtime.py:ReachSimulator._constant_pose'
    stats = {x['scope']: x for x in old['scoped_stats'] if x['function'] == fn}
    charge = {x['scope']: x for x in old['charge_stats'] if x['function'] == fn}
    kinds = charge['recording_sampling']['kinds']
    n = stats['recording_sampling']['calls']; m = kinds['pose_stationary_check']
    check('historical_sampling_calls_and_constructors', (n,m) == (192,62))
    check('historical_sampling_outer_hits', n-m == 130)
    check('historical_sampling_no_inverse_lookup', kinds['cache_lookup']-n-2*m == 0)
    check('historical_sampling_no_cold_rotation', kinds.get('quaternion_rescale',0) == 0 and kinds.get('pose_rotation_reference',0) == 0)
    check('historical_sampling_no_stationary_hit', kinds['cache_promote']-(n-m)-m == 0)
    check('historical_sampling_insert_eviction', kinds['cache_insert'] == kinds['cache_evict'] == 2*m)
    check('historical_sampling_vector_scalar_reconciliation', kinds['pose_vector_domain'] == 4*m and kinds['exact_decode'] == kinds['binary64_decode'] == 7*m)
    check('historical_sampling_total', sum(kinds.values()) == charge['recording_sampling']['reach_operations'] == stats['recording_sampling']['self_reach_operations'] == 1934)
    check('historical_sampling_three_charge_target', 3*m == 186)
    p = charge['advance:0:before']['kinds']; pn = stats['advance:0:before']['calls']; pm = p['pose_stationary_check']
    check('historical_planning_partition', (pn,pm,pn-pm,p['cache_lookup']-pn-2*pm,p['cache_promote']-(pn-pm)-pm) == (40,34,6,1,2))
    check('historical_planning_computed_inverse', p['quaternion_conjugate'] == p['pose_position_negate'] == 3 and p['cache_insert'] == 34+32+1)
    check('historical_other_scopes_warm', all(stats[s]['calls'] == 3 and charge[s]['kinds'] == {'cache_lookup':3,'cache_promote':3} for s in ['advance:0:after','advance:2:before']))
    check('historical_export_call_total', sum(x['calls'] for x in stats.values()) == 238)
    check('observer_neutrality_recorded', all(old[k] is True for k in ['matches_unobserved_work','matches_unobserved_diagnostic','matches_unobserved_operations','matches_unobserved_status','self_request_reconciles','self_reach_reconciles']) and not old['observer_anomalies'] and old['unreturned_selected_frames'] == old['unreturned_work_charges'] == 0)
    options = {'end':'3','fps':1,'helpers':False,'position_tolerance_m':0.001,'rotation_tolerance_rad':0.001,'time_tolerance_s':1e-6}
    check('original_request_options', old['options'] == current['options'] == options)
    check('both_original_failures_preserved', old['status'] == current['status'] == 'failed' and old['operations'] == current['operations'] == 100001 and old['max_operations'] == current['max_operations'] == 100000)
    check('current_report_identity', report['source_commit'] == binding['held_runtime_commit'] and report['source_tree'] == binding['held_runtime_tree'] and report['inputs_stable'] is True)
    check('current_refusal_counters', current['work']['operations'] == 80801 and current['work']['counts']['pose_stationary_check'] == 103 and current['work']['counts']['cache_lookup'] == 5053)
    check('current_refusal_before_membership', 'result = self.work.lookup(key)' in current['traceback'] and 'self.charge("cache_lookup")' in current['traceback'] and 'self.external_check()' in current['traceback'])
    check('current_ceiling_only', census['current_retained']['outer_calls'] is None and census['current_retained']['gross_completed_prefix_ceiling'] == 3*103 == 309)

    ef = 'reach_recording_fast.py:recording_float_excess'
    es = next(x for x in old['scoped_stats'] if x['function']==ef and x['scope']=='recording_sampling')
    ec = next(x for x in old['charge_stats'] if x['function']==ef and x['scope']=='recording_sampling')['kinds']
    check('historical_excess_cold_and_cost', es['calls']==32 and sum(ec.values())==es['request_operations']==960 and ec['cache_lookup']==ec['cache_insert']==ec['cache_evict']==32 and ec.get('cache_promote',0)==0)
    check('no_individual_excess_calls_retained', not any(x['function']==ef for x in old['calls']))
    ef_node = function(ROOT/'ontokin/reach_recording_fast.py','recording_float_excess')
    site_counts = {}
    for node in ef_node.body:
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
            site_counts[node.targets[0].id]=sum(isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='op' for x in ast.walk(node.value))
    check('common_arithmetic_sites', {k:site_counts[k] for k in ['source_leaves','e','g','q','rotation_rad']} == {'source_leaves':1,'e':4,'g':4,'q':4,'rotation_rad':1})
    check('position_arithmetic_sites_separate', site_counts['p']==10)
    check('current_excess_occurrences_only', current['work']['counts']['recording_float_excess_domain']==32 and census['larger_target_historical']['current_repeat_key_cardinality'] is None)
    check('full_product_unchanged', not report['release_acceptance'] and not report['full_product_goal_completed'])


if __name__ == '__main__':
    error = None
    try:
        main()
    except Exception as exc:
        error = {'type': type(exc).__name__, 'message': str(exc)}
    result = {'schema':'ontokin.checkpoint042-data-validation/0.1', 'status':'failed' if error else 'passed',
              'scope':'retained data, source identities, AST and accounting only', 'checks_passed':sum(x['passed'] for x in checks),
              'checks':checks, 'error':error, 'product_requests':0, 'runtime_tests':0, 'numerical_replays':0}
    print(json.dumps(result,indent=2))
    sys.exit(1 if error else 0)
