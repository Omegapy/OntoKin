from pathlib import Path
import datetime,hashlib,json,subprocess,zipfile,os

ROOT=Path('/workspace/scratch/bef4a6dd8f04/recovery/independent_review/core-records')
BASE=Path('/workspace/scratch/bef4a6dd8f04')
REPO=BASE/'OntoKin'
PARENT='e26dc6369a8d6ba88ea779b26a8c655121ae5dbc'
TREE='f7348aa84a02a3d2770b722ca6b1246e7c9ba3ed'
PHASE='docs/engineering/localized-repair-c271/loader-path-p14/'
REC=PHASE+'delivery-recovery-20261121/'
MAIN='e1a48f7d0635e9aa4f4b6d6a586e7305eb81999d'
checks=[]
def git(*args):return subprocess.check_output(['git','-C',str(REPO),*args])
def read(p,rev=TREE):return git('show',rev+':'+p)
def data(p,rev=TREE):return json.loads(read(p,rev))
def sha(b):return hashlib.sha256(b).hexdigest()
def check(name,condition,details=None):checks.append({'name':name,'passed':bool(condition),'details':details})
def dump(name,d):(ROOT/name).write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
def tree(rev):
    result={}
    for b in git('ls-tree','-r','-z',rev).split(b'\0'):
        if b:
            a,p=b.split(b'\t');mode,kind,oid=a.decode().split();result[p.decode()]=(mode,kind,oid)
    return result

expected_tree=tree(TREE);base_tree=tree(PARENT)
changed=git('diff','--name-only',PARENT,TREE).decode().splitlines()
check('exact_declared_parent_and_tree',git('rev-parse','HEAD').decode().strip()==PARENT and git('cat-file','-t',TREE).decode().strip()=='tree')
check('45_documentary_paths_only',len(changed)==45 and all(p.startswith('docs/') for p in changed) and all(p.startswith(REC) or p==PHASE+'P14-DELIVERY.json' or p in ['docs/workflow/CURRENT.json','docs/workflow/tasks/C271/task.json','docs/workflow/tasks/C271/REQUIREMENTS.md','docs/workflow/tasks/C271/PLAN.md'] for p in changed))
index={}
for b in git('ls-files','--stage','-z').split(b'\0'):
    if b:
        a,p=b.split(b'\t');mode,oid,stage=a.decode().split();index[p.decode()]=(mode,'blob',oid)
check('index_exact_candidate_tree',index==expected_tree)
rows=[];jsonerrors=[]
for p in changed:
    b=read(p)
    if p.endswith('.json'):
        try:json.loads(b)
        except Exception as e:jsonerrors.append({'path':p,'error':str(e)})
    rows.append({'path':p,'bytes':len(b),'sha256':sha(b),'git_blob':expected_tree[p][2],'mode':expected_tree[p][0],'working_bytes_equal':(REPO/p).read_bytes()==b})
check('all45_payloads_read_working_equal_valid_json',all(r['working_bytes_equal'] for r in rows) and not jsonerrors and not git('diff','--name-only').strip(),jsonerrors)
dump('CHANGED-FILES.json',rows)
check('frozen_original_p14_records_source_unchanged',all(expected_tree[p]==base_tree[p] for p in base_tree if p.startswith(PHASE)) and expected_tree['prototypes/static_tray_v01/current_host_inspection_v01.py']==base_tree['prototypes/static_tray_v01/current_host_inspection_v01.py'] and expected_tree['tests/test_current_host_loader_path_v01.py']==base_tree['tests/test_current_host_loader_path_v01.py'])

copy_map={'early-review/attempt001/':'recovery/independent_review/early/','early-review/attempt002/':'recovery/independent_review/early-attempt002/','implementation-review/':'recovery/independent_review/implementation/','final-package-review/':'recovery/final_package_review/','state-review/':'recovery/remote_audit/'}
copies=[]
for p in changed:
    if p.startswith(REC):
        sub=p[len(REC):]
        for dest,orig in copy_map.items():
            if sub.startswith(dest):
                source=BASE/(orig+sub[len(dest):]);copies.append({'path':p,'source':str(source),'exact_bytes':source.read_bytes()==read(p)});break
check('copied_independent_reviews_exact',bool(copies) and all(r['exact_bytes'] for r in copies),{'count':len(copies),'mismatches':[r for r in copies if not r['exact_bytes']]})
dump('EVIDENCE-COPY-BINDINGS.json',copies)

saved=json.loads((BASE/'recovery/evidence/FINAL-SAVE-RECEIPT.json').read_bytes());upload=json.loads((BASE/'recovery/evidence/FINAL-UPLOAD-RESULT.json').read_bytes())['results'];delivery=data(PHASE+'P14-DELIVERY.json')
check('core_receipt_exact_save_and_upload_ids',read(REC+'FINAL-SAVE-RECEIPT.json')==(BASE/'recovery/evidence/FINAL-SAVE-RECEIPT.json').read_bytes() and delivery['files']==saved['files'] and delivery['archive']==saved['files'][0] and delivery['matching_prompts']==saved['files'][1:] and all(all(row[k]==r[k] for k in r) for row,r in zip(saved['files'],upload)) and saved['all_saved'] and saved['all_readbacks_verified'])
file_checks=[]
for row in saved['files']:
    local=Path(row['local_path']);back=Path(row['readback_path']);a=local.read_bytes();b=back.read_bytes()
    file_checks.append({'role':row['role'],'file_id':row['file_id'],'library_file_id':row['library_file_id'],'version':row['version'],'bytes':len(a),'sha256':sha(a),'passed':a==b and len(a)==row['bytes'] and sha(a)==row['sha256'] and row['status']=='succeeded' and row['saved_bytes_readback_equal'] and row['version']==row['current_version_number']==0})
check('all_three_actual_readback_hashes_and_versions',all(r['passed'] for r in file_checks),file_checks)
with zipfile.ZipFile(saved['files'][0]['local_path']) as z:
    check('matching_saved_prompts_equal_frozen_members',all(Path(r['readback_path']).read_bytes()==z.read(r['archive_member']) for r in saved['files'][1:]))
check('final_zip_exact_existing_identity',saved['files'][0]['bytes']==88651427 and saved['files'][0]['sha256']=='96dd48ac7cfe01219f57a48a3adfaacb1faa21325f72c5ad06ca19fcd54760cd' and saved['original_final_zip_reused_without_changes'])
early=data(REC+'EARLY-RECOVERY-RECEIPT.json');ea=Path(early['local_path']).read_bytes();eb=Path(early['readback_path']).read_bytes()
check('early_saved_identity_exact',ea==eb and len(ea)==early['bytes']==81161841 and sha(ea)==early['sha256']=='638251a2baa543fd22121882425097c77af39a440c753510fd7cc21bd178e456' and early['library_file_id']=='libfile_fde3_f-c8807711ae6c81918f89e401615170f8_2ab2a24d43748191957f9bcc356b59de' and early['version']==0)

current=data('docs/workflow/CURRENT.json');prior_current=data('docs/workflow/CURRENT.json',PARENT)
check('all_prior_handoff_recovery_objects_preserved',current['previous_handoff']==prior_current['latest_handoff'] and prior_current['previous_handoff'] in current['older_handoffs'] and all(x in current['older_handoffs'] for x in prior_current['older_handoffs']) and current['previous_recovery']==prior_current['latest_recovery'] and prior_current['previous_recovery'] in current['older_recoveries'] and all(x in current['older_recoveries'] for x in prior_current['older_recoveries']) and current['historical_handoff']==prior_current['historical_handoff'],{'prior_older_handoffs':len(prior_current['older_handoffs']),'current_older_handoffs':len(current['older_handoffs']),'prior_older_recoveries':len(prior_current['older_recoveries']),'current_older_recoveries':len(current['older_recoveries'])})
check('current_latest_identities_and_pending_receipt',all(current['latest_handoff'][k]==v for k,v in saved['files'][0].items()) and current['latest_handoff']['matching_prompts']==saved['files'][1:] and current['latest_handoff']['terminal_receipt_status']=='pending' and all(current['latest_recovery'][k]==v for k,v in early.items() if k!='receipt'))
task=data('docs/workflow/tasks/C271/task.json');prior_task=data('docs/workflow/tasks/C271/task.json',PARENT)
historical=['prior_session_phases','prior_phase_deliveries','historical_checks','blocked_reason_history','prior_h0_constraints']
check('task_all_historical_arrays_unchanged',all(task[k]==prior_task[k] for k in historical) and all(x in task['checks'] for x in prior_task['checks']) and len(task['checks'])==len(prior_task['checks'])+1,{k:len(task[k]) for k in historical})
check('requirements_acceptance_unchanged_evidence_additive',all(all(new[k]==old[k] for k in old if k!='evidence') and set(old['evidence'])<=set(new['evidence']) for old,new in zip(prior_task['requirements'],task['requirements'])))
check('requirements_plan_text_append_only',all(read(p).startswith(read(p,PARENT)) and b'<!-- C271-P14-RECOVERY-CORE -->' in read(p)[len(read(p,PARENT)):] for p in ['docs/workflow/tasks/C271/REQUIREMENTS.md','docs/workflow/tasks/C271/PLAN.md']))
expected_requirements={'R01':'done','R02':'done','R03':'not_done','R04':'not_done','R05':'not_done'}
check('parent_requirements_plan_remain_open',task['status']==delivery['parent_status']=='blocked' and not delivery['parent_complete'] and {r['id']:r['status'] for r in task['requirements']}==delivery['requirements']==expected_requirements and task['plan']==prior_task['plan'] and delivery['plan']=={'P01':'done','P02':'in_progress'} and not task['delivery']['phase_complete'])
check('main_branch_pr_issue_and_lease_limits',current['observed_main']==delivery['main']==MAIN and delivery['main_unchanged'] and delivery['branch']=='work/c271-missing-import-digest-control' and delivery['branch_disposition']=='retained_unfinished' and delivery['pull_request']=={'number':274,'state':'open','draft':True,'merged':False} and delivery['scope_issue']=={'number':273,'state':'open'} and not delivery['main_lease_held'] and not delivery['integration_performed'])
check('implementation_publication_reconciled_not_replayed',delivery['implementation_publication']=={'commit':PARENT,'tree':'0271ee6a507f83015eea06b63b1bed51753ba419','changed_files_verified':28,'replayed':False} and task['completion']['loader_path_implementation']['commit']==PARENT and task['session_phase']['published_source']['commit']==PARENT)
check('terminal_checks_and_publication_honestly_pending',delivery['status']=='core_delivery_confirmed_terminal_receipt_pending' and delivery['terminal_receipt']['status']=='pending' and delivery['recovery_record_checks'].startswith('Pending at core snapshot') and task['delivery']['status']=='core_saved_terminal_receipt_pending' and not task['session_phase']['phase_complete'] and not (REPO/(PHASE+'P14-TERMINAL-CONFIRMATION.json')).exists())
check('historical_runtime_and_audit_counts_separate',delivery['verification']['runtime_controls_previously_passed']==96 and delivery['verification']['inherited_methods_previously_passed']==175 and delivery['verification']['runtime_rerun_in_recovery'] is False and delivery['review']['implementation_reuse_groups_passed']==35 and delivery['review']['final_package_groups_passed']==22 and delivery['review']['new_early_groups_passed']==17 and data(REC+'implementation-review/AUDIT.json')['runtime_tests_this_review']=='not_run')
check('N57_unmet_and_unrun_gates_retained',delivery['verification']['N57_runtime_pass'] is False and delivery['verification']['actual_loader_completeness']=='unestablished' and set(delivery['unrun'])=={'H0/H1','runtime installation','Node/ldd','original-seven/full routine','native/model/hosted execution','main integration'} and set(delivery['historical_unknowns'])=={'C270 broad-driver completion','Global prior-process termination','P13 read-only difflib completion'})
locations=data(REC+'EVIDENCE-LOCATIONS.json')
check('raw_evidence_future_terminal_location_explicit',locations['terminal_save_status']=='pending' and locations['terminal_receipt_filename']==delivery['terminal_receipt']['file_name'] and 'separately saved terminal receipt' in locations['published_summary'] and 'eventual Library identity' in read(REC+'README.md').decode())
check('one_phase_stop_boundary',all('then stop' in s and 'fresh' in s and 'stop before H1' in s for s in [task['next_action'],current['next_action']['summary'],delivery['exact_next_action']]) and task['session_phase']['integration_allowed'] is False)

commands=json.loads((BASE/'recovery/publication/core/CHECKS.json').read_bytes());logchecks=[]
for c in commands['checks']:
    for channel in ['stdout','stderr']:
        path=BASE/'recovery/publication/core'/(c['name']+'.'+channel)
        logchecks.append({'name':c['name'],'channel':channel,'match':sha(path.read_bytes())==c[channel+'_sha256']})
check('four_checks_bind_exact_candidate_and_logs',commands['checked_staged_tree']==TREE and commands['source_commit']==PARENT and len(commands['checks'])==4 and commands['all_passed'] and all(c['passed'] and c['exit_code']==0 for c in commands['checks']) and all(r['match'] for r in logchecks),logchecks)
check('final_candidate_still_stable',not git('diff','--name-only').strip() and git('rev-parse','HEAD').decode().strip()==PARENT and all(read(r['path'])==(REPO/r['path']).read_bytes() for r in rows))

result={'schema':'ontokin.c271.p14-core-records-independent-review/1','reviewer':'/root/evidence_review','at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewed_tree':TREE,'parent_commit':PARENT,'changed_paths':len(rows),'verdict':'accepted_for_conditional_publication' if all(c['passed'] for c in checks) else 'findings','checks':checks,'passed':sum(c['passed'] for c in checks),'failed':sum(not c['passed'] for c in checks),'mandatory_findings':[c for c in checks if not c['passed']],'limits':['Review is the exact staged documentary candidate; remote publication and terminal receipt remain Director-owned pending actions.','No repeated product or full-package audit.','Initial identity query invoked git write-tree and returned the already-existing declared tree; no ref/index/worktree change observed. All subsequent Git operations were reads.','No source/canonical writes, product execution, Library mutation or active subprocess remains.']}
dump('AUDIT.json',result)
(ROOT/'REPORT.md').write_text('# Independent core delivery record review\n\nVerdict: '+result['verdict']+'. '+str(result['passed'])+' groups passed; '+str(result['failed'])+' failed.\n\nReviewed exact staged tree `'+TREE+'` from parent `'+PARENT+'`: 45 documentary paths. Every staged payload was read, bound to Git and checked against working bytes. Independent review copies match their original evidence exactly.\n\nAll three saved final files match retained upload IDs, version 0, local and readback hashes; matching prompts equal frozen ZIP members. The unchanged final ZIP remains 88,651,427 bytes, SHA-256 96dd48ac7cfe01219f57a48a3adfaacb1faa21325f72c5ad06ca19fcd54760cd. Original P14 records and production/adapter bytes are unchanged.\n\nCURRENT preserves every prior handoff/recovery object; task historical arrays and prior checks remain intact. Requirements/plan text is append-only, acceptance wording is unchanged and evidence additions are additive. Parent remains blocked, R03–R05 not_done, P02 in_progress, PR274 draft/open/unmerged, issue273 open, main unchanged and no main lease/integration.\n\nSource publication is reconciled without replay. Previous 96 + 175 runtime methods are distinguished from recovery audit groups; N57 and unrun operational/full-routine gates remain explicit. Terminal receipt, future confirmation and post-snapshot check records are honestly pending. The four passed documentary commands bind this exact candidate tree and their retained logs.\n\nNext: Director conditionally publishes this reviewed documentary tree, reads back actual state, then completes the separately saved terminal receipt/confirmation and stops. No second technical phase.\n\nProcedure note: an initial identity query used git write-tree and returned the already-existing candidate tree; no ref/index/worktree change was observed. Subsequent operations read immutable Git data only. No canonical edit, product execution or Library mutation was performed by this reviewer.\n')
print(json.dumps({'verdict':result['verdict'],'tree':TREE,'passed':result['passed'],'failed':result['failed'],'findings':result['mandatory_findings'],'report':str(ROOT/'REPORT.md')}))
