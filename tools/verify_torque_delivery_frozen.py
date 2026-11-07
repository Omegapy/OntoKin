#!/usr/bin/env python3
"""Execute the frozen .22 exports with their original authorized allocations."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ontokin.budget_runtime import execute_budgeted_export
from ontokin.execution_budget import HostPolicy
from ontokin.profile_capabilities import TORQUE_PROFILE
from ontokin.scene import ExportOptions
from ontokin.texture_bundle import load_texture_file_manifest


def write(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--case", action="append")
    parser.add_argument("--repeat", action="store_true")
    parser.add_argument("--helpers", action="store_true",
                        help="Execute the five helper variants required by the frozen table")
    parser.add_argument("--extra-helpers", action="store_true",
                        help="Also execute optional helper variants, retaining their separate outcomes")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    frozen = ROOT / "docs/language-design/torque-v0.1/freeze"
    table = json.loads((frozen / "delivery-cases.json").read_bytes())
    cases = [row for row in table["cases"] if not args.case or row["id"] in args.case]
    if args.case and len(cases) != len(args.case):
        raise ValueError("Unknown or repeated frozen case id")
    source = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for folder in (ROOT / "ontokin", ROOT / "tools") for p in folder.glob("*")
              if p.is_file() and p.suffix in (".py", ".mjs")}
    identity = {"schema_version": "ontokin.c091-frozen-delivery-execution/1",
                "started": datetime.now(timezone.utc).isoformat(), "command": sys.argv,
                "implementation_commit": subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip(),
                "implementation_source_sha256": source, "interpreter": sys.version,
                "freeze_sha256": hashlib.sha256((frozen.parent / "INPUT-FREEZE.json").read_bytes()).hexdigest(),
                "delivery_table_sha256": hashlib.sha256((frozen / "delivery-cases.json").read_bytes()).hexdigest()}
    write(args.output / "implementation.json", identity)
    results = []
    for case in cases:
        bundle = load_texture_file_manifest(frozen / case["file_manifest"])
        assert bundle.program_revision == case["identity"]["program_revision"]
        original = None
        helpers = args.extra_helpers or args.helpers and case["helpers_true_repeat"]
        variants = ["original"] + (["repeat"] if args.repeat else []) + (["helpers"] if helpers else [])
        for variant in variants:
            folder = args.output / case["id"] / variant
            folder.mkdir(parents=True)
            started = time.monotonic()
            row = {"case": case["id"], "variant": variant, "input": case,
                   "artifact": None, "status": "failed"}
            try:
                options = {**case["options"], **({"helpers": True} if variant == "helpers" else {})}
                result = execute_budgeted_export(bundle, policy=HostPolicy(**case["host_policy"]),
                    options=ExportOptions(**options), profile=TORQUE_PROFILE)
                row["execution"] = result.report
                if result.data is not None:
                    path = folder / "scene.glb"
                    path.write_bytes(result.data)
                    row["artifact"] = {"path": path.name, "bytes": len(result.data),
                                       "sha256": hashlib.sha256(result.data).hexdigest()}
                    row["status"] = "passed"
                    if variant == "original":
                        original = result.data
                    if variant == "repeat":
                        row["complete_glb_bytes_equal"] = original is not None and result.data == original
                        if not row["complete_glb_bytes_equal"]:
                            row["status"] = "failed"
            except BaseException as error:
                row["error"] = f"{type(error).__name__}: {error}"
                row["traceback"] = traceback.format_exc()
            row["elapsed_seconds"] = time.monotonic() - started
            write(folder / "result.json", row)
            brief = {k: row[k] for k in ("case", "variant", "status", "artifact", "elapsed_seconds")}
            if row.get("error"):
                brief["error"] = row["error"]
            elif row["status"] != "passed":
                brief["diagnostics"] = row.get("execution", {}).get("diagnostics")
            results.append(brief)
            print(json.dumps(brief), flush=True)
            write(args.output / "summary.json", {**identity, "status": "passed" if all(r["status"] == "passed" for r in results) else "failed", "results": results})
    return 0 if all(row["status"] == "passed" for row in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
