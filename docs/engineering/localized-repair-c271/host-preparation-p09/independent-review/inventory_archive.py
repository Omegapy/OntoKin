"""Independent complete tar-member inventory. Never extracts or executes members."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import stat
import sys
import tarfile

OUT = Path('/workspace/scratch/e33f906d0e8e/audits/h0_review')
MAX_RAW = 512 * 1024 * 1024
MAX_EXPANDED = 1024 * 1024 * 1024
MAX_MEMBERS = 32768


def digest_stream(stream, maximum):
    count, sha = 0, hashlib.sha256()
    while True:
        block = stream.read(min(1024 * 1024, maximum - count + 1))
        if not block:
            return count, sha.hexdigest()
        count += len(block)
        if count > maximum:
            raise ValueError('Stream exceeded predeclared bound')
        sha.update(block)


def identity(info):
    return [info.st_dev, info.st_ino, info.st_mode, info.st_nlink,
            info.st_size, info.st_mtime_ns, info.st_ctime_ns]


parser = argparse.ArgumentParser()
parser.add_argument('--archive', required=True)
parser.add_argument('--bytes', type=int, required=True)
parser.add_argument('--sha256', required=True)
parser.add_argument('--label', required=True, choices=['c195', 'node'])
args = parser.parse_args()
path = Path(args.archive)
if not path.is_absolute() or path.resolve() != path:
    raise ValueError('Archive must be canonical absolute regular path')
out = OUT / (args.label.upper() + '-RAW-ARCHIVE-INVENTORY.json')
if out.exists():
    raise FileExistsError('Preserve prior frozen inventory')
fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
rows, members, findings = [], {}, []
with os.fdopen(fd, 'rb') as stream:
    before = os.fstat(stream.fileno())
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size > MAX_RAW:
        raise ValueError('Archive must be bounded private regular file')
    raw_size, raw_sha = digest_stream(stream, MAX_RAW)
    if (raw_size, raw_sha) != (args.bytes, args.sha256):
        raise ValueError('Archive identity differs from independently supplied frozen expectation')
    stream.seek(0)
    with tarfile.open(fileobj=stream, mode='r:*') as archive:
        for ordinal, member in enumerate(archive):
            if ordinal >= MAX_MEMBERS:
                raise ValueError('Archive member count exceeds accepted bound')
            raw_name = member.name
            name = raw_name[:-1] if raw_name.endswith('/') else raw_name
            p = PurePosixPath(name)
            safe = bool(name) and '\\' not in name and not p.is_absolute() and str(p) == name and '..' not in p.parts and name != '.'
            kind = 'file' if member.isfile() else 'directory' if member.isdir() else 'unsupported'
            mode = oct(member.mode)
            valid_mode = member.mode in range(0o1000) and member.mode & 0o022 == 0
            if not safe or name in members or kind == 'unsupported' or member.sparse or not valid_mode:
                findings.append({'ordinal': ordinal, 'raw_name': raw_name, 'safe': safe,
                                 'duplicate': name in members, 'kind': kind, 'sparse': member.sparse,
                                 'mode': mode, 'mode_admitted_by_preparer': valid_mode})
            sha = None
            if member.isfile():
                source = archive.extractfile(member)
                if source is None:
                    raise ValueError('Cannot read regular archive member')
                with source:
                    size, sha = digest_stream(source, member.size)
                if size != member.size:
                    raise ValueError('Archive member size differs')
            elif member.size != 0:
                findings.append({'ordinal': ordinal, 'reason': 'Non-file member has nonzero size'})
            row = {'ordinal': ordinal, 'raw_name': raw_name, 'path': name, 'kind': kind,
                   'tar_type_hex': member.type.hex(), 'size_bytes': member.size, 'sha256': sha,
                   'mode': mode, 'uid': member.uid, 'gid': member.gid, 'mtime': member.mtime,
                   'linkname': member.linkname, 'sparse': member.sparse, 'pax_headers': member.pax_headers}
            rows.append(row)
            if name not in members:
                members[name] = {k: row[k] for k in ['kind', 'size_bytes', 'sha256', 'mode']}
                members[name]['target'] = None
            if sum(row['size_bytes'] for row in rows) > MAX_EXPANDED:
                raise ValueError('Archive expanded byte allowance exceeded')
    stream.seek(0)
    raw_size_after, raw_sha_after = digest_stream(stream, MAX_RAW)
    after, named = os.fstat(stream.fileno()), path.lstat()
    unchanged = identity(before) == identity(after) == identity(named) and (raw_size_after, raw_sha_after) == (raw_size, raw_sha)
    if not unchanged:
        raise ValueError('Archive identity changed while inventorying')

report = {
    'schema': 'ontokin.c271.p09-independent-raw-archive-inventory/1',
    'recorded_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'reviewer': '/root/p08_delivery_audit',
    'phase': 'C271-P09-H0-static-preparation',
    'early_save_required_and_confirmed': '2026-11-21T18:46:28.445406+00:00',
    'archive': {'path': str(path), 'size_bytes': raw_size, 'sha256': raw_sha,
                'mode': oct(stat.S_IMODE(before.st_mode)), 'identity_before': identity(before), 'unchanged_after': unchanged},
    'environment': {'python': sys.version, 'executable': sys.executable, 'platform': platform.platform()},
    'command': sys.argv,
    'all_members_including_unmapped': True,
    'counts': {'members': len(rows), 'regular_files': sum(r['kind'] == 'file' for r in rows),
               'directories': sum(r['kind'] == 'directory' for r in rows),
               'logical_bytes': sum(r['size_bytes'] for r in rows)},
    'rows': rows, 'members': members, 'findings': findings,
    'passed': not findings,
    'limits': {'raw_bytes': MAX_RAW, 'expanded_bytes': MAX_EXPANDED, 'members': MAX_MEMBERS},
    'boundary': 'Raw archive inventory only. All target mappings are deliberately null; independent plan review must accept the selected target map separately. No extraction, installation, Node/ldd, product import or product test occurred.'
}
OUT.mkdir(parents=True, exist_ok=True)
with out.open('x') as target:
    target.write(json.dumps(report, sort_keys=True, indent=2) + '\n')
print(json.dumps({'path': str(out), 'passed': report['passed'], 'counts': report['counts'],
                  'findings': findings, 'sha256': hashlib.sha256(out.read_bytes()).hexdigest()}))
