"""Compare actual C209 source and review controls with independently retained hashes."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--repo', type=Path, required=True)
parser.add_argument('--review', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
manifest = json.loads((args.review/'REVIEWED-INPUTS-initial.json').read_text())
rows = []
for source in manifest['files']:
    name = source['relative']
    path = (args.review/name.split('/', 1)[1]) if name.startswith('independent-review/') else args.repo/name
    raw = path.read_bytes() if path.is_file() else None
    actual = hashlib.sha256(raw).hexdigest() if raw is not None else None
    rows.append({'path': name, 'expectedSha256': source['sha256'], 'actualSha256': actual,
                 'sizeBytes': len(raw) if raw is not None else None,
                 'match': actual == source['sha256'] and raw is not None and len(raw) == source['size_bytes']})
def git(*words):
    return subprocess.check_output(['git', '-C', str(args.repo), *words], text=True).strip()
shared = git('diff', '--name-status', manifest['base'], 'HEAD', '--', 'ontokin', 'tools', '.github',
             'prototypes/static_tray_v01', 'fixtures/static_tray_v01',
             'docs/engineering/static-tray-mapping-c198', 'docs/engineering/static-tray-qualification-c199',
             'docs/engineering/static-tray-exporter-c200')
record = {'schema': 'ontokin.c209.reviewed-input-equality/0.1',
          'observedAtUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'reviewedCommit': manifest['candidate'], 'actualCommit': git('rev-parse', 'HEAD'),
          'actualTree': git('rev-parse', 'HEAD^{tree}'), 'worktreeStatus': git('status', '--porcelain'),
          'reviewedInputCount': len(rows), 'files': rows, 'sharedRuntimeWorkflowHistoricalDiff': shared,
          'passed': all(row['match'] for row in rows) and not shared,
          'scope': 'Byte equality supports reuse of the component-only review; no execution authority'}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(record, indent=2)+'\n')
print(json.dumps({k: record[k] for k in ('actualCommit','reviewedInputCount','passed')}))
raise SystemExit(0 if record['passed'] else 1)
