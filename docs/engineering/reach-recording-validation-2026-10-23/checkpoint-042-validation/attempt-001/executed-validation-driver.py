"""Run only the C042 data audit and existing documentation checker."""
import datetime
import hashlib
import json
import platform
from pathlib import Path
import stat
import subprocess
import sys

BASE = Path('/workspace/scratch/b48023f8c519')
ROOT = BASE / 'ontokin-c042'
OUT = BASE / 'c042-meta/validation-runs/attempt-001'
OUT.mkdir(parents=True, exist_ok=False)
DOC = 'docs/engineering/reach-recording-validation-2026-10-23'
publication = json.loads((BASE / 'c042-meta/core-publication.json').read_text())
parent = json.loads((BASE / 'c042-meta/parent-tree.json').read_text())
expected = {x['path']: x['sha'] for x in parent['tree'] if x['type'] == 'blob'}
for row in json.loads((BASE / 'c042-meta/core-new-files.json').read_text()):
    assert row['path'] not in expected
    expected[row['path']] = row['sha']

def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def inventory():
    rows = []
    for path in sorted(ROOT.rglob('*')):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT).as_posix()
        data = path.read_bytes()
        digest = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        rows.append({'path': relative, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                     'git_blob': digest, 'physical_mode': oct(stat.S_IMODE(path.stat().st_mode)),
                     'matches_candidate_blob': expected.get(relative) == digest})
    return {'files': rows, 'file_count': len(rows), 'total_bytes': sum(x['bytes'] for x in rows),
            'all_present_files_match_candidate': all(x['matches_candidate_blob'] for x in rows),
            'remote_candidate_file_count': len(expected), 'complete_execution_checkout': False}

def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + '\n')

before = inventory()
write('inputs-before.json', before)
assert before['all_present_files_match_candidate']
commands = [
    ('data-audit', [sys.executable, DOC + '/checkpoint-042-validation/validate_census_data.py']),
    ('documentation-check', [sys.executable, 'docs/maintenance/reorganization-2026-10-17/verify_reorganization.py']),
]
runs = []
for name, argv in commands:
    started = utc()
    result = subprocess.run(argv, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    finished = utc()
    (OUT / (name + '.stdout')).write_bytes(result.stdout)
    (OUT / (name + '.stderr')).write_bytes(result.stderr)
    runs.append({'name': name, 'argv': argv, 'cwd': str(ROOT), 'started_utc': started,
                 'finished_utc': finished, 'exit_code': result.returncode,
                 'stdout': name + '.stdout', 'stderr': name + '.stderr',
                 'stdout_sha256': hashlib.sha256(result.stdout).hexdigest(),
                 'stderr_sha256': hashlib.sha256(result.stderr).hexdigest()})
after = inventory()
write('inputs-after.json', after)
receipt = {'schema': 'ontokin.checkpoint042-local-validation/0.1', 'candidate': publication,
           'source_identity_basis': 'actual GitHub commit/tree; exact bytes of every present local file; no synthetic local Git checkout',
           'interpreter': sys.version, 'executable': sys.executable, 'platform': platform.platform(),
           'runs': runs, 'inputs_stable': before == after, 'input_files': before['file_count'],
           'input_bytes': before['total_bytes'], 'all_present_files_match_candidate': before['all_present_files_match_candidate'],
           'complete_execution_checkout': False, 'product_requests': 0, 'runtime_tests': 0,
           'numerical_replays': 0, 'hosted_jobs_dispatched': 0}
write('receipt.json', receipt)
print(json.dumps({'candidate': publication['core_commit'], 'inputs_stable': receipt['inputs_stable'],
                  'input_files': receipt['input_files'], 'input_bytes': receipt['input_bytes'],
                  'runs': [{'name': x['name'], 'exit_code': x['exit_code']} for x in runs]}, indent=2))
