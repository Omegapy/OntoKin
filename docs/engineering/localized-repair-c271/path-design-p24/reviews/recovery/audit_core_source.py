from pathlib import Path
import base64, collections, datetime, hashlib, json, re, subprocess, zipfile
ROOT=Path('/workspace/scratch/660f372e2414');REPO=ROOT/'OntoKin';OWN=ROOT/'reviews/recovery'
SNAP=OWN/'core-source-attempt001-inputs';PREFIX='docs/engineering/localized-repair-c271/path-design-p24'
START='3bc46e80f3d59616110b218740a5f5f3dd688a57';MAIN='e43cc6c5777874101a40559e4058ad6826b07e51'
checks=[]
def sha(data):return hashlib.sha256(data).hexdigest()
def blob(data):return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
def git(*args):return subprocess.check_output(['git','--no-optional-locks','-C',str(REPO),*args])
def check(group,name,passed,**evidence):checks.append(dict(group=group,name=name,passed=bool(passed),**evidence))
def js(rel):return json.loads((SNAP/rel).read_bytes())
def pjs(rel):return js(PREFIX+'/'+rel)
def verify_binding(group,rec,rel=None):
 rel=rel or rec['path'];data=(SNAP/rel).read_bytes();size=rec.get('bytes',rec.get('size_bytes'))
 check(group,rel,len(data)==size and sha(data)==rec['sha256'],bytes=len(data),sha256=sha(data))
def canonical_worker_path(path):
 p=Path(path)
 if p.is_absolute():
  rel=p.relative_to(ROOT).as_posix()
  if rel.startswith('design/path/'):return PREFIX+'/'+rel[len('design/path/'):]
  if rel.startswith('reviews/path/'):return PREFIX+'/'+rel
  raise ValueError(path)
 return PREFIX+'/'+path
manifest=json.loads((OWN/'CORE-SOURCE-READSET.attempt001.json').read_bytes())
incident_rel=PREFIX+'/SESSION-INCIDENTS.json'
new_incident=(REPO/incident_rel).read_bytes();old_incident=(SNAP/incident_rel).read_bytes()
correction=OWN/'core-source-attempt001-correction';correction.mkdir(exist_ok=False)
(correction/'SESSION-INCIDENTS.json').write_bytes(new_incident)
inc=json.loads(new_incident);oldinc=json.loads(old_incident)
check('history','incident append preserves all prior incidents',inc['incidents'][:len(oldinc['incidents'])]==oldinc['incidents'] and inc['incidents'][-1]['id']=='P24-DOC-002')
rows=git('ls-files','--stage','-z').decode().split('\0');index={}
for row in rows:
 if row:
  meta,path=row.split('\t',1);mode,oid,stage=meta.split();index[path]=(mode,oid,stage)
reviewed=[]
for rec in manifest['files']:
 rel=rec['path'];data=new_incident if rel==incident_rel else (SNAP/rel).read_bytes();current=(REPO/rel).read_bytes()
 check('snapshot',rel,current==data)
 check('index',rel,rel in index and index[rel][1]==blob(data) and index[rel][2]=='0',index_entry=index.get(rel))
 reviewed.append({'path':rel,'bytes':len(data),'sha256':sha(data),'index_blob_sha1':index.get(rel,[None,None])[1]})
allowed={'docs/workflow/CURRENT.json','docs/workflow/tasks/C271/task.json','docs/workflow/tasks/C271/REQUIREMENTS.md','docs/workflow/tasks/C271/PLAN.md','docs/workflow/tasks/C271/P24-SESSION.md'}
changed=git('diff','--name-only','-z',START).decode().split('\0');changed=[p for p in changed if p]
check('scope','All changed paths remain authorized phase documents',all(p in allowed or p.startswith(PREFIX+'/') for p in changed),changed_count=len(changed))
check('scope','All changed paths are in reviewed inventory',set(changed)=={r['path'] for r in reviewed},unreviewed=sorted(set(changed)-{r['path'] for r in reviewed}))
check('scope','Protected implementation/test/tool/config paths unchanged',not git('diff','--name-only',START,'--','prototypes','tests','tools','ontokin','.github','pyproject.toml').strip())
task_rel='docs/workflow/tasks/C271/task.json';cur_rel='docs/workflow/CURRENT.json'
btask=json.loads(git('show',START+':'+task_rel));task=js(task_rel);bcur=json.loads(git('show',START+':'+cur_rel));cur=js(cur_rel)
for key in ['checks','prior_session_phases','prior_phase_deliveries','phase_reconciliations']:
 check('history',key+' prior ordered prefix exact',task[key][:len(btask[key])]==btask[key],old_count=len(btask[key]),current_count=len(task[key]))
check('history','P23 active session archived exactly',task['prior_session_phases'][-1]==btask['session_phase'])
check('history','P23 active delivery archived exactly',task['prior_phase_deliveries'][-1]==btask['delivery'])
check('history','CURRENT prior delivery archived exactly',cur['prior_p24_start_pending_delivery']==bcur['pending_phase_delivery'])
check('history','CURRENT old recovery archived exactly',cur['older_recoveries'][:-1]==bcur['older_recoveries'] and cur['older_recoveries'][-1]==bcur['latest_recovery'])
check('history','CURRENT old boundaries retained exactly',cur['boundaries'][:len(bcur['boundaries'])]==bcur['boundaries'])
for a,b in zip(task['requirements'],btask['requirements']):
 check('history','Requirement '+a['id']+' unchanged except appended evidence',{k:v for k,v in a.items() if k!='evidence'}=={k:v for k,v in b.items() if k!='evidence'} and a['evidence'][:len(b['evidence'])]==b['evidence'])
for key in set(btask)-{'checks','delivery','next_action','owner','phase_reconciliations','prior_phase_deliveries','prior_session_phases','requirements','session_phase'}:
 check('history','task unchanged field '+key,task.get(key)==btask[key])
for key in set(bcur)-{'boundaries','latest_recovery','next_action','older_recoveries','pending_phase_delivery','snapshot_date'}:
 check('history','CURRENT unchanged field '+key,cur.get(key)==bcur[key])
for rel in ['docs/workflow/tasks/C271/REQUIREMENTS.md','docs/workflow/tasks/C271/PLAN.md']:
 check('history',rel+' exact prior prefix',(SNAP/rel).read_bytes().startswith(git('show',START+':'+rel)))
check('state','CURRENT next_action is ready delivery-only',cur['next_action']['status']=='ready' and cur['next_action']['suggested_task']=='C271 P24 delivery only; no second technical phase')
check('state','Parent remains unfinished',{r['id']:r['status'] for r in task['requirements']}=={'R01':'done','R02':'done','R03':'not_done','R04':'not_done','R05':'not_done'} and task['status']==btask['status'])
adopt=pjs('ADOPTION.json');outcome=pjs('OUTCOME.json');phase=pjs('PHASE.json');review=pjs('reviews/path/REVIEW-FINAL.json');candidate=pjs('CANDIDATE-MANIFEST.json');schema=pjs('SCHEMA.json');matrix=pjs('reviews/path/CONTROL-MATRIX.json');cross=pjs('reviews/path/CONTROL-CROSSWALK.json');integrity=pjs('reviews/path/FINAL-INTEGRITY-AUDIT.json')
for binding in adopt['accepted_payloads']+[adopt[k] for k in ['candidate_manifest','independent_review','frozen_control_matrix','control_crosswalk']]:verify_binding('adoption_binding',binding)
for binding in candidate['payloads']:verify_binding('candidate_binding',binding,PREFIX+'/'+binding['path'])
for key in ['candidate_manifest','frozen_control_matrix','control_crosswalk','integrity_audit','readset','adopted_binding_audit','revision_history']:
 rec=review[key];verify_binding('review_binding',rec,canonical_worker_path(rec['path']))
for rec in review['reviewed_payloads']+review['prior_reviews']:verify_binding('review_binding',rec,canonical_worker_path(rec['path']))
for rec in outcome['documentary_evidence']:verify_binding('outcome_binding',rec)
check('adoption','Exact attempt004 accepted before separate adoption',adopt['candidate']==review['candidate']==candidate['candidate']==cross['candidate']=='attempt004' and review['verdict']=='accepted_for_separate_director_adoption_design_only' and review['reviewed_at_utc']<adopt['adopted_at_utc'])
check('adoption','Separate adoption leaves frozen candidate states intact',adopt['status']=='adopted_for_future_implementation_only' and candidate['status']=='frozen_for_independent_review_not_adopted' and schema['status']=='proposed_for_independent_review_not_adopted')
check('adoption','Three original mandatory findings resolved',review['mandatory_findings_total']==review['mandatory_findings_resolved']==3 and review['unresolved_mandatory_findings']==adopt['unresolved_mandatory_findings']==0)
check('adoption','Twelve manual groups and 101 documentary integrity checks',len(review['manual_review_groups'])==12 and all(c['passed'] for c in review['manual_review_groups']) and len(integrity['checks'])==integrity['checks_total']==integrity['checks_passed']==101 and all(c['passed'] for c in integrity['checks']))
counts=dict(collections.Counter(c['kind'] for c in matrix['cases']))
check('controls','Exact counts and unexecuted state',counts=={'positive':5,'refusal':34,'fault':13} and len(matrix['cases'])==len(cross['cases'])==52 and all(c['execution']=='not_run_design_only' for c in matrix['cases']+cross['cases']) and all(v==0 for v in matrix['actual_target_counts'].values()) and all(v==0 for v in cross['actual_target_counts'].values()),counts=counts)
check('controls','Exactly one independent external review condition',sum(c['applicability']=='independent_external_review_only' for c in cross['cases'])==1 and cross['counts']['future_primitive_or_mocked_implementation_controls']==51)
check('controls','Matrix byte identity remains independently frozen',sha((SNAP/PREFIX/'reviews/path/CONTROL-MATRIX.json').read_bytes())=='d52f64ffc28f7baf04e360f167fb56192cc6fb0baf6b36fd9f085907732a3196')
check('controls','Crosswalk identities and order exact',[c['id'] for c in matrix['cases']]==[c['id'] for c in cross['cases']] and len({c['id'] for c in cross['cases']})==52)
anchor_count=0
for m,x in zip(matrix['cases'],cross['cases']):
 check('crosswalk_case',m['id'],sha(json.dumps(m,sort_keys=True,separators=(',',':')).encode())==x['matrix_case_sha256'] and m['kind']==x['kind'] and m['expected']['boundary']==x['expected_boundary'] and m['expected']['code']==x['expected_code'] and m['expected']['process_counts']==x['expected_process_counts'])
 for anchor in x['candidate_anchors']:
  document=pjs(anchor['artifact']);ok=True
  try:
   for key in anchor['json_pointer'].lstrip('/').split('/'):
    key=key.replace('~1','/').replace('~0','~');document=document[int(key)] if isinstance(document,list) else document[key]
  except (KeyError,IndexError,ValueError,TypeError):ok=False
  check('crosswalk_anchor',m['id']+':'+anchor['json_pointer'],ok);anchor_count+=1
sources=pjs('SOURCE-BINDINGS.json');source_count=0
for rec in sources['sources']+sources['governing_instructions']:
 if rec.get('kind')=='verified_handoff_member':
  with zipfile.ZipFile(ROOT/'input/OntoKin_C271_P23_H0_Path_Blocker_Recommendation_Amendment_2026-11-23.zip') as z:data=z.read(rec['member'])
  name=rec['member']
 else:
  revision=rec.get('source_revision',rec.get('source_revision_as_supplied_by_director'));name=rec['repository_path'];data=git('show',revision+':'+name)
 good=len(data)==rec['size_bytes'] and sha(data)==rec['sha256'] and ('git_blob_sha1' not in rec or blob(data)==rec['git_blob_sha1'])
 check('source_binding',name,good);source_count+=1
copy_counts={}
for local_sub,canon_sub,recursive in [('design/path','',True),('reviews/path','reviews/path',False),('reviews/recovery','reviews/recovery',False)]:
 count=0
 paths=(ROOT/local_sub).rglob('*') if recursive else (ROOT/local_sub).glob('*')
 for src in sorted(paths):
  if not src.is_file():continue
  rel=src.relative_to(ROOT/local_sub).as_posix();target=SNAP/PREFIX/canon_sub/rel
  if target.is_file():check('worker_copy',local_sub+'/'+rel,src.read_bytes()==target.read_bytes());count+=1
 copy_counts[local_sub]=count
for name in ['P24-TRANSFER.attempt001.patch','P24-TRANSFER.attempt002.patch']:
 rec=pjs('reviews/recovery/'+name+'.json');decoded=base64.b64decode(rec['content'],validate=True)
 check('lossless_patch',name,len(decoded)==rec['bytes'] and sha(decoded)==rec['sha256'] and decoded==(OWN/name).read_bytes())
revision=pjs('REVISION-RECORD.json')
for attempt in revision['attempts']:
 for rec in attempt['files']:verify_binding('historical_candidate',rec,PREFIX+'/'+attempt['directory']+'/'+rec['path'])
provenance=pjs('PRE-ATTEMPT001-PROVENANCE.json');verify_binding('historical_candidate',provenance['artifact'],PREFIX+'/'+provenance['artifact']['path']);verify_binding('historical_candidate',provenance['source_successor'],PREFIX+'/'+provenance['source_successor']['path'])
recovered=(SNAP/PREFIX/provenance['artifact']['path']).read_text()
for edit in provenance['edits']:check('historical_candidate','Unique exact reversible edit',recovered.count(edit['old'])==1);recovered=recovered.replace(edit['old'],edit['new'],1)
check('historical_candidate','Recovered predecessor round trips exact successor',recovered.encode()==(SNAP/PREFIX/provenance['source_successor']['path']).read_bytes())
companions=pjs('history/pre-attempt001/COMPANION-PROVENANCE.json')
for rec in companions['files']:
 dest=PREFIX+'/history/pre-attempt001/'+rec['path'];verify_binding('historical_companion',rec,dest)
 check('historical_companion',rec['path']+' equals attempt001 bytes',(SNAP/dest).read_bytes()==(SNAP/PREFIX/'history/attempt001'/rec['path']).read_bytes())
log_bindings=[];documentary=[]
for label in ['candidate001','candidate002','core-final']:
 result=pjs('checks/'+label+'/RESULT.json')
 for cmd in result['checks']:
  for stream in ['stdout','stderr']:
   binding=cmd[stream];verify_binding('documentary_log',binding)
   log_bindings.append(binding)
   data=git('show',':'+binding['path']);check('documentary_log_index',binding['path'],sha(data)==binding['sha256'] and len(data)==binding['bytes'])
 for rec in result['tool_bindings']:
  data=git('show',START+':'+rec['path']);check('documentary_tool',label+':'+rec['path'],sha(data)==rec['sha256'] and len(data)==rec['bytes'])
 docs=json.loads((SNAP/PREFIX/('checks/'+label+'/documentation.stdout.log')).read_bytes());workflow=(SNAP/PREFIX/('checks/'+label+'/workflow.stdout.log')).read_text()
 documentary.append({'label':label,'checks':[{'name':c['name'],'result':c['result'],'exit_code':c['exit_code']} for c in result['checks']],'overall_passed':result['passed'],'workflow_tasks':int(re.search(r'passed \((\d+) tasks\)',workflow).group(1)),'documents':docs['links']['documents'],'local_links':docs['links']['local_links'],'anchors':docs['links']['anchors'],'sections':docs['sections_verified'],'sources':docs['sources_verified'],'failures':docs['failures']})
check('documentary','Candidate001 exact retained two-link failure',documentary[0]['overall_passed'] is False and len(documentary[0]['failures'])==2 and {f['target'] for f in documentary[0]['failures']}=={'SCHEMA.json','SOURCE-BINDINGS.json'})
check('documentary','Corrected and core-final results remain distinct',documentary[1]['overall_passed'] is True and documentary[2]['overall_passed'] is True and (documentary[1]['documents'],documentary[1]['local_links'])==(1614,6270) and (documentary[2]['documents'],documentary[2]['local_links'])==(1615,6280))
check('documentary','All final documentary commands passed',all(c['result']=='passed' and c['exit_code']==0 for c in documentary[2]['checks']) and documentary[2]['workflow_tasks']==12 and documentary[2]['sections']==233 and documentary[2]['sources']==29 and documentary[2]['failures']==[])
preserve=pjs('PRESERVATION-FINAL.json');check('documentary','Thirteen original preservation assertions retained',len(preserve['checks'])==13 and all(c['passed'] for c in preserve['checks']) and preserve['passed'] is True)
check('state','Only delivery remains within phase',phase['technical_phase_complete'] is True and phase['phase_complete'] is False and outcome['technical_phase_complete'] is True and outcome['phase_complete'] is False and task['session_phase']['technical_work_stopped'] is True and task['session_phase']['implementation_performed'] is False and outcome['next_action']==task['next_action']==cur['next_action']['summary'])
check('state','No implementation/H0/H1/product/installation/integration/parent claim',outcome['production_implementation_changed'] is False and outcome['test_implementation_changed'] is False and outcome['h0_accepted'] is False and outcome['h1_executed'] is False and outcome['product_tests_executed'] is False and outcome['full_routine_executed'] is False and outcome['host_installations']==0 and adopt['integration_approved'] is False and adopt['parent_complete'] is False)
check('state','Prior unknown operations remain exact',task['session_phase']['historical_unknown_operations']==btask['session_phase']['historical_unknown_operations']==outcome['historical_unknown_operations'] and phase['current_unknown_operations']==outcome['current_unknown_operations']==[])
check('state','Early save precedes phase and adoption',pjs('EARLY-RECOVERY-RECEIPT.json')['confirmed_at_utc']<phase['started_at_utc']<adopt['adopted_at_utc'])
report={'schema':'ontokin.c271.p24-core-source-review/1','reviewer':'/root/recovery_audit','reviewed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'base_revision':START,'observed_main':MAIN,'review_scope':'Independent canonical documentary/source-identity review; design safety acceptance attributed to exact /root/path_review record. No project helper imported, product target executed or repository/index changed.','verdict':'ACCEPTED_FOR_CONDITIONAL_CORE_PUBLICATION' if all(c['passed'] for c in checks) else 'UNRESOLVED_FINDINGS','unresolved_mandatory_findings':sum(not c['passed'] for c in checks),'reviewed_files':reviewed,'mechanical_documentary_comparisons':{'total':len(checks),'passed':sum(c['passed'] for c in checks),'by_group':dict(collections.Counter(c['group'] for c in checks))},'checks':checks,'observed_counts':{'canonical_files':len(reviewed),'source_identity_bindings':source_count,'frozen_controls':len(matrix['cases']),'control_kinds':counts,'crosswalk_case_hashes':52,'crosswalk_json_pointers':anchor_count,'future_primitive_or_mocked_controls':51,'external_review_only_controls':1,'executed_controls':0,'manual_design_review_groups':12,'design_reviewer_documentary_integrity_checks':101,'original_preservation_assertions':13,'documentary_streams':len(log_bindings),'empty_documentary_streams':sum(r['bytes']==0 for r in log_bindings),'worker_exact_copies':copy_counts,'historical_task_checks_retained':len(btask['checks']),'current_task_checks':len(task['checks'])},'documentary_results':documentary,'findings':[{'id':'CORE-01','severity':'mandatory_before_publication','observed':'All 18 documentary stdout/stderr .log paths were missing from the Git index although their RESULT.json bindings were staged. The initial 99-file workspace snapshot therefore had 81 indexed files.','status':'resolved','correction':'Director explicitly staged exact original streams without rerunning commands or changing ignore rules. This review verifies all 18 size/hash bindings and exact index bytes, including twelve empty streams. SESSION-INCIDENTS appended P24-DOC-002.','paths':[r['path'] for r in log_bindings]}],'read_coverage':{'complete_current_text':['ADOPTION.json','OUTCOME.json','PHASE.json','DECISION-CANDIDATE.md','SCHEMA.json','SOURCE-BINDINGS.json','CANDIDATE-MANIFEST.json','REVISION-RECORD.json','PRE-ATTEMPT001-PROVENANCE.json','history/pre-attempt001/COMPANION-PROVENANCE.json','PRESERVATION-FINAL.json','SESSION-INCIDENTS.json','EVIDENCE-TABLE.md','EXTERNAL-REFERENCES.json','LEARNING.json','reviews/path/REVIEW-FINAL.json','checks/core-final/RESULT.json','all three documentation stdout logs and workflow stdout logs'],'retained_bytes_reused':'Prior full branch records and earlier independent recovery reports were already reviewed; exact old prefixes/objects and copied report bytes are compared rather than semantically reread. Frozen author history and reviewer matrices/crosswalks receive identity, count, pointer and preservation checks; design safety review is not duplicated.','state_changes':'All changed current task/CURRENT fields and complete appended requirement/plan/session text read; unchanged history equality checked against START.'},'limitations':['Core publication/readback, final ZIP verification/save and terminal delivery are still pending; no remote publication or delivery acceptance claimed.','Final staged whitespace after adding this report and newly staged logs remains Director-owned. Earlier passed whitespace applies to its recorded index snapshot.','Candidate002 1614/6270 and core-final 1615/6280 counts describe their actual distinct observations; neither is recast as product qualification.','Current no-execution claims are consistent with source preservation and exact worker evidence; this review does not reconstruct globally unknown historical process state.','The earlier 20148-byte recovered draft has no independent contemporaneous digest. Reversible edits and successor equality support its recorded reconstruction; navigation companions are later exact attempt001 copies, not a claim of an observed earlier snapshot.'],'review_incidents':[{'kind':'exploratory_stream_parse_failure','description':'A read-only exploratory summary attempted JSON parsing of plain-text workflow.stdout.log and raised JSONDecodeError. No check result or source changed. The actual text and JSON documentation streams were then read and handled according to their formats.'}],'snapshot_incident_correction':{'before_sha256':sha(old_incident),'reviewed_sha256':sha(new_incident),'preserved_after_path':str((correction/'SESSION-INCIDENTS.json').relative_to(ROOT))},'next_action':'Director may include this review, run final staged whitespace, then conditionally publish/read back exact core and complete verified final handoff only. No second technical phase.'}
path=OWN/'CORE-SOURCE-REVIEW.json'
with path.open('x') as f:json.dump(report,f,indent=2);f.write('\n')
print(json.dumps({'path':str(path),'bytes':path.stat().st_size,'sha256':sha(path.read_bytes()),'verdict':report['verdict'],'comparisons':report['mechanical_documentary_comparisons'],'counts':report['observed_counts'],'failed_checks':[c for c in checks if not c['passed']]},indent=2))
