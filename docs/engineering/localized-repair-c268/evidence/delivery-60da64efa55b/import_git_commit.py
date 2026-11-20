import datetime, hashlib, json, pathlib, subprocess, sys

source = json.loads(pathlib.Path(sys.argv[1]).read_text())
if 'structuredContent' in source:
    source = source['structuredContent']
if 'content' in source and isinstance(source['content'], str):
    source = json.loads(source['content'])
repo = sys.argv[2]
headers = ['tree ' + source['tree']['sha']]
headers.extend('parent ' + p['sha'] for p in source['parents'])
for role in ['author', 'committer']:
    person = source[role]
    dt = datetime.datetime.fromisoformat(person['date'].replace('Z', '+00:00'))
    headers.append(role + ' ' + person['name'] + ' <' + person['email'] + '> ' + str(int(dt.timestamp())) + ' +0000')
verification = source.get('verification', {})
payload = verification.get('payload')
if payload and verification.get('signature'):
    first, rest = payload.split('\n\n', 1)
    signature = verification['signature'].rstrip('\n').replace('\n', '\n ')
    bases = [first + '\ngpgsig ' + signature + '\n\n' + rest]
else:
    # GitHub normalizes API dates to UTC but retains the original Git timezone
    # Only an exact object hash match permits installation
    zones = ['+0000', '-0000', '-0700']
    zones.extend(f'{sign}{hour:02d}{minute:02d}' for sign in ['+', '-'] for hour in range(15) for minute in [0, 15, 30, 45])
    bases = []
    for zone in dict.fromkeys(zones):
        adjusted = [line[:-5] + zone if line.startswith(('author ', 'committer ')) else line for line in headers]
        bases.append('\n'.join(adjusted) + '\n\n' + source['message'])
matched = None
for base in bases:
    for suffix in ['', '\n']:
        data = (base + suffix).encode()
        identity = hashlib.sha1(b'commit ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        if identity == source['sha']:
            matched = data
assert matched is not None, 'Cannot reconstruct exact remote commit object'
created = subprocess.check_output(['git', '-C', repo, 'hash-object', '-t', 'commit', '-w', '--stdin'], input=matched).decode().strip()
assert created == source['sha']
print(json.dumps({'sha': created, 'tree': source['tree']['sha'], 'parents': [p['sha'] for p in source['parents']], 'exact_remote_commit_object': True}))
