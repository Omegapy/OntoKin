"""Freeze review 002, script 10: P00's two lists, and what S7 runs or reads that they and the bindings cover.

1. The second list: its digest lines equal freeze 001's SHA256SUMS.txt lines for exactly the documents that
   freeze 002 rebinds from freeze 001 (bindings under W2-freeze-001), with the path made absolute.
2. The first list covers every file of freeze 002 (none unlisted), the second list among them.
3. The preparation's counts (FR-05).
4. Every absolute path in every command's argv, cwd and environment file, classified: in P00's lists, bound,
   under the evidence parent, an OS path, or in the worktree / MP's trees / plan 001.

Run: <worktree>/.venv/bin/python -I -S -B w3f2_10_p00_lists.py OUTPUT.json
"""
import json
import os
import sys

PROCESS_EVENTS = {"subprocess.Popen", "os.posix_spawn", "os.exec", "os.fork", "os.forkpty", "os.spawn", "os.system"}


def refuse(event, args):
    if event in PROCESS_EVENTS:
        raise PermissionError("no process: " + event)


sys.addaudithook(refuse)

P35 = "<local>/c271-p35"
F1D = P35 + "/workers/W2-freeze-001"
F2D = P35 + "/workers/W2-freeze-002"
E = P35 + "/evidence"
WT = "<worktree>"


def lines(path):
    with open(path, "rb") as s:
        return s.read().decode("utf-8").splitlines()


def main():
    with open(F2D + "/FREEZE-002.json", "rb") as s:
        f = json.loads(s.read())
    out = {"script": "w3f2_10_p00_lists.py"}
    second = lines(F2D + "/s7/p00-freeze-001-rebound.sha256sums.txt")
    comments = [x for x in second if x.startswith("#")]
    digest_lines = [x for x in second if not x.startswith("#")]
    f1_lines = {x.split("  ", 1)[1]: x for x in lines(F1D + "/SHA256SUMS.txt")}
    rebound = [b for b in f["bindings"] if b["path"].startswith(F1D + "/")]
    want = [f1_lines[b["path"][len(F1D) + 1:]].split("  ", 1)[0] + "  " + b["path"] for b in rebound]
    out["second_list"] = {"lines": len(second), "comments": len(comments), "digest_lines": len(digest_lines),
                          "blank_lines": sum(1 for x in second if not x.strip()),
                          "rebound_bindings": len(rebound),
                          "equals_freeze_001_lines_for_the_rebound_documents": sorted(digest_lines) == sorted(want),
                          "same_order_as_bindings": digest_lines == want,
                          "digests_equal_bindings": all(l.split("  ", 1)[0] == b["sha256"] for l, b in zip(want, rebound)),
                          "rebound_not_listed": sorted(set(want) - set(digest_lines)),
                          "listed_not_rebound": sorted(set(digest_lines) - set(want))}
    first = lines(F2D + "/SHA256SUMS.txt")
    names = [x.split("  ", 1)[1] for x in first]
    out["first_list"] = {"lines": len(first), "lists_second_list": "s7/p00-freeze-001-rebound.sha256sums.txt" in names,
                         "lists_freeze": "FREEZE-002.json" in names, "lists_itself": "SHA256SUMS.txt" in names}
    # Freeze 001's files that are NOT rebound (its own JSON, notes, author material): not read in S7.
    out["freeze_001_files_not_rebound"] = sorted(set(f1_lines) - {b["path"][len(F1D) + 1:] for b in rebound})
    prep = f["preparation"]["entries"]
    out["preparation"] = {"entries": len(prep), "directories": sum(1 for e in prep if e["kind"] == "directory"),
                          "files": sum(1 for e in prep if e["kind"] == "file")}
    # 4. Absolute paths that S7 starts or reads by name.
    bound = {b["path"] for b in f["bindings"]}
    p00 = {F2D + "/" + n for n in names} | {x.split("  ", 1)[1] for x in digest_lines}
    prepared = {e["path"] for e in prep}
    absent = set(f["absent_paths"]["before_preparation"]) | {p for c in f["commands"] for p in c["records"].values()}
    os_prefixes = ("/usr/bin/", "/bin/", "/usr/sbin/", "/usr/lib/", "/System/", "/dev/")
    classes = {}
    for c in f["commands"]:
        items = [c["cwd"], c["environment"]["file"]] + [a for a in c["argv"]]
        for a in items:
            for token in ([a] + ([a.split("=", 1)[1]] if "=" in a and not a.startswith("/") else [])):
                if not token.startswith("/"):
                    continue
                path = token.rstrip("/")
                if path in p00 and path in bound:
                    k = "P00 and bound"
                elif path in p00:
                    k = "P00 only"
                elif path in bound:
                    k = "bound only"
                elif path in prepared:
                    k = "prepared (D01, checked by D02)"
                elif path in absent or path.startswith(E + "/s7-001"):
                    k = "an S7 output or record"
                elif path == E or path.startswith(E + "/observe-001"):
                    k = "the evidence parent or S5's attempt"
                elif path.startswith(os_prefixes):
                    k = "an OS path"
                elif path.startswith(WT + "/.venv"):
                    k = "the venv (Python inventory, P02 to P04, Q01)"
                elif path == WT or path.startswith(WT + "/"):
                    k = "the worktree at C (P05, source inventory)"
                elif path.startswith("<prefix>/"):
                    k = "the framework (Python inventory)"
                else:
                    k = "other"
                classes.setdefault(k, set()).add(path)
    out["paths_named_by_commands"] = {k: sorted(v) for k, v in sorted(classes.items())}
    out["paths_named_counts"] = {k: len(v) for k, v in sorted(classes.items())}
    with open(sys.argv[1], "x") as s:
        json.dump(out, s, indent=1, sort_keys=True)
        s.write("\n")
    print(json.dumps({k: out[k] for k in ("second_list", "first_list", "preparation", "paths_named_counts")}, sort_keys=True))
    print(json.dumps({"bound_only": out["paths_named_by_commands"].get("bound only", []),
                      "other": out["paths_named_by_commands"].get("other", []),
                      "P00_only": out["paths_named_by_commands"].get("P00 only", [])}, indent=0)[:4000])


main()
