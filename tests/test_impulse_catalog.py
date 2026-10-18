"""Profile-specific discovery and public schema inheritance for source impulses."""
import copy
import hashlib
import json
from pathlib import Path
import unittest

from ontokin.bundle import load_file_manifest
from ontokin.construction_catalog import catalog
from ontokin.diagnostics import OntoKinError
from ontokin.linker import link_program
from tests.test_surface_source import bundle as studio_bundle


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "docs/language-design/impulse-v0.1"


class ImpulseCatalogTests(unittest.TestCase):
    def test_explicit_catalog_preserves_complete_older_payloads_and_hashes(self):
        old = catalog(); surface = catalog(profile="surface-0.1")
        self.assertEqual(old["revision"],"sha256:7c997692ee8d2516bc897ad898f34d101affb97ccb4a7eb95921bcd3b5f9f490")
        self.assertEqual(surface["revision"],"sha256:e11dab7746fa2ee9f7b36f172cef110fbb226e7a5f8b7cb5786dc07ee9234c35")
        result = catalog(profile="impulse-0.1")
        self.assertEqual((result['schema_version'],result['language_version'],result['agent_contract']),
                         ('ontokin.agent-catalog/0.4','0.4','ontokin.agent/0.4'))
        self.assertEqual(result['delivery_targets'],['ontokin.glb/0.4'])
        self.assertFalse(result['full_product_conformance_certified'])
        self.assertEqual(catalog(),old); self.assertEqual(catalog(profile='surface-0.1'),surface)
        self.assertEqual(result['limits'],surface['limits'])
        self.assertEqual(len({i['id'] for i in result['items']}),len(result['items']))

    def test_source_impulse_is_an_event_and_unsupported_physics_remains_explicit(self):
        result=catalog(profile='impulse-0.1')
        events={i['name']:i for i in result['items'] if i['kind']=='event'}
        self.assertIn('impulse',events); self.assertIn('release',events)
        self.assertIn('source_impulses',events['impulse']['capability'])
        self.assertTrue(any("own frame" in d for d in events['impulse']['domains']) or
                        any("object's frame" in d for d in events['impulse']['domains']))
        operations={i['name'] for i in result['items'] if i['kind']=='operation'}
        self.assertTrue({'impulse','apply_impulse','set_state'}.isdisjoint(operations))
        for name in ('source_impulses','bounded_impulse_state'):
            item=next(i for i in result['items'] if i['kind']=='capability' and i['name']==name)
            self.assertNotEqual(item['availability'],'unsupported')
        forces=next(i for i in result['items'] if i['name']=='external_forces_and_actuators')
        self.assertEqual(forces['availability'],'unsupported')
        self.assertIn('Finite force intervals',forces['description'])
        self.assertIn('continuous torques',forces['description'])
        self.assertNotIn('motors, impulses',forces['description'])
        self.assertIn('contact',json.dumps(result['unavailable_capabilities']))
        dynamic=next(i for i in result['items'] if i['kind']=='constant' and i['name']=='dynamic')
        self.assertIn('instantaneous impulses',dynamic['description'])

    def test_catalog_example_is_the_exact_adopted_mixed_source_closure(self):
        result=catalog(profile='impulse-0.1')
        program=load_file_manifest(ROOT/result['example_file_manifests'][0])
        manifest=json.loads((FIXTURES/'acceptance.json').read_text())
        case=next(c for c in manifest['source_cases'] if c['id']=='P02')
        self.assertEqual(program.program_revision,case['program_revision'])
        for dependency in result['example_bundles'][0]['dependencies']:
            raw=(ROOT/dependency['path']).read_bytes()
            self.assertEqual(dependency['source_revision'],'sha256:'+hashlib.sha256(raw).hexdigest())
            unit=next(u for u in program.modules if u.package_id==dependency['package_id'])
            self.assertEqual(unit.raw,raw)
        self.assertEqual(result['compatible_definition_profiles'],['construction-0.1','surface-0.1','impulse-0.1'])
        for item in result['items']:
            self.assertTrue((ROOT/item['specification']).is_file(),item['specification'])

    def test_detached_catalog_revision_covers_actual_payload_and_cancellation(self):
        first=catalog(profile='impulse-0.1'); original=copy.deepcopy(first)
        revision=first.pop('revision')
        raw=json.dumps(first,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
        self.assertEqual(revision,'sha256:'+hashlib.sha256(raw).hexdigest())
        first['items'][0]['domains'].append('tampered')
        self.assertEqual(catalog(profile='impulse-0.1'),original)
        marker=ValueError('interrupt exact identity')
        def cancel(): raise marker
        with self.assertRaises(ValueError) as caught:
            catalog(profile='impulse-0.1',check=cancel)
        self.assertIs(caught.exception,marker)
        for profile in ('impulse-0.2','core-0.1',None,[]):
            with self.subTest(profile=profile),self.assertRaises(OntoKinError): catalog(profile=profile)

    def test_mismatched_entry_is_rejected_without_relabelling_its_catalog(self):
        linked=link_program(studio_bundle())
        with self.assertRaises(OntoKinError) as caught:
            catalog(linked_program=linked,profile='impulse-0.1')
        self.assertEqual(caught.exception.code,'OKL-E-CAPABILITY-UNSUPPORTED')
        self.assertEqual(caught.exception.diagnostic.details,{'required_profile':'impulse-0.1','actual_profile':'surface-0.1'})

    def test_actual_mixed_import_declarations_keep_each_authored_profile(self):
        manifest=json.loads((FIXTURES/'acceptance.json').read_text())
        case=next(c for c in manifest['source_cases'] if c['id']=='P02')
        program=load_file_manifest(FIXTURES/case['file_manifest'])
        result=catalog(linked_program=link_program(program),profile='impulse-0.1')
        expected={
            'entry':('0.4','impulse-0.1'),
            'package:fixture.impulse-parts@1.0.0':('0.4','impulse-0.1'),
            'package:fixture.surface-parts@1.0.0':('0.3','surface-0.1'),
            'package:fixture.impulse-vectors@1.0.0':('0.2','construction-0.1'),
        }
        declarations=[i for i in result['items'] if 'source_id' in i]
        self.assertEqual({i['source_id'] for i in declarations},set(expected))
        for item in declarations:
            self.assertEqual((item['language_version'],item['profile']),expected[item['source_id']])
            self.assertEqual(item['source_revision'],program.sources[item['source_id']].revision)
            self.assertEqual(item['program_revision'],program.program_revision)
            span=item['source_span']
            self.assertGreater(span['end_byte'],span['start_byte'])

    def test_new_schema_reuses_exact_nested_geometry_and_diagnostic_contracts(self):
        old=ROOT/'docs/language-design/agent-v0.3'; new=ROOT/'docs/language-design/agent-v0.4'
        before=json.loads((old/'response.schema.json').read_text())
        after=json.loads((new/'response.schema.json').read_text())
        self.assertEqual(after['properties']['schema_version'],{'const':'ontokin.agent/0.4'})
        for name in ('surface_summary','mesh_page_result'):
            self.assertEqual(after['$defs'][name],before['$defs'][name])
            self.assertEqual(after['$defs'][name]['properties']['profile'],{'const':'surface-0.1'})
        self.assertEqual(after['$defs']['impulses']['$ref'],'https://ontokin.org/schemas/impulse-v0.1/impulses.schema.json')
        diagnostic=json.loads((new/'diagnostic.schema.json').read_text())
        self.assertEqual(diagnostic['$ref'],'https://omegapy.github.io/OntoKin/schemas/ontokin.diagnostic-0.2.json')
        operations=after['properties']['operation']['enum']
        self.assertEqual(operations,before['properties']['operation']['enum'])
        self.assertNotIn('impulse',operations)


if __name__=='__main__': unittest.main()
