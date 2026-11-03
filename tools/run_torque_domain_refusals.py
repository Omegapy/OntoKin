import sys,json,traceback,platform,hashlib
from pathlib import Path
from fractions import Fraction as F
repo=Path(sys.argv[1]);sys.path.insert(0,str(repo))
from ontokin.texture_bundle import load_texture_file_manifest
from ontokin.execution_budget import SharedExecutionBudget,admit_entry_budget
from ontokin.construction import compile_construction
from ontokin.evaluator import evaluate_prefix
from ontokin.program_diagnostics import diagnostic_dict
from ontokin.diagnostics import OntoKinError
f=repo/'docs/language-design/torque-v0.1/freeze';out=Path(sys.argv[2]);out.mkdir(exist_ok=False)
rows=[]
def ratio(v):return F(int(v['numerator']),int(v['denominator']))
def execute(name,t=None,side='after'):
 b=load_texture_file_manifest(f/(name+'.files.json'));l=SharedExecutionBudget();admit_entry_budget(b.entry,l,profile='torque-0.1');row={'id':name,'side':side,'time':t,'issues':[]}
 try:
  c=compile_construction(b,execution_budget=l);r=evaluate_prefix(c.model,c.model.duration if t is None else t,side=side,work=c.reach_work)
  row.update(failure=None if r['failure'] is None else diagnostic_dict(r['failure'].diagnostic,b),state=r['last_valid_state'],valid_until_seconds=r['valid_until_seconds'],valid_until_side=r['valid_until_side'])
 except OntoKinError as e:row['failure']=diagnostic_dict(e.diagnostic,b)
 except BaseException as e:row.update(exception=repr(e),traceback=traceback.format_exc());row['issues'].append('uncaught')
 row['work']=l.report(status='valid');return row
for case in json.loads((f/'evaluation-domain-cases.json').read_text())['cases']:
 r=execute(case['id'],case['time_seconds'],case['side'])
 if r.get('failure'):r['issues'].append('unexpected_failure')
 elif r.get('state'):
  s=r['state']['objects']['ball'];v=s['torques']
  for k,field in [('expected_phase_hex','phase_since_anchor_rad'),('expected_speed_hex','signed_angular_speed_rad_per_s'),('expected_canonical_speed_hex','signed_angular_speed_rad_per_s'),('expected_alpha_hex','angular_acceleration_rad_per_s2')]:
   if k in case and v[field].hex()!=case[k]:r['issues'].append(k)
  for k,field in [('expected_rotation_route','rotation_route'),('expected_rotation_anchor','rotation_anchor_seconds'),('expected_rotation_anchor_seconds','rotation_anchor_seconds')]:
   if k in case and v[field]!=case[k]:r['issues'].append(k)
  if 'expected_alpha_reference' in case and ratio(v['angular_acceleration_reference_rad_per_s2'])!=F(case['expected_alpha_reference']):r['issues'].append('reference_alpha')
  for key in ['angular_error_bound_rad','angular_speed_error_bound_rad_per_s']:
   if 'minimum_'+key in case and ratio(v[key])<F(case['minimum_'+key]):r['issues'].append('minimum_'+key)
  if 'expected_canonical_orientation_wxyz' in case and s['orientation_wxyz']!=case['expected_canonical_orientation_wxyz']:r['issues'].append('orientation')
 rows.append(r);print(r['id'],r['issues'],flush=True)
for case in json.loads((f/'refusal-cases.json').read_text())['cases']:
 expected=case['expected']
 if expected.get('phase') not in ('admission','evaluation') or case['id']=='n25-delivery-clock-collapse':continue
 for side in (['before','after'] if 'side_rule' in expected else ['after']):
  r=execute(case['id'],expected.get('failed_request_seconds'),side)
  actual=r.get('failure')
  if actual is None:r['issues'].append('expected_failure_missing')
  else:
   for key in ['code','phase','message']:
    if key in expected and actual.get(key)!=expected[key]:r['issues'].append({'field':key,'actual':actual.get(key),'expected':expected[key]})
   for key,value in expected.get('required_details',{}).items():
    if actual['details'].get(key)!=value:r['issues'].append({'detail':key,'actual':actual['details'].get(key),'expected':value})
   for key in ['start_byte','end_byte']:
    if key in expected.get('primary_source',{}) and actual['primary'][key]!=expected['primary_source'][key]:r['issues'].append({'primary':key,'actual':actual['primary'][key],'expected':expected['primary_source'][key]})
   if actual['time'] and actual['time']['side']!=(side if 'side_rule'in expected else expected.get('side','after')):r['issues'].append('wrong_side')
  rows.append(r);print(r['id'],side,r['issues'],flush=True)
for i,r in enumerate(rows):(out/(str(i)+'-'+r['id']+'.json')).write_text(json.dumps(r,indent=2)+'\n')
summary={'status':'failed' if any(r['issues'] for r in rows)else'passed','cases':len(rows),'failures':[{'id':r['id'],'side':r['side'],'issues':r['issues']}for r in rows if r['issues']],'python':platform.python_version()}
(out/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print(summary);sys.exit(summary['status']!='passed')
