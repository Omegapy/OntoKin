"""Hostile decoded-data controls for the independent C075 geometry checker."""
import copy
import json
from pathlib import Path
import unittest
from ontokin.bundle import ProgramBundle,SourceUnit
from ontokin.budget_runtime import execute_extrusion_export
from ontokin.scene import ExportOptions
from tools.extrusion_oracles import Decoded,check_geometry

F=Path(__file__).resolve().parents[1]/'examples/polygon-extrusions'
class ExtrusionOracleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source=ProgramBundle(SourceUnit('entry','rectangle.ok',(F/'rectangle.ok').read_bytes()))
        result=execute_extrusion_export(source,options=ExportOptions(fps=4,end='1',helpers=False))
        assert result.data is not None
        cls.decoded=Decoded(result.data)
        cls.wanted=next(x['geometry'] for x in json.loads((F/'expected.json').read_text())['cases'] if x['id']=='rectangle')
    def reject(self,mutate):
        rows=copy.deepcopy(self.decoded.triangles('shape'));mutate(rows)
        class Changed:
            def triangles(self,path):return rows
        with self.assertRaises(AssertionError):check_geometry(Changed(),'shape',self.wanted)
    def test_complete_decoded_rectangle_satisfies_analytic_measurements(self):
        self.assertEqual(check_geometry(self.decoded,'shape',self.wanted)['triangles'],12)
    def test_tilted_unit_normal_cannot_pass_positive_dot_alone(self):
        def change(rows):
            row=next(x for x in rows if x[0]=='top');row[2][:]=[(0,.6,.8)]*3
        self.reject(change)
    def test_reversed_cap_winding_rejects(self):
        def change(rows):
            row=next(x for x in rows if x[0]=='bottom');row[1][0],row[1][1]=row[1][1],row[1][0]
        self.reject(change)
    def test_missing_triangle_rejects(self):self.reject(lambda rows:rows.pop())
    def test_wrong_regional_color_rejects(self):
        def change(rows):rows[0][3]['pbrMetallicRoughness']['baseColorFactor']=[0,0,0,1]
        self.reject(change)
    def test_non_authored_corner_rejects(self):
        def change(rows):rows[0][1][0]=(100,100,100)
        self.reject(change)
