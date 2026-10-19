"""Evidence collection preserves failures and rejects unsafe/mutable closure."""
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import ontokin
from tools import build_force_release_evidence as collector


class ForceEvidenceCollectionTests(unittest.TestCase):
    def test_relative_destinations_reject_escape_and_mutable_state(self):
        for name in ('', '.', '..', '../escape', '/absolute', 'a/../b', 'a//b', 'a\\b',
                     'service-store/db', 'data.sqlite3-wal', 'a.db', 'node_modules/a'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                collector.safe_name(name)

    def test_colliding_files_and_nested_outputs_are_rejected_before_creation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); source = root / 'source.json'; source.write_text('{}')
            for destinations in (('a', 'a'), ('a', 'a/b'), ('a/b', 'a')):
                output = root / 'output'
                with self.subTest(destinations=destinations), self.assertRaises(ValueError):
                    collector.copy_inventory([{'source': str(source), 'destination': name} for name in destinations], output)
                self.assertFalse(output.exists())
            with self.assertRaises(ValueError):
                collector.copy_inventory([{'source': str(root), 'destination': 'copies'}], root / 'nested-output')

    def test_directory_copy_discloses_excluded_live_state_and_rejects_symlinks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); source = root / 'input'; source.mkdir()
            (source / 'report.json').write_text('{"status":"failed"}')
            (source / 'database.db-wal').write_bytes(b'live state')
            (source / 'service-store').mkdir(); (source / 'service-store' / 'unusual-name').write_bytes(b'live state')
            copies = [{'source': str(source), 'destination': 'retained'}]
            records, excluded = collector.copy_inventory(copies, root / 'output')
            self.assertEqual([record['path'] for _, record in records], ['retained/report.json'])
            self.assertEqual(set(excluded), {str(source / 'service-store'), str(source / 'database.db-wal')})
            (source / 'alias').symlink_to(source / 'report.json')
            with self.assertRaises(ValueError):
                collector.copy_inventory(copies, root / 'output')

    def test_file_and_byte_budgets_fail_before_output_creation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); source = root / 'input'; source.mkdir()
            for name in ('one', 'two'):
                (source / name).write_bytes(b'1234')
            copies = [{'source': str(source), 'destination': 'retained'}]; output = root / 'output'
            for limit in ({'MAX_FILES': 1}, {'MAX_BYTES': 7}):
                with patch.multiple(collector, **limit), self.assertRaises(ValueError):
                    collector.copy_inventory(copies, output)
                self.assertFalse(output.exists())

    def test_only_measured_file_references_are_resolved(self):
        record = {'path': 'roles/report.json', 'sha256': 'sha256:' + '1' * 64, 'byte_length': 19}
        self.assertEqual(collector.resolve_references({'execution': {'$file': record['path']}}, {record['path']: record}),
                         {'execution': record})
        for value in ({'$file': 'missing'}, {'$file': record['path'], 'status': 'passed'}, {'$command': 'anything'}):
            with self.assertRaises(ValueError):
                collector.resolve_references(value, {record['path']: record})

    def test_complete_collection_preserves_raw_failed_report_and_review_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); report = root / 'report.json'
            raw = b'{ "status": "failed", "commands": ["never execute this"], "pending": ["visual review"] }\n'
            report.write_bytes(raw)
            plan = {'schema_version': collector.PLAN_SCHEMA,
                    'copies': [{'source': str(report), 'destination': 'run/report.json'}],
                    'manifests': [{'destination': 'references.json', 'value': {'report': {'$file': 'run/report.json'}}}],
                    'roles': {'source': {'execution': {'$file': 'references.json'}}}}
            plan_path = root / 'plan.json'; plan_path.write_text(json.dumps(plan)); output = root / 'out'
            identity = {'implementation': {'name': 'test fixture'}, 'input_inventory_sha256': 'sha256:' + '2' * 64,
                        'committed_inputs_match': True}
            # This test exercises collection only. No source/run/review identity
            # in this artificial fixture is accepted by the release auditor.
            release = SimpleNamespace(json_file=lambda p: json.loads(p.read_text()),
                source_identity=lambda: identity, stable_source=lambda a, b: a == b,
                EVIDENCE_SCHEMA='ontokin.force-release-evidence/0.1')
            with patch.object(ontokin, 'force_conformance', release, create=True):
                result = collector.collect(plan_path, output)
            self.assertFalse(result['release_certified'])
            self.assertEqual((output / 'run/report.json').read_bytes(), raw)
            self.assertEqual((output / 'collection-plan.json').read_bytes(), plan_path.read_bytes())
            manifest = json.loads((output / 'evidence.json').read_text())
            for record in manifest['files']:
                self.assertEqual(collector.identity(output / record['path'], record['path']), record)
            self.assertEqual(json.loads((output / 'run/report.json').read_text())['status'], 'failed')
            with patch.object(ontokin, 'force_conformance', release, create=True), self.assertRaises(ValueError):
                collector.collect(plan_path, output)


if __name__ == '__main__':
    unittest.main()
