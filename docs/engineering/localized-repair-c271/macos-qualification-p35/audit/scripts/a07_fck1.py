"""W4 audit 001, a07: item 9, FAILURE-CAPTURE and FC-K1.

Usage: a07_fck1.py FREEZE HOST_REVIEW_JSON OUTPUT
  - no capture record and no capture-command path exists;
  - S5's records (observe-001/ and its beside-files) against HOST review 001's reviewed digests, S5's own
    readback listing, the Director's log digests, and their modification times;
  - every entry of the evidence parent accounted for: S5's, or a path that freeze 002 lists as absent
    before the preparation (that is, created by S7);
  - the 495 and 428 absent-path lists against what exists now, classified by the frozen command that
    creates each path; the paths that must still be absent;
  - the prepared entries (43) against the freeze, the consumed copy excepted;
  - the temporary directories (empty).
Starts nothing (an audit hook refuses process creation).
"""
import calendar
import hashlib
import json
import os
import stat
import sys
import time


def _refuse(event, args):
    if event in ("subprocess.Popen", "os.posix_spawn", "os.exec", "os.fork", "os.forkpty", "os.spawn",
                 "os.system", "os.startfile"):
        raise PermissionError("this audit script starts no process: " + event)


sys.addaudithook(_refuse)


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def describe(path):
    if not os.path.lexists(path):
        return {"state": "absent"}
    info = os.lstat(path)
    kind = "file" if stat.S_ISREG(info.st_mode) else "directory" if stat.S_ISDIR(info.st_mode) else "link" if stat.S_ISLNK(info.st_mode) else "other"
    record = {"state": "present", "kind": kind, "mode": "0o%03o" % stat.S_IMODE(info.st_mode), "size_bytes": info.st_size,
              "mtime": info.st_mtime}
    if kind == "file":
        record["sha256"] = sha(path)
    return record


def main():
    freeze = json.load(open(sys.argv[1]))
    review = json.load(open(sys.argv[2]))
    output = sys.argv[3]
    E = freeze["evidence"]["parent"]
    local = freeze["places"]["local"]
    commands = {c["id"]: c for c in freeze["commands"]}
    report = {"schema": "w4-audit-001.a07-fck1/1"}

    # Capture records.
    capture_like = sorted(n for n in os.listdir(E) if "failure-capture" in n or "overrun" in n or ".stop-" in n)
    capture_paths = []
    for cid in freeze["capture_commands"]:
        for path in list((commands[cid].get("records") or {}).values()) + list(commands[cid].get("outputs") or []):
            capture_paths.append(path)
    failure_records = [os.path.join(E, commands[c]["name"] + ".failure-capture.json") for c in freeze["order"]]
    report["capture"] = {"capture_like_names": capture_like,
                         "capture_command_paths": len(capture_paths),
                         "capture_command_paths_present": [p for p in capture_paths if os.path.lexists(p)],
                         "failure_capture_records_present": [p for p in failure_records if os.path.lexists(p)]}

    # S5's records against HOST review 001 and the Director's log.
    reviewed = {}
    for row in review["reviewed_files"]:
        path = row["path"].replace("<local>", local)
        if path.startswith(E + "/observe-001"):
            reviewed[path] = row
    s5_rows = []
    for path, row in sorted(reviewed.items()):
        now = describe(path)
        s5_rows.append({"path": os.path.relpath(path, E), "ok": now.get("sha256") == row["sha256"] and now.get("size_bytes") == row["size_bytes"]
                        and now.get("mode") == row["mode"]})
    s5_present = []
    for name in sorted(os.listdir(E)):
        if name.startswith("observe-001"):
            full = os.path.join(E, name)
            if os.path.isdir(full):
                for parent, directories, names in os.walk(full):
                    for n in names:
                        s5_present.append(os.path.join(parent, n))
            else:
                s5_present.append(full)
    not_reviewed = [os.path.relpath(p, E) for p in s5_present if p not in reviewed]
    readback = json.load(open(os.path.join(E, "observe-001.readback.json")))
    readback_rows = []
    for directory, info in readback["directories"].items():
        for rel, entry in info["entries"].items():
            now = describe(os.path.join(directory, rel))
            ok = now["state"] == entry["state"] and (entry.get("kind") != "file" or now.get("sha256") == entry["sha256"])
            readback_rows.append({"path": os.path.relpath(os.path.join(directory, rel), E), "ok": ok})
    for path, entry in readback["paths"].items():
        now = describe(path)
        ok = now["state"] == entry["state"] and (entry.get("kind") != "file" or now.get("sha256") == entry["sha256"])
        readback_rows.append({"path": os.path.relpath(path, E), "ok": ok})
    log_digests = {"observe-001/HOST.json": "34e94f29ea1b7d9d60b389598b4ce5bc7eaf6fcaa58f3798fc3df021a8f28a92",
                   "observe-001.readback.json": "058aee0b2dd416ce8a300a35eed73a6c2210c574077ea86efdf3d8f739e3cb6a",
                   "observe-001.probes.json": "9030422faa95bb27ddf864d6404c9ab3931627347114099537e3e0d6695dbadd",
                   "observe-001/completion.json": "fd1a035065e758825ddff81671fec29380720ed03d20c9571a17d993089488fe",
                   "observe-001/result.json": "1b4cae0f80cce491b200b5a24a1b5a75660af7889bb7120e98cec0a7080b2e1d"}
    s5_end = calendar.timegm(time.strptime("2026-11-27T05:35:20Z", "%Y-%m-%dT%H:%M:%SZ"))
    latest = max((os.lstat(p).st_mtime, os.path.relpath(p, E)) for p in s5_present)
    report["s5"] = {"reviewed_entries": len(s5_rows), "reviewed_failed": [r for r in s5_rows if not r["ok"]],
                    "present_files": len(s5_present), "present_not_in_review": not_reviewed,
                    "readback_entries": len(readback_rows), "readback_failed": [r for r in readback_rows if not r["ok"]],
                    "director_log_digests": {k: sha(os.path.join(E, k)) == v for k, v in log_digests.items()},
                    "latest_mtime_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(latest[0])), "latest_file": latest[1],
                    "nothing_newer_than_05_35_20Z": latest[0] <= s5_end,
                    "static_command_json_empty": os.path.getsize(os.path.join(E, "observe-001.static.command.json")) == 0}

    # Every top-level entry of the evidence parent.
    before = set(freeze["absent_paths"]["before_preparation"])
    after = set(freeze["absent_paths"]["after_preparation"])
    top = sorted(os.listdir(E))
    unaccounted = [n for n in top if not n.startswith("observe-001") and os.path.join(E, n) not in before]
    report["top_level"] = {"entries": len(top), "s5": sum(1 for n in top if n.startswith("observe-001")),
                           "s7": sum(1 for n in top if n.startswith("s7-001-")), "unaccounted": unaccounted,
                           "other_prefix": [n for n in top if not n.startswith(("observe-001", "s7-001-"))]}

    # The absent lists against what exists now, classified.
    creator = {}
    for cid in freeze["order"]:
        command = commands[cid]
        for path in list((command.get("records") or {}).values()) + list(command.get("outputs") or []) + \
                list(command.get("outputs_absent_before") or []):
            creator.setdefault(path, cid)
    prepared = {row["path"]: row for row in freeze["preparation"]["entries"]}
    for path in prepared:
        creator.setdefault(path, "D01")
    def classify(paths):
        rows = {"present_created_by_frozen_command": 0, "present_unexplained": [], "absent": [], "absent_capture": 0,
                "absent_failure_capture": 0, "absent_other": []}
        capture_set = set(capture_paths)
        for path in sorted(paths):
            exists = os.path.lexists(path)
            if exists:
                owner = creator.get(path)
                if owner is None:
                    # a path inside a frozen output directory
                    parents = [p for p in creator if path.startswith(p.rstrip("/") + "/")]
                    owner = creator[max(parents, key=len)] if parents else None
                if owner:
                    rows["present_created_by_frozen_command"] += 1
                else:
                    rows["present_unexplained"].append(path)
            else:
                rows["absent"].append(path)
                if path in capture_set:
                    rows["absent_capture"] += 1
                elif path.endswith(".failure-capture.json"):
                    rows["absent_failure_capture"] += 1
                else:
                    rows["absent_other"].append(path)
        rows["absent"] = len(rows["absent"])
        return rows
    report["absent_lists"] = {"before_preparation": {"count": len(before), **classify(before)},
                              "after_preparation": {"count": len(after), **classify(after)}}

    # Prepared entries now.
    consumed = set(freeze["post"]["consumed"])
    prepared_rows = []
    for row in freeze["preparation"]["entries"]:
        now = describe(row["path"])
        if row["kind"] == "file":
            ok = now.get("sha256") == row["sha256"] and now.get("mode") == row["mode"] and now.get("size_bytes") == row["size_bytes"]
            if row["id"] in consumed:
                ok = "consumed by design: " + str(now.get("sha256"))
        else:
            ok = now.get("kind") == "directory" and now.get("mode") == row["mode"]
        prepared_rows.append({"id": row["id"], "ok": ok})
    report["prepared"] = {"entries": len(prepared_rows), "not_ok": [r for r in prepared_rows if r["ok"] is not True]}
    tmp = {name: sorted(os.listdir(os.path.join(E, name))) for name in top if name.startswith("s7-001-tmp-")}
    report["temporary_directories"] = tmp
    data = json.dumps(report, indent=1, sort_keys=True).encode()
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    print(json.dumps(report, indent=1)[:8000])


main()
