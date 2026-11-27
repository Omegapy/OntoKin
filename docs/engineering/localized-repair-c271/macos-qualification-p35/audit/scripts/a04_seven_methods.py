"""W4 audit 001, a04: item 4, the seven methods of C17 against P07 section 6's table.

Usage: a04_seven_methods.py FREEZE OUTPUT
  - raw test IDs and outcomes (outcomes.json, journal.jsonl, unittest's own stderr lines), joined to the
    discovery document's IDs only through the declared prefix alias;
  - source, class, method and body identity, with this auditor's own AST digests (the ORIGINAL_BODIES
    definition: SHA-256 of ast.dump(ast.Module(body=node.body, type_ignores=[]), include_attributes=False));
  - the three CPU starts (one per case), attributed to the tests by the journal's time windows, and the
    four coordinator seams (mocked, no process event in their windows);
  - the imported reader versions, the raw stdout/stderr counts, the preserved input bytes;
  - the scientific predicates that the retained values allow, recomputed from probe.json and the reference.
Starts nothing (an audit hook refuses process creation).
"""
import ast
import hashlib
import json
import math
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


P07_TABLE = [
    "ReadbackCPUControls.test_q01_actual_synthetic_meshes_load_in_both_libraries",
    "ReadbackCPUControls.test_q03_actual_synthetic_rotations_load_in_both_libraries",
    "ReadbackCPUControls.test_three_rejects_changed_synthetic_reference",
    "ReadbackCoordinatorSeams.test_result_write_failure_leaves_predecessor_gate_blocked",
    "ReadbackCoordinatorSeams.test_host_alarm_cannot_interrupt_supervisor_cleanup",
    "ReadbackCoordinatorSeams.test_success_finalization_uses_remaining_outer_alarm",
    "ReadbackCoordinatorSeams.test_uncertain_marker_removal_recreates_pending",
]
DEFAULT_PREFIX = "test_static_tray_readback_v01."
PACKAGE_PREFIX = "tests.test_static_tray_readback_v01."
CASES = {"Q01-positive": P07_TABLE[0], "Q03-positive": P07_TABLE[1], "Q01-changed-reference": P07_TABLE[2]}


def finite_tree(value):
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return True
    if isinstance(value, (int, float)):
        return math.isfinite(value)
    if isinstance(value, list):
        return all(finite_tree(v) for v in value)
    if isinstance(value, dict):
        return all(finite_tree(v) for v in value.values())
    return True


def main():
    freeze = json.load(open(sys.argv[1]))
    output = sys.argv[2]
    evidence = freeze["evidence"]["parent"]
    wt = freeze["places"]["worktree"]
    cohort_root = freeze["audit_inputs"]["cohort_root"]
    node_path = [b["path"] for b in freeze["bindings"] if b["id"] == "mp:node"][0]
    git_path = [b["path"] for b in freeze["bindings"] if b["id"] == "git"][0]
    outcomes = json.load(open(os.path.join(evidence, "s7-001-cohort-outcomes/outcomes.json")))
    journal = [json.loads(line) for line in open(os.path.join(evidence, "s7-001-cohort-outcomes/journal.jsonl")) if line.strip()]
    stderr_text = open(os.path.join(evidence, "s7-001-c17-cohort.stderr.txt"), encoding="utf-8").read()
    stdout_size = os.path.getsize(os.path.join(evidence, "s7-001-c17-cohort.stdout.txt"))
    discovery = json.load(open(freeze["configurations"]["discovery"]["path"]))
    methods_doc = json.load(open(freeze["configurations"]["methods"]["path"]))
    report = {"schema": "w4-audit-001.a04-seven-methods/1"}

    # Raw IDs and outcomes.
    unittest_lines = re.findall(r"^(\w+) \(([\w.]+)\) \.\.\. (\w+)$", stderr_text, re.M)
    raw = [{"raw_id": t["raw_id"], "outcome": t["outcome"], "alias_id": t.get("alias_id")} for t in outcomes["tests"]]
    joined = {}
    for row in raw:
        rid = row["raw_id"]
        if rid.startswith(PACKAGE_PREFIX):
            joined[DEFAULT_PREFIX + rid[len(PACKAGE_PREFIX):]] = row["outcome"]
    report["ids"] = {
        "raw": raw,
        "unittest_stderr_lines": unittest_lines,
        "stderr_ids_equal_raw_ids": sorted(l[1] for l in unittest_lines) == sorted(r["raw_id"] for r in raw),
        "stderr_outcomes": sorted({l[2] for l in unittest_lines}),
        "joined_equal_discovery_ids": sorted(joined) == sorted(discovery["method_ids"]),
        "joined_equal_p07_table": sorted(joined) == sorted(DEFAULT_PREFIX + n for n in P07_TABLE),
        "joined_outcomes": joined,
        "alias_ids_recorded": [r["alias_id"] for r in raw],
        "required_methods": outcomes["required_methods"],
        "ran_summary": re.findall(r"^Ran (\d+) tests? in ([0-9.]+)s$", stderr_text, re.M),
        "final_line_ok": "\nOK\n" in stderr_text,
        "class_level_events": outcomes["class_level_events"], "unplanned_events": outcomes["unplanned_events"],
        "loader_errors": outcomes["loader_errors"], "bytecode_present": outcomes["bytecode_present"],
        "state": outcomes["state"], "outcome_counts": outcomes["outcome_counts"], "interrupted": outcomes["interrupted"],
        "c17_stdout_bytes": stdout_size, "c17_stderr_bytes": len(stderr_text.encode()),
    }

    # Source, class, method and body identity, with this auditor's own AST code.
    source_path = os.path.join(wt, methods_doc["source_test"])
    raw_source = open(source_path, "rb").read()
    tree = ast.parse(raw_source)
    bodies, defs = {}, {}
    for group in tree.body:
        if isinstance(group, ast.ClassDef):
            for node in group.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    name = group.name + "." + node.name
                    bodies[name] = hashlib.sha256(ast.dump(ast.Module(body=node.body, type_ignores=[]),
                                                           include_attributes=False).encode()).hexdigest()
                    defs[name] = {"line": node.lineno, "decorators": len(node.decorator_list)}
    frozen = methods_doc["original_bodies"]
    report["bodies"] = {
        "source_sha256": hashlib.sha256(raw_source).hexdigest(),
        "frozen_module_sha256": [b["sha256"] for b in freeze["bindings"] if b["id"] == "source:tests/test_static_tray_readback_v01.py"][0],
        "computed": {name: bodies.get(name) for name in frozen},
        "all_equal_frozen": all(bodies.get(name) == digest for name, digest in frozen.items()),
        "collector_record_equal": all(outcomes["original_bodies"][n]["source"] == bodies.get(n)
                                      and outcomes["original_bodies"][n]["frozen"] == frozen[n]
                                      and outcomes["original_bodies"][n]["equal"] is True for n in frozen),
        "defs": {name: defs.get(name) for name in frozen},
        "p07_methods_present_without_decorators": all(defs.get(n, {}).get("decorators") == 0 for n in P07_TABLE),
        "module_unchanged": outcomes["module_unchanged"], "module_sha256_before_after":
            (outcomes["module"]["sha256"], outcomes["module_after"]["sha256"]),
    }

    # Time windows of each test from the journal; attribution of the process events.
    windows = {}
    for event in journal:
        if event.get("kind") in ("start", "stop") and event.get("test"):
            windows.setdefault(event["test"], {})[event["kind"]] = event["monotonic"]
    run_start = [e["monotonic"] for e in journal if e.get("kind") == "start_run"]
    run_stop = [e["monotonic"] for e in journal if e.get("kind") == "stop_run"]
    attribution = []
    for event in outcomes["process_events"]:
        where = "outside any test (class setup or teardown)"
        for test, window in windows.items():
            if window.get("start", 1e99) <= event["monotonic"] <= window.get("stop", -1):
                where = test
        attribution.append({"sequence": event["sequence"], "argv0": event["argv"][0], "where": where,
                            "job": event["argv"][-1] if event["argv"][0] == node_path else None,
                            "git_subcommand": [a for a in event["argv"][1:] if not a.startswith("-")][:2]
                            if event["argv"][0] == git_path else None})
    per_test = {}
    for row in attribution:
        key = row["where"]
        per_test.setdefault(key, {"node": 0, "git": 0, "other": 0})
        per_test[key]["node" if row["argv0"] == node_path else "git" if row["argv0"] == git_path else "other"] += 1
    node_events = [r for r in attribution if r["argv0"] == node_path]
    report["starts"] = {
        "process_events": len(outcomes["process_events"]),
        "by_where": per_test,
        "node_events": node_events,
        "each_cpu_case_once": sorted(os.path.basename(os.path.dirname(r["job"])) for r in node_events)
                              == sorted(CASES),
        "node_event_in_its_own_test": all(PACKAGE_PREFIX + CASES[os.path.basename(os.path.dirname(r["job"]))] == r["where"]
                                          for r in node_events),
        "coordinator_tests_without_events": all(per_test.get(PACKAGE_PREFIX + n, {"node": 0, "git": 0, "other": 0})
                                                == {"node": 0, "git": 0, "other": 0}
                                                for n in P07_TABLE[3:]),
        "windows": windows, "run_window": [run_start, run_stop],
        "git_subcommands": sorted({" ".join(r["git_subcommand"]) for r in attribution if r["git_subcommand"]}),
    }
    # The coordinator seams' mocked boundary, in the source.
    seam_source = raw_source.decode()
    report["coordinator_mocked"] = {
        "class_docstring": ast.get_docstring([g for g in tree.body if isinstance(g, ast.ClassDef)
                                              and g.name == "ReadbackCoordinatorSeams"][0]),
        "run_process_patched": 'patch.object(format_check, "run_process", side_effect=child)' in seam_source,
        "mock_pid_123456": "123456" in seam_source,
    }

    # Per case: ledgers, receipts, logs, versions, preserved inputs, retained-value predicates.
    fixtures = freeze["configurations"]["fixtures"]
    fixture_for = {"Q01-positive": ("Q01/synthetic.glb", "Q01/synthetic-audit.json"),
                   "Q03-positive": ("Q03/synthetic.glb", "Q03/synthetic-audit.json"),
                   "Q01-changed-reference": ("Q01/synthetic.glb", "Q01-changed-reference/synthetic-audit.json")}
    three_pkg = json.load(open(os.path.join(freeze["configurations"]["approved_cohort"] and
                                            json.load(open(freeze["configurations"]["approved_cohort"]["path"]))["dependencies"]["root"],
                                            "indexer-view/three/package.json")))
    validator_pkg = json.load(open(os.path.join(json.load(open(freeze["configurations"]["approved_cohort"]["path"]))["dependencies"]["root"],
                                                "validator/package/package.json")))
    cases = {}
    for case in CASES:
        stage = os.path.join(cohort_root, case)
        ledger_dir = os.path.join(cohort_root, "provider-ledgers", case)
        result = json.load(open(os.path.join(ledger_dir, "result.json")))
        started = json.load(open(os.path.join(ledger_dir, "started.json")))
        receipt = json.load(open(os.path.join(stage, "synthetic-readback.process.json")))
        probe = json.load(open(os.path.join(stage, "probe.json")))
        reference = json.load(open(os.path.join(stage, "synthetic-audit.json")))
        job = json.load(open(os.path.join(stage, "job.json")))
        stdout_log = open(os.path.join(stage, "synthetic-readback.stdout.log"), "rb").read()
        stderr_log = open(os.path.join(stage, "synthetic-readback.stderr.log"), "rb").read()
        started_process = started.get("process", started)
        glb_sha, audit_sha = sha(os.path.join(stage, "synthetic.glb")), sha(os.path.join(stage, "synthetic-audit.json"))
        info = {
            "ledger_state": result["state"], "expected_checker_starts": result["expected_checker_starts"],
            "actual_checker_starts": result["actual_checker_starts"], "provider_failure": result["provider_failure"],
            "pid": result["process"]["pid"], "pid_same_everywhere": result["process"]["pid"] == started_process.get("pid")
            == receipt["pid"], "group_equals_pid": receipt["process_group"] == receipt["pid"],
            "receipt_equals_ledger_process": receipt == result["process"],
            "returncode": receipt["returncode"], "error": receipt["error"], "cleanup": receipt["cleanup"],
            "handles_closed": receipt["handles_closed"], "receipt_environment": receipt["environment"],
            "labels": result["labels"], "boot_before": result["boot_before"]["boot_session_uuid"],
            "boot_after": result["boot_after"]["boot_session_uuid"], "elapsed_ms": result["elapsed_ms"],
            "stdout_bytes": len(stdout_log), "stderr_bytes": len(stderr_log),
            "log_bytes_receipt": (receipt["observed_log_bytes"], receipt["retained_log_bytes"]),
            "log_bytes_match": receipt["observed_log_bytes"] == receipt["retained_log_bytes"] == len(stdout_log) + len(stderr_log),
            "stdout_line": json.loads(stdout_log.decode()) if stdout_log.strip() else None,
            "stderr_only_experimental_warning": stderr_log.decode().startswith("(node:") and "ExperimentalWarning" in stderr_log.decode()
            and "Error" not in stderr_log.decode(),
            "stderr_text": stderr_log.decode(),
            "artifacts_after_match_now": all(sha(os.path.join(stage, n)) == b["sha256"] for n, b in result["artifacts_after"].items()),
            "glb_sha256": glb_sha, "audit_sha256": audit_sha,
            "job_digests_match": job["artifact_sha256"] == glb_sha and job["audit_sha256"] == audit_sha,
            "fixture_glb_equal": glb_sha == fixtures[fixture_for[case][0]]["sha256"],
            "fixture_audit_equal": audit_sha == fixtures[fixture_for[case][1]]["sha256"],
            "input_preserved": probe.get("input_preserved"),
            "report_artifact_and_audit": (probe.get("artifact_sha256") == glb_sha, probe.get("audit_sha256") == audit_sha),
            "passed": probe.get("passed"), "error_member": "error" in probe,
            "versions": {"node": probe.get("node"), "khronos": probe["khronos"]["version"],
                         "validator_report": probe["khronos"]["report"]["validatorVersion"],
                         "three": probe["three"]["version"], "three_revision": probe["three"]["revision"],
                         "validator_package": validator_pkg["version"], "three_package": three_pkg["version"]},
            "labels_report": probe.get("labels"),
        }
        issues = probe["khronos"]["report"]["issues"]
        vinfo = probe["khronos"]["report"]["info"]
        info["validator"] = {"passed": probe["khronos"]["passed"], "numErrors": issues["numErrors"],
                             "numWarnings": issues["numWarnings"], "numInfos": issues["numInfos"],
                             "numHints": issues["numHints"], "truncated": issues["truncated"],
                             "messages": len(issues["messages"]), "resources": vinfo.get("resources"),
                             "animationCount": vinfo.get("animationCount"), "hasTextures": vinfo.get("hasTextures"),
                             "drawCallCount": vinfo.get("drawCallCount"), "totalVertexCount": vinfo.get("totalVertexCount"),
                             "totalTriangleCount": vinfo.get("totalTriangleCount")}
        three = probe["three"]
        nodes = three["nodes"]
        ref_nodes = reference["nodes"]
        exact = []
        mesh_ids = [i for i in sorted(ref_nodes) if ref_nodes[i].get("world_vertices") is not None]
        for nid in sorted(ref_nodes):
            n, r = nodes.get(nid), ref_nodes[nid]
            if n is None:
                exact.append((nid, "missing"))
                continue
            expected_parent = None if r["extras"]["role"] == "tray-root" else "/".join(r["extras"]["owner_id"])
            if n["original_name"] != nid:
                exact.append((nid, "original_name"))
            if n["extras"] != r["extras"]:
                exact.append((nid, "extras"))
            if n["children"] != sorted(r["children"]):
                exact.append((nid, "children"))
            if n["parent"] != expected_parent:
                exact.append((nid, "parent"))
            if nid in mesh_ids:
                if len(n["positions"]) != len(r["world_vertices"]) or len(n["normals"]) != len(r["world_vertices"]):
                    exact.append((nid, "vertex_count"))
                if n["indices"] != r["indices"]:
                    exact.append((nid, "indices"))
                if n["material"] != r["material"]:
                    exact.append((nid, "material"))
                bounds = [[min(v[a] for v in n["world_vertices"]) for a in range(3)],
                          [max(v[a] for v in n["world_vertices"]) for a in range(3)]]
                if bounds != n["world_bounds"]:
                    exact.append((nid, "world_bounds_not_min_max_of_world_vertices"))
            elif "positions" in n:
                exact.append((nid, "root has geometry"))
        info["retained_predicates"] = {
            "node_count": three["node_count"], "mesh_count": three["mesh_count"], "animations": three["animations"],
            "retained_nodes": len(nodes), "reference_nodes": len(ref_nodes), "mesh_nodes_in_reference": len(mesh_ids),
            "identity_inventory_equal": sorted(nodes) == sorted(ref_nodes),
            "exact_mismatches": exact,
            "all_retained_finite": finite_tree(nodes),
            "all_measurement_values_finite": all(math.isfinite(m["actual"]) and math.isfinite(m["expected"])
                                                 for m in three["measurements"]),
            "vertices_per_mesh": sorted({len(nodes[i]["positions"]) for i in mesh_ids}),
            "indices_per_mesh": sorted({len(nodes[i]["indices"]) for i in mesh_ids}),
            "tolerances": (three["position_tolerance_m"], three["matrix_tolerance"]),
            "findings": three["findings"], "three_passed": three["passed"],
        }
        cases[case] = info
    report["cases"] = cases
    setup = json.load(open(os.path.join(cohort_root, "setup.json")))
    cohort = json.load(open(os.path.join(cohort_root, "cohort.json")))
    report["setup"] = {"passed": setup["passed"], "run_kind": setup["run_kind"], "checker_starts": setup["checker_starts"],
                       "boot": setup["boot"]["boot_session_uuid"], "labels": setup["labels"],
                       "config_sha256": setup.get("config_sha256"), "manifest_sha256": setup.get("manifest_sha256")}
    report["cohort"] = {"passed": cohort["passed"], "actual_checker_starts": cohort.get("actual_checker_starts"),
                        "expected_cases": cohort["expected_cases"], "labels": cohort["labels"],
                        "attempts": cohort.get("attempts")}
    report["cohort_root_entries"] = sorted(os.listdir(cohort_root))
    report["unused_native_schedule_present"] = os.path.lexists(os.path.join(cohort_root, "unused-native-schedule"))
    data = json.dumps(report, indent=1, sort_keys=True).encode()
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    print("ids", json.dumps({k: v for k, v in report["ids"].items() if k not in ("raw", "unittest_stderr_lines", "required_methods")}))
    print("raw", json.dumps(report["ids"]["raw"]))
    print("required", json.dumps(report["ids"]["required_methods"]))
    print("bodies", json.dumps({k: v for k, v in report["bodies"].items() if k != "computed"}))
    print("starts", json.dumps({k: v for k, v in report["starts"].items() if k not in ("windows",)}))
    print("coordinator", json.dumps(report["coordinator_mocked"]))
    for case, info in cases.items():
        print("case", case, json.dumps({k: v for k, v in info.items() if k not in ("labels", "labels_report", "stderr_text", "receipt_environment")}))
    print("setup", json.dumps(report["setup"]))
    print("cohort", json.dumps({k: v for k, v in report["cohort"].items() if k != "labels"}))
    print("cohort root", report["cohort_root_entries"], "unused schedule present", report["unused_native_schedule_present"])


main()
