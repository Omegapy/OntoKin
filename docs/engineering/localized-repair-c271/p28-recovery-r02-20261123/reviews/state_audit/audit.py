"""Read-only evidence audit for bounded C271 P28 source recovery.

Writes only this review directory. Does not execute project code or mutate remote state.
"""
from pathlib import Path
import datetime
import difflib
import hashlib
import json
import shutil
import zipfile

ROOT = Path('/workspace/scratch/002c49ccf480')
OUT = ROOT / 'session/reviews/state_audit'
HEAD = '46b0fce68afb65cfbfcaba64f1276408d93ee85d'
MAIN = 'e43cc6c5777874101a40559e4058ad6826b07e51'
PARENT = '360c80062e769230199602326fa8de25660df714'
SOURCE = '5f340b4f49d13638f3522e201a1e99b93a19358b'

def read_json(path):
    return json.loads(path.read_text())

def api(name):
    value = read_json(OUT / f'{name}.json')['result']['structuredContent']['content']
    return json.loads(value)

def raw(name):
    return read_json(OUT / f'recovery-{name}.response.json')['result']['structuredContent']['content']

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def git_blob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()

checks = []
def check(name, condition, detail):
    checks.append({'name': name, 'passed': bool(condition), 'detail': detail})

task = read_json(ROOT / 'session/branch/docs/workflow/tasks/C271/task.json')
current = read_json(ROOT / 'session/branch/docs/workflow/CURRENT.json')
main_current = read_json(ROOT / 'session/governing/docs/workflow/CURRENT.json')
c270 = read_json(ROOT / 'session/governing/docs/workflow/tasks/C270/task.json')
pr = read_json(ROOT / 'session/evidence/pr.json')
issue = read_json(ROOT / 'session/evidence/issue.json')
branches = read_json(ROOT / 'session/evidence/branches.json')
branch_commit = api('branch-commit')
commits = api('commits-p28')
compare = api('compare-p28-recovery')
pr_comments = api('pr-comments-p28')
issue_comments = api('issue-comments-p28')
terminal_pr = next(c for c in pr_comments if c['id'] == 7113998703)
terminal_issue = next(c for c in issue_comments if c['id'] == 7113999171)
outcome = json.loads(raw('OUTCOME.json'))
reconciliation = json.loads(raw('RECONCILIATION.json'))

check('branch_inventory', {b['name']: b['commit']['sha'] for b in branches} == {'main': MAIN, 'work/c271-missing-import-digest-control': HEAD}, 'Only main and the retained C271 branch in the Director supplied inventory.')
check('pr_state', pr['state'] == 'open' and pr['draft'] is True and pr['merged'] is False and pr['head']['sha'] == HEAD, 'PR274 remains draft/open/unmerged at the exact observed head.')
check('issue_state', issue['number'] == 273 and issue['state'] == 'open', 'Scope issue273 remains open.')
check('main_pointer_lag', main_current['latest_task'] == 'C270' and main_current['active_task'] is None and main_current['next_action']['status'] == 'awaiting_user_direction', 'Main CURRENT is the prior completed C270 pointer; current authorized recovery and live C271 records govern active work.')
check('c270_completed', c270['status'] == 'done' and c270['completion']['merge_commit'] == '4d27756f1c503b430dd85219235778a1f78ef101' and c270['session_phase']['delivery_confirmed'] is True, 'No C270 technical or delivery gate was reopened by this audit.')
check('c271_open_requirements', {r['id']: r['status'] for r in task['requirements']} == {'R01':'done','R02':'done','R03':'not_done','R04':'not_done','R05':'not_done'}, 'Parent acceptance gates preserved.')
check('c271_active_pointer', current['active_task'] == 'C271' and current['latest_task'] == 'C271' and current['next_action']['status'] == 'blocked', 'Existing scope is active; no new milestone selected.')
check('parent_plan_preserved', {p['id']: p['status'] for p in task['plan']} == {'P01':'done','P02':'in_progress'}, 'Recovery delivery does not complete parent P02.')
check('exact_branch_tree', branch_commit['sha'] == HEAD and branch_commit['tree']['sha'] == 'e5d8dc89b9e6fba4315a3386f43e13e758b33c0e', 'Git commit object verifies the exact observed branch tree.')
check('recovery_commit_chain', [c['sha'] for c in commits] == [HEAD,SOURCE,PARENT,'105ac7c5f247fc1a01c1073266763f16e6587757'] and commits[0]['parents'][0]['sha'] == SOURCE and commits[1]['parents'][0]['sha'] == PARENT, 'Time bounded history since 18:00 UTC contains two P27 and two documentary P28 recovery commits; page1 returned4 of100.')
check('only_documentary_delta', compare['status'] == 'ahead' and compare['total_commits'] == 2 and len(compare['files']) == 29 and all(f['filename'].startswith('docs/') for f in compare['files']), 'The branch delta from the original intended parent has29 documentary paths and no production/test changes.')
check('terminal_copies_match', terminal_pr['body'] == terminal_issue['body'], 'Live PR comment7113998703 and issue comment7113999171 are identical.')
check('terminal_narrow_resolution', all(s in terminal_pr['body'] for s in ['releases only this recovery session','Original P28 implementation and parent C271 remain incomplete','Earlier worker liveness and historical unknown operations remain unknown']), 'Matching terminal markers resolve recovery delivery/ownership only.')
check('candidate_unknown_preserved', all(x['resulting_tree_sha'] is None and x['resulting_commit_sha'] is None and x['intended_parent'] == PARENT for x in outcome['unknown_operations']), 'Original immutable upload operation has no recoverable tree or commit identifier in these records.')
check('no_original_upload_replay', outcome['ownership']['original_upload_replay'] is False, 'No original upload has been replayed by the prior documentary recovery; none replayed by this audit.')
check('reconstruction_not_selected', 'Reimplementation' in outcome['exclusions'] and 'request a bounded reconstruction decision' in task['next_action'], 'No current reconstruction decision was supplied or found in the inspected operative records. The original implementation declaration is historical authority for that phase, not a new reconstruction decision.')
check('bounded_comments_complete', len(pr_comments) == 5 and len(issue_comments) == 4 and max(len(pr_comments),len(issue_comments)) < 100, 'REST issue comment collections filtered since 2026-11-23T18:00:00Z; both page1 results below page size100. Older comments not comprehensively reread.')
check('no_p28_candidate_in_historical_bodies', 'p28' not in pr['body'].lower() and 'p28' not in issue['body'].lower(), 'The large current PR/issue bodies contain historical P25 and earlier records, with no P28 string; no full semantic body review claimed.')
check('ci_no_status_checks', api('ci-status')['total_count'] == 0 and api('ci-status')['statuses'] == [], 'Combined state pending with zero statuses, not a CI pass.')
check('ci_no_runs', api('ci-runs')['total_count'] == 0 and api('ci-runs')['workflow_runs'] == [], 'No workflow runs for the exact current head; no repository-wide disablement claim.')

tree_names = ['tree-root','tree-docs','tree-workflow','tree-engineering','tree-tasks','tree-c271-evidence','tree-c271-task','tree-p28-recovery','tree-p27-design']
trees = {name:api(name) for name in tree_names}
check('bounded_trees_complete', all(t['truncated'] is False for t in trees.values()), 'All9 nonrecursive directory responses are complete for their own direct entries; no whole-repository recursive inventory claimed.')
check('nested_agents_absent_on_selected_chains', all(not any(e['path'] == 'AGENTS.md' for e in t['tree']) for name,t in trees.items() if name != 'tree-root'), 'No nested AGENTS.md at the inspected ancestor/task/recovery/design directories. Root AGENTS exists; current main governs the newer ephemeral-host rule.')

for filename in ['REQUIREMENTS.md','PLAN.md','task.json']:
    p=ROOT/'session/branch/docs/workflow/tasks/C271'/filename
    expected=next(e['sha'] for e in trees['tree-c271-task']['tree'] if e['path']==filename)
    check('source_blob_'+filename, git_blob(p.read_bytes()) == expected, {'local':str(p),'expected_git_blob':expected,'actual_git_blob':git_blob(p.read_bytes())})
p=ROOT/'session/branch/docs/workflow/CURRENT.json'
expected=next(e['sha'] for e in trees['tree-workflow']['tree'] if e['path']=='CURRENT.json')
check('source_blob_CURRENT.json',git_blob(p.read_bytes())==expected,{'expected_git_blob':expected,'actual_git_blob':git_blob(p.read_bytes())})

postfreeze_bytes=(OUT/'POSTFREEZE-EVIDENCE.zip').read_bytes()
postfreeze_zip=zipfile.ZipFile(OUT/'POSTFREEZE-EVIDENCE.zip')
postfreeze_publication=json.loads(postfreeze_zip.read('records/PUBLICATION.json'))
postfreeze_intent=json.loads(postfreeze_zip.read('records/PUBLICATION-INTENT.json'))
postfreeze_manifest=json.loads(postfreeze_zip.read('records/STAGED-PAYLOAD.json'))
check('postfreeze_exact_archive',len(postfreeze_bytes)==30001 and sha256(postfreeze_bytes)=='84b6f6b57831bb5af7a7f29fda3399c02a3e1f679ce8149e1d7897deb6fcbfa0','Additional durable archive independently fetched as base64 at the exact branch commit.')
check('postfreeze_archive_integrity',postfreeze_zip.testzip() is None and len(postfreeze_zip.namelist())==25,'All25 ZIP members were enumerated and hashed; no archive member code executed.')
check('postfreeze_documentary_manifest',len(postfreeze_manifest)==27 and all(x['path'].startswith('docs/') for x in postfreeze_manifest),'Manifest is the known27-file documentary recovery publication.')
check('postfreeze_known_publication',postfreeze_publication['source_commit']==SOURCE and postfreeze_publication['source_tree']=='6a85465aa64ba44dbd13e54087191ec2efbf9e05' and postfreeze_publication['parent']==PARENT,'Tree/commit creation receipts identify documentary sourceA, not the missing original P28 upload.')
check('postfreeze_original_still_unknown',postfreeze_intent['original_p28_objects']=='unknown and not retried','The archive explicitly preserves unknown original objects and supplies no recovered original candidate.')

read_paths = [
 'session/governing/AGENTS.md','session/governing/ROLE.md','session/governing/docs/workflow/PROTOCOL.md','session/governing/docs/workflow/HANDOFF.md','session/governing/docs/workflow/EPHEMERAL-HOST.md',
 'session/governing/docs/workflow/tasks/C270/REQUIREMENTS.md','session/governing/docs/workflow/tasks/C270/PLAN.md',
 'session/governing/docs/workflow/tasks/C270/task.json','session/governing/docs/workflow/CURRENT.json','session/governing/STATUS.md',
 'session/branch/docs/workflow/tasks/C271/REQUIREMENTS.md','session/branch/docs/workflow/tasks/C271/PLAN.md','session/branch/docs/workflow/tasks/C271/task.json','session/branch/docs/workflow/CURRENT.json']
identities=[]
for relative in read_paths:
    p=ROOT/relative; b=p.read_bytes(); dest=OUT/'read-snapshots'/relative.removeprefix('session/')
    dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
    identities.append({'input':relative,'snapshot':str(dest.relative_to(ROOT)),'bytes':len(b),'sha256':sha256(b),'git_blob':git_blob(b)})
r=(ROOT/'session/branch/docs/workflow/tasks/C271/REQUIREMENTS.md').read_text().splitlines()
p=(ROOT/'session/branch/docs/workflow/tasks/C271/PLAN.md').read_text().splitlines()
plan_coverage=[]
for op,a,b,c,d in difflib.SequenceMatcher(None,r,p,autojunk=False).get_opcodes():
    if c<d:plan_coverage.append({'plan_lines':[c+1,d],'coverage':'byte-identical line sequence already read in requirements' if op=='equal' else 'unique plan text separately read','requirements_lines':[a+1,b] if op=='equal' else None})

report={
 'schema':'ontokin.c271.p28-current-state-audit/1','reviewer':'/root/state_audit',
 'recorded_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'scope':'Bounded live state, original exact candidate recovery and prior documentary-delivery reconciliation; no mutations outside owned review files.',
 'verdict':'BLOCKED_EXACT_ORIGINAL_P28_CANDIDATE_NOT_FOUND_IN_INSPECTED_DURABLE_RECORDS',
 'observed':{'main':MAIN,'head':HEAD,'head_tree':branch_commit['tree']['sha'],'original_intended_parent':PARENT,'documentary_source_commit':SOURCE,'documentary_source_tree':'6a85465aa64ba44dbd13e54087191ec2efbf9e05','pr':274,'issue':273},
 'checks':checks,'checks_passed':sum(c['passed'] for c in checks),'checks_failed':sum(not c['passed'] for c in checks),
 'delivery_resolution':{'terminal_comments':[7113998703,7113999171],'matching_live_bodies':True,'prior_recovery_owner':'c271-p28-recovery-acb73444303d','release_scope':'prior documentary recovery only','external_receipt_library_file_id':'libfile_fde3_f-46d1b2e049348191b5ab4eb4645330e3_2ab2a24d43748191957f9bcc356b59de','external_receipt_bytes':96179,'external_receipt_sha256':'a345691387fa0f32133b4202fc94abbca12b17c94a73eadda0fe26838b4bc408','external_receipt_bytes_verified_by_this_worker':False,'artifact_verification':'Director/independent artifact reviewer handles actual Library-byte verification; this audit verifies the live exact terminal claims and Git identities.'},
 'unknown_operations':outcome['unknown_operations'],
 'postfreeze_additional_input':{'path':'docs/engineering/localized-repair-c271/p28-recovery-20261123/POSTFREEZE-EVIDENCE.zip','commit':HEAD,'git_blob':'5f8d81f94531661ed62e20b427c513d973675592','bytes':30001,'sha256':'84b6f6b57831bb5af7a7f29fda3399c02a3e1f679ce8149e1d7897deb6fcbfa0','members':25,'conclusion':'Known documentary recoveryA publication receipts and package audits only. Original upload objects remain expressly unknown.','fully_read_members':['records/PUBLICATION-INTENT.json','records/PUBLICATION.json','records/PUBLICATION-READBACK.json','records/tree-create.json','records/commit-create.json','records/STAGED-PAYLOAD.json','final-audit/REPORT.md','final-audit/attempt001/INCIDENT.json','final-audit/attempt002/INCIDENT.json','final-package/VERIFICATION.json'],'other_member_coverage':'Inventory/hashes and selected JSON fields inspected; historical audit scripts/logs and every audit assertion were not reread or executed.'},
 'historical_unknown_operations':outcome['historical_unknown_operations'],
 'prior_worker_liveness':'unknown',
 'no_reconstruction_authority':{'conclusion':'No separately recorded reconstruction decision supplied in current assignment or found in inspected operative records. Continue requires exact source recovery or a separately recorded bounded decision.','evidence':['task.json#/next_action','task.json#/session_phase/exclusions','OUTCOME.json#/next_action','live terminal comments7113998703/7113999171','Director assignment scope']},
 'read_coverage':{'full_human_reads':['AGENTS.md','ROLE.md','PROTOCOL.md','HANDOFF.md','EPHEMERAL-HOST.md','C270 REQUIREMENTS.md','C270 PLAN.md','C271 REQUIREMENTS.md (all lines)','C271 PLAN.md (all unique text plus proven duplicate line sequences)','current P28 OUTCOME.json','current P28 RECONCILIATION.json','current P28 SESSION.md','current P28 BRANCH-INVENTORY.json','all returned P27/P28 comment bodies since18:00 UTC'],
 'selected_json_fields':{'C271 task.json':['schema/id/title/intent/status/owner/branch/base_sha/scope_issue','requirements descriptions/acceptance/status','plan','completion','next_action','session_phase','delivery','authorization','blocked_reason','remaining_h0_constraint','phase_reconciliations','p27_predecessor_reconciliation','p27_design_decision','checks filtered for p28 (none)'], 'branch CURRENT.json':['latest_task','active_task','observed_main','snapshot_date','next_action','latest_handoff','latest_recovery','pending_phase_delivery'],'C270 task.json':['status','owner','completion','next_action','session_phase','delivery'],'main CURRENT.json':['latest_task','active_task','next_action']},
 'machine_parsed': ['All selected JSON input bytes parsed successfully; complete API results retained. Parsing does not imply full semantic review.'],
 'gaps':['C271 historical JSON arrays and most historical checks/evidence-reference lists were not fully reread; portions appeared in truncated displays and are not counted as complete reads.','C270 historical checks and phase-history objects were not fully reread.','Large historical PR/issue bodies were searched for P28 but not completely reread.','No whole-repository tree search, Git object database enumeration, unrelated branch/archive search, original prior-host search, or prior chat tool-result inspection performed.','Actual Library artifact byte verification delegated to the independent artifact audit.','Full global startup/selected project skills handled by Director; child was not assigned a second global startup.'], 'plan_read_coverage':plan_coverage,'input_identities':identities},
 'limits':['Negative result is bounded to inspected live records; it does not prove that unreferenced immutable Git objects do not exist.','Original reported597/597 methods and945 protected files remain unverified; no target or product tests were run.','No GitHub or Library mutations; no index/main/branch changes; no original upload replay; no nested agents.'],
 'next_action':'Stop at P28-RECOVERY-BYTES-001. Director preserves this evidence and finishes the authorized verified recovery handoff. Original implementation may resume only after exact candidate/evidence recovery or a separate recorded reconstruction decision.'
}
(OUT/'AUDIT.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'verdict':report['verdict'],'checks_passed':report['checks_passed'],'checks_failed':report['checks_failed'],'report':str(OUT/'AUDIT.json')},indent=2))
