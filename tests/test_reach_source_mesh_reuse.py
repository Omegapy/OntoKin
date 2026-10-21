"""Pure source-mesh reuse preserves actual bytes and occurrence obligations."""
import copy
from dataclasses import replace
from pathlib import Path
import struct
import unittest
from unittest.mock import patch

from ontokin.bundle import load_file_manifest
from ontokin.construction import compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.gltf import DecodedGLB, _validate_geometry, export_glb, read_glb
from ontokin.reach_conformance import _geometry_bounds
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork
from ontokin.scene import (ExportOptions, SurfaceMesh, _nodes, _source_surface_mesh,
                           build_surface_mesh, materialize_surface, program_metadata)
from ontokin.surface import LoftSection, SurfaceMaterial, SurfaceError
from tests.test_surface_export import compile_source, single_source


ROOT = Path(__file__).resolve().parents[1]
WRITER, READER = "reach_recording_source", "reach_independent_source"


def recipe():
    return {"kind": "placed", "surface": {
        "kind": "loft", "sections": (
            LoftSection("base", 0., (0., 0., 0.), .1, .08, "shell"),
            LoftSection("middle", .5, (0., 0., 0.), .08, .07, "trim"),
            LoftSection("end", 1., (0., 0., 0.), .06, .05, "trim")),
        "materials": (SurfaceMaterial("shell", (.1, .4, .8, 1.), .2, .4),
                      SurfaceMaterial("trim", (.8, .6, .2, 1.), .5, .3)),
        "facets": 16, "caps": "flat"},
        "local_position": (0., 0., 0.), "local_rotation": (1., 0., 0., 0.)}


def cached(value, work, *, namespace=WRITER, remaining=250000):
    return _source_surface_mesh(value, max_vertices=remaining, work=work, namespace=namespace)


class SourceSurfaceMeshReuseTests(unittest.TestCase):
    def test_complete_geometry_palette_and_local_placement_change_the_result(self):
        original, work = recipe(), ReachExecutionWork()
        first = cached(original, work)
        self.assertEqual(first, build_surface_mesh(original))
        with patch("ontokin.scene.materialize_surface",
                   side_effect=AssertionError("Repeated source construction")):
            self.assertIs(cached(copy.deepcopy(original), work), first)

        for changed in ("station", "radius", "region", "section_key", "facets", "caps",
                        "rgba", "metallic", "roughness", "position", "rotation"):
            value = copy.deepcopy(original)
            surface = value["surface"]
            if changed in ("station", "radius", "region", "section_key"):
                fields = {"station": {"station_m": .6}, "radius": {"radius_x_m": .12},
                          "region": {"region": "shell"}, "section_key": {"key": "changed"}}
                surface["sections"] = (surface["sections"][0],
                    replace(surface["sections"][1], **fields[changed]), surface["sections"][2])
            elif changed in ("rgba", "metallic", "roughness"):
                fields = {"rgba": {"rgba": (.2, .3, .7, .5)},
                          "metallic": {"metallic": .1}, "roughness": {"roughness": .9}}
                surface["materials"] = (replace(surface["materials"][0], **fields[changed]),
                                        surface["materials"][1])
            elif changed == "facets":
                surface[changed] = 8
            elif changed == "caps":
                surface[changed] = "none"
            elif changed == "position":
                value["local_position"] = (.25, 0., 0.)
            else:
                value["local_rotation"] = (0., 0., 0., 1.)
            with self.subTest(changed=changed):
                actual = cached(value, work)
                self.assertIsNot(actual, first)
                self.assertEqual(actual, build_surface_mesh(value))
                self.assertNotEqual(actual, first)

    def test_invalid_changed_recipe_never_reuses_a_valid_mesh(self):
        original, work = recipe(), ReachExecutionWork()
        cached(original, work)
        for changed in ("radius", "palette", "placement", "boolean", "long_key", "sections"):
            value = copy.deepcopy(original)
            surface = value["surface"]
            if changed in ("radius", "boolean", "long_key"):
                fields = {"radius": {"radius_x_m": float("nan")},
                          "boolean": {"station_m": False}, "long_key": {"key": "x" * 65}}
                surface["sections"] = (replace(surface["sections"][0], **fields[changed]),
                                       *surface["sections"][1:])
            elif changed == "palette":
                surface["materials"] = (replace(surface["materials"][0], roughness=-.1),
                                        surface["materials"][1])
            elif changed == "placement":
                value["local_position"] = (float("nan"), 0., 0.)
            else:
                surface["sections"] = surface["sections"] * 22
            before = tuple(work._cache.items())
            with self.subTest(changed=changed), self.assertRaises(SurfaceError):
                cached(value, work)
            self.assertEqual(tuple(work._cache.items()), before)

    def test_reduced_allowance_and_cache_capacity_remain_enforced(self):
        work, original = ReachExecutionWork(max_cache_entries=2), recipe()
        first = cached(original, work)
        self.assertEqual(len(first.positions), 288)
        self.assertIs(cached(original, work, remaining=288), first)
        with self.assertRaises(SurfaceError) as raised:
            cached(original, work, remaining=287)
        self.assertEqual(raised.exception.details, {"required": 288, "available": 287})
        for offset in (.1, .2, .3):
            value = copy.deepcopy(original)
            value["local_position"] = (offset, 0., 0.)
            cached(value, work)
            self.assertEqual(work.record()["cache_entries"], 2)
        with patch("ontokin.scene.materialize_surface", wraps=materialize_surface) as build:
            self.assertEqual(cached(original, work), first)
            self.assertEqual(build.call_count, 1)
        self.assertEqual(work.max_operations, 100000)
        self.assertEqual(work.max_cache_entries, 2)
        self.assertGreater(work.counts.get("cache_evict", 0), 0)

    def test_cancellation_and_budget_never_publish_partial_meshes(self):
        stopped = False
        marker = RuntimeError("cancel source geometry")

        def check():
            if stopped:
                raise marker

        work = ReachExecutionWork(check=check)
        original = recipe()
        cached(original, work)
        before = tuple(work._cache.items())
        stopped = True
        with self.assertRaises(RuntimeError) as raised:
            cached(original, work)
        self.assertIs(raised.exception, marker)
        self.assertIs(work.callback_error, marker)
        self.assertEqual(tuple(work._cache.items()), before)

        stopped = False
        work = ReachExecutionWork(check=check)

        def completed(*args, **kwargs):
            nonlocal stopped
            result = build_surface_mesh(*args, **kwargs)
            stopped = True
            return result

        with patch("ontokin.scene.build_surface_mesh", side_effect=completed):
            with self.assertRaises(RuntimeError) as raised:
                cached(original, work)
        self.assertIs(raised.exception, marker)
        self.assertIs(work.callback_error, marker)
        self.assertEqual(work.record()["cache_entries"], 0)
        work = ReachExecutionWork(max_operations=1)
        with self.assertRaises(ReachAdmissionError) as raised:
            cached(original, work)
        self.assertEqual(raised.exception.details["budget"], "max_operations")
        self.assertEqual(raised.exception.details["consumed"], 2)
        self.assertEqual(work.operations, 1)
        self.assertEqual(work.record()["cache_entries"], 0)


class ActualSurfaceOccurrenceReuseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, compiler = compile_source(single_source(objects='''
            object first @ "first": Shell {}
            object second @ "second": Shell {}
        ''', placement="pose(self.frame, vec3(0[m], 0[m], 0[m]), quat(1, 0, 0, 0))"))
        cls.model = compiler.model
        cls.options = ExportOptions(fps=1, helpers=False)
        cls.data = export_glb(cls.model, options=cls.options, target_contract="ontokin.glb/0.3").data

    def verify_geometry(self, decoded, model, work):
        geometry, meshes = _geometry_bounds(decoded, model, self.options, work=work)
        _validate_geometry(decoded, model, self.options, "ontokin.glb/0.3",
                           program_metadata(model), check=work.tick, source_meshes=meshes)
        return geometry, meshes

    def test_source_reuse_preserves_complete_export_bytes(self):
        work = ReachExecutionWork()

        def cached_nodes(model, options, *, check=None):
            return _nodes(model, options, check=check, work=work)

        with patch("ontokin.scene._nodes", side_effect=cached_nodes):
            result = export_glb(self.model, options=self.options, target_contract="ontokin.glb/0.3")
        self.assertEqual(result.data, self.data)
        self.assertEqual(result.report["validation"]["status"], "passed")

    def test_reader_reconstructs_independently_and_keeps_occurrence_limits(self):
        work = ReachExecutionWork()
        nodes = _nodes(self.model, self.options, check=work.tick, work=work)
        self.assertIs(nodes[0].mesh, nodes[1].mesh)
        self.assertNotEqual(nodes[0].metadata["element_id"], nodes[1].metadata["element_id"])
        decoded = read_glb(self.data, target_contract="ontokin.glb/0.3")
        with patch("ontokin.scene.materialize_surface", wraps=materialize_surface) as build:
            geometry, meshes = self.verify_geometry(decoded, self.model, work)
        self.assertEqual(build.call_count, 1)
        self.assertIs(meshes[0], meshes[1])
        self.assertIsNot(meshes[0], nodes[0].mesh)
        self.assertEqual(len(geometry), 2)
        self.assertNotEqual(geometry[0]["identity"], geometry[1]["identity"])
        self.assertEqual(sum(len(mesh.positions) for mesh in meshes.values()), 384)
        with patch("ontokin.scene.MAX_MESH_VERTICES", 383):
            with self.assertRaises(OntoKinError):
                _nodes(self.model, self.options, check=work.tick, work=work)
            with self.assertRaises(SurfaceError) as raised:
                _geometry_bounds(decoded, self.model, self.options, work=work)
        self.assertEqual(raised.exception.details, {"required": 192, "available": 191})

    def test_warm_source_mesh_reuse_checks_every_last_sibling_buffer_and_material(self):
        work = ReachExecutionWork()
        decoded = read_glb(self.data, target_contract="ontokin.glb/0.3")
        self.verify_geometry(decoded, self.model, work)
        for changed in ("POSITION", "NORMAL", "indices", "material", "provenance"):
            actual = DecodedGLB(copy.deepcopy(decoded.document), decoded.binary)
            primitive = actual.document["meshes"][actual.document["nodes"][-1]["mesh"]]["primitives"][0]
            if changed in ("POSITION", "NORMAL", "indices"):
                index = primitive["indices"] if changed == "indices" else primitive["attributes"][changed]
                accessor = actual.document["accessors"][index]
                view = actual.document["bufferViews"][accessor["bufferView"]]
                start = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
                binary = bytearray(actual.binary)
                format_ = "<H" if changed == "indices" else "<f"
                old = struct.unpack_from(format_, binary, start)[0]
                struct.pack_into(format_, binary, start, old + (1 if changed == "indices" else .125))
                actual.binary = bytes(binary)
            else:
                material = actual.document["materials"][primitive["material"]]
                if changed == "material":
                    material["pbrMetallicRoughness"]["roughnessFactor"] = .99
                else:
                    material["extras"]["ontokin"]["occurrence_path"] = "first"
            with self.subTest(changed=changed), self.assertRaises(OntoKinError):
                self.verify_geometry(actual, self.model, work)

    def test_frozen_p23_keeps_all_97_objects_and_18456_repeated_vertices(self):
        compiler = compile_construction(load_file_manifest(
            ROOT / "docs/language-design/planar-reach-v0.1/p23.files.json"), level="constructed")
        work = compiler.reach_work
        with patch("ontokin.scene.materialize_surface", wraps=materialize_surface) as build:
            nodes = _nodes(compiler.model, self.options, check=work.tick, work=work)
        surfaces = [node.mesh for node in nodes if isinstance(node.mesh, SurfaceMesh)]
        self.assertEqual(len(nodes), 97)
        self.assertEqual(len({node.metadata["path"] for node in nodes}), 97)
        self.assertEqual(len(surfaces), 64)
        self.assertEqual(len({id(mesh) for mesh in surfaces}), 1)
        self.assertEqual(build.call_count, 1)
        self.assertEqual(sum(len(node.mesh.positions) for node in nodes if node.mesh), 18456)
        self.assertLessEqual(compiler.budget.operations, 100000)
        self.assertEqual(work.max_operations, 100000)


if __name__ == "__main__":
    unittest.main()
