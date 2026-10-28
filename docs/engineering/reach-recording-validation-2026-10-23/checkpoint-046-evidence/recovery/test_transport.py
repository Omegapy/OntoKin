import urllib.request, json, pathlib, hashlib, datetime
p=pathlib.Path('/workspace/scratch/fd65650eb54f/c046-recovery')
x=json.loads((p/'runtime-url-map-private.json').read_text())[0]
out={'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'path':x['path']}
try:
    req=urllib.request.Request(x['download_url'],headers={'User-Agent':'OntoKin-source-recovery'})
    with urllib.request.urlopen(req,timeout=20) as response: b=response.read()
    h=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
    assert h==x['sha'] and len(b)==x['size']
    out.update(status='passed',size=len(b),sha=h)
except Exception as e:
    out.update(status='failed',error_type=type(e).__name__,reason_type=type(getattr(e,'reason',None)).__name__,reason_errno=getattr(getattr(e,'reason',None),'errno',None),details='redacted to avoid URL disclosure')
out['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
print(json.dumps(out))
(p/'signed-transport-result.json').write_text(json.dumps(out,indent=2)+'\n')
