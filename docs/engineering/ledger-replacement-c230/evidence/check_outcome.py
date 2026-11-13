"""Read-only C230 outcome verifier; never import or execute product code."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

parser=argparse.ArgumentParser()
parser.add_argument('--workspace',type=Path,default=Path('/workspace/scratch/ad17c735596b'))
parser.add_argument('--output',type=Path)
a=parser.parse_args();b=a.workspace.resolve();out=a.output or b/'diagnosis-review/OUTCOME-REVIEW.json'
run=b/'diagnosis-run';review=b/'diagnosis-review';prep=b/'diagnosis-author/repo/docs/engineering/ledger-replacement-c230/prepared';session=b/'handoff-c230/evidence/c230/session'
load=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
digest=lambda data:hashlib.sha256(data).hexdigest()
checks=[]
def check(name,value,detail=None):
 row={'name':name,'passed':bool(value)}
 if detail is not None:row['detail']=detail
 checks.append(row)
def eq(name,a,b):check(name,a==b)
plan=load(prep/'RUN-PLAN.json');approval=load(review/'APPROVAL.json');r=load(run/'RESULT.json');original=load(run/'original-method/result.json');obs=load(run/'observed-cases/result.json')
inv=load(session/'root-launch-invocation.json');completion=load(session/'root-launch-completion.json');prelaunch=load(session/'root-prelaunch.json')
saved=load(b/'recovery/preexecution-save-result.json')['results'][0];built=load(b/'recovery/preexecution-evidence-build.json')
eq('exact_plan',sha(prep/'RUN-PLAN.json'),r['plan_sha256']);eq('exact_approval',sha(review/'APPROVAL.json'),r['approval_sha256'])
eq('approval_plan_binding',approval['plan_sha256'],r['plan_sha256'])
for name,h in plan['harness_sha256'].items():eq('exact_script_'+name,sha(prep/name),h)
eq('outer_invocation_command',inv['command'],plan['outer_invocation']);eq('outer_working_directory',inv['workingDirectory'],plan['outer_working_directory']);eq('outer_result_cwd',r['caller_working_directory'],inv['workingDirectory'])
eq('invocation_plan',inv['planSha256'],r['plan_sha256']);eq('invocation_approval',inv['approvalSha256'],r['approval_sha256'])
check('one_invocation',inv['invocationOrdinal']==inv['maximumInvocations']==completion['launcherInvocations']==1)
check('new_output',inv['outputExistedBeforeInvocation'] is False and prelaunch['outputDoesNotExist'] is True)
check('outer_exit_zero',completion['toolExitCode']==0);check('product_execution_closed',completion['productExecutionClosed'] is True and completion['noRetryAuthorized'] is True)
eq('preexecution_successful_save',saved['status'],'succeeded');eq('preexecution_version',saved['current_version_number'],2)
eq('preexecution_exact_saved_file',saved['file_id'],'file_00000000b6ac81f4ad5cbfe139621e75');eq('saved_receipt_bound_in_invocation',inv['confirmedRecoveryEvidence'],saved)
eq('preexecution_archive_digest',inv['recoveryArchiveSha256'],built['sha256']);eq('known_preexecution_digest',built['sha256'],'3ae9f1baca68dde06332c2e509b55a8c5414f0affa53443c8349aabcf9902cf8');check('archive_build_verified',built['verified'] is True)
check('run_completed',r['completed'] is True and r['schedule_consumed'] is True);eq('exact_worker_count',r['worker_start_count'],2);eq('worker_order',[x['mode'] for x in r['worker_starts']],['original-method','observed-cases'])
eq('source_before_after',r['source_before'],r['source_after']);check('source_unchanged_flag',r['source_unchanged'] is True)
for stage in ['source_before','source_after']:
 eq(stage+'_commit',r[stage]['commit'],plan['source_commit']);eq(stage+'_tree',r[stage]['tree'],plan['source_tree']);eq(stage+'_clean',r[stage]['status'],'');eq(stage+'_hashes',r[stage]['source_hashes'],plan['source_sha256'])
source=b/'OntoKin';env=dict(os.environ,GIT_OPTIONAL_LOCKS='0')
def git(*args):
 p=subprocess.run(['git','--no-optional-locks','-C',str(source),*args],capture_output=True,text=True,env=env,timeout=20)
 if p.returncode:raise RuntimeError(p.stderr)
 return p.stdout
head,tree=git('rev-parse','HEAD','HEAD^{tree}').splitlines();eq('current_source_commit',head,plan['source_commit']);eq('current_source_tree',tree,plan['source_tree']);eq('current_source_clean',git('status','--porcelain','--untracked-files=all'),'')
for name,h in plan['source_sha256'].items():eq('current_source_hash_'+name,sha(source/name),h)
for i,w in enumerate(r['worker_starts']):
 mode=w['mode'];e=load(run/mode/'environment.json')
 check(mode+'_attempt_consumed',w['attempt_consumed'] is True and w['popen_succeeded'] is True)
 check(mode+'_clean_exit',w['outcome']=='exited' and w['reaped'] is True and w['remaining_process_group']==[])
 eq(mode+'_exit_code',w['exit_code'],[1,0][i]);eq(mode+'_ceiling',w['timeout_seconds'],60)
 eq(mode+'_script',w['command'][2],r['resolved_paths']['worker']);check(mode+'_absolute_arguments',all(Path(w['command'][j]).is_absolute() for j in [0,2,5,7,9]))
 eq(mode+'_actual_cwd',e['cwd'],r['resolved_paths']['source']);eq(mode+'_process_receipt',(e['pid'],e['pgid']),(w['pid'],w['pgid']))
 check(mode+'_isolation',e['bytecode_writes_disabled'] is True and e['max_child_starts']==0)
 check(mode+'_environment',e['python'].startswith('3.12.14 ') and e['uname']['sysname']=='Linux' and e['machine']=='x86_64' and bool(e['mountinfo']))
 eq(mode+'_child_start_attempts',load(run/mode/'result.json')['child_start_attempts'],[])
eq('native_starts',r['native_starts'],0);eq('aggregate_attempts',r['aggregate_attempts'],0)
check('original_complete',original['completed'] is True and original['tests_run']==1)
eq('original_subtests',len(original['subtests']),10);eq('original_passing_subtests',sum(x['status']=='passed' for x in original['subtests']),8)
failed=[x for x in original['subtests'] if x['status']=='failed'];eq('original_failed_subtests',len(failed),2);eq('original_method_errors',original['errors'],[]);eq('original_skips',original['skipped'],[])
check('original_not_modified',original['source_method_modified'] is False and original['instrumented_file_operations'] is False and original['live_file_bytes_or_inodes_observed'] is False)
check('original_fixture_cleanup',original['temporary_fixture_cleanup_observed_empty'] is True and not any((run/'tmp/original-method').iterdir()))
names=['C201-Q01-A01-A04-v0.1.0.invocation.json','C201-Q01-A01-A04-v0.1.0.ledger.jsonl'];marker,journal=names
eq('failed_file_inventory',sorted(x['parameters']['name'] for x in failed),sorted(names))
check('only_expected_replace_failures',all(x['parameters']['mutation']=='replace' and 'LedgerError not raised' in x['traceback'] for x in failed))
raw=(run/'original-method.stderr.log').read_text();check('raw_unittest_reconciles',raw.count('AssertionError: LedgerError not raised')==2 and 'FAILED (failures=2)' in raw)
historical=b/'input/c229/evidence/c228/aggregate-review/outcome'
for name,h in plan['original_failure_evidence_sha256'].items():eq('historical_failure_hash_'+name,sha(historical/name),h)
h=load(historical/'LEDGER-FAILURES.json');eq('historical_method_match',h['failedMethod'],failed[0]['test']);check('historical_same_failures',all(any(x['parameters']['name'] in y['heading'] and 'LedgerError not raised' in y['text'] for y in h['completeFailureBlocks']) for x in failed))
caseids=['marker-no-held-fd','journal-no-held-fd','marker-held-fd-control','journal-held-fd-control'];eq('observed_case_order',[c['case'] for c in obs['cases']],caseids)
check('observed_complete',obs['completed'] is True and obs['case_count']==4);check('retained_descriptors_closed',obs['cleanup']['retained_descriptors_closed'] is True)
events=[json.loads(line) for line in (run/'observed-cases/observations.jsonl').read_text().splitlines()];eq('event_count',len(events),16)
records={x['path']:x for x in obs['retained_bytes']};eq('retained_binary_count',len(records),32)
for path,row in records.items():
 p=run/'observed-cases'/path;eq('retained_hash_'+path,sha(p),row['sha256']);eq('retained_size_'+path,p.stat().st_size,row['bytes'])
case_summary=[]
for idx,c in enumerate(obs['cases']):
 cid=c['case'];held=c['retained_descriptor_intervention'];before=c['before_path'];after=c['after_recreation_path'];identity=lambda s:[s['st_dev'],s['st_ino']]
 eq(cid+'_hold_mode',held,idx>=2);check(cid+'_unlink_absence',c['unlink_returned'] is True and c['after_unlink_path']=={'exists':False})
 check(cid+'_same_content',c['recreated_content_identical'] is True and c['original_content_sha256']==c['recreated_content_sha256'])
 eq(cid+'_stored_identity',identity(before),c['stored_identity']['marker' if c['name']==marker else 'journal'])
 eq(cid+'_reuse_flag',c['device_inode_reused'],identity(before)==identity(after));check(cid+'_single_link_before_after',before['st_nlink']==after['st_nlink']==1)
 eq(cid+'_rewrite_size',c['rewrite_returned_bytes'],c['original_content_bytes']);check(cid+'_observed_time_order',c['observation_started_ns']<c['observation_finished_ns'])
 ds=[x['fd'] for x in c['descriptors_before_unlink'] if [x.get('st_dev'),x.get('st_ino')]==identity(before)]
 eq(cid+'_descriptor_inventory_match',ds,c['matching_descriptors_before_unlink']);eq(cid+'_held_inventory',ds,[c['held_fd']] if held else [])
 if held:
  eq(cid+'_fd_identity_before',identity(c['held_fd_before_unlink']),identity(before))
  for stage in ['held_fd_after_unlink','held_fd_after_recreation','held_fd_before_close']:
   eq(cid+'_'+stage+'_identity',identity(c[stage]),identity(before));eq(cid+'_'+stage+'_zero_links',c[stage]['st_nlink'],0)
  check(cid+'_held_fd_closed',c['held_fd_closed'] is True)
 else:eq(cid+'_no_held_fd',c['held_fd_closed'],None)
 ev=events[idx*4:idx*4+4];eq(cid+'_event_order',[x['event'] for x in ev],['before-mutation','after-recreation','after-first-reserve','case-finally']);eq(cid+'_final_event',ev[-1]['payload'],c)
 stages=['original','recreated','after-first-reserve','after-poison-check'];binary={stage:{name:(run/'observed-cases/retained-bytes'/cid/stage/name).read_bytes() for name in names} for stage in stages}
 for e,stage in zip(ev[:3],stages[:3]):
  eq(cid+'_'+stage+'_event_case',e['payload']['observation']['case'],cid)
  for name in names:eq(cid+'_'+stage+'_event_bytes_'+name,bytes.fromhex(e['payload']['files_hex'][name]),binary[stage][name])
 for name in names:
  eq(cid+'_original_recreated_'+name,binary['original'][name],binary['recreated'][name]);eq(cid+'_poison_no_further_append_'+name,binary['after-first-reserve'][name],binary['after-poison-check'][name])
  eq(cid+'_retained_final_authority_'+name,(run/'tmp/observed-cases'/cid/'authority'/name).read_bytes(),binary['after-poison-check'][name])
 eq(cid+'_original_digest',digest(binary['original'][c['name']]),c['original_content_sha256'])
 check(cid+'_native_flags_false',all(c[s]['native_readiness'] is False and c[s]['admission_completed'] is False for s in ['before_snapshot','after_first_reserve_snapshot','after_poison_check_snapshot']))
 returned=c['first_reserve']['outcome']=='returned'
 if returned:
  check(cid+'_observed_mechanism',not held and c['device_inode_reused'] is True and c['after_first_reserve_snapshot']['stopped'] is False and c['after_first_reserve_snapshot']['persistence_or_interruption_uncertain'] is False)
  eq(cid+'_poison_not_run',c['poison_check']['outcome'],'not_run');eq(cid+'_receipt_invocation',c['first_reserve']['receipt']['invocation_id'],c['invocation_id']);eq(cid+'_no_native_authority',c['first_reserve']['receipt']['native_start_authorized'],False)
  check(cid+'_journal_extended',binary['after-first-reserve'][journal].startswith(binary['original'][journal]) and len(binary['after-first-reserve'][journal])>len(binary['original'][journal]))
  lines=[json.loads(x) for x in binary['after-first-reserve'][journal].splitlines()];eq(cid+'_journal_event_types',[x['event']['type'] for x in lines],['INVOKED','RESERVED'])
  for seq,line in enumerate(lines):
   body={k:v for k,v in line.items() if k!='sha256'};eq(cid+'_journal_hash_'+str(seq),line['sha256'],digest(json.dumps(body,sort_keys=True,separators=(',',':'),allow_nan=False,ensure_ascii=True).encode('ascii')))
  eq(cid+'_journal_previous_hash',lines[1]['previous_sha256'],lines[0]['sha256'])
 else:
  eq(cid+'_rejection_chain',[x['code'] for x in c['first_reserve']['exception_chain']],['PERSISTENCE','INTEGRITY']);eq(cid+'_poison_chain',[x['code'] for x in c['poison_check']['exception_chain']],['STOPPED'])
  check(cid+'_stopped_uncertain',c['after_first_reserve_snapshot']['stopped'] is True and c['after_first_reserve_snapshot']['persistence_or_interruption_uncertain'] is True and c['after_poison_check_snapshot']['stopped'] is True)
  for name in names:eq(cid+'_rejection_preserves_bytes_'+name,binary['original'][name],binary['after-first-reserve'][name])
 case_summary.append({'case':cid,'before_identity':identity(before),'recreated_identity':identity(after),'identity_reused':c['device_inode_reused'],'held_descriptor':held,'first_reserve':c['first_reserve']['outcome'],'stopped':c['after_first_reserve_snapshot']['stopped'],'poison_check':c['poison_check']['outcome'],'original_bytes':len(binary['original'][c['name']]),'after_first_journal_bytes':len(binary['after-first-reserve'][journal])})
copy=b/'handoff-c230/evidence/c230/diagnosis-run';files=[p for p in run.rglob('*') if p.is_file()]
check('handoff_run_copy_exact',all((copy/p.relative_to(run)).is_file() and sha(copy/p.relative_to(run))==sha(p) for p in files),{'files':len(files)})
result={'schema':'ontokin.c230.independent-outcome-review/0.1','decision':'ACCEPT_FINITE_DIAGNOSTIC_RESULT' if all(x['passed'] for x in checks) else 'BLOCK','passed':all(x['passed'] for x in checks),'assertions':len(checks),'passed_assertions':sum(x['passed'] for x in checks),'checks':checks,'case_summary':case_summary,'accounting':{'launcher_invocations':1,'worker_starts':2,'original_methods':1,'original_subtests_passed':8,'original_subtests_failed':2,'observed_cases':4,'ledger_begin_calls':14,'reservation_calls':25,'call_count_basis':'Static unchanged control flow plus complete outcomes: original 10 begins/18 reserves, observations 4 begins/7 reserves; no inserted call counters.','native_starts':0,'aggregates':0,'diagnostic_retries':0,'review_product_executions':0},'source_commit':plan['source_commit'],'source_tree':plan['source_tree'],'plan_sha256':r['plan_sha256'],'approval_sha256':r['approval_sha256'],'preexecution_save':{'library_file_id':saved['library_file_id'],'file_id':saved['file_id'],'version':2,'sha256':built['sha256'],'review_basis':'Immutable successful save/build/root-invocation receipts and exact preserved approved source bytes. The mutable current recovery ZIP may contain a later version.'},'mechanism':'The journal-no-held-fd case directly observed absent path, same-content recreation reusing (st_dev,st_ino)=(27,4080855), accepted reservation and stopped=false.','limits':['Original marker and journal failures reproduced but their allocation sequence was not instrumented.','Instrumented marker received a different inode and correctly rejected; it did not independently demonstrate marker inode reuse.','C228 historical allocation sequence remains unobserved.','Held-descriptor controls deliberately alter object lifetime.','R02 remains blocked and no product repair or aggregate ran.'],'input_bindings':{str(p.relative_to(b)):sha(p) for p in [run/'RESULT.json',run/'original-method/result.json',run/'original-method.stderr.log',run/'observed-cases/result.json',run/'observed-cases/observations.jsonl',session/'root-launch-invocation.json',session/'root-launch-completion.json',b/'recovery/preexecution-save-result.json',b/'recovery/preexecution-evidence-build.json']},'review_script_sha256':sha(Path(__file__))}
out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'decision':result['decision'],'passed':result['passed'],'assertions':result['assertions'],'failed':[x['name'] for x in checks if not x['passed']],'source_commit':result['source_commit'],'review_product_executions':0}))
raise SystemExit(0 if result['passed'] else 1)
