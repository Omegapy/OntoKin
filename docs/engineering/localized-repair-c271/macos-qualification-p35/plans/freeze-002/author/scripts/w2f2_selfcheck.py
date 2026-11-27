"""W2 freeze author: static checks of FREEZE-002.json, alone and against FREEZE-001.json.

Run with <worktree>/.venv/bin/python -I -S -B. Standard library only; reads only; starts nothing; imports nothing of
the project. It recomputes what the builder derived, from the two documents and the files they bind.
Usage: w2f2_selfcheck.py FREEZE-001.json FREEZE-002.json
"""
import hashlib
import itertools
import json
import os
import stat
import sys

PROCESS_EVENTS = {"subprocess.Popen", "os.posix_spawn", "os.exec", "os.fork", "os.forkpty", "os.spawn", "os.system"}
sys.addaudithook(lambda event, args: (_ for _ in ()).throw(PermissionError(event)) if event in PROCESS_EVENTS else None)

LOCAL = "<local>"
E = LOCAL + "/c271-p35/evidence"
OUT1 = LOCAL + "/c271-p35/workers/W2-freeze-001"
OUT2 = LOCAL + "/c271-p35/workers/W2-freeze-002"
WRAPPER = LOCAL + "/c271-p35/director/run/run_once_v2.sh"
NODE = LOCAL + "/c271-macos/node-v24.22.1-darwin-arm64/bin/node"
GIT = "/Library/Developer/CommandLineTools/usr/bin/git"
CF_FILE = "<home>/.CFUserTextEncoding"
RESULTS = []


def ok(name, condition, detail=""):
    RESULTS.append({"check": name, "ok": bool(condition), "detail": detail})


def sha_file(path):
    with open(path, "rb") as stream:
        return hashlib.sha256(stream.read()).hexdigest()


def quote(argv):
    return " ".join("'" + item + "'" for item in argv)


def spelled(path):
    current = "/"
    for part in [p for p in path.split("/") if p]:
        if part not in os.listdir(current):
            return False
        current = os.path.join(current, part)
    return True


f1_path, f2_path = sys.argv[1], sys.argv[2]
F1, F2 = json.load(open(f1_path)), json.load(open(f2_path))
R1 = {row["id"]: row for row in F1["commands"]}
R2 = {row["id"]: row for row in F2["commands"]}
ok("ids unique", len(R2) == len(F2["commands"]))
ok("names unique", len({r["name"] for r in F2["commands"]}) == len(F2["commands"]))
ok("id and status", F2["id"] == "FREEZE-002" and F2["status"].startswith("FROZEN_NOT_RUN"))
ok("revision_of", F2["revision_of"]["sha256"] == sha_file(f1_path) and F2["revision_of"]["id"] == "FREEZE-001")
ok("order", F2["order"] == ["P00"] + F1["order"], json.dumps(F2["order"][:3]))
ok("order ids exist", all(i in R2 for i in F2["order"]))
capture = [r["id"] for r in F2["commands"] if r["phase"] == "capture"]
ok("capture list", capture == F2["capture_commands"] and not set(capture) & set(F2["order"]))
ok("every command in order or capture", set(R2) == set(F2["order"]) | set(capture))
ok("deferred inputs empty", F2["deferred_inputs"] == [])
ok("deferred arguments", sorted(F2["deferred_arguments"]) == ["<FREEZE-002.json SHA-256>",
                                                                "<baseline discovery SHA-256>",
                                                                "<current discovery SHA-256>"])

# ---- every command: wrapper argv, shell, environment, -B, placeholders, records, timer --------------------------
envs = {row["path"]: row for row in F2["environments"].values()}
template = F2["launch"]["timer_template"]
PH = set(F2["deferred_arguments"])
for row in F2["commands"]:
    ident = row["id"]
    full = ["/bin/sh", WRAPPER, row["name"], row["cwd"], row["environment"]["file"], "--", *row["argv"]]
    ok(ident + " wrapper_argv", row["wrapper_argv"] == full)
    ok(ident + " shell", row["shell"] == quote(full) and not any("'" in x for x in full))
    env = envs.get(row["environment"]["file"])
    ok(ident + " environment file", env is not None and env["sha256"] == row["environment"]["sha256"])
    if row["argv"][:2] == ["/usr/bin/env", "-i"]:
        assigns = []
        for item in row["argv"][2:]:
            if "=" in item and not item.startswith("/"):
                assigns.append(item)
            else:
                break
        ok(ident + " env -i equals its file", env is not None and assigns == [
            k + "=" + env["environment"][k] for k in sorted(env["environment"])], json.dumps(assigns)[:200])
    for index, item in enumerate(row["argv"]):
        if item.endswith("/.venv/bin/python") or os.path.basename(item).startswith("python3"):
            flags = []
            for flag in row["argv"][index + 1:]:
                if not flag.startswith("-"):
                    break
                flags.append(flag)
            ok(ident + " -B", "-B" in flags, json.dumps(flags))
    holders = [i for i, x in enumerate(row["argv"]) if x.startswith("<") and x.endswith(">")]
    ok(ident + " placeholders", holders == [d["argv_index"] for d in row["deferred_arguments"]] and all(
        row["argv"][i] in PH for i in holders))
    ok(ident + " deferred rows", all(d["wrapper_argv_index"] == d["argv_index"] + 6 and
                                     row["wrapper_argv"][d["wrapper_argv_index"]] == d["placeholder"]
                                     for d in row["deferred_arguments"]))
    rec = E + "/" + row["name"]
    ok(ident + " records", row["records"] == {"stdout": rec + ".stdout.txt", "stderr": rec + ".stderr.txt",
                                              "exit": rec + ".exit.txt", "command": rec + ".command.json"})
    ok(ident + " absent before", set(row["records"].values()) | set(row["outputs"]) <= set(row["outputs_absent_before"]))
    ok(ident + " timer", row["timer_shell"] == template.replace("{exit_file}", row["records"]["exit"]).replace(
        "{bound}", str(row["limits"]["outer_bound_s"])))
    first = row["expect"][0] if row["expect"] else {}
    ok(ident + " argv predicate", first.get("file") == rec + ".command.json" and first.get("argv_equals_except") ==
       {"argv": row["argv"], "indices": holders})

# ---- every predicate has one kind (FR-08: a second key would be ignored) --------------------------------------
KINDS = {"exists", "sha256", "text_equals", "text_includes", "text_excludes", "argv_equals_except",
         "equals_freeze_sha256", "equals_sha256_of", "equals_from", "nonempty_string", "equals", "length", "each",
         "count_where", "one_of", "startswith", "includes", "absent"}


def kinds_of(rule):
    return sorted(k for k in rule if k in KINDS)


def well_formed(rule, nested=False):
    found = kinds_of(rule)
    good = found in ([[k] for k in KINDS] + [["count_where", "equals"]])
    if not nested:
        good = good and "file" in rule
    for key in ("each", "count_where"):
        if key in rule:
            good = good and well_formed(rule[key], nested=True)
    return good


bad = [(row["id"], rule) for row in F2["commands"] for rule in row["expect"] + row["audit_expect"]
       if not well_formed(rule)]
ok("predicates have one kind each", not bad, json.dumps(bad[:2])[:300])

# ---- the commands of freeze 001: changed only as intended ----------------------------------------------------
F1_FREEZE, F2_FREEZE = OUT1 + "/FREEZE-001.json", OUT2 + "/FREEZE-002.json"
MC11_SHA = "aade03ac64a506678ce7ade184ecedcd10c5f6a58077d1f01aa7d0d70db63800"
SAME_FIELDS = ("phase", "name", "purpose", "control", "cwd", "environment", "records", "outputs",
               "outputs_absent_before", "audit_expect", "starts", "limits", "failure_capture")
main_ids = [i for i in F1["order"] if R1[i]["phase"] == "s7" and "." not in i]
for ident, old in R1.items():
    new = R2[ident]
    for key in SAME_FIELDS:
        ok(ident + " same " + key, new[key] == old[key])
    diffs = [i for i, (a, b) in enumerate(zip(old["argv"], new["argv"])) if a != b]
    if ident.endswith(".X") or ident in ("P01", "D02", "Q04"):
        good = (len(old["argv"]) == len(new["argv"]) and len(diffs) == 2 and
                [old["argv"][i] for i in diffs] == [F1_FREEZE, "<FREEZE-001.json SHA-256>"] and
                [new["argv"][i] for i in diffs] == [F2_FREEZE, "<FREEZE-002.json SHA-256>"])
        ok(ident + " argv: only the freeze and its digest", good, json.dumps(diffs))
    elif ident == "C01":
        ok("C01 argv: only the MC11 digest", diffs == [25] and old["argv"][25] == "<MC11 reviewed list SHA-256>" and
           new["argv"][25] == MC11_SHA and new["argv"][24] == "--reviewed-sha256")
    else:
        ok(ident + " argv, wrapper_argv and shell byte-identical", old["argv"] == new["argv"] and
           old["wrapper_argv"] == new["wrapper_argv"] and old["shell"] == new["shell"] and
           old["deferred_arguments"] == new["deferred_arguments"])
    k1 = 1 + len(old["deferred_arguments"]) + 5
    k2 = 1 + len(new["deferred_arguments"]) + 5
    ok(ident + " freeze 001's own predicates kept in order", new["expect"][k2:k2 + len(old["expect"]) - k1] ==
       old["expect"][k1:])
    if ident in main_ids:
        tail = R2[ident + ".L"]["expect"] + (R2[ident + ".P"]["expect"] if ident + ".P" in R2 else [])
        ok(ident + " FR-02: .L and .P predicates appended in full", new["expect"][-len(tail):] == tail and
           R2[ident + ".L"]["expect"] == R1[ident + ".L"]["expect"])
        middle = new["expect"][k2 + len(old["expect"]) - k1:len(new["expect"]) - len(tail)]
        if ident == "C17":
            out = R2["C17"]["outputs"][0] + "/outcomes.json"
            want = [{"file": out, "pointer": "/process_events", "each": {"pointer": "/event", "equals": "subprocess.Popen"}},
                    {"file": out, "pointer": "/process_events", "each": {"pointer": "/argv/0", "one_of": [NODE, GIT]}},
                    {"file": CF_FILE, "sha256": F2["host_facts"][0]["sha256"]}]
        elif ident in ("C06", "C07"):
            out = R2[ident]["outputs"][0]
            want = [{"file": out, "pointer": "/process_events", "each": {"pointer": "/event", "equals": "subprocess.Popen"}},
                    {"file": out, "pointer": "/process_events", "each": {"pointer": "/argv/0", "equals": GIT}}]
        else:
            want = []
        ok(ident + " FR-03/FR-12 predicates exactly", middle == want, json.dumps(middle)[:300])
    else:
        ok(ident + " nothing appended", len(new["expect"]) - k2 == len(old["expect"]) - k1)
    replaced = {"C02": ["exit 1, state_equals_host false"],
                "C03": ["refused at SOURCE, PYTHON, RUNTIME, DEPENDENCY, GIT, OS or ENVIRONMENT"],
                "C04": ["refused at SOURCE, PYTHON, RUNTIME, DEPENDENCY, GIT, OS or ENVIRONMENT"],
                "C05": ["refused at SOURCE, PYTHON, RUNTIME, DEPENDENCY, GIT, OS or ENVIRONMENT"]}.get(ident, [])
    kept = [r for r in old["classification"] if r["outcome"] not in replaced]
    ok(ident + " classification rows kept", all(r in new["classification"] for r in kept) and
       len(kept) == len(old["classification"]) - len(replaced))
ok("the CF predicate's digest is the host fact's", F2["host_facts"][0]["path"] == CF_FILE and
   F2["host_facts"][0]["sha256"] == "bd605d2eae2bc28178ba94d69e189242f971d699c5846addae706d7e52bc69fd")

# ---- P00 -----------------------------------------------------------------------------------------------------
p00 = R2["P00"]
ok("P00 argv", p00["argv"] == ["/usr/bin/env", "-i", "PATH=/usr/bin:/bin", "/usr/bin/shasum", "-a", "256", "--strict",
                               "-c", "SHA256SUMS.txt", "s7/p00-freeze-001-rebound.sha256sums.txt"])
ok("P00 cwd and phase", p00["cwd"] == OUT2 and p00["phase"] == "precondition" and F2["order"][0] == "P00")
listed = {}
with open(OUT2 + "/s7/p00-freeze-001-rebound.sha256sums.txt", "rb") as stream:
    for line in stream.read().decode("ascii").splitlines():
        if line.startswith("#"):
            continue
        digest, path = line.split("  ", 1)
        listed[path] = digest
sums1 = {}
with open(OUT1 + "/SHA256SUMS.txt", "rb") as stream:
    for line in stream.read().decode("ascii").splitlines():
        digest, rel = line.split("  ", 1)
        sums1[OUT1 + "/" + rel] = digest
rebound = {b["path"]: b["sha256"] for b in F2["bindings"] if b["path"].startswith(OUT1 + "/")}
ok("P00's second list: exactly the rebound documents", set(listed) == set(rebound), str(len(listed)))
ok("P00's second list: freeze 001's digests", all(sums1.get(p) == d == rebound[p] for p, d in listed.items()))
ok("the checker and the preparation are rebound", OUT1 + "/s7/w2f_s7_check.py" in listed and
   OUT1 + "/s7/prepare-s7-001.sh" in listed)

# ---- bindings -------------------------------------------------------------------------------------------------
ok("freeze 001's bindings unchanged", F2["bindings"][:len(F1["bindings"])] == F1["bindings"])
ok("two new bindings", [b["id"] for b in F2["bindings"][len(F1["bindings"]):]] == [
    "review001:MC11-REVIEWED-LIST-001.json", "freeze002:s7/p00-freeze-001-rebound.sha256sums.txt"])
for row in F2["bindings"]:
    info = os.lstat(row["path"])
    good = (stat.S_ISREG(info.st_mode) and sha_file(row["path"]) == row["sha256"] and info.st_size == row["size_bytes"]
            and "0o%03o" % stat.S_IMODE(info.st_mode) == row["mode"] and (info.st_nlink == 1 or not row["nlink_one"])
            and os.path.realpath(row["path"]) == row["path"] and spelled(row["path"]))
    ok("binding " + row["id"], good)
mc11 = [b for b in F2["bindings"] if b["id"] == "review001:MC11-REVIEWED-LIST-001.json"][0]
ok("MC11 binding as disposed", (mc11["sha256"], mc11["size_bytes"], mc11["mode"]) == (MC11_SHA, 344283, "0o644"))
ok("trees", F2["trees"] == F1["trees"] + [{"root": OUT2}])

# ---- absent paths --------------------------------------------------------------------------------------------
prepared = {row["path"] for row in F2["preparation"]["entries"]}
before, after = set(prepared), set()
for row in F2["commands"]:
    before |= set(row["outputs_absent_before"])
    if row["phase"] in ("s7", "post", "capture"):
        after |= set(row["outputs_absent_before"])
before -= set(R2["P00"]["outputs_absent_before"]) | set(R2["P01"]["outputs_absent_before"])
ok("before_preparation", sorted(before) == F2["absent_paths"]["before_preparation"])
ok("after_preparation", sorted(after) == F2["absent_paths"]["after_preparation"])
ok("no output is prepared", not after & prepared)
ok("preparation unchanged", F2["preparation"]["entries"] == F1["preparation"]["entries"] and
   F2["preparation"]["script"] == F1["preparation"]["script"])
ok("43 prepared entries: 25 directories, 18 files", (len(prepared), sum(1 for r in F2["preparation"]["entries"]
                                                                       if r["kind"] == "directory")) == (43, 25))
everything = before | set(R2["P00"]["outputs_absent_before"]) | set(R2["P01"]["outputs_absent_before"])
ok("every S7 path absent now", not [p for p in everything if os.path.lexists(p)])
ok("every S7 path under the evidence parent", all(p.startswith(E + "/") for p in everything))

# ---- capture commands ------------------------------------------------------------------------------------------
for parent in ("C16", "C17", "C19"):
    p_argv = R2[parent + ".P"]["argv"]
    start = p_argv.index("probe")
    prefix, pairs, i = p_argv[:start], [], start + 1
    while p_argv[i] == "--pair":
        pairs.append((p_argv[i + 1], p_argv[i + 2]))
        i += 3
    member = R2[parent]["overrun"]
    ok(parent + " candidates", [(c["before"], c["after"]) for c in member["candidates"]] == pairs and
       [c["k"] for c in member["candidates"]] == list(range(1, len(pairs) + 1)))
    want_probes = {}
    for size in range(1, len(pairs) + 1):
        for combo in itertools.combinations(range(len(pairs)), size):
            digits = "".join(str(i + 1) for i in combo)
            ident = parent + ".O" + digits
            want_probes[digits] = ident
            row = R2.get(ident)
            out = E + "/" + R2[parent]["name"] + ".overrun-probes-" + digits + ".json"
            ok(ident + " argv", row is not None and row["argv"] == prefix + ["probe"] + [
                x for c in combo for x in ("--pair",) + pairs[c]] + ["--output", out] and row["outputs"] == [out])
    ok(parent + " probe commands", member["probe_commands"] == want_probes)
    for k, pair in enumerate(pairs, 1):
        row = R2.get(parent + ".S%d" % k)
        out = E + "/" + R2[parent]["name"] + ".stop-%d.json" % k
        ok(parent + ".S%d argv" % k, row is not None and row["argv"] == prefix + ["stop", "--pair", *pair, "--output", out])
    ok(parent + " stop commands", member["stop_commands"] == {str(k): parent + ".S%d" % k for k in range(1, len(pairs) + 1)})
    text = "k=''; " + "; ".join("if [ -e '%s' ] || [ -L '%s' ]; then k=\"${k}%d\"; fi" % (a, a, k)
                                for k, (b, a) in enumerate(pairs, 1)) + \
        "; if [ -n \"$k\" ]; then printf 'overrun-select: %%s\\n' \"%s.O$k\"; else printf 'overrun-select: none\\n'; fi" % parent
    ok(parent + " select_shell", member["select_shell"] == text)
ok("25 capture commands", len(capture) == 25)
ok("no capture command in order", not [i for i in F2["order"] if R2[i]["phase"] == "capture"])

# ---- sections ------------------------------------------------------------------------------------------------
ok("launch", all(k in F2["launch"] for k in ("command", "timer", "timer_template", "after", "read", "p00")))
ok("overrun six steps", len(F2["overrun"]["steps"]) == 6 and all(F2["overrun"]["steps"][i].startswith(str(i + 1) + ".")
                                                                 for i in range(6)))
ok("stop rules", len(F2["stop_rules"]) == 12 and "P00" in F2["stop_rules"][0] and "overrun" in F2["stop_rules"][9])
ok("carried FR-01..FR-12", [c["id"] for c in F2["carried_findings"][-12:]] == ["FR-%02d" % i for i in range(1, 13)])
ok("totals unchanged", F2["totals"]["rows"] == F1["totals"]["rows"] and F2["totals"]["s7_bounded"] ==
   F1["totals"]["s7_bounded"] and F2["totals"]["mh_plan_table"] == F1["totals"]["mh_plan_table"])
ok("python launchers", F2["totals"]["recorded_not_bounded"]["python_launchers"] == 64)
ok("same environments, configurations, controls, classes", all(F2[k] == F1[k] for k in (
    "environments", "configurations", "controls", "classes", "host", "host_facts", "evidence", "wrapper", "contract",
    "fixed_state", "boot_session_uuid", "umask", "mh_plan_section_6", "audit_inputs", "post")))
ok("FR-09 limit", any("_OwnedTemporaryCohort" in x for x in F2["limits"]["this_freeze"]))
ok("FR-12 assumption", "CFUserTextEncoding" in F2["n04"]["assumption"] and "UID 501" in F2["n04"]["assumption"])
failed = [r for r in RESULTS if not r["ok"]]
print(json.dumps({"checks": len(RESULTS), "failed": len(failed)}, sort_keys=True))
for row in failed:
    print("FAIL", row["check"], row["detail"])
