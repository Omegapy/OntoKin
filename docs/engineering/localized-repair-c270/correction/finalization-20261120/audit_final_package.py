"""Independent final C270 handoff audit. Reads inputs; writes only own audit directory."""
from pathlib import Path, PurePosixPath
import collections
import hashlib
import io
import json
import os
import stat
import subprocess
import tempfile
import zipfile

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
REPO = ROOT / 'OntoKin'
NAME = 'OntoKin_C270_Correction_Finalization_Handoff_2026-11-20'
ARCHIVE = ROOT / 'deliverables' / (NAME + '.zip')
EXTERNAL = ARCHIVE.with_name(NAME + '_VERIFICATION.json')
MAIN = '0f90048b74b4cb69f2d5f058106c81967b13ae6d'
MERGE = '4d27756f1c503b430dd85219235778a1f78ef101'
CANDIDATE = '29e98cab1774629171152be3be68c14e39bb9c0e'
BASE = 'repository/docs/engineering/localized-repair-c270/correction/finalization-20261120/'
EXPECTED = {'bytes': 10963559, 'sha256': '4852a588a96bc9839234c9491b61497859011efc553a26518eadae655dd034cd'}
CHECKS = []
NESTED = []
COMMANDS = []
FRESH = Path(tempfile.mkdtemp(prefix='final-package-independent-', dir=OUT / 'fresh-extractions'))


def identify(data):
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def blob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def check(name, passed, evidence=None):
    CHECKS.append({'name': name, 'status': 'pass' if passed else 'fail', 'evidence': evidence})


def strict_json(data):
    def unique(pairs):
        obj = {}
        for key, value in pairs:
            if key in obj:
                raise ValueError('Duplicate JSON key: ' + key)
            obj[key] = value
        return obj
    return json.loads(data, object_pairs_hook=unique)


def git(*args):
    proc = subprocess.run(['git', '-C', str(REPO), *args], env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'), capture_output=True)
    COMMANDS.append({'argv': ['git', *args], 'returncode': proc.returncode})
    if proc.returncode:
        raise RuntimeError(proc.stderr.decode())
    return proc.stdout


def read_zip(data, label, extract=None, recurse=True):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        infos = archive.infolist()
        names = [x.filename for x in infos]
        duplicates = [n for n, count in collections.Counter(names).items() if count != 1]
        unsafe = [n for n in names if not n or PurePosixPath(n).is_absolute() or '\\' in n or ':' in n
                  or '\0' in n or any(p in ('.', '..') for p in n.split('/'))]
        special = [x.filename for x in infos if stat.S_IFMT(x.external_attr >> 16) not in (0, stat.S_IFREG, stat.S_IFDIR)]
        check(label + ': CRC', archive.testzip() is None)
        check(label + ': safe unique regular paths', not (duplicates or unsafe or special),
              {'duplicates': duplicates, 'unsafe': unsafe, 'special': special})
        if duplicates or unsafe or special:
            raise ValueError('Unsafe ZIP: ' + label)
        contents = {x.filename: archive.read(x) for x in infos if not x.is_dir()}
        if extract is not None:
            extract.mkdir(parents=True, exist_ok=True)
            for name, content in contents.items():
                target = extract / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
            actual = {str(p.relative_to(extract)): identify(p.read_bytes()) for p in extract.rglob('*') if p.is_file()}
            check(label + ': exact fresh extraction', actual == {n: identify(d) for n, d in contents.items()})
        if recurse:
            for name, content in contents.items():
                if name.endswith('.zip'):
                    nested_label = label + '::' + name
                    nested = read_zip(content, nested_label)
                    NESTED.append({'path': nested_label, **identify(content), 'member_count': len(nested)})
        return contents


def main():
    raw = ARCHIVE.read_bytes()
    identity = identify(raw)
    external = strict_json(EXTERNAL.read_bytes())
    check('frozen archive identity matches Director', identity == EXPECTED, identity)
    check('frozen archive identity matches builder verification', identity == {k: external['archive'][k] for k in ('bytes', 'sha256')})
    contents = read_zip(raw, 'final ZIP', FRESH / 'outer')
    actual = {n: identify(data) for n, data in contents.items()}
    manifest = strict_json(contents['MANIFEST-SHA256.json'])
    check('outer manifest exact payload inventory', set(manifest) == set(contents) - {'MANIFEST-SHA256.json'})
    check('outer manifest every byte count and SHA256', all(actual.get(n) == ident for n, ident in manifest.items()))
    check('external member inventory equals all actual members', actual == external['member_inventory'])
    check('external counts match', len(contents) == external['member_count'] == 437 and len(manifest) == external['manifest_payload_count'] == 436)
    required = ['README-START-HERE.md', 'CHECKPOINT.json', 'HANDOFF.md', 'NEXT-TASK.md', 'RECOVERY-STATUS.md',
                'PROMPT-1-CONTINUE.md', 'PROMPT-2-RECOVER.md', 'HISTORICAL-DEPENDENCIES.json', 'MANIFEST-SHA256.json']
    check('required root files present', all(x in contents for x in required))
    sources = strict_json(contents['SNAPSHOT-SOURCES.json'])
    tree_cache = {}
    for revision in {x['revision'] for x in sources['files']}:
        tree_cache[revision] = {}
        for raw_entry in git('ls-tree', '-rz', revision).split(b'\0'):
            if raw_entry:
                meta, path = raw_entry.split(b'\t', 1)
                mode, kind, sha = meta.decode().split()
                tree_cache[revision][path.decode()] = {'mode': mode, 'kind': kind, 'git_blob': sha}
    source_results = []
    for entry in sources['files']:
        data = contents.get(entry['package_path'])
        source = tree_cache[entry['revision']].get(entry['repository_path'])
        passed = data is not None and identify(data) == {k: entry[k] for k in ('bytes', 'sha256')} \
            and blob(data) == entry['git_blob'] and source is not None \
            and source['git_blob'] == entry['git_blob'] and source['mode'] == entry['mode']
        source_results.append({'package_path': entry['package_path'], 'revision': entry['revision'],
            'repository_path': entry['repository_path'], 'mode': entry['mode'], 'git_blob': entry['git_blob'],
            'status': 'pass' if passed else 'fail'})
    check('all 356 snapshot source revisions paths blobs modes and bytes', len(source_results) == 356 and all(r['status'] == 'pass' for r in source_results))
    mapped = [r['package_path'] for r in source_results]
    check('snapshot paths unique', len(mapped) == len(set(mapped)))
    repositories = {n for n in contents if n.startswith(('repository/', 'historical/reconciled-handoff/repository/'))}
    check('all repository payloads mapped', repositories <= set(mapped), sorted(repositories - set(mapped)))
    check('all 280 current repository snapshots are actual main', len([r for r in source_results if r['package_path'].startswith('repository/')]) == 280
          and all(r['revision'] == MAIN for r in source_results if r['package_path'].startswith('repository/')))
    check('external snapshot count agrees', external['git_snapshot_bytes']['count'] == len(source_results))
    checkpoint = strict_json(contents['CHECKPOINT.json'])
    main_tree = git('rev-parse', MAIN + '^{tree}').decode().strip()
    merge_tree = git('rev-parse', MERGE + '^{tree}').decode().strip()
    check('main checkpoint source tree', sources['main_revision'] == checkpoint['observed_main']['sha'] == MAIN
          and sources['main_tree'] == checkpoint['observed_main']['tree'] == main_tree)
    check('main parent is verified merge', git('rev-parse', MAIN + '^').decode().strip() == MERGE)
    integration = strict_json(contents[BASE + 'INTEGRATION.json'])
    check('merge parents and reviewed tree exact', git('show', '-s', '--format=%P', MERGE).decode().strip().split() == integration['parents']
          and integration['reviewed_candidate'] == CANDIDATE and integration['merge_commit'] == MERGE
          and integration['merge_tree'] == integration['reviewed_tree'] == merge_tree
          and git('rev-parse', CANDIDATE + '^{tree}').decode().strip() == merge_tree)
    check('candidate history retained in actual main', not git('merge-base', '--is-ancestor', CANDIDATE, MAIN))
    preserve = strict_json(contents['SOURCE-PRESERVATION.json'])
    source_archive = ROOT / 'source_handoffs' / preserve['source_archive']['filename']
    check('historical input archive identity', identify(source_archive.read_bytes()) == {k: preserve['source_archive'][k] for k in ('bytes', 'sha256')})
    with zipfile.ZipFile(source_archive) as historical:
        prior = {x.filename: historical.read(x) for x in historical.infolist() if not x.is_dir()}
    prefix = preserve['historical_prefix']
    expected_history = {name: identify(data) for name, data in prior.items()}
    check('all 116 historical payloads byte exact', len(prior) == 116
          and {n[len(prefix):]: identify(d) for n, d in contents.items() if n.startswith(prefix)} == expected_history
          and all(contents.get(prefix + n) == d for n, d in prior.items()))
    check('historical source inventory exact', preserve['preserved_source_files'] == expected_history)
    deps = strict_json(contents['HISTORICAL-DEPENDENCIES.json'])
    old_deps = strict_json(prior['HISTORICAL-DEPENDENCIES.json'])
    check('C262 identity and metadata unchanged', deps['C262'] == old_deps['C262'])
    unique = strict_json((OUT / 'PRESERVED-MANIFEST.json').read_bytes())
    unique_results = []
    for entry in unique['files']:
        path = preserve['unique_ancillary_prefix'] + entry['path']
        data = (OUT / entry['path']).read_bytes()
        passed = contents.get(path) == data and identify(data) == {k: entry[k] for k in ('bytes', 'sha256')}
        unique_results.append({'path': path, **identify(data), 'passed': passed})
    check('all 16 unique ancillary files exactly preserved', len(unique_results) == 16 and sum(r['bytes'] for r in unique_results) == 108037
          and all(r['passed'] for r in unique_results) and preserve['unique_ancillary_files'] == unique)
    local_results = []
    for entry in preserve['additional_local_evidence']:
        data = Path(entry['source']).read_bytes()
        passed = contents.get(entry['package_path']) == data and identify(data) == {k: entry[k] for k in ('bytes', 'sha256')}
        local_results.append({'source': entry['source'], 'package_path': entry['package_path'], **identify(data), 'passed': passed})
    check('all additional source records and final review preserved', all(r['passed'] for r in local_results), len(local_results))
    main_checks = strict_json(contents[BASE + 'ACTUAL-MAIN-CHECKS.json'])
    main_manifest = strict_json(contents[BASE + 'ACTUAL-MAIN-MANIFEST.json'])
    main_archive_data = contents[BASE + 'ACTUAL-MAIN-EVIDENCE.zip']
    check('actual-main nested archive exact identity', identify(main_archive_data) == {k: main_checks['archive'][k] for k in ('bytes', 'sha256')}
          and main_checks['archive'] == main_manifest['archive'])
    main_evidence = read_zip(main_archive_data, 'actual-main evidence ZIP', FRESH / 'actual-main', recurse=False)
    main_payloads = {r['path']: {k: r[k] for k in ('bytes', 'sha256')} for r in main_manifest['payloads']}
    check('actual-main all 39 payloads exact manifest', len(main_evidence) == 39 and main_payloads == {n: identify(d) for n, d in main_evidence.items()})
    check('actual-main manifest source binding', main_checks['source_revision'] == main_manifest['source_revision'] == MERGE
          and main_checks['source_tree'] == main_manifest['source_tree'] == merge_tree)
    check('actual-main report references match bytes', all(identify(main_evidence[r['archive_entry']]) == {k: r[k] for k in ('bytes', 'sha256')} for r in main_checks['reports']))
    cohort = strict_json(main_evidence['affected-cohort/CHECKS.json'])
    h16 = strict_json(main_evidence['h16/RESULTS.json'])
    distinctions = strict_json(main_evidence['distinctions/CHECKS.json'])
    check('actual-main scoped result and source consistency', cohort['source_before']['commit'] == cohort['source_after']['commit'] == h16['source_revision'] == distinctions['source_revision'] == MERGE
          and cohort['passed'] and cohort['complete'] and h16['passed'] and distinctions['passed']
          and cohort['total_methods'] == 282 and cohort['completed_check_count'] == 12 and len(h16['cases']) == 5 and distinctions['methods'] == 8)
    check('affected cohort logged outputs exact', all(identify(main_evidence['affected-cohort/' + row['log']['path']]) == {k: row['log'][k] for k in ('bytes', 'sha256')}
          and row['result'] == 'passed' and row['exit_code'] == 0 for row in cohort['checks']))
    routine_info = preserve['interrupted_routine']
    routine_data = contents[routine_info['path']]
    check('interrupted routine ZIP declared identity', identify(routine_data) == {k: routine_info[k] for k in ('bytes', 'sha256')})
    routine = read_zip(routine_data, 'interrupted routine ZIP', FRESH / 'routine', recurse=False)
    check('interrupted routine six payloads exact inventory and hashes', len(routine) == 6
          and {n: identify(d) for n, d in routine.items()} == routine_info['members'])
    check('interrupted routine equals original raw history', all(prior['session-evidence/routine-interrupted/' + n] == d for n, d in routine.items()))
    check('historical broad status is still running with unknown final result', strict_json(routine['summary.json'])['status'] == 'running'
          and 'unknown' in strict_json(routine['RECOVERY.json'])['driver_invocation_completed'])
    record_checks = strict_json(contents['session-evidence/published-source-record-checks/CHECKS.json'])
    check('published-source record checks bind main with complete hashed logs', record_checks['source_revision'] == MAIN
          and record_checks['source_tree'] == main_tree and record_checks['result'] == 'passed'
          and all(r['exit_code'] == 0 and identify(contents['session-evidence/published-source-record-checks/' + r['log']['path']]) ==
                  {k: r['log'][k] for k in ('bytes', 'sha256')} for r in record_checks['checks']))
    state_review = strict_json(contents['session-evidence/final-state-review/FINAL-STATE-REVIEW.json'])
    check('final-state acceptance exact source and no findings', state_review['source_revision'] == MAIN
          and state_review['passed'] and state_review['check_count'] == 169 and not state_review['mandatory_findings'])
    gates = {'R01': 'done', 'R02': 'done', 'R03': 'done', 'R04': 'done', 'R05': 'not_done'}
    task = strict_json(contents['repository/docs/workflow/tasks/C270/task.json'])
    check('R01-R04 done and only R05 pending throughout records', checkpoint['requirements_at_freeze'] == gates
          and integration['gate_state'] == gates and state_review['gate_state'] == gates
          and {r['id']: r['status'] for r in task['requirements']} == gates)
    check('parent and issue correctly remain open at freeze', checkpoint['parent_status'] == task['status'] == 'in_progress'
          and checkpoint['scope_issue']['state'] == 'open' and checkpoint['first_unmet_gate'] == 'R05'
          and checkpoint['delivery']['status'] == 'save_pending_at_freeze')
    check('future final receipt correctly external', 'repository/' + checkpoint['delivery']['external_receipt'] not in contents)
    prompts = []
    for name, standalone in [('PROMPT-1-CONTINUE.md', 'OntoKin_C270_Finalization_Prompt_1_Continue_2026-11-20.md'),
                             ('PROMPT-2-RECOVER.md', 'OntoKin_C270_Finalization_Prompt_2_Recover_2026-11-20.md')]:
        path = ROOT / 'deliverables' / standalone
        data = path.read_bytes()
        passed = data == contents[name]
        prompts.append({'archive_path': name, 'standalone_path': str(path), **identify(data), 'passed': passed})
        check(name + ': standalone exact', passed)
    narratives = {n: contents[n].decode() for n in ['README-START-HERE.md', 'HANDOFF.md', 'NEXT-TASK.md', 'RECOVERY-STATUS.md', 'PROMPT-1-CONTINUE.md', 'PROMPT-2-RECOVER.md']}
    check('current instructions explicitly name R05 and live receipt', all('R05' in t and 'DELIVERY.json' in t for t in narratives.values()))
    check('both prompts stop after live completion or delivery', all('If' in narratives[n] and 'stop/await' in narratives[n]
          and 'Do not' in narratives[n] and 'milestone' in narratives[n] for n in ('PROMPT-1-CONTINUE.md', 'PROMPT-2-RECOVER.md')))
    check('current narratives retain historical unknown outcome', all('unknown' in t and ('broad' in t or 'interrupted' in t) for t in narratives.values()))
    check('manual scope/readability review approved', True, {'inspected_in_full': list(narratives),
          'finding': 'Instructions restrict continuation to live receipt reconciliation and remaining R05 delivery/closure, preserve historical unknowns, and explicitly bar another milestone. No broader qualification or successful SiteRef endpoint claim.',
          'placeholder_note': 'Reusable prompts intentionally contain a confirmed-link insertion placeholder; exact repository receipt path is supplied.'})
    passed = all(r['status'] == 'pass' for r in CHECKS)
    result = {'schema': 'ontokin.c270.final-package-review/1', 'reviewer': '/root/recovery_audit',
        'review_time_clock_observation': '2026-11-20T21:28:08Z', 'scope': 'Independent final frozen archive approval; no behavioral rerun or remote/save mutation',
        'archive': {'path': str(ARCHIVE), **identity}, 'external_verification': {'path': str(EXTERNAL), **identify(EXTERNAL.read_bytes())},
        'source_main': MAIN, 'source_tree': main_tree, 'merge_commit': MERGE, 'reviewed_candidate': CANDIDATE,
        'passed': passed, 'verdict': 'approved_for_R05_save_and_external_receipt' if passed else 'changes_required',
        'audit_command': ['python3', '-B', str(Path(__file__).resolve())],
        'script_identity': identify(Path(__file__).read_bytes()),
        'check_count': len(CHECKS), 'checks': CHECKS, 'mandatory_findings': [r for r in CHECKS if r['status'] != 'pass'],
        'source_snapshots': source_results, 'nested_archives': NESTED, 'ancillary_records': unique_results,
        'additional_local_evidence': local_results, 'standalone_prompts': prompts, 'commands': COMMANDS,
        'fresh_extraction': str(FRESH), 'limits': ['No independent save operation or destination read; R05 remains pending until Director confirms save and separate receipt.',
            'Historical broad-driver outcome and global old-worker termination remain unknown.',
            'Finite C270 archive/source/evidence approval; no full product or H20/H22/H24 qualification.']}
    report = OUT / 'FINAL-PACKAGE-REVIEW.json'
    report.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'passed': passed, 'check_count': len(CHECKS), 'findings': result['mandatory_findings'],
        'source_snapshots': len(source_results), 'nested_archives_recursively_checked': len(NESTED),
        'archive': result['archive'], 'output': str(report)}, indent=2))


if __name__ == '__main__':
    main()
