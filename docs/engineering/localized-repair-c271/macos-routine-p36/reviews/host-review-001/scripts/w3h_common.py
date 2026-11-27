"""Shared helpers for HOST review 001 of C271-P36 (gate MR, stage S5).

Standard library only; nothing of the project is imported or executed. Every script
installs the audit hook below first: it refuses every process-creation event and every
ctypes lookup of a process-creation function, and admits os.kill/os.killpg only with
signal 0 (an existence probe that delivers no signal). Paths are arguments; outputs carry
labels instead of machine paths. Outputs are written to absent paths only (O_EXCL).
"""
import hashlib
import json
import os
import posixpath
import stat
import struct
import sys

BLOCKED_EVENTS = {
    "subprocess.Popen", "os.system", "os.exec", "os.posix_spawn", "os.spawn", "os.fork",
    "os.forkpty", "pty.spawn", "os.startfile", "os.popen",
}
BLOCKED_SYMBOLS = {
    b"fork", b"vfork", b"execve", b"execv", b"execvp", b"execvP", b"execl", b"execlp", b"execle",
    b"posix_spawn", b"posix_spawnp", b"system", b"popen", b"forkpty", b"__fork",
}
EVENTS = {"blocked": [], "kill_probes": 0, "dlopen": [], "dlsym": []}


def _hook(event, args):
    if event in BLOCKED_EVENTS:
        EVENTS["blocked"].append(event)
        raise RuntimeError("process creation refused by the reviewer's audit hook: " + event)
    if event in ("os.kill", "os.killpg"):
        signal_number = args[1] if len(args) > 1 else None
        if signal_number != 0:
            EVENTS["blocked"].append(event)
            raise RuntimeError("only signal 0 probes are admitted: " + event)
        EVENTS["kill_probes"] += 1
    if event == "ctypes.dlsym":
        name = args[1] if len(args) > 1 else None
        if isinstance(name, str):
            name = name.encode("ascii", "replace")
        if isinstance(name, bytes) and name in BLOCKED_SYMBOLS:
            EVENTS["blocked"].append(event + ":" + name.decode("ascii", "replace"))
            raise RuntimeError("ctypes lookup of a process-creation function refused")
        if isinstance(name, bytes):
            EVENTS["dlsym"].append(name.decode("ascii", "replace"))
    if event == "ctypes.dlopen":
        EVENTS["dlopen"].append(str(args[0]) if args else None)


def install_hook():
    sys.addaudithook(_hook)


def process_identity():
    return {"pid": os.getpid(), "ppid": os.getppid(),
            "flags": {"isolated": sys.flags.isolated, "no_site": sys.flags.no_site,
                      "dont_write_bytecode": sys.flags.dont_write_bytecode,
                      "ignore_environment": sys.flags.ignore_environment},
            "version": "%d.%d.%d" % sys.version_info[:3]}


# ---------------------------------------------------------------------------
# Canonical JSON and strict decoding
# ---------------------------------------------------------------------------

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      allow_nan=False).encode("ascii")


class DuplicateKey(ValueError):
    pass


def strict_loads(raw):
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise DuplicateKey(key)
            out[key] = value
        return out

    def constant(text):
        raise ValueError("nonfinite constant " + text)
    return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=constant)


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def mode_text(st_mode):
    return "0o%03o" % stat.S_IMODE(st_mode)


# ---------------------------------------------------------------------------
# Bounded reads through one descriptor, never following a link
# ---------------------------------------------------------------------------

def read_bytes(path, keep=True, prefix=0):
    """Hash one regular file through one descriptor; returns (raw or None, facts, head)."""
    named = os.lstat(path)
    if stat.S_ISLNK(named.st_mode):
        raise ValueError("symbolic link: " + path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError("not a regular file: " + path)
        digest, chunks, head, length = hashlib.sha256(), [], b"", 0
        while True:
            block = os.read(fd, 1 << 20)
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
    ident = lambda s: (s.st_dev, s.st_ino, s.st_mode, s.st_nlink, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    if not (ident(before) == ident(after) == ident(again)) or length != before.st_size:
        raise ValueError("file changed while read: " + path)
    facts = {"sha256": digest.hexdigest(), "size_bytes": length, "mode": mode_text(before.st_mode),
             "nlink": before.st_nlink, "dev": before.st_dev, "ino": before.st_ino,
             "mtime_ns": before.st_mtime_ns, "birthtime": getattr(before, "st_birthtime", None)}
    return (b"".join(chunks) if keep else None), facts, head


def binding(facts):
    return {"sha256": facts["sha256"], "size_bytes": facts["size_bytes"], "mode": facts["mode"]}


def descriptor(path, facts):
    return {"path": path, **binding(facts)}


# ---------------------------------------------------------------------------
# Link resolution, component by component, as the kernel does it
# ---------------------------------------------------------------------------

def resolve_chain(path, limit=40):
    """{state, path, hops}: state file, directory, other or absent; every link followed is a hop."""
    if not (isinstance(path, str) and path.startswith("/") and "\0" not in path):
        raise ValueError("absolute path expected")
    todo = [part for part in path.split("/") if part]
    here, hops = "/", []
    while todo:
        part = todo.pop(0)
        if part == ".":
            continue
        if part == "..":
            here = posixpath.dirname(here)
            continue
        nxt = posixpath.join(here, part)
        try:
            info = os.lstat(nxt)
        except FileNotFoundError:
            return {"state": "absent", "path": nxt, "hops": hops}
        if stat.S_ISLNK(info.st_mode):
            if len(hops) >= limit:
                raise ValueError("link chain too long: " + path)
            target = os.readlink(nxt)
            hops.append({"path": nxt, "target": target})
            if target.startswith("/"):
                here = "/"
            todo = [p for p in target.split("/") if p] + todo
            continue
        if todo and not stat.S_ISDIR(info.st_mode):
            return {"state": "absent", "path": nxt + "/" + "/".join(todo), "hops": hops}
        here = nxt
    info = os.lstat(here)
    if stat.S_ISREG(info.st_mode):
        state = "file"
    elif stat.S_ISDIR(info.st_mode):
        state = "directory"
    else:
        state = "other"
    return {"state": state, "path": here, "hops": hops}


def has_linked_component(path):
    """The first linked component of an absolute path, or None (the path itself included)."""
    current = ""
    for part in [p for p in path.split("/") if p]:
        current += "/" + part
        try:
            if stat.S_ISLNK(os.lstat(current).st_mode):
                return current
        except FileNotFoundError:
            return None
    return None


# ---------------------------------------------------------------------------
# Mach-O (thin 64-bit little-endian, and the fat header of a universal file)
# ---------------------------------------------------------------------------

REQ = 0x80000000
LC_NAMES = {
    0x1: "LC_SEGMENT", 0x2: "LC_SYMTAB", 0x3: "LC_SYMSEG", 0x4: "LC_THREAD", 0x5: "LC_UNIXTHREAD",
    0xB: "LC_DYSYMTAB", 0xC: "LC_LOAD_DYLIB", 0xD: "LC_ID_DYLIB", 0xE: "LC_LOAD_DYLINKER",
    0xF: "LC_ID_DYLINKER", 0x18 | REQ: "LC_LOAD_WEAK_DYLIB", 0x19: "LC_SEGMENT_64", 0x1B: "LC_UUID",
    0x1C | REQ: "LC_RPATH", 0x1D: "LC_CODE_SIGNATURE", 0x1E: "LC_SEGMENT_SPLIT_INFO",
    0x1F | REQ: "LC_REEXPORT_DYLIB", 0x20: "LC_LAZY_LOAD_DYLIB", 0x21: "LC_ENCRYPTION_INFO",
    0x22: "LC_DYLD_INFO", 0x22 | REQ: "LC_DYLD_INFO_ONLY", 0x23 | REQ: "LC_LOAD_UPWARD_DYLIB",
    0x24: "LC_VERSION_MIN_MACOSX", 0x26: "LC_FUNCTION_STARTS", 0x27: "LC_DYLD_ENVIRONMENT",
    0x28 | REQ: "LC_MAIN", 0x29: "LC_DATA_IN_CODE", 0x2A: "LC_SOURCE_VERSION",
    0x2B: "LC_DYLIB_CODE_SIGN_DRS", 0x2C: "LC_ENCRYPTION_INFO_64", 0x2D: "LC_LINKER_OPTION",
    0x2E: "LC_LINKER_OPTIMIZATION_HINT", 0x31: "LC_NOTE", 0x32: "LC_BUILD_VERSION",
    0x33 | REQ: "LC_DYLD_EXPORTS_TRIE", 0x34 | REQ: "LC_DYLD_CHAINED_FIXUPS",
    0x35 | REQ: "LC_FILESET_ENTRY", 0x36: "LC_ATOM_INFO",
}
FILE_TYPES = {1: "MH_OBJECT", 2: "MH_EXECUTE", 6: "MH_DYLIB", 7: "MH_DYLINKER", 8: "MH_BUNDLE"}
DYLIB_KINDS = {"LC_LOAD_DYLIB", "LC_LOAD_WEAK_DYLIB", "LC_ID_DYLIB", "LC_REEXPORT_DYLIB",
               "LC_LOAD_UPWARD_DYLIB", "LC_LAZY_LOAD_DYLIB"}
LINKEDIT_KINDS = {"LC_CODE_SIGNATURE", "LC_SEGMENT_SPLIT_INFO", "LC_FUNCTION_STARTS", "LC_DATA_IN_CODE",
                  "LC_DYLIB_CODE_SIGN_DRS", "LC_LINKER_OPTIMIZATION_HINT", "LC_DYLD_EXPORTS_TRIE",
                  "LC_DYLD_CHAINED_FIXUPS", "LC_ATOM_INFO"}


def magic_kind(head):
    m = head[:4]
    if m in (b"\xca\xfe\xba\xbe", b"\xbe\xba\xfe\xca", b"\xca\xfe\xba\xbf", b"\xbf\xba\xfe\xca"):
        return "fat"
    if m == b"\xcf\xfa\xed\xfe":
        return "macho64"
    if m in (b"\xce\xfa\xed\xfe", b"\xfe\xed\xfa\xce"):
        return "macho32"
    if m == b"\xfe\xed\xfa\xcf":
        return "macho64-be"
    return None


def _dotted(value):
    return "%d.%d.%d" % (value >> 16, (value >> 8) & 0xFF, value & 0xFF)


def _cstring(body, offset_field, minimum):
    if len(body) < minimum:
        raise ValueError("short command")
    offset = struct.unpack_from("<I", body, offset_field)[0]
    if not (minimum <= offset < len(body)):
        raise ValueError("string offset escapes")
    end = body.find(b"\0", offset)
    if end <= offset:
        raise ValueError("empty or unterminated string")
    raw = body[offset:end]
    if not all(0x20 <= b <= 0x7E for b in raw):
        raise ValueError("string not printable ASCII")
    return raw.decode("ascii")


def parse_thin(data, file_size, base=0):
    """Header and every load command of a thin 64-bit little-endian Mach-O image at offset base."""
    magic, cputype, cpusubtype, filetype, ncmds, sizeofcmds, flags, _r = struct.unpack_from("<8I", data, base)
    if magic != 0xFEEDFACF:
        raise ValueError("not MH_MAGIC_64")
    end = base + 32 + sizeofcmds
    if end > len(data) or 32 + sizeofcmds > file_size:
        raise ValueError("command table escapes")
    offset, commands = base + 32, []
    for _ in range(ncmds):
        cmd, cmdsize = struct.unpack_from("<II", data, offset)
        if cmdsize < 8 or cmdsize % 8 or offset + cmdsize > end:
            raise ValueError("bad cmdsize")
        body = data[offset:offset + cmdsize]
        name = LC_NAMES.get(cmd)
        row = {"cmd": "0x%08x" % cmd, "name": name, "cmdsize": cmdsize}
        if name == "LC_SEGMENT_64":
            segname = body[8:24].split(b"\0", 1)[0].decode("ascii")
            vmaddr, vmsize, fileoff, filesize, maxprot, initprot, nsects, _f = struct.unpack_from("<QQQQiiII", body, 24)
            if cmdsize != 72 + 80 * nsects:
                raise ValueError("segment size")
            row.update(segname=segname, vmaddr=vmaddr, vmsize=vmsize, fileoff=fileoff, filesize=filesize,
                       maxprot=maxprot, initprot=initprot, nsects=nsects)
        elif name == "LC_SYMTAB":
            _so, nsyms, _st, strsize = struct.unpack_from("<IIII", body, 8)
            row.update(nsyms=nsyms, strsize=strsize)
        elif name in ("LC_LOAD_DYLINKER", "LC_ID_DYLINKER", "LC_DYLD_ENVIRONMENT", "LC_RPATH"):
            row["path"] = _cstring(body, 8, 12)
        elif name in DYLIB_KINDS:
            row["path"] = _cstring(body, 8, 24)
            _ts, current, compat = struct.unpack_from("<III", body, 12)
            row.update(current_version=_dotted(current), compatibility_version=_dotted(compat))
        elif name == "LC_UUID":
            text = body[8:24].hex().upper()
            row["uuid"] = "-".join((text[:8], text[8:12], text[12:16], text[16:20], text[20:]))
        elif name == "LC_BUILD_VERSION":
            platform, minos, sdk, ntools = struct.unpack_from("<IIII", body, 8)
            if cmdsize != 24 + 8 * ntools:
                raise ValueError("build version size")
            row.update(platform=platform, minos=_dotted(minos), sdk=_dotted(sdk),
                       tools=[{"tool": t, "version": _dotted(v)} for t, v in struct.iter_unpack("<II", body[24:])])
        elif name == "LC_SOURCE_VERSION":
            v = struct.unpack_from("<Q", body, 8)[0]
            row["version"] = ".".join(str(x) for x in (v >> 40, (v >> 30) & 0x3FF, (v >> 20) & 0x3FF,
                                                      (v >> 10) & 0x3FF, v & 0x3FF))
        elif name == "LC_MAIN":
            entryoff, stacksize = struct.unpack_from("<QQ", body, 8)
            row.update(entryoff=entryoff, stacksize=stacksize)
        elif name in LINKEDIT_KINDS:
            dataoff, datasize = struct.unpack_from("<II", body, 8)
            row.update(dataoff=dataoff, datasize=datasize)
        commands.append(row)
        offset += cmdsize
    if offset != end:
        raise ValueError("sizes do not add up")
    return {"magic": "MH_MAGIC_64", "cputype": "0x%08x" % cputype, "cpusubtype": "0x%08x" % cpusubtype,
            "filetype": FILE_TYPES.get(filetype, "0x%08x" % filetype), "flags": "0x%08x" % flags,
            "ncmds": ncmds, "sizeofcmds": sizeofcmds, "commands": commands}


def parse_fat(data):
    """The slices of a universal file (32-bit fat header, big-endian)."""
    magic, count = struct.unpack_from(">II", data, 0)
    if magic != 0xCAFEBABE:
        raise ValueError("not FAT_MAGIC")
    rows = []
    for index in range(count):
        cputype, cpusubtype, offset, size, align = struct.unpack_from(">iIIII", data, 8 + 20 * index)
        rows.append({"cputype": "0x%08x" % (cputype & 0xFFFFFFFF), "cpusubtype": "0x%08x" % cpusubtype,
                     "offset": offset, "size": size, "align": align})
    return rows


# ---------------------------------------------------------------------------
# Labels and output
# ---------------------------------------------------------------------------

class Labeler:
    """Replaces machine prefixes, given as arguments, with labels (longest prefix first)."""

    def __init__(self, pairs):
        import re
        self.pairs = [(re.compile(re.escape(p) + r"(?=/|$|[^A-Za-z0-9._@+-])"), l)
                      for p, l in sorted(((p, l) for p, l in pairs if p), key=lambda item: -len(item[0]))]

    def text(self, value):
        for pattern, label in self.pairs:
            value = pattern.sub(lambda _m, _l=label: _l, value)
        return value

    def deep(self, value):
        if isinstance(value, str):
            return self.text(value)
        if isinstance(value, list):
            return [self.deep(v) for v in value]
        if isinstance(value, dict):
            return {self.text(k): self.deep(v) for k, v in value.items()}
        return value


def write_new(path, value):
    raw = (json.dumps(value, indent=1, sort_keys=True, ensure_ascii=True) + "\n").encode("ascii")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o644)
    try:
        offset = 0
        while offset < len(raw):
            offset += os.write(fd, raw[offset:])
        os.fsync(fd)
    finally:
        os.close(fd)
    return sha256(raw)


class Checks:
    def __init__(self):
        self.rows = []

    def add(self, cid, passed, statement, **details):
        self.rows.append({"id": cid, "passed": bool(passed), "statement": statement, **details})
        return bool(passed)

    def summary(self):
        failed = [row["id"] for row in self.rows if not row["passed"]]
        return {"total": len(self.rows), "passed": len(self.rows) - len(failed), "failed": failed}


def observer_constants(source):
    """The observer's module-level constants, evaluated from its AST (never imported or executed)."""
    import ast
    tree = ast.parse(source)
    env = {}

    def ev(node):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            if node.id in env:
                return env[node.id]
            raise KeyError(node.id)
        if isinstance(node, ast.Tuple):
            return tuple(ev(e) for e in node.elts)
        if isinstance(node, ast.List):
            return [ev(e) for e in node.elts]
        if isinstance(node, ast.Dict):
            out = {}
            for k, v in zip(node.keys, node.values):
                if k is None:
                    out.update(ev(v))
                else:
                    out[ev(k)] = ev(v)
            return out
        if isinstance(node, ast.BinOp):
            left, right = ev(node.left), ev(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.BitOr):
                return left | right
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "MappingProxyType":
            return dict(ev(node.args[0]))
        raise ValueError("not a constant")
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            try:
                env[node.targets[0].id] = ev(node.value)
            except Exception:
                pass
    return env


def json_pointer_leaves(value, prefix=""):
    """Every leaf of a JSON value as (pointer, value); empty containers are leaves too."""
    out = []
    if isinstance(value, dict) and value:
        for key in sorted(value):
            out.extend(json_pointer_leaves(value[key], prefix + "/" + key.replace("~", "~0").replace("/", "~1")))
    elif isinstance(value, list) and value:
        for index, item in enumerate(value):
            out.extend(json_pointer_leaves(item, prefix + "/" + str(index)))
    else:
        out.append((prefix, value))
    return out
