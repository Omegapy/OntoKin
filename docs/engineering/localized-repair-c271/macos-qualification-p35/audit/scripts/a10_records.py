"""W4 audit 001, a10: items 10 and 11. The audit_expect sets evaluated with this auditor's own evaluator,
and the consistency of every S7 command's records (FC-K2 and FC-K3) in the frozen order.

Usage: a10_records.py FREEZE FREEZE_SHA256 OUTPUT
Starts nothing (an audit hook refuses process creation).
"""
import hashlib
import json
import os
import re
import sys


def _refuse(event, args):
    if event in ("subprocess.Popen", "os.posix_spawn", "os.exec", "os.fork", "os.forkpty", "os.spawn",
                 "os.system", "os.startfile"):
        raise PermissionError("this audit script starts no process: " + event)


sys.addaudithook(_refuse)


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def resolve(document, pointer):
    current = document
    if pointer in ("", None):
        return True, current
    for token in pointer[1:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict) and token in current:
            current = current[token]
        elif isinstance(current, list) and token.isdigit() and int(token) < len(current):
            current = current[int(token)]
        else:
            return False, None
    return True, current


def strict_equal(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a == b
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(strict_equal(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return set(a) == set(b) and all(strict_equal(a[k], b[k]) for k in a)
    return type(a) is type(b) and a == b


def evaluate(rule):
    """This auditor's own reading of the predicate forms that audit_expect uses."""
    path = rule["file"]
    if "exists" in rule:
        return os.path.lexists(path) == rule["exists"], None
    if not os.path.isfile(path):
        return False, "absent"
    if "sha256" in rule:
        observed = sha(path)
        return observed == rule["sha256"], observed
    document = json.load(open(path))
    found, value = resolve(document, rule.get("pointer", ""))
    if not found:
        return False, "pointer not found"
    if "count_where" in rule:
        inner = rule["count_where"]
        count = 0
        for item in value:
            ok, item_value = resolve(item, inner.get("pointer", ""))
            if ok and strict_equal(item_value, inner["equals"]):
                count += 1
        return count == rule["equals"], count
    if "length" in rule:
        return len(value) == rule["length"], len(value)
    if "equals" in rule:
        return strict_equal(value, rule["equals"]), value if not isinstance(value, (list, dict)) else "(structure)"
    raise ValueError("unhandled predicate form: " + json.dumps(rule))


def main():
    freeze_path, freeze_sha, output = sys.argv[1], sys.argv[2], sys.argv[3]
    assert sha(freeze_path) == freeze_sha
    freeze = json.load(open(freeze_path))
    E = freeze["evidence"]["parent"]
    commands = {c["id"]: c for c in freeze["commands"]}
    report = {"schema": "w4-audit-001.a10-records/1"}

    # Item 10: every audit_expect rule, with this auditor's own evaluator.
    audit = {}
    for cid, command in commands.items():
        rules = command.get("audit_expect") or []
        if rules:
            rows = []
            for rule in rules:
                ok, observed = evaluate(rule)
                rows.append({"rule": rule, "ok": ok, "observed": observed})
            audit[cid] = {"rules": len(rows), "met": all(r["ok"] for r in rows), "rows": rows}
    report["audit_expect"] = audit

    # Deferred argument values, derived as the freeze states them.
    values = {"<FREEZE-002.json SHA-256>": freeze_sha}
    for name, spec in freeze["deferred_arguments"].items():
        if spec.get("kind") == "value_from":
            found, value = resolve(json.load(open(spec["file"])), spec["pointer"])
            values[name] = value if found else None
    discovery_now = {"<baseline discovery SHA-256>": sha(os.path.join(E, "s7-001-discovery-baseline.json")),
                     "<current discovery SHA-256>": sha(os.path.join(E, "s7-001-discovery-current.json"))}
    report["deferred_values"] = {"values": values, "discovery_files_now": discovery_now,
                                 "equal": all(values[k] == discovery_now[k] for k in discovery_now)}

    # Item 11: the records of each command, in the frozen order.
    order = freeze["order"]
    rows, previous_end = [], None
    for cid in order:
        command = commands[cid]
        records = command["records"]
        row = {"id": cid, "name": command["name"]}
        try:
            record = json.load(open(records["command"]))
        except (OSError, ValueError) as error:
            row["record_error"] = repr(error)
            rows.append(row)
            continue
        expected_argv = [values.get(a, a) if a in values else a for a in command["argv"]]
        expected_argv = [a for a in expected_argv]
        for placeholder, value in values.items():
            expected_argv = [a.replace(placeholder, value) if isinstance(a, str) and placeholder in a else a for a in expected_argv]
        start, end, wall = float(record["start_epoch_s"]), float(record["end_epoch_s"]), float(record["wall_time_s"])
        exit_text = open(records["exit"]).read()
        stdout_sha, stderr_sha = sha(records["stdout"]), sha(records["stderr"])
        env_file = command["environment"]["file"]
        exit_rule = [r for r in command.get("expect", []) if r.get("file") == records["exit"] and "text_equals" in r]
        row.update({
            "schema": record["schema"] == "ontokin.c271.p35-command-record/1", "name_ok": record["name"] == command["name"],
            "argv_ok": record["argv"] == expected_argv, "cwd_ok": record["cwd"] == command["cwd"],
            "env_file_ok": record["environment"]["file"] == env_file,
            "env_sha_ok": record["environment"]["sha256"] == sha(env_file) == command["environment"]["sha256"],
            "boot_ok": record["boot"]["before"] == record["boot"]["after"] == freeze["boot_session_uuid"],
            "wall_ok": abs((end - start) - wall) < 2e-6, "wall_s": wall, "outer_bound_s": command["limits"].get("outer_bound_s"),
            "within_outer_bound": wall <= command["limits"].get("outer_bound_s", 1e9),
            "exit_status": record["exit"]["status"], "exit_file_ok": exit_text == "%d\n" % record["exit"]["status"],
            "exit_expected": exit_rule[0]["text_equals"].strip() if exit_rule else None,
            "streams_ok": record["streams"]["stdout"]["sha256"] == stdout_sha and record["streams"]["stderr"]["sha256"] == stderr_sha
            and record["streams"]["stdout"]["size_bytes"] == os.path.getsize(records["stdout"])
            and record["streams"]["stderr"]["size_bytes"] == os.path.getsize(records["stderr"]),
            "stdout_bytes": os.path.getsize(records["stdout"]), "stderr_bytes": os.path.getsize(records["stderr"]),
            "retries": record["retries"], "written_by_ok": record["written_by"] == "director/run/run_once_v2.sh",
            "started_at_utc": record["started_at_utc"], "ended_at_utc": record["ended_at_utc"],
            "start_epoch_s": record["start_epoch_s"], "end_epoch_s": record["end_epoch_s"],
            "after_previous": previous_end is None or start > previous_end,
            "gap_s": None if previous_end is None else round(start - previous_end, 3),
        })
        if cid.endswith(".X"):
            checker = json.loads(open(records["stdout"]).read())
            main_id = cid[:-2]
            row["checker"] = {"state": checker["state"], "failed": len(checker["failed"]), "command": checker["command"],
                              "phase": checker["phase"], "predicate_set": checker.get("predicate_set"),
                              "predicates": len(checker["checks"].get("predicates", [])),
                              "frozen_predicates": len(commands[main_id]["expect"])}
        if cid in ("P01", "D02", "Q04"):
            checker = json.loads(open(records["stdout"]).read())
            row["checker"] = {"state": checker["state"], "failed": len(checker["failed"]), "phase": checker["phase"],
                              "bindings": len(checker["checks"].get("bindings", [])),
                              "bindings_ok": all(b["ok"] for b in checker["checks"].get("bindings", [])),
                              "absent_checked": (checker["checks"].get("absent") or {}).get("checked"),
                              "prepared": len(checker["checks"].get("prepared", [])),
                              "prepared_inputs": len(checker["checks"].get("prepared_inputs", [])),
                              "earlier_commands": len(checker["checks"].get("earlier_commands", []))}
        if cid == "P00":
            text = open(records["stdout"]).read()
            row["p00"] = {"ok_lines": sum(1 for line in text.splitlines() if line.endswith(": OK")),
                          "other_lines": [line for line in text.splitlines() if not line.endswith(": OK")]}
        rows.append(row)
        previous_end = end
    failures = []
    for row in rows:
        for key in ("schema", "name_ok", "argv_ok", "cwd_ok", "env_file_ok", "env_sha_ok", "boot_ok", "wall_ok",
                    "within_outer_bound", "exit_file_ok", "streams_ok", "written_by_ok", "after_previous"):
            if row.get(key) is not True:
                failures.append((row["id"], key))
        if row.get("retries") != 0:
            failures.append((row["id"], "retries"))
        if row.get("exit_expected") is not None and str(row.get("exit_status")) != row["exit_expected"]:
            failures.append((row["id"], "exit differs from the frozen expectation"))
        if "checker" in row and row["checker"]["state"] != "MET":
            failures.append((row["id"], "checker state"))
        if cid_is_x(row["id"]) and row.get("checker", {}).get("predicates") != row.get("checker", {}).get("frozen_predicates"):
            failures.append((row["id"], "predicate count"))
    first, last = rows[0], rows[-1]
    report["records"] = {"commands": len(rows), "failures": failures, "rows": rows,
                         "first_start_utc": first.get("started_at_utc"), "last_end_utc": last.get("ended_at_utc"),
                         "nonzero_exits": [(r["id"], r["exit_status"]) for r in rows if r.get("exit_status") != 0],
                         "max_wall": max((r["wall_s"], r["id"]) for r in rows if "wall_s" in r),
                         "x_predicate_total": sum(r.get("checker", {}).get("predicates", 0) for r in rows if r["id"].endswith(".X"))}
    # No record of a command that is not in the order, and no capture or failure record.
    names = {commands[c]["name"] for c in order}
    present = sorted(n for n in os.listdir(E) if n.endswith(".command.json"))
    report["unexpected_command_records"] = [n for n in present if n[:-len(".command.json")] not in names
                                            and not n.startswith("observe-001")]
    report["capture_records"] = sorted(n for n in os.listdir(E) if "failure-capture" in n or ".overrun-probes-" in n
                                       or ".stop-" in n)
    capture_paths = []
    for cid in freeze["capture_commands"]:
        command = commands[cid]
        for path in list((command.get("records") or {}).values()) + list(command.get("outputs") or []):
            capture_paths.append((cid, path, os.path.lexists(path)))
    report["capture_command_paths_present"] = [p for p in capture_paths if p[2]]
    report["capture_command_paths_checked"] = len(capture_paths)
    data = json.dumps(report, indent=1, sort_keys=True).encode()
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    for cid, value in audit.items():
        print("audit_expect", cid, value["rules"], "met", value["met"], [(r["ok"], r["observed"]) for r in value["rows"]])
    print("deferred", json.dumps(report["deferred_values"]))
    print("records", len(rows), "failures", failures)
    print("first start", first.get("started_at_utc"), "last end", last.get("ended_at_utc"))
    print("nonzero exits", report["records"]["nonzero_exits"], "max wall", report["records"]["max_wall"])
    print(".X predicate total", report["records"]["x_predicate_total"])
    for row in rows:
        brief = {k: row.get(k) for k in ("id", "exit_status", "exit_expected", "wall_s", "outer_bound_s", "gap_s", "stdout_bytes", "stderr_bytes", "started_at_utc")}
        if "checker" in row:
            brief["checker"] = row["checker"]
        if "p00" in row:
            brief["p00"] = row["p00"]
        print(json.dumps(brief))
    print("unexpected command records", report["unexpected_command_records"])
    print("capture records", report["capture_records"], "capture paths present", report["capture_command_paths_present"],
          "checked", report["capture_command_paths_checked"])


def cid_is_x(cid):
    return cid.endswith(".X")


main()
