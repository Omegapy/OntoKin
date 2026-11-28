#!/usr/bin/env python3
"""C272 qualification: one command for the frozen C253 cases V1, V2 and N1 (REQ-011).

    .venv/bin/python docs/engineering/localized-repair-c272/qualify.py --output-dir NEW_DIR

NEW_DIR must be new or empty and outside every checkout. The command:
1. runs each case from a new store through the real Agent/0.2 service with the scripted client;
2. builds the wheel of the committed revision and rebuilds each delivered source twice
   in empty workspaces;
3. observes start, final and rebuilt bytes and scores them with the unchanged C255 checker;
4. runs the evaluator and residual controls.

It writes RESULTS.json, which states for every case and check whether it passed, failed
or was not run. No model takes part, and no step is done by hand.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
import controls  # noqa: E402
import rebuild  # noqa: E402
import runner  # noqa: E402
import score  # noqa: E402

CASES = runner.CASES
WATCHED = ["ontokin", "pyproject.toml", "docs/engineering/localized-repair-c272", "docs/engineering/localized-repair-c253",
           "docs/engineering/localized-repair-c255", "docs/engineering/localized-repair-c256", "docs/engineering/localized-repair-c257",
           "docs/engineering/localized-repair-c258", "docs/engineering/localized-repair-c265", "docs/engineering/localized-repair-c266",
           "docs/engineering/localized-repair-c267", "docs/engineering/semantic-export-c210/evidence/proof"]


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()


def portable(value, out: Path):
    """JSON-safe copy: bytes become size and digest; local paths become labels."""
    if isinstance(value, bytes):
        return {"bytes": len(value), "sha256": hashlib.sha256(value).hexdigest()}
    if isinstance(value, dict):
        return {k: portable(v, out) for k, v in value.items() if k != "install_python"}
    if isinstance(value, (list, tuple)):
        return [portable(v, out) for v in value]
    if isinstance(value, str):
        for prefix, label in ((str(out), "<output>"), (str(ROOT), "<checkout>"), (str(Path.home()), "<home>")):
            value = value.replace(prefix, label)
    return value


def write(path: Path, value, out: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(portable(value, out), indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def variants() -> dict:
    def wrong_target(patch, program):
        raw, old = program.entry.raw, b'fingers["middle"].length = 0.65[m]'
        start = raw.index(old)
        return [{**patch, "element_id": ["keyed-rack", "demo"], "start_byte": start, "end_byte": start + len(old),
                 "expected_text": old.decode(), "replacement": 'fingers["upper"].length = 0.75[m]'}]
    def changed_sibling(patch, program):
        raw, old = program.entry.raw, b'"top": vec3(0[m], 1.2[m], 0[m])'
        start = raw.index(old)
        return [patch, {**patch, "element_id": ["keyed-rack", "demo"], "start_byte": start, "end_byte": start + len(old),
                        "expected_text": old.decode(), "replacement": '"top": vec3(0[m], 1.3[m], 0[m])'}]
    return {"wrong-target": wrong_target, "changed-sibling": changed_sibling}


def outcome_of(checks: dict) -> dict:
    return {name: ("not_run" if value is None else "passed" if value else "failed") for name, value in checks.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    out = args.output_dir.resolve()
    if rebuild.inside_checkout(out):
        parser.error("the output directory must lie outside every checkout")
    if out.exists() and any(out.iterdir()):
        parser.error("the output directory must be new or empty")
    dirty = git("status", "--porcelain", "--", *WATCHED)
    if dirty:
        parser.error("commit the product, the frozen inputs and this directory first; the rebuild uses the committed revision:\n" + dirty)
    out.mkdir(parents=True, exist_ok=True)
    began = time.time()
    revision, tree = git("rev-parse", "HEAD"), git("rev-parse", "HEAD^{tree}")
    corpus = score.ORACLE.load_corpus(ROOT)
    results = {"schema": "ontokin.c272.qualification/1", "revision": revision, "tree": tree,
               "executor": {"python": platform.python_version(), "implementation": platform.python_implementation(),
                            "system": platform.system(), "release": platform.mac_ver()[0] or platform.release(),
                            "machine": platform.machine()},
               "client": runner.SCRIPTED_CLIENT, "model": runner.NOT_APPLICABLE,
               "exercised": "construction-0.1 source, Agent/0.2 (ontokin.agent/0.2) accepted edits, GLB/0.2 and the semantic sidecar",
               "family": "keyed-rack-c210, one public, previously used assembly family",
               "cases": {}, "controls": {}}
    outcomes = {o["caseId"]: o for o in runner.run_all(out / "delivery")}
    prepared = rebuild.prepare(out / "rebuild", revision)
    results["rebuild_environment"] = {k: v for k, v in prepared.items() if k != "install_python"}
    materials = {}
    for case in CASES:
        o = outcomes[case]
        checks = {"runner completed": o["status"] == "completed"}
        if o["status"] != "completed":
            results["cases"][case] = {"passed": False, "runner": o["status"], "checks": outcome_of(
                {**checks, **{name: None for name in ("rebuild", "scoring", "controls")}}), "error": o.get("error")}
            continue
        record = out / "delivery/cases" / case / "record"
        authority = score.ORACLE.decode_authority(json.loads((record / "authority.json").read_text()))
        sources = authority["retained"]["sourceFiles"]
        rebuilds = [rebuild.rebuild_case(out / "rebuild", prepared, f"{case}-{k}", sources) for k in (1, 2)]
        first = rebuilds[0]
        rebuilt_artifacts = first.get("artifacts") or {}
        authority["rebuild"] = {"sourceFiles": first.get("sources_used") or dict(sources), "artifacts": rebuilt_artifacts,
                                "cleanWorkspace": bool(first.get("clean")), "declaredInputs": rebuild.DECLARED,
                                "determinism": "byte-exact"}
        cases = {c["case"]: c for c in o["protocol_cases"]}
        decision = authority["decision"]
        checks.update({
            "service decision as required": (decision["status"] == "rejected" and decision["diagnostic"] is not None)
                                            if case == "N1" else decision["status"] == "accepted",
            "identical retry returns the first response": cases["identical retry"]["equal_to_first_response"],
            "changed-payload retry is refused": (cases["changed-payload retry"]["protocol_error"] or {}).get("code") == "OKL-E-REQUEST-ID",
            "rebuild workspace clean (both runs)": all(r.get("clean") for r in rebuilds),
            "rebuild byte-identical to delivery (both runs)": all(r.get("artifacts") == authority["retained"]["artifacts"] for r in rebuilds),
            "rebuild implementation equals delivery implementation": first.get("implementation") == o["implementation"],
        })
        if case != "N1":
            checks["stale-revision edit is refused"] = cases["stale-revision edit"]["status"] == "rejected"
        start = score.observe_artifacts(authority["start"]["sourceFiles"], authority["start"]["artifacts"])
        final = score.observe_artifacts(sources, authority["retained"]["artifacts"])
        rebuilt = score.observe_artifacts(authority["rebuild"]["sourceFiles"], rebuilt_artifacts) if rebuilt_artifacts else \
            {"delivery": {"valid": False, "geometry": None, "poses": None}, "semantic": {"valid": False, "semantic": None}}
        scored = score.score_case(corpus, case, authority, start, final, rebuilt, rebuilt_artifacts, checks)
        write(out / "cases" / case / "score.json", scored, out)
        write(out / "cases" / case / "rebuild.json", rebuilds, out)
        write(out / "cases" / case / "semantic-final.json", final["semantic"], out)
        materials[case] = {"case": case, "authority": authority, "start": start, "final": final, "rebuilt": rebuilt,
                           "rebuild_artifacts": rebuilt_artifacts, "workflow": dict(checks)}
        results["cases"][case] = {
            "passed": scored["passed"], "runner": o["status"],
            "checks": outcome_of({**scored["workflowChecks"], "C255 component check": scored["c255"]["componentPass"]}),
            "c255_faults": scored["c255"]["faults"],
            "properties": {"total": len(scored["properties"]), "failed": [r for r in scored["properties"] if r["outcome"] != "passed"]},
            "poses": {"count": len(scored["poses"]), "max_position_error_m": max((p.get("position_error_m", float("inf")) for p in scored["poses"]), default=None),
                      "max_angle_error_rad": max((p.get("angle_error_rad", float("inf")) for p in scored["poses"]), default=None)},
            "locality": scored["locality"],
            "identities": {"start_program": authority["start"]["programRevision"], "final_program": authority["retained"]["programRevision"],
                           "candidate": decision["candidateId"],
                           "retained_hashes": {n: hashlib.sha256(b).hexdigest() for n, b in {**authority["retained"]["sourceFiles"], **authority["retained"]["artifacts"]}.items()}},
            "statement": scored["statement"]}
    if all(c in materials for c in CASES):
        found = {}
        for label, function in variants().items():
            o = runner.run_case("V1", out / "controls", label=label, variant=function)
            path = out / "controls/cases" / label / "record/authority.json"
            found[label] = {"outcome": o, "authority": score.ORACLE.decode_authority(json.loads(path.read_text())) if path.exists() else None}
        extras = {"undeclared-input rebuild": rebuild.rebuild_case(out / "rebuild", prepared, "control-undeclared",
                                                                    materials["V1"]["authority"]["retained"]["sourceFiles"],
                                                                    undeclared={"extra.ok": b"// undeclared input\n"})}
        if all(v["authority"] for v in found.values()):
            results["controls"]["evaluator"] = controls.evaluator_controls(corpus, materials, found, extras)
        else:
            results["controls"]["evaluator"] = [{"id": "E01-E02", "passed": False, "reason": "variant delivery failed",
                                                 "outcomes": {k: v["outcome"]["status"] for k, v in found.items()}}]
        results["controls"]["residual"] = controls.residual_controls(corpus, materials)
    else:
        results["controls"] = {"evaluator": "not_run: a case did not complete", "residual": "not_run: a case did not complete"}
    all_controls = [c for group in results["controls"].values() if isinstance(group, list) for c in group]
    results["summary"] = {"cases_passed": [c for c, r in results["cases"].items() if r["passed"]],
                          "cases_failed": [c for c, r in results["cases"].items() if not r["passed"]],
                          "controls_passed": sum(c["passed"] for c in all_controls), "controls_total": len(all_controls),
                          "controls_failed": [c["id"] for c in all_controls if not c["passed"]],
                          "seconds": round(time.time() - began, 1)}
    results["passed"] = (not results["summary"]["cases_failed"] and len(results["cases"]) == len(CASES)
                         and bool(all_controls) and not results["summary"]["controls_failed"])
    write(out / "RESULTS.json", results, out)
    print(json.dumps(portable(results["summary"], out), indent=2))
    return 0 if results["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
