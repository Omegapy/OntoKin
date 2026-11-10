#!/usr/bin/env python3
"""Read retained C193 lifecycle receipts; never start a worker or native solve."""
import argparse
import json
from pathlib import Path

from check_artifact import HERE, digest, require
from replay_evidence import artifact_for, save, verify_review_freezes


def inventory(root):
    return {str(p.relative_to(root)): {"sha256": digest(p), "bytes": p.stat().st_size}
            for p in sorted(root.rglob("*")) if p.is_file() and "__pycache__" not in p.parts}


def audit(lifecycle, namespaces, formal, repo):
    verify_review_freezes(repo)
    review = json.loads((HERE / "evidence/candidate-review.json").read_text())
    summary = json.loads((lifecycle / "summary.json").read_text())
    lock = json.loads((lifecycle / "INPUT-LOCK.json").read_text())
    plan = json.loads((lifecycle / "TEST-PLAN.json").read_text())
    freeze = repo / "docs/engineering/guide-repair-c193/native/lifecycle/frozen/lifecycle-fixtures.json"
    frozen = json.loads(freeze.read_text())
    methods = {r["id"].split("-", 1)[0]: r for r in frozen["failure_tests"]}
    require(summary["pass"] and summary["passed"] == summary["total"] == len(summary["cases"]) == 42,
            "Full lifecycle did not pass")
    require(summary["full_frozen_lifecycle_run"] and summary["selected_cases"] is None, "Partial lifecycle run")
    require(summary["input_lock_sha256"] == digest(lifecycle / "INPUT-LOCK.json"), "Lifecycle input lock differs")
    require(summary["implementation_revision"] == lock["implementation_revision"] == review["candidate_revision"], "Lifecycle used another candidate")
    require(lock["frozen_lifecycle_sha256"] == digest(freeze), "Lifecycle expectation bytes differ")
    require(lock["source_manifest_sha256"] == digest(HERE / "frozen/source-fixtures/manifest.json"), "Lifecycle source fixtures differ")
    for root, rows in ((repo / "prototypes/guided_contact_v02", lock["prototype_files"]),
                       (repo / "docs/language-design/guided-contact-v0.2", lock["contract_files"]),
                       (repo / "docs/engineering/guide-repair-c193/native/lifecycle/checker", lock["checker_files"])):
        for name, item in rows.items():
            path = root / name
            require(path.stat().st_size == item["bytes"] and digest(path) == item["sha256"], "Lifecycle locked source changed: " + name)
    require(lock["formal_summary_sha256"] == digest(formal / "formal-builds.json") and
            lock["formal_input_lock_sha256"] == digest(formal / "INPUT-LOCK.json"), "Lifecycle did not use the formal successful batch")
    require({r["id"] for r in summary["cases"]} == {r["id"] for r in plan} and len(plan) == 42,
            "Lifecycle retained plan differs")
    require(set(summary["frozen_failure_methods_covered"]) == set(methods) and len(methods) == 19,
            "Lifecycle omitted an inherited method")
    formal_rows = json.loads((formal / "formal-builds.json").read_text())["runs"]
    seed = artifact_for(formal, next(r for r in formal_rows if r["id"] == "ok-A-1"))
    require(digest(seed / "native-result.json") == lock["seed_native_sha256"], "Lifecycle seed is not formal A")
    store = lifecycle / "accepted-store"
    state = json.loads((store / "state.json").read_text())
    accepted = store / state["artifact_directory"]
    require(digest(store / "state.json") == lock["accepted_state_sha256"], "Accepted state changed")
    require(inventory(accepted) == lock["accepted_artifacts"] == inventory(seed), "Accepted artifacts changed")
    require(summary["all_prior_accepted_bytes_unchanged"], "Intermediate preservation failed")
    cases = []
    for row in summary["cases"]:
        directory = lifecycle / row["id"]
        result = json.loads((directory / "result.json").read_text())
        require(row == json.loads((directory / "review.json").read_text()), "Per-case lifecycle review differs")
        require(row["pass"] and row["previous_state_and_artifacts_unchanged"] and not row.get("harness_emergency_kill"), "Lifecycle failed or needed emergency reap")
        require(not result["successful"] and not result["committed"] and not result["levels"]["destination_validated"], "Failed lifecycle attempt was accepted")
        require(result["accepted_revision"] == result["previous_revision"] == state["accepted_revision"], "Lifecycle changed accepted revision")
        require(result["source_sha256"] == row["source_sha256"], "Lifecycle diagnostic source differs")
        diagnostic, = result["diagnostics"]
        require(diagnostic["code"] == row["expected_code"] and diagnostic["phase"] == row["expected_phase"] and
                diagnostic["span"] == row["expected_span"], "Wrong recorded diagnostic or source span")
        if row["frozen_test"]:
            fixture = methods[row["frozen_test"]]
            require(diagnostic["code"] == fixture["expected_code"] and diagnostic["phase"] == fixture["phase"] and
                    diagnostic["blocked_levels"] == fixture["blocked_levels"], "Frozen failure expectation changed")
        require(all(not result["levels"][name] for name in diagnostic["blocked_levels"]), "Blocked runtime level reported success")
        attempt = store / "attempts" / result["attempt_id"]
        require(json.loads((attempt / "result.json").read_text()) == result, "Failed attempt receipt missing or changed")
        events = json.loads((directory / "events.json").read_text())
        if "worker_pid" in events:
            stage = attempt / "failed-stage"
            if not stage.is_dir():
                stage = store / "artifacts" / Path(events["unaccepted_candidate"]).name
            command = json.loads((stage / "native-command.json").read_text())
            require(command["pid"] == events["worker_pid"] and command["process_group"] == row["supervised_process_group"], "Supervised worker receipt differs")
            require(command["poll_ms"] <= frozen["caps"]["supervisor_poll_ms"] and
                    command["terminate_grace_ms"] <= frozen["caps"]["terminate_grace_ms"], "Supervisor bounds changed")
        cases.append({"id": row["id"], "passed": True, "diagnostic": diagnostic["code"],
                      "phase": diagnostic["phase"], "result_sha256": digest(directory / "result.json"),
                      "review_sha256": digest(directory / "review.json"), "events_sha256": digest(directory / "events.json")})
    cancel = next(r for r in summary["cases"] if r["id"] == "T02-cancel-after-start")
    deadline = next(r for r in summary["cases"] if r["id"] == "T03-deadline-running-worker")
    require(cancel["descendant_reaped"] and deadline["descendant_reaped"] and
            cancel["request_to_API_return_ms"] <= frozen["caps"]["cancellation_completion_ms"] and
            cancel["reported_cancellation_completion_ms"] <= frozen["caps"]["cancellation_completion_ms"], "Recorded cancellation or descendant reap failed")
    ns = json.loads((namespaces / "summary.json").read_text())
    require(ns["passed"] and ns["native_executions"] == 0 and len(ns["cases"]) == 2, "Namespace controls failed")
    require(ns["seed_accepted_revision"] == state["accepted_revision"], "Namespace controls used another seed")
    for row, code in zip(ns["cases"], ("C193_E_IO", "C191_E_IO")):
        require(row["passed"] and row["accepted_bytes_unchanged"] and not row["source_admitted"] and not row["native_execution"], "Cross-version store control failed")
        require(row["result"]["diagnostics"][0]["code"] == code and not row["result"]["successful"] and
                not row["result"]["committed"], "Wrong namespace rejection")
    return {"version": "C193-independent-recorded-lifecycle-review-1", "passed": True,
            "lifecycle_cases": cases, "case_count": len(cases), "inherited_method_count": len(methods),
            "namespace_controls": 2, "native_execution_in_this_review": 0,
            "accepted_artifact_files_unchanged": len(lock["accepted_artifacts"]),
            "cancellation_completion_ms": cancel["request_to_API_return_ms"],
            "lifecycle_summary_sha256": digest(lifecycle / "summary.json"),
            "lifecycle_input_lock_sha256": digest(lifecycle / "INPUT-LOCK.json"),
            "namespace_summary_sha256": digest(namespaces / "summary.json"),
            "reviewer_sha256": digest(__file__),
            "scope": "Recorded diagnostics, exact accepted-byte preservation and frozen method coverage; prior process reap is checked from retained execution receipts, not re-executed."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lifecycle", type=Path, required=True)
    parser.add_argument("--namespaces", type=Path, required=True)
    parser.add_argument("--formal", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    require(not args.out.exists(), "Output already exists")
    report = audit(args.lifecycle, args.namespaces, args.formal, args.repo)
    save(args.out, report)
    print(json.dumps({"passed": report["passed"], "cases": report["case_count"], "namespaces": report["namespace_controls"]}))


if __name__ == "__main__":
    main()
