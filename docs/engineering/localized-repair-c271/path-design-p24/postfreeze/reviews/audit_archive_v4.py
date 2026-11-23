from pathlib import Path,PurePosixPath
from collections import Counter
import hashlib,io,json,os,stat,subprocess,sys,zipfile,datetime
BASE=Path('/workspace/scratch/660f372e2414/reviews/recovery')
REPO=Path('/workspace/scratch/660f372e2414/OntoKin')
p=Path(sys.argv[1])
label=sys.argv[2] if len(sys.argv)>2 else 'amendment'
expected_hash=sys.argv[3] if len(sys.argv)>3 else None
expected_bytes=int(sys.argv[4]) if len(sys.argv)>4 else None
r={'schema':'ontokin.c271.p24.independent-archive-audit/1','reviewer':'/root/recovery_audit','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'archive':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'expected_bytes':expected_bytes,'expected_sha256':expected_hash,'failures':[],'limits':[],'nested_archives':[]}
if expected_hash and r['sha256']!=expected_hash:r['failures'].append('archive SHA256 mismatch')
if expected_bytes and r['bytes']!=expected_bytes:r['failures'].append('archive byte count mismatch')

def digest(b):return hashlib.sha256(b).hexdigest()
def audit_zip(z,loc):
 infos=z.infolist();names=[i.filename for i in infos];bad=[]
 for i in infos:
  pp=PurePosixPath(i.filename)
  if pp.is_absolute() or '..' in pp.parts or '\\' in i.filename or ':' in pp.parts[0] or '\x00' in i.filename or any(x in ['', '.'] for x in i.filename.split('/')) or stat.S_ISLNK(i.external_attr>>16):bad.append(i.filename)
 out={'location':loc,'entry_count':len(infos),'safe_path_failures':bad,'duplicate_names':[n for n,c in Counter(names).items() if c>1],'crc_first_failure':z.testzip()}
 if 'MANIFEST-SHA256.json' in names:
  m=json.loads(z.read('MANIFEST-SHA256.json'));items=m if isinstance(m,list) else m.get('files',m.get('entries',[]));keys=[];fail=[]
  for x in items:
   n=x.get('path',x.get('member'));keys.append(n)
   if n not in names:fail.append({'path':n,'issue':'missing'});continue
   b=z.read(n)
   if len(b)!=x.get('bytes',x.get('size')) or digest(b)!=x['sha256']:fail.append({'path':n,'issue':'identity mismatch'})
  out.update(manifest_entries=len(items),manifest_failures=fail,manifest_duplicates=[n for n,c in Counter(keys).items() if c>1],manifest_unlisted=sorted(set(names)-{'MANIFEST-SHA256.json'}-set(keys)),manifest_extra=sorted(set(keys)-set(names)))
 else:out['manifest_absent']=True
 for k in ['safe_path_failures','duplicate_names','crc_first_failure','manifest_failures','manifest_duplicates','manifest_unlisted','manifest_extra']:
  if out.get(k):r['failures'].append({'zip':loc,'check':k,'detail':out[k]})
 return out
with zipfile.ZipFile(p) as z:
 r['top_level']=audit_zip(z,'archive')
 if r['top_level']['safe_path_failures'] or r['top_level']['duplicate_names']:raise RuntimeError('unsafe archive')
 dest=BASE/(label+'-extracted')
 dest.mkdir(exist_ok=False)
 z.extractall(dest)
 r['fresh_extraction']=str(dest)
 mismatch=[]
 for i in z.infolist():
  if i.is_dir():continue
  if (dest/i.filename).read_bytes()!=z.read(i.filename):mismatch.append(i.filename)
 r['extracted_byte_checks']=len(z.infolist());r['extracted_mismatches']=mismatch
 r['extracted_inventory_exact']={q.relative_to(dest).as_posix() for q in dest.rglob('*') if q.is_file()}=={i.filename for i in z.infolist() if not i.is_dir()}
 if not r['extracted_inventory_exact']:r['failures'].append('fresh extracted inventory mismatch')
 if mismatch:r['failures'].append('extracted bytes mismatch')
 src=json.loads(z.read('SOURCE-MANIFEST.json')) if 'SOURCE-MANIFEST.json' in z.namelist() else {}
 source_results=[]
 for x in src.get('files',[]):
  member=x.get('member',x.get('path'));source=x.get('repository_path',x.get('path'));commit=x.get('commit');o={'member':member,'commit':commit,'source_path':source,'declared_git_blob':x.get('git_blob')}
  b=z.read(member)
  o['archive_identity_matches']=len(b)==x['bytes'] and digest(b)==x['sha256']
  if commit and source:
   proc=subprocess.run(['git','-C',str(REPO),'cat-file','blob',commit+':'+source],capture_output=True)
   o['git_returncode']=proc.returncode
   if proc.returncode==0:
    o['source_bytes_match']=proc.stdout==b
    blob=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
    o['computed_git_blob']=blob;o['blob_matches']=not x.get('git_blob') or x.get('git_blob')==blob
   else:o['git_stderr']=proc.stderr.decode(errors='replace');o['source_bytes_match']=None;r['limits'].append({'member':member,'issue':'source object unavailable'})
  source_results.append(o)
  if not o['archive_identity_matches'] or o.get('source_bytes_match') is False or o.get('blob_matches') is False:r['failures'].append({'source_binding':o})
 r['source_bindings']={'count':len(source_results),'archive_identity_pass':sum(x['archive_identity_matches'] for x in source_results),'git_byte_pass':sum(x.get('source_bytes_match') is True for x in source_results),'unavailable':sum(x.get('source_bytes_match') is None for x in source_results),'results':source_results}
 rec=json.loads(z.read('RECOVERY-MANIFEST.json')) if 'RECOVERY-MANIFEST.json' in z.namelist() else {}
 checks=[]
 for x in rec.get('files',[]):
  member=x.get('member',x.get('archive_member'));b=z.read(member);passed=len(b)==x['bytes'] and digest(b)==x['sha256']
  checks.append({'member':member,'original_path':x.get('original_path',x.get('workspace_relative_path')),'declared_mode':x.get('mode',x.get('original_mode')),'bytes':len(b),'sha256':digest(b),'passed':passed})
  if not passed:r['failures'].append({'recovery_mapping':member})
 r['recovery_mappings']={'count':len(checks),'passed':sum(x['passed'] for x in checks),'results':checks}
 for i in z.infolist():
  if i.filename.endswith('.zip'):
   b=z.read(i.filename)
   prior_reports=['amendment-attempt002-archive-audit.json','early-attempt001-archive-audit.json','early-attempt002-archive-audit.json']
   matched=None
   for report_name in prior_reports:
    prior=json.loads((BASE/report_name).read_bytes())
    if prior['sha256']==digest(b) and prior['bytes']==len(b) and not prior['failures']:
     matched={'location':i.filename,'bytes':len(b),'sha256':digest(b),'mechanical_integrity_reused_from':report_name,'prior_report_sha256':digest((BASE/report_name).read_bytes()),'prior_top_level':prior['top_level'],'limit':'Exact archive-byte equality reuses prior integrity/source checks only; rejected early attempt001 remains rejected for its historical text findings.'}
     break
   if matched is not None:r['nested_archives'].append(matched)
   else:
    with zipfile.ZipFile(io.BytesIO(b)) as nested:
     nested_result=audit_zip(nested,i.filename)
     nested_result.update(bytes=len(b),sha256=digest(b));r['nested_archives'].append(nested_result)
 if 'AMENDMENT.json' in z.namelist():
  a=json.loads(z.read('AMENDMENT.json'));r['amendment']=a
  r['limits'].append('Original P23 predecessor ZIP bytes were not supplied to this reviewer; no direct whole-predecessor byte comparison claimed. Frozen Git-bound bytes and embedded predecessor archive were verified independently.')
  r['source_bound_preserved_regions']={'repository_members':len([n for n in z.namelist() if n.startswith('repository/')]),'source_bindings':len(source_results)}
 r['required_root_files']={n:n in z.namelist() for n in ['README-START-HERE.md','CHECKPOINT.json','HANDOFF.md','NEXT-TASK.md','RECOVERY-STATUS.md','PROMPT-1-CONTINUE.md','PROMPT-2-RECOVER.md','HISTORICAL-DEPENDENCIES.json','MANIFEST-SHA256.json','HOST-ENVIRONMENT.md']}
 if not all(r['required_root_files'].values()):r['failures'].append('required roots missing')
r['verdict']='PASS_WITH_STATED_LIMITS' if not r['failures'] else 'FAIL'
(BASE/(label+'-archive-audit.json')).write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({k:v for k,v in r.items() if k not in ['source_bindings','recovery_mappings','amendment']}|{'source_bindings_summary':{k:v for k,v in r['source_bindings'].items() if k!='results'},'recovery_mappings_summary':{k:v for k,v in r['recovery_mappings'].items() if k!='results'}},indent=2))
