#!/usr/bin/env python3
"""Bounded audit of published integration metadata and evidence containers."""
import hashlib,io,json,os,platform,subprocess,sys,zipfile
from datetime import datetime,timezone
from pathlib import Path,PurePosixPath
ROOT=Path('/workspace/scratch/a2bb67238030');R=ROOT/'OntoKin';OUT=ROOT/'audit/review'
OLD='4d27756f1c503b430dd85219235778a1f78ef101';NEW='0f90048b74b4cb69f2d5f058106c81967b13ae6d';TREE='12dbb596ec9c4695dcd5d9badab83cdabae24a72'
B='docs/engineering/localized-repair-c270/correction/finalization-20261120/'
checks=[];commands=[];sources={}
def ident(b):return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def chk(n,v,**d):checks.append({'name':n,'passed':bool(v),**d})
def git(*args):
 cmd=['git','-C',str(R),*args];p=subprocess.run(cmd,capture_output=True,env=dict(os.environ,GIT_OPTIONAL_LOCKS='0'));commands.append({'argv':cmd,'exit_code':p.returncode,'stdout_identity':ident(p.stdout)});p.check_returncode();return p.stdout
def raw(path,rev=NEW):
 b=git('show',rev+':'+path);sources[rev+':'+path]=ident(b);return b
def data(path,rev=NEW):return json.loads(raw(path,rev))
def local(path):
 b=Path(path).read_bytes();sources[str(path)]=ident(b);return json.loads(b)
def entries(ref):
 d={}
 for line in git('ls-tree','-rz','--full-tree',ref).split(b'\0'):
  if line:
   a,p=line.split(b'\t',1);mode,typ,sha=a.decode().split();d[p.decode()]={'mode':mode,'type':typ,'blob':sha}
 return d
old,new=entries(OLD),entries(NEW);modified=sorted(p for p in old.keys()&new.keys() if old[p]!=new[p]);added=sorted(new.keys()-old.keys())
chk('source_tree_and_single_parent',git('rev-parse',NEW+'^{tree}').decode().strip()==TREE and git('show','-s','--format=%P',NEW).decode().split()==[OLD])
chk('only_three_state_files_modified',modified==['STATUS.md','docs/workflow/CURRENT.json','docs/workflow/tasks/C270/task.json'],paths=modified)
chk('twenty_one_evidence_additions_only',len(added)==21 and all(p.startswith(B) for p in added),paths=added)
chk('all_previous_other_bytes_modes_retained',not old.keys()-new.keys() and all(old[p]==new[p] for p in old if p not in modified))
t=data('docs/workflow/tasks/C270/task.json');p=data('docs/workflow/tasks/C270/task.json',OLD);states={r['id']:r['status'] for r in t['requirements']}
expected={'R01':'done','R02':'done','R03':'done','R04':'done','R05':'not_done'}
chk('exact_requirement_gate_state',states==expected,states=states)
chk('requirement_acceptance_preserved',all({k:v for k,v in a.items() if k not in ['status','evidence']}=={k:v for k,v in b.items() if k not in ['status','evidence']} for a,b in zip(t['requirements'],p['requirements'])))
chk('parent_issue_delivery_pending',t['status']=='in_progress' and t['completion']['scope_issue_state']=='open' and t['delivery']['status']=='pending' and t['delivery']['receipt'] is None and t['session_phase']['delivery_confirmed'] is False)
chk('completion_identities_correct',t['completion']['implementation_commit']=='a6099546e2ae66e78621008338ecd3b2d352d9b8' and t['completion']['merge_commit']==OLD and t['completion']['pull_request']=='https://github.com/Omegapy/OntoKin/pull/272' and t['completion']['branch_disposition']=='deleted')
chk('session_stops_at_R05',t['session_phase']['remaining_gate']=='R05' and t['session_phase']['integration_complete'] is True and t['session_phase']['actual_main_verified'] is True and t['next_action'].startswith('R05 only:') and 'No next milestone' in t['next_action'])
chk('unknown_routine_status_retained',t['checks'][4]==p['checks'][4] and t['checks'][5]==p['checks'][5])
cur=data('docs/workflow/CURRENT.json');oldcur=data('docs/workflow/CURRENT.json',OLD)
chk('CURRENT_R05_only',cur['active_task']==cur['latest_task']=='C270' and cur['next_action']['summary']==t['next_action'] and 'R05 only' in cur['next_action']['suggested_task'])
chk('historical_archive_boundaries_retained',all(cur.get(k)==v for k,v in oldcur.items() if k not in ['observed_main','snapshot_date','next_action']))
status=raw('STATUS.md').decode()
chk('STATUS_does_not_prematurely_close',('R05 delivery remains pending' in status and 'R01-R04 are done' in status and 'unknown' in status and 'No successful SiteRef support' in status))
chk('lease_renewal_bounded_to_remaining_scope','2026-11-20T21:48:57Z' in status and '2026-11-20T21:18:57Z' in status and 'only remaining C270 R05 delivery/closure is authorized' in status)
integration=data(B+'INTEGRATION.json');mainchecks=data(B+'ACTUAL-MAIN-CHECKS.json');branch=data(B+'BRANCH-DISPOSITION.json')
chk('canonical_integration_matches_review',integration['implementation_commit']==t['completion']['implementation_commit'] and integration['merge_commit']==OLD and integration['reviewed_candidate']=='29e98cab1774629171152be3be68c14e39bb9c0e' and integration['merge_tree']=='3ec9ba3caa18f560a751044d1d5bbd2f036383a2' and integration['gate_state']==expected and integration['force'] is False)
chk('branch_record_matches_observation',branch==integration['branch'] and branch['disposition']=='deleted' and branch['automatic_deletion_observed'] is True and branch['manual_deletion_attempted'] is False and branch['observed_main']==OLD and branch['retained_history']['candidate_is_ancestor'] is True and branch['known_pending_branch_writes']==[])
for n in ['FINAL-REVIEW.md','FINAL-DELTA-EVIDENCE.json','FINAL-ARTIFACTS.json','ACTUAL-MAIN-REVIEW.md','ACTUAL-MAIN-REVIEW.json','ACTUAL-MAIN-ARTIFACTS.json','audit_actual_main.py','audit_final_delta.py','AUDIT-ATTEMPTS.json']:
 chk('published_reviewer_bytes:'+n,raw(B+n)==(OUT/n).read_bytes())
chk('published_setup_failures_retained',raw(B+'LOCAL-SETUP-ATTEMPTS.json')==(ROOT/'evidence/LOCAL-SETUP-ATTEMPTS.json').read_bytes())
manifest=data(B+'ACTUAL-MAIN-MANIFEST.json');zipbytes=raw(B+'ACTUAL-MAIN-EVIDENCE.zip');archive=mainchecks['archive']
chk('actual_main_archive_exact_identity',ident(zipbytes)=={'bytes':1918886,'sha256':'eee464faaa95b1d992c759262890e92332f145be1dbb5cd315b9c5d71b93a9df'} and archive==manifest['archive'])
chk('main_evidence_attribution_preserved',mainchecks['source_revision']==manifest['source_revision']==OLD and mainchecks['source_tree']==manifest['source_tree']=='3ec9ba3caa18f560a751044d1d5bbd2f036383a2')
with zipfile.ZipFile(io.BytesIO(zipbytes)) as z:
 names=z.namelist();rows={r['path']:r for r in manifest['payloads']}
 chk('archive_exact39_payloads_crc_safe',len(names)==len(set(names))==len(rows)==39 and set(names)==set(rows) and z.testzip() is None and all(not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts and '\\' not in n for n in names))
 for name in names:
  b=z.read(name);row=rows[name]
  chk('archive_payload_hash:'+name,ident(b)=={'bytes':row['bytes'],'sha256':row['sha256']})
  original=(ROOT/'evidence'/('actual-main-'+Path(name).name.replace('.log','')+'-driver.log')) if name.startswith('driver-logs/') else ROOT/'evidence/actual-main'/name
  chk('archive_original_bytes:'+name,b==original.read_bytes())
 for row in mainchecks['reports']:
  chk('canonical_report_binding:'+row['archive_entry'],ident(z.read(row['archive_entry']))=={'bytes':row['bytes'],'sha256':row['sha256']})
chk('canonical_counts_match_review',mainchecks['result']=='passed' and mainchecks['frozen_h16']['assertions']==45 and mainchecks['frozen_h16']['cases']==5 and mainchecks['affected_cohort']['methods']==282 and mainchecks['affected_cohort']['groups']==12 and mainchecks['affected_cohort']['corpus_bindings']==14 and mainchecks['distinctions']['methods']==8 and mainchecks['distinctions']['variants']==16 and mainchecks['distinctions']['interface_calls']==48 and mainchecks['review']['checks']==297)
intent=local(ROOT/'operations/integration-record-intent.json');result=local(ROOT/'operations/integration-record-result.json')
chk('publication_intent_correct_expected_nonforce',intent['branch']=='main' and intent['expected_head']==intent['parent']==OLD and intent['force'] is False and intent['additional_parents']==[] and intent['proposed_tree']==TREE)
chk('exact24_publication_entries',len(intent['entries'])==len(intent['bindings'])==24 and {x['path'] for x in intent['entries']}=={x['path'] for x in intent['bindings']}==set(modified+added))
for row in intent['bindings']:
 b=raw(row['path']);actual=new[row['path']]
 chk('publication_binding:'+row['path'],ident(b)=={'bytes':row['bytes'],'sha256':row['sha256']} and actual['blob']==row['blob'] and actual['mode']==row['mode'])
for row in intent['entries']:
 b=raw(row['path'])
 chk('publication_content:'+row['path'],row['content'].encode()==b if 'content' in row else row['binary_blob']==new[row['path']]['blob'] and row['binary_bytes']==len(b))
readback=json.loads(result['readback']['structuredContent']['content'])
chk('publication_success_exact_main_readback',result['tree']['structuredContent']['sha']==TREE and result['commit']['structuredContent']['sha']==NEW and result['update']['structuredContent']['success'] is True and readback['ref']=='refs/heads/main' and readback['object']['sha']==NEW)
rcdir=ROOT/'evidence/published-integration-records';rc=local(rcdir/'CHECKS.json')
chk('fresh0f_record_checks_exact_clean',rc['source_revision']==NEW and rc['source_tree']==TREE and rc['source_clean'] is True and rc['result']=='passed' and {c['name'] for c in rc['checks']}=={'workflow','documentation'})
for c in rc['checks']:
 b=(rcdir/c['log']['path']).read_bytes();sources[str(rcdir/c['log']['path'])]=ident(b)
 chk('fresh_record_log_identity:'+c['name'],ident(b)=={'bytes':c['log']['bytes'],'sha256':c['log']['sha256']} and c['result']=='passed' and c['exit_code']==0)
 chk('fresh_record_log_outcome:'+c['name'],b'Workflow structure passed (11 tasks).' in b if c['name']=='workflow' else json.loads(b)['status']=='passed' and json.loads(b)['failures']==[])
chk('same_record_check_environment',rc['environment']=={'python':sys.version,'platform':platform.platform()})
chk('fresh_runner_preserved',ident(raw(Path(rc['runner']['path']).relative_to(R).as_posix()))=={'bytes':rc['runner']['bytes'],'sha256':rc['runner']['sha256']})
failed=[c for c in checks if not c['passed']]
report={'schema':'ontokin.c270.final-state-review/1','reviewer':'/root/candidate_review','reviewed_at_utc':datetime.now(timezone.utc).isoformat(),'source_revision':NEW,'source_tree':TREE,'parent':OLD,'verdict':'accepted_R01_R04_done_R05_pending' if not failed else 'blocked','passed':not failed,'mandatory_findings':failed,'check_count':len(checks),'checks':checks,'commands':commands,'sources':sources,'audit_command':[sys.executable,*sys.argv],'script_identity':ident(Path(__file__).read_bytes()),'environment':{'python':sys.version,'platform':platform.platform()},'gate_state':states,'next_action':'R05 only: verify/save final package and matching prompts; confirm separate receipt; close task/issue and release ownership; stop','record_checks':rc,'limits':['Metadata/evidence-container binding only; no behavioral rerun.','Actual behavior remains attributed to4d277 and original candidate evidence, not this later record-only commit.','This review does not certify final handoff integrity/save or preapprove an unidentified receipt/closure commit.']}
(OUT/'FINAL-STATE-REVIEW.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'source':NEW,'checks':len(checks),'passed':not failed,'failed':failed}))
raise SystemExit(1 if failed else 0)
