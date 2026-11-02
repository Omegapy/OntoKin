#!/usr/bin/env python3
"""Execute the frozen C088 Agent workflows and retain actual durable evidence.

This producer never supplies an expected semantic result to the runtime. It
materializes published request templates, delegates the original service and
ledger methods, and retains original raw bytes, SQLite snapshots and artifacts.
Independent readers are separate programs and are not imported here.
"""
from __future__ import annotations

import argparse
import base64
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
import platform
import shutil
import sqlite3
import subprocess
import sys
import threading
import time
import traceback
from unittest.mock import patch


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def codes(response):
    result = [item.get('code') for item in response.get('diagnostics', [])]
    if response.get('protocol_error') is not None:
        result.append(response['protocol_error'].get('code'))
    return result


def error_record(error):
    result = {'type': type(error).__name__, 'message': str(error), 'identity': id(error)}
    if hasattr(error, 'diagnostic'):
        d = error.diagnostic
        result.update(code=d.code, phase=d.phase, details=d.details)
    return result


def source_identity(root):
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=root)
    rows = []
    for entry in git('ls-files', '-s', '-z').split(b'\0'):
        if not entry:
            continue
        metadata, name = entry.split(b'\t', 1)
        mode, blob, stage = metadata.decode().split()
        require(stage == '0', 'Source index has unresolved stages')
        path = name.decode()
        raw = (root / path).read_bytes()
        actual_blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        require(actual_blob == blob, 'Working bytes differ from fixed index: ' + path)
        rows.append({'path': path, 'mode': mode, 'git_blob': blob, 'bytes': len(raw), 'sha256': sha(raw)})
    return {'head': git('rev-parse', 'HEAD').decode().strip(),
            'tree': git('rev-parse', 'HEAD^{tree}').decode().strip(),
            'status': git('status', '--porcelain').decode(),
            'tracked_files': rows, 'inventory_sha256': sha(canonical(rows))}


def fixture_identity(root):
    manifest = json.loads((root / 'INPUTS-MANIFEST.json').read_bytes())
    rows = []
    for p in sorted(root.rglob('*')):
        if not p.is_file() or p.name == 'INPUTS-MANIFEST.json':
            continue
        raw = p.read_bytes()
        rows.append({'path': p.relative_to(root).as_posix(), 'bytes': len(raw),
                     'mode': '100755' if p.stat().st_mode & 0o111 else '100644', 'sha256': sha(raw)})
    require(rows == manifest['files'], 'Exact frozen fixture inventory')
    require(sha(canonical(rows)) == manifest['inventory_sha256'], 'Frozen inventory digest')
    return {'manifest_sha256': sha((root / 'INPUTS-MANIFEST.json').read_bytes()),
            'inventory_sha256': manifest['inventory_sha256'], 'files': rows}


class AgentRun:
    def __init__(self, root, fixtures, output):
        from ontokin.keyed_membership_agent import KeyedMembershipAgentService
        from ontokin.execution_budget import HostPolicy, SharedExecutionBudget
        from ontokin.texture_bundle import load_texture_file_manifest
        from jsonschema import Draft202012Validator
        from referencing import Registry, Resource
        self.root, self.fixtures, self.output = root, fixtures, output
        self.Service, self.HostPolicy = KeyedMembershipAgentService, HostPolicy
        self.SharedExecutionBudget = SharedExecutionBudget
        self.load_files = load_texture_file_manifest
        self.contract = json.loads((fixtures / 'agent/request-workflows.json').read_bytes())
        self.agent_cases = {c['files']: c for c in json.loads((fixtures / 'agent/expected.json').read_bytes())['cases']}
        self.source_cases = {c['id']: c for c in json.loads((fixtures / 'source-expected.json').read_bytes())['cases']}
        self.service = None
        self.scenario = None
        self.responses, self.requests, self.captures = {}, {}, {}
        self.transcript, self.ledger_records = [], []
        self.ledger_objects, self.ledger_by_id = [], {}
        self.barrier = None
        self.serial = 0
        self.summary = {'schema_version': 'ontokin.c088-agent-observations/1',
            'status': 'running', 'workflows': [], 'failures': [], 'stores': [],
            'snapshots': [], 'agent_artifacts': [], 'reopens': [], 'cancellation_barriers': [],
            'publication_interruptions': [], 'producer': {'path': str(Path(__file__).resolve()),
                'sha256': sha(Path(__file__).read_bytes())},
            'python': sys.version, 'platform': platform.platform(),
            'started_utc': dt.datetime.now(dt.timezone.utc).isoformat()}
        resources = {}
        for p in (root / 'docs/language-design').rglob('*.schema.json'):
            value = json.loads(p.read_bytes())
            if '$id' in value:
                resources[value['$id']] = Resource.from_contents(value)
        registry = Registry().with_resources(resources.items())
        self.validators = {kind: Draft202012Validator(json.loads((root /
            f'docs/language-design/agent-v0.21/{kind}.schema.json').read_bytes()), registry=registry)
            for kind in ['request', 'response']}

    def payload(self, file, *, core=False):
        p = self.fixtures / file if core else self.fixtures / 'agent' / file
        source = self.load_files(p)
        expected = self.source_cases[Path(file).name.removesuffix('.files.json')] if core else self.agent_cases[file]
        require(source.program_revision == expected['program_revision'], 'Prewritten program revision: ' + file)
        require(source.manifest() == expected['canonical_manifest'], 'Prewritten canonical manifest: ' + file)
        return source.to_payload()

    def materialize(self, value, loop=None):
        if isinstance(value, dict):
            if set(value) == {'$bundle_file'}:
                return self.payload(value['$bundle_file'])
            if set(value) in ({'$response'}, {'$capture'}):
                is_response = '$response' in value
                parts = value['$response' if is_response else '$capture'].split('.')
                result = (self.responses if is_response else self.captures)['.'.join(parts[:2])]
                for name in parts[2:]:
                    result = result[int(name)] if isinstance(result, list) else result[name]
                return copy.deepcopy(result)
            if set(value) == {'$loop'}:
                return loop[value['$loop']]
            return {key: self.materialize(child, loop) for key, child in value.items()}
        if isinstance(value, list):
            return [self.materialize(child, loop) for child in value]
        if isinstance(value, str) and loop is not None:
            return value.replace('${index}', str(loop['index']))
        return value

    def state(self, project):
        if self.service is None:
            return None
        revision = self.service.accepted_revision(project)
        with self.service._store.connection() as db:
            row = db.execute('SELECT raw FROM sources WHERE project_id=? AND revision=?',
                             (project, revision)).fetchone() if revision else None
            runs = [dict(r) for r in db.execute('SELECT id,source_revision,descriptor,version FROM runs WHERE project_id=? ORDER BY id', (project,))]
            artifacts = [{'id': r[0], 'program_revision': r[1], 'bytes': len(r[2]),
                          'sha256': sha(bytes(r[2])), 'stored_sha256': r[3]} for r in db.execute(
                          'SELECT id,source_revision,data,sha256 FROM artifacts WHERE project_id=? ORDER BY id', (project,))]
        raw = None if row is None else bytes(row[0])
        payload = None if raw is None else json.loads(raw)
        return {'accepted_program_revision': revision,
            'accepted_payload_sha256': None if payload is None else sha(canonical(payload)),
            'accepted_source_bytes_sha256': None if raw is None else sha(raw),
            'assets': [] if payload is None else [{k: a[k] for k in ['asset_id', 'sha256', 'media_type']} |
                {'bytes': len(base64.b64decode(a['data_base64'], validate=True))} for a in payload.get('assets', [])],
            'runs': runs, 'artifacts': artifacts}

    def install_observer(self):
        original = self.service._make_check
        def make_check(task):
            check = original(task)
            ledger = check.execution_budget
            row = {'index': len(self.ledger_records), 'workflow': self.scenario,
                   'request_id': task.request['request_id'], 'project_id': task.request['project_id'],
                   'ledger_id': id(ledger), 'started': ledger.started,
                   'original_clock_id': id(ledger._clock), 'host_policy': ledger.policy.ceilings,
                   'caller_caps': dict(ledger.caller_caps), 'ticks': [], 'callback_errors': []}
            self.ledger_records.append(row)
            self.ledger_objects.append(ledger)
            self.ledger_by_id[id(ledger)] = row
            original_poll = ledger.check
            row['original_callback_id'] = id(original_poll)
            def observed_poll():
                barrier = self.barrier
                if (barrier is not None and task.request['request_id'] == barrier['request_id']
                        and ledger.stage == barrier['stage'] and not barrier['reached'].is_set()):
                    barrier['at_barrier'] = {'ledger_id': id(ledger), 'stage': ledger.stage,
                        'operations': ledger.operations, 'started': ledger.started,
                        'clock_id': id(ledger._clock), 'resolved': ledger.report(status='barrier')}
                    barrier['reached'].set()
                    require(barrier['release'].wait(30), 'Actual cancellation barrier timed out')
                    # The existing service poll throttles at five milliseconds.
                    # This real wait leaves its timestamp and original clock intact.
                    time.sleep(.006)
                try:
                    if original_poll is not None:
                        return original_poll()
                except BaseException as error:
                    row['callback_errors'].append(error_record(error))
                    raise
            ledger.check = observed_poll
            return check
        self.service._make_check = make_check

    def observe_tick(self, original, ledger, node=None, amount=1):
        row = self.ledger_by_id.get(id(ledger))
        observed = row is not None and (ledger.stage or '').startswith(('keyed_membership_', 'string_concat_'))
        tick = None
        if observed:
            tick = {'stage': ledger.stage, 'amount': amount, 'operations_before': ledger.operations,
                'string_bytes_before': ledger.string_concat_bytes,
                'source_id': getattr(node, 'source_id', None),
                'start_byte': getattr(node, 'start', None), 'end_byte': getattr(node, 'end', None)}
            row['ticks'].append(tick)
        try:
            return original(ledger, node, amount)
        except BaseException as error:
            if tick is not None:
                tick['exception'] = error_record(error)
            raise
        finally:
            if tick is not None:
                tick.update(operations_after=ledger.operations, string_bytes_after=ledger.string_concat_bytes)

    def refresh_ledgers(self):
        for ledger, row in zip(self.ledger_objects, self.ledger_records):
            row.update(final_stage=ledger.stage, final_started=ledger.started,
                final_clock_id=id(ledger._clock), final_callback_error_id=None if ledger.callback_error is None else id(ledger.callback_error),
                execution_budget=ledger.report(status='observed'))

    def open(self, directory, policy=None):
        self.service = self.Service(directory, host_policy=self.HostPolicy(**(policy or self.contract['default_host_policy'])))
        self.install_observer()

    def reopen(self, policy=None):
        previous = self.service
        path = previous.database_path.parent
        record = {'workflow': self.scenario, 'after_exchange': len(self.transcript),
            'old_owner': previous._store.owner, 'old_policy': previous.host_policy.ceilings,
            'store_path': previous.database_path.relative_to(self.output).as_posix()}
        previous.close()
        self.open(path, policy)
        record.update(new_owner=self.service._store.owner, new_policy=self.service.host_policy.ceilings)
        require(record['old_owner'] != record['new_owner'], 'Reopen creates a new service session')
        self.summary['reopens'].append(record)

    def call(self, request, label, *, wait=True):
        self.serial += 1
        sequence = self.serial
        raw = json.dumps(request, ensure_ascii=False, allow_nan=False).encode()
        request = json.loads(raw)
        request_path = f'agent/request-{sequence:05}.json'
        response_path = f'agent/response-{sequence:05}.json'
        (self.output / request_path).write_bytes(raw)
        row = {'sequence': sequence, 'workflow': self.scenario, 'step': label,
            'wait': wait, 'request': request, 'request_file': request_path,
            'request_sha256': sha(raw), 'state_before': self.state(request['project_id']),
            'host_policy': self.service.host_policy.ceilings,
            'request_schema_errors': [e.message for e in self.validators['request'].iter_errors(request)]}
        self.requests[self.scenario + '.' + label] = copy.deepcopy(request)
        try:
            response = self.service.handle(request, wait=wait)
            wire = json.dumps(response, ensure_ascii=False, allow_nan=False).encode()
            (self.output / response_path).write_bytes(wire)
            row.update(response=copy.deepcopy(response), response_file=response_path,
                response_sha256=sha(wire), response_schema_errors=[e.message for e in self.validators['response'].iter_errors(response)])
            self.responses[self.scenario + '.' + label] = copy.deepcopy(response)
        except BaseException as error:
            row['exception'] = error_record(error)
            raise
        finally:
            row['state_after'] = self.state(request['project_id'])
            row['ledger_indices'] = [r['index'] for r in self.ledger_records
                if r['request_id'] == request['request_id'] and r['project_id'] == request['project_id']]
            self.transcript.append(row)
            save(self.output / f'agent/exchange-{sequence:05}.json', row)
        require(not row['request_schema_errors'], 'Actual request failed schema: ' + label)
        require(not row['response_schema_errors'], 'Actual response failed schema: ' + label)
        return response

    def check_step(self, step, response):
        if 'expected_status' in step:
            require(response['status'] == step['expected_status'],
                f"{self.scenario}.{step.get('step')}: expected {step['expected_status']}, observed {response['status']} {codes(response)}")
        if 'expected_code' in step:
            require(step['expected_code'] in codes(response), 'Frozen diagnostic code: ' + str(step))
        if 'expected_budget_reason' in step:
            require(any(d.get('details', {}).get('budget_reason') == step['expected_budget_reason']
                for d in response.get('diagnostics', [])), 'Frozen budget reason')
        if 'expect_exact_response_ref' in step:
            require(response == self.responses[step['expect_exact_response_ref']], 'Exact durable retry response')
        if 'expected_next_cursor_equals' in step:
            require(response['next_cursor'] == self.materialize(step['expected_next_cursor_equals']), 'Exact retained first-page cursor')

    def execute_step(self, step):
        if step.get('action') == 'close_and_reopen_same_store':
            self.reopen(step.get('host_policy'))
            return None
        request = (copy.deepcopy(self.requests[step['request_ref']]) if 'request_ref' in step
                   else self.materialize(step['request']))
        request.update(step.get('override', {}))
        response = self.call(request, step['step'])
        self.check_step(step, response)
        if request['operation'] == 'export' and response['status'] == 'succeeded' and 'request_ref' not in step:
            self.retrieve(response, step['step'])
        return response

    def request(self, project, request_id, operation, **fields):
        return {'schema_version': 'ontokin.agent/0.21', 'project_id': project,
                'request_id': request_id, 'operation': operation, **fields}

    def retrieve(self, response, name):
        expected = response['result']
        chunks, offset, index = [], 0, 0
        first = len(self.transcript) + 1
        while offset < expected['total_bytes']:
            label = name + '-whole-' + str(index)
            request = self.request(response['project_id'], response['request_id'] + '-whole-' + str(index),
                'artifact', artifact_id=expected['artifact_id'], offset=offset, max_bytes=65536)
            part = self.call(request, label)
            require(part['status'] == 'succeeded', 'Artifact retrieval must succeed')
            body = part['result']
            raw = base64.b64decode(body['data_base64'], validate=True)
            require(raw and body['offset'] == offset, 'Artifact retrieval must advance exactly')
            require(body['program_revision'] == response['program_revision'], 'Artifact immutable revision')
            chunks.append(raw)
            offset += len(raw)
            index += 1
        data = b''.join(chunks)
        require(len(data) == expected['total_bytes'] and 'sha256:' + sha(data) == expected['sha256'], 'Complete artifact identity')
        path = 'agent/artifacts/' + self.scenario + '-' + name + '.glb'
        destination = self.output / path
        require(not destination.exists(), 'Fresh artifact path')
        destination.write_bytes(data)
        self.summary['agent_artifacts'].append({'workflow': self.scenario, 'project_id': response['project_id'],
            'name': name, 'glb': path, 'bytes': len(data), 'sha256': sha(data),
            'program_revision': response['program_revision'], 'artifact_id': expected['artifact_id'],
            'export_request_id': response['request_id'], 'retrieval_first_exchange': first,
            'retrieval_last_exchange': len(self.transcript)})

    def cancellation(self, spec):
        for item in spec['repeat_for_each_stage']:
            request = self.materialize(item['queue_request'])
            before = self.state(request['project_id'])
            barrier = {'stage': item['stage'], 'request_id': request['request_id'],
                'reached': threading.Event(), 'release': threading.Event()}
            errors, worker = [], None
            self.barrier = barrier
            try:
                queue = self.call(request, 'queue-' + item['stage'], wait=False)
                require(queue['status'] == item['expected_queue_status'], 'Frozen queued status')
                def work():
                    try:
                        self.service.work_next()
                    except BaseException as error:
                        errors.append(error_record(error))
                worker = threading.Thread(target=work, name='c088-membership-cancel')
                worker.start()
                require(barrier['reached'].wait(30), 'Actual membership stage reached before cancel')
                response = self.call(self.materialize(item['cancel_request']), 'cancel-' + item['stage'])
                require(response['status'] == 'succeeded', 'Actual cancel succeeds')
                barrier['release'].set()
                worker.join(30)
                require(not worker.is_alive() and not errors, 'Cancelled worker terminates cleanly')
                terminal = self.call(request, 'terminal-' + item['stage'])
                require(terminal['status'] == item['expected_terminal_status'], 'Frozen cancellation terminal status')
                status = self.call(self.materialize(item['status_request']), 'status-' + item['stage'])
                require(status['status'] == 'succeeded', 'Actual cancellation status')
                require(before == self.state(request['project_id']), 'Cancellation preserves all accepted effects')
                actual = [(ledger, row) for ledger, row in zip(self.ledger_objects, self.ledger_records)
                    if row['request_id'] == request['request_id']]
                require(any(ledger.callback_error is not None and any(e['identity'] == id(ledger.callback_error)
                    for e in row['callback_errors']) for ledger, row in actual), 'Original callback exception object retained')
            finally:
                barrier['release'].set()
                if worker is not None:
                    worker.join(30)
                self.barrier = None
                self.refresh_ledgers()
                self.summary['cancellation_barriers'].append({
                    'stage': item['stage'], 'request_id': request['request_id'],
                    'reached': barrier['reached'].is_set(), 'checkpoint': barrier.get('at_barrier'),
                    'worker_errors': errors, 'before': before, 'after': self.state(request['project_id']),
                    'ledger_indices': [r['index'] for r in self.ledger_records if r['request_id'] == request['request_id']],
                    'intervention': 'Pause actual original request callback at a real membership tick, send protocol cancel, then resume original callback after its normal polling interval; no clock/counter/cap replacement.'})

    def publication_interruption(self, spec):
        request = self.materialize(spec['export_request'])
        before = self.state(request['project_id'])
        original = self.service._persist_task_metadata
        prepared = []
        class PublicationInterruption(BaseException):
            pass
        sentinel = PublicationInterruption('Frozen deliberate interruption in the actual uncommitted publication transaction')
        def fail_after_prepare(db, task):
            if task.artifact is not None:
                raw, report, artifact_id = task.artifact
                path = 'agent/artifacts/A07-prepared-only.glb'
                (self.output / path).write_bytes(raw)
                row = {'artifact_id': artifact_id, 'request_id': task.request['request_id'],
                    'bytes': len(raw), 'sha256': sha(raw), 'glb': path,
                    'sqlite_transaction_active': db.in_transaction, 'exception_identity': id(sentinel)}
                prepared.append(row)
                self.captures['A07.prepared'] = row
                raise sentinel
            return original(db, task)
        self.service._persist_task_metadata = fail_after_prepare
        caught = None
        try:
            self.call(request, 'export')
        except PublicationInterruption as error:
            caught = error
        finally:
            self.service._persist_task_metadata = original
        require(caught is sentinel and len(prepared) == 1 and prepared[0]['sqlite_transaction_active'],
                'Actual uncommitted prepared publication interruption')
        interrupted_state = self.state(request['project_id'])
        require(before == interrupted_state, 'Interrupted transaction publishes no accepted effects')
        for step in spec['then']:
            result = self.execute_step(step)
            if step.get('step') == 'status':
                require(result['result']['target_status'] == spec['expected_target_status'], 'Exact interrupted target status')
        self.summary['publication_interruptions'].append({'prepared_only': prepared,
            'before': before, 'interrupted_state': interrupted_state,
            'expected_outcome_source': 'frozen A07', 'actual_status_response': self.responses['A07.status'],
            'same_exception_object': caught is sentinel})

    def slices(self, spec):
        loop = spec['artifact_loop']
        export = self.responses['A10.export']
        total = export['result']['total_bytes']
        offset, index, chunks = 0, 0, []
        while offset < total:
            request = self.materialize(loop['request_template'], {'offset': offset, 'index': index})
            response = self.call(request, 'slice-' + str(index))
            require(response['status'] == 'succeeded', 'Frozen artifact slice succeeds')
            body = response['result']
            data = base64.b64decode(body['data_base64'], validate=True)
            require(data and body['offset'] == offset and body['total_bytes'] == total, 'Exact bounded artifact slice')
            chunks.append(data)
            offset += len(data)
            index += 1
        require('sha256:' + sha(b''.join(chunks)) == export['result']['sha256'], 'Whole frozen sliced artifact')
        for suffix, at, status in [('eof', total, 'succeeded'), ('past-eof', total + 1, 'rejected')]:
            request = self.materialize(loop['request_template'], {'offset': at, 'index': suffix})
            request['max_bytes'] = 1
            response = self.call(request, suffix)
            require(response['status'] == status, 'Artifact boundary status')
            if suffix == 'eof':
                require(response['result']['data_base64'] == '' and response['result']['next_offset'] is None, 'Exact artifact EOF')
            else:
                require('OKA-E-ARTIFACT' in codes(response), 'Exact past-EOF artifact refusal')
        loop = spec['asset_loop']
        offset, index, chunks = 0, 0, []
        while offset < loop['expected_bytes']:
            request = self.materialize(loop['request_template'], {'offset': offset, 'index': index})
            response = self.call(request, 'asset-' + str(index))
            require(response['status'] == 'succeeded', 'Frozen asset slice succeeds')
            body = response['result']
            data = base64.b64decode(body['data_base64'], validate=True)
            require(data and body['offset'] == offset and len(data) <= 17, 'Bounded exact asset progress')
            chunks.append(data)
            offset += len(data)
            index += 1
        raw = b''.join(chunks)
        require(len(raw) == loop['expected_bytes'] and sha(raw) == loop['expected_sha256'], 'Frozen whole asset bytes')

    def warm_provenance(self, spec):
        for index, name in enumerate(spec['fresh_projects_from_source_cases']):
            project = 'c088-a11-' + str(index)
            case = self.source_cases[name]
            prefix = project + '-'
            requests = [self.request(project, prefix + 'create', 'create', bundle=self.payload(case['files'], core=True),
                expected_program_revision=None, requested_level='constructed')]
            for suffix in ['inspect-1', 'inspect-2']:
                requests.append(self.request(project, prefix + suffix, 'inspect', program_revision=case['program_revision'],
                    selector={'path': 'probe'}, fields=['identity', 'source', 'values'], limit=1))
            requests.append(self.request(project, prefix + 'validate-1', 'validate',
                program_revision=case['program_revision'], requested_level='represented'))
            for request in requests:
                response = self.call(request, name + '-' + request['operation'] + '-' + request['request_id'])
                require(response['status'] == 'succeeded', 'Warm provenance request: ' + name)
            self.reopen()
            for operation in ['inspect', 'validate']:
                fields = ({'selector': {'path': 'probe'}, 'fields': ['identity', 'source', 'values'], 'limit': 1}
                          if operation == 'inspect' else {'requested_level': 'represented'})
                request = self.request(project, prefix + operation + '-reopened', operation,
                    program_revision=case['program_revision'], **fields)
                response = self.call(request, name + '-' + operation + '-reopened')
                require(response['status'] == 'succeeded', 'Reopened provenance request: ' + name)

    def snapshot_store(self):
        path = self.output / ('agent/' + self.scenario + '-store.sqlite3')
        require(not path.exists(), 'Fresh immutable snapshot')
        destination = sqlite3.connect(path)
        try:
            with self.service._store.connection() as source:
                source.backup(destination)
                rows = source.execute('SELECT project_id,revision,raw FROM sources ORDER BY project_id,revision').fetchall()
            destination.commit()
            destination.execute('PRAGMA wal_checkpoint(TRUNCATE)')
            require(destination.execute('PRAGMA journal_mode=DELETE').fetchone()[0] == 'delete',
                    'Snapshot must be a self-contained database')
        finally:
            destination.close()
        require(not Path(str(path) + '-wal').exists() and not Path(str(path) + '-shm').exists(),
                'Closed immutable snapshot has no live SQLite auxiliaries')
        for row in rows:
            raw = bytes(row['raw'])
            relative = f"agent/snapshots/{self.scenario}/{row['project_id']}/{row['revision'].split(':', 1)[1]}.json"
            target = self.output / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
            self.summary['snapshots'].append({'workflow': self.scenario, 'project_id': row['project_id'],
                'program_revision': row['revision'], 'path': relative, 'bytes': len(raw), 'sha256': sha(raw)})
        self.summary['stores'].append({'workflow': self.scenario, 'path': path.relative_to(self.output).as_posix(),
            'bytes': path.stat().st_size, 'sha256': sha(path.read_bytes()),
            'live_path': self.service.database_path.relative_to(self.output).as_posix(),
            'reader_mode': 'Closed checkpointed snapshot; inspect with mode=ro&immutable=1 or use a private copy.'})

    def run(self):
        original = self.SharedExecutionBudget.tick
        def observed(ledger, node=None, amount=1):
            return self.observe_tick(original, ledger, node, amount)
        with patch.object(self.SharedExecutionBudget, 'tick', observed):
            for spec in self.contract['scenarios']:
                self.scenario = spec['id']
                record = {'id': spec['id'], 'name': spec['name'], 'first_exchange': len(self.transcript) + 1}
                self.open(self.output / 'live-stores' / spec['id'])
                try:
                    for step in spec.get('steps', []):
                        self.execute_step(step)
                    if spec['id'] == 'A05':
                        self.cancellation(spec)
                    elif spec['id'] == 'A07':
                        self.publication_interruption(spec)
                    elif spec['id'] == 'A10':
                        self.slices(spec)
                    elif spec['id'] == 'A11':
                        self.warm_provenance(spec)
                    record['status'] = 'observed_as_expected'
                except Exception as error:
                    record.update(status='failed', exception=error_record(error), traceback=traceback.format_exc())
                    self.summary['failures'].append({'workflow': spec['id'], 'exception': error_record(error)})
                finally:
                    self.refresh_ledgers()
                    self.snapshot_store()
                    self.service.close()
                    self.service = None
                    record['last_exchange'] = len(self.transcript)
                    self.summary['workflows'].append(record)
                    save(self.output / 'summary.json', self.summary)
        self.summary['operation_inventory'] = sorted({r['request']['operation'] for r in self.transcript})
        save(self.output / 'agent/transcript.json', self.transcript)
        save(self.output / 'agent/ledger-observations.json', self.ledger_records)
        require(self.summary['operation_inventory'] == sorted(self.contract['required_operations']), 'All twelve actual operations')
        self.summary['status'] = 'passed' if not self.summary['failures'] else 'failed'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkout', type=Path, required=True)
    parser.add_argument('--fixtures', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root, fixtures, output = args.checkout.resolve(), args.fixtures.resolve(), args.output.resolve()
    require(not output.exists() and not output.is_relative_to(root), 'Output must be fresh and outside candidate')
    output.mkdir(parents=True)
    (output / 'agent/artifacts').mkdir(parents=True)
    before = source_identity(root)
    require(not before['status'], 'Candidate must be clean and committed before execution')
    inputs = fixture_identity(fixtures)
    save(output / 'source-before.json', before)
    save(output / 'inputs-before.json', inputs)
    sys.path.insert(0, str(root))
    run = AgentRun(root, fixtures, output)
    try:
        run.run()
    except BaseException as error:
        run.summary.update(status='failed', fatal_exception=error_record(error),
                           fatal_traceback=traceback.format_exc())
        raise
    finally:
        if run.service is not None:
            run.service.close()
        run.refresh_ledgers()
        save(output / 'agent/transcript.json', run.transcript)
        save(output / 'agent/ledger-observations.json', run.ledger_records)
        after = source_identity(root)
        after_inputs = fixture_identity(fixtures)
        save(output / 'source-after.json', after)
        save(output / 'inputs-after.json', after_inputs)
        run.summary.update(source=before, source_unchanged=before == after,
            frozen_inputs_unchanged=inputs == after_inputs,
            completed_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
            producer_sha256_after=sha(Path(__file__).read_bytes()))
        require(before == after and inputs == after_inputs, 'Exact source/input identity after execution')
        save(output / 'summary.json', run.summary)
        inventory = [{'path': p.relative_to(output).as_posix(), 'bytes': p.stat().st_size,
                      'sha256': sha(p.read_bytes())} for p in sorted(output.rglob('*')) if p.is_file()]
        save(output / 'PRODUCER-INVENTORY.json', inventory)
    print(json.dumps({'status': run.summary['status'], 'workflows': len(run.summary['workflows']),
        'exchanges': len(run.transcript), 'artifacts': len(run.summary['agent_artifacts']),
        'failures': run.summary['failures']}))
    return 0 if run.summary['status'] == 'passed' else 1


if __name__ == '__main__':
    sys.exit(main())
