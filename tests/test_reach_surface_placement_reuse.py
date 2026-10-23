"""Native geometry reuse preserves exact placed bytes and independent reads."""
import copy
from dataclasses import replace
import math
import struct
import unittest
from unittest.mock import patch

from ontokin import scene
from ontokin.diagnostics import OntoKinError
from ontokin.geometry import box_mesh, sphere_mesh
from ontokin.gltf import DecodedGLB, _validate_geometry, export_glb, read_glb
from ontokin.model import Pose
from ontokin.reach_conformance import _geometry_bounds
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork
from ontokin.surface import LoftMesh, SurfaceError
from tests.test_reach_source_mesh_reuse import recipe
from tests.test_surface_export import compile_source, single_source


def scalar_surface(geometry, *, max_vertices=250000, check=None):
    """The original per-corner placement, with no retained numeric results."""
    mesh, placement = scene.materialize_surface(geometry, max_vertices=max_vertices, check=check)
    positions, normals = [], []
    for position, normal in zip(mesh.positions, mesh.normals):
        if check is not None:
            check()
        rotated = scene._rotate(placement.rotation, position)
        transformed = tuple(a + b for a, b in zip(rotated, placement.position))
        transformed_normal = scene._rotate(placement.rotation, normal)
        if not all(math.isfinite(value) for value in (*transformed, *transformed_normal)):
            raise SurfaceError("OKL-E-SURFACE-NUMERIC",
                               "Local visual placement produced a nonfinite surface coordinate.")
        positions.append(transformed)
        normals.append(transformed_normal)
    if check is not None:
        check()
    return scene.SurfaceMesh("loft", tuple(positions), tuple(normals), mesh.regions,
                             mesh.section_keys, mesh.facets, mesh.caps)


def bits(mesh):
    return b"".join(struct.pack("!3d", *value) for value in (*mesh.positions, *mesh.normals))


class PlacedSurfaceReuseTests(unittest.TestCase):
    def test_native_placed_bytes_match_original_corner_calculations(self):
        for facets, caps in ((8, "none"), (16, "flat"), (64, "flat")):
            for position, rotation in (((0., -0., 0.), (1., 0., -0., 0.)),
                                       ((.125, -.375, .5), (.5, .5, .5, .5)),
                                       ((-.25, .75, -.125), (0., -0., 1., 0.))):
                value = recipe()
                value["surface"].update(facets=facets, caps=caps)
                value.update(local_position=position, local_rotation=rotation)
                value["surface"]["sections"] = tuple(
                    replace(section, center_m=(.015 * index, -.01 * index, -0.))
                    for index, section in enumerate(value["surface"]["sections"]))
                with self.subTest(facets=facets, caps=caps, position=position):
                    expected = scalar_surface(value)
                    actual = scene.build_surface_mesh(value)
                    self.assertEqual(actual, expected)
                    self.assertEqual(bits(actual), bits(expected))

    def test_real_rotation_and_checkpoint_work_decreases(self):
        counts = {}
        for name, builder in (("scalar", scalar_surface), ("reuse", scene.build_surface_mesh)):
            visits = []
            with patch("ontokin.scene._rotate", wraps=scene._rotate) as rotate:
                mesh = builder(recipe(), check=lambda: visits.append(True))
            counts[name] = len(visits), rotate.call_count, bits(mesh)
        self.assertEqual(counts["reuse"][2], counts["scalar"][2])
        self.assertLess(counts["reuse"][0], counts["scalar"][0])
        self.assertLess(counts["reuse"][1], counts["scalar"][1] * .75)

    def test_equal_values_with_different_signed_zero_never_alias(self):
        plus, minus = (0., 0., 1.), (-0., 0., 1.)
        normal = (0., -0., 1.)
        native = LoftMesh(("first", "last"), (plus, minus, plus) * 4,
                          (normal,) * 12, (), 8, "none")
        placement = Pose("self", (-0., -0., -0.), (1., -0., -0., -0.))
        with patch("ontokin.scene.materialize_surface", return_value=(native, placement)):
            expected = scalar_surface({})
            actual = scene.build_surface_mesh({})
        self.assertEqual(bits(actual), bits(expected))

    def test_repeated_corners_keep_bounded_cancellation_and_original_exception(self):
        position, normal = (.1, .2, .3), (0., 0., 1.)
        consumed = []

        class Corners:
            def __iter__(self):
                for _ in range(256):
                    consumed.append(True)
                    yield position

        native = LoftMesh(("first", "last"), Corners(),
                          (normal,) * 256, (), 8, "none")
        marker, visits = RuntimeError("cancel repeated placements"), []

        def cancel():
            visits.append(True)
            if len(visits) == 2:
                raise marker

        with patch("ontokin.scene.materialize_surface", return_value=(native, Pose())):
            with self.assertRaises(RuntimeError) as raised:
                scene.build_surface_mesh({}, check=cancel)
        self.assertIs(raised.exception, marker)
        self.assertEqual(len(visits), 2)
        self.assertLessEqual(len(consumed), 65)

    def test_current_recipe_remaining_allowance_and_nonfinite_errors_are_preserved(self):
        value = recipe()
        original = scene.build_surface_mesh(value)
        value["local_position"] = (.25, -.5, .75)
        self.assertEqual(bits(scene.build_surface_mesh(value)), bits(scalar_surface(value)))
        self.assertNotEqual(bits(scene.build_surface_mesh(value)), bits(original))
        with self.assertRaises(SurfaceError) as raised:
            scene.build_surface_mesh(value, max_vertices=len(original.positions) - 1)
        self.assertEqual(raised.exception.code, "OKL-E-RESOURCE")
        for builder in (scalar_surface, scene.build_surface_mesh):
            value["local_position"] = (math.inf, 0., 0.)
            with self.assertRaises(SurfaceError) as raised:
                builder(value)
            self.assertEqual(raised.exception.code, "OKL-E-SURFACE-NUMERIC")

    def test_callbacks_do_not_reread_mutated_placement_or_section_inputs(self):
        value = recipe()
        expected = scalar_surface(value)

        def mutate():
            value["local_position"] = (1000., 1000., 1000.)
            value["surface"]["sections"] = ()

        actual = scene.build_surface_mesh(value, check=mutate)
        self.assertEqual(bits(actual), bits(expected))

    def test_actual_surface_export_bytes_match_original_placement(self):
        _, compiler = compile_source(single_source(
            placement="pose(self.frame, vec3(0.125[m], -0.375[m], 0.5[m]), quat(0.5, 0.5, 0.5, 0.5))"))
        options = scene.ExportOptions(fps=1, helpers=False)
        with patch("ontokin.scene.build_surface_mesh", side_effect=scalar_surface):
            expected = export_glb(compiler.model, options=options, target_contract="ontokin.glb/0.3")
        actual = export_glb(compiler.model, options=options, target_contract="ontokin.glb/0.3")
        self.assertEqual(actual.data, expected.data)


class NativePrimitiveReuseTests(unittest.TestCase):
    def cached(self, geometry, work, namespace="reach_independent_source"):
        return scene._source_primitive_mesh(geometry, work=work, namespace=namespace)

    def test_exact_constructor_inputs_and_role_namespaces_remain_separate(self):
        for geometry, builder, value in (({"kind": "sphere", "radius": .05}, sphere_mesh, .05),
                                         ({"kind": "box", "size": (.2, .3, .4)}, box_mesh, (.2, .3, .4))):
            with self.subTest(kind=geometry["kind"]):
                work = ReachExecutionWork()
                first = self.cached(geometry, work)
                self.assertEqual(first, builder(value))
                self.assertIs(self.cached(copy.deepcopy(geometry), work), first)
                separate = self.cached(geometry, work, "reach_recording_source")
                self.assertEqual(separate, first)
                self.assertIsNot(separate, first)
                self.assertIsNot(separate.positions, first.positions)

    def test_signed_zero_types_mutable_values_and_changed_dimensions_do_not_alias(self):
        work = ReachExecutionWork()
        positive = self.cached({"kind": "box", "size": (0., .2, .3)}, work)
        negative = self.cached({"kind": "box", "size": (-0., .2, .3)}, work)
        self.assertIsNot(positive, negative)
        self.assertNotEqual(bits(positive), bits(negative))
        first = self.cached({"kind": "sphere", "radius": 1.}, work)
        for value in (1, True):
            self.assertIsNot(self.cached({"kind": "sphere", "radius": value}, work), first)
        mutable = {"kind": "box", "size": [.1, .2, .3]}
        before = tuple(work._cache.items())
        initial = self.cached(mutable, work)
        mutable["size"][0] = .5
        changed = self.cached(mutable, work)
        self.assertNotEqual(changed, initial)
        self.assertEqual(tuple(work._cache.items()), before)
        for invalid in (0., -1., math.inf, math.nan):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                self.cached({"kind": "sphere", "radius": invalid}, work)

    def test_live_source_changes_during_lookup_and_insertion_are_read_again(self):
        for stage in ("cache_lookup", "cache_promote", "cache_insert", "cache_evict"):
            with self.subTest(stage=stage):
                geometry = {"kind": "sphere", "radius": .05}
                work = ReachExecutionWork(max_cache_entries=1)
                if stage in ("cache_lookup", "cache_promote"):
                    self.cached(geometry, work)
                elif stage == "cache_evict":
                    self.cached({"kind": "sphere", "radius": .2}, work)
                charge, changed = work.charge, False

                def mutate(kind="checkpoint", amount=1):
                    nonlocal changed
                    if kind == stage and not changed:
                        geometry["radius"], changed = .125, True
                    return charge(kind, amount)

                work.charge = mutate
                actual = self.cached(geometry, work)
                self.assertTrue(changed)
                self.assertEqual(bits(actual), bits(sphere_mesh(.125)))
                self.assertEqual(len(work._cache), 1)
                self.assertIs(next(iter(work._cache.values())), actual)

    def test_continuously_changed_source_exhausts_the_original_budget(self):
        geometry = {"kind": "sphere", "radius": .05}
        work = ReachExecutionWork(max_operations=6)
        charge = work.charge

        def mutate(kind="checkpoint", amount=1):
            if kind == "cache_lookup":
                geometry["radius"] += .01
            return charge(kind, amount)

        work.charge = mutate
        with self.assertRaises(ReachAdmissionError) as raised:
            self.cached(geometry, work)
        self.assertEqual(raised.exception.details["consumed"], 7)
        self.assertEqual(work.operations, 6)
        self.assertEqual(len(work._cache), 0)

    def test_live_operand_scope_and_lru_limits_remain_enforced(self):
        geometry, work = {"kind": "sphere", "radius": .05}, ReachExecutionWork(max_cache_entries=2)
        first = self.cached(geometry, work)
        charge, narrowed = work.charge, False

        def narrow(kind="checkpoint", amount=1):
            nonlocal narrowed
            if kind == "cache_lookup" and not narrowed:
                work.max_operand_bits, narrowed = 8, True
            return charge(kind, amount)

        work.charge = narrow
        second = self.cached(geometry, work)
        self.assertIsNot(second, first)
        self.assertEqual(bits(second), bits(first))
        self.assertEqual(work._cache_operand_bits, 8)
        for radius in (.1, .2, .3):
            self.cached({"kind": "sphere", "radius": radius}, work)
        self.assertEqual(len(work._cache), 2)
        self.assertGreater(work.counts.get("cache_evict", 0), 0)
        self.assertEqual(work.max_operations, 100000)

    def test_cancellation_and_exhaustion_never_publish_partial_geometry(self):
        geometry, stopped = {"kind": "sphere", "radius": .05}, False
        marker = RuntimeError("cancel native source mesh")

        def cancel():
            if stopped:
                raise marker

        work = ReachExecutionWork(check=cancel)

        def completed(value):
            nonlocal stopped
            result = sphere_mesh(value)
            stopped = True
            return result

        with patch("ontokin.scene.sphere_mesh", side_effect=completed):
            with self.assertRaises(RuntimeError) as raised:
                self.cached(geometry, work)
        self.assertIs(raised.exception, marker)
        self.assertIs(work.callback_error, marker)
        self.assertEqual(len(work._cache), 0)
        limited = ReachExecutionWork(max_operations=1)
        with self.assertRaises(ReachAdmissionError) as raised:
            self.cached(geometry, limited)
        self.assertEqual(raised.exception.details["consumed"], 2)
        self.assertEqual(limited.operations, 1)
        self.assertEqual(len(limited._cache), 0)


class IndependentPrimitiveOccurrenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, compiler = compile_source('''ontokin "0.3";
module RepeatedEyes @ "repeated-eyes";
profile "surface-0.1";
class Eye @ "eye" { geometry = sphere(0.05[m]); physical = no_body(); }
scene Demo @ "demo" {
    duration = 1[s];
    gravity = vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2]);
    object first @ "first": Eye {}
    object second @ "second": Eye {}
    object third @ "third": Eye {}
}
''')
        cls.model = compiler.model
        cls.options = scene.ExportOptions(fps=1, helpers=False)
        cls.data = export_glb(cls.model, options=cls.options, target_contract="ontokin.glb/0.3").data

    def verify(self, decoded, work):
        bounds, meshes = _geometry_bounds(decoded, self.model, self.options, work=work)
        _validate_geometry(decoded, self.model, self.options, "ontokin.glb/0.3",
                           scene.program_metadata(self.model), check=work.tick, source_meshes=meshes)
        return bounds, meshes

    def test_repeated_native_source_keeps_independent_proof_and_occurrence_caps(self):
        work = ReachExecutionWork()
        decoded = read_glb(self.data, target_contract="ontokin.glb/0.3")
        with patch("ontokin.scene.sphere_mesh", wraps=sphere_mesh) as build:
            bounds, meshes = self.verify(decoded, work)
        self.assertEqual(build.call_count, 1)
        self.assertEqual(len(bounds), 3)
        self.assertEqual(len({id(mesh) for mesh in meshes.values()}), 1)
        self.assertEqual(work.counts["independent_geometry_point"], 482)
        self.assertGreater(work.counts["independent_geometry_reuse_block"], 0)
        self.assertEqual(sum(len(mesh.positions) for mesh in meshes.values()), 1446)
        with patch("ontokin.scene.MAX_MESH_VERTICES", 1445):
            with self.assertRaises(OntoKinError) as raised:
                self.verify(decoded, work)
        self.assertEqual(raised.exception.code, "OKL-E-RESOURCE")
        self.assertEqual(raised.exception.diagnostic.details["export_code"], "OKE-E-MESH-BUDGET")

    def test_warm_geometry_still_rejects_last_occurrence_buffer_and_source_changes(self):
        work = ReachExecutionWork()
        decoded = read_glb(self.data, target_contract="ontokin.glb/0.3")
        self.verify(decoded, work)
        for changed in ("POSITION", "NORMAL", "indices"):
            actual = DecodedGLB(copy.deepcopy(decoded.document), decoded.binary)
            primitive = actual.document["meshes"][actual.document["nodes"][-1]["mesh"]]["primitives"][0]
            index = primitive["indices"] if changed == "indices" else primitive["attributes"][changed]
            accessor = actual.document["accessors"][index]
            view = actual.document["bufferViews"][accessor["bufferView"]]
            start = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
            binary = bytearray(actual.binary)
            format_ = "<H" if changed == "indices" else "<f"
            old = struct.unpack_from(format_, binary, start)[0]
            struct.pack_into(format_, binary, start, old + (1 if changed == "indices" else .125))
            actual.binary = bytes(binary)
            with self.subTest(changed=changed), self.assertRaises(OntoKinError):
                self.verify(actual, work)
        last = list(self.model.objects.values())[-1]
        with patch.dict(last.geometry, radius=.125):
            with self.assertRaises(OntoKinError):
                self.verify(decoded, work)


if __name__ == "__main__":
    unittest.main()
