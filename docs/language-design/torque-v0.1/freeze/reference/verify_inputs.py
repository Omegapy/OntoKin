#!/usr/bin/env python3
"""Check independent C090 inputs, exact identities and analytic expectations.

This is a standard-library reference, never an OntoKin runtime or conformance
runner. It imports no production module and reads no candidate observation.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, localcontext, ROUND_FLOOR, ROUND_CEILING
from fractions import Fraction as F
import hashlib
import json
import math
from pathlib import Path
import platform
import sys

ROOT=Path(__file__).resolve().parents[1]


def sha(raw):
    return 'sha256:'+hashlib.sha256(raw).hexdigest()


def load(path):
    return json.loads((ROOT/path).read_text())


def canonical(value):
    return F(float(F(value)))


def scalar_reference(case, end):
    # This separate work/energy integrator is a check on the literal finite
    # table. It is not canonical anchor authority: state-expectations.json
    # separately requires preserved anchors and one-round phase/speed graphs.
    inertia=F(float.fromhex(case['inertia_hex']))
    w=canonical(case.get('omega_after_zero_impulse',case['omega']))
    phase=F(0)
    time=F(0)
    active=[]
    intervals=[(canonical(t['start']),canonical(t['start'])+canonical(t['duration']),canonical(t['torque']),t['key']) for t in case['torques']]
    boundaries=sorted({F(0),end,*[v for a,b,_,_ in intervals for v in (a,b) if 0<=v<=end]})
    work=F(0)
    residual=F(0)
    for left,right in zip(boundaries,boundaries[1:]):
        active=[v for a,b,v,_ in intervals if a<=left<b]
        net=F(float(sum(active,F(0))))
        alpha=F(float(net/inertia))
        h=right-left
        increment=w*h+alpha*h*h/2
        unrounded_w=w+alpha*h
        next_w=F(float(unrounded_w))
        work+=net*increment
        # This is the exact canonical work/energy discrepancy contribution,
        # not a tolerance fitted to an implementation.
        residual+=(inertia*alpha-net)*increment+inertia*(next_w*next_w-unrounded_w*unrounded_w)/2
        phase+=increment
        w=next_w
        time=right
    return phase,w,work,residual


def trig_enclosure(value, sine):
    """Taylor polynomial plus Lagrange remainder, entirely rational.

    Every derivative of sin/cos has magnitude at most one. The remainder
    after degree n therefore does not exceed |x|^(n+1)/(n+1)! for any real x.
    Here |x|<=16 and degree 180 gives ample independent oracle precision.
    """
    x=F(value)
    if abs(x)>16:
        raise ValueError('This independent corpus oracle is bounded to |x| <= 16')
    total=F(0)
    for k in range(91):
        power=2*k+(1 if sine else 0)
        if power>180:
            break
        total+=(-1 if k%2 else 1)*x**power/math.factorial(power)
    remainder=abs(x)**181/math.factorial(181)
    return total-remainder,total+remainder


def directed_decimal(value, direction):
    with localcontext() as context:
        context.prec=60
        context.rounding=direction
        return format(Decimal(value.numerator)/Decimal(value.denominator),'f')


def interval_data(pair):
    return {'lower_decimal':directed_decimal(pair[0],ROUND_FLOOR),
            'upper_decimal':directed_decimal(pair[1],ROUND_CEILING)}


def full_quaternion(case, cosine, sine):
    """Hamilton left product of world-axis increment with saved initial q."""
    q=[F(v) for v in case.get('initial_quaternion',['1','0','0','0'])]
    axis=[F(0),F(0),F(0)];axis[{'world_x':0,'world_y':1,'world_z':2}[case['axis']]]=F(1)
    w,x,y,z=q; ax,ay,az=axis
    coefficients=[(w,-ax*x-ay*y-az*z),(x,w*ax+ay*z-az*y),
                  (y,w*ay+az*x-ax*z),(z,w*az+ax*y-ay*x)]
    def scale(pair,factor):
        values=[pair[0]*factor,pair[1]*factor]
        return min(values),max(values)
    result=[]
    for c,s in coefficients:
        a=scale(cosine,c);b=scale(sine,s)
        result.append(interval_data((a[0]+b[0],a[1]+b[1])))
    return result


def identity(name):
    m=load(name+'.files.json')
    units=[{'source_id':'entry','package_id':None,'version':None,'filename':m['entry']['filename'],'source_revision':sha((ROOT/m['entry']['path']).read_bytes())}]
    for unit in m['modules']:
        units.append({'source_id':'package:'+unit['package_id']+'@'+unit['version'],'package_id':unit['package_id'],'version':unit['version'],'filename':unit['filename'],'source_revision':sha((ROOT/unit['path']).read_bytes())})
    assets=[{'asset_id':a['asset_id'],'media_type':a['media_type'],'sha256':sha((ROOT/a['path']).read_bytes()),'byte_length':(ROOT/a['path']).stat().st_size} for a in m['assets']]
    payload={'schema_version':'ontokin.bundle/0.2','entry_source_id':'entry','units':sorted(units,key=lambda u:u['source_id']),'assets':sorted(assets,key=lambda a:a['asset_id'])}
    canonical_json=json.dumps(payload,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
    return {'program_revision':sha(b'ontokin.bundle/0.2\0'+canonical_json),'manifest':payload}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('report',type=Path)
    args=ap.parse_args()
    if args.report.exists():
        raise SystemExit('Use a fresh report path; earlier observations are immutable')
    rows=[]; oracle=[]
    def check(name,actual,expected):
        passed=actual==expected
        rows.append({'id':name,'passed':passed,'actual':actual,'expected':expected})
    corpus=load('physics-cases.json')
    check('production-independent',corpus['candidate_output_used'],False)
    for case in corpus['cases']:
        key=case['id']
        check(key+'/identity',identity(key),case['identity'])
        control=case['predecessor_control']['file_manifest'].removesuffix('.files.json')
        check(key+'/control-identity',identity(control),case['predecessor_control']['identity'])
        inertia=F(float(F(2,5)*canonical(case['mass'])*canonical(case['radius'])**2))
        check(key+'/inertia',float(inertia).hex(),case['inertia_hex'])
        initial=canonical(case.get('omega_after_zero_impulse',case['omega']))
        for time,phase,speed in case['samples']:
            theta,omega,work,residual=scalar_reference(case,F(time))
            check(key+'/phase/'+time,str(theta),str(F(phase)))
            check(key+'/speed/'+time,str(omega),str(F(speed)))
            kinetic=inertia*(omega*omega-initial*initial)/2
            check(key+'/canonical-work-energy/'+time,str(kinetic-work),str(residual))
            half_cos=trig_enclosure(theta/2,False)
            half_sin=trig_enclosure(theta/2,True)
            full_cos=trig_enclosure(theta,False)
            full_sin=trig_enclosure(theta,True)
            oracle.append({'case':key,'time':time,'unwrapped_phase':str(theta),'signed_speed':str(omega),'rotational_work_j':str(work),'delta_kinetic_j':str(kinetic),'canonical_work_energy_residual_j':str(residual),'increment_quaternion_w':interval_data(half_cos),'increment_quaternion_axis':interval_data(half_sin),'quaternion_wxyz':full_quaternion(case,half_cos,half_sin),'full_cos':interval_data(full_cos),'full_sin':interval_data(full_sin),'axis':case['axis'],'marker_radius':case['marker_radius']})
    numerical=load('numerical-cases.json')
    for case in numerical['cases']:
        key=case['id']; kind=case['kind']
        if kind=='canonical-rounding':
            m=canonical(case['mass']); r=canonical(case['radius']); tau=canonical(case['torque'])
            inertia=F(float(F(2,5)*m*r*r)); alpha=F(float(tau/inertia)); dt=F(case['dt'])
            actual={'mass_hex':float(m).hex(),'radius_hex':float(r).hex(),'inertia_hex':float(inertia).hex(),'net_hex':float(tau).hex(),'alpha_hex':float(alpha).hex(),'speed_hex':float(alpha*dt).hex(),'phase_hex':float(alpha*dt*dt/2).hex()}
            check(key,actual,case['expected'])
            expected_shadow={'alpha_reference':str(tau/inertia),'alpha_canonical':str(alpha),'acceleration_error':str(abs(tau/inertia-alpha)),'speed_error_at_dt':str(abs(tau/inertia-alpha)*dt),'phase_error_at_dt':str(abs(tau/inertia-alpha)*dt*dt/2)}
            check(key+'/shadow',case['independent_shadow'],expected_shadow)
        elif kind=='canonical-sum':
            check(key,float(sum((canonical(x) for x in case['torque_sum_terms']),F(0))).hex(),case['expected_net_hex'])
        elif kind=='clock':
            end=canonical(case['start'])+canonical(case['duration'])
            check(key+'/end',str(end),case['expected_end_fraction'])
            check(key+'/different',end==canonical(case['separately_authored_time']),case['expected_equal'])
        elif kind=='anchor':
            p=F(float.fromhex(case['position_hex'])); v=F(float.fromhex(case['velocity_hex']))
            split=F(case['split']); end=F(case['end'])
            check(key+'/correct',float(p+v*end).hex(),case['expected_unsplit_hex'])
            check(key+'/forbidden',float(F(float(p+v*split))+v*(end-split)).hex(),case['forbidden_extra_anchor_hex'])
        elif kind=='recording-bound':
            alpha=abs(F(case['alpha'])); omega=max(abs(F(case['omega_start'])),abs(F(case['omega_end'])))
            h=F(case['width']); rho=F(case['rho'])
            check(key+'/angle',str(alpha*h*h/8),case['expected_phase_chord'])
            check(key+'/position',str(rho*(alpha+omega*omega)*h*h/8),case['expected_position_chord'])
        elif kind=='zero-crossing':
            check(key,str(-F(case['omega'])/F(case['alpha'])),case['expected_crossing'])
    for path in ('agent/repairs.json','agent/workflow-repairs.json'):
        repairs=load(path); base_name=repairs.get('base_fixture','agent-base')
        base=(ROOT/('sources/'+base_name+'.ok')).read_bytes()
        check('repair/'+base_name,identity(base_name),repairs['base_identity'])
        for item in repairs['repairs']:
            patch=item['patch']; actual=base[patch['start_byte']:patch['end_byte']]
            check(item['id']+'/old-bytes',actual.decode(),patch['expected_text'])
            result=base[:patch['start_byte']]+patch['replacement'].encode()+base[patch['end_byte']:]
            check(item['id']+'/new-bytes',sha(result),sha((ROOT/('sources/'+item['id']+'.ok')).read_bytes()))
            check(item['id']+'/new-identity',identity(item['id']),item['to'])
    state_data=load('state-expectations.json')
    for item in state_data['cases']:
        case=next(c for c in corpus['cases'] if c['id']==item['case']); key=case['id']
        inertia=F(float.fromhex(case['inertia_hex'])); raw=(ROOT/('sources/'+key+'.ok')).read_bytes()
        for record in item['source_records']:
            interval=next(t for t in case['torques'] if t['key']==record['torque_key'])
            check(key+'/record-id/'+interval['key'],record['torque_element_id'],['torque-cases','demo','torque',interval['key']])
            check(key+'/record-program/'+interval['key'],record['program_revision'],case['identity']['program_revision'])
            for field in ('source_location','operand_location','duration_location'):
                loc=record[field];value=raw[loc['start_byte']:loc['end_byte']].decode()
                check(key+'/'+interval['key']+'/'+field+'/nonempty',bool(value),True)
                check(key+'/'+interval['key']+'/'+field+'/revision',loc['source_revision'],sha(raw))
            check(key+'/exact-end/'+interval['key'],F(record['completion_time_seconds']),canonical(interval['start'])+canonical(interval['duration']))
        for observation in item['observations']:
            t=F(observation['time_seconds']);after=observation['side']=='after';actual=observation['exact_fields'];label=key+'/'+str(t)+'/'+observation['side']
            begins=lambda x:x<t or x==t and after
            active=[r for r in item['source_records'] if begins(F(r['activation_time_seconds'])) and not begins(F(r['completion_time_seconds']))]
            check(label+'/active',[r['torque_key'] for r in actual['active']],sorted(r['torque_key'] for r in active))
            total=sum((F(r['torque_n_m']) for r in active),F(0));net=canonical(total)
            check(label+'/net',float(actual['net_torque_n_m']).hex(),float(net).hex())
            started=sum(begins(F(r['activation_time_seconds'])) for r in item['source_records'])
            complete=sum(begins(F(r['completion_time_seconds'])) for r in item['source_records'])
            check(label+'/counts',[actual['started_count'],actual['completed_count']],[started,complete])
            first=case['expected_start_rotation'];split=first is not None and begins(F(first))
            check(label+'/route',actual['rotation_route'],'split' if split else 'legacy')
            if actual['axis'] is not None:
                check(label+'/alpha',float(actual['angular_acceleration_rad_per_s2']).hex(),float(canonical(net/inertia)).hex())
                ref=actual['angular_acceleration_reference_rad_per_s2']
                check(label+'/reference',F(int(ref['numerator']),int(ref['denominator'])),total/inertia)
            if split:
                anchor=F(actual['rotation_anchor_seconds']);theta,_,_,_=scalar_reference(case,t);origin,_,_,_=scalar_reference(case,anchor)
                check(label+'/retained-anchor-phase',float(actual['phase_since_anchor_rad']).hex(),float(theta-origin).hex())
            # Literal table gives an independent speed authority; before-zero
            # impulse is intentionally different from its after-zero sample.
            sample=next((s for s in case['samples'] if F(s[0])==t),None)
            if sample and actual['axis'] is not None:
                check(label+'/literal-speed',float(actual['signed_angular_speed_rad_per_s']).hex(),float(F(sample[2])).hex())
    for dataset in ('refusal-cases.json','evaluation-domain-cases.json','delivery-cases.json','delivery-refusals.json','language-cases.json'):
        for case in load(dataset)['cases']:
            check(dataset+'/'+case['id']+'/identity',identity(case['file_manifest'].removesuffix('.files.json')),case['identity'])
    domains=load('evaluation-domain-cases.json')['cases']
    for case in domains:
        if case['id'] in ('domain02-underflow-long-prefix','domain03-reference-origin-transfer'):
            t=F(case['time_seconds']);stop=F(case['reference_origin_changes_at'] or case['time_seconds']);a=F(1,2**1075)
            check(case['id']+'/phase',str(a*stop**2/2+a*stop*(t-stop)),case['exact_reference_phase'])
            check(case['id']+'/speed',str(a*stop),case['exact_reference_speed'])
            check(case['id']+'/canonical-alpha',float(a).hex(),'0x0.0p+0')
    check('phase-cap-equality',2**21//2,2**20)
    check('interior-vertex-refusal',F(2097154)-F(2097154,2),F(2**20+1))
    comparison=load('comparisons.json')
    check('six-comparison-classes',[c['id'] for c in comparison['classes']],['C1','C2','C3','C4','C5','C6'])
    resource=load('agent/resource-cases.json')
    check('source-runtime-recording-stage-count',len(resource['cases']),17)
    check('reference-origin-stage','torque_reference_origin' in [r['stage'] for r in resource['cases']],True)
    check('fixed-source-budget',load('delivery-cases.json')['allocation_decision']['source_operations'],1000000)
    # Hash every original compressed member as bytes, not a decoded projection.
    import zipfile
    archives=load('predecessor/ARCHIVES.json')
    for archive in archives['archives']:
        path=ROOT/'predecessor'/archive['archive'];check('archive/'+archive['archive'],sha(path.read_bytes()),archive['sha256'])
        with zipfile.ZipFile(path) as z:
            check('archive/'+archive['archive']+'/members',sorted(z.namelist()),sorted(m['path'] for m in archive['members']))
            for member in archive['members']:
                info=z.getinfo(member['path']);data=z.read(info)
                check('archive/'+archive['archive']+'/'+member['path'],[len(data),sha(data),oct((info.external_attr>>16)&0o777)],[member['bytes'],member['sha256'],'0o644'])
    success=all(row['passed'] for row in rows)
    report={'schema_version':'ontokin.torque-independent-input-check/1','status':'passed' if success else 'failed','assertions':len(rows),'failures':[r for r in rows if not r['passed']],'python':sys.version,'platform':platform.platform(),'script_sha256':sha(Path(__file__).read_bytes()),'production_imported':False,'candidate_output_used':False,'runtime_validation_performed':False,'rows':rows,'trigonometric_reference':oracle,'reference_method':'Exact rational polynomial degree 180 with Lagrange remainder |x|^181/181!, outward decimal display at 60 significant digits; |x|<=16'}
    args.report.parent.mkdir(parents=True,exist_ok=True)
    with args.report.open('x') as stream:
        json.dump(report,stream,indent=2,sort_keys=True,default=str);stream.write('\n')
    print(json.dumps({'status':report['status'],'assertions':len(rows),'failures':len(report['failures']),'reference_samples':len(oracle)}))
    return 0 if success else 1


if __name__=='__main__':
    raise SystemExit(main())
