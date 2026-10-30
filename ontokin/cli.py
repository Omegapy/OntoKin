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


def _export_paths(source: Path, output: Path, report: Path | None, *,
                  target_contract: str = "ontokin.glb/0.1",
                  protected_sources: tuple[Path, ...] = ()) -> tuple[Path, Path]:
    report = report if report is not None else output.with_suffix(".export.json")
    if output.suffix.lower() != ".glb" or report.suffix.lower() != ".json":
        raise OntoKinError(
            "OKL-E-CAPABILITY-UNSUPPORTED", "Export requires a .glb output and a .json report.",
            category="unsupported", phase="support", blocks=["delivered"],
            details={"target_contract": target_contract, "export_code": "OKE-E-OUTPUT-PATH"},
            repair="Choose separate .glb and .json output paths.",
        )
    pairs = [(path, destination) for path in (source, *protected_sources)
             for destination in (output, report)] + [(output, report)]
    if any(_same_path(a, b) for a, b in pairs):
        raise OntoKinError(
            "OKL-E-CAPABILITY-UNSUPPORTED", "Export destinations must be separate from each other and the source.",
            category="unsupported", phase="support", blocks=["delivered"],
            details={"target_contract": target_contract, "export_code": "OKE-E-OUTPUT-PATH"},
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


def _write_export_transaction(output: Path, data: bytes, report_path: Path, report: dict) -> None:
    """Publish a new-profile pair, restoring both destinations on a handled error.

The computation has already completed its shared allowance. Persistence is a
transport step. A process crash between two filesystem replacements still needs
the report's exact artifact hash to detect an incomplete pair.
"""
    from .json_limits import JSONLimitError, MAX_JSON_BYTES, measure_json
    try:
        measure_json(report)
        report_bytes = (json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
        if len(report_bytes) > MAX_JSON_BYTES:
            raise JSONLimitError("encoded_json_bytes", MAX_JSON_BYTES, len(report_bytes))
    except JSONLimitError as error:
        raise OntoKinError("OKL-E-RESOURCE", "The export receipt exceeds its output limit.",
                           category="resource_limit", phase="support", details=error.details) from error
    payloads = ((output, data), (report_path, report_bytes))
    staged = []
    backups = []
    published = []
    complete = False
    try:
        for destination, content in payloads:
            destination.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=".ontokin-",
                                             suffix=".tmp", delete=False) as stream:
                temporary = Path(stream.name)
                staged.append((temporary, destination))
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
        for _, destination in staged:
            if destination.exists() or destination.is_symlink():
                with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=".ontokin-",
                                                 suffix=".backup", delete=False) as stream:
                    backup = Path(stream.name)
                backups.append((backup, destination, False))
                os.replace(destination, backup)
                backups[-1] = (backup, destination, True)
        for temporary, destination in staged:
            os.replace(temporary, destination)
            published.append(destination)
        complete = True
    except BaseException as original_error:
        # Restore an old file directly over a newly published one. Unlinking
        # first is unnecessary and can prevent every later restoration.
        original_destinations = {destination for _, destination, moved in backups if moved}
        recovery_backups = []
        for index in reversed(range(len(backups))):
            backup, destination, moved = backups[index]
            if moved:
                try:
                    os.replace(backup, destination)
                    backups[index] = (backup, destination, False)
                except OSError:
                    recovery_backups.append(str(backup))
        unremoved_outputs = []
        for destination in reversed(published):
            if destination not in original_destinations:
                try:
                    destination.unlink(missing_ok=True)
                except OSError:
                    unremoved_outputs.append(str(destination))
        if recovery_backups or unremoved_outputs:
            details = []
            if recovery_backups:
                details.append("original files remain in recovery backups: " + ", ".join(recovery_backups))
            if unremoved_outputs:
                details.append("new outputs could not be removed: " + ", ".join(unremoved_outputs))
            raise OSError("Export failed; " + "; ".join(details)) from original_error
        raise
    finally:
        for temporary, _ in staged:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass  # A leftover staging file must not suppress recovery details.
        for backup, _, moved in backups:
            if complete or not moved:
                try:
                    backup.unlink(missing_ok=True)
                except OSError:
                    pass  # The delivered pair or the restored originals are intact.


def capabilities(*, host_policy=None) -> dict:
    from .execution_budget import HostPolicy, DEFAULT_LIMITS, MAX_LIMIT
    policy = HostPolicy() if host_policy is None else host_policy
    if not isinstance(policy, HostPolicy):
        raise TypeError("host_policy must be supplied as a HostPolicy by the embedding host.")
    return {
        "implementation": "ontokin-reference", "version": __version__,
        "language_version": "0.1", "profile": "core-0.1",
        "default_file_commands": "check/evaluate/export FILE.ok use language 0.1 and core-0.1",
        "construction_interface": {
            "language_version": "0.2", "profile": "construction-0.1",
            "schema_version": "ontokin.agent/0.2", "bundle_schema": "ontokin.bundle/0.1",
            "file_manifest_schema": "ontokin.files/0.1", "storage_schema": "ontokin.program-agent-store/0.1",
            "transport": "local Python ProgramAgentService and agent --protocol ontokin.agent/0.2 JSONL CLI",
            "source_features": ["offline_exact_pinned_imports", "module_qualified_nominal_types",
                                "public_private_definitions", "immutable_flat_keyed_values",
                                "declarative_keyed_parts", "stable_generated_identity", "per_key_public_overrides"],
            "program_revisions": "SHA-256 of the canonical complete exact-source manifest before parsing or linking",
            "edits": "atomic source-scoped UTF-8 patches and dependency add/replace/remove against one expected program revision",
            "limits": {"max_dependency_modules": 16, "max_import_depth": 8, "max_source_bytes": 2000000,
                       "max_tokens": 200000, "max_keyed_entries": 256, "max_objects": 1000,
                       "max_ownership_depth": 64, "max_operations": 100000, "max_value_entries": 100000,
                       "max_request_bytes": 4194304, "max_response_bytes": 4194304, "max_json_entries": 100000,
                       "max_json_depth": 128, "max_elapsed_ms": 30000, "max_element_id_segments": 256},
            "conformance_command": "python -m ontokin.construction_conformance --output REPORT.json --external-evidence MANIFEST.json",
            "external_gate": "C20 requires identified successful source/workflow/GLB/independent-loader/browser evidence and capture review",
            "limitations": ["No network dependency resolution or version ranges.",
                            "Generated ownership does not supply attachment, matter, or motion authority.",
                            "Bounded pure construction; no mutable collections, runtime generation, or new physics.",
                            "Agent 0.1 and 0.2 use separate stores; no implicit protocol or snapshot migration."],
        },
        "surface_interface": {
            "language_version": "0.3", "profile": "surface-0.1",
            "delivery_contract": "ontokin.glb/0.3",
            "source_features": ["typed_keyed_loft_sections", "parameterized_exterior_surfaces",
                                "regional_linear_pbr_materials", "rigid_local_visual_placement"],
            "single_source_command": "export SOURCE.ok --target ontokin.glb/0.3 --output MODEL.glb",
            "pinned_bundle_command": "export PROGRAM.files.json --bundle --target ontokin.glb/0.3 --output MODEL.glb",
            "agent_contract": "ontokin.agent/0.3",
            "storage_schema": "ontokin.surface-program-agent-store/0.1",
            "transport": "ProgramAgentService(store, protocol='ontokin.agent/0.3') and agent --protocol ontokin.agent/0.3 JSONL CLI",
            "operations": ["discover", "create", "edit", "validate", "inspect", "surface.mesh_page",
                           "evaluate", "reset", "status", "cancel", "export", "artifact"],
            "mesh_paging": {"count_unit": "complete triangles", "max_count": 256,
                            "coordinates": "carrier-local meters after one authored visual placement",
                            "identity": "accepted immutable program, occurrence, region, geometry digest and signed cursor"},
            "limits": {"max_sections": 64, "max_materials": 16, "max_facets": 64,
                       "max_mesh_vertices_per_request": 250000, "max_glb_bytes": 67108864},
            "limitations": ["Flat-shaded rigid lofts; no skin deformation, textures or automatic physical matter.",
                            "Agent 0.3 uses a separate store; the request schema does not select or migrate a service.",
                            "Finite source/workflow evidence does not establish the full GOAL; M01-M12 status is tracked separately."],
        },
        "impulse_interface": {
            "language_version": "0.4", "profile": "impulse-0.1",
            "agent_contract": "ontokin.agent/0.4", "delivery_contract": "ontokin.glb/0.4",
            "storage_schema": "ontokin.impulse-program-agent-store/0.1",
            "source_event": "impulse OBJECT using WORLD_VECTOR_N_S at TARGET_LOCAL_POINT;",
            "physical_model": "free homogeneous sphere with own mass and isotropic inertia",
            "events": "ordered atomic instantaneous momentum updates; release uses saved incoming state",
            "inspection": "bounded latest impulse boundary records with source spans, momentum and spin changes",
            "transport": "ProgramAgentService(store, protocol='ontokin.agent/0.4') and agent --protocol ontokin.agent/0.4 JSONL CLI",
            "pinned_bundle_command": "export PROGRAM.files.json --bundle --target ontokin.glb/0.4 --output MODEL.glb",
            "geometry_capability": "inherited surface-0.1 geometry and material region inspection",
            "limitations": ["Only source-authored instantaneous impulses; no host apply_impulse operation.",
                            "No contacts, finite forces, continuous torques, actuators or nonspherical dynamics.",
                            "Recorded GLB animation does not execute impulses or live physics in the destination."],
        },
        "force_interface": {
            "language_version": "0.5", "profile": "force-0.1",
            "agent_contract": "ontokin.agent/0.5", "delivery_contract": "ontokin.glb/0.5",
            "storage_schema": "ontokin.force-program-agent-store/0.1",
            "source_event": 'force OBJECT @ "KEY" using WORLD_VECTOR_N for DURATION;',
            "physical_model": "finite constant world center-of-mass forces on free homogeneous spheres",
            "events": "exact activation/completion clocks and additive overlaps at atomic source boundaries",
            "inspection": "complete active and latest source-bound force records with world force and acceleration",
            "transport": "ProgramAgentService(store, protocol='ontokin.agent/0.5') and agent --protocol ontokin.agent/0.5 JSONL CLI",
            "single_source_command": "export SOURCE.ok --target ontokin.glb/0.5 --output MODEL.glb",
            "pinned_bundle_command": "export PROGRAM.files.json --bundle --target ontokin.glb/0.5 --output MODEL.glb",
            "recording_interval": "--end and Agent options.end evaluate only the requested prefix; omitted end uses scene duration",
            "limitations": ["Only source-authored finite constant world forces at the center of mass; no host force mutation.",
                            "No continuous torque, contacts, controllers or general rigid-body dynamics.",
                            "Recorded GLB animation does not execute forces or live physics in the destination."],
        },
        "reach_interface": {
            "language_version": "0.6", "profile": "planar-reach-0.1",
            "agent_contract": "ontokin.agent/0.6", "delivery_contract": "ontokin.glb/0.6",
            "storage_schema": "ontokin.planar-reach-program-agent-store/0.1",
            "source_action": "reach_planar(shoulder, elbow, tip, target, duration, branch)",
            "motion_model": "two prescribed planar hinge coordinates with atomic coupled ownership",
            "inspection": "complete source-bound lifecycle, physical coordinates/rates, goal and latched terminal result",
            "transport": "ProgramAgentService(store, protocol='ontokin.agent/0.6') and agent --protocol ontokin.agent/0.6 JSONL CLI",
            "pinned_bundle_command": "export PROGRAM.files.json --bundle --target ontokin.glb/0.6 --output MODEL.glb",
            "limits": {"bound_chains": 32, "named_actions": 128, "active_reaches": 32,
                       "goal_residual_m": 1e-9, "max_interval_certificates": 100000},
            "limitations": ["Finite planar prescribed motion; no torque actuator, obstacle avoidance or contact solver.",
                            "Recorded playback is bound to the identified destination numerical method.",
                            "Experimental development implementation; planar-reach-0.1 release acceptance is incomplete."],
        },
        "execution_budget_interface": {
            "status": "experimental_source_cli_increment",
            "language_version": "0.7", "profile": "planar-reach-budget-0.1",
            "delivery_contract": "ontokin.glb/0.7", "agent_contract": None,
            "export_targets": {
                "ontokin.glb/0.7": {
                    "format": "glTF 2.0 binary (.glb)", "profile": "planar-reach-budget-0.1",
                    "selection": "Explicit source 0.7 and host-authorized source/CLI execution",
                    "validation": "Inherited geometry, physical history and independent supplied-byte checks under the same remaining allowance",
                    "limitations": "Experimental source/CLI increment; no Agent/0.7 lifecycle or live destination physics",
                },
            },
            "defaults": dict(DEFAULT_LIMITS), "host_ceilings": policy.ceilings,
            "policy_id": policy.policy_id, "max_representable_limit": MAX_LIMIT,
            "source_fields": ["max_operations", "max_elapsed"],
            "caller_caps": ["max_operations", "max_elapsed_ms"],
            "host_configuration": "Trusted Python HostPolicy passed to cli.main(host_policy=...) or execute_budgeted_export(policy=...)",
            "single_source_command": "export SOURCE.ok --target ontokin.glb/0.7 --output MODEL.glb",
            "accounting": "One original deadline and shared operation allowance through header, construction, evaluation, recording, export and independent readback",
            "limitations": ["Agent/0.7 is unavailable.",
                            "Computation timeout does not change scene.duration or recording options.",
                            "Host policy is configured by the embedding host; caller flags only reduce source requests.",
                            "Other source, object, numerical, cache and output limits remain in force."],
        },
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
            },
            "ontokin.glb/0.2": {
                "format": "glTF 2.0 binary (.glb)", "profile": "construction-0.1",
                "geometry": ["empty", "box", "sphere"],
                "animation": "same bounded world-pose baking with complete program, source-unit and occurrence provenance",
                "source_of_truth": "the complete exact pinned .ok source bundle",
                "selection": "explicit program-agent export destination; core-only models retain ontokin.glb/0.1",
                "default_fps": 60,
                "default_tolerances": {"position_m": 0.001, "rotation_rad": 0.001, "time_s": 0.000001},
            },
            "ontokin.glb/0.3": {
                "format": "glTF 2.0 binary (.glb)", "profile": "surface-0.1",
                "geometry": ["empty", "box", "sphere", "loft", "placed"],
                "materials": "one indexed primitive per used source region with linear RGBA, metallic and roughness",
                "animation": "source-evaluated rigid world poses; local visual placement baked once",
                "source_of_truth": "the complete exact pinned .ok source bundle",
                "selection": "explicit --target ontokin.glb/0.3, Agent/0.3 destination, or Python export_glb target_contract",
                "surface_vertex_tolerance_m": 0.00001,
                "validation": "decoded source topology, winding, normals, PBR, provenance and sampled animation",
                "cancellation": "cooperative compiler, mesh, serialization and decoded-validation callbacks",
            },
            "ontokin.glb/0.4": {
                "format": "glTF 2.0 binary (.glb)", "profile": "impulse-0.1",
                "geometry": ["empty", "box", "sphere", "loft", "placed"],
                "materials": "inherited native PBR regions and one local visual placement",
                "animation": "source-evaluated piecewise free-sphere motion after instantaneous impulses",
                "source_of_truth": "the complete exact pinned .ok source bundle",
                "selection": "explicit --target ontokin.glb/0.4 or Agent/0.4 destination",
                "impulse_metadata": "complete latest per-object source impulse records at each boundary",
                "sampling": "conservative authored-impulse spin bound plus every exact source boundary",
                "validation": "decoded native geometry, materials, source influence metadata and world animation",
                "limitations": "recorded rigid playback; no destination impulse engine or contacts",
            },
            "ontokin.glb/0.5": {
                "format": "glTF 2.0 binary (.glb)", "profile": "force-0.1",
                "geometry": ["empty", "box", "sphere", "loft", "placed"],
                "materials": "inherited native PBR regions and one local visual placement",
                "animation": "source-evaluated piecewise quadratic translation and inherited rigid angular motion",
                "source_of_truth": "the complete exact pinned .ok source bundle",
                "selection": "explicit --target ontokin.glb/0.5 or Agent/0.5 destination",
                "force_metadata": "complete source force and impulse state at every recorded exact boundary",
                "sampling": "requested-prefix acceleration and angular bounds plus every exact in-prefix boundary",
                "validation": "decoded source geometry, materials, influence provenance, float32 tracks and intermediate motion",
                "limitations": "bounded recorded rigid playback; no destination force engine, contacts or live physics",
            },
            "ontokin.glb/0.6": {
                "format": "glTF 2.0 binary (.glb)", "profile": "planar-reach-0.1",
                "geometry": ["empty", "box", "sphere", "loft", "placed"],
                "source_of_truth": "the complete exact pinned .ok source bundle",
                "selection": "explicit --target ontokin.glb/0.6 or Agent/0.6 destination",
                "clock_conversion": "binary32_rne_ties_to_even_from_exact_rational",
                "histories": "complete before/after joints, actions, authorities, impulses, forces, reaches and incoming releases",
                "validation": "independent supplied-byte clocks, complete geometry/PBR, source phases and continuous error certificates",
                "limitations": "experimental development implementation; planar-reach-0.1 release acceptance is incomplete; bounded recorded motion with explicit destination numerical identity and no embedded live solver",
            },
        },
        "limitations": ["General correctly rounded transcendental functions are not certified.",
                        "Exact represented rotations are approximated in binary64 spatial calculations.",
                        "Whole-interval range proofs for arbitrary rotating chains remain future work.",
                        "GLB export uses tessellated spheres and finite animation samples; it is not an all-time error proof.",
                        "Physics, live joint constraints, and editable source structure do not execute in a GLB viewer."],
    }


def _program_export(args, *, host_policy=None) -> int:
    """Export explicitly selected newer profiles from exact offline source files."""
    from .bundle import BundleError, MAX_MANIFEST_BYTES, load_bundle, load_file_manifest
    from .construction import compile_construction
    from .gltf import export_glb
    from .program_diagnostics import diagnostic_dict
    from .scene import ExportOptions
    program = None
    try:
        if args.target == "ontokin.glb/0.1":
            raise BundleError("OKA-E-REQUEST", "A program bundle requires explicit GLB/0.2 through GLB/0.6 delivery.")
        protected = []
        if args.bundle:
            manifest_path = args.file.resolve(strict=True)
            with manifest_path.open("rb") as stream:
                manifest_bytes = stream.read(MAX_MANIFEST_BYTES + 1)
            if len(manifest_bytes) > MAX_MANIFEST_BYTES:
                raise BundleError("OKA-E-RESOURCE", "The file manifest exceeds its byte budget.")
            program = load_file_manifest(manifest_path)
            if manifest_path.read_bytes() != manifest_bytes:
                raise BundleError("OKA-E-REQUEST", "The file manifest changed while its source snapshot was loaded.")
            manifest = json.loads(manifest_bytes)
            protected = [manifest_path.parent / descriptor["path"]
                         for descriptor in [manifest["entry"], *manifest["modules"]]]
        else:
            source = _read_source(args.file)
            try:
                source_text = source.raw.decode("utf-8", errors="strict")
            except UnicodeDecodeError:
                raise BundleError("OKA-E-REQUEST", "The source file must contain valid UTF-8.") from None
            program = load_bundle({"schema_version": "ontokin.bundle/0.1",
                "entry": {"filename": str(args.file), "source": source_text}, "modules": []})
        if args.target == "ontokin.glb/0.7":
            from .budget_runtime import execute_budgeted_export
            output, report_path = _export_paths(args.file, args.output, args.report,
                target_contract=args.target, protected_sources=tuple(protected))
            caps = {name: value for name, value in (
                ("max_operations", args.max_operations), ("max_elapsed_ms", args.max_elapsed_ms))
                if value is not None}
            result = execute_budgeted_export(program, policy=host_policy, caller_caps=caps,
                options=ExportOptions(fps=args.fps, end=args.end,
                    position_tolerance_m=args.position_tolerance,
                    rotation_tolerance_rad=args.rotation_tolerance,
                    time_tolerance_s=args.time_tolerance, helpers=not args.no_helpers))
            report = dict(result.report)
            if result.data is None:
                _print(report)
                return 3 if report["outcome"] == "unsupported" else 2
            report.update(operation="export", output=str(output), report=str(report_path))
            _write_export_transaction(output, result.data, report_path, report)
            _print(report)
            return 0
        if args.max_operations is not None or args.max_elapsed_ms is not None:
            raise BundleError("OKA-E-REQUEST", "Execution caller caps require explicit GLB/0.7.")
        compiler = compile_construction(program, level="evaluated")
        output, report_path = _export_paths(args.file, args.output, args.report,
            target_contract=args.target, protected_sources=tuple(protected))
        result = export_glb(compiler.model, target_contract=args.target,
            source_uri=program.entry.filename, source_sha256=program.entry.revision,
            work=compiler.reach_work if compiler.model.profile == "planar-reach-0.1" else None,
            options=ExportOptions(fps=args.fps, end=args.end,
                position_tolerance_m=args.position_tolerance,
                rotation_tolerance_rad=args.rotation_tolerance,
                time_tolerance_s=args.time_tolerance, helpers=not args.no_helpers))
        report = dict(result.report)
        report.update(operation="export", output=str(output), report=str(report_path),
            source_revision=program.entry.revision, program_revision=program.program_revision,
            source_diagnostics=[diagnostic_dict(d, program) for d in compiler.model.diagnostics])
        _write_export(output, result.data, report_path, report)
        _print(report)
        return 0
    except BundleError as error:
        _print({"outcome": "resource_limit" if error.code == "OKA-E-RESOURCE" else "invalid_request",
                "requested_level": "delivered", "target_contract": args.target,
                "error": error.to_dict()})
        return 2
    except OntoKinError as error:
        diagnostic = diagnostic_dict(error.diagnostic, program)
        diagnostic["details"]["target_contract"] = args.target
        _print({"outcome": diagnostic["category"], "requested_level": "delivered",
                "program_revision": program.program_revision, "diagnostics": [diagnostic]})
        return 3 if diagnostic["category"] == "unsupported" else 2
    except OSError as error:
        _print({"outcome": "io_error", "file": str(args.file), "message": str(error)})
        return 1
    except RecursionError:
        _print({"outcome": "resource_limit", "requested_level": "delivered",
                "message": "Source construction or export nesting budget exceeded."})
        return 2


def main(argv: list[str] | None = None, *, host_policy=None) -> int:
    """Run the CLI; only a trusted launcher supplies an increased host policy."""
    from .execution_budget import HostPolicy
    if host_policy is not None and not isinstance(host_policy, HostPolicy):
        raise TypeError("host_policy must be supplied as a HostPolicy by the embedding host.")
    parser = argparse.ArgumentParser(prog="ontokin", description="OntoKin reference evaluator, animation exporter, and versioned agent interfaces")
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
    export_parser.add_argument("--target", choices=["ontokin.glb/0.1", "ontokin.glb/0.2", "ontokin.glb/0.3", "ontokin.glb/0.4", "ontokin.glb/0.5", "ontokin.glb/0.6", "ontokin.glb/0.7"],
                               default="ontokin.glb/0.1", help="Explicit delivery profile; old source is never migrated")
    export_parser.add_argument("--bundle", action="store_true",
                               help="Read FILE as an ontokin.files/0.1 manifest of pinned offline .ok files")
    export_parser.add_argument("--output", type=Path, required=True, help="Destination .glb file")
    export_parser.add_argument("--report", type=Path, help="JSON evidence sidecar; defaults to OUTPUT.export.json")
    export_parser.add_argument("--fps", type=float, default=60, help="Minimum sample rate; default 60 frames per second")
    export_parser.add_argument("--end", help="Exact decimal end time, from zero through the authored scene duration")
    export_parser.add_argument("--position-tolerance", type=float, default=0.001, metavar="METRES")
    export_parser.add_argument("--rotation-tolerance", type=float, default=0.001, metavar="RADIANS")
    export_parser.add_argument("--time-tolerance", type=float, default=0.000001, metavar="SECONDS")
    export_parser.add_argument("--no-helpers", action="store_true", help="Omit the display-only assembly and joint markers")
    export_parser.add_argument("--max-operations", type=int,
                               help="GLB/0.7 caller reduction of the source operation request; grants no host authority")
    export_parser.add_argument("--max-elapsed-ms", type=int,
                               help="GLB/0.7 caller reduction of the source computation timeout in milliseconds")
    suite = commands.add_parser("conformance", help="Execute the published source cases and expected observations")
    suite.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURES)
    suite.add_argument("--output", type=Path, help="Write the complete JSON report to this path")
    agent = commands.add_parser("agent", help="Serve an explicitly selected durable agent contract as local JSONL")
    agent.add_argument("--protocol", choices=["ontokin.agent/0.1", "ontokin.agent/0.2", "ontokin.agent/0.3", "ontokin.agent/0.4", "ontokin.agent/0.5", "ontokin.agent/0.6"], default="ontokin.agent/0.1", help="Select the explicit core, construction, surface, impulse, force or planar reach agent contract")
    agent.add_argument("--store", type=Path, required=True, help="Directory for immutable snapshots and durable request/run state")
    agent.add_argument("--request", type=Path, help="Read one JSON request, emit its receipt, and exit")
    agent.add_argument("--wait", action="store_true", help="Wait for this request's terminal result instead of returning a queued receipt")
    args = parser.parse_args(argv)
    if args.command == "agent":
        from .agent_cli import run
        return run(args)
    if args.command == "capabilities":
        _print(capabilities(host_policy=host_policy))
        return 0
    if args.command == "export" and (args.bundle or args.target != "ontokin.glb/0.1"):
        return _program_export(args, host_policy=host_policy)
    if args.command == "export" and (args.max_operations is not None or args.max_elapsed_ms is not None):
        _print({"outcome": "invalid_request", "error": {"code": "OKA-E-REQUEST",
                "message": "Execution caller caps require explicit GLB/0.7."}})
        return 2
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
