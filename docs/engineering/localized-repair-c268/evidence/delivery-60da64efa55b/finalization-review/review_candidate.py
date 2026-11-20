#!/usr/bin/env python3
"""Independently inspect the immutable C268 delivery-record candidate tree."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone

REPO=Path('/workspace/scratch/60da64efa55b/OntoKin')
OUT=Path('/workspace/scratch/60da64efa55b/evidence/finalization-review')
MAIN='5084dd69312e8da5a49aadd33cf83ba56db7c058'
LEASE='bb317b3bb84c484a4877b2a1a5e74393d94795f8'
TREE='49b3e72d8966f9ac89f4108bf90c4bc7d4aaec27'
ORIGINAL='ecce5f18fd4693e254bc6c797cd8b3f0a74d32a1'
PUBLISHED='71932558224d80794f76e52adf603b6308580326'
OWNER='c268-delivery-60da64efa55b'
BASE='docs/engineering/localized-repair-c268'
DELIVERY=BASE+'/evidence/delivery-60da64efa55b'
checks=[]
identities=[]

def git(*args):
    return subprocess.check_output(['git','--no-optional-locks',*args],cwd=REPO)

def blob(ref,path): return git('show',ref+':'+path)
def load(ref,path): return json.loads(blob(ref,path))
def identity(raw): return {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def check(name,ok,detail=None):
    row={'name':name,'passed':bool(ok)}
    if detail is not None: row['detail']=detail
    checks.append(row)
def check_identity(name,raw,expected):
    actual=identity(raw)
    check(name,all(actual[k]==expected[k] for k in ['bytes','sha256']))
    identities.append({'path':name,**actual})

OUT.mkdir(parents=True,exist_ok=True)
check('observed_local_lease_head',git('rev-parse','HEAD').decode().strip()==LEASE)
check('index_matches_review_tree',not git('diff','--cached',TREE,'--name-only').strip())
check('no_unstaged_source_changes',not git('diff','--name-only').strip())
check('published_recovery_exact_tree',git('rev-parse',PUBLISHED+'^{tree}')==git('rev-parse',ORIGINAL+'^{tree}'))
check('publication_retains_merge_parent',git('show','-s','--format=%P',PUBLISHED).decode().strip()==MAIN)
instruction_paths=['AGENTS.md','ROLE.md','docs/workflow/PROTOCOL.md','docs/workflow/HANDOFF.md','.agents/skills/ontokin-delivery/SKILL.md','docs/workflow/tasks/C268/REQUIREMENTS.md','docs/engineering/OK-ENG-006-local-validation-and-hosted-ci-policy.md','docs/engineering/OK-ENG-009-development-integration-and-branch-lifecycle.md']
for p in instruction_paths:
    check('previous_full_read_still_applicable:'+p,blob(MAIN,p)==blob(TREE,p))

original_delta=[x.split('\t',1) for x in git('diff','--name-status',MAIN,ORIGINAL).decode().splitlines()]
changed_records={'STATUS.md','docs/workflow/CURRENT.json','docs/workflow/tasks/C268/task.json'}
for kind,p in original_delta:
    if p not in changed_records:
        check('original_recovery_payload_preserved:'+p,blob(ORIGINAL,p)==blob(TREE,p))
old_evidence=git('ls-tree','-r','--name-only',ORIGINAL,'--',BASE+'/evidence/finalization-a3de3dd23bbf').decode().splitlines()
for p in old_evidence:
    check('full_prior_finalization_evidence_preserved:'+p,blob(ORIGINAL,p)==blob(TREE,p))
audit_path=DELIVERY+'/main-evidence-audit'
manifest=load(TREE,audit_path+'/ARTIFACTS.json')
for row in manifest['files']:
    check_identity('copied_audit:'+row['path'],blob(TREE,audit_path+'/'+row['path']),row)
    check('copied_audit_identical_to_reviewer_output:'+row['path'],blob(TREE,audit_path+'/'+row['path'])==(OUT.parent/'main-evidence-audit'/row['path']).read_bytes())
check('copied_audit_manifest_exact',blob(TREE,audit_path+'/ARTIFACTS.json')==(OUT.parent/'main-evidence-audit/ARTIFACTS.json').read_bytes())
check('copied_audit_inventory_exact',set(git('ls-tree','-r','--name-only',TREE,'--',audit_path).decode().splitlines())=={audit_path+'/'+x['path'] for x in manifest['files']}|{audit_path+'/ARTIFACTS.json'})

delta=[x.split('\t',1) for x in git('diff','--name-status',LEASE,TREE).decode().splitlines()]
check('bounded_delta',len(delta)==90 and all(k in ['A','M'] and (p=='STATUS.md' or p.startswith(BASE+'/') or p in ['docs/workflow/CURRENT.json','docs/workflow/knowledge.json','docs/workflow/tasks/C268/PLAN.md','docs/workflow/tasks/C268/task.json']) for k,p in delta))
code_paths=[p for k,p in delta if p.endswith('.py') and '/evidence/' not in p]
check('no_implementation_changes',not code_paths)

task=load(TREE,'docs/workflow/tasks/C268/task.json')
current=load(TREE,'docs/workflow/CURRENT.json')
phase=load(TREE,DELIVERY+'/PHASE.json')
coord=load(TREE,DELIVERY+'/COORDINATION.json')
early=load(TREE,DELIVERY+'/EARLY-RECOVERY-RECEIPT.json')
provenance=load(TREE,DELIVERY+'/RECOVERY-PROVENANCE.json')
status=blob(TREE,'STATUS.md').decode()
lease_status=blob(LEASE,'STATUS.md').decode()
lease_section=lambda s:s.split('## Main integration lease\n',1)[1].split('## Historical status',1)[0]
check('lease_preserved_exactly',lease_section(status)==lease_section(lease_status))
check('owner_consistent',task['owner']==task['session_phase']['owner']==phase['owner']==coord['owner']==OWNER and OWNER in lease_section(status))
check('lease_coordinates',coord['acquisition_commit']==LEASE and coord['acquisition_readback_verified'] and coord['state']=='held_verified' and coord['acquired_at_utc'] in lease_section(status) and coord['expires_at_utc'] in lease_section(status))
check('parent_remains_active',task['status']==phase['parent_task_status']=='in_progress' and current['active_task']==current['latest_task']=='C268')
check('requirement_states',[(r['id'],r['status']) for r in task['requirements']]==[(f'R0{i}','done') for i in range(1,7)]+[('R07','not_done')])
check('plan_states',[(r['id'],r['status']) for r in task['plan']]==[(f'P0{i}','done') for i in range(1,5)]+[('P05','in_progress')])
check('final_save_not_claimed',task['delivery']['status']=='pending' and 'final saved delivery remains' in status and BASE+'/DELIVERY.json' not in git('ls-tree','-r','--name-only',TREE,'--',BASE).decode().splitlines())
check('early_save_distinct',early['save_outcome']=='confirmed' and early['scope']=='early recovery save, parent C268 remains in_progress' and early['preserved_unpublished_commit']==ORIGINAL and task['session_phase']['early_receipt']==DELIVERY+'/EARLY-RECOVERY-RECEIPT.json')
check('current_observed_main',current['observed_main']==LEASE)
check('original_execution_attribution',task['completion']['merge_commit']==provenance['original_main_execution_commit']==MAIN and provenance['main_execution_attribution_unchanged'] and provenance['affected_cohort_rerun'] is False)
check('recovery_mapping',task['completion']['recovered_main_evidence_publication_commit']==provenance['recovered_publication_commit']==PUBLISHED and task['completion']['original_main_evidence_commit']==provenance['original_unpublished_commit']==ORIGINAL and provenance['same_tree'])
check('bounded_stop',all('stop' in text.lower() for text in [task['next_action'],task['session_phase']['scope'],phase['scope']]) and 'no new milestone' in phase['stopping_point'] and 'closure' in phase['stopping_point'] and 'no next milestone' in task['next_action'] and 'R07' in task['session_phase']['acceptance'])
check('C262_unchanged',current['historical_handoff']==load(MAIN,'docs/workflow/CURRENT.json')['historical_handoff'])
check('accepted_knowledge_unchanged',blob(TREE,'docs/workflow/knowledge.json')==blob(ORIGINAL,'docs/workflow/knowledge.json'))
check('requirements_unchanged',blob(TREE,'docs/workflow/tasks/C268/REQUIREMENTS.md')==blob(MAIN,'docs/workflow/tasks/C268/REQUIREMENTS.md'))

external=OUT.parent/'recovery-record-checks'
receipt=json.loads((external/'CHECKS.json').read_bytes())
check('fresh_documentation_workflow_exact_tree',receipt['source_before']==receipt['source_after'] and receipt['source_before']['commit']==LEASE and receipt['source_before']['index_tree']==TREE and receipt['source_before']['unstaged_paths']=='' and receipt['inputs_stable'] and receipt['passed'])
for c in receipt['checks']:
    check_identity('fresh_record_check:'+c['name'],(external/c['log']['path']).read_bytes(),c['log'])
    check('fresh_record_check_pass:'+c['name'],c['passed'] and c['exit_code']==0)
check('exact_fresh_check_set',{c['name'] for c in receipt['checks']}=={'workflow','documentation'})

ws=json.loads((OUT.parent/'whitespace/REVIEW.json').read_bytes())
check_identity('preserved_whitespace_patch',blob(TREE,ws['excluded_path']),{'bytes':len(blob(TREE,ws['excluded_path'])),'sha256':ws['sha256']})
for c in ws['checks']:
    check_identity('whitespace_receipt:'+c['name'],(OUT.parent/'whitespace'/c['log']).read_bytes(),c)
check('whitespace_disposition',ws['checks'][0]['exit_code']==2 and ws['checks'][1]['exit_code']==0 and ws['excluded_path']==audit_path+'/METADATA-DELTA.patch')
log=(OUT.parent/'whitespace/full.log').read_text()
diagnostics=[s for s in log.splitlines() if ': trailing whitespace.' in s]
check('whitespace_only_preserved_patch',bool(diagnostics) and all(s.startswith(ws['excluded_path']+':') for s in diagnostics))
patch=blob(TREE,ws['excluded_path']).decode().splitlines()
line_numbers=[int(re.search(r':(\d+): trailing whitespace\.',s).group(1)) for s in diagnostics]
check('whitespace_only_unified_diff_blank_context',all(patch[i-1]==' ' for i in line_numbers))
check('index_unchanged_at_review_end',not git('diff','--cached',TREE,'--name-only').strip())

report={'schema':'ontokin.c268.finalization-metadata-review/1','reviewer':'/root/main_evidence_audit','reviewed_at_utc':datetime.now(timezone.utc).isoformat(),'candidate_tree':TREE,'observed_head':LEASE,'planned_publication_parents':[LEASE,PUBLISHED],'original_recovery_commit':ORIGINAL,'published_recovery_commit':PUBLISHED,'original_execution_commit':MAIN,'verdict':'eligible' if all(x['passed'] for x in checks) else 'findings','assertion_count':len(checks),'mandatory_findings':[x for x in checks if not x['passed']],'checks':checks,'identities':identities,'changed_paths':delta,'original_payload_paths_verified':len(original_delta)-len(changed_records),'prior_finalization_evidence_paths_verified':len(old_evidence),'copied_independent_audit_files':len(manifest['files'])+1,'fresh_record_check_receipt':{'path':str(external/'CHECKS.json'),**identity((external/'CHECKS.json').read_bytes())},'metadata_judgment':'R01-R06 are supported; R07 and final save remain pending. Current lease and owner preserved. Original 5084 execution attribution and ecce-to-7193 recovery mapping are explicit. Scope is publication of existing evidence and delivery/closure only.','limits':'Local immutable-tree and preserved-receipt review. No new network request, no cohort rerun, no final package or save acceptance. Director still verifies conditional publication/readback, final package, confirmed save, receipt, closure and lease release.','reviewer_read_helper_error':{'operation':'Schema inspection of BLOB-READBACK.json','error':'AttributeError: list object has no attribute items','cause':'Read helper assumed object; preserved file is a three-item list','effect':'Read-only helper stopped; corrected inspection completed. No product check or audit assertion failure.'},'ownership':{'repository_edits':False,'index_mutations':False,'network_writes':False,'nested_workers':False,'cohort_execution':False}}
(OUT/'REVIEW.json').write_text(json.dumps(report,indent=2)+'\n')
(OUT/'METADATA-DIFF.patch').write_bytes(git('diff',LEASE,TREE,'--','STATUS.md','docs/workflow/CURRENT.json','docs/workflow/knowledge.json','docs/workflow/tasks/C268/task.json','docs/workflow/tasks/C268/PLAN.md',DELIVERY+'/PHASE.json',DELIVERY+'/COORDINATION.json'))
print(json.dumps({k:report[k] for k in ['verdict','assertion_count','mandatory_findings','original_payload_paths_verified','prior_finalization_evidence_paths_verified','copied_independent_audit_files']},indent=2))
