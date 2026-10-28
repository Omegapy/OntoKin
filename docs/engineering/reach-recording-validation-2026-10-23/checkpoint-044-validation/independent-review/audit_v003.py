"""Independent metadata/ZIP audit of the immutable published C044 core.

Uses only Python stdlib and read-only Git commands. No product or archived code
is imported or executed, and no extraction, candidate arithmetic or tests run.
Outputs are exclusive-create; every failed attempt is retained.
"""
from __future__ import annotations

import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import traceback
import zipfile
import zlib

BASE = Path('/workspace/scratch/63c8eee975be')
ROOT = BASE / 'OntoKin-publication'
DOC_REL = 'docs/engineering/reach-recording-validation-2026-10-23'
DOC = ROOT / DOC_REL
PUB = BASE / 'c044-publication'
VALIDATION = BASE / 'c044-validation/attempt-001'
RESTORED = BASE / 'c044-restored-evidence'
OUTBASE = BASE / 'c044-validation/independent-review'
COMMIT = '725397be68153f27eaa128b1163bdfc3636e99c6'
TREE = 'd3a5609a2b39b0c3577b2d3065cfcbf65192bc51'
PARENT = '96b22349997b7d0d52262ea2f4cf4262b50365fd'
PARENT_TREE = 'd8c3a88f7a3017fedef667e217af76271068f560'
ARCHIVE_SHA = '53406dbde80cb37af0930f37385e03f6b8282ca9c23d020a30a5fdcb891b37a7'
FROZEN = {
    'p23_request.py': 'd3c2fff01dfd9ef66358ed805ed3f89f29e07b053b4b149aa99b6b1dfc7ff890',
    'run_pair.py': 'a492f0352ac66ab2542645fe4773dd0e8fa374dd1e654949aff81d4b66426db3',
    'angular_trace.py': 'c9510c2bf1d17d3a169c8157d28938442984418835e98e518fe2983e545f142d',
}
RAW_EXPECTED = {
    'c044-execution/pair-001/capture/trace.json': 'e2c992975ec7edf80e126f69b7f18261db6fcb1837d86e56612be16e8a0a246d',
    'c044-execution/pair-001/control/request-result.json': 'b12ab354da9f36816e9c88814d167068d2e1de2c41acdc65e59d54225e353d63',
    'c044-execution/pair-001/capture/request-result.json': '6d425e12f2c2211eeca38e26910907c4f2efd02e09147129bc945ce68e761044',
    'c044-execution/pair-001/pair-command.json': 'df98dc1ffde3b36f19ff298cdffd3dc0fade903496aee075323196afaa37f7ad',
    'c044-analysis/cache-review/attempt-001/audit.json': '1fc01b9731767b932db746034bc1d787b3c9bf82668cda38ee5bedbac93b323d',
}
NOW = lambda: datetime.now(timezone.utc).isoformat()
BOUND = {}


def check(value, why):
    if not value:
        raise AssertionError(why)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def git_hash(kind, raw):
    return hashlib.sha1(kind.encode() + b' ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def write(path, value):
    with path.open('xb') as stream:
        stream.write((json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n').encode())


def bound_read(path):
    check(path.is_file() and not path.is_symlink(), 'Regular evidence file: ' + str(path))
    raw = path.read_bytes()
    key = path.relative_to(BASE).as_posix()
    row = {'path': key, 'bytes': len(raw), 'sha256': sha(raw)}
    if key in BOUND:
        check(BOUND[key] == row, 'Evidence unchanged while read: ' + key)
    BOUND[key] = row
    return raw


def load(path):
    return json.loads(bound_read(path))


def safe_name(name):
    p = PurePosixPath(name)
    check(bool(name) and not p.is_absolute() and '\\' not in name and ':' not in name,
          'Safe POSIX relative name')
    check(all(part not in ('', '.', '..') for part in name.split('/')), 'No traversal or empty path segments')
    check(all(ord(c) >= 32 for c in name), 'No control characters in name')
    return p


def physical_files(root):
    paths = []
    for current, directories, files in os.walk(root, followlinks=False):
        current = Path(current)
        for name in tuple(directories):
            path = current / name
            if path == root / '.git':
                directories.remove(name)
            else:
                check(not path.is_symlink(), 'No directory symlink in audited tree')
        for name in files:
            path = current / name
            if path == root / '.git':
                continue
            check(stat.S_ISREG(path.lstat().st_mode) and not path.is_symlink(), 'Regular physical path')
            paths.append(path)
    return sorted(paths)


def source_inventory():
    rows = []
    for path in physical_files(ROOT):
        raw = path.read_bytes()
        rows.append({'path': path.relative_to(ROOT).as_posix(), 'bytes': len(raw),
                     'mode': '100755' if path.stat().st_mode & 0o111 else '100644',
                     'git_blob': git_hash('blob', raw), 'sha256': sha(raw)})
    rows.sort(key=lambda row: row['path'].encode('utf-8'))
    return {'source_commit': COMMIT, 'source_tree': TREE, 'files': rows,
            'file_count': len(rows), 'total_bytes': sum(r['bytes'] for r in rows)}


def reconstruct_trees(files, remote):
    """Reconstruct all Git tree object bytes from verified blobs and modes."""
    nested = {}
    for path, row in files.items():
        parts = safe_name(path).parts
        parent = nested
        for part in parts[:-1]:
            parent = parent.setdefault(part, {})
            check(isinstance(parent, dict), 'No file/directory collision')
        check(parts[-1] not in parent, 'Unique blob path')
        parent[parts[-1]] = (row['mode'], row['sha'])
    trees = {}

    def visit(node, path):
        entries = []
        for name, value in node.items():
            child = path + '/' + name if path else name
            if isinstance(value, dict):
                mode, blob, order = '40000', visit(value, child), name.encode() + b'/'
            else:
                mode, blob = value
                order = name.encode()
            entries.append((order, mode.encode() + b' ' + name.encode() + b'\0' + bytes.fromhex(blob)))
        raw = b''.join(data for _, data in sorted(entries))
        tree_sha = git_hash('tree', raw)
        trees[path] = tree_sha
        return tree_sha

    root_sha = visit(nested, '')
    expected = {r['path']: r['sha'] for r in remote['tree'] if r['type'] == 'tree'}
    check({k: v for k, v in trees.items() if k} == expected, 'Every reconstructed directory tree matches remote')
    check(root_sha == remote['sha'], 'Reconstructed root Git tree matches remote')
    return {'root': root_sha, 'directory_objects_including_root': len(trees)}


def main(out):
    started = NOW()
    print('Audit started', started, flush=True)
    # Only read-only Git operations; optional index locking is disabled.
    git_env = dict(os.environ, GIT_OPTIONAL_LOCKS='0')
    git_commands = [(['rev-parse', 'HEAD', 'HEAD^{tree}'], 'git-identity'),
                    (['status', '--porcelain=v1', '--untracked-files=all'], 'git-status-before'),
                    (['cat-file', 'commit', 'HEAD'], 'git-commit')]
    git_results = {}
    for arguments, label in git_commands:
        result = subprocess.run(['git', '-C', str(ROOT), *arguments], capture_output=True, env=git_env, check=False)
        (out / (label + '.stdout')).write_bytes(result.stdout)
        (out / (label + '.stderr')).write_bytes(result.stderr)
        check(result.returncode == 0 and result.stderr == b'', 'Read-only Git command succeeded: ' + label)
        git_results[label] = result.stdout
    check(git_results['git-identity'].decode().splitlines() == [COMMIT, TREE], 'Actual local core identity')
    check(git_results['git-status-before'] == b'', 'Actual core checkout initially clean')
    publication = load(PUB / 'core-publication.json')
    commit = load(PUB / 'core-commit.json')
    remote = load(PUB / 'core-tree.json')
    new_files = load(PUB / 'core-new-files.json')
    parent = load(BASE / 'recovery-review/parent-tree.json')
    check(publication['commit'] == commit['sha'] == COMMIT and publication['tree'] == remote['sha'] == TREE,
          'Retained GitHub immutable commit/tree responses')
    check(publication['remote_ref_readback']['object']['sha'] == COMMIT, 'Recorded branch readback')
    check(publication['parent'] == PARENT and [p['sha'] for p in commit['parents']] == [PARENT], 'Exact single parent')
    check(commit['tree']['sha'] == TREE and not remote['truncated'] and not parent['truncated'], 'Complete remote tree records')
    raw_commit = bound_read(PUB / 'core.commit')
    check(raw_commit == git_results['git-commit'] and git_hash('commit', raw_commit) == COMMIT, 'Exact original published commit bytes')
    headers = raw_commit.split(b'\n\n', 1)[0].splitlines()
    check(b'tree ' + TREE.encode() in headers and b'parent ' + PARENT.encode() in headers, 'Commit tree/parent object binding')
    parents = {r['path']: r for r in parent['tree'] if r['type'] == 'blob'}
    published = {r['path']: r for r in remote['tree'] if r['type'] == 'blob'}
    check(len(parents) == 2265 and len(published) == 2282, 'Expected exact source closure counts')
    check(all(r['type'] in ('tree', 'blob') for r in remote['tree']), 'No submodule or other remote object type')
    check(all(r['mode'] in ('100644', '100755') for r in published.values()), 'Only regular Git blob modes')
    before = source_inventory()
    write(out / 'inputs-before.json', before)
    check(before['file_count'] == 2282 and before['total_bytes'] == 485662995, 'All physical published core bytes')
    own = {r['path']: r for r in before['files']}
    check(set(own) == set(published), 'Exact physical/remote path closure')
    for path, row in published.items():
        check((row['sha'], row['mode'], row['size']) == (own[path]['git_blob'], own[path]['mode'], own[path]['bytes']),
              'Physical bytes/Git mode match remote: ' + path)
    for path, row in parents.items():
        check((row['sha'], row['mode'], row['size']) == (published[path]['sha'], published[path]['mode'], published[path]['size']),
              'Every original parent blob/mode/size preserved: ' + path)
    added = sorted(set(published) - set(parents))
    check(len(added) == 17 and new_files['parent_files_modified_or_removed'] == 0, 'Exactly seventeen additions')
    check(all(p.startswith(DOC_REL + '/checkpoint-044-') or p == DOC_REL + '/HANDOFF-044.md' for p in added), 'Only C044 doc/evidence additions')
    for row in new_files['new_files']:
        local = own[row['path']]
        check((row['sha'], row['mode'], row['bytes'], row['sha256']) ==
              (local['git_blob'], local['mode'], local['bytes'], local['sha256']), 'New-file publication binding')
    trees = reconstruct_trees(published, remote)
    parent_trees = reconstruct_trees(parents, parent)
    check(parent_trees['root'] == PARENT_TREE, 'Original parent root')
    print('All physical core files and both immutable Git trees verified', flush=True)

    manifest = load(DOC / 'checkpoint-044-evidence-manifest.json')
    packaging = load(PUB / 'packaging-receipt.json')
    check({k: v for k, v in manifest.items() if k != 'members'} == packaging, 'Packaging receipt matches published manifest')
    check(manifest['source_commit'] == PARENT and manifest['source_tree'] == PARENT_TREE, 'Archive source identity')
    parts = manifest['archive']['parts']
    check([p['path'] for p in parts] == ['checkpoint-044-evidence.zip.part%03d' % n for n in range(1, 10)], 'Exact ordered nine-part closure')
    joined_parts = []
    for row in parts:
        check(len(safe_name(row['path']).parts) == 1, 'Part beside manifest')
        raw = bound_read(DOC / row['path'])
        check(len(raw) == row['bytes'] and sha(raw) == row['sha256'], 'Archive part bytes/hash')
        joined_parts.append(raw)
    joined = b''.join(joined_parts)
    check(len(joined) == manifest['archive']['bytes'] == 6401045, 'Joined exact archive length')
    check(sha(joined) == manifest['archive']['sha256'] == ARCHIVE_SHA, 'Joined exact archive SHA256')
    check(joined == bound_read(PUB / 'checkpoint-044-evidence.zip'), 'Joined publication parts equal original packaged archive')
    expected = {r['path']: r for r in manifest['members']}
    check(len(expected) == len(manifest['members']) == manifest['member_count'] == 99, 'Unique 99-member manifest')
    payload = {}
    members = []
    with zipfile.ZipFile(io.BytesIO(joined)) as archive:
        infos = archive.infolist()
        check(len(infos) == 99 and len({i.filename for i in infos}) == 99, 'No duplicate ZIP members')
        check({i.filename for i in infos} == set(expected), 'Exact ZIP/manifest closure')
        check(len({i.header_offset for i in infos}) == 99, 'Distinct member local headers')
        check(archive.testzip() is None, 'Every ZIP CRC passes stdlib reader')
        for info in infos:
            name = safe_name(info.filename)
            check(not any('/'.join(name.parts[:i]) in expected for i in range(1, len(name.parts))), 'No file/descendant collision')
            mode = info.external_attr >> 16
            check(not info.is_dir() and stat.S_IFMT(mode) in (0, stat.S_IFREG) and not stat.S_ISLNK(mode), 'Regular ZIP member')
            check(info.create_system == 3 and not info.flag_bits & 1 and info.compress_type == zipfile.ZIP_DEFLATED,
                  'Unencrypted Unix deflate member')
            raw = archive.read(info)
            row = expected[info.filename]
            check(len(raw) == info.file_size == row['bytes'] and sha(raw) == row['sha256'], 'Member size/hash')
            check((zlib.crc32(raw) & 0xffffffff) == info.CRC, 'Independently computed member CRC')
            check(stat.S_IMODE(mode) == row['mode'] and row['mode'] in (0o600, 0o644), 'Exact safe member permission mode')
            original = BASE / info.filename
            check(raw == bound_read(original), 'Archived bytes equal retained original input')
            original_stat = original.stat()
            check(stat.S_IMODE(original_stat.st_mode) == row['mode'] and original_stat.st_mtime_ns == row['mtime_ns'],
                  'Retained original member mode and nanosecond time')
            payload[info.filename] = raw
            members.append({**row, 'zip_crc32': format(info.CRC, '08x'), 'compressed_bytes': info.compress_size,
                            'regular': True, 'crc_size_sha_mode_original_mtime_verified': True})
    check(sum(len(v) for v in payload.values()) == manifest['member_bytes'] == 49758827, 'Uncompressed member-byte closure')
    actual_restored = {p.relative_to(RESTORED).as_posix(): p for p in physical_files(RESTORED)}
    check(set(actual_restored) == set(expected), 'Actual roundtrip physical path closure')
    restored_rows = []
    for name, row in expected.items():
        path = actual_restored[name]
        raw = bound_read(path)
        st = path.stat()
        check(raw == payload[name] and sha(raw) == row['sha256'], 'Actual restored bytes/hash')
        check(stat.S_IMODE(st.st_mode) == row['mode'] and st.st_mtime_ns == row['mtime_ns'], 'Actual restored mode/mtime_ns')
        restored_rows.append({'path': name, 'bytes': len(raw), 'sha256': sha(raw),
                              'mode': stat.S_IMODE(st.st_mode), 'mtime_ns': st.st_mtime_ns})
    roundtrip = load(PUB / 'restore-roundtrip.json')
    check(roundtrip['status'] == 'passed' and roundtrip['members'] == 99 and roundtrip['bytes'] == 49758827 and
          roundtrip['all_roundtrip_hashes_modes_mtime_ns_verified'] is True, 'Root roundtrip receipt independently corroborated')
    for name in ('restore-roundtrip.stdout', 'restore-verify.stdout'):
        log = json.loads(bound_read(PUB / name))
        check(log['status'] == 'passed' and log['archive_sha256'] == ARCHIVE_SHA and log['members'] == 99,
              'Actual restore/verify command log')
    check(bound_read(PUB / 'restore-roundtrip.stderr') == b'' and bound_read(PUB / 'restore-verify.stderr') == b'',
          'Original restore commands have empty stderr')
    unknown = json.loads(payload['recovery-review/untracked-reconciliation.json'])
    unknown_path = 'recovery-review/' + unknown['preserved_path']
    check(unknown_path in payload and len(payload[unknown_path]) == unknown['bytes'] == 3670016, 'Unknown partial preserved in archive')
    check(sha(payload[unknown_path]) == unknown['sha256'] == 'a187c648bd1ae170f6b30044f0bba4c6cd741990edac341498883682f3425ea0',
          'Unknown partial exact original hash')
    check(expected[unknown_path]['mode'] == stat.S_IMODE(int(unknown['mode'], 8)) == 0o600 and
          expected[unknown_path]['mtime_ns'] == unknown['original_mtime_ns'], 'Unknown partial mode and time')
    check(unknown['origin'].startswith('unknown') and not (ROOT / unknown['original_path']).exists() and
          not (BASE / 'OntoKin' / unknown['original_path']).exists(), 'Unknown origin retained and file outside source checkouts')
    for row in manifest['excluded_duplicate_recovery_material']:
        check(row['path'] not in payload, 'Disclosed duplicate recovery material is excluded')
        raw = bound_read(BASE / row['path'])
        check(len(raw) == row['bytes'] and sha(raw) == row['sha256'], 'Excluded duplicate provenance binding')
    print('Nine-part archive, all 99 CRC/member bindings, and actual restored modes/times verified', flush=True)

    # Search concrete credential-bearing patterns; never retain or print matches.
    patterns = {
      'authenticated_http_query': re.compile(rb'https?://[^\s\x00"\'<>]+[?&](?:token|access_token|auth|signature|sig|x-amz-signature|x-amz-credential|x-amz-security-token)=[^\s\x00"\'<>]+', re.I),
      'http_embedded_credentials': re.compile(rb'https?://[^\s\x00/@:"\'<>]+:[^\s\x00/@"\'<>]+@', re.I),
      'github_pat_token': re.compile(rb'github_pat_[A-Za-z0-9_]{20,}'),
      'github_classic_token': re.compile(rb'gh[pousr]_[A-Za-z0-9]{20,}'),
      'bearer_credential': re.compile(rb'Bearer[ \t]+[A-Za-z0-9_.+/=-]{24,}', re.I),
    }
    scan_counts = Counter()
    scanned = dict(payload)
    for path in added:
        if '.zip.part' not in path:
            scanned['published-core/' + path] = bound_read(ROOT / path)
    for name, raw in scanned.items():
        for label, pattern in patterns.items():
            count = sum(1 for _ in pattern.finditer(raw))
            scan_counts[label] += count
            check(count == 0, 'Credential-bearing pattern detected in ' + name + '; match content suppressed')
    cleanup = json.loads(payload['c044-preparation/signed-url-cleanup.json'])
    for row in cleanup['entries']:
        check(not (BASE / 'recovery-review' / row['path']).exists(), 'Task-owned signed URL inventory remains absent')
        check(not any(PurePosixPath(p).name == row['path'] for p in payload), 'Private inventory excluded from archive')

    # Verify archive -> exact execution -> source/review binding without rerunning code.
    for path, expected_sha in RAW_EXPECTED.items():
        check(sha(payload[path]) == expected_sha, 'Previously reviewed raw evidence identity')
    snapshots = []
    for mode in ('control', 'capture'):
        for when in ('before', 'after'):
            name = 'c044-execution/pair-001/' + mode + '/inputs-' + when + '.json'
            check(sha(payload[name]) == 'db6308dff6f1643a99ecf389f9e3ec77f5136b7b5bb23cdbf22cc02aea848af5', 'Frozen complete request input inventory')
            snap = json.loads(payload[name])
            check(snap['commit'] == PARENT and snap['tree'] == PARENT_TREE and snap['file_count'] == 2265 and
                  snap['total_bytes'] == 477942773, 'Request input identity')
            snap_files = {r['path']: r for r in snap['files']}
            check(set(snap_files) == set(parents), 'All request input paths equal original parent')
            for path, row in snap_files.items():
                check((row['git_blob'], row['mode'], row['bytes'], row['sha256']) ==
                      (own[path]['git_blob'], own[path]['mode'], own[path]['bytes'], own[path]['sha256']), 'Request input equals preserved physical parent')
            snapshots.append(snap)
    check(all(s == snapshots[0] for s in snapshots), 'All four complete request inventories equal')
    executed_names = {'p23_request.py': 'executed-driver.py', 'run_pair.py': 'executed-runner.py', 'angular_trace.py': 'executed-tracer.py'}
    for name, expected_sha in FROZEN.items():
        prep = payload['c044-preparation/' + name]
        executed = payload['c044-execution/pair-001/' + executed_names[name]]
        check(prep == executed and sha(executed) == expected_sha, 'Frozen/prepared/executed file equality')
    frozen = json.loads(payload['c044-preparation/frozen-drivers.json'])
    for row in frozen['files']:
        check(row['sha256'] == FROZEN[row['path']] and row['bytes'] == len(payload['c044-preparation/' + row['path']]), 'Frozen hash receipt')
    static_review = json.loads(payload['c044-preparation/reviews/source-recovery-and-runner.json'])
    for row in static_review['reviewed_files']:
        check(row['sha256'] == FROZEN[PurePosixPath(row['path']).name], 'Independent static exact-hash review')
    requirements = json.loads(payload['c044-preparation/reviews/requirements-and-driver.json'])
    for row in requirements['reviewed'].values():
        check(row['sha256'] == FROZEN[PurePosixPath(row['path']).name], 'Requirements static exact-hash review')
    for row in requirements['source_bindings']:
        check(own[row['path']]['sha256'] == row['sha256'], 'Review original native source identity')
    source_binding = load(DOC / 'checkpoint-044-source-binding.json')
    check(source_binding['source_commit'] == PARENT and source_binding['source_tree'] == PARENT_TREE,
          'Published source binding')
    check(source_binding['runtime_changes'] is False and source_binding['release_acceptance'] is False,
          'Published scope limits')
    check(source_binding['execution_window_exception']['nominal_start_condition_met'] is False, 'Scheduling exception not erased')
    for mode in ('control', 'capture'):
        record = json.loads(payload['c044-execution/pair-001/' + mode + '/request-result.json'])
        check(record['source_commit'] == PARENT and record['source_tree'] == PARENT_TREE and record['exit_code'] == 1,
              'Original product failure and source identity')
        check(record['driver_sha256'] == FROZEN['p23_request.py'] and record['tracer_sha256'] == FROZEN['angular_trace.py'],
              'Request executed artifact identities')
        check(record['options'] == source_binding['request']['options'] and type(record['options']['fps']) is int,
              'Exact original request options and fps type')
        check(record['program_revision'] == source_binding['request']['program_revision'] and
              record['source_units'] == source_binding['request']['source_units'], 'Exact source-unit and revision provenance')
        check(sha((ROOT / record['source_files']).read_bytes()) == record['source_manifest_sha256'], 'Exact original P23 manifest')
        check(record['post_state']['work_limits'] == {'max_operations':100000, 'max_elapsed_ms':30000,
              'max_operand_bits':32768, 'max_cache_entries':256}, 'Original unchanged work caps')
        check(record['post_state']['shared_operations'] == 100001 and record['post_state']['reach_work']['operations'] == 80801,
              'Original failed-prefix counters retained')
    reference_resolutions = []

    def resolve(row, origin):
        path = row['path']
        if path.startswith('OntoKin-publication/'):
            raw = bound_read(BASE / path)
            location = 'published core'
        else:
            check(path in payload, 'Review/source evidence reference has archive member: ' + path)
            raw = payload[path]
            location = 'verified archive member'
        check(sha(raw) == row['sha256'] and ('bytes' not in row or len(raw) == row['bytes']), 'Reference hash/size: ' + path)
        reference_resolutions.append({'from': origin, 'path': path, 'sha256': sha(raw), 'bytes': len(raw), 'resolved_to': location})

    review_index = load(DOC / 'checkpoint-044-reviews.json')
    for row in review_index['review_records']:
        resolve(row, 'published review index')
    for group in ('inventory_bindings', 'evidence_bindings'):
        for row in source_binding[group]: resolve(row, 'published source binding: ' + group)
    census = bound_read(DOC / 'checkpoint-044-census.json')
    check(census == payload['c044-analysis/angular-review/angular-census.json'], 'Top-level census is exact archived census bytes')
    prose = json.loads(payload['c044-analysis/prose-review/prose-review.json'])
    for row in prose['reviewed_files']:
        resolve(row, 'exact prose review')
    for row in prose['evidence_bindings']:
        resolve(row, 'prose evidence binding')
    check(prose['unresolved_prose_issues'] == [], 'No unresolved reviewed prose issue')
    next_scope = load(DOC / 'checkpoint-044-next-scope.json')
    observed = next_scope['observed_opportunity']
    check((observed['calls'], observed['angular_signature_groups'], observed['spatial_signature_groups'], observed['whole_key_groups']) == (32,1,32,32), 'Next-scope observed group facts')
    for field in ('eligible_candidate_hits','net_saving_bound','candidate_cache_retention','complete_P23_cost_or_deficit'):
        check(observed[field] is None, 'No candidate or unseen-tail result asserted')
    check(observed['conditional_gross_repeated_sites'] == 434 and observed['original_envelope_charges'] == 960, 'Qualified gross-versus-original-cost metadata')
    for excluded in ('runtime edits','new product requests','candidate arithmetic replay','full-suite rerun','main integration','hosted jobs','release acceptance'):
        check(excluded in next_scope['out_of_scope'], 'Next scope keeps explicit excluded work')
    check('complete positive charged bound' in next_scope['implementation_gate'] and
          'independent authority review' in next_scope['implementation_gate'], 'Separate positive-bound implementation gate')
    check(next_scope['continuing_state']['original28'] == '24/28' and next_scope['continuing_state']['full_goal'] == 'open', 'Unchanged acceptance status')
    for filename in ('checkpoint-044-angular-census.md','HANDOFF-044.md'):
        text = bound_read(DOC / filename).decode()
        for phrase in ('24/28','C035','held','17:25:13.341049Z','17:26:00Z','434','gross','no elapsed neutrality'):
            check(phrase.lower() in text.lower(), 'Retained exact prose qualifier: ' + phrase)
        check('source-only' in text and 'net' in text and ('unseen' in text or 'unknown remainder after the original refusal' in text), 'Bounded future source feasibility and tail limits')
    restore_raw = bound_read(DOC / 'checkpoint-044-restore.py')
    restore_ast = ast.parse(restore_raw)
    imports = [n.module for n in ast.walk(restore_ast) if isinstance(n, ast.ImportFrom)] + [a.name for n in ast.walk(restore_ast) if isinstance(n, ast.Import) for a in n.names]
    check(not any(m and m.startswith('ontokin') for m in imports), 'Restore helper has no product import')
    check(not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ('eval','exec','compile','__import__') for n in ast.walk(restore_ast)), 'Restore helper has no dynamic code execution')
    check(b'ZipFile' in restore_raw and b'os.utime' in restore_raw and b'safe_name' in restore_raw,
          'Statically reviewed supplied restoration mechanism')
    print('Original request, review references, exact prose hashes, and next-scope limits verified', flush=True)

    # Independently corroborate actual root validation records, without rerunning.
    for name in ('core-publication.json','core-commit.json','core-tree.json','core-new-files.json','core.commit','core-identity.stdout','core-identity.stderr'):
        check(bound_read(VALIDATION / name) == bound_read(PUB / name), 'Validation exact published-core input copy')
    check(bound_read(VALIDATION / 'executed-validation-driver.py') == bound_read(PUB / 'validate_core.py'), 'Actual validation driver copy')
    validation_before = load(VALIDATION / 'inputs-before.json')
    validation_after = load(VALIDATION / 'inputs-after.json')
    check(validation_before == validation_after == before, 'Actual validation before/after equal independently audited core')
    receipt = load(VALIDATION / 'receipt.json')
    static_audit = load(VALIDATION / 'static-audit.json')
    command = load(VALIDATION / 'documentation-command.json')
    for name in ('stdout', 'stderr'):
        row = command[name]
        raw = bound_read(VALIDATION / row['path'])
        check(len(raw) == row['bytes'] and sha(raw) == row['sha256'], 'Actual documentation command log binding')
    doc_result = json.loads(bound_read(VALIDATION / 'documentation-check.stdout'))
    check(bound_read(VALIDATION / 'documentation-check.stderr') == b'', 'Documentation command empty stderr')
    check(command['exit_code'] == 0 and command['cwd'] == str(ROOT) and
          command['command'][1:] == ['docs/maintenance/reorganization-2026-10-17/verify_reorganization.py'], 'Actual unchanged documentation checker command')
    checker_path = 'docs/maintenance/reorganization-2026-10-17/verify_reorganization.py'
    check(published[checker_path]['sha'] == parents[checker_path]['sha'], 'Documentation checker byte-identical to parent')
    check(doc_result['status'] == 'passed' and doc_result['failures'] == [], 'Actual documentation pass')
    check((doc_result['sources_verified'],doc_result['sections_verified'],doc_result['links']['documents'],
           doc_result['links']['local_links'],doc_result['links']['anchors']) == (29,233,193,1593,90), 'Actual documentation metrics')
    check(receipt['source_commit'] == COMMIT and receipt['source_tree'] == TREE and receipt['status'] == 'passed', 'Actual validation receipt source/pass')
    check(receipt['product_requests'] == receipt['runtime_tests'] == 0 and receipt['release_acceptance'] is False,
          'Actual validation scope')
    check(static_audit['new_files'] == added and static_audit['status'] == 'passed', 'Actual static audit independently corroborated')
    check(receipt['documentation']['links'] == doc_result['links'] and receipt['documentation']['failures'] == [],
          'Validation summary matches raw output')

    after = source_inventory()
    write(out / 'inputs-after.json', after)
    check(before == after, 'Complete core remains physically unchanged through independent audit')
    final_git = subprocess.run(['git','-C',str(ROOT),'status','--porcelain=v1','--untracked-files=all'], capture_output=True, env=git_env, check=False)
    (out / 'git-status-after.stdout').write_bytes(final_git.stdout)
    (out / 'git-status-after.stderr').write_bytes(final_git.stderr)
    check(final_git.returncode == 0 and final_git.stdout == final_git.stderr == b'', 'Published core remains clean')
    for row in list(BOUND.values()):
        path = BASE / row['path']
        raw = path.read_bytes()
        check(len(raw) == row['bytes'] and sha(raw) == row['sha256'], 'All bound metadata/archive/restoration inputs stable')
    write(out / 'archive-members-audit.json', {'members': members, 'count':99, 'bytes':49758827})
    write(out / 'restored-files-audit.json', {'members':restored_rows, 'exact_path_hash_mode_mtime_ns_closure':True})
    write(out / 'reference-resolutions.json', reference_resolutions)
    write(out / 'input-bindings.json', sorted(BOUND.values(), key=lambda r:r['path']))
    result = {
      'schema':'ontokin.c044-independent-published-core-archive-audit/0.1',
      'status':'passed', 'started_utc':started, 'finished_utc':NOW(),
      'reviewer':'/root/source_recovery', 'script':str(Path(__file__).resolve()), 'script_sha256':sha(Path(__file__).read_bytes()),
      'exclusive_window':{'root_close_comment':6423191536, 'reviewer_handoff_after_root_close':True,
                          'declared_end_utc':'2026-10-26T18:03:00Z', 'system_wide_workload_monitor':False},
      'core':{'commit':COMMIT,'tree':TREE,'parent':PARENT,'parent_tree':PARENT_TREE,'files':2282,'bytes':485662995,
              'parent_files_preserved':2265,'new_files':added,'local_commit_exact_bytes_match':True,
              'all_physical_git_blobs_modes_sizes_match_remote':True,'all_remote_directory_tree_objects_reconstructed':trees,
              'original_parent_tree_objects_reconstructed':parent_trees,'before_after_identical':True,'git_clean_before_after':True},
      'archive':{'parts':9,'bytes':6401045,'sha256':ARCHIVE_SHA,'members':99,'member_bytes':49758827,
                 'duplicates_traversal_symlinks_encryption_or_nonregular_members':0,'all_crcs_bytes_hashes_modes_verified':True,
                 'all_original_member_bytes_modes_mtime_ns_match_manifest':True,'actual_root_roundtrip_exact_hash_mode_mtime_ns_closure':True,
                 'restoration_helper_reviewed_statically_only':True,'no_archived_code_executed_by_reviewer':True},
      'unknown_partial':{'origin':'unknown','path':unknown_path,'bytes':3670016,'sha256':unknown['sha256'],
                         'mode':384,'mtime_ns':unknown['original_mtime_ns'],'present_in_original_archive_and_restored_evidence':True,
                         'absent_from_both_source_checkouts':True},
      'credential_scan':{'scope':'all uncompressed archive members and new nonpart published C044 files',
                         'files_scanned':len(scanned),'pattern_counts':dict(scan_counts),
                         'private_signed_url_inventories_absent':True,'no_match_contents_logged':True,
                         'qualification':'Concrete authenticated-URL/GitHub-token/Bearer patterns only; not a universal proof that arbitrary bytes cannot encode a secret.'},
      'identities':{'all_four2265_file_execution_inventories_identical_and_parent_bound':True,
                     'frozen_prepared_executed_and_reviewed_driver_identities':FROZEN,
                     'raw_previously_reviewed_execution_and_cache_inputs':RAW_EXPECTED,
                     'review_index_records_resolved':len(review_index['review_records']),
                     'all_source_prose_and_review_hash_references_resolved':len(reference_resolutions),
                     'top_level_census_byte_identical_to_archived_census':True,
                     'exact_prose_review_hashes_match_published_markdown':True},
      'qualifications_retained':{'nominal_execution_window_start_not_met':True,'no_elapsed_neutrality':True,
          'gross434_is_not_net_or_eligible_candidate_saving':True,'no_candidate_retention_or_unseen_tail_result':True,
          'next_scope_is_source_retained_data_feasibility_with_separate_positive_bound_and_authority_gate':True,
          'existing_whole_key_lifetimes_and_endpoint_capacity_limits_retained':True,
          'original28':'24/28','C035':'held','release_acceptance':False,'formal_release_input_closure':'pending separate role audit'},
      'actual_published_core_validation':{'receipt':str(VALIDATION/'receipt.json'),'status':'passed',
          'started_utc':receipt['started_utc'],'finished_utc':receipt['finished_utc'],
          'documentation_command_reexecuted_by_reviewer':False,'raw_command_stdout_stderr_hashes_verified':True,
          'sources':29,'sections':233,'markdown_documents':193,'local_links':1593,'anchors':90,'failures':[],
          'all2282_file_before_after_manifests_independently_reconciled':True},
      'reviewer_work':{'product_imports':0,'product_requests':0,'runtime_tests':0,'candidate_arithmetic':0,
          'archived_scripts_executed':0,'restoration_helpers_executed':0,'new_extraction_runs':0,
          'commands':'Own stdlib audit plus read-only Git identity/status/object reads; source checkout not edited'},
      'limitations':['Remote identity uses retained GitHub core commit/tree/ref responses cryptographically reconciled to local bytes; no fresh branch or PR state is inferred.',
          'Existing independent neutrality/cache/angular audits are hash-bound here; this archive review does not rerun those analyses or product execution.',
          'The archive and supplied actual roundtrip are verified. No new restoration was executed by this reviewer.',
          'The original execution-window scheduling exception remains; metadata validation does not cure or relabel it.',
          'Final validation/review appendix and branch/PR closure remain root followup after this immutable core review.'],
      'decision':'PASS for exact published core archive/input/documentation evidence, with preserved qualifications; no runtime implementation or release approval',
      'pause_after_receipt':True}
    write(out/'result.json',result)
    print(json.dumps({'status':result['status'],'core':COMMIT,'tree':TREE,'archive_sha256':ARCHIVE_SHA,
                      'members':99,'member_bytes':49758827,'source_files':2282,'source_bytes':485662995,
                      'parent_files_preserved':2265,'resolved_references':len(reference_resolutions),
                      'result_sha256':sha((out/'result.json').read_bytes())},indent=2),flush=True)


if __name__=='__main__':
    check(len(sys.argv)==2 and re.fullmatch(r'attempt-[0-9]{3}',sys.argv[1]),'Use a fresh numbered audit attempt')
    out=OUTBASE/sys.argv[1]
    out.mkdir(exist_ok=False)
    try:
        main(out)
    except BaseException as error:
        failure={'status':'audit_preparation_or_validation_failed','at':NOW(),'script_sha256':sha(Path(__file__).read_bytes()),
                 'error_class':type(error).__name__,'error':str(error),'traceback':traceback.format_exc(),
                 'product_execution_performed':False,'core_mutated':False}
        write(out/'failure.json',failure)
        print(json.dumps(failure,indent=2),file=sys.stderr)
        raise
