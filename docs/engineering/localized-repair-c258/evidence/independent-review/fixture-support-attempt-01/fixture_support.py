"""Independent C258 mutation fixtures; no candidate or product imports.

Rebinds changed original source maps by explicit byte-edit intervals, hashes and
the adopted canonical manifest formula. It does not obtain semantic expected
answers from the proposed reader. Tests explicitly choose changed follow rows.
"""
from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import json
import struct
import subprocess

BASE_REV = '9b9d06d99e55fa9cf4d42e74d07505e98840c2b1'
REPO = Path('/workspace/scratch/da3bfd223c61/OntoKin')
PROOF = 'docs/engineering/semantic-export-c210/evidence/proof/'


def original(name):
    return subprocess.check_output(['git', '-C', str(REPO), 'show', BASE_REV + ':' + PROOF + name])


def source_bundle(endpoint='before'):
    return {'main.ok': original(endpoint + '.main.ok'), 'hinges.ok': original('hinges.ok')}


def decode_glb(raw):
    magic, version, total = struct.unpack_from('<4sII', raw)
    assert magic == b'glTF' and version == 2 and total == len(raw)
    size, kind = struct.unpack_from('<I4s', raw, 12)
    assert kind == b'JSON'
    return json.loads(raw[20:20+size]), raw[20+size:]


def encode_glb(document, tail):
    data = json.dumps(document, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()
    data += b' ' * (-len(data) % 4)
    return struct.pack('<4sII', b'glTF', 2, 20 + len(data) + len(tail)) + \
        struct.pack('<I4s', len(data), b'JSON') + data + tail


def changed_artifact(raw, change):
    document, tail = decode_glb(raw)
    change(document)
    return encode_glb(document, tail)


@dataclass(frozen=True)
class Edit:
    start: int
    end: int
    replacement: bytes


def apply_edits(raw, edits):
    cursor = 0
    pieces = []
    for edit in sorted(edits, key=lambda x:x.start):
        assert cursor <= edit.start <= edit.end <= len(raw)
        pieces.extend((raw[cursor:edit.start], edit.replacement))
        cursor = edit.end
    pieces.append(raw[cursor:])
    return b''.join(pieces)


def map_boundary(offset, edits, *, end=False):
    delta = 0
    for edit in sorted(edits, key=lambda x:x.start):
        if offset <= edit.start:
            return offset + delta
        if offset < edit.end:
            return edit.start + delta + (len(edit.replacement) if end else 0)
        delta += len(edit.replacement) - (edit.end - edit.start)
    return offset + delta


def mutate_sources(changes, endpoint='before'):
    """changes = [(filename, unique original bytes/string, replacement), ...]."""
    old = source_bundle(endpoint)
    edits = {name: [] for name in old}
    for filename, needle, replacement in changes:
        needle = needle.encode() if isinstance(needle, str) else needle
        replacement = replacement.encode() if isinstance(replacement, str) else replacement
        assert old[filename].count(needle) == 1, (filename, needle)
        start = old[filename].index(needle)
        edits[filename].append(Edit(start, start + len(needle), replacement))
    new_hinges = apply_edits(old['hinges.ok'], edits['hinges.ok'])
    if new_hinges != old['hinges.ok']:
        old_pin = sha256(old['hinges.ok']).hexdigest().encode()
        assert old['main.ok'].count(old_pin) == 1
        start = old['main.ok'].index(old_pin)
        edits['main.ok'].append(Edit(start, start + len(old_pin), sha256(new_hinges).hexdigest().encode()))
    new = {name: apply_edits(data, edits[name]) for name, data in old.items()}
    return new, edits


def rebind_artifact(raw, new_sources, edits, endpoint='before'):
    """Change only source authority/span bindings; caller explicitly edits values.

    Source spans that contain a changed expression expand by its byte delta.
    No source-derived semantic observations are called or copied here.
    """
    old_sources = source_bundle(endpoint)
    doc, tail = decode_glb(raw)
    meta = doc['extras']['ontokin']
    old_program_revision = meta['program']['revision']
    hash_changes = {'sha256:' + sha256(old_sources[n]).hexdigest():
                    'sha256:' + sha256(new_sources[n]).hexdigest() for n in old_sources}

    def replace(value):
        if isinstance(value, dict):
            result = {key: replace(v) for key,v in value.items()}
            name = value.get('filename')
            if name in edits and 'start_byte' in value and 'end_byte' in value:
                result['start_byte'] = map_boundary(value['start_byte'], edits[name])
                result['end_byte'] = map_boundary(value['end_byte'], edits[name], end=True)
            return result
        if isinstance(value, list):
            return [replace(x) for x in value]
        if isinstance(value, str):
            return hash_changes.get(value, value)
        return value

    doc = replace(doc)
    manifest = doc['extras']['ontokin']['program']['manifest']
    canonical = json.dumps(manifest, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
    new_program_revision = 'sha256:' + sha256(canonical).hexdigest()

    def program_replace(value):
        if isinstance(value, dict):
            return {key: program_replace(v) for key,v in value.items()}
        if isinstance(value, list):
            return [program_replace(x) for x in value]
        return new_program_revision if value == old_program_revision else value

    doc = program_replace(doc)
    return encode_glb(doc, tail)


def follow_rows(document):
    return document['extras']['ontokin']['follows']


def finger_nodes(document):
    child_paths = {row['child_object'] for row in follow_rows(document)}
    return [node['extras']['ontokin'] for node in document['nodes']
            if node['extras']['ontokin']['path'] in child_paths]


def receipt(sources, artifact=None):
    result = {name: {'bytes': len(raw), 'sha256': sha256(raw).hexdigest()}
              for name,raw in sources.items()}
    if artifact is not None:
        result['artifact.glb'] = {'bytes': len(artifact), 'sha256': sha256(artifact).hexdigest()}
    return result


if __name__ == '__main__':
    raw = original('before.glb')
    doc, tail = decode_glb(raw)
    assert decode_glb(encode_glb(doc, tail)) == (doc, tail)
    canonical = json.dumps(doc['extras']['ontokin']['program']['manifest'], sort_keys=True,
                           separators=(',', ':'), ensure_ascii=False).encode()
    assert 'sha256:' + sha256(canonical).hexdigest() == doc['extras']['ontokin']['program']['revision']
    sources, edits = mutate_sources([])
    assert decode_glb(rebind_artifact(raw, sources, edits)) == (doc, tail)
    sources, edits = mutate_sources([('main.ok', 'parent_frame = self.frame;', 'parent_frame = world;')])
    rebound, tail2 = decode_glb(rebind_artifact(raw, sources, edits))
    assert tail == tail2
    assert follow_rows(rebound) == follow_rows(doc)
    assert rebound['extras']['ontokin']['program']['revision'] != doc['extras']['ontokin']['program']['revision']
    print('PASS: independent GLB round trip, original canonical manifest, and changed-source binding fixture.')
