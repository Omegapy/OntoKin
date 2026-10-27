"""Record one exclusive C052 documentation or metadata validation attempt."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import platform
import subprocess
import sys
import time

root=Path(__file__).resolve().parents[4]
d=Path(__file__).resolve().parents[1]
role,attempt=sys.argv[1:]
if role not in {'documentation','metadata'}: raise ValueError('Unsupported source-validation role')
out=d/'checkpoint-052-validation'/attempt
out.mkdir(parents=True,exist_ok=False)
def record(p):
    b=p.read_bytes()
    return {'path':p.relative_to(root).as_posix(),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
files=[p for p in sorted(root.rglob('*')) if p.is_file() and not p.is_relative_to(out)]
before=[record(p) for p in files]
(out/'input-manifest.json').write_text(json.dumps(before,indent=2)+'\n')
command=[sys.executable,'docs/maintenance/reorganization-2026-10-17/verify_reorganization.py'] if role=='documentation' else [sys.executable,str((d/'checkpoint-052-validation/verify_metadata.py').relative_to(root))]
started=datetime.now(timezone.utc).isoformat(); t0=time.monotonic()
error=None;code=None
try:
    with (out/'stdout.txt').open('wb') as stdout,(out/'stderr.txt').open('wb') as stderr:
        p=subprocess.run(command,cwd=root,stdout=stdout,stderr=stderr,timeout=60)
    code=p.returncode
except BaseException as e:
    error={'type':type(e).__name__,'message':str(e)}
ended=datetime.now(timezone.utc).isoformat()
after=[record(p) if p.is_file() else {'path':p.relative_to(root).as_posix(),'missing':True} for p in files]
changed=[a['path'] for a,b in zip(before,after) if a!=b]
try: data=json.loads((out/'stdout.txt').read_text())
except (OSError,ValueError): data={'status':'failed','failures':['No complete JSON result'],'error':error}
(out/'result.json').write_text(json.dumps(data,indent=2)+'\n')
meta={'schema':'ontokin.checkpoint052-command/0.1','role':role,'command':command,'cwd':str(root),'started_utc':started,'ended_utc':ended,'elapsed_seconds':time.monotonic()-t0,'exit_code':code,'error':error,'python':sys.version,'platform':platform.platform(),'input_count':len(before),'changed_inputs':changed,'input_manifest':'input-manifest.json','stdout':'stdout.txt','stderr':'stderr.txt','result':'result.json','product_import':False,'driver':{'path':'../run_validation.py','sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}}
(out/'command.json').write_text(json.dumps(meta,indent=2)+'\n')
print(json.dumps({'role':role,'attempt':attempt,'exit_code':code,'status':data.get('status'),'stable_inputs':len(before) if not changed else None,'changed_inputs':changed,'summary':data.get('links',{'grouped_checks':data.get('grouped_checks')}),'failures':data.get('failures',[])}))
sys.exit(0 if code==0 and not changed else 1)
