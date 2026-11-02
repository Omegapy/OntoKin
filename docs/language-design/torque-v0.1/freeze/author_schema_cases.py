#!/usr/bin/env python3
"""Exact closed-shape and semantic/provenance adversarial input recipes."""
from __future__ import annotations
from copy import deepcopy
import json
from author_inputs import ROOT, write


def main():
    states=json.loads((ROOT/'state-expectations.json').read_text())
    first=next(c for c in states['cases'] if c['case']=='p01-spin-up')
    row=next(r for r in first['observations'] if r['time_seconds']=='0' and r['side']=='after')
    latched=deepcopy(row['exact_fields'])
    latched.update(angular_error_bound_rad={'numerator':'1','denominator':str(2**36)},angular_speed_error_bound_rad_per_s={'numerator':'1','denominator':str(2**36)})
    prototypes={'empty':states['null_state_for_unlatched_objects'],'latched':latched}
    cases=[]
    def case(name,prototype,operation,path,value=None,schema=False,semantic=False,why=''):
        cases.append({'id':name,'prototype':prototype,'operation':operation,'path':path,'value':value,'expected_schema_accepts':schema,'expected_semantic_accepts':semantic,'reason':why})
    for key in latched: case('missing-'+key,'latched','remove','/'+key,why='Complete state projections are closed and require all15fields.')
    case('extra-field','latched','add','/hidden_torque',0)
    case('bad-axis','latched','replace','/axis','world_q')
    case('bool-net','latched','replace','/net_torque_n_m',True)
    case('bool-count','latched','replace','/started_count',True)
    case('negative-count','latched','replace','/completed_count',-1)
    case('unlatched-nonnull-alpha','empty','replace','/angular_acceleration_rad_per_s2',0)
    case('legacy-anchor','empty','replace','/rotation_anchor_seconds','0')
    case('split-null-anchor','latched','replace','/rotation_anchor_seconds',None)
    case('latched-null-reference','latched','replace','/angular_acceleration_reference_rad_per_s2',None)
    case('latched-zero-starts','latched','replace','/started_count',0)
    case('completion-count-exceeds-starts','latched','replace','/completed_count',2,schema=True,why='Complete source ledger, not shape alone, determines counts.')
    case('duplicate-active','latched','append-copy','/active/0',schema=True,why='Exact active-set membership must reject duplicate source identity.')
    case('fake-source-revision','latched','replace','/active/0/source_location/source_revision','sha256:'+'0'*64,schema=True)
    case('fake-program-revision','latched','replace','/active/0/program_revision','sha256:'+'0'*64,schema=True)
    case('fake-target','latched','replace','/active/0/target_path','sibling',schema=True)
    case('fake-element-key','latched','replace','/active/0/torque_element_id/3','different',schema=True)
    case('wrong-span','latched','replace','/active/0/operand_location/start_byte',0,schema=True)
    case('wrong-end-clock','latched','replace','/active/0/completion_time_seconds','1',schema=True)
    case('negative-zero-rational','latched','replace','/angular_acceleration_reference_rad_per_s2/numerator','-0',schema=True,why='The shape deliberately leaves canonical sign/reduction to the independent semantic reader.')
    case('nonreduced-rational','latched','replace','/angular_error_bound_rad',{'numerator':'2','denominator':'2'},schema=True)
    case('rational-bit-cap','latched','replace','/angular_error_bound_rad/numerator','9'*9865,schema=True,why='9865decimal digits fit the schema string bound but this actual integer exceeds32768bits. Prospective guard must refuse before unbounded parse/allocation.')
    case('negative-zero-scalar','latched','replace','/net_torque_n_m',-0.0,schema=True,why='Canonical published zero is positive; native signed-zero semantics are not supplied by JSON Schema.')
    for field in first['source_records'][0]:
        case('record-missing-'+field,'latched','remove','/active/0/'+field)
    case('record-extra','latched','add','/active/0/unbounded_note','no')
    write('schema-cases.json',{'schema_version':'ontokin.torque-independent-schema-cases/1',
      'schema_reference':'../torques.schema.json','candidate_output_used':False,
      'prototype_status':'Explicit design-only shape examples constructed from frozen input expectations. They are not observed Agent responses; the chosen positive rational error allowance is not a measured implementation bound.',
      'prototypes':prototypes,'prototype_expected_schema_accepts':{'empty':True,'latched':True},'cases':cases,
      'required_outer_checks':['Complete available .22 object state requires torques; unavailable definition/source-only states retain inherited shapes and cannot fabricate it.','Successful source field on an object occurrence requires complete torque_intervals, ordered by activation/sequence.','Every full response validates the .22 response and diagnostic schemas before semantic identities are checked.','Closed JSON schema acceptance never replaces native finite scalar/type, exact source/pin, chronology, aggregate, rational reduction/bit, authority or artifact verification.']})
    transport=[]
    def tr(name,path,operation,value,message=None):
        transport.append({'id':name,'base_request':{'schema_version':'ontokin.agent/0.22','project_id':'c090-transport-'+name,'request_id':'c090-transport-'+name,'operation':'create','bundle':{'$bundle_file':'workflow-agent-base.files.json'},'expected_program_revision':None,'requested_level':'constructed'},'materialize_before_mutation':True,'path':path,'mutation':operation,'value':value,'expected_status':'rejected','expected_code':'OKA-E-REQUEST','exact_inherited_message':message,'accepted_revision_run_artifact_created':False})
    tr('wrong-png-digest','/bundle/assets/0/sha256','replace','sha256:'+'0'*64,'Asset sha256 does not match its exact supplied bytes.')
    tr('wrong-media','/bundle/assets/0/media_type','replace','image/jpeg','Asset media_type must be image/png.')
    tr('base64-whitespace','/bundle/assets/0/data_base64','append','\n','Asset data_base64 is not canonical padded base64.')
    tr('duplicate-asset','/bundle/assets','append-copy-first',None,'Two supplied images cannot have the same asset_id.')
    tr('asset-extra-field','/bundle/assets/0','add-member',{'unexpected':0})
    tr('missing-assets','/bundle','remove-member','assets')
    tr('wrong-bundle-version','/bundle/schema_version','replace','ontokin.bundle/0.1')
    tr('apply-torque-rpc','/operation','replace','apply_torque')
    tr('mutable-torque-request','/','add-member',{'torque_n_m':2})
    tr('boolean-operation-cap','/','add-member',{'budgets':{'max_operations':True}})
    tr('zero-operation-cap','/','add-member',{'budgets':{'max_operations':0}})
    tr('fractional-operation-cap','/','add-member',{'budgets':{'max_operations':1.5}})
    write('agent/transport-cases.json',{'schema_version':'ontokin.torque-independent-transport-cases/1','candidate_output_used':False,
      'host_policy':{'max_operations':1000000,'max_elapsed_ms':30000},'cases':transport,
      'independent_receipts':['Retain exact concrete request bytes, actual public response and SQLite absence of accepted state.','An unchanged valid materialized bundle control must succeed first under exactly the same host policy.','These are inherited bundle/request wire refusals. The source feature does not add host torque mutation commands.','Full chunk/EOF transport, immutable asset slice reconstruction and interrupted publication are separately specified in agent/request-workflows.json.']})


if __name__=='__main__':main()
