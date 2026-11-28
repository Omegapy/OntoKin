#!/usr/bin/env python3
"""Read-only C271 handoff integrity/provenance audit; no product execution."""
from __future__ import annotations

import collections
import datetime as dt
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import stat
import subprocess
import sys
import zipfile

BASE = Path('/workspace/scratch/cce28e2b3ca4')
OUT = BASE / 'reviews/c271-final-package-audit'
REPO = BASE / 'OntoKin'
ARCHIVE = BASE / 'artifacts/OntoKin_C271_Control_Candidate_Handoff_2026-11-20.zip'
SOURCE = 'e0b73f7d6ce49631e598d1378a0ddba717726524'
TREE = '9ab0d4dfcb21735fed4c019f85f8f450ebfaa7b4'
MAIN = 'e1a48f7d0635e9aa4f4b6d6a586e7305eb81999d'
MAIN_TREE = '9345594c980f121fae2f087b40e4c78adb8f7925'
CODE = '067392f2b5f592a5c3104fa8848cc0030ba1117b'
CODE_TREE = '21ab07914931495d6bee70591a70ff2d8bcabb84'
ZIP_SHA = '9bdb8ec134fbf8facc1b1f52aa9b7171de16f35593ddf7ad61930e521f4495df'
ZIP_BYTES = 12003931
OLD_SHA = '4852a588a96bc9839234c9491b61497859011efc553a26518eadae655dd034cd'
OLD_BYTES = 10963559
CONTROL = 'repository/docs/engineering/localized-repair-c271/'
REVIEW = 'session-evidence/candidate-review/'
REQUIRED_ROOTS = {
    'CHECKPOINT.json', 'HANDOFF.md', 'HISTORICAL-DEPENDENCIES.json',
    'MANIFEST-SHA256.json', 'NEXT-TASK.md', 'PROMPT-1-CONTINUE.md',
    'PROMPT-2-RECOVER.md', 'README-START-HERE.md', 'RECOVERY-STATUS.md',
}
REQUIRED_REPO = {
    'CHATGPT-START-HERE.md', 'AGENTS.md', 'GOAL.md', 'STATUS.md', 'ROLE.md',
    'docs/README.md', 'docs/workflow/registry.json', 'docs/workflow/CURRENT.json',
    'docs/workflow/PROTOCOL.md', 'docs/workflow/HANDOFF.md',
    'docs/workflow/BROWSER-PROMPTS.md', 'docs/workflow/prompts/CONTINUE.md',
    'docs/workflow/prompts/RECOVER.md', 'docs/workflow/templates/WORKER.md',
    'docs/workflow/templates/SESSION.md', 'docs/workflow/memory.json',
    'docs/workflow/knowledge.json', 'docs/workflow/KNOWLEDGE.md',
    'docs/workflow/tasks/C271/task.json', 'docs/workflow/tasks/C271/REQUIREMENTS.md',
    'docs/workflow/tasks/C271/PLAN.md', 'docs/workflow/tasks/C271/SESSION.md',
    '.agents/skills/ontokin-session/SKILL.md',
    '.agents/skills/ontokin-delivery/SKILL.md',
    '.agents/skills/ontokin-learning/SKILL.md',
    'docs/engineering/localized-repair-c260/CONTRACT.md',
    'docs/engineering/localized-repair-c260/CONTROL-PLAN.md',
    'docs/engineering/localized-repair-c260/INPUTS.json',
    'docs/engineering/localized-repair-c269/AUDIT.md',
    'docs/engineering/localized-repair-c269/COVERAGE.json',
    'docs/language-design/OK-LANG-002-pinned-modules-and-keyed-assembly-construction.md',
}
EXPECTED_IDENTITIES = {
    CONTROL + 'control/EXPECTED.json': (27400, '0b8da6eab52323e8092c348fabad0d8d77247552e4eb5e3a1ffdc17266d12522'),
    CONTROL + 'run_h22_control.py': (15910, '358c3a50a5b437d0b765ff9547cc1c4611bcbdbbff95c31a22cccae7050c2480'),
    CONTROL + 'evidence/control-candidate/RESULTS.json': (15891, 'ea516696267931321ab1d63f4fb420f31f6de28addb537dd9b7479329bdd6eb7'),
    CONTROL + 'evidence/control-candidate/RAW-EVIDENCE.zip': (123257, '24f8b99ca5682dbc23f93f7f4c856e211c98eb82124fe93475848196b41376b4'),
    CONTROL + 'evidence/control-candidate/driver.log': (107, '5b0d53400b2dbe44390f77e364eabb8024a514e9f53f877724c2e59bd6fe526a'),
    CONTROL + 'evidence/control-candidate/EXECUTION-RECEIPT.json': (1571, '1a4949b89b670a7752a5edd59f06ee4daf8742c0d4f63a69756321a82c52d817'),
    REVIEW + 'CANDIDATE-AUDIT.json': (77347, 'a9b6a51d42f4aea73fad6f66fc157bfd2c0817e2746dfecbcdb6819f31236ed0'),
    REVIEW + 'CANDIDATE-REVIEW.md': (2316, '479b8460efbd8320bd6c3325ebcad26bb5d440096c503fbc88b70d10862c2c9a'),
    REVIEW + 'PUBLICATION-REVIEW.json': (7777, 'b9017e2dd1a6214a01500f5571aac95d49c63d0738f74c3bcd5939532f71c317'),
    REVIEW + 'PUBLICATION-REVIEW.md': (2801, 'd2e2da9f1998814a5e7409b722caae4ac503f93807eeb40b640e22c73181ca41'),
    REVIEW + 'FINAL-STATE-REVIEW.json': (12347, '63cd33a6044ce4f82a712c87e5262a91c87e37b0690883a6f9b08da3f25c8ff5'),
    REVIEW + 'FINAL-STATE-REVIEW.md': (1974, '0147b469485927a313235443bf1d43c1117ef74514ec8eacd2e5dd54f39f3eb0'),
    REVIEW + 'FINAL-STATE-OBSERVATIONS.json': (12168, '9458712da9cd72d3a6116902af2b920ebf6c0999b2868094b6c03348a38a75d4'),
    'session-evidence/source-audit/AUDIT.json': (628595, 'de63e29d5200601d6013b722747ec95347838acf337cad4e166ef139288ec476'),
    'session-evidence/source-audit/FINAL-CLOSEOUT-VERIFICATION.json': (34207, '6e5ef3f26a5520145a08c72b60723a20bcb7f710fed0da4023ab6439077f00ec'),
    'session-evidence/final-source-record-checks/CHECKS.json': (1783, '8c0776c6bdc82ad6368ce7871b69a567b9855b942fbacf1e1d3dfbe545c08c2c'),
}
PROMPTS = {
    'PROMPT-1-CONTINUE.md': ('OntoKin_C271_Prompt_1_Continue_2026-11-20.md', 3559, '60252a3177831711fdbc34c60d735b16cf31162bd89efa250269d9275bab893d'),
    'PROMPT-2-RECOVER.md': ('OntoKin_C271_Prompt_2_Recover_2026-11-20.md', 3785, '09192571ddcaae69ad91fbb51872cc18087a973bd4fd551075fde43f62b93c89'),
}

checks = []
def check(group, name, passed, **evidence):
    checks.append({'group': group, 'name': name, 'passed': bool(passed), **evidence})

def sha(b):
    return hashlib.sha256(b).hexdigest()

def identity(b):
    return {'bytes': len(b), 'sha256': sha(b)}

def duplicate_free_object(pairs):
    d = {}
    for k, v in pairs:
        if k in d:
            raise ValueError('Duplicate JSON key: ' + k)
        d[k] = v
    return d

def parse(b):
    return json.loads(b, object_pairs_hook=duplicate_free_object)

def safe_name(name):
    p = PurePosixPath(name)
    return bool(name) and not p.is_absolute() and not PureWindowsPath(name).drive and '\\' not in name and '\x00' not in name and all(x not in ('', '.', '..') for x in name.split('/')) and str(p) == name

def git(*args):
    return subprocess.check_output(['git', '-C', str(REPO), *args], env={**os.environ, 'GIT_OPTIONAL_LOCKS': '0'})

def tree_map(rev):
    result = {}
    for row in git('ls-tree', '-r', '-z', rev).split(b'\0'):
        if row:
            head, path = row.split(b'\t', 1)
            mode, typ, blob = head.decode().split(' ')
            result[path.decode()] = {'git_mode': mode, 'git_type': typ, 'git_blob': blob}
    return result

def summary_checks(group, rows, expected):
    check(group, 'recorded_check_count_and_pass', len(rows) == expected and all(x['passed'] is True for x in rows), count=len(rows), failed=sum(x['passed'] is not True for x in rows))

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    data = ARCHIVE.read_bytes()
    archive_identity = {'path': str(ARCHIVE), 'filename': ARCHIVE.name, **identity(data)}
    check('archive', 'frozen_identity', len(data) == ZIP_BYTES and sha(data) == ZIP_SHA, **archive_identity)
    prompt_identities = {}
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        infos = z.infolist()
        names = z.namelist()
        name_set = set(names)
        check('archive', 'member_count_and_no_duplicates', len(names) == 160 and len(name_set) == len(names), members=len(names))
        check('archive', 'no_casefold_path_collisions', len({n.casefold() for n in names}) == len(names))
        check('archive', 'CRC', z.testzip() is None)
        for info in infos:
            mode = info.external_attr >> 16
            check('safe_path', info.filename, safe_name(info.filename) and not info.is_dir() and stat.S_ISREG(mode) and not info.flag_bits & 1, unix_mode=oct(mode), compressed_bytes=info.compress_size, bytes=info.file_size)
        if any(not c['passed'] for c in checks if c['group'] in ('archive', 'safe_path')):
            raise ValueError('Unsafe or changed archive; extraction refused')
        payload = {n: z.read(n) for n in names}
        js = lambda n: parse(payload[n])
        roots = {n for n in names if '/' not in n}
        check('inventory', 'required_roots_exact', roots == REQUIRED_ROOTS, observed=sorted(roots))
        check('inventory', 'required_startup_task_contract_roots', {'repository/' + p for p in REQUIRED_REPO}.issubset(name_set), required_count=len(REQUIRED_REPO))
        manifest = js('MANIFEST-SHA256.json')
        files = manifest['files']
        declared = [e['path'] for e in files]
        check('manifest', 'exact_inventory', len(files) == 159 and len(set(declared)) == len(declared) and set(declared) == name_set - {'MANIFEST-SHA256.json'} and manifest['excludes'] == ['MANIFEST-SHA256.json'], payloads=len(files))
        check('manifest', 'algorithm', manifest['hash_algorithm'].lower().replace('-', '') == 'sha256')
        for e in files:
            b = payload[e['path']]
            check('manifest_entry', e['path'], identity(b) == {'bytes': e['bytes'], 'sha256': e['sha256']}, **identity(b))

        extraction = OUT / 'fresh-extraction'
        extraction.mkdir(exist_ok=False)
        for name, b in payload.items():
            dest = extraction / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(b)
        extracted = {str(p.relative_to(extraction)): p for p in extraction.rglob('*') if p.is_file()}
        check('extraction', 'exact_fresh_inventory', set(extracted) == name_set, count=len(extracted), extraction_directory=str(extraction))
        for name, p in sorted(extracted.items()):
            check('extracted_entry', name, p.read_bytes() == payload[name])

        snap = js('metadata/SNAPSHOT-SOURCES.json')
        sessions = js('metadata/SESSION-SOURCES.json')
        preserved = js('metadata/PRESERVED-INPUTS.json')
        ext = js('metadata/EXTERNAL-SOURCE-DEPENDENCIES.json')
        config = js('recovery/final-package-config.json')
        check('source', 'source_metadata', snap['source_revision'] == SOURCE and snap['source_tree'] == TREE and config['source_revision'] == SOURCE and config['source_tree'] == TREE)
        maps = {r: tree_map(r) for r in (SOURCE, MAIN, CODE)}
        for r, t in ((SOURCE, TREE), (MAIN, MAIN_TREE), (CODE, CODE_TREE)):
            observed = git('rev-parse', r + '^{tree}').decode().strip()
            check('source', 'tree:' + r, observed == t, observed_tree=observed)
        snapshot_paths = [e['archive_path'] for e in snap['entries']]
        session_paths = [e['archive_path'] for e in sessions['entries']]
        preserved_paths = [e['archive_path'] for e in preserved['entries']]
        check('source', 'snapshot_counts', len(snapshot_paths) == 88 and len(set(snapshot_paths)) == 88 and collections.Counter(e['git_revision'] for e in snap['entries']) == {SOURCE: 85, MAIN: 3})
        selected = set(config['snapshot_paths'])
        for p in maps[SOURCE]:
            if any(p == prefix or p.startswith(prefix.rstrip('/') + '/') for prefix in config['snapshot_prefixes']):
                selected.add(p)
        expected_snapshot_paths = {'repository/' + p for p in selected} | {e['archive_path'] for e in config['additional_git_snapshots']}
        check('source', 'complete_declared_git_selection', set(snapshot_paths) == expected_snapshot_paths, selected_candidate_paths=len(selected))
        for e in snap['entries']:
            rev, path = e['git_revision'], e['git_path']
            b = git('cat-file', 'blob', rev + ':' + path)
            tree_entry = maps[rev].get(path)
            blob = hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest()
            role = ('repository/' + path == e['archive_path'] and rev == SOURCE) or ('observed-main/' + path == e['archive_path'] and rev == MAIN)
            check('git_snapshot', e['archive_path'], b == payload[e['archive_path']] and identity(b) == {'bytes': e['bytes'], 'sha256': e['sha256']} and blob == e['git_blob'] and tree_entry == {'git_mode': e['git_mode'], 'git_type': 'blob', 'git_blob': e['git_blob']} and role, git_revision=rev, git_path=path, git_blob=blob, git_mode=e['git_mode'], **identity(b))
        check('session', 'session_count_and_unique_paths', len(session_paths) == 58 and len(set(session_paths)) == 58)
        expected_session = {e['archive_path'] for e in config['extra_files']}
        for directory in config['extra_directories']:
            local = Path(directory['local_path'])
            expected_session.update(directory['archive_prefix'] + '/' + str(p.relative_to(local)) for p in local.rglob('*') if p.is_file())
        check('session', 'complete_declared_session_selection', set(session_paths) == expected_session, count=len(expected_session))
        for e in sessions['entries']:
            local = Path(e['local_source'])
            b = local.read_bytes()
            check('session_source', e['archive_path'], b == payload[e['archive_path']] and identity(b) == {'bytes': e['bytes'], 'sha256': e['sha256']} and e['source_kind'] == 'session_file_not_git_snapshot' and local.is_relative_to(BASE), local_source=str(local), source_kind=e['source_kind'], **identity(b))
        check('provenance', 'disjoint_origin_sets', not(set(snapshot_paths)&set(session_paths)) and not(set(snapshot_paths)&set(preserved_paths)) and not(set(session_paths)&set(preserved_paths)))
        derived = name_set - set(snapshot_paths) - set(session_paths) - set(preserved_paths)
        expected_derived = REQUIRED_ROOTS | {'metadata/SNAPSHOT-SOURCES.json', 'metadata/SESSION-SOURCES.json', 'metadata/PRESERVED-INPUTS.json', 'metadata/EXTERNAL-SOURCE-DEPENDENCIES.json'}
        check('provenance', 'all_payloads_classified', derived == expected_derived, derived_paths=sorted(derived))
        check('provenance', 'audit_outside_frozen_sources', all('c271-final-package-audit' not in e['local_source'] for e in sessions['entries']))

        external_paths = [e['git_path'] for e in ext['entries']]
        expected_external = {p for p in maps[SOURCE] if any(p == pre or p.startswith(pre.rstrip('/') + '/') for pre in config['external_source_prefixes'])}
        check('online_dependencies', 'exact_pinned_inventory', len(external_paths) == 1156 and len(set(external_paths)) == 1156 and set(external_paths) == expected_external and all(e['git_revision'] == SOURCE for e in ext['entries']), count=len(external_paths), boundary=ext['boundary'])
        for e in ext['entries']:
            expected_url = 'https://github.com/Omegapy/OntoKin/blob/' + SOURCE + '/' + e['git_path']
            check('online_dependency', e['git_path'], maps[SOURCE].get(e['git_path']) == {'git_mode': e['git_mode'], 'git_type': 'blob', 'git_blob': e['git_blob']} and e['url'] == expected_url, git_revision=e['git_revision'], git_blob=e['git_blob'], git_mode=e['git_mode'])

        old_path = BASE / 'source_handoff/OntoKin_C270_Correction_Finalization_Handoff_2026-11-20.zip'
        old = payload['historical/prior-development-handoff.zip']
        check('historical', 'untouched_nested_C270', old == old_path.read_bytes() and len(old) == OLD_BYTES and sha(old) == OLD_SHA, local_source=str(old_path), **identity(old))
        check('historical', 'preserved_inputs_exact', len(preserved['entries']) == 1 and preserved['entries'][0] == {'archive_path': 'historical/prior-development-handoff.zip', 'bytes': OLD_BYTES, 'sha256': OLD_SHA, 'library_file_id': 'libfile_fde3_f-a959b432b8c881918c0ef4ab596c8a8f_2ab2a24d43748191957f9bcc356b59de'})
        historical = js('HISTORICAL-DEPENDENCIES.json')
        with zipfile.ZipFile(io.BytesIO(old)) as oz:
            old_historical = parse(oz.read('HISTORICAL-DEPENDENCIES.json'))
            check('historical', 'C262_identity_retained', historical['C262'] == old_historical['C262'], identity=historical['C262'])
        old_audit = js('session-evidence/source-audit/AUDIT.json')
        check('historical', 'prior_intake_audit_retained', old_audit['verdict'] == 'passed' and len(old_audit['checks']) == 1703 and not old_audit['failed_checks'] and all(e['passed'] for e in old_audit['checks']), prior_audit_checks=1703, scope='Retained completed source audit; historical commands and nested audit not rerun')
        check('historical', 'prior_attempt_failure_preserved', 'session-evidence/source-audit/ATTEMPT-01-AUDIT.json' in name_set and any(not c['passed'] for c in js('session-evidence/source-audit/ATTEMPT-01-AUDIT.json')['checks']))
        for name, (size, digest) in EXPECTED_IDENTITIES.items():
            check('reviewed_identity', name, len(payload[name]) == size and sha(payload[name]) == digest, **identity(payload[name]))
        for name, (standalone, size, digest) in PROMPTS.items():
            p = BASE / 'artifacts' / standalone
            b = p.read_bytes()
            prompt_identities[name] = {'path': str(p), 'filename': standalone, 'archive_member': name, **identity(b)}
            check('prompt', name, b == payload[name] and len(b) == size and sha(b) == digest, **prompt_identities[name])

        result = js(CONTROL + 'evidence/control-candidate/RESULTS.json')
        receipt = js(CONTROL + 'evidence/control-candidate/EXECUTION-RECEIPT.json')
        expected_source = {'commit': CODE, 'dirty_before': '', 'tree': CODE_TREE}
        check('execution_evidence', 'frozen_source_and_counts', result['source'] == expected_source and result['input_cases_planned'] == 6 and result['interface_calls_planned'] == result['interface_calls_executed'] == 18 and result['checks_passed'] == 1042 and result['checks_failed'] == 0 and result['passed'] is True and not result['failed_checks'] and result['error'] is None)
        check('execution_evidence', 'six_positive_twelve_exact_refusals', len(result['calls']) == 18 and sum(c['outcome'] == 'success' and c['refusal_code'] is None for c in result['calls']) == 6 and sum(c['refusal_code'] == 'MALFORMED' for c in result['calls']) == 12 and all(c['outcome'] == c['expected']['outcome'] and c['refusal_code'] == c['expected']['refusal_code'] for c in result['calls']))
        check('execution_evidence', 'exact_invocation_receipt', receipt['source'] == expected_source and receipt['exit_code'] == 0 and receipt['argv'][1] == '-B' and receipt['exact_invocation'] == 'python3 -B docs/engineering/localized-repair-c271/run_h22_control.py --output /workspace/scratch/cce28e2b3ca4/c271-run-01 --phase C271-P01-control-candidate > /workspace/scratch/cce28e2b3ca4/c271-run-01-driver.log 2>&1')
        for k in ('driver_log', 'results'):
            e = receipt[k]
            b = payload[CONTROL + 'evidence/control-candidate/' + e['path']]
            check('execution_receipt', k, identity(b) == {'bytes': e['bytes'], 'sha256': e['sha256']})
        raw = payload[CONTROL + 'evidence/control-candidate/RAW-EVIDENCE.zip']
        with zipfile.ZipFile(io.BytesIO(raw)) as rz:
            rnames = rz.namelist()
            check('raw_archive', 'integrity_inventory_paths', len(rnames) == len(set(rnames)) == 27 and rz.testzip() is None and all(safe_name(n) for n in rnames))
            rm = parse(rz.read('MANIFEST-SHA256.json'))
            check('raw_archive', 'manifest_exact_inventory', set(rm) == set(rnames) - {'MANIFEST-SHA256.json'})
            for name, e in rm.items():
                b = rz.read(name)
                check('raw_manifest', name, identity(b) == {'bytes': e['bytes'], 'sha256': e['sha256']})
            raw_checks = parse(rz.read('CHECKS.json'))
            summary_checks('raw_assertions', raw_checks, 1042)
            raw_ids = parse(rz.read('INPUT-IDENTITIES.json'))
            check('execution_evidence', 'input_identity_record_equality', raw_ids['files'] == result['input_identities'] and raw_ids['source'] == expected_source and len(raw_ids['files']) == 22)
            for call in result['calls']:
                b = rz.read(call['response_member'])
                check('retained_response', call['response_member'], len(b) == call['response_bytes'] and sha(b) == call['response_sha256'])
        for e in result['input_identities']:
            b = git('cat-file', 'blob', CODE + ':' + e['path'])
            available = 'repository/' + e['path'] in name_set or e['path'] in set(external_paths)
            same_current_blob = maps[SOURCE].get(e['path'], {}).get('git_blob') == e['git_blob']
            check('execution_input_binding', e['path'], identity(b) == {'bytes': e['bytes'], 'sha256': e['sha256']} and maps[CODE].get(e['path'], {}).get('git_blob') == e['git_blob'] and same_current_blob and available, **e, availability='archive' if 'repository/' + e['path'] in name_set else 'pinned_online_dependency')

        candidate = js(REVIEW + 'CANDIDATE-AUDIT.json')
        publication = js(REVIEW + 'PUBLICATION-REVIEW.json')
        final = js(REVIEW + 'FINAL-STATE-REVIEW.json')
        summary_checks('retained_candidate_review', candidate['checks'], 425)
        summary_checks('retained_publication_review', publication['publication_audit']['checks'], 30)
        summary_checks('retained_final_state_review', final['checks'], 58)
        check('review', 'actual_independent_reviewer_and_scope', all(r['reviewer'] == '/root/github_reconciliation' and r['integration_approved'] is False and r['parent_completion_approved'] is False for r in (candidate, publication, final)) and candidate['actual_observer_execution_by_reviewer'] is False)
        check('review', 'initial_finding_preserved_then_resolved', candidate['mandatory_findings'][0]['id'] == 'C271-RV-001' and candidate['mandatory_findings'][0]['status'] == 'awaiting_external_receipt_inspection' and publication['resolved_findings'][0]['id'] == 'C271-RV-001' and publication['resolved_findings'][0]['status'] == 'resolved' and not publication['mandatory_findings'] and not final['mandatory_findings'])
        check('review', 'final_review_bound_to_source', final['candidate'] == SOURCE and final['tree'] == TREE and final['passed'] is True and final['saved_phase_delivery_verified'] is False)
        for name in ('CANDIDATE-AUDIT.json', 'CANDIDATE-REVIEW.md', 'PUBLICATION-REVIEW.json', 'PUBLICATION-REVIEW.md', 'PUBLISHED-CANDIDATE.json', 'PUBLISHED-EVIDENCE-STATE.json'):
            check('review_copy', name, payload[CONTROL + 'evidence/independent-review/' + name] == payload[REVIEW + name])

        records = js('session-evidence/final-source-record-checks/CHECKS.json')
        check('record_checks', 'exact_clean_source', records['source'] == {'commit': SOURCE, 'tree': TREE, 'dirty_before': '', 'dirty_after': ''} and records['passed'] is True and len(records['checks']) == 2)
        for e in records['checks']:
            b = payload['session-evidence/final-source-record-checks/' + e['log']]
            check('record_check_log', e['name'], e['exit_code'] == 0 and e['passed'] is True and identity(b) == {'bytes': e['bytes'], 'sha256': e['sha256']}, command=e['command'], **identity(b))
        check('record_checks', 'limits_preserved', set(records['not_run']) == {'routine local driver', 'complete affected integration cohort', 'actual-main verification', 'native/model trial'})

        cp = js('CHECKPOINT.json')
        task = js('repository/docs/workflow/tasks/C271/task.json')
        current = js('repository/docs/workflow/CURRENT.json')
        main_task = js('observed-main/docs/workflow/tasks/C270/task.json')
        main_current = js('observed-main/docs/workflow/CURRENT.json')
        check('boundary', 'checkpoint_matches_frozen_configuration', cp == config['checkpoint'])
        check('boundary', 'source_and_actual_main_distinct', cp['source_revision'] == cp['branch']['head'] == SOURCE and cp['source_tree'] == cp['branch']['tree'] == TREE and cp['observed_main']['sha'] == MAIN and cp['observed_main']['tree'] == MAIN_TREE and SOURCE != MAIN)
        check('boundary', 'parent_and_requirements_remain_open', cp['parent_status'] == task['status'] == 'in_progress' and cp['requirements_at_freeze'] == {r['id']: r['status'] for r in task['requirements']} == {'R01': 'done', 'R02': 'done', 'R03': 'not_done', 'R04': 'not_done', 'R05': 'not_done'})
        check('boundary', 'P02_gates_not_done', all(g['state'] == 'not_done' for g in cp['phase_table'] if g['gate'].startswith('P02')) and sum(g['gate'].startswith('P02') for g in cp['phase_table']) == 2)
        check('boundary', 'retained_open_draft_and_scope', cp['pull_request']['number'] == 274 and cp['pull_request']['state'] == 'open' and cp['pull_request']['draft'] is True and cp['pull_request']['merged'] is False and cp['pull_request']['head'] == SOURCE and cp['scope_issue']['number'] == 273 and cp['scope_issue']['state'] == 'open' and cp['branch']['disposition'] == 'active_retained')
        check('boundary', 'no_integration_or_lease', cp['integration_allowed_this_phase'] is False and task['session_phase']['integration_allowed_this_phase'] is False and cp['ownership']['main_integration_allowed'] is False and cp['ownership']['main_integration_lease'] == 'not_held' and task['completion']['merge_commit'] is None and task['completion']['branch_disposition'] == 'retained')
        receipt_path = 'docs/engineering/localized-repair-c271/delivery/P01-DELIVERY.json'
        check('boundary', 'future_receipt_separate_from_source', cp['delivery']['status'] == 'save_pending_at_freeze' and cp['delivery']['partial'] is True and cp['delivery']['external_receipt'] == task['delivery']['receipt'] == receipt_path and task['delivery']['status'] == 'pending' and 'repository/' + receipt_path not in name_set)
        check('boundary', 'source_task_predates_final_checks_and_save', 'clean_record_checks' in task['session_phase']['status'] and records['source']['commit'] == SOURCE and cp['verification_and_review']['record_checks']['result'] == 'passed' and cp['verification_and_review']['record_checks']['source_revision'] == SOURCE)
        check('boundary', 'recorded_review_and_execution_totals', cp['verification_and_review']['independent_focused_review']['total_checks'] == 513 and cp['verification_and_review']['controls']['assertions'] == 1042 and cp['verification_and_review']['controls']['source_revision'] == CODE and cp['implementation_candidate'] == CODE and cp['implementation_tree'] == CODE_TREE)
        check('boundary', 'actual_main_C270_complete', main_task['status'] == 'done' and all(r['status'] == 'done' for r in main_task['requirements']) and main_task['delivery']['status'] == 'saved' and main_current['active_task'] is None and main_task['delivery']['sha256'] == OLD_SHA)
        check('boundary', 'branch_current_C271_proposed', current['active_task'] == 'C271' and current['latest_task'] == 'C271')
        check('boundary', 'historical_unknowns_preserved', len(cp['historical_unknown_operations']) >= 2 and any('broad-driver' in s and 'unknown' in s for s in cp['historical_unknown_operations']) and cp['current_unknown_operations'] == [])
        check('boundary', 'delivery_then_stop_first_action', all(t.lower() in cp['next_action'].lower() for t in ('external P01 receipt', 'live branch', 'delivery-only', 'then stop', 'fresh parent chat', 'R03/P02')))
        docs = {n: payload[n].decode() for n in REQUIRED_ROOTS if n.endswith('.md')}
        for n in ('PROMPT-1-CONTINUE.md', 'PROMPT-2-RECOVER.md'):
            s = docs[n]
            check('recovery_instructions', n, all(t in s for t in ('C271', 'P01', 'P02', 'R03', 'PR274', SOURCE, MAIN)) and 'receipt' in s.lower() and 'stop' in s.lower(), bytes=len(payload[n]))
        check('manual_review', 'root_documents_and_recovery_sequence', True, reviewed_roots=sorted(docs), finding='Root prose was read in full: reconcile receipt and live branch first; incomplete P01 permits delivery-only recovery then stop; a fresh parent chat may resume the same C271 P02/R03 only after confirmed delivery. It distinguishes source e0b73 from future receipt-only metadata and actual-main e1a48; no offline restoration, broad qualification, integration or parent completion is claimed.')

    check('archive', 'unchanged_after_audit_reads', ARCHIVE.read_bytes() == data)
    failed = [c for c in checks if not c['passed']]
    groups = dict(collections.Counter(c['group'] for c in checks))
    report = {
        'schema': 'ontokin.c271.independent-final-package-audit/1',
        'reviewer': '/root/github_reconciliation',
        'builder': '/root/package_builder',
        'independent_of_builder': True,
        'reviewed_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'source_revision': SOURCE,
        'source_tree': TREE,
        'archive': archive_identity,
        'prompts': prompt_identities,
        'verdict': 'passed' if not failed else 'failed',
        'passed': not failed,
        'scope': 'Integrity, exact inventory, fresh extraction, declared origin equality, preservation, retained evidence and recovery-boundary review of this frozen P01 partial handoff only.',
        'coverage': {'outer_members': 160, 'manifest_payloads': 159, 'git_snapshots': 88, 'candidate_snapshots': 85, 'observed_main_snapshots': 3, 'session_sources': 58, 'preserved_source_archives': 1, 'pinned_online_dependency_entries': 1156, 'standalone_prompts': 2, 'raw_control_members': 27, 'retained_prior_source_audit_checks': 1703, 'retained_focused_review_checks': 513, 'retained_execution_assertions': 1042, 'retained_clean_record_checks': 2, 'new_independent_package_checks': len(checks)},
        'check_count': len(checks),
        'failed_count': len(failed),
        'group_counts': groups,
        'mandatory_findings': failed,
        'checks': checks,
        'execution': {'command': [sys.executable, '-B', str(Path(__file__))], 'python': sys.version, 'new_product_test_or_observer_calls': 0, 'repository_or_index_mutations': 0, 'remote_mutations': 0, 'new_phase_work': False},
        'approval': {'package_approved_for_P01_partial_save': not failed, 'saved_delivery_verified': False, 'integration_approved': False, 'parent_completion_approved': False, 'offline_restoration_verified': False},
        'retained_state': {'parent': 'in_progress', 'R01': 'done', 'R02': 'done', 'R03': 'not_done', 'R04': 'not_done', 'R05': 'not_done', 'P02': 'not_done', 'PR274': 'open draft unmerged', 'scope_issue273': 'open', 'main': MAIN, 'future_external_receipt': 'docs/engineering/localized-repair-c271/delivery/P01-DELIVERY.json'},
        'first_action': 'Reconcile the external P01 receipt and live branch. If P01 delivery is incomplete, finish only that delivery and stop. Once confirmed, a fresh parent chat may resume the same C271 P02 at R03.',
        'limitations': [
            'No new observer/product execution, broad routine driver, affected cohort, actual-main C271 verification, hosted CI, native/model trial or integration was performed by this audit.',
            'Fresh extraction verifies container/file integrity only; this is an online GitHub continuation package, not a complete offline restoration.',
            'The 1156 external source entries were checked against local Git tree objects at their pinned revision; their web URLs were not independently fetched and their payloads are intentionally outside the package.',
            'The nested C270 source ZIP is byte-identical to the independently audited input. Its 1703-check prior audit and historical failure records were preserved, not rerun; C262 and other historical external archives were not downloaded.',
            'Live branch/PR/main observations are the preserved final-source observations. This audit binds source snapshots to exact local Git objects and does not promise future remote state.',
            'Source task/CURRENT bytes intentionally predate subsequent final-source checks and the future save receipt. Later successful saving and receipt-only state publication require their own exact identity records.',
            'Historical broad-driver completion and global prior-process termination remain unknown.',
        ],
    }
    (OUT / 'AUDIT.json').write_text(json.dumps(report, indent=2) + '\n')
    md = f'''# C271 P01 final package audit\n\n**Verdict: {report['verdict']}** — {len(checks)} independent package checks, {len(failed)} failures. Reviewer: `/root/github_reconciliation`, independent of package builder `/root/package_builder`.\n\n## Exact audited artifact\n\n- ZIP: `{ARCHIVE.name}`\n- Bytes: **{archive_identity['bytes']:,}**\n- SHA-256: `{archive_identity['sha256']}`\n- Source revision: `{SOURCE}`\n- Source tree: `{TREE}`\n- Actual-main identity retained separately: `{MAIN}`\n\n## Coverage and evidence\n\nVerified all 160 safe, unique, regular ZIP members and CRCs; all 159 manifest payload sizes/hashes; and all 160 freshly extracted file bytes. All 88 Git snapshots match the declared Git blob, mode, contents, size and hash: 85 candidate files and three observed-main files. All 58 scratch/session files match their declared local originals. The remaining generated root/metadata files are separately classified. The 1,156 pinned online dependency entries match source Git-tree identities; they are not packaged source copies. Both standalone prompts exactly match their archive members and expected sizes/hashes.\n\nThe nested incoming C270 archive remains exactly {OLD_BYTES:,} bytes with SHA-256 `{OLD_SHA}`. Its completed 1,703-check intake audit and initial failed attempt remain intact. No historical audit was rerun.\n\nRetained C271 evidence includes the unchanged oracle, runner, RESULTS, 27-member RAW-EVIDENCE archive, exact invocation receipt and driver log. The recorded six cases, 18 calls, 1,042 successful assertions, six positive outcomes and 12 exact MALFORMED refusals are internally bound to executed source `{CODE}`. This audit made no observer calls. The 425-check initial review remains unchanged, including its original pending provenance finding; the separate 30-check publication review resolves C271-RV-001. The 58-check final-state review and two clean final-source record checks are preserved with exact evidence identities.\n\n## Scope and recovery decision\n\nThe archive is accepted for a **P01 partial save only**. Parent C271 remains in progress; R03–R05 and P02 remain not done. PR274 is retained as an open, unmerged draft, issue273 stays open, and no main-integration lease or approval is claimed.\n\nFirst reconcile the external P01 receipt and live branch. If delivery is incomplete, finish only that delivery and stop. After confirmed P01 delivery, a fresh parent chat may resume the same branch at P02/R03. Source task/CURRENT intentionally predate later check/save records. The future `docs/engineering/localized-repair-c271/delivery/P01-DELIVERY.json` is external to this immutable source archive; receipt-only publication does not require a self-referential rebuild.\n\nThis is an online continuation package. The audit does not establish a saved delivery, offline restoration, integration, parent completion, broad H22/C260 qualification, actual-main C271 behavior, native/model support or product completion. Historical broad-driver completion remains unknown.\n\nDetailed per-file evidence and exact prompt identities: `AUDIT.json`. Reproduction script: `audit_final_package.py`.\n'''
    if failed:
        md += '\n## Findings\n\n' + '\n'.join('- ' + c['group'] + ': ' + c['name'] for c in failed) + '\n'
    (OUT / 'REVIEW.md').write_text(md)
    print(json.dumps({'verdict': report['verdict'], 'check_count': len(checks), 'failed_count': len(failed), 'failed': failed, 'audit': str(OUT / 'AUDIT.json'), 'review': str(OUT / 'REVIEW.md'), 'archive': archive_identity, 'source_revision': SOURCE, 'source_tree': TREE}))
    return 0 if not failed else 1

if __name__ == '__main__':
    raise SystemExit(main())
