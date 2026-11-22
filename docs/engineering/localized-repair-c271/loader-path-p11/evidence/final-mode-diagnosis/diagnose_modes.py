#!/usr/bin/env python3
"""Read-only dimensional diagnosis of final ZIP mode transport and recovery."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import stat
import zipfile

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
ARCHIVE = ROOT / 'deliverables/final/OntoKin_C271_P11_Loader_Path_Handoff_2026-11-21.zip'
EXPECTED = '4eddd353047fb8d6aa316544c8b54d655eb53a1613f9c522bbed0edc1ab1249e'


def sha(data):
    return hashlib.sha256(data).hexdigest()


raw = ARCHIVE.read_bytes()
assert len(raw) == 5606509 and sha(raw) == EXPECTED
out = HERE / 'MODE-DIAGNOSIS.json'
assert not out.exists()
zip_mode_differences, byte_errors, original_errors = [], [], []
with zipfile.ZipFile(ARCHIVE) as z:
    rec = json.loads(z.read('RECOVERY-FILE-MAP.json'))
    for row in rec['files']:
        if 'payload_path' in row:
            value = z.read(row['payload_path'])
            if len(value) != row['bytes'] or sha(value) != row['sha256']:
                byte_errors.append(row['relative_path'])
            transport_mode = oct(stat.S_IMODE(z.getinfo(row['payload_path']).external_attr >> 16))
            if transport_mode != row['source_mode']:
                zip_mode_differences.append({'relative_path': row['relative_path'],
                                             'payload_path': row['payload_path'],
                                             'bytes': row['bytes'], 'sha256': row['sha256'],
                                             'recorded_original_mode': row['source_mode'],
                                             'zip_transport_mode': transport_mode})
        source = Path(row['original_path'])
        value = source.read_bytes()
        actual_mode = oct(stat.S_IMODE(source.lstat().st_mode))
        if len(value) != row['bytes'] or sha(value) != row['sha256'] or actual_mode != row['source_mode']:
            original_errors.append({'relative_path': row['relative_path'], 'actual_mode': actual_mode,
                                    'recorded_mode': row['source_mode'], 'bytes_equal': len(value) == row['bytes'],
                                    'hash_equal': sha(value) == row['sha256']})
    cited = {}
    for path in ['README-START-HERE.md', 'HANDOFF.md', 'RECOVERY-STATUS.md',
                 'repository/docs/engineering/localized-repair-c271/loader-path-p11/design/candidate004/MATERIALIZATION.md',
                 'recovery/session_evidence/packaging/verify_handoff.py',
                 'recovery/session_evidence/packaging/build_handoff.py']:
        value = z.read(path)
        cited[path] = {'bytes': len(value), 'sha256': sha(value)}
    status = z.read('RECOVERY-STATUS.md').decode()
    materialization = z.read('repository/docs/engineering/localized-repair-c271/loader-path-p11/design/candidate004/MATERIALIZATION.md').decode()
    assert 'Original modes are evidence; ZIP payloads are inert regular files.' in status
    assert 'Apply its manifest-recorded inert mode' in materialization
    report = {'schema': 'ontokin.c271.p11-final-mode-diagnosis/1',
              'checked_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
              'archive': {'path': str(ARCHIVE), 'bytes': len(raw), 'sha256': sha(raw)},
              'recovery_rows': len(rec['files']),
              'embedded_rows': sum('payload_path' in row for row in rec['files']),
              'embedded_byte_errors': byte_errors,
              'original_byte_or_mode_errors': original_errors,
              'zip_transport_mode_differences': zip_mode_differences,
              'mode_difference_count': len(zip_mode_differences),
              'frozen_instruction_sources': cited,
              'finding': 'The original physical modes are preserved as recovery metadata; ZIP transport modes are deliberately 0644. Byte identity and actual original source modes agree. FP12 adds equality between these two distinct mode dimensions.',
              'prior_wording_correction': 'The earlier package-engineer summary original physical recovery modes meant verification of current original files against RECOVERY-FILE-MAP.source_mode. The builder verifier did not apply those modes to extracted payload files. That summary was imprecise and must not be read as a completed private materialization check.',
              'guidance_scope': 'Frozen README/HANDOFF distinguish Git transport and physical recovery modes and point to GIT-TRANSPORT then candidate004/MATERIALIZATION.md. That materialization procedure step 3 explicitly restores authenticated payload modes and step 4 covers authenticated sibling support/prior candidates. RECOVERY-FILE-MAP provides original source_mode for every recovery row. There is no root-level explicit instruction to chmod every generic recovery row from source_mode.',
              'disposition': 'Independent reviewer must verify private materialization before deciding acceptance. This diagnosis does not waive a gate or authorize a rebuild.',
              'mutations': 'Only new followup source/report in this assigned directory; original ZIP, source files and existing package outputs unchanged.'}
out.write_text(json.dumps(report, indent=2) + '\n')
assert sha(ARCHIVE.read_bytes()) == EXPECTED
print(json.dumps({'report': str(out), 'mode_differences': len(zip_mode_differences),
                  'embedded_byte_errors': len(byte_errors), 'original_byte_or_mode_errors': len(original_errors),
                  'archive_unchanged': True}, indent=2))
