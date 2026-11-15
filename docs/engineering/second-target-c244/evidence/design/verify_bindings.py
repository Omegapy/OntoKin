#!/usr/bin/env python3
"""Read-only bindings for the independent C244 design review; no native launch."""
import argparse
import hashlib
import json
import platform
import stat
import struct
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def run(repo, package, report):
    repo, package, report = map(Path, (repo, package, report))
    def git(*args):
        return subprocess.check_output(['git', '-C', str(repo), *args], text=True).strip()
    commit = git('rev-parse', 'HEAD')
    tree = git('rev-parse', 'HEAD^{tree}')
    assert commit == '8264db6e36b0c6118cf5b7ab2e41724569f72d90'
    assert tree == 'c62c61d0287d5d006d53f653a3df8267289d547c'
    assert not git('status', '--porcelain', '--untracked-files=all')
    inventory_path = 'docs/engineering/second-target-c243/evidence/PRIMARY-SOURCES.json'
    inventory = json.loads((repo / inventory_path).read_text())
    sources = []
    for record in inventory['sources']:
        data = (package / record['packagePath']).read_bytes()
        sha256 = hashlib.sha256(data).hexdigest()
        blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        assert len(data) == record['bytes']
        assert sha256 == record['sha256']
        assert blob == record['gitBlobSha1']
        sources.append({**record, 'matched': True})
    authorities = []
    for record in inventory['authorityDocuments']:
        actual = hashlib.sha256((repo / record['path']).read_bytes()).hexdigest()
        assert actual == record['sha256']
        authorities.append({**record, 'matched': True})
    bindings_path = 'docs/engineering/second-target-c220/evidence/INPUT-BINDINGS.json'
    bindings = json.loads((repo / bindings_path).read_text())
    glb_record = next(x for x in bindings['items'] if x['packagePath'].endswith('/after.glb'))
    glb_path = package / glb_record['packagePath']
    glb = glb_path.read_bytes()
    assert len(glb) == glb_record['bytes']
    assert hashlib.sha256(glb).hexdigest() == glb_record['sha256']
    assert stat.S_IMODE(glb_path.stat().st_mode) == glb_record['mode']
    magic, version, length = struct.unpack_from('<III', glb)
    assert (magic, version, length) == (0x46546C67, 2, len(glb))
    json_length, json_type = struct.unpack_from('<II', glb, 12)
    assert json_type == 0x4E4F534A
    doc = json.loads(glb[20:20 + json_length])
    part_map = json.loads((repo / 'docs/engineering/second-target-c220/evidence/PART-MAP.json').read_text())
    expected_pairs = sorted((e['glbNode'], e['glbMesh']) for e in part_map['entries'])
    actual_pairs = [(i, n['mesh']) for i, n in enumerate(doc['nodes'])]
    assert actual_pairs == expected_pairs
    assert len(doc['nodes']) == 18 and len(doc['meshes']) == 5
    assert not doc.get('skins') and not any('skin' in n for n in doc['nodes'])
    assert 'GODOT_single_root' not in doc.get('extensionsUsed', [])
    assert all(len(m['primitives']) == 1 for m in doc['meshes'])
    source_files = []
    for name in ('DECISION.md', 'test_decision.py'):
        relative = 'docs/engineering/second-target-c244/' + name
        current = (repo / relative).read_bytes()
        assert current == (package / 'source/c244' / name).read_bytes()
        source_files.append({'path': relative, 'bytes': len(current), 'sha256': hashlib.sha256(current).hexdigest()})
    changed = git('diff', '--name-only', '6bf7b9b1d53a4d8181679bf7bd8f7b5147023c01', 'HEAD').splitlines()
    assert changed == [x['path'] for x in source_files]
    assert not git('status', '--porcelain', '--untracked-files=all')
    result = {
        'schema': 'ontokin.c245.independent-design-bindings/0.1',
        'passed': True,
        'recordedAtUtc': datetime.now(timezone.utc).isoformat(),
        'reviewer': '/root/design_review',
        'commit': commit,
        'tree': tree,
        'baseline': '6bf7b9b1d53a4d8181679bf7bd8f7b5147023c01',
        'platform': platform.platform(),
        'python': sys.version,
        'scriptSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'sourceFiles': source_files,
        'pinnedSources': sources,
        'unchangedAuthorities': authorities,
        'fixture': {**glb_record, 'matched': True, 'nodeCount': 18, 'meshCount': 5, 'pairs': actual_pairs, 'skins': 0, 'godotSingleRoot': False, 'onePrimitivePerMesh': True},
        'changedFilesAgainstMain': changed,
        'wholeWorktreeCleanBeforeAndAfter': True,
        'nativeStarts': 0,
        'limitations': ['Static source/fixture checks only', 'No installed-build lineage or runtime/callback proof', 'No adversarial decision-model test execution by this reviewer']
    }
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'passed': True, 'pinnedSources': len(sources), 'unchangedAuthorities': len(authorities), 'fixtureNodes': len(actual_pairs), 'commit': commit, 'report': str(report)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repository')
    parser.add_argument('package')
    parser.add_argument('report')
    args = parser.parse_args()
    run(args.repository, args.package, args.report)
