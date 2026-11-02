#!/usr/bin/env python3
"""Verify saved GitHub Git-data responses against an immutable local source tree.

No network request or ref update occurs. The caller supplies the actual saved
API responses, and this program binds those files and every changed source blob
to the locally prepared publication. Output must be a fresh path outside the
repository. A failed receipt never claims publication/readback acceptance.
"""
import argparse
import base64
import binascii
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from urllib.parse import unquote, urlsplit, urlunsplit

SHA1 = re.compile(r'[0-9a-f]{40}\Z')
SHA256 = re.compile(r'[0-9a-f]{64}\Z')


class VerificationError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise VerificationError(message)


def native_id(kind, data):
    return hashlib.sha1(kind.encode('ascii') + b' ' + str(len(data)).encode('ascii') + b'\0' + data).hexdigest()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def source_path(value, allow_root=False):
    require(type(value) is str, 'Source path must be a native string')
    if allow_root and value == '':
        return value
    require(value and not value.startswith('/') and '\0' not in value,
            'Source path is empty, absolute or contains NUL')
    require(all(part not in ('', '.', '..') for part in value.split('/')),
            'Source path contains a noncanonical or escaping component')
    return value


def sha1(value, context):
    require(type(value) is str and SHA1.fullmatch(value) is not None,
            context + ' is not an immutable lowercase SHA-1 object ID')
    return value


def integer(value, context):
    require(type(value) is int and value >= 0, context + ' is not a native nonnegative integer')
    return value


def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'Duplicate JSON key: ' + key)
        result[key] = value
    return result


def reject_constant(value):
    raise VerificationError('Nonfinite JSON constant: ' + value)


class Audit:
    def __init__(self, repository):
        self.repository = repository
        self.inputs = {}
        self.native_blobs = {}
        self.environment = os.environ.copy()
        for key in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_OBJECT_DIRECTORY',
                    'GIT_ALTERNATE_OBJECT_DIRECTORIES'):
            self.environment.pop(key, None)
        self.environment.update(GIT_NO_REPLACE_OBJECTS='1', GIT_OPTIONAL_LOCKS='0',
                                GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
                                GIT_TERMINAL_PROMPT='0')

    def git(self, *arguments):
        return subprocess.check_output(['git', '-C', str(self.repository), *arguments], env=self.environment)

    def read_bytes(self, path):
        require(stat.S_ISREG(path.lstat().st_mode), 'Evidence must be a regular file: ' + str(path))
        data = path.read_bytes()
        identity = {'path': str(path), 'bytes': len(data), 'sha256': digest(data),
                    'mode': format(stat.S_IMODE(path.stat().st_mode), '04o')}
        require(str(path) not in self.inputs, 'An evidence file was supplied more than once: ' + str(path))
        self.inputs[str(path)] = identity
        return data

    def read_json(self, path):
        data = self.read_bytes(path)
        return json.loads(data.decode('utf-8'), object_pairs_hook=no_duplicate_keys,
                          parse_constant=reject_constant)

    def native_object(self, kind, oid):
        sha1(oid, 'Native ' + kind)
        data = self.git('cat-file', kind, oid)
        require(native_id(kind, data) == oid, 'Local native ' + kind + ' object does not hash to ' + oid)
        return data

    def blob(self, oid):
        if oid not in self.native_blobs:
            self.native_blobs[oid] = self.native_object('blob', oid)
        return self.native_blobs[oid]

    def entries(self, tree):
        self.native_object('tree', tree)
        result = {}
        for raw in self.git('ls-tree', '-rz', '-t', '--full-tree', tree).split(b'\0'):
            if not raw:
                continue
            header, raw_path = raw.split(b'\t', 1)
            mode, kind, oid = header.decode('ascii').split()
            path = source_path(raw_path.decode('utf-8'))
            require(path not in result, 'Duplicate native source path: ' + path)
            require((kind == 'tree' and mode == '040000') or
                    (kind == 'blob' and mode in ('100644', '100755')),
                    'Nonordinary source entry: ' + path)
            result[path] = {'mode': mode, 'type': kind, 'sha': sha1(oid, 'Native entry')}
        return result

    def verify_inputs_unchanged(self):
        for value in self.inputs.values():
            path = Path(value['path'])
            require(stat.S_ISREG(path.lstat().st_mode), 'Evidence file type changed during verification')
            data = path.read_bytes()
            require(len(data) == value['bytes'] and digest(data) == value['sha256'] and
                    format(stat.S_IMODE(path.stat().st_mode), '04o') == value['mode'],
                    'Evidence bytes or mode changed during verification: ' + str(path))


def unique_path_rows(value, label):
    require(type(value) is list, label + ' must be an array')
    rows = {}
    for row in value:
        require(type(row) is dict, label + ' item must be an object')
        path = source_path(row.get('path'))
        require(path not in rows, 'Duplicate ' + label + ' path: ' + path)
        rows[path] = row
    return rows


def verify(args, audit):
    require(audit.git('rev-parse', '--show-object-format').decode().strip() == 'sha1',
            'This source publication requires its existing SHA-1 Git object format')
    publication = audit.read_json(args.publication)
    require(type(publication) is dict, 'Publication description must be an object')
    parent = sha1(publication.get('parent'), 'Publication parent')
    target_tree = sha1(publication.get('tree'), 'Publication tree')
    base_tree = sha1(publication.get('base_tree'), 'Publication base tree')
    audit.native_object('commit', parent)
    require(audit.git('rev-parse', '--verify', parent + '^{tree}').decode().strip() == base_tree,
            'Publication base tree differs from its immutable parent')
    old_entries, entries = audit.entries(base_tree), audit.entries(target_tree)
    old = {p: r for p, r in old_entries.items() if r['type'] == 'blob'}
    current = {p: r for p, r in entries.items() if r['type'] == 'blob'}
    require(not set(old) - set(current), 'Publication unexpectedly deletes predecessor source files')
    changed = {p: r for p, r in current.items() if old.get(p) != r}
    described = unique_path_rows(publication.get('identities'), 'publication identity')
    require(set(described) == set(changed), 'Publication identities are not the exact native changed-path set')
    native_identities = {}
    for path, row in changed.items():
        data = audit.blob(row['sha'])
        expected = {'path': path, **row, 'sha256': digest(data), 'bytes': len(data)}
        integer(described[path].get('bytes'), 'Publication source byte length')
        require(described[path] == expected, 'Publication identity differs from native bytes/mode: ' + path)
        native_identities[path] = expected
    elements = unique_path_rows(publication.get('elements'), 'publication element')
    require(set(elements) == set(changed), 'Publication elements differ from the exact changed-path set')
    expected_binaries = {}
    for path, element in elements.items():
        row = native_identities[path]
        data = audit.blob(row['sha'])
        try:
            text = data.decode('utf-8')
            is_text = '\0' not in text
        except UnicodeDecodeError:
            text, is_text = None, False
        expected = {'path': path, 'mode': row['mode'], 'type': 'blob'}
        if is_text:
            expected['content'] = text
        else:
            expected['sha'] = row['sha']
            expected_binaries[path] = row
        require(element == expected, 'Publication transport differs from exact native blob: ' + path)
    binary_rows = unique_path_rows(publication.get('binary_blobs'), 'publication binary')
    for row in binary_rows.values():
        integer(row.get('bytes'), 'Publication binary byte length')
    require(binary_rows == expected_binaries,
            'Publication binary list differs from its native bytes')

    expected_commit = sha1(args.expected_commit, 'Expected remote commit')
    commit = audit.read_json(args.commit)
    require(type(commit) is dict and commit.get('sha') == expected_commit,
            'Returned commit SHA differs from expected commit')
    require(type(commit.get('parents')) is list and len(commit['parents']) == 1 and
            type(commit['parents'][0]) is dict and commit['parents'][0].get('sha') == parent,
            'Returned commit must have exactly the prepared parent')
    require(type(commit.get('tree')) is dict and commit['tree'].get('sha') == target_tree,
            'Returned commit tree differs from the prepared native tree')

    tree_document = audit.read_json(args.trees)
    require(type(tree_document) is dict and type(tree_document.get('observations')) is list,
            'Tree evidence must contain an observations array')
    tree_ids = {'': target_tree, **{p: r['sha'] for p, r in entries.items() if r['type'] == 'tree'}}
    file_observations, tree_receipts = {}, []
    for index, observation in enumerate(tree_document['observations']):
        require(type(observation) is dict, 'Tree observation must be an object')
        prefix = source_path(observation.get('prefix'), allow_root=True)
        require(prefix in tree_ids, 'Observed tree prefix is not a native target directory: ' + prefix)
        oid = sha1(observation.get('expected_tree_sha'), 'Expected observed tree')
        require(oid == tree_ids[prefix], 'Observed tree identity does not belong to its target prefix')
        audit.native_object('tree', oid)
        recursive = observation.get('recursive')
        require(type(recursive) is bool, 'Tree recursive selector must be a native Bool')
        response = observation.get('response')
        require(type(response) is dict and response.get('sha') == oid,
                'Returned tree SHA differs from the native expected prefix')
        require(response.get('truncated') is False, 'Returned tree is truncated or lacks a false truncation flag')
        require(type(response.get('tree')) is list, 'Returned tree entries must be an array')
        expected = {}
        leading = prefix + '/' if prefix else ''
        for full_path, row in entries.items():
            if not full_path.startswith(leading):
                continue
            relative = full_path[len(leading):]
            if relative and (recursive or '/' not in relative):
                expected[relative] = row
        observed = {}
        for entry in response['tree']:
            require(type(entry) is dict, 'Returned tree entry must be an object')
            relative = source_path(entry.get('path'))
            require(recursive or '/' not in relative, 'Nonrecursive tree response includes a nested path')
            require(relative not in observed, 'Duplicate path within a returned tree response: ' + relative)
            row = {'mode': entry.get('mode'), 'type': entry.get('type'),
                   'sha': sha1(entry.get('sha'), 'Returned tree entry')}
            require(relative in expected and row == expected[relative],
                    'Returned tree entry differs from native target: ' + leading + relative)
            observed[relative] = row
            full_path = leading + relative
            if row['type'] == 'blob':
                if full_path in changed and 'size' in entry:
                    require(integer(entry['size'], 'Tree blob size') == native_identities[full_path]['bytes'],
                            'Returned tree blob size differs: ' + full_path)
                if full_path in file_observations:
                    require(file_observations[full_path]['entry'] == row, 'Conflicting repeated tree path observation')
                else:
                    file_observations[full_path] = {'tree_observation_index': index, 'prefix': prefix, 'entry': row}
        require(observed == expected, 'Nontruncated tree response omits native target entries at prefix: ' + prefix)
        tree_receipts.append({'index': index, 'prefix': prefix, 'tree_sha': oid,
                              'recursive': recursive, 'entries': len(observed), 'complete_native_entries_equal': True})
    require(set(changed) <= set(file_observations), 'API tree evidence does not cover every changed source path')

    expected_blob_ids = {r['sha'] for r in native_identities.values()}
    require(args.blobs.is_dir() and not args.blobs.is_symlink(), 'Blob evidence path must be an ordinary directory')
    pages = sorted(args.blobs.glob('page-*.json'))
    blobs, blob_receipts = {}, []

    def path_ref_identity(observation, requested):
        path = source_path(observation.get('requested_path'))
        require(path in changed and changed[path]['sha'] == requested,
                'Transport requested path/SHA is not an immutable changed source path')
        require(observation.get('requested_ref') == expected_commit,
                'Transport requested ref differs from the expected immutable commit')
        return path

    def record_blob(requested, data, receipt):
        require(requested in expected_blob_ids, 'Unexpected blob outside the changed unique blob set: ' + requested)
        require(requested not in blobs, 'Duplicate observation for changed blob: ' + requested)
        require(native_id('blob', data) == requested, 'Returned bytes do not hash to the requested native blob')
        require(data == audit.blob(requested), 'Returned blob bytes differ from immutable local source')
        receipt.update(requested_sha=requested, bytes=len(data), sha256=digest(data),
                       git_blob_sha1=requested, native_bytes_equal=True)
        blobs[requested] = receipt
        blob_receipts.append(receipt)
    for page in pages:
        document = audit.read_json(page)
        require(type(document) is dict and type(document.get('observations')) is list,
                'Blob page must contain an observations array: ' + str(page))
        for index, observation in enumerate(document['observations']):
            require(type(observation) is dict, 'Blob observation must be an object')
            requested = sha1(observation.get('requested_sha'), 'Requested blob')
            require(requested in expected_blob_ids, 'Unexpected blob outside the changed unique blob set: ' + requested)
            require(requested not in blobs, 'Duplicate observation for changed blob: ' + requested)
            variant = observation.get('api_variant', 'github_git_blob')
            require(variant in ('github_git_blob', 'github_fetch_file'), 'Unsupported saved blob transport variant')
            requested_path = path_ref_identity(observation, requested) if variant == 'github_fetch_file' else None
            response = observation.get('response')
            require(type(response) is dict and response.get('sha') == requested,
                    'Returned blob SHA differs from requested blob')
            require(response.get('encoding') == 'base64', 'Returned blob encoding must be base64')
            content = response.get('content')
            require(type(content) is str and all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=\r\n' for c in content),
                    'Returned base64 has characters outside its alphabet or GitHub CR/LF line wrapping')
            compact = content.replace('\r', '').replace('\n', '')
            try:
                data = base64.b64decode(compact, validate=True)
            except (ValueError, binascii.Error) as error:
                raise VerificationError('Returned blob base64 is invalid: ' + requested) from error
            require(base64.b64encode(data).decode('ascii') == compact,
                    'Returned blob base64 has noncanonical padding or discarded bits')
            if variant == 'github_git_blob' or 'size' in response:
                size = integer(response.get('size'), 'Returned blob size')
                require(size == len(data), 'Returned blob length differs from its decoded bytes')
            record_blob(requested, data, {'page': str(page), 'observation_index': index,
                        'api_variant': variant, 'requested_path': requested_path,
                        'requested_ref': expected_commit if requested_path is not None else None,
                        'size_field_supplied': 'size' in response})

    ignored_raw_receipts = []
    directory_cache = {}
    if args.raw_downloads is not None:
        raw_root = args.raw_downloads.resolve(strict=True)
        require(raw_root.is_dir() and not args.raw_downloads.is_symlink(), 'Raw downloads must use an ordinary directory')

        def nested_objects(value):
            if type(value) is dict:
                yield value
                for child in value.values():
                    yield from nested_objects(child)
            elif type(value) is list:
                for child in value:
                    yield from nested_objects(child)

        def raw_url(value, path):
            require(type(value) is str, 'Raw URL must be a string')
            parsed = urlsplit(value)
            require(parsed.scheme == 'https' and parsed.hostname == 'raw.githubusercontent.com' and
                    not parsed.query and not parsed.fragment,
                    'Raw receipt URL must be a query-stripped HTTPS raw.githubusercontent.com URL')
            parts = unquote(parsed.path).split('/', 3)
            require(len(parts) == 4 and parts[0] == '' and parts[1] and parts[2] and
                    parts[3] == expected_commit + '/' + path,
                    'Raw URL does not identify the requested immutable commit/path')
            return value

        for receipt_path in sorted(raw_root.glob('*.json')):
            if SHA1.fullmatch(receipt_path.stem) is None:
                ignored_raw_receipts.append({'path': str(receipt_path), 'reason': 'Not an exact SHA-named passing receipt; retained separately'})
                continue
            raw_receipt = audit.read_json(receipt_path)
            require(type(raw_receipt) is dict, 'Raw download receipt must be an object')
            if raw_receipt.get('status') != 'passed':
                ignored_raw_receipts.append({'path': str(receipt_path), 'reason': 'Download did not pass; never used as successful readback'})
                continue
            requested = sha1(raw_receipt.get('requested_sha'), 'Raw requested blob')
            require(requested == receipt_path.stem, 'Raw receipt filename differs from requested SHA')
            require(raw_receipt.get('api_variant') == 'github_raw_download', 'Raw receipt has the wrong transport identity')
            requested_path = path_ref_identity(raw_receipt, requested)
            require(type(raw_receipt.get('http_status')) is int and raw_receipt['http_status'] == 200,
                    'Raw payload was not an actual HTTP 200 download')
            requested_url = raw_url(raw_receipt.get('request_url_without_query'), requested_path)
            raw_url(raw_receipt.get('response_url_without_query'), requested_path)
            payload = Path(raw_receipt.get('payload_path', ''))
            require(payload.is_absolute() and payload.resolve(strict=True) == raw_root / (requested + '.bin'),
                    'Raw payload path does not identify its exact SHA-named local download')
            data = audit.read_bytes(payload)
            require(integer(raw_receipt.get('bytes'), 'Raw receipt length') == len(data) and
                    raw_receipt.get('sha256') == digest(data) and raw_receipt.get('git_blob_sha1') == requested,
                    'Raw receipt length/SHA-256/native identity differs from actual downloaded bytes')
            provenance = raw_receipt.get('directory_observation')
            require(type(provenance) is dict and type(provenance.get('path')) is str,
                    'Raw receipt lacks actual directory-observation provenance')
            directory_path = Path(provenance['path'])
            if not directory_path.is_absolute():
                directory_path = raw_root.parent.parent / directory_path
            directory_path = directory_path.absolute()
            require(directory_path.resolve(strict=True).is_relative_to(raw_root.parent),
                    'Directory-observation provenance is outside the readback evidence root')
            if str(directory_path) not in directory_cache:
                directory_cache[str(directory_path)] = audit.read_json(directory_path)
            require(audit.inputs[str(directory_path)]['sha256'] == provenance.get('sha256'),
                    'Actual directory-observation file hash differs from the raw receipt')
            matching = []
            for item in nested_objects(directory_cache[str(directory_path)]):
                if item.get('path') == requested_path and item.get('sha') == requested and type(item.get('download_url')) is str:
                    parsed = urlsplit(item['download_url'])
                    clean = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, '', ''))
                    if clean == requested_url:
                        matching.append(item)
            require(matching, 'Raw receipt URL/path/SHA is absent from its actual saved directory response')
            record_blob(requested, data, {'page': str(receipt_path), 'observation_index': None,
                        'api_variant': 'github_raw_download', 'requested_path': requested_path,
                        'requested_ref': expected_commit, 'payload_path': str(payload),
                        'http_status': 200, 'directory_observation': provenance,
                        'downloader_sha256': raw_receipt.get('downloader_sha256')})
    require(set(blobs) == expected_blob_ids, 'Blob observations are not the complete unique changed-blob set')
    files = []
    for path in sorted(native_identities):
        row = native_identities[path]
        tree_proof = file_observations[path]
        require(tree_proof['entry'] == changed[path], 'Changed path tree proof differs from native source')
        blob_proof = blobs[row['sha']]
        require(blob_proof['sha256'] == row['sha256'] and blob_proof['bytes'] == row['bytes'],
                'Changed source file blob proof differs from publication identity')
        files.append({**row, 'tree_observation_index': tree_proof['tree_observation_index'],
                      'tree_prefix': tree_proof['prefix'], 'blob_page': blob_proof['page'],
                      'blob_observation_index': blob_proof['observation_index'],
                      'api_tree_mode_and_blob_equal': True, 'api_blob_bytes_equal': True})
    audit.verify_inputs_unchanged()
    return {'schema_version': 'ontokin.c090-published-source-readback/1', 'status': 'passed',
            'expected_commit': expected_commit, 'parent': parent, 'base_tree': base_tree, 'tree': target_tree,
            'changed_files': len(files), 'changed_file_bytes': sum(r['bytes'] for r in files),
            'unique_changed_blobs': len(blobs), 'unique_changed_blob_bytes': sum(r['bytes'] for r in blob_receipts),
            'tree_observations': tree_receipts, 'blob_observations': blob_receipts, 'files': files,
            'ignored_raw_failure_receipts': ignored_raw_receipts,
            'complete_changed_path_and_blob_coverage': True,
            'all_changed_source_bytes_modes_equal_native_prepared_tree': True,
            'input_evidence_files_unchanged_during_verification': True,
            'base64_policy': 'Permit GitHub CR/LF wrapping only; validate compact alphabet/padding, exact decoded bytes, native SHA-1, SHA-256 and length.',
            'scope': 'Caller-supplied saved GitHub API responses compared with immutable local objects; no network request or ref update performed.',
            'runtime_or_release_acceptance': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--publication', type=Path, required=True)
    parser.add_argument('--expected-commit', required=True)
    parser.add_argument('--commit', type=Path, required=True)
    parser.add_argument('--trees', type=Path, required=True)
    parser.add_argument('--blobs', type=Path, required=True)
    parser.add_argument('--raw-downloads', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.repository = args.repository.resolve(strict=True)
    output = args.output.absolute()
    if output.is_relative_to(args.repository) or output.resolve(strict=False).is_relative_to(args.repository) or output.is_symlink() or output.exists():
        print('Output must be a fresh ordinary path outside the reviewed repository', file=sys.stderr)
        return 1
    audit = Audit(args.repository)
    started = datetime.now(timezone.utc).isoformat()
    try:
        result = verify(args, audit)
    except (VerificationError, OSError, UnicodeError, json.JSONDecodeError, subprocess.CalledProcessError) as error:
        result = {'schema_version': 'ontokin.c090-published-source-readback/1', 'status': 'failed',
                  'error_type': type(error).__name__, 'error': str(error),
                  'complete_changed_path_and_blob_coverage': False,
                  'runtime_or_release_acceptance': False}
    result.update(started_utc=started, completed_utc=datetime.now(timezone.utc).isoformat(),
                  repository=str(args.repository), argv=[sys.executable, *sys.argv],
                  verifier_sha256=digest(Path(__file__).read_bytes()),
                  evidence_files=list(audit.inputs.values()))
    with output.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({k: result[k] for k in ('status', 'changed_files', 'unique_changed_blobs', 'error') if k in result}))
    return 0 if result['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
