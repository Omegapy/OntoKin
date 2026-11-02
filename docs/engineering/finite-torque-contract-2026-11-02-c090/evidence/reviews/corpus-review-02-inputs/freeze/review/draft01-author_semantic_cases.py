#!/usr/bin/env python3
"""Author source refusals and exact ordered-boundary inputs independently."""
from __future__ import annotations
from copy import deepcopy
from fractions import Fraction as F
from pathlib import Path
import json

from author_inputs import ROOT, CASES, source, write, manifest, identities, span, tor


def main():
    base=source(CASES[0])
    original='torque ball @ "drive" about world_z using 2[N*m] for 2[s];'
    records=[]
    def add(name,text,condition,code,phase,location,**extra):
        write('sources/'+name+'.ok',text)
        write(name+'.files.json',manifest(name))
        location_record=span(text,location) if location else None
        records.append({'id':name,'file_manifest':name+'.files.json','identity':identities(name),'condition':condition,'expected':{'outcome':'refused','code':code,'phase':phase,'primary_source':location_record,**extra},'candidate_observations_used':False})
    add('n01-force-unit',base.replace('using 2[N*m]','using 2[N]'),'Force is not Torque','OKL-E-TYPE','type','2[N]')
    add('n02-zero-duration',base.replace('for 2[s]','for 0[s]'),'Duration must be strictly positive','OKL-E-EVENT-ORDER','validation','0[s]')
    add('n03-negative-duration',base.replace('for 2[s]','for -1[s]'),'Duration must be strictly positive','OKL-E-EVENT-ORDER','validation','-1[s]')
    add('n04-unknown-axis',base.replace('about world_z','about world_q'),'Only the three literal Cartesian axis tokens are admitted','OKL-E-SYNTAX','parse','world_q')
    add('n05-axis-expression',base.replace('about world_z','about vector(world, 0, 0, 1)'),'The axis slot is not an arbitrary expression','OKL-E-SYNTAX','parse','vector(world, 0, 0, 1)')
    add('n06-unresolved-target',base.replace('torque ball @','torque missing @'),'The target must resolve','OKL-E-NAME','resolve','missing')
    add('n07-prescribed-target',base.replace('    object ball @ "ball": rotors.Rotor {','    object ball @ "ball": rotors.Rotor {\n        motion = prescribed;'),'Torque does not change motion mode','OKL-E-MOTION-MODE','admission',original,boundary_seconds='0',accepted_prefix='before 0')
    add('n08-zero-mass',base.replace('body_mass = 2.5[kg]','body_mass = 0[kg]'),'Inherited sphere mass admission remains mandatory','OKL-E-PHYSICAL-DOMAIN','construction','0[kg]',diagnostic_authority='Inherited sphere_body diagnostic; effective constructor and parameter origin must both remain available')
    add('n09-zero-radius',base.replace('body_radius = 1[m]','body_radius = 0[m]'),'Inherited sphere radius admission remains mandatory','OKL-E-PHYSICAL-DOMAIN','construction','0[m]',diagnostic_authority='Inherited sphere_body diagnostic; effective constructor and parameter origin must both remain available')
    add('n10-property-target',base.replace('torque ball @','torque ball.body_mass @'),'A scalar property is not an object occurrence','OKL-E-TYPE','type','ball.body_mass')
    change=source({'id':'change','torques':[tor('neutral',0,'1/2',0),tor('drive',1,1,1,'world_x')]})
    stmt='torque ball @ "drive" about world_x using 1[N*m] for 1[s];'
    add('n11-empty-set-axis-change',change,'The first axis survives interval completion','OKL-E-FRAME','admission',stmt,boundary_seconds='1',accepted_prefix='before 1',expected_axis_before='world_z')
    mixed=source({'id':'mixed','torques':[tor('first',0,1,0,'world_x'),tor('second',0,1,0,'world_y')]})
    add('n12-zero-mixed-axes',mixed,'Each interval must name the already staged axis, even with zero net torque','OKL-E-FRAME','admission','torque ball @ "second" about world_y using 0[N*m] for 1[s];',boundary_seconds='0',accepted_prefix='before 0',whole_boundary_rollback=True)
    off=base.replace('omega = vector(world, 0[rad/s], 0[rad/s], 0[rad/s]);','omega = vector(world, 1[rad/s], 0[rad/s], 0[rad/s]);')
    add('n13-incoming-off-axis-spin',off,'Incoming canonical orthogonal components must be exactly zero','OKL-E-FRAME','admission',original,boundary_seconds='0',accepted_prefix='before 0')
    first='impulse ball using vector(world, 0[N*s], 0[N*s], 1[N*s]) at point(ball.frame, 1[m], 0[m], 0[m]);'
    inverse='impulse ball using vector(world, 0[N*s], 0[N*s], -1[N*s]) at point(ball.frame, 1[m], 0[m], 0[m]);'
    bad=base.replace(original,'torque ball @ "drive" about world_z using 0[N*m] for 2[s];\n        '+first+'\n        '+inverse)
    add('n14-intermediate-off-axis-impulse',bad,'An inverse later impulse cannot hide an off-axis intermediate state','OKL-E-FRAME','admission',first,boundary_seconds='0',accepted_prefix='before 0',whole_boundary_rollback=True,forbidden_effects=['axis latch','first impulse','second impulse','torque activation count'])
    overflow=source({'id':'over','torques':[tor('a',0,1,'1e308'),tor('b',0,1,'1e308')]})
    add('n15-net-overflow',overflow,'Final exact aggregate is not a finite binary64 net','OKL-E-NUMERIC','evaluation','torque ball @ "a" about world_z using 1e308[N*m] for 1[s];',boundary_seconds='0',accepted_prefix='before 0',whole_boundary_rollback=True,operation='net_torque')
    acceleration=source({'id':'over','mass':'5','radius':'1/2','torques':[tor('a',0,1,'1e308')]})
    add('n16-alpha-overflow',acceleration,'Finite net torque divided by canonical inertia has nonfinite final alpha','OKL-E-NUMERIC','evaluation','torque ball @ "a" about world_z using 1e308[N*m] for 1[s];',boundary_seconds='0',accepted_prefix='before 0',operation='angular_acceleration')
    future=source({'id':'future','torques':[tor('later',1,1,'1e308')]})
    add('n17-later-bounded-phase',future,'A requested later segment exceeds the adopted phase domain; an earlier valid prefix stays valid','OKL-E-NUMERIC','evaluation','torque ball @ "later" about world_z using 1e308[N*m] for 1[s];',successful_prefix_seconds='0.5',failed_request_seconds='2',last_successful_run_preserved=True,operation='phase_domain')
    duplicate=source({'id':'dup','torques':[tor('same',0,1,1),tor('same',1,1,1)]})
    add('n18-duplicate-key',duplicate,'Stable torque keys are unique across the whole entry scene','OKL-E-NAME','resolve','torque ball @ "same" about world_z using 1[N*m] for 1[s];',required_related='earlier torque with key same',primary_occurrence=1)
    records[-1]['expected']['primary_source']=span(duplicate,'torque ball @ "same" about world_z using 1[N*m] for 1[s];',1)
    old=base.replace('"0.22"','"0.21"',1).replace('profile "torque-0.1"','profile "keyed-membership-0.1"',1)
    add('n19-earlier-profile',old,'Older declaring profiles do not acquire torque syntax or semantics','OKL-E-CAPABILITY-UNSUPPORTED','support',original)
    wrongangle=base.replace('using 2[N*m]','using 2[N*m/rad]')
    add('n20-angle-dimension',wrongangle,'Operation-specific mechanical conversion does not erase the distinct Angle dimension','OKL-E-TYPE','type','2[N*m/rad]')
    add('n21-duration-units',base.replace('for 2[s]','for 1[m]'),'Duration has Time type','OKL-E-TYPE','type','1[m]')
    add('n22-boolean-torque',base.replace('using 2[N*m]','using true'),'Bool does not coerce to Torque','OKL-E-TYPE','type','true')
    locked=base.replace(original,'torque ball.label @ "drive" about world_z using 2[N*m] for 2[s];')
    add('n23-followed-marker',locked,'A followed massless marker is not a free dynamic body','OKL-E-MOTION-MODE','admission','torque ball.label @ "drive" about world_z using 2[N*m] for 2[s];',boundary_seconds='0',accepted_prefix='before 0')
    release=source(next(c for c in CASES if c['id']=='p28-release-then-torque'))
    release=release.replace('        release hold using incoming;\n        torque ball @ "drive" about world_z using 1[N*m] for 1[s];','        torque ball @ "drive" about world_z using 1[N*m] for 1[s];\n        release hold using incoming;')
    add('n24-torque-before-release',release,'Only an earlier staged release can make the sphere free','OKL-E-MOTION-MODE','admission','torque ball @ "drive" about world_z using 1[N*m] for 1[s];',boundary_seconds='1',accepted_prefix='before 1',whole_boundary_rollback=True)
    clock=source({'id':'collapse','horizon':'1/2','torques':[tor('drive','0.1','0.2',1),tor('near','0.3','0.1',0)]})
    add('n25-delivery-clock-collapse',clock,'Distinct mandatory exact source boundaries collapse in binary32 recording clocks','OKL-E-EXPORT','delivery',None,expected_compile='accepted',expected_evaluation='accepted',requested_output='ontokin.glb/0.22',near_clock='0.3',completion_fraction='10808639105689191/36028797018963968',permit_boundary_drop=False)
    write('refusal-cases.json',{'schema_version':'ontokin.torque-independent-refusals/1','state':'Review input; bind exact diagnostic wording and schema in the independently reviewed contract before adoption','candidate_observations_used':False,'cases':records})


if __name__=='__main__':
    main()
