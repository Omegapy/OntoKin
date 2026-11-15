#!/usr/bin/env python3
"""Record C241 static prerequisites without executing the candidate or a child."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import glob
import hashlib
import json
import mmap
import os
from pathlib import Path
import platform
import shutil
import stat
import struct


CANDIDATE = Path('/opt/godot/4.6.3/Godot_v4.6.3-stable_linux.x86_64')
EXPECTED_SHA256 = 'f64d4ed19fc9df9440321653fcc80df8c6e365ba7b6de0a29e2cfa9fa71bfeb3'
EXPECTED_BYTES = 138981968
EMBEDDED_ID = '7d41c59c457bd5a245092b4e7eb2d833e3b3f8c3'
UPSTREAM_ID = '35e80b3a8822a9df9be390814b62f44c0a9c69e8'


def identity(path: Path) -> dict:
    s = path.stat()
    return {'device': s.st_dev, 'inode': s.st_ino, 'bytes': s.st_size,
            'mode': oct(stat.S_IMODE(s.st_mode)), 'mtimeNs': s.st_mtime_ns,
            'ctimeNs': s.st_ctime_ns}


def digest(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def path_observation(path: str) -> dict:
    p = Path(path)
    value = {'path': path, 'exists': p.exists(), 'isSymlink': p.is_symlink()}
    if p.is_symlink():
        value['linkTarget'] = os.readlink(p)
    if p.exists():
        value['resolved'] = str(p.resolve(strict=True))
        value.update(identity(p))
        value['readable'] = os.access(p, os.R_OK)
        value['writable'] = os.access(p, os.W_OK)
    return value


def elf_static(path: Path) -> dict:
    with path.open('rb') as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as data:
        if data[:6] != b'\x7fELF\x02\x01':
            return {'status': 'UNSUPPORTED_STATIC_ELF_FORMAT'}
        header = struct.unpack_from('<16sHHIQQQIHHHHHH', data, 0)
        phoff, phentsize, phnum = header[5], header[9], header[10]
        if phentsize != 56 or phnum > 256 or phoff + phnum * phentsize > len(data):
            raise ValueError('Invalid or out-of-scope ELF program-header table')
        segments = [struct.unpack_from('<IIQQQQQQ', data, phoff + i * phentsize) for i in range(phnum)]
        loads = [p for p in segments if p[0] == 1]
        interp = next((bytes(data[p[2]:p[2]+p[5]]).rstrip(b'\0').decode('ascii') for p in segments if p[0] == 3), None)
        needed_offsets = []
        strtab_address = None
        for p in segments:
            if p[0] != 2:
                continue
            if p[2] + p[5] > len(data) or p[5] % 16:
                raise ValueError('Invalid ELF dynamic table')
            for off in range(p[2], p[2]+p[5], 16):
                tag, value = struct.unpack_from('<qQ', data, off)
                if tag == 0:
                    break
                if tag == 1:
                    needed_offsets.append(value)
                elif tag == 5:
                    strtab_address = value
        needed = []
        if needed_offsets:
            if strtab_address is None:
                raise ValueError('ELF dynamic strings missing')
            containing = [p for p in loads if p[3] <= strtab_address < p[3]+p[5]]
            if len(containing) != 1:
                raise ValueError('ELF dynamic strings do not have one file-backed segment')
            p = containing[0]
            strtab = p[2] + strtab_address - p[3]
            for relative in needed_offsets:
                begin = strtab + relative
                end = data.find(b'\0', begin, min(len(data), begin+4096))
                if end < begin:
                    raise ValueError('Invalid ELF dependency name')
                needed.append(bytes(data[begin:end]).decode('ascii'))
        strings = []
        for value in [EMBEDDED_ID, 'Godot Engine v4.6.3.stable.official']:
            encoded = value.encode('ascii')
            start = 0
            matches = []
            while (offset := data.find(encoded, start)) >= 0:
                matches.append(hex(offset))
                start = offset + len(encoded)
            strings.append({'text': value, 'hexOffsets': matches})
        return {'status': 'STATIC_ELF64_LITTLE_ENDIAN', 'machine': header[2],
                'elfType': header[1], 'interpreter': interp, 'neededLibraries': needed,
                'strings': strings, 'targetExecuted': False,
                'meaning': 'Headers, dependency names and embedded strings only; no dynamic loading or runtime version attestation'}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    before = identity(CANDIDATE)
    observed_sha = digest(CANDIDATE)
    elf = elf_static(CANDIDATE)
    after = identity(CANDIDATE)
    source_paths = [
        'docs/engineering/semantic-export-c210/DECISION.md',
        'docs/engineering/second-target-c220/PLAN.md',
        'docs/engineering/second-target-c220/evidence/INPUT-BINDINGS.json',
        'docs/engineering/second-target-c220/evidence/PART-MAP.json',
    ] + [f'docs/engineering/second-target-c{n}/CONTRACT.md' for n in [221,222,234,235,236,237,238,239]]
    contracts = [{'path': p, 'bytes': (args.repo_root/p).stat().st_size,
                  'sha256': digest(args.repo_root/p)} for p in source_paths]
    native_devices = [path_observation(p) for p in sorted(glob.glob('/dev/dri/*'))]
    lib_candidates = {}
    for needed in elf.get('neededLibraries', []):
        lib_candidates[needed] = [path_observation(str(Path(parent)/needed))
            for parent in ['/lib/x86_64-linux-gnu','/usr/lib/x86_64-linux-gnu','/lib64','/usr/lib64']
            if (Path(parent)/needed).exists()]
    limits = {}
    for p in ['/sys/fs/cgroup/memory.max','/sys/fs/cgroup/memory.current','/sys/fs/cgroup/pids.max']:
        try:
            limits[p] = Path(p).read_text().strip()
        except OSError as exc:
            limits[p] = {'unavailable': type(exc).__name__}
    report = {
        'schema': 'ontokin.c241.static-prerequisites/0.1',
        'observedAtUtc': datetime.now(timezone.utc).isoformat(),
        'sourceMeaning': 'Read-only observation script; no executable native admission or runtime contract implementation',
        'scriptSha256': digest(Path(__file__)),
        'host': {'system': platform.system(), 'release': platform.release(),
                 'machine': platform.machine(), 'python': platform.python_version()},
        'candidate': {'path': str(CANDIDATE), 'before': before, 'after': after,
                      'sha256': observed_sha, 'bytesMatchC220': before['bytes'] == EXPECTED_BYTES,
                      'hashMatchesC220': observed_sha == EXPECTED_SHA256,
                      'metadataUnchangedDuringRead': before == after, 'elf': elf,
                      'symlinks': [path_observation('/usr/local/bin/godot'), path_observation('/usr/local/bin/godot4')]},
        'buildLineage': {'embeddedCommitIdentifier': EMBEDDED_ID, 'pinnedUpstreamCommitIdentifier': UPSTREAM_ID,
                        'equal': EMBEDDED_ID == UPSTREAM_ID, 'status': 'UNRESOLVED',
                        'meaning': 'Retained C220 mismatch; static equality does not authenticate installed build'},
        'rendering': {'DISPLAY': os.environ.get('DISPLAY'), 'WAYLAND_DISPLAY': os.environ.get('WAYLAND_DISPLAY'),
                      'X11Sockets': sorted(glob.glob('/tmp/.X11-unix/*')),
                      'Xvfb': shutil.which('Xvfb'), 'xvfb-run': shutil.which('xvfb-run'),
                      'vulkanIcdFiles': sorted(set(glob.glob('/usr/share/vulkan/icd.d/*')+glob.glob('/etc/vulkan/icd.d/*'))),
                      'driDevices': native_devices,
                      'openGLLibraryPaths': sorted(glob.glob('/usr/lib/x86_64-linux-gnu/libGL*.so*')),
                      'status': 'NOT_ESTABLISHED', 'connectionAttempted': False, 'renderAttempted': False},
        'directLibraryCandidates': lib_candidates,
        'dynamicLibraryClosure': 'NOT_VERIFIED',
        'capacityObservation': {'cgroup': limits, 'memoryLimitEnforcement': 'NOT_IMPLEMENTED',
                               'meaning': 'Read-only counters are not an approved process budget or capacity reservation'},
        'contractBindings': contracts,
        'counts': {'childProcesses': 0, 'targetProcessStarts': 0, 'versionProbes': 0,
                   'sourceEvaluations': 0, 'exports': 0, 'imports': 0, 'renders': 0,
                   'sceneSaves': 0, 'sceneReopens': 0, 'aggregateRuns': 0},
        'executionPermission': False,
        'nativeStartReservation': 'NOT_CREATED',
    }
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'report': str(args.output), 'candidateHashMatchesC220': report['candidate']['hashMatchesC220'],
                      'targetProcessStarts': 0, 'rendering': report['rendering']['status']}))


if __name__ == '__main__':
    main()
