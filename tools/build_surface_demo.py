#!/usr/bin/env python3
"""Compile source-authored surface fixtures and retain identified GLB/0.3 evidence.

Python writes typed .ok fixture values, never mesh vertices. The separate
JavaScript verifier derives triangles from the published scalar definitions.
These artifacts establish export evidence; they do not close agent/0.3 or the
entire M01--M12 release gate.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ontokin.bundle import ProgramBundle, SourceUnit
from ontokin.construction import compile_construction
from ontokin.evaluator import evaluate
from ontokin.gltf import export_glb
from ontokin.scene import ExportOptions

FIXTURES = ROOT / "docs/language-design/surface-v0.1"
TIMES = ["0", "0.125", "0.5", "1", "1.375", "1.75", "2"]


def digest(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False,
                               allow_nan=False) + "\n", encoding="utf-8")


def section_fixture(data):
    """Normalize only authored scalar fixture fields, without meshing."""
    regions = data.get("region_keys", data.get("section_regions"))
    return [{"key": key, "station_m": station, "center_xy_m": center,
             "radii_xy_m": radii, "region": region}
            for key, station, center, radii, region in zip(
                data["keys"], data["stations_m"], data["centers_xy_m"],
                data["radii_xy_m"], regions)]


def shape_record(sections, materials, *, facets=16, caps="flat", path="shell",
                 element_id=None, local_position=(0, 0, 0), local_rotation=(1, 0, 0, 0),
                 motion=None, expected=None):
    return {"path": path, "element_id": element_id or ["surface-fixture", "demo", path],
            "sections": sections, "materials": materials, "facets": facets, "caps": caps,
            "local_position_m": list(local_position), "local_rotation_wxyz": list(local_rotation),
            "motion": motion or {"kind": "affine", "position_m": [0, 0, 0],
                                 "velocity_m_per_s": [0, 0, 0], "rotation_wxyz": [1, 0, 0, 0]},
            "expected": expected or {}}


def source_bundle(shape):
    """Express a scalar oracle as an actual public typed source parameter."""
    sections = ",\n".join(
        f'        "{s["key"]}": loft_section({s["station_m"]}[m], '
        f'vec3({s["center_xy_m"][0]}[m], {s["center_xy_m"][1]}[m], 0[m]), '
        f'{s["radii_xy_m"][0]}[m], {s["radii_xy_m"][1]}[m], "{s["region"]}")'
        for s in reversed(shape["sections"]))  # source order deliberately differs
    palette = ",\n".join(
        f'        "{key}": surface_material(rgba({", ".join(map(str, m["rgba"]))}), '
        f'{m["metallic"]}, {m["roughness"]})' for key, m in shape["materials"].items())
    px, py, pz = shape["local_position_m"]
    rotation = ", ".join(map(str, shape["local_rotation_wxyz"]))
    source = f'''ontokin "0.3";
module SurfaceFixture @ "surface-fixture";
profile "surface-0.1";

public class Shell @ "shell-type" {{
    public param rings @ "rings": Keyed<LoftSection> = keyed<LoftSection> {{
{sections}
    }};
    public param palette @ "palette": Keyed<SurfaceMaterial> = keyed<SurfaceMaterial> {{
{palette}
    }};
    geometry = placed(loft(self.rings, self.palette, {shape["facets"]}, "{shape["caps"]}"),
                      pose(self.frame, vec3({px}[m], {py}[m], {pz}[m]), quat({rotation})));
    physical = no_body();
}}

scene Demo @ "demo" {{
    duration = 2[s];
    gravity = vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2]);
    object shell @ "shell": Shell {{}}
}}
'''
    return ProgramBundle(SourceUnit("entry", "main.ok", source.encode("utf-8")))


def fixture_cases():
    manifest = json.loads((FIXTURES / "acceptance.json").read_text("utf-8"))
    cases = {case["id"]: case for case in manifest["cases"]}
    pin = manifest["source_bundle"]
    library = (FIXTURES / pin["library"]).read_bytes()
    entry = (FIXTURES / pin["entry"]).read_bytes()
    assert digest(library) == "sha256:" + pin["sha256"]
    assert ('digest "' + digest(library) + '";').encode() in entry
    frozen = ProgramBundle(SourceUnit("entry", pin["entry"], entry), (
        SourceUnit("package:fixture.surface-parts@1.0.0", pin["library"], library,
                   pin["package_id"], pin["version"]),))
    paint = {"clay": {"rgba": [.6, .3, .2, 1], "metallic": 0, "roughness": .8},
             "paint": {"rgba": [.1, .4, .8, 1], "metallic": .2, "roughness": .4}}
    first = shape_record([
        {"key": "foot", "station_m": 0, "center_xy_m": [0, 0], "radii_xy_m": [.5, .35], "region": "clay"},
        {"key": "neck", "station_m": 1, "center_xy_m": [.15, 0], "radii_xy_m": [.3, .2], "region": "paint"},
        {"key": "tip", "station_m": 1.5, "center_xy_m": [.15, 0], "radii_xy_m": [.2, .1], "region": "paint"}],
        paint, path="first", element_id=["surface-studio", "studio", "first"], local_position=(0, 0, .1),
        motion={"kind": "affine", "position_m": [-2, 0, 0], "velocity_m_per_s": [0, .5, 0],
                "rotation_wxyz": [1, 0, 0, 0]}, expected={"triangles": 96, "vertices": 288})
    second = shape_record([
        {"key": "foot", "station_m": 0, "center_xy_m": [0, 0], "radii_xy_m": [.65, .4], "region": "clay"},
        {"key": "middle", "station_m": .7, "center_xy_m": [.2, 0], "radii_xy_m": [.48, .38], "region": "clay"},
        {"key": "tip", "station_m": 1.8, "center_xy_m": [.25, 0], "radii_xy_m": [.1, .1], "region": "paint"}],
        paint, path="second", element_id=["surface-studio", "studio", "second"], local_position=(0, 0, .1),
        motion={"kind": "affine", "position_m": [2, 0, 0], "velocity_m_per_s": [0, 0, 0],
                "rotation_wxyz": [1, 0, 0, 0]}, expected={"triangles": 96, "vertices": 288})
    yield "studio", frozen, {"case_ids": ["M05", "M09", "M11"], "shapes": [first, second],
                              "frozen_source_bytes": True}
    for data in cases["M01"]["inputs"]:
        material = {key: {"rgba": [.15, .35, .7, 1], "metallic": .1, "roughness": .6}
                    for key in set(data["region_keys"])}
        shape = shape_record(section_fixture(data), material, facets=data["facets"],
                             caps=data["caps"], expected=data["expected"])
        yield data["name"], source_bundle(shape), {"case_ids": ["M01", "M03", "M11"], "shapes": [shape]}
    data = cases["M02"]["input"]
    material = cases["M04"]["input"]["materials"]
    taper_palette = {"base": material["base"], "middle": material["middle"], "tip": material["top"]}
    shape = shape_record(section_fixture(data), taper_palette, expected=cases["M02"]["expected"])
    yield "offset-taper", source_bundle(shape), {"case_ids": ["M02", "M11"], "shapes": [shape]}
    material_data = cases["M04"]["input"]
    rings = [{"key": f"station-{i}", "station_m": station, "center_xy_m": [0, 0],
              "radii_xy_m": [.4, .25], "region": material_data["section_regions"][i]}
             for i, station in enumerate(material_data["stations_m"])]
    shape = shape_record(rings, material, expected={"triangles": 96, "vertices": 288,
                         "triangles_per_region": cases["M04"]["expected"]["per_region_triangles"]})
    yield "regional-materials", source_bundle(shape), {"case_ids": ["M04", "M11"], "shapes": [shape]}
    edited = copy.deepcopy(shape)
    edited["materials"]["middle"] = {"rgba": [.7, .15, .1, 1], "metallic": .6, "roughness": .3}
    yield "regional-materials-edited", source_bundle(edited), {
        "case_ids": ["M04", "M11"], "shapes": [edited],
        "palette_edit_of": "regional-materials", "changed_region": "middle",
        "note": "Independent source variant, not an agent atomic-edit claim."}
    equal = copy.deepcopy(shape)
    equal["materials"] = {name: copy.deepcopy(material["base"]) for name in material}
    yield "equal-pbr-distinct-regions", source_bundle(equal), {"case_ids": ["M04", "M11"], "shapes": [equal]}
    for index, variant in enumerate(cases["M06"]["variants"]):
        rings = [{"key": f"section-{i:02}", "station_m": i, "center_xy_m": [0, 0],
                  "radii_xy_m": [variant["rx_m"], variant["ry_m"]], "region": "plain"}
                 for i in range(variant["sections"])]
        shape = shape_record(rings, {"plain": material["base"]}, facets=variant["facets"],
                             caps=variant["caps"], expected={"triangles": variant["expected_triangles"],
                                                           "vertices": variant["expected_vertices"]})
        yield f"held-out-{index + 1}", source_bundle(shape), {"case_ids": ["M06", "M11"], "shapes": [shape]}
    # A nonidentity visual rotation is local to the child. Its hinge's rotation
    # comes only from authored action and hierarchy, never from a Python mesh.
    rotated = copy.deepcopy(first)
    rotated.update(path="rig.shell", element_id=["surface-fixture", "demo", "rig", "shell"],
                   local_position_m=[.2, -.1, .3],
                   local_rotation_wxyz=[.7071067811865476, .7071067811865476, 0, 0],
                   motion={"kind": "hinge_y_on_translating_z90_parent", "position_m": [1, 2, .5],
                           "velocity_m_per_s": [.25, 0, 0], "mount_position_m": [.3, .4, .2],
                           "angle_rad_per_second": .7853981633974483})
    base = source_bundle(rotated).entry.text
    begin = base.index('scene Demo @ "demo"')
    source = base[:begin] + '''class Rig @ "rig-type" {
    geometry = empty();
    physical = no_body();
    public part shell @ "shell": Shell {}
    public site mount @ "mount" {
        pose = pose(self.frame, vec3(0.3[m], 0.4[m], 0.2[m]), quat(1, 0, 0, 0));
        interface = "rigid.origin";
        size = 0[m];
    }
    public joint yaw @ "yaw": hinge {
        parent = self.mount;
        child = self.shell.origin;
        axis = vec3(0, 1, 0);
        limits = range(0[deg], 90[deg]);
        initial = 0[rad];
    }
    public method turn @ "turn"(duration: Time) -> Action {
        return tween(self.yaw, 90[deg], duration);
    }
}
scene Demo @ "demo" {
    duration = 2[s];
    gravity = vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2]);
    object rig @ "rig": Rig {
        placement = pose(world, vec3(1[m], 2[m], 0.5[m]),
                         quat(0.7071067811865476, 0, 0, 0.7071067811865476));
    }
    action travel @ "travel" = move(rig, vector(world, 0.25[m/s], 0[m/s], 0[m/s]), 2[s]);
    action rotate @ "rotate" = rig.turn(2[s]);
    at 0[s] sequence { start travel; start rotate; }
}
'''
    yield "rotated-animation", ProgramBundle(SourceUnit("entry", "main.ok", source.encode())), {
        "case_ids": ["M09", "M11"], "shapes": [rotated],
        "empty_objects": [{"path": "rig", "element_id": ["surface-fixture", "demo", "rig"],
                           "motion": {"kind": "affine", "position_m": [1, 2, .5],
                                      "velocity_m_per_s": [.25, 0, 0],
                                      "rotation_wxyz": [.7071067811865476, 0, 0, .7071067811865476]}}]}


def build(output):
    output.mkdir(parents=True, exist_ok=True)
    manifest_bytes = (FIXTURES / "acceptance.json").read_bytes()
    records = []
    for name, bundle, oracle in fixture_cases():
        destination = output / name
        destination.mkdir(parents=True, exist_ok=True)
        compiler = compile_construction(bundle, level="evaluated")
        model = compiler.model
        # The exporter receives the compiled language model; no geometry is
        # passed from this builder or from the independent scalar oracle.
        result = export_glb(model, options=ExportOptions(helpers=False),
                            target_contract="ontokin.glb/0.3")
        assert result.report["validation"]["status"] == "passed"
        samples = evaluate(model, TIMES)["samples"]
        for unit in bundle.units:
            (destination / unit.filename).write_bytes(unit.raw)
        write_json(destination / "program.bundle.json", bundle.to_payload())
        (destination / "scene.glb").write_bytes(result.data)
        write_json(destination / "scene.export.json", result.report)
        write_json(destination / "oracle.json", {
            "schema_version": "ontokin.surface-fixture-oracle/0.1", "fixture": name,
            "origin": "Frozen acceptance values and independently stated source scalar values; no evaluated geometry.",
            "acceptance_manifest_sha256": digest(manifest_bytes), **oracle})
        write_json(destination / "scene.reference.json", {
            "schema_version": "ontokin.surface-native-reference/0.1",
            "program_revision": bundle.program_revision, "source_manifest": bundle.manifest(),
            "artifact_sha256": digest(result.data), "tolerances": result.report["tolerances"],
            "samples": [{"time_seconds": s["time_seconds"], "objects": {
                path: {"position_m": obj["position_m"], "orientation_wxyz": obj["orientation_wxyz"]}
                for path, obj in s["objects"].items()}} for s in samples]})
        records.append({"fixture": name, "case_ids": oracle["case_ids"],
                        "program_revision": bundle.program_revision,
                        "artifact_sha256": digest(result.data), "glb_bytes": len(result.data)})
    revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,
                              capture_output=True, check=True).stdout.strip()
    status = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, text=True,
                            capture_output=True, check=True).stdout.splitlines()
    summary = {"schema_version": "ontokin.surface-native-build/0.1", "status": "built",
               "generated_at_utc": datetime.now(timezone.utc).isoformat(), "git_revision": revision,
               "working_tree_changes": status, "builder_sha256": digest(Path(__file__).read_bytes()),
               "acceptance_manifest_sha256": digest(manifest_bytes), "fixtures": records,
               "limits": ["A source/export corpus is not the complete native surface release or agent/0.3 gate.",
                          "External destination and browser checks execute in separate tools.",
                          "No manual or host-generated geometry is supplied to the compiler/exporter."]}
    write_json(output / "build.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    summary = build(args.output_dir)
    print(json.dumps({"status": summary["status"], "fixtures": len(summary["fixtures"]),
                      "output_dir": str(args.output_dir)}, indent=2))


if __name__ == "__main__":
    main()
