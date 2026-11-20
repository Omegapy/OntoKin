#!/usr/bin/env python3
"""Audit retained fresh actual-main results without rerunning tests."""
import hashlib,json,os,platform,re,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path('/workspace/scratch/a2bb67238030');REPO=ROOT/'OntoKin';OUT=ROOT/'audit/review';E=ROOT/'evidence/actual-main'
MAIN='4d27756f1c503b430dd85219235778a1f78ef101';CAND='29e98cab1774629171152be3be68c14e39bb9c0e';LEASE='f2d503423c5a790df79d28d61679d146a4c28c32';TREE='3ec9ba3caa18f560a751044d1d5bbd2f036383a2'
checks=[];commands=[];identities={};cache={}
def ident(b):return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def check(n,v,**d):checks.append({'name':n,'passed':bool(v),**d})
def git(*args):
 cmd=['git','-C',str(REPO),*args];p=subprocess.run(cmd,capture_output=True,env=dict(os.environ,GIT_OPTIONAL_LOCKS='0'));commands.append({'argv':cmd,'exit_code':p.returncode,'stdout_identity':ident(p.stdout)});p.check_returncode();return p.stdout
def blob(p):
 if p not in cache:cache[p]=git('show',MAIN+':'+p);identities[MAIN+':'+p]=ident(cache[p])
 return cache[p]
def read(p):
 b=Path(p).read_bytes();identities[str(p)]=ident(b);return json.loads(b)
def verify(n,row,base=None,repo=False):
 p=Path(row['path'])
 if repo:
  path=p.relative_to(REPO).as_posix() if p.is_absolute() else p.as_posix();b=blob(path)
 else:
  p=p if p.is_absolute() else base/p;b=p.read_bytes();identities[str(p)]=ident(b)
 check(n,ident(b)=={'bytes':row['bytes'],'sha256':row['sha256'].removeprefix('sha256:')},recorded_path=row['path'])
 return b
post=read(ROOT/'operations/POST-MERGE.json')
def payload(name):return json.loads(post[name]['structuredContent']['content'])
main_ref,pr,branches,commit=(payload(n) for n in ['main_readback','pull_request','branches','git_commit'])
check('actual_main_ref',main_ref['ref']=='refs/heads/main' and main_ref['object']['sha']==MAIN)
check('approved_tree_exact_on_main',git('rev-parse',MAIN+'^{tree}').decode().strip()==TREE and git('diff','--name-status',CAND,MAIN)==b'')
check('two_parent_merge',git('show','-s','--format=%P',MAIN).decode().split()==[LEASE,CAND])
check('remote_tree_parents_match_authentic_git',commit['sha']==MAIN and commit['tree']['sha']==TREE and [p['sha'] for p in commit['parents']]==[LEASE,CAND])
check('conditional_nonforce_merge_intent',post['merge_intent']['expected_main']==LEASE and post['merge_intent']['candidate']==CAND and post['merge_intent']['reviewed_tree']==TREE and post['merge_intent']['force'] is False)
check('merge_update_observed_success',post['merge_commit']['structuredContent']['sha']==MAIN and post['merge_update']['structuredContent']['success'] is True)
check('PR272_merged_closed_exact',pr['number']==272 and pr['state']=='closed' and pr['merged'] is True and pr['merge_commit_sha']==MAIN and pr['head']['sha']==CAND)
check('branch_automatic_absence_observed',len(branches)==1 and branches[0]['name']=='main' and branches[0]['commit']['sha']==MAIN)
check('retained_candidate_ancestry',subprocess.run(['git','-C',str(REPO),'merge-base','--is-ancestor',CAND,MAIN],capture_output=True).returncode==0)
h=read(E/'h16/RESULTS.json');a=read(E/'affected-cohort/CHECKS.json');d=read(E/'distinctions/CHECKS.json')
check('h16_exact_main',h['source_revision']==MAIN and h['source_tree']==TREE)
check('h16_45_assertions_5_cases',h['passed'] and not h['failed_assertions'] and len(h['cases'])==5 and sum(len(c['assertions']) for c in h['cases'])==45 and all(c['passed'] and all(c['assertions'].values()) for c in h['cases']))
check('h16_inputs_clean_stable',h['inputs']==h['inputs_after'] and h['inputs_unchanged'] and h['source_revision_unchanged'] and h['tracked_clean_after'] and not h['tracked_dirty_status'])
for i,row in enumerate(h['inputs']):verify('h16_input:'+str(i),row,repo=True)
verify('h16_frozen_oracle',h['frozen_expectation'],repo=True)
check('original_oracle_unchanged',h['frozen_expectation']['sha256']=='aa73df1e9ffb4d76bc589a7239f454be28e4cd6ae4ee523b208dbf66860ef4a7')
hashes={'main.ok':'f7e22c5bb8c42dadc475b970d16c1ce0503dc2333ed359387d85e5e6638b584d','hinges.ok':'dd5b49760121c0fe8ee5e707fe60e1d269be954896951f991887f195b0686e97'};sizes={'main.ok':1708,'hinges.ok':1998}
for c in h['cases']:
 if 'response' in c:
  v=json.loads(verify('h16_response:'+c['label'],c['response'],E/'h16'))
  check('original_positive:'+c['label'],v.get('hingeCount')==8 and (c['label']!='original-source' or v.get('siteCount')==16))
 else:
  chain=c['cause_chain'];depth={'siteref-source':1,'siteref-binding':2,'siteref-comparison':3}[c['label']]
  check('exact_refusal_propagation:'+c['label'],len(chain)==depth and all(x['code']=='UNSUPPORTED_SOURCE_FORM' and x['detail']=='declared SiteRef parameter endpoint is unsupported' and x['sourceHashes']==hashes and x['sourceBytes']==sizes for x in chain))
  forbidden={'records','hinges','sites','objects','hingeCount','siteCount','objectCount','qualified','inputBindingVerified','hingeComparisonVerified','hingeSetAgreementVerified','endpointAgreementVerified'}
  check('no_partial_qualification:'+c['label'],all(not forbidden.intersection(x) for x in chain))
  check('originating_source_site:'+c['label'],chain[-1]['traceback'][-1]['function']=='site')
  if depth>1:check('artifact_retained:'+c['label'],all(x.get('artifactSha256')=='d009d9dba6c69bb8e8e6decdfa9d7e1e92f819e3b59013d481cd30101c973534' and x.get('artifactBytes')==185276 for x in chain[:-1]))
check('affected_exact_main_clean',all(a[k]['commit']==MAIN and a[k]['tree']==TREE and not a[k]['tracked_dirty_status'] and not a[k]['all_dirty_status'] for k in ['source_before','source_after']))
check('affected_complete_282_12',a['complete'] and a['passed'] and a['planned_check_count']==a['completed_check_count']==len(a['checks'])==12 and a['total_methods']==a['expected_total_methods']==282 and not a['remaining_checks'])
check('affected_all_inputs_stable',a['input_files_before']==a['input_files_after'] and a['input_identity_unchanged'])
for i,row in enumerate(a['input_files_before']):verify('affected_input:'+str(i),row,repo=True)
for i,row in enumerate(a['output_files']):verify('affected_output:'+str(i),row,E/'affected-cohort')
verify('affected_runner',a['runner'],repo=True)
methods={}
for c in a['checks']:
 check('affected_group:'+c['name'],c['result']=='passed' and c['exit_code']==0 and c['failure'] is None and all(c['assertions'].values()))
 log=verify('affected_log:'+c['name'],c['log'],E/'affected-cohort').decode()
 if c['expected_methods'] is not None:
  methods[c['name']]=c['expected_methods']
  check('method_log_complete:'+c['name'],re.findall(r'^Ran (\d+) tests? in ',log,re.M)==[str(c['expected_methods'])] and re.search(r'^OK\s*$',log,re.M) is not None and re.search(r'^FAILED\b|^ERROR:|^FAIL:|\.\.\. (?:skipped|expected failure|unexpected success)',log,re.M) is None)
 if c['name']=='c253-corpus':check('14_corpus_bindings',c['details']['passed'] and c['details']['boundFiles']==14)
 if c['name']=='workflow':check('fresh_main_workflow',json.loads(log)['passed'] is True and json.loads(log)['errors']==[])
 if c['name']=='documentation':check('fresh_main_documentation',json.loads(log)['status']=='passed' and json.loads(log)['failures']==[])
 if 'results_identity' in c['details']:
  v=json.loads(verify('retained_results:'+c['name'],c['details']['results_identity'],E/'affected-cohort'))
  check('retained_outcomes:'+c['name'],v['passed'] and v['testMethods']==c['expected_methods'] and not any(v[k] for k in ['failures','errors','skipped']) and len(v['cases'])==v['apiCalls'])
check('distinctions_exact_main_clean',d['source_revision']==d['source_revision_after']==MAIN and d['source_tree']==TREE and not d['tracked_dirty_before'] and not d['tracked_dirty_after'])
check('distinctions_eight_passed_stable',d['passed'] and d['methods']==8 and d['exit_code']==0 and d['inputs_before']==d['inputs_after'])
for i,row in enumerate(d['inputs_before']):verify('distinction_input:'+str(i),row,repo=True)
verify('distinction_runner',d['runner'],repo=True)
log=verify('distinction_log',d['log'],E/'distinctions').decode()
check('distinction_log_eight_tests',len(re.findall(r'^test_.* \.\.\. ok$',log,re.M))==8 and 'Ran 8 tests in ' in log and re.search(r'^OK\s*$',log,re.M) is not None)
binary=ident(Path(sys.executable).resolve().read_bytes())
check('same_interpreter_binary',all({'bytes':v['bytes'],'sha256':v['sha256']}==binary for v in [h['environment']['executable'],a['environment']['resolved_executable'],d['environment']['executable']]))
check('matching_execution_environment',all(v['python']==sys.version and v['platform']==platform.platform() for v in [h['environment'],a['environment'],d['environment']]))
check('matching_runtime_bundle',a['environment']['runtime_bundle_version']==os.environ.get('CODEX_PRIMARY_RUNTIME_BUNDLE_VERSION'))
for name in ['actual-main-cohort-driver.log','actual-main-h16-driver.log','actual-main-distinctions-driver.log']:
 p=ROOT/'evidence'/name;identities[str(p)]=ident(p.read_bytes())
failed=[c for c in checks if not c['passed']]
report={'schema':'ontokin.c270.actual-main-independent-review/1','reviewer':'/root/candidate_review','reviewed_at_utc':datetime.now(timezone.utc).isoformat(),'main':MAIN,'tree':TREE,'reviewed_candidate':CAND,'parents':[LEASE,CAND],'verdict':'approved_actual_main_R01_R04_evidence' if not failed else 'blocked','passed':not failed,'mandatory_findings':failed,'check_count':len(checks),'checks':checks,'method_inventory':methods,'source_artifact_identities':identities,'commands':commands,'audit_command':[sys.executable,*sys.argv],'audit_script':ident(Path(__file__).read_bytes()),'environment':{'python':sys.version,'platform':platform.platform(),'interpreter':binary,'runtime_bundle_version':os.environ.get('CODEX_PRIMARY_RUNTIME_BUNDLE_VERSION')},'execution_evidence':{'h16':{'report':str(E/'h16/RESULTS.json'),'cases':5,'assertions':45},'affected':{'report':str(E/'affected-cohort/CHECKS.json'),'groups':12,'methods':282,'corpus_bindings':14},'distinctions':{'report':str(E/'distinctions/CHECKS.json'),'methods':8,'variants':16,'api_calls':48}},'branch_disposition':'automatic absence observed after exact reviewed merge; reviewed history retained through main ancestry','remaining_gate':'R05 verified final handoff, confirmed save, separate receipt and truthful closure; publish current review/check evidence durably before claiming all acceptance complete','limits':['Reviewer inspected evidence and source identities; no behavioral execution by reviewer.','Actual-main executions are new scope-relevant checks and do not complete the historical interrupted broad driver.','No broad-suite pass, whole-product qualification, general source validity, native/model trial, compatibility matrix or comparative advantage claim.']}
(OUT/'ACTUAL-MAIN-REVIEW.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'main':MAIN,'checks':len(checks),'passed':not failed,'failed':failed}))
raise SystemExit(1 if failed else 0)
