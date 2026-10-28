#!/usr/bin/env python3
"""Execute only C058 documentation and metadata checks with stable-input receipts."""
from __future__ import annotations
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
REL=HERE.relative_to(ROOT).as_posix()
EXCLUDED={REL.rsplit('/',1)[0]+'/checkpoint-058.json',REL.rsplit('/',1)[0]+'/checkpoint-058-validation.json'}

def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def dump(p,v): p.write_text(json.dumps(v,indent=2)+'\n')
def inputs():
    rows=[]
    for p in sorted(ROOT.rglob('*')):
        if not p.is_file(): continue
        rel=p.relative_to(ROOT).as_posix()
        under=p.relative_to(HERE).parts if p.is_relative_to(HERE) else ()
        if rel in EXCLUDED or (len(under)>1 and under[0].startswith(('documentation-','metadata-'))): continue
        b=p.read_bytes()
        rows.append({'path':rel,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'git_blob':hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest(),'mode':oct(p.stat().st_mode & 0o777)})
    return rows

ap=argparse.ArgumentParser()
ap.add_argument('--source-commit',required=True)
ap.add_argument('--source-tree',required=True)
ap.add_argument('--attempt',default='001')
args=ap.parse_args()
results=[]
commands=[('documentation',[sys.executable,str(ROOT/'docs/maintenance/reorganization-2026-10-17/verify_reorganization.py')]),('metadata',[sys.executable,str(HERE/'audit_metadata.py')])]
for name,command in commands:
    out=HERE/f'{name}-{args.attempt}'
    out.mkdir(exist_ok=False)
    before=inputs()
    dump(out/'inputs-before.json',before)
    record={'schema':'ontokin.checkpoint058-command/0.1','source_commit':args.source_commit,'source_tree':args.source_tree,'workspace':'Exact partial snapshot plus all candidate additions; no synthetic Git commit','cwd':str(ROOT),'argv':command,'started_at':now(),'python':sys.version,'python_executable':sys.executable,'platform':platform.platform(),'excluded_self_outputs':['checkpoint-058-validation/documentation-*','checkpoint-058-validation/metadata-*'],'excluded_postprocessed_summaries':sorted(EXCLUDED),'product_execution_selected':False}
    dump(out/'command.json',record)
    started=time.monotonic()
    with (out/'stdout.txt').open('wb') as stdout,(out/'stderr.txt').open('wb') as stderr:
        completed=subprocess.run(command,cwd=ROOT,stdout=stdout,stderr=stderr,check=False)
    after=inputs();dump(out/'inputs-after.json',after)
    stable=before==after
    try: parsed=json.loads((out/'stdout.txt').read_text())
    except Exception: parsed=None
    result={'schema':'ontokin.checkpoint058-command-result/0.1','ended_at':now(),'elapsed_seconds':time.monotonic()-started,'exit_code':completed.returncode,'inputs':len(before),'inputs_stable':stable,'parsed_result':parsed,'status':'passed' if completed.returncode==0 and stable and parsed and parsed.get('status')=='passed' else 'failed'}
    dump(out/'result.json',result)
    results.append({'check':name,**{k:result[k] for k in ('status','exit_code','inputs','inputs_stable','elapsed_seconds')}})
    print(json.dumps(results[-1]),flush=True)
    if result['status']!='passed': break
sys.exit(0 if len(results)==2 and all(x['status']=='passed' for x in results) else 1)
