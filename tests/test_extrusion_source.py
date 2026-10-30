"""Frozen .ok construction, source compatibility and explicit GLB/0.8 delivery."""
import hashlib
import json
from pathlib import Path
import unittest

from ontokin.bundle import ProgramBundle, SourceUnit
from ontokin.construction import compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.execution_budget import SharedExecutionBudget, HostPolicy, admit_entry_budget
from ontokin.gltf import export_glb, read_glb, validate_export
from ontokin.profile_capabilities import EXTRUSION_PROFILE, BUDGET_PROFILE
from ontokin.scene import EXTRUSION_TARGET, ExportOptions, build_surface_mesh
from tests.test_extrusion_geometry import totals

ROOT = Path(__file__).resolve().parents[1]/'examples/polygon-extrusions'
EXPECTED = json.loads((ROOT/'corrected/expected.json').read_text())


def bundle(name='rectangle.ok', *, text=None, library=False):
    raw=(ROOT/name).read_bytes() if text is None else text.encode()
    modules=(SourceUnit('package:fixture.extrusion-parts@1.0.0','parts.ok',
                        (ROOT/'parts.ok').read_bytes(),'fixture.extrusion-parts','1.0.0'),) if library else ()
    return ProgramBundle(SourceUnit('entry',name,raw),modules)


def compile_source(program, *, profile=EXTRUSION_PROFILE, caps=None, policy=None, callback=None):
    ledger=SharedExecutionBudget(policy, caps, check=callback)
    admit_entry_budget(program.entry, ledger, profile=profile)
    return compile_construction(program,execution_budget=ledger),ledger


def export(program):
    compiler,ledger=compile_source(program)
    result=export_glb(compiler.model,options=ExportOptions(fps=4),
                       target_contract=EXTRUSION_TARGET,work=compiler.reach_work)
    return result,compiler,ledger


class ExtrusionSourceTests(unittest.TestCase):
    def test_frozen_original_and_correction_bytes_remain_exact(self):
        freeze=json.loads((ROOT/'acceptance-freeze.json').read_text())
        for name,row in freeze['files'].items():
            with self.subTest(name=name):
                raw=(ROOT/name).read_bytes()
                self.assertEqual(len(raw),row['bytes'])
                self.assertEqual(hashlib.sha256(raw).hexdigest(),row['sha256'])
        corrected=json.loads((ROOT/'acceptance-correction-001.json').read_text())
        for name,row in corrected['corrected_files'].items():
            with self.subTest(name=name):
                raw=(ROOT/name).read_bytes()
                self.assertEqual(len(raw),row['bytes'])
                self.assertEqual(hashlib.sha256(raw).hexdigest(),row['sha256'])

    def test_all_frozen_source_outcomes_and_exact_invalid_diagnostics(self):
        for row in EXPECTED['cases']:
            with self.subTest(case=row['id']):
                program=bundle(row['source'])
                profile=BUDGET_PROFILE if row['id']=='earlier-version-rejection' else EXTRUSION_PROFILE
                if row['expected_outcome']=='invalid':
                    with self.assertRaises(OntoKinError) as caught:compile_source(program,profile=profile)
                    if 'diagnostic_code' in row:self.assertEqual(caught.exception.code,row['diagnostic_code'])
                else:
                    compiler,ledger=compile_source(program)
                    self.assertEqual(compiler.model.profile,EXTRUSION_PROFILE)
                    value=compiler.surface_meshes['shape']['mesh']
                    if 'geometry' in row:
                        expected=row['geometry'];area,volume,edges=totals(value)
                        self.assertEqual(value.triangle_count,expected['triangle_count'])
                        self.assertAlmostEqual(area,expected['surface_area_m2'],places=9)
                        self.assertAlmostEqual(volume,expected['volume_m3'],places=9)
                    self.assertLess(ledger.operations,100000)

    def test_every_valid_frozen_shape_delivers_under_default_budget(self):
        for row in EXPECTED['cases']:
            if row['expected_outcome']!='valid':continue
            with self.subTest(case=row['id']):
                result,compiler,ledger=export(bundle(row['source']))
                self.assertEqual(result.report['target_contract'],EXTRUSION_TARGET)
                self.assertEqual(result.report['validation']['status'],'passed')
                self.assertEqual(ledger.limits,{'max_operations':100000,'max_elapsed_ms':30000})
                self.assertLess(ledger.operations,100000)

    def test_binary64_valid_destination_collapse_rejects_delivery(self):
        compiler,ledger=compile_source(bundle('binary32-collapse.ok'))
        self.assertEqual(compiler.surface_meshes['shape']['mesh'].triangle_count,12)
        with self.assertRaises(OntoKinError):
            export_glb(compiler.model,options=ExportOptions(fps=4),target_contract=EXTRUSION_TARGET,
                       work=compiler.reach_work)

    def test_reordered_source_preserves_geometry_but_has_its_own_revision(self):
        a,aw=compile_source(bundle('concave-bracket.ok'))
        b,bw=compile_source(bundle('reordered-bracket.ok'))
        self.assertNotEqual(a.model.program_revision,b.model.program_revision)
        self.assertEqual(a.surface_meshes['shape']['mesh'],b.surface_meshes['shape']['mesh'])

    def test_fixed_library_source_repairs_one_occurrence_and_preserves_sibling(self):
        original,ow=compile_source(bundle(EXPECTED['assembly']['entry'],library=True))
        repaired,rw=compile_source(bundle(EXPECTED['assembly']['repaired_entry'],library=True))
        self.assertEqual(set(original.model.objects),{'first','sibling'})
        self.assertEqual(original.bundle.modules,repaired.bundle.modules)
        self.assertEqual(original.surface_meshes['sibling']['mesh'],repaired.surface_meshes['sibling']['mesh'])
        first=original.surface_meshes['first']['mesh'];changed=repaired.surface_meshes['first']['mesh']
        self.assertEqual(first.vertex_keys,changed.vertex_keys)
        self.assertAlmostEqual(totals(first)[1],1.25)
        self.assertAlmostEqual(totals(changed)[1],1.375)
        self.assertEqual(original.model.objects['first'].element_id,repaired.model.objects['first'].element_id)
        for obj in repaired.model.objects.values():self.assertEqual(obj.physical['kind'],'no_body')

    def test_generated_reusable_parts_retain_depths_keys_and_following(self):
        program=bundle(EXPECTED['generated']['entry'],library=True)
        result,compiler,ledger=export(program)
        self.assertEqual(set(compiler.surface_meshes),
                         {'array.brackets["left"]','array.brackets["middle"]','array.brackets["right"]'})
        for name,expected in EXPECTED['generated']['parts'].items():
            path='array.brackets["'+name+'"]';value=compiler.surface_meshes[path]['mesh']
            self.assertAlmostEqual(totals(value)[1],expected['geometry']['volume_m3'])
        self.assertEqual(result.report['validation']['status'],'passed')

    def test_local_placement_is_baked_once_without_adding_physical_matter(self):
        compiler,ledger=compile_source(bundle('placed-bracket.ok'))
        obj=compiler.model.objects['shape'];value=build_surface_mesh(obj.geometry)
        self.assertEqual(value.name,'extrusion')
        self.assertEqual(obj.physical['kind'],'no_body')
        self.assertEqual([min(p[i] for p in value.positions) for i in range(3)],[.5,-3.5,-.04999999999999999])
        self.assertEqual([max(p[i] for p in value.positions) for i in range(3)],[3.5,-.5,.2])

    def test_explicit_header_admission_cannot_mix_versions_or_profiles(self):
        source=bundle()
        with self.assertRaises(OntoKinError):admit_entry_budget(source.entry,SharedExecutionBudget())
        with self.assertRaises(OntoKinError):
            compile_construction(source)
        text=source.entry.text.replace('ontokin "0.8"','ontokin "0.7"')
        with self.assertRaises(OntoKinError):compile_source(bundle(text=text))

    def test_old_declaring_module_cannot_import_new_extrusion_definitions(self):
        text=(ROOT/EXPECTED['assembly']['entry']).read_text().replace('ontokin "0.8"','ontokin "0.7"').replace(EXTRUSION_PROFILE,BUDGET_PROFILE)
        with self.assertRaises(OntoKinError) as caught:
            compile_source(bundle(text=text,library=True),profile=BUDGET_PROFILE)
        self.assertEqual(caught.exception.code,'OKL-E-CAPABILITY-UNSUPPORTED')
        self.assertEqual(caught.exception.diagnostic.details['dependency_profile'],EXTRUSION_PROFILE)

    def test_intrinsic_point_and_vertex_types_work_in_pure_functions(self):
        text=(ROOT/'rectangle.ok').read_text()
        text=text.replace('public class Shape',
            'public fn make_point @ "make-point"(x: Length, y: Length) -> PlanarPoint { return planar_point(x, y); }\npublic class Shape')
        text=text.replace('polygon_vertex(0, planar_point(0[m], 0[m])','polygon_vertex(0, make_point(0[m], 0[m])')
        compiler,ledger=compile_source(bundle(text=text))
        self.assertEqual(compiler.surface_meshes['shape']['mesh'].triangle_count,12)

    def test_constructor_arity_and_exact_parameter_types(self):
        text=(ROOT/'rectangle.ok').read_text()
        for before,after in [('polygon_vertex(0,','polygon_vertex(0.5,'),
                             ('planar_point(0[m], 0[m])','planar_point(0[m])'),
                             ('polygon_vertex(0, planar_point(0[m], 0[m]), "side")',
                              'polygon_vertex(0, vec3(0[m], 0[m], 0[m]), "side")')]:
            with self.subTest(after=after):
                with self.assertRaises(OntoKinError) as caught:compile_source(bundle(text=text.replace(before,after,1)))
                self.assertEqual(caught.exception.code,'OKL-E-TYPE')

    def test_source_budget_requests_keep_host_authority_and_original_ledger(self):
        text=(ROOT/'rectangle.ok').read_text().replace('profile "polygon-extrusion-0.1";',
                   'profile "polygon-extrusion-0.1";\nexecution { max_operations = 200000; max_elapsed = 60[s]; }')
        with self.assertRaises(OntoKinError) as caught:compile_source(bundle(text=text))
        self.assertEqual(caught.exception.diagnostic.details['budget_reason'],'host_ceiling_exceeded')
        compiler,ledger=compile_source(bundle(text=text),policy=HostPolicy(200000,60000))
        start=ledger.started;consumed=ledger.operations
        export_glb(compiler.model,options=ExportOptions(fps=4),target_contract=EXTRUSION_TARGET,work=compiler.reach_work)
        self.assertEqual(ledger.started,start)
        self.assertGreater(ledger.operations,consumed)
        with self.assertRaises(OntoKinError) as caught:
            compile_source(bundle(),caps={'max_operations':100})
        self.assertEqual(caught.exception.diagnostic.details['budget_reason'],'operation_budget_exhausted')

    def test_geometry_cancellation_preserves_the_callers_exception(self):
        marker=RuntimeError('cancel request');counter=0
        def cancel():
            nonlocal counter
            counter+=1
            if counter==650:raise marker
        with self.assertRaises(RuntimeError) as caught:compile_source(bundle(),callback=cancel)
        self.assertIs(caught.exception,marker)

    def test_source_and_artifact_cannot_silently_select_an_old_destination(self):
        result,compiler,ledger=export(bundle())
        with self.assertRaises(OntoKinError):read_glb(result.data)
        with self.assertRaises(OntoKinError):
            read_glb(result.data,target_contract='ontokin.glb/0.7',work=compiler.reach_work)
        with self.assertRaises(OntoKinError):
            export_glb(compiler.model,target_contract='ontokin.glb/0.7',work=compiler.reach_work)
        with self.assertRaises(OntoKinError):
            export_glb(compiler.model,target_contract=EXTRUSION_TARGET)

    def test_exported_polygon_metadata_describes_the_actual_family(self):
        result,compiler,ledger=export(bundle())
        decoded=read_glb(result.data,target_contract=EXTRUSION_TARGET,work=compiler.reach_work)
        metadata=decoded.document['extras']['ontokin']
        self.assertEqual(metadata['polygon_extrusion_profile']['name'],EXTRUSION_PROFILE)
        surface=decoded.document['nodes'][0]['extras']['ontokin']['surface']
        self.assertEqual(surface['family'],'polygon_extrusion')
        self.assertEqual(surface['vertex_keys'],['v0','v1','v2','v3'])
        self.assertEqual(surface['depth_m'],.5)


if __name__=='__main__':unittest.main()
