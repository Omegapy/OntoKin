#!/usr/bin/env python3
"""C193 prepared direct-Python runner on the unchanged C193 native constructor.

The editable Python file supplies DESIGN. No .ok parser or .ok source is used.
This runner and the native construction/export utilities count as reusable setup.
It is a bounded experiment harness, not a new supported product interface.
"""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import runpy
import sys
import time
from types import SimpleNamespace


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--design", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--blender", type=Path, required=True)
    parser.add_argument("--reopen", type=Path)
    args = parser.parse_args()
    started = time.time()
    args.out.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(args.repo.resolve()))
    from prototypes.guided_contact_v02.common import Budget, CONTRACT, canonical_bytes, load_contract, schema_check, sha256
    from prototypes.guided_contact_v02.glb import encode_raw, project, verify_mapping
    from prototypes.guided_contact_v02.native_validation import validate_native, validate_scene_artifact, write_native_evidence
    from prototypes.guided_contact_v02.supervisor import check_sizes, supervise
    from prototypes.guided_contact_v02.transaction import file_hash, retain_implementation, write_mapping

    budget = Budget(1000000, 80000)
    receipt = {"route": "direct-python", "successful": False, "started_unix_s": started,
               "python": platform.python_version(), "platform": platform.platform(),
               "reusable_setup": "C193 direct runner and unchanged C193 constructor/validation/recorded-output utilities",
               "ok_source_parsed": False, "product_transaction_claimed": False}
    try:
        source = args.design.read_bytes()
        design = runpy.run_path(str(args.design))["DESIGN"]
        contract = load_contract()
        backend = contract["backend"]
        assert design["backend_sha256"] == contract["backend_sha256"], "Direct design backend hash differs from selected contract"
        schema_check(design, contract["source_schema"], budget=budget)
        budget.authorize(design["execution"]["max_operations"], design["execution"]["max_elapsed_ms"], None, None)
        encoded = canonical_bytes(design)
        context = SimpleNamespace(sha=sha256(source), canonical=design,
            canonical_sha=sha256(encoded), headers={"backend": None, "output": None}, span=lambda _: None)
        assert platform.system() == "Linux" and platform.machine() == "x86_64"
        assert file_hash(args.blender, budget) == backend["runtime"]["executable_sha256"]
        (args.out / "source.py").write_bytes(source)
        (args.out / "canonical-input.json").write_bytes(encoded)
        manifest = {"source_sha256": context.sha, "canonical_input_sha256": context.canonical_sha,
                    "authoring_route": "direct-python", "source_path": args.design.name,
                    "canonical_profile_label": "The shared source_binding field names the C193 interchange profile; this route does not parse .ok"}
        (args.out / "source-manifest.json").write_bytes(canonical_bytes(manifest))
        (args.out / "backend.json").write_bytes((CONTRACT / "backend.json").read_bytes())
        retain_implementation(args.out, budget)
        (args.out / "direct-runner.py").write_bytes(Path(__file__).read_bytes())
        command = [str(args.blender.resolve()), "--factory-startup", "-b", "-t", "2", "--python-exit-code", "1",
                   "--python", str((args.out / "implementation/native_worker.py").resolve()), "--",
                   str((args.out / "canonical-input.json").resolve()), str((args.out / "source-manifest.json").resolve()),
                   str((args.out / "backend.json").resolve()), str(args.out.resolve())]
        if args.reopen:
            command.extend(["--reopen", str(args.reopen.resolve())])
        receipt.update(source_sha256=context.sha, canonical_input_sha256=context.canonical_sha,
                       executable_sha256=backend["runtime"]["executable_sha256"],
                       reopen_source_sha256=file_hash(args.reopen) if args.reopen else None)
        budget.charge("scheduled_native_substeps", backend["limits"]["scheduled_native_substeps"])
        supervise(command, args.out, budget, backend, None)
        assert file_hash(args.blender, budget) == backend["runtime"]["executable_sha256"]
        check_sizes(args.out, budget, backend["limits"])
        native = validate_native(args.out / "native-result.json", context, budget, contract)
        validate_scene_artifact(args.out / "scene.blend", context, budget, contract)
        write_native_evidence(args.out, native, context)
        write_mapping(args.out, native, context, backend)
        encode_raw(args.out, native, context, budget, backend)
        project(args.out, budget)
        verify_mapping(args.out, native, context, budget)
        check_sizes(args.out, budget, backend["limits"])
        receipt.update(successful=True, artifact_directory=str(args.out.resolve()))
    except Exception as error:
        receipt["error"] = type(error).__name__ + ": " + str(error)
    receipt.update(finished_unix_s=time.time(), cost=budget.cost())
    (args.out / "build-receipt.json").write_bytes(canonical_bytes(receipt))
    inventory = {str(p.relative_to(args.out)): {"bytes": p.stat().st_size,
                 "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                 for p in sorted(args.out.rglob("*")) if p.is_file()}
    (args.out / "manifest.json").write_bytes(canonical_bytes({"files": inventory}))
    print(json.dumps(receipt, sort_keys=True))
    raise SystemExit(0 if receipt["successful"] else 1)


if __name__ == "__main__":
    main()
