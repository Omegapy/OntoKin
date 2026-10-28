"""Verify copied checkouts against freshly retrieved complete GitHub trees."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

BASE = Path(__file__).resolve().parent

def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args])

reports = []
for name, folder, expected in [('doc', 'OntoKin', '6404b1e590a900e550ae216394e0f17d010bac9e'), ('run', 'c038-execution', '4ca73909f861fe4bef9694787473621c1d21c140')]:
    root = BASE.parent / folder
    remote = json.loads((BASE / (name + '_tree.json')).read_text())
    assert remote['truncated'] is False
    head = git(root, 'rev-parse', 'HEAD').decode().strip()
    tree = git(root, 'rev-parse', 'HEAD^{tree}').decode().strip()
    assert head == expected and tree == remote['sha']
    assert not git(root, 'status', '--porcelain')
    raw_commit = git(root, 'cat-file', 'commit', head)
    assert hashlib.sha1(b'commit ' + str(len(raw_commit)).encode() + b'\0' + raw_commit).hexdigest() == head
    entries = [e for e in remote['tree'] if e['type'] == 'blob']
    expected_paths = {e['path'] for e in entries}
    local_paths = set(git(root, 'ls-files', '-z').decode().strip('\0').split('\0'))
    assert local_paths == expected_paths
    inventory = []
    for e in sorted(entries, key=lambda item: item['path']):
        p = root / e['path']
        assert p.is_file() and not p.is_symlink()
        data = p.read_bytes()
        mode = '100755' if os.stat(p).st_mode & 0o111 else '100644'
        blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        assert len(data) == e['size'] and blob == e['sha'] and mode == e['mode'], e['path']
        inventory.append({'path': e['path'], 'bytes': len(data), 'mode': mode, 'git_blob': blob, 'sha256': hashlib.sha256(data).hexdigest()})
    out = {'schema_version': 'ontokin.c038-source-inventory/0.1', 'status': 'passed', 'root': str(root), 'head': head, 'tree': tree, 'shallow': git(root, 'rev-parse', '--is-shallow-repository').decode().strip() == 'true', 'files': len(inventory), 'bytes': sum(e['bytes'] for e in inventory), 'entries': inventory}
    (BASE / (name + '-source-inventory.json')).write_text(json.dumps(out, indent=2) + '\n')
    (BASE / (name + '-original.commit')).write_bytes(raw_commit)
    reports.append({k: v for k, v in out.items() if k != 'entries'})
(BASE / 'source-verification.json').write_text(json.dumps(reports, indent=2) + '\n')
print(json.dumps(reports, indent=2))
