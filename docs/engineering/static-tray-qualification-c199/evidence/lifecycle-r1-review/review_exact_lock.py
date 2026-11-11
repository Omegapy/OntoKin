"""Independent exact-byte L-R1 approval review. Does not run any control."""
from pathlib import Path
from datetime import datetime, timezone
import ast
import hashlib
import importlib.util
import json
import subprocess
import sys
import time

ROOT=Path('/workspace/scratch/801d9d641f68/ontokin')
DOC=ROOT/'docs/engineering/static-tray-qualification-c199'
OUT=Path('/workspace/scratch/801d9d641f68/c199-lifecycle-r1-review')
LOCK_PATH=DOC/'LIFECYCLE-INPUTS.json'
EXPECTED='c5d0817a3dfb88741963affce1fca66d144c5f56301b64d7608c404d6b343416'
checks=[]

def check(name,value,detail=None):
    checks.append({'name':name,'pass':bool(value),'detail':detail})
    if not value:
        raise AssertionError(name)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def git(*args):
    return subprocess.check_output(['git','-C',str(ROOT),*args])

raw=LOCK_PATH.read_bytes()
lock=json.loads(raw)
check('exact requested lock',hashlib.sha256(raw).hexdigest()==EXPECTED)
check('review interpreter isolation',sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode)
check('no site startup modules',not any('site-packages' in str(getattr(m,'__file__','')) for m in sys.modules.values()))
amendment=ROOT/lock['amendment_path']
check('amendment digest',sha(amendment)==lock['amendment_sha256'])
check('versioned narrow amendment',lock['decision']=='OK-VAL-STATIC-TRAY-001/0.1.1-L-R1')
implementation=lock['implementation']
check('implementation tree',git('rev-parse',implementation['commit']+'^{tree}').decode().strip()==implementation['tree'])
observed_head=git('rev-parse','HEAD').decode().strip()
check('implementation retained in current history',subprocess.run(['git','-C',str(ROOT),'merge-base','--is-ancestor',implementation['commit'],observed_head],capture_output=True).returncode==0)
for relative,row in lock['repository_files'].items():
    path=ROOT/relative
    b=path.read_bytes()
    check('repository bytes:'+relative,len(b)==row['size_bytes'] and hashlib.sha256(b).hexdigest()==row['sha256'])
    check('committed implementation bytes:'+relative,b==git('show',implementation['commit']+':'+relative))

runner_path=DOC/'run_lifecycle.py'
runner_text=runner_path.read_text()
runner_ast=ast.parse(runner_text)
check('coordinator exact flags','sys.flags.no_site' in runner_text and lock['argv'][1]=='-IBS')
check('coordinator exact environment','dict(os.environ) != lock["environment"]' in runner_text)
check('exact command identity','actual_argv != lock["argv"]' in runner_text)
check('stop first unexpected result','if not passed:\n            break' in runner_text)
check('fresh output destination','exist_ok=False' in runner_text and not Path(lock['output_directory']).exists())
check('one replacement slot each',[x['slot'] for x in lock['slots']]==['L-R1-%02d'%i for i in range(1,9)])
check('unchanged ordered controls',[x['case'] for x in lock['slots']]==['L%02d'%i for i in range(1,9)])
check('direct and grandchild limits',all(x['maximum_direct_starts']==1 for x in lock['slots']) and [x['maximum_grandchild_starts'] for x in lock['slots']]==[0,0,0,0,1,0,0,0])
check('additional cumulative disclosed limits',(lock['additional_direct_limit'],lock['additional_grandchild_limit'],lock['cumulative_direct_limit'],lock['cumulative_grandchild_limit'])==(8,1,16,2))
check('native schedule untouched',lock['native_starts_before_cohort']==0 and lock['native_slots_unchanged']==['N%02d'%i for i in range(1,13)])
life=(ROOT/'prototypes/static_tray_v01/lifecycle.py').read_text()
stub=(ROOT/'prototypes/static_tray_v01/lifecycle_stub.py').read_text()
check('controlled and grandchild no-site flags','"-IBS"' in life and '"-IBS"' in stub and '"-IB"' not in life and '"-IB"' not in stub)
check('callback propagation','if on_started:\n            on_started(record)' in life and 'on_started=child_started' in runner_text)
check('preflight charged to per-case allowance','remaining_ms=30000-(time.monotonic()-started)*1000' in runner_text and 'total_ms=remaining_ms' in runner_text and 'total<=30000' in runner_text)
check('reviewed supervisor repair unchanged',sha(ROOT/'prototypes/static_tray_v01/supervisor.py')=='c47b84ab464e89d4c8673d7541679a45ddf3fc4816a906aff4546e074b4c5a10')
check('reviewed store repair unchanged',sha(ROOT/'prototypes/static_tray_v01/store.py')=='d0006497ff6fc13ff0b563cdb58445789cd1a26c489ac4ce2a84e77a03607bd0')

# Import only the standalone reviewed verifier. Its main guard is not entered.
spec=importlib.util.spec_from_file_location('c199_independent_lifecycle_verifier',runner_path)
runner=importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
started=time.monotonic()
runner.verify(lock,ROOT,started+30)
elapsed=(time.monotonic()-started)*1000
host=json.loads(Path(lock['host_inventory']).read_bytes())
check('fresh complete host byte verification',elapsed<=30000,{'elapsed_ms':elapsed,'paths':len(host['files']),'unique_targets':host['unique_regular_targets'],'unique_bytes':host['unique_regular_bytes']})
check('host inventory exact',sha(lock['host_inventory'])==lock['host_inventory_sha256']=='2ed86412f09c74f5d3fb038f50e6417872b8eace0f89d7f168c79923efb14994')
check('still no site startup after imports',not any('site-packages' in str(getattr(m,'__file__','')) for m in sys.modules.values()))
check('original evidence present',(DOC/'evidence/lifecycle-original').is_dir())
check('prior blocked review retained',any('8922' in p.name for p in (DOC/'evidence').rglob('*.json')))
check('lock unchanged at end',sha(LOCK_PATH)==EXPECTED)
for relative,row in lock['repository_files'].items():
    check('final unchanged:'+relative,sha(ROOT/relative)==row['sha256'])

approval={'schema':'ontokin.c199.independent-lifecycle-r1-approval/0.1','decision':'APPROVED_FOR_L_R1',
          'reviewed_at_utc':datetime.now(timezone.utc).isoformat(),
          'reviewer':{'agent':'/root/repo_status','role':'Independent preflight and lifecycle-repair reviewer','runtime_authorship':'No supervisor, store, lifecycle, stub or runner implementation authored by this reviewer'},
          'input_lock_sha256':EXPECTED,'amendment_sha256':lock['amendment_sha256'],
          'source':implementation,'tree':implementation['tree'],'observed_repository_head':observed_head,
          'reviewer_script_sha256':sha(__file__),'checks':checks,'passed_checks':len(checks),
          'host_verification':{'paths':len(host['files']),'unique_targets':host['unique_regular_targets'],'unique_bytes':host['unique_regular_bytes'],'elapsed_ms':elapsed},
          'approved_scope':{'cohort':'L-R1 only','slots':[x['slot'] for x in lock['slots']],
                            'additional_direct_child_limit':8,'additional_grandchild_limit':1,
                            'cumulative_direct_child_limit':16,'cumulative_grandchild_limit':2,
                            'native_starts_authorized':0,'native_slots_consumed_by_review':0,
                            'command':lock['argv'],'environment':lock['environment'],
                            'output_directory':lock['output_directory'],'automatic_retries':0},
          'execution_conditions':['Copy this approval unchanged to the exact locked approval path.',
                                  'Launch exactly the locked argv with env equal to the locked environment.',
                                  'Run once in the locked new output directory; any changed locked byte invalidates this approval.',
                                  'Stop on first unexpected result or binding/cleanup failure; preserve consumed/unknown slots and all evidence.',
                                  'The prior cohort and earlier blocked lock remain historical and cannot be relabeled as this execution.'],
          'review_summary':['The corrected -IBS command removes the actually observed unbound site-packages startup dependency.',
                            'The coordinator checks isolation, environment, exact argv, amendment and approval before reserving a case.',
                            'Each case rechecks all bound source and host bytes under its 30000 ms allowance, records the actual start callback, and stops the cohort at first unexpected result.',
                            'The original adopted outcome expectations and process/time/output ceilings remain fixed except for the explicitly disclosed one-cohort process allowance.',
                            'The preserved no-child repair review covers short promotion allowance, postcommit uncertainty and setup-failure start/pipe accounting.'],
          'limits':['This approval permits only the replacement controlled lifecycle cohort. It is not a passing result.',
                    'No controlled case, native build, renderer, import or Blender main was run during this review.',
                    'It does not approve the full producer/reader/native executable closure, consume or reset a native slot, or establish Blender cancellation behavior.']}
OUT.mkdir(exist_ok=True)
(OUT/'INPUTS-c5d0817a.json').write_bytes(raw)
(OUT/'AMENDMENT-57611785.md').write_bytes(amendment.read_bytes())
target=OUT/'APPROVAL.json'
with target.open('x') as f:
    json.dump(approval,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'decision':approval['decision'],'approval':str(target),'sha256':sha(target),'checks':len(checks),'input_lock_sha256':EXPECTED,'amendment_sha256':lock['amendment_sha256'],'host_verification':approval['host_verification']},indent=2))
