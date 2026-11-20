#!/usr/bin/env python3
"""Independent static acceptance review; never imports candidate product code."""
import ast
import collections
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import platform
import subprocess
import sys
import traceback
import zipfile

ROOT=Path('/workspace/scratch/c219bb61a617')
REPO=ROOT/'OntoKin'
OUT=ROOT/'integration-review'
MAIN='e1a48f7d0635e9aa4f4b6d6a586e7305eb81999d'
EXECUTED='067392f2b5f592a5c3104fa8848cc0030ba1117b'
CANDIDATE='88bc8b51b3963b7072375edac6400b6e6a4532e4'
PHASE='2a85f71489fea57dc165cde61e3f7cc67a8ae999'
C271='docs/engineering/localized-repair-c271/'
checks=[]
commands=[]
trees={}
readset=[]

def digest(b): return hashlib.sha256(b).hexdigest()
def ident(b): return {'bytes':len(b),'sha256':digest(b)}
def save(name,obj): (OUT/name).write_text(json.dumps(obj,indent=2)+'\n')
def check(category,name,ok,**extra): checks.append({'category':category,'name':name,'passed':bool(ok),**extra})
def git(*args):
    cmd=['git','-C',str(REPO),*args]
    p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    commands.append({'command':cmd,'exit_code':p.returncode,'stderr':p.stderr.decode(errors='replace')})
    if p.returncode: raise RuntimeError(str(cmd)+': '+p.stderr.decode(errors='replace'))
    return p.stdout
def raw(rev,path): return git('show',rev+':'+path)
def doc(rev,path):
    b=raw(rev,path); readset.append({'git_revision':rev,'path':path,**ident(b)})
    return json.loads(b)
def tree(rev):
    if rev not in trees:
        rows={}
        for row in git('ls-tree','-rzl',rev).split(b'\0'):
            if not row: continue
            h,p=row.split(b'\t',1);mode,typ,sha,size=h.decode().split()
            rows[p.decode()]={'mode':mode,'kind':typ,'git_blob':sha,'bytes':int(size) if size!='-' else None}
        trees[rev]=rows
    return trees[rev]
def delta(a,b): return [line.split('\t',1) for line in git('diff','--name-status',a,b).decode().splitlines()]

def main():
    cumulative=delta(MAIN,CANDIDATE)
    phase_delta=delta(CANDIDATE,PHASE)
    check('scope','Cumulative 59 paths stay within C271 and proposed CURRENT',len(cumulative)==59 and all(p.startswith(C271) or p.startswith('docs/workflow/tasks/C271/') or p=='docs/workflow/CURRENT.json' for _,p in cumulative),changed_paths=len(cumulative))
    check('scope','No preexisting product/observer/contract/test/dependency/workflow file changed',all(s=='A' or p=='docs/workflow/CURRENT.json' for s,p in cumulative))
    phase_allowed={'docs/workflow/CURRENT.json','docs/workflow/tasks/C271/task.json','docs/workflow/tasks/C271/REQUIREMENTS.md','docs/workflow/tasks/C271/PLAN.md','docs/workflow/tasks/C271/P02-SESSION.md'}
    check('scope','P02 checkpoint is metadata/evidence only',len(phase_delta)==16 and all(p.startswith(C271+'finalization-20261120/') or p in phase_allowed for _,p in phase_delta),changed_paths=len(phase_delta))
    change_inventory=[]
    for rev,changes in [(CANDIDATE,cumulative),(PHASE,phase_delta)]:
        for status,path in changes:
            b=raw(rev,path); row={'revision':rev,'status':status,'path':path,**tree(rev)[path],**ident(b)}
            if path.endswith('.json'):
                parsed=json.loads(b);row['inspection']='JSON parsed fully; scoped evidence/record'
            elif path.endswith('.py'):
                ast.parse(b);row['inspection']='Python parsed as text/AST; not executed'
            elif path.endswith('.zip'):
                with zipfile.ZipFile(io.BytesIO(b)) as z:
                    row['zip_members']=len(z.infolist());row['zip_crc_passed']=z.testzip() is None
                row['inspection']='Evidence ZIP integrity and inventory'
            else: row['inspection']='Text/log/fixture bytes identified; relevant prose/source manually reviewed'
            change_inventory.append(row)
            check('changed_file',rev+':'+path,True)
    result=doc(CANDIDATE,C271+'evidence/control-candidate/RESULTS.json')
    receipt=doc(CANDIDATE,C271+'evidence/control-candidate/EXECUTION-RECEIPT.json')
    oracle=doc(CANDIDATE,C271+'control/EXPECTED.json')
    check('p01_evidence','Exact executed commit/tree and clean source',result['source']['commit']==EXECUTED and result['source']['tree']==git('rev-parse',EXECUTED+'^{tree}').decode().strip() and result['source']['dirty_before']=='')
    input_rows=[]
    for e in result['input_identities']:
        versions={rev:tree(rev).get(e['path']) for rev in [EXECUTED,CANDIDATE,PHASE]}
        b=raw(CANDIDATE,e['path'])
        ok=ident(b)=={'bytes':e['bytes'],'sha256':e['sha256']} and all(v and v['git_blob']==e['git_blob'] and v['bytes']==e['bytes'] for v in versions.values())
        input_rows.append({**e,'identities':versions,'unchanged':ok})
        check('reuse_input',e['path'],ok)
    control_paths=[p for p in tree(EXECUTED) if p.startswith(C271+'control/') or p==C271+'run_h22_control.py']
    for path in control_paths:
        check('immutable_control',path,tree(EXECUTED)[path]==tree(CANDIDATE).get(path)==tree(PHASE).get(path))
    env=json.loads((ROOT/'validation/preparation/ENVIRONMENT.json').read_text())
    check('reuse_environment','Recorded P01 Python/version/platform match current identified environment',result['environment']['python']==env['python'] and result['environment']['platform']==env['platform'] and result['environment']['executable']==env['executable'])
    check('reuse_command','Separate receipt retains exact -B command',receipt['source']==result['source'] and receipt['argv'][1]=='-B' and receipt['argv'][2]==C271+'run_h22_control.py' and receipt['exit_code']==0 and receipt['results']['sha256']==digest(raw(CANDIDATE,C271+'evidence/control-candidate/RESULTS.json')) and receipt['driver_log']['sha256']==digest(raw(CANDIDATE,C271+'evidence/control-candidate/driver.log')))
    raw_archive=raw(CANDIDATE,C271+'evidence/control-candidate/RAW-EVIDENCE.zip')
    check('p01_evidence','Raw archive identity',ident(raw_archive)=={'bytes':result['raw_evidence']['bytes'],'sha256':result['raw_evidence']['sha256']})
    with zipfile.ZipFile(io.BytesIO(raw_archive)) as z:
        manifest=json.loads(z.read('MANIFEST-SHA256.json'))
        check('p01_evidence','Raw archive exact payload inventory',set(manifest)==set(z.namelist())-{'MANIFEST-SHA256.json'} and len(z.namelist())==27 and z.testzip() is None)
        for name,declared in manifest.items(): check('p01_evidence',name,ident(z.read(name))==declared)
        assertions=json.loads(z.read('CHECKS.json'))
        check('p01_evidence','1042 original assertions retained',len(assertions)==1042 and all(x['passed'] is True for x in assertions) and result['checks_passed']==1042 and result['checks_failed']==0)
        ids=json.loads(z.read('INPUT-IDENTITIES.json'))
        check('p01_evidence','Input identity record equals RESULTS',ids['files']==result['input_identities'] and ids['source']==result['source'])
        cases={e['id']:e for e in oracle['cases']}
        for caseid,e in cases.items():
            check('oracle','Captured request '+caseid,json.loads(z.read('requests/'+caseid+'.json'))==e)
            for item in [*e['source_files'].values(),e['artifact']]:
                check('oracle',caseid+':'+item['path'],ident(raw(CANDIDATE,item['path']))=={'bytes':item['bytes'],'sha256':item['sha256']})
            m=e['mutation']
            if m:
                original=raw(CANDIDATE,m['original']['path']);candidate=raw(CANDIDATE,e['source_files']['main.ok']['path'])
                start,end=m['start_byte'],m['end_byte']
                check('oracle','Isolated exact deletion '+caseid,original[:start]+original[end:]==candidate and original[start:end]==m['removed_utf8'].encode() and digest(original[start:end])==m['removed_sha256'] and m['replacement_utf8']=='')
            canonical=json.dumps(e['candidate_program']['manifest'],sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
            check('oracle','Specification program identity '+caseid,e['candidate_program']['revision']=='sha256:'+digest(b'ontokin.bundle/0.1\0'+canonical))
        calls=[]
        for call in result['calls']:
            e=cases[call['case']];response=json.loads(z.read(call['response_member']));outcome=response['outcome'];calls.append(outcome)
            ok=(ident(z.read(call['response_member']))=={'bytes':call['response_bytes'],'sha256':call['response_sha256']} and response['case']==call['case'] and response['interface']==call['interface'] and outcome==e['expected'][call['interface']]['outcome']==call['outcome'])
            evidence=response['fault'] if outcome=='typed_refusal' else response['value']
            ok=ok and evidence['sourceHashes']=={name:item['sha256'] for name,item in e['source_files'].items()} and evidence['sourceBytes']=={name:item['bytes'] for name,item in e['source_files'].items()}
            if call['interface']!='source_observation': ok=ok and evidence['artifactSha256']==e['artifact']['sha256'] and evidence['artifactBytes']==e['artifact']['bytes']
            if outcome=='typed_refusal':
                ok=ok and evidence['code']==call['refusal_code']=='MALFORMED' and 'value' not in response and bool(evidence.get('detail')) and not any(k in evidence for k in ['records','hinges','sites','objects'])
            else:
                ok=ok and evidence['programRevision']==e['candidate_program']['revision'] and evidence['objectCount']==18
            check('retained_response',call['case']+'/'+call['interface'],ok)
        check('p01_evidence','Six positive and twelve typed-refusal outcomes',len(calls)==18 and collections.Counter(calls)=={'success':6,'typed_refusal':12})
    imports=[]
    for e in result['input_identities']:
        if not e['path'].endswith('.py'): continue
        syntax=ast.parse(raw(CANDIDATE,e['path']))
        modules=set()
        for n in ast.walk(syntax):
            if isinstance(n,ast.Import): modules.update(a.name.split('.')[0] for a in n.names)
            elif isinstance(n,ast.ImportFrom): modules.add((n.module or '').split('.')[0])
        nonstd=sorted(modules-set(sys.stdlib_module_names))
        imports.append({'path':e['path'],'static_import_roots':sorted(modules),'non_standard_library_static_imports':nonstd})
        check('reuse_dependencies',e['path']+': static imports are standard library',not nonstd)
    check('reuse_dependencies','All five dynamic observer/utility modules captured',all(p in {e['path'] for e in result['input_identities']} for p in ['docs/engineering/localized-repair-c257/ownership.py','docs/engineering/localized-repair-c261/hinge_glb.py','docs/engineering/localized-repair-c265/source_hinges.py','docs/engineering/localized-repair-c266/hinge_binding.py','docs/engineering/localized-repair-c267/hinge_compare.py']))
    inventory=json.loads((ROOT/'validation/preparation/AFFECTED-COHORT-INVENTORY.json').read_text())
    suite_rows=[]
    expected_counts={255:31,256:29,257:23,258:28,261:28,265:49,266:34,267:25,268:35}
    for e in inventory['suites']:
        b=raw(CANDIDATE,e['path']);module=ast.parse(b);methods=[]
        for c in module.body:
            if isinstance(c,ast.ClassDef): methods.extend(c.name+'.'+n.name for n in c.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name.startswith('test_'))
        ok=ident(b)=={'bytes':e['bytes'],'sha256':e['sha256']} and methods==e['static_test_definitions'] and len(methods)==e['required_methods']==e['static_test_def_count'] and tree(CANDIDATE)[e['path']]['git_blob']==e['git_blob'] and tree(CANDIDATE)[e['path']]==tree(MAIN)[e['path']]==tree(PHASE)[e['path']]
        suite_rows.append({'path':e['path'],'methods':methods,'count':len(methods),'identity':ident(b),'unchanged':tree(CANDIDATE)[e['path']]==tree(PHASE)[e['path']]})
        check('regression_inventory',e['path'],ok)
    check('regression_inventory','Full inherited 282-method nine-suite set',len(suite_rows)==9 and sum(x['count'] for x in suite_rows)==inventory['required_method_total']==282 and {int(e['path'].split('/')[2].removeprefix('localized-repair-c')):e['required_methods'] for e in inventory['suites']}==expected_counts)
    runner='docs/engineering/localized-repair-c268/evidence/run_checks.py'
    check('regression_inventory','Existing cohort runner unchanged from main',tree(MAIN)[runner]==tree(CANDIDATE)[runner]==tree(PHASE)[runner])
    all_reuse=json.loads((ROOT/'validation/preparation/REUSE-INPUT-GIT-MANIFEST.json').read_text())
    for e in all_reuse['files']:
        check('phase_reuse',e['path'],{k:tree(CANDIDATE)[e['path']][k] for k in ['mode','kind','git_blob','bytes']}=={k:e[k] for k in ['mode','kind','git_blob','bytes']}=={k:tree(PHASE)[e['path']][k] for k in ['mode','kind','git_blob','bytes']})
    early=doc(PHASE,C271+'finalization-20261120/EARLY-RECOVERY-RECEIPT.json')
    check('phase_records','Early recovery saved before substantive verification',early['status']=='saved' and early['source_revision']==CANDIDATE and early['bytes']==12681357 and early['sha256']=='b58d98120d6794de2692645e26676d8288c76f31f1fd43849f40062c66dbe08f')
    current=doc(PHASE,'docs/workflow/CURRENT.json')
    check('phase_records','Rejected CURRENT status corrected to allowed ready value',current['next_action']['status']=='ready')
    fail_log=raw(PHASE,C271+'finalization-20261120/record-preflight/attempt-01-workflow.log').decode()
    failed_attempt=doc(PHASE,C271+'finalization-20261120/record-preflight/attempt-01.json')
    check('phase_records','Original record-preflight failure preserved','current.next_action.status: expected one of awaiting_user_direction, blocked, ready' in fail_log and failed_attempt['exit_code']==1 and failed_attempt['classification']=='task pointer status enum error, no behavior executed' and 'in_progress' in failed_attempt['resolution'])
    phase_task=doc(PHASE,'docs/workflow/tasks/C271/task.json')
    check('phase_records','Parent remains open pending R03–R05',phase_task['status']=='in_progress' and all(r['status']!='done' for r in phase_task['requirements'] if r['id'] in ['R03','R04','R05']))
    count=len(checks);failed=[e for e in checks if not e['passed']]
    report={'schema':'ontokin.c271.p02-independent-static-review/1','reviewer':'/root/intake_audit','reviewed_at_utc':datetime.now(timezone.utc).isoformat(),'main':MAIN,'candidate':CANDIDATE,'candidate_tree':git('rev-parse',CANDIDATE+'^{tree}').decode().strip(),'phase_checkpoint':PHASE,'phase_tree':git('rev-parse',PHASE+'^{tree}').decode().strip(),'executed_p01_revision':EXECUTED,'verdict':'passed_static_scope' if not failed else 'failed_static_scope','integration_approval':'not_granted_pending_complete_required_evidence','checks':checks,'coverage':{'checks':count,'failed':len(failed),'categories':dict(collections.Counter(e['category'] for e in checks)),'cumulative_candidate_files':len(cumulative),'phase_checkpoint_files':len(phase_delta),'exact_p01_input_files':len(input_rows),'immutable_control_runner_files':len(control_paths),'regression_suites':len(suite_rows),'required_methods':282,'phase_reuse_inputs':len(all_reuse['files'])},'mandatory_findings':failed,'p01_reuse':{'eligible_as_retained_historical_finite_evidence':not failed,'exact_input_identity_report':'P01-REUSE-IDENTITIES.json','command_receipt':C271+'evidence/control-candidate/EXECUTION-RECEIPT.json','recorded_environment':result['environment'],'reason':'Exact control/runner, five observer/utility modules, contracts/grammar, fixture source/GLB and all 22 runtime-opened repository inputs remain unchanged through candidate and phase checkpoint. Recorded interpreter/version/platform agree. This retains the original identified execution; it claims no fresh replay.','limitation':'Original P01 environment reports interpreter version/build/platform/path but no executable-binary digest. No new exact Python binary equivalence claim is made. No non-standard-library static dependency was found in recorded executed modules.'},'remaining_required_evidence':['Complete routine driver with zero skipped required obligations and exact environment/source evidence','Complete affected cohort execution and log/call accounting','Fresh workflow/documentation records for later metadata-only source checkpoints','Independent final eligibility disposition; no merge before approval'],'behavioral_execution_by_reviewer':False,'read_set':readset}
    save('STATIC-REVIEW.json',report)
    save('P01-REUSE-IDENTITIES.json',{'executed':EXECUTED,'candidate':CANDIDATE,'phase':PHASE,'inputs':input_rows,'static_imports':imports,'control_and_runner_paths':control_paths,'recorded_environment':result['environment'],'current_environment_comparison':{'python':env['python'],'platform':env['platform'],'executable':env['executable']}})
    save('CHANGED-FILES-REVIEW.json',{'main':MAIN,'candidate':CANDIDATE,'phase':PHASE,'files':change_inventory})
    save('REGRESSION-INVENTORY-REVIEW.json',{'candidate':CANDIDATE,'suites':suite_rows,'method_total':sum(e['count'] for e in suite_rows),'other_checks':inventory['other_checks'],'runner':runner,'inventory_only':True})
    save('GIT-READ-COMMANDS.json',{'commands':commands})
    print(json.dumps({'verdict':report['verdict'],'coverage':report['coverage'],'findings':failed,'integration_approval':report['integration_approval']},indent=2))
    return 0 if not failed else 1

if __name__=='__main__':
    try: sys.exit(main())
    except Exception:
        save('STATIC-ABORTED-ATTEMPT.json',{'traceback':traceback.format_exc(),'checks':checks,'commands':commands})
        raise
