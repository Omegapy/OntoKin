"""C055 source/evidence metadata check. Does not import or execute OntoKin."""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path

EVIDENCE = Path(__file__).resolve().parents[1]
ROOT = EVIDENCE.parents[2]
checks = []

def read(name):
    return json.loads((EVIDENCE / name).read_text())

def check(name, condition, details=None):
    checks.append({'name': name, 'passed': bool(condition), 'details': details})

def digest(path):
    data = path.read_bytes()
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'git_blob': hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()}

schedule = read('checkpoint-055-schedule.json')
ledger = read('checkpoint-055-cost-ledger.json')
scope = read('checkpoint-055-next-scope.json')
binding = read('checkpoint-055-source-binding.json')
reviews = read('checkpoint-055-reviews.json')
coverage = read('checkpoint-055-validation/recovered-inputs.json')
startup = read('checkpoint-055-validation/startup.json')

check('fixed_source_identity', all(x.get('source_commit', x.get('source_basis_commit')) == binding['source_commit'] for x in [schedule, ledger, scope]) and binding['source_commit'] == '2aca5afb05a0320971ccaf9d9ce30904d120e249' and binding['source_tree'] == '7082ceb840e0ce4c2f30baccbdb527913e9fa2ca')
check('scoped_rejections_no_unsupported_gate', all(schedule[k]['result'].startswith('NO-GO') for k in ['G0','G1','G2']) and schedule['complete_gate_cost'] is None and schedule['complete_authority_proof'] is False)
components = sum(x['charges'] for x in ledger['conditional_factory_components'])
check('conditional_cost_and_no_double_funding', components == 163 and ledger['native_opportunity']['factory_room'] == 163 and ledger['native_opportunity']['lookup_retained'] == 1 and ledger['native_opportunity']['remember_retained'] == 1 and ledger['post_square_suffix']['d5_conditional_room'] == 114 and ledger['post_square_suffix']['d239_conditional_room'] == 34 and ledger['post_square_suffix']['prefix_may_not_be_spent_twice'] and ledger['gate']['full_cost'] is None and ledger['gate']['numeric_cost_rejection_claimed'] is False and ledger['strict_stop_and_endpoint_proof_performed'] is False)
check('next_scope_has_bootstrap_before_numerics', scope['next_checkpoint']=='C056' and scope['first_required_output']['kind']=='explicit source-level event and funding state machine' and scope['cost']['no_free_existing_checkpoint'] and scope['cost']['complete_gate_cost'] is None and len(scope['stop_rules'])==4)

expected_release={'original28':'24/28 historical','open':['P11','P16','P23','L03'],'C035':'held including adverse timing','full_product_goal_completed':False}
check('historical_gate_and_exclusions_preserved', all(x['release']==expected_release for x in [schedule,ledger,scope]) and all(schedule[k] is False for k in ['runtime_implementation_selected','numerical_generation_selected','collector_selected']))

problems=[]
for item in coverage['inputs']:
    p=ROOT/item['path']
    if not p.is_file(): problems.append({'path':item['path'],'reason':'missing'});continue
    d=digest(p)
    if any(d[k]!=item[k] for k in ['bytes','sha256','git_blob']):problems.append({'path':item['path'],'reason':'changed original'})
check('all_materialized_originals_exact', not problems and len(coverage['inputs'])==861 and sum(x['bytes'] for x in coverage['inputs'])==119489918, problems)

review_problems=[]
core=set(['checkpoint-055-cold-pi-feasibility.md','checkpoint-055-schedule.json','checkpoint-055-cost-ledger.json','checkpoint-055-next-scope.json','HANDOFF-055.md'])
for review in reviews['final_core_audits']:
    final=EVIDENCE/review['final_audit']
    if digest(final)['sha256']!=review['sha256']:review_problems.append('final audit hash '+review['role'])
    seen=set()
    for item in review['inputs']:
        name=Path(item['path']).name;seen.add(name)
        d=digest(EVIDENCE/name)
        if any(d[k]!=item[k] for k in ['bytes','sha256','git_blob']):review_problems.append(name+' '+review['role'])
    if seen!=core:review_problems.append('five core set '+review['role'])
    if review['unresolved_findings']!=0 or not review['paused']:review_problems.append('unresolved/unpaused '+review['role'])
check('all_final_reviews_bind_same_five_files',not review_problems and len(reviews['final_core_audits'])==3,review_problems)

parsed=ast.parse((ROOT/'ontokin/reach_reference.py').read_text())
arith=next(n for n in parsed.body if isinstance(n,ast.ClassDef) and n.name=='_Arithmetic')
names={n.name for n in arith.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
declared={n.removesuffix('.fget') for n in schedule['native_used_slice']['arithmetic_callables']}
check('used_arithmetic_names_exist_without_import',len(declared)==14 and declared<=names)

checker=ROOT/'docs/maintenance/reorganization-2026-10-17/verify_reorganization.py'
check('documentation_checker_unchanged',digest(checker)['git_blob']=='25e4c5a224cbe15bbeba9a7e35301de4368d3de7')
held=read('checkpoint-055-validation/held-runtime-binding.json')
check('remote_runtime_binding_separate_from_local_coverage',held['runtime_modules']==65 and held['held_runtime_modules']==65 and held['mismatches']==[] and binding['snapshot']['full_checkout'] is False and binding['snapshot']['local_runtime_modules']==20)
check('startup_explicit_release_and_owned_parent',startup['last_issue_comment']['id']==6454287406 and startup['new_branch']['object']['sha']==binding['source_commit'] and startup['new_scope']['id']==6454605895 and startup['main_commit']=='2bb4588e121fcfe99b4d42c734b15b38362f3642' and len(startup['branches'])==100 and len(startup['open_prs'])==30)

result={'schema':'ontokin.checkpoint055-metadata-result/0.1','passed':all(x['passed'] for x in checks),'grouped_checks':len(checks),'checks':checks,'product_execution':False,'endpoint_computation':False}
print(json.dumps(result,indent=2))
raise SystemExit(0 if result['passed'] else 1)
