"""Independent C208 public-API corruption controls; no external-stage execution."""
from __future__ import annotations
import argparse, contextlib, dataclasses, datetime, hashlib, json, os, pathlib, platform
import subprocess, sys, traceback, unittest
from copy import deepcopy
from unittest import mock

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--repo',type=pathlib.Path,required=True)
p.add_argument('--out',type=pathlib.Path,required=True)
p.add_argument('--expected-commit',required=True)
a=p.parse_args();repo=a.repo.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)

def git(*args):
    return subprocess.run(['git','--no-optional-locks','-C',str(repo),*args],check=True,capture_output=True,text=True).stdout.strip()

head=git('rev-parse','HEAD');tree=git('rev-parse','HEAD^{tree}');status=git('status','--porcelain=v1')
assert head==a.expected_commit,(head,a.expected_commit)
started=datetime.datetime.now(datetime.timezone.utc).isoformat()
sys.path.insert(0,str(repo))
armed=True;launch_attempts=[]
def audit_hook(event,args):
    if armed and event in {'subprocess.Popen','os.system','os.posix_spawn','os.fork','os.forkpty','os.exec'}:
        launch_attempts.append(event)
        raise AssertionError('Independent controls forbid process creation: '+event)
sys.addaudithook(audit_hook)

from fixture_support import Fixture, LIMITS, digest, encode, measurements
from prototypes.static_tray_admission_c201 import readback_binding as rb


class Controls(unittest.TestCase):
    def setUp(self):
        self.fixture=None
        self.blockers=[]
        for name in ('subprocess.Popen','os.fork','os.system','os.posix_spawn','os.posix_spawnp'):
            def forbidden(*args,_name=name,**kwargs):
                launch_attempts.append(_name)
                raise AssertionError('Independent controls forbid process creation: '+_name)
            self.blockers.append(self.enterContext(mock.patch(name,side_effect=forbidden)))

    def fixture_for(self,slot='A01'):
        fx=Fixture(slot);self.fixture=fx;self.addCleanup(fx.close);return fx

    def reject(self,fx,call=None,state=None):
        pointer=fx.pointer.read_bytes()
        with self.assertRaises(rb.ReadbackError) as caught:
            (call or fx.verify)()
        self.assertEqual(fx.pointer.read_bytes(),pointer)
        if state:self.assertEqual(caught.exception.state,state)
        return caught.exception

    def test_valid_four_slots_are_only_consistency_evidence(self):
        for name in ('A01','A02','A03','A04'):
            fx=self.fixture_for(name)
            answer=fx.verify()
            self.assertEqual(answer.state,'BINDINGS_VERIFIED')
            self.assertEqual(answer.slot,name)
            self.assertGreater(answer.measurement_count,2000)
            for field in ('authenticated_execution','node_start_authorized','native_start_authorized',
                          'native_readiness','admission_completed','next_slot_authorized'):
                self.assertIs(getattr(answer,field),False)
            self.assertEqual(fx.pointer_before,fx.pointer.read_bytes())
            self.assertEqual(answer.accepted_pointer_sha256,digest(fx.pointer_before))

    def test_job_is_explicit_immutable_binding_and_contains_exact_limits(self):
        fx=self.fixture_for();job=fx.job
        self.assertEqual(job['schema'],'ontokin.c201.readback-job/0.1')
        self.assertEqual(job['slot'],'A01');self.assertEqual(job['route'],'ontokin')
        self.assertEqual(job['limits'],LIMITS)
        self.assertEqual(job['command']['cwd'],str(fx.stage))
        self.assertEqual(job['command']['argv'][-2:],['--job',str(fx.stage/'job.json')])
        self.assertEqual(job['artifact']['sha256'],digest(pathlib.Path(job['artifact']['path']).read_bytes()))
        job['checks']['three']['position_tolerance_m']=1
        self.assertEqual(rb.inspect_readback_job(fx.prepared)['checks']['three']['position_tolerance_m'],0.000005)

    def test_reconstructed_prepared_handle_rejects(self):
        fx=self.fixture_for();false=dataclasses.replace(fx.prepared,job_bytes=fx.prepared.job_bytes)
        self.reject(fx,lambda:rb.verify_readback_result(false,process=fx.process))
        self.assertEqual(fx.verify().state,'BINDINGS_VERIFIED')

    def test_duplicate_completion_is_rejected(self):
        fx=self.fixture_for();fx.verify();self.reject(fx,state='REJECTED')

    def test_failed_result_stops_session_and_retains_partial_outputs(self):
        fx=self.fixture_for();fx.probe['passed']=False;fx.emit()
        before={p.name:p.read_bytes() for p in fx.stage.iterdir()}
        self.reject(fx,state='REJECTED')
        self.reject(fx,state='REJECTED')
        error=self.reject(fx,lambda:rb.prepare_readback(fx.binding,'A02',accepted=fx.accepted))
        self.assertTrue(error.code.endswith('REPLAY'))
        self.assertEqual(before,{p.name:p.read_bytes() for p in fx.stage.iterdir()})

    def test_unknown_result_preserves_unknown_and_stops_retry(self):
        fx=self.fixture_for();fx.probe['state']='UNKNOWN';fx.emit()
        self.reject(fx,state='UNKNOWN');self.reject(fx,state='REJECTED')

    def test_interrupt_returns_unknown_and_does_not_replay(self):
        fx=self.fixture_for()
        with mock.patch.object(rb,'_outputs',side_effect=KeyboardInterrupt('Controlled verification interruption')):
            self.reject(fx,state='UNKNOWN')
        self.reject(fx,state='REJECTED')

    def test_changed_job_command_rejects(self):
        fx=self.fixture_for();job=deepcopy(fx.job);job['command']['argv'].insert(1,'--inspect')
        pathlib.Path(job['outputs']['job']).write_bytes(encode(job));self.reject(fx)

    def test_changed_bound_source_rejects(self):
        fx=self.fixture_for();source=fx.transactions.inputs.repo/'prototypes/static_tray_v01/worker.py'
        source.write_bytes(source.read_bytes()+b'\n# changed independent control\n');self.reject(fx)

    def test_changed_accepted_artifact_rejects_without_pointer_write(self):
        fx=self.fixture_for();artifact=pathlib.Path(fx.job['artifact']['path']);artifact.chmod(0o600)
        artifact.write_bytes(artifact.read_bytes()+b'changed');self.reject(fx)

    def test_changed_accepted_pointer_is_not_repaired_or_accepted(self):
        fx=self.fixture_for();value=json.loads(fx.pointer.read_bytes());value['revision']='unrelated'
        fx.pointer.write_bytes(encode(value));self.reject(fx)

    def test_missing_probe_rejects(self):
        fx=self.fixture_for();pathlib.Path(fx.job['outputs']['probe']).unlink();self.reject(fx)

    def test_extra_output_rejects(self):
        fx=self.fixture_for();(fx.stage/'unexpected.json').write_text('{}');self.reject(fx)

    def test_probe_symlink_rejects(self):
        fx=self.fixture_for();path=pathlib.Path(fx.job['outputs']['probe']);path.unlink()
        path.symlink_to(fx.job['audit']['path']);self.reject(fx)

    def test_probe_hardlink_rejects(self):
        fx=self.fixture_for();path=pathlib.Path(fx.job['outputs']['probe'])
        copy=pathlib.Path(fx.temporary.name)/'probe-copy.json';copy.write_bytes(path.read_bytes());path.unlink();os.link(copy,path)
        self.reject(fx)

    def test_probe_fifo_rejects_without_blocking(self):
        fx=self.fixture_for();path=pathlib.Path(fx.job['outputs']['probe']);path.unlink();os.mkfifo(path);self.reject(fx)

    def test_probe_byte_cap_rejects(self):
        fx=self.fixture_for();pathlib.Path(fx.job['outputs']['probe']).write_bytes(b' '*4194305);self.reject(fx)

    def test_changed_logs_reject_even_when_result_says_passed(self):
        fx=self.fixture_for();pathlib.Path(fx.job['outputs']['stdout']).write_bytes(fx.stdout+b'changed');self.reject(fx)

    def test_successful_29_second_child_cannot_use_30_second_outer_budget(self):
        fx=self.fixture_for();fx.record['end_monotonic']=129.0;fx.process['completed_monotonic']=129.0;fx.emit();self.reject(fx)

    def test_nonfinite_process_time_rejects(self):
        fx=self.fixture_for();fx.process['completed_monotonic']=float('nan');self.reject(fx)

    def test_nonfinite_json_constant_rejects(self):
        fx=self.fixture_for();fx.probe['three']['nodes']['equipment-tray/pair/left']['world_matrix'][0][0]=float('nan')
        pathlib.Path(fx.job['outputs']['probe']).write_bytes(json.dumps(fx.probe,allow_nan=True).encode());self.reject(fx)

    def test_numeric_overflow_matrix_rejects(self):
        fx=self.fixture_for();fx.probe['three']['nodes']['equipment-tray/pair/left']['world_matrix'][0][0]=float('inf')
        raw=json.dumps(fx.probe,allow_nan=True).replace('Infinity','1e309').encode()
        pathlib.Path(fx.job['outputs']['probe']).write_bytes(raw);self.reject(fx)

    def test_duplicate_json_field_rejects(self):
        fx=self.fixture_for();raw=encode(fx.probe);pathlib.Path(fx.job['outputs']['probe']).write_bytes(b'{"passed":true,'+raw[1:]);self.reject(fx)

    def test_forged_geometry_and_self_reported_zero_difference_reject(self):
        fx=self.fixture_for();ident='equipment-tray/pair/left/back';node=fx.probe['three']['nodes'][ident]
        for coordinate in node['world_vertices']:coordinate[0]+=0.1
        for coordinate in node['positions']:coordinate[0]+=0.1
        node['world_bounds']=[[f(v[i] for v in node['world_vertices']) for i in range(3)] for f in (min,max)]
        for row in fx.probe['three']['measurements']:
            if row['semantic_id']==ident and row['field'].startswith(('world_vertex','world_min','world_max')):
                row['actual']+=0.1;row['expected']=row['actual'];row['difference']=0
        fx.emit();self.reject(fx)

    def test_local_positions_must_agree_with_retained_world_positions(self):
        fx=self.fixture_for();fx.probe['three']['nodes']['equipment-tray/pair/left/back']['positions'][0][0]+=0.2;fx.emit();self.reject(fx)

    def test_within_position_tolerance_keeps_historical_measurement_semantics(self):
        fx=self.fixture_for();ident='equipment-tray/pair/left/back';node=fx.probe['three']['nodes'][ident]
        for v in node['world_vertices']:v[0]+=0.000004
        for v in node['positions']:v[0]+=0.000004
        node['world_bounds']=[[f(v[i] for v in node['world_vertices']) for i in range(3)] for f in (min,max)]
        fx.probe['three']['measurements']=measurements(fx.probe['three']['nodes'],fx.audit)
        fx.emit();self.assertEqual(fx.verify().state,'BINDINGS_VERIFIED')


def assign(path,value):
    def mutate(fx):
        target=fx
        for key in path[:-1]:target=getattr(target,key) if isinstance(key,str) and hasattr(target,key) else target[key]
        target[path[-1]]=value
    return mutate

cases={
 'wrong_slot':assign(('probe','slot'),'A02'),
 'wrong_source_commit':assign(('probe','source','commit'),'f'*40),
 'wrong_source_tree':assign(('probe','source','tree'),'f'*40),
 'wrong_accepted_revision':assign(('probe','accepted_revision'),'f'*64),
 'wrong_artifact_digest':assign(('probe','artifact_sha256'),'f'*64),
 'wrong_audit_digest':assign(('probe','audit_sha256'),'f'*64),
 'wrong_lock_digest':assign(('probe','input_lock_sha256'),'f'*64),
 'wrong_job_digest':assign(('probe','job_sha256'),'f'*64),
 'wrong_route':assign(('probe','route'),'direct-python'),
 'wrong_probe_schema':assign(('probe','schema'),'ontokin.static-tray.external-readback/0.1.0'),
 'forged_authority_field':assign(('probe','next_slot_authorized'),True),
 'wrong_requested_limit':assign(('process','requested_limits','child_work_ms'),30000),
 'wrong_effective_limit':assign(('process','effective_limits','outer_ms'),30001),
 'wrong_probe_limit':assign(('probe','limits','result_bytes'),8388608),
 'wrong_process_cwd':assign(('process','command','cwd'),'/tmp'),
 'wrong_process_environment':assign(('process','command','environment','NODE_OPTIONS'),'--inspect'),
 'wrong_supervisor_cwd':assign(('record','cwd'),'/tmp'),
 'failed_exit_code':assign(('process','returncode'),1),
 'open_handles':assign(('process','handles_closed'),False),
 'unknown_cleanup':assign(('process','cleanup','reaped'),None),
 'failed_supervisor_cleanup':assign(('record','cleanup','passed'),False),
 'wrong_khronos_version':assign(('probe','khronos','version'),'wrong'),
 'khronos_warning':assign(('probe','khronos','report','issues','numWarnings'),1),
 'khronos_truncation':assign(('probe','khronos','report','issues','truncated'),True),
 'hidden_khronos_warning':assign(('probe','khronos','report','issues','messages'),[{'severity':1,'code':'HIDDEN'}]),
 'khronos_boolean_count':assign(('probe','khronos','report','issues','numErrors'),False),
 'unexpected_scene':assign(('probe','three','scenes'),2),
 'wrong_three_version':assign(('probe','three','version'),'0.187.0'),
 'weakened_tolerance':assign(('probe','three','position_tolerance_m'),0.001),
 'unexpected_texture':assign(('probe','three','textures'),['image.png']),
 'missing_measurements':assign(('probe','three','measurements'),[]),
 'bool_matrix_value':assign(('probe','three','nodes','equipment-tray/pair/left','world_matrix',0,0),True),
 'wrong_parent':assign(('probe','three','nodes','equipment-tray/pair/left/back','parent'),None),
 'wrong_original_name':assign(('probe','three','nodes','equipment-tray/pair/left/back','original_name'),'other'),
 'boolean_index':assign(('probe','three','nodes','equipment-tray/pair/left/back','indices',0),False),
 'material_changed':assign(('probe','three','nodes','equipment-tray/pair/left/back','material','doubleSided'),True),
 'non_preserved_input':assign(('probe','input_preserved'),False),
}
for name,mutation in cases.items():
    def test(self,_mutate=mutation):
        fx=self.fixture_for();_mutate(fx);fx.emit();self.reject(fx)
    setattr(Controls,'test_reject_'+name,test)

class RecordedResult(unittest.TextTestResult):
    def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.outcomes=[]
    def addSuccess(self,test):super().addSuccess(test);self.outcomes.append({'case':test.id(),'outcome':'passed'})
    def addFailure(self,test,err):super().addFailure(test,err);self.capture(test,err,'failed')
    def addError(self,test,err):super().addError(test,err);self.capture(test,err,'error')
    def capture(self,test,err,kind):
        self.outcomes.append({'case':test.id(),'outcome':kind,'error':''.join(traceback.format_exception(*err))})
        fx=getattr(test,'fixture',None)
        if fx is not None:
            folder=out/'failed-controls'/test.id().split('.')[-1];folder.mkdir(parents=True,exist_ok=True)
            for name in ('job.json','probe.json','node.process.json','node.stdout.log','node.stderr.log'):
                f=fx.stage/name
                if f.is_file() and not f.is_symlink():(folder/name).write_bytes(f.read_bytes())
            (folder/'accepted-pointer.json').write_bytes(fx.pointer.read_bytes())

with (out/'controls.log').open('w') as log:
    result=unittest.TextTestRunner(stream=log,verbosity=2,resultclass=RecordedResult).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
armed=False
inputs=set()
for module in list(sys.modules.values()):
    f=getattr(module,'__file__',None)
    if f:
        path=pathlib.Path(f).resolve()
        if path.is_file() and path.suffix=='.py' and path.is_relative_to(repo):inputs.add(path.relative_to(repo).as_posix())
for name in ['AGENTS.md','GOAL.md','STATUS.md','docs/engineering/static-tray-admission-c201/ADMISSION.md',
 'docs/engineering/static-tray-admission-c201/ADMISSION.json','docs/engineering/static-tray-admission-c201/INPUT-LOCK-C205.md',
 'docs/engineering/static-tray-admission-c201/TRANSACTION-C206.md','docs/engineering/static-tray-admission-c201/WORKING-DIRECTORIES-C207.md',
 'docs/engineering/static-tray-admission-c201/READBACK-BINDING-C208.md','prototypes/static_tray_v01/readback.mjs',
 'prototypes/static_tray_v01/format_check.py','tests/test_static_tray_admission_c201_readback_binding.py']:
    if (repo/name).is_file():inputs.add(name)
bindings=[{'path':name,'sizeBytes':(repo/name).stat().st_size,'sha256':digest((repo/name).read_bytes())} for name in sorted(inputs)]
(out/'SOURCE-BINDINGS.json').write_text(json.dumps({'commit':head,'tree':tree,'sourceFiles':bindings,'controlFiles':[{'path':str(f),'sha256':digest(f.read_bytes()),'sizeBytes':f.stat().st_size} for f in (pathlib.Path(__file__).resolve(),pathlib.Path(__file__).with_name('fixture_support.py').resolve())]},indent=2)+'\n')
final={'schema':'ontokin.c208.independent-cpu-controls/0.1','startedAtUtc':started,'completedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'sourceCommit':head,'sourceTree':tree,'sourceStatus':status,'pythonExecutable':sys.executable,'pythonVersion':platform.python_version(),'platform':platform.platform(),
 'methods':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),'outcomes':result.outcomes,'launchAttempts':launch_attempts,
 'nativeStarts':0,'nodeStarts':0,'receivingStarts':0,'lifecycleStarts':0,'timedAuthorStarts':0,'purpose':'Synthetic CPU binding consistency only; no actual external execution or authenticated receipt claim',
 'passed':result.wasSuccessful() and not launch_attempts,'finalCommit':git('rev-parse','HEAD'),'reviewedBindings':len(bindings)}
(out/'RESULT.json').write_text(json.dumps(final,indent=2)+'\n')
print(json.dumps({k:final[k] for k in ('sourceCommit','methods','failures','errors','skips','launchAttempts','passed','reviewedBindings')}))
raise SystemExit(0 if final['passed'] and final['finalCommit']==head else 1)
