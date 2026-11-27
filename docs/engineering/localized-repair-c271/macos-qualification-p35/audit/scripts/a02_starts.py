"""W4 audit 001, a02: item 2, the starts, counted by P07 section 4's rules from every record.

Usage: a02_starts.py FREEZE OUTPUT
Walks every JSON and JSONL record under the evidence parent (S5's and S7's), except the two exported
source trees (repository content, not records). It collects:
  - every process-creation audit event (any list named process_events, any journal event);
  - every dict that carries a positive integer "pid" (receipts, started records, tool self-records,
    probe targets), with its pointer;
and classifies them. It then checks the cleanup proof of every receipt, the FC-P3 probe records, and
the UNKNOWN/interrupted markers. Starts nothing (an audit hook refuses process creation).
"""
import json
import os
import sys


def _refuse(event, args):
    if event in ("subprocess.Popen", "os.posix_spawn", "os.exec", "os.fork", "os.forkpty", "os.spawn",
                 "os.system", "os.startfile"):
        raise PermissionError("this audit script starts no process: " + event)


sys.addaudithook(_refuse)
DARWIN_PID_MAX = 99999  # xnu bsd/sys/proc_internal.h PID_MAX


def walk(value, pointer, sink_pid, sink_events):
    if isinstance(value, dict):
        pid = value.get("pid")
        if isinstance(pid, int) and not isinstance(pid, bool) and pid > 0:
            sink_pid.append((pointer, value))
        for key, item in value.items():
            child = pointer + "/" + str(key)
            if key == "process_events" and isinstance(item, list):
                for index, event in enumerate(item):
                    sink_events.append((child + "/" + str(index), event))
            walk(item, child, sink_pid, sink_events)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            walk(item, pointer + "/" + str(index), sink_pid, sink_events)


def main():
    freeze = json.load(open(sys.argv[1]))
    output = sys.argv[2]
    evidence = freeze["evidence"]["parent"]
    node_path = [b["path"] for b in freeze["bindings"] if b["id"] == "mp:node"][0]
    git_path = [b["path"] for b in freeze["bindings"] if b["id"] == "git"][0]
    exports = [os.path.join(evidence, name) for name in os.listdir(evidence) if name.startswith("s7-001-export-")
               and os.path.isdir(os.path.join(evidence, name))]
    # Map each output path or record to its command.
    owner = {}
    for command in freeze["commands"]:
        for path in command.get("outputs") or []:
            owner[path] = command["id"]
        for path in (command.get("records") or {}).values():
            owner[path] = command["id"]

    def command_of(path):
        best = None
        for prefix, cid in owner.items():
            if path == prefix or path.startswith(prefix.rstrip("/") + "/"):
                if best is None or len(prefix) > len(best[0]):
                    best = (prefix, cid)
        if best:
            return best[1]
        name = os.path.relpath(path, evidence)
        if name.startswith("observe-001"):
            return "S5"
        if name.startswith("s7-001-probe-") or name.startswith("s7-001-r"):
            return "stage"
        return "?"

    files = []
    for parent, directories, names in os.walk(evidence):
        directories[:] = [d for d in directories if os.path.join(parent, d) not in exports]
        for name in names:
            if name.endswith((".json", ".jsonl")):
                files.append(os.path.join(parent, name))
    files.sort()
    pids, events, parse_errors = [], [], []
    for path in files:
        try:
            raw = open(path, "rb").read()
            if not raw.strip():
                parse_errors.append({"path": path, "reason": "empty"})
                continue
            if path.endswith(".jsonl"):
                documents = [json.loads(line) for line in raw.decode().splitlines() if line.strip()]
            else:
                documents = [json.loads(raw)]
        except ValueError as error:
            parse_errors.append({"path": path, "reason": str(error)[:120]})
            continue
        for index, document in enumerate(documents):
            local_pids, local_events = [], []
            walk(document, "#%d" % index if path.endswith(".jsonl") else "", local_pids, local_events)
            for pointer, value in local_pids:
                pids.append({"file": path, "command": command_of(path), "pointer": pointer, "pid": value["pid"],
                             "process_group": value.get("process_group"),
                             "argv0": (value.get("argv") or [None])[0] if isinstance(value.get("argv"), list)
                             else value.get("argv0"),
                             "label": value.get("label"), "returncode": value.get("returncode"),
                             "cleanup": value.get("cleanup"), "handles_closed": value.get("handles_closed"),
                             "error": value.get("error"), "has_receipt_fields": "returncode" in value and "cleanup" in value})
            for pointer, event in local_events:
                events.append({"file": path, "command": command_of(path), "pointer": pointer,
                               "event": event.get("event"), "argv0": (event.get("argv") or [None])[0],
                               "executable": event.get("executable"), "blocked": event.get("blocked"),
                               "sequence": event.get("sequence"), "utc": event.get("utc")})

    # Classify every positive PID.
    def classify(row):
        pointer = row["pointer"]
        if pointer.endswith("/invocation/pid"):
            return "tool-self (Python launcher of the tool, recorded, not bounded)"
        if "/pair/recorded" in pointer or pointer.endswith("/recorded"):
            return "probe target (copy of a started record)"
        if row["pid"] > DARWIN_PID_MAX:
            return "simulated receipt (PID above Darwin's PID_MAX; mocked boundary)"
        if row["argv0"] == node_path:
            return "Node start receipt or started record"
        if row["argv0"] == git_path:
            return "Git start receipt or started record"
        return "other"

    for row in pids:
        row["class"] = classify(row)
    distinct = {}
    for row in pids:
        if row["class"] in ("Node start receipt or started record", "Git start receipt or started record", "other"):
            entry = distinct.setdefault(row["pid"], {"pid": row["pid"], "argv0": row["argv0"], "records": [], "commands": set(),
                                                     "receipts": 0, "cleanup_ok": True, "groups": set()})
            entry["records"].append(row["file"] + "#" + row["pointer"])
            entry["commands"].add(row["command"])
            entry["groups"].add(row["process_group"])
            if row["has_receipt_fields"] and row["returncode"] is not None:
                entry["receipts"] += 1
                cleanup = row["cleanup"] or {}
                if not (cleanup.get("passed") is True and cleanup.get("process_group_absent") is True
                        and cleanup.get("reaped") is True and row["handles_closed"] is True):
                    entry["cleanup_ok"] = False
    distinct_rows = []
    for pid, entry in sorted(distinct.items()):
        entry["commands"] = sorted(entry["commands"])
        entry["groups"] = sorted(g for g in entry["groups"] if g is not None)
        entry["kind"] = "node" if entry["argv0"] == node_path else "git" if entry["argv0"] == git_path else "other"
        entry["record_count"] = len(entry["records"])
        distinct_rows.append(entry)
    simulated = sorted({(row["pid"], row["command"]) for row in pids if row["class"].startswith("simulated")})
    tool_self = [row for row in pids if row["class"].startswith("tool-self")]

    # Audit events by command (unique per file: the run.json lists repeat each row's event).
    by_command = {}
    for event in events:
        key = event["command"]
        by_command.setdefault(key, []).append(event)
    event_summary = {}
    for key, rows in sorted(by_command.items()):
        per_file = {}
        for row in rows:
            per_file.setdefault(os.path.relpath(row["file"], evidence), []).append(row)
        event_summary[key] = {name: {"count": len(items),
                                     "argv0": sorted({str(i["argv0"]) for i in items}),
                                     "events": sorted({str(i["event"]) for i in items}),
                                     "blocked": sorted({str(i["blocked"]) for i in items})}
                              for name, items in per_file.items()}

    # FC-P3 probe records.
    probes = {}
    for name in ("observe-001.probes.json", "s7-001-c16-direct-probe-r1.probes.json", "s7-001-c17-cohort.probes.json",
                 "s7-001-c19-direct-probe-r2.probes.json"):
        document = json.load(open(os.path.join(evidence, name)))
        targets = []
        for target in document["targets"]:
            recorded = target.get("pair", {}).get("recorded", {})
            targets.append({"pid": recorded.get("pid"), "group": recorded.get("process_group"), "argv0": recorded.get("argv0"),
                            "kill": target.get("kill"), "killpg": target.get("killpg"), "state": target.get("state")})
        probes[name] = {"targets": targets, "process_events": len(document.get("process_events", [])),
                        "boot_before": document.get("boot_before"), "boot_after": document.get("boot_after"),
                        "all_absent": all(t["state"] == "absent" and t["kill"] == "ESRCH" and t["killpg"] == "ESRCH"
                                          for t in targets)}

    # UNKNOWN or interrupted markers.
    markers = {}
    for run in ("s7-001-r1", "s7-001-r2"):
        document = json.load(open(os.path.join(evidence, run, "run.json")))
        markers[run] = {"state": document["state"], "interrupted": document["interrupted"],
                        "stopped_reason": document["stopped_reason"], "node_starts": document["node_starts"],
                        "rows": [(r["id"], r["state"], r["start_count_state"], r["actual_starts"], r["interrupted"])
                                 for r in document["rows"]]}
    for name in ("s7-001-cohort-outcomes", "s7-001-mc37-outcomes"):
        document = json.load(open(os.path.join(evidence, name, "outcomes.json")))
        journal = [json.loads(line) for line in open(os.path.join(evidence, name, "journal.jsonl")) if line.strip()]
        markers[name] = {"state": document["state"], "interrupted": document["interrupted"],
                         "journal_lines": len(journal), "journal_recorded_lines": document["journal"]["lines"],
                         "journal_failure": document["journal"]["failure"],
                         "journal_first": journal[0]["kind"], "journal_last": journal[-1]["kind"],
                         "outcome_counts": document["outcome_counts"]}
    cohort_root = freeze["audit_inputs"]["cohort_root"]
    for case in ("Q01-positive", "Q03-positive", "Q01-changed-reference"):
        ledger = json.load(open(os.path.join(cohort_root, "provider-ledgers", case, "result.json")))
        markers["C17/" + case] = {"state": ledger["state"], "expected_checker_starts": ledger["expected_checker_starts"],
                                  "actual_checker_starts": ledger["actual_checker_starts"],
                                  "provider_failure": ledger["provider_failure"],
                                  "finalization_failed_present": os.path.lexists(
                                      os.path.join(cohort_root, "provider-ledgers", case, "finalization.failed.json"))}
    cohort = json.load(open(os.path.join(cohort_root, "cohort.json")))
    markers["C17/cohort.json"] = {"passed": cohort["passed"], "actual_checker_starts": cohort.get("actual_checker_starts"),
                                  "expected_cases": cohort.get("expected_cases")}
    unknown_strings = []
    for path in files:
        text = open(path, "rb").read().decode("utf-8", "replace")
        for token in ('"UNKNOWN"', '"state": "UNKNOWN"', '"interrupted": true'):
            if token in text:
                unknown_strings.append((os.path.relpath(path, evidence), token))

    node_starts = [row for row in distinct_rows if row["kind"] == "node"]
    report = {
        "schema": "w4-audit-001.a02-starts/1",
        "files_parsed": len(files), "parse_errors": parse_errors,
        "positive_pid_dicts": len(pids),
        "distinct_started_pids": distinct_rows,
        "simulated_receipts": simulated,
        "tool_self_pids": [{"file": os.path.relpath(r["file"], evidence), "pid": r["pid"], "command": r["command"]}
                           for r in tool_self],
        "unclassified": [r for r in pids if r["class"] == "other"],
        "events_by_command": event_summary,
        "probes": probes, "markers": markers, "unknown_strings": unknown_strings,
        "totals": {
            "node_distinct_pids": len(node_starts),
            "node_by_command": {cid: sum(1 for r in node_starts if cid in r["commands"]) for cid in
                                sorted({c for r in node_starts for c in r["commands"]})},
            "git_distinct_pids": [r["pid"] for r in distinct_rows if r["kind"] == "git"],
            "other_distinct_pids": [r["pid"] for r in distinct_rows if r["kind"] == "other"],
        },
    }
    for row in report["distinct_started_pids"]:
        row["records"] = [os.path.relpath(p.split("#")[0], evidence) + "#" + p.split("#", 1)[1] for p in row["records"]]
    data = json.dumps(report, indent=1, sort_keys=True, default=list).encode()
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    print("files parsed", len(files), "parse errors", parse_errors)
    print("positive-pid dicts", len(pids))
    for row in distinct_rows:
        print("pid", row["pid"], row["kind"], row["commands"], "records", row["record_count"], "receipts", row["receipts"],
              "cleanup_ok", row["cleanup_ok"], "groups", row["groups"])
    print("simulated", simulated)
    print("tool-self pids", len(tool_self))
    print("unclassified", [(os.path.relpath(r["file"], evidence), r["pointer"], r["pid"]) for r in report["unclassified"]])
    for key, value in event_summary.items():
        for name, info in value.items():
            print("events", key, name, info)
    for name, info in probes.items():
        print("probe", name, info["all_absent"], info["targets"], "events", info["process_events"])
    for name, info in markers.items():
        print("marker", name, json.dumps(info))
    print("unknown strings", unknown_strings)
    print("totals", json.dumps(report["totals"]))


main()
