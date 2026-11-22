from pathlib import Path
import datetime, hashlib, json, subprocess, time

W=Path('/workspace/scratch/816157c5a30b');T=W/'technical'
plan_bytes=(T/'OBSERVATION-PLAN.json').read_bytes()
assert hashlib.sha256(plan_bytes).hexdigest()=='946fd14dc1022ddb1e9cc4d8f22a0c0a2746efb3b0b9c08db62cd70c17945aab'
plan=json.loads(plan_bytes)
for key in ('script','source','lock'):
    b=Path(plan[key]['path']).read_bytes()
    assert hashlib.sha256(b).hexdigest()==plan[key]['sha256']
    if 'bytes' in plan[key]: assert len(b)==plan[key]['bytes']
assert not Path(plan['output']).exists()
assert not (T/'LAUNCH-INTENT.json').exists()
review=W/'operational_review/PREEXEC-REVIEW-003.json'
assert review.is_file()
intent={'schema':'ontokin.c271.p19-launch/1','at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'plan_sha256':hashlib.sha256(plan_bytes).hexdigest(),'review_sha256':hashlib.sha256(review.read_bytes()).hexdigest(),'wrapper_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'argv':plan['command'],'environment':plan['environment'],'cwd':plan['cwd'],'timeout_seconds':60,'attempt':'attempt001','actual_invocation_retries':0,'process_denominator':'One Python observation process; zero child/target operations permitted inside'}
with (T/'LAUNCH-INTENT.json').open('x') as f: json.dump(intent,f,indent=2);f.write('\n')
start=time.monotonic()
try:
    run=subprocess.run(plan['command'],cwd=plan['cwd'],env=plan['environment'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60,check=False)
    (T/'observation.stdout').write_bytes(run.stdout);(T/'observation.stderr').write_bytes(run.stderr)
    result={'schema':'ontokin.c271.p19-launch-result/1','returncode':run.returncode,'elapsed_seconds':time.monotonic()-start,'stdout_sha256':hashlib.sha256(run.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(run.stderr).hexdigest(),'completed':True,'retry':False}
except subprocess.TimeoutExpired as exc:
    (T/'observation.stdout').write_bytes(exc.stdout or b'');(T/'observation.stderr').write_bytes(exc.stderr or b'')
    result={'schema':'ontokin.c271.p19-launch-result/1','completed':False,'timeout_seconds':60,'elapsed_seconds':time.monotonic()-start,'retry':False,'state':'interrupted_observation_requires_reconciliation'}
with (T/'LAUNCH-RESULT.json').open('x') as f: json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(result));print((T/'observation.stdout').read_text());print((T/'observation.stderr').read_text())
