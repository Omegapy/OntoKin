"""Capture exact permitted CPU/documentation check commands on merged main."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import platform
import subprocess
import sys

ROOT = Path('/workspace/scratch/a4d9132036d4')
REPO = ROOT / 'main-verification'
OUT = ROOT / 'work-c203/main-checks'
PREFIX = 'docs/engineering/static-tray-exporter-c200/'
OBSERVER = REPO / PREFIX / 'evidence/publication-c203/checks/run_observed.py'
CHECK = sys.argv[1]
assert CHECK in {'focused', 'protocol', 'core', 'documentation'}
assert subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], text=True).strip() == '2b2f3e7de7595099ad5f9e0176c5596220c0c2dc'

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def binding(path):
    raw = path.read_bytes()
    return {'path': str(path), 'size_bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

observed = [sys.executable, '-B', str(OBSERVER), '--repo', str(REPO), '--receipt', str(OUT / (CHECK + '-command.json')), '--']
if CHECK == 'focused':
    command = observed + [PREFIX + 'run_cpu_controls.py', '--cohort', 'focused', '--output', str(OUT / 'focused'), '--pinned-exporter', '/workspace/scratch/ef5ae272e66e/deps/blender-4.5.3-linux-x64/4.5/scripts/addons_core/io_scene_gltf2/__init__.py']
elif CHECK == 'protocol':
    command = observed + [PREFIX + 'test_protocol.py']
elif CHECK == 'documentation':
    command = observed + ['docs/maintenance/reorganization-2026-10-17/verify_reorganization.py', '--json-output', str(OUT / 'DOCUMENTATION-CHECK.json')]
else:
    command = [sys.executable, '-B', '-m', 'ontokin', 'conformance', '--output', str(OUT / 'core-conformance.json')]
stdout_path = OUT / (CHECK + '.stdout.log')
stderr_path = OUT / (CHECK + '.stderr.log')
receipt_path = OUT / (CHECK + '-launch.json')
assert not receipt_path.exists()
receipt = {
    'schema': 'ontokin.c203.actual-main-check-command/0.1',
    'check': CHECK, 'started_at_utc': now(), 'command': command,
    'cwd': str(REPO), 'source_commit': '2b2f3e7de7595099ad5f9e0176c5596220c0c2dc',
    'source_tree': '7e1ab341160cf5b86807e8ffec2cc3bb7b47db92',
    'python': sys.executable, 'python_version': platform.python_version(),
    'platform': platform.platform(), 'timeout_seconds': 300,
    'child_process_observer': binding(OBSERVER) if CHECK != 'core' else None,
    'core_process_observation_limit': 'Core CLI is recorded directly; its descendants are not instrumented.' if CHECK == 'core' else None,
    'status': 'STARTED'
}
receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
environment = dict(os.environ)
environment['PYTHONDONTWRITEBYTECODE'] = '1'
try:
    with stdout_path.open('xb') as stdout, stderr_path.open('xb') as stderr:
        result = subprocess.run(command, cwd=REPO, env=environment, stdout=stdout, stderr=stderr, timeout=300)
    receipt['exit_code'] = result.returncode
    receipt['status'] = 'PASS' if result.returncode == 0 else 'FAIL'
except BaseException as exc:
    receipt['status'] = 'ERROR'
    receipt['exception'] = {'type': type(exc).__name__, 'message': str(exc)}
    raise
finally:
    receipt['finished_at_utc'] = now()
    for key, path in [('stdout', stdout_path), ('stderr', stderr_path)]:
        if path.exists():
            receipt[key] = binding(path)
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({'check': CHECK, 'status': receipt['status'], 'exit_code': receipt.get('exit_code'), 'receipt': str(receipt_path)}))
raise SystemExit(receipt['exit_code'])
