"""Check byte preservation and syntax inventory; does not prove semantic equivalence."""
from pathlib import Path
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def run():
    manifest = json.loads((HERE / 'PRESERVATION.json').read_text())
    checks = []

    def check(name, passed, **detail):
        checks.append({'name': name, 'passed': bool(passed), **detail})

    for item in manifest['files']:
        path = item['path']
        original = (ROOT / item['original']).read_bytes()
        current = (ROOT / path).read_bytes()
        git_bytes = subprocess.check_output(['git', 'show', item['source_revision'] + ':' + path], cwd=ROOT)
        check(path + ': exact original', original == git_bytes and len(original) == item['bytes'] and hashlib.sha256(original).hexdigest() == item['sha256'])
        before, after = original.decode(), current.decode()
        headings = lambda text: re.findall(r'^#{1,6} .*$', text, re.M)
        links = lambda text: set(re.findall(r'(?<!!)\[[^\]]*\]\(([^)]+)\)', text))
        anchors = lambda text: re.findall(r'<a\s+id="[^"]+"\s*></a>', text)
        codes = lambda text: set(re.findall(r'`([^`\n]+)`', text))
        check(path + ': original headings', all(h in headings(after) for h in headings(before)))
        check(path + ': original link targets', links(before) <= links(after), missing=sorted(links(before) - links(after)))
        check(path + ': original anchors', anchors(before) == anchors(after))
        if path != 'STATUS.md':
            check(path + ': inline literals', codes(before) <= codes(after), missing=sorted(codes(before) - codes(after)))
        if path.endswith('SKILL.md'):
            check(path + ': frontmatter', before.split('---', 2)[:2] == after.split('---', 2)[:2])
    for item in manifest['protected_readmes']:
        check(item['path'] + ': README unchanged', hashlib.sha256((ROOT / item['path']).read_bytes()).hexdigest() == item['sha256'])
    for path in ['docs/workflow/registry.json', 'docs/workflow/CURRENT.json']:
        original = subprocess.check_output(['git', 'show', manifest['base_revision'] + ':' + path], cwd=ROOT)
        check(path + ': unchanged', (ROOT / path).read_bytes() == original)
    delta = subprocess.check_output(['git', 'diff', manifest['base_revision'], '--', 'docs/workflow/tasks/C268/', 'docs/engineering/localized-repair-c268/'], cwd=ROOT)
    check('C268 task and evidence unchanged', not delta)
    result = {'schema_version': 1, 'scope': 'Byte preservation and retained syntax only; independent semantic review is separate', 'base_revision': manifest['base_revision'], 'passed': all(c['passed'] for c in checks), 'checks': checks, 'originals': len(manifest['files']), 'protected_readmes': len(manifest['protected_readmes'])}
    (HERE / 'PRESERVATION-CHECKS.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'passed': result['passed'], 'checks': len(checks), 'originals': result['originals'], 'protected_readmes': result['protected_readmes'], 'failures': [c for c in checks if not c['passed']]}))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(run())
