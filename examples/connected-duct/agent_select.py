"""Fit an explicitly requested duct joint and edit its moving occurrence through Agent/0.11."""
import argparse
import hashlib
from pathlib import Path
import re
import tempfile

from agent_place import placement_text, validate_exchanges
from agent_repair import session, write_json
from fit_placement import SelectionError, solve_placement
from tools.verify_connected_duct import GLB, require


def declaration_bytes(program, mapping):
    span = mapping['declaration']
    source = program.entry
    require(span['source_id'] == 'entry' and span['filename'] == source.filename and
            span['source_revision'] == source.revision and
            0 <= span['start_byte'] < span['end_byte'] <= len(source.raw),
            'Occurrence has no matching accepted entry declaration')
    block = source.raw[span['start_byte']:span['end_byte']]
    name = re.escape(mapping['path'].encode('utf-8'))
    require(re.fullmatch(rb'object\s+\w+\s+@\s+"' + name + rb'":\s*ducts\.\w+\s*\{[^{}]*\}', block),
            'Occurrence declaration does not name the selected source object')
    return block


def placement_patch(program, mapping, pose):
    block = declaration_bytes(program, mapping)
    matches = list(re.finditer(rb'\bplacement\s*=\s*pose\([^;]+\);', block))
    require(len(matches) == 1, 'Expected one placement in selected source declaration')
    match, = matches
    start = mapping['declaration']['start_byte'] + match.start()
    return dict(source_id='entry', source_revision=program.entry.revision,
                element_id=['sources', 'entry'], start_byte=start, end_byte=start + len(match[0]),
                expected_text=match[0].decode('utf-8'), replacement=placement_text(pose))


def occurrences(raw):
    return GLB(raw, target='ontokin.glb/0.11').document['extras']['ontokin']['program']['occurrences']


def stationary_identities(program, mappings, moving):
    result = {}
    for path, record in mappings.items():
        if path != moving:
            block = declaration_bytes(program, record)
            result[path] = dict(element_id=record['element_id'], definition=record['definition'],
                                declaration_sha256=hashlib.sha256(block).hexdigest())
    return result


def replay(manifest, output, store, *, elbow, elbow_region, straight, straight_region):
    selection = dict(elbow=elbow, elbow_region=elbow_region, straight=straight, straight_region=straight_region)
    program, send, snapshot, _, export, _, summary = session(manifest, output, store)
    write_json(output / 'selection.json', selection)
    created = send('defective-create', 'create', bundle=program.to_payload(),
                   expected_program_revision=None, requested_level='constructed')
    before = snapshot('defective', created['accepted_program_revision'])
    require(before == program, 'Accepted defective source differs from the input')
    _, defective = export('defective', before.program_revision)
    try:
        pose = solve_placement(defective, **selection)
    except SelectionError as exc:
        preserved = snapshot('after-rejection', before.program_revision)
        require(preserved == before, 'Selection rejection changed accepted source')
        summary.update(outcome='selection-rejected', reason=str(exc), preserved_revision=before.program_revision,
                       schema_validated_pairs=validate_exchanges(output, edits=0))
        write_json(output / 'summary.json', summary)
        return summary

    write_json(output / 'fit.json', pose)
    mappings = occurrences(defective)
    patch = placement_patch(before, mappings[straight], pose)
    changed = send('place-selected', 'edit', expected_program_revision=before.program_revision,
                   requested_level='constructed', patches=[patch])
    after = snapshot('repaired', changed['accepted_program_revision'])
    old = before.entry.raw
    require(after.entry.raw == old[:patch['start_byte']] + patch['replacement'].encode() + old[patch['end_byte']:]
            and after.entry.raw != old, 'Expected one change at the selected placement')
    _, repaired = export('repaired', after.program_revision)
    original = stationary_identities(before, mappings, straight)
    updated = occurrences(repaired)
    require(set(mappings) == set(updated) and mappings[straight]['element_id'] == updated[straight]['element_id']
            and mappings[straight]['definition'] == updated[straight]['definition']
            and stationary_identities(after, updated, straight) == original, 'An occurrence identity changed')
    summary.update(outcome='placed', source=dict(defective_entry=before.entry.revision,
                   repaired_entry=after.entry.revision, unchanged_stationary=original,
                   unchanged_modules={m.source_id: m.revision for m in after.modules}),
                   schema_validated_pairs=validate_exchanges(output, edits=1))
    write_json(output / 'summary.json', summary)
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('output', type=Path)
    for field in ('elbow', 'elbow-region', 'straight', 'straight-region'):
        parser.add_argument('--' + field, required=True)
    args = vars(parser.parse_args())
    with tempfile.TemporaryDirectory(prefix='duct-selection-') as store:
        result = replay(store=store, **args)
    if result['outcome'] != 'placed':
        parser.exit(2, result['reason'] + '\n')
