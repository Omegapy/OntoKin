"""Independent C199 byte-only preflight. Never launches Blender or an exporter."""
from pathlib import Path
import hashlib
import json
import mmap
import os
import platform
import stat
import subprocess
import sys
import tarfile
from datetime import datetime, timezone

ROOT = Path('/workspace/scratch/801d9d641f68/ontokin')
OUT = Path('/workspace/scratch/801d9d641f68/c199-independent-preflight')
DOC = ROOT / 'docs/engineering/static-tray-mapping-c198'
DEP = Path('/workspace/scratch/efc86516cbb7/deps/blender-4.5.3-linux-x64')
ARCHIVE = DEP.parent / (DEP.name + '.tar.xz')
checks = []

def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()

def check(name, passed, details=None):
    checks.append({'name': name, 'pass': bool(passed), 'details': details})

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)

def js(name):
    return json.loads((DOC / name).read_text())

head = git('rev-parse', 'HEAD').decode().strip()
freeze = js('INPUT-FREEZE.json')
for row in freeze['files']:
    p = DOC / row['path']
    actual = {'bytes': p.stat().st_size, 'sha256': sha(p)}
    check('freeze:' + row['path'], actual['bytes'] == row['bytes'] and actual['sha256'] == row['sha256'], actual)
check('freeze:file-list-digest', hashlib.sha256(json.dumps(freeze['files'], sort_keys=True, separators=(',', ':')).encode()).hexdigest() == freeze['files_digest_sha256'])
check('freeze:nine-normative-inputs', len(freeze['files']) == 9)
check('freeze:39-controls', len(js('CONTROLS.json')['controls']) == freeze['control_count'] == 39)

source_bindings = []
for name in ['BASELINE-INPUTS.json', 'DEPENDENCIES.json']:
    data = js(name)
    revision = data.get('source_commit', data.get('baseline_commit'))
    tree = data.get('source_tree', data.get('baseline_tree'))
    check(name + ':tree', git('rev-parse', revision + '^{tree}').decode().strip() == tree)
    for row in data['files']:
        b = git('show', revision + ':' + row['path'])
        entry = git('ls-tree', revision, '--', row['path']).decode().strip().split('\t')[0].split()
        actual = {'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest(), 'git_mode': entry[0], 'git_blob': entry[2]}
        matches = all(actual[k] == row[k] for k in actual)
        check(name + ':' + row['path'], matches, actual)
        working = ROOT / row['path']
        source_bindings.append({'manifest': name, 'path': row['path'], 'baseline_matches': matches, 'current_matches_baseline': working.is_file() and sha(working) == row['sha256']})

required = js('DEPENDENCIES.json')['selected_external_backend']
archive_result = {'path': str(ARCHIVE), 'bytes': ARCHIVE.stat().st_size, 'sha256': sha(ARCHIVE)}
exe = DEP / 'blender'
executable_result = {'path': str(exe), 'bytes': exe.stat().st_size, 'sha256': sha(exe), 'mode': oct(stat.S_IMODE(exe.stat().st_mode))}
check('backend:archive', archive_result['bytes'] == required['archive_bytes'] and archive_result['sha256'] == required['archive_sha256'], archive_result)
check('backend:executable', executable_result['sha256'] == required['executable_sha256'], executable_result)
with exe.open('rb') as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as data:
    executable_result['expected_build_string_present'] = required['build_hash'].encode() in data
    executable_result['expected_version_string_present'] = b'4.5.3' in data
check('backend:static-build-string', executable_result['expected_build_string_present'])
check('backend:static-version-string', executable_result['expected_version_string_present'])

prefixes = ('4.5/python/', '4.5/scripts/addons_core/io_scene_gltf2/')
installed = {}
for prefix in prefixes:
    for p in sorted((DEP / prefix).rglob('*')):
        if p.is_file():
            rel = p.relative_to(DEP).as_posix()
            installed[rel] = {'path': rel, 'bytes': p.stat().st_size, 'sha256': sha(p), 'symlink': p.is_symlink()}
archive_entries = []
archive_paths = set()
with tarfile.open(ARCHIVE, mode='r|xz') as tf:
    for member in tf:
        parts = member.name.split('/', 1)
        if len(parts) != 2:
            continue
        rel = parts[1]
        if not rel.startswith(prefixes):
            continue
        archive_paths.add(rel)
        if member.isfile():
            f = tf.extractfile(member)
            h = hashlib.sha256()
            for b in iter(lambda: f.read(1024 * 1024), b''):
                h.update(b)
            row = {'path': rel, 'bytes': member.size, 'sha256': h.hexdigest(), 'mode': oct(member.mode)}
            actual = installed.get(rel)
            row['installed_matches'] = actual is not None and actual['bytes'] == row['bytes'] and actual['sha256'] == row['sha256']
            archive_entries.append(row)
            check('installed-byte:' + rel, row['installed_matches'])
        elif member.issym() or member.islnk():
            archive_entries.append({'path': rel, 'linkname': member.linkname, 'type': 'symlink' if member.issym() else 'hardlink'})
extra = [row for rel, row in installed.items() if rel not in archive_paths]

py = Path(sys.executable).resolve()
host = {'implementation': platform.python_implementation(), 'version': platform.python_version(), 'platform': platform.platform(), 'machine': platform.machine(), 'executable': str(py), 'executable_sha256': sha(py)}
check('host:target', host['implementation'] == 'CPython' and host['version'] == '3.12.14' and host['machine'] == 'x86_64' and sys.platform == 'linux', host)
loaded_modules = []
for name, module in sorted(sys.modules.items()):
    path = getattr(module, '__file__', None)
    if path and Path(path).is_file():
        p = Path(path).resolve()
        loaded_modules.append({'module': name, 'path': str(p), 'bytes': p.stat().st_size, 'sha256': sha(p)})

summary = {'schema': 'ontokin.c199.independent-byte-preflight/0.1', 'observed_at_utc': datetime.now(timezone.utc).isoformat(), 'head': head, 'head_tree': git('rev-parse','HEAD^{tree}').decode().strip(), 'input_freeze_sha256': sha(DOC / 'INPUT-FREEZE.json'), 'checks': len(checks), 'failed_checks': [x for x in checks if not x['pass']], 'status': 'PASS' if all(x['pass'] for x in checks) else 'FAIL', 'normative_files': len(freeze['files']), 'baseline_files': len(js('BASELINE-INPUTS.json')['files']), 'dependency_source_files': len(js('DEPENDENCIES.json')['files']), 'source_bindings': source_bindings, 'archive': archive_result, 'executable': executable_result, 'host': host, 'archive_inventory_entries': len(archive_entries), 'installed_inventory_entries': len(installed), 'installed_extras': len(extra), 'installed_extras_are_all_bytecode': all(x['path'].endswith('.pyc') for x in extra), 'native_processes_started': 0, 'native_exports': 0, 'receiving_processes': 0, 'qualification_status': 'NOT_RUN', 'implementation_lock_status': 'NOT_YET_CREATED_OR_REVIEWED', 'limitations': ['This checks dependency bytes, not runtime availability or native qualification.', 'Host loaded-module inventory records only this preflight, not the future implementation closure.', 'Installed bytecode extras are separately recorded; use a clean archive extraction and explicit bytecode policy in the future reviewed launch lock.']}
OUT.mkdir(parents=True, exist_ok=True)
for filename, data in [('PREFLIGHT.json', summary), ('CHECKS.json', checks), ('ARCHIVE-COMPONENT-INVENTORY.json', archive_entries), ('INSTALLED-COMPONENT-INVENTORY.json', list(installed.values())), ('INSTALLED-EXTRAS.json', extra), ('HOST-PREFLIGHT-LOADED-MODULES.json', loaded_modules)]:
    (OUT / filename).write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')
print(json.dumps({k:v for k,v in summary.items() if k != 'source_bindings'}, indent=2))
raise SystemExit(0 if summary['status'] == 'PASS' else 1)
