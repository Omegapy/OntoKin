"""Derive documentary input paths without importing or invoking either checker."""

from __future__ import annotations

import collections
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import posixpath
import re
import subprocess
from urllib.parse import unquote, urlsplit

ROOT = Path('/workspace/scratch/f8d879d19e34/OntoKin')
OUT = Path(__file__).parent
SUFFIXES = {'.md', '.markdown', '.html', '.htm'}


def visible_document(path):
    return Path(path).suffix.lower() in SUFFIXES and not any(
        part.startswith('.') or part in {'venv', 'node_modules', '__pycache__'}
        for part in Path(path).parts
    )


class References(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []

    def handle_starttag(self, tag, attrs):
        self.links.extend(value for key, value in attrs if key in {'href', 'src'} and value)

    handle_startendtag = handle_starttag


def mask_code(text):
    lines = text.splitlines(keepends=True)
    output = []
    fence = None
    front = bool(lines and lines[0].strip() == '---')
    for index, line in enumerate(lines):
        if front:
            output.append('\n' if line.endswith('\n') else '')
            if index and line.strip() in {'---', '...'}:
                front = False
            continue
        match = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$', line.rstrip('\r\n'))
        if fence:
            if match and match[1][0] == fence[0] and len(match[1]) >= fence[1] and not match[2].strip():
                fence = None
            output.append('\n' if line.endswith('\n') else '')
        elif match:
            fence = (match[1][0], len(match[1]))
            output.append('\n' if line.endswith('\n') else '')
        else:
            output.append(line)
    return re.sub(
        r'(?<!`)(`+)(?!`)([\s\S]*?)(?<!`)\1(?!`)',
        lambda match: ''.join('\n' if char == '\n' else ' ' for char in match[0]),
        ''.join(output),
    )


def document_links(text, markdown):
    if not markdown:
        parser = References()
        parser.feed(text)
        yield from parser.links
        return
    text = mask_code(text)
    definitions = {}
    for match in re.finditer(r'^ {0,3}\[([^\]\n]+)\]:\s*(?:<([^>\n]+)>|(\S+))', text, re.M):
        destination = match[2] or match[3]
        definitions[' '.join(match[1].split()).casefold()] = destination
        yield destination
    body = re.sub(r'^ {0,3}\[[^\]\n]+\]:[^\n]*', '', text, flags=re.M)
    index = 0
    while index < len(body):
        if body[index] != '[' or (index and body[index - 1] == '\\'):
            index += 1
            continue
        start = index
        end = start + 1
        depth = 1
        while end < len(body) and depth:
            if body[end] == '\\':
                end += 2
                continue
            if body[end] == '[':
                depth += 1
            elif body[end] == ']':
                depth -= 1
            end += 1
        if depth:
            index += 1
            continue
        label = body[start + 1:end - 1]
        if end < len(body) and body[end] == '(':
            position = end + 1
            while position < len(body) and body[position].isspace():
                position += 1
            if position < len(body) and body[position] == '<':
                close = body.find('>', position + 1)
                if close != -1:
                    yield body[position + 1:close]
                    index = close + 1
                    continue
            begin = position
            nested = 0
            while position < len(body):
                char = body[position]
                if char == '\\':
                    position += 2
                    continue
                if char == '(':
                    nested += 1
                elif char == ')':
                    if not nested:
                        break
                    nested -= 1
                elif char.isspace() and not nested:
                    break
                position += 1
            yield body[begin:position]
            index = max(position, end + 1)
        elif end < len(body) and body[end] == '[':
            close = body.find(']', end + 1)
            if close != -1:
                key = ' '.join((body[end + 1:close] or label).split()).casefold()
                if key in definitions:
                    yield definitions[key]
                index = close + 1
            else:
                index = end
        else:
            key = ' '.join(label.split()).casefold()
            if key in definitions:
                yield definitions[key]
            index = end
    parser = References()
    parser.feed(text)
    yield from parser.links


def main():
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    tracked = set(subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', head], cwd=ROOT, text=True).splitlines())
    documents = {path for path in tracked if visible_document(path)}
    # Include newly authored candidate documents, whose bodies the real checker also scans.
    present_docs = {path.relative_to(ROOT).as_posix() for path in ROOT.rglob('*')
                    if path.is_file() and visible_document(path.relative_to(ROOT).as_posix())}
    documents |= present_docs
    unavailable = sorted(path for path in documents if not (ROOT / path).is_file())
    if unavailable:
        (OUT / 'HYDRATION-DOCUMENTS-STILL-MISSING.txt').write_text('\n'.join(unavailable) + '\n')
        print(json.dumps({'ready': False, 'missing_documents': len(unavailable)}))
        return
    base = set((OUT / 'HYDRATION-STAGE1-TRACKED-PATHS.txt').read_text().splitlines())
    needed = set(base)
    reasons = collections.defaultdict(set)
    directories = {'.'}
    for path in tracked:
        directories.update(parent.as_posix() for parent in Path(path).parents)
    directory_targets = set()
    unknown = []
    new_candidate_targets = set()
    edge_count = 0
    for path in sorted(documents):
        text = (ROOT / path).read_text(encoding='utf-8')
        for raw in document_links(text, Path(path).suffix.lower() in {'.md', '.markdown'}):
            raw = html.unescape(re.sub(r'\\([!"#$%&\'()*+,\-./:;<=>?@\[\]\\^_`{|}~])', r'\1', raw)).strip()
            if not raw or raw.startswith('//') or re.match(r'^[A-Za-z][A-Za-z0-9+.-]*:', raw):
                continue
            parsed = urlsplit(raw)
            relative = unquote(parsed.path)
            target = posixpath.normpath(
                relative.lstrip('/') if relative.startswith('/') else posixpath.join(posixpath.dirname(path), relative)
            ) if relative else path
            edge_count += 1
            if target in tracked:
                needed.add(target)
                reasons[target].add('local document target')
            elif target in directories:
                directory_targets.add(target)
                if parsed.fragment:
                    prefix = '' if target == '.' else target + '/'
                    index_path = next((prefix + name for name in ['README.md', 'readme.md', 'index.md', 'index.html']
                                       if prefix + name in tracked), None)
                    if index_path:
                        needed.add(index_path)
                        reasons[index_path].add('directory anchor document')
                    else:
                        unknown.append({'source': path, 'link': raw, 'target': target, 'reason': 'no tracked directory anchor index'})
            elif (ROOT / target).exists() and (ROOT / target).resolve().is_relative_to(ROOT.resolve()):
                new_candidate_targets.add(target)
            else:
                unknown.append({'source': path, 'link': raw, 'target': target, 'reason': 'target not tracked or present'})
    for directory in sorted(directory_targets):
        if directory == '.' or any(path.startswith(directory + '/') for path in needed):
            continue
        children = sorted(path for path in tracked if path.startswith(directory + '/'))
        child = next((path for path in children if Path(path).suffix.lower() in {'.md', '.json', '.txt', '.py', '.toml'}), children[0])
        needed.add(child)
        reasons[child].add('real tracked child establishing linked directory')
    additions = sorted(needed - base)
    missing = sorted(path for path in needed if not (ROOT / path).exists())
    for name, paths in [('DOCUMENTARY-TRACKED-PATHS.txt', sorted(needed)),
                        ('DOCUMENTARY-MISSING-TRACKED-PATHS.txt', missing),
                        ('HYDRATION-STAGE2-TARGET-PATHS.txt', additions),
                        ('DOCUMENTARY-VISIBLE-DOCUMENTS.txt', sorted(documents))]:
        (OUT / name).write_text('\n'.join(paths) + '\n')
    report = {
        'schema': 'ontokin.c271.p23.documentary-hydration/1',
        'source_head': head,
        'method': 'Static dependency derivation from fully inspected checker source and separate standard-library link parser. Neither checker was imported or executed. No Git mutation or placeholders.',
        'counts': {'tracked_repository_files': len(tracked), 'documents_read': len(documents),
                   'tracked_visible_documents': len([path for path in tracked if visible_document(path)]),
                   'stage1_paths': len(base), 'stage2_target_paths': len(additions),
                   'required_tracked_paths': len(needed), 'missing_tracked_paths': len(missing),
                   'local_link_edges': edge_count},
        'candidate_targets_not_yet_tracked': sorted(new_candidate_targets),
        'unresolved_targets': unknown,
        'additional_path_reasons': {path: sorted(reasons[path]) for path in additions},
        'checker_identities': [{'path': path, 'bytes': (ROOT / path).stat().st_size,
                                'sha256': hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}
                               for path in ['tools/chat_workflow.py', 'docs/maintenance/reorganization-2026-10-17/verify_reorganization.py']],
        'limits': 'Path coverage only; no anchor correctness, source preservation, workflow acceptance or product execution result. Run actual unchanged checkers after hydration and include later P23 documents/refs.',
    }
    (OUT / 'DOCUMENTARY-HYDRATION.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'ready': True, **report['counts'], 'unresolved_targets': len(unknown)}))


if __name__ == '__main__':
    main()
