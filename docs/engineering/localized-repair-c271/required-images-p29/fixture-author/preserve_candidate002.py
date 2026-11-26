"""Preserve the accepted second fixture candidate before inventory correction."""
from pathlib import Path
import hashlib
import json
import stat
import zipfile

BASE = Path('/workspace/scratch/2eb33b59a678')
ROOT = BASE / 'repository'
AREA = ROOT / 'docs/engineering/localized-repair-c271/required-images-p29'
FREEZE = AREA / 'controls/FREEZE.json'
EXPECTED_FREEZE = 'a705a493a37d907eb677bc3e207a99670ef2ca3d906ef82087a3a815f218bc09'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_ordinary(path):
    assert path.resolve() == path and stat.S_ISREG(path.lstat().st_mode)
    return path.read_bytes()


freeze_raw = read_ordinary(FREEZE)
assert digest(freeze_raw) == EXPECTED_FREEZE
freeze = json.loads(freeze_raw)
companions = json.loads(read_ordinary(AREA / 'controls/COMPANIONS.json'))['files']
rows = freeze['files'] + companions
payloads = {}
for row in rows:
    path = ROOT / row['path']
    data = read_ordinary(path)
    assert len(data) == row['size_bytes'] and digest(data) == row['sha256'], row['path']
    assert oct(stat.S_IMODE(path.stat().st_mode)) == row['mode'], row['path']
    if row['path'] in payloads:
        assert payloads[row['path']] == data
    payloads[row['path']] = data
payloads[FREEZE.relative_to(ROOT).as_posix()] = freeze_raw
assert len(freeze['files']) == 115 and len(companions) == 24

archive = AREA / 'fixture-revisions/CANDIDATE002.zip'
assert not archive.exists()
with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED, compresslevel=9) as out:
    for name, data in sorted(payloads.items()):
        entry = zipfile.ZipInfo(name, date_time=(2026, 11, 23, 23, 0, 0))
        entry.create_system = 3
        entry.external_attr = (stat.S_IFREG | 0o644) << 16
        entry.compress_type = zipfile.ZIP_DEFLATED
        out.writestr(entry, data)
with zipfile.ZipFile(archive) as saved:
    assert saved.testzip() is None
    assert len(saved.namelist()) == len(set(saved.namelist()))
    assert set(saved.namelist()) == set(payloads)
    for name, data in payloads.items():
        assert saved.read(name) == data

author_root = BASE / 'reviews/fixture-author'
preserved = author_root / 'candidate002'
preserved.mkdir(exist_ok=False)
author_files = []
for name in ('ATTEMPTS.json', 'REPORT.md', 'STATIC-CHECKS.json', 'build_fixtures.py', 'freeze_static.py'):
    data = read_ordinary(author_root / name)
    destination = preserved / name
    with destination.open('xb') as stream:
        stream.write(data)
    assert read_ordinary(destination) == data
    author_files.append({'path': str(destination.relative_to(BASE)), 'bytes': len(data), 'sha256': digest(data)})

record = {
    'schema': 'ontokin.c271.p29-fixture-candidate-preservation/1',
    'candidate': '002',
    'archive': archive.name,
    'bytes': archive.stat().st_size,
    'sha256': digest(read_ordinary(archive)),
    'freeze_sha256': EXPECTED_FREEZE,
    'adapter_sha256': freeze['adapter']['sha256'],
    'files': len(payloads),
    'bound_payloads': len(freeze['files']),
    'bound_companions': len(companions),
    'verified': True,
    'status': 'accepted_then_inventory_defect_observed_before_inherited_test_execution',
    'finding': 'baseline-inherited discovered 481 inherited methods against frozen 372; comparison failed before runner invocation. Production remained unchanged. All 116 adopted expectations remain unchanged.',
    'baseline_evidence': 'verification/baseline-inherited/',
    'author_files': author_files,
    'preservation_product_execution': 0,
}
record_path = archive.with_name('CANDIDATE002-ARCHIVE.json')
with record_path.open('x') as stream:
    stream.write(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2))
