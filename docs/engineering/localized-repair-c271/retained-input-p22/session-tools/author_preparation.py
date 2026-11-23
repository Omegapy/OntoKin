"""Author canonical installation plans from fixed archives without importing project code."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
import tarfile
from datetime import datetime, timezone

BASE = Path('/workspace/scratch/aa6113404163')
ROOT = BASE / 'prepared-source'
OUT = BASE / 'phase-p22/preparation'
OUT.mkdir(parents=True, exist_ok=False)
TARGET_PARENT = BASE / 'prepared-inputs'
TARGET_PARENT.mkdir(mode=0o755, exist_ok=False)
REQ = json.loads((BASE / 'phase-p22/prep_review/PREPARATION-REQUIREMENTS.json').read_text())

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode('ascii')

def write_new(path, value, mode=0o644):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    with os.fdopen(fd, 'wb') as f:
        f.write(canonical(value))
        f.flush()
        os.fsync(f.fileno())
    return descriptor(path)

def binding(path):
    before = path.lstat()
    assert stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and not path.is_symlink(), str(path)
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    after = path.lstat()
    assert (before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) == (after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
    return {'sha256':h.hexdigest(), 'size_bytes':before.st_size, 'mode':oct(stat.S_IMODE(before.st_mode))}

def descriptor(path):
    return {'path':str(path), **binding(path)}

def git(*args):
    return subprocess.check_output(['git', '-c', 'core.fsmonitor=false', '-C', str(ROOT), *args], text=True).rstrip('\n')

assert (ROOT / '.git').is_dir() and not (ROOT / '.git').is_symlink()
assert git('rev-parse','HEAD') == '527368bd5195c439762b43e2cc836ff9822213f8'
assert not git('status','--porcelain=v1','--untracked-files=all')
predicates = REQ['source_predicates']
paths = set(predicates['explicit_files'])
for directory in predicates['source_trees']:
    for p in (ROOT / directory).rglob('*'):
        assert not p.is_symlink() and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.pyo'), str(p)
        if p.is_file():
            paths.add(p.relative_to(ROOT).as_posix())
paths.update(p for p in predicates['optional_existing_files'] if (ROOT/p).exists())
source_inventory = {'schema':'ontokin.current-host-readback-source/0.1.0',
                    'files':{p:binding(ROOT/p) for p in sorted(paths)}}
source = {'root':str(ROOT), 'commit':git('rev-parse','HEAD'), 'tree':git('rev-parse','HEAD^{tree}'),
          'inventory':write_new(OUT/'SOURCE-INVENTORY.json',source_inventory)}
write_new(OUT/'SOURCE.json',source)

def archive_plan(name, purpose, archive_path, targets):
    expected = REQ['archives'][name]
    actual = descriptor(archive_path)
    assert actual['sha256'] == expected['sha256'] and actual['size_bytes'] == expected['size_bytes']
    members = {}
    with tarfile.open(archive_path,'r:*') as tar:
        for m in tar:
            n = m.name.rstrip('/')
            p = PurePosixPath(n)
            assert not p.is_absolute() and str(p)==n and '..' not in p.parts and '\\' not in n and n not in members
            assert m.isfile() and not m.sparse
            h = hashlib.sha256()
            stream = tar.extractfile(m)
            count = 0
            with stream:
                for chunk in iter(lambda:stream.read(1024*1024),b''):
                    count += len(chunk);h.update(chunk)
            assert count == m.size
            members[n] = {'kind':'file','size_bytes':count,'sha256':h.hexdigest(),'mode':oct(m.mode),'target':targets.get(n)}
    assert len(members)==expected['member_count']
    assert sum(x['size_bytes'] for x in members.values())==expected['expanded_bytes']
    files = {row['target']:{k:row[k] for k in ['sha256','size_bytes','mode']} for row in members.values() if row['target'] is not None}
    expected_rows = expected['member_mapping'] if name=='node' else expected['target_files']
    assert files == {row['target']:{k:row[k] for k in ['sha256','size_bytes','mode']} for row in expected_rows}
    directories = {str(parent):'0o755' for path in files for parent in PurePosixPath(path).parents if str(parent)!='.'}
    plan_name = 'NODE' if name=='node' else 'DEPENDENCIES'
    destination = TARGET_PARENT / ('node' if name=='node' else 'readback-dependencies')
    assert not destination.exists()
    plan = {'schema':'ontokin.current-host-readback-install/0.1.0','purpose':purpose,'source':source,
            'archive':actual,'destination':str(destination),'root_mode':'0o755','files':files,
            'directories':directories,'members':members,'report':str(OUT/(plan_name+'-INSTALL-REPORT.json'))}
    plan_descriptor = write_new(OUT/(plan_name+'-INSTALL-PLAN.json'), plan)
    if name!='node':
        write_new(OUT/'DEPENDENCY-INVENTORY.json',{'schema':'ontokin.current-host-readback-dependencies/0.1.0',
            'files':files,'directories':directories,'archive':actual})
    return plan_name, plan, plan_descriptor

node_targets = {row['archive_member']:row['target'] for row in REQ['archives']['node']['member_mapping']}
dep_targets = {row['archive_member']:row['target'] for row in REQ['archives']['dependencies']['target_files']}
rows = [archive_plan('node','selected-node', BASE/'retained-archives/OntoKin_C271_P05_Node_Candidate_2026-11-20.tar.gz', node_targets),
        archive_plan('dependencies','retained-dependencies',ROOT/REQ['archives']['dependencies']['relative_archive_path'],dep_targets)]
python = Path(sys.executable).resolve(strict=True)
assert binding(python)['sha256'] == REQ['host_and_launch_boundary']['python_pin_for_later_h0']['sha256']
environment = REQ['host_and_launch_boundary']['clean_environment']
ancestors = {}
for p in (TARGET_PARENT,*TARGET_PARENT.parents,OUT,*OUT.parents):
    st=p.lstat();assert stat.S_ISDIR(st.st_mode) and not p.is_symlink()
    ancestors[str(p)]={'device':st.st_dev,'inode':st.st_ino,'mode':oct(stat.S_IMODE(st.st_mode))}
launch = {'schema':'ontokin.c271.p22-preparation-launch/1','recorded_at_utc':datetime.now(timezone.utc).isoformat(),
          'source':source,'source_file_count':len(paths),'python':descriptor(python),'python_version':sys.version,
          'git':descriptor(Path('/usr/bin/git')),'preparer':descriptor(ROOT/'tools/prepare_current_host_readback.py'),
          'environment':environment,'cwd':str(ROOT),'destination_and_evidence_ancestors':ancestors,
          'execution_boundary':REQ['host_and_launch_boundary'],'commands':[],
          'stop':'Stop immediately after first failure or unknown; no automatic retry, H0/H1, target execution or second phase',
          'per_command_timeout_seconds':120,'command_order':['NODE','DEPENDENCIES'],
          'postprocess':'After each successful command, create an exclusive canonical index from the exact plan and original report descriptors; no report rewrite'}
for name,plan,d in rows:
    launch['commands'].append({'name':name,'plan':d,'argv':[str(python),'-I','-S','-B',str(ROOT/'tools/prepare_current_host_readback.py'),
        '--plan',d['path'],'--plan-sha256',d['sha256'],'--apply'],
        'expected_preparation_state':'INSTALLED_EXACT','destination':plan['destination'],
        'fresh_outputs':[plan['report'],plan['report']+'.preflight.json',plan['report']+'.publication.json',
                         str(OUT/(name+'-INSTALLATION-INDEX.json')),str(OUT/(name+'.stdout.log')),str(OUT/(name+'.stderr.log'))]})
write_new(OUT/'LAUNCH-PLAN.json',launch)
print(json.dumps({'source':source,'source_files':len(paths),'plans':[{'name':n,'descriptor':d,'members':len(p['members']),'target_files':len(p['files'])} for n,p,d in rows]}))
