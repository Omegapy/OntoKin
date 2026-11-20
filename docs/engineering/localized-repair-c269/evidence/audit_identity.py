"""Read-only identity audit of retained C268 execution, not a behavioral rerun."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
BASE = '23c044775ad77e7c1ab2f27eb1c9dd4a67c004bb'
ORIGINAL = '5084dd69312e8da5a49aadd33cf83ba56db7c058'
RECEIPT = 'docs/engineering/localized-repair-c268/evidence/finalization-a3de3dd23bbf/main-integration/CHECKS.json'
OUT = Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).with_name('EXECUTION-ELIGIBILITY.json')

def git_bytes(rev, path):
    return subprocess.check_output(['git','show',rev+':'+path],cwd=ROOT)

def identity(data):
    return {'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}

j=json.loads(git_bytes(BASE,RECEIPT))
assert j['source_before']['commit']==ORIGINAL and j['source_after']==j['source_before']
assert j['complete'] and j['passed'] and j['input_identity_unchanged']
assert j['input_files_before']==j['input_files_after']
assert j['planned_check_count']==j['completed_check_count']==12 and j['total_methods']==282
inputs=[];deltas=[];outputs=[]
allowed_deltas={'STATUS.md','docs/engineering/localized-repair-c268/README.md','docs/engineering/localized-repair-c268/RESULTS.md','docs/workflow/CURRENT.json','docs/workflow/knowledge.json','docs/workflow/tasks/C268/PLAN.md','docs/workflow/tasks/C268/task.json'}
for item in j['input_files_before']:
    original=identity(git_bytes(ORIGINAL,item['path']))
    assert original=={k:item[k] for k in ('bytes','sha256')},item['path']
    observed=identity(git_bytes(BASE,item['path']))
    row={'path':item['path'],'execution_revision':ORIGINAL,'original':original,'audit_baseline_revision':BASE,'audit_baseline':observed,'unchanged':observed==original}
    inputs.append(row)
    if not row['unchanged']:deltas.append(row)
assert {x['path'] for x in deltas}==allowed_deltas
assert all(x['unchanged'] for x in inputs if x['path'].endswith(('.py','.ok','.glb')))
parent=Path(RECEIPT).parent
for item in j['output_files']:
    p=(parent/item['path']).as_posix();actual=identity(git_bytes(BASE,p))
    assert actual=={k:item[k] for k in ('bytes','sha256')},p
    outputs.append({'path':p,**actual,'revision':BASE})
for check in j['checks']:
    assert check['result']=='passed' and check['exit_code']==0
    assert all(check['assertions'].values()),check['name']
    log=check['log'];assert identity(git_bytes(BASE,(parent/log['path']).as_posix()))=={k:log[k] for k in ('bytes','sha256')}
result={'schema':'ontokin.c269.execution-evidence-identity/1','result':'passed','audited_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'audit_baseline_revision':BASE,'original_execution_revision':ORIGINAL,'receipt':{'path':RECEIPT,**identity(git_bytes(BASE,RECEIPT))},'source_inputs':inputs,'changed_documentation_records':deltas,'behavioral_inputs_unchanged':True,'outputs':outputs,'checks':[{'name':x['name'],'command':x['command'],'methods':x['methods'],'result':x['result'],'assertions':x['assertions'],'log':x['log']} for x in j['checks']],'historical_environment':j['environment'],'current_inspection_environment':{'python':sys.version,'platform':platform.platform()},'new_behavioral_execution':False,'verdict':'Existing behavioral execution is eligible for audit at its original revision: code, tests, fixtures and dependency identities remain exact. Seven documentation/state records changed; original checks do not validate new C269 documents. H-group completeness requires separate assertion-level analysis.','limits':j['limits'],'not_run':j['not_run']}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'result':'passed','source_inputs':len(inputs),'unchanged_inputs':sum(x['unchanged'] for x in inputs),'document_deltas':len(deltas),'output_identities':len(outputs),'original_groups':12,'original_methods':282,'behavioral_rerun':False,'output':str(OUT)}))
