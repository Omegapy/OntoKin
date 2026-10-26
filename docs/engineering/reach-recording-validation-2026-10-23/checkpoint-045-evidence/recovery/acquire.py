#!/usr/bin/env python3
"""Recover exact published repository blobs without importing product code."""
import concurrent.futures, datetime, hashlib, json, os, pathlib, sys, urllib.request
root = pathlib.Path('/workspace/scratch/bd03c06e866f/ontokin')
meta = pathlib.Path('/workspace/scratch/bd03c06e866f/c045-meta/recovery')
meta.mkdir(parents=True, exist_ok=True)
source = pathlib.Path(sys.argv[1])
items = json.loads(source.read_text())
tree = json.loads(pathlib.Path('/workspace/scratch/bd03c06e866f/c045-meta/parent-tree.json').read_text())
expected = {x['path']:x for x in tree['tree'] if x['type']=='blob'}
def one(x):
    rel=x['path']; e=expected[rel]; p=root/rel
    out={'path':rel, 'expected_blob':e['sha'], 'expected_size':e['size'], 'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    try:
        if p.exists():
            b=p.read_bytes(); state='existing'
        else:
            request=urllib.request.Request(x['download_url'],headers={'User-Agent':'OntoKin-source-recovery'})
            with urllib.request.urlopen(request,timeout=40) as response: b=response.read()
            state='downloaded'
        h=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
        assert h==e['sha'] and len(b)==e['size'], 'source identity mismatch'
        if state=='downloaded':
            p.parent.mkdir(parents=True,exist_ok=True)
            with p.open('xb') as f:f.write(b)
            p.chmod(int(e['mode'][-3:],8))
        out.update(status='passed', acquisition=state, bytes=len(b), blob=h, sha256=hashlib.sha256(b).hexdigest(), mode=oct(p.stat().st_mode & 0o777))
    except BaseException as error:
        out.update(status='failed',error_type=type(error).__name__,error_detail='redacted to avoid URL disclosure')
    out['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    return out
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
    results=list(pool.map(one,items))
receipt=meta/(sys.argv[2]+'.json')
receipt.write_text(json.dumps({'parent':'91e8899ad90f04292dd4aee5aaec8b730b397d45','items':results},indent=2)+'\n')
print(json.dumps({'receipt':str(receipt),'passed':sum(x['status']=='passed' for x in results),'failed':sum(x['status']=='failed' for x in results),'bytes':sum(x.get('bytes',0) for x in results),'failures':[{'path':x['path'],'type':x['error_type']} for x in results if x['status']=='failed']}))

