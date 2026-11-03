"""Actual A11 Agent stores, repeated timed inspections, and resumed runs.

Usage: python -B tools/run_torque_agent_state_matrix.py REPO OUTPUT_DIRECTORY
The immutable source cohort and every complete request/response are retained.
"""
import copy
import gzip
import hashlib
import importlib.util
import json
from fractions import Fraction as F
from pathlib import Path
import sqlite3
import subprocess
import sys
import traceback

repo=Path(sys.argv[1]);sys.path.insert(0,str(repo));out=Path(sys.argv[2]);out.mkdir(exist_ok=False)
from ontokin.texture_bundle import load_texture_file_manifest
from ontokin.torque_agent import TorqueAgentService
from ontokin.torque_protocol import canonical_request
from ontokin.evaluator import time_text

freeze=repo/'docs/language-design/torque-v0.1/freeze'
cases=json.loads((freeze/'state-expectations.json').read_text())['cases']
physics={c['id']:c for c in json.loads((freeze/'physics-cases.json').read_text())['cases']}
spec=importlib.util.spec_from_file_location('independent_frozen_oracle',freeze/'reference/verify_inputs.py')
oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)
identity={'head':subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip(),
          'sources':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (repo/'ontokin').glob('*.py')}}
(out/'SOURCE-IDENTITIES.json').write_text(json.dumps(identity,indent=2)+'\n')
def ratio(value):return F(int(value['numerator']),int(value['denominator']))
def clean_state(state):return {k:v for k,v in state.items() if k not in {'run_id','valid_interval'}}
all_results=[]
for case in cases:
 name=case['case'];directory=out/name;directory.mkdir();checks=[];failures=[];count=0
 service=TorqueAgentService(directory/'store');last_request=last_response=None
 log=gzip.open(directory/'exchanges.jsonl.gz','wt',encoding='utf8')
 def check(name,condition):
  checks.append({'check':name,'status':'passed' if condition else 'failed'})
  if not condition:raise AssertionError(name)
 def send(project,operation,**fields):
  global count,last_request,last_response
  count+=1
  request={'schema_version':'ontokin.agent/0.22','project_id':project,'request_id':'a11-'+str(count),'operation':operation,**fields}
  clean,raw=canonical_request(request);response=service.handle(clean)
  log.write(json.dumps({'request':clean,'canonical_request_sha256':hashlib.sha256(raw.encode()).hexdigest(),'response':response},sort_keys=True,separators=(',',':'))+'\n');log.flush()
  last_request,last_response=clean,response
  check(operation+' succeeded',response['status']=='succeeded')
  return response
 def inspect(project,run,time,side,frame=None,fields=None,selector=None):
  return send(project,'inspect',program_revision=case['program_revision'],run_id=run,
    selector=selector or {'kind':'object'},fields=fields or ['state'],
    time={'seconds':time,'side':side},limit=100,**({} if frame is None else {'frame':frame}))
 try:
  bundle=load_texture_file_manifest(freeze/(name+'.files.json'))
  check('frozen complete program identity',bundle.program_revision==case['program_revision']==physics[name]['identity']['program_revision'])
  direct='a11-direct';resumed='a11-resumed'
  for project in (direct,resumed):send(project,'create',expected_program_revision=None,requested_level='constructed',bundle=bundle.to_payload())
  horizon=time_text(F(physics[name]['horizon']))
  full=send(direct,'evaluate',program_revision=case['program_revision'],run_id=None,until_seconds=horizon);direct_run=full['run_id']
  observed={}
  for index,obs in enumerate(case['observations']):
   first=inspect(direct,direct_run,obs['time_seconds'],obs['side']);second=inspect(direct,direct_run,obs['time_seconds'],obs['side'])
   check('new-ID repeated complete result '+str(index),first['result']==second['result'])
   items={v['path']:v['state'] for v in first['result']['items']};value=items[case['target_path']]['torques']
   observed[(obs['time_seconds'],obs['side'])]=items
   for key,expected in obs['exact_fields'].items():check('exact '+str(index)+' '+key,value[key]==expected)
   for key,expected in obs['canonical_hex'].items():check('canonical '+str(index)+' '+key,type(value[key]) is float and value[key].hex()==expected)
   for key,bounds in obs['error_constraints'].items():check('error '+str(index)+' '+key,value[key] is None if bounds is None else ratio(bounds['minimum'])<=ratio(value[key])<=ratio(bounds['maximum']))
   if F(obs['time_seconds'])!=0 or obs['side']=='after':
    theta,_,_,_=oracle.scalar_reference(physics[name],F(obs['time_seconds']))
    pairs=oracle.full_quaternion(physics[name],oracle.trig_enclosure(theta/2,False),oracle.trig_enclosure(theta/2,True))
    actual=items[case['target_path']]['orientation_wxyz'];tol=F(1,1<<40)
    def matches(sign):return all(F(v['lower_decimal'])-tol<=sign*F(a)<=F(v['upper_decimal'])+tol for v,a in zip(pairs,actual))
    check('full independent quaternion '+str(index),matches(1) or matches(-1))
  source_query=inspect(direct,direct_run,horizon,'after',fields=['source'],selector={'path':case['target_path']})
  rows=source_query['result']['items'][0]['source']['torque_intervals']
  check('complete independent source intervals',rows==case['source_records'])
  after=sorted({obs['time_seconds'] for obs in case['observations'] if obs['side']=='after'},key=F)
  torque_boundaries={F(record[field]) for record in case['source_records']
                    for field in ('activation_time_seconds','completion_time_seconds')
                    if 0<F(record[field])<=F(horizon)}
  first_torque_boundary=min(torque_boundaries) if torque_boundaries else None
  run=None;reopened=False
  for time in after:
   result=send(resumed,'evaluate',program_revision=case['program_revision'],run_id=run,until_seconds=time)
   if run is not None:check('same actual resumed run '+time,result['run_id']==run)
   run=result['run_id'];current=inspect(resumed,run,time,'after')
   items={v['path']:v['state'] for v in current['result']['items']}
   for path,value in items.items():
    old=observed[(time,'after')][path]
    check('direct inspected run prefix '+time+' '+path,F(old['valid_interval']['end_seconds'])==F(horizon))
    check('resumed inspected run prefix '+time+' '+path,F(value['valid_interval']['end_seconds'])==F(time))
    check('all other validity fields '+time+' '+path,{k:v for k,v in old['valid_interval'].items() if k!='end_seconds'}=={k:v for k,v in value['valid_interval'].items() if k!='end_seconds'})
   check('direct/resumed complete state '+time,{p:clean_state(v) for p,v in items.items()}=={p:clean_state(v) for p,v in observed[(time,'after')].items()})
   if not reopened and first_torque_boundary is not None and F(time)==first_torque_boundary:
    previous_request,previous_response=copy.deepcopy(last_request),copy.deepcopy(last_response)
    service.close();service=TorqueAgentService(directory/'store');retry=service.handle(previous_request)
    log.write(json.dumps({'request':previous_request,'response':retry,'historical_retry_after_reopen':True},sort_keys=True,separators=(',',':'))+'\n');log.flush()
    check('same-ID historical response after reopen',retry==previous_response);reopened=True
  check('reopened at first in-prefix nonzero torque boundary',first_torque_boundary is None or reopened)
  for time,side in observed:
   response=inspect(direct,direct_run,time,side,frame=case['target_path']+'.frame',selector={'path':case['target_path']})
   value=response['result']['items'][0]['state'];world=observed[(time,side)][case['target_path']]
   check('self-frame complete world scalar history '+time+' '+side,value['torques']==world['torques'])
   check('self-frame origin '+time+' '+side,all(v==0 for v in value['position_m']))
  service.close();service=None;log.close()
  with sqlite3.connect('file:'+str(directory/'store/torque-program-agent.sqlite3')+'?mode=ro',uri=True) as db:
   check('actual store integrity',db.execute('pragma integrity_check').fetchone()[0]=='ok')
   metadata=dict(db.execute('select name,value from metadata'));check('actual torque store schema',metadata['schema_version']=='ontokin.torque-program-agent-store/0.1')
   counts={t:db.execute('select count(*) from '+t).fetchone()[0] for t in ['projects','sources','runs','requests','artifacts']}
   check('no unintended artifacts',counts['artifacts']==0)
   (directory/'store-readback.json').write_text(json.dumps({'metadata':metadata,'counts':counts},indent=2)+'\n')
 except BaseException as e:failures.append({'exception':repr(e),'traceback':traceback.format_exc()})
 finally:
  if service is not None:service.close()
  if not log.closed:log.close()
 row={'case':name,'status':'failed' if failures else 'passed','exchanges':count,'checks':checks,'failures':failures}
 (directory/'SUMMARY.json').write_text(json.dumps(row,indent=2)+'\n');all_results.append({'case':name,'status':row['status'],'exchanges':count,'checks':len(checks),'failures':failures})
 print(name,row['status'],len(checks),'checks',str(failures)[:500],flush=True)
summary={'status':'failed' if any(v['status']=='failed' for v in all_results) else 'passed','cases':len(all_results),'checks':sum(r['checks'] for r in all_results),'results':all_results,'scope':'A11 positive complete physics/Agent boundary, repeated fresh-ID inspect, direct and resumed actual runs, actual reopen/historical retry, self-frame scalar history, exact sources and independent full quaternion. Domain and refusal matrices recorded separately.'}
(out/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');sys.exit(summary['status']!='passed')
