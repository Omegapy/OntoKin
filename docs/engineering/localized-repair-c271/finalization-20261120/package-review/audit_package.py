"""Inspect one frozen ZIP and prompts; write only this review directory."""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
from collections import Counter
import hashlib, json, posixpath, stat, subprocess, zipfile

B=Path('/workspace/scratch/c219bb61a617'); O=B/'final-package-review'; P=B/'packages'; R=B/'OntoKin'
NAME='OntoKin_C271_P02_Validation_Blocked_Handoff_2026-11-20.zip'; Z=P/NAME
SHA='f9cd741651c271a31cbe6fa691b07080dcc531f6fc35ea62adf6186cb0091b7a'
REV='70a658c31085bf8dd78d79663c57f8e3cdb28ceb'; TREE='77ee621cdfb00acf637828ce71f3384b4dd8275c'
MAIN='e1a48f7d0635e9aa4f4b6d6a586e7305eb81999d'; MTREE='9345594c980f121fae2f087b40e4c78adb8f7925'
F='repository/docs/engineering/localized-repair-c271/finalization-20261120/'
checks=[]; reads=[]; commands=[]
def sha(d): return hashlib.sha256(d).hexdigest()
def ck(n,v,category='package'): checks.append(dict(name=n,passed=bool(v),category=category))
def read(p):
 d=p.read_bytes(); reads.append(dict(path=str(p),bytes=len(d),sha256=sha(d))); return d
def git(*a):
 argv=['git','-C',str(R),*a]; p=subprocess.run(argv,capture_output=True)
 commands.append(dict(argv=argv,returncode=p.returncode,stdout_bytes=len(p.stdout),stdout_sha256=sha(p.stdout),stderr=p.stderr.decode()))
 if p.returncode: raise RuntimeError(str(commands[-1]))
 return p.stdout
def tree(rev):
 result={}
 for row in git('ls-tree','-r','-l','-z',rev).split(b'\0'):
  if row:
   meta,path=row.decode().split('\t',1);mode,kind,blob,size=meta.split();result[path]=dict(mode=mode,blob=blob,bytes=int(size))
 return result
def put(n,x): (O/n).write_text(json.dumps(x,indent=2)+'\n')

archive=read(Z);ck('expected archive identity',len(archive)==19975795 and sha(archive)==SHA)
builder=json.loads(read(P/'OntoKin_C271_P02_Validation_Blocked_Handoff_2026-11-20_VERIFICATION.json'))
ck('builder receipt binds same archive',builder['passed'] and builder['checks_failed']==0 and builder['archive']['bytes']==len(archive) and builder['archive']['sha256']==SHA)
trees={REV:tree(REV),MAIN:tree(MAIN)}
ck('exact candidate tree',git('rev-parse',REV+'^{tree}').decode().strip()==TREE,'git')
ck('exact observed main tree',git('rev-parse',MAIN+'^{tree}').decode().strip()==MTREE,'git')
extract=O/'fresh-extraction-01';extract.mkdir(exist_ok=False)
with zipfile.ZipFile(Z) as z:
 names=z.namelist(); infos=z.infolist()
 safe=all(not PurePosixPath(n).is_absolute() and n==posixpath.normpath(n) and '..' not in PurePosixPath(n).parts and '\\' not in n and ':' not in PurePosixPath(n).parts[0] and not n.endswith('/') and not stat.S_ISLNK(i.external_attr>>16) and not i.flag_bits&1 for n,i in zip(names,infos))
 ck('safe relative regular unencrypted paths',safe);ck('no exact/casefold duplicates',len(names)==len(set(names))==len({n.casefold() for n in names}));ck('CRC integrity',z.testzip() is None)
 if not safe or len(names)!=len(set(names)): raise RuntimeError('Unsafe ZIP; no extraction permitted')
 content={n:z.read(n) for n in names}
 def j(n): return json.loads(content[n])
 manifest=j('MANIFEST-SHA256.json');mp={x['path'] for x in manifest['files']}
 ck('219 members / 218 exact manifest payloads',len(names)==219 and len(manifest['files'])==len(mp)==218 and set(names)==mp|{'MANIFEST-SHA256.json'})
 ck('explicit manifest self exclusion',manifest['excludes']==['MANIFEST-SHA256.json'])
 for x in manifest['files']:
  d=content[x['path']];ck('manifest '+x['path'],len(d)==x['bytes'] and sha(d)==x['sha256'],'manifest')
 for n,d in content.items():
  p=extract/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(d);ck('extraction '+n,p.read_bytes()==d,'extraction')
 ck('fresh extraction exact inventory',{str(p.relative_to(extract)) for p in extract.rglob('*') if p.is_file()}==set(names),'extraction')
 snaps=j('metadata/SNAPSHOT-SOURCES.json')['files'];sources=j('metadata/SESSION-AND-RECOVERY-SOURCES.json')['files'];external=j('metadata/EXTERNAL-SOURCE-DEPENDENCIES.json')['files']
 ck('157 unique Git snapshots',len(snaps)==len({x['package_path'] for x in snaps})==157,'git')
 for x in snaps:
  d=content[x['package_path']];g=git('show',x['revision']+':'+x['repository_path']);entry=trees[x['revision']][x['repository_path']]
  ck('Git snapshot '+x['package_path'],d==g and len(d)==x['bytes'] and sha(d)==x['sha256'] and entry['mode']==x['git_mode'] and entry['blob']==x['git_blob'],'git')
  ck('snapshot prefix '+x['package_path'],x['package_path']==('repository/' if x['revision']==REV else 'observed-main/')+x['repository_path'],'git')
 ck('144 candidate / 13 main snapshots',Counter(x['revision'] for x in snaps)=={REV:144,MAIN:13},'git')
 for x in external:
  d=git('show',x['revision']+':'+x['repository_path']);ck('online dependency '+x['repository_path'],x['revision']==REV and len(d)==x['bytes'] and sha(d)==x['sha256'] and trees[REV][x['repository_path']]['blob']==x['git_blob'],'online')
 ck('eight pinned online dependencies',len(external)==8,'online')
 for x in sources:
  d=content[x['package_path']];ck('source map '+x['source_path'],d==read(Path(x['source_path'])) and len(d)==x['bytes'] and sha(d)==x['sha256'],'mapping')
  if 'representation' in x:ck('exact alias '+x['source_path'],x['package_path'] in {q['package_path'] for q in snaps},'alias')
 ck('118 source/recovery mappings',len(sources)==118,'mapping')
 generated={'metadata/BUILD-BOUNDARY.json','metadata/EXTERNAL-SOURCE-DEPENDENCIES.json','metadata/SESSION-AND-RECOVERY-SOURCES.json','metadata/SNAPSHOT-SOURCES.json'}
 ck('every payload classified',mp=={x['package_path'] for x in snaps}|{x['package_path'] for x in sources}|generated,'mapping')
 for directory,count in [('integration-review',34),('final-source-review',13)]:
  fs=sorted(p for p in (B/directory).rglob('*') if p.is_file()); mapping={x['source_path']:x for x in sources if x['source_path'].startswith(str(B/directory)+'/')}
  ck('complete frozen '+directory,len(fs)==len(mapping)==count and set(mapping)=={str(p) for p in fs},'review')
  for p in fs:ck('retained review '+str(p.relative_to(B)),content[mapping[str(p)]['package_path']]==p.read_bytes(),'review')
 nested=[('preserved-inputs/OntoKin_C271_Control_Candidate_Handoff_2026-11-20.zip',B/'source/OntoKin_C271_Control_Candidate_Handoff_2026-11-20.zip',12003931,'9bdb8ec134fbf8facc1b1f52aa9b7171de16f35593ddf7ad61930e521f4495df'),(F+'verification/RAW-EVIDENCE.zip',B/'validation/RAW-EVIDENCE.zip',4965080,'c4c973d40c4f6571def93b257877de69568bcd5fdca43bcfed92ff6acfc61e20'),(F+'verification/AFFECTED-RAW-EVIDENCE.zip',R/(F.removeprefix('repository/')+'verification/AFFECTED-RAW-EVIDENCE.zip'),1868775,'196278f75b4bc268c45517d455ba42d0c6c4b78353199296b07f0ba7712f9d75')]
 for n,p,size,digest in nested:ck('nested archive identity only '+n,content[n]==read(p) and len(content[n])==size and sha(content[n])==digest,'nested_identity')
 recovery=j('recovery/UNPUBLISHED-COMMIT-IDENTITY.json');rawpath=next(x['package_path'] for x in sources if x['source_path']==str(B/'session/UNPUBLISHED-AFFECTED-COMMIT.txt'));raw=content[rawpath]
 ck('exact recoverable unpublished commit',len(raw)==recovery['raw_commit_bytes']==269 and sha(raw)==recovery['raw_commit_sha256'] and hashlib.sha1(b'commit '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==recovery['local_commit']=='01b2013fc13ec872fd029d13766e19e86d0eb618','recovery')
 ck('unpublished tree equals published equivalent',git('rev-parse',recovery['local_commit']+'^{tree}').decode().strip()==git('rev-parse',recovery['published_equivalent_commit']+'^{tree}').decode().strip()==recovery['same_tree'],'recovery')
 ck('failed CLI push retained',content[F+'operation-history/AFFECTED-GIT-PUSH-FAILURE.json']==read(B/'session/AFFECTED-GIT-PUSH-FAILURE.json'),'recovery')
 cp=j('CHECKPOINT.json');task=j('repository/docs/workflow/tasks/C271/task.json');outcome=j(F+'PHASE-OUTCOME.json');accept=j(F+'independent-review/INTEGRATION-REVIEW.json');fsreview=j('review-evidence/final-source-review/AUDIT.json')
 roots={'README-START-HERE.md','CHECKPOINT.json','HANDOFF.md','RECOVERY-STATUS.md','NEXT-TASK.md','HISTORICAL-DEPENDENCIES.json','PROMPT-1-CONTINUE.md','PROMPT-2-RECOVER.md'}
 ck('all eight required roots present',roots<=mp,'root')
 ck('checkpoint frozen/main/executed identities',cp['repository_snapshot']['sha']==REV and cp['repository_snapshot']['tree']==TREE and cp['observed_main']['sha']==MAIN and cp['observed_main']['tree']==MTREE and cp['executed_source']['sha']=='88bc8b51b3963b7072375edac6400b6e6a4532e4','root')
 ck('blocked partial requirements accurate',cp['phase_outcome']=='partial' and cp['parent_status']==task['status']=='blocked' and cp['requirements']=={x['id']:x['status'] for x in task['requirements']}==dict(R01='done',R02='done',R03='not_done',R04='not_done',R05='not_done'),'root')
 ck('P01 done P02 incomplete',cp['parent_plan_state']=={x['id']:x['status'] for x in task['plan']}==dict(P01='done',P02='in_progress'),'root')
 ck('actual routine and affected results retained',cp['verification']['routine']==outcome['routine'] and cp['verification']['affected']==outcome['affected'],'root')
 ck('negative independent approval preserved',cp['verification']['independent_acceptance']['verdict']==accept['verdict']=='not_eligible' and cp['verification']['independent_acceptance']['integration_approved'] is accept['integration_approved'] is False and cp['verification']['independent_acceptance']['parent_closure_approved'] is accept['parent_closure_approved'] is False,'root')
 ck('final source audit correctly scoped',cp['verification']['final_source_review']['checks_passed']==fsreview['check_count']==1522 and cp['verification']['final_source_review']['integration_approved'] is False,'root')
 ck('pending save / external receipt',cp['delivery']['status']=='save_pending' and cp['delivery']['partial'] is True and task['delivery']['status']=='pending' and F+'P02-DELIVERY.json' not in names,'root')
 ck('no integration lease closure or active operation claimed',cp['ownership']['main_lease_held'] is False and cp['ownership']['integration_performed'] is False and cp['pull_request']['draft'] is True and cp['pull_request']['merged'] is False and cp['scope_issue']['state']=='open' and cp['current_validation_operations']['active']==cp['current_validation_operations']['unknown']==[],'root')
 ck('unwaived blockers and exact next action',cp['blocking_findings']==outcome['blocking_findings'] and cp['blocking_findings'][0]['complete_suite_count'] is None and cp['blocking_findings'][1]['waiver'] is False and cp['next_action']==outcome['next_action']==task['next_action'],'root')
 hist=j('HISTORICAL-DEPENDENCIES.json');early=j(F+'EARLY-RECOVERY-RECEIPT.json');bound=j('metadata/BUILD-BOUNDARY.json')
 ck('saved early recovery distinct from pending final',cp['early_recovery']==early and early['status']=='saved' and hist['c271_p02_early_recovery']['included'] is False,'root')
 ck('historical input/C262 identities',hist['incoming_c271_p01']['sha256']==nested[0][3] and hist['incoming_c271_p01']['bytes']==12003931 and hist['c262']['sha256']=='b8af544f730a4d1f741d47b56eb3fcf76147ed392a9ebb020f3d966f2f305c90' and hist['c262']['bytes']==532260846,'root')
 ck('builder/config boundary exact',sha(content['builder/build_final.py'])==bound['builder_script_sha256'] and sha(content['builder/final-config.json'])==bound['configuration_sha256'] and bound['source_revision']==REV and bound['source_tree']==TREE and bound['early_zip_embedded'] is False,'root')
 prompts=[('PROMPT-1-CONTINUE.md','OntoKin_C271_P02_Blocked_Prompt_1_Continue_2026-11-20.md',4830,'e468d8edc5d9a97a7a44d5d961159339e9959689fc375c2d84a554c6e8827eca'),('PROMPT-2-RECOVER.md','OntoKin_C271_P02_Blocked_Prompt_2_Recover_2026-11-20.md',5106,'20df654347e76b99c63ada054109e3941beb9f9b036db98b99ccde3c0fb5030f')]
 for n,file,size,digest in prompts:
  d=content[n];text=d.decode();ck('standalone prompt equals ZIP '+n,d==read(P/file) and len(d)==size and sha(d)==digest,'prompt')
  ck('prompt source/status/save identity '+n,all(s in text for s in [REV,TREE,MAIN,NAME,'P02-DELIVERY.json','not eligible for integration']),'prompt')
  ck('prompt bounded next action/preparation '+n,cp['next_action'] in text and 'historical readback inputs' in text and 'early recovery' in text and 'before substantial work' in text and 'one bounded phase' in text and 'stop' in text.lower(),'prompt')
 text=content['PROMPT-2-RECOVER.md'].decode();ck('delivery-only and uncertain-operation recovery','complete only those delivery actions and stop' in text and 'before retrying' in text and 'Never force refs' in text and 'historical C270' in text,'prompt')
 upload=j('session-evidence/FINAL-UPLOAD-REQUEST.json');ck('planned upload is not a save result',set(upload)=={'uploads'} and len(upload['uploads'])==3 and all(x['purpose']=='create_library_file' for x in upload['uploads']),'delivery')
 ck('planned upload names audited deliverables',{Path(x['local_path']).name for x in upload['uploads']}=={NAME,*[x[1] for x in prompts]},'delivery')
ck('archive unchanged after inspection',Z.stat().st_size==19975795 and sha(Z.read_bytes())==SHA)
failed=[x for x in checks if not x['passed']]
result=dict(schema='ontokin.c271.p02-independent-final-package-audit/1',reviewer='/root/intake_audit',reviewed_at_utc=datetime.now(timezone.utc).isoformat(),verdict='eligible_for_save' if not failed else 'not_eligible_for_save',integration_approved=False,parent_closure_approved=False,save_observed=False,archive=dict(path=str(Z),bytes=len(archive),sha256=sha(archive)),source_commit=REV,source_tree=TREE,observed_main=MAIN,observed_main_tree=MTREE,members=len(names),manifest_payloads=len(manifest['files']),git_snapshots=len(snaps),snapshot_counts=dict(Counter(x['revision'] for x in snaps)),source_recovery_mappings=len(sources),exact_git_alias_mappings=sum('representation' in x for x in sources),online_source_dependencies=len(external),preserved_acceptance_review_files=34,preserved_final_source_review_files=13,fresh_extraction=str(extract),nested_archive_expansion=False,behavioral_reexecution=False,source_or_package_mutated=False,manual_root_document_review=dict(files=sorted(roots),finding='Accurate blocked/pending-save state, original failures/environment limits, distinct main/source, bounded recovery, external receipt rule and no false integration/closure approval.'),checks=checks,check_count=len(checks),failed_count=len(failed),limits=['Actual saved-file confirmation and later receipt-only publication remain outside this audit','Online continuation package, not complete offline restoration','Routine failures and parent requirements remain unmet','Planned upload input does not establish a write'],next_action='Root may save this exact ZIP and matching prompts, verify saved identities, publish the external receipt, verify receipt-only state, then stop.')
put('AUDIT.json',result);put('READ-SET.json',dict(schema='ontokin.final-package-read-set/1',governing_reads_reused='../integration-review/READ-SET.json',file_reads=reads,git_reads=commands,archive_member_reads=names,nested_members_not_expanded=True))
attempts=json.loads((O/'AUDIT-ATTEMPTS.json').read_text());attempts['completed_audit_attempts'].append(dict(log='audit-run-01.log',checks=len(checks),failed=len(failed),status=result['verdict']));put('AUDIT-ATTEMPTS.json',attempts)
print(json.dumps(dict(verdict=result['verdict'],checks=len(checks),failed_count=len(failed),failed=failed)))
