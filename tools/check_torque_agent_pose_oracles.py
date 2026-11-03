"""Independent frozen rational COM, quaternion, marker and landmark checks.

Reads retained real A11 Agent exchanges; imports no OntoKin production module.
The separate frozen Taylor oracle is unchanged and sees no candidate output.
"""
import gzip
import hashlib
import importlib.util
import itertools
import json
import math
from fractions import Fraction as F
from pathlib import Path
import sys

repo,inputs,out=map(Path,sys.argv[1:]);out.mkdir(exist_ok=False)
freeze=repo/'docs/language-design/torque-v0.1/freeze'
spec=importlib.util.spec_from_file_location('independent_frozen_oracle',freeze/'reference/verify_inputs.py')
oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)
physics={c['id']:c for c in json.loads((freeze/'physics-cases.json').read_text())['cases']}
targets={c['case']:c['target_path'] for c in json.loads((freeze/'state-expectations.json').read_text())['cases']}
canonical=lambda v:F(float(F(v)))
def add(x,y):return x[0]+y[0],x[1]+y[1]
def neg(x):return -x[1],-x[0]
def sub(x,y):return add(x,neg(y))
def mul(x,y):
 v=[a*b for a in x for b in y];return min(v),max(v)
def exact(v):return F(v),F(v)
def cross(x,y):return tuple(sub(mul(x[a],y[b]),mul(x[b],y[a])) for a,b in [(1,2),(2,0),(0,1)])
def rotate(q,vector):
 v=tuple(exact(a) for a in vector);u=q[1:];a=cross(u,v);b=cross(u,a)
 return tuple(add(vv,mul(exact(2),add(mul(q[0],aa),bb))) for vv,aa,bb in zip(v,a,b))
def squared_distance_upper(actual,intervals):
 return sum((max(abs(F(a)-v[0]),abs(F(a)-v[1]))**2 for a,v in zip(actual,intervals)),F(0))
def sqrt_lower(value):
 return F(math.isqrt((value.numerator << 192)//value.denominator),1<<96)
def com(case,time,side):
 p=list(map(canonical,case['position']));v=list(map(canonical,case['velocity']))
 if time==0 and side=='before' and ('impulse_order' in case or case.get('release')):v=[F(0)]*3
 acceleration=[F(0)]*3;anchor=F(0);mass=canonical(case['mass'])
 intervals=[(canonical(x['start']),canonical(x['start'])+canonical(x['duration']),tuple(map(canonical,x['force']))) for x in case['forces']]
 boundaries=sorted({clock for start,end,_ in intervals for clock in (start,end) if clock<=time})
 for clock in boundaries:
  force=[sum((value[i] for start,end,value in intervals if start<=clock<end),F(0)) for i in range(3)]
  next_acceleration=[F(float(F(float(value))/mass)) for value in force]
  if next_acceleration!=acceleration:
   dt=clock-anchor
   p=[F(float(a+b*dt+c*dt*dt/2)) for a,b,c in zip(p,v,acceleration)]
   v=[F(float(a+b*dt)) for a,b in zip(v,acceleration)]
   acceleration=next_acceleration;anchor=clock
 dt=time-anchor
 return tuple(F(float(a+b*dt+c*dt*dt/2)) for a,b,c in zip(p,v,acceleration)),tuple(F(float(a+b*dt)) for a,b in zip(v,acceleration))

tol=F(1,1<<40);all_rows=[];failures=[];observations=0;checks=0
for name,case in physics.items():
 file=inputs/name/'exchanges.jsonl.gz'
 if not file.exists():raise ValueError('Missing actual case '+name)
 seen=set();rows=[]
 for line in gzip.open(file,'rt'):
  exchange=json.loads(line);request=exchange['request'];response=exchange['response']
  if (request['operation']!='inspect' or request.get('project_id')!='a11-direct'
      or request.get('frame','world')!='world' or request.get('fields')!=['state']
      or response['status']!='succeeded'):continue
  clock=request['time'];identity=(clock['seconds'],clock['side'])
  if identity in seen:continue
  seen.add(identity);observations+=1;time=F(clock['seconds']);side=clock['side']
  items={v['path']:v['state'] for v in response['result']['items']};path=targets[name];root=items[path]
  phase,_,_,_=oracle.scalar_reference(case,time)
  raw=oracle.full_quaternion(case,oracle.trig_enclosure(phase/2,False),oracle.trig_enclosure(phase/2,True))
  q=tuple((F(v['lower_decimal']),F(v['upper_decimal'])) for v in raw)
  com_position,com_velocity=com(case,time,side)
  qerror=min(squared_distance_upper(root['orientation_wxyz'],q),
             squared_distance_upper([-x for x in root['orientation_wxyz']],q))
  assertions={'full_quaternion_euclidean':qerror<=tol*tol,
              'canonical_com_position':tuple(map(F,root['position_m']))==com_position,
              'canonical_com_velocity':tuple(map(F,root['velocity_m_per_s']))==com_velocity}
  offsets={path+'.label':(canonical(case['marker_radius']),F(0),F(0)),
           path+'.arm':(F(1,4),F(0),F(0)),path+'.arm.tip':(F(3,4),F(3,8),F(0))}
  comparisons=[]
  for marker,offset in offsets.items():
   observed=items[marker];rho=sqrt_lower(sum((x*x for x in offset),F(0)))
   ideal=tuple(add(exact(c),r) for c,r in zip(com_position,rotate(q,offset)))
   origin_error=squared_distance_upper(observed['position_m'],ideal)
   allowance=(1+rho)*tol
   assertions['marker_origin:'+marker]=origin_error<=allowance*allowance
   comparisons.append({'frame':marker,'kind':'origin','squared_error_upper':str(origin_error),'tolerance_squared':str(allowance*allowance)})
   if marker.endswith('.arm'):continue
   local_radius=sqrt_lower(F(21,64));allowance=(1+rho+local_radius)*tol
   observed_q=tuple(exact(v) for v in observed['orientation_wxyz'])
   for index,vertex in enumerate(itertools.product((F(0),F(1,4)),(F(0),F(1,2)),(F(0),F(1,8)))):
    ideal=tuple(add(exact(c),r) for c,r in zip(com_position,rotate(q,tuple(a+b for a,b in zip(offset,vertex)))))
    # Public source p/q determine the observed point; exact rational matrix
    # arithmetic introduces no additional host floating-point allowance.
    observed_point=[F(p)+r[0] for p,r in zip(observed['position_m'],rotate(observed_q,vertex))]
    error=squared_distance_upper(observed_point,ideal)
    assertions['landmark:'+marker+':'+str(index)]=error<=allowance*allowance
    comparisons.append({'frame':marker,'kind':'vertex','vertex':index,'squared_error_upper':str(error),'tolerance_squared':str(allowance*allowance)})
  checks+=len(assertions)
  row={'case':name,'time':clock,'assertions':assertions,'quaternion_squared_error_upper':str(qerror),'marker_comparisons':comparisons}
  rows.append(row)
  if not all(assertions.values()):failures.append({'case':name,'time':clock,'failed':[k for k,v in assertions.items() if not v]})
 (out/(name+'.json')).write_text(json.dumps(rows,indent=2)+'\n');all_rows.append({'case':name,'observations':len(rows),'actual_exchange_sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
summary={'status':'failed' if failures else 'passed','cases':len(all_rows),'observations':observations,'checks':checks,'failures':failures,'inputs':all_rows,
 'tolerances':'Frozen2^-40 quaternion Euclidean, exact canonical COM, and frozen(1+rho+r)*2^-40 marker/vertex allowances. 96-bit lower bounds for geometric radii make these tests strictly no looser than frozen allowances.',
 'oracle_sha256':hashlib.sha256((freeze/'reference/verify_inputs.py').read_bytes()).hexdigest()}
(out/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:summary[k] for k in ['status','cases','observations','checks','failures']}));sys.exit(bool(failures))
