"""Rebind only the independently corrected inherited inventory; no product import."""
from pathlib import Path
import hashlib
import json
import stat
import zipfile

BASE = Path('/workspace/scratch/2eb33b59a678')
ROOT = BASE / 'repository'
AREA = ROOT / 'docs/engineering/localized-repair-c271/required-images-p29'
OUT = AREA / 'controls'
ARCHIVE = AREA / 'fixture-revisions/CANDIDATE002.zip'
OLD_COHORT = 'dab30610b44cdb0596c395505a940722506e2c5535ed58b0984317f261de6efe'
NEW_COHORT = '7aa9e1278419e6b4fd27afbc758d5dcea195a245960cd4c972d8102a34dcce77'
OLD_FREEZE = 'a705a493a37d907eb677bc3e207a99670ef2ca3d906ef82087a3a815f218bc09'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def save(name, value):
    path = OUT / name
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')
    path.chmod(0o644)


assert sha(ARCHIVE.read_bytes()) == '5db85af0b84fb4712dffe94c69297a9bfe459614e3312b7c27f41c32ec119cf6'
assert sha((OUT / 'FREEZE.json').read_bytes()) == OLD_FREEZE
prior = load(OUT / 'FREEZE.json')
with zipfile.ZipFile(ARCHIVE) as archive:
    for row in prior['files']:
        current = (ROOT / row['path']).read_bytes()
        assert sha(current) == row['sha256'] and current == archive.read(row['path']), row['path']

cohort_path = AREA / 'INHERITED-COHORT.json'
cohort_raw = cohort_path.read_bytes()
assert len(cohort_raw) == 67770 and sha(cohort_raw) == NEW_COHORT
cohort = json.loads(cohort_raw)
assert len(cohort['selected_test_ids']) == len(set(cohort['selected_test_ids'])) == 481
assert cohort['exclusions'] == []
runtime_path = BASE / 'verification/baseline-inherited/RUNTIME-INVENTORY.json'
runtime_raw = runtime_path.read_bytes()
assert sha(runtime_raw) == '51c06426550538d2abba19e86659ff0198002e3f5a6e11709de501bd51cb2dfd'
runtime = json.loads(runtime_raw)
assert sorted(cohort['selected_test_ids']) == runtime['actual_ids']
assert set(runtime['expected_ids']) < set(runtime['actual_ids'])
assert len(runtime['expected_ids']) == 372 and not runtime['exact_match']

commands = load(OUT / 'COMMANDS.json')
assert commands['inherited_cohort']['sha256'] == OLD_COHORT
assert commands['inherited_command'][2].count(OLD_COHORT) == 2
commands['inherited_command'][2] = commands['inherited_command'][2].replace(OLD_COHORT, NEW_COHORT)
commands['inherited_cohort'].update(sha256=NEW_COHORT, selected_ids=481)
commands['superseded_proposal'] = (
    'The 371-method exclusion proposal was superseded by 372 with zero exclusions. '
    'Candidate002 baseline-inherited discovery then exposed 109 omitted CONTROL_VARIANTS methods; '
    'the comparison failed before any test method ran. Candidate003 binds all 481 statically '
    'derived IDs, independently reconciled with the retained runtime inventory, with zero exclusions.'
)
commands['retained_prior_attempt'] = {
    'path': 'verification/baseline-inherited/',
    'runtime_inventory_sha256': sha(runtime_raw),
    'returncode': 1,
    'test_methods_executed': 0,
    'product_module_imports': True,
    'status': 'discovery_inventory_refused_before_runner',
    'production_unchanged': True,
}
save('COMMANDS.json', commands)

companions = load(OUT / 'COMPANIONS.json')
matching = [row for row in companions['files'] if row['path'] == cohort_path.relative_to(ROOT).as_posix()]
assert len(matching) == 1 and matching[0]['sha256'] == OLD_COHORT
matching[0].update(size_bytes=len(cohort_raw), sha256=NEW_COHORT, mode=oct(stat.S_IMODE(cohort_path.stat().st_mode)))
save('COMPANIONS.json', companions)

revision = {
    'schema': 'ontokin.c271.p29-fixture-revision/1',
    'candidate': 'candidate003',
    'previous_candidate': {
        'freeze_sha256': OLD_FREEZE,
        'adapter_sha256': 'ca650e2b0d2557bb050dcfc5b5269ccc3519d0a357a1ff3a0c2f89d03f5bb717',
        'preserved_archive': ARCHIVE.relative_to(ROOT).as_posix(),
        'archive_sha256': sha(ARCHIVE.read_bytes()),
    },
    'reviewer_findings': [
        'The inherited cohort omitted 109 CONTROL_VARIANTS-generated HostInspectionControls methods. '
        'All are applicable; the corrected 481 exact IDs were independently derived and reconciled '
        'with the failed preflight discovery before retry. No runtime exclusion is permitted.'
    ],
    'allowed_changed_payloads': [
        'tests/test_current_host_required_images_v01.py',
        *[(OUT / name).relative_to(ROOT).as_posix() for name in (
            'COMMANDS.json', 'COMPANIONS.json', 'README.md', 'REVISION.json', 'FIXTURE-MANIFEST.json')],
    ],
    'adapter_change_limit': 'Only FIXTURE_MANIFEST_SHA256 string literal may differ; all other AST nodes must be identical to candidate002.',
    'adopted_p27_expectations_changed': False,
    'design_change': False,
    'fixture_author_product_imports_or_execution': 0,
    'prior_director_attempt': commands['retained_prior_attempt'],
    'cohort_correction': 'docs/engineering/localized-repair-c271/required-images-p29/INHERITED-COHORT-CORRECTION.json',
}
save('REVISION.json', revision)

readme_path = OUT / 'README.md'
readme = readme_path.read_text()
assert readme.count('372') == 2
readme = readme.replace('372', '481')
readme = readme.replace(
    'Candidate 001 remains\npreserved at the identity in `REVISION.json`.',
    'Both earlier candidates remain preserved. `REVISION.json` identifies the\nimmediate predecessor and its exact archive.'
)
readme = readme.replace(
    '## Execution gate\n',
    '## Candidate 003 inventory correction\n\n'
    'The Director\'s first inherited baseline imported the unchanged modules and\n'
    'discovered 481 methods against candidate 002\'s declared 372. Its exact-ID\n'
    'comparison refused before any test method ran. The missing 109 methods come\n'
    'from the unchanged inspection module\'s literal `CONTROL_VARIANTS` registration.\n'
    'The Director and independent reviewer reconciled all 481 IDs; none is excluded.\n'
    'Candidate 003 changes inventory bindings and records only. Every adopted oracle,\n'
    'fixture/context byte and adapter behavior is unchanged; only the adapter\'s\n'
    'manifest-hash literal changes. The prior discovery failure remains retained.\n\n'
    '## Execution gate\n'
)
readme_path.write_text(readme)
print(json.dumps({'candidate': 'candidate003', 'cohort_sha256': NEW_COHORT, 'selected_ids': 481, 'status': 'rebound_pending_static_freeze'}, indent=2))
