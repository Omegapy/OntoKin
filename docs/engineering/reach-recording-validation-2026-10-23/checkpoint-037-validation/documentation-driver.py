import hashlib
import json
import pathlib
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone

root = pathlib.Path('/workspace/scratch/76d468ef8f7e/OntoKin')
out = pathlib.Path('/workspace/scratch/76d468ef8f7e/c037-validation/documentation-001')
out.mkdir(parents=True, exist_ok=False)
def git(*args):
    return subprocess.check_output(['git', '-C', str(root), *args])
def utc():
    return datetime.now(timezone.utc).isoformat()
def sha(data):
    return hashlib.sha256(data).hexdigest()
def write(name, value):
    (out/name).write_text(json.dumps(value, indent=2)+'\n')
def snapshot():
    rows=[]
    for name in sorted(p for p in git('ls-files','-z').decode().split('\0') if p):
        p=root/name
        b=p.read_bytes()
        rows.append({'path':name,'bytes':len(b),'sha256':sha(b),
                     'mode':'100755' if p.stat().st_mode & 0o111 else '100644'})
    return rows
head=git('rev-parse','HEAD').decode().strip()
tree=git('rev-parse','HEAD^{tree}').decode().strip()
assert head=='ac1568b6d511b3d4fbb698314dc2bf57c1950627'
assert tree=='83bd04dc06258769a76769da40f24166d78f60c3'
assert not git('status','--porcelain')
before=snapshot()
inventory_bytes=(json.dumps(before,sort_keys=True,separators=(',',':'))+'\n').encode()
(out/'inputs.json').write_bytes(inventory_bytes)
command=[sys.executable,'docs/maintenance/reorganization-2026-10-17/verify_reorganization.py']
started=utc(); clock=time.monotonic()
with (out/'stdout.json').open('xb') as stdout, (out/'stderr.txt').open('xb') as stderr:
    proc=subprocess.run(command,cwd=root,stdout=stdout,stderr=stderr)
elapsed=time.monotonic()-clock; finished=utc()
after=snapshot()
after_bytes=(json.dumps(after,sort_keys=True,separators=(',',':'))+'\n').encode()
clean=not git('status','--porcelain')
same=before==after and head==git('rev-parse','HEAD').decode().strip() and tree==git('rev-parse','HEAD^{tree}').decode().strip() and clean
stdout=(out/'stdout.json').read_bytes(); stderr=(out/'stderr.txt').read_bytes()
summary=json.loads(stdout)
result={'schema_version':'ontokin.checkpoint037-documentation/0.1',
 'status':'passed' if proc.returncode==0 and same and summary['status']=='passed' else 'failed',
 'command':command,'working_directory':str(root),'started_at_utc':started,'finished_at_utc':finished,
 'exit_code':proc.returncode,'elapsed_seconds':elapsed,'source_commit':head,'source_tree':tree,
 'source_clean_before':True,'source_clean_after':clean,'complete_inputs_stable':same,
 'input_file_count':len(before),'input_bytes':sum(x['bytes'] for x in before),
 'before_inventory_sha256':sha(inventory_bytes),'after_inventory_sha256':sha(after_bytes),
 'input_inventory':'inputs.json','after_comparison':'Actual full named before/after arrays compared exactly; identical after array is represented by the same inventory plus its independently computed hash.',
 'stdout':{'path':'stdout.json','bytes':len(stdout),'sha256':sha(stdout)},
 'stderr':{'path':'stderr.txt','bytes':len(stderr),'sha256':sha(stderr)},
 'interpreter':{'version':sys.version,'executable':sys.executable,'executable_sha256':sha(pathlib.Path(sys.executable).resolve().read_bytes()),'platform':platform.platform()},
 'summary':{k:v for k,v in summary.items() if k!='sources'},
 'product_requests':0,'runtime_test_methods':0,'runtime_acceptance_claimed':False}
write('result.json',result)
print(json.dumps(result,indent=2))
raise SystemExit(0 if result['status']=='passed' else 1)
