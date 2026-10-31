#!/usr/bin/env python3
"""Independently read supplied C080 evidence; import no production modules."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import struct
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.texture_reference import (FREEZE_COMMIT, FREEZE_SHA256, GLB,
    ReferenceError, bundle_identity, case_payload, check_artifact, decode_png, digest,
    exact_uv, file_payload, load_fixtures, loads, ordinary_path, require, sha)
from tools.texture_adversaries import generate


def codes(value):
    if isinstance(value, dict):
        return sorted(set(([value["code"]] if isinstance(value.get("code"), str) else []) +
                          [code for child in value.values() for code in codes(child)]))
    if isinstance(value, list):
        return sorted(set(code for child in value for code in codes(child)))
    return []


def png_inputs(fixtures):
    records = []
    for name, wanted in fixtures["expected"]["images"].items():
        raw = ordinary_path(fixtures["root"], wanted["path"]).read_bytes()
        require(len(raw) == wanted["byte_length"] and digest(raw) == wanted["sha256"], "Frozen PNG identity differs")
        record = {"name": name, "encoded_bytes": len(raw), "sha256": sha(raw)}
        try:
            actual = decode_png(raw)
        except ReferenceError as error:
            require(not wanted["expected_png_valid"], "Independent decoder refused a frozen valid PNG: " + name)
            record.update(outcome="refused", code=error.code, reason=str(error))
        else:
            require(wanted["expected_png_valid"], "Independent decoder accepted a frozen hostile PNG: " + name)
            for key in ("width", "height", "channels", "decoded_bytes", "decoded_sha256"):
                require(actual[key] == wanted[key], "PNG independent reconstruction differs: " + name + "/" + key)
            width, height, channels, pixels = actual["width"], actual["height"], actual["channels"], actual["pixels"]
            rows = [pixels[y * width * channels:(y + 1) * width * channels] for y in range(height)]
            require([digest(row) for row in rows] == wanted["row_sha256"], "Independent PNG row digests differ")
            if "complete_pixels_top_to_bottom" in wanted:
                require([list(row) for row in rows] == wanted["complete_pixels_top_to_bottom"], "Independent PNG literal pixels differ")
            for probe in wanted["pixel_probes"]:
                x, y = probe["xy"]
                require(list(rows[y][x * channels:(x + 1) * channels]) == probe["channels"], "PNG source pixel probe differs")
            record.update(outcome="reconstructed", width=width, height=height, channels=channels,
                          decoded_sha256=actual["decoded_sha256"], decoded_bytes=len(pixels),
                          row_filters=actual["row_filters"])
        records.append(record)
    require(len(records) == 47 and Counter(r["outcome"] for r in records) == {"reconstructed": 12, "refused": 35},
            "Independent PNG corpus is incomplete")
    return records


def source_expectations(fixtures):
    probes = 0
    for case in fixtures["expected"]["cases"]:
        payload = case_payload(fixtures, case)
        revision, manifest = bundle_identity(payload)
        require(revision == case["program_revision"] and manifest == case["canonical_manifest"], "Frozen canonical manifest cannot be reproduced independently")
        for binding in case.get("texture_bindings", []):
            for probe in binding.get("uv_probes", []):
                value = exact_uv(probe["position_m"], binding["mapping"])
                require([struct.pack("<f", x).hex() for x in value] == probe["uv_binary32_le_hex"], "Frozen analytic UV probe differs from exact-rational reconstruction")
                probes += 1
    color = []
    for probe in fixtures["expected"]["color_probes"]:
        normalized = probe["sample_byte"] / 255
        linear = normalized / 12.92 if normalized <= .04045 else ((normalized + .055) / 1.055) ** 2.4
        result = [linear * x for x in probe["factor_rgb"]]
        require(abs(linear - probe["linear"]) <= 1e-15 and all(abs(a - b) <= 1e-15 for a, b in zip(result, probe["multiplied_linear_rgb"])),
                "Frozen sRGB/linear multiplication reference differs")
        color.append({"sample_byte": probe["sample_byte"], "linear": linear, "multiplied_linear_rgb": result})
    witness = fixtures["cases"]["exact-rational-uv"]["texture_bindings"][0]
    actual = exact_uv([.1, 0., .25], witness["mapping"])[0]
    require(actual == 2 ** -55 and actual != float((.1 - -.2) + -.3), "Once-rounded exact-rational UV witness lost its distinction")
    return {"canonical_programs": len(fixtures["cases"]), "analytic_uv_probes": probes,
            "once_rounded_uv_witness": {"expected": actual, "binary32_hex": struct.pack("<f", actual).hex()},
            "color_reference": color}


def verify_case(case, record, fixtures, directory):
    require(record["name"] == case["name"] and record["id"] == case["id"], "Actual source case identity mismatch")
    require(record.get("producer_status") == "observed_as_expected", "Actual source producer reported failure")
    receipt = loads(ordinary_path(directory, record["receipt"]).read_bytes())
    require(record["program_revision"] == case["program_revision"] == receipt["program_revision"], "Actual source/asset revision differs")
    require(receipt["source_revision"] == case["canonical_manifest"]["units"][0]["source_revision"], "Exact UTF-8 source hash differs")
    require(record["host_policy"] == case["host_policy"], "Producer changed frozen caller host authority")
    budget = receipt.get("execution_budget") or {}
    if budget.get("source_request") is not None:
        require(budget["source_request"] == case["host_policy"], "Actual source declaration/default budget differs")
    if case["expected_outcome"] != "valid":
        require(not record["delivered"] and "glb" not in record, "Refused source retained artifact")
        require(case["expected_code"] in codes(receipt), "Refused source lost exact frozen diagnostic")
        require(receipt.get("achieved_level") != "delivered", "Refused source claims delivery")
        if case["expected_code"] != "OKL-E-RESOURCE":
            require("OKL-E-RESOURCE" not in codes(receipt), "Resource failure substituted for required semantic refusal")
        return {"case": case["name"], "status": "passed", "outcome": "refused",
                "code": case["expected_code"], "expected_stage": case["expected_stage"],
                "actual_achieved_level": receipt.get("achieved_level"),
                "actual_budget_stage": budget.get("stage"),
                "actual_diagnostic_phases": sorted({str(d.get("phase")) for d in receipt.get("diagnostics", [])})}
    data = ordinary_path(directory, record["glb"]).read_bytes()
    require(sha(data) == record["sha256"] and len(data) == record["bytes"], "Supplied success bytes differ from producer receipt")
    control = ordinary_path(directory, record["control"]).read_bytes()
    control_payload = case_payload(fixtures, case, legacy=True)
    control_revision, _ = bundle_identity(control_payload)
    require(GLB(control, target="ontokin.glb/0.12").document["extras"]["ontokin"]["program"]["revision"] == control_revision,
            "Actual .12 control is not bound to independently frozen underlying source")
    result = check_artifact(data, case, fixtures, control)
    result.update(outcome="delivered", operations=budget.get("consumed_operations"),
                  elapsed_ms=budget.get("elapsed_ms"))
    return result


def verify_auxiliary(summary, fixtures):
    results = {}
    expected = {"transport": fixtures["transport"],
                "file_transport": fixtures["file_transport"]["cases"] + fixtures["file_transport"]["additional_isolated_probes"],
                "workflows": fixtures["workflows"]["sequences"],
                "asset_slice_probes": fixtures["workflows"]["asset_slice_boundary_probes"],
                "envelope_boundaries": fixtures["workflows"]["request_envelope_boundaries"]}
    for key, cases in expected.items():
        rows = summary.get(key, [])
        require(len(rows) == len(cases) and {r["name"] for r in rows} == {r["name"] for r in cases}, "Incomplete actual " + key)
        require(all(r.get("status") == "observed_as_expected" for r in rows), "Producer failure in " + key)
        results[key] = len(rows)
    for key in ("transport", "file_transport"):
        by_name = {r["name"]: r for r in summary[key]}
        for case in expected[key]:
            row = by_name[case["name"]]
            require(case["expected_code"] in row.get("actual_codes", []), "Transport refusal lost required diagnostic")
    mutable = next(r for r in summary["file_transport"] if r["name"] == "mutable-file-during-read")
    require(len(mutable["actual_mutations"]) == 1 and mutable["actual_mutations"][0]["after_read_bytes"] > 0,
            "Mutable input adversary was not actually exercised")
    alias = next(r for r in summary["file_transport"] if r["name"] == "input-overwritten-by-output")
    require(alias["input_hashes_before"] == alias["input_hashes_after"] and alias["exit_code"] != 0,
            "Source/image output alias damaged input or succeeded")
    return results


def verify(directory, fixtures):
    summary = loads(ordinary_path(directory, "summary.json").read_bytes())
    report = {"schema_version": "ontokin.c080-independent-readback/0.1", "status": "running",
              "started_utc": datetime.now(timezone.utc).isoformat(), "frozen_input_commit": FREEZE_COMMIT,
              "frozen_manifest_sha256": FREEZE_SHA256, "actual_git": summary["git"],
              "input_corpus_version": fixtures["corpus_version"],
              "correction_manifest_sha256": fixtures.get("correction_manifest_sha256"),
              "correction_input_commit": summary.get("correction_input_commit"),
              "release_acceptance": False, "cases": [], "agent_artifacts": [],
              "hostile_glbs": [], "failures": [], "producer_summary_sha256": sha((directory / "summary.json").read_bytes())}
    def section(label, action):
        try:
            return action()
        except Exception as error:
            report["failures"].append({"scope": label, "exception": type(error).__name__,
                                       "reason": str(error), "traceback": traceback.format_exc()})
            return None
    report["png_inputs"] = section("independent_png_inputs", lambda: png_inputs(fixtures))
    report["source_expectations"] = section("independent_source_expectations", lambda: source_expectations(fixtures))
    section("producer_frozen_identity", lambda: require(summary["frozen_input_commit"] == FREEZE_COMMIT and
        summary["frozen_manifest_sha256"] == FREEZE_SHA256 and
        summary.get("input_corpus_version", 1) == fixtures["corpus_version"] and
        summary.get("correction_manifest_sha256") == fixtures.get("correction_manifest_sha256"),
        "Producer used another input freeze/corpus version; corrections require explicit selection"))
    records = {r["name"]: r for r in summary["cases"]}
    section("source_case_inventory", lambda: require(len(summary["cases"]) == len(records) == 102 and set(records) == set(fixtures["cases"]), "Actual source case coverage differs"))
    for case in fixtures["expected"]["cases"]:
        result = section("source/" + case["name"], lambda case=case: verify_case(case, records[case["name"]], fixtures, directory))
        if result is not None:
            report["cases"].append(result)
    report["auxiliary_coverage"] = section("transport_and_workflow_inventory", lambda: verify_auxiliary(summary, fixtures))
    by_revision = {c["program_revision"]: c for c in fixtures["cases"].values() if c["expected_outcome"] == "valid"}
    for item in summary.get("agent_artifacts", []):
        def read_agent(item=item):
            case = by_revision[item["program_revision"]]
            data = ordinary_path(directory, item["glb"]).read_bytes()
            require(sha(data) == item["sha256"] and len(data) == item["bytes"], "Actual Agent artifact identity differs")
            result = check_artifact(data, case, fixtures, ordinary_path(directory, records[case["name"]]["control"]).read_bytes())
            result.update(project_id=item["project_id"], artifact_id=item["artifact_id"], source="actual_agent_artifact_slices")
            return result
        result = section("agent_artifact/" + item["glb"], read_agent)
        if result is not None:
            report["agent_artifacts"].append(result)
    def hostiles():
        artifacts = {r["name"]: ordinary_path(directory, r["glb"]).read_bytes() for r in records.values() if "glb" in r}
        regenerated = generate(fixtures, artifacts)
        actual = {r["id"]: r for r in summary.get("hostile_glbs", [])}
        require(len(actual) == len(regenerated) == 19, "Hostile supplied-byte corpus incomplete")
        require(len(summary.get("supplied_glb_positive_controls", [])) == 4 and
                all(r["status"] == "observed_as_expected" for r in summary["supplied_glb_positive_controls"]),
                "Actual supplied-GLB validator lacks successful positive controls")
        for wanted in regenerated:
            item = actual[wanted["id"]]
            raw = ordinary_path(directory, item["path"]).read_bytes()
            require(raw == wanted["data"] and sha(raw) == item["sha256"] and item["base_sha256"] == wanted["base_sha256"],
                    "Retained hostile bytes do not match the independently repeated mutation")
            require(item["status"] == "observed_as_expected" and item["actual_export_code"] == wanted["expected_code"],
                    "Actual product did not refuse the supplied hostile bytes with its adopted code")
            case = fixtures["cases"][item["case"]]
            try:
                check_artifact(raw, case, fixtures, ordinary_path(directory, records[case["name"]]["control"]).read_bytes())
            except ReferenceError as error:
                require(error.code == wanted["expected_code"], "Independent hostile classification differs")
                report["hostile_glbs"].append({"id": wanted["id"], "mutation": wanted["mutation"],
                    "sha256": sha(raw), "actual_product_code": item["actual_export_code"],
                    "independent_code": error.code, "independent_reason": str(error), "status": "passed"})
            else:
                raise ReferenceError("Independent reader accepted hostile mutation: " + wanted["mutation"])
    section("real_supplied_glb_adversaries", hostiles)
    section("producer_terminal_status", lambda: require(summary["status"] == "produced_as_expected" and not summary["failures"], "Producer did not finish every required actual operation"))
    report["status"] = "failed" if report["failures"] else "passed"
    report["finished_utc"] = datetime.now(timezone.utc).isoformat()
    report["coverage"] = {"source_cases": len(report["cases"]), "delivered_sources": sum(r["outcome"] == "delivered" for r in report["cases"]),
                          "agent_artifacts": len(report["agent_artifacts"]), "hostile_glbs": len(report["hostile_glbs"])}
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, default=ROOT / "examples/textured-surfaces")
    parser.add_argument("--corrections", type=Path, help="Explicitly select the separately frozen input corpus version 2")
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("--output must be a new report path")
    fixtures = load_fixtures(args.fixtures, args.corrections)
    report = verify(args.results.resolve(), fixtures)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], **report["coverage"], "failures": len(report["failures"])}))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
