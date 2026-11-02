#!/usr/bin/env python3
"""Author source refusals and exact ordered-boundary inputs independently."""
from __future__ import annotations
from copy import deepcopy
from fractions import Fraction as F
from pathlib import Path
import json
import re

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

    vertex=source({'id':'vertex','horizon':'2','omega':'2097154','torques':[tor('brake',0,2,'-2097154')]})
    add('n26-interior-phase-domain',vertex,'Endpoint phases are zero but the interior vertex exceeds the new split-only phase cap','OKL-E-NUMERIC','evaluation','torque ball @ "brake" about world_z using -2097154[N*m] for 2[s];',successful_prefix_seconds='0.25',failed_request_seconds='2',last_successful_run_preserved=True,operation='phase_domain',exact_phase_at_0='0',exact_phase_at_1='1048577',exact_phase_at_2='0',phase_limit='1048576')
    add('n27-torque-type-before-duration-child',base.replace('using 2[N*m] for 2[s]','using 2[N] for (1[s] / 0)'), 'Torque expression and its type check precede evaluation of the failing duration child','OKL-E-TYPE','type','2[N]',forbidden_diagnostic='Division by zero in the unevaluated duration')
    add('n28-torque-child-before-duration-type',base.replace('using 2[N*m] for 2[s]','using (2[N*m] / 0) for 1[m]'),'Inherited failing torque child precedes the duration signature error','OKL-E-NUMERIC','elaboration','2[N*m] / 0',message='Division by zero.',diagnostic_authority='Untouched ontokin/values.py arithmetic constructor; original binary expression span excludes its grouping parentheses',forbidden_diagnostic='A torque interval requires a Time duration.')
    add('n29-axis-before-nonpositive-duration',base.replace('about world_z using 2[N*m] for 2[s]','about world_q using 2[N*m] for 0[s]'),'After both expression type checks, axis admission precedes positive-duration admission','OKL-E-FRAME','compile','world_q',forbidden_diagnostic='A torque interval requires a strictly positive duration.')
    add('n30-duration-type-before-axis',base.replace('about world_z using 2[N*m] for 2[s]','about world_q using 2[N*m] for 1[m]'),'Duration type admission precedes axis spelling','OKL-E-TYPE','type','1[m]',forbidden_diagnostic='A torque axis must be world_x, world_y or world_z.')

    # Contract review amendment 01 selects diagnostics before any candidate
    # torque implementation. The preceding draft is retained under review/.
    messages={
      'operand_type':('OKL-E-TYPE','type','A torque interval requires a scalar Torque value.'),
      'duration_type':('OKL-E-TYPE','type','A torque interval requires a Time duration.'),
      'axis_name':('OKL-E-FRAME','compile','A torque axis must be world_x, world_y or world_z.'),
      'duration_nonpositive':('OKL-E-EVENT-ORDER','compile','A torque interval requires a strictly positive duration.'),
      'duplicate_key':('OKL-E-NAME','compile','Torque interval keys must be unique within the entry scene.'),
      'target_mode':('OKL-E-MOTION-MODE','admission','A torque requires a currently free dynamic sphere.'),
      'axis_lock':('OKL-E-FRAME','admission',"A torque interval must use the carrier's latched world axis."),
      'incoming_axis':('OKL-E-FRAME','admission','Angular velocity must lie on the selected torque axis.'),
      'impulse_axis':('OKL-E-FRAME','admission',"An impulse must preserve the carrier's latched torque axis."),
      'net_overflow':('OKL-E-NUMERIC','evaluation','A canonical torque result exceeds the finite binary64 domain.'),
      'acceleration_overflow':('OKL-E-NUMERIC','evaluation','A canonical torque result exceeds the finite binary64 domain.'),
      'phase_domain':('OKL-E-NUMERIC','evaluation','A torque rotation segment exceeds the supported phase domain.')}
    reasons={1:'operand_type',2:'duration_nonpositive',3:'duration_nonpositive',4:'axis_name',7:'target_mode',11:'axis_lock',12:'axis_lock',13:'incoming_axis',14:'impulse_axis',15:'net_overflow',16:'acceleration_overflow',17:'phase_domain',18:'duplicate_key',20:'operand_type',21:'duration_type',22:'operand_type',23:'target_mode',24:'target_mode',26:'phase_domain',27:'operand_type',29:'axis_name',30:'duration_type'}
    for item in records:
        number=int(item['id'][1:3]); expected=item['expected']; text=(ROOT/('sources/'+item['id']+'.ok')).read_text()
        if number in reasons:
            reason=reasons[number]; code,phase,message=messages[reason]
            expected.update(code=code,phase=phase,message=message,torque_reason=reason)
            old=expected['primary_source']
            if reason!='impulse_axis':
                statements=list(re.finditer(r'torque\s+[^;]+;',text))
                # Duration literals can also occur in scene.duration. The
                # amended primary is selected from the actual event statement.
                candidates=[s for s in statements if s.start()<=old['start_byte']<s.end()]
                chosen=candidates[0] if candidates else next(s for s in statements if old['text'] in s.group())
                expected['primary_source']=span(text,chosen.group(),1 if number==18 else 0)
                # Immutable details are complete before any runtime exists.
                parsed=re.match(r'torque\s+(.*?)\s+@\s+"([^"]+)"',chosen.group())
                target,key=parsed.groups()
                block=text.rfind('sequence {',0,chosen.start())
                prefix=text[block+len('sequence {'):chosen.start()]
                expected['required_details']={'torque_key':key,'target_path':target,'sequence_index':prefix.count(';'),'torque_reason':reason}
            else:
                expected['required_details']={'torque_reason':'impulse_axis','expected_axis':'world_z','actual_angular_velocity_world_rad_per_s':[0,-1,0]}
            if phase in ('admission','evaluation'):
                expected['side']='after'
            if reason=='axis_lock':
                expected['required_details'].update(expected_axis='world_z' if number==11 else 'world_x',actual_axis='world_x' if number==11 else 'world_y')
            if reason in ('target_mode','incoming_axis'):
                expected['required_related_target_declaration']=True
        if number==5:
            expected.update(phase='syntax',primary_source=span(text,'(',text[:text.index('about vector')].count('(')))
            expected['inherited_diagnostic_authority']='Parser.take context: axis identifier vector accepted; next token ( refuses expected contextual using.'
        if number in (6,10):
            statement=next(re.finditer(r'torque\s+[^;]+;',text)).group()
            expected['primary_source']=span(text,statement)
            expected['diagnostic_authority']='Inherited force_values target path_value(...,event) and compiler.expect(...,event), including the unchanged values.coerce constructor. Independent reviewer traced exact source before implementation.'
            if number==6:
                expected.update(code='OKL-E-NAME',phase='binding',message="Unknown name 'missing' in this lexical scope.",required_details={})
            else:
                expected.update(code='OKL-E-UNIT',phase='type',message='Expected Ref<Object>, received Mass.',required_details={'expected':'Ref<Object>','actual':'Mass'})
        if number==25:
            expected.update(code='OKL-E-NUMERIC',phase='evaluation',category='numerical_failure',agent_status='failed',
              message='Distinct semantic boundaries collapse to one binary32 clock.',adapter_export_code='OKE-E-TIMES-COLLAPSED',
              blocks=['delivered'],required_details={'target_contract':'ontokin.glb/0.22','export_code':'OKE-E-TIMES-COLLAPSED'},
              diagnostic_authority='Inherited reach_export._fail numeric default through scene.export_error; OKE code is adapter identity in details, not a public diagnostic code.')
            scene_text=text[text.index('scene Demo @ "demo" {'):text.rfind('}')+1]
            expected['primary_source']=span(text,scene_text)
        if number in (17,26):
            # A requested incoming segment preserves the request's own side;
            # only staged boundary failures force the after side.
            expected.pop('side',None)
            expected['side_rule']='same as the requested observation; execute both before and after requests independently'
        if number in (8,9):
            name='control-'+item['id']
            oldtext=re.sub(r'        torque[^\n]+\n','',text).replace('"0.22"','"0.21"',1).replace('"torque-0.1"','"keyed-membership-0.1"',1)
            write('sources/'+name+'.ok',oldtext);write(name+'.files.json',manifest(name))
            item['predecessor_diagnostic_control']={'file_manifest':name+'.files.json','identity':identities(name),'expected_code':'OKL-E-PHYSICAL-DOMAIN','final_projection_authority':'Untouched C088 construction attempt retained in predecessor evidence; library source location plus inherited parameter origin, not a fabricated torque statement span.'}
    # Actual inherited control envelopes are legitimate predecessor evidence,
    # not a torque implementation oracle. Preserve every field and substitute
    # only the independently known .22 program revision for body controls.
    predecessor=ROOT/'evidence/inherited-refusals01.json'
    if predecessor.exists():
        observed=json.loads(predecessor.read_text())
        for item in records:
            number=int(item['id'][1:3])
            if number not in (8,9,19): continue
            name=('control-' if number in (8,9) else '')+item['id']+'.files.json'
            row=next(r for r in observed['cases'] if r['file_manifest']==name)
            projection=deepcopy(row['diagnostic'])
            projection['program_revision']=item['identity']['program_revision']
            primary=projection['primary']
            unit=(ROOT/'modules/carriers.ok').read_text() if number in (8,9) else (ROOT/('sources/'+item['id']+'.ok')).read_text()
            item['expected'].update(code=projection['code'],phase=projection['phase'],message=projection['message'],
              primary_source={'source_id':primary['source_id'],'start_byte':primary['start_byte'],'end_byte':primary['end_byte'],'text':unit.encode()[primary['start_byte']:primary['end_byte']].decode()},
              diagnostic_projection=projection,diagnostic_authority='Exact untouched C088 predecessor envelope in evidence/inherited-refusals01.json; only the .22 body-case program revision changes. No extra related span is fabricated.')
            item['predecessor_observation_used']=True
    write('refusal-cases.json',{'schema_version':'ontokin.torque-independent-refusals/1','state':'Pre-implementation independent expected refusals; root contract review amendment 01 and actual inherited control diagnostics applied','candidate_observations_used':False,'cases':records})

    # A large phase boundary is evaluation-only: its mathematical assertion
    # does not use the small-angle trigonometric oracle or promise delivery.
    cap=source({'id':'domain01-exact-phase-cap','horizon':'1','torques':[tor('drive',0,1,'2097152')]})
    write('sources/domain01-exact-phase-cap.ok',cap);write('domain01-exact-phase-cap.files.json',manifest('domain01-exact-phase-cap'))
    domains=[{'id':'domain01-exact-phase-cap','file_manifest':'domain01-exact-phase-cap.files.json','identity':identities('domain01-exact-phase-cap'),'expected_compile':'accepted','expected_evaluation':'accepted','time_seconds':'1','side':'before','expected_phase_hex':float(2**20).hex(),'expected_speed_hex':float(2**21).hex(),'phase_max_exact':'1048576','phase_max_at_seconds':'1','recording_claim':False,'small_trigonometric_oracle_applies':False}]
    large=2**537
    for name,duration,phase,speed in [('domain02-underflow-long-prefix',large,F(1,4),F(1,2**538)),('domain03-reference-origin-transfer',large//2,F(3,16),F(1,2**539))]:
        text=source({'id':name,'mass':'5','horizon':str(large),'torques':[tor('shadow',0,str(duration),'5e-324')]})
        write('sources/'+name+'.ok',text);write(name+'.files.json',manifest(name))
        domains.append({'id':name,'file_manifest':name+'.files.json','identity':identities(name),'expected_compile':'accepted','expected_evaluation':'accepted','time_seconds':str(large),'side':'after','expected_rotation_route':'legacy','expected_rotation_anchor':None,'expected_canonical_orientation_wxyz':[1,0,0,0],'expected_canonical_speed_hex':'0x0.0p+0','inertia_hex':'0x1.0000000000000p+1','alpha_reference_when_active':str(F(1,2**1075)),'exact_reference_phase':str(phase),'exact_reference_speed':str(speed),'minimum_angular_error_bound_rad':str(phase),'minimum_angular_speed_error_bound_rad_per_s':str(speed),'reference_origin_changes_at':None if duration==large else str(duration),'recording_claim':False,'new_phase_cap_does_not_apply_to_legacy':True,'witness_origin':'Independently recomputed from exact tau/I and exact clocks after numeric reviewer supplied long-prefix scenario; no candidate output.'})
    name='domain04-reference-only-change'
    text=source({'id':name,'horizon':'3','torques':[tor('drive',0,3,1),tor('shadow',1,1,'5e-324')]})
    write('sources/'+name+'.ok',text);write(name+'.files.json',manifest(name))
    domains.append({'id':name,'file_manifest':name+'.files.json','identity':identities(name),'expected_compile':'accepted','expected_evaluation':'accepted','time_seconds':'1.5','side':'after','expected_rotation_route':'split','expected_rotation_anchor_seconds':'0','expected_phase_hex':float(F(9,8)).hex(),'expected_speed_hex':float(F(3,2)).hex(),'expected_alpha_hex':'0x1.0000000000000p+0','expected_alpha_reference':str(1+F(1,2**1074)),'exact_reference_phase':str(F(9,8)+F(1,2**1077)),'exact_reference_speed':str(F(3,2)+F(1,2**1075)),'reference_origin_changes_at':'1','canonical_anchor_must_not_change':True,'recording_claim':False,'small_trigonometric_oracle_applies':True,'predecessor_control':'control-spin-up.files.json'})
    write('evaluation-domain-cases.json',{'schema_version':'ontokin.torque-independent-evaluation-domains/1','candidate_observations_used':False,'cases':domains})


if __name__=='__main__':
    main()
