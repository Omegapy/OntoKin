#!/usr/bin/env python3
"""Verify completed affected-cohort evidence without rerunning its behavior."""
import collections
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT=Path('/workspace/scratch/c219bb61a617')
OUT=ROOT/'integration-review'
RESULT=ROOT/'validation/affected-candidate'
REPO=ROOT/'OntoKin'
CANDIDATE='88bc8b51b3963b7072375edac6400b6e6a4532e4'
PHASE='2a85f71489fea57dc165cde61e3f7cc67a8ae999'
checks=[]
def identity(b):return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def verify(group,name,ok,**data):checks.append({'category':group,'name':name,'passed':bool(ok),**data})
def raw(rev,path):return subprocess.check_output(['git','-C',str(REPO),'show',rev+':'+path])
def read(path):return json.loads(Path(path).read_text())

report=read(RESULT/'CHECKS.json')
receipt_path=ROOT/'validation/execution-receipts/affected-candidate/EXECUTION.json'
receipt=read(receipt_path)
inventory=read(OUT/'REGRESSION-INVENTORY-REVIEW.json')
verify('execution','Outer process completed successfully',receipt['status']=='passed' and receipt['returncode']==0 and receipt['source_unchanged'] is True)
verify('execution','Confirmed early save precedes execution',datetime.fromisoformat(receipt['early_recovery']['record']['saved_at_utc'])<datetime.fromisoformat(receipt['started_at']))
verify('execution','Exact candidate clean before and after',report['source_before']==report['source_after']==receipt['source_before']==receipt['source_after'] and report['source_before']['commit']==CANDIDATE and report['source_before']['all_dirty_status']=='')
verify('execution','All required checks and 282 methods completed',report['complete'] is True and report['passed'] is True and report['completed_check_count']==report['planned_check_count']==12 and report['total_methods']==report['expected_total_methods']==282 and not report['remaining_checks'])
verify('inputs','All source input identities stable',report['input_identity_unchanged'] is True and report['input_files_before']==report['input_files_after'])
record_changes=[]
for e in report['input_files_before']:
    observed=identity(raw(CANDIDATE,e['path']))
    verify('inputs',e['path'],observed=={'bytes':e['bytes'],'sha256':e['sha256']})
    later=identity(raw(PHASE,e['path']))
    if later!=observed:record_changes.append({'path':e['path'],'candidate':observed,'phase':later})
verify('reuse','Later phase changes only record input CURRENT among this manifest',all(e['path']=='docs/workflow/CURRENT.json' for e in record_changes),changed_inputs=record_changes)
for e in report['output_files']:
    verify('outputs',e['path'],identity((RESULT/e['path']).read_bytes())=={'bytes':e['bytes'],'sha256':e['sha256']})
for name in ['stdout_identity','stderr_identity','entrypoint','wrapper']:
    e=receipt[name]
    verify('execution',name,identity(Path(e['path']).read_bytes())=={'bytes':e['bytes'],'sha256':e['sha256']})
suite_by_component={re.search(r'localized-repair-c(\d+)',e['path']).group(1):e for e in inventory['suites']}
actual_methods=[]
for step in report['checks']:
    log=(RESULT/step['log']['path']).read_text()
    verify('check_result',step['name'],step['result']=='passed' and step['exit_code']==0 and step['failure'] is None and all(v is True for v in step['assertions'].values()))
    if step['expected_methods'] is not None:
        component=re.match(r'c(\d+)',step['name']).group(1)
        found=re.findall(r'^test_\w+ \(([^)]+)\) \.\.\. ok$',log,re.MULTILINE)
        names=['.'.join(x.split('.')[-2:]) for x in found]
        expected=suite_by_component[component]['methods']
        verify('method_inventory',step['name'],len(names)==len(set(names))==step['expected_methods'] and set(names)==set(expected) and bool(re.search(r'^OK$',log,re.MULTILINE)),executed_methods=names)
        actual_methods.extend([component+':'+n for n in names])
    elif step['name']=='c253-corpus':
        value=json.loads(log)
        verify('check_result','Actual corpus checker values',value['passed'] is True and value['boundFiles']==14 and value['tasks']==3)
    elif step['name']=='workflow':
        value=json.loads(log);verify('check_result','Actual workflow result',value['passed'] is True and value['errors']==[])
    elif step['name']=='documentation':
        value=json.loads(log);verify('check_result','Actual documentation result',value['status']=='passed' and value['failures']==[])
verify('method_inventory','Every declared method executed once',len(actual_methods)==len(set(actual_methods))==282)
call_totals={}
for component,count in [(266,748),(267,123),(268,131)]:
    value=read(RESULT/f'c{component}-controls/results.json')
    outcomes=dict(collections.Counter(c['outcome'] for c in value['cases']))
    call_totals[str(component)]={'calls':value['apiCalls'],'outcomes':outcomes}
    verify('control_accounting',f'C{component} original response cases',len(value['cases'])==value['apiCalls']==count and value['passed'] is True and value['failures']==value['errors']==value['skipped']==[] and sum(outcomes.values())==count,outcomes=outcomes)
    for path,e in value['implementationAndControlInputs'].items():
        verify('control_inputs',f'C{component}: '+path,identity(raw(CANDIDATE,path))==e)
    if component in [267,268]:verify('control_inputs',f'C{component} stable during actual execution',value['inputCodeStableDuringRun'] is True)
    if component==268:verify('control_accounting','C268 no untyped exceptions',value['untypedExceptions']==0 and value['callAccountingVerified'] is True)
failed=[c for c in checks if not c['passed']]
result={'schema':'ontokin.c271.p02-independent-affected-evidence-review/1','reviewer':'/root/intake_audit','reviewed_at_utc':datetime.now(timezone.utc).isoformat(),'verdict':'passed' if not failed else 'failed','candidate':CANDIDATE,'candidate_tree':report['source_before']['tree'],'phase_checkpoint':PHASE,'source_report':{'path':str(RESULT/'CHECKS.json'),**identity((RESULT/'CHECKS.json').read_bytes())},'execution_receipt':{'path':str(receipt_path),**identity(receipt_path.read_bytes())},'coverage':{'checks':len(checks),'failed':len(failed),'source_inputs':len(report['input_files_before']),'verified_outputs':len(report['output_files']),'executed_methods':len(actual_methods),'actual_cohort_checks':12,'call_accounting':call_totals},'later_changed_record_inputs':record_changes,'behavioral_suite_reuse_to_phase_checkpoint':'eligible; exact code/fixture/test identities unchanged','workflow_record_reuse_to_phase_checkpoint':'not eligible for changed CURRENT; fresh exact-checkpoint record checks required','integration_approval':'not granted: routine-driver and final metadata evidence still separate','behavioral_reexecution':False,'mandatory_findings':failed,'checks':checks}
(OUT/'AFFECTED-EVIDENCE-REVIEW.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['verdict','coverage','mandatory_findings','integration_approval']},indent=2))
raise SystemExit(1 if failed else 0)
