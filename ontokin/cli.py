"""Check OntoKin source, evaluate its motion, and export verified animation."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import uuid

from . import __version__
from .diagnostics import Diagnostic, OntoKinError, Source
from .fixtures import DEFAULT_FIXTURES
from .syntax import MAX_SOURCE_BYTES, Node, parse


def _print(value: dict) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False))


def _read_source(path: Path) -> Source:
    with path.open("rb") as stream:
        raw = stream.read(MAX_SOURCE_BYTES + 1)
    return Source(raw.decode("utf-8", errors="replace"), str(path), raw=raw)


def _same_path(first: Path, second: Path) -> bool:
    """Include symlinks and existing hard links when protecting source files."""
    return first.resolve() == second.resolve() or (
        first.exists() and second.exists() and first.samefile(second)
    )


def _export_paths(source: Path, output: Path, report: Path | None) -> tuple[Path, Path]:
    report = report if report is not None else output.with_suffix(".export.json")
    if output.suffix.lower() != ".glb" or report.suffix.lower() != ".json":
        raise OntoKinError(
            "OKL-E-CAPABILITY-UNSUPPORTED", "Export requires a .glb output and a .json report.",
            category="unsupported", phase="support", blocks=["delivered"],
            details={"target_contract": "ontokin.glb/0.1", "export_code": "OKE-E-OUTPUT-PATH"},
            repair="Choose separate .glb and .json output paths.",
        )
    if any(_same_path(a, b) for a, b in ((source, output), (source, report), (output, report))):
        raise OntoKinError(
            "OKL-E-CAPABILITY-UNSUPPORTED", "Export destinations must be separate from each other and the source.",
            category="unsupported", phase="support", blocks=["delivered"],
            details={"target_contract": "ontokin.glb/0.1", "export_code": "OKE-E-OUTPUT-PATH"},
            repair="Choose new output paths that do not alias the .ok source.",
        )
    return output, report


def _write_export(output: Path, data: bytes, report_path: Path, report: dict) -> None:
    """Stage complete files before replacing either destination.

    Each replacement is atomic. The report's artifact hash identifies its exact
    GLB; two paths in different directories cannot form one atomic transaction.
    """
    staged: list[tuple[Path, Path]] = []
    report_bytes = (json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    try:
        for destination, content in ((output, data), (report_path, report_bytes)):
            destination.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=".ontokin-", suffix=".tmp", delete=False) as stream:
                temporary = Path(stream.name)
                staged.append((temporary, destination))
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
        for temporary, destination in staged:
            os.replace(temporary, destination)
    finally:
        for temporary, _ in staged:
            temporary.unlink(missing_ok=True)


def capabilities() -> dict:
    return {
        "implementation": "ontokin-reference", "version": __version__,
        "language_version": "0.1", "profile": "core-0.1",
        "operations": ["check", "evaluate", "export", "agent", "conformance", "capabilities"],
        "output_levels": ["represented", "constructed", "evaluated"],
        "source_features": ["classes", "single_inheritance", "pure_functions_and_methods",
                            "typed_quantities", "independent_parts", "sites", "follow",
                            "fixed_hinge_slider_grip", "move_spin_tween", "ordered_events"],
        "physics": "constant uniform gravity and contact-free homogeneous solid spheres",
        "runtime_dependencies": [],
        "numeric_contract": "exact canonical source arithmetic and event clock; binary64 analytical spatial calculations",
        "conformance_scope": "published source cases and bounded behavioral checks; not universal core certification",
        "unsupported": ["contact_and_collision_response", "dynamic_articulated_joints", "closed_mechanical_loops",
                        "general_rigid_body_dynamics", "general_external_delivery", "distributed_agent_service"],
        "agent_interface": {
            "schema_version": "ontokin.agent/0.1", "storage_schema": "ontokin.agent-store/0.1",
            "transport": "local Python AgentService and UTF-8 JSONL CLI",
            "operations": ["discover", "create", "edit", "validate", "inspect", "evaluate", "reset", "status", "cancel", "export", "artifact"],
            "source_revisions": "immutable SHA-256 of exact UTF-8 bytes; first recorded filename is canonical per project and revision",
            "durability": "local SQLite transactions; source acceptance, run/artifact changes and terminal request result commit together",
            "retry": "project-scoped canonical request identity; exact retained results or nonreplayable tombstones",
            "engine_binding": "runs and queued work pin the implementation version and Python source digest",
            "limits": {"max_source_bytes": 2097152, "max_request_bytes": 4194304, "max_objects": 1000,
                       "max_operations": 100000, "max_result_items": 1000, "max_elapsed_ms": 30000,
                       "artifact_chunk_bytes": 65536},
            "cancellation": "cooperative checkpoints and a final atomic commit fence; export kernels may delay observation",
            "retention": "explicit result expiry preserves identity/digest tombstones; no automatic source/run/artifact expiry",
        },
        "export_targets": {
            "ontokin.glb/0.1": {
                "format": "glTF 2.0 binary (.glb)",
                "geometry": ["empty", "box", "sphere"],
                "animation": "evaluated world transforms baked to float32 LINEAR tracks",
                "source_of_truth": ".ok source; exported playback does not execute OntoKin physics",
                "default_fps": 60,
                "default_tolerances": {"position_m": 0.001, "rotation_rad": 0.001, "time_s": 0.000001},
                "validation": "encoded keyframes, event boundaries, and finite interior samples",
            }
        },
        "limitations": ["General correctly rounded transcendental functions are not certified.",
                        "Exact represented rotations are approximated in binary64 spatial calculations.",
                        "Whole-interval range proofs for arbitrary rotating chains remain future work.",
                        "GLB export uses tessellated spheres and finite animation samples; it is not an all-time error proof.",
                        "Physics, live joint constraints, and editable source structure do not execute in a GLB viewer."],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ontokin", description="OntoKin core-0.1 reference implementation and animation exporter")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("capabilities", help="Show implemented operations and physical/numeric limits as JSON")
    check = commands.add_parser("check", help="Validate a source file; default also checks its complete timeline")
    check.add_argument("file", type=Path)
    check.add_argument("--level", choices=("represented", "constructed", "evaluated", "delivered"), default="evaluated")
    evaluate_parser = commands.add_parser("evaluate", help="Calculate object state at requested exact times")
    evaluate_parser.add_argument("file", type=Path)
    evaluate_parser.add_argument("--times", nargs="+", help="Exact decimal seconds; defaults to zero and the scene endpoint")
    evaluate_parser.add_argument("--side", choices=("before", "after"), default="after")
    evaluate_parser.add_argument("--object", help="Inspect one object's pose and world-measured velocity")
    evaluate_parser.add_argument("--frame", default="world", help="Frame for --object inspection, for example first.frame")
    export_parser = commands.add_parser("export", help="Bake and verify an animation in a self-contained .glb file")
    export_parser.add_argument("file", type=Path)
    export_parser.add_argument("--output", type=Path, required=True, help="Destination .glb file")
    export_parser.add_argument("--report", type=Path, help="JSON evidence sidecar; defaults to OUTPUT.export.json")
    export_parser.add_argument("--fps", type=float, default=60, help="Minimum sample rate; default 60 frames per second")
    export_parser.add_argument("--end", help="Exact decimal end time, from zero through the authored scene duration")
    export_parser.add_argument("--position-tolerance", type=float, default=0.001, metavar="METRES")
    export_parser.add_argument("--rotation-tolerance", type=float, default=0.001, metavar="RADIANS")
    export_parser.add_argument("--time-tolerance", type=float, default=0.000001, metavar="SECONDS")
    export_parser.add_argument("--no-helpers", action="store_true", help="Omit the display-only assembly and joint markers")
    suite = commands.add_parser("conformance", help="Execute the published source cases and expected observations")
    suite.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURES)
    suite.add_argument("--output", type=Path, help="Write the complete JSON report to this path")
    agent = commands.add_parser("agent", help="Serve durable ontokin.agent/0.1 requests as local JSONL")
    agent.add_argument("--store", type=Path, required=True, help="Directory for immutable snapshots and durable request/run state")
    agent.add_argument("--request", type=Path, help="Read one JSON request, emit its receipt, and exit")
    agent.add_argument("--wait", action="store_true", help="Wait for this request's terminal result instead of returning a queued receipt")
    args = parser.parse_args(argv)
    if args.command == "agent":
        from .agent_cli import run
        return run(args)
    if args.command == "capabilities":
        _print(capabilities())
        return 0
    if args.command == "conformance":
        from .conformance import run_conformance
        try:
            report = run_conformance(args.fixtures)
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
                _print({"report": str(args.output), "summary": report["summary"]})
            else:
                _print(report)
            return 0 if report["summary"]["failed"] == 0 else 1
        except (OSError, ValueError) as exc:
            _print({"outcome": "io_or_fixture_error", "message": str(exc)})
            return 1
    try:
        source = _read_source(args.file)
    except OSError as exc:
        _print({"outcome": "io_error", "file": str(args.file), "message": str(exc)})
        return 1
    requested = args.level if args.command == "check" else ("delivered" if args.command == "export" else "evaluated")
    try:
        if len(source.raw) > MAX_SOURCE_BYTES:
            raise OntoKinError("OKL-E-RESOURCE", "Source exceeds the 2 MB reference budget.",
                               category="resource_limit", phase="lexical")
        try:
            text = source.raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise OntoKinError("OKL-E-LEXICAL", "Source is not valid UTF-8.",
                               Node("span", exc.start, exc.end), phase="lexical") from None
        from .validator import validate
        from .evaluator import construct, evaluate, inspect_in_frame, preflight
        ast = parse(text, source.filename)
        # Source errors remain primary even if the requested delivery level is unavailable.
        model = validate(ast, level="evaluated" if requested == "delivered" else requested)
        if requested == "delivered" and args.command == "check":
            raise OntoKinError("OKL-E-CAPABILITY-UNSUPPORTED", "Generic delivered-level checking has no target. Use export for the ontokin.glb/0.1 contract.",
                               ast, category="unsupported", phase="support", blocks=["delivered"])
        warnings = [d.to_dict(source) for d in model.diagnostics]
        if args.command == "export":
            from .gltf import export_glb
            from .scene import ExportOptions
            output, report_path = _export_paths(args.file, args.output, args.report)
            exported = export_glb(
                model,
                options=ExportOptions(fps=args.fps, end=args.end,
                                      position_tolerance_m=args.position_tolerance,
                                      rotation_tolerance_rad=args.rotation_tolerance,
                                      time_tolerance_s=args.time_tolerance,
                                      helpers=not args.no_helpers),
                source_uri=str(args.file), source_sha256=source.revision,
            )
            report = dict(exported.report)
            report.update({"operation": "export", "output": str(output), "report": str(report_path),
                           "source_revision": source.revision, "source_diagnostics": warnings})
            _write_export(output, exported.data, report_path, report)
            _print(report)
        elif args.command == "check":
            result = {"outcome": "valid", "operation": "check", "level": requested,
                      "profile": model.profile, "source_revision": source.revision,
                      "module": model.module_name, "scene": model.scene_name,
                      "objects": len(model.objects), "joints": len(model.joints), "follows": len(model.follows),
                      "actions": len(model.actions), "requested_capabilities": list(model.requested_capabilities),
                      "diagnostics": warnings}
            if requested == "evaluated":
                result["timeline_preflight"] = preflight(model)
            elif requested == "constructed":
                result["initial_state"] = construct(model)["initial_state"]
            _print(result)
        else:
            result = evaluate(model, args.times, side=args.side)
            if args.object:
                result["inspection"] = [inspect_in_frame(s, args.object, args.frame) for s in result["samples"]]
                del result["samples"]
            result.update({"operation": "evaluate", "source_revision": source.revision,
                           "run_id": str(uuid.uuid4()), "diagnostics": warnings})
            _print(result)
        return 0
    except OSError as exc:
        _print({"outcome": "io_error", "file": str(args.file), "message": str(exc)})
        return 1
    except OntoKinError as exc:
        diagnostic = exc.diagnostic.to_dict(source)
        _print({"outcome": diagnostic["category"], "requested_level": requested,
                "source_revision": source.revision, "diagnostics": [diagnostic]})
        return 3 if diagnostic["category"] == "unsupported" else 2
    except RecursionError:
        diagnostic = Diagnostic("OKL-E-RESOURCE", "Reference expansion or evaluation nesting budget exceeded.",
                                category="resource_limit", phase="elaboration").to_dict(source)
        _print({"outcome": "resource_limit", "source_revision": source.revision, "diagnostics": [diagnostic]})
        return 2


if __name__ == "__main__":
    sys.exit(main())
