#!/usr/bin/env python3
"""Verify prepared source/hash closure and independent finite analytic checks.

This checks proposal inputs. It neither executes nor implements reach semantics.
"""
from __future__ import annotations
import hashlib
import json
import math
from fractions import Fraction as Q
from pathlib import Path
import re
import sys
import tempfile

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE))
import author_fixtures


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def sha(data):
    return 'sha256:' + hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(path.read_text())


def safe_member(root, name):
    require(isinstance(name, str) and name and '\\' not in name, 'invalid member name')
    relative = Path(name)
    require(not relative.is_absolute() and '..' not in relative.parts, 'unsafe member path')
    path = root / relative
    require(path.resolve().is_relative_to(root.resolve()) and not path.is_symlink(), 'escaping member')
    require(path.is_file(), 'missing member: ' + name)
    require(path.stat().st_size <= 2 * 1024 * 1024, 'unexpectedly large prepared input')
    return path


def close(actual, expected, tolerance=1e-12):
    require(len(actual) == len(expected), 'vector arity')
    require(all(math.isfinite(a) and abs(a-b) <= tolerance for a,b in zip(actual, expected)),
            f'analytic mismatch: {actual!r} versus {expected!r}')


def sample(case, time, side='after'):
    target = Q(str(time))
    matches = [item for item in case['expected']['samples']
               if Q(int(item['time']['numerator']), int(item['time']['denominator'])) == target and item['side'] == side]
    require(len(matches) == 1, 'sample is not unique')
    return matches[0]


def verify():
    acceptance = read_json(HERE/'acceptance.json')
    inventory = read_json(HERE/'generated-members.json')
    require(acceptance['status'] == 'proposed_not_adopted', 'proposal status changed')
    require(acceptance['oracle_sha256'] == sha((HERE/'oracle.py').read_bytes()), 'oracle bytes changed')
    require(acceptance['author_script_sha256'] == sha((HERE/'author_fixtures.py').read_bytes()), 'author bytes changed')
    require(acceptance['dependency']['reconciliation_required_before_implementation'] is True, 'dependency must remain explicit')
    names = [member['path'] for member in inventory['members']]
    require(names == sorted(set(names)), 'member names not a sorted unique set')
    for member in inventory['members']:
        raw = safe_member(HERE, member['path']).read_bytes()
        require(len(raw) == member['bytes'] and sha(raw) == member['sha256'], 'member changed: ' + member['path'])
    cases = {case['id']: case for case in acceptance['source_cases']}
    require(len(cases) == 41 and acceptance['source_case_count'] == 41, 'source count')
    require(acceptance['positive_count'] == 26 and acceptance['negative_count'] == 15, 'kind counts')
    require(set(cases) == {f'P{i:02d}' for i in range(1,27)} | {f'N{i:02d}' for i in range(1,16)}, 'case IDs')
    require({path.relative_to(HERE).as_posix() for path in (HERE/'sources').glob('*.ok')} ==
            {case['entry_source'] for case in cases.values()}, 'unbound/stale source file')
    total_units = 0
    for identity, case in cases.items():
        require(case['expected']['source_evaluation_status'] == 'not_executed', 'prepared value relabeled executed')
        entry = safe_member(HERE, case['entry_source']).read_bytes()
        require(sha(entry) == case['source_sha256'], identity + ' entry hash')
        transport_raw = safe_member(HERE, case['file_manifest']).read_bytes()
        require(sha(transport_raw) == case['file_manifest_sha256'], identity + ' transport hash')
        transport = json.loads(transport_raw)
        require(transport['schema_version'] == 'ontokin.files/0.1', 'inherited file schema')
        require(transport['entry'] == {'filename':'reach-entry.ok','path':case['entry_source']}, 'entry transport')
        source_map = {'entry': entry}
        expected_units = [{'source_id':'entry','package_id':None,'version':None,
                           'filename':'reach-entry.ok','source_revision':sha(entry)}]
        for unit in transport['modules']:
            require(re.fullmatch(r'\d+\.\d+\.\d+', unit['version']) is not None, 'invalid inherited package version')
            raw = safe_member(HERE, unit['path']).read_bytes()
            source_id = 'package:' + unit['package_id'] + '@' + unit['version']
            require(source_id not in source_map, 'duplicate source ID')
            source_map[source_id] = raw
            expected_units.append({'source_id':source_id,'package_id':unit['package_id'],
                'version':unit['version'],'filename':unit['filename'],'source_revision':sha(raw)})
        expected_units.sort(key=lambda unit:unit['source_id'])
        require(expected_units == case['source_units'], identity + ' source-unit closure')
        available = {(unit['package_id'],unit['version']):unit['source_revision'] for unit in expected_units if unit['package_id']}
        for raw in source_map.values():
            for package, version, digest in re.findall(rb'from\s+"([^"]+)"\s+version\s+"([^"]+)"\s+digest\s+"([^"]+)"', raw):
                require(available.get((package.decode(), version.decode())) == digest.decode(), identity + ' import pin')
        manifest = {'schema_version':'ontokin.bundle/0.1','entry_source_id':'entry','units':expected_units}
        revision = sha(b'ontokin.bundle/0.1\0'+json.dumps(manifest,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())
        require(revision == case['program_revision'], identity + ' bundle revision')
        span = case['reach_action_span']
        require(span['source_id'] == 'entry' and span['source_revision'] == sha(entry), identity + ' span source')
        require(entry[span['start_byte']:span['end_byte']].decode() == span['text'], identity + ' UTF-8 span')
        require(span['text'].startswith('action reach @ "reach" = '), identity + ' span action')
        total_units += len(expected_units)
    with tempfile.TemporaryDirectory(prefix='ontokin-reach-preparation-') as temporary:
        rebuilt = Path(temporary)
        author_fixtures.build(rebuilt)
        require((rebuilt/'generated-members.json').read_bytes() == (HERE/'generated-members.json').read_bytes(), 'rebuild inventory differs')
        for name in names:
            require((rebuilt/name).read_bytes() == (HERE/name).read_bytes(), 'rebuild differs: ' + name)

    # These simple closed forms do not call the IK oracle; they cross-check its preparation.
    pi = math.pi
    require(cases['P01']['expected']['independent_solution']['resolved_joint_targets_rad'] == [0., pi/2], 'unit positive branch')
    require(cases['P02']['expected']['independent_solution']['resolved_joint_targets_rad'] == [pi/2, -pi/2], 'unit negative branch')
    require(cases['P03']['expected']['independent_solution']['resolved_joint_targets_rad'] == [0., pi/2], 'unequal right angle')
    for identity, elbow in [('P07',pi), ('P08',-pi)]:
        require(cases[identity]['expected']['independent_solution']['resolved_joint_targets_rad'] == [0., elbow], 'inner branch sign')
    require(cases['P09']['expected']['independent_solution']['resolved_joint_targets_rad'] == [-pi,pi/2], 'principal wrapping')
    close(sample(cases['P01'], 1)['tip_position_base_m'], [1+math.sqrt(.5),math.sqrt(.5),0])
    close(sample(cases['P02'], 1)['elbow_position_base_m'], [math.sqrt(.5),math.sqrt(.5),0])
    close(sample(cases['P04'], 2)['tip_position_world_m'], [1.,-1.,1.])
    expected_long = float((Q.from_float(3.)+Q.from_float(-pi))/2)
    require(sample(cases['P09'],1)['joint_coordinates_rad'][0] == expected_long, 'long unwrapped coordinate')
    require(sample(cases['P14'],.5)['claimed_coordinates'] == ['shoulder','elbow'], 'pause retains both claims')
    require(sample(cases['P14'],.5)['joint_rates_rad_per_s'] == [0.,0.], 'pause rates')
    require(sample(cases['P14'],1.5)['action_state'] == 'running', 'resume boundary')
    require(sample(cases['P15'],.5)['goal_outcome'] == 'interrupted', 'stopped goal')
    require(sample(cases['P15'],.5)['claimed_coordinates'] == [], 'stop releases both claims')

    # At P16 completion, q1=pi/6, q2=2pi/3, root angle=1/2 and base mount=(0,1,0).
    release = cases['P16']['expected']['release']
    incoming = release['incoming_state']
    c, s = math.cos(.5), math.sin(.5)
    local_v = [-pi/4-.5, -math.sqrt(3)*pi/6]
    closed_p = [1-2*s,2*c,0.]
    closed_v = [.5+c*local_v[0]-s*local_v[1],s*local_v[0]+c*local_v[1],0.]
    close(incoming['tip_position_world_m'], closed_p)
    close(incoming['tip_velocity_world_m_per_s'], closed_v)
    close(incoming['forearm_omega_world_rad_per_s'], [0.,0.,.25+5*pi/12])
    require(release['both_incoming_joint_rates_nonzero'] is True and abs(closed_v[1]) > .1, 'nontrivial release derivative')
    close(release['position_at_3_seconds_m'], [p+v+(1 if i==0 else 0) for i,(p,v) in enumerate(zip(closed_p,closed_v))])
    close(release['position_at_4_seconds_m'], [p+2*v+(3 if i==0 else 0) for i,(p,v) in enumerate(zip(closed_p,closed_v))])
    require(sample(cases['P16'],2)['joint_rates_rad_per_s'] == [0.,0.], 'completed outgoing rates')
    before = (HERE/cases['P13']['entry_source']).read_bytes()
    after = (HERE/cases['P20']['entry_source']).read_bytes()
    old = b'arms["first"].forearm_length = 1[m];'
    new = b'arms["first"].forearm_length = 1.5[m];'
    require(before.count(old) == 1 and before.replace(old,new) == after, 'repair must be one local source edit')
    require(len(cases['P20']['expected']['repair']['required_unchanged_paths']) == 13, 'four complete siblings plus rack')
    require(cases['P13']['source_units'][1:] == cases['P20']['source_units'][1:], 'repair changed a pinned library')
    for identity, count in [('P23',32),('N11',33),('P24',128),('N13',129)]:
        require(len(cases[identity]['expected']['reach_action_paths']) == count, identity+' named action source count')
    require(cases['P23']['expected']['peak_active_reaches'] == 32, 'max active bound')
    require(cases['P17']['expected']['full_horizon_failure']['time'] == {'numerator':'3','denominator':'1'}, 'future failure clock')
    require({key for key,value in cases.items() if value['held_out_before_implementation']} == {'P18','P19'}, 'held-outs')
    requirements = read_json(HERE/'requirements.json')
    require({r['id'] for r in requirements['requirements']} == {f'R{i:02d}' for i in range(1,10)}, 'requirement IDs')
    require(set(cases) <= {case for r in requirements['requirements'] for case in r['cases']}, 'unmapped source case')
    local_links = 0
    for document in [HERE.parent/'OK-LANG-006-reusable-planar-reach-actions.md', *sorted(HERE.glob('*.md'))]:
        for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)', document.read_text()):
            if '://' in target or target.startswith('#'):
                continue
            require((document.parent/target.split('#')[0]).is_file(), 'broken proposal link: '+target)
            local_links += 1
    return {'schema_version':'ontokin.proposed-reach-input-check/0.1','status':'passed',
            'proposal_status':acceptance['status'],'source_cases':len(cases),'source_units_across_cases':total_units,
            'generated_members':len(names),'generated_bytes':sum(member['bytes'] for member in inventory['members']),
            'generated_inventory_sha256':sha((HERE/'generated-members.json').read_bytes()),
            'byte_identical_reconstruction':True,'independent_simple_case_and_release_checks':True,
            'proposal_local_links_checked':local_links,
            'proposed_parser_or_runtime_executed':False,'agent_or_destination_executed':False}


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2, sort_keys=True, allow_nan=False))
