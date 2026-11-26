"""Helper and package regressions in isolated roots; not live interview tests."""
from __future__ import annotations
import ast
import contextlib
import copy
from datetime import datetime
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / 'scripts/trd.py'
spec = importlib.util.spec_from_file_location('to_trd_under_test', SCRIPT)
trd = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = trd
spec.loader.exec_module(trd)
EXAMPLE = json.loads((SKILL / 'assets/example-input.json').read_text(encoding='utf-8'))
FIXED_TIME = '2026-08-28T00:00:00-06:00'

# Synthetic fixtures cover all legacy states, placeholder progress, historical
# questions, uncertainty, and assumptions. They contain fictional requirements;
# validating or migrating the actual project catalogs is a separate operation.
LEGACY_STATE_MAPPING = {'draft': 'draft', 'not_done': 'trd_done',
                        'done': 'trd_done', 'retired': 'retired'}
V2_STATES = ('draft', 'trd_done', 'retired')
LEGACY_PLACEHOLDERS = ('none', 'n/a', 'na', 'not yet verified', 'not verified',
                       'unverified', 'pending', 'todo', 'tbd', 'not run',
                       'not tested', 'no evidence', 'no evidence yet')
LEGACY_EVIDENCE_BLOCKERS = ('OK', 'v1', 'Test output confirms expected behavior.')


def v2_payload():
    payload = copy.deepcopy(EXAMPLE)
    body = re.sub(r'^- \[[ xX]\] Complete\n|^- Evidence: .*\n', '',
                  payload['body'], flags=re.M)
    payload['body'] = body.split('## Completion evidence')[0].strip() + '\n'
    return payload


def legacy_body():
    """Explicit v1 fixture, independent of the current shipped example schema."""
    body = re.sub(r'(^### REQ-\d+ [—-] .+\n)', r'\1- [ ] Complete\n',
                  v2_payload()['body'], flags=re.M)
    body = re.sub(r'(^- Depends on: .+\n)', r'\1- Evidence: Not yet verified.\n',
                  body, flags=re.M)
    return body.rstrip() + '\n\n## Completion evidence\n\nNot yet verified.\n'


def snapshot(root: Path) -> dict:
    return {str(p.relative_to(root)): ('link', os.readlink(p)) if p.is_symlink()
            else ('dir',) if p.is_dir() else ('file', p.read_bytes())
            for p in sorted(root.rglob('*'))}


class TrdTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = trd.Store(self.root, 'America/Denver')
        self.payload = v2_payload()

    def error(self, code, function, *args, **kwargs):
        with self.assertRaises(trd.TrdError) as caught:
            function(*args, **kwargs)
        self.assertEqual(caught.exception.code, code, str(caught.exception))
        return caught.exception

    def record(self, store=None, selector=None):
        store = store or self.store
        records, _ = store.read()
        return store.resolve(selector, records) if selector else records[0]

    def change(self, status, store=None, selector=None):
        store = store or self.store
        record = self.record(store, selector)
        return store.set_status(record.meta['trd_id'], record.sha256, status,
                                'Explicit fixture instruction for this isolated transition.', True)

    def make(self, state='draft', store=None):
        store = store or self.store
        payload = copy.deepcopy(self.payload)
        receipt = store.create(payload)['document']
        if state != 'draft':
            self.change(state, store, receipt['trd_id'])
        return self.record(store, receipt['trd_id'])

    def legacy(self, state='draft', store=None, body=None, title=None):
        """Write explicit schema-1 bytes without the current create/status path."""
        store = store or self.store
        store.folder.mkdir(exist_ok=True)
        number = len(list(store.folder.glob('trd_*.md'))) + 1
        slug = f'legacy-{number}'
        metadata = {
            'schema_version': 1,
            'trd_id': f'TRD-20260828-{number:08X}',
            'title': title or f'Legacy contacts {number}',
            'slug': slug,
            'created_at': FIXED_TIME,
            'updated_at': FIXED_TIME,
            'status': state,
            'revision': 7,
            'last_action_id': {'draft': 'TO-TRD-003', 'not_done': 'TO-TRD-006',
                               'done': 'TO-TRD-007', 'retired': 'TO-TRD-008'}[state],
            'status_reason': 'Historical fixture state; no product completion asserted.',
        }
        front = '\n'.join(f'{key}: {json.dumps(value, ensure_ascii=False)}'
                          for key, value in metadata.items())
        document = (f'---\n{front}\n---\n\n'
                    f'# Task Requirement Document: {metadata["title"]}\n\n'
                    f'{body if body is not None else legacy_body()}')
        path = store.folder / f'trd_{slug}_2026-08-28.md'
        path.write_bytes(document.encode('utf-8'))
        store.reindex()
        return self.record(store, metadata['trd_id'])

    def migrate(self, rec, store=None):
        return (store or self.store).migrate(
            rec.meta['trd_id'], rec.sha256, 'Explicit isolated migration fixture.', True)

    def cli(self, *args, payload=None, expected=0):
        proc = subprocess.run([sys.executable, str(SCRIPT), '--project-root', str(self.root),
                               '--timezone', 'America/Denver', *args],
                              input=json.dumps(payload) if payload is not None else None,
                              text=True, capture_output=True, timeout=15,
                              env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
        self.assertEqual(proc.returncode, expected, proc.stdout + proc.stderr)
        self.assertFalse(proc.stderr, proc.stderr)
        return json.loads(proc.stdout)

    def test_skill_package_contract(self):
        required = ['SKILL.md', 'README.md', 'INDEX.md', 'AGENTS.md', 'ACTIONS.md',
                    'ATTRIBUTION.md', 'agents/openai.yaml', 'references/wayfinding.md',
                    'references/trd-contract.md', 'references/interaction-examples.md',
                    'tests/interaction-scenarios.md', 'assets/trd-body-template.md',
                    'assets/example-input.json', 'licenses/wayfinder-MIT.txt']
        for name in required:
            with self.subTest(file=name):
                self.assertTrue((SKILL / name).is_file(), name)
        skill = (SKILL / 'SKILL.md').read_text(encoding='utf-8')
        front = skill.split('---', 2)[1]
        self.assertRegex(front, r'(?m)^name: to-trd$')
        description = re.search(r'(?m)^description: (.+)$', front).group(1)
        self.assertLessEqual(len(description), 1024)
        self.assertIn('explicitly', description)
        self.assertLess(len(skill.splitlines()), 500)
        metadata = (SKILL / 'agents/openai.yaml').read_text()
        self.assertRegex(metadata, r'(?m)^policy:\n  allow_implicit_invocation: false$')
        self.assertIn('$to-trd', metadata)
        short_description = re.search(r'  short_description: "(.+)"', metadata).group(1)
        self.assertTrue(25 <= len(short_description) <= 64)
        # Package resources must remain discoverable after a whole-folder copy.
        for document in SKILL.rglob('*.md'):
            for target in re.findall(r'\]\(([^)]+)\)', document.read_text()):
                if '://' not in target and not target.startswith('#'):
                    self.assertTrue((document.parent / target.split('#')[0]).is_file(),
                                    f'{document.relative_to(SKILL)}: {target}')
        for node in ast.walk(ast.parse(SCRIPT.read_text())):
            if isinstance(node, ast.Import):
                names = [alias.name.split('.')[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module.split('.')[0]]
            else:
                continue
            self.assertTrue(set(names) <= sys.stdlib_module_names, names)
        license_raw = (SKILL / 'licenses/wayfinder-MIT.txt').read_bytes()
        blob = hashlib.sha1(f'blob {len(license_raw)}\0'.encode() + license_raw).hexdigest()
        self.assertEqual(blob, 'f1dd2c09108dde1a5f56097cee8461b3ea834499')
        credit = (SKILL / 'ATTRIBUTION.md').read_text()
        self.assertIn('Matt Pocock', credit)
        self.assertIn('https://www.aihero.dev/skills-wayfinder', credit)
        self.assertIn('812805b760baf328db0ebdef6f3807e381f97016', credit)

    def test_template_and_example(self):
        template = (SKILL / 'assets/trd-body-template.md').read_text()
        self.assertEqual(tuple(re.findall(r'^## (.+)$', template, re.M)), trd.SECTIONS)
        self.assertIn('{{', template)
        self.assertIn('## Open questions\n\nNone.', template)
        self.error(2, trd.validate_body, template)
        sections, reqs = trd.validate_body(EXAMPLE['body'])
        self.assertEqual(len(reqs), 2)
        self.assertEqual(sections['Open questions'], 'None.')
        self.assertEqual(reqs[1]['dependencies'], ['REQ-001'])
        self.assertNotIn('{{', EXAMPLE['body'])
        self.assertNotIn('Completion evidence', template)
        self.assertNotRegex(template, r'- \[[ xX]\] Complete|- Evidence:')
        self.assertNotRegex(EXAMPLE['body'], r'- \[[ xX]\] Complete|- Evidence:|## Completion evidence')
        self.assertTrue(all('complete' not in req and 'evidence' not in req for req in reqs))
        self.assertEqual([req['id'] for req in reqs], ['REQ-001', 'REQ-002'])
        self.assertIn('Synthetic clarification', sections['Captured user intent'])
        self.assertIn('active filtered contacts', sections['In scope'])
        self.assertIn('fictional', sections['Context and sources'])
        self.assertIn('U03', ' '.join(reqs[0]['fields']['Source']))
        self.assertIn('active filtered view', reqs[0]['fields']['Requirement'][0])
        self.assertIn('excluded contacts are absent', reqs[0]['fields']['Acceptance'][0])

    def test_explicit_v1_and_v2_fixtures(self):
        sections, requirements = trd.validate_body(self.payload['body'])
        self.assertEqual(len(sections), 10)
        self.assertEqual(len(requirements), 2)
        self.error(2, trd.validate_body, legacy_body())
        legacy_sections, legacy_requirements = trd.validate_body(legacy_body(), schema_version=1)
        self.assertEqual(len(legacy_sections), 11)
        self.assertEqual([req['complete'] for req in legacy_requirements], [False, False])
        self.assertEqual([req['evidence'] for req in legacy_requirements],
                         [['Not yet verified.'], ['Not yet verified.']])
        self.error(2, trd.validate_body, self.payload['body'], schema_version=1)

    def test_clarification_questions_stay_out_of_new_writes(self):
        question = 'Should unfiltered records also be exported?'
        body_with_question = self.payload['body'].replace(
            '## Open questions\n\nNone.', f'## Open questions\n\n{question}')
        self.error(2, self.store.create, dict(self.payload, body=body_with_question))
        self.assertFalse(self.store.folder.exists())

        question_as_fog = self.payload['body'].replace(
            '## Not yet specified\n\nNone.',
            '## Not yet specified\n\nWhich optional fields may be added later?')
        self.error(2, self.store.create, dict(self.payload, body=question_as_fog))
        self.assertFalse(self.store.folder.exists())

        record = self.make()
        record.path.write_text(record.path.read_text().replace(
            '## Open questions\n\nNone.', f'## Open questions\n\n{question}'))
        legacy = self.record()
        self.assertEqual(legacy.sections['Open questions'], question)

        before = snapshot(self.root)
        self.error(2, self.store.update, legacy.meta['trd_id'], legacy.sha256,
                   {'title': 'Legacy title change'})
        self.assertEqual(snapshot(self.root), before)

        # Prepared synthetic answer checks storage propagation, not model questioning.
        resolved_body = legacy.body
        for before_text, after_text in (
            (f'## Open questions\n\n{question}', '## Open questions\n\nNone.'),
            ('## Context and sources',
             'U04 — Synthetic clarification: include all contacts regardless of the active '
             'filter, superseding U03 on selection only.\n\n## Context and sources'),
            ('exports the active filtered contacts', 'exports all existing contacts'),
            ('Export the active filtered contacts and all their existing fields',
             'Export all existing contacts and all their existing fields'),
            ('### REQ-001 — Export the filtered contacts', '### REQ-001 — Export all contacts'),
            ('- Requirement: Export only the contacts in the active filtered view as a local '
             'CSV file, including every existing field.',
             '- Requirement: Export every existing contact and field as a local CSV file.'),
            ('- Source: U03 — synthetic clarification of selection and fields.',
             '- Source: U03 — synthetic clarification of fields and empty-output behavior.\n'
             '- Source: U04 — synthetic clarification superseding the filtered selection.'),
            ('- Acceptance: The exported file contains exactly the contacts in the active '
             'filtered view and all their existing fields; excluded contacts are absent '
             'and source records remain unchanged.',
             '- Acceptance: The exported file contains every existing contact and field, '
             'including unfiltered contacts, without changing source records.'),
            ('An empty filtered view produces', 'An empty contact list produces'),
            ('## Decisions\n\nNone.',
             '## Decisions\n\n- U04 supersedes only the filtered-selection choice in U03; '
             'fields, locality, empty-output and overwrite behavior remain unchanged.'),
        ):
            self.assertEqual(resolved_body.count(before_text), 1, before_text)
            resolved_body = resolved_body.replace(before_text, after_text, 1)
        result = self.store.update(legacy.meta['trd_id'], legacy.sha256,
                                   {'body': resolved_body})
        updated = self.record()
        self.assertTrue(result['scope_changed'])
        self.assertEqual(updated.sections['Open questions'], 'None.')
        self.assertIn('U04 supersedes', updated.sections['Decisions'])
        self.assertIn('U04', updated.sections['Captured user intent'])
        self.assertIn('Export all existing contacts', updated.sections['In scope'])
        self.assertIn(
            'every existing contact and field',
            updated.requirements[0]['fields']['Requirement'][0],
        )
        self.assertIn('U04', ' '.join(updated.requirements[0]['fields']['Source']))
        self.assertIn('including unfiltered contacts',
                      updated.requirements[0]['fields']['Acceptance'][0])
        self.assertNotIn('excluded contacts are absent', updated.body)
        self.assertEqual([req['id'] for req in updated.requirements], ['REQ-001', 'REQ-002'])
        self.assertEqual(updated.requirements[1], legacy.requirements[1])

    def test_creation_naming_collision_and_identity(self):
        self.payload['title'] = 'Café / contacts :: ?'
        with patch.object(trd, 'now', return_value=FIXED_TIME):
            one = self.store.create(self.payload)['document']
            two = self.store.create(self.payload)['document']
            third = self.store.create(dict(self.payload, title='!!!'))['document']
        self.assertEqual(one['path'], 'TRDs/trd_cafe-contacts_2026-08-28.md')
        self.assertEqual(two['path'], 'TRDs/trd_cafe-contacts-2_2026-08-28.md')
        self.assertEqual(third['path'], 'TRDs/trd_trd_2026-08-28.md')
        self.assertNotEqual(one['trd_id'], two['trd_id'])
        self.assertRegex(one['trd_id'], r'^TRD-20260828-[A-F0-9]{8}$')
        updated = self.store.update(one['trd_id'], one['sha256'], {'title':'Another human name'})['document']
        for key in ('trd_id', 'slug', 'created_at', 'path'):
            self.assertEqual(updated[key], one[key])
        self.assertEqual(updated['revision'], 2)
        self.assertEqual(self.record(selector=one['trd_id']).meta['title'], 'Another human name')
        self.assertEqual(trd.now(floor='2099-01-01T00:00:00.123456+00:00'),
                         '2099-01-01T00:00:00.123456+00:00')

    def test_read_only_and_single_authority(self):
        before = snapshot(self.root)
        self.assertEqual(self.store.read()[0], [])
        listing = self.cli('list')
        self.assertEqual(listing['counts'], {'draft': 0, 'trd_done': 0, 'retired': 0})
        self.assertNotIn('legacy_counts', listing)
        result = self.cli('validate')
        self.assertTrue(result['canonical_valid'])
        self.assertFalse(result['index_current'])
        self.assertEqual(snapshot(self.root), before)
        rec = self.make()
        before = snapshot(self.root)
        self.cli('show', rec.meta['trd_id'])
        self.cli('list', '--status', 'draft')
        self.cli('validate')
        self.assertEqual(snapshot(self.root), before)
        self.assertEqual(set(p.name for p in self.store.folder.iterdir()),
                         {rec.path.name, 'INDEX.md'})
        self.assertFalse((self.store.folder / 'responses').exists())
        self.assertFalse((self.root / 'Tasks').exists())

    def test_body_validation_and_dependencies(self):
        original = self.payload['body']
        bad = [
            re.sub(r'^- Source: .+\n', '', original, flags=re.M),
            original.replace('### REQ-002', '### REQ-001'),
            original.replace('- Depends on: REQ-001', '- Depends on: REQ-999'),
            original.replace('- Depends on: None.', '- Depends on: REQ-001', 1),
            original.replace('- Depends on: None.', '- Depends on: REQ-002', 1),
            original.replace('- Depends on: REQ-001', '- Depends on: REQ-001, REQ-001'),
            original.replace('- Requirement:', '- [x] Complete\n- Requirement:', 1),
            original.replace('- Requirement:', '- [ ] Complete\n- Requirement:', 1),
            original.replace('- Requirement:', '- Evidence: Not yet verified.\n- Requirement:', 1),
            original + '\n## Completion evidence\n\nNot yet verified.\n',
            original.replace('- Requirement:', '- Unsupported:', 1),
            original.replace('## Decisions', '## Something else'),
        ]
        for body in bad:
            with self.subTest(body=body[:80]):
                self.error(2, trd.validate_body, body)
        self.assertEqual(len(trd.validate_body(original.replace(' — ', ' - '))[1]), 2)

    def test_metadata_and_payload_validation(self):
        for payload in ({}, {'title':'A'}, dict(self.payload, extra=True),
                        dict(self.payload, title='bad\nname'), dict(self.payload, title='\ud800')):
            with self.subTest(payload=str(payload)[:70]):
                self.error(2, self.store.create, payload)
        self.assertFalse(self.store.folder.exists())
        rec = self.make()
        raw = rec.path.read_bytes()
        variants = [
            raw.replace(b'schema_version: 2', b'schema_version: 99'),
            raw.replace(b'schema_version: 2', b'schema_version: true'),
            raw.replace(b'revision: 1', b'revision: true'),
            raw.replace(b'revision: 1', b'revision: 1\nrevision: 1'),
            raw.replace(b'revision: 1', b'revision: 1\nunknown: "x"'),
            raw.replace(b'last_action_id: "TO-TRD-001"', b'last_action_id: "TO-TRD-004"'),
            raw.replace(b'last_action_id: "TO-TRD-001"', b'last_action_id: "TO-TRD-007"'),
            raw.replace(b'status: "draft"', b'status: "not_done"'),
            raw.replace(b'status: "draft"', b'status: "done"'),
            raw.replace(b'# Task Requirement Document:', b'# Wrong title:'),
        ]
        for variant in variants:
            self.assertNotEqual(variant, raw)
            self.error(2, trd.parse_document, rec.path, variant)
        meta = dict(rec.meta, created_at='2026-08-28T10:00:00')
        self.error(2, trd.parse_document, rec.path, trd.render_document(meta, rec.body).encode())
        meta = dict(rec.meta, updated_at='2000-01-01T00:00:00+00:00')
        self.error(2, trd.parse_document, rec.path, trd.render_document(meta, rec.body).encode())
        payload_path = self.root/'payload.json'
        payload_path.write_text('{"title":"one","title":"two","body":"x"}')
        self.error(2, trd.load_payload, str(payload_path))
        payload_path.write_bytes(b'x' * (trd.MAX_BYTES + 1))
        self.error(2, trd.load_payload, str(payload_path))
        payload_path.write_bytes(b'\xff')
        self.error(2, trd.load_payload, str(payload_path))

    def test_exact_selection_and_ambiguity(self):
        one = self.make()
        records, _ = self.store.read()
        self.assertEqual(self.store.resolve(one.meta['trd_id'], records).path, one.path)
        self.assertEqual(self.store.resolve(one.path.name, records).path, one.path)
        self.assertEqual(self.store.resolve('CONTACTS EXPORT', records).path, one.path)
        self.make()
        records, _ = self.store.read()
        exc = self.error(4, self.store.resolve, 'Contacts export', records)
        self.assertEqual(len(exc.details['candidates']), 2)
        self.error(3, self.store.resolve, one.meta['trd_id'][:15], records)
        self.error(3, self.store.resolve, 'Export', records)
        for selector in ('../x', '/tmp/x', '.hidden', 'bad\nname', 'x\\y'):
            self.error(2, self.store.resolve, selector, records)

    def test_index_order_escaping_and_rebuild(self):
        with patch.object(trd, 'now', return_value=FIXED_TIME):
            one = self.store.create(dict(self.payload, title='Report | [external](https://example.invalid)'))['document']
            two = self.store.create(dict(self.payload, title='Second'))['document']
        for identifier, updated in ((one['trd_id'],'2026-08-28T15:30:00-06:00'),
                                    (two['trd_id'],'2026-08-28T20:00:00+00:00')):
            rec = self.record(selector=identifier)
            rec.path.write_text(trd.render_document(dict(rec.meta, updated_at=updated), rec.body))
        records, warnings = self.store.read()
        self.assertTrue(warnings)
        self.assertEqual(trd.sorted_records(records)[0].meta['trd_id'], one['trd_id'])
        before_docs = {r.path.name:r.path.read_bytes() for r in records}
        self.store.reindex()
        text = (self.store.folder/'INDEX.md').read_text()
        self.assertIn(r'Report \| \[external\]\(https://example.invalid\)', text)
        self.assertLess(text.index(one['trd_id']), text.index(two['trd_id']))
        self.assertEqual(before_docs, {r.path.name:r.path.read_bytes() for r in self.store.read()[0]})
        self.assertFalse(self.store.reindex()['mutated'])
        (self.store.folder/'INDEX.md').unlink()
        self.assertEqual(len(self.store.read()[0]), 2)
        self.assertTrue(self.store.read()[1])
        self.store.reindex()
        self.assertFalse(self.store.read()[1])
        self.change('retired', selector=one['trd_id'])
        self.assertEqual(trd.sorted_records(self.store.read()[0])[-1].meta['trd_id'], one['trd_id'])

    def test_corrupt_catalog_fails_closed(self):
        rec = self.make()
        rec.path.write_text(rec.path.read_text().replace('status: "draft"','status: "unknown"'))
        before = snapshot(self.root)
        self.error(5, self.store.read)
        self.error(5, self.store.reindex)
        self.error(5, self.store.create, self.payload)
        self.assertEqual(snapshot(self.root), before)

    def test_all_lifecycle_pairs(self):
        allowed = {('draft', 'trd_done'), ('draft', 'retired'),
                   ('trd_done', 'draft'), ('trd_done', 'retired'), ('retired', 'draft')}
        for before in V2_STATES:
            for after in V2_STATES:
                with self.subTest(before=before, after=after):
                    root = self.root/f'{before}-{after}'
                    root.mkdir()
                    store = trd.Store(root, 'America/Denver')
                    rec = self.make(before, store)
                    snap = snapshot(root)
                    if after == before or (before, after) in allowed:
                        result = store.set_status(rec.meta['trd_id'], rec.sha256, after,
                                                  'Explicit fixture transition.', True)
                        current = self.record(store)
                        self.assertEqual(current.meta['status'], after)
                        self.assertEqual(current.meta['created_at'], rec.meta['created_at'])
                        if after == before:
                            self.assertFalse(result['mutated'])
                            self.assertEqual(snapshot(root), snap)
                        else:
                            self.assertEqual(current.meta['revision'], rec.meta['revision']+1)
                            self.assertEqual(current.body, rec.body)
                            self.assertEqual(current.path, rec.path)
                            self.assertTrue(result['index_updated'])
                    else:
                        self.error(8, store.set_status, rec.meta['trd_id'], rec.sha256, after,
                                   'Explicit fixture transition.', True)
                        self.assertEqual(snapshot(root), snap)
        rec = self.make('retired')
        before = snapshot(self.root)
        self.error(8, self.store.update, rec.meta['trd_id'], rec.sha256, {'title':'Edited'})
        self.assertEqual(snapshot(self.root), before)

    def test_document_readiness_and_confirmation_gates(self):
        rec = self.make()
        before = snapshot(self.root)
        self.error(8, self.store.set_status, rec.meta['trd_id'], rec.sha256, 'trd_done', 'Approval.', False)
        self.assertEqual(snapshot(self.root), before)
        done = self.change('trd_done')['document']
        self.assertEqual(done['status'], 'trd_done')
        self.assertNotIn('complete_count', done)
        self.assertNotIn('completed_count', done)
        self.assertEqual(self.record().body, self.payload['body'])
        for label, body in (
            ('fog',self.payload['body'].replace('## Not yet specified\n\nNone.', '## Not yet specified\n\nFuture input shape is not known.')),
            ('assumption',self.payload['body'].replace('## Assumptions\n\nNone.', '## Assumptions\n\n- Unconfirmed: Export includes every field.')),
            ('empty', re.sub(r'## Task requirements\n.*?\n## Decisions',
                            '## Task requirements\n\nNo task requirements captured yet.\n\n## Decisions',
                            self.payload['body'], flags=re.S)),
        ):
            with self.subTest(case=label):
                root = self.root/label
                root.mkdir()
                store = trd.Store(root)
                doc = store.create(dict(self.payload, body=body))['document']
                before = snapshot(root)
                self.error(8, store.set_status, doc['trd_id'], doc['sha256'], 'trd_done', 'Approve.', True)
                self.assertEqual(snapshot(root), before)
        rec = self.legacy(body=legacy_body().replace(
            '## Open questions\n\nNone.', '## Open questions\n\nWhich export format?'))
        self.migrate(rec)
        rec = self.record(selector=rec.meta['trd_id'])
        before = snapshot(self.root)
        self.error(8, self.store.set_status, rec.meta['trd_id'], rec.sha256,
                   'trd_done', 'Approve.', True)
        self.assertEqual(snapshot(self.root), before)

    def test_completion_reports_all_content_blockers_without_writes(self):
        body = re.sub(r'## Task requirements\n.*?\n## Decisions',
                      '## Task requirements\n\nNo task requirements captured yet.\n\n## Decisions',
                      self.payload['body'], flags=re.S)
        body = body.replace('## Not yet specified\n\nNone.',
                            '## Not yet specified\n\nThe required export fields are undecided.')
        body = body.replace('## Assumptions\n\nNone.',
                            '## Assumptions\n\n- Unconfirmed: Export includes personal notes.')
        doc = self.cli('create', '--input', '-', payload=dict(self.payload, body=body))['document']
        diagnostic = doc['completion']
        self.assertFalse(diagnostic['content_ready'])
        self.assertEqual(diagnostic['next_action'], 'resolve_requirements')
        self.assertEqual([b['code'] for b in diagnostic['blockers']],
                         ['missing_requirements', 'unspecified_requirements', 'unconfirmed_assumptions'])
        before = snapshot(self.root)
        shown = self.cli('show', doc['trd_id'])['document']
        self.assertEqual(shown['completion'], diagnostic)
        for command in ('list', 'validate'):
            self.assertEqual(self.cli(command)['documents'][0]['completion'], diagnostic)
        rejected = self.cli('set-status', doc['trd_id'], '--expect-sha256', doc['sha256'],
                            '--status', 'trd_done', '--reason', 'Fixture approval.',
                            '--confirmed', expected=8)
        self.assertEqual(rejected['completion_blockers'], diagnostic['blockers'])
        self.assertEqual(snapshot(self.root), before)

    def test_planning_choices_allow_document_approval(self):
        body = self.payload['body'].replace(
            '## Decisions\n\nNone.',
            '## Decisions\n\nImplementation planning selects the export library, dependency '
            'versions, and module layout within the required local CSV and source-preservation constraints.')
        doc = self.cli('create', '--input', '-', payload=dict(self.payload, body=body))['document']
        self.assertEqual(doc['completion'],
                         dict(content_ready=True, blockers=[], next_action='request_approval'))
        before = snapshot(self.root)
        self.cli('set-status', doc['trd_id'], '--expect-sha256', doc['sha256'],
                 '--status', 'trd_done', '--reason', 'Fixture approval.', expected=8)
        self.assertEqual(snapshot(self.root), before)
        done = self.cli('set-status', doc['trd_id'], '--expect-sha256', doc['sha256'],
                        '--status', 'trd_done', '--reason', 'User approved the displayed fixture.',
                        '--confirmed')['document']
        current = self.record(selector=doc['trd_id'])
        self.assertEqual(current.meta['status'], 'trd_done')
        self.assertEqual(current.body, body)
        self.assertEqual(done['completion'], dict(content_ready=True, blockers=[], next_action='none'))
        self.assertTrue(self.cli('validate')['index_current'])
        self.assertEqual({p.name for p in self.root.iterdir()}, {'TRDs'})
        revised = self.cli('update', doc['trd_id'], '--expect-sha256', done['sha256'],
                           '--input', '-', payload={'title': 'Revised export requirements'})['document']
        self.assertEqual(revised['status'], 'draft')
        self.assertEqual(revised['completion']['next_action'], 'request_approval')
        before = snapshot(self.root)
        self.cli('set-status', doc['trd_id'], '--expect-sha256', done['sha256'],
                 '--status', 'trd_done', '--reason', 'Obsolete fixture approval.', '--confirmed', expected=6)
        self.assertEqual(snapshot(self.root), before)

    def test_completion_preserves_authority_gaps(self):
        body = self.payload['body'].replace(
            '## Decisions\n\nNone.', '## Decisions\n\nImplementation planning defines the approval interface.')
        body = body.replace('## Not yet specified\n\nNone.',
                            '## Not yet specified\n\nThe authority permitted to approve disclosure is undecided.')
        doc = self.store.create(dict(self.payload, body=body))['document']
        self.assertEqual(doc['completion']['blockers'][0]['code'], 'unspecified_requirements')
        before = snapshot(self.root)
        self.error(8, self.store.set_status, doc['trd_id'], doc['sha256'],
                   'trd_done', 'Fixture approval.', True)
        self.assertEqual(snapshot(self.root), before)

    def test_completion_diagnostics_for_retired_and_legacy_documents(self):
        rec = self.make('retired')
        before = snapshot(self.root)
        summary = self.cli('show', rec.meta['trd_id'])['document']
        self.assertEqual(summary['completion'],
                         dict(content_ready=True, blockers=[], next_action='restore_to_draft'))
        self.assertEqual(snapshot(self.root), before)
        historical = self.legacy('draft', body=legacy_body().replace(
            '## Open questions\n\nNone.', '## Open questions\n\nWhich fields are required?'))
        before = snapshot(self.root)
        diagnostic = self.cli('show', historical.meta['trd_id'])['document']['completion']
        self.assertIsNone(diagnostic['content_ready'])
        self.assertEqual(diagnostic['next_action'], 'migrate')
        self.assertEqual(diagnostic['blockers'][0]['code'], 'legacy_schema')
        self.assertEqual(snapshot(self.root), before)
        self.migrate(historical)
        migrated = self.record(selector=historical.meta['trd_id'])
        diagnostic = migrated.summary()['completion']
        self.assertFalse(diagnostic['content_ready'])
        self.assertEqual(diagnostic['next_action'], 'resolve_requirements')
        self.assertEqual(diagnostic['blockers'][0]['code'], 'open_questions')

    def test_material_updates_reopen_document_review(self):
        changes = [
            {'title': 'New display title'},
            {'title': ' Contacts export'},
            {'title': 'Contacts export '},
        ]
        for before, after in (
            ('Provide a project-local command', 'Provide a local command'),
            ('without editing contacts.', 'without modifying contacts.'),
            ('The only source for its requirements', 'The stated source for its requirements'),
            ('Export the active filtered contacts', 'Export the currently filtered contacts'),
            ('Editing contacts, cloud synchronization', 'Editing contacts, cloud storage'),
            ('Export the filtered contacts\n-', 'Export the selected contacts\n-'),
            ('- Requirement: Export only the contacts', '- Requirement: Export the selected contacts'),
            ('- Source: U01 — example user intent.', '- Source: U01 — clarified user intent.'),
            ('- Acceptance: The exported file', '- Acceptance: The revised exported file'),
            ('- Depends on: REQ-001', '- Depends on: None.'),
            ('## Decisions\n\nNone.', '## Decisions\n\n- Include existing fields.'),
            ('## Not yet specified\n\nNone.', '## Not yet specified\n\nEncoding needs review.'),
            ('## Assumptions\n\nNone.', '## Assumptions\n\n- Accepted: Input remains local.'),
            ('## Decisions\n\nNone.', '## Decisions\n\n\nNone.'),
        ):
            body = self.payload['body'].replace(before, after, 1)
            self.assertNotEqual(body, self.payload['body'], before)
            changes.append({'body': body})
        for change in changes:
            with self.subTest(change=str(change)[:90]):
                rec = self.make('trd_done')
                result = self.store.update(rec.meta['trd_id'], rec.sha256, change)
                current = self.record(selector=rec.meta['trd_id'])
                self.assertTrue(result['scope_changed'])
                self.assertTrue(result['index_updated'])
                self.assertEqual(current.meta['status'], 'draft')
                self.assertEqual(current.meta['revision'], rec.meta['revision'] + 1)
                self.assertIn('review', current.meta['status_reason'])
                self.assertEqual(current.meta['last_action_id'], 'TO-TRD-003')
                self.assertEqual(current.meta['title'], change.get('title', rec.meta['title']))
                self.assertEqual(current.body, change.get('body', rec.body))
                self.assertEqual(current.path, rec.path)
                for field in ('created_at', 'trd_id', 'slug'):
                    self.assertEqual(current.meta[field], rec.meta[field])

    def test_representation_only_no_ops_preserve_every_byte(self):
        for state in ('draft', 'trd_done'):
            rec = self.make(state)
            for body in (rec.body, '\n\n' + rec.body + '\n\n',
                         rec.body.replace('\n', '\r\n'),
                         '\r\n' + rec.body.replace('\n', '\r\n') + '\r\n'):
                with self.subTest(state=state, representation=repr(body[:30])):
                    before = snapshot(self.root)
                    result = self.store.update(rec.meta['trd_id'], rec.sha256, {'body': body})
                    self.assertFalse(result['mutated'])
                    self.assertEqual(result['status'], 'no_op')
                    self.assertEqual(result['document']['sha256'], rec.sha256)
                    self.assertEqual(snapshot(self.root), before)

    def test_same_state_requests_still_require_all_preconditions(self):
        for state in V2_STATES:
            rec = self.make(state)
            for selector, digest, reason, confirmed, code in (
                (rec.meta['trd_id'], rec.sha256, 'Approved.', False, 8),
                (rec.meta['trd_id'], rec.sha256, ' ', True, 2),
                (rec.meta['trd_id'], '0' * 64, 'Approved.', True, 6),
                (rec.meta['trd_id'], rec.sha256.upper(), 'Approved.', True, 2),
                ('absent', rec.sha256, 'Approved.', True, 3),
            ):
                before = snapshot(self.root)
                self.error(code, self.store.set_status, selector, digest, state, reason, confirmed)
                self.assertEqual(snapshot(self.root), before)

    def test_stale_hash_and_no_op(self):
        rec = self.make()
        rec.path.write_text(rec.path.read_text().replace('without editing contacts.', 'without changing contacts.'))
        before = snapshot(self.root)
        self.error(6, self.store.update, rec.meta['trd_id'], rec.sha256, {'title':'Should not publish'})
        self.assertEqual(snapshot(self.root), before)
        current = self.record()
        result = self.store.update(current.meta['trd_id'], current.sha256, {'body':current.body})
        self.assertFalse(result['mutated'])
        self.assertEqual(snapshot(self.root), before)
        result = self.store.set_status(current.meta['trd_id'], current.sha256, 'draft',
                                        'Different reason must not mutate a no-op.', True)
        self.assertFalse(result['mutated'])
        self.assertEqual(snapshot(self.root), before)

    def test_path_and_symlink_safety(self):
        self.error(3, trd.Store, self.root/'does-not-exist')
        outside = self.root/'outside'
        outside.mkdir()
        self.store.folder.symlink_to(outside, target_is_directory=True)
        before = snapshot(self.root)
        self.error(5, trd.Store, self.root)
        self.assertEqual(snapshot(self.root), before)
        self.store.folder.unlink()
        rec = self.make()
        external = outside/'external.md'
        external.write_bytes(rec.path.read_bytes())
        original = external.read_bytes()
        rec.path.unlink()
        rec.path.symlink_to(external)
        self.error(5, self.store.read)
        self.error(5, self.store.reindex)
        self.assertEqual(external.read_bytes(), original)
        rec.path.unlink()
        rec.path.write_bytes(original)
        index = self.store.folder/'INDEX.md'
        index.unlink()
        index.symlink_to(external)
        before = snapshot(self.root)
        self.error(5, self.store.create, self.payload)
        self.assertEqual(snapshot(self.root), before)
        payload_link = self.root/'input-link.json'
        payload_link.symlink_to(SKILL/'assets/example-input.json')
        self.error(2, trd.load_payload, str(payload_link))

    def test_lock_and_atomic_failure(self):
        rec = self.make()
        self.store.lock_path.mkdir()
        (self.store.lock_path/'owner.json').write_text('{"process_id":123}')
        before = snapshot(self.root)
        self.error(7, self.store.read)
        self.error(7, self.store.create, self.payload)
        self.assertEqual(snapshot(self.root), before)
        (self.store.lock_path/'owner.json').unlink()
        self.store.lock_path.rmdir()
        before = snapshot(self.root)
        with patch.object(trd.os, 'replace', side_effect=OSError('Injected canonical replacement failure')):
            with self.assertRaises(OSError):
                self.store.update(rec.meta['trd_id'], rec.sha256, {'title':'Not committed'})
        self.assertEqual(snapshot(self.root), before)
        self.assertFalse(list(self.store.folder.glob('.to-trd-tmp-*')))
        self.assertFalse(self.store.lock_path.exists())

    def test_partial_index_failure_receipt(self):
        real_write = self.store.atomic_write
        def failing_index(path, text, **kwargs):
            if path.name == 'INDEX.md':
                raise OSError('Injected index failure')
            return real_write(path, text, **kwargs)
        with patch.object(self.store, 'atomic_write', side_effect=failing_index):
            exc = self.error(9, self.store.create, self.payload)
        self.assertTrue(exc.details['mutated'])
        self.assertFalse(exc.details['index_updated'])
        self.assertIn('trd_id', exc.details['document'])
        records, warnings = self.store.read()
        self.assertEqual(len(records), 1)
        self.assertTrue(warnings)
        rec_bytes = records[0].path.read_bytes()
        self.store.reindex()
        self.assertEqual(self.store.read()[1], [])
        self.assertEqual(self.store.read()[0][0].path.read_bytes(), rec_bytes)
        self.assertEqual(len(self.store.read()[0]), 1)

    def test_known_secret_guard(self):
        synthetic_secrets = ['-----BEGIN PRIVATE KEY-----', 'sk-proj-'+'x'*32,
                             'ghp_'+'x'*36, 'api_key: synthetic_secret_value_123']
        for value in synthetic_secrets:
            with self.subTest(value=value[:12]):
                self.error(2, trd.secret_guard, value)
        trd.secret_guard('Document the API_KEY variable name, not a value. Password policy is part of the scope.')
        self.error(2, self.store.create, dict(self.payload, body=self.payload['body']+'\napi_key: synthetic_secret_value_123\n'))
        self.assertFalse(self.store.folder.exists())

    def test_action_ids_and_metadata(self):
        self.assertEqual(set(trd.ACTIONS.values()), {f'TO-TRD-{i:03d}' for i in range(1,14)})
        action_doc = (SKILL/'ACTIONS.md').read_text()
        self.assertEqual(set(re.findall(r'TO-TRD-\d{3}', action_doc)), set(trd.ACTIONS.values()))
        rec = self.make()
        self.assertEqual(rec.meta['last_action_id'], 'TO-TRD-001')
        self.assertEqual(self.change('trd_done')['document']['last_action_id'], 'TO-TRD-006')
        self.assertEqual(self.change('draft')['document']['last_action_id'], 'TO-TRD-012')
        self.change('trd_done')
        self.assertEqual(self.change('retired')['document']['last_action_id'], 'TO-TRD-008')
        self.assertEqual(self.change('draft')['document']['last_action_id'], 'TO-TRD-009')
        current = self.record()
        self.store.reindex()
        self.assertEqual(self.record().sha256, current.sha256)
        legacy = self.legacy('done')
        self.assertEqual(legacy.meta['last_action_id'], 'TO-TRD-007')
        self.assertEqual(self.migrate(legacy)['document']['last_action_id'], 'TO-TRD-013')

    def test_cli_json_contract(self):
        self.assertFalse(self.cli('list')['mutated'])
        created = self.cli('create', '--input', '-', payload=self.payload)['document']
        identifier = created['trd_id']
        shown = self.cli('show', identifier)
        self.assertEqual(shown['body'], self.payload['body'])
        ready = self.cli('set-status', identifier, '--expect-sha256', shown['document']['sha256'],
                         '--status','trd_done','--reason','Explicit fixture approval.','--confirmed')['document']
        self.assertEqual(ready['status'], 'trd_done')
        edited = self.cli('update', identifier, '--expect-sha256', ready['sha256'], '--input','-',
                         payload={'title': 'Revised contacts export'})['document']
        self.assertEqual(edited['status'], 'draft')
        done = self.cli('set-status', identifier, '--expect-sha256', edited['sha256'],
                        '--status', 'trd_done', '--reason', 'Approve revised document.',
                        '--confirmed')['document']
        retired = self.cli('set-status', identifier,'--expect-sha256',done['sha256'],
                           '--status','retired','--reason','Explicit fixture retirement.','--confirmed')['document']
        self.cli('set-status',identifier,'--expect-sha256',retired['sha256'],
                 '--status','draft','--reason','Explicit fixture restoration.','--confirmed')
        checked = self.cli('validate')
        self.assertTrue(checked['canonical_valid'])
        self.assertTrue(checked['index_current'])
        self.assertFalse(self.cli('reindex')['mutated'])
        self.cli('show','missing',expected=3)
        self.cli('create',expected=2)
        self.cli('create','--input','-',payload={'bad':'input'},expected=2)

    def test_cli_rejects_legacy_status_tokens_without_aliases(self):
        rec = self.make()
        for legacy_status in ('not_done', 'done'):
            before = snapshot(self.root)
            result = self.cli('list', '--status', legacy_status, expected=2)
            self.assertFalse(result['mutated'])
            result = self.cli('set-status', rec.meta['trd_id'], '--expect-sha256', rec.sha256,
                              '--status', legacy_status, '--reason', 'Fixture.', '--confirmed', expected=2)
            self.assertFalse(result['mutated'])
            self.assertEqual(snapshot(self.root), before)

    def test_legacy_mutations_require_migration_even_for_no_ops(self):
        for state in LEGACY_STATE_MAPPING:
            rec = self.legacy(state)
            for payload in ({'title': rec.meta['title']}, {'body': rec.body}):
                before = snapshot(self.root)
                exc = self.error(8, self.store.update, rec.meta['trd_id'], rec.sha256, payload)
                self.assertEqual(exc.category, 'migration_required')
                self.assertEqual(snapshot(self.root), before)
            before = snapshot(self.root)
            # Legacy tokens themselves are invalid; overlapping current tokens
            # must still be denied because the record remains schema 1.
            target = state if state in V2_STATES else 'trd_done'
            exc = self.error(8, self.store.set_status, rec.meta['trd_id'], rec.sha256,
                             target, 'Explicit fixture.', True)
            self.assertEqual(exc.category, 'migration_required')
            self.assertEqual(snapshot(self.root), before)

    def test_all_legacy_mappings_preserve_document_meaning(self):
        for legacy_state, target_state in LEGACY_STATE_MAPPING.items():
            with self.subTest(legacy_state=legacy_state):
                root = self.root / legacy_state
                root.mkdir()
                store = trd.Store(root)
                rec = self.legacy(legacy_state, store)
                before = snapshot(root)
                preflight = store.preflight(rec.meta['trd_id'], rec.sha256)
                self.assertTrue(preflight['preflight']['eligible'])
                self.assertFalse(preflight['mutated'])
                self.assertEqual(preflight['preflight']['target_status'], target_state)
                self.assertEqual(snapshot(root), before)
                with patch.object(trd, 'now', return_value='2099-01-01T00:00:00+00:00'):
                    result = self.migrate(rec, store)
                current = self.record(store)
                self.assertTrue(result['mutated'])
                self.assertTrue(result['index_updated'])
                self.assertEqual(result['migration_from'], rec.summary())
                self.assertEqual(result['document']['sha256'], hashlib.sha256(current.path.read_bytes()).hexdigest())
                self.assertNotEqual(current.sha256, rec.sha256)
                self.assertEqual(current.meta['schema_version'], 2)
                self.assertEqual(current.meta['status'], target_state)
                self.assertEqual(current.meta['revision'], rec.meta['revision'] + 1)
                self.assertEqual(current.meta['last_action_id'], 'TO-TRD-013')
                self.assertEqual(current.meta['status_reason'], 'Explicit isolated migration fixture.')
                self.assertGreaterEqual(datetime.fromisoformat(current.meta['updated_at']),
                                        datetime.fromisoformat(rec.meta['updated_at']))
                self.assertEqual(current.path, rec.path)
                for field in ('trd_id', 'slug', 'title', 'created_at'):
                    self.assertEqual(current.meta[field], rec.meta[field])
                self.assertEqual(current.body, self.payload['body'])
                self.assertEqual([req['id'] for req in current.requirements], ['REQ-001', 'REQ-002'])
                self.assertEqual(current.requirements[1]['dependencies'], ['REQ-001'])
                self.assertNotRegex(current.body, r'- \[[ xX]\] Complete|- Evidence:|## Completion evidence')
                self.assertFalse(current.summary()['migration_required'])
                self.assertEqual(current.summary()['compatibility'], 'current')
                self.assertEqual(store.read()[1], [])
                index = (store.folder / 'INDEX.md').read_text()
                self.assertIn(f'| {target_state} | current |', index)
                self.assertNotIn('Legacy schema 1 (', index)
                self.assertEqual(set(p.name for p in store.folder.iterdir()), {rec.path.name, 'INDEX.md'})

    def test_migration_accepts_every_documented_empty_marker(self):
        for marker in LEGACY_PLACEHOLDERS:
            for suffix in ('', '.', '!'):
                with self.subTest(marker=marker, suffix=suffix):
                    value = '  ' + marker.swapcase() + suffix + '  '
                    body = legacy_body().replace('Not yet verified.', value)
                    rec = self.legacy(body=body)
                    before = snapshot(self.root)
                    check = self.store.preflight(rec.meta['trd_id'])
                    self.assertEqual(check['preflight']['blockers'], [])
                    self.assertEqual(snapshot(self.root), before)
                    self.migrate(rec)
                    self.assertEqual(self.record(selector=rec.meta['trd_id']).body, self.payload['body'])

    def test_migration_blocks_checked_or_nonplaceholder_evidence(self):
        cases = [
            ('checked lower', legacy_body().replace('- [ ] Complete', '- [x] Complete', 1), 'REQ-001.Complete'),
            ('checked upper', legacy_body().replace('- [ ] Complete', '- [X] Complete', 1), 'REQ-001.Complete'),
        ]
        for evidence in (*LEGACY_EVIDENCE_BLOCKERS, 'None..', 'Pending!!', 'Not yet verified.\nOK'):
            if '\n' not in evidence:
                cases.append(('requirement ' + evidence,
                              legacy_body().replace('- Evidence: Not yet verified.', '- Evidence: ' + evidence, 1),
                              'REQ-001.Evidence[1]'))
            cases.append(('document ' + evidence, legacy_body().replace(
                '## Completion evidence\n\nNot yet verified.', '## Completion evidence\n\n' + evidence),
                'Completion evidence'))
        cases.append(('second evidence value', legacy_body().replace(
            '- Evidence: Not yet verified.', '- Evidence: Not yet verified.\n- Evidence: OK', 1),
            'REQ-001.Evidence[2]'))
        cases.append(('second requirement', legacy_body().replace(
            '- Depends on: REQ-001\n- Evidence: Not yet verified.',
            '- Depends on: REQ-001\n- Evidence: OK'), 'REQ-002.Evidence[1]'))
        for label, body, field in cases:
            with self.subTest(case=label):
                root = self.root / f'blocked-{len(list(self.root.iterdir()))}'
                root.mkdir()
                store = trd.Store(root)
                rec = self.legacy('done', store, body=body)
                before = snapshot(root)
                preflight = store.preflight(rec.meta['trd_id'], rec.sha256)
                self.assertFalse(preflight['preflight']['eligible'])
                self.assertIn({'trd_id': rec.meta['trd_id'], 'field': field},
                              [{key: blocker[key] for key in ('trd_id', 'field')}
                               for blocker in preflight['preflight']['blockers']])
                self.assertEqual(snapshot(root), before)
                exc = self.error(8, self.migrate, rec, store)
                self.assertEqual(exc.category, 'migration_blocked')
                self.assertEqual(exc.details['document']['trd_id'], rec.meta['trd_id'])
                self.assertEqual(exc.details['blockers'], preflight['preflight']['blockers'])
                self.assertEqual(snapshot(root), before)

    def test_migration_preserves_historical_questions_and_narrative(self):
        body = legacy_body().replace('## Open questions\n\nNone.',
                                   '## Open questions\n\nWhich fields may be exported?')
        body = body.replace('## Not yet specified\n\nNone.',
                            '## Not yet specified\n\nWhat character encoding is needed?')
        body = body.replace('## Assumptions\n\nNone.',
                            '## Assumptions\n\n- Unconfirmed: The old encoding remains suitable.')
        body = body.replace('## Decisions\n\nNone.',
                            '## Decisions\n\n- Evidence: This is narrative outside the legacy progress fields.\n'
                            '- [ ] Complete\nPreserve these exact historical words.')
        for state in ('draft', 'retired'):
            rec = self.legacy(state, body=body)
            original_sections = rec.sections
            self.migrate(rec)
            migrated = self.record(selector=rec.meta['trd_id'])
            self.assertEqual(migrated.meta['status'], state)
            for heading, content in original_sections.items():
                if heading not in ('Task requirements', 'Completion evidence'):
                    self.assertEqual(migrated.sections[heading], content)
            self.assertIn('- Evidence: This is narrative', migrated.body)
            self.assertIn('- [ ] Complete\nPreserve', migrated.body)
            before = snapshot(self.root)
            self.error(2 if state == 'draft' else 8, self.store.update,
                       migrated.meta['trd_id'], migrated.sha256, {'title': 'Still unresolved'})
            self.assertEqual(snapshot(self.root), before)
        for state in ('not_done', 'done'):
            rec = self.legacy(state, body=body)
            before = snapshot(self.root)
            check = self.store.preflight(rec.meta['trd_id'])
            self.assertEqual([blocker['field'] for blocker in check['preflight']['blockers']], ['status'])
            self.error(8, self.migrate, rec)
            self.assertEqual(snapshot(self.root), before)

    def test_mixed_catalog_reads_counts_order_and_filters_are_read_only(self):
        current = {state: self.make(state) for state in V2_STATES}
        legacy = {state: self.legacy(state) for state in LEGACY_STATE_MAPPING}
        expected_ids = ([current[state].meta['trd_id'] for state in V2_STATES]
                        + [legacy[state].meta['trd_id'] for state in LEGACY_STATE_MAPPING])
        index = self.store.folder / 'INDEX.md'
        for index_state in ('current', 'stale', 'missing'):
            if index_state == 'stale':
                index.write_text('Old projection bytes retained by every read.\n')
            elif index_state == 'missing':
                index.unlink()
            before = snapshot(self.root)
            listed = self.cli('list')
            self.assertEqual([doc['trd_id'] for doc in listed['documents']], expected_ids)
            self.assertEqual(listed['counts'], {'draft': 1, 'trd_done': 1, 'retired': 1})
            self.assertEqual(listed['legacy_counts'], {'draft': 1, 'not_done': 1, 'done': 1, 'retired': 1})
            self.assertEqual(listed['document_count'], 7)
            self.assertEqual(listed['schema_version'], 2)
            for document in listed['documents']:
                self.assertNotIn('complete_count', document)
                self.assertNotIn('completed_count', document)
                self.assertNotIn('completed_requirement_count', document)
                is_legacy = document['schema_version'] == 1
                self.assertEqual(document['migration_required'], is_legacy)
                self.assertEqual(document['compatibility'],
                                 'legacy_v1_requires_migration' if is_legacy else 'current')
                shown = self.cli('show', document['trd_id'])
                self.assertEqual(shown['document'], document)
            for state in V2_STATES:
                filtered = self.cli('list', '--status', state)
                self.assertEqual([doc['trd_id'] for doc in filtered['documents']],
                                 [current[state].meta['trd_id']])
            validated = self.cli('validate')
            self.assertTrue(validated['canonical_valid'])
            self.assertEqual(validated['index_current'], index_state == 'current')
            self.assertEqual(snapshot(self.root), before)
        docs = {rec.path.name: rec.path.read_bytes() for rec in self.store.read()[0]}
        self.store.reindex()
        text = index.read_text()
        self.assertIn('draft: 1 | trd_done: 1 | retired: 1', text)
        self.assertIn('Legacy schema 1 (explicit migration required): draft: 1 | not_done: 1 | done: 1 | retired: 1', text)
        rows = re.findall(r'^\| (TRD-[^ ]+) \|', text, re.M)
        self.assertEqual(rows, expected_ids)
        self.assertEqual({rec.path.name: rec.path.read_bytes() for rec in self.store.read()[0]}, docs)
        before = snapshot(self.root)
        with patch.object(trd, 'now', return_value='2099-01-01T00:00:00+00:00'):
            self.assertFalse(self.store.reindex()['mutated'])
        self.assertEqual(snapshot(self.root), before)

    def test_legacy_index_uses_update_instants_and_id_tie_break(self):
        earlier = self.legacy()
        later = self.legacy()
        for rec, updated in ((earlier, '2026-08-28T20:00:00+00:00'),
                             (later, '2026-08-28T15:30:00-06:00')):
            raw = rec.path.read_text().replace(f'updated_at: "{FIXED_TIME}"',
                                              f'updated_at: "{updated}"')
            rec.path.write_text(raw)
        self.store.reindex()
        listing = self.cli('list')
        self.assertEqual([doc['trd_id'] for doc in listing['documents']],
                         [later.meta['trd_id'], earlier.meta['trd_id']])
        raw = earlier.path.read_text().replace('2026-08-28T20:00:00+00:00', '2026-08-28T15:30:00-06:00')
        earlier.path.write_text(raw)
        self.store.reindex()
        listing = self.cli('list')
        self.assertEqual([doc['trd_id'] for doc in listing['documents']],
                         sorted([later.meta['trd_id'], earlier.meta['trd_id']]))

    def test_migration_exact_selection_hash_confirmation_and_cli(self):
        rec = self.legacy(title='Historical contacts')
        for selector in (rec.meta['trd_id'], rec.path.name, 'HISTORICAL CONTACTS'):
            before = snapshot(self.root)
            result = self.cli('migrate', selector, '--check', '--expect-sha256', rec.sha256)
            self.assertFalse(result['mutated'])
            self.assertEqual(result['document']['trd_id'], rec.meta['trd_id'])
            self.assertTrue(result['preflight']['eligible'])
            self.assertEqual(snapshot(self.root), before)
        for args, code in (
            (('migrate', rec.meta['trd_id']), 2),
            (('migrate', rec.meta['trd_id'], '--expect-sha256', rec.sha256, '--reason', 'Approve.'), 8),
            (('migrate', rec.meta['trd_id'], '--expect-sha256', rec.sha256, '--reason', ' ', '--confirmed'), 2),
            (('migrate', rec.meta['trd_id'], '--expect-sha256', '0' * 64, '--reason', 'Approve.', '--confirmed'), 6),
            (('migrate', rec.meta['trd_id'], '--check', '--expect-sha256', '0' * 64), 6),
            (('migrate', rec.meta['trd_id'], '--check', '--expect-sha256', rec.sha256.upper()), 2),
            (('migrate', rec.meta['trd_id'], '--check', '--confirmed'), 2),
            (('migrate', rec.meta['trd_id'], '--check', '--reason', 'Approve.'), 2),
            (('migrate', 'Historical', '--check'), 3),
            (('migrate', '../bad', '--check'), 2),
        ):
            before = snapshot(self.root)
            self.cli(*args, expected=code)
            self.assertEqual(snapshot(self.root), before)
        twin = self.legacy(title='Historical contacts')
        before = snapshot(self.root)
        ambiguous = self.cli('migrate', 'Historical contacts', '--check', expected=4)
        self.assertEqual(len(ambiguous['candidates']), 2)
        self.assertEqual(snapshot(self.root), before)
        result = self.cli('migrate', rec.path.name, '--expect-sha256', rec.sha256,
                          '--reason', 'Migrate the selected fixture only.', '--confirmed')
        self.assertTrue(result['mutated'])
        self.assertEqual(result['migration_from']['sha256'], rec.sha256)
        self.assertEqual(result['document']['schema_version'], 2)
        self.assertEqual(self.record(selector=twin.meta['trd_id']).sha256, twin.sha256)

    def test_duplicate_migration_is_a_validated_no_op(self):
        rec = self.legacy()
        self.migrate(rec)
        current = self.record()
        # A stale index must remain stale during the no-op as well.
        (self.store.folder / 'INDEX.md').write_text('Preserve stale projection on no-op.\n')
        before = snapshot(self.root)
        check = self.store.preflight(current.path.name, current.sha256)
        self.assertTrue(check['preflight']['already_current'])
        self.assertFalse(check['preflight']['eligible'])
        result = self.migrate(current)
        self.assertEqual(result['status'], 'no_op')
        self.assertFalse(result['mutated'])
        self.assertEqual(result['document'], current.summary())
        self.assertEqual(snapshot(self.root), before)
        for expected, reason, confirmed, code in (
            (rec.sha256, 'Approve.', True, 6),
            (current.sha256.upper(), 'Approve.', True, 2),
            (current.sha256, ' ', True, 2),
            (current.sha256, 'Approve.', False, 8),
        ):
            self.error(code, self.store.migrate, current.meta['trd_id'], expected, reason, confirmed)
            self.assertEqual(snapshot(self.root), before)

    def test_migration_failures_before_and_after_canonical_publication(self):
        rec = self.legacy('not_done')
        before = snapshot(self.root)
        with patch.object(trd.os, 'replace', side_effect=OSError('Injected canonical migration failure')):
            with self.assertRaises(OSError):
                self.migrate(rec)
        self.assertEqual(snapshot(self.root), before)
        self.assertFalse(self.store.lock_path.exists())
        self.assertFalse(list(self.store.folder.glob('.to-trd-tmp-*')))
        real_write = self.store.atomic_write
        def fail_index(path, content, **kwargs):
            if path.name == 'INDEX.md':
                raise OSError('Injected migration projection failure')
            return real_write(path, content, **kwargs)
        with patch.object(self.store, 'atomic_write', side_effect=fail_index):
            exc = self.error(9, self.migrate, rec)
        self.assertEqual(exc.category, 'partial_commit')
        self.assertTrue(exc.details['mutated'])
        self.assertFalse(exc.details['index_updated'])
        self.assertEqual(exc.details['migration_from'], rec.summary())
        self.assertEqual(exc.details['document']['schema_version'], 2)
        current = self.record()
        self.assertEqual(current.meta['status'], 'trd_done')
        self.assertEqual(current.body, self.payload['body'])
        self.assertEqual(exc.details['document']['sha256'], current.sha256)
        self.assertEqual((self.store.folder / 'INDEX.md').read_bytes(), before['TRDs/INDEX.md'][1])
        current_bytes = current.path.read_bytes()
        self.assertTrue(self.store.read()[1])
        self.store.reindex()
        self.assertEqual(current.path.read_bytes(), current_bytes)
        self.assertEqual(self.store.read()[1], [])
        self.assertEqual(len(self.store.read()[0]), 1)

    def test_migration_rechecks_staleness_under_lock_and_before_publication(self):
        for point in ('lock', 'publication'):
            root = self.root / point
            root.mkdir()
            store = trd.Store(root)
            rec = self.legacy(store=store)
            index_bytes = (store.folder / 'INDEX.md').read_bytes()
            manual = rec.path.read_bytes().replace(b'without editing contacts.', b'without altering contacts.')
            self.assertNotEqual(manual, rec.path.read_bytes())
            if point == 'lock':
                real_lock = store.locked
                @contextlib.contextmanager
                def race_lock(*args, **kwargs):
                    with real_lock(*args, **kwargs):
                        rec.path.write_bytes(manual)
                        yield
                with patch.object(store, 'locked', side_effect=race_lock):
                    self.error(6, self.migrate, rec, store)
            else:
                real_write = store.atomic_write
                def race_publish(path, content, **kwargs):
                    if path == rec.path:
                        path.write_bytes(manual)
                    return real_write(path, content, **kwargs)
                with patch.object(store, 'atomic_write', side_effect=race_publish):
                    self.error(6, self.migrate, rec, store)
            self.assertEqual(rec.path.read_bytes(), manual)
            self.assertEqual((store.folder / 'INDEX.md').read_bytes(), index_bytes)
            self.assertEqual(set(p.name for p in store.folder.iterdir()), {rec.path.name, 'INDEX.md'})

    def test_migration_obeys_lock_and_managed_symlink_boundaries(self):
        rec = self.legacy()
        self.store.lock_path.mkdir()
        owner = self.store.lock_path / 'owner.json'
        owner.write_text('{"process_id":123,"command":"existing fixture writer"}')
        before = snapshot(self.root)
        self.error(7, self.store.preflight, rec.meta['trd_id'])
        self.error(7, self.migrate, rec)
        self.assertEqual(snapshot(self.root), before)
        owner.unlink()
        self.store.lock_path.rmdir()
        outside = self.root / 'outside'
        outside.mkdir()
        external = outside / 'original.md'
        external.write_bytes(rec.path.read_bytes())
        rec.path.unlink()
        rec.path.symlink_to(external)
        before = snapshot(self.root)
        self.error(5, self.store.preflight, rec.meta['trd_id'])
        self.error(5, self.migrate, rec)
        self.assertEqual(snapshot(self.root), before)
        rec.path.unlink()
        rec.path.write_bytes(external.read_bytes())
        index = self.store.folder / 'INDEX.md'
        index.unlink()
        index.symlink_to(external)
        before = snapshot(self.root)
        self.error(5, self.store.preflight, rec.meta['trd_id'])
        self.error(5, self.migrate, rec)
        self.assertEqual(snapshot(self.root), before)

    def test_migration_unknown_schema_and_corrupt_catalog_fail_closed(self):
        for replacement in (b'schema_version: 99', b'schema_version: true', b'schema_version: "1"'):
            root = self.root / str(len(list(self.root.iterdir())))
            root.mkdir()
            store = trd.Store(root)
            rec = self.legacy(store=store)
            rec.path.write_bytes(rec.path.read_bytes().replace(b'schema_version: 1', replacement))
            before = snapshot(root)
            self.error(5, store.preflight, rec.meta['trd_id'])
            self.error(5, self.migrate, rec, store)
            self.error(5, store.reindex)
            self.assertEqual(snapshot(root), before)
        rec = self.legacy()
        corrupt = self.store.folder / 'trd_corrupt_2026-08-28.md'
        corrupt.write_text('Malformed peer must not be silently skipped.\n')
        before = snapshot(self.root)
        self.error(5, self.migrate, rec)
        self.assertEqual(snapshot(self.root), before)

    def test_source_handoff_observation_preserves_document_and_authority(self):
        rec = self.make()
        for state in ('draft', 'trd_done'):
            if state == 'trd_done':
                self.change(state, selector=rec.meta['trd_id'])
                rec = self.record(selector=rec.meta['trd_id'])
            before = snapshot(self.root)
            observation = self.cli('show', rec.meta['trd_id'])
            source = observation['document']
            self.assertEqual({key: source[key] for key in ('trd_id', 'revision', 'sha256', 'status', 'schema_version')},
                             {'trd_id': rec.meta['trd_id'], 'revision': rec.meta['revision'],
                              'sha256': rec.sha256, 'status': state, 'schema_version': 2})
            self.assertEqual(observation['body'], rec.body)
            self.assertEqual(snapshot(self.root), before)
            self.assertFalse((self.root / 'Implementation_Plans').exists())
            self.assertFalse((self.root / 'Tasks').exists())
        validated = self.cli('validate')
        self.assertIn('no implementation or external authority', validated['validation_scope'])

    def test_direct_input_bounds_and_large_dependency_graph(self):
        for payload in (dict(self.payload, title='é' * 81),
                        dict(self.payload, body=self.payload['body'] + '\n' * trd.MAX_BYTES),
                        dict(self.payload, body=self.payload['body'] + 'x' * trd.MAX_BYTES)):
            before = snapshot(self.root)
            self.error(2, self.store.create, payload)
            self.assertEqual(snapshot(self.root), before)
        req_start = self.payload['body'].index('### REQ-001')
        req_end = self.payload['body'].index('## Decisions')
        blocks = []
        for number in range(1, 2002):
            dependency = f'REQ-{number - 1:03d}' if number > 1 else 'None.'
            blocks.append(f'### REQ-{number:03d} — Bounded requirement {number}\n'
                          '- Requirement: Preserve the fixture item.\n'
                          '- Source: Explicit synthetic requirement.\n'
                          '- Acceptance: The fixture item remains unchanged.\n'
                          f'- Depends on: {dependency}\n\n')
        valid = self.payload['body'][:req_start] + ''.join(blocks[:-1]) + self.payload['body'][req_end:]
        self.assertEqual(len(trd.validate_body(valid)[1]), 2000)
        invalid = self.payload['body'][:req_start] + ''.join(blocks) + self.payload['body'][req_end:]
        self.error(2, trd.validate_body, invalid)
        rec = self.make()
        before = snapshot(self.root)
        self.error(2, self.store.update, rec.meta['trd_id'], rec.sha256,
                   {'body': rec.body + '\n' * trd.MAX_BYTES})
        self.assertEqual(snapshot(self.root), before)
        self.error(2, trd.parse_document, rec.path, rec.path.read_bytes() + b'\n' * trd.MAX_BYTES)

    def test_id_collision_is_retried_without_overwriting(self):
        class FixtureUUID:
            def __init__(self, prefix):
                self.hex = prefix + '0' * 24
        with patch.object(trd, 'now', return_value=FIXED_TIME):
            with patch.object(trd.uuid, 'uuid4', return_value=FixtureUUID('12345678')):
                first = self.make()
            original = first.path.read_bytes()
            with patch.object(trd.uuid, 'uuid4', side_effect=[FixtureUUID('12345678'), FixtureUUID('87654321')]) as issued:
                second = self.make()
                self.assertEqual(issued.call_count, 2)
        self.assertEqual(first.meta['trd_id'], 'TRD-20260828-12345678')
        self.assertEqual(second.meta['trd_id'], 'TRD-20260828-87654321')
        self.assertEqual(first.path.read_bytes(), original)
        self.assertNotEqual(first.path, second.path)

    def test_legacy_privacy_and_structural_checks_remain_in_force(self):
        rec = self.legacy()
        before = snapshot(self.root)
        synthetic = 'api_key: synthetic_secret_value_123'
        error = self.error(2, self.store.migrate, rec.meta['trd_id'], rec.sha256, synthetic, True)
        self.assertNotIn('synthetic_secret_value_123', str(error))
        self.assertEqual(snapshot(self.root), before)
        original = rec.path.read_bytes()
        variants = (
            original.replace(b'- Depends on: REQ-001', b'- Depends on: REQ-999'),
            original.replace(b'- Depends on: None.', b'- Depends on: REQ-002'),
            original.replace(b'schema_version: 1', b'schema_version: 1\nschema_version: 1'),
            original.replace(b'revision: 7', b'revision: true'),
            original.replace(b'- [ ] Complete\n', b'', 1),
            original + b'\n' + synthetic.encode() + b'\n',
            original + b'\n' * trd.MAX_BYTES,
            b'\xff' + original,
        )
        for variant in variants:
            rec.path.write_bytes(variant)
            before = snapshot(self.root)
            error = self.error(5, self.store.preflight, rec.meta['trd_id'])
            self.assertNotIn('synthetic_secret_value_123', str(error))
            self.error(5, self.migrate, rec)
            self.assertEqual(snapshot(self.root), before)
        rec.path.write_bytes(original)

    def test_read_detects_lock_appearing_during_scan(self):
        rec = self.legacy()
        original_bytes = rec.path.read_bytes()
        original_index = (self.store.folder / 'INDEX.md').read_bytes()
        real_scan = self.store._scan
        def scan_then_lock():
            records = real_scan()
            self.store.lock_path.mkdir()
            (self.store.lock_path / 'owner.json').write_text('{"process_id":123}')
            return records
        with patch.object(self.store, '_scan', side_effect=scan_then_lock):
            self.error(7, self.store.preflight, rec.meta['trd_id'])
        self.assertTrue(self.store.lock_path.is_dir())
        self.assertEqual(rec.path.read_bytes(), original_bytes)
        self.assertEqual((self.store.folder / 'INDEX.md').read_bytes(), original_index)


if __name__ == '__main__':
    unittest.main()
