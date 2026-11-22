from pathlib import Path, PurePosixPath
import datetime, hashlib, io, json, os, posixpath, re, stat, struct, zipfile

R=Path('/workspace/scratch/5041e572c132');O=R/'p15-session/final-package-review/attempt002';O.mkdir(exist_ok=True)
P=R/'deliverables/final-attempt002/OntoKin_C271_P15_H0_Loader_Review_Handoff_2026-11-21_Attempt002.zip'
X=R/'final-review-attempt002-extraction';RECON=R/'final-review-attempt001-reconstructed.zip'
NEW_SHA='d1f978b059b5b11a3b344532a550b9593d7a53ed221dca751c73aa6510de36c5';OLD_SHA='440da098ebc5c637d30bdb7d9cd869bd455c3615c4faf6cd7eb43bdd7c3de32b'
C='0474280a2087299004324419ea345ab7c716bc9a';T='0670b1107a5805278d966c47ce4cf1f4d781b10d';H='recovery/session/final-history/attempt001/';B='repository/docs/engineering/localized-repair-c271/host-loader-p15/'
checks=[];findings=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def unique(pairs):
 d={}
 for k,v in pairs:
  if k in d:raise ValueError('duplicate JSON key: '+k)
  d[k]=v
 return d
def j(b):return json.loads(b,object_pairs_hook=unique)
def save(n,d):(O/n).write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
def check(n,ok,d):
 row={'name':n,'passed':bool(ok),'detail':d};checks.append(row)
 if not ok:findings.append({'id':'P15-FINAL-ATTEMPT002-'+str(len(findings)+1).zfill(3),**row})
def safety(z):
 names=z.namelist();ns=set(names)
 paths=len(names)==len(ns)and all(n and not n.startswith('/')and '\\'not in n and ':'not in n and '\x00'not in n and not any(p in ('','.','..')for p in n.split('/'))and PurePosixPath(n).as_posix()==n and not any('/'.join(n.split('/')[:i])in ns for i in range(1,len(n.split('/'))))for n in names)
 modes=all(stat.S_IFMT(i.external_attr>>16)in(0,stat.S_IFREG)and stat.S_IMODE(i.external_attr>>16)==0o644 and not i.is_dir()and not i.flag_bits&1 for i in z.infolist())
 return paths,modes
def check_manifest(payload,name='MANIFEST-SHA256.json'):
 manifest=j(payload[name]);inventory=set(payload)==set(manifest)|{name}and name not in manifest
 return manifest,inventory and all(len(payload[n])==r['bytes']and sha(payload[n])==r['sha256']for n,r in manifest.items())

raw=P.read_bytes()
try:
 with zipfile.ZipFile(io.BytesIO(raw))as z:
  names=z.namelist();paths,modes=safety(z);payload={i.filename:z.read(i)for i in z.infolist()};manifest,valid=check_manifest(payload)
  check('exact_attempt002_identity',len(raw)==49067300 and sha(raw)==NEW_SHA,{'path':str(P),'bytes':len(raw),'sha256':sha(raw)})
  check('all_403_members_safe_unique_regular_inert',len(names)==403 and paths and modes,{'members':len(names),'safe_unique_paths':paths,'regular_0644':modes})
  check('all_CRCs_and_402_payload_inventory_sizes_hashes',len(manifest)==402 and valid,{'payloads':len(manifest),'crc_all_members':True,'exact_manifest':valid})
  if not(paths and modes and valid):raise ValueError('unsafe or invalid Attempt002 ZIP')
  if X.exists():raise ValueError('fresh extraction destination already exists')
  X.mkdir(mode=0o700)
  for n,b in payload.items():
   p=X/n;p.parent.mkdir(exist_ok=True,parents=True,mode=0o700);fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o644)
   with os.fdopen(fd,'wb')as f:f.write(b)
  check('fresh_extracted_bytes_outside_session',all((X/n).read_bytes()==b and stat.S_ISREG((X/n).lstat().st_mode)and stat.S_IMODE((X/n).lstat().st_mode)==0o644 for n,b in payload.items()),{'path':str(X),'outside_recursive_session':True})

  # Independent reassembly: parse metadata and copy raw segments; execute no packaged utility.
  recipe=j(payload[H+'RECIPE.json']);hm=j(payload[H+'MANIFEST.json']);listed=hm['files'];listed_paths={H+r['path']for r in listed};history_names={n for n in names if n.startswith(H)}
  check('all_22_reassembly_artifacts_exactly_bound',len(history_names)==22 and history_names==listed_paths|{H+'MANIFEST.json'}and len(listed_paths)==len(listed)and all(len(payload[H+r['path']])==r['bytes']and sha(payload[H+r['path']])==r['sha256']for r in listed),{'artifacts':len(history_names),'manifest_lists':len(listed),'recipe_sha256':sha(payload[H+'RECIPE.json'])})
  check('recipe_targets_known_failed_candidate',recipe['original_archive']['bytes']==48916090 and recipe['original_archive']['sha256']==OLD_SHA and hm['original_bytes']==48916090 and hm['original_sha256']==OLD_SHA,recipe['original_archive'])
  eocd=raw.rfind(b'PK\x05\x06',max(0,len(raw)-65557))
  if eocd<0:raise ValueError('replacement EOCD absent')
  signature,disk,cd_disk,disk_count,total_count,cd_size,cd_offset,comment_length=struct.unpack_from('<4s4H2IH',raw,eocd)
  if disk or cd_disk or disk_count!=total_count or total_count!=403 or eocd+22+comment_length!=len(raw)or cd_offset+cd_size!=eocd:raise ValueError('unexpected replacement ZIP structure')
  infos=sorted(z.infolist(),key=lambda i:i.header_offset);bounds={}
  for idx,info in enumerate(infos):
   end=infos[idx+1].header_offset if idx+1<len(infos)else cd_offset
   if not 0<=info.header_offset<end<=cd_offset or raw[info.header_offset:info.header_offset+4]!=b'PK\x03\x04':raise ValueError('invalid replacement local-record boundary')
   bounds[info.filename]=(info.header_offset,end)
  def retained_piece(row):
   rel=row['file'];n=H+rel
   if n not in payload:raise ValueError('missing packaged reconstruction data: '+n)
   b=payload[n]
   if len(b)!=row['bytes']or sha(b)!=row['sha256']:raise ValueError('reconstruction piece identity mismatch: '+n)
   return b
  prefix=retained_piece(recipe['prefix']);pieces=[prefix];position=len(prefix);segment_results=[];used_overrides=[]
  for index,row in enumerate(recipe['segments']):
   if row['offset']!=position:raise ValueError('noncontiguous original segment positions')
   if 'override_file'in row:
    rel=row['override_file']
    if not re.fullmatch(r'overrides/\d{6}\.raw',rel):raise ValueError('unexpected override path')
    b=payload[H+rel];origin={'kind':'packaged_override','member':H+rel};used_overrides.append(rel)
   else:
    start,end=bounds[row['source_member']];b=raw[start:end];origin={'kind':'replacement_raw_record','member':row['source_member'],'replacement_offset':start,'replacement_end':end}
   if len(b)!=row['bytes']or sha(b)!=row['sha256']:raise ValueError('raw-record identity mismatch: '+row['source_member'])
   pieces.append(b);position+=len(b);segment_results.append({'index':index,'original_offset':row['offset'],'bytes':len(b),'sha256':sha(b),**origin})
  tailrow=recipe['central_directory_and_tail']
  if position!=tailrow['original_offset']:raise ValueError('original central-directory offset mismatch')
  tail=retained_piece(tailrow);pieces.append(tail);reconstructed=b''.join(pieces)
  check('raw_reassembly_369_records_16_overrides_353_reuses',len(segment_results)==369 and len(used_overrides)==len(set(used_overrides))==16 and sum(r['kind']=='replacement_raw_record'for r in segment_results)==353,{'segments':len(segment_results),'overrides':len(used_overrides),'reused_records':sum(r['kind']=='replacement_raw_record'for r in segment_results),'override_bytes':sum(r['bytes']for r in segment_results if r['kind']=='packaged_override'),'prefix_bytes':len(prefix),'tail_bytes':len(tail)})
  exact_old=len(reconstructed)==48916090 and sha(reconstructed)==OLD_SHA
  check('independent_reconstruction_exact_original_bytes',exact_old,{'bytes':len(reconstructed),'sha256':sha(reconstructed),'inputs':[str(P),H+'RECIPE.json',H+'MANIFEST.json'],'original_scratch_archive_read':False,'original_scratch_override_files_read':False,'packaged_utility_executed':False})
  if not exact_old:raise ValueError('known original ZIP identity not reproduced')
  if RECON.exists():raise ValueError('reconstruction output exists')
  fd=os.open(RECON,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o644)
  with os.fdopen(fd,'wb')as f:f.write(reconstructed)
  save('REASSEMBLY-SEGMENTS.json',segment_results)
  proof={'schema':'ontokin.c271.p15-independent-raw-reassembly-proof/1','reviewer':'/root/receipt_reconciliation','method':'Independently parsed replacement EOCD/local-record bounds, verified all recipe artifact and raw-record hashes, concatenated packaged prefix/16 overrides/353 exact replacement records/tail. No recovered utility was executed.','replacement':{'path':str(P),'bytes':len(raw),'sha256':sha(raw)},'output':{'path':str(RECON),'bytes':len(reconstructed),'sha256':sha(reconstructed)},'original_archive_or_scratch_overrides_read':False,'only_replacement_bytes_and_packaged_recovery_data':True,'exact_known_original_match':exact_old}
  save('REASSEMBLY-PROOF.json',proof)

 with zipfile.ZipFile(io.BytesIO(reconstructed))as old:
  oldpaths,oldmodes=safety(old);oldpayload={i.filename:old.read(i)for i in old.infolist()};oldmanifest,oldvalid=check_manifest(oldpayload)
  check('reconstructed_original_CRC_manifest_and_safety',len(oldpayload)==369 and len(oldmanifest)==368 and oldpaths and oldmodes and oldvalid,{'members':len(oldpayload),'payloads':len(oldmanifest),'crc':True,'manifest':oldvalid})
  check('original_recovery_map_and_changed_payloads_exact',len(oldpayload['RECOVERY-FILE-MAP.json'])==recipe['original_recovery_file_map']['bytes']and sha(oldpayload['RECOVERY-FILE-MAP.json'])==recipe['original_recovery_file_map']['sha256']and all(len(oldpayload[r['source_member']])==r['original_payload']['bytes']and sha(oldpayload[r['source_member']])==r['original_payload']['sha256']for r in recipe['changed_recovery_members']),{'changed_recovery_members':recipe['changed_recovery_members']})

 prior=j(payload['recovery/session/final-package-review/AUDIT.json']);prior_sources=j(payload['recovery/session/final-package-review/SOURCE-BINDINGS.json']);sm=j(payload['SOURCE-MANIFEST.json']);cp=j(payload['CHECKPOINT.json']);oldcp=j(oldpayload['CHECKPOINT.json'])
 check('first_failed_review_and_all_findings_retained',prior['candidate']['sha256']==OLD_SHA and prior['passed']==28 and prior['failed']==2 and {r['id']for r in prior['mandatory_findings']}=={'P15-FINAL-001','P15-FINAL-002'}, {'prior_verdict':prior['verdict'],'prior_findings':[r['id']for r in prior['mandatory_findings']]})
 source_equal=payload['SOURCE-MANIFEST.json']==oldpayload['SOURCE-MANIFEST.json']and all(payload[r['member']]==oldpayload[r['member']]for r in sm)
 framed=all(hashlib.sha1(b'blob '+str(len(payload[r['member']])).encode()+b'\0'+payload[r['member']]).hexdigest()==r['git_blob']for r in sm)
 check('all_80_source_bindings_reused_at_exact_unchanged_commit',len(sm)==80 and source_equal and framed and all(r['passed']for r in prior_sources)and cp['source_revision']==C and cp['source_tree']==T and all(r['commit']==C and r['tree']==T for r in sm),{'source_revision':C,'source_tree':T,'sources':len(sm),'unchanged_source_manifest_and_bytes':source_equal,'prior_local_Git_tree_blob_review':'recovery/session/final-package-review/SOURCE-BINDINGS.json','fresh_git_or_fetch_operations':False})
 links=[]
 for doc in ['README-START-HERE.md','HANDOFF.md','NEXT-TASK.md','RECOVERY-STATUS.md']:
  for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',payload[doc].decode()):
   if re.match(r'^[A-Za-z][A-Za-z0-9+.-]*:',target)or target.startswith('#'):continue
   resolved=posixpath.normpath(posixpath.join(posixpath.dirname(doc),target.split('#',1)[0]));links.append({'document':doc,'target':target,'exists':resolved in payload})
 check('P15_FINAL_002_phase_link_and_all_root_links_corrected',all(r['exists']for r in links)and B+'PHASE.json'in payload and ']('+B+'PHASE.json)'in payload['HANDOFF.md'].decode(),links)
 check('P15_FINAL_001_current_jobs_explicitly_pending',all(s.startswith('Pending:')for s in cp['current_jobs'])and cp['delivery']['status']=='save_pending_at_freeze'and not cp['phase_complete'],{'current_jobs':cp['current_jobs'],'delivery':cp['delivery']})
 stable=['task','phase','scope','acceptance','constraints','stop','technical_stop','technical_stop_at_utc','source_revision','source_tree','parent_status','parent_complete','parent_plan','requirements','published_source','observed_main','latest_main_recheck','main_movement','early_recovery','early_save_confirmed','next_fresh_chat_action','phase_table','pull_request','scope_issue','historical_unknowns','current_unknown_operations']
 check('technical_outcome_source_time_limits_and_parent_gates_unchanged',all(cp[k]==oldcp[k]for k in stable),{'compared_fields':stable,'H0_plan_H1':'remain unaccepted','main_integration':'not performed','final_save':'pending'})
 changed_common=[n for n in payload if n in oldpayload and payload[n]!=oldpayload[n]];added=[n for n in payload if n not in oldpayload];removed=sorted(set(oldpayload)-set(payload));save('CANDIDATE-DELTA.json',{'changed_common':changed_common,'added':added,'removed':removed,'checkpoint_changed_fields':[k for k in set(cp)|set(oldcp)if cp.get(k)!=oldcp.get(k)]})
 check('no_original_archive_payload_dropped',not removed,{'removed':removed,'changed_common_count':len(changed_common),'new_members':len(added)})
 critical=[n for n in oldpayload if n.startswith('repository/')or n.startswith('predecessor/')or n.startswith('recovery/session/source-provenance/')or n.startswith('recovery/session/loader-review/')or n.startswith('recovery/session/h0-static-admission-attempt001/')or n.startswith('recovery/session/host-evidence')or n.startswith('recovery/session/publication/')or n.startswith('recovery/session/verification/')]
 check('previously_accepted_technical_publication_and_check_evidence_unchanged',all(payload[n]==oldpayload[n]for n in critical),{'exact_unchanged_members':len(critical),'prior_28_passed_groups_reused_on_unchanged_inputs':True})
 rm=j(payload['RECOVERY-FILE-MAP.json']);expected={r['member']for r in rm};actual={n for n in payload if n.startswith(('recovery/session/','recovery/reconciliation/','predecessor/saved-receipts/'))}
 check('all_311_recovery_bindings_exact_and_complete',len(rm)==311 and len(expected)==311 and expected==actual and all(len(payload[r['member']])==r['bytes']and sha(payload[r['member']])==r['sha256']for r in rm),{'mapped':len(rm),'inventory':len(actual),'new_recovery_files':len(rm)-277})
 oldmap=j(oldpayload['RECOVERY-FILE-MAP.json']);check('all_old_recovery_members_retained_with_changed_versions_recoverable',{r['member']for r in oldmap}<=expected and all(r['source_member']in oldpayload for r in recipe['changed_recovery_members']),{'old_members':len(oldmap),'new_members':len(rm),'old_changed_versions':'exactly preserved by verified raw reconstruction'})
 check('four_exclusions_and_exact_selection_mappings_unchanged',payload['RECOVERY-EXCLUSIONS.json']==oldpayload['RECOVERY-EXCLUSIONS.json']and payload['recovery/session/receipt-review/final-preflight/SELECTION-RECOMMENDATIONS.json']==oldpayload['recovery/session/receipt-review/final-preflight/SELECTION-RECOMMENDATIONS.json'],{'accepted_exclusions':4,'earlier_exact_source_recovery_review_reused':True})
 desc=j(payload[B+'P15-EVIDENCE.json']);ext=[]
 for row in desc['external_objects']:
  b=payload[row['recovery_member']];ext.append({'member':row['recovery_member'],'bytes':len(b),'sha256':sha(b),'passed':len(b)==row['bytes']and sha(b)==row['sha256']})
 check('both_external_evidence_objects_exact_in_attempt002',len(ext)==2 and all(r['passed']for r in ext),ext)
 check('nested_evidence_ZIP_exactly_unchanged',payload[B+'P15-EVIDENCE.zip']==oldpayload[B+'P15-EVIDENCE.zip']and len(payload[B+'P15-EVIDENCE.zip'])==desc['bytes']and sha(payload[B+'P15-EVIDENCE.zip'])==desc['sha256'],{'members':201,'payloads':200,'unchanged_previous_complete_independent_verification':True})
 prompts=[]
 for member,suffix in [('PROMPT-1-CONTINUE.md','Continue'),('PROMPT-2-RECOVER.md','Recover')]:
  p=P.with_name(P.stem+'_'+suffix+'.md');b=p.read_bytes();prompts.append({'member':member,'path':str(p),'bytes':len(b),'sha256':sha(b),'matches':b==payload[member],'correct_filename':P.name in b.decode()})
 request=j(payload['recovery/session/delivery/final-upload-request.json']);request_text=json.dumps(request)
 check('prompts_and_prepared_upload_request_name_attempt002',all(p['matches']and p['correct_filename']for p in prompts)and P.name in request_text and all(Path(p['path']).name in request_text for p in prompts),{'prompts':prompts,'upload_request_member':'recovery/session/delivery/final-upload-request.json','dispatched_by_reviewer':False})
 check('required_contents_and_recovery_boundary_preserved',all(n in payload for n in ['README-START-HERE.md','CHECKPOINT.json','HANDOFF.md','NEXT-TASK.md','RECOVERY-STATUS.md','PROMPT-1-CONTINUE.md','PROMPT-2-RECOVER.md','HISTORICAL-DEPENDENCIES.json'])and 'does not establish complete offline restoration'in payload['README-START-HERE.md'].decode()and 'future receipt'in payload['README-START-HERE.md'].decode()and 'delivery only'in payload['PROMPT-2-RECOVER.md'].decode(),{'package_type':cp['package_type'],'exact_next_action':cp['exact_next_action']})
 check('reassembly_capture_pending_is_source_time_only','awaiting frozen replacement ZIP' in hm['state']and exact_old,{'packaged_manifest_state':hm['state'],'later_observed_outcome':'Independent exact reconstruction succeeded using only Attempt002 and packaged recovery artifacts. Preserve this separate proof with the later delivery receipt; do not rebuild the frozen archive merely to insert it.'})

except Exception as exc:
 save('HELPER-FAILURE.json',{'type':type(exc).__name__,'message':str(exc),'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks_completed':checks})
 raise

audit={'schema':'ontokin.c271.p15-final-attempt002-independent-review/1','reviewer':'/root/receipt_reconciliation','reviewed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidate':{'path':str(P),'bytes':len(raw),'sha256':sha(raw),'source_revision':C,'source_tree':T},'checks':checks,'passed':sum(r['passed']for r in checks),'failed':sum(not r['passed']for r in checks),'mandatory_findings':findings,'verdict':'accepted_for_final_save'if not findings else 'changes_required_before_final_save','prior_finding_dispositions':{'P15-FINAL-001':'corrected: current jobs explicitly pending','P15-FINAL-002':'corrected: phase declaration link resolves inside package'},'first_archive_recovery_proof':'REASSEMBLY-PROOF.json','current_jobs':[],'current_unknown_writes':[],'save_not_dispatched_by_reviewer':True,'packaged_or_product_code_executed':False,'canonical_Git_Library_or_frozen_artifact_mutations':[]}
save('AUDIT.json',audit)
report=f'''# P15 final Attempt002 independent review

**Verdict: {audit['verdict']}.** All {audit['passed']} of {len(checks)} check groups passed; {len(findings)} mandatory findings remain.

Candidate `{P.name}` is {len(raw):,} bytes, SHA-256 `{sha(raw)}`. Source remains `{C}`, tree `{T}`.

All 403 ZIP members and 402 manifest payloads pass CRC, exact inventory, safe unique relative paths, inert 0644 modes, size/hash checks and fresh extraction/readback outside the session directory. All 311 recovery-file bindings pass. Both prompts match their ZIP members and the prepared upload request names Attempt002.

Both first-review findings are corrected. Current jobs explicitly describe pending save/readback/receipt actions. The HANDOFF phase-declaration link resolves to an included exact repository snapshot; all root relative links resolve.

The 80 source snapshots and their complete manifest are identical to the independently accepted first candidate, and their Git blob hashes were recomputed. Technical decisions, source/host observations, published commit/readback and documentary logs remain byte-identical. Their prior 28 accepted review groups are reused on unchanged inputs; package mechanics and changed recovery material were checked again. Both declared external evidence objects remain exact. The four accepted derived exclusions and precise recovery mappings are unchanged.

## Independent recovery of the failed first ZIP

Using only Attempt002 bytes and its packaged recipe/overrides, this review independently parsed ZIP local-record boundaries and concatenated the retained prefix, 16 packaged overrides, 353 exact replacement records and original central-directory/tail. Every recipe/artifact/segment hash matched. No supplied recovery utility was executed, and neither the original scratch ZIP nor scratch override sources were read.

The result is exactly **48,916,090 bytes**, SHA-256 **`{OLD_SHA}`**. The reconstructed archive also passes all 369 member CRCs, its 368-payload manifest and safe-path/mode checks. Output: `{RECON}`. Detailed proof and per-segment bindings are retained beside this report.

The packaged reconstruction README/manifest truthfully describe their capture-time pending verification. This later exact proof supplies the result; preserve it in the separate delivery evidence without changing the frozen archive.

Source-union acceptance remains separate from the first libc dynamic-tag refusal. H0, operational-plan adoption and H1 remain unaccepted. Parent C271, its retained branch, draft PR274 and issue273 remain open. Final save is still pending; this review establishes eligibility for saving, not confirmed delivery.

No current reviewer job or unknown write remains. No canonical, Git/index, frozen ZIP/prompt or Library mutation occurred. Root owns save/readback and the later separate receipt.
'''
(O/'REPORT.md').write_text(report)
print(json.dumps({'verdict':audit['verdict'],'checks':len(checks),'passed':audit['passed'],'failed':audit['failed'],'mandatory_findings':findings,'reconstructed_archive':{'path':str(RECON),'bytes':len(reconstructed),'sha256':sha(reconstructed)},'audit':str(O/'AUDIT.json'),'report':str(O/'REPORT.md')}))
