"""Import verified parent bytes as their actual Git objects; no product imports."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path('/workspace/scratch/bd03c06e866f/ontokin')
META = ROOT.parent / 'c045-meta'
BRANCH = 'work/reach06-conditional-angular-feasibility-20261026-c045'
PARENT = '91e8899ad90f04292dd4aee5aaec8b730b397d45'
TREE = '11d1ce9acc2cb4fa93be44c4772a9e8e3b3270ff'

def git(*args, data=None):
    p = subprocess.run(['git', '-C', str(ROOT), *args], input=data,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return p.stdout

if (ROOT / '.git').exists():
    raise RuntimeError('Refuse to replace existing Git state')
inventory = json.loads((META / 'parent-tree.json').read_bytes())
files = [row for row in inventory['tree'] if row['type'] == 'blob']
assert len(files) == 2356 and sum(row['size'] for row in files) == 490821760
git('init', '--initial-branch=' + BRANCH)
index = bytearray()
for row in files:
    data = (ROOT / row['path']).read_bytes()
    assert len(data) == row['size']
    assert hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() == row['sha']
    observed = git('hash-object', '-w', '--stdin', data=data).decode().strip()
    assert observed == row['sha']
    index.extend((row['mode'] + ' ' + row['sha'] + '\t' + row['path']).encode() + b'\0')
git('update-index', '-z', '--index-info', data=bytes(index))
assert git('write-tree').decode().strip() == TREE
raw = (META / 'recovery/parent.commit').read_bytes()
assert git('hash-object', '-t', 'commit', '-w', '--stdin', data=raw).decode().strip() == PARENT
git('update-ref', 'refs/heads/' + BRANCH, PARENT)
git('remote', 'add', 'origin', 'https://github.com/Omegapy/OntoKin.git')
status = git('status', '--porcelain=v1', '--untracked-files=all').decode()
assert status == '', status
result = {'status': 'passed', 'commit': PARENT, 'tree': TREE, 'branch': BRANCH,
          'files': len(files), 'bytes': sum(row['size'] for row in files),
          'clean': True, 'synthetic_commit_created': False,
          'history_qualification': 'Only the original parent commit and complete tree/blobs were imported; earlier history objects were not downloaded.',
          'product_imports_or_requests': 0}
(META / 'import-parent-result.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
