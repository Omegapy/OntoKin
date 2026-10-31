"""Immutable bundle/0.2 source snapshots and explicitly pinned PNG bytes.

Sealing performs transport checks only.  PNG interpretation belongs to the
admitted compiler, so constructing or reopening a snapshot grants no authority.
Legacy bundle/0.1 loaders and identity rules remain untouched.
"""

from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
from typing import Any, Callable

from .bundle import (
    BUNDLE_SCHEMA as SOURCE_BUNDLE_SCHEMA, FILES_SCHEMA as SOURCE_FILES_SCHEMA,
    DIGEST_RE, MAX_MANIFEST_BYTES, MAX_SOURCE_BYTES, BundleError, ProgramBundle,
    SourceUnit, _bad, _constant, _descriptors, _limit, _object, _pairs,
    _relative_path, load_bundle, package_source_id,
)


BUNDLE_SCHEMA = "ontokin.bundle/0.2"
FILES_SCHEMA = "ontokin.files/0.2"
PROGRAM_DOMAIN = b"ontokin.bundle/0.2\0"
MAX_ASSETS = 4
MAX_ASSET_BYTES = 300_000
MAX_TOTAL_ASSET_BYTES = 1_200_000
MAX_BASE64_CHARS = ((MAX_ASSET_BYTES + 2) // 3) * 4
ASSET_ID_RE = re.compile(r"[a-z][a-z0-9._-]{0,63}\Z", re.ASCII)


def validate_asset_id(value: Any) -> str:
    if not isinstance(value, str) or len(value) > 64 or ASSET_ID_RE.fullmatch(value) is None:
        _bad("asset_id must match [a-z][a-z0-9._-]{0,63}.")
    return value


def validate_asset_digest(value: Any) -> str:
    if not isinstance(value, str) or len(value) != 71 or DIGEST_RE.fullmatch(value) is None:
        _bad("Asset sha256 must be sha256: followed by 64 lowercase hexadecimal digits.")
    return value


@dataclass(frozen=True)
class AssetUnit:
    """One immutable named byte string, independent of its source declarations."""

    asset_id: str
    raw: bytes
    media_type: str = "image/png"
    sha256: str = field(init=False)

    def __post_init__(self) -> None:
        validate_asset_id(self.asset_id)
        if self.media_type != "image/png":
            _bad("Asset media_type must be image/png.")
        if not isinstance(self.raw, bytes):
            _bad("AssetUnit.raw must be immutable bytes.")
        if len(self.raw) > MAX_ASSET_BYTES:
            _limit("An image exceeds the encoded PNG byte bound.", limit=MAX_ASSET_BYTES,
                   consumed=len(self.raw))
        object.__setattr__(self, "sha256", "sha256:" + hashlib.sha256(self.raw).hexdigest())

    @property
    def revision(self) -> str:
        return self.sha256

    def manifest(self) -> dict:
        return {"asset_id": self.asset_id, "media_type": self.media_type,
                "sha256": self.sha256, "byte_length": len(self.raw)}

    def to_descriptor(self) -> dict:
        return {"asset_id": self.asset_id, "media_type": self.media_type,
                "sha256": self.sha256,
                "data_base64": base64.b64encode(self.raw).decode("ascii")}


@dataclass(frozen=True)
class TextureBundle(ProgramBundle):
    assets: tuple[AssetUnit, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.assets, (tuple, list)):
            _bad("TextureBundle.assets must be a finite sequence of AssetUnit values.")
        if len(self.assets) > MAX_ASSETS:
            _limit("The bundle exceeds the asset count bound.", limit=MAX_ASSETS)
        if any(not isinstance(asset, AssetUnit) for asset in self.assets):
            _bad("TextureBundle.assets must contain AssetUnit values.")
        assets = tuple(sorted(self.assets, key=lambda asset: asset.asset_id))
        if len({asset.asset_id for asset in assets}) != len(assets):
            _bad("Two supplied images cannot have the same asset_id.")
        size = sum(len(asset.raw) for asset in assets)
        if size > MAX_TOTAL_ASSET_BYTES:
            _limit("The bundle exceeds the aggregate encoded PNG byte bound.",
                   limit=MAX_TOTAL_ASSET_BYTES, consumed=size)
        object.__setattr__(self, "assets", assets)
        super().__post_init__()
        canonical = json.dumps(self.manifest(), sort_keys=True, ensure_ascii=False,
                               separators=(",", ":"), allow_nan=False).encode("utf-8")
        object.__setattr__(self, "program_revision",
                           "sha256:" + hashlib.sha256(PROGRAM_DOMAIN + canonical).hexdigest())

    @property
    def asset_map(self) -> dict[str, AssetUnit]:
        return {asset.asset_id: asset for asset in self.assets}

    def manifest(self) -> dict:
        result = super().manifest()
        result["schema_version"] = BUNDLE_SCHEMA
        result["assets"] = [asset.manifest() for asset in self.assets]
        return result

    def to_payload(self) -> dict:
        result = super().to_payload()
        result["schema_version"] = BUNDLE_SCHEMA
        result["assets"] = [asset.to_descriptor() for asset in self.assets]
        return result


def _asset_descriptors(payload: Any, *, files: bool) -> tuple[dict, list[dict], list[dict]]:
    _object(payload, {"schema_version", "entry", "modules", "assets"},
            "texture file manifest" if files else "texture bundle")
    if payload["schema_version"] != (FILES_SCHEMA if files else BUNDLE_SCHEMA):
        _bad("Unknown texture bundle or file manifest schema version.")
    # Reuse exactly the older source-only descriptor rules without admitting
    # assets to the old public loader or changing any source-unit identity.
    entry, modules = _descriptors({
        "schema_version": SOURCE_FILES_SCHEMA if files else SOURCE_BUNDLE_SCHEMA,
        "entry": payload["entry"], "modules": payload["modules"],
    }, files=files)
    assets = payload["assets"]
    if not isinstance(assets, list):
        _bad("assets must be an array.")
    if len(assets) > MAX_ASSETS:
        _limit("The bundle exceeds the asset count bound.", limit=MAX_ASSETS)
    seen: set[str] = set()
    content = "path" if files else "data_base64"
    for asset in assets:
        _object(asset, {"asset_id", "sha256", "media_type", content}, "asset")
        ident = validate_asset_id(asset["asset_id"])
        if ident in seen:
            _bad("Two supplied images cannot have the same asset_id.", asset_id=ident)
        seen.add(ident)
        validate_asset_digest(asset["sha256"])
        if asset["media_type"] != "image/png":
            _bad("Asset media_type must be image/png.")
        if files:
            _texture_path(asset["path"])
        else:
            encoded = asset["data_base64"]
            if not isinstance(encoded, str):
                _bad("Asset data_base64 must be a canonical base64 string.")
            if len(encoded) > MAX_BASE64_CHARS:
                _limit("Asset base64 exceeds the encoded PNG byte bound.", limit=MAX_BASE64_CHARS)
    if files:
        for source in [entry, *modules]:
            _texture_path(source["path"])
    return entry, modules, assets


def load_texture_bundle(payload: Any, *, check: Callable[[], None] | None = None) -> TextureBundle:
    """Seal strict inline transfer fields without interpreting PNG bytes."""
    if check is not None:
        check()
    entry, modules, descriptors = _asset_descriptors(payload, files=False)
    source = load_bundle({"schema_version": SOURCE_BUNDLE_SCHEMA,
                          "entry": entry, "modules": modules})
    assets = []
    total = 0
    for descriptor in descriptors:
        if check is not None:
            check()
        encoded = descriptor["data_base64"]
        try:
            raw = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError, UnicodeError) as exc:
            raise BundleError("OKA-E-REQUEST", "Asset data_base64 is not canonical padded base64.") from exc
        if base64.b64encode(raw).decode("ascii") != encoded:
            _bad("Asset data_base64 is not canonical padded base64.")
        asset = AssetUnit(descriptor["asset_id"], raw, descriptor["media_type"])
        if asset.sha256 != descriptor["sha256"]:
            _bad("Asset sha256 does not match its exact supplied bytes.", asset_id=asset.asset_id)
        total += len(raw)
        if total > MAX_TOTAL_ASSET_BYTES:
            _limit("The bundle exceeds the aggregate encoded PNG byte bound.",
                   limit=MAX_TOTAL_ASSET_BYTES, consumed=total)
        assets.append(asset)
    if check is not None:
        check()
    return TextureBundle(source.entry, source.modules, tuple(assets))


def _texture_path(value: Any) -> PurePosixPath:
    result = _relative_path(value)
    if ":" in value:
        _bad("A texture manifest path cannot be a URL or drive-qualified path.")
    return result


def _stamp(info: os.stat_result) -> tuple[int, int, int, int, int]:
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns


def _read_regular_at(parent: int, name: str, limit: int, description: str,
                     check: Callable[[], None] | None) -> bytes:
    """Read through a held directory descriptor and reject replacement/mutation."""
    descriptor = None
    try:
        flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0)
        before_path = os.stat(name, dir_fd=parent, follow_symlinks=False)
        if not stat.S_ISREG(before_path.st_mode):
            _bad(f"{description} must name an ordinary file without symlinks.")
        descriptor = os.open(name, flags, dir_fd=parent)
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or _stamp(before) != _stamp(before_path):
            _bad(f"{description} changed before its bounded read.")
        if before.st_size > limit:
            _limit(f"{description} exceeds its remaining byte bound.", limit=limit,
                   consumed=before.st_size)
        parts: list[bytes] = []
        size = 0
        while True:
            if check is not None:
                check()
            chunk = os.read(descriptor, min(65_536, limit + 1 - size))
            if not chunk:
                break
            parts.append(chunk)
            size += len(chunk)
            if size > limit:
                _limit(f"{description} exceeds its remaining byte bound.", limit=limit)
        after = os.fstat(descriptor)
        after_path = os.stat(name, dir_fd=parent, follow_symlinks=False)
        if (not stat.S_ISREG(after_path.st_mode) or _stamp(before) != _stamp(after)
                or _stamp(before) != _stamp(after_path) or size != before.st_size):
            _bad(f"{description} changed during its bounded read.")
        return b"".join(parts)
    except OSError as exc:
        raise BundleError("OKA-E-REQUEST", f"Cannot read {description} without symlinks.",
                          reason=str(exc)) from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _open_directory(parent: int, name: str) -> int:
    before = os.stat(name, dir_fd=parent, follow_symlinks=False)
    if not stat.S_ISDIR(before.st_mode):
        _bad("A texture manifest path must traverse ordinary directories without symlinks.")
    descriptor = os.open(name, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
                         | getattr(os, "O_NOFOLLOW", 0), dir_fd=parent)
    actual = os.fstat(descriptor)
    if (not stat.S_ISDIR(actual.st_mode)
            or (actual.st_dev, actual.st_ino) != (before.st_dev, before.st_ino)):
        os.close(descriptor)
        _bad("A texture manifest directory changed during path resolution.")
    return descriptor


def _read_relative(root: int, relative: PurePosixPath, limit: int, description: str,
                   check: Callable[[], None] | None) -> bytes:
    parent = os.dup(root)
    try:
        for segment in relative.parts[:-1]:
            if check is not None:
                check()
            child = _open_directory(parent, segment)
            os.close(parent)
            parent = child
        return _read_regular_at(parent, relative.parts[-1], limit, description, check)
    except OSError as exc:
        raise BundleError("OKA-E-REQUEST", "Cannot resolve a declared file inside the manifest root.",
                          path=str(relative), reason=str(exc)) from exc
    finally:
        os.close(parent)


def load_texture_file_manifest_transport(path: str | Path, *,
        check: Callable[[], None] | None = None) -> tuple[TextureBundle, bytes, tuple[str, ...]]:
    """Seal one secure file read and return detached CLI transport information.

    Relative traversal uses directory file descriptors with no-follow opens;
    symlink replacement cannot escape the root between path checking and reads.
    The returned original manifest bytes and relative source/image paths let a
    CLI protect its inputs without another ordinary or unbounded file read.
    Neither transport bytes nor paths become source/asset identity fields.
    """
    if not isinstance(path, (str, Path)):
        _bad("The texture manifest path must be a string or Path.")
    root = None
    try:
        absolute = Path(os.path.abspath(path))
        root = os.open(absolute.anchor, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        for segment in absolute.parts[1:-1]:
            if check is not None:
                check()
            child = _open_directory(root, segment)
            os.close(root)
            root = child
        manifest_stamp = _stamp(os.stat(absolute.name, dir_fd=root, follow_symlinks=False))
        raw_manifest = _read_regular_at(root, absolute.name, MAX_MANIFEST_BYTES,
                                       "the texture file manifest", check)
        try:
            payload = json.loads(raw_manifest.decode("utf-8"), object_pairs_hook=_pairs,
                                 parse_constant=_constant)
        except RecursionError as exc:
            raise BundleError("OKA-E-RESOURCE", "The texture manifest exceeds the JSON nesting bound.") from exc
        except (ValueError, UnicodeError) as exc:
            if isinstance(exc, BundleError):
                raise
            raise BundleError("OKA-E-REQUEST", "The texture manifest must contain UTF-8 JSON.") from exc
        entry, modules, descriptors = _asset_descriptors(payload, files=True)
        relative_paths = tuple(descriptor["path"] for descriptor in [entry, *modules, *descriptors])
        sources = []
        remaining = MAX_SOURCE_BYTES
        for index, descriptor in enumerate([entry, *modules]):
            raw = _read_relative(root, _texture_path(descriptor["path"]), remaining,
                                 "a declared source file", check)
            remaining -= len(raw)
            if index == 0:
                source = SourceUnit("entry", descriptor["filename"], raw)
            else:
                package, version = descriptor["package_id"], descriptor["version"]
                source = SourceUnit(package_source_id(package, version), descriptor["filename"],
                                    raw, package, version)
            sources.append(source)
        assets = []
        remaining = MAX_TOTAL_ASSET_BYTES
        for descriptor in descriptors:
            raw = _read_relative(root, _texture_path(descriptor["path"]),
                                 min(MAX_ASSET_BYTES, remaining), "a declared image file", check)
            remaining -= len(raw)
            asset = AssetUnit(descriptor["asset_id"], raw, descriptor["media_type"])
            if asset.sha256 != descriptor["sha256"]:
                _bad("Asset sha256 does not match its exact file bytes.", asset_id=asset.asset_id)
            assets.append(asset)
        if check is not None:
            check()
        final_manifest = os.stat(absolute.name, dir_fd=root, follow_symlinks=False)
        if not stat.S_ISREG(final_manifest.st_mode) or _stamp(final_manifest) != manifest_stamp:
            _bad("The texture file manifest changed while its source and image snapshot was loaded.")
        bundle = TextureBundle(sources[0], tuple(sources[1:]), tuple(assets))
        return bundle, raw_manifest, relative_paths
    except (OSError, ValueError) as exc:
        if isinstance(exc, BundleError):
            raise
        raise BundleError("OKA-E-REQUEST", "Cannot read the texture manifest and its explicit files.",
                          reason=str(exc)) from exc
    finally:
        if root is not None:
            os.close(root)


def load_texture_file_manifest(path: str | Path, *,
                               check: Callable[[], None] | None = None) -> TextureBundle:
    """Read only explicit stable ordinary files and return their sealed bundle."""
    return load_texture_file_manifest_transport(path, check=check)[0]
