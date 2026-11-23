from pathlib import Path
import hashlib,json,subprocess,zipfile,stat,datetime,sys,platform

BASE=Path('/workspace/scratch/f8d879d19e34')
REPO=BASE/'OntoKin'
PHASE=BASE/'phase-p23'
MAIN='e43cc6c5777874101a40559e4058ad6826b07e51'
HEAD='51a00f21013386df6ee4ce3c3560c902b32c6af5'
OWNER='c271-p23-f8d879d19e34'
def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2)+'\n')
def git(*args):
    return subprocess.check_output(['git',*args],cwd=REPO)
assert git('rev-parse','HEAD').decode().strip()==HEAD
assert not git('status','--porcelain')
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
phase={
 'schema':'ontokin.c271.p23-phase/1','task':'C271','phase':'C271-P23-current-host-H0-plan','owner':OWNER,
 'declared_at_utc':now,'starting_revision':HEAD,'starting_tree':git('rev-parse','HEAD^{tree}').decode().strip(),
 'observed_main':{'sha':MAIN,'tree':'2a4712e9d1c6ddd2fb4571292e239d1b16bb5fda','observed_at_utc':now},
 'branch':'work/c271-missing-import-digest-control','pr':{'number':274,'state':'open','draft':True,'merged':False},
 'issue':{'number':273,'state':'open'},'main_lease_held':False,
 'scope':'Prepare and independently review a complete H0 operational plan for the current disposable host, reconstructing only required pinned inputs after reviewed preparation, or preserve the first concrete prerequisite blocker.',
 'acceptance':[
  'A01 Reconcile exact amended P22 and terminal receipt with current main/branch/PR/issue; verify and confirm early recovery save.',
  'A02 Read adopted H0 contracts; perform one bounded current-host readiness check with exact input identity; preserve prior evidence.',
  'A03 Independently accept complete H0 operational plan, or independently confirm first concrete blocker and reproducible next action.',
  'A04 Review documentary candidate; required workflow/documentation/whitespace checks; conditional retained-branch publication and exact readback.',
  'A05 Independently verify/freeze/save next ZIP and matching prompts; record separate delivery receipt; stop.'
 ],
 'stop':'Accepted H0 plan or first concrete missing prerequisite; after that only documentary review/publication and verified handoff.',
 'constraints':['No H1, original-seven methods, full routine, main integration, branch deletion or parent closure','No product/test/pin/contract changes','No previous-host path/process recovery','Retain frozen source commit 527368bd5195c439762b43e2cc836ff9822213f8 and original P22 inventory descriptor unchanged as historical evidence','Root owns Git/index/canonical records/publication/Library; workers own disjoint review directories; no nested fanout'],
 'parent_status':'in_progress','parent_complete':False,'h0_accepted':False,'h0_plan_accepted':False,
 'requirements':{'R01':'done','R02':'done','R03':'not_done','R04':'not_done','R05':'not_done'},'parent_plan':{'P01':'done','P02':'in_progress'},
 'phase_complete':False,'early_save_confirmed':False,'delivery_state':'early_save_pending',
 'current_unknown_operations':[],
 'historical_unknown_operations':['C270 ancillary broad-driver completion','Global prior-process termination','P13 read-only difflib completion; do not retry'],
 'workers':[{'id':'/root/archive_audit','owned':'phase-p23/reviews/archive','status':'startup archive review'},{'id':'/root/ledger','owned':'phase-p23/reviews/ledger','status':'startup ledger review'},{'id':'/root/h0_review','owned':'phase-p23/reviews/h0','status':'read-only governing-contract investigation'}],
 'capabilities':{'repository_read':'GitHub connector and authentic sparse Git checkout observed','repository_write':'Git object/update_ref tools with expected_sha available; not yet exercised','native_push':'not selected; prior diagnosed unavailable route not retried','terminal':'Linux x86_64 CPython 3.12.14 observed','subagents':'three actual fresh-context workers','zip':'stdlib creation and validation','library':'supplied artifacts downloaded; existing OntoKin folder resolved','merge_deletion':'not selected'},
 'next_action':'Verify/save/read back this early ZIP, then execute only A02/A03 within the selected boundary.',
 'readset':'READ-SET.json','package_type':'browser-session handoff for online GitHub continuation'
}
dump(PHASE/'state/PHASE.json',phase)
operations={'schema':'ontokin.c271.p23-startup-operations/1','read_only_failures':[
 {'operation':'Library materialize using truncated share-link identifier','result':'INVALID_ARGUMENT','resolution':'Exact full identifier resolved by folder listing; current helper downloaded exact listed item once'},
 {'operation':'GitHub encoded branch URL','result':'INVALID_ARGUMENT','resolution':'Literal branch-path fetch succeeded; observed exact branch head'},
 {'operation':'git status before initial checkout','result':'no-checkout clone showed index-to-empty-worktree deletions','resolution':'Applied sparse checkout and selected existing branch; clean authentic checkout verified'},
 {'operation':'large required-record output','result':'tool display truncation','resolution':'Complete source bytes retained; current task fields inspected, full active task records delegated to ledger; read gaps explicit'}],
 'remote_mutations':[],'unpublished_repository_work':False,'current_unknown_operations':[],
 'prior_source_time_delivery_pending':'P22 exact matching live terminal markers and saved terminal receipt resolve delivery only; no re-execution.',
 'authority_reconciliation':'Current main ephemeral-host policy governs older branch copies; branch C271 remains authorized by latest user continuation.'}
dump(PHASE/'state/STARTUP-OPERATIONS.json',operations)

stage=BASE/'early-stage'
assert not stage.exists();stage.mkdir()
def put(name,data):
    p=stage/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
def text(name,value):put(name,value.encode())
source=[]
main_paths=['CHATGPT-START-HERE.md','AGENTS.md','GOAL.md','STATUS.md','ROLE.md','docs/workflow/registry.json','docs/workflow/CURRENT.json','docs/workflow/PROTOCOL.md','docs/workflow/HANDOFF.md','docs/workflow/EPHEMERAL-HOST.md','docs/workflow/BROWSER-PROMPTS.md','docs/workflow/prompts/CONTINUE.md','docs/workflow/prompts/RECOVER.md','.agents/skills/ontokin-session/SKILL.md','.agents/skills/ontokin-delivery/SKILL.md','.agents/skills/ontokin-learning/SKILL.md']
for ref,paths,prefix in [(MAIN,main_paths,'repository/main/'),(HEAD,['docs/workflow/CURRENT.json','docs/workflow/tasks/C271/task.json','docs/workflow/tasks/C271/REQUIREMENTS.md','docs/workflow/tasks/C271/PLAN.md'],'repository/branch/')]:
    for path in paths:
        data=git('show',ref+':'+path);name=prefix+path;put(name,data)
        source.append({'member':name,'commit':ref,'path':path,'git_blob':git('rev-parse',ref+':'+path).decode().strip(),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
readset={'observed_main':MAIN,'initial_required_main':'Director read complete required files once; STATUS excluded exactly 50 navigation-only empty a-tag lines; exact bytes retained','main_gap':'No unresolved required main instruction gap','active_task':'Complete JSON decoded and current fields inspected by Director; full current task/requirements/plan inspected by independent ledger worker','selected_skills':['ontokin-session','ontokin-delivery','ontokin-learning'],'scope_contracts':'H0 reviewer acquiring applicable adopted contract list; A02 remains pending','snapshots':source}
dump(PHASE/'state/READ-SET.json',readset)
put('READ-SET.json',(PHASE/'state/READ-SET.json').read_bytes())
put('CHECKPOINT.json',(PHASE/'state/PHASE.json').read_bytes())
text('README-START-HERE.md','# OntoKin C271 P23 early recovery\n\nBrowser-session handoff for online GitHub continuation. Each fresh chat uses a different disposable host. Never recover old temporary paths or workers. Read HOST-ENVIRONMENT.md, CHECKPOINT.json and HANDOFF.md; then read actual live main CHATGPT-START-HERE.md and required instructions.\n\nSource branch '+HEAD+'; observed main '+MAIN+'. This early recovery precedes technical H0 work. Reconcile any later GitHub commits and separate save receipt before retrying. Prior P22 artifacts are external immutable history; their exact identities are in HISTORICAL-DEPENDENCIES.json.\n')
text('HOST-ENVIRONMENT.md','# Fresh disposable host\n\nEvery new ChatGPT browser discussion has a different disposable execution host. Old /workspace and /tmp paths, environments, installations and processes are historical only. Recreate only task-required inputs from exact GitHub commits and verified saved artifacts in current-session paths. Do not search old hosts. Current host observations here apply only to c271-p23-f8d879d19e34. Follow live main docs/workflow/EPHEMERAL-HOST.md.\n')
text('HANDOFF.md','# P23 early checkpoint\n\nStartup has identified existing C271 branch, draft PR274 and open issue273. P22 terminal markers match and its saved receipt SHA-256 is verified. Main policy e43cc6c applies. R01/R02 done; R03-R05 not_done and parent plan P02 in_progress.\n\nNo technical H0 preparation or target execution has occurred. Three independent workers are performing read-only startup/contract review. Root owns all writes. Main lease is not selected. Confirm early save before A02. At accepted H0 plan or first blocker, perform only documentary publication and final delivery. No H1, original-seven/full routine or integration. Historical failures and unknown operations remain unchanged.\n')
text('NEXT-TASK.md','# Resume P23 only\n\nReconcile live branch/PR/issue and the separately saved early receipt. If this is the latest checkpoint, finish missing startup/early-save checks, read adopted H0 contracts, perform one bounded current-host readiness check and independently review the complete H0 plan or first concrete blocker. Reconstruct only necessary inputs after concrete preparation review. Preserve historical receipts unchanged. Stop at this phase boundary and save the verified final handoff.\n')
text('RECOVERY-STATUS.md','# Recovery state\n\nNo unpublished repository changes or uncertain remote writes at early freeze. Current workers have independent review-only assignments; no target child command exists. Prior C270 broad-driver completion, global old-process termination and P13 difflib completion remain unknown historical observations and must not be replayed. This ZIP preserves unique startup state and exact Git snapshots; live GitHub and linked Library artifacts are external dependencies. It is not a full offline repository backup.\n')
common='Repository: https://github.com/Omegapy/OntoKin\n\nEvery new ChatGPT browser chat uses a different disposable host. Old paths, environments and workers do not persist. Use verified GitHub/Library artifacts and reconstruct only task-needed inputs. Read README-START-HERE.md, CHECKPOINT.json and live main CHATGPT-START-HERE.md with its required instructions once at the observed revision. Reconcile branch, draft PR274, issue273, ownership, tests, saves and unpublished work. Follow PROTOCOL and HANDOFF. Resume C271 P23 only, confirm early recovery before substantial work, use independent subagents, and stop at accepted H0 plan or first concrete prerequisite blocker. No H1, original seven/full routine, main integration or second phase. Save verified ZIP and matching prompts plus separate actual receipt, then stop. Keep C271 open.\n'
text('PROMPT-1-CONTINUE.md','# Continue C271 P23 from early recovery\n\n'+common)
text('PROMPT-2-RECOVER.md','# Recover interrupted C271 P23\n\n'+common+'\nCheck any later GitHub checkpoint and exact Library save result before retrying. Completed technical work requires delivery-only recovery; never replay an uncertain operation or start another phase.\n')
deps=json.loads((BASE/'handoff-input/HISTORICAL-DEPENDENCIES.json').read_text())
dump(stage/'HISTORICAL-DEPENDENCIES.json',{'schema':'ontokin.c271.p23-external-dependencies/1','predecessor':json.loads((BASE/'input/OntoKin/OntoKin_C271_P22_Ephemeral_Host_Amendment_Delivery_Receipt_2026-11-22.json').read_text()),'p22_terminal':json.loads((BASE/'state/p22-terminal.json').read_text())['terminal_receipt'],'inherited':deps,'purpose':'Online continuation; C262 full historical/offline retention remains separate and unchanged'})
dump(stage/'SOURCE-MANIFEST.json',{'files':source})
for root,prefix in [(BASE/'state','recovery/startup/'),(PHASE/'state','recovery/phase/')]:
    for p in sorted(root.rglob('*')):
        if p.is_file():put(prefix+p.relative_to(root).as_posix(),p.read_bytes())
put('recovery/build_early.py',Path(__file__).read_bytes())
payload=[]
for p in sorted(stage.rglob('*')):
    if p.is_file():
        data=p.read_bytes();payload.append({'path':p.relative_to(stage).as_posix(),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
dump(stage/'MANIFEST-SHA256.json',{'schema':'ontokin.handoff-manifest/1','files':payload})
out=BASE/'packages/OntoKin_C271_P23_H0_Plan_Early_Recovery_2026-11-22.zip';out.parent.mkdir(exist_ok=True)
assert not out.exists()
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(stage.rglob('*')):
        if p.is_file():z.write(p,p.relative_to(stage).as_posix())
with zipfile.ZipFile(out) as z:
    assert z.testzip() is None
    assert len(z.namelist())==len(set(z.namelist()))
    for e in payload:
        data=z.read(e['path']);assert len(data)==e['bytes'] and hashlib.sha256(data).hexdigest()==e['sha256']
    extract=BASE/'early-verify';assert not extract.exists();z.extractall(extract)
    for e in payload:assert (extract/e['path']).read_bytes()==(stage/e['path']).read_bytes()
identity={'file_name':out.name,'path':str(out),'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'members':len(payload)+1,'payloads':len(payload),'source_bindings':len(source),'root_verified':True,'independent_review':'pending','save':'pending'}
dump(PHASE/'state/EARLY-IDENTITY.json',identity)
print(json.dumps(identity))
