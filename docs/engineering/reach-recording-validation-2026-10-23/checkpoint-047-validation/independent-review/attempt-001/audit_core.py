#!/usr/bin/env python3
"""Independent C047 published-core metadata/source audit. No product import or execution."""
import ast
import hashlib
import io
import json
import os
import platform
import stat
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path, PurePosixPath

B = Path('/workspace/scratch/f34f66f87e3e')
R = B / 'OntoKin'
O = B / 'c047-final-review'
E = R / 'docs/engineering/reach-recording-validation-2026-10-23'
CORE = '7d2c118f5cc5ca141f2092b68d02b23fd933b571'
TREE = '219ceb20170a5dc3393bc9e7383b374193ce6c02'
PARENT = '48b5d381a0f86d9706a109b78e2ce52eb0d287f0'
PTREE = '33ac0caa77528432d18132a1e606d1e4fbd7ab80'
EXPIRY = '2026-10-26T22:19:09+00:00'
checks = []
facts = {}
started = datetime.now(timezone.utc).isoformat()

def h(b): return hashlib.sha256(b).hexdigest()
def obj(kind,b): return hashlib.sha1(kind.encode()+b' '+str(len(b)).encode()+b'\0'+b).hexdigest()
def j(p): return json.loads(Path(p).read_text())
def save(name,value): (O/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
def check(name,value,detail=None):
    row={'name':name,'passed':bool(value)}
    if detail is not None: row['detail']=detail
    checks.append(row)
    if not value: print('FAIL '+name+' '+repr(detail),flush=True)
def desc(p):
    p=Path(p);data=p.read_bytes()
    return {'path':str(p.relative_to(B)),'bytes':len(data),'sha256':h(data),'mode':oct(stat.S_IMODE(p.stat().st_mode))}
def matches(p,row):
    data=Path(p).read_bytes()
    return len(data)==row['bytes'] and h(data)==row['sha256']
def git(*args):
    x=subprocess.run(['git','-C',str(R),*args],capture_output=True,text=True,env={**os.environ,'GIT_OPTIONAL_LOCKS':'0'})
    if x.returncode: raise RuntimeError({'args':args,'exit':x.returncode,'stderr':x.stderr})
    return x.stdout.strip()
def within(start,finish,window):
    t=lambda x:datetime.fromisoformat(x.replace('Z','+00:00'))
    return t(window['active_after'])<=t(start)<=t(finish)<=t(window['expires_at'])

remote=j(O/'remote-core-tree.json')
tree_rows={x['path']:x for x in remote['tree'] if x['type']=='blob'}
input_paths={R/p for p in tree_rows}
for directory in ['c047-execution','c047-recovery','c047-driver-review','c047-independent-comparison','c047-lifetime-review','c047-publication','c047-validation']:
    input_paths.update(p for p in (B/directory).rglob('*') if p.is_file())
input_paths.update(O/p for p in ['owned-ref.json','remote-core-commit.json','remote-core-tree.json','window.json','audit_core.py','run_audit.py'])
input_paths=sorted(input_paths,key=str)
before=[desc(p) for p in input_paths]
save('inputs-before.json',before)
before_map={x['path']:x for x in before}
check('exclusive window active',datetime.fromisoformat(started)<datetime.fromisoformat(EXPIRY) and j(O/'window.json')['id']==6428329816)

# Independent fresh GitHub metadata, complete current bytes and authentic commit object.
ref=j(O/'owned-ref.json'); commit=j(O/'remote-core-commit.json')
check('fresh owned ref and authentic core commit/tree',ref['object']['sha']==CORE and commit['sha']==CORE and commit['tree']['sha']==TREE and [x['sha'] for x in commit['parents']]==[PARENT])
check('fresh complete recursive tree',remote['sha']==TREE and remote['truncated'] is False and len(tree_rows)==2596)
check('local current core and clean checkout',git('rev-parse','HEAD')==CORE and git('rev-parse','HEAD^{tree}')==TREE and git('status','--porcelain=v1')=='')
check('local index exact complete source membership',set(git('ls-files').splitlines())==set(tree_rows))
source_rows=[];bad=[]
for name,row in sorted(tree_rows.items()):
    p=R/name;data=p.read_bytes();mode='100755' if p.stat().st_mode&0o111 else '100644'
    actual={'path':name,'bytes':len(data),'sha256':h(data),'git_blob':obj('blob',data),'mode':mode}
    source_rows.append(actual)
    if actual['git_blob']!=row['sha'] or len(data)!=row['size'] or mode!=row['mode']: bad.append(name)
check('all 2596 local files match fresh remote blob mode and size',not bad,{'mismatches':bad,'files':len(source_rows),'bytes':sum(x['bytes'] for x in source_rows)})
check('complete core byte count',sum(x['bytes'] for x in source_rows)==524662681)
save('core-file-bindings.json',source_rows)
source_map={x['path']:x for x in source_rows}
root={}
for name,row in tree_rows.items():
    d=root;parts=name.split('/')
    for part in parts[:-1]: d=d.setdefault(part,{})
    d[parts[-1]]=(row['mode'],row['sha'])
def tree_hash(d):
    rows=[]
    for name,v in d.items():
        if isinstance(v,dict): rows.append((name+'/',b'40000 '+name.encode()+b'\0'+bytes.fromhex(tree_hash(v))))
        else: rows.append((name,v[0].encode()+b' '+name.encode()+b'\0'+bytes.fromhex(v[1])))
    return obj('tree',b''.join(v for _,v in sorted(rows)))
check('independently reconstructed complete root tree',tree_hash(root)==TREE)
raw=(B/'c047-publication/core-actual-commit.bin').read_bytes()
check('authentic imported commit bytes',len(raw)==314 and obj('commit',raw)==CORE and raw.startswith(('tree '+TREE+'\nparent '+PARENT+'\n').encode()) and not raw.endswith(b'\n'))
parent=j(B/'c047-recovery/remote-tree.json')
parent_rows={x['path']:x for x in parent['tree'] if x['type']=='blob'}
check('all parent 2556 file identities modes sizes preserved',parent['sha']==PTREE and not parent['truncated'] and len(parent_rows)==2556 and all(p in tree_rows and all(row[k]==tree_rows[p][k] for k in ['sha','mode','size']) for p,row in parent_rows.items()))
plan=j(B/'c047-publication/core-plan.json');adds=set(tree_rows)-set(parent_rows)
check('exact 40 documentation/evidence additions match publication plan',len(adds)==40 and adds=={x['path'] for x in plan['files']} and sum(source_map[p]['bytes'] for p in adds)==15983134 and all(x['path'].startswith('docs/engineering/reach-recording-validation-2026-10-23/') and all(source_map[x['path']][a]==x[b] for a,b in [('bytes','bytes'),('sha256','sha256'),('git_blob','sha'),('mode','mode')]) for x in plan['files']))
held=j(B/'c047-recovery/held-runtime-tree-readback.json');heldrows={x['path']:x for x in held['tree'] if x['type']=='blob'}
runtime={p:r for p,r in tree_rows.items() if p.startswith('ontokin/') and p.endswith('.py')}
check('all 65 held C035 runtime modules unchanged',len(runtime)==65 and held['sha']=='87c949b238055af1ce368c694e1d5683c8aeacde' and all(p in heldrows and all(r[k]==heldrows[p][k] for k in ['sha','mode','size']) for p,r in runtime.items()))

# Published archive is read as members and CRC streams; nothing is extracted.
cp=j(E/'checkpoint-047.json');manifest=j(E/'checkpoint-047-evidence-manifest.json')
check('checkpoint immutable parent source and nonacceptance scope',cp['source_commit']==PARENT and cp['source_tree']==PTREE and cp['product_requests_passed']==0 and cp['accepted_artifact'] is False and cp['runtime_candidate_selected'] is False and cp['release_acceptance'] is False and cp['full_product_goal_completed'] is False)
check('exact member manifest hash',h((E/'checkpoint-047-evidence-manifest.json').read_bytes())==cp['manifest_sha256']=='bff175cc43e11ccfedba16db7a51f6ee3ab237fc145bb3116da54ddc64b80351')
parts=cp['archive']['parts'];partdata=[(E/x['path']).read_bytes() for x in parts]
check('all 18 published archive parts exact',len(parts)==18 and len({x['path'] for x in parts})==18 and all(len(d)==x['bytes'] and h(d)==x['sha256'] for d,x in zip(partdata,parts)))
archive=b''.join(partdata)
check('joined published archive exact bytes and hash',len(archive)==15483218==cp['archive']['bytes'] and h(archive)==cp['archive']['sha256']=='ee15945c4377c6dc86b22587fe239d4846bdeacda08cefd882ae773736681137' and archive==(B/'c047-publication/checkpoint-047-evidence.zip').read_bytes())
z=zipfile.ZipFile(io.BytesIO(archive));infos=z.infolist();members=manifest['members'];mm={x['path']:x for x in members}
check('exact safe unique archive membership',len(infos)==len(members)==len(mm)==414 and len({x.filename for x in infos})==414 and {x.filename for x in infos}==set(mm) and all(not PurePosixPath(x.filename).is_absolute() and '..' not in PurePosixPath(x.filename).parts and not x.is_dir() for x in infos))
member_errors=[];total=0
for info in infos:
    data=z.read(info);row=mm[info.filename];total+=len(data)
    if len(data)!=row['bytes'] or h(data)!=row['sha256'] or oct(stat.S_IMODE(info.external_attr>>16))!=row['mode'] or data!=(B/info.filename).read_bytes(): member_errors.append(info.filename)
check('all archive CRCs sizes modes hashes and original bytes',not member_errors and total==167310502==manifest['member_bytes'],{'members':len(infos),'member_bytes':total,'mismatches':member_errors})
copies=list((E/'checkpoint-047-lifetime-review').rglob('*'));copies=[x for x in copies if x.is_file()]
check('all 14 direct lifetime files exact archive and original copies',len(copies)==14 and all(x.read_bytes()==z.read('c047-lifetime-review/'+str(x.relative_to(E/'checkpoint-047-lifetime-review')))==(B/'c047-lifetime-review'/x.relative_to(E/'checkpoint-047-lifetime-review')).read_bytes() for x in copies))
review_index=j(E/'checkpoint-047-reviews.json');review_members=[m for x in review_index['reviews'] for m in x['members']]
check('all indexed review bytes and package hashes bound',all(len(z.read(x['archive_path']))==x['bytes'] and h(z.read(x['archive_path']))==x['sha256'] for x in review_members))
restore=j(B/'c047-publication/restore-receipt.json');pack=j(B/'c047-publication/packaging-receipt.json')
check('actual archive packaging and prior restoration receipts bound',restore['status']=='passed' and restore['archive_sha256']==h(archive) and restore['checkpoint_sha256']==h((E/'checkpoint-047.json').read_bytes()) and restore['members']==414 and pack['archive']==cp['archive'] and pack['inputs_stable'] is True)
readback=j(B/'c047-publication/core-remote-byte-verification.json');rr=readback['remote_added_file_readbacks']
check('retained full immutable GitHub byte readbacks bind every core addition',readback['status']=='passed' and readback['core_commit']==CORE and readback['core_tree']==TREE and len(rr)==40 and {x['path'] for x in rr}==adds and all(x['remote_bytes_equal'] and x['status']=='passed' and x['git_blob']==tree_rows[x['path']]['sha'] and x['sha256']==source_map[x['path']]['sha256'] and x['bytes']==source_map[x['path']]['bytes'] for x in rr))
check('publication preparation failure disclosed and retained',len(j(B/'c047-publication/preparation-failures.json')['failures'])==1)

# Bind the earlier complete raw-pair review rather than repeating its 61,593 assertions.
pair=j(B/'c047-independent-comparison/result.json');pc=j(B/'c047-independent-comparison/command.json')
check('earlier successful independent pair audit exact result',h((B/'c047-independent-comparison/result.json').read_bytes())=='65517f6fe4a5ea7f45a1da4bb12dcb8c7035e68261c7856984142ed913666aab' and pair['status']=='passed' and pair['checks_passed']==61593 and not pair['findings'] and pc['exit_code']==0 and pc['inputs_stable'] and pc['input_files']==2901)
check('pair audit exact successful code and raw logs',h((B/'c047-independent-comparison/audit_pair.py').read_bytes())=='65e62855d0d7fb8eee0022bce089999325a5770afa5b9e828e8d69f1ca390b9c' and all(matches(B/x['path'],x) for x in [pc['stdout'],pc['stderr'],pc['script_before'],pc['script_after']]) and pc['stderr']['bytes']==0)
check('earlier failed audit preserved without erasure',len(pair['failed_audit_attempts'])==1 and (B/'c047-independent-comparison/attempt-001/command.json').exists() and j(B/'c047-independent-comparison/attempt-001/command.json')['exit_code']!=0)
check('earlier pair audit before after exact stability',j(B/'c047-independent-comparison/command-inputs-before.json')==j(B/'c047-independent-comparison/command-inputs-after.json'))
commands=[j(B/('c047-execution/'+x+'-command.json')) for x in ['stock-001','capture-001']]
check('actual original command exits windows and source identity',all(x['exit_code']==x['expected_product_exit']==1 and x['process_completed'] and x['inputs_stable'] and x['source_commit']==PARENT and x['source_tree']==PTREE and within(x['started_at'],x['finished_at'],x['window']) for x in commands))
stock=j(B/'c047-execution/stock-001/report.json');observed=j(B/'c047-execution/capture-001/stock/report.json');cap=j(B/'c047-execution/capture-001/capture.json')
check('two original requests remain failed and capture errors empty',stock['status']==observed['status']=='failed' and cap['product_request_status']=='failed' and not cap['accepted_artifact'] and not cap['release_acceptance'] and cap['observation_errors']==[] and not cap['elapsed_neutrality_claimed'])
check('capture exact key ledger snapshots and failure bytes bound by archive',cap['key_calls']==154 and len(cap['ordered_cache_snapshot_files'])==311 and all(matches(B/'c047-execution/capture-001'/x['path'],x) for x in cap['ordered_cache_snapshot_files']+[cap['ledger_file'],cap['failure_locals_file'],cap['artifact']]))
check('request original options and program identity preserved',stock['deliveries'][0]['options']==observed['deliveries'][0]['options']=={'end':'4','fps':1.0,'helpers':False,'position_tolerance_m':0.001,'rotation_tolerance_rad':0.001,'time_tolerance_s':1e-6} and stock['deliveries'][0]['program_revision']==observed['deliveries'][0]['program_revision']=='sha256:0d8e38f49425cf9a0e9b96f8aadb42d7baf1743208e152aaea8f2d58f759abc7')
facts['pair_measurements']=pair['facts']['elapsed']
facts['pair_identity_summary']={k:pair['facts'][k] for k in ['shared_operations','reach_operations','work_categories','key_calls','returned_keys','snapshot_files','outer_identity_checks','per_key_identity_checks','failure','glb']}

# New independent compact retained-data check of the lifetime proof's premises.
ledger=j(B/'c047-execution/capture-001/key-ledger.json');keys=ledger['keys'];life=j(B/'c047-lifetime-review/census-001/result.json')
check('separate lifetime census passed with stable 325 inputs',life['status']=='passed' and life['checks_passed']==27 and life['input_count']==325 and not life['findings'] and j(B/'c047-lifetime-review/census-001/inputs-before.json')==j(B/'c047-lifetime-review/census-001/inputs-after.json'))
check('all lifetime declared inputs still exact',all(matches(B/x['path'],x) for x in j(B/'c047-lifetime-review/census-001/inputs-before.json')))
check('entire consecutive bounded key prefix',len(keys)==154 and [x['index'] for x in keys]==list(range(154)) and all(x['outcome']=='returned' for x in keys[:-1]) and keys[-1]['outcome']=='raised' and all(Fraction(int(x['time']['numerator']),int(x['time']['denominator']))==(Fraction(2*x['index'],87) if x['index']<=87 else Fraction(x['index']+91,89)) for x in keys))
first=keys[0];last=keys[-1]
check('key zero empty batch followed by centered False registered plan',first['entry']['source_batch']['plans']==[] and first['entry']['source_batch']['cursor_ledger_entries']==0 and len(first['exit']['source_batch']['plans'])==1 and first['exit']['source_batch']['plans'][0]['centered_recipe_fields'] is False and len(first['exit']['source_batch']['plans'][0]['targets'])==6 and len(first['exit']['source_batch']['plans'][0]['node_paths'])==8)
def centered(side): return [x for x in side['source_cursors'] if x.get('value',{}).get('type')=='_CenteredCursor']
snapshots={x['path']:j(B/'c047-execution/capture-001'/x['path']) for x in cap['ordered_cache_snapshot_files']}
check('native fixed source domain in all 311 retained snapshots',all(x['source_domain']=={'bits':128,'scale':2**128,'_cache_operand_limit':32768} and x['work_operand_limit']==32768 for x in snapshots.values()))
boundary=[];previous=set();born=[];loss=[];sizes=[];centered_counts=[]
for key in keys:
    for side in ['entry','exit']:
        state=key[side];refrow=state['source_cache_ordered_snapshot_file'];snap=snapshots[refrow['path']]
        coeff={tuple(row['key']) for row in snap['ordered_rows'] if row['key'][0]=='series_coefficients'}
        sizes.append(len(snap['ordered_rows']))
        if boundary:
            lost=previous-coeff
            if lost:loss.append({'index':key['index'],'side':side,'keys':sorted(lost)})
            new=coeff-previous
            if new:born.append({'index':key['index'],'side':side,'keys':sorted(new)})
        boundary.append({'index':key['index'],'side':side,'entries':len(snap['ordered_rows']),'coefficient_keys':sorted(coeff)})
        previous=coeff
        if side=='exit':centered_counts.append(sum(1 for row in snap['ordered_rows'] if row.get('native_type')=='_CenteredCursor' or row.get('value_type')=='_CenteredCursor' or 'centered_cursor' in row))
expected_births=[{'index':1,'side':'exit','keys':[('series_coefficients',32768,129,7),('series_coefficients',32768,129,8)]},{'index':66,'side':'exit','keys':[('series_coefficients',32768,129,13),('series_coefficients',32768,129,17)]},{'index':88,'side':'exit','keys':[('series_coefficients',32768,129,16)]}]
check('independent coefficient births exactly five current keys',born==expected_births and len(boundary[0]['coefficient_keys'])==7 and len(boundary[-1]['coefficient_keys'])==12 and loss==[],{'births':born,'losses':loss})
failed_key=['series_coefficients',32768,129,14]
check('failed coefficient absent in all 311 retained snapshots',all(all(row['key']!=failed_key for row in snap['ordered_rows']) for snap in snapshots.values()))
check('boundary occupancy nondecreasing from 112 to 165 below 256',sizes[0]==112 and sizes[-1]==165 and min(sizes)==112 and max(sizes)==165 and all(a<=b for a,b in zip(sizes,sizes[1:])))
# The ledger retains explicit native cursor class fields. Its original byte integrity was checked above.
check('centered cursor survives each exit after key zero',all(centered(key['exit']) for key in keys[1:]))
check('all boundary batches remain active unprepared and no hook authority changes',all(k[s]['source_batch']['active'] is True and k[s]['source_batch']['prepared'] is False for k in keys for s in ['entry','exit']) and all(all(v is True for v in k['identity_checks'].values()) for k in keys) and all(v is True for v in cap['identity_checks'].values()))
failure=j(B/'c047-execution/capture-001/failure-locals.json');fl={x['function']:x for x in failure['frames']};coeff=fl['_series_coefficients']['locals'];integer=fl['_series_integer']['locals'];orient=fl['_orientation']['locals']
check('current exact failed coefficient partial construction',coeff['key']==failed_key and coeff['cached'] is None and coeff['degree']==14 and coeff['exponent']==129 and coeff['index']==7 and coeff['odd']==15 and len(coeff['coefficients'])==7 and integer['kind']=='div' and integer['a']==coeff['common'] and integer['b']==coeff['factorials'][15] and fl['_series_integer']['line']==437)
check('current retired forearm reseed fails before publishing replacement',orient['advance'] is False and orient['steps']==0 and orient['previous']['steps']==64 and last['entry']['source_cursors']==last['exit']['source_cursors'] and orient['node']['path']=='rig.arm.forearm.frame')
facts['lifetime_data']={'interval':'key 0 entry through key 153 exception snapshot before outer cleanup','boundary_snapshots':len(boundary),'all_snapshots':len(snapshots),'first_entries':sizes[0],'last_entries':sizes[-1],'births':born,'coefficient_keys_initial':boundary[0]['coefficient_keys'],'coefficient_keys_final':boundary[-1]['coefficient_keys'],'failed_key':failed_key,'failed_key_present':False}

# Text/AST source binding. This does not import or run any product helper.
selection={
 'ontokin/reach_reference.py':['_Arithmetic.__init__','_Arithmetic._sync_cache_operand_limit','_Arithmetic.tick','_Arithmetic.remember','_Arithmetic.lookup','_Arithmetic._series_integer','_Arithmetic._series_coefficients','_PoseArithmetic._recording_cartesian_rotate','ReachReference._recording_centered_poses'],
 'ontokin/reach_reference_center.py':['_Guard.lookup','_Guard.remember','_orientation','_ProductSession.publish','_ProductSession.close','evaluate','prepare'],
 'ontokin/reach_reference_plan.py':['_SourceBatch.register','_SourceBatch.check_cursors','_SourceBatch.record_cursors','_SourceBatch.discard_cursors','_SourceBatch.completed_ordinary_request','_SourceBatch.__exit__','_PendingCursors.remember','_PendingCursors.publish','_Plan.evaluate','_phase_poses','recording_centered_poses'],
 'ontokin/reach_conformance.py':['_key_comparisons','_verify_certificates','_verify_certificates.compare_certificates'],
 'ontokin/construction.py':['ConstructionBudget.tick'],
 'ontokin/reach_numeric.py':['ReachExecutionWork.__init__','ReachExecutionWork.tick','ReachExecutionWork.checkpoint'],
}
bindings=[];functions={}
for path,names in selection.items():
    p=R/path
    if not p.exists(): continue
    text=p.read_text();lines=text.splitlines(keepends=True);tree=ast.parse(text)
    found={}
    def visit(node,prefix=()):
        for ch in ast.iter_child_nodes(node):
            if isinstance(ch,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef)):
                q='.'.join(prefix+(ch.name,))
                if isinstance(ch,(ast.FunctionDef,ast.AsyncFunctionDef)):found[q]=ch
                visit(ch,prefix+(ch.name,))
            else:visit(ch,prefix)
    visit(tree)
    symbols=[]
    for name in names:
        if name not in found: continue
        node=found[name];chunk=''.join(lines[node.lineno-1:node.end_lineno]);functions[(path,name)]=chunk
        symbols.append({'name':name,'start':node.lineno,'end':node.end_lineno,'source_sha256':h(chunk.encode())})
    bindings.append({'path':path,**{k:source_map[path][k] for k in ['bytes','sha256','git_blob']},'symbols':symbols,'requested_symbols_not_found':sorted(set(names)-set(found))})
save('source-bindings.json',{'core_commit':CORE,'core_tree':TREE,'executed_parent':PARENT,'executed_parent_tree':PTREE,'method':'Text and AST only; no source helpers executed','files':bindings})
check('all requested source proof symbols located',all(not x['requested_symbols_not_found'] for x in bindings))
f=lambda p,n:functions[('ontokin/'+p+'.py',n)]
product=f('reach_reference_center','_ProductSession.publish')
check('C035 product publication guarded by exact still-resident previous identity','if self.valid and self.a.cache.get(key) is previous:' in product and 'self.a.cache[key] = expanded' in product and 'del self.a.cache' not in product and 'self.a.cache.clear' not in product)
check('product session close has no reader-cache mutation','a.cache' not in f('reach_reference_center','_ProductSession.close'))
phase=f('reach_reference_plan','_phase_poses')
check('rejected centered False plan returns before centered evaluation','if type(plan.centered) is not tuple:' in phase and phase.index('if type(plan.centered) is not tuple:')<phase.index('evaluate(plan, reference, time, adopted)'))
ordinary=f('reach_reference_plan','_Plan.evaluate')
check('ordinary fallback cannot construct native centered cursor','_CenteredCursor' not in ordinary and 'centered_evaluate' not in ordinary and 'centered_stationary' not in ordinary)
check('ordinary ledger cleanup retains unchanged owned cache entries','if self.a.cache.get(key) is not value:' in f('reach_reference_plan','_SourceBatch.completed_ordinary_request'))
check('discard removes exact owned resident values and clears ledger','if self.a.cache.get(key) is value:' in f('reach_reference_plan','_SourceBatch.discard_cursors') and 'del self.a.cache[key]' in f('reach_reference_plan','_SourceBatch.discard_cursors'))
check('reader domain clear conditional on operand domain change','if self._cache_operand_limit != self.operand_limit:' in f('reach_reference','_Arithmetic._sync_cache_operand_limit') and 'self.cache.clear()' in f('reach_reference','_Arithmetic._sync_cache_operand_limit'))
check('reader replacement and capacity insert preserve size after capacity','if key in self.cache:' in f('reach_reference','_Arithmetic.remember') and 'elif len(self.cache) >= MAX_CACHE:' in f('reach_reference','_Arithmetic.remember') and 'del self.cache[next(iter(self.cache))]' in f('reach_reference','_Arithmetic.remember'))
check('failed exact integer helper tick precedes division branch',f('reach_reference','_Arithmetic._series_integer').index('self.tick()')<f('reach_reference','_Arithmetic._series_integer').index('if kind =='))
facts['source_bound_conclusion']='With fixed native operand domain and effectful discard excluded by key-zero rejected plan and surviving owned centered cursors at later exits, completed reader mutations cannot reduce size. A capacity eviction would force size to reach and remain 256, contrary to final size 165. C035 product replacement requires the previous resident object and cannot restore an evicted slot. Therefore no capacity eviction and no earlier completed/published failed coefficient key within key 0 entry through key 153 pre-cleanup snapshot. This excludes setup, outer cleanup and the failed request tail.'

# Published actual documentation and metadata validation, without executing them again.
validation=j(B/'c047-validation/result.json');dc=j(B/'c047-validation/documentation-command.json');docs=j(B/'c047-validation/documentation.stdout')
check('actual root 53-check metadata validation passed inside window',validation['status']=='passed' and validation['checks_passed']==53 and validation['inputs_stable'] and validation['source_commit']==CORE and validation['source_tree']==TREE and within(validation['started_at'],validation['finished_at'],validation['window']) and h((B/'c047-validation/result.json').read_bytes())=='0941b4f19571d664ecf19e682af34cdc731150b76282e9e4e97ef62fdfef4d8c')
check('actual unchanged documentation command zero exit and raw output binding',dc['exit_code']==0 and dc['source_commit']==CORE and within(dc['started_at'],dc['finished_at'],dc['window']) and matches(B/'c047-validation/documentation.stdout',dc['documentation.stdout']) and matches(B/'c047-validation/documentation.stderr',dc['documentation.stderr']) and dc['documentation.stderr']['bytes']==0)
check('documentation actual complete result counts',docs['sources_verified']==29 and docs['sections_verified']==233 and docs['links']['documents']==208 and docs['links']['local_links']==1671 and docs['links']['anchors']==92 and docs['failures']==[])
vb=j(B/'c047-validation/inputs-before.json');va=j(B/'c047-validation/inputs-after.json')
check('root all 2596 before after inputs stable and equal current bytes',vb==va and vb==source_rows)
prose=(E/'checkpoint-047-l03-capture.md').read_text()+'\n'+(E/'HANDOFF-047.md').read_text()
check('scope retains held runtime failed suite no elapsed neutrality and open gates','24/28' in prose and 'C035' in prose and 'held' in prose.lower() and 'elapsed' in prose.lower() and 'R01' in prose and 'Q01' in prose and '3.11' in prose and '3.12' in prose and '3.13' in prose)
check('final appendix absent from audited core','docs/engineering/reach-recording-validation-2026-10-23/checkpoint-047-validation.json' not in tree_rows)

after=[desc(p) for p in input_paths];save('inputs-after.json',after)
check('actual complete independent audit inputs stable before after',before==after,{'input_files':len(before),'input_bytes':sum(x['bytes'] for x in before)})
check('local core and working tree unchanged after audit',git('rev-parse','HEAD')==CORE and git('rev-parse','HEAD^{tree}')==TREE and git('status','--porcelain=v1')=='')
finished=datetime.now(timezone.utc).isoformat()
check('actual independent audit completion inside exclusive window',datetime.fromisoformat(finished)<=datetime.fromisoformat(EXPIRY))
result={'schema':'ontokin.c047-independent-published-core-audit/0.1','status':'passed' if all(x['passed'] for x in checks) else 'failed','started_utc':started,'finished_utc':finished,'core_commit':CORE,'core_tree':TREE,'parent_commit':PARENT,'parent_tree':PTREE,'window_comment_id':6428329816,'window_expires_utc':EXPIRY,'python':sys.version,'executable':sys.executable,'platform':platform.platform(),'checks_passed':sum(x['passed'] for x in checks),'checks_total':len(checks),'checks':checks,'input_files':len(before),'input_bytes':sum(x['bytes'] for x in before),'inputs_stable':before==after,'facts':facts,'prior_role_disclosure':'Reviewer earlier acquired and hash-verified C046 source and independently audited the original C047 pair. It did not author the capture driver, pair runner, lifetime review, published prose or core publication. The earlier pair audit clock-formula failure is retained. This new audit binds prior bytes and independently checks published core, source-control-flow premises and compact current census.','scope':'Published core only. No product imports, execution, tests, original pair rerun, archive extraction or source/remote mutation. Aggregate metadata checks are not runtime tests. Final appendix not yet present. No runtime candidate, elapsed neutrality, numerical acceptance or release acceptance.','findings':[x for x in checks if not x['passed']]}
save('result.json',result)
print(json.dumps({k:result[k] for k in ['status','started_utc','finished_utc','checks_passed','checks_total','input_files','input_bytes','inputs_stable','findings']},indent=2),flush=True)
sys.exit(0 if result['status']=='passed' else 1)
