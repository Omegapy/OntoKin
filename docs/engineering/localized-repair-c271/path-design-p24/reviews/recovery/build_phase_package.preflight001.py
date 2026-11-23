from pathlib import Path
import datetime, hashlib, json, subprocess, zipfile

ROOT = Path(__file__).resolve().parent
REPO = ROOT / 'OntoKin'
MAIN = 'e43cc6c5777874101a40559e4058ad6826b07e51'
START = '3bc46e80f3d59616110b218740a5f5f3dd688a57'
OWNER = 'c271-p24-660f372e2414'
PHASE = 'C271-P24-H0-path-design-adoption'
BRANCH = 'work/c271-missing-import-digest-control'
PREFIX = 'docs/engineering/localized-repair-c271/path-design-p24'

def git(*args):
    return subprocess.check_output(['git', '-C', str(REPO), *args])

def sha(data):
    return hashlib.sha256(data).hexdigest()

def js(value):
    return (json.dumps(value, indent=2) + '\n').encode()

def build(kind='early', source=START):
    out = ROOT / 'packages' / kind
    out.mkdir(parents=True, exist_ok=True)
    payload = {}
    bindings = []
    main_files = ['CHATGPT-START-HERE.md', 'AGENTS.md', 'GOAL.md', 'STATUS.md', 'ROLE.md',
      'docs/workflow/registry.json', 'docs/workflow/PROTOCOL.md', 'docs/workflow/HANDOFF.md',
      'docs/workflow/BROWSER-PROMPTS.md', 'docs/workflow/EPHEMERAL-HOST.md',
      '.agents/skills/ontokin-session/SKILL.md', '.agents/skills/ontokin-delivery/SKILL.md',
      '.agents/skills/ontokin-learning/SKILL.md',
      'docs/engineering/OK-ENG-006-local-validation-and-hosted-ci-policy.md',
      'docs/engineering/OK-ENG-009-development-integration-and-branch-lifecycle.md']
    branch_files = ['docs/workflow/CURRENT.json', 'docs/workflow/tasks/C271/task.json',
      'docs/workflow/tasks/C271/REQUIREMENTS.md', 'docs/workflow/tasks/C271/PLAN.md',
      'docs/engineering/localized-repair-c271/h0-plan-p23/P23-DELIVERY.json',
      'docs/engineering/localized-repair-c271/h0-plan-p23/OUTCOME.json',
      'docs/engineering/localized-repair-c271/h0-plan-p23/reviews/h0/BLOCKER-REVIEW.json']
    if kind == 'final':
        branch_files += git('ls-tree', '-r', '--name-only', source, PREFIX, 'docs/workflow/tasks/C271/P24-SESSION.md').decode().splitlines()
    for revision, paths in [(MAIN, main_files), (source, branch_files)]:
        for path in sorted(set(paths)):
            data = git('show', revision + ':' + path)
            target = 'repository/' + path
            payload[target] = data
            bindings.append({'path': target, 'repository_path': path, 'commit': revision,
                             'bytes': len(data), 'sha256': sha(data)})
    predecessor = ROOT / 'input/OntoKin_C271_P23_H0_Path_Blocker_Recommendation_Amendment_2026-11-23.zip'
    payload['history/' + predecessor.name] = predecessor.read_bytes()
    payload['history/OWNER-RECOMMENDATION-2026-11-23.md'] = (ROOT / 'input/extracted/OWNER-RECOMMENDATION-2026-11-23.md').read_bytes()
    payload['recovery/RECONCILIATION.json'] = (ROOT / 'records/RECONCILIATION.json').read_bytes()
    payload['recovery/build_phase_package.py'] = Path(__file__).read_bytes()
    inherited = json.loads((ROOT / 'input/extracted/HISTORICAL-DEPENDENCIES.json').read_text())
    payload['HISTORICAL-DEPENDENCIES.json'] = js({'schema':'ontokin.c271.p24-dependencies/1',
      'immediate_predecessor':{'archive_member':'history/'+predecessor.name,
      'library_file_id':'libfile_fde3_f-a7a282874a748191b524f12a3b59c21e_2ab2a24d43748191957f9bcc356b59de',
      'bytes':predecessor.stat().st_size,'sha256':sha(predecessor.read_bytes()),
      'receipt_library_file_id':'libfile_fde3_f-7c650ce73d708191a6522e9ccbae583c_2ab2a24d43748191957f9bcc356b59de'},
      'inherited_p23_dependencies':inherited,
      'inherited_member_path_base':'All member paths in inherited_p23_dependencies refer to the nested immediate_predecessor archive, not this ZIP root.',
      'purpose':'Online continuation; historical full offline C262 restoration is not claimed.'})
    if kind == 'final':
        payload['recovery/initialize_p24.py'] = (ROOT/'records/initialize_p24.py').read_bytes()
        payload['recovery/run_documentary_checks.py'] = (ROOT/'records/run_documentary_checks.py').read_bytes()
        payload['recovery/P24-TRANSFER.attempt001.patch'] = (ROOT/'reviews/recovery/P24-TRANSFER.attempt001.patch').read_bytes()
        rejected = ROOT/'packages/early-attempt001/OntoKin_C271_P24_H0_Path_Design_Early_Recovery_2026-11-23.zip'
        payload['recovery/rejected-early-attempt001.zip'] = rejected.read_bytes()
        old_current = git('show',MAIN+':docs/workflow/CURRENT.json')
        payload['history/main-CURRENT.json'] = old_current
        bindings.append({'path':'history/main-CURRENT.json','repository_path':'docs/workflow/CURRENT.json','commit':MAIN,'bytes':len(old_current),'sha256':sha(old_current)})
    scope = 'One narrow design/adoption decision for absent loader-candidate ancestors and parent-traversing loader aliases, or independently justified retained refusal with a concrete alternative.'
    stop = 'Stop at the independently accepted design/adoption decision or first concrete blocker; then documentary checks, conditional retained-branch publication and verified handoff only.'
    next_action = 'Reconcile this early recovery and exact live refs. Confirm its external save receipt before substantive design. Complete one independently reviewed path-representation decision; do not implement or execute H0/H1/product validation.'
    state = 'early_recovery_before_substantial_work'
    if kind == 'final':
        next_action = 'In a fresh chat reconcile P24 delivery, then implement only the independently adopted versioned path policy and its required positive/refusal controls. Stop at reviewed bounded implementation or the first concrete blocker, before H0/H1 and the full routine.'
        state = 'technical_phase_complete_final_save_pending'
    checkpoint = {'schema':'ontokin.c271.p24-checkpoint/1','task':'C271','phase':PHASE,'owner':OWNER,
      'kind':kind,'package_type':'browser-session handoff for online GitHub continuation',
      'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
      'user_facing_date':'2026-11-23','user_timezone':'America/Denver','observed_main':MAIN,
      'observed_main_tree':git('rev-parse',MAIN+'^{tree}').decode().strip(),
      'branch':BRANCH,'source_commit':source,'source_tree':git('rev-parse',source+'^{tree}').decode().strip(),
      'pr':{'number':274,'state':'open','draft':True,'merged':False},'issue':{'number':273,'state':'open'},
      'main_lease_held':False,'scope':scope,'acceptance':'Independent acceptance of a closed safe approach to both recorded path cases, or justified refusal with one concrete alternative.',
      'stop':stop,'requirements':{'R01':'done','R02':'done','R03':'not_done','R04':'not_done','R05':'not_done'},
      'parent_plan':{'P01':'done','P02':'in_progress'},'parent_status':'in_progress','parent_complete':False,
      'h0_accepted':False,'h1_executed':False,'production_implementation_changed':False,
      'delivery_state':state,'current_unknown_operations':[],
      'historical_unknown_operations':['C270 ancillary broad-driver completion','Global prior-process termination','P13 read-only difflib completion; do not retry'],
      'next_action':next_action,'receipt_path':PREFIX+'/P24-DELIVERY.json',
      'read_set_note':('Main mandatory instructions read in full once, excluding exactly 50 STATUS anchor-only lines permitted by START. Large branch records parsed for active fields; independent complete review is pending at this early freeze. Truncated first display is not claimed as full Director text read.' if kind=='early' else 'Main mandatory instructions read fully once except the 50 permitted anchor-only STATUS lines. Large branch records parsed by Director and completely independently reviewed against starting Git revision; exact coverage and duplicate reuse in review evidence. No truncated display is claimed as complete.')}
    payload['CHECKPOINT.json'] = js(checkpoint)
    host = '# Disposable execution host\n\nEvery fresh ChatGPT browser thread uses a different disposable host. Previous paths, environments, workers and installation receipts are historical evidence only. Use live GitHub and verified artifacts; reconstruct only inputs indispensable for the selected gate in fresh paths. P24 is design-only and needs no target runtime reconstruction. No prior host search or system loader mutation is authorized.\n'
    payload['HOST-ENVIRONMENT.md'] = host.encode()
    payload['README-START-HERE.md'] = ('# OntoKin C271 P24 '+kind+' handoff\n\nBrowser-session handoff for online GitHub continuation; not a complete offline repository backup.\n\n'+host.split('\n\n',1)[1]+'\nRead HOST-ENVIRONMENT.md, CHECKPOINT.json, HANDOFF.md and NEXT-TASK.md, then reconcile live GitHub CHATGPT-START-HERE.md and all required instructions. Main instructions are frozen at '+MAIN+'; active branch records at '+source+'. SOURCE-MANIFEST.json binds every repository snapshot.\n\nThe exact recommendation-amended P23 archive is included under history. Its separate delivery receipt and matching original P23 live terminal markers were reconciled. Main CURRENT still names completed C270; active C271 branch/PR274/issue273 govern unfinished task state. No main integration is selected.\n\n'+scope+' '+stop+'\n\nA later separate P24-DELIVERY.json resolves only this package save status. It cannot pass H0/H1, R03-R05 or complete C271.\n').encode()
    payload['HANDOFF.md'] = ('# P24 phase boundary\n\n'+scope+'\n\nAcceptance: independent review of both cases, closed versioned schema/finite guards/literal candidate equality and negative-control requirements, or evidence-backed refusal with a concrete alternative. Required finish: documentation/workflow/whitespace checks, source preservation, conditional branch publication, verified saved ZIP and matching prompts with separate receipt.\n\n'+stop+'\n\nR01/R02 remain done; R03-R05 remain not_done. PR274 remains draft/open/unmerged; issue273 open. Main is unchanged; no lease held. Original routine failures and historical unknown operations retain their meanings. No production code, tests, pins, H0/H1, product validation, package installation, main integration or branch deletion belongs to P24.\n\n'+('This early package precedes substantive design work and claims no design decision.\n' if kind=='early' else 'See repository/'+PREFIX+'/DECISION.md, ADOPTION.json, OUTCOME.json and independent review for exact design result, limitations and future implementation obligations.\n')).encode()
    payload['NEXT-TASK.md'] = ('# Next action\n\n'+next_action+'\n\nKeep C271 open until R03-R05 actually pass. Future implementation, current-host H0/H1 and original required routine are distinct gates; design acceptance is none of those.\n').encode()
    payload['RECOVERY-STATUS.md'] = ('# Recovery status\n\nNo current uncertain remote operation is known at freeze. The supplied amendment archive preserves unique P23 recovery bytes. Repository history remains in Git; this is not a full offline backup. The exact main and active branch sources are identified in SOURCE-MANIFEST.json. Historical process uncertainties are retained in CHECKPOINT.json and must not be replayed.\n\n'+('Substantive P24 design has not started. /root/recovery_audit is assigned read-only incoming/early-package audit; its later report belongs to the separate receipt. No runtime worker is running.\n' if kind=='early' else 'P24 technical work is stopped. Inspect the external delivery receipt and live branch before retrying any save/publication. Resume delivery only if unconfirmed; otherwise the next technical phase requires a fresh chat.\n')).encode()
    for n, recovery in [('PROMPT-1-CONTINUE.md',False),('PROMPT-2-RECOVER.md',True)]:
        payload[n] = ('# '+('Recover' if recovery else 'Continue')+' OntoKin C271\n\nRepository: https://github.com/Omegapy/OntoKin\n\nUse this P24 '+kind+' handoff and its separate confirmed Library receipt. Every new ChatGPT browser thread is a different disposable host. Prior paths, installations and workers are history, not current resources.\n\n1. Open README-START-HERE.md, HOST-ENVIRONMENT.md and CHECKPOINT.json. Read live main CHATGPT-START-HERE.md and required instructions once; reconcile active task/plan, branch/PR/issue, ownership, checks, receipts and unpublished work. GitHub governs current state.\n2. '+('Reconcile uncertain operations before any retry. If the technical stopping point was already reached and final delivery is incomplete, finish delivery only and stop. A confirmed early recovery before technical work permits resuming its same unfinished phase after reconciliation. Otherwise ' if recovery else '')+next_action+'\n3. Declare one phase, acceptance and stop; confirm an early recovery ZIP before substantial work. Delegate independent bounded work to real subagents, preserve failures and unique bytes.\n4. At the phase boundary verify and save the ZIP and matching prompts in the existing OntoKin folder and publish its separate receipt. Report actual checks, branch/main state, limits and first remaining action. Keep parent open until all gates pass. Do not start a second phase.\n\nNo prior save receipt proves current runtime readiness. No test/guard/pin waiver or host-loader mutation.\n').encode()
    payload['SOURCE-MANIFEST.json'] = js({'schema':'ontokin.source-bindings/1','files':bindings})
    payload['MANIFEST-SHA256.json'] = js({'schema':'ontokin.payload-manifest/1','files':[{'path':p,'bytes':len(b),'sha256':sha(b)} for p,b in sorted(payload.items())]})
    name = 'OntoKin_C271_P24_H0_Path_Design_'+('Early_Recovery' if kind=='early' else 'Handoff')+'_2026-11-23.zip'
    archive = out/name
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p,b in sorted(payload.items()): z.writestr(p,b)
    extract = out/'verification'
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert len(set(z.namelist())) == len(z.namelist())
        for p in z.namelist():
            pp=Path(p); assert not pp.is_absolute() and '..' not in pp.parts
        z.extractall(extract)
    for rec in json.loads(payload['MANIFEST-SHA256.json'])['files']:
        b=(extract/rec['path']).read_bytes(); assert len(b)==rec['bytes'] and sha(b)==rec['sha256']
    for rec in bindings:
        assert (extract/rec['path']).read_bytes()==git('show',rec['commit']+':'+rec['repository_path'])
    result={'path':str(archive),'file_name':name,'bytes':archive.stat().st_size,'sha256':sha(archive.read_bytes()),'members':len(payload),'source_bindings':len(bindings),'root_verification':'passed','source_commit':source,'source_tree':checkpoint['source_tree']}
    (out/'BUILD-RESULT.json').write_bytes(js(result))
    for name,member in [('Continue','PROMPT-1-CONTINUE.md'),('Recover','PROMPT-2-RECOVER.md')]:
        (out/('OntoKin_C271_P24_'+name+'_2026-11-23.md')).write_bytes(payload[member])
    print(json.dumps(result))

if __name__ == '__main__':
    import sys
    build(*(sys.argv[1:]))
