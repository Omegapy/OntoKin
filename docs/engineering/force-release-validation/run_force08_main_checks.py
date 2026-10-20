"""Execute fresh resulting-main checks and re-audit the accepted immutable evidence."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

repo = Path('/workspace/scratch/0229a0b41cd2/OntoKin-force08-integration')
out = Path(sys.argv[1]).absolute()
expected = 'e74dd14bd90bfd0ef7b11d9a939292bb9e5dda4c'
python = '/tmp/ontokin-agent05-validation-venv/bin/python'
node = '/tmp/ontokin-force05-node22/node-v22.20.0-linux-x64/bin/node'
accepted = Path('/tmp/ontokin-force05-evidence-008')
env = dict(os.environ, PATH=str(Path(node).parent) + os.pathsep + os.environ['PATH'],
           PLAYWRIGHT_BROWSERS_PATH='/tmp/ontokin-force05-browsers')
sys.path.insert(0, str(repo))
from ontokin.force_conformance import source_identity

def now():
    return datetime.now(timezone.utc).isoformat()

def sha(path):
    return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()

audit = json.loads((accepted / 'audit.json').read_text())
assert sha(accepted / 'audit.json') == 'sha256:8f78950e2b9c68a4a6023e2565b862b0da6190d450ed2eb10a6d0cdf9d8c4cc8'
before = source_identity()
assert before['git']['commit'] == expected and not before['git']['worktree_changes']
assert before['committed_inputs_match'] and before['inputs'] == audit['source_before']['inputs']
assert before['implementation'] == audit['implementation']
out.mkdir()
(out / 'logs').mkdir()
(out / 'reports').mkdir()
delivery = out / 'delivery'
delivery_audit = out / 'reports/force-delivery-audit.json'
native = out / 'reports/agent-native.json'
tool = 'tools/run_force_conformance.py'

def record(role, primary, argv):
    return (role, [python, tool, 'record', '--role', role, '--output-dir', str(out/'executions'/role),
                   '--report', str(primary), '--', *map(str, argv)])

steps = [('local-force-agent', [python, 'tools/check_local.py', '--force-agent', '--output-dir', str(out/'local')]),
         ('source', [python, tool, 'execute', '--role', 'source', '--output-dir', str(out/'executions/source')]),
         record('force-delivery-build', delivery/'workflow.json', [python, 'tools/build_force_delivery_demo.py', '--output-dir', delivery]),
         record('force-delivery', delivery_audit, [python, 'tools/verify_force_delivery_workflow.py', '--workflow-dir', delivery, '--output', delivery_audit]),
         record('agent-native', native, [node, 'tools/verify_force_native.mjs', '--demo-dir', delivery, '--agent-workflow', '--agent-audit', delivery_audit, '--output', native]),
         ('accepted-evidence-audit', [python, tool, 'audit', '--evidence', str(accepted/'evidence.json'), '--evidence-root', str(accepted), '--output', str(out/'reports/accepted-evidence-audit.json')])]
recording = {'schema_version': 'ontokin.force-resulting-main-checks/0.1', 'started_at_utc': now(),
             'source_before': before, 'accepted_audit_sha256': sha(accepted/'audit.json'),
             'accepted_evidence_sha256': sha(accepted/'evidence.json'), 'eligible_inputs_match_accepted_execution': True,
             'driver_sha256': sha(Path(__file__)), 'pid': os.getpid(), 'plan': [{'role': role, 'argv': argv} for role, argv in steps],
             'steps': [], 'status': 'running', 'full_product_conformance_certified': False}

def save():
    (out/'driver.json').write_text(json.dumps(recording, indent=2)+'\n')

save()
for index, (role, argv) in enumerate(steps):
    print(json.dumps({'event':'start','role':role,'step':index+1,'of':len(steps),'at':now()}), flush=True)
    start = time.monotonic()
    started_at = now()
    log = out/'logs'/(role+'.log')
    with log.open('xb') as stream:
        with subprocess.Popen(argv, cwd=repo, env=env, stdout=stream, stderr=subprocess.STDOUT) as p:
            while True:
                try:
                    p.wait(timeout=45)
                    break
                except subprocess.TimeoutExpired:
                    print(json.dumps({'event':'running','role':role,'seconds':time.monotonic()-start,'at':now()}), flush=True)
    row = {'role':role,'argv':argv,'cwd':str(repo),'started_at_utc':started_at,'finished_at_utc':now(),
           'exit_code':p.returncode,'seconds':time.monotonic()-start,'log':str(log.relative_to(out)),'log_sha256':sha(log)}
    recording['steps'].append(row)
    save()
    print(json.dumps({'event':'finish',**row}), flush=True)
    if p.returncode:
        print(log.read_text()[-6000:], flush=True)
        break
recording.update(source_after=source_identity(), finished_at_utc=now())
recording['source_stable'] = recording['source_before'] == recording['source_after']
recording['status'] = 'passed' if len(recording['steps']) == len(steps) and all(s['exit_code'] == 0 for s in recording['steps']) and recording['source_stable'] else 'failed'
save()
print(json.dumps({'status':recording['status'],'source_stable':recording['source_stable'],'output':str(out)}), flush=True)
raise SystemExit(0 if recording['status'] == 'passed' else 1)
