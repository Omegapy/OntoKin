"""Run only the workflow, documentation and whitespace gates for documentary changes."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

BASE=Path('/workspace/scratch/aa6113404163')
REPO=BASE/'OntoKin'
parser=argparse.ArgumentParser()
parser.add_argument('label')
parser.add_argument('--base',default='527368bd5195c439762b43e2cc836ff9822213f8')
parser.add_argument('--published',action='store_true')
parser.add_argument('--preserved-eof',type=Path)
args=parser.parse_args()
output=BASE/'phase-p22/checks'/args.label
output.mkdir(parents=True,exist_ok=False)
commands=[('workflow',[sys.executable,'-B','tools/chat_workflow.py','check']),
          ('documentation',[sys.executable,'-B','docs/maintenance/reorganization-2026-10-17/verify_reorganization.py']),
          ('whitespace',['git','diff','--check',args.base,'HEAD'] if args.published else ['git','diff','--cached','--check'])]
exceptions=[]
if args.preserved_eof:
    disposition=json.loads(args.preserved_eof.read_text())
    exceptions=[row['repository_path'] for row in disposition['excluded_files']]
    for row in disposition['excluded_files']:
        data=(REPO/row['repository_path']).read_bytes()
        assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
    basecmd=['git','diff','--check',args.base,'HEAD'] if args.published else ['git','diff','--cached','--check']
    commands.append(('authored_whitespace',basecmd+['--','.']+[':(exclude)'+name for name in exceptions]))
def now():return datetime.now(timezone.utc).isoformat()
def describe(path):
    data=path.read_bytes();return {'path':str(path),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
def run(item):
    name,command=item
    stdout=output/(name+'.stdout.log');stderr=output/(name+'.stderr.log')
    row={'name':name,'command':command,'cwd':str(REPO),'started_at_utc':now()}
    with stdout.open('xb') as out,stderr.open('xb') as err:
        result=subprocess.run(command,cwd=REPO,stdout=out,stderr=err,timeout=120)
    row.update(exit_code=result.returncode,finished_at_utc=now(),stdout=describe(stdout),stderr=describe(stderr))
    return row
with ThreadPoolExecutor(max_workers=3) as pool:
    results=list(pool.map(run,commands))
result={'schema':'ontokin.c271.p22-record-checks/1','label':args.label,
        'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
        'index_tree':subprocess.check_output(['git','write-tree'],cwd=REPO,text=True).strip(),
        'published':args.published,'checks':results,'all_passed':all(row['exit_code']==0 for row in results),
        'scope':'Workflow/documentation/full selected delta whitespace only. No H0/H1, product tests or full routine.'}
if exceptions:
    full=next(row for row in results if row['name']=='whitespace')
    lines=Path(full['stdout']['path']).read_text().splitlines()
    matches=[re.fullmatch(r'(.+):(\d+): new blank line at EOF\.',line) for line in lines]
    exact=all(matches) and {m.group(1) for m in matches}==set(exceptions) and len(lines)==len(exceptions)
    result['preserved_eof_disposition']={'path':str(args.preserved_eof),'sha256':hashlib.sha256(args.preserved_eof.read_bytes()).hexdigest(),
        'full_failed_output_matches_exact_evidence_only_exceptions':exact,'excluded_files':exceptions}
    result['required_gates_passed']=exact and all(row['exit_code']==0 for row in results if row['name']!='whitespace')
    result['scope']=f'Workflow/documentation and strict authored-payload whitespace; full whitespace remains explicitly failed only for {len(exceptions)} exact byte-preserved review EOFs. No product or full routine.'
(output/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'label':args.label,'all_passed':result['all_passed'],'required_gates_passed':result.get('required_gates_passed',result['all_passed']),'checks':[{k:row[k] for k in ['name','exit_code']} for row in results],'head':result['head'],'index_tree':result['index_tree']}))
sys.exit(0 if result.get('required_gates_passed',result['all_passed']) else 1)
