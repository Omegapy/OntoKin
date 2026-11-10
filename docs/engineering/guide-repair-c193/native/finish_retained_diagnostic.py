"""Finish N2 postprocessing from immutable completed native output; no rerun."""
import argparse
import json
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.repo.resolve()))
    from prototypes.guided_contact_v01.common import Budget, canonical_bytes, load_contract, sha256, strict_json
    from prototypes.guided_contact_v01.glb import encode_raw, project, verify_mapping
    from prototypes.guided_contact_v01.native_validation import validate_native, validate_scene_artifact, write_native_evidence
    from prototypes.guided_contact_v01.supervisor import check_sizes
    from prototypes.guided_contact_v01.transaction import write_mapping
    prior = json.loads((args.input / "diagnostic-receipt.json").read_text())
    assert prior["case"] == "N2" and prior["error"] == "Failure: Native driver/authority differs: left_stop"
    shutil.copytree(args.input, args.out)
    out = args.out
    (out / "diagnostic-receipt.json").rename(out / "preserved-original-diagnostic-receipt.json")
    (out / "diagnostic-manifest.json").rename(out / "preserved-original-diagnostic-manifest.json")
    budget = Budget(1000000, 80000)
    budget.authorize(1000000, 80000, None, None)
    receipt = {"schema": "ontokin.c193.retained-diagnostic-postprocessing/0.1", "case": "N2",
               "native_execution_performed": False, "qualified_delivery": False,
               "original_attempt": str(args.input.resolve()),
               "original_receipt_sha256": sha256((args.input / "diagnostic-receipt.json").read_bytes()),
               "reason": "Validate the exact serialized backend variable ordering consumed by the completed worker; no native bytes are changed."}
    contract = load_contract()
    backend = strict_json((out / "backend.json").read_bytes())
    canonical = strict_json((out / "canonical-input.json").read_bytes())
    context = SimpleNamespace(sha=sha256((out / "source.py").read_bytes()), canonical=canonical,
                              canonical_sha=sha256((out / "canonical-input.json").read_bytes()),
                              headers={"backend": None, "output": None}, span=lambda _: None)
    diagnostic_contract = dict(contract, backend=backend)
    native = validate_native(out / "native-result.json", context, budget, diagnostic_contract)
    validate_scene_artifact(out / "scene.blend", context, budget, diagnostic_contract)
    write_native_evidence(out, native, context)
    write_mapping(out, native, context, backend)
    encode_raw(out, native, context, budget, backend)
    try:
        project(out, budget)
        verify_mapping(out, native, context, budget)
        receipt["mapping_pass"] = True
    except Exception as error:
        receipt["mapping_pass"] = False
        receipt["mapping_failure"] = type(error).__name__ + ": " + str(error)
        if not (out / "mapping-failure.json").exists():
            raise
    check_sizes(out, budget, backend["limits"])
    receipt.update(native_validation="pass", cost=budget.cost())
    (out / "postprocessing-receipt.json").write_bytes(canonical_bytes(receipt))
    inventory = {str(path.relative_to(out)): {"bytes": path.stat().st_size,
                 "sha256": sha256(path.read_bytes())} for path in sorted(out.rglob("*")) if path.is_file()}
    (out / "postprocessing-manifest.json").write_bytes(canonical_bytes({"files": inventory}))
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
