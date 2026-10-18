"""Immutable, explicitly supplied source snapshots for construction-0.1.

This module does not parse OntoKin, resolve imports, or search for packages.
Every well-formed supplied snapshot has a program revision, including snapshots
whose source text or import graph will subsequently be rejected. Source hashes
always retain their original meaning: SHA-256 of one exact UTF-8 file.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
from typing import Any, Callable

from .diagnostics import Source


BUNDLE_SCHEMA = "ontokin.bundle/0.1"
FILES_SCHEMA = "ontokin.files/0.1"
PROGRAM_DOMAIN = b"ontokin.bundle/0.1\0"
MAX_SOURCE_BYTES = 2_000_000
MAX_MODULES = 16
MAX_MANIFEST_BYTES = 4 * 1024 * 1024
MAX_FILENAME_BYTES = 1024
MAX_PATH_BYTES = 4096
MAX_VERSION_COMPONENT = 2_147_483_647
PACKAGE_RE = re.compile(r"[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*\Z", re.ASCII)
VERSION_RE = re.compile(r"(0|[1-9][0-9]{0,9})\.(0|[1-9][0-9]{0,9})\.(0|[1-9][0-9]{0,9})\Z", re.ASCII)
DIGEST_RE = re.compile(r"sha256:[0-9a-f]{64}\Z", re.ASCII)


class BundleError(ValueError):
    """Transport failure with no invented OntoKin source diagnostic."""

    def __init__(self, code: str, message: str, **details: Any):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details

    def to_dict(self) -> dict:
        return {"code": self.code, "message": self.message, "details": self.details}


def _bad(message: str, **details: Any) -> None:
    raise BundleError("OKA-E-REQUEST", message, **details)


def _limit(message: str, **details: Any) -> None:
    raise BundleError("OKA-E-RESOURCE", message, **details)


def _text(value: Any, name: str, *, limit: int, empty: bool = False,
          controls: bool = True) -> bytes:
    if not isinstance(value, str) or (not empty and not value):
        _bad(f"{name} must be a {'possibly empty' if empty else 'nonempty'} UTF-8 string.")
    # The character count is a cheap lower bound on its UTF-8 byte count.
    if len(value) > limit:
        _limit(f"{name} exceeds its byte limit.", limit=limit)
    try:
        raw = value.encode("utf-8")
    except UnicodeError as exc:
        raise BundleError("OKA-E-REQUEST", f"{name} must contain valid Unicode scalar values.") from exc
    if len(raw) > limit:
        _limit(f"{name} exceeds its byte limit.", limit=limit)
    if not controls and any(ord(c) < 32 or 127 <= ord(c) <= 159 for c in value):
        _bad(f"{name} cannot contain control characters.")
    return raw


def validate_package_id(value: Any) -> str:
    _text(value, "package_id", limit=128)
    if PACKAGE_RE.fullmatch(value) is None:
        _bad("package_id must use the construction-0.1 lowercase package identifier grammar.")
    return value


def validate_version(value: Any) -> str:
    _text(value, "version", limit=32)
    match = VERSION_RE.fullmatch(value)
    if match is None or any(int(part) > MAX_VERSION_COMPONENT for part in match.groups()):
        _bad("version must be exact major.minor.patch with components from 0 through 2147483647.")
    return value


def package_source_id(package_id: str, version: str) -> str:
    return "package:" + validate_package_id(package_id) + "@" + validate_version(version)


@dataclass(frozen=True)
class SourceUnit:
    """One immutable file, with a canonical source ID separate from its bytes."""

    source_id: str
    filename: str
    raw: bytes
    package_id: str | None = None
    version: str | None = None
    revision: str = field(init=False)
    _text: str = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        _text(self.filename, "filename", limit=MAX_FILENAME_BYTES, controls=False)
        if not isinstance(self.raw, bytes):
            _bad("SourceUnit.raw must be exact UTF-8 bytes.")
        if len(self.raw) > MAX_SOURCE_BYTES:
            _limit("A source unit exceeds the aggregate source-byte limit.", limit=MAX_SOURCE_BYTES)
        try:
            decoded = self.raw.decode("utf-8")
        except UnicodeError as exc:
            raise BundleError("OKA-E-REQUEST", "A source unit must contain valid UTF-8 bytes.") from exc
        if self.package_id is None and self.version is None:
            expected = "entry"
        elif self.package_id is not None and self.version is not None:
            expected = package_source_id(self.package_id, self.version)
        else:
            _bad("A dependency source unit requires both package_id and version.")
        if self.source_id != expected:
            _bad("SourceUnit.source_id does not match its declared role and package pin.", expected=expected)
        object.__setattr__(self, "_text", decoded)
        object.__setattr__(self, "revision", "sha256:" + hashlib.sha256(self.raw).hexdigest())

    @property
    def text(self) -> str:
        return self._text

    def to_source(self) -> Source:
        """Return a detached legacy Source; mutating it cannot mutate this unit."""
        return Source(self._text, self.filename, self.raw)


@dataclass(frozen=True)
class ProgramBundle:
    """Entry plus all supplied units, sealed before source validity is known.

    ``to_payload()`` and ``load_bundle()`` round-trip exact source bytes. The
    round trip preserves source IDs, filenames, hashes and program revision;
    reordering JSON object members or the supplied module array is immaterial.
    No Source object exposed by a convenience accessor is shared mutable state.
    """

    entry: SourceUnit
    modules: tuple[SourceUnit, ...] = ()
    program_revision: str = field(init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.entry, SourceUnit) or self.entry.source_id != "entry":
            _bad("ProgramBundle.entry must be the entry SourceUnit.")
        if not isinstance(self.modules, (tuple, list)):
            _bad("ProgramBundle.modules must be a finite sequence of SourceUnit values.")
        if len(self.modules) > MAX_MODULES:
            _limit("The bundle exceeds the dependency-module limit.", limit=MAX_MODULES)
        if any(not isinstance(unit, SourceUnit) or unit.package_id is None for unit in self.modules):
            _bad("ProgramBundle.modules must contain dependency SourceUnit values.")
        modules = tuple(sorted(self.modules, key=lambda unit: unit.source_id))
        ids = [unit.source_id for unit in modules]
        if len(set(ids)) != len(ids):
            _bad("Two supplied source units cannot have the same canonical source_id.")
        size = len(self.entry.raw) + sum(len(unit.raw) for unit in modules)
        if size > MAX_SOURCE_BYTES:
            _limit("The supplied sources exceed the aggregate UTF-8 byte limit.",
                   limit=MAX_SOURCE_BYTES, consumed=size)
        object.__setattr__(self, "modules", modules)
        canonical = json.dumps(self.manifest(), sort_keys=True, ensure_ascii=False,
                               separators=(",", ":"), allow_nan=False).encode("utf-8")
        object.__setattr__(self, "program_revision",
                           "sha256:" + hashlib.sha256(PROGRAM_DOMAIN + canonical).hexdigest())

    @property
    def units(self) -> tuple[SourceUnit, ...]:
        return (self.entry,) + self.modules

    @property
    def sources(self) -> dict[str, Source]:
        return {unit.source_id: unit.to_source() for unit in self.units}

    @property
    def source_registry(self) -> dict[str, Source]:
        return self.sources

    def manifest(self) -> dict:
        return {
            "schema_version": BUNDLE_SCHEMA,
            "entry_source_id": "entry",
            "units": [{"source_id": unit.source_id, "package_id": unit.package_id,
                       "version": unit.version, "filename": unit.filename,
                       "source_revision": unit.revision}
                      for unit in sorted(self.units, key=lambda unit: unit.source_id)],
        }

    def to_payload(self) -> dict:
        return {
            "schema_version": BUNDLE_SCHEMA,
            "entry": {"filename": self.entry.filename, "source": self.entry.text},
            "modules": [{"package_id": unit.package_id, "version": unit.version,
                         "filename": unit.filename, "source": unit.text}
                        for unit in self.modules],
        }


def _object(value: Any, required: set[str], name: str) -> None:
    if not isinstance(value, dict) or set(value) != required:
        _bad(f"{name} has missing or unknown fields.", required=sorted(required))


def _descriptors(payload: Any, *, files: bool) -> tuple[dict, list[dict]]:
    _object(payload, {"schema_version", "entry", "modules"}, "bundle" if not files else "file manifest")
    if payload["schema_version"] != (FILES_SCHEMA if files else BUNDLE_SCHEMA):
        _bad("Unknown source bundle or file manifest schema version.")
    modules = payload["modules"]
    if not isinstance(modules, list):
        _bad("modules must be an array.")
    if len(modules) > MAX_MODULES:
        _limit("The bundle exceeds the dependency-module limit.", limit=MAX_MODULES)
    content = "path" if files else "source"
    _object(payload["entry"], {"filename", content}, "entry")
    for unit in modules:
        _object(unit, {"package_id", "version", "filename", content}, "module")
        validate_package_id(unit["package_id"])
        validate_version(unit["version"])
    ids = [package_source_id(unit["package_id"], unit["version"]) for unit in modules]
    if len(set(ids)) != len(ids):
        _bad("Two supplied source units cannot have the same canonical source_id.")
    for unit in [payload["entry"], *modules]:
        _text(unit["filename"], "filename", limit=MAX_FILENAME_BYTES, controls=False)
        if files:
            _relative_path(unit["path"])
        else:
            _text(unit["source"], "source", limit=MAX_SOURCE_BYTES, empty=True)
    return payload["entry"], modules


def load_bundle(payload: Any) -> ProgramBundle:
    """Seal a strict inline payload without parsing or resolving its content."""
    entry, modules = _descriptors(payload, files=False)
    total = sum(len(unit["source"].encode("utf-8")) for unit in [entry, *modules])
    if total > MAX_SOURCE_BYTES:
        _limit("The supplied sources exceed the aggregate UTF-8 byte limit.",
               limit=MAX_SOURCE_BYTES, consumed=total)
    first = SourceUnit("entry", entry["filename"], entry["source"].encode("utf-8"))
    others = tuple(SourceUnit(package_source_id(unit["package_id"], unit["version"]),
                              unit["filename"], unit["source"].encode("utf-8"),
                              unit["package_id"], unit["version"])
                   for unit in modules)
    return ProgramBundle(first, others)


def _relative_path(value: Any) -> PurePosixPath:
    _text(value, "path", limit=MAX_PATH_BYTES, controls=False)
    parts = value.split("/")
    if value.startswith("/") or "\\" in value or any(part in ("", ".", "..") for part in parts):
        _bad("A file path must be relative POSIX with no empty, dot, parent or backslash segments.")
    return PurePosixPath(*parts)


def _read_bounded(path: Path, limit: int, description: str) -> bytes:
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NONBLOCK", 0))
        with os.fdopen(descriptor, "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                _bad(f"{description} must name a regular file.")
            raw = stream.read(limit + 1)
    except OSError as exc:
        raise BundleError("OKA-E-REQUEST", f"Cannot read {description}.", reason=str(exc)) from exc
    if len(raw) > limit:
        _limit(f"{description} exceeds the remaining byte budget.", limit=limit)
    return raw


def _pairs(pairs: list[tuple[str, Any]]) -> dict:
    result = {}
    for name, value in pairs:
        if name in result:
            _bad("A source file manifest cannot contain duplicate JSON object keys.", key=name)
        result[name] = value
    return result


def _constant(value: str) -> None:
    _bad("A source file manifest cannot contain non-finite JSON values.", value=value)


def load_file_manifest(path: str | Path, *, check: Callable[[], None] | None = None) -> ProgramBundle:
    """Read only explicitly listed files, then seal the same inline snapshot.

    Every descriptor and resolved path is checked before any source file is
    opened. Transport paths never enter program identity. The resolved manifest
    directory is the boundary for declared relative paths and symlink targets.
    """
    if not isinstance(path, (str, Path)):
        _bad("The source manifest path must be a string or Path.")
    try:
        manifest_path = Path(path).resolve(strict=True)
    except (OSError, RuntimeError, ValueError) as exc:
        raise BundleError("OKA-E-REQUEST", "Cannot resolve the source file manifest.", reason=str(exc)) from exc
    raw = _read_bounded(manifest_path, MAX_MANIFEST_BYTES, "the source file manifest")
    try:
        payload = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs,
                             parse_constant=_constant)
    except RecursionError as exc:
        raise BundleError("OKA-E-RESOURCE", "The source file manifest exceeds the JSON nesting budget.") from exc
    except (ValueError, UnicodeError) as exc:
        if isinstance(exc, BundleError):
            raise
        raise BundleError("OKA-E-REQUEST", "The source file manifest must be UTF-8 JSON.", reason=str(exc)) from exc
    entry, modules = _descriptors(payload, files=True)
    base = manifest_path.parent
    resolved: list[Path] = []
    for descriptor in [entry, *modules]:
        if check is not None:
            check()
        relative = _relative_path(descriptor["path"])
        try:
            candidate = base.joinpath(*relative.parts).resolve(strict=True)
            candidate.relative_to(base)
            if not candidate.is_file():
                _bad("A declared source path must name a regular file.", path=descriptor["path"])
        except (OSError, RuntimeError, ValueError) as exc:
            if isinstance(exc, BundleError):
                raise
            raise BundleError("OKA-E-REQUEST", "A declared source path must resolve inside the manifest directory.",
                              path=descriptor["path"]) from exc
        resolved.append(candidate)
    loaded: list[dict] = []
    remaining = MAX_SOURCE_BYTES
    for descriptor, candidate in zip([entry, *modules], resolved):
        if check is not None:
            check()
        raw_source = _read_bounded(candidate, remaining, "a declared source file")
        remaining -= len(raw_source)
        try:
            source = raw_source.decode("utf-8")
        except UnicodeError as exc:
            raise BundleError("OKA-E-REQUEST", "A declared source file must contain valid UTF-8.",
                              path=descriptor["path"]) from exc
        loaded.append({**{key: value for key, value in descriptor.items() if key != "path"}, "source": source})
    return load_bundle({"schema_version": BUNDLE_SCHEMA, "entry": loaded[0], "modules": loaded[1:]})
