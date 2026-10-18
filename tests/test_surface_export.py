"""Native .ok surface delivery checked independently from serialized GLB bytes.

All geometry enters through the source compiler. The test reader and analytical
oracles do not call the production exporter, mesh builder or playback reader.
These checks cover the GLB portion of M01–M04/M06–M10; the whole release also
needs the separate agent, composition and external destination evidence.
"""

from collections import Counter
import copy
import hashlib
import json
import math
import struct
import unittest
from unittest.mock import patch

from ontokin.bundle import ProgramBundle, SourceUnit
from ontokin.construction import compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.gltf import export_glb, validate_export
from ontokin.scene import ExportOptions
from ontokin.syntax import parse
from ontokin.validator import validate
from tests.test_construction import RELEASE_SOURCE, bundle as construction_bundle
from tests.test_export import DecodedGLB, encode_glb, simple_source
from tests.test_surface_source import ROOT, bundle as studio_bundle


CONTRACT = "ontokin.glb/0.3"
ACCEPTANCE = json.loads((ROOT / "acceptance.json").read_text("utf-8"))
CASES = {case["id"]: case for case in ACCEPTANCE["cases"]}
DEFAULT_PALETTE = {"blue": {"rgba": [.1, .4, .8, 1], "metallic": .2, "roughness": .4}}
DEFAULT_SECTIONS = [("bottom", 0, 0, 0, .5, .5, "blue"),
                    ("top", 2, 0, 0, .5, .5, "blue")]


def surface_members(sections=None, palette=None, *, facets=16, caps="flat", placement=None):
    """Write typed .ok values; no host mesh or triangle buffer is supplied."""
    sections = DEFAULT_SECTIONS if sections is None else sections
    palette = DEFAULT_PALETTE if palette is None else palette
    rings = ",\n".join(
        f'"{key}": loft_section({z!r}[m], vec3({x!r}[m], {y!r}[m], 0[m]), '
        f'{rx!r}[m], {ry!r}[m], "{region}")'
        for key, z, x, y, rx, ry, region in sections)
    materials = ",\n".join(
        f'"{key}": surface_material(rgba({", ".join(repr(c) for c in value["rgba"])}), '
        f'{value["metallic"]!r}, {value["roughness"]!r})'
        for key, value in palette.items())
    geometry = f'loft(self.rings, self.palette, {facets}, "{caps}")'
    if placement is not None:
        geometry = f"placed({geometry}, {placement})"
    return f'''
    public param rings @ "rings": Keyed<LoftSection> = keyed<LoftSection> {{ {rings} }};
    public param palette @ "palette": Keyed<SurfaceMaterial> = keyed<SurfaceMaterial> {{ {materials} }};
    geometry = {geometry};
'''


def single_source(sections=None, palette=None, *, facets=16, caps="flat", placement=None,
                  objects='object shell @ "shell": Shell {}', scene="", duration=2):
    return f'''ontokin "0.3";
module NativeExport @ "native-export";
profile "surface-0.1";
class Shell @ "shell-class" {{
    {surface_members(sections, palette, facets=facets, caps=caps, placement=placement)}
    physical = no_body();
}}
scene Demo @ "demo" {{
    duration = {duration}[s];
    gravity = vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2]);
    {objects}
    {scene}
}}
'''


def compile_source(text, **kwargs):
    sealed = ProgramBundle(SourceUnit("entry", "native-export.ok", text.encode("utf-8")))
    return sealed, compile_construction(sealed, level="evaluated", **kwargs)


def render(text, *, options=None, **kwargs):
    sealed, compiler = compile_source(text)
    result = export_glb(compiler.model, target_contract=CONTRACT,
                        options=options or ExportOptions(helpers=False), **kwargs)
    return DecodedGLB(result.data), result, compiler, sealed


def mesh_primitives(decoded, path):
    _, node = decoded.source_node(path)
    return decoded.document["meshes"][node["mesh"]]["primitives"]


def regions(decoded, path):
    return {primitive["extras"]["ontokin"]["region_key"]: primitive
            for primitive in mesh_primitives(decoded, path)}


def triangles(decoded, primitive):
    positions = decoded.accessor(primitive["attributes"]["POSITION"])
    normals = decoded.accessor(primitive["attributes"]["NORMAL"])
    indices = [row[0] for row in decoded.accessor(primitive["indices"])]
    for offset in range(0, len(indices), 3):
        face = indices[offset:offset + 3]
        yield tuple(positions[index] for index in face), tuple(normals[index] for index in face)


def mesh_content(decoded, path):
    """Compare geometry/material payloads independently of buffer offsets."""
    return {key: {"faces": list(triangles(decoded, primitive)),
                  "pbr": decoded.document["materials"][primitive["material"]]["pbrMetallicRoughness"]}
            for key, primitive in regions(decoded, path).items()}


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def oriented_volume(faces):
    return math.fsum(sum(x * y for x, y in zip(a, cross(b, c))) / 6
                     for a, b, c in faces)


def change_accessor(binary, document, accessor_index, row_index, values):
    """Patch existing BIN values using only glTF accessor definitions."""
    accessor = document["accessors"][accessor_index]
    view = document["bufferViews"][accessor["bufferView"]]
    width = {"SCALAR": 1, "VEC3": 3, "VEC4": 4}[accessor["type"]]
    kind = {5121: "B", 5123: "H", 5125: "I", 5126: "f"}[accessor["componentType"]]
    fmt = "<" + kind * width
    stride = view.get("byteStride", struct.calcsize(fmt))
    offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0) + row_index * stride
    struct.pack_into(fmt, binary, offset, *values)


class NativeSurfaceExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sealed = studio_bundle()
        cls.compiler = compile_construction(cls.sealed, level="evaluated")
        cls.result = export_glb(cls.compiler.model, target_contract=CONTRACT,
                               source_uri="surface-studio.bundle.json",
                               source_sha256=cls.sealed.entry.revision,
                               options=ExportOptions(helpers=False))
        cls.decoded = DecodedGLB(cls.result.data)

    def assertVector(self, actual, expected, tolerance=1e-5):
        self.assertEqual(len(actual), len(expected))
        for actual_value, expected_value in zip(actual, expected):
            self.assertAlmostEqual(actual_value, expected_value, delta=tolerance)

    def assertRejected(self, document, binary=None, *, model=None, options=None):
        data = encode_glb(document, self.decoded.binary if binary is None else binary)
        try:
            report = validate_export(data, self.compiler.model if model is None else model,
                                     target_contract=CONTRACT, options=options)
        except OntoKinError as error:
            self.assertEqual(error.diagnostic.details["target_contract"], CONTRACT)
        else:
            self.assertEqual(report["status"], "failed", "Modified artifact was incorrectly accepted")

    def test_frozen_bundle_delivers_native_profile_and_exact_source_identities(self):
        result, document = self.result, self.decoded.document
        self.assertEqual(result.report["schema_version"], "ontokin.glb-report/0.3")
        self.assertEqual(result.report["target_contract"], CONTRACT)
        self.assertEqual(result.report["outcome"], "valid")
        self.assertEqual(result.report["program_revision"], self.sealed.program_revision)
        self.assertEqual(result.report["program"]["manifest"], self.sealed.manifest())
        self.assertEqual(result.report["artifact"]["sha256"],
                         "sha256:" + hashlib.sha256(result.data).hexdigest())
        self.assertEqual(result.report["validation"]["status"], "passed")
        metadata = document["extras"]["ontokin"]
        self.assertEqual(metadata["profile"], "surface-0.1")
        self.assertEqual(metadata["program"], result.report["program"])
        self.assertEqual(metadata["source"]["entry_revision"], self.sealed.entry.revision)
        self.assertNotEqual(metadata["source"]["entry_revision"], self.sealed.program_revision)
        self.assertEqual(len(document["nodes"]), 2)
        self.assertTrue(all("children" not in node for node in document["nodes"]))
        self.assertEqual(document["scenes"][0]["nodes"], [0, 1])
        for path, ordered in (("first", ["foot", "neck", "tip"]),
                              ("second", ["foot", "middle", "tip"])):
            _, node = self.decoded.source_node(path)
            record = node["extras"]["ontokin"]
            self.assertEqual(record["element_id"], list(self.compiler.model.objects[path].element_id))
            self.assertEqual(record["program_revision"], self.sealed.program_revision)
            self.assertEqual(record["source_mapping"], self.compiler.model.occurrence_provenance[path])
            self.assertEqual(record["physical"]["kind"], "no_body")
            surface = record["surface"]
            self.assertEqual(surface["section_keys"], ordered)
            self.assertEqual(surface["triangle_count"], 96)
            self.assertEqual(surface["vertex_count"], 288)
            self.assertEqual(surface["facets"], 16)
            self.assertEqual(surface["caps"], "flat")
            self.assertEqual(surface["physical_participation"], "none")
            self.assertEqual(surface["local_visual_placement"], {
                "frame": "carrier_self_frame", "position_m": [0., 0., .1],
                "orientation_wxyz": [1., 0., 0., 0.]})
            location = surface["source_location"]
            self.assertEqual(location["source_id"], "package:fixture.surface-parts@1.0.0")
            source = self.sealed.modules[0].raw
            self.assertIn(b"loft(", source[location["start_byte"]:location["end_byte"]])

    def test_frozen_source_world_motion_and_local_offset_are_applied_once(self):
        for t, expected in zip(CASES["M09"]["times_s"], CASES["M09"]["world_positions_m"]):
            self.assertVector(self.decoded.node_pose("first", t)["translation"], expected)
            self.assertVector(self.decoded.node_pose("second", t)["translation"], (2, 0, 0))
        for path, expected_top in (("first", 1.6), ("second", 1.9)):
            positions = self.decoded.accessor(mesh_primitives(self.decoded, path)[0]["attributes"]["POSITION"])
            self.assertAlmostEqual(min(p[2] for p in positions), .1, delta=1e-6)
            self.assertAlmostEqual(max(p[2] for p in positions), expected_top, delta=1e-6)
        self.assertEqual(len(self.compiler.model.actions), 1)
        self.assertEqual(self.compiler.model.owned_mass("first"), 0)

    def test_analytic_circular_and_elliptic_meshes_use_native_source(self):
        for case in CASES["M01"]["inputs"]:
            with self.subTest(shape=case["name"]):
                sections = [(key, z, *center, *radius, region)
                            for key, z, center, radius, region in zip(
                                case["keys"], case["stations_m"], case["centers_xy_m"],
                                case["radii_xy_m"], case["region_keys"])]
                palette = {case["region_keys"][0]: DEFAULT_PALETTE["blue"]}
                decoded, _, compiler, _ = render(single_source(sections, palette))
                primitive = mesh_primitives(decoded, "shell")[0]
                positions = decoded.accessor(primitive["attributes"]["POSITION"])
                faces = [face for face, _ in triangles(decoded, primitive)]
                self.assertEqual(len(positions), case["expected"]["vertices"])
                self.assertEqual(len(faces), case["expected"]["triangles"])
                self.assertVector(tuple(min(p[k] for p in positions) for k in range(3)),
                                  case["expected"]["bounds_m"][0])
                self.assertVector(tuple(max(p[k] for p in positions) for k in range(3)),
                                  case["expected"]["bounds_m"][1])
                ideal = [(cx + rx * math.cos(2 * math.pi * j / 16),
                          cy + ry * math.sin(2 * math.pi * j / 16), z)
                         for _, z, cx, cy, rx, ry, _ in sections for j in range(16)]
                ideal += [(cx, cy, z) for _, z, cx, cy, _, _, _ in (sections[0], sections[-1])]
                for position in positions:
                    self.assertLessEqual(min(max(abs(a - b) for a, b in zip(position, wanted))
                                             for wanted in ideal), 1e-5)
                for wanted in ideal:
                    self.assertLessEqual(min(max(abs(a - b) for a, b in zip(position, wanted))
                                             for position in positions), 1e-5)
                if case["name"] == "cylinder":
                    # The frozen 1e-9 volume limit applies before float32 storage.
                    source_mesh = compiler.surface_meshes["shell"]["mesh"]
                    source_faces = [source_mesh.positions[i:i + 3]
                                    for i in range(0, len(source_mesh.positions), 3)]
                    self.assertAlmostEqual(oriented_volume(source_faces), case["expected"]["volume_m3"], delta=1e-9)
                    self.assertAlmostEqual(oriented_volume(faces), case["expected"]["volume_m3"], delta=2e-7)
                    self.assertGreater(oriented_volume(faces), 0)

    def test_offset_taper_caps_winding_flat_normals_and_material_membership(self):
        case = CASES["M02"]
        values = case["input"]
        sections = [(key, z, *center, *radius, region)
                    for key, z, center, radius, region in zip(
                        values["keys"], values["stations_m"], values["centers_xy_m"],
                        values["radii_xy_m"], values["section_regions"])]
        palette = {"base": DEFAULT_PALETTE["blue"],
                   "middle": {"rgba": [.8, .2, .1, .6], "metallic": .9, "roughness": .1},
                   "tip": {"rgba": [.7, .7, .7, 1], "metallic": .5, "roughness": .5}}
        decoded, _, _, _ = render(single_source(list(reversed(sections)), palette))
        _, node = decoded.source_node("shell")
        self.assertEqual(node["extras"]["ontokin"]["surface"]["section_keys"],
                         case["expected"]["numeric_station_order"])
        counts = Counter()
        caps = Counter()
        for key, primitive in regions(decoded, "shell").items():
            self.assertEqual(primitive.get("mode", 4), 4)
            for face, normals in triangles(decoded, primitive):
                counts[key] += 1
                a, b, c = face
                area = cross(tuple(y - x for x, y in zip(a, b)),
                             tuple(y - x for x, y in zip(a, c)))
                self.assertGreater(math.hypot(*area), 1e-10)
                for normal in normals:
                    self.assertTrue(all(math.isfinite(value) for value in normal))
                    self.assertAlmostEqual(math.hypot(*normal), 1, delta=1e-6)
                    self.assertVector(normal, tuple(v / math.hypot(*area) for v in area), 2e-6)
                zlow, zhigh = min(p[2] for p in face), max(p[2] for p in face)
                if abs(zhigh - zlow) < 1e-6:
                    lower = abs(zlow) < 1e-6
                    self.assertEqual(key, "base" if lower else "tip")
                    self.assertVector(normals[0], (0, 0, -1 if lower else 1), 1e-6)
                    caps["lower" if lower else "upper"] += 1
                else:
                    interval = 0 if abs(zlow) < 1e-6 else 1
                    self.assertEqual(key, values["section_regions"][interval])
                    self.assertAlmostEqual(zhigh, values["stations_m"][interval + 1], delta=1e-6)
                    mean_z = sum(p[2] for p in face) / 3
                    weight = ((mean_z - values["stations_m"][interval]) /
                              (values["stations_m"][interval + 1] - values["stations_m"][interval]))
                    lower_center, upper_center = values["centers_xy_m"][interval:interval + 2]
                    center = tuple(a + weight * (b - a) for a, b in zip(lower_center, upper_center))
                    radial = (sum(p[0] for p in face) / 3 - center[0],
                              sum(p[1] for p in face) / 3 - center[1])
                    self.assertGreater(area[0] * radial[0] + area[1] * radial[1], 0)
        self.assertEqual(dict(counts), case["expected"]["triangles_per_region"])
        self.assertEqual(dict(caps), {"lower": 16, "upper": 16})

    def test_frozen_held_out_counts_bounds_and_open_caps(self):
        for case in CASES["M06"]["variants"]:
            with self.subTest(sections=case["sections"], facets=case["facets"]):
                sections = [(f"ring{i}", i * .1, 0, 0, case["rx_m"], case["ry_m"], "blue")
                            for i in range(case["sections"])]
                decoded, _, _, _ = render(single_source(sections, facets=case["facets"], caps=case["caps"]))
                primitive = mesh_primitives(decoded, "shell")[0]
                positions = decoded.accessor(primitive["attributes"]["POSITION"])
                faces = list(triangles(decoded, primitive))
                self.assertEqual(len(positions), case["expected_vertices"])
                self.assertEqual(len(faces), case["expected_triangles"])
                self.assertVector(tuple(min(p[k] for p in positions) for k in range(3)),
                                  (-case["rx_m"], -case["ry_m"], 0))
                self.assertVector(tuple(max(p[k] for p in positions) for k in range(3)),
                                  (case["rx_m"], case["ry_m"], (case["sections"] - 1) * .1))
                for face, normals in faces:
                    self.assertTrue(all(math.isfinite(v) for p in face + normals for v in p))
                    if case["caps"] == "none":
                        self.assertGreater(max(p[2] for p in face) - min(p[2] for p in face), .09)

    def test_repeated_regions_remain_single_groups_and_unused_palette_is_omitted(self):
        palette = {"blue": DEFAULT_PALETTE["blue"],
                   "red": {"rgba": [.8, .1, .1, .5], "metallic": .7, "roughness": .2},
                   "unused": {"rgba": [0, 1, 0, 1], "metallic": 0, "roughness": 1}}
        sections = [(f"s{i}", i, 0, 0, .5, .5, region)
                    for i, region in enumerate(("blue", "red", "blue", "red"))]
        decoded, _, _, _ = render(single_source(sections, palette))
        groups = regions(decoded, "shell")
        self.assertEqual(set(groups), {"blue", "red"})
        self.assertEqual(len(mesh_primitives(decoded, "shell")), 2)
        self.assertEqual({key: len(list(triangles(decoded, primitive))) for key, primitive in groups.items()},
                         {"blue": 80, "red": 48})
        for key, primitive in groups.items():
            material = decoded.document["materials"][primitive["material"]]
            self.assertEqual(material["pbrMetallicRoughness"], {
                "baseColorFactor": palette[key]["rgba"],
                "metallicFactor": palette[key]["metallic"],
                "roughnessFactor": palette[key]["roughness"]})
            self.assertEqual(material.get("alphaMode", "OPAQUE"), "BLEND" if key == "red" else "OPAQUE")

    def test_same_color_different_pbr_factors_are_not_merged(self):
        palette = {"blue": DEFAULT_PALETTE["blue"],
                   "metal": {"rgba": DEFAULT_PALETTE["blue"]["rgba"], "metallic": 1, "roughness": .05}}
        sections = [DEFAULT_SECTIONS[0], ("top", 2, 0, 0, .5, .5, "metal")]
        decoded, _, _, _ = render(single_source(sections, palette))
        groups = regions(decoded, "shell")
        self.assertNotEqual(groups["blue"]["material"], groups["metal"]["material"])
        self.assertEqual(decoded.document["materials"][groups["metal"]["material"]]["pbrMetallicRoughness"]["metallicFactor"], 1)

    def test_station_region_edit_changes_triangle_membership_without_moving_vertices(self):
        palette = {"blue": DEFAULT_PALETTE["blue"],
                   "red": {"rgba": [.8, .1, .1, 1], "metallic": .7, "roughness": .2}}
        sections = [("bottom", 0, 0, 0, .5, .5, "blue"),
                    ("middle", 1, .2, 0, .4, .3, "red"),
                    ("top", 2, .3, 0, .2, .1, "red")]
        edited = list(sections)
        edited[1] = (*edited[1][:-1], "blue")
        before, _, _, first_revision = render(single_source(sections, palette))
        after, _, _, next_revision = render(single_source(edited, palette))
        self.assertNotEqual(first_revision.program_revision, next_revision.program_revision)
        for attribute in ("POSITION", "NORMAL"):
            self.assertEqual(before.accessor(mesh_primitives(before, "shell")[0]["attributes"][attribute]),
                             after.accessor(mesh_primitives(after, "shell")[0]["attributes"][attribute]))
        counts = lambda decoded: {key: len(list(triangles(decoded, primitive)))
                                  for key, primitive in regions(decoded, "shell").items()}
        self.assertEqual(counts(before), {"blue": 48, "red": 48})
        self.assertEqual(counts(after), {"blue": 80, "red": 16})
        for key, old_primitive in regions(before, "shell").items():
            new_primitive = regions(after, "shell")[key]
            old_pbr = before.document["materials"][old_primitive["material"]]["pbrMetallicRoughness"]
            new_pbr = after.document["materials"][new_primitive["material"]]["pbrMetallicRoughness"]
            self.assertEqual(old_pbr, new_pbr)

    def test_compatible_older_primitive_module_can_share_the_native_scene(self):
        library = b'''ontokin "0.2";
module Legacy @ "legacy";
profile "construction-0.1";
public class Marker @ "marker" {
    geometry = sphere(0.1[m]);
    appearance = rgba(0.2, 0.3, 0.4, 0.5);
    physical = no_body();
}
'''
        dependency = SourceUnit("package:fixture.legacy@1.0.0", "legacy.ok", library,
                                "fixture.legacy", "1.0.0")
        source = single_source(objects='''object shell @ "shell": Shell {}
            object marker @ "marker": old.Marker {}''')
        source = source.replace('profile "surface-0.1";', 'profile "surface-0.1";\n' +
                                f'import old @ "old" from "fixture.legacy" version "1.0.0" digest "{dependency.revision}";')
        sealed = ProgramBundle(SourceUnit("entry", "native-export.ok", source.encode("utf-8")), (dependency,))
        compiler = compile_construction(sealed, level="evaluated")
        result = export_glb(compiler.model, target_contract=CONTRACT, options=ExportOptions(helpers=False))
        decoded = DecodedGLB(result.data)
        self.assertEqual(len(decoded.document["nodes"]), 2)
        primitive = mesh_primitives(decoded, "marker")[0]
        for vertex in decoded.accessor(primitive["attributes"]["POSITION"]):
            self.assertAlmostEqual(math.hypot(*vertex), .1, delta=1e-6)
        material = decoded.document["materials"][primitive["material"]]
        self.assertEqual(material["pbrMetallicRoughness"], {
            "baseColorFactor": [.2, .3, .4, .5], "metallicFactor": 0., "roughnessFactor": .7})
        self.assertEqual(material["alphaMode"], "BLEND")
        _, marker = decoded.source_node("marker")
        self.assertNotIn("surface", marker["extras"]["ontokin"])
        self.assertEqual(result.report["program"]["sources"][dependency.source_id]["source_revision"],
                         dependency.revision)

    def test_occurrence_palette_repair_changes_only_its_material_and_revision(self):
        entry = (ROOT / "02-studio.ok").read_text("utf-8")
        declaration = 'object second @ "second": shapes.Shell {'
        override = '''
        palette = keyed<SurfaceMaterial> {
            "clay": surface_material(rgba(0.6, 0.3, 0.2, 1), 0, 0.8),
            "paint": surface_material(rgba(0.8, 0.2, 0.1, 0.5), 0.9, 0.1)
        };
'''
        changed = studio_bundle(entry=entry.replace(declaration, declaration + override))
        compiler = compile_construction(changed, level="evaluated")
        result = export_glb(compiler.model, target_contract=CONTRACT, options=ExportOptions(helpers=False))
        decoded = DecodedGLB(result.data)
        self.assertEqual(changed.modules[0].raw, self.sealed.modules[0].raw)
        self.assertNotEqual(changed.program_revision, self.sealed.program_revision)
        self.assertEqual(result.report["program_revision"], changed.program_revision)
        self.assertEqual(mesh_content(decoded, "first"), mesh_content(self.decoded, "first"))
        before, after = mesh_content(self.decoded, "second"), mesh_content(decoded, "second")
        self.assertEqual(before["clay"], after["clay"])
        self.assertEqual(before["paint"]["faces"], after["paint"]["faces"])
        self.assertNotEqual(before["paint"]["pbr"], after["paint"]["pbr"])
        self.assertEqual(after["paint"]["pbr"], {
            "baseColorFactor": [.8, .2, .1, .5], "metallicFactor": .9, "roughnessFactor": .1})

    def test_occurrence_section_repair_and_reorder_preserve_sibling_and_authored_keys(self):
        entry = (ROOT / "02-studio.ok").read_text("utf-8")
        changed = studio_bundle(entry=entry.replace("0.48[m], 0.38[m]", "0.52[m], 0.38[m]"))
        compiler = compile_construction(changed, level="evaluated")
        result = export_glb(compiler.model, target_contract=CONTRACT, options=ExportOptions(helpers=False))
        decoded = DecodedGLB(result.data)
        self.assertEqual(changed.modules[0].raw, self.sealed.modules[0].raw)
        self.assertEqual(mesh_content(decoded, "first"), mesh_content(self.decoded, "first"))
        self.assertNotEqual(mesh_content(decoded, "second"), mesh_content(self.decoded, "second"))
        _, node = decoded.source_node("second")
        self.assertEqual(node["extras"]["ontokin"]["surface"]["section_keys"], ["foot", "middle", "tip"])
        positions = decoded.accessor(mesh_primitives(decoded, "second")[0]["attributes"]["POSITION"])
        middle = [p for p in positions if abs(p[2] - .8) < 1e-6]
        self.assertAlmostEqual(max(p[0] for p in middle), .72, delta=1e-6)
        a, _, _, sealed_a = render(single_source(DEFAULT_SECTIONS))
        b, _, _, sealed_b = render(single_source(list(reversed(DEFAULT_SECTIONS))))
        self.assertNotEqual(sealed_a.program_revision, sealed_b.program_revision)
        self.assertEqual(mesh_content(a, "shell"), mesh_content(b, "shell"))

    def test_noncommuting_visual_placement_and_carrier_rotation_are_separate(self):
        placement = "pose(self.frame, vec3(0.3[m], 0.4[m], 0.5[m]), axis_angle(vec3(0, 1, 0), 90[deg]))"
        objects = '''object shell @ "shell": Shell {
            placement = pose(world, vec3(2[m], 3[m], 4[m]), axis_angle(vec3(1, 0, 0), 90[deg]));
        }'''
        scene = '''action drift @ "drift" = move(shell, vector(world, 1[m/s], 0[m/s], 0[m/s]), 2[s]);
        action turn @ "turn" = spin(shell, vector(world, 0[rad/s], 0[rad/s], 1[rad/s]), 2[s]);
        at 0[s] sequence { start drift; start turn; }'''
        decoded, _, compiler, _ = render(single_source(placement=placement, objects=objects, scene=scene))
        self.assertEqual(len(decoded.document["nodes"]), 1)
        self.assertEqual(len(compiler.model.objects), 1)
        positions = decoded.accessor(mesh_primitives(decoded, "shell")[0]["attributes"]["POSITION"])
        # Ry(90) * (0.5, 0, 0) + (0.3, 0.4, 0.5) = (0.3, 0.4, 0).
        point = min(positions, key=lambda p: math.dist(p, (.3, .4, 0)))
        self.assertVector(point, (.3, .4, 0), 1e-6)
        cap_normals = [normals[0] for face, normals in triangles(decoded, mesh_primitives(decoded, "shell")[0])
                       if max(p[0] for p in face) - min(p[0] for p in face) < 1e-6]
        self.assertTrue(any(math.dist(n, (-1, 0, 0)) < 1e-6 for n in cap_normals))
        self.assertTrue(any(math.dist(n, (1, 0, 0)) < 1e-6 for n in cap_normals))
        for t in (0, .125, .5, 1, 1.75, 2):
            pose = decoded.node_pose("shell", t)
            self.assertVector(pose["translation"], (2 + t, 3, 4), 1e-6)
            h = math.sqrt(.5)
            expected_q = (h * math.cos(t / 2), h * math.sin(t / 2),
                          h * math.sin(t / 2), h * math.cos(t / 2))
            self.assertLessEqual(min(math.dist(pose["rotation"], expected_q),
                                     math.dist(pose["rotation"], tuple(-x for x in expected_q))), 1e-6)
            # Independently rotate the selected stored vertex by the decoded quaternion.
            qx, qy, qz, qw = pose["rotation"]
            axis = (qx, qy, qz)
            term = tuple(2 * v for v in cross(axis, point))
            extra = cross(axis, term)
            actual = tuple(p + qw * v + w + origin
                           for p, v, w, origin in zip(point, term, extra, pose["translation"]))
            # Carrier Rx(90), then world Rz(t): local (.3,.4,0) -> (.3*cos(t),.3*sin(t),.4).
            self.assertVector(actual, (2 + t + .3 * math.cos(t), 3 + .3 * math.sin(t), 4.4), 2e-6)

    def test_generated_native_surface_release_retains_sphere_proxy_mass_and_motion(self):
        source = RELEASE_SOURCE.replace('ontokin "0.2";', 'ontokin "0.3";').replace(
            'profile "construction-0.1";', 'profile "surface-0.1";')
        source = source.replace("geometry = sphere(self.radius);", surface_members(
            placement="pose(self.frame, vec3(0[m], 0[m], 0.1[m]), axis_angle(vec3(1, 0, 0), 90[deg]))"))
        decoded, _, compiler, _ = render(source)
        self.assertEqual(len(decoded.document["nodes"]), 3)
        self.assertEqual(compiler.model.owned_mass("rig"), 2)
        for t in (0, .5, 1, 1.25, 1.5, 2):
            tau = max(0, t - 1)
            self.assertVector(decoded.node_pose('rig.balls["one"]', t)["translation"],
                              (t + .5, 2 - 5 * tau * tau, 0), .001)
            self.assertVector(decoded.node_pose('rig.balls["two"]', t)["translation"],
                              (t + .5, 2, 0), .001)
        _, node = decoded.source_node('rig.balls["one"]')
        self.assertEqual(node["extras"]["ontokin"]["physical"]["kind"], "sphere_body")
        self.assertEqual(node["extras"]["ontokin"]["surface"]["physical_participation"], "none")
        self.assertEqual(node["extras"]["ontokin"]["source_mapping"]["generated"]["key"], "one")

    def test_contract_selection_preserves_old_source_and_output_profiles(self):
        for wrong in ("ontokin.glb/0.1", "ontokin.glb/0.2"):
            with self.subTest(target=wrong), self.assertRaises(OntoKinError):
                export_glb(self.compiler.model, target_contract=wrong)
            with self.assertRaises(OntoKinError):
                validate_export(self.result.data, self.compiler.model, target_contract=wrong)
        core = validate(parse(simple_source()), level="evaluated")
        construction = compile_construction(construction_bundle(RELEASE_SOURCE), level="evaluated").model
        for model in (core, construction):
            with self.subTest(profile=model.profile), self.assertRaises(OntoKinError):
                export_glb(model, target_contract=CONTRACT)
        self.assertEqual(export_glb(core).report["target_contract"], "ontokin.glb/0.1")
        self.assertEqual(export_glb(construction, target_contract="ontokin.glb/0.2").report["target_contract"],
                         "ontokin.glb/0.2")

    def test_same_program_exports_deterministically_without_mutation(self):
        original = copy.deepcopy(self.compiler.model)
        repeated = export_glb(self.compiler.model, target_contract=CONTRACT,
                              source_uri="surface-studio.bundle.json", source_sha256=self.sealed.entry.revision,
                              options=ExportOptions(helpers=False))
        self.assertEqual(repeated.data, self.result.data)
        self.assertEqual(self.compiler.model, original)

    def test_serialized_source_revision_and_surface_summary_tampering_is_rejected(self):
        index, _ = self.decoded.source_node("first")
        mutations = {
            "program revision": lambda d: d["extras"]["ontokin"]["program"].update(revision="sha256:" + "0" * 64),
            "entry revision": lambda d: d["extras"]["ontokin"]["source"].update(entry_revision="sha256:" + "0" * 64),
            "library revision": lambda d: d["extras"]["ontokin"]["program"]["sources"]["package:fixture.surface-parts@1.0.0"].update(source_revision="sha256:" + "0" * 64),
            "occurrence": lambda d: d["nodes"][index]["extras"]["ontokin"]["source_mapping"].update(path="second"),
            "section order": lambda d: d["nodes"][index]["extras"]["ontokin"]["surface"].update(section_keys=["tip", "neck", "foot"]),
            "caps": lambda d: d["nodes"][index]["extras"]["ontokin"]["surface"].update(caps="none"),
            "local placement": lambda d: d["nodes"][index]["extras"]["ontokin"]["surface"]["local_visual_placement"].update(position_m=[1, 0, 0]),
            "animation profile": lambda d: d["animations"][0]["extras"]["ontokin"].update(target_contract="ontokin.glb/0.2"),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                document = copy.deepcopy(self.decoded.document)
                mutate(document)
                self.assertRejected(document)

    def test_changed_source_dependency_cannot_relabel_identical_numerical_output(self):
        revised_library = self.sealed.modules[0].raw + b"\n// Revised source bytes, unchanged shape.\n"
        changed = studio_bundle(library=revised_library)
        compiler = compile_construction(changed, level="evaluated")
        self.assertNotEqual(changed.program_revision, self.sealed.program_revision)
        with self.assertRaises(OntoKinError):
            validate_export(self.result.data, compiler.model, target_contract=CONTRACT)
        with self.assertRaises(OntoKinError):
            export_glb(self.compiler.model, target_contract=CONTRACT, source_sha256=self.sealed.program_revision)

    def test_material_factors_assignment_and_region_labels_are_validated(self):
        primitive = mesh_primitives(self.decoded, "first")[0]
        material_index = primitive["material"]
        for field, value in (("baseColorFactor", [.9, .9, .9, 1]),
                             ("metallicFactor", .75), ("roughnessFactor", .05)):
            with self.subTest(field=field):
                document = copy.deepcopy(self.decoded.document)
                document["materials"][material_index]["pbrMetallicRoughness"][field] = value
                self.assertRejected(document)
        _, node = self.decoded.source_node("first")
        for field in ("material", "indices", "region_key"):
            with self.subTest(field=field):
                document = copy.deepcopy(self.decoded.document)
                first, second = document["meshes"][node["mesh"]]["primitives"]
                if field == "region_key":
                    first["extras"]["ontokin"]["region_key"] = "paint"
                else:
                    first[field], second[field] = second[field], first[field]
                self.assertRejected(document)

    def test_winding_and_normals_tampering_reads_real_bin_values(self):
        primitive = mesh_primitives(self.decoded, "first")[0]
        indices = self.decoded.accessor(primitive["indices"])
        binary = bytearray(self.decoded.binary)
        change_accessor(binary, self.decoded.document, primitive["indices"], 0, indices[1])
        change_accessor(binary, self.decoded.document, primitive["indices"], 1, indices[0])
        self.assertRejected(self.decoded.document, binary)
        normals = self.decoded.accessor(primitive["attributes"]["NORMAL"])
        binary = bytearray(self.decoded.binary)
        change_accessor(binary, self.decoded.document, primitive["attributes"]["NORMAL"], indices[0][0],
                        tuple(-v for v in normals[indices[0][0]]))
        self.assertRejected(self.decoded.document, binary)

    def test_surface_vertex_tolerance_cannot_be_weakened_by_animation_options(self):
        primitive = mesh_primitives(self.decoded, "first")[0]
        positions = self.decoded.accessor(primitive["attributes"]["POSITION"])
        index = next(i for i, p in enumerate(positions) if -.25 < p[0] < .25)
        binary = bytearray(self.decoded.binary)
        shifted = (positions[index][0] + .0001, *positions[index][1:])
        change_accessor(binary, self.decoded.document, primitive["attributes"]["POSITION"], index, shifted)
        self.assertRejected(self.decoded.document, binary,
                            options=ExportOptions(helpers=False, position_tolerance_m=1.0))

    def test_repeated_instances_charge_aggregate_export_geometry_budget(self):
        _, compiler = compile_source(single_source(objects='''
            object first @ "first": Shell {}
            object second @ "second": Shell {}
        '''))
        original = copy.deepcopy(compiler.model)
        # Each closed 2-section/16-facet native surface has 192 vertices.
        with patch("ontokin.scene.MAX_MESH_VERTICES", 383), self.assertRaises(OntoKinError) as caught:
            export_glb(compiler.model, target_contract=CONTRACT)
        self.assertEqual(caught.exception.code, "OKL-E-RESOURCE")
        self.assertEqual(caught.exception.diagnostic.details["target_contract"], CONTRACT)
        self.assertEqual(compiler.model, original)
        self.assertEqual(export_glb(compiler.model, target_contract=CONTRACT).report["outcome"], "valid")

    def test_binary_byte_limit_fails_without_returning_partial_artifact(self):
        original = copy.deepcopy(self.compiler.model)
        with patch("ontokin.gltf.MAX_GLB_BYTES", 1024), self.assertRaises(OntoKinError) as caught:
            export_glb(self.compiler.model, target_contract=CONTRACT)
        self.assertEqual(caught.exception.code, "OKL-E-RESOURCE")
        self.assertEqual(caught.exception.diagnostic.details["target_contract"], CONTRACT)
        self.assertEqual(self.compiler.model, original)

    def test_export_and_validation_cancellation_propagate_original_exception(self):
        original = copy.deepcopy(self.compiler.model)
        for operation in ("export", "validate"):
            visits = 0
            def count():
                nonlocal visits
                visits += 1
            def run(check):
                if operation == "export":
                    return export_glb(self.compiler.model, target_contract=CONTRACT,
                                      options=ExportOptions(helpers=False), check=check)
                return validate_export(self.result.data, self.compiler.model, target_contract=CONTRACT,
                                       options=ExportOptions(helpers=False), check=check)
            run(count)
            total = visits
            self.assertGreater(total, 10, "Cancellation must be checked inside the bounded work")
            for at in (1, total // 2, total - 1):
                with self.subTest(operation=operation, checkpoint=at):
                    sentinel = ValueError("Cancellation from the caller, not malformed GLB")
                    visits = 0
                    def cancel():
                        nonlocal visits
                        visits += 1
                        if visits >= at:
                            raise sentinel
                    with self.assertRaises(ValueError) as caught:
                        run(cancel)
                    self.assertIs(caught.exception, sentinel)
                    self.assertEqual(self.compiler.model, original)
                    self.assertEqual(self.compiler.model.program_revision, self.sealed.program_revision)


class NativeSurfaceSourceFailureTests(unittest.TestCase):
    def test_invalid_source_cannot_replace_previously_compiled_geometry(self):
        sealed, accepted = compile_source(single_source())
        original = copy.deepcopy(accepted.model)
        invalid = [
            ([("only", 0, 0, 0, .5, .5, "blue")], "OKL-E-SURFACE-SECTION"),
            ([DEFAULT_SECTIONS[0], ("other", 0, 0, 0, .5, .5, "blue")], "OKL-E-SURFACE-STATION"),
            ([DEFAULT_SECTIONS[0], ("other", .000999, 0, 0, .5, .5, "blue")], "OKL-E-SURFACE-STATION"),
            ([("bottom", 0, 0, 0, 0, .5, "blue"), DEFAULT_SECTIONS[1]], "OKL-E-SURFACE-RADIUS"),
            ([DEFAULT_SECTIONS[0], ("top", 2, 0, 0, .5, .5, "missing")], "OKL-E-SURFACE-REGION"),
        ]
        for sections, expected in invalid:
            with self.subTest(error=expected), self.assertRaises(OntoKinError) as caught:
                compile_source(single_source(sections))
            self.assertEqual(caught.exception.code, expected)
            self.assertEqual(accepted.model, original)
            self.assertEqual(accepted.model.program_revision, sealed.program_revision)

    def test_native_source_rejects_invalid_caps_facets_and_world_visual_frame(self):
        inputs = [({"caps": "rounded"}, "OKL-E-SURFACE-CAPS"),
                  ({"facets": 9}, "OKL-E-SURFACE-FACETS"),
                  ({"facets": 68}, "OKL-E-SURFACE-FACETS"),
                  ({"placement": "pose(world, vec3(0[m], 0[m], 0[m]), quat(1,0,0,0))"},
                   "OKL-E-SURFACE-PLACEMENT")]
        for kwargs, expected in inputs:
            with self.subTest(kwargs=kwargs), self.assertRaises(OntoKinError) as caught:
                compile_source(single_source(**kwargs))
            self.assertEqual(caught.exception.code, expected)


if __name__ == "__main__":
    unittest.main()
