"""W3 freeze review 001, script 03: structural checks of the 71 commands and a compact listing.

Checks: shell == single-quoted wrapper_argv; wrapper_argv = wrapper prefix + argv; placeholder
indices; -B on every Python start; env -i assignments equal the environment file; records and
outputs in the absent lists; predicate key combinations the checker would partly ignore.
Reads only; writes records into OUT/records.
"""
import json
import os
import sys

FREEZE = sys.argv[1]
OUT = sys.argv[2]
E = "<local>/c271-p35/evidence/"

with open(FREEZE, "rb") as f:
    fz = json.loads(f.read())


def q(s):
    return "'" + s.replace("'", "'\\''") + "'"


issues = []
lines = []
pred_keysets = {}
absent_before = set(fz["absent_paths"]["before_preparation"])
absent_after = set(fz["absent_paths"]["after_preparation"])
prepared_paths = {e["path"] for e in fz["preparation"]["entries"]}
order = fz["order"]
cmds = {c["id"]: c for c in fz["commands"]}
if [c["id"] for c in fz["commands"]] != order:
    issues.append(("ORDER", "commands list order differs from order"))
envs = {v["path"]: (k, v) for k, v in fz["environments"].items()}
PRED_KEYS = {"argv_equals_except", "equals_freeze_sha256", "equals_sha256_of", "equals_from", "nonempty_string",
             "equals", "length", "each", "count_where", "one_of", "startswith", "includes", "absent", "exists",
             "sha256", "text_equals", "text_includes", "text_excludes"}
STRUCT_KEYS = {"file", "pointer", "jsonl_last", "note", "why"}


def walk_rule(rule, cid, where):
    keys = frozenset(k for k in rule)
    pred_keysets.setdefault(keys, []).append((cid, where))
    for sub in ("each", "count_where"):
        if sub in rule and isinstance(rule[sub], dict):
            walk_rule(rule[sub], cid, where + "/" + sub)


all_files_read = set()
for c in fz["commands"]:
    cid = c["id"]
    wa, argv = c["wrapper_argv"], c["argv"]
    # shell quoting
    if c["shell"] != " ".join(q(a) for a in wa):
        issues.append((cid, "shell != quoted wrapper_argv"))
    # wrapper prefix
    pre = ["/bin/sh", fz["wrapper"]["path"], c["name"], c["cwd"], c["environment"]["file"], "--"]
    if wa[:6] != pre:
        issues.append((cid, "wrapper prefix differs", wa[:6]))
    if wa[6:] != argv:
        issues.append((cid, "wrapper_argv[6:] != argv"))
    # env file
    ef = c["environment"]["file"]
    if ef not in envs:
        issues.append((cid, "environment file not frozen", ef))
    else:
        ename, env = envs[ef]
        if env["sha256"] != c["environment"]["sha256"] or ename != c["environment"]["name"]:
            issues.append((cid, "environment name/sha differs"))
    # deferred
    declared_idx = {}
    for d in c["deferred_arguments"]:
        if argv[d["argv_index"]] != d["placeholder"] or wa[d["wrapper_argv_index"]] != d["placeholder"]:
            issues.append((cid, "placeholder index wrong", d))
        if d["wrapper_argv_index"] != d["argv_index"] + 6:
            issues.append((cid, "wrapper index offset", d))
        if d["placeholder"] not in fz["deferred_arguments"]:
            issues.append((cid, "undeclared placeholder", d["placeholder"]))
        declared_idx[d["argv_index"]] = d["placeholder"]
    for i, a in enumerate(argv):
        if a.startswith("<") and a.endswith(">") and i not in declared_idx:
            issues.append((cid, "undeclared placeholder-like argv", i, a))
        if "<" in a and ">" in a and i not in declared_idx:
            issues.append((cid, "NOTE argv element with <...>", i, a))
    # env -i assignments
    envassign = {}
    exe_index = None
    if argv[:2] == ["/usr/bin/env", "-i"]:
        i = 2
        while i < len(argv) and "=" in argv[i] and not argv[i].startswith("/"):
            k, v = argv[i].split("=", 1)
            envassign[k] = v
            i += 1
        exe_index = i
        if ef in envs and envassign != envs[ef][1]["environment"]:
            issues.append((cid, "env -i assignments differ from the environment file", sorted(set(envassign) ^ set(envs[ef][1]["environment"])),
                           {k: (envassign.get(k), envs[ef][1]["environment"].get(k)) for k in set(envassign) | set(envs[ef][1]["environment"]) if envassign.get(k) != envs[ef][1]["environment"].get(k)}))
    else:
        exe_index = 0
        issues.append((cid, "NOTE argv does not start with env -i", argv[:3]))
    exe = argv[exe_index] if exe_index is not None and exe_index < len(argv) else None
    flags = []
    if exe and ("python" in os.path.basename(exe)):
        j = exe_index + 1
        while j < len(argv) and argv[j].startswith("-") and argv[j] not in ("-m",):
            flags.append(argv[j])
            j += 1
        if "-B" not in flags:
            issues.append((cid, "Python start without -B", argv[exe_index:exe_index + 4]))
    # records & outputs absent
    recs = c["records"]
    for k in ("command", "exit", "stderr", "stdout"):
        if recs[k] != E + c["name"] + "." + {"command": "command.json", "exit": "exit.txt", "stderr": "stderr.txt", "stdout": "stdout.txt"}[k]:
            issues.append((cid, "record path", k, recs[k]))
    oab = set(c["outputs_absent_before"])
    for p in list(recs.values()) + list(c["outputs"]):
        if p not in oab:
            issues.append((cid, "record/output not in outputs_absent_before", p))
    for p in oab:
        if p not in absent_before:
            issues.append((cid, "outputs_absent_before not in before_preparation", p))
        if c["phase"] not in ("precondition",) and cid not in ("D01",) and p not in absent_after:
            issues.append((cid, "outputs_absent_before not in after_preparation", p))
        if p in prepared_paths:
            issues.append((cid, "output is a prepared path", p))
    # predicates
    for where in ("expect", "audit_expect"):
        for n, r in enumerate(c[where]):
            walk_rule(r, cid, "%s[%d]" % (where, n))
            if "file" in r:
                all_files_read.add(r["file"])
    # compact listing
    lines.append("=" * 100)
    lines.append("%s  %s  phase=%s  control=%s  env=%s  cwd=%s" % (cid, c["name"], c["phase"], c.get("control"), c["environment"]["name"], c["cwd"]))
    lines.append("  argv: " + " ".join(a.replace("<local>", "<L>").replace("<worktree>", "<W>") for a in argv[exe_index:] if exe_index is not None))
    lines.append("  envassign: " + json.dumps(envassign))
    lines.append("  flags: %s  limits: %s  starts: %s" % (flags, json.dumps(c["limits"]), json.dumps(c["starts"])))
    lines.append("  outputs: " + json.dumps([o.replace(E, "<E>/") for o in c["outputs"]]))
    lines.append("  failure_capture: " + json.dumps(c["failure_capture"])[:600])
    lines.append("  purpose: " + c.get("purpose", ""))
    for cl in c["classification"]:
        lines.append("  CLASS: %s -> %s" % (cl.get("outcome"), cl.get("class")))
    other = set(c) - {"argv", "audit_expect", "classification", "control", "cwd", "deferred_arguments", "environment", "expect", "failure_capture", "id", "limits", "name", "outputs", "outputs_absent_before", "phase", "purpose", "records", "shell", "starts", "wrapper_argv"}
    if other:
        lines.append("  OTHER KEYS: " + json.dumps({k: c[k] for k in other})[:1500])
    for where in ("expect", "audit_expect"):
        for r in c[where]:
            rr = dict(r)
            fn = rr.pop("file", "").replace(E, "<E>/").replace("<local>", "<L>")
            if "argv_equals_except" in rr:
                rr["argv_equals_except"] = {"indices": rr["argv_equals_except"]["indices"], "len": len(rr["argv_equals_except"]["argv"]),
                                            "same_as_argv": rr["argv_equals_except"]["argv"] == argv}
            s = json.dumps(rr, ensure_ascii=False)
            if len(s) > 700:
                s = s[:700] + "..."
            lines.append("  %s %s :: %s" % ("X" if where == "expect" else "A", fn, s))

# absent list consistency
summary = {
    "before_preparation": len(absent_before), "after_preparation": len(absent_after),
    "after_minus_before": sorted(absent_after - absent_before),
    "before_minus_after": sorted(p.replace(E, "<E>/") for p in absent_before - absent_after),
    "prepared_in_after": sorted(p for p in prepared_paths if p in absent_after),
    "prepared_in_before": len([p for p in prepared_paths if p in absent_before]),
    "prepared_count": {"dirs": sum(1 for e in fz["preparation"]["entries"] if e["kind"] == "directory"),
                       "files": sum(1 for e in fz["preparation"]["entries"] if e["kind"] == "file")},
}
# every absent path must be named by some command or prepared entry
named = set()
for c in fz["commands"]:
    named |= set(c["outputs_absent_before"])
named |= prepared_paths
summary["absent_not_named_by_any_command_or_preparation"] = sorted(p.replace(E, "<E>/") for p in (absent_before | absent_after) - named)
summary["absent_under_evidence"] = all(p.startswith(E) for p in absent_before | absent_after)

keysets = [{"keys": sorted(k), "count": len(v), "examples": v[:3]} for k, v in pred_keysets.items()]
multi = []
for k, v in pred_keysets.items():
    pk = set(k) & PRED_KEYS
    unknown = set(k) - PRED_KEYS - STRUCT_KEYS
    if len(pk) > 1 or unknown or not pk:
        multi.append({"keys": sorted(k), "pred_keys": sorted(pk), "unknown": sorted(unknown), "count": len(v), "examples": v[:5]})

with open(os.path.join(OUT, "records", "03-commands.txt"), "x", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
with open(os.path.join(OUT, "records", "03-commands-checks.json"), "x", encoding="utf-8") as f:
    json.dump({"issues": issues, "summary": summary, "keysets": keysets, "multi_or_unknown_predicate_keys": multi,
               "files_read_by_predicates": sorted(all_files_read)}, f, indent=1)
    f.write("\n")
print("commands", len(fz["commands"]), "issues", len(issues))
for i in issues:
    print("ISSUE", json.dumps(i)[:600])
print(json.dumps(summary, indent=1)[:6000])
print("MULTI/UNKNOWN predicate key sets:")
for m in multi:
    print(json.dumps(m)[:800])
