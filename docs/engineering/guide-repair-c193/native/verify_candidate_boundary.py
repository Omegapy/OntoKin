"""Check version separation and unchanged construction/projection algorithms."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import runpy
import sys
import tempfile


def functions(path):
    return {node.name: ast.dump(node, include_attributes=False)
            for node in ast.parse(path.read_text()).body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = args.repo.resolve()
    sys.path.insert(0, str(root))
    from prototypes.guided_contact_v02.api import validate_source
    from prototypes.guided_contact_v01.api import validate_source as validate_legacy
    old, new = root / "prototypes/guided_contact_v01", root / "prototypes/guided_contact_v02"
    origin = [{"name": path.name,
               "original_sha256": hashlib.sha256((old / path.name).read_bytes()).hexdigest(),
               "selected_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
              for path in sorted(new.glob("*.py"))]
    before, after = functions(old / "native_worker.py"), functions(new / "native_worker.py")
    constructor = {name: before[name] == after[name] for name in
                   ("native_point", "mesh_box", "add_body", "add_constraint", "construct", "configuration", "capture")}
    before, after = functions(old / "playback_projection.py"), functions(new / "playback_projection.py")
    projection = {name: before[name] == after[name] for name in before}
    assert all(constructor.values()) and all(projection.values())
    backend_before = json.loads((root / "docs/language-design/guided-contact-v0.1/backend.json").read_text())
    backend_after = json.loads((root / "docs/language-design/guided-contact-v0.2/backend.json").read_text())
    expected = json.loads(json.dumps(backend_before))
    expected.update(binding=backend_after["binding"], status=backend_after["status"])
    expected["guide"]["solver_iterations"] = 400
    assert backend_after == expected
    rows = []
    with tempfile.TemporaryDirectory(prefix="c193-candidate-") as temporary:
        temporary = Path(temporary)
        for case in "ABCDEF":
            source = root / f"docs/language-design/guided-contact-v0.2/examples/{case}.ok"
            canonical = temporary / f"{case}.json"
            result = validate_source(source, host_max_operations=1000000, host_max_elapsed_ms=80000,
                                     canonical_out=canonical)
            assert result["successful"]
            row = {"case": case, "source_sha256": result["source_sha256"],
                   "canonical_sha256": result["canonical_input_sha256"], "validated": True}
            if case in "EF":
                direct = runpy.run_path(str(root / f"docs/engineering/guide-repair-c193/native/direct-sources/{case}.py"))["DESIGN"]
                row["direct_canonical_equal"] = json.loads(canonical.read_text()) == direct
                assert row["direct_canonical_equal"]
            rows.append(row)
        new_from_old = validate_source(root / "docs/language-design/guided-contact-v0.1/examples/A.ok",
                                      host_max_operations=1000000, host_max_elapsed_ms=80000)
        old_from_new = validate_legacy(root / "docs/language-design/guided-contact-v0.2/examples/A.ok",
                                      host_max_operations=1000000, host_max_elapsed_ms=80000)
        assert new_from_old["diagnostics"][0]["code"] == "C193_E_BINDING"
        assert old_from_new["diagnostics"][0]["code"] == "C191_E_BINDING"
    report = {"native_qualification_performed": False,
              "checker_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "constructor_functions_ast_identical": constructor,
              "projection_functions_ast_identical": projection,
              "backend_only_physical_change": "guide.solver_iterations100→400; binding/status metadata separate",
              "package_origin": origin, "source_admission": rows,
              "cross_binding_rejected": {"new_rejects_old": new_from_old, "old_rejects_new": old_from_new}}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": True, "sources": len(rows), "constructor_functions": len(constructor),
                      "projection_functions": len(projection), "cross_binding_rejected": True}))


if __name__ == "__main__":
    main()
