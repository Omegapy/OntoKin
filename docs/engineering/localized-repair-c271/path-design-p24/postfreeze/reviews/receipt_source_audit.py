from pathlib import Path
import collections,datetime,hashlib,json,re,subprocess
ROOT=Path('/workspace/scratch/660f372e2414');REPO=ROOT/'OntoKin';OWN=ROOT/'reviews/recovery';SNAP=OWN/'receipt-source-attempt001-inputs';PREFIX='docs/engineering/localized-repair-c271/path-design-p24';CORE='66866415e492e151eafd95da2237374fc127f79b';checks=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def blob(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def git(*args):return subprocess.check_output(['git','--no-optional-locks','-C',str(REPO),*args])
def read(rel):return json.loads((SNAP/rel).read_bytes())
def phase_read(rel):return read(PREFIX+'/'+rel)
def base(rel):return json.loads(git('show',CORE+':'+rel))
def check(group,name,passed,**details):checks.append(dict(group=group,name=name,passed=bool(passed),**details))
def bindcheck(group,binding):
 data=(SNAP/binding['path']).read_bytes();check(group,binding['path'],len(data)==binding.get('bytes',binding.get('size_bytes')) and sha(data)==binding['sha256'])
readset=json.loads((OWN/'RECEIPT-SOURCE-READSET.json').read_bytes());changed=git('diff','--name-only',CORE).decode().splitlines();index={}
for row in git('ls-files','--stage','-z').decode().split('\0'):
 if row:
  meta,path=row.split('\t',1);mode,oid,stage=meta.split();index[path]=(mode,oid,stage)
for rec in readset['files']:
 data=(SNAP/rec['path']).read_bytes();check('snapshot',rec['path'],(REPO/rec['path']).read_bytes()==data and len(data)==rec['bytes'] and sha(data)==rec['sha256'])
 check('index',rec['path'],rec['path'] in index and index[rec['path']][1]==blob(data) and index[rec['path']][2]=='0')
check('scope','Exactly the 32 captured receipt-delta files',len(changed)==32 and set(changed)=={r['path'] for r in readset['files']})
allowed_existing={PREFIX+'/PHASE.json',PREFIX+'/OUTCOME.json','docs/workflow/CURRENT.json','docs/workflow/tasks/C271/task.json'}
existing=set(git('ls-tree','-r','--name-only',CORE).decode().splitlines())
check('scope','Existing source edits confined to delivery-bearing records',set(changed)&existing==allowed_existing)
check('scope','All other additions are receipt evidence',all(p.startswith(PREFIX+'/postfreeze/') or p.startswith(PREFIX+'/checks/receipt-final/') or p in [PREFIX+'/P24-DELIVERY.json',PREFIX+'/PRESERVATION-RECEIPT.json'] for p in set(changed)-existing))
missing_index=[str(p.relative_to(REPO)) for p in (REPO/PREFIX).rglob('*') if p.is_file() and str(p.relative_to(REPO)) not in index]
check('scope','No local phase file omitted from index',not missing_index,omitted=missing_index)
check('scope','No product/test/tool/config or governing source delta',not git('diff','--name-only',CORE,'--','prototypes','tests','tools','ontokin','.github','.agents','AGENTS.md','ROLE.md','pyproject.toml').strip())
for rel in ['ADOPTION.json','CANDIDATE-MANIFEST.json','DECISION-CANDIDATE.md','SCHEMA.json','SOURCE-BINDINGS.json','reviews/path/REVIEW-FINAL.json','reviews/path/CONTROL-MATRIX.json','reviews/path/CONTROL-CROSSWALK.json','EARLY-RECOVERY-RECEIPT.json','SESSION-INCIDENTS.json']:
 check('frozen_preservation',rel,(REPO/PREFIX/rel).read_bytes()==git('show',CORE+':'+PREFIX+'/'+rel))
check('frozen_preservation','All design history and prior reviewer evidence unchanged',not git('diff','--name-only',CORE,'--',PREFIX+'/history',PREFIX+'/reviews',PREFIX+'/checks/candidate001',PREFIX+'/checks/candidate002',PREFIX+'/checks/core-final').strip())
receipt=phase_read('P24-DELIVERY.json');savedreview=phase_read('postfreeze/reviews/FINAL-SAVED-REVIEW.json');archive_review=phase_read('postfreeze/reviews/FINAL-ARCHIVE-REVIEW.json');saved=phase_read('postfreeze/evidence/FINAL-SAVE-READBACK.json');upload=phase_read('postfreeze/evidence/FINAL-UPLOAD-RESULT.json')
check('saved_review','Exact independent accepted 40-check saved review',sha((SNAP/PREFIX/'postfreeze/reviews/FINAL-SAVED-REVIEW.json').read_bytes())=='280125f46f6b9fc92d7b6c074c648c2bd9d6f2b133f12069018f9b0529c76e4a' and savedreview['verdict']=='ACCEPTED_SAVED_HANDOFF_AND_MATCHING_PROMPTS' and savedreview['unresolved_mandatory_findings']==0 and savedreview['checks_total']==savedreview['checks_passed']==len(savedreview['checks'])==40 and all(c['passed'] for c in savedreview['checks']))
check('saved_review','Exact accepted archive review reused',sha((SNAP/PREFIX/'postfreeze/reviews/FINAL-ARCHIVE-REVIEW.json').read_bytes())=='26ddf516a3055aa2532675dfa5561f3e765083d0d0529adfc38d78eca28ea08b' and archive_review['verdict']=='ACCEPTED_FOR_SAVE' and archive_review['unresolved_mandatory_findings']==0)
for key in ['independent_package_review','independent_saved_readback_review']:bindcheck('receipt_binding',receipt[key])
check('saved_identity','All evidence names the same frozen core',receipt['source_commit']==savedreview['source_commit']==saved['source_commit']==CORE and receipt['source_tree']==savedreview['source_tree']==archive_review['archive']['source_tree']=='546798a1d3cadc9cf4211c219827287d1ad1bc03')
check('saved_identity','Exact saved archive and prompts copied from readback record',receipt['archive']==saved['archive'] and receipt['matching_prompts']==saved['matching_prompts'])
previous=[archive_review['archive']]+archive_review['matching_prompts'];actual=[receipt['archive']]+receipt['matching_prompts']
for i,(rec,proof,audited) in enumerate(zip(actual,savedreview['saved_files'],previous)):
 check('saved_identity','Saved item '+str(i)+' matches accepted bytes',rec['bytes']==proof['size_bytes']==audited['bytes'] and rec['sha256']==proof['sha256']==audited['sha256'] and proof['actual_byte_equality'] is True and rec['saved_bytes_readback_equal'] is True)
 check('saved_identity','Saved item '+str(i)+' stable IDs and version agree',all(rec[k]==proof[k] for k in ['file_name','file_id','library_file_id','version','url']) and rec['version']==0 and rec['status']=='succeeded' and rec['local_metadata_applied'] is True)
 if i:check('saved_identity','Prompt '+str(i)+' is exact ZIP member',rec['matches_zip_member'] is True and savedreview['prompt_members'][i-1]['exact_saved_member_equality'] is True and rec['zip_member']==savedreview['prompt_members'][i-1]['zip_member']==audited['archive_member'])
for rec in savedreview['inputs']:
 original=Path(rec['path']);data=original.read_bytes();check('saved_review_input',str(original),len(data)==rec['size_bytes'] and sha(data)==rec['sha256'])
check('saved_identity','Saved confirmation precedes receipt authoring',receipt['confirmed_at_utc']==saved['confirmed_at_utc'] and receipt['confirmed_at_utc']<savedreview['reviewed_at_utc']<receipt['recorded_at_utc'])
check('terminal','Truthful pending final receipt and terminal markers',receipt['status']=='zip_and_prompts_saved_verified_terminal_receipt_pending' and receipt['phase_complete'] is False and receipt['parent_complete'] is False and receipt['receipt_publication'].startswith('Pending ') and 'matching live PR274/issue273 P24 terminal markers' in receipt['terminal_resolution'])
check('terminal','Parent and PR/issue remain open',receipt['requirements']=={'R01':'done','R02':'done','R03':'not_done','R04':'not_done','R05':'not_done'} and receipt['parent_plan']=={'P01':'done','P02':'in_progress'} and receipt['pr']=={'number':274,'state':'open','draft':True,'merged':False} and receipt['issue']=={'number':273,'state':'open'})
check('terminal','No implementation/runtime/integration authorization',receipt['production_implementation_changed'] is False and receipt['h0_accepted'] is False and receipt['h1_executed'] is False and receipt['main_lease_held'] is False and receipt['main_integration'] is False and receipt['control_counts']['executed']==0 and receipt['current_unknown_operations']==[] and receipt['next_action'].endswith('No technical work or second phase.'))
tr='docs/workflow/tasks/C271/task.json';cr='docs/workflow/CURRENT.json';task=read(tr);before=base(tr);current=read(cr);bc=base(cr)
for key in set(before)-{'checks','delivery','next_action','requirements','session_phase'}:check('task_history','Unchanged task field '+key,task.get(key)==before[key])
check('task_history','All 82 core checks retained and one receipt check appended',task['checks'][:-1]==before['checks'] and len(task['checks'])==83 and task['checks'][-1]['result']=='passed')
for old,new in zip(before['requirements'],task['requirements']):
 check('task_history','Requirement '+old['id']+' state/acceptance/history preserved',{k:v for k,v in old.items() if k!='evidence'}=={k:v for k,v in new.items() if k!='evidence'} and new['evidence'][:len(old['evidence'])]==old['evidence'] and (new['evidence'][len(old['evidence']):]==([PREFIX+'/P24-DELIVERY.json'] if old['id']=='R05' else [])))
session_allowed={'status','final_handoff_saved','delivery_confirmed','delivery_receipt','handoff_source_revision','independent_package_review','next_phase_started'}
check('task_history','Session technical state unchanged',all(task['session_phase'].get(k)==v for k,v in before['session_phase'].items() if k not in session_allowed) and task['session_phase']['phase_complete'] is False and task['session_phase']['delivery_confirmed'] is False and task['session_phase']['next_phase_started'] is False)
check('terminal','Canonical records agree on delivery-only next action',task['next_action']==current['next_action']['summary']==receipt['next_action'] and current['next_action']['status']=='ready' and current['pending_phase_delivery']==task['delivery'])
for key in set(bc)-{'boundaries','latest_handoff','next_action','older_handoffs','pending_phase_delivery','previous_handoff','snapshot_date'}:check('current_history','Unchanged CURRENT field '+key,current.get(key)==bc[key])
check('current_history','Prior handoff rotation is lossless',current['previous_handoff']==bc['latest_handoff'] and current['older_handoffs'][:len(bc['older_handoffs'])]==bc['older_handoffs'] and bc['previous_handoff'] in current['older_handoffs'])
check('current_history','Prior boundaries are retained',current['boundaries'][:-1]==bc['boundaries'])
check('current_history','Latest handoff identifies exact saved partial phase',current['latest_handoff']['sha256']==receipt['archive']['sha256'] and current['latest_handoff']['library_file_id']==receipt['archive']['library_file_id'] and current['latest_handoff']['matching_prompts']==receipt['matching_prompts'] and current['latest_handoff']['partial'] is True and current['latest_handoff']['phase_complete'] is False)
for rel in ['PHASE.json','OUTCOME.json']:
 new=phase_read(rel);old=base(PREFIX+'/'+rel);permitted={'delivery_receipt','delivery_status','final_handoff_saved','terminal_resolution'}
 check('phase_state',rel+' only delivery fields changed',all(new.get(k)==v for k,v in old.items() if k not in permitted) and set(new)-set(old)<=permitted and new['phase_complete'] is False and new['delivery_status']==receipt['status'] and new['terminal_resolution']==receipt['terminal_resolution'])
manifest=phase_read('postfreeze/SOURCE-MANIFEST.json');manifest_paths={r['path'] for r in manifest['files']}
actual_post={str(p.relative_to(SNAP)) for p in (SNAP/PREFIX/'postfreeze').rglob('*') if p.is_file()}
check('postfreeze_manifest','All 18 post-freeze payloads represented exactly',len(manifest['files'])==len(manifest_paths)==18 and actual_post==manifest_paths|{PREFIX+'/postfreeze/SOURCE-MANIFEST.json'})
for rec in manifest['files']:bindcheck('postfreeze_binding',rec)
for rec in manifest['files']:
 rel=rec['path'].split('/postfreeze/',1)[1]
 if rel.startswith('reviews/'):
  name=Path(rel).name;original=(ROOT/'reviews/delivery'/name) if name=='FINAL-SAVED-REVIEW.json' else OWN/name
 elif rel.startswith('evidence/'):
  name=Path(rel).name;original=(ROOT/'records/postfreeze'/name) if name=='REMOTE-CORE-STATE.json' else ROOT/'records'/name
 elif rel.startswith('session-records/'):original=ROOT/'records/postfreeze'/rel[len('session-records/'):]
 else:original=ROOT/'records/record_final_delivery.py'
 check('postfreeze_exact_copy',rel,(SNAP/rec['path']).read_bytes()==original.read_bytes())
history=phase_read('postfreeze/session-records/delivery-helper-history/PROVENANCE.json')
for rec in history['files']:
 path=PREFIX+'/postfreeze/session-records/delivery-helper-history/'+rec['name'];data=(SNAP/path).read_bytes();check('helper_history',rec['name'],len(data)==rec['bytes'] and sha(data)==rec['sha256'])
check('helper_history','Originally reviewed helper hash preserved',history['files'][0]['sha256']==archive_review['preserved_prior_attempt']['delivery_script_sha256']=='dec34df7667806abe3fd6b41ea7006412bb1e918fbd6fbfb0061234c940345d6')
check('failure_preservation','Rejected first archive audit remains exact',sha((SNAP/PREFIX/'postfreeze/reviews/FINAL-ARCHIVE-REVIEW.attempt001.json').read_bytes())==archive_review['preserved_prior_attempt']['sha256']=='a62c36e17e871dd8f7959222fd99cf1d12e1638aaddca38cd964d2c2ecd2f141')
lines=upload['raw_receipt_stream'].splitlines();markers=[l for l in lines if l.startswith('__OPENAI_LIBRARY_FILE_WRITE_RECEIPT_V1__=')];last=json.loads(lines[-1])
check('failure_preservation','Original successful receipt stream and local parse failure retained',len(markers)==3 and last['results']==upload['results'] and upload['local_parse_incident']['id']==savedreview['local_parse_incident']['id']=='P24-DELIVERY-PARSE-001' and upload['local_parse_incident']['current_unknown_operation'] is False and 'No upload retried' in upload['local_parse_incident']['resolution'])
result=phase_read('checks/receipt-final/RESULT.json');doc=phase_read('checks/receipt-final/documentation.stdout.log');stream_count=0
for c in result['checks']:
 check('documentary_result',c['name'],c['result']=='passed' and c['exit_code']==0)
 for key in ['stdout','stderr']:bindcheck('documentary_log',c[key]);stream_count+=1
check('documentary_result','Receipt-only check scope and counts',result['head']==CORE and result['passed'] is True and result['product_tests_run'] is False and result['h0_h1_run'] is False and doc['status']=='passed' and doc['links']['documents']==1615 and doc['links']['local_links']==6280 and doc['sections_verified']==233 and doc['sources_verified']==29 and doc['failures']==[])
check('documentary_result','Workflow reports 12 tasks','Workflow structure passed (12 tasks).' in (SNAP/PREFIX/'checks/receipt-final/workflow.stdout.log').read_text())
preservation=phase_read('PRESERVATION-RECEIPT.json');check('documentary_result','13 preservation results remain passed',preservation['current_head']==CORE and len(preservation['checks'])==13 and preservation['passed'] is True and all(c['passed'] for c in preservation['checks']))
report={'schema':'ontokin.c271.p24-receipt-source-review/1','reviewer':'/root/recovery_audit','reviewed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Only the staged 32-file receipt-source delta from published core 66866415e492e151eafd95da2237374fc127f79b: delivery-state changes, exact saved identities, new evidence/history/manifest/log preservation and index agreement. Earlier design/source/archive/readback reviews reused by exact binding; none re-executed.','base_core':CORE,'verdict':'ACCEPTED_FOR_CONDITIONAL_RECEIPT_PUBLICATION' if all(c['passed'] for c in checks) else 'UNRESOLVED_FINDINGS','unresolved_mandatory_findings':sum(not c['passed'] for c in checks),'reviewed_files':readset['files'],'counts':{'changed_files':32,'modified_existing_delivery_records':4,'new_receipt_evidence_files':28,'postfreeze_manifest_payloads':18,'receipt_check_streams':stream_count,'prior_core_task_checks_retained':82,'current_task_checks':83,'saved_artifacts':3,'saved_review_checks_reused':40,'archive_review_comparisons_reused':246,'receipt_documentary_commands_passed':3,'preservation_assertions_passed':13},'comparisons':{'total':len(checks),'passed':sum(c['passed'] for c in checks),'by_group':dict(collections.Counter(c['group'] for c in checks))},'checks':checks,'saved_archive_identity':{k:receipt['archive'][k] for k in ['file_name','bytes','sha256','library_file_id','file_id','version']},'receipt_time_boundary':{'zip_and_prompts_saved_readback':True,'receipt_commit_created':False,'external_receipt_saved':False,'matching_terminal_markers_verified':False,'phase_complete':False,'parent_complete':False},'findings':[],'limits':['No full source/archive/design audit, saved readback execution, product invocation, host action, remote query/write, canonical edit or Git/index mutation performed.','Saved-byte and xattr facts are supported by the exact independent /root/path_review 40-check report and preserved actual upload/materialization/readback evidence; no new upload/download performed.','Earlier successful receipt-final whitespace covers its recorded index snapshot. Director must run the final staged-whitespace gate after adding this review.','The reviewed postfreeze manifest covers the current 18 payloads. Appending this review and its supporting audit metadata is a later documentary addition and must be preserved without rewriting frozen core/ZIP.','Receipt commit publication/readback, external receipt save/readback and matching live terminal metadata remain pending and must agree on ZIP hash, core commit, receipt commit and receipt identity before phase delivery is terminal.'],'next_action':'Director may append this review, perform final staged whitespace, conditionally publish and read back receipt commit, save/read back the external receipt and verify matching terminal markers; then stop. C271 remains open and no technical phase starts.'}
path=OWN/'RECEIPT-SOURCE-REVIEW.json'
with path.open('x') as f:json.dump(report,f,indent=2);f.write('\n')
print(json.dumps({'report':str(path),'bytes':path.stat().st_size,'sha256':sha(path.read_bytes()),'verdict':report['verdict'],'counts':report['counts'],'comparisons':report['comparisons'],'failures':[c for c in checks if not c['passed']]},indent=2))
