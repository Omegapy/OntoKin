#!/usr/bin/env python3
"""Exercise independent guards with real retained and deliberately changed bytes."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import struct
import tempfile

from check_artifact import CASES, check_source, decode, digest, review, verify_frozen


def encode(doc, blob):
    encoded = json.dumps(doc, separators=(",", ":")).encode()
    encoded += b" " * (-len(encoded) % 4)
    blob += b"\0" * (-len(blob) % 4)
    return (struct.pack("<4sII", b"glTF", 2, 28 + len(encoded) + len(blob))
            + struct.pack("<I4s", len(encoded), b"JSON") + encoded
            + struct.pack("<I4s", len(blob), b"BIN\0") + blob)


def mutate_glb(path, mutation):
    doc, blob = decode(path)
    blob = bytearray(blob)
    channel = next(c for c in doc["animations"][0]["channels"]
        if doc["nodes"][c["target"]["node"]]["name"] == "left_carriage"
        and c["target"]["path"] == "translation")
    sampler = doc["animations"][0]["samplers"][channel["sampler"]]
    if mutation == "drop_key":
        doc["accessors"][sampler["input"]]["count"] -= 1
        doc["accessors"][sampler["output"]]["count"] -= 1
    else:
        accessor_index = sampler["input" if mutation == "retime" else "output"]
        if mutation == "mesh_vertex":
            accessor_index = doc["meshes"][0]["primitives"][0]["attributes"]["POSITION"]
        accessor = doc["accessors"][accessor_index]
        view = doc["bufferViews"][accessor["bufferView"]]
        width = 1 if accessor["type"] == "SCALAR" else 3
        row = 0 if mutation == "mesh_vertex" else 100
        offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0) + row * view.get("byteStride", width * 4)
        value, = struct.unpack_from("<f", blob, offset)
        struct.pack_into("<f", blob, offset, value + (0.0001 if mutation == "retime" else 0.001))
    path.write_bytes(encode(doc, bytes(blob)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--diagnostics", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    require_new = not args.out.exists()
    if not require_new:
        raise ValueError("Refusing to replace checker-control evidence")
    source_dir = args.diagnostics / "N2-postprocess-r1"
    backend_path = source_dir / "backend.json"
    backend_sha = digest(backend_path)
    backend = json.loads(backend_path.read_text())
    source = json.loads((source_dir / "canonical-input.json").read_text())
    results = []

    def test(name, expected, call):
        try:
            value = call()
            accepted = bool(value["passed"])
            observed = "accepted" if accepted else "rejected"
            detail = value.get("failures", [])
        except (ValueError, AssertionError, IndexError, KeyError, ArithmeticError) as error:
            accepted, observed, detail = False, "rejected", type(error).__name__ + ": " + str(error)
        passed = accepted == expected
        results.append({"control": name, "expected": "accepted" if expected else "rejected",
                        "observed": observed, "passed": passed, "detail": detail})

    test("unchanged-N2-guide400-positive", True, lambda: review(source_dir, "F", backend_path, backend_sha))
    test("retained-N0-mapping-failure", False, lambda: review(args.diagnostics / "N0", "F",
        args.diagnostics / "N0/backend.json", digest(args.diagnostics / "N0/backend.json")))
    test("retained-N3-anchor-mapping-failure", False, lambda: review(args.diagnostics / "N3", "F",
        args.diagnostics / "N3/backend.json", digest(args.diagnostics / "N3/backend.json")))
    test("N1-collider-removed-causal-control", True, lambda: review(args.diagnostics / "N1", "N1",
        args.diagnostics / "N1/backend.json", digest(args.diagnostics / "N1/backend.json")))
    changes = {
        "second-mass-owner-or-total-mass": lambda s: s["bodies"]["body.left"].update(mass_kg=2),
        "prescribed-motion-authority": lambda s: s["bodies"]["body.left"].update(authority="prescribed"),
        "changed-right-feed": lambda s: s["bodies"]["body.right"].update(feed_mm_s=149),
        "changed-follow-parent": lambda s: s["follows"]["follow.left"].update(parent="right_carriage"),
        "hidden-stop-schedule": lambda s: s["bodies"]["body.left"].update(stop_time_s=1.54),
        "wrong-collider-owner": lambda s: s["colliders"]["contact.left_shoe"].update(owner="body.right"),
    }
    for name, mutation in changes.items():
        changed = copy.deepcopy(source)
        mutation(changed)
        test(name, False, lambda changed=changed: check_source(changed, CASES["F"], backend, backend_sha))
    test("unreviewed-backend-hash", False, lambda: review(source_dir, "F", backend_path, "0" * 64))
    with tempfile.TemporaryDirectory(prefix="c193-independent-checker-") as work:
        work = Path(work)
        for mutation in ("retime", "final_x", "drop_key", "mesh_vertex", "native_x", "native_time"):
            path = work / mutation
            path.mkdir()
            for name in ("backend.json", "canonical-input.json", "raw.glb", "final.glb", "native-transforms.json", "scene.blend"):
                shutil.copyfile(source_dir / name, path / name)
            if mutation.startswith("native_"):
                trace = json.loads((path / "native-transforms.json").read_text())
                if mutation == "native_x":
                    trace[100]["matrices_blender_m"]["left_carriage"][0][3] += 0.001
                else:
                    trace[100]["time_s"] += 0.0001
                (path / "native-transforms.json").write_text(json.dumps(trace) + "\n")
                modified = "native-transforms.json"
            else:
                mutate_glb(path / "final.glb", mutation)
                modified = "final.glb"
            test(mutation, False, lambda path=path: review(path, "F", backend_path, backend_sha))
            results[-1]["mutated_file_sha256"] = digest(path / modified)
    report = {"version": "C193-independent-checker-controls-1", "passed": all(r["passed"] for r in results),
        "controls": results, "count": len(results), "checker_sha256": digest(Path(__file__).parent / "check_artifact.py"),
        "control_code_sha256": digest(__file__), "inherited_preservation": verify_frozen(),
        "basis": {"N2_native_result_sha256": digest(source_dir / "native-result.json"),
                  "N2_backend_sha256": backend_sha},
        "native_executions": 0, "notes": "Mutations are reproducible checker controls; no source/scene/retained output is modified."}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": report["passed"], "controls": report["count"], "evidence": str(args.out)}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
