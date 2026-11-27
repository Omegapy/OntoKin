"""HOST review 001, script h04: the two starts and the capture records (questions 2 and 7), the CF variable
and the processes that run the bound images.

Run as: <worktree>/.venv/bin/python -I -S -B h04_evidence.py --host H --plan P --launch M0-LAUNCH --w2static S
        --wrapper1 R1 --wrapper2 R2 --output OUT
It reads the evidence and changes nothing in it.
"""
import argparse
import ctypes
import importlib.util
import json
import os
import pwd
import re
import stat
import struct
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.realpath(__file__))
_spec = importlib.util.spec_from_file_location("h_common", HERE + "/h_common.py")
C = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(C)

CHECKS = []
PROCESS_KEYS = {"argv", "cwd", "environment", "label", "start_monotonic", "pid", "process_group", "returncode",
                "observed_log_bytes", "retained_log_bytes", "cleanup", "handles_closed", "error", "end_monotonic"}
REVISION = {"contract": "ontokin.current-host-readback/0.2.0", "design_revision": 4,
            "amendments": ["P33-AMENDMENT-001"]}
GIT_LINE = re.compile(rb"git version [\x20-\x7e]{1,200}\n")


def check(cid, what, ok, **details):
    CHECKS.append({"id": cid, "what": what, "passed": bool(ok), **({"details": details} if details else {})})


def t(text):
    return datetime.fromisoformat(text).timestamp()


def ns(value):
    return value / 1e9


def doc(path):
    raw, facts, _ = C.read_bound(path, keep=True)
    return json.loads(raw.decode("ascii")), raw, facts


def desc(path):
    _, facts, _ = C.read_bound(path)
    return {"path": path, **C.binding(facts)}


def revised(value):
    return all(value.get(k) == v for k, v in REVISION.items())


def listing(root):
    rows = {"root": {"kind": "directory", "mode": C.mode_text(os.lstat(root).st_mode),
                     "size_bytes": os.lstat(root).st_size, "state": "present"}}
    entries = {}
    for base, dirs, files in os.walk(root, followlinks=False):
        for name in sorted(dirs + files):
            path = os.path.join(base, name)
            rel = os.path.relpath(path, root)
            info = os.lstat(path)
            if stat.S_ISDIR(info.st_mode):
                entries[rel] = {"kind": "directory", "mode": C.mode_text(info.st_mode), "size_bytes": info.st_size,
                                "state": "present"}
            elif stat.S_ISREG(info.st_mode):
                _, facts, _ = C.read_bound(path)
                entries[rel] = {"kind": "file", **C.binding(facts), "state": "present"}
            else:
                entries[rel] = {"kind": "other", "state": "present"}
    rows["entries"] = entries
    return rows


def libproc():
    lib = ctypes.CDLL("/usr/lib/libSystem.B.dylib", use_errno=True)
    lib.proc_listallpids.argtypes = [ctypes.c_void_p, ctypes.c_int]
    lib.proc_listallpids.restype = ctypes.c_int
    lib.proc_pidpath.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
    lib.proc_pidpath.restype = ctypes.c_int
    lib.proc_pidinfo.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_int]
    lib.proc_pidinfo.restype = ctypes.c_int
    return lib


def processes_with_images(images):
    lib = libproc()
    count = lib.proc_listallpids(None, 0)
    buf = (ctypes.c_int * (count + 256))()
    got = lib.proc_listallpids(buf, ctypes.sizeof(buf))
    rows, scanned = [], 0
    for pid in list(buf)[:got]:
        if pid <= 0:
            continue
        scanned += 1
        path = ctypes.create_string_buffer(4096)
        length = lib.proc_pidpath(pid, path, 4096)
        if length <= 0:
            continue
        image = os.fsdecode(path.raw[:length])
        if image not in images:
            continue
        info = ctypes.create_string_buffer(136)
        size = lib.proc_pidinfo(pid, 3, 0, info, 136)  # PROC_PIDTBSDINFO
        row = {"pid": pid, "image_role": images[image]}
        if size == 136:
            raw = info.raw
            ppid, uid = struct.unpack_from("<II", raw, 16)
            pgid = struct.unpack_from("<I", raw, 100)[0]
            start_s, start_us = struct.unpack_from("<QQ", raw, 120)
            row.update(ppid=ppid, pgid=pgid, same_user=uid == os.getuid(),
                       started_utc=datetime.fromtimestamp(start_s + start_us / 1e6, timezone.utc).isoformat(),
                       comm=raw[48:64].split(b"\0", 1)[0].decode("ascii", "replace"))
        rows.append(row)
    return rows, scanned


def main():
    parser = argparse.ArgumentParser()
    for name in ("host", "plan", "launch", "w2static", "wrapper1", "wrapper2", "output"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    out = {"script": "h04_evidence.py", "process": C.process_facts()}
    host, _, host_facts = doc(args.host)
    plan, _, plan_facts = doc(args.plan)
    launch, _, _ = doc(args.launch)
    outputs = plan["evidence"]["outputs"]
    attempt = plan["evidence"]["attempt"]
    parent = plan["evidence"]["parent"]
    plan_desc = {"path": args.plan, **C.binding(plan_facts)}
    commands = {c["id"]: c for c in plan["commands"]}
    boot = plan["platform"]["boot_session_uuid"]
    preflight, _, preflight_facts = doc(outputs["preflight"])
    static_out = json.loads(C.read_bound(parent + "/observe-001.static.stdout.txt", keep=True)[0])
    facts_sha = preflight["facts_sha256"]
    times, pids = {}, {}

    # Question 2: each start, from its records.
    for cid in ("git_version", "node_version"):
        paths, command = outputs[cid], commands[cid]
        intent, _, intent_f = doc(paths["intent"])
        started, _, started_f = doc(paths["started"])
        process, process_raw, process_f = doc(paths["process"])
        inspection, _, inspection_f = doc(paths["inspection"])
        post, _, post_f = doc(paths["postflight"])
        stdout, stdout_f, _ = C.read_bound(paths["stdout"], keep=True)
        stderr, stderr_f, _ = C.read_bound(paths["stderr"], keep=True)
        sp = started["process"]
        check("Q2-%s-intent" % cid, cid + ": intent.json was written before the start, UNKNOWN, observed 0, planned argv",
              intent["schema"].endswith("observation-attempt/0.2.0") and revised(intent)
              and intent["command_id"] == cid and intent["kind"] == command["kind"] and intent["argv"] == command["argv"]
              and intent["expected_direct_starts"] == 1 and intent["actual_direct_starts"] is None
              and intent["observed_direct_starts"] == 0 and intent["start_count_state"] == "UNKNOWN"
              and intent["state"] == "UNKNOWN" and intent["process"] is None and intent["start"] is None
              and intent["plan"] == plan_desc and intent["boundary"] == "real")
        check("Q2-%s-started" % cid, cid + ": started.json holds one positive PID leading its own group, with the planned argv, cwd, environment and label",
              started["schema"].endswith("observation-start/0.2.0") and revised(started)
              and started["command_id"] == cid and started["plan"] == plan_desc and started["boundary"] == "real"
              and isinstance(sp["pid"], int) and sp["pid"] > 0 and sp["process_group"] == sp["pid"]
              and sp["argv"] == command["argv"] and sp["cwd"] == command["cwd"]
              and sp["environment"] == command["environment"] and sp["label"] == command["label"]
              and sp["returncode"] is None and sp["cleanup"] is None and sp["handles_closed"] is False,
              pid=sp["pid"])
        duration = process["end_monotonic"] - process["start_monotonic"]
        check("Q2-%s-receipt" % cid, cid + ": process.json is the supervisor's 14-field receipt: same identity as started.json, exit 0, reaped, group absent, handles closed",
              set(process) == PROCESS_KEYS and process["argv"] == command["argv"] and process["cwd"] == command["cwd"]
              and process["environment"] == command["environment"] and process["label"] == command["label"]
              and all(process[k] == sp[k] for k in ("pid", "process_group", "argv", "cwd", "environment", "label",
                                                    "start_monotonic"))
              and process["returncode"] == 0 and process["error"] is None and process["handles_closed"] is True
              and process["cleanup"] == {"elapsed_ms": 0, "passed": True, "process_group_absent": True, "reaped": True}
              and process["observed_log_bytes"] == process["retained_log_bytes"] == len(stdout) + len(stderr)
              and process_raw == C.canonical(process))
        check("Q2-%s-limits" % cid, cid + ": the start ended within the 3,000 ms of active work and the 5,000 ms in all",
              0 <= duration <= command["active_work_ms"] / 1000 and command["timeout_ms"] == 5000
              and command["active_work_ms"] == 3000 and command["cleanup_ms"] == 2000, duration_s=round(duration, 6))
        if cid == "git_version":
            predicate = GIT_LINE.fullmatch(stdout) is not None
        else:
            predicate = stdout == b"v24.22.1\n"
        check("Q2-%s-predicate" % cid, cid + ": the stdout predicate holds and stderr is empty",
              predicate and stderr == b"", stdout=stdout.decode("ascii"), stderr_bytes=len(stderr))
        check("Q2-%s-inspection" % cid, cid + ": inspection.json is the closed 0.2.0 receipt of this start",
              set(inspection) == {"schema", "contract", "design_revision", "amendments", "argv", "environment",
                                  "timeout_ms", "started_at_utc", "finished_at_utc", "process", "stdout", "stderr"}
              and revised(inspection) and inspection["argv"] == command["argv"]
              and inspection["environment"] == command["environment"] and inspection["timeout_ms"] == 5000
              and inspection["process"] == process and inspection["stdout"] == stdout.decode("ascii")
              and inspection["stderr"] == stderr.decode("ascii")
              and t(inspection["started_at_utc"]) <= t(started["observed_at_utc"]) <= t(inspection["finished_at_utc"]))
        check("Q2-%s-postflight" % cid, cid + ": postflight.json is COMPLETED and OBSERVED_ONE, with every artifact bound and both rechecks equal to the static facts",
              post["state"] == "COMPLETED" and post["start_count_state"] == "OBSERVED_ONE"
              and post["actual_direct_starts"] == 1 and post["observed_direct_starts"] == 1
              and post["expected_direct_starts"] == 1 and post["failure"] is None and post["supervisor_failure"] is None
              and post["process"] == process and post["start"] == desc(paths["started"])
              and post["artifacts"] == {"inspection": desc(paths["inspection"]), "process": desc(paths["process"]),
                                        "stdout": desc(paths["stdout"]), "stderr": desc(paths["stderr"])}
              and post["preflight"]["passed"] and post["postflight"]["passed"]
              and post["preflight"]["facts_sha256"] == post["postflight"]["facts_sha256"] == facts_sha
              == static_out["facts_sha256"]
              and t(post["preflight"]["checked_at_utc"]) <= t(inspection["started_at_utc"])
              and t(inspection["finished_at_utc"]) <= t(post["postflight"]["checked_at_utc"]))
        check("Q2-%s-failure-absent" % cid, cid + ": no failure.json", not os.path.lexists(paths["failure"]))
        times[cid] = {"intent_mtime": ns(intent_f["mtime_ns"]), "started_mtime": ns(started_f["mtime_ns"]),
                      "post_mtime": ns(post_f["mtime_ns"]), "started_at": t(inspection["started_at_utc"]),
                      "finished_at": t(inspection["finished_at_utc"]),
                      "preflight_at": t(post["preflight"]["checked_at_utc"]),
                      "postflight_at": t(post["postflight"]["checked_at_utc"]), "duration_s": duration}
        pids[cid] = sp["pid"]
        out.setdefault("starts", {})[cid] = {"pid": sp["pid"], "process_group": sp["process_group"],
                                             "duration_s": round(duration, 6), "stdout": stdout.decode("ascii"),
                                             "stderr_bytes": len(stderr), "kind": command["kind"],
                                             "preflight_at": post["preflight"]["checked_at_utc"],
                                             "started_at": inspection["started_at_utc"],
                                             "finished_at": inspection["finished_at_utc"],
                                             "postflight_at": post["postflight"]["checked_at_utc"]}
    g, n = times["git_version"], times["node_version"]
    check("Q2-order", "intent, start and postflight of Git precede Node's, and HOST follows Node's postflight",
          g["intent_mtime"] < g["started_mtime"] < g["post_mtime"] <= n["intent_mtime"] < n["started_mtime"]
          < n["post_mtime"] < t(host["observed_at_utc"]) <= ns(host_facts["mtime_ns"]))
    counts = {"node": sum(1 for c in plan["commands"] if c["kind"] == "node" and pids[c["id"]] > 0),
              "other": sum(1 for c in plan["commands"] if c["kind"] == "other" and pids[c["id"]] > 0)}
    out["start_counts"] = counts
    check("Q2-counts", "P07 section 4: one receipt with a positive PID per command, so {node: 1, other: 1}, as MH-PLAN section 7's M0 and M1 rows expect",
          counts == {"node": 1, "other": 1} == host["starts"])
    check("Q2-pids", "the two PIDs are consecutive (no other process was created on the host between the two forks)",
          pids["node_version"] == pids["git_version"] + 1, pids=pids)

    # The attempt's own documents.
    result, _, result_f = doc(outputs["result"])
    completion, _, completion_f = doc(outputs["completion"])
    reserved, _, _ = doc(outputs["reserved"])
    observe_out = json.loads(C.read_bound(parent + "/observe-001.observe.stdout.txt", keep=True)[0])
    host_desc = {"path": args.host, **C.binding(host_facts)}
    check("Q2-result", "result.json: both attempts, HOST, starts exact 1 and 1, PENDING_COMPLETION before the completion marker",
          result["attempts"] == [desc(outputs["git_version"]["postflight"]), desc(outputs["node_version"]["postflight"])]
          and result["host"] == host_desc and result["state"] == "PENDING_COMPLETION"
          and result["evidence_finalized"] is False and result["failures"] == []
          and result["starts"] == {"node": {"exact": 1, "observed_lower_bound": 1},
                                   "other": {"exact": 1, "observed_lower_bound": 1}}
          and result["labels"] == host["labels"] and result["reserved"] == desc(outputs["reserved"])
          and result["preflight"] == desc(outputs["preflight"]) and result["plan"] == plan_desc)
    check("Q2-completion", "completion.json: OBSERVED_UNAPPROVED, evidence_finalized, HOST and result bound",
          completion["state"] == "OBSERVED_UNAPPROVED" and completion["evidence_finalized"] is True
          and completion["host"] == host_desc and completion["result"] == {"path": outputs["result"], **C.binding(result_f)}
          and completion["starts"] == result["starts"] and completion["boundary"] == "real" and revised(completion))
    check("Q2-stdout", "observe's stdout result: OBSERVED_UNAPPROVED, finalized, with the completion and result descriptors",
          observe_out["state"] == "OBSERVED_UNAPPROVED" and observe_out["evidence_finalized"] is True
          and observe_out["completion"] == {"path": outputs["completion"], **C.binding(completion_f)}
          and observe_out["result"] == completion["result"] and observe_out["host"] == host_desc)
    check("Q2-reserved", "reserved.json owns exactly the three directories and expects {node: 1, other: 1}",
          reserved["owned_directories"] == sorted([attempt, outputs["git_version"]["stage"],
                                                   outputs["node_version"]["stage"]])
          and reserved["expected_starts"] == {"node": 1, "other": 1})
    check("Q2-preflight", "preflight.json's inventory digest is HOST's, and its facts digest is the static run's",
          preflight["python_inventory_sha256"] == host["python"]["inventory_sha256"]
          and facts_sha == static_out["facts_sha256"])
    check("Q2-no-failure", "no attempt-level failure.json", not os.path.lexists(outputs["failure"]))

    # Question 7: the readback listing against the attempt as it now is.
    readback, _, readback_f = doc(parent + "/observe-001.readback.json")
    now = listing(attempt)
    then = readback["directories"][attempt]
    out["listing_now"] = {"entries": len(now["entries"]), "root": now["root"]}
    check("Q7-listing", "the readback listing equals the attempt directory now: every path, kind, size, mode and digest",
          now == then, added=sorted(set(now["entries"]) - set(then["entries"])),
          missing=sorted(set(then["entries"]) - set(now["entries"])),
          changed=sorted(k for k in set(now["entries"]) & set(then["entries"]) if now["entries"][k] != then["entries"][k]))
    path_rows = {}
    for path in readback["paths"]:
        if os.path.lexists(path):
            info = os.lstat(path)
            if stat.S_ISDIR(info.st_mode):
                path_rows[path] = {"kind": "directory", "mode": C.mode_text(info.st_mode), "size_bytes": info.st_size,
                                   "state": "present"}
            else:
                _, f, _ = C.read_bound(path)
                path_rows[path] = {"kind": "file", **C.binding(f), "state": "present"}
        else:
            path_rows[path] = {"state": "absent"}
    planned = set()

    def visit(value):
        if isinstance(value, str):
            planned.add(value)
        elif isinstance(value, dict):
            for item in value.values():
                visit(item)
    visit(outputs)
    planned.discard(attempt)
    check("Q7-paths", "the readback's per-path record covers every planned output and equals the files now",
          path_rows == readback["paths"] and set(readback["paths"]) == planned,
          not_covered=sorted(planned - set(readback["paths"])), extra=sorted(set(readback["paths"]) - planned))
    tool = readback["tool"]
    check("Q7-listing-meta", "the listing was made by the bound capture_probe.py, under -I -S -B, with no process event, in the plan's boot",
          tool == desc(tool["path"]) and readback["process_events"] == [] and readback["loaded_project_files"] == []
          and readback["boot_before"] == readback["boot_after"] == boot
          and readback["invocation"]["python"]["flags"]["dont_write_bytecode"] == 1
          and readback["invocation"]["python"]["flags"]["isolated"] == 1
          and readback["invocation"]["python"]["flags"]["no_site"] == 1)
    probes, _, _ = doc(parent + "/observe-001.probes.json")
    rows = []
    for target in probes["targets"]:
        pair = target["pair"]
        info_i, info_s = os.lstat(pair["intent"]["path"]), os.lstat(pair["started"]["path"])
        started = json.loads(C.read_bound(pair["started"]["path"], keep=True)[0])["process"]
        rows.append(pair["intent"]["mtime_ns"] == info_i.st_mtime_ns and pair["started"]["mtime_ns"] == info_s.st_mtime_ns
                    and {k: pair["intent"][k] for k in ("path", "sha256", "size_bytes", "mode")} == desc(pair["intent"]["path"])
                    and {k: pair["started"][k] for k in ("path", "sha256", "size_bytes", "mode")} == desc(pair["started"]["path"])
                    and pair["recorded"] == {"argv0": started["argv"][0], "pid": started["pid"],
                                             "process_group": started["process_group"]}
                    and target["kill"] == "ESRCH" and target["killpg"] == "ESRCH" and target["state"] == "absent")
    check("Q7-probes", "FC-P3: both recorded starts are absent by ESRCH for kill and killpg; each pair is the attempt's intent and started records, unchanged",
          len(rows) == 2 and all(rows) and sorted(r["pair"]["recorded"]["pid"] for r in probes["targets"])
          == sorted(pids.values()) and probes["boot_before"] == probes["boot_after"] == boot
          and probes["tool"] == tool and probes["process_events"] == [])

    # The command records (FC-K2, FC-K3).
    env_path = parent + "/observe-001.environment.json"
    env_raw, env_f, _ = C.read_bound(env_path, keep=True)
    env = json.loads(env_raw)
    check("Q7-env", "the environment file is the canonical declared map, its SHA-256 is M0-LAUNCH's, and the argv's assignments are the same map",
          C.canonical(env) == env_raw and env == plan["environment"]
          and env_f["sha256"] == launch["command"]["environment_canonical_sha256"])
    records = {}
    for name in ("observe", "readback-listing", "probes"):
        record, _, record_f = doc(parent + "/observe-001." + name + ".command.json")
        records[name] = (record, record_f)
    static_record, _, static_record_f = doc(parent + "/observe-001.static.command-record.json")
    records["static"] = (static_record, static_record_f)
    fc_k3 = {"argv", "cwd", "environment", "started_at_utc", "ended_at_utc", "wall_time_s", "boot"}
    births = {}
    for name, (record, record_f) in records.items():
        start = float(str(record["start_epoch_s"]).split()[0])
        end = float(str(record["end_epoch_s"]).split()[0])
        so = parent + "/observe-001." + name + ".stdout.txt"
        se = parent + "/observe-001." + name + ".stderr.txt"
        ex = parent + "/observe-001." + name + ".exit.txt"
        so_f, se_f, ex_f = C.read_bound(so)[1], C.read_bound(se)[1], C.read_bound(ex, keep=True)
        assigned = dict(item.split("=", 1) for item in record["argv"][2:7])
        so_birth, ex_birth = C.birth_exact_ns(so), C.birth_exact_ns(ex)
        ex_f[1]["birth_ns"], so_f["birth_ns"] = ex_birth, so_birth
        record_path = parent + "/observe-001." + name + (".command-record.json" if name == "static" else ".command.json")
        births[name] = {"stdout": so_birth, "exit": ex_birth, "record": C.birth_exact_ns(record_path),
                        "record_mtime": record_f["mtime_ns"], "start": start, "end": end}
        utc = lambda text: datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
        s_start, s_end = utc(record["started_at_utc"]), utc(record["ended_at_utc"])
        births[name]["utc_window"] = {"started_at_utc": record["started_at_utc"], "ended_at_utc": record["ended_at_utc"],
                                      "start_minus_second": start - s_start, "end_second_minus_end": s_end - end}
        check("Q7-record-" + name, name + ": FC-K3's fields, the env file's digest, the declared assignments, streams, exit and boot agree with the files",
              fc_k3 <= set(record) and record["environment"] == {"file": env_path, "sha256": env_f["sha256"]}
              and record["argv"][:2] == ["/usr/bin/env", "-i"] and assigned == plan["environment"]
              and record["argv"][7:11] == [plan["python"]["venv"] + "/bin/python", "-I", "-S", "-B"]
              and record["cwd"] == parent
              and record["streams"]["stdout"] == {"path": so, "sha256": so_f["sha256"], "size_bytes": so_f["size_bytes"]}
              and record["streams"]["stderr"] == {"path": se, "sha256": se_f["sha256"], "size_bytes": se_f["size_bytes"]}
              and record["streams"]["exit"] == {"path": ex}
              and ex_f[0] == (str(record["exit"]["status"]) + "\n").encode() and record["exit"]["status"] == 0
              and record["boot"] == {"before": boot, "after": boot} and record["retries"] == 0
              and s_start <= start < s_start + 1.1 and end - 1 < s_end <= end + 0.1
              and start <= ns(so_f["birth_ns"]) + 0.000001 and end <= ns(ex_f[1]["birth_ns"]) + 0.000001,
              start=start, end=end, stdout_birth=ns(so_f["birth_ns"]), exit_birth=ns(ex_f[1]["birth_ns"]),
              wall=record["wall_time_s"])
    obs, _ = records["observe"]
    check("Q7-observe-argv", "observe's record has exactly M0-LAUNCH's argv and cwd, and its window holds the whole attempt",
          obs["argv"] == launch["command"]["argv"] and obs["cwd"] == launch["command"]["cwd"]
          and float(obs["start_epoch_s"]) <= ns(C.birth_exact_ns(attempt))
          and t(host["observed_at_utc"]) <= float(obs["end_epoch_s"])
          and abs(float(obs["end_epoch_s"]) - float(obs["start_epoch_s"]) - float(obs["wall_time_s"])) < 1e-5)
    rl, _ = records["readback-listing"]
    pr, _ = records["probes"]
    check("Q7-listing-argv", "the listing record's argv is the listing's invocation, and its window holds the listing's times",
          rl["argv"][11:] == readback["invocation"]["argv"] and rl["argv"][7:11] == obs["argv"][7:11]
          and float(rl["start_epoch_s"]) <= t(readback["started_at_utc"]) <= t(readback["finished_at_utc"])
          <= float(rl["end_epoch_s"]))
    check("Q7-probes-argv", "the probe record's argv is the probe's invocation, and its window holds the probe's times",
          pr["argv"][11:] == probes["invocation"]["argv"]
          and float(pr["start_epoch_s"]) <= t(probes["started_at_utc"]) <= t(probes["finished_at_utc"])
          <= float(pr["end_epoch_s"]))
    check("Q7-order", "the readback listing was the first command after observe, and the probe followed it",
          float(obs["end_epoch_s"]) < float(rl["start_epoch_s"]) < float(rl["end_epoch_s"]) < float(pr["start_epoch_s"]))

    # The hand-written static record and the empty first record.
    st, _ = records["static"]
    empty = parent + "/observe-001.static.command.json"
    empty_info = os.lstat(empty)
    so_birth = births["static"]["stdout"]
    ex_birth = births["static"]["exit"]
    empty_birth = C.birth_exact_ns(empty)
    out["record_times"] = births
    out["static_record"] = {"start_epoch_s": st["start_epoch_s"], "end_epoch_s": st["end_epoch_s"],
                            "stdout_birth_ns": so_birth, "exit_birth_ns": ex_birth,
                            "empty_record": {"size_bytes": empty_info.st_size, "birth_ns": empty_birth,
                                             "mtime_ns": empty_info.st_mtime_ns,
                                             "mode": C.mode_text(empty_info.st_mode)},
                            "hand_record_birth_ns": births["static"]["record"],
                            "hand_record_mtime_ns": births["static"]["record_mtime"],
                            "birth_interval_s": (ex_birth - so_birth) / 1e9, "wall_time_s": st["wall_time_s"]}
    check("Q7-static-times", "the hand record's start and end are the stdout and exit files' birth times, to the nanosecond",
          str(st["start_epoch_s"]).split()[0] == "%d.%09d" % divmod(so_birth, 10 ** 9)
          and str(st["end_epoch_s"]).split()[0] == "%d.%09d" % divmod(ex_birth, 10 ** 9))
    wall = float(str(st["wall_time_s"]).split()[0])
    check("Q7-static-wall", "the printed wall time is a little shorter than the birth interval, as the wrapper's order predicts",
          0 < (ex_birth - so_birth) / 1e9 - wall < 0.05, difference_s=(ex_birth - so_birth) / 1e9 - wall)
    check("Q7-static-argv", "the hand record's argv is M0-LAUNCH's with static in place of observe",
          st["argv"] == [("static" if a == "observe" else a) for a in launch["command"]["argv"]]
          and st["argv"].count("static") == 1)
    check("Q7-static-output", "static's stdout is W2's static-001 output byte for byte, STATIC_READY with zero starts and the same facts digest",
          C.read_bound(parent + "/observe-001.static.stdout.txt")[1]["sha256"] == C.read_bound(args.w2static)[1]["sha256"]
          and static_out["state"] == "STATIC_READY" and static_out["mode"] == "static"
          and static_out["starts"] == {"node": {"exact": 0, "observed_lower_bound": 0},
                                       "other": {"exact": 0, "observed_lower_bound": 0}}
          and static_out["plan"] == plan_desc)
    check("Q7-static-empty", "the empty first record (0 bytes) was created after static ended and before the hand record, and is kept",
          empty_info.st_size == 0 and ex_birth <= empty_birth <= births["static"]["record"]
          and births["static"]["record_mtime"] < float(obs["start_epoch_s"]) * 1e9)
    w1_f = C.read_bound(args.wrapper1)[1]
    w2_f = C.read_bound(args.wrapper2)[1]
    w1_f["birth_ns"], w2_f["birth_ns"] = C.birth_exact_ns(args.wrapper1), C.birth_exact_ns(args.wrapper2)
    out["wrappers"] = {"run_once.sh": {k: w1_f[k] for k in ("sha256", "size_bytes", "mode", "mtime_ns", "birth_ns")},
                       "run_once_v2.sh": {k: w2_f[k] for k in ("sha256", "size_bytes", "mode", "mtime_ns", "birth_ns")}}
    check("Q7-wrappers", "run_once.sh was not changed after static started; run_once_v2.sh was written after static and before observe",
          w1_f["mtime_ns"] < so_birth and ex_birth < w2_f["birth_ns"] <= w2_f["mtime_ns"]
          < float(obs["start_epoch_s"]) * 1e9)

    # The evidence parent and its ancestors.
    names = sorted(os.listdir(parent))
    expected = sorted(["observe-001", "observe-001.environment.json"]
                      + ["observe-001.%s.%s" % (a, b) for a in ("observe", "readback-listing", "probes", "static")
                         for b in ("stdout.txt", "stderr.txt", "exit.txt")]
                      + ["observe-001.%s.command.json" % a for a in ("observe", "readback-listing", "probes", "static")]
                      + ["observe-001.static.command-record.json", "observe-001.readback.json", "observe-001.probes.json"])
    check("Q7-parent", "the evidence parent holds exactly the attempt and its 21 sibling records, and nothing else",
          names == expected, extra=sorted(set(names) - set(expected)), missing=sorted(set(expected) - set(names)))
    ancestors = []
    current = parent
    while True:
        info = os.lstat(current)
        ancestors.append({"path": current, "device": info.st_dev, "inode": info.st_ino,
                          "mode": C.mode_text(info.st_mode)})
        if current == "/":
            break
        current = os.path.dirname(current)
    check("Q7-ancestors", "the evidence parent's ancestors keep the plan's device, inode and mode",
          sorted(ancestors, key=lambda r: r["path"]) == plan["evidence"]["ancestors"])
    modes = {rel: row.get("mode") for rel, row in now["entries"].items()}
    check("Q7-modes", "directories 0o700, observer documents 0o600, the supervisor's three files 0o644, no temporary file left",
          all(m == "0o700" for r, m in modes.items() if now["entries"][r]["kind"] == "directory")
          and all(m == ("0o644" if r.split("/")[-1].startswith("host-") else "0o600")
                  for r, m in modes.items() if now["entries"][r]["kind"] == "file")
          and not any(r.split("/")[-1].startswith(".") for r in modes))

    # Question 8: __CF_USER_TEXT_ENCODING and the user's text-encoding file.
    home = pwd.getpwuid(os.getuid()).pw_dir
    cf_file = home + "/.CFUserTextEncoding"
    cf = {"uid": os.getuid(), "uid_hex": "0x%X" % os.getuid(), "host_value": host["environment"]["cf_user_text_encoding"],
          "this_process_inherited_value": os.environ.get("__CF_USER_TEXT_ENCODING"),
          "file": "<home>/.CFUserTextEncoding"}
    if os.path.lexists(cf_file):
        raw, facts, _ = C.read_bound(cf_file, keep=True)
        cf.update(file_present=True, file_bytes=raw.decode("ascii", "replace"), file_sha256=facts["sha256"],
                  file_size=facts["size_bytes"], file_mode=facts["mode"], file_mtime_ns=facts["mtime_ns"])
    else:
        cf.update(file_present=False)
    out["cf"] = cf
    check("Q8-cf", "HOST's value is 0x<uid>:<file content>, the form CoreFoundation builds from the user's .CFUserTextEncoding",
          cf.get("file_present") and host["environment"]["cf_user_text_encoding"] == cf["uid_hex"] + ":" + cf["file_bytes"].strip())

    # Processes that run the bound images (context only, FC-P1: a listing by image never proves absence).
    framework = host["python"]["framework"]
    images = {framework + "/Resources/Python.app/Contents/MacOS/Python": "framework-process-image",
              host["runtime"]["executable"]: "bound-node", host["git"]["path"]: "bound-git"}
    rows, scanned = processes_with_images(images)
    out["processes_with_bound_images"] = {"scanned": scanned, "rows": rows, "this_pid": os.getpid()}
    check("Q8-no-node-git", "no process runs the prepared bin/node or the bound Git now",
          not [r for r in rows if r["image_role"] != "framework-process-image"])
    out["checks"] = CHECKS
    out["failed"] = [c["id"] for c in CHECKS if not c["passed"]]
    out["refused_events"] = C.REFUSED_EVENTS
    C.write_new(args.output, out)
    print(json.dumps({"failed": out["failed"], "checks": len(CHECKS)}))


if __name__ == "__main__":
    main()
