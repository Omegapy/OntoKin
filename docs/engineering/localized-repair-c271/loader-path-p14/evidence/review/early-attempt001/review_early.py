"""Independent package audit; only stdlib/Git reads and owned review writes."""
import collections
import datetime
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import platform
import stat
import subprocess
import sys
import zipfile

ROOT = Path('/workspace/scratch/29fbc446c948')
OUT = ROOT / 'p14-session/review/early-attempt001'
REPO = ROOT / 'OntoKin'
ARTIFACTS = ROOT / 'deliverables/early-attempt001'
ARCHIVE = ARTIFACTS / 'OntoKin_C271_P14_Loader_Path_Early_Recovery_2026-11-21.zip'
EXPECTED_SHA = '962f122f141ec27ce979f7878e53c2a0b29356ed69127ac6fd6e93fcc799af72'
checks = []
reviewed = []

def identity(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

def check(name, passed, detail):
    checks.append({'id': name, 'passed': bool(passed), 'detail': detail})

def git(*args):
    env = dict(os.environ, GIT_OPTIONAL_LOCKS='0')
    return subprocess.check_output(['git', '-C', str(REPO), *args], env=env)

def safe(name):
    p = PurePosixPath(name)
    return bool(name) and not p.is_absolute() and all(x not in ('', '.', '..') for x in name.split('/')) and '\\' not in name and '\x00' not in name and ':' not in name

raw = ARCHIVE.read_bytes()
archive_id = identity(raw)
check('archive_identity', archive_id == {'bytes': 3370213, 'sha256': EXPECTED_SHA}, archive_id)
reviewed.append({'path': str(ARCHIVE), **archive_id})
with zipfile.ZipFile(io.BytesIO(raw)) as z:
    infos = z.infolist()
    names = [x.filename for x in infos]
    check('unique_safe_inventory', len(names) == len(set(names)) and all(safe(x) for x in names), {'members': len(names)})
    check('inert_regular_members', all(not x.is_dir() and stat.S_IFMT(x.external_attr >> 16) == stat.S_IFREG and stat.S_IMODE(x.external_attr >> 16) == 0o644 for x in infos), 'Every outer member is an inert regular 0644 file; historical Git/fixture modes remain separate metadata.')
    check('zip_integrity', z.testzip() is None, 'CRC and decompression checked for every member.')
    contents = {name: z.read(name) for name in names}
    manifest = json.loads(contents['MANIFEST-SHA256.json'])
    check('manifest_inventory', set(manifest) == set(names) - {'MANIFEST-SHA256.json'}, {'payloads': len(manifest)})
    mismatches = [name for name, desc in manifest.items() if identity(contents[name]) != desc]
    check('all_payload_hashes', not mismatches, mismatches)
    required = {'README-START-HERE.md','CHECKPOINT.json','HANDOFF.md','NEXT-TASK.md','RECOVERY-STATUS.md','PROMPT-1-CONTINUE.md','PROMPT-2-RECOVER.md','HISTORICAL-DEPENDENCIES.json','MANIFEST-SHA256.json'}
    check('required_roots', required <= set(names), sorted(required - set(names)))
    if not all(x['passed'] for x in checks):
        raise RuntimeError('Transport audit failed before extraction')
    target = OUT / 'extracted'
    target.mkdir()
    for name, content in contents.items():
        dst = target / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        with dst.open('xb') as f:
            f.write(content)
        dst.chmod(0o600)
        reviewed.append({'member': name, **identity(content)})
    check('fresh_extraction', all((target / name).read_bytes() == content for name, content in contents.items()), 'Extracted every safe member to a new private directory and independently compared returned bytes. No payload executed.')
    source = json.loads(contents['SOURCE-MANIFEST.json'])
    source_errors = []
    trees = {}
    for rev in {row['commit'] for row in source}:
        actual_tree = git('rev-parse', rev + '^{tree}').decode().strip()
        listing = {}
        for record in git('ls-tree', '-rz', '--full-tree', rev).split(b'\0'):
            if not record:
                continue
            header, path = record.split(b'\t', 1)
            mode, kind, oid = header.decode().split()
            listing[path.decode()] = (mode, kind, oid)
        trees[rev] = (actual_tree, listing)
    for row in source:
        content = contents[row['member']]
        actual_tree, listing = trees[row['commit']]
        if row['tree'] != actual_tree or listing.get(row['path']) != (row['git_mode'], 'blob', row['git_blob']) or identity(content) != {'bytes': row['bytes'], 'sha256': row['sha256']} or git('cat-file', 'blob', row['git_blob']) != content:
            source_errors.append(row['member'])
    check('exact_git_snapshots', not source_errors, {'snapshots': len(source), 'commits': {k: v[0] for k, v in trees.items()}, 'errors': source_errors})
    represented_sources = {row['member'] for row in source}
    check('all_snapshot_paths_bound', represented_sources == {x for x in names if x.startswith(('repository/', 'observed-main/'))}, 'Every repository/observed-main member occurs in the exact source manifest.')
    for stem, member in [('Continue','PROMPT-1-CONTINUE.md'), ('Recover','PROMPT-2-RECOVER.md')]:
        path = ARTIFACTS / ('OntoKin_C271_P14_Loader_Path_Early_Recovery_2026-11-21_' + stem + '.md')
        p_raw = path.read_bytes()
        reviewed.append({'path': str(path), **identity(p_raw)})
        check('matching_prompt_' + stem.lower(), p_raw == contents[member], identity(p_raw))
    phase = json.loads(contents['recovery/session/PHASE.json'])
    checkpoint = json.loads(contents['CHECKPOINT.json'])
    check('phase_identity', contents['recovery/session/PHASE.json'] == (ROOT / 'p14-session/PHASE.json').read_bytes(), identity(contents['recovery/session/PHASE.json']))
    check('checkpoint_phase_consistency', all(checkpoint.get(k) == v for k, v in phase.items()), 'All declared phase fields preserved in checkpoint.')
    recovery = json.loads(contents['RECOVERY-FILE-MAP.json'])
    recovery_errors = []
    for row in recovery:
        content = contents[row['member']]
        if identity(content) != {'bytes': row['bytes'], 'sha256': row['sha256']}:
            recovery_errors.append(row['member'])
    check('recovery_file_map', not recovery_errors, {'files': len(recovery), 'errors': recovery_errors})
    key_recovery = ['PHASE.json','READ-SET.json','STARTUP-FAILURES.json','intake-evidence.json','initial-ci-observation.json','review/SCOPE-AUDIT.json','review/SCOPE-REPORT.md','review/READ-SET.json','state-review/RECONCILIATION-EVIDENCE.json','state-review/READSET.json']
    check('unique_startup_coverage', all('recovery/session/' + x in names for x in key_recovery), 'Unique startup phase, failures, observations and completed worker evidence are present; derived read chunks have explicit exclusions.')
    check('unpublished_phase_recoverable', 'recovery/unpublished-tracked.patch' in names and contents['recovery/unpublished/docs/engineering/localized-repair-c271/loader-path-p14/PHASE.json'] == contents['recovery/session/PHASE.json'], 'Unpublished phase file and tracked patch retained against declared source revision.')
    base = 'repository/docs/engineering/localized-repair-c271/review-boundary-p13/'
    terminal = json.loads(contents[base + 'P13-TERMINAL-CONFIRMATION.json'])
    receipt_name = 'predecessor/OntoKin_C271_P13_Delivery_Receipt_2026-11-21.json'
    predecessor_name = 'predecessor/OntoKin_C271_P13_Review_Policy_Design_Handoff_2026-11-21.zip'
    receipt = json.loads(contents[receipt_name])
    check('p13_predecessor_identities', identity(contents[receipt_name]) == {k:terminal['terminal_receipt'][k] for k in ['bytes','sha256']} and identity(contents[predecessor_name]) == {k:terminal['archive'][k] for k in ['bytes','sha256']}, 'Included exact P13 archive and terminal receipt match the Git-pinned terminal confirmation.')
    check('p13_delivery_reconciled', terminal['phase_complete'] is True and terminal['parent_complete'] is False and terminal['disposition'] == 'complete_partial_delivery' and all(terminal[k]['saved_bytes_readback_equal'] for k in ['archive','terminal_receipt']) and all(p['saved_bytes_readback_equal'] for p in terminal['matching_prompts']), 'P13 terminal confirmation resolves its prior frozen save_pending fields without closing parent C271.')
    check('p13_core_receipt_binding', json.loads(contents[base + 'P13-DELIVERY.json']) == receipt['core_delivery'] and identity(contents[base + 'P13-DELIVERY.json']) == {k: receipt['core_delivery_file'][k] for k in ['bytes','sha256']}, 'Receipt core equals the exact Git-pinned P13-DELIVERY.json.')
    dependencies = json.loads(contents['HISTORICAL-DEPENDENCIES.json'])
    with zipfile.ZipFile(io.BytesIO(contents[predecessor_name])) as previous:
        check('inherited_dependencies_exact', dependencies['inherited_dependencies_unchanged'] == json.loads(previous.read('HISTORICAL-DEPENDENCIES.json')), 'Historical dependency descriptors remain unchanged; full offline recovery is expressly not claimed.')
    check('inherited_mode_and_external_boundary', dependencies['full_offline_restoration_claim'] is False and 'REVISION-004.diff' in dependencies['p11_external_member'] and b'MATERIALIZATION.md' in contents['README-START-HERE.md'] and b'Restore original fixture modes' in contents['README-START-HERE.md'], 'Explicit external diff and inert transport/recorded fixture-mode distinction retained.')
    check('checkpoint_required_status', 'phase_table' in checkpoint and ('observed_main' in checkpoint or 'observed_main_at_utc' in checkpoint) and 'current_worker_states' in checkpoint and 'current_unknown_operations' in checkpoint and 'evidence' in checkpoint, 'FAIL: criteria do not supply completed/pending states, observed-main timestamp/evidence or current worker/operation status.')
    check('next_action_unambiguous', b'If P14 delivery is incomplete, finish delivery only and stop.' not in contents['NEXT-TASK.md'], 'FAIL: unqualified final-delivery-only instruction contradicts this early package continuation into implementation after confirmed save.')

findings = [
    {'id':'P14-EARLY-001','severity':'mandatory','paths':['CHECKPOINT.json','HANDOFF.md','RECOVERY-STATUS.md'],'finding':'Checkpoint omits explicit completed/incomplete gate states, observed-main observation time/evidence, and current worker/operation dispositions. HANDOFF and RECOVERY-STATUS falsely direct recovery to the checkpoint for those omitted facts.','required_change':'Add a concise explicit phase table, observed main SHA/tree/time with evidence reference, current worker states and known current unknown operations (explicitly none when known); distinguish historical unknowns. Preserve existing observations and source-time fields.'},
    {'id':'P14-EARLY-002','severity':'mandatory','paths':['NEXT-TASK.md'],'finding':'The early-package first action says save/readback then implement, but the same file unconditionally says incomplete P14 delivery means delivery-only and stop. This makes early recovery stop before its selected implementation phase.','required_change':'Apply delivery-only recovery only when the final phase boundary has been reached. State that an early package resumes the declared phase after the early save gate and live reconciliation.'}
]
audit = {'schema':'ontokin.c271.p14-independent-early-package-review/1','reviewer':'/root/independent_review','created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':'python3 -I -B ' + str(OUT / 'review_early.py'),'environment':{'python':sys.version,'platform':platform.platform()},'archive':{'path':str(ARCHIVE),**archive_id},'verdict':'rejected_pending_recovery_instruction_corrections','checks':checks,'passed':sum(x['passed'] for x in checks),'failed':sum(not x['passed'] for x in checks),'mandatory_findings':findings,'limits':['Only package/metadata/Git bytes were read; no product, payload, host or restored code executed.','This review does not claim current Library save or fresh remote readback; P13 reconciliation is supported by its exact Git-pinned confirmation.','No historical full offline closure is required or claimed.','No mutations outside assigned review directory; no Git/index mutation.']}
for name, value in [('AUDIT.json',audit),('REVIEWED-FILES.json',{'schema':'ontokin.c271.p14-early-reviewed-files/1','reviewer':'/root/independent_review','files':reviewed})]:
    with (OUT / name).open('x') as f:
        json.dump(value,f,indent=2,sort_keys=True);f.write('\n')
report = '''# Early attempt001: rejected pending two recovery corrections

Archive: OntoKin_C271_P14_Loader_Path_Early_Recovery_2026-11-21.zip; 3,370,213 bytes; SHA-256 962f122f141ec27ce979f7878e53c2a0b29356ed69127ac6fd6e93fcc799af72.

Transport and source checks pass: 297 safe unique inert members, all 296 payload hashes, fresh extraction, both matching prompts, 239 exact Git snapshots, 43 recovery mappings and P13 archive/receipt/core/terminal reconciliation. Historical external dependencies and fixture-mode restrictions remain explicit; no full offline proof is demanded.

P14-EARLY-001 (mandatory): CHECKPOINT omits explicit completed/incomplete states, observed-main time/evidence and current worker/operation states, although HANDOFF and RECOVERY-STATUS claim those details are there. Add the concise gate table, observation and evidence, worker dispositions and explicit current unknown-operation status.

P14-EARLY-002 (mandatory): NEXT-TASK says to save early recovery then implement, but also unconditionally restricts incomplete P14 delivery to delivery-only then stop. Restrict that instruction to final phase-boundary recovery; early recovery must resume the declared implementation phase after its save gate and live reconciliation.

Preserve this rejected archive and evidence, issue a corrected candidate, and re-review before saving for implementation release. No product/payload/host code ran; no process or unknown write remains from this review.
'''
with (OUT / 'REPORT.md').open('x') as f:f.write(report)
print(json.dumps({'verdict':audit['verdict'],'passed':audit['passed'],'failed':audit['failed'],'findings':[x['id'] for x in findings],'audit':str(OUT / 'AUDIT.json')}))
