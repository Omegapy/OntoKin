"""Place the straight duct using its accepted GLB and save the Agent/0.11 exchanges."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import tempfile

from agent_repair import PROJECT, PROTOCOL, session, write_json
from fit_placement import solve_placement
from tools.run_framed_loft_acceptance import schema_validators


def declaration(source, occurrence, part):
    # These example occurrences have flat settings and no nested declarations.
    pattern = rf'\bobject {occurrence} @ "{occurrence}": ducts\.{part} \{{[^{{}}]*\}}'
    block, = re.findall(pattern, source)
    return block


def replacement(source, pose):
    straight = declaration(source, 'straight', 'Straight')
    old, = re.findall(r'\bplacement = pose\([^;]+\);', straight)
    xyz, quat = pose['translation_m'], pose['rotation_wxyz']
    if len(xyz) != 3 or len(quat) != 4 or not all(math.isfinite(v) for v in (*xyz, *quat)):
        raise ValueError('solver returned an invalid placement')
    position = ', '.join(f'{v:.17g}[m]' for v in xyz)
    rotation = ', '.join(f'{v:.17g}' for v in quat)
    return old, f'placement = pose(world, vec3({position}), quat({rotation}));'


def replay(manifest, output, store):
    program, send, snapshot, _, export, edit, summary = session(manifest, output, store)
    created = send('defective-create', 'create', bundle=program.to_payload(),
                   expected_program_revision=None, requested_level='constructed')
    before = snapshot('defective', created['accepted_program_revision'])
    if before != program:
        raise ValueError('accepted defective source differs from the input manifest')
    _, defective = export('defective', before.program_revision)
    pose = solve_placement(defective)
    write_json(output / 'fit.json', pose)
    old, new = replacement(before.entry.text, pose)
    changed = edit('place-straight', before, old, new)
    after = snapshot('repaired', changed['accepted_program_revision'])
    if old == new or before.entry.text.replace(old, new) != after.entry.text:
        raise ValueError('accepted edit must change exactly one straight placement')
    elbow = declaration(before.entry.text, 'elbow', 'Elbow')
    if declaration(after.entry.text, 'elbow', 'Elbow') != elbow or after.modules != before.modules:
        raise ValueError('elbow declaration or imported module changed')
    _, repaired = export('repaired', after.program_revision)
    if repaired == defective:
        raise ValueError('placement edit yielded identical GLBs')
    validators = schema_validators(output)
    requests = sorted((output / 'exchanges').glob('*-request.json'))
    operations = []
    for path in requests:
        key = path.name.removesuffix('-request.json')
        req = json.loads(path.read_bytes())
        res = json.loads(path.with_name(key + '-response.json').read_bytes())
        validators['request.schema.json'].validate(req)
        validators['response.schema.json'].validate(res)
        for record in (req, res):
            if (record['request_id'], record['project_id'], record['schema_version']) != (key, PROJECT, PROTOCOL):
                raise ValueError(f'{key} exchange identity mismatch')
        operations.append(req['operation'])
    if operations.count('edit') != 1:
        raise ValueError('expected one source edit')
    summary['source'] = dict(defective_entry=before.entry.revision, repaired_entry=after.entry.revision,
                             unchanged_elbow_declaration='sha256:' + hashlib.sha256(elbow.encode()).hexdigest(),
                             unchanged_modules={m.source_id: m.revision for m in after.modules})
    summary['schema_validated_pairs'] = len(requests)
    write_json(output / 'summary.json', summary)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='duct-placement-') as store:
        replay(args.manifest, args.output, store)
