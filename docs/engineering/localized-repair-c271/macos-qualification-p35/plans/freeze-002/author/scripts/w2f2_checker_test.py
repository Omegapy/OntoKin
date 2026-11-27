"""W2 freeze author: run the unchanged checker's expect phase, in this one process, on a synthetic freeze whose
commands carry freeze 002's new predicates (FR-02's appended .L and .P predicates, FR-03's process-event bounds,
FR-12's CF-file digest), each file path redirected into a synthetic world inside OUT2.

Run with <worktree>/.venv/bin/python -I -S -B. Standard library only; starts nothing; writes only under TEST_DIR.
Usage: w2f2_checker_test.py CHECKER FREEZE-002.json TEST_DIR   (TEST_DIR must be absent)
"""
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import os
import sys

PROCESS_EVENTS = {"subprocess.Popen", "os.posix_spawn", "os.exec", "os.fork", "os.forkpty", "os.spawn", "os.system"}
sys.addaudithook(lambda event, args: (_ for _ in ()).throw(PermissionError(event)) if event in PROCESS_EVENTS else None)

checker_path, freeze_path, top = sys.argv[1:4]
E = "<local>/c271-p35/evidence"
CF_FILE = "<home>/.CFUserTextEncoding"
NODE = "<local>/c271-macos/node-v24.22.1-darwin-arm64/bin/node"
GIT = "/Library/Developer/CommandLineTools/usr/bin/git"
BOOT = "C90010BA-4DA9-475D-BBAB-CF1A9C40175A"
os.mkdir(top, 0o755)
F2 = json.load(open(freeze_path))
R = {row["id"]: row for row in F2["commands"]}


def put(path, data, mode=0o644):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as stream:
        stream.write(data)
    os.chmod(path, mode)


def put_json(path, value):
    put(path, json.dumps(value).encode())


# ---- records of a .L and a .P (C16's), good unless a case changes one ----------------------------------------
L, P = R["C16.L"], R["C16.P"]
tool_sha = [r for r in L["expect"] if r.get("pointer") == "/tool/sha256"][0]["equals"]
probe_targets = len(P["argv"][P["argv"].index("probe") + 1:-2]) // 3


def build_lp(base, *, states=None, listing_events=0, drop=None, targets=None):
    def local(path):
        if not path.startswith(E + "/"):
            raise SystemExit("unexpected path " + path)
        return base + "/E" + path[len(E):]
    for row in (L, P):
        rec = local(E + "/" + row["name"] + ".command.json")
        put_json(rec, {"argv": row["argv"], "cwd": row["cwd"], "environment": {"sha256": row["environment"]["sha256"]},
                       "boot": {"before": BOOT, "after": BOOT}, "retries": 0})
        put(local(E + "/" + row["name"] + ".exit.txt"), b"0\n")
    put_json(local(L["outputs"][0]), {"command": "listing", "boot_before": BOOT, "boot_after": BOOT,
                                      "process_events": [{"event": "subprocess.Popen"}] * listing_events,
                                      "tool": {"sha256": tool_sha}})
    states = states or ["absent"] * probe_targets
    put_json(local(P["outputs"][0]), {"command": "probe", "boot_after": BOOT, "process_events": [],
                                      "targets": [{"state": s} for s in (targets if targets is not None else states)]})
    if drop:
        os.unlink(local(drop))
    rules = copy.deepcopy(L["expect"] + P["expect"])
    for rule in rules:
        rule["file"] = local(rule["file"])
    return rules


commands = []


def command(ident, expect):
    commands.append({"id": ident, "phase": "s7", "expect": expect, "audit_expect": []})


command("T_LP_all_absent_MET", build_lp(top + "/w1"))
command("T_LP_present_established", build_lp(top + "/w2", states=["absent", "present, identity established", "absent"]))
command("T_LP_present_not_established", build_lp(top + "/w3", states=["absent", "absent",
                                                                       "present, identity not established"]))
command("T_LP_unknown", build_lp(top + "/w4", states=["unknown", "absent", "absent"]))
command("T_LP_two_targets", build_lp(top + "/w5", targets=["absent", "absent"]))
command("T_LP_listing_event", build_lp(top + "/w6", listing_events=1))
command("T_LP_listing_absent", build_lp(top + "/w7", drop=L["outputs"][0]))
command("T_LP_probe_exit_absent", build_lp(top + "/w8", drop=E + "/" + P["name"] + ".exit.txt"))

# ---- FR-03 on C17 and C06, and C17's count of Node events --------------------------------------------------
c17_out = R["C17"]["outputs"][0] + "/outcomes.json"
fr03_c17 = [r for r in R["C17"]["expect"] if r["file"] == c17_out and "each" in r and
            r["each"]["pointer"] in ("/event", "/argv/0")]
count_node = [r for r in R["C17"]["expect"] if r["file"] == c17_out and "count_where" in r]
c06_out = R["C06"]["outputs"][0]
fr03_c06 = [r for r in R["C06"]["expect"] if r["file"] == c06_out and "each" in r and
            r["each"]["pointer"] in ("/event", "/argv/0")]
assert len(fr03_c17) == 2 and len(count_node) == 1 and len(fr03_c06) == 2


def events_world(name, events, out):
    path = top + "/" + name + "/outcomes.json"
    put_json(path, {"process_events": events})
    rules = copy.deepcopy(out)
    for rule in rules:
        rule["file"] = path
    return rules


popen = lambda program: {"event": "subprocess.Popen", "argv": [program, "x"]}
good = [popen(NODE)] * 3 + [popen(GIT)] * 60
command("T_C17_events_MET", events_world("e1", good, fr03_c17 + count_node))
command("T_C17_event_other_program", events_world("e2", good + [popen("/bin/sh")], fr03_c17))
command("T_C17_event_posix_spawn", events_world("e3", good + [{"event": "os.posix_spawn", "argv": [NODE]}], fr03_c17))
command("T_C17_event_without_argv", events_world("e4", good + [{"event": "subprocess.Popen"}], fr03_c17))
command("T_C17_event_without_event", events_world("e5", good + [{"argv": [NODE]}], fr03_c17))
command("T_C17_events_empty_vacuous_MET", events_world("e6", [], fr03_c17))
command("T_C17_events_empty_with_count", events_world("e7", [], fr03_c17 + count_node))
command("T_C17_events_null_member", events_world("e8", None, fr03_c17))
command("T_C06_git_MET", events_world("g1", [popen(GIT)] * 15, fr03_c06))
command("T_C06_node", events_world("g2", [popen(GIT)] * 15 + [popen(NODE)], fr03_c06))

# ---- FR-12: the CF file's digest -----------------------------------------------------------------------------
cf_rule = [r for r in R["C17"]["expect"] if r["file"] == CF_FILE]
assert len(cf_rule) == 1 and cf_rule[0]["sha256"] == hashlib.sha256(b"0x0:0x0").hexdigest()
for name, content in (("c1", b"0x0:0x0"), ("c2", b"0x0:0x1")):
    path = top + "/" + name + "/.CFUserTextEncoding"
    put(path, content, 0o400)
    rule = copy.deepcopy(cf_rule)
    rule[0]["file"] = path
    command("T_CF_" + ("same_MET" if name == "c1" else "changed"), rule)
rule = copy.deepcopy(cf_rule)
rule[0]["file"] = top + "/c3/.CFUserTextEncoding"
command("T_CF_absent", rule)

# ---- the real C17's expect, with every record missing: NOT_MET, never an exception ------------------------
real = copy.deepcopy(R["C17"]["expect"])
for rule in real:
    rule["file"] = top + "/empty" + rule["file"]
command("T_C17_real_no_records", real)

freeze = {"schema": "synthetic", "commands": commands}
freeze_file = top + "/synthetic-freeze.json"
put_json(freeze_file, freeze)
freeze_sha = hashlib.sha256(open(freeze_file, "rb").read()).hexdigest()
spec = importlib.util.spec_from_file_location("w2f_s7_check_under_test", checker_path)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)
WANT = {"T_LP_all_absent_MET": (0, "MET"), "T_C17_events_MET": (0, "MET"), "T_C17_events_empty_vacuous_MET": (0, "MET"),
        "T_C06_git_MET": (0, "MET"), "T_CF_same_MET": (0, "MET")}
results = []
for row in commands:
    out = io.StringIO()
    sys.argv = [checker_path, "--freeze", freeze_file, "--freeze-sha256", freeze_sha, "expect", "--command", row["id"]]
    try:
        with contextlib.redirect_stdout(out):
            code = checker.main()
        report = json.loads(out.getvalue())
        state = report.get("state")
        failed = [f["item"]["rule"].get("pointer", f["item"]["rule"].get("file", "")[-40:]) for f in report["failed"]]
    except Exception as exc:  # a crash would also stop S7 (exit 1), but none is expected here
        code, state, failed = "raised", type(exc).__name__ + ": " + str(exc), []
    want = WANT.get(row["id"], (1, "NOT_MET"))
    results.append({"case": row["id"], "ok": (code, state) == want, "code": code, "state": state,
                    "failed_pointers": failed[:4], "predicates": len(row["expect"])})
print(json.dumps({"cases": len(results), "failed": [r["case"] for r in results if not r["ok"]],
                  "synthetic_freeze_sha256": freeze_sha}, indent=1))
print(json.dumps(results, indent=1))
