#!/usr/bin/env python3
"""Run original reach recording requests with an explicit partial-checkout audit.

This diagnostic does not replace the complete stock source-delivery harness.
It verifies every materialized tracked input and records every omitted path.
The product request is the unchanged frozen compile/export sequence. No runtime
method, budget, fixture, callback, or failed continuation is replaced here.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.reach_delivery_inventory import (ROOT, descriptor, fresh_output,
    frozen_cases, read_bounded, require, settings, sha, source_files, utc, write_json)

SCHEMA = "ontokin.reach-recording-diagnostic/0.1"


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def input_snapshot():
    """Bind materialized bytes to HEAD; missing tracked files remain missing."""
    commit = git("rev-parse", "HEAD").decode().strip()
    tree = git("rev-parse", "HEAD^{tree}").decode().strip()
    status = git("status", "--porcelain=v1", "--untracked-files=all").decode()
    require(not status, "Publish or commit the diagnostic before execution")
    entries = git("ls-tree", "-rz", "--full-tree", "HEAD").split(b"\0")
    present, omitted = [], []
    for row in entries:
        if not row:
            continue
        metadata, encoded = row.split(b"\t", 1)
        mode, kind, expected = metadata.decode().split()
        name = encoded.decode()
        require(kind == "blob" and mode in ("100644", "100755"), "Unsupported tracked input type")
        path = ROOT / name
        require(not any(parent.is_symlink() for parent in (path, *path.parents)), "Symlink input")
        if not path.exists():
            omitted.append({"path": name, "git_blob": expected, "mode": mode})
            continue
        raw = read_bounded(path)
        item = {"path": name, "sha256": sha(raw), "bytes": len(raw)}
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        require(actual == expected, "Materialized bytes differ from HEAD: " + name)
        require(bool(path.stat().st_mode & 0o111) == (mode == "100755"), "Materialized mode differs")
        present.append({**item, "git_blob": expected, "mode": mode})
    expected_runtime = {row.split(b"\t", 1)[1].decode() for row in entries if row and
                        row.split(b"\t", 1)[1].startswith(b"ontokin/")}
    present_names = {item["path"] for item in present}
    require(expected_runtime <= present_names, "Runtime source closure is incomplete")
    require(git("rev-parse", "HEAD").decode().strip() == commit and
            not git("status", "--porcelain=v1", "--untracked-files=all").strip(), "Input identity changed")
    return {"scope": "materialized_tracked_bytes_with_explicit_omissions",
            "git": {"commit": commit, "tree": tree, "status": status,
                    "shallow": git("rev-parse", "--is-shallow-repository").decode().strip() == "true"},
            "files": present, "omitted": omitted, "materialized_count": len(present),
            "tracked_count": len(present) + len(omitted), "complete_checkout": not omitted,
            "complete_stock_harness": False}


def loaded_modules(inputs):
    rows = []
    expected = {row["path"]: row for row in inputs["files"]}
    for name, module in sorted(sys.modules.items()):
        if name == "ontokin" or name.startswith("ontokin.") or name.startswith("tools."):
            value = getattr(module, "__file__", None)
            if value is None:
                continue
            path = Path(value).resolve()
            require(path.is_relative_to(ROOT) and path.suffix == ".py", "Foreign runtime module: " + name)
            item = descriptor(path, relative_to=ROOT)
            require(item["path"] in expected and all(item[key] == expected[item["path"]][key]
                    for key in ("path", "bytes", "sha256")), "Loaded module differs from frozen inputs: " + name)
            rows.append({"module": name, **item})
    return rows


def exception_record(error):
    return {"type": type(error).__name__, "message": str(error),
            "frames": [{"file": str(Path(frame.filename).resolve().relative_to(ROOT))
                        if Path(frame.filename).resolve().is_relative_to(ROOT) else frame.filename,
                        "line": frame.lineno, "function": frame.name}
                       for frame in traceback.extract_tb(error.__traceback__)]}


def exception_graph(error):
    objects, rows, queue = [], [], [error]
    while queue:
        current = queue.pop(0)
        if any(current is prior for prior in objects):
            continue
        require(len(objects) < 16, "Unexpected exception graph size")
        objects.append(current)
        queue.extend(value for value in (current.__cause__, current.__context__) if value is not None)
    for current in objects:
        rows.append({**exception_record(current),
                     "cause": next((i for i, value in enumerate(objects) if value is current.__cause__), None),
                     "context": next((i for i, value in enumerate(objects) if value is current.__context__), None),
                     "suppress_context": current.__suppress_context__})
    return rows


def failed_reader_bytes(error):
    """Inspect existing traceback locals only after the failed request returns."""
    current = error.__traceback__
    candidates = []
    reader_entered = False
    while current is not None:
        frame = current.tb_frame
        if (Path(frame.f_code.co_filename).resolve() == ROOT / "ontokin/gltf.py"
                and frame.f_code.co_name == "validate_export"):
            reader_entered = True
        if (Path(frame.f_code.co_filename).resolve() == ROOT / "ontokin/gltf.py"
                and frame.f_code.co_name == "_export_glb"):
            raw = frame.f_locals.get("data")
            if type(raw) is bytes and len(raw) <= 64 * 1024 * 1024:
                candidates.append(raw)
        current = current.tb_next
    require(not candidates or all(raw == candidates[0] for raw in candidates),
            "Inconsistent retained failed-reader bytes")
    return candidates[0] if reader_entered and candidates else None


def build(output, cases, fps):
    output = fresh_output(output)
    require(set(cases) <= {"P11", "L03"} and len(cases) == len(set(cases)), "Select P11/L03 once")
    require(type(fps) is float and fps == 1.0, "Preserve the original float fps setting")
    report = {"schema_version": SCHEMA, "status": "running", "started_at": utc(),
              "command": [sys.executable, *sys.argv], "working_directory": str(ROOT),
              "execution": {"python": sys.version, "executable": sys.executable,
                            "platform": platform.platform()},
              "scope": "Original requests on exact materialized source; explicit tracked omissions",
              "complete_stock_harness": False, "release_acceptance": False,
              "complete_source_delivery_corpus": False, "full_product_goal_completed": False,
              "deliveries": []}
    try:
        before = input_snapshot()
        write_json(output / "inputs-before.json", before)
    except Exception as caught:
        report.update(status="diagnostic_failed", input_verification_failure=exception_record(caught),
                      inputs_stable=False, finished_at=utc())
        write_json(output / "report.json", report)
        return report
    report.update(source_commit=before["git"]["commit"], source_tree=before["git"]["tree"])
    try:
        from ontokin.bundle import load_file_manifest
        from ontokin.construction import compile_construction
        from ontokin.gltf import export_glb
        from ontokin.scene import ExportOptions
        frozen = frozen_cases()
        for case_id in cases:
            directory = output / case_id
            directory.mkdir()
            options = settings(case_id, fps=fps)
            row = {"case_id": case_id, "status": "running", "source_files": source_files(case_id),
                   "program_revision": frozen[case_id]["program_revision"], "options": options,
                   "started_at": utc(), "max_operations": 100000}
            compiler = bundle = None
            started = time.monotonic()
            error = None
            try:
                manifest = ROOT / row["source_files"]
                row["source_manifest"] = descriptor(manifest, relative_to=ROOT)
                bundle = load_file_manifest(manifest)
                require(bundle.program_revision == row["program_revision"], "Frozen source revision differs")
                compiler = compile_construction(bundle, level="constructed")
                row["after_construction"] = {"shared_operations": compiler.budget.operations,
                                             "work": compiler.reach_work.record()}
                result = export_glb(compiler.model,
                    options=ExportOptions(**{**options, "end": Fraction(options["end"])}),
                    target_contract="ontokin.glb/0.6", work=compiler.reach_work)
                require(result.report["validation"]["status"] == "passed", "Reader validation did not pass")
                require(compiler.budget.operations <= 100000 and compiler.reach_work.max_operations == 100000,
                        "Original operation allowance changed or exceeded")
                (directory / "scene.glb").write_bytes(result.data)
                write_json(directory / "export-report.json", result.report)
                row.update(status="passed", artifact=descriptor(directory / "scene.glb", relative_to=output))
            except Exception as caught:
                error = caught
                row.update(status="failed", failure=exception_record(caught), traceback=traceback.format_exc())
                if hasattr(caught, "diagnostic") and bundle is not None:
                    source_id = getattr(caught.diagnostic.node, "source_id", "entry")
                    row["diagnostic"] = caught.diagnostic.to_dict(bundle.sources.get(source_id, bundle.entry.to_source()))
            row.update(finished_at=utc(), elapsed_seconds=time.monotonic() - started)
            if compiler is not None:
                row.update(operations=compiler.budget.operations, work=compiler.reach_work.record(),
                           budget_limits=dict(compiler.budget.limits),
                           work_limits={name: getattr(compiler.reach_work, name) for name in
                               ("max_operations", "max_elapsed_ms", "max_operand_bits", "max_cache_entries")})
            if bundle is not None:
                row["source_units"] = [{"source_id": unit.source_id, "bytes": len(unit.raw), "sha256": sha(unit.raw)}
                                       for unit in bundle.units]
            # Product execution is over. Serialization and import inspection do not
            # affect its work, callbacks, exception choice or elapsed-time checks.
            if error is not None:
                row["exception_graph"] = exception_graph(error)
                raw = failed_reader_bytes(error)
                if raw is not None:
                    (directory / "unvalidated-reader-input.glb").write_bytes(raw)
                    row["unvalidated_reader_input"] = descriptor(directory / "unvalidated-reader-input.glb", relative_to=output)
                    row["accepted_artifact"] = False
            row["loaded_modules"] = loaded_modules(before)
            write_json(directory / "request-result.json", row)
            report["deliveries"].append(row)
            print(f"{case_id}: {row['status']} ({row.get('operations')} shared operations)", flush=True)
        report["status"] = "passed" if all(row["status"] == "passed" for row in report["deliveries"]) else "failed"
    except Exception as caught:
        report.update(status="diagnostic_failed", diagnostic_failure=exception_record(caught), traceback=traceback.format_exc())
    finally:
        try:
            after = input_snapshot()
            write_json(output / "inputs-after.json", after)
            report["inputs_stable"] = before == after
            require(report["inputs_stable"], "Materialized inputs or Git identity changed during request")
        except Exception as caught:
            report.update(status="diagnostic_failed", inputs_stable=False,
                          input_verification_failure=exception_record(caught))
    report["finished_at"] = utc()
    write_json(output / "report.json", report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--case", required=True, choices=("P11", "L03"))
    args = parser.parse_args(argv)
    return 0 if build(args.output_dir, (args.case,), 1.0)["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
