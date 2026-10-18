"""Independent byte-level checks for provisional multi-region GLB encoding."""

import json
import struct
import unittest

from prototypes.surface_v01.mesh import LoftSection, SurfaceMaterial, triangulate_loft
from prototypes.surface_v01.glb import export_loft_prototype, GLBPrototype


def surface():
    secs = (
        LoftSection("z-start", 0.0, (0.0, 0.0, 0.0), 0.5, 0.3, "base"),
        LoftSection("a-middle", 0.8, (0.25, 0.1, 0.0), 0.4, 0.2, "middle"),
        LoftSection("b-end", 2.0, (0.4, 0.15, 0.0), 0.1, 0.1, "tip"),
    )
    mats = (
        SurfaceMaterial("base", (0.6, 0.3, 0.2, 1), 0.0, 0.8),
        SurfaceMaterial("middle", (0.1, 0.4, 0.8, 1), 0.2, 0.4),
        SurfaceMaterial("tip", (0.8, 0.8, 0.8, 1), 0.5, 0.5),
    )
    return triangulate_loft(secs, mats, 16, "flat")


def decode(data):
    magic, version, length = struct.unpack_from("<III", data)
    if (magic, version, length) != (0x46546c67, 2, len(data)):
        raise AssertionError("GLB header must carry correct length and version.")
    json_size, json_type = struct.unpack_from("<II", data, 12)
    if json_type != 0x4e4f534a:
        raise AssertionError("GLB JSON chunk is missing.")
    document = json.loads(data[20:20 + json_size])
    start = 20 + json_size
    binary_size, binary_type = struct.unpack_from("<II", data, start)
    if binary_type != 0x004e4942 or start+8+binary_size != len(data):
        raise AssertionError("GLB binary chunk is missing or truncated.")
    return document, data[start+8:]


def unpack_accessor(document, binary, idx):
    accessor = document["accessors"][idx]
    view = document["bufferViews"][accessor["bufferView"]]
    count = accessor["count"]
    width = {"VEC3":3,"SCALAR":1}[accessor["type"]]
    kind = {5126:"f",5123:"H",5125:"I"}[accessor["componentType"]]
    fmt = struct.Struct("<" + kind * width)
    offset = view.get("byteOffset",0) + accessor.get("byteOffset",0)
    return [fmt.unpack_from(binary, offset+i*fmt.size) for i in range(count)]


class SurfaceGLBPrototypeTests(unittest.TestCase):
    def test_pbr_primitives_are_real_and_region_scoped(self):
        mesh=surface()
        result=export_loft_prototype(mesh, name="Offset tapered shell")
        self.assertIsInstance(result, GLBPrototype)
        self.assertEqual(result.primitives,3)
        self.assertEqual(result.triangles,96)
        self.assertLessEqual(result.max_vertex_error_m,1e-5)
        d,b=decode(result.data)
        self.assertTrue(d["extras"]["ontokin"]["prototype_only"])
        self.assertTrue(d["extras"]["ontokin"]["not_ontokin_glb_0_3"])
        self.assertNotIn("animations",d)
        self.assertEqual(len(d["meshes"]),1)
        primitives=d["meshes"][0]["primitives"]
        self.assertEqual(len(primitives),3)
        self.assertEqual([p["extras"]["ontokin"]["region_key"] for p in primitives],
                         ["base","middle","tip"])
        positions=unpack_accessor(d,b,primitives[0]["attributes"]["POSITION"])
        normals=unpack_accessor(d,b,primitives[0]["attributes"]["NORMAL"])
        self.assertEqual(len(positions),288)
        self.assertEqual(len(normals),288)
        self.assertEqual([len(unpack_accessor(d,b,p["indices"]))//3 for p in primitives],
                         [48,32,16])
        actual_indices=sorted(i[0] for p in primitives
                              for i in unpack_accessor(d,b,p["indices"]))
        self.assertEqual(actual_indices,list(range(288)))
        self.assertAlmostEqual(positions[0][0],0.5,places=6)
        self.assertEqual([d["materials"][p["material"]]["pbrMetallicRoughness"]["baseColorFactor"]
                          for p in primitives],
                          [[0.6,0.3,0.2,1],[0.1,0.4,0.8,1],[0.8,0.8,0.8,1]])
        self.assertEqual(d["materials"][1]["pbrMetallicRoughness"]["roughnessFactor"],0.4)
        self.assertEqual(d["materials"][2]["pbrMetallicRoughness"]["metallicFactor"],0.5)

    def test_binary_glb_is_deterministic_and_open_mesh_has_no_cap(self):
        mesh=surface()
        first=export_loft_prototype(mesh)
        self.assertEqual(first.data,export_loft_prototype(mesh).data)
        open_mesh=triangulate_loft((
            LoftSection("a",0,(0,0,0),0.4,0.4,"base"),
            LoftSection("b",1,(0,0,0),0.4,0.4,"base")
        ),(SurfaceMaterial("base",(0.4,0.6,0.4,0.8),0.1,0.9),),8,"none")
        r=export_loft_prototype(open_mesh)
        d,b=decode(r.data)
        self.assertEqual(r.triangles,16)
        self.assertEqual(d["materials"][0]["alphaMode"],"BLEND")
        self.assertEqual(len(unpack_accessor(d,b,d["meshes"][0]["primitives"][0]["indices"]))//3,16)

    def test_explicitly_not_native_program_delivery(self):
        d,_=decode(export_loft_prototype(surface()).data)
        self.assertNotIn("source_manifest",d["extras"]["ontokin"])
        self.assertNotIn("program_revision",d["extras"]["ontokin"])
        self.assertNotEqual(d["asset"]["generator"],"OntoKin reference 0.4.0")


if __name__=="__main__":
    unittest.main()
