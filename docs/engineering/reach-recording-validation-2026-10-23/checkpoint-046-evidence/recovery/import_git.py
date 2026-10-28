#!/usr/bin/env python3
"""Import only cryptographically verified published Git objects; no product code."""
import datetime, hashlib, json, pathlib, subprocess, zlib
ROOT=pathlib.Path('/workspace/scratch/fd65650eb54f/OntoKin')
META=pathlib.Path('/workspace/scratch/fd65650eb54f/c046-recovery')
REMOTE=json.loads((META/'remote-tree.json').read_text())
SOURCE='a5bb1e674e4ae3eb1d77e83b63f7a809eacf0bd0'
def git(*args,input=None):
    result=subprocess.run(['git','-C',str(ROOT),*args],input=input,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
    return result.stdout.decode()
git('init','--quiet')
objects=ROOT/'.git/objects'
def put(kind,data,expected):
    raw=kind.encode()+b' '+str(len(data)).encode()+b'\0'+data
    actual=hashlib.sha1(raw).hexdigest();assert actual==expected,(kind,actual,expected)
    path=objects/actual[:2]/actual[2:];path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists():path.write_bytes(zlib.compress(raw))
    return actual
blobs=[e for e in REMOTE['tree'] if e['type']=='blob']
for e in blobs:put('blob',(ROOT/e['path']).read_bytes(),e['sha'])
alltrees={'':REMOTE['sha'],**{e['path']:e['sha'] for e in REMOTE['tree'] if e['type']=='tree'}}
verified=[]
for directory,expected in sorted(alltrees.items(),key=lambda x:x[0].count('/'),reverse=True):
    entries=[e for e in REMOTE['tree'] if (e['path'].rsplit('/',1)[0] if '/' in e['path'] else '')==directory]
    entries.sort(key=lambda e:(e['path'].rsplit('/',1)[-1]+('/' if e['type']=='tree' else '')).encode())
    raw=b''
    for e in entries:
        name=e['path'].rsplit('/',1)[-1]
        mode='40000' if e['type']=='tree' else e['mode']
        raw+=mode.encode()+b' '+name.encode()+b'\0'+bytes.fromhex(e['sha'])
    put('tree',raw,expected);verified.append({'path':directory,'sha':expected,'bytes':len(raw)})
put('commit',(META/'parent.commit').read_bytes(),SOURCE)
(ROOT/'.git/shallow').write_text(SOURCE+'\n')
git('update-ref','--no-deref','HEAD',SOURCE)
git('read-tree',SOURCE)
status=git('status','--porcelain=v1')
result={'source_commit':SOURCE,'source_tree':REMOTE['sha'],'imported_blobs':len(blobs),'imported_trees':len(verified),'tree_objects':verified,'verified_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actual_head':git('rev-parse','HEAD').strip(),'actual_tree':git('rev-parse','HEAD^{tree}').strip(),'status':status,'historical_objects_recovered':False,'shallow_boundary':SOURCE,'synthetic_commit_created':False}
(META/'git-import-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='tree_objects'}))
