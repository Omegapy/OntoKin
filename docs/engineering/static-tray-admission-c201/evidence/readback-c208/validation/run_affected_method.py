from pathlib import Path
import datetime,json,platform,subprocess,sys,unittest,hashlib,os
repo=Path('/tmp/ontokin-c208-4c105e/repo');out=Path('/workspace/scratch/4c105edcd17c/validation/main-affected-method');out.mkdir(exist_ok=False)
os.chdir(repo);sys.path.insert(0,str(repo));sys.dont_write_bytecode=True
head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();assert head=='f8e397405b432d7a63464b136431d15a009c38df'
source=repo/'tests/test_static_tray_admission_c201_readback_binding.py';before=hashlib.sha256(source.read_bytes()).hexdigest();environment=platform.platform();attempts=[]
def guard(event,args):
 if event in {'subprocess.Popen','os.system','os.fork','os.forkpty','os.posix_spawn','os.exec'}:
  attempts.append(event);raise RuntimeError('No child starts in CPU check')
sys.addaudithook(guard)
name='tests.test_static_tray_admission_c201_readback_binding.ReadbackBindingControls.test_actual_four_slot_bindings_and_measurements_without_authority'
with (out/'tests.log').open('w') as stream:result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName(name))
record={'schema':'ontokin.c208.affected-main-method/0.1','recordedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'commit':head,'python':platform.python_version(),'platform':environment,'method':name,'testsRun':result.testsRun,'success':result.wasSuccessful() and not attempts,'failures':result.failures,'errors':result.errors,'skipped':result.skipped,'childStartAttempts':attempts,'sourceSha256':before,'sourceUnchanged':hashlib.sha256(source.read_bytes()).hexdigest()==before,'changedInput':'No source, expectation or limit changed. Other CPU check and recovery archive jobs are stopped for this affected-method diagnosis.'}
(out/'RESULT.json').write_text(json.dumps(record,indent=2,default=str)+'\n');print(json.dumps(record,default=str));raise SystemExit(0 if record['success'] else 1)
