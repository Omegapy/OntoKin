"""Validate C043 source/evidence metadata; never import or execute OntoKin."""
from pathlib import Path
import argparse
import ast
import hashlib
import json

ROOT = Path(__file__).resolve().parents[4]
DOC = Path(__file__).resolve().parent.parent
RET = DOC / 'checkpoint-042-retained'
NEWRET = DOC / 'checkpoint-043-retained/source-88473124'
checks = []

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def check(name, result):
    checks.append({'check': name, 'passed': bool(result)})
    if not result:
        raise AssertionError(name)

def identity(path):
    data = path.read_bytes()
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
            'git_blob': hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()}

def function(path, name, class_name=None):
    tree = ast.parse(path.read_text(encoding='utf-8'))
    if class_name:
        tree = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name)
    return next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)

def ast_hash(node):
    return hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()

def count_ops(node):
    return sum(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'op' for n in ast.walk(node))

def audit():
    binding = read(DOC/'checkpoint-043-source-binding.json')
    census = read(DOC/'checkpoint-043-census.json')
    ledger = read(DOC/'checkpoint-043-cost-ledger.json')
    index = read(DOC/'checkpoint-043-reviews.json')
    evidence = read(DOC/'checkpoint-043-reviews/angular-evidence.json')
    historical = read(RET/'020/execution/p23-sampling-observer-001/P23.json')
    current = read(RET/'035/execution/original28-002/P23/request-result.json')
    old_inventory = {r['path']:r for r in read(RET/'020/execution/p23-sampling-observer-001/inputs-before.json')['files']}
    current_inventory = {r['path']:r for r in read(RET/'035/execution/original28-002/inputs-before.json')['files']}
    check('65 runtime remote identities', len(binding['runtime_blob_mode_comparison']) == 65
          and all(r['parent_blob'] == r['held_blob'] for r in binding['runtime_blob_mode_comparison']))
    for row in binding['selected_inputs']:
        actual = identity(ROOT/row['path'])
        check('selected exact bytes: '+row['path'], all(actual[k] == row[k] for k in actual))
        if row.get('parent_blob'):
            check('parent blob binding: '+row['path'], actual['git_blob'] == row['parent_blob'])
        if row['path'].startswith('ontokin/'):
            expected = current_inventory[row['path']]
            check('held execution inventory: '+row['path'], actual['sha256'] == expected['sha256'].removeprefix('sha256:'))
        if 'source-88473124/' in row['path']:
            original = row['path'].split('source-88473124/',1)[1]
            check('historical inventory: '+original, actual['sha256'] == old_inventory[original]['sha256']
                  and actual['git_blob'] == old_inventory[original]['git_blob_sha1'])
    for review in index['reviews']:
        for row in review['files']:
            actual = identity(ROOT/row['path'])
            check('review exact bytes: '+row['path'], all(actual[k] == row[k] for k in actual))
    check('three independent reviewers', len(index['reviews']) == 3)
    check('retained reviewer audit', len(evidence['checks']) == 41 and all(x['passed'] for x in evidence['checks']))

    old_fast = RET/'source-88473124/ontokin/reach_recording_fast.py'
    cur_fast = ROOT/'ontokin/reach_recording_fast.py'
    target = function(cur_fast,'recording_float_excess')
    check('target original/current AST', ast_hash(target) == ast_hash(function(old_fast,'recording_float_excess')) == binding['target_ast_sha256'])
    counts = {n.targets[0].id:count_ops(n.value) for n in target.body if isinstance(n,ast.Assign)
              and isinstance(n.targets[0],ast.Name) and n.targets[0].id in {'source_leaves','e','g','q','p','rotation_rad'}}
    dynamic = next(n for n in target.body if isinstance(n,ast.If) and isinstance(n.test,ast.Name) and n.test.id == 'dynamic')
    counts['dynamic_p'] = count_ops(dynamic)
    check('actual arithmetic sites', counts == {'source_leaves':1,'e':4,'g':4,'q':4,'p':10,'rotation_rad':1,'dynamic_p':4})
    check('retained cost AST record', counts == read(DOC/'checkpoint-043-reviews/angular-cost-ast.json')['counts'])
    statements = {n.targets[0].id:n for n in target.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name)}
    range_if = next(n for n in target.body if isinstance(n,ast.If) and isinstance(n.test,ast.BoolOp)
                    and isinstance(n.test.op,ast.Or) and '_checked_compare' in ast.unparse(n.test))
    check('prefix/position/range/late order', statements['q'].lineno < statements['p'].lineno < dynamic.lineno < range_if.lineno < statements['rotation_rad'].lineno)
    check('two short-circuit range terms', len(range_if.test.values) == 2 and '_checked_compare(e,' in ast.unparse(range_if.test.values[0])
          and '_checked_compare(q,' in ast.unparse(range_if.test.values[1]))
    warm = next(n for n in target.body if isinstance(n,ast.If) and ast.unparse(n.test) == 'old is not None')
    check('whole warm path unchanged distinction', 'return old' in ast.unparse(warm) and 'guard_bits' not in ast.unparse(warm))
    for comparison in binding['arithmetic_cache_comparisons']:
        name = comparison['name']; file = comparison['file']
        cls = 'ReachExecutionWork' if name in {'charge','lookup','remember'} else None
        old = function(RET/'source-88473124/ontokin'/file,name,cls)
        new = function(ROOT/'ontokin'/file,name,cls)
        check('old/current arithmetic/cache applicability: '+name,
              ast_hash(old) == comparison['historical']['ast_sha256'] and ast_hash(new) == comparison['current']['ast_sha256']
              and (ast_hash(old) == ast_hash(new)) == comparison['ast_identical'])
    for name, cls in [('__init__','_CapturedPhase'),('sample','_CapturedPhase'),('finish','_CapturedPhase'),('begin_captured_phase',None),('_sample_graph',None)]:
        old = function(NEWRET/'ontokin/reach_recording_capture.py',name,cls)
        new = function(ROOT/'ontokin/reach_recording_capture.py',name,cls)
        label = (cls+'.' if cls else '')+name
        relation = binding['function_comparisons'][label]
        check('captured source applicability: '+label, ast_hash(old) == relation['historical']['ast_sha256']
              and ast_hash(new) == relation['current']['ast_sha256'] and (ast_hash(old) == ast_hash(new)) == relation['ast_equal'])
    check('complete phase source equal', (NEWRET/'ontokin/reach_phase.py').read_bytes() == (ROOT/'ontokin/reach_phase.py').read_bytes())

    key='reach_recording_fast.py:recording_float_excess'
    expected={'recording_float_excess_domain':32,'cache_lookup':32,'exact_add':320,'exact_mul':448,'exact_compare':64,'cache_insert':32,'cache_evict':32}
    charge_rows=[r for r in historical['charge_stats']if r['function']==key]
    scoped=[r for r in historical['scoped_stats']if r['function']==key]
    check('exact original aggregate', historical['stats'][key] == {'calls':32,'request_operations':960,'self_request_operations':960,'reach_operations':960,'self_reach_operations':960})
    check('single sampling charge row', len(charge_rows)==1 and charge_rows[0]['kinds']==expected and len(scoped)==1 and scoped[0]['scope']=='recording_sampling')
    check('960 reconciles', sum(expected.values())==32*(1+1+10+14+2+1+1)==960)
    check('no individual envelope inputs', not [r for r in historical['calls']if r['function']==key])
    check('no selected radius or dynamic extras', historical['work']['counts'].get('recording_cell_radius_domain',0)==0
          and expected['exact_add']==32*10 and expected['exact_mul']==32*14)
    first=next(r for r in historical['calls']if r['function']=='reach_recording_capture.py:_CapturedPhase.sample')
    check('first sample exact origin', (first['call_id'],first['parameters']['time'],first['request_start'],first['request_end'],first['returned_none'])==(459229,'1/26',79732,82476,False))
    check('51 completed sample calls', historical['stats']['reach_recording_capture.py:_CapturedPhase.sample']['calls']==51)
    finish=next(r for r in historical['calls']if r['function']=='reach_recording_capture.py:_CapturedPhase.finish')
    check('phase finish and later original refusal', finish['request_end']==95308 and 'work.charge("binary64_round")' in historical['traceback'])
    check('no observation anomalies/restart', historical['observer_anomalies']==[] and historical['unreturned_selected_frames']==0
          and historical['unreturned_work_charges']==0 and all('restart'not in k for k in historical['work']['counts']))
    check('no scalar sampler substitution', 'reach_recording_fast.py:_sample_planar_frames' not in historical['stats'])
    check('original requests/caps match', historical['options']==current['options'] and historical['max_operations']==current['max_operations']==100000)
    check('failures and current domains retained', historical['operations']==current['operations']==100001 and current['work']['operations']==80801
          and current['status']=='failed' and current['work']['counts']['recording_float_excess_domain']==32)
    check('census historic record binding', census['historical']==evidence['historical_sampling'])
    check('census current uncertainty retained', census['actual_current_repeats'] is None and census['current']['cold_warm_sequence'] is None)
    check('counterexample baseline partition', sum(ledger['original_empty_cache_charge_partition'].values())==29)
    check('closed singleton and sequence ledger', [(r['original'],r['candidate_lower_bound'],r['saving_upper_bound'])for r in ledger['counterexamples']]==[(29,31,-2),(30,33,-3),(29*32,31*32,-2*32)])
    check('counterexample cache capacity/ranges', ledger['counterexamples'][2]['candidate_keys']==64<=256
          and ledger['counterexamples'][2]['max_e_power_of_two']==-41 < -6
          and ledger['counterexamples'][2]['max_q_power_of_two']==-37 < -6)
    check('conditional quantities remain unproved', ledger['r13'] is None and ledger['r1'] is None and ledger['Delta_other_sign'] is None
          and not ledger['positive_complete_bound_established'] and not ledger['runtime_scope_selected'])
    nextscope=read(DOC/'checkpoint-043-next-scope.json')
    check('next request unchanged', nextscope['original_request']=={'case':'P23','end':'3','fps':1,'helpers':False,'position_tolerance':0.001,'rotation_tolerance':0.001,'time_tolerance':0.000001})
    check('next caps unchanged', nextscope['caps']=={'shared_operations':100000,'elapsed_ms':30000,'operand_bits':32768,'numerical_cache_entries':256,'category_metadata_entries':512})
    return {'schema':'ontokin.checkpoint043-static-audit/0.1','status':'passed','checks_passed':len(checks),'checks':checks,
            'product_imports':0,'product_requests':0,'runtime_tests':0,'numerical_replays':0,
            'scope':'exact bytes, source ASTs, retained JSON, algebraic ledger metadata and preserved uncertainty; no product execution'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    result=audit()
    text=json.dumps(result,indent=2)+'\n'
    if args.output: args.output.write_text(text)
    print(text,end='')
