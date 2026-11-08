"""Authenticate the five retained Agent runs against the editable fixtures and reconstruct every GLB."""
import argparse
import base64
from hashlib import sha256
import json
from pathlib import Path
import re


def check(condition, description):
    if not condition:
        raise ValueError(description)


def digest(raw):
    return 'sha256:' + sha256(raw).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def audit(root, example, case, *, offset=False):
    label = 'incompatible' if case == 'incompatible' else 'achievable'
    prefix = 'offset' if offset else 'route'
    fixture = example / f'{prefix}-{label}.ok'
    chain = (['outbound', 'lead', 'turn', 'bridge', 'rise', 'tail', 'inbound'] if offset else
             ['outbound', 'lead', 'turn', 'tail', 'inbound'])
    outcome = {'target': 'fitted', 'incompatible': 'fit-rejected', 'rollback': 'edit-rejected'}.get(case, 'control-exported')
    reason = '-0.5' if offset else 'skew'
    return audit_case(root / case, fixture, chain, outcome, root / 'target', reason)


def audit_case(directory, fixture, chain, outcome, successful_directory, rejection_contains=None):
    case = directory.name
    rejected = outcome == 'fit-rejected'
    rollback = outcome == 'edit-rejected'
    bundle = load(directory / 'defective-bundle.json')
    summary = load(directory / 'summary.json')
    control = case if outcome in ('edit-rejected', 'control-exported') else None
    check(summary['outcome'] == outcome and summary.get('control') == control, f'{case}: case outcome')
    module, = bundle['modules']
    check(bundle['entry'] == dict(filename=fixture.name, source=fixture.read_text()) and
          module == dict(filename='parts-span.ok', package_id='example.connected-duct-parts',
                         version='1.1.0', source=(fixture.parent / 'parts-span.ok').read_text()),
          f'{case}: frozen input')
    check(load(directory / 'selection.json') == chain, f'{case}: selected occurrence chain')

    exchanges = directory / 'exchanges'
    paths = sorted(exchanges.glob('*-request.json'))
    pairs = []
    for i, p in enumerate(paths, 1):
        key = p.name.removesuffix('-request.json')
        q, r = load(p), load(exchanges / (key + '-response.json'))
        check(key.startswith(f'{i:02d}-') and q['request_id'] == r['request_id'] == key and
              q['schema_version'] == r['schema_version'] == 'ontokin.agent/0.11' and
              q['project_id'] == r['project_id'] == 'connected-duct' and
              q['operation'] == r['operation'] and
              r['status'] == ('rejected' if rollback and q['operation'] == 'edit' else 'succeeded'), f'{case}/{key}: pair')
        pairs.append((q, r))
    check(len(list(exchanges.iterdir())) == 2*len(paths) and len(paths) == summary['schema_validated_pairs'],
          f'{case}: exchange inventory')
    i = 0
    rebuilt = []
    oldrev = None
    raw = fixture.read_bytes()
    producers = {}
    states = ['defective']
    if not rejected:
        states.append('after-rejection' if rollback else 'repaired')
    for state in states:
        q, r = pairs[i]
        if state == 'defective':
            check(q['operation'] == 'create' and q['bundle'] == bundle and q['expected_program_revision'] is None,
                  f'{case}: create')
        else:
            check(q['operation'] == 'edit' and q['expected_program_revision'] == oldrev and
                  q.get('module_changes', []) == [], f'{case}: guarded atomic transaction')
            patches = sorted(q['patches'], key=lambda p: p['start_byte'])
            fields = []
            for index, name in enumerate(chain[1:-1]):
                fields.append((name, 'placement'))
                if index % 2 == 0:
                    fields.append((name, 'span'))
            check(len(patches) == len(fields) == summary['attempted_patch_count' if rollback else 'edit_patch_count'], f'{case}: patch count')
            chunks, pos = [], 0
            for p, (name, field) in zip(patches, fields):
                region, = re.finditer(rb'object\s+\w+\s+@\s*"' + name.encode() +
                                      rb'"\s*:\s*ducts\.\w+\s*\{[^{}]*\}', raw)
                start, end = p['start_byte'], p['end_byte']
                pattern = field + r'\s*=\s*[^;{}]+;'
                check(region.start() <= start < end <= region.end() and pos <= start and
                      p['source_id'] == 'entry' and p['source_revision'] == digest(raw) and
                      p['element_id'] == ['sources','entry'] and
                      (raw[start:end] == p['expected_text'].encode()) == (not rollback or (name, field) != (chain[-2], 'span')) and
                      re.fullmatch(pattern, p['expected_text']) and re.fullmatch(pattern, p['replacement']),
                      f'{case}: {field} source range')
                chunks.extend([raw[pos:start], p['replacement'].encode()])
                pos = end
            if rollback:
                target_edit, = (successful_directory / 'exchanges').glob('*-fit-route-request.json')
                target_patches = load(target_edit)['patches']
                submitted = q['patches']
                check(submitted[-1] == patches[-1] and submitted[:-1] == target_patches[:-1] and
                      dict(submitted[-1], expected_text=target_patches[-1]['expected_text']) == target_patches[-1],
                      f'{case}: only the final submitted guard may differ from the successful edit')
                diagnostic, = r['diagnostics']
                check(diagnostic['code'] == 'OKL-E-REVISION' and diagnostic['phase'] == 'edit' and
                      diagnostic['primary']['start_byte'] == patches[-1]['start_byte'] and
                      r['accepted_program_revision'] == oldrev == summary['preserved_revision'] and
                      summary['outcome'] == 'edit-rejected', f'{case}: stale final patch')
            else:
                raw = b''.join(chunks + [raw[pos:]])
        accepted = load(directory / (state + '-bundle.json'))
        check(raw == (directory / (state + '.ok')).read_bytes() == accepted['entry']['source'].encode()
              and accepted['entry']['filename'] == fixture.name and accepted['modules'] == bundle['modules'],
              f'{case}/{state}: reconstructed source')
        rev = r['accepted_program_revision']
        q, r = pairs[i+1]
        export = r['result']
        blob = (directory / (state + '.glb')).read_bytes()
        descriptor = dict(sha256=digest(blob), program_revision=rev, total_bytes=len(blob),
                          artifact_id='artifact:' + sha256(blob).hexdigest())
        manifest = export['source_manifest']
        canonical = json.dumps(manifest, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()
        check(digest(b'ontokin.bundle/0.1\0' + canonical) == rev and manifest['entry_source_id'] == 'entry'
              and len(manifest['units']) == 2 and {unit['filename']:unit['source_revision'] for unit in manifest['units']} ==
              {fixture.name:digest(raw), 'parts-span.ok':digest(module['source'].encode())}, f'{case}/{state}: revisions')
        check(q['operation'] == 'export' and q['program_revision'] == r['accepted_program_revision'] == rev
              and q['destination'] == 'ontokin.glb/0.11' and q['options'] == dict(end='1', fps=2, helpers=False)
              and descriptor == summary[state] and all(export[k] == v for k, v in descriptor.items()),
              f'{case}/{state}: export')
        budget = r['execution_budget']
        limits = dict(max_operations=300000, max_elapsed_ms=30000)
        check(budget['effective'] == budget['source_request'] == budget['host_ceilings'] == limits and
              0 < budget['consumed_operations'] <= limits['max_operations'] and budget['status'] == 'succeeded',
              f'{case}/{state}: finite budget')
        key = producers.setdefault(descriptor['artifact_id'], q['request_id'])
        i += 2
        joined = bytearray()
        while len(joined) < len(blob):
            q, r = pairs[i]
            payload = r['result']
            check(q['operation'] == 'artifact' and r['accepted_program_revision'] == rev and
                  q['offset'] == payload['offset'] == len(joined) and q['artifact_id'] == descriptor['artifact_id'] and
                  all(payload[k] == v for k,v in descriptor.items()) and payload['producer_request_id'] == key,
                  f'{case}/{state}: read provenance')
            piece = base64.b64decode(payload['data_base64'], validate=True)
            check(0 < len(piece) <= q['max_bytes'], f'{case}/{state}: read size')
            joined.extend(piece)
            check(payload['next_offset'] == (len(joined) if len(joined) < len(blob) else None),
                  f'{case}/{state}: read continuation')
            i += 1
        check(joined == blob, f'{case}/{state}: reconstructed GLB')
        rebuilt.append(dict(state=state, sha256=descriptor['sha256'], operations=budget['consumed_operations']))
        oldrev = rev
    check(i == len(pairs), f'{case}: unexpected operation')
    if rejected:
        check(summary['outcome'] == 'fit-rejected' and summary['edit_patch_count'] == 0 and bool(summary['reason']) and
              (rejection_contains is None or rejection_contains in summary['reason'].lower()) and
              summary['preserved_revision'] == oldrev and
              (directory / 'after-rejection-bundle.json').read_bytes() == (directory / 'defective-bundle.json').read_bytes() and
              (directory / 'after-rejection.ok').read_bytes() == raw, f'{case}: rejected source identity')
    if rollback:
        check(summary['defective'] == summary['after-rejection'] and
              (directory / 'defective-bundle.json').read_bytes() ==
              (directory / 'after-rejection-bundle.json').read_bytes(), f'{case}: retained rollback identity')
    return dict(case=case, accepted_edits=int(not rejected and not rollback),
                rejected_edits=int(rollback), pairs=len(pairs), artifacts=rebuilt)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('agent_directory', type=Path)
    parser.add_argument('example_directory', type=Path)
    parser.add_argument('--offset', action='store_true', help='Check the C167 two-elbow route')
    args = parser.parse_args()
    controls = ('wrong-plane', 'interior-gap') if args.offset else ('wrong-turn', 'one-sided')
    results = [audit(args.agent_directory, args.example_directory, label, offset=args.offset)
               for label in ('target', 'incompatible', *controls, 'rollback')]
    print(json.dumps(dict(result='passed', cases=results), indent=2))
