#!/usr/bin/env python3
"""N34-M independent Mach-O reader (worker W1, gate MH, phase C271-P35).

Written for the N34-M review of prototypes/static_tray_v01/current_host_observation_v02.py.
It shares no code with that parser and does not import it. Standard library only.

What it does, all by static reads:
  * the Node executable: SHA-256, size, mode, link count, container (thin or fat), every fat
    slice, the header with the CPU subtype's capability bits separated, the file type and flags,
    and every load command with its decoded fields;
  * the interpreter installation: pyvenv.cfg, the bin/python link chain hop by hop, the
    framework version directory it resolves to, an exhaustive listing of both trees (no link is
    followed), every regular file classified by its leading magic, and every Mach-O file read as
    above;
  * the dependency closure of those Mach-O files, by two resolutions of @rpath: the image's own
    LC_RPATH entries only, and a dyld-like rpath stack (own entries, then those of the loading
    chain, the dlopen caller and the main executable);
  * the system references, against the on-disk file system and the image list of the OS
    cryptex's dyld shared cache (its header and image table only);
  * optional extra files (for example a Git implementation), read statically and never started;
  * an independent evaluation of the contract's Node rules (section 7) and Python rules
    (section 4).

It starts no process. It writes exactly one file, the --output path, by exclusive creation.
Every string in the output has the --label substitutions applied.

Run:  <venv>/bin/python -I -S -B n34m_reader.py --node N --venv V [--extra F ...]
          --dyld-cache C --label NAME=PATH ... --output OUT.json
"""
import argparse
import hashlib
import json
import os
import posixpath
import stat
import struct
import sys
import time

# ---------------------------------------------------------------------------
# Constants from <mach-o/loader.h>, <mach-o/fat.h> and <mach/machine.h>
# ---------------------------------------------------------------------------

MAGICS = {
    bytes.fromhex("cffaedfe"): ("MH_MAGIC_64", "macho", 64, "<"),
    bytes.fromhex("feedfacf"): ("MH_CIGAM_64", "macho", 64, ">"),
    bytes.fromhex("cefaedfe"): ("MH_MAGIC", "macho", 32, "<"),
    bytes.fromhex("feedface"): ("MH_CIGAM", "macho", 32, ">"),
    bytes.fromhex("cafebabe"): ("FAT_MAGIC", "fat", 32, ">"),
    bytes.fromhex("bebafeca"): ("FAT_CIGAM", "fat", 32, "<"),
    bytes.fromhex("cafebabf"): ("FAT_MAGIC_64", "fat", 64, ">"),
    bytes.fromhex("bfbafeca"): ("FAT_CIGAM_64", "fat", 64, "<"),
}

CPU_ARCH_ABI64 = 0x01000000
CPU_ARCH_ABI64_32 = 0x02000000
CPU_TYPES = {7: "CPU_TYPE_X86", 7 | CPU_ARCH_ABI64: "CPU_TYPE_X86_64", 12: "CPU_TYPE_ARM",
             12 | CPU_ARCH_ABI64: "CPU_TYPE_ARM64", 12 | CPU_ARCH_ABI64_32: "CPU_TYPE_ARM64_32",
             18: "CPU_TYPE_POWERPC", 18 | CPU_ARCH_ABI64: "CPU_TYPE_POWERPC64"}
CPU_SUBTYPE_MASK = 0xFF000000
ARM64_SUBTYPES = {0: "CPU_SUBTYPE_ARM64_ALL", 1: "CPU_SUBTYPE_ARM64_V8", 2: "CPU_SUBTYPE_ARM64E"}
X86_64_SUBTYPES = {3: "CPU_SUBTYPE_X86_64_ALL", 8: "CPU_SUBTYPE_X86_64_H"}

FILETYPES = {1: "MH_OBJECT", 2: "MH_EXECUTE", 3: "MH_FVMLIB", 4: "MH_CORE", 5: "MH_PRELOAD", 6: "MH_DYLIB",
             7: "MH_DYLINKER", 8: "MH_BUNDLE", 9: "MH_DYLIB_STUB", 10: "MH_DSYM", 11: "MH_KEXT_BUNDLE",
             12: "MH_FILESET", 13: "MH_GPU_EXECUTE", 14: "MH_GPU_DYLIB"}

HEADER_FLAGS = [(0x1, "MH_NOUNDEFS"), (0x2, "MH_INCRLINK"), (0x4, "MH_DYLDLINK"), (0x8, "MH_BINDATLOAD"),
                (0x10, "MH_PREBOUND"), (0x20, "MH_SPLIT_SEGS"), (0x40, "MH_LAZY_INIT"), (0x80, "MH_TWOLEVEL"),
                (0x100, "MH_FORCE_FLAT"), (0x200, "MH_NOMULTIDEFS"), (0x400, "MH_NOFIXPREBINDING"),
                (0x800, "MH_PREBINDABLE"), (0x1000, "MH_ALLMODSBOUND"), (0x2000, "MH_SUBSECTIONS_VIA_SYMBOLS"),
                (0x4000, "MH_CANONICAL"), (0x8000, "MH_WEAK_DEFINES"), (0x10000, "MH_BINDS_TO_WEAK"),
                (0x20000, "MH_ALLOW_STACK_EXECUTION"), (0x40000, "MH_ROOT_SAFE"), (0x80000, "MH_SETUID_SAFE"),
                (0x100000, "MH_NO_REEXPORTED_DYLIBS"), (0x200000, "MH_PIE"),
                (0x400000, "MH_DEAD_STRIPPABLE_DYLIB"), (0x800000, "MH_HAS_TLV_DESCRIPTORS"),
                (0x1000000, "MH_NO_HEAP_EXECUTION"), (0x2000000, "MH_APP_EXTENSION_SAFE"),
                (0x4000000, "MH_NLIST_OUTOFSYNC_WITH_DYLDINFO"), (0x8000000, "MH_SIM_SUPPORT"),
                (0x80000000, "MH_DYLIB_IN_CACHE")]

LC_REQ_DYLD = 0x80000000
# Full command values, the LC_REQ_DYLD bit included where loader.h defines it.
LC_NAMES = {
    0x1: "LC_SEGMENT", 0x2: "LC_SYMTAB", 0x3: "LC_SYMSEG", 0x4: "LC_THREAD", 0x5: "LC_UNIXTHREAD",
    0x6: "LC_LOADFVMLIB", 0x7: "LC_IDFVMLIB", 0x8: "LC_IDENT", 0x9: "LC_FVMFILE", 0xA: "LC_PREPAGE",
    0xB: "LC_DYSYMTAB", 0xC: "LC_LOAD_DYLIB", 0xD: "LC_ID_DYLIB", 0xE: "LC_LOAD_DYLINKER",
    0xF: "LC_ID_DYLINKER", 0x10: "LC_PREBOUND_DYLIB", 0x11: "LC_ROUTINES", 0x12: "LC_SUB_FRAMEWORK",
    0x13: "LC_SUB_UMBRELLA", 0x14: "LC_SUB_CLIENT", 0x15: "LC_SUB_LIBRARY", 0x16: "LC_TWOLEVEL_HINTS",
    0x17: "LC_PREBIND_CKSUM", 0x18 | LC_REQ_DYLD: "LC_LOAD_WEAK_DYLIB", 0x19: "LC_SEGMENT_64",
    0x1A: "LC_ROUTINES_64", 0x1B: "LC_UUID", 0x1C | LC_REQ_DYLD: "LC_RPATH", 0x1D: "LC_CODE_SIGNATURE",
    0x1E: "LC_SEGMENT_SPLIT_INFO", 0x1F | LC_REQ_DYLD: "LC_REEXPORT_DYLIB", 0x20: "LC_LAZY_LOAD_DYLIB",
    0x21: "LC_ENCRYPTION_INFO", 0x22: "LC_DYLD_INFO", 0x22 | LC_REQ_DYLD: "LC_DYLD_INFO_ONLY",
    0x23 | LC_REQ_DYLD: "LC_LOAD_UPWARD_DYLIB", 0x24: "LC_VERSION_MIN_MACOSX", 0x25: "LC_VERSION_MIN_IPHONEOS",
    0x26: "LC_FUNCTION_STARTS", 0x27: "LC_DYLD_ENVIRONMENT", 0x28 | LC_REQ_DYLD: "LC_MAIN",
    0x29: "LC_DATA_IN_CODE", 0x2A: "LC_SOURCE_VERSION", 0x2B: "LC_DYLIB_CODE_SIGN_DRS",
    0x2C: "LC_ENCRYPTION_INFO_64", 0x2D: "LC_LINKER_OPTION", 0x2E: "LC_LINKER_OPTIMIZATION_HINT",
    0x2F: "LC_VERSION_MIN_TVOS", 0x30: "LC_VERSION_MIN_WATCHOS", 0x31: "LC_NOTE", 0x32: "LC_BUILD_VERSION",
    0x33 | LC_REQ_DYLD: "LC_DYLD_EXPORTS_TRIE", 0x34 | LC_REQ_DYLD: "LC_DYLD_CHAINED_FIXUPS",
    0x35 | LC_REQ_DYLD: "LC_FILESET_ENTRY", 0x36: "LC_ATOM_INFO",
}
# Recent SDK headers define 0x37 to 0x39 as well; the names are given for diagnostics only.
LC_NAMES_RECENT = {0x37: "LC_FUNCTION_VARIANTS", 0x38: "LC_FUNCTION_VARIANT_FIXUPS", 0x39: "LC_TARGET_TRIPLE"}

DYLIB_COMMANDS = {"LC_LOAD_DYLIB", "LC_LOAD_WEAK_DYLIB", "LC_REEXPORT_DYLIB", "LC_LOAD_UPWARD_DYLIB",
                  "LC_LAZY_LOAD_DYLIB", "LC_ID_DYLIB"}
REFERENCE_COMMANDS = DYLIB_COMMANDS - {"LC_ID_DYLIB"}
LINKEDIT_DATA = {"LC_CODE_SIGNATURE", "LC_SEGMENT_SPLIT_INFO", "LC_FUNCTION_STARTS", "LC_DATA_IN_CODE",
                 "LC_DYLIB_CODE_SIGN_DRS", "LC_LINKER_OPTIMIZATION_HINT", "LC_DYLD_EXPORTS_TRIE",
                 "LC_DYLD_CHAINED_FIXUPS", "LC_ATOM_INFO", "LC_FUNCTION_VARIANTS", "LC_FUNCTION_VARIANT_FIXUPS"}
PLATFORMS = {1: "MACOS", 2: "IOS", 3: "TVOS", 4: "WATCHOS", 5: "BRIDGEOS", 6: "MACCATALYST", 7: "IOSSIMULATOR",
             8: "TVOSSIMULATOR", 9: "WATCHOSSIMULATOR", 10: "DRIVERKIT", 11: "VISIONOS", 12: "VISIONOSSIMULATOR"}
TOOLS = {1: "CLANG", 2: "SWIFT", 3: "LD", 4: "LLD", 1024: "METAL", 1025: "AIRLLD", 1026: "AIRNT",
         1027: "AIRNT_PLUGIN", 1028: "AIRPACK", 1031: "GPUARCHIVER", 1032: "METAL_FRAMEWORK"}

SYSTEM_PREFIXES = ("/usr/lib/", "/System/Library/")

# The contract's rule sets, transcribed from CONTRACT.md sections 4 and 7 (design revision 4;
# AMENDMENT-001 changes neither section).
CONTRACT_NODE_ALLOWED = {"LC_SEGMENT_64", "LC_SYMTAB", "LC_DYSYMTAB", "LC_LOAD_DYLINKER", "LC_UUID",
                         "LC_BUILD_VERSION", "LC_SOURCE_VERSION", "LC_MAIN", "LC_LOAD_DYLIB", "LC_LOAD_WEAK_DYLIB",
                         "LC_FUNCTION_STARTS", "LC_DATA_IN_CODE", "LC_CODE_SIGNATURE", "LC_DYLD_INFO_ONLY",
                         "LC_DYLD_CHAINED_FIXUPS", "LC_DYLD_EXPORTS_TRIE"}
CONTRACT_NODE_REFUSED = {"LC_RPATH", "LC_DYLD_ENVIRONMENT", "LC_LOAD_UPWARD_DYLIB", "LC_REEXPORT_DYLIB"}
CONTRACT_PYTHON_ALLOWED = CONTRACT_NODE_ALLOWED | {"LC_ID_DYLIB", "LC_RPATH"}
CONTRACT_PYTHON_REFUSED = {"LC_DYLD_ENVIRONMENT", "LC_LOAD_UPWARD_DYLIB"}
CONTRACT_PYTHON_FILETYPES = {"MH_EXECUTE", "MH_DYLIB", "MH_BUNDLE"}


def version_text(value):
    return "%d.%d.%d" % (value >> 16, (value >> 8) & 0xFF, value & 0xFF)


def hexs(value):
    return "0x%08x" % value


# ---------------------------------------------------------------------------
# Files
# ---------------------------------------------------------------------------

def file_identity(path):
    """SHA-256, size, mode and link count through one descriptor; refuses a change during the read."""
    info = os.lstat(path)
    if not stat.S_ISREG(info.st_mode):
        raise ValueError("not a regular file: " + path)
    digest = hashlib.sha256()
    length = 0
    with open(path, "rb", buffering=0) as handle:
        before = os.fstat(handle.fileno())
        while True:
            block = handle.read(4 * 1024 * 1024)
            if not block:
                break
            digest.update(block)
            length += len(block)
        after = os.fstat(handle.fileno())
    if (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns) \
            or length != before.st_size:
        raise ValueError("file changed while read: " + path)
    return {"sha256": digest.hexdigest(), "size_bytes": length, "mode": "0o%03o" % stat.S_IMODE(info.st_mode),
            "nlink": info.st_nlink}


def read_range(path, offset, size):
    with open(path, "rb", buffering=0) as handle:
        handle.seek(offset)
        data = handle.read(size)
    return data


def classify_magic(head):
    """('macho'|'fat'|'cafebabe-java'|'ar-archive'|None, magic name)."""
    if len(head) < 4:
        return None, None
    entry = MAGICS.get(head[:4])
    if entry is None:
        if head[:8] == b"!<arch>\n":
            return "ar-archive", "AR"
        return None, None
    name, kind, _bits, _order = entry
    if name == "FAT_MAGIC" and len(head) >= 8:
        # A Java class file starts with the same 4 bytes; its major version (>= 45) sits where a
        # fat header keeps a small slice count.
        count = struct.unpack(">I", head[4:8])[0]
        if count >= 45:
            return "cafebabe-java", name
    return kind, name


# ---------------------------------------------------------------------------
# Mach-O parsing
# ---------------------------------------------------------------------------

def cstring(body, offset):
    """(text, anomaly) for an lc_str inside a command body."""
    if offset >= len(body):
        return None, "string offset %d not inside command of %d bytes" % (offset, len(body))
    end = body.find(b"\0", offset)
    if end < 0:
        return body[offset:].decode("latin-1"), "string not NUL-terminated inside its command"
    raw = body[offset:end]
    if not raw:
        return "", "empty string"
    if any(byte < 0x20 or byte > 0x7E for byte in raw):
        return raw.decode("latin-1"), "string not printable ASCII"
    return raw.decode("ascii"), None


def decode_command(name, body, order, slice_size, anomalies, index):
    """Decode one command's fields; append structural anomalies."""
    row = {}

    def need(size, exact=False):
        ok = len(body) == size if exact else len(body) >= size
        if not ok:
            anomalies.append("command %d %s: size %d, expected %s%d" % (index, name, len(body),
                                                                        "" if exact else ">=", size))
        return len(body) >= size

    def within(label, offset, size):
        if offset + size > slice_size:
            anomalies.append("command %d %s: %s range %d+%d beyond the slice of %d bytes"
                             % (index, name, label, offset, size, slice_size))

    def string_field(field_offset, minimum, key="path"):
        if not need(minimum):
            return
        offset = struct.unpack_from(order + "I", body, field_offset)[0]
        row[key + "_offset"] = offset
        if offset < minimum:
            anomalies.append("command %d %s: string offset %d inside the fixed structure" % (index, name, offset))
        text, problem = cstring(body, offset)
        row[key] = text
        if problem:
            anomalies.append("command %d %s: %s" % (index, name, problem))

    if name == "LC_SEGMENT_64":
        if need(72):
            segname = body[8:24].split(b"\0", 1)[0].decode("latin-1")
            vmaddr, vmsize, fileoff, filesize, maxprot, initprot, nsects, flags = \
                struct.unpack_from(order + "QQQQiiII", body, 24)
            row.update(segname=segname, vmaddr=hex(vmaddr), vmsize=hex(vmsize), fileoff=fileoff,
                       filesize=filesize, maxprot=maxprot, initprot=initprot, nsects=nsects, flags=hexs(flags))
            if len(body) != 72 + 80 * nsects:
                anomalies.append("command %d LC_SEGMENT_64: cmdsize %d != 72 + 80 * %d" % (index, len(body), nsects))
            within("segment file", fileoff, filesize)
            sections = []
            for number in range(nsects):
                base = 72 + 80 * number
                if base + 80 > len(body):
                    break
                sectname = body[base:base + 16].split(b"\0", 1)[0].decode("latin-1")
                sseg = body[base + 16:base + 32].split(b"\0", 1)[0].decode("latin-1")
                addr, size, offset, align, reloff, nreloc, sflags = struct.unpack_from(order + "QQIIIII", body,
                                                                                        base + 32)
                kind = sflags & 0xFF
                sections.append({"sectname": sectname, "segname": sseg, "addr": hex(addr), "size": size,
                                 "offset": offset, "align": align, "nreloc": nreloc, "flags": hexs(sflags)})
                # Zero-fill sections (S_ZEROFILL 1, S_GB_ZEROFILL 0xc, S_THREAD_LOCAL_ZEROFILL 0x12) have no
                # file content.
                if kind not in (0x1, 0xC, 0x12) and offset:
                    within("section %s,%s" % (sseg, sectname), offset, size)
            row["sections"] = sections
    elif name == "LC_SEGMENT":
        if need(56):
            segname = body[8:24].split(b"\0", 1)[0].decode("latin-1")
            row["segname"] = segname
    elif name == "LC_SYMTAB":
        if need(24, exact=True):
            symoff, nsyms, stroff, strsize = struct.unpack_from(order + "IIII", body, 8)
            row.update(symoff=symoff, nsyms=nsyms, stroff=stroff, strsize=strsize)
            within("symbol table", symoff, nsyms * 16)
            within("string table", stroff, strsize)
    elif name == "LC_DYSYMTAB":
        if need(80, exact=True):
            fields = struct.unpack_from(order + "18I", body, 8)
            keys = ("ilocalsym", "nlocalsym", "iextdefsym", "nextdefsym", "iundefsym", "nundefsym", "tocoff",
                    "ntoc", "modtaboff", "nmodtab", "extrefsymoff", "nextrefsyms", "indirectsymoff",
                    "nindirectsyms", "extreloff", "nextrel", "locreloff", "nlocrel")
            row.update(dict(zip(keys, fields)))
            within("indirect symbols", row["indirectsymoff"], row["nindirectsyms"] * 4)
    elif name in DYLIB_COMMANDS:
        string_field(8, 24)
        if len(body) >= 24:
            timestamp, current, compatibility = struct.unpack_from(order + "III", body, 12)
            row.update(timestamp=timestamp, current_version=version_text(current),
                       compatibility_version=version_text(compatibility))
    elif name in ("LC_LOAD_DYLINKER", "LC_ID_DYLINKER", "LC_DYLD_ENVIRONMENT", "LC_RPATH", "LC_SUB_FRAMEWORK",
                  "LC_SUB_UMBRELLA", "LC_SUB_CLIENT", "LC_SUB_LIBRARY"):
        string_field(8, 12)
    elif name == "LC_UUID":
        if need(24, exact=True):
            text = body[8:24].hex().upper()
            row["uuid"] = "-".join((text[0:8], text[8:12], text[12:16], text[16:20], text[20:32]))
    elif name == "LC_BUILD_VERSION":
        if need(24):
            platform, minos, sdk, ntools = struct.unpack_from(order + "IIII", body, 8)
            row.update(platform=platform, platform_name=PLATFORMS.get(platform), minos=version_text(minos),
                       sdk=version_text(sdk), ntools=ntools)
            if len(body) != 24 + 8 * ntools:
                anomalies.append("command %d LC_BUILD_VERSION: cmdsize %d != 24 + 8 * %d" % (index, len(body), ntools))
            tools = []
            for number in range(ntools):
                base = 24 + 8 * number
                if base + 8 > len(body):
                    break
                tool, version = struct.unpack_from(order + "II", body, base)
                tools.append({"tool": tool, "tool_name": TOOLS.get(tool), "version": version_text(version)})
            row["tools"] = tools
    elif name in ("LC_VERSION_MIN_MACOSX", "LC_VERSION_MIN_IPHONEOS", "LC_VERSION_MIN_TVOS", "LC_VERSION_MIN_WATCHOS"):
        if need(16, exact=True):
            version, sdk = struct.unpack_from(order + "II", body, 8)
            row.update(version=version_text(version), sdk=version_text(sdk))
    elif name == "LC_SOURCE_VERSION":
        if need(16, exact=True):
            value = struct.unpack_from(order + "Q", body, 8)[0]
            row["version"] = "%d.%d.%d.%d.%d" % (value >> 40, (value >> 30) & 0x3FF, (value >> 20) & 0x3FF,
                                                 (value >> 10) & 0x3FF, value & 0x3FF)
    elif name == "LC_MAIN":
        if need(24, exact=True):
            entryoff, stacksize = struct.unpack_from(order + "QQ", body, 8)
            row.update(entryoff=entryoff, stacksize=stacksize)
            within("entry point", entryoff, 0)
    elif name in LINKEDIT_DATA:
        if need(16, exact=True):
            dataoff, datasize = struct.unpack_from(order + "II", body, 8)
            row.update(dataoff=dataoff, datasize=datasize)
            within("linkedit data", dataoff, datasize)
    elif name in ("LC_DYLD_INFO", "LC_DYLD_INFO_ONLY"):
        if need(48, exact=True):
            values = struct.unpack_from(order + "10I", body, 8)
            keys = ("rebase", "bind", "weak_bind", "lazy_bind", "export")
            for number, key in enumerate(keys):
                row[key + "_off"], row[key + "_size"] = values[2 * number], values[2 * number + 1]
                within(key, values[2 * number], values[2 * number + 1])
    elif name in ("LC_ENCRYPTION_INFO", "LC_ENCRYPTION_INFO_64"):
        if need(20):
            cryptoff, cryptsize, cryptid = struct.unpack_from(order + "III", body, 8)
            row.update(cryptoff=cryptoff, cryptsize=cryptsize, cryptid=cryptid)
    elif name == "LC_LINKER_OPTION":
        if need(12):
            count = struct.unpack_from(order + "I", body, 8)[0]
            parts = body[12:].split(b"\0")
            row.update(count=count, strings=[part.decode("latin-1") for part in parts[:count]])
    elif name == "LC_NOTE":
        if need(40, exact=True):
            owner = body[8:24].split(b"\0", 1)[0].decode("latin-1")
            offset, size = struct.unpack_from(order + "QQ", body, 24)
            row.update(data_owner=owner, offset=offset, size=size)
            within("note", offset, size)
    elif name in ("LC_TARGET_TRIPLE",):
        string_field(8, 12, key="triple")
    return row


def parse_slice(path, offset, size):
    """Header and every load command of one thin Mach-O image at ``offset`` (``size`` bytes)."""
    head = read_range(path, offset, 32)
    entry = MAGICS.get(head[:4])
    result = {"offset": offset, "size": size, "anomalies": []}
    anomalies = result["anomalies"]
    if entry is None or entry[1] != "macho":
        result["magic"] = head[:4].hex()
        anomalies.append("slice does not start with a thin Mach-O magic")
        return result
    magic_name, _kind, bits, order = entry
    header_size = 32 if bits == 64 else 28
    if len(head) < header_size:
        anomalies.append("truncated header")
        return result
    fields = struct.unpack_from(order + "IiiIIII", head, 0)
    _magic, cputype, cpusubtype, filetype, ncmds, sizeofcmds, flags = fields
    cputype &= 0xFFFFFFFF
    cpusubtype &= 0xFFFFFFFF
    reserved = struct.unpack_from(order + "I", head, 28)[0] if bits == 64 else None
    subtype_value = cpusubtype & ~CPU_SUBTYPE_MASK & 0xFFFFFFFF
    capability = cpusubtype & CPU_SUBTYPE_MASK
    if cputype == 12 | CPU_ARCH_ABI64:
        subtype_name = ARM64_SUBTYPES.get(subtype_value)
        capability_names = []
        if capability & 0x80000000:
            capability_names.append("CPU_SUBTYPE_PTRAUTH_ABI")
        if capability & 0x0F000000:
            capability_names.append("ptrauth ABI version %d" % ((capability >> 24) & 0xF))
        if capability & 0x70000000:
            capability_names.append("other capability bits 0x%08x" % (capability & 0x70000000))
    elif cputype == 7 | CPU_ARCH_ABI64:
        subtype_name = X86_64_SUBTYPES.get(subtype_value)
        capability_names = ["CPU_SUBTYPE_LIB64"] if capability & 0x80000000 else []
        if capability & 0x7F000000:
            capability_names.append("other capability bits 0x%08x" % (capability & 0x7F000000))
    else:
        subtype_name = None
        capability_names = ["0x%08x" % capability] if capability else []
    names = [label for bit, label in HEADER_FLAGS if flags & bit]
    unknown_flags = flags & ~sum(bit for bit, _ in HEADER_FLAGS) & 0xFFFFFFFF
    result["header"] = {
        "magic": magic_name, "bits": bits, "byte_order": "little" if order == "<" else "big",
        "cputype": hexs(cputype), "cputype_name": CPU_TYPES.get(cputype),
        "cpusubtype_raw": hexs(cpusubtype), "cpusubtype_value": subtype_value, "cpusubtype_name": subtype_name,
        "cpusubtype_capability_bits": hexs(capability), "cpusubtype_capabilities": capability_names,
        "filetype": filetype, "filetype_name": FILETYPES.get(filetype), "ncmds": ncmds, "sizeofcmds": sizeofcmds,
        "flags": hexs(flags), "flag_names": names, "unknown_flag_bits": hexs(unknown_flags),
        "reserved": hexs(reserved) if reserved is not None else None}
    if header_size + sizeofcmds > size:
        anomalies.append("load command table (%d bytes) escapes the slice" % sizeofcmds)
        return result
    table = read_range(path, offset + header_size, sizeofcmds)
    commands = []
    position = 0
    for index in range(ncmds):
        if position + 8 > len(table):
            anomalies.append("command %d header beyond sizeofcmds" % index)
            break
        cmd, cmdsize = struct.unpack_from(order + "II", table, position)
        name = LC_NAMES.get(cmd) or LC_NAMES_RECENT.get(cmd)
        row = {"index": index, "file_offset": header_size + position, "cmd": hexs(cmd), "name": name,
               "classic_loader_h": cmd in LC_NAMES, "req_dyld": bool(cmd & LC_REQ_DYLD), "cmdsize": cmdsize}
        if cmdsize < 8 or position + cmdsize > len(table):
            anomalies.append("command %d cmdsize %d invalid or escapes sizeofcmds" % (index, cmdsize))
            commands.append(row)
            break
        if cmdsize % (8 if bits == 64 else 4):
            anomalies.append("command %d cmdsize %d not a multiple of %d" % (index, cmdsize, 8 if bits == 64 else 4))
        body = table[position:position + cmdsize]
        if name is None:
            row["unknown"] = True
            row["body_hex_prefix"] = body[:64].hex()
        else:
            row.update(decode_command(name, body, order, size, anomalies, index))
        commands.append(row)
        position += cmdsize
    if position != sizeofcmds:
        anomalies.append("commands occupy %d bytes; sizeofcmds is %d" % (position, sizeofcmds))
    if len(commands) != ncmds:
        anomalies.append("parsed %d of %d commands" % (len(commands), ncmds))
    # Overlap of segment file ranges (dyld refuses overlapping segment content).
    ranges = sorted((row["fileoff"], row["fileoff"] + row["filesize"], row["segname"]) for row in commands
                    if row.get("name") == "LC_SEGMENT_64" and row.get("filesize"))
    for (start_a, end_a, name_a), (start_b, end_b, name_b) in zip(ranges, ranges[1:]):
        if start_b < end_a:
            anomalies.append("segments %s and %s overlap in the file" % (name_a, name_b))
    result["load_commands"] = commands
    return result


def read_macho_file(path):
    """The complete record of one file: identity, container, fat slices and every thin image."""
    record = {"path": path}
    record.update(file_identity(path))
    head = read_range(path, 0, 4096)
    kind, magic = classify_magic(head)
    record["magic_class"] = kind
    record["magic"] = magic
    if kind == "macho":
        record["container"] = "thin"
        record["slices"] = [parse_slice(path, 0, record["size_bytes"])]
    elif kind == "fat":
        _name, _kind, bits, order = MAGICS[head[:4]]
        nfat = struct.unpack_from(order + "I", head, 4)[0]
        record["container"] = "fat"
        arches = []
        size = 20 if bits == 32 else 32
        table = read_range(path, 8, nfat * size)
        for number in range(nfat):
            if bits == 32:
                cputype, cpusubtype, offset, length, align = struct.unpack_from(order + "iiIII", table, number * 20)
            else:
                cputype, cpusubtype, offset, length, align, _reserved = struct.unpack_from(order + "iiQQII", table,
                                                                                            number * 32)
            cputype &= 0xFFFFFFFF
            cpusubtype &= 0xFFFFFFFF
            arches.append({"cputype": hexs(cputype), "cputype_name": CPU_TYPES.get(cputype),
                           "cpusubtype": hexs(cpusubtype), "offset": offset, "size": length, "align": align})
        record["fat"] = {"magic": magic, "nfat_arch": nfat, "arches": arches}
        record["slices"] = [parse_slice(path, row["offset"], row["size"]) for row in arches]
    else:
        record["container"] = "not-macho"
    return record


def image_view(record):
    """The single thin image of a record, or None."""
    if record.get("container") != "thin":
        return None
    return record["slices"][0]


def commands_of(record):
    view = image_view(record)
    return [] if view is None else view.get("load_commands", [])


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def resolve(path, limit=64):
    """Kernel-style resolution of an absolute path; every symbolic-link hop in order.

    Returns {state: file|directory|other|absent|not-a-directory, path, hops}. ``..`` applies to the
    physical directory reached so far, as the kernel's lookup does.
    """
    pending = [part for part in path.split("/") if part]
    current, hops = "/", []
    while pending:
        part = pending.pop(0)
        if part == ".":
            continue
        if part == "..":
            current = posixpath.dirname(current) if current != "/" else "/"
            continue
        candidate = current.rstrip("/") + "/" + part
        try:
            info = os.lstat(candidate)
        except FileNotFoundError:
            return {"state": "absent", "path": candidate + ("/" + "/".join(pending) if pending else ""), "hops": hops}
        if stat.S_ISLNK(info.st_mode):
            target = os.readlink(candidate)
            hops.append({"path": candidate, "target": target})
            if len(hops) > limit:
                return {"state": "loop", "path": candidate, "hops": hops}
            if target.startswith("/"):
                current = "/"
            pending = [segment for segment in target.split("/") if segment] + pending
            continue
        if pending and not stat.S_ISDIR(info.st_mode):
            return {"state": "not-a-directory", "path": candidate, "hops": hops}
        current = candidate
    info = os.lstat(current)
    state = "file" if stat.S_ISREG(info.st_mode) else "directory" if stat.S_ISDIR(info.st_mode) else "other"
    return {"state": state, "path": current, "hops": hops}


def list_tree(root):
    """Exhaustive listing of a tree without following links: files, links (with targets), directories."""
    files, links, directories, special = [], [], [], []
    stack = [root]
    while stack:
        directory = stack.pop()
        with os.scandir(directory) as iterator:
            entries = sorted(iterator, key=lambda entry: entry.name)
        for entry in entries:
            path = directory + "/" + entry.name
            info = os.lstat(path)
            if stat.S_ISLNK(info.st_mode):
                links.append({"path": path, "target": os.readlink(path)})
            elif stat.S_ISDIR(info.st_mode):
                directories.append(path)
                stack.append(path)
            elif stat.S_ISREG(info.st_mode):
                files.append(path)
            else:
                special.append(path)
    return {"files": sorted(files), "links": sorted(links, key=lambda row: row["path"]),
            "directories": sorted(directories), "special": sorted(special)}


def inside(path, root):
    return path == root or path.startswith(root.rstrip("/") + "/")


# ---------------------------------------------------------------------------
# The dyld shared cache's image list (header and image table only)
# ---------------------------------------------------------------------------

def shared_cache_images(path):
    """The main cache file's header fields and its image-path table (the file is small; subcaches are not read)."""
    identity = file_identity(path)
    with open(path, "rb") as handle:
        blob = handle.read()
    magic = blob[:16].split(b"\0", 1)[0].decode("latin-1")
    mapping_offset, mapping_count = struct.unpack_from("<II", blob, 16)
    if mapping_offset >= 456:
        images_offset, images_count = struct.unpack_from("<II", blob, 448)
        source = "imagesOffset/imagesCount"
    else:
        images_offset, images_count = struct.unpack_from("<II", blob, 24)
        source = "imagesOffsetOld/imagesCountOld"
    uuid = blob[88:104].hex().upper()
    platform = struct.unpack_from("<I", blob, 216)[0]
    dyld_in_cache_mh, dyld_in_cache_entry = struct.unpack_from("<QQ", blob, 120)
    os_version = struct.unpack_from("<I", blob, 364)[0] if mapping_offset >= 368 else None
    sub_count = struct.unpack_from("<I", blob, 396)[0] if mapping_offset >= 400 else None
    paths = []
    for number in range(images_count):
        _address, _mtime, _inode, path_offset, _pad = struct.unpack_from("<QQQII", blob, images_offset + number * 32)
        paths.append(blob[path_offset:blob.index(b"\0", path_offset)].decode("utf-8", "replace"))
    return {"path": path, **identity, "magic": magic, "mapping_offset": mapping_offset,
            "mapping_count": mapping_count, "image_table": source, "images_count": images_count,
            "uuid": "-".join((uuid[0:8], uuid[8:12], uuid[12:16], uuid[16:20], uuid[20:32])),
            "platform": platform, "os_version": version_text(os_version) if os_version is not None else None,
            "dyld_in_cache_mh": hex(dyld_in_cache_mh), "dyld_in_cache_entry": hex(dyld_in_cache_entry),
            "sub_cache_count": sub_count, "images": paths,
            "usr_lib_dyld_in_image_list": "/usr/lib/dyld" in paths}


# ---------------------------------------------------------------------------
# Contract rules, evaluated independently
# ---------------------------------------------------------------------------

def at_kind(path):
    if path.startswith("@rpath/"):
        return "@rpath"
    if path.startswith("@loader_path/"):
        return "@loader_path"
    if path.startswith("@executable_path/"):
        return "@executable_path"
    if path.startswith("@"):
        return "@other"
    return None


def normalized_absolute(path):
    return path.startswith("/") and not path.startswith("//") and posixpath.normpath(path) == path


def strings_of(row):
    return [row[key] for key in ("path", "triple") if isinstance(row.get(key), str)]


def node_rules(record):
    """Contract section 7 (and section 3's 'thin 64-bit arm64 Mach-O executable')."""
    reasons = []
    if record["container"] != "thin":
        reasons.append("not thin (" + record["container"] + ")")
        return {"verdict": "REFUSE", "reasons": reasons}
    view = image_view(record)
    header = view.get("header", {})
    if header.get("magic") != "MH_MAGIC_64":
        reasons.append("not 64-bit little-endian")
    if header.get("cputype_name") != "CPU_TYPE_ARM64":
        reasons.append("CPU type other than arm64")
    if header.get("filetype_name") != "MH_EXECUTE":
        reasons.append("file type other than MH_EXECUTE")
    if view["anomalies"]:
        reasons.append("structural anomalies: " + "; ".join(view["anomalies"]))
    for row in view.get("load_commands", []):
        name = row["name"]
        if name is None:
            reasons.append("unknown command %s at index %d" % (row["cmd"], row["index"]))
            continue
        if name in CONTRACT_NODE_REFUSED:
            reasons.append("refused command %s" % name)
        elif name not in CONTRACT_NODE_ALLOWED:
            reasons.append("command outside the closed allow-list: %s" % name)
        for text in strings_of(row):
            if text.startswith("@"):
                reasons.append("@-relative path in %s: %s" % (name, text))
        if name == "LC_LOAD_DYLINKER" and row.get("path") != "/usr/lib/dyld":
            reasons.append("LC_LOAD_DYLINKER is %r" % row.get("path"))
        if name in DYLIB_COMMANDS:
            text = row.get("path") or ""
            if not (normalized_absolute(text) and text.startswith(SYSTEM_PREFIXES)):
                reasons.append("dylib path outside /usr/lib/ and /System/Library/: %s" % text)
    return {"verdict": "REFUSE" if reasons else "ACCEPT", "reasons": reasons}


def python_rules(record):
    """Contract section 4's per-file rules; @-relative resolution is judged by the closure."""
    reasons = []
    if record["container"] != "thin":
        reasons.append("not thin (" + record["container"] + ")")
        return {"verdict": "REFUSE", "reasons": reasons}
    view = image_view(record)
    header = view.get("header", {})
    if header.get("magic") != "MH_MAGIC_64" or header.get("cputype_name") != "CPU_TYPE_ARM64":
        reasons.append("not a 64-bit arm64 image")
    if header.get("filetype_name") not in CONTRACT_PYTHON_FILETYPES:
        reasons.append("file type %s outside MH_EXECUTE, MH_DYLIB, MH_BUNDLE" % header.get("filetype_name"))
    if view["anomalies"]:
        reasons.append("structural anomalies: " + "; ".join(view["anomalies"]))
    for row in view.get("load_commands", []):
        name = row["name"]
        if name is None:
            reasons.append("unknown command %s at index %d" % (row["cmd"], row["index"]))
            continue
        if name in CONTRACT_PYTHON_REFUSED:
            reasons.append("refused command %s" % name)
        elif name not in CONTRACT_PYTHON_ALLOWED:
            reasons.append("command outside the accepted set (Node's allow-list, LC_ID_DYLIB, LC_RPATH): %s" % name)
        if name == "LC_LOAD_DYLINKER" and row.get("path") != "/usr/lib/dyld":
            reasons.append("LC_LOAD_DYLINKER is %r" % row.get("path"))
        if name in REFERENCE_COMMANDS:
            text = row.get("path") or ""
            kind = at_kind(text)
            if kind == "@other":
                reasons.append("@-relative reference of an unsupported form: %s" % text)
            elif kind is None and not normalized_absolute(text):
                reasons.append("reference neither @-relative nor a normalized absolute path: %s" % text)
        if name == "LC_RPATH":
            text = row.get("path") or ""
            if text.startswith("@") and not (text in ("@loader_path", "@executable_path")
                                             or text.startswith(("@loader_path/", "@executable_path/"))):
                reasons.append("LC_RPATH of an unsupported @ form: %s" % text)
    return {"verdict": "REFUSE" if reasons else "ACCEPT", "reasons": reasons}


# ---------------------------------------------------------------------------
# Interpreter installation and its closure
# ---------------------------------------------------------------------------

def parse_pyvenv(path):
    values = {}
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle.read().splitlines():
            if "=" in line:
                key, value = (part.strip() for part in line.split("=", 1))
                values[key] = value
    return values


def interpreter(venv):
    cfg = parse_pyvenv(venv + "/pyvenv.cfg")
    chain = resolve(venv + "/bin/python")
    launcher = chain["path"]
    version_dir = posixpath.dirname(posixpath.dirname(launcher))
    home_launcher = resolve(cfg.get("home", "").rstrip("/") + "/python" + posixpath.basename(version_dir))
    executable = resolve(cfg["executable"]) if "executable" in cfg else None
    return {"pyvenv_cfg": cfg, "launcher_chain": chain, "launcher": launcher, "version_directory": version_dir,
            "home_chain": resolve(cfg.get("home", "/")), "home_launcher_chain": home_launcher,
            "executable_chain": executable,
            "realpath_cross_check": {"launcher": os.path.realpath(venv + "/bin/python"),
                                     "agrees": os.path.realpath(venv + "/bin/python") == launcher}}


def closure(images, process_image, python_library, framework, venv):
    """Repeat closure passes until the spellings and referrers are stable (at most 12 passes)."""
    records = dict(images)
    spellings = {path: {path} for path in records}
    referrers = {}
    for number in range(12):
        before = ({key: frozenset(value) for key, value in spellings.items()},
                  {key: frozenset(value) for key, value in referrers.items()})
        result = closure_pass(records, spellings, referrers, process_image, python_library, framework, venv)
        after = ({key: frozenset(value) for key, value in spellings.items()},
                 {key: frozenset(value) for key, value in referrers.items()})
        if before == after:
            result["passes"] = number + 1
            result["external"] = {path: records[path] for path in records if path not in images}
            return result
    raise RuntimeError("closure did not stabilize")


def closure_pass(records, spellings, referrers, process_image, python_library, framework, venv):
    """Resolve every reference of every image; external targets join the work list.

    For @rpath it computes two resolutions: 'own' (the image's own LC_RPATH entries) and
    'stack' (own entries, then those of each image that references this one, transitively, then
    the dlopen caller (the Python library) and the main executable, the process image).
    @loader_path uses the image's canonical directory and the directory of every spelling by
    which another image references it. @executable_path uses the process image's directory, and
    an executable's own directory for that executable.
    """
    rows = {}
    order = sorted(records)
    position = 0

    def rpaths(path):
        out = []
        for row in commands_of(records[path]):
            if row.get("name") == "LC_RPATH":
                out.append(row.get("path"))
        return out

    def expand_rpath(raw, owner):
        bases = []
        if raw.startswith("@loader_path"):
            for spelling in sorted(spellings.get(owner, {owner})):
                bases.append(posixpath.dirname(spelling) + raw[len("@loader_path"):])
        elif raw.startswith("@executable_path"):
            bases.append(posixpath.dirname(process_image) + raw[len("@executable_path"):])
        else:
            bases.append(raw)
        return bases

    while position < len(order):
        path = order[position]
        position += 1
        record = records[path]
        view = image_view(record)
        if view is None or "header" not in view:
            rows[path] = {"error": "not a thin image"}
            continue
        filetype = view["header"].get("filetype_name")
        out = []
        for row in view.get("load_commands", []):
            if row.get("name") not in REFERENCE_COMMANDS:
                continue
            raw = row.get("path") or ""
            entry = {"command": row["name"], "raw": raw}
            kind = at_kind(raw)
            if kind is None and raw.startswith(SYSTEM_PREFIXES):
                entry["kind"] = "system"
                out.append(entry)
                continue
            entry["kind"] = kind or "absolute"
            candidates = []
            if kind == "@loader_path":
                for spelling in sorted(spellings.get(path, {path})):
                    candidates.append(posixpath.dirname(spelling) + raw[len("@loader_path"):])
            elif kind == "@executable_path":
                base = path if filetype == "MH_EXECUTE" else process_image
                candidates.append(posixpath.dirname(base) + raw[len("@executable_path"):])
            elif kind == "@rpath":
                own = []
                for rp in rpaths(path):
                    own.extend(expand_rpath(rp, path))
                stack = list(own)
                seen, frontier = {path}, list(referrers.get(path, ()))
                while frontier:
                    parent = frontier.pop(0)
                    if parent in seen:
                        continue
                    seen.add(parent)
                    for rp in rpaths(parent):
                        stack.extend(expand_rpath(rp, parent))
                    frontier.extend(referrers.get(parent, ()))
                for anchor in (python_library, process_image):
                    if anchor in records and anchor not in seen:
                        for rp in rpaths(anchor):
                            stack.extend(expand_rpath(rp, anchor))
                suffix = raw[len("@rpath"):]
                entry["own_rpath_candidates"] = [{"candidate": base + suffix, **resolve(base + suffix)}
                                                 for base in own]
                entry["stack_rpath_candidates"] = [{"candidate": base + suffix, **resolve(base + suffix)}
                                                   for base in stack]
                own_hit = next((row2 for row2 in entry["own_rpath_candidates"] if row2["state"] == "file"), None)
                stack_hit = next((row2 for row2 in entry["stack_rpath_candidates"] if row2["state"] == "file"), None)
                entry["own_resolves"] = own_hit is not None
                entry["stack_resolves"] = stack_hit is not None
                hit = stack_hit or own_hit
                candidates = [hit["candidate"]] if hit else []
            elif kind == "@other":
                entry["unsupported"] = True
                out.append(entry)
                continue
            else:
                candidates.append(raw)
            outcomes = [{"spelling": spelling, **resolve(spelling)} for spelling in candidates]
            entry["outcomes"] = outcomes
            distinct = {(row2["state"], row2["path"]) for row2 in outcomes}
            entry["agree"] = len(distinct) <= 1
            if outcomes and outcomes[0]["state"] == "file":
                target = outcomes[0]["path"]
                entry["target"] = target
                entry["target_tree"] = ("framework" if inside(target, framework) else
                                        "venv" if inside(target, venv) else
                                        "system" if target.startswith(SYSTEM_PREFIXES) else "external")
                referrers.setdefault(target, set()).add(path)
                for outcome in outcomes:
                    spellings.setdefault(target, {target}).add(outcome["spelling"])
                if entry["target_tree"] in ("framework", "venv") and target not in records:
                    entry["tree_target_not_an_image"] = True
                elif entry["target_tree"] == "system":
                    entry["non_system_reference_resolves_into_system_tree"] = True
                else:
                    if target not in records:
                        records[target] = read_macho_file(target)
                        spellings.setdefault(target, {target})
                    if target not in order:
                        order.append(target)
            else:
                entry["target"] = None
            out.append(entry)
        rows[path] = {"filetype": filetype, "references": out}
    return {"references": rows,
            "spellings": {path: sorted(names) for path, names in spellings.items() if len(names) > 1},
            "referrers": {path: sorted(names) for path, names in referrers.items()}}


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def apply_labels(value, labels):
    if isinstance(value, str):
        for name, prefix in labels:
            value = value.replace(prefix, name)
        return value
    if isinstance(value, list):
        return [apply_labels(item, labels) for item in value]
    if isinstance(value, dict):
        return {apply_labels(key, labels): apply_labels(item, labels) for key, item in value.items()}
    return value


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--node", required=True)
    parser.add_argument("--venv", required=True)
    parser.add_argument("--dyld-cache", required=True)
    parser.add_argument("--extra", action="append", default=[])
    parser.add_argument("--label", action="append", default=[])
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    labels = []
    for item in args.label:
        name, _, prefix = item.partition("=")
        labels.append((name, prefix))
    labels.sort(key=lambda row: -len(row[1]))
    started = time.time()

    node = read_macho_file(args.node)
    node["rules"] = node_rules(node)

    selection = interpreter(args.venv)
    framework = selection["version_directory"]
    venv = args.venv
    trees = {"framework": list_tree(framework), "venv": list_tree(venv)}
    classified = {}
    images = {}
    for tree, listing in trees.items():
        counts = {}
        for path in listing["files"]:
            kind, magic = classify_magic(read_range(path, 0, 8))
            key = kind or "other"
            counts[key] = counts.get(key, 0) + 1
            if kind is not None:
                classified[path] = {"tree": tree, "class": kind, "magic": magic}
            if kind in ("macho", "fat"):
                images[path] = read_macho_file(path)
        listing["magic_counts"] = counts
    process_image = framework + "/Resources/Python.app/Contents/MacOS/Python"
    python_library = framework + "/Python"
    resolved = closure(images, process_image, python_library, framework, venv)
    for path, record in images.items():
        record["tree"] = "framework" if inside(path, framework) else "venv"
        record["rules"] = python_rules(record)
    for path, record in resolved["external"].items():
        record["tree"] = "external"
        record["rules"] = python_rules(record)

    # System references of every Python image and of Node, against the disk and the cache.
    cache = shared_cache_images(args.dyld_cache)
    cache_set = set(cache["images"])
    system = {}

    def note_system(owner, row):
        text = row.get("path") or ""
        if text.startswith(SYSTEM_PREFIXES):
            entry = system.setdefault(text, {"referenced_by": [], "commands": set()})
            entry["referenced_by"].append(owner)
            entry["commands"].add(row["name"])
    for row in commands_of(node):
        if row.get("name") in REFERENCE_COMMANDS:
            note_system(args.node, row)
    for path, record in list(images.items()) + list(resolved["external"].items()):
        for row in commands_of(record):
            if row.get("name") in REFERENCE_COMMANDS:
                note_system(path, row)
    for text, entry in system.items():
        entry["commands"] = sorted(entry["commands"])
        entry["referenced_by"] = sorted(set(entry["referenced_by"]))
        entry["on_disk"] = os.path.lexists(text)
        entry["in_shared_cache_image_list"] = text in cache_set

    # Install names against every reference string (a collision could let dyld reuse an image).
    install_names = {}
    for path, record in list(images.items()) + list(resolved["external"].items()):
        for row in commands_of(record):
            if row.get("name") == "LC_ID_DYLIB":
                install_names[path] = row.get("path")
    reference_strings = {}
    for path, record in [(args.node, node)] + list(images.items()) + list(resolved["external"].items()):
        for row in commands_of(record):
            if row.get("name") in REFERENCE_COMMANDS:
                reference_strings.setdefault(row.get("path"), set()).add(path)
    collisions = []
    for path, name in install_names.items():
        if name in reference_strings:
            resolved_name = resolve(name) if name.startswith("/") else {"state": "relative", "path": None}
            collisions.append({"image": path, "install_name": name, "referenced_by": sorted(reference_strings[name]),
                               "install_name_resolves_to": resolved_name.get("path"),
                               "same_file": resolved_name.get("path") == path})
        if name and name in cache_set:
            collisions.append({"image": path, "install_name": name, "in_shared_cache": True})

    extras = []
    for path in args.extra:
        record = read_macho_file(path)
        for view in record.get("slices", []):
            view["dylib_paths"] = [row.get("path") for row in view.get("load_commands", [])
                                   if row.get("name") in DYLIB_COMMANDS]
            view["system_only"] = all((text or "").startswith(SYSTEM_PREFIXES) for text in view["dylib_paths"])
            view["dylib_paths_in_shared_cache_image_list"] = {text: text in cache_set for text in view["dylib_paths"]}
            view["dylib_paths_on_disk"] = {text: os.path.lexists(text) for text in view["dylib_paths"]}
        extras.append(record)

    # The dynamic linker named by LC_LOAD_DYLINKER: an on-disk file of the system volume, not a library of the cache.
    dylinker = {"path": "/usr/lib/dyld", "chain": resolve("/usr/lib/dyld")}
    if dylinker["chain"]["state"] == "file":
        dylinker.update(read_macho_file(dylinker["chain"]["path"]))
        dylinker["slices_summary"] = [{"cputype_name": view.get("header", {}).get("cputype_name"),
                                       "cpusubtype_raw": view.get("header", {}).get("cpusubtype_raw"),
                                       "filetype_name": view.get("header", {}).get("filetype_name")}
                                      for view in dylinker.get("slices", [])]
        dylinker.pop("slices", None)

    document = {
        "schema": "n34m-reader-raw/1",
        "tool": {"name": "n34m_reader.py", "sha256": file_identity(os.path.realpath(__file__))["sha256"],
                 "python": sys.version, "executable": sys.executable,
                 "flags": {"isolated": sys.flags.isolated, "no_site": sys.flags.no_site,
                           "dont_write_bytecode": sys.flags.dont_write_bytecode}},
        "started_unix": started,
        "node": node,
        "python": {"selection": selection, "framework_root": framework, "venv_root": venv,
                   "trees": {tree: {"files": len(listing["files"]), "links": listing["links"],
                                    "directories": len(listing["directories"]), "special": listing["special"],
                                    "magic_counts": listing["magic_counts"]}
                             for tree, listing in trees.items()},
                   "file_lists": {tree: listing["files"] for tree, listing in trees.items()},
                   "directory_lists": {tree: listing["directories"] for tree, listing in trees.items()},
                   "classified_by_magic": classified,
                   "process_image": process_image, "python_library": python_library,
                   "images": images, "external": resolved["external"],
                   "closure": {"references": resolved["references"], "spellings": resolved["spellings"],
                               "referrers": resolved["referrers"]},
                   "install_names": install_names, "install_name_collisions": collisions},
        "system_references": system,
        "dyld_shared_cache": {key: value for key, value in cache.items() if key != "images"},
        "dylinker": dylinker,
        "extras": extras,
        "elapsed_s": round(time.time() - started, 3),
    }
    text = json.dumps(apply_labels(document, labels), indent=1, sort_keys=True, default=sorted) + "\n"
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(text)
    print(json.dumps({"output": apply_labels(args.output, labels), "bytes": len(text),
                      "elapsed_s": document["elapsed_s"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
