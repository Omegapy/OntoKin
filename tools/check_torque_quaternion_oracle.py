import sys,json,hashlib,importlib.util
from fractions import Fraction as F
from pathlib import Path
repo=Path(sys.argv[1]);freeze=repo/'docs/language-design/torque-v0.1/freeze'
observed=Path(sys.argv[2]);out=Path(sys.argv[3]);out.mkdir(exist_ok=False)
spec=importlib.util.spec_from_file_location('frozen_independent_torque_oracle',freeze/'reference/verify_inputs.py')
oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)
physics={c['id']:c for c in json.loads((freeze/'physics-cases.json').read_text())['cases']}
targets={c['case']:c['target_path'] for c in json.loads((freeze/'state-expectations.json').read_text())['cases']}
tol=F(1,1<<40);rows=[];failures=[]
for path in sorted(observed.glob('p*.json')):
 row=json.loads(path.read_text());case=physics[row['case']];time=F(row['time']);target=targets[row['case']]
 # An incoming zero boundary precedes authored impulses; positive-time
 # orientation remains continuous at every authored/completion boundary.
 if time==0 and row['side']=='before':continue
 theta,omega,_,_=oracle.scalar_reference(case,time)
 q=oracle.full_quaternion(case,oracle.trig_enclosure(theta/2,False),oracle.trig_enclosure(theta/2,True))
 intervals=[(F(v['lower_decimal']),F(v['upper_decimal'])) for v in q]
 actual=list(map(F,row['state']['objects'][target]['orientation_wxyz']))
 def discrepancy(sign):
  return max(max(F(0),lo-sign*v,sign*v-hi) for (lo,hi),v in zip(intervals,actual))
 err=min(discrepancy(1),discrepancy(-1))
 check={'case':row['case'],'time':row['time'],'side':row['side'],'observed_file':path.name,
        'observed_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'oracle_quaternion':q,
        'actual_quaternion':row['state']['objects'][target]['orientation_wxyz'],
        'maximum_component_discrepancy_upper':str(err),'tolerance':str(tol),'status':'passed' if err<=tol else 'failed'}
 rows.append(check)
 if err>tol:failures.append(check)
(out/'quaternion-comparisons.json').write_text(json.dumps(rows,indent=2)+'\n')
summary={'status':'failed' if failures else 'passed','checks':len(rows),'cases':len({r['case'] for r in rows}),
         'failed':failures,'oracle_sha256':hashlib.sha256((freeze/'reference/verify_inputs.py').read_bytes()).hexdigest(),
         'comparison':'All four complete quaternion components, Hamilton left product, publication-sign invariant; exact frozen Taylor/rational oracle.'}
(out/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:summary[k] for k in ['status','checks','cases','failed']}));sys.exit(bool(failures))
