"""W3 freeze review 001, script 10: the S7 checker (s7/w2f_s7_check.py, unchanged, loaded from its bound bytes) on
synthetic freezes inside OUT, in this one process.

Each case builds a synthetic world under OUT/checker-test/, writes a synthetic freeze, and calls the checker's own
main() with its own argv, capturing stdout and the return code. The checker installs its audit hook in this process,
so any process creation here would be refused. Every predicate kind is exercised in both directions, plus the phases,
a wrong freeze digest, an unknown command, the vacuous 'each', type strictness, rule-key precedence and a malformed
record. Writes only under OUT/checker-test/ and one record in OUT/records.
"""
import contextlib
import ctypes
import hashlib
import importlib.util
import io
import json
import os
import stat
import sys

OUT = sys.argv[1]
CHECKER = sys.argv[2]
EXPECTED_CHECKER_SHA = sys.argv[3]
BASE = os.path.join(OUT, "checker-test")
os.mkdir(BASE, 0o755)
with open(CHECKER, "rb") as f:
    raw_checker = f.read()
assert hashlib.sha256(raw_checker).hexdigest() == EXPECTED_CHECKER_SHA, "checker bytes differ from the binding"
spec = importlib.util.spec_from_loader("w2f_s7_check_under_test", loader=None)
checker = importlib.util.module_from_spec(spec)
checker.__file__ = CHECKER
exec(compile(raw_checker, CHECKER, "exec"), checker.__dict__)


def boot():
    fn = ctypes.CDLL("/usr/lib/libSystem.B.dylib", use_errno=True).sysctlbyname
    fn.argtypes = (ctypes.c_char_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t), ctypes.c_void_p, ctypes.c_size_t)
    buf = ctypes.create_string_buffer(128)
    size = ctypes.c_size_t(128)
    assert fn(b"kern.bootsessionuuid", buf, ctypes.byref(size), None, 0) == 0
    return buf.value.decode()


BOOT = boot()
mask = os.umask(0o022)
os.umask(mask)
UMASK = "0o%03o" % mask


def write(path, data, mode=0o644):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data if isinstance(data, bytes) else data.encode())
    os.chmod(path, mode)
    return path


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def binding(path, ident):
    st = os.lstat(path)
    return {"id": ident, "kind": "file", "path": path, "sha256": sha(path), "size_bytes": st.st_size,
            "mode": "0o%03o" % stat.S_IMODE(st.st_mode), "nlink_one": True, "role": "synthetic"}


def ancestors(parent):
    rows, cur = [], parent
    while True:
        st = os.lstat(cur)
        rows.append({"path": cur, "device": st.st_dev, "inode": st.st_ino, "mode": "0o%03o" % stat.S_IMODE(st.st_mode)})
        if cur == "/":
            break
        cur = os.path.dirname(cur)
    return sorted(rows, key=lambda r: r["path"])


def run(case, freeze_doc, phase, command=None, audit=False, digest=None, extra_argv=None):
    path = os.path.join(BASE, "freeze-" + case + ".json")
    write(path, json.dumps(freeze_doc, indent=1, sort_keys=True))
    argv = ["w2f_s7_check.py", "--freeze", path, "--freeze-sha256", digest or sha(path), phase]
    if command:
        argv += ["--command", command]
    if audit:
        argv.append("--audit")
    argv += extra_argv or []
    old = sys.argv
    sys.argv = argv
    buf = io.StringIO()
    error = None
    try:
        with contextlib.redirect_stdout(buf):
            code = checker.main()
    except SystemExit as exc:
        code = exc.code
    except BaseException as exc:
        code, error = "EXCEPTION", type(exc).__name__ + ": " + str(exc)
    finally:
        sys.argv = old
    out = buf.getvalue()
    try:
        report = json.loads(out) if out.strip() else None
    except ValueError:
        report = None
    return {"case": case, "code": code, "state": (report or {}).get("state"), "error": error,
            "failed": [f["check"] for f in (report or {}).get("failed", [])], "report": report}


# The synthetic world
world = os.path.join(BASE, "world")
evidence = os.path.join(world, "evidence")
os.makedirs(evidence)
tree = os.path.join(world, "tree")
os.makedirs(os.path.join(tree, "excluded", "__pycache__"))
write(os.path.join(tree, "a.py"), "x = 1\n")
b1 = write(os.path.join(world, "bound", "one.txt"), "one\n")
b2 = write(os.path.join(world, "bound", "two.json"), '{"k": 1}\n')
fact = write(os.path.join(world, "fact.txt"), "fact", 0o400)
rec = os.path.join(evidence, "s7-x-c01")
cmdjson = write(rec + ".command.json", json.dumps({
    "argv": ["/usr/bin/env", "-i", "A=1", "/tool", "--digest", "<D>"], "cwd": evidence,
    "environment": {"sha256": "e" * 64}, "boot": {"before": BOOT, "after": BOOT}, "retries": 0}))
write(rec + ".exit.txt", "0\n")
write(rec + ".stdout.txt", 'line\n"state": "MET"\n')
write(rec + ".stderr.txt", "")
outjson = write(os.path.join(evidence, "s7-x-out.json"), json.dumps({
    "state": "EXPECTED", "flag": True, "one": 1, "onef": 1.0, "nothing": None, "list": [{"s": "absent"}, {"s": "absent"}],
    "empty": [], "events": [{"argv": ["/n"]}, {"argv": ["/g"]}, {"argv": ["/n"]}], "text": "prefix-middle-suffix",
    "paths": {"/a/b.json": {"sha256": "f" * 64}}, "obj": {"x": 1}}))
readback = write(os.path.join(evidence, "s7-x-readback.json"), json.dumps({"paths": {"/a/b.json": {"sha256": "f" * 64}}}))
listfile = write(os.path.join(world, "reviewed.json"), json.dumps({"schema": "S", "status": "REVIEWED", "reviewer": "me"}))
prep_dir = os.path.join(evidence, "s7-x-prep")
os.mkdir(prep_dir, 0o700)
prep_file = write(os.path.join(prep_dir, "copy.json"), "{}\n")


def P(rule, **kw):
    r = dict(rule)
    r.update(kw)
    return r


def base_freeze():
    return {
        "boot_session_uuid": BOOT, "umask": UMASK, "bindings": [binding(b1, "b1"), binding(b2, "b2")],
        "host_facts": [binding(fact, "fact")], "evidence": {"parent": evidence, "ancestors": ancestors(evidence)},
        "trees": [{"root": tree, "exclude": [os.path.join(tree, "excluded")], "bytecode": True}],
        "absent_paths": {"before_preparation": [os.path.join(evidence, "s7-x-absent")],
                         "after_preparation": [os.path.join(evidence, "s7-x-absent")]},
        "deferred_inputs": [{"id": "list", "path": listfile, "requirements": [
            {"pointer": "/schema", "equals": "S"}, {"pointer": "/status", "equals": "REVIEWED"},
            {"pointer": "/reviewer", "nonempty_string": True}]}],
        "preparation": {"entries": [
            {"id": "prepared:dir", "kind": "directory", "mode": "0o700", "path": prep_dir, "entries": ["copy.json"]},
            dict(binding(prep_file, "prepared:file"), copied_from=b2)]},
        "post": {"commands": ["Q1"], "not_rechecked": [], "consumed": []},
        "commands": []}


def command(ident, phase, rules, audit_rules=None):
    return {"id": ident, "phase": phase, "expect": rules, "audit_expect": audit_rules or []}


results = []
F = rec + ".command.json"
O = outjson
true_rules = [
    {"file": F, "pointer": "/argv", "argv_equals_except": {"argv": ["/usr/bin/env", "-i", "A=1", "/tool", "--digest", "IGNORED"], "indices": [5]}},
    {"file": F, "pointer": "/cwd", "equals": evidence},
    {"file": F, "pointer": "/retries", "equals": 0},
    {"file": rec + ".exit.txt", "text_equals": "0\n"},
    {"file": rec + ".stdout.txt", "text_includes": '"state": "MET"'},
    {"file": rec + ".stderr.txt", "text_excludes": "Traceback"},
    {"file": O, "pointer": "/flag", "equals": True},
    {"file": O, "pointer": "/one", "equals": 1.0},
    {"file": O, "pointer": "/nothing", "equals": None},
    {"file": O, "pointer": "/list", "length": 2},
    {"file": O, "pointer": "/obj", "length": 1},
    {"file": O, "pointer": "/text", "length": 20},
    {"file": O, "pointer": "/list", "each": {"pointer": "/s", "equals": "absent"}},
    {"file": O, "pointer": "/events", "count_where": {"pointer": "/argv/0", "equals": "/n"}, "equals": 2},
    {"file": O, "pointer": "/state", "one_of": ["EXPECTED", "OTHER"]},
    {"file": O, "pointer": "/text", "startswith": "prefix"},
    {"file": O, "pointer": "/text", "includes": "middle"},
    {"file": O, "pointer": "/missing", "absent": True},
    {"file": os.path.join(evidence, "s7-x-absent"), "exists": False},
    {"file": O, "exists": True},
    {"file": b1, "sha256": sha(b1)},
    {"file": F, "pointer": "/argv/5", "equals_sha256_of": None},  # patched below
    {"file": O, "pointer": "/paths/~1a~1b.json/sha256", "equals_from": {"file": readback, "pointer": "/paths/~1a~1b.json/sha256"}},
    {"file": F, "pointer": "/environment/sha256", "nonempty_string": True},
]
# equals_sha256_of: make a record whose argv/5 is a file digest
write(rec + "2.command.json", json.dumps({"argv": ["a", "b", "c", "d", "e", sha(listfile)]}))
true_rules[21] = {"file": rec + "2.command.json", "pointer": "/argv/5", "equals_sha256_of": listfile}
false_rules = [
    {"file": F, "pointer": "/argv", "argv_equals_except": {"argv": ["/usr/bin/env", "-i", "A=2", "/tool", "--digest", "X"], "indices": [5]}},
    {"file": F, "pointer": "/argv", "argv_equals_except": {"argv": ["/usr/bin/env"], "indices": []}},
    {"file": F, "pointer": "/retries", "equals": False},
    {"file": O, "pointer": "/flag", "equals": 1},
    {"file": O, "pointer": "/missing", "equals": None},
    {"file": rec + ".exit.txt", "text_equals": "0"},
    {"file": rec + ".stdout.txt", "text_includes": "NOT_PRESENT"},
    {"file": rec + ".stdout.txt", "text_excludes": "MET"},
    {"file": O, "pointer": "/list", "length": 3},
    {"file": O, "pointer": "/events", "each": {"pointer": "/argv/0", "equals": "/n"}},
    {"file": O, "pointer": "/events", "count_where": {"pointer": "/argv/0", "equals": "/n"}, "equals": 3},
    {"file": O, "pointer": "/state", "one_of": ["OTHER"]},
    {"file": O, "pointer": "/text", "startswith": "suffix"},
    {"file": O, "pointer": "/text", "includes": "absentword"},
    {"file": O, "pointer": "/state", "absent": True},
    {"file": O, "exists": False},
    {"file": b1, "sha256": "0" * 64},
    {"file": rec + "2.command.json", "pointer": "/argv/5", "equals_sha256_of": b1},
    {"file": O, "pointer": "/paths/~1a~1b.json/sha256", "equals_from": {"file": readback, "pointer": "/paths/missing"}},
    {"file": O, "pointer": "/nothing", "nonempty_string": True},
    {"file": os.path.join(evidence, "absent.json"), "pointer": "/x", "equals": 1},
    {"file": O, "pointer": "/state", "unknown_kind": "EXPECTED"},
    {"file": F, "pointer": "/argv/5", "equals_freeze_sha256": True},
]
# 1. every true rule alone is MET, every false rule alone is NOT_MET
for i, rule in enumerate(true_rules):
    fz = base_freeze()
    fz["commands"] = [command("C1", "s7", [rule])]
    r = run("true-%02d" % i, fz, "expect", "C1")
    results.append({"case": "true-%02d" % i, "rule_keys": sorted(rule), "expected": "MET", "state": r["state"], "code": r["code"], "error": r["error"]})
for i, rule in enumerate(false_rules):
    fz = base_freeze()
    fz["commands"] = [command("C1", "s7", [rule])]
    r = run("false-%02d" % i, fz, "expect", "C1")
    results.append({"case": "false-%02d" % i, "rule_keys": sorted(rule), "expected": "NOT_MET", "state": r["state"], "code": r["code"], "error": r["error"]})
# 2. equals_freeze_sha256 true: the argv element equals the digest given to the checker
fz = base_freeze()
path = os.path.join(BASE, "freeze-efs.json")
fz["commands"] = [command("C1", "s7", [{"file": rec + "3.command.json", "pointer": "/argv/0", "equals_freeze_sha256": True}])]
data = json.dumps(fz, indent=1, sort_keys=True)
write(path, data)
write(rec + "3.command.json", json.dumps({"argv": [sha(path)]}))
old = sys.argv
sys.argv = ["w2f_s7_check.py", "--freeze", path, "--freeze-sha256", sha(path), "expect", "--command", "C1"]
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    code = checker.main()
sys.argv = old
results.append({"case": "equals_freeze_sha256-true", "expected": "MET", "state": json.loads(buf.getvalue())["state"], "code": code})
# 3. special cases
special = []
fz = base_freeze()
fz["commands"] = [command("C1", "s7", [])]
special.append(("empty expect list is MET (vacuous)", run("empty", fz, "expect", "C1")))
fz["commands"] = [command("C1", "s7", [{"file": O, "pointer": "/empty", "each": {"pointer": "/s", "equals": "absent"}}])]
special.append(("each on an empty list is MET (vacuous)", run("each-empty", fz, "expect", "C1")))
fz["commands"] = [command("C1", "s7", [{"file": rec + ".stdout.txt", "text_includes": '"state": "MET"', "text_excludes": "line"}])]
special.append(("text_includes and text_excludes in one rule: only text_includes is evaluated", run("text-both", fz, "expect", "C1")))
fz["commands"] = [command("C1", "s7", [{"file": O, "pointer": "/list", "length": 2, "each": {"pointer": "/s", "equals": "WRONG"}}])]
special.append(("length and each in one rule: only length is evaluated", run("length-each", fz, "expect", "C1")))
bad = write(os.path.join(evidence, "s7-x-bad.json"), "{not json")
fz["commands"] = [command("C1", "s7", [{"file": bad, "pointer": "/x", "equals": 1}])]
special.append(("a malformed JSON record", run("bad-json", fz, "expect", "C1")))
fz["commands"] = [command("C1", "s7", [{"file": O, "pointer": "/state", "equals": "EXPECTED"}])]
special.append(("unknown command id", run("unknown", fz, "expect", "C9")))
special.append(("wrong freeze digest", run("digest", fz, "expect", "C1", digest="0" * 64)))
special.append(("audit set", run("audit", dict(fz, commands=[command("C1", "s7", [], [{"file": O, "pointer": "/state", "equals": "X"}])]), "expect", "C1", audit=True)))
# 4. the phases
fz = base_freeze()
fz["commands"] = [command("P1", "precondition", [{"file": O, "pointer": "/state", "equals": "EXPECTED"}]),
                  command("D2", "preparation", []), command("Q1", "post", [{"file": O, "pointer": "/flag", "equals": True}]),
                  command("Q04", "post", [])]
special.append(("pre: all met", run("pre-ok", fz, "pre")))
special.append(("prepared: all met", run("prepared-ok", fz, "prepared")))
special.append(("post: all met", run("post-ok", fz, "post")))
fz2 = json.loads(json.dumps(fz))
fz2["bindings"][0]["sha256"] = "0" * 64
special.append(("pre: a binding digest differs", run("pre-digest", fz2, "pre")))
fz2 = json.loads(json.dumps(fz))
fz2["bindings"][0]["mode"] = "0o600"
special.append(("pre: a binding mode differs", run("pre-mode", fz2, "pre")))
hard = os.path.join(world, "bound", "hard.txt")
os.link(b1, hard)
special.append(("pre: a bound file with two links", run("pre-nlink", fz, "pre")))
os.unlink(hard)
fz2 = json.loads(json.dumps(fz))
fz2["bindings"][0]["path"] = b1.replace("bound", "BOUND")
special.append(("pre: a bound path spelled in another case", run("pre-case", fz2, "pre")))
os.symlink(os.path.join(world, "bound"), os.path.join(world, "linked"))
fz2 = json.loads(json.dumps(fz))
fz2["bindings"][0]["path"] = b1.replace("/bound/", "/linked/")
special.append(("pre: a bound path through a symlink", run("pre-link", fz2, "pre")))
write(os.path.join(tree, ".DS_Store"), "x")
special.append(("pre: a .DS_Store in a tree", run("pre-dsstore", fz, "pre")))
os.unlink(os.path.join(tree, ".DS_Store"))
os.mkdir(os.path.join(tree, "__pycache__"))
special.append(("pre: bytecode directory outside the excluded subtree", run("pre-pycache", fz, "pre")))
os.rmdir(os.path.join(tree, "__pycache__"))
fz2 = json.loads(json.dumps(fz))
fz2["absent_paths"]["before_preparation"].append(O)
special.append(("pre: a path that must be absent exists", run("pre-present", fz2, "pre")))
fz2 = json.loads(json.dumps(fz))
fz2["evidence"]["ancestors"][-1]["inode"] += 1
special.append(("pre: an ancestor's inode differs", run("pre-ancestor", fz2, "pre")))
fz2 = json.loads(json.dumps(fz))
fz2["deferred_inputs"][0]["requirements"][1]["equals"] = "NOPE"
special.append(("pre: the deferred input's status differs", run("pre-deferred", fz2, "pre")))
fz2 = json.loads(json.dumps(fz))
fz2["umask"] = "0o077"
special.append(("pre: umask differs", run("pre-umask", fz2, "pre")))
fz2 = json.loads(json.dumps(fz))
fz2["boot_session_uuid"] = "00000000-0000-0000-0000-000000000000"
special.append(("pre: boot differs", run("pre-boot", fz2, "pre")))
fz2 = json.loads(json.dumps(fz))
fz2["preparation"]["entries"][0]["entries"] = []
special.append(("prepared: a directory's entries differ", run("prepared-entries", fz2, "prepared")))
fz2 = json.loads(json.dumps(fz))
fz2["commands"][0]["expect"] = [{"file": O, "pointer": "/state", "equals": "NO"}]
special.append(("prepared: an earlier command's predicate fails", run("prepared-earlier", fz2, "prepared")))
fz2 = json.loads(json.dumps(fz))
fz2["commands"][2]["expect"] = [{"file": O, "pointer": "/flag", "equals": False}]
special.append(("post: Q01..Q03's predicate fails", run("post-earlier", fz2, "post")))
with open(prep_file, "ab") as f:
    f.write(b" ")
special.append(("post: a prepared input changed", run("post-changed", fz, "post")))
fz2 = json.loads(json.dumps(fz))
fz2["post"]["consumed"] = ["prepared:file"]
special.append(("post: the changed input is the consumed one", run("post-consumed", fz2, "post")))
for name, r in special:
    results.append({"case": name, "state": r["state"], "code": r["code"], "error": r["error"], "failed": r["failed"]})

with open(os.path.join(OUT, "records", "10-checker-tests.json"), "x", encoding="utf-8") as f:
    json.dump(results, f, indent=1)
    f.write("\n")
bad_cases = [r for r in results if "expected" in r and r["state"] != r["expected"]]
for r in results:
    print(json.dumps({k: r.get(k) for k in ("case", "expected", "state", "code", "error", "failed")})[:300])
print("predicate cases", sum(1 for r in results if "expected" in r), "unexpected", len(bad_cases))
