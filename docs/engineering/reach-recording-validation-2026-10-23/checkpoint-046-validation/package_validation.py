"""Append actual C046 validation evidence without changing the reviewed core."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import shutil
import subprocess

ROOT = Path('/workspace/scratch/fd65650eb54f')
REPO = ROOT / 'OntoKin'
BASE = REPO / 'docs/engineering/reach-recording-validation-2026-10-23'
DEST = BASE / 'checkpoint-046-validation'
WORK = ROOT / 'c046-work'
CORE = 'ef4ebc263deca57ad7b0d014ec4e9af16ca9ab0b'
TREE = '591258c1caad81864f0bd2801ffa0cace1100d59'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=REPO).decode().strip()


def read(path):
    return json.loads(path.read_text())


def write(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')


def binding(path):
    raw = path.read_bytes()
    return {'path': path.relative_to(BASE).as_posix(), 'bytes': len(raw),
            'sha256': hashlib.sha256(raw).hexdigest()}


def copy(src, dst):
    assert src.is_file() and not src.is_symlink()
    assert not dst.exists(), dst
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    assert src.read_bytes() == dst.read_bytes()


assert git('rev-parse', 'HEAD') == CORE
assert git('rev-parse', 'HEAD^{tree}') == TREE
assert not git('status', '--porcelain')
assert not DEST.exists()
core_tree = read(WORK / 'core-remote-tree.json')
assert core_tree['sha'] == TREE and not core_tree['truncated']
core_files = {x['path']: x for x in core_tree['tree'] if x['type'] == 'blob'}
assert len(core_files) == 2503
for path, entry in core_files.items():
    raw = (REPO / path).read_bytes()
    assert len(raw) == entry['size']
    assert hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == entry['sha']

ind_src = ROOT / 'c046-validation/independent-review'
ind_manifest = read(ind_src / 'manifest.json')
assert len(ind_manifest['files']) == 27
assert sum(x['bytes'] for x in ind_manifest['files']) == 4331131
for entry in ind_manifest['files']:
    path = ind_src / entry['path']
    raw = path.read_bytes()
    assert len(raw) == entry['bytes'] and hashlib.sha256(raw).hexdigest() == entry['sha256']
    copy(path, DEST / 'independent-review' / entry['path'])
copy(ind_src / 'manifest.json', DEST / 'independent-review/manifest.json')
for path in sorted((ROOT / 'c046-validation/published-core').iterdir()):
    copy(path, DEST / 'published-core' / path.name)
copy(WORK / 'run_core_validation.py', DEST / 'published-core/run_core_validation.py')
for name in ['core-actual-commit.bin', 'core-import-verification.json',
             'core-publication-plan.json', 'core-publication-receipt.json',
             'core-remote-commit.json', 'core-remote-ref.json', 'core-remote-tree.json',
             'core-whitespace.stdout', 'core-whitespace.stderr']:
    copy(WORK / name, DEST / 'publication' / name)
copy(Path(__file__), DEST / 'package_validation.py')

actual = read(DEST / 'published-core/result.json')
audit = read(DEST / 'published-core/source-data.json')
docs = read(DEST / 'published-core/documentation.stdout')
independent = read(DEST / 'independent-review/result.json')
closure = read(DEST / 'independent-review/closure.json')
assert actual['status'] == audit['status'] == docs['status'] == independent['status'] == 'passed'
assert audit['checks_passed'] == 344 and audit['checks_failed'] == 0
assert independent['checks_passed'] == 85 and independent['checks_failed'] == 0
assert not independent['findings']
assert actual['commit'] == independent['core_commit'] == CORE
assert actual['tree'] == independent['core_tree'] == TREE

record = {
    'schema': 'ontokin.checkpoint046-validation/0.1',
    'status': 'passed',
    'created_utc': datetime.now(timezone.utc).isoformat(),
    'owner': 'interactive-reach06-l03-retirement-review-20261026-c046-9d64',
    'branch': 'work/reach06-l03-retirement-review-20261026-c046',
    'parent_commit': 'a5bb1e674e4ae3eb1d77e83b63f7a809eacf0bd0',
    'core_commit': CORE, 'core_tree': TREE,
    'publication_rule': 'Append only these new validation records to the unchanged exact core using expected-head nonforce update. Final containing commit/tree and draft PR are bound by remote readback in Issue #26 closure; no self-containing final identity is fabricated here.',
    'ownership_comment': 6424530160,
    'core_validation_window_comment': 6424891921,
    'independent_audit_window_comment': 6424984212,
    'appendix_window_comment': 6425093159,
    'appendix_window_expires_utc': '2026-10-26T19:40:00Z',
    'decision': {
        'task': 'L03 retirement/direct reseeding and coefficient-cache lifetime source/retained-data review',
        'runtime_candidate_selected': False,
        'historical_published_seeds': 6,
        'historical_published_advances': 296,
        'historical_no_capacity_eviction_interval': 'C033 key 1 entry through key 153 wrapper exit snapshot before outer cleanup only',
        'no_eviction_is_source_bound_inference': True,
        'excluded_lifetimes': ['setup/key 0', 'earlier history', 'outer cleanup', 'custom or reentrant callbacks', 'current C035'],
        'current_trace_establishes': 'Completed coefficient lookup miss followed by construction division precharge refusal in the direct source-seed route',
        'current_locals_and_ordered_reader_cache_missing': True,
        'prepared_capture_executed': False,
        'capture_neutrality_established': False,
        'universal_impossibility_claimed': False
    },
    'actual_validation': {
        'receipt': 'checkpoint-046-validation/published-core/result.json',
        'source_files': actual['files'], 'source_bytes': actual['bytes'],
        'all_remote_paths_modes_sizes_blobs_match': True,
        'full_inputs_stable': actual['inputs_stable'],
        'python': actual['python'], 'python_executable': actual['executable'],
        'platform': actual['platform'],
        'started_utc': actual['started_utc'], 'finished_utc': actual['finished_utc'],
        'commands': actual['commands'],
        'documentation': {
            'exit_code': actual['commands'][0]['exit_code'],
            'sources': docs['sources_verified'], 'sections': docs['sections_verified'],
            'documents': docs['links']['documents'], 'local_links': docs['links']['local_links'],
            'anchors': docs['links']['anchors'], 'failures': len(docs['failures'])
        },
        'source_data_audit': {'exit_code': actual['commands'][1]['exit_code'],
                              'checks_passed': audit['checks_passed'],
                              'checks_failed': audit['checks_failed']},
        'independent_retained_data_review': {
            'checks_passed': 51,
            'result': 'checkpoint-046-reviews/evidence/result.json'
        }
    },
    'independent_final_core_audit': {
        'result': binding(DEST / 'independent-review/result.json'),
        'closure': binding(DEST / 'independent-review/closure.json'),
        'command': closure['actual_successful_command'],
        'checks_passed': independent['checks_passed'], 'findings': independent['findings'],
        'scope': 'Published core and available evidence; appendix/final containing commit are outside this independent audit.',
        'independence_disclosure': independent['independence_disclosure'],
        'preserved_first_attempt': closure['preserved_audit_preparation_failure'],
        'window_closed_utc': closure['closed_utc']
    },
    'archives': independent['archives'],
    'all_727_members_hashes_crcs_and_restored_bytes_verified': True,
    'current_runtime_modules_identical_to_held_C035': 65,
    'prepared_capture': {
        'path': 'checkpoint-046-capture.py', 'bytes': 36992,
        'sha256': 'd5803f0249aae67047d4780a1a1f0d19c67663a5a1cc24b00c160d54d7e61276',
        'statically_reviewed': True, 'imported_or_executed': False,
        'measured_neutrality': None, 'diagnostic_size_sufficiency': None
    },
    'appendix_input_application': 'Every core byte remains unchanged during packaging. The appendix contains only JSON, raw command logs, actual commit bytes and scripts. No Markdown/HTML documentation input is added or changed after the actual documentation command. The containing appendix is verified for exact membership and hashes; no repeat product or checker run is inferred.',
    'retained_failures_and_limits': [
        'Source transport/authentication failures and original-byte recovery provenance remain in checkpoint-046-evidence/recovery. All 2441 parent files and original commit bytes were recovered; earlier Git history remains unavailable.',
        'One unattributed recovery fragment is preserved externally with its exact hash/mode/mtime receipt in the core. Its origin is unknown and it is excluded from source/publication.',
        'Initial capture codec/product-observer/size/ID-qualification defects and literal docstring plus signs were corrected before any capture execution; superseded source and preparation history remain in the core.',
        'First independent final-audit attempt exited 1 on an overly literal prose matcher. Only that assertion was corrected; exact failed script/log/inputs and successful replacement are retained, with the core unchanged.',
        'Historical no-capacity-eviction is a source-bound inference for key 1 entry through key 153 pre-cleanup only. It is not a directly observed internal mutation sequence or a theorem about current C035.',
        'Historical coefficient key (32768,129,14) is source-derived from native locals/domain, not a directly captured tuple. It is not relabeled as current.',
        'Boundary counts do not identify all coefficient keys, exact hits or internal event chronology. Instantaneous IDs/bit widths in future capture do not establish payload equality or lifetime.',
        'The degree-14 60-charge gross helper difference is a source-derived counterfactual, not measured savings, a full failed-tail cost or a complete candidate bound.',
        'Prepared capture has not been executed or imported. Actual neutrality, diagnostic-bound sufficiency and current locals remain unestablished.',
        'C033 original elapsed/provenance qualifications and C035 adverse diagnostic timing remain visible. No new product request, numerical candidate replay, benchmark, runtime regression, hosted job, main merge or release acceptance occurred.',
        'Original28 remains 24/28 with P11/P16/P23/L03 capped; C035 remains held. The complete R01-R12/Q01-Q22 release and full product goal remain open.'
    ],
    'product_requests': 0, 'runtime_changes': 0, 'hosted_jobs_dispatched': 0,
    'main_merges': 0, 'release_acceptance': False,
    'original28': {'passed': 24, 'total': 28, 'new_execution': False},
    'next_scope': 'checkpoint-046-next-scope.json'
}
metadata = BASE / 'checkpoint-046-validation.json'
write(metadata, record)
relative_dest = DEST.relative_to(REPO).as_posix()
relative_metadata = metadata.relative_to(REPO).as_posix()
subprocess.run(['git', 'add', '--', relative_dest, relative_metadata], cwd=REPO, check=True)
check = subprocess.run(['git', 'diff', '--cached', '--check'], cwd=REPO, capture_output=True)
(DEST / 'appendix-whitespace.stdout').write_bytes(check.stdout)
(DEST / 'appendix-whitespace.stderr').write_bytes(check.stderr)
record['appendix_whitespace_check'] = {'exit_code': check.returncode,
    'stdout': 'checkpoint-046-validation/appendix-whitespace.stdout',
    'stderr': 'checkpoint-046-validation/appendix-whitespace.stderr'}
if check.returncode:
    record['appendix_whitespace_qualification'] = 'Exact executed evidence is preserved byte-for-byte. Any nonzero whitespace check is disclosed in its raw log and is not reported as a pass.'
members = [binding(p) for p in sorted(DEST.rglob('*')) if p.is_file()]
record['appendix_member_files'] = len(members)
record['appendix_member_bytes'] = sum(x['bytes'] for x in members)
record['files'] = members
write(metadata, record)
subprocess.run(['git', 'add', '--', relative_dest, relative_metadata], cwd=REPO, check=True)
assert subprocess.run(['git', 'diff', '--cached', '--check'], cwd=REPO, capture_output=True).returncode == check.returncode
names = subprocess.check_output(['git', 'diff', '--cached', '--name-status'], cwd=REPO).decode().splitlines()
assert len(names) == len(members) + 1
for row in names:
    kind, name = row.split('\t')
    assert kind == 'A' and (name == relative_metadata or name.startswith(relative_dest + '/'))
    assert Path(name).suffix.lower() not in {'.md', '.html', '.htm'}
for path, entry in core_files.items():
    raw = (REPO / path).read_bytes()
    assert len(raw) == entry['size']
    assert hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == entry['sha']
plan_files = []
for row in names:
    name = row.split('\t')[1]
    p = REPO / name
    raw = p.read_bytes()
    mode = '100755' if p.stat().st_mode & 0o111 else '100644'
    plan_files.append({'path': name, 'mode': mode, 'type': 'blob',
        'sha': hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest(),
        'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
plan = {'parent': CORE, 'base_tree': TREE, 'intended_tree': git('write-tree'),
        'files': plan_files, 'core_files_preserved': 2503,
        'core_bytes_preserved': 501832579, 'new_files': len(plan_files),
        'new_bytes': sum(x['bytes'] for x in plan_files),
        'no_markdown_or_html_delta': True, 'whitespace_exit': check.returncode,
        'window_comment': 6425093159}
write(WORK / 'final-publication-plan.json', plan)
print(json.dumps({k:v for k,v in plan.items() if k != 'files'}, indent=2))
