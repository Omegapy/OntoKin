"""Independent review of exact inert Git evidence transport.

Only data is decoded and copied into this reviewer's fresh private directory.
No product code, author helper, original evidence, index, or Git setting changes.
"""
import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess

workspace=Path('/workspace/scratch/2ad494d5da19')
repo=workspace/'OntoKin'
phase=repo/'docs/engineering/localized-repair-c271/loader-path-p11'
out=workspace/'session_evidence/transport_review'
checks=[]


def check(label, condition, detail=None):
    checks.append({'check':label,'pass':bool(condition),'detail':detail})


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def no_duplicates(pairs):
    result={}
    for k,v in pairs:
        if k in result:raise ValueError('Duplicate JSON key: '+k)
        result[k]=v
    return result


def load(p):
    return json.loads(p.read_text(),object_pairs_hook=no_duplicates)


def safe_relative(name):
    return (type(name) is str and bool(name) and not PurePosixPath(name).is_absolute()
            and all(p not in ('','.','..') for p in name.split('/'))
            and '\\' not in name and '\0' not in name and str(PurePosixPath(name))==name)


def identity(p):
    s=p.lstat();raw=p.read_bytes()
    return {'path':str(p),'mode':oct(stat.S_IMODE(s.st_mode)),'size_bytes':len(raw),'sha256':digest(raw),
            'device':s.st_dev,'inode':s.st_ino,'nlink':s.st_nlink,'mtime_ns':s.st_mtime_ns,'ctime_ns':s.st_ctime_ns,
            'regular':stat.S_ISREG(s.st_mode),'symlink':p.is_symlink()}


mapping_path=phase/'GIT-TRANSPORT.json'
instruction_path=phase/'GIT-TRANSPORT.md'
mapping=load(mapping_path)
check('Exact closed mapping shape',set(mapping)=={'schema','created_at_utc','scope','reason','records'} and mapping['schema']=='ontokin.c271.p11-git-evidence-transport/1')
check('Exactly3 unique mapped paths and2 envelopes',len(mapping['records'])==3 and len({r['materialized_relative_path'] for r in mapping['records']})==3 and len({r['envelope_relative_path'] for r in mapping['records']})==2)
expected_paths={'design/candidate004/REVISION-004.diff','review/candidate004/INDEPENDENT-DOCUMENT-DIFF.diff','evidence/technical-candidate/whitespace.stdout.txt'}
check('Only explicitly authorized raw evidence paths',set(r['materialized_relative_path'] for r in mapping['records'])==expected_paths)
if set(r['materialized_relative_path'] for r in mapping['records'])!=expected_paths:
    raise ValueError('Unexpected materialization destination set')
originals_before={}
decoded_records=[]
source_rows={}
for row in mapping['records']:
    check(row['materialized_relative_path']+': closed mapping record',set(row)=={'materialized_relative_path','envelope_relative_path','envelope_sha256','decoded_size_bytes','decoded_sha256','materialized_mode','unaltered_original_recovery_path'})
    check(row['materialized_relative_path']+': normalized safe paths',all(safe_relative(row[k]) for k in ['materialized_relative_path','envelope_relative_path','unaltered_original_recovery_path']))
    if not all(safe_relative(row[k]) for k in ['materialized_relative_path','envelope_relative_path','unaltered_original_recovery_path']):
        raise ValueError('Unsafe transport path')
    envelope_path=phase/row['envelope_relative_path']
    envelope_raw=envelope_path.read_bytes()
    check(row['materialized_relative_path']+': exact envelope hash',digest(envelope_raw)==row['envelope_sha256'])
    envelope=load(envelope_path)
    check(row['materialized_relative_path']+': exact closed envelope fields',set(envelope)=={'schema','encoding','decoded_size_bytes','decoded_sha256','content_base64'})
    check(row['materialized_relative_path']+': exact envelope schema/encoding/types',envelope['schema']=='ontokin.lossless-evidence-envelope/1' and envelope['encoding']=='base64' and type(envelope['decoded_size_bytes']) is int and type(envelope['content_base64']) is str)
    decoded=base64.b64decode(envelope['content_base64'],validate=True)
    check(row['materialized_relative_path']+': canonical strict base64',base64.b64encode(decoded).decode('ascii')==envelope['content_base64'])
    check(row['materialized_relative_path']+': exact decoded binding',len(decoded)==row['decoded_size_bytes']==envelope['decoded_size_bytes'] and digest(decoded)==row['decoded_sha256']==envelope['decoded_sha256'])
    source=workspace/row['unaltered_original_recovery_path']
    before=identity(source);originals_before[row['unaltered_original_recovery_path']]=before
    check(row['materialized_relative_path']+': original recovery bytes and mode equal',source.resolve().is_relative_to(workspace/'session_evidence') and before['regular'] and not before['symlink'] and before['nlink']==1 and source.read_bytes()==decoded and before['mode']==row['materialized_mode']=='0o644')
    check(row['materialized_relative_path']+': no raw transport path in current source',not (phase/row['materialized_relative_path']).exists() and not (phase/row['materialized_relative_path']).is_symlink())
    source_rows[row['materialized_relative_path']]={'mapping':row,'envelope':{'path':str(envelope_path),'size_bytes':len(envelope_raw),'sha256':digest(envelope_raw)},'decoded_sha256':digest(decoded),'decoded_size_bytes':len(decoded)}
    decoded_records.append((row,decoded))

candidate=workspace/'session_evidence/loader_design/candidate004/CANDIDATE-MANIFEST.json'
candidate_before=identity(candidate)
check('Original accepted candidate manifest unchanged',candidate_before['sha256']=='e7b505aa768d0656db6c4dfaf7541e796aefee7148878a6fdf380d6ab0b911de' and candidate_before['size_bytes']==35041)
canonical_candidate=phase/'design/candidate004/CANDIDATE-MANIFEST.json'
check('Git-transported candidate manifest byte-identical',canonical_candidate.read_bytes()==candidate.read_bytes())
raw_candidate_binding=next(r for r in load(candidate)['payload'] if r['path']=='REVISION-004.diff')
candidate_row=next(r for r in mapping['records'] if r['materialized_relative_path'].startswith('design/'))
check('Decoded candidate diff agrees with independently accepted frozen payload binding',raw_candidate_binding['sha256']==candidate_row['decoded_sha256'] and raw_candidate_binding['size_bytes']==candidate_row['decoded_size_bytes'] and raw_candidate_binding['mode']==candidate_row['materialized_mode'])
check('Independent reviewer diff and author diff use same exact byte identity',decoded_records[0][1]==decoded_records[1][1] and candidate_row['decoded_sha256']=='2c08bfced30e1ddbf6f4584d8c5081db817aa3b8c5f68c4144265be1d1e5b417')
oracle=workspace/'session_evidence/loader_design/candidate004/EXPECTATIONS.json'
oracle_before=identity(oracle)
check('Frozen accepted oracle unchanged',oracle_before['sha256']=='dfb285f41a58a1f7254aaae4aa022f91afdc72fb7d5dad2f3d6b1e8257d14137')
check('Repository oracle byte-identical',(phase/'design/candidate004/EXPECTATIONS.json').read_bytes()==oracle.read_bytes())

# Demonstrate strict, exclusive restoration under the assigned review root.
materialized=out/'fresh_materialized'
materialized.mkdir(mode=0o700,exist_ok=False)
receipts=[]
for row,decoded in decoded_records:
    destination=materialized/row['materialized_relative_path']
    current=materialized
    for component in PurePosixPath(row['materialized_relative_path']).parts[:-1]:
        current=current/component
        if not current.exists():current.mkdir(mode=0o700)
        s=current.lstat()
        if current.is_symlink() or not stat.S_ISDIR(s.st_mode):raise ValueError('Unsafe private parent')
    fd=os.open(destination,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o644)
    try:
        os.fchmod(fd,0o644)
        pos=0
        while pos<len(decoded):pos+=os.write(fd,decoded[pos:])
    finally:os.close(fd)
    actual=identity(destination)
    check(row['materialized_relative_path']+': fresh exact regular nonexecutable restoration',actual['regular'] and not actual['symlink'] and actual['nlink']==1 and actual['mode']=='0o644' and actual['sha256']==row['decoded_sha256'] and actual['size_bytes']==row['decoded_size_bytes'] and destination.read_bytes()==decoded)
    receipts.append({'materialized':actual,'reproducible_from':row['unaltered_original_recovery_path'],'envelope':row['envelope_relative_path']})
for name,before in originals_before.items():
    check(name+': raw original identity/mode/bytes unchanged',identity(workspace/name)==before)
check('Candidate manifest and oracle unchanged after restoration',identity(candidate)==candidate_before and identity(oracle)==oracle_before)

instructions=instruction_path.read_text()
check('Instruction requires authenticated exact schema and decoded binding','exact reviewed Git revision' in instructions and 'exact closed envelope schema' in instructions and 'decode it strictly' in instructions and 'adopted candidate manifest' in instructions)
check('Instruction rejects unsafe/restored existing paths','Reject absolute paths, empty/parent components, symlink traversal, hardlinks, special files and existing destinations' in instructions and 'fresh owned private evidence tree' in instructions)
check('Instruction preserves full candidate materialization and external receipt','design/candidate004/MATERIALIZATION.md' in instructions and 'Record materialization outside the frozen payload' in instructions)
check('Instruction explicitly does not waive Git guard or grant execution','no Git whitespace option or attribute is weakened' in instructions and 'does not grant execution authority' in instructions)

# Read-only Git observations: ordinary guard, settings and staged control paths.
git_records=[]
commands=[['git','diff','--cached','--check'],['git','diff','--cached','--name-only'],['git','config','--get','core.whitespace'],['git','check-attr','whitespace','--',*[str((phase/r['envelope_relative_path']).relative_to(repo)) for r in mapping['records']]]]
for index,argv in enumerate(commands):
    p=subprocess.run(argv,cwd=repo,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
    stdout=out/('git-read-'+str(index)+'.stdout.txt');stderr=out/('git-read-'+str(index)+'.stderr.txt')
    stdout.write_bytes(p.stdout);stderr.write_bytes(p.stderr)
    git_records.append({'argv':argv,'exit_code':p.returncode,'stdout':str(stdout),'stderr':str(stderr),'stdout_sha256':digest(p.stdout),'stderr_sha256':digest(p.stderr)})
    if index==0:check('Ordinary git diff --cached --check passes without options disabling whitespace',p.returncode==0 and not p.stdout and not p.stderr)
    if index==1:
        names=p.stdout.decode().splitlines()
        check('No staged whitespace attribute or repository policy waiver',p.returncode==0 and not any(PurePosixPath(n).name in ('.gitattributes','.gitconfig') for n in names))
    if index==2:check('No configured core.whitespace weakening observed',p.returncode==1 and not p.stdout or p.returncode==0 and not any(x in p.stdout.decode().split(',') for x in ('-trailing-space','-blank-at-eol','-blank-at-eof')))
    if index==3:check('Envelope paths do not carry whitespace suppression attributes',p.returncode==0 and all(line.endswith(': whitespace: unspecified') for line in p.stdout.decode().splitlines()))

root_provenance=load(workspace/'session_evidence/ROOT-TRANSPORT-VERIFICATION.json')
check('Root provenance references same exact records',root_provenance['records']==mapping['records'] and root_provenance['candidate_manifest_sha256']==candidate_before['sha256'])
report={'schema':'ontokin.c271.p11-independent-git-transport-review/1','verdict':'pass' if all(c['pass'] for c in checks) else 'fail',
        'reviewer':'/root/intake_audit','mapping':identity(mapping_path),'instructions':identity(instruction_path),
        'check_count':len(checks),'passed':sum(c['pass'] for c in checks),'failed':[c for c in checks if not c['pass']],
        'records':source_rows,'fresh_materialization':receipts,'git_observations':git_records,
        'candidate_manifest_sha256':candidate_before['sha256'],'oracle_sha256':oracle_before['sha256'],
        'execution_scope':'Reviewer static decoding/copy and read-only Git guard observations only; no product code/tests or target execution.',
        'originals_modified':False,'git_or_config_writes':False,
        'derived_materialized_files':'Exact reproducible copies; keep in recovery or map to original raw sources, do not blindly copy these raw whitespace-bearing files into Git.'}
(out/'CHECKS.json').write_text(json.dumps(checks,indent=2,sort_keys=True)+'\n')
(out/'REVIEW.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('records','fresh_materialization','git_observations')},indent=2,sort_keys=True))
raise SystemExit(0 if report['verdict']=='pass' else 1)
