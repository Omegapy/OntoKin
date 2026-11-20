from pathlib import Path
import hashlib
import json
import subprocess
import sys

root = Path('/workspace/scratch/c219bb61a617')
repo = root / 'OntoKin'
label = sys.argv[1]

def git(*args):
    return subprocess.check_output(['git', *args], cwd=repo)

paths = git('diff', '--cached', '--name-only', '--diff-filter=ACM').decode().splitlines()
all_paths = git('diff', '--cached', '--name-only').decode().splitlines()
assert paths == all_paths, 'Deletion or unexpected change type requires reconciliation'
assert paths, 'No staged publication'
allowed = ('docs/engineering/localized-repair-c271/finalization-20261120/', 'docs/workflow/tasks/C271/')
assert all(p.startswith(allowed) or p == 'docs/workflow/CURRENT.json' for p in paths)
entries = []
identities = []
for path in paths:
    b = git('show', ':' + path)
    mode, sha, _ = git('ls-files', '-s', '--', path).decode().split(None, 2)
    item = {'path': path, 'mode': mode, 'type': 'blob'}
    if path.endswith('.zip'):
        item['sha'] = sha
    else:
        item['content'] = b.decode('utf-8')
    entries.append(item)
    identities.append({'path': path, 'mode': mode, 'git_blob': sha, 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()})
payload = {'parent': git('rev-parse', 'HEAD').decode().strip(), 'base_tree': git('rev-parse', 'HEAD^{tree}').decode().strip(), 'tree': git('write-tree').decode().strip(), 'entries': entries, 'identities': identities}
dest = root / 'session' / (label + '-publication-input.json')
dest.write_text(json.dumps(payload, ensure_ascii=True))
print(json.dumps({'payload': str(dest), 'bytes': dest.stat().st_size, 'sha256': hashlib.sha256(dest.read_bytes()).hexdigest(), 'parent': payload['parent'], 'tree': payload['tree'], 'files': len(paths), 'binary_entries': [i for i in identities if i['path'].endswith('.zip')]}))
