"""Freeze review 002, script 06: the absent lists, recomputed from the commands and the preparation.

Run: <worktree>/.venv/bin/python -I -S -B w3f2_06_absent.py OUTPUT.json
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
E = P35 + "/evidence"


def load(p):
    with open(p, "rb") as s:
        return json.loads(s.read())


def main():
    f1 = load(P35 + "/workers/W2-freeze-001/FREEZE-001.json")
    f2 = load(P35 + "/workers/W2-freeze-002/FREEZE-002.json")
    out = {"script": "w3f2_06_absent.py"}
    for name, f in (("freeze_001", f1), ("freeze_002", f2)):
        before = f["absent_paths"]["before_preparation"]
        after = f["absent_paths"]["after_preparation"]
        named = {}
        for c in f["commands"]:
            for p in list(c["records"].values()) + list(c["outputs"]) + list(c["outputs_absent_before"]):
                named.setdefault(p, set()).add(c["id"])
        prepared = [e["path"] for e in f["preparation"]["entries"]]
        own_records = lambda ids: {p for c in f["commands"] if c["id"] in ids for p in c["records"].values()}
        pre_exempt = own_records({"P00", "P01"})
        post_exempt = own_records({"P00", "P01", "P02", "P03", "P04", "P05", "D01", "D02"})
        want_before = (set(named) | set(prepared)) - pre_exempt
        want_after = (set(named) - post_exempt)
        out[name] = {
            "before": len(before), "after": len(after),
            "before_unique": len(set(before)) == len(before), "after_unique": len(set(after)) == len(after),
            "before_sorted": before == sorted(before), "after_sorted": after == sorted(after),
            "prepared_entries": len(prepared),
            "before_equals_recomputed": set(before) == want_before,
            "before_extra": sorted(set(before) - want_before), "before_missing": sorted(want_before - set(before)),
            "after_equals_recomputed": set(after) == want_after,
            "after_extra": sorted(set(after) - want_after), "after_missing": sorted(want_after - set(after)),
            "after_is_before_minus_prepared_and_P02_to_D02": set(after) == set(before) - set(prepared) - post_exempt,
            "all_under_evidence": all(p.startswith(E + "/") for p in before + after),
            "present_now": [p for p in set(before) | set(after) | pre_exempt | post_exempt if os.path.lexists(p)],
            "exempt_records": {"pre": len(pre_exempt), "post": len(post_exempt)}}
    b1, b2 = set(f1["absent_paths"]["before_preparation"]), set(f2["absent_paths"]["before_preparation"])
    a1, a2 = set(f1["absent_paths"]["after_preparation"]), set(f2["absent_paths"]["after_preparation"])
    capture = {p for c in f2["commands"] if c["phase"] == "capture" for p in c["outputs_absent_before"]}
    out["delta"] = {"before_added": len(b2 - b1), "before_removed": sorted(b1 - b2), "after_added": len(a2 - a1),
                    "after_removed": sorted(a1 - a2), "before_added_equals_capture": (b2 - b1) == capture,
                    "after_added_equals_capture": (a2 - a1) == capture, "capture_paths": len(capture)}
    # The P00 records: absent now, and in neither list.
    p00 = next(c for c in f2["commands"] if c["id"] == "P00")
    out["p00_records"] = {"in_before": sorted(set(p00["records"].values()) & b2), "in_after": sorted(set(p00["records"].values()) & a2),
                          "present_now": [p for p in p00["records"].values() if os.path.lexists(p)]}
    with open(sys.argv[1], "x") as s:
        json.dump(out, s, indent=1, sort_keys=True)
        s.write("\n")
    print(json.dumps(out, sort_keys=True)[:3000])


main()
