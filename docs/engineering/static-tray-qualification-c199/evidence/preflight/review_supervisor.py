"""Independent no-child fault probes against a captured supervisor/store snapshot."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import shutil
import stat
import sys
import types
from unittest.mock import patch

SOURCE = Path('/workspace/scratch/801d9d641f68/ontokin/prototypes/static_tray_v01')
OUT = Path('/workspace/scratch/801d9d641f68/c199-independent-preflight/supervisor-review-v3')
SNAPSHOT = OUT / 'snapshot'
SNAPSHOT.mkdir(parents=True, exist_ok=True)
identities = {}
for name in ['supervisor.py','store.py','lifecycle.py','lifecycle_stub.py']:
    raw=(SOURCE/name).read_bytes()
    (SNAPSHOT/name).write_bytes(raw)
    identities[name]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

package=types.ModuleType('review_tray')
package.__path__=[str(SNAPSHOT)]
sys.modules['review_tray']=package
def module(name):
    spec=importlib.util.spec_from_file_location('review_tray.'+name,SNAPSHOT/(name+'.py'))
    mod=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=mod
    spec.loader.exec_module(mod)
    return mod
supervisor=module('supervisor')
store=module('store')
cleanup=[{'handles_closed':True,'cleanup':{'passed':True}}]
probes=[]

def fixture(name):
    p=OUT/name
    p.mkdir(exist_ok=False)
    (p/'state.json').write_bytes(store.json_bytes({'revision':'old'}))
    return p

# No child is launched: promotion is a file transaction using a current clock.
p=fixture('short-clock-store')
clock=supervisor.Clock(total_ms=500)
try:
    result=store.promote(p,expected='old',state={'revision':'new'},clock=clock,cleanup_records=cleanup)
    probes.append({'id':'P01','finding':'Promotion starts with only 500 ms remaining despite a declared 3000 ms stage allowance','returned':result,'actual_state':store.read_state(p),'observed':True})
except supervisor.Stop as exc:
    probes.append({'id':'P01','observed':False,'rejected':exc.as_dict()})

# Inject a real post-rename durability error, using no subprocess or sleeping.
p=fixture('postcommit-fsync-store')
original_fsync=os.fsync
def fail_directory_fsync(fd):
    if stat.S_ISDIR(os.fstat(fd).st_mode):
        raise OSError('controlled directory fsync failure after pointer replace')
    return original_fsync(fd)
try:
    with patch.object(store.os,'fsync',fail_directory_fsync):
        store.promote(p,expected='old',state={'revision':'new'},clock=supervisor.Clock(),cleanup_records=cleanup)
except BaseException as exc:
    probes.append({'id':'P02','finding':'Postcommit durability error is not classified UNKNOWN although the accepted pointer changed','exception_type':type(exc).__name__,'exception_state':getattr(exc,'state',None),'actual_state':store.read_state(p),'observed':store.read_state(p)=={'revision':'new'} and getattr(exc,'state',None)!='UNKNOWN'})

# Simulate elapsed time only after the commit point; no wall-clock wait occurs.
p=fixture('postcommit-deadline-store')
now=[0.0]
class SimulatedClock:
    end=5.0
    def stage(self,milliseconds):
        self.check()
        if self.end-now[0]<milliseconds/1000:
            raise supervisor.Stop('OTRAY-E-RESOURCE','Controlled short allowance','TIMEOUT')
        return now[0]+milliseconds/1000
    def check(self,stage_end=None):
        if now[0]>=min(self.end,stage_end if stage_end is not None else self.end):
            raise supervisor.Stop('OTRAY-E-RESOURCE','Controlled elapsed clock','TIMEOUT')
original_replace=os.replace
def replace_then_expire(a,b):
    original_replace(a,b)
    now[0]=10.0
try:
    with patch.object(store.time,'monotonic',lambda:now[0]),patch.object(store.os,'replace',replace_then_expire):
        result=store.promote(p,expected='old',state={'revision':'new'},clock=SimulatedClock(),cleanup_records=cleanup)
    probes.append({'id':'P03','finding':'Promotion returns success after its stage and transaction deadlines expire following replace','returned':result,'simulated_elapsed_seconds':now[0],'observed':result.get('promoted') is True and now[0]>5.0})
except supervisor.Stop as exc:
    probes.append({'id':'P03','finding':'Postcommit deadline expiry must conservatively report UNKNOWN and preserve readback','exception_state':exc.state,'actual_state':store.read_state(p),'observed':exc.state!='UNKNOWN','simulated_elapsed_seconds':now[0]})

# Model a child start followed by log-file setup failure, without starting a child.
stage=OUT/'fake-child-log-open-failure'
stage.mkdir(exist_ok=False)
(stage/'construction.stdout.log').write_bytes(b'existing diagnostic')
rd1,wr1=os.pipe()
rd2,wr2=os.pipe()
class FakeProcess:
    pid=2147483646
    returncode=0
    stdout=os.fdopen(rd1,'rb')
    stderr=os.fdopen(rd2,'rb')
    def poll(self): return self.returncode
    def wait(self,timeout=None): return self.returncode
fake=FakeProcess()
class FakeLibC:
    def prctl(self,*args): return 0
starts=[]
try:
    with patch.object(supervisor.ctypes,'CDLL',lambda *a,**k:FakeLibC()),patch.object(supervisor.subprocess,'Popen',lambda *a,**k:fake),patch.object(supervisor,'terminate_group',lambda process,*args:{'passed':True,'reaped':True,'process_group_absent':True,'elapsed_ms':0}):
        supervisor.run_process(['FAKE-NOT-EXECUTED'],stage=stage,label='construction',clock=supervisor.Clock(),stage_end=supervisor.time.monotonic()+10,on_started=lambda r:starts.append(r))
except supervisor.Stop as exc:
    r=exc.process_record
    probes.append({'id':'P04','finding':'Failure opening the first log occurs after Popen but before start notification; both pipe handles remain open while receipt says handles_closed','simulated_start_notifications':len(starts),'receipt_handles_closed':r['handles_closed'],'actual_stdout_closed':fake.stdout.closed,'actual_stderr_closed':fake.stderr.closed,'observed':len(starts)==0 and r['handles_closed'] and not fake.stdout.closed and not fake.stderr.closed,'scope':'Mocked Popen and cleanup only; zero process or native launches'})
finally:
    fake.stdout.close();fake.stderr.close();os.close(wr1);os.close(wr2)

summary={'schema':'ontokin.c199.independent-supervisor-prelock-review/0.1','status':'PASS_TARGETED_NO_CHILD_REPAIR_REVIEW' if all(not p['observed'] for p in probes) else 'CHANGES_REQUIRED','source_snapshot':identities,'reviewer_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'actual_child_starts':0,'native_starts':0,'official_controls_rerun':False,'probes':probes,'statically_reviewed_corrections':['Full 3000 ms promotion allowance','Post-replace error and postcommit deadline UNKNOWN classification','Nonblocking clock-aware ledger lock and bounded valid transitions','Cleanup clock bound and reserved outer time','Immediate start accounting and unconditional process-pipe closure','2048-entry inventory bound with per-entry clock checks; selector wait subtracts elapsed inventory work'],'remaining_obligations':['Explicit reviewed validation amendment before any replacement lifecycle cohort','Exact-byte real-subprocess lifecycle requalification if the amendment is adopted','Complete implementation and executable-input-lock review before native slots'],'scope':'Targeted review of captured implementation bytes and repaired fault paths. This does not establish real-child lifecycle requalification or native cancellation. Original L01-L08 receipts remain preserved; no native or subprocess rerun was requested or performed.'}
(OUT/'REVIEW.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
print(json.dumps(summary,indent=2))
