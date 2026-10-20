"""Reconstruct exact retained ZIPs from verified repository parts, offline."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile


def identity(path):
    digest = hashlib.sha256()
    size = 0
    with path.open('rb') as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b''):
            size += len(data)
            digest.update(data)
    return {'sha256': 'sha256:' + digest.hexdigest(), 'byte_length': size}


def checked_file(root, record):
    name = record['path']
    if not isinstance(name, str) or Path(name).name != name or name in ('.', '..'):
        raise ValueError('Expected a plain archive or part filename')
    path = root / name
    if path.is_symlink() or not path.is_file():
        raise ValueError('Missing or nonregular retained part: ' + name)
    actual = identity(path)
    if any(actual[key] != record[key] for key in actual):
        raise ValueError('Retained part hash or length mismatch: ' + name)
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    output = args.output_dir.absolute()
    if output.exists():
        raise ValueError('Use a new output directory; existing archives are preserved')
    manifests = sorted(root.glob('*.zip.parts.json'))
    if not manifests:
        raise ValueError('No retained archive part manifests are present')
    plans = []
    for manifest in manifests:
        data = json.loads(manifest.read_text())
        if data['schema_version'] != 'ontokin.archive-parts/0.1':
            raise ValueError('Unknown archive part manifest')
        archive = data['archive']
        name = archive['path']
        if Path(name).name != name or not name.endswith('.zip'):
            raise ValueError('Expected a plain ZIP filename')
        parts = data['parts']
        if not parts or [row['path'] for row in parts] != [name + f'.part{i + 1:03}' for i in range(len(parts))]:
            raise ValueError('Archive parts are missing, duplicated or out of order')
        paths = [checked_file(root, row) for row in parts]
        if sum(row['byte_length'] for row in parts) != archive['byte_length']:
            raise ValueError('Archive part lengths do not add to the original length')
        plans.append((archive, paths))
    output.mkdir(parents=True)
    for archive, paths in plans:
        target = output / archive['path']
        with target.open('xb') as stream:
            for path in paths:
                with path.open('rb') as source:
                    for data in iter(lambda: source.read(1024 * 1024), b''):
                        stream.write(data)
        actual = identity(target)
        if any(actual[key] != archive[key] for key in actual):
            raise ValueError('Reconstructed archive differs from its original identity')
        with zipfile.ZipFile(target) as zipped:
            if zipped.testzip() is not None:
                raise ValueError('Reconstructed archive failed ZIP CRC verification')
        print(json.dumps({'archive': str(target), **actual, 'status': 'restored'}))


if __name__ == '__main__':
    main()
