"""Cancellation and immutable-run fencing through the actual force service."""
import unittest
from unittest.mock import patch
import test_force_agent as support


class ForceAgentTransactionTests(unittest.TestCase):
    setUp = support.ForceAgentTests.setUp
    tearDown = support.ForceAgentTests.tearDown
    request = support.ForceAgentTests.request
    send = support.ForceAgentTests.send
    success = support.ForceAgentTests.success
    create = support.ForceAgentTests.create
    head = support.ForceAgentTests.head

    def test_cancel_after_create_computation_prevents_acceptance_and_run(self):
        b = support.source_case('P01')
        req = self.request('create', bundle=b.to_payload(), expected_program_revision=None,
                           requested_level='evaluated')
        original = self.service._execute
        reached = []
        def execute(task, check):
            original(task, check)
            reached.append((task.accept, task.run is not None))
            self.send('cancel', target_request_id=req['request_id'])
        with patch.object(self.service, '_execute', side_effect=execute):
            response = self.service.handle(req)
        self.assertEqual(reached, [(True, True)])
        self.assertEqual(response['status'], 'cancelled')
        self.assertIsNone(response['run_id']); self.assertIsNone(response['result'])
        self.assertIsNone(self.head())
        with self.service._store.connection() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM runs').fetchone()[0], 0)
            self.assertEqual(db.execute('SELECT count(*) FROM artifacts').fetchone()[0], 0)

    def test_cancel_completed_tentative_extension_preserves_original_run(self):
        b, _ = self.create()
        prior = self.success(self.send('evaluate', program_revision=b.program_revision,
                                       run_id=None, until_seconds='1.5'))
        saved = self.service._store.read_run('force', prior['run_id'])
        req = self.request('evaluate', program_revision=b.program_revision,
                           run_id=prior['run_id'], until_seconds='3')
        original = self.service._execute
        reached = []
        def execute(task, check):
            original(task, check)
            reached.append(task.run['valid_until_seconds'])
            self.send('cancel', target_request_id=req['request_id'])
        with patch.object(self.service, '_execute', side_effect=execute):
            response = self.service.handle(req)
        self.assertEqual(reached, ['3'])
        self.assertEqual(response['status'], 'cancelled')
        self.assertEqual(self.service._store.read_run('force', prior['run_id']), saved)
        self.assertEqual(self.head(), b.program_revision)

    def test_cancel_between_execution_and_commit_is_fenced(self):
        b, _ = self.create()
        new = support.source_case('P02')
        # Use an independent project so the legitimate candidate can be prepared.
        req = {**self.request('create', bundle=new.to_payload(), expected_program_revision=None,
                              requested_level='constructed'), 'project_id': 'cancel-at-commit'}
        original = self.service._finish
        def finish(task):
            self.service.handle({**self.request('cancel', target_request_id=req['request_id']),
                                 'project_id': req['project_id']})
            return original(task)
        with patch.object(self.service, '_finish', side_effect=finish):
            response = self.service.handle(req)
        self.assertEqual(response['status'], 'cancelled')
        self.assertIsNone(response['accepted_program_revision'])
        self.assertIsNone(self.service.accepted_revision('cancel-at-commit'))
        self.assertEqual(self.head(), b.program_revision)

    def test_request_from_other_protocol_cannot_change_force_store(self):
        b, _ = self.create()
        before = self.head()
        response = self.service.handle({**self.request('reset', program_revision=b.program_revision),
                                        'schema_version': 'ontokin.agent/0.4'})
        self.assertEqual(response['status'], 'rejected')
        self.assertEqual(self.head(), before)
        with self.service._store.connection() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM runs').fetchone()[0], 0)

    def test_force_cursor_cannot_be_used_after_other_revision_edit(self):
        b, _ = self.create('P10')
        page = self.success(self.send('surface.mesh_page', program_revision=b.program_revision,
                                      element_id=support.FIRST, count=1))
        new = support.source_case('P11')
        self.success(self.send('edit', expected_program_revision=b.program_revision,
                                patches=[support.minimal_patch(b, new, support.RACK)],
                                requested_level='constructed'))
        response = self.send('surface.mesh_page', program_revision=new.program_revision,
                             element_id=support.FIRST, count=1, cursor=page['next_cursor'])
        self.assertIn(response['status'], ('failed', 'rejected'))
        self.assertEqual(self.head(), new.program_revision)
        # The old immutable source still has valid geometry under its own cursor.
        self.success(self.send('surface.mesh_page', program_revision=b.program_revision,
                                element_id=support.FIRST, count=1, cursor=page['next_cursor']))
