"""Independent CLI transport checks using independently built inert records."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from independent_controls import make_case

base=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--repo',type=Path,required=True)
args=parser.parse_args()
repo=args.repo.resolve()
source=repo/'docs/engineering/localized-repair-c255/oracle.py'
observed,authority=make_case(repo,'V1')
encoded=copy.deepcopy(authority)
for part in ('start','candidate','retained','rebuild'):
 for field in ('sourceFiles','artifacts'):
  encoded[part][field]={k:{'encoding':'hex','data':v.hex()} for k,v in encoded[part][field].items()}
results=[]
with tempfile.TemporaryDirectory(prefix='cli-controls-',dir=base) as directory:
 root=Path(directory)
 for case in ('positive','hash-only-authority','duplicate-observation-key','nonfinite-observation'):
  op=root/'observation.json';ap=root/'authority.json'
  body=json.dumps(observed,allow_nan=False)
  auth=copy.deepcopy(encoded)
  if case=='hash-only-authority':auth['retained']['sourceFiles']['main.ok']='0'*64
  if case=='duplicate-observation-key':body='{"schema":"duplicate",'+body[1:]
  if case=='nonfinite-observation':
   obs=copy.deepcopy(observed);obs['poses'][0]['time_s']=float('nan');body=json.dumps(obs)
  op.write_text(body);ap.write_text(json.dumps(auth))
  command=[sys.executable,'-IB',str(source),'--repo',str(repo),'--case','V1','--observation',str(op),'--authority',str(ap)]
  run=subprocess.run(command,capture_output=True,text=True,timeout=30)
  result=json.loads(run.stdout)
  wanted=case=='positive'
  results.append({'case':case,'exitCode':run.returncode,'result':result,'passed':(run.returncode==0)==wanted and result['componentPass'] is wanted and result.get('realTrialSuccess') is None and result.get('executionAllowed') is False,'stderr':run.stderr})
record={'oracleSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'results':results,'passed':all(x['passed'] for x in results)}
(base/'cli-control-results.json').write_text(json.dumps(record,indent=2))
print(json.dumps({'passed':record['passed'],'controls':len(results),'failures':[r for r in results if not r['passed']]}))
