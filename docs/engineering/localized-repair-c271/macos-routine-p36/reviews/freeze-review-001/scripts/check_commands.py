"""Check each frozen command's shell member, wrapper argv, environment file and timer (read only).

Usage: python3 -I -S -B check_commands.py FREEZE OUT.json
"""
import hashlib, json, re, shlex, sys

freeze = json.load(open(sys.argv[1], "rb"))
destination = sys.argv[2]
wrapper = freeze["wrapper"]["path"]
problems, rows = [], []
for c in freeze["commands"]:
    p = []
    split = shlex.split(c["shell"])
    if split != c["wrapper_argv"]:
        p.append("shell member does not split to wrapper_argv")
    w = c["wrapper_argv"]
    if w[:2] != ["/bin/sh", wrapper] or w[2] != c["name"] or w[3] != c["cwd"] or w[5] != "--":
        p.append("wrapper argv head differs")
    if w[4] != c["environment"]["file"]:
        p.append("environment file differs")
    if w[6:] != c["argv"]:
        p.append("wrapper argv tail differs from argv")
    env_raw = open(c["environment"]["file"], "rb").read()
    if hashlib.sha256(env_raw).hexdigest() != c["environment"]["sha256"]:
        p.append("environment file digest differs")
    declared = json.loads(env_raw)["environment"]
    if c["argv"][:2] != ["/usr/bin/env", "-i"]:
        p.append("argv does not start with env -i")
    assignments = {}
    for item in c["argv"][2:]:
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", item):
            name, value = item.split("=", 1)
            assignments[name] = value
        else:
            break
    if assignments != declared:
        p.append("env -i assignments differ from the environment file: %s vs %s" % (sorted(assignments), sorted(declared)))
    timer = c["timer_shell"]
    match = re.match(r"f='([^']*)'; b=(\d+);", timer)
    if not match or match.group(1) != c["records"]["exit"] or int(match.group(2)) != c["limits"]["outer_bound_s"]:
        p.append("timer exit file or bound differs")
    for placeholder in re.findall(r"<[^<>]*SHA-256>|<R1 [a-z ]+>", c["shell"]):
        if placeholder not in [row["placeholder"] for row in freeze["deferred_arguments"]["rows"]]:
            p.append("unknown placeholder " + placeholder)
    if any(x in c["shell"] for x in ("$(", "`", ";", "&&", "||", "|")) and c["id"] not in ("R1.F", "R1.N"):
        # the cohort scripts are one quoted /bin/sh -c word; others must be simple
        if not all(x not in " ".join(shlex.quote(a) for a in c["wrapper_argv"]) for x in ("$(", "`")):
            p.append("shell metacharacters outside quoting")
    rows.append({"id": c["id"], "ok": not p, "problems": p})
    problems += [(c["id"], x) for x in p]
out = {"commands": len(rows), "ok": sum(r["ok"] for r in rows), "problems": problems,
       "order_ids_exist": all(i in {c["id"] for c in freeze["commands"]} for i in freeze["order"]),
       "commands_not_in_order": sorted({c["id"] for c in freeze["commands"]} - set(freeze["order"]))}
with open(destination, "x") as fh:
    json.dump(out, fh, indent=1)
    fh.write("\n")
print(json.dumps(out, indent=1)[:3000])
