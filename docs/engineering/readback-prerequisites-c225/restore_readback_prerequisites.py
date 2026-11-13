#!/usr/bin/env python3
"""Restore only C199's exact retained CPU-readback prerequisites.

Dry-run by default. No Node, native application, product program or test runs.
The original HOST document remains historical; this is not a new host attestation.
"""
from __future__ import annotations

import argparse
import ctypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile

DEPENDENCIES = Path('/workspace/scratch/801d9d641f68/incoming-audit/work/prior-replay/evidence/c195-validation/receiving')
HOST_DESTINATION = Path('/workspace/scratch/801d9d641f68/c199-independent-preflight/HOST-RUNTIME-INVENTORY.json')
MANIFEST = 'docs/engineering/static-tray-qualification-c199/EXTERNAL-INPUTS.json'
ARCHIVE = 'docs/engineering/ownership-recovery-c195/evidence/recorded-evidence.tar.xz'
HOST_SOURCE = 'docs/engineering/static-tray-qualification-c199/evidence/preflight/HOST-RUNTIME-INVENTORY.json'
SOURCE_HASHES = {
    MANIFEST: '21fd6bad8738ed51d4ced8036a0fcde5dd046823f55f71de52b9b81df659ccd5',
    ARCHIVE: 'b1e54a6cfef133f7004b1988c90bc718fc954409843c2bcac3772d42e904a0c9',
    HOST_SOURCE: '2ed86412f09c74f5d3fb038f50e6417872b8eace0f89d7f168c79923efb14994',
    'tests/test_static_tray_readback_v01.py': '2f0abd812aa668b7abf9e249315acdb9c0fd175adb59672ab1c454679d494394',
    'prototypes/static_tray_v01/format_check.py': 'e0d71482b9878fbdf9ca1287013756fc0f6b9df530864f5634b8863354a29447',
    'prototypes/static_tray_v01/readback.mjs': '156c988ffc478adafe59c495a07e0a48f5ac77c12829d85d147838578b523b4c',
}
ARCHIVE_PREFIX = 'c195-validation/receiving/'


def sha256(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def no_symlink_ancestors(path):
    path = Path(path).absolute()
    for part in [path, *path.parents]:
        require(not part.is_symlink(), 'Refusing symlink path component: ' + str(part))


def regular_binding(path):
    path = Path(path)
    require(not path.is_symlink() and path.is_file(), 'Expected regular non-symlink file: ' + str(path))
    value = path.stat()
    require(stat.S_ISREG(value.st_mode), 'Expected regular file: ' + str(path))
    return {'sha256': sha256(path), 'size_bytes': value.st_size, 'mode': oct(stat.S_IMODE(value.st_mode))}


def compare_binding(path, expected, *, mode=False):
    actual = regular_binding(path)
    keys = ['sha256', 'size_bytes'] + (['mode'] if mode else [])
    require(all(actual[key] == expected[key] for key in keys), 'Binding differs: ' + str(path))
    return actual


def existing_dependency_state(path, expected):
    no_symlink_ancestors(path)
    if not path.exists():
        return {'state': 'absent'}
    require(path.is_dir(), 'Expected directory: ' + str(path))
    files, directories = set(), set()
    for item in path.rglob('*'):
        require(not item.is_symlink(), 'Refusing dependency symlink: ' + str(item))
        relative = item.relative_to(path).as_posix()
        if item.is_file():
            require(stat.S_ISREG(item.stat().st_mode), 'Nonregular dependency: ' + str(item))
            files.add(relative)
        else:
            require(item.is_dir(), 'Unexpected dependency entry: ' + str(item))
            directories.add(relative)
    allowed_directories = {p.as_posix() for name in expected for p in PurePosixPath(name).parents if p.as_posix() != '.'}
    require(files == set(expected), 'Preexisting dependency file set differs')
    require(directories == allowed_directories, 'Preexisting dependency directory set differs')
    rows = {name: compare_binding(path / name, binding) for name, binding in expected.items()}
    return {'state': 'complete_exact', 'files': rows}


def existing_host_state(path, expected):
    no_symlink_ancestors(path)
    if not path.exists():
        return {'state': 'absent'}
    return {'state': 'complete_exact', 'binding': compare_binding(path, expected)}


def atomic_report(path, report):
    no_symlink_ancestors(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, prefix=path.name + '.', delete=False) as stream:
        temporary = Path(stream.name)
        json.dump(report, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def rename_without_replacement(source, destination):
    # Linux renameat2 with RENAME_NOREPLACE prevents an unexpected replacement.
    library = ctypes.CDLL(None, use_errno=True)
    function = getattr(library, 'renameat2', None)
    require(function is not None, 'Atomic no-replace rename is unavailable')
    function.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    function.restype = ctypes.c_int
    code = function(-100, os.fsencode(source), -100, os.fsencode(destination), 1)
    if code != 0:
        number = ctypes.get_errno()
        raise OSError(number, os.strerror(number), str(destination))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True, type=Path)
    parser.add_argument('--report', required=True, type=Path)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    repo = args.repo.absolute()
    output = args.report.absolute()
    report_safe = False
    report = {
        'schema': 'ontokin.c225.retained-readback-preparation/0.1',
        'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
        'apply_requested': args.apply,
        'historical_host_inventory_only': True,
        'source_repository': str(repo),
        'targets': {'dependencies': str(DEPENDENCIES), 'host': str(HOST_DESTINATION)},
        'operation_log': [],
        'execution_counts': {'node': 0, 'ldd': 0, 'test_methods': 0, 'native': 0, 'product_source': 0},
    }
    staged_root = None
    installed = []
    expected = {}
    host_binding = {}
    try:
        # Reject symlink traversal before normalizing '..' for containment checks.
        no_symlink_ancestors(repo)
        no_symlink_ancestors(output)
        repo = repo.resolve()
        output = output.resolve()
        require(not output.is_relative_to(repo), 'Report must be outside the source repository')
        require(not output.is_relative_to(DEPENDENCIES), 'Report must be outside restored dependencies')
        require(output != HOST_DESTINATION, 'Report cannot overwrite the historical HOST inventory')
        require(not output.exists() or output.is_file(), 'Report destination must be a regular file or absent')
        report_safe = True
        report['source_repository'] = str(repo)
        require(repo.is_dir(), 'Source repository is missing')
        report['source_commit'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip()
        report['source_tree'] = subprocess.check_output(['git', 'rev-parse', 'HEAD^{tree}'], cwd=repo, text=True).strip()
        source_status = subprocess.check_output(['git', 'status', '--porcelain=v1'], cwd=repo, text=True)
        require(not source_status, 'Source checkout must be clean')
        report['source_clean'] = True
        report['source_bindings'] = {}
        for relative, expected_hash in SOURCE_HASHES.items():
            value = regular_binding(repo / relative)
            require(value['sha256'] == expected_hash, 'Source binding differs: ' + relative)
            report['source_bindings'][relative] = value
        manifest = json.loads((repo / MANIFEST).read_text())
        require(manifest['dependencies_root'] == str(DEPENDENCIES), 'Historical dependency target differs')
        runtime = manifest['runtime']
        require(runtime['host_inventory'] == str(HOST_DESTINATION), 'Historical HOST target differs')
        require(runtime['version'] == 'v24.22.1', 'Historical Node version differs')
        host_binding = {'sha256': runtime['host_inventory_sha256'], 'size_bytes': runtime['host_inventory_size_bytes']}
        compare_binding(repo / HOST_SOURCE, host_binding)
        report['runtime_bindings'] = {path: compare_binding(path, binding, mode=True) for path, binding in runtime['files'].items()}
        require(len(report['runtime_bindings']) == 10, 'Expected exactly ten runtime bindings')
        report['runtime_aliases'] = {}
        for name, expected_alias in runtime['aliases'].items():
            path = Path(name)
            actual = {'resolved_path': str(path.resolve(strict=True)), 'symlink': path.is_symlink(), 'link_target': os.readlink(path) if path.is_symlink() else None}
            require(actual == expected_alias, 'Runtime alias differs: ' + name)
            report['runtime_aliases'][name] = actual
        prefix = str(DEPENDENCIES) + '/'
        expected = {path[len(prefix):]: binding for path, binding in manifest['files'].items() if path.startswith(prefix)}
        require(len(expected) == 24, 'Expected exactly 24 retained dependency files')
        payloads, modes = {}, {}
        with tarfile.open(repo / ARCHIVE) as archive:
            selected = {}
            for member in archive.getmembers():
                if not member.name.startswith(ARCHIVE_PREFIX):
                    continue
                relative = member.name[len(ARCHIVE_PREFIX):]
                relevant = relative.startswith(('validator/package/', 'indexer-view/three/')) or relative == 'tools/three_loader.mjs'
                if not relevant:
                    continue
                require(relative not in selected, 'Duplicate archive member: ' + relative)
                selected[relative] = member
            require(set(selected) == set(expected), 'Retained archive dependency set differs')
            for relative, member in selected.items():
                require(member.isfile() and not member.issym() and not member.islnk(), 'Dependency member is not a regular file: ' + relative)
                relative_path = PurePosixPath(relative)
                require(not relative_path.is_absolute() and '..' not in relative_path.parts, 'Unsafe archive member: ' + relative)
                payload = archive.extractfile(member).read()
                require(len(payload) == expected[relative]['size_bytes'] and hashlib.sha256(payload).hexdigest() == expected[relative]['sha256'], 'Archive bytes differ: ' + relative)
                payloads[relative] = payload
                modes[relative] = member.mode & 0o777
        report['dependency_file_count'] = len(expected)
        report['dependency_bytes'] = sum(len(data) for data in payloads.values())
        report['dependency_bindings'] = expected
        report['before'] = {'dependencies': existing_dependency_state(DEPENDENCIES, expected), 'host': existing_host_state(HOST_DESTINATION, host_binding)}
        states = {row['state'] for row in report['before'].values()}
        require(len(states) == 1, 'Partial historical installation detected; reconcile it explicitly before retrying')
        report['preflight_passed'] = True
        report['passed'] = True
        report['outcome'] = 'DRY_RUN_READY' if states == {'absent'} else 'ALREADY_PRESENT_EXACT'
        atomic_report(output, report)
        if not args.apply or states == {'complete_exact'}:
            print(json.dumps({'passed': True, 'outcome': report['outcome'], 'report': str(output)}))
            return 0
        # Retain a separate pre-install receipt before either target can be created.
        atomic_report(output.with_name(output.stem + '-preflight' + output.suffix), report)
        require(sys.platform == 'linux', 'This exact historical restoration requires Linux')
        require(getattr(ctypes.CDLL(None), 'renameat2', None) is not None, 'Atomic no-replace rename is unavailable')
        staged_root = Path(tempfile.mkdtemp(prefix='c225-readback-stage-', dir=output.parent))
        staged_deps = staged_root / 'receiving'
        for relative, payload in payloads.items():
            target = staged_deps / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as stream:
                stream.write(payload)
            target.chmod(modes[relative])
        staged_host = staged_root / 'HOST-RUNTIME-INVENTORY.json'
        with staged_host.open('xb') as stream:
            stream.write((repo / HOST_SOURCE).read_bytes())
        staged_host.chmod(0o644)
        existing_dependency_state(staged_deps, expected)
        compare_binding(staged_host, host_binding)
        for target in [DEPENDENCIES, HOST_DESTINATION]:
            no_symlink_ancestors(target)
            require(not target.exists(), 'Target appeared after preflight: ' + str(target))
            target.parent.mkdir(parents=True, exist_ok=True)
            no_symlink_ancestors(target)
            require(target.parent.stat().st_dev == staged_root.stat().st_dev, 'Staging and target must use the same filesystem')
        for source, target in [(staged_deps, DEPENDENCIES), (staged_host, HOST_DESTINATION)]:
            rename_without_replacement(source, target)
            installed.append(target)
            report['operation_log'].append({'action': 'installed_without_replacement', 'path': str(target)})
            report['outcome'] = 'INSTALLATION_IN_PROGRESS'
            report['passed'] = False
            atomic_report(output, report)
        report['after'] = {'dependencies': existing_dependency_state(DEPENDENCIES, expected), 'host': existing_host_state(HOST_DESTINATION, host_binding)}
        report['passed'] = True
        report['outcome'] = 'RESTORED_EXACT_RETAINED_PREREQUISITES'
        report['unknown_mutations'] = []
        atomic_report(output, report)
        print(json.dumps({'passed': True, 'outcome': report['outcome'], 'dependency_files': 24, 'report': str(output)}))
        return 0
    except BaseException as error:
        report['passed'] = False
        report['outcome'] = 'REFUSED_OR_FAILED'
        report['error'] = type(error).__name__ + ': ' + str(error)
        report['rollback'] = []
        for path in reversed(installed):
            try:
                if path == HOST_DESTINATION:
                    compare_binding(path, host_binding)
                    path.unlink()
                else:
                    existing_dependency_state(path, expected)
                    shutil.rmtree(path)
                report['rollback'].append({'path': str(path), 'removed_owned_exact_install': True})
            except BaseException as rollback_error:
                report['rollback'].append({'path': str(path), 'error': str(rollback_error), 'manual_reconciliation_required': True})
        if report_safe:
            try:
                atomic_report(output, report)
            except BaseException as report_error:
                print('Unable to save report: ' + str(report_error), file=sys.stderr)
        else:
            print('Refused unsafe report destination without writing it', file=sys.stderr)
        print(json.dumps({'passed': False, 'error': report['error'], 'report': str(output)}))
        return 1
    finally:
        if staged_root is not None and staged_root.exists():
            shutil.rmtree(staged_root)


if __name__ == '__main__':
    raise SystemExit(main())
