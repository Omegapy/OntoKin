#!/usr/bin/env python3
"""Read published bytes using only scoped URLs actually returned by GitHub.

Private URL observations stay outside delivery evidence. Public receipts remove
all URL query strings. No repository file or remote reference is modified.
"""
import argparse
import concurrent.futures
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import urllib.error
import urllib.parse
import urllib.request


def digest(data):
    return hashlib.sha256(data).hexdigest()


def native(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def load(path):
    require(path.is_file() and not path.is_symlink(), 'Input is not an ordinary file')
    return json.loads(path.read_text())


def stripped(url):
    p = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((p.scheme, p.netloc, p.path, '', ''))


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('Redirect refused for pinned raw-file request')


def write_new(path, data):
    with path.open('xb') as stream:
        stream.write(data)


def json_new(path, value):
    write_new(path, (json.dumps(value, indent=2, sort_keys=True) + '\n').encode())


def prepare(args):
    plan = load(args.plan)
    ref = plan['ref']
    require(re.fullmatch(r'[0-9a-f]{40}', ref) is not None, 'Ref must be immutable SHA')
    files = plan['files']
    require(len({r['sha'] for r in files}) == len(files), 'Duplicate unique blob')
    urls, directories = {}, {}
    for directory in plan['directories']:
        private = load(args.private_directories / (str(directory['id']) + '.json'))
        public_path = args.public_directories / (str(directory['id']) + '.json')
        public = load(public_path)
        expected_request = 'https://api.github.com/repos/Omegapy/OntoKin/contents/' + directory['path'] + '?ref=' + ref
        require(private['request_url'] == expected_request and private['requested_ref'] == ref and
                private['directory'] == directory['path'], 'Private directory request differs')
        require(public['requested_ref'] == ref and public['directory'] == directory['path'],
                'Public directory request differs')
        public_rows = {r['path']: r for r in public['listing']}
        require(len(public_rows) == len(public['listing']), 'Duplicate public directory entry')
        for entry in private['listing']:
            path = entry['path']
            require(path.rsplit('/', 1)[0] == directory['path'] if '/' in path else directory['path'] == '',
                    'Directory entry has wrong parent')
            require(path in public_rows, 'Private entry absent from redacted observation')
            require(all(public_rows[path].get(k) == entry.get(k) for k in ('path', 'sha', 'size', 'type')),
                    'Private and public identity disagree')
            if entry['type'] != 'file':
                continue
            require(path not in urls, 'Duplicate private path')
            urls[path] = entry
            directories[path] = {'path': str(public_path), 'sha256': digest(public_path.read_bytes())}
    prepared = []
    for row in files:
        path = row['path']
        require(not path.startswith('/') and all(p not in ('', '.', '..') for p in path.split('/')),
                'Noncanonical source path')
        require(re.fullmatch(r'[0-9a-f]{40}', row['sha']) is not None and
                re.fullmatch(r'[0-9a-f]{64}', row['sha256']) is not None and
                type(row['bytes']) is int and 0 <= row['bytes'] <= 50_000_000, 'Invalid planned identity')
        require(path in urls, 'Missing actual GitHub file URL')
        entry = urls[path]
        require(entry['sha'] == row['sha'] and entry['size'] == row['bytes'], 'GitHub directory identity differs')
        url = entry['download_url']
        parsed = urllib.parse.urlsplit(url)
        require(parsed.scheme == 'https' and parsed.netloc == 'raw.githubusercontent.com' and
                not parsed.fragment and urllib.parse.unquote(parsed.path) == '/Omegapy/OntoKin/' + ref + '/' + path,
                'Download URL is not the exact pinned GitHub source path')
        prepared.append((row, url, directories[path]))
    return plan, prepared


def download_one(args, ref, item):
    row, url, source = item
    sha = row['sha']
    payload = args.output / (sha + '.bin')
    receipt_path = args.output / (sha + '.json')
    if receipt_path.exists():
        receipt = load(receipt_path)
        require(payload.is_file() and not payload.is_symlink(), 'Saved payload is missing or irregular')
        data = payload.read_bytes()
        require(receipt['status'] == 'passed' and receipt['requested_ref'] == ref and
                receipt['requested_path'] == row['path'] and receipt['requested_sha'] == sha and
                receipt['http_status'] == 200 and receipt['bytes'] == len(data) == row['bytes'] and
                receipt['sha256'] == digest(data) == row['sha256'] and native(data) == sha,
                'Previously completed download receipt or payload differs')
        return {'sha': sha, 'status': 'verified_existing'}
    require(not payload.exists(), 'Unreceipted payload requires reconciliation')
    started = datetime.now(timezone.utc).isoformat()
    observation = {'api_variant': 'github_raw_download', 'requested_ref': ref,
                   'requested_path': row['path'], 'requested_sha': sha,
                   'request_url_without_query': stripped(url), 'directory_observation': source,
                   'started_utc': started}
    try:
        opener = urllib.request.build_opener(NoRedirect())
        req = urllib.request.Request(url, headers={'Accept-Encoding': 'identity', 'User-Agent': 'OntoKin-C090-byte-readback'})
        with opener.open(req, timeout=30) as response:
            require(response.status == 200 and response.geturl() == url, 'Unexpected HTTP status or URL')
            length = response.headers.get('Content-Length')
            require(length is None or int(length) == row['bytes'], 'HTTP Content-Length differs')
            data = response.read(row['bytes'] + 1)
            observation.update(http_status=response.status, response_url_without_query=stripped(response.geturl()),
                               content_type=response.headers.get('Content-Type'), etag=response.headers.get('ETag'))
        observation.update(bytes=len(data), sha256=digest(data), git_blob_sha1=native(data))
        require(len(data) == row['bytes'] and digest(data) == row['sha256'] and native(data) == sha,
                'Downloaded actual bytes differ from immutable expected source')
        write_new(payload, data)
        observation.update(status='passed', payload_path=str(payload), completed_utc=datetime.now(timezone.utc).isoformat())
        json_new(receipt_path, observation)
        return {'sha': sha, 'status': 'passed', 'bytes': len(data)}
    except Exception as error:
        observation.update(status='failed', error_type=type(error).__name__,
                           error='HTTP or exact-byte readback failed; URLs and credential queries are not included.',
                           completed_utc=datetime.now(timezone.utc).isoformat())
        failure = args.output / (sha + '-failed-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f') + '.json')
        json_new(failure, observation)
        return {'sha': sha, 'status': 'failed', 'error_type': type(error).__name__}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plan', type=Path, required=True)
    p.add_argument('--private-directories', type=Path, required=True)
    p.add_argument('--public-directories', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--limit', type=int, default=60)
    args = p.parse_args()
    require(1 <= args.limit <= 100, 'Limit must be 1..100')
    args.output = args.output.absolute()
    require(not args.output.is_symlink(), 'Output cannot be a symlink')
    args.output.mkdir(parents=True, exist_ok=True)
    plan, prepared = prepare(args)
    existing = [item for item in prepared if (args.output / (item[0]['sha'] + '.json')).exists()]
    for item in existing:
        download_one(args, plan['ref'], item)
    pending = [item for item in prepared if not (args.output / (item[0]['sha'] + '.json')).exists()]
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for result in pool.map(lambda item: download_one(args, plan['ref'], item), pending[:args.limit]):
            results.append(result)
    failed = [r for r in results if r['status'] == 'failed']
    print(json.dumps({'status': 'failed' if failed else 'passed', 'selected': len(results),
                      'scope': 'This bounded download batch only; complete publication is verified separately.',
                      'existing_receipts_and_payloads_verified': len(existing),
                      'remaining_before': len(pending), 'downloaded_bytes': sum(r.get('bytes', 0) for r in results),
                      'failed': failed, 'plan_sha256': digest(args.plan.read_bytes()),
                      'script_sha256': digest(Path(__file__).read_bytes())}))
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
