"""Static semantic review of exact Director startup-record snapshot."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import subprocess

ROOT=Path('/workspace/scratch/29fbc446c948')
REPO=ROOT/'OntoKin'
OUT=ROOT/'p14-session/review/director-startup/attempt002'
SNAP=OUT/'candidate'
BASE='4023a878ccc9980726e3b56102b41faa51be0eb1'
P14='docs/engineering/localized-repair-c271/loader-path-p14/'
checks=[]

def j(rel):return json.loads((SNAP/rel).read_bytes())
def before(rel):return subprocess.check_output(['git','-C',str(REPO),'show',BASE+':'+rel],env=dict(os.environ,GIT_OPTIONAL_LOCKS='0'))
def check(name,passed,detail):checks.append({'id':name,'passed':bool(passed),'detail':detail})
def ident(raw):return {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

taskrel='docs/workflow/tasks/C271/task.json'
currentrel='docs/workflow/CURRENT.json'
task=j(taskrel);oldtask=json.loads(before(taskrel));current=j(currentrel);oldcurrent=json.loads(before(currentrel));phase=j(P14+'PHASE.json');receipt=j(P14+'EARLY-RECOVERY-RECEIPT.json')
allowed_task={'owner','blocked_reason','checks','delivery','next_action','prior_phase_deliveries','prior_session_phases','session_phase'}
changed_task={k for k in set(task)|set(oldtask) if task.get(k)!=oldtask.get(k)}
check('task_change_surface',changed_task<=allowed_task,sorted(changed_task))
check('requirements_plan_parent_preserved',task['requirements']==oldtask['requirements'] and task['plan']==oldtask['plan'] and task['status']=='blocked',{'requirements':[(x['id'],x['status']) for x in task['requirements']],'plan':[(x['id'],x['status']) for x in task['plan']]})
check('historical_arrays_preserved',all(task[k][:len(oldtask[k])]==oldtask[k] for k in ['checks','prior_session_phases','prior_phase_deliveries']),'All 49 prior checks, 12 prior sessions and 12 prior deliveries remain unchanged.')
check('new_checks_truthful',len(task['checks'])==len(oldtask['checks'])+4 and all(x['result']=='not_run' and x['required'] is True and x['evidence']==[] for x in task['checks'][len(oldtask['checks']):]),'Runtime96, inherited175, independent implementation review and documentary gates are initially not_run.')
check('historical_source_pointer',task['prior_session_phases'][-1]['source_revision']==BASE and BASE in task['prior_session_phases'][-1]['exact_prior_session_phase'] and task['prior_phase_deliveries'][-1]['terminal_confirmation'].endswith('P13-TERMINAL-CONFIRMATION.json'),'Exact historical P13 fields retained by immutable source pointer and separately reconciled terminal record.')
for name in ['REQUIREMENTS.md','PLAN.md']:
    rel='docs/workflow/tasks/C271/'+name
    check('append_only_'+name,(SNAP/rel).read_bytes().startswith(before(rel)),'Prior requirement and plan prose is byte-for-byte unchanged.')
check('current_recovery_chain',current['previous_recovery']==oldcurrent['latest_recovery'] and current['older_recoveries'][:-1]==oldcurrent['older_recoveries'] and current['older_recoveries'][-1]==oldcurrent['previous_recovery'],'P13 and P12 recoveries relocated intact; older recovery list preserved.')
allowed_current={'snapshot_date','next_action','latest_recovery','previous_recovery','older_recoveries'}
check('current_change_surface',{k for k in set(current)|set(oldcurrent) if current.get(k)!=oldcurrent.get(k)}<=allowed_current,'Historical handoffs and active/latest task identity preserved.')
check('canonical_phase_consistency',task['session_phase']==phase and task['owner']==phase['owner'] and task['next_action']==phase['exact_next_action']==current['next_action']['summary'],'Current owner, phase, stop/scope and exact next action agree across canonical records.')
check('early_receipts_agree',phase['early_recovery']==receipt==current['latest_recovery'] and (SNAP/(P14+'EARLY-RECOVERY-RECEIPT.json')).read_bytes()==(ROOT/'p14-session/EARLY-RECOVERY-RECEIPT.json').read_bytes(),'All current receipt copies agree.')
expected={'bytes':6627947,'sha256':'e52fbde87c3b831d877c20242f2f80af3dcc033b9bb033f5659b6c9332632012'}
source=Path(receipt['local_path']).read_bytes();readback=Path(receipt['readback_path']).read_bytes()
check('early_exact_readback',ident(source)==ident(readback)==expected and source==readback and receipt['status']=='succeeded' and receipt['saved_bytes_readback_equal'] is True and receipt['version']==0,'Accepted archive and actual retained downloaded readback are byte-identical; saved-file identity/status is supported by the Director receipt.')
check('early_review_identity',receipt['independent_review']['reviewer']=='/root/independent_review' and receipt['independent_review']['groups_passed']==29 and receipt['independent_review']['mandatory_findings']==[],'Receipt correctly cites this independent reviewer accepted29-group result.')
check('scope_no_expansion',phase['scope']=='Implement only P11 candidate004 FUTURE-SURFACE under adopted P13-RB-001 and its 96 runtime plus one external-review mapping.' and phase['parent_complete'] is False and phase['integration_allowed'] is False and phase['main_lease_held'] is False and 'no second phase' in phase['stop'],'No host, full-routine, integration or parent closure claim added.')
check('stale_early_pending_corrected',not any('Independent early-package acceptance and confirmed save/readback.'==x for x in phase['incomplete_steps']) and not phase['capabilities'].get('library_save_tools_available_not_yet_exercised',False),'Current phase contradicts passed A01/receipt by retaining early recovery as incomplete and claiming save tools unexercised.')
references=list(phase['evidence'].values())+[phase['observed_main']['evidence'],phase['startup_failures'],j(P14+'STARTUP-RECONCILIATION.json')['main']['evidence']]
broken=[p for p in references if not (SNAP/P14/p).is_file() and not (SNAP/p).is_file()]
check('canonical_evidence_paths',not broken,broken)
readme=(SNAP/(P14+'README.md')).read_text()
check('receipt_report_path_mapping',receipt['independent_review']['report']=='review/early-attempt002/REPORT.md' and 'review/early-attempt002/REPORT.md' in readme and 'evidence/review/early-attempt002/REPORT.md' in readme and (SNAP/(P14+'evidence/review/early-attempt002/REPORT.md')).is_file(),'Immutable receipt retains source-time relative path; README maps it to exact canonical evidence.')
review_copy_paths=['SCOPE-AUDIT.json','SCOPE-REPORT.md','READ-SET.json','early-attempt001/AUDIT.json','early-attempt001/REPORT.md','early-attempt001/REVIEWED-FILES.json','early-attempt002/AUDIT.json','early-attempt002/REPORT.md','early-attempt002/REVIEWED-FILES.json']
check('independent_review_copies_unchanged',all((SNAP/(P14+'evidence/review/'+p)).read_bytes()==(ROOT/'p14-session/review'/p).read_bytes() for p in review_copy_paths),'Canonical review copies match exact reviewer-owned originals.')
check('no_derived_extraction_copies',not any('extracted' in p.parts for p in (REPO/P14).rglob('*')),'No reproducible extracted archive tree is copied into the canonical candidate; original review scratch bytes remain intact.')
check('corrected_phase_state',phase['early_save_confirmed'] is True and phase['phase_table'][0]['state']=='passed' and phase['capabilities']['library_save_observed'] is True and phase['capabilities']['library_exact_readback_observed'] is True,'Confirmed early save now consistently appears complete; other implementation/delivery gates remain pending.')
findings=[]

audit={'schema':'ontokin.c271.p14-director-startup-review/1','reviewer':'/root/independent_review','created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'base':BASE,'candidate_manifest':ident((OUT/'CANDIDATE.json').read_bytes()),'verdict':'accepted_for_documentary_checkpoint' if all(c['passed'] for c in checks) else 'changes_required','checks':checks,'passed':sum(x['passed'] for x in checks),'failed':sum(not x['passed'] for x in checks),'mandatory_findings':findings,'assembly_observation':'Reproducible extracted archive trees removed from canonical evidence; original reviews remain unchanged and original extraction bytes stay in reviewer scratch. Both P14-RECORD-001 and P14-RECORD-002 resolved.','limits':['Production module and new adapter excluded entirely.','No duplicate global task-history read; only semantic changes and new records inspected.','No product/host code executed; no Git/index/canonical/remote changes by reviewer.','This static review does not replace root required documentary checks or later implementation acceptance.']}
(OUT/'AUDIT.json').write_text(json.dumps(audit,indent=2,sort_keys=True)+'\n')
(OUT/'REPORT.md').write_text(f"""# P14 Director startup records: {audit['verdict']}

Reviewer: /root/independent_review. Base: 4023a878ccc9980726e3b56102b41faa51be0eb1. Exact reviewed file identities are in CANDIDATE.json. {audit['passed']} independent static groups passed; {audit['failed']} failed.

All original requirements, plan states, 49 historical checks, 12 prior sessions and 12 prior deliveries remain unchanged. P13 is preserved by its exact historical source pointer and reconciled terminal confirmation. The four new P14 check entries are correctly not_run. Parent blocked, R03–R05 not_done and P02 in_progress are preserved. Scope, ownership, stop and concrete next action are consistent.

Confirmed early save is truthful within the inspected evidence: actual retained source/readback bytes are identical to the independently accepted 6,627,947-byte archive, SHA-256 e52fbde87c3b831d877c20242f2f80af3dcc033b9bb033f5659b6c9332632012. Saved-file identity/status is supplied by the exact Director receipt. P14-RECORD-001 is resolved by current completed/capability fields; P14-RECORD-002 is resolved by canonical evidence paths and the explicit immutable-receipt report mapping. Review copies are unchanged, and duplicate extracted trees are absent from canonical evidence.

Accepted only for a documentation checkpoint after fresh required staged checks and exact publication readback. Production module/new adapter are wholly excluded from this review. No implementation, actual loader, H0/H1, full-routine, integration or parent completion claim follows. No product/host code ran, and the reviewer made no Git/index/canonical/remote changes.
""")

print(json.dumps({'verdict':audit['verdict'],'passed':audit['passed'],'failed':audit['failed'],'findings':[x['id'] for x in findings]}))
