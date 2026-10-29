#!/usr/bin/env python3
"""Run the two fixed C062 offline checks and retain exact receipts."""
import datetime
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / 'c062-documentation-base'
CP = REPO / 'docs/engineering/reach-recording-validation-2026-10-28-c062'
OUT = ROOT / 'c062-work/final-checks'
OUT.mkdir(exist_ok=False)

def info(path):
    raw = path.read_bytes()
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
            'git_blob': hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()}

def inventory():
    return [{'path': p.relative_to(REPO).as_posix(), **info(p)}
            for p in sorted(REPO.rglob('*')) if p.is_file()]

def write(name, value):
    (OUT/name).write_text(json.dumps(value, indent=2)+'\n')

def run(name, command, before):
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    start = time.monotonic()
    result = subprocess.run(command, cwd=REPO, capture_output=True)
    ended = datetime.datetime.now(datetime.timezone.utc).isoformat()
    (OUT/(name+'.stdout')).write_bytes(result.stdout)
    (OUT/(name+'.stderr')).write_bytes(result.stderr)
    after = inventory()
    write(name+'-inputs-before.json', before)
    write(name+'-inputs-after.json', after)
    receipt = {'command': command, 'cwd': str(REPO), 'started_at': started,
               'finished_at': ended, 'elapsed_seconds': time.monotonic()-start,
               'returncode': result.returncode, 'inputs_stable': before == after,
               'materialized_input_files': len(before),
               'base_source_commit': 'e5e99b92e4efa541b434abcdda5c2ec31dda6a39',
               'candidate_documents_not_yet_committed': True,
               'interpreter': sys.version, 'platform': platform.platform(),
               'runner': info(Path(__file__)), 'executable': info(Path(sys.executable)),
               'stdout': info(OUT/(name+'.stdout')), 'stderr': info(OUT/(name+'.stderr')),
               'input_inventory_before': info(OUT/(name+'-inputs-before.json')),
               'input_inventory_after': info(OUT/(name+'-inputs-after.json')),
               'product_requests_executed': 0}
    write(name+'-command.json', receipt)
    if not receipt['inputs_stable']:
        raise RuntimeError(name+' changed input files')
    return receipt, result

before = inventory()
calculation, result = run('calculation', [sys.executable, '-B',
    str(CP/'c062_ancestry_cost_screen.py'),
    str(REPO/'docs/engineering/reach-recording-validation-2026-10-28-c061')], before)
if result.returncode:
    raise RuntimeError('Offline calculation failed; see retained receipts')
output = json.loads(result.stdout)
assert output['results']['P11']['conditional_necessary_work_lower_bound'] == 100549
assert output['results']['L03']['conditional_necessary_work_lower_bound'] == 100358
assert result.stdout == (CP/'c062-cost-screen.json').read_bytes()
documentation, result = run('documentation', [sys.executable, '-B',
    str(REPO/'docs/maintenance/reorganization-2026-10-17/verify_reorganization.py')], inventory())
gate = json.loads(result.stdout)
summary = {'calculation_returncode': calculation['returncode'],
           'calculation_inputs_stable': calculation['inputs_stable'],
           'documentation_returncode': documentation['returncode'],
           'documentation_inputs_stable': documentation['inputs_stable'],
           'documentation_status': gate['status'],
           'documentation_failure_count': len(gate['failures']),
           'sources_verified': gate['sources_verified'],
           'sections_verified': gate['sections_verified'], 'links': gate['links'],
           'failures': gate['failures'], 'product_requests_executed': 0}
write('summary.json', summary)
print(json.dumps(summary, indent=2))
