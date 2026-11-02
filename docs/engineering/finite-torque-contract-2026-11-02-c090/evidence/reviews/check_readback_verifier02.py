#!/usr/bin/env python3
"""Seven focused mixed-transport synthetic controls for the publication readback verifier."""
from pathlib import Path
from datetime import datetime, timezone
import base64
import copy
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys

ROOT = Path('/workspace/scratch/05c3f95a49c1/c090-reviews')
OUT = ROOT / 'integration-readback-review02-inputs'
HELPER = Path('/workspace/scratch/05c3f95a49c1/c090-tools/verify_published_readback.py')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def main():
    assert not OUT.exists();OUT.mkdir()
    shutil.copyfile(HELPER, OUT / HELPER.name)
    spec = importlib.util.spec_from_file_location('synthetic_fixture_helpers', ROOT / 'check_integration_helpers.py')
    module = importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    temporary, repo, baseline = module.make_repo()
    try:
        for name, data, mode in [
            ('a.txt', 'multibyte é漢🙂\r\n'.encode(), 0o644),
            ('b.txt', 'multibyte é漢🙂\r\n'.encode(), 0o644),
            ('binary.bin', b'\0\xff\xfe\x80binary\n', 0o644),
            ('empty.txt', b'', 0o644),
            ('run.py', b'#!/usr/bin/env python3\n', 0o755),
        ]:
            module.put(repo, 'docs/language-design/torque-v0.1/' + name, data, mode)
        (repo / 'docs/README.md').chmod(0o755)
        module.git(repo, 'add', '.')
        tree = module.git(repo, 'write-tree')
        commit = module.git(repo, 'commit-tree', tree, '-p', baseline, data=b'synthetic publication\n')
        publication_path = OUT / 'publication.json'
        prepare = subprocess.run([sys.executable, '-B', '/workspace/scratch/05c3f95a49c1/c090-tools/prepare_publication.py',
                                  '--repository', str(repo), '--parent', baseline, '--output', str(publication_path)],
                                 env=module.ENV, capture_output=True, text=True, check=True)
        publication = json.loads(publication_path.read_bytes())
        def tree_response(oid, recursive):
            arguments = ['ls-tree', '-z', '-t']
            if recursive:arguments.append('-r')
            raw = subprocess.check_output([module.REAL_GIT, '-C', str(repo), *arguments, oid], env=module.ENV)
            entries = []
            for line in raw.split(b'\0'):
                if not line:continue
                header, path = line.split(b'\t', 1);mode, kind, object_id = header.decode().split()
                entry = {'path': path.decode(), 'mode': mode, 'type': kind, 'sha': object_id}
                if kind == 'blob':entry['size'] = int(module.git(repo, 'cat-file', '-s', object_id))
                entries.append(entry)
            return {'sha': oid, 'truncated': False, 'tree': entries}
        docs_tree = module.git(repo, 'rev-parse', tree + ':docs')
        trees = {'observations': [
            {'prefix': '', 'expected_tree_sha': tree, 'recursive': False, 'response': tree_response(tree, False)},
            {'prefix': 'docs', 'expected_tree_sha': docs_tree, 'recursive': True, 'response': tree_response(docs_tree, True)},
        ]}
        raw_commit = {'sha': commit, 'parents': [{'sha': baseline}], 'tree': {'sha': tree}}
        blobs = {'observations': []}
        for oid in sorted({r['sha'] for r in publication['identities']}):
            data = subprocess.check_output([module.REAL_GIT, '-C', str(repo), 'cat-file', 'blob', oid], env=module.ENV)
            text = base64.b64encode(data).decode()
            wrapped = '\n'.join(text[i:i+8] for i in range(0, len(text), 8)) + ('\n' if text else '')
            blobs['observations'].append({'requested_sha': oid, 'response': {'sha': oid, 'size': len(data), 'encoding': 'base64', 'content': wrapped}})
        observations = []
        for name in ('complete', 'tampered-blob-bytes', 'missing-tree-entry', 'duplicate-blob-response', 'wrong-parent', 'wrong-fetch-ref', 'wrong-raw-path'):
            directory = OUT / name;directory.mkdir()
            candidate_trees, candidate_blobs, candidate_commit = copy.deepcopy(trees), copy.deepcopy(blobs), copy.deepcopy(raw_commit)
            if name == 'tampered-blob-bytes':
                item = next(r for r in candidate_blobs['observations'] if r['response']['size'] > 0)
                original = base64.b64decode(item['response']['content'])
                item['response']['content'] = base64.b64encode(bytes([original[0] ^ 1]) + original[1:]).decode()
            elif name == 'missing-tree-entry':
                candidate_trees['observations'][1]['response']['tree'].pop()
            elif name == 'duplicate-blob-response':
                candidate_blobs['observations'].append(copy.deepcopy(candidate_blobs['observations'][0]))
            elif name == 'wrong-parent':
                candidate_commit['parents'][0]['sha'] = '0' * 40
            raw_item = candidate_blobs['observations'].pop(0)
            raw_sha = raw_item['requested_sha']
            native_row = next(r for r in publication['identities'] if r['sha'] == raw_sha)
            raw_path = native_row['path']
            raw_data = base64.b64decode(raw_item['response']['content'])
            raw_directory = directory / 'raw';raw_directory.mkdir()
            payload = raw_directory / (raw_sha + '.bin');payload.write_bytes(raw_data)
            download_url = 'https://raw.githubusercontent.com/Omegapy/OntoKin/' + commit + '/' + raw_path
            provenance = directory / 'directory-observation.json'
            save(provenance, {'requested_ref': commit, 'listing': [{'path': raw_path, 'sha': raw_sha, 'download_url': download_url}]})
            raw_receipt = {'status': 'passed', 'api_variant': 'github_raw_download', 'requested_ref': commit,
                'requested_path': raw_path, 'requested_sha': raw_sha, 'http_status': 200,
                'payload_path': str(payload), 'bytes': len(raw_data), 'sha256': hashlib.sha256(raw_data).hexdigest(),
                'git_blob_sha1': raw_sha, 'request_url_without_query': download_url, 'response_url_without_query': download_url,
                'directory_observation': {'path': str(provenance), 'sha256': sha(provenance)}}
            if name == 'wrong-raw-path':raw_receipt['requested_path'] = 'runtime.txt'
            save(raw_directory / (raw_sha + '.json'), raw_receipt)
            save(raw_directory / (raw_sha + '-failed-http404.json'), {'status': 'failed', 'http_status': 404})
            for item in candidate_blobs['observations']:
                item.update(api_variant='github_fetch_file', requested_ref=commit,
                    requested_path=next(r['path'] for r in publication['identities'] if r['sha'] == item['requested_sha']))
                item['response'].pop('size', None)
            if name == 'wrong-fetch-ref':candidate_blobs['observations'][0]['requested_ref'] = '0' * 40
            save(directory / 'commit.json', candidate_commit)
            save(directory / 'trees.json', candidate_trees)
            save(directory / 'blobs/page-001.json', candidate_blobs)
            command = [sys.executable, '-B', str(OUT / HELPER.name), '--repository', str(repo),
                       '--publication', str(publication_path), '--expected-commit', commit,
                       '--commit', str(directory / 'commit.json'), '--trees', str(directory / 'trees.json'),
                       '--blobs', str(directory / 'blobs'), '--raw-downloads', str(raw_directory), '--output', str(directory / 'receipt.json')]
            run = subprocess.run(command, env=module.ENV, text=True, capture_output=True, timeout=30)
            (directory / 'stdout').write_text(run.stdout);(directory / 'stderr').write_text(run.stderr)
            receipt = json.loads((directory / 'receipt.json').read_bytes())
            expected = 'passed' if name == 'complete' else 'failed'
            correct = receipt['status'] == expected and run.returncode == (0 if name == 'complete' else 1)
            if name == 'complete':
                correct &= receipt['changed_files'] == 6 and receipt['unique_changed_blobs'] == 5
                correct &= len(receipt['files']) == 6 and all(r['api_blob_bytes_equal'] for r in receipt['files'])
            observations.append({'id': name, 'expected_status': expected, 'actual_status': receipt['status'],
                                 'passed': bool(correct), 'returncode': run.returncode, 'argv': command,
                                 'receipt': str((directory / 'receipt.json').relative_to(ROOT)),
                                 'receipt_sha256': sha(directory / 'receipt.json'), 'error': receipt.get('error')})
        result = {'schema_version': 'ontokin.c090-readback-verifier-focused-controls/1',
                  'recorded_utc': datetime.now(timezone.utc).isoformat(),
                  'status': 'passed' if all(r['passed'] for r in observations) else 'failed',
                  'scope': 'Seven synthetic mixed-transport local Git/API-shaped controls; no actual API request or publication claim',
                  'checks': observations, 'helper_sha256': sha(OUT / HELPER.name),
                  'current_helper_unchanged': sha(HELPER) == sha(OUT / HELPER.name),
                  'driver_sha256': sha(Path(__file__)), 'synthetic_baseline_commit': baseline,
                  'synthetic_target_tree': tree, 'synthetic_commit': commit,
                  'publication_sha256': sha(publication_path), 'prepare_stdout': prepare.stdout}
        save(ROOT / 'integration-readback-verifier-review02.json', result)
        print(json.dumps({'status': result['status'], 'cases': len(observations), 'helper_unchanged': result['current_helper_unchanged']}))
        return 0 if result['status'] == 'passed' else 1
    finally:
        shutil.rmtree(temporary)


if __name__ == '__main__':
    raise SystemExit(main())
