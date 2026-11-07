import sys,json,traceback,hashlib,subprocess,copy
from pathlib import Path
from fractions import Fraction as F
from dataclasses import asdict
repo=Path(sys.argv[1]);sys.path.insert(0,str(repo))
from ontokin.texture_bundle import load_texture_file_manifest
from ontokin.execution_budget import SharedExecutionBudget,admit_entry_budget
from ontokin.construction import compile_construction
from ontokin.evaluator import _simulator
freeze=repo/'docs/language-design/torque-v0.1/freeze'
out=Path(sys.argv[2]);out.mkdir(exist_ok=False)
physics={c['id']:c for c in json.loads((freeze/'physics-cases.json').read_text())['cases']}
classes={c['id']:c for c in json.loads((freeze/'comparisons.json').read_text())['classes']}
expect={c['case']:c for c in json.loads((freeze/'state-expectations.json').read_text())['cases']}
def build(manifest,profile):
 b=load_texture_file_manifest(freeze/manifest);l=SharedExecutionBudget();admit_entry_budget(b.entry,l,profile=profile)
 c=compile_construction(b,execution_budget=l);return _simulator(c.model,work=c.reach_work),l
def normalize(x):
 if type(x) is F:return str(x)
 if type(x) is float:return {'hex':x.hex()}
 if type(x) in (list,tuple):return [normalize(v) for v in x]
 if type(x) is dict:return {k:normalize(v) for k,v in x.items()}
 if hasattr(x,'__dataclass_fields__'):return normalize(asdict(x))
 return x
def translation(sim,path):
 s=sim.state
 if path not in s.dynamic:return None
 v=s.dynamic[path];e=s.dynamic_errors[path]
 return normalize({'time':v.time,'since':v.since,'position':v.state.position,'velocity':v.state.velocity,
 'error_position':e.position_m,'error_velocity':e.velocity_m_per_s,'error_time':s.dynamic_error_times[path],
 'ideal_acceleration':s.ideal_accelerations[path]})
def angular(sim,path):
 s=sim.state;v=s.dynamic[path];e=s.dynamic_errors[path]
 return normalize({'orientation':v.state.orientation,'omega':v.state.omega,'rotation_error':e.rotation_rad,
                   'omega_error':e.angular_velocity_rad_per_s})
results=[];failures=[]
for cls in ['C3','C4']:
 for name in classes[cls]['inputs']:
  case=physics[name];path=expect[name]['target_path'];row={'class':cls,'case':name,'observations':[],'failures':[]}
  try:
   cand,cl=build(case['file_manifest'],'torque-0.1');base,bl=build(case['predecessor_control']['file_manifest'],'keyed-membership-0.1')
   for time,_,_ in case['samples']:
    c=cand.advance(F(time),'after');b=base.advance(F(time),'after')
    co,bo=c['objects'][path],b['objects'][path]
    ct,bt=translation(cand,path),translation(base,path)
    obs={'time':time,'candidate_translation':ct,'control_translation':bt,'candidate_cells':bool(cand.state.dynamic_cells),'control_cells':bool(base.state.dynamic_cells),'failures':[]}
    for key in ['position_m','velocity_m_per_s']+(['orientation_wxyz','angular_velocity_rad_per_s'] if cls=='C3' else []):
     if normalize(co[key])!=normalize(bo[key]):obs['failures'].append({'physical':key,'candidate':co[key],'control':bo[key]})
    if ct!=bt:obs['failures'].append('internal_translation')
    if cls=='C3':
     ca,ba=angular(cand,path),angular(base,path);obs.update(candidate_angular=ca,control_angular=ba)
     if ca!=ba:obs['failures'].append('legacy_angular_anchor')
    if obs['failures']:row['failures'].append({'time':time,'failures':obs['failures']})
    row['observations'].append(obs)
   row['candidate_work']=cl.report();row['control_work']=bl.report()
  except BaseException as e:row['failures'].append({'exception':repr(e),'traceback':traceback.format_exc()})
  (out/(cls+'-'+name+'.json')).write_text(json.dumps(row,indent=2)+'\n')
  results.append({'class':cls,'case':name,'status':'failed' if row['failures'] else 'passed','observations':len(row['observations'])})
  if row['failures']:failures.append({'class':cls,'case':name,'failures':row['failures']})
  print(cls,name,results[-1]['status'],str(row['failures'])[:1200],flush=True)
summary={'status':'failed' if failures else 'passed','results':results,'failures':failures,'source_head':subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()}
(out/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');sys.exit(bool(failures))
