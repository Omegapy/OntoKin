"""Targeted independent mode restoration and recovery-map adjudication.

The initial audit remains intact. This applies the recorded physical modes in
new private inert copies; it does not change ZIP bytes, raw extraction, originals,
source, an oracle, a runtime, Git, or Library.
"""
import base64
import collections
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import zipfile
import zlib

BASE=Path('/workspace/scratch/2ad494d5da19')
OUT=BASE/'session_evidence/final_package_review'
FRESH=OUT/'fresh_extract'


def sha(raw):return hashlib.sha256(raw).hexdigest()


def load(p):return json.loads(p.read_text())


def safe(s):return bool(s) and not PurePosixPath(s).is_absolute() and all(x not in ('','.','..') for x in s.split('/')) and str(PurePosixPath(s))==s and '\\' not in s and '\0' not in s


def fingerprint(p):
    s=p.lstat();raw=p.read_bytes()
    return {'sha256':sha(raw),'bytes':len(raw),'mode':oct(stat.S_IMODE(s.st_mode)),'device':s.st_dev,'inode':s.st_ino,'nlink':s.st_nlink,'mtime_ns':s.st_mtime_ns,'ctime_ns':s.st_ctime_ns}


# RUN001 copies and the entire failed RUN002 attempt remain immutable.
initial=load(OUT/'REVIEW-RUN001.json')
mapping=load(FRESH/'RECOVERY-FILE-MAP.json')
rows=mapping['files'];embedded=[r for r in rows if 'payload_path' in r]
checks=[]


def check(label,okay,details=None):checks.append({'check':label,'pass':bool(okay),'details':details})


check('Initial failure is only the recorded FP12 mode conjunction',len(initial['blocking_findings'])==1 and initial['blocking_findings'][0]['id']=='FP12-complete-exact-recovery-map')
decoded_bad=[];attribute_differences=[];original_before={}
for row in embedded:
    raw=(FRESH/row['payload_path']).read_bytes()
    if len(raw)!=row['bytes'] or sha(raw)!=row['sha256']:decoded_bad.append(row['relative_path'])
    transport_mode=oct(stat.S_IMODE((FRESH/row['payload_path']).stat().st_mode))
    if transport_mode!=row['source_mode']:
        attribute_differences.append({'relative_path':row['relative_path'],'transport_mode':transport_mode,'source_mode':row['source_mode'],'bytes':row['bytes'],'sha256':row['sha256']})
    original_before[row['relative_path']]=fingerprint(BASE/row['relative_path'])
failed_paths=set(initial['blocking_findings'][0]['details']['mismatches'])
check('Every initial FP12 mismatch is exactly a mode-transport difference',not decoded_bad and failed_paths=={r['relative_path'] for r in attribute_differences},{'initial_mismatch_count':len(failed_paths),'mode_difference_count':len(attribute_differences),'byte_mismatches':decoded_bad})
check('Every difference preserves0600 metadata within inert0644 transport',all(r['transport_mode']=='0o644' and r['source_mode']=='0o600' for r in attribute_differences),{'groups':dict(collections.Counter('/'.join(r['relative_path'].split('/')[:3]) for r in attribute_differences))})

destination_root=OUT/'mode_restored_run003';destination_root.mkdir(mode=0o700,exist_ok=False)
restored=[]
for row in embedded:
    if not safe(row['relative_path']) or not safe(row['payload_path']) or row['source_mode'] not in ('0o600','0o644'):
        raise ValueError('Unsafe or unexpected restoration record')
    source=FRESH/row['payload_path'];raw=source.read_bytes()
    if sha(raw)!=row['sha256'] or len(raw)!=row['bytes']:raise ValueError('Source byte mismatch')
    target=destination_root/row['relative_path'];parent=destination_root
    for part in PurePosixPath(row['relative_path']).parts[:-1]:
        parent=parent/part
        if not parent.exists():parent.mkdir(mode=0o700)
        if parent.is_symlink() or not stat.S_ISDIR(parent.lstat().st_mode):raise ValueError('Unsafe private parent')
    mode=int(row['source_mode'],8)
    fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,mode)
    try:
        os.fchmod(fd,mode);offset=0
        while offset<len(raw):offset+=os.write(fd,raw[offset:])
    finally:os.close(fd)
    actual=fingerprint(target)
    okay=stat.S_ISREG(target.lstat().st_mode) and not target.is_symlink() and actual['nlink']==1 and actual['sha256']==row['sha256'] and actual['bytes']==row['bytes'] and actual['mode']==row['source_mode'] and not mode&0o111
    check('Exact private restoration/'+row['relative_path'],okay)
    restored.append({'relative_path':row['relative_path'],'payload_path':row['payload_path'],'bytes':actual['bytes'],'sha256':actual['sha256'],'restored_mode':actual['mode'],'transport_mode':oct(stat.S_IMODE(source.stat().st_mode))})
unchanged=[rel for rel,before in original_before.items() if fingerprint(BASE/rel)!=before]
check('Original813 recovery files unchanged',not unchanged,{'changed':unchanged})
check('Raw extraction retains its recorded ZIP transport modes',all(oct(stat.S_IMODE((FRESH/r['payload_path']).stat().st_mode))=='0o644' for r in embedded))

# Revalidate receipt aliases using their actual documented blob fields. The
# initial audit used previously authenticated member/receipt digests; its unused
# lazy helper guessed data_base64, so that branch is not reused here.
receipt=load(BASE/'incoming/OntoKin/OntoKin_C271_P10_Delivery_Receipt_2026-11-21.json')
receipt_aliases=[r for r in rows if r.get('external_source',{}).get('json_pointer')=='/late_evidence/files']
blob_cache={};receipt_bad=[]
for row in receipt_aliases:
    h=row['external_source']['blob_sha256']
    if h not in blob_cache:
        b=receipt['late_evidence']['blobs'][h]
        if b['encoding']!='zlib+base64':raise ValueError('Unknown exact receipt encoding')
        raw=zlib.decompress(base64.b64decode(b['payload'],validate=True))
        if len(raw)!=b['bytes'] or sha(raw)!=h:raise ValueError('Receipt blob binding differs')
        blob_cache[h]=raw
    raw=blob_cache[h]
    if len(raw)!=row['bytes'] or sha(raw)!=row['sha256']:receipt_bad.append(row['relative_path'])
check('All110 receipt aliases resolve through exact documented compressed blobs',len(receipt_aliases)==110 and not receipt_bad,{'aliases':len(receipt_aliases),'unique_blobs':len(blob_cache),'mismatches':receipt_bad,'prior_intake_not_repeated':'Targeted external mapping mechanism only; no product/host qualification.'})

candidate=destination_root/'session_evidence/loader_design/candidate004'
cm=load(candidate/'CANDIDATE-MANIFEST.json');candidate_bad=[]
# Nine empty supporting logs are exact external aliases rather than embedded rows.
# Resolve only these actual manifest dependencies through their authenticated map.
by_relative={r['relative_path']:r for r in rows}
external_supports=[]
p10=BASE/'incoming/OntoKin/OntoKin_C271_P10_ELF_Mapping_Handoff_2026-11-21.zip'
if p10.stat().st_size!=10556884 or sha(p10.read_bytes())!='42739db560ae8a46706d41ded21038d44a8a8a61ac45d6792374a7e31306c275':raise ValueError('Exact prior archive identity changed')
with zipfile.ZipFile(p10) as prior:
    for entry in cm['payload']+cm['supporting_files']:
        logical=os.path.normpath('session_evidence/loader_design/candidate004/'+entry['path'])
        if not safe(logical):raise ValueError('Unsafe logical support destination')
        row=by_relative[logical]
        if 'payload_path' in row:continue
        source=row['external_source']
        if source['dependency']!='p10_archive' or not safe(source['archive_member']):raise ValueError('Unexpected support dependency')
        raw=prior.read(source['archive_member'])
        if len(raw)!=row['bytes'] or sha(raw)!=row['sha256']:raise ValueError('External support mismatch')
        before=fingerprint(BASE/logical)
        target=destination_root/logical
        if not target.parent.is_dir() or target.parent.is_symlink():raise ValueError('Unsafe support parent')
        mode=int(row['source_mode'],8)
        if mode not in (0o600,0o644):raise ValueError('Unexpected support mode')
        fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,mode)
        try:
            os.fchmod(fd,mode)
            offset=0
            while offset<len(raw):offset+=os.write(fd,raw[offset:])
        finally:os.close(fd)
        actual=fingerprint(target)
        okay=stat.S_ISREG(target.lstat().st_mode) and actual['nlink']==1 and actual['bytes']==row['bytes'] and actual['sha256']==row['sha256'] and actual['mode']==row['source_mode'] and fingerprint(BASE/logical)==before
        check('Exact external candidate support/'+logical,okay)
        external_supports.append({'relative_path':logical,'external_source':source,'bytes':len(raw),'sha256':sha(raw),'restored_mode':actual['mode']})
check('Only nine declared external candidate support aliases materialized',len(external_supports)==9)
for row in cm['payload']+cm['supporting_files']:
    p=candidate/row['path'];raw=p.read_bytes()
    if len(raw)!=row['size_bytes'] or sha(raw)!=row['sha256'] or ('mode' in row and oct(stat.S_IMODE(p.stat().st_mode))!=row['mode']):candidate_bad.append(row['path'])
check('Complete accepted candidate payload/support restored exactly',not candidate_bad and sha((candidate/'CANDIDATE-MANIFEST.json').read_bytes())=='e7b505aa768d0656db6c4dfaf7541e796aefee7148878a6fdf380d6ab0b911de',{'payloads':len(cm['payload']),'supports':len(cm['supporting_files']),'mismatches':candidate_bad})
archive=BASE/'deliverables/final/OntoKin_C271_P11_Loader_Path_Handoff_2026-11-21.zip'
check('Frozen archive unchanged',archive.stat().st_size==5606509 and sha(archive.read_bytes())=='4eddd353047fb8d6aa316544c8b54d655eb53a1613f9c522bbed0edc1ab1249e')

materialization=(candidate/'MATERIALIZATION.md').read_text()
check('Frozen candidate procedure requires recorded mode restoration before consumption','Apply its manifest-recorded inert mode' in materialization and 'verify its exact size, SHA-256 and mode after the copy' in materialization and 'only against the faithful private copy' in materialization)
check('Frozen root documents distinguish recorded modes from transport','Original modes are evidence; ZIP payloads are inert regular files' in (FRESH/'RECOVERY-STATUS.md').read_text() and 'recovery rows separately preserve the original physical modes' in (FRESH/'README-START-HERE.md').read_text())

supplement=BASE/'session_evidence/packaging/final-review-followup/RECOVERY-MODE-RESTORATION.md'
supplement_raw=supplement.read_bytes()
check('Exact concrete receipt supplement covers safe complete restoration',sha(supplement_raw)=='c2ba5026577a11710891dcbb16c040b8cd4748b11a458ae85c37c53f404b52b4' and all(x in supplement_raw.decode() for x in ['813 embedded rows','532','source_mode','single-link','external rows','0700','Do not execute any restored file']))
report={'schema':'ontokin.c271.p11-independent-final-mode-restoration/1','verdict':'pass' if all(c['pass'] for c in checks) else 'fail',
        'check_count':len(checks),'passed':sum(c['pass'] for c in checks),'failed':[c for c in checks if not c['pass']],
        'embedded_restored':len(restored),'external_candidate_supports_restored':len(external_supports),'restoration_root':str(destination_root),'receipt_supplement':{'path':str(supplement),'bytes':len(supplement_raw),'sha256':sha(supplement_raw)},'source_mode_counts':dict(collections.Counter(r['restored_mode'] for r in restored)),
        'initial_attribute_mismatches':len(attribute_differences),'originals_changed':unchanged,'receipt_aliases_checked':len(receipt_aliases),
        'contract_assessment':'The original check incorrectly required transport mode to equal original physical mode. Exact physical modes are recorded separately and the frozen candidate procedure requires restoring them before controls. This follow-up demonstrates every embedded recovery row can be restored exactly without changing the package or original evidence.',
        'instruction_limit':'Root documents do not claim ordinary unzip restores original physical modes and do not spell out a generic chmod command for all recovery rows. The required terminal receipt must clarify application of the existing source_mode map to all recovered files.',
        'required_receipt_supplement':[
          'All ZIP members intentionally have inert0644 transport attributes; automatic unzip is not original-mode restoration.',
          'Recover each row through its payload or exact authenticated external source, then exclusively create a regular nonexecutable copy inside a fresh owned private evidence tree.',
          'Apply that RECOVERY-FILE-MAP row source_mode and verify exact byte count, SHA-256 and resulting mode before consumption; reject unsafe paths, aliases, special files or existing destinations.',
          'Apply GIT-TRANSPORT and accepted MATERIALIZATION instructions as appropriate; never alter originals, repository/runtime files, operational0755 Python pins or frozen expectations.',
          'Identify initial failed FP12 assertion and this successful813-file independent restoration as external postfreeze evidence.'
        ],'product_calls':0,'target_executions':0,'author_validator_calls':0,'Git_or_Library_writes':False}
(OUT/'RESTORATION-CHECKS.json').write_text(json.dumps(checks,indent=2,sort_keys=True)+'\n')
(OUT/'RESTORED-FILES.json').write_text(json.dumps(restored,indent=2,sort_keys=True)+'\n')
(OUT/'EXTERNAL-SUPPORT-RESTORATION.json').write_text(json.dumps(external_supports,indent=2,sort_keys=True)+'\n')
(OUT/'MODE-FOLLOWUP.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps(report,indent=2,sort_keys=True))
raise SystemExit(0 if report['verdict']=='pass' else 1)
