"""Verify and summarize recorded checks on the exact merged main."""
from pathlib import Path
import collections
import datetime
import hashlib
import json

ROOT = Path('/workspace/scratch/a4d9132036d4')
OUT = ROOT / 'work-c203/main-checks'
REPO = ROOT / 'main-verification'
PRIOR = REPO / 'docs/engineering/static-tray-exporter-c200/evidence/publication-c203/checks'

def read(path):
    return json.loads(path.read_bytes())

def binding(path):
    data = path.read_bytes()
    return {'path': str(path), 'size_bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}

before = read(OUT / 'IDENTITY-BEFORE.json')
after = read(OUT / 'IDENTITY-AFTER.json')
assert before['passed'] and after['passed'] and after['inputs_unchanged_during_tests']
for name in ['focused', 'protocol', 'core', 'documentation']:
    launch = read(OUT / (name + '-launch.json'))
    assert launch['status'] == 'PASS' and launch['exit_code'] == 0, name
    assert launch['source_commit'] == after['main_commit'] and launch['source_tree'] == after['main_tree']
    for stream in ['stdout', 'stderr']:
        assert launch[stream] == binding(Path(launch[stream]['path']))
focused = read(OUT / 'focused/RESULTS.json')
prior_focused = read(PRIOR / 'focused/RESULTS.json')
assert focused['implementation_commit'] == after['main_commit']
assert focused['implementation_tree'] == after['main_tree']
assert focused['worktree_status'] == []
assert focused['status'] == 'PASS' and focused['tests_run'] == 107
assert focused['failures'] == [] and focused['errors'] == [] and focused['skipped'] == []
assert len(focused['unique_planned_ids']) == len(set(focused['unique_planned_ids'])) == 107
assert set(focused['passed_ids']) == set(focused['unique_planned_ids']) == set(prior_focused['passed_ids'])
assert focused['log'] == binding(OUT / 'focused/tests.log')
pinned_methods = [name for name in focused['passed_ids'] if '.PinnedExporterSourceControls.' in name]
assert len(pinned_methods) == 5
source_checks = []
for source in focused['sources']:
    assert source == binding(Path(source['path'])), source['path']
    source_checks.append(source)
protocol_log = (OUT / 'protocol.stderr.log').read_text()
protocol_methods = [line for line in protocol_log.splitlines() if line.startswith('test_')]
assert len(protocol_methods) == 10 and all(line.endswith(' ... ok') for line in protocol_methods)
assert 'Ran 10 tests in ' in protocol_log and protocol_log.endswith('\nOK\n')
core = read(OUT / 'core-conformance.json')
assert core['summary'] == {'passed': 43, 'failed': 0, 'total': 43, 'assertions': 694, 'expected_valid': 12, 'expected_invalid_or_conflicting': 29, 'expected_unsupported': 2}
docs = read(OUT / 'DOCUMENTATION-CHECK.json')
assert docs['status'] == 'passed' and docs['failures'] == []
assert docs['sources_verified'] == 29 and docs['sections_verified'] == 233
assert docs['links']['local_links'] == 4106
compiler = read(PRIOR / 'compiler/RESULTS.json')
assert compiler['status'] == 'PASS' and compiler['tests_run'] == 47
assert compiler['failures'] == [] and compiler['errors'] == [] and compiler['skipped'] == []
assert set(compiler['passed_ids']) == set(compiler['unique_planned_ids']) and len(set(compiler['passed_ids'])) == 47
compiler_sources = []
old_repo = ROOT / 'candidate'
for source in compiler['sources']:
    relative = Path(source['path']).relative_to(old_repo)
    actual = binding(REPO / relative)
    assert actual['sha256'] == source['sha256'] and actual['size_bytes'] == source['size_bytes']
    compiler_sources.append({'path': str(relative), 'sha256': actual['sha256'], 'size_bytes': actual['size_bytes']})
process_rows = []
process_counts = {}
for name in ['focused', 'protocol', 'documentation']:
    observed = read(OUT / (name + '-command.json'))
    assert observed['exit_code'] == 0 and observed['target_unchanged'] is True
    counts = collections.Counter()
    for process in observed['process_starts']:
        executable = Path(process['executable']).name
        assert process['blocked'] is False
        assert executable in {'git', 'python', 'python3', 'python3.12'}
        counts['git_metadata' if executable == 'git' else 'python_reader_cli'] += 1
        process_rows.append({'cohort': name, **process})
    process_counts[name] = dict(counts)
assert process_counts['focused'] == {'git_metadata': 3, 'python_reader_cli': 8}
assert process_counts['protocol'] == {} and process_counts['documentation'] == {}
remote_source = ROOT / 'work-c203/C200-MERGE-READBACK.json'
remote_copy = OUT / 'REMOTE-MERGE-READBACK.json'
assert not remote_copy.exists()
remote_copy.write_bytes(remote_source.read_bytes())
report = {
    'schema': 'ontokin.c203.actual-main-applicable-checks/0.1',
    'decision': 'PASS_ACTUAL_MAIN_APPLICABLE_CHECKS',
    'completed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'main_commit': after['main_commit'], 'main_tree': after['main_tree'],
    'merged_pr': 137, 'closed_issue': 136,
    'remote_readback': binding(remote_copy),
    'remote_readback_scope': after['remote_readback_scope'],
    'remote_main_and_tree_equal_worktree': True,
    'published_source_tree_equal_main': True,
    'worktree_clean_before_and_after': True,
    'reviewed_candidate': after['reviewed_candidate'],
    'changes_since_reviewed_candidate': after['changes_since_reviewed_candidate'],
    'independent_review_files_equal_approved_copies': after['independent_review_artifacts'],
    'locked_inputs_verified_before_and_after': 301,
    'locked_and_prior_tested_inputs_equal_main': True,
    'input_lock': after['input_lock'],
    'python_version': focused['python_version'], 'platform': focused['platform'],
    'fresh_cohorts': {
        'focused': {'passed': 107, 'skipped': 0, 'pinned_exporter_methods': pinned_methods},
        'protocol': {'passed': 10, 'skipped': 0},
        'core': core['summary'],
        'documentation': {'sources': 29, 'sections': 233, 'documents': docs['links']['documents'], 'local_links': 4106, 'failures': []}
    },
    'fresh_focused_direct_source_bindings': source_checks,
    'compiler': {
        'rerun_on_main': False, 'reused_passed_methods': 47, 'skipped': 0,
        'reason': 'The complete main diff from the reviewed candidate adds only the five unchanged review artifacts; execution code and all locked/tested inputs are identical. All four directly recorded compiler input files also match current main. A second compiler execution would repeat the same covered input cohort.',
        'source_commit': compiler['implementation_commit'],
        'result': binding(PRIOR / 'compiler/RESULTS.json'),
        'verified_direct_inputs': compiler_sources
    },
    'process_observations': process_counts,
    'process_observation_rows': process_rows,
    'core_child_processes_instrumented': False,
    'core_scope': 'Direct actual core CLI executed and logged; no blanket claim that all descendants were instrumented.',
    'new_lifecycle_scope': {'native_constructions': 0, 'receiving': 0, 'node': 0, 'lifecycle_stubs': 0, 'timed_authors': 0, 'qualification_runs': 0},
    'c199_c200_schedules_closed': True,
    'full_legacy_regression': {
        'rerun': False, 'status': 'FAILED', 'distinct_passing_methods': 4239,
        'torque_read_methods_not_run': 13, 'setup_timeout_ms': 30000,
        'reason': 'Shared runtime, fixtures, schemas, grammar, conformance tools and workflows are unchanged from premerge main. The independently approved experimental integration has no new or worsened identified legacy behavior. No full-suite pass is claimed.'
    },
    'limitations': [
        'Fresh CPU evidence establishes only the recorded Python 3.12.14/Linux environment.',
        'Historical visual limits, incomplete cancellation/general contact/live physics/external compatibility/comparative benefit and complete release roles remain unchanged.',
        'Eight recovered streams retain recovery-time-only individual hashes; their historical provenance limit is unchanged.',
        'C201 admission remains unexecuted and requires its separate protocol and authority.',
        'Remote status is bound to the integrator-captured post-merge readback; this verifier did not make a new remote request.'
    ],
    'checks_artifacts': [binding(path) for path in sorted(OUT.iterdir()) if path.is_file() and path.name not in {'CHECKS-SUMMARY.json', 'CHECKS-SUMMARY.md'}]
}
(OUT / 'CHECKS-SUMMARY.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
markdown = '''# Actual-main validation after C200 integration

**PASS: the merged main commit passed the applicable fresh checks.** Main is `{commit}`, tree `{tree}`. The clean validation worktree matches the integrator's captured GitHub main and merge readback for PR #137. Issue #136 is closed in that same readback. This verifier compared the retained API response independently; it did not issue another network request.

## Identity and preservation

All **301 immutable locked inputs** and the prior tested-source manifest match actual main, before and after these checks. Executable C200 source is identical to the previously executed qualification. Shared runtime, fixtures, schemas, grammar, conformance tools and workflows are identical to the premerge main.

The main tree differs from reviewed candidate `125353836119e50215287c27d80e99cef6d85e8f` only by the five published independent-review artifacts. Every published review file matches its approved original bytes. The merged source branch tree equals the actual main tree.

## Actual checks on main

| Fresh check | Result |
| --- | --- |
| Focused exporter/source/reader controls | 107 passed; zero skips; all five pinned-exporter source methods executed |
| C200 protocol controls | 10 passed; zero skips |
| Core conformance | 43 cases, 694 assertions, zero failures |
| Documentation preservation and navigation | 29 sources, 233 sections, 796 documents, 4,106 local links; zero failures |

The checks used CPython 3.12.14 on Linux x86-64. Commands, stdout, stderr, method identities, source bindings and results are preserved beside this report. Focused/protocol/documentation child-process observations contain eight Python reader CLI children and three Git metadata reads, all from the focused cohort; protocol and documentation started no children. The core CLI was executed directly, with its command and output recorded, but its child activity was not instrumented.

The **47 compiler methods** were not repeated. Their prior passing result remains reusable because the complete source tree change adds only unchanged review evidence, all locked/tested inputs match, and all four direct compiler source bindings independently match actual main. This reuse is recorded separately from the fresh checks.

No new native construction, receiving, Node, lifecycle, timed-author or qualification execution occurred. C199/C200 schedules remain closed.

## Preserved limits

The historical full regression remains **FAILED**: 4,239 distinct passing methods and 13 torque-read methods NOT RUN after the unchanged 30,000 ms setup timeout. It was not rerun. The unchanged shared runtime identities and the independently reviewed experimental boundary justify the applicable scope; this report makes no new full-suite or complete-release claim.

Existing visual limits, incomplete external compatibility and other release roles remain unchanged. Eight recovered preparation streams still have only recovery-time individual hashes. C201 admission has not executed. A later main change requires validation of its own identified source scope.

## Evidence

- `CHECKS-SUMMARY.json`: machine-readable decision, verified input bindings and limits.
- `IDENTITY-BEFORE.json` and `IDENTITY-AFTER.json`: exact main, remote-readback comparison, all 301 inputs and five review artifact hashes.
- `REMOTE-MERGE-READBACK.json`: unchanged copy of the integrator's captured API response.
- `focused/RESULTS.json` and `focused/tests.log`: actual 107-method execution.
- `protocol.stderr.log`, `core-conformance.json` and `DOCUMENTATION-CHECK.json`: actual corresponding results.
- Each `*-launch.json` and available `*-command.json`: exact commands, environment, stream hashes and process observations.
'''.format(commit=after['main_commit'], tree=after['main_tree'])
(OUT / 'CHECKS-SUMMARY.md').write_text(markdown)
print(json.dumps({'decision': report['decision'], 'main_commit': report['main_commit'], 'main_tree': report['main_tree'], 'fresh_focused': 107, 'fresh_protocol': 10, 'fresh_core_cases': 43, 'fresh_core_assertions': 694, 'reused_compiler': 47, 'doc_links': 4106, 'locked_inputs': 301}))
