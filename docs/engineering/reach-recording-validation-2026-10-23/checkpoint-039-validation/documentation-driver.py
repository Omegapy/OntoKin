import datetime,hashlib,json,pathlib,platform,subprocess,sys,time
root=pathlib.Path('/workspace/scratch/d300b0425597/OntoKin');auth=root.parent/'c039-authority';out=auth/'documentation-001';out.mkdir(exist_ok=False)
cfg=json.loads(pathlib.Path('/tmp/c039-doc-config.json').read_text());entries={e['path']:e for e in json.loads((auth/'parent_tree.json').read_text())['tree'] if e['type']=='blob'}
for e in cfg['core_files']:entries[e['path']]={'sha':e['sha'],'mode':e['mode'],'size':e['bytes']}
def digest(b):return hashlib.sha256(b).hexdigest()
def snapshot():
    rows=[]
    for p in sorted(root.rglob('*')):
        if not p.is_file():continue
        n=p.relative_to(root).as_posix();b=p.read_bytes();e=entries.get(n);g=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
        if e is None or e['sha']!=g or e['size']!=len(b):raise ValueError('Snapshot differs: '+n)
        mode='100755' if p.stat().st_mode&0o111 else '100644'
        if mode!=e['mode']:raise ValueError('Mode differs: '+n)
        rows.append({'path':n,'bytes':len(b),'sha256':digest(b),'git_blob':g,'mode':mode})
    return (json.dumps(rows,indent=2)+'\n').encode()
before=snapshot();(out/'inputs-before.json').write_bytes(before)
command=['python3','docs/maintenance/reorganization-2026-10-17/verify_reorganization.py','--json-output',str(out/'report.json')]
start={'schema':'ontokin.checkpoint039-command-start/0.1','command':command,'cwd':str(root),'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_commit':cfg['commit'],'source_tree':cfg['tree'],'source_kind':'Exact Git-verified documentation-complete subset; not a full execution checkout','input_manifest_sha256':digest(before),'python':sys.version,'executable':sys.executable,'platform':platform.platform()}
(out/'start.json').write_text(json.dumps(start,indent=2)+'\n');t=time.monotonic()
with (out/'stdout.txt').open('wb') as so,(out/'stderr.txt').open('wb') as se:
    completed=subprocess.run(command,cwd=root,stdout=so,stderr=se,timeout=120)
after=snapshot();(out/'inputs-after.json').write_bytes(after);report=json.loads((out/'report.json').read_text())
result={'schema':'ontokin.checkpoint039-command-result/0.1','status':'passed' if completed.returncode==0 and before==after else 'failed','exit_code':completed.returncode,'ended_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'elapsed_seconds':time.monotonic()-t,'source_commit':cfg['commit'],'source_tree':cfg['tree'],'input_files':len(json.loads(before)),'input_bytes':sum(x['bytes'] for x in json.loads(before)),'inputs_before_sha256':digest(before),'inputs_after_sha256':digest(after),'inputs_unchanged':before==after,'report_status':report['status'],'sources_verified':report['sources_verified'],'sections_verified':report.get('sections_verified'),'links':report['links'],'failures':report['failures'],'stdout_sha256':digest((out/'stdout.txt').read_bytes()),'stderr_sha256':digest((out/'stderr.txt').read_bytes())}
(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));sys.exit(0 if result['status']=='passed' else 1)
