"""P19 read-only actual-input observation; this is not an H0 plan runner."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import re
import stat
import sys
import time
import types

ROOT = Path('/workspace/scratch/816157c5a30b/OntoKin')
OUT = Path('/workspace/scratch/816157c5a30b/technical/attempt001')
SOURCE = ROOT / 'prototypes/static_tray_v01/current_host_inspection_v01.py'
SOURCE_SHA = 'e14542e45deb200bb97f2a591c94bdd19916a1d33dcb3ce9f631816b98e0c206'
LOCK_SHA = 'a7f17491000c2e139ccc5d213ca0e8a6f917e5befb4b878fef29f5ff72ae780f'
PYTHON = Path('/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3.12')
LOADER = Path('/usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2')
LIBC = Path('/usr/lib/x86_64-linux-gnu/libc.so.6')
PINS = {
    'python': (PYTHON, 30894944, 'fa67443527ed9647f760d807e2a38f26340757123e643c4639cf273ed15d5ea7'),
    'loader': (LOADER, 225672, 'c8438e4fde1934e61c88311633f00949ff645d5c04cdb8671fa3d78164d2f307'),
    'libc': (LIBC, 1995216, '9792e3cbb541c8f44c7acf5f14f4022ea62998ecc787d326bed4d8b6547dfd92'),
}
ENV = {'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TZ':'UTC','UV_THREADPOOL_SIZE':'2'}
START = time.monotonic()
EVENTS = []
OBS = []
METADATA = []
RAW = {}
BEFORE = {}

class InputBlocker(RuntimeError):
    def __init__(self, code, details):
        self.code, self.details = code, details
        super().__init__(code)

def check():
    if time.monotonic() - START > 60:
        raise InputBlocker('OBSERVATION_DEADLINE', {'seconds':60})

def guard(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork', 'pty.spawn')) or event in ('os.system','os.kill','os.killpg','ctypes.dlopen','socket.__new__'):
        EVENTS.append({'event':event, 'arguments_retained':False})
        raise InputBlocker('FORBIDDEN_PROCESS_OR_NATIVE_OPERATION', {'event':event})

sys.addaudithook(guard)

def sha(data): return hashlib.sha256(data).hexdigest()

def identity(info):
    return {'device':info.st_dev,'inode':info.st_ino,'size_bytes':info.st_size,
            'mode':oct(stat.S_IMODE(info.st_mode)),'mtime_ns':info.st_mtime_ns,
            'ctime_ns':info.st_ctime_ns,'nlink':info.st_nlink}

def bounded(path, maximum):
    check()
    fd=os.open(path, os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        before=os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_size>maximum:
            raise InputBlocker('UNSAFE_OR_OVERSIZED_INPUT', {'path':str(path),'identity':identity(before)})
        blocks=[];total=0
        while True:
            check();b=os.read(fd,min(1024*1024,maximum-total+1))
            if not b: break
            total+=len(b)
            if total>maximum: raise InputBlocker('INPUT_LIMIT', {'path':str(path)})
            blocks.append(b)
        data=b''.join(blocks)
        if identity(before)!=identity(os.fstat(fd)) or identity(before)!=identity(Path(path).lstat()):
            raise InputBlocker('INPUT_CHANGED', {'path':str(path)})
        BEFORE[str(path)]={'identity':identity(before),'sha256':sha(data)}
        return data,identity(before)
    finally: os.close(fd)

def write(name,value):
    with (OUT/name).open('x') as f: json.dump(value,f,indent=2);f.write('\n')

def normalized(value): return re.sub('[-_.]+','-',value).lower()

def observe():
    if dict(os.environ)!=ENV or not (sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode) or 'site' in sys.modules:
        raise InputBlocker('CLEAN_LAUNCHER_MISMATCH', {'environment_keys':sorted(os.environ),'isolated':sys.flags.isolated,'no_site':sys.flags.no_site,'dont_write_bytecode':sys.dont_write_bytecode})
    if Path(sys.executable)!=PYTHON or Path('/proc/self/exe').resolve()!=PYTHON:
        raise InputBlocker('SELECTED_PYTHON_PATH_MISMATCH', {'sys_executable':sys.executable,'proc_self_exe':os.readlink('/proc/self/exe')})
    # Fixed byte identities precede product import and metadata interpretation.
    for role,(path,size,expected) in PINS.items():
        data,info=bounded(path,40*1024*1024)
        row={'role':role,'path':str(path),'canonical_path':str(path.resolve()),**info,'sha256':sha(data)}
        OBS.append(row)
        if path.resolve()!=path or len(data)!=size or sha(data)!=expected or info['mode']!='0o755':
            raise InputBlocker('FIXED_INPUT_PIN_MISMATCH', {'actual':row,'expected':{'size_bytes':size,'sha256':expected,'mode':'0o755'}})
    raw_source,source_info=bounded(SOURCE,1024*1024)
    if len(raw_source)!=196305 or sha(raw_source)!=SOURCE_SHA:
        raise InputBlocker('SOURCE_IDENTITY_MISMATCH', {'path':str(SOURCE),'sha256':sha(raw_source),'size_bytes':len(raw_source)})
    with Path('/proc/self/maps').open('rb') as f:
        maps_bytes=f.read(1024*1024+1)
    if len(maps_bytes)>1024*1024: raise InputBlocker('MAPS_LIMIT', {})
    maps=maps_bytes.decode()
    # Only selected-image rows are retained; no claim of complete process closure.
    relevant=[]
    for line in maps.splitlines():
        fields=line.split(None,5)
        if len(fields)==6 and fields[5] in {str(PYTHON),str(LOADER),str(LIBC)}:
            relevant.append(line)
    RAW['selected_process_maps']=relevant
    for role,(path,_,_) in PINS.items():
        rows=[line.split(None,5) for line in relevant if line.split(None,5)[5]==str(path)]
        info=path.stat()
        if not rows or any(int(row[4])!=info.st_ino or tuple(int(x,16) for x in row[3].split(':'))!=(os.major(info.st_dev),os.minor(info.st_dev)) for row in rows):
            raise InputBlocker('MAPPED_ROLE_IDENTITY_MISMATCH', {'role':role,'path':str(path)})
    module=types.ModuleType('p19_bound_inspection_source')
    module.__file__=str(SOURCE)
    exec(compile(raw_source,str(SOURCE),'exec'),module.__dict__)
    readers=[('python',module._read_origin_elf_metadata,True),('loader',module.read_elf_metadata,False),('libc',module._read_libc_static_tls_elf_metadata,False)]
    for role,reader,requires_interpreter in readers:
        check()
        row={'role':role,'reader':reader.__name__,'route':'raw_metadata_primitive_only','operational_policy_admitted':False}
        RAW.setdefault('metadata_observations',[]).append(row)
        try:
            row['metadata']=reader(PINS[role][0],check=check,require_interpreter=requires_interpreter)
            row['outcome']='metadata_returned'
        except module.HostInspectionError as exc:
            row['outcome']='refused';row['refusal']={'code':exc.code,'reason':exc.reason,'state':exc.state,'details':exc.details,'cause':str(exc.cause) if exc.cause else None}
            raise InputBlocker('ACTUAL_RAW_METADATA_REFUSAL', row['refusal']) from exc
    python_metadata=RAW['metadata_observations'][0]['metadata']
    if 'libc.so.6' not in python_metadata['needed'] or Path(python_metadata['interpreter']).resolve()!=LOADER:
        raise InputBlocker('PYTHON_LIBC_LOADER_RELATION_MISMATCH', {'python_metadata':python_metadata})
    RAW['limited_relation']={'actual_python_needed_includes_libc':True,'actual_python_interpreter_resolves_to_pinned_loader':True,'complete_loader_selection_proved':False}
    # Next H0 prerequisite: inspect distribution text without importing site/packages.
    lock=ROOT/'tools/native-reader-verification-linux-cp312.lock'
    lock_bytes,lock_info=bounded(lock,64*1024)
    if sha(lock_bytes)!=LOCK_SHA:
        raise InputBlocker('LOCK_IDENTITY_MISMATCH', {'expected_sha256':LOCK_SHA,'observed_sha256':sha(lock_bytes)})
    pins=[]
    for line in lock_bytes.decode().splitlines():
        if not line or line.startswith('#'): continue
        match=re.fullmatch(r'([A-Za-z0-9_.-]+)==([^ ]+) --hash=sha256:([0-9a-f]{64})',line)
        if not match: raise InputBlocker('UNRECOGNIZED_LOCK_ROW', {'line':line})
        pins.append({'name':match[1],'version':match[2],'wheel_sha256':match[3]})
    if len(pins)!=7: raise InputBlocker('LOCK_COUNT_MISMATCH', {'count':len(pins)})
    RAW['pin_lock']={'path':str(lock),'sha256':sha(lock_bytes),**lock_info,'pins':pins}
    packages=PYTHON.parent.parent/'lib/python3.12/site-packages'
    if not packages.is_dir(): raise InputBlocker('PACKAGE_METADATA_ROOT_MISSING', {'path':str(packages)})
    entries=[]
    for entry in packages.iterdir():
        check();entries.append(entry)
        if len(entries)>4096: raise InputBlocker('PACKAGE_DIRECTORY_LIMIT', {'count':len(entries)})
    entries.sort(key=lambda x:x.name)
    RAW['package_root']={'path':str(packages),'identity':identity(packages.stat()),'scope':'selected interpreter standard site-packages directory; no alternate environment search'}
    for pin in pins:
        check();name=pin['name']
        candidates=[x for x in entries if x.name.endswith('.dist-info') and normalized(x.name[:-10].rsplit('-',1)[0])==normalized(name)]
        row={'name':name,'expected_version':pin['version'],'candidate_roots':[str(x) for x in candidates]};METADATA.append(row)
        if len(candidates)!=1: raise InputBlocker('PACKAGE_METADATA_MISSING_OR_AMBIGUOUS',row)
        dist=candidates[0]
        if dist.is_symlink() or not dist.is_dir(): raise InputBlocker('PACKAGE_METADATA_UNSAFE_ROOT',row)
        data,info=bounded(dist/'METADATA',4*1024*1024)
        with (OUT/('METADATA-'+normalized(name)+'.txt')).open('xb') as f:
            f.write(data)
        header=data.decode().split('\n\n',1)[0]
        names=re.findall(r'^Name: ([^\r\n]+)$',header,re.M);versions=re.findall(r'^Version: ([^\r\n]+)$',header,re.M)
        row.update({'metadata_path':str(dist/'METADATA'),'metadata_sha256':sha(data),'identity':info,'observed_names':names,'observed_versions':versions})
        if len(names)!=1 or len(versions)!=1 or normalized(names[0])!=normalized(name) or versions[0]!=pin['version']:
            raise InputBlocker('PACKAGE_METADATA_PIN_MISMATCH',row)
        row['outcome']='metadata_name_version_match_only'
    RAW['all_seven_metadata_names_versions_match']=True

OUT.mkdir(mode=0o700,parents=False,exist_ok=False)
script=Path(__file__).read_bytes()
write('INTENT.json',{'schema':'ontokin.c271.p19-actual-input-intent/1','recorded_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'script_sha256':sha(script),'source_sha256':SOURCE_SHA,'argv':sys.argv,'selected_order':['python identity','loader identity','libc identity','source identity','mapped-role witness','raw Python metadata','raw loader metadata','raw libc0.1.3 metadata','limited actual dependency relation','package metadata in lockfile order'],'stop':'first new mismatch/refusal; no repair/substitution/retry','expectation':'exact pins and unchanged adopted reader predicates; no predetermined success','process_starts_permitted':0})
failure=None
try:
    observe()
except BaseException as exc:
    failure={'type':type(exc).__name__,'code':getattr(exc,'code','UNEXPECTED_OBSERVATION_ERROR'),'details':getattr(exc,'details',{}),'message':str(exc)}
finally:
    after=[]
    for path,before in BEFORE.items():
        try:
            data,info=bounded(Path(path),40*1024*1024)
            after.append({'path':path,'identity_unchanged':info==before['identity'],'bytes_unchanged':sha(data)==before['sha256']})
        except BaseException as exc:
            after.append({'path':path,'error':str(exc),'identity_unchanged':False,'bytes_unchanged':False})
    postflight_failures=[x for x in after if not x['identity_unchanged'] or not x['bytes_unchanged']]
    if postflight_failures and failure is None:
        failure={'type':'InputBlocker','code':'POSTFLIGHT_INPUT_OR_DEADLINE_FAILURE','details':{'failed_rechecks':postflight_failures},'message':'Post-read identity/hash/deadline verification failed'}
    result={'schema':'ontokin.c271.p19-actual-input-result/1','at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'elapsed_seconds':time.monotonic()-START,'source_revision':'2f791017c6559bfd47937b32b1862cfe98a81551','source_sha256':SOURCE_SHA,'script_sha256':sha(script),'python_version':sys.version,'observations':OBS,'raw':RAW,'package_metadata':METADATA,'first_blocker':failure,'post_read_rechecks':after,'postflight_failures':postflight_failures,'process_operation_attempts':EVENTS,'direct_target_starts':0,'h0_accepted':False,'operational_plan_created':False,'operational_policy_admitted':False,'h1_approved':False,'N57':'external_only_not_evaluated','status':'input_blocked' if failure else 'raw_inputs_passed_complete_h0_review_still_required'}
    write('RESULT.json',result)
    print(json.dumps({'status':result['status'],'first_blocker':failure,'metadata_readers':[(x['role'],x['outcome']) for x in RAW.get('metadata_observations',[])],'packages_checked':len(METADATA),'forbidden_attempts':len(EVENTS),'post_read_equal':all(x['identity_unchanged'] and x['bytes_unchanged'] for x in after),'h0_accepted':False}))
sys.exit(2 if failure else 0)
