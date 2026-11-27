"""W4 audit 001, a03: items 3 and 6 (record side), the direct-probe rows of C16 (R1) and C19 (R2).

Usage: a03_direct_probe.py FREEZE OUTPUT
For every row: one actual Node start (one audit event, one started record, one receipt with a positive
PID, the same PID everywhere), exit status, supervisor error, stdout and stderr against the files,
the refusal selector, probe.json presence and content, the stage's entries, the boot. Then the
source-backed inference of P07 section 5: where the bound probe and loader import the readers.
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


H01 = "CH-SELECTION: manifest digest is not external approval"
H02 = "Current-host binding: wrong configuration contract/schema"
ENV_DIFFERS = "Current-host binding: actual Node environment differs"
INPUT_DIFFERS = "Actual input identity differs"


def row_audit(run_dir, row_id, node_path, boot):
    out = json.load(open(os.path.join(run_dir, row_id, "outcome.json")))
    intent = json.load(open(os.path.join(run_dir, row_id, "intent.json")))
    started = json.load(open(os.path.join(run_dir, row_id, "started-1.json")))
    process = out["process"]
    stage = out["row"]["stage"]
    label = out["row"]["label"]
    receipt_path = os.path.join(stage, label + ".process.json")
    receipt = json.load(open(receipt_path))
    stdout_path = os.path.join(stage, label + ".stdout.log")
    stderr_path = os.path.join(stage, label + ".stderr.log")
    stdout = open(stdout_path, "rb").read().decode()
    stderr = open(stderr_path, "rb").read().decode()
    started_process = started.get("process", started)
    events = out["process_events"]
    entries = sorted(os.listdir(stage))
    result = {
        "row": row_id, "state": out["state"], "start_count_state": out["start_count_state"],
        "actual_starts": out["actual_starts"], "interrupted": out["interrupted"], "expectation_met": out["expectation_met"],
        "boot_ok": out["boot_before"] == out["boot_after"] == boot and out["boot_unchanged"] is True,
        "events": len(events), "event_argv_equals_receipt": len(events) == 1 and events[0]["argv"] == process["argv"],
        "event_executable_is_bound_node": len(events) == 1 and events[0]["executable"] == node_path,
        "pid": process["pid"], "pid_positive": isinstance(process["pid"], int) and process["pid"] > 0,
        "group_equals_pid": process["process_group"] == process["pid"],
        "started_pid_same": started_process.get("pid") == process["pid"],
        "receipt_file_equals_record": receipt == process,
        "returncode": process["returncode"], "error": process["error"],
        "cleanup": process["cleanup"], "handles_closed": process["handles_closed"],
        "receipt_environment": process["environment"],
        "stdout_bytes": len(stdout.encode()), "stderr_bytes": len(stderr.encode()),
        "stdout_recorded_equals_file": out["stdout"]["text"] == stdout and out["stdout"]["sha256"] == sha(stdout_path),
        "stderr_recorded_equals_file": out["stderr"]["text"] == stderr and out["stderr"]["sha256"] == sha(stderr_path),
        "log_bytes": {"observed": process["observed_log_bytes"], "retained": process["retained_log_bytes"],
                      "files": len(stdout.encode()) + len(stderr.encode())},
        "stage": stage, "stage_entries_now": entries,
        "probe_json_present": os.path.lexists(os.path.join(stage, "probe.json")),
        "intent_boot": intent.get("boot_session_uuid") or intent.get("boot"),
        "elapsed_ms": out.get("clock", {}).get("elapsed_ms"), "clock": out.get("clock"),
        "row_limits": {"total_ms": out["row"]["total_ms"], "stage_ms": out["row"]["stage_ms"]},
        "argv": process["argv"],
    }
    result["stderr_has_h01"] = H01 in stderr
    result["stderr_has_h02"] = H02 in stderr
    result["stderr_has_uncaught_error_marker"] = "Error [CurrentHostBindingError]" in stderr or "Error: Current-host" in stderr
    frames = re.findall(r"at (\w+) \(file://[^)]*current_host_readback_v02\.mjs:(\d+):(\d+)\)", stderr)
    frames += [("<module>", a, b) for a, b in re.findall(r"at file://[^ ]*current_host_readback_v02\.mjs:(\d+):(\d+)", stderr)]
    result["stack_frames"] = frames
    if result["probe_json_present"]:
        report = json.load(open(os.path.join(stage, "probe.json")))
        result["probe_json"] = {"passed": report.get("passed"), "error": report.get("error"),
                                "has_khronos": "khronos" in report, "has_three": "three" in report,
                                "has_input_preserved": "input_preserved" in report,
                                "labels_present": report.get("labels") is not None,
                                "labels_boundary": (report.get("labels") or {}).get("boundary")}
        result["stdout_json"] = json.loads(stdout) if stdout.strip() else None
    return result


def main():
    freeze = json.load(open(sys.argv[1]))
    output = sys.argv[2]
    evidence = freeze["evidence"]["parent"]
    boot = freeze["boot_session_uuid"]
    node_path = [b["path"] for b in freeze["bindings"] if b["id"] == "mp:node"][0]
    report = {"schema": "w4-audit-001.a03-direct-probe/1", "rows": {}}
    for run in ("s7-001-r1", "s7-001-r2"):
        run_doc = json.load(open(os.path.join(evidence, run, "run.json")))
        report["rows"][run] = {"state": run_doc["state"], "rows_independent": run_doc["rows_independent"],
                               "node_starts": run_doc["node_starts"], "order": [r["id"] for r in run_doc["rows"]],
                               "results": [row_audit(os.path.join(evidence, run), r["id"], node_path, boot)
                                           for r in run_doc["rows"]],
                               "rows_document": run_doc["inputs"]["rows"]}

    # The mutations of the H01, H02, MC30 and MC36 configurations against the approved one.
    configs = freeze["configurations"]
    approved = json.load(open(configs["approved_cohort"]["path"]))
    mutations = {}
    for key, row in configs["probe_rows"].items():
        mutated = json.load(open(row["config"]["path"]))
        differing = sorted(k for k in set(approved) | set(mutated) if approved.get(k) != mutated.get(k))
        mutations[key] = {"differing_top_level_members": differing,
                          "values": {k: mutated.get(k) for k in differing if k != "host"},
                          "host": mutated.get("host") if "host" in differing else None,
                          "argv_digest": row["argv_digest"], "own_digest": sha(row["config"]["path"]),
                          "argv_digest_is_own_digest": row["argv_digest"] == sha(row["config"]["path"]),
                          "argv_digest_is_D0": row["argv_digest"] == configs["approved_cohort"]["D0"]}
    report["mutations"] = mutations
    # The HOST copies against HOST: only environment.cf_user_text_encoding may differ.
    host = json.load(open(freeze["host"]["HOST"]["path"]))
    copies = {}
    for key, row in configs["host_copies"].items():
        copy = json.load(open(row["path"]))
        differing = []
        for k in sorted(set(host) | set(copy)):
            if host.get(k) != copy.get(k):
                if k == "environment":
                    for kk in sorted(set(host[k]) | set(copy[k])):
                        if host[k].get(kk) != copy[k].get(kk):
                            differing.append("environment/" + kk)
                else:
                    differing.append(k)
        copies[key] = {"differing": differing, "cf_value": copy["environment"]["cf_user_text_encoding"],
                       "host_cf_value": host["environment"]["cf_user_text_encoding"]}
    report["host_copies"] = copies

    # The source-backed inference: where the probe and the loader import the readers.
    wt = freeze["places"]["worktree"]
    probe_path = os.path.join(wt, "prototypes/static_tray_v01/current_host_readback_v02.mjs")
    lines = open(probe_path, encoding="utf-8").read().split("\n")
    def find(pattern):
        return [i + 1 for i, line in enumerate(lines) if re.search(pattern, line)]
    static_imports = [(i + 1, line.strip()) for i, line in enumerate(lines) if re.match(r"\s*import\s.*\sfrom\s+'", line)]
    dynamic_imports = [(i + 1, line.strip()) for i, line in enumerate(lines) if re.search(r"\bimport\s*\(", line)]
    require_calls = [(i + 1, line.strip()) for i, line in enumerate(lines) if re.search(r"\brequire\s*\(", line)]
    anchors = {
        "approvedEnvelope_call": find(r"^const envelope = approvedEnvelope\(args\);"),
        "try_block": find(r"^try \{"),
        "verifyBootstrap_call": find(r"^\s+verifyBootstrap\(envelope, manifest\);"),
        "input_identity_check": find(r"Actual input identity differs"),
        "validator_require": find(r"require\(manifest\.validator_entry\)"),
        "three_import": find(r"import\(pathToFileURL\(manifest\.three_entry\)"),
        "gltf_import": find(r"import\(pathToFileURL\(manifest\.gltf_loader_entry\)"),
        "environment_check": find(r"'actual Node environment differs'"),
        "h01_selector": find(r"'manifest digest is not external approval'"),
        "h02_selector": find(r"'wrong configuration contract/schema'"),
        "requireSelection_throw": find(r"const error = Error\('CH-SELECTION: ' \+ message\);"),
        "requireValue_throw": find(r"if \(!condition\) throw Error\('Current-host binding: ' \+ message\);"),
        "output_call": find(r"^output\(job\.result, report\);"),
        "verifyHost_call_in_bootstrap": find(r"host = verifyHost\(config\);"),
        "function_approvedEnvelope": find(r"^function approvedEnvelope\("),
        "function_verifyBootstrap": find(r"^function verifyBootstrap\("),
        "function_verifyHost": find(r"^function verifyHost\("),
    }
    order_ok = (anchors["approvedEnvelope_call"][0] < anchors["try_block"][0] < anchors["verifyBootstrap_call"][0]
                < anchors["input_identity_check"][-1] < anchors["validator_require"][0] < anchors["three_import"][0]
                < anchors["gltf_import"][0])
    loader_path = [b["path"] for b in freeze["bindings"] if b["id"] == "reader:tools/three_loader.mjs"][0]
    loader_lines = open(loader_path, encoding="utf-8").read().split("\n")
    loader_static = [line.strip() for line in loader_lines if re.match(r"\s*import\s", line)]
    loader_dynamic = [line.strip() for line in loader_lines if re.search(r"\bimport\s*\(|\brequire\s*\(", line)]
    report["inference"] = {
        "probe_sha256": sha(probe_path), "loader_sha256": sha(loader_path),
        "static_imports": static_imports,
        "static_import_specifiers": sorted({re.search(r"from\s+'([^']+)'", s).group(1) for _, s in static_imports}),
        "dynamic_imports": dynamic_imports, "require_calls": require_calls, "anchors": anchors,
        "order_envelope_before_try_before_bootstrap_before_readers": order_ok,
        "loader_static_imports": loader_static, "loader_dynamic_imports_or_requires": loader_dynamic,
        "loader_exports": [line.strip() for line in loader_lines if line.startswith("export")],
    }
    data = json.dumps(report, indent=1, sort_keys=True).encode()
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    for run, info in report["rows"].items():
        print(run, info["state"], "independent", info["rows_independent"], info["node_starts"], info["order"])
        for r in info["results"]:
            print(" ", json.dumps({k: v for k, v in r.items() if k not in ("argv", "receipt_environment")}))
    print("mutations", json.dumps(mutations))
    print("host copies", json.dumps(copies))
    print("inference", json.dumps(report["inference"]))


main()
