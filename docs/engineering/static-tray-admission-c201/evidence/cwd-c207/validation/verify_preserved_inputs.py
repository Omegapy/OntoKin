"""Check immutable inherited inputs against preserved C206 evidence."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--repo', type=Path, required=True)
p.add_argument('--baseline', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
baseline = json.loads(a.baseline.read_text())
def check(rows):
    result = []
    for row in rows:
        path = a.repo / row['path']
        actual_size = path.stat().st_size if path.is_file() else None
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        result.append({'path': row['path'], 'size_bytes': row['size_bytes'], 'sha256': row['sha256'],
                       'observed_size_bytes': actual_size, 'observed_sha256': actual_hash,
                       'match': actual_size == row['size_bytes'] and actual_hash == row['sha256']})
    return result
locked = check(baseline['lockedInputs'])
protocol = check(baseline['protocolDocuments'])
git = lambda *args: subprocess.check_output(['git', '-C', str(a.repo), *args], text=True).strip()
result = {'schema': 'ontokin.c207.protected-inputs/0.1',
          'atUtc': datetime.now(timezone.utc).isoformat(), 'commit': git('rev-parse', 'HEAD'),
          'tree': git('rev-parse', 'HEAD^{tree}'), 'baseline': str(a.baseline),
          'lockedInputs': locked, 'lockedInputsCount': len(locked),
          'lockedInputsAllMatch': all(row['match'] for row in locked),
          'protocolDocuments': protocol, 'allProtocolDocumentsMatch': all(row['match'] for row in protocol),
          'changesFromStartingMain': git('diff', '--name-status', '2a1ac8ccbdc290942e88504c640790b1bda9229c', 'HEAD'),
          'legacyFullRegression': {'state': 'FAILED', 'distinctPassingMethods': 4239,
                                   'torqueReadMethodsNotRun': 13, 'unchangedSetupTimeoutMs': 30000,
                                   'rerunThisSession': False}}
result['passed'] = result['lockedInputsAllMatch'] and result['allProtocolDocumentsMatch']
a.output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: result[k] for k in ['commit', 'lockedInputsCount', 'lockedInputsAllMatch', 'allProtocolDocumentsMatch', 'passed']}))
raise SystemExit(0 if result['passed'] else 1)
