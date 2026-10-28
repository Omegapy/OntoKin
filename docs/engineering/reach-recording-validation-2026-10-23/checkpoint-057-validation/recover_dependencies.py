from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path,PurePosixPath
from datetime import datetime,timezone
import json,hashlib,urllib.request,time,os,sys
ROOT=Path('/workspace/scratch/813fb8a53b1a'); SNAP=ROOT/'snapshot'; LOG=ROOT/'reviews/evidence'
private=LOG/'private-transport-all.json'; os.chmod(private,0o600)
transport=json.loads(private.read_text())['entries']; plan=json.loads((LOG/'dependency-plan.json').read_text())
expected={x['path']:x for x in plan['needed']}
start=datetime.now(timezone.utc).isoformat(); started=time.monotonic()
def fetch(path):
    e=expected[path]; x=transport[path]
    assert e['sha']==x['sha'] and e['size']==x['size'] and x['type']=='file'
    rel=PurePosixPath(path);assert not rel.is_absolute() and '..' not in rel.parts
    p=SNAP/path
    if p.exists():b=p.read_bytes();origin='already_present_exact'
    else:
        with urllib.request.urlopen(x['download_url'],timeout=45) as response:b=response.read(e['size']+1)
        origin='downloaded_exact'
    h=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
    assert len(b)==e['size'] and h==e['sha'],path
    if not p.exists():p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
    return {'path':path,'status':origin,'bytes':len(b),'git_blob':h,'mode':e['mode'],'sha256':hashlib.sha256(b).hexdigest()}
records=[];failed=[]
with (LOG/'dependency-recovery-results.jsonl').open('w') as log:
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures={pool.submit(fetch,p):p for p in sorted(expected)}
        for f in as_completed(futures):
            path=futures[f]
            try:r=f.result();records.append(r)
            except Exception as e:r={'path':path,'status':'failed','exception':type(e).__name__,'detail':str(e).split('http')[0]};failed.append(r)
            log.write(json.dumps(r)+'\n');log.flush()
            if (len(records)+len(failed))%100==0:print(json.dumps({'exact':len(records),'failed':len(failed),'total':len(expected)}),flush=True)
result={'source_commit':'8287be55a21c28320aa11895cadd29c68ae18f90','scope':'Exact byte recovery for documentation dependencies only; no archive extraction or product import','start_utc':start,'duration_seconds':time.monotonic()-started,'python':sys.version,'files':len(records),'bytes':sum(r['bytes'] for r in records),'failed':failed,'inputs':sorted(records,key=lambda x:x['path'])}
(LOG/'dependency-recovery-summary.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('inputs',)}),flush=True)
raise SystemExit(bool(failed))
