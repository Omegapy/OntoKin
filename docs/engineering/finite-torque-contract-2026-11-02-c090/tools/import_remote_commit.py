#!/usr/bin/env python3
"""Reproduce a fetched GitHub commit object and require its observed object ID."""
import argparse, datetime, hashlib, json, subprocess
from pathlib import Path

def identity(row):
    dt = datetime.datetime.fromisoformat(row['date'].replace('Z', '+00:00'))
    offset = dt.strftime('%z')
    return f"{row['name']} <{row['email']}> {int(dt.timestamp())} {offset}"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('repo', type=Path)
    parser.add_argument('response', type=Path)
    args = parser.parse_args()
    data = json.loads(args.response.read_text())
    v = data.get('verification') or {}
    candidates = []
    if v.get('payload') and v.get('signature'):
        header, message = v['payload'].split('\n\n', 1)
        signature = v['signature']
        for sig in (signature, signature.rstrip('\n')):
            candidates.append((header + '\ngpgsig ' + sig.replace('\n', '\n ') + '\n\n' + message).encode())
    else:
        # GitHub's JSON dates normalize the original timezone to UTC. Recover
        # only a candidate whose complete native hash matches the observed ID.
        prefix = '\n'.join(['tree ' + data['tree']['sha'],
            *['parent ' + p['sha'] for p in data['parents']]])
        zones = [f'{sign}{hour:02}{minute:02}' for sign in '+-' for hour in range(15) for minute in (0,15,30,45)]
        candidates = ((prefix + '\nauthor ' + identity(data['author'])[:-5] + az +
            '\ncommitter ' + identity(data['committer'])[:-5] + cz + '\n\n' + data['message'] + ending).encode()
            for az in zones for cz in zones for ending in ('', '\n', '\n\n'))
    matches = [raw for raw in candidates if hashlib.sha1(b'commit ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == data['sha']]
    if not matches:
        raise SystemExit('Observed commit could not be reproduced; no object written')
    raw = matches[0]
    oid = subprocess.check_output(['git', '-C', str(args.repo), 'hash-object', '-w', '-t', 'commit', '--stdin'], input=raw).decode().strip()
    if oid != data['sha']:
        raise SystemExit('Native imported ID differs')
    print(json.dumps({'status':'passed','sha':oid,'tree':data['tree']['sha'],'raw_bytes':len(raw),'raw_sha256':hashlib.sha256(raw).hexdigest(),'parents':[p['sha'] for p in data['parents']]}))

if __name__ == '__main__':
    main()
