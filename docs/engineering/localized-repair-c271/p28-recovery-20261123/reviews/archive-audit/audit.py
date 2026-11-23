import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import zipfile
import zlib
from datetime import datetime, timezone

ROOT = Path('/workspace/scratch/acb73444303d')
OUT = ROOT / 'reviews/archive-audit'
OUT.mkdir(parents=True, exist_ok=True)
failures = []
checks = []

def check(name, passed, detail=None):
    checks.append({'check': name, 'passed': bool(passed), 'detail': detail})
    if not passed:
        failures.append(checks[-1])

def ident(data):
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}

archives = []
for name, filename, expected_sha, library_id in [
    ('p27', 'OntoKin_C271_P27_Required_Image_Design_Handoff_2026-11-23.zip', 'd9fdae71a39f343b1fa14a6eb358f780428a1d05af66e85bd9e4c191abe82a77', 'libfile_fde3_f-f6f4b4072b88819186ef487642077dae_2ab2a24d43748191957f9bcc356b59de'),
    ('p28-early', 'OntoKin_C271_P28_Required_Images_Early_Recovery_2026-11-23.zip', '520b24277f2f4a28b5ed96122a477b2438a60905c1a1ae80de39d448426cb15e', 'libfile_fde3_f-921dd7a4adc081919dbecbc1ab5ba13f_2ab2a24d43748191957f9bcc356b59de'),
]:
    path = ROOT/'incoming'/filename
    extracted = ROOT/'incoming'/name
    zbytes = path.read_bytes()
    info = {'name': name, 'file_name': filename, **ident(zbytes), 'library_file_id': library_id}
    check(name+'/expected-digest', info['sha256'] == expected_sha)
    check(name+'/library-xattr', os.getxattr(path, 'user.library-file-id').decode() == library_id)
    check(name+'/version-xattr', os.getxattr(path, 'user.library-file-version').decode() == '0')
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        check(name+'/crc', z.testzip() is None)
        check(name+'/duplicates', len(names) == len(set(names)))
        check(name+'/safe-paths', all(not n.startswith('/') and '..' not in PurePosixPath(n).parts and '\\' not in n for n in names))
        manifest = json.loads(z.read('MANIFEST-SHA256.json'))
        source = json.loads(z.read('SOURCE-MANIFEST.json'))
        check(name+'/exact-manifest-inventory', {e['path'] for e in manifest} == set(names) - {'MANIFEST-SHA256.json'})
        check(name+'/manifest-unique', len(manifest) == len({e['path'] for e in manifest}))
        check(name+'/extracted-inventory', {str(p.relative_to(extracted)) for p in extracted.rglob('*') if p.is_file()} == set(names))
        for e in manifest:
            b = z.read(e['path'])
            check(name+'/payload/'+e['path'], ident(b) == {'bytes': e['bytes'], 'sha256': e['sha256']})
            check(name+'/extracted/'+e['path'], b == (extracted/e['path']).read_bytes())
        for e in source:
            b = z.read(e['archive_path'])
            check(name+'/source-content/'+e['archive_path'], ident(b) == {'bytes': e['bytes'], 'sha256': e['sha256']})
            check(name+'/source-path/'+e['archive_path'], e['archive_path'] in ['repository/'+e['git_path'], 'governing-main/'+e['git_path']])
        info.update({'zip_members': len(names), 'payloads': len(manifest), 'source_bindings': len(source), 'source_commits': sorted(set(e['commit'] for e in source)), 'source_binding_limit': 'Verified declared file identities and paths against archive bytes; current remote Git object identity requires independent live reconciliation by Director.'})
        if 'RECOVERY-MANIFEST.json' in names:
            recovery = json.loads(z.read('RECOVERY-MANIFEST.json'))
            for e in recovery['files']:
                b = z.read(e['archive_path'])
                check(name+'/recovery/'+e['archive_path'], ident(b) == {'bytes': e['bytes'], 'sha256': e['sha256']})
            info['recovery_manifest_files'] = len(recovery['files'])
            info['reproducible_exclusions'] = recovery['reproducible_exclusions']
        info['current_phase_recovery_members'] = [n for n in names if n.startswith('recovery/')]
    archives.append(info)

pred = ROOT/'incoming/p28-early/predecessor'
receipt_path = pred/'OntoKin_C271_P27_Delivery_Receipt_2026-11-23.json'
terminal_path = pred/'OntoKin_C271_P27_Terminal_Verification_2026-11-23.json'
receipt = json.loads(receipt_path.read_text())
terminal = json.loads(terminal_path.read_text())
archive = terminal['saved_development_handoff']['archive']
check('p27/nested-predecessor-byte-equality', (pred/archive['file_name']).read_bytes() == (ROOT/'incoming'/archive['file_name']).read_bytes())
check('p27/terminal-archive-identity', ident((pred/archive['file_name']).read_bytes()) == {'bytes': archive['bytes'], 'sha256': archive['sha256']})
receipt_record = terminal['earlier_external_receipt']['file']
check('p27/terminal-receipt-identity', ident(receipt_path.read_bytes()) == {'bytes': receipt_record['bytes'], 'sha256': receipt_record['sha256']})
embedded = []
for path, obj in [(receipt_path, receipt), (terminal_path, terminal)]:
    kinds = {}
    for e in obj['postfreeze_recovery']['files']:
        enc = e.get('encoding')
        kinds[enc] = kinds.get(enc, 0) + 1
        if enc == 'utf-8':
            b = e['content'].encode('utf-8')
        elif enc == 'base64':
            b = base64.b64decode(e['content'])
        elif enc in ['zlib-base64', 'zlib+base64']:
            b = zlib.decompress(base64.b64decode(e['content']))
        elif enc is None:
            continue
        else:
            check(path.name+'/known-embedded-encoding/'+e['path'], False, enc)
            continue
        check(path.name+'/embedded/'+e['path'], ident(b) == {'bytes': e['bytes'], 'sha256': e['sha256']})
    embedded.append({'file_name': path.name, 'encodings': kinds, 'records': len(obj['postfreeze_recovery']['files'])})

report = {
    'schema': 'ontokin.c271.p28-recovery-input-audit/1',
    'reviewer': '/root/archive_audit',
    'observed_at_utc': datetime.now(timezone.utc).isoformat(),
    'scope': 'Read-only integrity and retained-state audit of fresh Library P27 development handoff and P28 early recovery ZIP; report files only',
    'passed': not failures,
    'archives': archives,
    'checks_passed': sum(e['passed'] for e in checks),
    'checks_failed': len(failures),
    'failures': failures,
    'p27_predecessor': {
        'source_a': terminal['source_a']['commit'],
        'source_tree_a': terminal['source_a']['tree'],
        'receipt_b': terminal['receipt_b']['commit'],
        'receipt_tree_b': terminal['receipt_b']['tree'],
        'receipt': {k: receipt_record[k] for k in ['file_name', 'library_file_id', 'file_id', 'version', 'bytes', 'sha256']},
        'terminal_file': {'file_name': terminal_path.name, **ident(terminal_path.read_bytes())},
        'terminal_comments': terminal['terminal']['comments'],
        'owner_state_recorded': terminal['owner_state'],
        'remaining_current_phase_recorded': terminal['remaining_current_phase'],
        'embedded_recovery': embedded,
    },
    'gates': {
        'completed_in_archive_evidence': ['P27 versioned design and independent acceptance', 'P27 saved handoff and receipt, matching terminal comments and release as historical evidence'],
        'p28_early_freeze': 'Startup-only; no product edits or control runs yet. Published base is P27 receipt commit 360c80062e769230199602326fa8de25660df714.',
        'pending_live_reconciliation': ['P28 early save exact receipt', 'P28 later candidate/code/fixture/test evidence and Git object publication outcome', 'Retained branch and active ownership', 'Final handoff and external receipt'],
        'unknown_from_these_inputs': ['Exact later P28 implementation bytes', 'Frozen executable fixtures/oracles and exact test run records from later P28 work', 'Latest uploaded intermediate Git tree identities', 'Whether interrupted publication advanced branch'],
        'parent_remaining': ['R03', 'R04', 'R05', 'P02 in progress', 'H0/H1/full routine', 'main integration'],
        'historical_unknowns': ['C270 ancillary broad-driver completion', 'Global prior-process termination', 'P13 read-only difflib completion; do not retry'],
    },
    'finding': 'P28 early recovery is internally valid but preserves no substantive P28 implementation, control, result, or publication payload. It cannot by itself justify reusing later reported passes or reconstructing the intended later tree. Reconcile exact later durable destinations before replaying any work.',
    'next_action': 'Director must inspect live branch/PR/issue and resolve later saved artifacts or Git object identities; if unavailable, record a concrete lost-unpublished-bytes blocker rather than silently recreating an allegedly tested candidate.',
    'limits': ['No product tests, host preparation, or external writes performed', 'Current GitHub destination verification is delegated to Director; archive assertions are not fresh remote observations', 'No prior host paths were inspected or relied on'],
    'checks': checks,
}
(OUT/'AUDIT.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps({'passed':report['passed'],'checks_passed':report['checks_passed'],'checks_failed':report['checks_failed'],'failures':failures,'archives':[{k:a[k] for k in ['name','bytes','sha256','zip_members','payloads','source_bindings']} for a in archives],'embedded':embedded},indent=2))
