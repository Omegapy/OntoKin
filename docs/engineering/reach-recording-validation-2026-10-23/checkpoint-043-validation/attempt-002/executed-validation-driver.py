"""Run only source/evidence metadata and unchanged documentation verification."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,platform,shutil,subprocess,sys,time

BASE=Path('/workspace/scratch/73029ed6994e')
ROOT=BASE/'ontokin-c043'
OUT=BASE/'c043-validation/attempt-002'
OUT.mkdir(parents=True,exist_ok=False)
publication=json.loads((BASE/'c043-core-publication.json').read_text())
tree={r['path']:r for r in json.loads((BASE/'c043-core-tree.json').read_text())['tree']if r['type']=='blob'}

def write(name,obj): (OUT/name).write_text(json.dumps(obj,indent=2)+'\n')
def inventory():
 rows=[]
 for p in sorted(ROOT.rglob('*')):
  if not p.is_file() or '__pycache__' in p.parts:continue
  rel=p.relative_to(ROOT).as_posix();b=p.read_bytes();blob=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();expected=tree.get(rel)
  row={'path':rel,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'git_blob':blob,'physical_mode':oct(p.stat().st_mode&0o777),'published_mode':expected.get('mode')if expected else None,'matches_candidate_blob':bool(expected and expected['sha']==blob and expected['size']==len(b))};rows.append(row)
 assert all(x['matches_candidate_blob']for x in rows),'actual input differs from published candidate'
 return {'files':rows,'file_count':len(rows),'total_bytes':sum(x['bytes']for x in rows),'all_present_files_match_candidate':True,'complete_execution_checkout':False,'candidate_commit':publication['commit'],'candidate_tree':publication['tree']}

shutil.copyfile(__file__,OUT/'executed-validation-driver.py')
shutil.copyfile(BASE/'c043-core-publication.json',OUT/'core-publication.json')
shutil.copyfile(BASE/'c043-core-files.json',OUT/'core-new-files.json')
before=inventory();write('inputs-before.json',before)
commands=[('static-audit',[sys.executable,'docs/engineering/reach-recording-validation-2026-10-23/checkpoint-043-validation/validate-static.py']),('documentation-check',[sys.executable,'docs/maintenance/reorganization-2026-10-17/verify_reorganization.py'])]
results=[]
for name,command in commands:
 start=datetime.now(timezone.utc).isoformat();tick=time.monotonic()
 with (OUT/(name+'.stdout')).open('wb')as stdout,(OUT/(name+'.stderr')).open('wb')as stderr:
  process=subprocess.run(command,cwd=ROOT,stdout=stdout,stderr=stderr,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},timeout=60)
 results.append({'name':name,'command':command,'working_directory':str(ROOT),'started_utc':start,'ended_utc':datetime.now(timezone.utc).isoformat(),'seconds':time.monotonic()-tick,'exit_code':process.returncode,'stdout':name+'.stdout','stderr':name+'.stderr'})
after=inventory();write('inputs-after.json',after)
assert before==after,'source subset changed during metadata verification'
write('receipt.json',{'schema':'ontokin.checkpoint043-validation-execution/0.1','candidate':publication,'environment':{'python':sys.version,'executable':sys.executable,'platform':platform.platform()},'commands':results,'inputs':{'file_count':before['file_count'],'total_bytes':before['total_bytes'],'unchanged':before==after,'all_present_files_match_published_candidate':True,'complete_execution_checkout':False},'product_requests':0,'runtime_tests':0,'recording_runs':0,'numerical_replays':0,'benchmarks':0})
summary={'commands':results,'inputs':{'files':before['file_count'],'bytes':before['total_bytes'],'unchanged':True}}
for name,_ in commands:
 try:
  result=json.loads((OUT/(name+'.stdout')).read_text());summary[name]={k:result[k]for k in ['status','checks_passed','sources_verified','sections_verified','links','failures']if k in result}
 except (ValueError,KeyError):summary[name]={'parseable':False,'stderr':(OUT/(name+'.stderr')).read_text()}
print(json.dumps(summary,indent=2))
