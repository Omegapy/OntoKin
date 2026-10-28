#!/usr/bin/env python3
"""Execute the proposed independent rate rule for the complete frozen inventory.

The 724 frozen derived-rate fields remain measurements. Each planned request
compiles and observes the original source and independently audits both rate
vectors for the required carriers under the original single request budget.
This collector never adopts the proposal or marks a release role complete.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import traceback

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ontokin.bundle import load_file_manifest
from tools.reach_source_rates import execute_source_rate_audit


DATA = ROOT / "docs/language-design/planar-reach-v0.1"
SUPPLEMENT = DATA / "draft2-supplements"
SCHEMA = "ontokin.reach-rate-inventory-proposal/0.1"


def sha(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, check=True,
                          stdout=subprocess.PIPE).stdout


def input_identity():
    rows = []
    for name in sorted(git("ls-files", "-z").decode().split("\0")):
        if not name:
            continue
        path = ROOT / name
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(ROOT):
            raise ValueError("Missing or escaping tracked input: " + name)
        raw = path.read_bytes()
        rows.append({"path": name, "bytes": len(raw), "sha256": sha(raw)})
    return {"commit": git("rev-parse", "HEAD").decode().strip(),
            "tree": git("rev-parse", "HEAD^{tree}").decode().strip(),
            "status": git("status", "--porcelain=v1", "--untracked-files=all").decode(),
            "inputs": rows}


def inventory():
    original = json.loads((DATA / "acceptance.json").read_text())
    supplementary = json.loads((SUPPLEMENT / "acceptance.json").read_text())
    cases = {row["id"]: (DATA, row) for row in original["source_cases"]}
    cases.update({row["id"]: (SUPPLEMENT, row) for row in supplementary["source_cases"]})
    if set(cases) != ({f"P{i:02}" for i in range(1, 27)} |
                      {f"N{i:02}" for i in range(1, 16)} | {f"L{i:02}" for i in range(1, 5)}):
        raise ValueError("The frozen 45-case source inventory changed")
    mapping = json.loads((ROOT / "docs/engineering/reach-source-acceptance-validation/source-case-map.json").read_text())
    for name, expected in mapping["frozen_input_hashes"].items():
        if sha((ROOT / name).read_bytes()) != expected:
            raise ValueError("A frozen source-corpus input changed: " + name)
    planned = []

    def add(case_id, label, clock, side, fields):
        directory, case = cases[case_id]
        manifest = directory / case["file_manifest"]
        if sha(manifest.read_bytes()) != case["file_manifest_sha256"]:
            raise ValueError("A frozen file manifest changed: " + case_id)
        planned.append({"id": case_id + "." + label, "case_id": case_id,
            "file_manifest": str(manifest.relative_to(ROOT)), "program_revision": case["program_revision"],
            "time_seconds": str(clock), "side": side,
            "carriers": list(dict.fromkeys(field["carrier"] for field in fields)),
            "frozen_fields": fields})

    def physical(arm, sample):
        return [{"carrier": arm + ".forearm.tip.frame", "field": "velocity_m_per_s",
                 "frozen_field": "tip_velocity_world_m_per_s", "measurement": sample["tip_velocity_world_m_per_s"]},
                {"carrier": arm + ".forearm.frame", "field": "angular_velocity_rad_per_s",
                 "frozen_field": "forearm_omega_world_rad_per_s", "measurement": sample["forearm_omega_world_rad_per_s"]}]

    for case_id, (_, case) in cases.items():
        expected = case.get("expected", case)
        for index, sample in enumerate(expected.get("samples", [])):
            clock = Fraction(int(sample["time"]["numerator"]), int(sample["time"]["denominator"]))
            arm = "rig.arm" if case_id.startswith("L") else expected["tracked_arm"]
            add(case_id, f"sample-{index:03}", clock, sample["side"], physical(arm, sample.get("physical", sample)))
        if case_id == "P16":
            release = expected["release"]
            add(case_id, "release-incoming", Fraction(2), "before",
                physical(expected["tracked_arm"], release["incoming_state"]))
            for endpoint in (3, 4):
                fields = [{"carrier": "payload.frame", "field": "velocity_m_per_s",
                    "frozen_field": f"velocity_at_{endpoint}_seconds_m_per_s",
                    "measurement": release[f"velocity_at_{endpoint}_seconds_m_per_s"]},
                    {"carrier": "payload.frame", "field": "angular_velocity_rad_per_s",
                    "frozen_field": "constant_free_omega_world_rad_per_s",
                    "measurement": release["constant_free_omega_world_rad_per_s"]}]
                add(case_id, f"payload-{endpoint}", Fraction(endpoint), "after", fields)
    if len(planned) != 362 or sum(len(row["frozen_fields"]) for row in planned) != 724:
        raise ValueError("The original 724-field measurement inventory changed")
    if len({row["id"] for row in planned}) != len(planned):
        raise ValueError("Duplicate independent rate request identity")
    return planned


def write(path, value):
    raw = (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n").encode()
    path.write_bytes(raw)
    return {"path": path.name, "bytes": len(raw), "sha256": sha(raw)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--cases", nargs="+", help="Optional explicit case subset; coverage remains partial")
    options = parser.parse_args()
    planned = inventory()
    if options.cases:
        selected = set(options.cases)
        if len(selected) != len(options.cases) or not selected <= {row["case_id"] for row in planned}:
            parser.error("--cases must name unique cases with frozen derived-rate measurements")
        planned = [row for row in planned if row["case_id"] in selected]
    output = options.output_dir.resolve()
    if output.is_relative_to(ROOT):
        parser.error("Evidence must be outside the checkout so its own writes do not alter input identity")
    output.mkdir(parents=True, exist_ok=False)
    before = input_identity()
    write(output / "inputs-before.json", before)
    write(output / "inventory.json", planned)
    rows, started = [], utc()
    for request in planned:
        row = {"id": request["id"], "case_id": request["case_id"], "started_utc": utc(),
               "frozen_field_count": len(request["frozen_fields"])}
        try:
            source = load_file_manifest(ROOT / request["file_manifest"])
            if source.program_revision != request["program_revision"]:
                raise ValueError("Fresh source bundle identity differs from the frozen request")
            report = execute_source_rate_audit(source, time=Fraction(request["time_seconds"]),
                side=request["side"], carriers=request["carriers"])
            results = {(item["carrier"], item["field"]): item for item in report["results"]}
            required = {(item["carrier"], item["field"]) for item in request["frozen_fields"]}
            covered = required <= set(results)
            if report["status"] == "proved" and not covered:
                raise ValueError("A proposed proof omitted a required frozen measurement carrier/field")
            row.update(status=report["status"], covered=covered,
                request_operations=report["request_operations"], vector_comparison_count=len(results),
                report=write(output / (request["id"] + ".json"), report))
        except Exception as error:
            diagnostic = getattr(error, "diagnostic", None)
            failure = {"type": type(error).__name__, "message": str(error),
                "code": getattr(error, "code", None), "reach_code": getattr(error, "reach_code", None),
                "phase": getattr(diagnostic, "phase", None), "category": getattr(diagnostic, "category", None),
                "traceback": traceback.format_exc()}
            row.update(status="error", covered=False,
                report=write(output / (request["id"] + ".error.json"), failure))
        row["finished_utc"] = utc()
        rows.append(row)
        print(json.dumps({"id": row["id"], "status": row["status"]}), flush=True)
    after = input_identity()
    write(output / "inputs-after.json", after)
    stable = before == after
    counts = dict(Counter(row["status"] for row in rows))
    proved = stable and all(row["status"] == "proved" and row["covered"] for row in rows)
    result = {"schema_version": SCHEMA, "status": "proved" if proved else "not_established",
        "criterion_status": "proposed_not_adopted", "release_acceptance": False,
        "source_execution_role": "pending", "full_product_goal_completed": False,
        "started_utc": started, "finished_utc": utc(), "inputs_stable": stable,
        "command": sys.argv, "python": sys.version, "platform": platform.platform(),
        "commit": before["commit"], "tree": before["tree"], "initial_git_status": before["status"],
        "complete_frozen_rate_inventory": len(planned) == 362,
        "request_count": len(rows), "frozen_field_count": sum(row["frozen_field_count"] for row in rows),
        "proved_frozen_fields": sum(row["frozen_field_count"] for row in rows if row["status"] == "proved" and row["covered"]),
        "counts": counts, "requests": rows,
        "frozen_measurement_policy": "Frozen values identify coverage only; each verdict compares fresh actual source rates to independent ideal intervals and dimensioned source allowances.",
        "budget_scope": "Each request shares one original compiler/source/reference/rate budget. Collector input hashing and evidence serialization are outside the source requests."}
    write(output / "report.json", result)
    print(json.dumps({"status": result["status"], "counts": counts,
                      "proved_frozen_fields": result["proved_frozen_fields"]}), flush=True)
    return 0 if proved else 1


if __name__ == "__main__":
    raise SystemExit(main())
