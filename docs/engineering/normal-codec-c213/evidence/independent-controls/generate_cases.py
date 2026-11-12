#!/usr/bin/env python3
"""Predeclare finite boundary inputs without importing the C213 implementation."""
from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parent

def f32(x):
    return struct.unpack('<f', struct.pack('<f', float(x)))[0]

def bits(x):
    return struct.unpack('<I', struct.pack('<f', float(x)))[0]

def from_bits(x):
    return struct.unpack('<f', struct.pack('<I', x))[0]

def neighbor(x, direction):
    x = f32(x)
    return from_bits(bits(x) + direction * (1 if x >= 0 else -1))

def dot32(v, w):
    return f32(f32(f32(v[0]*w[0])+f32(v[1]*w[1]))+f32(v[2]*w[2]))

def q32(x):
    return math.floor(f32(f32(f32(x)*f32(32767))+f32(0.5)))

frames = {
 'canonical': {'lnor':[0,0,1], 'ref':[1,0,0], 'ortho':[0,1,0], 'alpha':math.pi/2, 'beta':math.pi},
 'rotated': {'lnor':[1,0,0], 'ref':[0,1,0], 'ortho':[0,0,1], 'alpha':math.pi/3, 'beta':math.pi/2},
 'oblique': {'lnor':[0.6,0,0.8], 'ref':[0.8,0,-0.6], 'ortho':[0,1,0], 'alpha':2*math.pi/3, 'beta':3*math.pi/2},
 'full_beta': {'lnor':[0,0,1], 'ref':[1,0,0], 'ortho':[0,1,0], 'alpha':math.pi/2, 'beta':2*math.pi},
}
cases=[]
expect={}

def add(identifier, family, expected='accepted', **case):
    row={'id':identifier, **case}
    cases.append(row)
    expect[identifier]={'family':family,'status':expected}
    return expect[identifier]

def rt(identifier, family, normal, frame='canonical', mode='unit', **kw):
    return add(identifier,family,operation='roundtrip',frame=copy.deepcopy(frames[frame]),normal=normal,mode=mode,**kw)

def direction(frame, polar, azimuth):
    f=frames[frame]
    return [math.cos(polar)*f['lnor'][i]+math.sin(polar)*(math.cos(azimuth)*f['ref'][i]+math.sin(azimuth)*f['ortho'][i]) for i in range(3)]

for frame in ('canonical','rotated','oblique'):
    f=frames[frame]
    for name,v in [('auto',f['lnor']),('anti_auto',[-x for x in f['lnor']]),('ref',f['ref']),('anti_ref',[-x for x in f['ref']]),('ortho',f['ortho']),('anti_ortho',[-x for x in f['ortho']])]:
        e=rt(f'{frame}_{name}','cardinal',v,frame)
        if name=='auto': e['encoded']=[0,0]
    for j,(p,b) in enumerate([(0.7,0.8),(1.9,2.3),(2.7,5.2),(0.4,5.9),(2.9,0.4)]):
        rt(f'{frame}_oblique_{j}','oblique',direction(frame,p,b),frame)

for frame in ('canonical','rotated','full_beta'):
    for j,(p,b) in enumerate([(math.pi/2,0.01),(1.0,0.01),(math.pi/2,2*math.pi-0.01),(1.0,2*math.pi-0.01)]):
        e=rt(f'{frame}_shortcut_{j}','azimuth_shortcut_counterexample',direction(frame,p,b),frame)
        e['azimuthShortcut']=True
        e['minimumComponentError']=0.004
        e['encodedBeta']=0

t=f32(1e-4)
for sign in (1,-1):
    for name,x in [('below',neighbor(t,-1)),('at',t),('above',neighbor(t,1)),('twice',f32(t*2))]:
        e=rt(f'near_auto_{sign}_{name}','near_auto_boundary',[sign*x,0,math.sqrt(1-x*x)])
        e['nearAuto']=name in ('below','at')
        if name in ('below','at'):e['encoded']=[0,0]
        e['minimumComponentError']=2e-6
e=rt('near_auto_component_cube','near_auto_component_cube',[9e-5,9e-5,math.sqrt(1-2*(9e-5)**2)])
e.update(nearAuto=True,encoded=[0,0],minimumComponentError=8e-5)

threshold=f32(f32(1)-f32(1e-4))
for offset in (-2,-1,0,1,2):
    x=from_bits(bits(threshold)+offset)
    y=f32(math.sqrt(max(0,1-x*x)))
    for sign in (1,-1):
        e=rt(f'azimuth_cos_{offset}_{sign}','azimuth_threshold',[x,sign*y,0])
        d=dot32([x,y,0],[x,y,0])
        norm=f32(math.sqrt(d))
        projected_x=f32(x/norm)
        e['expectedProjectedCosBeta']=projected_x
        e['azimuthShortcut']=projected_x>=threshold
        if projected_x>=threshold:e['encodedBeta']=0

for k in (0,1,2,127,16382,32766):
    for sign in (1,-1):
        midpoint=f32(sign*(k+0.5)/32767)
        for label,value in [('below',neighbor(midpoint,-1)),('at',midpoint),('above',neighbor(midpoint,1))]:
            e=add(f'q_{sign}_{k}_{label}','signed_rounding_boundary',operation='quantize',value=value)
            e['encoded']=q32(value)
for name,value in [('neg_one',-1),('zero',0),('pos_one',1),('neg_zero',-0.0)]:
    e=add('q_'+name,'signed_rounding_endpoint',operation='quantize',value=value)
    e['encoded']=q32(value)
for name,value in [('too_low',-1.0001),('too_high',1.0001),('nan','NaN'),('infinity','Infinity')]:
    add('q_reject_'+name,'quantize_refusal','rejected',operation='quantize',value=value)

for a in (-32767,-16384,-1,0,1,16384,32767):
    for b in (-32767,-16384,-1,0,1,16384,32767):
        add(f'decode_{a}_{b}','decoder_signed_grid',operation='decode',frame=copy.deepcopy(frames['canonical']),shorts=[a,b])
for field in ('alpha','beta'):
    f=copy.deepcopy(frames['canonical']);f[field]=0
    add('decode_raw_zero_'+field,'upstream_invalid_range_fallback',operation='decode',frame=f,shorts=[123,456],mode='invalid-range-fallback')
    add('decode_refuse_zero_'+field,'strict_invalid_range_refusal','rejected',operation='decode',frame=f,shorts=[123,456])
for name,shorts in [('below',[-32768,1]),('above',[1,32768]),('noninteger',[1.5,2])]:
    add('decode_refuse_'+name,'decoder_refusal','rejected',operation='decode',frame=copy.deepcopy(frames['canonical']),shorts=shorts)

for name,value in [('below_neg_one',-1.00001),('neg_one',-1),('neg_near_one',-0.9999),('neg_half',-.5),('neg_tiny',-1e-40),('neg_zero',-0.0),('zero',0),('tiny',1e-40),('half',.5),('near_one',.9999),('one',1),('above_one',1.00001)]:
    add('acos_'+name,'approximate_acos',operation='acos',value=value)
for name,value in [('nan','NaN'),('inf','Infinity'),('neg_inf','-Infinity')]:
    add('acos_refuse_'+name,'acos_nonfinite_refusal','rejected',operation='acos',value=value)

normalization_inputs=[('zero',[0,0,0]),('ordinary',[2,3,4]),('negative',[-2,-3,-4]),('tiny',[1e-30,0,0]),('large',[1e30,0,0])]
length_mid=f32(math.sqrt(f32(1e-35)))
for name,x in [('below',neighbor(length_mid,-1)),('at',length_mid),('above',neighbor(length_mid,1))]:
    normalization_inputs.append(('cutoff_'+name,[x,0,0]))
for name,v in normalization_inputs:
    add('normalize_'+name,'normalization',operation='normalize',normal=v)
for name,v in [('ordinary',[2,3,4]),('negative',[-2,-3,-4]),('tiny',[1e-30,0,0]),('large',[1e30,0,0]),('zero',[0,0,0]),('nan',['NaN',0,1]),('inf',[0,'Infinity',1])]:
    status='rejected' if name in ('tiny','large','zero','nan','inf') else 'accepted'
    add('strict_normal_'+name,'strict_normal_input',status,operation='roundtrip',frame=copy.deepcopy(frames['canonical']),normal=v)
add('unit_refuse_nonunit','unit_input_refusal','rejected',operation='roundtrip',mode='unit',frame=copy.deepcopy(frames['canonical']),normal=[0,0,2])
e=add('raw_zero_sentinel','upstream_zero_sentinel',operation='roundtrip',mode='zero-sentinel',frame=copy.deepcopy(frames['canonical']),normal=[0,0,0]);e['encoded']=[0,0]

invalids={}
for name,key,value in [('alpha_zero','alpha',0),('alpha_negative','alpha',-.1),('alpha_large','alpha',math.pi+.01),('alpha_nonfinite','alpha','NaN'),('beta_zero','beta',0),('beta_negative','beta',-.1),('beta_large','beta',2*math.pi+.01),('beta_nonfinite','beta','Infinity'),('zero_lnor','lnor',[0,0,0]),('nonunit_ref','ref',[2,0,0]),('nonorthogonal','ref',[0.8,0,0.6]),('left_handed','ortho',[0,-1,0]),('nonfinite_basis','ortho',[0,'NaN',0])]:
    f=copy.deepcopy(frames['canonical']);f[key]=value;invalids[name]=f
for name,f in invalids.items():
    add('frame_refuse_'+name,'frame_refusal','rejected',operation='roundtrip',frame=f,normal=[1,0,0])

for name,v in [('face_a',[1,0,0]),('face_b',[0,1,0]),('face_c',[-1,0,0])]:
    rt('sharp_'+name,'distinct_sharp_boundary_corners',v)

metadata={
 'schema':'ontokin.c213.independent-cases/0.1',
 'scope':'Finite explicit-frame boundary characterization; never native fan reconstruction or a universal approximation budget',
 'sourceCommit':'32f5fdce0a0a571a39198edf8d7b5d719bf59f2c',
 'implementationReadBeforePredeclaration':False,
 'nativeExecution':False,
 'caseCount':len(cases),
 'frames':frames,
 'cases':cases,
}
(ROOT/'cases.json').write_text(json.dumps(metadata,indent=2,allow_nan=False)+'\n')
(ROOT/'expectations.json').write_text(json.dumps({'schema':'ontokin.c213.independent-expectations/0.1','cases':expect,'referenceRules':{
 'quantize':'float32 input, float32 multiply by 32767, float32 +0.5, mathematical floor; each stage rounded independently by Python struct',
 'nearAuto':'Pinned compare_ff uses <= on every component independently; mode unit prevents extra input normalization',
 'azimuth':'Pinned scalar threshold float32(1-float32(1e-4)); expected projected cosine computed from explicit canonical frame with float32 dot and norm',
 'decode':'Compare to independent double precision spherical reconstruction of returned shorts, with explicit per-output finite floating-point allowance; this is a mathematical reference, not a native binary oracle',
 'error':'Recompute component error, direction angle and unit drift from returned input/output vectors; a counterexample passes the investigation by failing the original 2e-6 preservation promise',
 'nativeBoundary':'Supplied basis/ranges do not prove Blender fan construction reaches them; no native fan values or encoded C211 shorts are invented',
}},indent=2,allow_nan=False)+'\n')
print(json.dumps({'caseCount':len(cases),'families':sorted(set(x['family'] for x in expect.values()))}))
