"""Execute one frozen C193 control. Every output remains explicitly diagnostic."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import platform
import runpy
import sys
import time
from types import SimpleNamespace


FREEZE_SHA = "b5f0ef1361705bb8948ffd34f46fb974bd9489b898b4bd81be5cf8792794e261"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--retained", type=Path, required=True)
    parser.add_argument("--design", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--blender", type=Path, required=True)
    parser.add_argument("--case", choices=("N0", "N1", "N2", "N3"), required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    sys.path.insert(0, str(repo))
    from prototypes.guided_contact_v01.common import Budget, canonical_bytes, load_contract, schema_check, sha256, strict_json
    from prototypes.guided_contact_v01.glb import encode_raw, project, verify_mapping
    from prototypes.guided_contact_v01.native_validation import validate_native, validate_scene_artifact, write_native_evidence
    from prototypes.guided_contact_v01.supervisor import check_sizes, supervise
    from prototypes.guided_contact_v01.transaction import file_hash, retain_implementation, write_mapping

    assert sha256(args.freeze.read_bytes()) == FREEZE_SHA, "Independent control freeze differs"
    args.out.mkdir(parents=True, exist_ok=False)
    out = args.out.resolve()
    budget = Budget(1000000, 80000)
    budget.authorize(1000000, 80000, None, None)
    receipt = {"schema": "ontokin.c193.native-diagnostic/0.1", "case": args.case,
               "started_unix_s": time.time(), "qualified_delivery": False,
               "independent_freeze_sha256": FREEZE_SHA,
               "python": platform.python_version(), "platform": platform.platform(),
               "native_executed": False, "mapping_pass": False}
    try:
        original_source = args.design.read_bytes()
        source_text = original_source.decode()
        contract = load_contract()
        original_backend = (repo / "docs/language-design/guided-contact-v0.1/backend.json").read_bytes()
        backend = copy.deepcopy(contract["backend"])
        if args.case == "N1":
            token = "'contact.left_shoe': {'box_mm': [130, 50, 80],\n                                     'enabled': True"
            assert source_text.count(token) == 1
            source_text = source_text.replace(token, token.removesuffix("True") + "False")
        if args.case in ("N2", "N3"):
            backend["binding"] = "blender-bullet-c193-diagnostic-" + args.case.lower()
            backend["status"] = "diagnostic_only_not_adopted"
            if args.case == "N2":
                backend["guide"]["solver_iterations"] = 400
            else:
                for row in backend["native_objects"]:
                    if row["name"] in ("_left_generic", "_right_generic"):
                        row["frame"] = "initial source-derived matching shoe center"
            backend_bytes = canonical_bytes(backend)
            source_text = source_text.replace("'blender-bullet-c190-0.1'", repr(backend["binding"]))
            source_text = source_text.replace(contract["backend_sha256"], sha256(backend_bytes))
        else:
            backend_bytes = original_backend
        # The native worker consumes this serialization. Preserve its named
        # driver-variable order in validation as well as its values.
        backend = strict_json(backend_bytes)
        (out / "source-original.py").write_bytes(original_source)
        (out / "source.py").write_text(source_text)
        design = runpy.run_path(str(out / "source.py"))["DESIGN"]
        original_design = runpy.run_path(str(args.design))["DESIGN"]
        expected = copy.deepcopy(original_design)
        if args.case == "N1":
            expected["colliders"]["contact.left_shoe"]["enabled"] = False
        if args.case in ("N2", "N3"):
            expected.update(backend=backend["binding"], backend_sha256=sha256(backend_bytes))
        assert design == expected
        assert design["parts"]["left_stop"]["at_mm"][0] == 372.5
        if args.case in ("N0", "N1"):
            schema_check(design, contract["source_schema"], budget=budget)
        encoded = canonical_bytes(design)
        context = SimpleNamespace(sha=sha256(source_text.encode()), canonical=design,
                                  canonical_sha=sha256(encoded), headers={"backend": None, "output": None},
                                  span=lambda _: None)
        assert file_hash(args.blender, budget) == backend["runtime"]["executable_sha256"]
        (out / "canonical-input.json").write_bytes(encoded)
        manifest = {"source_sha256": context.sha, "canonical_input_sha256": context.canonical_sha,
                    "original_source_sha256": sha256(original_source),
                    "authoring_route": "direct-python-diagnostic", "case": args.case,
                    "qualified_delivery": False}
        (out / "source-manifest.json").write_bytes(canonical_bytes(manifest))
        (out / "backend-original.json").write_bytes(original_backend)
        (out / "backend.json").write_bytes(backend_bytes)
        retain_implementation(out, budget)
        original_worker = (out / "implementation/native_worker.py").read_bytes()
        (out / "native-worker-original.py").write_bytes(original_worker)
        if args.case == "N3":
            original_line = "    obj.location = carriage.location\n"
            replacement = (
                "    if kind == 'GENERIC':\n"
                "        follow = source['follows']['follow.' + lane]\n"
                "        part = source['parts'][lane + '_shoe']\n"
                "        origin = source['parts'][lane + '_carriage']['at_mm']\n"
                "        obj.location = native_point([origin[a] + follow['offset_mm'][a] + part['box_mm'][a] / 2 for a in range(3)])\n"
                "    else:\n"
                "        obj.location = carriage.location\n")
            worker = original_worker.decode()
            assert worker.count(original_line) == 1
            (out / "implementation/native_worker.py").write_text(worker.replace(original_line, replacement))
            (out / "constructor-change.json").write_bytes(canonical_bytes({
                "original_sha256": sha256(original_worker), "removed": original_line, "inserted": replacement,
                "scope": "diagnostic copy only; historical native_worker.py unchanged"}))
        (out / "diagnostic-runner.py").write_bytes(Path(__file__).read_bytes())
        command = [str(args.blender.resolve()), "--factory-startup", "-b", "-t", "2", "--python-exit-code", "1",
                   "--python", str(out / "implementation/native_worker.py"), "--", str(out / "canonical-input.json"),
                   str(out / "source-manifest.json"), str(out / "backend.json"), str(out)]
        receipt.update(source_sha256=context.sha, canonical_input_sha256=context.canonical_sha,
                       backend_sha256=sha256(backend_bytes), backend_binding=backend["binding"],
                       native_worker_sha256=file_hash(out / "implementation/native_worker.py"),
                       original_native_worker_sha256=sha256(original_worker),
                       executable_sha256=backend["runtime"]["executable_sha256"])
        budget.charge("scheduled_native_substeps", backend["limits"]["scheduled_native_substeps"])
        receipt["native_executed"] = True
        supervise(command, out, budget, backend, None)
        check_sizes(out, budget, backend["limits"])
        diagnostic_contract = dict(contract, backend=backend, backend_sha256=sha256(backend_bytes))
        native = strict_json((out / "native-result.json").read_bytes())
        schema_check(native, contract["native_schema"], budget=budget)
        try:
            validate_native(out / "native-result.json", context, budget, diagnostic_contract)
            receipt["native_validation"] = "pass"
        except Exception as error:
            receipt["native_validation"] = type(error).__name__ + ": " + str(error)
            if args.case != "N3" or "Native initial world frame differs: _left_generic" not in str(error):
                raise
            receipt["native_validation_limit"] = "Historical frame validator intentionally rejects the new diagnostic guide frame; independent configuration inspection required."
        validate_scene_artifact(out / "scene.blend", context, budget, diagnostic_contract)
        write_native_evidence(out, native, context)
        write_mapping(out, native, context, backend)
        if args.case == "N0":
            retained = json.loads((args.retained / "native-result.json").read_text())
            receipt["retained_samples_identical"] = native["samples"] == retained["samples"]
            assert receipt["retained_samples_identical"], "Unchanged diagnostic control failed to reproduce retained samples"
        encode_raw(out, native, context, budget, backend)
        try:
            project(out, budget)
            verify_mapping(out, native, context, budget)
            receipt["mapping_pass"] = True
        except Exception as error:
            receipt["mapping_failure"] = type(error).__name__ + ": " + str(error)
            if not (out / "mapping-failure.json").exists():
                raise
        receipt["diagnostic_completed"] = True
        check_sizes(out, budget, backend["limits"])
    except Exception as error:
        receipt["diagnostic_completed"] = False
        receipt["error"] = type(error).__name__ + ": " + str(error)
    receipt.update(finished_unix_s=time.time(), cost=budget.cost())
    (out / "diagnostic-receipt.json").write_bytes(canonical_bytes(receipt))
    inventory = {str(path.relative_to(out)): {"bytes": path.stat().st_size,
                 "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                 for path in sorted(out.rglob("*")) if path.is_file()}
    (out / "diagnostic-manifest.json").write_bytes(canonical_bytes({"files": inventory}))
    print(json.dumps(receipt, sort_keys=True))
    raise SystemExit(0 if receipt["diagnostic_completed"] else 1)


if __name__ == "__main__":
    main()
