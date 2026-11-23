"""Execute only the independently approved P22 two-command preparation plan."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
from datetime import datetime, timezone

def now():
    return datetime.now(timezone.utc).isoformat()

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode('ascii')

def describe(path):
    p=Path(path)
    st=p.lstat()
    assert stat.S_ISREG(st.st_mode) and st.st_nlink==1 and not p.is_symlink(), str(p)
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):
            h.update(block)
    end=p.lstat()
    assert (st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns)==(end.st_ino,end.st_size,end.st_mtime_ns,end.st_ctime_ns)
    return {'path':str(p),'sha256':h.hexdigest(),'size_bytes':st.st_size,'mode':oct(stat.S_IMODE(st.st_mode))}

def bound(d):
    assert describe(d['path'])==d, 'Input changed: '+d['path']

def document(d):
    bound(d)
    raw=Path(d['path']).read_bytes()
    value=json.loads(raw)
    assert canonical(value)==raw, 'Noncanonical input: '+d['path']
    return value

def write_new(path,value):
    p=Path(path)
    fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o644)
    with os.fdopen(fd,'wb') as f:
        f.write(canonical(value));f.flush();os.fsync(f.fileno())
    return describe(p)

parser=argparse.ArgumentParser()
parser.add_argument('--launch-plan',required=True)
parser.add_argument('--launch-sha256',required=True)
args=parser.parse_args()
plan_path=Path(args.launch_plan)
raw=plan_path.read_bytes()
assert hashlib.sha256(raw).hexdigest()==args.launch_sha256
launch=json.loads(raw)
assert canonical(launch)==raw
assert launch['schema']=='ontokin.c271.p22-preparation-launch/1'
assert describe(Path(sys.executable).resolve())==launch['python']
bound(launch['git']);bound(launch['preparer'])
inventory=document(launch['source']['inventory'])
source_root=Path(launch['source']['root'])
assert source_root==Path(launch['cwd'])
for name,binding in inventory['files'].items():
    bound({'path':str(source_root/name),**binding})
for path,identity in launch['destination_and_evidence_ancestors'].items():
    p=Path(path);s=p.lstat()
    assert not p.is_symlink() and stat.S_ISDIR(s.st_mode)
    assert {'device':s.st_dev,'inode':s.st_ino,'mode':oct(stat.S_IMODE(s.st_mode))}==identity
assert [c['name'] for c in launch['commands']]==['NODE','DEPENDENCIES']
for command in launch['commands']:
    selected=document(command['plan']);bound(selected['archive'])
    assert selected['source']==launch['source']
    assert not Path(command['destination']).exists()
    assert all(not Path(p).exists() for p in command['fresh_outputs'])
for p in [launch['outer_outputs']['intent'],launch['outer_outputs']['result']]:
    assert not Path(p).exists()
write_new(launch['outer_outputs']['intent'],{'schema':'ontokin.c271.p22-preparation-intent/1',
    'at_utc':now(),'launch_plan':describe(plan_path),'launcher':describe(Path(__file__).resolve()),
    'source':launch['source'],'commands':launch['commands'],'status':'prepared_to_start_once'})
result={'schema':'ontokin.c271.p22-preparation-result/1','started_at_utc':now(),
    'launch_plan':describe(plan_path),'launcher':describe(Path(__file__).resolve()),
    'source':launch['source'],'commands':[],'passed':False,'status':'in_progress',
    'explicit_scope':'Input staging only; no Node, ldd, checker, H0/H1, product tests or full routine',
    'unknown_operations':[]}
try:
    for command in launch['commands']:
        selected=document(command['plan'])
        bound(selected['archive']);bound(launch['preparer']);bound(launch['python']);bound(launch['git'])
        entry={'name':command['name'],'argv':command['argv'],'cwd':launch['cwd'],
               'environment':launch['environment'],'started_at_utc':now()}
        result['commands'].append(entry)
        stdout=Path(selected['report']).parent/(command['name']+'.stdout.log')
        stderr=Path(selected['report']).parent/(command['name']+'.stderr.log')
        with stdout.open('xb') as out,stderr.open('xb') as err:
            proc=subprocess.Popen(command['argv'],cwd=launch['cwd'],env=launch['environment'],
                                  stdin=subprocess.DEVNULL,stdout=out,stderr=err,start_new_session=True)
            entry['pid']=proc.pid
            try:
                entry['exit_code']=proc.wait(timeout=launch['per_command_timeout_seconds'])
            except subprocess.TimeoutExpired:
                entry['timeout']=True
                result['unknown_operations'].append({'command':command['name'],'reason':'Timed out; reconcile publication destinations/reports before any retry'})
                os.killpg(proc.pid,signal.SIGTERM)
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid,signal.SIGKILL);proc.wait(timeout=3)
                entry['exit_code']=proc.returncode
                raise RuntimeError('Preparation timeout; stopped without retry')
        entry['finished_at_utc']=now();entry['stdout']=describe(stdout);entry['stderr']=describe(stderr)
        assert entry['exit_code']==0, 'Preparer refused; stop without retry'
        report_descriptor=describe(selected['report'])
        report=document(report_descriptor)
        assert report['passed'] is True and report['state']=='INSTALLED_EXACT'
        assert report['execution_counts']=={'node':0,'ldd':0,'checkers':0}
        assert report['apply_requested'] is True and report['after']['state']=='complete_exact'
        entry['report']=report_descriptor
        entry['installation_index']=write_new(Path(selected['report']).parent/(command['name']+'-INSTALLATION-INDEX.json'),
            {'schema':'ontokin.current-host-readback-inspection-installation/0.1.0',
             'plan':command['plan'],'report':report_descriptor})
        bound(command['plan']);bound(selected['archive'])
    for name,binding in inventory['files'].items():
        bound({'path':str(source_root/name),**binding})
    bound(launch['source']['inventory']);bound(launch['python']);bound(launch['preparer']);bound(launch['git'])
    result.update(passed=True,status='preparation_complete_pending_independent_outcome_review',
                  source_files_unchanged=len(inventory['files']))
except BaseException as exc:
    result.update(passed=False,status='stopped_at_first_failure_or_unknown',
                  error={'type':type(exc).__name__,'message':str(exc)})
finally:
    result['finished_at_utc']=now()
    result_descriptor=write_new(launch['outer_outputs']['result'],result)
print(json.dumps({'passed':result['passed'],'status':result['status'],'commands':len(result['commands']),
                  'result':result_descriptor,'unknown_operations':result['unknown_operations']}))
sys.exit(0 if result['passed'] else 1)
