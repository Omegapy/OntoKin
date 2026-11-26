"""Retain candidate003 bytes and author records before the metadata-leaf repair."""
from pathlib import Path
import hashlib
import json
import stat
import zipfile

BASE = Path('/workspace/scratch/2eb33b59a678')
ROOT = BASE / 'repository'
AREA = ROOT / 'docs/engineering/localized-repair-c271/required-images-p29'
FREEZE = AREA / 'controls/FREEZE.json'
EXPECTED = 'ca54eae3708af5e72f6d01c39a17b625511b8de1411b77d0a7ac0d7427eeae1a'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    assert path.resolve() == path and stat.S_ISREG(path.lstat().st_mode)
    return path.read_bytes()


freeze_raw = read(FREEZE)
assert digest(freeze_raw) == EXPECTED
freeze = json.loads(freeze_raw)
companions = json.loads(read(AREA / 'controls/COMPANIONS.json'))['files']
payloads = {}
for row in freeze['files'] + companions:
    path = ROOT / row['path']
    raw = read(path)
    assert len(raw) == row['size_bytes'] and digest(raw) == row['sha256']
    assert oct(stat.S_IMODE(path.stat().st_mode)) == row['mode']
    if row['path'] in payloads:
        assert payloads[row['path']] == raw
    payloads[row['path']] = raw
payloads[FREEZE.relative_to(ROOT).as_posix()] = freeze_raw
assert len(freeze['files']) == 115 and len(companions) == 24 and len(payloads) == 140
archive = AREA / 'fixture-revisions/CANDIDATE003.zip'
with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED, compresslevel=9) as output:
    for name, data in sorted(payloads.items()):
        entry = zipfile.ZipInfo(name, date_time=(2026, 11, 23, 23, 11, 0))
        entry.create_system = 3
        entry.external_attr = (stat.S_IFREG | 0o644) << 16
        entry.compress_type = zipfile.ZIP_DEFLATED
        output.writestr(entry, data)
with zipfile.ZipFile(archive) as saved:
    assert saved.testzip() is None and len(saved.namelist()) == len(set(saved.namelist()))
    assert set(saved.namelist()) == set(payloads)
    for name, data in payloads.items():
        assert saved.read(name) == data
author = BASE / 'reviews/fixture-author'
destination = author / 'candidate003'
destination.mkdir(exist_ok=False)
author_files = []
for path in sorted(author.iterdir()):
    if not path.is_file():
        continue
    raw = read(path)
    with (destination / path.name).open('xb') as output:
        output.write(raw)
    assert read(destination / path.name) == raw
    author_files.append({'path': str((destination / path.name).relative_to(BASE)), 'bytes': len(raw), 'sha256': digest(raw)})
record = {
    'schema': 'ontokin.c271.p29-fixture-candidate-preservation/1',
    'candidate': '003',
    'archive': archive.name,
    'bytes': archive.stat().st_size,
    'sha256': digest(read(archive)),
    'freeze_sha256': EXPECTED,
    'adapter_sha256': freeze['adapter']['sha256'],
    'files': len(payloads),
    'bound_payloads': 115,
    'bound_companions': 24,
    'verified': True,
    'status': 'accepted_then_nested_RTLD_recording_metadata_dependency_blocked_in_focused_attempt',
    'finding': 'Focused attempt001 passed 115 of 116 obligations. RI-L08 discovered61 inherited RTLD/supplemental methods but ran only10 supplemental methods because the recording-only platform.platform leaf attempted uname -p in RTLD setUpClass and was blocked by the outer process guard before launch. No oracle or production change is authorized by this preservation.',
    'failure_evidence': 'verification/implementation-focused-001/control-data/required-images/RI-L08.json',
    'failure_evidence_sha256': '28038c710f692023611e35467920059e3c4d7a024cda92affb65d56491170872',
    'author_files': author_files,
    'preservation_product_imports_or_execution': 0,
}
path = archive.with_name('CANDIDATE003-ARCHIVE.json')
with path.open('x') as output:
    output.write(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2))
