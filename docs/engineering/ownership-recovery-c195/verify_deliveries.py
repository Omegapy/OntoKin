#!/usr/bin/env python3
"""Validate the four C195 author deliveries using unchanged C194/C193 readers.

G means the repaired 365 mm delivery; H means preserved 375 mm regeneration.
Every row has id, route, case, source, run and repo; H also has preserve_from.
One exclusive coordinator ledger reserves four clean builds with no retries.
Author preservation/accounting is an independently reviewed receipt, bound to
these exact sources and run inventories. Without it native/destination results
remain provisional. --finalize adds that receipt without repeating native work.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import re
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PREP = HERE.parent / "contact-preparation-c194"
sys.path.insert(0, str(PREP))
import common as c
import run_preparation as setup


def public_inputs(root):
    root = Path(root).resolve()
    frozen = json.loads((HERE / "FREEZE.json").read_text())
    path = HERE / "INPUTS.json"
    c.require(frozen["author_dispatch_authorized"] is True, "C195 dispatch was not authorized")
    c.require(frozen["authors_before_freeze"] == frozen["native_builds_before_freeze"] == 0,
              "C195 freeze did not precede the exercise")
    c.require(c.digest(path) == frozen["input_manifest_sha256"], "C195 input manifest changed")
    for name in ("FREEZE.json", "INPUTS.json", "evidence/FIXTURE-REVIEW.json"):
        c.require((root / HERE.relative_to(REPO) / name).read_bytes() == (HERE / name).read_bytes(),
                  "Author freeze differs: " + name)
    review_path = HERE / "evidence/FIXTURE-REVIEW.json"
    c.require(c.digest(review_path) == frozen["independent_review_sha256"], "Fixture review changed")
    review = json.loads(review_path.read_text())
    c.require(review["passed"] and review["input_manifest_sha256"] == c.digest(path),
              "Fixture review did not approve these inputs")
    c.require(c.digest(HERE / "evidence/STATIC-QUALIFICATION.json") == frozen["static_qualification_sha256"],
              "Static qualification changed")
    c.require(c.digest(HERE / "PROTOCOL.md") == frozen["protocol_sha256"], "Protocol changed")
    manifest = json.loads(path.read_text())
    seen = set()
    for row in manifest["files"]:
        p = (root / row["path"]).resolve()
        c.require(p.is_relative_to(root) and p not in seen, "Invalid or duplicate frozen input path")
        seen.add(p)
        c.require(p.is_file() and p.stat().st_size == row["bytes"] and c.digest(p) == row["sha256"],
                  "Frozen input differs: " + str(p))
    return {"passed": True, "files": len(seen), "manifest_sha256": c.digest(path),
            "freeze_sha256": c.digest(HERE / "FREEZE.json")}


def inventory(root):
    return {str(p.relative_to(root)): {"bytes": p.stat().st_size, "sha256": c.digest(p)}
            for p in sorted(root.rglob("*")) if p.is_file()}


def inventory_sha256(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate_rows(rows):
    c.require(isinstance(rows, list) and len(rows) == 4, "Exactly four C195 deliveries required")
    c.require(len({r["id"] for r in rows}) == 4, "Duplicate delivery identity")
    c.require(all(re.fullmatch(r"[a-zA-Z0-9_-]+", r["id"]) for r in rows), "Unsafe delivery identity")
    c.require({(r["case"], r["route"]) for r in rows} ==
              {(case, route) for case in ("G", "H") for route in ("ok", "python")},
              "Expected repaired G and preserved H for both routes")
    c.require(all(r.get("preserve_from") for r in rows if r["case"] == "H"),
              "Both H deliveries require their actual C194 accepted artifact")
    c.require(len({str(Path(r["run"]).resolve()) for r in rows}) == 4,
              "Submitted variants must use four separate native runs")


def source_and_baseline(row):
    route, case = row["route"], row["case"]
    bases = json.loads((HERE / "BASELINES.json").read_text())
    base = bases["routes"][route]
    original = (REPO / base["source"]).read_bytes()
    c.require(hashlib.sha256(original).hexdigest() == base["source_sha256"], "Accepted baseline changed")
    source = Path(row["source"])
    if case == "G":
        token = b'at = [375, 130, -220][mm];' if route == "ok" else b"'at_mm': [375, 130, -220]"
        c.require(original.count(token) == 1, "Stop coordinate is not uniquely identified")
        expected = original.replace(token, token.replace(b"375", b"365"))
    else:
        expected = original
    c.require(source.read_bytes() == expected, "Source has an unrelated or incomplete repair")
    result = {"passed": True, "baseline_source_sha256": base["source_sha256"],
              "source_sha256": c.digest(source), "only_intended_stop_delta": case == "G",
              "exact_accepted_source": case == "H"}
    if case == "H":
        previous = Path(row["preserve_from"]).resolve()
        c.require(inventory(previous) == base["artifact_files"], "C194 accepted artifact closure differs")
        acceptance = REPO / bases["acceptance"]
        c.require(c.digest(acceptance) == bases["acceptance_sha256"], "C194 acceptance changed")
        accepted = json.loads(acceptance.read_text())
        c.require(accepted["accepted"] is True, "C194 baseline is not accepted")
        entry = next(x for x in accepted["sources_and_artifacts"] if x["id"] == route + "-reuse")
        c.require(entry["source_sha256"] == base["source_sha256"], "C194 baseline source identity differs")
        c.require(all(c.digest(previous / n) == h for n, h in entry["artifacts"].items()),
                  "C194 accepted outputs differ")
        result.update(accepted_artifact=str(previous), acceptance_sha256=c.digest(acceptance),
                      accepted_artifact_inventory_sha256=inventory_sha256(inventory(previous)))
    return result


def author_audit(path, rows, manifest_sha):
    """Bind an independent review of raw author evidence to these exact runs."""
    if path is None:
        return {"passed": False, "status": "PENDING", "reason": "Independent author evidence review required"}
    audit = json.loads(path.read_text())
    c.require(audit["schema"] == "ontokin.c195.author-evidence-audit/0.1" and audit["passed"] is True,
              "Author evidence audit did not pass")
    c.require(audit["input_manifest_sha256"] == c.digest(HERE / "INPUTS.json") and
              audit["freeze_sha256"] == c.digest(HERE / "FREEZE.json") and
              audit["delivery_manifest_sha256"] == manifest_sha, "Author audit binds different inputs")
    c.require(set(audit["authors"]) == {"ok", "python"}, "Both author reviews are required")
    for route in ("ok", "python"):
        author = audit["authors"][route]
        for key in ("passed", "rejection_observed", "diagnostic_accurate",
                    "baseline_preserved_after_rejection", "baseline_preserved_at_submission"):
            c.require(author[key] is True, route + ": " + key + " failed")
        c.require(author["negative_native_substeps"] == 0 and author["negative_native_outputs"] is False,
                  "Negative candidate reached native work")
        elapsed = author["wall_seconds"]
        c.require(isinstance(elapsed, (int, float)) and math.isfinite(elapsed) and 0 <= elapsed <= 1200,
                  "Author wall allowance exceeded")
        submissions = author["formal_submissions"]
        c.require(type(submissions) is int and 1 <= submissions <= 3, "Submission allowance exceeded")
        c.require(type(author["repaired_native_builds"]) is int and author["repaired_native_builds"] == 1 and
                  type(author["baseline_native_builds"]) is int and author["baseline_native_builds"] == 1,
                  "Native construction allowance exceeded or incomplete")
        c.require(bool(author["evidence"]), "Raw author evidence identities missing")
        for evidence in author["evidence"]:
            evidence_path = Path(evidence["path"])
            c.require(evidence_path.is_file() and evidence_path.stat().st_size == evidence["bytes"] and
                      c.digest(evidence_path) == evidence["sha256"], "Raw author evidence changed")
        for row in (r for r in rows if r["route"] == route):
            declared = author["submissions"][row["case"]]
            c.require(declared["source_sha256"] == c.digest(row["source"]) and
                      declared["run_inventory_sha256"] == inventory_sha256(inventory(Path(row["run"]))),
                      "Author review does not bind the actual submitted source/run")
    return {"passed": True, "status": "PASSED", "path": str(path.resolve()), "sha256": c.digest(path)}


def finalize_author_audit(args, rows):
    """Add the independent author review without invoking any native tool."""
    c.require(args.author_audit is not None, "Finalization requires --author-audit")
    result_path = args.out / "RESULTS.json"
    record = json.loads(result_path.read_text())
    c.require(record["schema"] == "ontokin.c195.author-delivery-validation/0.1", "Wrong validation record")
    c.require(record["manifest_sha256"] == c.digest(args.manifest), "Delivery manifest changed")
    public_inputs(REPO)
    c.require(record["numerical_receiving_gates_passed"] is True, "Numerical/receiving gates failed")
    for row in rows:
        source_and_baseline(row)
        public_inputs(Path(row["repo"]))
        retained = next(r for r in record["runs"] if r["id"] == row["id"])
        c.require(retained["source_sha256"] == c.digest(row["source"]) and
                  retained["run_inventory_sha256"] == inventory_sha256(inventory(Path(row["run"]))),
                  "Submitted bytes changed since native validation")
    audit = author_audit(args.author_audit, rows, record["manifest_sha256"])
    final = {"schema": "ontokin.c195.final-automated-validation/0.1",
             "finished_utc": datetime.now(timezone.utc).isoformat(),
             "validation_sha256": c.digest(result_path), "author_audit": audit,
             "automated_gates_passed": True, "visual_review": "PENDING",
             "new_native_builds": 0, "new_native_replays": 0, "new_receiving_executions": 0}
    c.write(args.out / "FINAL-AUTOMATED-RESULT.json", final, exclusive=True)
    print(json.dumps(final), flush=True)
    return 0


def provenance(artifact, route, source, case):
    sys.path.insert(0, str(c.C193 / "independent"))
    module = c.load_module("c194_public_provenance", c.C193 / "independent/audit_provenance.py")
    audit = module.audit(artifact, c.CONTRACT, c.C193 / "independent/evidence/candidate-review.json")
    retained = artifact / ("source.ok" if route == "ok" else "source.py")
    c.require(retained.read_bytes() == source.read_bytes(), "Retained source differs from author submission")
    c.require(json.loads((artifact / "canonical-input.json").read_text()) ==
              json.loads((PREP / ("frozen/" + case + "-canonical.json")).read_text()),
              "Canonical input differs from frozen target")
    if route == "ok":
        store = artifact.parent.parent
        state = json.loads((store / "state.json").read_text())
        c.require(state["schema"] == "ontokin.c193.store/0.1", "Wrong accepted-store namespace")
        c.require((store / state["artifact_directory"]).resolve() == artifact.resolve(), "Store points elsewhere")
        c.require(state["manifest_sha256"] == c.digest(artifact / "manifest.json"), "Store manifest differs")
    return audit


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--blender", type=Path)
    p.add_argument("--author-audit", type=Path)
    p.add_argument("--finalize", action="store_true", help="Attach author audit; no native or receiving work")
    a = p.parse_args()
    rows = json.loads(a.manifest.read_text())
    validate_rows(rows)
    if a.finalize:
        return finalize_author_audit(a, rows)
    c.require(a.blender is not None, "--blender is required for native validation")
    c.verify_freeze()
    freeze = public_inputs(REPO)
    c.require(c.digest(a.blender) == c.BLENDER_SHA, "Pinned Blender differs")
    for row in rows:
        public_inputs(Path(row["repo"]))
        source_and_baseline(row)
    if a.author_audit is not None:
        author_audit(a.author_audit, rows, c.digest(a.manifest))
    c.require(not a.out.exists(), "Validation output must be a new directory")
    ledger_path = HERE / "COORDINATOR-EXECUTION.json"
    ledger = {"schema": "ontokin.c195.coordinator-execution/0.1",
              "reserved_utc": datetime.now(timezone.utc).isoformat(),
              "manifest_sha256": c.digest(a.manifest), "freeze_sha256": freeze["freeze_sha256"],
              "output": str(a.out.resolve()), "planned_builds": [r["id"] for r in rows],
              "started_builds": [], "automatic_retries": False}
    c.write(ledger_path, ledger, exclusive=True)
    a.out.mkdir(parents=True, exist_ok=False)
    out = a.out.resolve()
    record = {"schema": "ontokin.c195.author-delivery-validation/0.1",
              "started_utc": datetime.now(timezone.utc).isoformat(),
              "manifest_sha256": c.digest(a.manifest), "public_inputs": freeze,
              "coordinator_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
              "orchestrator_sha256": c.digest(__file__), "automatic_retry_allowed": False,
              "runs": [], "automated_gates_passed": False, "numerical_receiving_gates_passed": False,
              "author_audit": {"passed": False, "status": "PENDING"}, "visual_review": "PENDING"}
    c.write(out / "RESULTS.json", record)
    reader = c.artifact_reader()
    reader.verify_frozen()
    receiving = []
    for row in rows:
        identifier, route, case = row["id"], row["route"], row["case"]
        run, source, author_repo = (Path(row[k]).resolve() for k in ("run", "source", "repo"))
        public_inputs(author_repo)
        localized = source_and_baseline(row)
        before = inventory(run)
        c.write(out / "inventories" / (identifier + "-before.json"), before, exclusive=True)
        receipt = json.loads((run / "delivery.json").read_text())
        artifact = setup.retained_artifact(run, route, receipt)
        result = {"id": identifier, "route": route, "case": case, "source_sha256": c.digest(source),
                  "artifact": str(artifact), "submitted_run": str(run), "source_locality": localized,
                  "run_inventory_sha256": inventory_sha256(before), "passed": False, "failures": []}
        try:
            c.require(receipt["successful"] and receipt["source_unchanged_during_build"], "Author producer failed")
            c.require(receipt["source_sha256"] == c.digest(source), "Author source no longer matches build")
            cost = receipt["cost"]
            c.require(cost["requested_operations"] == cost["host_operations_ceiling"] == 1000000 and
                      cost["requested_elapsed_ms"] == cost["host_elapsed_ms_ceiling"] == 80000,
                      "Author construction changed a frozen budget")
            result["author_cost"] = cost
            result["author_build_elapsed_s"] = receipt["elapsed_s"]
            audit = provenance(artifact, route, source, case)
            c.require(audit["passed"], "Submitted source/implementation provenance failed")
            c.write(out / "reports" / (identifier + "-provenance.json"), audit, exclusive=True)
            numerical = reader.review(artifact, case, c.CONTRACT / "backend.json", c.BACKEND_SHA, c.SOURCE_BINDING)
            c.write(out / "reports" / (identifier + "-artifact.json"), numerical, exclusive=True)
            c.require(numerical["passed"], "Numerical reader rejected: " + repr(numerical["failures"]))
            result["native_peak_mm"] = numerical["diagnosis"]["peak"]["distance_mm"]
            result["continuous_bound_mm"] = numerical["mapping_measurements"]["maximumContinuousRawToFinalVertexDeviationBoundMm"]
            result["artifacts"] = {name: c.digest(artifact / name) for name in setup.EQUAL_FILES}
            result["reopen"] = setup.reopen(artifact, identifier, route, case, a.blender, out)
            rebuilt = out / "builds" / identifier
            ledger["started_builds"].append({"id": identifier, "started_utc": datetime.now(timezone.utc).isoformat()})
            c.write(ledger_path, ledger)
            build = setup.command("rebuild-" + identifier,
                [sys.executable, "-B", c.C193 / "native/build.py", "--repo", REPO, "--route", route,
                 "--source", source, "--out", rebuilt, "--blender", a.blender], out, 110)
            new_receipt = json.loads((rebuilt / "delivery.json").read_text())
            c.require(build["passed"] and new_receipt["successful"], "Independent clean rebuild failed")
            new_artifact = setup.retained_artifact(rebuilt, route, new_receipt)
            rebuilt_provenance = provenance(new_artifact, route, source, case)
            c.require(rebuilt_provenance["passed"], "Clean rebuild provenance failed")
            c.write(out / "reports" / (identifier + "-rebuild-provenance.json"), rebuilt_provenance, exclusive=True)
            rebuilt_audit = reader.review(new_artifact, case, c.CONTRACT / "backend.json", c.BACKEND_SHA, c.SOURCE_BINDING)
            c.write(out / "reports" / (identifier + "-rebuild-artifact.json"), rebuilt_audit, exclusive=True)
            c.require(rebuilt_audit["passed"], "Independent rebuild numerical gates failed")
            result["clean_regeneration"] = {name: c.digest(new_artifact / name) == sha for name, sha in result["artifacts"].items()}
            c.require(all(result["clean_regeneration"].values()), "Independent rebuild bytes differ")
            result["coordinator_build_cost"] = new_receipt["cost"]
            if case == "H":
                previous = Path(row["preserve_from"])
                result["accepted_375_regeneration"] = {name: c.digest(previous / name) == sha for name, sha in result["artifacts"].items()}
                c.require(all(result["accepted_375_regeneration"].values()), "Accepted C194 375 mm output did not regenerate exactly")
                result["accepted_375_source_preserved"] = (previous / ("source.ok" if route == "ok" else "source.py")).read_bytes() == source.read_bytes()
                c.require(result["accepted_375_source_preserved"], "Accepted C194 375 mm source changed")
            receiving.append({"id": identifier, "artifact": str(artifact), "contact_s": c.CASES[case]["ideal_first_contact_s"], "final_gap_mm": 0, "render": True})
        except Exception as error:
            result["failures"].append(type(error).__name__ + ": " + str(error))
        result["submitted_bytes_preserved"] = before == inventory(run)
        if not result["submitted_bytes_preserved"]:
            result["failures"].append("Submitted run bytes changed during independent validation")
        result["submitted_source_preserved"] = c.digest(source) == result["source_sha256"]
        if not result["submitted_source_preserved"]:
            result["failures"].append("Submitted editable source changed during independent validation")
        result["passed"] = not result["failures"]
        record["runs"].append(result)
        c.write(out / "RESULTS.json", record)
        print(json.dumps({k: result[k] for k in ("id", "passed", "failures")}), flush=True)
    groups = {}
    for result in record["runs"]:
        groups.setdefault(result["case"], []).append(result)
    record["route_equality"] = {case: all(len(group) == 2 and len({r.get("artifacts", {}).get(name) for r in group}) == 1 and all(name in r.get("artifacts", {}) for r in group) for name in setup.EQUAL_FILES) for case, group in groups.items()}
    c.write(out / "receiving-manifest.json", receiving, exclusive=True)
    try:
        c.require(len(receiving) == len(rows), "A delivery did not qualify for receiving")
        command = setup.command("receiving", [sys.executable, "-B", c.C193 / "tools/receive.py", "--repo", REPO,
            "--manifest", out / "receiving-manifest.json", "--blender", a.blender, "--out", out / "receiving"], out, 570)
        c.require(command["passed"], "Receiving command failed")
        summary = json.loads((out / "receiving/summary.json").read_text())
        c.require(summary["pass_for_executed_receiving_checks"] and summary["khronos_errors"] == 0 and summary["khronos_warnings"] == 0 and summary["glb_paths"] == 2*len(rows) and summary["three_poses"] == 6*len(rows) and summary["blender_import_jobs"] == len(rows), "Receiving counts or gates differ")
        record["receiving"] = {"passed": True, "summary": summary, "summary_sha256": c.digest(out / "receiving/summary.json")}
    except Exception as error:
        record["receiving"] = {"passed": False, "failure": type(error).__name__ + ": " + str(error)}
    record["numerical_receiving_gates_passed"] = all(r["passed"] for r in record["runs"]) and all(record["route_equality"].values()) and record["receiving"]["passed"]
    try:
        record["author_audit"] = author_audit(a.author_audit, rows, record["manifest_sha256"])
    except Exception as error:
        record["author_audit"] = {"passed": False, "status": "FAILED", "failure": str(error)}
    record["automated_gates_passed"] = record["numerical_receiving_gates_passed"] and record["author_audit"]["passed"]
    record["finished_utc"] = datetime.now(timezone.utc).isoformat()
    record["input_preservation_after"] = public_inputs(REPO)
    record["author_input_preservation_after"] = {str(Path(r["repo"]).resolve()): public_inputs(Path(r["repo"])) for r in rows}
    c.write(out / "RESULTS.json", record)
    print(json.dumps({"automated_gates_passed": record["automated_gates_passed"], "visual_review": "PENDING"}), flush=True)
    return 0 if record["automated_gates_passed"] else (2 if record["numerical_receiving_gates_passed"] and record["author_audit"]["status"] == "PENDING" else 1)


if __name__ == "__main__":
    raise SystemExit(main())
