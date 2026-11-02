#!/usr/bin/env python3
"""Record actual C088 source/control observations against one clean fixed cut.

Candidate imports occur only inside main after exact input and source checks.
The producer records observations; the separate stdlib reader judges them.
Control execution uses a separate process pinned to unchanged C087.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
from pathlib import Path
import sys

from keyed_membership_evidence import (
    EvidenceRun, Freeze, PREDECESSOR_COMMIT, PROFILE, TARGET, error_record,
    jsonl_writer, node_location, safe, save, sha,
)
from keyed_membership_observer import ExecutionObserver


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=("candidate", "predecessor-controls", "candidate-controls"), required=True)
    parser.add_argument("--no-exports", action="store_true", help="Diagnostic source-only subset; never full acceptance")
    parser.add_argument("--only", nargs="+", help="Explicit preserved diagnostic subset; never full acceptance")
    args = parser.parse_args()
    sys.dont_write_bytecode = True
    freeze = Freeze(args.inputs)
    run = EvidenceRun(args.output, args.checkout, freeze, "source-observations")
    run.summary.update(mode=args.mode, full_cohort=not args.only and not args.no_exports)
    if args.mode == "predecessor-controls" and run.before["commit"] != PREDECESSOR_COMMIT:
        raise ValueError("Literal/reduction controls require exact unchanged C087.")
    if args.mode == "candidate-controls" and run.before["commit"] == PREDECESSOR_COMMIT:
        raise ValueError("Candidate controls require a separately fixed candidate source cut.")
    sys.path.insert(0, str(args.checkout.resolve()))
    import ontokin
    if Path(ontokin.__file__).resolve().parent != args.checkout.resolve() / "ontokin":
        raise RuntimeError("Runtime import resolved outside the explicitly selected checkout.")
    from ontokin.texture_bundle import load_texture_file_manifest
    from ontokin.execution_budget import HostPolicy, SharedExecutionBudget, admit_entry_budget
    from ontokin.construction import compile_construction
    from ontokin.values import Type, Value, KeyedValue
    from ontokin.syntax import Node
    from ontokin.string_concat import concat_strings
    from ontokin.string_concat_program_runtime import StringConcatProgramRuntime
    from ontokin.budget_runtime import execute_string_concat_export
    from ontokin.scene import ExportOptions
    from ontokin.surface_runtime import materialize_surface
    from ontokin.texture_runtime import texture_coordinates, texture_metadata
    from ontokin.evaluator import evaluate
    functions = {"concat_strings": concat_strings}
    if args.mode == "candidate":
        from ontokin.keyed_membership import has_key
        from ontokin.keyed_membership_program_runtime import KeyedMembershipProgramRuntime
        from ontokin.budget_runtime import execute_keyed_membership_export
        functions["has_key"] = has_key

    def scalar(value):
        if value.type.kind == "Keyed":
            return {key: scalar(leaf) for key, leaf in value.value.entries}
        return detached(value.value) if value.known else {"unknown": True}

    def detached(value, depth=0):
        if depth > 20:
            raise ValueError("Unexpected deep observed metadata")
        if isinstance(value, Node):
            return node_location(value)
        if isinstance(value, Type):
            return {"kind": value.kind, "dimension": None if value.dimension is None else list(value.dimension),
                    "element": None if value.element is None else detached(value.element, depth + 1),
                    "name": value.name}
        if isinstance(value, Value):
            return {"type": detached(value.type, depth + 1), "known": value.known,
                    "value": detached(value.value, depth + 1) if value.known else None,
                    "frame": value.frame, "hint": value.hint}
        if isinstance(value, KeyedValue):
            return [[key, detached(leaf, depth + 1)] for key, leaf in value.entries]
        if dataclasses.is_dataclass(value):
            return {f.name: detached(getattr(value, f.name), depth + 1) for f in dataclasses.fields(value)}
        if type(value) is dict:
            return {str(key): detached(child, depth + 1) for key, child in value.items()}
        if type(value) in (tuple, list):
            return [detached(child, depth + 1) for child in value]
        return safe(value)

    class Context:
        def __init__(self, policy, profile):
            self.profile = profile
            self.observer = None
            self.execution_budget = SharedExecutionBudget(policy=policy, check=self.poll)
            self.observer = ExecutionObserver(self.execution_budget, functions)

        def poll(self):
            if self.observer is not None:
                self.observer.checkpoint()

        def __call__(self):
            self.execution_budget.tick()

        def admit(self, source):
            if self.execution_budget.resolved is None:
                admit_entry_budget(source.entry, self.execution_budget, profile=self.profile)
            elif self.execution_budget.admitted_entry_revision != source.entry.revision:
                raise ValueError("A request cannot silently replace its admitted source.")

    def binding(source):
        if source.entry.raw.lstrip().startswith(b'ontokin "0.20";'):
            return StringConcatProgramRuntime(), "string-concat-0.1", execute_string_concat_export
        if args.mode != "candidate" or not source.entry.raw.lstrip().startswith(b'ontokin "0.21";'):
            raise ValueError("Unexpected entry declaring version")
        return KeyedMembershipProgramRuntime(), PROFILE, execute_keyed_membership_export

    cases = []
    for original in freeze.source["cases"]:
        if args.mode == "candidate":
            cases.append({"id": original["id"], "kind": "core", "files": freeze.root / original["files"],
                          "original": original, "mode": "source"})
        else:
            for mode, file in original.get("controls", {}).items():
                cases.append({"id": mode + "-" + original["id"], "kind": "core",
                              "files": freeze.root / file, "original": original, "mode": mode})
            if "predecessor-direct" in original.get("tags", []):
                cases.append({"id": original["id"], "kind": "core", "files": freeze.root / original["files"],
                              "original": original, "mode": "source"})
    for original in freeze.representative["cases"]:
        if (original["mode"] == "source") == (args.mode == "candidate"):
            cases.append({"id": "agent-" + original["id"], "kind": "representative",
                          "files": freeze.root / "agent" / original["files"],
                          "original": original, "mode": original["mode"]})
    if args.only:
        selected = set(args.only)
        cases = [case for case in cases if case["id"] in selected]
        if {case["id"] for case in cases} != selected:
            raise ValueError("Unknown selected source case")
    run.summary["case_inventory"] = [{"id": c["id"], "kind": c["kind"], "mode": c["mode"]} for c in cases]
    run.checkpoint()

    def provenance(compiler, value, owner, field):
        result = {"members": [p + "." + n for p, n in sorted(compiler.dependencies.get((owner, field), set()))],
                  "called_definitions": [list(x) for x in sorted(compiler.call_dependencies.get((owner, field), set()))],
                  "generated_dependencies": sorted(compiler.generated_dependencies.get((owner, field), set()))}
        for family, method in (("transforms", "_transform_records"), ("reductions", "_reduction_records"),
                               ("filters", "_filter_records"), ("merges", "_merge_records"),
                               ("zips", "_zip_records"), ("rekeys", "_rekey_records")):
            result[family] = detached(getattr(compiler, method)(value))
        return result

    def public(source, runtime, profile, policy):
        ctx = Context(policy, profile)
        with ctx.observer:
            try:
                result = runtime.validate_revision(source, level="constructed", check=ctx)
                record = {"status": "passed" if result.get("outcome") == "valid" else "failed", "result": result}
            except BaseException as error:
                record = {"status": "failed", "error": error_record(error)}
        record.update(api=type(runtime).__name__ + ".validate_revision", execution_budget=ctx.execution_budget.report(status=record["status"]),
                      observation=ctx.observer.report())
        return record

    def private(source, profile, policy, case):
        ctx = Context(policy, profile)
        with ctx.observer:
            try:
                ctx.admit(source)
                compiler = compile_construction(source, level="constructed", execution_budget=ctx.execution_budget)
                result = {"status": "passed", "canonical_manifest": source.manifest(),
                          "program_revision": source.program_revision}
                if case["kind"] == "core":
                    value = compiler.field("probe", "observed", compiler.program)
                    result.update(observed=scalar(value), observed_type=detached(value.type), known=value.known,
                                  geometry=detached(compiler.model.objects["probe"].geometry),
                                  provenance=provenance(compiler, value, "probe", "observed"))
                    repeated = compiler.field("probe", "observed", compiler.program)
                    result["warm_binding"] = {"observed": scalar(repeated),
                                              "provenance": provenance(compiler, repeated, "probe", "observed")}
                else:
                    result["values"], result["provenance"] = {}, {}
                    for owner in ("first", "sibling"):
                        for field in ("overrides", "override_flags", "selected", "names"):
                            value = compiler.field(owner, field, compiler.program)
                            result["values"][owner + "." + field] = scalar(value)
                            result["provenance"][owner + "." + field] = provenance(compiler, value, owner, field)
                    result["generated_keys"] = {owner: list(compiler.collections[owner + ".panels"]["ordered_keys"])
                                                for owner in ("first", "sibling")}
                    result["property_names"] = {path: list(obj.properties) for path, obj in compiler.model.objects.items()}
                    result["properties"] = {path: {name: detached(value) for name, value in obj.properties.items()}
                                             for path, obj in compiler.model.objects.items()}
                    evaluated = evaluate(compiler.model, times=freeze.representative["times_seconds"], work=compiler.reach_work)
                    result["geometry"] = {}
                    for path, obj in compiler.model.objects.items():
                        if path in ("first", "sibling"):
                            continue
                        record = {"element_id": list(obj.element_id),
                                  "translation_samples_m": [s["objects"][path]["position_m"] for s in evaluated["samples"]],
                                  "quaternion_samples_wxyz": [s["objects"][path]["orientation_wxyz"] for s in evaluated["samples"]]}
                        if obj.geometry["kind"] == "box":
                            record["box_size_m"] = list(obj.geometry["size"])
                        else:
                            mesh, placement = materialize_surface(obj.geometry, max_vertices=1000, check=ctx)
                            record.update(corners_m=[list(point) for point in sorted(set(mesh.positions))],
                                          triangles=mesh.triangle_count, local_placement=detached(placement),
                                          regions={r.key: {"color": list(r.material.rgba), "metallic": r.material.metallic,
                                                           "roughness": r.material.roughness} for r in mesh.regions},
                                          texture=texture_metadata(obj.geometry, check=ctx))
                            coordinates = texture_coordinates(obj.geometry, mesh, check=ctx)
                            top = next(r for r in mesh.regions if r.key == "top")
                            record["top_uv_rows"] = [{"position": list(mesh.positions[i]), "uv": list(coordinates["top"][i])}
                                                      for i in sorted(set(top.indices))]
                        result["geometry"][path] = record
                    result["texture_sha256"] = {key: sha(asset.raw) for key, asset in compiler.model.texture_assets.items()}
            except BaseException as error:
                result = {"status": "failed", "error": error_record(error)}
        result.update(api="compile_construction + typed source/geometry/provenance observation",
                      execution_budget=ctx.execution_budget.report(status=result["status"]),
                      observation=ctx.observer.report())
        return result

    with jsonl_writer(run.output / "source-records.jsonl.gz") as emit:
        for case in cases:
            record = {"id": case["id"], "kind": case["kind"], "mode": case["mode"],
                      "source_case": case["original"]["id"], "input_files": case["files"].relative_to(freeze.root).as_posix()}
            try:
                source = load_texture_file_manifest(case["files"])
                runtime, profile, execute = binding(source)
                policy = HostPolicy(**case["original"].get("host_policy", {}))
                record.update(profile=profile, program_revision=source.program_revision,
                              canonical_manifest=source.manifest(), host_policy=policy.ceilings)
                record["public"] = public(source, runtime, profile, policy)
                record["private"] = private(source, profile, policy, case)
                if case["kind"] == "representative" and case["original"]["status"] == "passed" and not args.no_exports:
                    exported = execute(source, policy=policy, options=ExportOptions(fps=4, end="1", helpers=False))
                    record["export"] = {"report": exported.report, "has_bytes": exported.data is not None}
                    if exported.data is not None:
                        relative = "glb/" + case["original"]["id"] + ".glb"
                        path = run.output / relative
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_bytes(exported.data)
                        record["export"].update(path=relative, sha256=sha(exported.data), bytes=len(exported.data))
                        run.summary.setdefault("artifacts", []).append({"role": case["original"]["id"],
                            "program_revision": source.program_revision, "path": relative,
                            "sha256": sha(exported.data), "bytes": len(exported.data)})
            except BaseException as error:
                record["producer_exception"] = error_record(error)
                run.summary["internal_failures"].append({"id": case["id"], "error": error_record(error)})
            emit(record)
            run.summary["records"].append({"id": case["id"], "public_status": record.get("public", {}).get("status"),
                                            "private_status": record.get("private", {}).get("status")})
            run.checkpoint()
    finished = run.finish()
    print(json.dumps({"status": run.summary["status"], "records": len(run.summary["records"]),
                      "artifacts": len(run.summary.get("artifacts", [])), "output": str(run.output)}))
    return 0 if finished else 1


if __name__ == "__main__":
    raise SystemExit(main())
