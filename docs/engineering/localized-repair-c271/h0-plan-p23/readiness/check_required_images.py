"""Read current process image identities only; never validate or execute H0."""
import hashlib
import json
import os
import stat
import sys
import time

PINS = {
    'python': {'sha256': 'fa67443527ed9647f760d807e2a38f26340757123e643c4639cf273ed15d5ea7', 'size_bytes': 30894944, 'mode': '0o755'},
    'libc': {'sha256': '9792e3cbb541c8f44c7acf5f14f4022ea62998ecc787d326bed4d8b6547dfd92', 'size_bytes': 1995216, 'mode': '0o755'},
    'loader': {'sha256': 'c8438e4fde1934e61c88311633f00949ff645d5c04cdb8671fa3d78164d2f307', 'size_bytes': 225672, 'mode': '0o755'},
}
DEADLINE = time.monotonic() + 20
result = {'schema': 'ontokin.c271.p23-pin-readiness/1', 'purpose': 'Necessary image-pin predicates only; not H0 plan validation', 'pid': os.getpid(), 'python_version': sys.version, 'observations': [], 'target_starts': {'node': 0, 'ldd': 0, 'direct_loader': 0, 'product': 0}, 'h0_plan_accepted': False, 'h0_accepted': False}

class ReadinessFailure(Exception):
    pass

def tick():
    if time.monotonic() > DEADLINE:
        raise ReadinessFailure('bounded readiness deadline exceeded')

def identity(s):
    return [s.st_dev, s.st_ino, s.st_mode, s.st_size, s.st_mtime_ns, s.st_ctime_ns]

def inspect(role, path, expected_device_inode):
    tick()
    if not path.startswith('/') or os.path.realpath(path) != path:
        raise ReadinessFailure(role + ': path is not canonical')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_size > 64 * 1024 * 1024:
            raise ReadinessFailure(role + ': unsupported file kind/size')
        if (before.st_dev, before.st_ino) != expected_device_inode:
            raise ReadinessFailure(role + ': mapped/opened file identity differs')
        h = hashlib.sha256()
        count = 0
        while True:
            tick()
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                break
            count += len(chunk)
            if count > 64 * 1024 * 1024:
                raise ReadinessFailure(role + ': file grew beyond bound')
            h.update(chunk)
        after = os.fstat(fd)
        named = os.stat(path, follow_symlinks=False)
        if identity(before) != identity(after) or identity(before) != identity(named) or count != before.st_size:
            raise ReadinessFailure(role + ': file changed during read')
        measured = {'path': path, 'sha256': h.hexdigest(), 'size_bytes': count, 'mode': oct(stat.S_IMODE(before.st_mode)), 'device': before.st_dev, 'inode': before.st_ino}
        matched = all(measured[k] == v for k, v in PINS[role].items())
        result['observations'].append({'role': role, 'expected': PINS[role], 'measured': measured, 'matched': matched, 'stable_read': True})
        if not matched:
            raise ReadinessFailure(role + ': exact adopted image pin mismatch')
    finally:
        os.close(fd)

try:
    selected = os.path.realpath(sys.executable)
    kernel_path = os.readlink('/proc/self/exe')
    kernel = os.stat('/proc/self/exe')
    result['selected_python'] = sys.executable
    result['kernel_executable'] = kernel_path
    if kernel_path.endswith(' (deleted)') or os.path.realpath(kernel_path) != selected:
        raise ReadinessFailure('current Python selection/kernel executable ambiguity')
    inspect('python', selected, (kernel.st_dev, kernel.st_ino))
    tick()
    with open('/proc/self/maps', 'rb') as stream:
        maps = stream.read(1024 * 1024 + 1)
    if len(maps) > 1024 * 1024:
        raise ReadinessFailure('current mapping input exceeds bound')
    result['mapping_input'] = {'path': '/proc/self/maps', 'size_bytes': len(maps), 'sha256': hashlib.sha256(maps).hexdigest(), 'scope': 'Current checking process; only libc and loader rows selected'}
    for role, basename in [('libc', 'libc.so.6'), ('loader', 'ld-linux-x86-64.so.2')]:
        candidates = {}
        for line in maps.decode('utf-8', 'strict').splitlines():
            fields = line.split(None, 5)
            if len(fields) != 6:
                continue
            path = fields[5]
            if os.path.basename(path.removesuffix(' (deleted)')) != basename:
                continue
            if path.endswith(' (deleted)') or not path.startswith('/'):
                raise ReadinessFailure(role + ': deleted or nonabsolute mapped image')
            major, minor = fields[3].split(':')
            device = os.makedev(int(major, 16), int(minor, 16))
            inode = int(fields[4])
            candidates[(device, inode, path)] = True
        if len(candidates) != 1:
            raise ReadinessFailure(role + ': mapped image role is absent or ambiguous')
        device, inode, path = next(iter(candidates))
        inspect(role, path, (device, inode))
    result['state'] = 'NECESSARY_IMAGE_PINS_MATCH'
    result['next_action'] = 'Continue current-host H0 prerequisites; no whole-plan acceptance follows from these three matches'
    code = 0
except (ReadinessFailure, OSError, ValueError, UnicodeError) as exc:
    result['state'] = 'BLOCKED_FIRST_PREREQUISITE'
    result['blocker'] = str(exc)
    result['next_action'] = 'Stop technical work; independently review this exact blocker and preserve a reproducible remedy'
    code = 2
result['checked_at_utc_epoch'] = time.time()
result['limits'] = ['No project or verification package imported', 'No subprocess, installation, Node, ldd or direct loader invoked', 'No ELF closure, source-completeness or operational-plan validation', 'Matching path bytes do not attest all mapped memory or the operating system']
print(json.dumps(result, indent=2))
sys.exit(code)
