#!/usr/bin/env python3
"""Independent C046 publication audit: metadata, JSON, hashes, ZIP reads and ASTs only."""
import ast, datetime, hashlib, io, json, os, pathlib, re, subprocess, sys, zipfile
ROOT=pathlib.Path('/workspace/scratch/fd65650eb54f')
REPO=ROOT/'OntoKin'
OUT=ROOT/'c046-validation/independent-review'
BASE=REPO/'docs/engineering/reach-recording-validation-2026-10-23'
PREFIX=BASE.relative_to(REPO).as_posix()+'/'
CORE='ef4ebc263deca57ad7b0d014ec4e9af16ca9ab0b'
TREE='591258c1caad81864f0bd2801ffa0cace1100d59'
PARENT='a5bb1e674e4ae3eb1d77e83b63f7a809eacf0bd0'
checks=[];input_bindings={};now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
def read(path):
    path=pathlib.Path(path);b=path.read_bytes()
    input_bindings[str(path.relative_to(ROOT))]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
    return b
def J(path):return json.loads(read(path))
def save(name,value):(OUT/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
def check(name,condition,detail=None):
    checks.append({'name':name,'passed':bool(condition),'detail':detail})
    if not condition:raise AssertionError(name)
def git(*args):return subprocess.check_output(['git','--no-optional-locks','-C',str(REPO),*args])
def blob(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def entries(tree):return {e['path']:e for e in tree['tree'] if e['type']=='blob'}
def inventory(expected):
    rows=[]
    for path,e in sorted(expected.items()):
        b=(REPO/path).read_bytes();mode='100755' if (REPO/path).stat().st_mode&0o111 else '100644'
        rows.append({'path':path,'bytes':len(b),'blob':blob(b),'sha256':hashlib.sha256(b).hexdigest(),'mode':mode})
    return rows
def manifest(path,base,field='files'):
    m=J(path);rows=m[field]
    check(path.name+' unique membership',len(rows)==len({x['path'] for x in rows}))
    for x in rows:
        b=read(base/x['path']);assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256'],str(base/x['path'])
    check(path.name+' exact member bytes',True,len(rows));return m
def functions(path):
    source=read(path).decode();tree=ast.parse(source);out={}
    def visit(node,scope=()):
        for child in ast.iter_child_nodes(node):
            if isinstance(child,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
                name=scope+(child.name,)
                if isinstance(child,(ast.FunctionDef,ast.AsyncFunctionDef)):out['.'.join(name)]=ast.get_source_segment(source,child)
                visit(child,name)
            else:visit(child,scope)
    visit(tree);return source,tree,out
started=now()
remote=J(OUT/'remote-core-commit.json');tree=J(OUT/'remote-core-tree.json');ref=J(OUT/'remote-owned-ref.json')
parent=J(BASE/'checkpoint-046-evidence/recovery/remote-tree.json')
held=J(OUT/'held-runtime-remote-tree.json');historical=J(OUT/'historical-runtime-remote-tree.json')
corefiles,parentfiles,heldfiles,historicalfiles=map(entries,(tree,parent,held,historical))
check('remote core commit, tree, parent and owned ref agree',remote['sha']==CORE and remote['tree']['sha']==TREE and remote['parents'][0]['sha']==PARENT and tree['sha']==TREE and ref['object']['sha']==CORE)
check('recursive remote trees complete',not any(x['truncated'] for x in (tree,parent,held,historical)))
check('core and parent file totals',len(corefiles)==2503 and sum(x['size'] for x in corefiles.values())==501832579 and len(parentfiles)==2441 and sum(x['size'] for x in parentfiles.values())==498113305)
check('all parent entries preserved',all(p in corefiles and all(e[k]==corefiles[p][k] for k in ('sha','size','mode','type')) for p,e in parentfiles.items()))
added=set(corefiles)-set(parentfiles)
check('exact 62 new C046 paths only',len(added)==62 and all(p.startswith(PREFIX+'checkpoint-046') or p==PREFIX+'HANDOFF-046.md' for p in added))
before=inventory(corefiles);save('inputs-before.json',before)
check('every actual core file matches remote path mode length blob',all(r['blob']==corefiles[r['path']]['sha'] and r['bytes']==corefiles[r['path']]['size'] and r['mode']==corefiles[r['path']]['mode'] for r in before))
raw=git('cat-file','commit',CORE)
check('actual original core commit bytes match SHA',hashlib.sha1(b'commit '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==CORE)
(OUT/'core.commit').write_bytes(raw)
check('actual local HEAD/tree and clean status',git('rev-parse','HEAD').decode().strip()==CORE and git('rev-parse','HEAD^{tree}').decode().strip()==TREE and git('status','--porcelain=v1')==b'')
runtime={p:e for p,e in corefiles.items() if p.startswith('ontokin/') and p.endswith('.py')}
check('65 runtime modules remain exactly held C035',len(runtime)==65 and all(p in heldfiles and all(e[k]==heldfiles[p][k] for k in ('sha','size','mode')) for p,e in runtime.items()))
changed=[p for p,e in runtime.items() if e['sha']!=historicalfiles[p]['sha']]
check('only two runtime files differ from historical C033',sorted(changed)==['ontokin/reach_reference.py','ontokin/reach_reference_center.py'])
for name in ['reach_reference.py','reach_reference_center.py','reach_reference_plan.py']:
    p=BASE/'checkpoint-046-reviews/historical/ontokin'/name
    check('historical source remote blob '+name,blob(read(p))==historicalfiles['ontokin/'+name]['sha'])
mainmanifest=manifest(BASE/'checkpoint-046-evidence-manifest.json',BASE)
check('C046 manifest is complete except itself',set(PREFIX+x['path'] for x in mainmanifest['files'])==added-{PREFIX+'checkpoint-046-evidence-manifest.json'})
manifest(BASE/'checkpoint-046-evidence/recovery/manifest.json',BASE/'checkpoint-046-evidence/recovery')
reviewmanifest=manifest(BASE/'checkpoint-046-reviews/review-manifest.json',BASE/'checkpoint-046-reviews')
check('reviewer scope retains no capture/product execution',reviewmanifest['product_executions']==0 and reviewmanifest['archived_program_executions']==0 and reviewmanifest['capture_preparation_executed'] is False and reviewmanifest['capture_neutrality_established'] is False)
for name,field in [('capture-preparation-review.json','reviewed_inputs'),('prose-review.json','reviewed_inputs')]:
    data=J(BASE/'checkpoint-046-reviews'/name)
    for v in data[field]:
        b=read(pathlib.Path(v['path']));assert len(b)==v['bytes'] and hashlib.sha256(b).hexdigest()==v['sha256'],v['path']
    check('exact review input binding '+name,True)
ep=J(BASE/'checkpoint-046-reviews/evidence/preparation-review.json')
for v in ep['inputs']:
    b=read(ROOT/v['path']);assert len(b)==v['bytes'] and hashlib.sha256(b).hexdigest()==v['sha256'],v['path']
check('evidence reviewer exact preparation input binding',ep['product_requests']==0 and ep['prepared_driver_executed'] is False)
check('review prose findings resolved',J(BASE/'checkpoint-046-reviews/prose-review.json')['material_findings_remaining']==[])
archive_results=[]
for n,total_count,total_bytes in [(33,87,69084895),(35,640,122611161)]:
    checkpoint=J(BASE/f'checkpoint-{n:03}.json');archive=checkpoint['archive'];man=J(BASE/f'checkpoint-{n:03}-manifest.json')
    check(f'C{n:03} member manifest binding',hashlib.sha256(read(BASE/f'checkpoint-{n:03}-manifest.json')).hexdigest()==checkpoint['manifest_sha256'])
    joined=[]
    for part in archive['parts']:
        b=read(BASE/part['path']);assert len(b)==part['bytes'] and hashlib.sha256(b).hexdigest()==part['sha256'];joined.append(b)
    data=b''.join(joined)
    check(f'C{n:03} ordered part and archive hash',len(data)==archive['bytes'] and hashlib.sha256(data).hexdigest()==archive['sha256'])
    members={v['path']:v for v in man['members']};actual=[]
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names=z.namelist();assert len(names)==len(set(names)) and set(names)==set(members)
        for info in z.infolist():
            rel=pathlib.PurePosixPath(info.filename);assert not rel.is_absolute() and '..' not in rel.parts
            b=z.read(info);row=members[info.filename];assert len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256']
            extracted=ROOT/f'c046-evidence/restored-c{n:03}'/info.filename
            eb=read(extracted);assert eb==b
            actual.append({'path':info.filename,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'crc32':info.CRC})
        assert z.testzip() is None
    check(f'C{n:03} all ZIP members CRCs hashes and restored bytes',len(actual)==total_count and sum(r['bytes'] for r in actual)==total_bytes)
    actual_names={p.relative_to(ROOT/f'c046-evidence/restored-c{n:03}').as_posix() for p in (ROOT/f'c046-evidence/restored-c{n:03}').rglob('*') if p.is_file()}
    check(f'C{n:03} exact restored membership',actual_names==set(members))
    save(f'c{n:03}-member-verification.json',actual)
    archive_results.append({'checkpoint':n,'parts':len(archive['parts']),'archive_bytes':len(data),'members':len(actual),'member_bytes':sum(v['bytes'] for v in actual)})
ledger=J(ROOT/'c046-evidence/restored-c033/capture-l03-001/key-ledger.json')['keys']
capture=J(ROOT/'c046-evidence/restored-c033/capture-l03-001/capture.json')
failure=J(ROOT/'c046-evidence/restored-c033/capture-l03-001/failure-locals.json')
check('historical 154 entered keys and 153 provisional returns',len(ledger)==154 and [r['index'] for r in ledger]==list(range(154)) and [r['outcome'] for r in ledger]==['returned']*153+['raised'])
check('all historical capture and key identity receipts true',all(capture['identity_checks'].values()) and all(all(k['identity_checks'].values()) for k in ledger) and capture['observation_errors']==[])
check('historical native callback with no construction check',capture['callbacks']['external']=={'module':'ontokin.construction','qualname':'ConstructionBudget.tick','bound_owner_type':'ConstructionBudget'} and capture['callbacks']['construction_check'] is None)
states=[k[b] for k in ledger for b in ('entry','exit')]
check('all 308 category sums match reader cache size',all(sum(s['source_cache_categories'].values())==s['source_cache_entries'] for s in states))
fields=('source_cache_entries','source_cache_categories','source_cursors')
check('all 153 adjacent source boundaries agree',all(all(ledger[i]['exit'][f]==ledger[i+1]['entry'][f] for f in fields) for i in range(153)))
check('historical selected interval has continuing centered cursors',all(k['exit']['source_cursors'] for k in ledger[1:]))
check('historical reader-cache occupancy bound',min(s['source_cache_entries'] for s in states)==112 and max(s['source_cache_entries'] for s in states)==165 and ledger[1]['entry']['source_cache_entries']==122)
seeds=[];advances=[];category_changes=[]
for k in ledger:
    old={json.dumps(v['key'],sort_keys=True):v['value'] for v in k['entry']['source_cursors']}
    for v in k['exit']['source_cursors']:
        key=json.dumps(v['key'],sort_keys=True);previous=old.get(key);cur=v['value']
        if previous!=cur:
            if cur['steps']==0:seeds.append({'index':k['index'],'time':k['time'],'frame':v['key'][-1][-1]})
            else:
                assert previous is not None and cur['steps']==previous['steps']+1
                advances.append({'index':k['index'],'phase':v['key'][-1][0][2]})
    first=k['entry']['source_cache_categories'].get('series_coefficients',0);last=k['exit']['source_cache_categories'].get('series_coefficients',0)
    if first!=last:category_changes.append([k['index'],first,last])
check('six published seeds at keys1,66,88',len(seeds)==6 and [v['index'] for v in seeds]==[1,1,66,66,88,88])
check('296 published advances with phase split168/128',len(advances)==296 and sum(v['phase']==0 for v in advances)==168 and sum(v['phase']==1 for v in advances)==128)
check('exact coefficient category increases',category_changes==[[1,7,9],[66,9,11],[88,11,12]])
for i,t,phase in [(65,('130','87'),0),(152,('243','89'),1)]:
    cursors=[v for v in ledger[i]['exit']['source_cursors'] if v['key'][-1][0][2]==phase]
    check(f'historical key{i} both cursors reach64',len(cursors)==2 and all(v['value']['steps']==64 and v['value']['clock']==dict(zip(['numerator','denominator'],t)) for v in cursors))
frames={v['function']:v['locals'] for v in failure['frames']}
check('historical selected failure frame names unique',len(frames)==len(failure['frames']))
o=frames['_orientation'];coef=frames['_series_coefficients'];integer=frames['_series_integer'];pending=frames['evaluate']['pending_values']
check('historical key153 and forearm64 locals',frames['_key_comparisons']['index']==153 and frames['_key_comparisons']['time']=={'numerator':'244','denominator':'89'} and o['previous']['steps']==64 and o['node']['path']=='rig.arm.forearm.frame')
check('historical failed key preserves published cursors',ledger[-1]['entry']['source_cursors']==ledger[-1]['exit']['source_cursors'])
check('one completed unpublished upper cursor at failure',len(pending)==1 and pending[0]['key'][-1][-1]=='rig.arm.upper.frame' and pending[0]['value']['steps']==0 and pending[0]['value']['clock']=={'numerator':'244','denominator':'89'})
check('historical coefficient129 degree14 index7 division inputs',coef['exponent']==129 and coef['degree']==14 and coef['index']==7 and coef['odd']==15 and integer=={'a':8841761993739701954543616000000,'b':1307674368000,'kind':'div'})
paths=[ROOT/'c046-evidence/restored-c033'/p for p in ['stock-l03-001/L03/request-result.json','capture-l03-001/stock/L03/request-result.json']]+[ROOT/'c046-evidence/restored-c035'/p for p in ['execution/complete-p11-l03-002/L03/request-result.json','execution/original28-002/L03/request-result.json']]
reports=[J(p) for p in paths]
shared_fields=('case_id','status','source_files','program_revision','options','max_operations','source_manifest','failure','diagnostic','operations','work')
check('all four original L03 reports agree on complete retained request and work',all(all(r[f]==reports[0][f] for f in shared_fields) for r in reports))
check('all four failures retain100001 shared95767 reach288 categories256 work-cache',all(r['status']=='failed' and r['operations']==100001 and r['work']['operations']==95767 and len(r['work']['counts'])==288 and r['work']['cache_entries']==256 for r in reports))
def trace(r):
    entries=re.findall(r'  File "([^"]+)", line (\d+), in ([^\n]+)',r['traceback'])
    excluded=[];kept=[]
    for file,line,func in entries:
        if pathlib.Path(file).name=='capture_reach_endpoints.py' and func in ('capture_validate_export','capture_key_comparisons'):
            excluded.append(func);continue
        kept.append((pathlib.Path(file).name,func))
    return kept,excluded
traces=[trace(r) for r in reports]
check('exact27 underlying frames match with only approved wrappers removed',len(traces[0][0])==27 and all(t[0]==traces[0][0] for t in traces) and len(traces[1][1])==2 and all(not traces[i][1] for i in (0,2,3)))
check('current failure contains required direct-seed coefficient route',all(f in [v[1] for v in traces[-1][0]] for f in ['_orientation','original','_series_coefficients','_series_integer']))
symbol_results=[]
selections={'reach_reference.py':['_Arithmetic.lookup','_Arithmetic.remember','_Arithmetic._sync_cache_operand_limit','_Arithmetic._series_integer','_Arithmetic._series_coefficients','_Arithmetic._series_dyadic','_Arithmetic._series_sincos'], 'reach_reference_center.py':['_orientation','_seed','_Guard.original','_Guard.lookup','_Guard.remember'], 'reach_reference_plan.py':['_PendingCursors.publish','_PendingCursors.remember','_SourceBatch.discard_cursors','_SourceBatch.__exit__']}
source_maps={}
for module,names in selections.items():
    oldsource,oldt,oldf=functions(BASE/'checkpoint-046-reviews/historical/ontokin'/module);source,t,f=functions(REPO/'ontokin'/module);source_maps[module]=f
    for name in names:
        check('complete source body unchanged '+module+':'+name,name in oldf and name in f and oldf[name]==f[name]);symbol_results.append({'module':module,'symbol':name,'sha256':hashlib.sha256(f[name].encode()).hexdigest()})
orientation=source_maps['reach_reference_center.py']['_orientation']
series=source_maps['reach_reference.py']['_Arithmetic._series_coefficients']
check('64 update predicate and original-before-seed remain exact','previous.steps < 64' in orientation and '_seed(guard.original(body.direct, clock), axis, guard)' in orientation)
check('coefficient key includes domain exponent degree and early hit return', 'key = ("series_coefficients", self.operand_limit, exponent, degree)' in series and 'cached = self.lookup(key)\n        if cached is not None:\n            return cached' in series and series.rstrip().endswith('return self.remember(key, (tuple(coefficients), denominator, lane))'))
check('integer charge precedes integer work',source_maps['reach_reference.py']['_Arithmetic._series_integer'].index('self.tick()')<source_maps['reach_reference.py']['_Arithmetic._series_integer'].index('an, bn ='))
src,parsed,funcs=functions(BASE/'checkpoint-046-capture.py')
calls=[n for n in ast.walk(parsed) if isinstance(n,ast.Call)]
check('prepared capture forwards each original once',sum(isinstance(n.func,ast.Name) and n.func.id=='validate_original' for n in calls)==1 and sum(isinstance(n.func,ast.Name) and n.func.id=='key_original' for n in calls)==1)
check('prepared capture has no trace profile monitor installer calls',not any(isinstance(n.func,ast.Attribute) and n.func.attr in ('settrace','setprofile','set_events','register_callback','use_tool_id') for n in calls))
rootresult=J(ROOT/'c046-validation/published-core/result.json');rootaudit=J(ROOT/'c046-validation/published-core/source-data.json')
check('recorded root commands both exit0 on exact core',rootresult['commit']==CORE and rootresult['tree']==TREE and rootresult['inputs_stable'] and [v['exit_code'] for v in rootresult['commands']]==[0,0])
check('root source audit actual344 checks retained',rootaudit['checks_passed']==344 and rootaudit['checks_failed']==0 and rootaudit['prepared_capture_executed'] is False)
check('root before/after complete input snapshots identical',read(ROOT/'c046-validation/published-core/inputs-before.json')==read(ROOT/'c046-validation/published-core/inputs-after.json'))
rootinputs=J(ROOT/'c046-validation/published-core/inputs-before.json')
ourinputs={v['path']:v for v in before}
check('root snapshots cover exact complete core',len(rootinputs)==2503 and all(v['path'] in ourinputs and v['bytes']==ourinputs[v['path']]['bytes'] and v['sha256']==ourinputs[v['path']]['sha256'] and v['git_blob']==ourinputs[v['path']]['blob'] and v['mode']==ourinputs[v['path']]['mode'] for v in rootinputs))
doclog=read(ROOT/'c046-validation/published-core/documentation.stdout').decode()
docresult=json.loads(doclog)
check('actual documentation success retained',docresult['failures']==[] and docresult['sources_verified']==29 and docresult['links']['documents']==203 and docresult['links']['local_links']==1646 and read(ROOT/'c046-validation/published-core/documentation.stderr')==b'')
prose=read(BASE/'checkpoint-046-l03-retirement-review.md').decode();handoff=read(BASE/'HANDOFF-046.md').decode();plan=read(BASE/'checkpoint-046-capture-plan.md').decode()
check('report preserves bounded historical lifetime and current-local limits','key 1 entry through key 153' in prose and 'pre-key-1' in prose and 'Historical values' in prose and 'must not be relabeled current' in prose and 'not executed' in prose)
check('report handoff and plan retain unexecuted preparation',all('unexecuted' in s.lower() or 'not executed' in s.lower() for s in (prose,handoff,plan)))
check('no release acceptance or implementation selection claimed','No runtime implementation is selected' in prose and '**24/28**' in prose and 'C035 remains held' in prose)
after=inventory(corefiles);save('inputs-after.json',after)
check('all complete core inputs stable during independent audit',before==after)
check('checkout remains clean',git('status','--porcelain=v1')==b'')
save('input-bindings.json',input_bindings)
save('source-symbol-bindings.json',symbol_results)
result={'schema':'ontokin.checkpoint046-independent-core-audit/0.1','status':'passed','started_utc':started,'finished_utc':now(),'core_commit':CORE,'core_tree':TREE,'parent_commit':PARENT,'checks_passed':len(checks),'checks_failed':0,'checks':checks,'findings':[],'core_files':len(corefiles),'core_bytes':sum(e['size'] for e in corefiles.values()),'parent_files_preserved':len(parentfiles),'new_core_files':len(added),'archives':archive_results,'historical_published_seed_count':len(seeds),'historical_published_advance_count':len(advances),'historical_coefficient_changes':category_changes,'independence_disclosure':'Reviewer performed C045 source acquisition earlier in C046; did not author the C046 report, root audit, capture, source/evidence/capture reviews or product code. Independently fetched remote core/ref and held/historical trees; independently checked physical files, archives, retained-data census and critical source bodies.','no_eviction_scope':'Independent critical-source and retained-premise review supports the published native key1-entry through key153-precleanup inference only. It is not a directly observed mutation sequence; setup/key0, later cleanup, foreign callbacks and current C035 are excluded.','limits':['Final appendix and final containing commit are outside this core audit.','Prepared capture remains unexecuted; measured neutrality and diagnostic size sufficiency are unestablished.','No exact current locals or intra-key cache event counts inferred.','No product execution, archived-driver execution, extraction, root checker rerun or root audit rerun.'],'product_requests':0,'prepared_capture_executed':False,'archive_extractions':0,'root_checkers_rerun':False,'release_acceptance':False}
save('result.json',result)
print(json.dumps({k:result[k] for k in ('status','checks_passed','checks_failed','core_files','core_bytes','finished_utc')}))
