"""Prepare exact new-file publication metadata; no product imports or execution."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path('/workspace/scratch/bd03c06e866f/ontokin')
META = ROOT.parent / 'c045-meta'
PREFIX = 'docs/engineering/reach-recording-validation-2026-10-23/'
PARENT = '91e8899ad90f04292dd4aee5aaec8b730b397d45'

def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])

assert git('rev-parse', 'HEAD').decode().strip() == PARENT
assert not git('diff', '--name-only')
assert not git('diff', '--cached', '--name-only')
new = sorted(p for p in git('ls-files', '--others', '--exclude-standard', '-z').decode().split('\0') if p)
assert len(new) == 41
assert all(p.startswith(PREFIX + 'checkpoint-045') or p == PREFIX + 'HANDOFF-045.md' for p in new)
records = []
contents = {}
for name in new:
    data = (ROOT / name).read_bytes()
    contents[name] = data.decode('utf-8')
    records.append({'path': name, 'mode': '100644', 'type': 'blob', 'bytes': len(data),
                    'sha': hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest(),
                    'sha256': hashlib.sha256(data).hexdigest()})
git('add', '--', *new)
git('diff', '--cached', '--check')
changes = git('diff', '--cached', '--name-status').decode().splitlines()
assert len(changes) == len(new) and all(row.startswith('A\t') for row in changes)
tree = git('write-tree').decode().strip()
result = {'schema': 'ontokin.checkpoint045-core-publication-inputs/0.1',
          'parent': PARENT, 'parent_tree': '11d1ce9acc2cb4fa93be44c4772a9e8e3b3270ff',
          'tree': tree, 'new_files': len(records), 'new_bytes': sum(x['bytes'] for x in records),
          'all_changes_are_new_owned_files': True, 'files': records}
(META / 'core-publication-inputs.json').write_text(json.dumps(result, indent=2) + '\n')
(META / 'core-content-bundle.json').write_text(json.dumps(contents, ensure_ascii=False) + '\n')
print(json.dumps({key: value for key, value in result.items() if key != 'files'}))
print(json.dumps({'bundle_bytes': (META / 'core-content-bundle.json').stat().st_size}))
