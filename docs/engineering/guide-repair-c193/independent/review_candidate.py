#!/usr/bin/env python3
"""Audit exact candidate bytes, isolated scope and permitted version changes."""
import argparse
import ast
import copy
import difflib
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import sys

from check_artifact import CASES, check_source, digest, require, verify_frozen


def functions(path):
    return {node.name: ast.dump(node, include_attributes=False)
            for node in ast.parse(path.read_text()).body if isinstance(node, ast.FunctionDef)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    require(not args.out.exists(), "Refusing to replace independent review evidence")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    require(head == args.revision, "Candidate Git head differs")
    old, new = repo / "prototypes/guided_contact_v01", repo / "prototypes/guided_contact_v02"
    prior_contract, contract = repo / "docs/language-design/guided-contact-v0.1", repo / "docs/language-design/guided-contact-v0.2"
    manifest_sha = digest(contract / "CONTRACT-FILES.json")
    old_manifest_sha = digest(prior_contract / "CONTRACT-FILES.json")
    files = []
    for path in sorted(new.glob("*.py")):
        prior = old / path.name
        expected = (prior.read_text().replace("C191", "C193").replace("c191", "c193")
            .replace("guided_contact_v01", "guided_contact_v02").replace("guided-contact-v0.1", "guided-contact-v0.2")
            .replace("blender-bullet-c190-0.1", "blender-bullet-c193-0.1")
            .replace("amendments/C193-A1.md", "amendments/C191-A1.md")
            .replace(old_manifest_sha, manifest_sha))
        require(path.read_text() == expected, "Change beyond explicit namespace/path/hash translation: " + path.name)
        files.append({"path": str(path.relative_to(repo)), "sha256": digest(path),
                      "prior_sha256": digest(prior), "only_explicit_version_translation": True})
    require({p.name for p in old.glob("*.py")} == {p.name for p in new.glob("*.py")}, "Python module inventory changed")
    backend = json.loads((contract / "backend.json").read_text())
    prior_backend = json.loads((prior_contract / "backend.json").read_text())
    expected = copy.deepcopy(prior_backend)
    expected.update(binding="blender-bullet-c193-0.1", status=backend["status"])
    expected["guide"]["solver_iterations"] = 400
    require(backend == expected, "Backend differs beyond guide400 and version metadata")
    for item in json.loads((contract / "CONTRACT-FILES.json").read_text())["files"]:
        path = contract / item["path"]
        require(digest(path) == item["sha256"] and path.stat().st_size == item["bytes"], "Contract manifest entry differs")
    method_checks = {}
    for filename, names in (("native_worker.py", ("native_point", "mesh_box", "add_body", "add_constraint", "construct", "configuration", "capture")),
                            ("playback_projection.py", None)):
        before, after = functions(old / filename), functions(new / filename)
        for name in names or before:
            method_checks[filename + ":" + name] = before[name] == after[name]
    require(all(method_checks.values()), "Construction/capture/projection algorithm changed")
    for name in ("source.schema.json", "native-result.schema.json", "output.schema.json", "diagnostics.json", "GRAMMAR.ebnf"):
        expected = ((prior_contract / name).read_text().replace("C191", "C193").replace("c191", "c193")
                    .replace("blender-bullet-c190-0.1", "blender-bullet-c193-0.1"))
        require((contract / name).read_text() == expected, "Schema/grammar changed beyond version: " + name)
    backend_sha = digest(contract / "backend.json")
    source_rows = []
    sys.path.insert(0, str(repo))
    from prototypes.guided_contact_v02.api import validate_source
    from prototypes.guided_contact_v02.common import Budget, load_contract
    from prototypes.guided_contact_v02.source import Source
    import tempfile
    with tempfile.TemporaryDirectory(prefix="c193-independent-candidate-") as temporary:
        for case in "ABCDEF":
            source = contract / "examples" / (case + ".ok")
            output = Path(temporary) / (case + ".json")
            result = validate_source(source, host_max_operations=1000000, host_max_elapsed_ms=80000, canonical_out=output)
            require(result["successful"], "Candidate source validation failed: " + case)
            canonical = json.loads(output.read_text())
            check_source(canonical, CASES[case], backend, backend_sha, "c193-experimental-0.1")
            context = Source(source, source.read_bytes(), Budget(1000000, 80000), load_contract())
            context.parse()
            context.validate()
            require(context.source_manifest["contract_manifest_sha256"] == manifest_sha,
                    "Emitted source manifest identifies a different contract: " + case)
            row = {"case": case, "source_sha256": digest(source), "canonical_sha256": digest(output),
                   "source_manifest_contract_sha256": context.source_manifest["contract_manifest_sha256"],
                   "independent_frozen_design_equal": True}
            if case in "EF":
                direct = repo / "docs/engineering/guide-repair-c193/native/direct-sources" / (case + ".py")
                design = runpy.run_path(str(direct))["DESIGN"]
                require(design == canonical, "Direct source differs: " + case)
                row.update(direct_source_sha256=digest(direct), direct_canonical_equal=True)
            source_rows.append(row)
    base = "294d84ac5c5a15e07d042e5225646c2dab440293"
    changed = subprocess.check_output(["git", "diff", "--name-status", base, head], cwd=repo, text=True).splitlines()
    allowed = ("docs/engineering/guide-repair-c193/native/", "docs/language-design/guided-contact-v0.2/", "prototypes/guided_contact_v02/")
    require(all(line.startswith("A\t") and line.split("\t", 1)[1].startswith(allowed) for line in changed),
            "Candidate changes overlap historical/shared scope")
    report = {"version": "C193-independent-contract-and-code-review-1", "passed_for_adoption_and_qualification": True,
        "candidate_revision": head, "candidate_tree": subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=repo, text=True).strip(),
        "base_revision": base, "checker_sha256": digest(__file__), "contract_manifest_sha256": manifest_sha,
        "backend_sha256": backend_sha, "implementation_files": files,
        "constructor_capture_projection_AST_identical": method_checks, "source_rows": source_rows,
        "only_physical_change": "Both GENERIC guide overrides100→400; world/MOTOR100 unchanged",
        "work_bounds": {"capture_samples": 481, "substeps_per_frame": 10, "scheduled_substeps": 4800,
            "guide_override_iterations": 400, "world_iterations": 100, "motor_iterations": 100,
            "qualification_operation_ceiling": 1000000, "qualification_elapsed_ms_ceiling": 80000,
            "all_other_caps_identical": backend["limits"] == prior_backend["limits"],
            "operation_semantics": "Preserved scheduled-substep charges; Bullet internal iteration count is not observed or charged as host operations"},
        "inherited_preservation": verify_frozen(repo), "changed_paths": changed,
        "shared_runtime_or_old_prototype_changed": False, "new_dependency_introduced": False,
        "native_formal_qualification_claimed": False,
        "remaining_acceptance_gates": ["14 frozen formal builds", "14 independent saved-scene replays", "repeat and route byte equality",
            "all original numerical/continuous/causal gates", "translated inherited42 lifecycle cases covering19 methods",
            "fresh receiving checks", "coordinator applicable regression/integration verification"],
        "limits": "This approves exact candidate bytes for versioned adoption and bounded qualification. It does not accept a delivery or change any historical result."}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"passed_for_adoption_and_qualification": True, "candidate_revision": head,
                     "backend_sha256": backend_sha, "historical_files_verified": report["inherited_preservation"]["historical_files_verified"]}))


if __name__ == "__main__":
    main()
