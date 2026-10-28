"""Record actual pure documentation/metadata runs and before/after input hashes."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import platform
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
EVIDENCE=HERE.parent

def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def inventory():
    rows=[]
    for p in sorted(ROOT.rglob('*')):
        if not p.is_file() or '__pycache__' in p.parts:continue
        rel=p.relative_to(ROOT).as_posix()
        if any(part.startswith(('documentation-','metadata-')) for part in p.relative_to(HERE).parts) if p.is_relative_to(HERE) else False:continue
        if p in {EVIDENCE/'checkpoint-056-validation.json',EVIDENCE/'checkpoint-056.json'}:continue
        b=p.read_bytes();rows.append({'path':rel,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
    return rows

ap=argparse.ArgumentParser();ap.add_argument('kind',choices=['documentation','metadata']);ap.add_argument('--attempt',default='001');args=ap.parse_args()
out=HERE/(args.kind+'-'+args.attempt);out.mkdir(exist_ok=False)
command=[sys.executable,'docs/maintenance/reorganization-2026-10-17/verify_reorganization.py'] if args.kind=='documentation' else [sys.executable,str(HERE/'verify_metadata.py')]
before=inventory();(out/'input-manifest.json').write_text(json.dumps(before,indent=2)+'\n')
record={'command':command,'cwd':str(ROOT),'start_utc':now(),'python':sys.version,'executable':sys.executable,'platform':platform.platform(),'source_parent_commit':'8000959ad25e89d1794d1401c0f8c2960bcd18fc','source_parent_tree':'5282f90bc12c321c67829ce6d7ce62c891b32424','validation_identity':'Exact identified local original inputs plus reviewed uncommitted C056 documentation; no future publication identity assumed.','input_count':len(before),'summary_exclusions':['checkpoint-056-validation.json','checkpoint-056.json'],'receipt_directories_excluded':True,'product_execution':False}
(out/'command.json').write_text(json.dumps(record,indent=2)+'\n')
start=time.monotonic()
with (out/'stdout.txt').open('wb') as stdout,(out/'stderr.txt').open('wb') as stderr:
    try:
        proc=subprocess.run(command,cwd=ROOT,stdout=stdout,stderr=stderr,timeout=120)
        code=proc.returncode;failure=None
    except subprocess.TimeoutExpired as e:
        code=None;failure=type(e).__name__
after=inventory()
result={'command':command,'start_utc':record['start_utc'],'end_utc':now(),'elapsed_seconds':time.monotonic()-start,'exit_code':code,'failure':failure,'input_count':len(before),'inputs_stable':before==after,'status':'passed' if code==0 and before==after else 'failed','product_execution':False}
try:result['command_result']=json.loads((out/'stdout.txt').read_text())
except Exception:pass
(out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='command_result'},indent=2))
raise SystemExit(result['status']!='passed')
