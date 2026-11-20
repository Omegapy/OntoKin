from pathlib import Path
import argparse
import datetime as dt
import hashlib
import json
import platform
import subprocess
import sys

p=argparse.ArgumentParser();p.add_argument('--repo',required=True);p.add_argument('--output',required=True);p.add_argument('--phase',required=True);a=p.parse_args()
r=Path(a.repo).resolve();out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=True)
def git(*args):return subprocess.check_output(['git',*args],cwd=r,text=True).strip()
revision=git('rev-parse','HEAD');tree=git('rev-parse','HEAD^{tree}');before=git('status','--porcelain','--untracked-files=no')
assert not before,'Checks require an identified clean tracked candidate.'
checks=[]
commands=[('workflow',[sys.executable,'-B','tools/chat_workflow.py','check']),('documentation',[sys.executable,'-B','docs/maintenance/reorganization-2026-10-17/verify_reorganization.py'])]
for name,cmd in commands:
    start=dt.datetime.now(dt.timezone.utc).isoformat()
    result=subprocess.run(cmd,cwd=r,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    path=out/(name+'.log');path.write_bytes(result.stdout)
    checks.append({'name':name,'command':cmd,'started_at_utc':start,'finished_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'result':'passed' if result.returncode==0 else 'failed','exit_code':result.returncode,'log':{'path':path.name,'bytes':len(result.stdout),'sha256':hashlib.sha256(result.stdout).hexdigest()}})
    print(name,checks[-1]['result'])
after=git('status','--porcelain','--untracked-files=no');assert before==after
runner=Path(__file__).resolve();runner_bytes=runner.read_bytes()
report={'runner':{'path':str(runner),'bytes':len(runner_bytes),'sha256':hashlib.sha256(runner_bytes).hexdigest()},'schema':'ontokin.c269.document-checks/1','phase':a.phase,'source_revision':revision,'source_tree':tree,'source_clean':True,'environment':{'python':sys.version,'platform':platform.platform()},'checks':checks,'result':'passed' if all(x['exit_code']==0 for x in checks) else 'failed','limits':['Documentation/workflow evidence only','No behavioral cohort or product/native/model/compatibility test executed']}
(out/'CHECKS.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'phase':a.phase,'revision':revision,'result':report['result'],'output':str(out)}))
raise SystemExit(0 if report['result']=='passed' else 1)
