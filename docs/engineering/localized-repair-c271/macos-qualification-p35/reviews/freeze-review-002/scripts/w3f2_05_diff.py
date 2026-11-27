"""Freeze review 002, script 05: my own mechanical comparison of FREEZE-001.json and FREEZE-002.json.

Every leaf difference outside the commands (and the commands' non-argv fields that changed), as JSON
pointers, for comparison with FREEZE-002-DIFFERENCES.json's D-01 to D-14 and stated additions.

Run: <worktree>/.venv/bin/python -I -S -B w3f2_05_diff.py OUTPUT.json TEXT.txt
"""
import json
import sys

PROCESS_EVENTS = {"subprocess.Popen", "os.posix_spawn", "os.exec", "os.fork", "os.forkpty", "os.spawn", "os.system"}


def refuse(event, args):
    if event in PROCESS_EVENTS:
        raise PermissionError("no process: " + event)


sys.addaudithook(refuse)

P35 = "<local>/c271-p35"


def load(p):
    with open(p, "rb") as s:
        return json.loads(s.read())


def esc(k):
    return str(k).replace("~", "~0").replace("/", "~1")


def diff(a, b, path, out):
    if type(a) is not type(b):
        out.append({"path": path, "old": a, "new": b})
        return
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            p = path + "/" + esc(k)
            if k not in a:
                out.append({"path": p, "added": b[k]})
            elif k not in b:
                out.append({"path": p, "removed": a[k]})
            else:
                diff(a[k], b[k], p, out)
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append({"path": path, "old_len": len(a), "new_len": len(b), "old": a, "new": b})
            return
        for i, (x, y) in enumerate(zip(a, b)):
            diff(x, y, path + "/" + str(i), out)
    elif a != b:
        out.append({"path": path, "old": a, "new": b})


def main():
    f1 = load(P35 + "/workers/W2-freeze-001/FREEZE-001.json")
    f2 = load(P35 + "/workers/W2-freeze-002/FREEZE-002.json")
    out = []
    for k in sorted(set(f1) | set(f2)):
        if k in ("commands", "absent_paths", "bindings"):
            continue
        if k not in f1:
            out.append({"path": "/" + k, "added": f2[k]})
        elif k not in f2:
            out.append({"path": "/" + k, "removed": f1[k]})
        else:
            diff(f1[k], f2[k], "/" + k, out)
    # Commands: the non-argv fields, per id, excluding expect (script 03) and timer_shell.
    c1 = {c["id"]: c for c in f1["commands"]}
    c2 = {c["id"]: c for c in f2["commands"]}
    cmd = []
    for cid in c1:
        for field in sorted(set(c1[cid]) | set(c2[cid])):
            if field in ("argv", "wrapper_argv", "shell", "timer_shell", "expect"):
                continue
            if c1[cid].get(field) != c2[cid].get(field):
                d = []
                diff(c1[cid].get(field), c2[cid].get(field), "/commands/" + cid + "/" + field, d)
                cmd += d
    top = sorted({d["path"].split("/")[1] for d in out})
    result = {"script": "w3f2_05_diff.py", "top_level_changed": top, "differences": out, "command_field_differences": cmd}
    with open(sys.argv[1], "x") as s:
        json.dump(result, s, indent=1, sort_keys=True)
        s.write("\n")
    lines = []
    for d in out + cmd:
        if "added" in d:
            lines.append("ADDED   %s = %s" % (d["path"], json.dumps(d["added"])[:600]))
        elif "removed" in d:
            lines.append("REMOVED %s = %s" % (d["path"], json.dumps(d["removed"])[:600]))
        elif "old_len" in d:
            lines.append("LIST    %s %d -> %d\n   old: %s\n   new: %s" % (d["path"], d["old_len"], d["new_len"],
                                                                      json.dumps(d["old"])[:3000], json.dumps(d["new"])[:3000]))
        else:
            lines.append("CHANGED %s\n   old: %s\n   new: %s" % (d["path"], json.dumps(d["old"])[:3000], json.dumps(d["new"])[:3000]))
    with open(sys.argv[2], "x") as s:
        s.write("\n".join(lines) + "\n")
    print(json.dumps({"top_level_changed": top, "differences": len(out), "command_field_differences": len(cmd)}))


main()
