#!/usr/bin/env python3
"""Verify every tracked byte/mode and the complete C089 preservation scope."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import stat
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--baseline', default='655097f016af17434b9b26fae22491f5f302aa18')
    parser.add_argument('--ref', default='HEAD')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit('Output must be a fresh path')

    def git(*argv):
        return subprocess.check_output(['git', '-C', str(args.repository), *argv])

    def rows(ref):
        result = {}
        for raw in git('ls-tree', '-rz', ref).split(b'\0'):
            if raw:
                header, path = raw.split(b'\t', 1)
                mode, kind, sha = header.decode().split()
                if kind != 'blob' or mode not in ('100644', '100755'):
                    raise ValueError('Unexpected native source kind')
                result[path.decode()] = (mode, sha)
        return result

    baseline = git('rev-parse', '--verify', args.baseline + '^{commit}').decode().strip()
    target = git('rev-parse', '--verify', args.ref).decode().strip()
    target_tree = git('rev-parse', target + '^{tree}').decode().strip()
    if git('write-tree').decode().strip() != target_tree:
        raise ValueError('Index does not match the exact target tree')
    old, current = rows(baseline), rows(target_tree)
    changed = [p for p in old if current.get(p) != old[p]]
    allowed_old = {'docs/README.md', 'STATUS.md'}
    if set(changed) - allowed_old or set(old) - set(current):
        raise ValueError('Predecessor path outside the declared coordination/navigation scope changed')
    added = sorted(set(current) - set(old))
    prefixes = ('docs/language-design/torque-v0.1/', 'docs/language-design/agent-v0.22/',
                'docs/engineering/finite-torque-contract-2026-11-02-c090/')
    if any(not p.startswith(prefixes) for p in added):
        raise ValueError('New file is outside the declared checkpoint scope')
    byte_count = 0
    for path, (mode, sha) in current.items():
        p = args.repository / path
        st = p.lstat()
        if not stat.S_ISREG(st.st_mode):
            raise ValueError('Nonregular source ' + path)
        expected_permissions = 0o755 if mode == '100755' else 0o644
        if stat.S_IMODE(st.st_mode) != expected_permissions:
            raise ValueError('Worktree permission mode differs: ' + path)
        data = p.read_bytes()
        actual = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        if actual != sha:
            raise ValueError('Worktree source differs: ' + path)
        byte_count += len(data)
    untracked = git('ls-files', '--others', '--exclude-standard', '-z').split(b'\0')
    if any(untracked):
        raise ValueError('Untracked source files remain')
    if git('write-tree').decode().strip() != target_tree:
        raise ValueError('Index changed during verification')
    result = {'schema_version': 'ontokin.c090-source-preservation/1', 'status': 'passed',
              'created_utc': datetime.now(timezone.utc).isoformat(), 'baseline': baseline,
              'requested_ref': args.ref, 'ref': target, 'tree': target_tree,
              'files': len(current), 'bytes': byte_count, 'old_files': len(old),
              'old_changed_paths': sorted(changed), 'added_files': added,
              'all_tracked_bytes_modes_match_native_tree': True,
              'old_runtime_tests_schemas_tools_workflows_contracts_gates_unchanged': True,
              'runtime_or_release_acceptance': False}
    with args.output.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('status', 'files', 'bytes', 'old_changed_paths')}))


if __name__ == '__main__':
    main()
