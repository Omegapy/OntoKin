#!/usr/bin/env python3
"""Audit retained C270 execution bytes without executing the observer again."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
EXECUTION = REPO.parent / "execution/h16-candidate"
LOG = REPO.parent / "operations/h16-candidate.log"
REVISION = "1ae7b594cc075031d11f2f1a33e4c5c0f0171da4"
TREE = "2af435b52ca1047a1a16e5a66afb91a855d1d1bd"
BASE = "254e481351239b536394c182b6761ec4c8662764"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def identity(path):
    raw = path.read_bytes()
    return {"path": str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path),
            "bytes": len(raw), "sha256": digest(raw)}


def git_bytes(revision, path):
    return subprocess.check_output(["git", "show", revision + ":" + path], cwd=REPO)


def main():
    checks = []

    def check(name, value):
        checks.append({"name": name, "passed": bool(value)})

    result_path = EXECUTION / "RESULTS.json"
    result = json.loads(result_path.read_text())
    api = json.loads((HERE / "EXECUTION-COMMIT-API.json").read_text())
    preexec = json.loads((HERE / "PREEXEC-REVIEW.json").read_text())
    check("published exact commit/tree observed through GitHub", api["sha"] == REVISION and api["commit"]["tree"]["sha"] == TREE)
    check("recorded run names exact published candidate", result["source_revision"] == REVISION and result["source_tree"] == TREE)
    check("tracked source clean during run", result["tracked_dirty_status"] == "" and result["tracked_clean_after"] is True)
    check("input and revision stability recorded", result["inputs"] == result["inputs_after"] and result["inputs_unchanged"] is True and result["source_revision_unchanged"] is True)
    inputs = {}
    for item in result["inputs"]:
        raw = git_bytes(REVISION, item["path"])
        inputs[item["path"]] = raw
        check("exact checked Git payload: " + item["path"], len(raw) == item["bytes"] and digest(raw) == item["sha256"])
        if "/localized-repair-c270/" not in item["path"]:
            check("unchanged preexisting behavior/input: " + item["path"], raw == git_bytes(BASE, item["path"]))
    for item in preexec["fixture_identities"]:
        check("preexecution review binds executed file: " + item["path"],
              digest(inputs[item["path"]]) == item["sha256"] and len(inputs[item["path"]]) == item["bytes"])
    expected = json.loads(inputs["docs/engineering/localized-repair-c270/control/EXPECTED.json"])
    check("unmodified independent oracle", result["frozen_expectation"]["sha256"] == "aa73df1e9ffb4d76bc589a7239f454be28e4cd6ae4ee523b208dbf66860ef4a7")
    check("expected category remains exact", result["expected_code"] == "UNSUPPORTED_SOURCE_FORM" and all(row["exact_code"] == "UNSUPPORTED_SOURCE_FORM" for row in expected["expected"].values()))
    cases = result["cases"]
    check("exact five planned calls retained", [row["label"] for row in cases] == ["original-source", "original-comparison", "siteref-source", "siteref-binding", "siteref-comparison"])
    check("aggregate correctly fails", result["passed"] is False)
    expected_failures = [{"case": name, "assertion": "exact_unsupported_category"} for name in ("siteref-source", "siteref-binding", "siteref-comparison")]
    check("only three exact classification assertions failed", result["failed_assertions"] == expected_failures)
    all_logs = [json.loads(line) for line in LOG.read_text().splitlines() if line.strip()]
    check("five log entries agree with retained outcomes", len(all_logs) == 5 and all(log["case"] == row["label"] and log["passed"] == row["passed"] and log["outcome"] == row["outcome"] for log, row in zip(all_logs, cases)))
    response_inputs = []
    for case in cases[:2]:
        path = Path(case["response"]["path"])
        raw = path.read_bytes()
        response = json.loads(raw)
        response_inputs.append(identity(path))
        check(case["label"] + " exact response bytes", len(raw) == case["response"]["bytes"] and digest(raw) == case["response"]["sha256"])
        check(case["label"] + " real complete original counts", len(response["records"]) == response["hingeCount"] == 8 and len(response["sites"]) == response["siteCount"] == 16)
        check(case["label"] + " unique original identities", len({tuple(row["id"]) for row in response["records"]}) == 8 and len({tuple(row["id"]) for row in response["sites"]}) == 16)
        check(case["label"] + " claims remain bounded", all(response[key] is False for key in ("historicalInputsBound", "sitePosesEvaluated", "sourceValidityQualified", "acceptedRevisionQualified", "completeC255Semantic", "executionAllowed")))
        check(case["label"] + " all baseline assertions passed", case["passed"] is True and all(case["assertions"].values()))
        if case["label"] == "original-comparison":
            check("actual complete comparison flags", all(response[key] is True for key in ("inputBindingVerified", "hingeComparisonVerified", "hingeSetAgreementVerified", "endpointAgreementVerified")))
    changed_hashes = {record["filename"]: record["sha256"] for record in expected["supplied_sources"]}
    changed_sizes = {record["filename"]: record["bytes"] for record in expected["supplied_sources"]}
    source_path = str(REPO / "docs/engineering/localized-repair-c265/source_hinges.py")
    forbidden = {"hinges", "sites", "objects", "hingeCount", "siteCount", "objectCount", "inputBindingVerified", "hingeComparisonVerified", "hingeSetAgreementVerified", "endpointAgreementVerified", "qualified"}
    for case in cases[2:]:
        error, chain = case["exception"], case["cause_chain"]
        check(case["label"] + " actual wrong category retained", case["outcome"] == "typed_refusal" and error["code"] == "MALFORMED" and case["passed"] is False)
        check(case["label"] + " exact existing source reason", error["detail"] == "endpoint must resolve to a declared site")
        check(case["label"] + " exact frozen source identities", error["sourceHashes"] == changed_hashes and error["sourceBytes"] == changed_sizes)
        check(case["label"] + " no returned or partial qualified set", "response" not in case and all(not (forbidden & set(node)) for node in chain))
        check(case["label"] + " only code assertion failed", [name for name, passed in case["assertions"].items() if not passed] == ["exact_unsupported_category"])
        check(case["label"] + " source cause follows exact endpoint path", all(any(frame["file"] == source_path and frame["line"] == number and frame["function"] == function for frame in chain[-1]["traceback"]) for number, function in ((552, "endpoint"), (521, "site"), (63, "_require"))))
        check(case["label"] + " optional source origin remains explicit null", error["origin"] is None and case["diagnostic_origin"] is None and all(node["origin"] is None for node in chain))
        if case["label"] != "siteref-source":
            check(case["label"] + " correct source cause attribution", chain[-1]["module"] == "_c266_pinned_source" and chain[-1]["sourceHashes"] == changed_hashes and chain[-1]["sourceBytes"] == changed_sizes)
            check(case["label"] + " code/reason propagated unchanged", all(node["code"] == "MALFORMED" and node["detail"] == error["detail"] for node in chain))
            check(case["label"] + " supplied artifact identity retained", error["artifactSha256"] == expected["comparison_input"]["sha256"] and error["artifactBytes"] == expected["comparison_input"]["bytes"])
    source_lines = inputs["docs/engineering/localized-repair-c265/source_hinges.py"].decode().splitlines()
    check("failure source code matches explanatory path", 'member is not None and member["memberKind"] == "site"' in source_lines[520] and 'code="MALFORMED"' in source_lines[60])
    report = {
        "schema": "ontokin.c270.independent-execution-audit/1", "reviewer": "/root/reconcile",
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(), "checked_candidate": REVISION, "checked_tree": TREE,
        "script": identity(Path(__file__).resolve()), "command": [sys.executable, *sys.argv],
        "environment": {"python": sys.version, "platform": platform.platform()},
        "retained_inputs": [identity(result_path), identity(LOG), identity(HERE / "EXECUTION-COMMIT-API.json"), *response_inputs],
        "check_count": len(checks), "checks": checks, "passed": all(row["passed"] for row in checks),
        "failed_audit_checks": [row["name"] for row in checks if not row["passed"]],
        "audit_result_is_control_pass": False,
        "control_outcome": "failed exact required UNSUPPORTED_SOURCE_FORM classification in source, binding and comparator; original positive controls passed",
        "defect": "Preexisting C265 declaration-kind classification conflates a missing endpoint name with an existing SiteRef parameter; C266/C267 correctly propagate the wrong source category.",
        "reviewer_observer_or_product_executions": 0,
        "required_state": "R02/H16.02 remains unmet; no full H16/C260 or product qualification; task/issue remain open",
    }
    out = HERE / "EXECUTION-REVIEW.json"
    if out.exists():
        raise FileExistsError("Do not overwrite a prior audit")
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"audit_passed": report["passed"], "checks": len(checks), "failed_audit_checks": report["failed_audit_checks"], "control_passed": False, "output": str(out.relative_to(REPO))}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
