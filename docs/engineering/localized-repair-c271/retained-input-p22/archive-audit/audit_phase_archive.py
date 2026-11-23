"""Independent inert ZIP audit; reads bytes and Git objects, never payload code."""
from datetime import datetime, timezone
from collections import Counter
from pathlib import Path, PurePosixPath
import hashlib
import json
import re
import stat
import subprocess
import sys
import zipfile

ROOT = Path('/workspace/scratch/aa6113404163')
OUT = ROOT / 'phase-p22/archive_audit'
REPO = ROOT / 'OntoKin'
archive_path = Path(sys.argv[1]).resolve()
label = sys.argv[2]
identity_path = Path(sys.argv[3]).resolve()
expected = json.loads(identity_path.read_bytes())
checks = {}
details = {}

def identity(data):
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}

def safe(name):
    return (bool(name) and not name.startswith('/') and '\\' not in name and '\0' not in name and
            not re.match(r'^[A-Za-z]:', name) and all(x not in ('', '.', '..') for x in name.split('/')) and
            str(PurePosixPath(name)) == name)

def check(name, passed, detail=None):
    checks[name] = bool(passed)
    if detail is not None:
        details[name] = detail

def parse(data):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Duplicate JSON key: ' + key)
            result[key] = value
        return result
    return json.loads(data, object_pairs_hook=pairs)

def entries(value):
    return value if isinstance(value, list) else value['files']

def git(*args):
    return subprocess.run(['git', '-C', str(REPO), *args], capture_output=True, check=True).stdout

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')

data = archive_path.read_bytes()
check('exact_archive_identity', identity(data) == {'bytes': expected['bytes'], 'sha256': expected['sha256']})
with zipfile.ZipFile(archive_path) as z:
    infos = z.infolist()
    names = [i.filename for i in infos]
    check('zip_crc', z.testzip() is None)
    check('unique_safe_member_paths', len(names) == len(set(names)) and all(safe(n) for n in names))
    check('regular_inert_unencrypted_files', all(not i.is_dir() and not i.flag_bits & 1 and
          stat.S_IFMT(i.external_attr >> 16) == stat.S_IFREG and
          stat.S_IMODE(i.external_attr >> 16) == 0o644 for i in infos),
          {'modes': dict(Counter(oct(i.external_attr >> 16) for i in infos))})
    members = {n: z.read(n) for n in names}

required = ['README-START-HERE.md', 'CHECKPOINT.json', 'HANDOFF.md', 'NEXT-TASK.md',
            'RECOVERY-STATUS.md', 'PROMPT-1-CONTINUE.md', 'PROMPT-2-RECOVER.md',
            'HISTORICAL-DEPENDENCIES.json', 'MANIFEST-SHA256.json']
check('all_required_root_members', all(n in members for n in required))
manifest = entries(parse(members['MANIFEST-SHA256.json']))
mapped = [r['path'] for r in manifest]
check('exact_manifest_inventory', len(mapped) == len(set(mapped)) and set(mapped) == set(names) - {'MANIFEST-SHA256.json'})
inventory = [{'path': r['path'], **identity(members[r['path']]),
              'equal': identity(members[r['path']]) == {'bytes': r['bytes'], 'sha256': r['sha256']}} for r in manifest]
check('all_manifest_sizes_and_hashes', all(x['equal'] for x in inventory))
extraction = OUT / 'derived' / (label.lower() + '-fresh-extraction')
if extraction.exists():
    raise FileExistsError('Fresh extraction already exists; preserve it and select a new label: ' + str(extraction))
extraction.mkdir(parents=True)
if not checks['unique_safe_member_paths'] or not checks['regular_inert_unencrypted_files']:
    raise ValueError('Unsafe archive refused before extraction')
for name, content in members.items():
    dest = extraction / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(content)
    dest.chmod(0o644)
actual_paths = {p.relative_to(extraction).as_posix() for p in extraction.rglob('*') if p.is_file()}
check('fresh_extraction_exact_inventory', actual_paths == set(names))
check('fresh_extraction_all_bytes_equal', all((extraction / n).read_bytes() == content for n, content in members.items()))

sources = entries(parse(members['SOURCE-MANIFEST.json']))
source_results = []
source_names = []
for row in sources:
    member = row.get('package_path', row.get('member'))
    revision = row.get('git_revision', row.get('revision'))
    path = row.get('git_path', row.get('path'))
    mode = row.get('git_mode', row.get('source_mode'))
    source_names.append(member)
    content = members[member]
    metadata, actual_path = git('ls-tree', revision, '--', path).decode().strip().split('\t', 1)
    actual_mode, kind, blob_id = metadata.split(' ')
    matches = (actual_path == path and actual_mode == mode and kind == 'blob' and blob_id == row['git_blob'] and
               git('cat-file', 'blob', revision + ':' + path) == content and
               identity(content) == {'bytes': row['bytes'], 'sha256': row['sha256']})
    source_results.append({'member': member, 'revision': revision, 'path': path, 'matches': matches})
check('source_manifest_exact_unique_inventory', len(source_names) == len(set(source_names)) and
      set(source_names) == {n for n in names if n.startswith(('repository/', 'observed-main/'))})
check('all_source_git_bindings_modes_and_bytes', all(x['matches'] for x in source_results))

recovery = entries(parse(members['RECOVERY-FILE-MAP.json']))
recovery_names = [r.get('path', r.get('member')) for r in recovery]
check('recovery_map_exact_unique_session_inventory', len(recovery_names) == len(set(recovery_names)) and
      set(recovery_names) == {n for n in names if n.startswith('recovery/session/')})
check('all_recovery_sizes_and_hashes', all(identity(members[r.get('path', r.get('member'))]) ==
      {'bytes': r['bytes'], 'sha256': r['sha256']} for r in recovery))

checkpoint = parse(members['CHECKPOINT.json'])
check('identity_record_source_checkpoint_agree', checkpoint['source_revision'] == expected['source_revision'] and
      checkpoint['source_tree'] == expected['source_tree'] and checkpoint['package_kind'] == expected['kind'])
check('counts_match_identity_record', len(names) == expected['members'] and len(manifest) == expected['payloads'] and
      len(sources) == expected['source_bindings'] and len(recovery) == expected['recovery_files'])
check('source_commit_tree_matches_git', git('cat-file', 'commit', checkpoint['source_revision']).splitlines()[0].decode() == 'tree ' + checkpoint['source_tree'])
check('main_commit_tree_matches_git', git('cat-file', 'commit', checkpoint['observed_main']['sha']).splitlines()[0].decode() == 'tree ' + checkpoint['observed_main']['tree'])

record = {'schema': 'ontokin.c271.p22-archive-byte-review/1', 'reviewer': '/root/archive_audit',
          'at_utc': datetime.now(timezone.utc).isoformat(),
          'archive': {'path': str(archive_path), **identity(data)},
          'identity_record': {'path': str(identity_path), **identity(identity_path.read_bytes())},
          'counts': {'members': len(names), 'manifest_files': len(manifest), 'source_bindings': len(sources), 'recovery_files': len(recovery)},
          'checks': checks, 'details': details, 'source_results': source_results,
          'inventory': inventory, 'all_passed': all(checks.values()),
          'derived_extraction': {'path': str(extraction), 'source_archive_sha256': identity(data)['sha256'],
                                 'files': len(names), 'inventory_and_every_byte_equal': True,
                                 'disposition': 'Exact derived extraction only. May omit from final package if this source archive identity and audit report are retained; no deletion authorized.'},
          'scope': 'Bytes and Git objects only; no archived/repository code execution or mutation'}
save(OUT / (label.upper() + '-BYTE-AUDIT.json'), record)
print(json.dumps({'label': label, 'all_passed': record['all_passed'], 'groups': len(checks),
                  'counts': record['counts'], 'failed': [k for k, v in checks.items() if not v]}))
