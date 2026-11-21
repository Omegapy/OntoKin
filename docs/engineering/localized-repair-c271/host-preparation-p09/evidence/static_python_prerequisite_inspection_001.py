"""Read only the existing selected Python image; never import project code."""
import hashlib
import json
import os
from pathlib import Path
import stat
import struct
import sys
from datetime import datetime, timezone

OUT = Path('/workspace/scratch/e33f906d0e8e/h0_work')
SELECTED = Path('/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3')
source = SELECTED.resolve(strict=True)
assert Path(sys.executable).resolve(strict=True) == source
with source.open('rb') as stream:
    before = os.fstat(stream.fileno())
    raw = stream.read()
    after = os.fstat(stream.fileno())
identity = lambda st: (st.st_dev, st.st_ino, st.st_size, st.st_mode, st.st_nlink, st.st_mtime_ns, st.st_ctime_ns)
assert identity(before) == identity(after) == identity(source.stat())
assert stat.S_ISREG(before.st_mode)
assert raw[:7] == b'\x7fELF\x02\x01\x01'
phoff = struct.unpack_from('<Q', raw, 32)[0]
phentsize, phnum = struct.unpack_from('<HH', raw, 54)
assert phentsize == 56 and 0 < phnum <= 256
segments, dynamic, interpreter = [], [], None
for n in range(phnum):
    kind, flags, offset, virtual, physical, filesz, memsz, align = struct.unpack_from('<IIQQQQQQ', raw, phoff + n*phentsize)
    assert offset + filesz <= len(raw)
    if kind == 1:
        segments.append((virtual, offset, filesz))
    elif kind == 2:
        dynamic.append((offset, filesz))
    elif kind == 3:
        assert interpreter is None and raw[offset+filesz-1] == 0
        interpreter = raw[offset:offset+filesz-1].decode('ascii')
assert len(dynamic) == 1
entries = []
offset, length = dynamic[0]
for position in range(offset, offset+length, 16):
    tag, value = struct.unpack_from('<qQ', raw, position)
    if tag == 0:
        break
    entries.append((tag, value))
else:
    raise ValueError('Unterminated ELF dynamic table')
single = lambda tag: next(value for item, value in entries if item == tag)
straddr, strsize = single(5), single(10)
mapped = [offset+straddr-virtual for virtual, offset, size in segments if virtual <= straddr and straddr+strsize <= virtual+size]
assert len(set(mapped)) == 1
strings = raw[mapped[0]:mapped[0]+strsize]
def string(index):
    end = strings.index(b'\0', index)
    return strings[index:end].decode('ascii')
needed = [string(value) for tag, value in entries if tag == 1]
search = {name: [string(value) for tag, value in entries if tag == number]
          for name, number in [('rpath', 15), ('runpath', 29)]}
unsupported = [value for values in search.values() for value in values if '$' in value]
snapshot = OUT/'selected-python.bin'
with snapshot.open('xb') as stream:
    stream.write(raw)
    stream.flush()
    os.fsync(stream.fileno())
os.chmod(snapshot, 0o600)
report = {
    'schema': 'ontokin.c271.p09-python-static-prerequisite/1',
    'observed_at_utc': datetime.now(timezone.utc).isoformat(),
    'scope': 'Existing selected Python executable file and ELF dynamic strings only',
    'selected_path': str(SELECTED), 'resolved_path': str(source),
    'python_version_of_inspecting_process': '.'.join(map(str, sys.version_info[:3])),
    'descriptor': {'path': str(source), 'sha256': hashlib.sha256(raw).hexdigest(), 'size_bytes': len(raw), 'mode': oct(stat.S_IMODE(before.st_mode))},
    'identity': dict(zip(['device','inode','size_bytes','stat_mode','hardlinks','mtime_ns','ctime_ns'],identity(before))),
    'elf': {'interpreter': interpreter, 'needed': needed, **search, 'dynamic_entries': entries},
    'snapshot': {'path': str(snapshot), 'sha256': hashlib.sha256(raw).hexdigest(), 'size_bytes': len(raw), 'mode': '0o600'},
    'unsupported_loader_tokens': unsupported,
    'state': 'BLOCKED_STATIC_ELF_TOKEN' if unsupported else 'PYTHON_IMAGE_NO_TOKEN_BLOCKER_FOUND',
    'source_predicate': 'current_host_inspection_v01.py read_elf_metadata: require "$" not in each DT_RPATH/DT_RUNPATH entry; failure category CHI-UNSUPPORTED',
    'production_invocations': 0, 'candidate_imports': 0, 'node_starts': 0, 'ldd_starts': 0,
    'runtime_installations': 0, 'preparer_invocations': 0,
    'not_inspected_after_first_blocker': ['Python package metadata', 'Python transitive ELF closure', 'ldd closure', 'Git closure', 'host plan'],
    'decision': 'Stop H0 substantive work at first concrete unsupported ELF token; no alternative Python selection or repair' if unsupported else 'No conclusion about full closure',
}
with (OUT/'PYTHON-STATIC-PREREQUISITE-001.json').open('x') as stream:
    json.dump(report, stream, indent=2, sort_keys=True)
    stream.write('\n')
    stream.flush()
    os.fsync(stream.fileno())
print(json.dumps({'state': report['state'], 'selected_path': str(source), 'rpath': search['rpath'], 'runpath': search['runpath'], 'report': str(OUT/'PYTHON-STATIC-PREREQUISITE-001.json')}))
