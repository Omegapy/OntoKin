"""Account for complete and multiline unittest outcomes without executing tests."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

parser = argparse.ArgumentParser()
parser.add_argument('--log', required=True, type=Path)
parser.add_argument('--collection', required=True, type=Path)
parser.add_argument('--output', required=True, type=Path)
args = parser.parse_args()
raw = args.log.read_bytes()
collection_bytes = args.collection.read_bytes()
collection = json.loads(collection_bytes)
assert collection['loader_errors'] == [] and collection['duplicates'] == {}
expected = set(collection['test_ids'])
records = {}
pending = None
for number, line in enumerate(raw.decode('utf-8').splitlines(), 1):
    header = re.match(r'^(test_\w+) \(([^)]+)\)(?: \.\.\. (.+))?$', line)
    if header:
        name, identity, outcome = header.groups()
        identity = identity.removeprefix('tests.')
        pending = {'test_id': identity, 'header_line': number}
        if outcome is None:
            continue
    elif pending is not None:
        result = re.search(r' \.\.\. (ok|ERROR|FAIL|skipped.*|expected failure|unexpected success)$', line)
        if not result:
            continue
        outcome = result.group(1)
    else:
        continue
    pending.update(outcome_line=number, outcome=outcome)
    assert pending['test_id'] not in records, 'Repeated test outcome needs separate accounting'
    records[pending['test_id']] = pending
    pending = None
placeholders = sorted(x for x in records if x.startswith('unittest.loader._FailedTest.'))
methods = sorted(set(records) - set(placeholders))
assert not (set(methods) - expected), 'Observed method absent from actual collection'
passed = [x for x in methods if records[x]['outcome'] == 'ok']
errors = [x for x in methods if records[x]['outcome'] == 'ERROR']
other = [x for x in methods if records[x]['outcome'] not in ('ok', 'ERROR')]
unrun = sorted(expected - set(methods))
result = {
    'schema': 'ontokin.c210.global-unit-log-tally/0.2',
    'status': 'FAILED',
    'counts': {'collected_real_methods': len(expected), 'distinct_passed_methods': len(passed),
               'distinct_error_methods': len(errors), 'other_nonpassing_methods': len(other),
               'real_methods_without_outcomes': len(unrun), 'failed_import_placeholders': len(placeholders),
               'error_records_including_placeholders': len(errors) + len(placeholders)},
    'logIdentity': {'sha256': 'sha256:' + hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)},
    'collectionIdentity': {'sha256': 'sha256:' + hashlib.sha256(collection_bytes).hexdigest(), 'bytes': len(collection_bytes)},
    'completeUnittestSummaryPresent': bool(re.search(rb'^Ran \d+ tests?', raw, re.M)),
    'methods': [records[x] for x in methods], 'failedImportPlaceholders': [records[x] for x in placeholders],
    'unrunMethods': unrun, 'unrunByModule': dict(sorted(Counter(x.split('.')[0] for x in unrun).items())),
    'errorsByModule': dict(sorted(Counter(x.split('.')[0] for x in errors).items())),
    'parserCorrection': {'initialSingleLineParserPassed': 4282,
                         'additionalPassedMethodsWithMultilineDocstrings': [x for x in passed if records[x]['header_line'] != records[x]['outcome_line']],
                         'meaning': 'Existing ok outcomes with multiline descriptions were omitted by the initial parser, including dynamically generated force-source cases; no test was rerun or reclassified.'},
    'limits': ['This run timed out at 900 seconds; it is not a complete suite pass.',
               'Failed-import placeholders are not real methods; their unexecuted methods remain in the unrun list.',
               'Actual IDs were collected separately with bytecode disabled and no test/setup execution.',
               'The unchanged driver summary tests_run=0 reflects its missing final unittest footer, not zero observed executions.']}
assert len(passed) + len(errors) + len(other) + len(unrun) == len(expected)
args.output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result['counts']))
