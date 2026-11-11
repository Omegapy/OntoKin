"""Install the already verified dependency archive without executing native code."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import os
import shutil
import stat
import tarfile
from datetime import datetime, timezone

ARCHIVE = Path('/workspace/scratch/efc86516cbb7/deps/blender-4.5.3-linux-x64.tar.xz')
DEST = Path('/workspace/scratch/801d9d641f68/deps')
TOP = 'blender-4.5.3-linux-x64'
OUT = Path('/workspace/scratch/801d9d641f68/c199-independent-preflight')
EXPECTED = '975c58fcb244273838534bba771e64ad87739216b0f9b39a888531a49a72d845'
EXE = '5e15447670804c855fef6033ac9b8fd82696b762095becf0df79b1c2f8034397'

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024), b''):
            h.update(b)
    return h.hexdigest()

assert ARCHIVE.stat().st_size == 377397328
assert sha(ARCHIVE) == EXPECTED
free = shutil.disk_usage(DEST.parent).free
assert free > 3 * 1024**3, f'Insufficient free space: {free}'
assert not (DEST/TOP).exists(), 'Fresh target already exists; do not overwrite'
DEST.mkdir(exist_ok=True)
seen=set()
entries=[]
total=0
with tarfile.open(ARCHIVE, mode='r|xz') as tf:
    for m in tf:
        path=PurePosixPath(m.name)
        assert not path.is_absolute() and '..' not in path.parts and path.parts[0] == TOP, m.name
        assert m.name not in seen, 'Duplicate archive member: '+m.name
        seen.add(m.name)
        assert len(seen) <= 20000
        assert m.isdir() or m.isfile() or m.issym() or m.islnk(), 'Unsupported member type'
        total+=m.size
        assert total <= 2 * 1024**3, 'Unpacked byte ceiling exceeded'
        if m.issym():
            resolved = (DEST/path.parent/m.linkname).resolve()
            assert resolved.is_relative_to((DEST/TOP).resolve()), 'Symlink outside distribution'
        if m.islnk():
            target=PurePosixPath(m.linkname)
            assert not target.is_absolute() and '..' not in target.parts and target.parts[0] == TOP, 'Hardlink outside distribution'
        tf.extract(m, DEST, filter='data')
        local=DEST/path
        row={'path':m.name,'archive_bytes':m.size,'archive_mode':oct(m.mode),'type':'file' if m.isfile() else 'directory' if m.isdir() else 'symlink' if m.issym() else 'hardlink'}
        if m.isfile():
            assert local.stat().st_size == m.size
            row.update(bytes=local.stat().st_size,sha256=sha(local),mode=oct(stat.S_IMODE(local.stat().st_mode)))
        elif m.issym() or m.islnk():
            row['linkname']=m.linkname
        entries.append(row)

assert sha(DEST/TOP/'blender') == EXE
output={'schema':'ontokin.c199.exact-dependency-install/0.1','status':'PASS','observed_at_utc':datetime.now(timezone.utc).isoformat(),'archive_path':str(ARCHIVE),'archive_bytes':ARCHIVE.stat().st_size,'archive_sha256':EXPECTED,'destination':str(DEST/TOP),'free_bytes_before':free,'free_bytes_after':shutil.disk_usage(DEST).free,'members':len(entries),'regular_files':sum(x['type']=='file' for x in entries),'expanded_regular_bytes':total,'executable_sha256':EXE,'native_processes_started':0,'extraction_policy':'Verified exact archive; new empty target; one fixed root; no traversal, devices, FIFOs or outward links; Python tarfile data filter; <=20000 members and <=2 GiB regular content','inventory':'CLEAN-DISTRIBUTION-INVENTORY.json'}
(OUT/'CLEAN-DISTRIBUTION-INVENTORY.json').write_text(json.dumps(entries,indent=2,sort_keys=True)+'\n')
(OUT/'CLEAN-DEPENDENCY-INSTALL.json').write_text(json.dumps(output,indent=2,sort_keys=True)+'\n')
for role,prefix in [('GLTF','4.5/scripts/addons_core/io_scene_gltf2/'),('PYTHON','4.5/python/')]:
    selected=[x for x in entries if x['path'].startswith(TOP+'/'+prefix) and x['type'] != 'directory']
    (OUT/('CLEAN-'+role+'-INVENTORY.json')).write_text(json.dumps(selected,indent=2,sort_keys=True)+'\n')
print(json.dumps(output,indent=2))
