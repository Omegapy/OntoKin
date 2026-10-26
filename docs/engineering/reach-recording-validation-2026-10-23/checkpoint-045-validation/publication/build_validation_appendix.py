"""Package actual C045 documentation/metadata validation without changing the core."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone

ROOT = Path('/workspace/scratch/bd03c06e866f/ontokin')
META = ROOT.parent / 'c045-meta'
BASE = ROOT / 'docs/engineering/reach-recording-validation-2026-10-23'
OUT = BASE / 'checkpoint-045-validation'
CORE = 'f2ed86eddcf37215fc134c5bb0ee9dce9bbd9d2b'
TREE = '64f80e946d8f498bfc96ad75fd010315c0a9ecc5'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])

def load(path):
    return json.loads(path.read_bytes())

def record(path, root=BASE):
    data = path.read_bytes()
    return {'path': path.relative_to(root).as_posix(), 'bytes': len(data), 'sha256': sha(data)}

assert git('rev-parse', 'HEAD').decode().strip() == CORE
assert git('rev-parse', 'HEAD^{tree}').decode().strip() == TREE
assert not git('diff', '--name-only') and not git('diff', '--cached', '--name-only')
assert not (BASE / 'checkpoint-045-validation.json').exists()
independent = load(OUT / 'independent-review/result.json')
closure = load(OUT / 'independent-review/closure.json')
assert independent['status'] == 'passed' and independent['checks_passed'] == 44 and not independent['findings']
assert sha((OUT / 'independent-review/result.json').read_bytes()) == '2ef042f3beb1d73bfe760f56d518fc000a38d7e0a05cd71e7286c0d4becf3641'
assert sha((OUT / 'independent-review/closure.json').read_bytes()) == '2448db84f2c2ecaa2c50602e05d291b5fc54734966d065e3cc337931e05acd55'
for row in closure['files_before_this_closure']:
    file = OUT / 'independent-review' / row['path']
    assert (file.stat().st_size, sha(file.read_bytes())) == (row['bytes'], row['sha256'])
assert len(list((OUT / 'independent-review').iterdir())) == 17

shutil.copytree(META / 'core-validation', OUT / 'published-core')
pub = OUT / 'publication'
pub.mkdir()
for name in ['core-publication-inputs.json', 'core-commit.json', 'core-tree.json', 'core-ref.json',
             'core.commit', 'core-import.json', 'prepublication-heads.json', 'publication-window.json',
             'blob-upload-retry.json', 'publication-preparation-attempts.json',
             'prepare_publication-v001.py', 'prepare_publication.py', 'import_published.py',
             'validate_core.py', 'coordination-validation.json', 'build_validation_appendix.py']:
    shutil.copy2(META / name, pub / name)
validation = load(OUT / 'published-core/result.json')
docs = load(OUT / 'published-core/documentation.stdout')
audit = load(OUT / 'published-core/source-data-result.json')
assert validation['status'] == docs['status'] == audit['status'] == 'passed'
assert validation['source_commit'] == CORE and validation['source_tree'] == TREE
assert audit['checks_passed'] == 49 and docs['failures'] == []
assert docs['sources_verified'] == 29 and docs['sections_verified'] == 233
assert docs['links']['documents'] == 197 and docs['links']['local_links'] == 1627 and docs['links']['anchors'] == 92
assert (OUT / 'published-core/inputs-before.json').read_bytes() == (OUT / 'published-core/inputs-after.json').read_bytes()
for row in load(OUT / 'published-core/inputs-after.json'):
    path = ROOT / row['path']
    assert path.stat().st_size == row['bytes'] and sha(path.read_bytes()) == row['sha256']
members = [record(p) for p in sorted(OUT.rglob('*')) if p.is_file()]
assert not any(Path(row['path']).suffix.lower() in {'.md', '.markdown', '.html', '.htm'} for row in members)
result = {
    'schema': 'ontokin.checkpoint045-validation/0.1', 'status': 'passed',
    'created_utc': datetime.now(timezone.utc).isoformat(),
    'owner': 'interactive-reach06-conditional-angular-feasibility-20261026-c045-7f92',
    'branch': 'work/reach06-conditional-angular-feasibility-20261026-c045',
    'parent_commit': '91e8899ad90f04292dd4aee5aaec8b730b397d45',
    'core_commit': CORE, 'core_tree': TREE,
    'publication_rule': 'Append only these new validation records to the unchanged exact core using expected-head nonforce update. Final containing commit/tree and draft PR are bound by remote readback in Issue26 closure; no self-containing final identity is fabricated here.',
    'decision': {'candidate': 'B-Angular/full-entry-audit/0.1', 'outcome': 'source-only NO-GO on observed current-P23 batch',
                 'prefix_gross_ceiling': 403, 'defined_admitted_route_audit_floor': 512,
                 'forced_admitted_route_saving_upper_bound': -109,
                 'proper_structural_screen_declines_before_audit': True,
                 'proper_rejected_route_prefix_reuses': 0, 'measured_candidate_cost': None,
                 'universal_impossibility_claimed': False},
    'actual_validation': {'receipt': 'checkpoint-045-validation/published-core/result.json',
                         'source_files': 2397, 'source_bytes': 493496287,
                         'all_remote_paths_modes_sizes_blobs_match': True,
                         'full_inputs_stable': True, 'python': validation['python'],
                         'python_executable': validation['python_executable'], 'platform': validation['platform'],
                         'started_utc': validation['started_utc'], 'finished_utc': validation['finished_utc'],
                         'documentation': {'exit_code': 0, 'sources': 29, 'sections': 233,
                                           'documents': 197, 'local_links': 1627, 'anchors': 92, 'failures': 0},
                         'source_data_audit': {'exit_code': 0, 'checks_passed': 49, 'checks_failed': 0}},
    'independent_final_core_audit': {'result': record(OUT / 'independent-review/result.json'),
                                   'closure': record(OUT / 'independent-review/closure.json'),
                                   'checks_passed': 44, 'findings': [],
                                   'scope': 'Published core and available evidence; future appendix/final containing commit are outside this independent audit.',
                                   'independence_disclosure': independent['independence_disclosure']},
    'archive': {'C044_parts': 9, 'joined_bytes': 6401045,
                'joined_sha256': '53406dbde80cb37af0930f37385e03f6b8282ca9c23d020a30a5fdcb891b37a7',
                'members': 99, 'member_bytes': 49758827, 'hashes_crcs_modes_restored_mtimes_verified': True},
    'appendix_input_application': 'Every core byte remained unchanged during packaging. Appendix contains only JSON, text logs, actual commit bytes and scripts; no Markdown/HTML documentation input was added or changed after the actual documentation command.',
    'retained_failures_and_limits': [
        'Recovery default/HTTP errors, original parent timezone correction and task URL cleanup remain preserved in the core.',
        'Initial source audit failed on missing invocation_id in return events; original script/log preserved and correction uses call_event.',
        'Initial metadata builder NameError and initial publication-helper whitespace exception retain exact scripts and transcript-only log qualification.',
        'One terminal blank line in original recovery/acquire.py is preserved; git whitespace-check exit2 is disclosed, not called a pass.',
        'One blob upload internal error was read back as404 and then retried identically before any commit/ref mutation.',
        'Independent reviewer exploratory read-only summary/path errors are disclosed in inspection-attempts.json.',
        'C044 launch preceded its nominal declared start; no elapsed neutrality, unknown-tail result or partial-archive origin is inferred.',
        'Original key-order replays use C044 reviewed equality mapping, not a fresh native-equality proof.',
        'The4327-bit numerical bound is conditional on the defined native2048-bit inputs, original constants and32768-bit cap; it is not cache/authority/lifetime proof.',
        'No positive candidate net bound, runtime optimization, product rerun, candidate numerical replay, benchmark, hosted job, merge or full release pass is established.',
        'Original28 remains24/28 with P11/P16/P23/L03 capped; C035 remains held including adverse L03 timing.'
    ],
    'product_requests': 0, 'runtime_changes': 0, 'hosted_jobs_dispatched': 0, 'main_merges': 0,
    'next_scope': 'checkpoint-045-next-scope.json',
    'files': members, 'appendix_member_files': len(members),
    'appendix_member_bytes': sum(x['bytes'] for x in members),
}
(BASE / 'checkpoint-045-validation.json').write_text(json.dumps(result, indent=2) + '\n')
new = sorted(p for p in git('ls-files', '--others', '--exclude-standard', '-z').decode().split('\0') if p)
owned = 'docs/engineering/reach-recording-validation-2026-10-23/checkpoint-045-validation'
assert all(p.startswith(owned + '/') or p == owned + '.json' for p in new)
assert len(new) == len(members) + 1
git('add', '--', *new)
assert not git('diff', '--name-only')
changes = git('diff', '--cached', '--name-status').decode().splitlines()
assert all(x.startswith('A\t') for x in changes) and len(changes) == len(new)
white = subprocess.run(['git', '-C', str(ROOT), 'diff', '--cached', '--check'],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
records, contents = [], {}
for name in new:
    data = (ROOT / name).read_bytes()
    records.append({'path': name, 'mode': '100644', 'type': 'blob', 'bytes': len(data),
                    'sha': hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest(), 'sha256': sha(data)})
    contents[name] = data.decode('utf-8')
pub_result = {'schema': 'ontokin.checkpoint045-appendix-publication-inputs/0.1',
              'parent': CORE, 'parent_tree': TREE, 'tree': git('write-tree').decode().strip(),
              'new_files': len(records), 'new_bytes': sum(x['bytes'] for x in records),
              'all_changes_are_new_owned_validation_files': True,
              'all_core_files_preserved': True,
              'whitespace_check': {'exit_code': white.returncode, 'stdout': white.stdout.decode(), 'stderr': white.stderr.decode()},
              'files': records}
(META / 'appendix-publication-inputs.json').write_text(json.dumps(pub_result, indent=2) + '\n')
(META / 'appendix-content-bundle.json').write_text(json.dumps(contents, ensure_ascii=False) + '\n')
print(json.dumps({k: v for k, v in pub_result.items() if k != 'files'}))
print(json.dumps({'validation': record(BASE / 'checkpoint-045-validation.json'), 'appendix_members': len(members)}))
