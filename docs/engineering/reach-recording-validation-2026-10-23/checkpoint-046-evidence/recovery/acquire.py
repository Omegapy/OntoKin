#!/usr/bin/env python3
"""Acquire only exact remote C045 blobs. Never import or execute product code."""
import concurrent.futures, datetime, hashlib, json, pathlib, sys, urllib.request
ROOT=pathlib.Path('/workspace/scratch/fd65650eb54f/OntoKin')
META=pathlib.Path('/workspace/scratch/fd65650eb54f/c046-recovery')
EXPECTED={x['path']:x for x in json.loads((META/'remote-tree.json').read_text())['tree'] if x['type']=='blob'}
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def one(item):
    rel=item['path'];expected=EXPECTED[rel];path=ROOT/rel
    out={'path':rel,'expected_blob':expected['sha'],'expected_bytes':expected['size'],'started_utc':now()}
    try:
        if path.exists():
            data=path.read_bytes();how='existing'
        else:
            request=urllib.request.Request(item['download_url'],headers={'User-Agent':'OntoKin-source-recovery'})
            with urllib.request.urlopen(request,timeout=40) as response:data=response.read()
            how='downloaded'
        blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        assert blob==expected['sha'] and len(data)==expected['size'],'source identity mismatch'
        if how=='downloaded':
            path.parent.mkdir(parents=True,exist_ok=True)
            with path.open('xb') as stream:stream.write(data)
            path.chmod(int(expected['mode'][-3:],8))
        out.update(status='passed',acquisition=how,bytes=len(data),blob=blob,sha256=hashlib.sha256(data).hexdigest(),mode=oct(path.stat().st_mode & 0o777))
    except BaseException as error:
        out.update(status='failed',error_type=type(error).__name__,http_code=getattr(error,'code',None),error_detail='redacted to avoid URL disclosure')
    out['finished_utc']=now();return out
items=json.loads(pathlib.Path(sys.argv[1]).read_text())
start=now()
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:results=list(pool.map(one,items))
receipt={'parent':'a5bb1e674e4ae3eb1d77e83b63f7a809eacf0bd0','started_utc':start,'finished_utc':now(),'items':results}
(META/(sys.argv[2]+'.json')).write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'receipt':sys.argv[2],'passed':sum(x['status']=='passed' for x in results),'failed':sum(x['status']=='failed' for x in results),'bytes':sum(x.get('bytes',0) for x in results),'failures':[{'path':x['path'],'type':x['error_type'],'http_code':x['http_code']} for x in results if x['status']=='failed']}))
