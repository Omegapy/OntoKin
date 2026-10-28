import hashlib
import json
import pathlib
import subprocess
import sys
from datetime import datetime, timezone

root = pathlib.Path('/workspace/scratch/76d468ef8f7e/OntoKin')
output = pathlib.Path('/workspace/scratch/76d468ef8f7e/c037-preflight/source-verification.json')
remote = json.loads(pathlib.Path('/workspace/scratch/76d468ef8f7e/c037-preflight/remote-tree.json').read_text())
def git(*args):
    return subprocess.check_output(['git', '-C', str(root), *args])
head = git('rev-parse', 'HEAD').decode().strip()
tree = git('rev-parse', 'HEAD^{tree}').decode().strip()
assert head == '96b8f05571fecaf8babb3b6c000b4a829f0a9fb3'
assert tree == remote['sha'] == 'ee1b241fb5d5de8b3ac965f9ad0063928a393190'
assert remote['truncated'] is False
assert not git('status', '--porcelain')
inventory = []
for entry in remote['tree']:
    if entry['type'] != 'blob':
        continue
    path = root / entry['path']
    assert path.is_file() and not path.is_symlink(), str(path)
    data = path.read_bytes()
    blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    assert blob == entry['sha'], entry['path']
    assert len(data) == entry['size'], entry['path']
    mode = '100755' if path.stat().st_mode & 0o111 else '100644'
    assert mode == entry['mode'], entry['path']
    inventory.append({'path': entry['path'], 'mode': mode, 'bytes': len(data), 'git_blob': blob,
                      'sha256': hashlib.sha256(data).hexdigest()})
tracked = sorted(p for p in git('ls-files', '-z').decode().split('\0') if p)
assert sorted(x['path'] for x in inventory) == tracked
raw_commit = git('cat-file', 'commit', head)
assert hashlib.sha1(b'commit ' + str(len(raw_commit)).encode() + b'\0' + raw_commit).hexdigest() == head
candidate = '4ca73909f861fe4bef9694787473621c1d21c140'
candidate_tree = git('rev-parse', candidate + '^{tree}').decode().strip()
assert candidate_tree == '87c949b238055af1ce368c694e1d5683c8aeacde'
unchanged = ['ontokin', 'tests', '.github', 'tools', 'docs/language-design/planar-reach-v0.1',
             'docs/language-design/OK-LANG-006-reusable-planar-reach-actions.md']
assert not git('diff', '--name-only', candidate, head, '--', *unchanged)
inventory.sort(key=lambda x: x['path'])
result = {'schema_version': 'ontokin.checkpoint037-source-verification/0.1',
          'status': 'passed', 'observed_at_utc': datetime.now(timezone.utc).isoformat(),
          'source_commit': head, 'source_tree': tree, 'source_history': 'shallow; no historical completeness claimed',
          'candidate_commit': candidate, 'candidate_tree': candidate_tree,
          'candidate_identical_scopes': unchanged,
          'remote_tree_complete': True, 'working_tree_clean': True,
          'tracked_files': len(inventory), 'tracked_bytes': sum(x['bytes'] for x in inventory),
          'inventory_sha256': hashlib.sha256((json.dumps(inventory, sort_keys=True, separators=(',', ':'))+'\n').encode()).hexdigest(),
          'verification': 'Every tracked regular file, executable mode, byte length and Git blob matches the fresh GitHub recursive tree. Local original commit object hashes exactly. Named candidate scopes are unchanged.',
          'product_requests_executed': 0, 'runtime_test_methods_executed': 0, 'inventory': inventory}
output.write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k != 'inventory'}, indent=2))
