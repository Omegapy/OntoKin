"""Read current ldd's literal loader list as data; never execute ldd or a loader."""
import hashlib
import json
import os
import re
import stat
import time

START = time.monotonic()
REPORT = {
    'schema': 'ontokin.c271.p23-ldd-candidate-observation/1',
    'scope': 'Current script bytes and literal RTLDLIST path facts only',
    'project_imports': [], 'subprocesses': 0,
    'target_starts': {'node': 0, 'ldd': 0, 'direct_loader': 0, 'product': 0},
    'h0_plan_accepted': False, 'h0_accepted': False,
}

def check():
    if time.monotonic() - START > 10:
        raise RuntimeError('Ten-second observation allowance exceeded')

def identity(s):
    return [s.st_dev, s.st_ino, s.st_mode, s.st_nlink, s.st_size, s.st_mtime_ns, s.st_ctime_ns]

def path_facts(path):
    check()
    try:
        a = os.lstat(path)
    except FileNotFoundError:
        a = None
    try:
        resolved_stat = os.stat(path)
    except FileNotFoundError:
        resolved_stat = None
    result = {
        'path': path, 'lexists': a is not None, 'exists': resolved_stat is not None,
        'is_directory': resolved_stat is not None and stat.S_ISDIR(resolved_stat.st_mode),
        'is_file': resolved_stat is not None and stat.S_ISREG(resolved_stat.st_mode),
        'is_symlink': a is not None and stat.S_ISLNK(a.st_mode),
        'lstat_identity': identity(a) if a is not None else None,
        'stat_identity': identity(resolved_stat) if resolved_stat is not None else None,
    }
    if result['is_symlink']:
        result['link_target'] = os.readlink(path)
    return result

try:
    path = '/usr/bin/ldd'
    check()
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size > 1024 * 1024:
            raise RuntimeError('Selected ldd script is not a private bounded regular file')
        raw = bytearray()
        while True:
            check()
            chunk = os.read(fd, min(65536, 1024 * 1024 + 1 - len(raw)))
            if not chunk:
                break
            raw.extend(chunk)
            if len(raw) > 1024 * 1024:
                raise RuntimeError('Selected ldd script exceeded the byte bound')
        after = os.fstat(fd)
        named = os.lstat(path)
        if identity(before) != identity(after) or identity(after) != identity(named) or len(raw) != before.st_size:
            raise RuntimeError('Selected ldd script changed during read')
    finally:
        os.close(fd)
    raw = bytes(raw)
    REPORT['script'] = {
        'path': path, 'sha256': hashlib.sha256(raw).hexdigest(),
        'size_bytes': len(raw), 'mode': oct(stat.S_IMODE(before.st_mode)),
        'identity': identity(before), 'stable_read': True,
        'first_line': raw.split(b'\n', 1)[0].decode('ascii'),
    }
    matches = re.findall(rb'^RTLDLIST=["\x27]([^"\x27\n]+)["\x27]$', raw, flags=re.MULTILINE)
    if len(matches) != 1:
        raise RuntimeError('Expected one exact literal RTLDLIST assignment')
    literal = matches[0].decode('ascii')
    candidates = literal.split()
    if not 0 < len(candidates) <= 16 or len(candidates) != len(set(candidates)):
        raise RuntimeError('Invalid or excessive candidate list')
    REPORT['rtldlist_literal'] = literal
    REPORT['observations'] = []
    for candidate in candidates:
        if not candidate.startswith('/') or os.path.normpath(candidate) != candidate or '\\' in candidate or '\x00' in candidate:
            raise RuntimeError('Unsupported candidate pathname')
        parent = os.path.dirname(candidate)
        first = {'candidate': path_facts(candidate), 'parent': path_facts(parent)}
        second = {'candidate': path_facts(candidate), 'parent': path_facts(parent)}
        if first != second:
            raise RuntimeError('Candidate or parent changed during observation')
        first['stable_observation'] = True
        first['absent_candidate_with_nonexistent_parent'] = (
            not first['candidate']['lexists'] and not first['parent']['exists']
        )
        REPORT['observations'].append(first)
    REPORT['state'] = 'RTLDLIST_RAW_OBSERVATION_COMPLETE'
    REPORT['limits'] = [
        'Data observation only, not executable policy validation or a host qualification',
        'No selected candidate file was opened or executed',
        'The literal list and immediate-parent facts require independent source applicability review',
    ]
    REPORT['elapsed_seconds'] = time.monotonic() - START
    print(json.dumps(REPORT, indent=2, sort_keys=True))
except Exception as error:
    REPORT['state'] = 'OBSERVATION_UNSUCCESSFUL_NO_RETRY'
    REPORT['error'] = {'type': type(error).__name__, 'message': str(error)}
    REPORT['elapsed_seconds'] = time.monotonic() - START
    print(json.dumps(REPORT, indent=2, sort_keys=True))
    raise SystemExit(2)
