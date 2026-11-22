"""Audit only new final saved-file identities/readbacks; no ZIP requalification."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import sys
import zipfile

B = Path('/workspace/scratch/816157c5a30b')
O = B / 'recovery_audit'
checks, readset = [], []

def sha(data):
    return hashlib.sha256(data).hexdigest()

def read(path, purpose):
    data = path.read_bytes()
    readset.append({'path': str(path), 'bytes': len(data), 'sha256': sha(data), 'purpose': purpose})
    return data

def load(path, purpose):
    return json.loads(read(path, purpose))

def check(name, condition, detail=None):
    checks.append({'check': name, 'passed': bool(condition), 'detail': detail})

def attrs(path):
    return {name: os.getxattr(path, name).decode() for name in os.listxattr(path) if name in ('user.library-file-id', 'user.library-file-version')}

receipt = load(B/'state/FINAL-SAVE-RECEIPT.json', 'New saved-artifact receipt')
result = load(B/'state/FINAL-UPLOAD-RESULT.json', 'New upload execution result')
response = load(B/'state/FINAL-UPLOAD-RESPONSE.json', 'Actual returned creation identities')
folder = load(B/'state/FINAL-FOLDER-METADATA.json', 'Actual folder listing for the three target artifacts')
materialize = load(B/'state/FINAL-MATERIALIZE.json', 'Actual materialization identities and outcomes')
accepted = load(O/'FINAL-REVIEW.json', 'Reuse accepted immutable artifact identities only; no repeat of prior archive checks')
expected = {f['role']: f for f in accepted['external_artifacts']}
check('exact_three_roles', len(receipt['artifacts'])==3 and {f['role'] for f in receipt['artifacts']}==set(expected))
check('three_distinct_returned_identities', len(response['results'])==3 and len({f['library_file_id'] for f in response['results']})==3 and len({f['file_id'] for f in response['results']})==3)
check('single_successful_recorded_batch_no_retry', result['returncode']==0 and result['single_ordered_batch'] and result['retry'] is False and receipt['single_ordered_save_batch'] and receipt['retries']==0)
check('expected_folder_name', receipt['folder']=='OntoKin' and receipt['directory_id']=='libdir_fde3_dl-6ad29e65bf148191aef327539199fc34_2ab2a24d43748191957f9bcc356b59de')
check('prior_archive_acceptance_reused', accepted['verdict']=='accepted' and accepted['passed_groups']==58 and not accepted['mandatory_findings'])
rows=[]
zip_path=Path(expected['handoff_zip']['local_path'])
with zipfile.ZipFile(zip_path) as z:
    for item in receipt['artifacts']:
        role=item['role'];exp=expected[role]
        local=Path(item['local_path']);back=Path(item['readback_path'])
        local_bytes=read(local,'Accepted artifact after save: identity comparison only')
        back_bytes=read(back,'Actual materialized saved bytes')
        local_attrs=attrs(local);back_attrs=attrs(back)
        creations=[f for f in response['results'] if f['library_file_id']==item['library_file_id']]
        listings=[f for f in folder['items'] if f.get('library_file_id')==item['library_file_id']]
        transfers=[f for f in materialize['transfers'] if f['library_file_id']==item['library_file_id']]
        requests=[f for f in result['artifacts'] if f['role']==role]
        check(role+'_exact_receipt_metadata_cardinality', len(creations)==len(listings)==len(transfers)==len(requests)==1)
        created,listed,transfer,requested=creations[0],listings[0],transfers[0],requests[0]
        check(role+'_accepted_identity_unchanged', all(item[k]==exp[k] and requested[k]==exp[k] for k in ('bytes','sha256')) and item['local_path']==exp['local_path'])
        check(role+'_local_and_readback_bytes', local_bytes==back_bytes and len(local_bytes)==item['bytes'] and sha(local_bytes)==item['sha256'] and len(back_bytes)==item['bytes'] and sha(back_bytes)==item['sha256'])
        check(role+'_actual_creation_response', all(created[k]==item[k] for k in ('file_id','library_file_id','file_name','path','local_path')) and created['status']=='succeeded' and created['purpose']=='create_library_file' and created['local_metadata_applied'] is True)
        check(role+'_folder_listing_identity_size_version', all(listed[k]==item[k] for k in ('file_id','library_file_id','path')) and listed['name']==item['file_name']==local.name==back.name and listed['size_bytes']==item['bytes'] and listed['path']=='/OntoKin/'+item['file_name'] and listed['version_id']=='0')
        check(role+'_all_version_zero', item['version']==item['current_version_number']==created['current_version_number']==transfer['current_version_number']==0)
        check(role+'_materialization_binding', all(transfer[k]==item[k] for k in ('file_id','library_file_id','file_name')) and transfer['workspace_path']==str(back) and transfer['size_bytes']==item['bytes'] and transfer['expected_sha256']==item['sha256'] and transfer['helper_returncode']==0 and transfer['method']=='GET')
        check(role+'_local_and_readback_library_xattrs', local_attrs==back_attrs=={'user.library-file-version':'0','user.library-file-id':item['library_file_id']})
        check(role+'_receipt_url_and_readback_claims', item['url']=='https://chatgpt.com/library?file_id='+item['library_file_id']+'&account_id=personal' and item['saved_bytes_readback_equal'] and item['local_bytes_unchanged_after_save'] and item['readback_metadata_applied'] and item['folder_metadata_verified'])
        prompt_equal=None
        if role!='handoff_zip':
            prompt_equal=local_bytes==back_bytes==z.read(item['matching_zip_member'])
            check(role+'_prompt_matches_accepted_ZIP_member', prompt_equal and item['matching_zip_member']==exp['matching_zip_member'])
        else:
            check('assigned_saved_zip_library_identity', item['library_file_id']=='libfile_fde3_f-5b9681f90a808191843b35644ad3e218_2ab2a24d43748191957f9bcc356b59de')
            check('saved_zip_source_identity', item['source_revision']==accepted['source_revision'] and item['source_tree']==accepted['source_tree'])
        rows.append({'role':role,'file_name':item['file_name'],'file_id':item['file_id'],'library_file_id':item['library_file_id'],'version':item['version'],'path':item['path'],'url':item['url'],'bytes':len(back_bytes),'sha256':sha(back_bytes),'local_path':str(local),'readback_path':str(back),'local_xattrs':local_attrs,'readback_xattrs':back_attrs,'prompt_zip_equal':prompt_equal,'creation_response':created,'folder_metadata':listed,'materialization_metadata':transfer})

failures=[c for c in checks if not c['passed']]
report={'schema':'ontokin.c271.p19-independent-saved-artifacts-review/1','auditor':'/root/recovery_audit','reviewed_at_utc':datetime.now(timezone.utc).isoformat(),'verdict':'accepted_saved_artifact_bindings' if not failures else 'rejected','passed_groups':sum(c['passed'] for c in checks),'mandatory_findings':failures,'checks':checks,'saved_artifacts':rows,'source_revision':accepted['source_revision'],'source_tree':accepted['source_tree'],'accepted_archive_review':{'path':'recovery_audit/FINAL-REVIEW.json','sha256':sha((O/'FINAL-REVIEW.json').read_bytes()),'groups':58,'reused_without_internal_reaudit':True},'folder':receipt['folder'],'directory_id':receipt['directory_id'],'folder_listing_limit':'Exact three target entries independently verified. Listing pagination is not claimed complete or needed for these exact identities.','pending':['Final Git receipt publication and readback','Any required postfreeze recovery-delta/receipt save and exact readback','Matching terminal PR274/issue273 confirmation and final phase disposition'],'parent_complete':False,'readset':readset,'execution':{'executable':sys.executable,'python':sys.version,'argv':sys.argv,'script_sha256':sha(Path(__file__).read_bytes())},'limits':['Only new saved-artifact bindings and readback bytes audited.','No unchanged archive-internal requalification, technical work, product/host rerun or Git mutation.','No Library operation by this worker; actual returned metadata and local readbacks were inspected.','Saved ZIP/prompts do not alone establish completion of remaining receipt/terminal gates.']}
(O/'SAVED-ARTIFACTS-REVIEW.json').write_text(json.dumps(report,indent=2)+'\n')
md=['# P19 saved-artifact independent review','','Verdict: **'+report['verdict']+'**. '+str(report['passed_groups'])+' checks passed; '+str(len(failures))+' mandatory findings.','','All three artifacts are present in `/OntoKin/` at version 0. Actual creation responses, folder entries, materialization records, local/readback Library IDs and version xattrs agree. Every materialized file is byte-identical to its accepted local artifact and matches the accepted size and SHA-256. Both prompt files also match their exact accepted ZIP members.','','| Artifact | Bytes | Library identity |','| --- | ---: | --- |']
for row in rows:
    md.append('| '+row['role']+' | '+str(row['bytes'])+' | `'+row['library_file_id']+'` |')
md += ['','ZIP SHA-256: `'+accepted['archive']['sha256']+'`. Source: `'+accepted['source_revision']+'`; tree: `'+accepted['source_tree']+'`.','','The prior 58-group archive acceptance is reused. This review reads only the two required prompt members from the ZIP and compares complete file identities; unchanged ZIP internals and technical evidence were not re-audited. No product or host work ran. No Git, canonical-file or Library mutation occurred.','','**Final Git receipt publication/readback and terminal confirmation remain pending.** This review confirms the saved ZIP/prompt bindings only; it does not close the parent task or the remaining delivery gates. Preserve this review and its independent script in the pending canonical evidence or compact recovery delta.','','Detailed bindings, actual xattrs, source hashes and input read-set are in `SAVED-ARTIFACTS-REVIEW.json`. Audit source: `audit_saved_artifacts.py`; Python standard library only.','']
(O/'SAVED-ARTIFACTS-REVIEW.md').write_text('\n'.join(md))
print(json.dumps({'verdict':report['verdict'],'passed_groups':report['passed_groups'],'mandatory_findings':failures,'artifacts':[{'role':r['role'],'library_file_id':r['library_file_id'],'version':r['version'],'bytes':r['bytes'],'sha256':r['sha256']} for r in rows],'pending':report['pending']},indent=2))
