from pathlib import Path
import json, hashlib, sys
ROOT = Path('/workspace/scratch/813fb8a53b1a')
payload = Path(sys.argv[1])
data = json.loads(payload.read_text())
results = []
for f in data['files']:
    p = ROOT / 'snapshot' / f['path']
    assert p.resolve().is_relative_to((ROOT / 'snapshot').resolve())
    if f.get('error'):
        results.append({'path': f['path'], 'status': 'retrieval_failed', 'error': f['error']})
        continue
    b = f['text'].encode('utf-8')
    h = hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest()
    if len(b) != f['size'] or h != f['sha']:
        results.append({'path':f['path'],'status':'identity_failed','expected_bytes':f['size'],'actual_bytes':len(b),'expected_blob':f['sha'],'actual_blob':h})
        continue
    if p.exists():
        assert p.read_bytes() == b, f['path']
        status = 'already_present_exact'
    else:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b)
        status = 'recovered_exact'
    results.append({'path':f['path'],'status':status,'bytes':len(b),'git_blob':h,'sha256':hashlib.sha256(b).hexdigest()})
out = payload.with_name(payload.stem + '-result.json')
out.write_text(json.dumps({'source_commit':'8287be55a21c28320aa11895cadd29c68ae18f90','results':results},indent=2)+'\n')
print(json.dumps({'batch':payload.name,'exact':sum(x['status'].endswith('exact') for x in results),'failed':[x for x in results if not x['status'].endswith('exact')]}))
