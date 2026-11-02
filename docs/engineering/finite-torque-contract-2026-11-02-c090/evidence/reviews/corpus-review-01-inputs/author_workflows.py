#!/usr/bin/env python3
"""Author bounded Agent/resource procedures before any torque implementation."""
from __future__ import annotations

from copy import deepcopy
import json
from author_inputs import ROOT, write, identities


def request(case,step,operation,**fields):
    return {'schema_version':'ontokin.agent/0.22','project_id':'c090-'+case.lower(),
            'request_id':'c090-'+case.lower()+'-'+step,'operation':operation,**fields}


def step(case,name,operation,status='succeeded',code=None,**fields):
    result={'step':name,'request':request(case,name,operation,**fields),'expected_status':status}
    if code: result['expected_code']=code
    return result


def create(case,name='agent-base',step_name='create'):
    return step(case,step_name,'create',bundle={'$bundle_file':name+'.files.json'},
                expected_program_revision=None,requested_level='constructed')


def inspect(case,name='inspect',revision=None,**fields):
    defaults={'program_revision':revision or identities('agent-base')['program_revision'],
              'selector':{'kind':'object'},'fields':['identity','source','state','matter'],
              'limit':100}
    defaults.update(fields)
    return step(case,name,'inspect',**defaults)


def export(case,name='export',revision=None,**fields):
    defaults={'program_revision':revision or identities('agent-base')['program_revision'],
              'destination':'ontokin.glb/0.22','options':{'fps':4,'end':'2','helpers':False,
              'position_tolerance_m':0.001,'rotation_tolerance_rad':0.001,'time_tolerance_s':0.000001}}
    defaults.update(fields)
    return step(case,name,'export',**defaults)


def main():
    repairs=json.loads((ROOT/'agent/repairs.json').read_text())
    rev=repairs['base_identity']['program_revision']
    scenarios=[]
    s='A01'
    scenarios.append({'id':s,'name':'discover-create-resume-inspect-export',
      'steps':[step(s,'discover','discover',profile='torque-0.1',limit=1000),create(s),
        step(s,'validate','validate',program_revision=rev,requested_level='constructed'),
        inspect(s,'inspect-initial'),
        step(s,'evaluate-half','evaluate',program_revision=rev,run_id=None,until_seconds='0.5'),
        step(s,'resume','evaluate',program_revision=rev,run_id={'$response':'A01.evaluate-half.run_id'},until_seconds='2'),
        inspect(s,'inspect-final',run_id={'$response':'A01.resume.run_id'},time={'seconds':'2','side':'after'}),
        inspect(s,'inspect-self',selector={'path':'ball'},run_id={'$response':'A01.resume.run_id'},frame='ball.frame',time={'seconds':'1','side':'after'}),
        step(s,'mesh','surface.mesh_page',program_revision=rev,element_id=['torque-cases','demo','sibling','label'],count=256),
        export(s),step(s,'artifact-first','artifact',artifact_id={'$response':'A01.export.result.artifact_id'},offset=0,max_bytes=65536)],
      'assertions':['Catalog exposes the complete torque_interface and every inherited interface under its real .22 membership.',
        'Source torque records have full frozen identities, spans and source order. Every available object state has all 15 closed torque fields.',
        'Ball at 2 s: phase=2, speed=2, I=1. Sibling: phase=-1, speed=-1, I=1. Both counts start1/end1; anchor at2 after completion, phase_since_anchor=0.',
        'Self-frame requests preserve world-referenced torque scalar axis/history, source identities, canonical net and signed speed.',
        'Complete recorded closure, PNG, material/mesh/UV streams and actual controlled destination are checked by delivery-cases.json.']})
    # Every repair starts from a separate accepted base. No earlier valid edit
    # is silently rebased to make a later patch succeed.
    for index,repair in enumerate(repairs['repairs']):
        s='A02-'+str(index+1); valid=repair['expected_accepted']
        edit=step(s,'edit','edit',status='succeeded' if valid else 'rejected',
                  code=None if valid else ('OKL-E-EVENT-ORDER' if 'duration' in repair['id'] else 'OKL-E-PHYSICAL-DOMAIN'),
                  expected_program_revision=rev,requested_level='constructed',patches=[repair['patch']])
        target=repair['to']['program_revision'] if valid else rev
        scenarios.append({'id':s,'name':repair['id'],'steps':[create(s),
          step(s,'evaluate-base','evaluate',program_revision=rev,run_id=None,until_seconds='2'),export(s,'export-base'),edit,
          inspect(s,'inspect-after',revision=target),step(s,'evaluate-after','evaluate',program_revision=target,run_id=None,until_seconds='2'),
          inspect(s,'old-run',revision=rev,run_id={'$response':s+'.evaluate-base.run_id'},time={'seconds':'2','side':'after'}),
          step(s,'old-artifact','artifact',artifact_id={'$response':s+'.export-base.result.artifact_id'},offset=0,max_bytes=65536)],
          'repair_record':repair['id'],'expected_first_carrier':repairs['first_carrier_at_2'].get(repair['id'],repairs['first_carrier_at_2']['agent-base']),
          'exact_invariants':['Pinned library and image bytes/revisions','Sibling physical and visual state at every common clock','All bytes outside exact entry patch','Old accepted runs/artifacts remain immutable'],
          'invalid_rollback':not valid})
    s='A03'
    original=export(s)
    scenarios.append({'id':s,'name':'same-id-reopen-reset','steps':[create(s),
      step(s,'evaluate','evaluate',program_revision=rev,run_id=None,until_seconds='2'),original,
      {'step':'reopen','action':'close_and_reopen_same_store'},
      {'step':'same-create','request_ref':'A03.create','expected_status':'succeeded'},
      {'step':'same-export','request_ref':'A03.export','expected_status':'succeeded'},
      {'step':'changed-retry','request_ref':'A03.export','overrides':{'options':{**original['request']['options'],'fps':2}},'expected_status':'rejected','expected_code':'OKL-E-REQUEST-ID'},
      step(s,'status','status',target_request_id='c090-a03-export'),
      step(s,'reset','reset',program_revision=rev),inspect(s,'after-reset'),
      step(s,'fresh-evaluate','evaluate',program_revision=rev,run_id=None,until_seconds='2')],
      'assertions':['Historical create/export outcome remains exact and does not re-execute source or create another artifact.',
                    'Reset exposes before-zero empty/null torque state on every object; then new evaluation rebuilds histories.',
                    'A fresh request consumes current original authority despite unchanged source and warm caches.']})
    s='A04'; change=next(r for r in repairs['repairs'] if r['id']=='agent-magnitude')
    scenarios.append({'id':s,'name':'cursor-and-stale-source','steps':[create(s),
      inspect(s,'page',limit=1),{'step':'reopen','action':'close_and_reopen_same_store'},
      inspect(s,'old-cursor-reopened',cursor={'$response':'A04.page.result.next_cursor'},limit=1),
      step(s,'edit','edit',expected_program_revision=rev,requested_level='constructed',patches=[change['patch']]),
      step(s,'stale-edit','edit',status='rejected',code='OKL-E-REVISION',expected_program_revision=rev,requested_level='constructed',patches=[change['patch']]),
      {**inspect(s,'stale-cursor',revision=change['to']['program_revision'],cursor={'$response':'A04.page.result.next_cursor'},limit=1),'expected_status':'rejected','expected_code':'OKL-E-REVISION'}],
      'additional_cursor_controls':['Same source/context reopened cursor must pass.','Change filter/project/profile/current-policy context independently; no coincident numeric offset acceptance.']})
    s='A05'
    deny=[step(s,'deny-evaluate','evaluate',program_revision=rev,run_id=None,until_seconds='2'),export(s,'deny-export'),inspect(s,'deny-inspect'),
          step(s,'deny-validate','validate',program_revision=rev,requested_level='constructed'),
          step(s,'deny-mesh','surface.mesh_page',program_revision=rev,element_id=['torque-cases','demo','ball','label'],count=1),
          step(s,'deny-artifact','artifact',artifact_id={'$response':'A05.export.result.artifact_id'},offset=0,max_bytes=1)]
    for row in deny: row.update(expected_status='failed',expected_code='OKL-E-RESOURCE')
    scenarios.append({'id':s,'name':'current-host-authority','steps':[create(s),export(s),
      {'step':'reopen-low','action':'close_and_reopen_same_store','host_policy':{'max_operations':99999,'max_elapsed_ms':30000}},
      {'step':'historical-export','request_ref':'A05.export','expected_status':'succeeded'},*deny],
      'assertions':['Historical outcome is identified as historical; it is not a fresh successful execution.',
                    'All fresh IDs require current authority. Reduced host ceiling cannot be replenished by source default100000, warm caches or store reopen.',
                    'Accepted revision, prior runs and existing artifact inventory remain unchanged.']})
    s='A06'; capped=[]
    specs=[('operations','validate',{'program_revision':rev,'requested_level':'represented','budgets':{'max_operations':1}},'failed','OKL-E-RESOURCE'),
           ('items','inspect',{'program_revision':rev,'selector':{'kind':'object'},'fields':['identity'],'limit':2,'budgets':{'max_result_items':1}},'rejected','OKL-E-SAMPLE'),
           ('records','inspect',{'program_revision':rev,'selector':{'path':'ball'},'fields':['state'],'time':{'seconds':'1','side':'after'},'limit':1,'budgets':{'max_value_entries':1}},'failed','OKL-E-RESOURCE'),
           ('enlarge','validate',{'program_revision':rev,'requested_level':'represented','budgets':{'max_operations':100001}},'failed','OKL-E-RESOURCE'),
           ('artifact','artifact',{'artifact_id':{'$response':'A06.export.result.artifact_id'},'offset':0,'max_bytes':1,'budgets':{'max_operations':1}},'failed','OKL-E-RESOURCE')]
    for name,op,kw,status,code in specs: capped.append(step(s,name,op,status=status,code=code,**kw))
    scenarios.append({'id':s,'name':'caller-and-output-caps','steps':[create(s),export(s),*capped],
                      'assertions':['Every failure retains original consumed-work prefix and deadline. No partial active/history projection is published as success.']})
    s='A07'
    scenarios.append({'id':s,'name':'interrupted-artifact-publication','steps':[create(s)],'export_request':export(s)['request'],
      'fault':'Wrap the real _persist_task_metadata invoked inside _commit_task. Once task.artifact holds verified bytes and db.in_transaction is true, preserve exact prepared identity and bytes; raise a fresh sentinel subclass of BaseException. Let transaction unwind, restore the original method, close and reopen the same store. Issue no cancel.',
      'then':[{'step':'reopen','action':'close_and_reopen_same_store'},step(s,'status','status',target_request_id='c090-a07-export'),
          {'step':'same-id-retry','request_ref':'A07.export','expected_status':'unknown_outcome','expected_code':'OKA-E-UNKNOWN-OUTCOME'},
          step(s,'prepared-only','artifact',status='rejected',code='OKA-E-ARTIFACT',artifact_id={'$capture':'A07.prepared.artifact_id'},offset=0,max_bytes=1),export(s,'fresh-export')],
      'assertions':['Accepted revision unchanged; no committed artifact/run for interrupted request.','Read actual SQLite transaction rows independently and compare prepared-only ID with absence from accepted artifact table.','Never mutate a history row to manufacture successful recovery.']})
    s='A08'
    scenarios.append({'id':s,'name':'chunk-and-EOF-byte-transport','steps':[create(s),export(s)],
      'artifact_loops':[{'max_bytes':size,'initial_offset':0,'request_template':request(s,'artifact-${index}','artifact',artifact_id={'$response':'A08.export.result.artifact_id'},offset={'$loop':'offset'},max_bytes=size),
        'advance':'decoded returned byte count','stop':'exact actual total_bytes','must_equal':'Complete accepted GLB length and SHA256; every returned range equals exact original bytes.'} for size in (1,17,65536)],
      'eof_request':request(s,'eof','artifact',artifact_id={'$response':'A08.export.result.artifact_id'},offset={'$capture':'A08.exact_total_bytes'},max_bytes=1),
      'eof_expected':{'status':'succeeded','data_base64':'','next_offset':None,'truncated':False},
      'past_eof_request':request(s,'past-eof','artifact',artifact_id={'$response':'A08.export.result.artifact_id'},offset={'$capture':'A08.exact_total_bytes_plus_one'},max_bytes=1),
      'past_eof_expected':{'status':'rejected','code':'OKA-E-ARTIFACT'},
      'asset_loop':{'request_template':request(s,'asset-${index}','inspect',program_revision=rev,selector={'element_id':['assets','label']},fields=['identity','source'],limit=1,asset_slice={'offset':{'$loop':'offset'},'max_bytes':17}),
                    'total_bytes':89,'sha256':'sha256:5f87c7071d06327a077e05e1f57253370bc0b2eff1fa7f2025765825b7dcdd6e'},
      'retain':'Every concrete materialized request and response plus exact reconstructed bytes; no JSON normalization.'})
    stages=[('torque_source','p01-spin-up','validate'),('torque_boundary_scan','p04-overlap','evaluate'),
      ('torque_completion','p09-completion-starts-rotation','evaluate'),('torque_activation','p01-spin-up','evaluate'),
      ('torque_impulse_axis','p19-torque-then-impulse','evaluate'),('torque_aggregate_begin','p05-cancelling','evaluate'),
      ('torque_aggregate_term','p23-partial-sum-overflow-cancels','evaluate'),('torque_aggregate_publish','p05-cancelling','evaluate'),
      ('torque_rotation_anchor','p09-completion-starts-rotation','evaluate'),('torque_reference_origin','p30-underflow-replacement','evaluate'),
      ('torque_segment','p01-spin-up','evaluate'),('torque_segment_vertex','p22-nondyadic-zero-crossing','evaluate'),
      ('torque_projection','p01-spin-up','inspect'),('torque_boundary_commit','p04-overlap','evaluate'),
      ('torque_recording_path','p14-offset-reversal','export'),('torque_recording_phase','p21-equal-endpoint-reversal','export'),
      ('torque_recording_certificate','p14-offset-reversal','export')]
    resource_rows=[]
    physics={r['id']:r for r in json.loads((ROOT/'physics-cases.json').read_text())['cases']}
    for index,(stage_name,fixture,operation) in enumerate(stages):
        s='R'+str(index+1).zfill(2); program=identities(fixture)['program_revision']; horizon=str(physics[fixture]['horizon'])
        if operation=='validate': task=step(s,'task',operation,program_revision=program,requested_level='constructed')
        elif operation=='inspect': task=inspect(s,'task',revision=program,selector={'kind':'object'},fields=['state'],time={'seconds':'1','side':'after'},limit=100)
        elif operation=='export': task=export(s,'task',revision=program,options={'fps':4,'end':horizon,'helpers':False,'position_tolerance_m':0.001,'rotation_tolerance_rad':0.001,'time_tolerance_s':0.000001})
        else: task=step(s,'task',operation,program_revision=program,run_id=None,until_seconds=horizon)
        resource_rows.append({'id':s,'stage':stage_name,'fixture':fixture,'setup':create(s,fixture),'task_request':task['request'],
          'successful_control':'Run identical original request in fresh project with original defaults; record observed visit count, complete outcome and actual ledger identity before fault variants.',
          'fault_variants':['cancel','operation-cap','deadline','original-callback-exception'],
          'barrier':'Observe the actual shared ledger stage; preserve ledger, original monotonic start and callback object. Pause just before the selected structural tick. Never mock a successful stage or substitute a second budget.',
          'cancel_request':request(s,'cancel','cancel',target_request_id=task['request']['request_id']),
          'status_request':request(s,'status','status',target_request_id=task['request']['request_id']),
          'cancel_expected':{'queue_status':'queued','terminal_status':'cancelled'},
          'operation_expected':{'status':'failed','code':'OKL-E-RESOURCE','method':'Admit an actual reduced original request cap that expires on the selected real tick; derive cap solely from the independent successful-control trace before running this fault, retain both traces.'},
          'deadline_expected':{'status':'failed','code':'OKL-E-RESOURCE','method':'Advance controlled monotonic clock past the already admitted original deadline at this barrier, leaving start and ceiling unchanged.'},
          'callback_exception_expected':{'same_object_identity':True,'method':'Original callback raises a fresh captured sentinel; actual private helper must return that exact object without converting it to a numeric error.'},
          'must_preserve':['All prior accepted state including source/force/torque locks, anchors, active sets, counts and recent changes','Prior immutable source/run/artifact records','Original stage restored in finally','No successful artifact or truncated success after any failed final check'],
          'special':('Count carrier and every empty massless/unlatched object header; cancelling its empty-header tick must still refuse.' if stage_name=='torque_projection' else 'Reference-origin initialization must be visited on the neutral underflow carrier; also repeat with domain04-reference-only-change at t1.' if stage_name=='torque_reference_origin' else None)})
    write('agent/resource-cases.json',{'schema_version':'ontokin.torque-independent-resource-cases/1','candidate_output_used':False,'default_host':{'max_operations':100000,'max_elapsed_ms':30000},
      'fixed_limits':{'numeric_operand_bits':32768,'cache_entries':256,'recording_cursor_steps':64,'keys':10000,'poses':250000,'certificates':100000,'value_entries':100000,'json_bytes':8388608},
      'structural_aggregate_assertion':'Exactly n+2 aggregate-specific ticks per affected carrier (begin, n terms, publish), plus real primitive charges. Zero and cancelling terms count. Never allocate/parse an oversized operand before its prospective guard.',
      'cases':resource_rows,
      'extra_native_admission_cases':['No admitted execution context','Foreign/custom dict/list/numeric wrapper','Bool masquerading as scalar/count','Mutated history owner/context after original callback','Oversized rational numerator/denominator before parse','Cache hit under a new rejected request budget','History that would exceed whole-result record/JSON ceiling'],
      'execution_claim':False})
    scenarios.append({'id':'A09','name':'actual-cancellation-and-budget-stages','matrix':'agent/resource-cases.json','required_rows':[r['id'] for r in resource_rows]})
    scenarios.append({'id':'A10','name':'store-isolation-and-independent-reconciliation','protocol':'ontokin.agent/0.22',
      'database_filename':'torque-program-agent.sqlite3','store_schema':'ontokin.torque-program-agent-store/0.1',
      'procedure':['Create the same project name in explicit .21 and .22 services in a temporary common parent directory; write/read each through its real service.',
        'Open both SQLite files independently read-only. Verify actual store/protocol identities, accepted revision pointers, source/asset bytes, run sides/prefixes, request payload hash and response/transaction/byte hashes.',
        'Reopen each actual service; .21 and all old defaults retain original files and behavior. A mismatched explicitly selected store must refuse; do not migrate or rewrite the .21 store.',
        'Run A07 interruption, cancellation before/after acceptance, staged-artifact response-limit failure and every warm/reopened reader under current authority; inspect actual rows after each.'],
      'must_preserve':['Unchanged predecessor complete-byte outputs','No accepted pointer to uncommitted or candidate-only source/run/artifact','Same-ID historical linkage and unknown-outcome tombstone','No database edits by verifier']})
    scenarios.append({'id':'A11','name':'complete-physics-boundary-and-resumption-matrix','input':'state-expectations.json',
      'procedure':['For each case create exact sealed input in a fresh project; verify frozen program/source/asset identity before evaluation.',
        'At every frozen observation clock request the exact before/after state with inspect, then repeat with a new request ID and compare all defined fields.',
        'Evaluate once directly to horizon, and independently in increasing frozen after clocks with returned run_id; close/reopen at first nonzero torque boundary and resume same actual run.',
        'Compare source records, exact canonical hex/anchors/counts, bounded errors, independent quaternion/marker and COM oracles. Read self-frame variants at initial, reversal and completion clocks.',
        'No sample-only split, hidden zero-crossing public event, future completion outside requested prefix or torque-induced translation anchor is permitted.'],
      'refusal_matrix':'refusal-cases.json','additional_evaluation_domains':'evaluation-domain-cases.json'})
    write('agent/request-workflows.json',{'schema_version':'ontokin.c090-independent-workflows/1','candidate_observations_used':False,
      'template_rules':{'$bundle_file':'Read exact frozen files manifest and source/PNG bytes, seal unchanged bundle/0.2, verify independently frozen identity BEFORE dispatch. No ambient import.',
        '$response':'Resolve exact named earlier actual response path; no alternative or fabricated identifier.',
        '$capture':'Use the actual barrier/byte-length field named here; it is captured evidence, not a guessed ID.',
        '$loop':'Use zero-based iteration index and current exact returned byte offset; retain every fully materialized request.',
        'request_ref':'Reuse complete named prior request including request_id; only explicit override test changes it.',
        'namespaces':'Every scenario, repair, stage, fault variant and chunk-size loop uses its own fresh project/store/request namespace. Templates retain all field values; replace only the documented namespace prefix to avoid accidental duplicate IDs.',
        'unexpected_outcomes':'Retain actual failing outcome and input; correct only by reviewed new pre-implementation revision. Never retune expectations to candidate output.'},
      'required_operations':['discover','create','edit','validate','inspect','evaluate','reset','status','cancel','export','artifact','surface.mesh_page'],
      'default_host_policy':{'max_operations':100000,'max_elapsed_ms':30000},'scenarios':scenarios,'execution_claim':False})


if __name__=='__main__': main()
