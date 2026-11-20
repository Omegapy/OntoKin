#!/usr/bin/env python3
"""Approve exact final C270 evidence candidate without any behavioral execution."""
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import subprocess
import zipfile

REPO=Path('/workspace/scratch/9e9d17639499/OntoKin')
OUT=Path(__file__).resolve().parent
SHA='4c53c3566cd18cb0f1fd47b02be6b23a40b40e68'
PARENT='096803b2377966a04f9043139324bac2c65b6a52'
P='docs/engineering/localized-repair-c270/'
E=P+'evidence/recovery-20261120/'
checks=[]
def git(*args): return subprocess.check_output(['git','-C',str(REPO),*args])
def raw(path,rev=SHA): return git('show',rev+':'+path)
def obj(path,rev=SHA): return json.loads(raw(path,rev))
def ident(b): return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def check(name,passed,detail=None):
    row={'name':name,'passed':bool(passed)}
    if detail is not None: row['detail']=detail
    checks.append(row)

changed=[row.split('\t') for row in git('diff','--name-status',PARENT,SHA).decode().splitlines()]
check('exact final candidate tree',git('rev-parse',SHA+'^{tree}').decode().strip()=='c923dad3176443f23167ef4526c0264e6e172c0f')
check('exact final candidate retains previously approved parent',git('show','-s','--format=%P',SHA).decode().strip()==PARENT)
check('ten-path final delta only adds review/check evidence and updates truthful state',len(changed)==10 and all(status in {'A','M'} and (p.startswith(E) or p in {P+'RECOVERY-FINALIZATION.md','docs/workflow/CURRENT.json','docs/workflow/tasks/C270/task.json'}) for status,p in changed))
inventory=[]
for status,path in changed:
    b=raw(path);inventory.append({'status':status,'path':path,**ident(b)})
    if path.endswith('.json'): json.loads(b)
    elif not path.endswith('.zip'): b.decode('utf-8')
check('original immutable evidence still unchanged',all(raw(p)==raw(p,'1a2e9f85fa3ba210a16235e5660f1762ea8a953e') for p in git('ls-tree','-r','--name-only','1a2e9f85fa3ba210a16235e5660f1762ea8a953e','--',P).decode().splitlines()))
check('direct published review approval matches reviewer bytes',raw(E+'CANDIDATE-REVIEW.json')==(OUT/'APPROVAL.json').read_bytes())
check('direct published review prose matches reviewer bytes',raw(E+'CANDIDATE-REVIEW.md')==(OUT/'REVIEW.md').read_bytes())
archive_record=obj(E+'CANDIDATE-REVIEW-ARCHIVE.json'); archive=raw(E+archive_record['file'])
check('full review archive identity matches receipt',ident(archive)=={k:archive_record[k] for k in ('bytes','sha256')})
z=zipfile.ZipFile(io.BytesIO(archive)); names=z.namelist(); manifest=json.loads(z.read('MANIFEST-SHA256.json'))['files']
check('review archive has safe unique paths and valid CRC',len(names)==len(set(names)) and z.testzip() is None and all(not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts and '\\' not in n for n in names))
check('all 14 archived payload files are covered exactly once',len(manifest)==archive_record['payload_files']==14 and {x['path'] for x in manifest}==set(names)-{'MANIFEST-SHA256.json'})
for item in manifest:
    b=z.read(item['path'])
    check('archive preserves exact original review artifact: '+item['path'],ident(b)=={k:item[k] for k in ('bytes','sha256')} and b==(OUT/item['path']).read_bytes())
old_dir=OUT.parent/'checks/recovery-checkpoint'
for name in ('CHECKS.json','workflow.log','documentation.log'):
    check('published earlier candidate-check bytes: '+name,raw(E+'candidate-checks/'+name)==(old_dir/name).read_bytes())
task=obj('docs/workflow/tasks/C270/task.json'); old_task=obj('docs/workflow/tasks/C270/task.json',PARENT)
check('parent task/issue branch stay unfinished',task['status']=='in_progress' and task['branch']==old_task['branch'] and task['completion']['branch_disposition']=='active' and task['scope_issue']==old_task['scope_issue'])
check('R02 still unmet with unchanged acceptance',next(r for r in task['requirements'] if r['id']=='R02')==next(r for r in old_task['requirements'] if r['id']=='R02') and next(r for r in task['requirements'] if r['id']=='R02')['status']=='not_done')
check('all requirement definitions unchanged',all({k:v for k,v in a.items() if k not in {'status','evidence'}}=={k:v for k,v in b.items() if k not in {'status','evidence'}} for a,b in zip(task['requirements'],old_task['requirements'])))
check('only satisfied R03 advances; R04/R05 remain pending',[r['status'] for r in task['requirements']]==['done','not_done','done','not_done','not_done'])
check('R03 links reviewed approval, fresh records and historical cohort',next(r for r in task['requirements'] if r['id']=='R03')['evidence']==[E+'CANDIDATE-REVIEW.json',E+'candidate-checks/CHECKS.json',P+'evidence/candidate/regressions/CHECKS.json'])
check('scope remains finalization-only without behavioral reruns',task['session_phase']==old_task['session_phase'] and task['session_phase']['behavioral_reruns_this_phase']==0 and task['delivery']['status']=='pending')
check('CURRENT remains active and correction forbidden',obj('docs/workflow/CURRENT.json')['active_task']=='C270' and 'do not implement the correction' in obj('docs/workflow/CURRENT.json')['next_action']['summary'])
check('final metadata review correctly awaited external outcome before integration',task['recovery']['independent_review']['final_metadata_delta_review']=='pending' and 'actual-main' in task['next_action'])

fresh_dir=OUT.parent/'checks/final-candidate'; fresh=json.loads((fresh_dir/'CHECKS.json').read_bytes())
check('fresh final-candidate checks bind exact clean candidate/tree',fresh['source_revision']==SHA and fresh['source_tree']=='c923dad3176443f23167ef4526c0264e6e172c0f' and fresh['source_clean'] is True and fresh['result']=='passed')
check('both required final-candidate record commands executed', [r['name'] for r in fresh['checks']]==['workflow','documentation'] and fresh['checks'][0]['command'][-2:]==['tools/chat_workflow.py','check'] and fresh['checks'][1]['command'][-1]=='docs/maintenance/reorganization-2026-10-17/verify_reorganization.py')
for row in fresh['checks']:
    b=(fresh_dir/row['log']['path']).read_bytes()
    check('fresh final '+row['name']+' exact output and successful process',ident(b)=={k:row['log'][k] for k in ('bytes','sha256')} and row['exit_code']==0 and row['result']=='passed')
    if row['name']=='workflow':
        check('fresh final workflow log confirms structure pass',b.startswith(b'Workflow structure passed (11 tasks).'))
    else:
        result=json.loads(b);check('fresh final documentation report confirms pass/no failures',result['status']=='passed' and result['failures']==[])
failed=[c for c in checks if not c['passed']]
report={'schema':'ontokin.c270.final-candidate-approval/1','reviewer':'/root/candidate_review','director':'c270-recovery-9e9d17639499','recorded_at_utc':datetime.now(timezone.utc).isoformat(),'candidate':SHA,'tree':'c923dad3176443f23167ef4526c0264e6e172c0f','parent':PARENT,'compared_main':'ab0f196cd8c67dfa94cba369381dafa8b6c7a015','verdict':'approved_for_evidence_only_integration' if not failed else 'not_approved','mandatory_findings':failed,'passed':not failed,'final_delta_check_count':len(checks),'prior_static_checks':389,'total_static_checks':389+len(checks),'checks':checks,'changed_files':inventory,'fresh_record_checks':{'path':str(fresh_dir/'CHECKS.json'),**ident((fresh_dir/'CHECKS.json').read_bytes())},'archive_verified':archive_record,'behavioral_runs':0,'remote_operations':0,'unknown_operations':[],'R02':'failed; original oracle and outcomes unchanged','parent_and_issue_must_remain_open':True,'unfinished_branch_must_be_retained':True,'remaining_gates':['Conditional integration of this exact candidate','Fresh actual-main documentation/workflow checks','Observed branch retention','Verified saved partial handoff/prompts plus external confirmed receipt','Stop without classification correction'],'script':{'path':Path(__file__).name,**ident(Path(__file__).read_bytes())}}
(OUT/'FINAL-APPROVAL.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ('candidate','verdict','final_delta_check_count','total_static_checks','mandatory_findings')}))
