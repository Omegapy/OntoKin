"""Capture existing OntoKin documentation/workflow checks on identified bytes."""
import argparse
import datetime
import hashlib
import json
import pathlib
import platform
import subprocess
import sys
import time

parser = argparse.ArgumentParser()
parser.add_argument('--repo', required=True, type=pathlib.Path)
parser.add_argument('--output', required=True, type=pathlib.Path)
parser.add_argument('--phase', required=True)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=False)

def git(*words):
    return subprocess.check_output(['git', '-C', str(args.repo), *words], text=True).strip()

def state():
    return {'commit': git('rev-parse', 'HEAD'), 'index_tree': git('write-tree'),
            'status': git('status', '--porcelain=v1', '--untracked-files=all'),
            'unstaged_paths': git('diff', '--name-only')}

before = state()
assert not before['unstaged_paths'], 'Unstaged tracked edits need reconciliation'
report = {'schema_version': 1, 'phase': args.phase, 'source_before': before,
          'started_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'python': sys.version, 'platform': platform.platform(),
          'executable': {'path': sys.executable, 'sha256': hashlib.sha256(pathlib.Path(sys.executable).read_bytes()).hexdigest()},
          'runner_sha256': hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
          'checks': []}
groups = [('workflow', ['tools/chat_workflow.py', 'check', '--json']),
          ('documentation', ['docs/maintenance/reorganization-2026-10-17/verify_reorganization.py'])]
for name, words in groups:
    command = [sys.executable, '-B', *words]
    started = time.monotonic()
    proc = subprocess.run(command, cwd=args.repo, capture_output=True)
    raw = proc.stdout + proc.stderr
    (args.output / (name + '.log')).write_bytes(raw)
    try:
        result = json.loads(proc.stdout)
    except (ValueError, UnicodeDecodeError):
        result = {}
    passed = proc.returncode == 0 and (result.get('passed') is True if name == 'workflow' else result.get('status') == 'passed')
    report['checks'].append({'name': name, 'command': command, 'exit_code': proc.returncode,
                            'passed': passed, 'seconds': round(time.monotonic() - started, 4),
                            'log': {'path': name + '.log', 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()},
                            'summary': result})
report['source_after'] = state()
report['inputs_stable'] = report['source_before'] == report['source_after']
report['passed'] = report['inputs_stable'] and all(x['passed'] for x in report['checks'])
report['finished_at_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
report['limits'] = ['Documentation/workflow structure and preservation only', 'No observer cohort, full product, native, model, hosted or other interpreter execution']
(args.output / 'CHECKS.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'passed': report['passed'], 'checked_tree': before['index_tree'],
                  'checks': [{'name': x['name'], 'passed': x['passed']} for x in report['checks']]}))
raise SystemExit(0 if report['passed'] else 1)
