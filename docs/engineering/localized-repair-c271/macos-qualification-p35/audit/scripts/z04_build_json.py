"""W4 audit 001, z04: assemble AUDIT-001.json from this audit's own outputs, with labelled paths.

Usage: z04_build_json.py OUT_DIR FREEZE
Reads outputs/a01..a11, x12, z01..z03 and the start listing; writes AUDIT-001.json by exclusive creation.
Starts nothing (an audit hook refuses process creation).
"""
import hashlib
import json
import os
import sys


def _refuse(event, args):
    if event in ("subprocess.Popen", "os.posix_spawn", "os.exec", "os.fork", "os.forkpty", "os.spawn",
                 "os.system", "os.startfile"):
        raise PermissionError("this audit script starts no process: " + event)


sys.addaudithook(_refuse)


def main():
    out, freeze_path = sys.argv[1], sys.argv[2]
    freeze = json.load(open(freeze_path))
    o = lambda name: json.load(open(os.path.join(out, "outputs", name)))
    wt, local = freeze["places"]["worktree"], freeze["places"]["local"]
    home = os.path.dirname(freeze["host_facts"][0]["path"])
    git_path = [b["path"] for b in freeze["bindings"] if b["id"] == "git"][0]
    host = json.load(open(freeze["host"]["HOST"]["path"]))
    prefix_root = host["python"]["framework"].split("/Cellar/")[0] if "/Cellar/" in host["python"]["framework"] else None

    def label(text):
        if not isinstance(text, str):
            return text
        if prefix_root and text.startswith(prefix_root):
            return "<prefix>/..."
        text = text.replace(git_path, "<bound-git>")
        text = text.replace(wt, "<worktree>").replace(local, "<local>").replace(home, "<home>")
        common = os.path.dirname(os.path.dirname(wt))
        return text

    def clean(value):
        if isinstance(value, dict):
            return {label(k): clean(v) for k, v in value.items()}
        if isinstance(value, list):
            return [clean(v) for v in value]
        return label(value)

    a01, a02, a03, a04, a05 = o("a01-bindings.json"), o("a02-starts.json"), o("a03-direct-probe.json"), o("a04-seven-methods.json"), o("a05-numeric.json")
    a06, a07, a09, a10, a11 = o("a06-controls.json"), o("a07-fck1.json"), o("a09-git-static.json"), o("a10-records.json"), o("a11-checker-summary.json")
    x12 = o("x12-audit-numeric-crosscheck.json")
    c18 = json.load(open(os.path.join(freeze["evidence"]["parent"], "s7-001-audit-numeric.json")))
    z01 = json.load(open(os.path.join(out, "outputs", "z01-python-inventory.stdout.txt")))
    z02, z03 = o("z02-listing-comparison.json"), o("z03-process-check-2.json")
    crosscheck_equal = all([(r["semantic_id"], r["field"], r["actual"], r["expected"], r["difference"], r["threshold"], r["passed"])
                            for r in x12["cases"][c]["rows"]] == [(r["semantic_id"], r["field"], r["actual"], r["expected"], r["difference"],
                                                                    r["threshold"], r["passed"]) for r in c18["cases"][c]["rows"]]
                           for c in ("Q01-positive", "Q03-positive", "Q01-changed-reference"))

    node_chains = {}
    for chain in a01["node_start_inputs"]:
        entry = {k: chain.get(k) for k in ("node_sha256", "probe_sha256", "loader_sha256", "expected_config_sha256", "job_sha256",
                                            "manifest_sha256", "job_manifest_sha256", "configuration_sha256",
                                            "argv_digest_equals_manifest_selection", "manifest_selection_equals_configuration_bytes",
                                            "manifest_host_sha256_now", "artifact_sha256", "job_artifact_sha256", "audit_sha256",
                                            "job_audit_sha256", "ledger_job_binding_sha256", "ledger_manifest_sha256",
                                            "ledger_config_sha256", "ledger_postflight_equal_preflight", "flags") if k in chain}
        node_chains[chain["label"]] = entry

    files = []
    listing = o("a00-listing-start.json")
    for root, info in listing["roots"].items():
        if not info.get("exists"):
            continue
        for entry in info["entries"]:
            if entry.get("kind") != "file":
                continue
            rel = entry["path"]
            if root.endswith("/evidence") and rel.startswith(("s7-001-export-1c2f25ba/", "s7-001-export-0eb9a551/")):
                continue
            if root.endswith("W3-freeze-002") and not rel.startswith("FREEZE-REVIEW-002"):
                continue
            files.append({"path": label(os.path.join(root, rel)), "sha256": entry["sha256"], "size_bytes": entry["size"]})
    for row in a01["bindings"]["rows"]:
        if row["path"].startswith(wt) or row["path"] == git_path:
            files.append({"path": label(row["path"]), "sha256": row["observed"]["sha256"], "size_bytes": row["observed"]["size_bytes"]})
    for rel in ("docs/engineering/localized-repair-c271/host-inspection-p07/QUALIFICATION-PLAN.md",
                "docs/engineering/localized-repair-c271/macos-qualification-p35/MH-PLAN.md",
                "docs/engineering/localized-repair-c271/macos-implementation-p33/interfaces/W5-PROVIDER.md",
                "docs/engineering/localized-repair-c271/macos-implementation-p33/interfaces/W4-DRIVER.md",
                "GOAL.md", "ontokin/construction.py"):
        path = os.path.join(wt, rel)
        files.append({"path": label(path), "sha256": hashlib.sha256(open(path, "rb").read()).hexdigest(),
                      "size_bytes": os.path.getsize(path)})
    for path in (os.path.join(local, "c271-p35/workers/WORKERS.md"),):
        files.append({"path": label(path), "sha256": hashlib.sha256(open(path, "rb").read()).hexdigest(),
                      "size_bytes": os.path.getsize(path), "note": "read at the start of the audit; the Director's log grows"})
    seen, unique_files = set(), []
    for f in files:
        if f["path"] not in seen:
            seen.add(f["path"])
            unique_files.append(f)

    doc = {
        "schema": "ontokin.c271.p35-audit/1",
        "id": "AUDIT-001",
        "task": "C271", "phase": "C271-P35-macos-host-qualification-mh", "gate": "MH", "stage": "S8", "acceptance": "A8",
        "auditor": "W4, a Claude Code subagent in a fresh context with the session's model (Claude Opus 5.5); it wrote none of the freezes, the tooling, the observer, the provider, the probe, the contract, MP's preparation or any review, and took no part in any earlier stage",
        "written_at_utc": "2026-11-27",
        "subject": {"freeze": {"path": label(freeze_path), "sha256": a01["freeze"]["observed"], "size_bytes": a01["freeze"]["size_bytes"]},
                    "commit": freeze["fixed_state"]["commit"], "tree": freeze["fixed_state"]["tree"],
                    "boot_session_uuid": freeze["boot_session_uuid"], "cohort_configuration_sha256": a01["cohort_configuration"]["sha256"],
                    "host_sha256": freeze["host"]["HOST"]["sha256"], "s7_window_utc": [a10["records"]["first_start_utc"], a10["records"]["last_end_utc"]]},
        "verdict": "PASS_WITH_NONBLOCKING_FINDINGS",
        "blocking_findings": [],
        "findings": [
            {"id": "AU-01", "blocking": False, "item": 13, "subject": "C01 launch message",
             "text": "C01's launch message held a third call, a foreground log append before the launch pair, against FR2-03 (a)'s two calls. The append ended before C01's call began; C01 ran once (exit 0, retries 0, wall 2.0 s), its timer was the pair's second call, and every later launch held two calls. No effect on the bound, the order or any record; the outcome should keep it as a recorded launch deviation."},
            {"id": "AU-02", "blocking": False, "item": 2, "subject": "MC37's start has no PID receipt",
             "text": "C15's other start is one subprocess.Popen audit event of the bound interpreter (-I -S -B -c ...). No record keeps its PID, so FC-P3 could not probe it (failure_capture.no_pair). The start and its cleanup rest on the passing test's own evidence: killpg answered EPERM while the child was unreaped and ESRCH after Popen.wait reaped it. The count is exact only for the audited route (FC-P7); the outcome should say so rather than cite a receipt."},
            {"id": "AU-03", "blocking": False, "item": 2, "subject": "simulated receipts with positive PIDs",
             "text": "The MC10 harness (C03 to C05) wrote supervisor-shaped receipts with PIDs 999990001 and 999990002. They are above Darwin's PID_MAX (99999), the records are labelled mocked, no audit event exists and every zero_process_starts check holds, so they are simulated, not starts. A literal reading of P07 section 4 over every S7 record would count them; the outcome and its portable copies should name them as simulated."},
            {"id": "AU-04", "blocking": False, "item": 11, "subject": "timer lines not on disk",
             "text": "The bound timer writes nothing by design, so no file holds its 72 lines; the Director's log states 'every timer: exit-file' as a summary. The audit decided the bound from the records instead (FR2-03 (b)): the 72 commands ran strictly in the frozen order without overlap, and the largest wall time, 7.98 s (C17), is far below every outer bound (120 to 600 s). If S9 cites the timer lines, it should keep them from the session transcript."},
            {"id": "AU-05", "blocking": False, "item": 2, "subject": "unaudited routes",
             "text": "'No other program started' holds for the routes the audit hooks see. The provider's 100 bound Git reads (C06 15, C07 25, C17 60) have audit events but no receipts or probes, and their own children are not observed; the non-Python commands (P00 shasum, P05 and Q03 git status, C08 and C10 git archive, C09 and C11 tar, D01 sh with mkdir and cp) run without any hook. This is the frozen design (recorded, not bounded; FC-P7). For C08 to C11 the audit confirmed independently that each extracted tree equals its commit's tree."},
            {"id": "AU-06", "blocking": False, "item": 4, "subject": "the quartet's mocked label lives outside the cohort records",
             "text": "outcomes.json records the four coordinator seams as pass with no label; 'mocked' comes from the freeze's controls table (MC26) and from the test source (format_check.run_process patched, class docstring 'Mocked child seams'). P07 section 6 requires the four results to stay labelled mocks, so the MH outcome must carry the label explicitly."},
            {"id": "AU-07", "blocking": False, "item": 4, "subject": "loader deprecation warning on stderr",
             "text": "Every Node start that uses the module loader writes Node's 417-byte ExperimentalWarning that --experimental-loader may be removed (stderr of C17's three cases, MC30-probe and MC36, and inside H01's and H02's refusal text). It is not an error and no frozen predicate depends on it; the contract's argv keeps --experimental-loader, which a later Node release may drop. A note for MR and R04, not for MH."},
            {"id": "AU-08", "blocking": False, "item": 1, "subject": "one HOST descriptor is relative",
             "text": "HOST's runtime.node_source.content.extracted is the only descriptor whose path is relative ('bin/node', relative to the runtime directory, copied from NODE-SOURCE.json); a generic recomputation of every descriptor reads it as absent. Its digest equals the bound Node. Documentation only."},
        ],
        "starts": {
            "rule": "P07 section 4: an audit event shows an attempt; a receipt with a positive PID establishes a start",
            "mh": {"node": 9, "other": 2,
                   "rows": [{"row": "M0 Git --version", "where": "S5", "pid": 7994, "kind": "other"},
                            {"row": "M1 Node --version", "where": "S5", "pid": 7995, "kind": "node"},
                            {"row": "probe syntax check", "where": "C16 R1", "pid": 33371, "kind": "node"},
                            {"row": "P06-H01", "where": "C16 R1", "pid": 33379, "kind": "node"},
                            {"row": "P06-H02", "where": "C16 R1", "pid": 33380, "kind": "node"},
                            {"row": "Q01-positive", "where": "C17", "pid": 33806, "kind": "node"},
                            {"row": "Q03-positive", "where": "C17", "pid": 33835, "kind": "node"},
                            {"row": "Q01-changed-reference", "where": "C17", "pid": 33862, "kind": "node"},
                            {"row": "MC30-probe", "where": "C19 R2", "pid": 34541, "kind": "node"},
                            {"row": "MC36", "where": "C19 R2", "pid": 34550, "kind": "node"},
                            {"row": "MC37's Python child", "where": "C15", "pid": None, "kind": "other",
                             "basis": "one audit event and the test's own EPERM/ESRCH evidence (AU-02)"}]},
            "s7_bounded": {"node": 8, "other": 1},
            "s7_audit_events": {"C06": 15, "C07": 25, "C15": 1, "C16": 3, "C17": 63, "C19": 2, "total": 109,
                                "by_program": {"bound Node": 8, "bound Git (provider reads)": 100, "bound interpreter (MC37 child)": 1}},
            "receipts_with_positive_pid": {"node_s7": 8, "node_s5": 1, "git_s5": 1, "simulated_mc10": [999990001, 999990002]},
            "cleanup": {"all_receipts_passed_group_absent_reaped_handles_closed": all(r["cleanup_ok"] for r in a02["distinct_started_pids"]),
                        "fc_p3_all_absent_esrch": {k: v["all_absent"] for k, v in a02["probes"].items()}},
            "unknown_or_interrupted": {"runner_rows_all_OBSERVED_ONE_not_interrupted": True,
                                       "collectors_complete_journals": True, "intent_records_UNKNOWN_before_start_only": True},
            "recorded_not_bounded": {"python_launchers": 64, "python_launchers_self_recorded_pids": 37, "director_git_reads": 4,
                                     "tar": 2, "shasum": 1, "prepare_script": 1, "provider_git_reads": 100},
            "forbidden_by_record": {"ldd": 0, "codesign": 0, "otool": 0, "observe": 0, "node_outside_C16_C17_C19": 0},
        },
        "numerical": {case: {"rows": a05["summary"][case]["rows"], "unique": a05["summary"][case]["unique"],
                             "same_inventory_and_order_as_report": a05["summary"][case]["same_as_report"],
                             "value_mismatches_with_report": a05["summary"][case]["value_mismatches"],
                             "failed_rows": a05["summary"][case]["failed_rows"], "findings": a05["summary"][case]["findings"],
                             "glb_positions_normals_indices_equal_importer": a05["summary"][case]["glb_positions_normals_indices_exact"],
                             "c18_rows_equal": a05["c18"]["cases"][case]["c18_rows_equal_mine"]}
                      for case in ("Q01-positive", "Q03-positive", "Q01-changed-reference")},
        "numerical_negative_row": a05["negative_row"],
        "numerical_negative_difference_minus_0_001": a05["negative_difference_minus_0_001"],
        "numerical_row_kinds_per_case": a05["cases"]["Q01-positive"]["rows"]["by_kind"],
        "numerical_crosscheck_tool_run": {"passed": x12["passed"], "rows_equal_c18": crosscheck_equal},
        "controls": [
            {"id": "MC10", "label": "mocked (command boundary), real static bindings", "commands": ["C03", "C04", "C05"], "outcome": "met",
             "evidence": "v24.22.0\\n and v24.22.1 without newline refused CHO-OUTPUT with no HOST or completion; v24.22.1\\n accepted, HOST labelled mocked, runtime v24.22.1, OBSERVED_UNAPPROVED; zero audit events"},
            {"id": "MC11", "label": "real (static scan; a name scan cannot exclude every dynamic route)", "commands": ["C01"], "outcome": "met",
             "evidence": "frozen rule passed (587 dynamic hits reviewed, 0 unreviewed), wider scan process creation 0, reviewed list aade03ac... matches, 0 unresolved specifiers; totals 628/23/53; 25 files"},
            {"id": "MC24", "label": "real", "commands": ["C17", "C18"], "outcome": "met", "evidence": "Q01 and Q03 positive: exit 0, probe passed, 2,060 rows each all pass, input preserved"},
            {"id": "MC25", "label": "real", "commands": ["C17", "C18"], "outcome": "met",
             "evidence": "Q01 changed reference: exit 1, no error member, exactly one failed row and one finding at equipment-tray/pair/left/base matrix_0_3 (difference 0.0010000000000000009, threshold 5e-6)"},
            {"id": "MC26", "label": "mocked (the original seams)", "commands": ["C17"], "outcome": "met", "evidence": "four seams pass; no process event in their windows (AU-06)"},
            {"id": "MC27", "label": "real", "commands": ["C16"], "outcome": "met",
             "evidence": "P06-H01 and P06-H02: one Node start each, exit 1, exact refusal selectors on stderr, no probe.json, refusal in approvedEnvelope before the try block (source-backed inference)"},
            {"id": "probe-syntax-check", "label": "real", "commands": ["C16"], "outcome": "met", "evidence": "exit 0, empty stdout and stderr"},
            {"id": "MC28", "label": "real", "commands": ["C08", "C09", "C10", "C11", "C12", "C13", "C14"], "outcome": "met",
             "evidence": "baseline 5,587 (382 modules), current 5,994 (388 modules) = baseline + exactly the 407 additions, recomputed; exports equal their commits' trees"},
            {"id": "MC29", "label": "mocked (supervisor recorder) with the real detectors", "commands": ["C06", "C07"], "outcome": "met",
             "evidence": "configuration: attempt and accounting CH-SELECTION; job input: attempt CH-JOB, accounting CH-EVIDENCE; zero supervisor and on_started calls; Git reads 15 and 25"},
            {"id": "MC29 source/runtime/dependency/OS-build cases", "label": "NOT_RUN at MH (MI's simulated cases)", "commands": [], "outcome": "NOT_RUN"},
            {"id": "MC30", "label": "real (positive direction and MC30-probe; the value by elimination only)", "commands": ["C17", "C19"], "outcome": "met"},
            {"id": "MC30 case without the variable", "label": "mocked (MI)", "commands": [], "outcome": "NOT_RUN at MH"},
            {"id": "MC36", "label": "real, after MC30-probe", "commands": ["C19"], "outcome": "met",
             "evidence": "refused 'Current-host binding: actual Node environment differs' in probe.json, no khronos or three member"},
            {"id": "MC37", "label": "real", "commands": ["C15"], "outcome": "met", "evidence": "raw_unreaped EPERM, raw_reaped ESRCH; one other start (AU-02)"},
            {"id": "F-04", "label": "real", "commands": ["C02", "C17"], "outcome": "met",
             "evidence": "host-state equals HOST with nothing substituted and boundary real; setup and every ledger boot C90010BA with boundary real"},
            {"id": "MC09", "label": "real (positive direction only); change cases stay MI's (simulated)", "commands": ["C02", "C17"], "outcome": "met (positive direction)"},
            {"id": "MC18, MC19, MC32", "label": "NOT_RUN as controls (positive direction in every selection check and in P02 to P04 and Q01)", "commands": [], "outcome": "NOT_RUN"},
            {"id": "MC23", "label": "NOT_RUN (MR's)", "commands": [], "outcome": "NOT_RUN"},
            {"id": "MC01..MC05, MC06, MC07, MC08, MC12..MC17, MC20..MC22, MC31, MC33..MC35, MC38, MC39", "label": "NOT_RUN at MH", "commands": [], "outcome": "NOT_RUN"},
            {"id": "P07 section 6 numerical audit", "label": "real (zero starts)", "commands": ["C18"], "outcome": "met; recomputed by this audit"},
        ],
        "items": {
            "1_bindings": {"freeze_sha256_ok": a01["freeze"]["ok"], "bindings": a01["bindings"]["count"], "bindings_failed": len(a01["bindings"]["failed"]),
                           "host_fact_cf_ok": all(r["ok"] for r in a01["host_facts"]), "evidence_ancestors_ok": a01["evidence_ancestors"]["ok"],
                           "digest_lists": {k: {"lines": v["lines"], "failed": len(v["failed"])} for k, v in a01["digest_lists"].items()},
                           "digest_list_note": "P00's second list has two comment lines, counted above as failed by the line parser; its 44 digest lines all verify",
                           "freeze_directories": a01["freeze_directories"], "cohort_configuration": clean(a01["cohort_configuration"]),
                           "original_bodies_declarations": a01["original_bodies_declarations"],
                           "reader_tree": clean({k: v for k, v in a01["reader_tree"].items() if k != "archive"}),
                           "source_inventory": clean({k: v for k, v in a01["source_inventory"].items() if k not in ("source_trees",)}),
                           "python_inventory": {"sha256": a01["python_inventory"]["sha256"], "q01_equal": a01["python_inventory"]["q01_output_equal_bytes"],
                                                "framework": {k: a01["python_inventory"]["framework"][k] for k in ("entries", "mismatched_count", "extra_count")},
                                                "venv": {k: a01["python_inventory"]["venv"][k] for k in ("entries", "mismatched_count", "extra_count")},
                                                "closure_external_failed": len(a01["python_inventory"]["closure_external"]["failed"]),
                                                "observer_rerun_at_end": z01["output"]["sha256"]},
                           "node_start_inputs": clean(node_chains)},
            "3_direct_probe": clean({run: [{k: r[k] for k in ("row", "state", "start_count_state", "pid", "returncode", "error", "stdout_bytes",
                                                             "stderr_bytes", "stderr_has_h01", "stderr_has_h02", "probe_json_present",
                                                             "stack_frames", "receipt_file_equals_record", "event_argv_equals_receipt")}
                                          for r in v["results"]] for run, v in a03["rows"].items()}),
            "3_inference": clean({k: a03["inference"][k] for k in ("static_import_specifiers", "dynamic_imports", "require_calls", "anchors",
                                                                    "order_envelope_before_try_before_bootstrap_before_readers",
                                                                    "loader_static_imports", "loader_dynamic_imports_or_requires", "loader_exports")}),
            "3_mutations": clean(a03["mutations"]), "3_host_copies": a03["host_copies"],
            "4_seven_methods": clean({"ids": {k: a04["ids"][k] for k in ("stderr_ids_equal_raw_ids", "joined_equal_discovery_ids",
                                                                          "joined_equal_p07_table", "joined_outcomes", "ran_summary", "state")},
                                      "bodies": {k: a04["bodies"][k] for k in ("source_sha256", "all_equal_frozen", "collector_record_equal",
                                                                                "p07_methods_present_without_decorators", "module_unchanged")},
                                      "starts": {k: a04["starts"][k] for k in ("process_events", "by_where", "each_cpu_case_once",
                                                                                "node_event_in_its_own_test", "coordinator_tests_without_events")},
                                      "cases": {c: {k: v[k] for k in ("pid", "returncode", "ledger_state", "actual_checker_starts", "stdout_bytes",
                                                                       "stderr_bytes", "log_bytes_match", "versions", "validator", "input_preserved",
                                                                       "fixture_glb_equal", "fixture_audit_equal", "passed", "error_member",
                                                                       "retained_predicates")} for c, v in a04["cases"].items()}}),
            "6_n04": clean(a06["n04"]),
            "7_controls_records": clean(a06["controls"]),
            "8_limits": clean({k: v for k, v in a06["limits"].items() if k != "goal_ceiling_mentions_in_records"}),
            "8_goal_ceilings": "100,000 operations and 30,000 ms are source-execution ceilings of the runtime (for example ontokin/construction.py LIMITS); the cohort runs no .ok source, so no S7 record shows them; the source is unchanged (worktree clean at C, source inventory equal)",
            "9_fck1": clean(a07), "9_git_static": clean(a09), "9_listing_during_audit": clean({k: {kk: (len(vv) if isinstance(vv, list) else vv) for kk, vv in v.items()} for k, v in z02["roots"].items()}),
            "10_audit_expect": {cid: {"rules": v["rules"], "met": v["met"]} for cid, v in a10["audit_expect"].items()},
            "10_checker_audit_runs": [{"command": r["command"], "state": r["state"], "predicates": r["predicates"]} for r in a11["audit_runs"]],
            "11_records": {"commands": a10["records"]["commands"], "failures": a10["records"]["failures"],
                           "first_start_utc": a10["records"]["first_start_utc"], "last_end_utc": a10["records"]["last_end_utc"],
                           "max_wall": a10["records"]["max_wall"], "x_predicates": a10["records"]["x_predicate_total"],
                           "deferred_values_equal": a10["deferred_values"]["equal"],
                           "checker_expect_crosscheck": {"met": a11["expect_met"], "of": 72, "predicates": a11["expect_predicates_total"]}},
            "12_labels": clean(a06["labels"]),
        },
        "claims": {
            "may_claim_if_reported": "the seven original methods of tests/test_static_tray_readback_v01.py and the direct negatives P06-H01 and P06-H02 qualified on this executor only (executor macos-arm64-local), under ontokin.current-host-readback/0.2.0 at design revision 4 with P33-AMENDMENT-001, with contract section 10's labels; the MH controls with the labels listed",
            "labels": clean(a06["labels"]["expected"]),
            "never": freeze["limits"]["contract_section_10"],
            "also_not": ["MR, R03, R04, R05 or a release (MH-PLAN section 1)", "any NOT_RUN control as passed",
                         "HOST's four claims as complete (HR-06)", "the Node archive's signature (signature_check not_performed)",
                         "Node behaviour beyond the three observed cases (contract section 12)"],
            "limits": freeze["limits"]["this_freeze"],
        },
        "auditor_starts": {
            "shell_tool_calls": 54, "interpreter_starts_all_-I_-S_-B": 136,
            "of_which": {"own_scripts": 42, "own_inline": 14, "bound_checker_expect_audit": 6, "bound_checker_expect": 72,
                         "audit_numeric_crosscheck": 1, "observer_python_inventory": 1},
            "env_launchers_exec_the_interpreter": 80,
            "utilities": {"wc": 3, "grep": 11, "head": 16, "cat": 15, "tail": 4, "ls": 3, "mkdir": 2},
            "note": "counts include the planned last three calls (this JSON's build, the privacy scan with the digest list, the last process check); grep and head include one upper-bound pair from a call whose first command never started (shell glob error)",
            "forbidden": {"node": 0, "git_any": 0, "ldd": 0, "codesign": 0, "otool": 0, "observe": 0, "runner": 0, "collector": 0,
                          "harness": 0, "discovery": 0, "capture_probe": 0, "wrapper": 0, "preparation_script": 0, "test_modules": 0},
            "leftover_processes": z03["matching_processes"],
        },
        "files": unique_files,
    }
    data = json.dumps(clean(doc), indent=1, sort_keys=False).encode()
    path = os.path.join(out, "AUDIT-001.json")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    print("written", path, len(data), "files listed", len(unique_files), "crosscheck rows equal", crosscheck_equal)


main()
