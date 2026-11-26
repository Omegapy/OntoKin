#!/usr/bin/env python3
"""N34-M comparison (worker W1, gate MH, phase C271-P35).

Loads the parser under review by file path and calls, on the real files, only its pure reading
and checking functions:
    macho_magic_kind, read_macho, parse_macho, check_node_macho, check_python_macho,
    python_inventory, compare_inventory, python_inventory_digest, verify_packages,
    launcher_state (ctypes proc_pidpath; no process start), check_launcher, read_os_identity.
It never calls observe_host, static_check, static_observation, main, write_new,
rename_exclusive, load_darwin_supervisor, check_git_binding, or anything that starts Git or Node.
Importing the module starts nothing and writes nothing (its docstring and imports say so; this
script checks sys.modules before and after the import).

It then compares the parser's parse of every file with the independent reader's raw output
(n34m_reader.py), and runs in-memory mutation cases against parse_macho, check_node_macho and
check_python_macho to test the structural rules (no file is written for them).

It writes exactly one file, --output, by exclusive creation, with the --label substitutions.

Run:  <venv>/bin/python -I -S -B n34m_compare.py --parser P --reader-json R --node N --venv V
          --framework F --node-source S --label NAME=PATH ... --output OUT.json
"""
import argparse
import hashlib
import importlib.util
import json
import os
import struct
import sys
import time


def apply_labels(value, labels):
    if isinstance(value, str):
        for name, prefix in labels:
            value = value.replace(prefix, name)
        return value
    if isinstance(value, list):
        return [apply_labels(item, labels) for item in value]
    if isinstance(value, tuple):
        return [apply_labels(item, labels) for item in value]
    if isinstance(value, dict):
        return {apply_labels(str(key), labels): apply_labels(item, labels) for key, item in value.items()}
    return value


def load_parser(path):
    before = set(sys.modules)
    spec = importlib.util.spec_from_file_location("n34m_parser_under_review", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    added = sorted(set(sys.modules) - before)
    return module, added


def refusal(module, exc):
    if isinstance(exc, module.ObservationError):
        return {"refused": True, "code": exc.code, "reason": exc.reason, "details": exc.details}
    return {"refused": True, "code": "EXCEPTION", "type": type(exc).__name__, "reason": str(exc)}


def attempt(module, function, *args, **kwargs):
    try:
        return {"refused": False, "value": function(*args, **kwargs)}
    except Exception as exc:  # the parser's refusals and any unexpected error are both recorded
        return refusal(module, exc)


# ---------------------------------------------------------------------------
# Field-by-field comparison of the parser's summary with the reader's record
# ---------------------------------------------------------------------------

COMPARED_FIELDS = ("path", "segname", "fileoff", "filesize", "nsects", "uuid", "minos", "sdk", "platform",
                   "entryoff", "stacksize", "dataoff", "datasize", "current_version", "compatibility_version",
                   "nsyms", "strsize")


def compare_parse(summary, reader_record):
    """Differences between the parser's parse and the reader's, command by command."""
    view = reader_record["slices"][0]
    header = view["header"]
    differences = []
    expected_header = {"cputype": header["cputype"], "cpusubtype": header["cpusubtype_raw"],
                       "filetype": header["filetype_name"], "flags": header["flags"], "ncmds": header["ncmds"],
                       "sizeofcmds": header["sizeofcmds"]}
    for key, value in expected_header.items():
        if summary[key] != value:
            differences.append({"field": "header." + key, "parser": summary[key], "reader": value})
    commands = view["load_commands"]
    if len(summary["commands"]) != len(commands):
        differences.append({"field": "command count", "parser": len(summary["commands"]), "reader": len(commands)})
    for index, (mine, theirs) in enumerate(zip(commands, summary["commands"])):
        if (mine["cmd"], mine["cmdsize"]) != (theirs["cmd"], theirs["cmdsize"]):
            differences.append({"field": "command %d cmd/cmdsize" % index, "parser": [theirs["cmd"], theirs["cmdsize"]],
                                "reader": [mine["cmd"], mine["cmdsize"]]})
        if mine["name"] != theirs["name"]:
            differences.append({"field": "command %d name" % index, "parser": theirs["name"], "reader": mine["name"]})
        for key in COMPARED_FIELDS:
            if key in mine and key in theirs and mine[key] != theirs[key]:
                differences.append({"field": "command %d %s" % (index, key), "parser": theirs[key],
                                    "reader": mine[key]})
            if key in ("path",) and (key in mine) != (key in theirs):
                differences.append({"field": "command %d %s presence" % (index, key), "parser": key in theirs,
                                    "reader": key in mine})
    return differences


# ---------------------------------------------------------------------------
# In-memory mutation cases (structural rules of section (e))
# ---------------------------------------------------------------------------

def command_offsets(data):
    ncmds = struct.unpack_from("<I", data, 16)[0]
    offsets, position = [], 32
    for _ in range(ncmds):
        cmd, size = struct.unpack_from("<II", data, position)
        offsets.append((position, cmd, size))
        position += size
    return offsets


def find(data, cmd, occurrence=0):
    rows = [row for row in command_offsets(data) if row[1] == cmd]
    return rows[occurrence]


def put(data, offset, fmt, *values):
    buffer = bytearray(data)
    struct.pack_into(fmt, buffer, offset, *values)
    return bytes(buffer)


def replace_string(data, cmd, new, occurrence=0, field=8):
    position, _cmd, size = find(data, cmd, occurrence)
    offset = struct.unpack_from("<I", data, position + field)[0]
    room = size - offset
    raw = new.encode("latin-1")
    if len(raw) + 1 > room:
        raise ValueError("replacement does not fit")
    buffer = bytearray(data)
    buffer[position + offset:position + size] = raw + b"\0" * (room - len(raw))
    return bytes(buffer)


def retype(data, old_cmd, new_cmd, occurrence=0):
    position, _cmd, _size = find(data, old_cmd, occurrence)
    return put(data, position, "<I", new_cmd)


def node_cases(module, data, size):
    LC = module.LC
    cases = []

    def case(identifier, description, mutated, expected, file_size=None, rules="node"):
        file_size = size if file_size is None else file_size
        try:
            summary = module.parse_macho(mutated, file_size)
            if rules == "node":
                module.check_node_macho(summary)
            elif rules == "python":
                module.check_python_macho(summary)
            outcome = "ACCEPT"
            detail = None
        except module.ObservationError as exc:
            outcome = exc.details.get("rule", exc.code)
            detail = exc.reason
        except Exception as exc:  # an unexpected exception is a finding in itself
            outcome = "EXCEPTION:" + type(exc).__name__
            detail = str(exc)
        cases.append({"id": identifier, "case": description, "expected": expected, "observed": outcome,
                      "detail": detail, "as_expected": outcome == expected})

    dylinker = find(data, LC["LC_LOAD_DYLINKER"])[0]
    libcxx = find(data, LC["LC_LOAD_DYLIB"], 2)[0]
    source_version = find(data, LC["LC_SOURCE_VERSION"])[0]
    uuid = find(data, LC["LC_UUID"])[0]
    segment_data_const = find(data, LC["LC_SEGMENT_64"], 2)[0]
    symtab = find(data, LC["LC_SYMTAB"])[0]
    signature = find(data, LC["LC_CODE_SIGNATURE"])[0]
    main = find(data, LC["LC_MAIN"])[0]
    build = find(data, LC["LC_BUILD_VERSION"])[0]
    dysymtab = find(data, LC["LC_DYSYMTAB"])[0]

    case("N00", "the real header and load commands, unchanged", data, "ACCEPT")
    case("N01", "fat magic 0xcafebabe", b"\xca\xfe\xba\xbe" + data[4:], "MACHO-FAT")
    case("N02", "fat 64 magic 0xcafebabf", b"\xca\xfe\xba\xbf" + data[4:], "MACHO-FAT")
    case("N03", "32-bit magic", b"\xce\xfa\xed\xfe" + data[4:], "MACHO-MAGIC")
    case("N04", "64-bit big-endian magic", b"\xfe\xed\xfa\xcf" + data[4:], "MACHO-MAGIC")
    case("N05", "cputype x86_64", put(data, 4, "<I", 0x01000007), "MACHO-CPU")
    case("N06", "cpusubtype CPU_SUBTYPE_ARM64E (2)", put(data, 8, "<I", 2), "MACHO-CPU")
    case("N07", "cpusubtype ARM64_ALL with the capability bit 0x80000000", put(data, 8, "<I", 0x80000000), "MACHO-CPU")
    case("N08", "cpusubtype arm64e with CPU_SUBTYPE_PTRAUTH_ABI", put(data, 8, "<I", 0x80000002), "MACHO-CPU")
    case("N09", "cpusubtype CPU_SUBTYPE_ARM64_V8 (1)", put(data, 8, "<I", 1), "MACHO-CPU")
    case("N10", "filetype MH_DYLIB for Node", put(data, 12, "<I", 6), "MACHO-FILETYPE")
    case("N11", "ncmds one more than present", put(data, 16, "<I", struct.unpack_from("<I", data, 16)[0] + 1),
         "MACHO-MALFORMED")
    case("N12", "ncmds one fewer than present", put(data, 16, "<I", struct.unpack_from("<I", data, 16)[0] - 1),
         "MACHO-MALFORMED")
    case("N13", "ncmds zero", put(data, 16, "<I", 0), "MACHO-MALFORMED")
    case("N14", "sizeofcmds 8 larger than the commands", put(data, 20, "<I", struct.unpack_from("<I", data, 20)[0] + 8)
         + b"\0" * 8, "MACHO-MALFORMED")
    case("N15", "sizeofcmds beyond the file", data, "MACHO-MALFORMED", file_size=len(data) - 8)
    case("N16", "header shorter than 32 bytes", data[:31], "MACHO-MALFORMED", file_size=31)
    case("N17", "command bytes not all supplied", data[:-16], "MACHO-MALFORMED")
    case("N18", "cmdsize not a multiple of 8 (LC_LOAD_DYLINKER 32 -> 36)", put(data, dylinker + 4, "<I", 36),
         "MACHO-MALFORMED")
    case("N19", "cmdsize 4 (below 8)", put(data, dylinker + 4, "<I", 4), "MACHO-MALFORMED")
    case("N20", "cmdsize 0", put(data, dylinker + 4, "<I", 0), "MACHO-MALFORMED")
    last = command_offsets(data)[-1][0]
    case("N21", "last command's cmdsize escapes sizeofcmds", put(data, last + 4, "<I", 24), "MACHO-MALFORMED")
    case("N22", "LC_LOAD_DYLINKER string offset equal to cmdsize", put(data, dylinker + 8, "<I", 32), "MACHO-MALFORMED")
    case("N23", "LC_LOAD_DYLINKER string offset inside the fixed structure (8)", put(data, dylinker + 8, "<I", 8),
         "MACHO-MALFORMED")
    unterminated = bytearray(data)
    unterminated[dylinker + 12:dylinker + 32] = b"/usr/lib/dyld_______"
    case("N24", "LC_LOAD_DYLINKER string not NUL-terminated inside the command", bytes(unterminated), "MACHO-MALFORMED")
    case("N25", "LC_LOAD_DYLINKER string empty", replace_string(data, LC["LC_LOAD_DYLINKER"], ""), "MACHO-MALFORMED")
    case("N26", "LC_LOAD_DYLINKER string with a non-ASCII byte",
         replace_string(data, LC["LC_LOAD_DYLINKER"], "/usr/lib/dy\xe9d"), "MACHO-MALFORMED")
    case("N27", "LC_LOAD_DYLINKER /usr/lib/dyle", replace_string(data, LC["LC_LOAD_DYLINKER"], "/usr/lib/dyle"),
         "MACHO-DYLINKER")
    case("N28", "LC_LOAD_DYLIB @rpath/libc++.1.dylib",
         replace_string(data, LC["LC_LOAD_DYLIB"], "@rpath/libc++.1.dylib", 2), "MACHO-AT-PATH")
    case("N29", "LC_LOAD_DYLIB @loader_path/libc++.dylib",
         replace_string(data, LC["LC_LOAD_DYLIB"], "@loader_path/c.dylib", 2), "MACHO-AT-PATH")
    case("N30", "LC_LOAD_DYLIB /usr/lib/../lib/c.dylib",
         replace_string(data, LC["LC_LOAD_DYLIB"], "/usr/lib/../lib/c.dyl", 2), "MACHO-DYLIB-PATH")
    case("N31", "LC_LOAD_DYLIB /usr/local/lib/c.dylib",
         replace_string(data, LC["LC_LOAD_DYLIB"], "/usr/local/lib/c.dylib", 2), "MACHO-DYLIB-PATH")
    case("N32", "LC_LOAD_DYLIB //usr/lib/libc++.dylib",
         replace_string(data, LC["LC_LOAD_DYLIB"], "//usr/lib/libc++.dylib", 2), "MACHO-DYLIB-PATH")
    case("N33", "LC_LOAD_DYLIB /usr/lib//libc++.dylib",
         replace_string(data, LC["LC_LOAD_DYLIB"], "/usr/lib//libc++.dylib", 2), "MACHO-DYLIB-PATH")
    case("N34", "LC_LOAD_DYLIB relative leaf name libc++.1.dylib",
         replace_string(data, LC["LC_LOAD_DYLIB"], "libc++.1.dylib", 2), "MACHO-DYLIB-PATH")
    case("N35", "LC_LOAD_DYLIB /USR/LIB/libc++.1.dylib (case differs)",
         replace_string(data, LC["LC_LOAD_DYLIB"], "/USR/LIB/libc++.1.dylib", 2), "MACHO-DYLIB-PATH")
    case("N36", "LC_LOAD_DYLIB cmd with the LC_REQ_DYLD bit (0x8000000c)", put(data, libcxx, "<I", 0x8000000C),
         "MACHO-COMMAND")
    case("N37", "LC_LOAD_WEAK_DYLIB without the LC_REQ_DYLD bit (0x18)", put(data, libcxx, "<I", 0x18), "MACHO-COMMAND")
    case("N38", "LC_LOAD_WEAK_DYLIB (0x80000018) of a system dylib", put(data, libcxx, "<I", 0x80000018), "ACCEPT")
    case("N39", "LC_REEXPORT_DYLIB", put(data, libcxx, "<I", 0x8000001F), "MACHO-REFUSED-COMMAND")
    case("N40", "LC_LOAD_UPWARD_DYLIB", put(data, libcxx, "<I", 0x80000023), "MACHO-REFUSED-COMMAND")
    case("N41", "LC_LAZY_LOAD_DYLIB", put(data, libcxx, "<I", 0x20), "MACHO-COMMAND")
    case("N42", "LC_ID_DYLIB in the executable", put(data, libcxx, "<I", 0xD), "MACHO-COMMAND")
    rpath = put(put(data, source_version, "<II", 0x8000001C, 16), source_version + 8, "<I", 12)
    rpath = put(rpath, source_version + 12, "<4s", b"/a\0\0")
    case("N43", "LC_RPATH /a in place of LC_SOURCE_VERSION", rpath, "MACHO-REFUSED-COMMAND")
    rpath_no_bit = put(rpath, source_version, "<I", 0x1C)
    case("N44", "LC_RPATH without the LC_REQ_DYLD bit (0x1c)", rpath_no_bit, "MACHO-COMMAND")
    environment = put(rpath, source_version, "<I", 0x27)
    case("N45", "LC_DYLD_ENVIRONMENT /a", environment, "MACHO-REFUSED-COMMAND")
    case("N46", "unknown command 0x37", put(data, source_version, "<I", 0x37), "MACHO-COMMAND")
    case("N47", "unknown command 0x80000099 (LC_REQ_DYLD set)", put(data, source_version, "<I", 0x80000099),
         "MACHO-COMMAND")
    case("N48", "LC_VERSION_MIN_MACOSX (known, outside the allow-list)", put(data, source_version, "<I", 0x24),
         "MACHO-COMMAND")
    case("N49", "LC_ENCRYPTION_INFO_64 (known, outside the allow-list)", put(data, uuid, "<I", 0x2C), "MACHO-COMMAND")
    duplicate_main = put(put(data, uuid, "<II", 0x80000028, 24), uuid + 8, "<QQ", 0, 0)
    case("N50", "a second LC_MAIN in place of LC_UUID", duplicate_main, "MACHO-DUPLICATE")
    case("N51", "LC_SEGMENT_64 file range beyond the file", put(data, segment_data_const + 48, "<Q", size),
         "MACHO-MALFORMED")
    case("N52", "LC_SEGMENT_64 nsects disagrees with cmdsize", put(data, segment_data_const + 64, "<I", 0),
         "MACHO-MALFORMED")
    case("N53", "LC_SYMTAB string table beyond the file", put(data, symtab + 16, "<I", size), "MACHO-MALFORMED")
    case("N54", "LC_CODE_SIGNATURE beyond the file", put(data, signature + 8, "<I", size), "MACHO-MALFORMED")
    case("N55", "LC_MAIN entry offset beyond the file", put(data, main + 8, "<Q", size), "MACHO-MALFORMED")
    case("N56", "LC_BUILD_VERSION ntools disagrees with cmdsize", put(data, build + 20, "<I", 2), "MACHO-MALFORMED")
    case("N57", "LC_UUID cmdsize 32 (padding)", put(data, uuid + 4, "<I", 32), "MACHO-MALFORMED")
    # Properties the parser does not decide (the contract does not require them): expected ACCEPT.
    case("N58", "LC_BUILD_VERSION platform IOS (2) [not decided by the parser]", put(data, build + 8, "<I", 2), "ACCEPT")
    case("N59", "header flag MH_FORCE_FLAT [not decided by the parser]",
         put(data, 24, "<I", struct.unpack_from("<I", data, 24)[0] | 0x100), "ACCEPT")
    case("N60", "header flag MH_ALLOW_STACK_EXECUTION [not decided by the parser]",
         put(data, 24, "<I", struct.unpack_from("<I", data, 24)[0] | 0x20000), "ACCEPT")
    case("N61", "__DATA_CONST file range moved to overlap __TEXT [not decided by the parser]",
         put(data, segment_data_const + 40, "<Q", 0), "ACCEPT")
    case("N62", "LC_DYSYMTAB indirect-symbol offset beyond the file [not decided by the parser]",
         put(data, dysymtab + 56, "<I", 0xFFFFFFF0), "ACCEPT")
    case("N63", "LC_SEGMENT_64 section offset beyond the file [not decided by the parser]",
         put(data, find(data, LC["LC_SEGMENT_64"], 1)[0] + 72 + 48, "<I", 0xFFFFFFF0), "ACCEPT")
    return cases


def python_cases(module, data, size, rpath_text):
    """Python-rule mutations on a real lib-dynload bundle with an absolute LC_RPATH."""
    LC = module.LC
    cases = []

    def case(identifier, description, mutated, expected):
        try:
            summary = module.parse_macho(mutated, size)
            module.check_python_macho(summary)
            outcome, detail = "ACCEPT", None
        except module.ObservationError as exc:
            outcome, detail = exc.details.get("rule", exc.code), exc.reason
        except Exception as exc:
            outcome, detail = "EXCEPTION:" + type(exc).__name__, str(exc)
        cases.append({"id": identifier, "case": description, "expected": expected, "observed": outcome,
                      "detail": detail, "as_expected": outcome == expected})

    width = len(rpath_text)
    dylib = find(data, LC["LC_LOAD_DYLIB"])[0]
    case("P00", "the real lib-dynload bundle, unchanged", data, "ACCEPT")
    case("P01", "filetype MH_OBJECT (W3 Q5)", put(data, 12, "<I", 1), "MACHO-FILETYPE")
    case("P02", "filetype MH_DYLIB without LC_ID_DYLIB", put(data, 12, "<I", 6), "MACHO-STRUCTURE")
    case("P03", "filetype MH_EXECUTE without LC_MAIN and LC_LOAD_DYLINKER", put(data, 12, "<I", 2), "MACHO-STRUCTURE")
    case("P04", "LC_RPATH @rpath/...", replace_string(data, LC["LC_RPATH"], ("@rpath/" + "x" * width)[:width]),
         "MACHO-RPATH")
    case("P05", "LC_RPATH @loader_path/../lib", replace_string(data, LC["LC_RPATH"], "@loader_path/../lib"), "ACCEPT")
    case("P06", "LC_RPATH relative directory", replace_string(data, LC["LC_RPATH"], ("relative/" + "y" * width)[:width]),
         "MACHO-RPATH")
    case("P07", "LC_RPATH @executable_pathX (no slash)",
         replace_string(data, LC["LC_RPATH"], "@executable_pathX"), "MACHO-RPATH")
    case("P08", "LC_LOAD_DYLIB @foo/libz.dylib (other @ form)",
         replace_string(data, LC["LC_LOAD_DYLIB"], "@foo/libz.dylib"), "MACHO-AT-PATH")
    case("P09", "LC_LOAD_DYLIB @rpath/ (empty name)", replace_string(data, LC["LC_LOAD_DYLIB"], "@rpath/"),
         "MACHO-AT-PATH")
    case("P10", "LC_LOAD_DYLIB @rpath/libz.dylib (per-file rule; resolution is the closure's)",
         replace_string(data, LC["LC_LOAD_DYLIB"], "@rpath/libz.dylib"), "ACCEPT")
    case("P11", "LC_LOAD_DYLIB relative leaf name", replace_string(data, LC["LC_LOAD_DYLIB"], "libz.1.dylib"),
         "MACHO-DYLIB-PATH")
    case("P12", "LC_REEXPORT_DYLIB", put(data, dylib, "<I", 0x8000001F), "MACHO-COMMAND")
    case("P13", "LC_LOAD_UPWARD_DYLIB", put(data, dylib, "<I", 0x80000023), "MACHO-REFUSED-COMMAND")
    case("P14", "LC_LAZY_LOAD_DYLIB", put(data, dylib, "<I", 0x20), "MACHO-COMMAND")
    environment = put(data, find(data, LC["LC_RPATH"])[0], "<I", 0x27)
    case("P15", "LC_DYLD_ENVIRONMENT in place of LC_RPATH", environment, "MACHO-REFUSED-COMMAND")
    case("P16", "LC_RPATH without the LC_REQ_DYLD bit (0x1c)", put(data, find(data, LC["LC_RPATH"])[0], "<I", 0x1C),
         "MACHO-COMMAND")
    return cases


def main(argv=None):
    parser = argparse.ArgumentParser()
    for name in ("parser", "reader-json", "node", "venv", "framework", "node-source", "output"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--git", default=None)
    parser.add_argument("--label", action="append", default=[])
    args = parser.parse_args(argv)
    labels = sorted(((item.partition("=")[0], item.partition("=")[2]) for item in args.label),
                    key=lambda row: -len(row[1]))
    started = time.time()
    module, added_modules = load_parser(args.parser)
    reader = json.load(open(args.reader_json, encoding="utf-8"))
    unlabel = {name: prefix for name, prefix in labels}

    def real(path):
        for name, prefix in unlabel.items():
            path = path.replace(name, prefix)
        return path

    def unlabelled(value):
        """The reader's record with its labels undone, so that it compares with the parser's real paths."""
        if isinstance(value, str):
            return real(value)
        if isinstance(value, list):
            return [unlabelled(item) for item in value]
        if isinstance(value, dict):
            return {key: unlabelled(item) for key, item in value.items()}
        return value

    out = {"schema": "n34m-compare-raw/1", "parser": {"path": args.parser,
                                                     "sha256": hashlib.sha256(open(args.parser, "rb").read()).hexdigest(),
                                                     "modules_added_by_import": added_modules,
                                                     "contract": module.CONTRACT,
                                                     "design_revision": module.DESIGN_REVISION,
                                                     "amendments": list(module.AMENDMENTS)}}

    # Node: the observer's own call shape in check_runtime.
    source = json.load(open(args.node_source, encoding="utf-8"))
    pin = {key: source["extracted"][key] for key in ("sha256", "size_bytes", "mode")}
    node = attempt(module, module.read_macho, args.node, maximum=pin["size_bytes"], private=True, category="RUNTIME",
                   expected=pin)
    node_out = {"pin_from_node_source": pin}
    if not node["refused"]:
        binding, summary = node["value"]
        node_out["binding"] = binding
        node_out["summary"] = module.macho_summary(summary)
        node_out["check_node_macho"] = attempt(module, module.check_node_macho, summary)
        node_out["check_python_macho_for_contrast"] = attempt(module, module.check_python_macho, summary)
        node_out["differences_from_reader"] = compare_parse(summary, unlabelled(reader["node"]))
        head = open(args.node, "rb").read(32 + summary["sizeofcmds"])
        node_out["mutation_cases"] = node_cases(module, head, binding["size_bytes"])
    else:
        node_out["read_macho"] = node
    out["node"] = node_out

    # Every Python image, one by one, as _closure_pass reads and checks it.
    images = {}
    for labelled, record in sorted(list(reader["python"]["images"].items()) + list(reader["python"]["external"].items())):
        path = real(labelled)
        row = {"tree": record["tree"]}
        result = attempt(module, module.read_macho, path, maximum=module.LIMITS["tree_file_bytes"], category="PYTHON")
        if result["refused"]:
            row["read_macho"] = result
        else:
            binding, summary = result["value"]
            row["binding_matches_reader"] = binding["sha256"] == record["sha256"] and \
                binding["size_bytes"] == record["size_bytes"]
            checked = attempt(module, module.check_python_macho, summary)
            row["check_python_macho"] = ({"refused": False, "rpaths": checked["value"]["rpaths"],
                                          "references": checked["value"]["references"], "id": checked["value"]["id"],
                                          "filetype": checked["value"]["filetype"]}
                                         if not checked["refused"] else checked)
            row["differences_from_reader"] = compare_parse(summary, unlabelled(record))
        images[path] = row
    out["python_images"] = images

    # Python-rule mutations on a real lib-dynload bundle.
    ssl = None
    for path in images:
        if path.endswith("/lib-dynload/_ssl.cpython-312-darwin.so"):
            ssl = path
    if ssl:
        binding, summary = module.read_macho(ssl, maximum=module.LIMITS["tree_file_bytes"], category="PYTHON")
        head = open(ssl, "rb").read(32 + summary["sizeofcmds"])
        rpath_text = [row["path"] for row in summary["commands"] if row["name"] == "LC_RPATH"][0]
        out["python_mutation_base"] = ssl
        out["python_mutation_cases"] = python_cases(module, head, binding["size_bytes"], rpath_text)

    # The observer's interpreter checks for this very process (-I -S -B under the venv).
    state = attempt(module, module.launcher_state)
    out["launcher_state"] = state
    if not state["refused"]:
        out["check_launcher"] = attempt(module, module.check_launcher, state["value"], args.venv, args.framework,
                                        "%d.%d.%d" % sys.version_info[:3])

    # The complete installation-tree inventory, twice, and the package verification.
    first = attempt(module, module.python_inventory, args.venv, args.framework)
    if first["refused"]:
        out["python_inventory"] = first
    else:
        inventory = first["value"]
        second = module.python_inventory(args.venv, args.framework)
        closure = inventory["closure"]
        out["python_inventory"] = {
            "refused": False, "digest": module.python_inventory_digest(inventory),
            "canonical_bytes": len(module._canonical(inventory)),
            "second_computation_differences": module.compare_inventory(inventory, second),
            "second_digest": module.python_inventory_digest(second),
            "framework_entries": len(inventory["framework"]["entries"]),
            "venv_entries": len(inventory["venv"]["entries"]),
            "kinds": {tree: {kind: sum(1 for entry in inventory[tree]["entries"].values() if entry["kind"] == kind)
                             for kind in ("file", "symlink", "directory")} for tree in ("framework", "venv")},
            "selection": inventory["selection"], "closure_images": len(closure["images"]),
            "closure_external": sorted(closure["external"]), "closure_links": closure["links"],
            "closure": closure}
        # Independent cross-check of the tree selection: paths, kinds, link targets and every file's SHA-256.
        cross = {}
        for tree, root in (("framework", args.framework), ("venv", args.venv)):
            entries = inventory[tree]["entries"]
            files = [real(path) for path in reader["python"]["file_lists"][tree]]
            directories = [real(path) for path in reader["python"]["directory_lists"][tree]]
            links = {real(row["path"]): row["target"] for row in reader["python"]["trees"][tree]["links"]}
            mine = {}
            for path in files:
                digest = hashlib.sha256(open(path, "rb").read()).hexdigest()
                mine[path[len(root) + 1:]] = ("file", digest, os.path.getsize(path))
            for path in directories:
                mine[path[len(root) + 1:]] = ("directory",)
            for path, target in links.items():
                mine[path[len(root) + 1:]] = ("symlink", real(target) if target.startswith("<") else target)
            theirs = {}
            for rel, entry in entries.items():
                if entry["kind"] == "file":
                    theirs[rel] = ("file", entry["sha256"], entry["size_bytes"])
                elif entry["kind"] == "directory":
                    theirs[rel] = ("directory",)
                else:
                    theirs[rel] = ("symlink", entry["target"])
            cross[tree] = {"reader_entries": len(mine), "parser_entries": len(theirs),
                           "only_reader": sorted(set(mine) - set(theirs))[:50],
                           "only_parser": sorted(set(theirs) - set(mine))[:50],
                           "differing": sorted(rel for rel in set(mine) & set(theirs) if mine[rel] != theirs[rel])[:50]}
        reader_images = {real(path) for path in reader["python"]["images"]}
        reader_external = {real(path) for path in reader["python"]["external"]}
        cross["closure_images_equal_reader_images_plus_external"] = \
            set(closure["images"]) == reader_images | reader_external
        cross["closure_external_equal_reader_external"] = set(closure["external"]) == reader_external
        out["inventory_cross_check"] = cross
        packages = attempt(module, module.verify_packages, args.venv, inventory["venv"]["entries"],
                           dict(module.PYTHON_PINS), inventory["selection"]["version_directory"])
        out["verify_packages"] = packages

    # OS identity for the labels of the closure claim, through the observer's own reader.
    out["os_identity"] = attempt(module, module.read_os_identity)

    # W3's F3: the parser's classification of the developer tools' Git (never parsed by M0).
    if args.git:
        out["git_magic_kind"] = module.macho_magic_kind(open(args.git, "rb").read(4))
        out["git_parse_macho"] = attempt(module, module._macho_extent, open(args.git, "rb").read(4096),
                                         os.path.getsize(args.git))
    out["elapsed_s"] = round(time.time() - started, 3)
    text = json.dumps(apply_labels(out, labels), indent=1, sort_keys=True, default=str) + "\n"
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(text)
    print(json.dumps({"output": apply_labels(args.output, labels), "bytes": len(text), "elapsed_s": out["elapsed_s"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
