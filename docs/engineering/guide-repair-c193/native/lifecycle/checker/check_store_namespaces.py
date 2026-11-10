"""Check actual C193 accepted-store namespace and both incompatible-store rejects."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys


def inventory(root):
    return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(root.rglob("*")) if path.is_file()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--seed", type=Path, required=True)
    parser.add_argument("--blender", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    sys.path.insert(0, str(repo))
    from prototypes.guided_contact_v01.api import run as legacy_run
    from prototypes.guided_contact_v02.api import run as selected_run
    from prototypes.guided_contact_v02.transaction import load_state
    original_store = args.seed.resolve().parents[1]
    seed_state = load_state(original_store)
    assert seed_state["schema"] == "ontokin.c193.store/0.1"
    assert (original_store / seed_state["artifact_directory"]).resolve() == args.seed.resolve()
    args.out.mkdir(parents=True, exist_ok=False)
    rows = []
    for name, function, schema, prefix, version in (
        ("selected_rejects_legacy_store", selected_run, "ontokin.c191.store/0.1", "C193", "0.2"),
        ("legacy_rejects_selected_store", legacy_run, "ontokin.c193.store/0.1", "C191", "0.1"),
    ):
        store = args.out / name
        shutil.copytree(original_store, store)
        state = dict(seed_state, schema=schema)
        (store / "state.json").write_text(json.dumps(state, sort_keys=True) + "\n")
        before = (store / "state.json").read_bytes()
        artifact = store / state["artifact_directory"]
        previous = inventory(artifact)
        called = []

        def prohibited_worker(argv, stage):
            called.append(True)
            raise AssertionError("Incompatible store reached native execution")

        result = function(repo / f"docs/language-design/guided-contact-v{version}/examples/A.ok",
                          store=store, blender=args.blender, host_max_operations=1000000,
                          host_max_elapsed_ms=80000, hooks={"worker_command": prohibited_worker})
        assert not result["successful"] and not result["committed"] and not called
        diagnostic, = result["diagnostics"]
        assert diagnostic["code"] == prefix + "_E_IO"
        assert diagnostic["message"] == "Malformed accepted store state"
        assert result["source_sha256"] is None and diagnostic["span"] is None
        assert (store / "state.json").read_bytes() == before and inventory(artifact) == previous
        rows.append({"case": name, "passed": True, "source_admitted": False, "native_execution": False,
                     "accepted_bytes_unchanged": True, "result": result})
    report = {"schema": "ontokin.c193.store-namespace-check/0.1", "passed": True,
              "seed_artifact": str(args.seed.resolve()), "seed_store_schema": seed_state["schema"],
              "seed_accepted_revision": seed_state["accepted_revision"],
              "native_executions": 0, "cases": rows}
    (args.out / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": True, "cases": len(rows), "native_executions": 0}))


if __name__ == "__main__":
    main()
