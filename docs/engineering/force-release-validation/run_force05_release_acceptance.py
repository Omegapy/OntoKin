"""Run fresh repository acceptance roles sequentially in one executor window."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

repo = Path('/workspace/scratch/0229a0b41cd2/OntoKin')
out = Path(sys.argv[1]).absolute()
expected_head = sys.argv[2]
python = '/tmp/ontokin-agent05-validation-venv/bin/python'
pythons = {'3.11': '/tmp/ontokin-force05-venv311/bin/python', '3.12': python,
           '3.13': '/tmp/ontokin-force05-venv313/bin/python'}
node = '/tmp/ontokin-force05-node22/node-v22.20.0-linux-x64/bin/node'
tool = 'tools/run_force_conformance.py'
environment = dict(os.environ, PLAYWRIGHT_BROWSERS_PATH='/tmp/ontokin-force05-browsers',
                   PATH=str(Path(node).parent) + os.pathsep + os.environ['PATH'])

def now():
    return datetime.now(timezone.utc).isoformat()

def revision():
    return {'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip(),
            'tree': subprocess.check_output(['git', 'rev-parse', 'HEAD^{tree}'], cwd=repo, text=True).strip(),
            'changes': subprocess.check_output(['git', 'status', '--porcelain'], cwd=repo, text=True).splitlines()}

def execute(role, name=None, interpreter=python):
    return (name or role, [interpreter, tool, 'execute', '--role', role, '--output-dir', str(out/'executions'/(name or role))])

def record(role, primary, argv):
    return (role, [python, tool, 'record', '--role', role, '--output-dir', str(out/'executions'/role),
                  '--report', str(primary), '--', *map(str, argv)])

source = out/'artifacts/source-force'
agent = out/'artifacts/force-agent'
delivery = out/'artifacts/force-delivery'
source_audit = out/'reports/force-agent-audit.json'
delivery_audit = out/'reports/force-delivery-audit.json'
source_native = out/'reports/force-native.json'
agent_native = out/'reports/agent-native.json'
source_browser = out/'artifacts/force-browser'
agent_browser = out/'artifacts/agent-browser'
legacy = out/'legacy-full'
steps = [execute('source'), execute('mapped-tests')]
steps += [record('source-build', source/'workflow.json', [python, 'tools/build_force_demo.py', '--output-dir', source]),
          record('force-agent-build', agent/'workflow.json', [python, 'tools/build_force_agent_demo.py', '--output-dir', agent]),
          record('force-agent', source_audit, [python, 'tools/verify_force_agent_workflow.py', '--workflow-dir', agent, '--output', source_audit]),
          record('force-delivery-build', delivery/'workflow.json', [python, 'tools/build_force_delivery_demo.py', '--output-dir', delivery]),
          record('force-delivery', delivery_audit, [python, 'tools/verify_force_delivery_workflow.py', '--workflow-dir', delivery, '--output', delivery_audit]),
          record('force-native', source_native, [node, 'tools/verify_force_native.mjs', '--demo-dir', source, '--output', source_native]),
          record('agent-native', agent_native, [node, 'tools/verify_force_native.mjs', '--demo-dir', delivery, '--agent-workflow', '--agent-audit', delivery_audit, '--output', agent_native]),
          record('force-browser', source_browser/'browser-validation.json', [node, 'tools/verify_force_viewer.mjs', '--demo-dir', source, '--output-dir', source_browser]),
          record('agent-browser', agent_browser/'browser-validation.json', [node, 'tools/verify_force_viewer.mjs', '--demo-dir', delivery, '--agent-workflow', '--agent-audit', delivery_audit, '--output-dir', agent_browser])]
steps += [execute('regression', 'regression-'+version, interpreter) for version,interpreter in pythons.items()]
steps += [execute(role) for role in ('core','agent','construction','surface','impulse')]
steps += [record('legacy-visual', legacy/'summary.json', [python, 'tools/check_local.py', '--full', '--force-agent', '--output-dir', legacy])]
before = revision()
assert before['commit'] == expected_head and not before['changes'], before
out.mkdir()
(out/'driver-logs').mkdir(); (out/'reports').mkdir(); (out/'artifacts').mkdir(); (out/'executions').mkdir()
recording = {'schema_version': 'ontokin.force-release-execution-driver/0.1', 'started_at_utc': now(),
             'source_before': before, 'driver_sha256': 'sha256:'+hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             'plan': [{'role': name, 'argv': argv} for name,argv in steps], 'steps': [],
             'status': 'running', 'full_force_release_complete': False}

def save():
    (out/'driver.json').write_text(json.dumps(recording, indent=2)+'\n')

save()
for index,(name,argv) in enumerate(steps):
    print(json.dumps({'event':'start','role':name,'step':index+1,'of':len(steps),'at':now()}), flush=True)
    started = time.monotonic(); log = out/'driver-logs'/(name+'.log')
    with log.open('wb') as stream:
        with subprocess.Popen(argv, cwd=repo, env=environment, stdout=stream, stderr=subprocess.STDOUT) as completed:
            while True:
                try:
                    completed.wait(timeout=45)
                    break
                except subprocess.TimeoutExpired:
                    print(json.dumps({'event':'running','role':name,'seconds':time.monotonic()-started,
                                      'at':now()}),flush=True)
    row = {'role':name, 'argv':argv, 'exit_code':completed.returncode, 'seconds':time.monotonic()-started,
           'log':str(log.relative_to(out)), 'log_sha256':'sha256:'+hashlib.sha256(log.read_bytes()).hexdigest()}
    recording['steps'].append(row); save(); print(json.dumps({'event':'finish',**row}), flush=True)
    if completed.returncode:
        print(log.read_text()[-6000:], flush=True)
        break
recording.update(source_after=revision(), finished_at_utc=now())
recording['source_stable'] = recording['source_before'] == recording['source_after']
recording['status'] = 'passed' if len(recording['steps'])==len(steps) and all(row['exit_code']==0 for row in recording['steps']) and recording['source_stable'] else 'failed'
save()
print(json.dumps({'status':recording['status'],'source_stable':recording['source_stable'],'output':str(out)}),flush=True)
raise SystemExit(0 if recording['status']=='passed' else 1)
