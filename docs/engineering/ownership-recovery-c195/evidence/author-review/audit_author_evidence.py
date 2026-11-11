#!/usr/bin/env python3
"""Read-only audit of C195 author receipts; never invokes native or author tools."""
import hashlib, importlib.util, json, math, stat, subprocess
from datetime import datetime, timezone
from pathlib import Path
B=Path('/workspace/scratch/3cb1527378cd'); REPO=B/'repo'; HERE=REPO/'docs/engineering/ownership-recovery-c195'
OUT=B/'c195-prep/AUTHOR-EVIDENCE-AUDIT.json'
spec=importlib.util.spec_from_file_location('c195_audit_verifier', HERE/'verify_deliveries.py'); v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
count=0

def check(condition, message):
 global count
 count+=1
 if not condition: raise AssertionError(message)
def js(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dt(t):return datetime.fromisoformat(t)
def git(repo,*args):return subprocess.check_output(['git',*args],cwd=repo,text=True).strip()
def file_record(p):return {'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':sha(p)}
def check_record(p,record,mode=False):
 check(p.is_file(), 'missing '+str(p))
 check(p.stat().st_size==record['bytes'] and sha(p)==record['sha256'],'file identity '+str(p))
 if mode:check(oct(stat.S_IMODE(p.stat().st_mode))==record['mode'],'file mode '+str(p))
def check_io(record):
 for key in ['stdout','stderr']:
  item=record.get(key)
  if isinstance(item,dict):check_record(Path(item['path']),item)

manifest=HERE/'evidence/DELIVERIES.json';rows=js(manifest);v.validate_rows(rows)
check(sha(HERE/'verify_deliveries.py')=='d3eaa6a4e7090563c353d5dfd72be1b4cc8129b13f140617757fa75ea16dd610','reviewed verifier identity')
check(sha(HERE/'INPUTS.json')=='e6b7cf1da886d61a81a1795f33871d8fd780cd3e8c83d0d481109ee30da34411','input identity')
freeze_check=v.public_inputs(REPO);bases=js(HERE/'BASELINES.json')
dispatch=js(HERE/'evidence/AUTHOR-DISPATCH.json');start=dt(dispatch['dispatched_utc']);deadline=dt(dispatch['deadline_utc'])
check((deadline-start).total_seconds()==1200,'dispatch allowance')
check(dispatch['fork_turns']=='none' and dispatch['two_fresh_default_authors'] is True and dispatch['model_override'] is None and dispatch['reasoning_override'] is None,'fresh default dispatch declaration')
check(dispatch['freeze_sha256']==sha(HERE/'FREEZE.json'),'dispatch freeze identity')
commits={'ok':'586babe1f09e153518e80c286e96ee1f46f25377','python':'57e6407d8bd7279d7c74168f7f492379f2fe600a'}
results={}
for route in ['ok','python']:
 root=B/'c195-runs'/route;repo=B/'c195-authors'/route;d=repo/'docs/engineering/ownership-recovery-c195/authors'/route
 ext='ok' if route=='ok' else 'py';base=bases['routes'][route];sub=js(d/'SUBMISSION.json');acct=js(d/'ACCOUNTING.json')
 check(js(root/'DISPATCH.json')==dispatch,route+' shared dispatch')
 freeze=v.public_inputs(repo)
 check(git(repo,'rev-parse','HEAD')==commits[route],route+' exact commit')
 check(git(repo,'status','--porcelain')=='',route+' clean worktree')
 changed=git(repo,'diff','--name-only',dispatch['local_source_revision'],'HEAD').splitlines()
 check(bool(changed) and all(x.startswith('docs/engineering/ownership-recovery-c195/authors/'+route+'/') for x in changed),route+' own dossier only')
 for p in sorted(d.rglob('*')):
  if p.is_file():
   blob=subprocess.check_output(['git','show','HEAD:'+str(p.relative_to(repo))],cwd=repo)
   check(blob==p.read_bytes(),'committed bytes '+str(p))
 check((d/'SUBMISSION.sha256').read_text().split()[0]==sha(d/'SUBMISSION.json'),route+' sealed manifest hash')
 check(sub['submission_number']==acct['formal_submissions']==1,route+' one submission')
 for name,record in sub['author_files'].items():check_record(d/name,record)
 end=dt(sub['submitted_utc']);declared_wall=(end-start).total_seconds()
 check(acct['started_utc']==dispatch['dispatched_utc'],route+' measured from dispatch')
 check(math.isclose(declared_wall,acct['elapsed_wall_seconds' if route=='ok' else 'wall_seconds_to_formal_seal'],abs_tol=1e-6),route+' reported elapsed')
 journal=[json.loads(s) for s in (root/'commands.jsonl').read_text().splitlines()] if route=='ok' else js(root/'COMMANDS.json')['execution_records']
 for record in journal:check_io(record)
 commit_record=next(x for x in journal if x.get('argv',[])[:2]==['git','commit']) if route=='ok' else js(root/'logs/git-author-commit.json')
 check(commit_record['returncode']==0,route+' successful sealed dossier commit')
 complete=dt(commit_record['finished_utc']);wall=(complete-start).total_seconds()
 seal_mtime=datetime.fromtimestamp((d/'SUBMISSION.sha256').stat().st_mtime,timezone.utc)
 check(start<=end<=seal_mtime<=complete<=deadline,route+' seal/commit bounded by deadline')
 check(0<=wall<=1200,route+' conservative duration')
 actual_commit_time=dt(git(repo,'show','-s','--format=%cI','HEAD'))
 check(abs((actual_commit_time-complete).total_seconds())<1,route+' Git timestamp agrees with raw command')
 fixed=(HERE/'fixtures'/('baseline.'+ext)).read_bytes();candidate=(HERE/'fixtures'/('candidate.'+ext)).read_bytes();repaired=(d/('repaired.'+ext)).read_bytes()
 check((d/('accepted-source.'+ext)).read_bytes()==fixed==(root/('accepted-source.'+ext)).read_bytes(),route+' accepted source preserved')
 check((d/('candidate.'+ext)).read_bytes()==candidate,route+' malformed source preserved')
 old=(b'collider left_shoe_box @ "contact.left_shoe" {\n        part = "left_shoe";\n        owner = "body.right";' if route=='ok' else b"                                     'owner': 'body.right',\n                                     'part': 'left_shoe',")
 check(candidate.count(old)==1 and candidate.replace(old,old.replace(b'body.right',b'body.left'))==repaired,route+' one localized owner repair')
 check(acct['source_repairs']==1 and acct['incorrect_repairs']==0,route+' repair accounting')
 check(sha(root/'C194-ACCEPTANCE.json')==bases['acceptance_sha256'],route+' original acceptance record')
 acceptance=js(root/'C194-ACCEPTANCE.json');check(acceptance['accepted'] is True,route+' accepted original output')
 if route=='ok':
  names=['preservation-before-negative.json','preservation-immediately-after-negative.json','preservation-at-final-submission.json']
  negative=js(root/'negative-result.json');negative_path=root/'negative-result.json';negcmd=js(root/'negative-01/command.json')
  check(json.loads((root/'negative-01/stdout.txt').read_text())==negative,'OK raw result/stdout identical')
  diagnostic=negative['diagnostics'][0];span=diagnostic['span']
  check(negative['successful'] is False and negative['committed'] is False,'OK actual failure')
  check(diagnostic['code']=='C193_E_OWNERSHIP' and diagnostic['phase']=='validate' and diagnostic['message']=='Collider is assigned to the wrong mass owner','OK actual diagnostic')
  check(candidate[span['start_byte']:span['end_byte']]==b'"body.right"' and span['source_sha256']==sha(d/'candidate.ok'),'OK actual diagnostic byte span')
  check((span['start_byte'],span['end_byte'],span['start_line'],span['end_line'],span['start_column'],span['end_column'])==(2400,2412,81,81,17,29),'OK span exact')
  check(negative['accepted_revision']==negative['previous_revision']==base['source_sha256'],'OK accepted revision unchanged')
  check(negative['levels']=={'represented':True,'constructed':False,'evaluated':False,'exported':False,'destination_validated':False},'OK rejection level')
  check(negative['artifact_directory'] is None and negative['artifacts']=={} and negative['runtime']['executable_sha256'] is None,'OK no native artifact/runtime')
  failrel='accepted-run/store/attempts/'+negative['attempt_id']+'/result.json'
  check(js(root/failrel)==negative,'OK only new transaction failure receipt')
  expected_add={failrel};stamp='captured_utc'
  diagnostic_summary={'code':diagnostic['code'],'phase':diagnostic['phase'],'message':diagnostic['message'],'span':span}
 else:
  names=['baseline-before-negative.json','baseline-after-negative.json','baseline-at-submission.json']
  negative_path=root/'negative-01/build-receipt.json';negative=js(negative_path);negcmd=js(root/'logs/negative-01.json');check_io(negcmd)
  check(json.loads(Path(negcmd['stdout']['path']).read_text())==negative,'Python actual receipt/stdout identical')
  check(negative['successful'] is False and negative['product_transaction_claimed'] is False,'Python direct static rejection')
  check(negative['error']=='ValueError: $.colliders.contact.left_shoe.owner: differs from frozen constant','Python actual diagnostic')
  check(set(v.inventory(root/'negative-01'))=={'build-receipt.json','manifest.json'},'Python negative only rejection receipt/manifest')
  first=js(root/'negative-verification.json');supplement=js(root/'negative-verification-complete.json')
  check(first['receipt']==supplement['receipt']==negative and first['scheduled_native_substeps'] is None and supplement['scheduled_native_substeps']==0,'Python retained reporting correction and unchanged receipt')
  expected_add=set();stamp='recorded_utc'
  diagnostic_summary={'message':negative['error'],'schema_field':'$.colliders.contact.left_shoe.owner'}
 check(negcmd['returncode']==1,route+' expected rejection exit')
 negcost=negative['cost'];check(negcost['operation_components'].get('scheduled_native_substeps',0)==0,route+' negative native substeps zero')
 for key in ['native_elapsed_ms','native_log_bytes','native_result_bytes','staged_output_bytes']:check(negcost[key]==0,route+' negative '+key+' zero')
 snapshots=[js(root/n) for n in names];before,after,final=snapshots
 expected={'accepted-run/'+n:r for n,r in base['run_files'].items()}
 expected['accepted-source.'+ext]={'bytes':len(fixed),'sha256':base['source_sha256']}
 expected['C194-ACCEPTANCE.json']={'bytes':(root/'C194-ACCEPTANCE.json').stat().st_size,'sha256':bases['acceptance_sha256']}
 before_nomode={n:{k:val for k,val in rec.items() if k!='mode'} for n,rec in before['files'].items()}
 check(before_nomode==expected,route+' exact original C194 baseline closure')
 check(set(after['files'])-set(before['files'])==set(final['files'])-set(before['files'])==expected_add,route+' only permitted additive rejection receipt')
 check(after['files']==final['files'],route+' after rejection through final submission unchanged')
 for name,record in before['files'].items():
  check(after['files'].get(name)==final['files'].get(name)==record,route+' retained file snapshot '+name)
  check_record(root/name,record,mode=True)
 check(dt(before[stamp])<=dt(negcmd['started_utc'])<=dt(negcmd['finished_utc'])<=dt(after[stamp])<=dt(final[stamp])<=seal_mtime,route+' preserved snapshots bracket reject and complete seal')
 if route=='ok':
  check(before['state']==after['state']==final['state']==base['accepted_state']==js(root/'accepted-run/store/state.json'),'OK preserved state pointer')
  check(set(v.inventory(root/'accepted-run'))==set(base['run_files'])|{failrel.removeprefix('accepted-run/')},'OK accepted run only failure receipt added')
 else:check(v.inventory(root/'accepted-run')==base['run_files'],'Python accepted file run unchanged')
 positive_wrappers=[x for x in journal if any(str(a).endswith('guide-repair-c193/native/build.py') for a in x.get('argv',[]))]
 check(len(positive_wrappers)==2 and all(x['returncode']==0 for x in positive_wrappers),route+' exactly two successful positive wrapper calls')
 new_native=sorted(str(p.relative_to(root)) for p in root.rglob('native-command.json') if 'accepted-run' not in p.relative_to(root).parts)
 new_scenes=sorted(str(p.relative_to(root)) for p in root.rglob('scene.blend') if 'accepted-run' not in p.relative_to(root).parts)
 new_deliveries=sorted(str(p.relative_to(root)) for p in root.rglob('delivery.json') if 'accepted-run' not in p.relative_to(root).parts)
 check(len(new_native)==len(new_scenes)==len(new_deliveries)==2,route+' exactly two new native products and deliveries')
 check(all(n.split('/')[0] in ['repaired-01','baseline-regenerated-01'] for n in new_native+new_scenes+new_deliveries),route+' no unaccounted native output directory')
 check(len(list(d.glob('SUBMISSION*.json')))==1,route+' single formal submission file')
 submitted={};build_details=[];total_ops=negcost['operations_consumed'];declared_variants=list(sub['variants'].values()) if route=='ok' else sub['runs']
 for row in [r for r in rows if r['route']==route]:
  source=Path(row['source']);run=Path(row['run']);source_check=v.source_and_baseline(row)
  delivery=js(run/'delivery.json');command=js(run/'command.json')
  check(delivery==command and delivery['successful'] is True and delivery['returncode']==0,route+' real successful delivery '+row['case'])
  check(delivery['route']==route and delivery['source']==str(source) and delivery['source_sha256']==sha(source),route+' delivery source identity '+row['case'])
  check(delivery['source_unchanged_during_build'] is True and (run/('submitted-source.'+ext)).read_bytes()==source.read_bytes(),route+' submitted source retained '+row['case'])
  check(start.timestamp()<=delivery['started_unix_s']<=delivery['finished_unix_s']<=end.timestamp(),route+' positive build before seal '+row['case'])
  cost=delivery['cost'];check(cost['requested_operations']==cost['host_operations_ceiling']==1000000 and cost['requested_elapsed_ms']==cost['host_elapsed_ms_ceiling']==80000,route+' exact build limits '+row['case'])
  check(cost['operations_consumed']<=1000000 and cost['elapsed_ms']<=80000 and cost['operation_components']['scheduled_native_substeps']==4800,route+' build consumed within limits '+row['case'])
  check(cost['operations_consumed']==sum(cost['operation_components'].values()),route+' charges add correctly '+row['case'])
  total_ops+=cost['operations_consumed'];artifact=v.setup.retained_artifact(run,route,delivery)
  check((artifact/('source.'+ext)).read_bytes()==source.read_bytes(),route+' artifact source retained '+row['case'])
  native=js(artifact/'native-command.json');check(native['returncode']==0 and native['stop_reason'] is None and native['trusted_test_hooks']==[],route+' genuine clean native command '+row['case'])
  check('--reopen' not in native['argv'] and '--factory-startup' in native['argv'],route+' construction not reopen '+row['case'])
  check(delivery['started_unix_s']<=native['started_unix_ns']/1e9<=native['finished_unix_ns']/1e9<=delivery['finished_unix_s'],route+' nested native time '+row['case'])
  artmanifest=js(artifact/'manifest.json')
  for name,record in artmanifest['files'].items():check_record(artifact/name,record)
  variant=next(x for x in declared_variants if x['case']==row['case'])
  check(variant['run']==str(run) and variant['source_sha256']==sha(source) and variant['delivery_sha256']==sha(run/'delivery.json'),route+' sealed submission binds actual manifest row '+row['case'])
  if row['case']=='H':
   previous=Path(row['preserve_from'])
   for name in v.setup.EQUAL_FILES:check((artifact/name).read_bytes()==(previous/name).read_bytes(),route+' H byte-identical regeneration '+name)
  submitted[row['case']]={'source_sha256':sha(source),'run_inventory_sha256':v.inventory_sha256(v.inventory(run))}
  build_details.append({'case':row['case'],'source_sha256':sha(source),'delivery_sha256':sha(run/'delivery.json'),'artifact':str(artifact),'native_command_sha256':sha(artifact/'native-command.json'),'operations':cost['operations_consumed'],'scheduled_native_substeps':4800,'elapsed_s':delivery['elapsed_s'],'source_and_baseline':source_check})
 expected_total=acct['charged_operations_total' if route=='ok' else 'harness_operations_total'];check(total_ops==expected_total,route+' total includes negative and both builds')
 check(acct['human_interventions' if route=='ok' else 'human_interventions_after_dispatch']==0,route+' no human repair intervention recorded')
 if route=='ok':
  check(acct['author_delegations']==acct['coordinator_repair_corrections']==0,'OK author independence accounting')
  check(acct['native_constructions']=={'baseline_regeneration':1,'failed':0,'receiving_native_checks':0,'reopens':0,'repaired':1,'retries':0},'OK native counts')
  check(acct['expected_static_rejections']==1 and acct['unexpected_inspection_command_failures']==1,'OK all failures retained')
  failures=[x for x in acct['commands']['initial_read_only'] if x['returncode']!=0]
  check(len(failures)==1 and failures[0]['returncode']==2 and '2>/dev/null' in failures[0]['shell'],'OK missing-glob read failure retained')
  unexpected={'count':1,'kind':'Read-only rg inspection with an unmatched glob exited 2; stderr was suppressed and original raw error text is unavailable. Retrospective command accounting retained.'}
  corrections=[]
 else:
  check(acct['author_settings']['delegations']==0 and acct['native_reopens']==acct['receiving_jobs']==0,'Python no delegated or uncharged native work recorded')
  check(acct['native_constructions']=={'automatic_retries':0,'failed':0,'preserved_375_mm':1,'repaired_365_mm':1,'total':2},'Python native counts')
  check(acct['expected_command_failures']==1 and acct['unexpected_command_failures']==0,'Python all failures retained')
  unexpected={'count':0};corrections=[{'kind':'Accounting extraction correction','original':'negative-verification.json','supplement':'negative-verification-complete.json','finding':'Original summary recorded null using nonexistent charges/categories; supplement reads operation_components. Both retain the identical actual zero-native rejection receipt.'}]
 evidence_paths=set(p.resolve() for p in root.rglob('*') if p.is_file())|set(p.resolve() for p in d.rglob('*') if p.is_file())
 evidence_paths|={HERE/n for n in ['INPUTS.json','FREEZE.json','PROTOCOL.md','BASELINES.json','verify_deliveries.py','evidence/DELIVERIES.json','evidence/AUTHOR-DISPATCH.json']}
 check(all(p.is_relative_to(root) or p.is_relative_to(d) or p.is_relative_to(HERE) for p in evidence_paths),route+' archiveable evidence path scope')
 evidence=[file_record(p) for p in sorted(evidence_paths)]
 results[route]={
  'passed':True,'rejection_observed':True,'diagnostic_accurate':True,
  'baseline_preserved_after_rejection':True,'baseline_preserved_at_submission':True,
  'negative_native_substeps':0,'negative_native_outputs':False,'wall_seconds':wall,
  'formal_submissions':1,'repaired_native_builds':1,'baseline_native_builds':1,
  'submissions':submitted,'evidence':evidence,'submission_commit':commits[route],
  'submission_manifest_sha256':sha(d/'SUBMISSION.json'),'frozen_inputs':freeze,
  'timing':{'dispatched_utc':dispatch['dispatched_utc'],'reported_submitted_utc':sub['submitted_utc'],
    'reported_wall_seconds':declared_wall,'observed_checksum_mtime_utc':seal_mtime.isoformat(),
    'checksum_mtime_ns':(d/'SUBMISSION.sha256').stat().st_mtime_ns,
    'conservative_completed_utc':complete.isoformat(),'conservative_wall_seconds':wall,
    'basis':'The original submitted_utc marks start of sealing. Deadline acceptance uses the later successful Git commit command completion, which binds the exact sealed dossier. Local checksum mtime corroborates sealing; it is not assumed to survive archival.',
    'raw_commit_command_record':str(root/('commands.jsonl' if route=='ok' else 'logs/git-author-commit.json'))},
  'negative':{'diagnostic':diagnostic_summary,'receipt_sha256':sha(negative_path),'cost':negcost,'returncode':negcmd['returncode']},
  'preservation':{'baseline_files':len(before['files']),'baseline_bytes':before['total_bytes'],
    'before':str(root/names[0]),'after_rejection':str(root/names[1]),'at_final_seal':str(root/names[2]),
    'permitted_added_files':sorted(expected_add),'all_existing_mode_size_hash_records_unchanged':True,
    'current_baseline_still_matches':True,'original_acceptance_sha256':bases['acceptance_sha256'],
    'method':'Copied accepted transaction store remains on 375 mm; only failure attempt receipt was added.' if route=='ok' else 'Ordinary file staging; accepted source/output closure remains byte-identical. No product transaction claim.'},
  'repair':{'candidate_to_repaired':'Only contact.left_shoe owner changes body.right to body.left.',
    'accepted_to_repaired':'Only left_stop X changes 375 to 365 mm.', 'source_repairs':1,'incorrect_repairs':0,
    'prepared_positive_substitution':'No evidence of substitution; retained repair script reads candidate and original baseline and makes only the owner replacement.'},
  'native_census':{'positive_wrapper_calls':2,'new_native_commands':new_native,'new_scenes':new_scenes,
    'new_deliveries':new_deliveries,'failed_positive_builds':0,'retries':0,'author_reopens':0,'author_receiving_jobs':0},
  'builds':build_details,'harness_operations_total_including_rejection':total_ops,
  'expected_negative_failures':1,'unexpected_command_failures':unexpected,'retained_reporting_corrections':corrections,
  'diagnosis_review':'Actual diagnosis identifies the left shoe following the left carriage while assigned to body.right; both delivered repairs restore body.left and retain the intended 365 mm stop. Public supplied-defect limits are stated.',
  'caveats':['Initial read-only commands include retrospective accounting; original local stdout is not available for every such inspection.',
    'Native census covers the provided author output trees and retained command records in a shared environment; it is not a proof of whole-host isolation.',
    'Provider token/billed-cost telemetry is unavailable. This single supplied recovery per route establishes neither blind diagnostic ability nor comparative language reliability/cost.']}
report={'schema':'ontokin.c195.author-evidence-audit/0.1','passed':True,'reviewed_utc':datetime.now(timezone.utc).isoformat(),
 'input_manifest_sha256':sha(HERE/'INPUTS.json'),'freeze_sha256':sha(HERE/'FREEZE.json'),
 'delivery_manifest_sha256':sha(manifest),'verifier_sha256':sha(HERE/'verify_deliveries.py'),
 'reviewer':'Independent C195 preparation/review agent; no author work or native execution',
 'authors':results,'assertions_passed':count,'new_native_builds':0,'new_native_replays':0,'new_receiving_executions':0,
 'manual_review':['Both DIAGNOSIS.md narratives, retained localized repair scripts, negative control flow and positive build wrappers reviewed.',
 'All raw route evidence files and exact author dossier files are hash-bound below. Paths are limited to author output/dossier/current frozen repo locations for archival.'],
 'reviewer_check_corrections':['An initial review condition incorrectly required final preservation snapshots to precede the author reported seal-start timestamp. No report was issued. The final review correctly brackets snapshots by actual seal completion and uses the later recorded Git commit command completion conservatively; no author evidence was rewritten.'],
 'scope':'Author rejection, preservation, locality, submission and native accounting only. Independent numerical, saved-scene and receiving acceptance is a separate coordinator result. No comparative advantage claim.',
 'legacy_status':{'driver':'FAILED','supplemental_tail':'FAILED','passed_unique_methods':4239,'torque_methods_not_run':13}}
OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
validation=v.author_audit(OUT,rows,sha(manifest))
print(json.dumps({'audit':str(OUT),'sha256':sha(OUT),'schema_validation':validation,'assertions_passed':count,'authors':{r:{'wall_seconds':x['wall_seconds'],'reported_wall_seconds':x['timing']['reported_wall_seconds'],'evidence_files':len(x['evidence']),'operations':x['harness_operations_total_including_rejection']} for r,x in results.items()}},indent=2))
