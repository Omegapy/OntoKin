#!/usr/bin/env python3
"""Independently check actual C194 author deliveries with the frozen readers.

This is orchestration, not a new acceptance rule. Each input row identifies one
actual source/run; a new output directory reserves one validation invocation.
No retry, reconstruction or alteration of submitted artifacts is performed.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
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
    frozen = json.loads((HERE / "frozen/FREEZE.json").read_text())
    path = HERE / "frozen/INPUTS.json"
    c.require(frozen["author_dispatch_authorized"] is True, "Public dispatch was not authorized")
    for name in ("FREEZE.json", "INPUTS.json"):
        c.require((root / HERE.relative_to(REPO) / "frozen" / name).read_bytes() ==
                  (HERE / "frozen" / name).read_bytes(), "Author public freeze differs: " + name)
    c.require(c.digest(path) == frozen["input_manifest_sha256"], "Public manifest changed")
    manifest = json.loads(path.read_text())
    for row in manifest["files"]:
        p = root / row["path"]
        c.require(p.stat().st_size == row["bytes"] and c.digest(p) == row["sha256"],
                  "Frozen input differs: " + str(p))
    return {"passed": True, "files": len(manifest["files"]), "manifest_sha256": c.digest(path)}


def inventory(root):
    return {str(p.relative_to(root)): {"bytes": p.stat().st_size, "sha256": c.digest(p)}
            for p in sorted(root.rglob("*")) if p.is_file()}


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
    p.add_argument("--blender", type=Path, required=True)
    a = p.parse_args()
    rows = json.loads(a.manifest.read_text())
    c.require(len(rows) in (2, 4), "Expected first pair or four reuse deliveries")
    c.require(len({r["id"] for r in rows}) == len(rows), "Duplicate delivery identity")
    expected = {(case, route) for case in (("G",) if len(rows) == 2 else ("G", "H"))
                for route in ("ok", "python")}
    c.require({(r["case"], r["route"]) for r in rows} == expected, "Wrong route/target delivery matrix")
    if len(rows) == 4:
        c.require(all(r.get("preserve_from") for r in rows if r["case"] == "G"),
                  "Reuse requires both first-accepted artifact identities")
    c.verify_freeze()
    freeze = public_inputs(REPO)
    c.require(c.digest(a.blender) == c.BLENDER_SHA, "Pinned Blender differs")
    a.out.mkdir(parents=True, exist_ok=False)
    out = a.out.resolve()
    record = {"schema": "ontokin.c194.author-delivery-validation/0.1",
              "started_utc": datetime.now(timezone.utc).isoformat(),
              "manifest_sha256": c.digest(a.manifest), "public_inputs": freeze,
              "coordinator_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
              "orchestrator_sha256": c.digest(__file__), "automatic_retry_allowed": False,
              "runs": [], "automated_gates_passed": False, "visual_review": "PENDING"}
    c.write(out / "RESULTS.json", record)
    reader = c.artifact_reader()
    reader.verify_frozen()
    receiving = []
    for row in rows:
        identifier, route, case = row["id"], row["route"], row["case"]
        run, source, author_repo = (Path(row[k]).resolve() for k in ("run", "source", "repo"))
        public_inputs(author_repo)
        before = inventory(run)
        c.write(out / "inventories" / (identifier + "-before.json"), before, exclusive=True)
        receipt = json.loads((run / "delivery.json").read_text())
        artifact = setup.retained_artifact(run, route, receipt)
        result = {"id": identifier, "route": route, "case": case, "source_sha256": c.digest(source),
                  "artifact": str(artifact), "submitted_run": str(run), "passed": False, "failures": []}
        try:
            c.require(receipt["successful"] and receipt["source_unchanged_during_build"], "Author producer failed")
            c.require(receipt["source_sha256"] == c.digest(source), "Author source no longer matches build")
            result["author_cost"] = receipt["cost"]
            result["author_build_elapsed_s"] = receipt["elapsed_s"]
            audit = provenance(artifact, route, source, case)
            c.write(out / "reports" / (identifier + "-provenance.json"), audit, exclusive=True)
            numerical = reader.review(artifact, case, c.CONTRACT / "backend.json", c.BACKEND_SHA, c.SOURCE_BINDING)
            c.write(out / "reports" / (identifier + "-artifact.json"), numerical, exclusive=True)
            c.require(numerical["passed"], "Numerical reader rejected: " + repr(numerical["failures"]))
            result["native_peak_mm"] = numerical["diagnosis"]["peak"]["distance_mm"]
            result["continuous_bound_mm"] = numerical["mapping_measurements"]["maximumContinuousRawToFinalVertexDeviationBoundMm"]
            result["artifacts"] = {name: c.digest(artifact / name) for name in setup.EQUAL_FILES}
            result["reopen"] = setup.reopen(artifact, identifier, route, case, a.blender, out)
            rebuilt = out / "builds" / identifier
            build = setup.command("rebuild-" + identifier,
                [sys.executable, "-B", c.C193 / "native/build.py", "--repo", REPO, "--route", route,
                 "--source", source, "--out", rebuilt, "--blender", a.blender], out, 110)
            new_receipt = json.loads((rebuilt / "delivery.json").read_text())
            c.require(build["passed"] and new_receipt["successful"], "Independent clean rebuild failed")
            new_artifact = setup.retained_artifact(rebuilt, route, new_receipt)
            rebuilt_audit = reader.review(new_artifact, case, c.CONTRACT / "backend.json", c.BACKEND_SHA, c.SOURCE_BINDING)
            c.write(out / "reports" / (identifier + "-rebuild-artifact.json"), rebuilt_audit, exclusive=True)
            c.require(rebuilt_audit["passed"], "Independent rebuild numerical gates failed")
            result["clean_regeneration"] = {name: c.digest(new_artifact / name) == sha for name, sha in result["artifacts"].items()}
            c.require(all(result["clean_regeneration"].values()), "Independent rebuild bytes differ")
            result["coordinator_build_cost"] = new_receipt["cost"]
            if row.get("preserve_from"):
                previous = Path(row["preserve_from"])
                result["first_accepted_regeneration"] = {name: c.digest(previous / name) == sha for name, sha in result["artifacts"].items()}
                c.require(all(result["first_accepted_regeneration"].values()), "First accepted result changed during reuse")
                result["first_accepted_source_preserved"] = (previous / ("source.ok" if route == "ok" else "source.py")).read_bytes() == source.read_bytes()
                c.require(result["first_accepted_source_preserved"], "First accepted editable source changed during reuse")
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
    record["automated_gates_passed"] = all(r["passed"] for r in record["runs"]) and all(record["route_equality"].values()) and record["receiving"]["passed"]
    record["finished_utc"] = datetime.now(timezone.utc).isoformat()
    record["input_preservation_after"] = public_inputs(REPO)
    c.write(out / "RESULTS.json", record)
    print(json.dumps({"automated_gates_passed": record["automated_gates_passed"], "visual_review": "PENDING"}), flush=True)
    return 0 if record["automated_gates_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
