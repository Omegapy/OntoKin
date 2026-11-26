"""Independently materialize P27 declarations; imports no OntoKin code."""
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import stat
import struct
import zipfile

ROOT = Path('/workspace/scratch/2eb33b59a678/repository')
DESIGN = ROOT / 'docs/engineering/localized-repair-c271/required-image-design-p27'
OUT = ROOT / 'docs/engineering/localized-repair-c271/required-images-p29/controls'
OUT.mkdir(parents=True, exist_ok=True)
PLAN_RAW = (DESIGN / 'design/CONTROL-PLAN.json').read_bytes()
assert hashlib.sha256(PLAN_RAW).hexdigest() == '55dc8e776253232e7eb23e51593754f9b69cf72e23732246424adb6ed58ba89f'
CONTROL = json.loads(PLAN_RAW)
DECISION = json.loads((DESIGN / 'design/DECISION.json').read_bytes())
def canonical(v): return json.dumps(v, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode('ascii')
def digest(raw): return hashlib.sha256(raw).hexdigest()
def binding(raw, mode='0o600'): return {'sha256':digest(raw),'size_bytes':len(raw),'mode':mode}
def desc(path, raw=b'Frozen synthetic observation.\n', mode='0o644'): return {'path':path,**binding(raw,mode)}
def save(name, value):
    path=OUT/name; path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n'); path.chmod(0o644)
def put(name, raw):
    path=OUT/name; path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(raw); path.chmod(0o644)
def alias(path): return {'resolved_path':path,'symlink':False,'link_target':None}
def only_binding(d): return {k:d[k] for k in ('sha256','size_bytes','mode')}

# Unchanged companion pins/shapes are read as literal AST constants, never by
# executing the inspector. New expected semantics come only from adopted P27.
constants={}
for n in ast.parse((ROOT/'prototypes/static_tray_v01/current_host_inspection_v01.py').read_text()).body:
    if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name):
        try: constants[n.targets[0].id]=ast.literal_eval(n.value)
        except (ValueError,TypeError): pass
constants['LIMITS']={'direct_starts':2,'command_ms':5000,'active_work_ms':3000,'cleanup_ms':2000,'log_bytes':4194304,'inspection_bytes':8388608,'host_bytes':8388608,'document_bytes':16777216,'stage_bytes':67108864,'stage_entries':2048,'static_ms':60000,'publication_ms':30000}
PREFIX='ontokin.current-host-readback-'
LOADER_ALIAS='/lib64/ld-linux-x86-64.so.2'
LOADER='/usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2'
PYTHON='/required-python/bin/python'
NODE='/required-node/bin/node'
LIBC='/required-images/libc.so.6'
GIT='/required-tools/git'
SHELL='/required-tools/bash'
EXTERNAL='/required-tools/echo'
ENTRY='/required-source/prototypes/static_tray_v01/current_host_inspection_v01.py'
SUBJECTS={k:{'path':'/required-images/'+k,**v['binding']} for k,v in DECISION['catalog'].items()}
loader={'path':LOADER,**DECISION['associated_loader']}
libc={'path':LIBC,**constants['LIBC']}
python={'path':PYTHON,**constants['PYTHON']}
node={'path':NODE,**constants['NODE']}
shell=desc(SHELL,mode='0o755'); git=desc(GIT,mode='0o755'); external=desc(EXTERNAL,mode='0o755')
script=deepcopy(constants['RTLD_SCRIPT'])
all_descriptors=[*SUBJECTS.values(),loader,libc,python,node,shell,git,external,script,desc(ENTRY)]
aliases={d['path']:alias(d['path']) for d in all_descriptors}
aliases[LOADER_ALIAS]={'resolved_path':LOADER,'symlink':True,'link_target':'../lib/x86_64-linux-gnu/ld-linux-x86-64.so.2'}
files={d['path']:only_binding(d) for d in all_descriptors}
roles={'node':NODE,'python':PYTHON,'ldd':'/usr/bin/ldd','inspector_interpreter':SHELL,'elf_interpreter':LOADER_ALIAS,
       'loader_configuration':[], 'shared_libraries':[SUBJECTS['libdl.so.2']['path'],LIBC],
       'inspector_runtime':[d['path'] for d in [*SUBJECTS.values(),libc,git,shell,external,script]]}
needed=['libpthread.so.0','libdl.so.2','libutil.so.1','libm.so.6','librt.so.1','libc.so.6']
def meta(soname=None, needed=(), interpreter=None, rpath=()):
    return {'class':64,'endian':'little','machine':62,'type':3,'interpreter':interpreter,'needed':list(needed),'soname':soname,'rpath':list(rpath),'runpath':[]}
python_meta=meta(needed=needed,interpreter=LOADER_ALIAS,rpath=['$ORIGIN/../lib'])
images=[]
for key,d in SUBJECTS.items():
    m=deepcopy(DECISION['catalog'][key]['actual_fixture_metadata'])
    images.append({'file':deepcopy(d),'metadata':m,'resolved_needed':{n:LOADER_ALIAS if n=='ld-linux-x86-64.so.2' else LIBC for n in m['needed']}})
images += [{'file':deepcopy(libc),'metadata':meta('libc.so.6'),'resolved_needed':{}},
           {'file':deepcopy(loader),'metadata':meta('ld-linux-x86-64.so.2'),'resolved_needed':{}},
           {'file':deepcopy(python),'metadata':python_meta,'resolved_needed':{k:SUBJECTS[k]['path'] if k in SUBJECTS else LIBC for k in needed}},
           {'file':deepcopy(node),'metadata':meta(needed=['libdl.so.2'],interpreter=LOADER_ALIAS),'resolved_needed':{'libdl.so.2':SUBJECTS['libdl.so.2']['path']}},
           *[{'file':deepcopy(d),'metadata':meta(interpreter=LOADER_ALIAS),'resolved_needed':{}} for d in (git,shell,external)]]
edges=[{'image':r['file']['path'],'soname':n,'resolved_path':aliases[p]['resolved_path']} for r in images for n,p in r['resolved_needed'].items()]
components=[('/', 'directory',None),('/lib','symlink','usr/lib'),('/lib64','symlink','usr/lib64'),('/usr','directory',None),('/usr/lib','directory',None),('/usr/lib/x86_64-linux-gnu','directory',None),(LOADER,'file',None),('/usr/lib64','directory',None),('/usr/lib64/ld-linux-x86-64.so.2','symlink','../lib/x86_64-linux-gnu/ld-linux-x86-64.so.2')]
rtld_model={'schema':PREFIX+'rtld-paths/0.1.0','components':[{'path':p,'kind':kind,'target':target,'identity':[1,i+1,{'directory':stat.S_IFDIR|0o755,'symlink':stat.S_IFLNK|0o777,'file':stat.S_IFREG|0o755}[kind],1,225672 if kind=='file' else 0,1,1]} for i,(p,kind,target) in enumerate(components)],'absences':[{'path':'/lib/ld-linux.so.2','nearest_existing_ancestor':'/usr/lib','first_missing':'/usr/lib/ld-linux.so.2','remaining_suffix':[]},{'path':'/libx32/ld-linux-x32.so.2','nearest_existing_ancestor':'/','first_missing':'/libx32','remaining_suffix':['ld-linux-x32.so.2']}]}
rtld_snapshot={'results':[{'path':LOADER_ALIAS,'resolved_path':LOADER,'binding':only_binding(loader)}],'observations':[]}
rationale_raw=b'Frozen synthetic source-completeness prerequisite; not an approval.\n'
rationale=desc('/required-documents/rationale.txt',rationale_raw)
origin={'schema':PREFIX+'python-origin-rpath/0.1.0','subject':deepcopy(python),'invocation':PYTHON,'raw_rpath':['$ORIGIN/../lib'],'origin':'/required-python/bin','expanded_rpath':['/required-python/lib'],'kernel_origin':{'exe_path':PYTHON,'at_secure':0},'variant_review':desc('/required-documents/variants.json'),'variants':[],'needed_names':needed}
resolution={'profile':DECISION['new_pair']['resolution_profile'],'images':images,'needed_edges':edges,'loader_inputs':[],
 'search_directories':[{'path':'/required-python/lib','device':1,'inode':2,'mode':'0o755','entries':{}}],
 'inspector_commands':{'script':script,'interpreter':shell,'commands':[external], 'rtld_candidates':[{'path':LOADER_ALIAS,'state':'file','binding':only_binding(loader)}, {'path':'/lib/ld-linux.so.2','state':'absent','parent':'/lib'}, {'path':'/libx32/ld-linux-x32.so.2','state':'absent','parent':'/libx32'}]},
 'ignored_kernel_rows':[],'rationale':rationale,'origin_rpath':origin,'libc_plt':{'schema':PREFIX+'libc-plt/0.1.0','subject':libc,'loader':loader},'rtld_paths':rtld_model,
 'required_images':{'schema':DECISION['closed_shapes']['required_images_schema'],'catalog':DECISION['closed_shapes']['required_images_catalog'],'loader':deepcopy(loader),'subjects':deepcopy(SUBJECTS)}}
attempt='/required-evidence/attempt'
outputs={k:attempt+'/'+k+'.json' for k in ('reserved','preflight','result','completion')}; outputs['host']=attempt+'/HOST.json'
commands=[]
for name,label in [('node_version','host-node-version'),('shared_libraries','host-shared-libraries')]:
    stage=attempt+'/'+name
    outputs[name]={k:stage+'/'+k+'.json' for k in ('intent','started','inspection','postflight','failure')}
    outputs[name].update(stdout=stage+'/'+label+'.stdout.log',stderr=stage+'/'+label+'.stderr.log',supervisor_outcome={'raw':stage+'/'+label+'.process.json','committed':stage+'/supervisor-outcome.json'})
    commands.append({'id':name,'argv':[NODE,'--version'] if name=='node_version' else ['/usr/bin/ldd',NODE],'cwd':stage,'label':label,'timeout_ms':5000,'active_work_ms':3000,'cleanup_ms':2000,'expected_direct_starts':1,'stdout_predicate':'v24.22.1\n' if name=='node_version' else 'linux-glibc-declared-closure-v1','stderr_predicate':''})
plan={'schema':DECISION['new_pair']['plan_schema'],'contract':PREFIX[:-1]+'/0.1.0',
 'source':{'root':'/required-source','commit':'1'*40,'tree':'2'*40,'inventory':desc('/required-documents/source.json')},
 'author':{'entry_point':ENTRY,'source_descriptor':desc(ENTRY),'python_descriptor':python,'python_version':'3.12.0','runtime_inventory':desc('/required-documents/runtime.json'),'metadata_inventory':desc('/required-documents/metadata.json'),'git_descriptor':git,'source_commands':[]},
 'runtime':{'executable':NODE,'version':'v24.22.1','candidate':constants['NODE'],'source_archive':{'path':'/required-inputs/node.tar','sha256':constants['NODE_ARCHIVE_SHA256'],'size_bytes':constants['NODE_ARCHIVE_BYTES'],'mode':'0o600'},'install_receipt':desc('/required-documents/node-install.json')},
 'dependencies':{'root':'/required-dependencies','inventory':desc('/required-documents/dependencies.json'),'install_receipt':desc('/required-documents/dependencies-install.json')},
 'host_static':{'platform':{'system':'Linux','release':'synthetic','machine':'x86_64','libc':['glibc','2.41'],'boot_id':'synthetic-not-host'},'files':files,'aliases':aliases,'roles':roles,'resolution':resolution,'path_guards':[]},
 'environment':constants['ENVIRONMENT'],'limits':constants['LIMITS'],'commands':commands,
 'evidence':{'parent':'/required-evidence','attempt_root':attempt,'ancestor_identities':[],'outputs':outputs,'outer_capture':{'authority':desc('/required-documents/authority.txt'),'log':desc('/required-documents/caller.log')}}}
runtime={'executable':PYTHON,'interpreter':LOADER_ALIAS,'startup_files':[d['path'] for d in [*SUBJECTS.values(),libc]],'extension_files':[],'loader_inputs':[],'files':deepcopy(files),'aliases':deepcopy(aliases)}
base={'operational':False,'plan':plan,'runtime':runtime,'actual_python_metadata':deepcopy(python_meta),
      'libc_policy':{'schema':plan['schema'],'subject':libc,'loader':loader},'origin_policy':origin,'rationale_raw_ascii':rationale_raw.decode(),
      'rtld_snapshot':rtld_snapshot,'expected_resolution':{'libraries':{'libdl.so.2':SUBJECTS['libdl.so.2']['path'],'libc.so.6':LIBC},'interpreter':LOADER_ALIAS,'vdso':[]},
      'plan_path':'/required-documents/plan.json','git_state':{'synthetic':True},'source_inventory':{'files':{}},
      'mock_boundaries':['source/runtime/host/origin/libc/RTLD/guard prerequisite observations are stipulated, not proven','ROOT and logical Path.resolve/is_symlink projections do not observe a host','new selector, constructor, _bound comparisons, dispatch, private raw reads, caller order and wrappers remain real']}
save('BASE-CONTEXT.json',base)

def image_bytes(inp):
    spec=deepcopy(CONTROL['base_definitions']['SYNTHETIC_LIBDL']); spec.update({k:v for k,v in inp.items() if k not in ('base','mutation')}); spec.update(inp.get('mutation',{}))
    strings=bytearray(b'\0')
    def add(text):
        off=len(strings); strings.extend(text.encode('ascii')+b'\0'); return off
    entries=[]
    for n in ([spec['needed_name']] if 'needed_name' in spec else spec['needed']): entries.append((1,add(n)))
    entries.append((14,add(spec.get('soname','libdl.so.2'))))
    for name,tag in [('rpath',15),('runpath',29)]:
        if spec.get(name): entries.append((tag,add(':'.join(spec[name]))))
    tags=deepcopy(spec['plt_tags'])
    if 'plt_values' in spec: tags=[[tag,value] for (tag,_),value in zip(tags,spec['plt_values'])]
    if spec.get('remove_all_plt_tags'): tags=[]
    if 'remove_dynamic_tag' in spec: tags=[x for x in tags if x[0]!=spec['remove_dynamic_tag']]
    if 'duplicate_dynamic_tag' in spec: tags.append(deepcopy(next(x for x in tags if x[0]==spec['duplicate_dynamic_tag'])))
    if 'extra_dynamic_tag' in spec: tags.append([spec['extra_dynamic_tag'],0])
    entries += [tuple(x) for x in tags] + [(30,v) for v in spec['dt_flags_entries']] + [(0x6ffffffb,v) for v in spec['dt_flags_1_entries']]
    count=len(entries)+2+(not spec.get('remove_final_dynamic_terminator',False))
    dynsize=spec.get('dynamic_table_bytes',count*16); dynoff=512; stroff=dynoff+dynsize
    entries=[(5,0x400000+stroff),(10,len(strings))]+entries
    if not spec.get('remove_final_dynamic_terminator'):
        entries += [(21,0)]*((dynsize//16)-len(entries)-1)+[(0,0)]
    rawdyn=b''.join(struct.pack('<qQ',*x) for x in entries)
    assert len(rawdyn)==dynsize
    length=stroff+len(strings)
    ident=b'\x7fELF'+bytes([2,1,1,spec.get('osabi',0)])+b'\0'*8
    head=ident+struct.pack('<HHIQQQIHHHHHH',spec.get('elf_type',spec.get('type',3)),spec.get('machine',62),1,0,64,0,0,64,56,2,0,0,0)
    ph=struct.pack('<IIQQQQQQ',1,4,0,0x400000,0,length,length,4096)+struct.pack('<IIQQQQQQ',2,4,dynoff,0x400000+dynoff,0,dynsize,dynsize,8)
    raw=head+ph+b'\0'*(dynoff-len(head)-len(ph))+rawdyn+strings
    return bytes(raw),{'pread_ranges':[[0,64],[64,112],[dynoff,dynsize],[stroff,len(strings)]],'nonnull_dynamic_entries':len(entries)-(not spec.get('remove_final_dynamic_terminator',False)),'catalog_key':spec.get('catalog_key','libdl.so.2')}

def coherent_binding(context,key,field,value):
    r=context['plan']['host_static']['resolution']; d=r['required_images']['subjects'][key]; d[field]=value; path=d['path']
    next(x for x in r['images'] if x['file']['path']==path)['file'][field]=value
    context['plan']['host_static']['files'][path][field]=value; context['runtime']['files'][path][field]=value

def relation_context(cid):
    c=deepcopy(base); p=c['plan']; h=p['host_static']; r=h['resolution']; s=r['required_images']['subjects']; path=s['libdl.so.2']['path']; py=next(x for x in r['images'] if x['file']['path']==PYTHON)
    if cid=='RI-D01': c['actual_python_metadata']['needed'].remove('libdl.so.2')
    elif cid=='RI-D02':
        for name in ('inspector_runtime','shared_libraries'): h['roles'][name]=[x for x in h['roles'][name] if x!=path]
    elif cid=='RI-D03': del c['runtime']['aliases'][path]
    elif cid=='RI-D04': c['runtime']['aliases'][path]['resolved_path']='/required-images/different.so'
    elif cid=='RI-D05': c['runtime']['aliases'][path].update(symlink=True,link_target='elsewhere')
    elif cid=='RI-D06': next(x for x in r['images'] if x['file']['path']==path)['file']['sha256']='0'*64
    elif cid=='RI-D07': r['images'].append(deepcopy(next(x for x in r['images'] if x['file']['path']==path)))
    elif cid=='RI-D08':
        selected='/required-images/selected-elsewhere.so'; py['resolved_needed']['libdl.so.2']=selected
        h['roles']['inspector_runtime'].append(selected)
        for aliases in (h['aliases'],c['runtime']['aliases']): aliases[selected]=alias(selected)
        for filemap in (h['files'],c['runtime']['files']): filemap[selected]=only_binding(s['libdl.so.2'])
    elif cid=='RI-D09':
        a,b='libdl.so.2','libpthread.so.0'; s[a],s[b]=s[b],s[a]; py['resolved_needed'][a]=s[a]['path']; py['resolved_needed'][b]=s[b]['path']
    elif cid in ('RI-D10','RI-D11','RI-D12'): coherent_binding(c,'libdl.so.2',{'RI-D10':'sha256','RI-D11':'size_bytes','RI-D12':'mode'}[cid],{'RI-D10':'0'*64,'RI-D11':14409,'RI-D12':'0o755'}[cid])
    elif cid=='RI-D13': r['required_images']['loader']['sha256']='0'*64
    elif cid=='RI-D14': s['libdl.so.2']['path']=s['libm.so.6']['path']
    elif cid=='RI-D15': c['runtime']['extension_files'].append(path)
    elif cid=='RI-D16': r['inspector_commands']['commands'].append(deepcopy(s['libdl.so.2']))
    elif cid.startswith('RI-D17'):
        s['libdl.so.2']['path']={'A':LIBC,'B':LOADER,'C':PYTHON,'D':NODE,'E':GIT,'F':script['path'],'G':SHELL,'H':ENTRY}[cid[-1]]
    elif cid=='RI-D18': del c['runtime']['files'][path]
    elif cid=='RI-C02': coherent_binding(c,'libutil.so.1','sha256','0'*64)
    if cid=='RI-C01': r['images'].sort(key=lambda row:row['file']['path'],reverse=True); r['images'].sort(key=lambda row:row['file']['path']==PYTHON)
    return c

def selector_context(cid):
    c=deepcopy(base); p=c['plan']; r=p['host_static']['resolution']; ri=r['required_images']
    if cid=='RI-S01': r['profile']='linux-glibc-declared-python-origin-rpath-libc-plt-static-tls-rtld-paths-v1'
    elif cid=='RI-S02': p['schema']=PREFIX+'inspection-plan/0.1.6'
    elif cid=='RI-S03': del r['required_images']
    elif cid=='RI-S04': ri['schema']=PREFIX+'required-images/0.1.1'
    elif cid=='RI-S05': ri['catalog']='glibc-any-version'
    elif cid=='RI-S06': ri['approved']=True
    elif cid=='RI-S07': ri['subjects']['libother.so.1']=desc('/required-images/libother.so.1')
    elif cid=='RI-S08': del ri['subjects']['libutil.so.1']
    elif cid=='RI-S09': ri['subjects']['libdl.so.2']['size_bytes']=True
    elif cid=='RI-S10': ri['subjects']['libdl.so.2']['path']='relative/libdl.so.2'
    elif cid=='RI-S11': ri['flags_mask']=24
    elif cid=='RI-S13': r['allow_extra_images']=True
    elif cid in ('RI-S14','RI-S15','RI-S16'): del r[{'RI-S14':'origin_rpath','RI-S15':'rtld_paths','RI-S16':'libc_plt'}[cid]]
    return c

profiles=['linux-glibc-declared-closure-v1','linux-glibc-declared-python-origin-rpath-v1','linux-glibc-declared-python-origin-rpath-libc-plt-v1','linux-glibc-declared-python-origin-rpath-libc-plt-static-tls-v1','linux-glibc-declared-python-origin-rpath-libc-plt-static-tls-rtld-paths-v1']
cases=[]
for source_case in CONTROL['cases']:
    case=deepcopy(source_case); cid=case['id']; case['operational']=False; case['test_method']='test_'+cid.replace('-','_'); case['source_case_sha256']=digest(canonical(source_case))
    if case['route'].startswith('private_') and 'actual_inert' not in case['route']:
        raw,layout=image_bytes(case['input']); name='images/'+cid+'.elf.inert'; put(name,raw)
        case['fixture']={'scope':'controls','path':name,**binding(raw,'0o644'),'layout':layout}
    elif 'fixture' in case['input']:
        rel='design/'+case['input']['fixture']; path=DESIGN/rel; raw=path.read_bytes()
        case['fixture']={'scope':'repository','path':path.relative_to(ROOT).as_posix(),**binding(raw,'0o644')}
    if case['route']=='pure_selector': context=selector_context(cid)
    elif case['route'] in ('mocked_relation_and_policy','mocked_post_metadata_relation','mocked_dispatch','pure_relation_callback_fault') or cid.startswith('RI-C'): context=relation_context(cid)
    elif case['route']=='old_schema_closed_shape':
        context=deepcopy(base); p=context['plan']; r=p['host_static']['resolution']; version=ord(cid[-1])-ord('A'); p['schema']=case['input']['old_schema']; r['profile']=profiles[version]
        for key,minversion in [('origin_rpath',1),('libc_plt',2),('rtld_paths',4)]:
            if version<minversion: del r[key]
    else: context=None
    if context is not None:
        name='contexts/'+cid+'.json'; save(name,context); case['context']=name
    case['execution_status']='NOT_RUN'; cases.append(case)

# The old corpus manifests are inspected as inert JSON, without importing tests.
inventories={}
for phase,mod,cls in [('p16','test_current_host_libc_plt_metadata_v01','LibcPltFrozenTests'),('p17','test_current_host_libc_static_tls_flags_v01','LibcStaticTlsFrozenTests')]:
    rel='docs/engineering/localized-repair-c271/'+('libc-tags-p16' if phase=='p16' else 'libc-flags-p17')+'/design/CANDIDATE001.zip'
    with zipfile.ZipFile(ROOT/rel) as z: rows=json.loads(z.read('candidate001/CONTROLS.json'))['cases']
    inventories[mod]=sorted(mod+'.'+cls+'.test_'+r['id'] for r in rows)
matrix=json.loads((ROOT/'docs/engineering/localized-repair-c271/path-design-p24/reviews/path/CONTROL-MATRIX.json').read_bytes())
mod='test_current_host_rtld_paths_v01'
inventories[mod]=sorted([mod+'.RTLDPathControls.test_'+r['id'] for r in matrix['cases'] if r['id']!='N34'] + [mod+'.'+cls.name+'.'+method.name for cls in ast.parse((ROOT/'tests'/f'{mod}.py').read_text()).body if isinstance(cls,ast.ClassDef) and cls.name=='SupplementalControls' for method in cls.body if isinstance(method,ast.FunctionDef) and method.name.startswith('test_')])
save('INHERITED-INVENTORIES.json',{'methods':inventories,'external_only':['P24-N34','historical-N57'],'test_results':'NOT_RUN'})

# Freeze the exact C06 fake receipt, all raw streams, five store publications,
# their complete payloads and descriptors before any product execution.
c=deepcopy(base); p=c['plan']; command=commands[0]; paths=outputs['node_version']
plan_descriptor=desc(c['plan_path'],canonical(p))
mock_process={'argv':command['argv'],'cwd':command['cwd'],'environment':p['environment'],'label':command['label'],'start_monotonic':1000.0,'pid':12345,'process_group':12345,'returncode':0,'observed_log_bytes':10,'retained_log_bytes':10,'cleanup':{'passed':True,'process_group_absent':True,'reaped':True,'elapsed_ms':0.0},'handles_closed':True,'error':None,'end_monotonic':1000.1}
raws={paths['supervisor_outcome']['raw']:canonical(mock_process),paths['stdout']:b'v24.22.1\n',paths['stderr']:b''}
# The literal output has nine bytes; retain exact literal-derived counts.
mock_process['observed_log_bytes']=mock_process['retained_log_bytes']=len(raws[paths['stdout']]); raws[paths['supervisor_outcome']['raw']]=canonical(mock_process)
artifacts={key:desc(path,raws[path],'0o600') for key,path in [('raw_process',paths['supervisor_outcome']['raw']),('stdout',paths['stdout']),('stderr',paths['stderr'])]}
preflight={'passed':True,'mocked':True}
record={'schema':PREFIX+'inspection-attempt/0.1.0','plan':plan_descriptor,'command_id':command['id'],'expected_argv':command['argv'],'expected_direct_starts':1,'actual_direct_starts':None,'observed_direct_starts':0,'start_count_state':'UNKNOWN','state':'UNKNOWN','preflight':preflight,'start':None,'supervisor_process':None,'supervisor_failure':None,'postflight':None,'artifacts':{},'evidence_finalized':False,'failure':None}
expected={paths['intent']:deepcopy(record)}
when='2026-01-01T00:00:00+00:00'
start={'schema':PREFIX+'inspection-start/0.1.0','plan':plan_descriptor,'command_id':command['id'],'process':mock_process,'observed_at_utc':when}
expected[paths['started']]=start; start_descriptor=desc(paths['started'],canonical(start))
outcome={'decoded_raw_process':mock_process,'schema':PREFIX+'inspection-supervisor-outcome/0.1.0','plan':plan_descriptor,'command_id':command['id'],'process':mock_process,'supervisor_failure':None,'observed_start':mock_process,'artifacts':artifacts,'faults':[]}
expected[paths['supervisor_outcome']['committed']]=outcome
cause={'code':'CHI-INSPECTOR','reason':'Bound file identity differs: /required-images/libdl.so.2','state':'REJECTED','details':{},'cause':None}
failure={'code':'CHI-DRIFT','reason':'An admitted input changed before/after the command','state':'REJECTED','details':{'stage':'recheck','rule_id':'LP-RECHECK'},'cause':cause}
publication_names=[paths['intent'],paths['started'],paths['supervisor_outcome']['committed']]
expected[paths['failure']]={'schema':PREFIX+'inspection-failure/0.1.0','plan':plan_descriptor,'command_id':command['id'],'failure':failure,'process':mock_process,'observed_start':mock_process,'publications':[{'destination':x} for x in publication_names]}
record.update(actual_direct_starts=1,observed_direct_starts=1,start_count_state='OBSERVED_ONE',state='REJECTED',start=start_descriptor,supervisor_process=desc(paths['supervisor_outcome']['committed'],canonical(outcome)),postflight={'passed':False,'failure':failure},artifacts=artifacts,evidence_finalized=True,failure=failure)
expected[paths['postflight']]=record
save('MOCK-COMMAND.json',{'operational':False,'command':command,'process':mock_process,'preflight':preflight,'utc':when,'plan_descriptor':plan_descriptor,'raw_ascii':{k:v.decode('ascii') for k,v in raws.items()},'expected_publications':[{'path':path,'payload':payload,'descriptor':desc(path,canonical(payload))} for path,payload in expected.items()],'target_starts':{'node':0,'ldd':0,'direct_loader':0,'cpu_checker':0},'fake_run_process_calls':1})
prelaunch_expected={paths['intent']:deepcopy(expected[paths['intent']])}
prelaunch_error=next(case['expected'] for case in CONTROL['cases'] if case['id']=='RI-C05')
prelaunch_error={key:deepcopy(prelaunch_error[key]) for key in ('code','reason','state','details','cause')}
prelaunch_expected[paths['failure']]={'schema':PREFIX+'inspection-failure/0.1.0','plan':plan_descriptor,'command_id':command['id'],'failure':prelaunch_error,'process':None,'observed_start':None,'publications':[{'destination':paths['intent']}]}
prelaunch_record=deepcopy(prelaunch_expected[paths['intent']])
prelaunch_record.update(actual_direct_starts=0,observed_direct_starts=0,start_count_state='PROVEN_ZERO',state='REJECTED',evidence_finalized=True,failure=prelaunch_error)
prelaunch_expected[paths['postflight']]=prelaunch_record
save('MOCK-PRELAUNCH.json',{'operational':False,'command':command,'preflight':preflight,'plan_descriptor':plan_descriptor,'raw_ascii':{},'snapshot_fixture':{'relative_name':'libdl.so.2','before_ascii':'inert snapshot fixture\n','after_ascii':'changed inert snapshot fixture\n','mode':'0o600'},'expected_publications':[{'path':path,'payload':payload,'descriptor':desc(path,canonical(payload))} for path,payload in prelaunch_expected.items()],'target_starts':{'node':0,'ldd':0,'direct_loader':0,'cpu_checker':0},'fake_run_process_calls':0,'real_launch_check_calls':1,'stipulated_initial_preflight_calls':1,'claim':'Real _run_command and _launch_check refuse actual inert temporary-file identity drift before the counted fake process boundary. Initial preflight and the complete memory-store outputs are stipulated, not host or durability evidence.'})
save('CONTROL-CROSSWALK.json',{'schema':'ontokin.c271.p29-control-crosswalk/1','plan_sha256':digest(PLAN_RAW),'obligations':len(cases),'cases':cases,'results':'NOT_RUN'})
save('ADAPTER-CONTRACT.json',{'schema':'ontokin.c271.p29-adapter-contract/1','helpers':['_select_required_images_profile(schema,resolution)','_prepare_required_images_policy(plan,runtime,python_metadata,libc_policy,*,check=lambda:None)','_read_required_image_elf_metadata(path,catalog_key,*,check=lambda:None,require_interpreter=False)','_required_image_checkpoint(check,stage)','_read_plan_elf_metadata(path,policy,*,check=lambda:None,require_interpreter=False,libc_policy=None,required_policy=None)'],'policy_exact_keys':['schema','subjects','loader'],'subject_values':'immutable exact descriptors keyed by fixed catalog key','checkpoint_stages':DECISION['callback_rules']['new_checkpoints'],'all_product_execution':'NOT_RUN','mock_boundaries':base['mock_boundaries']})
inherited_modules=json.loads((DESIGN/'design/FUTURE-SURFACE.json').read_bytes())['required_inherited_test_modules']+['tests/test_current_host_readback_provider.py','tests/test_current_host_readback_driver.py']
cohort_relative='docs/engineering/localized-repair-c271/required-images-p29/INHERITED-COHORT.json'
cohort_sha='dab30610b44cdb0596c395505a940722506e2c5535ed58b0984317f261de6efe'
assert digest((ROOT/cohort_relative).read_bytes())==cohort_sha
inherited_script='''import hashlib,json,os,sys,unittest
from pathlib import Path
cohort_path=Path(COHORT_PATH)
raw=cohort_path.read_bytes()
assert hashlib.sha256(raw).hexdigest()==COHORT_SHA, 'Frozen cohort differs'
cohort=json.loads(raw)
out=Path(os.environ.get('ONTOKIN_INHERITED_RETAIN_ROOT') or str(Path(os.environ['ONTOKIN_INHERITED_INVENTORY_PATH']).parent/'inherited-results'))
out.mkdir(parents=True,exist_ok=False)
for key,name in [('ONTOKIN_HI_RETAIN_ROOT','inspection'),('ONTOKIN_ELF_RETAIN_ROOT','mapping'),('ONTOKIN_LP_RETAIN_ROOT','loader'),('ONTOKIN_LIBC_RETAIN_ROOT','libc'),('ONTOKIN_RTLD_RETAIN_ROOT','rtld')]:
    os.environ.setdefault(key,str(out/name))
sys.path.insert(0,'tests')
suite=unittest.defaultTestLoader.loadTestsFromNames(MODULE_NAMES)
def flatten(suite):
    for item in suite:
        if isinstance(item,unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item.id()
ids=sorted(flatten(suite))
inventory={'expected_ids':sorted(cohort['selected_test_ids']),'actual_ids':ids,'exact_match':ids==sorted(cohort['selected_test_ids']),'cohort_sha256':COHORT_SHA,'production_sha256':hashlib.sha256(Path('prototypes/static_tray_v01/current_host_inspection_v01.py').read_bytes()).hexdigest(),'expected_non_target_child':cohort['expected_non_target_child'],'exclusions':[]}
inventory_path=Path(os.environ.get('ONTOKIN_INHERITED_INVENTORY_PATH',str(out/'RUNTIME-INVENTORY.json')))
with inventory_path.open('x') as stream:
    stream.write(json.dumps(inventory,indent=2)+'\\n')
print(json.dumps({'runtime_methods':len(ids),'exact_inventory_match':inventory['exact_match']}),flush=True)
assert inventory['exact_match'], 'Runtime method inventory differs before execution'
class RecordingResult(unittest.TextTestResult):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs); self.methods=[]
    def addSuccess(self,test):
        self.methods.append({'id':test.id(),'status':'passed'}); super().addSuccess(test)
    def addError(self,test,error):
        self.methods.append({'id':test.id(),'status':'error'}); super().addError(test,error)
    def addFailure(self,test,error):
        self.methods.append({'id':test.id(),'status':'failed'}); super().addFailure(test,error)
    def addSkip(self,test,reason):
        self.methods.append({'id':test.id(),'status':'skipped','reason':reason}); super().addSkip(test,reason)
with (out/'unittest.txt').open('x') as stream:
    result=unittest.TextTestRunner(stream=stream,verbosity=2,resultclass=RecordingResult).run(suite)
report={'tests_run':result.testsRun,'methods':result.methods,'failures':[(t.id(),text) for t,text in result.failures],'errors':[(t.id(),text) for t,text in result.errors],'skipped':[(t.id(),reason) for t,reason in result.skipped],'expected_non_target_child':cohort['expected_non_target_child']}
(out/'RESULTS.json').write_text(json.dumps(report,indent=2)+'\\n')
print(json.dumps({'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped)}))
sys.exit(not(result.wasSuccessful() and not result.skipped and result.testsRun==len(ids)))
'''.replace('COHORT_PATH',repr(cohort_relative)).replace('COHORT_SHA',repr(cohort_sha)).replace('MODULE_NAMES',repr([Path(p).stem for p in inherited_modules]))
inherited_command=['python3','-c',inherited_script]
save('COMMANDS.json',{'scope':'Run only after independent fixture/adapter freeze acceptance. No host admission or Node/ldd/direct-loader/CPU-checker target starts.','focused':['python3','-m','unittest','discover','-s','tests','-p','test_current_host_required_images_v01.py','-v'],'required_inherited_modules':inherited_modules,'inherited_command':inherited_command,'inherited_cohort':{'path':cohort_relative,'sha256':cohort_sha,'selected_ids':372},'inherited_exclusions':[],'superseded_proposal':'record-checks/INHERITED-COHORT-CANDIDATE001.json proposed371 with one excluded child; Director/reviewer retained all372 before execution.','inherited_non_target_child':'The unchanged driver transport control starts one inline Python unittest child for environment transport; it imports no OntoKin product or CPU/native readback. Director/reviewer explicitly retained this control.','evidence_environment':'ONTOKIN_REQUIRED_IMAGES_RETAIN_ROOT=<new empty absolute evidence directory>; inherited roots are selected under it by the adapter. For the separate full inherited command set ONTOKIN_INHERITED_RETAIN_ROOT=<another new absolute evidence directory>; its per-module retained roots are set by the frozen command.','status':'NOT_RUN'})
refs=[DESIGN/'design/CONTROL-PLAN.json',DESIGN/'design/DECISION.json',DESIGN/'design/DESIGN.md',DESIGN/'design/FUTURE-SURFACE.json',DESIGN/'ADOPTION.json']
refs += list((DESIGN/'design/sources/package-images').glob('*.inert'))
refs += [ROOT/p for p in inherited_modules]
refs += [ROOT/('docs/engineering/localized-repair-c271/'+d+'/design/CANDIDATE001.zip') for d in ('libc-tags-p16','libc-flags-p17')]
refs += [ROOT/'docs/engineering/localized-repair-c271/path-design-p24'/rel for rel in ('SCHEMA.json','reviews/path/CONTROL-MATRIX.json','reviews/path/CONTROL-CROSSWALK.json')]
refs += [ROOT/cohort_relative]
save('COMPANIONS.json',{'files':[{'path':p.relative_to(ROOT).as_posix(),**binding(p.read_bytes(),oct(stat.S_IMODE(p.stat().st_mode)))} for p in refs]})
save('REVISION.json',{'schema':'ontokin.c271.p29-fixture-revision/1','candidate':'candidate002','previous_candidate':{'freeze_sha256':'4e794172745f0cdb99b6050313eca8a08967fefe871ee4cf636dfb6ed1a4be14','adapter_sha256':'f43c0586ff4f5cf91388a8914f0969be73cf8c8b2a17119d212588bdafa9e7f2','preserved_archive':'docs/engineering/localized-repair-c271/required-images-p29/fixture-revisions/CANDIDATE001.zip','archive_sha256':'801b4700361f9347ade3409ff9562bfa3783fdbd9858359cd4f5a3eee71c1073'},'reviewer_findings':['Observe _git_state separately from _check_git and every not-reached recheck stage, including exact early/final resolution entries.','C05 runs the real enclosing command/launch check with a counted zero fake-process boundary and frozen three-publication failure record.','P07 compares the entire frozen policy including every descriptor, preserving nested immutability checks.','F05 observes zero descriptor opens, no policy return and the exact terminal third-subject checkpoint sequence.'],'adopted_p27_expectations_changed':False,'design_change':False,'product_imports_or_execution':0})
print(json.dumps({'obligations':len(cases),'synthetic_images':len(list((OUT/'images').glob('*.inert'))),'logical_contexts':len(list((OUT/'contexts').glob('*.json'))),'inherited_methods':{k:len(v) for k,v in inventories.items()},'product_execution':'NOT_RUN'},indent=2))
