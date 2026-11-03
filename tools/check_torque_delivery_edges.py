#!/usr/bin/env python3
"""Execute frozen fixed-marker delivery and the three explicit delivery refusals."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ontokin.budget_runtime import execute_budgeted_export
from ontokin.construction import compile_construction
from ontokin.evaluator import evaluate_prefix
from ontokin.execution_budget import HostPolicy, SharedExecutionBudget, admit_entry_budget
from ontokin.profile_capabilities import TORQUE_PROFILE
from ontokin.scene import ExportOptions
from ontokin.texture_bundle import load_texture_file_manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    f = ROOT / "docs/language-design/torque-v0.1/freeze"
    language = json.loads((f / "language-cases.json").read_bytes())["cases"]
    positive = next(c for c in language if c["id"] == "l02-nonidentity-fixed-local-rotation")
    negative = next(c for c in json.loads((f / "refusal-cases.json").read_bytes())["cases"]
                    if c["id"] == "n25-delivery-clock-collapse")
    cases = [{"id": "delivery-" + positive["id"], **positive["delivery_variant"], "expected": None},
        {**negative, "options": {"fps": 4, "end": "0.5", "helpers": False}},
        *[{**c, "expected": c["expected_delivery"]}
          for c in json.loads((f / "delivery-refusals.json").read_bytes())["cases"]]]
    summary = {"schema_version": "ontokin.c091-delivery-edge-execution/1", "command": sys.argv,
        "started": datetime.now(timezone.utc).isoformat(), "interpreter": sys.version,
        "commit": subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip(),
        "results": []}
    for case in cases:
        directory = args.output / case["id"]
        directory.mkdir()
        row = {"id": case["id"], "input": case, "status": "failed", "checks": []}
        try:
            bundle = load_texture_file_manifest(f / case["file_manifest"])
            assert bundle.program_revision == case["identity"]["program_revision"]
            policy = HostPolicy(**case.get("host_policy", {}))
            ledger = SharedExecutionBudget(policy)
            admit_entry_budget(bundle.entry, ledger, profile=TORQUE_PROFILE)
            compiler = compile_construction(bundle, execution_budget=ledger)
            prefix = evaluate_prefix(compiler.model, case["options"]["end"], work=compiler.reach_work)
            assert prefix["failure"] is None
            row["checks"].append("standalone construction and complete evaluated prefix accepted")
            row["evaluation_budget"] = ledger.report(status="valid")
            (directory / "evaluated-state.json").write_text(json.dumps(prefix["last_valid_state"], indent=2) + "\n")
            result = execute_budgeted_export(bundle, policy=policy, options=ExportOptions(**case["options"]), profile=TORQUE_PROFILE)
            row["execution"] = result.report
            expected = case["expected"]
            if expected is None:
                assert result.data is not None, result.report
                (directory / "scene.glb").write_bytes(result.data)
                row["artifact"] = {"bytes": len(result.data), "sha256": hashlib.sha256(result.data).hexdigest()}
                row["checks"].append("actual fixed local rotation artifact accepted with independent source/byte proof")
            else:
                assert result.data is None
                diagnostic = result.report["diagnostics"][0]
                for key in ("code", "category", "phase", "message", "blocks"):
                    assert diagnostic[key] == expected[key], (key, diagnostic[key], expected[key])
                for key, value in expected.get("required_details", expected.get("details", {})).items():
                    assert diagnostic["details"][key] == value, key
                assert diagnostic["details"]["export_code"] == expected["adapter_export_code"]
                primary = diagnostic["primary"]
                for key in ("source_id", "start_byte", "end_byte"):
                    assert primary[key] == expected["primary_source"][key], key
                unit = bundle.sources[primary["source_id"]]
                assert unit.text.encode()[primary["start_byte"]:primary["end_byte"]].decode() == expected["primary_source"]["text"]
                row["checks"].append("exact frozen refusal category, code, phase, message, details, source span and no artifact bytes")
            row["status"] = "passed"
        except BaseException as error:
            row["error"] = f"{type(error).__name__}: {error}"
            row["traceback"] = traceback.format_exc()
        (directory / "result.json").write_text(json.dumps(row, indent=2) + "\n")
        summary["results"].append({key: row[key] for key in ("id", "status", "checks")})
        summary["status"] = "passed" if all(r["status"] == "passed" for r in summary["results"]) else "failed"
        (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps({key: row.get(key) for key in ("id", "status", "error", "artifact")}), flush=True)
    return 0 if summary["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
