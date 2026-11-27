"""W4 audit 001, a06: items 6, 7, 8 and 12 from the records: N-04 with MC30-probe and MC36, every MH
control of the freeze's table with its label, the limits, and the labels of contract section 10.

Usage: a06_controls.py FREEZE OUTPUT
Starts nothing (an audit hook refuses process creation).
"""
import hashlib
import json
import os
import re
import stat
import sys


def _refuse(event, args):
    if event in ("subprocess.Popen", "os.posix_spawn", "os.exec", "os.fork", "os.forkpty", "os.spawn",
                 "os.system", "os.startfile"):
        raise PermissionError("this audit script starts no process: " + event)


sys.addaudithook(_refuse)
DARWIN_PID_MAX = 99999


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def load(path):
    return json.load(open(path))


def checker_record(path):
    """The checker writes one JSON document on stdout (indented)."""
    return json.loads(open(path, encoding="utf-8").read())


def main():
    freeze = load(sys.argv[1])
    output = sys.argv[2]
    E = freeze["evidence"]["parent"]
    wt = freeze["places"]["worktree"]
    cohort_root = freeze["audit_inputs"]["cohort_root"]
    node_path = [b["path"] for b in freeze["bindings"] if b["id"] == "mp:node"][0]
    host = load(freeze["host"]["HOST"]["path"])
    declared = load(freeze["environments"]["declared"]["path"])
    report = {"schema": "w4-audit-001.a06-controls/1"}

    # ---- Item 6: N-04 ----------------------------------------------------------------------------------
    receipts = {}
    receipts["S5/M1"] = load(os.path.join(E, "observe-001/node_version/host-node-version.process.json"))
    for run in ("s7-001-r1", "s7-001-r2"):
        for row in load(os.path.join(E, run, "run.json"))["rows"]:
            receipts[run + "/" + row["id"]] = load(os.path.join(E, run, row["id"], "outcome.json"))["process"]
    for case in ("Q01-positive", "Q03-positive", "Q01-changed-reference"):
        receipts["C17/" + case] = load(os.path.join(cohort_root, case, "synthetic-readback.process.json"))
    envs = {k: v["environment"] for k, v in receipts.items()}
    declared_env = declared.get("environment", declared)
    report["n04"] = {
        "receipt_environments_identical": len({json.dumps(v, sort_keys=True) for v in envs.values()}) == 1,
        "receipt_environment": envs["S5/M1"],
        "receipt_environment_equals_declared_file": envs["S5/M1"] == declared_env,
        "receipt_environment_equals_host_declared": envs["S5/M1"] == host["environment"]["declared"],
        "same_executable": len({r["argv"][0] for r in receipts.values()}) == 1 and receipts["S5/M1"]["argv"][0] == node_path,
        "node_binding_now": sha(node_path) == host["runtime"]["binding"]["sha256"],
        "host_cf_value": host["environment"]["cf_user_text_encoding"],
        "host_cf_uid": int(host["environment"]["cf_user_text_encoding"].split(":")[0], 16),
    }
    positives = {}
    for case in ("Q01-positive", "Q03-positive", "Q01-changed-reference"):
        probe = load(os.path.join(cohort_root, case, "probe.json"))
        manifest = load(os.path.join(cohort_root, "supplemental-cpu.json"))
        positives[case] = {"passed": probe["passed"], "error": probe.get("error"),
                           "reached_scientific_body": "three" in probe and "khronos" in probe,
                           "manifest_host_sha256": manifest["host"]["sha256"],
                           "probe_json_uid": os.lstat(os.path.join(cohort_root, case, "probe.json")).st_uid}
    report["n04"]["cohort_starts"] = positives
    for name, key in (("MC30-probe", "mc30"), ("MC36", "mc36")):
        stage = freeze["configurations"]["probe_rows"][key]["stage"]
        probe = load(os.path.join(stage, "probe.json"))
        report["n04"][name] = {"error": probe.get("error"), "passed": probe.get("passed"),
                               "khronos_member": "khronos" in probe, "three_member": "three" in probe,
                               "probe_json_uid": os.lstat(os.path.join(stage, "probe.json")).st_uid,
                               "host_copy_cf": load(freeze["configurations"]["host_copies"][key]["path"])["environment"]["cf_user_text_encoding"]}
    r2 = load(os.path.join(E, "s7-001-r2/run.json"))
    c17 = load(os.path.join(E, "s7-001-c17-cohort.command.json"))
    c19 = load(os.path.join(E, "s7-001-c19-direct-probe-r2.command.json"))
    report["n04"]["order"] = {"r2_rows": [r["id"] for r in r2["rows"]], "rows_independent": r2["rows_independent"],
                              "c19_started_after_c17_ended": float(c19["start_epoch_s"]) > float(c17["end_epoch_s"])}
    cf = freeze["host_facts"][0]
    info = os.lstat(cf["path"])
    report["n04"]["cf_file_now"] = {"sha256": sha(cf["path"]), "size": info.st_size, "mode": "0o%03o" % stat.S_IMODE(info.st_mode),
                                    "nlink": info.st_nlink, "uid": info.st_uid,
                                    "equals_frozen": sha(cf["path"]) == cf["sha256"] and info.st_size == cf["size_bytes"]
                                    and "0o%03o" % stat.S_IMODE(info.st_mode) == cf["mode"] and info.st_nlink == 1,
                                    "uid_equals_cf_prefix": info.st_uid == report["n04"]["host_cf_uid"]}
    cf_checks = {}
    for name, cid in (("P01", "s7-001-p01-check-pre.stdout.txt"), ("D02", "s7-001-d02-check-prepared.stdout.txt"),
                      ("Q04", "s7-001-q04-check-post.stdout.txt"), ("C17.X", "s7-001-c17-cohort.expect.stdout.txt")):
        record = checker_record(os.path.join(E, cid))
        found = []
        for item in record["checks"].get("host_facts", []):
            found.append({"ok": item["ok"], "sha256": item.get("observed", {}).get("sha256"), "mode": item.get("observed", {}).get("mode")})
        for item in record["checks"].get("predicates", []):
            if item["rule"].get("file") == cf["path"]:
                found.append({"ok": item["ok"], "sha256": item.get("observed")})
        cf_checks[name] = {"state": record["state"], "cf_checks": found}
    report["n04"]["cf_file_records"] = cf_checks
    outcomes = load(os.path.join(E, "s7-001-cohort-outcomes/outcomes.json"))
    report["n04"]["c17_supervisor_loaded"] = [row for row in outcomes["loaded_project_files"]
                                              if row["path"].endswith("supervisor_darwin_v01.py") or row["path"].endswith("supervisor.py")]
    report["n04"]["runner_supervisor_loaded"] = {run: [row for row in load(os.path.join(E, run, "run.json"))["loaded_project_files"]
                                                       if "supervisor" in row["path"]] for run in ("s7-001-r1", "s7-001-r2")}
    report["n04"]["c17_admitted_cf"] = outcomes["environment"]["admitted_cf_user_text_encoding"]

    # ---- Item 7: the controls --------------------------------------------------------------------------
    controls = {}
    # MC10
    mc10 = {}
    for name, cid, expect in (("s7-001-mc10-node-v24-22-0", "C03", "refused-output"),
                              ("s7-001-mc10-node-v24-22-1-without-newline", "C04", "refused-output"),
                              ("s7-001-mc10-node-v24-22-1", "C05", "accepted")):
        doc = load(os.path.join(E, name + ".json"))
        attempt = os.path.join(E, name)
        files = sorted(os.listdir(attempt))
        pids = []
        for sub in ("git_version", "node_version"):
            receipt = load(os.path.join(attempt, sub, ("host-git-version" if sub == "git_version" else "host-node-version") + ".process.json"))
            pids.append(receipt["pid"])
        entry = {"command": cid, "state": doc["state"], "expectation_met": doc["expectation_met"],
                 "checks_all_true": all(doc["checks"].values()), "checks": doc["checks"],
                 "process_events": len(doc["process_events"]), "substituted": doc["substituted"],
                 "simulated_node_stdout": bytes.fromhex(doc["simulated_outputs"]["node_version_hex"]).decode(),
                 "simulated_git_stdout": bytes.fromhex(doc["simulated_outputs"]["git_version_hex"]).decode(),
                 "observation_error": (doc.get("observation_error") or {}).get("code"),
                 "attempt_files": files, "host_present": "HOST.json" in files, "completion_present": "completion.json" in files,
                 "receipt_pids": pids, "receipt_pids_impossible": all(p > DARWIN_PID_MAX for p in pids),
                 "expected": expect}
        if "HOST.json" in files:
            mc10_host = load(os.path.join(attempt, "HOST.json"))
            entry["host_labels_boundary"] = mc10_host["labels"]["boundary"]
            entry["host_runtime_version"] = mc10_host["runtime"]["version"]
            entry["completion_state"] = load(os.path.join(attempt, "completion.json")).get("state")
        mc10[cid] = entry
    controls["MC10"] = mc10
    # MC11
    scan = load(os.path.join(E, "s7-001-mc11-scan.json"))
    controls["MC11"] = {"frozen_rule": scan["frozen_rule"], "wider_scan": scan["wider_scan"], "none_found": scan["none_found"],
                        "reviewed_list_given": scan["reviewed_list_given"], "reviewed_list_matches": scan["reviewed_list_matches"],
                        "unresolved_relative_specifiers": scan["unresolved_relative_specifiers"], "totals": scan["totals"],
                        "files": len(scan["files"]), "limit": scan["limit"],
                        "reviewed_list": scan["inputs"].get("reviewed"), "probe_input": scan["inputs"]["probe"]["sha256"]}
    # MC28, recomputed from the two discovery documents and the additions record.
    baseline = load(os.path.join(E, "s7-001-discovery-baseline.json"))
    current = load(os.path.join(E, "s7-001-discovery-current.json"))
    additions_path = os.path.join(wt, "docs/engineering/localized-repair-c271/macos-implementation-p33/INVENTORY-ADDITIONS.json")
    additions = load(additions_path)
    b_ids, c_ids = baseline["ids_in_discovery_order"], current["ids_in_discovery_order"]
    expected = (set(b_ids) | set(additions["added"])) - set(additions["removed"])
    by_module = {}
    for item in additions["added"]:
        by_module[item.split(".")[0]] = by_module.get(item.split(".")[0], 0) + 1
    compare = load(os.path.join(E, "s7-001-discovery-compare.json"))
    controls["MC28"] = {
        "baseline_count": len(b_ids), "baseline_unique": len(set(b_ids)), "current_count": len(c_ids), "current_unique": len(set(c_ids)),
        "added": len(additions["added"]), "added_unique": len(set(additions["added"])), "removed": len(additions["removed"]),
        "added_already_in_baseline": len(set(additions["added"]) & set(b_ids)),
        "added_by_module_recomputed": by_module, "added_by_module_declared": additions["added_by_module"],
        "missing": sorted(expected - set(c_ids))[:20], "extra": sorted(set(c_ids) - expected)[:20],
        "exact": expected == set(c_ids) and len(c_ids) == len(set(c_ids)),
        "baseline_sorted_sha256_recomputed": hashlib.sha256("\n".join(sorted(set(b_ids))).encode()).hexdigest(),
        "baseline_sorted_sha256_recorded": baseline["sorted_sha256"],
        "current_sorted_sha256_recomputed": hashlib.sha256("\n".join(sorted(set(c_ids))).encode()).hexdigest(),
        "current_sorted_sha256_recorded": current["sorted_sha256"],
        "baseline_modules": baseline["module_count"], "current_modules": current["module_count"],
        "modules_recomputed": (len({i.split(".")[0] for i in b_ids}), len({i.split(".")[0] for i in c_ids})),
        "failed_imports": (len(baseline["failed_imports"]), len(current["failed_imports"])),
        "loader_errors": (len(baseline["loader_errors"]), len(current["loader_errors"])),
        "process_events": (len(baseline["process_events"]), len(current["process_events"])),
        "bytecode_present": (len(baseline["bytecode_present"]), len(current["bytecode_present"])),
        "duplicates": (baseline["duplicates"], current["duplicates"]),
        "states": (baseline["state"], current["state"]),
        "compare_tool": {"exact_match": compare["exact_match"], "missing": compare["missing"], "extra": compare["extra"],
                         "expected_count": compare["expected_count"], "current_count": compare["current_count"]},
        "additions_sha256": sha(additions_path),
        "seven_original_ids_in_current": all(("test_static_tray_readback_v01." + n) in c_ids for n in [
            "ReadbackCPUControls.test_q01_actual_synthetic_meshes_load_in_both_libraries",
            "ReadbackCPUControls.test_q03_actual_synthetic_rotations_load_in_both_libraries",
            "ReadbackCPUControls.test_three_rejects_changed_synthetic_reference",
            "ReadbackCoordinatorSeams.test_result_write_failure_leaves_predecessor_gate_blocked",
            "ReadbackCoordinatorSeams.test_host_alarm_cannot_interrupt_supervisor_cleanup",
            "ReadbackCoordinatorSeams.test_success_finalization_uses_remaining_outer_alarm",
            "ReadbackCoordinatorSeams.test_uncertain_marker_removal_recreates_pending"]),
        "discovery_roots": (baseline.get("root"), current.get("root")),
    }
    # MC29
    mc29 = {}
    sources = freeze["configurations"]["mc29_sources"]
    for name, case in (("s7-001-mc29-configuration", "configuration"), ("s7-001-mc29-job-input", "job-input")):
        doc = load(os.path.join(E, name + ".json"))
        mc29[case] = {"state": doc["state"], "expectation_met": doc["expectation_met"], "checks_all_true": all(doc["checks"].values()),
                      "attempt_code": doc["attempt_error"]["code"], "attempt_reason": doc["attempt_error"]["reason"],
                      "accounting_code": doc["finish_error"]["code"], "accounting_reason": doc["finish_error"]["reason"],
                      "setup_error": doc["setup_error"], "supervisor_calls": len(doc["supervisor_calls"]),
                      "on_started_calls": doc["on_started_calls"], "node_process_events": len(doc["node_process_events"]),
                      "git_process_events": doc["git_process_events"],
                      "process_events": len(doc["process_events"]), "ledger_labels_boundary": doc["ledger"]["labels"]["boundary"],
                      "ledger_actual_checker_starts": doc["ledger"]["actual_checker_starts"], "ledger_state": doc["ledger"]["state"],
                      "detectors_all_own": all(doc["detectors_are_the_providers_own"].values()),
                      "substituted": doc["substituted"], "boundary": (doc["boundary_before"], doc["boundary_after"])}
    original = open(sources["configuration"]["path"], "rb").read()
    consumed = open(freeze["configurations"]["mc29_copies"]["configuration"], "rb").read()
    mc29["configuration"]["copy_is_source_plus_one_space"] = consumed == original + b" "
    job_glb = open(os.path.join(E, "s7-001-mc29-job-input/run/Q01-positive/synthetic.glb"), "rb").read()
    fixture_glb = open(freeze["configurations"]["fixtures"]["Q01/synthetic.glb"]["path"], "rb").read()
    mc29["job-input"]["glb_is_fixture_plus_one_zero_byte"] = job_glb == fixture_glb + b"\x00"
    mc29["job-input"]["copy_unchanged"] = sha(freeze["configurations"]["mc29_copies"]["job-input"]) == sources["job-input"]["sha256"]
    controls["MC29"] = mc29
    # MC37
    mc37 = load(os.path.join(E, "s7-001-mc37-outcomes/outcomes.json"))
    stderr15 = open(os.path.join(E, "s7-001-c15-mc37.stderr.txt"), encoding="utf-8").read()
    evidence = re.search(r"CONTROL-EVIDENCE (\{.*\})", stderr15)
    refreeze = load(os.path.join(wt, "docs/engineering/localized-repair-c271/macos-implementation-p33/CONTROLS-REFREEZE-002.json"))
    controls["MC37"] = {"state": mc37["state"], "tests": [(t["raw_id"], t["outcome"]) for t in mc37["tests"]],
                        "process_events": [(e["event"], e["argv"]) for e in mc37["process_events"]],
                        "control_evidence": json.loads(evidence.group(1)) if evidence else None,
                        "module_sha256": mc37["module"]["sha256"], "module_unchanged": mc37["module_unchanged"],
                        "module_equals_refreeze_002": mc37["module"]["sha256"] == refreeze["module"]["sha256"],
                        "label_in_test_output": "Label: real." in stderr15,
                        "admitted_cf": mc37["environment"]["admitted_cf_user_text_encoding"]}
    # F-04 (C02 and C17's own reads)
    hs = load(os.path.join(E, "s7-001-host-state.json"))
    ledgers = {}
    for case in ("Q01-positive", "Q03-positive", "Q01-changed-reference"):
        ledger = load(os.path.join(cohort_root, "provider-ledgers", case, "result.json"))
        ledgers[case] = {"boot_before": ledger["boot_before"]["boot_session_uuid"], "boot_after": ledger["boot_after"]["boot_session_uuid"],
                         "os_before": ledger["boot_before"]["os"], "boundary": ledger["labels"]["boundary"],
                         "preflight_platform_equals_host": ledger["preflight"]["host_state"]["platform"] == host["platform"],
                         "postflight_platform_equals_host": ledger["postflight"]["host_state"]["platform"] == host["platform"],
                         "preflight_os_equals_host": ledger["preflight"]["host_state"]["os"] == host["os"],
                         "postflight_os_equals_host": ledger["postflight"]["host_state"]["os"] == host["os"]}
    setup = load(os.path.join(cohort_root, "setup.json"))
    controls["F-04"] = {"C02": {"state": hs["state"], "checks": hs["checks"], "substituted": hs["substituted"],
                                "boundary": (hs["boundary_before"], hs["boundary_after"]), "process_events": len(hs["process_events"]),
                                "observed_platform_equals_host": hs["observed_state"]["platform"] == host["platform"],
                                "observed_os_equals_host": hs["observed_state"]["os"] == host["os"]},
                        "C17": {"setup_boot": setup["boot"]["boot_session_uuid"], "setup_boundary": setup["labels"]["boundary"],
                                "ledgers": ledgers}}
    report["controls"] = controls

    # ---- Item 8: limits -------------------------------------------------------------------------------
    manifest = load(os.path.join(cohort_root, "supplemental-cpu.json"))
    sizes = {}
    for case in ("Q01-positive", "Q03-positive", "Q01-changed-reference"):
        stage = os.path.join(cohort_root, case)
        receipt = load(os.path.join(stage, "synthetic-readback.process.json"))
        total = sum(os.lstat(os.path.join(stage, n)).st_size for n in os.listdir(stage))
        sizes[case] = {"glb": os.path.getsize(os.path.join(stage, "synthetic.glb")),
                       "result": os.path.getsize(os.path.join(stage, "probe.json")),
                       "audit": os.path.getsize(os.path.join(stage, "synthetic-audit.json")),
                       "job": os.path.getsize(os.path.join(stage, "job.json")),
                       "log_bytes": receipt["observed_log_bytes"], "stage_entries": len(os.listdir(stage)), "stage_bytes": total,
                       "process_seconds": receipt["end_monotonic"] - receipt["start_monotonic"]}
    rows_limits = {}
    for run in ("s7-001-r1", "s7-001-r2"):
        for row in load(os.path.join(E, run, "run.json"))["rows"]:
            outcome = load(os.path.join(E, run, row["id"], "outcome.json"))
            rows_limits[row["id"]] = {"total_ms": outcome["row"]["total_ms"], "stage_ms": outcome["row"]["stage_ms"],
                                      "reserve_ms": outcome["row"]["total_ms"] - outcome["row"]["stage_ms"],
                                      "clock": outcome["clock"],
                                      "process_seconds": outcome["process"]["end_monotonic"] - outcome["process"]["start_monotonic"]}
    test_source = open(os.path.join(wt, "tests/test_static_tray_readback_v01.py"), encoding="utf-8").read()
    probe_source = open(os.path.join(wt, "prototypes/static_tray_v01/current_host_readback_v02.mjs"), encoding="utf-8").read()
    supervisor_source = open(os.path.join(wt, "prototypes/static_tray_v01/supervisor.py"), encoding="utf-8").read()
    schedule_roots = [os.path.join(cohort_root, "unused-native-schedule")]
    for key in ("h01", "h02", "mc30", "mc36"):
        schedule_roots.append(os.path.join(freeze["configurations"]["probe_rows"][key]["cohort"], "unused-native-schedule"))
    for name in ("s7-001-mc29-configuration", "s7-001-mc29-job-input"):
        schedule_roots.append(os.path.join(E, name, "run", "unused-native-schedule"))
    goal_hits = []
    for parent, directories, names in os.walk(E):
        directories[:] = [d for d in directories if not d.startswith("s7-001-export-")]
        for name in names:
            if name.endswith((".json", ".jsonl", ".txt")) and os.path.getsize(os.path.join(parent, name)) < 50 * 1024 * 1024:
                text = open(os.path.join(parent, name), "rb").read().decode("utf-8", "replace")
                if "100000" in text or "100,000" in text or "operations" in text:
                    goal_hits.append(os.path.relpath(os.path.join(parent, name), E))
    report["limits"] = {
        "manifest_limits": manifest["limits"],
        "check_case_clock": "Clock(total_ms=30000)" in test_source and "stage_end=clock.started + 28" in test_source,
        "probe_limits_constant": re.search(r"const LIMITS = \{([^}]*)\}", probe_source).group(1),
        "supervisor_limits": re.search(r"LIMITS = \{(.*?)\}", supervisor_source, re.S).group(1),
        "supervisor_entry_cap_2048": "count > 2048" in supervisor_source,
        "cohort_sizes": sizes, "direct_rows": rows_limits,
        "unused_native_schedule": {p: os.path.lexists(p) for p in schedule_roots},
        "goal_ceiling_mentions_in_records": goal_hits,
        "probe_job_bound": "fileBytes(jobPath, 32768)" in probe_source, "probe_manifest_bound": "1024 * 1024" in probe_source,
    }

    # ---- Item 12: labels of contract section 10 in the results -----------------------------------------
    labels = {}
    for case in ("Q01-positive", "Q03-positive", "Q01-changed-reference"):
        labels["probe " + case] = load(os.path.join(cohort_root, case, "probe.json")).get("labels")
        labels["ledger " + case] = load(os.path.join(cohort_root, "provider-ledgers", case, "result.json"))["labels"]
    labels["setup"] = setup["labels"]
    labels["cohort"] = load(os.path.join(cohort_root, "cohort.json"))["labels"]
    expected_labels = {"executor": "macos-arm64-local", "contract": "ontokin.current-host-readback/0.2.0", "design_revision": 4,
                       "amendments": ["P33-AMENDMENT-001"], "profile": "darwin-arm64-v1", "os": host["labels"]["os"],
                       "node": host["labels"]["node"], "python_inventory_sha256": host["python"]["inventory_sha256"],
                       "git": {"path": host["git"]["path"], "sha256": host["git"]["sha256"]}, "run_kind": "qualifying", "boundary": "real"}
    report["labels"] = {"expected": expected_labels,
                        "equal": {name: value == expected_labels for name, value in labels.items()},
                        "refused_results": {name: load(os.path.join(freeze["configurations"]["probe_rows"][key]["stage"], "probe.json")).get("labels")
                                            == expected_labels for name, key in (("MC30-probe", "mc30"), ("MC36", "mc36"))}}
    data = json.dumps(report, indent=1, sort_keys=True).encode()
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    print("n04", json.dumps(report["n04"], indent=None)[:6000])
    for name, value in controls.items():
        print("control", name, json.dumps(value)[:3500])
    print("limits", json.dumps(report["limits"])[:5000])
    print("labels", json.dumps({k: v for k, v in report["labels"].items() if k != "expected"}))


main()
