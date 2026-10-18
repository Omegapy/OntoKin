"""Check actual GLB bytes against source geometry and analytical trajectories.

The decoder and playback interpolation below do not call the exporter's reader
or sampler. That separation catches a writer and its own validator agreeing on
the same incorrect buffer, quaternion order, hierarchy, or interpolation.
"""

from __future__ import annotations

from bisect import bisect_right
import copy
from fractions import Fraction
import hashlib
import json
import math
import re
import struct
import unittest

from ontokin.diagnostics import OntoKinError, Source
from ontokin.fixtures import DEFAULT_FIXTURES, load_manifest, materialize
from ontokin.gltf import export_glb, validate_export
from ontokin.scene import ExportOptions
from ontokin.syntax import parse
from ontokin.validator import validate


class DecodedGLB:
    """Read only the core GLB/accessor/animation features this target promises."""

    def __init__(self, data):
        magic, version, length = struct.unpack_from("<4sII", data)
        if (magic, version, length) != (b"glTF", 2, len(data)):
            raise AssertionError("Invalid GLB header")
        chunks = []
        offset = 12
        while offset < len(data):
            size, kind = struct.unpack_from("<II", data, offset)
            if size % 4 or offset + 8 + size > len(data):
                raise AssertionError("Invalid GLB chunk alignment or length")
            chunks.append((kind, data[offset + 8:offset + 8 + size]))
            offset += 8 + size
        if offset != len(data) or [kind for kind, _ in chunks] != [0x4E4F534A, 0x004E4942]:
            raise AssertionError("Expected embedded JSON and BIN chunks")
        self.document = json.loads(chunks[0][1])
        self.binary = chunks[1][1]
        if self.document["asset"]["version"] != "2.0":
            raise AssertionError("Expected glTF 2.0")
        buffer = self.document["buffers"][0]
        if "uri" in buffer or not 0 <= len(self.binary) - buffer["byteLength"] <= 3:
            raise AssertionError("Expected one correctly padded embedded buffer")

    def accessor(self, index):
        accessor = self.document["accessors"][index]
        view = self.document["bufferViews"][accessor["bufferView"]]
        if view.get("buffer", 0) != 0 or "sparse" in accessor:
            raise AssertionError("Unexpected external or sparse data")
        arity = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[accessor["type"]]
        component = {5121: "B", 5123: "H", 5125: "I", 5126: "f"}[accessor["componentType"]]
        fmt = "<" + component * arity
        size = struct.calcsize(fmt)
        stride = view.get("byteStride", size)
        offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
        end = offset + (accessor["count"] - 1) * stride + size
        if end > view.get("byteOffset", 0) + view["byteLength"]:
            raise AssertionError("Accessor extends beyond its buffer view")
        return [struct.unpack_from(fmt, self.binary, offset + i * stride)
                for i in range(accessor["count"])]

    def source_node(self, path):
        found = [(i, node) for i, node in enumerate(self.document["nodes"])
                 if node.get("extras", {}).get("ontokin", {}).get("kind") == "object"
                 and node["extras"]["ontokin"]["path"] == path]
        if len(found) != 1:
            raise AssertionError(f"Expected one stable source node for {path}")
        return found[0]

    def node_pose(self, path, time):
        index, node = self.source_node(path)
        if "matrix" in node:
            raise AssertionError("Animated source nodes must use TRS")
        pose = {"translation": tuple(node.get("translation", (0, 0, 0))),
                "rotation": tuple(node.get("rotation", (0, 0, 0, 1)))}
        for animation in self.document.get("animations", []):
            for channel in animation["channels"]:
                if channel["target"]["node"] != index:
                    continue
                target = channel["target"]["path"]
                sampler = animation["samplers"][channel["sampler"]]
                times = [v[0] for v in self.accessor(sampler["input"])]
                values = self.accessor(sampler["output"])
                if len(times) != len(values) or any(a >= b for a, b in zip(times, times[1:])):
                    raise AssertionError("Invalid animation input/output cardinality or ordering")
                if sampler.get("interpolation", "LINEAR") != "LINEAR":
                    raise AssertionError("This target promises LINEAR keys")
                if time <= times[0]:
                    value = values[0]
                elif time >= times[-1]:
                    value = values[-1]
                else:
                    left = bisect_right(times, time) - 1
                    weight = (time - times[left]) / (times[left + 1] - times[left])
                    a, b = values[left], values[left + 1]
                    value = (slerp(a, b, weight) if target == "rotation" else
                             tuple(x + (y - x) * weight for x, y in zip(a, b)))
                pose[target] = value
        return pose

    def animation_times(self):
        return {v[0] for animation in self.document.get("animations", [])
                for sampler in animation["samplers"]
                for v in self.accessor(sampler["input"])}


def slerp(a, b, weight):
    a = tuple(x / math.hypot(*a) for x in a)
    b = tuple(x / math.hypot(*b) for x in b)
    dot = sum(x * y for x, y in zip(a, b))
    if dot < 0:
        b, dot = tuple(-x for x in b), -dot
    if dot > 0.9995:
        value = tuple(x + weight * (y - x) for x, y in zip(a, b))
    else:
        angle = math.acos(min(1, dot))
        left = math.sin((1 - weight) * angle) / math.sin(angle)
        right = math.sin(weight * angle) / math.sin(angle)
        value = tuple(left * x + right * y for x, y in zip(a, b))
    return tuple(x / math.hypot(*value) for x in value)


def encode_glb(document, binary):
    """Repackage independent mutations without the production GLB writer."""
    encoded = json.dumps(document, ensure_ascii=False, allow_nan=False,
                         separators=(",", ":")).encode("utf-8")
    encoded += b" " * (-len(encoded) % 4)
    binary = bytes(binary) + b"\0" * (-len(binary) % 4)
    chunks = (struct.pack("<II", len(encoded), 0x4E4F534A) + encoded
              + struct.pack("<II", len(binary), 0x004E4942) + binary)
    return struct.pack("<4sII", b"glTF", 2, 12 + len(chunks)) + chunks


def simple_source(*, geometry="box(vec3(2[m], 4[m], 6[m]))", placement="0[m]",
                  extra_class="", extra_object="", extra_scene="", duration="1[s]"):
    return f'''ontokin "0.1";
module ExportCase @ "export-case";
profile "core-0.1";
class Shape @ "shape" {{
    geometry = {geometry};
    appearance = rgba(0.125, 0.25, 0.5, 0.35);
    {extra_class}
}}
scene Demo @ "demo" {{
    duration = {duration};
    gravity = vector(world, 0[m/s^2], -9.81[m/s^2], 0[m/s^2]);
    object body @ "body": Shape {{
        placement = pose(world, vec3({placement}, 0[m], 0[m]),
                         axis_angle(vec3(1, 0, 0), 90[deg]));
        {extra_object}
    }}
    {extra_scene}
}}
'''


CHAIN_SOURCE = '''ontokin "0.1";
module Chain @ "chain";
profile "core-0.1";
class Root @ "root-type" { geometry = box(vec3(0.2[m], 0.2[m], 0.2[m])); }
class Link @ "link-type" {
    public site tip @ "tip" {
        pose = pose(self.frame, vec3(0.5[m], 0[m], 0[m]), quat(1, 0, 0, 0));
        interface = "rigid.origin"; size = 0[m];
    }
}
class Payload @ "payload-type" {
    geometry = sphere(0.1[m]); physical = sphere_body(0.1[m], 1[kg]);
    public site mount @ "mount" {
        pose = pose(self.frame, vec3(0.2[m], 0[m], 0[m]),
                    axis_angle(vec3(0, 0, 1), 0.4[rad]));
        interface = "rigid.origin"; size = 0[m];
    }
}
class Label @ "label-type" { geometry = box(vec3(0.05[m], 0.05[m], 0.05[m])); }
scene Demo @ "demo" {
    duration = 2[s];
    gravity = vector(world, 0[m/s^2], -9.81[m/s^2], 0[m/s^2]);
    object root @ "root": Root {
        placement = pose(world, vec3(0[m], 2[m], 0[m]),
                         axis_angle(vec3(0, 0, 1), -1[rad]));
    }
    object link @ "link": Link {}
    object hand @ "hand": Object {}
    object payload @ "payload": Payload {}
    object label @ "label": Label {}
    joint yaw @ "yaw": hinge {
        parent = root.origin; child = link.origin; axis = vec3(0, 0, 1);
        limits = range(-2[rad], 2[rad]); initial = 0[rad];
    }
    joint reach @ "reach": slider {
        parent = link.tip; child = hand.origin; axis = vec3(1, 0, 0);
        limits = range(0[m], 1[m]); initial = 0.25[m];
    }
    joint hold @ "hold": grip { parent = hand.origin; child = payload.mount; }
    follow caption @ "caption" {
        parent = payload.frame; child = label;
        offset = pose(payload.frame, vec3(0[m], 0.5[m], 0[m]), quat(1, 0, 0, 0));
    }
    action translate @ "translate" = move(root, vector(world, 1[m/s], 0[m/s], 0[m/s]), 2[s]);
    action rotate @ "rotate" = spin(root, vector(world, 0[rad/s], 0[rad/s], 2[rad/s]), 2[s]);
    action turn @ "turn" = tween(yaw, 1[rad], 1[s]);
    action extend @ "extend" = tween(reach, 0.75[m], 1[s]);
    at 0[s] sequence { start translate; start rotate; start turn; start extend; }
    at 1[s] sequence { release hold using incoming; }
}
'''


class ExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = {c["id"]: c for c in load_manifest()["cases"]}
        cls.base = {}
        for case_id in ("P01", "P02", "P03", "P04"):
            source = materialize(cls.cases[case_id])
            model = validate(parse(source), level="evaluated")
            result = export_glb(model, options=ExportOptions(helpers=False),
                                source_uri=cls.cases[case_id]["source"]["base_file"],
                                source_sha256=hashlib.sha256(source.encode()).hexdigest())
            cls.base[case_id] = (DecodedGLB(result.data), result, model, source)

    def build(self, source, **options):
        model = validate(parse(source), level="evaluated")
        result = export_glb(model, options=ExportOptions(**{"helpers": False, **options}))
        return DecodedGLB(result.data), result, model

    def assertVector(self, actual, expected, tolerance=0.001):
        self.assertEqual(len(actual), len(expected))
        self.assertLessEqual(max(abs(a - e) for a, e in zip(actual, expected)), tolerance,
                             f"{actual} differs from {expected}")

    def assertRotation(self, actual_xyzw, expected_xyzw, tolerance=0.001):
        actual = tuple(x / math.hypot(*actual_xyzw) for x in actual_xyzw)
        expected = tuple(x / math.hypot(*expected_xyzw) for x in expected_xyzw)
        if sum(a * e for a, e in zip(actual, expected)) < 0:
            expected = tuple(-x for x in expected)
        chord = math.hypot(*(a - e for a, e in zip(actual, expected)))
        self.assertLessEqual(4 * math.asin(min(1, chord / 2)), tolerance)

    def test_p01_world_translation_and_independent_head_and_hand(self):
        glb = self.base["P01"][0]
        for t in (0, 0.125, 0.5, 1, 1.5, 2, 3):
            with self.subTest(time=t):
                x = min(t, 2)
                self.assertVector(glb.node_pose("rig", t)["translation"], (x, 0, 0))
                self.assertVector(glb.node_pose("rig.head", t)["translation"], (x, 1, 0))
                self.assertVector(glb.node_pose("rig.arm.hand", t)["translation"],
                                  (0.25 + 1.25 * min(t, 2), 0.5, 0))
                half_angle = math.pi * min(t, 1) / 4
                self.assertRotation(glb.node_pose("rig.head", t)["rotation"],
                                    (0, math.sin(half_angle), 0, math.cos(half_angle)))

    def test_p02_release_has_world_trajectory_and_no_implicit_ground(self):
        glb = self.base["P02"][0]
        for t in (0, 0.5, 0.999, 1, 1.001, 1.5, 1.875, 2):
            with self.subTest(time=t):
                delta = max(0, t - 1)
                self.assertVector(glb.node_pose("payload", t)["translation"],
                                  (t, 2 - 4.905 * delta * delta, 0))
                self.assertVector(glb.node_pose("carrier", t)["translation"], (t, 2, 0))
        self.assertLess(glb.node_pose("payload", 2)["translation"][1], 0)

    def test_p03_release_preserves_tangential_velocity_and_angular_motion(self):
        glb = self.base["P03"][0]
        for t in (0, 0.25, 0.875, 1, 1.5, 2):
            with self.subTest(time=t):
                if t <= 1:
                    theta = 2 * t - 2
                    expected = (t + 0.5 * math.cos(theta), 2 + 0.5 * math.sin(theta), 0)
                else:
                    delta = t - 1
                    expected = (1.5 + delta, 2 + delta - 4.905 * delta * delta, 0)
                self.assertVector(glb.node_pose("payload", t)["translation"], expected)
                self.assertRotation(glb.node_pose("payload", t)["rotation"],
                                    (0, 0, math.sin(t - 1), math.cos(t - 1)))

    def test_p04_ownership_and_follow_remain_different_relationships(self):
        glb = self.base["P04"][0]
        for t in (0, 0.125, 0.5, 0.875, 1):
            with self.subTest(time=t):
                y = 2 - 4.905 * t * t
                self.assertVector(glb.node_pose("first", t)["translation"], (t, 0, 0))
                for path in ("first.ball", "second.ball"):
                    self.assertVector(glb.node_pose(path, t)["translation"], (0, y, 0))
                self.assertVector(glb.node_pose("label", t)["translation"], (0, y + 0.5, 0))

    def test_all_source_nodes_are_world_roots_with_stable_identity(self):
        for case_id, (glb, _, model, _) in self.base.items():
            roots = set(glb.document["scenes"][glb.document.get("scene", 0)]["nodes"])
            child_indices = {i for node in glb.document["nodes"] for i in node.get("children", [])}
            for path, obj in model.objects.items():
                with self.subTest(case=case_id, object=path):
                    index, node = glb.source_node(path)
                    metadata = node["extras"]["ontokin"]
                    self.assertIn(index, roots)
                    self.assertNotIn(index, child_indices)
                    self.assertEqual(node.get("scale", [1, 1, 1]), [1, 1, 1])
                    self.assertEqual(metadata["element_id"], list(obj.element_id))
                    self.assertEqual(metadata["owner"], obj.owner)
                    self.assertEqual(metadata["pose_frame"], "world")
                    self.assertEqual(metadata["collision"], "disabled")

    def test_release_survives_pause_completion_and_carrier_replacement(self):
        for case_id, expected in (("P05", (1.25, 2, 0)), ("P07", (2, 2, 0))):
            with self.subTest(case=case_id):
                glb, _, _ = self.build(materialize(self.cases[case_id]))
                self.assertVector(glb.node_pose("carrier", 1.5)["translation"], expected)
                self.assertVector(glb.node_pose("payload", 1.5)["translation"], (1.5, 0.77375, 0))
        # Extend the P06 observation horizon so its incoming-state handoff is
        # visible after the carrier has naturally completed at t=2.
        source = materialize(self.cases["P06"]).replace("duration = 2[s];", "duration = 3[s];")
        glb, _, _ = self.build(source)
        self.assertVector(glb.node_pose("carrier", 2.5)["translation"], (2, 2, 0))
        self.assertVector(glb.node_pose("payload", 2.5)["translation"], (2.5, 0.77375, 0))

    def test_stop_root_preserves_local_action_and_completed_head_angle(self):
        glb, _, _ = self.build(materialize(self.cases["P12"]))
        self.assertVector(glb.node_pose("rig.arm.hand", 1.5)["translation"], (1.625, 0.5, 0))
        self.assertRotation(glb.node_pose("rig.head", 1.5)["rotation"],
                            (0, math.sqrt(0.5), 0, math.sqrt(0.5)))

    def test_nonzero_child_site_and_local_joint_rates_transfer_through_release(self):
        glb, _, _ = self.build(CHAIN_SOURCE)
        ox = 1.25 * math.cos(2) - 0.2 * math.cos(1.6)
        oy = 1.25 * math.sin(2) - 0.2 * math.sin(1.6)
        vx = 1 + 0.5 * math.cos(2) - 3 * oy
        vy = 0.5 * math.sin(2) + 3 * ox
        for t in (1, 1.5, 2):
            delta = t - 1
            position = (1 + ox + vx * delta, 2 + oy + vy * delta - 4.905 * delta * delta, 0)
            angle = 1.6 + 3 * delta
            self.assertVector(glb.node_pose("payload", t)["translation"], position)
            self.assertRotation(glb.node_pose("payload", t)["rotation"],
                                (0, 0, math.sin(angle / 2), math.cos(angle / 2)))
            self.assertVector(glb.node_pose("label", t)["translation"],
                              (position[0] - 0.5 * math.sin(angle),
                               position[1] + 0.5 * math.cos(angle), 0))

    def test_world_spin_multiplies_noncommuting_initial_orientation_on_left(self):
        for dynamic in (False, True):
            with self.subTest(dynamic=dynamic):
                if dynamic:
                    source = simple_source(extra_class="physical = sphere_body(0.2[m], 1[kg]); motion = dynamic;",
                                           extra_object="omega = vector(world, 0[rad/s], 0[rad/s], 2[rad/s]);")
                else:
                    source = simple_source(extra_scene='''
                        action turn @ "turn" = spin(body, vector(world, 0[rad/s], 0[rad/s], 2[rad/s]), 1[s]);
                        at 0[s] sequence { start turn; }''')
                glb, _, _ = self.build(source)
                for t in (0, 0.125, 0.5, 1):
                    h = math.sqrt(0.5)
                    self.assertRotation(glb.node_pose("body", t)["rotation"],
                                        (h * math.cos(t), h * math.sin(t), h * math.sin(t), h * math.cos(t)))

    def test_low_requested_fps_cannot_alias_multiple_complete_turns(self):
        speed = 16 * math.pi
        source = simple_source(extra_scene=f'''
            action turn @ "turn" = spin(body, vector(world, 0[rad/s], 0[rad/s], {speed!r}[rad/s]), 1[s]);
            at 0[s] sequence {{ start turn; }}''')
        glb, _, _ = self.build(source, fps=1)
        self.assertGreater(len(glb.animation_times()), 16)
        h = math.sqrt(0.5)
        for t in (0.015625, 0.03125, 0.123, 0.257, 0.499, 0.753, 1):
            with self.subTest(time=t):
                theta = speed * t / 2
                self.assertRotation(glb.node_pose("body", t)["rotation"],
                                    (h * math.cos(theta), h * math.sin(theta), h * math.sin(theta), h * math.cos(theta)))
        for animation in glb.document["animations"]:
            for channel in animation["channels"]:
                if channel["target"]["path"] == "rotation":
                    sampler = animation["samplers"][channel["sampler"]]
                    values = glb.accessor(sampler["output"])
                    for a, b in zip(values, values[1:]):
                        self.assertGreaterEqual(sum(x * y for x, y in zip(a, b)), 0)

    def test_event_and_natural_completion_boundaries_are_explicit_keys(self):
        source = simple_source(duration="2[s]", extra_scene='''
            action advance @ "advance" = move(body, vector(world, 1[m/s], 0[m/s], 0[m/s]), 0.5[s]);
            at 0.1[s] sequence { start advance; }
            at 1.125[s] sequence {}
        ''')
        glb, result, _ = self.build(source, fps=7)
        expected = {Fraction(0), Fraction.from_float(0.1),
                    Fraction.from_float(0.1) + Fraction(1, 2), Fraction(9, 8), Fraction(2)}
        sampling = result.report["sampling"]
        self.assertEqual({Fraction(t) for t in sampling["boundary_times_seconds"]}, expected)
        mappings = {Fraction(item["source_seconds"]): item for item in sampling["boundary_time_mapping"]}
        for exact in expected:
            mapped = mappings[exact]
            self.assertLessEqual(abs(Fraction.from_float(mapped["export_seconds"]) - exact), Fraction(1, 1000000))
            self.assertIn(mapped["export_seconds"], glb.animation_times())

    def test_meshes_have_outward_winding_finite_unit_normals_and_valid_indices(self):
        for case_id, (glb, _, _, _) in self.base.items():
            for mesh in glb.document["meshes"]:
                for primitive in mesh["primitives"]:
                    with self.subTest(case=case_id, mesh=mesh.get("name")):
                        self.assertEqual(primitive.get("mode", 4), 4)
                        positions = glb.accessor(primitive["attributes"]["POSITION"])
                        normals = glb.accessor(primitive["attributes"]["NORMAL"])
                        indices = [v[0] for v in glb.accessor(primitive["indices"])]
                        self.assertEqual(len(positions), len(normals))
                        self.assertEqual(len(indices) % 3, 0)
                        self.assertTrue(all(0 <= i < len(positions) for i in indices))
                        self.assertTrue(all(math.isfinite(x) for v in positions + normals for x in v))
                        for normal in normals:
                            self.assertAlmostEqual(math.hypot(*normal), 1, delta=1e-6)
                        for i in range(0, len(indices), 3):
                            a, b, c = [positions[index] for index in indices[i:i + 3]]
                            u, v = [b[k] - a[k] for k in range(3)], [c[k] - a[k] for k in range(3)]
                            cross = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
                            self.assertGreater(math.hypot(*cross), 1e-12)
                            normal = normals[indices[i]]
                            self.assertGreater(sum(n * x for n, x in zip(normal, cross)), 0)

    def test_box_uses_full_lengths_and_visual_geometry_not_sphere_physics_proxy(self):
        source = simple_source(extra_class="physical = sphere_body(0.2[m], 1[kg]); motion = dynamic;")
        glb, _, _ = self.build(source)
        _, node = glb.source_node("body")
        primitive = glb.document["meshes"][node["mesh"]]["primitives"][0]
        positions = glb.accessor(primitive["attributes"]["POSITION"])
        self.assertVector(tuple(min(p[k] for p in positions) for k in range(3)), (-1, -2, -3), 1e-6)
        self.assertVector(tuple(max(p[k] for p in positions) for k in range(3)), (1, 2, 3), 1e-6)
        self.assertEqual(node["extras"]["ontokin"]["geometry"]["kind"], "box")
        self.assertEqual(node["extras"]["ontokin"]["physical"]["kind"], "sphere_body")

    def test_sphere_vertices_use_authored_radius_and_instance_overrides(self):
        glb = self.base["P04"][0]
        for path, radius in (("first.ball", 0.2), ("second.ball", 0.3)):
            _, node = glb.source_node(path)
            primitive = glb.document["meshes"][node["mesh"]]["primitives"][0]
            for position in glb.accessor(primitive["attributes"]["POSITION"]):
                self.assertAlmostEqual(math.hypot(*position), radius, delta=1e-6)

    def test_linear_rgba_and_alpha_are_preserved_in_material(self):
        glb, _, _ = self.build(simple_source())
        _, node = glb.source_node("body")
        primitive = glb.document["meshes"][node["mesh"]]["primitives"][0]
        material = glb.document["materials"][primitive["material"]]
        self.assertEqual(material["pbrMetallicRoughness"]["baseColorFactor"], [0.125, 0.25, 0.5, 0.35])
        self.assertEqual(material["alphaMode"], "BLEND")

    def test_helpers_are_separate_massless_glyphs_and_empty_source_geometry_stays_empty(self):
        source = self.base["P01"][3]
        glb, _, _ = self.build(source, helpers=True)
        _, root = glb.source_node("rig")
        self.assertNotIn("mesh", root)
        helpers = [node for node in glb.document["nodes"]
                   if node.get("extras", {}).get("ontokin", {}).get("kind") == "visual_helper"]
        self.assertTrue(helpers)
        kinds = set()
        for node in helpers:
            metadata = node["extras"]["ontokin"]
            kinds.add(metadata["helper_kind"])
            self.assertEqual(metadata["physical_participation"], "none")
            self.assertTrue(metadata["related_element_id"])
        self.assertIn("assembly_origin", kinds)
        self.assertIn("joint_parent_site", kinds)

    def test_identical_source_export_is_deterministic_and_does_not_mutate_model(self):
        _, previous, model, source = self.base["P03"]
        original = copy.deepcopy(model)
        repeated = export_glb(model, options=ExportOptions(helpers=False),
                              source_uri=self.cases["P03"]["source"]["base_file"],
                              source_sha256=hashlib.sha256(source.encode()).hexdigest())
        self.assertEqual(repeated.data, previous.data)
        self.assertEqual(model, original)

    def test_numerical_validation_reads_the_serialized_animation_bytes(self):
        glb, result, model, _ = self.base["P02"]
        payload_index, _ = glb.source_node("payload")
        animation = glb.document["animations"][0]
        channel = next(c for c in animation["channels"]
                       if c["target"] == {"node": payload_index, "path": "translation"})
        sampler = animation["samplers"][channel["sampler"]]
        accessor = glb.document["accessors"][sampler["output"]]
        view = glb.document["bufferViews"][accessor["bufferView"]]
        json_chunk_size = struct.unpack_from("<I", result.data, 12)[0]
        binary_start = 12 + 8 + json_chunk_size + 8
        offset = (binary_start + view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
                  + (accessor["count"] // 2) * view.get("byteStride", 12))
        corrupted = bytearray(result.data)
        original_x = struct.unpack_from("<f", corrupted, offset)[0]
        struct.pack_into("<f", corrupted, offset, original_x + 0.25)
        report = validate_export(bytes(corrupted), model, options=ExportOptions(helpers=False))
        self.assertEqual(report["status"], "failed")
        self.assertGreaterEqual(report["max_position_error_m"], 0.249)

    def test_modified_scale_or_default_transform_is_rejected(self):
        glb, _, model, _ = self.base["P02"]
        payload_index, payload = glb.source_node("payload")
        shifted = list(payload["translation"])
        shifted[0] += 0.25
        for property_name, value in (("scale", [2, 1, 1]),
                                     ("translation", shifted),
                                     ("rotation", [0, 0, 1, 0])):
            with self.subTest(property=property_name):
                document = copy.deepcopy(glb.document)
                document["nodes"][payload_index][property_name] = value
                data = encode_glb(document, glb.binary)
                with self.assertRaises(OntoKinError) as context:
                    validate_export(data, model, options=ExportOptions(helpers=False))
                self.assertEqual(context.exception.diagnostic.details["export_code"],
                                 "OKE-E-GLB-STRUCTURE")

    def test_coarsened_complete_turns_cannot_evade_independent_angular_bound(self):
        speed = 8 * math.pi
        source = simple_source(extra_scene=f'''
            action turn @ "turn" = spin(body, vector(world, 0[rad/s], 0[rad/s], {speed!r}[rad/s]), 1[s]);
            at 0[s] sequence {{ start turn; }}''')
        glb, _, model = self.build(source, fps=1)
        self.assertGreater(len(glb.animation_times()), 2)
        document = copy.deepcopy(glb.document)
        binary = bytearray(glb.binary[:document["buffers"][0]["byteLength"]])

        def append_accessor(rows, value_type):
            binary.extend(b"\0" * (-len(binary) % 4))
            offset = len(binary)
            for row in rows:
                binary.extend(struct.pack("<" + "f" * len(row), *row))
            view = len(document["bufferViews"])
            document["bufferViews"].append({"buffer": 0, "byteOffset": offset,
                                          "byteLength": len(binary) - offset})
            index = len(document["accessors"])
            document["accessors"].append({
                "bufferView": view, "componentType": 5126,
                "count": len(rows), "type": value_type,
                "min": [min(column) for column in zip(*rows)],
                "max": [max(column) for column in zip(*rows)],
            })
            return index

        clock = append_accessor([(0.,), (1.,)], "SCALAR")
        animation = document["animations"][0]
        for sampler in animation["samplers"]:
            values = glb.accessor(sampler["output"])
            value_type = document["accessors"][sampler["output"]]["type"]
            sampler["input"] = clock
            sampler["output"] = append_accessor([values[0], values[-1]], value_type)
        animation["extras"]["ontokin"]["exact_times_seconds"] = ["0", "1"]
        document["buffers"][0]["byteLength"] = len(binary)
        data = encode_glb(document, binary)
        coarsened = DecodedGLB(data)
        self.assertEqual(coarsened.animation_times(), {0., 1.})

        # Four full turns put all endpoint/quarter probes at equivalent poses.
        # A validator needs the source rotation-rate bound to detect this loss.
        h = math.sqrt(0.5)
        for t in (0, 0.25, 0.5, 0.75, 1):
            theta = speed * t / 2
            self.assertRotation(coarsened.node_pose("body", t)["rotation"],
                                (h * math.cos(theta), h * math.sin(theta),
                                 h * math.sin(theta), h * math.cos(theta)))
        with self.assertRaises(OntoKinError) as context:
            validate_export(data, model, options=ExportOptions(helpers=False))
        self.assertEqual(context.exception.diagnostic.details["export_code"],
                         "OKE-E-ROTATION-ALIAS")

    def test_equivalent_units_and_renamed_display_symbol_preserve_identity_and_geometry(self):
        for case_id in ("P08", "P09"):
            with self.subTest(case=case_id):
                glb, _, _ = self.build(materialize(self.cases[case_id]))
                path = "rig.arm.palm" if case_id == "P09" else "rig.arm.hand"
                _, node = glb.source_node(path)
                self.assertEqual(node["extras"]["ontokin"]["element_id"],
                                 ["independent-parts", "demo", "rig", "arm", "hand"])
                self.assertVector(glb.node_pose(path, 1.5)["translation"], (2.125, 0.5, 0))
                _, original = self.base["P01"][0].source_node("rig.head")
                _, current = glb.source_node("rig.head")
                self.assertEqual(current["extras"]["ontokin"]["geometry"], original["extras"]["ontokin"]["geometry"])

    def assertExportFailure(self, source, **options):
        with self.assertRaises(OntoKinError) as context:
            self.build(source, **options)
        diagnostic = context.exception.diagnostic.to_dict(Source(source))
        schema = json.loads((DEFAULT_FIXTURES / "diagnostic.schema.json").read_text())
        specification = (DEFAULT_FIXTURES.parent / "OK-LANG-001-core-language-specification.md").read_text()
        self.assertEqual(set(diagnostic), set(schema["required"]))
        self.assertIn(diagnostic["phase"], schema["properties"]["phase"]["enum"])
        self.assertIn(diagnostic["category"], schema["properties"]["category"]["enum"])
        self.assertIn(diagnostic["code"], set(re.findall(r"`(OKL-[EW]-[A-Z0-9-]+)`", specification)))
        self.assertEqual(diagnostic["blocks"], ["delivered"])
        self.assertEqual(diagnostic["details"]["target_contract"], "ontokin.glb/0.1")
        self.assertTrue(diagnostic["details"]["export_code"])
        json.dumps(diagnostic, allow_nan=False)
        return diagnostic

    def test_invalid_sampling_arguments_report_structured_delivery_failure(self):
        source = simple_source()
        for fps in (0, -1, float("nan"), float("inf"), True, 1e12):
            with self.subTest(fps=fps):
                self.assertExportFailure(source, fps=fps)
        for end in ("-1", "1.1", float("nan"), True):
            with self.subTest(end=end):
                self.assertExportFailure(source, end=end)

    def test_float32_collapsed_event_times_are_not_silently_merged(self):
        source = simple_source(duration="2[s]", extra_scene="at 1[s] sequence {} at 1.00000001[s] sequence {}")
        self.assertExportFailure(source)

    def test_curved_flight_cannot_pass_by_checking_keyframes_only(self):
        # At 1 fps the authored release and end positions are exact keys, but
        # the straight segment between them misses the gravitational parabola.
        self.assertExportFailure(materialize(self.cases["P02"]), fps=1)

    def test_finite_source_coordinates_cannot_hide_float32_precision_loss(self):
        for position in ("10000000001[m]", "1e40[m]"):
            with self.subTest(position=position):
                self.assertExportFailure(simple_source(placement=position))

    def test_tiny_valid_geometry_cannot_be_exported_as_collapsed_triangles(self):
        for radius in ("1e-50", "1e-45"):
            with self.subTest(radius=radius):
                # The latter retains a nonzero bounding box in binary32, yet
                # some adjacent sphere vertices collapse to the same point.
                self.assertExportFailure(simple_source(geometry=f"sphere({radius}[m])"))

    def test_requested_unavailable_capability_blocks_export_of_represented_model(self):
        source = materialize(self.cases["N25"])
        model = validate(parse(source), level="represented")
        with self.assertRaises(OntoKinError) as context:
            export_glb(model)
        self.assertEqual(context.exception.diagnostic.category, "unsupported")


if __name__ == "__main__":
    unittest.main()
