"""Record documentation/metadata commands without importing OntoKin."""
from pathlib import Path
import datetime, hashlib, json, platform, subprocess, sys

ROOT=Path(__file__).resolve().parents[4]
AREA=Path(__file__).resolve().parents[1]
VALIDATION=Path(__file__).resolve().parent
PREFIX=AREA.relative_to(ROOT).as_posix()+'/'

def utc(): return datetime.datetime.now(datetime.timezone.utc).isoformat()

def inputs():
    rows=[]
    for p in sorted(ROOT.rglob('*')):
        if not p.is_file(): continue
        rel=p.relative_to(ROOT).as_posix()
        if '__pycache__' in p.parts: continue
        if rel in {PREFIX+'checkpoint-054-validation.json',PREFIX+'checkpoint-054.json'}: continue
        if rel.startswith(PREFIX+'checkpoint-054-validation/documentation-') or rel.startswith(PREFIX+'checkpoint-054-validation/metadata-'): continue
        b=p.read_bytes()
        rows.append({'path':rel,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'git_blob':hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()})
    return rows

name=sys.argv[1]
if name.startswith('documentation-'):
    command=[sys.executable,'docs/maintenance/reorganization-2026-10-17/verify_reorganization.py']
elif name.startswith('metadata-'):
    command=[sys.executable,str((VALIDATION/'verify_metadata.py').relative_to(ROOT))]
else: raise ValueError('Unknown validation role')
out=VALIDATION/name
if out.exists(): raise ValueError('Validation attempt already exists')
out.mkdir()
before=inputs(); start=utc()
record={'schema':'ontokin.checkpoint054-command/0.1','name':name,'source_parent_commit':'6f6e16f2e26ac1885e5675a9d931ba385304e63c','source_parent_tree':'2d6857bb63bf84dff0f27976fb6da29487a4f05c','cwd_policy':'isolated exact partial parent source plus only new C054 evidence','command':command,'start_utc':start,'interpreter':sys.version,'executable':sys.executable,'platform':platform.platform(),'input_policy':'All materialized inputs except validation command-output directories and the two later summary records; every excluded summary is postprocessed evidence, not tested product source.','input_manifest':'input-manifest.json','input_files':len(before)}
(out/'input-manifest.json').write_text(json.dumps(before,indent=2)+'\n')
process=subprocess.run(command,cwd=ROOT,capture_output=True)
(out/'stdout.txt').write_bytes(process.stdout); (out/'stderr.txt').write_bytes(process.stderr)
after=inputs(); record.update({'end_utc':utc(),'exit_code':process.returncode,'stable_inputs':before==after})
if before!=after:
    (out/'input-manifest-after.json').write_text(json.dumps(after,indent=2)+'\n')
try: result=json.loads(process.stdout)
except (UnicodeError,json.JSONDecodeError): result={'status':'unparseable-output','exit_code':process.returncode}
(out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
record['reported_status']=result.get('status')
(out/'command.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'name':name,'exit_code':process.returncode,'stable_inputs':record['stable_inputs'],'input_files':len(before),'status':result.get('status'),'sources_verified':result.get('sources_verified'),'sections_verified':result.get('sections_verified'),'links':result.get('links'),'grouped_checks':result.get('grouped_checks'),'failures':result.get('failures',[])},indent=2))
sys.exit(process.returncode if before==after else 2)
