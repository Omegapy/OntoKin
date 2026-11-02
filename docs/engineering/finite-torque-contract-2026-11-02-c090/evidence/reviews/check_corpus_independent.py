#!/usr/bin/env python3
"""Independent static input/byte/rational audit; no OntoKin imports or execution."""
import argparse
import hashlib
import json
import math
from fractions import Fraction as F
from pathlib import Path
import re
import struct
import zlib

parser=argparse.ArgumentParser()
parser.add_argument('--freeze',type=Path,required=True)
parser.add_argument('--report',type=Path,required=True)
args=parser.parse_args()
assert not args.report.exists()
root=args.freeze
rows=[]

def check(name,actual,expected=True):
 rows.append({'name':name,'passed':actual==expected})
 if actual!=expected:
  rows[-1].update(actual=str(actual),expected=str(expected))

def load(path):return json.loads((root/path).read_text())
def sha(raw):return 'sha256:'+hashlib.sha256(raw).hexdigest()
def rn(value):
 f=float(F(value))
 if not math.isfinite(f):raise ValueError('Unexpected nonfinite independent reference')
 return F(f) if f else F(0)

identities={}
for p in sorted(root.glob('*.files.json')):
 m=json.loads(p.read_text());entry=m['entry'];raw=(root/entry['path']).read_bytes()
 units=[{'source_id':'entry','package_id':None,'version':None,'filename':entry['filename'],'source_revision':sha(raw)}]
 for unit in m['modules']:
  unitraw=(root/unit['path']).read_bytes();dig=sha(unitraw)
  units.append({'source_id':'package:'+unit['package_id']+'@'+unit['version'],'package_id':unit['package_id'],'version':unit['version'],'filename':unit['filename'],'source_revision':dig})
  check(p.name+'/pin/'+unit['package_id'],dig.encode() in raw)
 assets=[]
 for a in m['assets']:
  b=(root/a['path']).read_bytes();dig=sha(b)
  check(p.name+'/asset-pin/'+a['asset_id'],dig,a['sha256'])
  assets.append({'asset_id':a['asset_id'],'media_type':a['media_type'],'sha256':dig,'byte_length':len(b)})
 payload={'schema_version':'ontokin.bundle/0.2','entry_source_id':'entry','units':sorted(units,key=lambda x:x['source_id']),'assets':sorted(assets,key=lambda x:x['asset_id'])}
 canonical=json.dumps(payload,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
 identities[p.name]={'manifest':payload,'program_revision':sha(b'ontokin.bundle/0.2\0'+canonical)}
 check(p.name+'/regular',not p.is_symlink())

# Validate each retained identity recursively, pairing every top-level case or
# repair with its exact actual input, not a candidate response.
for table in ['physics-cases.json','refusal-cases.json','evaluation-domain-cases.json']:
 for c in load(table)['cases']:
  check(c['id']+'/bundle-identity',identities[c['file_manifest']],c['identity'])
  if 'predecessor_control' in c and isinstance(c['predecessor_control'],dict):
   con=c['predecessor_control'];check(c['id']+'/control-identity',identities[con['file_manifest']],con['identity'])

# PNG framing and CRC identify a literal valid asset independently.
png=(root/'assets/label.png').read_bytes()
check('png/signature',png[:8],b'\x89PNG\r\n\x1a\n')
i=8;chunks=[]
while i<len(png):
 n=int.from_bytes(png[i:i+4],'big');kind=png[i+4:i+8];data=png[i+8:i+8+n];crc=int.from_bytes(png[i+8+n:i+12+n],'big')
 check('png/crc/'+kind.decode(),zlib.crc32(kind+data)&0xffffffff,crc)
 chunks.append(kind);i+=12+n
check('png/exact-framing',i,len(png));check('png/end',chunks[-1],b'IEND')

# Independently parse the finite literal event subset actually authored here.
num=r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?'
torque_re=re.compile(r'torque\s+(.+?)\s+@\s+"([^\"]+)"\s+about\s+(world_[xyz])\s+using\s+('+num+r')\[N\*m\]\s+for\s+('+num+r')\[s\];')
block_re=re.compile(r'at\s+('+num+r')\[s\]\s+sequence\s*\{(.*?)\}',re.S)
physics=load('physics-cases.json')['cases'];states={c['case']:c for c in load('state-expectations.json')['cases']}
for case in physics:
 key=case['id'];raw=(root/'sources'/f'{key}.ok').read_bytes();text=raw.decode();events=[]
 for block in block_re.finditer(text):
  start=rn(block.group(1))
  for m in torque_re.finditer(block.group(2)):
   target,tkey,axis,tau,duration=m.groups();absolute=block.start(2)+m.start();end=block.start(2)+m.end()
   events.append({'target':target,'key':tkey,'axis':axis,'start':start,'end':start+rn(duration),'duration':rn(duration),'torque':rn(tau),'sequence':block.group(2)[:m.start()].count(';'),'source_start':len(text[:absolute].encode()),'source_end':len(text[:end].encode()),'statement':m.group()})
 check(key+'/event-count',len(events),len(case['torques']))
 expected_events=[(t['target'],t['key'],t['axis'],rn(t['start']),rn(t['duration']),rn(t['torque'])) for t in case['torques']]
 check(key+'/literal-events',[(e['target'],e['key'],e['axis'],e['start'],e['duration'],e['torque']) for e in events],expected_events)
 mass=rn(case['mass']);radius=rn(case['radius']);inertia=rn(F(2,5)*mass*radius*radius)
 check(key+'/inertia',float(inertia).hex(),case['inertia_hex'])
 if key!='p27-generated-two-carriers':
  check(key+'/literal-mass',rn(re.search(r'body_mass\s*=\s*('+num+r')\[kg\]',text).group(1)),mass)
  check(key+'/literal-radius',rn(re.search(r'body_radius\s*=\s*('+num+r')\[m\]',text).group(1)),radius)
 sr=states[key]['source_records']
 for e,r in zip(events,sr):
  check(key+'/'+e['key']+'/source-span',raw[r['source_location']['start_byte']:r['source_location']['end_byte']].decode(),e['statement'])
  check(key+'/'+e['key']+'/start',F(r['activation_time_seconds']),e['start'])
  check(key+'/'+e['key']+'/end',F(r['completion_time_seconds']),e['end'])
  check(key+'/'+e['key']+'/sequence',r['sequence_index'],e['sequence'])
  check(key+'/'+e['key']+'/identity',r['torque_element_id'],['torque-cases','demo','torque',e['key']])
  check(key+'/'+e['key']+'/program',r['program_revision'],case['identity']['program_revision'])
  for field,pattern in [('operand_location',r'using\s+(.+?)\s+for'),('duration_location',r'for\s+(.+?);')]:
   check(key+'/'+e['key']+'/'+field,raw[r[field]['start_byte']:r[field]['end_byte']].decode(),re.search(pattern,e['statement']).group(1))
 initial=rn(case['omega'])
 impulse_delta=F(0)
 for m in re.finditer(r'impulse\s+ball\s+using\s+vector\(world,\s*('+num+r')\[N\*s\],\s*('+num+r')\[N\*s\],\s*('+num+r')\[N\*s\]\)\s+at\s+point\(ball.frame,\s*('+num+r')\[m\],\s*('+num+r')\[m\],\s*('+num+r')\[m\]\);',text):
  jx,jy,jz,rx,ry,rz=map(rn,m.groups());axis_index={'world_x':0,'world_y':1,'world_z':2}[case['axis']]
  cross=(ry*jz-rz*jy,rz*jx-rx*jz,rx*jy-ry*jx)
  impulse_delta += cross[axis_index]/inertia
 if case.get('impulse_order'):
  check(key+'/literal-impulse',rn(initial+impulse_delta),rn(case['omega_after_zero_impulse']))
 for obs in states[key]['observations']:
  t=F(obs['time_seconds']);side=obs['side'];active={};axis=None;route='legacy';anchor=None;w_anchor=initial;alpha=F(0);started=completed=0;last=None;changes=[]
  if impulse_delta and (t>0 or side=='after'):w_anchor=rn(w_anchor+impulse_delta)
  boundaries=sorted({e[k] for e in events for k in ('start','end') if e[k]<t or (e[k]==t and side=='after')})
  for b in boundaries:
   incoming=rn(w_anchor+alpha*(b-anchor)) if route=='split' else w_anchor
   delta=[]
   for e in sorted((e for e in events if e['end']==b),key=lambda e:e['key']):
    del active[e['key']];completed+=1;delta.append(('completed',e['key']))
   for e in (e for e in events if e['start']==b):
    active[e['key']]=e;started+=1;axis=e['axis'] if axis is None else axis;delta.append(('started',e['key']))
   net=rn(sum((e['torque'] for e in active.values()),F(0)));next_alpha=rn(net/inertia)
   if (route=='legacy' and next_alpha!=0) or (route=='split' and next_alpha!=alpha):
    route='split';anchor=b;w_anchor=incoming
   alpha=next_alpha
   if delta:last=b;changes=delta
  f=obs['exact_fields'];prefix=key+'/'+obs['time_fraction']+'/'+side
  check(prefix+'/active',[r['torque_key'] for r in f['active']],sorted(active))
  check(prefix+'/counts',(f['started_count'],f['completed_count']),(started,completed))
  check(prefix+'/axis-route',(f['axis'],f['rotation_route']),(axis,route))
  check(prefix+'/anchor',None if f['rotation_anchor_seconds'] is None else F(f['rotation_anchor_seconds']),anchor)
  check(prefix+'/last',None if f['last_change_time_seconds'] is None else F(f['last_change_time_seconds']),last)
  check(prefix+'/changes',[(r['kind'],r['torque_key']) for r in f['last_changes']],changes)
  net=rn(sum((e['torque'] for e in active.values()),F(0)))
  check(prefix+'/net',rn(f['net_torque_n_m']),net)
  check(prefix+'/alpha',None if f['angular_acceleration_rad_per_s2'] is None else rn(f['angular_acceleration_rad_per_s2']),alpha if axis else None)
  speed=rn(w_anchor+alpha*(t-anchor)) if route=='split' else w_anchor
  check(prefix+'/speed',None if f['signed_angular_speed_rad_per_s'] is None else rn(f['signed_angular_speed_rad_per_s']),speed if axis else None)
  phase=rn(w_anchor*(t-anchor)+alpha*(t-anchor)**2/2) if route=='split' else None
  check(prefix+'/phase',None if f['phase_since_anchor_rad'] is None else rn(f['phase_since_anchor_rad']),phase)
  ar=sum((e['torque'] for e in active.values()),F(0))/inertia
  reported=f['angular_acceleration_reference_rad_per_s2']
  check(prefix+'/reference',None if reported is None else F(int(reported['numerator']),int(reported['denominator'])),ar if axis else None)
  for field,bounds in obs['error_constraints'].items():
   if bounds is None:check(prefix+'/'+field+'/unlatched',axis,None);continue
   lo=F(int(bounds['minimum']['numerator']),int(bounds['minimum']['denominator']));hi=F(int(bounds['maximum']['numerator']),int(bounds['maximum']['denominator']))
   check(prefix+'/'+field+'/ordered',0<=lo<=hi)

# Actual patch bytes, half-open coordinates and replacement result are exact.
repairs=load('agent/repairs.json');base=(root/'sources/agent-base.ok').read_bytes()
for r in repairs['repairs']:
 p=r['patch'];before=base[p['start_byte']:p['end_byte']]
 check(r['id']+'/patch-text',before.decode(),p['expected_text'])
 changed=base[:p['start_byte']]+p['replacement'].encode()+base[p['end_byte']:]
 check(r['id']+'/exact-patched-bytes',changed,(root/'sources'/f"{r['id']}.ok").read_bytes())
 check(r['id']+'/patched-identity',identities[r['file_manifest']],r['to'])

# Every known new source and recording structural stage has all four failures.
stages={'torque_source','torque_boundary_scan','torque_completion','torque_activation','torque_impulse_axis','torque_aggregate_begin','torque_aggregate_term','torque_aggregate_publish','torque_reference_origin','torque_rotation_anchor','torque_segment','torque_segment_vertex','torque_projection','torque_boundary_commit','torque_recording_path','torque_recording_phase','torque_recording_certificate'}
resources=load('agent/resource-cases.json')
check('resource/stage-coverage',{r['stage'] for r in resources['cases']},stages)
for r in resources['cases']:
 check(r['id']+'/faults',set(r['fault_variants']),{'cancel','operation-cap','deadline','original-callback-exception'})

result={'schema_version':'ontokin.independent-corpus-static-review-check/1','outcome':'passed' if all(r['passed'] for r in rows) else 'failed','checks':len(rows),'failures':[r for r in rows if not r['passed']],'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'input_root':str(root),'production_imported_or_executed':False,'candidate_output_used':False,'runtime_or_release_acceptance':False,'rows':rows}
args.report.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))
raise SystemExit(0 if result['outcome']=='passed' else 1)
