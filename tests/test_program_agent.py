"""Program revision, real generated inspection and atomic source-edit acceptance."""
from pathlib import Path
import copy
import json
import tempfile
import unittest

from ontokin.agent import AgentService
from ontokin.bundle import load_bundle
from ontokin.program_agent import ProgramAgentService

FIXTURE = Path(__file__).resolve().parents[1] / 'docs/language-design/construction-v0.1/01-keyed-rack/program.bundle.json'


class ProgramAgentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.service = ProgramAgentService(Path(self.temp.name))
        self.payload = json.loads(FIXTURE.read_text())
        self.original = load_bundle(self.payload)
        self.sequence = 0

    def tearDown(self):
        self.service.close()
        self.temp.cleanup()

    def request(self, operation, **fields):
        self.sequence += 1
        return {'schema_version': 'ontokin.agent/0.2', 'project_id': 'program',
                'request_id': f'r{self.sequence}', 'operation': operation, **fields}

    def send(self, operation, **fields):
        return self.service.handle(self.request(operation, **fields))

    def create(self, level='evaluated', payload=None):
        response = self.send('create', bundle=payload or self.payload, expected_program_revision=None, requested_level=level)
        self.assertEqual(response['status'], 'succeeded', response)
        return response['program_revision']

    def inspect(self, revision, path, fields=None, **extra):
        response = self.send('inspect', program_revision=revision, selector={'path': path},
                             fields=fields or ['identity', 'source', 'values'], limit=1, **extra)
        self.assertEqual(response['status'], 'succeeded', response)
        self.assertEqual(response['result']['total'], 1)
        return response['result']['items'][0]

    def patch(self, source_id, old, new, element_id=None, program=None):
        program = program or self.original
        source = program.sources[source_id]
        start = source.raw.index(old.encode())
        return {'source_id': source_id, 'source_revision': source.revision,
                'element_id': element_id or ['sources', source_id], 'start_byte': start,
                'end_byte': start + len(old.encode()), 'expected_text': old, 'replacement': new}

    def test_complete_program_identity_and_independent_store(self):
        revision = self.create()
        self.assertEqual(revision, self.original.program_revision)
        self.assertNotEqual(revision, self.original.entry.revision)
        self.assertEqual(self.service.read_program('program', revision).to_payload(), self.payload)
        with AgentService(Path(self.temp.name)) as legacy:
            self.assertIsNone(legacy.accepted_revision('program'))
            self.assertNotEqual(legacy.database_path, self.service.database_path)

    def test_unverified_patch_coordinates_do_not_invent_source_locations(self):
        revision = self.create()
        original = self.patch('entry', '0.75[m]', '0.8[m]')
        stale = copy.deepcopy(original)
        stale['source_revision'] = 'sha256:' + '0' * 64
        outside = copy.deepcopy(original)
        outside.update(start_byte=len(self.original.entry.raw) + 10,
                       end_byte=len(self.original.entry.raw) + 11)
        for patch in [stale, outside]:
            with self.subTest(patch=patch):
                response = self.send('edit', expected_program_revision=revision,
                                     patches=[patch], requested_level='constructed')
                self.assertEqual(response['status'], 'rejected', response)
                diagnostic = response['diagnostics'][0]
                self.assertEqual(diagnostic['code'], 'OKL-E-REVISION')
                self.assertIsNone(diagnostic['primary'])
                self.assertEqual(diagnostic['location_status'], 'program_condition_without_source_span')
                self.assertEqual(diagnostic['details']['submitted_start_byte'], patch['start_byte'])
                self.assertEqual(diagnostic['details']['submitted_source_revision'], patch['source_revision'])
                self.assertEqual(response['accepted_program_revision'], revision)
        self.assertEqual(self.service.read_program('program', revision).entry.raw, self.original.entry.raw)
        self.assertEqual(self.service.database_path.name, 'program-agent.sqlite3')

    def test_generated_source_locations_and_public_initializer_target(self):
        revision = self.create('represented')
        item = self.inspect(revision, 'first.fingers["middle"].length')
        self.assertEqual(item['values']['length']['value'], .75)
        self.assertEqual(item['source']['source_id'], 'package:example.hinges@1.0.0')
        self.assertEqual(item['source']['writable_spans'], [])
        target = item['source']['initializer_target']
        self.assertEqual(target['rendered_path'], 'fingers["middle"].length')
        self.assertEqual(target['parameter_path'][1], {'kind': 'key', 'value': 'middle'})
        source = self.original.sources[target['assignment_span']['source_id']]
        span = target['assignment_span']
        self.assertEqual(source.raw[span['start_byte']:span['end_byte']].decode(), 'fingers["middle"].length = 0.75[m];')
        generated = self.inspect(revision, 'first.fingers["middle"]', ['identity', 'source'])
        self.assertIsNone(generated['source']['span'])
        self.assertFalse(generated['source']['generated']['unique_declaration_span'])

    def test_scoped_repair_changes_one_generated_occurrence_only(self):
        revision = self.create()
        patch = self.patch('entry', '0.75[m]', '0.9[m]', ['keyed-rack', 'demo', 'first'])
        response = self.send('edit', expected_program_revision=revision, requested_level='evaluated', patches=[patch])
        self.assertEqual(response['status'], 'succeeded', response)
        changed = response['program_revision']
        self.assertNotEqual(changed, revision)
        self.assertEqual(self.inspect(changed, 'first.fingers["middle"].length')['values']['length']['value'], .9)
        self.assertEqual(self.inspect(changed, 'second.fingers["middle"].length')['values']['length']['value'], .6)
        self.assertEqual(self.service.read_unit('program', changed, 'package:example.hinges@1.0.0').raw, self.original.modules[0].raw)
        self.assertEqual(self.service.read_unit('program', revision, 'entry').raw, self.original.entry.raw)

    def test_invalid_candidate_has_its_actual_unit_hash_and_preserves_head(self):
        revision = self.create()
        response = self.send('edit', expected_program_revision=revision, requested_level='evaluated',
                             patches=[self.patch('entry', '0.75[m]', '0.75[kg]', ['keyed-rack', 'demo', 'first'])])
        self.assertEqual(response['status'], 'rejected', response)
        candidate = response['program_revision']
        self.assertNotEqual(candidate, revision)
        source = self.service.read_unit('program', candidate, 'entry')
        diagnostic = response['diagnostics'][0]
        self.assertEqual(diagnostic['schema_version'], 'ontokin.diagnostic/0.2')
        self.assertEqual(diagnostic['program_revision'], candidate)
        self.assertEqual(diagnostic['source_revision'], source.revision)
        self.assertEqual(diagnostic['primary']['source_id'], 'entry')
        self.assertIn(b'0.75[kg]', source.raw)
        self.assertEqual(self.service.accepted_revision('program'), revision)
        forbidden = self.send('evaluate', program_revision=candidate, run_id=None, until_seconds='1')
        self.assertEqual(forbidden['status'], 'rejected')
        inspected = self.send('inspect', program_revision=candidate, selector={'kind': 'source', 'source_id': 'entry'},
                              fields=['source', 'state'], limit=1)
        self.assertEqual(inspected['status'], 'succeeded', inspected)
        self.assertFalse(inspected['result']['index_complete'])
        self.assertFalse(inspected['result']['items'][0]['state']['available'])

    def test_generated_identity_cannot_write_shared_library_bytes(self):
        revision = self.create('represented')
        patch = self.patch('package:example.hinges@1.0.0', '0.6[m]', '0.9[m]',
                           ['keyed-rack', 'demo', 'first', 'fingers', 'middle'])
        response = self.send('edit', expected_program_revision=revision, requested_level='represented', patches=[patch])
        self.assertEqual(response['status'], 'rejected', response)
        self.assertEqual(response['diagnostics'][0]['code'], 'OKL-E-REVISION')
        self.assertEqual(self.service.accepted_revision('program'), revision)

    def test_library_change_and_exact_import_pin_are_one_candidate(self):
        revision = self.create('represented')
        module = copy.deepcopy(self.payload['modules'][0])
        module['source'] += '\n// Library revision β\n'
        replacement = load_bundle({'schema_version':'ontokin.bundle/0.1','entry':self.payload['entry'],'modules':[module]})
        pin = self.patch('entry', self.original.modules[0].revision, replacement.modules[0].revision)
        change = {'operation':'replace','source_id':self.original.modules[0].source_id,
                  'source_revision':self.original.modules[0].revision,'module':module}
        failed = self.send('edit', expected_program_revision=revision, requested_level='represented', patches=[], module_changes=[change])
        self.assertEqual(failed['status'], 'rejected', failed)
        self.assertEqual(self.service.accepted_revision('program'), revision)
        response = self.send('edit', expected_program_revision=revision, requested_level='evaluated', patches=[pin], module_changes=[change])
        self.assertEqual(response['status'], 'succeeded', response)
        bundle = self.service.read_program('program', response['program_revision'])
        self.assertEqual(bundle.modules[0].raw, module['source'].encode())
        self.assertIn(bundle.modules[0].revision, bundle.entry.text)
        self.assertEqual(self.service.read_program('program', revision).modules[0].raw, self.original.modules[0].raw)

    def test_entry_and_library_patch_is_atomic_on_wrong_source_precondition(self):
        revision = self.create('represented')
        patch = self.patch('entry', '0.75[m]', '0.8[m]')
        library = self.patch(self.original.modules[0].source_id, '0.6[m]', '0.7[m]')
        library['source_revision'] = 'sha256:' + '0'*64
        response = self.send('edit', expected_program_revision=revision, requested_level='represented', patches=[patch, library])
        self.assertEqual(response['status'], 'rejected', response)
        self.assertEqual(self.service.read_unit('program', revision, 'entry').raw, self.original.entry.raw)
        self.assertEqual(self.service.accepted_revision('program'), revision)

    def test_utf8_boundary_failure_uses_original_source_location(self):
        payload = copy.deepcopy(self.payload)
        payload['entry']['source'] += '\n// café\n'
        revision = self.create('represented', payload)
        program = self.service.read_program('program', revision)
        start = program.entry.raw.index('é'.encode()) + 1
        patch = {'source_id':'entry','source_revision':program.entry.revision,'element_id':['sources','entry'],
                 'start_byte':start,'end_byte':start,'expected_text':'','replacement':'x'}
        response = self.send('edit', expected_program_revision=revision, requested_level='represented', patches=[patch])
        self.assertEqual(response['status'], 'rejected')
        self.assertEqual(response['diagnostics'][0]['primary']['source_id'], 'entry')
        self.assertEqual(self.service.accepted_revision('program'), revision)

    def test_source_only_state_prefix_and_old_program_run_isolation(self):
        revision = self.create('represented')
        self.assertFalse(self.inspect(revision, 'first', ['state'])['state']['available'])
        run = self.send('evaluate', program_revision=revision, run_id=None, until_seconds='0.5')
        self.assertEqual(run['status'], 'succeeded', run)
        item = self.inspect(revision, 'first', ['state'], run_id=run['run_id'], time={'seconds':'0.5','side':'after'})
        self.assertEqual(item['state']['program_revision'], revision)
        self.assertAlmostEqual(item['state']['position_m'][1], .1)
        edit = self.send('edit', expected_program_revision=revision, requested_level='represented', patches=[self.patch('entry','0.75[m]','0.8[m]')])
        self.assertEqual(edit['status'],'succeeded',edit)
        wrong = self.send('evaluate', program_revision=edit['program_revision'], run_id=run['run_id'], until_seconds='1')
        self.assertEqual(wrong['status'],'rejected',wrong)
        old = self.inspect(revision, 'first', ['state'], run_id=run['run_id'])
        self.assertEqual(old['state']['program_revision'], revision)

    def test_cursor_is_bound_to_program_and_immutable_query(self):
        revision = self.create('represented')
        first = self.send('inspect', program_revision=revision, selector={'kind':'object'}, fields=['identity'], limit=1)
        self.assertTrue(first['truncated'])
        edit = self.send('edit', expected_program_revision=revision, requested_level='represented', patches=[self.patch('entry','0.75[m]','0.8[m]')])
        response = self.send('inspect', program_revision=edit['program_revision'], selector={'kind':'object'},
                             fields=['identity'], limit=1, cursor=first['next_cursor'])
        self.assertEqual(response['status'],'rejected',response)
        self.assertEqual(response['protocol_error']['code'],'OKL-E-REVISION')
        old = self.send('inspect',program_revision=revision,selector={'kind':'object'},fields=['identity'],limit=1,cursor=first['next_cursor'])
        self.assertEqual(old['status'],'succeeded',old)
        self.assertNotEqual(old['result']['items'][0]['element_id'],first['result']['items'][0]['element_id'])

    def test_result_budget_failure_rolls_back_computed_acceptance_and_run(self):
        original_execute = self.service._execute
        def oversized(task, check):
            original_execute(task, check)
            task.response['result']['oversized_fixture'] = 'x'*(4*1024*1024)
        self.service._execute = oversized
        response = self.send('create', bundle=self.payload, expected_program_revision=None, requested_level='evaluated')
        self.assertEqual(response['status'],'failed',response)
        self.assertEqual(response['protocol_error']['code'],'OKA-E-RESOURCE')
        self.assertIsNone(self.service.accepted_revision('program'))
        with self.service._store.connection() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM runs').fetchone()[0],0)
            self.assertEqual(db.execute('SELECT count(*) FROM artifacts').fetchone()[0],0)
        self.assertEqual(self.service.read_program('program',self.original.program_revision).to_payload(),self.payload)

    def test_generated_nominal_replacement_requires_new_occurrence_key(self):
        revision = self.create('represented')
        module = copy.deepcopy(self.payload['modules'][0])
        module['source'] = module['source'].replace('class Finger @ "finger"', 'class Finger @ "finger-v2"')
        replacement = load_bundle({'schema_version':'ontokin.bundle/0.1','entry':self.payload['entry'],'modules':[module]})
        response = self.send('edit', expected_program_revision=revision, requested_level='represented',
                             patches=[self.patch('entry', self.original.modules[0].revision, replacement.modules[0].revision)],
                             module_changes=[{'operation':'replace','source_id':self.original.modules[0].source_id,
                                              'source_revision':self.original.modules[0].revision,'module':module}])
        self.assertEqual(response['status'],'rejected',response)
        self.assertEqual(response['diagnostics'][0]['code'],'OKL-E-ID')
        self.assertEqual(self.service.accepted_revision('program'),revision)
        self.assertIn(['keyed-rack','demo','first','fingers','middle'], response['diagnostics'][0]['details']['changed_occurrences'])

    def test_retrieved_old_artifact_keeps_its_original_program_after_edit(self):
        import base64,hashlib
        revision=self.create('evaluated')
        exported=self.send('export',program_revision=revision,destination='ontokin.glb/0.2')
        self.assertEqual(exported['status'],'succeeded',exported)
        self.assertEqual(exported['result']['report']['program_revision'],revision)
        changed=self.send('edit',expected_program_revision=revision,requested_level='represented',patches=[self.patch('entry','0.75[m]','0.8[m]')])
        self.assertEqual(changed['status'],'succeeded',changed)
        data=bytearray();offset=0
        while offset is not None:
            response=self.send('artifact',artifact_id=exported['result']['artifact_id'],offset=offset,max_bytes=65536)
            self.assertEqual(response['status'],'succeeded',response)
            self.assertEqual(response['program_revision'],revision)
            self.assertEqual(response['accepted_program_revision'],changed['program_revision'])
            part=response['result']
            self.assertEqual(part['program_revision'],revision)
            data.extend(base64.b64decode(part['data_base64'],validate=True));offset=part['next_offset']
        self.assertEqual('sha256:'+hashlib.sha256(data).hexdigest(),exported['result']['sha256'])
        document=json.loads(data[20:20+int.from_bytes(data[12:16],'little')])
        self.assertEqual(document['extras']['ontokin']['program']['revision'],revision)
        self.assertNotEqual(document['extras']['ontokin']['program']['revision'],changed['program_revision'])


if __name__ == '__main__':
    unittest.main()
