#!/usr/bin/env python3
"""Verify and retain immutable GitHub payload bytes from connector responses."""
import base64, datetime, hashlib, json
from pathlib import Path, PurePosixPath

ROOT=Path(__file__).resolve().parents[1]
PLAN=json.loads((ROOT/'c061-package/publication-plan.json').read_text())
EXPECTED={entry['path']:entry for entry in PLAN['files']}
records={}
for batch in sorted((ROOT/'c061-remote-readback').glob('batch-*.json')):
    for item in json.loads(batch.read_text()):
        path=item['path'];relative=PurePosixPath(path)
        if relative.is_absolute() or '..' in relative.parts or path not in EXPECTED:
            raise ValueError('Unexpected remote path')
        response=item['response'];content=response['content'];encoding=response['encoding']
        raw=base64.b64decode(''.join(content.split()),validate=True) if encoding=='base64' else content.encode() if encoding=='utf-8' else None
        if raw is None:raise ValueError('Unexpected remote encoding')
        actual={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
                'blob':hashlib.sha1(f'blob {len(raw)}\0'.encode()+raw).hexdigest()}
        expected=EXPECTED[path]
        if any(actual[key]!=expected[key] for key in actual):
            raise ValueError(f'Remote byte mismatch: {path}')
        if path in records:raise ValueError(f'Duplicate readback: {path}')
        target=ROOT/'c061-remote-readback/repository'/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists() and target.read_bytes()!=raw:raise ValueError('Different existing readback bytes')
        target.write_bytes(raw)
        records[path]={'path':path,**actual,'mode':expected['mode'],'attempt':item['attempt'],'verified':True}
if set(records)!=set(EXPECTED):raise ValueError(f'Missing remote members: {set(EXPECTED)-set(records)}')
commit=json.loads((ROOT/'c061-recovery/payload-commit.json').read_text())
receipt={'schema_version':'ontokin.c061-remote-readback/0.1','status':'passed',
         'completed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'payload_commit':commit['sha'],'payload_tree':commit['tree']['sha'],'expected_parent':PLAN['parent'],
         'files_verified':len(records),'bytes_verified':sum(x['bytes'] for x in records.values()),
         'files':[records[name] for name in sorted(records)],'method':'Immutable commit contents reads; exact UTF-8 blob fallback for two >1 MiB JSON receipts. Local byte length, SHA-256 and Git blob verified independently.',
         'release_acceptance':False}
(ROOT/'c061-remote-readback/receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({key:value for key,value in receipt.items() if key!='files'},indent=2))
