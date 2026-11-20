#!/usr/bin/env python3
"""Independent read-only verification of the frozen C268 handoff artifacts."""
from collections import Counter
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path,PurePosixPath
import stat
import subprocess
import tempfile
import zipfile

ROOT=Path('/workspace/scratch/60da64efa55b')
REPO=ROOT/'OntoKin'
OUT=ROOT/'evidence/final-package-review'
DELIVER=ROOT/'deliverables'
ZIP=DELIVER/'OntoKin_C268_Development_Handoff_2026-11-19.zip'
SNAPSHOT='0e0ed57bb704b6291bc66fcc057b73828d247f79'
TREE='b8b6e764053a0344c0ae1d4fcade5787938f33bb'
MAIN='5084dd69312e8da5a49aadd33cf83ba56db7c058'
ORIGINAL='ecce5f18fd4693e254bc6c797cd8b3f0a74d32a1'
ORIGINAL_TREE='5fa6a2a2be560255413a692704ec175f4901d4c5'
PUBLIC_RECOVERY='71932558224d80794f76e52adf603b6308580326'
EXPECTED_ZIP={'bytes':4125939,'sha256':'5ba28847d3993a25715ea76f7bc9fdd0f3e7de906c7c787d0d17eb25673b4a9f'}
checks=[]

def git(*args):return subprocess.check_output(['git','--no-optional-locks',*args],cwd=REPO)
def blob(rev,path):return git('show',rev+':'+path)
def ident(raw):return {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def check(name,passed,detail=None):
    row={'name':name,'passed':bool(passed)}
    if detail is not None:row['detail']=detail
    checks.append(row)
def verify(name,raw,expected):check(name,ident(raw)=={k:expected[k] for k in ['bytes','sha256']})
def sha1_blob(raw):return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
def nested_values(obj,key):
    if isinstance(obj,dict):
        for k,v in obj.items():
            if k==key:yield v
            yield from nested_values(v,key)
    elif isinstance(obj,list):
        for v in obj:yield from nested_values(v,key)

OUT.mkdir(parents=True,exist_ok=True)
started=datetime.now(timezone.utc).isoformat()
archive_bytes=ZIP.read_bytes()
verify('frozen_zip_identity',archive_bytes,EXPECTED_ZIP)
builder_path=DELIVER/'C268-HANDOFF-VERIFICATION.json'
builder=json.loads(builder_path.read_bytes())
check('builder_binding',builder['archive']['filename']==ZIP.name and ident(archive_bytes)=={k:builder['archive'][k] for k in ['bytes','sha256']} and builder['verdict']=='passed')
check('public_snapshot_object',git('rev-parse',SNAPSHOT+'^{tree}').decode().strip()==TREE)
check('public_snapshot_parents',git('show','-s','--format=%P',SNAPSHOT).decode().strip().split()==['bb317b3bb84c484a4877b2a1a5e74393d94795f8',PUBLIC_RECOVERY])
required={'README-START-HERE.md','CHECKPOINT.json','HANDOFF.md','NEXT-TASK.md','RECOVERY-STATUS.md','PROMPT-1-CONTINUE.md','PROMPT-2-RECOVER.md','HISTORICAL-DEPENDENCIES.json','MANIFEST-SHA256.json'}
extraction=Path(tempfile.mkdtemp(prefix='c268-independent-package-',dir=ROOT))
with zipfile.ZipFile(ZIP) as z:
    names=z.namelist()
    safe=all(not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts and '\\' not in n and str(PurePosixPath(n))==n and ':' not in PurePosixPath(n).parts[0] for n in names)
    check('unique_safe_regular_inventory',len(names)==len(set(names)) and safe and all(stat.S_ISREG(i.external_attr>>16) and not i.is_dir() for i in z.infolist()))
    check('required_root_files',required<=set(names))
    check('zip_crc',z.testzip() is None)
    manifest=json.loads(z.read('MANIFEST-SHA256.json'))
    inventory=manifest['files']
    check('exact_manifest_inventory',set(names)==set(inventory)|{'MANIFEST-SHA256.json'} and manifest['excluded']==['MANIFEST-SHA256.json'])
    if not safe or len(names)!=len(set(names)):raise RuntimeError('Unsafe archive cannot be extracted')
    z.extractall(extraction)
    info_by_name={i.filename:i for i in z.infolist()}
    for p,expected in inventory.items():verify('payload:'+p,(extraction/p).read_bytes(),expected)
    check('fresh_extraction_exact_inventory',{p.relative_to(extraction).as_posix() for p in extraction.rglob('*') if p.is_file()}==set(names))
    check('builder_payload_count',builder['payload_file_count_excluding_manifest']==len(inventory))
    snapshots=json.loads(z.read('SNAPSHOT-SOURCES.json'))
    for row in snapshots:
        raw=(extraction/row['package_path']).read_bytes()
        verify('snapshot_digest:'+row['repository_path'],raw,row)
        check('snapshot_git:'+row['repository_path'],row['source_revision']==SNAPSHOT and raw==blob(SNAPSHOT,row['repository_path']) and sha1_blob(raw)==row['git_blob'])
        entry=git('ls-tree',SNAPSHOT,'--',row['repository_path']).decode().strip().split()
        check('snapshot_mode:'+row['repository_path'],entry[0]==row['git_mode'] and (info_by_name[row['package_path']].external_attr>>16)==int(row['git_mode'],8))
    check('exact_snapshot_inventory',{n for n in names if n.startswith('repository/')}=={r['package_path'] for r in snapshots})
    registry=json.loads(z.read('repository/docs/workflow/registry.json'))
    mandatory=set(registry['required_reads'])|{s['path'] for s in registry['skills']}|{'docs/workflow/BROWSER-PROMPTS.md','docs/engineering/localized-repair-c268/INTEGRATION.json'}
    mandatory.update(git('ls-tree','-r','--name-only',SNAPSHOT,'--','docs/workflow/tasks/C268').decode().splitlines())
    check('mandatory_snapshots_and_full_active_task',mandatory<={r['repository_path'] for r in snapshots})
    check('builder_snapshot_count',builder['snapshot_files']==len(snapshots))

    cp=json.loads(z.read('CHECKPOINT.json'));history=json.loads(z.read('HISTORICAL-DEPENDENCIES.json'));sources=json.loads(z.read('SOURCE-IDENTITIES.json'))
    observed=json.loads(z.read('evidence/FINAL-STATE-OBSERVATION.json'))
    check('observed_state_exact',z.read('evidence/FINAL-STATE-OBSERVATION.json')==(ROOT/'evidence/FINAL-PACKAGE-STATE.json').read_bytes())
    check('checkpoint_source_identity',cp['source_snapshot_revision']==cp['observed_main']['sha']==SNAPSHOT and cp['source_snapshot_tree']==cp['observed_main']['tree']==TREE)
    check('checkpoint_live_observation',cp['observed_main']['observation']==observed['observed_at_utc'] and cp['remote']==observed['remote'] and cp['ownership']==observed['ownership'])
    check('pending_R07_truth',cp['parent_task_status']=='in_progress' and cp['requirements']=={**{f'R0{i}':'done' for i in range(1,7)},'R07':'not_done'} and cp['remote']['issue265']=='open' and cp['session_delivery_at_freeze'].startswith('save_pending'))
    check('execution_provenance',cp['verification']['executed_cohort_source']==sources['pr266_merge_and_executed_main']==MAIN and sources['final_packaged_public_main']==SNAPSHOT and sources['final_packaged_public_tree']==TREE and cp['verification']['cohort_rerun_in_current_recovery'] is False)
    check('future_receipt_not_fabricated',history['final_save_receipt']['state_at_freeze']=='future external record; authoritative only after actual confirmed save' and not any(n.endswith('/localized-repair-c268/DELIVERY.json') for n in names))
    current=json.loads(z.read('repository/docs/workflow/CURRENT.json'))
    check('C262_exact',history['C262_unchanged']==current['historical_handoff'] and history['C262_library_file_id']=='libfile_fde3_f-99755ba096208191b599cd0087fa0a19_2ab2a24d43748191957f9bcc356b59de')

    early=history['current_confirmed_early_archive'];early_path=DELIVER/early['file_name']
    verify('early_archive_identity',early_path.read_bytes(),early)
    check('early_receipt_exact',early==json.loads(blob(SNAPSHOT,'docs/engineering/localized-repair-c268/evidence/delivery-60da64efa55b/EARLY-RECOVERY-RECEIPT.json'))==json.loads(z.read('evidence/EARLY-RECOVERY-RECEIPT.json')))
    check('early_saved_id',early['save_outcome']=='confirmed' and early['library_file_id']=='libfile_fde3_f-fd815384ec70819182812c63cc6b7f61_2ab2a24d43748191957f9bcc356b59de' and early['sha256']=='482a59c33e886a609cec7cf27aef85770d11c9b05f17f835fb62085cd59686dd')
    upload=json.loads((ROOT/'evidence/EARLY-UPLOAD-RESULT.json').read_bytes())
    check('early_upload_receipt_binding',early['library_file_id'] in set(nested_values(upload,'library_file_id')) and early['file_id'] in set(nested_values(upload,'file_id')))
    verify('early_verification_identity',z.read('evidence/EARLY-RECOVERY-VERIFICATION.json'),{'bytes':len(z.read('evidence/EARLY-RECOVERY-VERIFICATION.json')),'sha256':early['verification_sha256']})

    index=json.loads(z.read('evidence/INDEX.json'))
    preservation=Counter(r['preservation'] for r in index)
    check('unique_evidence_index',len(index)==len({r['source_relative_path'] for r in index}))
    with zipfile.ZipFile(early_path) as ez:
        check('early_dependency_crc',ez.testzip() is None)
        early_manifest=json.loads(ez.read('MANIFEST-SHA256.json'))['files']
        prior=json.loads(z.read('recovery/PRIOR-EXTERNAL-RECOVERY.json'))
        check('prior_external_index_exact',prior['archive']==early and prior['files']==json.loads(ez.read('recovery/EXTERNAL-FILES.json')))
        for row in prior['files']:
            verify('prior_external_recovery:'+row['relative_to_prior_workspace'],ez.read(row['package_path']),row)
            check('prior_external_manifest:'+row['relative_to_prior_workspace'],early_manifest[row['package_path']]=={k:row[k] for k in ['bytes','sha256']})
        for row in index:
            name=row['source_relative_path']
            if row['preservation']=='included_exact_bytes':
                raw=z.read(row['package_path'])
            elif row['preservation']=='published_git':
                raw=blob(row['source_revision'],row['repository_path'])
                check('published_evidence_pin:'+name,row['source_revision']==SNAPSHOT and row['url']=='https://github.com/Omegapy/OntoKin/blob/'+SNAPSHOT+'/'+row['repository_path'])
            elif row['preservation']=='confirmed_early_archive':
                check('early_evidence_pin:'+name,row['archive_library_file_id']==early['library_file_id'] and row['archive_sha256']==early['sha256'])
                raw=ez.read(row['early_package_paths'][0])
                check('early_matching_locations:'+name,all(ident(ez.read(p))=={k:row[k] for k in ['bytes','sha256']} for p in row['early_package_paths']))
            else:
                check('known_preservation:'+name,False);continue
            verify('current_external_recovery:'+name,raw,row)
            check('external_git_blob:'+name,sha1_blob(raw)==row['git_blob'])
            if 'package_path' in row:verify('included_index_payload:'+name,z.read(row['package_path']),row)
        original=json.loads(z.read('recovery/UNPUBLISHED-COMMIT.json'))
        bundle=z.read(original['bundle'])
        verify('original_bundle_identity',bundle,{'bytes':original['bundle_bytes'],'sha256':original['bundle_sha256']})
        check('bundle_equals_confirmed_early_bytes',bundle==ez.read(original['bundle']))
    check('builder_external_counts',builder['direct_external_files']==preservation['included_exact_bytes'] and builder['evidence_index_entries']==len(index))
    cutoff=datetime.fromisoformat(cp['frozen_at_utc']).timestamp()
    expected_existing=[]
    for directory in [ROOT/'evidence',ROOT/'publication']:
        if directory.exists():
            expected_existing.extend(p.relative_to(ROOT).as_posix() for p in directory.rglob('*') if p.is_file() and p.stat().st_mtime<=cutoff and '__pycache__' not in p.parts and 'final-package-review' not in p.parts)
    missing=sorted(set(expected_existing)-{r['source_relative_path'] for r in index})
    check('prefreeze_evidence_inventory_covered',not missing,{'missing':missing})

    header=bundle.split(b'\n\n',1)[0].decode().splitlines()
    prereqs=[s[1:].split()[0] for s in header if s.startswith('-')]
    heads=[s for s in header if s.startswith(ORIGINAL+' ')]
    check('bundle_exact_online_prerequisite',prereqs==[MAIN] and heads==[ORIGINAL+' refs/heads/preserved-c268-ecce5f18'])
    check('recovery_original_metadata',original['commit']==ORIGINAL and original['tree']==ORIGINAL_TREE and original['parent']==MAIN and history['online_dependency']['incremental_bundle_prerequisite']==MAIN)
    raw_commit=original['raw_commit_utf8'].encode()
    check('original_raw_commit_hash',hashlib.sha1(b'commit '+str(len(raw_commit)).encode()+b'\0'+raw_commit).hexdigest()==ORIGINAL and raw_commit==git('cat-file','commit',ORIGINAL))
    check('original_changed_inventory',{r['path'] for r in original['changed_files']}==set(git('diff','--name-only',MAIN,ORIGINAL).decode().splitlines()))
    for row in original['changed_files']:
        raw=blob(ORIGINAL,row['path']);verify('original_recoverable_path:'+row['path'],raw,row)
        check('original_git_blob:'+row['path'],sha1_blob(raw)==row['git_blob'])
    cmd=['git','--no-optional-locks','bundle','verify',str(extraction/original['bundle'])]
    result=subprocess.run(cmd,cwd=REPO,capture_output=True,text=True)
    (OUT/'BUNDLE-VERIFY.log').write_text(result.stdout+result.stderr)
    check('bundle_verify_with_available_prerequisite',result.returncode==0)
    listheads=git('bundle','list-heads',str(extraction/original['bundle'])).decode().strip()
    check('bundle_list_heads_exact',listheads==ORIGINAL+' refs/heads/preserved-c268-ecce5f18')

    prompts=[]
    for row in builder['standalone_prompts']:
        raw=(DELIVER/row['filename']).read_bytes();verify('standalone_prompt:'+row['filename'],raw,row)
        check('standalone_equals_zip:'+row['filename'],raw==z.read(row['zip_path']))
        prompts.append({k:row[k] for k in ['filename','zip_path','bytes','sha256']})
    p1=z.read('PROMPT-1-CONTINUE.md').decode();p2=z.read('PROMPT-2-RECOVER.md').decode()
    check('prompt1_conflict_resolved','Do not select another task.' in p1 and 'Resume only remaining C268 delivery gates.' in p1)
    check('both_prompts_bind_exact_file_and_snapshot',all(ZIP.name in p and SNAPSHOT in p and 'DELIVERY.json' in p for p in [p1,p2]))
    check('both_prompts_reconcile_then_wait_or_R07',all('If all R01–R07 gates and final saved delivery are complete' in p and 'If R07 remains, finish only saving, external receipt, closure and ownership release' in p for p in [p1,p2]))
    attempt=json.loads(z.read('package-preparation/attempt-01/ATTEMPT.json'))
    old_manifest=json.loads(z.read('package-preparation/attempt-01/MANIFEST-SHA256.json'))['files']
    old_verify=json.loads(z.read('package-preparation/attempt-01/VERIFICATION.json'))
    check('prior_preparation_attempt_honest',attempt['status']=='superseded_before_save' and attempt['save_attempted'] is False and attempt['prior_archive_sha256']==old_verify['archive']['sha256'])
    for n in ['PROMPT-1-CONTINUE.md','PROMPT-2-RECOVER.md']:
        verify('preserved_failed_prompt:'+n,z.read('package-preparation/attempt-01/'+n),old_manifest[n])
    check('failed_prompt1_materially_corrected',z.read('package-preparation/attempt-01/PROMPT-1-CONTINUE.md')!=z.read('PROMPT-1-CONTINUE.md'))

    row_by_source={r['source_relative_path']:r for r in index}
    record_row=row_by_source['evidence/published-checkpoint-checks/CHECKS.json']
    record=json.loads(z.read(record_row['package_path']))
    check('published_checkpoint_fresh_checks',record['source_before']==record['source_after'] and record['source_before']['commit']==SNAPSHOT and record['source_before']['index_tree']==TREE and record['source_before']['unstaged_paths']=='' and record['passed'] and record['inputs_stable'])
    for c in record['checks']:
        r=row_by_source['evidence/published-checkpoint-checks/'+c['log']['path']]
        raw=z.read(r['package_path']) if 'package_path' in r else blob(r['source_revision'],r['repository_path'])
        verify('published_check_log:'+c['name'],raw,c['log']);check('published_check_pass:'+c['name'],c['passed'] and c['exit_code']==0)

verify('frozen_zip_unchanged_after_review',ZIP.read_bytes(),EXPECTED_ZIP)
report={'schema':'ontokin.c268.independent-final-package-review/1','reviewer':'/root/main_evidence_audit','started_at_utc':started,'finished_at_utc':datetime.now(timezone.utc).isoformat(),'verdict':'eligible_for_save' if all(x['passed'] for x in checks) else 'findings','assertion_count':len(checks),'mandatory_findings':[x for x in checks if not x['passed']],'archive':{'filename':ZIP.name,**ident(archive_bytes)},'source_revision':SNAPSHOT,'source_tree':TREE,'payload_files_excluding_manifest':len(inventory),'snapshot_files':len(snapshots),'evidence_index_entries':len(index),'preservation_counts':dict(preservation),'prior_external_files':len(prior['files']),'original_recovery_paths':len(original['changed_files']),'original_bundle':{'path':original['bundle'],'bytes':original['bundle_bytes'],'sha256':original['bundle_sha256'],'prerequisite':MAIN,'head':ORIGINAL},'standalone_prompts':prompts,'early_saved_dependency':{'library_file_id':early['library_file_id'],'bytes':early['bytes'],'sha256':early['sha256'],'url':early['url']},'fresh_extraction_directory':str(extraction),'bundle_verify_command':cmd,'checks':checks,'manual_review':{'read_in_full':['README-START-HERE.md','HANDOFF.md','NEXT-TASK.md','RECOVERY-STATUS.md','PROMPT-1-CONTINUE.md','PROMPT-2-RECOVER.md','recovery/RESTORE.md','package-preparation/attempt-01/ATTEMPT.json'],'judgment':'Coherent online continuation; R01-R06 complete, R07 pending at freeze. Reconcile actual live delivery receipt and closure before work. Complete only remaining delivery or wait for fresh user direction. No future save/receipt/closure represented as observed. Both prompts carry the same bounded instruction.','historical_boundaries':'C262 unchanged; early archive contains identified prior external recovery bytes. Current external bytes have exact retained locations. Original ecce metadata remains historical and is not instructions to overwrite live ownership.'},'scope_limits':['Archive/source/recovery integrity only; no product cohort rerun or release qualification','No network read/write, no uploads, no shared repository/index or frozen-artifact mutation','Bundle identity/prerequisites verified with existing local Git prerequisite; no complete offline reconstruction claimed','Director must still save exact ZIP and prompts, verify save results, publish external receipt, close task/issue, release lease and stop']}
(OUT/'REVIEW.json').write_text(json.dumps(report,indent=2)+'\n')
(OUT/'MANIFEST-COPY.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['verdict','assertion_count','mandatory_findings','payload_files_excluding_manifest','snapshot_files','evidence_index_entries','preservation_counts','prior_external_files']},indent=2))
