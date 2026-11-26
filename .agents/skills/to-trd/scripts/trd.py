#!/usr/bin/env python3
"""Manage project-local Task Requirement Documents; Python 3.10+, stdlib only.

TRD Markdown is canonical. INDEX.md is a disposable projection. This helper
validates document structure, not user consent. trd_done means the requirements
document is approved; it grants no planning, implementation, or external authority.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import unicodedata
import uuid
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

SCHEMA_VERSION = 2
MAX_BYTES = 1_048_576
STATUSES = ('draft', 'trd_done', 'retired')
# Schema-1 compatibility only; ordinary operations never accept these aliases.
LEGACY_STATUSES = ('draft', 'not_done', 'done', 'retired')
LEGACY_STATE_MAPPING = dict(zip(LEGACY_STATUSES, ('draft', 'trd_done', 'trd_done', 'retired')))
TRANSITIONS = {
    'draft': {'trd_done', 'retired'},
    'trd_done': {'draft', 'retired'},
    'retired': {'draft'},
}
ACTIONS = {
    'create': 'TO-TRD-001', 'resume': 'TO-TRD-002', 'update': 'TO-TRD-003',
    'list': 'TO-TRD-004', 'show': 'TO-TRD-005', 'approve': 'TO-TRD-006',
    'legacy_complete': 'TO-TRD-007', 'retire': 'TO-TRD-008', 'reopen': 'TO-TRD-009',
    'validate': 'TO-TRD-010', 'reindex': 'TO-TRD-011', 'draft': 'TO-TRD-012',
    'migrate': 'TO-TRD-013',
}
MUTATING_ACTIONS = {ACTIONS[k] for k in (
    'create', 'update', 'approve', 'retire', 'reopen', 'draft', 'migrate')}
LEGACY_MUTATING_ACTIONS = (MUTATING_ACTIONS - {ACTIONS['migrate']}) | {ACTIONS['legacy_complete']}
SECTIONS = (
    'Destination', 'Captured user intent', 'Context and sources', 'In scope',
    'Out of scope', 'Task requirements', 'Decisions', 'Open questions',
    'Not yet specified', 'Assumptions',
)
LEGACY_SECTIONS = (*SECTIONS, 'Completion evidence')
META_KEYS = (
    'schema_version', 'trd_id', 'title', 'slug', 'created_at', 'updated_at',
    'status', 'revision', 'last_action_id', 'status_reason',
)
FILENAME_RE = re.compile(r'trd_([a-z0-9]+(?:-[a-z0-9]+)*)_(\d{4}-\d{2}-\d{2})\.md\Z')
ID_RE = re.compile(r'TRD-(\d{8})-[A-F0-9]{8}\Z')
REQ_HEADER_RE = re.compile(r'^### (REQ-\d{3,}) [—-] (.+)$', re.M)
EMPTY_EVIDENCE_RE = re.compile(
    r'^(?:none|n/?a|not yet verified|not verified|unverified|pending|todo|tbd|'
    r'not run|not tested|no evidence|no evidence yet)[.!]?$', re.I)
SECRET_PATTERNS = (
    re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    re.compile(r'\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b'),
    re.compile(r'\bgh[pousr]_[A-Za-z0-9]{30,}\b'),
    re.compile(r'''(?im)^\s*(?:api[_-]?key|password|access[_-]?token|secret)\s*[:=]\s*["']?[^\s"']{8,}'''),
)


class TrdError(Exception):
    """A bounded, machine-readable error with an optional durable receipt."""
    def __init__(self, code: int, category: str, message: str, **details):
        super().__init__(message)
        self.code, self.category, self.details = code, category, details


def require(condition: bool, message: str, code: int = 2, category: str = 'invalid') -> None:
    if not condition:
        raise TrdError(code, category, message)


def text_value(value, name: str, maximum: int = MAX_BYTES, multiline: bool = False) -> str:
    require(isinstance(value, str), f'{name} must be a string.')
    try:
        size = len(value.encode('utf-8'))
    except UnicodeError:
        raise TrdError(2, 'invalid', f'{name} contains invalid Unicode.') from None
    require(bool(value.strip()) and size <= maximum,
            f'{name} must be nonblank and at most {maximum} UTF-8 bytes.')
    require(not any(ord(c) < 32 and not (multiline and c in '\n\t') or ord(c) == 127
                    for c in value), f'{name} contains unsupported control characters.')
    return value


def secret_guard(text: str) -> None:
    require(not any(pattern.search(text) for pattern in SECRET_PATTERNS),
            'Possible credential or private-key material detected; redact before saving.')


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f'Duplicate JSON key: {key}.')
        result[key] = value
    return result


def load_payload(source: str) -> dict:
    if source == '-':
        raw = sys.stdin.buffer.read(MAX_BYTES + 1)
    else:
        path = Path(source).expanduser()
        require(not path.is_symlink() and path.is_file(), 'Payload must be a regular, non-symlink file.')
        with path.open('rb') as stream:
            raw = stream.read(MAX_BYTES + 1)
    require(len(raw) <= MAX_BYTES, 'Payload exceeds 1 MiB.')
    try:
        result = json.loads(raw.decode('utf-8'), object_pairs_hook=unique_object)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise TrdError(2, 'invalid', f'Payload is not valid UTF-8 JSON: {exc}') from None
    require(isinstance(result, dict), 'Payload must be a JSON object.')
    return result


def slugify(title: str) -> str:
    ascii_title = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', ascii_title).strip('-')[:60].rstrip('-') or 'trd'


def timestamp(value: str) -> datetime:
    require(isinstance(value, str) and bool(re.search(r'(?:Z|[+-]\d{2}:\d{2})$', value)),
            'Timestamps must include an explicit UTC offset.')
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        raise TrdError(2, 'invalid', 'Invalid ISO 8601 timestamp.') from None
    require(result.tzinfo is not None and result.utcoffset() is not None, 'Naive timestamp rejected.')
    return result


def now(timezone: str | None = None, floor: str | None = None) -> str:
    try:
        current = datetime.now(ZoneInfo(timezone)) if timezone else datetime.now().astimezone()
    except ZoneInfoNotFoundError:
        raise TrdError(2, 'invalid', f'Timezone is not available: {timezone}.') from None
    current = current.replace(microsecond=0)
    if floor and current < timestamp(floor):
        return floor
    return current.isoformat(timespec='seconds')


def md_escape(value: str) -> str:
    value = value.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return re.sub(r'([\\`*_|\[\]()])', r'\\\1', value)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def validate_body(
    body: str, *, schema_version: int = SCHEMA_VERSION,
    allow_legacy_open_questions: bool = True,
) -> tuple[dict[str, str], list[dict]]:
    require(type(schema_version) is int and schema_version in (1, SCHEMA_VERSION),
            'Unsupported schema_version.')
    legacy = schema_version == 1
    text_value(body, 'body', multiline=True)
    secret_guard(body)
    require(not re.search(r'\{\{[^{}]+\}\}', body), 'Unfilled template slot in body.')
    headings = list(re.finditer(r'^## (.+)$', body, re.M))
    require(tuple(h.group(1) for h in headings) == (LEGACY_SECTIONS if legacy else SECTIONS),
            'Body must contain the documented H2 sections exactly once, in order.')
    require(not body[:headings[0].start()].strip(), 'Body must start with ## Destination; the helper supplies H1.')
    sections = {}
    for i, heading in enumerate(headings):
        content = body[heading.end():headings[i+1].start() if i+1 < len(headings) else len(body)].strip()
        require(bool(content), f'Empty section: {heading.group(1)}. Use None. for an intentionally empty list.')
        sections[heading.group(1)] = content
    require(sections['Destination'] != 'None.' and sections['Captured user intent'] != 'None.',
            'Destination and captured intent must state the known outcome, not None.')
    req_text = sections['Task requirements']
    matches = list(REQ_HEADER_RE.finditer(req_text))
    require(len(matches) <= 2000, 'At most 2,000 requirements are supported per TRD.')
    if not matches:
        require(req_text == 'No task requirements captured yet.', 'No valid requirement blocks found.')
    else:
        require(not req_text[:matches[0].start()].strip(), 'Unexpected text before first requirement.')
    requirements = []
    ids = set()
    for i, match in enumerate(matches):
        req_id, title = match.groups()
        require(req_id not in ids, f'Duplicate requirement ID: {req_id}.')
        ids.add(req_id)
        block = req_text[match.end():matches[i+1].start() if i+1 < len(matches) else len(req_text)]
        names = ('Requirement', 'Source', 'Acceptance', 'Depends on') + (('Evidence',) if legacy else ())
        fields = {k: [] for k in names}
        checks = []
        for line in (line.strip() for line in block.splitlines() if line.strip()):
            check = re.fullmatch(r'- \[([ xX])\] Complete', line)
            if check and legacy:
                checks.append(check.group(1).lower() == 'x')
                continue
            field = re.fullmatch(r'- (' + '|'.join(names) + r'): (.+)', line)
            require(field is not None, f'{req_id}: unsupported requirement line: {line[:100]}')
            fields[field.group(1)].append(field.group(2).strip())
        if legacy:
            require(len(checks) == 1, f'{req_id}: legacy schema requires exactly one Complete checkbox.')
        require(all(fields.values()), f'{req_id}: a required field is missing.')
        require(len(fields['Requirement']) == 1 and len(fields['Depends on']) == 1,
                f'{req_id}: Requirement and Depends on must occur once.')
        dependency_text = fields['Depends on'][0]
        deps = [] if dependency_text == 'None.' else [part.strip() for part in dependency_text.split(',')]
        require(len(deps) == len(set(deps)) and all(re.fullmatch(r'REQ-\d{3,}', d) for d in deps),
                f'{req_id}: invalid dependency list.')
        requirement = dict(id=req_id, title=title, dependencies=deps, fields=fields)
        if legacy:
            # Preserve raw historical progress for explicit migration preflight.
            # Do not interpret it as verified implementation or apply old gates.
            requirement.update(complete=checks[0], evidence=fields['Evidence'])
        requirements.append(requirement)
    for req in requirements:
        require(set(req['dependencies']) <= ids and req['id'] not in req['dependencies'],
                f"{req['id']}: missing or self-referencing dependency.")
    # Kahn's algorithm avoids recursive stack limits for a large but bounded TRD.
    pending = {r['id']: set(r['dependencies']) for r in requirements}
    resolved = set()
    while pending:
        frontier = {key for key, deps in pending.items() if deps <= resolved}
        require(bool(frontier), 'Requirement dependency cycle detected.')
        resolved.update(frontier)
        for key in frontier:
            del pending[key]
    assumptions = sections['Assumptions']
    if assumptions != 'None.':
        require(all(line.startswith(('- Accepted: ', '- Unconfirmed: '))
                    for line in assumptions.splitlines() if line.strip()),
                'Each assumption must be labeled - Accepted: or - Unconfirmed:.')
    if not allow_legacy_open_questions:
        require(sections['Open questions'] == 'None.',
                'New or updated TRDs cannot store clarification questions; resolve them in conversation '
                'or describe unresolved scope declaratively under Not yet specified.')
        require('?' not in sections['Not yet specified'],
                'Not yet specified must describe unresolved scope declaratively, not as questions.')
    return sections, requirements


def completion_blockers(sections: dict[str, str], requirements: list[dict]) -> list[dict]:
    """Report document-content gates; semantic review and consent remain human concerns."""
    checks = (
        (not requirements, 'missing_requirements', 'Task requirements',
         'A completed TRD document requires at least one requirement.'),
        (sections['Open questions'] != 'None.', 'open_questions', 'Open questions',
         'Unresolved requirements questions must remain draft.'),
        (sections['Not yet specified'] != 'None.', 'unspecified_requirements', 'Not yet specified',
         'Unresolved requirement scope or acceptance must remain draft. '
         'Implementation choices belong in Decisions when the requirements already constrain them.'),
        ('- Unconfirmed: ' in sections['Assumptions'], 'unconfirmed_assumptions', 'Assumptions',
         'Unconfirmed assumptions must remain draft.'),
    )
    return [dict(code=code, section=section, message=message)
            for failed, code, section, message in checks if failed]


def gate(status: str, sections: dict[str, str], requirements: list[dict]) -> None:
    if status == 'trd_done' and (blockers := completion_blockers(sections, requirements)):
        raise TrdError(8, 'lifecycle', blockers[0]['message'], completion_blockers=blockers)


def normalized_body(body: str) -> str:
    """Only line endings and outer blank lines are representation equivalences."""
    require(isinstance(body, str), 'body must be a string.')
    try:
        require(len(body.encode('utf-8')) <= MAX_BYTES, 'body exceeds 1 MiB.')
    except UnicodeError:
        raise TrdError(2, 'invalid', 'body contains invalid Unicode.') from None
    normalized = body.replace('\r\n', '\n').strip('\n') + '\n'
    text_value(normalized, 'body', multiline=True)
    return normalized


def scope_signature(title: str, body: str) -> tuple[str, str]:
    return title, normalized_body(body)


@dataclass
class Record:
    path: Path
    meta: dict
    body: str
    sha256: str
    sections: dict[str, str]
    requirements: list[dict]

    def summary(self) -> dict:
        legacy = self.meta['schema_version'] == 1
        blockers = completion_blockers(self.sections, self.requirements) if not legacy else [
            dict(code='legacy_schema', section='schema_version',
                 message='Explicit schema-1 migration is required before document approval.')]
        if legacy:
            next_action = 'migrate'
        elif self.meta['status'] == 'trd_done':
            next_action = 'none'
        elif self.meta['status'] == 'retired':
            next_action = 'restore_to_draft'
        else:
            next_action = 'resolve_requirements' if blockers else 'request_approval'
        return dict(self.meta, path=f'TRDs/{self.path.name}', sha256=self.sha256,
                    requirement_count=len(self.requirements),
                    compatibility='legacy_v1_requires_migration' if legacy else 'current',
                    migration_required=legacy,
                    completion=dict(content_ready=None if legacy else not blockers,
                                    blockers=blockers, next_action=next_action))


def render_document(meta: dict, body: str) -> str:
    fields = '\n'.join(f'{key}: {json.dumps(meta[key], ensure_ascii=False)}' for key in META_KEYS)
    return f'---\n{fields}\n---\n\n# Task Requirement Document: {md_escape(meta["title"])}\n\n{body.strip()}\n'


def parse_document(path: Path, raw: bytes) -> Record:
    require(len(raw) <= MAX_BYTES, 'TRD exceeds 1 MiB.')
    try:
        text = raw.decode('utf-8').replace('\r\n', '\n')
    except UnicodeError:
        raise TrdError(2, 'invalid', 'TRD is not valid UTF-8.') from None
    require(text.startswith('---\n') and '\n---\n' in text[4:], 'Missing frontmatter boundaries.')
    front, rest = text[4:].split('\n---\n', 1)
    meta = {}
    for line in front.splitlines():
        require(': ' in line, 'Metadata must use one key: JSON-scalar pair per line.')
        key, value = line.split(': ', 1)
        require(key in META_KEYS and key not in meta, f'Unknown or duplicate metadata key: {key}.')
        try:
            meta[key] = json.loads(value)
        except json.JSONDecodeError:
            raise TrdError(2, 'invalid', f'Metadata field {key} is not a JSON scalar.') from None
    require(set(meta) == set(META_KEYS), 'Required metadata keys are missing.')
    require(type(meta['schema_version']) is int and meta['schema_version'] in (1, SCHEMA_VERSION),
            'Unsupported schema_version.')
    require(type(meta['revision']) is int and meta['revision'] >= 1, 'revision must be a positive integer.')
    for key in META_KEYS:
        if key not in ('schema_version', 'revision'):
            text_value(meta[key], key, 1024 if key == 'status_reason' else 256)
    text_value(meta['title'], 'title', 160)
    legacy = meta['schema_version'] == 1
    require(meta['status'] in (LEGACY_STATUSES if legacy else STATUSES), 'Unknown TRD status for schema.')
    require(meta['last_action_id'] in (LEGACY_MUTATING_ACTIONS if legacy else MUTATING_ACTIONS),
            'Invalid last_action_id for schema.')
    created, updated = timestamp(meta['created_at']), timestamp(meta['updated_at'])
    require(updated >= created, 'updated_at precedes created_at.')
    id_match, file_match = ID_RE.fullmatch(meta['trd_id']), FILENAME_RE.fullmatch(path.name)
    require(id_match is not None and file_match is not None, 'Invalid TRD ID or filename.')
    require(id_match.group(1) == created.strftime('%Y%m%d') and
            file_match.group(2) == created.date().isoformat(), 'ID/filename creation date mismatch.')
    require(file_match.group(1) == meta['slug'] and len(meta['slug']) <= 64, 'Slug/filename mismatch.')
    prefix = f'# Task Requirement Document: {md_escape(meta["title"])}\n\n'
    require(rest.lstrip('\n').startswith(prefix), 'Document H1 does not match metadata title.')
    body = rest.lstrip('\n')[len(prefix):].strip() + '\n'
    sections, requirements = validate_body(body, schema_version=meta['schema_version'])
    secret_guard(meta['title'] + '\n' + meta['status_reason'])
    if not legacy:
        gate(meta['status'], sections, requirements)
    return Record(path, meta, body, digest(raw), sections, requirements)


def sorted_records(records: list[Record]) -> list[Record]:
    return sorted(records, key=lambda r: (r.meta['schema_version'] == 1,
                  (LEGACY_STATUSES if r.meta['schema_version'] == 1 else STATUSES).index(r.meta['status']),
                  -timestamp(r.meta['updated_at']).timestamp(), r.meta['trd_id']))


def catalog_counts(records: list[Record]) -> dict:
    result = {'counts': {s: sum(r.meta['schema_version'] == SCHEMA_VERSION and
                               r.meta['status'] == s for r in records) for s in STATUSES}}
    if any(r.meta['schema_version'] == 1 for r in records):
        result['legacy_counts'] = {s: sum(r.meta['schema_version'] == 1 and r.meta['status'] == s
                                         for r in records) for s in LEGACY_STATUSES}
    return result


def render_index(records: list[Record]) -> str:
    counts = catalog_counts(records)
    latest = max((timestamp(r.meta['updated_at']) for r in records), default=None)
    snapshot = latest.isoformat(timespec='seconds') if latest else 'No records'
    lines = [
        '<!-- Generated from canonical trd_*.md files. Rebuild with to-trd reindex; do not edit this index. -->',
        '', '# Task Requirement Documents', '',
        f'Canonical snapshot: {snapshot}.', '',
        ' | '.join(f'{status}: {counts["counts"][status]}' for status in STATUSES), '',
    ]
    if 'legacy_counts' in counts:
        lines += ['Legacy schema 1 (explicit migration required): ' +
                  ' | '.join(f'{status}: {count}' for status, count in counts['legacy_counts'].items()), '']
    lines += ['| TRD ID | Name | State | Schema compatibility | Created | Updated | Revision |',
              '| --- | --- | --- | --- | --- | --- | --- |']
    for record in sorted_records(records):
        m = record.meta
        lines.append(f'| {m["trd_id"]} | [{md_escape(m["title"])}]({record.path.name}) | '
                     f'{m["status"]} | {"legacy schema 1; migrate" if m["schema_version"] == 1 else "current"} | '
                     f'{m["created_at"]} | {m["updated_at"]} | {m["revision"]} |')
    if not records:
        lines += ['', 'No TRDs have been created.']
    lines += ['', '`draft`: document content needs review. `trd_done`: the exact requirements document is complete and approved.',
              '`retired`: inactive document, retained in the catalog.',
              'Document approval grants no planning, implementation, installation, migration, Git, publication, deployment, or external authority.', '',
              'Use `$to-trd list`, `$to-trd show <TRD-ID>`, or `$to-trd reindex` explicitly.',
              'The TRD files, not this index, determine identity and state.', '']
    return '\n'.join(lines)


def migrated_body(record: Record) -> str:
    """Strip preflighted legacy progress only within its recognized sections."""
    headings = list(re.finditer(r'^## (.+)$', record.body, re.M))
    start = next(i for i, h in enumerate(headings) if h.group(1) == 'Task requirements')
    first, end = headings[start].end(), headings[start+1].start()
    requirements = re.sub(r'^[ \t]*- (?:\[ \] Complete[ \t]*|Evidence:.*)\n?', '',
                          record.body[first:end], flags=re.M)
    return (record.body[:first] + requirements + record.body[end:headings[-1].start()]).rstrip() + '\n'


def migration_preflight(record: Record) -> dict:
    current = record.meta['schema_version'] == SCHEMA_VERSION
    result = dict(already_current=current, eligible=False, blockers=[],
                  target_schema_version=SCHEMA_VERSION,
                  target_status=record.meta['status'] if current else LEGACY_STATE_MAPPING[record.meta['status']])
    if current:
        return result

    def blocked(field: str, reason: str) -> None:
        result['blockers'].append(dict(trd_id=record.meta['trd_id'], field=field, reason=reason))

    for requirement in record.requirements:
        if requirement['complete']:
            blocked(f"{requirement['id']}.Complete", 'A checked legacy requirement must be preserved under a separately reviewed decision.')
        for index, value in enumerate(requirement['evidence'], 1):
            if not EMPTY_EVIDENCE_RE.fullmatch(value.strip()):
                blocked(f"{requirement['id']}.Evidence[{index}]", 'Non-placeholder legacy evidence would be lost.')
    if not EMPTY_EVIDENCE_RE.fullmatch(record.sections['Completion evidence'].strip()):
        blocked('Completion evidence', 'Non-placeholder legacy document evidence would be lost.')
    if not result['blockers']:
        # Historical questions are preserved in drafts/retired records. A mapped
        # approved document still has to satisfy the current document-only gate.
        sections, requirements = validate_body(migrated_body(record))
        try:
            gate(result['target_status'], sections, requirements)
        except TrdError as exc:
            blocked('status', str(exc))
    result['eligible'] = not result['blockers']
    return result


class Store:
    def __init__(self, project_root: str | Path, timezone: str | None = None):
        root = Path(project_root).expanduser()
        require(root.is_dir(), f'Project root does not exist: {root}', 3, 'not_found')
        self.root = root.resolve()
        self.folder = self.root / 'TRDs'
        self.lock_path = self.folder / '.to-trd.lock'
        self.timezone = timezone
        self.cleanup_warnings: list[str] = []
        self._check_folder()

    def _check_folder(self) -> None:
        require(not self.folder.is_symlink(), 'TRDs must not be a symlink.', 5, 'unsafe_path')
        require(not self.folder.exists() or self.folder.is_dir(), 'TRDs must be a directory.', 5, 'unsafe_path')

    def _check_file(self, path: Path) -> None:
        self._check_folder()
        require(path.parent == self.folder and not path.is_symlink(),
                f'Unsafe managed file: {path.name}', 5, 'unsafe_path')
        require(not path.exists() or path.is_file(), f'Managed path is not a file: {path.name}', 5, 'unsafe_path')

    def _busy_check(self) -> None:
        if self.lock_path.exists() or self.lock_path.is_symlink():
            raise TrdError(7, 'busy', f'Catalog lock exists: {self.lock_path}. Do not remove it until no writer is active.')

    def _scan(self) -> list[Record]:
        self._check_folder()
        records = []
        if not self.folder.exists():
            return records
        ids = set()
        for path in sorted(self.folder.iterdir()):
            if not (path.name.startswith('trd_') and path.name.endswith('.md')):
                continue
            self._check_file(path)
            try:
                record = parse_document(path, path.read_bytes())
            except TrdError as exc:
                raise TrdError(5, 'integrity', f'{path.name}: {exc}') from None
            require(record.meta['trd_id'] not in ids, f'Duplicate TRD ID in {path.name}.', 5, 'integrity')
            ids.add(record.meta['trd_id'])
            records.append(record)
        return records

    def _index_warnings(self, records: list[Record]) -> list[str]:
        if not self.folder.exists():
            return ['TRDs is not initialized; read-only operation created nothing.']
        index = self.folder / 'INDEX.md'
        self._check_file(index)
        if not index.exists():
            return ['INDEX.md is missing; use explicit reindex. Canonical TRDs remain discoverable.']
        try:
            current = index.read_text(encoding='utf-8')
        except UnicodeError:
            return ['INDEX.md is not UTF-8; use explicit reindex.']
        return [] if current == render_index(records) else ['INDEX.md is stale; use explicit reindex.']

    def read(self) -> tuple[list[Record], list[str]]:
        self._busy_check()
        records = self._scan()
        warnings = self._index_warnings(records)
        self._busy_check()
        return records, warnings

    def resolve(self, selector: str, records: list[Record]) -> Record:
        text_value(selector, 'selector', 256)
        require(not any(c in selector for c in ('/', '\\')) and selector not in ('.', '..') and
                not selector.startswith('.'), 'Use an exact TRD ID, filename, or full title; paths are not selectors.')
        for field in ('trd_id', 'filename', 'title'):
            hits = [r for r in records if
                    (r.path.name == selector if field == 'filename' else
                     r.meta[field].casefold() == selector.casefold() if field == 'title' else
                     r.meta[field] == selector)]
            if len(hits) == 1:
                return hits[0]
            if len(hits) > 1:
                raise TrdError(4, 'ambiguous', 'Several TRDs have that title; select an exact ID.',
                               candidates=[r.summary() for r in hits])
        raise TrdError(3, 'not_found', f'No exact TRD match: {selector}.')

    @contextmanager
    def locked(self, initialize: bool = False, command: str = 'write'):
        self._check_folder()
        if initialize:
            self.folder.mkdir(exist_ok=True)
        require(self.folder.exists(), 'TRDs is not initialized.', 3, 'not_found')
        self._check_folder()
        try:
            self.lock_path.mkdir()
        except FileExistsError:
            self._busy_check()
            raise TrdError(7, 'busy', 'Catalog lock could not be acquired.') from None
        owner = self.lock_path / 'owner.json'
        try:
            owner.write_text(json.dumps({'process_id': os.getpid(), 'acquired_at': now(self.timezone), 'command': command},
                                        indent=2) + '\n', encoding='utf-8')
            self._check_file(self.folder / 'INDEX.md')
            _ontology_checkpoint()
            yield
        finally:
            try:
                if owner.exists() and not owner.is_symlink():
                    owner.unlink()
                self.lock_path.rmdir()
            except OSError:
                self.cleanup_warnings.append(f'Lock cleanup needs inspection: {self.lock_path}')

    def atomic_write(self, path: Path, text: str, expected: str | None = None, new: bool = False) -> None:
        """Publish one file atomically; the caller holds the cooperative catalog lock."""
        self._check_file(path)
        temp_path = None
        try:
            fd, name = tempfile.mkstemp(prefix='.to-trd-tmp-', dir=self.folder)
            temp_path = Path(name)
            with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as stream:
                stream.write(text)
                stream.flush()
                os.fsync(stream.fileno())
            self._check_file(path)
            if new:
                require(not path.exists(), 'Creation target already exists; no overwrite performed.', 5, 'integrity')
            if expected is not None:
                require(path.exists() and digest(path.read_bytes()) == expected,
                        'Document changed before publication; reread before retrying.', 6, 'stale')
            _ontology_checkpoint(targets=False)
            os.replace(temp_path, path)
        finally:
            if temp_path is not None and temp_path.exists():
                temp_path.unlink()

    def _expect(self, record: Record, expected: str) -> None:
        require(isinstance(expected, str) and re.fullmatch(r'[a-f0-9]{64}', expected) is not None,
                'A lowercase SHA-256 from show is required.')
        require(record.sha256 == expected, 'Stale document hash; reread and reconsider the edit.', 6, 'stale')

    def _commit(self, meta: dict, body: str, path: Path, records: list[Record], expected: str | None = None) -> dict:
        raw = render_document(meta, body)
        committed = parse_document(path, raw.encode('utf-8'))
        self.atomic_write(path, raw, expected=expected, new=expected is None)
        receipt = committed.summary()
        updated = [r for r in records if r.path != path] + [committed]
        try:
            self.atomic_write(self.folder / 'INDEX.md', render_index(updated))
        except (OSError, TrdError) as exc:
            raise TrdError(9, 'partial_commit',
                           'TRD was committed but INDEX.md was not updated. Reindex; do not repeat the document mutation.',
                           mutated=True, index_updated=False, document=receipt,
                           recovery='Run explicit reindex after resolving the index write error.',
                           cause=str(exc)) from None
        return {'status': 'ok', 'mutated': True, 'index_updated': True, 'document': receipt, 'warnings': []}

    def create(self, payload: dict) -> dict:
        require(isinstance(payload, dict) and set(payload) == {'title', 'body'},
                'Create payload must contain exactly title and body.')
        title = text_value(payload['title'], 'title', 160).strip()
        body = normalized_body(payload['body'])
        validate_body(body, allow_legacy_open_questions=False)
        secret_guard(title)
        with self.locked(initialize=True, command='create'):
            records = self._scan()
            created = now(self.timezone)
            day = timestamp(created).date()
            base = slugify(title)
            slug, suffix = base, 1
            path = self.folder / f'trd_{slug}_{day.isoformat()}.md'
            while path.exists() or path.is_symlink():
                suffix += 1
                tag = f'-{suffix}'
                slug = base[:60-len(tag)].rstrip('-') + tag
                path = self.folder / f'trd_{slug}_{day.isoformat()}.md'
            existing_ids = {r.meta['trd_id'] for r in records}
            identifier = ''
            while not identifier or identifier in existing_ids:
                identifier = f'TRD-{day:%Y%m%d}-{uuid.uuid4().hex[:8].upper()}'
            meta = dict(schema_version=SCHEMA_VERSION, trd_id=identifier, title=title, slug=slug,
                        created_at=created, updated_at=created, status='draft', revision=1,
                        last_action_id=ACTIONS['create'],
                        status_reason='Created as a draft from an explicit user request.')
            result = self._commit(meta, body, path, records)
        result['warnings'].extend(self.cleanup_warnings)
        return result

    def update(self, selector: str, expected: str, payload: dict) -> dict:
        require(isinstance(payload, dict) and bool(payload) and set(payload) <= {'title', 'body'},
                'Update payload accepts title and/or body only.')
        if 'title' in payload:
            text_value(payload['title'], 'title', 160)
            secret_guard(payload['title'])
        if 'body' in payload:
            secret_guard(normalized_body(payload['body']))
        with self.locked(command='update'):
            records = self._scan()
            record = self.resolve(selector, records)
            self._expect(record, expected)
            require(record.meta['schema_version'] == SCHEMA_VERSION,
                    'Legacy schema 1 requires explicit migration before update.', 8, 'migration_required')
            require(record.meta['status'] != 'retired',
                    'Retired TRD is read-only; explicitly restore before editing.', 8, 'lifecycle')
            title = payload.get('title', record.meta['title'])
            body = normalized_body(payload.get('body', record.body))
            validate_body(body, allow_legacy_open_questions=False)
            changed_scope = scope_signature(title, body) != scope_signature(record.meta['title'], record.body)
            if not changed_scope:
                result = {'status': 'no_op', 'mutated': False, 'document': record.summary(),
                          'warnings': self._index_warnings(records)}
            else:
                meta = dict(record.meta)
                if meta['status'] == 'trd_done':
                    meta['status'] = 'draft'
                    meta['status_reason'] = 'Document content or title revised; the requirements baseline needs renewed review.'
                meta.update(title=title, updated_at=now(self.timezone, meta['updated_at']),
                            revision=meta['revision']+1, last_action_id=ACTIONS['update'])
                result = self._commit(meta, body, record.path, records, expected)
                result['scope_changed'] = changed_scope
        result['warnings'].extend(self.cleanup_warnings)
        return result

    def set_status(self, selector: str, expected: str, status: str, reason: str, confirmed: bool) -> dict:
        require(status in STATUSES, 'Unknown target status.')
        text_value(reason, 'reason', 1024)
        secret_guard(reason)
        require(confirmed is True, 'Explicit user confirmation must be attested with --confirmed.', 8, 'lifecycle')
        with self.locked(command='set-status'):
            records = self._scan()
            record = self.resolve(selector, records)
            self._expect(record, expected)
            require(record.meta['schema_version'] == SCHEMA_VERSION,
                    'Legacy schema 1 requires explicit migration before a status change.', 8, 'migration_required')
            before = record.meta['status']
            if status == before:
                result = {'status': 'no_op', 'mutated': False, 'document': record.summary(),
                          'warnings': self._index_warnings(records)}
            else:
                require(status in TRANSITIONS[before], f'Transition {before} -> {status} is prohibited.', 8, 'lifecycle')
                gate(status, record.sections, record.requirements)
                if status == 'retired':
                    action = ACTIONS['retire']
                elif before == 'retired':
                    action = ACTIONS['reopen']
                else:
                    action = ACTIONS[{'trd_done': 'approve', 'draft': 'draft'}[status]]
                meta = dict(record.meta, status=status, status_reason=reason.strip(),
                            updated_at=now(self.timezone, record.meta['updated_at']),
                            revision=record.meta['revision']+1, last_action_id=action)
                result = self._commit(meta, record.body, record.path, records, expected)
        result['warnings'].extend(self.cleanup_warnings)
        return result

    def preflight(self, selector: str, expected: str | None = None) -> dict:
        records, warnings = self.read()
        record = self.resolve(selector, records)
        if expected is not None:
            self._expect(record, expected)
        return dict(status='ok', mutated=False, document=record.summary(),
                    preflight=migration_preflight(record), warnings=warnings)

    def migrate(self, selector: str, expected: str, reason: str, confirmed: bool) -> dict:
        text_value(reason, 'reason', 1024)
        secret_guard(reason)
        require(confirmed is True, 'Explicit migration confirmation must be attested with --confirmed.', 8, 'lifecycle')
        with self.locked(command='migrate'):
            records = self._scan()
            record = self.resolve(selector, records)
            self._expect(record, expected)
            check = migration_preflight(record)
            if check['already_current']:
                result = dict(status='no_op', mutated=False, document=record.summary(),
                              preflight=check, warnings=self._index_warnings(records))
            else:
                if check['blockers']:
                    raise TrdError(8, 'migration_blocked', 'Legacy content prevents lossless migration.',
                                   document=record.summary(), blockers=check['blockers'])
                meta = dict(record.meta, schema_version=SCHEMA_VERSION,
                            status=LEGACY_STATE_MAPPING[record.meta['status']],
                            status_reason=reason.strip(), last_action_id=ACTIONS['migrate'],
                            revision=record.meta['revision']+1,
                            updated_at=now(self.timezone, record.meta['updated_at']))
                before = record.summary()
                try:
                    result = self._commit(meta, migrated_body(record), record.path, records, expected)
                except TrdError as exc:
                    if exc.details.get('mutated'):
                        exc.details['migration_from'] = before
                    raise
                result['migration_from'] = before
        result['warnings'].extend(self.cleanup_warnings)
        return result

    def reindex(self) -> dict:
        with self.locked(initialize=True, command='reindex'):
            records = self._scan()
            index = self.folder / 'INDEX.md'
            self._check_file(index)
            rendered = render_index(records)
            unchanged = index.exists() and index.read_bytes() == rendered.encode('utf-8')
            if not unchanged:
                self.atomic_write(index, rendered)
            result = {'status': 'no_op' if unchanged else 'ok', 'mutated': not unchanged,
                      'index_updated': True, 'document_count': len(records), 'warnings': []}
        result['warnings'].extend(self.cleanup_warnings)
        return result


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise TrdError(2, 'invalid', message)


def make_parser() -> argparse.ArgumentParser:
    parser = Parser(description=__doc__)
    parser.add_argument('--project-root', required=True, help='Explicit existing project root, not an inferred working directory.')
    parser.add_argument('--timezone', help='Optional IANA timezone for recorded local timestamps; default is host local time.')
    sub = parser.add_subparsers(dest='command', required=True, parser_class=Parser)
    command = sub.add_parser('create', help='Create a draft and regenerate the index.')
    command.add_argument('--input', required=True, help='JSON file, or - for stdin.')
    command = sub.add_parser('update', help='Revise draft or trd_done content; material changes return the document to draft.')
    command.add_argument('selector')
    command.add_argument('--expect-sha256', required=True)
    command.add_argument('--input', required=True)
    command = sub.add_parser('set-status', help='Explicit lifecycle transition; does not execute the requirements.')
    command.add_argument('selector')
    command.add_argument('--expect-sha256', required=True)
    command.add_argument('--status', choices=STATUSES, required=True)
    command.add_argument('--reason', required=True)
    command.add_argument('--confirmed', action='store_true')
    command = sub.add_parser('migrate', help='Explicitly convert one legacy schema-1 TRD to the document-only schema; no execution authority is granted.')
    command.add_argument('selector')
    command.add_argument('--expect-sha256')
    command.add_argument('--reason')
    command.add_argument('--confirmed', action='store_true')
    command.add_argument('--check', action='store_true', help='Read-only preflight; report blockers and change no files.')
    command = sub.add_parser('list', help='Read-only catalog listing.')
    command.add_argument('--status', choices=STATUSES)
    command = sub.add_parser('show', help='Read one exact document, including body and content hash.')
    command.add_argument('selector')
    sub.add_parser('validate', help='Read-only full catalog validation; reports projection drift.')
    sub.add_parser('reindex', help='Explicitly create/rebuild INDEX.md; never alter TRD meaning.')
    return parser


def main(argv: list[str] | None = None) -> int:
    command = None
    try:
        args = make_parser().parse_args(argv)
        command = args.command
        store = Store(args.project_root, args.timezone)
        if command == 'create':
            result = store.create(load_payload(args.input))
        elif command == 'update':
            result = store.update(args.selector, args.expect_sha256, load_payload(args.input))
        elif command == 'set-status':
            result = store.set_status(args.selector, args.expect_sha256, args.status, args.reason, args.confirmed)
        elif command == 'migrate':
            if args.check:
                require(args.reason is None and not args.confirmed,
                        '--check is read-only; do not combine it with --reason or --confirmed.')
                result = store.preflight(args.selector, args.expect_sha256)
            else:
                require(args.expect_sha256 is not None and args.reason is not None,
                        'Migration requires --expect-sha256 and --reason; use --check for read-only preflight.')
                result = store.migrate(args.selector, args.expect_sha256, args.reason, args.confirmed)
        elif command == 'reindex':
            result = store.reindex()
        else:
            records, warnings = store.read()
            result = {'status': 'ok', 'mutated': False, 'warnings': warnings}
            if command == 'show':
                record = store.resolve(args.selector, records)
                result.update(document=record.summary(), body=record.body)
            else:
                selected = [r for r in records if not getattr(args, 'status', None) or
                            (r.meta['schema_version'] == SCHEMA_VERSION and r.meta['status'] == args.status)]
                result.update(document_count=len(records),
                              **catalog_counts(records),
                              documents=[r.summary() for r in sorted_records(selected)])
                if command == 'validate':
                    result.update(canonical_valid=True, index_current=not warnings,
                                  validation_scope='Document structure, document approval prerequisites, legacy compatibility, and index consistency. Document approval grants no implementation or external authority.')
        print(json.dumps(dict(schema_version=SCHEMA_VERSION, command=command,
                              project_root=str(store.root), **result), ensure_ascii=False, indent=2))
        return 0
    except TrdError as exc:
        result = dict(schema_version=SCHEMA_VERSION, command=command, status='error',
                      mutated=False, error={'category': exc.category, 'message': str(exc)})
        result.update(exc.details)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return exc.code
    except (OSError, UnicodeError) as exc:
        print(json.dumps(dict(schema_version=SCHEMA_VERSION, command=command, status='error',
                              mutated=False, error={'category': 'io', 'message': str(exc)}), indent=2))
        return 9



# Optional action guard adapter.  Standalone/core use imports no ontology runtime.
def _ontology_checkpoint(*, targets=True):
    import sys as _sys
    _module = _sys.modules.get("ontology_guards")
    if _module is not None:
        _module.checkpoint(targets=targets)


def _ontology_guard_adapter(function, family, root_argument, target_paths):
    import functools as _functools
    import inspect as _inspect
    @_functools.wraps(function)
    def guarded(*args, **kwargs):
        import importlib.util as _util
        import sys as _sys
        from pathlib import Path as _Path
        arguments = dict(_inspect.signature(function).bind(*args, **kwargs).arguments)
        if root_argument == "@depot":
            selected_root = installed_locations()[0]
        else:
            selected_root = arguments[root_argument]
            if not isinstance(selected_root, (_Path, str)):
                selected_root = getattr(selected_root, "project_root", getattr(selected_root, "root", selected_root))
        selected_root = _Path(selected_root).absolute()
        config_path = selected_root / "ontology-advanced.yaml"
        if not config_path.exists() and not config_path.is_symlink():
            return function(*args, **kwargs)
        if family == "template" and arguments.get("command") == "check":
            return function(*args, **kwargs)
        import json as _json
        import hashlib as _hashlib
        def unique_pairs(pairs):
            value = {}
            for key, item in pairs:
                if key in value:
                    raise ValueError("duplicate guard configuration key")
                value[key] = item
            return value
        try:
            if config_path.is_symlink():
                raise ValueError("symbolic guard configuration")
            config = _json.loads(config_path.read_text(), object_pairs_hook=unique_pairs)
            selected = config.get("profiles", {}).get("guards", {"enabled": False})
            if config.get("schema_version") != 1 or not isinstance(selected, dict) or type(selected.get("enabled")) is not bool:
                raise ValueError("unsupported guard configuration")
        except (OSError, ValueError, AttributeError) as exc:
            raise _ontology_adapter_error("guard_schema", "Guard configuration is unreadable or unsupported.", {}) from exc
        if not selected["enabled"]:
            if set(selected) != {"enabled"}:
                raise _ontology_adapter_error("guard_schema", "Disabled guard configuration has unsupported fields.", {})
            return function(*args, **kwargs)
        script = selected_root / ".agents/skills/ontology/scripts/ontology_guards.py"
        if not script.is_file() or any(parent.is_symlink() for parent in (script, *script.parents)):
            raise _ontology_adapter_error("guard_unavailable", "Enabled guards require their current project-local installed adapter.", {})
        current_sha256 = _hashlib.sha256(script.read_bytes()).hexdigest()
        module = _sys.modules.get("ontology_guards")
        if module is not None and (_Path(module.__file__).resolve() != script.resolve()
                or getattr(module, "ENGINE_SOURCE_SHA256", None) != current_sha256):
            raise _ontology_adapter_error("guard_stale", "Loaded guard code differs from this selected project's current installed bytes; use a fresh owning-helper process after reviewed repair.", {})
        if module is None:
            spec = _util.spec_from_file_location("ontology_guards", script)
            module = _util.module_from_spec(spec)
            _sys.modules["ontology_guards"] = module
            _sys.path.insert(0, str(script.parent))
            spec.loader.exec_module(module)
        targets = list(target_paths)
        if family == "setup":
            destination = _Path(arguments["destination"]).absolute()
            try:
                relative = destination.relative_to(selected_root).as_posix()
            except ValueError:
                raise _ontology_adapter_error("guard_scope", "Setup target escapes the selected depot.", {})
            targets.extend([relative + "/control_records/project-setup.json", relative + "/AGENTS.md", relative + "/ROLE.md"])
        try:
            return module.dispatch(lambda: function(*args, **kwargs), family, function.__name__, selected_root, arguments, targets)
        except module.GuardError as exc:
            raise _ontology_adapter_error(exc.code, str(exc), exc.details) from exc
    return guarded


def _ontology_adapter_error(code, message, details):
    return TrdError(2, code, message, **details)

ONTOLOGY_GUARDED_ACTIONS = ['Store.create', 'Store.update', 'Store.set_status', 'Store.migrate', 'Store.reindex']
Store.create = _ontology_guard_adapter(Store.create, 'trd', 'self', ['TRDs'])
Store.update = _ontology_guard_adapter(Store.update, 'trd', 'self', ['TRDs'])
Store.set_status = _ontology_guard_adapter(Store.set_status, 'trd', 'self', ['TRDs'])
Store.migrate = _ontology_guard_adapter(Store.migrate, 'trd', 'self', ['TRDs'])
Store.reindex = _ontology_guard_adapter(Store.reindex, 'trd', 'self', ['TRDs'])

if __name__ == '__main__':
    raise SystemExit(main())
