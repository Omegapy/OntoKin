#!/usr/bin/env python3
"""Retain actual independent final-audit process receipts and raw streams."""
import hashlib
import json
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
B=Path('/workspace/scratch/f34f66f87e3e');O=B/'c047-final-review'
def desc(p):
    d=p.read_bytes();return {'path':str(p.relative_to(B)),'bytes':len(d),'sha256':hashlib.sha256(d).hexdigest()}
now=lambda:datetime.now(timezone.utc).isoformat()
script=O/'audit_core.py';cmd=[sys.executable,str(script)]
receipt={'command':cmd,'cwd':str(B),'started_utc':now(),'python':sys.version,'executable':sys.executable,'platform':platform.platform(),'window_comment_id':6428329816,'window_expires_utc':'2026-10-26T22:19:09Z','script_before':desc(script),'product_imported_or_executed':False,'archive_extraction':False}
t=time.perf_counter()
with (O/'audit.stdout').open('wb') as out,(O/'audit.stderr').open('wb') as err:
    p=subprocess.run(cmd,cwd=B,stdout=out,stderr=err)
receipt.update({'exit_code':p.returncode,'finished_utc':now(),'wall_seconds':time.perf_counter()-t,'script_after':desc(script),'stdout':desc(O/'audit.stdout'),'stderr':desc(O/'audit.stderr')})
if (O/'result.json').exists():
    r=json.loads((O/'result.json').read_text());receipt.update({'result':desc(O/'result.json'),'inputs_stable':r['inputs_stable'],'input_files':r['input_files']})
(O/'command.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
sys.exit(p.returncode)
