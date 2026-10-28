#!/usr/bin/env python3
"""Recover immutable repository bytes; never execute recovered source."""
import base64
import concurrent.futures
import hashlib
import json
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request

BASE = Path('/workspace/scratch/0dd9316e88af/c058')

def recover(job):
    started = time.time()
    rec = {k: job[k] for k in ('path', 'commit', 'sha', 'size', 'mode', 'destination', 'method') if k in job}
    try:
        target = BASE / job['destination']
        if not target.resolve().is_relative_to(BASE):
            raise ValueError('destination escapes recovery root')
        if target.exists():
            data = target.read_bytes()
            rec['method'] = 'existing exact bytes reverified against immutable tree'
        elif 'content' in job:
            data = job['content'].encode('utf-8')
        elif 'base64' in job:
            data = base64.b64decode(job['base64'])
        else:
            with urllib.request.urlopen(job['download_url'], timeout=45) as response:
                data = response.read()
        actual = hashlib.sha1(('blob %d\0' % len(data)).encode() + data).hexdigest()
        rec.update(actual_bytes=len(data), git_blob=actual, sha256=hashlib.sha256(data).hexdigest())
        if len(data) != job['size'] or actual != job['sha']:
            raise ValueError('immutable size/blob mismatch')
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if target.read_bytes() != data:
                raise ValueError('existing destination has different bytes')
        else:
            target.write_bytes(data)
        if job.get('mode') in ('100644', '100755'):
            target.chmod(int(job['mode'][-3:], 8))
        rec['status'] = 'exact'
    except Exception as exc:
        rec.update(status='failed', error_type=type(exc).__name__)
        if isinstance(exc, urllib.error.HTTPError):
            rec['http_status'] = exc.code
        elif isinstance(exc, ValueError):
            rec['error'] = str(exc)
    rec['elapsed_seconds'] = round(time.time() - started, 6)
    return rec

def main():
    jobs = json.load(sys.stdin)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(recover, jobs))
    log = BASE / 'recovery' / 'acquisition-results.jsonl'
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open('a', encoding='utf-8') as out:
        for rec in results:
            out.write(json.dumps(rec, sort_keys=True) + '\n')
    print(json.dumps({'attempts':len(results), 'exact':sum(x['status']=='exact' for x in results), 'failed':[x for x in results if x['status']!='exact']}, separators=(',',':')))

if __name__ == '__main__':
    main()
