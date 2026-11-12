#!/usr/bin/env python3
"""Independent finite assertions; never imports the worker implementation."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT=Path(__file__).resolve().parent

def f32(x):
    try:return struct.unpack('<f',struct.pack('<f',float(x)))[0]
    except OverflowError:return math.copysign(math.inf,float(x))

def dot32(a,b):
    return f32(f32(f32(a[0]*b[0])+f32(a[1]*b[1]))+f32(a[2]*b[2]))

def norm_ref(v):
    v=[f32(x) for x in v]
    d=dot32(v,v)
    if not d>f32(1e-35):return [0.,0.,0.]
    length=f32(math.sqrt(d))
    return [f32(x/length) for x in v]

def spherical_ref(frame,shorts):
    n,r,o=([f32(x) for x in frame[k]] for k in ('lnor','ref','ortho'))
    ra,rb=f32(frame['alpha']),f32(frame['beta'])
    if shorts[0]==0 or ra==0 or rb==0:return n
    u,v=shorts[0]/32767,shorts[1]/32767
    a=(ra if u>0 else f32(2*math.pi)-ra)*u
    b=(rb if v>0 else f32(2*math.pi)-rb)*v
    return [math.cos(a)*n[i]+math.sin(a)*(math.cos(b)*r[i]+math.sin(b)*o[i]) for i in range(3)]

def angle(a,b):
    la=math.sqrt(sum(x*x for x in a));lb=math.sqrt(sum(x*x for x in b))
    if not la or not lb:return None
    aa=[x/la for x in a];bb=[x/lb for x in b]
    cross=[aa[1]*bb[2]-aa[2]*bb[1],aa[2]*bb[0]-aa[0]*bb[2],aa[0]*bb[1]-aa[1]*bb[0]]
    return math.atan2(math.sqrt(sum(x*x for x in cross)),sum(x*y for x,y in zip(aa,bb)))

def rows_of(report):
    if isinstance(report,list):return report
    for key in ('results','cases','observations','rows'):
        if isinstance(report.get(key),list):return report[key]
    raise ValueError('No result rows')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('result');ap.add_argument('--output',required=True);args=ap.parse_args()
    corpus=json.loads((ROOT/'cases.json').read_text());expect=json.loads((ROOT/'expectations.json').read_text())['cases']
    report=json.loads(Path(args.result).read_text());rows=rows_of(report)
    checks=[];observations=[]
    def check(name,passed,detail=None):
        checks.append({'name':name,'passed':bool(passed),**({'detail':detail} if detail is not None else {})})
    ids=[r.get('id') for r in rows]
    check('exact_case_identity_set',set(ids)==set(expect) and len(ids)==len(expect),{'expected':len(expect),'actual':len(ids)})
    check('unique_case_identities',len(ids)==len(set(ids)))
    index={r['id']:r for r in rows}
    for case in corpus['cases']:
        cid=case['id'];e=expect[cid];r=index.get(cid)
        if r is None:continue
        check(cid+':status',r.get('status')==e['status'],{'expected':e['status'],'actual':r.get('status')})
        if r.get('status')!='accepted':
            check(cid+':refusal_reason',bool(r.get('reason')))
            continue
        op=case['operation'];trace=r.get('trace',{})
        if 'encoded' in e:check(cid+':encoding',r.get('encoded')==e['encoded'],{'expected':e['encoded'],'actual':r.get('encoded')})
        if 'encodedBeta' in e:check(cid+':zero_azimuth',r.get('encoded',[None,None])[1]==e['encodedBeta'])
        for key in ('nearAuto','azimuthShortcut'):
            if key in e:check(cid+':'+key,trace.get(key)==e[key],{'expected':e[key],'actual':trace.get(key)})
        if op=='quantize':
            x=f32(case['value']);q=math.floor(f32(f32(x*f32(32767))+f32(.5)))
            check(cid+':independent_quantizer',r.get('encoded')==q)
        elif op=='acos':
            x=f32(case['value']);exact=math.acos(max(-1.,min(1.,x)))
            v=r.get('approximate',r.get('value',r.get('acosApprox')))
            if isinstance(v,(int,float)):
                check(cid+':documented_approximation_scale',abs(v-exact)<=4.6e-5,{'absoluteError':abs(v-exact)})
                observations.append({'id':cid,'family':e['family'],'acosAbsoluteError':abs(v-exact)})
            else:check(cid+':numeric_acos',False,{'keys':sorted(r)})
        elif op=='normalize':
            v=r.get('normalized',r.get('normalizedInput'))
            expected=norm_ref(case['normal'])
            check(cid+':upstream_normalization',isinstance(v,list) and len(v)==3 and max(abs(x-y) for x,y in zip(v,expected))<=1e-7,{'expected':expected,'actual':v})
        elif op in ('decode','roundtrip'):
            v=r.get('decoded');shorts=case.get('shorts') if op=='decode' else r.get('encoded')
            check(cid+':decoded_finite',isinstance(v,list) and len(v)==3 and all(isinstance(x,(int,float)) and math.isfinite(x) for x in v))
            if not isinstance(v,list) or len(v)!=3:continue
            ref=spherical_ref(case['frame'],shorts)
            oracle_diff=max(abs(x-y) for x,y in zip(v,ref))
            check(cid+':independent_spherical_decoder',oracle_diff<=1e-6,{'maximumComponentDifference':oracle_diff,'reference':ref})
            drift=abs(math.sqrt(sum(x*x for x in v))-1)
            check(cid+':finite_unit_drift',drift<=3e-6,{'drift':drift})
            o={'id':cid,'family':e['family'],'encoded':shorts,'decoded':v,'decoderReferenceDifference':oracle_diff,'unitLengthDrift':drift}
            if op=='roundtrip' and case.get('mode')!='zero-sentinel':
                target=[f32(x) for x in case['normal']] if case.get('mode')=='unit' else norm_ref(case['normal'])
                error=max(abs(x-y) for x,y in zip(target,v));ang=angle(target,v)
                o.update(maximumComponentError=error,angularErrorRadians=ang,originalStrictGateFailed=error>2e-6)
                if 'minimumComponentError' in e:check(cid+':declared_counterexample',error>=e['minimumComponentError'],{'observed':error,'declaredMinimum':e['minimumComponentError']})
                metrics=r.get('metrics',{})
                check(cid+':independent_component_metric',abs(metrics.get('maxComponentError',math.inf)-error)<=1e-12,{'independent':error,'reported':metrics.get('maxComponentError')})
                if ang is not None:check(cid+':independent_angular_metric',abs(metrics.get('angularErrorRadians',math.inf)-ang)<=1e-8,{'independent':ang,'reported':metrics.get('angularErrorRadians')})
            observations.append(o)
    sharp=[index[cid].get('decoded') for cid in ('sharp_face_a','sharp_face_b','sharp_face_c')]
    check('sharp_boundary_distinct_corner_outputs',all(math.sqrt(sum((x-y)**2 for x,y in zip(sharp[i],sharp[j])))>1 for i in range(3) for j in range(i)))
    seal=json.loads((ROOT/'PREDECLARATION.json').read_text())
    for rel,binding in seal['files'].items():
        check('predeclaration_unchanged:'+rel,hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==binding['sha256'])
    result={'schema':'ontokin.c213.independent-control-result/0.1','passed':all(c['passed'] for c in checks),'caseCount':len(corpus['cases']),'checkCount':len(checks),'failedChecks':[c for c in checks if not c['passed']],'acceptedRows':sum(r.get('status')=='accepted' for r in rows),'rejectedRows':sum(r.get('status')=='rejected' for r in rows),'families':dict(Counter(e['family'] for e in expect.values())),'inputSha256':hashlib.sha256((ROOT/'cases.json').read_bytes()).hexdigest(),'resultSha256':hashlib.sha256(Path(args.result).read_bytes()).hexdigest(),'checks':checks,'observations':observations,'limitations':['Finite explicit-frame controls only; no reconstruction of native fan construction or fan averaging','Approximation-scale and independent mathematical decoder allowances are harness checks, not a replacement receiving tolerance','No Blender process or full product regression is executed','Installed C211 binary/source lineage and native frame/short values remain unknown']}
    Path(args.output).write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('passed','caseCount','checkCount','acceptedRows','rejectedRows','failedChecks')}))
    raise SystemExit(0 if result['passed'] else 1)

if __name__=='__main__':main()
