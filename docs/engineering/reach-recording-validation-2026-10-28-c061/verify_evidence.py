#!/usr/bin/env python3
"""Verify C061 evidence bytes and partial Git identity without running OntoKin."""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import zipfile

def sha256(raw):
    return hashlib.sha256(raw).hexdigest()

def git_hash(kind, raw):
    return hashlib.sha1(f'{kind} {len(raw)}\0'.encode() + raw).hexdigest()

def safe(name):
    path = PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or str(path) != name:
        raise ValueError(f'Unsafe member name: {name}')
    return name

def tree_hash(entries):
    root = {}
    for entry in entries:
        parts = PurePosixPath(safe(entry['path'])).parts
        node = root
        for part in parts[:-1]:
            node = node.setdefault(part, {})
            if not isinstance(node, dict):
                raise ValueError('File/directory collision')
        if parts[-1] in node:
            raise ValueError('Duplicate source tree path')
        node[parts[-1]] = entry
    def build(node):
        rows = []
        for name, value in node.items():
            is_dir = 'path' not in value
            mode, sha = ('40000', build(value)) if is_dir else (value['mode'], value['sha'])
            rows.append(((name + ('/' if is_dir else '')).encode(),
                         mode.encode() + b' ' + name.encode() + b'\0' + bytes.fromhex(sha)))
        return git_hash('tree', b''.join(raw for _, raw in sorted(rows)))
    return build(root)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('checkpoint_dir', nargs='?', type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    root = args.checkpoint_dir.resolve()
    manifest = json.loads((root/'evidence-manifest.json').read_text())
    pieces = []
    for part in manifest['parts']:
        raw = (root/safe(part['path'])).read_bytes()
        if len(raw) != part['bytes'] or sha256(raw) != part['sha256'] or git_hash('blob', raw) != part['git_blob']:
            raise ValueError(f'Archive part mismatch: {part["path"]}')
        pieces.append(raw)
    raw = b''.join(pieces)
    if len(raw) != manifest['archive']['bytes'] or sha256(raw) != manifest['archive']['sha256']:
        raise ValueError('Reassembled archive mismatch')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = archive.namelist()
        expected = {item['path']: item for item in manifest['members']}
        if len(names) != len(set(names)) or set(names) != set(expected):
            raise ValueError('Archive member inventory mismatch')
        for name in names:
            safe(name)
            data = archive.read(name)
            item = expected[name]
            if len(data) != item['bytes'] or sha256(data) != item['sha256']:
                raise ValueError(f'Archive member mismatch: {name}')
        source = json.loads(archive.read('preparation/executed-tree.json'))
        checkout = json.loads(archive.read('evidence/execution-checkout.json'))
        actual_tree = tree_hash(source['entries'])
        commit_raw = archive.read('preparation/tooling-commit.raw')
        if (actual_tree != checkout['tree'] or git_hash('commit', commit_raw) != checkout['source_commit']
                or commit_raw.splitlines()[0] != f'tree {actual_tree}'.encode()):
            raise ValueError('Executed Git commit/tree identity mismatch')
        entries = {entry['path']: entry for entry in source['entries']}
        materialized = set()
        total = 0
        for item in checkout['files']:
            path = safe(item['path'])
            data = archive.read('source/'+path)
            original = entries[path]
            if (len(data) != item['bytes'] or sha256(data) != item['sha256']
                    or git_hash('blob', data) != original['sha'] or original['sha'] != item['git_blob']
                    or original['mode'] != item['mode']):
                raise ValueError(f'Materialized source mismatch: {path}')
            materialized.add(path)
            total += len(data)
        if (materialized.intersection(checkout['omitted']) or materialized.union(checkout['omitted']) != set(entries)
                or len(materialized) != checkout['materialized_count'] or total != checkout['materialized_bytes']
                or len(checkout['omitted']) != checkout['omitted_count']):
            raise ValueError('Partial checkout inventory mismatch')
    print(json.dumps({'status':'passed','archive_sha256':sha256(raw),'parts':len(pieces),
                      'members':len(names),'materialized_source_files':len(materialized),
                      'omitted_tracked_files':len(checkout['omitted']),
                      'executed_commit':checkout['source_commit'],'executed_tree':actual_tree,
                      'product_requests_executed':0,'release_acceptance':False},indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
