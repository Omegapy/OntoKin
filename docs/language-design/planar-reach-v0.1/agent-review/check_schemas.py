#!/usr/bin/env python3
"""Pure proposed-schema checks: no Agent, store, source evaluation or GLB run."""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
from importlib.metadata import version
import json
from pathlib import Path
import platform
import subprocess
import sys
from urllib.parse import urldefrag

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

HERE = Path(__file__).resolve().parent
PROPOSAL = HERE.parent
REPO = PROPOSAL.parents[2]
REV = 'sha256:' + '1' * 64
HEAD_REV = 'sha256:' + '2' * 64
IMPL = {'name':'synthetic-schema-shape', 'version':'0', 'source_code_sha256':'sha256:'+'3'*64}
START = datetime.now(timezone.utc).isoformat()


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


AUTHOR = load_module('proposed_reach_schema_author', PROPOSAL/'author_schema_drafts.py')
# This pure counter imports only the standard library. It creates no service,
# runtime, SQLite connection or source model.
JSON_LIMITS = load_module('inherited_json_limits', REPO/'ontokin/json_limits.py')
ROWS = AUTHOR.schemas()
RESOURCES = {row['$id']: row for row in ROWS.values()}
for name in AUTHOR.INHERITED_INPUTS:
    data = json.loads((PROPOSAL.parent/name).read_text())
    RESOURCES[data['$id']] = data
REGISTRY = Registry().with_resources((uri, Resource.from_contents(data))
                                    for uri, data in RESOURCES.items())
VALIDATORS = {name: Draft202012Validator(data, registry=REGISTRY) for name, data in ROWS.items()}
CHECKS = []


def sha(raw):
    return 'sha256:' + hashlib.sha256(raw).hexdigest()


def check(name, condition, detail=None):
    row = {'id':f'C{len(CHECKS)+1:04d}', 'name':name,
           'status':'passed' if condition else 'failed'}
    if detail is not None:
        row['detail'] = detail
    CHECKS.append(row)


def shape(name, filename, data, expected=True):
    errors = list(VALIDATORS[filename].iter_errors(data))
    check(name, bool(errors) != expected,
          {'expected_valid':expected, 'error_count':len(errors),
           'first_error':None if not errors else errors[0].message[:500]})


def wire(name, value, expected=True):
    try:
        JSON_LIMITS.measure_json(value)
        valid = True
    except (ValueError, TypeError, RecursionError):
        valid = False
    check(name, valid == expected)


def occurrence(path):
    return {'path':path, 'element_id':['shape','scene',*path.split('.')]}


def projection(lifecycle='running', *, context='agent', sampled=True):
    q = [0.2, 0.3]
    pose = {'position_m':[1,1,0], 'orientation_wxyz':[1,0,0,0]}
    state = {
        'observation':{'time_seconds':'1.5','side':'after','run_id':'run:synthetic',
                       'context_kind':'run_sample'},
        'lifecycle':lifecycle,
        'goal_outcome':{'pending':'pending','running':'active','paused':'active',
                        'stopped':'interrupted','completed':'satisfied'}[lifecycle],
        'resolved_joint_targets_rad':[0.4,0.5], 'start_coordinates_rad':[0,0],
        'start_time_seconds':'0', 'elapsed_seconds':'1.5', 'completion_time_seconds':'2',
        'joint_coordinates_rad':q, 'joint_rates_rad_per_s':[0.2,0.25],
        'action_joint_rates_rad_per_s':[0.2,0.25],
        'claimed_joint_ids':[occurrence('arm.shoulder')['element_id'],occurrence('arm.elbow')['element_id']],
        'current_residual_m':0.1, 'tip_pose_base':copy.deepcopy(pose), 'tip_pose_world':copy.deepcopy(pose),
        'current_world_target_m':[1,1,0], 'terminal_result':None,
    }
    if lifecycle in ('pending','stopped','completed'):
        state['claimed_joint_ids'] = []
    if lifecycle != 'running':
        state['action_joint_rates_rad_per_s'] = [0,0]
    if lifecycle == 'pending':
        for field in ('resolved_joint_targets_rad','start_coordinates_rad','start_time_seconds',
                      'elapsed_seconds','completion_time_seconds','current_residual_m'):
            state[field] = None
    if lifecycle in ('paused','stopped'):
        state['completion_time_seconds'] = None
    if lifecycle == 'paused':
        state['joint_rates_rad_per_s'] = [0,0]
    if lifecycle in ('stopped','completed'):
        state['terminal_result'] = {'outcome':state['goal_outcome'],'time_seconds':'1',
            'position_residual_m':0 if lifecycle == 'completed' else 0.2,
            'joint_coordinates_rad':[0.1,0.15],'tip_pose_base':copy.deepcopy(pose)}
    if context == 'source_recording':
        state['observation'].update(context_kind='recorded_prefix',run_id=None)
    frame = {'path':'arm.base','site_element_id':['shape','scene','arm','base']}
    return {
        'kind':'reach_planar','element_id':['shape','scene','reach'],
        'description_identity':['shape','scene','reach'],'program_revision':REV,
        'accepted_program_revision':REV if context == 'agent' else None,
        'candidate_only':False if context == 'agent' else None,'context_origin':context,
        'source_location':{'source_id':'entry','source_revision':REV,'start_byte':0,'end_byte':10},
        'channel':'joint_coordinates', 'chain':{'shoulder':occurrence('arm.shoulder'),
            'elbow':occurrence('arm.elbow'),'tip':occurrence('arm.tip'),'base_frame':frame,
            'lengths_m':[1,1],'closed_limits_rad':{'shoulder':[-3.14,3.14],'elbow':[-3.14,3.14]}},
        'target':{'type':'Point3','frame':copy.deepcopy(frame),'coordinates_m':[1,1,0]},
        'branch':'elbow_positive','duration_seconds':'2',
        'current':{'available':True,'reason':None,'value':state} if sampled else
                  {'available':False,'reason':'run_required','value':None},
    }


def envelope(*, operation='inspect', result=None):
    return {'schema_version':'ontokin.agent/0.6','project_id':'synthetic-shape-project',
        'request_id':'synthetic-shape-request','operation':operation,'status':'succeeded',
        'program_revision':REV,'accepted_program_revision':REV,'requested_level':None,
        'achieved_level':'represented','run_id':'run:synthetic','diagnostics':[],
        'result':result if result is not None else {'items':[{'actions':[projection()]}]},
        'progress':{'phase':'complete','cancellation_requested':False,'implementation':IMPL},
        'next_cursor':None,'truncated':False,'protocol_error':None}


def schema_checks():
    check('exactly_seven_named_schemas', set(ROWS) == {
        'common.schema.json','agent-request.schema.json','agent-response.schema.json',
        'reach-projection.schema.json','reach-diagnostic.schema.json',
        'quantization.schema.json','glb-metadata.schema.json'})
    for name, data in ROWS.items():
        try:
            Draft202012Validator.check_schema(data)
            valid = True
        except Exception as error:
            valid = False
            check('schema_meta_error_'+name, False, str(error))
        check('schema_meta_'+name, valid)
        raw = (json.dumps(data,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()
        check('generated_bytes_'+name, (PROPOSAL/'schema-drafts'/name).read_bytes() == raw)
        check('proposal_id_'+name, data['$id'] == AUTHOR.ROOT+name)

    def references(value, base):
        if isinstance(value, dict):
            if '$id' in value:
                base = value['$id']
            if '$ref' in value:
                target = value['$ref']
                uri, fragment = urldefrag(target)
                uri = uri or base
                check('local_ref_'+target, uri in RESOURCES, {'base':base})
                if uri in RESOURCES and fragment:
                    current = RESOURCES[uri]
                    try:
                        for part in fragment.lstrip('/').split('/'):
                            key = part.replace('~1','/').replace('~0','~')
                            current = current[int(key)] if isinstance(current,list) else current[key]
                        resolved = True
                    except (KeyError, IndexError, ValueError, TypeError):
                        resolved = False
                    check('local_fragment_'+target, resolved, {'base':base})
            for child in value.values():
                references(child,base)
        elif isinstance(value,list):
            for child in value:
                references(child,base)
    for data in RESOURCES.values():
        references(data,data['$id'])
    inventory = json.loads((PROPOSAL/'generated-members.json').read_text())
    for row in inventory['members']:
        data = (PROPOSAL/row['path']).read_bytes()
        check('original_corpus_'+row['path'], len(data) == row['bytes'] and sha(data) == row['sha256'])


def request_checks():
    names = ['discover','create','edit','validate','inspect','evaluate','reset','status',
             'cancel','export','artifact','surface.mesh_page']
    check('exactly_twelve_inherited_operations',
          [r['properties']['operation']['const'] for r in ROWS['agent-request.schema.json']['oneOf']] == names)
    old = json.loads((PROPOSAL.parent/'agent-v0.5/request.schema.json').read_text())
    expected = json.loads(json.dumps(old).replace('ontokin.agent/0.5','ontokin.agent/0.6').replace('ontokin.glb/0.5','ontokin.glb/0.6'))
    for operation in expected['oneOf']:
        fields = operation['properties']
        if fields['operation']['const'] == 'discover':
            fields['profile'] = {'const':'planar-reach-0.1'}
        if 'options' in fields:
            fields['options']['properties']['time_tolerance_s']['maximum'] = 1e-6
    check('request_payload_inheritance_exact_except_declared_changes',
          ROWS['agent-request.schema.json']['oneOf'] == expected['oneOf'])
    bundle = {'schema_version':'ontokin.bundle/0.1',
              'entry':{'filename':'synthetic.ok','source':'// schema shape only\n'},'modules':[]}
    patch = {'source_id':'entry','source_revision':REV,'element_id':['@source','entry'],
             'start_byte':0,'end_byte':0,'expected_text':'','replacement':'// shape\n'}
    extras = {
        'discover':{'profile':'planar-reach-0.1','limit':128},
        'create':{'bundle':bundle,'expected_program_revision':None,'requested_level':'constructed'},
        'edit':{'expected_program_revision':REV,'patches':[patch],'requested_level':'constructed'},
        'validate':{'program_revision':REV,'requested_level':'constructed'},
        'inspect':{'program_revision':REV,'selector':{'kind':'action'},'fields':['actions'],'limit':128,
                   'run_id':'run:synthetic','time':{'seconds':'1.5','side':'after'}},
        'evaluate':{'program_revision':REV,'run_id':None,'until_seconds':'1.5'},
        'reset':{'program_revision':REV},'status':{'target_request_id':'old'},
        'cancel':{'target_request_id':'old'},
        'export':{'program_revision':REV,'destination':'ontokin.glb/0.6','options':{'end':'0.25'}},
        'artifact':{'artifact_id':'artifact:synthetic','offset':0,'max_bytes':65536},
        'surface.mesh_page':{'program_revision':REV,'element_id':['shape','scene','arm'],'count':256},
    }
    requests = {}
    for name in names:
        request = {'schema_version':'ontokin.agent/0.6','project_id':'p','request_id':name,'operation':name,**extras[name]}
        requests[name] = request
        shape('request_'+name,'agent-request.schema.json',request)
    for name, change in [
        ('old_binding',{'schema_version':'ontokin.agent/0.5'}),
        ('host_reach',{'operation':'reach'}),('new_response_bytes',{'max_response_bytes':1000}),
        ('inspect_max_bytes',{'max_bytes':1000}),('raised_entry_budget',{'budgets':{'max_value_entries':100001}}),
        ('incomplete_time',{'time':{'seconds':'1.5'}}),('wrong_selector',{'selector':{'kind':'reach'}}),
    ]:
        shape('reject_request_'+name,'agent-request.schema.json',{**requests['inspect'],**change},False)
    shape('reject_discover_two_source_bindings','agent-request.schema.json',
          {**requests['discover'],'bundle':bundle,'program_revision':REV},False)
    shape('reject_old_destination','agent-request.schema.json',
          {**requests['export'],'destination':'ontokin.glb/0.5'},False)
    shape('reject_time_tolerance_one_over','agent-request.schema.json',
          {**requests['export'],'options':{'time_tolerance_s':1.0000000000000002e-6}},False)
    shape('reject_options_without_destination','agent-request.schema.json',
          {**requests['validate'],'options':{'end':'0.25'}},False)
    shape('reject_destination_at_constructed_level','agent-request.schema.json',
          {**requests['validate'],'destination':'ontokin.glb/0.6'},False)
    shape('reject_patch_extra_scope_bypass','agent-request.schema.json',
          {**requests['edit'],'patches':[{**patch,'ignore_authority':True}]},False)


def projection_checks():
    name = 'reach-projection.schema.json'
    for lifecycle in ('pending','running','paused','stopped','completed'):
        for context in ('agent','source_recording'):
            shape('projection_'+lifecycle+'_'+context,name,projection(lifecycle,context=context))
    shape('unrun_source_inspection',name,projection(sampled=False))
    candidate = projection(sampled=False)
    candidate.update(candidate_only=True,accepted_program_revision=HEAD_REV)
    shape('candidate_keeps_different_accepted_head',name,candidate)
    history = projection('completed')
    history['accepted_program_revision'] = HEAD_REV
    shape('historical_accepted_is_not_candidate',name,history)
    constructed = projection('pending')
    constructed['current']['value']['observation'].update(time_seconds='0',side='before',run_id=None,context_kind='constructed_initial')
    shape('constructed_before_zero',name,constructed)
    mutations = []
    def mutate(label, base, path, value):
        item = copy.deepcopy(base)
        here = item
        for part in path[:-1]:
            here = here[part]
        here[path[-1]] = value
        mutations.append((label,item))
    mutate('failed_current_goal',projection(),['current','value','goal_outcome'],'failed')
    mutate('pending_admission_targets',projection('pending'),['current','value','resolved_joint_targets_rad'],[0,0])
    mutate('partial_claim',projection(),['current','value','claimed_joint_ids'],[['one']])
    mutate('duplicate_claim',projection(),['current','value','claimed_joint_ids'],[['one'],['one']])
    mutate('paused_prediction',projection('paused'),['current','value','completion_time_seconds'],'2')
    mutate('paused_physical_motion',projection('paused'),['current','value','joint_rates_rad_per_s'],[1,0])
    mutate('stopped_own_motion',projection('stopped'),['current','value','action_joint_rates_rad_per_s'],[0,1])
    mutate('completed_own_motion',projection('completed'),['current','value','action_joint_rates_rad_per_s'],[1,0])
    mutate('running_terminal',projection(),['current','value','terminal_result'],projection('completed')['current']['value']['terminal_result'])
    mutate('stopped_satisfied',projection('stopped'),['current','value','goal_outcome'],'satisfied')
    mutate('completed_terminal_residual',projection('completed'),['current','value','terminal_result','position_residual_m'],2e-9)
    mutate('unrun_nonnull_value',projection(sampled=False),['current','value'],projection('pending')['current']['value'])
    mutate('run_without_run_id',projection(),['current','value','observation','run_id'],None)
    mutate('constructed_after_zero',constructed,['current','value','observation','side'],'after')
    mutate('constructed_later_clock',constructed,['current','value','observation','time_seconds'],'0.5')
    mutate('constructed_run_id',constructed,['current','value','observation','run_id'],'run:invented')
    mutate('recorded_service_acceptance',projection(context='source_recording'),['accepted_program_revision'],REV)
    mutate('recorded_fake_run',projection(context='source_recording'),['current','value','observation','run_id'],'run:invented')
    mutate('agent_recorded_observation',projection(),['current','value','observation','context_kind'],'recorded_prefix')
    mutate('accepted_without_head',projection(),['accepted_program_revision'],None)
    mutate('wrong_target_plane',projection(),['target','coordinates_m'],[1,1,0.1])
    for label,item in mutations:
        shape('reject_'+label,name,item,False)
    missing = projection()
    del missing['source_location']['source_revision']
    shape('reject_missing_source_span_revision',name,missing,False)
    shape('response_complete_action','agent-response.schema.json',envelope())
    for reason in ('source_is_unresolved','definition_has_no_occurrence_state'):
        shape('inherited_unavailable_actions_'+reason,'agent-response.schema.json',
              envelope(result={'items':[{'actions':{'available':False,'reason':reason}}]}))
    bad = envelope()
    del bad['result']['items'][0]['actions'][0]['chain']
    shape('response_reject_partial_reach_group','agent-response.schema.json',bad,False)
    initial = envelope(operation='create',result={'initial_state':{'time_seconds':'0','side':'before',
        'objects':{},'reaches':{'reach':constructed}}})
    initial['run_id'] = None
    shape('response_actual_constructed_shape','agent-response.schema.json',initial)
    bad = copy.deepcopy(initial)
    bad['result']['initial_state']['reaches']['reach'] = projection('pending')
    shape('response_reject_construction_as_run','agent-response.schema.json',bad,False)
    run = envelope(operation='evaluate',result={'run_state':{'run_id':'run:synthetic',
        'last_valid_state':{'objects':{},'reaches':{'reach':projection('completed')}}}})
    shape('response_actual_run_shape','agent-response.schema.json',run)
    bad = copy.deepcopy(run)
    bad['result']['run_state']['last_valid_state']['reaches']['reach'] = constructed
    shape('response_reject_run_as_construction','agent-response.schema.json',bad,False)
    wire('wire_reject_nonfinite',{'value':float('inf')},False)
    wire('wire_reject_unicode_surrogate',{'value':'\ud800'},False)


def diagnostic_checks():
    expected = {
        'reach_type':('OKL-E-TYPE','invalid','type'),
        'reach_frame':('OKL-E-REACH','invalid','elaboration'),
        'reach_chain':('OKL-E-REACH','unsupported','support'),
        'reach_domain':('OKL-E-REACH','unsupported','support'),
        'reach_claim_conflict':('OKL-E-REACH','invalid','admission'),
        'reach_unreachable':('OKL-E-REACH','invalid','admission'),
        'reach_singular':('OKL-E-REACH','invalid','admission'),
        'reach_limit':('OKL-E-REACH','invalid','admission'),
        'reach_numeric':('OKL-E-NUMERIC','numerical_failure','admission'),
        'reach_resource':('OKL-E-RESOURCE','resource_limit','support'),
    }
    for subcode,(code,category,phase) in expected.items():
        data = {'schema_version':'ontokin.diagnostic/0.2','program_revision':REV,
            'source_id':'entry','source_revision':REV,'run_id':None,'code':code,'severity':'error',
            'category':category,'phase':phase,'message':'Synthetic shape probe.',
            'time':None,'primary':{'source_id':'entry','source_revision':REV,'file':'shape.ok',
                'start_byte':0,'end_byte':1,'element_id':['shape','scene','reach']},
            'related':[],'rule_ids':['REACH-001'],'details':{'reach_code':subcode},
            'repair':None,'blocks':['evaluated','delivered']}
        shape('diagnostic_'+subcode,'reach-diagnostic.schema.json',data)
        shape('reject_category_'+subcode,'reach-diagnostic.schema.json',
              {**data,'category':'goal_failure'},False)
        shape('reject_code_'+subcode,'reach-diagnostic.schema.json',
              {**data,'code':'OKL-E-OTHER'},False)
        shape('reject_phase_'+subcode,'reach-diagnostic.schema.json',
              {**data,'phase':'goal'},False)
    bad = copy.deepcopy(data)
    bad['details']['reach_code'] = 'reach_conflict'
    shape('reject_unknown_subcode_alias','reach-diagnostic.schema.json',bad,False)
    response = envelope()
    response['diagnostics'] = [bad]
    shape('response_reject_wrong_diagnostic_taxonomy','agent-response.schema.json',response,False)
    response['diagnostics'] = []
    response['result']['diagnostics'] = [bad]
    shape('response_reject_wrong_nested_diagnostic_taxonomy','agent-response.schema.json',response,False)
    response = envelope(operation='evaluate',result={'run_state':{'failure':{'diagnostic':bad}}})
    shape('response_reject_wrong_failure_diagnostic_taxonomy','agent-response.schema.json',response,False)


def recording_checks():
    basis = {'name':'synthetic-algorithm','version':'0','implementation_sha256':REV,
             'method':'Synthetic shape, not a proof or executed implementation.','derivation_sha256':REV}
    interval = {name:0 for name in ROWS['quantization.schema.json']['properties']['interval_certificates']['items']['properties']}
    interval.update(left_key_index=0,right_key_index=1,carrier=occurrence('arm'),source_phase_indices=[0],
                    h_authored_seconds={'numerator':'1','denominator':'2'},
                    h_stored_seconds={'numerator':'1','denominator':'2'})
    quant = {'schema_version':'ontokin.reach-quantization/0.1','rotation_interpolation':'shortest_arc_slerp',
        'clock_conversion':'binary32_rne_ties_to_even_from_exact_rational',
        'position_tolerance_m':.001,'rotation_tolerance_rad':.001,'time_tolerance_s':1e-6,
        'source_numeric_bound_basis':copy.deepcopy(basis),'destination_numeric_bound_basis':copy.deepcopy(basis),
        'retained_keys':[{'authored_seconds':{'numerator':'1','denominator':'2'},'stored_seconds':.5,
                          'stored_binary32_bits':'3f000000','semantic_boundary':True}],
        'interval_certificates':[interval],'all_values_independently_recomputed':True,
        'unknown_error_bound_policy':'reject',
        'certificate_scope':'specified source and supplied bytes; separately identified destination numeric behavior'}
    shape('quantization_complete_shape','quantization.schema.json',quant)
    for field in ('enclosing_carrier_acceleration_bound_m_per_s2','carrier_position_bound_m'):
        bad = copy.deepcopy(quant)
        del bad['interval_certificates'][0][field]
        shape('reject_missing_'+field,'quantization.schema.json',bad,False)
    for field in ('clock_conversion','source_numeric_bound_basis','destination_numeric_bound_basis'):
        bad = copy.deepcopy(quant)
        del bad[field]
        shape('reject_missing_'+field,'quantization.schema.json',bad,False)
    bad = copy.deepcopy(quant)
    bad['clock_conversion'] = 'binary64_then_binary32'
    shape('reject_double_rounding_policy','quantization.schema.json',bad,False)
    bad = copy.deepcopy(quant)
    del bad['retained_keys'][0]['stored_binary32_bits']
    shape('reject_missing_actual_clock_bits_field','quantization.schema.json',bad,False)
    bad = copy.deepcopy(quant)
    bad['source_numeric_bound_basis'].pop('implementation_sha256')
    shape('reject_unidentified_source_numeric_implementation','quantization.schema.json',bad,False)
    release = {'program_revision':REV,'source_location':{'source_id':'entry','source_revision':REV,
        'start_byte':0,'end_byte':1},'sequence_index':0,'time_seconds':'1.5',
        'grip':occurrence('arm.grip'),'target':occurrence('payload'),
        'reach_contributors':[{'action':occurrence('reach'),'shoulder':occurrence('arm.shoulder'),
            'elbow':occurrence('arm.elbow'),'joint_coordinates_rad':[0.2,0.3],'joint_rates_rad_per_s':[.2,.25]}],
        'incoming_pose_world':{'position_m':[1,1,0],'orientation_wxyz':[1,0,0,0]},
        'incoming_linear_velocity_world_m_per_s':[1,2,3],
        'incoming_angular_velocity_world_rad_per_s':[0,0,.45]}
    boundary = {'source_seconds':'1.5','incoming_releases':[release]}
    for side in ('before','after'):
        for group in ('joint_states','action_states','pose_authorities','impulse_states','force_states'):
            boundary[group+'_'+side] = {}
        reach = projection(context='source_recording')
        reach['current']['value']['observation']['side'] = side
        boundary['reach_states_'+side] = {'reach':reach}
    metadata = {'target_contract':'ontokin.glb/0.6','schema_version':'0.6','profile':'planar-reach-0.1',
        'transform_policy':'all_nodes_are_roots_with_baked_world_poses',
        'program':{'revision':REV,'manifest':{'schema_version':'ontokin.bundle/0.1','entry_source_id':'entry',
            'units':[{'source_id':'entry','source_revision':REV,'filename':'shape.ok','package_id':None,'version':None}]}},
        'reach_profile':{'schema_version':'ontokin.reach-recording/0.1','source_profile':'planar-reach-0.1',
            'motion_model':'two_prescribed_planar_hinges','rotation_interpolation':'shortest_arc_slerp',
            'goal_residual_max_m':1e-9,'bound_chain_tuple_max':32,'named_reach_action_max':128,'live_solver_embedded':False},
        'boundary_states':[boundary],'reach_quantization':quant}
    shape('complete_before_after_recording_shape','glb-metadata.schema.json',metadata)
    for field in ('reach_states_before','force_states_before','incoming_releases'):
        bad = copy.deepcopy(metadata)
        del bad['boundary_states'][0][field]
        shape('reject_missing_boundary_'+field,'glb-metadata.schema.json',bad,False)
    for field in ('source_location','reach_contributors','incoming_linear_velocity_world_m_per_s',
                  'incoming_angular_velocity_world_rad_per_s','incoming_pose_world'):
        bad = copy.deepcopy(metadata)
        del bad['boundary_states'][0]['incoming_releases'][0][field]
        shape('reject_missing_release_'+field,'glb-metadata.schema.json',bad,False)
    bad = copy.deepcopy(metadata)
    bad['boundary_states'][0]['reach_states_before']['reach']['current']['value']['observation']['side'] = 'after'
    shape('reject_swapped_recording_side','glb-metadata.schema.json',bad,False)
    bad = copy.deepcopy(metadata)
    bad['boundary_states'][0]['incoming_releases'][0]['reach_contributors'][0].pop('joint_rates_rad_per_s')
    shape('reject_omitted_incoming_joint_rates','glb-metadata.schema.json',bad,False)


def synthetic_budget_check():
    # This is a deliberately synthetic shape with P24's fixed cardinality/query.
    # It does not calculate the real response or construction-work requirement.
    items = []
    for index in range(128):
        name = 'reach' if index == 0 else f'pending_{index:03d}'
        p = projection('running' if index == 0 else 'pending')
        p['element_id'][-1] = name
        p['description_identity'][-1] = name
        items.append({'element_id':copy.deepcopy(p['element_id']),'path':name,'kind':'action','actions':[p]})
    context = {'program_revision':REV,'run_id':'run:synthetic','time_seconds':'1.5','side':'after',
               'frame':'world','selector':{'kind':'action'},'fields':['actions']}
    response = envelope(result={'schema_version':'ontokin.program-runtime/0.1','program_revision':REV,
        'requested_level':None,'achieved_level':'represented','outcome':'valid','diagnostics':[],
        'source_manifest':{'schema_version':'ontokin.bundle/0.1','entry_source_id':'entry','units':[
            {'source_id':'entry','source_revision':REV,'filename':'synthetic.ok','package_id':None,'version':None}]},
        'items':items,'total':128,'offset':0,'next_offset':None,'truncated':False,'index_complete':True,
        'context':context,'sample_context':copy.deepcopy(context),'implementation':IMPL})
    shape('synthetic_full_128_action_envelope','agent-response.schema.json',response)
    measured = JSON_LIMITS.measure_json(response)
    check('synthetic_full_envelope_fits_default_global_limits',measured['entries'] <= 100000 and measured['bytes'] <= 4194304)
    exact = JSON_LIMITS.measure_json(response,max_entries=measured['entries'])
    check('synthetic_counter_equal_limit',exact == measured)
    try:
        JSON_LIMITS.measure_json(response,max_entries=measured['entries']-1)
        rejected = False
    except JSON_LIMITS.JSONLimitError as error:
        rejected = error.details['budget'] == 'logical_json_entries'
    check('synthetic_counter_one_below_limit',rejected)
    return {'scope':'synthetic schema/cardinality only; not actual Q03 execution',
            'query':{'selector':{'kind':'action'},'fields':['actions'],'limit':128,
                     'time_seconds':'1.5','side':'after'},
            'complete_envelope_measurement':measured,'actual_protocol_N':None,
            'actual_constructor_cumulative_entries':None,'actual_publication_guard_executed':False}


def supplemental_checks(directory):
    if directory is None:
        return {'status':'pending','reason':'Supplemental reconstructed fixtures are a separately owned dependency.'}
    data = json.loads((directory/'acceptance.json').read_text())
    count = sides = 0
    for case in data['source_cases']:
        for sample in case['samples']:
            sides += 1
            for path,item in sample['reaches'].items():
                shape(f"supplement_{case['id']}_{sides}_{path}",'reach-projection.schema.json',item)
                count += 1
    check('supplement_51_sides_86_complete_projections',sides == 51 and count == 86)
    return {'status':'checked','sample_sides':sides,'complete_projections':count,
            'acceptance_sha256':sha((directory/'acceptance.json').read_bytes()),
            'scope':'stored expectation shape only; no source or Agent evaluation'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--supplements-dir',type=Path)
    args = parser.parse_args()
    schema_checks()
    request_checks()
    projection_checks()
    diagnostic_checks()
    recording_checks()
    budget = synthetic_budget_check()
    supplements = supplemental_checks(args.supplements_dir)
    paths = [PROPOSAL/'author_schema_drafts.py',PROPOSAL/'agent-operations.md',Path(__file__),
             PROPOSAL/'generated-members.json',REPO/'ontokin/json_limits.py']
    paths += sorted((PROPOSAL/'schema-drafts').glob('*.json'))
    paths += [PROPOSAL.parent/name for name in AUTHOR.INHERITED_INPUTS]
    inputs = [{'path':str(p.relative_to(REPO)),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())}
              for p in sorted(paths)]
    failed = [row for row in CHECKS if row['status'] != 'passed']
    report = {'schema_version':'ontokin.proposed-reach-schema-check/0.2',
        'reconstruction_id':AUTHOR.RECONSTRUCTION,'status':'passed' if not failed else 'failed',
        'scope':'pure proposal schema, inherited-envelope and synthetic counting checks',
        'historical_schema_equivalence_claimed':False,'started_at':START,
        'finished_at':datetime.now(timezone.utc).isoformat(),
        'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
        'source_tree':subprocess.check_output(['git','rev-parse','HEAD^{tree}'],cwd=REPO,text=True).strip(),
        'worktree_changes_at_check':subprocess.check_output(['git','status','--porcelain=v1'],cwd=REPO,text=True).splitlines(),
        'command':[sys.executable,*sys.argv],
        'environment':{'python':sys.version,'platform':platform.platform(),
                       'jsonschema':version('jsonschema'),'referencing':version('referencing')},
        'inputs':inputs,'check_count':len(CHECKS),'failed_count':len(failed),'checks':CHECKS,
        'synthetic_budget':budget,'supplementary_shape_checks':supplements,
        'not_executed':['Agent service','SQLite','source construction/evaluation','GLB writer/reader',
                        'browser','full regression suite','archives','actual Q03 publication guard'],
        'runtime_support_claimed':False,'adoption_claimed':False}
    raw = json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+'\n'
    if args.output:
        if args.output.exists():
            raise SystemExit('Refusing to overwrite an earlier check report: '+str(args.output))
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(raw)
    print(json.dumps({'status':report['status'],'checks':len(CHECKS),'failed':failed,
                      'synthetic_budget':budget,'supplementary_shape_checks':supplements},sort_keys=True))
    return bool(failed)


if __name__ == '__main__':
    raise SystemExit(main())
