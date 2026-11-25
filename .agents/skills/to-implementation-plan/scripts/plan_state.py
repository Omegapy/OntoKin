#!/usr/bin/env python3
"""Create, inspect, validate, and safely mutate tracked implementation plans.

This helper intentionally uses only the Python standard library.  ``plan.json``
is canonical; every Markdown file written by this program is a deterministic
projection of canonical state.
"""

from __future__ import annotations

import argparse
import copy
import dataclasses
import datetime as dt
import errno
import hashlib
import json
import math
import os
import re
import socket
import stat
import sys
import unicodedata
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence


SCHEMA_VERSION = 1
RESULT_SCHEMA_VERSION = 1
MAX_JSON_BYTES = 8 * 1024 * 1024
MAX_STRING_CHARS = 64 * 1024
MAX_INTEGER_DIGITS = 64
MAX_SHORT_TEXT = 8192
MAX_LOCATOR_CHARS = 8192
MAX_TITLE_CHARS = 256
MAX_ID_CHARS = 64
MAX_SLUG_CHARS = 64
MAX_COLLECTION_ITEMS = 10_000
MAX_NESTING_DEPTH = 32

PLAN_STATES = {
    "draft",
    "ready",
    "in_progress",
    "paused",
    "blocked",
    "completed",
    "retired",
    "cancelled",
}
TASK_STATES = {
    "planned",
    "in_progress",
    "paused",
    "blocked",
    "completed",
    "skipped",
}
PHASE_STATES = {"planned", "in_progress", "paused", "blocked", "completed"}
REQUIREMENT_STATES = {"active", "satisfied", "dispositioned"}
DECISION_STATES = {"proposed", "approved", "rejected"}
QUESTION_STATES = {"open", "answered", "withdrawn"}
ASSUMPTION_STATES = {"unconfirmed", "accepted", "rejected"}
SOURCE_KINDS = {"prompt", "text", "file", "trd", "prd", "url", "other"}
PROVENANCE_MODES = {"user_supplied", "agent_inspected"}
INSPECTION_METHODS = {
    "direct_text",
    "pdf_tool",
    "document_tool",
    "spreadsheet_tool",
    "presentation_tool",
    "other_format_tool",
    "browser_tool",
}
LOCAL_INSPECTION_METHODS = INSPECTION_METHODS - {"browser_tool"}
EVIDENCE_TYPES = {
    "planned_check",
    "inspection",
    "command",
    "test",
    "runtime",
    "user_report",
    "external_report",
    "not_exercised",
}
EVIDENCE_RESULT_STATUSES = {
    "planned",
    "passed",
    "failed",
    "blocked",
    "partial",
    "not_exercised",
}
VERIFICATION_LEVELS = {
    "planned",
    "inspected_only",
    "static_checks_passed",
    "targeted_tests_passed",
    "broader_suite_passed",
    "runtime_observed",
    "end_to_end_verified",
    "not_exercised",
}
OBSERVATION_SOURCES = {"agent", "user", "tool", "external", "plan"}
DISPOSITION_KINDS = {
    "out_of_scope",
    "duplicate",
    "superseded",
    "not_required",
    "other",
}
VALIDATION_STATUSES = {"pass", "fail", "unresolved", "not_exercised"}
FINDING_STATUSES = {"open", "resolved", "accepted"}
FINDING_SEVERITIES = {"error", "warning", "info"}

MEANINGLESS_EVIDENCE_MARKERS = {
    "complete",
    "completed",
    "done",
    "evidence",
    "n a",
    "na",
    "none",
    "ok",
    "pass",
    "passed",
    "pending",
    "planned",
    "success",
    "successful",
    "tbd",
    "todo",
    "unknown",
}
READINESS_PLACEHOLDER_MARKERS = {
    "fill in",
    "fill me",
    "fill this",
    "n a",
    "na",
    "nil",
    "none",
    "not available",
    "not decided",
    "not applicable",
    "not known",
    "not provided",
    "not specified",
    "placeholder",
    "pending",
    "tba",
    "tbc",
    "tbd",
    "to be announced",
    "to be confirmed",
    "to be decided",
    "to do",
    "to be determined",
    "todo",
    "undetermined",
    "unknown",
    "unspecified",
}

PLAN_TRANSITIONS = {
    "draft": {"ready", "retired", "cancelled"},
    "ready": {"draft", "in_progress", "retired", "cancelled"},
    "in_progress": {"paused", "blocked", "completed", "cancelled", "draft"},
    "paused": {"in_progress", "cancelled", "draft"},
    "blocked": {"in_progress", "cancelled", "draft"},
    "completed": {"in_progress", "retired"},
    "retired": {"draft"},
    "cancelled": {"draft"},
}
TASK_TRANSITIONS = {
    "planned": {"in_progress", "blocked", "skipped"},
    "in_progress": {"paused", "blocked", "completed"},
    "paused": {"in_progress", "blocked", "skipped"},
    "blocked": {"in_progress", "paused", "skipped"},
    "completed": {"in_progress"},
    "skipped": {"planned"},
}

PLAN_ID_RE = re.compile(r"^PLAN-(\d{8})-([A-F0-9]{8})$")
DIRECTORY_RE = re.compile(
    r"^Plan_([a-z0-9]+(?:-[a-z0-9]+)*)_(\d{4}-\d{2}-\d{2})_([A-F0-9]{8})$"
)
PHASE_ID_RE = re.compile(r"^PHASE-(\d{3,})$")
TASK_ID_RE = re.compile(r"^TASK-(\d{3,})$")
SOURCE_ID_RE = re.compile(r"^SRC-(\d{3,})$")
REQUIREMENT_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)*$")
DECISION_ID_RE = re.compile(r"^DEC-(\d{3,})$")
QUESTION_ID_RE = re.compile(r"^Q-(\d{3,})$")
ASSUMPTION_ID_RE = re.compile(r"^ASM-(\d{3,})$")
EVIDENCE_ID_RE = re.compile(r"^EVID-(\d{3,})$")
ACTION_ID_RE = re.compile(r"^TO-IP-(?:001|004|005|006|007|008)$")
RESERVED_ACTION_NAMESPACE_RE = re.compile(r"^TO-IP-\d{3,}$")
FINDING_ID_RE = re.compile(r"^FIND-(\d{3,})$")
SAFE_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SAFE_PARALLEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
GENERATED_PHASE_FILE_RE = re.compile(
    r"^PHASE-\d{3,}_[a-z0-9]+(?:-[a-z0-9]+)*\.md$"
)
TEMP_FILE_RE = re.compile(
    r"^\.(?:plan\.json|PLAN\.md|TRACEABILITY\.md|INDEX\.md|PHASE-\d{3,}_[a-z0-9-]+\.md)\.tmp-[A-F0-9]{32}$"
)
GENERATED_PROJECTION_MARKER = (
    b"<!-- Generated by to-implementation-plan. plan.json is canonical. -->\n"
)

TOP_LEVEL_FIELDS = {
    "schema_version",
    "plan_id",
    "title",
    "slug",
    "created_at",
    "updated_at",
    "status",
    "revision",
    "status_reason",
    "project",
    "objective",
    "scope",
    "sources",
    "requirements",
    "decisions",
    "open_questions",
    "assumptions",
    "phases",
    "tasks",
    "coverage",
    "validation",
    "initial_record_ids",
    "history",
}

EXIT_CODES = {
    "invalid_input": 2,
    "not_found": 3,
    "ambiguous_selector": 4,
    "unsafe_or_corrupt": 5,
    "stale_state": 6,
    "active_lock": 7,
    "prohibited_transition": 8,
    "unmet_gate": 9,
    "io_error": 10,
    "partial_projection": 11,
}
LOCK_COMMANDS = {
    "create",
    "update",
    "update-phase",
    "update-task",
    "record-evidence",
    "set-status",
    "rebuild-projections",
    "reindex",
    "reconcile",
}

SECRET_PATTERNS = (
    re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(
        r"(?i)\b(?:password|passwd|api[_ -]?key|access[_ -]?token|secret)\s*[:=]\s*['\"]?[^\s'\"]{8,}"
    ),
    re.compile(r"(?i)\bauthorization\s*:\s*bearer\s+\S{8,}"),
)
HIDDEN_REASONING_PATTERNS = (
    re.compile(r"(?is)<(?:analysis|thinking)>.*?</(?:analysis|thinking)>"),
    re.compile(r"(?i)\b(?:store|save|record|include)\s+(?:the\s+)?(?:hidden\s+reasoning|chain[- ]of[- ]thought)\b"),
)


class AppError(Exception):
    """Expected, categorized command failure."""

    def __init__(
        self,
        category: str,
        message: str,
        *,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        if category not in EXIT_CODES:
            raise ValueError(f"unknown error category: {category}")
        self.category = category
        self.message = message
        self.details = dict(details or {})
        self.exit_code = EXIT_CODES[category]


class DuplicateKeyError(ValueError):
    pass


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        # argparse reflects untrusted choices and unknown option values in its
        # message.  Keep the public diagnostic non-reflective so a credential
        # passed in argv cannot be echoed to stdout.
        raise AppError("invalid_input", "Invalid command arguments.")


@dataclasses.dataclass(frozen=True)
class Context:
    project_root: Path
    plans_root: Path
    project_root_identity: tuple[int, int]


@dataclasses.dataclass
class LockHandle:
    path: Path
    token: str
    owner: dict[str, Any]
    parent_identity: tuple[int, int]
    lock_identity: tuple[int, int]
    owner_sha256: str


@dataclasses.dataclass
class BoundCreatedDirectory:
    parent_fd: int
    child_fd: int
    parent_identity: tuple[int, int]
    child_identity: tuple[int, int]
    parent_path: Path
    child_name: str

    def close(self) -> None:
        os.close(self.child_fd)
        os.close(self.parent_fd)


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def timestamp(value: dt.datetime | None = None) -> str:
    current = (value or utc_now()).astimezone(dt.timezone.utc)
    return current.isoformat(timespec="microseconds").replace("+00:00", "Z")


def parse_timestamp(value: Any, field: str) -> dt.datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a nonblank offset-aware timestamp")
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} is not an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include a UTC offset")
    return parsed


def next_timestamp(previous: str) -> str:
    old = parse_timestamp(previous, "updated_at")
    current = utc_now()
    if current <= old:
        current = old + dt.timedelta(microseconds=1)
    return timestamp(current)


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            separators=(",", ": "),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    absolute = path if path.is_absolute() else Path(os.path.abspath(path))
    descriptor, _ = open_regular_file_without_symlinks(
        absolute, label="file to hash"
    )
    try:
        while True:
            block = os.read(descriptor, 1024 * 1024)
            if not block:
                break
            digest.update(block)
    finally:
        os.close(descriptor)
    return digest.hexdigest()


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            # Object keys are untrusted input and may themselves contain a
            # credential.  Never echo the duplicate key in a diagnostic.
            raise DuplicateKeyError("duplicate JSON object key")
        result[key] = value
    return result


def _safe_object_path(path: str, key: str) -> str:
    """Return a useful JSON path without reflecting secret-bearing keys."""
    if any(pattern.search(key) for pattern in (*SECRET_PATTERNS, *HIDDEN_REASONING_PATTERNS)):
        return f"{path}.<redacted-key>"
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]{0,63}", key):
        return f"{path}.{key}"
    return f"{path}.<object-key>"


def _validate_value_bounds(value: Any, path: str = "$", depth: int = 0) -> None:
    if depth > MAX_NESTING_DEPTH:
        raise AppError(
            "invalid_input",
            "JSON nesting exceeds the supported depth.",
            details={"path": path, "maximum_depth": MAX_NESTING_DEPTH},
        )
    if isinstance(value, str):
        if len(value) > MAX_STRING_CHARS:
            raise AppError(
                "invalid_input",
                "A JSON string exceeds the supported size.",
                details={"path": path, "maximum_characters": MAX_STRING_CHARS},
            )
        if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
            raise AppError(
                "invalid_input",
                "A JSON string contains an unsupported surrogate code point.",
                details={"path": path},
            )
        return
    if isinstance(value, float) and not math.isfinite(value):
        raise AppError(
            "invalid_input",
            "JSON contains a non-finite number.",
            details={"path": path},
        )
    if isinstance(value, list):
        if len(value) > MAX_COLLECTION_ITEMS:
            raise AppError(
                "invalid_input",
                "A JSON collection exceeds the supported item count.",
                details={"path": path, "maximum_items": MAX_COLLECTION_ITEMS},
            )
        for index, item in enumerate(value):
            _validate_value_bounds(item, f"{path}[{index}]", depth + 1)
        return
    if isinstance(value, dict):
        if len(value) > MAX_COLLECTION_ITEMS:
            raise AppError(
                "invalid_input",
                "A JSON object exceeds the supported member count.",
                details={"path": path, "maximum_items": MAX_COLLECTION_ITEMS},
            )
        for key, item in value.items():
            if not isinstance(key, str):
                raise AppError("invalid_input", "JSON object keys must be strings.")
            _validate_value_bounds(key, f"{path}.<object-key>", depth + 1)
            _validate_value_bounds(item, _safe_object_path(path, key), depth + 1)


def decode_json_bytes(data: bytes, source_label: str) -> Any:
    if len(data) > MAX_JSON_BYTES:
        raise AppError(
            "invalid_input",
            "JSON input exceeds the supported size.",
            details={"maximum_bytes": MAX_JSON_BYTES},
        )
    if data.startswith(b"\xef\xbb\xbf"):
        raise AppError("invalid_input", "JSON must use UTF-8 without a byte-order mark.")
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise AppError("invalid_input", "JSON input is not valid UTF-8.") from exc
    try:
        def parse_bounded_int(token: str) -> int:
            digits = token[1:] if token.startswith("-") else token
            if len(digits) > MAX_INTEGER_DIGITS:
                raise ValueError("integer literal exceeds the supported size")
            return int(token, 10)

        value = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_int=parse_bounded_int,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError(f"non-finite JSON number: {token}")
            ),
        )
    except DuplicateKeyError as exc:
        raise AppError("unsafe_or_corrupt", str(exc)) from exc
    except json.JSONDecodeError as exc:
        raise AppError(
            "invalid_input",
            "JSON input is malformed.",
            details={"line": exc.lineno, "column": exc.colno},
        ) from exc
    except ValueError as exc:
        raise AppError(
            "invalid_input", "JSON contains an unsupported numeric value."
        ) from exc
    except (RecursionError, MemoryError) as exc:
        raise AppError(
            "invalid_input",
            "JSON input exceeds safe parser complexity limits.",
        ) from exc
    _validate_value_bounds(value)
    return value


def read_bounded_regular_file(path: Path, *, label: str) -> bytes:
    absolute = path if path.is_absolute() else Path(os.path.abspath(path))
    return read_local_file_without_symlinks(absolute, label=label)


def read_input(specifier: str) -> dict[str, Any]:
    if specifier == "-":
        data = sys.stdin.buffer.read(MAX_JSON_BYTES + 1)
        value = decode_json_bytes(data, "standard input")
    else:
        if "\x00" in specifier:
            raise AppError("invalid_input", "Input path contains an invalid character.")
        value = decode_json_bytes(
            read_bounded_regular_file(Path(specifier), label="input file"),
            "input file",
        )
    if not isinstance(value, dict):
        raise AppError("invalid_input", "Command input must be one JSON object.")
    return value


def _walk_strings(value: Any, path: str = "$") -> Iterator[tuple[str, str]]:
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk_strings(item, f"{path}[{index}]")
    elif isinstance(value, dict):
        for key, item in value.items():
            # Scan keys as data, but use a non-reflective location in case the
            # key itself is the prohibited value.
            yield f"{path}.<object-key>", key
            yield from _walk_strings(item, _safe_object_path(path, key))


def guard_prohibited_content(value: Any) -> None:
    for path, text in _walk_strings(value):
        if any(pattern.search(text) for pattern in SECRET_PATTERNS):
            raise AppError(
                "unsafe_or_corrupt",
                "Input contains a prohibited credential or secret pattern.",
                details={"path": path},
            )
        if any(pattern.search(text) for pattern in HIDDEN_REASONING_PATTERNS):
            raise AppError(
                "unsafe_or_corrupt",
                "Input requests or contains prohibited hidden-reasoning content.",
                details={"path": path},
            )


def safe_slug(text: str, fallback: str = "plan") -> str:
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")
    slug = re.sub(r"-+", "-", slug)[:MAX_SLUG_CHARS].strip("-")
    return slug or fallback


def ensure_confined(root: Path, candidate: Path, label: str) -> None:
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise AppError("unsafe_or_corrupt", f"{label} escapes the project root.") from exc


def ensure_no_symlink_components(root: Path, candidate: Path, label: str) -> None:
    ensure_confined(root, candidate, label)
    current = root
    for part in candidate.relative_to(root).parts:
        current = current / part
        try:
            info = current.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise AppError("io_error", f"Cannot inspect {label}.") from exc
        if stat.S_ISLNK(info.st_mode):
            raise AppError("unsafe_or_corrupt", f"{label} traverses a symlink.")


def filesystem_is_case_insensitive(root: Path) -> bool:
    """Probe the existing root name without creating a filesystem artifact."""
    variant_name = "".join(
        character.swapcase() if character.isalpha() else character
        for character in root.name
    )
    if not variant_name or variant_name == root.name:
        return False
    try:
        return os.path.samefile(root, root.with_name(variant_name))
    except OSError:
        return False


def normalized_artifact_key(
    value: Any, *, project_root: Path, case_insensitive: bool
) -> str:
    """Normalize a target locator so equivalent write scopes collide."""
    text = str(value).strip()
    prefix = "path:"
    for candidate in ("file:", "path:", "output:", "observation:"):
        if text.casefold().startswith(candidate):
            prefix = "observation:" if candidate == "observation:" else "path:"
            text = text[len(candidate) :].strip()
            break
    if prefix == "path:":
        artifact_path = Path(text)
        normalized = os.path.normpath(
            str(
                artifact_path
                if artifact_path.is_absolute()
                else project_root / artifact_path
            )
        )
    else:
        normalized = " ".join(text.split())
    key = f"{prefix}{normalized}"
    return key.casefold() if case_insensitive else key


def artifact_scopes_overlap(left: str, right: str) -> bool:
    """Conservatively detect equal, ancestor, descendant, or glob write scopes."""
    if left == right:
        return True
    if not left.startswith("path:") or not right.startswith("path:"):
        return False
    left_path = left.removeprefix("path:")
    right_path = right.removeprefix("path:")
    if any(character in left_path + right_path for character in "*?["):
        return True
    separator = os.sep
    return left_path.startswith(right_path.rstrip(separator) + separator) or right_path.startswith(
        left_path.rstrip(separator) + separator
    )


def graph_reaches(
    start: str, target: str, edges: Mapping[str, Sequence[str]]
) -> bool:
    pending = list(edges.get(start, []))
    visited: set[str] = set()
    while pending:
        current = pending.pop()
        if current == target:
            return True
        if current in visited:
            continue
        visited.add(current)
        pending.extend(edges.get(current, []))
    return False


def resolve_context(project_root_arg: str, plans_root_arg: str) -> Context:
    raw_project = Path(project_root_arg)
    if not raw_project.is_absolute():
        raise AppError("invalid_input", "--project-root must be an absolute path.")
    try:
        project_root = raw_project.resolve(strict=True)
    except (FileNotFoundError, OSError) as exc:
        raise AppError("not_found", "The project root does not exist.") from exc
    if not project_root.is_dir():
        raise AppError("invalid_input", "The project root must be a directory.")

    if not plans_root_arg or "\x00" in plans_root_arg:
        raise AppError("invalid_input", "--plans-root is invalid.")
    raw_plans = Path(plans_root_arg)
    raw_parts = raw_plans.parts[1:] if raw_plans.is_absolute() else raw_plans.parts
    if any(part in {"", ".", ".."} for part in raw_parts):
        raise AppError(
            "unsafe_or_corrupt",
            "--plans-root contains a hidden or traversal path component.",
        )
    candidate = raw_plans if raw_plans.is_absolute() else project_root / raw_plans
    candidate = Path(os.path.abspath(candidate))
    ensure_confined(project_root, candidate, "plans root")
    relative_parts = candidate.relative_to(project_root).parts
    if any(part.startswith(".") for part in relative_parts):
        raise AppError(
            "unsafe_or_corrupt",
            "--plans-root contains a hidden path component.",
        )
    ensure_no_symlink_components(project_root, candidate, "plans root")
    try:
        candidate_info = candidate.lstat()
    except FileNotFoundError:
        candidate_info = None
    except OSError as exc:
        raise AppError("io_error", "Cannot inspect --plans-root.") from exc
    if candidate_info is not None:
        info = candidate_info
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            raise AppError(
                "unsafe_or_corrupt",
                "The plans root must be a non-symlink directory.",
            )
    else:
        parent = candidate.parent
        if not parent.exists() or not parent.is_dir():
            raise AppError(
                "not_found",
                "The parent directory for --plans-root does not exist.",
            )
        ensure_no_symlink_components(project_root, parent, "plans-root parent")
    project_info = project_root.stat()
    return Context(
        project_root=project_root,
        plans_root=candidate,
        project_root_identity=(project_info.st_dev, project_info.st_ino),
    )


def fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_write_bytes(
    path: Path,
    data: bytes,
    *,
    expected_parent_identity: tuple[int, int] | None = None,
    required_existing_prefix: bytes | None = None,
) -> bool:
    """Write bytes by same-directory replace; return False for an exact no-op."""
    absolute = path if path.is_absolute() else Path(os.path.abspath(path))
    parent_fd = open_directory_without_symlinks(
        absolute.parent, label="managed-file parent"
    )
    parent_info = os.fstat(parent_fd)
    bound_identity = (parent_info.st_dev, parent_info.st_ino)
    if expected_parent_identity is not None and bound_identity != expected_parent_identity:
        os.close(parent_fd)
        raise AppError(
            "unsafe_or_corrupt",
            "The managed-file parent changed after it was selected; no write occurred.",
        )

    def descriptor_sha256(descriptor_value: int) -> str:
        digest = hashlib.sha256()
        os.lseek(descriptor_value, 0, os.SEEK_SET)
        while True:
            block = os.read(descriptor_value, 1024 * 1024)
            if not block:
                break
            digest.update(block)
        return digest.hexdigest()

    def parent_path_matches() -> bool:
        fresh_fd: int | None = None
        try:
            fresh_fd = open_directory_without_symlinks(
                absolute.parent, label="managed-file parent"
            )
            info = os.fstat(fresh_fd)
        except (AppError, OSError):
            return False
        finally:
            if fresh_fd is not None:
                os.close(fresh_fd)
        return stat.S_ISDIR(info.st_mode) and (
            info.st_dev,
            info.st_ino,
        ) == bound_identity

    existing_fd: int | None = None
    try:
        try:
            entry_info = os.stat(
                absolute.name, dir_fd=parent_fd, follow_symlinks=False
            )
            if stat.S_ISLNK(entry_info.st_mode) or not stat.S_ISREG(
                entry_info.st_mode
            ):
                raise AppError(
                    "unsafe_or_corrupt",
                    "A managed-file destination is not a regular, non-symlink file.",
                )
            existing_fd = os.open(
                absolute.name,
                os.O_RDONLY
                | os.O_NOFOLLOW
                | getattr(os, "O_NONBLOCK", 0)
                | getattr(os, "O_CLOEXEC", 0),
                dir_fd=parent_fd,
            )
        except FileNotFoundError:
            existing_fd = None
        except OSError as exc:
            if exc.errno in {errno.ELOOP, errno.ENOTDIR}:
                raise AppError(
                    "unsafe_or_corrupt",
                    "A managed-file destination is not a regular, non-symlink file.",
                ) from exc
            raise
        if existing_fd is not None:
            existing_info = os.fstat(existing_fd)
            if not stat.S_ISREG(existing_info.st_mode) or (
                existing_info.st_dev,
                existing_info.st_ino,
            ) != (entry_info.st_dev, entry_info.st_ino):
                raise AppError(
                    "unsafe_or_corrupt",
                    "A managed-file destination is not a regular, non-symlink file.",
                )
            if required_existing_prefix is not None:
                os.lseek(existing_fd, 0, os.SEEK_SET)
                if os.read(existing_fd, len(required_existing_prefix)) != required_existing_prefix:
                    raise AppError(
                        "unsafe_or_corrupt",
                        "An existing generated-file destination is unmanaged and will not be overwritten.",
                    )
            if (
                existing_info.st_size == len(data)
                and descriptor_sha256(existing_fd) == sha256_bytes(data)
            ):
                if not parent_path_matches():
                    raise AppError(
                        "unsafe_or_corrupt",
                        "The managed-file parent changed during the no-op comparison; no current-path claim was made.",
                    )
                os.close(parent_fd)
                return False
    except BaseException:
        os.close(parent_fd)
        raise
    finally:
        if existing_fd is not None:
            os.close(existing_fd)

    token = uuid.uuid4().hex.upper()
    temporary_name = f".{absolute.name}.tmp-{token}"
    descriptor: int | None = None
    replacement_completed = False
    try:
        if not parent_path_matches():
            raise AppError(
                "unsafe_or_corrupt",
                "The managed-file parent changed before the write; no mutation occurred.",
            )
        descriptor = os.open(
            temporary_name,
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | os.O_NOFOLLOW
            | getattr(os, "O_CLOEXEC", 0),
            0o600,
            dir_fd=parent_fd,
        )
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            descriptor = None
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if not parent_path_matches():
            os.unlink(temporary_name, dir_fd=parent_fd)
            os.fsync(parent_fd)
            raise AppError(
                "unsafe_or_corrupt",
                "The managed-file parent changed before replacement; no destination mutation occurred.",
            )
        _ontology_checkpoint(targets=False)
        os.replace(
            temporary_name,
            absolute.name,
            src_dir_fd=parent_fd,
            dst_dir_fd=parent_fd,
        )
        replacement_completed = True
        os.fsync(parent_fd)
        if not parent_path_matches():
            raise AppError(
                "io_error",
                "The managed-file parent changed after replacement.",
                details={
                    "temporary_name": temporary_name,
                    "replacement_completed": True,
                },
            )
        return True
    except AppError:
        raise
    except (Exception, KeyboardInterrupt) as exc:
        if descriptor is not None:
            os.close(descriptor)
        if not replacement_completed:
            try:
                try:
                    os.stat(
                        temporary_name,
                        dir_fd=parent_fd,
                        follow_symlinks=False,
                    )
                    temporary_missing = False
                except FileNotFoundError:
                    temporary_missing = True
                replacement_completed = (
                    temporary_missing
                    and stat.S_ISREG(
                        os.stat(
                            absolute.name,
                            dir_fd=parent_fd,
                            follow_symlinks=False,
                        ).st_mode
                    )
                )
                if replacement_completed:
                    current_fd = os.open(
                        absolute.name,
                        os.O_RDONLY | os.O_NOFOLLOW,
                        dir_fd=parent_fd,
                    )
                    try:
                        current_info = os.fstat(current_fd)
                        replacement_completed = (
                            current_info.st_size == len(data)
                            and descriptor_sha256(current_fd) == sha256_bytes(data)
                        )
                    finally:
                        os.close(current_fd)
            except (AppError, OSError):
                replacement_completed = False
        raise AppError(
            "io_error",
            "An atomic managed-file write failed; inspect only the reported transaction residue.",
            details={
                "temporary_name": temporary_name,
                "replacement_completed": replacement_completed,
            },
        ) from exc
    finally:
        os.close(parent_fd)


def _safe_lock_owner(owner: Any) -> dict[str, Any] | None:
    if not isinstance(owner, dict):
        return None
    safe: dict[str, Any] = {}
    if owner.get("schema_version") == 1:
        safe["schema_version"] = 1
    token = owner.get("token")
    if isinstance(token, str) and re.fullmatch(r"[A-F0-9]{32}", token):
        safe["token"] = token
    pid = owner.get("pid")
    if isinstance(pid, int) and not isinstance(pid, bool) and pid > 0:
        safe["pid"] = pid
    host = owner.get("host")
    safe["host"] = socket.gethostname() if host == socket.gethostname() else None
    started_at = owner.get("started_at")
    try:
        parse_timestamp(started_at, "lock started_at")
    except ValueError:
        pass
    else:
        safe["started_at"] = started_at
    command = owner.get("command")
    if command in LOCK_COMMANDS:
        safe["command"] = command
    return safe


def read_lock_owner(lock_path: Path) -> dict[str, Any] | None:
    owner_path = lock_path / "owner.json"
    try:
        info = owner_path.lstat()
    except FileNotFoundError:
        return None
    except OSError:
        return None
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        return None
    try:
        value = decode_json_bytes(
            read_bounded_regular_file(owner_path, label="lock owner"),
            "lock owner",
        )
    except AppError:
        return None
    return _safe_lock_owner(value)


def read_lock_owner_from_fd(
    lock_fd: int,
) -> tuple[dict[str, Any] | None, bytes | None]:
    """Read a bounded lock owner through an already bound lock directory."""
    owner_fd: int | None = None
    try:
        owner_fd = os.open(
            "owner.json",
            os.O_RDONLY
            | os.O_NOFOLLOW
            | getattr(os, "O_NONBLOCK", 0)
            | getattr(os, "O_CLOEXEC", 0),
            dir_fd=lock_fd,
        )
        info = os.fstat(owner_fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_JSON_BYTES:
            return None, None
        chunks: list[bytes] = []
        remaining = MAX_JSON_BYTES + 1
        while remaining:
            block = os.read(owner_fd, min(64 * 1024, remaining))
            if not block:
                break
            chunks.append(block)
            remaining -= len(block)
        raw = b"".join(chunks)
        if len(raw) > MAX_JSON_BYTES:
            return None, None
        return _safe_lock_owner(decode_json_bytes(raw, "lock owner")), raw
    except (AppError, FileNotFoundError, OSError, ValueError):
        return None, None
    finally:
        if owner_fd is not None:
            os.close(owner_fd)


def acquire_lock(lock_path: Path, command: str) -> LockHandle:
    token = uuid.uuid4().hex.upper()
    owner = {
        "schema_version": 1,
        "token": token,
        "pid": os.getpid(),
        "host": socket.gethostname(),
        "started_at": timestamp(),
        "command": command,
    }
    parent_fd = open_directory_without_symlinks(
        lock_path.parent, label="write-lock parent"
    )
    parent_info = os.fstat(parent_fd)
    parent_identity = (parent_info.st_dev, parent_info.st_ino)
    try:
        os.mkdir(lock_path.name, 0o700, dir_fd=parent_fd)
    except FileExistsError as exc:
        os.close(parent_fd)
        raise AppError(
            "active_lock",
            "A required write lock already exists; it was not stolen or removed.",
            details={
                "lock_path": str(lock_path),
                "owner": read_lock_owner(lock_path),
            },
        ) from exc
    except OSError as exc:
        os.close(parent_fd)
        raise AppError("io_error", "Cannot create the required write lock.") from exc
    descriptor: int | None = None
    lock_fd: int | None = None
    owner_bytes = canonical_bytes(owner)
    try:
        lock_fd = os.open(
            lock_path.name,
            os.O_RDONLY
            | os.O_DIRECTORY
            | os.O_NOFOLLOW
            | getattr(os, "O_CLOEXEC", 0),
            dir_fd=parent_fd,
        )
        lock_info = os.fstat(lock_fd)
        descriptor = os.open(
            "owner.json",
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | os.O_NOFOLLOW
            | getattr(os, "O_CLOEXEC", 0),
            0o600,
            dir_fd=lock_fd,
        )
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = None
            handle.write(owner_bytes)
            handle.flush()
            os.fsync(handle.fileno())
        os.fsync(lock_fd)
        os.fsync(parent_fd)
    except (Exception, KeyboardInterrupt) as exc:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass
        released_name = f"{lock_path.name}.released-{token}"
        released_path = lock_path.parent / released_name
        release_renamed = False
        try:
            os.rename(
                lock_path.name,
                released_name,
                src_dir_fd=parent_fd,
                dst_dir_fd=parent_fd,
            )
            release_renamed = True
            os.fsync(parent_fd)
            if lock_fd is None:
                lock_fd = os.open(
                    released_name,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                    dir_fd=parent_fd,
                )
            try:
                os.unlink("owner.json", dir_fd=lock_fd)
            except FileNotFoundError:
                pass
            os.rmdir(released_name, dir_fd=parent_fd)
            os.fsync(parent_fd)
        except (OSError, KeyboardInterrupt):
            pass
        details: dict[str, Any] = {}
        try:
            try:
                os.stat(released_name, dir_fd=parent_fd, follow_symlinks=False)
                released_exists = True
            except FileNotFoundError:
                released_exists = False
            if released_exists:
                owner_sha256 = None
                if lock_fd is not None:
                    _, raw_owner = read_lock_owner_from_fd(lock_fd)
                    if raw_owner is not None:
                        owner_sha256 = sha256_bytes(raw_owner)
                scope = (
                    "catalog"
                    if lock_path.name == ".to-implementation-plan.catalog.lock"
                    else "plan"
                )
                selector = "catalog" if scope == "catalog" else lock_path.parent.name
                recovery_input: dict[str, Any] = {
                    "action": "remove_released_lock",
                    "scope": scope,
                    "relative_name": released_path.name,
                    "token": token,
                }
                if owner_sha256 is not None:
                    recovery_input["owner_sha256"] = owner_sha256
                details = {
                    "lock_initialization_cleanup_incomplete": True,
                    "lock_path": str(lock_path),
                    "token": token,
                    "release_renamed": release_renamed,
                    "released_lock_path": str(released_path),
                    "released_lock_name": released_path.name,
                    "recovery_required": {
                        "command": "reconcile",
                        "selector": selector,
                        "input": recovery_input,
                        "then": "validate",
                    },
                }
            else:
                try:
                    os.stat(
                        lock_path.name, dir_fd=parent_fd, follow_symlinks=False
                    )
                    original_exists = True
                except FileNotFoundError:
                    original_exists = False
                if original_exists:
                    details = {
                        "lock_initialization_cleanup_incomplete": True,
                        "lock_path": str(lock_path),
                        "token": token,
                    }
        except OSError:
            pass
        if lock_fd is not None:
            os.close(lock_fd)
            lock_fd = None
        os.close(parent_fd)
        raise AppError(
            "io_error",
            "Cannot initialize the required write lock.",
            details=details,
        ) from exc
    assert lock_fd is not None
    lock_identity = (lock_info.st_dev, lock_info.st_ino)
    os.close(lock_fd)
    os.close(parent_fd)
    return LockHandle(
        path=lock_path,
        token=token,
        owner=owner,
        parent_identity=parent_identity,
        lock_identity=lock_identity,
        owner_sha256=sha256_bytes(owner_bytes),
    )


def release_lock(handle: LockHandle) -> None:
    parent_fd: int | None = None
    lock_fd: int | None = None
    try:
        parent_fd = open_directory_without_symlinks(
            handle.path.parent, label="write-lock parent"
        )
        parent_info = os.fstat(parent_fd)
        if (parent_info.st_dev, parent_info.st_ino) != handle.parent_identity:
            raise AppError(
                "unsafe_or_corrupt",
                "Write-lock parent changed during the operation; no redirected cleanup occurred.",
            )
        lock_fd = os.open(
            handle.path.name,
            os.O_RDONLY
            | os.O_DIRECTORY
            | os.O_NOFOLLOW
            | getattr(os, "O_CLOEXEC", 0),
            dir_fd=parent_fd,
        )
        lock_info = os.fstat(lock_fd)
        if (lock_info.st_dev, lock_info.st_ino) != handle.lock_identity:
            raise AppError(
                "unsafe_or_corrupt",
                "Write-lock identity changed during the operation; the lock was preserved.",
            )
        current, owner_raw = read_lock_owner_from_fd(lock_fd)
    except AppError as exc:
        exc.details.update(
            {
                "lock_cleanup_failed": True,
                "lock_path": str(handle.path),
                "token": handle.token,
                "release_renamed": False,
            }
        )
        if lock_fd is not None:
            os.close(lock_fd)
        if parent_fd is not None:
            os.close(parent_fd)
        raise
    except OSError as exc:
        if lock_fd is not None:
            os.close(lock_fd)
        if parent_fd is not None:
            os.close(parent_fd)
        raise AppError(
            "io_error",
            "Cannot bind the owned write lock for cleanup.",
            details={
                "lock_cleanup_failed": True,
                "lock_path": str(handle.path),
                "token": handle.token,
                "release_renamed": False,
            },
        ) from exc
    if (
        not current
        or current.get("token") != handle.token
        or owner_raw is None
        or sha256_bytes(owner_raw) != handle.owner_sha256
    ):
        os.close(lock_fd)
        os.close(parent_fd)
        raise AppError(
            "unsafe_or_corrupt",
            "Write-lock ownership changed during the operation; the lock was preserved.",
            details={
                "lock_cleanup_failed": True,
                "lock_path": str(handle.path),
                "token": handle.token,
            },
        )
    released_name = f"{handle.path.name}.released-{handle.token}"
    released_path = handle.path.parent / released_name
    release_renamed = False
    try:
        os.rename(
            handle.path.name,
            released_name,
            src_dir_fd=parent_fd,
            dst_dir_fd=parent_fd,
        )
        release_renamed = True
        os.fsync(parent_fd)
        os.unlink("owner.json", dir_fd=lock_fd)
        os.rmdir(released_name, dir_fd=parent_fd)
        os.fsync(parent_fd)
    except (OSError, KeyboardInterrupt) as exc:
        details: dict[str, Any] = {
            "lock_cleanup_failed": True,
            "lock_path": str(handle.path),
            "token": handle.token,
            "release_renamed": release_renamed,
        }
        if release_renamed:
            details["released_lock_path"] = str(released_path)
            details["released_lock_name"] = released_path.name
            if owner_raw is not None:
                details["owner_sha256"] = sha256_bytes(owner_raw)
        os.close(lock_fd)
        os.close(parent_fd)
        raise AppError(
            "io_error",
            "The operation finished but its owned write lock could not be removed.",
            details=details,
        ) from exc
    os.close(lock_fd)
    os.close(parent_fd)


def lock_cleanup_recovery(
    lock_path: Path, token: str, details: Mapping[str, Any]
) -> dict[str, Any]:
    """Return the exact, fail-closed reconcile route for owned lock residue."""
    scope = (
        "catalog"
        if lock_path.name == ".to-implementation-plan.catalog.lock"
        else "plan"
    )
    selector = "catalog" if scope == "catalog" else lock_path.parent.name
    if details.get("release_renamed") is True:
        recovery_input: dict[str, Any] = {
            "action": "remove_released_lock",
            "scope": scope,
            "relative_name": details.get("released_lock_name")
            or f"{lock_path.name}.released-{token}",
            "token": token,
        }
        owner_sha256 = details.get("owner_sha256")
        if isinstance(owner_sha256, str) and re.fullmatch(
            r"[a-fA-F0-9]{64}", owner_sha256
        ):
            recovery_input["owner_sha256"] = owner_sha256.lower()
    else:
        recovery_input = {
            "action": "remove_abandoned_lock",
            "scope": scope,
            "token": token,
        }
    return {
        "command": "reconcile",
        "selector": selector,
        "input": recovery_input,
        "then": "validate",
    }


def append_recovery_tail(
    recovery: Mapping[str, Any], tail: Mapping[str, Any]
) -> dict[str, Any]:
    """Append one ordered recovery step without discarding an existing chain."""
    result = copy.deepcopy(dict(recovery))
    cursor = result
    while isinstance(cursor.get("then"), Mapping):
        cursor = cursor["then"]
    existing = cursor.get("then")
    if isinstance(existing, str) and existing:
        next_step: dict[str, Any] = {"command": existing}
        cursor["then"] = next_step
        cursor = next_step
    elif existing is not None:
        raise AppError(
            "io_error",
            "An existing recovery chain has an unsupported continuation.",
        )
    cursor["then"] = copy.deepcopy(dict(tail))
    return result


@contextmanager
def held_lock(
    lock_path: Path, command: str, outcome_probe: Any | None = None
) -> Iterator[LockHandle]:
    handle = acquire_lock(lock_path, command)
    primary_error: BaseException | None = None
    try:
        _ontology_checkpoint()
        yield handle
    except BaseException as exc:
        primary_error = exc
        raise
    finally:
        try:
            release_lock(handle)
        except AppError as exc:
            if primary_error is None:
                if outcome_probe is not None:
                    observed_outcome = outcome_probe()
                    if (
                        isinstance(observed_outcome, Mapping)
                        and isinstance(observed_outcome.get("mutation"), bool)
                    ):
                        exc.details["committed_outcome"] = copy.deepcopy(
                            observed_outcome
                        )
                exc.details["recovery_required"] = lock_cleanup_recovery(
                    handle.path, handle.token, exc.details
                )
                raise
            if isinstance(primary_error, AppError):
                primary_error.details["lock_cleanup_failed"] = True
                primary_error.details["lock_cleanup"] = {
                    key: copy.deepcopy(exc.details[key])
                    for key in (
                        "lock_path",
                        "token",
                        "release_renamed",
                        "released_lock_name",
                        "owner_sha256",
                    )
                    if key in exc.details
                }
                primary_error.details["recovery_required"] = lock_cleanup_recovery(
                    handle.path, handle.token, exc.details
                )
            else:
                exc.details["recovery_required"] = lock_cleanup_recovery(
                    handle.path, handle.token, exc.details
                )
                raise exc from primary_error


def catalog_lock_path(context: Context) -> Path:
    return context.plans_root / ".to-implementation-plan.catalog.lock"


def plan_lock_path(plan_dir: Path) -> Path:
    return plan_dir / ".to-implementation-plan.plan.lock"


def ensure_catalog_for_write(context: Context) -> tuple[int, int]:
    """Open or create the catalog through bound no-follow directory handles."""
    try:
        catalog_fd = open_directory_without_symlinks(
            context.plans_root, label="plans catalog"
        )
    except AppError as exc:
        if exc.category != "not_found":
            raise
    else:
        try:
            info = os.fstat(catalog_fd)
            return info.st_dev, info.st_ino
        finally:
            os.close(catalog_fd)

    parent_fd = open_directory_without_symlinks(
        context.plans_root.parent, label="plans-catalog parent"
    )
    catalog_fd: int | None = None
    created = False
    try:
        if context.plans_root.parent == context.project_root:
            parent_info = os.fstat(parent_fd)
            if (parent_info.st_dev, parent_info.st_ino) != context.project_root_identity:
                raise AppError(
                    "unsafe_or_corrupt",
                    "The project root changed before catalog initialization.",
                )
        os.mkdir(context.plans_root.name, mode=0o700, dir_fd=parent_fd)
        created = True
        catalog_fd = os.open(
            context.plans_root.name,
            os.O_RDONLY
            | os.O_DIRECTORY
            | os.O_NOFOLLOW
            | getattr(os, "O_CLOEXEC", 0),
            dir_fd=parent_fd,
        )
        catalog_info = os.fstat(catalog_fd)
        catalog_identity = (catalog_info.st_dev, catalog_info.st_ino)
        os.fsync(parent_fd)
        if not directory_path_matches_identity(
            context.plans_root, catalog_identity, label="plans catalog"
        ):
            raise AppError(
                "unsafe_or_corrupt",
                "The plans catalog path changed during initialization.",
            )
        return catalog_identity
    except FileExistsError:
        # A concurrent creator may have won. Reopen through the full no-follow
        # path rather than trusting the unresolved directory entry.
        if created:
            raise
        try:
            existing_fd = open_directory_without_symlinks(
                context.plans_root, label="plans catalog"
            )
            try:
                info = os.fstat(existing_fd)
                return info.st_dev, info.st_ino
            finally:
                os.close(existing_fd)
        except AppError as reopen_error:
            raise AppError(
                "unsafe_or_corrupt",
                "The concurrently created plans catalog is unsafe.",
            ) from reopen_error
    except (AppError, OSError, KeyboardInterrupt) as exc:
        cleanup_incomplete = False
        if created:
            try:
                os.rmdir(context.plans_root.name, dir_fd=parent_fd)
                os.fsync(parent_fd)
                created = False
            except (OSError, KeyboardInterrupt):
                cleanup_incomplete = True
        if isinstance(exc, AppError) and not cleanup_incomplete:
            raise
        raise AppError(
            "io_error",
            "Cannot initialize the plans catalog durably.",
            details={
                "catalog_initialization_cleanup_incomplete": cleanup_incomplete,
                "filesystem_mutation": cleanup_incomplete,
                "catalog_name": context.plans_root.name,
            },
        ) from exc
    finally:
        if catalog_fd is not None:
            os.close(catalog_fd)
        os.close(parent_fd)


def create_bound_subdirectory(
    parent_path: Path,
    expected_parent_identity: tuple[int, int],
    child_name: str,
) -> BoundCreatedDirectory:
    """Create one empty child with mkdirat and retain both bound handles."""
    parent_fd = open_directory_without_symlinks(
        parent_path, label="managed-directory parent"
    )
    child_fd: int | None = None
    created = False
    try:
        parent_info = os.fstat(parent_fd)
        parent_identity = (parent_info.st_dev, parent_info.st_ino)
        if parent_identity != expected_parent_identity:
            raise AppError(
                "unsafe_or_corrupt",
                "The managed-directory parent changed before creation.",
            )
        os.mkdir(child_name, mode=0o700, dir_fd=parent_fd)
        created = True
        child_fd = os.open(
            child_name,
            os.O_RDONLY
            | os.O_DIRECTORY
            | os.O_NOFOLLOW
            | getattr(os, "O_CLOEXEC", 0),
            dir_fd=parent_fd,
        )
        child_info = os.fstat(child_fd)
        child_identity = (child_info.st_dev, child_info.st_ino)
        os.fsync(parent_fd)
        if not directory_path_matches_identity(
            parent_path, parent_identity, label="managed-directory parent"
        ) or not directory_path_matches_identity(
            parent_path / child_name,
            child_identity,
            label="managed directory",
        ):
            raise AppError(
                "unsafe_or_corrupt",
                "The managed-directory path changed during creation.",
            )
        result = BoundCreatedDirectory(
            parent_fd=parent_fd,
            child_fd=child_fd,
            parent_identity=parent_identity,
            child_identity=child_identity,
            parent_path=parent_path,
            child_name=child_name,
        )
        child_fd = None
        parent_fd = -1
        return result
    except FileExistsError as exc:
        raise AppError(
            "unsafe_or_corrupt", "Allocated managed directory already exists."
        ) from exc
    except (AppError, OSError, KeyboardInterrupt) as exc:
        cleanup_incomplete = False
        if created:
            try:
                os.rmdir(child_name, dir_fd=parent_fd)
                os.fsync(parent_fd)
                created = False
            except (OSError, KeyboardInterrupt):
                cleanup_incomplete = True
        if isinstance(exc, AppError) and not cleanup_incomplete:
            raise
        raise AppError(
            "io_error",
            "Cannot create the managed directory durably.",
            details={
                "directory_creation_cleanup_incomplete": cleanup_incomplete,
                "filesystem_mutation": cleanup_incomplete,
                "directory": child_name,
            },
        ) from exc
    finally:
        if child_fd is not None:
            os.close(child_fd)
        if parent_fd >= 0:
            os.close(parent_fd)


def ensure_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AppError("invalid_input", f"{label} must be a JSON object.")
    return value


def list_or_empty(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def normalized_marker_text(value: Any) -> str:
    """Normalize short human markers across case, Unicode, and punctuation."""
    normalized = unicodedata.normalize("NFKC", str(value)).casefold()
    return " ".join(re.sub(r"[_\W]+", " ", normalized).split())


def is_meaningless_evidence_text(value: Any) -> bool:
    normalized = normalized_marker_text(value)
    if normalized in MEANINGLESS_EVIDENCE_MARKERS:
        return True
    tokens = normalized.split()
    if not tokens:
        return True
    marker_tokens = {
        token
        for marker in MEANINGLESS_EVIDENCE_MARKERS
        for token in marker.split()
    }
    if all(token in marker_tokens for token in tokens):
        return True
    if len(tokens) > 1 and all(len(token) == 1 for token in tokens):
        return "".join(tokens) in {
            marker.replace(" ", "") for marker in MEANINGLESS_EVIDENCE_MARKERS
        }
    return False


def is_readiness_placeholder(value: Any) -> bool:
    normalized = normalized_marker_text(value)
    if not normalized:
        return True
    if normalized in READINESS_PLACEHOLDER_MARKERS:
        return True
    tokens = normalized.split()
    if len(tokens) > 1 and all(len(token) == 1 for token in tokens):
        collapsed = "".join(tokens)
        return collapsed in {
            marker.replace(" ", "") for marker in READINESS_PLACEHOLDER_MARKERS
        }
    strong_markers = {"placeholder", "tba", "tbc", "tbd", "todo"}
    marker_fillers = {"here", "later", "needed", "pending", "required", "text", "value"}
    if tokens[0] in strong_markers and all(
        token in marker_fillers for token in tokens[1:]
    ):
        return True
    prefix_length = 0
    while prefix_length < len(tokens) and len(tokens[prefix_length]) == 1:
        prefix_length += 1
    if prefix_length > 1 and "".join(tokens[:prefix_length]) in strong_markers and all(
        token in marker_fillers for token in tokens[prefix_length:]
    ):
        return True
    if len(tokens) >= 2 and tokens[:2] in (["fill", "me"], ["fill", "this"]):
        return True
    if len(tokens) >= 3 and tokens[:2] == ["to", "be"] and tokens[2] in {
        "announced",
        "confirmed",
        "decided",
        "determined",
    }:
        return True
    return False


def readiness_semantic_texts(plan: Mapping[str, Any]) -> Iterator[tuple[str, str]]:
    """Yield readiness-critical semantic strings with deterministic paths."""

    def fields(
        record: Any,
        prefix: str,
        scalar_fields: Sequence[str],
        list_fields: Sequence[str],
    ) -> Iterator[tuple[str, str]]:
        if not isinstance(record, Mapping):
            return
        for field in scalar_fields:
            value = record.get(field)
            if isinstance(value, str):
                yield f"{prefix}.{field}", value
        for field in list_fields:
            for index, value in enumerate(list_or_empty(record.get(field))):
                if isinstance(value, str):
                    yield f"{prefix}.{field}[{index}]", value

    if isinstance(plan.get("title"), str):
        yield "title", str(plan["title"])
    if isinstance(plan.get("status_reason"), str):
        yield "status_reason", str(plan["status_reason"])
    yield from fields(
        plan.get("objective"),
        "objective",
        ("summary", "user_value"),
        ("success_outcomes",),
    )
    yield from fields(
        plan.get("scope"),
        "scope",
        ("execution_authority",),
        ("in_scope", "out_of_scope"),
    )
    yield from fields(
        plan.get("project"),
        "project",
        (),
        ("constraints", "preserved_paths"),
    )
    project = plan.get("project")
    if isinstance(project, Mapping):
        for index, guidance in enumerate(list_or_empty(project.get("guidance"))):
            yield from fields(
                guidance,
                f"project.guidance[{index}]",
                ("summary",),
                (),
            )
        for index, fact in enumerate(list_or_empty(project.get("baseline_facts"))):
            yield from fields(
                fact,
                f"project.baseline_facts[{index}]",
                ("fact",),
                (),
            )
    collection_contracts = (
        ("sources", ("title",), ("facts_used",)),
        (
            "requirements",
            ("title", "outcome", "intent"),
            ("acceptance_criteria", "negative_requirements"),
        ),
        (
            "phases",
            ("title", "objective"),
            ("scope", "entry_conditions", "exit_criteria", "risks"),
        ),
        (
            "tasks",
            ("title", "action"),
            (
                "design_basis",
                "target_artifacts",
                "risks",
                "acceptance_criteria",
                "verification_steps",
            ),
        ),
        ("decisions", ("statement", "authority_basis"), (),),
        ("open_questions", ("question", "answer", "authority_basis"), (),),
        ("assumptions", ("statement", "basis", "authority_basis"), (),),
    )
    for collection, scalar_fields, list_fields in collection_contracts:
        for index, record in enumerate(list_or_empty(plan.get(collection))):
            yield from fields(
                record,
                f"{collection}[{index}]",
                scalar_fields,
                list_fields,
            )
            if collection == "requirements" and isinstance(record, Mapping):
                yield from fields(
                    record.get("disposition"),
                    f"requirements[{index}].disposition",
                    ("reason", "authority_basis"),
                    (),
                )
            if collection == "tasks":
                yield from fields(
                    record,
                    f"tasks[{index}]",
                    (
                        "blocker_reason",
                        "pause_reason",
                        "skip_reason",
                        "skip_authority",
                    ),
                    (),
                )
    coverage = plan.get("coverage")
    if isinstance(coverage, Mapping):
        for collection in ("source_to_requirement", "requirement_to_task"):
            for index, edge in enumerate(list_or_empty(coverage.get(collection))):
                if isinstance(edge, Mapping):
                    yield from fields(
                        edge.get("disposition"),
                        f"coverage.{collection}[{index}].disposition",
                        ("reason", "authority_basis"),
                        (),
                    )


def _allocate_id(prefix: str, used: set[str], width: int = 3) -> str:
    number = 1
    while True:
        candidate = f"{prefix}-{number:0{width}d}"
        if candidate not in used:
            used.add(candidate)
            return candidate
        number += 1


def _fill_list(record: dict[str, Any], key: str) -> None:
    if key not in record:
        record[key] = []


TASK_DEFINITION_FIELDS = (
    "task_id",
    "phase_id",
    "title",
    "action",
    "requirement_ids",
    "design_basis",
    "target_artifacts",
    "dependencies",
    "parallel_group",
    "risks",
    "acceptance_criteria",
    "verification_steps",
)
REQUIREMENT_DEFINITION_FIELDS = (
    "requirement_id",
    "title",
    "outcome",
    "intent",
    "source_ids",
    "acceptance_criteria",
    "dependencies",
    "negative_requirements",
)


def build_target_digest_context(plan: Mapping[str, Any]) -> dict[str, Any]:
    """Index plan context once so per-target evidence binding stays linear."""
    return {
        "requirements": {
            str(item.get("requirement_id")): item
            for item in list_or_empty(plan.get("requirements"))
            if isinstance(item, Mapping)
            and isinstance(item.get("requirement_id"), str)
        },
        "sources": {
            str(item.get("source_id")): item
            for item in list_or_empty(plan.get("sources"))
            if isinstance(item, Mapping) and isinstance(item.get("source_id"), str)
        },
        "coverage": {
            str(item.get("requirement_id")): item
            for item in list_or_empty(
                plan.get("coverage", {}).get("requirement_to_task")
                if isinstance(plan.get("coverage"), Mapping)
                else None
            )
            if isinstance(item, Mapping)
            and isinstance(item.get("requirement_id"), str)
        },
        "phases": {
            str(item.get("phase_id")): item
            for item in list_or_empty(plan.get("phases"))
            if isinstance(item, Mapping) and isinstance(item.get("phase_id"), str)
        },
    }


def target_definition_digest(
    target: Mapping[str, Any],
    target_kind: str,
    plan: Mapping[str, Any] | None = None,
    digest_context: Mapping[str, Any] | None = None,
) -> str:
    fields = (
        TASK_DEFINITION_FIELDS if target_kind == "task" else REQUIREMENT_DEFINITION_FIELDS
    )
    definition: dict[str, Any] = {
        "target": {field: copy.deepcopy(target.get(field)) for field in fields}
    }
    if plan is not None:
        indexes = digest_context or build_target_digest_context(plan)
        requirements = indexes.get("requirements", {})
        indexed_sources = indexes.get("sources", {})
        indexed_coverage = indexes.get("coverage", {})
        indexed_phases = indexes.get("phases", {})
        requirement_ids = (
            [str(target.get("requirement_id"))]
            if target_kind == "requirement"
            else [str(item) for item in list_or_empty(target.get("requirement_ids"))]
        )
        linked_requirements = [
            {
                field: copy.deepcopy(requirements[requirement_id].get(field))
                for field in REQUIREMENT_DEFINITION_FIELDS
            }
            for requirement_id in sorted(requirement_ids)
            if requirement_id in requirements
        ]
        source_ids = {
            str(source_id)
            for requirement_id in requirement_ids
            for source_id in list_or_empty(
                requirements.get(requirement_id, {}).get("source_ids")
            )
        }
        sources = [
            copy.deepcopy(indexed_sources[source_id])
            for source_id in sorted(source_ids)
            if source_id in indexed_sources
        ]
        coverage = [
            copy.deepcopy(indexed_coverage[requirement_id])
            for requirement_id in sorted(set(requirement_ids))
            if requirement_id in indexed_coverage
        ]
        phase_context: dict[str, Any] | None = None
        if target_kind == "task":
            phase = indexed_phases.get(str(target.get("phase_id")))
            if phase is not None:
                phase_context = {
                    field: copy.deepcopy(phase.get(field))
                    for field in (
                        "phase_id",
                        "title",
                        "objective",
                        "scope",
                        "depends_on_phase_ids",
                        "entry_conditions",
                        "exit_criteria",
                        "risks",
                    )
                }
        project = plan.get("project", {})
        definition["context"] = {
            "project": {
                field: copy.deepcopy(project.get(field))
                for field in ("root_hint", "guidance", "constraints", "preserved_paths")
            },
            "objective": copy.deepcopy(plan.get("objective")),
            "scope": copy.deepcopy(plan.get("scope")),
            "requirements": linked_requirements,
            "sources": sorted(sources, key=lambda item: str(item.get("source_id"))),
            "coverage": sorted(
                coverage, key=lambda item: str(item.get("requirement_id"))
            ),
            "phase": phase_context,
        }
    return "sha256:" + sha256_bytes(canonical_bytes(definition))


def _normalize_evidence(
    evidence: dict[str, Any], used_ids: set[str], now: str, target_digest: str
) -> dict[str, Any]:
    result = copy.deepcopy(evidence)
    if not result.get("evidence_id"):
        result["evidence_id"] = _allocate_id("EVID", used_ids)
    else:
        used_ids.add(str(result["evidence_id"]))
    result.setdefault("timestamp", now)
    result.setdefault("evidence_type", "planned_check")
    result.setdefault(
        "result_status",
        "planned" if result.get("evidence_type") == "planned_check" else None,
    )
    result.setdefault("description", "")
    result.setdefault("locator_or_command", None)
    result.setdefault("observed_result", "")
    result.setdefault("verification_level", "planned")
    result.setdefault("observation_source", "plan")
    result.setdefault("target_digest", target_digest)
    return result


def open_directory_without_symlinks(path: Path, *, label: str) -> int:
    """Open one directory while binding every component without symlinks."""
    if not path.is_absolute():
        raise AppError("invalid_input", f"{label} path must be absolute.")
    if os.name != "posix" or not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
        raise AppError(
            "unsafe_or_corrupt",
            "Safe no-symlink file intake requires a POSIX host with O_NOFOLLOW and O_DIRECTORY support.",
        )
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    directory_flag = getattr(os, "O_DIRECTORY", 0)
    close_on_exec = getattr(os, "O_CLOEXEC", 0)
    directory_fd: int | None = None
    try:
        directory_fd = os.open(
            path.anchor,
            os.O_RDONLY | directory_flag | nofollow | close_on_exec,
        )
        for component in path.parts[1:]:
            next_fd = os.open(
                component,
                os.O_RDONLY | directory_flag | nofollow | close_on_exec,
                dir_fd=directory_fd,
            )
            os.close(directory_fd)
            directory_fd = next_fd
        result_fd = directory_fd
        directory_fd = None
        return result_fd
    except FileNotFoundError as exc:
        raise AppError("not_found", f"{label} does not exist.") from exc
    except ValueError as exc:
        raise AppError("invalid_input", f"{label} path contains an invalid character.") from exc
    except OSError as exc:
        if exc.errno in {errno.ELOOP, errno.ENOTDIR}:
            raise AppError(
                "unsafe_or_corrupt",
                f"{label} traverses a symlink or non-directory component.",
            ) from exc
        raise AppError("io_error", f"Cannot safely open {label}.") from exc
    finally:
        if directory_fd is not None:
            os.close(directory_fd)


def directory_path_matches_identity(
    path: Path, expected_identity: tuple[int, int], *, label: str
) -> bool:
    """Reopen an absolute path without symlinks and compare its bound inode."""
    descriptor: int | None = None
    try:
        descriptor = open_directory_without_symlinks(path, label=label)
        info = os.fstat(descriptor)
        return (info.st_dev, info.st_ino) == expected_identity
    except (AppError, OSError):
        return False
    finally:
        if descriptor is not None:
            os.close(descriptor)


def open_regular_file_without_symlinks(
    path: Path, *, label: str
) -> tuple[int, os.stat_result]:
    """Open one regular file without following any component symlink."""
    if not path.is_absolute() or not path.name:
        raise AppError("invalid_input", f"{label} path must be an absolute file path.")
    directory_fd = open_directory_without_symlinks(path.parent, label=f"{label} parent")
    file_fd: int | None = None
    try:
        entry_info = os.stat(path.name, dir_fd=directory_fd, follow_symlinks=False)
        if stat.S_ISLNK(entry_info.st_mode) or not stat.S_ISREG(entry_info.st_mode):
            raise AppError(
                "unsafe_or_corrupt",
                f"{label} must be a regular, non-symlink file.",
            )
        file_fd = os.open(
            path.name,
            os.O_RDONLY
            | os.O_NOFOLLOW
            | getattr(os, "O_NONBLOCK", 0)
            | getattr(os, "O_CLOEXEC", 0),
            dir_fd=directory_fd,
        )
        info = os.fstat(file_fd)
        if not stat.S_ISREG(info.st_mode) or (
            info.st_dev,
            info.st_ino,
        ) != (entry_info.st_dev, entry_info.st_ino):
            raise AppError(
                "unsafe_or_corrupt",
                f"{label} must be a regular, non-symlink file.",
            )
        result_fd = file_fd
        file_fd = None
        return result_fd, info
    except AppError:
        raise
    except FileNotFoundError as exc:
        raise AppError("not_found", f"{label} does not exist.") from exc
    except ValueError as exc:
        raise AppError("invalid_input", f"{label} path contains an invalid character.") from exc
    except OSError as exc:
        if exc.errno in {errno.ELOOP, errno.ENOTDIR}:
            raise AppError("unsafe_or_corrupt", f"{label} traverses a symlink.") from exc
        raise AppError("io_error", f"Cannot safely open {label}.") from exc
    finally:
        if file_fd is not None:
            os.close(file_fd)
        os.close(directory_fd)


def read_local_file_without_symlinks(path: Path, *, label: str) -> bytes:
    """Read one bounded local source without following any path symlink."""
    file_fd, info = open_regular_file_without_symlinks(path, label=label)
    try:
        if info.st_size > MAX_JSON_BYTES:
            raise AppError(
                "invalid_input",
                f"{label} exceeds the supported size.",
                details={"maximum_bytes": MAX_JSON_BYTES},
            )
        chunks: list[bytes] = []
        remaining = MAX_JSON_BYTES + 1
        while remaining:
            block = os.read(file_fd, min(1024 * 1024, remaining))
            if not block:
                break
            chunks.append(block)
            remaining -= len(block)
        data = b"".join(chunks)
        if len(data) > MAX_JSON_BYTES:
            raise AppError("invalid_input", f"{label} exceeds the supported size.")
        return data
    except OSError as exc:
        raise AppError("io_error", f"Cannot safely read {label}.") from exc
    finally:
        os.close(file_fd)


def validate_utf8_text_bytes(data: bytes, *, label: str) -> None:
    """Reject binary or unsupported bytes for a direct-text inspection claim."""
    if data.startswith(b"\xef\xbb\xbf"):
        raise AppError("invalid_input", f"{label} is not supported UTF-8 text.")
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise AppError("invalid_input", f"{label} is not supported UTF-8 text.") from exc
    if "\x00" in text or any(
        ord(character) < 32 and character not in {"\t", "\n", "\r"}
        for character in text
    ):
        raise AppError("invalid_input", f"{label} contains unsupported binary data.")


def validate_agent_inspected_local_sources(
    sources: Sequence[Mapping[str, Any]], context: Context
) -> None:
    """Reject unsupported local-source access claims before canonical write."""
    for source in sources:
        if source.get("provenance_mode") != "agent_inspected":
            continue
        kind = source.get("kind")
        inspection_method = source.get("inspection_method")
        if kind == "url":
            if inspection_method != "browser_tool":
                raise AppError(
                    "invalid_input",
                    "An agent-inspected URL source requires browser_tool inspection.",
                    details={"targets": [str(source.get("source_id", "source"))]},
                )
            continue
        if not _is_enum_value(kind, {"file", "trd", "prd"}):
            raise AppError(
                "invalid_input",
                "Agent-inspected sources must be a URL or a supported local file kind.",
                details={"targets": [str(source.get("source_id", "source"))]},
            )
        facts = source.get("facts_used") if isinstance(source.get("facts_used"), list) else []
        limitations = (
            source.get("access_limitations")
            if isinstance(source.get("access_limitations"), list)
            else []
        )
        locator = source.get("locator")
        source_id = str(source.get("source_id", "local source"))
        digest = source.get("digest")
        claiming_access = bool(facts) or digest is not None or not limitations
        if not isinstance(locator, str) or not locator.strip():
            if claiming_access:
                raise AppError(
                    "invalid_input",
                    "An agent-inspected local source requires an exact locator or an honest access limitation with no claimed facts.",
                    details={"targets": [source_id]},
                )
            continue
        if "\x00" in locator or any(
            ord(character) < 32 for character in locator
        ):
            raise AppError(
                "invalid_input",
                "An agent-inspected local source locator contains an invalid control character.",
                details={"targets": [source_id]},
            )
        raw_path = Path(locator)
        path = raw_path if raw_path.is_absolute() else context.project_root / raw_path
        path = Path(os.path.abspath(path))
        try:
            data = read_local_file_without_symlinks(
                path, label="agent-inspected local source"
            )
            if inspection_method == "direct_text":
                validate_utf8_text_bytes(data, label="agent-inspected local source")
            elif not _is_enum_value(inspection_method, LOCAL_INSPECTION_METHODS):
                raise AppError(
                    "invalid_input",
                    "An agent-inspected local source requires a supported inspection method.",
                )
            if facts and not (
                isinstance(digest, str)
                and re.fullmatch(r"sha256:[a-f0-9]{64}", digest)
            ):
                raise AppError(
                    "invalid_input",
                    "Agent-inspected local-source facts require a digest of the inspected file.",
                )
        except AppError as exc:
            if claiming_access:
                exc.details.setdefault("targets", [source_id])
                raise
            continue
        if isinstance(digest, str) and re.fullmatch(r"sha256:[a-f0-9]{64}", digest):
            if sha256_bytes(data) != digest.removeprefix("sha256:"):
                raise AppError(
                    "invalid_input",
                    "An agent-inspected local source digest no longer matches its record.",
                    details={"targets": [source_id]},
                )


def normalize_plan_input(payload: dict[str, Any], context: Context) -> dict[str, Any]:
    """Normalize a create payload into the complete V1 canonical shape."""
    guard_prohibited_content(payload)
    now = timestamp()
    title_value = payload.get("title")
    if not isinstance(title_value, str) or not title_value.strip():
        raise AppError("invalid_input", "create input requires a nonblank title.")
    slug_value = payload.get("slug") or safe_slug(title_value)
    if not isinstance(slug_value, str):
        raise AppError("invalid_input", "slug must be a string.")
    slug_value = safe_slug(slug_value)

    project = copy.deepcopy(payload.get("project", {}))
    ensure_object(project, "project")
    supplied_root = project.get("root_hint")
    if supplied_root == ".":
        supplied_root = str(context.project_root)
    if supplied_root not in (None, "", str(context.project_root)):
        try:
            if Path(str(supplied_root)).resolve(strict=True) != context.project_root:
                raise AppError(
                    "unsafe_or_corrupt",
                    "project.root_hint does not match --project-root.",
                )
        except (FileNotFoundError, OSError) as exc:
            raise AppError(
                "unsafe_or_corrupt",
                "project.root_hint does not resolve to --project-root.",
            ) from exc
    project["root_hint"] = str(context.project_root)
    project.setdefault("inspected_at", None)
    for key in (
        "guidance",
        "baseline_facts",
        "constraints",
        "preserved_paths",
        "evidence_gaps",
    ):
        _fill_list(project, key)

    objective_value = payload.get("objective", {})
    if isinstance(objective_value, str):
        objective = {
            "summary": objective_value,
            "user_value": "",
            "success_outcomes": [],
        }
    else:
        objective = copy.deepcopy(ensure_object(objective_value, "objective"))
        objective.setdefault("summary", "")
        objective.setdefault("user_value", "")
        _fill_list(objective, "success_outcomes")

    scope = copy.deepcopy(payload.get("scope", {}))
    ensure_object(scope, "scope")
    _fill_list(scope, "in_scope")
    _fill_list(scope, "out_of_scope")
    scope.setdefault(
        "execution_authority",
        "This plan records work but does not itself authorize execution.",
    )

    sources = copy.deepcopy(payload.get("sources", []))
    requirements = copy.deepcopy(payload.get("requirements", []))
    decisions = copy.deepcopy(payload.get("decisions", []))
    questions = copy.deepcopy(payload.get("open_questions", []))
    assumptions = copy.deepcopy(payload.get("assumptions", []))
    phases = copy.deepcopy(payload.get("phases", []))
    tasks = copy.deepcopy(payload.get("tasks", []))
    for label, records in (
        ("sources", sources),
        ("requirements", requirements),
        ("decisions", decisions),
        ("open_questions", questions),
        ("assumptions", assumptions),
        ("phases", phases),
        ("tasks", tasks),
    ):
        if not isinstance(records, list) or not all(isinstance(item, dict) for item in records):
            raise AppError("invalid_input", f"{label} must be an array of objects.")

    used_source_ids = {str(item.get("source_id")) for item in sources if item.get("source_id")}
    for source in sources:
        if not source.get("source_id"):
            source["source_id"] = _allocate_id("SRC", used_source_ids)
        source.setdefault("kind", "other")
        source.setdefault("locator", None)
        source.setdefault("title", "Untitled source")
        source.setdefault("accessed_at", now)
        source.setdefault("digest", None)
        _fill_list(source, "facts_used")
        _fill_list(source, "access_limitations")
        source.setdefault("provenance_mode", "user_supplied")
        source.setdefault("external_id", None)
        if source.get("inspection_method") is None:
            if source.get("provenance_mode") == "agent_inspected":
                source["inspection_method"] = (
                    "browser_tool" if source.get("kind") == "url" else "direct_text"
                )
            else:
                source["inspection_method"] = None
    validate_agent_inspected_local_sources(sources, context)

    used_req_ids = {
        str(item.get("requirement_id")) for item in requirements if item.get("requirement_id")
    }
    evidence_ids: set[str] = set()
    for requirement in requirements:
        if not requirement.get("requirement_id"):
            requirement["requirement_id"] = _allocate_id("REQ", used_req_ids)
        requirement.setdefault("title", "Untitled requirement")
        requirement.setdefault("outcome", "")
        requirement.setdefault("intent", "")
        for key in (
            "source_ids",
            "acceptance_criteria",
            "dependencies",
            "negative_requirements",
        ):
            _fill_list(requirement, key)
        requirement.setdefault("status", "active")
        requirement.setdefault("disposition", None)
        raw_evidence = requirement.setdefault("evidence", [])
        if isinstance(raw_evidence, list):
            definition_digest = target_definition_digest(requirement, "requirement")
            requirement["evidence"] = [
                _normalize_evidence(item, evidence_ids, now, definition_digest)
                if isinstance(item, dict)
                else item
                for item in raw_evidence
            ]

    used_decision_ids = {
        str(item.get("decision_id")) for item in decisions if item.get("decision_id")
    }
    for decision in decisions:
        if not decision.get("decision_id"):
            decision["decision_id"] = _allocate_id("DEC", used_decision_ids)
        decision.setdefault("statement", "")
        decision.setdefault("status", "proposed")
        _fill_list(decision, "source_ids")
        decision.setdefault("authority_basis", "")
        decision.setdefault("decided_at", None)

    used_question_ids = {
        str(item.get("question_id")) for item in questions if item.get("question_id")
    }
    for question in questions:
        if not question.get("question_id"):
            question["question_id"] = _allocate_id("Q", used_question_ids)
        question.setdefault("question", "")
        _fill_list(question, "affects")
        _fill_list(question, "prerequisites")
        question.setdefault("status", "open")
        question.setdefault("answer", None)
        question.setdefault("authority_basis", None)

    used_assumption_ids = {
        str(item.get("assumption_id")) for item in assumptions if item.get("assumption_id")
    }
    for assumption in assumptions:
        if not assumption.get("assumption_id"):
            assumption["assumption_id"] = _allocate_id("ASM", used_assumption_ids)
        assumption.setdefault("statement", "")
        assumption.setdefault("basis", "")
        assumption.setdefault("status", "unconfirmed")
        assumption.setdefault("authority_basis", None)

    used_phase_ids = {str(item.get("phase_id")) for item in phases if item.get("phase_id")}
    for phase in phases:
        if not phase.get("phase_id"):
            phase["phase_id"] = _allocate_id("PHASE", used_phase_ids)
        phase.setdefault("title", "Untitled phase")
        phase.setdefault("objective", "")
        for key in (
            "scope",
            "depends_on_phase_ids",
            "entry_conditions",
            "exit_criteria",
            "task_ids",
            "risks",
        ):
            _fill_list(phase, key)
        phase.setdefault("status", "planned")

    used_task_ids = {str(item.get("task_id")) for item in tasks if item.get("task_id")}
    for task in tasks:
        if not task.get("task_id"):
            task["task_id"] = _allocate_id("TASK", used_task_ids)
        task.setdefault("phase_id", "")
        task.setdefault("title", "Untitled task")
        task.setdefault("action", "")
        for key in (
            "requirement_ids",
            "design_basis",
            "target_artifacts",
            "dependencies",
            "risks",
            "acceptance_criteria",
            "verification_steps",
        ):
            _fill_list(task, key)
        task.setdefault("parallel_group", None)
        task.setdefault("status", "planned")
        task.setdefault("blocker_reason", None)
        task.setdefault("pause_reason", None)
        task.setdefault("skip_reason", None)
        task.setdefault("skip_authority", None)
        raw_evidence = task.setdefault("evidence", [])
        if isinstance(raw_evidence, list):
            definition_digest = target_definition_digest(task, "task")
            task["evidence"] = [
                _normalize_evidence(item, evidence_ids, now, definition_digest)
                if isinstance(item, dict)
                else item
                for item in raw_evidence
            ]
        task.setdefault("completed_at", None)

    task_ids_by_phase: dict[str, list[str]] = {}
    for task in tasks:
        task_ids_by_phase.setdefault(str(task.get("phase_id", "")), []).append(
            str(task.get("task_id", ""))
        )
    for phase in phases:
        if not phase.get("task_ids"):
            phase["task_ids"] = sorted(task_ids_by_phase.get(str(phase["phase_id"]), []))

    coverage = copy.deepcopy(payload.get("coverage", {}))
    ensure_object(coverage, "coverage")
    if "source_to_requirement" not in coverage:
        coverage["source_to_requirement"] = []
        for source in sources:
            source_id = source["source_id"]
            linked = sorted(
                requirement["requirement_id"]
                for requirement in requirements
                if source_id in requirement["source_ids"]
            )
            coverage["source_to_requirement"].append(
                {"source_id": source_id, "requirement_ids": linked, "disposition": None}
            )
    if "requirement_to_task" not in coverage:
        coverage["requirement_to_task"] = []
        for requirement in requirements:
            requirement_id = requirement["requirement_id"]
            linked = sorted(
                task["task_id"]
                for task in tasks
                if requirement_id in task["requirement_ids"]
            )
            coverage["requirement_to_task"].append(
                {
                    "requirement_id": requirement_id,
                    "task_ids": linked,
                    "disposition": copy.deepcopy(requirement.get("disposition")),
                }
            )

    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "plan_id": "",
        "title": title_value.strip(),
        "slug": slug_value,
        "created_at": now,
        "updated_at": now,
        "status": "draft",
        "revision": 1,
        "status_reason": str(payload.get("status_reason") or "Initial draft created.").strip(),
        "project": project,
        "objective": objective,
        "scope": scope,
        "sources": sources,
        "requirements": requirements,
        "decisions": decisions,
        "open_questions": questions,
        "assumptions": assumptions,
        "phases": phases,
        "tasks": tasks,
        "coverage": coverage,
        "validation": {
            "checked_revision": 1,
            "checked_at": now,
            "status": "not_exercised",
            "findings": [],
        },
        "initial_record_ids": [],
        "history": [],
    }
    result["initial_record_ids"] = stable_record_ids(result)
    return result


def _schema_error(
    errors: list[dict[str, Any]], code: str, message: str, *targets: str
) -> None:
    errors.append(
        {
            "code": code,
            "message": message,
            "targets": list(dict.fromkeys(target for target in targets if target)),
        }
    )


def _check_exact_keys(
    value: Any,
    required: set[str],
    path: str,
    errors: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        _schema_error(errors, "wrong_type", f"{path} must be an object.", path)
        return None
    missing = sorted(required - set(value))
    unknown = sorted(set(value) - required)
    if missing:
        _schema_error(
            errors,
            "missing_field",
            f"{path} is missing required fields: {', '.join(missing)}.",
            path,
        )
    if unknown:
        _schema_error(
            errors,
            "unknown_field",
            f"{path} has {len(unknown)} unsupported field(s).",
            path,
        )
    return value


def _check_string(
    value: Any,
    path: str,
    errors: list[dict[str, Any]],
    *,
    nonblank: bool = True,
    nullable: bool = False,
    maximum: int = MAX_SHORT_TEXT,
) -> bool:
    if value is None and nullable:
        return True
    if not isinstance(value, str):
        _schema_error(errors, "wrong_type", f"{path} must be a string.", path)
        return False
    if nonblank and not value.strip():
        _schema_error(errors, "blank_value", f"{path} must not be blank.", path)
        return False
    if len(value) > maximum:
        _schema_error(
            errors,
            "size_limit",
            f"{path} exceeds {maximum} characters.",
            path,
        )
        return False
    return True


def _check_timestamp(
    value: Any,
    path: str,
    errors: list[dict[str, Any]],
    *,
    nullable: bool = False,
) -> dt.datetime | None:
    if value is None and nullable:
        return None
    try:
        return parse_timestamp(value, path)
    except ValueError as exc:
        _schema_error(errors, "invalid_timestamp", str(exc), path)
        return None


def _check_observation_boundary(
    value: dt.datetime | None,
    latest: dt.datetime | None,
    path: str,
    errors: list[dict[str, Any]],
) -> None:
    if value is not None and latest is not None and value > latest:
        _schema_error(
            errors,
            "future_observation",
            f"{path} is later than the canonical observation boundary.",
            path,
        )


def _check_enum(
    value: Any,
    allowed: set[str],
    path: str,
    errors: list[dict[str, Any]],
) -> bool:
    if not isinstance(value, str) or value not in allowed:
        _schema_error(
            errors,
            "invalid_enum",
            f"{path} must be one of: {', '.join(sorted(allowed))}.",
            path,
        )
        return False
    return True


def _is_enum_value(value: Any, allowed: set[str]) -> bool:
    """Safely test a schema value without hashing malformed containers."""
    return isinstance(value, str) and value in allowed


def _check_string_list(
    value: Any,
    path: str,
    errors: list[dict[str, Any]],
    *,
    minimum: int = 0,
    unique: bool = False,
    maximum_text: int = MAX_SHORT_TEXT,
) -> list[str] | None:
    if not isinstance(value, list):
        _schema_error(errors, "wrong_type", f"{path} must be an array.", path)
        return None
    if len(value) < minimum:
        _schema_error(
            errors,
            "missing_item",
            f"{path} must contain at least {minimum} item(s).",
            path,
        )
    if len(value) > MAX_COLLECTION_ITEMS:
        _schema_error(errors, "size_limit", f"{path} has too many items.", path)
    result: list[str] = []
    for index, item in enumerate(value):
        item_path = f"{path}[{index}]"
        if _check_string(item, item_path, errors, maximum=maximum_text):
            result.append(item)
    if unique and len(result) != len(set(result)):
        _schema_error(errors, "duplicate_reference", f"{path} contains duplicates.", path)
    return result


def _check_id(
    value: Any,
    pattern: re.Pattern[str],
    path: str,
    errors: list[dict[str, Any]],
) -> bool:
    if not isinstance(value, str) or len(value) > MAX_ID_CHARS or not pattern.fullmatch(value):
        _schema_error(errors, "invalid_identifier", f"{path} is not a valid identifier.", path)
        return False
    if any(
        pattern is candidate
        for candidate in (
            PHASE_ID_RE,
            TASK_ID_RE,
            SOURCE_ID_RE,
            DECISION_ID_RE,
            QUESTION_ID_RE,
            ASSUMPTION_ID_RE,
            EVIDENCE_ID_RE,
        )
    ):
        match = pattern.fullmatch(value)
        assert match is not None
        number = int(match.group(1))
        if number < 1 or match.group(1) != f"{number:03d}":
            _schema_error(
                errors,
                "noncanonical_identifier",
                f"{path} must use canonical positive numeric formatting.",
                path,
            )
            return False
    return True


def _requirement_id_uses_reserved_namespace(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    if (
        PLAN_ID_RE.fullmatch(value)
        or RESERVED_ACTION_NAMESPACE_RE.fullmatch(value)
        or FINDING_ID_RE.fullmatch(value)
    ):
        return True
    return any(
        pattern.fullmatch(value)
        for pattern in (
            PHASE_ID_RE,
            TASK_ID_RE,
            SOURCE_ID_RE,
            DECISION_ID_RE,
            QUESTION_ID_RE,
            ASSUMPTION_ID_RE,
            EVIDENCE_ID_RE,
        )
    )


def _check_unique_record_ids(
    records: Any,
    key: str,
    path: str,
    errors: list[dict[str, Any]],
) -> set[str]:
    if not isinstance(records, list):
        _schema_error(errors, "wrong_type", f"{path} must be an array.", path)
        return set()
    if len(records) > MAX_COLLECTION_ITEMS:
        _schema_error(errors, "size_limit", f"{path} has too many records.", path)
    seen: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            _schema_error(
                errors,
                "wrong_type",
                f"{path}[{index}] must be an object.",
                f"{path}[{index}]",
            )
            continue
        identifier = record.get(key)
        if isinstance(identifier, str):
            if identifier in seen:
                _schema_error(
                    errors,
                    "duplicate_identifier",
                    f"{path} repeats {identifier}.",
                    identifier,
                )
            seen.add(identifier)
    return seen


def _check_disposition(
    value: Any,
    path: str,
    errors: list[dict[str, Any]],
    *,
    nullable: bool = True,
) -> None:
    if value is None and nullable:
        return
    record = _check_exact_keys(
        value,
        {"kind", "reason", "authority_basis"},
        path,
        errors,
    )
    if record is None:
        return
    _check_enum(record.get("kind"), DISPOSITION_KINDS, f"{path}.kind", errors)
    _check_string(record.get("reason"), f"{path}.reason", errors)
    _check_string(record.get("authority_basis"), f"{path}.authority_basis", errors)


def _check_evidence_record(
    record: Any,
    path: str,
    errors: list[dict[str, Any]],
    evidence_ids: set[str],
    *,
    earliest: dt.datetime | None = None,
    latest: dt.datetime | None = None,
) -> None:
    value = _check_exact_keys(
        record,
        {
            "evidence_id",
            "timestamp",
            "evidence_type",
            "result_status",
            "description",
            "locator_or_command",
            "observed_result",
            "verification_level",
            "observation_source",
            "target_digest",
        },
        path,
        errors,
    )
    if value is None:
        return
    evidence_id = value.get("evidence_id")
    if _check_id(evidence_id, EVIDENCE_ID_RE, f"{path}.evidence_id", errors):
        if evidence_id in evidence_ids:
            _schema_error(
                errors,
                "duplicate_identifier",
                f"Evidence identifier {evidence_id} is reused.",
                str(evidence_id),
            )
        evidence_ids.add(str(evidence_id))
    evidence_time = _check_timestamp(value.get("timestamp"), f"{path}.timestamp", errors)
    if evidence_time is not None and earliest is not None and evidence_time < earliest:
        _schema_error(
            errors,
            "evidence_timestamp_order",
            f"{path}.timestamp predates the target record.",
            str(value.get("evidence_id")),
        )
    if evidence_time is not None and latest is not None and evidence_time > latest:
        _schema_error(
            errors,
            "future_observation",
            f"{path}.timestamp is later than the canonical observation boundary.",
            str(value.get("evidence_id")),
        )
    _check_enum(value.get("evidence_type"), EVIDENCE_TYPES, f"{path}.evidence_type", errors)
    _check_enum(
        value.get("result_status"),
        EVIDENCE_RESULT_STATUSES,
        f"{path}.result_status",
        errors,
    )
    _check_string(
        value.get("description"),
        f"{path}.description",
        errors,
        maximum=MAX_SHORT_TEXT,
    )
    _check_string(
        value.get("locator_or_command"),
        f"{path}.locator_or_command",
        errors,
        nullable=True,
        maximum=MAX_LOCATOR_CHARS,
    )
    _check_string(
        value.get("observed_result"),
        f"{path}.observed_result",
        errors,
        maximum=MAX_SHORT_TEXT,
    )
    _check_enum(
        value.get("verification_level"),
        VERIFICATION_LEVELS,
        f"{path}.verification_level",
        errors,
    )
    _check_enum(
        value.get("observation_source"),
        OBSERVATION_SOURCES,
        f"{path}.observation_source",
        errors,
    )
    target_digest = value.get("target_digest")
    if not isinstance(target_digest, str) or not re.fullmatch(
        r"sha256:[a-f0-9]{64}", target_digest
    ):
        _schema_error(
            errors,
            "invalid_digest",
            f"{path}.target_digest must bind evidence to one target definition.",
            str(value.get("evidence_id")),
        )
    if value.get("evidence_type") == "planned_check" and value.get("verification_level") != "planned":
        _schema_error(
            errors,
            "evidence_semantics",
            f"{path} planned_check evidence must use verification level planned.",
            str(value.get("evidence_id")),
        )
    if value.get("evidence_type") == "planned_check" and value.get("result_status") != "planned":
        _schema_error(
            errors,
            "evidence_semantics",
            f"{path} planned_check evidence must use result status planned.",
            str(value.get("evidence_id")),
        )
    if value.get("result_status") == "planned" and value.get(
        "evidence_type"
    ) != "planned_check":
        _schema_error(
            errors,
            "evidence_semantics",
            f"{path} result status planned is reserved for planned_check evidence.",
            str(value.get("evidence_id")),
        )
    if value.get("evidence_type") == "not_exercised" and value.get("verification_level") != "not_exercised":
        _schema_error(
            errors,
            "evidence_semantics",
            f"{path} not_exercised evidence must use verification level not_exercised.",
            str(value.get("evidence_id")),
        )
    if value.get("evidence_type") == "not_exercised" and value.get("result_status") != "not_exercised":
        _schema_error(
            errors,
            "evidence_semantics",
            f"{path} not_exercised evidence must use result status not_exercised.",
            str(value.get("evidence_id")),
        )
    if value.get("result_status") == "not_exercised" and value.get(
        "evidence_type"
    ) != "not_exercised":
        _schema_error(
            errors,
            "evidence_semantics",
            f"{path} result status not_exercised requires not_exercised evidence type.",
            str(value.get("evidence_id")),
        )
    if value.get("verification_level") == "not_exercised" and (
        value.get("evidence_type") != "not_exercised"
        or value.get("result_status") != "not_exercised"
    ):
        _schema_error(
            errors,
            "evidence_semantics",
            f"{path} verification level not_exercised requires matching evidence type and result status.",
            str(value.get("evidence_id")),
        )
    if value.get("verification_level") == "planned" and value.get(
        "result_status"
    ) != "planned":
        _schema_error(
            errors,
            "evidence_semantics",
            f"{path} verification level planned requires result status planned.",
            str(value.get("evidence_id")),
        )
    passing_levels = {
        "static_checks_passed",
        "targeted_tests_passed",
        "broader_suite_passed",
        "end_to_end_verified",
    }
    if _is_enum_value(value.get("verification_level"), passing_levels) and value.get("result_status") != "passed":
        _schema_error(
            errors,
            "evidence_semantics",
            f"{path} a passing verification level requires result status passed.",
            str(value.get("evidence_id")),
        )
    if value.get("result_status") == "passed" and _is_enum_value(
        value.get("verification_level"), {"planned", "not_exercised"}
    ):
        _schema_error(
            errors,
            "evidence_semantics",
            f"{path} passed evidence requires an observed verification level.",
            str(value.get("evidence_id")),
        )
    contradiction_text = (
        str(value.get("description", ""))
        + "\n"
        + str(value.get("observed_result", ""))
    )
    count_patterns = (
        r"(?im)\b(\d+)\s+failed\b",
        r"(?im)\b(\d+)\s+errors?\b",
        r"(?im)\bfailures?\s*=\s*(\d+)\b",
        r"(?im)\berrors?\s*=\s*(\d+)\b",
    )
    positive_failure_count = any(
        int(match.group(1)) > 0
        for pattern in count_patterns
        for match in re.finditer(pattern, contradiction_text)
    )
    obvious_failure = re.search(
        r"(?im)(?:"
        r"\b(?:assertionerror|traceback)\b|"
        r"\b(?:exit(?:ed)?|return(?:ed)?)\s+(?:status|code)?\s*[1-9]\d*\b|"
        r"^\s*(?:FAIL|ERROR)\b|"
        r"^\s*FAILED\b|"
        r"\bFAILED\s*\(|"
        r"\b(?:test|check|command|workflow|suite|build|execution)\s+"
        r"(?:was\s+|is\s+)?(?:failed|blocked|partial|incomplete)\b|"
        r"\bdid not (?:pass|succeed|complete)\b"
        r")",
        contradiction_text,
    )
    if value.get("result_status") == "passed" and (
        obvious_failure or positive_failure_count
    ):
        _schema_error(
            errors,
            "evidence_result_contradiction",
            f"{path} is classified passed but contains a standard failure indicator.",
            str(value.get("evidence_id")),
        )
    if value.get("evidence_type") == "user_report" and value.get("observation_source") != "user":
        _schema_error(
            errors,
            "evidence_semantics",
            f"{path} user_report evidence must retain user observation source.",
            str(value.get("evidence_id")),
        )
    if value.get("evidence_type") == "external_report" and value.get("observation_source") != "external":
        _schema_error(
            errors,
            "evidence_semantics",
            f"{path} external_report evidence must retain external observation source.",
            str(value.get("evidence_id")),
        )
    if _is_enum_value(
        value.get("evidence_type"), {"inspection", "command", "test", "runtime"}
    ) and not _is_enum_value(value.get("observation_source"), {"agent", "tool"}):
        _schema_error(
            errors,
            "evidence_semantics",
            f"{path} observed agent/tool evidence cannot use a plan, user, or external source label.",
            str(value.get("evidence_id")),
        )
    if _is_enum_value(
        value.get("evidence_type"), {"inspection", "command", "test", "runtime"}
    ) and (
        not isinstance(value.get("locator_or_command"), str)
        or not value.get("locator_or_command", "").strip()
    ):
        _schema_error(
            errors,
            "evidence_locator_missing",
            f"{path} observed agent/tool evidence requires a reviewable locator or command.",
            str(value.get("evidence_id")),
        )


def meaningful_evidence(records: Any) -> list[dict[str, Any]]:
    if not isinstance(records, list):
        return []
    useful: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        description = str(record.get("description", "")).strip()
        observed = str(record.get("observed_result", "")).strip()
        level = record.get("verification_level")
        if (
            len(description) >= 4
            and len(observed) >= 4
            and not is_meaningless_evidence_text(description)
            and not is_meaningless_evidence_text(observed)
            and level
            in {
                "inspected_only",
                "static_checks_passed",
                "targeted_tests_passed",
                "broader_suite_passed",
                "runtime_observed",
                "end_to_end_verified",
            }
            and (
                not _is_enum_value(
                    record.get("evidence_type"),
                    {"inspection", "command", "test", "runtime"},
                )
                or (
                    isinstance(record.get("locator_or_command"), str)
                    and record.get("locator_or_command", "").strip()
                )
            )
        ):
            useful.append(record)
    return useful


def completion_evidence(
    records: Any, target_digest: str | None = None
) -> list[dict[str, Any]]:
    return [
        record
        for record in meaningful_evidence(records)
        if not _is_enum_value(
            record.get("evidence_type"), {"planned_check", "not_exercised"}
        )
        and record.get("result_status") == "passed"
        and record.get("observation_source") != "plan"
        and (target_digest is None or record.get("target_digest") == target_digest)
    ]


def _normalized_evidence_text(record: Mapping[str, Any]) -> str:
    return " ".join(
        (
            str(record.get("description", ""))
            + "\n"
            + str(record.get("observed_result", ""))
        )
        .casefold()
        .split()
    )


def missing_criterion_evidence(
    criteria: Sequence[Any], records: Any, target_digest: str | None = None
) -> list[str]:
    """Return acceptance criteria not explicitly named by passing evidence."""
    candidates = [
        _normalized_evidence_text(record)
        for record in completion_evidence(records, target_digest)
    ]
    missing: list[str] = []
    for criterion in criteria:
        text = str(criterion).strip()
        normalized = " ".join(text.casefold().split())
        if not normalized or not any(normalized in candidate for candidate in candidates):
            missing.append(text)
    return missing


def missing_verification_reports(
    steps: Sequence[Any], records: Any, target_digest: str | None = None
) -> list[str]:
    """Return planned verification steps with no explicit result classification."""
    candidates: list[str] = []
    if isinstance(records, list):
        for record in records:
            if not isinstance(record, dict):
                continue
            if record.get("evidence_type") == "planned_check" or record.get(
                "result_status"
            ) == "planned":
                continue
            if target_digest is not None and record.get("target_digest") != target_digest:
                continue
            description = str(record.get("description", "")).strip()
            observed = str(record.get("observed_result", "")).strip()
            if (
                len(description) >= 4
                and len(observed) >= 4
                and not is_meaningless_evidence_text(description)
                and not is_meaningless_evidence_text(observed)
            ):
                candidates.append(_normalized_evidence_text(record))
    missing: list[str] = []
    for step in steps:
        text = str(step).strip()
        normalized = " ".join(text.casefold().split())
        if not normalized or not any(normalized in candidate for candidate in candidates):
            missing.append(text)
    return missing


def highest_verification_level(plan: Mapping[str, Any]) -> str:
    ordered = [
        "planned",
        "not_exercised",
        "inspected_only",
        "static_checks_passed",
        "targeted_tests_passed",
        "broader_suite_passed",
        "runtime_observed",
        "end_to_end_verified",
    ]
    rank = {value: index for index, value in enumerate(ordered)}
    observed = ["not_exercised"]
    digest_context = build_target_digest_context(plan)
    for collection in ("requirements", "tasks"):
        target_kind = "requirement" if collection == "requirements" else "task"
        for target in plan.get(collection, []):
            if not isinstance(target, dict):
                continue
            current_digest = target_definition_digest(
                target, target_kind, plan, digest_context
            )
            for evidence in completion_evidence(
                target.get("evidence", []), current_digest
            ):
                if isinstance(evidence.get("verification_level"), str) and evidence.get(
                    "verification_level"
                ) in rank:
                    observed.append(str(evidence["verification_level"]))
    return max(observed, key=lambda value: rank[value])


def skipped_task_is_disposed(task: Mapping[str, Any], plan: Mapping[str, Any] | None) -> bool:
    if task.get("status") != "skipped":
        return True
    if not task.get("skip_reason") or not task.get("skip_authority"):
        return False
    if plan is None:
        return False
    requirements = {
        item.get("requirement_id"): item
        for item in plan.get("requirements", [])
        if isinstance(item, dict)
    }
    edges = {
        item.get("requirement_id"): item
        for item in plan.get("coverage", {}).get("requirement_to_task", [])
        if isinstance(item, dict)
    }
    for requirement_id in list_or_empty(task.get("requirement_ids")):
        requirement = requirements.get(requirement_id, {})
        edge = edges.get(requirement_id, {})
        if (
            requirement.get("status") != "dispositioned"
            or requirement.get("disposition") is None
            or edge.get("disposition") is None
        ):
            return False
    return True


def derive_phase_status(
    tasks: Sequence[Mapping[str, Any]], plan: Mapping[str, Any] | None = None
) -> str:
    if not tasks:
        return "planned"
    statuses = [str(task.get("status")) for task in tasks]
    if all(status in {"completed", "skipped"} for status in statuses) and all(
        skipped_task_is_disposed(task, plan) for task in tasks
    ):
        return "completed"
    unfinished_tasks = [
        task
        for task in tasks
        if not _is_enum_value(task.get("status"), {"completed", "skipped"})
    ]
    unfinished = [str(task.get("status")) for task in unfinished_tasks]
    if unfinished and all(status == "planned" for status in statuses):
        return "planned"
    status_records = (
        plan.get("tasks", []) if plan is not None else tasks
    )
    task_status = {
        str(task.get("task_id")): str(task.get("status"))
        for task in status_records
        if isinstance(task, dict)
    }
    ready_tasks = [
        task
        for task in unfinished_tasks
        if all(
            task_status.get(str(dependency)) in {"completed", "skipped"}
            for dependency in list_or_empty(task.get("dependencies"))
        )
    ]
    if any(
        not _is_enum_value(task.get("status"), {"blocked", "paused"})
        for task in ready_tasks
    ):
        return "in_progress"
    if any(task.get("status") == "blocked" for task in ready_tasks):
        return "blocked"
    if ready_tasks and all(task.get("status") == "paused" for task in ready_tasks):
        return "paused"
    if "blocked" in unfinished:
        return "blocked"
    if "paused" in unfinished:
        return "paused"
    return "blocked"


def _graph_cycles(nodes: Iterable[str], edges: Mapping[str, Sequence[str]]) -> list[list[str]]:
    state: dict[str, int] = {}
    cycles: set[tuple[str, ...]] = set()
    for start in sorted(nodes):
        if state.get(start, 0) != 0:
            continue
        path: list[str] = [start]
        positions: dict[str, int] = {start: 0}
        state[start] = 1
        work: list[tuple[str, int, list[str]]] = [
            (start, 0, [item for item in sorted(edges.get(start, [])) if item in edges])
        ]
        while work:
            node, index, dependencies = work[-1]
            if index >= len(dependencies):
                work.pop()
                state[node] = 2
                positions.pop(node, None)
                if path and path[-1] == node:
                    path.pop()
                continue
            dependency = dependencies[index]
            work[-1] = (node, index + 1, dependencies)
            marker = state.get(dependency, 0)
            if marker == 0:
                state[dependency] = 1
                positions[dependency] = len(path)
                path.append(dependency)
                work.append(
                    (
                        dependency,
                        0,
                        [
                            item
                            for item in sorted(edges.get(dependency, []))
                            if item in edges
                        ],
                    )
                )
            elif marker == 1 and dependency in positions:
                body = path[positions[dependency] :]
                if body:
                    # IDs are unique, so the lexicographically minimal
                    # rotation starts at the one minimal ID.  Rotate once
                    # instead of materializing O(k^2) full rotations.
                    offset = body.index(min(body))
                    cycles.add(tuple(body[offset:] + body[:offset]))
    return [list(cycle) + [cycle[0]] for cycle in sorted(cycles) if cycle]


def validate_plan_structure(
    plan: Any,
    context: Context,
    *,
    directory_name: str | None = None,
) -> list[dict[str, Any]]:
    """Return deterministic schema and invariant errors for canonical state."""
    errors: list[dict[str, Any]] = []
    if not isinstance(plan, dict):
        return [{"code": "wrong_type", "message": "plan.json must contain an object.", "targets": ["$"]}]
    try:
        _validate_value_bounds(plan)
        guard_prohibited_content(plan)
    except AppError as exc:
        return [{"code": "prohibited_content", "message": exc.message, "targets": []}]
    root = _check_exact_keys(plan, TOP_LEVEL_FIELDS, "$", errors)
    if root is None:
        return errors
    digest_context = build_target_digest_context(plan)

    version = plan.get("schema_version")
    if isinstance(version, bool) or not isinstance(version, int) or version != SCHEMA_VERSION:
        _schema_error(
            errors,
            "unsupported_schema",
            f"schema_version must be {SCHEMA_VERSION}.",
            "schema_version",
        )
    plan_id = plan.get("plan_id")
    plan_match = PLAN_ID_RE.fullmatch(plan_id) if isinstance(plan_id, str) else None
    if not plan_match:
        _schema_error(errors, "invalid_identifier", "plan_id is invalid.", "plan_id")
    _check_string(plan.get("title"), "title", errors, maximum=MAX_TITLE_CHARS)
    slug = plan.get("slug")
    if (
        not isinstance(slug, str)
        or len(slug) > MAX_SLUG_CHARS
        or not SAFE_SLUG_RE.fullmatch(slug)
    ):
        _schema_error(errors, "invalid_slug", "slug is not a safe bounded ASCII slug.", "slug")
    created = _check_timestamp(plan.get("created_at"), "created_at", errors)
    updated = _check_timestamp(plan.get("updated_at"), "updated_at", errors)
    if created and updated and updated < created:
        _schema_error(errors, "timestamp_order", "updated_at predates created_at.", "updated_at")
    if plan_match and created and plan_match.group(1) != created.strftime("%Y%m%d"):
        _schema_error(
            errors,
            "identity_date_mismatch",
            "plan_id date does not match created_at.",
            "plan_id",
            "created_at",
        )
    _check_enum(plan.get("status"), PLAN_STATES, "status", errors)
    revision = plan.get("revision")
    if (
        isinstance(revision, bool)
        or not isinstance(revision, int)
        or revision < 1
        or revision > MAX_COLLECTION_ITEMS
    ):
        _schema_error(
            errors,
            "invalid_revision",
            f"revision must be an integer from 1 through {MAX_COLLECTION_ITEMS}.",
            "revision",
        )
    _check_string(plan.get("status_reason"), "status_reason", errors, maximum=MAX_SHORT_TEXT)

    project = _check_exact_keys(
        plan.get("project"),
        {
            "root_hint",
            "inspected_at",
            "guidance",
            "baseline_facts",
            "constraints",
            "preserved_paths",
            "evidence_gaps",
        },
        "project",
        errors,
    )
    if project is not None:
        if _check_string(
            project.get("root_hint"),
            "project.root_hint",
            errors,
            maximum=MAX_LOCATOR_CHARS,
        ) and project.get("root_hint") != str(context.project_root):
            _schema_error(
                errors,
                "project_root_mismatch",
                "project.root_hint does not match the explicit project root.",
                "project.root_hint",
            )
        project_inspected = _check_timestamp(
            project.get("inspected_at"), "project.inspected_at", errors
        )
        _check_observation_boundary(
            project_inspected, updated, "project.inspected_at", errors
        )
        guidance = project.get("guidance")
        if not isinstance(guidance, list):
            _schema_error(errors, "wrong_type", "project.guidance must be an array.", "project.guidance")
        else:
            for index, item in enumerate(guidance):
                path = f"project.guidance[{index}]"
                record = _check_exact_keys(
                    item,
                    {"path", "observed_at", "digest", "summary"},
                    path,
                    errors,
                )
                if record:
                    _check_string(record.get("path"), f"{path}.path", errors, maximum=MAX_LOCATOR_CHARS)
                    observed_at = _check_timestamp(
                        record.get("observed_at"), f"{path}.observed_at", errors
                    )
                    _check_observation_boundary(
                        observed_at, updated, f"{path}.observed_at", errors
                    )
                    _check_string(record.get("digest"), f"{path}.digest", errors, nullable=True, maximum=256)
                    _check_string(record.get("summary"), f"{path}.summary", errors)
        facts = project.get("baseline_facts")
        if not isinstance(facts, list):
            _schema_error(errors, "wrong_type", "project.baseline_facts must be an array.", "project.baseline_facts")
        else:
            for index, item in enumerate(facts):
                path = f"project.baseline_facts[{index}]"
                record = _check_exact_keys(
                    item,
                    {"fact", "evidence_locator", "observed_at"},
                    path,
                    errors,
                )
                if record:
                    _check_string(record.get("fact"), f"{path}.fact", errors)
                    _check_string(
                        record.get("evidence_locator"),
                        f"{path}.evidence_locator",
                        errors,
                        maximum=MAX_LOCATOR_CHARS,
                    )
                    observed_at = _check_timestamp(
                        record.get("observed_at"), f"{path}.observed_at", errors
                    )
                    _check_observation_boundary(
                        observed_at, updated, f"{path}.observed_at", errors
                    )
        for key in ("constraints", "preserved_paths", "evidence_gaps"):
            _check_string_list(project.get(key), f"project.{key}", errors, unique=True)

    objective = _check_exact_keys(
        plan.get("objective"),
        {"summary", "user_value", "success_outcomes"},
        "objective",
        errors,
    )
    if objective:
        _check_string(objective.get("summary"), "objective.summary", errors)
        _check_string(
            objective.get("user_value"),
            "objective.user_value",
            errors,
        )
        _check_string_list(
            objective.get("success_outcomes"),
            "objective.success_outcomes",
            errors,
            minimum=1,
            unique=True,
        )

    scope = _check_exact_keys(
        plan.get("scope"),
        {"in_scope", "out_of_scope", "execution_authority"},
        "scope",
        errors,
    )
    if scope:
        _check_string_list(scope.get("in_scope"), "scope.in_scope", errors, unique=True)
        _check_string_list(scope.get("out_of_scope"), "scope.out_of_scope", errors, unique=True)
        if _check_string(
            scope.get("execution_authority"), "scope.execution_authority", errors
        ):
            authority_text = str(scope.get("execution_authority")).casefold()
            if "authoriz" not in authority_text or not any(
                marker in authority_text
                for marker in ("does not", "do not", "not authoriz", "never authoriz", "no authority")
            ):
                _schema_error(
                    errors,
                    "authority_boundary_missing",
                    "scope.execution_authority must state that plan state does not authorize execution or separately governed action.",
                    "scope.execution_authority",
                )

    source_ids = _check_unique_record_ids(plan.get("sources"), "source_id", "sources", errors)
    requirement_ids = _check_unique_record_ids(
        plan.get("requirements"), "requirement_id", "requirements", errors
    )
    decision_ids = _check_unique_record_ids(plan.get("decisions"), "decision_id", "decisions", errors)
    question_ids = _check_unique_record_ids(
        plan.get("open_questions"), "question_id", "open_questions", errors
    )
    assumption_ids = _check_unique_record_ids(
        plan.get("assumptions"), "assumption_id", "assumptions", errors
    )
    phase_ids = _check_unique_record_ids(plan.get("phases"), "phase_id", "phases", errors)
    task_ids = _check_unique_record_ids(plan.get("tasks"), "task_id", "tasks", errors)
    evidence_ids: set[str] = set()
    introduction_times: dict[str, dt.datetime] = {}
    for history_item in list_or_empty(plan.get("history")):
        if not isinstance(history_item, Mapping):
            continue
        try:
            history_time = parse_timestamp(history_item.get("timestamp"), "history timestamp")
        except ValueError:
            continue
        for affected_id in list_or_empty(history_item.get("affected_ids")):
            if isinstance(affected_id, str):
                introduction_times.setdefault(affected_id, history_time)

    sources = plan.get("sources") if isinstance(plan.get("sources"), list) else []
    sources_by_id = {
        str(item.get("source_id")): item
        for item in sources
        if isinstance(item, dict) and isinstance(item.get("source_id"), str)
    }
    for index, item in enumerate(sources):
        path = f"sources[{index}]"
        record = _check_exact_keys(
            item,
            {
                "source_id",
                "kind",
                "locator",
                "title",
                "accessed_at",
                "digest",
                "facts_used",
                "access_limitations",
                "provenance_mode",
                "inspection_method",
                "external_id",
            },
            path,
            errors,
        )
        if not record:
            continue
        _check_id(record.get("source_id"), SOURCE_ID_RE, f"{path}.source_id", errors)
        kind_valid = _check_enum(
            record.get("kind"), SOURCE_KINDS, f"{path}.kind", errors
        )
        _check_string(
            record.get("locator"),
            f"{path}.locator",
            errors,
            nullable=True,
            maximum=MAX_LOCATOR_CHARS,
        )
        if kind_valid and _is_enum_value(
            record.get("kind"), {"file", "trd", "prd", "url"}
        ) and record.get("locator") is None:
            _schema_error(errors, "missing_locator", f"{path}.locator is required for this source kind.", path)
        _check_string(record.get("title"), f"{path}.title", errors, maximum=MAX_TITLE_CHARS)
        accessed_at = _check_timestamp(
            record.get("accessed_at"), f"{path}.accessed_at", errors
        )
        _check_observation_boundary(
            accessed_at, updated, f"{path}.accessed_at", errors
        )
        if record.get("digest") is not None:
            digest = record.get("digest")
            if not isinstance(digest, str) or not re.fullmatch(r"sha256:[a-f0-9]{64}", digest):
                _schema_error(errors, "invalid_digest", f"{path}.digest is invalid.", path)
        _check_string_list(record.get("facts_used"), f"{path}.facts_used", errors)
        _check_string_list(record.get("access_limitations"), f"{path}.access_limitations", errors)
        if not record.get("facts_used") and not record.get("access_limitations"):
            _schema_error(
                errors,
                "empty_source_result",
                f"{path} must record facts used or an exact access limitation.",
                str(record.get("source_id")),
            )
        provenance_valid = _check_enum(
            record.get("provenance_mode"),
            PROVENANCE_MODES,
            f"{path}.provenance_mode",
            errors,
        )
        method = record.get("inspection_method")
        method_valid = True
        if method is not None:
            method_valid = _check_enum(
                method, INSPECTION_METHODS, f"{path}.inspection_method", errors
            )
        if record.get("provenance_mode") == "agent_inspected" and method is None:
            _schema_error(
                errors,
                "missing_inspection_method",
                f"{path}.inspection_method is required for agent-inspected facts or limitations.",
                str(record.get("source_id")),
            )
        if record.get("provenance_mode") == "user_supplied" and method is not None:
            _schema_error(
                errors,
                "unexpected_inspection_method",
                f"{path}.inspection_method must be null for user-supplied source content.",
                str(record.get("source_id")),
            )
        if provenance_valid and record.get("provenance_mode") == "agent_inspected":
            kind = record.get("kind")
            if kind_valid and kind == "url" and method != "browser_tool":
                _schema_error(
                    errors,
                    "inspection_method_mismatch",
                    f"{path} agent-inspected URL sources require browser_tool.",
                    str(record.get("source_id")),
                )
            elif kind_valid and kind in {"file", "trd", "prd"} and (
                not method_valid or not _is_enum_value(method, LOCAL_INSPECTION_METHODS)
            ):
                _schema_error(
                    errors,
                    "inspection_method_mismatch",
                    f"{path} agent-inspected local sources require a local file inspection method.",
                    str(record.get("source_id")),
                )
            elif kind_valid and kind not in {"file", "trd", "prd", "url"}:
                _schema_error(
                    errors,
                    "unsupported_agent_source_kind",
                    f"{path} kind cannot support an agent-inspected provenance claim.",
                    str(record.get("source_id")),
                )
        _check_string(
            record.get("external_id"),
            f"{path}.external_id",
            errors,
            nullable=True,
            maximum=MAX_ID_CHARS,
        )

    requirements = (
        plan.get("requirements") if isinstance(plan.get("requirements"), list) else []
    )
    requirement_edges: dict[str, list[str]] = {}
    for index, item in enumerate(requirements):
        path = f"requirements[{index}]"
        record = _check_exact_keys(
            item,
            {
                "requirement_id",
                "title",
                "outcome",
                "intent",
                "source_ids",
                "acceptance_criteria",
                "dependencies",
                "negative_requirements",
                "status",
                "disposition",
                "evidence",
            },
            path,
            errors,
        )
        if not record:
            continue
        requirement_id = record.get("requirement_id")
        requirement_id_valid = _check_id(
            requirement_id,
            REQUIREMENT_ID_RE,
            f"{path}.requirement_id",
            errors,
        )
        if requirement_id_valid and _requirement_id_uses_reserved_namespace(
            requirement_id
        ):
            _schema_error(
                errors,
                "reserved_identifier_namespace",
                f"{path}.requirement_id uses a reserved plan-local identifier namespace.",
                str(requirement_id),
            )
        _check_string(record.get("title"), f"{path}.title", errors, maximum=MAX_TITLE_CHARS)
        _check_string(record.get("outcome"), f"{path}.outcome", errors)
        _check_string(record.get("intent"), f"{path}.intent", errors)
        refs = _check_string_list(
            record.get("source_ids"),
            f"{path}.source_ids",
            errors,
            minimum=1,
            unique=True,
            maximum_text=MAX_ID_CHARS,
        ) or []
        for ref in refs:
            if ref not in source_ids:
                _schema_error(errors, "missing_reference", f"{requirement_id} references missing source {ref}.", str(requirement_id), ref)
        _check_string_list(
            record.get("acceptance_criteria"),
            f"{path}.acceptance_criteria",
            errors,
            minimum=1,
        )
        dependencies = _check_string_list(
            record.get("dependencies"),
            f"{path}.dependencies",
            errors,
            unique=True,
            maximum_text=MAX_ID_CHARS,
        ) or []
        requirement_edges[str(requirement_id)] = dependencies
        for ref in dependencies:
            if ref == requirement_id:
                _schema_error(errors, "self_dependency", f"{requirement_id} depends on itself.", str(requirement_id))
            elif ref not in requirement_ids:
                _schema_error(errors, "missing_dependency", f"{requirement_id} depends on missing requirement {ref}.", str(requirement_id), ref)
        _check_string_list(record.get("negative_requirements"), f"{path}.negative_requirements", errors)
        _check_enum(record.get("status"), REQUIREMENT_STATES, f"{path}.status", errors)
        disposition = record.get("disposition")
        _check_disposition(disposition, f"{path}.disposition", errors)
        if record.get("status") == "dispositioned" and disposition is None:
            _schema_error(errors, "missing_disposition", f"{requirement_id} is dispositioned without a disposition.", str(requirement_id))
        if record.get("status") != "dispositioned" and disposition is not None:
            _schema_error(errors, "unexpected_disposition", f"{requirement_id} has a disposition while active.", str(requirement_id))
        record_evidence = record.get("evidence")
        if not isinstance(record_evidence, list):
            _schema_error(errors, "wrong_type", f"{path}.evidence must be an array.", path)
        else:
            for evidence_index, evidence in enumerate(record_evidence):
                _check_evidence_record(
                    evidence,
                    f"{path}.evidence[{evidence_index}]",
                    errors,
                    evidence_ids,
                    earliest=introduction_times.get(str(requirement_id), created),
                    latest=updated,
                )
        if record.get("status") == "satisfied" and missing_criterion_evidence(
            record.get("acceptance_criteria", []),
            record_evidence,
            target_definition_digest(
                record, "requirement", plan, digest_context
            ),
        ):
            _schema_error(
                errors,
                "missing_evidence",
                f"Satisfied requirement {requirement_id} lacks passing evidence for every acceptance criterion.",
                str(requirement_id),
            )

    for cycle in _graph_cycles(requirement_ids, requirement_edges):
        _schema_error(errors, "dependency_cycle", f"Requirement dependency cycle: {' -> '.join(cycle)}.", *cycle)
    lowered_requirement_ids: dict[str, str] = {}
    for requirement_id in sorted(requirement_ids):
        folded = requirement_id.casefold()
        if folded in lowered_requirement_ids and lowered_requirement_ids[folded] != requirement_id:
            _schema_error(
                errors,
                "duplicate_identifier",
                f"Requirement identifiers {lowered_requirement_ids[folded]} and {requirement_id} collide case-insensitively.",
                lowered_requirement_ids[folded],
                requirement_id,
            )
        lowered_requirement_ids[folded] = requirement_id

    decisions = plan.get("decisions") if isinstance(plan.get("decisions"), list) else []
    for index, item in enumerate(decisions):
        path = f"decisions[{index}]"
        record = _check_exact_keys(
            item,
            {"decision_id", "statement", "status", "source_ids", "authority_basis", "decided_at"},
            path,
            errors,
        )
        if not record:
            continue
        _check_id(record.get("decision_id"), DECISION_ID_RE, f"{path}.decision_id", errors)
        _check_string(record.get("statement"), f"{path}.statement", errors)
        decision_status_valid = _check_enum(
            record.get("status"), DECISION_STATES, f"{path}.status", errors
        )
        refs = _check_string_list(record.get("source_ids"), f"{path}.source_ids", errors, unique=True) or []
        for ref in refs:
            if ref not in source_ids:
                _schema_error(errors, "missing_reference", f"Decision references missing source {ref}.", str(record.get("decision_id")), ref)
        _check_string(record.get("authority_basis"), f"{path}.authority_basis", errors, nonblank=record.get("status") != "proposed")
        decided_at = _check_timestamp(
            record.get("decided_at"), f"{path}.decided_at", errors, nullable=True
        )
        _check_observation_boundary(decided_at, updated, f"{path}.decided_at", errors)
        if decision_status_valid and _is_enum_value(
            record.get("status"), {"approved", "rejected"}
        ) and record.get("decided_at") is None:
            _schema_error(errors, "missing_timestamp", f"{path}.decided_at is required for a decided record.", path)

    questions = plan.get("open_questions") if isinstance(plan.get("open_questions"), list) else []
    known_targets = source_ids | requirement_ids | phase_ids | task_ids | decision_ids | question_ids | assumption_ids
    for index, item in enumerate(questions):
        path = f"open_questions[{index}]"
        record = _check_exact_keys(
            item,
            {"question_id", "question", "affects", "prerequisites", "status", "answer", "authority_basis"},
            path,
            errors,
        )
        if not record:
            continue
        _check_id(record.get("question_id"), QUESTION_ID_RE, f"{path}.question_id", errors)
        _check_string(record.get("question"), f"{path}.question", errors)
        affects = _check_string_list(record.get("affects"), f"{path}.affects", errors, unique=True) or []
        prereqs = _check_string_list(record.get("prerequisites"), f"{path}.prerequisites", errors, unique=True) or []
        for ref in affects + prereqs:
            if ref not in known_targets:
                _schema_error(errors, "missing_reference", f"Question references unknown target {ref}.", str(record.get("question_id")), ref)
        _check_enum(record.get("status"), QUESTION_STATES, f"{path}.status", errors)
        _check_string(record.get("answer"), f"{path}.answer", errors, nullable=True)
        _check_string(
            record.get("authority_basis"),
            f"{path}.authority_basis",
            errors,
            nonblank=record.get("status") != "open",
            nullable=record.get("status") == "open",
        )
        if record.get("status") == "answered" and record.get("answer") is None:
            _schema_error(errors, "missing_answer", f"{path}.answer is required for an answered question.", path)

    assumptions = plan.get("assumptions") if isinstance(plan.get("assumptions"), list) else []
    for index, item in enumerate(assumptions):
        path = f"assumptions[{index}]"
        record = _check_exact_keys(
            item,
            {"assumption_id", "statement", "basis", "status", "authority_basis"},
            path,
            errors,
        )
        if not record:
            continue
        _check_id(record.get("assumption_id"), ASSUMPTION_ID_RE, f"{path}.assumption_id", errors)
        _check_string(record.get("statement"), f"{path}.statement", errors)
        _check_string(record.get("basis"), f"{path}.basis", errors)
        _check_enum(record.get("status"), ASSUMPTION_STATES, f"{path}.status", errors)
        _check_string(
            record.get("authority_basis"),
            f"{path}.authority_basis",
            errors,
            nonblank=record.get("status") != "unconfirmed",
            nullable=record.get("status") == "unconfirmed",
        )

    phases = plan.get("phases") if isinstance(plan.get("phases"), list) else []
    phase_edges: dict[str, list[str]] = {}
    phase_position: dict[str, int] = {}
    phase_task_memberships: dict[str, str] = {}
    for index, item in enumerate(phases):
        path = f"phases[{index}]"
        record = _check_exact_keys(
            item,
            {
                "phase_id",
                "title",
                "objective",
                "scope",
                "depends_on_phase_ids",
                "entry_conditions",
                "exit_criteria",
                "task_ids",
                "risks",
                "status",
            },
            path,
            errors,
        )
        if not record:
            continue
        phase_id = record.get("phase_id")
        _check_id(phase_id, PHASE_ID_RE, f"{path}.phase_id", errors)
        phase_number_match = PHASE_ID_RE.fullmatch(str(phase_id))
        phase_position[str(phase_id)] = (
            int(phase_number_match.group(1)) if phase_number_match else index + 1
        )
        _check_string(record.get("title"), f"{path}.title", errors, maximum=MAX_TITLE_CHARS)
        _check_string(record.get("objective"), f"{path}.objective", errors)
        _check_string_list(record.get("scope"), f"{path}.scope", errors)
        dependencies = _check_string_list(
            record.get("depends_on_phase_ids"),
            f"{path}.depends_on_phase_ids",
            errors,
            unique=True,
        ) or []
        phase_edges[str(phase_id)] = dependencies
        for ref in dependencies:
            if ref == phase_id:
                _schema_error(errors, "self_dependency", f"{phase_id} depends on itself.", str(phase_id))
            elif ref not in phase_ids:
                _schema_error(errors, "missing_dependency", f"{phase_id} depends on missing phase {ref}.", str(phase_id), ref)
            elif phase_position.get(ref, len(phases) + 1) >= phase_position.get(str(phase_id), index + 1):
                _schema_error(errors, "phase_order", f"{phase_id} depends on a phase that is not earlier.", str(phase_id), ref)
        _check_string_list(record.get("entry_conditions"), f"{path}.entry_conditions", errors, minimum=1)
        _check_string_list(record.get("exit_criteria"), f"{path}.exit_criteria", errors, minimum=1)
        memberships = _check_string_list(
            record.get("task_ids"),
            f"{path}.task_ids",
            errors,
            minimum=1,
            unique=True,
        ) or []
        sorted_memberships = sorted(
            memberships,
            key=lambda value: (
                0,
                int(TASK_ID_RE.fullmatch(value).group(1)),
            )
            if TASK_ID_RE.fullmatch(value)
            else (1, value),
        )
        if memberships != sorted_memberships:
            _schema_error(
                errors,
                "nondeterministic_order",
                f"{path}.task_ids must use numeric task order.",
                str(phase_id),
            )
        for task_id in memberships:
            if task_id not in task_ids:
                _schema_error(errors, "missing_reference", f"{phase_id} references missing task {task_id}.", str(phase_id), task_id)
            if task_id in phase_task_memberships:
                _schema_error(errors, "duplicate_membership", f"Task {task_id} belongs to more than one phase.", task_id)
            phase_task_memberships[task_id] = str(phase_id)
        _check_string_list(record.get("risks"), f"{path}.risks", errors)
        _check_enum(record.get("status"), PHASE_STATES, f"{path}.status", errors)

    for cycle in _graph_cycles(phase_ids, phase_edges):
        _schema_error(errors, "dependency_cycle", f"Phase dependency cycle: {' -> '.join(cycle)}.", *cycle)
    phase_numbers = [
        int(match.group(1))
        for phase in phases
        if isinstance(phase, dict)
        and (match := PHASE_ID_RE.fullmatch(str(phase.get("phase_id", ""))))
    ]
    if phase_numbers != sorted(phase_numbers):
        _schema_error(
            errors,
            "nondeterministic_order",
            "phases must use numeric phase order.",
            "phases",
        )

    tasks = plan.get("tasks") if isinstance(plan.get("tasks"), list) else []
    task_edges: dict[str, list[str]] = {}
    tasks_by_id: dict[str, dict[str, Any]] = {}
    tasks_by_phase: dict[str, list[dict[str, Any]]] = {phase_id: [] for phase_id in phase_ids}
    for index, item in enumerate(tasks):
        path = f"tasks[{index}]"
        record = _check_exact_keys(
            item,
            {
                "task_id",
                "phase_id",
                "title",
                "action",
                "requirement_ids",
                "design_basis",
                "target_artifacts",
                "dependencies",
                "parallel_group",
                "risks",
                "acceptance_criteria",
                "verification_steps",
                "status",
                "blocker_reason",
                "pause_reason",
                "skip_reason",
                "skip_authority",
                "evidence",
                "completed_at",
            },
            path,
            errors,
        )
        if not record:
            continue
        task_id = record.get("task_id")
        phase_id = record.get("phase_id")
        _check_id(task_id, TASK_ID_RE, f"{path}.task_id", errors)
        phase_id_valid = _check_id(
            phase_id, PHASE_ID_RE, f"{path}.phase_id", errors
        )
        tasks_by_id[str(task_id)] = record
        tasks_by_phase.setdefault(str(phase_id), []).append(record)
        if phase_id_valid and phase_id not in phase_ids:
            _schema_error(errors, "missing_reference", f"{task_id} references missing phase {phase_id}.", str(task_id), str(phase_id))
        if phase_task_memberships.get(str(task_id)) != phase_id:
            _schema_error(errors, "membership_mismatch", f"{task_id} phase membership is inconsistent.", str(task_id), str(phase_id))
        _check_string(record.get("title"), f"{path}.title", errors, maximum=MAX_TITLE_CHARS)
        _check_string(record.get("action"), f"{path}.action", errors)
        req_refs = _check_string_list(record.get("requirement_ids"), f"{path}.requirement_ids", errors, unique=True) or []
        bases = _check_string_list(record.get("design_basis"), f"{path}.design_basis", errors, unique=True) or []
        if not req_refs and not bases:
            _schema_error(errors, "orphan_task", f"{task_id} has no requirement or design basis.", str(task_id))
        for ref in req_refs:
            if ref not in requirement_ids:
                _schema_error(errors, "missing_reference", f"{task_id} references missing requirement {ref}.", str(task_id), ref)
        _check_string_list(record.get("target_artifacts"), f"{path}.target_artifacts", errors, minimum=1)
        dependencies = _check_string_list(record.get("dependencies"), f"{path}.dependencies", errors, unique=True) or []
        task_edges[str(task_id)] = dependencies
        for ref in dependencies:
            if ref == task_id:
                _schema_error(errors, "self_dependency", f"{task_id} depends on itself.", str(task_id))
            elif ref not in task_ids:
                _schema_error(errors, "missing_dependency", f"{task_id} depends on missing task {ref}.", str(task_id), ref)
        parallel = record.get("parallel_group")
        if parallel is not None and (
            not isinstance(parallel, str) or not SAFE_PARALLEL_RE.fullmatch(parallel)
        ):
            _schema_error(errors, "invalid_parallel_group", f"{path}.parallel_group is invalid.", path)
        _check_string_list(record.get("risks"), f"{path}.risks", errors)
        _check_string_list(record.get("acceptance_criteria"), f"{path}.acceptance_criteria", errors, minimum=1)
        _check_string_list(record.get("verification_steps"), f"{path}.verification_steps", errors, minimum=1)
        task_status_valid = _check_enum(
            record.get("status"), TASK_STATES, f"{path}.status", errors
        )
        _check_string(record.get("blocker_reason"), f"{path}.blocker_reason", errors, nullable=True)
        _check_string(record.get("pause_reason"), f"{path}.pause_reason", errors, nullable=True)
        _check_string(record.get("skip_reason"), f"{path}.skip_reason", errors, nullable=True)
        _check_string(record.get("skip_authority"), f"{path}.skip_authority", errors, nullable=True)
        if record.get("status") == "blocked" and record.get("blocker_reason") is None:
            _schema_error(errors, "missing_reason", f"Blocked task {task_id} lacks blocker_reason.", str(task_id))
        if record.get("status") != "blocked" and record.get("blocker_reason") is not None:
            _schema_error(errors, "unexpected_reason", f"Unblocked task {task_id} retains blocker_reason.", str(task_id))
        if record.get("status") == "paused" and record.get("pause_reason") is None:
            _schema_error(errors, "missing_reason", f"Paused task {task_id} lacks pause_reason.", str(task_id))
        if record.get("status") != "paused" and record.get("pause_reason") is not None:
            _schema_error(errors, "unexpected_reason", f"Active task {task_id} retains pause_reason.", str(task_id))
        if record.get("status") == "skipped":
            if record.get("skip_reason") is None or record.get("skip_authority") is None:
                _schema_error(errors, "missing_skip_authority", f"Skipped task {task_id} lacks reason or authority.", str(task_id))
        elif record.get("skip_reason") is not None or record.get("skip_authority") is not None:
            _schema_error(errors, "unexpected_skip", f"Non-skipped task {task_id} retains skip fields.", str(task_id))
        record_evidence = record.get("evidence")
        if not isinstance(record_evidence, list):
            _schema_error(errors, "wrong_type", f"{path}.evidence must be an array.", path)
        else:
            for evidence_index, evidence in enumerate(record_evidence):
                _check_evidence_record(
                    evidence,
                    f"{path}.evidence[{evidence_index}]",
                    errors,
                    evidence_ids,
                    earliest=introduction_times.get(str(task_id), created),
                    latest=updated,
                )
        completed_at = _check_timestamp(
            record.get("completed_at"), f"{path}.completed_at", errors, nullable=True
        )
        _check_observation_boundary(
            completed_at, updated, f"{path}.completed_at", errors
        )
        if task_status_valid and record.get("status") == "completed":
            if record.get("completed_at") is None:
                _schema_error(errors, "missing_timestamp", f"Completed task {task_id} lacks completed_at.", str(task_id))
            if missing_criterion_evidence(
                record.get("acceptance_criteria", []),
                record_evidence,
                target_definition_digest(record, "task", plan, digest_context),
            ):
                _schema_error(
                    errors,
                    "missing_evidence",
                    f"Completed task {task_id} lacks passing evidence for every acceptance criterion.",
                    str(task_id),
                )
        elif task_status_valid and record.get("completed_at") is not None:
            _schema_error(errors, "unexpected_timestamp", f"Incomplete task {task_id} retains completed_at.", str(task_id))

    for cycle in _graph_cycles(task_ids, task_edges):
        _schema_error(errors, "dependency_cycle", f"Task dependency cycle: {' -> '.join(cycle)}.", *cycle)
    for task_id, dependencies in sorted(task_edges.items()):
        task = tasks_by_id.get(task_id)
        if not task:
            continue
        current_phase = phase_position.get(str(task.get("phase_id")), -1)
        for dependency in dependencies:
            predecessor = tasks_by_id.get(dependency)
            if predecessor:
                predecessor_phase = phase_position.get(str(predecessor.get("phase_id")), -1)
                if predecessor_phase > current_phase:
                    _schema_error(errors, "phase_order", f"{task_id} depends on task {dependency} in a later phase.", task_id, dependency)
        if _is_enum_value(task.get("status"), {"in_progress", "completed"}):
            unfinished = [
                dependency
                for dependency in dependencies
                if not _is_enum_value(
                    tasks_by_id.get(dependency, {}).get("status"),
                    {"completed", "skipped"},
                )
            ]
            if unfinished:
                _schema_error(errors, "predecessor_incomplete", f"{task_id} started before predecessors completed.", task_id, *unfinished)

    phase_status_by_id = {
        str(phase.get("phase_id")): phase.get("status")
        for phase in phases
        if isinstance(phase, Mapping) and isinstance(phase.get("phase_id"), str)
    }
    for phase in phases:
        if not isinstance(phase, dict) or not isinstance(phase.get("phase_id"), str):
            continue
        derived = derive_phase_status(tasks_by_phase.get(phase["phase_id"], []), plan)
        if phase.get("status") != derived:
            _schema_error(
                errors,
                "phase_status_drift",
                f"{phase['phase_id']} stores {phase.get('status')} but derives {derived}.",
                phase["phase_id"],
            )
        if _is_enum_value(phase.get("status"), {"in_progress", "completed"}):
            incomplete_phase_predecessors = [
                predecessor
                for predecessor in phase_edges.get(phase["phase_id"], [])
                if phase_status_by_id.get(predecessor) != "completed"
            ]
            if incomplete_phase_predecessors:
                _schema_error(
                    errors,
                    "phase_predecessor_incomplete",
                    f"{phase['phase_id']} entered execution before predecessor phases completed.",
                    phase["phase_id"],
                    *incomplete_phase_predecessors,
                )

    parallel_groups: dict[str, list[dict[str, Any]]] = {}
    for task in tasks:
        if isinstance(task, dict) and isinstance(task.get("parallel_group"), str):
            parallel_groups.setdefault(task["parallel_group"], []).append(task)

    for group, members in sorted(parallel_groups.items()):
        member_ids = {str(member.get("task_id")) for member in members}
        for member in members:
            member_id = str(member.get("task_id"))
            pending = list(task_edges.get(member_id, []))
            visited: set[str] = set()
            related: str | None = None
            while pending:
                dependency = pending.pop()
                if dependency in member_ids and dependency != member_id:
                    related = dependency
                    break
                if dependency in visited:
                    continue
                visited.add(dependency)
                pending.extend(task_edges.get(dependency, []))
            if related is not None:
                _schema_error(
                    errors,
                    "unsafe_parallel_group",
                    f"Parallel group {group} contains dependency-related tasks.",
                    member_id,
                    related,
                )
        member_phase_ids = {
            str(member.get("phase_id")) for member in members
        }
        reported_phase_pairs: set[tuple[str, str]] = set()
        for start_phase in sorted(member_phase_ids):
            pending = list(phase_edges.get(start_phase, []))
            visited: set[str] = set()
            while pending:
                dependency_phase = pending.pop()
                if dependency_phase in visited:
                    continue
                visited.add(dependency_phase)
                if dependency_phase in member_phase_ids:
                    pair = tuple(sorted((start_phase, dependency_phase)))
                    if pair not in reported_phase_pairs:
                        reported_phase_pairs.add(pair)
                        _schema_error(
                            errors,
                            "unsafe_parallel_group",
                            f"Parallel group {group} spans dependency-related phases.",
                            *pair,
                        )
                    break
                pending.extend(phase_edges.get(dependency_phase, []))
        artifact_records: list[tuple[str, str, str]] = []
        case_insensitive = filesystem_is_case_insensitive(context.project_root)
        for member in members:
            member_id = str(member.get("task_id"))
            for artifact in {
                item
                for item in list_or_empty(member.get("target_artifacts"))
                if isinstance(item, str)
            }:
                key = normalized_artifact_key(
                    artifact,
                    project_root=context.project_root,
                    case_insensitive=case_insensitive,
                )
                artifact_records.append((member_id, str(artifact), key))
        path_records = [
            record for record in artifact_records if record[2].startswith("path:")
        ]
        glob_records = [
            record
            for record in path_records
            if any(character in record[2] for character in "*?[")
        ]
        if glob_records and len(member_ids) > 1:
            _schema_error(
                errors,
                "unsafe_parallel_group",
                f"Parallel group {group} contains an indeterminate glob write scope.",
                *sorted(member_ids),
                *sorted(record[1] for record in glob_records),
            )
        concrete_paths = sorted(
            (
                tuple(Path(record[2].removeprefix("path:")).parts),
                record,
            )
            for record in path_records
            if not any(character in record[2] for character in "*?[")
        )
        ancestor_stack: list[tuple[tuple[str, ...], tuple[str, str, str]]] = []
        for parts, record in concrete_paths:
            while ancestor_stack and parts[: len(ancestor_stack[-1][0])] != ancestor_stack[-1][0]:
                ancestor_stack.pop()
            conflicting = next(
                (
                    ancestor
                    for ancestor in reversed(ancestor_stack)
                    if ancestor[1][0] != record[0]
                ),
                None,
            )
            if conflicting is not None:
                _schema_error(
                    errors,
                    "unsafe_parallel_group",
                    f"Parallel group {group} contains tasks with an overlapping normalized target.",
                    conflicting[1][0],
                    record[0],
                    conflicting[1][1],
                    record[1],
                )
            ancestor_stack.append((parts, record))
        observation_owners: dict[str, list[tuple[str, str]]] = {}
        for owner, artifact, key in artifact_records:
            if not key.startswith("path:"):
                observation_owners.setdefault(key, []).append((owner, artifact))
        for records in observation_owners.values():
            owners = {record[0] for record in records}
            if len(owners) > 1:
                _schema_error(
                    errors,
                    "unsafe_parallel_group",
                    f"Parallel group {group} contains tasks with an overlapping normalized target.",
                    *sorted(owners),
                    *sorted(record[1] for record in records),
                )

    coverage = _check_exact_keys(
        plan.get("coverage"),
        {"source_to_requirement", "requirement_to_task"},
        "coverage",
        errors,
    )
    requirements_by_id = {
        str(item.get("requirement_id")): item
        for item in requirements
        if isinstance(item, dict) and isinstance(item.get("requirement_id"), str)
    }
    if coverage:
        source_edges = coverage.get("source_to_requirement")
        seen_sources: set[str] = set()
        if not isinstance(source_edges, list):
            _schema_error(errors, "wrong_type", "coverage.source_to_requirement must be an array.", "coverage")
        else:
            source_edge_requirement_ids: dict[str, set[str]] = {}
            for candidate_edge in source_edges:
                if not isinstance(candidate_edge, Mapping) or not isinstance(
                    candidate_edge.get("source_id"), str
                ):
                    continue
                candidate_refs = candidate_edge.get("requirement_ids")
                if not isinstance(candidate_refs, list):
                    continue
                source_edge_requirement_ids.setdefault(
                    str(candidate_edge["source_id"]), set()
                ).update(
                    ref for ref in candidate_refs if isinstance(ref, str)
                )
            for index, item in enumerate(source_edges):
                path = f"coverage.source_to_requirement[{index}]"
                edge = _check_exact_keys(item, {"source_id", "requirement_ids", "disposition"}, path, errors)
                if not edge:
                    continue
                source_id = edge.get("source_id")
                _check_id(source_id, SOURCE_ID_RE, f"{path}.source_id", errors)
                if isinstance(source_id, str) and source_id in seen_sources:
                    _schema_error(errors, "duplicate_coverage_edge", f"Coverage repeats source {source_id}.", str(source_id))
                seen_sources.add(str(source_id))
                if isinstance(source_id, str) and source_id not in source_ids:
                    _schema_error(errors, "missing_reference", f"Coverage references missing source {source_id}.", str(source_id))
                refs = _check_string_list(edge.get("requirement_ids"), f"{path}.requirement_ids", errors, unique=True) or []
                for ref in refs:
                    if ref not in requirement_ids:
                        _schema_error(errors, "missing_reference", f"Coverage references missing requirement {ref}.", str(source_id), ref)
                _check_disposition(edge.get("disposition"), f"{path}.disposition", errors)
                disposition = edge.get("disposition")
                if (
                    isinstance(disposition, Mapping)
                    and disposition.get("kind") == "superseded"
                ):
                    replacement_sources = {
                        candidate_id
                        for requirement in requirements
                        if isinstance(requirement, Mapping)
                        for candidate_id in list_or_empty(
                            requirement.get("source_ids")
                        )
                        if isinstance(candidate_id, str)
                        and candidate_id != source_id
                        and candidate_id in sources_by_id
                        and bool(sources_by_id[candidate_id].get("facts_used"))
                        and not sources_by_id[candidate_id].get(
                            "access_limitations"
                        )
                        and any(
                            requirements_by_id.get(requirement_id, {}).get("status")
                            in {"active", "satisfied"}
                            and candidate_id
                            in list_or_empty(
                                requirements_by_id.get(requirement_id, {}).get(
                                    "source_ids"
                                )
                            )
                            for requirement_id in source_edge_requirement_ids.get(
                                candidate_id, set()
                            )
                        )
                    }
                    if refs or not replacement_sources:
                        _schema_error(
                            errors,
                            "invalid_source_supersession",
                            "A superseded source must have no live requirement edge and at least one fully inspected replacement source in active coverage.",
                            str(source_id),
                        )
        requirement_edges_list = coverage.get("requirement_to_task")
        seen_requirements: set[str] = set()
        if not isinstance(requirement_edges_list, list):
            _schema_error(errors, "wrong_type", "coverage.requirement_to_task must be an array.", "coverage")
        else:
            for index, item in enumerate(requirement_edges_list):
                path = f"coverage.requirement_to_task[{index}]"
                edge = _check_exact_keys(item, {"requirement_id", "task_ids", "disposition"}, path, errors)
                if not edge:
                    continue
                requirement_id = edge.get("requirement_id")
                _check_id(requirement_id, REQUIREMENT_ID_RE, f"{path}.requirement_id", errors)
                if isinstance(requirement_id, str) and requirement_id in seen_requirements:
                    _schema_error(errors, "duplicate_coverage_edge", f"Coverage repeats requirement {requirement_id}.", str(requirement_id))
                seen_requirements.add(str(requirement_id))
                if isinstance(requirement_id, str) and requirement_id not in requirement_ids:
                    _schema_error(errors, "missing_reference", f"Coverage references missing requirement {requirement_id}.", str(requirement_id))
                refs = _check_string_list(edge.get("task_ids"), f"{path}.task_ids", errors, unique=True) or []
                for ref in refs:
                    if ref not in task_ids:
                        _schema_error(errors, "missing_reference", f"Coverage references missing task {ref}.", str(requirement_id), ref)
                    elif requirement_id not in list_or_empty(
                        tasks_by_id.get(ref, {}).get("requirement_ids")
                    ):
                        _schema_error(errors, "coverage_mismatch", f"Coverage edge {requirement_id} -> {ref} disagrees with the task.", str(requirement_id), ref)
                _check_disposition(edge.get("disposition"), f"{path}.disposition", errors)
                requirement = requirements_by_id.get(str(requirement_id))
                if requirement is not None and edge.get("disposition") != requirement.get(
                    "disposition"
                ):
                    _schema_error(
                        errors,
                        "coverage_disposition_mismatch",
                        f"Coverage disposition for {requirement_id} must exactly match the requirement disposition.",
                        str(requirement_id),
                    )

    for task in tasks:
        if not isinstance(task, dict):
            continue
        task_id = str(task.get("task_id", ""))
        if task.get("status") == "completed" and missing_criterion_evidence(
            task.get("acceptance_criteria", []),
            task.get("evidence"),
            target_definition_digest(task, "task", plan, digest_context),
        ):
            _schema_error(
                errors,
                "missing_evidence",
                f"Completed task {task_id} lacks evidence for every acceptance criterion.",
                task_id,
            )
        if task.get("status") == "skipped" and not skipped_task_is_disposed(task, plan):
            _schema_error(
                errors,
                "invalid_skip_disposition",
                f"Skipped task {task_id} lacks disposed requirement coverage.",
                task_id,
                *[str(item) for item in list_or_empty(task.get("requirement_ids"))],
            )

    validation = _check_exact_keys(
        plan.get("validation"),
        {"checked_revision", "checked_at", "status", "findings"},
        "validation",
        errors,
    )
    if validation:
        checked_revision = validation.get("checked_revision")
        if isinstance(checked_revision, bool) or not isinstance(checked_revision, int) or checked_revision < 1:
            _schema_error(errors, "invalid_revision", "validation.checked_revision must be positive.", "validation")
        elif isinstance(revision, int) and checked_revision != revision:
            _schema_error(errors, "stale_validation", "validation.checked_revision does not match revision.", "validation")
        checked_at = _check_timestamp(
            validation.get("checked_at"), "validation.checked_at", errors
        )
        _check_observation_boundary(
            checked_at, updated, "validation.checked_at", errors
        )
        if checked_at is not None and updated is not None and checked_at != updated:
            _schema_error(
                errors,
                "validation_timestamp_drift",
                "validation.checked_at must equal updated_at for the current revision.",
                "validation.checked_at",
                "updated_at",
            )
        _check_enum(validation.get("status"), VALIDATION_STATUSES, "validation.status", errors)
        findings = validation.get("findings")
        if not isinstance(findings, list):
            _schema_error(errors, "wrong_type", "validation.findings must be an array.", "validation")
        else:
            finding_ids: set[str] = set()
            for index, item in enumerate(findings):
                path = f"validation.findings[{index}]"
                finding = _check_exact_keys(
                    item,
                    {"finding_id", "severity", "status", "code", "message", "targets"},
                    path,
                    errors,
                )
                if not finding:
                    continue
                finding_id = finding.get("finding_id")
                if not isinstance(finding_id, str) or not re.fullmatch(r"FIND-\d{3,}", finding_id):
                    _schema_error(errors, "invalid_identifier", f"{path}.finding_id is invalid.", path)
                elif finding_id in finding_ids:
                    _schema_error(errors, "duplicate_identifier", f"Validation repeats {finding_id}.", finding_id)
                else:
                    finding_ids.add(finding_id)
                _check_enum(finding.get("severity"), FINDING_SEVERITIES, f"{path}.severity", errors)
                _check_enum(finding.get("status"), FINDING_STATUSES, f"{path}.status", errors)
                _check_string(finding.get("code"), f"{path}.code", errors, maximum=128)
                _check_string(finding.get("message"), f"{path}.message", errors)
                _check_string_list(finding.get("targets"), f"{path}.targets", errors, unique=True)

    initial_record_ids = _check_string_list(
        plan.get("initial_record_ids"),
        "initial_record_ids",
        errors,
        minimum=1,
        unique=True,
        maximum_text=MAX_ID_CHARS,
    ) or []
    for identifier in initial_record_ids:
        if identifier not in known_targets:
            _schema_error(
                errors,
                "missing_reference",
                "initial_record_ids references an unknown stable record.",
                identifier,
            )

    history = plan.get("history")
    if not isinstance(history, list):
        _schema_error(errors, "wrong_type", "history must be an array.", "history")
    else:
        seen_revisions: list[int] = []
        seen_history_times: list[dt.datetime] = []
        for index, item in enumerate(history):
            path = f"history[{index}]"
            record = _check_exact_keys(
                item,
                {
                    "revision",
                    "timestamp",
                    "action_id",
                    "affected_ids",
                    "status_before",
                    "status_after",
                    "summary",
                    "authority_basis",
                },
                path,
                errors,
            )
            if not record:
                continue
            item_revision = record.get("revision")
            if isinstance(item_revision, bool) or not isinstance(item_revision, int) or item_revision < 1:
                _schema_error(errors, "invalid_revision", f"{path}.revision is invalid.", path)
            else:
                seen_revisions.append(item_revision)
            history_time = _check_timestamp(
                record.get("timestamp"), f"{path}.timestamp", errors
            )
            if history_time is not None:
                seen_history_times.append(history_time)
            action_id = record.get("action_id")
            action_valid = _check_id(
                action_id, ACTION_ID_RE, f"{path}.action_id", errors
            )
            affected = _check_string_list(record.get("affected_ids"), f"{path}.affected_ids", errors, minimum=1, unique=True) or []
            known_history_targets = known_targets | evidence_ids
            for ref in affected:
                if ref not in known_history_targets and ref != plan_id:
                    _schema_error(errors, "missing_reference", f"History references unknown identifier {ref}.", ref)
            _check_string(record.get("status_before"), f"{path}.status_before", errors, nullable=True, maximum=64)
            _check_string(record.get("status_after"), f"{path}.status_after", errors, nullable=True, maximum=64)
            status_before = record.get("status_before")
            status_after = record.get("status_after")
            if action_valid:
                if action_id == "TO-IP-001":
                    if status_before is not None or status_after != "draft":
                        _schema_error(
                            errors,
                            "history_status_domain",
                            "TO-IP-001 history must record the initial null to draft transition.",
                            path,
                        )
                elif action_id in {"TO-IP-004", "TO-IP-005", "TO-IP-008"}:
                    if not _is_enum_value(
                        status_before, PLAN_STATES
                    ) or not _is_enum_value(status_after, PLAN_STATES):
                        _schema_error(
                            errors,
                            "history_status_domain",
                            f"{action_id} history must use plan lifecycle states.",
                            path,
                        )
                elif action_id == "TO-IP-006":
                    if not _is_enum_value(
                        status_before, TASK_STATES
                    ) or not _is_enum_value(status_after, TASK_STATES):
                        _schema_error(
                            errors,
                            "history_status_domain",
                            "TO-IP-006 history must use task lifecycle states.",
                            path,
                        )
                elif action_id == "TO-IP-007":
                    domain = TASK_STATES | REQUIREMENT_STATES
                    if not _is_enum_value(
                        status_before, domain
                    ) or status_after != status_before:
                        _schema_error(
                            errors,
                            "history_status_domain",
                            "TO-IP-007 history must preserve one task or requirement state.",
                            path,
                        )
            _check_string(record.get("summary"), f"{path}.summary", errors)
            _check_string(record.get("authority_basis"), f"{path}.authority_basis", errors)
        if isinstance(revision, int) and (
            revision != len(history)
            or len(seen_revisions) != len(history)
            or any(
                item_revision != expected_revision
                for expected_revision, item_revision in enumerate(
                    seen_revisions, start=1
                )
            )
        ):
            _schema_error(errors, "history_revision_gap", "History revisions must be contiguous through the current revision.", "history")
        if seen_history_times != sorted(seen_history_times):
            _schema_error(
                errors,
                "history_timestamp_order",
                "History timestamps must not move backward.",
                "history",
            )
        if history:
            first = history[0] if isinstance(history[0], dict) else {}
            last = history[-1] if isinstance(history[-1], dict) else {}
            if first.get("revision") != 1 or first.get("action_id") != "TO-IP-001":
                _schema_error(
                    errors,
                    "history_creation_missing",
                    "History revision 1 must be the TO-IP-001 creation event.",
                    "history[0]",
                )
            try:
                first_time = parse_timestamp(first.get("timestamp"), "history[0].timestamp")
            except ValueError:
                first_time = None
            if first_time is not None and created is not None and first_time != created:
                _schema_error(
                    errors,
                    "history_creation_timestamp",
                    "The creation history timestamp must equal created_at.",
                    "history[0]",
                    "created_at",
                )
            try:
                last_time = parse_timestamp(
                    last.get("timestamp"), "history[-1].timestamp"
                )
            except ValueError:
                last_time = None
            if last_time is not None and updated is not None and last_time != updated:
                _schema_error(
                    errors,
                    "history_current_timestamp_mismatch",
                    "The current history entry timestamp must equal updated_at.",
                    "history[-1]",
                    "updated_at",
                )
            later_creation = [
                f"history[{index}]"
                for index, item in enumerate(history[1:], start=1)
                if isinstance(item, dict) and item.get("action_id") == "TO-IP-001"
            ]
            if later_creation:
                _schema_error(
                    errors,
                    "history_creation_repeated",
                    "TO-IP-001 can appear only at history revision 1.",
                    *later_creation,
                )
            all_affected = {
                str(identifier)
                for item in history
                if isinstance(item, dict)
                for identifier in list_or_empty(item.get("affected_ids"))
                if isinstance(identifier, str)
            }
            missing_history_ids = sorted(
                set(stable_record_ids(plan)) - all_affected
            )
            if missing_history_ids:
                _schema_error(
                    errors,
                    "history_target_omission",
                    "One or more stable records never appear in history affected_ids.",
                    *missing_history_ids,
                )
            first_affected = {
                identifier
                for identifier in list_or_empty(first.get("affected_ids"))
                if isinstance(identifier, str)
            }
            expected_creation_affected = {str(plan_id), *initial_record_ids}
            if first_affected != expected_creation_affected:
                _schema_error(
                    errors,
                    "history_creation_affected_mismatch",
                    "Creation history affected_ids must exactly match plan_id plus initial_record_ids.",
                    "history[0]",
                    "initial_record_ids",
                )
            initial_required_groups = (
                (source_ids, "source"),
                (requirement_ids, "requirement"),
                (phase_ids, "phase"),
                (task_ids, "task"),
            )
            for identifiers, label in initial_required_groups:
                if identifiers and not (set(identifiers) & first_affected):
                    _schema_error(
                        errors,
                        "history_creation_incomplete",
                        f"Creation history must name at least one initial {label} record.",
                        "history[0]",
                    )
        if updated and any(item > updated for item in seen_history_times):
            _schema_error(
                errors,
                "history_timestamp_order",
                "History cannot be newer than updated_at.",
                "history",
                "updated_at",
            )

    if plan.get("status") == "completed":
        for finding in completion_findings(plan):
            _schema_error(
                errors,
                f"completion_{finding['code']}",
                finding["message"],
                *finding["targets"],
            )

    if directory_name is not None:
        directory_match = DIRECTORY_RE.fullmatch(directory_name)
        if not directory_match:
            _schema_error(errors, "invalid_directory", "Managed plan directory name is invalid.", directory_name)
        elif plan_match:
            if directory_match.group(1) != slug:
                _schema_error(errors, "identity_mismatch", "Directory slug does not match canonical slug.", directory_name)
            if directory_match.group(2).replace("-", "") != plan_match.group(1):
                _schema_error(errors, "identity_mismatch", "Directory date does not match plan_id.", directory_name)
            if directory_match.group(3) != plan_match.group(2):
                _schema_error(errors, "identity_mismatch", "Directory suffix does not match plan_id.", directory_name)

    return errors


def _finding(
    severity: str,
    code: str,
    message: str,
    *targets: str,
) -> dict[str, Any]:
    return {
        "finding_id": "",
        "severity": severity,
        "status": "open",
        "code": code,
        "message": message,
        "targets": list(dict.fromkeys(target for target in targets if target)),
    }


def quality_findings(plan: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Compute current readiness and bidirectional-coverage findings."""
    findings: list[dict[str, Any]] = []
    digest_context = build_target_digest_context(plan)
    project = plan.get("project", {})
    if not project.get("inspected_at"):
        findings.append(
            _finding(
                "warning",
                "project_not_inspected",
                "The target project inspection time is unresolved.",
                "project",
            )
        )
    if not project.get("guidance"):
        findings.append(
            _finding(
                "warning",
                "guidance_not_inspected",
                "No applicable project guidance inspection is recorded.",
                "project.guidance",
            )
        )
    if not project.get("baseline_facts"):
        findings.append(
            _finding(
                "warning",
                "baseline_missing",
                "No live project baseline facts are recorded.",
                "project.baseline_facts",
            )
        )
    for index, gap in enumerate(project.get("evidence_gaps", [])):
        findings.append(
            _finding(
                "warning",
                "project_evidence_gap",
                f"Project evidence gap remains: {gap}",
                f"project.evidence_gaps[{index}]",
            )
        )

    sources = {
        item["source_id"]: item
        for item in plan.get("sources", [])
        if isinstance(item, dict) and isinstance(item.get("source_id"), str)
    }
    requirements = {
        item["requirement_id"]: item
        for item in plan.get("requirements", [])
        if isinstance(item, dict) and isinstance(item.get("requirement_id"), str)
    }
    tasks = {
        item["task_id"]: item
        for item in plan.get("tasks", [])
        if isinstance(item, dict) and isinstance(item.get("task_id"), str)
    }
    phases = {
        item["phase_id"]: item
        for item in plan.get("phases", [])
        if isinstance(item, dict) and isinstance(item.get("phase_id"), str)
    }
    for path, text in readiness_semantic_texts(plan):
        if is_readiness_placeholder(text):
            findings.append(
                _finding(
                    "error",
                    "placeholder_semantic_text",
                    "A readiness-critical semantic field contains placeholder text.",
                    path,
                )
            )
    actual_requirements_by_source: dict[str, set[str]] = {
        source_id: set() for source_id in sources
    }
    for requirement_id, requirement in requirements.items():
        for source_id in list_or_empty(requirement.get("source_ids")):
            if isinstance(source_id, str):
                actual_requirements_by_source.setdefault(source_id, set()).add(
                    requirement_id
                )
    actual_tasks_by_requirement: dict[str, set[str]] = {
        requirement_id: set() for requirement_id in requirements
    }
    for task_id, task in tasks.items():
        for requirement_id in list_or_empty(task.get("requirement_ids")):
            if isinstance(requirement_id, str):
                actual_tasks_by_requirement.setdefault(requirement_id, set()).add(
                    task_id
                )

    if not sources:
        findings.append(
            _finding("error", "no_sources", "The plan has no source records.", "sources")
        )
    if not requirements:
        findings.append(
            _finding(
                "error",
                "no_requirements",
                "The plan has no requirement records.",
                "requirements",
            )
        )
    if not phases:
        findings.append(
            _finding("error", "no_phases", "The plan has no phases.", "phases")
        )
    if not tasks:
        findings.append(_finding("error", "no_tasks", "The plan has no tasks.", "tasks"))
    if plan.get("status") in {"draft", "ready"}:
        active_task_ids = sorted(
            task_id
            for task_id, task in tasks.items()
            if task.get("status") == "in_progress"
        )
        if active_task_ids:
            findings.append(
                _finding(
                    "error",
                    "active_task_before_execution",
                    "A draft or ready plan cannot retain an in-progress task.",
                    *active_task_ids,
                )
            )

    source_edge_lookup = {
        str(edge.get("source_id")): edge
        for edge in plan.get("coverage", {}).get("source_to_requirement", [])
        if isinstance(edge, Mapping) and isinstance(edge.get("source_id"), str)
    }
    for source_id, source in sorted(sources.items()):
        source_edge = source_edge_lookup.get(source_id, {})
        historical = bool(source_edge.get("disposition")) and not bool(
            source_edge.get("requirement_ids")
        )
        for limitation in source.get("access_limitations", []):
            findings.append(
                _finding(
                    "info" if historical else "warning",
                    "historical_source_access_limitation"
                    if historical
                    else "source_access_limitation",
                    (
                        f"Historical disposed source limitation: {limitation}"
                        if historical
                        else f"Source access limitation remains: {limitation}"
                    ),
                    source_id,
                )
            )

    for decision in plan.get("decisions", []):
        if isinstance(decision, dict) and decision.get("status") == "proposed":
            findings.append(
                _finding(
                    "warning",
                    "proposed_decision",
                    "A proposed decision remains unapproved.",
                    str(decision.get("decision_id", "")),
                )
            )
    for question in plan.get("open_questions", []):
        if isinstance(question, dict) and question.get("status") == "open":
            findings.append(
                _finding(
                    "warning",
                    "open_question",
                    "A material plan question remains open.",
                    str(question.get("question_id", "")),
                )
            )
    for assumption in plan.get("assumptions", []):
        if isinstance(assumption, dict) and assumption.get("status") == "unconfirmed":
            findings.append(
                _finding(
                    "warning",
                    "unconfirmed_assumption",
                    "A plan assumption remains unconfirmed.",
                    str(assumption.get("assumption_id", "")),
                )
            )

    coverage = plan.get("coverage", {})
    source_edges: dict[str, Mapping[str, Any]] = {}
    for edge in coverage.get("source_to_requirement", []) if isinstance(coverage, dict) else []:
        if isinstance(edge, dict) and isinstance(edge.get("source_id"), str):
            source_edges[edge["source_id"]] = edge
    requirement_edges: dict[str, Mapping[str, Any]] = {}
    for edge in coverage.get("requirement_to_task", []) if isinstance(coverage, dict) else []:
        if isinstance(edge, dict) and isinstance(edge.get("requirement_id"), str):
            requirement_edges[edge["requirement_id"]] = edge

    for source_id in sorted(sources):
        edge = source_edges.get(source_id)
        if edge is None:
            findings.append(
                _finding(
                    "error",
                    "missing_source_coverage",
                    "A source has no forward-coverage edge.",
                    source_id,
                )
            )
        elif not edge.get("requirement_ids") and edge.get("disposition") is None:
            findings.append(
                _finding(
                    "error",
                    "uncovered_source",
                    "A source maps to no requirement and has no disposition.",
                    source_id,
                )
            )
        else:
            linked_requirements = set(edge.get("requirement_ids", []))
            actual_requirements = actual_requirements_by_source.get(
                source_id, set()
            )
            if linked_requirements != actual_requirements:
                findings.append(
                    _finding(
                        "error",
                        "coverage_mismatch",
                        "Source coverage disagrees with requirement source links.",
                        source_id,
                        *sorted(linked_requirements ^ actual_requirements),
                    )
                )
    for extra in sorted(set(source_edges) - set(sources)):
        findings.append(
            _finding(
                "error",
                "orphan_source_coverage",
                "A source coverage edge has no source record.",
                extra,
            )
        )

    for requirement_id, requirement in sorted(requirements.items()):
        edge = requirement_edges.get(requirement_id)
        if edge is None:
            findings.append(
                _finding(
                    "error",
                    "missing_requirement_coverage",
                    "A requirement has no reverse-coverage edge.",
                    requirement_id,
                )
            )
            continue
        linked_tasks = set(edge.get("task_ids", []))
        actual_tasks = actual_tasks_by_requirement.get(requirement_id, set())
        if linked_tasks != actual_tasks:
            findings.append(
                _finding(
                    "error",
                    "coverage_mismatch",
                    "Requirement coverage disagrees with task requirement links.",
                    requirement_id,
                    *sorted(linked_tasks ^ actual_tasks),
                )
            )
        if (
            requirement.get("status") in {"active", "satisfied"}
            and not linked_tasks
            and edge.get("disposition") is None
        ):
            findings.append(
                _finding(
                    "error",
                    "uncovered_requirement",
                    "An active requirement maps to no task and has no disposition.",
                    requirement_id,
                )
            )
        if requirement.get("status") == "dispositioned":
            if edge.get("disposition") is None:
                findings.append(
                    _finding(
                        "error",
                        "missing_coverage_disposition",
                        "A dispositioned requirement lacks a coverage disposition.",
                        requirement_id,
                    )
                )
        if requirement.get("status") == "satisfied":
            if missing_criterion_evidence(
                requirement.get("acceptance_criteria", []),
                requirement.get("evidence"),
                target_definition_digest(
                    requirement, "requirement", plan, digest_context
                ),
            ):
                findings.append(
                    _finding(
                        "error",
                        "requirement_evidence_gap",
                        "A satisfied requirement lacks evidence for every acceptance criterion.",
                        requirement_id,
                    )
                )
    for extra in sorted(set(requirement_edges) - set(requirements)):
        findings.append(
            _finding(
                "error",
                "orphan_requirement_coverage",
                "A requirement coverage edge has no requirement record.",
                extra,
            )
        )

    for task_id, task in sorted(tasks.items()):
        if not task.get("requirement_ids") and not task.get("design_basis"):
            findings.append(
                _finding(
                    "error",
                    "orphan_task",
                    "A task has no requirement or design basis.",
                    task_id,
                )
            )
    for phase_id, phase in sorted(phases.items()):
        if not phase.get("task_ids"):
            findings.append(
                _finding(
                    "error",
                    "empty_phase",
                    "A phase owns no tasks.",
                    phase_id,
                )
            )

    findings.sort(
        key=lambda item: (
            {"error": 0, "warning": 1, "info": 2}[item["severity"]],
            item["code"],
            tuple(item["targets"]),
            item["message"],
        )
    )
    for index, item in enumerate(findings, 1):
        item["finding_id"] = f"FIND-{index:03d}"
    return findings


def validation_status(findings: Sequence[Mapping[str, Any]]) -> str:
    if any(
        item.get("severity") == "error" and item.get("status") == "open"
        for item in findings
    ):
        return "fail"
    if any(
        item.get("severity") == "warning" and item.get("status") == "open"
        for item in findings
    ):
        return "unresolved"
    return "pass"


def refresh_validation(plan: dict[str, Any], checked_at: str | None = None) -> None:
    findings = quality_findings(plan)
    plan["validation"] = {
        "checked_revision": plan["revision"],
        "checked_at": checked_at or plan["updated_at"],
        "status": validation_status(findings),
        "findings": findings,
    }


def check_validation_snapshot(plan: Mapping[str, Any]) -> list[dict[str, Any]]:
    expected_findings = quality_findings(plan)
    expected_status = validation_status(expected_findings)
    stored = plan.get("validation", {})
    errors: list[dict[str, Any]] = []
    if stored.get("status") != expected_status:
        _schema_error(
            errors,
            "validation_drift",
            "Stored validation status does not match current canonical state.",
            "validation.status",
        )
    if stored.get("findings") != expected_findings:
        _schema_error(
            errors,
            "validation_drift",
            "Stored validation findings do not match current canonical state.",
            "validation.findings",
        )
    return errors


def ensure_structurally_valid(
    plan: Any,
    context: Context,
    *,
    directory_name: str | None,
    input_context: bool,
    check_snapshot: bool = True,
) -> None:
    errors = validate_plan_structure(plan, context, directory_name=directory_name)
    if not errors and check_snapshot:
        errors = check_validation_snapshot(plan)
    if errors:
        category = "invalid_input" if input_context else "unsafe_or_corrupt"
        raise AppError(
            category,
            "The plan does not satisfy the canonical V1 contract.",
            details={"findings": errors},
        )


def readiness_findings(plan: Mapping[str, Any]) -> list[dict[str, Any]]:
    findings = quality_findings(plan)
    return [
        item
        for item in findings
        if item.get("status") == "open" and item.get("severity") in {"error", "warning"}
    ]


def is_positive_preservation_fact(value: Any) -> bool:
    """Require an affirmative preservation observation, not a negated match."""
    folded = " ".join(unicodedata.normalize("NFKC", str(value)).casefold().split())
    preservation_terms = (
        "unchanged",
        "preserved",
        "byte-identical",
        "sha256",
        "sha-256",
        "remained absent",
        "still absent",
        "not modified",
    )
    if not any(term in folded for term in preservation_terms):
        return False
    # "not modified" is an affirmative preservation phrase. Mask it before
    # looking for negative polarity around other preservation terms.
    polarity_text = folded.replace("not modified", "unmodified")
    for affirmative_negative_form, replacement in (
        ("no changes", "zero changes"),
        ("no change", "zero change"),
        ("no modifications", "zero modifications"),
        ("no modification", "zero modification"),
        ("no differences", "zero differences"),
        ("no difference", "zero difference"),
        ("no mismatch", "matching"),
    ):
        polarity_text = polarity_text.replace(
            affirmative_negative_form, replacement
        )
    negative_tokens = {
        "changed",
        "deleted",
        "different",
        "failed",
        "failure",
        "false",
        "incorrect",
        "incorrectly",
        "mismatch",
        "mismatched",
        "missing",
        "modified",
        "never",
        "no",
        "not",
        "removed",
        "unsuccessful",
        "unsuccessfully",
    }
    if set(re.findall(r"[a-z0-9]+", polarity_text)) & negative_tokens:
        return False
    negative = re.search(
        r"(?:"
        r"\b(?:not|never)\s+(?:been\s+)?(?:unchanged|preserved|byte[- ]identical|absent)\b|"
        r"\bno longer\s+(?:unchanged|preserved|byte[- ]identical|absent)\b|"
        r"\b(?:failed|failure|unable|cannot|could not)\b.{0,64}"
        r"\b(?:preserv\w*|unchanged|reinspect\w*|verif\w*|sha-?256)\b|"
        r"\b(?:preserv\w*|reinspect\w*|verif\w*)\b.{0,64}"
        r"\b(?:failed|failure|unable|cannot|could not)\b|"
        r"\b(?:preserved|unchanged|byte[- ]identical|sha-?256)\b\s*"
        r"(?:[:?=\-]\s*)?(?:false|no)\b|"
        r"\b(?:unsuccessful(?:ly)?|incorrect(?:ly)?)\b|"
        r"\b(?:changed unexpectedly|was changed|were changed|deleted|removed|"
        r"digest mismatch|sha-?256 mismatch)\b"
        r")",
        polarity_text,
    )
    return negative is None


def completion_findings(plan: Mapping[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    digest_context = build_target_digest_context(plan)
    requirements = {
        item["requirement_id"]: item
        for item in plan.get("requirements", [])
        if isinstance(item, dict) and isinstance(item.get("requirement_id"), str)
    }
    coverage_edges = {
        item["requirement_id"]: item
        for item in plan.get("coverage", {}).get("requirement_to_task", [])
        if isinstance(item, dict) and isinstance(item.get("requirement_id"), str)
    }
    for task in plan.get("tasks", []):
        if not isinstance(task, dict):
            continue
        task_id = str(task.get("task_id", ""))
        if not _is_enum_value(task.get("status"), {"completed", "skipped"}):
            findings.append(
                _finding(
                    "error",
                    "task_incomplete",
                    "A required task is not completed or skipped.",
                    task_id,
                )
            )
        elif task.get("status") == "completed" and missing_criterion_evidence(
            task.get("acceptance_criteria", []),
            task.get("evidence"),
            target_definition_digest(task, "task", plan, digest_context),
        ):
            findings.append(
                _finding(
                    "error",
                    "task_evidence_gap",
                    "A completed task lacks evidence for every acceptance criterion.",
                    task_id,
                )
            )
        elif task.get("status") == "skipped":
            for requirement_id in task.get("requirement_ids", []):
                requirement = requirements.get(requirement_id, {})
                edge = coverage_edges.get(requirement_id, {})
                if (
                    requirement.get("status") != "dispositioned"
                    or requirement.get("disposition") is None
                    or edge.get("disposition") is None
                ):
                    findings.append(
                        _finding(
                            "error",
                            "skip_coverage_not_disposed",
                            "A skipped task retains requirement coverage without an accepted disposition.",
                            task_id,
                            requirement_id,
                        )
                    )
        if missing_verification_reports(
            task.get("verification_steps", []),
            task.get("evidence"),
            target_definition_digest(task, "task", plan, digest_context),
        ):
            findings.append(
                _finding(
                    "error",
                    "verification_step_unreported",
                    "A task has planned verification steps without a result or not-exercised evidence record.",
                    task_id,
                )
            )
    for requirement_id, requirement in sorted(requirements.items()):
        if requirement.get("status") == "active":
            findings.append(
                _finding(
                    "error",
                    "requirement_unsatisfied",
                    "An active requirement is not satisfied or dispositioned.",
                    requirement_id,
                )
            )
        elif requirement.get("status") == "satisfied" and missing_criterion_evidence(
            requirement.get("acceptance_criteria", []),
            requirement.get("evidence"),
            target_definition_digest(
                requirement, "requirement", plan, digest_context
            ),
        ):
            findings.append(
                _finding(
                    "error",
                    "requirement_evidence_gap",
                    "A requirement lacks evidence for every acceptance criterion.",
                    requirement_id,
                )
            )
    current_observation_times: list[dt.datetime] = []
    for collection, target_kind in (
        (plan.get("tasks", []), "task"),
        (plan.get("requirements", []), "requirement"),
    ):
        for target in collection:
            if not isinstance(target, Mapping):
                continue
            if target_kind == "task" and target.get("completed_at") is not None:
                try:
                    current_observation_times.append(
                        parse_timestamp(target.get("completed_at"), "completed_at")
                    )
                except ValueError:
                    pass
            digest = target_definition_digest(
                target, target_kind, plan, digest_context
            )
            for evidence in target.get("evidence", []):
                if not isinstance(evidence, Mapping) or evidence.get("target_digest") != digest:
                    continue
                try:
                    current_observation_times.append(
                        parse_timestamp(evidence.get("timestamp"), "evidence.timestamp")
                    )
                except ValueError:
                    pass
    cutoff = max(current_observation_times) if current_observation_times else None
    project = plan.get("project", {})
    inspected_at: dt.datetime | None = None
    try:
        inspected_at = parse_timestamp(project.get("inspected_at"), "project.inspected_at")
    except ValueError:
        pass
    current_facts: list[Mapping[str, Any]] = []
    for fact in project.get("baseline_facts", []):
        if not isinstance(fact, Mapping):
            continue
        try:
            observed_at = parse_timestamp(fact.get("observed_at"), "baseline fact")
        except ValueError:
            continue
        if cutoff is None or observed_at > cutoff:
            current_facts.append(fact)
    if (
        inspected_at is None
        or (cutoff is not None and inspected_at <= cutoff)
        or not current_facts
    ):
        findings.append(
            _finding(
                "error",
                "final_project_reinspection_missing",
                "The final project state was not reinspected after current implementation evidence.",
                "project.inspected_at",
                "project.baseline_facts",
            )
        )
    for preserved_path in project.get("preserved_paths", []):
        preserved_text = str(preserved_path).strip()
        if not preserved_text:
            continue
        preserved_candidate = Path(preserved_text)
        expected_locators = {
            os.path.normpath(preserved_text),
            os.path.normpath(
                str(
                    preserved_candidate
                    if preserved_candidate.is_absolute()
                    else Path(str(project.get("root_hint", ""))) / preserved_candidate
                )
            ),
        }
        if not any(
            os.path.normpath(str(fact.get("evidence_locator", "")).strip())
            in expected_locators
            and is_positive_preservation_fact(fact.get("fact", ""))
            for fact in current_facts
        ):
            findings.append(
                _finding(
                    "error",
                    "protected_path_reinspection_missing",
                    "A protected path lacks a current final reinspection record.",
                    str(preserved_path),
                )
            )
    findings.extend(readiness_findings(plan))
    findings.sort(key=lambda item: (item["code"], tuple(item["targets"])))
    for index, finding in enumerate(findings, 1):
        finding["finding_id"] = f"FIND-{index:03d}"
    return findings


@dataclasses.dataclass(frozen=True)
class PlanRecord:
    directory: str
    path: Path
    canonical_path: Path
    plan: dict[str, Any]
    raw: bytes
    sha256: str
    directory_identity: tuple[int, int]


def load_plan_record(context: Context, plan_dir: Path) -> PlanRecord:
    ensure_no_symlink_components(context.project_root, plan_dir, "managed plan directory")
    try:
        directory_info = plan_dir.lstat()
    except OSError as exc:
        raise AppError("io_error", "Cannot inspect a managed plan directory.") from exc
    if stat.S_ISLNK(directory_info.st_mode) or not stat.S_ISDIR(directory_info.st_mode):
        raise AppError("unsafe_or_corrupt", "A managed plan path is not a safe directory.")
    canonical_path = plan_dir / "plan.json"
    try:
        raw = read_bounded_regular_file(canonical_path, label="canonical plan")
        plan = decode_json_bytes(raw, "canonical plan")
    except AppError as exc:
        if exc.category in {"not_found", "invalid_input"}:
            raise AppError(
                "unsafe_or_corrupt",
                "A managed plan has malformed or unreadable canonical state.",
                details={"directory": plan_dir.name},
            ) from exc
        raise
    if not isinstance(plan, dict):
        raise AppError(
            "unsafe_or_corrupt",
            "A managed plan canonical file does not contain an object.",
            details={"directory": plan_dir.name},
        )
    guard_prohibited_content(plan)
    ensure_structurally_valid(
        plan,
        context,
        directory_name=plan_dir.name,
        input_context=False,
        check_snapshot=True,
    )
    expected = canonical_bytes(plan)
    if raw != expected:
        raise AppError(
            "unsafe_or_corrupt",
            "A managed plan canonical file is not in deterministic canonical form.",
            details={"directory": plan_dir.name},
        )
    return PlanRecord(
        directory=plan_dir.name,
        path=plan_dir,
        canonical_path=canonical_path,
        plan=plan,
        raw=raw,
        sha256=sha256_bytes(raw),
        directory_identity=(directory_info.st_dev, directory_info.st_ino),
    )


def discover_managed_plans(context: Context) -> tuple[list[PlanRecord], list[str]]:
    """Discover only managed directories; any corrupt managed record fails closed."""
    if not context.plans_root.exists():
        return [], []
    records: list[PlanRecord] = []
    unmanaged: list[str] = []
    try:
        entries = sorted(context.plans_root.iterdir(), key=lambda item: item.name)
    except OSError as exc:
        raise AppError("io_error", "Cannot read the plans catalog.") from exc
    for entry in entries:
        if entry.name in {"INDEX.md", ".to-implementation-plan.catalog.lock"}:
            continue
        try:
            info = entry.lstat()
        except OSError as exc:
            raise AppError("io_error", "Cannot inspect a catalog entry.") from exc
        if stat.S_ISLNK(info.st_mode):
            unmanaged.append(entry.name)
            continue
        if not stat.S_ISDIR(info.st_mode) or not DIRECTORY_RE.fullmatch(entry.name):
            unmanaged.append(entry.name)
            continue
        canonical = entry / "plan.json"
        try:
            canonical.lstat()
        except FileNotFoundError:
            unmanaged.append(entry.name)
            continue
        except OSError as exc:
            raise AppError("io_error", "Cannot inspect a canonical plan path.") from exc
        records.append(load_plan_record(context, entry))
    seen_plan_ids: dict[str, str] = {}
    for record in records:
        plan_id = record.plan["plan_id"]
        if plan_id in seen_plan_ids:
            raise AppError(
                "unsafe_or_corrupt",
                "The catalog contains duplicate plan identities.",
                details={"directories": sorted([seen_plan_ids[plan_id], record.directory])},
            )
        seen_plan_ids[plan_id] = record.directory
    records.sort(key=lambda item: item.plan["plan_id"])
    return records, unmanaged


def validate_selector_text(selector: str) -> None:
    if not selector or len(selector) > MAX_TITLE_CHARS:
        raise AppError("invalid_input", "Plan selector is blank or too long.")
    if any(ord(character) < 32 or ord(character) == 127 for character in selector):
        raise AppError("unsafe_or_corrupt", "Plan selector contains a control character.")
    if "/" in selector or "\\" in selector or selector.startswith("."):
        raise AppError("unsafe_or_corrupt", "Plan selector has an unsafe path form.")
    if any(segment in {".", ".."} for segment in re.split(r"[./\\]", selector)):
        raise AppError("unsafe_or_corrupt", "Plan selector has a traversal form.")


def select_plan(context: Context, selector: str) -> PlanRecord:
    validate_selector_text(selector)
    records, _ = discover_managed_plans(context)
    id_matches = [item for item in records if item.plan["plan_id"] == selector]
    if id_matches:
        return id_matches[0]
    directory_matches = [item for item in records if item.directory == selector]
    if directory_matches:
        return directory_matches[0]
    title_matches = [
        item for item in records if item.plan["title"].casefold() == selector.casefold()
    ]
    if len(title_matches) == 1:
        return title_matches[0]
    if len(title_matches) > 1:
        raise AppError(
            "ambiguous_selector",
            "The complete title matches more than one managed plan.",
            details={
                "candidates": [
                    {"plan_id": item.plan["plan_id"], "directory": item.directory}
                    for item in title_matches
                ]
            },
        )
    raise AppError("not_found", "No managed plan matches the exact selector.")


def numeric_id_key(identifier: str) -> tuple[str, int, str]:
    match = re.fullmatch(r"([A-Za-z]+)-(\d+)", identifier)
    if match:
        return (match.group(1), int(match.group(2)), identifier)
    return (identifier, 0, identifier)


def md_cell(value: Any) -> str:
    if value is None or value == "":
        return "None"
    if isinstance(value, list):
        if not value:
            return "None"
        value = ", ".join(str(item) for item in value)
    text = str(value)
    text = text.replace("\\", "\\\\").replace("|", "\\|")
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")
    text = text.replace("<", "&lt;").replace(">", "&gt;")
    return text


def md_block(value: Any) -> str:
    if value is None or value == "":
        return "None"
    text = str(value).replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("<", "&lt;").replace(">", "&gt;")
    return text


def md_list(values: Sequence[Any]) -> str:
    if not values:
        return "- None"
    return "\n".join(f"- {md_block(value)}" for value in values)


def disposition_text(value: Any) -> str:
    if not isinstance(value, dict):
        return "None"
    return f"{value.get('kind')}: {value.get('reason')} (authority: {value.get('authority_basis')})"


def render_plan_overview(record: PlanRecord) -> bytes:
    plan = record.plan
    project = plan["project"]
    objective = plan["objective"]
    scope = plan["scope"]
    lines: list[str] = [
        "<!-- Generated by to-implementation-plan. plan.json is canonical. -->",
        "",
        f"# {md_block(plan['title'])}",
        "",
        "## Plan identity",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Plan ID | `{md_cell(plan['plan_id'])}` |",
        f"| Status | `{md_cell(plan['status'])}` |",
        f"| Status reason | {md_cell(plan['status_reason'])} |",
        f"| Revision | {plan['revision']} |",
        f"| Created | {md_cell(plan['created_at'])} |",
        f"| Updated | {md_cell(plan['updated_at'])} |",
        f"| Initial record IDs | {md_cell(plan['initial_record_ids'])} |",
        f"| Canonical SHA-256 | `{record.sha256}` |",
        f"| Managed directory | `{md_cell(record.directory)}` |",
        "",
        "## Objective",
        "",
        md_block(objective["summary"]),
        "",
        f"User value: {md_block(objective['user_value'])}",
        "",
        "### Success outcomes",
        "",
        md_list(objective["success_outcomes"]),
        "",
        "## Scope",
        "",
        "### In scope",
        "",
        md_list(scope["in_scope"]),
        "",
        "### Out of scope",
        "",
        md_list(scope["out_of_scope"]),
        "",
        "### Execution authority",
        "",
        md_block(scope["execution_authority"]),
        "",
        "## Project baseline",
        "",
        f"Root hint: `{md_cell(project['root_hint'])}`",
        "",
        f"Inspected: {md_cell(project['inspected_at'])}",
        "",
        "### Guidance inspected",
        "",
        "| Path | Observed | Digest | Summary |",
        "| --- | --- | --- | --- |",
    ]
    guidance = sorted(project["guidance"], key=lambda item: (item["path"], item["observed_at"]))
    lines.extend(
        f"| {md_cell(item['path'])} | {md_cell(item['observed_at'])} | {md_cell(item['digest'])} | {md_cell(item['summary'])} |"
        for item in guidance
    )
    if not guidance:
        lines.append("| None | None | None | None |")
    lines += [
        "",
        "### Observed facts",
        "",
        "| Fact | Evidence | Observed |",
        "| --- | --- | --- |",
    ]
    facts = sorted(
        project["baseline_facts"],
        key=lambda item: (item["fact"], item["evidence_locator"], item["observed_at"]),
    )
    lines.extend(
        f"| {md_cell(item['fact'])} | {md_cell(item['evidence_locator'])} | {md_cell(item['observed_at'])} |"
        for item in facts
    )
    if not facts:
        lines.append("| None | None | None |")
    for heading, key in (
        ("Constraints", "constraints"),
        ("Preserved paths", "preserved_paths"),
        ("Evidence gaps", "evidence_gaps"),
    ):
        lines += ["", f"### {heading}", "", md_list(project[key])]
    lines += [
        "",
        "## Sources",
        "",
        "| Source | Kind | Title | Locator | Accessed | Digest | Inspection method | Limitations |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    sources = sorted(plan["sources"], key=lambda item: numeric_id_key(item["source_id"]))
    lines.extend(
        f"| `{md_cell(item['source_id'])}` | {md_cell(item['kind'])} | {md_cell(item['title'])} | {md_cell(item['locator'])} | {md_cell(item['accessed_at'])} | {md_cell(item['digest'])} | {md_cell(item['inspection_method'])} | {md_cell(item['access_limitations'])} |"
        for item in sources
    )
    if not sources:
        lines.append("| None | None | None | None | None | None | None | None |")
    lines += [
        "",
        "## Requirements",
        "",
        "| Requirement | Outcome | Status | Sources | Evidence count |",
        "| --- | --- | --- | --- | ---: |",
    ]
    requirements = sorted(plan["requirements"], key=lambda item: item["requirement_id"].casefold())
    lines.extend(
        f"| `{md_cell(item['requirement_id'])}` | {md_cell(item['outcome'])} | `{md_cell(item['status'])}` | {md_cell(item['source_ids'])} | {len(item['evidence'])} |"
        for item in requirements
    )
    if not requirements:
        lines.append("| None | None | None | None | 0 |")
    lines += [
        "",
        "## Decisions",
        "",
        "| Decision | Status | Statement | Authority |",
        "| --- | --- | --- | --- |",
    ]
    decisions = sorted(plan["decisions"], key=lambda item: numeric_id_key(item["decision_id"]))
    lines.extend(
        f"| `{md_cell(item['decision_id'])}` | `{md_cell(item['status'])}` | {md_cell(item['statement'])} | {md_cell(item['authority_basis'])} |"
        for item in decisions
    )
    if not decisions:
        lines.append("| None | None | None | None |")
    lines += [
        "",
        "## Open questions",
        "",
        "| Question | Status | Affects | Answer |",
        "| --- | --- | --- | --- |",
    ]
    questions = sorted(plan["open_questions"], key=lambda item: numeric_id_key(item["question_id"]))
    lines.extend(
        f"| `{md_cell(item['question_id'])}` | `{md_cell(item['status'])}` | {md_cell(item['affects'])} | {md_cell(item['answer'])} |"
        for item in questions
    )
    if not questions:
        lines.append("| None | None | None | None |")
    lines += [
        "",
        "## Assumptions",
        "",
        "| Assumption | Status | Statement | Basis |",
        "| --- | --- | --- | --- |",
    ]
    assumptions = sorted(plan["assumptions"], key=lambda item: numeric_id_key(item["assumption_id"]))
    lines.extend(
        f"| `{md_cell(item['assumption_id'])}` | `{md_cell(item['status'])}` | {md_cell(item['statement'])} | {md_cell(item['basis'])} |"
        for item in assumptions
    )
    if not assumptions:
        lines.append("| None | None | None | None |")
    lines += [
        "",
        "## Phase summary",
        "",
        "| Phase | Title | Status | Depends on | Tasks |",
        "| --- | --- | --- | --- | ---: |",
    ]
    phases = sorted(plan["phases"], key=lambda item: numeric_id_key(item["phase_id"]))
    lines.extend(
        f"| `{md_cell(item['phase_id'])}` | {md_cell(item['title'])} | `{md_cell(item['status'])}` | {md_cell(item['depends_on_phase_ids'])} | {len(item['task_ids'])} |"
        for item in phases
    )
    if not phases:
        lines.append("| None | None | None | None | 0 |")
    validation = plan["validation"]
    lines += [
        "",
        "## Latest validation",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Checked revision | {validation['checked_revision']} |",
        f"| Checked at | {md_cell(validation['checked_at'])} |",
        f"| Result | `{md_cell(validation['status'])}` |",
        "",
        "| Finding | Severity | Status | Code | Targets | Message |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    lines.extend(
        f"| `{md_cell(item['finding_id'])}` | {md_cell(item['severity'])} | {md_cell(item['status'])} | `{md_cell(item['code'])}` | {md_cell(item['targets'])} | {md_cell(item['message'])} |"
        for item in validation["findings"]
    )
    if not validation["findings"]:
        lines.append("| None | None | None | None | None | None |")
    lines += [
        "",
        "## Recent history",
        "",
        "| Revision | Timestamp | Action | Affected IDs | Status change | Summary | Authority |",
        "| ---: | --- | --- | --- | --- | --- | --- |",
    ]
    history = sorted(plan["history"], key=lambda item: item["revision"])
    lines.extend(
        f"| {item['revision']} | {md_cell(item['timestamp'])} | `{md_cell(item['action_id'])}` | {md_cell(item['affected_ids'])} | {md_cell(item['status_before'])} -> {md_cell(item['status_after'])} | {md_cell(item['summary'])} | {md_cell(item['authority_basis'])} |"
        for item in history
    )
    if not history:
        lines.append("| None | None | None | None | None | None | None |")
    return ("\n".join(lines) + "\n").encode("utf-8")


def render_phase(plan: Mapping[str, Any], phase: Mapping[str, Any]) -> bytes:
    tasks_by_id = {
        item["task_id"]: item
        for item in plan["tasks"]
        if isinstance(item, dict) and isinstance(item.get("task_id"), str)
    }
    tasks = [tasks_by_id[task_id] for task_id in phase["task_ids"] if task_id in tasks_by_id]
    tasks.sort(key=lambda item: numeric_id_key(item["task_id"]))
    lines: list[str] = [
        "<!-- Generated by to-implementation-plan. plan.json is canonical. -->",
        "",
        f"# {md_block(phase['phase_id'])} - {md_block(phase['title'])}",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Plan | `{md_cell(plan['plan_id'])}` |",
        f"| Phase status | `{md_cell(phase['status'])}` |",
        f"| Depends on | {md_cell(phase['depends_on_phase_ids'])} |",
        f"| Canonical revision | {plan['revision']} |",
        "",
        "## Objective",
        "",
        md_block(phase["objective"]),
        "",
        "## Scope",
        "",
        md_list(phase["scope"]),
        "",
        "## Entry conditions",
        "",
        md_list(phase["entry_conditions"]),
        "",
        "## Exit criteria",
        "",
        md_list(phase["exit_criteria"]),
        "",
        "## Risks",
        "",
        md_list(phase["risks"]),
        "",
        "## Task summary",
        "",
        "| Task | Title | Status | Requirements | Depends on | Parallel group |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    lines.extend(
        f"| `{md_cell(task['task_id'])}` | {md_cell(task['title'])} | `{md_cell(task['status'])}` | {md_cell(task['requirement_ids'])} | {md_cell(task['dependencies'])} | {md_cell(task['parallel_group'])} |"
        for task in tasks
    )
    if not tasks:
        lines.append("| None | None | None | None | None | None |")
    for task in tasks:
        reason = task["blocker_reason"] or task["pause_reason"] or task["skip_reason"]
        lines += [
            "",
            f"## {md_block(task['task_id'])} - {md_block(task['title'])}",
            "",
            md_block(task["action"]),
            "",
            "| Field | Value |",
            "| --- | --- |",
            f"| Status | `{md_cell(task['status'])}` |",
            f"| State reason | {md_cell(reason)} |",
            f"| Skip authority | {md_cell(task['skip_authority'])} |",
            f"| Requirements | {md_cell(task['requirement_ids'])} |",
            f"| Design basis | {md_cell(task['design_basis'])} |",
            f"| Target artifacts | {md_cell(task['target_artifacts'])} |",
            f"| Dependencies | {md_cell(task['dependencies'])} |",
            f"| Parallel group | {md_cell(task['parallel_group'])} |",
            f"| Completed at | {md_cell(task['completed_at'])} |",
            "",
            "### Risks",
            "",
            md_list(task["risks"]),
            "",
            "### Acceptance criteria",
            "",
            md_list(task["acceptance_criteria"]),
            "",
            "### Planned verification",
            "",
            md_list(task["verification_steps"]),
            "",
            "### Evidence",
            "",
            "| Evidence | Timestamp | Type | Result status | Verification level | Source | Target digest | Description | Result | Locator or command |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
        evidence = sorted(
            task["evidence"],
            key=lambda item: (
                parse_timestamp(item["timestamp"], "evidence timestamp").astimezone(
                    dt.timezone.utc
                ),
                numeric_id_key(item["evidence_id"]),
            ),
        )
        lines.extend(
            f"| `{md_cell(item['evidence_id'])}` | {md_cell(item['timestamp'])} | {md_cell(item['evidence_type'])} | {md_cell(item['result_status'])} | {md_cell(item['verification_level'])} | {md_cell(item['observation_source'])} | {md_cell(item['target_digest'])} | {md_cell(item['description'])} | {md_cell(item['observed_result'])} | {md_cell(item['locator_or_command'])} |"
            for item in evidence
        )
        if not evidence:
            lines.append("| None | None | None | None | None | None | None | None | None | None |")
    return ("\n".join(lines) + "\n").encode("utf-8")


def render_traceability(record: PlanRecord) -> bytes:
    plan = record.plan
    requirements = {
        item["requirement_id"]: item for item in plan["requirements"]
    }
    lines: list[str] = [
        "<!-- Generated by to-implementation-plan. plan.json is canonical. -->",
        "",
        f"# Traceability for {md_block(plan['plan_id'])}",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Plan title | {md_cell(plan['title'])} |",
        f"| Plan status | `{md_cell(plan['status'])}` |",
        f"| Canonical revision | {plan['revision']} |",
        f"| Validation result | `{md_cell(plan['validation']['status'])}` |",
        "",
        "## Source to requirement",
        "",
        "| Source | Requirements | Disposition |",
        "| --- | --- | --- |",
    ]
    source_edges = sorted(
        plan["coverage"]["source_to_requirement"],
        key=lambda item: numeric_id_key(item["source_id"]),
    )
    lines.extend(
        f"| `{md_cell(item['source_id'])}` | {md_cell(item['requirement_ids'])} | {md_cell(disposition_text(item['disposition']))} |"
        for item in source_edges
    )
    if not source_edges:
        lines.append("| None | None | None |")
    lines += [
        "",
        "## Requirement to task",
        "",
        "| Requirement | Tasks | Disposition |",
        "| --- | --- | --- |",
    ]
    requirement_edges = sorted(
        plan["coverage"]["requirement_to_task"],
        key=lambda item: item["requirement_id"].casefold(),
    )
    lines.extend(
        f"| `{md_cell(item['requirement_id'])}` | {md_cell(item['task_ids'])} | {md_cell(disposition_text(item['disposition']))} |"
        for item in requirement_edges
    )
    if not requirement_edges:
        lines.append("| None | None | None |")
    lines += [
        "",
        "## Requirement acceptance and evidence",
        "",
        "| Requirement | Acceptance criteria | Status | Evidence | Open finding |",
        "| --- | --- | --- | --- | --- |",
    ]
    open_findings_by_target: dict[str, list[str]] = {}
    for finding in plan["validation"]["findings"]:
        if finding["status"] == "open":
            for target in finding["targets"]:
                open_findings_by_target.setdefault(target, []).append(finding["code"])
    for requirement_id, requirement in sorted(requirements.items(), key=lambda item: item[0].casefold()):
        lines.append(
            f"| `{md_cell(requirement_id)}` | {md_cell(requirement['acceptance_criteria'])} | `{md_cell(requirement['status'])}` | {len(requirement['evidence'])} | {md_cell(sorted(open_findings_by_target.get(requirement_id, [])))} |"
        )
    if not requirements:
        lines.append("| None | None | None | 0 | None |")
    lines += [
        "",
        "## Reverse task basis",
        "",
        "| Task | Phase | Requirements | Design basis | Coverage result |",
        "| --- | --- | --- | --- | --- |",
    ]
    for task in sorted(plan["tasks"], key=lambda item: numeric_id_key(item["task_id"])):
        coverage_result = "mapped" if task["requirement_ids"] or task["design_basis"] else "orphan"
        lines.append(
            f"| `{md_cell(task['task_id'])}` | `{md_cell(task['phase_id'])}` | {md_cell(task['requirement_ids'])} | {md_cell(task['design_basis'])} | {coverage_result} |"
        )
    if not plan["tasks"]:
        lines.append("| None | None | None | None | None |")
    lines += [
        "",
        "## Coverage findings",
        "",
        "| Finding | Severity | Status | Code | Targets | Message |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    coverage_codes = {
        "no_sources",
        "no_requirements",
        "no_phases",
        "no_tasks",
        "missing_source_coverage",
        "uncovered_source",
        "orphan_source_coverage",
        "missing_requirement_coverage",
        "coverage_mismatch",
        "uncovered_requirement",
        "missing_coverage_disposition",
        "orphan_requirement_coverage",
        "orphan_task",
        "empty_phase",
    }
    coverage_findings = [
        item for item in plan["validation"]["findings"] if item["code"] in coverage_codes
    ]
    lines.extend(
        f"| `{md_cell(item['finding_id'])}` | {md_cell(item['severity'])} | {md_cell(item['status'])} | `{md_cell(item['code'])}` | {md_cell(item['targets'])} | {md_cell(item['message'])} |"
        for item in coverage_findings
    )
    if not coverage_findings:
        lines.append("| None | None | None | None | None | None |")
    return ("\n".join(lines) + "\n").encode("utf-8")


def expected_plan_projections(record: PlanRecord) -> dict[Path, bytes]:
    projections: dict[Path, bytes] = {
        record.path / "PLAN.md": render_plan_overview(record),
        record.path / "TRACEABILITY.md": render_traceability(record),
    }
    for phase in sorted(record.plan["phases"], key=lambda item: numeric_id_key(item["phase_id"])):
        filename = f"{phase['phase_id']}_{safe_slug(phase['title'], 'phase')}.md"
        projections[record.path / "phases" / filename] = render_phase(record.plan, phase)
    return projections


def projection_paths_for_plan(
    plan_dir: Path, plan: Mapping[str, Any]
) -> list[Path]:
    paths = [plan_dir / "PLAN.md", plan_dir / "TRACEABILITY.md"]
    for phase in sorted(
        list_or_empty(plan.get("phases")),
        key=lambda item: numeric_id_key(str(item.get("phase_id", "")))
        if isinstance(item, Mapping)
        else (1, str(item)),
    ):
        if not isinstance(phase, Mapping):
            continue
        filename = (
            f"{phase.get('phase_id')}_"
            f"{safe_slug(str(phase.get('title', '')), 'phase')}.md"
        )
        paths.append(plan_dir / "phases" / filename)
    return paths


def preflight_projection_destinations(
    plan_dir: Path, plan: Mapping[str, Any]
) -> None:
    """Refuse every existing projection destination without our marker."""
    phases_dir = plan_dir / "phases"
    try:
        phases_info = phases_dir.lstat()
    except FileNotFoundError:
        phases_info = None
    except OSError as exc:
        raise AppError("io_error", "Cannot inspect the phases projection path.") from exc
    if phases_info is not None and (
        stat.S_ISLNK(phases_info.st_mode) or not stat.S_ISDIR(phases_info.st_mode)
    ):
        raise AppError("unsafe_or_corrupt", "The phases projection path is unsafe.")
    collisions: list[str] = []
    for path in projection_paths_for_plan(plan_dir, plan):
        try:
            info = path.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise AppError("io_error", "Cannot inspect a projection destination.") from exc
        if (
            stat.S_ISLNK(info.st_mode)
            or not stat.S_ISREG(info.st_mode)
            or not is_generated_projection(path)
        ):
            collisions.append(str(path.relative_to(plan_dir)))
    if collisions:
        raise AppError(
            "unsafe_or_corrupt",
            "One or more projection destinations are unmanaged and will not be overwritten.",
            details={"targets": sorted(collisions)},
        )


def inspect_projection_drift(record: PlanRecord) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    expected = expected_plan_projections(record)
    for path, data in sorted(expected.items(), key=lambda item: str(item[0])):
        try:
            info = path.lstat()
        except FileNotFoundError:
            findings.append(
                _finding(
                    "error",
                    "missing_projection",
                    "A generated projection is missing.",
                    str(path.relative_to(record.path)),
                )
            )
            continue
        except OSError as exc:
            raise AppError("io_error", "Cannot inspect a generated projection.") from exc
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            findings.append(
                _finding(
                    "error",
                    "unsafe_projection",
                    "A generated projection path is not a regular file.",
                    str(path.relative_to(record.path)),
                )
            )
            continue
        if info.st_size != len(data) or sha256_file(path) != sha256_bytes(data):
            findings.append(
                _finding(
                    "error",
                    "projection_drift",
                    "A generated projection differs from canonical state.",
                    str(path.relative_to(record.path)),
                )
            )
    phases_dir = record.path / "phases"
    if phases_dir.exists():
        try:
            info = phases_dir.lstat()
        except OSError as exc:
            raise AppError("io_error", "Cannot inspect the phases projection directory.") from exc
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            findings.append(
                _finding(
                    "error",
                    "unsafe_projection",
                    "The phases projection path is not a regular directory.",
                    "phases",
                )
            )
        else:
            expected_names = {path.name for path in expected if path.parent == phases_dir}
            for path in sorted(phases_dir.iterdir(), key=lambda item: item.name):
                if (
                    GENERATED_PHASE_FILE_RE.fullmatch(path.name)
                    and path.name not in expected_names
                    and is_generated_projection(path)
                ):
                    findings.append(
                        _finding(
                            "error",
                            "obsolete_projection",
                            "An obsolete generated phase projection remains.",
                            f"phases/{path.name}",
                        )
                    )
    findings.sort(key=lambda item: (item["code"], tuple(item["targets"])))
    for index, item in enumerate(findings, 1):
        item["finding_id"] = f"FIND-P{index:03d}"
    return findings


def write_plan_projections(record: PlanRecord) -> list[str]:
    """Publish only generated files for one valid plan; return changed relatives."""
    preflight_projection_destinations(record.path, record.plan)
    expected = expected_plan_projections(record)
    phases_dir = record.path / "phases"
    changed: list[str] = []
    record_fd = open_directory_without_symlinks(
        record.path, label="managed plan directory"
    )
    record_info = os.fstat(record_fd)
    if (record_info.st_dev, record_info.st_ino) != record.directory_identity:
        os.close(record_fd)
        raise AppError(
            "unsafe_or_corrupt",
            "The managed plan directory changed before projection publication.",
        )
    phases_fd: int | None = None
    try:
        try:
            phases_info = os.stat("phases", dir_fd=record_fd, follow_symlinks=False)
        except FileNotFoundError:
            phases_info = None
        except OSError as exc:
            raise AppError("io_error", "Cannot inspect the phases projection path.") from exc
        if phases_info is not None and (
            stat.S_ISLNK(phases_info.st_mode) or not stat.S_ISDIR(phases_info.st_mode)
        ):
            raise AppError("unsafe_or_corrupt", "The phases projection path is unsafe.")
        if phases_info is None:
            created_phases_dir = False
            try:
                os.mkdir("phases", mode=0o700, dir_fd=record_fd)
                created_phases_dir = True
                changed.append("phases/")
                os.fsync(record_fd)
            except OSError as exc:
                raise AppError(
                    "io_error",
                    "Cannot create the phases projection directory.",
                    details={
                        "generated_files_changed": ["phases/"]
                        if created_phases_dir
                        else []
                    },
                ) from exc
        phases_fd = os.open(
            "phases",
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
            dir_fd=record_fd,
        )
        phases_bound = os.fstat(phases_fd)
        phases_identity = (phases_bound.st_dev, phases_bound.st_ino)
        for path, data in sorted(expected.items(), key=lambda item: str(item[0])):
            relative = str(path.relative_to(record.path))
            expected_identity = (
                phases_identity if path.parent == phases_dir else record.directory_identity
            )
            try:
                if atomic_write_bytes(
                    path,
                    data,
                    expected_parent_identity=expected_identity,
                    required_existing_prefix=GENERATED_PROJECTION_MARKER,
                ):
                    changed.append(relative)
            except AppError as exc:
                if exc.details.get("replacement_completed"):
                    changed.append(relative)
                exc.details["generated_files_changed"] = sorted(set(changed))
                raise
        expected_names = {path.name for path in expected if path.parent == phases_dir}
        try:
            phase_names = sorted(os.listdir(phases_fd))
        except OSError as exc:
            raise AppError(
                "io_error",
                "Cannot inspect generated phase projections.",
                details={"generated_files_changed": sorted(set(changed))},
            ) from exc
        for name in phase_names:
            if not GENERATED_PHASE_FILE_RE.fullmatch(name) or name in expected_names:
                continue
            candidate_fd: int | None = None
            try:
                candidate_fd = os.open(
                    name,
                    os.O_RDONLY | os.O_NOFOLLOW,
                    dir_fd=phases_fd,
                )
                candidate_info = os.fstat(candidate_fd)
                generated = stat.S_ISREG(candidate_info.st_mode) and (
                    os.read(candidate_fd, len(GENERATED_PROJECTION_MARKER))
                    == GENERATED_PROJECTION_MARKER
                )
            except FileNotFoundError:
                continue
            except OSError as exc:
                if exc.errno == errno.ELOOP:
                    continue
                raise AppError(
                    "io_error",
                    "Cannot inspect a possible obsolete generated projection.",
                    details={"generated_files_changed": sorted(set(changed))},
                ) from exc
            finally:
                if candidate_fd is not None:
                    os.close(candidate_fd)
            if not generated:
                continue
            try:
                fresh_phases_fd = open_directory_without_symlinks(
                    phases_dir, label="phases projection directory"
                )
                try:
                    current_phases = os.fstat(fresh_phases_fd)
                finally:
                    os.close(fresh_phases_fd)
                if (current_phases.st_dev, current_phases.st_ino) != phases_identity:
                    raise AppError(
                        "unsafe_or_corrupt",
                        "The phases directory changed before obsolete projection removal.",
                        details={"generated_files_changed": sorted(set(changed))},
                    )
                os.unlink(name, dir_fd=phases_fd)
                changed.append(f"phases/{name}")
                os.fsync(phases_fd)
            except AppError:
                raise
            except OSError as exc:
                raise AppError(
                    "io_error",
                    "Cannot remove an obsolete generated projection.",
                    details={"generated_files_changed": sorted(set(changed))},
                ) from exc
        return sorted(changed)
    finally:
        if phases_fd is not None:
            os.close(phases_fd)
        os.close(record_fd)


def is_generated_projection(path: Path) -> bool:
    """Return true only for a regular file carrying this helper's ownership marker."""
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise AppError("io_error", "Cannot inspect a possible generated projection.") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        return False
    descriptor, _ = open_regular_file_without_symlinks(
        path if path.is_absolute() else Path(os.path.abspath(path)),
        label="possible generated projection",
    )
    try:
        return os.read(descriptor, len(GENERATED_PROJECTION_MARKER)) == GENERATED_PROJECTION_MARKER
    except OSError as exc:
        raise AppError("io_error", "Cannot read a possible generated projection.") from exc
    finally:
        os.close(descriptor)


def render_index(records: Sequence[PlanRecord]) -> bytes:
    lines = [
        "<!-- Generated by to-implementation-plan. plan.json is canonical. -->",
        "",
        "# Tracked implementation plans",
        "",
        "| Plan ID | Title | Status | Revision | Updated | Directory | Phases | Tasks | Validation |",
        "| --- | --- | --- | ---: | --- | --- | ---: | ---: | --- |",
    ]
    for record in sorted(records, key=lambda item: item.plan["plan_id"]):
        plan = record.plan
        lines.append(
            f"| `{md_cell(plan['plan_id'])}` | {md_cell(plan['title'])} | `{md_cell(plan['status'])}` | {plan['revision']} | {md_cell(plan['updated_at'])} | `{md_cell(record.directory)}` | {len(plan['phases'])} | {len(plan['tasks'])} | `{md_cell(plan['validation']['status'])}` |"
        )
    if not records:
        lines.append("| None | None | None | 0 | None | None | 0 | 0 | None |")
    return ("\n".join(lines) + "\n").encode("utf-8")


def ensure_index_is_managed(context: Context) -> None:
    index = context.plans_root / "INDEX.md"
    try:
        info = index.lstat()
    except FileNotFoundError:
        return
    except OSError as exc:
        raise AppError("io_error", "Cannot inspect the catalog index.") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise AppError(
            "unsafe_or_corrupt",
            "Existing INDEX.md is not a regular, non-symlink generated file.",
        )
    if not is_generated_projection(index):
        raise AppError(
            "unsafe_or_corrupt",
            "Existing INDEX.md is unmanaged and will not be overwritten.",
        )


def write_index(
    context: Context,
    records: Sequence[PlanRecord],
) -> bool:
    ensure_index_is_managed(context)
    return atomic_write_bytes(
        context.plans_root / "INDEX.md",
        render_index(records),
        required_existing_prefix=GENERATED_PROJECTION_MARKER,
    )


def inspect_index_drift(context: Context, records: Sequence[PlanRecord]) -> list[dict[str, Any]]:
    if not context.plans_root.exists():
        return []
    index = context.plans_root / "INDEX.md"
    expected = render_index(records)
    if not index.exists():
        return [
            _finding("error", "missing_index", "The generated catalog index is missing.", "INDEX.md")
        ]
    try:
        info = index.lstat()
    except OSError as exc:
        raise AppError("io_error", "Cannot inspect the catalog index.") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        return [
            _finding("error", "unsafe_index", "The catalog index is not a regular file.", "INDEX.md")
        ]
    if info.st_size != len(expected) or sha256_file(index) != sha256_bytes(expected):
        return [
            _finding("error", "index_drift", "The catalog index differs from canonical state.", "INDEX.md")
        ]
    return []


def plan_receipt(
    record: PlanRecord,
    *,
    canonical_committed: bool,
    projection_status: str,
    index_status: str,
) -> dict[str, Any]:
    return {
        "plan_id": record.plan["plan_id"],
        "directory": record.directory,
        "canonical_path": str(record.canonical_path),
        "revision": record.plan["revision"],
        "sha256": record.sha256,
        "plan_status": record.plan["status"],
        "phase_count": len(record.plan["phases"]),
        "task_count": len(record.plan["tasks"]),
        "validation_status": record.plan["validation"]["status"],
        "index_status": index_status,
        "canonical_committed": canonical_committed,
        "projection_status": projection_status,
    }


def recompute_phase_statuses(plan: dict[str, Any]) -> None:
    tasks_by_phase: dict[str, list[dict[str, Any]]] = {}
    for task in plan.get("tasks", []):
        if isinstance(task, dict):
            tasks_by_phase.setdefault(str(task.get("phase_id")), []).append(task)
    for phase in plan.get("phases", []):
        if isinstance(phase, dict) and isinstance(phase.get("phase_id"), str):
            phase["status"] = derive_phase_status(
                tasks_by_phase.get(phase["phase_id"], []), plan
            )


def history_entry(
    plan: Mapping[str, Any],
    *,
    revision: int,
    event_time: str,
    action_id: str,
    affected_ids: Sequence[str],
    status_before: str | None,
    status_after: str | None,
    summary: str,
    authority_basis: str,
) -> dict[str, Any]:
    ids = list(dict.fromkeys([str(plan["plan_id"]), *map(str, affected_ids)]))
    return {
        "revision": revision,
        "timestamp": event_time,
        "action_id": action_id,
        "affected_ids": ids,
        "status_before": status_before,
        "status_after": status_after,
        "summary": summary.strip(),
        "authority_basis": authority_basis.strip(),
    }


def prepare_canonical_mutation(
    current: PlanRecord,
    proposed: dict[str, Any],
    context: Context,
    *,
    action_id: str,
    affected_ids: Sequence[str],
    status_before: str | None,
    status_after: str | None,
    summary: str,
    authority_basis: str,
) -> bytes:
    event_time = next_timestamp(current.plan["updated_at"])
    proposed["schema_version"] = SCHEMA_VERSION
    proposed["plan_id"] = current.plan["plan_id"]
    proposed["slug"] = current.plan["slug"]
    proposed["created_at"] = current.plan["created_at"]
    proposed["initial_record_ids"] = copy.deepcopy(
        current.plan["initial_record_ids"]
    )
    proposed["revision"] = current.plan["revision"] + 1
    proposed["updated_at"] = event_time
    proposed["history"] = copy.deepcopy(current.plan["history"])
    proposed["history"].append(
        history_entry(
            proposed,
            revision=proposed["revision"],
            event_time=event_time,
            action_id=action_id,
            affected_ids=affected_ids,
            status_before=status_before,
            status_after=status_after,
            summary=summary,
            authority_basis=authority_basis,
        )
    )
    recompute_phase_statuses(proposed)
    refresh_validation(proposed, event_time)
    ensure_structurally_valid(
        proposed,
        context,
        directory_name=current.directory,
        input_context=True,
        check_snapshot=True,
    )
    data = canonical_bytes(proposed)
    if len(data) > MAX_JSON_BYTES:
        raise AppError(
            "invalid_input",
            "The proposed canonical plan exceeds the supported size.",
            details={"maximum_bytes": MAX_JSON_BYTES},
        )
    return data


def validate_expected(record: PlanRecord, revision: int, sha256_value: str) -> None:
    if revision != record.plan["revision"] or sha256_value.lower() != record.sha256:
        raise AppError(
            "stale_state",
            "Expected revision or canonical SHA-256 no longer matches.",
            details={
                "current_revision": record.plan["revision"],
                "current_sha256": record.sha256,
            },
        )


def parse_expected_hash(value: str) -> str:
    if not re.fullmatch(r"[a-fA-F0-9]{64}", value):
        raise AppError("invalid_input", "--expect-sha256 must be 64 hexadecimal characters.")
    return value.lower()


def _operation_controls(
    payload: dict[str, Any],
    *,
    command: str,
    allowed_patch_fields: set[str],
) -> tuple[dict[str, Any], str, str, bool, bool]:
    """Return patch, summary, authority, confirmed, material-change hint."""
    guard_prohibited_content(payload)
    controls = {"patch", "summary", "authority_basis", "confirmed", "material_change"}
    if "patch" in payload:
        unknown = set(payload) - controls
        if unknown:
            raise AppError(
                "invalid_input",
                f"{command} input has {len(unknown)} unsupported control field(s).",
            )
        patch = ensure_object(payload.get("patch"), "patch")
    else:
        patch = {key: copy.deepcopy(value) for key, value in payload.items() if key in allowed_patch_fields}
        unknown = set(payload) - allowed_patch_fields - (controls - {"patch"})
        if unknown:
            raise AppError(
                "invalid_input",
                f"{command} input has {len(unknown)} unsupported field(s).",
            )
    unsupported = set(patch) - allowed_patch_fields
    if unsupported:
        raise AppError(
            "invalid_input",
            f"{command} patch has {len(unsupported)} unsupported field(s).",
        )
    summary = payload.get("summary", f"Applied {command} mutation.")
    authority = payload.get(
        "authority_basis", f"Current explicit {command} instruction for the exact plan."
    )
    if not isinstance(summary, str) or not summary.strip() or len(summary) > MAX_SHORT_TEXT:
        raise AppError("invalid_input", "Mutation summary must be concise and nonblank.")
    if not isinstance(authority, str) or not authority.strip() or len(authority) > MAX_SHORT_TEXT:
        raise AppError("invalid_input", "Mutation authority_basis must be concise and nonblank.")
    confirmed = payload.get("confirmed", False)
    material_change = payload.get("material_change", False)
    if not isinstance(confirmed, bool) or not isinstance(material_change, bool):
        raise AppError("invalid_input", "confirmed and material_change must be booleans.")
    return copy.deepcopy(patch), summary.strip(), authority.strip(), confirmed, material_change


def validate_patch_value_types(
    patch: Mapping[str, Any],
    expected: Mapping[str, tuple[type, ...]],
    command: str,
) -> None:
    """Reject malformed patch containers before mutation-specific logic."""
    for field, value in patch.items():
        allowed = expected.get(field)
        if allowed is not None and not isinstance(value, allowed):
            names = ", ".join(item.__name__ for item in allowed)
            raise AppError(
                "invalid_input",
                f"{command} patch field {field} must use type {names}.",
                details={"targets": [field]},
            )


def _find_record(records: Sequence[dict[str, Any]], key: str, value: str, label: str) -> dict[str, Any]:
    matches = [item for item in records if isinstance(item, dict) and item.get(key) == value]
    if not matches:
        raise AppError("not_found", f"The exact {label} does not exist.")
    return matches[0]


def _assert_local_id(value: str, pattern: re.Pattern[str], label: str) -> None:
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise AppError("invalid_input", f"{label} must be one complete valid identifier.")


def _evidence_index(plan: Mapping[str, Any]) -> dict[str, tuple[str, dict[str, Any]]]:
    found: dict[str, tuple[str, dict[str, Any]]] = {}
    for collection in ("requirements", "tasks"):
        id_key = "requirement_id" if collection == "requirements" else "task_id"
        for target in plan.get(collection, []):
            if not isinstance(target, dict):
                continue
            target_id = str(target.get(id_key, ""))
            for evidence in target.get("evidence", []):
                if isinstance(evidence, dict) and isinstance(evidence.get("evidence_id"), str):
                    found[evidence["evidence_id"]] = (target_id, evidence)
    return found


def _assert_preserved_baseline(
    current: Mapping[str, Any], proposed: Mapping[str, Any], *, confirmed: bool
) -> None:
    """Prevent stable-ID deletion, reuse, or prior-evidence erasure."""
    for collection, key in (
        ("sources", "source_id"),
        ("requirements", "requirement_id"),
        ("decisions", "decision_id"),
        ("open_questions", "question_id"),
        ("assumptions", "assumption_id"),
        ("phases", "phase_id"),
        ("tasks", "task_id"),
    ):
        old_records = {
            item.get(key): item
            for item in current.get(collection, [])
            if isinstance(item, dict)
        }
        new_records = {
            item.get(key): item
            for item in proposed.get(collection, [])
            if isinstance(item, dict)
        }
        removed = sorted(identifier for identifier in old_records if identifier not in new_records)
        if removed:
            raise AppError(
                "invalid_input",
                "Baseline update cannot remove stable records; retain an explicit disposition or history-bearing record.",
                details={"targets": removed},
            )
    old_sources = {
        item.get("source_id"): item
        for item in current.get("sources", [])
        if isinstance(item, dict)
    }
    new_sources = {
        item.get("source_id"): item
        for item in proposed.get("sources", [])
        if isinstance(item, dict)
    }
    rewritten_sources = sorted(
        str(source_id)
        for source_id, old_record in old_sources.items()
        if new_sources.get(source_id) != old_record
    )
    if rewritten_sources:
        raise AppError(
            "invalid_input",
            "An existing source record is immutable provenance; append a new source ID for a new observation.",
            details={"targets": rewritten_sources},
        )
    old_project = current.get("project", {})
    new_project = proposed.get("project", {})
    old_facts = list(old_project.get("baseline_facts", []))
    new_facts = list(new_project.get("baseline_facts", []))
    if len(new_facts) < len(old_facts) or new_facts[: len(old_facts)] != old_facts:
        raise AppError(
            "invalid_input",
            "Project baseline observations are append-only in sequence and cannot be removed, reordered, or rewritten.",
            details={"targets": ["project.baseline_facts"]},
        )
    appended_facts = new_facts[len(old_facts) :]
    if any(
        item in old_facts or item in appended_facts[:index]
        for index, item in enumerate(appended_facts)
    ):
        raise AppError(
            "invalid_input",
            "Project baseline observations cannot append duplicate records.",
            details={"targets": ["project.baseline_facts"]},
        )
    old_guidance = list(old_project.get("guidance", []))
    new_guidance = list(new_project.get("guidance", []))
    if len(new_guidance) < len(old_guidance) or new_guidance[: len(old_guidance)] != old_guidance:
        raise AppError(
            "invalid_input",
            "Project guidance observations are append-only in sequence and cannot be removed, reordered, or rewritten.",
            details={"targets": ["project.guidance"]},
        )
    appended_guidance = new_guidance[len(old_guidance) :]
    if any(
        item in old_guidance or item in appended_guidance[:index]
        for index, item in enumerate(appended_guidance)
    ):
        raise AppError(
            "invalid_input",
            "Project guidance observations cannot append duplicate records.",
            details={"targets": ["project.guidance"]},
        )
    try:
        old_inspected = parse_timestamp(old_project.get("inspected_at"), "inspected_at")
        new_inspected = parse_timestamp(new_project.get("inspected_at"), "inspected_at")
    except ValueError:
        old_inspected = new_inspected = None
    if old_inspected is not None and new_inspected is not None and new_inspected < old_inspected:
        raise AppError(
            "invalid_input",
            "Project inspected_at cannot move backward.",
            details={"targets": ["project.inspected_at"]},
        )
    removed_gaps = [
        str(gap)
        for gap in old_project.get("evidence_gaps", [])
        if gap not in new_project.get("evidence_gaps", [])
    ]
    unresolved_gap_removals = [
        gap
        for gap in removed_gaps
        if not any(
            gap.casefold() in str(fact.get("fact", "")).casefold()
            and str(fact.get("evidence_locator", "")).strip()
            for fact in appended_facts
            if isinstance(fact, Mapping)
        )
    ]
    if removed_gaps and (not confirmed or unresolved_gap_removals):
        raise AppError(
            "unmet_gate",
            "Removing a project evidence gap requires confirmation and a new resolution observation naming that gap.",
            details={"targets": unresolved_gap_removals or removed_gaps},
        )
    old_requirements = {
        item.get("requirement_id"): item
        for item in current.get("requirements", [])
        if isinstance(item, dict)
    }
    new_requirements = {
        item.get("requirement_id"): item
        for item in proposed.get("requirements", [])
        if isinstance(item, dict)
    }
    for requirement_id, old_record in old_requirements.items():
        new_record = new_requirements.get(requirement_id, {})
        if any(
            new_record.get(field) != old_record.get(field)
            for field in ("title", "outcome", "intent")
        ):
            raise AppError(
                "invalid_input",
                "An existing requirement ID cannot be reused for a different title, outcome, or intent.",
                details={"targets": [str(requirement_id)]},
            )
        if new_record.get("evidence") != old_record.get("evidence"):
            raise AppError(
                "invalid_input",
                "Baseline update cannot add, erase, or rewrite requirement evidence; use record-evidence.",
                details={"targets": [str(requirement_id)]},
            )
        old_status = old_record.get("status")
        new_status = new_record.get("status")
        disposition_changed = new_record.get("disposition") != old_record.get("disposition")
        if new_status == "satisfied" and missing_criterion_evidence(
            new_record.get("acceptance_criteria", []),
            new_record.get("evidence"),
            target_definition_digest(new_record, "requirement", proposed),
        ):
            raise AppError(
                "unmet_gate",
                "A requirement cannot become satisfied without criterion-linked passing evidence.",
                details={"targets": [str(requirement_id)]},
            )
        if (
            new_status == "dispositioned"
            or old_status == "dispositioned"
            or disposition_changed
        ) and (new_status != old_status or disposition_changed) and not confirmed:
            raise AppError(
                "unmet_gate",
                "Changing a requirement disposition requires confirmed: true.",
                details={"targets": [str(requirement_id)]},
            )

    current_task_map = {
        item.get("task_id"): item
        for item in current.get("tasks", [])
        if isinstance(item, dict)
    }
    proposed_task_map = {
        item.get("task_id"): item
        for item in proposed.get("tasks", [])
        if isinstance(item, dict)
    }
    protected_task_fields = {
        "status",
        "blocker_reason",
        "pause_reason",
        "skip_reason",
        "skip_authority",
        "evidence",
        "completed_at",
    }
    for task_id, old_record in current_task_map.items():
        new_record = proposed_task_map.get(task_id, {})
        changed = sorted(
            field
            for field in protected_task_fields
            if new_record.get(field) != old_record.get(field)
        )
        if changed:
            raise AppError(
                "invalid_input",
                "Baseline update cannot change task lifecycle or evidence fields; use update-task or record-evidence.",
                details={"targets": [str(task_id), *changed]},
            )

    current_phase_map = {
        item.get("phase_id"): item
        for item in current.get("phases", [])
        if isinstance(item, dict)
    }
    proposed_phase_map = {
        item.get("phase_id"): item
        for item in proposed.get("phases", [])
        if isinstance(item, dict)
    }
    derived_phase_edits = sorted(
        str(phase_id)
        for phase_id, old_record in current_phase_map.items()
        if proposed_phase_map.get(phase_id, {}).get("status")
        != old_record.get("status")
    )
    if derived_phase_edits:
        raise AppError(
            "invalid_input",
            "Phase status is derived from task state and cannot be set by a baseline update.",
            details={"targets": derived_phase_edits},
        )

    for requirement_id in sorted(set(new_requirements) - set(old_requirements)):
        record = new_requirements[requirement_id]
        if (
            record.get("status") != "active"
            or record.get("disposition") is not None
            or record.get("evidence") not in (None, [])
        ):
            raise AppError(
                "invalid_input",
                "A new requirement must begin active without disposition or evidence.",
                details={"targets": [str(requirement_id)]},
            )
    for task_id in sorted(set(proposed_task_map) - set(current_task_map)):
        record = proposed_task_map[task_id]
        if (
            record.get("status") != "planned"
            or record.get("evidence") not in (None, [])
            or record.get("completed_at") is not None
            or any(record.get(field) is not None for field in (
                "blocker_reason", "pause_reason", "skip_reason", "skip_authority"
            ))
        ):
            raise AppError(
                "invalid_input",
                "A new task must begin planned without lifecycle reasons, evidence, or completion time.",
                details={"targets": [str(task_id)]},
            )

    for collection, key, statement_field in (
        ("decisions", "decision_id", "statement"),
        ("open_questions", "question_id", "question"),
        ("assumptions", "assumption_id", "statement"),
    ):
        old_map = {
            item.get(key): item
            for item in current.get(collection, [])
            if isinstance(item, dict)
        }
        new_map = {
            item.get(key): item
            for item in proposed.get(collection, [])
            if isinstance(item, dict)
        }
        for identifier, old_record in old_map.items():
            new_record = new_map.get(identifier, {})
            if new_record.get(statement_field) != old_record.get(statement_field):
                raise AppError(
                    "invalid_input",
                    "A stable decision, question, or assumption ID cannot be reused for different meaning.",
                    details={"targets": [str(identifier)]},
                )
            if new_record.get("status") != old_record.get("status") and not confirmed:
                raise AppError(
                    "unmet_gate",
                    "Changing a decision, question, or assumption status requires confirmed: true.",
                    details={"targets": [str(identifier)]},
                )
        for identifier in set(new_map) - set(old_map):
            status_value = new_map[identifier].get("status")
            initial = {
                "decisions": "proposed",
                "open_questions": "open",
                "assumptions": "unconfirmed",
            }[collection]
            if status_value != initial and not confirmed:
                raise AppError(
                    "unmet_gate",
                    "A new decided or resolved record requires confirmed: true.",
                    details={"targets": [str(identifier)]},
                )

    old_edges = {
        item.get("requirement_id"): item.get("disposition")
        for item in current.get("coverage", {}).get("requirement_to_task", [])
        if isinstance(item, dict)
    }
    new_edges = {
        item.get("requirement_id"): item.get("disposition")
        for item in proposed.get("coverage", {}).get("requirement_to_task", [])
        if isinstance(item, dict)
    }
    if any(new_edges.get(key) != value for key, value in old_edges.items()) and not confirmed:
        raise AppError(
            "unmet_gate",
            "Changing requirement coverage dispositions requires confirmed: true.",
        )
    old_evidence = _evidence_index(current)
    new_evidence = _evidence_index(proposed)
    for evidence_id, (target_id, evidence) in old_evidence.items():
        if evidence_id not in new_evidence or new_evidence[evidence_id] != (target_id, evidence):
            raise AppError(
                "invalid_input",
                "Baseline update cannot erase or rewrite prior evidence.",
                details={"targets": [evidence_id, target_id]},
            )


def _result_warning(category: str, message: str, *targets: str) -> dict[str, Any]:
    return {
        "category": category,
        "message": message,
        "targets": list(dict.fromkeys(target for target in targets if target)),
    }


def make_envelope(
    context: Context | None,
    command: str,
    *,
    status: str,
    mutation: bool,
    warnings: Sequence[Mapping[str, Any]] = (),
    errors: Sequence[Mapping[str, Any]] = (),
    recovery_required: Mapping[str, Any] | None = None,
    receipt: Mapping[str, Any] | None = None,
    data: Any = None,
) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "command": command,
        "project_root": str(context.project_root) if context else None,
        "plans_root": str(context.plans_root) if context else None,
        "status": status,
        "mutation": mutation,
        "warnings": [dict(item) for item in warnings],
        "errors": [dict(item) for item in errors],
        "recovery_required": dict(recovery_required) if recovery_required else None,
        "plan": dict(receipt) if receipt else None,
        "data": data,
    }


@dataclasses.dataclass
class ProposedMutation:
    plan: dict[str, Any]
    affected_ids: list[str]
    status_before: str | None
    status_after: str | None
    summary: str
    authority_basis: str


def commit_canonical_with_probe(
    context: Context,
    *,
    canonical_path: Path,
    plan_directory: Path,
    canonical: bytes,
    expected_parent_identity: tuple[int, int],
) -> PlanRecord:
    """Commit and reload, converting any post-commit interruption into a partial result."""
    try:
        atomic_write_bytes(
            canonical_path,
            canonical,
            expected_parent_identity=expected_parent_identity,
        )
        return load_plan_record(context, plan_directory)
    except BaseException as original:
        exact_commit = False
        try:
            exact_commit = (
                read_bounded_regular_file(
                    canonical_path, label="canonical commit probe"
                )
                == canonical
            )
        except (AppError, OSError):
            exact_commit = False
        if exact_commit:
            details = (
                copy.deepcopy(original.details)
                if isinstance(original, AppError)
                else {}
            )
            details["replacement_completed"] = True
            raise AppError(
                "io_error",
                "Canonical bytes committed, but the commit boundary was interrupted before a complete publication receipt.",
                details=details,
            ) from original
        raise


def sha256_regular_file_at(directory_fd: int, name: str) -> str:
    descriptor = os.open(
        name,
        os.O_RDONLY
        | os.O_NOFOLLOW
        | getattr(os, "O_NONBLOCK", 0)
        | getattr(os, "O_CLOEXEC", 0),
        dir_fd=directory_fd,
    )
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode):
            raise AppError(
                "unsafe_or_corrupt", "Bound recovery target is not a regular file."
            )
        digest = hashlib.sha256()
        while True:
            block = os.read(descriptor, 1024 * 1024)
            if not block:
                break
            digest.update(block)
        return digest.hexdigest()
    finally:
        os.close(descriptor)


def create_and_commit_new_plan(
    context: Context,
    *,
    catalog_identity: tuple[int, int],
    directory: str,
    canonical: bytes,
) -> PlanRecord:
    """Create one plan directory and commit canonical bytes through bound fds."""
    bound = create_bound_subdirectory(
        context.plans_root, catalog_identity, directory
    )
    plan_dir = context.plans_root / directory
    try:
        try:
            return commit_canonical_with_probe(
                context,
                canonical_path=plan_dir / "plan.json",
                plan_directory=plan_dir,
                canonical=canonical,
                expected_parent_identity=bound.child_identity,
            )
        except BaseException as original:
            error = (
                original
                if isinstance(original, AppError)
                else AppError(
                    "io_error",
                    "Initial canonical commit was interrupted before completion.",
                )
            )
            parent_current = directory_path_matches_identity(
                context.plans_root,
                bound.parent_identity,
                label="plans catalog",
            )
            child_current = directory_path_matches_identity(
                plan_dir,
                bound.child_identity,
                label="managed plan directory",
            )
            try:
                names = sorted(os.listdir(bound.child_fd))
            except OSError:
                names = []
            temporary_names = [
                name
                for name in names
                if re.fullmatch(r"^\.plan\.json\.tmp-[A-F0-9]{32}$", name)
            ]
            if error.details.get("replacement_completed") and parent_current and child_current:
                if error is original:
                    raise
                raise error from original
            if parent_current and child_current and len(names) == 1 and temporary_names:
                temporary_name = temporary_names[0]
                error.details["recovery_required"] = {
                    "command": "reconcile",
                    "selector": "catalog",
                    "input": {
                        "action": "remove_partial_create",
                        "scope": "catalog",
                        "state": "temporary",
                        "directory": directory,
                        "relative_path": temporary_name,
                        "sha256": sha256_regular_file_at(
                            bound.child_fd, temporary_name
                        ),
                    },
                    "then": "validate",
                }
                if error is original:
                    raise
                raise error from original

            cleanup_incomplete = False
            removable_names = set(temporary_names)
            if "plan.json" in names:
                removable_names.add("plan.json")
            if set(names) == removable_names:
                try:
                    for name in sorted(removable_names):
                        os.unlink(name, dir_fd=bound.child_fd)
                    os.fsync(bound.child_fd)
                    os.rmdir(directory, dir_fd=bound.parent_fd)
                    os.fsync(bound.parent_fd)
                except (OSError, KeyboardInterrupt):
                    cleanup_incomplete = True
            else:
                cleanup_incomplete = True
            if cleanup_incomplete:
                error.details.update(
                    {
                        "directory_creation_cleanup_incomplete": True,
                        "filesystem_mutation": True,
                        "directory": directory,
                    }
                )
            else:
                error.details.pop("replacement_completed", None)
            if error is original:
                raise
            raise error from original
    finally:
        bound.close()


def committed_record_from_known_bytes(
    context: Context, plan_directory: Path, canonical: bytes
) -> PlanRecord:
    """Build a conservative receipt record after exact on-disk bytes were confirmed."""
    plan = decode_json_bytes(canonical, "known committed canonical bytes")
    ensure_structurally_valid(
        plan,
        context,
        directory_name=plan_directory.name,
        input_context=False,
        check_snapshot=True,
    )
    directory_fd = open_directory_without_symlinks(
        plan_directory, label="known committed plan directory"
    )
    try:
        info = os.fstat(directory_fd)
        directory_identity = (info.st_dev, info.st_ino)
    finally:
        os.close(directory_fd)
    return PlanRecord(
        directory=plan_directory.name,
        path=plan_directory,
        canonical_path=plan_directory / "plan.json",
        plan=plan,
        raw=canonical,
        sha256=sha256_bytes(canonical),
        directory_identity=directory_identity,
    )


def mutate_existing_plan(
    context: Context,
    *,
    selector: str,
    expected_revision: int,
    expected_sha256: str,
    command: str,
    action_id: str,
    mutator: Any,
) -> tuple[dict[str, Any], int]:
    before = select_plan(context, selector)
    validate_expected(before, expected_revision, expected_sha256)
    ensure_catalog_for_write(context)
    outcome: dict[str, Any] | None = None
    with held_lock(catalog_lock_path(context), command, lambda: outcome):
        # Fail closed on every malformed managed record before changing one plan.
        discover_managed_plans(context)
        with held_lock(plan_lock_path(before.path), command, lambda: outcome):
            current = load_plan_record(context, before.path)
            validate_expected(current, expected_revision, expected_sha256)
            ensure_index_is_managed(context)
            try:
                proposal: ProposedMutation | None = mutator(current)
            except AppError:
                raise
            except (AttributeError, KeyError, TypeError, ValueError) as exc:
                raise AppError(
                    "invalid_input",
                    "Mutation input does not match the canonical field contract.",
                ) from exc
            if proposal is None:
                drift = inspect_projection_drift(current)
                receipt = plan_receipt(
                    current,
                    canonical_committed=False,
                    projection_status="drift" if drift else "current",
                    index_status="not_checked",
                )
                outcome = make_envelope(
                    context,
                    command,
                    status="no_op",
                    mutation=False,
                    receipt=receipt,
                    data={"projection_findings": drift},
                )
            else:
                try:
                    preflight_projection_destinations(current.path, proposal.plan)
                    canonical = prepare_canonical_mutation(
                        current,
                        proposal.plan,
                        context,
                        action_id=action_id,
                        affected_ids=proposal.affected_ids,
                        status_before=proposal.status_before,
                        status_after=proposal.status_after,
                        summary=proposal.summary,
                        authority_basis=proposal.authority_basis,
                    )
                except AppError:
                    raise
                except (AttributeError, KeyError, TypeError, ValueError) as exc:
                    raise AppError(
                        "invalid_input",
                        "Mutation input does not match the canonical field contract.",
                    ) from exc
                committed: PlanRecord | None = None
                try:
                    committed = commit_canonical_with_probe(
                        context,
                        canonical_path=current.canonical_path,
                        plan_directory=current.path,
                        canonical=canonical,
                        expected_parent_identity=current.directory_identity,
                    )
                except AppError as exc:
                    if not exc.details.get("replacement_completed"):
                        raise
                    committed = committed_record_from_known_bytes(
                        context, current.path, canonical
                    )
                    outcome = make_envelope(
                        context,
                        command,
                        status="partial",
                        mutation=True,
                        errors=[
                            _result_warning(
                                "partial_projection",
                                "Canonical replacement completed but durability sync or generated publication did not finish.",
                                committed.plan["plan_id"],
                            )
                        ],
                        recovery_required={
                            "command": "rebuild-projections",
                            "selector": committed.plan["plan_id"],
                            "then": "reindex",
                        },
                        receipt=plan_receipt(
                            committed,
                            canonical_committed=True,
                            projection_status="failed",
                            index_status="failed",
                        ),
                    )
                    committed = None
                if committed is None:
                    pass
                else:
                    projection_status = "current"
                    index_status = "current"
                    try:
                        projection_changed = write_plan_projections(committed)
                        projection_status = "updated" if projection_changed else "current"
                        records, _ = discover_managed_plans(context)
                        index_changed = write_index(context, records)
                        index_status = "updated" if index_changed else "current"
                    except AppError as exc:
                        receipt = plan_receipt(
                            committed,
                            canonical_committed=True,
                            projection_status=(
                                "failed" if projection_status == "current" else projection_status
                            ),
                            index_status="failed",
                        )
                        outcome = make_envelope(
                            context,
                            command,
                            status="partial",
                            mutation=True,
                            errors=[
                                _result_warning(
                                    "partial_projection",
                                    "Canonical state committed but generated publication did not finish.",
                                    committed.plan["plan_id"],
                                )
                            ],
                            recovery_required={
                                "command": "rebuild-projections",
                                "selector": committed.plan["plan_id"],
                                "then": "reindex",
                            },
                            receipt=receipt,
                            data={"failure_category": exc.category},
                        )
                    else:
                        receipt = plan_receipt(
                            committed,
                            canonical_committed=True,
                            projection_status=projection_status,
                            index_status=index_status,
                        )
                        outcome = make_envelope(
                            context,
                            command,
                            status="ok",
                            mutation=True,
                            receipt=receipt,
                        )
    if outcome is None:
        raise AppError("io_error", "Mutation ended without a result receipt.")
    return outcome, (
        EXIT_CODES["partial_projection"] if outcome["status"] == "partial" else 0
    )


def _assign_new_identity(
    plan: dict[str, Any],
    existing_directories: set[str],
    existing_plan_ids: set[str] | None = None,
) -> str:
    created = parse_timestamp(plan["created_at"], "created_at")
    date_compact = created.strftime("%Y%m%d")
    date_display = created.strftime("%Y-%m-%d")
    used_plan_ids = existing_plan_ids or set()
    for _ in range(128):
        suffix = uuid.uuid4().hex[:8].upper()
        directory = f"Plan_{plan['slug']}_{date_display}_{suffix}"
        plan_id = f"PLAN-{date_compact}-{suffix}"
        if directory not in existing_directories and plan_id not in used_plan_ids:
            plan["plan_id"] = plan_id
            return directory
    raise AppError("io_error", "Could not allocate a collision-free plan identity.")


def ensure_initial_lifecycle_state(plan: Mapping[str, Any]) -> None:
    """Creation records a plan baseline; it cannot import execution success."""
    invalid_requirements = [
        str(item.get("requirement_id"))
        for item in plan.get("requirements", [])
        if isinstance(item, Mapping)
        and (
            not _is_enum_value(
                item.get("status"), {"active", "dispositioned"}
            )
            or item.get("evidence") not in (None, [])
        )
    ]
    invalid_tasks = [
        str(item.get("task_id"))
        for item in plan.get("tasks", [])
        if isinstance(item, Mapping)
        and (
            item.get("status") != "planned"
            or item.get("evidence") not in (None, [])
            or item.get("completed_at") is not None
            or any(
                item.get(field) is not None
                for field in (
                    "blocker_reason",
                    "pause_reason",
                    "skip_reason",
                    "skip_authority",
                )
            )
        )
    ]
    if invalid_requirements or invalid_tasks:
        raise AppError(
            "invalid_input",
            "create accepts a planning baseline only; execution evidence and completed lifecycle state must be recorded through later gated actions.",
            details={"targets": invalid_requirements + invalid_tasks},
        )


def stable_record_ids(plan: Mapping[str, Any]) -> list[str]:
    result: list[str] = []
    for collection, key in (
        ("sources", "source_id"),
        ("requirements", "requirement_id"),
        ("decisions", "decision_id"),
        ("open_questions", "question_id"),
        ("assumptions", "assumption_id"),
        ("phases", "phase_id"),
        ("tasks", "task_id"),
    ):
        result.extend(
            str(item.get(key))
            for item in list_or_empty(plan.get(collection))
            if isinstance(item, Mapping) and isinstance(item.get(key), str)
        )
    return list(dict.fromkeys(result))


def handle_create(context: Context, args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    payload = read_input(args.input)
    guard_prohibited_content(payload)
    allowed = {
        "title",
        "slug",
        "status_reason",
        "project",
        "objective",
        "scope",
        "sources",
        "requirements",
        "decisions",
        "open_questions",
        "assumptions",
        "phases",
        "tasks",
        "coverage",
    }
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise AppError(
            "invalid_input",
            f"create input has {len(unknown)} unsupported field(s).",
        )
    plan = normalize_plan_input(payload, context)
    ensure_initial_lifecycle_state(plan)
    directory = _assign_new_identity(plan, set())
    plan["history"] = [
        history_entry(
            plan,
            revision=1,
            event_time=plan["created_at"],
            action_id="TO-IP-001",
            affected_ids=stable_record_ids(plan),
            status_before=None,
            status_after="draft",
            summary="Created the initial tracked implementation-plan draft.",
            authority_basis="Current explicit create operation for this project root.",
        )
    ]
    recompute_phase_statuses(plan)
    refresh_validation(plan, plan["updated_at"])
    ensure_structurally_valid(
        plan,
        context,
        directory_name=directory,
        input_context=True,
        check_snapshot=True,
    )
    canonical = canonical_bytes(plan)
    if len(canonical) > MAX_JSON_BYTES:
        raise AppError("invalid_input", "The canonical plan exceeds the supported size.")

    ensure_catalog_for_write(context)
    outcome: dict[str, Any] | None = None
    with held_lock(
        catalog_lock_path(context), "create", lambda: outcome
    ) as catalog_handle:
        existing, unmanaged = discover_managed_plans(context)
        ensure_index_is_managed(context)
        existing_directories = {record.directory for record in existing} | set(unmanaged)
        existing_plan_ids = {str(record.plan["plan_id"]) for record in existing}
        if directory in existing_directories or plan["plan_id"] in existing_plan_ids:
            directory = _assign_new_identity(
                plan, existing_directories, existing_plan_ids
            )
            plan["history"][0]["affected_ids"] = [
                plan["plan_id"],
                *stable_record_ids(plan),
            ]
            refresh_validation(plan, plan["updated_at"])
            ensure_structurally_valid(
                plan,
                context,
                directory_name=directory,
                input_context=True,
                check_snapshot=True,
            )
            canonical = canonical_bytes(plan)
        plan_dir = context.plans_root / directory
        committed: PlanRecord | None = None
        try:
            committed = create_and_commit_new_plan(
                context,
                catalog_identity=catalog_handle.parent_identity,
                directory=directory,
                canonical=canonical,
            )
        except AppError as exc:
            if exc.details.get("replacement_completed"):
                committed_record = committed_record_from_known_bytes(
                    context, plan_dir, canonical
                )
                outcome = make_envelope(
                    context,
                    "create",
                    status="partial",
                    mutation=True,
                    errors=[
                        _result_warning(
                            "partial_projection",
                            "Canonical creation replacement completed but durability sync or generated publication did not finish.",
                            committed_record.plan["plan_id"],
                        )
                    ],
                    recovery_required={
                        "command": "rebuild-projections",
                        "selector": committed_record.plan["plan_id"],
                        "then": "reindex",
                    },
                    receipt=plan_receipt(
                        committed_record,
                        canonical_committed=True,
                        projection_status="failed",
                        index_status="failed",
                    ),
                )
                committed = None
            else:
                raise
        if committed is not None:
            projection_status = "current"
            index_status = "current"
            try:
                projection_changed = write_plan_projections(committed)
                projection_status = "updated" if projection_changed else "current"
                records, _ = discover_managed_plans(context)
                index_changed = write_index(context, records)
                index_status = "updated" if index_changed else "current"
            except AppError as exc:
                outcome = make_envelope(
                    context,
                    "create",
                    status="partial",
                    mutation=True,
                    errors=[
                        _result_warning(
                            "partial_projection",
                            "Canonical plan creation committed but generated publication did not finish.",
                            committed.plan["plan_id"],
                        )
                    ],
                    recovery_required={
                        "command": "rebuild-projections",
                        "selector": committed.plan["plan_id"],
                        "then": "reindex",
                    },
                    receipt=plan_receipt(
                        committed,
                        canonical_committed=True,
                        projection_status="failed" if projection_status == "current" else projection_status,
                        index_status="failed",
                    ),
                    data={"failure_category": exc.category},
                )
            else:
                outcome = make_envelope(
                    context,
                    "create",
                    status="ok",
                    mutation=True,
                    receipt=plan_receipt(
                        committed,
                        canonical_committed=True,
                        projection_status=projection_status,
                        index_status=index_status,
                    ),
                )
    if outcome is None:
        raise AppError("io_error", "Create ended without a result receipt.")
    return outcome, EXIT_CODES["partial_projection"] if outcome["status"] == "partial" else 0


def _lock_warnings(context: Context, records: Sequence[PlanRecord]) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    catalog_lock = catalog_lock_path(context)
    if catalog_lock.exists():
        warnings.append(
            _result_warning(
                "active_lock",
                "The catalog has a write lock; read-only state may change concurrently.",
                str(catalog_lock),
            )
        )
    for record in records:
        lock = plan_lock_path(record.path)
        if lock.exists():
            warnings.append(
                _result_warning(
                    "active_lock",
                    "A selected managed plan has a write lock; read-only state may change concurrently.",
                    record.plan["plan_id"],
                    str(lock),
                )
            )
    return warnings


def handle_show(context: Context, args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    record = select_plan(context, args.selector)
    records, _ = discover_managed_plans(context)
    projection_findings = inspect_projection_drift(record)
    index_findings = inspect_index_drift(context, records)
    return (
        make_envelope(
            context,
            "show",
            status="ok",
            mutation=False,
            warnings=_lock_warnings(context, [record]),
            receipt=plan_receipt(
                record,
                canonical_committed=False,
                projection_status="drift" if projection_findings else "current",
                index_status="drift" if index_findings else "current",
            ),
            data={
                "canonical": record.plan,
                "projection_findings": projection_findings,
                "index_findings": index_findings,
            },
        ),
        0,
    )


def handle_list(context: Context, args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    records, unmanaged = discover_managed_plans(context)
    selected = [
        record
        for record in records
        if args.status_filter is None or record.plan["status"] == args.status_filter
    ]
    summaries = [
        {
            "plan_id": record.plan["plan_id"],
            "title": record.plan["title"],
            "directory": record.directory,
            "status": record.plan["status"],
            "revision": record.plan["revision"],
            "sha256": record.sha256,
            "updated_at": record.plan["updated_at"],
            "phase_count": len(record.plan["phases"]),
            "task_count": len(record.plan["tasks"]),
            "validation_status": record.plan["validation"]["status"],
        }
        for record in selected
    ]
    return (
        make_envelope(
            context,
            "list",
            status="ok",
            mutation=False,
            warnings=_lock_warnings(context, records),
            data={
                "plans": summaries,
                "count": len(summaries),
                "status_filter": args.status_filter,
                "unmanaged_entries": unmanaged,
            },
        ),
        0,
    )


def handle_validate(context: Context, args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    records, unmanaged = discover_managed_plans(context)
    if args.selector is not None:
        selected_record = select_plan(context, args.selector)
        selected = [selected_record]
    else:
        selected = records
    plan_results: list[dict[str, Any]] = []
    any_failure = False
    for record in selected:
        projection_findings = inspect_projection_drift(record)
        canonical_status = record.plan["validation"]["status"]
        effective_status = "fail" if projection_findings else canonical_status
        if effective_status in {"fail", "unresolved"}:
            any_failure = True
        plan_results.append(
            {
                "plan_id": record.plan["plan_id"],
                "directory": record.directory,
                "canonical_validation": copy.deepcopy(record.plan["validation"]),
                "projection_findings": projection_findings,
                "status": effective_status,
            }
        )
    index_findings = inspect_index_drift(context, records)
    if index_findings:
        any_failure = True
    receipt = None
    if args.selector is not None and len(selected) == 1:
        record = selected[0]
        receipt = plan_receipt(
            record,
            canonical_committed=False,
            projection_status="drift" if plan_results[0]["projection_findings"] else "current",
            index_status="drift" if index_findings else "current",
        )
    return (
        make_envelope(
            context,
            "validate",
            status="ok",
            mutation=False,
            warnings=_lock_warnings(context, selected),
            receipt=receipt,
            data={
                "status": "fail" if any_failure else "pass",
                "plans": plan_results,
                "index_findings": index_findings,
                "unmanaged_entries": unmanaged,
            },
        ),
        0,
    )


def handle_rebuild_projections(
    context: Context, args: argparse.Namespace
) -> tuple[dict[str, Any], int]:
    if catalog_lock_path(context).exists():
        raise AppError(
            "active_lock",
            "Catalog creation or mutation is active; plan projections were not rebuilt.",
            details={"targets": [str(catalog_lock_path(context))]},
        )
    before = select_plan(context, args.selector)
    partial_error: AppError | None = None
    changed: list[str] = []
    outcome: dict[str, Any] | None = None
    exit_code = 0
    with held_lock(
        plan_lock_path(before.path), "rebuild-projections", lambda: outcome
    ):
        current = load_plan_record(context, before.path)
        try:
            changed = write_plan_projections(current)
        except AppError as exc:
            changed = [
                str(item)
                for item in exc.details.get("generated_files_changed", [])
                if isinstance(item, str)
            ]
            if not changed:
                raise
            partial_error = exc
        receipt = plan_receipt(
            current,
            canonical_committed=False,
            projection_status="failed"
            if partial_error
            else ("updated" if changed else "current"),
            index_status="not_checked",
        )
        if partial_error is not None:
            outcome = make_envelope(
                context,
                "rebuild-projections",
                status="partial",
                mutation=True,
                errors=[
                    _result_warning(
                        "partial_projection",
                        "Projection repair changed generated files but did not finish.",
                        current.plan["plan_id"],
                    )
                ],
                recovery_required={
                    "command": "rebuild-projections",
                    "selector": current.plan["plan_id"],
                },
                receipt=receipt,
                data={"changed_files": changed},
            )
            exit_code = EXIT_CODES["partial_projection"]
        else:
            outcome = make_envelope(
                context,
                "rebuild-projections",
                status="ok" if changed else "no_op",
                mutation=bool(changed),
                receipt=receipt,
                data={"changed_files": changed},
            )
    if outcome is None:
        raise AppError("io_error", "Projection rebuild ended without a result receipt.")
    return outcome, exit_code


def handle_reindex(context: Context, args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    ensure_catalog_for_write(context)
    partial = False
    changed = False
    outcome: dict[str, Any] | None = None
    exit_code = 0
    with held_lock(catalog_lock_path(context), "reindex", lambda: outcome):
        records, unmanaged = discover_managed_plans(context)
        try:
            changed = write_index(context, records)
        except AppError as exc:
            if not exc.details.get("replacement_completed"):
                raise
            partial = True
            changed = True
        if partial:
            outcome = make_envelope(
                context,
                "reindex",
                status="partial",
                mutation=True,
                errors=[
                    _result_warning(
                        "partial_projection",
                        "Catalog index replacement completed but durability sync did not finish.",
                        "INDEX.md",
                    )
                ],
                recovery_required={"command": "reindex"},
                data={
                    "index_path": str(context.plans_root / "INDEX.md"),
                    "managed_plan_count": len(records),
                    "unmanaged_entries": unmanaged,
                },
            )
            exit_code = EXIT_CODES["partial_projection"]
        else:
            outcome = make_envelope(
                context,
                "reindex",
                status="ok" if changed else "no_op",
                mutation=changed,
                data={
                    "index_path": str(context.plans_root / "INDEX.md"),
                    "managed_plan_count": len(records),
                    "unmanaged_entries": unmanaged,
                },
            )
    if outcome is None:
        raise AppError("io_error", "Reindex ended without a result receipt.")
    return outcome, exit_code


BASELINE_PATCH_FIELDS = {
    "title",
    "project",
    "objective",
    "scope",
    "sources",
    "requirements",
    "decisions",
    "open_questions",
    "assumptions",
    "phases",
    "tasks",
    "coverage",
}
BASELINE_PATCH_TYPES: dict[str, tuple[type, ...]] = {
    "title": (str,),
    "project": (dict,),
    "objective": (dict,),
    "scope": (dict,),
    "sources": (list,),
    "requirements": (list,),
    "decisions": (list,),
    "open_questions": (list,),
    "assumptions": (list,),
    "phases": (list,),
    "tasks": (list,),
    "coverage": (dict,),
}


def _requirements_materially_differ(
    old: Sequence[Mapping[str, Any]], new: Sequence[Mapping[str, Any]]
) -> bool:
    ignored = {"status", "evidence"}
    old_map = {
        str(item.get("requirement_id")): {
            key: value for key, value in item.items() if key not in ignored
        }
        for item in old
    }
    new_map = {
        str(item.get("requirement_id")): {
            key: value for key, value in item.items() if key not in ignored
        }
        for item in new
    }
    return old_map != new_map


SOURCE_ACCESS_CLAIM_FIELDS = {
    "kind",
    "locator",
    "accessed_at",
    "digest",
    "facts_used",
    "provenance_mode",
    "inspection_method",
}


def _sources_requiring_live_validation(
    current: Sequence[Mapping[str, Any]], proposed: Sequence[Mapping[str, Any]]
) -> list[Mapping[str, Any]]:
    """Return only new or freshly reasserted local-source observations."""
    old = {
        str(item.get("source_id")): item
        for item in current
        if isinstance(item, Mapping)
    }
    result: list[Mapping[str, Any]] = []
    for source in proposed:
        if not isinstance(source, Mapping):
            continue
        previous = old.get(str(source.get("source_id")))
        if previous is None or any(
            source.get(field) != previous.get(field)
            for field in SOURCE_ACCESS_CLAIM_FIELDS
        ):
            result.append(source)
    return result


def _baseline_affected_ids(
    current: Mapping[str, Any], proposed: Mapping[str, Any], patch: Mapping[str, Any]
) -> list[str]:
    """Name every stable record whose canonical meaning changed in TO-IP-004."""
    identifiers: list[str] = []
    for collection, key in (
        ("sources", "source_id"),
        ("requirements", "requirement_id"),
        ("decisions", "decision_id"),
        ("open_questions", "question_id"),
        ("assumptions", "assumption_id"),
        ("phases", "phase_id"),
        ("tasks", "task_id"),
    ):
        if collection not in patch:
            continue
        old = {
            str(item.get(key)): item
            for item in current.get(collection, [])
            if isinstance(item, Mapping)
        }
        new = {
            str(item.get(key)): item
            for item in proposed.get(collection, [])
            if isinstance(item, Mapping)
        }
        identifiers.extend(
            identifier
            for identifier, record in new.items()
            if old.get(identifier) != record
        )
    if "coverage" in patch:
        for edge_key, id_key in (
            ("source_to_requirement", "source_id"),
            ("requirement_to_task", "requirement_id"),
        ):
            old_edges = {
                str(item.get(id_key)): item
                for item in current.get("coverage", {}).get(edge_key, [])
                if isinstance(item, Mapping)
            }
            new_edges = {
                str(item.get(id_key)): item
                for item in proposed.get("coverage", {}).get(edge_key, [])
                if isinstance(item, Mapping)
            }
            identifiers.extend(
                identifier
                for identifier, edge in new_edges.items()
                if old_edges.get(identifier) != edge
            )
    return list(dict.fromkeys(identifiers))


def _project_patch_is_observation_only(
    current: Mapping[str, Any], proposed: Mapping[str, Any]
) -> bool:
    """Allow final inspection timestamps/facts without redefining scope."""
    immutable_for_observation = {
        "root_hint",
        "guidance",
        "constraints",
        "preserved_paths",
    }
    if not all(
        current.get(field) == proposed.get(field)
        for field in immutable_for_observation
    ):
        return False
    current_facts = list(current.get("baseline_facts", []))
    proposed_facts = list(proposed.get("baseline_facts", []))
    if (
        len(proposed_facts) < len(current_facts)
        or proposed_facts[: len(current_facts)] != current_facts
    ):
        return False
    if any(
        item not in proposed.get("evidence_gaps", [])
        for item in current.get("evidence_gaps", [])
    ):
        return False
    try:
        current_time = parse_timestamp(current.get("inspected_at"), "inspected_at")
        proposed_time = parse_timestamp(proposed.get("inspected_at"), "inspected_at")
    except ValueError:
        return False
    return proposed_time >= current_time


def _ensure_no_active_tasks_for_material(plan: Mapping[str, Any]) -> None:
    active_tasks = [
        str(task.get("task_id"))
        for task in plan.get("tasks", [])
        if isinstance(task, Mapping) and task.get("status") == "in_progress"
    ]
    if active_tasks:
        raise AppError(
            "unmet_gate",
            "Pause or block active tasks before changing the material baseline.",
            details={"targets": active_tasks},
        )


def handle_update(context: Context, args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    payload = read_input(args.input)
    guard_prohibited_content(payload)
    patch, summary, authority, confirmed, material_hint = _operation_controls(
        payload,
        command="update",
        allowed_patch_fields=BASELINE_PATCH_FIELDS,
    )
    validate_patch_value_types(patch, BASELINE_PATCH_TYPES, "update")

    def mutate(current: PlanRecord) -> ProposedMutation | None:
        if not patch:
            return None
        proposed = copy.deepcopy(current.plan)
        for key, value in patch.items():
            proposed[key] = copy.deepcopy(value)
        if "sources" in patch:
            validate_agent_inspected_local_sources(
                _sources_requiring_live_validation(
                    current.plan["sources"], proposed["sources"]
                ),
                context,
            )
        _assert_preserved_baseline(current.plan, proposed, confirmed=confirmed)
        if all(proposed.get(key) == current.plan.get(key) for key in patch):
            return None
        material_keys = set(patch) - {"requirements"}
        if "project" in material_keys and _project_patch_is_observation_only(
            current.plan["project"], proposed["project"]
        ):
            material_keys.remove("project")
        material = material_hint or bool(material_keys)
        if "requirements" in patch and _requirements_materially_differ(
            current.plan["requirements"], proposed["requirements"]
        ):
            material = True
        if material and current.plan["status"] in {"completed", "retired", "cancelled"}:
            raise AppError(
                "prohibited_transition",
                "Restore or reopen the plan before changing its material baseline.",
            )
        if material:
            _ensure_no_active_tasks_for_material(current.plan)
        status_before = current.plan["status"]
        if material and current.plan["status"] != "draft":
            proposed["status"] = "draft"
            proposed["status_reason"] = (
                "Material baseline changed; renewed validation and approval are required."
            )
        return ProposedMutation(
            plan=proposed,
            affected_ids=_baseline_affected_ids(current.plan, proposed, patch),
            status_before=status_before,
            status_after=proposed["status"],
            summary=summary,
            authority_basis=authority,
        )

    return mutate_existing_plan(
        context,
        selector=args.selector,
        expected_revision=args.expect_revision,
        expected_sha256=parse_expected_hash(args.expect_sha256),
        command="update",
        action_id="TO-IP-004",
        mutator=mutate,
    )


PHASE_PATCH_FIELDS = {
    "title",
    "objective",
    "scope",
    "depends_on_phase_ids",
    "entry_conditions",
    "exit_criteria",
    "risks",
}
PHASE_PATCH_TYPES: dict[str, tuple[type, ...]] = {
    "title": (str,),
    "objective": (str,),
    "scope": (list,),
    "depends_on_phase_ids": (list,),
    "entry_conditions": (list,),
    "exit_criteria": (list,),
    "risks": (list,),
}


def handle_update_phase(context: Context, args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    _assert_local_id(args.phase_id, PHASE_ID_RE, "phase ID")
    payload = read_input(args.input)
    patch, summary, authority, _, _ = _operation_controls(
        payload,
        command="update-phase",
        allowed_patch_fields=PHASE_PATCH_FIELDS,
    )
    validate_patch_value_types(patch, PHASE_PATCH_TYPES, "update-phase")

    def mutate(current: PlanRecord) -> ProposedMutation | None:
        phase = _find_record(current.plan["phases"], "phase_id", args.phase_id, "phase")
        if not patch or all(phase.get(key) == value for key, value in patch.items()):
            return None
        if current.plan["status"] in {"completed", "retired", "cancelled"}:
            raise AppError(
                "prohibited_transition",
                "Restore or reopen the plan before changing phase content.",
            )
        _ensure_no_active_tasks_for_material(current.plan)
        proposed = copy.deepcopy(current.plan)
        target = _find_record(proposed["phases"], "phase_id", args.phase_id, "phase")
        for key, value in patch.items():
            target[key] = copy.deepcopy(value)
        status_before = current.plan["status"]
        if proposed["status"] != "draft":
            proposed["status"] = "draft"
            proposed["status_reason"] = (
                "Phase baseline changed; renewed validation and approval are required."
            )
        return ProposedMutation(
            plan=proposed,
            affected_ids=[args.phase_id],
            status_before=status_before,
            status_after=proposed["status"],
            summary=summary,
            authority_basis=authority,
        )

    return mutate_existing_plan(
        context,
        selector=args.selector,
        expected_revision=args.expect_revision,
        expected_sha256=parse_expected_hash(args.expect_sha256),
        command="update-phase",
        action_id="TO-IP-005",
        mutator=mutate,
    )


TASK_PATCH_FIELDS = {
    "title",
    "action",
    "requirement_ids",
    "design_basis",
    "target_artifacts",
    "dependencies",
    "parallel_group",
    "risks",
    "acceptance_criteria",
    "verification_steps",
    "status",
    "blocker_reason",
    "pause_reason",
    "skip_reason",
    "skip_authority",
}
TASK_PATCH_TYPES: dict[str, tuple[type, ...]] = {
    "title": (str,),
    "action": (str,),
    "requirement_ids": (list,),
    "design_basis": (list,),
    "target_artifacts": (list,),
    "dependencies": (list,),
    "parallel_group": (str, type(None)),
    "risks": (list,),
    "acceptance_criteria": (list,),
    "verification_steps": (list,),
    "status": (str,),
    "blocker_reason": (str, type(None)),
    "pause_reason": (str, type(None)),
    "skip_reason": (str, type(None)),
    "skip_authority": (str, type(None)),
}
TASK_CONTENT_FIELDS = TASK_PATCH_FIELDS - {
    "status",
    "blocker_reason",
    "pause_reason",
    "skip_reason",
    "skip_authority",
}


def _gate_task_transition(
    plan: Mapping[str, Any],
    current_task: Mapping[str, Any],
    proposed_task: dict[str, Any],
    *,
    confirmed: bool,
) -> None:
    old_status = str(current_task["status"])
    new_status = str(proposed_task["status"])
    for field in (
        "blocker_reason",
        "pause_reason",
        "skip_reason",
        "skip_authority",
    ):
        value = proposed_task.get(field)
        if isinstance(value, str) and is_readiness_placeholder(value):
            raise AppError(
                "invalid_input",
                f"Task lifecycle field {field} cannot be placeholder text.",
                details={"targets": [str(current_task["task_id"]), field]},
            )
    if new_status == old_status:
        skip_exception_changed = new_status == "skipped" and any(
            proposed_task.get(field) != current_task.get(field)
            for field in ("skip_reason", "skip_authority")
        )
        if skip_exception_changed:
            if plan["status"] != "in_progress":
                raise AppError(
                    "unmet_gate",
                    "A skipped-task exception can change only while the exact plan is in_progress.",
                    details={
                        "targets": [
                            str(current_task["task_id"]),
                            str(plan["plan_id"]),
                        ]
                    },
                )
            if not confirmed:
                raise AppError(
                    "unmet_gate",
                    "Changing a skipped-task exception requires confirmed: true in the input.",
                )
            if not proposed_task.get("skip_reason") or not proposed_task.get(
                "skip_authority"
            ):
                raise AppError(
                    "unmet_gate",
                    "A skipped-task exception requires skip_reason and skip_authority.",
                )
            if not skipped_task_is_disposed(proposed_task, plan):
                raise AppError(
                    "unmet_gate",
                    "Changing this skipped-task exception requires accepted dispositions for its requirement coverage.",
                    details={
                        "targets": list(proposed_task.get("requirement_ids", []))
                    },
                )
        return
    if new_status not in TASK_TRANSITIONS.get(old_status, set()):
        raise AppError(
            "prohibited_transition",
            f"Task transition {old_status} -> {new_status} is not allowed.",
        )
    if plan["status"] != "in_progress":
        raise AppError(
            "unmet_gate",
            "Task lifecycle changes require the exact plan to be in_progress.",
            details={"targets": [str(current_task["task_id"]), str(plan["plan_id"])]},
        )
    tasks = {
        task["task_id"]: task for task in plan["tasks"] if isinstance(task, dict)
    }
    if new_status in {"in_progress", "completed"}:
        unfinished = [
            dependency
            for dependency in proposed_task["dependencies"]
            if tasks.get(dependency, {}).get("status") not in {"completed", "skipped"}
            or (
                tasks.get(dependency, {}).get("status") == "skipped"
                and not skipped_task_is_disposed(tasks[dependency], plan)
            )
        ]
        if unfinished:
            raise AppError(
                "unmet_gate",
                "Task predecessors are not completed or validly skipped.",
                details={"targets": unfinished},
            )
        phases = {
            str(phase.get("phase_id")): phase
            for phase in plan.get("phases", [])
            if isinstance(phase, Mapping)
        }
        current_phase = phases.get(str(proposed_task.get("phase_id")), {})
        unfinished_phases = [
            str(phase_id)
            for phase_id in list_or_empty(
                current_phase.get("depends_on_phase_ids")
            )
            if isinstance(phase_id, str)
            and phases.get(phase_id, {}).get("status") != "completed"
        ]
        if unfinished_phases:
            raise AppError(
                "unmet_gate",
                "Task execution cannot enter a phase whose predecessor phases are incomplete.",
                details={"targets": unfinished_phases},
            )
    if new_status == "completed":
        if missing_criterion_evidence(
            proposed_task["acceptance_criteria"],
            proposed_task["evidence"],
            target_definition_digest(proposed_task, "task", plan),
        ):
            raise AppError(
                "unmet_gate",
                "Task completion lacks meaningful evidence for every acceptance criterion.",
                details={"targets": [str(current_task["task_id"])]},
            )
        proposed_task["completed_at"] = timestamp()
        proposed_task["blocker_reason"] = None
        proposed_task["pause_reason"] = None
        proposed_task["skip_reason"] = None
        proposed_task["skip_authority"] = None
    elif new_status == "skipped":
        if not confirmed:
            raise AppError("unmet_gate", "Skipping a task requires confirmed: true in the input.")
        if not proposed_task.get("skip_reason") or not proposed_task.get("skip_authority"):
            raise AppError("unmet_gate", "Skipping a task requires skip_reason and skip_authority.")
        if not skipped_task_is_disposed(proposed_task, plan):
            raise AppError(
                "unmet_gate",
                "Skipping this task requires accepted dispositions for its requirement coverage.",
                details={"targets": list(proposed_task.get("requirement_ids", []))},
            )
        proposed_task["completed_at"] = None
        proposed_task["blocker_reason"] = None
        proposed_task["pause_reason"] = None
    elif old_status == "completed" and new_status == "in_progress":
        if not confirmed:
            raise AppError("unmet_gate", "Reopening a completed task requires confirmed: true.")
        dependents = [
            task_id
            for task_id, task in tasks.items()
            if current_task["task_id"] in task.get("dependencies", [])
            and task.get("status") in {"in_progress", "completed"}
        ]
        if dependents:
            raise AppError(
                "unmet_gate",
                "Reopen dependent tasks before reopening their predecessor.",
                details={"targets": dependents},
            )
        proposed_task["completed_at"] = None
        proposed_task["blocker_reason"] = None
        proposed_task["pause_reason"] = None
        proposed_task["skip_reason"] = None
        proposed_task["skip_authority"] = None
    elif old_status == "skipped" and new_status == "planned":
        if not confirmed:
            raise AppError("unmet_gate", "Restoring a skipped task requires confirmed: true.")
        proposed_task["skip_reason"] = None
        proposed_task["skip_authority"] = None
        proposed_task["blocker_reason"] = None
        proposed_task["pause_reason"] = None
        proposed_task["completed_at"] = None
    elif new_status == "blocked":
        if not proposed_task.get("blocker_reason"):
            raise AppError("unmet_gate", "A blocked task requires blocker_reason.")
        proposed_task["pause_reason"] = None
        proposed_task["skip_reason"] = None
        proposed_task["skip_authority"] = None
        proposed_task["completed_at"] = None
    elif new_status == "paused":
        if not proposed_task.get("pause_reason"):
            raise AppError("unmet_gate", "A paused task requires pause_reason.")
        proposed_task["blocker_reason"] = None
        proposed_task["skip_reason"] = None
        proposed_task["skip_authority"] = None
        proposed_task["completed_at"] = None
    elif new_status == "in_progress":
        proposed_task["blocker_reason"] = None
        proposed_task["pause_reason"] = None
        proposed_task["skip_reason"] = None
        proposed_task["skip_authority"] = None
        proposed_task["completed_at"] = None


def handle_update_task(context: Context, args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    _assert_local_id(args.task_id, TASK_ID_RE, "task ID")
    payload = read_input(args.input)
    patch, summary, authority, confirmed, _ = _operation_controls(
        payload,
        command="update-task",
        allowed_patch_fields=TASK_PATCH_FIELDS,
    )
    validate_patch_value_types(patch, TASK_PATCH_TYPES, "update-task")

    def mutate(current: PlanRecord) -> ProposedMutation | None:
        current_task = _find_record(current.plan["tasks"], "task_id", args.task_id, "task")
        if not patch or all(current_task.get(key) == value for key, value in patch.items()):
            return None
        content_change = bool(set(patch) & TASK_CONTENT_FIELDS)
        if (
            content_change
            and "status" in patch
            and patch["status"] != current_task.get("status")
        ):
            raise AppError(
                "invalid_input",
                "Change task content and task lifecycle state in separate revision-safe operations.",
            )
        if content_change and current.plan["status"] in {"completed", "retired", "cancelled"}:
            raise AppError(
                "prohibited_transition",
                "Restore or reopen the plan before changing task content.",
            )
        if content_change and current_task.get("status") in {"skipped", "completed"}:
            raise AppError(
                "unmet_gate",
                "Restore or reopen this task before changing its content.",
                details={"targets": [args.task_id]},
            )
        if content_change and current_task.get("status") in {"paused", "blocked"}:
            reason_field = (
                "pause_reason"
                if current_task.get("status") == "paused"
                else "blocker_reason"
            )
            if not confirmed or not isinstance(patch.get(reason_field), str) or not patch[
                reason_field
            ].strip():
                raise AppError(
                    "unmet_gate",
                    "Changing paused or blocked task content requires confirmation and a renewed state reason.",
                    details={"targets": [args.task_id, reason_field]},
                )
        if content_change:
            _ensure_no_active_tasks_for_material(current.plan)
        proposed = copy.deepcopy(current.plan)
        task = _find_record(proposed["tasks"], "task_id", args.task_id, "task")
        for key, value in patch.items():
            task[key] = copy.deepcopy(value)
        _gate_task_transition(current.plan, current_task, task, confirmed=confirmed)
        if content_change and proposed["status"] != "draft":
            proposed["status"] = "draft"
            proposed["status_reason"] = (
                "Task baseline changed; renewed validation and approval are required."
            )
        return ProposedMutation(
            plan=proposed,
            affected_ids=[args.task_id],
            status_before=str(current_task["status"]),
            status_after=str(task["status"]),
            summary=summary,
            authority_basis=authority,
        )

    return mutate_existing_plan(
        context,
        selector=args.selector,
        expected_revision=args.expect_revision,
        expected_sha256=parse_expected_hash(args.expect_sha256),
        command="update-task",
        action_id="TO-IP-006",
        mutator=mutate,
    )


def handle_record_evidence(
    context: Context, args: argparse.Namespace
) -> tuple[dict[str, Any], int]:
    if not (
        REQUIREMENT_ID_RE.fullmatch(args.target_id) or TASK_ID_RE.fullmatch(args.target_id)
    ):
        raise AppError("invalid_input", "Evidence target must be one complete task or requirement ID.")
    payload = read_input(args.input)
    guard_prohibited_content(payload)
    allowed = {
        "evidence_id",
        "timestamp",
        "evidence_type",
        "result_status",
        "description",
        "locator_or_command",
        "observed_result",
        "verification_level",
        "observation_source",
        "authority_basis",
        "summary",
    }
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise AppError(
            "invalid_input",
            f"record-evidence input has {len(unknown)} unsupported field(s).",
        )
    authority = payload.pop(
        "authority_basis", "Current explicit evidence-recording instruction."
    )
    summary = payload.pop("summary", f"Recorded evidence for {args.target_id}.")
    if not isinstance(authority, str) or not authority.strip():
        raise AppError("invalid_input", "Evidence authority_basis must be nonblank.")
    if not isinstance(summary, str) or not summary.strip():
        raise AppError("invalid_input", "Evidence summary must be nonblank.")

    def mutate(current: PlanRecord) -> ProposedMutation | None:
        proposed = copy.deepcopy(current.plan)
        collection = "tasks" if TASK_ID_RE.fullmatch(args.target_id) else "requirements"
        key = "task_id" if collection == "tasks" else "requirement_id"
        target = _find_record(proposed[collection], key, args.target_id, "evidence target")
        if (
            payload.get("evidence_type", "planned_check") != "planned_check"
            and current.plan.get("status") != "in_progress"
        ):
            raise AppError(
                "unmet_gate",
                "Observed or not-exercised implementation evidence requires the exact plan to be in_progress.",
                details={"targets": [str(current.plan["plan_id"]), args.target_id]},
            )
        existing = _evidence_index(current.plan)
        used_ids = set(existing)
        evidence = _normalize_evidence(
            copy.deepcopy(payload),
            used_ids,
            timestamp(),
            target_definition_digest(
                target,
                "task" if collection == "tasks" else "requirement",
                current.plan,
            ),
        )
        evidence_id = evidence["evidence_id"]
        if evidence_id in existing:
            old_target, old_evidence = existing[evidence_id]
            if old_target == args.target_id and old_evidence == evidence:
                return None
            raise AppError(
                "invalid_input",
                "Evidence identifier already exists and cannot be reused.",
                details={"targets": [evidence_id]},
            )
        temporary_errors: list[dict[str, Any]] = []
        _check_evidence_record(evidence, "evidence", temporary_errors, set())
        if temporary_errors:
            raise AppError(
                "invalid_input",
                "Evidence does not satisfy the V1 contract.",
                details={"findings": temporary_errors},
            )
        if is_meaningless_evidence_text(evidence["observed_result"]):
            raise AppError(
                "invalid_input",
                "Evidence observed_result is a meaningless completion marker.",
            )
        if is_meaningless_evidence_text(evidence["description"]):
            raise AppError("invalid_input", "Evidence description is not meaningful.")
        target["evidence"].append(evidence)
        return ProposedMutation(
            plan=proposed,
            affected_ids=[args.target_id, evidence_id],
            status_before=str(target.get("status")),
            status_after=str(target.get("status")),
            summary=summary.strip(),
            authority_basis=authority.strip(),
        )

    return mutate_existing_plan(
        context,
        selector=args.selector,
        expected_revision=args.expect_revision,
        expected_sha256=parse_expected_hash(args.expect_sha256),
        command="record-evidence",
        action_id="TO-IP-007",
        mutator=mutate,
    )


def handle_set_status(context: Context, args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    guard_prohibited_content({"reason": args.reason})
    if not args.reason.strip() or len(args.reason) > MAX_SHORT_TEXT:
        raise AppError("invalid_input", "--reason must be concise and nonblank.")
    if is_readiness_placeholder(args.reason):
        raise AppError("invalid_input", "--reason cannot be placeholder text.")
    if not args.confirmed:
        raise AppError("unmet_gate", "Plan lifecycle changes require --confirmed.")

    def mutate(current: PlanRecord) -> ProposedMutation | None:
        old_status = current.plan["status"]
        new_status = args.status_value
        if old_status == new_status:
            if current.plan["status_reason"] == args.reason.strip():
                return None
            raise AppError(
                "prohibited_transition",
                "set-status does not rewrite a reason without a lifecycle transition.",
            )
        if new_status not in PLAN_TRANSITIONS.get(old_status, set()):
            raise AppError(
                "prohibited_transition",
                f"Plan transition {old_status} -> {new_status} is not allowed.",
            )
        if new_status in {"draft", "paused", "blocked", "cancelled"}:
            _ensure_no_active_tasks_for_material(current.plan)
        if new_status == "ready":
            blockers = readiness_findings(current.plan)
            if blockers:
                raise AppError(
                    "unmet_gate",
                    "The exact canonical revision does not satisfy readiness gates.",
                    details={"findings": blockers},
                )
        if old_status == "ready" and new_status == "in_progress":
            # --confirmed is the current exact-plan execution instruction.
            if current.plan["validation"]["status"] != "pass":
                raise AppError(
                    "unmet_gate",
                    "Execution cannot start from a plan whose validation is not pass.",
                )
        if old_status == "completed" and new_status == "in_progress" and not args.confirmed:
            raise AppError("unmet_gate", "Reopening a completed plan requires confirmation.")
        if new_status == "completed":
            blockers = completion_findings(current.plan)
            if blockers:
                raise AppError(
                    "unmet_gate",
                    "The exact canonical revision does not satisfy completion gates.",
                    details={"findings": blockers},
                )
        proposed = copy.deepcopy(current.plan)
        proposed["status"] = new_status
        transition_summary = args.reason.strip()
        if new_status == "completed":
            normalized_reason = " ".join(
                re.sub(
                    r"[_\W]+",
                    " ",
                    unicodedata.normalize("NFKC", transition_summary).casefold(),
                ).split()
            )
            verification_aliases = {
                "highest verification level",
                "inspected only",
                "static checks",
                "static checks passed",
                "targeted tests",
                "targeted tests passed",
                "broader suite",
                "broader suite passed",
                "runtime observed",
                "end to end",
                "end to end verified",
                "e2e",
                "e2e verified",
                "end2end",
                "end2end verified",
                "broader test suite",
                "broader test suite passed",
                "targeted test suite",
                "targeted test suite passed",
                "not exercised",
            }
            padded_reason = f" {normalized_reason} "
            verification_claim_tokens = {
                "broader",
                "e2e",
                "end2end",
                "exercised",
                "inspected",
                "runtime",
                "static",
                "suite",
                "targeted",
                "test",
                "tested",
                "tests",
                "verification",
                "verified",
            }
            reason_tokens = set(normalized_reason.split())
            compact_reason = normalized_reason.replace(" ", "")
            if (
                any(f" {alias} " in padded_reason for alias in verification_aliases)
                or bool(reason_tokens & verification_claim_tokens)
                or "e2e" in compact_reason
                or "end2end" in compact_reason
            ):
                raise AppError(
                    "invalid_input",
                    "Completion reason must not supply a verification-level claim; the helper records the computed level.",
                )
            level = highest_verification_level(current.plan)
            transition_summary = (
                f"{transition_summary.rstrip('.')}. "
                f"Highest verification level reached: {level}."
            )
            if len(transition_summary) > MAX_SHORT_TEXT:
                raise AppError(
                    "invalid_input",
                    "Completion reason is too long after adding the computed verification level.",
                )
        proposed["status_reason"] = transition_summary
        return ProposedMutation(
            plan=proposed,
            affected_ids=[],
            status_before=old_status,
            status_after=new_status,
            summary=transition_summary,
            authority_basis=(
                "Current explicit confirmed lifecycle instruction for the exact plan revision."
            ),
        )

    return mutate_existing_plan(
        context,
        selector=args.selector,
        expected_revision=args.expect_revision,
        expected_sha256=parse_expected_hash(args.expect_sha256),
        command="set-status",
        action_id="TO-IP-008",
        mutator=mutate,
    )


def _pid_is_active(owner: Mapping[str, Any]) -> bool | None:
    host = owner.get("host")
    pid = owner.get("pid")
    if host != socket.gethostname() or isinstance(pid, bool) or not isinstance(pid, int):
        return None
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return None
    return True


def _remove_reviewed_lock(lock_path: Path, token: str) -> bool:
    parent_fd = open_directory_without_symlinks(
        lock_path.parent, label="reviewed-lock parent"
    )
    lock_fd: int | None = None
    try:
        parent_info = os.fstat(parent_fd)
        parent_identity = (parent_info.st_dev, parent_info.st_ino)
        try:
            entry_info = os.stat(
                lock_path.name, dir_fd=parent_fd, follow_symlinks=False
            )
        except FileNotFoundError:
            return False
        if stat.S_ISLNK(entry_info.st_mode) or not stat.S_ISDIR(
            entry_info.st_mode
        ):
            raise AppError(
                "unsafe_or_corrupt",
                "The reviewed lock path is not helper-owned.",
            )
        lock_fd = os.open(
            lock_path.name,
            os.O_RDONLY
            | os.O_DIRECTORY
            | os.O_NOFOLLOW
            | getattr(os, "O_CLOEXEC", 0),
            dir_fd=parent_fd,
        )
        bound_info = os.fstat(lock_fd)
        lock_identity = (bound_info.st_dev, bound_info.st_ino)
        if lock_identity != (entry_info.st_dev, entry_info.st_ino):
            raise AppError(
                "unsafe_or_corrupt",
                "The reviewed lock changed while it was being bound.",
            )
        owner, owner_raw = read_lock_owner_from_fd(lock_fd)
        if owner is None or owner_raw is None or owner.get("token") != token:
            raise AppError(
                "unsafe_or_corrupt",
                "The reviewed lock owner or token does not match; the lock was preserved.",
            )
        if _pid_is_active(owner) is not False:
            raise AppError(
                "active_lock",
                "The reviewed lock may still have an active writer and was preserved.",
                details={"owner": owner},
            )
        if sorted(os.listdir(lock_fd)) != ["owner.json"]:
            raise AppError(
                "unsafe_or_corrupt",
                "The reviewed lock contains unknown files and was preserved.",
            )
        if not directory_path_matches_identity(
            lock_path.parent,
            parent_identity,
            label="reviewed-lock parent",
        ) or not directory_path_matches_identity(
            lock_path, lock_identity, label="reviewed lock"
        ):
            raise AppError(
                "unsafe_or_corrupt",
                "The reviewed lock path changed before removal; it was preserved.",
            )
        released_name = f"{lock_path.name}.released-{token}"
        released_path = lock_path.parent / released_name
        removal_completed = False
        try:
            os.rename(
                lock_path.name,
                released_name,
                src_dir_fd=parent_fd,
                dst_dir_fd=parent_fd,
            )
            removal_completed = True
            os.fsync(parent_fd)
            os.unlink("owner.json", dir_fd=lock_fd)
            os.rmdir(released_name, dir_fd=parent_fd)
            os.fsync(parent_fd)
        except (OSError, KeyboardInterrupt) as exc:
            raise AppError(
                "io_error",
                "Cannot durably remove the reviewed abandoned lock.",
                details={
                    "removal_completed": removal_completed,
                    "lock_path": str(lock_path),
                    "token": token,
                    "release_renamed": removal_completed,
                    "released_lock_path": str(released_path)
                    if removal_completed
                    else None,
                    "released_lock_name": released_name
                    if removal_completed
                    else None,
                    "owner_sha256": sha256_bytes(owner_raw),
                },
            ) from exc
        return True
    except OSError as exc:
        raise AppError("io_error", "Cannot inspect the reviewed lock.") from exc
    finally:
        if lock_fd is not None:
            os.close(lock_fd)
        os.close(parent_fd)


def _reviewed_temp_path(
    context: Context,
    record: PlanRecord | None,
    scope: str,
    relative_path: str,
) -> Path:
    if not isinstance(relative_path, str) or not relative_path or "\x00" in relative_path:
        raise AppError("invalid_input", "Recovery relative_path is invalid.")
    candidate_relative = Path(relative_path)
    if candidate_relative.is_absolute() or any(
        part in {"", ".", ".."} for part in candidate_relative.parts
    ):
        raise AppError("unsafe_or_corrupt", "Recovery target has a traversal form.")
    if scope == "catalog":
        if len(candidate_relative.parts) != 1 or not re.fullmatch(
            r"^\.INDEX\.md\.tmp-[A-F0-9]{32}$", candidate_relative.name
        ):
            raise AppError("unsafe_or_corrupt", "Recovery target is not a catalog temporary file.")
        target = context.plans_root / candidate_relative
    elif scope == "plan":
        if record is None:
            raise AppError("invalid_input", "Plan recovery requires an exact plan selector.")
        if len(candidate_relative.parts) == 1:
            if not TEMP_FILE_RE.fullmatch(candidate_relative.name) or candidate_relative.name.startswith(
                ".INDEX.md"
            ):
                raise AppError("unsafe_or_corrupt", "Recovery target is not a plan temporary file.")
        elif len(candidate_relative.parts) == 2 and candidate_relative.parts[0] == "phases":
            if not TEMP_FILE_RE.fullmatch(candidate_relative.name):
                raise AppError("unsafe_or_corrupt", "Recovery target is not a phase temporary file.")
        else:
            raise AppError("unsafe_or_corrupt", "Recovery target is outside the reviewed scope.")
        target = record.path / candidate_relative
    else:
        raise AppError("invalid_input", "Recovery scope must be plan or catalog.")
    target = Path(os.path.abspath(target))
    ensure_confined(context.project_root, target, "recovery target")
    ensure_no_symlink_components(context.project_root, target.parent, "recovery target parent")
    return target


def remove_released_lock_residue_bound(
    *,
    parent_path: Path,
    expected_parent_identity: tuple[int, int],
    relative_name: str,
    token: str,
    expected_owner_hash: str | None,
) -> bool:
    parent_fd = open_directory_without_symlinks(
        parent_path, label="released-lock parent"
    )
    target_fd: int | None = None
    changed = False
    try:
        parent_info = os.fstat(parent_fd)
        parent_identity = (parent_info.st_dev, parent_info.st_ino)
        if parent_identity != expected_parent_identity:
            raise AppError(
                "unsafe_or_corrupt", "Released-lock parent identity changed."
            )
        try:
            target_info = os.stat(
                relative_name, dir_fd=parent_fd, follow_symlinks=False
            )
        except FileNotFoundError:
            return False
        if stat.S_ISLNK(target_info.st_mode) or not stat.S_ISDIR(
            target_info.st_mode
        ):
            raise AppError(
                "unsafe_or_corrupt", "Released-lock residue is not a directory."
            )
        target_fd = os.open(
            relative_name,
            os.O_RDONLY
            | os.O_DIRECTORY
            | os.O_NOFOLLOW
            | getattr(os, "O_CLOEXEC", 0),
            dir_fd=parent_fd,
        )
        bound_info = os.fstat(target_fd)
        target_identity = (bound_info.st_dev, bound_info.st_ino)
        if target_identity != (target_info.st_dev, target_info.st_ino):
            raise AppError(
                "unsafe_or_corrupt", "Released-lock residue changed while binding."
            )
        names = sorted(os.listdir(target_fd))
        if names not in ([], ["owner.json"]):
            raise AppError(
                "unsafe_or_corrupt",
                "Released-lock residue contains unknown content.",
            )
        if names == ["owner.json"]:
            owner, owner_raw = read_lock_owner_from_fd(target_fd)
            if owner_raw is None:
                raise AppError(
                    "unsafe_or_corrupt", "Released-lock owner is unreadable."
                )
            if expected_owner_hash is not None:
                if sha256_bytes(owner_raw) != expected_owner_hash.lower():
                    raise AppError(
                        "stale_state",
                        "Released-lock owner SHA-256 no longer matches.",
                    )
            elif owner is None or owner.get("token") != token:
                raise AppError(
                    "unsafe_or_corrupt",
                    "Released-lock owner does not match the token.",
                )
            if owner is not None and owner.get("token") == token:
                if _pid_is_active(owner) is True:
                    raise AppError(
                        "active_lock",
                        "The released-lock owner process is still active; retry after it exits.",
                    )
        if not directory_path_matches_identity(
            parent_path,
            parent_identity,
            label="released-lock parent",
        ) or not directory_path_matches_identity(
            parent_path / relative_name,
            target_identity,
            label="released-lock residue",
        ):
            raise AppError(
                "unsafe_or_corrupt",
                "Released-lock residue path changed before cleanup.",
            )
        try:
            if names == ["owner.json"]:
                os.unlink("owner.json", dir_fd=target_fd)
                changed = True
            os.rmdir(relative_name, dir_fd=parent_fd)
            changed = True
            os.fsync(parent_fd)
        except (OSError, KeyboardInterrupt) as exc:
            raise AppError(
                "io_error",
                "Released-lock cleanup did not finish durably.",
                details={"removal_completed": changed, "filesystem_mutation": changed},
            ) from exc
        return True
    finally:
        if target_fd is not None:
            os.close(target_fd)
        os.close(parent_fd)


def remove_partial_create_bound(
    *,
    catalog_path: Path,
    expected_catalog_identity: tuple[int, int],
    directory: str,
    expected_state: str,
    relative_path: str | None,
    expected_hash: str | None,
) -> bool:
    catalog_fd = open_directory_without_symlinks(
        catalog_path, label="partial-create catalog"
    )
    partial_fd: int | None = None
    changed = False
    try:
        catalog_info = os.fstat(catalog_fd)
        catalog_identity = (catalog_info.st_dev, catalog_info.st_ino)
        if catalog_identity != expected_catalog_identity:
            raise AppError(
                "unsafe_or_corrupt", "Partial-create catalog identity changed."
            )
        try:
            entry_info = os.stat(directory, dir_fd=catalog_fd, follow_symlinks=False)
        except FileNotFoundError:
            return False
        if stat.S_ISLNK(entry_info.st_mode) or not stat.S_ISDIR(entry_info.st_mode):
            raise AppError(
                "unsafe_or_corrupt",
                "Reviewed partial-create target is not a regular directory.",
            )
        partial_fd = os.open(
            directory,
            os.O_RDONLY
            | os.O_DIRECTORY
            | os.O_NOFOLLOW
            | getattr(os, "O_CLOEXEC", 0),
            dir_fd=catalog_fd,
        )
        bound_info = os.fstat(partial_fd)
        partial_identity = (bound_info.st_dev, bound_info.st_ino)
        if partial_identity != (entry_info.st_dev, entry_info.st_ino):
            raise AppError(
                "unsafe_or_corrupt", "Partial-create directory changed while binding."
            )
        names = sorted(os.listdir(partial_fd))
        if expected_state == "empty":
            if names:
                raise AppError(
                    "stale_state",
                    "Reviewed empty partial-create directory now contains content.",
                )
        else:
            if names != [relative_path]:
                raise AppError(
                    "unsafe_or_corrupt",
                    "Reviewed partial-create directory contains unknown content.",
                )
            assert isinstance(relative_path, str)
            assert isinstance(expected_hash, str)
            if sha256_regular_file_at(partial_fd, relative_path) != expected_hash.lower():
                raise AppError(
                    "stale_state", "Reviewed partial-create SHA-256 no longer matches."
                )
        if not directory_path_matches_identity(
            catalog_path,
            catalog_identity,
            label="partial-create catalog",
        ) or not directory_path_matches_identity(
            catalog_path / directory,
            partial_identity,
            label="partial-create directory",
        ):
            raise AppError(
                "unsafe_or_corrupt",
                "Partial-create path changed before cleanup.",
            )
        try:
            if expected_state == "temporary":
                assert isinstance(relative_path, str)
                os.unlink(relative_path, dir_fd=partial_fd)
                changed = True
                os.fsync(partial_fd)
            os.rmdir(directory, dir_fd=catalog_fd)
            changed = True
            os.fsync(catalog_fd)
        except (OSError, KeyboardInterrupt) as exc:
            raise AppError(
                "io_error",
                "Partial-create cleanup did not finish durably.",
                details={"removal_completed": changed, "filesystem_mutation": changed},
            ) from exc
        return True
    finally:
        if partial_fd is not None:
            os.close(partial_fd)
        os.close(catalog_fd)


def remove_orphan_temp_bound(
    *,
    parent_path: Path,
    expected_parent_identity: tuple[int, int],
    target_name: str,
    expected_hash: str,
) -> bool:
    parent_fd = open_directory_without_symlinks(
        parent_path, label="orphan-temporary parent"
    )
    try:
        parent_info = os.fstat(parent_fd)
        parent_identity = (parent_info.st_dev, parent_info.st_ino)
        if parent_identity != expected_parent_identity:
            raise AppError(
                "unsafe_or_corrupt", "Orphan-temporary parent identity changed."
            )
        try:
            info = os.stat(target_name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            return False
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            raise AppError(
                "unsafe_or_corrupt", "Reviewed temporary target is not a regular file."
            )
        if sha256_regular_file_at(parent_fd, target_name) != expected_hash.lower():
            raise AppError(
                "stale_state", "Reviewed temporary-file SHA-256 no longer matches."
            )
        if not directory_path_matches_identity(
            parent_path,
            parent_identity,
            label="orphan-temporary parent",
        ):
            raise AppError(
                "unsafe_or_corrupt", "Temporary-file parent changed before removal."
            )
        try:
            os.unlink(target_name, dir_fd=parent_fd)
            os.fsync(parent_fd)
        except (OSError, KeyboardInterrupt) as exc:
            # If unlink succeeded, a retry is a safe no-op; report the mutation.
            try:
                os.stat(target_name, dir_fd=parent_fd, follow_symlinks=False)
                changed = False
            except FileNotFoundError:
                changed = True
            raise AppError(
                "io_error",
                "Temporary-file cleanup did not finish durably.",
                details={"removal_completed": changed, "filesystem_mutation": changed},
            ) from exc
        return True
    finally:
        os.close(parent_fd)


def catalog_path_is_absent(context: Context) -> bool:
    """Check catalog absence without following a dangling or hostile symlink."""
    try:
        context.plans_root.lstat()
    except FileNotFoundError:
        return True
    except OSError as exc:
        raise AppError("io_error", "Cannot inspect the catalog recovery path.") from exc
    return False


def handle_reconcile(context: Context, args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    if not args.confirmed:
        raise AppError("unmet_gate", "reconcile requires --confirmed.")
    payload = read_input(args.input)
    guard_prohibited_content(payload)
    action = payload.get("action")
    scope = payload.get("scope", "plan")
    if not isinstance(action, str) or not isinstance(scope, str):
        raise AppError("invalid_input", "Recovery action and scope must be strings.")
    if scope not in {"plan", "catalog"}:
        raise AppError("invalid_input", "Recovery scope must be plan or catalog.")
    if scope == "catalog":
        if args.selector != "catalog":
            raise AppError(
                "invalid_input",
                "Catalog recovery requires the literal selector catalog.",
            )
        record: PlanRecord | None = None
    else:
        if args.selector == "catalog":
            raise AppError("invalid_input", "Plan recovery requires an exact plan selector.")
        record = select_plan(context, args.selector)

    def receipt_for(selected: PlanRecord | None) -> dict[str, Any] | None:
        if selected is None:
            return None
        current_record = load_plan_record(context, selected.path)
        return plan_receipt(
            current_record,
            canonical_committed=False,
            projection_status="not_checked",
            index_status="not_checked",
        )

    def absent_catalog_no_op(target: Path) -> tuple[dict[str, Any], int] | None:
        if record is not None or not catalog_path_is_absent(context):
            return None
        return (
            make_envelope(
                context,
                "reconcile",
                status="no_op",
                mutation=False,
                data={"action": action, "scope": scope, "target": str(target)},
            ),
            0,
        )

    if action == "remove_abandoned_lock":
        allowed = {"action", "scope", "token"}
        unknown = set(payload) - allowed
        if unknown:
            raise AppError("invalid_input", "Lock recovery input has unsupported fields.")
        token = payload.get("token")
        if not isinstance(token, str) or not re.fullmatch(
            r"[A-F0-9]{32}", token
        ):
            raise AppError("invalid_input", "Lock recovery requires exact scope and owner token.")
        lock_path = (
            plan_lock_path(record.path) if record is not None else catalog_lock_path(context)
        )
        absent = absent_catalog_no_op(lock_path)
        if absent is not None:
            return absent
        if scope == "plan" and catalog_lock_path(context).exists():
            raise AppError(
                "active_lock",
                "The catalog lock may own this plan operation; the plan lock was preserved.",
            )
        if record is None:
            # Validate every managed canonical record before removing the lock;
            # recovery must not expose an already-corrupt catalog to writers.
            discover_managed_plans(context)
        try:
            changed = _remove_reviewed_lock(lock_path, token)
        except AppError as exc:
            if not exc.details.get("removal_completed"):
                raise
            if record is None:
                discover_managed_plans(context)
            return (
                make_envelope(
                    context,
                    "reconcile",
                    status="partial",
                    mutation=True,
                    errors=[
                        _result_warning(
                            "io_error",
                            "The reviewed lock was renamed for release, but cleanup or durability sync did not finish.",
                            str(lock_path),
                        )
                    ],
                    recovery_required=lock_cleanup_recovery(
                        lock_path, token, exc.details
                    ),
                    receipt=receipt_for(record),
                    data={"action": action, "scope": scope, "target": str(lock_path)},
                ),
                EXIT_CODES["io_error"],
            )
        if record is None:
            try:
                discover_managed_plans(context)
            except AppError as exc:
                return (
                    make_envelope(
                        context,
                        "reconcile",
                        status="partial",
                        mutation=True,
                        errors=[
                            _result_warning(
                                exc.category,
                                "The reviewed catalog lock was removed, but the post-removal catalog check failed.",
                                str(lock_path),
                            )
                        ],
                        recovery_required={
                            "command": "validate",
                            "selector": "catalog",
                        },
                        data={
                            "action": action,
                            "scope": scope,
                            "target": str(lock_path),
                            "failure_category": exc.category,
                        },
                    ),
                    EXIT_CODES["io_error"],
                )
        return (
            make_envelope(
                context,
                "reconcile",
                status="ok" if changed else "no_op",
                mutation=changed,
                receipt=receipt_for(record),
                data={"action": action, "scope": scope, "target": str(lock_path)},
            ),
            0,
        )
    if action == "remove_released_lock":
        allowed = {"action", "scope", "relative_name", "token", "owner_sha256"}
        if set(payload) - allowed:
            raise AppError(
                "invalid_input", "Released-lock recovery input has unsupported fields."
            )
        token = payload.get("token")
        expected_owner_hash = payload.get("owner_sha256")
        relative_name = payload.get("relative_name")
        if not isinstance(token, str) or not re.fullmatch(r"[A-F0-9]{32}", token):
            raise AppError("invalid_input", "Released-lock token is invalid.")
        if expected_owner_hash is not None and (
            not isinstance(expected_owner_hash, str)
            or not re.fullmatch(r"[a-fA-F0-9]{64}", expected_owner_hash)
        ):
            raise AppError("invalid_input", "Released-lock owner SHA-256 is invalid.")
        base_name = (
            ".to-implementation-plan.catalog.lock"
            if scope == "catalog"
            else ".to-implementation-plan.plan.lock"
        )
        expected_name = f"{base_name}.released-{token}"
        if relative_name != expected_name:
            raise AppError(
                "invalid_input", "Released-lock name does not match its scope and token."
            )
        parent_path = context.plans_root if record is None else record.path
        target = parent_path / expected_name
        absent = absent_catalog_no_op(target)
        if absent is not None:
            return absent
        outcome: dict[str, Any] | None = None
        exit_code = 0
        if record is None:
            ensure_catalog_for_write(context)
        lock_for_recovery = (
            catalog_lock_path(context)
            if record is None
            else plan_lock_path(record.path)
        )
        with held_lock(
            lock_for_recovery, "reconcile", lambda: outcome
        ) as recovery_handle:
            expected_parent_identity = (
                recovery_handle.parent_identity
                if record is None
                else record.directory_identity
            )
            if recovery_handle.parent_identity != expected_parent_identity:
                raise AppError(
                    "unsafe_or_corrupt",
                    "Recovery lock parent does not match the selected scope.",
                )
            try:
                changed = remove_released_lock_residue_bound(
                    parent_path=parent_path,
                    expected_parent_identity=expected_parent_identity,
                    relative_name=expected_name,
                    token=token,
                    expected_owner_hash=expected_owner_hash,
                )
            except AppError as exc:
                if not exc.details.get("removal_completed"):
                    raise
                outcome = make_envelope(
                    context,
                    "reconcile",
                    status="partial",
                    mutation=True,
                    errors=[
                        _result_warning(
                            "io_error",
                            "Released-lock cleanup changed residue but did not finish durably.",
                            str(target),
                        )
                    ],
                    recovery_required={
                        "command": "reconcile",
                        "selector": args.selector,
                        "input": copy.deepcopy(payload),
                        "then": "validate",
                    },
                    receipt=receipt_for(record),
                    data={"action": action, "scope": scope, "target": str(target)},
                )
                exit_code = EXIT_CODES["io_error"]
            else:
                outcome = make_envelope(
                    context,
                    "reconcile",
                    status="ok" if changed else "no_op",
                    mutation=changed,
                    receipt=receipt_for(record),
                    data={"action": action, "scope": scope, "target": str(target)},
                )
        if outcome is None:
            raise AppError("io_error", "Released-lock recovery ended without a receipt.")
        return outcome, exit_code
    if action == "remove_partial_create":
        allowed = {
            "action",
            "scope",
            "state",
            "directory",
            "relative_path",
            "sha256",
        }
        unknown = set(payload) - allowed
        if unknown:
            raise AppError(
                "invalid_input",
                "Partial-create recovery input has unsupported fields.",
            )
        if scope != "catalog" or record is not None:
            raise AppError(
                "invalid_input",
                "Partial-create recovery requires catalog scope and selector catalog.",
            )
        directory = payload.get("directory")
        expected_state = payload.get("state")
        relative_path = payload.get("relative_path")
        expected_hash = payload.get("sha256")
        if not isinstance(directory, str) or not DIRECTORY_RE.fullmatch(directory):
            raise AppError("invalid_input", "Partial-create directory is invalid.")
        if not isinstance(expected_state, str) or expected_state not in {
            "empty",
            "temporary",
        }:
            raise AppError("invalid_input", "Partial-create state is invalid.")
        if expected_state == "temporary":
            if not isinstance(relative_path, str) or not re.fullmatch(
                r"^\.plan\.json\.tmp-[A-F0-9]{32}$", relative_path
            ):
                raise AppError("invalid_input", "Partial-create temporary name is invalid.")
            if not isinstance(expected_hash, str) or not re.fullmatch(
                r"[a-fA-F0-9]{64}", expected_hash
            ):
                raise AppError("invalid_input", "Partial-create SHA-256 is invalid.")
        elif relative_path is not None or expected_hash is not None:
            raise AppError(
                "invalid_input",
                "Empty partial-create recovery must not name a temporary file or digest.",
            )
        partial_dir = context.plans_root / directory
        ensure_confined(context.project_root, partial_dir, "partial-create directory")
        absent = absent_catalog_no_op(partial_dir)
        if absent is not None:
            return absent
        ensure_catalog_for_write(context)
        outcome: dict[str, Any] | None = None
        exit_code = 0
        with held_lock(
            catalog_lock_path(context), "reconcile", lambda: outcome
        ) as recovery_handle:
            discover_managed_plans(context)
            try:
                changed = remove_partial_create_bound(
                    catalog_path=context.plans_root,
                    expected_catalog_identity=recovery_handle.parent_identity,
                    directory=directory,
                    expected_state=expected_state,
                    relative_path=relative_path,
                    expected_hash=expected_hash,
                )
            except AppError as exc:
                if not exc.details.get("removal_completed"):
                    raise
                retry_payload = copy.deepcopy(payload)
                if expected_state == "temporary":
                    retry_payload["state"] = "empty"
                    retry_payload.pop("relative_path", None)
                    retry_payload.pop("sha256", None)
                outcome = make_envelope(
                    context,
                    "reconcile",
                    status="partial",
                    mutation=True,
                    errors=[
                        _result_warning(
                            "io_error",
                            "Partial-create cleanup changed reviewed residue but did not finish durably.",
                            str(partial_dir),
                        )
                    ],
                    recovery_required={
                        "command": "reconcile",
                        "selector": "catalog",
                        "input": retry_payload,
                        "then": "validate",
                    },
                    data={
                        "action": action,
                        "scope": scope,
                        "target": str(partial_dir),
                    },
                )
                exit_code = EXIT_CODES["io_error"]
            else:
                outcome = make_envelope(
                    context,
                    "reconcile",
                    status="ok" if changed else "no_op",
                    mutation=changed,
                    data={
                        "action": action,
                        "scope": scope,
                        "target": str(partial_dir),
                    },
                )
        if outcome is None:
            raise AppError("io_error", "Partial-create recovery ended without a receipt.")
        return outcome, exit_code
    if action == "remove_orphan_temp":
        allowed = {"action", "scope", "relative_path", "sha256"}
        unknown = set(payload) - allowed
        if unknown:
            raise AppError("invalid_input", "Temporary-file recovery input has unsupported fields.")
        relative_path = payload.get("relative_path")
        expected_hash = payload.get("sha256")
        if not isinstance(relative_path, str):
            raise AppError("invalid_input", "Temporary-file recovery requires a relative path.")
        if not isinstance(expected_hash, str) or not re.fullmatch(r"[a-fA-F0-9]{64}", expected_hash):
            raise AppError("invalid_input", "Temporary-file recovery requires exact sha256.")
        if scope == "catalog":
            catalog_target = context.plans_root / Path(relative_path)
            absent = absent_catalog_no_op(catalog_target)
            if absent is not None:
                return absent
        target = _reviewed_temp_path(context, record, scope, relative_path)
        if scope == "plan" and catalog_lock_path(context).exists():
            raise AppError(
                "active_lock",
                "Catalog creation or mutation may own the reviewed plan temporary file.",
            )
        outcome: dict[str, Any] | None = None
        exit_code = 0
        if scope == "plan":
            assert record is not None
            with held_lock(
                plan_lock_path(record.path), "reconcile", lambda: outcome
            ) as recovery_handle:
                if recovery_handle.parent_identity != record.directory_identity:
                    raise AppError(
                        "unsafe_or_corrupt",
                        "Recovery lock parent does not match the selected plan.",
                    )
                current = load_plan_record(context, record.path)
                relative = Path(relative_path)
                if len(relative.parts) == 1:
                    parent_path = current.path
                    parent_identity = current.directory_identity
                    target_name = relative.name
                else:
                    plan_fd = open_directory_without_symlinks(
                        current.path, label="selected plan directory"
                    )
                    phases_fd: int | None = None
                    try:
                        plan_info = os.fstat(plan_fd)
                        if (plan_info.st_dev, plan_info.st_ino) != current.directory_identity:
                            raise AppError(
                                "unsafe_or_corrupt",
                                "Selected plan directory identity changed.",
                            )
                        phases_fd = os.open(
                            "phases",
                            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                            dir_fd=plan_fd,
                        )
                        phases_info = os.fstat(phases_fd)
                        parent_identity = (phases_info.st_dev, phases_info.st_ino)
                    finally:
                        if phases_fd is not None:
                            os.close(phases_fd)
                        os.close(plan_fd)
                    parent_path = current.path / "phases"
                    target_name = relative.name
                try:
                    changed = remove_orphan_temp_bound(
                        parent_path=parent_path,
                        expected_parent_identity=parent_identity,
                        target_name=target_name,
                        expected_hash=expected_hash,
                    )
                except AppError as exc:
                    if not exc.details.get("removal_completed"):
                        raise
                    outcome = make_envelope(
                        context,
                        "reconcile",
                        status="partial",
                        mutation=True,
                        errors=[
                            _result_warning(
                                "io_error",
                                "The reviewed temporary file was removed, but directory durability sync failed.",
                                str(target),
                            )
                        ],
                        recovery_required={
                            "command": "validate",
                            "selector": args.selector,
                        },
                        receipt=receipt_for(record),
                        data={"action": action, "scope": scope, "target": str(target)},
                    )
                    exit_code = EXIT_CODES["io_error"]
                else:
                    outcome = make_envelope(
                        context,
                        "reconcile",
                        status="ok" if changed else "no_op",
                        mutation=changed,
                        receipt=receipt_for(record),
                        data={"action": action, "scope": scope, "target": str(target)},
                    )
        else:
            ensure_catalog_for_write(context)
            with held_lock(
                catalog_lock_path(context), "reconcile", lambda: outcome
            ) as recovery_handle:
                discover_managed_plans(context)
                try:
                    changed = remove_orphan_temp_bound(
                        parent_path=context.plans_root,
                        expected_parent_identity=recovery_handle.parent_identity,
                        target_name=Path(relative_path).name,
                        expected_hash=expected_hash,
                    )
                except AppError as exc:
                    if not exc.details.get("removal_completed"):
                        raise
                    outcome = make_envelope(
                        context,
                        "reconcile",
                        status="partial",
                        mutation=True,
                        errors=[
                            _result_warning(
                                "io_error",
                                "The reviewed temporary file was removed, but directory durability sync failed.",
                                str(target),
                            )
                        ],
                        recovery_required={
                            "command": "validate",
                            "selector": args.selector,
                        },
                        data={"action": action, "scope": scope, "target": str(target)},
                    )
                    exit_code = EXIT_CODES["io_error"]
                else:
                    outcome = make_envelope(
                        context,
                        "reconcile",
                        status="ok" if changed else "no_op",
                        mutation=changed,
                        data={"action": action, "scope": scope, "target": str(target)},
                    )
        if outcome is None:
            raise AppError("io_error", "Reconcile ended without a deletion receipt.")
        return outcome, exit_code
    raise AppError(
        "invalid_input",
        "reconcile supports only remove_abandoned_lock, remove_released_lock, remove_partial_create, or remove_orphan_temp.",
    )


def positive_integer(value: str) -> int:
    try:
        parsed = int(value, 10)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a positive integer") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def add_stale_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--expect-revision", required=True, type=positive_integer)
    parser.add_argument("--expect-sha256", required=True)


def build_parser() -> JsonArgumentParser:
    parser = JsonArgumentParser(
        description="Create and safely track canonical implementation plans.",
    )
    parser.add_argument(
        "--project-root",
        required=True,
        help="Absolute target-project root.",
    )
    parser.add_argument(
        "--plans-root",
        default="Implementation_Plans",
        help="Catalog root beneath the project root (default: Implementation_Plans).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create", help="Create one new draft plan.")
    create.add_argument("--input", required=True, help="JSON file or - for standard input.")

    show = subparsers.add_parser("show", help="Show one exactly selected plan.")
    show.add_argument("selector")

    list_parser = subparsers.add_parser("list", help="List managed plans.")
    list_parser.add_argument(
        "--status",
        dest="status_filter",
        choices=sorted(PLAN_STATES),
        default=None,
    )

    update = subparsers.add_parser("update", help="Revise one plan baseline.")
    update.add_argument("selector")
    add_stale_arguments(update)
    update.add_argument("--input", required=True, help="JSON file or - for standard input.")

    update_phase = subparsers.add_parser("update-phase", help="Revise one phase.")
    update_phase.add_argument("selector")
    update_phase.add_argument("phase_id")
    add_stale_arguments(update_phase)
    update_phase.add_argument("--input", required=True, help="JSON file or - for standard input.")

    update_task = subparsers.add_parser("update-task", help="Revise or transition one task.")
    update_task.add_argument("selector")
    update_task.add_argument("task_id")
    add_stale_arguments(update_task)
    update_task.add_argument("--input", required=True, help="JSON file or - for standard input.")

    evidence = subparsers.add_parser("record-evidence", help="Append task or requirement evidence.")
    evidence.add_argument("selector")
    evidence.add_argument("target_id")
    add_stale_arguments(evidence)
    evidence.add_argument("--input", required=True, help="JSON file or - for standard input.")

    set_status = subparsers.add_parser("set-status", help="Apply a gated plan transition.")
    set_status.add_argument("selector")
    add_stale_arguments(set_status)
    set_status.add_argument("--status", dest="status_value", choices=sorted(PLAN_STATES), required=True)
    set_status.add_argument("--reason", required=True)
    set_status.add_argument("--confirmed", action="store_true", required=True)

    validate = subparsers.add_parser("validate", help="Validate one plan or the managed catalog.")
    validate.add_argument("selector", nargs="?")

    rebuild = subparsers.add_parser(
        "rebuild-projections", help="Rebuild one plan's generated Markdown only."
    )
    rebuild.add_argument("selector")

    subparsers.add_parser("reindex", help="Rebuild the generated catalog index only.")

    reconcile = subparsers.add_parser("reconcile", help="Apply one reviewed bounded recovery.")
    reconcile.add_argument("selector")
    reconcile.add_argument("--input", required=True, help="JSON file or - for standard input.")
    reconcile.add_argument("--confirmed", action="store_true", required=True)
    return parser


HANDLERS = {
    "create": handle_create,
    "show": handle_show,
    "list": handle_list,
    "update": handle_update,
    "update-phase": handle_update_phase,
    "update-task": handle_update_task,
    "record-evidence": handle_record_evidence,
    "set-status": handle_set_status,
    "validate": handle_validate,
    "rebuild-projections": handle_rebuild_projections,
    "reindex": handle_reindex,
    "reconcile": handle_reconcile,
}


def _error_targets(details: Mapping[str, Any]) -> list[str]:
    targets: list[str] = []
    direct = details.get("targets")
    if isinstance(direct, list):
        targets.extend(str(item) for item in direct if isinstance(item, (str, int)))
    findings = details.get("findings")
    if isinstance(findings, list):
        for finding in findings:
            if isinstance(finding, dict) and isinstance(finding.get("targets"), list):
                targets.extend(str(item) for item in finding["targets"])
    candidates = details.get("candidates")
    if isinstance(candidates, list):
        for candidate in candidates:
            if isinstance(candidate, dict):
                for key in ("plan_id", "directory"):
                    if isinstance(candidate.get(key), str):
                        targets.append(candidate[key])
    return list(dict.fromkeys(targets))


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(argv if argv is not None else sys.argv[1:])
    command = next((item for item in arguments if item in HANDLERS), "unknown")
    context: Context | None = None
    try:
        args = build_parser().parse_args(arguments)
        command = args.command
        context = resolve_context(args.project_root, args.plans_root)
        envelope, exit_code = HANDLERS[command](context, args)
    except AppError as exc:
        committed_outcome = exc.details.get("committed_outcome")
        if isinstance(committed_outcome, Mapping):
            envelope = copy.deepcopy(dict(committed_outcome))
            prior_recovery = envelope.get("recovery_required")
            substantive_mutation = committed_outcome.get("mutation") is True
            envelope["status"] = "partial" if substantive_mutation else "error"
            envelope["mutation"] = substantive_mutation
            envelope.setdefault("errors", []).append(
                _result_warning(
                    "io_error",
                    (
                        "The substantive operation committed, but owned lock cleanup did not finish durably."
                        if substantive_mutation
                        else "The requested operation was a no-op, but owned lock cleanup did not finish durably."
                    ),
                    str(exc.details.get("lock_path", "")),
                )
            )
            lock_path_text = str(exc.details.get("lock_path", ""))
            scope = "catalog" if lock_path_text.endswith(
                ".to-implementation-plan.catalog.lock"
            ) else "plan"
            selector = (
                str(envelope.get("plan", {}).get("plan_id"))
                if scope == "plan" and isinstance(envelope.get("plan"), Mapping)
                else "catalog"
            )
            recovery_input = (
                {
                    "action": "remove_released_lock",
                    "scope": scope,
                    "relative_name": exc.details.get("released_lock_name"),
                    "token": exc.details.get("token"),
                }
                if exc.details.get("release_renamed") is True
                else {
                    "action": "remove_abandoned_lock",
                    "scope": scope,
                    "token": exc.details.get("token"),
                }
            )
            lock_recovery: dict[str, Any] = {
                "command": "reconcile",
                "selector": selector,
                "input": recovery_input,
            }
            if isinstance(prior_recovery, Mapping):
                lock_recovery["then"] = append_recovery_tail(
                    prior_recovery,
                    {"command": "validate", "selector": selector},
                )
            else:
                lock_recovery["then"] = "validate"
            envelope["recovery_required"] = lock_recovery
            exit_code = EXIT_CODES["io_error"]
            sys.stdout.write(
                json.dumps(
                    envelope,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                    allow_nan=False,
                )
                + "\n"
            )
            return exit_code
        if exc.details.get("filesystem_mutation") is True:
            envelope = make_envelope(
                context,
                command,
                status="partial",
                mutation=True,
                errors=[
                    _result_warning(
                        exc.category,
                        exc.message,
                        *_error_targets(exc.details),
                    )
                ],
                recovery_required=(
                    exc.details.get("recovery_required")
                    if isinstance(exc.details.get("recovery_required"), Mapping)
                    else None
                ),
                data={"details": exc.details},
            )
            sys.stdout.write(
                json.dumps(
                    envelope,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                    allow_nan=False,
                )
                + "\n"
            )
            return exc.exit_code
        error = _result_warning(exc.category, exc.message, *_error_targets(exc.details))
        envelope = make_envelope(
            context,
            command,
            status="error",
            mutation=False,
            errors=[error],
            recovery_required=(
                exc.details.get("recovery_required")
                if isinstance(exc.details.get("recovery_required"), Mapping)
                else None
            ),
            data={"details": exc.details} if exc.details else None,
        )
        exit_code = exc.exit_code
    except KeyboardInterrupt:
        envelope = make_envelope(
            context,
            command,
            status="error",
            mutation=False,
            errors=[
                _result_warning(
                    "io_error",
                    "The operation was interrupted; inspect helper-owned locks and temporary files before recovery.",
                )
            ],
        )
        exit_code = EXIT_CODES["io_error"]
    except Exception:
        # Unexpected details stay out of diagnostics because payloads may contain
        # sensitive source content.  Tests can call functions directly for a
        # traceback when developing this package.
        envelope = make_envelope(
            context,
            command,
            status="error",
            mutation=False,
            errors=[
                _result_warning(
                    "io_error",
                    "An unexpected internal failure stopped the operation before a complete receipt.",
                )
            ],
        )
        exit_code = EXIT_CODES["io_error"]
    sys.stdout.write(
        json.dumps(
            envelope,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    )
    return exit_code



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
    return AppError("invalid_input", message, details={"code": code, **details})

ONTOLOGY_GUARDED_ACTIONS = ['handle_create', 'mutate_existing_plan', 'handle_rebuild_projections', 'handle_reindex', 'handle_reconcile', 'handle_update', 'handle_update_phase', 'handle_update_task', 'handle_record_evidence', 'handle_set_status']
handle_create = _ontology_guard_adapter(handle_create, 'plan', 'context', ['Implementation_Plans'])
mutate_existing_plan = _ontology_guard_adapter(mutate_existing_plan, 'plan', 'context', ['Implementation_Plans'])
handle_rebuild_projections = _ontology_guard_adapter(handle_rebuild_projections, 'plan', 'context', ['Implementation_Plans'])
handle_reindex = _ontology_guard_adapter(handle_reindex, 'plan', 'context', ['Implementation_Plans'])
handle_reconcile = _ontology_guard_adapter(handle_reconcile, 'plan', 'context', ['Implementation_Plans'])

handle_update = _ontology_guard_adapter(handle_update, "plan", "context", ["Implementation_Plans"])
handle_update_phase = _ontology_guard_adapter(handle_update_phase, "plan", "context", ["Implementation_Plans"])
handle_update_task = _ontology_guard_adapter(handle_update_task, "plan", "context", ["Implementation_Plans"])
handle_record_evidence = _ontology_guard_adapter(handle_record_evidence, "plan", "context", ["Implementation_Plans"])
handle_set_status = _ontology_guard_adapter(handle_set_status, "plan", "context", ["Implementation_Plans"])

if __name__ == "__main__":
    raise SystemExit(main())
