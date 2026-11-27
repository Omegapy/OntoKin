"""HOST review 001, script 05: this HOST against MH's HOST, leaf by leaf, and their inspection receipts.

Every differing leaf is listed (labelled) and classified: expected to differ (the source commit and
tree, the ref file that holds the commit, times, the plan and the inspection receipts, and the
paths of MR's own plan, inventories and evidence), or unexplained. The groups that must be equal
(host facts, environment, interpreter and inventories, runtime, reader tree, Git, labels, claims)
are checked to have no differing leaf.
Usage: python3 -I -S -B w3h_05_compare_mh.py --host H --mh-host M --out OUT [--label PATH=LABEL ...]
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w3h_common as C  # noqa: E402

C.install_hook()


def unescape(pointer):
    return [part.replace("~1", "/").replace("~0", "~") for part in pointer.split("/")[1:]]


def main():
    ap = argparse.ArgumentParser()
    for name in ("--host", "--mh-host", "--out"):
        ap.add_argument(name, required=True)
    ap.add_argument("--label", action="append", default=[])
    args = ap.parse_args()
    lab = C.Labeler([tuple(item.split("=", 1)) for item in args.label])
    ck = C.Checks()
    started = time.time()
    raw, facts, _ = C.read_bytes(args.host)
    mraw, mfacts, _ = C.read_bytes(args.mh_host)
    host, mh = C.strict_loads(raw), C.strict_loads(mraw)
    ck.add("M00", mfacts["sha256"] == "34e94f29ea1b7d9d60b389598b4ce5bc7eaf6fcaa58f3798fc3df021a8f28a92"
           and mfacts["size_bytes"] == 18420 and mfacts["mode"] == "0o600" and C.canonical(mh) == mraw,
           "MH's HOST is unchanged: its recorded SHA-256, 18,420 bytes, 0o600, canonical")
    a, b = dict(C.json_pointer_leaves(mh)), dict(C.json_pointer_leaves(host))
    keys = sorted(set(a) | set(b))
    diffs = [k for k in keys if a.get(k, "<absent>") != b.get(k, "<absent>")]
    ref = mh["source"]["head"]["ref"]
    ref_file = mh["source"]["head"]["common_dir"] + "/" + ref

    def reason(pointer):
        parts = unescape(pointer)
        if parts in (["source", "commit"], ["source", "head", "commit"]):
            return "the source commit: MH's C, this HOST's B"
        if parts == ["source", "tree"]:
            return "the source tree: C's and B's"
        if parts[:3] == ["source", "head", "files"] and parts[3:] == [ref_file, "sha256"]:
            return "the loose ref file that holds the commit (same 41 bytes, other commit)"
        if parts == ["observed_at_utc"]:
            return "the time of the observation"
        if parts in (["plan", "path"], ["plan", "sha256"]):
            return "MR's own observation plan (the same 9,017 bytes in size, 37 leaves different)"
        if parts[0] == "inspections" and parts[2] in ("path", "sha256", "size_bytes"):
            return "MR's own inspection receipts: other evidence parent, times and PIDs"
        if parts in (["source", "inventory", "path"], ["python", "inventory", "path"],
                     ["dependencies", "inventory", "path"]):
            return "the inventories are MR's own copies, byte-identical to MH's, under MR's plan directory"
        return None
    rows = [{"pointer": lab.text("/" + "/".join(unescape(k))), "mh": lab.deep(a.get(k, "<absent>")),
             "this": lab.deep(b.get(k, "<absent>")), "reason": reason(k)} for k in diffs]
    unexplained = [r for r in rows if r["reason"] is None]
    ck.add("M01", not unexplained, "every differing leaf is explained", differing_leaves=len(rows),
           unexplained=unexplained)
    must_equal = ["schema", "contract", "design_revision", "amendments", "profile", "executor", "observer", "platform",
                  "os", "environment", "runtime", "git", "labels", "claims", "starts"]
    groups = {g: all(unescape(k)[0] != g for k in diffs) for g in must_equal}
    py = [unescape(k) for k in diffs if unescape(k)[0] == "python"]
    dep = [unescape(k) for k in diffs if unescape(k)[0] == "dependencies"]
    ck.add("M02", all(groups.values()) and py == [["python", "inventory", "path"]]
           and dep == [["dependencies", "inventory", "path"]],
           "equal: the platform (boot included), the OS identity, the environment and CoreFoundation value, the "
           "observer, the whole python group (interpreter, selection, inventory digest, packages, RECORD rows, "
           "lock) apart from the frozen inventory's path, the runtime, the reader tree apart from its inventory's "
           "path, Git with its version line, the labels, the claims and the starts", groups=groups)
    must_differ = [["source", "commit"], ["source", "tree"], ["observed_at_utc"], ["plan", "sha256"]]
    ck.add("M03", all("/" + "/".join(p) in ["/" + "/".join(unescape(k)) for k in diffs] for p in must_differ)
           and host["source"]["commit"] == "4ca781429c5411c67c0965bc69306b42c6cc74ad"
           and mh["source"]["commit"] == "0eb9a5517f4e19705178a2c59b8d8d33fb87867a",
           "what must differ does: the commit (C to B), the tree, the observation time and the plan")
    for name in ("source", "python", "dependencies"):
        key = "inventory"
        ck.add("M04-" + name, {k: host[name][key][k] for k in ("sha256", "size_bytes", "mode")} ==
               {k: mh[name][key][k] for k in ("sha256", "size_bytes", "mode")},
               "the " + name + " inventory has MH's SHA-256, size and mode; only its path differs")
    # the inspection receipts each HOST binds
    insp = {}
    for cid in ("git_version", "node_version"):
        x = C.strict_loads(C.read_bytes(host["inspections"][cid]["path"])[0])
        y = C.strict_loads(C.read_bytes(mh["inspections"][cid]["path"])[0])
        lx, ly = dict(C.json_pointer_leaves(x)), dict(C.json_pointer_leaves(y))
        changed = sorted(k for k in set(lx) | set(ly) if lx.get(k) != ly.get(k))
        allowed = {"/finished_at_utc", "/started_at_utc", "/process/pid", "/process/process_group",
                   "/process/start_monotonic", "/process/end_monotonic", "/process/cwd"}
        insp[cid] = {"changed": changed, "pids": [y["process"]["pid"], x["process"]["pid"]],
                     "duration_ms": [round((y["process"]["end_monotonic"] - y["process"]["start_monotonic"]) * 1000, 3),
                                     round((x["process"]["end_monotonic"] - x["process"]["start_monotonic"]) * 1000, 3)],
                     "stdout_equal": x["stdout"] == y["stdout"], "stderr_both_empty": x["stderr"] == y["stderr"] == ""}
        ck.add("M05-" + cid, set(changed) <= allowed and insp[cid]["stdout_equal"] and insp[cid]["stderr_both_empty"],
               "the " + cid + " receipts differ only in times, PID and group, monotonic times and the stage path; "
               "argv, environment, timeout, return code, cleanup, log sizes, stdout and stderr are equal",
               **insp[cid])
    out = {"script": "w3h_05_compare_mh.py", "process": C.process_identity(), "started_epoch": started,
           "ended_epoch": time.time(), "differences": rows, "checks": ck.rows, "summary": ck.summary(),
           "audit_events": C.EVENTS}
    print(C.write_new(args.out, lab.deep(out)), ck.summary())


if __name__ == "__main__":
    main()
