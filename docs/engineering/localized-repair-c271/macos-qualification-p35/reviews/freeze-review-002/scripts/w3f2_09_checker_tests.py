"""Freeze review 002, script 09: the bound checker, loaded from its bytes, on synthetic worlds inside <OUT>.

1. Confirms the checker's SHA-256 (eb96aa1a...) before loading it.
2. For each main command C01 to C19: builds a synthetic world in which every frozen predicate of its expect
   (its own, FR-03, FR-12, its .L's and .P's) holds, with every 'file' path moved into the world; shows the
   predicates jointly satisfiable (MET), then mutates the FR-02, FR-03 and FR-12 parts one at a time.
3. Runs the checker's main() in phase expect on synthetic freezes (base and mutations), and in phase prepared on
   a synthetic freeze that holds P00 and a D02, for A-7.
4. Records the checker semantics that matter for the appended predicates (FR-08).

Run: <worktree>/.venv/bin/python -I -S -B w3f2_09_checker_tests.py OUTPUT.json
"""
import contextlib
import copy
import hashlib
import io
import json
import os
import stat
import sys

PROCESS_EVENTS = {"subprocess.Popen", "os.posix_spawn", "os.exec", "os.fork", "os.forkpty", "os.spawn", "os.system"}


def refuse(event, args):
    if event in PROCESS_EVENTS:
        raise PermissionError("no process: " + event)


sys.addaudithook(refuse)

P35 = "<local>/c271-p35"
E = P35 + "/evidence"
OUT = P35 + "/workers/W3-freeze-002"
# Run 1 (<OUT>/checker-test) stopped on a fault in this script's prepared() test; run 2 (<OUT>/checker-test-run2)
# could not build C14's world (its equals_from sources are other commands' files); run 3 builds them.
WORLD = OUT + "/" + (sys.argv[2] if len(sys.argv) > 2 else "checker-test-run2")
CHECKER = P35 + "/workers/W2-freeze-001/s7/w2f_s7_check.py"
F2 = P35 + "/workers/W2-freeze-002/FREEZE-002.json"
CF = "<home>/.CFUserTextEncoding"
NODE = "<local>/c271-macos/node-v24.22.1-darwin-arm64/bin/node"
GIT = "/Library/Developer/CommandLineTools/usr/bin/git"
TEST_FREEZE_SHA = "f" * 64


def sha(data):
    return hashlib.sha256(data).hexdigest()


with open(CHECKER, "rb") as stream:
    SOURCE = stream.read()
assert sha(SOURCE) == "eb96aa1a25ba51bf32f55420997bc8599343a59c2238ce70b4b0c622d01643f6", "checker bytes differ"
NS = {"__name__": "w2f_s7_check_under_review", "__file__": CHECKER}
exec(compile(SOURCE, CHECKER, "exec"), NS)
check_predicate, evaluate_on, pointer_fn = NS["check_predicate"], NS["evaluate_on"], NS["pointer"]


def toks(p):
    return [] if not p else [t.replace("~1", "/").replace("~0", "~") for t in p[1:].split("/")]


def get(doc, p):
    return pointer_fn(doc, p)


def put(doc, p, value):
    t = toks(p)
    cur = doc
    for i, tok in enumerate(t):
        last = i == len(t) - 1
        if isinstance(cur, list):
            idx = int(tok)
            while len(cur) <= idx:
                cur.append({})
            if last:
                cur[idx] = value
            else:
                if not isinstance(cur[idx], (dict, list)):
                    cur[idx] = [] if t[i + 1].isdigit() else {}
                cur = cur[idx]
        else:
            if last:
                cur[tok] = value
            else:
                if tok not in cur or not isinstance(cur[tok], (dict, list)):
                    cur[tok] = [] if t[i + 1].isdigit() else {}
                cur = cur[tok]


def remove(doc, p):
    t = toks(p)
    cur = doc
    for tok in t[:-1]:
        cur = cur[int(tok)] if isinstance(cur, list) else cur.get(tok, {})
    if isinstance(cur, dict):
        cur.pop(t[-1], None)


def satisfy_value(doc, rule):
    """Make doc satisfy one JSON rule (pointer + one predicate), unless it already does."""
    if evaluate_on(doc, rule):
        return
    p = rule.get("pointer", "")
    if rule.get("absent"):
        remove(doc, p)
    elif "argv_equals_except" in rule:
        put(doc, p, list(rule["argv_equals_except"]["argv"]))
    elif rule.get("equals_freeze_sha256"):
        put(doc, p, TEST_FREEZE_SHA)
    elif rule.get("nonempty_string"):
        put(doc, p, "x")
    elif "equals" in rule and "count_where" not in rule and "length" not in rule:
        put(doc, p, copy.deepcopy(rule["equals"]))
    elif "length" in rule:
        found, value = get(doc, p)
        if found and isinstance(value, list):
            del value[rule["length"]:]
            while len(value) < rule["length"]:
                value.append({})
        else:
            put(doc, p, [{} for _ in range(rule["length"])])
    elif "each" in rule:
        found, value = get(doc, p)
        if not found or not isinstance(value, list):
            put(doc, p, [])
            found, value = get(doc, p)
        for item in value:
            satisfy_value(item, rule["each"])
    elif "count_where" in rule:
        found, value = get(doc, p)
        if not found or not isinstance(value, list):
            put(doc, p, [])
            found, value = get(doc, p)
        have = sum(1 for item in value if evaluate_on(item, rule["count_where"]))
        while have < rule["equals"]:
            item = {}
            satisfy_value(item, rule["count_where"])
            value.append(item)
            have += 1
    elif "one_of" in rule:
        put(doc, p, copy.deepcopy(rule["one_of"][0]))
    elif "startswith" in rule:
        put(doc, p, rule["startswith"])
    elif "includes" in rule:
        put(doc, p, rule["includes"])


def relocate(rules, root):
    """Move every file path of the rules into the world; argv and equals values stay as frozen."""
    out = []
    for r in copy.deepcopy(rules):
        if "file" in r:
            r["file"] = r["file"].replace(E, root + "/E").replace(CF, root + "/home/.CFUserTextEncoding")
        if "equals_from" in r:
            r["equals_from"]["file"] = r["equals_from"]["file"].replace(E, root + "/E")
        out.append(r)
    return out


def build(rules, root, extras=None):
    """Write a world in which every rule holds; returns the list of rules that could not be satisfied."""
    os.makedirs(root, exist_ok=False)
    docs, texts, creates, never = {}, {}, set(), set()
    for r in rules:
        f = r["file"]
        if "exists" in r:
            (creates if r["exists"] else never).add(f)
        elif "sha256" in r:
            texts.setdefault(f, {"equals": None, "includes": [], "excludes": []})
            texts[f]["equals"] = "0x0:0x0"
        elif "text_equals" in r or "text_includes" in r or "text_excludes" in r:
            t = texts.setdefault(f, {"equals": None, "includes": [], "excludes": []})
            if "text_equals" in r:
                t["equals"] = r["text_equals"]
            elif "text_includes" in r:
                t["includes"].append(r["text_includes"])
            else:
                t["excludes"].append(r["text_excludes"])
        else:
            docs.setdefault(f, {})
    for phase in (("argv_equals_except", "length", "count_where"), None):
        for r in rules:
            if r["file"] in docs and "equals_from" not in r:
                kinds = [k for k in ("argv_equals_except", "length", "count_where") if k in r]
                if (phase is not None and kinds) or (phase is None and not kinds):
                    satisfy_value(docs[r["file"]], r)
    for r in rules:  # FR-03 and argv_equals_except may need a second pass after equals_freeze_sha256
        if r["file"] in docs and "equals_from" not in r:
            satisfy_value(docs[r["file"]], r)
    if extras:
        extras(docs, root)
    for r in rules:
        if "equals_from" in r and r["file"] in docs:
            src = docs.get(r["equals_from"]["file"])
            if src is None:  # a source written by another command (C12.L, C13.L for C14): a synthetic one
                src = docs[r["equals_from"]["file"]] = {}
                put(src, r["equals_from"]["pointer"], "a" * 64)
            if src is not None:
                ok, value = get(src, r["equals_from"]["pointer"])
                if ok:
                    put(docs[r["file"]], r["pointer"], copy.deepcopy(value))
    for f, d in docs.items():
        os.makedirs(os.path.dirname(f), exist_ok=True)
        with open(f, "x") as s:
            json.dump(d, s, sort_keys=True)
    for f, t in texts.items():
        os.makedirs(os.path.dirname(f), exist_ok=True)
        body = t["equals"] if t["equals"] is not None else "".join(t["includes"])
        with open(f, "x") as s:
            s.write(body)
    for f in creates - set(docs) - set(texts):
        os.makedirs(os.path.dirname(f), exist_ok=True)
        open(f, "x").close()
    NS["CONTEXT"]["freeze_sha256"] = TEST_FREEZE_SHA
    return [r for r in rules if not check_predicate(r, {})["ok"]]


def state(rules):
    NS["CONTEXT"]["freeze_sha256"] = TEST_FREEZE_SHA
    results = [check_predicate(r, {}) for r in rules]
    return ("MET" if all(x["ok"] for x in results) else "NOT_MET"), [x["rule"] for x in results if not x["ok"]]


def rewrite_json(path, fn):
    with open(path, "rb") as s:
        d = json.loads(s.read())
    fn(d)
    os.chmod(path, 0o644)
    os.unlink(path)
    with open(path, "x") as s:
        json.dump(d, s, sort_keys=True)


def main_expect(freeze_doc, root, command):
    """The checker's own main(), phase expect, on a synthetic freeze written in the world."""
    path = root + "/synthetic-freeze-" + command + ".json"
    data = json.dumps(freeze_doc, sort_keys=True).encode("ascii")
    if not os.path.exists(path):
        with open(path, "xb") as s:
            s.write(data)
    argv = ["w2f_s7_check.py", "--freeze", path, "--freeze-sha256", sha(data), "expect", "--command", command]
    NS["CONTEXT"]["freeze_sha256"] = None
    buffer = io.StringIO()
    saved = sys.argv
    sys.argv = argv
    try:
        with contextlib.redirect_stdout(buffer):
            code = NS["main"]()
    finally:
        sys.argv = saved
    report = json.loads(buffer.getvalue())
    return code, report["state"], sha(data)


def main():
    with open(F2, "rb") as s:
        f = json.loads(s.read())
    cmds = {c["id"]: c for c in f["commands"]}
    os.makedirs(WORLD, exist_ok=False)
    result = {"script": "w3f2_09_checker_tests.py", "checker_sha256": sha(SOURCE), "cases": []}

    def case(name, expected, got, note=""):
        result["cases"].append({"case": name, "expected": expected, "got": got, "as_expected": expected == got, "note": note})

    def c17_extras(docs, root):
        out = docs.get(root + "/E/s7-001-cohort-outcomes/outcomes.json")
        if out is not None:
            for _ in range(60):
                out["process_events"].append({"event": "subprocess.Popen", "argv": [GIT, "-c", "core.fsmonitor=false"]})

    def c0607_extras(docs, root):
        for name in ("s7-001-mc29-configuration.json", "s7-001-mc29-job-input.json"):
            out = docs.get(root + "/E/" + name)
            if out is not None:
                out["process_events"] = [{"event": "subprocess.Popen", "argv": [GIT, "rev-parse"]} for _ in range(15)]
    # 1. Every main command: the frozen expect jointly satisfiable in a world.
    for n in range(1, 20):
        cid = "C%02d" % n
        root = WORLD + "/base-" + cid
        rules = relocate(cmds[cid]["expect"], root)
        extras = c17_extras if cid == "C17" else (c0607_extras if cid in ("C06", "C07") else None)
        unsatisfied = build(rules, root, extras)
        st, failed = state(rules)
        case("base " + cid + ": every frozen predicate holds in the synthetic world", "MET", st,
             "" if not unsatisfied else "unsatisfied: " + json.dumps(unsatisfied)[:500])
        # The same through the checker's main() on a synthetic freeze.
        doc = {"commands": [dict(cmds[cid], expect=rules)]}
        code, mstate, _ = main_expect(doc, root, cid)
        case("main() base " + cid, [0, "MET"], [code, mstate])
    # 2. FR-02: the .P parts of C16, C17 and C19, each state but absent; missing, short, refused records.
    for cid, probes_name in (("C16", "s7-001-c16-direct-probe-r1"), ("C17", "s7-001-c17-cohort"), ("C19", "s7-001-c19-direct-probe-r2")):
        for label, mutate in (
                ("target 0 present, identity established", lambda d: d["targets"][0].update(state="present, identity established")),
                ("last target present, identity not established", lambda d: d["targets"][-1].update(state="present, identity not established")),
                ("a target unknown", lambda d: d["targets"][0].update(state="unknown")),
                ("one target fewer", lambda d: d["targets"].pop()),
                ("a target without state", lambda d: d["targets"][0].pop("state")),
                ("refusal document in place of the record", lambda d: (d.clear(), d.update(schema="ontokin.c271.p35-tool-refusal/1", state="REFUSED"))),
                ("a process event in the probe", lambda d: d["process_events"].append({"event": "subprocess.Popen"})),
                ("boot_after differs", lambda d: d.update(boot_after="00000000-0000-0000-0000-000000000000"))):
            root = WORLD + "/fr02-%s-%s" % (cid, label.replace(" ", "-").replace(",", ""))
            rules = relocate(cmds[cid]["expect"], root)
            build(rules, root, c17_extras if cid == "C17" else None)
            rewrite_json(root + "/E/" + probes_name + ".probes.json", mutate)
            st, failed = state(rules)
            case("FR-02 %s.P: %s" % (cid, label), "NOT_MET", st, "failed rules: %d" % len(failed))
        for label, target in (("probe record absent", ".probes.json"), ("probe exit file absent", ".probes.exit.txt"),
                              ("listing record absent", ".readback.json"), ("listing command record absent", ".readback-listing.command.json")):
            root = WORLD + "/fr02-%s-%s" % (cid, label.replace(" ", "-"))
            rules = relocate(cmds[cid]["expect"], root)
            build(rules, root, c17_extras if cid == "C17" else None)
            os.unlink(root + "/E/" + probes_name + target)
            st, failed = state(rules)
            case("FR-02 %s: %s" % (cid, label), "NOT_MET", st)
        root = WORLD + "/fr02-%s-probe-exit-2" % cid
        rules = relocate(cmds[cid]["expect"], root)
        build(rules, root, c17_extras if cid == "C17" else None)
        os.unlink(root + "/E/" + probes_name + ".probes.exit.txt")
        with open(root + "/E/" + probes_name + ".probes.exit.txt", "x") as s:
            s.write("2\n")
        case("FR-02 %s.P: exit 2" % cid, "NOT_MET", state(rules)[0])
        root = WORLD + "/fr02-%s-listing-tool-digest" % cid
        rules = relocate(cmds[cid]["expect"], root)
        build(rules, root, c17_extras if cid == "C17" else None)
        rewrite_json(root + "/E/" + probes_name + ".readback.json", lambda d: d["tool"].update(sha256="0" * 64))
        case("FR-02 %s.L: another tool digest" % cid, "NOT_MET", state(rules)[0])
    # FR-02 for a command without a .P (C09): the .L parts.
    root = WORLD + "/fr02-C09-listing-event"
    rules = relocate(cmds["C09"]["expect"], root)
    build(rules, root)
    rewrite_json(root + "/E/s7-001-c09-extract-1c2f25ba.readback.json", lambda d: d["process_events"].append({"event": "os.system"}))
    case("FR-02 C09.L: a process event in the listing", "NOT_MET", state(rules)[0])
    # 3. FR-03: C17, C06, C07.
    out17 = "/E/s7-001-cohort-outcomes/outcomes.json"
    for label, mutate in (
            ("an os.posix_spawn event of the bound Git", lambda d: d["process_events"].append({"event": "os.posix_spawn", "argv": [GIT]})),
            ("a Popen of /bin/sh", lambda d: d["process_events"].append({"event": "subprocess.Popen", "argv": ["/bin/sh", "-c", "x"]})),
            ("a Popen of git by name", lambda d: d["process_events"].append({"event": "subprocess.Popen", "argv": ["git", "status"]})),
            ("an event without argv (ctypes.dlsym)", lambda d: d["process_events"].append({"event": "ctypes.dlsym", "symbol": "fork"})),
            ("a description_error event", lambda d: d["process_events"].append({"event": "subprocess.Popen", "description_error": "TypeError"})),
            ("a fourth Node start", lambda d: d["process_events"].append({"event": "subprocess.Popen", "argv": [NODE]}))):
        root = WORLD + "/fr03-C17-" + label.replace(" ", "-").replace("/", "_").replace("(", "").replace(")", "")
        rules = relocate(cmds["C17"]["expect"], root)
        build(rules, root, c17_extras)
        rewrite_json(root + out17, mutate)
        case("FR-03 C17: " + label, "NOT_MET", state(rules)[0])
    root = WORLD + "/fr03-C17-only-git-no-node"
    rules = relocate(cmds["C17"]["expect"], root)
    build(rules, root, c17_extras)
    rewrite_json(root + out17, lambda d: d.update(process_events=[e for e in d["process_events"] if e["argv"][0] == GIT]))
    case("FR-03 C17: no Node event (count_where 3 fails)", "NOT_MET", state(rules)[0])
    for cid, name in (("C06", "s7-001-mc29-configuration.json"), ("C07", "s7-001-mc29-job-input.json")):
        for label, mutate in (("a Popen of the bound Node", lambda d: d["process_events"].append({"event": "subprocess.Popen", "argv": [NODE]})),
                              ("an os.exec event", lambda d: d["process_events"].append({"event": "os.exec", "argv": [GIT]})),
                              ("a Popen of /usr/bin/true", lambda d: d["process_events"].append({"event": "subprocess.Popen", "argv": ["/usr/bin/true"]}))):
            root = WORLD + "/fr03-%s-%s" % (cid, label.replace(" ", "-").replace("/", "_"))
            rules = relocate(cmds[cid]["expect"], root)
            build(rules, root, c0607_extras)
            rewrite_json(root + "/E/" + name, mutate)
            case("FR-03 %s: %s" % (cid, label), "NOT_MET", state(rules)[0])
        root = WORLD + "/fr03-%s-empty-events" % cid
        rules = relocate(cmds[cid]["expect"], root)
        build(rules, root, c0607_extras)
        rewrite_json(root + "/E/" + name, lambda d: d.update(process_events=[]))
        case("FR-03 %s: no process event at all (each over [] is vacuous)" % cid, "MET", state(rules)[0],
             "the Git counts 15 and 25 are in audit_expect only")
    # 4. FR-12: the CF file's content.
    for label, content in (("content changed", "0x0:0x1"), ("content with a newline", "0x0:0x0\n")):
        root = WORLD + "/fr12-" + label.replace(" ", "-")
        rules = relocate(cmds["C17"]["expect"], root)
        build(rules, root, c17_extras)
        cfp = root + "/home/.CFUserTextEncoding"
        os.unlink(cfp)
        with open(cfp, "x") as s:
            s.write(content)
        case("FR-12 C17: CF file " + label, "NOT_MET", state(rules)[0])
    root = WORLD + "/fr12-absent"
    rules = relocate(cmds["C17"]["expect"], root)
    build(rules, root, c17_extras)
    os.unlink(root + "/home/.CFUserTextEncoding")
    case("FR-12 C17: CF file absent", "NOT_MET", state(rules)[0])
    root = WORLD + "/fr12-mode-0600"
    rules = relocate(cmds["C17"]["expect"], root)
    build(rules, root, c17_extras)
    os.chmod(root + "/home/.CFUserTextEncoding", 0o600)
    case("FR-12 C17: CF file mode 0o600, same content (the stated gap)", "MET", state(rules)[0], "mode is not expressible in expect")
    with open(root + "/home/.CFUserTextEncoding", "rb") as s:
        result["cf_synthetic_sha256"] = sha(s.read())
    # 5. main() on a mutated synthetic freeze, for each Node command's .P.
    for cid, probes_name in (("C16", "s7-001-c16-direct-probe-r1"), ("C17", "s7-001-c17-cohort"), ("C19", "s7-001-c19-direct-probe-r2")):
        root = WORLD + "/main-" + cid + "-established"
        rules = relocate(cmds[cid]["expect"], root)
        build(rules, root, c17_extras if cid == "C17" else None)
        rewrite_json(root + "/E/" + probes_name + ".probes.json",
                     lambda d: d["targets"][-1].update(state="present, identity established"))
        code, mstate, _ = main_expect({"commands": [dict(cmds[cid], expect=rules)]}, root, cid)
        case("main() %s with a .P target 'present, identity established'" % cid, [1, "NOT_MET"], [code, mstate])
    # 6. Phase prepared with P00 and a D02: A-7.
    def prepared(root, mutate=None):
        os.makedirs(root, exist_ok=False)
        p00 = cmds["P00"]
        rules = relocate(p00["expect"], root + "/w")
        build(rules, root + "/w")
        if mutate:
            mutate(root + "/w")
        anc, cur = [], root
        while True:
            info = os.lstat(cur)
            anc.append({"path": cur, "device": info.st_dev, "inode": info.st_ino, "mode": "0o%03o" % stat.S_IMODE(info.st_mode)})
            if cur == "/":
                break
            cur = os.path.dirname(cur)
        anc.sort(key=lambda r: r["path"])
        mask = os.umask(0o022)
        os.umask(mask)
        doc = {"boot_session_uuid": f["boot_session_uuid"], "umask": "0o%03o" % mask, "bindings": [], "trees": [],
               "host_facts": [], "evidence": {"parent": root, "ancestors": anc}, "preparation": {"entries": []},
               "absent_paths": {"after_preparation": []},
               "commands": [dict(p00, expect=rules), {"id": "D02", "phase": "preparation", "expect": []},
                            {"id": "C99", "phase": "capture", "expect": [{"file": root + "/nothing", "exists": True}]}]}
        path = root + "/synthetic-freeze-prepared.json"
        data = json.dumps(doc, sort_keys=True).encode("ascii")
        with open(path, "xb") as s:
            s.write(data)
        buffer = io.StringIO()
        saved = sys.argv
        sys.argv = ["w2f_s7_check.py", "--freeze", path, "--freeze-sha256", sha(data), "prepared"]
        try:
            with contextlib.redirect_stdout(buffer):
                code = NS["main"]()
        finally:
            sys.argv = saved
        report = json.loads(buffer.getvalue())
        return code, report["state"], len(report["checks"]["earlier_commands"])

    def stdout_path(w):
        return w + "/E/s7-001-p00-shasum.stdout.txt"

    def replace_stdout(text):
        def m(w):
            os.unlink(stdout_path(w))
            with open(stdout_path(w), "x") as s:
                s.write(text)
        return m
    ok_lines = ("FREEZE-002.json: OK\ns7/p00-freeze-001-rebound.sha256sums.txt: OK\n"
                "<local>/c271-p35/workers/W2-freeze-001/s7/w2f_s7_check.py: OK\n")
    case("phase prepared: P00's predicates evaluated (base)", [0, "MET", 12], list(prepared(WORLD + "/prepared-base")))
    case("phase prepared: P00 stdout holds a FAILED line", [1, "NOT_MET", 12],
         list(prepared(WORLD + "/prepared-failed", replace_stdout(ok_lines + "x: FAILED\n"))))
    case("phase prepared: P00 stdout lacks the checker's OK line", [1, "NOT_MET", 12],
         list(prepared(WORLD + "/prepared-no-checker", replace_stdout("FREEZE-002.json: OK\ns7/p00-freeze-001-rebound.sha256sums.txt: OK\n"))))

    def stderr_warning(w):
        p = w + "/E/s7-001-p00-shasum.stderr.txt"
        os.unlink(p)
        with open(p, "x") as s:
            s.write("shasum: WARNING: 1 line is improperly formatted\n")
    case("phase prepared: P00 stderr holds shasum's warning", [1, "NOT_MET", 12], list(prepared(WORLD + "/prepared-warning", stderr_warning)))
    # 7. Semantics of the checker that bear on appended predicates (FR-08), on literal documents.
    case("each over [] is vacuously true", True, evaluate_on({"x": []}, {"pointer": "/x", "each": {"pointer": "/s", "equals": "absent"}}))
    case("length+each in one rule evaluates length only", True,
         evaluate_on({"x": [{"s": "unknown"}]}, {"pointer": "/x", "length": 1, "each": {"pointer": "/s", "equals": "absent"}}))
    case("each with a missing pointer in an item fails", False, evaluate_on({"x": [{}]}, {"pointer": "/x", "each": {"pointer": "/s", "equals": "absent"}}))
    case("one_of is type-strict (1 is not true)", False, evaluate_on({"x": True}, {"pointer": "/x", "one_of": [1]}))
    result["summary"] = {"cases": len(result["cases"]), "as_expected": sum(1 for c in result["cases"] if c["as_expected"]),
                         "unexpected": [c for c in result["cases"] if not c["as_expected"]]}
    with open(sys.argv[1], "x") as s:
        json.dump(result, s, indent=1, sort_keys=True)
        s.write("\n")
    print(json.dumps(result["summary"], sort_keys=True)[:4000])


main()
