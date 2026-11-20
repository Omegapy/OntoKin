#!/usr/bin/env python3
"""Independent final C270 metadata/publication audit against exact Git objects."""
import hashlib, io, json, os, platform, subprocess, sys, zipfile
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
ROOT=Path('/workspace/scratch/a2bb67238030'); REPO=ROOT/'OntoKin'; OUT=ROOT/'audit/review'
OLD='2076b06f133fd548079052102e060bc29abc7493'; NEW='29e98cab1774629171152be3be68c14e39bb9c0e'
LEASE='f2d503423c5a790df79d28d61679d146a4c28c32'; TREE='3ec9ba3caa18f560a751044d1d5bbd2f036383a2'
BASE='docs/engineering/localized-repair-c270/correction/finalization-20261120/'
checks=[]; commands=[]; sources={}
def ident(b):return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def check(n,v,**d):checks.append({'name':n,'passed':bool(v),**d})
def g(*a):
 c=['git','-C',str(REPO),*a];p=subprocess.run(c,capture_output=True,env=dict(os.environ,GIT_OPTIONAL_LOCKS='0'));commands.append({'argv':c,'exit_code':p.returncode,'stdout_identity':ident(p.stdout)});p.check_returncode();return p.stdout
def raw(p,rev=NEW):
 b=g('show',rev+':'+p);sources[rev+':'+p]=ident(b);return b
def data(p,rev=NEW):return json.loads(raw(p,rev))
def local(p):
 b=Path(p).read_bytes();sources[str(p)]=ident(b);return json.loads(b)
def entries(rev):
 d={}
 for r in g('ls-tree','-rz','--full-tree',rev).split(b'\0'):
  if r:
   meta,p=r.split(b'\t',1);mode,typ,sha=meta.decode().split();d[p.decode()]={'mode':mode,'type':typ,'blob':sha}
 return d
before,after,lease=entries(OLD),entries(NEW),entries(LEASE)
changed=sorted(p for p in before.keys()&after.keys() if before[p]!=after[p]);added=sorted(after.keys()-before.keys())
check('candidate_exact_tree',g('rev-parse',NEW+'^{tree}').decode().strip()==TREE)
check('candidate_exact_parents',g('show','-s','--format=%P',NEW).decode().split()==[OLD,LEASE])
allowed=['STATUS.md','docs/workflow/CURRENT.json','docs/workflow/tasks/C270/PLAN.md','docs/workflow/tasks/C270/task.json']
check('only_four_existing_record_paths_modified',changed==sorted(allowed),paths=changed)
check('no_original_paths_deleted',not before.keys()-after.keys())
check('eighteen_scoped_additions',len(added)==18 and all(p.startswith((BASE,'docs/engineering/localized-repair-c270/correction/recovery-20261120/')) for p in added),paths=added)
check('all_implementation_fixture_test_command_inputs_stable',all(before[p]==after[p] for p in before if p not in allowed))
historical=[p for p in added if '/correction/recovery-20261120/' in p]
check('four_older_recovery_files_inherited_exactly',len(historical)==4 and all(lease.get(p)==after[p] for p in historical))
for p,n in [('INITIAL-REVIEW.md','REVIEW.md'),('INITIAL-EVIDENCE.json','EVIDENCE.json'),('audit_finalization.py','audit_finalization.py')]:
 check('review_payload_exact:'+p,raw(BASE+p)==(OUT/n).read_bytes())
task=data('docs/workflow/tasks/C270/task.json'); prior=data('docs/workflow/tasks/C270/task.json',OLD)
check('all_requirements_and_acceptance_unchanged',task['requirements']==prior['requirements'])
check('original_four_required_checks_preserved',task['checks'][:4]==prior['checks'][:4])
check('parent_open_and_R03_R05_not_prematurely_closed',task['status']=='in_progress' and task['completion']['scope_issue_state']=='open' and all(r['status']=='not_done' for r in task['requirements'] if r['id'] in ['R03','R04','R05']))
optional=task['checks'][4]; mandatory=task['checks'][5]
check('unknown_completion_explicit_and_optional',optional['required'] is False and optional['result']=='not_run' and optional['execution_status']=='interrupted_unknown' and optional['invocation_observed'] is True and optional['final_exit_code'] is None and 'No completed result is available' in optional['interpretation'] and 'No full-suite pass or failure is claimed' in optional['interpretation'])
check('mandatory_invocation_only_evidenced',mandatory['required'] is True and mandatory['result']=='passed' and 'Only invocation' in mandatory['interpretation'] and 'Broad completion remains unknown' in mandatory['interpretation'])
dis=data(BASE+'ROUTINE-DISPOSITION.json')
check('routine_disposition_matches_independent_review',dis['independent_disposition']['reviewer']=='/root/candidate_review' and dis['independent_disposition']['reviewed_candidate']==OLD and dis['execution_status']=='interrupted_unknown' and dis['final_exit_code'] is None and dis['completed_broad_result'] is None and dis['broad_pass_claimed'] is False)
zip_raw=raw(BASE+dis['preserved_archive']['path']);exp=dis['preserved_archive']
check('raw_archive_identity',ident(zip_raw)=={'bytes':exp['bytes'],'sha256':exp['sha256']})
with zipfile.ZipFile(io.BytesIO(zip_raw)) as z:
 names=z.namelist(); expected={r['path']:r for r in exp['files']}
 check('zip_crc',z.testzip() is None)
 check('exact_six_archive_members',len(names)==len(set(names))==6 and set(names)==set(expected))
 check('safe_zip_members',all(not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts and '\\' not in n for n in names))
 for n in names:
  b=z.read(n);r=expected[n]
  check('archived_identity:'+n,ident(b)=={'bytes':r['bytes'],'sha256':r['sha256']})
  check('archived_original_bytes:'+n,b==(ROOT/'recovered/latest/session-evidence/routine-interrupted'/n).read_bytes())
current=data('docs/workflow/CURRENT.json');old_current=data('docs/workflow/CURRENT.json',OLD)
check('C262_and_historical_handoffs_preserved',all(current.get(k)==v for k,v in old_current.items() if k not in ('observed_main','snapshot_date','next_action')))
check('latest_recovery_matches_confirmed_early_receipt',current['latest_recovery']['library_file_id']=='libfile_fde3_f-3afa93d934708191b8d10378d9afb0ed_2ab2a24d43748191957f9bcc356b59de' and current['latest_recovery']['sha256']=='7551b18d3af9f69ff3dc0726801bd5f4ffb3993a04c5ef481b149e1d22398b1c')
check('plan_preserves_previous_phase_text',raw('docs/workflow/tasks/C270/PLAN.md').startswith(raw('docs/workflow/tasks/C270/PLAN.md',OLD)))
ops=ROOT/'operations';intent=local(ops/'candidate-intent.json');pre=local(ops/'candidate-before-ref.json');result=local(ops/'candidate-result.json');tr=local(ops/'candidate-tree-result.json')
check('published_candidate_expected_head_nonforce',intent['expected_head']==OLD and intent['parent']==OLD and intent['additional_parents']==[LEASE] and intent['force'] is False and pre['force'] is False and pre['expected']==OLD and pre['commit']==NEW)
check('proposed_remote_actual_tree_equal',intent['proposed_tree']==tr['structuredContent']['sha']==TREE)
check('entry_inventory_exact_changed_payload',len(intent['entries'])==len(intent['bindings'])==22 and {r['path'] for r in intent['entries']}==set(changed+added)=={r['path'] for r in intent['bindings']})
for row in intent['bindings']:
 p=row['path'];b=raw(p);actual=after[p]
 check('published_binding:'+p,ident(b)=={'bytes':row['bytes'],'sha256':row['sha256']} and actual['blob']==row['blob'] and actual['mode']==row['mode'])
for row in intent['entries']:
 p=row['path'];b=raw(p)
 if 'content' in row:check('published_text_bytes:'+p,row['content'].encode()==b)
 else:check('published_binary_blob:'+p,row['binary_blob']==after[p]['blob'] and row['binary_bytes']==len(b))
readback=json.loads(result['readback']['structuredContent']['content'])
check('remote_success_and_exact_ref_readback',result['commit']['structuredContent']['sha']==NEW and result['update']['structuredContent']['success'] is True and readback['object']['sha']==NEW and readback['ref']=='refs/heads/work/c270-valid-siteref-control' and not any(result[k].get('isError') for k in ('commit','update','readback')))
records=ROOT/'evidence/final-candidate-records-02';rc=local(records/'CHECKS.json')
check('fresh_checks_exact_candidate_clean',rc['source_revision']==NEW and rc['source_tree']==TREE and rc['source_clean'] is True and rc['result']=='passed')
runner=rc['runner'];runner_path=Path(runner['path']).relative_to(REPO).as_posix()
check('record_runner_identity',ident(raw(runner_path))=={'bytes':runner['bytes'],'sha256':runner['sha256']})
check('fresh_check_environment',rc['environment']['python']==sys.version and rc['environment']['platform']==platform.platform())
for c in rc['checks']:
 log=(records/c['log']['path']).read_bytes();sources[str(records/c['log']['path'])]=ident(log)
 check('fresh_record_result:'+c['name'],c['result']=='passed' and c['exit_code']==0 and ident(log)=={'bytes':c['log']['bytes'],'sha256':c['log']['sha256']})
 if c['name']=='workflow':
  check('fresh_record_log:'+c['name'],b'workflow structure passed (11 tasks).' in log.lower() and b'error' not in log.lower())
 else:
  logdata=json.loads(log)
  check('fresh_record_log:'+c['name'],logdata.get('status')=='passed' and logdata.get('failures')==[])
check('both_applicable_fresh_checks',{c['name'] for c in rc['checks']}=={'workflow','documentation'})
attempts=local(ROOT/'evidence/LOCAL-SETUP-ATTEMPTS.json')
check('local_setup_attempts_truthfully_retained',attempts['remote_writes_replayed'] is False and len(attempts['attempts'])==3)
check('current_git_head_exact',g('rev-parse','HEAD').decode().strip()==NEW)
check('current_checkout_clean',g('status','--porcelain=v1')==b'')
check('no_unmerged_index',g('ls-files','-u')==b'')
failed=[c for c in checks if not c['passed']]
report={'schema':'ontokin.c270.final-metadata-review/1','reviewer':'/root/candidate_review','reviewed_at_utc':datetime.now(timezone.utc).isoformat(),'candidate':NEW,'tree':TREE,'parents':[OLD,LEASE],'environment':{'python':sys.version,'platform':platform.platform()},'command':[sys.executable,*sys.argv],'script_identity':ident(Path(__file__).read_bytes()),'checks':checks,'check_count':len(checks),'failed':failed,'passed':not failed,'verdict':'approved_for_conditional_integration' if not failed else 'blocked','mandatory_findings':failed,'changed_paths':changed,'added_paths':added,'sources':sources,'commands':commands,'record_checks':rc,'remaining_gates':['Observed-main conditional integration; exact resulting-main tree verification and fresh applicable checks','Observed branch disposition, final package verification/save, separate receipt and truthful closure'],'limits':['No behavioral rerun or full-suite pass claim.','Remote publication observations are the preserved connector results independently inspected against authentic local Git objects.','No future merge, receipt, closure or package is approved by this candidate review.']}
(OUT/'FINAL-DELTA-EVIDENCE.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'candidate':NEW,'checks':len(checks),'passed':not failed,'failed':failed}))
raise SystemExit(1 if failed else 0)
