#!/usr/bin/env python3
"""Freeze source-authorized delivery settings and hostile supplied-byte probes."""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction as F
from pathlib import Path
import json
import re

from author_inputs import ROOT, write, manifest, identities, span, source, tor
from reference.author_state_expectations import records

AUTHORIZATION='execution { max_operations = 1000000; max_elapsed = 30[s]; }\n'
HOST={'max_operations':1000000,'max_elapsed_ms':30000}


def authorized(text):
    return text.replace('profile "torque-0.1";\n','profile "torque-0.1";\n'+AUTHORIZATION,1)


def variant(name,text):
    write('sources/'+name+'.ok',authorized(text));write(name+'.files.json',manifest(name))
    return identities(name)


def main():
    physics=json.loads((ROOT/'physics-cases.json').read_text())['cases']
    missing={'p03-braking-reversal':'Default100000-operation readback cap at100001.',
             'p19-torque-then-impulse':'Default100000-operation readback cap at100001.',
             'p20-impulse-then-torque':'Default100000-operation readback cap at100001.',
             'p28-release-then-torque':'Inherited independent validation: Independent spin norm is unresolved.'}
    deliveries=[]
    for case in physics:
        name='delivery-'+case['id']; identity=variant(name,(ROOT/('sources/'+case['id']+'.ok')).read_text())
        bound_case={**case,'id':name,'identity':identity}
        records_for_source=records(bound_case)
        deliveries.append({'id':name,'physics_case':case['id'],'file_manifest':name+'.files.json','identity':identity,
          'source_authorization':HOST,'host_policy':HOST,
          'options':{'fps':4,'end':case['horizon'] if '/' not in case['horizon'] else str(float(F(case['horizon']))),'helpers':False,'position_tolerance_m':0.001,'rotation_tolerance_rad':0.001,'time_tolerance_s':0.000001},
          'required_future_outcome':'Complete accepted .22 artifact and independent supplied-byte/native/controlled-destination evidence. This is a future gate, not an observed success. Any cap/refusal remains a failure under this frozen allocation.',
          'actual_predecessor_artifact_available':case['id'] not in missing,'actual_predecessor_limitation':missing.get(case['id']),
          'predecessor_evidence_archive':'predecessor/new-control-artifacts01.zip',
          'predecessor_case_path':'cases/'+case['id'],
          'source_records':records_for_source,
          'expected_physics_binding':'Use the immutable physics and exact state values of '+case['id']+'; replace only complete interval/program/source identities by source_records here. Canonical numbers/anchors/counts/times remain equal.',
          'common_clock_oracle':'Every physics-cases sample plus both sides of every state-expectations boundary; use exact clocks and the requested side. Before/after metadata is distinct even when poses coincide.',
          'dense_playback_oracle':'For each actual retained key interval [a,b], independently evaluate the source law at a+(b-a)*j/32, j=0..32, and all frozen sample clocks. Compare actual named controlled destination matrices, frame origins, each source box vertex and named sites against independent interval enclosures. Dense checks supplement the complete interval certificate, never replace it.',
          'comparison_classes':['C1 only for separately replayed unchanged old accepted bytes','C2 repeated same .22 source','C4 carrier COM','C6 changed-source delivery'],
          'helpers_true_repeat':case['id'] in ('p01-spin-up','p14-offset-reversal','p27-generated-two-carriers','p28-release-then-torque','p31-noncommuting-initial-rotation')})
    write('delivery-cases.json',{'schema_version':'ontokin.torque-independent-delivery-cases/1','candidate_output_used':False,
      'allocation_decision':{'source_operations':1000000,'source_elapsed_ms':30000,'host':HOST,'decision':'Root selected this separate10x operation allocation before implementation. No old source, default, original control, horizon or failure is changed. No further cap adjustment is authorized by candidate output.'},
      'required_target':'ontokin.glb/0.22','required_player':'ontokin-controlled-three-recording/0.2.0',
      'baseline_status':{'source_and_pose_controls_passed':31,'original_artifacts_passed':27,'artifact_batch_status':'failed','four_limitations':missing,'success_claim':'Only actually retained accepted original.glb bytes supply C1/C6 artifact pairs. All31 controls supply source/common-clock pose evidence. New .22 release delivery needs its own proof; no old p28 artifact is invented.'},
      'cases':deliveries,
      'geometry_and_landmarks':{'marker_vertices_local_m':[['0','0','0'],['1/4','0','0'],['1/4','1/2','0'],['0','1/2','0'],['0','0','1/8'],['1/4','0','1/8'],['1/4','1/2','1/8'],['0','1/2','1/8']],
        'marker_local_radius_squared':'21/64','label_origin_offset':['marker_radius','0','0'],'arm_origin_offset':['1/4','0','0'],'nested_tip_origin_offset':['3/4','3/8','0'],'nested_tip_origin_radius_squared':'45/64',
        'top_uv':'U=4*x,V=2*y; exact binary32 corner UVs0/1. Bottom/top PBR linearRGBA(1,1,1,1),metallic0,roughness.75; sideRGBA(.125,.5,.875,1),metallic0,roughness.5.',
        'png_sha256':'sha256:5f87c7071d06327a077e05e1f57253370bc0b2eff1fa7f2025765825b7dcdd6e','png_bytes':89,
        'matter':'Every visual marker has own mass0/inertia null. Source sphere mass/inertia remain the independently frozen own quantities; marker geometry adds no mass.'},
      'small_source_pose_comparison':{'quaternion_sign':'Minimum Euclidean difference against q and -q, using full saved-rotation left product intervals. Stored adjacent endpoint sign coherence remains a separate exact reader requirement.',
        'quaternion_absolute_tolerance':'1/1099511627776','carrier_position_absolute_tolerance_m':'1/1099511627776','marker_position_absolute_tolerance_m':'(1+COM_to_marker_radius+local_landmark_radius)/1099511627776',
        'scope':'Only31 small physics cases and their unchanged numeric delivery variants. Long-prefix domains and cap-boundary domain are excluded. The delivered .001 bounds are independently recomputed, not inferred from this sampled agreement.'},
      'certificate_minimum_rules':['Alpha=max exact absolute reference angular acceleration on each complete phase, including inherited transfer uncertainty; two independent Alpha fields cannot silently default to0.',
        'Omega=max endpoint magnitude of the exact affine reference speed, including inherited angular uncertainty; never abs(net displacement)/duration.',
        'Origin speed<=V_COM+rho*Omega and acceleration<=A_COM+rho*(Alpha+Omega^2), including full nested offset. Mesh/site local radius separately multiplies total angular error.',
        'At p14 width1, Alpha=1/512,Omega=1/1024,rho100: phase chord1/4096 and origin chord51225/2097152; equal orientation endpoints alone cannot certify the moving100m marker.',
        'Source quaternion chord Alpha*h^2/16+Omega^2*h^2/32; rotation plan(Alpha+Omega^2)*h^2/4; position plan A*h^2/8; all complete source,endpoint,clock,quaternion,destination terms remain required.'],
      'metadata_difference_whitelist':['/extras/ontokin/{target_contract,schema_version,profile,program,source,torque_profile,reach_profile,reach_quantization,boundary_states}',
        '/animations/0/extras/ontokin/{target_contract,boundary_times_seconds,exact_times_seconds}',
        'Source-bound entry revision/provenance leaves on otherwise identical occurrences, only where independently recomputed from frozen new source.',
        'Animation input/output accessor byte ranges, counts, extrema, offsets and buffer length caused solely by justified new exact key clocks and poses; re-decode every value and compare source.',
        'Source-authorized execution request identity in new delivery/workflow variants.'],
      'forbidden_normalization':['Dropping unknown metadata fields or unordered arrays','Stripping complete torque/boundary histories','Comparing geometry only by visual screenshots','Treating new-source GLB bytes as identical to old source-bound bytes','Relaxing unchanged predecessor whole-stream equality'],
      'execution_claim':False})

    # Separate exact Agent workflow source and repair identities carry the
    # selected source request; original default fixtures remain byte-identical.
    repairs=json.loads((ROOT/'agent/repairs.json').read_text())
    base='workflow-agent-base'; base_text=authorized((ROOT/'sources/agent-base.ok').read_text())
    variant(base,(ROOT/'sources/agent-base.ok').read_text())
    extended=deepcopy(repairs);extended['base_identity']=identities(base);extended['base_fixture']=base
    for row in extended['repairs']:
        old_id=row['id']; new_id='workflow-'+old_id; variant(new_id,(ROOT/('sources/'+old_id+'.ok')).read_text())
        patch=row['patch']; located=span(base_text,patch['expected_text'])
        row.update(id=new_id,**{'from':identities(base)},to=identities(new_id),file_manifest=new_id+'.files.json')
        patch.update(start_byte=located['start_byte'],end_byte=located['end_byte'],source_revision=next(u['source_revision'] for u in identities(base)['manifest']['units'] if u['source_id']=='entry'))
    extended['first_carrier_at_2']={'workflow-'+key:value for key,value in repairs['first_carrier_at_2'].items()}
    extended['source_authorization']=HOST;extended['host_policy']=HOST
    extended['invalid_candidates_preserve']='Exact accepted workflow-agent-base revision, runs and artifacts. All original default agent-base fixtures remain separate immutable inputs.'
    write('agent/workflow-repairs.json',extended)

    # Explicit unsupported fixed-path boundary: a still-active authored joint
    # under even a zero-torque latch is outside recorded composition scope.
    negative=[]
    for name,moving in [('n31-static-articulated-marker',False),('n32-moving-articulated-marker',True)]:
        text=source({'id':name,'horizon':'2','torques':[tor('drive',0,2,1 if moving else 0)]})
        cls='public class Flag @ "flag-type" {\n    geometry = box(vec3(0.25[m], 0.5[m], 0.125[m]));\n    physical = no_body();\n}\n\n'
        text=text.replace('scene Demo @ "demo" {',cls+'scene Demo @ "demo" {')
        # Core joints require a prescribed parent. The massless arm is a
        # prescribed fixed follower of the free sphere, so the joint remains
        # on a torque-affected dependency path without changing source rules.
        joint='joint swivel @ "swivel": hinge {\n        parent = ball.arm.origin;\n        child = flag.origin;\n        axis = vec3(0, 0, 1);\n        limits = range(-1[rad], 1[rad]);\n        initial = 0[rad];\n    }'
        members='    object flag @ "flag": Flag {}\n    '+joint+'\n'
        if moving: members+='    action turn @ "turn" = tween(swivel, 0.5[rad], 1[s]);\n'
        text=text.replace('    at 0[s] sequence {',members+'    at 0[s] sequence {'+(('\n        start turn;') if moving else ''),1)
        ident=variant(name,text); final=(ROOT/('sources/'+name+'.ok')).read_text()
        negative.append({'id':name,'file_manifest':name+'.files.json','identity':ident,'expected_compile':'accepted','expected_evaluation':'accepted',
          'host_policy':HOST,'options':{'fps':4,'end':'2','helpers':False,'position_tolerance_m':0.001,'rotation_tolerance_rad':0.001,'time_tolerance_s':0.000001},
          'expected_delivery':{'outcome':'refused','agent_status':'rejected','code':'OKL-E-CAPABILITY-UNSUPPORTED','phase':'support','category':'unsupported','adapter_export_code':'OKE-E-TORQUE-COMPOSITION','kind':'unsupported','blocks':['delivered'],'message':'Torque recording requires fixed rigid marker paths.','primary_source':span(final,joint),'details':{'target_contract':'ontokin.glb/0.22','export_code':'OKE-E-TORQUE-COMPOSITION','profile':'torque-0.1','carrier':'ball','frame':'flag.frame'},'repair_summary':'Use supported visual geometry and the explicitly matching model/delivery profile.','artifact_published':False}})
        control='control-'+name
        old=re.sub(r'        torque[^\n]+\n','',final).replace('"0.22"','"0.21"',1).replace('"torque-0.1"','"keyed-membership-0.1"',1)
        write('sources/'+control+'.ok',old);write(control+'.files.json',manifest(control))
        negative[-1]['predecessor_construction_control']={'file_manifest':control+'.files.json','identity':identities(control),'host_policy':HOST,'expected_compile':'accepted','expected_objects':9}
    write('delivery-refusals.json',{'schema_version':'ontokin.torque-independent-delivery-refusals/1','cases':negative,'candidate_output_used':False})

    cert='/extras/ontokin/reach_quantization/interval_certificates'
    mutations=[]
    def mutation(key,fixture,selector,action,code,**more):
        unsupported=code=='OKE-E-GLB-STRUCTURE'
        details=more.pop('expected_details',{})
        mutations.append({'id':key,'original_fixture':fixture,'selector':selector,'mutation':action,'expected_export_code':code,
          'expected_code':'OKL-E-CAPABILITY-UNSUPPORTED' if unsupported else 'OKL-E-NUMERIC',
          'expected_phase':'support' if unsupported else 'evaluation','expected_category':'unsupported' if unsupported else 'numerical_failure',
          'expected_agent_status':'rejected' if unsupported else 'failed','expected_blocks':['delivered'],
          'expected_details':{'target_contract':'ontokin.glb/0.22','export_code':code,**details},
          'expected_outcome':'refused','details_mode':'Required exact listed scalar values; retain inherited additional bounded detail keys from the actual selected constructor.',**more})
    for field in ['angular_acceleration_bound_rad_per_s2','enclosing_angular_acceleration_bound_rad_per_s2']:
        mutation('missing-'+field,'delivery-p14-offset-reversal',cert+'[carrier.path=ball.label,left_key_index=0]/'+field,{'operation':'delete'},'OKE-E-CERTIFICATE-COVERAGE')
        mutation('zero-'+field,'delivery-p14-offset-reversal',cert+'[carrier.path=ball.label,left_key_index=0]/'+field,{'operation':'replace','value':0},'OKE-E-CERTIFICATE',expected_details={'quantity':field})
    for field in ['carrier_acceleration_bound_m_per_s2','enclosing_carrier_speed_bound_m_per_s','enclosing_carrier_acceleration_bound_m_per_s2']:
        mutation('zero-offset-'+field,'delivery-p14-offset-reversal',cert+'[carrier.path=ball.label,left_key_index=0]/'+field,{'operation':'replace','value':0},'OKE-E-CERTIFICATE',expected_details={'quantity':field})
    mutation('nested-offset','delivery-p01-spin-up',cert+'[carrier.path=ball.arm.tip,left_key_index=0]/carrier_acceleration_bound_m_per_s2',{'operation':'replace','value':0},'OKE-E-CERTIFICATE',expected_details={'quantity':'carrier_acceleration_bound_m_per_s2'})
    mutation('zero-landmark','delivery-p01-spin-up',cert+'[carrier.path=ball.label,left_key_index=0]/landmark_radius_m',{'operation':'replace','value':0},'OKE-E-CERTIFICATE',expected_details={'quantity':'landmark_radius_m'})
    mutation('zero-vertex-error','delivery-p01-spin-up',cert+'[carrier.path=ball,left_key_index=0]/local_vertex_error_bound_m',{'operation':'replace','value':0},'OKE-E-CERTIFICATE',expected_details={'quantity':'local_vertex_error_bound_m'},precondition='Original source sphere binary32 conversion has a strictly positive independently recomputed error; zero-error carriers are not eligible substitutes.')
    for action in ['delete-first','duplicate-first','replace-right-index-with-left']:
        mutation('certificate-'+action,'delivery-p01-spin-up',cert,{'operation':action},'OKE-E-CERTIFICATE-COVERAGE')
    mutation('extra-certificate-field','delivery-p01-spin-up',cert+'[0]',{'operation':'add','key':'unproved','value':0},'OKE-E-CERTIFICATE-COVERAGE')
    mutation('bool-Alpha','delivery-p01-spin-up',cert+'[0]/angular_acceleration_bound_rad_per_s2',{'operation':'replace','value':True},'OKE-E-CERTIFICATE')
    mutation('negative-Alpha','delivery-p01-spin-up',cert+'[0]/angular_acceleration_bound_rad_per_s2',{'operation':'replace','value':-1},'OKE-E-CERTIFICATE')
    mutation('nan-JSON','delivery-p01-spin-up',cert+'[0]/angular_acceleration_bound_rad_per_s2',{'operation':'raw-json-number-token','value':'NaN'},'OKE-E-GLB-STRUCTURE')
    mutation('nonreduced-width','delivery-p01-spin-up',cert+'[0]/h_authored_seconds',{'operation':'multiply-both-integer-strings','factor':2},'OKE-E-CLOCK')
    mutation('zero-denominator','delivery-p01-spin-up',cert+'[0]/h_authored_seconds/denominator',{'operation':'replace','value':'0'},'OKE-E-CLOCK')
    mutation('neighboring-phase-enclosing-Alpha','delivery-p29-canonical-clock-addition',cert+'[carrier.path=ball,authored-right-clock=exact-canonical-0.1,authored-Alpha=0]/enclosing_angular_acceleration_bound_rad_per_s2',{'operation':'replace','value':0},'OKE-E-CERTIFICATE',expected_details={'quantity':'enclosing_angular_acceleration_bound_rad_per_s2'},precondition='The binary32 stored0.1 endpoint is above exact canonical source0.1 and intersects the newly accelerated neighboring phase; authored Alpha remains0 while enclosing Alpha is independently at least1.')
    mutation('actual-clock-binary32-rounding','delivery-p01-spin-up','common binary32 input accessor, first positive nonfinal key',{'operation':'increment exact unsigned binary32 bits by1; update accessor extrema only if changed; leave exact authored clocks and retained labels unchanged'},'OKE-E-CLOCK-ROUNDING')
    mutation('reordered-common-clock','delivery-p01-spin-up','common binary32 input accessor, first two positive adjacent nonfinal keys',{'operation':'swap the two four-byte entries only; retain valid framing and all metadata'},'OKE-E-GLB-STRUCTURE')
    mutation('different-channel-clock','delivery-p01-spin-up','one nonfirst sampler input accessor',{'operation':'copy original common clock accessor/bufferView, increment one strictly interior positive binary32 clock by1, redirect only this sampler, retain strictly increasing clocks and framing'},'OKE-E-CLOCK')
    mutation('missing-phase','delivery-p04-overlap',cert+'[carrier.path=ball,left_key_index=first-row-with-positive-width-phase]/source_phase_indices',{'operation':'replace','value':[]},'OKE-E-PHASE-COVERAGE')
    mutation('duplicate-phase','delivery-p04-overlap',cert+'[0]/source_phase_indices',{'operation':'append-first-again'},'OKE-E-PHASE-COVERAGE')
    mutation('wrong-source-basis','delivery-p01-spin-up','/extras/ontokin/reach_quantization/source_numeric_bound_basis/implementation_sha256',{'operation':'replace','value':'sha256:'+'0'*64},'OKE-E-SOURCE-NUMERIC-BASIS')
    mutation('old-player-basis','delivery-p01-spin-up','/extras/ontokin/reach_quantization/destination_numeric_bound_basis/version',{'operation':'replace','value':'0.1.0'},'OKE-E-DESTINATION-NUMERIC-BASIS')
    for key,field,value in [('axis','axis','world_x'),('key','torque_key','forged'),('sign','torque_n_m',-2),('program','program_revision','sha256:'+'0'*64),('span','source_location.start_byte',0)]:
        mutation('history-'+key,'delivery-p01-spin-up','first after-zero recorded ball.torques.active[torque_key=drive]/'+field,{'operation':'replace','value':value},'OKE-E-BOUNDARY-HISTORY')
    mutation('history-missing-zero','delivery-p05-cancelling','first after-zero ball.torques.active',{'operation':'delete-first'},'OKE-E-BOUNDARY-HISTORY')
    mutation('history-reordered','delivery-p05-cancelling','first after-zero ball.torques.active',{'operation':'reverse'},'OKE-E-BOUNDARY-HISTORY')
    mutation('history-fake-route','delivery-p24-underflow-is-neutral','first after-zero ball.torques.rotation_route',{'operation':'replace','value':'split'},'OKE-E-BOUNDARY-HISTORY')
    mutation('history-drop-shadow','delivery-p24-underflow-is-neutral','final ball.torques.angular_error_bound_rad',{'operation':'replace','value':{'numerator':'0','denominator':'1'}},'OKE-E-BOUNDARY-HISTORY')
    mutation('root-topology','delivery-p01-spin-up','/nodes[mesh of ball]/children',{'operation':'add','value':['actual ball.label node index'],'remove_child_from_scene_roots':True},'OKE-E-GLB-STRUCTURE')
    mutation('incoherent-quaternion-sign','delivery-p01-spin-up','ball rotation accessor middle sample',{'operation':'negate-all-four-components','also_change_node_if_first':False},'OKE-E-QUATERNION-LIFT')
    mutation('self-consistent-understatement','delivery-p14-offset-reversal',cert+'[carrier.path=ball.label,left_key_index=0]',{'operation':'set authored/enclosing Alpha to0 and recompute only claimed algebraic totals from these forged primitives; retain truthful large totals when necessary'},'OKE-E-CERTIFICATE',required_failure='Independent source minimum, regardless of self-consistent reported algebra.')
    mutation('equal-endpoints-delete-interior','delivery-p21-equal-endpoint-reversal','all input and output animation tracks plus certificate/index arrays',{'operation':'retain only exact0and1 endpoints, preserve source boundary/history metadata, rebuild valid GLB framing and adjacent certificate coverage; recompute widths and endpoint claims but preserve independent Alpha/Omega minima'},'OKE-E-CERTIFICATE',required_failure='Rotation-plan quarter allocation or source-acceleration chord cannot be met by endpoint-only playback.')
    write('hostile-delivery-cases.json',{'schema_version':'ontokin.torque-independent-hostile-bytes/1','candidate_output_used':False,
      'procedure':['First produce and independently accept the unchanged original from exact named delivery fixture/options under its fixed source/host policy. Freeze original raw bytes/hash before mutation.',
        'Apply only the stated mutation. JSON edits rebuild valid chunk framing with canonical compact JSON and space padding, leaving original BIN bytes unchanged unless mutation explicitly names an accessor. Preserve all other semantic fields exactly.',
        'Selectors use exact source carrier path and canonical smallest left key index; missing or nonunique selector is a fixture failure, never skip or choose a convenient different original.',
        'Submit altered raw GLB to the actual independent supplied-byte reader with the same original source/options. Verify actual OntoKinError public code/phase/category/blocks and adapter identity in details.export_code; there is no invented ExportError class or public phase export. No accepted artifact publication.',
        'Retain complete original and hostile bytes, both hashes, mutation receipt, actual rejection code/details, and unchanged successful original control. Then independently reopen store and verify no hostile artifact entered accepted inventory.'],
      'cases':mutations,'execution_claim':False})


if __name__=='__main__': main()
