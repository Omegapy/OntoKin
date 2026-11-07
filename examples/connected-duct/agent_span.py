"""Fit an editable straight between two signed ports through one Agent/0.11 edit."""
import argparse
import math
from pathlib import Path
import re
import tempfile

from agent_place import validate_exchanges
from agent_repair import session, write_json
from agent_select import declaration_bytes, occurrences, placement_patch, stationary_identities
from fit_placement import compose, rotate
from span_solver import solve
from ontokin.execution_budget import HostPolicy
from tools.verify_connected_duct import require


def span_patch(program, mapping, length):
    require(math.isfinite(length) and length > 0, 'Fitted straight length must be positive')
    block = declaration_bytes(program, mapping)
    matches = list(re.finditer(rb'\bspan\s*=\s*[^;{}]+;', block))
    require(len(matches) == 1, 'Expected one editable span in the moving declaration')
    match, = matches
    start = mapping['declaration']['start_byte'] + match.start()
    return dict(source_id='entry', source_revision=program.entry.revision,
                element_id=['sources', 'entry'], start_byte=start, end_byte=start + len(match[0]),
                expected_text=match[0].decode('utf-8'), replacement=f'span = {length:.17g}[m];')


def fit_patches(program, mapping, fit, control):
    pose = fit
    if control == 'wrong-end':
        # The example's straight begins at its local origin and extends along +Z.
        # Reverse it about its midpoint so the two unsigned openings still coincide.
        rotation = fit['rotation_wxyz']
        delta = rotate(rotation, (0, 0, fit['length_m']))
        pose = dict(translation_m=[a+b for a, b in zip(fit['translation_m'], delta)],
                    rotation_wxyz=compose(rotation, (0, 1, 0, 0)))
    patches = [placement_patch(program, mapping, pose)]
    if control != 'incorrect-length':
        patches.append(span_patch(program, mapping, fit['length_m']))
    return patches


def replay(manifest, output, store, selection, control=None):
    program, send, snapshot, _, export, _, summary = session(
        manifest, output, store, host_policy=HostPolicy(200000, 30000))
    write_json(output / 'selection.json', selection)
    created = send('defective-create', 'create', bundle=program.to_payload(),
                   expected_program_revision=None, requested_level='constructed')
    before = snapshot('defective', created['accepted_program_revision'])
    require(before == program, 'Accepted starting source differs from the input')
    _, defective = export('defective', before.program_revision)
    try:
        fit = solve(defective, **selection)
    except ValueError as exc:
        preserved = snapshot('after-rejection', before.program_revision)
        require(preserved == before, 'Rejected fit changed the accepted source')
        summary.update(outcome='fit-rejected', reason=str(exc), preserved_revision=before.program_revision,
                       schema_validated_pairs=validate_exchanges(output, edits=0))
        write_json(output / 'summary.json', summary)
        return summary

    write_json(output / 'fit.json', fit)
    moving = selection['moving_name']
    original = occurrences(defective)
    patches = fit_patches(before, original[moving], fit, control)
    changed = send('fit-span', 'edit', expected_program_revision=before.program_revision,
                   requested_level='constructed', patches=patches)
    after = snapshot('repaired', changed['accepted_program_revision'])
    expected = before.entry.raw
    for p in sorted(patches, key=lambda p: p['start_byte'], reverse=True):
        expected = expected[:p['start_byte']] + p['replacement'].encode('utf-8') + expected[p['end_byte']:]
    require(after.entry.raw == expected and before.modules == after.modules,
            'Accepted edit differs from the prescribed patches')
    _, repaired = export('repaired', after.program_revision)
    updated = occurrences(repaired)
    stationary = stationary_identities(before, original, moving)
    require(set(original) == set(updated) and original[moving]['element_id'] == updated[moving]['element_id']
            and original[moving]['definition'] == updated[moving]['definition']
            and stationary_identities(after, updated, moving) == stationary, 'An occurrence identity changed')
    summary.update(outcome='control-exported' if control else 'fitted', control=control,
                   source=dict(before=before.entry.revision, after=after.entry.revision,
                               unchanged_stationary=stationary,
                               unchanged_modules={m.source_id: m.revision for m in after.modules}),
                   edit_patch_count=len(patches), schema_validated_pairs=validate_exchanges(output, edits=1))
    write_json(output / 'summary.json', summary)
    return summary


def signed_port(value):
    occurrence, sep, region = value.rpartition('/')
    if not occurrence or not sep or not region:
        raise argparse.ArgumentTypeError('Use occurrence/region')
    return occurrence, region


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('output', type=Path)
    for field in ('upstream', 'inlet', 'outlet', 'downstream'):
        parser.add_argument('--' + field, required=True, type=signed_port, metavar='OCCURRENCE/REGION')
    parser.add_argument('--control', choices=('wrong-end', 'incorrect-length'),
                        help='Deliberately export a flawed fit in this isolated run')
    args = parser.parse_args()
    if args.inlet[0] != args.outlet[0]:
        parser.error('Inlet and outlet must name the same moving occurrence')
    selection = dict(source_name=args.upstream[0], source_region=args.upstream[1],
                     sink_name=args.downstream[0], sink_region=args.downstream[1],
                     moving_name=args.inlet[0], moving_bottom=args.inlet[1], moving_top=args.outlet[1])
    with tempfile.TemporaryDirectory(prefix='duct-span-') as store:
        result = replay(args.manifest, args.output, store, selection, args.control)
    if result['outcome'] == 'fit-rejected':
        parser.exit(2, result['reason'] + '\n')
