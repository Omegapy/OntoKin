"""W2 (freeze 001): the author's self-check of FREEZE-001.json. It starts no process and writes only OUTPUT.

Usage: python3 -I -S -B w2f_selfcheck.py FREEZE CHECKER MH_FREEZE_002 SELFTEST_DIR VALIDATION_DIR OUTPUT

1. Shape: every command's keys; ORDER covers every non-overrun command; names unique; records under <E>.
2. Every shell member splits (POSIX rules) back into its wrapper_argv, which is the wrapper, the name, the cwd, the
   environment file, '--' and the argv; every argv element is free of single quotes and line ends.
3. Every timer_shell is MH's timer template with this command's exit file and bound (MH's FREEZE-002 /launch).
4. Every deferred placeholder occurs in its command, and nowhere else; every env -i list equals its environment file.
5. Every predicate has a form that the checker evaluates (no silent False from an unknown form); every file a
   predicate names is a bound input, an existing frozen file, a host fact, or an S7 path in absent_paths.
6. Every binding's SHA-256, size and mode equal the file now.
7. The checker's own predicate evaluator (loaded from its file) applied to substitute files: the collector's and the
   comparator's predicates of R2 on outputs of the same tools for main's runs, so that every pointer resolves.
"""
import sys

if not sys.flags.dont_write_bytecode:
    raise SystemExit("run with -B")
import hashlib
import importlib.util
import json
import os
import shlex
import stat

freeze_path, checker_path, mh_freeze, selftest_dir, validation_dir, output = sys.argv[1:7]
if os.path.lexists(output):
    raise SystemExit("output exists")
freeze = json.load(open(freeze_path))
results = []


def check(name, condition, detail=None):
    results.append({"check": name, "ok": bool(condition), **({"detail": detail} if detail is not None else {})})


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


E = freeze["evidence"]["parent"]
commands = freeze["commands"]
ids = [c["id"] for c in commands]
names = [c["name"] for c in commands]
check("ids unique", len(ids) == len(set(ids)))
check("names unique", len(names) == len(set(names)))
check("order covers every non-overrun command", sorted(freeze["order"]) == sorted(c["id"] for c in commands if c["phase"] != "overrun"))
wrapper = freeze["wrapper"]["path"]
template = json.load(open(mh_freeze))["launch"]["timer_template"]
envs = {name: json.load(open(row["file"]))["environment"] for name, row in freeze["environments"].items()}
placeholders = [row["placeholder"] for row in freeze["deferred_arguments"]["rows"]]
for c in commands:
    w = c["wrapper_argv"]
    check(c["id"] + ": wrapper argv", w[:6] == ["/bin/sh", wrapper, c["name"], c["cwd"], c["environment"]["file"], "--"] and w[6:] == c["argv"])
    check(c["id"] + ": shell splits to wrapper argv", shlex.split(c["shell"], posix=True) == w)
    check(c["id"] + ": no quote or line end in argv", all("'" not in a and "\n" not in a for a in w))
    check(c["id"] + ": timer is MH's template", c["timer_shell"] == template.replace("{exit_file}", c["records"]["exit"]).replace("{bound}", str(c["limits"]["outer_bound_s"])))
    rec = c["records"]
    check(c["id"] + ": records under the evidence parent", all(v == E + "/" + c["name"] + "." + k for k, v in
                                                              {"stdout.txt": rec["stdout"], "stderr.txt": rec["stderr"], "exit.txt": rec["exit"], "command.json": rec["command"]}.items()))
    env = envs[c["environment"]["name"]]
    head = ["/usr/bin/env", "-i"] + [k + "=" + v for k, v in sorted(env.items())]
    check(c["id"] + ": env -i list equals its environment file", c["argv"][:len(head)] == head and not c["argv"][len(head)].count("="))
    check(c["id"] + ": environment file digest", sha256(c["environment"]["file"]) == c["environment"]["sha256"])
    used = {p for p in placeholders if any(p in a for a in c["argv"])}
    declared = {row["placeholder"] for row in c["deferred_arguments"]}
    check(c["id"] + ": deferred placeholders declared", used == declared, sorted(used ^ declared))
    if any(a.endswith("/python") for a in c["argv"]) or any("python" in a.rsplit("/", 1)[-1] for a in c["argv"][:12]):
        i = next((n for n, a in enumerate(c["argv"]) if a.endswith(".venv/bin/python")), None)
        if i is not None:
            check(c["id"] + ": interpreter start carries -B", "-B" in c["argv"][i + 1:i + 4])
for row in freeze["deferred_arguments"]["rows"]:
    users = sorted(c["id"] for c in commands if any(row["placeholder"] in a for a in c["argv"]))
    check("placeholder used exactly by its rows: " + row["placeholder"], set(users) <= set(row["used_by"]) and set(users) >= set(u for u in row["used_by"]), users)

spec = importlib.util.spec_from_file_location("w2f_checker", checker_path)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)
FORMS = [{"argv_equals_except"}, {"equals_freeze_sha256"}, {"equals_sha256_of"}, {"equals_from"}, {"equals"}, {"length"},
         {"each"}, {"count_where", "equals"}, {"one_of"}, {"startswith"}, {"includes"}, {"absent"}]
FILE_FORMS = [{"exists"}, {"sha256"}, {"text_equals"}, {"text_includes"}, {"text_excludes"}]


def valid(rule, top=True):
    keys = set(rule) - {"file", "pointer", "jsonl_last"}
    if top and keys in FILE_FORMS:
        return "pointer" not in rule
    if keys not in FORMS:
        return False
    if "each" in rule:
        return valid(rule["each"], top=False)
    if "count_where" in rule:
        return valid(rule["count_where"], top=False)
    return True


absent = set(freeze["absent_paths"]["before_preparation"]) | set(freeze["absent_paths"]["after_preparation"])
for c in commands:
    absent |= set(c["outputs_absent_before"])
known = {row["path"] for row in freeze["bindings"]} | {row["path"] for row in freeze["host_facts"]} | \
        {row["path"] for row in freeze["deferred_inputs"]}
s7_prefixes = tuple(sorted(c["outputs"][0] + "/" for c in commands if c["outputs"] and c["id"] in ("R1", "R2", "D01")))
bad_forms, bad_files = [], []
for c in commands:
    for key in ("expect", "audit_expect"):
        for rule in c[key]:
            if not valid(rule):
                bad_forms.append([c["id"], key, rule])
            path = rule.get("file")
            for ref in [rule.get("equals_sha256_of"), (rule.get("equals_from") or {}).get("file")] + [path]:
                if ref is None:
                    continue
                if not (ref in known or ref in absent or ref.startswith(s7_prefixes) or os.path.isfile(ref)):
                    bad_files.append([c["id"], key, ref])
check("every predicate has an evaluable form", not bad_forms, bad_forms[:5])
check("every predicate's file is known, bound or an S7 path", not bad_files, bad_files[:5])
for row in freeze["bindings"] + freeze["host_facts"]:
    info = os.lstat(row["path"])
    ok = (sha256(row["path"]) == row["sha256"] and info.st_size == row["size_bytes"] and "0o%03o" % stat.S_IMODE(info.st_mode) == row["mode"]
          and (not row.get("nlink_one") or info.st_nlink == 1))
    check("binding now: " + row["id"], ok)
check("absent paths absent now", not [p for p in freeze["absent_paths"]["before_preparation"] if os.path.lexists(p)])
check("no S7 output path exists", not [p for p in absent if os.path.lexists(p)])

# 7. The checker's evaluator on substitute files (outputs of the same tools for main's runs).
by_id = {c["id"]: c for c in commands}
substitutes = {
    E + "/mr-001-r2.compare-main.json": os.path.join(selftest_dir, "compare-main-default-self-r2attr.json"),
    E + "/mr-001-r1.compare-main.json": os.path.join(selftest_dir, "compare-main-resolved-self-r1attr.json"),
    E + "/mr-001-r1.unit-outcomes.json": os.path.join(selftest_dir, "collect-main-resolved-with-r1-args.json"),
    E + "/mr-001-r2.unit-outcomes.json": os.path.join(selftest_dir, "collect-main-default-with-r2-args.json")}
resolution = []
for ident in ("R1", "R2"):
    for rule in by_id[ident]["audit_expect"] + by_id[ident]["expect"]:
        if rule.get("file") not in substitutes or "pointer" not in rule:
            continue
        local = dict(rule, file=substitutes[rule["file"]])
        document = json.load(open(local["file"]))
        found, _ = checker.pointer(document, rule["pointer"])
        outcome = checker.check_predicate(local, {})
        resolution.append({"command": ident, "pointer": rule["pointer"], "resolves": found or bool(rule.get("absent")),
                           "holds_on_substitute": outcome["ok"]})
unresolved = [r for r in resolution if not r["resolves"]]
check("every collector and comparator pointer resolves on a substitute output", not unresolved, unresolved[:10])
document = {"schema": "ontokin.c271.p36-w2-freeze-selfcheck/1", "freeze": {"path": freeze_path, "sha256": sha256(freeze_path)},
            "checks": results, "failed": [r for r in results if not r["ok"]], "pointer_resolution": resolution,
            "substitutes": substitutes,
            "note": "holds_on_substitute is informational: the substitutes are main's runs, not R1 or R2"}
fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
with os.fdopen(fd, "w") as stream:
    stream.write(json.dumps(document, indent=1) + "\n")
print(json.dumps({"checks": len(results), "failed": len(document["failed"]), "pointers": len(resolution),
                  "unresolved": len(unresolved)}))
for row in document["failed"][:20]:
    print(json.dumps(row)[:400])
