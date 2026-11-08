"""Fit a selected straight–elbow–straight chain in one guarded Agent edit."""
import argparse
from pathlib import Path
import tempfile

from agent_place import validate_exchanges
from agent_repair import session, write_json
from agent_select import occurrences, placement_patch
from agent_span import span_patch
from fit_placement import compose
from route_solver import solve
from ontokin.execution_budget import HostPolicy
from tools.verify_connected_duct import require


def route_patches(program, mappings, fit, chain, control):
    _, first, bend, second, _ = chain
    patches = []
    for name in (first, bend, second):
        pose = fit[name]
        if name == bend and control == 'wrong-turn':
            # Roll around the bend's local inlet axis, leaving its inlet center fixed.
            pose = dict(pose, rotation_wxyz=compose(pose['rotation_wxyz'], (0, 0, 0, 1)))
        patches.append(placement_patch(program, mappings[name], pose))
        if name != bend:
            length = fit[name]['length_m']
            if name == second and control == 'one-sided':
                length -= 1
            patches.append(span_patch(program, mappings[name], length))
    return patches


def replay(manifest, output, store, chain, control=None):
    program, send, snapshot, _, export, _, summary = session(
        manifest, output, store, host_policy=HostPolicy(300000, 30000))
    write_json(output / 'selection.json', list(chain))
    created = send('defective-create', 'create', bundle=program.to_payload(),
                   expected_program_revision=None, requested_level='constructed')
    before = snapshot('defective', created['accepted_program_revision'])
    require(before == program, 'Accepted input differs from the manifest')
    _, raw = export('defective', before.program_revision)
    try:
        fit = solve(raw, *chain)
    except ValueError as exc:
        require(snapshot('after-rejection', before.program_revision) == before,
                'Rejected route changed the accepted source')
        summary.update(outcome='fit-rejected', reason=str(exc), preserved_revision=before.program_revision,
                       edit_patch_count=0, schema_validated_pairs=validate_exchanges(output, edits=0))
    else:
        write_json(output / 'fit.json', fit)
        mappings = occurrences(raw)
        patches = route_patches(before, mappings, fit, chain, control)
        if control == 'rollback':
            # The final patch has a stale precondition. The four earlier valid patches
            # must never become visible, even after reopening the store.
            patches[-1]['expected_text'] = 'span = 9[m];'
            result = send('stale-route', 'edit', invalid=True, expected_program_revision=before.program_revision,
                          requested_level='constructed', patches=patches)
            require(result['accepted_program_revision'] == before.program_revision and
                    snapshot('after-rejection', before.program_revision) == before,
                    'Atomic edit rejection changed the accepted source')
            _, restored = export('after-rejection', before.program_revision)
            require(restored == raw, 'Atomic rejection changed the exported geometry')
            summary.update(outcome='edit-rejected', control=control, preserved_revision=before.program_revision,
                           attempted_patch_count=len(patches), schema_validated_pairs=validate_exchanges(output, edits=1))
            write_json(output / 'summary.json', summary)
            return summary
        result = send('fit-route', 'edit', expected_program_revision=before.program_revision,
                      requested_level='constructed', patches=patches)
        after = snapshot('repaired', result['accepted_program_revision'])
        expected = before.entry.raw
        for patch in sorted(patches, key=lambda p: p['start_byte'], reverse=True):
            start, end = patch['start_byte'], patch['end_byte']
            require(expected[start:end] == patch['expected_text'].encode(), 'Stale patch source range')
            expected = expected[:start] + patch['replacement'].encode() + expected[end:]
        require(after.entry.raw == expected and after.modules == before.modules,
                'Accepted source differs from the guarded field edits')
        _, repaired = export('repaired', after.program_revision)
        updated = occurrences(repaired)
        require(set(updated) == set(mappings) and all(
            updated[name][field] == record[field] for name, record in mappings.items()
            for field in ('element_id', 'definition')), 'Occurrence identity changed')
        summary.update(outcome='control-exported' if control else 'fitted', control=control,
                       edit_patch_count=len(patches), schema_validated_pairs=validate_exchanges(output, edits=1))
    write_json(output / 'summary.json', summary)
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--chain', nargs=5, required=True, metavar=('SOURCE','FIRST','BEND','SECOND','SINK'))
    parser.add_argument('--control', choices=('wrong-turn', 'one-sided', 'rollback'))
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='duct-route-') as store:
        summary = replay(args.manifest, args.output, store, args.chain, args.control)
    if summary['outcome'] == 'fit-rejected':
        parser.exit(2, summary['reason'] + '\n')
