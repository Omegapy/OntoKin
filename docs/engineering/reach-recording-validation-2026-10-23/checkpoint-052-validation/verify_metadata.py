"""Verify C052 file identity, review bindings and source-ledger metadata only.

This script does not import OntoKin or execute a numerical candidate or request.
Run after source reviews finish. It is not a runtime or release-conformance gate.
"""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[4]
D = Path(__file__).resolve().parents[1]
V = Path(__file__).resolve().parent
failures = []
checks = []

def j(path):
    return json.loads(path.read_text())

def record(path):
    data = path.read_bytes()
    return len(data), hashlib.sha256(data).hexdigest(), hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()

def check(name, condition, **details):
    checks.append({'check': name, 'passed': bool(condition), **details})
    if not condition:
        failures.append(name)

source = j(V/'recovered-inputs.json')
bad = []
for row in source['files']:
    path = ROOT/row['path']
    if not path.is_file() or record(path) != (row['bytes'], row['sha256'], row['git_blob']):
        bad.append(row['path'])
check('recovered_parent_bytes_preserved', not bad and len(source['files']) == 1042,
      input_count=len(source['files']), bytes=sum(x['bytes'] for x in source['files']), mismatches=bad)
held = j(V/'held-runtime-binding.json')
check('held_runtime_unchanged', len(held['files']) == 65 and all(x['matched'] and x['c051_blob']==x['held_c035_blob'] for x in held['files']), modules=len(held['files']))
base_paths = {x['path'] for x in source['files']}
new = [p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file() and p.relative_to(ROOT).as_posix() not in base_paths]
prefix = 'docs/engineering/reach-recording-validation-2026-10-23/'
check('all_new_files_in_c052_scope', all(p.startswith(prefix) and (p[len(prefix):].startswith('checkpoint-052') or p[len(prefix):]=='HANDOFF-052.md') for p in new), new_files=len(new))
ledger=j(D/'checkpoint-052-cost-ledger.json')
pi=ledger['native128_pi']; case=ledger['manual_source_case']; scan=ledger['R2']
check('source_ledger_bookkeeping', sum(pi['cold_components'].values())==pi['cold']==165 and pi['cold']-pi['authentic_eligible_hit']==pi['gross']==164 and case['common_prefix']+case['fresh_body']==case['original']==211 and case['common_prefix']+case['hit_body']==case['reuse_before_admission']==47 and case['original']-case['reuse_before_admission']==164 and scan['at_full_256']==164-256==-92 and pi['constructor_tick_saving']==0)
check('complete_request_unknowns_preserved', all(ledger['whole_request'][x] is None for x in ('H_value','A_total_value','Delta_later_value','complete_saving','elapsed_saving')) and ledger['whole_request']['failed_tail_completed'] is False and ledger['runtime_execution'] is False)
scope=j(D/'checkpoint-052-next-scope.json'); checkpoint=j(D/'checkpoint-052.json'); validation=j(D/'checkpoint-052-validation.json')
check('source_scope_and_release_limits', not checkpoint['implementation_selected'] and not checkpoint['runtime_changes'] and not checkpoint['main_merged'] and not checkpoint['full_product_goal_completed'] and checkpoint['original28']=={'passed':24,'total':28,'new_execution':False} and not scope['incidence_if_survives']['product_execution_authorized_by_this_record'] and all(v==0 for v in validation['runtime'].values()) and ledger['preserved_limits']=={'operations':100000,'elapsed_ms':30000,'operand_bits':32768,'cache_entries':256,'cursor_updates':64})
review_index=j(D/'checkpoint-052-reviews.json')
missing=[]
for entry in review_index['reviews']:
    for key in ('review','result','inputs','final_draft_review'):
        if key in entry and not (D/entry[key]).is_file(): missing.append(entry[key])
check('independent_review_members_present', len(review_index['reviews'])==3 and not missing, missing=missing)
core_names=['checkpoint-052-canonical-arithmetic-feasibility.md','HANDOFF-052.md','checkpoint-052-cost-ledger.json','checkpoint-052-next-scope.json']
check('required_core_files_nonempty', all((D/n).is_file() and (D/n).stat().st_size>0 for n in core_names))
check('unchanged_documentation_checker', record(ROOT/'docs/maintenance/reorganization-2026-10-17/verify_reorganization.py')[2]=='25e4c5a224cbe15bbeba9a7e35301de4368d3de7')
result={'schema':'ontokin.checkpoint052-metadata-result/0.1','status':'passed' if not failures else 'failed','scope':'file identity, scoped additions, review membership and source-ledger metadata; no product execution','grouped_checks':len(checks),'checks':checks,'failures':failures}
print(json.dumps(result,indent=2))
sys.exit(1 if failures else 0)
