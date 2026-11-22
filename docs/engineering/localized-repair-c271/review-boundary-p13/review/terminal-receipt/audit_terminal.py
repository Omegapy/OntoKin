#!/usr/bin/env python3
"""Independent P13 terminal data receipt audit; no product or remote operation."""
import base64
from collections import Counter
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import zipfile

BASE=Path('/workspace/scratch/82b6b514e749')
REPO=BASE/'repo'
OUT=BASE/'reviews/terminal-receipt/attempt001'
RECEIPT=BASE/'deliverables/terminal-attempt001/OntoKin_C271_P13_Delivery_Receipt_2026-11-21.json'
SOURCE='23476c3e6ee72962b40d868c48be5d7c34f06b47'
SOURCE_TREE='fe1987dc094d2efea5497b3a410f55c9be942e21'
TERMINAL='42442a42425b57b8f9d88d6c473de30166a2498e'
TREE='ac503b75ca2afc5c32118d9c9a70329e525987e9'
P13='docs/engineering/localized-repair-c271/review-boundary-p13/'
ARCHIVES={'final_handoff':BASE/'deliverables/final-attempt001/OntoKin_C271_P13_Review_Policy_Design_Handoff_2026-11-21.zip','p13_early_attempt002':BASE/'deliverables/early-attempt002/OntoKin_C271_P13_Review_Policy_Early_Recovery_2026-11-21_Attempt002.zip'}
def sha(b):return hashlib.sha256(b).hexdigest()
def identity(p):
 b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':sha(b)}
def unique(pairs):
 d={}
 for k,v in pairs:
  if k in d:raise ValueError('Duplicate JSON key: '+k)
  d[k]=v
 return d
def parse(b):return json.loads(b,object_pairs_hook=unique)
def read(p):return parse(p.read_bytes())
def exact(p,row):return p.is_file() and not p.is_symlink() and p.stat().st_size==row['bytes'] and sha(p.read_bytes())==row['sha256']
def safe(p):return isinstance(p,str) and bool(p) and not p.startswith('/') and '\\' not in p and '\x00' not in p and ':' not in p.split('/')[0] and all(s not in ('','.','..') for s in p.split('/'))
def git(*a):return subprocess.run(['git','--no-optional-locks',*a],cwd=REPO,capture_output=True,check=True).stdout
OUT.mkdir(parents=True,exist_ok=False)
started=datetime.now(timezone.utc).isoformat()
checks=[]
def check(name,ok,details=None):checks.append({'id':name,'passed':bool(ok),'details':details})
x=read(RECEIPT);r=x['post_freeze_recovery'];body=read(BASE/'delivery/TERMINAL-BASE.json');core=read(REPO/(P13+'P13-DELIVERY.json'))
check('exact_frozen_terminal_receipt',identity(RECEIPT)['bytes']==759600 and identity(RECEIPT)['sha256']=='6cdc3eb4d05f52e47a0e43cf85117c5981a34ec0b75dd9f4febdd8441aad8f2a' and stat.S_IMODE(RECEIPT.stat().st_mode)==0o444)
check('only_recovery_added_to_exact_director_base',{k:v for k,v in x.items() if k!='post_freeze_recovery'}==body and identity(BASE/'delivery/TERMINAL-BASE.json')['bytes']==21824 and sha((BASE/'delivery/TERMINAL-BASE.json').read_bytes())==r['cutoff']['body_sha256']=='fe5bf3be3c6935c8f90b8e6be160bccfbb3c9f87f93a5d7389f471a7c6d4a409')
check('core_object_and_exact_file_unchanged',x['core_delivery']==core and exact(Path(x['core_delivery_file']['path']),x['core_delivery_file']) and x['core_delivery_file']['sha256']=='2b0d3fd4e58fcfaa7d89e252165c7cdac5f090dde1d7d3b1dbd506075ae5db1c')
check('source_and_terminal_commit_parent_trees_exact',x['source_revision']==SOURCE and x['source_tree']==SOURCE_TREE and git('show','-s','--format=%H %T %P',TERMINAL).decode().strip()==TERMINAL+' '+TREE+' '+SOURCE and git('show','-s','--format=%H %T',SOURCE).decode().strip()==SOURCE+' '+SOURCE_TREE)
checkpoint=x['terminal_repository_checkpoint']
check('terminal_checkpoint_records_exact_git',checkpoint['commit']==TERMINAL and checkpoint['tree']==TREE and checkpoint['parent']==SOURCE and checkpoint['conditional_nonforce_update'] and checkpoint['exact_readback'] and checkpoint['checked_index_tree_equals_published_tree'] and checkpoint['working_tree_clean'])
git_rows=[]
for row in checkpoint['changed_files']:
 blob=git('show',TERMINAL+':'+row['path']);entry=git('ls-tree','-z',TERMINAL,'--',row['path']).rstrip(b'\x00').split(b'\t',1);mode,kind,obj=entry[0].decode().split()
 git_rows.append({**row,'passed':kind=='blob' and mode==row['mode'] and obj==row['git_blob'] and len(blob)==row['bytes'] and sha(blob)==row['sha256'] and exact(REPO/row['path'],row)})
check('all_12_published_changes_exact_blob_mode_bytes',len(git_rows)==12 and all(v['passed'] for v in git_rows) and set(v['path'] for v in git_rows)==set(git('diff-tree','--no-commit-id','--name-only','-r',TERMINAL).decode().splitlines()))
verification=x['verification']
bound=[verification['source_checks'][k] for k in ['check_report','publication_readback']]+[verification[k] for k in ['terminal_record_checks','terminal_publication_readback','saved_file_readback','folder_metadata']]
for k in ['independent_final_package_review','independent_core_record_review']:
 bound += [verification[k][s] for s in ['report','audit','reviewed_files']]
check('all_bound_checks_reviews_readbacks_exact',all(exact(Path(v['path']),v) for v in bound))
dc=read(Path(verification['terminal_record_checks']['path']));pub=read(Path(verification['terminal_publication_readback']['path']))
check('four_terminal_gates_same_published_tree',dc['source']['index_tree']==TREE and dc['source']['head']==SOURCE and len(dc['checks'])==4 and dc['passed'] and all(v['exit_code']==0 and v['result']=='passed' for v in dc['checks']) and pub['terminal_commit']==TERMINAL and pub['terminal_tree']==TREE and pub['parent_source_commit']==SOURCE and pub['all_12_file_bytes_equal_reviewed_checked_candidate'] and pub['checked_index_tree_equals_published_tree'])
dcdir=Path(verification['terminal_record_checks']['path']).parent
check('terminal_gate_stdout_stderr_exact',all(exact(dcdir/v[k]['path'],v[k]) for v in dc['checks'] for k in ['stdout','stderr']))
check('942_source_preservation_evidence_reused',dc['protected_sources']['count']==942 and dc['protected_sources']['passed'] and sha((dcdir/dc['protected_sources']['path']).read_bytes())==dc['protected_sources']['sha256']=='47321a9d482888d258e712ba3e825a171dce46c7dc254079b5953fd3d926c577' and pub['design_and_product_unchanged_from_handoff_source'] and all(dc[k] is False for k in ['product_imports','product_tests_run','H0_H1','full_routine','main_integration']))
saved=read(Path(verification['saved_file_readback']['path']))
check('saved_archive_and_prompts_core_binding_reused',core['archive']==saved['archive'] and core['matching_prompts']==saved['matching_prompts'] and saved['all_saved_and_exactly_readback_verified'] and all(exact(Path(v['local_path']),v) and exact(Path(v['readback_path']),v) for v in [saved['archive'],*saved['matching_prompts']]))
check('self_save_identity_explicitly_future',x['self_library_save']['status_at_freeze']=='not_yet_saved' and x['self_library_save']['library_identity_at_freeze'] is None and x['self_library_save']['file_name']==RECEIPT.name and x['completion_scope']['terminal_receipt_self_save_pending_at_freeze'] and 'future' in r['self_reference_boundary'])
scope=x['completion_scope'];state=x['observed_repository_state']
check('parent_open_no_execution_or_integration',scope['parent_complete'] is False and scope['parent_status']=='blocked' and all(scope['requirements'][k]=='not_done' for k in ['R03','R04','R05']) and all(scope[k] is False for k in ['runtime_tests_run','H0_H1','full_routine','main_integration','next_development_phase_started']) and scope['actual_source_completeness']=='not_established' and state['pr']=={'number':274,'state':'open','draft':True,'merged':False} and state['issue']=={'number':273,'state':'open'} and state['main_lease_held'] is False and state['integration_performed'] is False and state['branch_retained'])
check('unknown_read_only_operation_honest',x['operations']['unknown_writes']==[] and x['operations']['current_unknown_read_only_operations']==core['current_unknown_operations'] and x['operations']['historical_unknowns']==core['historical_unknowns'])
check('phase_stop_and_later_confirmation_scoped','supersede' in core['scope_of_later_confirmation'] and 'only this receipt self-save and phase delivery' in x['source_time_pending_resolution'] and x['stop'].endswith('Do not begin another development phase.'))

archives={k:zipfile.ZipFile(p) for k,p in ARCHIVES.items()}
dependency_rows=[]
for k,d in r['archive_dependencies'].items():
 p=ARCHIVES[k];actual=core['archive'] if k=='final_handoff' else read(BASE/'session/EARLY-RECOVERY-RECEIPT.json')
 dependency_rows.append({'id':k,**identity(p),'passed':exact(p,d) and all(d[f]==actual[f] for f in ['file_id','library_file_id','version','file_name','bytes','sha256'])})
check('two_exact_archive_dependencies_and_saved_identities',set(r['archive_dependencies'])==set(ARCHIVES) and all(v['passed'] for v in dependency_rows))
imap_raw=archives[r['inherits']['dependency']].read(r['inherits']['member']);imap=parse(imap_raw);inherited={v['relative_path']:v for v in imap['files']}
check('exact_inherited_final_map',r['inherits']['dependency']=='final_handoff' and r['inherits']['member']=='RECOVERY-FILE-MAP.json' and len(imap_raw)==r['inherits']['bytes']==113203 and sha(imap_raw)==r['inherits']['sha256']=='804b3e8e46515142fd8e5f9bb98e1b3ebcc0fb5797fbad7a50d07072f27188e6' and len(inherited)==r['inherits']['files']==234)
blobs={};blob_rows=[]
for digest,blob in r['inline_blobs'].items():
 compressed=base64.b64decode(blob['data'],validate=True);uncompressed=gzip.decompress(compressed)
 good=blob['encoding']=='gzip+base64' and len(compressed)==blob['compressed_bytes'] and sha(compressed)==blob['compressed_sha256'] and len(uncompressed)==blob['bytes'] and sha(uncompressed)==digest
 blobs[digest]=uncompressed;blob_rows.append({'sha256':digest,'bytes':len(uncompressed),'compressed_bytes':len(compressed),'compressed_sha256':sha(compressed),'passed':good})
check('all_61_unique_inline_blobs_exact',len(blobs)==61 and all(v['passed'] for v in blob_rows))
rows=r['files'];by_rel={v['relative_path']:v for v in rows};decoded={}
check('100_safe_unique_regular_permission_paths',len(rows)==len(by_rel)==100 and all(safe(v['relative_path']) and v['original_path']==str(BASE/v['relative_path']) and int(v['source_mode'],8)&~0o777==0 for v in rows))
delta_rows=[]
for row in rows:
 st=row['storage'];raw=archives[st['dependency']].read(st['member']) if st['kind']=='archive_member' else blobs[st['sha256']]
 decoded[row['relative_path']]=raw;p=Path(row['original_path'])
 good=len(raw)==row['bytes'] and sha(raw)==row['sha256'] and p.is_file() and not p.is_symlink() and p.read_bytes()==raw and stat.S_IMODE(p.stat().st_mode)==int(row['source_mode'],8)
 if st['kind']=='archive_member':good=good and safe(st['member'])
 delta_rows.append({k:v for k,v in row.items() if k!='storage'}|{'storage':st,'passed':good})
check('each_delta_blob_or_alias_matches_actual_bytes_and_mode',all(v['passed'] for v in delta_rows) and sum(v['bytes'] for v in rows)==r['logical_bytes']==3548235)
check('30_archive_alias_70_inline_rows_no_unused_blob',Counter(v['storage']['kind'] for v in rows)=={'archive_member':30,'inline_blob':70} and set(v['storage']['sha256'] for v in rows if v['storage']['kind']=='inline_blob')==set(blobs))
git_delta=[]
for row in rows:
 if 'source_git' not in row:continue
 g=row['source_git'];raw=git('show',TERMINAL+':'+g['path']);header=git('ls-tree','-z',TERMINAL,'--',g['path']).split(b'\t')[0].decode().split()
 git_delta.append({'path':row['relative_path'],'passed':g['commit']==TERMINAL and g['tree']==TREE and g['blob']==header[2] and g['mode']==header[0] and raw==decoded[row['relative_path']]})
check('all_12_canonical_recovery_rows_exact_terminal_git',len(git_delta)==12 and all(v['passed'] for v in git_delta))
spec_path='packaging/terminal-inputs/selection-attempt002/SPEC-FINAL.json';spec=parse(decoded[spec_path]);selected=spec['selected_files']
inherited_rows=[]
for selected_row in selected:
 rel=selected_row['relative_path'];p=Path(selected_row['path'])
 if rel in by_rel:continue
 old=inherited[rel];storage=old.get('external_storage');raw=archives[storage['dependency_id']].read(storage['member']) if storage else archives['final_handoff'].read(old['payload_path'])
 inherited_rows.append({'path':rel,'bytes':old['bytes'],'sha256':old['sha256'],'source_mode':old['source_mode'],'passed':p==BASE/rel and safe(rel) and p.read_bytes()==raw and len(raw)==old['bytes'] and sha(raw)==old['sha256'] and stat.S_IMODE(p.stat().st_mode)==int(old['source_mode'],8)})
check('324_selected_exact_224_inherited_plus_100_delta',len(selected)==len({v['relative_path'] for v in selected})==r['selected_files']==324 and len(inherited_rows)==r['inherited_exact_files']==224 and all(v['passed'] for v in inherited_rows) and set(by_rel)<={v['relative_path'] for v in selected})
check('self_and_postfreeze_outputs_not_captured',not any(RECEIPT.name in v['relative_path'] or v['relative_path'].startswith('reviews/terminal-receipt/') for v in rows) and r['cutoff']['remaining_future_operations']==['Independent exact terminal receipt audit','Root terminal receipt save/readback','Matching final confirmation'])
required=['reviews/final/attempt001/AUDIT.json','reviews/final/attempt002/AUDIT.json','reviews/final/attempt002/REPORT.md','reviews/final/attempt002/REVIEWED-FILES.json','reviews/final/OBSERVATION-ERRORS.json','reviews/final/COVERAGE-RECONCILIATION.json','delivery/SAVED-FILES.json','delivery/VERIFY-ATTEMPT001-ERROR.json','reviews/delivery-record/AUDIT.json','publication/receipt-checkpoint/READBACK.json','verification/receipt-record-checks/CHECKS.json']
check('unique_final_delivery_review_failure_evidence_present',all(v in by_rel for v in required) and all('reviews/final/attempt001/'+label+'.'+stream+'.txt' in by_rel for label in ['restore-default','restore-original-modes','refuse-existing','refuse-dangling','refuse-ancestor','refuse-missing-external','refuse-wrong-external','refuse-wrong-external-member','refuse-missing-external-member'] for stream in ['stdout','stderr']))
recon=[]
for rec in r['reconstruction_records']:
 if 'modified_files' in rec:
  root=BASE/rec['path'];changed=[];names=archives['final_handoff'].namelist()
  observed={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
  for n in names:
   if (root/n).read_bytes()!=archives['final_handoff'].read(n):changed.append(n)
  good=observed==set(names) and sorted(changed)==['MANIFEST-SHA256.json','RECOVERY-FILE-MAP.json'] and rec['all_other_members_verified_equal_final'] and all(v['relative_path'] in by_rel and exact(BASE/v['relative_path'],v) and stat.S_IMODE((BASE/v['relative_path']).stat().st_mode)==int(v['source_mode'],8) for v in rec['modified_files'])
 else:
  raw=bytearray(ARCHIVES[rec['source_dependency']].read_bytes());raw[-1]^=1;p=BASE/rec['path']
  good=rec['verified_exact_reconstruction'] and len(raw)==rec['bytes'] and sha(raw)==rec['sha256'] and p.read_bytes()==raw and stat.S_IMODE(p.stat().st_mode)==int(rec['source_mode'],8) and rec['source_sha256']==r['archive_dependencies'][rec['source_dependency']]['sha256']
 recon.append({'path':rec['path'],'passed':good})
check('three_excluded_fixture_reconstructions_exact',len(recon)==3 and all(v['passed'] for v in recon))
links=[]
for link in r['inert_symlink_fixture_metadata']:
 p=BASE/link['relative_path'];links.append({'relative_path':link['relative_path'],'passed':safe(link['relative_path']) and p.is_symlink() and os.readlink(p)==link['target'] and stat.S_IMODE(p.lstat().st_mode)==int(link['mode'],8) and link['relative_path'] not in by_rel and not any(n.startswith(link['relative_path']+'/') for n in by_rel) and 'never create an active link' in link['restoration']})
check('nine_symlinks_retained_as_inert_metadata_only',len(links)==9 and all(v['passed'] for v in links))
exclusions=r['exclusions'];excluded={v['path']:v for v in exclusions}
check('39_exclusions_explicit_no_raw_transfer_payload',len(exclusions)==39 and all(v in excluded for v in ['evidence/final-library-materialize.json','evidence/early-library-materialize.json','publication/source-checkpoint/TREE-PACKET.json','publication/receipt-checkpoint/TREE-PACKET.json']) and not any(v in by_rel for v in ['evidence/final-library-materialize.json','evidence/early-library-materialize.json']))
packet=excluded['publication/receipt-checkpoint/TREE-PACKET.json']
check('terminal_transport_exclusion_hash_and_confirmed_publication',exact(BASE/packet['path'],packet) and pub['all_12_file_bytes_equal_reviewed_checked_candidate'] and pub['checked_index_tree_equals_published_tree'] and 'publication/receipt-checkpoint/INTENT.json' in by_rel and 'publication/prepare_packet.py' in inherited)
check('private_inert_restoration_instructions',all(t in r['restoration'] for t in ['new private directory (0700)','never write original absolute paths','existing destinations and symlink ancestors','Default files to0600','overrides','do not execute payloads','No automatic replay']))
check('immutable_receipt_and_clean_repository_after_review',identity(RECEIPT)['sha256']=='6cdc3eb4d05f52e47a0e43cf85117c5981a34ec0b75dd9f4febdd8441aad8f2a' and git('rev-parse','HEAD').decode().strip()==TERMINAL and not git('status','--porcelain=v1','--untracked-files=all').strip())
for z in archives.values():z.close()
audit={'schema':'ontokin.c271.p13-independent-terminal-receipt-review/1','reviewer':'/root/intake_review','started_at_utc':started,'completed_at_utc':datetime.now(timezone.utc).isoformat(),'receipt':identity(RECEIPT),'terminal_commit':TERMINAL,'terminal_tree':TREE,'source_revision':SOURCE,'source_tree':SOURCE_TREE,'verdict':'accepted_for_exact_self_save_and_readback' if all(v['passed'] for v in checks) else 'blocked','check_groups_passed':sum(v['passed'] for v in checks),'check_groups_failed':sum(not v['passed'] for v in checks),'checks':checks,'details':{'git_changes':git_rows,'archive_dependencies':dependency_rows,'inline_blobs':blob_rows,'delta_rows':delta_rows,'canonical_git_rows':git_delta,'inherited_rows':inherited_rows,'fixture_reconstructions':recon,'inert_links':links},'limits':['Metadata, exact byte/mode comparisons and inert decompression only; no product code, package restore or historical qualification rerun.','The accepted final and early facts are reused through their exact identities.','This audit and the receipt self-save/readback/final confirmation are post-freeze evidence; receipt must not be rebuilt to include them.','No canonical edit or remote/Library write by reviewer.'],'worker_active_operations':[],'worker_unknown_operations':[]}
(OUT/'AUDIT.json').write_text(json.dumps(audit,indent=2)+'\n')
print(json.dumps({'verdict':audit['verdict'],'passed':audit['check_groups_passed'],'failed':audit['check_groups_failed'],'findings':[v for v in checks if not v['passed']],'audit':identity(OUT/'AUDIT.json')},indent=2))
