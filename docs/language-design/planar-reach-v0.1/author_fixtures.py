#!/usr/bin/env python3
"""Prepare complete proposed source and independent expectations, never runtime output."""
from __future__ import annotations
import argparse
import copy
from fractions import Fraction as Q
import hashlib
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import oracle

BASE = '06cf8206a8e7205f1b5f87c37c3c12dff0f65b9a'
VERSION = '0.1.0'
PROPOSAL_VERSION = '0.1.0-draft.1'
PROFILE = 'planar-reach-0.1'


def sha(raw):
    return 'sha256:' + hashlib.sha256(raw).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + '\n')


def scalar(value):
    return format(float(value), '.17g')


def xyz(values):
    return ', '.join(scalar(value) + '[m]' for value in values)


def canonical_clock(value):
    q = Q(str(value))
    return {'numerator': str(q.numerator), 'denominator': str(q.denominator)}


def specimens():
    rows = [
        dict(id='P01', name='bench-positive', family='R01'),
        dict(id='P02', name='bench-negative-branch', family='R02', branch='negative'),
        dict(id='P03', name='unequal-links', family='R02', lengths=[2, 1], target=[2, 1, 0]),
        dict(id='P04', name='rotated-base', family='R04', base_translation=[3, -2, 1], base_angle_deg=90),
        dict(id='P05', name='moving-base', family='R06', root_move=True, root_spin=True),
        dict(id='P06', name='outer-boundary', family='R03', target=[2, 0, 0]),
        dict(id='P07', name='inner-boundary-positive', family='R03', lengths=[2, 1], target=[1, 0, 0]),
        dict(id='P08', name='inner-boundary-negative', family='R03', lengths=[2, 1], target=[1, 0, 0], branch='negative'),
        dict(id='P09', name='principal-shoulder-wrap', family='R03', target=[-1, -1, 0], initial=[3, 0]),
        dict(id='P10', name='closed-elbow-limit', family='R03', elbow_high_deg=90),
        dict(id='P11', name='complete-segmented-character', family='R06', asset='character', lengths=[.75, .5], target=[.75, .5, 0]),
        dict(id='P12', name='keyed-one', family='R06', asset='rack', count=1),
        dict(id='P13', name='keyed-five', family='R06', asset='rack', count=5),
        dict(id='P14', name='pause-resume', family='R07', lifecycle='pause', horizon=4),
        dict(id='P15', name='stop-before-goal', family='R07', lifecycle='stop'),
        dict(id='P16', name='incoming-release-and-force', family='R07', release=True, horizon=4,
             target=[0, 1, 0], root_move=True, root_spin=True),
        dict(id='P17', name='valid-prefix-before-failed-goal', family='R07', future_bad_goal=True, horizon=4, request_horizon=2),
        dict(id='P18', name='held-out-oblique', family='R02', lengths=[.7, 1.3], target=[.45, 1.1, 0], held_out=True),
        dict(id='P19', name='held-out-unequal', family='R02', lengths=[1.75, .625], target=[1.8, .45, 0], branch='negative', held_out=True),
        dict(id='P20', name='scoped-length-repair', family='R08', asset='rack', count=5,
             lengths=[1, 1.5], repair_of='P13'),
        dict(id='P21', name='minimum-link-lengths', family='R03', lengths=[.125, .125], target=[.125, .125, 0]),
        dict(id='P22', name='maximum-link-and-target-lengths', family='R03', lengths=[4, 4], target=[8, 0, 0]),
        dict(id='P23', name='maximum-chain-count', family='R09', asset='rack', count=32, all_chains=True),
        dict(id='P24', name='maximum-named-action-count', family='R09', action_count=128),
        dict(id='P25', name='minimum-duration', family='R03', duration=1/1024),
        dict(id='P26', name='maximum-duration', family='R03', duration=60, horizon=60),
        dict(id='N01', name='outside-outer-boundary', family='R03', target=[math.nextafter(2., math.inf), 0, 0], failure='reach_unreachable'),
        dict(id='N02', name='inside-inner-boundary', family='R03', lengths=[2, 1], target=[math.nextafter(1., 0.), 0, 0], failure='reach_unreachable'),
        dict(id='N03', name='singular-origin', family='R03', target=[0, 0, 0], failure='reach_singular'),
        dict(id='N04', name='out-of-plane', family='R04', target=[1, 1, .125], failure='reach_frame'),
        dict(id='N05', name='different-target-frame', family='R04', wrong_frame=True, failure='reach_frame'),
        dict(id='N06', name='selected-branch-limit', family='R05', elbow_high_deg=60, failure='reach_limit'),
        dict(id='N07', name='length-one-over', family='R05', lengths=[math.nextafter(4., math.inf), 1], failure='reach_domain'),
        dict(id='N08', name='branch-string-is-not-enum', family='R05', wrong_branch_type=True, failure='reach_type'),
        dict(id='N09', name='partial-claim-conflict', family='R07', conflict=True, failure='reach_claim_conflict'),
        dict(id='N10', name='wrong-end-site', family='R05', wrong_tip=True, failure='reach_chain'),
        dict(id='N11', name='chain-count-one-over', family='R09', asset='rack', count=33, all_chains=True, failure='reach_resource'),
        dict(id='N12', name='duration-below-minimum', family='R05', duration=math.nextafter(1/1024, 0.), failure='reach_domain'),
        dict(id='N13', name='named-action-count-one-over', family='R09', action_count=129, failure='reach_resource'),
        dict(id='N14', name='duration-above-maximum', family='R05', duration=math.nextafter(60., math.inf), horizon=61, failure='reach_domain'),
        dict(id='N15', name='nonparallel-elbow-axis', family='R05', wrong_axis=True, failure='reach_chain'),
    ]
    for row in rows:
        row.setdefault('asset', 'bench')
        row.setdefault('lengths', [1, 1])
        row.setdefault('target', [1, 1, 0])
        row.setdefault('branch', 'positive')
        row.setdefault('initial', [0, 0])
        row.setdefault('duration', 2)
        row.setdefault('horizon', 3)
        row.setdefault('request_horizon', row['horizon'])
        row.setdefault('base_translation', [0, 0, 0])
        row.setdefault('base_angle_deg', 0)
    return rows


def source_for(row, pins):
    header = f'''ontokin "0.6";
module ReachFixture @ "planar-reach-fixture";
profile "planar-reach-0.1";

// Proposed source. This profile and reach_planar are not implemented yet.
import assets @ "assets" from "proposal.reach-assets" version "{VERSION}"
    digest "{pins['assets']}";
import shapes @ "shapes" from "proposal.reach-exterior" version "{VERSION}"
    digest "{pins['exterior']}";

scene Demo @ "demo" {{
    duration = {scalar(row['horizon'])}[s];
    gravity = vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2]);
'''
    asset = row['asset']
    if asset == 'bench':
        body = f'''    object rig @ "rig": assets.BenchArm {{
        upper_length = {scalar(row['lengths'][0])}[m];
        forearm_length = {scalar(row['lengths'][1])}[m];
        arm.shoulder_initial = {scalar(row['initial'][0])}[rad];
        arm.elbow_high = {scalar(row.get('elbow_high_deg', 180))}[deg];
        placement = pose(world, vec3({xyz(row['base_translation'])}),
                         axis_angle(vec3(0, 0, 1), {scalar(row['base_angle_deg'])}[deg]));
    }}
'''
        arm, offset = 'rig.arm', [0, 1, 0]
        if row.get('wrong_axis'):
            body = body.replace('        placement =', '        arm.elbow_axis = vec3(0, 1, 0);\n        placement =')
        objects = ['rig', 'rig.column', 'rig.arm', 'rig.arm.upper', 'rig.arm.forearm', 'rig.tool']
        visible = ['rig', 'rig.column', 'rig.arm.upper', 'rig.arm.forearm', 'rig.tool']
    elif asset == 'character':
        body = '''    object rig @ "rig": assets.SegmentedCharacter {
        placement = pose(world, vec3(0[m], 1.25[m], 0[m]), quat(1, 0, 0, 0));
    }
'''
        arm, offset = 'rig.arms["left"]', [-.35, 2., 0]
        objects = ['rig', 'rig.head'] + [f'rig.head.eyes["{key}"]' for key in ('left', 'right', 'brow')]
        for collection, keys in (('arms', ('left', 'right')), ('legs', ('left', 'middle', 'right'))):
            for key in keys:
                path = f'rig.{collection}["{key}"]'
                objects.extend([path, path + '.upper', path + '.forearm'])
        visible = [path for path in objects if path == 'rig' or path == 'rig.head' or '.eyes[' in path or path.endswith(('.upper', '.forearm'))]
    else:
        keys = ['first'] + [f'part-{index:02d}' for index in range(1, row['count'])]
        entries = ',\n'.join(f'            "{key}": vec3(0[m], {scalar(index * .25)}[m], 0[m])' for index, key in enumerate(keys))
        body = f'''    object rig @ "rig": assets.ArmRack {{
        mounts = keyed<Vec3<Length>> {{
{entries}
        }};
        arms["first"].forearm_length = {scalar(row['lengths'][1])}[m];
    }}
'''
        arm, offset = 'rig.arms["first"]', [0, 0, 0]
        objects = ['rig']
        for key in keys:
            path = f'rig.arms["{key}"]'
            objects.extend([path, path + '.upper', path + '.forearm'])
        visible = [path for path in objects if path == 'rig' or path.endswith(('.upper', '.forearm'))]
    frame = 'world' if row.get('wrong_frame') else arm + '.reach_frame'
    branch = '"positive"' if row.get('wrong_branch_type') else 'elbow_' + row['branch']
    target = f'point({frame}, {xyz(row["target"])})'
    expression = (f'reach_planar({arm}.shoulder, {arm}.elbow, {arm}.upper.tip, {target}, {scalar(row["duration"])}[s], {branch})'
                  if row.get('wrong_tip') else f'{arm}.reach_to({target}, {scalar(row["duration"])}[s], {branch})')
    body += f'    action reach @ "reach" = {expression};\n'
    start = []
    action_paths = ['reach']
    if row.get('all_chains'):
        for index, key in enumerate(keys[1:], 1):
            other_arm = f'rig.arms["{key}"]'
            action = f'reach_{index:02d}'
            body += f'    action {action} @ "reach-{index:02d}" = {other_arm}.reach_to(point({other_arm}.reach_frame, 1[m], 1[m], 0[m]), 2[s], elbow_positive);\n'
            start.append(f'start {action};')
            action_paths.append(action)
    for index in range(1, row.get('action_count', 1)):
        action = f'pending_{index:03d}'
        body += f'    action {action} @ "pending-{index:03d}" = {expression};\n'
        action_paths.append(action)
    if row.get('root_move'):
        body += '    action travel @ "travel" = move(rig, vector(world, 0.5[m/s], 0[m/s], 0[m/s]), 3[s]);\n'
        start.append('start travel;')
    if row.get('root_spin'):
        body += '    action turn @ "turn" = spin(rig, vector(world, 0[rad/s], 0[rad/s], 0.25[rad/s]), 3[s]);\n'
        start.append('start turn;')
    if row.get('conflict'):
        body += f'    action occupied @ "occupied" = tween({arm}.elbow, 0[rad], 3[s]);\n'
        start.append('start occupied;')
    if asset == 'character':
        body += '''    action look @ "look" = rig.look_to(30[deg], 2[s]);
    action other_arm @ "other-arm" = rig.arms["right"].reach_to(
        point(rig.arms["right"].reach_frame, 0.75[m], -0.5[m], 0[m]), 2[s], elbow_negative);
'''
        start.extend(['start look;', 'start other_arm;'])
        action_paths.append('other_arm')
    if row.get('release'):
        body += f'''    object payload @ "payload": shapes.Payload {{}}
    joint grip @ "grip": grip {{
        parent = {arm}.forearm.tip;
        child = payload.origin;
    }}
'''
        objects.append('payload'); visible.append('payload')
    if row.get('future_bad_goal'):
        body += f'    action later @ "later" = {arm}.reach_to(point({arm}.reach_frame, 8[m], 8[m], 0[m]), 1[s], elbow_positive);\n'
        action_paths.append('later')
    start.append('start reach;')
    body += '    at 0[s] sequence { ' + ' '.join(start) + ' }\n'
    if row.get('lifecycle') == 'pause':
        body += '    at 0.5[s] sequence { pause reach; }\n    at 1.5[s] sequence { resume reach; }\n'
    if row.get('lifecycle') == 'stop':
        body += '    at 0.5[s] sequence { stop reach; }\n'
    if row.get('release'):
        body += '    at 2[s] sequence { release grip using incoming; force payload @ "released-push" using vector(world, 1[N], 0[N], 0[N]) for 1[s]; }\n'
    if row.get('future_bad_goal'):
        body += '    at 3[s] sequence { start later; }\n'
    body += '}\n'
    return header + body, {'tracked_arm': arm, 'base_offset_world_at_rest_m': offset,
                           'reach_action_paths': action_paths,
                           'active_reach_count': len(keys) if row.get('all_chains') else (2 if asset == 'character' else 1),
                           'expected_object_paths': sorted(objects), 'expected_visible_paths': sorted(visible)}


def expected_for(row, layout):
    limits = [[-oracle.P, oracle.P], [-oracle.P, float(Q.from_float(oracle.P) * Q(row.get('elbow_high_deg', 180), 180))]]
    # All angle limits in this initial corpus are exact integer fractions of a half-turn.
    result = {'intended_family': row['family'], 'tracked_arm': layout['tracked_arm'],
              'source_evaluation_status': 'not_executed', 'expected_object_paths': layout['expected_object_paths'],
              'expected_visible_paths': layout['expected_visible_paths'], 'source_tolerance_m': 1e-9,
              'numeric_reference_tolerance_rad': 2e-15, 'joint_target_rounding': 'exact_binary64_targets_required',
              'geometry_generated_from_source_required': True,
              'reach_action_paths': layout['reach_action_paths'], 'peak_active_reaches': layout['active_reach_count']}
    failure = row.get('failure')
    if failure:
        result.update(expected_status='rejected', reach_code=failure, accepted_source_preserved=True,
                      no_partial_joint_claims=True, no_successful_destination=True)
        if failure in ('reach_unreachable', 'reach_singular', 'reach_limit', 'reach_domain', 'reach_frame') and not row.get('wrong_frame') and 1/1024 <= row.get('duration', 2) <= 60:
            classified = oracle.solve(row['lengths'], row['target'], row['branch'], limits)
            if classified.get('reach_code') != failure:
                raise AssertionError((row['id'], classified, failure))
            result['independent_solution'] = classified
        result['failure_phase'] = ('admission' if failure in ('reach_unreachable', 'reach_singular', 'reach_limit', 'reach_claim_conflict')
                                   else 'construction_or_typed_action_construction')
        return result
    solution = oracle.solve(row['lengths'], row['target'], row['branch'], limits)
    if solution['status'] != 'resolved':
        raise AssertionError((row['id'], solution))
    result.update(expected_status='evaluated', independent_solution=solution, samples=[])
    completion = row['duration'] + (1 if row.get('lifecycle') == 'pause' else 0)
    times = sorted({0., .5, 1., 1.5, float(completion), float(row['request_horizon'])})
    times = [value for value in times if value <= row['request_horizon']]
    for time in times:
        for side in ('before', 'after'):
            elapsed = time
            if row.get('lifecycle') == 'pause':
                elapsed = min(time, .5) if time <= 1.5 else time - 1
            elif row.get('lifecycle') == 'stop':
                elapsed = min(time, .5)
            elapsed = min(elapsed, row['duration'])
            start = list(map(Q.from_float, map(float, row['initial'])))
            target = list(map(Q.from_float, solution['resolved_joint_targets_rad']))
            d = Q.from_float(float(row['duration']))
            u = Q.from_float(float(elapsed))
            coordinates = [float(a + (b-a) * u/d) for a, b in zip(start, target)]
            moving = ((time > 0 or side == 'after') and (time < completion or (time == completion and side == 'before')))
            if row.get('lifecycle') == 'pause' and (.5 < time < 1.5 or time == .5 and side == 'after' or time == 1.5 and side == 'before'):
                moving = False
            if row.get('lifecycle') == 'stop' and (time > .5 or time == .5 and side == 'after'):
                moving = False
            rates = [float((b-a)/d) if moving else 0. for a, b in zip(start, target)]
            root_elapsed = min(time, 3)
            root_angle = row['base_angle_deg'] * oracle.P / 180 + (.25 * root_elapsed if row.get('root_spin') else 0)
            c, s = math.cos(root_angle), math.sin(root_angle)
            offset = layout['base_offset_world_at_rest_m']
            rotated = [c*offset[0]-s*offset[1], s*offset[0]+c*offset[1], offset[2]]
            root_position = [row['base_translation'][0] + (.5 * root_elapsed if row.get('root_move') else 0), *row['base_translation'][1:]]
            base_position = [a+b for a,b in zip(root_position, rotated)]
            root_w = .25 if row.get('root_spin') and (time < 3 or time == 3 and side == 'before') and (time > 0 or side == 'after') else 0.
            base_v = [(.5 if row.get('root_move') and (time < 3 or time == 3 and side == 'before') and (time > 0 or side == 'after') else 0) - root_w*rotated[1], root_w*rotated[0], 0]
            posed = oracle.pose(row['lengths'], coordinates, rates, base_position, root_angle, base_v, root_w)
            state = 'pending' if time == 0 and side == 'before' else 'running'
            if row.get('lifecycle') == 'stop' and (time > .5 or time == .5 and side == 'after'):
                state = 'stopped'
            elif row.get('lifecycle') == 'pause' and (.5 < time < 1.5 or time == .5 and side == 'after' or time == 1.5 and side == 'before'):
                state = 'paused'
            elif time > completion or time == completion and side == 'after':
                state = 'completed'
            result['samples'].append({'time': canonical_clock(time), 'side': side, 'action_state': state,
                'goal_outcome': {'pending':'pending','running':'active','paused':'active','stopped':'interrupted','completed':'satisfied'}[state],
                'claimed_coordinates': ['shoulder','elbow'] if state in ('running','paused') else [],
                'resolved_targets_visible': state != 'pending',
                'current_goal_residual_m': None if state == 'pending' else math.dist(posed['tip_position_base_m'], row['target']),
                'joint_coordinates_rad': coordinates, 'joint_rates_rad_per_s': rates, **posed})
    if row.get('release'):
        incoming = next(s for s in result['samples'] if s['time'] == canonical_clock(2) and s['side'] == 'before')
        p0 = incoming['tip_position_world_m']
        v0 = incoming['tip_velocity_world_m_per_s']
        acceleration = [2., 0., 0.]
        p3 = [p + v + a/2 for p, v, a in zip(p0, v0, acceleration)]
        v3 = [v + a for v, a in zip(v0, acceleration)]
        omega = incoming['forearm_omega_world_rad_per_s']
        result['release'] = {'time': canonical_clock(2), 'incoming_state': incoming,
            'own_mass_kg': .5, 'world_force_n': [1, 0, 0], 'force_end': canonical_clock(3),
            'position_at_3_seconds_m': p3, 'velocity_at_3_seconds_m_per_s': v3,
            'position_at_4_seconds_m': [p+v for p,v in zip(p3, v3)],
            'velocity_at_4_seconds_m_per_s': v3, 'constant_free_omega_world_rad_per_s': omega,
            'orientation_at_release_wxyz': incoming['forearm_orientation_wxyz'],
            'free_orientation_rule': 'world Z rotation omega_z*(t-2) left-multiplied onto orientation_at_release_wxyz; normalize/sign under inherited rules',
            'both_incoming_joint_rates_nonzero': all(value != 0 for value in incoming['joint_rates_rad_per_s']),
            'outgoing_joint_rates_are_zero': True, 'physical_model': 'inherited_free_homogeneous_sphere'}
    if row.get('future_bad_goal'):
        result['full_horizon_failure'] = {'time': canonical_clock(3), 'reach_code': 'reach_unreachable',
                                         'last_valid_side': 'before', 'short_prefix_seconds': '2'}
    if row.get('asset') == 'character':
        result['other_goals'] = {'right_arm': oracle.solve([.75, .5], [.75, -.5, 0], 'negative'),
                                 'head_yaw_at_2_seconds_rad': oracle.P / 6,
                                 'three_legs_and_three_eyes_preserved': True,
                                 'locomotion_or_contact_claimed': False}
    if row.get('repair_of'):
        siblings = [path for path in layout['expected_object_paths'] if not path.startswith('rig.arms["first"]')]
        result['repair'] = {'before_case': row['repair_of'], 'changed_parameter': 'rig.arms["first"].forearm_length',
                            'old_text': 'forearm_length = 1[m];', 'new_text': 'forearm_length = 1.5[m];',
                            'entry_only': True, 'same_spatial_goal': True, 'same_pinned_library_bytes': True,
                            'required_unchanged_paths': siblings, 'stale_runs_and_artifacts_must_remain_old_revision': True}
    return result


def build(destination):
    destination.mkdir(parents=True, exist_ok=True)
    (destination/'libraries').mkdir(exist_ok=True)
    (destination/'sources').mkdir(exist_ok=True)
    exterior = (HERE/'libraries/reach-exterior.ok').read_bytes()
    (destination/'libraries/reach-exterior.ok').write_bytes(exterior)
    pins = {'exterior': sha(exterior)}
    parts = (HERE/'libraries/reach-parts.ok.in').read_text().replace('__EXTERIOR_DIGEST__', pins['exterior'])
    (destination/'libraries/reach-parts.ok').write_text(parts)
    pins['parts'] = sha(parts.encode())
    assets = (HERE/'libraries/reach-assets.ok.in').read_text().replace('__EXTERIOR_DIGEST__', pins['exterior']).replace('__PARTS_DIGEST__', pins['parts'])
    (destination/'libraries/reach-assets.ok').write_text(assets)
    pins['assets'] = sha(assets.encode())
    modules = [{'package_id':'proposal.reach-'+kind,'version':VERSION,'filename':'reach-'+kind+'.ok','path':'libraries/reach-'+kind+'.ok'}
               for kind in ('assets', 'exterior', 'parts')]
    cases = []
    for original in specimens():
        row = copy.deepcopy(original)
        source, layout = source_for(row, pins)
        filename = row['id'].lower()+'-'+row['name']+'.ok'
        relative = 'sources/'+filename
        (destination/relative).write_text(source)
        transport = {'schema_version':'ontokin.files/0.1','entry':{'filename':'reach-entry.ok','path':relative},'modules':modules}
        file_manifest = row['id'].lower()+'.files.json'
        write_json(destination/file_manifest, transport)
        units = [{'source_id':'entry','package_id':None,'version':None,'filename':'reach-entry.ok','source_revision':sha(source.encode())}]
        units += [{'source_id':'package:'+unit['package_id']+'@'+VERSION,'package_id':unit['package_id'],'version':VERSION,
                   'filename':unit['filename'],'source_revision':sha((destination/unit['path']).read_bytes())} for unit in modules]
        units.sort(key=lambda unit:unit['source_id'])
        manifest = {'schema_version':'ontokin.bundle/0.1','entry_source_id':'entry','units':units}
        revision = sha(b'ontokin.bundle/0.1\0'+json.dumps(manifest,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())
        expected = expected_for(row, layout)
        source_bytes = source.encode()
        action_start = source_bytes.index(b'action reach @')
        action_end = source_bytes.index(b';', action_start) + 1
        cases.append({'id':row['id'],'name':row['name'],'family':row['family'],'kind':'negative' if row.get('failure') else 'positive',
            'held_out_before_implementation':row.get('held_out',False),'specification':row,'file_manifest':file_manifest,
            'file_manifest_sha256':sha((destination/file_manifest).read_bytes()),'entry_source':relative,'source_sha256':sha(source_bytes),
            'source_units':units,'program_revision':revision,
            'reach_action_span':{'source_id':'entry','source_revision':sha(source_bytes),'start_byte':action_start,'end_byte':action_end,
                                 'text':source_bytes[action_start:action_end].decode()},'expected':expected})
    acceptance = {'schema_version':'ontokin.planar-reach-proposal-corpus/0.1','proposal':PROPOSAL_VERSION,'package_version':VERSION,'status':'proposed_not_adopted',
        'base_commit':BASE,'dependency':{'pull_request':17,'force_release_accepted':False,'reconciliation_required_before_implementation':True},
        'oracle_scope':'High-precision independently stated planar IK/FK and rigid-root transport. These are expected values, not parser/runtime/export results.',
        'oracle_sha256':sha((HERE/'oracle.py').read_bytes()),'author_script_sha256':sha(Path(__file__).read_bytes()),
        'positive_count':sum(case['kind']=='positive' for case in cases),'negative_count':sum(case['kind']=='negative' for case in cases),
        'source_case_count':len(cases),'source_cases':cases,
        'pending_before_adoption':['Independent peer review of semantics and complete source/expectation closure.',
            'Resolve draft diagnostic projection and exact transcendental rounding review.',
            'Review the conservative articulated-world sampling derivation.',
            'Add the final executable Agent/GLB engineering schemas and role mapping before implementation acceptance.',
            'Reconcile accepted force revision; publish a separate adoption record with exact source/member hashes.']}
    write_json(destination/'acceptance.json', acceptance)
    generated = ['acceptance.json', *['libraries/reach-'+kind+'.ok' for kind in ('assets','exterior','parts')]]
    generated += [case['entry_source'] for case in cases] + [case['file_manifest'] for case in cases]
    write_json(destination/'generated-members.json', {'schema_version':'ontokin.proposed-fixture-members/0.1','status':'expected_inputs_not_execution',
        'members':[{'path':name,'bytes':(destination/name).stat().st_size,'sha256':sha((destination/name).read_bytes())} for name in sorted(generated)]})
    return acceptance


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=HERE)
    args = parser.parse_args()
    acceptance = build(args.output_dir)
    print(json.dumps({key:acceptance[key] for key in ('status','positive_count','negative_count','source_case_count')}))
