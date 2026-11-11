"""Read-only CPython and bounded OS-library inventory; no Blender main launch."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
import platform
import re
import stat
import subprocess
import sys
import sysconfig

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', required=True)
parser.add_argument('--blender', required=True)
args=parser.parse_args()
OUT=Path(args.output).resolve()
BLENDER=Path(args.blender).resolve()
OUT.mkdir(parents=True,exist_ok=True)
for name in ('HOST-RUNTIME-INVENTORY.json','LDD-PYTHON.txt','LDD-BLENDER.txt'):
    if (OUT/name).exists():raise ValueError('Refuse to replace existing inventory evidence: '+name)
PYTHON=Path(sys.executable).resolve()
STDLIB=Path(sysconfig.get_paths()['stdlib'])
RUNTIME=Path(sys.base_prefix)
LIB_ROOTS=[Path('/usr/lib/x86_64-linux-gnu'),Path('/usr/lib64')]
cache={}
records={}

def hashed(path):
    target=path.resolve(strict=True)
    key=str(target)
    if key not in cache:
        info=target.stat()
        if not stat.S_ISREG(info.st_mode):
            raise ValueError('Not regular: '+key)
        h=hashlib.sha256()
        with target.open('rb') as f:
            for chunk in iter(lambda:f.read(1024*1024),b''):
                h.update(chunk)
        cache[key]={'bytes':info.st_size,'sha256':h.hexdigest(),'mode':oct(stat.S_IMODE(info.st_mode))}
    return target,cache[key]

def add(path,role):
    path=Path(path).absolute()
    target,d=hashed(path)
    key=str(path)
    if key not in records:
        records[key]={'path':key,'resolved_path':str(target),**d,'roles':[],
                      'symlink':path.is_symlink(),'link_target':os.readlink(path) if path.is_symlink() else None}
    if role not in records[key]['roles']:
        records[key]['roles'].append(role)
    if len(records)>12000:
        raise ValueError('File inventory ceiling exceeded')

add(PYTHON,'host_python_executable')
for p in sorted((RUNTIME/'bin').glob('python*')):
    if p.is_file() and p.resolve()==PYTHON:
        add(p,'host_python_executable_alias')

excluded=[]
stdlib_count=0
for root,dirs,names in os.walk(STDLIB,followlinks=False):
    removed=[d for d in dirs if d in {'site-packages','dist-packages'}]
    excluded.extend(str(Path(root)/d) for d in removed)
    dirs[:]=sorted(d for d in dirs if d not in {'site-packages','dist-packages'})
    for name in sorted(names):
        p=Path(root)/name
        if p.is_file():
            add(p,'host_standard_library')
            stdlib_count+=1

libpython_paths=[]
for p in sorted((RUNTIME/'lib').glob('libpython*')):
    if p.is_file():
        add(p,'host_libpython')
        libpython_paths.append(str(p))
for root,dirs,names in os.walk(RUNTIME/'lib',followlinks=False):
    dirs[:]=sorted(d for d in dirs if d not in {'site-packages','dist-packages'})
    for name in sorted(names):
        if '.so' in name:
            p=Path(root)/name
            if p.is_file():add(p,'host_runtime_shared_library')

trace=[]
ldd=Path('/usr/bin/ldd')
add(ldd,'dependency_inspection_tool')
for name,exe in [('python',PYTHON),('blender',BLENDER)]:
    cp=subprocess.run([str(ldd),str(exe)],capture_output=True,text=True,timeout=30,check=False)
    log=OUT/('LDD-'+name.upper()+'.txt')
    log.write_text(cp.stdout+cp.stderr)
    entries=[]
    for line in cp.stdout.splitlines():
        match=re.search(r'(?:=>\s+)?(/\S+)\s+\(',line)
        if match:
            p=Path(match.group(1))
            add(p,'ldd_'+name+'_resolution')
            entries.append(str(p))
    unresolved=[line.strip() for line in (cp.stdout+cp.stderr).splitlines() if 'not found' in line]
    trace.append({'command':[str(ldd),str(exe)],'returncode':cp.returncode,'log':log.name,
                  'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest(),'resolved_paths':entries,
                  'unresolved':unresolved,'meaning':'Dynamic-loader dependency trace only; target executable main was not invoked'})
    if cp.returncode!=0 or unresolved:
        raise ValueError('Unresolved loader dependency: '+name)

for root in LIB_ROOTS:
    if root.is_dir():
        for p in sorted(root.rglob('*')):
            if '.so' in p.name and p.is_file():
                add(p,'overinclusive_system_shared_library')

config_roots=[Path('/usr/share/glvnd/egl_vendor.d'),Path('/usr/share/vulkan/icd.d'),Path('/etc/ld.so.conf.d')]
config_state=[]
for root in config_roots:
    config_state.append({'path':str(root),'exists':root.exists()})
    if root.is_dir():
        for p in sorted(root.rglob('*')):
            if p.is_file():add(p,'graphics_or_loader_configuration')
for p in [Path('/etc/ld.so.cache'),Path('/etc/ld.so.conf'),Path('/etc/ld.so.preload')]:
    config_state.append({'path':str(p),'exists':p.exists()})
    if p.is_file():add(p,'loader_configuration')

unique_bytes=sum(r['bytes'] for r in cache.values())
if unique_bytes>8*1024**3:
    raise ValueError('Bounded shared-library inventory exceeded 8 GiB')
files=[records[k] for k in sorted(records)]
for row in files:row['roles'].sort()
data={'schema':'ontokin.c200.host-runtime-inventory/0.1','status':'PASS_STATIC_INVENTORY',
      'observed_at_utc':datetime.now(timezone.utc).isoformat(),'platform':platform.platform(),
      'machine':platform.machine(),'python_implementation':platform.python_implementation(),
      'python_version':platform.python_version(),'python_executable':str(PYTHON),
      'python_executable_sha256':records[str(PYTHON)]['sha256'],
      'stdlib_root':str(STDLIB),'stdlib_files':stdlib_count,
      'excluded_site_package_roots':sorted(excluded),'libpython_paths':libpython_paths,
      'system_library_roots':[str(p) for p in LIB_ROOTS],
      'system_selection':'All regular files or symlink targets whose basename contains .so, recursively under the explicit roots. Overinclusive coverage includes GL/EGL/Mesa/DRI loaders and other unused libraries.',
      'limits':{'max_paths':12000,'max_unique_regular_bytes':8*1024**3},
      'configuration_roots':config_state,'ldd_inspections':trace,'files':files,
      'file_paths':len(files),'unique_regular_targets':len(cache),'unique_regular_bytes':unique_bytes,
      'files_digest_sha256':hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
      'blender_main_starts':0,'controlled_lifecycle_starts':0,'native_qualification_starts':0,
      'scope':'Exact static byte inventory of the host interpreter/stdlib and an explicit overinclusive OS shared-library set, plus trusted ldd dependency inspection.',
      'limitations':['Static ldd does not prove dynamic renderer/importer initialization, device availability or all future dlopen choices.',
                     'The executable lock must bind actual launch environment and the full separately inventoried Blender archive.',
                     'Any dynamically loaded file outside this recorded set needs prior lock coverage or a rejected qualification result; absence from ldd is not approval.',
                     'Kernel/vDSO and device state are recorded by platform and later execution receipts, not represented as immutable ordinary files.',
                     'No Blender main, actual renderer, GLB import, native export or controlled lifecycle child was launched.']}
path=OUT/'HOST-RUNTIME-INVENTORY.json'
path.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':data['status'],'path':str(path),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'stdlib_files':stdlib_count,'files':len(files),'unique_regular_targets':len(cache),'unique_regular_bytes':unique_bytes,'ldd_resolutions':{Path(x['command'][1]).name:len(x['resolved_paths']) for x in trace},'limits':data['limits']},indent=2))
