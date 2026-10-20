#!/usr/bin/env python3
"""Reproduce proposed Agent/GLB0.6 schema drafts; no runtime or fixture evaluation."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
LANGUAGE = HERE.parent
ROOT = 'https://omegapy.github.io/OntoKin/proposals/planar-reach-v0.1/'
DIALECT = 'https://json-schema.org/draft/2020-12/schema'
VERSION = '0.1.0-draft.2'


def sha(raw):
    return 'sha256:' + hashlib.sha256(raw).hexdigest()


def obj(properties, required=None, **extra):
    return {'type':'object','properties':properties,'required':list(properties) if required is None else required,
            'additionalProperties':False, **extra}


def array(items, maximum, minimum=0, **extra):
    return {'type':'array','items':items,'minItems':minimum,'maxItems':maximum, **extra}


def ref(name):
    return {'$ref': ROOT+'common.schema.json#/$defs/'+name}


def nullable(schema):
    return {'oneOf':[schema,{'type':'null'}]}


def document(filename, title, shape, description):
    return {'$schema':DIALECT,'$id':ROOT+filename,'title':title,
            '$comment':'Proposed OK-LANG-006 '+VERSION+'; no adoption or implementation claim.',
            'description':description, **shape}


def schemas():
    number = {'type':'number'}
    positive = {'type':'number','exclusiveMinimum':0}
    nonnegative = {'type':'number','minimum':0}
    integer = {'type':'integer','minimum':0}
    text = {'type':'string','minLength':1,'maxLength':4096}
    identity = array({'type':'string','minLength':1,'maxLength':200},256,1)
    vector = array(number,3,3)
    pair = array({'type':'number','minimum':-3.141592653589793,'maximum':3.141592653589793},2,2)
    defs = {
        'revision':{'type':'string','pattern':'^sha256:[0-9a-f]{64}$'},
        'element_id':identity,
        'path':text,
        'vector3':vector,
        'quaternion_wxyz':array(number,4,4),
        'angle_pair':pair,
        'rate_pair':array(number,2,2),
        'time':{'type':'string','pattern':'^[0-9]+(?:\\.[0-9]+)?$','maxLength':4096},
        'rational_time':obj({'numerator':{'type':'string','pattern':'^(0|[1-9][0-9]*)$','maxLength':4096},
                             'denominator':{'type':'string','pattern':'^[1-9][0-9]*$','maxLength':4096}}),
        'occurrence_ref':obj({'path':ref('path'),'element_id':ref('element_id')}),
        'site_frame':obj({'path':ref('path'),'site_element_id':ref('element_id')}),
        'source_location':obj({'source_id':text,'source_revision':ref('revision'),
                                'start_byte':integer,'end_byte':integer}),
        'pose':obj({'position_m':ref('vector3'),'orientation_wxyz':ref('quaternion_wxyz')}),
        'target':obj({'type':{'const':'Point3'},'frame':ref('site_frame'),
                      'coordinates_m':{'type':'array','minItems':3,'maxItems':3,
                          'prefixItems':[{'type':'number','minimum':-8,'maximum':8},
                                         {'type':'number','minimum':-8,'maximum':8},{'const':0}], 'items':False}}),
        'chain':obj({'shoulder':ref('occurrence_ref'),'elbow':ref('occurrence_ref'),'tip':ref('occurrence_ref'),
                     'base_frame':ref('site_frame'),'lengths_m':array({'type':'number','minimum':.125,'maximum':4},2,2),
                     'closed_limits_rad':obj({'shoulder':ref('angle_pair'),'elbow':ref('angle_pair')})}),
        'observation':obj({'time_seconds':ref('time'),'side':{'enum':['before','after']},
                           'run_id':nullable(text),'context_kind':{'enum':['run_sample','constructed_initial','recorded_prefix']}}),
    }
    source_unit = obj({'source_id':text,'source_revision':ref('revision'),'filename':text,
                      'package_id':nullable(text),'version':nullable({'type':'string','pattern':'^[0-9]+\\.[0-9]+\\.[0-9]+$'})})
    defs['source_manifest'] = obj({'schema_version':{'const':'ontokin.bundle/0.1'},'entry_source_id':{'const':'entry'},
                                    'units':array(source_unit,17,1)})
    terminal = obj({'outcome':{'enum':['satisfied','interrupted']},'time_seconds':ref('time'),
                    'position_residual_m':nonnegative,'joint_coordinates_rad':ref('angle_pair'),
                    'tip_pose_base':ref('pose')})
    state = obj({
        'observation':ref('observation'),'lifecycle':{'enum':['pending','running','paused','stopped','completed']},
        'goal_outcome':{'enum':['pending','active','interrupted','satisfied']},
        'resolved_joint_targets_rad':nullable(ref('angle_pair')),'start_coordinates_rad':nullable(ref('angle_pair')),
        'start_time_seconds':nullable(ref('time')),'elapsed_seconds':nullable(ref('time')),
        'completion_time_seconds':nullable(ref('time')),'joint_coordinates_rad':ref('angle_pair'),
        'joint_rates_rad_per_s':ref('rate_pair'),'action_joint_rates_rad_per_s':ref('rate_pair'),
        'claimed_joint_ids':array(ref('element_id'),2,uniqueItems=True),
        'current_residual_m':nullable(nonnegative),'tip_pose_base':ref('pose'),'tip_pose_world':ref('pose'),
        'current_world_target_m':ref('vector3'),'terminal_result':nullable(terminal),
    })
    pending = ['resolved_joint_targets_rad','start_coordinates_rad','start_time_seconds','elapsed_seconds',
               'completion_time_seconds','current_residual_m','terminal_result']
    state['allOf'] = []
    for lifecycle, outcome in [('pending','pending'),('running','active'),('paused','active'),('stopped','interrupted'),('completed','satisfied')]:
        properties = {'goal_outcome':{'const':outcome},'claimed_joint_ids':{'minItems':2,'maxItems':2} if lifecycle in ('running','paused') else {'maxItems':0}}
        if lifecycle == 'pending':
            properties.update({name:{'type':'null'} for name in pending})
        else:
            properties.update({'resolved_joint_targets_rad':ref('angle_pair'),'start_coordinates_rad':ref('angle_pair'),
                               'start_time_seconds':ref('time'),'elapsed_seconds':ref('time'),'current_residual_m':nonnegative})
        if lifecycle in ('pending','paused','stopped','completed'):
            properties['action_joint_rates_rad_per_s'] = {'const':[0,0]}
        if lifecycle == 'paused':
            properties['joint_rates_rad_per_s'] = {'const':[0,0]}
        if lifecycle in ('paused','stopped'):
            properties['completion_time_seconds'] = {'type':'null'}
        elif lifecycle in ('running','completed'):
            properties['completion_time_seconds'] = ref('time')
        if lifecycle in ('running','paused'):
            properties['terminal_result'] = {'type':'null'}
        if lifecycle in ('stopped','completed'):
            properties['terminal_result'] = {'type':'object','properties':{'outcome':{'const':outcome}}}
        if lifecycle == 'completed':
            properties['terminal_result']['properties']['position_residual_m'] = {'type':'number','minimum':0,'maximum':1e-9}
        state['allOf'].append({'if':{'properties':{'lifecycle':{'const':lifecycle}},'required':['lifecycle']},
                              'then':{'properties':properties}})
    defs['reach_state'] = state
    current = {'oneOf':[
        obj({'available':{'const':False},'reason':{'const':'run_required'},'value':{'type':'null'}}),
        obj({'available':{'const':True},'reason':{'type':'null'},'value':ref('reach_state')})]}
    projection = obj({'kind':{'const':'reach_planar'},'element_id':ref('element_id'),'description_identity':ref('element_id'),
        'program_revision':ref('revision'),'accepted_program_revision':nullable(ref('revision')),
        'candidate_only':nullable({'type':'boolean'}),'context_origin':{'enum':['agent','source_recording']},
        'source_location':ref('source_location'),'channel':{'const':'joint_coordinates'},
        'chain':ref('chain'),'target':ref('target'),'branch':{'enum':['elbow_positive','elbow_negative']},
        'duration_seconds':ref('time'),'current':current})
    projection['allOf'] = [
        {'if':{'properties':{'context_origin':{'const':'agent'}}},
         'then':{'properties':{'candidate_only':{'type':'boolean'}}}},
        {'if':{'properties':{'context_origin':{'const':'source_recording'}}},
         'then':{'properties':{'accepted_program_revision':{'type':'null'},'candidate_only':{'type':'null'}}}},
    ]
    rows = {'common.schema.json':document('common.schema.json','Proposed bounded reach values',{'$defs':defs},
            'All JSON numbers must additionally be finite. Canonical clocks, reduced rational times, source closure, equality of referenced identities, closed-limit order and unit quaternion meaning require independent semantic validation.'),
        'reach-projection.schema.json':document('reach-projection.schema.json','Proposed complete source-bound reach action projection',projection,
            'One inspect actions[] record or snapshot reaches[path] record. Unrun inspection is unavailable rather than fabricated pending state. A sampled pending state has null admission fields. Failed admission is a diagnostic on the failed boundary; accepted projection is unchanged.')}

    inherited_request = LANGUAGE/'agent-v0.5/request.schema.json'
    inherited_response = LANGUAGE/'agent-v0.5/response.schema.json'
    def rebound(path, kind):
        raw = path.read_text().replace('ontokin.agent/0.5','ontokin.agent/0.6').replace('ontokin.glb/0.5','ontokin.glb/0.6')
        data = json.loads(raw)
        data['$id'] = ROOT+'agent-'+kind+'.schema.json'
        data['title'] = 'Proposed planar reach Agent/0.6 '+kind
        data['description'] = 'Unadopted OK-LANG-006 draft interface. Inherited Agent/0.5 shape with explicit Agent/GLB0.6 binding and the additions recorded in agent-operations.md. No runtime support follows from shape validity.'
        data['$comment'] = 'Proposed '+VERSION+'; inherited schema SHA-256 '+sha(path.read_bytes())
        return data
    request = rebound(inherited_request,'request')
    for operation in request['oneOf']:
        fields = operation['properties']
        if fields['operation']['const'] == 'discover':
            fields['profile'] = {'const':'planar-reach-0.1'}
        if 'options' in fields:
            fields['options']['properties']['time_tolerance_s']['maximum'] = 1e-6
    rows['agent-request.schema.json'] = request
    response = rebound(inherited_response,'response')
    reach_map = {'type':'object','maxProperties':128,
                 'additionalProperties':{'$ref':ROOT+'reach-projection.schema.json'}}
    response['$defs']['force_sample']['properties']['reaches'] = copy.deepcopy(reach_map)
    response['$defs']['force_sample']['required'].append('reaches')
    for clause in response['allOf']:
        if clause.get('if',{}).get('properties',{}).get('operation',{}).get('const') == 'inspect':
            item = clause['then']['properties']['result']['properties']['items']['items']
            item['properties']['actions'] = {'type':'array','maxItems':100000,'items':{
                'type':'object','required':['kind'],'allOf':[{'if':{'properties':{'kind':{'const':'reach_planar'}},'required':['kind']},
                    'then':{'$ref':ROOT+'reach-projection.schema.json'}}]}}
    rows['agent-response.schema.json'] = response

    interval = obj({
        'left_key_index':{'type':'integer','minimum':0,'maximum':9998},
        'right_key_index':{'type':'integer','minimum':1,'maximum':9999},'carrier':ref('occurrence_ref'),
        'source_phase_indices':array({'type':'integer','minimum':0,'maximum':99999},100000,1,uniqueItems=True),
        'h_authored_seconds':ref('rational_time'),'h_stored_seconds':ref('rational_time'),
        'landmark_radius_m':nonnegative,'angular_speed_bound_rad_per_s':nonnegative,
        'carrier_acceleration_bound_m_per_s2':nonnegative,'enclosing_carrier_speed_bound_m_per_s':nonnegative,
        'enclosing_angular_speed_bound_rad_per_s':nonnegative,'max_endpoint_time_shift_s':nonnegative,
        'max_endpoint_position_error_m':nonnegative,'max_endpoint_unit_quaternion_error':nonnegative,
        'stored_quaternion_arc_upper_rad':{'type':'number','minimum':0,'maximum':0.7853981633974483},
        'source_numeric_position_bound_m':nonnegative,'source_numeric_rotation_bound_rad':nonnegative,
        'destination_numeric_position_bound_m':nonnegative,'destination_numeric_rotation_bound_rad':nonnegative,
        'local_vertex_error_bound_m':nonnegative,'ideal_position_bound_m':nonnegative,
        'ideal_rotation_bound_rad':nonnegative,'unit_quaternion_difference_bound':{'type':'number','minimum':0,'maximum':.5},
        'total_position_bound_m':nonnegative,'total_rotation_bound_rad':nonnegative})
    quantization = obj({
        'schema_version':{'const':'ontokin.reach-quantization/0.1'},'rotation_interpolation':{'const':'shortest_arc_slerp'},
        'position_tolerance_m':positive,'rotation_tolerance_rad':positive,
        'time_tolerance_s':{'type':'number','exclusiveMinimum':0,'maximum':1e-6},
        'source_numeric_bound_basis':obj({'method':text,'derivation_sha256':ref('revision')}),
        'destination_numeric_bound_basis':obj({'name':text,'version':text,'implementation_sha256':ref('revision'),
                                                'method':text,'derivation_sha256':ref('revision')}),
        'retained_keys':array(obj({'authored_seconds':ref('rational_time'),'stored_seconds':nonnegative,
                                  'semantic_boundary':{'type':'boolean'}}),10000,1),
        'interval_certificates':array(interval,100000),
        'all_values_independently_recomputed':{'const':True},
        'unknown_error_bound_policy':{'const':'reject'},
        'certificate_scope':{'const':'specified source and supplied bytes; separately identified destination numeric behavior'}})
    rows['quantization.schema.json'] = document('quantization.schema.json','Proposed source/stored-time reach error certificate',quantization,
        'The document quantization.md defines every quantity, proof inequality and rejection condition. Claimed true/recomputed fields do not prove a certificate: the independent reader must derive it from exact source and actual bytes before acceptance. All repeated entries consume inherited aggregate budgets.')
    after_observation = {'properties':{'side':{'const':'after'},'context_kind':{'const':'recorded_prefix'},
                                       'run_id':{'type':'null'}}}
    after_current = {'properties':{'available':{'const':True},
                                   'value':{'properties':{'observation':after_observation}}}}
    after_projection = {'allOf':[{'$ref':ROOT+'reach-projection.schema.json'},
        {'properties':{'context_origin':{'const':'source_recording'},'current':after_current}}]}
    boundary = obj({'source_seconds':ref('time'),'joint_states_after':{'type':'object'},'action_states_after':{'type':'object'},
        'pose_authorities_after':{'type':'object'},
        'impulse_states_after':{'type':'object','additionalProperties':{'$ref':'https://ontokin.org/schemas/impulse-v0.1/impulses.schema.json'}},
        'force_states_after':{'type':'object','additionalProperties':{'$ref':'https://ontokin.org/schemas/force-v0.1/forces.schema.json'}},
        'reach_states_after':{'type':'object','maxProperties':128,'additionalProperties':after_projection}})
    metadata = {'type':'object','properties':{
        'target_contract':{'const':'ontokin.glb/0.6'},'schema_version':{'const':'0.6'},'profile':{'const':'planar-reach-0.1'},
        'transform_policy':{'const':'all_nodes_are_roots_with_baked_world_poses'},
        'program':{'type':'object','properties':{'revision':ref('revision'),'manifest':ref('source_manifest')},
                   'required':['revision','manifest']},
        'reach_profile':obj({'schema_version':{'const':'ontokin.reach-recording/0.1'},'source_profile':{'const':'planar-reach-0.1'},
            'motion_model':{'const':'two_prescribed_planar_hinges'},'rotation_interpolation':{'const':'shortest_arc_slerp'},
            'goal_residual_max_m':{'const':1e-9},'bound_chain_tuple_max':{'const':32},'named_reach_action_max':{'const':128},
            'live_solver_embedded':{'const':False}}),
        'boundary_states':array(boundary,100000),
        'reach_quantization':{'$ref':ROOT+'quantization.schema.json'}},
        'required':['target_contract','schema_version','profile','transform_policy','program','reach_profile','boundary_states','reach_quantization']}
    rows['glb-metadata.schema.json'] = document('glb-metadata.schema.json','Proposed GLB0.6 metadata additions and complete boundary records',metadata,
        'Applies to document.extras.ontokin under the inherited exporter layout. This schema constrains the new reach additions and complete boundary projections. All other inherited source, surface/PBR, force, impulse, authority, geometry and active-scene rules still require their existing independent byte validators; unconstrained inherited fields are not exemptions.')
    return rows


def build(destination):
    destination.mkdir(parents=True,exist_ok=True)
    members=[]
    for name, data in sorted(schemas().items()):
        raw=(json.dumps(data,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()
        (destination/name).write_bytes(raw)
        members.append({'path':name,'bytes':len(raw),'sha256':sha(raw)})
    record={'schema_version':'ontokin.proposed-reach-schema-members/0.1','status':'proposed_not_adopted',
        'proposal_version':VERSION,'members':members,
        'inherited_inputs':[{'path':'../agent-v0.5/'+name,'sha256':sha((LANGUAGE/'agent-v0.5'/name).read_bytes())}
                            for name in ('request.schema.json','response.schema.json')],
        'author_script_sha256':sha(Path(__file__).read_bytes()),
        'unchanged_source_corpus_inventory_sha256':sha((HERE/'generated-members.json').read_bytes())}
    (destination/'schema-drafts-manifest.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
    return record


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,default=HERE/'schema-drafts')
    args=parser.parse_args()
    result=build(args.output_dir)
    print(json.dumps({'status':result['status'],'schema_count':len(result['members'])}))
