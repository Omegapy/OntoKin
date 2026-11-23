from pathlib import Path
import datetime, hashlib, json, os, zipfile

ROOT = Path(__file__).resolve().parents[2]
uploaded = json.loads((ROOT/'records/FINAL-UPLOAD-RESULT.json').read_text())
materialized = json.loads((ROOT/'records/FINAL-MATERIALIZATION-METADATA.json').read_text())
build = json.loads((ROOT/'packages/final/BUILD-RESULT.json').read_text())
assert len(uploaded['results']) == len(materialized['transfers']) == 3
assert not materialized['unavailable_items']
by_id = {row['library_file_id']:row for row in materialized['transfers']}
assert len(by_id) == 3
rows=[]
for item in uploaded['results']:
    assert item['status']=='succeeded'
    assert item['path']=='/OntoKin/'+item['file_name']
    transfer=by_id[item['library_file_id']]
    for key in ['file_id','library_file_id','file_name','current_version_number']:
        assert transfer[key]==item[key]
    local=Path(item['local_path']); remote=Path(transfer['workspace_path'])
    data=local.read_bytes(); returned=remote.read_bytes()
    assert data==returned and len(data)==transfer['size_bytes']
    assert os.getxattr(remote,'user.library-file-id').decode()==item['library_file_id']
    assert os.getxattr(remote,'user.library-file-version').decode()==str(item['current_version_number'])
    row={**item,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),
        'version':item['current_version_number'],'readback_path':str(remote),
        'saved_bytes_readback_equal':True,'stable_id_version_attributes_verified':True,
        'backing_id_verified_against_materialize_response':True,
        'url':'https://chatgpt.com/library?file_id='+item['library_file_id']+'&account_id=personal'}
    rows.append(row)
archive=next(row for row in rows if row['file_name'].endswith('.zip'))
assert archive['sha256']==build['sha256'] and archive['bytes']==build['bytes']
prompts=[]
with zipfile.ZipFile(archive['local_path']) as z:
    for row in rows:
        if row is archive:continue
        member='PROMPT-1-CONTINUE.md' if '_Continue_' in row['file_name'] else 'PROMPT-2-RECOVER.md'
        assert Path(row['readback_path']).read_bytes()==z.read(member)
        row.update({'zip_member':member,'matches_zip_member':True})
        prompts.append(row)
result={'schema':'ontokin.c271.p24-final-save-readback/1',
    'status':'zip_and_prompts_saved_and_exact_readback_verified',
    'confirmed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'source_commit':build['source_commit'],'source_tree':build['source_tree'],
    'archive':archive,'matching_prompts':prompts,
    'archive_members':build['members'],'source_bindings':build['source_bindings'],
    'independent_archive_review':'reviews/recovery/FINAL-ARCHIVE-REVIEW.json',
    'current_unknown_operations':[],
    'local_parse_incident':uploaded['local_parse_incident'],
    'limits':'Final external receipt publication/save and matching terminal markers remain pending. No technical or parent-completion gate is passed by delivery.'}
(ROOT/'records/FINAL-SAVE-READBACK.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':result['status'],'files':len(rows),'archive_library_file_id':archive['library_file_id'],'sha256':archive['sha256']}))
