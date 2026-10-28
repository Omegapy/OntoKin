import argparse, datetime, hashlib, json, os, pathlib, subprocess

BASE = pathlib.Path('/workspace/scratch/abbf47b1d319')
ROOT = BASE / 'OntoKin'
TESTED = '4155acfd1b01e1b72aac23be5e28b054d2e10440'
PREFIX = 'docs/engineering/repository-reconciliation-2026-10-28/evidence/'
SOURCE_DIRS = ('ontokin', 'tests', 'tools', 'docs', 'examples', 'schemas', 'prototypes', '.github')
ROOT_FILES = ('pyproject.toml', 'README.md', 'AGENTS.md', 'GOAL.md', 'STATUS.md', 'LICENSE', '.gitignore')
IGNORED = {'.git','node_modules','__pycache__','.venv','venv','.tox','.cache','.pytest_cache','.mypy_cache','.ruff_cache','build','dist','_build'}
TAIL = [PREFIX + x for x in ('premerge-policy-review.json','premerge-documentation.log','premerge-verification.json','resulting-main-documentation.log','resulting-main-verification.json','integration.json','verify_publication.py')]

def safe_path(path):
    if not isinstance(path,str) or not path or '\\' in path or '\x00' in path: raise ValueError('unsafe path')
    normalized=pathlib.PurePosixPath(path)
    if normalized.is_absolute() or normalized.as_posix()!=path or any(p in ('.','..','') for p in path.split('/')): raise ValueError('unsafe path '+path)
    return path

def strict(path):
    def pairs(items):
        d = {}
        for k,v in items:
            if k in d: raise ValueError('duplicate JSON key: '+k)
            d[k]=v
        return d
    return json.loads(path.read_text(), object_pairs_hook=pairs, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()

def sha(data): return hashlib.sha256(data).hexdigest()
def git(*args): return subprocess.check_output(['git', '-C', str(ROOT), *args])
def tree(rev):
    result={}
    for entry in git('ls-tree','-r','-l','-z',rev).split(b'\0'):
        if not entry: continue
        meta,name=entry.split(b'\t',1); mode,kind,oid,size=meta.decode().split(); name=safe_path(name.decode())
        if kind!='blob' or mode not in ('100644','100755'): raise ValueError('unsupported tree entry '+name)
        if name in result: raise ValueError('duplicate tree path '+name)
        result[name]={'mode':mode,'git_blob_sha1':oid,'bytes':int(size)}
    return result

def identity(path):
    if path.is_symlink(): raise ValueError('symlink '+str(path))
    data=path.read_bytes()
    return {'bytes':len(data),'sha256':'sha256:'+sha(data),'git_blob_sha1':hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()}

def ignored(name): return name in IGNORED or name=='.env' or name.startswith('.env.') or name.endswith(('.pyc','.pyo'))
def inventory():
    files=[ROOT/name for name in ROOT_FILES if (ROOT/name).is_file()]
    for name in SOURCE_DIRS:
        top=ROOT/name
        if top.is_symlink(): raise ValueError('source symlink')
        if not top.is_dir(): continue
        for parent,dirs,names in os.walk(top,followlinks=False):
            dirs[:]=sorted(d for d in dirs if not ignored(d))
            for d in dirs:
                if (pathlib.Path(parent)/d).is_symlink(): raise ValueError('source symlink')
            files.extend(pathlib.Path(parent)/n for n in sorted(names) if not ignored(n))
    rows=[]
    for path in sorted(files):
        rel=path.relative_to(ROOT).as_posix(); ident=identity(path)
        rows.append({'path':rel,'sha256':ident['sha256'],'bytes':ident['bytes']})
    if len({r['path'] for r in rows})!=len(rows): raise ValueError('duplicate inventory path')
    return {'sha256':'sha256:'+sha(canonical(rows)),'file_count':len(rows),'files':rows}

p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--phase',required=True);p.add_argument('--expected-head');p.add_argument('--expected-tree');args=p.parse_args()
head=git('rev-parse','HEAD').decode().strip()
if args.expected_head and head!=args.expected_head: raise ValueError('unexpected HEAD')
old=tree(TESTED)
index_tree=git('write-tree').decode().strip();new=tree(index_tree)
head_tree=git('rev-parse','HEAD^{tree}').decode().strip()
if args.phase in ('resulting-main','final-main') and index_tree!=head_tree: raise ValueError('index differs from observed main tree')
if args.expected_tree and index_tree!=args.expected_tree: raise ValueError('tree differs from remote readback')
allow={'STATUS.md','docs/engineering/repository-reconciliation-2026-10-28/README.md',*TAIL}
package_paths=set()
for name in ('repository-files.json','extra-upload-inventory.json'):
    for row in strict(BASE/'reconcile-audit/packaged-evidence'/name)['files']:
        path=safe_path(row['path'])
        if path in package_paths: raise ValueError('duplicate packaged path '+path)
        package_paths.add(path);allow.add(path)
        if path not in new or new[path]['mode']!=row['mode']: raise ValueError('package path/mode differs from index '+path)
        actual=identity(ROOT/path)
        if actual['sha256'].removeprefix('sha256:')!=row['sha256'] or actual['bytes']!=row['bytes'] or actual['git_blob_sha1']!=row['git_blob_sha1']: raise ValueError('packaged member changed '+path)
diff=sorted(path for path in set(old)|set(new) if old.get(path)!=new.get(path))
if set(diff)-allow: raise ValueError('unapproved tree differences '+repr(set(diff)-allow))
if set(old)-set(new): raise ValueError('original path deleted')
for path in set(new)-set(old):
    if new[path]['mode']!='100644': raise ValueError('new executable activation '+path)
for path,row in new.items():
    act=identity(ROOT/path)
    if act['git_blob_sha1']!=row['git_blob_sha1'] or act['bytes']!=row['bytes']: raise ValueError('worktree mismatch '+path)
    actualmode='100755' if (ROOT/path).stat().st_mode&0o111 else '100644'
    if actualmode!=row['mode']: raise ValueError('mode mismatch '+path)
current=inventory();prior=strict(BASE/'c059-validation-full-001/source-before.json')
if prior['sha256']!='sha256:'+sha(canonical(prior['files'])) or prior['file_count']!=len(prior['files']): raise ValueError('original inventory invalid')
if prior!=strict(BASE/'c059-validation-full-001/source-after.json'): raise ValueError('original source changed')
omap={r['path']:r for r in prior['files']};nmap={r['path']:r for r in current['files']}
if len(omap)!=len(prior['files']): raise ValueError('duplicate original inventory paths')
for path in (*omap,*nmap,*allow): safe_path(path)
idiff=sorted(path for path in set(omap)|set(nmap) if omap.get(path)!=nmap.get(path))
if set(idiff)-allow: raise ValueError('unapproved inventory difference '+repr(set(idiff)-allow))
if set(omap)-set(nmap): raise ValueError('original source inventory member deleted')
if set(idiff)!=set(diff): raise ValueError('tree/inventory difference sets do not agree')
equal=sorted(path for path in old if path not in diff)
exceptions=[]
for path in diff:
    ident=identity(ROOT/path)
    exceptions.append({'path':path,'old':old.get(path),'new':{**new[path],'sha256':ident['sha256']},'reason':'Current result/ownership narrative; no changed computational authority' if path in ('STATUS.md','docs/engineering/repository-reconciliation-2026-10-28/README.md') else 'Retained execution, review, transport or publication output; not an active computational input','verification':'Complete payload/member/claim audit and publication identity readback; navigation check for Markdown/HTML'})
record={'schema_version':'ontokin.c059.publication-equality/0.1','phase':args.phase,'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'passed','tested_commit':TESTED,'tested_tree':git('rev-parse',TESTED+'^{tree}').decode().strip(),'observed_head':head,'observed_index_tree':index_tree,'tracked_file_count':len(new),'unchanged_tracked_file_count':len(equal),'unchanged_tracked_mapping_sha256':sha(canonical({k:old[k] for k in equal})),'tested_inventory':{k:v for k,v in prior.items() if k!='files'},'current_inventory':{k:v for k,v in current.items() if k!='files'},'equal_eligible_inventory_count':len([k for k in omap if k not in idiff]),'equal_eligible_inventory_sha256':sha(canonical([omap[k] for k in sorted(omap) if k not in idiff])),'exact_exceptions':exceptions,'reserved_append_only_output_paths':TAIL,'output_boundary':'This record is generated after the comparison. Its own bytes and any later named output records are bound through the subsequent immutable commit/tree and readback, not by a circular self-hash. Uncreated reserved paths are not claimed as verified.','limits':['No runtime role rerun is implied.','Original failed attempts, pending compatibility/release roles and unknown SQLite physical cause remain.','Evidence additions change the complete source inventory; all unchanged eligible inputs remain equal.']}
out=pathlib.Path(args.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(record,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
print(json.dumps({'status':'passed','phase':args.phase,'head':head,'tree':index_tree,'equal_inputs':len(equal),'exact_exceptions':len(diff),'output':str(out)}))
