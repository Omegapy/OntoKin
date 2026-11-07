"""Replay the connected-duct edit and save the exact Agent exchanges and artifacts."""
import argparse
import base64
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from ontokin.bundle import load_file_manifest
from ontokin.framed_loft_agent import FramedLoftAgentService

PROTOCOL = 'ontokin.agent/0.11'
PROJECT = 'connected-duct'
OPTIONS = {'end': '1', 'fps': 2, 'helpers': False}
ALIGNED = "bore_shift = 0[m];"
OFFSET = "bore_shift = 0.25[m];"
INVALID = "bore_shift = 2[m];"


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def session(manifest, output, store):
    program = load_file_manifest(manifest)
    output.mkdir(parents=True, exist_ok=True)
    records = output / 'exchanges'
    records.mkdir(exist_ok=False)
    sequence = 0
    summary = {}

    def send(label, operation, *, invalid=False, **fields):
        nonlocal sequence
        sequence += 1
        key = f'{sequence:02d}-{label}'
        request = dict(schema_version=PROTOCOL, project_id=PROJECT,
                       request_id=key, operation=operation, **fields)
        write_json(records / (key + '-request.json'), request)
        # Reopen the on-disk store for each request, including after rejection.
        with closing(FramedLoftAgentService(str(store))) as service:
            response = service.handle(request)
        write_json(records / (key + '-response.json'), response)
        allowed = ('rejected', 'failed') if invalid else ('succeeded',)
        if response['status'] not in allowed:
            raise ValueError(f'{key} returned {response["status"]}; see exchanges')
        return response

    def snapshot(label, revision):
        with closing(FramedLoftAgentService(str(store))) as service:
            if service.accepted_revision(PROJECT) != revision:
                raise ValueError(f'{label}: accepted revision does not match the response')
            accepted = service.read_program(PROJECT, revision)
        if accepted.modules != program.modules:
            raise ValueError(f'{label}: the shared module changed')
        write_json(output / (label + '-bundle.json'), accepted.to_payload())
        (output / (label + '.ok')).write_bytes(accepted.entry.raw)
        return accepted

    def retrieve(label, exported):
        data = bytearray()
        while True:
            chunk = send(label + '-read', 'artifact', artifact_id=exported['artifact_id'],
                         offset=len(data), max_bytes=8192)['result']
            if any(chunk[k] != exported[k] for k in ('artifact_id', 'sha256', 'total_bytes', 'program_revision')):
                raise ValueError(f'{label}: artifact metadata changed')
            if chunk['offset'] != len(data):
                raise ValueError(f'{label}: chunk offset mismatch')
            decoded = base64.b64decode(chunk['data_base64'], validate=True)
            data.extend(decoded)
            if chunk['next_offset'] is None:
                break
            if not decoded or chunk['next_offset'] != len(data):
                raise ValueError(f'{label}: invalid chunk continuation')
        digest = 'sha256:' + hashlib.sha256(data).hexdigest()
        if digest != exported['sha256'] or len(data) != exported['total_bytes']:
            raise ValueError(f'{label}: artifact integrity failure')
        return bytes(data)

    def export(label, revision):
        descriptor = send(label + '-export', 'export', program_revision=revision,
                          destination='ontokin.glb/0.11', options=OPTIONS)['result']
        if descriptor['program_revision'] != revision:
            raise ValueError(f'{label}: export revision mismatch')
        data = retrieve(label, descriptor)
        (output / (label + '.glb')).write_bytes(data)
        summary[label] = {k: descriptor[k] for k in ('program_revision', 'sha256', 'total_bytes', 'artifact_id')}
        return descriptor, data

    def edit(label, accepted, old, new, invalid=False):
        original = old.encode('utf-8')
        if accepted.entry.raw.count(original) != 1:
            raise ValueError(f'{label}: expected exactly one editable source span')
        start = accepted.entry.raw.index(original)
        patch = dict(source_id='entry', source_revision=accepted.entry.revision,
                     element_id=['sources', 'entry'], start_byte=start,
                     end_byte=start + len(original), expected_text=old, replacement=new)
        return send(label, 'edit', invalid=invalid, expected_program_revision=accepted.program_revision,
                    requested_level='constructed', patches=[patch])

    return program, send, snapshot, retrieve, export, edit, summary


def replay(manifest, output, store):
    program, send, snapshot, retrieve, export, edit, summary = session(manifest, output, store)
    created = send('nominal-create', 'create', bundle=program.to_payload(),
                   expected_program_revision=None, requested_level='constructed')
    nominal = snapshot('nominal', created['accepted_program_revision'])
    if nominal != program:
        raise ValueError('accepted nominal source differs from input')
    descriptor, nominal_bytes = export('nominal', nominal.program_revision)
    rejected = edit('invalid', nominal, ALIGNED, INVALID, invalid=True)
    codes = [d['code'] for d in rejected['diagnostics']]
    if 'OKL-E-HOLES-CONTAINMENT' not in codes or rejected['accepted_program_revision'] != nominal.program_revision:
        raise ValueError('invalid source edit did not preserve the expected accepted revision')
    with closing(FramedLoftAgentService(str(store))) as service:
        if service.accepted_revision(PROJECT) != nominal.program_revision or service.read_program(PROJECT, nominal.program_revision) != nominal:
            raise ValueError('accepted source changed after rejection')
    if retrieve('after-rejection', descriptor) != nominal_bytes:
        raise ValueError('accepted artifact changed after rejection')
    summary['invalid_edit'] = dict(diagnostic_codes=codes,
                                   preserved_revision=nominal.program_revision, retrieved_sha256=descriptor['sha256'])
    defective = snapshot('defective', edit('misalign', nominal, ALIGNED, OFFSET)['accepted_program_revision'])
    _, defective_bytes = export('defective', defective.program_revision)
    if defective_bytes == nominal_bytes or defective.entry.text != nominal.entry.text.replace(ALIGNED, OFFSET):
        raise ValueError('defect did not produce the expected source and distinct artifact')
    repaired = snapshot('repaired', edit('repair', defective, OFFSET, ALIGNED)['accepted_program_revision'])
    _, repaired_bytes = export('repaired', repaired.program_revision)
    if repaired != nominal or repaired_bytes != nominal_bytes:
        raise ValueError('exact reversal did not restore original source and artifact')
    write_json(output / 'summary.json', summary)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='duct-repair-') as directory:
        replay(args.manifest, args.output, directory)
