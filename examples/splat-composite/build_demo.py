"""Export both service-entrance edits and register one fixed visual environment."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import struct
import subprocess
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SERVICE = ROOT / "examples" / "service-entrance"
sys.path.insert(0, str(ROOT))

from ontokin.budget_runtime import execute_torque_export
from ontokin.execution_budget import HostPolicy
from ontokin.scene import ExportOptions
from ontokin.texture_bundle import load_texture_bundle


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def asset(root, path):
    return {"path": path.relative_to(root).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def export_cart(root, case, source, width, clearance):
    directory = root / case
    directory.mkdir()
    entry = directory / "main.ok"
    entry.write_bytes(source.encode("utf-8"))
    bundle = load_texture_bundle({
        "schema_version": "ontokin.bundle/0.2", "entry": {"filename": entry.name, "source": source},
        "modules": [], "assets": [],
    })
    accepted = directory / "accepted-bundle.json"
    write_json(accepted, bundle.to_payload())
    result = execute_torque_export(
        bundle, policy=HostPolicy(max_operations=1_000_000, max_elapsed_ms=80_000),
        caller_caps={"max_operations": 450_000, "max_elapsed_ms": 80_000},
        options=ExportOptions(end="3.25", fps=32, helpers=False),
    )
    write_json(directory / "export.json", result.report)
    if result.data is None:
        raise ValueError(f"{case} export failed; see {directory / 'export.json'}")
    recording = directory / "sliding-gate.glb"
    recording.write_bytes(result.data)
    check = subprocess.run(
        [sys.executable, "-IB", str(SERVICE / "checks" / "check_passage.py"), str(entry),
         str(accepted), str(recording), "--width", str(width)], capture_output=True, text=True,
    )
    if check.stderr:
        print(check.stderr, file=sys.stderr)
    report = json.loads(check.stdout)
    write_json(directory / "passage.json", report)
    if check.returncode or report["result"] != "PASS":
        raise ValueError(f"{case} passage check failed; see {directory / 'passage.json'}")
    measured = report["crossing"]["minimum_lateral_clearance_m"]
    if not all(math.isclose(measured[side], clearance, abs_tol=1e-6) for side in ("panel", "post")):
        raise ValueError(f"{case} clearance disagrees with the expected {clearance} m per side")
    return {"source": asset(root, entry), "glb": asset(root, recording)}, measured


def screen_anchors(fixture):
    """Pair three stored splat centres with the fixture design coordinates in metres."""
    data = fixture.read_bytes()
    json_size = struct.unpack_from("<I", data, 12)[0]
    doc = json.loads(data[20:20 + json_size])
    primitive = doc["meshes"][0]["primitives"][0]
    positions = doc["accessors"][primitive["attributes"]["POSITION"]]
    view = doc["bufferViews"][positions["bufferView"]]
    start = 28 + json_size + view.get("byteOffset", 0) + positions.get("byteOffset", 0)
    # The fixture generator appends five columns of six screen splats after the room.
    first = positions["count"] - 30
    corners = [("screen-bottom-left", first, [-0.20, 0.01, -0.34]),
               ("screen-bottom-right", first + 24, [0.20, 0.01, -0.34]),
               ("screen-top-left", first + 5, [-0.20, 0.51, -0.34])]
    return [{"name": name, "world": design,
             "environment": list(struct.unpack_from("<3f", data, start + index * view.get("byteStride", 12)))}
            for name, index, design in corners]


def build(output):
    from ontokin.composite_manifest import check_manifest

    output.mkdir(parents=True, exist_ok=False)
    fixture = HERE / "fixtures" / "registration-screen.glb"
    env = output / fixture.name
    shutil.copyfile(fixture, env)
    environment = {
        "name": "Registration screen", **asset(output, env),
        "requiredExtension": "KHR_gaussian_splatting", "authority": "visual-only",
        "provenance": "Synthetic OntoKin registration-screen fixture in the authored metre frame.",
    }
    registration = {
        "kind": "rigid", "worldUnit": "metre",
        "matrix": [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
        "toleranceM": 0.000001,
        "anchors": screen_anchors(env),
    }
    source = (SERVICE / "src" / "main.ok").read_text(encoding="utf-8")
    if source.count("0.29[m]") != 4:
        raise ValueError("expected four cart deck-edge coordinates in the original source")
    summary = {}
    for case, text, width, clearance in (("baseline", source, 0.58, 0.46),
                                         ("widened", source.replace("0.29[m]", "0.45[m]"), 0.90, 0.30)):
        authored, measured = export_cart(output, case, text, width, clearance)
        manifest = output / (case + ".json")
        write_json(manifest, {"schema": "ontokin-composite/1", "authored": authored,
                              "environment": environment, "registration": registration, "collisionProxy": None})
        checks = check_manifest(manifest)
        write_json(output / case / "manifest-check.json", checks)
        summary[case] = {"manifest": manifest.name, "cartWidthM": width,
                         "clearanceM": measured, "environmentSha256": checks["environment"]["sha256"]}
    write_json(output / "results.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="new output directory")
    build(parser.parse_args().output.resolve())
