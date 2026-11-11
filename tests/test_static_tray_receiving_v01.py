"""Synthetic CPU checks of receiving comparison, with no native execution.

The source observation is an independent hand-derived synthetic GLB measured by
the separate reader. Native-style eight-corner meshes and GLB-style split mesh
vertices are constructed from that measured reference only for these controls.
"""

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"/"static_tray_reader_v01"))
from reader import audit
from tests.test_static_tray_reader_v01 import synthetic

SPEC=importlib.util.spec_from_file_location("static_tray_receive_check",ROOT/"prototypes"/"static_tray_v01"/"receive_check.py")
CHECK=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)
compare=CHECK.compare


def observations(reference,native_unique=True):
    stages={}
    for stage in ("native_scene","imported_glb"):
        rows={}
        for name,source in reference["nodes"].items():
            row={"name":name,"extras":deepcopy(source["extras"]),
                 "children":sorted(source["children"]),"world_matrix":deepcopy(source["world_matrix"]),
                 "parent":None if source["extras"]["role"]=="tray-root" else "/".join(source["extras"]["owner_id"])}
            if "world_vertices" in source:
                positions=deepcopy(source["world_vertices"])
                indices=source["indices"]
                if stage=="native_scene" and native_unique:
                    vertices=sorted(set(tuple(v) for v in positions))
                    translation={i:vertices.index(tuple(v)) for i,v in enumerate(positions)}
                    triangles=[[translation[i] for i in indices[j:j+3]] for j in range(0,len(indices),3)]
                    positions=[list(v) for v in vertices]
                else:
                    triangles=[indices[j:j+3] for j in range(0,len(indices),3)]
                row.update(world_vertices=positions,triangles=triangles,material=deepcopy(source["material"]))
            rows[name]=row
        stages[stage]={"nodes":rows,"object_count":len(rows),"scene":"Synthetic receiving control",
                       "physics_world":False,"measurement_frame":"source-rh-y-up-metres"}
    return {"schema":"ontokin.static-tray.receiving-observations/0.1.0",
            "blender_version":[4,5,3],"build_hash":"67807e1800cc",**stages,
            "note":"Synthetic CPU observations; Blender was not started"}


class StaticTrayReceivingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.references={}
        for case in ("Q01","Q02","Q03","Q04","Q05"):
            path=Path(cls.temp.name)/(case+".glb")
            path.write_bytes(synthetic(case))
            cls.references[case]=audit(path,case,cls.references.get("Q01") if case in ("Q04","Q05") else None)
            if not cls.references[case]["passed"]:
                raise AssertionError(cls.references[case]["findings"])

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.reference=self.references["Q01"]
        self.observed=observations(self.reference)

    def mesh(self,stage="native_scene"):
        return self.observed[stage]["nodes"]["equipment-tray/pair/left/base"]

    def test_native_corner_and_import_normal_splits_match_all_frozen_cases(self):
        for case,reference in self.references.items():
            with self.subTest(case=case):
                result=compare(observations(reference),reference)
                self.assertTrue(result["passed"],result["findings"])
                self.assertTrue(result["compared_native_scene"])
                self.assertTrue(result["compared_imported_glb"])
                self.assertGreater(len(result["measurements"]),1000)
                self.assertLess(len(json.dumps(result,allow_nan=False)),4*1024*1024)

    def test_explicit_parent_and_identity_are_checked(self):
        for change in ("parent","identity","children"):
            self.observed=observations(self.reference)
            row=self.mesh()
            if change=="parent":
                row["parent"]="equipment-tray/pair/right"
            elif change=="identity":
                row["extras"]["owner_id"][-1]="right"
            else:
                row["children"]=["equipment-tray/pair/right/base"]
            with self.subTest(change=change):
                self.assertFalse(compare(self.observed,self.reference)["passed"])

    def test_out_of_tolerance_geometry_retains_actual_differences(self):
        self.mesh()["world_vertices"][0][0]+=.002
        result=compare(self.observed,self.reference)
        self.assertFalse(result["passed"])
        self.assertTrue(any(not x["passed"] and x.get("difference",0)>.001 for x in result["measurements"]))

    def test_translation_uses_five_micrometre_geometry_allowance(self):
        row=self.mesh()
        row["world_matrix"][0][3]+=.000004
        for vertex in row["world_vertices"]:
            vertex[0]+=.000004
        result=compare(self.observed,self.reference)
        self.assertTrue(result["passed"],result["findings"])
        row["world_matrix"][0][3]+=.000002
        for vertex in row["world_vertices"]:
            vertex[0]+=.000002
        self.assertFalse(compare(self.observed,self.reference)["passed"])

    def test_nonfinite_matrix_vertex_and_material_cannot_pass(self):
        for position in ("matrix","vertex","material"):
            for value in (float("nan"),float("inf"),-float("inf")):
                self.observed=observations(self.reference)
                row=self.mesh()
                if position=="matrix":
                    row["world_matrix"][0][0]=value
                elif position=="vertex":
                    row["world_vertices"][0][0]=value
                else:
                    row["material"]["roughnessFactor"]=value
                with self.subTest(position=position,value=repr(value)):
                    result=compare(self.observed,self.reference)
                    self.assertFalse(result["passed"])
                    json.dumps(result,allow_nan=False)

    def test_oriented_surface_damage_is_rejected_with_unchanged_bounds(self):
        for change in ("reverse","duplicate","missing","index"):
            self.observed=observations(self.reference)
            triangles=self.mesh()["triangles"]
            if change=="reverse":
                triangles[0].reverse()
            elif change=="duplicate":
                triangles[0]=triangles[1][:]
            elif change=="missing":
                triangles.pop()
            else:
                triangles[0][0]=999
            with self.subTest(change=change):
                self.assertFalse(compare(self.observed,self.reference)["passed"])

    def test_material_values_are_exact(self):
        row=self.mesh("imported_glb")
        row["material"]["roughnessFactor"]+=.00000001
        result=compare(self.observed,self.reference)
        self.assertFalse(result["passed"])
        self.assertTrue(any(x["name"]=="fixed_material" and not x["passed"] for x in result["measurements"]))

    def test_missing_receiving_stage_or_changed_identity_inventory_fails(self):
        for change in ("stage","missing","extra","physics","version"):
            self.observed=observations(self.reference)
            if change=="stage":
                del self.observed["imported_glb"]
            elif change=="missing":
                del self.observed["native_scene"]["nodes"]["equipment-tray/pair/right/base"]
            elif change=="extra":
                self.observed["native_scene"]["nodes"]["unwanted"]={}
            elif change=="physics":
                self.observed["native_scene"]["physics_world"]=True
            else:
                self.observed["blender_version"]=[4,5,4]
            with self.subTest(change=change):
                self.assertFalse(compare(self.observed,self.reference)["passed"])

    def test_unpassed_geometry_reference_cannot_authorize_receiving(self):
        reference=deepcopy(self.reference)
        reference["passed"]=False
        self.assertFalse(compare(self.observed,reference)["passed"])

    def test_allowed_coincident_reference_splits_use_corner_welding(self):
        reference=deepcopy(self.reference)
        row=reference["nodes"]["equipment-tray/pair/left/base"]
        row["world_vertices"][0][0]+=.0000001
        result=compare(self.observed,reference)
        self.assertTrue(result["passed"],result["findings"])

    def test_scale_or_reflection_fails_rigid_transform_comparison(self):
        for value in (1.001,-1):
            self.observed=observations(self.reference)
            self.mesh()["world_matrix"][0][0]=value
            self.assertFalse(compare(self.observed,self.reference)["passed"])


if __name__=="__main__":
    unittest.main()
