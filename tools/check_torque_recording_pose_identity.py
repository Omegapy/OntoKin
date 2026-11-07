import sys,json,traceback,hashlib,subprocess
from fractions import Fraction as F
from pathlib import Path
repo=Path(sys.argv[1]);sys.path.insert(0,str(repo))
from ontokin.texture_bundle import load_texture_file_manifest
from ontokin.execution_budget import SharedExecutionBudget,admit_entry_budget
from ontokin.construction import compile_construction
from ontokin.evaluator import _simulator
freeze=repo/'docs/language-design/torque-v0.1/freeze';out=Path(sys.argv[2]);out.mkdir(exist_ok=False)
cases=json.loads((freeze/'state-expectations.json').read_text())['cases'];rows=[];failures=[]
for case in cases:
 for i,obs in enumerate(case['observations']):
  row={'case':case['case'],'index':i,'time':obs['time_seconds'],'side':obs['side'],'failures':[]}
  try:
   b=load_texture_file_manifest(freeze/(case['case']+'.files.json'));ledger=SharedExecutionBudget();admit_entry_budget(b.entry,ledger,profile='torque-0.1')
   c=compile_construction(b,execution_budget=ledger);s=_simulator(c.model,work=c.reach_work);time=F(obs['time_seconds']);full=s.advance(time,obs['side'])
   selected=sorted(full['frames']);before=ledger.operations
   moving=s.recording_moving_frames(s.state,selected)
   actual=s.recording_frames(time,s.state,selected,moving_frames=moving)
   row['recording_operations']=ledger.operations-before;row['frames']=len(selected);row['comparisons']=[]
   for path in selected:
    expected=full['frames'][path];point=actual[path]
    cq=tuple(x.hex() for x in point.orientation);cp=tuple(x.hex() for x in point.position)
    eq=tuple(x.hex() for x in expected['orientation_wxyz']);ep=tuple(x.hex() for x in expected['position_m'])
    same=cq==eq and cp==ep
    row['comparisons'].append({'frame':path,'exact_same_pq':same,'position_hex':cp,'quaternion_hex':cq})
    if not same:row['failures'].append({'frame':path,'candidate':[cp,cq],'full_source':[ep,eq]})
   row['ledger']=ledger.report()
  except BaseException as e:row['failures'].append({'exception':repr(e),'traceback':traceback.format_exc()})
  name=case['case']+'-'+str(i)+'.json';(out/name).write_text(json.dumps(row,indent=2)+'\n')
  result={'case':case['case'],'index':i,'status':'failed' if row['failures'] else 'passed','file':name};rows.append(result)
  if row['failures']:failures.append({'row':result,'failures':row['failures']});print('FAIL',str(row['failures'])[:500],flush=True)
 print(case['case'],'done',flush=True)
summary={'status':'failed' if failures else 'passed','checks':len(rows),'results':rows,'failures':failures,'head':subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()}
(out/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');sys.exit(bool(failures))
