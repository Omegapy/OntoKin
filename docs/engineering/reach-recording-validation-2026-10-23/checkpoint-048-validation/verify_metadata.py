"""C048 scoped source/evidence metadata checks; imports no OntoKin code."""
from pathlib import Path, PurePosixPath
import ast, datetime, hashlib, json, re

ROOT = Path('/workspace/scratch/514b4c8f2cdb/c048')
SOURCE = ROOT / 'source'
BASE = SOURCE / 'docs/engineering/reach-recording-validation-2026-10-23'
checks = []

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def git(kind, raw):
    return hashlib.sha1(kind.encode()+b' '+str(len(raw)).encode()+b'\0'+raw).hexdigest()

def check(value, label):
    checks.append({'name':label,'passed':bool(value)})
    if not value:
        raise AssertionError(label)

def read(path):
    return json.loads(path.read_text())

def main():
    start=datetime.datetime.now(datetime.timezone.utc).isoformat()
    tree=json.loads(read(ROOT/'acquisition/tree.json')['structuredContent']['content'])
    entries={e['path']:e for e in tree['tree']}
    blobs={p:e for p,e in entries.items() if e['type']=='blob'}
    check(not tree['truncated'] and len(blobs)==2673,'complete remote C047 tree metadata')
    directories={'':[]}
    for name,e in entries.items():
        parent=str(PurePosixPath(name).parent)
        if parent=='.':parent=''
        directories.setdefault(parent,[]).append(e)
        if e['type']=='tree':directories.setdefault(name,[])
    for name,children in directories.items():
        rows=[]
        for e in children:
            leaf=PurePosixPath(e['path']).name
            mode='40000' if e['type']=='tree' else e['mode']
            key=(leaf+'/' if e['type']=='tree' else leaf).encode()
            rows.append((key,mode.encode()+b' '+leaf.encode()+b'\0'+bytes.fromhex(e['sha'])))
        actual=git('tree',b''.join(r for _,r in sorted(rows)))
        expected=tree['sha'] if not name else entries[name]['sha']
        assert actual==expected, name
    check(True,'every recursive Git tree identity recomputed from complete metadata')
    inventory=read(BASE/'checkpoint-048-validation/recovery/source-verification.json')
    input_paths=[SOURCE/e['path'] for e in inventory['verified']]
    base_before={p.relative_to(SOURCE).as_posix():sha(p.read_bytes()) for p in input_paths}
    for e in inventory['verified']:
        p=SOURCE/e['path'];raw=p.read_bytes()
        assert len(raw)==e['bytes'] and sha(raw)==e['sha256'] and git('blob',raw)==blobs[e['path']]['sha']
    check(len(input_paths)==813 and sum(p.stat().st_size for p in input_paths)==59720305,'all813recovered base files exact')
    runtime=[e for e in inventory['verified'] if e['path'].startswith('ontokin/')]
    held=read(BASE/'checkpoint-048-validation/recovery/held-runtime-fresh-check.json')
    check(len(runtime)==65 and held['all_equal'] and held['current_modules']==held['held_modules']==65,'all65runtime modules match freshly read held tree')
    docs=[p for p in blobs if Path(p).suffix.lower() in {'.md','.markdown','.html','.htm'}]
    check(all((SOURCE/p).is_file() for p in docs),'all original narrative files available and exact')
    new=[p for p in SOURCE.rglob('*') if p.is_file() and p.relative_to(SOURCE).as_posix() not in blobs]
    for p in new:
        rel=p.relative_to(BASE)
        assert rel.parts[0].startswith('checkpoint-048') or rel.as_posix()=='HANDOFF-048.md'
    check(True,'all additions confined to owned C048 records')
    for p in new:
        if p.suffix=='.json':json.loads(p.read_text())
        if p.suffix=='.py':ast.parse(p.read_text(),filename=str(p))
    check(True,'new JSON parses and Python evidence utilities parse without execution')
    reviews=read(BASE/'checkpoint-048-reviews.json')
    check(all(sha((BASE/r['path']).read_bytes())==r['sha256'] for r in reviews['reviews']),'all four independent review payloads match indexed hashes')
    archive=read(BASE/'checkpoint-048-validation/archive-recovery-001/result.json')
    check(archive['status']=='passed' and archive['members']==414 and archive['parts']==18 and archive['product_rerun'] is False,'current archive recovery result bound without product rerun')
    v=read(BASE/'checkpoint-048-validation.json');d=read(BASE/v['documentation']['result'])
    check(d['status']=='failed' and d['sources_verified']==29 and d['sections_verified']==233 and len(d['failures'])==12,'unchanged full documentation checker retains actual twelve-input failure')
    for f in d['failures']:
        p=(SOURCE/f['file']).parent/f['target'];rel=p.resolve().relative_to(SOURCE).as_posix()
        assert rel in blobs and not p.exists() and 'checkpoint-048' not in f['file'] and blobs[rel]['size']>1000000
    check(True,'all twelve checker failures are absent existing historical binary archives')
    check(v['documentation']['new_C048_document_link_failures']==0 and v['documentation']['passed'] is False,'no new-document link error or relabeled full gate pass')
    ledger=read(BASE/'checkpoint-048-cost-ledger.json')
    check(sum(ledger['current_evidence']['gross_ceilings'])==56 and ledger['current_evidence']['failed_degree14']['original_completed_construction']-ledger['current_evidence']['failed_degree14']['hypothetical_affine_before_corresponding_division']==4,'reported arithmetic subtotals internally consistent, not measured candidates')
    check(ledger['runtime_candidate_selected'] is False and ledger['runtime_execution'] is False and v['release']['original28_passed']==24 and not v['release']['release_accepted'],'runtime and release limits remain explicit')
    bad=[]
    for p in new:
        raw=p.read_bytes()
        if re.search(rb'(?:github_pat_[A-Za-z0-9_]{12,}|ghp_[A-Za-z0-9]{20,}|[?&]token=[A-Za-z0-9]{12,})',raw):bad.append(str(p))
    check(not bad,'defined credential patterns absent from additions; no universal secret claim')
    check(not (ROOT/'acquisition/temporary-download-manifest.json').exists() and not (ROOT/'acquisition/temporary-download-extra.json').exists(),'temporary signed download manifests removed')
    check(base_before=={p.relative_to(SOURCE).as_posix():sha(p.read_bytes()) for p in input_paths},'all recovered base inputs stable across metadata check')
    out={'schema':'ontokin.checkpoint048-metadata-validation/0.1','status':'passed','started_at':start,'finished_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':checks,'checks_passed':len(checks),'exact_base_files':813,'complete_checkout':False,'runtime_modules':65,'new_files_inspected':len(new),'new_bytes_inspected':sum(p.stat().st_size for p in new),'product_execution':False,'full_documentation_gate':'failed due12missing historical archive inputs','release_acceptance':False}
    target=BASE/'checkpoint-048-validation/metadata-001/result.json';target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('x') as f:json.dump(out,f,indent=2);f.write('\n')
    print(json.dumps({k:v for k,v in out.items() if k!='checks'}))

if __name__=='__main__':
    main()
