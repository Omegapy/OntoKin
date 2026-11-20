#!/usr/bin/env python3
"""Review the exact prepared delivery receipt tree against successful saves."""
import hashlib,io,json,os,platform,subprocess,sys,zipfile
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path('/workspace/scratch/a2bb67238030');R=ROOT/'OntoKin';OUT=ROOT/'audit/review'
BASE='0f90048b74b4cb69f2d5f058106c81967b13ae6d';B='docs/engineering/localized-repair-c270/correction/finalization-20261120/'
checks=[];commands=[];sources={}
def ident(b):return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def chk(n,v,**d):checks.append({'name':n,'passed':bool(v),**d})
def git(*args):
 cmd=['git','-C',str(R),*args];p=subprocess.run(cmd,capture_output=True,env=dict(os.environ,GIT_OPTIONAL_LOCKS='0'));commands.append({'argv':cmd,'exit_code':p.returncode,'stdout_identity':ident(p.stdout)});p.check_returncode();return p.stdout
def local(p):
 b=Path(p).read_bytes();sources[str(p)]=ident(b);return json.loads(b)
intent=local(ROOT/'operations/delivery-receipt-intent.json');TREE=intent['proposed_tree']
def raw(p,rev=TREE):
 b=git('show',rev+':'+p);sources[rev+':'+p]=ident(b);return b
def data(p,rev=TREE):return json.loads(raw(p,rev))
def entries(ref):
 d={}
 for line in git('ls-tree','-rz','--full-tree',ref).split(b'\0'):
  if line:
   a,p=line.split(b'\t',1);mode,typ,sha=a.decode().split();d[p.decode()]={'mode':mode,'type':typ,'blob':sha}
 return d
old,new=entries(BASE),entries(TREE);changed=sorted(p for p in old.keys()&new.keys() if old[p]!=new[p]);added=sorted(new.keys()-old.keys())
chk('only_three_existing_delivery_state_files_changed',changed==['STATUS.md','docs/workflow/CURRENT.json','docs/workflow/tasks/C270/task.json'])
chk('fifteen_scoped_record_additions',len(added)==15 and all(p.startswith(B) for p in added),paths=added)
chk('all_other_prior_bytes_modes_preserved',not old.keys()-new.keys() and all(old[p]==new[p] for p in old if p not in changed))
chk('prepared_nonforce_expected_parent',intent['branch']=='main' and intent['expected_head']==intent['parent']==BASE and intent['additional_parents']==[] and intent['force'] is False)
chk('exact_eighteen_intended_paths',len(intent['entries'])==len(intent['bindings'])==18 and {x['path'] for x in intent['entries']}=={x['path'] for x in intent['bindings']}==set(changed+added))
for row in intent['bindings']:
 p=row['path'];b=raw(p);entry=new[p]
 chk('intent_tree_worktree_binding:'+p,ident(b)=={'bytes':row['bytes'],'sha256':row['sha256']} and entry['blob']==row['blob'] and entry['mode']==row['mode'] and b==(R/p).read_bytes())
for row in intent['entries']:
 chk('intent_content:'+row['path'],row['content'].encode()==raw(row['path']))
saved=local(ROOT/'operations/final-save-result.json');metadata=local(ROOT/'operations/final-save-metadata.json')
delivery=data(B+'DELIVERY.json');receipts=data(B+'SAVE-RECEIPTS.json');artifacts=local(ROOT/'deliverables/OntoKin_C270_Correction_Finalization_Handoff_2026-11-20_ARTIFACTS.json')
chk('three_successful_saves',saved['exit_code']==0 and len(saved['response']['results'])==3 and all(x['status']=='succeeded' for x in saved['response']['results']))
chk('canonical_save_receipts_exact',receipts['ordered_result']==saved['response']['results'] and receipts['metadata_readback']==metadata and receipts['saved_at_utc']==saved['finished_at_utc'])
chk('delivery_source_and_phase_identities',delivery['source_revision']==BASE and delivery['source_tree']=='12dbb596ec9c4695dcd5d9badab83cdabae24a72' and delivery['implementation_commit']=='a6099546e2ae66e78621008338ecd3b2d352d9b8' and delivery['reviewed_candidate']=='29e98cab1774629171152be3be68c14e39bb9c0e' and delivery['merge_commit']=='4d27756f1c503b430dd85219235778a1f78ef101' and delivery['branch_disposition']=='deleted')
rows=[delivery['archive'],*delivery['prompts']];observed={x['file_name']:x for x in saved['response']['results']};meta={x['library_file_id']:x for x in metadata['items']};artifact={x['filename']:x for x in artifacts['files']}
for row in rows:
 name=row['file_name'];obs=observed[name];m=meta[row['library_file_id']];path=Path(obs['local_path']);b=path.read_bytes();sources[str(path)]=ident(b)
 chk('saved_identity:'+name,row['library_file_id']==obs['library_file_id']==m['library_file_id'] and row['file_id']==obs['file_id']==m['file_id'])
 chk('saved_path_name_version:'+name,row['path']==obs['path']==m['path'] and row['version']==obs['current_version_number']==int(m['version_id'])==0 and name==m['name'])
 chk('saved_size_local_digest:'+name,ident(b)=={'bytes':row['bytes'],'sha256':row['sha256']}=={'bytes':artifact[name]['bytes'],'sha256':artifact[name]['sha256']} and m['size_bytes']==row['bytes'])
 chk('saved_link_and_status:'+name,row['url']=='https://chatgpt.com/library?file_id='+row['library_file_id']+'&account_id=personal' and row['status']=='saved' and row['metadata_readback']=='passed')
zip_path=Path(observed[delivery['archive']['file_name']]['local_path']);zipbytes=zip_path.read_bytes()
pkg=local(ROOT/'audit/recovery/FINAL-PACKAGE-REVIEW.json');verify=local(ROOT/'deliverables/OntoKin_C270_Correction_Finalization_Handoff_2026-11-20_VERIFICATION.json')
chk('previous_independent_package_approval_bound',pkg['passed'] is True and pkg['check_count']==76 and not pkg['mandatory_findings'] and ident(zipbytes)=={'bytes':pkg['archive']['bytes'],'sha256':pkg['archive']['sha256']} and pkg['source_main']==BASE)
chk('builder_verification_bound',verify['result']=='passed' and ident(zipbytes)=={'bytes':verify['archive']['bytes'],'sha256':verify['archive']['sha256']} and verify['source_main']==BASE and verify['source_tree']==delivery['source_tree'])
chk('immutable_frozen_zip_identity',ident(zipbytes)=={'bytes':10963559,'sha256':'4852a588a96bc9839234c9491b61497859011efc553a26518eadae655dd034cd'})
with zipfile.ZipFile(io.BytesIO(zipbytes)) as z:
 checkpoint=json.loads(z.read('CHECKPOINT.json'));frozen_task=json.loads(z.read('repository/docs/workflow/tasks/C270/task.json'))
 chk('freeze_remains_pending_receipt',checkpoint['parent_status']=='in_progress' and checkpoint['requirements_at_freeze']=={'R01':'done','R02':'done','R03':'done','R04':'done','R05':'not_done'} and checkpoint['observed_main']['sha']==BASE and frozen_task['delivery']['status']=='pending')
 chk('future_external_receipt_not_inside_frozen_zip','repository/'+B+'DELIVERY.json' not in z.namelist() and 'repository/'+B+'CLOSEOUT.json' not in z.namelist())
 for row in delivery['prompts']:
  chk('matching_saved_prompt:'+row['matches_member'],z.read(row['matches_member'])==Path(observed[row['file_name']]['local_path']).read_bytes())
chk('receipt_external_boundary_truthful',delivery['status']=='saved' and delivery['closure']['status']=='pending_at_this_receipt' and 'Subsequent receipt/closure-only commits are external' in delivery['freeze_boundary'])
t=data('docs/workflow/tasks/C270/task.json');oldtask=data('docs/workflow/tasks/C270/task.json',BASE);cur=data('docs/workflow/CURRENT.json');oldcur=data('docs/workflow/CURRENT.json',BASE);status=raw('STATUS.md').decode()
chk('parent_and_issue_remain_open',t['status']=='in_progress' and t['completion']['scope_issue_state']=='open' and t['requirements'][-1]['status']=='not_done')
chk('acceptance_and_completed_gates_unchanged',all(a['id']==b['id'] and a['acceptance']==b['acceptance'] and a['status']==b['status'] for a,b in zip(t['requirements'],oldtask['requirements'])))
chk('task_saved_delivery_matches_receipt',t['delivery']['status']=='saved' and t['delivery']['library_file_id']==delivery['archive']['library_file_id'] and t['delivery']['sha256']==delivery['archive']['sha256'] and t['delivery']['bytes']==delivery['archive']['bytes'] and t['delivery']['version']==0 and t['delivery']['source_revision']==BASE and t['session_phase']['delivery_confirmed'] is True)
chk('closure_only_next_action',t['next_action']==cur['next_action']['summary'] and t['next_action'].startswith('R05 closure only:') and 'No next milestone' in t['next_action'] and 'await user direction' in cur['next_action']['suggested_task'])
chk('CURRENT_latest_saved_identity',cur['latest_handoff']['library_file_id']==delivery['archive']['library_file_id'] and cur['latest_handoff']['sha256']==delivery['archive']['sha256'] and cur['latest_handoff']['bytes']==delivery['archive']['bytes'] and cur['latest_handoff']['source_revision']==BASE)
chk('prior_handoff_and_C262_preserved',cur['previous_handoff']==oldcur['latest_handoff'] and oldcur['previous_handoff'] in cur['older_handoffs'] and cur['historical_handoff']==oldcur['historical_handoff'])
chk('STATUS_truthful_open_closure',('integrated, verified and saved; final closure remains pending' in status and 'historical ancillary broad-driver completion remains **unknown**' in status and 'Only [scope270]' in status))
copy_sources={'FINAL-DELIVERY-ARTIFACTS.json':ROOT/'deliverables/OntoKin_C270_Correction_Finalization_Handoff_2026-11-20_ARTIFACTS.json','FINAL-PACKAGE-VERIFICATION.json':ROOT/'deliverables/OntoKin_C270_Correction_Finalization_Handoff_2026-11-20_VERIFICATION.json','FINAL-PACKAGE-REVIEW.json':ROOT/'audit/recovery/FINAL-PACKAGE-REVIEW.json','FINAL-PACKAGE-REVIEW.md':ROOT/'audit/recovery/FINAL-PACKAGE-REVIEW.md','FINAL-PACKAGE-ARTIFACTS.json':ROOT/'audit/recovery/FINAL-PACKAGE-ARTIFACTS.json','audit_final_package.py':ROOT/'audit/recovery/audit_final_package.py','FINAL-STATE-REVIEW.json':OUT/'FINAL-STATE-REVIEW.json','FINAL-STATE-REVIEW.md':OUT/'FINAL-STATE-REVIEW.md','FINAL-STATE-ARTIFACTS.json':OUT/'FINAL-STATE-ARTIFACTS.json','audit_final_state.py':OUT/'audit_final_state.py'}
for target,p in copy_sources.items():chk('receipt_evidence_copy:'+target,raw(B+target)==p.read_bytes())
for n in ['CHECKS.json','documentation.log','workflow.log']:
 chk('published_source_records_copy:'+n,raw(B+'published-source-record-checks/'+n)==(ROOT/'evidence/published-integration-records'/n).read_bytes())
failed=[c for c in checks if not c['passed']]
report={'schema':'ontokin.c270.delivery-record-review/1','reviewer':'/root/candidate_review','reviewed_at_utc':datetime.now(timezone.utc).isoformat(),'baseline':BASE,'proposed_tree':TREE,'verdict':'approved_for_conditional_receipt_publication' if not failed else 'blocked','passed':not failed,'mandatory_findings':failed,'check_count':len(checks),'checks':checks,'commands':commands,'sources':sources,'audit_command':[sys.executable,*sys.argv],'script_identity':ident(Path(__file__).read_bytes()),'environment':{'python':sys.version,'platform':platform.platform()},'saved_files':rows,'boundary':'Prepared exact receipt tree; no publication or task/issue closure is claimed. After expected-main publication and fresh checks, only truthful closure/lease release remain.','limits':['No behavioral rerun or duplicate full package verification.','Save success and destination identities/sizes/versions are checked from preserved service responses; SHA-256 binds local uploaded bytes and independent frozen-package evidence, not a returned remote checksum.','Frozen ZIP stays at0f90048; later receipt/closure-only records remain external.']}
(OUT/'DELIVERY-RECORD-REVIEW.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'tree':TREE,'checks':len(checks),'passed':not failed,'failed':failed}))
raise SystemExit(1 if failed else 0)
