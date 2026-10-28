"""Import a published GitHub commit only if its exact raw bytes match its SHA."""
from pathlib import Path
import hashlib
import itertools
import json
import subprocess
import sys
from datetime import datetime

ROOT = Path('/workspace/scratch/bd03c06e866f/ontokin')
META = ROOT.parent / 'c045-meta'
data = json.loads(Path(sys.argv[1]).read_bytes())
prefix = sys.argv[2]
previous = sys.argv[3]

def git(*args, data=None):
    return subprocess.check_output(['git', '-C', str(ROOT), *args], input=data)

assert git('rev-parse', 'HEAD').decode().strip() == previous
assert git('write-tree').decode().strip() == data['tree']['sha']
found = []
for az, cz, ending in itertools.product(['+0000', '-0600'], ['+0000', '-0600'], ['', '\n']):
    lines = ['tree ' + data['tree']['sha']] + ['parent ' + p['sha'] for p in data['parents']]
    for role, zone in [('author', az), ('committer', cz)]:
        row = data[role]
        epoch = int(datetime.fromisoformat(row['date'].replace('Z', '+00:00')).timestamp())
        lines.append(f"{role} {row['name']} <{row['email']}> {epoch} {zone}")
    raw = ('\n'.join(lines) + '\n\n' + data['message'] + ending).encode()
    observed = hashlib.sha1(b'commit ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
    if observed == data['sha']:
        found.append((raw, az, cz, ending))
assert len(found) == 1, 'Actual published commit could not be exactly reconstructed'
raw, az, cz, ending = found[0]
assert git('hash-object', '-t', 'commit', '-w', '--stdin', data=raw).decode().strip() == data['sha']
git('update-ref', 'HEAD', data['sha'], previous)
assert git('status', '--porcelain=v1', '--untracked-files=all') == b''
(META / (prefix + '.commit')).write_bytes(raw)
result = {'status': 'passed', 'commit': data['sha'], 'tree': data['tree']['sha'],
          'previous_head': previous, 'raw_bytes': len(raw),
          'raw_sha256': hashlib.sha256(raw).hexdigest(), 'author_timezone': az,
          'committer_timezone': cz, 'message_trailing_newline': bool(ending),
          'synthetic_commit_created': False, 'worktree_clean': True}
(META / (prefix + '-import.json')).write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
