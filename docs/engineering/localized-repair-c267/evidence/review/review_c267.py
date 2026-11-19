#!/usr/bin/env python3
"""Independent C267 review: retained-control audit and multi-joint probes."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import platform
import subprocess
import sys
import traceback
import zipfile
from datetime import datetime, timezone
from pathlib import Path


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def pointer(document, value):
    for item in value.lstrip('/').split('/'):
        key = item.replace('~1', '/').replace('~0', '~')
        document = document[int(key)] if type(document) is list else document[key]
    return document


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--controls', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    root = args.repo.resolve()
    area = root / 'docs/engineering/localized-repair-c267'
    paths = [area / name for name in ('hinge_compare.py', 'comparison_control_fixtures.py',
             'test_hinge_compare.py', 'CONTROL-COVERAGE.md')]
    paths += [root / ('docs/engineering/' + name) for name in (
        'localized-repair-c266/hinge_binding.py', 'localized-repair-c266/binding_control_fixtures.py',
        'localized-repair-c265/source_hinges.py', 'localized-repair-c261/hinge_glb.py',
        'localized-repair-c257/ownership.py', 'localized-repair-c260/CONTRACT.md',
        'localized-repair-c260/CONTROL-PLAN.md', 'localized-repair-c260/FIELD-ORIGINS.md')]
    paths += [root / 'docs/workflow/tasks/C267' / name for name in ('REQUIREMENTS.md', 'PLAN.md')]
    paths.append(Path(__file__).resolve())
    identities = {p.relative_to(root).as_posix(): {'bytes': p.stat().st_size, 'sha256': digest(p.read_bytes())}
                  for p in paths}
    result = {'schema': 'ontokin.c267.independent-review/1', 'reviewer': '/root/reconcile',
              'started_at': datetime.now(timezone.utc).isoformat(),
              'command': [sys.executable, '-B', str(Path(__file__).resolve()), *sys.argv[1:]],
              'python': sys.version, 'executable': sys.executable,
              'executable_sha256': digest(Path(sys.executable).read_bytes()),
              'platform': platform.platform(), 'machine': platform.machine(),
              'observed_checkout_head': subprocess.run(['git', '-C', str(root), 'rev-parse', 'HEAD'],
                  capture_output=True, text=True, check=True).stdout.strip(),
              'implementation_published_at': '2d47c608a953dc0d2ffb09b67e0ce6f720b205eb',
              'input_code': identities, 'controls_evidence': str(args.controls.resolve()),
              'cases': [], 'findings': [], 'passed': False}
    inputs = {}
    try:
        retained = json.loads((args.controls / 'results.json').read_text())
        assert retained['passed'] and retained['inputCodeStableDuringRun']
        assert not retained['failures'] and not retained['errors'] and not retained['skipped']
        assert retained['testMethods'] == 25 and retained['apiCalls'] == 123
        assert retained['agreementCalls'] == 35 and retained['typedRefusals'] == 88
        for name, identity in retained['implementationAndControlInputs'].items():
            assert identities[name] == identity, name
        with zipfile.ZipFile(args.controls / 'inputs.zip') as archive:
            assert archive.testzip() is None
            assert len(archive.namelist()) == len(set(archive.namelist()))
            for name in archive.namelist():
                assert digest(archive.read(name)) == name.split('.')[0], name
            checked_witnesses = 0
            for case in retained['cases']:
                assert (case['expected'], case['outcome']) in (
                    ('agreement', 'agreement'), ('refusal', 'typed_refusal'))
                entries = list(case['sources'].values()) + [case['artifact']]
                for entry in entries:
                    if type(entry) is not dict or 'sha256' not in entry:
                        continue
                    name = entry['snapshot'].split('!', 1)[1]
                    data = archive.read(name)
                    assert len(data) == entry['bytes'] and digest(data) == entry['sha256']
                    checked_witnesses += 1
        for name in ('hinge_compare.py', 'comparison_control_fixtures.py', 'test_hinge_compare.py'):
            assert (args.controls / 'checked-code' / name).read_bytes() == (area / name).read_bytes()
        result['retained_control_audit'] = {'passed': True, 'methods': 25, 'calls': 123,
            'agreements': 35, 'typed_refusals': 88, 'input_byte_witnesses_verified': checked_witnesses,
            'results_sha256': digest((args.controls / 'results.json').read_bytes()),
            'inputs_zip_sha256': digest((args.controls / 'inputs.zip').read_bytes())}

        fixtures = load('c267_review_independent_recipes', area / 'comparison_control_fixtures.py')
        api = load('c267_review_candidate', area / 'hinge_compare.py')
        original = fixtures.synthetic(first_keys=('first.key', 'second-key'), second_keys=('third_key',))
        leaf = original.sources['hinges.ok']
        low, high = fixtures.base.block_span(leaf, 'public joint flex @ "flex"')
        block = leaf[low:high].decode()
        alternate = block.replace('joint flex @ "flex"', 'joint twist @ "twist.key-2"')
        alternate = alternate.replace('vec3(0, 0, 1)', 'vec3(-1, 0, 0)')
        alternate = alternate.replace('range(-45[deg], 45[deg])', 'range(-1[rad], 1[rad])')
        alternate = alternate.replace('initial = 0[rad]', 'initial = 0.25[rad]')
        fixture = fixtures.synthetic(first_keys=('first.key', 'second-key'), second_keys=('third_key',),
                                     edits=((block, block + '\n' + alternate),))
        for expected in list(fixture.joints.values()):
            extra = copy.deepcopy(expected)
            extra['id'][-1] = 'twist.key-2'
            extra['definitionId'][-1] = 'twist.key-2'
            extra['path'] = expected['path'][:-4] + 'twist'
            extra.update(name='twist', key='twist.key-2', axis=[-1, 0, 0], limits=[-1, 1], initial=0.25)
            fixture.joints[extra['path']] = extra
        fixture.doc['extras']['ontokin']['joints'] = fixtures.rows(fixture.joints)
        assert len(fixture.joints) == 6

        def run(label, item, refusal=False):
            raw = item.raw
            entry = {'label': label, 'expected': 'FIELD_MISMATCH' if refusal else 'agreement',
                     'source_hashes': {name: digest(value) for name, value in item.sources.items()},
                     'artifact_sha256': digest(raw), 'artifact_bytes': len(raw)}
            for name, value in item.sources.items():
                inputs[digest(value) + '.ok'] = value
            inputs[digest(raw) + '.glb'] = raw
            result['cases'].append(entry)
            try:
                observed = api.compare_hinges(item.sources, raw)
            except api.Fault as exc:
                entry.update(outcome='typed_refusal', code=exc.code, detail=exc.detail, pointer=exc.pointer)
                assert refusal and exc.code == 'FIELD_MISMATCH', entry
                assert exc.sourceHashes == entry['source_hashes']
                assert exc.artifactSha256 == digest(raw) and exc.artifactBytes == len(raw)
                assert not hasattr(exc, 'records')
                return
            assert not refusal, entry
            assert observed['hingeCount'] == 6 and observed['siteCount'] == 6
            assert len({tuple(row['definitionId']) for row in observed['records']}) == 2
            assert {row['path'] for row in observed['records']} == set(item.joints)
            document, _ = fixtures.base.decode_glb(raw)
            for row in observed['records']:
                expected = item.joints[row['path']]
                for key in ('id', 'definitionId', 'path', 'name', 'key', 'ownerId', 'ownerDefinitionId',
                            'axis', 'limits', 'initial'):
                    assert row['source'][key] == expected[key], (label, key)
                for key, value in row['artifact']['claims'].items():
                    assert pointer(document, row['artifact']['origins'][key]) == value
                assert row['ownerBinding']['id'] == expected['ownerId']
                assert row['source']['sourceCompatibilityVerified'] is True
                for order, key in (('parent', 'parentSite'), ('child', 'childSite')):
                    endpoint = row['endpoints'][order]
                    assert endpoint['source']['id'] == expected[key]['id']
                    assert endpoint['source']['definitionId'] == expected[key]['definitionId']
                    assert endpoint['objectBinding']['id'] == expected[key]['objectId']
                    assert endpoint['artifactPath'] == expected[key]['path']
                    assert pointer(document, endpoint['artifactOrigin']) == expected[key]['path']
                    assert endpoint['source']['compatibilityAuthority'] == 'source-only'
                    assert endpoint['source']['poseEvaluated'] is False
            for flag in ('historicalInputsBound', 'sitePosesEvaluated', 'executionAllowed',
                         'acceptedRevisionQualified', 'directSiteTableObserved', 'jointDefinitionOrSpanObserved'):
                assert observed[flag] is False
            entry.update(outcome='agreement', hinge_count=6, distinct_sites=6, distinct_joint_definitions=2)

        run('two joint definitions share each endpoint pair', fixture)
        reordered = fixture.copy()
        reordered.doc['extras']['ontokin']['joints'].reverse()
        reordered.doc['nodes'].reverse()
        run('two joint definitions with reordered rows and nodes', reordered)
        for change in ('remove_second_definition_occurrence', 'swap_ids_between_definitions',
                       'swap_paths_between_definitions', 'changed_second_initial', 'swap_owner_endpoint_pairs'):
            mutant = fixture.copy()
            joints = mutant.doc['extras']['ontokin']['joints']
            alternate_index = next(i for i, row in enumerate(joints) if row['element_id'][-1] == 'twist.key-2')
            if change == 'remove_second_definition_occurrence':
                joints.pop(alternate_index)
            elif change == 'swap_ids_between_definitions':
                joints[0]['element_id'], joints[alternate_index]['element_id'] = joints[alternate_index]['element_id'], joints[0]['element_id']
            elif change == 'swap_paths_between_definitions':
                joints[0]['path'], joints[alternate_index]['path'] = joints[alternate_index]['path'], joints[0]['path']
            elif change == 'changed_second_initial':
                joints[alternate_index]['initial'] = 0
            else:
                for key in ('parent_site', 'child_site'):
                    joints[0][key], joints[1][key] = joints[1][key], joints[0][key]
            run(change, mutant, refusal=True)
        result['passed'] = True
    except Exception as exc:
        result['findings'].append({'type': type(exc).__name__, 'detail': str(exc), 'traceback': traceback.format_exc()})
    result['code_stable_during_review'] = all(
        {'bytes': (root / path).stat().st_size, 'sha256': digest((root / path).read_bytes())} == identity
        for path, identity in identities.items())
    result['passed'] = result['passed'] and result['code_stable_during_review']
    result['completed_at'] = datetime.now(timezone.utc).isoformat()
    result['limits'] = ['Finite declaration agreement only; no historical admission API',
        'Retained control audit is not reported as reexecuting those 123 calls',
        'No native, model, source export, full source/glTF validity, physical or release qualification']
    (args.out / 'RESULTS.json').write_text(json.dumps(result, indent=2) + '\n')
    with zipfile.ZipFile(args.out / 'inputs.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, value in sorted(inputs.items()):
            archive.writestr(name, value)
    print(json.dumps({'passed': result['passed'], 'cases': len(result['cases']),
                      'findings': result['findings'], 'code_stable_during_review': result['code_stable_during_review']}))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
