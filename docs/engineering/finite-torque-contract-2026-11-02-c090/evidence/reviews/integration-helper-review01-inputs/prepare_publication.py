#!/usr/bin/env python3
"""Describe an already staged exact Git tree for the GitHub Git-data API.

This helper does not contact GitHub or change a ref. It emits complete UTF-8
contents for text entries and separately lists binary blobs. The caller must
compare returned Git object IDs and perform expected-head publication/readback.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--parent', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit('Output must be a fresh path')

    def git(*argv):
        return subprocess.check_output(['git', '-C', str(args.repository), *argv])

    def tree_rows(ref):
        rows = {}
        for raw in git('ls-tree', '-rz', ref).split(b'\0'):
            if not raw:
                continue
            header, path = raw.split(b'\t', 1)
            mode, kind, sha = header.decode('ascii').split()
            if kind != 'blob' or mode not in ('100644', '100755'):
                raise ValueError('Only ordinary source blobs are allowed')
            rows[path.decode('utf-8')] = (mode, sha)
        return rows

    base_tree = git('rev-parse', args.parent + '^{tree}').decode().strip()
    tree = git('write-tree').decode().strip()
    old, current = tree_rows(base_tree), tree_rows(tree)
    if set(old) - set(current):
        raise ValueError('This contract checkpoint permits no source deletion')
    elements, binaries, identities = [], [], []
    for path, (mode, sha) in current.items():
        if old.get(path) == (mode, sha):
            continue
        data = git('cat-file', 'blob', sha)
        digest = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        if digest != sha:
            raise ValueError('Local native blob differs')
        row = {'path': path, 'mode': mode, 'type': 'blob'}
        identity = {**row, 'sha': sha, 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
        identities.append(identity)
        try:
            text = data.decode('utf-8')
            if '\0' in text:
                raise UnicodeError('NUL is not text')
            elements.append({**row, 'content': text})
        except UnicodeError:
            elements.append({**row, 'sha': sha})
            binaries.append(identity)
    result = {'parent': args.parent, 'base_tree': base_tree, 'tree': tree,
              'elements': elements, 'binary_blobs': binaries, 'identities': identities}
    args.output.write_text(json.dumps(result, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({'parent': args.parent, 'tree': tree, 'changed_files': len(elements),
                      'binary_blobs': len(binaries), 'bytes': sum(x['bytes'] for x in identities)}))


if __name__ == '__main__':
    main()
