"""Independent C205 CPU-only controls using actual validator and labeled fixture."""
from pathlib import Path
from dataclasses import replace, asdict
from contextlib import ExitStack
from unittest import mock
import datetime, hashlib, importlib.util, json, os, signal, sys, tempfile, time
sys.dont_write_bytecode = True
REPO = Path('/workspace/scratch/4ba2fd100db8/repo')
sys.path.insert(0, str(REPO))
from prototypes.static_tray_admission_c201 import input_lock as mod
from prototypes.static_tray_admission_c201.schedule import canonical
from prototypes.static_tray_admission_c201.ledger import MARKER
spec=importlib.util.spec_from_file_location('c205_fixture', REPO/'tests/test_static_tray_admission_c201_input_lock.py')
fixtures=importlib.util.module_from_spec(spec); spec.loader.exec_module(fixtures)
OUT=Path(__file__).parent

def reseal(f, *, closure=False, plan=False):
    """Explicit fixture-only independent-anchor rebinding for structural controls."""
    if closure:
        f.context=replace(f.context,closure_sha256=mod.closure_digest(f.lock))
        for binding in f.lock['gate_receipts'].values():
            root=Path(f.context.repository_root if binding['root']=='repository' else f.context.host_root)
            path=root/binding['path']; receipt=json.loads(path.read_bytes())
            receipt['closure_sha256']=f.context.closure_sha256
            path.write_bytes(canonical(receipt))
            binding.update(size_bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),mode=path.stat().st_mode & 0o777)
    if plan:f.context=replace(f.context,launch_plan_sha256=mod.launch_plan_digest(f.lock))
    f.repin()

def good(f):
    value=f.validate()
    assert value.purpose=='fixture-only'
    assert value.native_start_authorized is False and value.native_readiness is False and value.admission_completed is False

def nested_slash(f):
    p=f.repo/'nested-output';p.mkdir();v='/'+str(p)
    old=f.lock['outputs']['A01']['construction'];f.lock['outputs']['A01']['construction']=v
    cmd=f.lock['commands']['A01']['construction'];cmd['output']=v;cmd['argv']=[x.replace(old,v) for x in cmd['argv']]
    reseal(f,plan=True)

def frozen_dependency(f):
    extra='host:transitive-library'
    f.lock['dependencies']['host:shared_libraries']=[]
    root=f.lock['roles']['constructor'][0]
    f.lock['dependencies'][root]=[extra]
    reseal(f,closure=True)

def missing_transitive(f):
    f.lock['inputs'].pop('host:transitive-library')
    f.lock['dependencies'].pop('host:transitive-library')
    f.lock['dependencies']['host:shared_libraries']=[]
    f.repin()

def fixed_role_missing(f):
    f.lock['roles'].pop('admission_transaction');reseal(f,closure=True)

def changed_bytes(f):
    p=f.host/'transitive-library';data=p.read_bytes();p.write_bytes(b'X'+data[1:])

def fifo_lock(f):
    f.lock_path.unlink();os.mkfifo(f.lock_path)

def symlink_ancestor(f):
    folder=f.host/'directory';folder.mkdir();old=f.host/'transitive-library';p=folder/old.name;old.rename(p);old.symlink_to(p)

def replaced_authority(f):
    f.authority.rename(f.base/'retained-original-authority');f.authority.mkdir()

def replay_new_output(f):
    (f.authority/MARKER).write_bytes(b'preserved uncertain invocation\n')
    p=f.base/'different-output';p.mkdir()
    old=f.lock['outputs']['A01']['construction'];f.lock['outputs']['A01']['construction']=str(p)
    cmd=f.lock['commands']['A01']['construction'];cmd['output']=str(p);cmd['argv']=[x.replace(old,str(p)) for x in cmd['argv']]
    reseal(f,plan=True)

def missing_gate(f):
    f.lock['gate_receipts'].pop('current_host');f.repin()

def self_review(f):
    f.context=replace(f.context,reviewer=f.context.producer);f.repin()

def wrong_approval_commit(f):
    f.approval['source_commit']='3'*40;f.save_approval()

def nonboolean_receipt(f):
    b=f.lock['gate_receipts']['current_host'];p=f.host/b['path'];v=json.loads(p.read_bytes());v['passed']=1;p.write_bytes(canonical(v));b.update(f.binding(p,'host'));f.repin()

def malformed_type(f):
    f.lock['schedule']['slots'][0]['maximum_native_starts']=True;f.repin()

def duplicate_keys(f):
    raw=f.lock_path.read_bytes();raw=b'{"schema":"shadowed",'+raw[1:];f.lock_path.write_bytes(raw)
    f.context=replace(f.context,lock_sha256=hashlib.sha256(raw).hexdigest())

def missing_safe_native_flag(f):
    f.lock['commands']['A01']['construction']['argv'].remove('--factory-startup');reseal(f,plan=True)

def unsafe_blender_environment(f):
    f.lock['commands']['A01']['construction']['environment']['BLENDER_USER_SCRIPTS']=str(f.repo);reseal(f,plan=True)

def node_evaluation_extra(f):
    f.lock['commands']['A01']['node']['argv'].extend(['--eval','process.exit(0)']);reseal(f,plan=True)

def polluted_environment_root(f):
    (Path(f.lock['environments']['A01'])/'unexpected.py').write_text('# unrelated existing script\n')

def root_host_namespace(f):
    remap={}
    for old,b in f.lock['inputs'].items():
        if b['root']=='host':
            b['path']=str(f.host/b['path']).lstrip('/')
            remap[old]='host:'+b['path']
        else:remap[old]=old
    f.lock['inputs']={remap[k]:v for k,v in f.lock['inputs'].items()}
    f.lock['dependencies']={remap[k]:[remap[v] for v in values] for k,values in f.lock['dependencies'].items()}
    f.lock['roles']={k:[remap[v] for v in values] for k,values in f.lock['roles'].items()}
    for b in f.lock['gate_receipts'].values():
        if b['root']=='host':b['path']=str(f.host/b['path']).lstrip('/')
    f.context=replace(f.context,host_root='/')
    reseal(f,closure=True)

def host_file_inside_repository(f):
    root_host_namespace(f)
    old='host:'+str(f.host/'transitive-library').lstrip('/')
    path=f.repo/'overlapping-host-library';path.write_bytes((f.host/'transitive-library').read_bytes())
    binding=f.lock['inputs'].pop(old);binding['path']=str(path).lstrip('/')
    new='host:'+binding['path'];f.lock['inputs'][new]=binding
    f.lock['dependencies']={new if k==old else k:[new if v==old else v for v in values] for k,values in f.lock['dependencies'].items()}
    reseal(f,closure=True)

def duplicate_node_loader_member(f):
    f.lock['roles']['node_loader'].append(f.lock['roles']['node_packages'][0]);reseal(f,closure=True)

CASES=[
 ('baseline-fixture-no-authorization',None,False),
 ('nested-double-slash-output',nested_slash,True),
 ('dependency-reachable-only-via-frozen-constructor',frozen_dependency,False),
 ('omitted-transitive-input-independent-anchor',missing_transitive,True),
 ('missing-fixed-role-even-with-resealed-fixture-anchor',fixed_role_missing,True),
 ('same-size-altered-dependency-bytes',changed_bytes,True),
 ('fifo-lock-nonblocking',fifo_lock,True),
 ('symlink-dependency',symlink_ancestor,True),
 ('replaced-authority-same-path',replaced_authority,True),
 ('stopped-authority-with-new-output',replay_new_output,True),
 ('missing-independent-host-gate',missing_gate,True),
 ('reviewer-equals-producer',self_review,True),
 ('approval-wrong-commit',wrong_approval_commit,True),
 ('receipt-boolean-integer-confusion',nonboolean_receipt,True),
 ('schedule-boolean-integer-confusion',malformed_type,True),
 ('duplicate-json-fields',duplicate_keys,True),
 ('native-safe-flag-omitted-even-after-plan-reseal',missing_safe_native_flag,True),
 ('blender-user-script-environment-changed-after-plan-reseal',unsafe_blender_environment,True),
 ('node-evaluation-extra-after-plan-reseal',node_evaluation_extra,True),
 ('preexisting-environment-root-file',polluted_environment_root,True),
 ('root-host-namespace-with-actual-bound-input-paths',root_host_namespace,False),
 ('host-namespace-cannot-hide-input-inside-repository',host_file_inside_repository,True),
 ('multiple-node-loader-inputs-even-after-closure-reseal',duplicate_node_loader_member,True),
]

def alarm(signum,frame):raise TimeoutError('CPU validation exceeded five-second guard')

def run():
    source_before=Path(mod.__file__).read_bytes();test_before=(REPO/'tests/test_static_tray_admission_c201_input_lock.py').read_bytes()
    rows=[]
    with ExitStack() as stack:
        for target in ('subprocess.Popen','os.fork','os.system'):
            stack.enter_context(mock.patch(target,side_effect=AssertionError('No child start permitted')))
        prior=signal.signal(signal.SIGALRM,alarm)
        try:
            for name,setup,rejection in CASES:
                start=time.monotonic();row={'name':name,'expected':'reject' if rejection else 'accept-fixture-only'}
                try:
                    with tempfile.TemporaryDirectory(prefix='c205-independent-') as d:
                        f=fixtures.Fixture(d)
                        if setup:setup(f)
                        signal.alarm(5)
                        try:
                            good(f);row['observed']='accept-fixture-only';row['passed']=not rejection
                        except mod.InputLockError as e:
                            row.update(observed='reject',code=e.code,message=str(e),passed=rejection)
                        finally:signal.alarm(0)
                except BaseException as exc:row.update(observed='unexpected-exception',error=repr(exc),passed=False)
                row['elapsedSeconds']=round(time.monotonic()-start,6);rows.append(row)
        finally:signal.signal(signal.SIGALRM,prior)
    value={'schema':'ontokin.c205.independent-lock-controls/0.1','observedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'validatorSha256':hashlib.sha256(source_before).hexdigest(),'fixtureTestSha256':hashlib.sha256(test_before).hexdigest(),
        'inputsUnchangedDuringRun':source_before==Path(mod.__file__).read_bytes() and test_before==(REPO/'tests/test_static_tray_admission_c201_input_lock.py').read_bytes(),
        'passed':sum(r['passed'] for r in rows),'failed':sum(not r['passed'] for r in rows),'nativeStarts':0,'receiverStarts':0,'nodeStarts':0,'lifecycleStarts':0,'authorStarts':0,
        'context':'All inputs are explicitly synthetic fixtures; no native readiness evidence is created.','controls':rows}
    target=OUT/(sys.argv[1] if len(sys.argv)>1 else 'draft-independent-controls.json');target.write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps({k:v for k,v in value.items() if k!='controls'}));print(json.dumps([r for r in rows if not r['passed']]))
    return 0 if value['failed']==0 and value['inputsUnchangedDuringRun'] else 1
if __name__=='__main__':sys.exit(run())
