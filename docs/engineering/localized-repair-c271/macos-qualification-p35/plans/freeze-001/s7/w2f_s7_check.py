#!/usr/bin/env python3
"""Operational freeze 001 of gate MH (C271-P35): the Director's checker for stage S7.

It reads the freeze (bound by a SHA-256 given as an argument) and the files the freeze names, and
prints one JSON record on stdout. It starts nothing (an audit hook refuses every process creation),
imports nothing of the project, writes no file, and refuses a start without -B.

Launch: env -i <declared environment> <worktree>/.venv/bin/python -I -S -B w2f_s7_check.py \
            --freeze FREEZE-001.json --freeze-sha256 H PHASE [--command ID]

PHASE:
  pre       every binding and host fact, the boot, the evidence ancestors, the umask, no bytecode or
            .DS_Store in the named roots, and every S7 path absent (before the preparation)
  prepared  the same bindings, the boot and the umask, every prepared entry exactly as frozen, and every
            path that the preparation leaves absent still absent
  expect    one command's frozen predicates (--command ID), read from its records
  post      the bindings of the inputs, the boot, no bytecode, and every prepared input file unchanged
            (the one consumed copy excepted, as frozen)

Exit: 0 when every check holds; 1 when a check fails; 2 for a refusal (usage, freeze digest, -B).
"""
import argparse
import ctypes
import hashlib
import json
import os
import stat
import sys

PROCESS_EVENTS = {"subprocess.Popen", "os.posix_spawn", "os.exec", "os.fork", "os.forkpty", "os.spawn", "os.system",
                  "os.startfile"}
LIBSYSTEM = "/usr/lib/libSystem.B.dylib"


def refuse_processes(event, args):
    if event in PROCESS_EVENTS:
        raise PermissionError("the S7 checker starts no process: " + event)


def sha256_file(path):
    digest = hashlib.sha256()
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        while True:
            block = os.read(fd, 1 << 20)
            if not block:
                break
            digest.update(block)
    finally:
        os.close(fd)
    return digest.hexdigest()


def mode_text(st_mode):
    return "0o%03o" % stat.S_IMODE(st_mode)


def spelled_on_disk(path):
    current = "/"
    for part in [p for p in path.split("/") if p]:
        try:
            if part not in os.listdir(current):
                return False
        except OSError:
            return False
        current = os.path.join(current, part)
    return True


def boot_session_uuid():
    function = ctypes.CDLL(LIBSYSTEM, use_errno=True).sysctlbyname
    function.argtypes = (ctypes.c_char_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t), ctypes.c_void_p,
                         ctypes.c_size_t)
    function.restype = ctypes.c_int
    buffer = ctypes.create_string_buffer(128)
    size = ctypes.c_size_t(ctypes.sizeof(buffer))
    if function(b"kern.bootsessionuuid", buffer, ctypes.byref(size), None, 0) != 0:
        return None
    return buffer.value.decode("ascii", "replace")


def check_file(row):
    """A bound regular file: kind, digest, size, mode, one link, canonical and spelled as on disk."""
    path = row["path"]
    result = {"id": row["id"], "path": path}
    try:
        info = os.lstat(path)
    except OSError as exc:
        result.update(ok=False, reason="absent or unreadable: " + str(exc))
        return result
    observed = {"kind": "file" if stat.S_ISREG(info.st_mode) else "directory" if stat.S_ISDIR(info.st_mode)
                else "symlink" if stat.S_ISLNK(info.st_mode) else "special", "mode": mode_text(info.st_mode)}
    problems = []
    if os.path.realpath(path) != path or os.path.normpath(path) != path:
        problems.append("not canonical")
    if not spelled_on_disk(path):
        problems.append("a component is not spelled as on disk")
    if observed["kind"] != row["kind"]:
        problems.append("kind " + observed["kind"])
    elif row["kind"] == "file":
        observed.update(sha256=sha256_file(path), size_bytes=info.st_size, nlink=info.st_nlink)
        for key in ("sha256", "size_bytes", "mode"):
            if observed[key] != row[key]:
                problems.append(key + " differs")
        if row.get("nlink_one") and info.st_nlink != 1:
            problems.append("more than one link")
    elif row["kind"] == "directory":
        if observed["mode"] != row["mode"]:
            problems.append("mode differs")
        if "entries" in row and sorted(os.listdir(path)) != sorted(row["entries"]):
            problems.append("entries differ: " + json.dumps(sorted(os.listdir(path))))
    result.update(ok=not problems, problems=problems, observed=observed)
    return result


def check_absent(paths):
    present = [path for path in paths if os.path.lexists(path)]
    return {"ok": not present, "checked": len(paths), "present": present}


def check_ancestors(evidence):
    rows = []
    current = evidence["parent"]
    while True:
        info = os.lstat(current)
        rows.append({"path": current, "device": info.st_dev, "inode": info.st_ino, "mode": mode_text(info.st_mode)})
        if current == "/":
            break
        current = os.path.dirname(current)
    rows.sort(key=lambda row: row["path"])
    return {"ok": rows == evidence["ancestors"], "observed": rows}


def check_trees(spec):
    """No bytecode in the roots named (their excluded subtrees left out), and no .DS_Store."""
    found = []
    for row in spec:
        root, excluded = row["root"], set(row.get("exclude", []))
        for parent, directories, names in os.walk(root, followlinks=False):
            directories[:] = [d for d in directories if os.path.join(parent, d) not in excluded]
            for name in directories + names:
                full = os.path.join(parent, name)
                if row.get("bytecode") and (name == "__pycache__" or name.endswith((".pyc", ".pyo"))):
                    found.append(full)
                if name == ".DS_Store":
                    found.append(full)
    return {"ok": not found, "found": found[:50], "roots": [row["root"] for row in spec]}


def pointer(document, text):
    current = document
    if text == "":
        return True, current
    for token in text[1:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict):
            if token not in current:
                return False, None
            current = current[token]
        elif isinstance(current, list):
            if not token.isdigit() or int(token) >= len(current):
                return False, None
            current = current[int(token)]
        else:
            return False, None
    return True, current


def same(first, second):
    if type(first) is bool or type(second) is bool:
        return type(first) is type(second) and first == second
    if type(first) in (int, float) and type(second) in (int, float):
        return first == second
    if isinstance(first, list) and isinstance(second, list):
        return len(first) == len(second) and all(same(a, b) for a, b in zip(first, second))
    if isinstance(first, dict) and isinstance(second, dict):
        return set(first) == set(second) and all(same(first[k], second[k]) for k in first)
    return type(first) is type(second) and first == second


CONTEXT = {"freeze_sha256": None}


def member_predicate(value, rule):
    """One predicate on one JSON value: equals, absent (handled by caller), length, each, count_where, and the
    deferred-argument forms argv_equals_except, equals_freeze_sha256, equals_sha256_of and equals_from."""
    if "argv_equals_except" in rule:
        expected, skipped = rule["argv_equals_except"]["argv"], set(rule["argv_equals_except"]["indices"])
        return (isinstance(value, list) and len(value) == len(expected)
                and all(same(a, b) for index, (a, b) in enumerate(zip(value, expected)) if index not in skipped))
    if rule.get("equals_freeze_sha256"):
        return value == CONTEXT["freeze_sha256"]
    if "equals_sha256_of" in rule:
        return os.path.isfile(rule["equals_sha256_of"]) and value == sha256_file(rule["equals_sha256_of"])
    if "equals_from" in rule:
        source = rule["equals_from"]
        if not os.path.isfile(source["file"]):
            return False
        with open(source["file"], "rb") as stream:
            found, other = pointer(json.loads(stream.read()), source["pointer"])
        return found and same(value, other)
    if rule.get("nonempty_string"):
        return isinstance(value, str) and value.strip() != ""
    if "equals" in rule and "count_where" not in rule and "length" not in rule:
        return same(value, rule["equals"])
    if "length" in rule:
        return isinstance(value, (list, dict, str)) and len(value) == rule["length"]
    if "each" in rule:
        if not isinstance(value, list):
            return False
        return all(evaluate_on(item, rule["each"]) for item in value)
    if "count_where" in rule:
        if not isinstance(value, list):
            return False
        count = sum(1 for item in value if evaluate_on(item, rule["count_where"]))
        return count == rule["equals"]
    if "one_of" in rule:
        return any(same(value, option) for option in rule["one_of"])
    if "startswith" in rule:
        return isinstance(value, str) and value.startswith(rule["startswith"])
    if "includes" in rule:
        return isinstance(value, str) and rule["includes"] in value
    return False


def evaluate_on(document, rule):
    found, value = pointer(document, rule.get("pointer", ""))
    if rule.get("absent"):
        return not found
    return found and member_predicate(value, rule)


def check_predicate(rule, cache):
    path = rule["file"]
    result = {"rule": rule}
    if "exists" in rule:
        result["ok"] = os.path.lexists(path) == rule["exists"]
        return result
    if not os.path.isfile(path):
        result.update(ok=False, reason="the file is absent")
        return result
    if "sha256" in rule:
        result["observed"] = sha256_file(path)
        result["ok"] = result["observed"] == rule["sha256"]
        return result
    if "text_equals" in rule or "text_includes" in rule or "text_excludes" in rule:
        with open(path, "rb") as stream:
            text = stream.read().decode("utf-8", "replace")
        if "text_equals" in rule:
            result["ok"] = text == rule["text_equals"]
        elif "text_includes" in rule:
            result["ok"] = rule["text_includes"] in text
        else:
            result["ok"] = rule["text_excludes"] not in text
        return result
    if path not in cache:
        with open(path, "rb") as stream:
            raw = stream.read()
        if rule.get("jsonl_last"):
            lines = [line for line in raw.decode("utf-8").splitlines() if line.strip()]
            cache[path] = json.loads(lines[-1]) if lines else None
        else:
            cache[path] = json.loads(raw)
    result["ok"] = evaluate_on(cache[path], rule)
    found, value = pointer(cache[path], rule.get("pointer", ""))
    if found and not isinstance(value, (dict, list)):
        result["observed"] = value
    elif found:
        result["observed_length"] = len(value)
    return result


def main():
    sys.addaudithook(refuse_processes)
    parser = argparse.ArgumentParser(prog="w2f_s7_check.py")
    parser.add_argument("--freeze", required=True)
    parser.add_argument("--freeze-sha256", required=True)
    parser.add_argument("phase", choices=("pre", "prepared", "expect", "post"))
    parser.add_argument("--command")
    parser.add_argument("--audit", action="store_true",
                        help="with expect: the command's recorded expectations for the audit (S8), not its stop rule")
    args = parser.parse_args()
    report = {"schema": "ontokin.c271.p35-s7-check/1", "phase": args.phase, "command": args.command,
              "python_flags": {"dont_write_bytecode": sys.flags.dont_write_bytecode, "isolated": sys.flags.isolated,
                               "no_site": sys.flags.no_site}}
    if not (sys.flags.dont_write_bytecode and sys.flags.isolated and sys.flags.no_site):
        report.update(state="REFUSED", reason="run with -I -S -B")
        print(json.dumps(report, sort_keys=True))
        return 2
    if sha256_file(args.freeze) != args.freeze_sha256:
        report.update(state="REFUSED", reason="the freeze differs from its supplied SHA-256")
        print(json.dumps(report, sort_keys=True))
        return 2
    with open(args.freeze, "rb") as stream:
        freeze = json.loads(stream.read())
    CONTEXT["freeze_sha256"] = args.freeze_sha256
    checks = {}
    if args.phase in ("pre", "prepared", "post"):
        checks["boot"] = {"ok": boot_session_uuid() == freeze["boot_session_uuid"], "observed": boot_session_uuid()}
        mask = os.umask(0o022)
        os.umask(mask)
        checks["umask"] = {"ok": "0o%03o" % mask == freeze["umask"], "observed": "0o%03o" % mask}
        rows = freeze["bindings"] if args.phase != "post" else [row for row in freeze["bindings"]
                                                                  if row["id"] not in freeze["post"]["not_rechecked"]]
        checks["bindings"] = [check_file(row) for row in rows]
        checks["trees"] = check_trees(freeze["trees"])
    if args.phase == "pre":
        checks["host_facts"] = [check_file(row) for row in freeze["host_facts"]]
        checks["ancestors"] = check_ancestors(freeze["evidence"])
        checks["absent"] = check_absent(freeze["absent_paths"]["before_preparation"])
        deferred = []
        for row in freeze["deferred_inputs"]:
            item = {"id": row["id"], "path": row["path"]}
            if not os.path.isfile(row["path"]) or os.path.islink(row["path"]):
                item.update(ok=False, reason="absent, or not a regular file")
            else:
                info = os.lstat(row["path"])
                item.update(sha256=sha256_file(row["path"]), size_bytes=info.st_size, mode=mode_text(info.st_mode))
                with open(row["path"], "rb") as stream:
                    document = json.loads(stream.read())
                item["requirements"] = [dict(rule, ok=evaluate_on(document, rule)) for rule in row["requirements"]]
                item["ok"] = all(rule["ok"] for rule in item["requirements"])
            deferred.append(item)
        checks["deferred_inputs"] = deferred
    elif args.phase == "prepared":
        checks["host_facts"] = [check_file(row) for row in freeze["host_facts"]]
        checks["ancestors"] = check_ancestors(freeze["evidence"])
        checks["prepared"] = [check_file(row) for row in freeze["preparation"]["entries"]]
        checks["absent"] = check_absent(freeze["absent_paths"]["after_preparation"])
        cache = {}
        checks["earlier_commands"] = [dict(check_predicate(rule, cache), command=row["id"]) for row in freeze["commands"]
                                      if row["phase"] in ("precondition", "preparation") and row["id"] != "D02"
                                      for rule in row["expect"]]
    elif args.phase == "post":
        checks["host_facts"] = [check_file(row) for row in freeze["host_facts"]]
        checks["prepared_inputs"] = [check_file(row) for row in freeze["preparation"]["entries"]
                                     if row["kind"] == "file" and row["id"] not in freeze["post"]["consumed"]]
        cache = {}
        checks["earlier_commands"] = [dict(check_predicate(rule, cache), command=row["id"]) for row in freeze["commands"]
                                      if row["phase"] == "post" and row["id"] != "Q04" for rule in row["expect"]]
    elif args.phase == "expect":
        commands = {row["id"]: row for row in freeze["commands"]}
        if args.command not in commands:
            report.update(state="REFUSED", reason="unknown command id")
            print(json.dumps(report, sort_keys=True))
            return 2
        cache = {}
        rules = commands[args.command]["audit_expect" if args.audit else "expect"]
        report["predicate_set"] = "audit_expect" if args.audit else "expect"
        checks["predicates"] = [check_predicate(rule, cache) for rule in rules]
    failed = []
    for name, value in checks.items():
        items = value if isinstance(value, list) else [value]
        for item in items:
            if not item.get("ok"):
                failed.append({"check": name, "item": item})
    report.update(checks=checks, failed=failed, state="MET" if not failed else "NOT_MET")
    print(json.dumps(report, sort_keys=True, indent=1))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
