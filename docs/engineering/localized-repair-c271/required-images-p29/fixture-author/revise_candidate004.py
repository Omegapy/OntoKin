"""Freeze the reviewed RI-L08 recording-only metadata input; no product import."""
from pathlib import Path
import ast
import hashlib
import json
import zipfile

BASE = Path('/workspace/scratch/2eb33b59a678')
ROOT = BASE / 'repository'
AREA = ROOT / 'docs/engineering/localized-repair-c271/required-images-p29'
OUT = AREA / 'controls'
ARCHIVE = AREA / 'fixture-revisions/CANDIDATE003.zip'
ADAPTER = ROOT / 'tests/test_current_host_required_images_v01.py'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(name, value):
    path = OUT / name
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')
    path.chmod(0o644)


assert sha(ARCHIVE.read_bytes()) == '56f59a7cab4d8d552a9ccd3ea763e4dad9c187f9a263e2b68e746be0ff6801f1'
assert sha((OUT / 'FREEZE.json').read_bytes()) == 'ca54eae3708af5e72f6d01c39a17b625511b8de1411b77d0a7ac0d7427eeae1a'
with zipfile.ZipFile(ARCHIVE) as archive:
    prior = json.loads(archive.read((OUT / 'FREEZE.json').relative_to(ROOT).as_posix()))
    for row in prior['files']:
        if row['path'] != ADAPTER.relative_to(ROOT).as_posix():
            assert (ROOT / row['path']).read_bytes() == archive.read(row['path']), row['path']
ast.parse(ADAPTER.read_bytes())
failure_path = BASE / 'verification/implementation-focused-001/control-data/required-images/RI-L08.json'
failure_raw = failure_path.read_bytes()
assert sha(failure_raw) == '28038c710f692023611e35467920059e3c4d7a024cda92affb65d56491170872'
failure = json.loads(failure_raw)
assert failure['passed'] is False and failure['forbidden_calls'] == ["(['uname', '-p'],)"]
inherited = failure['observations']['inherited_corpora'][0]
assert len(inherited['method_ids']) == 61 and inherited['tests_run'] == 10 and len(inherited['errors']) == 1

save('INHERITED-METADATA-STUB.json', {
    'schema': 'ontokin.c271.p29-inherited-recording-metadata-stub/1',
    'control_id': 'RI-L08',
    'module': 'test_current_host_rtld_paths_v01',
    'leaf': 'platform.platform',
    'value': 'Synthetic P29 RI-L08 metadata; host not probed',
    'expected_call_count': 1,
    'expected_args': [],
    'expected_kwargs': {},
    'recording_file': 'INPUTS.json',
    'recording_key': 'platform',
    'duration': 'Only this module nested suite.run; original callable restored before assertions.',
    'classification': 'Mocked recording metadata leaf; no product input, policy, parser, caller, process guard or oracle is replaced.',
    'claim_limit': 'The synthetic label conveys no host observation or qualification. All 61 inherited method IDs and original expected results remain real and unchanged; N34/N57 stay external.'
})
save('REVISION.json', {
    'schema': 'ontokin.c271.p29-fixture-revision/1',
    'candidate': 'candidate004',
    'previous_candidate': {
        'freeze_sha256': 'ca54eae3708af5e72f6d01c39a17b625511b8de1411b77d0a7ac0d7427eeae1a',
        'adapter_sha256': 'a6d5f9622eecd0f8a4e52621c851637a8b97f816b8d70a464c93ce97f5917de5',
        'preserved_archive': ARCHIVE.relative_to(ROOT).as_posix(),
        'archive_sha256': sha(ARCHIVE.read_bytes()),
    },
    'reviewer_findings': [
        'RI-L08 RTLD setUpClass calls platform.platform once, only to record INPUTS.json metadata. Its lazy processor lookup attempted uname -p and the existing outer guard refused before launch. The 51 original RTLD runtime methods were unrun; the 10 supplemental methods ran.',
        'The independent reviewer confirmed a scoped synthetic metadata label is permissible. Apply it only to the RI-L08 nested RTLD suite, observe exactly one zero-argument call, prove restoration and recorded label equality, and preserve every process/checkpoint guard and original expectation.'
    ],
    'allowed_changed_payloads': [
        ADAPTER.relative_to(ROOT).as_posix(),
        *[(OUT / name).relative_to(ROOT).as_posix() for name in ('README.md', 'REVISION.json', 'FIXTURE-MANIFEST.json')],
    ],
    'allowed_added_payloads': [(OUT / 'INHERITED-METADATA-STUB.json').relative_to(ROOT).as_posix()],
    'adapter_change_limit': 'Only new INHERITED_METADATA_STUB constant load, RequiredImageControls.inherited_case metadata leaf scope/observation, and FIXTURE_MANIFEST_SHA256 literal may differ. Every other byte must match candidate003.',
    'adopted_p27_expectations_changed': False,
    'old_corpus_sources_or_expectations_changed': False,
    'production_changed_by_fixture_author': False,
    'design_change': False,
    'fixture_author_product_imports_or_execution': 0,
    'prior_director_attempt': {
        'path': 'verification/implementation-focused-001/',
        'returncode': 1,
        'outer_test_methods_executed': 116,
        'outer_passed': 115,
        'outer_failed': ['RI-L08'],
        'nested_inherited_discovered': 61,
        'nested_inherited_executed': 10,
        'nested_RTLD_methods_unrun': 51,
        'blocked_metadata_command': ['uname', '-p'],
        'blocked_before_real_launch': True,
        'production_source_sha256': '71e837c31df06df7ce10262683c5d28a72bdb3c039f09b97eec58839f4121758',
        'failure_evidence_sha256': sha(failure_raw),
        'relabeled_as_pass': False,
    },
    'unchanged_inherited_cohort_sha256': '7aa9e1278419e6b4fd27afbc758d5dcea195a245960cd4c972d8102a34dcce77',
    'candidate004_product_execution': 'NOT_RUN'
})
readme = OUT / 'README.md'
text = readme.read_text()
assert '## Candidate 004 recording metadata correction' not in text
text = text.replace('## Execution gate\n',
    '## Candidate 004 recording metadata correction\n\n'
    'The first focused implementation attempt passed 115 of 116 obligations. RI-L08\n'
    'discovered all 61 inherited RTLD and supplemental methods, but its unchanged\n'
    'RTLD setup tried `uname -p` through `platform.platform()` solely to record the\n'
    '`INPUTS.json` platform field. The outer process guard refused before launch.\n'
    'The 51 RTLD runtime methods were unrun; all 10 supplemental methods ran.\n'
    'That failed attempt remains retained and is not relabeled as a pass.\n\n'
    '`INHERITED-METADATA-STUB.json` freezes an explicitly synthetic recording label.\n'
    'Only RI-L08 patches `module.platform.platform` during its nested suite run.\n'
    'The adapter records and asserts one zero-argument call, exact recorded label,\n'
    'and restoration of the original callable afterward. All process guards,\n'
    'checkpoint refusals, 61 method IDs, old corpus bytes and 116 adopted oracles\n'
    'remain unchanged. The production `_platform` function is not patched by this\n'
    'correction. The label is no evidence about the host.\n\n'
    '## Execution gate\n')
text = text.replace('Product results\nare **NOT_RUN** at freeze.',
    'Candidate 004 product results\nare **NOT_RUN** at freeze; prior attempts and their failures remain preserved.')
readme.write_text(text)
print(json.dumps({'candidate': 'candidate004', 'metadata_leaf': 'platform.platform', 'scope': 'RI-L08 nested suite recording only', 'status': 'materialized_pending_static_freeze'}, indent=2))
