"""Independent final handoff audit: archive, exact Git objects and inert data only."""
import base64
import collections
import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import posixpath
import stat
import subprocess
import zipfile
import zlib

BASE=Path('/workspace/scratch/2ad494d5da19')
REPO=BASE/'OntoKin'
OUT=BASE/'session_evidence/final_package_review'
ARCHIVE=BASE/'deliverables/final/OntoKin_C271_P11_Loader_Path_Handoff_2026-11-21.zip'
HEAD='e7508fb23c64563549631a1be46a3523593e2d9f'
TREE='06c7db644326a5e03bffe8ad53ea4fa0004e7065'
MAIN='e1a48f7d0635e9aa4f4b6d6a586e7305eb81999d'
MAIN_TREE='9345594c980f121fae2f087b40e4c78adb8f7925'
SHA='4eddd353047fb8d6aa316544c8b54d655eb53a1613f9c522bbed0edc1ab1249e'
checks=[]


def sha(b):return hashlib.sha256(b).hexdigest()


def no_duplicates(pairs):
    out={}
    for k,v in pairs:
        if k in out:raise ValueError('Duplicate JSON key: '+k)
        out[k]=v
    return out


def parse(b):return json.loads(b,object_pairs_hook=no_duplicates)


def load(p):return parse(p.read_bytes())


def binding(b):return {'bytes':len(b),'sha256':sha(b)}


def check(label,okay,details=None):checks.append({'id':label,'passed':bool(okay),'details':details})


def safe(name):
    p=PurePosixPath(name)
    return bool(name) and not p.is_absolute() and all(x not in ('','.','..') for x in name.split('/')) and str(p)==name and '\\' not in name and '\0' not in name


def git(*args):return subprocess.check_output(['git',*args],cwd=REPO)


OUT.mkdir(parents=True,exist_ok=True)
fresh=OUT/'fresh_extract';fresh.mkdir(mode=0o700,exist_ok=False)
archive_bytes=ARCHIVE.read_bytes()
check('FP01-exact-requested-frozen-archive',len(archive_bytes)==5606509 and sha(archive_bytes)==SHA,{'path':str(ARCHIVE),**binding(archive_bytes)})
with zipfile.ZipFile(ARCHIVE) as z:
    infos=z.infolist();names=[i.filename for i in infos]
    bad=[i.filename for i in infos if not safe(i.filename) or stat.S_IFMT(i.external_attr>>16) not in (0,stat.S_IFREG)]
    duplicates=[k for k,v in collections.Counter(names).items() if v!=1]
    crc=z.testzip()
    check('FP02-archive-safe-inventory-and-CRC',not bad and not duplicates and crc is None,{'entries':len(infos),'total_payload_bytes':sum(i.file_size for i in infos),'unsafe':bad,'duplicate':duplicates,'crc_failure':crc})
    if bad or duplicates or crc:raise RuntimeError('Unsafe archive refused')
    modes={}
    for i in infos:
        p=fresh/i.filename;p.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
        mode=stat.S_IMODE(i.external_attr>>16)
        if mode not in (0o600,0o644,0o755):raise RuntimeError('Unexpected archived regular-file mode')
        fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,mode)
        try:
            raw=z.read(i.filename);os.fchmod(fd,mode)
            offset=0
            while offset<len(raw):offset+=os.write(fd,raw[offset:])
        finally:os.close(fd)
        modes[i.filename]=oct(mode)

manifest=load(fresh/'MANIFEST-SHA256.json')
rows=manifest['files'];mnames=[r['path'] for r in rows]
manifest_bad=[r['path'] for r in rows if not safe(r['path']) or binding((fresh/r['path']).read_bytes())!={k:r[k] for k in ['bytes','sha256']}]
check('FP03-complete-payload-manifest-and-fresh-bytes',not manifest_bad and len(set(mnames))==len(mnames) and set(mnames)==set(names)-{'MANIFEST-SHA256.json'}, {'payloads':len(rows),'mismatches':manifest_bad})
physical_bad=[n for n in names if not stat.S_ISREG((fresh/n).lstat().st_mode) or (fresh/n).is_symlink() or oct(stat.S_IMODE((fresh/n).lstat().st_mode))!=modes[n]]
check('FP04-fresh-regular-files-and-exact-archive-modes',not physical_bad,{'mismatches':physical_bad,'mode_counts':dict(collections.Counter(modes.values()))})
required=['README-START-HERE.md','CHECKPOINT.json','HANDOFF.md','NEXT-TASK.md','RECOVERY-STATUS.md','PROMPT-1-CONTINUE.md','PROMPT-2-RECOVER.md','HISTORICAL-DEPENDENCIES.json','MANIFEST-SHA256.json']
check('FP05-required-root-contents',all(n in names for n in required),required)

source=load(fresh/'SOURCE-MANIFEST.json')['snapshots']
revisions={r['revision'] for r in source};git_trees={};git_files={}
for revision in revisions:
    git_trees[revision]=git('rev-parse',revision+'^{tree}').decode().strip()
    inventory={}
    for record in git('ls-tree','-r','-z',revision).split(b'\0'):
        if not record:continue
        metadata,path=record.split(b'\t',1);mode,kind,oid=metadata.decode().split()
        inventory[path.decode()]={'git_mode':mode,'kind':kind,'git_blob_sha1':oid}
    git_files[revision]=inventory
source_bad=[]
for row in source:
    raw=(fresh/row['payload_path']).read_bytes()
    observed=git_files[row['revision']].get(row['repository_path'])
    oid=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    if not (observed=={'git_mode':row['git_mode'],'kind':'blob','git_blob_sha1':row['git_blob_sha1']} and oid==row['git_blob_sha1'] and git_trees[row['revision']]==row['tree'] and binding(raw)=={k:row[k] for k in ['bytes','sha256']} and int(row['git_mode'],8)&0o777==int(modes[row['payload_path']],8)):
        source_bad.append(row['payload_path'])
check('FP06-all-source-snapshots-match-exact-Git-objects',not source_bad and len({r['payload_path'] for r in source})==len(source),{'snapshots':len(source),'revisions':git_trees,'mismatches':source_bad})
check('FP07-published-and-main-tree-identities',git_trees=={HEAD:TREE,MAIN:MAIN_TREE},{'source':HEAD,'source_tree':TREE,'main':MAIN,'main_tree':MAIN_TREE})
source_paths={r['repository_path'] for r in source if r['revision']==HEAD}
need=['CHATGPT-START-HERE.md','AGENTS.md','GOAL.md','STATUS.md','ROLE.md','docs/workflow/registry.json','docs/workflow/CURRENT.json','docs/workflow/PROTOCOL.md','docs/workflow/HANDOFF.md','docs/workflow/BROWSER-PROMPTS.md','docs/workflow/templates/WORKER.md','docs/workflow/tasks/C271/REQUIREMENTS.md','docs/workflow/tasks/C271/PLAN.md','docs/workflow/tasks/C271/task.json']
prefix='docs/engineering/localized-repair-c271/loader-path-p11/'
p11_git={p for p in git_files[HEAD] if p.startswith(prefix)}
check('FP08-required-instructions-task-and-full-P11-source',set(need)<=source_paths and p11_git<=source_paths,{'required':need,'P11_Git_files':len(p11_git),'missing':sorted((set(need)|p11_git)-source_paths)})
protected=load(BASE/'session_evidence/loader_design/candidate004/PROTECTED-SOURCES.json')['files']
protected_bad=[r['path'] for r in protected if binding(git('show',HEAD+':'+r['path']))!={'bytes':r['size_bytes'],'sha256':r['sha256']}]
check('FP09-protected-source-remains-exact',not protected_bad,{'protected_files':len(protected),'mismatches':protected_bad})

deps=load(fresh/'HISTORICAL-DEPENDENCIES.json')
prior_review=load(BASE/'session_evidence/intake_audit/REVIEW.json')
early_review=load(BASE/'session_evidence/early_review/REVIEW.json')
expected_inputs={
 'p10_archive':(BASE/'incoming/OntoKin/OntoKin_C271_P10_ELF_Mapping_Handoff_2026-11-21.zip',10556884,'42739db560ae8a46706d41ded21038d44a8a8a61ac45d6792374a7e31306c275'),
 'p10_terminal_receipt':(BASE/'incoming/OntoKin/OntoKin_C271_P10_Delivery_Receipt_2026-11-21.json',1767981,'4195824db6585ebeed3f0bef1b933c9b465a6541f9ff155a38767f853c7232f5'),
 'saved_session_archive_f8047061fd25':(BASE/'deliverables/early/OntoKin_C271_P11_Loader_Path_Early_Recovery_2026-11-21.zip',899708,'f8047061fd25c770c92baf260cce31351dc4a5dcb5bbbb7006e4188b9848ae94')}
prior_zips={};prior_members={};prior_modes={};input_checks=[]
for key,(path,size,h) in expected_inputs.items():
    actual=binding(path.read_bytes());okay=actual=={'bytes':size,'sha256':h} and {k:deps[key][k] for k in ['bytes','sha256']}==actual
    input_checks.append({'dependency':key,**actual,'matched':okay})
    if path.suffix=='.zip':
        z=zipfile.ZipFile(path);prior_zips[key]=z
        index={r['path']:{k:r[k] for k in ['bytes','sha256']} for r in parse(z.read('MANIFEST-SHA256.json'))['files']}
        index['MANIFEST-SHA256.json']=binding(z.read('MANIFEST-SHA256.json'))
        prior_members[key]=index;prior_modes[key]={i.filename:oct(stat.S_IMODE(i.external_attr>>16)) for i in z.infolist()}
check('FP10-reused-authenticated-prior-input-identities',all(r['matched'] for r in input_checks) and prior_review['verdict']=='pass_with_declared_external_dependency' and early_review['verdict']=='accepted_for_save_with_external_receipt_clarification',{'inputs':input_checks,'prior_full_intake_repeated':False,'prior_primary_source_or_host_revalidation':False})
olddeps=parse(prior_zips['p10_archive'].read('HISTORICAL-DEPENDENCIES.json'))
check('FP11-selected-Python-P09-and-C262-dependencies-exact',deps['selected_python_fixture']==olddeps['selected_python_fixture'] and deps['p09_archive']==olddeps['incoming_p09'] and deps['c262']==olddeps['c262'],{'selected_fixture':deps['selected_python_fixture'],'P09_retrieved_or_executed':False,'C262_retrieved':False})
terminal=load(expected_inputs['p10_terminal_receipt'][0]);late={r['relative_path']:r for r in terminal['late_evidence']['files']}
recovery=load(fresh/'RECOVERY-FILE-MAP.json');rrows=recovery['files'];rmap={r['relative_path']:r for r in rrows}
map_bad=[];mode_bad=[];embedded=0;external=0
for row in rrows:
    rel=row['relative_path'];want={k:row[k] for k in ['bytes','sha256']}
    okay=safe(rel) and row['original_path']==str(BASE/rel) and row['source_mode'] in ['0o600','0o644','0o755']
    if 'payload_path' in row:
        embedded+=1
        okay=okay and safe(row['payload_path']) and binding((fresh/row['payload_path']).read_bytes())==want and modes[row['payload_path']]==row['source_mode']
    else:
        external+=1;ref=row['external_source'];dep=ref['dependency']
        if 'archive_member' in ref:
            okay=okay and prior_members.get(dep,{}).get(ref['archive_member'])==want
        elif 'json_pointer' in ref:
            prior=late.get(ref['relative_path'],{})
            okay=okay and dep=='p10_terminal_receipt' and ref['json_pointer']=='/late_evidence/files' and {k:prior.get(k) for k in ['bytes','sha256']}==want and ref['blob_sha256']==row['sha256'] and ref['decode']=='zlib+base64 from late_evidence.blobs[sha256]'
        else:
            okay=okay and dep in expected_inputs and ref['file']==deps[dep]['file_name'] and want=={k:deps[dep][k] for k in ['bytes','sha256']}
    if not okay:map_bad.append(rel)
    original=BASE/rel
    if not original.is_file() or original.is_symlink() or oct(stat.S_IMODE(original.lstat().st_mode))!=row['source_mode']:mode_bad.append(rel)
check('FP12-complete-exact-recovery-map',not map_bad and len(rmap)==len(rrows) and recovery['base_revision']==HEAD,{'rows':len(rrows),'embedded':embedded,'external':external,'mismatches':map_bad})
check('FP13-current-original-and-restored-mode-evidence',not mode_bad,{'original_modes_observed':len(rrows),'mismatches':mode_bad,'external_mode_note':'Explicit source_mode is the required restored physical mode; it can differ from a source archive member mode when an earlier extraction changed private transport metadata.'})


def recover_bytes(relative):
    row=rmap[relative]
    if 'payload_path' in row:return (fresh/row['payload_path']).read_bytes()
    ref=row['external_source'];dep=ref['dependency']
    if 'archive_member' in ref:return prior_zips[dep].read(ref['archive_member'])
    if 'json_pointer' in ref:
        blob=terminal['late_evidence']['blobs'][ref['blob_sha256']]
        return zlib.decompress(base64.b64decode(blob['data_base64'],validate=True))
    return expected_inputs[dep][0].read_bytes()


cp=load(fresh/'CHECKPOINT.json');freeze=datetime.datetime.fromisoformat(cp['frozen_at_utc']).timestamp()
missing_before=[];late_unmapped=[];late_changed=[];current_mismatch=[];current_verified=0
for p in (BASE/'session_evidence').rglob('*'):
    if not p.is_file() or 'final_package_review' in p.relative_to(BASE/'session_evidence').parts or '__pycache__' in p.parts:continue
    rel=str(p.relative_to(BASE));observed=binding(p.read_bytes())
    if rel not in rmap:
        (missing_before if p.stat().st_mtime<=freeze else late_unmapped).append(rel)
    elif observed!={k:rmap[rel][k] for k in ['bytes','sha256']}:
        (current_mismatch if p.stat().st_mtime<=freeze else late_changed).append(rel)
    else:current_verified+=1
check('FP14-all-current-prefreeze-session-evidence-recoverable',not missing_before and not current_mismatch,{'verified_current_files':current_verified,'missing_before_freeze':missing_before,'changed_before_freeze':current_mismatch,'postfreeze_unmapped_external_receipt':sorted(late_unmapped),'postfreeze_changed_external_receipt':sorted(late_changed),'this_review_excluded_as_late':True})
specific=['session_evidence/PHASE.json','session_evidence/EARLY-RECOVERY-RECEIPT.json','session_evidence/intake_audit/REVIEW-RUN001.json','session_evidence/intake_audit/audit_followup.py','session_evidence/loader_design/static001.stdout.json','session_evidence/loader_design/ATTEMPT003-RETENTION.json','session_evidence/design_review/candidate002/REVIEW.json','session_evidence/design_review/candidate002/CASE-SEMANTICS.json','session_evidence/design_review/REVIEW.json','session_evidence/design_review/DOCUMENT-CAP-DECISION.json','session_evidence/design_review/candidate004/REVISION-REVIEW.json','session_evidence/design_review/candidate004/REVISION-FOLLOWUP.json','session_evidence/transport_review/REVIEW.json','session_evidence/USER-DOCUMENT-CAP-DECISION.json','session_evidence/checks/technical-candidate/whitespace.stdout.txt','session_evidence/checks/published/CHECKS.json','session_evidence/checks/published/SOURCE-BOUNDARY.json','session_evidence/publication/technical/VERIFICATION.json']
specific_bad=[p for p in specific if p not in rmap or recover_bytes(p)!=(BASE/p).read_bytes()]
check('FP15-key-failures-real-reviews-and-publication-evidence-preserved',not specific_bad,{'required':specific,'mismatches':specific_bad})
groups={}
for part in ['loader_design','design_review','transport_review']:
    paths=[str(p.relative_to(BASE)) for p in (BASE/'session_evidence'/part).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    groups[part]={'files':len(paths),'all_mapped':all(p in rmap for p in paths)}
check('FP16-complete-author-and-independent-review-history',all(v['all_mapped'] for v in groups.values()),groups)

candidate_rel='session_evidence/loader_design/candidate004'
candidate_manifest_raw=recover_bytes(candidate_rel+'/CANDIDATE-MANIFEST.json');cm=parse(candidate_manifest_raw)
candidate_bad=[]
for row in cm['payload']+cm['supporting_files']:
    rel=posixpath.normpath(candidate_rel+'/'+row['path'])
    raw=recover_bytes(rel)
    if not rel.startswith('session_evidence/loader_design/') or binding(raw)!={'bytes':row['size_bytes'],'sha256':row['sha256']} or ('mode' in row and rmap[rel]['source_mode']!=row['mode']):candidate_bad.append(rel)
phase_prefix='repository/'+prefix
canonical_manifest=(fresh/(phase_prefix+'design/candidate004/CANDIDATE-MANIFEST.json')).read_bytes()
check('FP17-accepted004-complete-original-byte-and-mode-recovery',sha(candidate_manifest_raw)=='e7b505aa768d0656db6c4dfaf7541e796aefee7148878a6fdf380d6ab0b911de' and len(candidate_manifest_raw)==35041 and canonical_manifest==candidate_manifest_raw and not candidate_bad,{'payloads':len(cm['payload']),'supports':len(cm['supporting_files']),'mismatches':candidate_bad})
expectations=parse(recover_bytes(candidate_rel+'/EXPECTATIONS.json'));fixtures=parse(recover_bytes(candidate_rel+'/FIXTURE-MANIFEST.json'))
decision=recover_bytes(candidate_rel+'/DECISION.md').decode();surface=parse(recover_bytes(candidate_rel+'/FUTURE-SURFACE.json'))
check('FP18-exact97-controls-and-inherited16MiB-policy',len(expectations['cases'])==97 and len(fixtures['cases'])==97 and len(fixtures['files'])==131 and "maximum=LIMITS['document_bytes']" in decision and 'unchanged 16 MiB allowance' in decision and not any(k.startswith(('P08','N74')) for k in expectations['cases']) and surface['implementation_authorized_in_p11'] is False,{'cases':len(expectations['cases']),'fixtures':len(fixtures['files']),'production_changes_authorized':False})
for ident,want in [('session_evidence/design_review/REVIEW.json','b9e6db3125acb05c2fab420a608e404810e234c9e4abdcee10a61838c6712a58'),('session_evidence/transport_review/REVIEW.json','f26cfaaa80509060d4e8e1e86436bf72a3947106c968560b61dad7d3ecae5fea')]:
    check('FP19-authenticated-real-review-'+ident.split('/')[-2],sha(recover_bytes(ident))==want,{'path':ident,'sha256':sha(recover_bytes(ident))})
ret=parse(recover_bytes('session_evidence/loader_design/ATTEMPT003-RETENTION.json'));retbad=[]
for row in ret['preserved_payload']+ret['preserved_support']:
    rel='session_evidence/loader_design/'+row['path']
    if binding(recover_bytes(rel))!={'bytes':row['size_bytes'],'sha256':row['sha256']} or rmap[rel]['source_mode']!=row['mode']:retbad.append(rel)
check('FP20-withdrawn003-and-supports-exact',not retbad and len(ret['preserved_payload'])==148 and len(ret['preserved_support'])==12,{'payloads':148,'supports':12,'mismatches':retbad,'state':ret['state']})

transport=load(fresh/(phase_prefix+'GIT-TRANSPORT.json'));transport_bad=[]
for row in transport['records']:
    encoded=(fresh/(phase_prefix+row['envelope_relative_path'])).read_bytes();envelope=parse(encoded)
    raw=base64.b64decode(envelope['content_base64'],validate=True)
    original=recover_bytes(row['unaltered_original_recovery_path'])
    if not (set(envelope)=={'schema','encoding','decoded_size_bytes','decoded_sha256','content_base64'} and envelope['schema']=='ontokin.lossless-evidence-envelope/1' and envelope['encoding']=='base64' and sha(encoded)==row['envelope_sha256'] and raw==original and binding(raw)=={'bytes':row['decoded_size_bytes'],'sha256':row['decoded_sha256']} and rmap[row['unaltered_original_recovery_path']]['source_mode']==row['materialized_mode']):transport_bad.append(row['materialized_relative_path'])
check('FP21-Git-envelopes-and-original-raw-bytes-recoverable',not transport_bad and len(transport['records'])==3,{'mappings':3,'envelopes':2,'mismatches':transport_bad,'materialization_instructions_present':phase_prefix+'GIT-TRANSPORT.md' in names})

phase_raw=recover_bytes('session_evidence/PHASE.json');phase=parse(phase_raw)
agree=['task','phase','owner','scope','acceptance','constraints','parent_status','parent_complete','parent_requirements','parent_plan','stop','workers','current_unknown_operations','historical_unknowns','post_delivery_next_action','worker_dispositions','next_phase_acceptance','next_phase_stop']
disagree=[k for k in agree if cp[k]!=phase[k]]
check('FP22-checkpoint-source-phase-roster-delivery-agreement',not disagree and cp['source_commit']==HEAD and cp['source_tree']==TREE and cp['branch']['head']==HEAD and cp['observed_main']['commit']==MAIN and cp['early_save_confirmed'] is True and cp['delivery']['status']=='save_pending' and cp['parent_complete'] is False and cp['main_lease_held'] is False and cp['integration_allowed'] is False and set(cp['workers'])=={'/root','/root/loader_design','/root/intake_audit','/root/handoff_engineer'} and cp['phase_record']['bytes']==len(phase_raw) and cp['phase_record']['sha256']==sha(phase_raw),{'disagreements':disagree,'delivery':cp['delivery'],'roster':cp['worker_dispositions']})
prompt_results=[]
for suffix,member,expected_sha,expected_size in [('_Continue.md','PROMPT-1-CONTINUE.md','0d0b6bbf3d5e0cdbd550f8777d37b54cea3db339e9b121bfbb5461e46b966237',5673),('_Recover.md','PROMPT-2-RECOVER.md','9cae6e7f92ab216cbae6e917152e58a9ad4fb261ecaff70190f5d85509e3bbda',5899)]:
    p=ARCHIVE.with_name(ARCHIVE.stem+suffix);raw=(fresh/member).read_bytes()
    prompt_results.append({'member':member,'standalone':str(p),**binding(raw),'equal':p.read_bytes()==raw and sha(raw)==expected_sha and len(raw)==expected_size})
check('FP23-exact-matching-complete-prompts',all(r['equal'] for r in prompt_results),prompt_results)
check('FP24-delivery-first-and-one-later-phase-instructions',all('If P11 delivery is incomplete' in (fresh/n).read_text() and 'if delivery is confirmed' in (fresh/n).read_text() for n in ['PROMPT-1-CONTINUE.md','PROMPT-2-RECOVER.md']) and 'If P11 delivery or publication is still incomplete, complete only that remaining work and stop' in (fresh/'NEXT-TASK.md').read_text() and 'Do not begin implementation in this chat' in cp['exact_next_action'],{'human_review':'All required root prose and both full prompts read. Technical publication/checks already complete; first remaining action is independent package review, exact save/readback, separate receipt, stop.'})
check('FP25-no-execution-qualification-or-parent-overclaim',cp['accepted_design_summary']['implementation_authorized_in_this_chat'] is False and cp['accepted_design_summary']['product_execution'] is False and cp['accepted_design_summary']['h0_accepted'] is False and cp['accepted_design_summary']['h1_approved'] is False and cp['parent_requirements']['R03']=='not_done' and cp['parent_requirements']['R04']=='not_done' and cp['parent_requirements']['R05']=='not_done' and cp['pull_request']['draft'] is True and cp['pull_request']['merged'] is False and cp['scope_issue']['state']=='open',{'H0':'unaccepted','H1':'unapproved','R03_R05':'not_done','main_lease':False,'historical_unknowns':cp['historical_unknowns']})
check('FP26-clean-patch-and-no-future-save-self-reference',(fresh/recovery['tracked_change_patch']).read_bytes()==b'' and recovery['deleted_repository_paths']==[] and cp['delivery']['status']=='save_pending' and 'library_file_id' not in cp['delivery'] and load(fresh/'PACKAGE-BOUNDARY.json')['external_receipt_required'] is True,{'tracked_patch_bytes':len((fresh/recovery['tracked_change_patch']).read_bytes()),'terminal_receipt':'necessarily external after freeze'})

coverage={'freeze':cp['frozen_at_utc'],'recovery_rows':len(rrows),'embedded':embedded,'external':external,'late_unmapped':sorted(late_unmapped),'late_changed':sorted(late_changed),'specific_required_evidence':specific,'group_coverage':groups}
(OUT/'COVERAGE.json').write_text(json.dumps(coverage,indent=2,sort_keys=True)+'\n')
(OUT/'CHECKS.json').write_text(json.dumps(checks,indent=2,sort_keys=True)+'\n')
review={'schema':'ontokin.c271.p11-independent-final-package-review/1','reviewer':'/root/intake_audit','verdict':'accepted_for_exact_save_and_external_receipt' if all(c['passed'] for c in checks) else 'failed','archive':{'path':str(ARCHIVE),**binding(archive_bytes)},'source':{'commit':HEAD,'tree':TREE,'main':MAIN,'main_tree':MAIN_TREE},'check_groups':len(checks),'passed_groups':sum(c['passed'] for c in checks),'blocking_findings':[c for c in checks if not c['passed']],'counts':{'zip_entries':len(names),'manifest_payloads':len(rows),'Git_snapshots':len(source),'embedded_recovery':embedded,'external_recovery_aliases':external,'total_recovery_records':len(rrows)},'prompts':prompt_results,'checks':'CHECKS.json','coverage':'COVERAGE.json','required_external_receipt_items':['Exact saved ZIP and standalone prompt identities, destination folder/version and byte readback','This independent final review and builder/verifier artifacts created after freeze','Any postfreeze source/publication/worker/readback observations and exact late evidence','Final phase delivery result and retained unfinished branch/PR/issue state; no parent closure or new implementation phase'],'limitations':['No Library write or saved-byte observation by this reviewer. Acceptance authorizes root to finish the already authorized exact save, not a claim that it has happened.','No live GitHub API reread or product/author-validator execution. Exact local Git objects and packaged readback evidence checked; root retains live publication/delivery responsibilities.','Authenticated prior intake and early-archive evidence reused. P09 selected-image bytes and C262 remain exact external dependencies, not newly retrieved or executed.','Archive is for online continuation, not complete offline restoration. Late review/receipt bytes remain outside this immutable ZIP.'],'product_calls':0,'target_executions':0,'Git_or_Library_writes':False}
(OUT/'REVIEW.json').write_text(json.dumps(review,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:v for k,v in review.items() if k not in ['prompts','limitations','required_external_receipt_items']},indent=2,sort_keys=True))
raise SystemExit(0 if not review['blocking_findings'] else 1)
