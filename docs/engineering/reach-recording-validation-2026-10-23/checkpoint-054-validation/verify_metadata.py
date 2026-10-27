"""Audit C054 document identities and declared source bounds; no product execution."""
from pathlib import Path
import ast, hashlib, json

ROOT=Path(__file__).resolve().parents[4]
AREA=Path(__file__).resolve().parents[1]
V=Path(__file__).resolve().parent
checks=[]

def read(p): return json.loads(p.read_text())

def identity(p):
    b=p.read_bytes()
    return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'git_blob':hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()}

def check(name,condition,detail):
    checks.append({'name':name,'status':'passed' if condition else 'failed','detail':detail})

source=read(AREA/'checkpoint-054-source-binding.json')
manifest=read(V/'recovered-inputs.json')
errors=[]
for row in manifest:
    actual=identity(ROOT/row['path'])
    if any(actual[k]!=row[k] for k in ('bytes','sha256','git_blob')): errors.append(row['path'])
check('exact_parent_snapshot',not errors and len(manifest)==851 and sum(x['bytes'] for x in manifest)==119372542,{'files':len(manifest),'bytes':sum(x['bytes'] for x in manifest),'mismatches':errors})
check('coverage_and_limits',len([x for x in manifest if x['path'].endswith(('.md','.html'))])==238 and len([x for x in manifest if x['path'].startswith('ontokin/')])==21 and not source['full_checkout'] and not source['archive_internal_audit'],'238 parent documents;21 local runtime modules; partial snapshot and no internal archive audit')
held=read(V/'held-runtime-binding.json')
check('complete_remote_runtime_binding',held['tree']=='87c949b238055af1ce368c694e1d5683c8aeacde' and held['module_count']==65 and held['all_match'] and all(x['sha']==x['held_sha'] for x in held['files']),'65 complete remote runtime blobs agree with held C035; this is separate from local coverage')
attachments=read(V/'attachment-audit.json')['files']
check('attached_evidence',len(attachments)==5 and all(x['matches_supplied_readback'] and x['matches_parent_recovery'] for x in attachments),'five supplied source evidence files agree with uploaded readback and immutable parent bytes')
schedule=read(AREA/'checkpoint-054-schedule.json'); ledger=read(AREA/'checkpoint-054-cost-ledger.json')
d=schedule['D36']; names=d['callables']
check('D36_arithmetic_and_scope',len(names)==len(set(names))==36 and len(d['predicates'])==5 and d['minimum_predicates']==36*5==180 and ledger['D36']['one_convergent_publication_ceiling_before_all_other_work']==163-180 and ledger['D36']['ceiling_including_one_entry_discriminator']==163-180-1 and ledger['D36']['full_gate_cost'] is None and not ledger['D36']['complete_safe_gate'],'one selected36x5 screen; scoped-17/-18 ceilings; unknown complete safety/cost retained')
tree=ast.parse((ROOT/'ontokin/reach_reference.py').read_text())
ar=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='_Arithmetic')
defs={x.name for x in ar.body if isinstance(x,ast.FunctionDef)}
requested=[x.split('.',1)[1].removesuffix('.fget') for x in names if x.startswith('_Arithmetic.')]
check('arithmetic_inventory_source',len(requested)==19 and set(requested)<=defs,'AST-only binding of19 named original arithmetic definitions; no imports')
t=ledger['tag_screens']
check('tag_screen_formulas',t['T1']['per_key']==4 and t['T2']['per_key']==6 and 8*20<163<8*21 and 12*13<163<12*14 and t['T1']['stable_sufficient_nonpositive_threshold']==21 and t['T2']['stable_sufficient_nonpositive_threshold']==14,'two pre-insertion occupancies; stable thresholds apply only to literal predicate schedules')
index=read(AREA/'checkpoint-054-reviews.json'); findings=[]
for r in index['final_core_audits']:
    p=AREA/r['final_audit']; a=identity(p)
    if any(a[k]!=r[k] for k in a): findings.append(r['role']+':audit identity')
    audit=read(p)
    if audit['unresolved_findings'] not in (0,[]): findings.append(r['role']+':unresolved findings')
    if len(r['inputs'])!=5: findings.append(r['role']+':input count')
    for row in r['inputs']:
        p=(ROOT/row['path']) if row['path'].startswith('docs/') else (AREA/row['path'])
        actual=identity(p)
        if any(actual[k]!=row[k] for k in actual): findings.append(r['role']+':'+row['path'])
check('three_final_five_file_audits',len(index['final_core_audits'])==3 and not findings and sum(x['checks'] for x in index['final_core_audits'])==40,{'findings':findings,'substantive_checks':40})
doc=read(V/'documentation-001/result.json'); receipt=read(V/'documentation-001/command.json')
check('actual_documentation_result',doc['status']=='passed' and doc['sources_verified']==29 and doc['sections_verified']==233 and not doc['failures'] and receipt['exit_code']==0 and receipt['stable_inputs'],{'sources':doc['sources_verified'],'sections':doc['sections_verified'],'links':doc['links']})
n=read(AREA/'checkpoint-054-next-scope.json')
check('next_boundary_and_exclusions',n['next_checkpoint']=='C055' and n['cost']['factory_room']==163 and n['cost']['not_164'] and n['cost']['complete_gate_cost'] is None and 'No endpoint constant computation or numerical replay' in n['exclusions'] and 'No main integration or release acceptance' in n['exclusions'] and n['release']['original28']=='24/28 historical' and n['release']['open']==['P11','P16','P23','L03'] and not n['release']['full_product_goal_completed'],'distinct use-sensitive original cold miss; no implementation/constants/collector or changed release state')
check('unchanged_documentation_checker',identity(ROOT/'docs/maintenance/reorganization-2026-10-17/verify_reorganization.py')['git_blob']=='25e4c5a224cbe15bbeba9a7e35301de4368d3de7','original checker bytes remain exact')
failed=[x for x in checks if x['status']!='passed']
print(json.dumps({'schema':'ontokin.checkpoint054-metadata-result/0.1','status':'failed' if failed else 'passed','grouped_checks':len(checks),'checks':checks,'failures':failed,'scope':'file/source/claim consistency only; not numerical/runtime execution or a release audit'},indent=2))
raise SystemExit(1 if failed else 0)
