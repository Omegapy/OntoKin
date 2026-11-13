#!/usr/bin/env python3
"""Independent read-only audit of completed C227 diagnostic evidence."""
from pathlib import Path
import base64
import hashlib
import json
import os
import pstats
import shutil
import sqlite3
import struct
import subprocess

ROOT = Path('/workspace/scratch/28482a5da524')
RUN = ROOT / 'c227-diagnostic-run'
OUT = ROOT / 'diagnosis-review/outcome'
REPO = ROOT / 'OntoKin'
CHECKS = []

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read(path):
    return json.loads(Path(path).read_text())

def require(name, value, detail=None):
    CHECKS.append({'check': name, 'passed': bool(value), 'detail': detail})
    if not value:
        raise AssertionError(name)

def inventory(root):
    return [{'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)}
            for p in sorted(root.rglob('*')) if p.is_file()]

def group_absent(pgid):
    try:
        os.killpg(pgid, 0)
        return False
    except ProcessLookupError:
        return True

def main():
    summary = read(RUN/'RUN-SUMMARY.json')
    plan, approval = read(RUN/'REVIEWED-PLAN.json'), read(RUN/'APPROVAL.json')
    require('exact two consumed slots', summary['scopeComplete'] is True and summary['consumedSlots']==2 and summary['remainingSlots']==[] and summary['stopReason'] is None)
    require('no broader work reported', summary['aggregateRun'] is False and summary['repairPerformed'] is False and summary['nativeStarts']==0 and summary['productTestMethods']==0)
    for key, path in [('planSha256',RUN/'REVIEWED-PLAN.json'),('approvalSha256',RUN/'APPROVAL.json'),('identityReviewSha256',RUN/'IDENTITY-REVIEW.txt'),('scriptSha256',ROOT/'diagnostic-author/diagnose_a08.py')]:
        require('actual '+key, sha(path)==summary[key])
    require('copied approval exact', approval==read(ROOT/'diagnosis-review/APPROVAL.json'))
    expected = read(RUN/'EVIDENCE-SHA256.json')['files']
    names = []
    for row in expected:
        p=RUN/row['path'];names.append(row['path'])
        require('safe evidence path '+row['path'], p.resolve().is_relative_to(RUN) and not p.is_symlink())
        require('evidence bytes '+row['path'], p.is_file() and p.stat().st_size==row['bytes'] and sha(p)==row['sha256'])
    require('unique manifest paths',len(names)==len(set(names)))
    require('complete evidence manifest',set(names)=={p.relative_to(RUN).as_posix() for p in RUN.rglob('*') if p.is_file() and p.name!='EVIDENCE-SHA256.json'})
    inputs=read(RUN/'INPUTS.json')
    require('input source identity',inputs['commit']==approval['sourceCommit'] and inputs['tree']==approval['sourceTree'])
    for row in inputs['protectedInputs']:
        p=REPO/row['path']
        require('unchanged protected bytes '+row['path'],p.stat().st_size==row['bytes'] and sha(p)==row['sha256'])
        actual=subprocess.check_output(['git','cat-file','blob',row['gitBlob']],cwd=REPO)
        require('bound Git blob '+row['path'],actual==p.read_bytes())
    fixed=REPO/'docs/language-design/torque-v0.1/freeze'
    workflow=next(x for x in read(fixed/'agent/request-workflows.json')['scenarios'] if x['id']=='A08')
    expected_export=workflow['steps'][1]['request'].copy()
    expected_export.update(project_id='c091-byte-proof',request_id='seed-export')
    source_manifest=read(fixed/'workflow-agent-base.files.json')
    outcomes=[]
    for index, mode in enumerate(('baseline','cprofile'),1):
        slot=RUN/f'{index}-{mode}'
        process=read(slot/'PROCESS.json');result=read(slot/'SETUP-RESULT.json')
        consumed=read(slot/'CONSUMED.json');started=read(slot/'STARTED.json')
        require(mode+' process receipt equals summary',process==summary['slots'][index-1])
        require(mode+' start and consumption agreement',all(started[k]==v for k,v in consumed.items() if k in started))
        require(mode+' mode and slot identity',consumed['slot']==index and consumed['mode']==mode and started['slot']==index and started['mode']==mode)
        require(mode+' source binding',started['sourceCommit']==approval['sourceCommit'] and started['sourceTree']==approval['sourceTree'] and result['source']['commit']==approval['sourceCommit'] and result['source']['tree']==approval['sourceTree'])
        require(mode+' process identity',started['pid']==process['pid']==process['processGroup']==result['pid']==result['processGroup'])
        require(mode+' terminal process',process['exitCode']==(0 if mode=='baseline' else 1) and not process['timedOut'] and process['processGroupAbsent'] and process['signals']==[] and not process.get('residualGroupTerminated'))
        require(mode+' process group still absent',group_absent(process['processGroup']))
        require(mode+' original cleanup and source stability',result['originalClassCleanup'] and result['sourceAndInputsUnchanged'] and result['semanticExportModuleImported'] is False)
        require(mode+' zero test methods',result['testMethodsExecuted']==0)
        raw=slot/'store-raw';raw_before=inventory(raw)
        require(mode+' retained raw inventory',raw_before==result['store']['rawInventory'])
        copied=OUT/f'inspection-{mode}'
        require(mode+' fresh review inspection copy',not copied.exists())
        shutil.copytree(raw,copied)
        dbpath=next(copied.glob('*.sqlite3'))
        with sqlite3.connect(dbpath.as_uri()+'?mode=ro',uri=True) as db:
            db.row_factory=sqlite3.Row;db.execute('PRAGMA query_only=ON')
            require(mode+' independent database integrity',db.execute('PRAGMA integrity_check').fetchone()[0]=='ok')
            projects=[dict(x) for x in db.execute('SELECT * FROM projects')]
            require(mode+' accepted source preserved',projects==[{'id':'c091-byte-proof','accepted_revision':plan['programRevision']}])
            requests=[]
            for x in db.execute('SELECT sequence,id,operation,state,payload,response FROM requests ORDER BY sequence'):
                x=dict(x);x['payload']=json.loads(x['payload']);x['response']=json.loads(x['response']);requests.append(x)
            require(mode+' exact derived requests',requests==result['store']['databases'][0]['requests'])
            require(mode+' only original two requests',[x['id'] for x in requests]==['seed-create','seed-export'])
            require(mode+' unchanged original export request',requests[1]['payload']==expected_export)
            create=requests[0]['payload'];bundle=create['bundle']
            require(mode+' original entry source',bundle['entry']['filename']==source_manifest['entry']['filename'] and bundle['entry']['source'].encode()==(fixed/source_manifest['entry']['path']).read_bytes())
            require(mode+' one original module',len(bundle['modules'])==1)
            for module, declared in zip(bundle['modules'],source_manifest['modules']):
                require(mode+' original module source',all(module[k]==declared[k] for k in ('filename','package_id','version')) and module['source'].encode()==(fixed/declared['path']).read_bytes())
            for asset, declared in zip(bundle['assets'],source_manifest['assets']):
                data=base64.b64decode(asset['data_base64'],validate=True)
                require(mode+' original asset bytes',data==(fixed/declared['path']).read_bytes() and 'sha256:'+hashlib.sha256(data).hexdigest()==declared['sha256'])
            source_row=db.execute('SELECT * FROM sources').fetchall()
            require(mode+' exact retained source payload',len(source_row)==1 and json.loads(bytes(source_row[0]['raw']))==bundle and source_row[0]['accepted_once']==1 and source_row[0]['revision']==plan['programRevision'])
            require(mode+' service session closed',all(x['closed']==1 for x in db.execute('SELECT * FROM sessions')))
            require(mode+' no running requests',all(x['state'] in ('succeeded','failed') for x in requests))
            export=requests[1]['response'];budget=export['execution_budget']
            require(mode+' exact request/host/source budgets',all(budget[k]==plan['productLimits'] for k in ('effective','host_ceilings','source_request')))
            require(mode+' exact implementation/program identity',budget['implementation']['source_code_sha256']==plan['implementationDigest'] and budget['program_revision']==plan['programRevision'])
            artifacts=list(db.execute('SELECT * FROM artifacts'));runs=list(db.execute('SELECT * FROM runs'))
            if mode=='baseline':
                require('baseline original success',export['status']=='succeeded' and result['setupOutcome']=='succeeded' and budget['elapsed_ms']<30000 and budget['consumed_operations']==452627)
                require('baseline atomic published run/artifact',len(runs)==1 and len(artifacts)==1 and export['run_id']==runs[0]['id'])
                data=bytes(artifacts[0]['data']);artifact_hash=hashlib.sha256(data).hexdigest()
                require('baseline exact historical artifact',len(data)==2447148 and artifact_hash=='6911a4921133841df9b12e308c59b89b9ef4b5219f604751c6de2861410564aa')
                require('baseline artifact identity and report',artifacts[0]['id']==export['result']['artifact_id']=='artifact:'+artifact_hash and artifacts[0]['sha256']=='sha256:'+artifact_hash and json.loads(artifacts[0]['report'])==export['result']['report'])
                require('baseline GLB header',struct.unpack('<4sII',data[:12])==(b'glTF',2,len(data)))
            else:
                require('profile failure equals raw assertion',export==result['response'])
                require('profile exact deadline refusal',export['status']=='failed' and result['setupOutcome']=='assertion' and budget['budget_reason']=='execution_deadline_exceeded' and budget['stage']=='recording_export_readback' and budget['consumed_operations']==140127)
                require('profile no partial artifact/run publication',len(artifacts)==0 and len(runs)==0 and export['run_id'] is None)
                artifact_hash=None
            outcomes.append({'mode':mode,'setupOutcome':result['setupOutcome'],'setupWallSeconds':result['setupWallSeconds'],'setupCpuSeconds':result['setupCpuSeconds'],'exportStatus':export['status'],'exportBudget':budget,'requestCount':len(requests),'artifactCount':len(artifacts),'runCount':len(runs),'artifactSha256':artifact_hash,'process':process,'cpuContextBeforeSetup':result['cpuContextBeforeSetup'],'cpuContextAfterSetup':result['cpuContextAfterSetup']})
        shutil.rmtree(copied)
        require(mode+' original raw evidence remained exact',inventory(raw)==raw_before)
    profile=read(RUN/'2-cprofile/profile-functions.json');stats=pstats.Stats(str(RUN/'2-cprofile/setup.prof'))
    require('profile call totals match binary',profile['totalCalls']==stats.total_calls and profile['primitiveCalls']==stats.prim_calls and profile['totalProfileSeconds']==stats.total_tt)
    require('complete profile function inventory',len(profile['functions'])==len(stats.stats))
    for row in profile['functions']:
        cc,nc,tt,ct,callers=stats.stats[(row['filename'],row['line'],row['function'])]
        require('profile function '+row['filename']+':'+str(row['line'])+':'+row['function'],(cc,nc,tt,ct)==(row['primitiveCalls'],row['totalCalls'],row['selfSeconds'],row['cumulativeSeconds']))
        normalized=[{'filename':key[0],'line':key[1],'function':key[2],'costs':list(value) if isinstance(value,tuple) else value} for key,value in sorted(callers.items())]
        require('profile callers '+row['filename']+':'+str(row['line'])+':'+row['function'],normalized==row['callers'])
    selected=[]
    for file,name in [('torque_recording.py','_sample_recording_nodes'),('torque_runtime.py','recording_frames'),('torque_runtime.py','guard'),('torque_runtime.py','_source_watches_current'),('execution_budget.py','tick'),('execution_budget.py','admit_callback'),('budget_agent.py','_poll')]:
        matches=[x for x in profile['functions'] if x['filename'].endswith('/'+file) and x['function']==name]
        selected.extend({k:v for k,v in x.items() if k!='callers'} for x in matches)
    unreached=[]
    for file,name in [('gltf.py','_encode'),('gltf.py','read_glb'),('gltf.py','validate_export'),('torque_recording.py','interval_certificates'),('torque_validation_guard.py','__enter__')]:
        found=any(x['filename'].endswith('/'+file) and x['function']==name for x in profile['functions'])
        require('profile did not reach '+file+':'+name,not found)
        unreached.append(file+':'+name)
    return {'schema':'ontokin.c227.independent-outcome-review/0.1','status':'passed','checks':CHECKS,'checkCount':len(CHECKS),'outcomes':outcomes,'profile':{'totalCalls':profile['totalCalls'],'primitiveCalls':profile['primitiveCalls'],'functionCount':len(profile['functions']),'selected':selected,'unreached':unreached,'interpretation':'Instrumented prefix only; cumulative times overlap and must not be added or treated as baseline percentages.'},'productExecutionsByReviewer':0,'rawEvidencePreserved':True}

if __name__=='__main__':
    OUT.mkdir(parents=True,exist_ok=True)
    try:
        result=main()
    except BaseException as exc:
        result={'schema':'ontokin.c227.independent-outcome-review/0.1','status':'failed','checks':CHECKS,'errorType':type(exc).__name__,'error':str(exc),'productExecutionsByReviewer':0}
        (OUT/'OUTCOME-REVIEW.json').write_text(json.dumps(result,indent=2)+'\n')
        raise
    (OUT/'OUTCOME-REVIEW.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'checks':result['checkCount'],'profileFunctions':result['profile']['functionCount'],'productExecutionsByReviewer':0}))
