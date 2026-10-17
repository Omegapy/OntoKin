"""Command-line source checking and deterministic headless evaluation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
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


def capabilities() -> dict:
    return {
        "implementation": "ontokin-reference", "version": __version__,
        "language_version": "0.1", "profile": "core-0.1",
        "operations": ["check", "evaluate", "conformance", "capabilities"],
        "output_levels": ["represented", "constructed", "evaluated"],
        "source_features": ["classes", "single_inheritance", "pure_functions_and_methods",
                            "typed_quantities", "independent_parts", "sites", "follow",
                            "fixed_hinge_slider_grip", "move_spin_tween", "ordered_events"],
        "physics": "constant uniform gravity and contact-free homogeneous solid spheres",
        "runtime_dependencies": [],
        "numeric_contract": "exact canonical source arithmetic and event clock; binary64 analytical spatial calculations",
        "conformance_scope": "published source cases and bounded behavioral checks; not universal core certification",
        "unsupported": ["contact_and_collision_response", "dynamic_articulated_joints", "closed_mechanical_loops",
                        "general_rigid_body_dynamics", "rendering", "external_delivery", "persistent_agent_editing_service"],
        "limitations": ["General correctly rounded transcendental functions are not certified.",
                        "Exact represented rotations are approximated in binary64 spatial calculations.",
                        "Whole-interval range proofs for arbitrary rotating chains remain future work."],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ontokin", description="OntoKin core-0.1 headless reference prototype")
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
    suite = commands.add_parser("conformance", help="Execute the published source cases and expected observations")
    suite.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURES)
    suite.add_argument("--output", type=Path, help="Write the complete JSON report to this path")
    args = parser.parse_args(argv)
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
    requested = args.level if args.command == "check" else "evaluated"
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
        if requested == "delivered":
            raise OntoKinError("OKL-E-CAPABILITY-UNSUPPORTED", "The reference prototype has no external delivery operation.",
                               ast, category="unsupported", phase="support", blocks=["delivered"])
        warnings = [d.to_dict(source) for d in model.diagnostics]
        if args.command == "check":
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
