#!/usr/bin/env python3
"""Execute the exact required source-to-GLB corpus on unchanged request budgets.

Every selected case is a separate actual source/export request. A case filter
creates a finite development probe, never a claim that the full corpus passed.
Actual native/browser checks and the independent release audit are separate.
"""
import argparse
from fractions import Fraction
from pathlib import Path
import platform
import sys
import time
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.reach_delivery_inventory import (ROOT, SOURCE_CASES, descriptor,
    finish_inputs, fresh_output, frozen_cases, require, selected_cases, settings, sha, snapshot,
    source_files, utc, write_json)


def build(output, cases, fps):
    output = fresh_output(output)
    report = {"schema_version": "ontokin.reach-source-delivery/0.1", "status": "running",
              "source_kind": "source_component", "provider": "local", "started_at": utc(),
              "command": [sys.executable, str(Path(__file__).resolve()), *sys.argv[1:]],
              "working_directory": str(ROOT), "execution": {"python": sys.version,
                  "executable": sys.executable, "platform": platform.platform()},
              "required_cases": list(SOURCE_CASES), "selected_cases": list(cases), "deliveries": [],
              "release_acceptance": False, "complete_source_delivery_corpus": False,
              "native_validation": "pending", "browser_validation": "pending",
              "full_product_goal_completed": False}
    before = None
    try:
        before = snapshot()
        write_json(output / "inputs-before.json", before)
        report.update(source_commit=before["git"]["commit"], source_tree=before["git"]["tree"])
        frozen = frozen_cases()
        sys.path.insert(0, str(ROOT))
        from ontokin.bundle import load_file_manifest
        from ontokin.construction import compile_construction
        from ontokin.gltf import export_glb
        from ontokin.scene import ExportOptions
        for case_id in cases:
            directory = output / case_id
            directory.mkdir()
            options = settings(case_id, fps=fps)
            row = {"case_id": case_id, "status": "running", "source_files": source_files(case_id),
                   "program_revision": frozen[case_id]["program_revision"], "options": options,
                   "started_at": utc(), "max_operations": 100000}
            compiler = bundle = None
            started = time.monotonic()
            try:
                manifest_path = ROOT / row["source_files"]
                row["source_manifest"] = descriptor(manifest_path, relative_to=ROOT)
                bundle = load_file_manifest(manifest_path)
                require(bundle.program_revision == row["program_revision"], "Source differs from the frozen case")
                compiler = compile_construction(bundle, level="constructed")
                result = export_glb(compiler.model, options=ExportOptions(**{**options, "end": Fraction(options["end"])}),
                                    target_contract="ontokin.glb/0.6", work=compiler.reach_work)
                require(result.report["validation"]["status"] == "passed", "Supplied-byte validation did not pass")
                require(compiler.budget.operations <= 100000 and compiler.reach_work.max_operations == 100000,
                        "The source/export request exceeded or changed its operation allowance")
                with (directory / "scene.glb").open("xb") as stream:
                    stream.write(result.data)
                write_json(directory / "export-report.json", result.report)
                row.update(status="passed", artifact=descriptor(directory / "scene.glb", relative_to=output),
                           export_report=descriptor(directory / "export-report.json", relative_to=output),
                           source_units=[{"source_id": unit.source_id, "bytes": len(unit.raw), "sha256": sha(unit.raw)}
                                         for unit in bundle.units])
            except Exception as error:
                row.update(status="failed", failure={"type": type(error).__name__, "message": str(error)},
                           traceback=traceback.format_exc())
                if hasattr(error, "diagnostic") and bundle is not None:
                    source_id = getattr(error.diagnostic.node, "source_id", "entry")
                    row["diagnostic"] = error.diagnostic.to_dict(bundle.sources.get(source_id, bundle.entry.to_source()))
                if (directory / "scene.glb").exists():
                    row["unclaimed_partial_artifact"] = descriptor(directory / "scene.glb", relative_to=output)
            row.update(finished_at=utc(), elapsed_seconds=time.monotonic() - started)
            if compiler is not None:
                row.update(operations=compiler.budget.operations, work=compiler.reach_work.record())
            write_json(directory / "request-result.json", row)
            report["deliveries"].append(row)
            print(f"{case_id}: {row['status']} ({row.get('operations', 'no compiler')} operations)", flush=True)
        report["status"] = "passed" if all(row["status"] == "passed" for row in report["deliveries"]) else "failed"
    except Exception as error:
        report.update(status="failed", failure={"type": type(error).__name__, "message": str(error)},
                      traceback=traceback.format_exc())
    finish_inputs(output, before, report)
    report["complete_source_delivery_corpus"] = report["status"] == "passed" and set(cases) == set(SOURCE_CASES)
    report["finished_at"] = utc()
    write_json(output / "report.json", report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--case", action="append", default=[])
    parser.add_argument("--fps", type=float, default=1)
    args = parser.parse_args(argv)
    require(0 < args.fps <= 10000, "Requested fps must be finite, positive and at most 10000")
    report = build(args.output_dir, selected_cases("source_component", args.case), args.fps)
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
