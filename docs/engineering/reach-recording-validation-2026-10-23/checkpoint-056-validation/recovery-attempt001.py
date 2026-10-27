"""Fetch only pinned repository inputs, verify Git identities, never import product code."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path, PurePosixPath
import hashlib
import json
import time
import urllib.request

BASE = Path('/workspace/scratch/a9a94ced6ae4')
ROOT = BASE / 'ontokin-c056'
REF = '8000959ad25e89d1794d1401c0f8c2960bcd18fc'
TREE = json.loads((BASE/'c056-preparation/parent-tree.json').read_text())
ENTRIES = {r['path']: r for r in TREE['tree'] if r['type'] == 'blob'}
OLD = json.loads((BASE/'c056-preparation/c055-recovered-inputs.json').read_text())
SELECTED = {r['path'] for r in OLD['inputs']}
SELECTED.update(p for p in ENTRIES if p.startswith('ontokin/') or p.endswith(('.md','.html','.markdown','.htm')))
SELECTED.update(p for p in ENTRIES if p.startswith('docs/engineering/reach-recording-validation-2026-10-23/checkpoint-055') or p.endswith('/HANDOFF-055.md'))

def blob(b):
    return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()

def fetch(path):
    rel = PurePosixPath(path)
    assert not rel.is_absolute() and '..' not in rel.parts
    entry = ENTRIES[path]
    assert entry['mode'] in ('100644','100755')
    target = ROOT/path
    if target.exists():
        data = target.read_bytes()
        assert blob(data) == entry['sha'], path
        origin = 'existing verified source'
    else:
        url = 'https://raw.githubusercontent.com/Omegapy/OntoKin/'+REF+'/'+urllib.parse.quote(path)
        with urllib.request.urlopen(url, timeout=45) as response:
            data = response.read(entry.get('size',0)+1)
        assert len(data) == entry['size'] and blob(data) == entry['sha'], path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        origin = 'immutable remote read'
    return {'path':path,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'git_blob':blob(data),'origin':origin}

records=[]
failures=[]
start=time.time()
with (BASE/'c056-preparation/recovery-results.jsonl').open('a') as log:
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures={pool.submit(fetch,p):p for p in sorted(SELECTED)}
        for f in as_completed(futures):
            path=futures[f]
            try:
                r=fetch_result=f.result()
                records.append(r)
            except Exception as e:
                r={'path':path,'error':type(e).__name__,'detail':str(e)}
                failures.append(r)
            log.write(json.dumps(r)+'\n'); log.flush()
            if (len(records)+len(failures)) % 100 == 0:
                print(json.dumps({'completed':len(records),'failures':len(failures),'selected':len(SELECTED)}),flush=True)
report={'source_commit':REF,'source_tree':TREE['sha'],'parent_files':len(ENTRIES),'files':len(records),'bytes':sum(r['bytes'] for r in records),'partial_snapshot':True,'product_imports':0,'archive_extractions':0,'duration_seconds':time.time()-start,'failures':failures,'inputs':sorted(records,key=lambda r:r['path'])}
(BASE/'c056-preparation/recovered-inputs.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='inputs'}),flush=True)
raise SystemExit(bool(failures))
