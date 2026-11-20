"""Prepare an exact Git tree payload from a staged, reconciled checkpoint."""
import argparse
import json
import pathlib
import subprocess

ap = argparse.ArgumentParser()
ap.add_argument('--repo', type=pathlib.Path, required=True)
ap.add_argument('--base', required=True)
ap.add_argument('--known', action='append', default=[])
ap.add_argument('--output', type=pathlib.Path, required=True)
a = ap.parse_args()

def git(*args):
    return subprocess.check_output(['git', '-C', str(a.repo), *args])

assert git('rev-parse', 'HEAD').decode().strip() == a.base
assert not git('diff', '--name-only').strip(), 'Unstaged edits'
known = set()
for ref in [a.base, *a.known]:
    for row in git('ls-tree', '-r', '-z', ref).split(b'\0'):
        if row:
            known.add(row.split(b'\t', 1)[0].split()[2].decode())
index = {}
for row in git('ls-files', '-s', '-z').split(b'\0'):
    if row:
        meta, name = row.split(b'\t', 1)
        mode, sha, stage = meta.decode().split()
        assert stage == '0'
        index[name.decode()] = (mode, sha)
entries = []
for raw_name in git('diff', '--cached', '--name-only', '-z').split(b'\0'):
    if not raw_name:
        continue
    name = raw_name.decode()
    assert name in index, 'Deletion requires explicit handling'
    mode, sha = index[name]
    entry = {'path': name, 'mode': mode, 'type': 'blob'}
    if sha in known:
        entry['sha'] = sha
    else:
        entry['content'] = git('cat-file', 'blob', sha).decode('utf-8')
    entries.append(entry)
payload = {'base_commit': a.base, 'base_tree': git('rev-parse', a.base + '^{tree}').decode().strip(),
           'expected_tree': git('write-tree').decode().strip(), 'entries': entries}
a.output.parent.mkdir(parents=True, exist_ok=True)
a.output.write_text(json.dumps(payload) + '\n')
print(json.dumps({'entries': len(entries), 'new_text_blobs': sum('content' in e for e in entries),
                  'bytes': a.output.stat().st_size, 'expected_tree': payload['expected_tree']}))
