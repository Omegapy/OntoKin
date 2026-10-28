"""Run only the named documentation or metadata check with exact stable inputs."""
from __future__ import annotations
import datetime
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
EVIDENCE=HERE.parent
ROOT=EVIDENCE.parents[2]
kind=sys.argv[1]
if kind not in ('documentation','metadata'):raise ValueError('unsupported validation kind')
out=HERE/(kind+'-001')
if out.exists():raise FileExistsError('attempt already exists; retain and choose explicit new attempt')
out.mkdir()
excluded_prefix='docs/engineering/reach-recording-validation-2026-10-23/checkpoint-055-validation/'
summary_names={'checkpoint-055.json','checkpoint-055-validation.json'}

def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def snapshot():
    rows=[]
    for path in sorted(ROOT.rglob('*')):
        if not path.is_file():continue
        rel=path.relative_to(ROOT).as_posix()
        if path.name in summary_names:continue
        if rel.startswith(excluded_prefix) and any(x in path.parts for x in ('documentation-001','metadata-001')):continue
        data=path.read_bytes()
        rows.append({'path':rel,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    return rows

before=snapshot()
(out/'input-manifest.json').write_text(json.dumps(before,indent=2)+'\n')
target='docs/maintenance/reorganization-2026-10-17/verify_reorganization.py' if kind=='documentation' else 'docs/engineering/reach-recording-validation-2026-10-23/checkpoint-055-validation/verify_metadata.py'
cmd=[sys.executable,target]
record={'schema':'ontokin.checkpoint055-validation-command/0.1','kind':kind,'command':cmd,'cwd':str(ROOT),'source_commit':'2aca5afb05a0320971ccaf9d9ce30904d120e249','source_tree':'7082ceb840e0ce4c2f30baccbdb527913e9fa2ca','snapshot':'partial exact pinned source plus C055 evidence additions; no synthetic Git commit','interpreter':sys.version,'platform':platform.platform(),'started_utc':stamp(),'inputs':len(before),'excluded':'This attempt output directory, the other C055 validation output directory, and the two postprocessed checkpoint/validation summaries.'}
(out/'command.json').write_text(json.dumps(record,indent=2)+'\n')
started=time.monotonic()
proc=subprocess.run(cmd,cwd=ROOT,capture_output=True,timeout=120)
(out/'stdout.txt').write_bytes(proc.stdout)
(out/'stderr.txt').write_bytes(proc.stderr)
after=snapshot()
changes=[]
a={i['path']:i for i in before};b={i['path']:i for i in after}
for path in sorted(a.keys()|b.keys()):
    if a.get(path)!=b.get(path):changes.append(path)
try:actual=json.loads(proc.stdout)
except Exception:actual=None
result={'schema':'ontokin.checkpoint055-validation-run/0.1','kind':kind,'finished_utc':stamp(),'duration_seconds':time.monotonic()-started,'exit_code':proc.returncode,'inputs':len(before),'inputs_stable':not changes,'changed_inputs':changes,'passed':proc.returncode==0 and not changes,'stdout_sha256':hashlib.sha256(proc.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(proc.stderr).hexdigest(),'actual_result':actual,'product_execution':False}
(out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='actual_result'},indent=2))
raise SystemExit(0 if result['passed'] else 1)
