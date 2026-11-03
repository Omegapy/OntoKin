"""Frozen C2 both-side fresh/resumed and C5 exact common-clock trajectories."""
import json
from fractions import Fraction as F
from pathlib import Path
import subprocess
import sys
import traceback
repo=Path(sys.argv[1]);sys.path.insert(0,str(repo));out=Path(sys.argv[2]);out.mkdir(exist_ok=False)
from ontokin.texture_bundle import load_texture_file_manifest
from ontokin.execution_budget import SharedExecutionBudget,admit_entry_budget
from ontokin.construction import compile_construction
from ontokin.evaluator import _simulator,time_text
freeze=repo/'docs/language-design/torque-v0.1/freeze'
cases={c['case']:c for c in json.loads((freeze/'state-expectations.json').read_text())['cases']}
physics={c['id']:c for c in json.loads((freeze/'physics-cases.json').read_text())['cases']}
def build(name):
 b=load_texture_file_manifest(freeze/(name+'.files.json'));l=SharedExecutionBudget();admit_entry_budget(b.entry,l,profile='torque-0.1');c=compile_construction(b,execution_budget=l)
 return _simulator(c.model,work=c.reach_work),l
def physics_fields(sample):
 return {p:{k:v[k] for k in ('position_m','orientation_wxyz','velocity_m_per_s','angular_velocity_rad_per_s','pose_authority')}
         for p,v in sample['objects'].items()}
results=[]
for name in ['p03-braking-reversal','p09-completion-starts-rotation']:
 row={'class':'C2','case':name,'observations':[],'failures':[]}
 try:
  resumed,ledger=build(name)
  for obs in sorted(cases[name]['observations'],key=lambda v:(F(v['time_seconds']),v['side']=='after')):
   clock,side=F(obs['time_seconds']),obs['side'];fresh,fl=build(name)
   direct=fresh.advance(clock,side);incremental=resumed.advance(clock,side)
   target=cases[name]['target_path'];dh=fresh.state.torques[target];rh=resumed.state.torques[target]
   assertions={'complete_public_state':direct==incremental,
    'exact_private_rotation_anchor':dh.rotation==rh.rotation,
    'exact_reference_error_origin':dh.reference==rh.reference,
    'exact_semantic_boundary_list':fresh.boundaries==resumed.boundaries,
    'exact_com_anchor':fresh.state.dynamic[target].time==resumed.state.dynamic[target].time}
   if not all(assertions.values()):row['failures'].append({'time':str(clock),'side':side,'assertions':assertions})
   row['observations'].append({'time':str(clock),'side':side,'assertions':assertions,'direct':direct,'resumed':incremental,'fresh_work':fl.report()})
  row['resumed_work']=ledger.report()
 except BaseException as e:row['failures'].append({'exception':repr(e),'traceback':traceback.format_exc()})
 (out/('C2-'+name+'.json')).write_text(json.dumps(row,indent=2)+'\n');results.append({'class':'C2','cases':[name],'status':'failed' if row['failures'] else 'passed','checks':len(row['observations']),'failures':row['failures']});print(results[-1],flush=True)
for left,right in [('p01-spin-up','p07-same-net-replacement'),('p19-torque-then-impulse','p20-impulse-then-torque')]:
 row={'class':'C5','cases':[left,right],'observations':[],'failures':[]}
 try:
  a,al=build(left);b,bl=build(right);horizon=min(F(physics[left]['horizon']),F(physics[right]['horizon']))
  clocks=sorted({F(o['time_seconds']) for n in (left,right) for o in cases[n]['observations'] if F(o['time_seconds'])<=horizon})
  fields=('net_torque_n_m','angular_acceleration_rad_per_s2','axis','rotation_route','rotation_anchor_seconds','signed_angular_speed_rad_per_s','phase_since_anchor_rad','angular_acceleration_reference_rad_per_s2')
  for clock in clocks:
   for side in ['before','after']:
    x=a.advance(clock,side);y=b.advance(clock,side);px=cases[left]['target_path'];py=cases[right]['target_path'];tx=x['objects'][px]['torques'];ty=y['objects'][py]['torques']
    assertions={'complete_physics':physics_fields(x)==physics_fields(y),'canonical_torque_law':{k:tx[k] for k in fields}=={k:ty[k] for k in fields},'same_full_internal_rotation_anchor':a.state.torques[px].rotation==b.state.torques[py].rotation}
    # Each independent per-source error constraint remains authoritative;
    # different source order may retain different conservative transfer bounds.
    for name,t in [(left,tx),(right,ty)]:
     expected=next((o for o in cases[name]['observations'] if F(o['time_seconds'])==clock and o['side']==side),None)
     if expected:
      for k,v in expected['error_constraints'].items():
       def ratio(z):return F(int(z['numerator']),int(z['denominator']))
       assertions[name+':'+k]=(t[k] is None if v is None else ratio(v['minimum'])<=ratio(t[k])<=ratio(v['maximum']))
    if not all(assertions.values()):row['failures'].append({'time':str(clock),'side':side,'assertions':assertions})
    row['observations'].append({'time':str(clock),'side':side,'assertions':assertions,'left':x,'right':y})
  row.update(left_work=al.report(),right_work=bl.report())
 except BaseException as e:row['failures'].append({'exception':repr(e),'traceback':traceback.format_exc()})
 (out/('C5-'+left+'--'+right+'.json')).write_text(json.dumps(row,indent=2)+'\n');results.append({'class':'C5','cases':[left,right],'status':'failed' if row['failures'] else 'passed','checks':len(row['observations']),'failures':row['failures']});print(results[-1],flush=True)
summary={'status':'failed' if any(r['status']=='failed' for r in results) else 'passed','results':results,'head':subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()}
(out/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');sys.exit(summary['status']!='passed')
