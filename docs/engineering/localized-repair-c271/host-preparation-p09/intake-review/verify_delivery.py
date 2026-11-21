"""Read-only verification of prior P08 handoff; writes only this audit directory.

This verifier does not import or execute OntoKin, run Git, start Node/ldd,
install dependencies, or recreate any historical fixture path or special entry.
"""
from __future__ import annotations

import base64
import collections
import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import platform
import stat
import sys
import zipfile
import zlib

BASE = Path('/workspace/scratch/e33f906d0e8e')
OUT = BASE / 'audits/p08_delivery'
INCOMING = BASE / 'incoming/OntoKin'
ZIP = INCOMING / 'OntoKin_C271_P08_Host_Inspection_Implementation_Handoff_2026-11-21.zip'
RECEIPT = INCOMING / 'OntoKin_C271_P08_Delivery_Receipt_2026-11-21.json'
FRESH = OUT / 'fresh_extract'
POSTFREEZE = OUT / 'postfreeze_decoded'
OUT.mkdir(parents=True, exist_ok=True)


def identity_bytes(data: bytes) -> dict:
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def identity_file(path: Path) -> dict:
    return {'path': str(path), **identity_bytes(path.read_bytes())}


def safe_relative(path: str) -> bool:
    p = PurePosixPath(path)
    return (bool(path) and not p.is_absolute() and '\\' not in path
            and not any(part in ('', '.', '..') for part in path.split('/'))
            and ':' not in p.parts[0])


report = {
    'schema': 'ontokin.p08.startup-independent-delivery-audit/1',
    'recorded_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'reviewer': '/root/p08_delivery_audit',
    'scope': 'Prior P08 package and delivery reconciliation; no product acceptance or H0 execution.',
    'command': 'python3 audits/p08_delivery/verify_delivery.py',
    'environment': {'python': sys.version, 'platform': platform.platform()},
    'inputs': [identity_file(ZIP), identity_file(RECEIPT)],
    'checks': [],
    'limitations': [
        'Remote refs, Git trees, and Library save are not observed directly by this verifier.',
        'Git blob hashes and recorded source bindings are checked locally; commit/tree membership requires the Director live readback.',
        'No product test, installed executable, archived script, or archived fixture is executed.',
        'No full offline restoration or product qualification is claimed.',
    ],
}


def check(name: str, passed: bool, detail=None):
    report['checks'].append({'name': name, 'passed': bool(passed), 'detail': detail})


receipt = json.loads(RECEIPT.read_text())
check('archive exact expected identity',
      identity_bytes(ZIP.read_bytes()) == {
          'bytes': 14680844,
          'sha256': '037d7ff2b2b64f61f1b53b5fdae93b3d16a32bdb6fd681f45f824e2652d425b5'})

with zipfile.ZipFile(ZIP) as z:
    members = z.infolist()
    names = [m.filename for m in members]
    bad_paths = [n for n in names if not safe_relative(n)]
    duplicates = [n for n, count in collections.Counter(names).items() if count > 1]
    nonregular = [m.filename for m in members
                  if stat.S_IFMT(m.external_attr >> 16) not in (0, stat.S_IFREG)]
    check('unique safe regular ZIP entries', not bad_paths and not duplicates and not nonregular,
          {'entries': len(names), 'bad_paths': bad_paths, 'duplicates': duplicates,
           'nonregular': nonregular})
    check('ZIP CRC integrity', z.testzip() is None)
    if bad_paths or duplicates or nonregular:
        raise RuntimeError('Unsafe or unexpected archive entry; no extraction performed.')
    if FRESH.exists():
        raise FileExistsError('Fresh extraction target already exists; preserve earlier output.')
    FRESH.mkdir()
    z.extractall(FRESH)

manifest = json.loads((FRESH / 'MANIFEST-SHA256.json').read_text())
payloads = manifest['files']
expected = {r['path'] for r in payloads}
actual = {p.relative_to(FRESH).as_posix() for p in FRESH.rglob('*') if p.is_file()}
check('manifest rows unique', len(expected) == len(payloads))
check('manifest exact ZIP and fresh extraction inventory',
      expected | {'MANIFEST-SHA256.json'} == set(names) == actual,
      {'payloads': len(payloads), 'extracted_files': len(actual),
       'missing': sorted(expected - actual), 'extra': sorted(actual - expected - {'MANIFEST-SHA256.json'})})
required = ['README-START-HERE.md', 'CHECKPOINT.json', 'HANDOFF.md', 'NEXT-TASK.md',
            'RECOVERY-STATUS.md', 'PROMPT-1-CONTINUE.md', 'PROMPT-2-RECOVER.md',
            'HISTORICAL-DEPENDENCIES.json', 'MANIFEST-SHA256.json']
check('required root files', all((FRESH / n).is_file() for n in required), required)

payload_failures = []
provided_extraction_failures = []
for row in payloads:
    expected_identity = {'bytes': row['bytes'], 'sha256': row['sha256']}
    if identity_bytes((FRESH / row['path']).read_bytes()) != expected_identity:
        payload_failures.append(row['path'])
    prior = BASE / 'p08' / row['path']
    if not prior.is_file() or identity_bytes(prior.read_bytes()) != expected_identity:
        provided_extraction_failures.append(row['path'])
check('all fresh payload sizes and SHA256', not payload_failures,
      {'checked': len(payloads), 'failures': payload_failures})
check('provided extraction agrees with original ZIP payload', not provided_extraction_failures,
      {'checked': len(payloads), 'failures': provided_extraction_failures})

source = json.loads((FRESH / 'SOURCE-MANIFEST.json').read_text())
source_failures = []
source_revisions = collections.Counter()
source_paths = []
for row in source['files']:
    data = (FRESH / row['payload_path']).read_bytes()
    blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    local_identity = identity_bytes(data)
    source_paths.append(row['payload_path'])
    source_revisions[(row['git_commit'], row['git_tree'])] += 1
    if (local_identity != {'bytes': row['bytes'], 'sha256': row['sha256']}
            or blob != row['git_blob'] or row['git_mode'] not in ('100644', '100755')):
        source_failures.append({'path': row['payload_path'], 'actual': local_identity,
                                'blob': blob, 'recorded': row})
check('source manifest bytes and Git blob identities', not source_failures,
      {'snapshots': len(source['files']), 'failures': source_failures,
       'recorded_revision_groups': [{'commit': c, 'tree': t, 'files': n}
                                    for (c, t), n in sorted(source_revisions.items())]})
check('source manifest exact repository inventory',
      len(set(source_paths)) == len(source_paths)
      and set(source_paths) == {n for n in actual if n.startswith('repository/')})

recovery = json.loads((FRESH / 'RECOVERY-FILE-MAP.json').read_text())
recovery_failures = []
for row in recovery['files']:
    p = FRESH / row['payload_path']
    if not p.is_file() or identity_bytes(p.read_bytes()) != {'bytes': row['bytes'], 'sha256': row['sha256']}:
        recovery_failures.append(row['payload_path'])
check('all mapped recovery bytes', not recovery_failures,
      {'mapped_files': len(recovery['files']), 'failures': recovery_failures})

receipt_failures = []
prompt_results = []
for item in receipt['saved_archive_and_prompts']:
    local = INCOMING / item['file_name']
    valid = local.is_file() and identity_bytes(local.read_bytes()) == {'bytes': item['bytes'], 'sha256': item['sha256']}
    if not valid:
        receipt_failures.append(item['file_name'])
    if item.get('archive_member'):
        equal = local.read_bytes() == (FRESH / item['archive_member']).read_bytes()
        prompt_results.append({'file_name': item['file_name'], 'archive_member': item['archive_member'],
                               'equal': equal, **identity_bytes(local.read_bytes())})
check('receipt saved archive and prompt identities', not receipt_failures,
      {'files': len(receipt['saved_archive_and_prompts']), 'failures': receipt_failures})
check('standalone prompt byte equality with ZIP members', all(p['equal'] for p in prompt_results), prompt_results)

POSTFREEZE.mkdir(exist_ok=False)
postfreeze_inventory = []
postfreeze_failures = []
seen = set()
for row in receipt['postfreeze_evidence']:
    rel = row['original_relative_path']
    if not safe_relative(rel) or rel in seen or row['encoding'] != 'zlib+base64':
        raise RuntimeError('Unsafe duplicate or unsupported postfreeze evidence entry')
    seen.add(rel)
    data = zlib.decompress(base64.b64decode(row['encoded_data'], validate=True))
    ident = identity_bytes(data)
    if ident != {'bytes': row['bytes'], 'sha256': row['sha256']}:
        postfreeze_failures.append(rel)
        continue
    dest = POSTFREEZE / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    postfreeze_inventory.append({'path': rel, **ident})
check('postfreeze receipt evidence decoded and every size/hash verified', not postfreeze_failures,
      {'files': len(postfreeze_inventory), 'bytes': sum(p['bytes'] for p in postfreeze_inventory),
       'failures': postfreeze_failures})
(OUT / 'POSTFREEZE-INVENTORY.json').write_text(json.dumps(postfreeze_inventory, indent=2) + '\n')

canonical_record = receipt['canonical_delivery_receipt']
canonical_path = POSTFREEZE / 'OntoKin' / canonical_record['repository_path']
check('embedded canonical P08 delivery receipt identity',
      canonical_path.is_file() and identity_bytes(canonical_path.read_bytes()) == {
          'bytes': canonical_record['bytes'], 'sha256': canonical_record['sha256']},
      {'path': str(canonical_path), **canonical_record})

checkpoint = json.loads((FRESH / 'CHECKPOINT.json').read_text())
review = receipt['independent_package_review']
check('frozen source and receipt boundary consistency',
      checkpoint['source']['commit'] == receipt['archive_source_commit'] == review['source_commit']
      and checkpoint['source']['tree'] == receipt['archive_source_tree'] == review['source_tree']
      and checkpoint['accepted_candidate']['source_commit'] == receipt['accepted_code_commit'] == review['accepted_code_commit']
      and receipt['receipt_commit'] == receipt['receipt_source_checks']['source_commit']
      and receipt['receipt_tree'] == receipt['receipt_source_checks']['source_tree'],
      {'frozen_source': receipt['archive_source_commit'], 'receipt_commit': receipt['receipt_commit'],
       'accepted_code_commit': receipt['accepted_code_commit'],
       'frozen_delivery': checkpoint['delivery']['status'], 'later_phase_status': receipt['phase_status']})
check('independent exact package acceptance binds actual ZIP',
      review['package_accepted'] is True and review['mandatory_findings'] == []
      and review['archive']['bytes'] == ZIP.stat().st_size
      and review['archive']['sha256'] == identity_bytes(ZIP.read_bytes())['sha256'])
check('recorded saved-byte gates after independent package review',
      all(item.get('status') == 'saved' and item.get('saved_bytes_readback_equal') is True
          and item.get('local_bytes_unchanged_after_save') is True
          and item.get('destination_metadata_observed') is True
          for item in receipt['saved_archive_and_prompts']),
      'Recorded prior observations; no fresh Library query by this verifier.')

failure = receipt['postpublication_metadata_failure']
correction = receipt['postpublication_metadata_correction']
initial_checks = receipt['initial_receipt_checks_preserved']
final_checks = receipt['receipt_source_checks']
check('late metadata failure retained with separate correction and passing receipt checks',
      failure['failed_commit'] == receipt['initial_receipt_commit'] == initial_checks['source_commit'] == correction['expected_head']
      and initial_checks['passed'] is False and final_checks['passed'] is True
      and correction['canonical_path'] == 'docs/workflow/CURRENT.json'
      and correction['field'] == 'snapshot_date'
      and correction['checker_changed'] is False
      and correction['product_archive_or_oracle_changed'] is False,
      {'failure': failure['actual_failure'], 'initial_commit': receipt['initial_receipt_commit'],
       'corrected_commit': receipt['receipt_commit'], 'before': correction['before'], 'after': correction['after']})

report['observed_archive_state'] = {
    'source': checkpoint['source'], 'main': checkpoint['main'], 'branch': checkpoint['branch'],
    'pull_request': checkpoint['pull_request'], 'issue': checkpoint['issue'],
    'phase_status': checkpoint['phase_status'], 'parent_status': checkpoint['parent_status'],
    'parent_requirements': checkpoint['parent_requirements'], 'unknown_operations': checkpoint['unknown_operations'],
}
report['separate_receipt_state'] = {
    k: receipt[k] for k in ['phase_status', 'parent_status', 'archive_source_commit',
                           'archive_source_tree', 'receipt_commit', 'receipt_tree',
                           'parent_requirements', 'parent_plan', 'main_integration_performed',
                           'branch_disposition', 'historical_unknowns', 'next_action',
                           'remaining_delivery_actions_at_file_freeze']}
report['fresh_extraction'] = str(FRESH)
report['postfreeze_evidence_directory'] = str(POSTFREEZE)
report['passed'] = all(row['passed'] for row in report['checks'])
report['counts'] = {'checks': len(report['checks']), 'failed': sum(not row['passed'] for row in report['checks']),
                    'zip_entries': len(names), 'payloads': len(payloads),
                    'source_snapshots': len(source['files']), 'recovery_files': len(recovery['files']),
                    'postfreeze_files': len(postfreeze_inventory)}
output_path = OUT / 'VERIFICATION.json'
output_path.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'passed': report['passed'], 'counts': report['counts'],
                  'report': str(output_path), 'receipt_identity': identity_file(RECEIPT)}))
