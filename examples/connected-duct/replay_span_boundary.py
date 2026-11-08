"""Replay the frozen C169 span-limit scenes and independently verify the exported meshes."""
import argparse
from hashlib import sha256
from math import dist
from pathlib import Path
import re
from shutil import copyfile
import tempfile

from agent_offset import replay
from replay_inferred import EXAMPLE, audit_case, check, direct_export, load, write_json
from verify_inferred_duct_offset import verify_case


def number(value):
    return str(int(value)) if value.is_integer() else repr(value)


def fixture_files(directory, source, poses):
    directory.mkdir(parents=True)
    for name, pose in zip(('outbound', 'inbound'), poses, strict=True):
        position = ', '.join(number(float(x)) + '[m]' for x in pose['position_m'])
        rotation = ', '.join(number(float(x)) for x in pose['quaternion_wxyz'])
        pattern = rf'(object {name} @ "{name}": ducts.Elbow \{{\s*placement = )[^;]+'
        source, count = re.subn(pattern, rf'\g<1>pose(world, vec3({position}), quat({rotation}))', source)
        check(count == 1, f'{name}: expected exactly one fixed placement')
    for filename in ('parts-span.ok', 'offset-achievable.files.json'):
        copyfile(EXAMPLE / filename, directory / filename)
    (directory / 'offset-achievable.ok').write_text(source)
    return directory / 'offset-achievable.files.json'


def audit_lengths(case, chain, directory, limits):
    directions = load(directory / 'directions.json')
    selected, = [c for c in directions['candidates'] if c['feasible']]
    check(dist(selected['direction'], case['flow_axes'][2]) < 1e-8, 'Incorrect travel direction')
    measured = selected['lengths_m']
    fit = load(directory / 'fit.json')
    source_values = [float(x) for x in re.findall(r'\bspan = ([0-9.eE+-]+)\[m\];', (directory / 'repaired.ok').read_text())]
    position = chain[1::2].index(case['position'])
    check(abs(measured[position] - case['axis_translation_measurement_m']) < 1e-10, 'Wrong projected measurement')
    expected = [min(max(value, limits[0]), limits[1]) for value in measured]
    check(len(source_values) == 3 and source_values == expected, 'Unexpected emitted source spans')
    for i, name in enumerate(chain[1::2]):
        record = fit[name]
        check(record['length_m'] == expected[i], name + ': reported span differs from source')
        if measured[i] != expected[i]:
            check(record['measured_length_m'] == measured[i], name + ': missing boundary measurement')
    return dict(measured_m=measured, emitted_source_m=source_values)


def run(output):
    freeze = load(EXAMPLE / 'span-boundary-contract.json')
    for field in ('template', 'base_contract'):
        check(sha256((EXAMPLE / freeze[field]).read_bytes()).hexdigest() == freeze[field + '_sha256'], field + ' hash')
    source = (EXAMPLE / freeze['template']).read_text()
    spec = load(EXAMPLE / freeze['base_contract'])
    base = spec['cases']['positive']
    chain = base['chain']
    reports = []
    for label, case in freeze['cases'].items():
        manifest = fixture_files(output / 'sources' / label, source, case['fixed_poses'])
        directory = output / 'agent' / label
        with tempfile.TemporaryDirectory(prefix='span-boundary-') as store:
            summary = replay(manifest, directory, store, chain)
        fitted = case['expected'] == 'unique_fit'
        outcome = 'fitted' if fitted else 'fit-rejected'
        report = audit_case(directory, manifest.parent / freeze['template'], chain, outcome, directory)
        if fitted:
            report['lengths'] = audit_lengths(case, chain, directory, spec['straight_span_limits_m'])
            report['direct_export'] = direct_export(manifest, directory, summary)
            geometry_case = dict(base, joint_centers_m=case['joint_centers_m'], flow_axes=case['flow_axes'],
                                 straight_spans_m=case['authored_target_spans_m'])
            report['geometry'] = verify_case(label, (directory / 'defective.glb').read_bytes(),
                                             (directory / 'repaired.glb').read_bytes(), spec, geometry_case, manifest.parent)
        else:
            report['refusal'] = summary['reason']
            decisions = load(directory / 'directions.json')
            check(decisions['selected_direction'] is None and not any(c['feasible'] for c in decisions['candidates']),
                  label + ': unexpected feasible direction')
            intended, = [c for c in decisions['candidates'] if dist(c['direction'], case['flow_axes'][2]) < 1e-8]
            expected_reason = 'rim' if label == 'rim-roll' else 'Straight spans'
            check(expected_reason in intended['reason'], label + ': wrong refusal reason')
            report['candidate_refusals'] = [c['reason'] for c in decisions['candidates']]
        reports.append(report)
    write_json(output / 'span-boundary-results.json', dict(result='passed', cases=reports))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    run(parser.parse_args().output)
