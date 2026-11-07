import sys,json,traceback,hashlib,platform,time,subprocess
from pathlib import Path
from fractions import Fraction as F
repo=Path(sys.argv[1]);sys.path.insert(0,str(repo))
from ontokin.texture_bundle import load_texture_file_manifest
from ontokin.execution_budget import SharedExecutionBudget,admit_entry_budget
from ontokin.construction import compile_construction
from ontokin.evaluator import evaluate_prefix
from ontokin.program_diagnostics import diagnostic_dict
freeze=repo/'docs/language-design/torque-v0.1/freeze'
out=Path(sys.argv[2]);out.mkdir(exist_ok=False)
expectations=json.loads((freeze/'state-expectations.json').read_text())
def ratio(v): return F(int(v['numerator']),int(v['denominator']))
results=[];failed=[]
for case in expectations['cases']:
 for i,obs in enumerate(case['observations']):
  row={'case':case['case'],'observation':i,'time':obs['time_seconds'],'side':obs['side'],'failures':[]}
  b=load_texture_file_manifest(freeze/(case['case']+'.files.json'))
  ledger=SharedExecutionBudget();admit_entry_budget(b.entry,ledger,profile='torque-0.1')
  try:
   c=compile_construction(b,execution_budget=ledger)
   r=evaluate_prefix(c.model,obs['time_seconds'],side=obs['side'],work=c.reach_work)
   row['failure']=None if r['failure'] is None else diagnostic_dict(r['failure'].diagnostic,b)
   row['valid_until_seconds']=r['valid_until_seconds'];row['valid_until_side']=r['valid_until_side']
   if r['failure']: row['failures'].append('evaluation_failed')
   if r['last_valid_state']:
    row['state']=r['last_valid_state']
    value=r['last_valid_state']['objects'][case['target_path']]['torques']
    for key,expected in obs['exact_fields'].items():
     if value[key]!=expected:row['failures'].append({'field':key,'actual':value[key],'expected':expected})
    for key,expected in obs['canonical_hex'].items():
     if type(value[key]) is not float or value[key].hex()!=expected:row['failures'].append({'hex':key,'actual':value[key],'expected':expected})
    for key,bounds in obs['error_constraints'].items():
     if bounds is None:
      if value[key] is not None:row['failures'].append({'null':key})
     elif not ratio(bounds['minimum'])<=ratio(value[key])<=ratio(bounds['maximum']):row['failures'].append({'error':key,'actual':value[key],'expected':bounds})
  except BaseException as e:
   row['failures'].append({'exception':repr(e),'traceback':traceback.format_exc()})
  row['work']=ledger.report(status='failed' if row['failures'] else 'valid')
  path=out/(case['case']+'-'+str(i)+'.json');path.write_text(json.dumps(row,indent=2)+'\n')
  results.append({'case':case['case'],'index':i,'status':'failed' if row['failures'] else 'passed','path':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
  if row['failures']:
   failed.append(results[-1]);print('FAIL',case['case'],i,str(row['failures'])[:500],flush=True)
 print('CASE',case['case'],'completed',flush=True)
summary={'status':'passed' if not failed else 'failed','checks':len(results),'failed':failed,'results':results,'python':platform.python_version(),'head':subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip(),'uncommitted_source':subprocess.check_output(['git','-C',str(repo),'status','--short'],text=True)}
(out/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:summary[k] for k in ['status','checks','failed']}));sys.exit(bool(failed))
