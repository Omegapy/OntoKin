"""Metadata-only C056 audit. Never imports or executes OntoKin product code."""
from pathlib import Path
import hashlib
import json
import sys

HERE=Path(__file__).resolve().parent
EVIDENCE=HERE.parent
ROOT=HERE.parents[3]
CHECKS=[]

def read(p): return json.loads(p.read_text())
def blob(b): return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def check(name, condition, detail):
    CHECKS.append({'check':name,'passed':bool(condition),'detail':detail})
def matches(row, p):
    b=p.read_bytes()
    return len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256'] and ('git_blob' not in row or blob(b)==row['git_blob'])

tree=read(HERE/'parent-tree.json')
entries={e['path']:e for e in tree['tree'] if e['type']=='blob'}
branches={}
for p,e in entries.items():
    d=branches
    parts=p.split('/')
    for part in parts[:-1]: d=d.setdefault(part,{})
    d[parts[-1]]=(e['mode'],e['sha'])
def treehash(d):
    records=[]
    for name,v in d.items():
        if isinstance(v,dict): mode,sha,key='40000',treehash(v),(name+'/').encode()
        else: mode,sha=v;key=name.encode()
        records.append((key,mode.encode()+b' '+name.encode()+b'\0'+bytes.fromhex(sha)))
    b=b''.join(r for _,r in sorted(records))
    return hashlib.sha1(b'tree '+str(len(b)).encode()+b'\0'+b).hexdigest()
check('complete_parent_tree',not tree['truncated'] and len(entries)==3009 and treehash(branches)==tree['sha']=='5282f90bc12c321c67829ce6d7ce62c891b32424','Complete immutable tree reconstructed from all blob paths/modes.')
recovered=read(HERE/'recovered-inputs.json')
bad=[]
for r in recovered['inputs']:
    if not matches(r,ROOT/r['path']) or entries[r['path']]['sha']!=r['git_blob'] or entries[r['path']]['size']!=r['bytes']: bad.append(r['path'])
check('all_materialized_originals',not bad and len(recovered['inputs'])==955 and sum(r['bytes'] for r in recovered['inputs'])==121864778,{'mismatches':bad,'files':955,'bytes':121864778})
local_originals={r['path'] for r in recovered['inputs']}
check('complete_document_and_runtime_coverage',all(p in local_originals for p in entries if p.endswith(('.md','.html')) or p.startswith('ontokin/')),'All250 original Markdown/HTML and65 runtime files materialized; complete checkout not claimed.')
binding=read(EVIDENCE/'checkpoint-056-source-binding.json')
check('primary_source_bindings',all(matches(r,ROOT/r['path']) for r in binding['primary_inputs']),'Fourteen primary source/governance/checker files match their hashes.')
check('distinct_main_status',blob((HERE/'main-STATUS.txt').read_bytes())==binding['main_status_blob']=='bad53fefb2c7ab2901a59a9d5484a6d703709571','Main STATUS preserved separately from continuation STATUS.')
held=read(HERE/'held-runtime-mode-binding.json')
check('held_runtime_blobs_and_modes',len(held['files'])==65 and all(r['current']==r['held']==entries[r['path']]['sha'] and r['current_mode']==r['held_mode']==entries[r['path']]['mode'] for r in held['files']),'Complete supplied remote comparison retains each current/held blob and mode.')
start=read(HERE/'startup.json')
check('startup_and_explicit_release',len(start['branches'])==101 and len(start['pull_requests'])==31 and start['explicit_predecessor_release']['id']==6454923162 and start['pr52']['head_sha']==recovered['source_commit'] and start['new_scope_comment']==6455640385,'Ownership derives from explicit release, not expiry; isolated scope retained.')
new=[]
for p in ROOT.rglob('*'):
    if not p.is_file() or '__pycache__' in p.parts: continue
    rel=p.relative_to(ROOT).as_posix()
    if rel not in entries: new.append(rel)
prefix=EVIDENCE.relative_to(ROOT).as_posix()+'/'
check('only_owned_additions',all(p==prefix+'HANDOFF-056.md' or p.startswith(prefix+'checkpoint-056') for p in new),{'new_files':len(new),'prior_file_mutations':bad})
schedule=read(EVIDENCE/'checkpoint-056-schedule.json')
ledger=read(EVIDENCE/'checkpoint-056-cost-ledger.json')
check('exact_frozen_schedule',schedule['schedule_id']=='R56-first-term-read-compare-repay' and [w['id'] for w in schedule['witnesses']]==['W1-new-comparison-charge','W2-rejected-repayment','W3-lowered-remaining-budget'] and schedule['seam']['source_lines']=={'exact':[126,145],'atan':[370,387],'pi':[389,395]},'Corrected exact source ranges and three unexecuted source witnesses retained.')
check('conditional_cost_seams',ledger['inherited_structural_counts']['whole_pi_factory']==163 and ledger['seams']['after_completed_square']['unexecuted_original_operations_d5']==114 and ledger['seams']['after_first_term_tick_U']['original_future_charge_units_d5']==113 and ledger['seams']['after_first_term_tick_U']['original_future_charge_units_d239']==33 and ledger['complete_gate_cost'] is None and ledger['whole_request_saving'] is None,'No double funding, complete gate cost or whole-request saving invented.')
index=read(EVIDENCE/'checkpoint-056-reviews.json')
review_bad=[]
for item in index['final_core_audits']:
    path=EVIDENCE/item['final_audit']
    if not matches(item,path): review_bad.append(str(path))
    review=read(path)
    rows=review.get('core_inputs',review.get('inputs',[]))
    core=[r for r in rows if Path(r['path']).name in {'HANDOFF-056.md','checkpoint-056-atan-bootstrap-feasibility.md','checkpoint-056-schedule.json','checkpoint-056-cost-ledger.json','checkpoint-056-next-scope.json'}]
    if len(core)!=5 or not all(matches(r,ROOT/r['path']) for r in core):review_bad.append(item['role'])
check('independent_final_review_bindings',len(index['final_core_audits'])==3 and not review_bad and index['unresolved_findings']==0,{'mismatches':review_bad,'checks':index['substantive_checks']})
next_scope=read(EVIDENCE/'checkpoint-056-next-scope.json')
check('bounded_next_scope',next_scope['next_checkpoint']=='C057' and '_CertificateFieldComparisons.compare' in next_scope['comparison_baseline']['primary_site'] and next_scope['release']['original28']=='24/28 historical' and next_scope['release']['open']==['P11','P16','P23','L03'] and next_scope['release']['full_product_goal_completed'] is False,'One existing admission audit; no implementation or semantic redefinition selected.')
first=(HERE/'recovery-attempt001-results.jsonl').read_bytes();both=(HERE/'recovery-results.jsonl').read_bytes()
check('preserved_failed_transport',both.startswith(first) and len(first.splitlines())==955 and len(both.splitlines())==1910 and not (ROOT.parent/'c056-preparation/temporary-transport.json').exists(),'Failed943 remote reads preserved in first attempt; later955 matches distinct; signed URLs removed.')
check('unchanged_documentation_checker',blob((ROOT/'docs/maintenance/reorganization-2026-10-17/verify_reorganization.py').read_bytes())=='25e4c5a224cbe15bbeba9a7e35301de4368d3de7','Required checker remains exact original; no product module imported.')
out={'schema':'ontokin.checkpoint056-metadata-result/0.1','status':'passed' if all(c['passed'] for c in CHECKS) else 'failed','grouped_checks':len(CHECKS),'checks':CHECKS,'product_imports':0,'numerical_execution':False}
print(json.dumps(out,indent=2))
raise SystemExit(out['status']!='passed')
