"""Freeze review 002, script 03: every command of freeze 002, and each against freeze 001.

Run: <worktree>/.venv/bin/python -I -S -B w3f2_03_commands.py OUTPUT.json LISTING.txt
Reads only; starts no process; writes OUTPUT.json and LISTING.txt only.
"""
import json
import os
import re
import sys

PROCESS_EVENTS = {"subprocess.Popen", "os.posix_spawn", "os.exec", "os.fork", "os.forkpty", "os.spawn", "os.system"}


def refuse(event, args):
    if event in PROCESS_EVENTS:
        raise PermissionError("no process: " + event)


sys.addaudithook(refuse)

P35 = "<local>/c271-p35"
E = P35 + "/evidence"
F1D = P35 + "/workers/W2-freeze-001"
F2D = P35 + "/workers/W2-freeze-002"
WRAPPER = P35 + "/director/run/run_once_v2.sh"
WT = "<worktree>"
PY = WT + "/.venv/bin/python"
TOOLS = WT + "/docs/engineering/localized-repair-c271/macos-qualification-p35/tooling"
CAPTURE = TOOLS + "/capture_probe.py"
CHECKER = F1D + "/s7/w2f_s7_check.py"
PH1, PH2 = "<FREEZE-001.json SHA-256>", "<FREEZE-002.json SHA-256>"
MC11PH = "<MC11 reviewed list SHA-256>"
MC11SHA = "aade03ac64a506678ce7ade184ecedcd10c5f6a58077d1f01aa7d0d70db63800"

FILE_KEYS = ("exists", "sha256", "text_equals", "text_includes", "text_excludes")
JSON_KEYS = ("absent", "argv_equals_except", "equals_freeze_sha256", "equals_sha256_of", "equals_from", "nonempty_string",
             "equals", "length", "each", "count_where", "one_of", "startswith", "includes")


def load(path):
    with open(path, "rb") as s:
        return json.loads(s.read())


def quote(items):
    return " ".join("'" + x + "'" for x in items)


def predicate_keys(rule, top=True):
    """The predicate keys of one rule, in the checker's order of evaluation; nested each/count_where too."""
    out = []
    if top:
        out += [k for k in FILE_KEYS if k in rule]
    out += [k for k in JSON_KEYS if k in rule]
    return out


def multi_key(rule, where, top=True):
    """Rules where the checker would evaluate only the first of several predicate keys (count_where+equals is one)."""
    found = []
    keys = predicate_keys(rule, top)
    effective = [k for k in keys if not (k == "equals" and "count_where" in rule)]
    if len(effective) > 1:
        found.append({"where": where, "keys": keys, "rule": rule})
    for k in ("each", "count_where"):
        if isinstance(rule.get(k), dict):
            found += multi_key(rule[k], where + "/" + k, top=False)
    return found


def subst(obj, pairs):
    text = json.dumps(obj, sort_keys=True)
    for a, b in pairs:
        text = text.replace(json.dumps(a)[1:-1], json.dumps(b)[1:-1])
    return json.loads(text)


def canon(obj):
    return json.dumps(obj, sort_keys=True)


def main():
    f1 = load(F1D + "/FREEZE-001.json")
    f2 = load(F2D + "/FREEZE-002.json")
    c1 = {c["id"]: c for c in f1["commands"]}
    c2 = {c["id"]: c for c in f2["commands"]}
    ids2 = [c["id"] for c in f2["commands"]]
    report = {"script": "w3f2_03_commands.py", "count_001": len(c1), "count_002": len(c2),
              "duplicate_ids": sorted({i for i in ids2 if ids2.count(i) > 1})}
    problems = []

    def bad(cid, what, **details):
        problems.append(dict({"id": cid, "what": what}, **details))

    envs = {name: load(row["path"]) for name, row in f2["environments"].items()}
    template = f2["launch"]["timer_template"]
    order = f2["order"]
    capture = f2["capture_commands"]
    report["order"] = {"count": len(order), "first": order[0], "unique": len(set(order)) == len(order),
                       "all_known": all(i in c2 for i in order),
                       "non_capture_in_order": sorted(i for i in c2 if c2[i]["phase"] != "capture" and i not in order),
                       "capture_in_order": [i for i in order if i in capture],
                       "capture_phase_ids": [i for i in ids2 if c2[i]["phase"] == "capture"] == capture,
                       "order_001_plus_P00": order == ["P00"] + f1["order"]}
    # Structural checks of every command.
    absent_before = set(f2["absent_paths"]["before_preparation"])
    absent_after = set(f2["absent_paths"]["after_preparation"])
    placeholder_re = re.compile(r"^<[^>]+>$")
    listing = []
    for c in f2["commands"]:
        cid = c["id"]
        name = c["name"]
        recs = {k: E + "/" + name + "." + s for k, s in
                (("stdout", "stdout.txt"), ("stderr", "stderr.txt"), ("exit", "exit.txt"), ("command", "command.json"))}
        if c["records"] != recs:
            bad(cid, "records are not the wrapper's four paths", records=c["records"])
        want_wrapper = ["/bin/sh", WRAPPER, name, c["cwd"], c["environment"]["file"], "--"] + c["argv"]
        if c["wrapper_argv"] != want_wrapper:
            bad(cid, "wrapper_argv is not the wrapper prefix plus argv")
        if any("'" in x for x in c["wrapper_argv"]):
            bad(cid, "an element holds a single quote")
        if c["shell"] != quote(c["wrapper_argv"]):
            bad(cid, "shell is not the single-quoted wrapper_argv")
        want_timer = template.replace("{exit_file}", c["records"]["exit"]).replace("{bound}", str(c["limits"]["outer_bound_s"]))
        if c.get("timer_shell") != want_timer:
            bad(cid, "timer_shell is not the template with this command's exit file and bound")
        if type(c["limits"].get("outer_bound_s")) is not int or c["limits"]["outer_bound_s"] <= 0:
            bad(cid, "outer_bound_s not a positive integer")
        # Environment: env -i NAME=VALUE ... PROGRAM, equal to the environment file.
        argv = c["argv"]
        if argv[:2] != ["/usr/bin/env", "-i"]:
            bad(cid, "argv does not start with env -i")
        else:
            i, assigned = 2, {}
            while i < len(argv) and "=" in argv[i] and not argv[i].startswith("/"):
                k, v = argv[i].split("=", 1)
                assigned[k] = v
                i += 1
            envdoc = envs[c["environment"]["name"]]
            if assigned != envdoc["environment"]:
                bad(cid, "env -i assignments differ from the environment file", assigned=assigned)
            if c["environment"]["sha256"] != f2["environments"][c["environment"]["name"]]["sha256"] or \
                    c["environment"]["file"] != f2["environments"][c["environment"]["name"]]["path"]:
                bad(cid, "environment reference differs from environments")
            program = argv[i] if i < len(argv) else None
            if program in (PY,) or (program or "").endswith(("/python", "/python3", "/python3.12")):
                flags = []
                j = i + 1
                while j < len(argv) and argv[j].startswith("-") and argv[j] not in ("-c", "-m"):
                    flags.append(argv[j])
                    j += 1
                if "-B" not in flags:
                    bad(cid, "a Python start without -B", flags=flags)
        # Placeholders.
        phs = [(n, x) for n, x in enumerate(argv) if placeholder_re.match(x)]
        declared = [(d["argv_index"], d["placeholder"]) for d in c["deferred_arguments"]]
        if sorted(phs) != sorted(declared):
            bad(cid, "placeholders differ from deferred_arguments", found=phs, declared=declared)
        for d in c["deferred_arguments"]:
            if d["wrapper_argv_index"] != d["argv_index"] + 6 or c["wrapper_argv"][d["wrapper_argv_index"]] != d["placeholder"]:
                bad(cid, "wrapper_argv_index wrong", d=d)
            if d["placeholder"] not in f2["deferred_arguments"]:
                bad(cid, "placeholder not in the freeze's deferred_arguments", d=d)
        # Absent paths.
        own = set(c["records"].values()) | set(c["outputs"])
        if set(c["outputs_absent_before"]) != own:
            bad(cid, "outputs_absent_before is not records plus outputs",
                extra=sorted(set(c["outputs_absent_before"]) - own), missing=sorted(own - set(c["outputs_absent_before"])))
        exempt_before = cid in ("P00", "P01")
        exempt_after = cid in ("P00", "P01", "P02", "P03", "P04", "P05", "D01", "D02")
        for p in own:
            if not exempt_before and p not in absent_before:
                bad(cid, "path not in before_preparation", path=p)
            if not exempt_after and p not in absent_after:
                bad(cid, "path not in after_preparation", path=p)
            if exempt_before and p in absent_before:
                bad(cid, "own record unexpectedly in before_preparation", path=p)
        # Multi-key rules.
        for set_name in ("expect", "audit_expect"):
            for n, rule in enumerate(c[set_name]):
                for item in multi_key(rule, cid + "/" + set_name + "/" + str(n)):
                    bad(cid, "rule with several predicate keys", **item)
        listing.append("%-9s %-11s bound=%-4s cwd=%s env=%s outputs=%d expect=%d audit=%d defer=%s" % (
            cid, c["phase"], c["limits"]["outer_bound_s"], c["cwd"].replace(P35, "<P35>").replace(WT, "<WT>"),
            c["environment"]["name"], len(c["outputs"]), len(c["expect"]), len(c["audit_expect"]),
            [d["placeholder"] for d in c["deferred_arguments"]]))
        listing.append("    argv: " + " ".join(x.replace(P35, "<P35>").replace(WT, "<WT>") for x in argv))
    # Comparison with freeze 001.
    comp = {"identical_argv_wrapper_shell": [], "changed": {}, "fields_changed": {}}
    for cid, old in c1.items():
        new = c2.get(cid)
        if new is None:
            bad(cid, "command of freeze 001 missing in freeze 002")
            continue
        fields = sorted(k for k in set(old) | set(new) if old.get(k) != new.get(k))
        comp["fields_changed"][cid] = fields
        if old["argv"] == new["argv"] and old["wrapper_argv"] == new["wrapper_argv"] and old["shell"] == new["shell"]:
            comp["identical_argv_wrapper_shell"].append(cid)
        else:
            diffs = [[n, a, b] for n, (a, b) in enumerate(zip(old["argv"], new["argv"])) if a != b]
            comp["changed"][cid] = {"len_old": len(old["argv"]), "len_new": len(new["argv"]), "argv_diffs": diffs,
                                    "wrapper_diffs": [[n, a, b] for n, (a, b) in enumerate(zip(old["wrapper_argv"], new["wrapper_argv"])) if a != b]}
            allowed = {(F1D + "/FREEZE-001.json", F2D + "/FREEZE-002.json"), (PH1, PH2), (MC11PH, MC11SHA)}
            if len(old["argv"]) != len(new["argv"]) or any((a, b) not in allowed for _, a, b in diffs):
                bad(cid, "argv changed beyond the stated substitutions", diffs=diffs)
    report["comparison"] = {"identical_count": len(comp["identical_argv_wrapper_shell"]),
                            "identical": comp["identical_argv_wrapper_shell"], "changed": comp["changed"],
                            "fields_changed": comp["fields_changed"]}
    # The difference record's claims about fields.
    diff = load(F2D + "/FREEZE-002-DIFFERENCES.json")
    claimed = {row["id"]: sorted(row.get("changed_fields", [])) for row in diff["mechanical"]["commands"]["changed"]
               if "changed_fields" in row}
    only_timer = diff["mechanical"]["commands"]["only_timer_shell_added"]
    mismatch = []
    for cid, fields in comp["fields_changed"].items():
        if cid in claimed:
            if fields != claimed[cid]:
                mismatch.append({"id": cid, "observed": fields, "claimed": claimed[cid]})
        elif cid in only_timer:
            if fields != ["timer_shell"]:
                mismatch.append({"id": cid, "observed": fields, "claimed": ["timer_shell"]})
        else:
            mismatch.append({"id": cid, "observed": fields, "claimed": None})
    report["difference_record_field_claims_mismatch"] = mismatch
    # Expect composition of the main commands.
    comp_rows = {}
    for n in range(1, 20):
        cid = "C%02d" % n
        old, new = c1[cid]["expect"], c2[cid]["expect"]
        L = c2[cid + ".L"]["expect"]
        P = c2[cid + ".P"]["expect"] if cid + ".P" in c2 else []
        row = {"old": len(old), "new": len(new), "L": len(L), "P": len(P),
               "L_unchanged_from_001": c1[cid + ".L"]["expect"] == L,
               "P_unchanged_from_001": (c1[cid + ".P"]["expect"] == P) if cid + ".P" in c1 else None}
        tail = L + P
        row["ends_with_L_then_P_in_full"] = [canon(r) for r in new[len(new) - len(tail):]] == [canon(r) for r in tail]
        head = new[:len(new) - len(tail)]
        if cid == "C01":
            # The old wrapper rules are rebuilt: compare after the stated substitution, minus equals_sha256_of.
            old_sub = [r for r in subst(old, [(MC11PH, MC11SHA)]) if "equals_sha256_of" not in r]
            for r in old_sub:
                if "argv_equals_except" in r:
                    r["argv_equals_except"]["indices"] = [i for i in r["argv_equals_except"]["indices"] if i != 25]
            row["head_equals_old_after_substitution"] = sorted(canon(r) for r in head) == sorted(canon(r) for r in old_sub)
            row["head_in_old_order"] = [canon(r) for r in head] == [canon(r) for r in old_sub]
            row["removed_from_old"] = [r for r in old if "equals_sha256_of" in r]
            row["inserted"] = []
        else:
            row["old_is_prefix"] = [canon(r) for r in head[:len(old)]] == [canon(r) for r in old]
            row["inserted"] = head[len(old):]
        comp_rows[cid] = row
        if not row["ends_with_L_then_P_in_full"]:
            bad(cid, "expect does not end with the .L's and .P's predicates in full")
        if cid != "C01" and not row["old_is_prefix"]:
            bad(cid, "freeze 001's expect is not kept as the prefix")
        if not row["L_unchanged_from_001"] or row["P_unchanged_from_001"] is False:
            bad(cid, ".L or .P expect changed from freeze 001")
    report["main_expect_composition"] = comp_rows
    # Rebuilt wrapper predicates: P01, D02, Q04 and every .X.
    rebuilt = {}
    for cid in ["P01", "D02", "Q04"] + ["C%02d.X" % n for n in range(1, 20)]:
        old_sub = subst(c1[cid]["expect"], [(F1D + "/FREEZE-001.json", F2D + "/FREEZE-002.json"), (PH1, PH2)])
        new = c2[cid]["expect"]
        rebuilt[cid] = {"equal_after_substitution": [canon(r) for r in old_sub] == [canon(r) for r in new],
                        "equal_as_multiset": sorted(canon(r) for r in old_sub) == sorted(canon(r) for r in new)}
        if not rebuilt[cid]["equal_as_multiset"]:
            bad(cid, "rebuilt expect differs from freeze 001's beyond the substitution")
        for k in ("classification", "audit_expect", "limits", "starts", "purpose", "outputs", "records", "cwd", "environment"):
            if subst(c1[cid].get(k), [(F1D + "/FREEZE-001.json", F2D + "/FREEZE-002.json"), (PH1, PH2), ("FREEZE-001", "FREEZE-002"),
                                     ("freeze review 001", "freeze review 002")]) != c2[cid].get(k) and c1[cid].get(k) != c2[cid].get(k):
                rebuilt[cid].setdefault("other_fields_changed", []).append(k)
    report["rebuilt_wrapper_predicates"] = rebuilt
    report["problems"] = problems
    with open(sys.argv[1], "x") as s:
        json.dump(report, s, indent=1, sort_keys=True)
        s.write("\n")
    with open(sys.argv[2], "x") as s:
        s.write("\n".join(listing) + "\n")
    print(json.dumps({"commands": len(c2), "problems": len(problems), "identical": len(comp["identical_argv_wrapper_shell"]),
                      "changed": sorted(comp["changed"]), "field_claim_mismatch": len(mismatch),
                      "order": report["order"]}, sort_keys=True))


main()
