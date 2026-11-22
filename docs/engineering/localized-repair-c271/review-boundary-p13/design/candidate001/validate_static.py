"""Check P13 documentary bytes and mappings only; no product imports or calls."""
from pathlib import Path
import argparse
import ast
from collections import Counter
import copy
from datetime import datetime, timezone
import hashlib
import json
import platform
import sys


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def file_matches(path, record):
    if not path.is_file() or path.is_symlink():
        return False
    raw = path.read_bytes()
    size = record.get('bytes', record.get('size_bytes'))
    return len(raw) == size and sha(raw) == record['sha256']


def delta(a, b, path=''):
    if type(a) is dict and type(b) is dict:
        rows = []
        for key in sorted(set(a) | set(b)):
            if key not in a or key not in b:
                rows.append({'path': path + '/' + key, 'key_presence_differs': True})
            else:
                rows.extend(delta(a[key], b[key], path + '/' + key))
        return rows
    return [] if a == b else [{'path': path, 'positive': a, 'negative': b}]


def at(value, dotted):
    for key in dotted.split('.'):
        value = value[key]
    return value


def neutral(value):
    result = copy.deepcopy(value)
    del result['variant_review']['completeness']
    return json.dumps(result, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    root = args.repo.resolve()
    candidate = Path(__file__).resolve().parent
    rows = []
    report = {
        'schema': 'ontokin.c271.p13-author-static-validation/1',
        'author': '/root/design_author',
        'started_at_utc': datetime.now(timezone.utc).isoformat(),
        'command_argv': [sys.executable, '-I', '-B', *sys.argv],
        'environment': {'python': sys.version, 'executable': sys.executable, 'platform': platform.platform()},
        'repository': str(root),
        'candidate': str(candidate),
        'checks': rows,
        'semantic_review': 'B04/B05/B08 require independent reviewer judgment; author structural checks do not complete that gate.',
        'product_imports': 0,
        'product_methods': 0,
        'target_starts': 0,
        'excluded': ['operational plan creation', 'policy implementation', 'production/tests/tools edits', 'H0/H1', 'runtime preparation or installation', 'Node/ldd', 'original seven', 'full routine', 'hosted/native/model work', 'main integration', 'parent closure'],
    }

    def check(name, result, detail=None):
        row = {'id': name, 'passed': bool(result)}
        if detail is not None:
            row['detail'] = detail
        rows.append(row)

    try:
        inputs = read(candidate / 'INPUTS.json')
        report['source_revision_from_bound_inputs'] = inputs['source_revision']
        paths = {key: root / record['path'] for key, record in inputs['files'].items()}
        mismatches = [key for key, record in inputs['files'].items() if not file_matches(paths[key], record)]
        check('input_byte_identities', not mismatches, {'checked': len(paths), 'mismatches': mismatches})
        frozen_pins = {
            'E07': 'dfb285f41a58a1f7254aaae4aa022f91afdc72fb7d5dad2f3d6b1e8257d14137',
            'E09': 'e7b505aa768d0656db6c4dfaf7541e796aefee7148878a6fdf380d6ab0b911de',
            'E10': 'ffae051f6da02526bd8b5b52313d004063f900fa84ebe779f24aeb0df59d72de',
            'E11': '85a0c7f2b1055f39328c42a3c95e405d474e67b6ba7e442eec4c271d018953a5',
            'E12': '0c2ef54a227e2e05a7eb1f71a4fedd934399aa27d98ec7a3845f93a4dbfbb612',
        }
        check('independently_retained_p11_p12_pins', all(inputs['files'][key]['sha256'] == value for key, value in frozen_pins.items()))
        controls_doc = read(candidate / 'BOUNDARY-CONTROLS.json')
        controls = {row['id']: row for row in controls_doc['controls']}
        check('finite_boundary_control_ids', list(controls) == ['B01', 'B02', 'B03', 'B04', 'B05', 'B06', 'B07', 'B08'] and len(controls_doc['controls']) == 8)
        positive, negative = read(paths['E10']), read(paths['E11'])
        evidence = read(candidate / 'SOURCE-EVIDENCE.json')
        diff = delta(positive, negative)
        check('B01_exact_sole_delta', diff == controls['B01']['expected']['differences'] == evidence['exact_case_differences'])
        norm_p, norm_n = neutral(positive), neutral(negative)
        expected = controls['B02']['expected']
        check('B02_review_neutral_equality', norm_p == norm_n and len(norm_p) == expected['bytes'] and sha(norm_p) == expected['sha256'], {'bytes': len(norm_p), 'sha256': sha(norm_p), 'operational_document_created': False})
        check('B03_equal_binding_observations', all(at(positive, field) == at(negative, field) for field in controls['B03']['expected']['equal_fields']))

        production = paths['E12'].read_text()
        tree = ast.parse(production)
        resolution = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == '_check_resolution')
        review_uses = sorted((node.lineno, type(node.ctx).__name__) for node in ast.walk(resolution) if isinstance(node, ast.Name) and node.id == 'review')
        excerpt = '\n'.join(production.splitlines()[resolution.lineno - 1:resolution.lineno + 5]) + '\n'
        check('B04_rationale_source_statement_identity', excerpt == evidence['rationale_boundary']['excerpt'] == read(paths['E13'])['excerpt'], {'function_start': resolution.lineno, 'review_variable_occurrences': review_uses})
        check('B04_rationale_variable_uses', review_uses == [(resolution.lineno + 3, 'Store'), (resolution.lineno + 4, 'Load'), (resolution.lineno + 4, 'Load')])
        original_decision = paths['E04'].read_text()
        projection = read(paths['E17'])
        check('B04_four_field_operational_boundary', projection['operational_keys'] == controls['B04']['expected']['variant_keys'] == evidence['proposed_operational_variant_keys'] and 'The separate variant document has exactly `schema, loader, source_review, suffixes`.' in original_decision and 'No field in these objects constitutes approval.' in original_decision)

        external_binding = read(paths['E18'])
        actual_absent = (
            positive['operational'] is False and negative['operational'] is False
            and positive['schema'] == negative['schema'] == 'ontokin.c271.p11-portable-rule-context/1'
            and external_binding['actual_plan_bytes_supplied'] is False
            and external_binding['actual_external_expected_digest_supplied'] is False
            and all(projection[key][field]['actual_descriptor_supplied'] is False for key in ('P01', 'N57') for field in ('loader', 'source_review'))
        )
        check('B05_supplied_contexts_lack_actual_evidence', actual_absent, {'scope': 'These supplied synthetic inputs only; no inference about an uninspected actual host.'})
        check('B05_no_label_based_positive_review', all(controls['B05']['expected'][key] == evidence['actual_source_review_from_supplied_contexts'][key] == 'not_established_by_supplied_inputs' for key in ('P01_nonselecting_base', 'N57_source_variant_unknown')) and controls['B05']['expected']['runtime_outcome'] is None)

        fixture, oracle, original_manifest = read(paths['E08']), read(paths['E07']), read(paths['E09'])
        old_base = paths['E09'].parent
        fixture_failures = [row['path'] for row in fixture['files'] if not file_matches(old_base / row['path'], row)]
        check('B06_all_original_fixture_bytes', len(fixture['files']) == 131 and not fixture_failures, {'checked': len(fixture['files']), 'mismatches': fixture_failures, 'modes': 'Recorded original mode strings preserved; no materialization or chmod.'})
        payload_failures, payload_external, payload_matches = [], [], 0
        external = inputs['external_historical_payload']
        for record in original_manifest['payload']:
            path = old_base / record['path']
            if not path.exists() and record['path'] == 'REVISION-004.diff':
                payload_external.append(record)
            elif file_matches(path, record):
                payload_matches += 1
            else:
                payload_failures.append(record['path'])
        check('B06_available_original_candidate_payloads', len(original_manifest['payload']) == 146 and payload_matches == 145 and not payload_failures, {'matches': payload_matches, 'mismatches': payload_failures})
        check('B06_external_historical_payload_identity', len(payload_external) == 1 and payload_external[0]['sha256'] == external['sha256'] and payload_external[0]['size_bytes'] == external['bytes'] and external['source_kind'] == 'exact_external_prior_package_member; absent from Git tree', {'author_reverified_archive_member_bytes': False, 'external': external})
        support_failures = [row['path'] for row in original_manifest['supporting_files'] if not file_matches(old_base / row['path'], row)]
        check('B06_original_supporting_bytes', len(original_manifest['supporting_files']) == 29 and not support_failures, {'checked': len(original_manifest['supporting_files']), 'mismatches': support_failures})

        mapping = read(candidate / 'CONTROL-MAPPING.json')
        mapped = {row['id']: row for row in mapping['cases']}
        old_cases = {row['id']: row for row in fixture['cases']}
        check('B06_exact_total_case_ids', len(mapping['cases']) == len(mapped) == len(old_cases) == len(oracle['cases']) == 97 and set(mapped) == set(old_cases) == set(oracle['cases']))
        mapping_failures = []
        for case_id, original in old_cases.items():
            row = mapped.get(case_id, {})
            reference = {'source': 'E07', 'json_pointer': '/cases/' + original['expected_key']}
            is_review = case_id == 'N57_source_variant_unknown'
            expected_row = {
                'id': case_id,
                'original_route': original['route'],
                'original_input': original['input']['path'],
                'original_expected_key': original['expected_key'],
                'original_expectation': reference,
                'classification': 'independent_review_only' if is_review else 'future_runtime_primitive',
                'runtime_expectation': None if is_review else reference,
                'oracle_status': 'historical_runtime_oracle_not_executable_under_p13' if is_review else 'unchanged_future_runtime_obligation',
            }
            if row != expected_row:
                mapping_failures.append(case_id)
        check('B06_exact_each_case_mapping', not mapping_failures, {'mismatches': mapping_failures})
        counts = dict(Counter(row['classification'] for row in mapped.values()))
        check('B06_explicit_96_plus_one_allocation', counts == mapping['classification_counts'] == {'future_runtime_primitive': 96, 'independent_review_only': 1}, counts)
        check('B06_historical_n57_oracle_exact', oracle['cases']['N57_source_variant_unknown'] == evidence['original_n57_oracle'] == {'code': 'CHI-UNSUPPORTED', 'host_qualified': False, 'outcome': 'refusal', 'rule_id': 'LP-VARIANT-SEMANTICS', 'stage': 'variant_review', 'state': 'REJECTED', 'target_starts': 0})
        check('B06_p01_synthetic_scope_retained', oracle['cases']['P01_nonselecting_base']['accepted_for'] == 'synthetic_private_rule_only' and oracle['cases']['P01_nonselecting_base']['host_qualified'] is False and mapped['P01_nonselecting_base']['classification'] == 'future_runtime_primitive')

        protected = read(paths['E15'])
        protection_failures = [row['path'] for row in protected['files'] if not file_matches(root / row['path'], row)]
        check('B07_original_protected_sources', not protection_failures, {'checked': len(protected['files']), 'mismatches': protection_failures, 'full_repository_protection_owner': 'Director'})
        check('B07_preserved_limit_statements', '"document_bytes": 16 * 1024 * 1024' in production and 'def _document(descriptor, maximum=16 * 1024 * 1024' in production and '100,000 operations/30,000 ms' in original_decision and controls['B07']['expected'] == {'protected_sources_changed': False, 'document_bytes': 16777216, 'source_operations': 100000, 'source_ms': 30000})
        check('B07_no_new_focused_product_test', not (root / 'tests/test_current_host_loader_path_v01.py').exists())

        check('B08_proposal_and_no_runtime_result', mapping['state'] == controls['B08']['expected']['candidate_state'] == 'proposed_pending_independent_review_and_director_adoption' and mapping['product_execution'] == 'not_run' and mapping['host_qualification'] == 'not_established' and mapping['n57_disposition']['historical_oracle_satisfied'] is False and mapping['n57_disposition']['runtime_expectation'] is None)
        check('B08_independent_semantic_review_explicit', all(controls[key]['expected']['independent_semantic_review_required'] is True for key in ('B04', 'B05', 'B08')))

        candidate_manifest_path = candidate / 'CANDIDATE-MANIFEST.json'
        manifest_raw = candidate_manifest_path.read_bytes()
        manifest = json.loads(manifest_raw)
        report['candidate_manifest'] = {'path': str(candidate_manifest_path), 'bytes': len(manifest_raw), 'sha256': sha(manifest_raw)}
        manifest_names = [record['path'] for record in manifest['payload']]
        actual_names = sorted(str(path.relative_to(candidate)) for path in candidate.rglob('*') if path.is_file() and path != candidate_manifest_path)
        candidate_failures = [record['path'] for record in manifest['payload'] if not file_matches(candidate / record['path'], record)]
        check('frozen_candidate_exact_inventory_and_hashes', len(manifest_names) == len(set(manifest_names)) and sorted(manifest_names) == actual_names and not candidate_failures, {'payload_files': len(actual_names), 'mismatches': candidate_failures})
    except Exception as exc:
        report['fatal_error'] = {'type': type(exc).__name__, 'message': str(exc)}
        check('completed_without_unexpected_error', False)

    report['finished_at_utc'] = datetime.now(timezone.utc).isoformat()
    report['checks_passed'] = sum(row['passed'] for row in rows)
    report['checks_failed'] = sum(not row['passed'] for row in rows)
    report['status'] = 'passed_static_only' if report['checks_failed'] == 0 else 'failed_static_validation'
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'status': report['status'], 'passed': report['checks_passed'], 'failed': report['checks_failed'], 'report': str(args.report.resolve())}, sort_keys=True))
    return 0 if report['checks_failed'] == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
