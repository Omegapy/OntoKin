#!/usr/bin/env python3
"""Retain actual Agent/0.5 source repairs and retrieved GLB/0.5 bytes.

The service performs construction, evaluation, export and artifact retrieval.
This recorder never calls a compiler, simulator, geometry builder or exporter.
The separately versioned reader checks the exact source/message/artifact closure.
"""
from __future__ import annotations

import argparse
import base64
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ontokin.json_limits import measure_json
from tools.build_force_agent_demo import (Recorder as SourceRecorder, DATA,
    PROTOCOL, SCENE, require, seconds, sha, write_json)

SCHEMA = 'ontokin.force-delivery-workflow/0.1'
TARGET = 'ontokin.glb/0.5'
CASE_IDS = ('P01', 'P07', 'P10', 'P11', 'P12', 'P13', 'P21')
CHUNK_BYTES = 32768


def source_revision():
    return {
        'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'tree': subprocess.check_output(['git', 'rev-parse', 'HEAD^{tree}'], cwd=ROOT, text=True).strip(),
        'worktree_clean': not subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip()}


def current_runtime_sha256():
    """Read current package bytes, independently of the running service cache."""
    digest = hashlib.sha256()
    for path in sorted((ROOT / 'ontokin').glob('*.py')):
        digest.update(path.name.encode('utf-8') + b'\0' + path.read_bytes() + b'\0')
    return 'sha256:' + digest.hexdigest()


class Recorder(SourceRecorder):
    def __init__(self, destination):
        revision = source_revision()
        require(revision['worktree_clean'], 'Record delivery evidence from a clean, identified source revision')
        super().__init__(destination)
        self.deliveries = []
        self.export_requests = {}
        self.export_responses = {}
        self.manifest.update(schema_version=SCHEMA, target_contract=TARGET,
            writer_sha256=sha(Path(__file__).read_bytes()),
            helper_inputs={name: sha((ROOT / name).read_bytes()) for name in
                           ('tools/build_force_agent_demo.py', 'tools/force_oracles.py')},
            source_fixtures=list(CASE_IDS), deliveries=self.deliveries,
            source_revision=revision,
            environment={'python': platform.python_version(), 'implementation': platform.python_implementation(),
                         'operating_system': platform.system(), 'machine': platform.machine()},
            limits=['This workflow establishes the named Agent delivery trace and retrieved artifact closure.',
                    'Independent native-loader and browser evidence remain separate required roles.',
                    'Recorded GLB playback does not execute forces or live physics.',
                    'This component does not certify complete F01-F12 or the full product.'])

    def deliver(self, name):
        from tools.force_oracles import oracle_for, sample_requests
        program = self.bundles[name]
        project = 'case-' + name
        options = {'end': seconds(self.cases[name]['request_horizon']), 'fps': 2, 'helpers': False}
        request = self.request(project, 'export', program_revision=program.program_revision,
                               destination=TARGET, options=options)
        response = self.exchange(name + '/export', request)
        self.export_requests[name] = request
        self.export_responses[name] = response
        result = response['result']
        require(response['achieved_level'] == 'delivered', 'Export did not achieve delivered output')
        chunks = []
        roles = []
        offset = 0
        while offset < result['total_bytes']:
            require(len(roles) < 2048, 'Artifact exceeds the declared GLB retrieval bound')
            role = f'{name}/artifact/{len(roles):04d}'
            reply = self.send(role, project, 'artifact', artifact_id=result['artifact_id'],
                              offset=offset, max_bytes=CHUNK_BYTES)
            part = reply['result']
            raw = base64.b64decode(part['data_base64'], validate=True)
            require(raw and part['offset'] == offset and part['total_bytes'] == result['total_bytes'],
                    'Artifact retrieval did not advance over the declared complete file')
            require(part['sha256'] == result['sha256'], 'Artifact chunks identify different files')
            chunks.append(raw)
            roles.append(role)
            offset += len(raw)
            require(part['next_offset'] == (offset if offset < result['total_bytes'] else None),
                    'Artifact next offset is not contiguous')
        data = b''.join(chunks)
        require(len(data) == result['total_bytes'] and sha(data) == result['sha256'],
                'Retrieved GLB bytes do not match the export receipt')
        relative = 'cases/' + name
        directory = self.root / relative
        directory.mkdir(parents=True)
        actual = self.service.read_program(project, program.program_revision)
        require(actual.to_payload() == program.to_payload(), 'Delivered source snapshot changed')
        write_json(directory / 'program.bundle.json', actual.to_payload())
        write_json(directory / 'source-manifest.json', actual.manifest())
        write_json(directory / 'scene.export.json', result['report'])
        (directory / 'scene.glb').write_bytes(data)
        for unit in actual.units:
            require(Path(unit.filename).name == unit.filename, 'The fixed workflow expects safe source basenames')
            (directory / unit.filename).write_bytes(unit.raw)
        samples = []
        reference_roles = []
        fields = ('element_id', 'position_m', 'orientation_wxyz', 'velocity_m_per_s',
                  'angular_velocity_rad_per_s', 'forces', 'impulses', 'pose_authority', 'own_mass_kg')
        for index, sample in enumerate(sample_requests(name)):
            role = f'{name}/destination-sample/{index:04d}'
            reply = self.send(role, project, 'inspect', program_revision=program.program_revision,
                run_id=response['run_id'], selector={}, fields=['identity', 'state'], limit=1000,
                time={'seconds': sample['time_seconds'], 'side': sample['side']})
            require(not reply['truncated'] and reply['next_cursor'] is None, 'Destination reference is incomplete')
            objects = {item['path']: {field: copy.deepcopy(item['state'][field]) for field in fields}
                       for item in reply['result']['items']}
            samples.append({**sample, 'objects': objects})
            reference_roles.append(role)
        write_json(directory / 'scene.reference.json', dict(schema_version='ontokin.force-native-reference/0.1',
            program_revision=program.program_revision, source_manifest=program.manifest(),
            artifact_sha256=result['sha256'], implementation=self.service.implementation,
            tolerances=result['report']['tolerances'], samples=samples))
        write_json(directory / 'oracle.json', {**oracle_for(name), 'program_revision': program.program_revision})
        filenames = ('program.bundle.json', 'source-manifest.json', 'scene.glb', 'scene.export.json',
                     'scene.reference.json', 'oracle.json', *(unit.filename for unit in actual.units))
        self.deliveries.append(dict(case_id=name, project_id=project,
            program_revision=program.program_revision, export_role=name + '/export',
            artifact_id=result['artifact_id'], sha256=result['sha256'], total_bytes=len(data),
            options=options, artifact_roles=roles, reference_roles=reference_roles,
            files={filename: {'path': relative + '/' + filename, 'sha256': sha((directory / filename).read_bytes())}
                   for filename in filenames}))

    def failures(self):
        program = self.bundles['P01']
        project = 'case-P01'
        self.send('failure/invalid-create', 'invalid', 'create', bundle=self.bundle('N01').to_payload(),
            expected_program_revision=None, requested_level='constructed',
            expected=('failed', 'rejected'), code='OKL-E-TYPE')
        start = program.entry.raw.index(b'for 1[s]') + 4
        self.send('failure/invalid-edit', project, 'edit', expected_program_revision=program.program_revision,
            patches=[dict(source_id='entry', source_revision=program.entry.revision, element_id=SCENE,
                          start_byte=start, end_byte=start + 4, expected_text='1[s]', replacement='-1[s]')],
            requested_level='constructed', expected=('failed', 'rejected'), code='OKL-E-EVENT-ORDER')
        original = self.export_requests['P01']
        first = self.export_responses['P01']
        require(self.exchange('retry/same-export', original) == first, 'Exact export retry changed its retained receipt')
        collision = copy.deepcopy(original)
        collision['options']['fps'] = 3
        self.exchange('retry/collision', collision, expected='rejected', code='OKL-E-REQUEST-ID')
        self.send('retry/status', project, 'status', target_request_id=original['request_id'])
        artifact = first['result']
        self.send('isolation/foreign-artifact', 'foreign', 'artifact', artifact_id=artifact['artifact_id'],
                  max_bytes=64, expected=('failed', 'rejected'), code='OKA-E-ARTIFACT')
        self.send('failure/artifact-offset', project, 'artifact', artifact_id=artifact['artifact_id'],
                  offset=artifact['total_bytes'] + 1, expected=('failed', 'rejected'), code='OKA-E-ARTIFACT')
        self.send('failure/final-budget', 'limited', 'create', bundle=program.to_payload(),
            expected_program_revision=None, requested_level='delivered', destination=TARGET,
            options=copy.deepcopy(original['options']),
            budgets={'max_value_entries': measure_json(first)['entries'] - 1},
            expected=('failed', 'rejected'), code='OKA-E-RESOURCE')
        self.send('failure/budget-candidate-export', 'limited', 'export',
            program_revision=program.program_revision, destination=TARGET,
            expected=('failed', 'rejected'), code='OKL-E-REVISION')
        queued = self.request('queued', 'create', bundle=program.to_payload(),
            expected_program_revision=None, requested_level='delivered', destination=TARGET,
            options=copy.deepcopy(original['options']))
        self.exchange('cancel/submit', queued, method='submit', expected='queued')
        self.send('cancel/request', 'queued', 'cancel', target_request_id=queued['request_id'])
        self.service.work_next()
        self.exchange('cancel/result', queued, expected='cancelled')
        self.send('cancel/status', 'queued', 'status', target_request_id=queued['request_id'])
        prefix = self.bundles['P21']
        self.send('prefix/full-failure', 'case-P21', 'export', program_revision=prefix.program_revision,
            destination=TARGET, expected='failed', code='OKL-E-NUMERIC')
        self.send('prefix/reject-later', 'case-P21', 'inspect', program_revision=prefix.program_revision,
            run_id=self.export_responses['P21']['run_id'], selector={'path': 'ball'}, fields=['state'], limit=1,
            time={'seconds': '1.5', 'side': 'after'}, expected=('failed', 'rejected'), code='OKL-E-SAMPLE')
        self.send('failure/head', project, 'inspect', program_revision=program.program_revision,
                  selector={'path': 'ball'}, fields=['identity', 'source'], limit=1)

    def build(self):
        try:
            self.send('discovery', 'discovery', 'discover', profile='force-0.1', limit=1000)
            for name in CASE_IDS:
                self.positive(name)
                self.deliver(name)
            self.failures()
            self.manifest['source_revision_after'] = source_revision()
            require(self.manifest['source_revision_after'] == self.manifest['source_revision'],
                    'Source commit, tree or clean state changed during delivery recording')
            require(self.manifest['writer_sha256'] == sha(Path(__file__).read_bytes()) and
                    self.manifest['helper_inputs'] == {name: sha((ROOT / name).read_bytes())
                                                       for name in self.manifest['helper_inputs']},
                    'The delivery writer or its helpers changed during recording')
            require(self.manifest['fixture_inputs'] == {name: sha((DATA / name).read_bytes())
                                                        for name in self.manifest['fixture_inputs']},
                    'The adopted source inputs changed during recording')
            require(self.manifest['implementation'] == self.service.implementation and
                    current_runtime_sha256() == self.manifest['implementation']['source_code_sha256'],
                    'The running service no longer matches the current implementation bytes')
            self.manifest.update(status='recorded', exchange_count=len(self.trace),
                snapshot_count=len(self.snapshots), delivery_count=len(self.deliveries),
                sample_count=sum('/sample/' in row['role'] for row in self.trace),
                artifact_chunk_count=sum(len(row['artifact_roles']) for row in self.deliveries),
                destination_sample_count=sum(len(row['reference_roles']) for row in self.deliveries))
        except Exception as error:
            self.manifest.update(status='failed', failure={'type': type(error).__name__, 'message': str(error)})
            raise
        finally:
            self.service.close()
            self.manifest['finished_at_utc'] = datetime.now(timezone.utc).isoformat()
            write_json(self.root / 'workflow.json', self.manifest)
        return {key: self.manifest[key] for key in ('schema_version', 'status', 'exchange_count',
            'snapshot_count', 'sample_count', 'delivery_count', 'artifact_chunk_count', 'destination_sample_count', 'implementation')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    arguments = parser.parse_args()
    print(json.dumps(Recorder(arguments.output_dir).build(), indent=2))


if __name__ == '__main__':
    main()
