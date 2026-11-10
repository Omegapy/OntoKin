"""Run the frozen fourteen C193 builds after exact adoption publication."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


BACKEND_SHA = "9ce64fd758b4e7f659ddd9d4bb3bcf7a0faa6a1883cc018c673e10536fe0aefe"
CONTRACT_SHA = "d5ce5afa4e1a548f493b9b0184798bfe8e88f954a2f57771e2d20e0256037037"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--blender", type=Path, required=True)
    parser.add_argument("--adoption", type=Path, required=True)
    parser.add_argument("--adoption-sha256", required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    assert digest(args.adoption) == args.adoption_sha256
    contract = repo / "docs/language-design/guided-contact-v0.2"
    assert digest(contract / "backend.json") == BACKEND_SHA
    assert digest(contract / "CONTRACT-FILES.json") == CONTRACT_SHA
    args.out.mkdir(parents=True, exist_ok=False)
    output = args.out.resolve()
    (output / "adoption-receipt.md").write_bytes(args.adoption.read_bytes())
    matrix = [(f"ok-{case}-{repeat}", "ok", case) for case in "ABCDEF" for repeat in (1, 2)]
    matrix += [(f"python-{case}-1", "python", case) for case in "EF"]
    manifest = {"schema": "ontokin.c193.formal-builds/0.1", "started_unix_s": time.time(),
                "adoption_sha256": args.adoption_sha256, "backend_sha256": BACKEND_SHA,
                "contract_manifest_sha256": CONTRACT_SHA,
                "planned_builds": len(matrix), "native_resimulations_performed_here": 0,
                "independent_and_receiving_checks": "pending; separate reviewer and coordinator scope",
                "runs": []}
    (output / "formal-builds.json").write_text(json.dumps(manifest, indent=2) + "\n")
    for identifier, route, case in matrix:
        source = (contract / f"examples/{case}.ok" if route == "ok" else
                  Path(__file__).resolve().parent / f"direct-sources/{case}.py")
        destination = output / identifier
        command = [sys.executable, "-B", str(Path(__file__).resolve().parent / "build.py"),
                   "--repo", str(repo), "--route", route, "--source", str(source), "--out", str(destination),
                   "--blender", str(args.blender.resolve())]
        with (output / f"{identifier}.wrapper.stdout.txt").open("wb") as stdout, \
                (output / f"{identifier}.wrapper.stderr.txt").open("wb") as stderr:
            process = subprocess.run(command, cwd=repo, stdout=stdout, stderr=stderr, timeout=110)
        receipt = json.loads((destination / "delivery.json").read_text())
        artifact = receipt.get("artifact_directory")
        if artifact is None:
            if route == "python":
                artifact = destination / "artifact"
            else:
                stages = list((destination / "store/attempts").glob("*/failed-stage"))
                assert len(stages) == 1, "Failed build must identify its single retained stage"
                artifact = stages[0]
        artifact = Path(artifact)
        row = {"id": identifier, "case": case, "route": route, "source": str(source),
               "source_sha256": digest(source), "command": command,
               "wrapper_returncode": process.returncode, "build_receipt": str(destination / "delivery.json"),
               "artifact_directory": str(artifact), "build_successful": receipt["successful"],
               "independently_qualified": False,
               "ideal_contact_s": {"A": 1.6, "B": 1.4, "C": 1.5, "D": None, "E": 1.46, "F": 1.54}[case],
               "expected_left_final_gap_mm": -50 if case == "D" else 0,
               "expected_right_final_gap_mm": 15,
               "artifacts": {name: {"path": str(artifact / name), "sha256": digest(artifact / name),
                                    "bytes": (artifact / name).stat().st_size}
                             for name in ("canonical-input.json", "scene.blend", "native-result.json", "native-transforms.json",
                                          "raw.glb", "final.glb", "backend.json", "implementation-manifest.json")
                             if (artifact / name).exists()}}
        manifest["runs"].append(row)
        (output / "formal-builds.json").write_text(json.dumps(manifest, indent=2) + "\n")
        print(json.dumps({"id": identifier, "build_successful": receipt["successful"],
                          "artifact": str(artifact)}), flush=True)
    manifest["finished_unix_s"] = time.time()
    manifest["all_builds_self_checked"] = all(row["build_successful"] for row in manifest["runs"])
    (output / "formal-builds.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"completed_builds": len(manifest["runs"]),
                      "all_builds_self_checked": manifest["all_builds_self_checked"],
                      "manifest": str(output / "formal-builds.json")}), flush=True)


if __name__ == "__main__":
    main()
