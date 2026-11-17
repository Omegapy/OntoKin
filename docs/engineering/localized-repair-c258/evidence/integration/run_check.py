"""Execute one identified focused check and preserve its complete outcome."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

parser = argparse.ArgumentParser()
parser.add_argument('--repo', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--name', required=True)
parser.add_argument('script')
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=True)
report_path = args.output / (args.name + '.json')
log_path = args.output / (args.name + '.log')
assert not report_path.exists() and not log_path.exists(), 'Use a fresh check identity'

def git(*values):
    return subprocess.check_output(['git', '-C', str(args.repo), *values], text=True).strip()

commit, tree = git('rev-parse', 'HEAD'), git('rev-parse', 'HEAD^{tree}')
before = git('status', '--porcelain', '--untracked-files=all')
assert not before, 'The checked source must be clean'
script = args.repo / args.script
script_hash = hashlib.sha256(script.read_bytes()).hexdigest()
command = [sys.executable, '-IB', args.script]
start = time.monotonic()
timed_out = False
try:
    execution = subprocess.run(command, cwd=args.repo, capture_output=True, text=True, timeout=180)
    output, return_code = execution.stdout + execution.stderr, execution.returncode
except subprocess.TimeoutExpired as exc:
    def text(value):
        return value.decode(errors='replace') if isinstance(value, bytes) else value or ''
    output, return_code, timed_out = text(exc.stdout) + text(exc.stderr), None, True
log_path.write_text(output)
unchanged = (git('rev-parse', 'HEAD') == commit and git('rev-parse', 'HEAD^{tree}') == tree
             and not git('status', '--porcelain', '--untracked-files=all')
             and hashlib.sha256(script.read_bytes()).hexdigest() == script_hash)
report = {'schema': 'ontokin.c258.executed-check/0.1', 'name': args.name,
          'commit': commit, 'tree': tree, 'command': command,
          'workingDirectory': str(args.repo), 'scriptSha256': script_hash,
          'sourceCleanBefore': not before, 'sourceUnchangedAfter': unchanged,
          'returnCode': return_code, 'timedOut': timed_out,
          'passed': return_code == 0 and unchanged and not timed_out,
          'elapsedSeconds': round(time.monotonic() - start, 3),
          'python': sys.version, 'platform': platform.platform(),
          'log': log_path.name, 'logSha256': hashlib.sha256(log_path.read_bytes()).hexdigest()}
report_path.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
raise SystemExit(0 if report['passed'] else 1)
