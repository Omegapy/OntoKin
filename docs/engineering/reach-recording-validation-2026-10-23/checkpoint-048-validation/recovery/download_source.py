"""Download immutable authorized source bytes; never print signed URLs."""
from pathlib import Path, PurePosixPath
import concurrent.futures, datetime, hashlib, json, os, time, urllib.request, urllib.parse

ROOT = Path('/workspace/scratch/514b4c8f2cdb/c048')
SOURCE = ROOT / 'source'
MANIFESTS = [ROOT / 'acquisition/temporary-download-manifest.json', ROOT / 'acquisition/temporary-download-extra.json']

def git_blob(raw):
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()

def acquire(item):
    name = PurePosixPath(item['path'])
    assert not name.is_absolute() and '..' not in name.parts and '\\' not in item['path']
    parsed = urllib.parse.urlsplit(item['url'])
    assert parsed.scheme == 'https' and parsed.hostname == 'raw.githubusercontent.com'
    target = SOURCE / name
    assert target.resolve().is_relative_to(SOURCE.resolve())
    if target.exists():
        raw = target.read_bytes()
        assert len(raw) == item['size'] and git_blob(raw) == item['sha'], item['path']
        return {'path':item['path'], 'bytes':len(raw), 'sha':item['sha'], 'status':'already exact'}
    try:
        request = urllib.request.Request(item['url'], headers={'User-Agent':'OntoKin-source-recovery'})
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read(item['size'] + 1)
        assert len(raw) == item['size'] and git_blob(raw) == item['sha']
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(raw)
        target.chmod(int(item['mode'],8) & 0o777)
        return {'path':item['path'], 'bytes':len(raw), 'sha':item['sha'], 'sha256':hashlib.sha256(raw).hexdigest(), 'status':'verified'}
    except Exception as exc:
        return {'path':item['path'], 'status':'failed', 'error_type':type(exc).__name__, 'http_code':getattr(exc,'code',None)}

def main():
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    t = time.monotonic()
    inputs = [p for p in MANIFESTS if p.is_file()]
    items = [i for p in inputs for i in json.loads(p.read_text())['files']]
    assert len(items) == len({e['path'] for e in items})
    rows = []
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            for row in pool.map(acquire, items):
                rows.append(row)
                if len(rows) % 200 == 0:
                    print(json.dumps({'completed':len(rows),'total':len(items),'failures':sum(r['status']=='failed' for r in rows)}), flush=True)
    finally:
        for p in inputs:
            p.unlink(missing_ok=True)
    result = {'started_at':started,'finished_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'seconds':time.monotonic()-t,'files':rows,'signed_url_manifests_deleted':all(not p.exists() for p in inputs),'product_execution':False}
    path = ROOT/'acquisition/download-result-001.json'
    with path.open('x') as out:
        json.dump(result,out,indent=2);out.write('\n')
    failures = [r for r in rows if r['status']=='failed']
    print(json.dumps({'files':len(rows),'bytes':sum(r.get('bytes',0) for r in rows),'failures':failures,'seconds':result['seconds'],'signed_url_manifests_deleted':result['signed_url_manifests_deleted']}),flush=True)
    return bool(failures)

if __name__ == '__main__':
    raise SystemExit(main())
