"""Run only the documentation and source/retained-JSON audit on the published core."""
from pathlib import Path
import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path('/workspace/scratch/bd03c06e866f/ontokin')
META = ROOT.parent / 'c045-meta'
OUT = META / 'core-validation'
COMMIT = 'f2ed86eddcf37215fc134c5bb0ee9dce9bbd9d2b'
TREE = '64f80e946d8f498bfc96ad75fd010315c0a9ecc5'
PREFIX = 'docs/engineering/reach-recording-validation-2026-10-23/'

def now():
    return datetime.now(timezone.utc).isoformat()

def sha(data):
    return hashlib.sha256(data).hexdigest()

def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])

assert not OUT.exists(), 'Do not replace an earlier validation'
OUT.mkdir()
started = now()
assert git('rev-parse', 'HEAD').decode().strip() == COMMIT
assert git('rev-parse', 'HEAD^{tree}').decode().strip() == TREE
assert git('status', '--porcelain=v1', '--untracked-files=all') == b''
remote = json.loads((META / 'core-tree.json').read_bytes())
assert remote['sha'] == TREE and remote['truncated'] is False
files = sorted((x for x in remote['tree'] if x['type'] == 'blob'), key=lambda x: x['path'])
assert len(files) == 2397

def inventory():
    out = []
    for row in files:
        path = ROOT / row['path']
        data = path.read_bytes()
        mode = '100755' if path.stat().st_mode & 0o111 else '100644'
        blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        assert (mode, len(data), blob) == (row['mode'], row['size'], row['sha']), row['path']
        out.append({'path': row['path'], 'mode': mode, 'bytes': len(data), 'blob': blob, 'sha256': sha(data)})
    return out

before = inventory()
(OUT / 'inputs-before.json').write_text(json.dumps(before, indent=2) + '\n')
receipts = []
commands = [
    ('documentation', [sys.executable, 'docs/maintenance/reorganization-2026-10-17/verify_reorganization.py']),
    ('source-data', [sys.executable, PREFIX + 'checkpoint-045-audit.py', '--repo', str(ROOT),
                     '--retained', str(ROOT.parent / 'c044-retained'), '--output', str(OUT / 'source-data-result.json')]),
]
for label, argv in commands:
    begin = now()
    proc = subprocess.run(argv, cwd=ROOT, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'},
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    finish = now()
    (OUT / (label + '.stdout')).write_bytes(proc.stdout)
    (OUT / (label + '.stderr')).write_bytes(proc.stderr)
    receipt = {'label': label, 'argv': argv, 'cwd': str(ROOT), 'source_commit': COMMIT,
               'source_tree': TREE, 'started_utc': begin, 'finished_utc': finish,
               'exit_code': proc.returncode, 'stdout': label + '.stdout',
               'stdout_bytes': len(proc.stdout), 'stdout_sha256': sha(proc.stdout),
               'stderr': label + '.stderr', 'stderr_bytes': len(proc.stderr),
               'stderr_sha256': sha(proc.stderr), 'environment_override': {'PYTHONDONTWRITEBYTECODE': '1'}}
    (OUT / (label + '-receipt.json')).write_text(json.dumps(receipt, indent=2) + '\n')
    receipts.append(receipt)
    print(json.dumps({'label': label, 'exit_code': proc.returncode, 'stdout': proc.stdout.decode(),
                      'stderr': proc.stderr.decode()}), flush=True)
after = inventory()
(OUT / 'inputs-after.json').write_text(json.dumps(after, indent=2) + '\n')
assert before == after
assert git('status', '--porcelain=v1', '--untracked-files=all') == b''
result = {'schema': 'ontokin.checkpoint045-published-core-validation/0.1',
          'status': 'passed' if all(x['exit_code'] == 0 for x in receipts) else 'failed',
          'source_commit': COMMIT, 'source_tree': TREE,
          'started_utc': started, 'finished_utc': now(), 'python_executable': sys.executable,
          'python': sys.version, 'platform': platform.platform(), 'commands': receipts,
          'source_files': len(before), 'source_bytes': sum(x['bytes'] for x in before),
          'all_remote_paths_modes_sizes_git_blobs_match': True, 'inputs_stable': True,
          'worktree_clean_before_and_after': True,
          'product_imports_requests_tests_or_candidate_replays': 0,
          'hosted_jobs_dispatched': 0, 'validation_scope': 'documentation preservation/links plus stdlib source AST, retained JSON, original recorded key-order and integer bound analysis only'}
(OUT / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k != 'commands'}))
sys.exit(0 if result['status'] == 'passed' else 1)
