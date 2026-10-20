"""Record the actual launch identity before entering the isolated executor run."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

runtime = '/tmp/ontokin-agent05-validation-venv/bin/python'
driver = Path('/workspace/scratch/0229a0b41cd2/run_force05_release_acceptance.py')
output, head = Path(sys.argv[1]).absolute(), sys.argv[2]
launch = output.with_name(output.name + '.launch.json')
assert not output.exists() and not launch.exists()
argv = [runtime, '-u', str(driver), str(output), head]
record = {'schema_version': 'ontokin.isolated-execution-launch/0.1',
          'started_at_utc': datetime.now(timezone.utc).isoformat(),
          'pid': os.getpid(), 'argv': argv, 'cwd': str(Path.cwd()),
          'driver_sha256': 'sha256:' + hashlib.sha256(driver.read_bytes()).hexdigest(),
          'expected_published_head': head, 'release_certified': False}
with launch.open('x') as stream:
    stream.write(json.dumps(record, indent=2) + '\n')
print(json.dumps({'event': 'launch', 'record': str(launch), 'pid': os.getpid()}), flush=True)
os.execv(runtime, argv)
