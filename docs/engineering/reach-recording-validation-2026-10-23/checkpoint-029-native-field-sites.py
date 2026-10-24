"""Count prospective native field proofs in retained P09 data; run no product.

This is a static site inventory, not admission proof, implementation, measured
savings, independently certified source minima, or a successful full request.
The complete-inequality requirements come from the separately audited census.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import struct
import sys


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def fields(value):
    return int(value['numerator']), int(value['denominator'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--census', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    paths = [Path(__file__).resolve(), args.snapshot.resolve(), args.census.resolve()]
    inputs = {str(p): p.read_bytes() for p in paths}
    snapshot = json.loads(inputs[str(args.snapshot.resolve())])['snapshots'][0]
    census = json.loads(inputs[str(args.census.resolve())])
    assert census['status'] == 'passed'
    assert len(snapshot['groups']) == len(census['census']['groups']) == 12
    names = snapshot['numeric_keys']
    assert len(names) == 21
    rows, equality_counts = [], Counter()
    complete_names = {'unit_quaternion_difference_bound', 'ideal_rotation_bound_rad',
        'ideal_position_bound_m', 'total_rotation_bound_rad',
        'carrier_position_bound_m', 'total_position_bound_m'}
    all_bits = duplicate_bits = minimum_bits = minimum_prospective_bits = 0
    for group, modeled in zip(snapshot['groups'], census['census']['groups']):
        assert group['ordinal'] == modeled['ordinal']
        seen, duplicates = {}, []
        for name, raw in zip(names, group['key'], strict=True):
            assert raw['type'] in ('int', 'float')
            assert type(raw['value']).__name__ == raw['type']
            key = (raw['type'], struct.pack('>d', raw['value']).hex() if raw['type'] == 'float' else str(raw['value']))
            pair = fields(group['quantities'][name])
            original = Fraction(raw['value'])
            assert pair == (original.numerator, original.denominator)
            width = max(x.bit_length() for x in pair)
            all_bits = max(all_bits, width)
            if key in seen:
                earlier = seen[key]
                assert pair == fields(group['quantities'][earlier])
                duplicates.append({'field': name, 'earlier_completed_field': earlier,
                    'native_type': key[0], 'exact_input': key[1], 'max_fraction_field_bits': width})
                duplicate_bits = max(duplicate_bits, width)
            else:
                seen[key] = name
        equalities = []
        for check in modeled['algebra']['checks']:
            name = check['name']
            if name.startswith('source_minimum.'):
                kind = 'observed_source_minimum'
            elif name in complete_names:
                kind = 'complete_inequality_requirement'
            elif name in ('destination_numeric_position_bound_m', 'destination_numeric_rotation_bound_rad'):
                kind = 'destination_requirement'
            else:
                continue
            first, second = fields(check['actual']), fields(check['required'])
            if first != second:
                continue
            assert check['relation'] == '>=' and check['passed'] is True
            prospective = max(first[0].bit_length() + second[1].bit_length(),
                              second[0].bit_length() + first[1].bit_length())
            equalities.append({'name': name, 'kind': kind,
                'numerator': str(first[0]), 'denominator': str(first[1]),
                'original_prospective_comparison_bits': prospective})
            equality_counts[kind] += 1
            if kind == 'observed_source_minimum':
                minimum_bits = max(minimum_bits, *(x.bit_length() for x in first))
                minimum_prospective_bits = max(minimum_prospective_bits, prospective)
        rows.append({'group': group['ordinal'], 'reported_fields': len(names),
            'distinct_typed_inputs': len(seen), 'duplicate_decode_sites': duplicates,
            'fresh_equal_requirement_sites': equalities})
    duplicate_count = sum(len(row['duplicate_decode_sites']) for row in rows)
    equal_count = sum(equality_counts.values())
    assert duplicate_count == 78
    assert equality_counts == {'observed_source_minimum': 74,
        'complete_inequality_requirement': 20, 'destination_requirement': 2}
    deficit = census['census']['static_remaining_work']['conditional_reduction_needed_for_100000']
    assert deficit == 125
    overhead_allowance = 2 * len(rows)
    result = {'schema_version': 'ontokin.p09-native-field-site-inventory/0.1',
        'status': 'passed', 'created_at': datetime.now(timezone.utc).isoformat(),
        'command': [sys.executable, *sys.argv],
        'imports_ontokin': False, 'product_runtime_executed': False,
        'optimization_implemented': False, 'measured_savings': None,
        'runtime_admission_applicability_proved': False,
        'captured_source_minima_independently_certified': False,
        'complete_requirement_basis': 'Exact reported-field formulas in the independently audited census',
        'summary': {'group_count': len(rows), 'reported_fields': 21 * len(rows),
            'duplicate_decode_sites': duplicate_count,
            'fresh_equal_requirement_sites': equal_count,
            'equal_requirement_categories': dict(equality_counts),
            'gross_site_ceiling': duplicate_count + equal_count,
            'illustrative_admission_allowance': overhead_allowance,
            'conditional_net_ceiling_under_allowance': duplicate_count + equal_count - overhead_allowance,
            'conditional_request_deficit': deficit,
            'conditional_margin_under_allowance': duplicate_count + equal_count - overhead_allowance - deficit,
            'maximum_reported_fraction_field_bits': all_bits,
            'maximum_duplicate_fraction_field_bits': duplicate_bits,
            'maximum_equal_minimum_fraction_field_bits': minimum_bits,
            'maximum_equal_minimum_prospective_bits': minimum_prospective_bits},
        'groups': rows,
        'required_proof': [
            'Retain exact native input type and binary64 bits, including signed zero.',
            'Reuse only earlier completed decodes in the same 21-field group; copy fresh Fraction results.',
            'Pin all omitted dispatch paths, including math.isfinite and any field/bit readers.',
            'Keep original operand, output and prospective-product guards under current live limits.',
            'Keep each current required claim, threshold continuation flags, owner and receipt checks.',
            'Use ordinary fallback for foreign or modified callbacks, observers, dispatch or unsupported domains.',
            'Charge actual admission work; establish runtime eligibility and measured complete-request savings separately.'],
        'limitations': [
            'Numerical matches do not prove the proposed native admission predicate.',
            'The 24-operation allowance is an illustration, not measured or implemented overhead.',
            '125 is a conditional static deficit, not an observed completed request total.',
            'The retained GLB remains unvalidated; no new recording or release pass is claimed.'],
        'inputs': [{'path': name, 'bytes': len(raw), 'sha256': digest(raw),
                    'unchanged': Path(name).read_bytes() == raw} for name, raw in inputs.items()]}
    assert all(row['unchanged'] for row in result['inputs'])
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'status': result['status'], 'summary': result['summary']}))


if __name__ == '__main__':
    main()
