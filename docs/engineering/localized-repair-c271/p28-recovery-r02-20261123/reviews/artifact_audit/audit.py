#!/usr/bin/env python3
"""Read-only, bounded C271-P28 supplied-artifact audit.

Only writes under this script's directory. Does not execute archived code,
reconstruct a product candidate, call GitHub, or search a historical host.
"""
from __future__ import annotations

import base64
import collections
import datetime
import hashlib
import io
import json
import pathlib
import platform
import re
import stat
import sys
import zipfile

ROOT = pathlib.Path('/workspace/scratch/002c49ccf480')
OUT = pathlib.Path(__file__).resolve().parent
ORIGINAL = ROOT / 'inputs/OntoKin/OntoKin_C271_P28_Recovery_Handoff_2026-11-23.zip'
RECEIPT = ROOT / 'inputs/OntoKin/OntoKin_C271_P28_Recovery_Delivery_Receipt_2026-11-23.json'
checks: list[dict] = []
archives: list[dict] = []
identities: list[dict] = []


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def blob(data: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def check(name: str, passed: bool, detail=None) -> None:
    checks.append({'name': name, 'passed': bool(passed), 'detail': detail})


def save(name: str, value) -> None:
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def safe_name(name: str) -> bool:
    p = pathlib.PurePosixPath(name)
    return bool(name) and not p.is_absolute() and '\\' not in name and '\x00' not in name and ':' not in name and all(s not in ('', '.', '..') for s in name.rstrip('/').split('/'))


def rows_verify(label: str, payload: dict[str, bytes], rows: list[dict], path_key='path', exact=False, excluded=()) -> None:
    names = [v[path_key] for v in rows]
    check(label + ': manifest unique names', len(names) == len(set(names)))
    check(label + ': manifest safe names', all(safe_name(n) for n in names))
    if exact:
        check(label + ': exact manifest inventory', set(names) == set(payload) - set(excluded), {'missing_manifest': sorted(set(payload) - set(excluded) - set(names)), 'missing_payload': sorted(set(names) - set(payload))})
    for item in rows:
        name = item[path_key]
        actual = payload.get(name)
        check(label + ': bytes/hash ' + name, actual is not None and len(actual) == item['bytes'] and digest(actual) == item['sha256'])


def zip_audit(data: bytes, label: str, external_manifest=None, extract=False) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        infos = z.infolist()
        names = [i.filename for i in infos]
        safe = all(safe_name(n) for n in names)
        distinct = len(names) == len(set(names))
        unsafe_types = [i.filename for i in infos if stat.S_IFMT(i.external_attr >> 16) not in (0, stat.S_IFREG, stat.S_IFDIR)]
        check(label + ': CRC integrity', z.testzip() is None)
        check(label + ': safe names', safe)
        check(label + ': duplicate absence', distinct)
        check(label + ': no symlink/special files', not unsafe_types, unsafe_types)
        check(label + ': no encrypted entries', all(not (i.flag_bits & 1) for i in infos))
        if not (safe and distinct and not unsafe_types):
            raise RuntimeError('Unsafe ZIP; no extraction: ' + label)
        payload = {i.filename: z.read(i) for i in infos if not i.is_dir()}
        inventory = [{'path': i.filename, 'bytes': i.file_size, 'sha256': digest(payload[i.filename]) if i.filename in payload else None, 'archive_mode': oct(i.external_attr >> 16), 'directory': i.is_dir()} for i in infos]
        record = {'label': label, 'bytes': len(data), 'sha256': digest(data), 'members': len(infos), 'files': len(payload), 'inventory': inventory}
        if external_manifest is not None:
            rows_verify(label, payload, external_manifest, exact=True)
            record['manifest_payloads'] = len(external_manifest)
        elif 'MANIFEST-SHA256.json' in payload:
            manifest = json.loads(payload['MANIFEST-SHA256.json'])
            rows_verify(label, payload, manifest, exact=True, excluded=('MANIFEST-SHA256.json',))
            record['manifest_payloads'] = len(manifest)
        if 'SOURCE-MANIFEST.json' in payload:
            sources = json.loads(payload['SOURCE-MANIFEST.json'])
            rows_verify(label + ': sources', payload, sources, path_key='archive_path')
            calculated = []
            for source in sources:
                raw = payload[source['archive_path']]
                actual_blob = blob(raw)
                declared_blob = source.get('git_blob')
                if declared_blob is not None:
                    check(label + ': Git blob ' + source['archive_path'], actual_blob == declared_blob)
                calculated.append({**source, 'computed_git_blob': actual_blob, 'blob_declaration_present': declared_blob is not None, 'blob_matches_declaration': actual_blob == declared_blob if declared_blob else None, 'live_commit_path_binding_verified_this_audit': False})
            record['source_bindings'] = len(sources)
            record['explicit_git_blob_bindings'] = sum('git_blob' in source for source in sources)
            record['source_commits'] = dict(collections.Counter(source['commit'] for source in sources))
            save(label + '-source-bindings.json', calculated)
        if 'RECOVERY-MANIFEST.json' in payload:
            recoveries = json.loads(payload['RECOVERY-MANIFEST.json'])
            rows_verify(label + ': recovery manifest', payload, recoveries['files'], path_key='archive_path')
            record['recovery_bindings'] = len(recoveries['files'])
        if extract:
            dest = OUT / 'extracted' / label
            dest.mkdir(parents=True, exist_ok=False)
            for name, raw in payload.items():
                path = dest / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
            extracted = {str(p.relative_to(dest)): p.read_bytes() for p in dest.rglob('*') if p.is_file()}
            check(label + ': fresh extraction exact inventory and bytes', extracted == payload)
        archives.append(record)
        return payload


def identity_fields(value, label, path='$'):
    if isinstance(value, dict):
        for key, item in value.items():
            if key == 'data' and value.get('format') == 'zip+base64':
                continue
            identity_fields(item, label, path + '.' + key)
    elif isinstance(value, list):
        for i, item in enumerate(value):
            identity_fields(item, label, path + '[' + str(i) + ']')
    elif isinstance(value, str) and re.fullmatch(r'[a-f0-9]{40}', value):
        identities.append({'source': label, 'json_path': path, 'sha': value})


archive_bytes = ORIGINAL.read_bytes()
receipt_bytes = RECEIPT.read_bytes()
receipt = json.loads(receipt_bytes)
check('supplied receipt binds exact supplied ZIP', receipt['archive']['bytes'] == len(archive_bytes) and receipt['archive']['sha256'] == digest(archive_bytes))
root = zip_audit(archive_bytes, 'supplied-recovery', extract=True)
existing = {str(p.relative_to(ROOT / 'inputs/p28')): p.read_bytes() for p in (ROOT / 'inputs/p28').rglob('*') if p.is_file()}
check('Director extraction exact complete supplied ZIP', root == existing)

early_name = 'predecessor/OntoKin_C271_P28_Required_Images_Early_Recovery_2026-11-23.zip'
early_bytes = root[early_name]
early = zip_audit(early_bytes, 'original-p28-early')
historical = json.loads(root['HISTORICAL-DEPENDENCIES.json'])['embedded_original_p28_early']
check('original early byte identity matches historical dependency', len(early_bytes) == historical['bytes'] and digest(early_bytes) == historical['sha256'])

p27_name = 'predecessor/OntoKin_C271_P27_Required_Image_Design_Handoff_2026-11-23.zip'
p27_bytes = early[p27_name]
p27 = zip_audit(p27_bytes, 'p27-design')
early_checkpoint = json.loads(early['CHECKPOINT.json'])
check('P27 predecessor byte identity matches early checkpoint', digest(p27_bytes) == early_checkpoint['predecessor']['archive_sha256'])
p27_receipt_name = 'predecessor/OntoKin_C271_P27_Delivery_Receipt_2026-11-23.json'
check('P27 receipt exact historical hash', digest(early[p27_receipt_name]) == early_checkpoint['predecessor']['receipt_sha256'])

evidence = receipt['recovery_evidence']
check('separate receipt recovery-evidence format', evidence['format'] == 'zip+base64')
receipt_evidence_bytes = base64.b64decode(evidence['data'], validate=True)
check('separate receipt embedded archive bytes/hash', len(receipt_evidence_bytes) == evidence['bytes'] and digest(receipt_evidence_bytes) == evidence['sha256'])
(OUT / 'receipt-recovery-evidence.zip').write_bytes(receipt_evidence_bytes)
receipt_evidence = zip_audit(receipt_evidence_bytes, 'receipt-evidence', external_manifest=evidence['manifest'])

base = 'repository/docs/engineering/localized-repair-c271/p28-recovery-20261123/'
candidate = zip_audit(root[base + 'CANDIDATE-REVIEW.zip'], 'documentary-candidate-review')
candidate_manifest = json.loads(candidate['MANIFEST.json'])
rows_verify('documentary candidate payload', {n.removeprefix('repository/'): v for n, v in root.items() if n.startswith('repository/')}, candidate_manifest)
check('documentary candidate has only docs paths', all(row['path'].startswith('docs/') for row in candidate_manifest))
observations = zip_audit(root[base + 'OBSERVATIONS.zip'], 'retained-observations')
prior_branch_tree = json.loads(observations['live/branch-tree.json'])
check('historical failed branch-tree call retained', prior_branch_tree.get('isError') is True and 'Transport closed' in str(prior_branch_tree))

receipt_candidate_manifest = json.loads(receipt_evidence['reviews/receipt-audit/MANIFEST.json'])
check('separate receipt candidate manifest exact hash', digest(receipt_evidence['reviews/receipt-audit/MANIFEST.json']) == receipt['receipt_candidate_review']['manifest_sha256'])
check('separate receipt candidate has four documentary paths', len(receipt_candidate_manifest) == 4 and all(row['path'].startswith('docs/') for row in receipt_candidate_manifest))

runtime = 'repository/prototypes/static_tray_v01/current_host_inspection_v01.py'
check('only packaged prototype unchanged across root/early/P27', root[runtime] == early[runtime] == p27[runtime])
product_paths = {label: [name for name in payload if name.startswith(('repository/prototypes/', 'repository/tests/', 'repository/ontokin/'))] for label, payload in [('supplied-recovery', root), ('original-p28-early', early), ('p27-design', p27)]}
check('no new packaged test or product implementation', all(paths == [runtime] for paths in product_paths.values()), product_paths)
checkpoint = json.loads(root['CHECKPOINT.json'])
p27_checkpoint = json.loads(p27['CHECKPOINT.json'])
check('early archive froze before P28 implementation', early_checkpoint['status'] == 'startup_early_save_pending' and early_checkpoint['early_save_confirmed'] is False and early_checkpoint['source_commit'] == '360c80062e769230199602326fa8de25660df714')
check('P27 artifact declares design only', 'production or test implementation' in p27_checkpoint['exclusions'])
check('missing original P28 tree/commit explicit in complete receipt', all(v['resulting_tree_sha'] is None and v['resulting_commit_sha'] is None for v in receipt['current_unknown_operations']))
check('597 report remains explicitly unverified', '597/597 tests' in checkpoint['reported_but_not_reverified'] and checkpoint['original_p28_implementation_verified'] is False and receipt['original_p28_implementation_verified'] is False)
check('no original upload replay claimed', receipt['source_publication']['original_p28_uploads_replayed'] is False)

relevant_documents = {'complete-separate-receipt': receipt, 'root-checkpoint': checkpoint, 'original-early-checkpoint': early_checkpoint, 'P27-checkpoint': p27_checkpoint, 'original-archive-inventory-summary': json.loads(receipt_evidence['records/ORIGINAL-ARCHIVE-INVENTORY-SUMMARY.json'])}
for label, document in relevant_documents.items():
    identity_fields(document, label)
save('candidate-identity-inventory.json', identities)
save('archive-inventories.json', archives)
save('receipt-summary.json', {k: ( {ek: ev for ek, ev in v.items() if ek != 'data'} if k == 'recovery_evidence' else {ck: cv for ck, cv in v.items() if ck != 'checks'} if k == 'receipt_candidate_review' else v) for k, v in receipt.items()})

failed = [item for item in checks if not item['passed']]
result = {
    'schema': 'ontokin.c271.p28-independent-artifact-recovery-audit/1',
    'reviewer': '/root/artifact_audit',
    'observed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'command': 'python3 session/reviews/artifact_audit/audit.py',
    'environment': {'python': sys.version, 'platform': platform.platform()},
    'input_zip': {'path': str(ORIGINAL), 'bytes': len(archive_bytes), 'sha256': digest(archive_bytes)},
    'separate_receipt': {'path': str(RECEIPT), 'bytes': len(receipt_bytes), 'sha256': digest(receipt_bytes)},
    'checks_passed': len(checks) - len(failed),
    'checks_failed': len(failed),
    'checks': checks,
    'verdict': 'verified-supplied-artifacts-but-exact-P28-source-unavailable' if not failed else 'audit-failed',
    'blocker': 'P28-RECOVERY-BYTES-001',
    'self_contained_exact_P28_candidate_recovered': False,
    'reported_product_tests_reverified': False,
    'original_tree_and_commit': None,
    'runtime_snapshot': {'path': runtime, 'sha256': digest(root[runtime]), 'git_blob': blob(root[runtime]), 'unchanged_across_three_archives': root[runtime] == early[runtime] == p27[runtime]},
    'known_documentary_objects': {'recovery_commit': receipt['source_publication']['source_commit'], 'recovery_tree': receipt['source_publication']['source_tree'], 'receipt_commit': receipt['receipt_publication']['commit'], 'receipt_tree': receipt['receipt_publication']['tree']},
    'scope_boundary': 'Verified supplied recovery ZIP, original P28 early ZIP, direct P27 design predecessor, both small root evidence ZIPs, and all bytes of the separate receipt including its 22-member embedded evidence ZIP. P26 and older nested archives were retained and covered as payload bytes, but not recursively opened because their declared phase predates P28 implementation.',
    'limitations': [
        'Calculated Git blob IDs verify exact declared byte bindings. This audit did not independently fetch all commit/path/mode mappings from GitHub.',
        'No absence claim about unreferenced remote Git objects or unsupplied artifacts.',
        'No previous host search, original upload retry, implementation reconstruction, product execution, GitHub mutation, or Library mutation.',
        'The historical Library inventory summary is historical evidence, not a new live inventory.',
        'Known documentary recovery and receipt trees are not the missing original P28 candidate.'
    ],
    'next_action': 'Obtain the full original P28 final uploaded tree SHA plus publication manifest/completed group list, or exact implementation/fixture/test/review artifact; inspect that recorded object and verify completeness before any branch mutation. If unavailable, retain this blocker and obtain an explicit bounded reconstruction decision. Do not replay unknown uploads or relabel new work as recovered work.'
}
save('AUDIT.json', result)
print(json.dumps({k: result[k] for k in ['verdict', 'checks_passed', 'checks_failed', 'blocker', 'self_contained_exact_P28_candidate_recovered']}))
print(json.dumps([{'label': a['label'], 'members': a['members'], 'manifest_payloads': a.get('manifest_payloads'), 'source_bindings': a.get('source_bindings'), 'explicit_git_blob_bindings': a.get('explicit_git_blob_bindings')} for a in archives]))
if failed:
    print(json.dumps(failed, indent=2))
    raise SystemExit(1)
