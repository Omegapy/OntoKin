"""HOST review 001, script 04: the attempt's records, the two starts, the capture records and the wrapper.

Static reads only, plus kill(pid, 0) and killpg(pid, 0) for the two recorded PIDs: signal 0
delivers nothing (the audit hook refuses any other signal).
Usage: python3 -I -S -B w3h_04_evidence.py --plan P --launch L --review R --wrapper W --mh-wrapper W2
       --w2-static S --out OUT [--label PATH=LABEL ...]
"""
import argparse
import datetime
import difflib
import errno
import os
import posixpath
import re
import stat
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w3h_common as C  # noqa: E402

C.install_hook()

ATTEMPT_KEYS = {"schema", "contract", "design_revision", "amendments", "plan", "command_id", "kind", "argv",
                "expected_direct_starts", "actual_direct_starts", "observed_direct_starts", "start_count_state", "state",
                "start", "process", "supervisor_failure", "artifacts", "preflight", "postflight", "boundary", "failure"}
PROCESS_KEYS = {"argv", "cwd", "environment", "label", "start_monotonic", "pid", "process_group", "returncode",
                "observed_log_bytes", "retained_log_bytes", "cleanup", "handles_closed", "error", "end_monotonic"}
REVISION = {"contract": "ontokin.current-host-readback/0.2.0", "design_revision": 4, "amendments": ["P33-AMENDMENT-001"]}


def iso(value):
    return datetime.datetime.fromisoformat(value).timestamp()


def utc(epoch):
    return datetime.datetime.fromtimestamp(epoch, datetime.timezone.utc).isoformat()


def load(path):
    raw, facts, _ = C.read_bytes(path)
    return C.strict_loads(raw), raw, facts


def probe(pid):
    out = {}
    for name, fn in (("kill", os.kill), ("killpg", os.killpg)):
        try:
            fn(pid, 0)
            out[name] = "present"
        except ProcessLookupError:
            out[name] = "ESRCH"
        except PermissionError:
            out[name] = "EPERM"
        except OSError as exc:
            out[name] = errno.errorcode.get(exc.errno, str(exc.errno))
    return out


def main():
    ap = argparse.ArgumentParser()
    for name in ("--plan", "--launch", "--review", "--wrapper", "--mh-wrapper", "--w2-static", "--out"):
        ap.add_argument(name, required=True)
    ap.add_argument("--label", action="append", default=[])
    args = ap.parse_args()
    lab = C.Labeler([tuple(item.split("=", 1)) for item in args.label])
    ck = C.Checks()
    started = time.time()
    plan, plan_raw, plan_facts = load(args.plan)
    launch = load(args.launch)[0]
    review = load(args.review)[0]
    digest = review["plan"]["sha256"]
    plan_desc = C.descriptor(args.plan, plan_facts)
    ev = plan["evidence"]
    attempt, parent, outs = ev["attempt"], ev["parent"], ev["outputs"]
    success = launch["expected_outputs"]["success"]

    # --- the attempt's tree -----------------------------------------------------
    listing = {}
    for dirpath, dirnames, filenames in os.walk(attempt):
        for name in dirnames + filenames:
            path = os.path.join(dirpath, name)
            info = os.lstat(path)
            row = {"kind": "directory" if stat.S_ISDIR(info.st_mode) else "file" if stat.S_ISREG(info.st_mode)
                   else "other", "mode": C.mode_text(info.st_mode), "nlink": info.st_nlink,
                   "birth": info.st_birthtime}
            if row["kind"] == "file":
                _, facts, _ = C.read_bytes(path, keep=False)
                row.update(sha256=facts["sha256"], size_bytes=facts["size_bytes"])
            listing[path] = row
    root_info = os.lstat(attempt)
    dirs = sorted([attempt] + [p for p, r in listing.items() if r["kind"] == "directory"])
    files = sorted(p for p, r in listing.items() if r["kind"] == "file")
    ck.add("T01", dirs == sorted(success["directories"]) and C.mode_text(root_info.st_mode) == "0o700"
           and all(listing[d]["mode"] == "0o700" for d in dirs if d != attempt),
           "the attempt holds exactly the three planned directories, each 0o700")
    ck.add("T02", files == sorted(success["files"]) and not any(r["kind"] == "other" for r in listing.values()),
           "the attempt holds exactly M0-LAUNCH's 19 success files and nothing else (no temporary, hidden or "
           ".DS_Store entry)", files=len(files))
    ck.add("T03", not any(os.path.lexists(p) for p in success["files_absent_on_success"]),
           "none of the three failure.json files exists")
    sup = {p for p in files if p.endswith((".stdout.log", ".stderr.log", ".process.json"))}
    ck.add("T04", all(listing[p]["mode"] == ("0o644" if p in sup else "0o600") and listing[p]["nlink"] == 1
                      for p in files) and len(sup) == 6,
           "modes: 0o600 for the observer's 13 documents, 0o644 for the supervisor's six files (umask 022); one link "
           "each")
    by = {p: C.descriptor(p, {**listing[p], "mode": listing[p]["mode"]}) for p in files}

    # --- result, completion, reservation, preflight -----------------------------
    host_path = outs["host"]
    result, _, rf = load(outs["result"])
    completion, _, cf = load(outs["completion"])
    reserved, _, _ = load(outs["reserved"])
    preflight, _, _ = load(outs["preflight"])
    host, _, hf = load(host_path)
    ck.add("R01", result["host"] == by[host_path] == completion["host"] and result["plan"] == plan_desc ==
           completion["plan"] == reserved["plan"] == preflight["plan"]
           and result["reserved"] == by[outs["reserved"]] and result["preflight"] == by[outs["preflight"]]
           and result["attempts"] == [by[outs["git_version"]["postflight"]], by[outs["node_version"]["postflight"]]]
           and completion["result"] == by[outs["result"]],
           "every descriptor in result.json and completion.json is the file's own (HOST, plan, reservation, "
           "preflight, both attempts, result)")
    ck.add("R02", result["state"] == "PENDING_COMPLETION" and result["evidence_finalized"] is False
           and result["failures"] == [] and result["mode"] == "observe"
           and result["starts"] == {"node": {"exact": 1, "observed_lower_bound": 1},
                                    "other": {"exact": 1, "observed_lower_bound": 1}}
           and result["labels"] == host["labels"] and all(result[k] == v for k, v in REVISION.items()),
           "result.json: PENDING_COMPLETION by design, no failure, exact counts node 1 and other 1, HOST's labels")
    ck.add("R03", completion["state"] == "OBSERVED_UNAPPROVED" and completion["evidence_finalized"] is True
           and completion["starts"] == result["starts"] and completion["boundary"] == "real"
           and all(completion[k] == v for k, v in REVISION.items()),
           "completion.json: OBSERVED_UNAPPROVED, finalized, the same counts, boundary real")
    ck.add("R04", reserved["attempt"] == attempt and reserved["owned_directories"] == dirs
           and reserved["expected_starts"] == {"node": 1, "other": 1} and reserved["boundary"] == "real",
           "reserved.json: the attempt, its three owned directories and the expected starts")
    ck.add("R05", preflight["facts_sha256"] == "3f0624318211f82e76aaf408a98e2e0a82ec2147ed681682242f37c9343c4ddf"
           and preflight["python_inventory_sha256"] == host["python"]["inventory_sha256"] ==
           "c277bdd3ac6aa73105df3924707a271a402a0dc7c722be27a6834f2c78605633",
           "preflight.json: the static facts digest and the inventory digest")

    # --- the two starts ------------------------------------------------------------
    commands = {c["id"]: c for c in plan["commands"]}
    per, timeline = {}, []
    for cid, kind in (("git_version", "other"), ("node_version", "node")):
        o, cmd = outs[cid], commands[cid]
        intent, _, _ = load(o["intent"])
        start, _, _ = load(o["started"])
        proc, proc_raw, _ = load(o["process"])
        insp, _, _ = load(o["inspection"])
        post, _, _ = load(o["postflight"])
        stdout = C.read_bytes(o["stdout"])[0]
        stderr = C.read_bytes(o["stderr"])[0]
        sp = start["process"]
        rows = []
        rows.append(set(intent) == ATTEMPT_KEYS and intent["command_id"] == cid and intent["kind"] == kind
                    and intent["argv"] == cmd["argv"] and intent["expected_direct_starts"] == 1
                    and intent["actual_direct_starts"] is None and intent["observed_direct_starts"] == 0
                    and intent["start_count_state"] == "UNKNOWN" and intent["state"] == "UNKNOWN"
                    and intent["artifacts"] == {} and all(intent[k] is None for k in (
                        "start", "process", "supervisor_failure", "preflight", "postflight", "failure"))
                    and intent["plan"] == plan_desc and intent["boundary"] == "real")
        rows.append(set(start) == {"schema", "contract", "design_revision", "amendments", "plan", "command_id",
                                   "process", "observed_at_utc", "boundary"}
                    and set(sp) == PROCESS_KEYS - {"end_monotonic"} and sp["pid"] > 0 and sp["process_group"] ==
                    sp["pid"] and sp["argv"] == cmd["argv"] and sp["cwd"] == cmd["cwd"] and sp["environment"] ==
                    cmd["environment"] and sp["label"] == cmd["label"] and sp["returncode"] is None
                    and sp["cleanup"] is None and sp["handles_closed"] is False and sp["observed_log_bytes"] == 0)
        rows.append(set(proc) == PROCESS_KEYS and proc_raw == C.canonical(proc) and all(
            proc[k] == sp[k] for k in ("pid", "process_group", "argv", "cwd", "environment", "label",
                                       "start_monotonic"))
                    and proc["returncode"] == 0 and proc["handles_closed"] is True and proc["error"] is None
                    and proc["cleanup"] == {"passed": True, "process_group_absent": True, "reaped": True,
                                            "elapsed_ms": 0}
                    and proc["observed_log_bytes"] == proc["retained_log_bytes"] == len(stdout) + len(stderr))
        rows.append(set(insp) == {"schema", "contract", "design_revision", "amendments", "argv", "environment",
                                  "timeout_ms", "started_at_utc", "finished_at_utc", "process", "stdout", "stderr"}
                    and insp["process"] == proc and insp["argv"] == cmd["argv"] and insp["environment"] ==
                    cmd["environment"] and insp["timeout_ms"] == 5000 and insp["stdout"] == stdout.decode("ascii")
                    and insp["stderr"] == stderr.decode("ascii")
                    and iso(insp["started_at_utc"]) <= iso(start["observed_at_utc"]) <= iso(insp["finished_at_utc"]))
        rows.append(set(post) == ATTEMPT_KEYS and post["state"] == "COMPLETED" and post["start_count_state"] ==
                    "OBSERVED_ONE" and post["actual_direct_starts"] == 1 and post["observed_direct_starts"] == 1
                    and post["failure"] is None and post["supervisor_failure"] is None and post["process"] == proc
                    and post["start"] == by[o["started"]]
                    and post["artifacts"] == {"inspection": by[o["inspection"]], "process": by[o["process"]],
                                              "stderr": by[o["stderr"]], "stdout": by[o["stdout"]]}
                    and post["preflight"]["passed"] is True and post["postflight"]["passed"] is True
                    and post["preflight"]["stage"] == "before " + cid and post["postflight"]["stage"] == "after " + cid
                    and post["preflight"]["facts_sha256"] == post["postflight"]["facts_sha256"] ==
                    preflight["facts_sha256"])
        if cid == "git_version":
            rows.append(re.fullmatch(rb"git version [\x20-\x7e]{1,200}\n", stdout) is not None and stderr == b"")
        else:
            rows.append(stdout == b"v24.22.1\n" and stderr == b"")
        rows.append(all(d[k] == v for d in (intent, start, insp, post) for k, v in REVISION.items()))
        duration = proc["end_monotonic"] - proc["start_monotonic"]
        rows.append(0 <= duration <= cmd["active_work_ms"] / 1000 <= cmd["timeout_ms"] / 1000
                    and cmd["timeout_ms"] == 5000 and cmd["active_work_ms"] == 3000 and cmd["cleanup_ms"] == 2000)
        names = ["intent", "started", "process", "inspection", "postflight", "predicate", "revision", "limits"]
        per[cid] = {"checks": dict(zip(names, rows)), "pid": proc["pid"], "process_group": proc["process_group"],
                    "duration_ms": round(duration * 1000, 3),
                    "inspection_window": [insp["started_at_utc"], insp["finished_at_utc"]],
                    "preflight_recheck": post["preflight"]["checked_at_utc"],
                    "postflight_recheck": post["postflight"]["checked_at_utc"],
                    "stdout": stdout.decode("ascii"), "stderr_bytes": len(stderr), "now": probe(proc["pid"])}
        ck.add("C-" + cid, all(rows), "the " + cid + " start: intent, start record, supervisor receipt, inspection, "
               "postflight, predicates, revision fields and limits", **per[cid])
        timeline += [(listing[o["intent"]]["birth"], cid + " intent.json created"),
                     (iso(post["preflight"]["checked_at_utc"]), cid + " preflight recheck"),
                     (iso(insp["started_at_utc"]), cid + " inspection start"),
                     (iso(start["observed_at_utc"]), cid + " start observed"),
                     (iso(insp["finished_at_utc"]), cid + " inspection end"),
                     (iso(post["postflight"]["checked_at_utc"]), cid + " postflight recheck"),
                     (listing[o["postflight"]]["birth"], cid + " postflight.json created")]
    timeline.append((iso(host["observed_at_utc"]), "HOST observed"))
    timeline.append((listing[host_path]["birth"], "HOST.json created"))
    timeline.append((listing[outs["result"]]["birth"], "result.json created"))
    timeline.append((listing[outs["completion"]]["birth"], "completion.json created"))
    order = [t for t, _ in timeline]
    ck.add("O01", all(order[i] <= order[i + 1] + 2e-6 for i in range(len(order) - 1)),
           "the records run in order: Git's intent, rechecks, start and postflight, then Node's, then HOST, result "
           "and completion", timeline=[[utc(t), what] for t, what in timeline])
    g, n = per["git_version"]["pid"], per["node_version"]["pid"]
    ck.add("O02", n == g + 1, "the two PIDs are consecutive (consistent with no other process creation on the host "
           "between the two forks, since XNU assigns PIDs in sequence)", pids=[g, n])
    ck.add("O03", all(per[c]["now"] == {"kill": "ESRCH", "killpg": "ESRCH"} for c in per),
           "now both recorded PIDs and process groups are absent (ESRCH), probed with signal 0")

    # --- the observer's and supervisor's start routes (static) ------------------
    obs = C.read_bytes(plan["observer"]["path"])[0].decode("utf-8")
    sup_path = plan["source"]["root"] + "/prototypes/static_tray_v01/supervisor_darwin_v01.py"
    supv = C.read_bytes(sup_path)[0].decode("utf-8")
    pattern = (r"\bsubprocess\b|\bos\.system\b|\bos\.popen\b|\bos\.exec|\bos\.spawn|\bos\.posix_spawn|\bos\.fork|"
               r"\bpty\.|\bmultiprocessing\b|\bPopen\b")

    def matches(text):
        # comment lines and trailing comments are not code (supervisor line 158 mentions Popen in a comment)
        rows = []
        for i, line in enumerate(text.splitlines()):
            code_part = "" if line.lstrip().startswith("#") else line.split("  #", 1)[0]
            rows += [[i + 1, m.group(0)] for m in re.finditer(pattern, code_part)]
        return rows
    om, sm = matches(obs), matches(supv)
    ck.add("O04", om == [] and obs.count("supervisor.run_process(") == 1 and obs.count("def _run_start(") == 1
           and obs.count("= _run_start(context, command)") == 1
           and obs.count('for command in validated.plan["commands"]:') == 1
           and supv.count("subprocess.Popen(") == 1 and [m for m in sm if m[1] == "Popen"] == [[155, "Popen"]]
           and sorted({m[0] for m in sm}) == [33, 155, 156],
           "statically: the observer has no process-creation call of its own; its one start route is "
           "supervisor.run_process inside _run_start, which observe_host calls once for each of the plan's two "
           "commands; run_process makes one subprocess.Popen (supervisor_darwin_v01.py line 155)",
           observer_matches=om, supervisor_matches=sm)

    # --- the capture records ---------------------------------------------------
    environment_file = launch["environment_file"]
    _, env_facts, _ = C.read_bytes(environment_file["path"])
    rec = {}
    for name, key in (("observe-001.static", "static_before_observe"), ("observe-001.observe", "observe")):
        paths = {s: parent + "/" + name + "." + s for s in ("stdout.txt", "stderr.txt", "exit.txt", "command.json")}
        facts = {s: C.read_bytes(p, keep=False)[1] for s, p in paths.items()}
        record = C.strict_loads(C.read_bytes(paths["command.json"])[0])
        exit_raw = C.read_bytes(paths["exit.txt"])[0]
        out_raw = C.read_bytes(paths["stdout.txt"])[0]
        t0, t1 = float(record["start_epoch_s"]), float(record["end_epoch_s"])
        s0 = datetime.datetime.strptime(record["started_at_utc"], "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=datetime.timezone.utc).timestamp()
        s1 = datetime.datetime.strptime(record["ended_at_utc"], "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=datetime.timezone.utc).timestamp()
        argv = launch[key]["argv_without_digest"] + [digest]
        rows = {
            "argv": record["argv"] == argv and argv[-2] == "--plan-sha256" and argv.count(digest) == 1,
            "cwd": record["cwd"] == launch[key]["cwd"] == parent,
            "environment": record["environment"] == {"file": environment_file["path"], "sha256": env_facts["sha256"]}
            and env_facts["sha256"] == environment_file["sha256"]
            and record["argv"][2:7] == ["%s=%s" % kv for kv in [("PATH", "/usr/bin:/bin"), ("LANG", "C.UTF-8"),
                                                                ("LC_ALL", "C.UTF-8"), ("TZ", "UTC"),
                                                                ("UV_THREADPOOL_SIZE", "2")]]
            and record["argv"][:2] == ["/usr/bin/env", "-i"] and record["argv"][8:11] == ["-I", "-S", "-B"],
            "boot": record["boot"] == {"before": plan["platform"]["boot_session_uuid"],
                                       "after": plan["platform"]["boot_session_uuid"]},
            "exit": record["exit"] == {"status": 0} and exit_raw == b"0\n",
            "streams": record["streams"]["stdout"] == {"path": paths["stdout.txt"], "sha256": facts["stdout.txt"][
                "sha256"], "size_bytes": facts["stdout.txt"]["size_bytes"]}
            and record["streams"]["stderr"] == {"path": paths["stderr.txt"], "sha256": facts["stderr.txt"]["sha256"],
                                                "size_bytes": 0} and record["streams"]["exit"] == {"path": paths[
                                                    "exit.txt"]},
            "times": abs((t1 - t0) - float(record["wall_time_s"])) < 2e-6 and s0 <= t0 < s0 + 2
            and s1 <= t1 + 1 + 1e-6 and int(s1) >= int(t1) and t0 <= facts["stdout.txt"]["birthtime"] <= t1
            and t0 <= facts["exit.txt"]["birthtime"] and t1 <= facts["exit.txt"]["birthtime"] + 1e-3,
            "record": record["schema"] == "ontokin.c271.p36-command-record/1" and record["name"] == name
            and record["retries"] == 0 and record["written_by"] == "director/run/run_once_p36.sh",
            "modes": all(f["mode"] == "0o644" and f["nlink"] == 1 for f in facts.values()),
        }
        rec[name] = {"checks": rows, "window": [utc(t0), utc(t1)], "wall_time_s": record["wall_time_s"],
                     "stdout_sha256": facts["stdout.txt"]["sha256"], "stdout_bytes": facts["stdout.txt"]["size_bytes"],
                     "stdout_birth": utc(facts["stdout.txt"]["birthtime"]),
                     "exit_birth": utc(facts["exit.txt"]["birthtime"]),
                     "command_record_birth": utc(facts["command.json"]["birthtime"])}
        rec[name]["out"] = C.strict_loads(out_raw)
        rec[name]["out_canonical"] = out_raw == C.canonical(rec[name]["out"]) + b"\n"
        rec[name]["t"] = (t0, t1)
        ck.add("D-" + name, all(rows.values()) and rec[name]["out_canonical"],
               name + ": the command record holds the exact argv with the review record's digest, the cwd, the "
               "environment file, boot before and after, exit 0, the streams (stderr empty) and consistent times; "
               "stdout is one canonical line", **{k: v for k, v in rec[name].items() if k not in ("out", "t")})
    st = rec["observe-001.static"]["out"]
    w2_raw, w2_facts, _ = C.read_bytes(args.w2_static)
    ck.add("D01", st["state"] == "STATIC_READY" and st["mode"] == "static" and st["host"] is None
           and st["attempts"] == [] and st["facts_sha256"] == preflight["facts_sha256"]
           and st["starts"] == {"node": {"exact": 0, "observed_lower_bound": 0},
                                "other": {"exact": 0, "observed_lower_bound": 0}}
           and st["labels"] == host["labels"] and st["plan"] == plan_desc
           and C.read_bytes(parent + "/observe-001.static.stdout.txt")[0] == w2_raw,
           "the Director's static run: STATIC_READY, zero starts, the facts digest that observe's rechecks found, "
           "and stdout byte-identical to W2's static run", w2_static_sha256=w2_facts["sha256"])
    ob = rec["observe-001.observe"]["out"]
    expected = dict(result)
    expected.update(state="OBSERVED_UNAPPROVED", evidence_finalized=True, result=by[outs["result"]],
                    completion=by[outs["completion"]])
    ck.add("D02", ob == expected, "observe's stdout is result.json completed by the result and completion "
           "descriptors, with state OBSERVED_UNAPPROVED and evidence finalized")
    ts, to = rec["observe-001.static"]["t"], rec["observe-001.observe"]["t"]
    births = [r["birth"] for r in listing.values()] + [root_info.st_birthtime]
    ck.add("D03", ts[1] < to[0] and to[0] <= min(births) and max(births) <= to[1]
           and to[0] <= iso(host["observed_at_utc"]) <= to[1],
           "static ended before observe began; every attempt entry was created inside observe's window, and HOST "
           "was observed inside it", attempt_birth=utc(root_info.st_birthtime), first_entry=utc(min(births)),
           last_entry=utc(max(births)))

    # --- the evidence parent -----------------------------------------------------
    names = sorted(os.listdir(parent))
    want = sorted([posixpath.basename(attempt)] + [n + "." + s for n in ("observe-001.static", "observe-001.observe")
                                                    for s in ("stdout.txt", "stderr.txt", "exit.txt", "command.json")])
    rows = []
    for row in ev["ancestors"]:
        info = os.lstat(row["path"])
        rows.append((info.st_dev, info.st_ino, C.mode_text(info.st_mode)) == (row["device"], row["inode"], row["mode"])
                    and not stat.S_ISLNK(info.st_mode))
    ck.add("P01", names == want, "the evidence parent holds exactly the attempt and its eight capture files",
           entries=len(names))
    ck.add("P02", all(rows) and len(rows) == 7, "the parent and its six ancestors keep the plan's device, inode and "
           "mode, and none is a link")

    # --- the wrapper -----------------------------------------------------------
    w_raw, w_facts, _ = C.read_bytes(args.wrapper)
    m_raw, m_facts, _ = C.read_bytes(args.mh_wrapper)
    a, b = m_raw.decode("utf-8").splitlines(), w_raw.decode("utf-8").splitlines()
    subs = (("run_once_v2", "run_once_p36"), ("c271-p35", "c271-p36"), ("p35-command-record", "p36-command-record"))

    def code(lines, substitute):
        out = []
        for line in lines:
            if line.lstrip().startswith("#"):
                continue
            if substitute:
                for old, new in subs:
                    line = line.replace(old, new)
            out.append(line)
        return out
    mh_code, p36_code = code(a, True), code(b, False)
    raw_diff = [line for line in difflib.unified_diff(code(a, False), p36_code, lineterm="", n=0)
                if line[:1] in "+-" and not line.startswith(("+++", "---"))]
    left = [line for line in difflib.unified_diff(mh_code, p36_code, lineterm="", n=0)
            if line[:1] in "+-" and not line.startswith(("+++", "---"))]
    ck.add("W01", w_facts["sha256"] == "9154f181cfa7c8648c21b31a1f309af43f9b2b5046df1656a124a4b6b55e07a7"
           and m_facts["sha256"] == "3c24f923025f855603fce02a3e9fc794eb52409824369e53338f903ce9da8e1f",
           "the wrapper has the brief's SHA-256; MH's run_once_v2.sh has MH's", wrapper_mtime_utc=utc(
               w_facts["mtime_ns"] / 1e9), wrapper_bytes=w_facts["size_bytes"], wrapper_mode=w_facts["mode"],
           mh_wrapper_bytes=m_facts["size_bytes"])
    ck.add("W02", not left, "apart from comment lines, the wrapper is MH's run_once_v2.sh with only the evidence "
           "parent, the message prefix, and the record schema and writer names replaced",
           code_lines=[len(mh_code), len(p36_code)], comment_lines=[len(a) - len(mh_code), len(b) - len(p36_code)],
           changed_code_lines_before_substitution=len(raw_diff), differences_left=[lab.text(x) for x in left])
    w_text = w_raw.decode("utf-8")
    programs = sorted(set(re.findall(r"(?:/usr/s?bin|/bin)/[a-z0-9]+", w_text)))
    ck.add("W03", not any("python" in line.lower() for line in p36_code) and w_text.count("exec \"$@\"") == 1,
           "the wrapper's code names no Python and executes the argv once, in a subshell", programs=programs)

    result_out = {"script": "w3h_04_evidence.py", "process": C.process_identity(), "started_epoch": started,
                  "ended_epoch": time.time(), "checks": ck.rows, "summary": ck.summary(), "audit_events": C.EVENTS}
    print(C.write_new(args.out, lab.deep(result_out)), ck.summary())


if __name__ == "__main__":
    main()
