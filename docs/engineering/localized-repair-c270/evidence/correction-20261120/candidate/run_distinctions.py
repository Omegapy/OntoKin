#!/usr/bin/env python3
"""Record C270 distinction tests against an immutable identified checkout."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--repo', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--phase', required=True)
args = parser.parse_args()
repo, out = args.repo.resolve(), args.output.resolve()
out.mkdir(parents=True, exist_ok=False)
def git(*parts):
    return subprocess.check_output(['git', *parts], cwd=repo, text=True).strip()
def identity(path):
    raw = path.read_bytes()
    return {'path': str(path.relative_to(repo)) if path.is_relative_to(repo) else str(path),
            'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
paths = [repo / ('docs/engineering/localized-repair-c' + component + '/' + filename)
         for component, filename in [('265','source_hinges.py'),('266','hinge_binding.py'),
         ('267','hinge_compare.py'),('268','endpoint_reader.py'),('268','endpoint_control_fixtures.py'),
         ('270','correction/test_refusal_classification.py'),('270','control/EXPECTED.json'),
         ('270','control/main.ok'),('270','control/hinges.ok')]]
command = [sys.executable, '-B', 'docs/engineering/localized-repair-c270/correction/test_refusal_classification.py', '-v']
report = {'schema':'ontokin.c270.correction-distinction-checks/1', 'phase':args.phase,
          'source_revision':git('rev-parse','HEAD'), 'source_tree':git('rev-parse','HEAD^{tree}'),
          'tracked_dirty_before':git('status','--porcelain','--untracked-files=no'),
          'environment':{'python':sys.version,'platform':platform.platform(),'executable':identity(Path(sys.executable).resolve())},
          'runner':identity(Path(__file__).resolve()), 'inputs_before':[identity(p) for p in paths],
          'command':command,'started_at_utc':datetime.now(timezone.utc).isoformat()}
if report['tracked_dirty_before']:
    raise SystemExit('Tracked source is dirty; refusing unbound execution')
result = subprocess.run(command,cwd=repo,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=300)
(out/'distinctions.log').write_bytes(result.stdout)
log = result.stdout.decode('utf-8',errors='replace')
methods = re.findall(r'(?m)^Ran (\d+) tests? in ',log)
report.update(exit_code=result.returncode,methods=int(methods[-1]) if methods else None,
              log=identity(out/'distinctions.log'),finished_at_utc=datetime.now(timezone.utc).isoformat(),
              inputs_after=[identity(p) for p in paths],source_revision_after=git('rev-parse','HEAD'),
              tracked_dirty_after=git('status','--porcelain','--untracked-files=no'))
report['passed'] = result.returncode == 0 and bool(re.search(r'(?m)^OK\r?$',log)) and report['inputs_before']==report['inputs_after'] and report['source_revision']==report['source_revision_after'] and not report['tracked_dirty_after']
report['limits']=['Narrow classification/access controls only; no general source validity, site evaluation, support expansion or full C260/product claim']
(out/'CHECKS.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ('source_revision','methods','exit_code','passed')}))
raise SystemExit(0 if report['passed'] else 1)
