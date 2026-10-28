#!/usr/bin/env python3
"""C058 document/source identity and static metadata audit. Never import product code."""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
CORE=HERE.parent
ROOT=HERE.parents[3]
checks=[]

def load(p):
    return json.loads(p.read_text(encoding='utf-8'))

def identity(p):
    b=p.read_bytes()
    return dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),git_blob=hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest())

def group(name,fn):
    try:
        detail=fn()
        checks.append(dict(check=name,status='passed',detail=detail))
    except Exception as e:
        checks.append(dict(check=name,status='failed',error=f'{type(e).__name__}: {e}'))

def require(condition,message):
    if not condition:
        raise AssertionError(message)

def same_file(p,record):
    got=identity(p)
    for k in ('bytes','sha256','git_blob'):
        require(got[k]==record[k],f'{p}: {k} mismatch')

def parse_owned_json():
    files=list(CORE.glob('checkpoint-058*.json'))
    files += list((CORE/'checkpoint-058-reviews').rglob('*.json'))
    files += [p for p in HERE.rglob('*.json') if not any(x.startswith(('documentation-','metadata-')) for x in p.relative_to(HERE).parts[:-1])]
    for p in files: load(p)
    return dict(files=len(files))

binding=load(CORE/'checkpoint-058-source-binding.json')
matrix=load(CORE/'checkpoint-058-semantic-matrix.json')
plan=load(CORE/'checkpoint-058-evidence-plan.json')
manifest=load(CORE/'checkpoint-058-proposal-identities.json')
recovery=load(HERE/'recovered-inputs.json')
parent=load(HERE/'c057-tree.json')
parent_map={x['path']:x for x in parent['tree'] if x['type']=='blob'}

group('owned_json_parses',parse_owned_json)

def old_new():
    require(binding['source_parent_commit']=='3b82b5bd74495850e08cf8b4f51daca0342f9882','wrong parent')
    require(binding['source_parent_tree']==parent['sha']=='37e4a53d6bb6a052bd2a53e74b73d720633b467e','wrong tree')
    require(not parent['truncated'] and len(parent_map)==3118,'incomplete parent tree')
    require(binding['accepted_commit']=='d2f0088c4f3c1f570630334804a5a8f78e0105ac','wrong C030')
    require(binding['new_adopted_authority'] is None and binding['new_runtime_identity'] is None,'unexpected adoption/runtime')
    return dict(parent_files=len(parent_map),new_authority=None,new_runtime=None)
group('exact_old_new_identity_boundary',old_new)

def paired_sources():
    sliced=load(HERE/'accepted-source-slice.json')
    old={x['path']:x for x in sliced['files']}
    require(len(old)==len(binding['paired_inputs'])==8,'expected eight separate inputs')
    for row in binding['paired_inputs']:
        same_file(ROOT/row['path'],row['current'])
        b=old[row['path']]['content'].encode()
        got=dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),git_blob=hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest())
        for k in got: require(got[k]==row['accepted'][k],f'accepted {row["path"]}: {k}')
        require(row['identical']==(row['accepted']['sha256']==row['current']['sha256']),'paired identity flag')
    return dict(paired_files=8,identical=sum(x['identical'] for x in binding['paired_inputs']))
group('separately_pinned_source_bytes',paired_sources)

def adopted_inputs():
    adoption=load(ROOT/'docs/language-design/planar-reach-v0.1/adoption.json')
    observed=load(HERE/'observed-priority-bindings.json')
    frozen={x['path']:x for x in adoption['frozen_inputs']}
    observed_frozen={x['path']:x for x in observed['frozen_inputs']}
    for row in binding['additional_adopted_authority']:
        same_file(ROOT/row['path'],row)
        basename=row['path'].split('/')[-1]
        require(basename in adoption['effective_normative_inputs'],'missing exact effective normative input')
        require(basename in observed['effective_normative_inputs'],'missing exact observed normative input')
        for source in (frozen,observed_frozen):
            require(row['path'] in source,'missing exact frozen path')
            for key in ('path','bytes','sha256'):
                require(source[row['path']][key]==row[key],f'wrong frozen {key}')
    for row in binding['governance_inputs']: same_file(ROOT/row['path'],row)
    content=load(HERE/'main-STATUS.json')['content'].encode()
    require(hashlib.sha256(content).hexdigest()==binding['main_status']['sha256'],'main STATUS mismatch')
    return dict(additional_adopted_inputs=2,governance_inputs=len(binding['governance_inputs']))
group('adoption_and_governance_bindings',adopted_inputs)

def recovered_inputs():
    require(len(recovery['inputs'])==939 and sum(x['bytes'] for x in recovery['inputs'])==123453599,'recovery counts')
    for row in recovery['inputs']:
        same_file(ROOT/row['path'],row)
        remote=parent_map[row['path']]
        require(remote['sha']==row['git_blob'] and remote['size']==row['bytes'],'remote recovery binding')
        require((ROOT/row['path']).stat().st_mode & 0o777 == int(row['mode'],8),'local mode changed')
    require(recovery['partial_snapshot'] and not recovery['native_git_checkout'],'snapshot qualification')
    require(recovery['all_parent_markdown_html_count']==260 and recovery['all_parent_markdown_html_present'],'markdown coverage')
    require(not recovery['identity_failures'] and not recovery['known_dependency_targets_missing'],'recovery gaps')
    return dict(files=939,bytes=123453599,markdown_html=260,partial_snapshot=True)
group('all_recovered_parent_bytes_preserved',recovered_inputs)

def allowed_scope():
    added=[]
    base='docs/engineering/reach-recording-validation-2026-10-23/'
    for p in ROOT.rglob('*'):
        if not p.is_file(): continue
        rel=p.relative_to(ROOT).as_posix()
        if rel in parent_map: continue
        require(rel.startswith(base),'addition outside owned directory: '+rel)
        tail=rel[len(base):]
        require(tail=='HANDOFF-058.md' or tail.startswith('checkpoint-058'),'addition outside owned prefix: '+rel)
        added.append(rel)
    return dict(owned_added_files=len(added),runtime_changes=0,shared_contract_changes=0)
group('owned_additions_only',allowed_scope)

def core_hashes():
    require(len(manifest['files'])==6 and not manifest['adopted'],'core identity scope')
    names=set()
    for row in manifest['files']:
        require(row['path'] not in names,'duplicate core path')
        names.add(row['path']); same_file(CORE/row['path'],row)
    require('checkpoint-058-proposal-identities.json' not in names,'self-referential manifest')
    return dict(core_files=len(names))
group('exact_new_proposal_identities',core_hashes)

def coverage():
    ids={u['id'] for u in matrix['units']}
    require(len(ids)==len(matrix['units']),'duplicate units')
    require({e['id'] for e in matrix['events']}=={f'E{i:02}' for i in range(12)},'event coverage')
    require({g['id'] for g in matrix['full_gate_expansion']}=={f'G{i}' for i in range(1,5)},'gate coverage')
    require({f['id'] for f in matrix['failure_paths']}=={f'F{i:02}' for i in range(15)},'failure coverage')
    for row in matrix['events']+matrix['full_gate_expansion']:
        require(set(row['units'])<=ids,'undeclared units')
    by={x['id']:x for x in matrix['events']}
    gate_units=set().union(*(set(x['units']) for x in matrix['full_gate_expansion']))
    for event_id in ('E02','E06','E09'):
        require(gate_units<=set(by[event_id]['units']),'expanded gate units omitted at '+event_id)
    require({'C','W'}<=set(by['E05']['units']),'early equality tuple creation omitted')
    require('N' in by['E07']['units'],'fresh reader optional width query omitted')
    require(matrix['proposed_event_order'][:3]==['E01','E00','E02'],'setup seam not explicit')
    require(not matrix['adopted'] and not matrix['runtime_changed'],'scope state')
    return dict(unit_kinds=len(ids),source_events=12,gate_expansions=4,failure_cases=15)
group('finite_matrix_coverage_and_stage_order',coverage)

def candidate_bounds():
    setup=matrix['setup']
    require(not setup['cross_group_reuse'] and not setup['new_allowance'] and not setup['current_module_snapshots_eligible_as_paid_receipts'],'invalid setup policy')
    require(matrix['complete_gate_cost'] is None and matrix['whole_request_net_saving'] is None and matrix['measured_setup_incidence'] is None,'invented measurement')
    passive=matrix['passive_boundary']
    require('permitted_meter_transitions' in passive and 'iterator_topology' in passive,'meter/lifetime obligations missing')
    require(passive['status']=='Proposed eligibility premise; not established by current source','authority proof overstated')
    require(passive['concrete_meter_schedule_proved'] is False and bool(passive['ordinary_route']),'routing/meter proof boundary absent')
    return dict(new_allowance=False,complete_gate_cost=None,authority_proof='unproved')
group('setup_authority_and_measurement_qualifications',candidate_bounds)

def static_cardinalities():
    source=(ROOT/'ontokin/reach_conformance.py').read_text()
    syntax=ast.parse(source)
    assign={t.id:n.value for n in syntax.body if isinstance(n,ast.Assign) for t in n.targets if isinstance(t,ast.Name)}
    known={n:ast.literal_eval(assign[n]) for n in ('_TERM_STORAGE','_TERM_BOUNDS_METHODS','_TERM_WORK_METHODS','_TERM_BUDGET_METHODS')}
    def strings(node):
        if isinstance(node,ast.Constant) and isinstance(node.value,str): return node.value
        if isinstance(node,ast.Name) and node.id in known: return known[node.id]
        if isinstance(node,ast.Tuple):
            out=[]
            for e in node.elts:
                if isinstance(e,ast.Starred): out.extend(strings(e.value))
                else: out.append(strings(e))
            return tuple(out)
        raise ValueError('unexpected static syntax')
    table=assign['_TERM_CLASS_FIELDS'].args[0].generators[0].iter
    counts={}
    fraction_fields=()
    for row in table.elts:
        name=ast.unparse(row.elts[0]).split('.')[-1]
        fields=tuple(dict.fromkeys(known['_TERM_STORAGE']+strings(row.elts[1])))
        counts[name]=len(fields)
        if name=='Fraction': fraction_fields=fields
    term=len(assign['_TERM_GLOBALS'].elts); field=len(assign['_FIELD_GLOBALS'].elts)
    early=len(set(fraction_fields)&set(known['_TERM_STORAGE']+('numerator','denominator','_numerator','_denominator')))
    actual=dict(class_counts=counts,class_total=sum(counts.values()),term_module_bindings=term,field_module_bindings=field,full_gate_binding_units_at_least=sum(counts.values())+term+field,early_fraction_access_bindings=early)
    declared=matrix['static_binding_lower_bound']
    for k,v in actual.items(): require(v==declared[k],f'static cardinality {k}')
    require(actual['full_gate_binding_units_at_least']-1==114,'delta coefficient')
    return dict(**actual,product_imports=0,qualification='Conditional M1 units, not observed runtime ticks')
group('independent_syntax_derived_cost_lower_bound',static_cardinalities)

def review_bindings():
    summary=load(CORE/'checkpoint-058-reviews.json')
    require(summary['unresolved_findings']==0,'unresolved final findings')
    expected_inputs={x['path'] for x in manifest['files']}|{'checkpoint-058-proposal-identities.json'}
    total=0
    for row in summary['final_reviews']:
        p=CORE/row['path']; same_file(p,row)
        r=load(p)
        require(r['result']=='passed' and not r['unresolved_findings'],'review not passed')
        require(r['paused'] is True,'reviewer not paused')
        actual_inputs=[x['path'] for x in r['inputs']]
        require(len(actual_inputs)==len(set(actual_inputs)) and set(actual_inputs)==expected_inputs,'wrong or duplicate review input set')
        for entry in r['inputs']: same_file(CORE/entry['path'],entry)
        require(len(r['inputs'])==7,'review did not bind seven inputs')
        require(len(r['checks'])==row['checks'],'review check count')
        total+=len(r['checks'])
    require(len(summary['final_reviews'])==3 and total==summary['substantive_checks'],'review totals')
    return dict(reviewers=3,substantive_checks=total)
group('independent_final_review_exact_inputs',review_bindings)

def evidence_plan():
    require(len(plan['probes'])==15,'probe scope')
    require(not plan['runtime_execution_selected'] and not plan['adoption_selected'],'selected execution/adoption')
    require(plan['new_adopted_contract_identity'] is None and plan['new_runtime_identity'] is None,'new identity overstated')
    for r in plan['probes']:
        require(all(r[k] for k in ('independent_role','required_inputs','pass_criterion','execution_status')),'incomplete evidence criterion')
    return dict(probes=15,runtime_execution=False,adoption=False)
group('bounded_independent_evidence_plan',evidence_plan)

def historical_state():
    next_scope=load(CORE/'checkpoint-058-next-scope.json')
    for r in (plan,next_scope['release']):
        require(r['original28']=='24/28 historical','recording status changed')
        require(r['open']==['P11','P16','P23','L03'],'open failures changed')
        require(r['C035']=='held including adverse timing' and not r['full_product_goal_completed'],'hold/goal changed')
    require('no automatic' in next_scope['status'].lower(),'next-scope boundary')
    return dict(original28='24/28 historical',open=['P11','P16','P23','L03'],C035='held')
group('historical_results_and_next_scope_preserved',historical_state)

def startup():
    r=load(HERE/'reconciliation-summary.json')
    require(r['branches']==103 and r['open_prs']==33,'baseline inventory counts')
    for name in ('branch_head_changes','missing_or_extra_branches','pr_head_changes','missing_or_extra_open_prs','preexisting_pr_state_draft_headref_baseref_basesha_changes'):
        require(not r[name],name)
    require(r['all_published_addition_paths_git_blobs_modes_sizes_match'] and r['all_parent_git_blobs_modes_sizes_preserved'],'C057 preservation')
    require(r['additions']==59 and r['addition_bytes']==3732519,'C057 additions')
    require('6457268685' in (HERE/'c057-closure.json').read_text(),'explicit C057 closure missing')
    require('6474322587' in (HERE/'owned-scope-and-ref.json').read_text(),'C058 declared scope missing')
    return dict(prior_branches=103,prior_open_prs=33,C057_additions=59,explicit_release=True)
group('startup_ownership_and_preservation_receipts',startup)

def recovery_failures():
    require(len(recovery['acquisition_failures'])==4,'failure record count')
    require(recovery['archive_whole_file_hashing_only'] and recovery['product_imports']==0 and recovery['archive_extractions']==0,'recovery scope overclaim')
    require(recovery['documentation_checker_runs']==0 and recovery['runtime_test_runs']==0,'recovery versus validation distinction')
    return dict(acquisition_failures=4,missing_recovered_inputs=0,archive_scope='whole-file identities only')
group('acquisition_failures_separated_from_validation',recovery_failures)

result={'schema':'ontokin.checkpoint058-metadata-audit/0.1','status':'passed' if all(x['status']=='passed' for x in checks) else 'failed','checks':checks,'grouped_checks':len(checks),'failures':[x for x in checks if x['status']=='failed'],'product_imports':0,'runtime_execution':False,'qualification':'Document/source-identity/static metadata audit, not proof of candidate runtime authority or release acceptance.'}
print(json.dumps(result,indent=2))
sys.exit(0 if result['status']=='passed' else 1)
