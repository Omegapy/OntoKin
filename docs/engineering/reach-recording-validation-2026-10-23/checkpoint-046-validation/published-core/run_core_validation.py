"""Execute only documentation and retained-data checks on the published C046 core."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import platform
import subprocess
import sys

root = Path('/workspace/scratch/fd65650eb54f')
repo = root / 'OntoKin'
output = root / 'c046-validation/published-core'
output.mkdir(parents=True, exist_ok=False)
expected = 'ef4ebc263deca57ad7b0d014ec4e9af16ca9ab0b'
tree = '591258c1caad81864f0bd2801ffa0cace1100d59'
remote = json.loads((root/'c046-work/core-remote-tree.json').read_text())
files = [item for item in remote['tree'] if item['type'] == 'blob']

def git(*args):
    return subprocess.check_output(['git', *args], cwd=repo, text=True).strip()

def snapshot():
    assert git('rev-parse', 'HEAD') == expected and git('rev-parse', 'HEAD^{tree}') == tree
    assert git('status', '--porcelain') == ''
    result = []
    for item in files:
        path = repo/item['path']
        raw = path.read_bytes()
        mode = '100755' if path.stat().st_mode & 0o111 else '100644'
        blob = hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        assert len(raw) == item['size'] and mode == item['mode'] and blob == item['sha']
        result.append({'path': item['path'], 'bytes': len(raw), 'mode': mode,
                       'git_blob': blob, 'sha256': hashlib.sha256(raw).hexdigest()})
    return result

def write(name, value):
    (output/name).write_text(json.dumps(value, indent=2)+'\n')

started = datetime.now(timezone.utc).isoformat()
before = snapshot()
write('inputs-before.json', before)
commands = [
    ('documentation', [sys.executable, 'docs/maintenance/reorganization-2026-10-17/verify_reorganization.py']),
    ('source-data', [sys.executable, 'docs/engineering/reach-recording-validation-2026-10-23/checkpoint-046-audit.py',
        '--repo', str(repo), '--c033', str(root/'c046-evidence/restored-c033'),
        '--c035', str(root/'c046-evidence/restored-c035'), '--output', str(output/'source-data.json')]),
]
record = {'schema': 'ontokin.checkpoint046-core-validation-command/0.1', 'commit': expected, 'tree': tree,
          'window_comment': 6424891921, 'started_utc': started, 'python': sys.version,
          'executable': sys.executable, 'platform': platform.platform(), 'commands': [],
          'product_requests': 0, 'prepared_capture_executed': False}
for label, command in commands:
    entry = {'name': label, 'args': command, 'cwd': str(repo),
             'started_utc': datetime.now(timezone.utc).isoformat()}
    with (output/(label+'.stdout')).open('xb') as stdout, (output/(label+'.stderr')).open('xb') as stderr:
        completed = subprocess.run(command, cwd=repo, stdout=stdout, stderr=stderr, timeout=180)
    entry.update(exit_code=completed.returncode, finished_utc=datetime.now(timezone.utc).isoformat())
    record['commands'].append(entry)
    write('result.json', record)
    print(label, 'exit', completed.returncode, flush=True)
after = snapshot()
write('inputs-after.json', after)
record.update(finished_utc=datetime.now(timezone.utc).isoformat(), inputs_stable=before == after,
              files=len(before), bytes=sum(item['bytes'] for item in before),
              status='passed' if before == after and all(item['exit_code'] == 0 for item in record['commands']) else 'failed')
write('result.json', record)
print(json.dumps({'status':record['status'], 'files':record['files'], 'bytes':record['bytes'],
                  'inputs_stable':record['inputs_stable']}))
raise SystemExit(0 if record['status'] == 'passed' else 1)
