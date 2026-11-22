#!/usr/bin/env python3
"""Independent receipt audit; never imports or executes archive payloads."""
import base64,collections,datetime,hashlib,io,json,os,pathlib,re,stat,subprocess,zipfile
ROOT=pathlib.Path('/workspace/scratch/bef4a6dd8f04');OUT=ROOT/'recovery/terminal_receipt_review';REPO=ROOT/'OntoKin'
P=ROOT/'deliverables/receipt/OntoKin_C271_P14_Delivery_Receipt_2026-11-21.json'
EXPECTED={'bytes':1821141,'sha256':'cf9cc66071751f63d179c172986c7e4f5b610efcfe96c893e9fad792e0e5bef2'}
CORE='f0fb9a634269b515476f2fc467556ccea789c2d8';TREE='f7348aa84a02a3d2770b722ca6b1246e7c9ba3ed';SOURCE='e26dc6369a8d6ba88ea779b26a8c655121ae5dbc';SOURCE_TREE='0271ee6a507f83015eea06b63b1bed51753ba419';MAIN='e1a48f7d0635e9aa4f4b6d6a586e7305eb81999d'
checks=[];findings=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def ident(b):return {'bytes':len(b),'sha256':sha(b)}
def hashfile(p):
 h=hashlib.sha256();n=0
 with open(p,'rb') as f:
  while b:=f.read(1024*1024):h.update(b);n+=len(b)
 return {'bytes':n,'sha256':h.hexdigest()}
def save(n,v):
 p=OUT/n;p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n');return {'path':str(p),**hashfile(p)}
def check(n,condition,**evidence):
 row={'name':n,'passed':bool(condition),**evidence};checks.append(row)
 if not condition:findings.append(row)
 print(json.dumps({'group':n,'passed':bool(condition)}),flush=True)
def git(*args):return subprocess.check_output(['git','-C',str(REPO),*args])
def pairs(rows):
 d={}
 for k,v in rows:
  if k in d:raise ValueError('Duplicate JSON key '+k)
  d[k]=v
 return d
def safe(n):return bool(n) and not n.startswith('/') and not re.match(r'^[A-Za-z]:',n) and '\\' not in n and '\x00' not in n and all(x not in ('','.','..') for x in n.split('/'))
raw=P.read_bytes();d=json.loads(raw,object_pairs_hook=pairs)
check('exact_receipt_identity_and_unambiguous_json',ident(raw)==EXPECTED,observed=ident(raw),expected=EXPECTED)
e=d['post_freeze_recovery'];zb=base64.b64decode(e['base64'],validate=True)
check('strict_base64_embedded_zip_identity',ident(zb)=={'bytes':e['bytes'],'sha256':e['sha256']} and base64.b64encode(zb).decode()==e['base64'],observed=ident(zb))
Z=zipfile.ZipFile(io.BytesIO(zb));names=Z.namelist();infos=Z.infolist();m=json.loads(Z.read(e['manifest']),object_pairs_hook=pairs);mm={x['path']:{'bytes':x['bytes'],'sha256':x['sha256']} for x in m['files']}
structure=len(names)==len(set(names))==len(set(n.casefold() for n in names)) and all(safe(n) for n in names)
structure=structure and all(not i.is_dir() and stat.S_IFMT(i.external_attr>>16)==stat.S_IFREG and stat.S_IMODE(i.external_attr>>16)==0o644 and not i.flag_bits&1 for i in infos)
check('safe_unique_inert_zip_structure',structure,members=len(names),all_modes='regular0644',encrypted=False)
check('exact_manifest_inventory_and_counts',set(mm)==set(names)-{'MANIFEST-SHA256.json'} and len(mm)==len(m['files'])==e['manifest_payloads']==144 and len(names)==e['members']==145 and sha(Z.read('MANIFEST-SHA256.json'))==e['manifest_sha256'] and sum(i.file_size for i in infos)==e['logical_payload_bytes'],manifest_payloads=len(mm),uncompressed_bytes_including_manifest=sum(i.file_size for i in infos))
extract=OUT/'fresh-extract';extract.mkdir(mode=0o700)
rows=[];bad=[]
for i in infos:
 b=Z.read(i);observed=ident(b);dest=extract/i.filename;dest.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
 with dest.open('xb') as f:f.write(b)
 dest.chmod(0o644)
 good=hashfile(dest)==observed and observed['bytes']==i.file_size and (i.filename not in mm or mm[i.filename]==observed)
 if not good:bad.append(i.filename)
 rows.append({'member':i.filename,**observed,'crc_read':True,'fresh_extract_equal':good})
check('all_crc_payload_hashes_and_fresh_extraction',not bad,verified=len(rows),bad=bad,evidence=save('PAYLOAD-VERIFICATION.json',rows))
sel=json.loads(Z.read('RECOVERY-SELECTION.json'));aliases=json.loads(Z.read('RECOVERY-ALIASES.json'));selection=[];bad=[]
for x in sel['files']:
 src=ROOT/x['source_path'];b=Z.read(x['member']);identity=ident(b);good=safe(x['source_path']) and x['transformation']=='none' and src.is_file() and not src.is_symlink() and hashfile(src)==identity=={'bytes':x['bytes'],'sha256':x['sha256']}
 selection.append({**x,'source_equal':good,'original_mode':oct(stat.S_IMODE(src.lstat().st_mode))})
 if not good:bad.append(x['member'])
check('all_selected_source_bytes_unchanged',not bad and len(sel['files'])==e['selected_input_files']==136 and len({x['member'] for x in sel['files']})==136,count=len(selection),bad=bad,evidence=save('SOURCE-BINDINGS.json',selection))
package_pairs={'package/build_terminal_receipt.py':'recovery/package-work/build_terminal_receipt.py','package/BUILD-CONFIG.json':'recovery/package-work/TERMINAL-RECEIPT-CONFIG.json','package/RECEIPT-PREFLIGHT-CONTENT-CHECK.json':'recovery/package-work/RECEIPT-PREFLIGHT-CONTENT-CHECK.json','package/RECEIPT-PREFLIGHT-INSPECTION-FAILURE.json':'recovery/package-work/RECEIPT-PREFLIGHT-INSPECTION-FAILURE.json'}
check('builder_script_config_and_failed_preflight_preserved',all(Z.read(k)==(ROOT/v).read_bytes() for k,v in package_pairs.items()),bindings=package_pairs,environment_record='package/ENVIRONMENT.json',scope='Compared as inert bytes only; no embedded helper executed.')

up=json.loads(Z.read('recovery/evidence/FINAL-UPLOAD-RESULT.json'))['results'];upmap={x['file_name']:x for x in up};fr=json.loads(Z.read('recovery/evidence/FINAL-SAVE-RECEIPT.json'));fid=json.loads(Z.read('recovery/evidence/FINAL-FILE-IDENTITIES.json'));fidmap={x['name']:x for x in fid};saved=[];bad=[]
check('saved_files_receipt_identity',d['saved_final_files']==fr['files'] and len(upmap)==3 and fr['all_saved'] and fr['all_readbacks_verified'] and fr['original_final_zip_reused_without_changes'],saved_count=len(d['saved_final_files']),confirmed_at=fr['confirmed_at_utc'])
for x in d['saved_final_files']:
 u=upmap[x['file_name']];y=fidmap[x['file_name']];expected={'bytes':x['bytes'],'sha256':x['sha256']}
 local=hashfile(pathlib.Path(x['local_path']));rb=hashfile(pathlib.Path(x['readback_path']))
 good=all(x[k]==v for k,v in u.items()) and all(x[k]==v for k,v in y.items()) and local==rb==expected and x['saved_bytes_readback_equal'] is True and x['status']=='succeeded' and x['version']==x['current_version_number']==0 and x['source_revision']==SOURCE and x['source_tree']==SOURCE_TREE
 good=good and x['url']=='https://chatgpt.com/library?file_id='+x['library_file_id']+'&account_id=personal'
 if not good:bad.append(x['file_name'])
 saved.append({'name':x['file_name'],'role':x['role'],'library_file_id':x['library_file_id'],'file_id':x['file_id'],'version':x['version'],**expected,'local_and_readback_equal':local==rb==expected,'raw_upload_binding_equal':all(x[k]==v for k,v in u.items())})
check('three_final_upload_ids_versions_and_exact_byte_readbacks',not bad,bad=bad,evidence=save('SAVED-FILE-BINDINGS.json',saved))
ziprow=next(x for x in d['saved_final_files'] if x['role']=='handoff_zip');fz=zipfile.ZipFile(ziprow['local_path'])
check('unchanged_final_zip_and_matching_saved_prompts',ziprow['bytes']==88651427 and ziprow['sha256']=='96dd48ac7cfe01219f57a48a3adfaacb1faa21325f72c5ad06ca19fcd54760cd' and all(fz.read(x['archive_member'])==pathlib.Path(x['readback_path']).read_bytes() and x['matches_archived_prompt_bytes'] for x in d['saved_final_files'] if x['role']!='handoff_zip'),source_commit=SOURCE,source_tree=SOURCE_TREE)
ear=d['early_recovery'];er=json.loads(Z.read('recovery/evidence/EARLY-RECOVERY-RECEIPT.json'));eu=json.loads(Z.read('recovery/evidence/EARLY-UPLOAD-RESULT.json'))['results'][0];eid={'bytes':ear['bytes'],'sha256':ear['sha256']}
check('early_saved_identity_upload_and_readback',ear==er and all(ear[k]==v for k,v in eu.items()) and hashfile(pathlib.Path(ear['local_path']))==hashfile(pathlib.Path(ear['readback_path']))==eid and ear['saved_bytes_readback_equal'] and ear['version']==ear['current_version_number']==0,identity={'library_file_id':ear['library_file_id'],'file_id':ear['file_id'],'version':ear['version'],**eid},confirmed_at=ear['confirmed_at_utc'])
aliasrows=[];bad=[]
for x in aliases['files']:
 source=ROOT/x['source_path'];data=fz.read(x['archive_member']);expected={'bytes':x['bytes'],'sha256':x['sha256']};good=ident(data)==hashfile(source)==expected and x['archive_sha256']==ziprow['sha256']
 if not good:bad.append(x['source_path'])
 aliasrows.append({**x,'source_and_archive_equal':good})
check('two_exact_external_duplicate_aliases',not bad and aliases['dependency']==ziprow and len(aliasrows)==e['exact_external_aliases']==2,evidence=save('ALIASES-VERIFICATION.json',aliasrows))

# Enumerate every new substantive evidence/review/publication file, excluding proven extractions.
selected={x['source_path'] for x in sel['files']};aliased={x['source_path'] for x in aliases['files']};allowed={x['path'] for x in sel['exclusions']};uncovered=[];exclusions=[]
for dr in ['recovery/evidence','recovery/final_package_review','recovery/remote_audit','recovery/independent_review','recovery/publication/core']:
 for root,dirs,files in os.walk(ROOT/dr,followlinks=False):
  dirs[:]=[x for x in dirs if x not in ['fresh-extract','extracted']]
  for n in files:
   p=pathlib.Path(root)/n;rel=p.relative_to(ROOT).as_posix()
   if rel in selected or rel in aliased:continue
   if rel in allowed:exclusions.append({'path':rel,**hashfile(p)})
   else:uncovered.append(rel)
check('complete_new_evidence_inventory',not uncovered,selected_files=len(selected),aliased_files=len(aliased),explicit_nonextract_exclusions=exclusions,uncovered=uncovered)
required_arrays=['PAYLOAD-VERIFICATION.json','RECOVERY-VERIFICATION.json','EXCLUSIONS-VERIFICATION.json','SOURCE-VERIFICATION.json','SYMLINK-VERIFICATION.json','AUDIT.json','FINAL-AUDIT.json','DERIVED-READ-CHUNKS-RESOLUTION.json','SPECIAL-FIXTURE-RESOLUTION.json','review_final.py','resolve_findings.py','review.stdout','review.stderr','resolution.stdout','resolution.stderr']
required_failures=['recovery/independent_review/early/AUDIT.json','recovery/independent_review/early/REPORT.md','recovery/independent_review/implementation/audit-attempt001/AUDIT.json','recovery/independent_review/implementation/audit-attempt001/HARNESS-FINDING.json','recovery/independent_review/implementation/audit-attempt001/audit_reuse.py','package/RECEIPT-PREFLIGHT-INSPECTION-FAILURE.json']
check('full_arrays_initial_findings_resolutions_and_failures',all('recovery/final_package_review/'+n in names for n in required_arrays) and all(n in names for n in required_failures),array_and_script_members=required_arrays,failed_attempt_members=required_failures)
# Prior early builder/config bytes and reconstructible failed archive are already in saved wrapper.
ez=zipfile.ZipFile(ear['local_path']);early_bindings={'build_delivery_recovery.py':'recovery/package/build_delivery_recovery.py','correct_early_attempt002.py':'recovery/package/correct_early_attempt002.py','restore_early_attempt001.py':'recovery/package/restore_early_attempt001.py','EARLY-BUILD-CONFIG.json':'recovery/package/BUILD-CONFIG.json'}
earlyequal=all((ROOT/'recovery/package-work'/src).read_bytes()==ez.read(dst) for src,dst in early_bindings.items())
recipe=json.loads(ez.read('recovery/early-attempt001/ZIP-RECONSTRUCTION.json'));restored=hashfile(ROOT/'recovery/independent_review/early-attempt002/restored-attempt001.zip')
original=recipe['original'];expected_original={'bytes':original['bytes'],'sha256':original['sha256']}
check('early_builder_and_failed_archive_preserved_externally',earlyequal and restored==expected_original,early_builder_bindings=early_bindings,failed_archive=restored,reconstruction_member='recovery/early-attempt001/ZIP-RECONSTRUCTION.json',boundary='Prior accepted audit proves reconstruction. This review verifies exact dependency and restored identities without executing its helper.')

rb=json.loads(Z.read(d['core_readback']['member']));cc=json.loads(Z.read(d['core_checks']['member']));cr=json.loads(Z.read(d['reviews']['core_records']['member']));remote=json.loads(Z.read('recovery/publication/core/REMOTE-READBACK.json'))
parsed={k:json.loads(remote[k]['value']['structuredContent']['content']) for k in ('0','1','2')}
core=d['core_repository_checkpoint'];cond=json.loads(Z.read('recovery/publication/core/REF-UPDATE-RESULT.json'))['structuredContent']['success'];created=json.loads(Z.read('recovery/publication/core/CREATE-COMMIT.json'))['structuredContent']['sha']
actual_tree=git('rev-parse',CORE+'^{tree}').decode().strip();actual_parent=git('rev-parse',CORE+'^').decode().strip();head=git('rev-parse','HEAD').decode().strip();clean=not git('status','--porcelain=v1')
coregood=core['commit']==rb['commit']==created==parsed['0']['object']['sha']==parsed['2']['sha']==CORE and actual_tree==core['tree']==rb['tree']==parsed['2']['tree']['sha']==TREE and actual_parent==core['parent']==rb['parent']==SOURCE and parsed['1']['object']['sha']==core['main']==rb['main']==MAIN and cond is True and clean and head==CORE
check('actual_core_commit_tree_parent_remote_and_clean_checkout',coregood,commit=CORE,tree=actual_tree,parent=actual_parent,main=MAIN,HEAD=head,checkout_clean=clean,conditional_nonforce_confirmed=cond)
changed=git('diff-tree','--no-commit-id','--name-only','-r','-z',CORE).decode().rstrip('\0').split('\0');rbpaths={x['path'] for x in rb['files']};bound=[];bad=[]
treemap={}
for entry in git('ls-tree','-rz',CORE).split(b'\0'):
 if not entry:continue
 hdr,p=entry.split(b'\t',1);mode,kind,blob=hdr.decode().split();treemap[p.decode()]={'mode':mode,'kind':kind,'blob':blob}
for x in rb['files']:
 b=git('show',CORE+':'+x['path']);identity=ident(b);entry=treemap[x['path']]
 good=identity=={'bytes':x['bytes'],'sha256':x['sha256']} and entry=={'mode':x['mode'],'kind':'blob','blob':x['blob']} and x['verified'] is True
 bound.append({**x,'git_identity_equal':good})
 if not good:bad.append(x['path'])
check('all45_core_changed_files_exact_git_readback',not bad and len(changed)==len(rbpaths)==len(rb['files'])==45 and set(changed)==rbpaths,changed_count=len(changed),bad=bad,evidence=save('CORE-FILE-BINDINGS.json',bound))
logrows=[];good=True
for c in cc['checks']:
 for stream in ['stdout','stderr']:
  member='recovery/publication/core/'+c['name']+'.'+stream;actual=sha(Z.read(member));equal=actual==c[stream+'_sha256'];good &= equal;logrows.append({'member':member,'sha256':actual,'expected_equal':equal})
 good &= c['exit_code']==0 and c['passed'] is True
check('four_checks_exact_tree_and_logs',good and len(cc['checks'])==4 and cc['all_passed'] and cc['checked_staged_tree']==TREE and cc['source_commit']==SOURCE and ident(Z.read(d['core_checks']['member']))=={'bytes':d['core_checks']['bytes'],'sha256':d['core_checks']['sha256']} and ident(Z.read(d['core_readback']['member']))=={'bytes':d['core_readback']['bytes'],'sha256':d['core_readback']['sha256']},checks_count=len(cc['checks']),log_bindings=logrows,scope='Evidence verification only; no check command rerun.')
check('26_group_independent_core_review_binding',cr['passed']==26 and cr['failed']==0 and cr['mandatory_findings']==[] and cr['reviewed_tree']==TREE and cr['parent_commit']==SOURCE and cr['changed_paths']==45 and cr['verdict']==d['reviews']['core_records']['verdict'],reviewer=cr['reviewer'],reviewed_tree=cr['reviewed_tree'],groups_passed=cr['passed'])
prior_reviews={k:json.loads(Z.read(v['member'])) for k,v in d['reviews'].items() if isinstance(v,dict)}
check('earlier_independent_review_bindings',prior_reviews['final_package']['groups_passed']==22 and prior_reviews['final_package']['verdict']==d['reviews']['final_package']['verdict'] and prior_reviews['implementation_evidence_reuse']['passed']==35 and prior_reviews['implementation_evidence_reuse']['failed']==0 and prior_reviews['early_recovery']['passed']==17 and prior_reviews['early_recovery']['failed']==0,counts={'final_package':22,'implementation_evidence_reuse':35,'early_recovery':17},boundary='Original failed audits remain retained; these counts are artifact/reuse reviews, not new runtime methods.')
protected=['prototypes/static_tray_v01/current_host_inspection_v01.py','tests/test_current_host_loader_path_v01.py']
check('product_source_and_original_final_unchanged',all(git('show',CORE+':'+p)==git('show',SOURCE+':'+p) for p in protected) and all(not p.startswith(('prototypes/','tests/')) for p in changed) and hashfile(pathlib.Path(ziprow['local_path']))=={'bytes':88651427,'sha256':'96dd48ac7cfe01219f57a48a3adfaacb1faa21325f72c5ad06ca19fcd54760cd'},changed_paths_scope='45 documentary files only',runtime_execution_this_audit=False)
s=d['scope_and_stop'];ss=d['self_library_save']
check('truthful_self_save_review_and_external_confirmation_boundary',ss['library_identity_at_freeze'] is None and ss['status_at_freeze']=='pending' and ss['confirmation_record']=='docs/engineering/localized-repair-c271/loader-path-p14/P14-TERMINAL-CONFIRMATION.json' and d['reviews']['receipt_independent_review_at_freeze'].startswith('pending;') and 'After exact terminal receipt review/save/readback and external confirmation, stop' in s['stop'],remaining=['accepted exact receipt save','exact saved byte readback','matching independent review and receipt identity in external terminal confirmation','final branch/main check and stop'])
check('parent_operational_limits_and_no_next_phase',s['parent_status']=='blocked' and s['parent_complete'] is False and s['requirements']=={'R01':'done','R02':'done','R03':'not_done','R04':'not_done','R05':'not_done'} and s['parent_plan']=={'P01':'done','P02':'in_progress'} and s['integration_performed'] is False and s['main_lease_held'] is False and s['N57']=={'actual_loader_completeness':'unestablished','historical_oracle_satisfied':False,'runtime_pass':False,'runtime_skip':False} and s['pr']=={'draft':True,'merged':False,'number':274,'state':'open'} and s['issue']=={'number':273,'state':'open'} and 'stop before H1' in s['next_fresh_chat_action'],N57=s['N57'],unrun=s['unrun'],next_fresh_chat_action=s['next_fresh_chat_action'])
check('current_operation_and_worker_boundary',d['operations']['current_unknown_writes']==[],at_freeze=d['operations']['current_workers'],observed_now={'/root':'running Director delivery finalization','/root/evidence_review':'completed core-record review','/root/package_engineer':'completed frozen receipt; reported no active process or unknown write','/root/remote_reconciliation':'this bounded terminal audit; stops on return'},historical_unknowns=d['operations']['historical_unknowns'],observation_source='collaboration.list_agents observed during this audit; global historical process termination not inferred.')
check('receipt_and_dependencies_unchanged_after_audit',hashfile(P)==EXPECTED and hashfile(pathlib.Path(ziprow['local_path']))=={'bytes':ziprow['bytes'],'sha256':ziprow['sha256']},receipt=hashfile(P))

# Preserve a nonessential preparatory inventory in this review, without modifying the frozen receipt.
preflight=ROOT/'recovery/package-work/TERMINAL-RECEIPT-PREFLIGHT.json'
(OUT/'PREPARATORY-INVENTORY-COPY.json').write_bytes(preflight.read_bytes())
observations=[{'kind':'nonessential_preparatory_inventory','source':str(preflight),'identity':hashfile(preflight),'preservation':'Exact copy included in terminal review evidence as PREPARATORY-INVENTORY-COPY.json. Its only pending-input observation (core READBACK unavailable at preparation) is already retained in package/RECEIPT-PREFLIGHT-CONTENT-CHECK.json and resolved by the confirmed core readback. It adds no lost unique product work and does not require rebuilding the receipt.'},{'kind':'preliminary_path_inventory_output_truncated','effect':'Read-only broad rg inventory included many reproducible extraction trees; no files changed. Focused independent inventories exclude extraction trees and account for all substantive new evidence.'}]
result={'schema':'ontokin.c271.p14-independent-terminal-receipt-review/1','reviewer':'/root/remote_reconciliation','completed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'receipt':{'path':str(P),**EXPECTED},'embedded_zip':{'bytes':len(zb),'sha256':sha(zb),'members':len(names),'manifest_payloads':len(mm),'selected_files':len(selection),'exact_external_aliases':len(aliasrows)},'checks':checks,'passed':sum(c['passed'] for c in checks),'failed':sum(not c['passed'] for c in checks),'mandatory_findings':findings,'verdict':'accepted_for_exact_save_and_terminal_confirmation' if not findings else 'changes_required','material_receipt_change_required':bool(findings),'observations':observations,'limits':['No embedded payload/helper execution','No product tests, host checks or full routine','No Git/index/Library writes','No new milestone or nested worker','Receipt self-save/readback and later external confirmation remain pending until Director completes them'],'worker_stop_state':'On return this reviewer has no active process or unknown write. Other workers were observed completed; Director owns remaining delivery and final stop.'}
save('AUDIT.json',result)
save('READSET.json',{'receipt':{'path':str(P),**EXPECTED,'read_completeness':'Full JSON fields read; base64 strictly decoded and all embedded bytes verified'},'embedded_members_full_byte_verified':len(names),'selected_original_files_full_byte_verified':len(selection),'core_changed_git_files_full_byte_verified':len(bound),'saved_files_local_and_readback_full_byte_verified':4,'governing_instructions':'Previously completed exact-main and required history readsets reused without unchanged full rereads','readset_reference':'../remote_audit/READSET.json'})
report=f'''# Independent terminal receipt review\n\n**Verdict: {result['verdict']}. {result['passed']} groups passed; {result['failed']} failed.**\n\nThe exact receipt is **{EXPECTED['bytes']:,} bytes**, SHA-256 **`{EXPECTED['sha256']}`**. No material change is required.\n\n## Verified identities and evidence\n\nStrict JSON/base64 decoding, CRC reads, safe unique regular `0644` names, exact manifest inventory and every fresh-extracted payload passed. Embedded ZIP: **1,356,061 bytes**, SHA-256 `7de551ac4398ae4f0e44db6b7a284caa012abf4c537e05244e03a9977ee6260a`; **145 members**, **144 manifest payloads**, **136 exact selected source files** and **two exact external aliases**.\n\nFinal ZIP and both prompt receipts match their successful upload IDs, version 0, sizes and SHA-256 values, actual local/readback bytes and archived prompt bytes. The early wrapper receives the same identity/readback verification. The original final ZIP remains unchanged.\n\nCore publication **`{CORE}`**, tree **`{TREE}`**, parent **`{SOURCE}`**, is confirmed by retained remote ref/commit results and immutable Git. All **45 documentary files** match exact published modes, blobs, sizes and hashes. Four passed checks and retained stdout/stderr hashes bind that tree. The independent core review records **26 passed groups**. Checkout was clean at that core head; main remained `{MAIN}`. Production and adapter bytes are unchanged.\n\nThe embedded evidence retains all new raw arrays, failed and corrected review attempts, original findings and resolutions, reviewer/director scripts, publication operations and checks. Both external aliases match the exact saved final ZIP and original files. The failed early package remains reconstructible in the exact saved early wrapper; its prior accepted audit and retained restored bytes agree. Focused source-directory inventories found no unaccounted substantive new evidence. A redundant preparatory inventory is additionally copied into this review's evidence; its pending-core-readback observation was already retained and is resolved.\n\n## Honest final boundary\n\nReceipt review and its own future save identity were correctly pending when frozen. The later `P14-TERMINAL-CONFIRMATION.json` must bind this exact receipt hash/size, actual saved identity/version, exact readback and this accepted independent review. These later facts do not require changing frozen receipt bytes.\n\nC271 remains blocked: R03–R05 unfinished, P02 in progress, PR274 open/draft/unmerged, issue273 open, no main lease or integration. N57 and actual-loader completeness remain unresolved. No runtime methods, H0/H1, full routine or host/native/model/hosted execution occurred in this recovery audit. Complete the receipt save/readback and external confirmation, then stop. Any H0 source-and-plan work requires a new main chat.\n\n## Worker and artifact limits\n\nThe evidence reviewer and package engineer were observed completed. This reviewer stops on return with no active process or unknown write; the Director owns remaining delivery. Historical process uncertainties are preserved rather than relabelled as known termination.\n\nNo embedded helper was run, and this reviewer made no Git, index or Library writes. `AUDIT.json`, detailed payload/source/alias/core/saved-file bindings, `READSET.json`, this script and stdout/stderr form the review evidence. `fresh-extract/` and `postfreeze.zip` are reproducible copies and need not be repackaged.\n'''
(OUT/'REPORT.md').write_text(report)
print(json.dumps({'verdict':result['verdict'],'passed':result['passed'],'failed':result['failed'],'mandatory_findings':len(findings),'report':{'path':str(OUT/'REPORT.md'),**hashfile(OUT/'REPORT.md')},'audit':{'path':str(OUT/'AUDIT.json'),**hashfile(OUT/'AUDIT.json')}}))
