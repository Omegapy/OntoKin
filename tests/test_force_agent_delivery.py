"""Actual force delivery, prefix authority and atomic publication failures."""
from __future__ import annotations

import base64
import copy
import hashlib
import unittest
from unittest.mock import patch

from ontokin.json_limits import measure_json
from test_export import DecodedGLB
import test_force_agent as support


TARGET = 'ontokin.glb/0.5'
OPTIONS = {'end': '2.5', 'fps': 2, 'helpers': False}


class ForceAgentDeliveryTests(unittest.TestCase):
    setUp = support.ForceAgentTests.setUp
    tearDown = support.ForceAgentTests.tearDown
    request = support.ForceAgentTests.request
    send = support.ForceAgentTests.send
    success = support.ForceAgentTests.success
    error = support.ForceAgentTests.error
    create = support.ForceAgentTests.create
    head = support.ForceAgentTests.head

    def effects(self, project='force'):
        with self.service._store.connection() as db:
            return {table: db.execute('SELECT count(*) FROM ' + table + ' WHERE project_id=?',
                                     (project,)).fetchone()[0]
                    for table in ('runs', 'artifacts')}

    def test_actual_export_retrieves_complete_revision_bound_glb_and_exact_retry(self):
        program, _ = self.create()
        request = self.request('export', program_revision=program.program_revision,
                               destination=TARGET, options=OPTIONS)
        response = self.success(self.service.handle(request))
        self.assertEqual(response['achieved_level'], 'delivered')
        result = response['result']
        self.assertEqual(result['destination'], TARGET)
        self.assertEqual(result['program_revision'], program.program_revision)
        self.assertEqual(result['report']['program_revision'], program.program_revision)
        self.assertEqual(result['run_state']['valid_until_seconds'], '2.5')
        self.assertEqual(result['run_state']['valid_until_side'], 'after')
        self.assertEqual(self.service.handle(request), response)
        self.assertEqual(self.effects(), {'runs': 1, 'artifacts': 1})
        changed = copy.deepcopy(request)
        changed['options']['end'] = '2'
        self.assertEqual(self.service.handle(changed)['status'], 'rejected')
        self.assertEqual(self.effects(), {'runs': 1, 'artifacts': 1})

        chunks = []
        offset = 0
        while offset < result['total_bytes']:
            reply = self.success(self.send('artifact', artifact_id=result['artifact_id'],
                                            offset=offset, max_bytes=32768))
            chunk = reply['result']
            self.assertEqual(chunk['artifact_provenance']['program_revision'], program.program_revision)
            self.assertEqual(chunk['sha256'], result['sha256'])
            data = base64.b64decode(chunk['data_base64'], validate=True)
            self.assertTrue(data)
            chunks.append(data)
            offset += len(data)
        data = b''.join(chunks)
        self.assertEqual(len(data), result['total_bytes'])
        self.assertEqual('sha256:' + hashlib.sha256(data).hexdigest(), result['sha256'])
        decoded = DecodedGLB(data)
        metadata = decoded.document['extras']['ontokin']
        self.assertEqual(metadata['target_contract'], TARGET)
        self.assertEqual(metadata['program']['revision'], program.program_revision)
        self.assertAlmostEqual(decoded.node_pose('ball', 1.5)['translation'][0], .25, delta=.001)
        self.assertEqual(self.head(), program.program_revision)
        self.assertEqual(self.service.read_program('force', program.program_revision), program)
        self.error(self.send('artifact', artifact_id=result['artifact_id'],
                             offset=result['total_bytes'] + 1), 'OKA-E-ARTIFACT')
        foreign = self.request('artifact', artifact_id=result['artifact_id'], max_bytes=64)
        self.error(self.service.handle({**foreign, 'project_id': 'foreign'}), 'OKA-E-ARTIFACT')
        self.service.close()
        self.service = support.ProgramAgentService(self.tmp.name, protocol=support.PROTOCOL)
        self.assertEqual(self.service.handle(request), response)
        retained = self.success(self.send('artifact', artifact_id=result['artifact_id'], max_bytes=64))
        self.assertEqual(base64.b64decode(retained['result']['data_base64']), data[:64])
        self.assertEqual(retained['result']['artifact_provenance']['program_revision'], program.program_revision)

    def test_short_prefix_delivery_uses_the_same_end_for_create_validate_and_export(self):
        program = support.source_case('P21')
        options = {'end': '1', 'fps': 2, 'helpers': False}
        for operation in ('create', 'validate', 'export'):
            project = 'prefix-' + operation
            if operation != 'create':
                request = self.request('create', bundle=program.to_payload(),
                    expected_program_revision=None, requested_level='constructed')
                self.success(self.service.handle({**request, 'project_id': project}))
            if operation == 'create':
                fields = {'bundle': program.to_payload(), 'expected_program_revision': None,
                          'requested_level': 'delivered'}
            else:
                fields = {'program_revision': program.program_revision}
                if operation == 'validate':
                    fields['requested_level'] = 'delivered'
            request = self.request(operation, **fields, destination=TARGET, options=options)
            with self.subTest(operation=operation):
                response = self.success(self.service.handle({**request, 'project_id': project}))
                self.assertEqual(response['achieved_level'], 'delivered')
                self.assertEqual(response['accepted_program_revision'], program.program_revision)
                self.assertEqual(response['result']['run_state']['valid_until_seconds'], '1')
                self.assertEqual(response['result']['report']['sampling']['end_seconds'], '1')
                self.assertEqual(response['result']['run_state']['last_valid_state']['objects']['ball']['position_m'], [1, 0, 0])
                self.assertEqual(self.effects(project), {'runs': 1, 'artifacts': 1})
                inspect = self.request('inspect', program_revision=program.program_revision,
                    run_id=response['run_id'], selector={'path': 'ball'}, fields=['state'], limit=1,
                    time={'seconds': '1.5', 'side': 'after'})
                self.error(self.service.handle({**inspect, 'project_id': project}), 'OKL-E-SAMPLE')

    def test_omitted_end_keeps_full_horizon_failure_and_no_artifact(self):
        program, _ = self.create('P21')
        response = self.error(self.send('export', program_revision=program.program_revision,
                                        destination=TARGET), 'OKL-E-NUMERIC')
        self.assertNotEqual(response['achieved_level'], 'delivered')
        self.assertEqual(self.head(), program.program_revision)
        self.assertEqual(self.effects()['artifacts'], 0)

    def test_failed_delivery_of_changed_source_preserves_head_and_old_artifacts(self):
        original, _ = self.create()
        delivered = self.success(self.send('export', program_revision=original.program_revision,
                                           destination=TARGET, options=OPTIONS))
        before = self.effects()
        changed = support.source_case('P21')
        response = self.error(self.send('edit', expected_program_revision=original.program_revision,
            patches=[support.minimal_patch(original, changed, support.SCENE)],
            requested_level='delivered', destination=TARGET), 'OKL-E-NUMERIC')
        self.assertEqual(response['accepted_program_revision'], original.program_revision)
        self.assertEqual(response['program_revision'], changed.program_revision)
        self.assertEqual(self.effects()['artifacts'], before['artifacts'])
        retained = self.success(self.send('artifact', artifact_id=delivered['result']['artifact_id'],
                                          max_bytes=64))
        self.assertEqual(retained['result']['sha256'], delivered['result']['sha256'])
        self.error(self.send('export', program_revision=changed.program_revision,
                            destination=TARGET, options={'end': '1'}), 'OKL-E-REVISION')

    def test_final_delivery_budget_rolls_back_force_source_run_and_artifact(self):
        original, _ = self.create('P10')
        changed = support.source_case('P12')
        baseline_create = self.request('create', bundle=original.to_payload(),
            expected_program_revision=None, requested_level='constructed')
        self.success(self.service.handle({**baseline_create, 'project_id': 'baseline'}))
        fields = dict(expected_program_revision=original.program_revision,
            patches=[support.minimal_patch(original, changed, support.SCENE)],
            requested_level='delivered', destination=TARGET,
            options={'end': '2', 'fps': 2, 'helpers': False})
        baseline_request = self.request('edit', **fields)
        baseline = self.success(self.service.handle({**baseline_request, 'project_id': 'baseline'}))
        entries = measure_json(baseline)['entries']
        before = self.effects()
        prepared = []
        execute = self.service._execute

        def observe(task, check):
            execute(task, check)
            prepared.append((task.accept, task.run is not None, task.artifact is not None))

        with patch.object(self.service, '_execute', side_effect=observe):
            failed = self.error(self.send('edit', **fields,
                               budgets={'max_value_entries': entries - 1}), 'OKA-E-RESOURCE')
        self.assertEqual(prepared, [(True, True, True)])
        self.assertFalse(failed['protocol_error']['details']['effects_committed'])
        self.assertEqual(failed['accepted_program_revision'], original.program_revision)
        self.assertEqual(failed['program_revision'], changed.program_revision)
        self.assertIsNone(failed['run_id'])
        self.assertIsNone(failed['result'])
        self.assertEqual(self.effects(), before)
        exact = self.success(self.send('edit', **fields, budgets={'max_value_entries': entries}))
        self.assertEqual(exact['accepted_program_revision'], changed.program_revision)
        self.assertEqual(measure_json(exact)['entries'], entries)

    def test_cancel_after_real_delivery_prevents_source_run_and_artifact_publication(self):
        original, _ = self.create('P10')
        changed = support.source_case('P12')
        request = self.request('edit', expected_program_revision=original.program_revision,
            patches=[support.minimal_patch(original, changed, support.SCENE)],
            requested_level='delivered', destination=TARGET,
            options={'end': '2', 'fps': 2, 'helpers': False})
        execute = self.service._execute
        prepared = []

        def cancel_after_delivery(task, check):
            execute(task, check)
            prepared.append((task.accept, task.run is not None, task.artifact is not None))
            self.success(self.send('cancel', target_request_id=request['request_id']))

        with patch.object(self.service, '_execute', side_effect=cancel_after_delivery):
            response = self.service.handle(request)
        self.assertEqual(prepared, [(True, True, True)])
        self.assertEqual(response['status'], 'cancelled')
        self.assertEqual(response['accepted_program_revision'], original.program_revision)
        self.assertIsNone(response['result'])
        self.assertIsNone(response['run_id'])
        self.assertEqual(self.effects(), {'runs': 0, 'artifacts': 0})
        self.assertEqual(self.service.handle(request), response)
        retry = self.success(self.service.handle({**request, 'request_id': 'fresh-delivery'}))
        self.assertEqual(retry['accepted_program_revision'], changed.program_revision)

    def test_export_cooperative_work_failure_leaves_no_artifact(self):
        program, _ = self.create()
        response = self.error(self.send('export', program_revision=program.program_revision,
            destination=TARGET, options=OPTIONS, budgets={'max_operations': 1}), 'OKL-E-RESOURCE')
        self.assertNotEqual(response['achieved_level'], 'delivered')
        self.assertEqual(self.effects(), {'runs': 0, 'artifacts': 0})
        self.assertEqual(self.head(), program.program_revision)


if __name__ == '__main__':
    unittest.main()
