"""Privately materialize authenticated frozen evidence; execute no payload."""
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess

ROOT=Path('/workspace/scratch/378b783967ca')
REPO=ROOT/'OntoKin'
OUT=ROOT/'session_p12/review'
DEST=OUT/'private-corpus'
REV='79292cf456df6e0f49524fcb1fcfd1fd2f7b08ae'
P11='docs/engineering/localized-repair-c271/loader-path-p11/'
MANIFEST=P11+'design/candidate004/CANDIDATE-MANIFEST.json'
PIN='e7b505aa768d0656db6c4dfaf7541e796aefee7148878a6fdf380d6ab0b911de'

def sha(data):return hashlib.sha256(data).hexdigest()
def git_bytes(path):return subprocess.run(['git','show',f'{REV}:{path}'],cwd=REPO,capture_output=True,check=True).stdout
def safe(path):return bool(path) and not path.startswith('/') and '\\' not in path and ':' not in path and all(x not in ('','.','..') for x in path.split('/')) and str(PurePosixPath(path))==path

manifest_raw=git_bytes(MANIFEST)
if sha(manifest_raw)!=PIN:raise ValueError('Unaccepted manifest')
manifest=json.loads(manifest_raw)
mapping_raw=git_bytes(P11+'GIT-TRANSPORT.json')
mapping=json.loads(mapping_raw)
transports={P11+x['materialized_relative_path']:x for x in mapping['records']}
git_paths=set(subprocess.run(['git','ls-tree','-r','--name-only',REV],cwd=REPO,capture_output=True,check=True,text=True).stdout.splitlines())
pending=[]
for role,rows in [('payload',manifest['payload']),('support',manifest['supporting_files'])]:
 for row in rows:
  if role=='payload':
   if not safe(row['path']):raise ValueError('Unsafe payload path')
   relative='candidate004/'+row['path']
  else:
   if not row['path'].startswith('../') or not safe(row['path'][3:]):raise ValueError('Unsupported explicit sibling path')
   relative=row['path'][3:]
  source=P11+'design/'+relative
  transport=None
  if source in git_paths:data=git_bytes(source)
  else:
   transport=transports[source]
   envelope_path=P11+transport['envelope_relative_path']
   encoded=git_bytes(envelope_path)
   if sha(encoded)!=transport['envelope_sha256']:raise ValueError('Envelope identity mismatch')
   envelope=json.loads(encoded)
   if set(envelope)!={'schema','encoding','decoded_size_bytes','decoded_sha256','content_base64'} or envelope['schema']!='ontokin.lossless-evidence-envelope/1' or envelope['encoding']!='base64':raise ValueError('Envelope shape mismatch')
   data=base64.b64decode(envelope['content_base64'],validate=True)
   if len(data)!=transport['decoded_size_bytes'] or sha(data)!=transport['decoded_sha256'] or len(data)!=envelope['decoded_size_bytes'] or sha(data)!=envelope['decoded_sha256']:raise ValueError('Decoded envelope mismatch')
  if len(data)!=row['size_bytes'] or sha(data)!=row['sha256']:raise ValueError('Manifest content mismatch: '+row['path'])
  mode=int(row.get('mode','0o644'),8)
  if mode not in (0o600,0o644):raise ValueError('Noninert recorded mode')
  pending.append({'role':role,'manifest_path':row['path'],'relative_path':relative,'source_revision':REV,'source_path':source,'bytes':len(data),'sha256':sha(data),'mode':oct(mode),'transport':transport,'data':data})
if len({x['relative_path'] for x in pending})!=len(pending):raise ValueError('Duplicate destination')
DEST.mkdir(mode=0o700);DEST.chmod(0o700)
for row in pending:
 p=DEST/row['relative_path'];p.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
 with p.open('xb') as stream:stream.write(row['data'])
 p.chmod(int(row['mode'],8))
 s=p.lstat()
 if not stat.S_ISREG(s.st_mode) or s.st_nlink!=1 or stat.S_IMODE(s.st_mode)!=int(row['mode'],8) or p.read_bytes()!=row['data']:raise ValueError('Restoration mismatch')
 row['restored_verified']=True
 del row['data']
p=DEST/'candidate004/CANDIDATE-MANIFEST.json'
with p.open('xb') as stream:stream.write(manifest_raw)
p.chmod(0o644)
receipt={'schema':'ontokin.c271.p12-independent-corpus-materialization/1','reviewer':'/root/intake_review','completed_at_utc':datetime.now(timezone.utc).isoformat(),'source_revision':REV,'manifest':{'path':MANIFEST,'bytes':len(manifest_raw),'sha256':sha(manifest_raw)},'transport_mapping':{'path':P11+'GIT-TRANSPORT.json','bytes':len(mapping_raw),'sha256':sha(mapping_raw)},'destination':str(DEST),'destination_mode':'0o700','payloads':len(manifest['payload']),'supports':len(manifest['supporting_files']),'manifest_also_copied':True,'cases':len(json.loads((DEST/'candidate004/EXPECTATIONS.json').read_text())['cases']),'files':pending,'payload_execution':False,'production_imports':False,'original_paths_written':False,'logical_exceptional_files_created':False,'status':'passed','limits':['Only exact candidate004 payloads and explicit supporting-file bindings materialized; retained prior attempts remain at authenticated Git/archive sources.','No static author checker, product test, source runtime, host observation or policy adapter was executed.']}
(OUT/'MATERIALIZATION-RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:receipt[k] for k in ['status','payloads','supports','cases','destination']},indent=2))
