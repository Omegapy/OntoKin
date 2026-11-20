from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess

root = Path('/workspace/scratch/c219bb61a617')
session = root / 'session'
intent = json.loads((session / 'FINAL-UPLOAD-INTENT.json').read_text())
audit = json.loads((root / 'final-package-review/AUDIT.json').read_text())
assert audit['failed_count'] == 0
for item in intent['ordered_files']:
    data = Path(item['local_path']).read_bytes()
    assert len(data) == item['bytes']
    assert hashlib.sha256(data).hexdigest() == item['sha256']
request = session / 'FINAL-UPLOAD-REQUEST.json'
result = session / 'FINAL-UPLOAD-RESULT.json'
errors = session / 'FINAL-UPLOAD-STDERR.log'
operation = session / 'FINAL-UPLOAD-OPERATION.json'
assert not result.exists(), 'Reconcile a previous result before any retry'
command = ['python3', str(root / '.library-helpers-current/library_upload.py')]
with request.open('rb') as source, result.open('wb') as output, errors.open('wb') as stderr:
    process = subprocess.Popen(command, stdin=source, stdout=output, stderr=stderr)
    state = {'schema': 'ontokin.c271.p02-upload-operation/1', 'started_at_utc': datetime.now(timezone.utc).isoformat(), 'state': 'running', 'pid': process.pid, 'command': command, 'request': request.name, 'ordered_file_count': 3, 'independent_archive_audit': 'passed'}
    operation.write_text(json.dumps(state, indent=2) + '\n')
    print(json.dumps({'state': 'running', 'pid': process.pid, 'files': 3}), flush=True)
    code = process.wait()
state.update(state='completed', completed_at_utc=datetime.now(timezone.utc).isoformat(), exit_code=code)
operation.write_text(json.dumps(state, indent=2) + '\n')
print(json.dumps({'state': 'completed', 'exit_code': code, 'result_path': str(result)}), flush=True)
raise SystemExit(code)
