import sys,json,traceback,copy,subprocess,hashlib
from pathlib import Path
from fractions import Fraction as F
repo=Path(sys.argv[1]);sys.path.insert(0,str(repo))
from ontokin.texture_bundle import load_texture_file_manifest
from ontokin.execution_budget import SharedExecutionBudget,admit_entry_budget
from ontokin.construction import compile_construction
from ontokin.evaluator import _simulator
from ontokin.diagnostics import OntoKinError
from ontokin.agent import _Cancelled
freeze=repo/'docs/language-design/torque-v0.1/freeze';out=Path(sys.argv[2]);out.mkdir(exist_ok=False)
cases=[c for c in json.loads((freeze/'agent/resource-cases.json').read_text())['cases'] if 2<=int(c['id'][1:])<=14]
class Sentinel(Exception):pass
def run(case,mode,cap=None):
 h={'clock':0.0,'seen':[],'mode':mode,'captured':None};sentinel=_Cancelled() if mode=='cancel' else Sentinel(case['id'])
 def check():
  l=h['ledger']
  if l.stage==case['stage']:
   h['seen'].append(l.operations)
   if h['captured'] is None:
    s=h.get('sim');h['captured']=(s.state,copy.deepcopy(s.state),s.event_index,s.last_boundary,tuple(s.boundaries)) if s else None
    if mode in ['cancel','callback']:raise sentinel
    if mode=='deadline':h['clock']=31.0
 ledger=SharedExecutionBudget(caller_caps=None if cap is None else {'max_operations':cap},check=check,clock=lambda:h['clock']);h['ledger']=ledger
 row={'case':case['id'],'stage':case['stage'],'fixture':case['fixture'],'mode':mode,'cap':cap,'failures':[]}
 try:
  b=load_texture_file_manifest(freeze/(case['fixture']+'.files.json'));admit_entry_budget(b.entry,ledger,profile='torque-0.1')
  c=compile_construction(b,execution_budget=ledger);s=_simulator(c.model,work=c.reach_work);h['sim']=s
  time=F(case['task_request'].get('until_seconds',case['task_request'].get('time',{}).get('seconds',str(c.model.duration))))
  result=s.advance(time,'after');row['success_state']=result;row['numeric_counts']=dict(s.work.counts)
  if mode!='control':row['failures'].append('fault did not stop request')
 except BaseException as e:
  row['exception_type']=type(e).__name__;row['exception']=str(e);row['same_exception_object']=e is sentinel
  if mode=='control':row['failures'].append({'control_exception':repr(e),'traceback':traceback.format_exc()})
  elif mode in ['cancel','callback']:
   if e is not sentinel:row['failures'].append('callback exception identity changed')
  elif not isinstance(e,OntoKinError) or e.diagnostic.code!='OKL-E-RESOURCE':row['failures'].append({'wrong_resource_error':repr(e),'traceback':traceback.format_exc()})
  elif e.diagnostic.details.get('stage')!=case['stage']:row['failures'].append({'wrong_stage':e.diagnostic.details})
  if isinstance(e,OntoKinError):row['diagnostic']={'code':e.diagnostic.code,'details':e.diagnostic.details}
  captured=h['captured'];s=h.get('sim')
  if captured and s:
   owner,saved,index,last,boundaries=captured
   atomic=s.state is owner and s.state==saved and s.event_index==index and s.last_boundary==last and tuple(s.boundaries)==boundaries
   row['accepted_state_unchanged']=atomic
   if not atomic:row['failures'].append('accepted boundary state changed after failure')
 row['stage_visit_operations_before_tick']=h['seen'];row['ledger']=ledger.report()
 row['original_clock_and_callback_retained']=ledger.started==0 and ledger.check is check
 if mode!='control' and ledger.stage!=('execution'):
  # Stages present before a torque helper can be evaluator-specific. These
  # direct calls keep the original post-compile execution stage.
  row['failures'].append({'unrestored_stage':ledger.stage})
 if not h['seen']:row['failures'].append('requested real stage not reached')
 return row
results=[]
for case in cases:
 control=run(case,'control');rows=[control]
 if not control['failures']:
  cap=control['stage_visit_operations_before_tick'][0]
  rows += [run(case,mode,cap if mode=='cap' else None) for mode in ['cancel','cap','deadline','callback']]
 for row in rows:
  name=case['id']+'-'+row['mode']+'.json';(out/name).write_text(json.dumps(row,indent=2)+'\n')
  results.append({'case':case['id'],'mode':row['mode'],'status':'failed' if row['failures'] else 'passed','failures':row['failures'],'file':name})
 print(case['id'],[(r['mode'],r['failures']) for r in rows],flush=True)
summary={'status':'failed' if any(r['failures'] for r in results) else 'passed','checks':len(results),'results':results,'scope':'Actual runtime original-ledger callbacks and atomic boundary state; Agent queued/status/store obligations are separately tested.','head':subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()}
(out/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');sys.exit(summary['status']!='passed')
