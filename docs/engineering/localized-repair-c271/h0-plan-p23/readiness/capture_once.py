"""Exclusive capture for the independently reviewed, single readiness observation."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import time

BASE = Path('/workspace/scratch/f8d879d19e34/phase-p23/readiness')
PLAN = BASE / 'READINESS-LAUNCH.json'
REVIEW = BASE.parent / 'reviews/h0/READINESS-REVIEW.json'
EXPECTED_PLAN = '224d5f3eba66ce36336f483e133f243abc50a06868828491c1f8d4e5ea307301'
EXPECTED_REVIEW = 'da402333dacda2b6c3d3449bc9405566b0bf5275d315e94683320a794297526a'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save_exclusive(path, data):
    with path.open('x', encoding='utf-8') as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write('\n')

assert digest(PLAN) == EXPECTED_PLAN
assert digest(REVIEW) == EXPECTED_REVIEW
plan = json.loads(PLAN.read_text())
script = Path(plan['script']['path'])
assert digest(script) == plan['script']['sha256']
assert script.stat().st_size == plan['script']['size_bytes']
review = json.loads(REVIEW.read_text())
assert review['verdict'] == 'accepted_for_one_bounded_current_host_pin_observation'
assert not review['mandatory_findings']
result = {
    'schema': 'ontokin.c271.p23-readiness-capture/1',
    'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'plan_sha256': EXPECTED_PLAN,
    'review_sha256': EXPECTED_REVIEW,
    'script_sha256': digest(script),
    'argv': plan['argv'],
    'cwd': plan['cwd'],
    'environment': plan['environment'],
    'outer_timeout_seconds': plan['outer_timeout_seconds'],
    'launch_count': 0,
    'target_starts': 0,
    'state': 'PRELAUNCH',
    'h0_plan_accepted': False,
}
save_exclusive(BASE / 'run001.attempt.json', result)
started = time.monotonic()
try:
    with open(plan['exclusive_stdout'], 'xb') as stdout, open(plan['exclusive_stderr'], 'xb') as stderr:
        # Final rehash occurs after exclusive outputs exist and before the only launch.
        assert digest(PLAN) == EXPECTED_PLAN
        assert digest(script) == plan['script']['sha256']
        result['launch_count'] = 1
        try:
            completed = subprocess.run(
                plan['argv'], cwd=plan['cwd'], env=plan['environment'],
                stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                timeout=plan['outer_timeout_seconds'], check=False,
            )
            result['returncode'] = completed.returncode
            result['state'] = 'COMPLETED'
        except subprocess.TimeoutExpired:
            result['state'] = 'OUTER_TIMEOUT_UNSUCCESSFUL_NO_RETRY'
except BaseException as error:
    result['state'] = 'CAPTURE_ERROR_UNSUCCESSFUL_NO_RETRY'
    result['error'] = {'type': type(error).__name__, 'message': str(error)}
finally:
    result['elapsed_seconds'] = time.monotonic() - started
    result['ended_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    result['outputs'] = {}
    for role in ('stdout', 'stderr'):
        path = Path(plan['exclusive_' + role])
        if path.exists():
            result['outputs'][role] = {
                'path': str(path), 'size_bytes': path.stat().st_size, 'sha256': digest(path)
            }
    save_exclusive(BASE / 'run001.capture.json', result)
print(json.dumps(result, sort_keys=True))
