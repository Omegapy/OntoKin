"""Offline Git/LFS identity for the bounded engineering-archive storage profile.

Ordinary files retain raw Git-blob equality. LFS is selected only by attributes
from the identified commit/index, and binds a canonical pointer to the actual
hydrated bytes. This module imports no product/runtime code and never transfers
objects or copies repository credentials/configuration.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import shutil
import subprocess
import tempfile


SCHEMA = "ontokin.storage-binding/0.1"
PROFILE = "engineering-archives/0.1"
LFS_VERSION = "https://git-lfs.github.com/spec/v1"
MAX_POINTER_BYTES = 1024
MAX_ATTRIBUTES_BYTES = 1024 * 1024
_POINTER = re.compile(rb"version https://git-lfs.github.com/spec/v1\noid sha256:([0-9a-f]{64})\nsize (0|[1-9][0-9]{0,18})\n\Z")
_ARCHIVE = re.compile(r".+(?:\.zip(?:\.part[0-9]{3})?|\.tar\.xz|\.tar\.gz)\Z")


class StorageIdentityError(ValueError):
    """A storage representation is missing, ambiguous, or inconsistent."""


def git_environment(root: Path) -> dict[str, str]:
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    environment.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
                       GIT_ATTR_NOSYSTEM="1", GIT_TERMINAL_PROMPT="0",
                       GIT_OPTIONAL_LOCKS="0", GIT_NO_REPLACE_OBJECTS="1",
                       GIT_NO_LAZY_FETCH="1", GIT_CEILING_DIRECTORIES=str(root.resolve().parent))
    return environment


def git(root: Path, *arguments: str, input: bytes | None = None) -> bytes:
    try:
        return subprocess.run(
            ["git", "-c", "core.fsmonitor=false", "-c", "core.hooksPath=" + os.devnull,
             "-c", "core.attributesFile=" + os.devnull, "-C", str(root), *arguments],
            input=input, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=git_environment(root), check=True, timeout=120).stdout
    except (OSError, subprocess.SubprocessError) as error:
        raise StorageIdentityError("Cannot read the identified local Git storage state: " + str(error)) from error


def _path(name: str) -> PurePosixPath:
    path = PurePosixPath(name)
    if not name or path.is_absolute() or ".." in path.parts or "\x00" in name or path.as_posix() != name:
        raise StorageIdentityError("Unsafe storage path: " + repr(name))
    return path


def archive_path(name: str) -> bool:
    """Positive scope: archive payloads, never parts.json or normative inputs."""
    path = _path(name)
    return path.parts[:2] == ("docs", "engineering") and bool(_ARCHIVE.fullmatch(path.name))


def blob_id(raw: bytes, algorithm: str = "sha1") -> str:
    return hashlib.new(algorithm, b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def pointer_bytes(oid: str, size: int) -> bytes:
    if not re.fullmatch(r"[0-9a-f]{64}", oid) or type(size) is not int or not 0 <= size <= 2**63 - 1:
        raise StorageIdentityError("Invalid LFS SHA-256 or size")
    return f"version {LFS_VERSION}\noid sha256:{oid}\nsize {size}\n".encode("ascii")


def parse_pointer(raw: bytes) -> dict:
    match = _POINTER.fullmatch(raw) if len(raw) <= MAX_POINTER_BYTES else None
    if match is None:
        raise StorageIdentityError("Expected a canonical three-field LFS v1/SHA-256/size pointer")
    oid, size = match[1].decode("ascii"), int(match[2])
    if pointer_bytes(oid, size) != raw:
        raise StorageIdentityError("Noncanonical LFS pointer")
    return {"version": LFS_VERSION, "oid": "sha256:" + oid, "size": size}


@dataclass(frozen=True)
class Entry:
    mode: str
    blob: str


class StorageContext:
    """Resolve storage from one exact Git commit or the current stage-zero index."""

    def __init__(self, root: Path, revision: str | None = "HEAD"):
        self.root = Path(root).resolve()
        if Path(git(self.root, "rev-parse", "--show-toplevel").decode().strip()).resolve() != self.root:
            raise StorageIdentityError("Storage identity requires a Git checkout at the supplied root")
        self.revision = (git(self.root, "rev-parse", "--verify", revision + "^{commit}").decode().strip()
                         if revision is not None else None)
        self.algorithm = git(self.root, "rev-parse", "--show-object-format").decode().strip()
        if self.algorithm not in {"sha1", "sha256"}:
            raise StorageIdentityError("Unsupported Git object format")
        self.entries: dict[str, Entry] = {}
        command = ("ls-files", "--stage", "-z") if revision is None else ("ls-tree", "-r", "-z", self.revision)
        for record in git(self.root, *command).split(b"\0"):
            if not record:
                continue
            metadata, encoded_name = record.split(b"\t", 1)
            first, second, third = metadata.decode("ascii").split()
            name = encoded_name.decode("utf-8")
            _path(name)
            if revision is None:
                mode, blob = first, second
                if third != "0":
                    raise StorageIdentityError("Unmerged storage input: " + name)
            else:
                mode, kind, blob = first, second, third
                if kind != "blob":
                    raise StorageIdentityError("Unsupported Git tree entry in storage inputs: " + name)
            self.entries[name] = Entry(mode, blob)
        self.attributes = self._attributes()
        self.lfs_paths = tuple(name for name in self.entries if self.attributes.get(name) == "lfs")
        for name in self.lfs_paths:
            if not archive_path(name) or self.entries[name].mode != "100644":
                raise StorageIdentityError("LFS is outside the bounded engineering archive profile: " + name)

    def _attributes(self) -> dict[str, str]:
        sources = [(name, entry) for name, entry in self.entries.items() if PurePosixPath(name).name == ".gitattributes"]
        if not sources:
            return {}
        total = 0
        with tempfile.TemporaryDirectory(prefix="ontokin-committed-attributes-") as temporary:
            root = Path(temporary)
            git(root, "init", "--quiet", "--template=")
            for name, entry in sources:
                if entry.mode != "100644":
                    raise StorageIdentityError("Attributes must be regular nonexecutable files: " + name)
                size = int(git(self.root, "cat-file", "-s", entry.blob))
                total += size
                if total > MAX_ATTRIBUTES_BYTES:
                    raise StorageIdentityError("Committed attribute files exceed the bounded metadata limit")
                raw = git(self.root, "cat-file", "blob", entry.blob)
                if len(raw) != size or blob_id(raw, self.algorithm) != entry.blob:
                    raise StorageIdentityError("Attribute blob identity differs: " + name)
                destination = root / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(raw)
            names = tuple(self.entries)
            raw = git(root, "check-attr", "-z", "--stdin", "filter",
                      input=b"\0".join(name.encode("utf-8") for name in names) + b"\0")
            fields = raw.split(b"\0")
            if fields[-1:] != [b""] or len(fields) != 3 * len(names) + 1:
                raise StorageIdentityError("Incomplete committed-attribute resolution")
            result = {}
            for index, name in enumerate(names):
                observed, attribute, value = fields[index * 3:index * 3 + 3]
                if observed.decode("utf-8") != name or attribute != b"filter":
                    raise StorageIdentityError("Unexpected committed-attribute response")
                result[name] = value.decode("utf-8")
            return result

    def _pointer(self, name: str) -> tuple[bytes, dict]:
        entry = self.entries[name]
        size = int(git(self.root, "cat-file", "-s", entry.blob))
        if size > MAX_POINTER_BYTES:
            raise StorageIdentityError("LFS-selected file is still an ordinary blob: " + name)
        raw = git(self.root, "cat-file", "blob", entry.blob)
        if len(raw) != size or blob_id(raw, self.algorithm) != entry.blob:
            raise StorageIdentityError("Committed pointer blob differs: " + name)
        return raw, parse_pointer(raw)

    def verify_file(self, name: str) -> dict:
        path = self.root / _path(name)
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(self.root):
            raise StorageIdentityError("Missing, nonregular or escaping storage input: " + name)
        entry = self.entries.get(name)
        size = path.stat().st_size
        digest = hashlib.sha256()
        blob = hashlib.new(self.algorithm, b"blob " + str(size).encode("ascii") + b"\0")
        prefix = b""
        observed_size = 0
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                if not prefix:
                    prefix = block[:MAX_POINTER_BYTES + 1]
                digest.update(block)
                blob.update(block)
                observed_size += len(block)
        if observed_size != size or path.stat().st_size != size:
            raise StorageIdentityError("Storage input changed during hashing: " + name)
        payload = {"sha256": "sha256:" + digest.hexdigest(), "bytes": size,
                   "raw_git_blob": blob.hexdigest()}
        if name not in self.lfs_paths:
            if entry is not None and blob.hexdigest() != entry.blob:
                raise StorageIdentityError("Ordinary tracked input differs from its Git blob: " + name)
            return {"kind": "git-blob" if entry else "untracked", "payload": payload,
                    "git_object": {"algorithm": self.algorithm, "oid": entry.blob, "mode": entry.mode} if entry else None}
        raw, pointer = self._pointer(name)
        if prefix == raw and size == len(raw):
            raise StorageIdentityError("LFS payload is not hydrated: " + name)
        if size != pointer["size"] or payload["sha256"] != pointer["oid"]:
            raise StorageIdentityError("Hydrated LFS payload does not match its committed SHA-256 and size: " + name)
        return {"schema_version": SCHEMA, "profile": PROFILE, "kind": "git-lfs",
                "basis": "index" if self.revision is None else self.revision,
                "git_object": {"algorithm": self.algorithm, "oid": entry.blob,
                               "mode": entry.mode, "bytes": len(raw)},
                "pointer": pointer, "payload": payload, "hydrated": True}


def configure_offline_filters(root: Path) -> dict:
    """Set only known local filters; no hooks, remotes, credentials or transfers."""
    executable = shutil.which("git-lfs")
    if executable is None:
        raise StorageIdentityError("Hydrated LFS validation requires a separately prepared git-lfs client")
    executable = str(Path(executable).resolve())
    version = subprocess.run([executable, "version"], capture_output=True, text=True,
                             check=True, timeout=15).stdout.strip()
    matched = re.match(r"git-lfs/(\d+)\.(\d+)\.(\d+)(?: |$)", version)
    if matched is None or tuple(map(int, matched.groups())) < (3, 8, 1):
        raise StorageIdentityError("This storage profile requires a separately prepared Git LFS 3.8.1 or newer client")
    command = shlex.quote(executable)
    git_directory = Path(git(root, "rev-parse", "--absolute-git-dir").decode().strip())
    if not git_directory.is_relative_to(Path(root).resolve()):
        raise StorageIdentityError("Offline filter configuration requires owned isolated Git metadata")
    settings = {"core.hooksPath": os.devnull, "core.attributesFile": os.devnull,
                "lfs.storage": str(git_directory / "lfs"),
                "filter.lfs.clean": command + " clean -- %f",
                "filter.lfs.smudge": command + " smudge --skip -- %f",
                "filter.lfs.process": command + " filter-process --skip",
                "filter.lfs.required": "true"}
    for key, value in settings.items():
        git(root, "config", "--local", key, value)
    return {"executable": executable, "version": version, "automatic_downloads": False,
            "source_configuration_copied": False, "hooks_installed": False,
            "private_cache": str(git_directory / "lfs")}


def prepare_offline_workspace(root: Path) -> dict:
    """Verify copied hydration and populate a private cache before status checks."""
    context = StorageContext(root)
    bindings = [{"path": name, **context.verify_file(name)} for name in context.lfs_paths]
    report = {"schema_version": SCHEMA, "profile": PROFILE, "lfs_files": bindings,
              "network_transfers": False, "source_configuration_copied": False}
    if not bindings:
        return report
    git_directory = Path(git(root, "rev-parse", "--absolute-git-dir").decode().strip())
    if not git_directory.is_relative_to(Path(root).resolve()):
        raise StorageIdentityError("The isolated workspace must own its Git metadata and LFS cache")
    report["client"] = configure_offline_filters(root)
    for binding in bindings:
        oid = binding["pointer"]["oid"].removeprefix("sha256:")
        target = git_directory / "lfs/objects" / oid[:2] / oid[2:4] / oid
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_symlink() or not target.resolve().is_relative_to(git_directory):
            raise StorageIdentityError("Private LFS cache path escapes the isolated Git directory")
        if target.exists():
            with target.open("rb") as stream:
                actual = hashlib.file_digest(stream, "sha256").hexdigest()
            if target.stat().st_size != binding["pointer"]["size"] or actual != oid:
                raise StorageIdentityError("Conflicting private LFS cache object: " + binding["path"])
        else:
            with (Path(root) / binding["path"]).open("rb") as source, target.open("xb") as destination:
                shutil.copyfileobj(source, destination, length=1024 * 1024)
            with target.open("rb") as stream:
                actual = hashlib.file_digest(stream, "sha256").hexdigest()
            if target.stat().st_size != binding["pointer"]["size"] or actual != oid:
                raise StorageIdentityError("Copied private LFS object differs: " + binding["path"])
    return report
