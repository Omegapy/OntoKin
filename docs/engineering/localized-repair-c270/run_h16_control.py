#!/usr/bin/env python3
"""Execute the frozen H16 control without evaluating or exporting source."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import subprocess
import sys
import traceback


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def identity(path):
    raw = path.read_bytes()
    return {"path": str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path),
            "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def git(*args):
    return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--phase", required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    source_path = HERE.parent / "localized-repair-c265/source_hinges.py"
    compare_path = HERE.parent / "localized-repair-c267/hinge_compare.py"
    proof = HERE.parent / "semantic-export-c210/evidence/proof"
    control = HERE / "control"
    input_paths = [source_path, compare_path,
                   HERE.parent / "localized-repair-c266/hinge_binding.py",
                   HERE.parent / "localized-repair-c261/hinge_glb.py",
                   HERE.parent / "localized-repair-c257/ownership.py",
                   proof / "before.main.ok", proof / "hinges.ok", proof / "before.glb",
                   *sorted(p for p in control.rglob("*") if p.is_file()), Path(__file__).resolve()]
    before = [identity(p) for p in input_paths]
    report = {"schema": "ontokin.c270.h16-control/1", "phase": args.phase,
              "started_at_utc": datetime.now(timezone.utc).isoformat(),
              "source_revision": git("rev-parse", "HEAD"),
              "source_tree": git("rev-parse", "HEAD^{tree}"),
              "tracked_dirty_status": git("status", "--porcelain", "--untracked-files=no"),
              "all_dirty_status": git("status", "--porcelain"),
              "environment": {"python": sys.version, "platform": platform.platform(),
                              "executable": identity(Path(sys.executable).resolve())},
              "command": [sys.executable, *sys.argv], "inputs": before,
              "expected_code": "UNSUPPORTED_SOURCE_FORM", "cases": [],
              "scope": "One frozen source-valid SiteRef parameter; source refusal propagation only",
              "artifact_policy": "Unchanged original before.glb; not rebound and no paired agreement claimed. C266 calls source observation before artifact parsing/provenance; refusal chain is retained.",
              "limits": ["No source compiler/evaluator/exporter execution", "No implementation repair",
                         "No H20/H22/H24 or full C260/product/site/world qualification"]}
    write(out / "RESULTS.json", report)
    if report["tracked_dirty_status"]:
        report["setup_failure"] = "Tracked candidate is dirty"
        write(out / "RESULTS.json", report)
        return 2
    baseline = {"main.ok": (proof / "before.main.ok").read_bytes(),
                "hinges.ok": (proof / "hinges.ok").read_bytes()}
    changed = {name: (control / name).read_bytes() for name in ("main.ok", "hinges.ok")}
    raw = (proof / "before.glb").read_bytes()
    expected_path = control / "EXPECTED.json"
    oracle = json.loads(expected_path.read_text())
    for function in ("observe_source_hinges", "compare_hinges"):
        assert oracle["expected"][function]["exact_code"] == "UNSUPPORTED_SOURCE_FORM"
    for item in oracle["supplied_sources"] + oracle["original_inputs"]:
        actual = identity(REPO / item["path"])
        assert (actual["bytes"], actual["sha256"]) == (item["bytes"], item["sha256"])
    source = load("c270_source_under_test", source_path)
    binding = load("c270_binding_under_test", HERE.parent / "localized-repair-c266/hinge_binding.py")
    comparison = load("c270_comparison_under_test", compare_path)
    report["frozen_expectation"] = identity(expected_path)
    forbidden = {"hinges", "sites", "objects", "hingeCount", "siteCount", "objectCount",
                 "inputBindingVerified", "hingeComparisonVerified", "hingeSetAgreementVerified",
                 "endpointAgreementVerified", "qualified"}
    source_failure = None
    for label, module, function, files, is_comparison, negative in (
        ("original-source", source, "observe_source_hinges", baseline, False, False),
        ("original-comparison", comparison, "compare_hinges", baseline, True, False),
        ("siteref-source", source, "observe_source_hinges", changed, False, True),
        ("siteref-binding", binding, "bind_hinge_inputs", changed, True, True),
        ("siteref-comparison", comparison, "compare_hinges", changed, True, True),
    ):
        case = {"label": label, "expected": "UNSUPPORTED_SOURCE_FORM" if negative else "eight complete original hinges",
                "assertions": {}, "outcome": None}
        hashes = {k: hashlib.sha256(v).hexdigest() for k, v in files.items()}
        sizes = {k: len(v) for k, v in files.items()}
        try:
            result = getattr(module, function)(files, raw) if is_comparison else getattr(module, function)(files)
        except module.Fault as error:
            case["outcome"] = "typed_refusal"
            case["exception"] = {"class": type(error).__name__, "module": type(error).__module__, **vars(error)}
            chain = []
            current = error
            while current is not None:
                chain.append({"class": type(current).__name__, "module": type(current).__module__,
                              **vars(current), "traceback": [
                                  {"file": frame.filename, "line": frame.lineno, "function": frame.name}
                                  for frame in traceback.extract_tb(current.__traceback__)]})
                current = current.__cause__
            case["cause_chain"] = chain
            case["assertions"] = {
                "refusal_expected": negative,
                "exact_unsupported_category": error.code == "UNSUPPORTED_SOURCE_FORM",
                "source_hashes_retained": error.sourceHashes == hashes,
                "source_sizes_retained": error.sourceBytes == sizes,
                "nonempty_reason": isinstance(error.detail, str) and bool(error.detail),
                "no_partial_qualified_set": all(not (forbidden & set(row)) for row in chain),
                "optional_origin_propagated": all(row.get("origin") == error.origin for row in chain),
            }
            origin = error.origin
            case["diagnostic_origin"] = origin
            if origin is not None:
                name = origin.get("file") if isinstance(origin, dict) else None
                start = origin.get("startByte") if isinstance(origin, dict) else None
                end = origin.get("endByteExclusive") if isinstance(origin, dict) else None
                case["assertions"]["supplied_origin_matches_source"] = (
                    name in files and origin.get("sha256") == hashes[name]
                    and type(start) is int and type(end) is int and 0 <= start < end <= sizes[name])
            if label == "siteref-source":
                source_failure = {k: getattr(error, k) for k in ("code", "detail", "origin")}
            if is_comparison:
                case["assertions"].update(
                    artifact_hash_retained=error.artifactSha256 == hashlib.sha256(raw).hexdigest(),
                    artifact_size_retained=error.artifactBytes == len(raw),
                    source_refusal_propagated=len(chain) >= (3 if function == "compare_hinges" else 2) and all(
                        row.get("code") == error.code and row.get("detail") == error.detail for row in chain),
                    originating_source_identity_retained=chain[-1].get("sourceHashes") == hashes
                    and chain[-1].get("sourceBytes") == sizes,
                    originating_source_module=chain[-1]["module"] == "_c266_pinned_source",
                    originating_source_api=any(frame["file"] == str(source_path)
                                               and frame["function"] == "observe_source_hinges"
                                               for frame in chain[-1]["traceback"]),
                    equals_direct_source_failure=source_failure is not None and all(
                        getattr(error, k) == source_failure[k] for k in ("code", "detail", "origin")),
                )
        except Exception as error:
            case.update(outcome="untyped_exception", exception={"class": type(error).__name__, "detail": str(error)})
            case["assertions"] = {"typed_public_boundary": False}
        else:
            response = out / "responses" / (label + ".json")
            write(response, result)
            case.update(outcome="returned_result", response=identity(response))
            case["assertions"] = {"success_expected": not negative,
                                  "complete_original_hinges": result.get("hingeCount") == 8,
                                  "source_hashes_retained": result.get("sourceHashes") == hashes,
                                  "source_sizes_retained": result.get("sourceBytes") == sizes}
            if is_comparison:
                case["assertions"]["complete_agreement"] = all(result.get(k) is True for k in (
                    "inputBindingVerified", "hingeComparisonVerified", "hingeSetAgreementVerified", "endpointAgreementVerified"))
            else:
                case["assertions"]["complete_original_sites"] = result.get("siteCount") == 16
        case["passed"] = all(case["assertions"].values())
        report["cases"].append(case)
        write(out / "RESULTS.json", report)
        print(json.dumps({"case": label, "outcome": case["outcome"], "passed": case["passed"],
                          "code": case.get("exception", {}).get("code")}), flush=True)
    report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    report["inputs_after"] = [identity(p) for p in input_paths]
    report["inputs_unchanged"] = before == report["inputs_after"]
    report["source_revision_unchanged"] = report["source_revision"] == git("rev-parse", "HEAD")
    report["tracked_clean_after"] = not git("status", "--porcelain", "--untracked-files=no")
    report["passed"] = all(c["passed"] for c in report["cases"]) and all(report[k] for k in (
        "inputs_unchanged", "source_revision_unchanged", "tracked_clean_after"))
    report["failed_assertions"] = [{"case": c["label"], "assertion": name} for c in report["cases"]
                                    for name, passed in c["assertions"].items() if not passed]
    write(out / "RESULTS.json", report)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
