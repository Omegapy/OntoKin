#!/usr/bin/env python3
"""Verify complete frozen corpus bytes/modes without importing production."""
from pathlib import Path
import hashlib,json,stat

ROOT=Path(__file__).resolve().parents[1]


def main():
    manifest=json.loads((ROOT/'INPUTS.json').read_text())
    actual={p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    expected={r['path'] for r in manifest['files']}|{'INPUTS.json'}
    errors=[]
    if actual!=expected:errors.append({'file_membership':{'missing':sorted(expected-actual),'extra':sorted(actual-expected)}})
    for row in manifest['files']:
        path=ROOT/row['path']
        if not path.is_file():continue
        raw=path.read_bytes();mode=path.lstat().st_mode
        found={'bytes':len(raw),'sha256':'sha256:'+hashlib.sha256(raw).hexdigest(),'mode':'100644' if stat.S_ISREG(mode) and stat.S_IMODE(mode)==0o644 else oct(mode)}
        wanted={k:row[k] for k in found}
        if found!=wanted:errors.append({'path':row['path'],'actual':found,'expected':wanted})
    print(json.dumps({'status':'passed' if not errors else 'failed','files':len(manifest['files']),'manifest_sha256':'sha256:'+hashlib.sha256((ROOT/'INPUTS.json').read_bytes()).hexdigest(),'errors':errors},sort_keys=True))
    return bool(errors)


if __name__=='__main__':raise SystemExit(main())
