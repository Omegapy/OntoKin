#!/usr/bin/env python3
"""Independent exact source-record and scalar-anchor expectations.

No OntoKin import, candidate read, source simulator, trig or GLB producer is
used here. This evaluates the separately specified finite scalar arithmetic
graph, and records state constraints for the literal physics table.
"""
from __future__ import annotations

from fractions import Fraction as F
from pathlib import Path
import json
import re

ROOT=Path(__file__).resolve().parents[1]


def rn(value):
    return F(float(F(value)))


def decimal(value):
    value=F(value); n=value.numerator; d=value.denominator; k=0
    while d%2==0: d//=2; k+=1
    if d!=1: raise ValueError('This author uses binary exact clocks only')
    digits=str(abs(n)*5**k).zfill(k+1)
    result=digits if not k else (digits[:-k]+'.'+digits[-k:]).rstrip('0').rstrip('.')
    return ('-' if n<0 else '')+result


def rational(value):
    value=F(value)
    return {'numerator':str(value.numerator),'denominator':str(value.denominator)}


def location(text,start,end,revision):
    return {'source_id':'entry','source_revision':revision,'start_byte':len(text[:start].encode()),'end_byte':len(text[:end].encode())}


def records(case):
    text=(ROOT/('sources/'+case['id']+'.ok')).read_text()
    revision=next(u['source_revision'] for u in case['identity']['manifest']['units'] if u['source_id']=='entry')
    result=[]
    for interval in case['torques']:
        key=interval['key']
        match=next(m for m in re.finditer(r'torque\s+[^;]+;',text) if '@ "'+key+'"' in m.group())
        stmt=match.group(); operand=stmt.index(' using ')+7; duration=stmt.index(' for ')+5
        target=interval['target']
        target_id=['torque-cases','demo',*re.findall(r'[A-Za-z0-9_-]+',target)]
        block=text.rfind('sequence {',0,match.start())
        sequence=text[block+len('sequence {'):match.start()].count(';')
        start=rn(interval['start']); width=rn(interval['duration'])
        result.append({'torque_key':key,'torque_element_id':['torque-cases','demo','torque',key],
          'target_path':target,'target_element_id':target_id,'program_revision':case['identity']['program_revision'],
          'source_location':location(text,match.start(),match.end(),revision),
          'operand_location':location(text,match.start()+operand,match.start()+duration-5,revision),
          'duration_location':location(text,match.start()+duration,match.end()-1,revision),
          'sequence_index':sequence,'axis':interval['axis'],'torque_n_m':float(rn(interval['torque'])),
          'activation_time_seconds':decimal(start),'duration_seconds':decimal(width),'completion_time_seconds':decimal(start+width)})
    return sorted(result,key=lambda r:(F(r['activation_time_seconds']),r['sequence_index']))


def scalar_state(case, source_records, clock, side):
    inertia=F(float.fromhex(case['inertia_hex']))
    intervals={r['torque_key']:r for r in source_records}
    starts={}; ends={}
    for record in source_records:
        starts.setdefault(F(record['activation_time_seconds']),[]).append(record)
        ends.setdefault(F(record['completion_time_seconds']),[]).append(record)
    axis=None; route='legacy'; tr=None; wr=rn(case['omega']); alpha=F(0)
    active={}; count_start=0; count_end=0; last=None; changes=[]
    # The impulse fixture has an explicit source-zero impulse. Before-side
    # at zero is the authored zero omega; after-side has its analytic 5/4.
    boundaries=set(starts)|set(ends)
    if case.get('impulse_order'): boundaries.add(F(0))
    for time in sorted(t for t in boundaries if t<clock or (t==clock and side=='after')):
        incoming=rn(wr+alpha*(time-tr)) if route=='split' else wr
        if case.get('impulse_order') and time==0:
            incoming=rn(case['omega_after_zero_impulse'])
            if route=='legacy': wr=incoming
        changes_at=[]
        for record in sorted(ends.get(time,[]),key=lambda r:r['torque_key']):
            active.pop(record['torque_key']); count_end+=1
            changes_at.append({'kind':'completed',**record})
        for record in starts.get(time,[]):
            active[record['torque_key']]=record; count_start+=1
            axis=record['axis'] if axis is None else axis
            changes_at.append({'kind':'started',**record})
        net=rn(sum((F(r['torque_n_m']) for r in active.values()),F(0)))
        next_alpha=rn(net/inertia)
        if (route=='legacy' and next_alpha) or (route=='split' and next_alpha!=alpha):
            route='split'; tr=time; wr=incoming
        alpha=next_alpha
        if changes_at: last=time; changes=changes_at
    net=rn(sum((F(r['torque_n_m']) for r in active.values()),F(0)))
    reference=sum((F(r['torque_n_m']) for r in active.values()),F(0))/inertia
    speed=rn(wr+alpha*(clock-tr)) if route=='split' else wr
    phase=rn(wr*(clock-tr)+alpha*(clock-tr)**2/2) if route=='split' else None
    exact={'active':[active[k] for k in sorted(active)],'net_torque_n_m':float(net),
       'angular_acceleration_rad_per_s2':float(alpha) if axis else None,'axis':axis,'rotation_route':route,
       'rotation_anchor_seconds':decimal(tr) if tr is not None else None,
       'signed_angular_speed_rad_per_s':float(speed) if axis else None,
       'phase_since_anchor_rad':float(phase) if phase is not None else None,
       'angular_acceleration_reference_rad_per_s2':rational(reference) if axis else None,
       'started_count':count_start,'completed_count':count_end,
       'last_change_time_seconds':decimal(last) if last is not None else None,'last_changes':changes}
    errors={'angular_error_bound_rad':None,'angular_speed_error_bound_rad_per_s':None}
    if axis:
        # Independent input-derived lower bounds are nonzero for underflow
        # despite identical canonical motion. Larger ordinary source error
        # is allowed only under this preselected small-case finite ceiling.
        angle_min=F(0); speed_min=F(0)
        if case['id'] in ('p24-underflow-is-neutral','p30-underflow-replacement'):
            elapsed=min(clock,F(1)); a=F(1,2**1075)
            speed_min=a*elapsed
            angle_min=a*elapsed**2/2+speed_min*max(F(0),clock-1)
        errors={'angular_error_bound_rad':{'minimum':rational(angle_min),'maximum':rational(F(1,2**36))},
                'angular_speed_error_bound_rad_per_s':{'minimum':rational(speed_min),'maximum':rational(F(1,2**36))}}
    return {'exact_fields':exact,'error_constraints':errors,
            'canonical_hex':{k:float(v).hex() for k,v in exact.items() if type(v) is float}}


def main():
    corpus=json.loads((ROOT/'physics-cases.json').read_text())
    result=[]
    for case in corpus['cases']:
        sr=records(case); horizon=F(case['horizon'])
        queries={(F(t),'after') for t,_,_ in case['samples']}
        # Include both sides of every in-prefix exact torque boundary, even
        # when it is not a user-requested display sample.
        boundaries={F(0)}|{F(r[k]) for r in sr for k in ('activation_time_seconds','completion_time_seconds')}
        for time in boundaries:
            if 0<=time<=horizon: queries.update(((time,'before'),(time,'after')))
        rows=[]
        for time,side in sorted(queries,key=lambda x:(x[0],x[1]=='after')):
            rows.append({'time_seconds':decimal(time),'time_fraction':str(time),'side':side,
                         **scalar_state(case,sr,time,side)})
        result.append({'case':case['id'],'program_revision':case['identity']['program_revision'],
                       'target_path':case['torques'][0]['target'],'source_records':sr,'observations':rows})
    document={'schema_version':'ontokin.torque-independent-state-expectations/1',
       'status':'frozen expected input; no candidate execution','candidate_output_used':False,
       'interpretation':'exact_fields and canonical_hex are authoritative; error_constraints are closed reduced-rational inequality obligations, not fabricated runtime values. Global unwrapped phases in physics-cases differ from phase_since_anchor after a genuine reanchor.',
       'null_state_for_unlatched_objects':{'active':[],'net_torque_n_m':0,'angular_acceleration_rad_per_s2':None,'axis':None,'rotation_route':'legacy','rotation_anchor_seconds':None,'signed_angular_speed_rad_per_s':None,'phase_since_anchor_rad':None,'angular_acceleration_reference_rad_per_s2':None,'angular_error_bound_rad':None,'angular_speed_error_bound_rad_per_s':None,'started_count':0,'completed_count':0,'last_change_time_seconds':None,'last_changes':[]},
       'small_corpus_error_ceiling_reason':'These cases have |unwrapped phase|<=16, at most eight angular source/transfer anchors, 96-bit source products with AXIS_ERROR=2^-74 and PRODUCT_ERROR=2^-91, and EXPOSED_ROTATION_ERROR=2^-50. At most sixteen phase/speed roundings each below 16*2^-53 plus subnormal allowance stay below 2^-43; 2^-36 is a fixed generous reported-error ceiling. Long-prefix domain02/domain03 are explicitly excluded.',
       'cases':result}
    (ROOT/'state-expectations.json').write_text(json.dumps(document,indent=2,sort_keys=True,allow_nan=False)+'\n')
    (ROOT/'state-expectations.json').chmod(0o644)
    print(json.dumps({'cases':len(result),'observations':sum(len(r['observations']) for r in result),'candidate_output_used':False}))


if __name__=='__main__': main()
