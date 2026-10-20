"""Archive explicit immutable execution files, preserving bytes and failures."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path('/workspace/scratch/0229a0b41cd2/OntoKin')
sys.path.insert(0, str(ROOT))
from tools.build_force_release_evidence import copy_inventory

plan_path, archive_path, manifest_path = map(Path, sys.argv[1:4])
assert not archive_path.exists() and not manifest_path.exists(), 'Preserve earlier archives.'
plan = json.loads(plan_path.read_text())
records, excluded = copy_inventory(plan['copies'], archive_path)
with zipfile.ZipFile(archive_path, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for source, item in records:
        raw = source.read_bytes()
        assert len(raw) == item['byte_length']
        assert 'sha256:' + hashlib.sha256(raw).hexdigest() == item['sha256']
        info = zipfile.ZipInfo(item['path'], date_time=(2026, 10, 20, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        archive.writestr(info, raw, compresslevel=9)
with zipfile.ZipFile(archive_path) as archive:
    assert archive.testzip() is None
    assert archive.namelist() == [item['path'] for _, item in records]
    for _, item in records:
        raw = archive.read(item['path'])
        assert len(raw) == item['byte_length']
        assert 'sha256:' + hashlib.sha256(raw).hexdigest() == item['sha256']
raw_archive = archive_path.read_bytes()
manifest = {
    'schema_version': 'ontokin.retained-execution-archive/0.1',
    'generated_at_utc': datetime.now(timezone.utc).isoformat(),
    'purpose': plan['purpose'],
    'release_certified': False,
    'archive': {'path': archive_path.name, 'sha256': 'sha256:' + hashlib.sha256(raw_archive).hexdigest(),
                'byte_length': len(raw_archive)},
    'archive_member_bytes_verified': True,
    'members': [item for _, item in records],
    'excluded_mutable_inputs': excluded,
    'source_plan': plan,
}
with manifest_path.open('x') as stream:
    stream.write(json.dumps(manifest, indent=2) + '\n')
print(json.dumps({'archive': str(archive_path), 'manifest': str(manifest_path),
                  'files': len(records), 'uncompressed_bytes': sum(r['byte_length'] for _, r in records),
                  'archive_identity': manifest['archive'], 'excluded': len(excluded)}))
