"""Shared helpers of HOST review 001 (gate MH, C271-P35). Loaded by path by the h0N scripts.

Independent code: it imports nothing of the project and copies no project function. It reads
files, never follows a link it is not asked to resolve, starts no process (an audit hook refuses
every process-creation event and the ctypes lookups of libc's process-creation functions), and
writes only absent output files with O_EXCL. It holds no machine path.
"""
import hashlib
import json
import os
import posixpath
import stat
import struct
import sys

PROCESS_EVENTS = frozenset(("subprocess.Popen", "os.posix_spawn", "os.exec", "os.fork", "os.forkpty",
                            "os.spawn", "os.system", "os.startfile", "pty.spawn"))
LIBC_PROCESS_NAMES = frozenset(("fork", "vfork", "execve", "execv", "execvp", "execvpe", "execl", "execlp",
                                "execle", "posix_spawn", "posix_spawnp", "system", "popen"))
REFUSED_EVENTS = []


def _hook(event, args):
    if event in PROCESS_EVENTS:
        REFUSED_EVENTS.append(event)
        raise RuntimeError("HOST review: process creation refused (" + event + ")")
    if event == "ctypes.dlsym" and len(args) >= 2:
        name = args[1]
        if isinstance(name, bytes):
            name = name.decode("ascii", "replace")
        if isinstance(name, str) and name in LIBC_PROCESS_NAMES:
            REFUSED_EVENTS.append(event + ":" + name)
            raise RuntimeError("HOST review: lookup of a process-creation function refused (" + name + ")")


sys.addaudithook(_hook)


def process_facts():
    return {"pid": os.getpid(), "ppid": os.getppid(), "executable": sys.executable,
            "flags": {"isolated": sys.flags.isolated, "no_site": sys.flags.no_site,
                      "dont_write_bytecode": sys.flags.dont_write_bytecode,
                      "ignore_environment": sys.flags.ignore_environment, "safe_path": sys.flags.safe_path}}


def mode_text(st_mode):
    return "0o%03o" % stat.S_IMODE(st_mode)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      allow_nan=False).encode("ascii")


def sha256_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def birth_ns(info):
    """Float-derived birth time (about 0.24 us resolution at this epoch); see birth_exact_ns for the exact value."""
    value = getattr(info, "st_birthtime_ns", None)
    if value is None and hasattr(info, "st_birthtime"):
        value = int(info.st_birthtime * 1e9)
    return value


def birth_exact_ns(path):
    """The exact creation time through getattrlist(ATTR_CMN_CRTIME), without following a final link."""
    import ctypes

    class AttrList(ctypes.Structure):
        _fields_ = [("bitmapcount", ctypes.c_ushort), ("reserved", ctypes.c_uint16),
                    ("commonattr", ctypes.c_uint32), ("volattr", ctypes.c_uint32), ("dirattr", ctypes.c_uint32),
                    ("fileattr", ctypes.c_uint32), ("forkattr", ctypes.c_uint32)]
    lib = ctypes.CDLL("/usr/lib/libSystem.B.dylib", use_errno=True)
    fn = lib.getattrlist
    fn.argtypes = [ctypes.c_char_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint32]
    fn.restype = ctypes.c_int
    request = AttrList(5, 0, 0x00000200, 0, 0, 0, 0)  # ATTR_BIT_MAP_COUNT, ATTR_CMN_CRTIME
    buffer = ctypes.create_string_buffer(64)
    if fn(os.fsencode(path), ctypes.byref(request), buffer, 64, 0x00000001) != 0:  # FSOPT_NOFOLLOW
        raise OSError(ctypes.get_errno(), "getattrlist " + path)
    length, seconds, nanoseconds = struct.unpack_from("<Iqq", buffer.raw, 0)
    if length < 20:
        raise ValueError("short getattrlist reply")
    return seconds * 10 ** 9 + nanoseconds


def read_bound(path, *, keep=False, prefix=0):
    """Hash one regular file through one descriptor, refusing a link; returns (bytes|None, facts, head)."""
    named = os.lstat(path)
    if stat.S_ISLNK(named.st_mode):
        raise ValueError("bound file is a symbolic link: " + path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0))
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError("not a regular file: " + path)
        digest, chunks, head, length = hashlib.sha256(), [], b"", 0
        while True:
            block = os.read(fd, 4 * 1024 * 1024)
            if not block:
                break
            length += len(block)
            digest.update(block)
            if keep:
                chunks.append(block)
            if len(head) < prefix:
                head += block[:prefix - len(head)]
        after = os.fstat(fd)
    finally:
        os.close(fd)
    again = os.lstat(path)
    ident = lambda i: (i.st_dev, i.st_ino, i.st_size, i.st_mtime_ns, i.st_ctime_ns, i.st_nlink, i.st_mode)
    if not (ident(before) == ident(after) == ident(again)) or length != before.st_size:
        raise ValueError("file changed while being read: " + path)
    facts = {"sha256": digest.hexdigest(), "size_bytes": length, "mode": mode_text(before.st_mode),
             "nlink": before.st_nlink, "mtime_ns": before.st_mtime_ns, "ctime_ns": before.st_ctime_ns,
             "birth_ns": birth_ns(before), "dev": before.st_dev, "ino": before.st_ino}
    return (b"".join(chunks) if keep else None), facts, head


def binding(facts):
    return {"sha256": facts["sha256"], "size_bytes": facts["size_bytes"], "mode": facts["mode"]}


def descriptor(path):
    _, facts, _ = read_bound(path)
    return {"path": path, **binding(facts)}


def load_json(path):
    raw, facts, _ = read_bound(path, keep=True)
    return json.loads(raw.decode("utf-8")), raw, facts


def write_new(path, value, *, pretty=True):
    raw = (json.dumps(value, sort_keys=True, indent=1, ensure_ascii=True, allow_nan=False) + "\n").encode("ascii") \
        if pretty else canonical(value)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
    try:
        offset = 0
        while offset < len(raw):
            offset += os.write(fd, raw[offset:])
        os.fsync(fd)
    finally:
        os.close(fd)
    return {"path": path, "sha256": sha256_bytes(raw), "size_bytes": len(raw)}


def resolve_chain(path, limit=40):
    """Resolve an absolute path one component at a time, as the kernel does; record each link."""
    if not path.startswith("/"):
        raise ValueError("relative path: " + path)
    pending = [name for name in path.split("/") if name]
    resolved, hops = "/", []
    while pending:
        name = pending.pop(0)
        if name == ".":
            continue
        if name == "..":
            resolved = posixpath.dirname(resolved)
            continue
        candidate = posixpath.join(resolved, name)
        try:
            info = os.lstat(candidate)
        except FileNotFoundError:
            return {"state": "absent", "path": candidate, "hops": hops}
        if stat.S_ISLNK(info.st_mode):
            if len(hops) >= limit:
                raise ValueError("link chain too long: " + path)
            target = os.readlink(candidate)
            hops.append({"path": candidate, "target": target})
            if target.startswith("/"):
                resolved = "/"
            pending = [part for part in target.split("/") if part] + pending
            continue
        if pending and not stat.S_ISDIR(info.st_mode):
            return {"state": "absent", "path": candidate + "/" + "/".join(pending), "hops": hops}
        resolved = candidate
    info = os.lstat(resolved)
    state = "file" if stat.S_ISREG(info.st_mode) else "directory" if stat.S_ISDIR(info.st_mode) else "other"
    return {"state": state, "path": resolved, "hops": hops}


def linked_components(path):
    """Every component of ``path`` that is a symbolic link (lstat, no resolution)."""
    found, current = [], ""
    for name in [part for part in path.split("/") if part]:
        current += "/" + name
        try:
            if stat.S_ISLNK(os.lstat(current).st_mode):
                found.append(current)
        except FileNotFoundError:
            break
    return found


# --- Mach-O (from <mach-o/loader.h>, written for this review) -------------------------------------

REQ = 0x80000000
LC_NAME = {
    0x1: "LC_SEGMENT", 0x2: "LC_SYMTAB", 0x3: "LC_SYMSEG", 0x4: "LC_THREAD", 0x5: "LC_UNIXTHREAD",
    0x6: "LC_LOADFVMLIB", 0x7: "LC_IDFVMLIB", 0x8: "LC_IDENT", 0x9: "LC_FVMFILE", 0xA: "LC_PREPAGE",
    0xB: "LC_DYSYMTAB", 0xC: "LC_LOAD_DYLIB", 0xD: "LC_ID_DYLIB", 0xE: "LC_LOAD_DYLINKER", 0xF: "LC_ID_DYLINKER",
    0x10: "LC_PREBOUND_DYLIB", 0x11: "LC_ROUTINES", 0x12: "LC_SUB_FRAMEWORK", 0x13: "LC_SUB_UMBRELLA",
    0x14: "LC_SUB_CLIENT", 0x15: "LC_SUB_LIBRARY", 0x16: "LC_TWOLEVEL_HINTS", 0x17: "LC_PREBIND_CKSUM",
    0x18 | REQ: "LC_LOAD_WEAK_DYLIB", 0x19: "LC_SEGMENT_64", 0x1A: "LC_ROUTINES_64", 0x1B: "LC_UUID",
    0x1C | REQ: "LC_RPATH", 0x1D: "LC_CODE_SIGNATURE", 0x1E: "LC_SEGMENT_SPLIT_INFO", 0x1F | REQ: "LC_REEXPORT_DYLIB",
    0x20: "LC_LAZY_LOAD_DYLIB", 0x21: "LC_ENCRYPTION_INFO", 0x22: "LC_DYLD_INFO", 0x22 | REQ: "LC_DYLD_INFO_ONLY",
    0x23 | REQ: "LC_LOAD_UPWARD_DYLIB", 0x24: "LC_VERSION_MIN_MACOSX", 0x25: "LC_VERSION_MIN_IPHONEOS",
    0x26: "LC_FUNCTION_STARTS", 0x27: "LC_DYLD_ENVIRONMENT", 0x28 | REQ: "LC_MAIN", 0x29: "LC_DATA_IN_CODE",
    0x2A: "LC_SOURCE_VERSION", 0x2B: "LC_DYLIB_CODE_SIGN_DRS", 0x2C: "LC_ENCRYPTION_INFO_64",
    0x2D: "LC_LINKER_OPTION", 0x2E: "LC_LINKER_OPTIMIZATION_HINT", 0x2F: "LC_VERSION_MIN_TVOS",
    0x30: "LC_VERSION_MIN_WATCHOS", 0x31: "LC_NOTE", 0x32: "LC_BUILD_VERSION", 0x33 | REQ: "LC_DYLD_EXPORTS_TRIE",
    0x34 | REQ: "LC_DYLD_CHAINED_FIXUPS", 0x35 | REQ: "LC_FILESET_ENTRY", 0x36: "LC_ATOM_INFO"}
FILETYPE = {1: "MH_OBJECT", 2: "MH_EXECUTE", 3: "MH_FVMLIB", 4: "MH_CORE", 5: "MH_PRELOAD", 6: "MH_DYLIB",
            7: "MH_DYLINKER", 8: "MH_BUNDLE", 9: "MH_DYLIB_STUB", 10: "MH_DSYM", 11: "MH_KEXT_BUNDLE",
            12: "MH_FILESET"}
DYLIB_KINDS = ("LC_LOAD_DYLIB", "LC_LOAD_WEAK_DYLIB", "LC_ID_DYLIB", "LC_REEXPORT_DYLIB",
               "LC_LOAD_UPWARD_DYLIB", "LC_LAZY_LOAD_DYLIB")
LINKEDIT_KINDS = ("LC_CODE_SIGNATURE", "LC_SEGMENT_SPLIT_INFO", "LC_FUNCTION_STARTS", "LC_DATA_IN_CODE",
                  "LC_DYLIB_CODE_SIGN_DRS", "LC_LINKER_OPTIMIZATION_HINT", "LC_DYLD_EXPORTS_TRIE",
                  "LC_DYLD_CHAINED_FIXUPS", "LC_ATOM_INFO")


def magic_kind(head):
    magic = head[:4]
    if magic in (b"\xca\xfe\xba\xbe", b"\xbe\xba\xfe\xca", b"\xca\xfe\xba\xbf", b"\xbf\xba\xfe\xca"):
        return "fat"
    if magic == b"\xcf\xfa\xed\xfe":
        return "macho64"
    if magic in (b"\xce\xfa\xed\xfe", b"\xfe\xed\xfa\xce"):
        return "macho32"
    if magic == b"\xfe\xed\xfa\xcf":
        return "macho64-be"
    return None


def _ver3(value):
    return "%d.%d.%d" % (value >> 16, (value >> 8) & 0xFF, value & 0xFF)


def _cstring(body, offset_field):
    offset = struct.unpack_from("<I", body, offset_field)[0]
    end = body.find(b"\0", offset)
    if not (offset < len(body)) or end < 0:
        raise ValueError("load command string escapes its command")
    return body[offset:end].decode("ascii")


def parse_thin(data, file_size):
    """Header and every load command of a thin 64-bit little-endian image; returns (summary, problems)."""
    problems = []
    magic, cputype, cpusubtype, filetype, ncmds, sizeofcmds, flags, _ = struct.unpack_from("<8I", data, 0)
    if magic != 0xFEEDFACF:
        raise ValueError("not MH_MAGIC_64")
    commands, offset, end = [], 32, 32 + sizeofcmds
    if end > len(data):
        raise ValueError("load commands not supplied")
    for index in range(ncmds):
        cmd, cmdsize = struct.unpack_from("<II", data, offset)
        if cmdsize < 8 or cmdsize % 8 or offset + cmdsize > end:
            raise ValueError("bad cmdsize at command %d" % index)
        body = data[offset:offset + cmdsize]
        name = LC_NAME.get(cmd)
        row = {"cmd": "0x%08x" % cmd, "name": name, "cmdsize": cmdsize}
        if name == "LC_SEGMENT_64":
            segname = body[8:24].split(b"\0", 1)[0].decode("ascii")
            vmaddr, vmsize, fileoff, filesize, maxprot, initprot, nsects, _flags = struct.unpack_from("<QQQQiiII",
                                                                                                    body, 24)
            if cmdsize != 72 + 80 * nsects:
                problems.append("segment %s size disagrees with its sections" % segname)
            if fileoff + filesize > file_size:
                problems.append("segment %s escapes the file" % segname)
            row.update(segname=segname, vmaddr=vmaddr, vmsize=vmsize, fileoff=fileoff, filesize=filesize,
                       maxprot=maxprot, initprot=initprot, nsects=nsects)
        elif name == "LC_SYMTAB":
            symoff, nsyms, stroff, strsize = struct.unpack_from("<IIII", body, 8)
            if symoff + 16 * nsyms > file_size or stroff + strsize > file_size:
                problems.append("symbol or string table escapes the file")
            row.update(nsyms=nsyms, strsize=strsize)
        elif name in ("LC_LOAD_DYLINKER", "LC_ID_DYLINKER", "LC_DYLD_ENVIRONMENT", "LC_RPATH"):
            row["path"] = _cstring(body, 8)
        elif name in DYLIB_KINDS:
            row["path"] = _cstring(body, 8)
            _ts, current, compatibility = struct.unpack_from("<III", body, 12)
            row.update(current_version=_ver3(current), compatibility_version=_ver3(compatibility))
        elif name == "LC_UUID":
            text = body[8:24].hex().upper()
            row["uuid"] = "-".join((text[:8], text[8:12], text[12:16], text[16:20], text[20:]))
        elif name == "LC_BUILD_VERSION":
            platform, minos, sdk, ntools = struct.unpack_from("<IIII", body, 8)
            row.update(platform=platform, minos=_ver3(minos), sdk=_ver3(sdk),
                       tools=[{"tool": t, "version": _ver3(v)} for t, v in struct.iter_unpack("<II", body[24:24 + 8 * ntools])])
        elif name == "LC_SOURCE_VERSION":
            value = struct.unpack_from("<Q", body, 8)[0]
            row["version"] = ".".join(str(p) for p in (value >> 40, (value >> 30) & 0x3FF, (value >> 20) & 0x3FF,
                                                        (value >> 10) & 0x3FF, value & 0x3FF))
        elif name == "LC_MAIN":
            entryoff, stacksize = struct.unpack_from("<QQ", body, 8)
            row.update(entryoff=entryoff, stacksize=stacksize)
        elif name in LINKEDIT_KINDS:
            dataoff, datasize = struct.unpack_from("<II", body, 8)
            if dataoff + datasize > file_size:
                problems.append(name + " data escapes the file")
            row.update(dataoff=dataoff, datasize=datasize)
        commands.append(row)
        offset += cmdsize
    if offset != end:
        problems.append("command sizes do not add up to sizeofcmds")
    summary = {"magic": "MH_MAGIC_64", "cputype": "0x%08x" % cputype, "cpusubtype": "0x%08x" % cpusubtype,
               "filetype": FILETYPE.get(filetype, "0x%08x" % filetype), "flags": "0x%08x" % flags,
               "ncmds": ncmds, "sizeofcmds": sizeofcmds, "commands": commands}
    return summary, problems


def read_thin_macho(path):
    """Hash a file and parse its thin Mach-O header and load commands from the same bytes."""
    _, facts, head = read_bound(path, prefix=65536)
    if magic_kind(head) != "macho64":
        raise ValueError("not a thin 64-bit little-endian Mach-O file: " + path)
    sizeofcmds = struct.unpack_from("<I", head, 20)[0]
    if 32 + sizeofcmds > len(head):
        _, again, head = read_bound(path, prefix=32 + sizeofcmds)
        if binding(again) != binding(facts):
            raise ValueError("file changed while parsed: " + path)
    summary, problems = parse_thin(head, facts["size_bytes"])
    return facts, summary, problems
