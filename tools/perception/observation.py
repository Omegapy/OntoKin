"""Versioned, file-based observation exchange. All paths are local."""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import importlib
import json
import math
import re
import struct
import tempfile
from pathlib import Path
from zipfile import BadZipFile, ZipFile

import numpy as np
from numpy.lib import format

SCHEMA = "ontokin.observation/1"
ADAPTERS = ("flowhmr", "solv3r")
MAX_BYTES = 256 * 1024 * 1024
MAX_MANIFEST = 4 * 1024 * 1024
KEY = re.compile(r"[A-Za-z][A-Za-z0-9_]*\Z")


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


@contextmanager
def _open_npz(source):
    # NumPy emits a plain ZIP with an uncommented end record. Bound the
    # directory before ZipFile constructs an object for every member.
    with source.open("rb") as stream:
        size = stream.seek(0, 2)
        if not 22 <= size <= MAX_BYTES + MAX_MANIFEST:
            raise ValueError("NPZ is empty, truncated or exceeds the input budget")
        stream.seek(-22, 2)
        tag, disk, start_disk, count, total, length, offset, comment = struct.unpack(
            "<4s4H2IH", stream.read(22))
        if (tag != b"PK\x05\x06" or disk or start_disk or comment or count != total
                or not 0 < count <= 128 or not 0 < length <= 128 * 1024
                or offset + length != size - 22):
            raise ValueError("Unsupported or oversized NPZ central directory")
        # Refuse an overriding ZIP64 end record, unnecessary at this size.
        if size >= 42:
            stream.seek(-42, 2)
            if stream.read(4) == b"PK\x06\x07":
                raise ValueError("Unsupported ZIP64 central directory")
        with ZipFile(stream) as archive:
            yield archive


def read_arrays(source: Path, names, *, optional=(), exact=False) -> dict[str, np.ndarray]:
    """Admit numeric or string NPY arrays with bounded allocation, without pickle."""
    if source.stat().st_size > MAX_BYTES + MAX_MANIFEST:
        raise ValueError("NPZ exceeds the 256 MiB observation input budget")
    try:
        with _open_npz(source) as archive:
            members = archive.infolist()
            if len(members) > 128 or sum(m.file_size for m in members) > MAX_BYTES:
                raise ValueError("NPZ exceeds the member or uncompressed size limit")
            files = {m.filename: m for m in members}
            if len(files) != len(members):
                raise ValueError("Duplicate NPZ member")
            if any(not n.endswith(".npy") or not KEY.fullmatch(n[:-4]) for n in files):
                raise ValueError("Invalid NPZ member name")
            if exact and set(files) != {key + ".npy" for key in names}:
                raise ValueError("Observation array inventory mismatch")
            result = {}
            for key in (*names, *optional):
                member = files.get(key + ".npy")
                if member is None:
                    if key in optional:
                        continue
                    raise ValueError(f"Missing NPZ field {key}")
                with archive.open(member) as stream:
                    version = format.read_magic(stream)
                    if version == (1, 0):
                        shape, _, dtype = format.read_array_header_1_0(stream)
                    elif version == (2, 0):
                        shape, _, dtype = format.read_array_header_2_0(stream)
                    else:
                        raise ValueError(f"Unsupported NPY version in {key}")
                    if (dtype.kind not in "biufSU" or len(shape) > 6
                            or any(n < 0 or n > MAX_BYTES for n in shape)
                            or stream.tell() + math.prod(shape) * dtype.itemsize != member.file_size):
                        raise ValueError(f"Invalid dtype, shape or length in {key}")
                with archive.open(member) as stream:
                    result[key] = format.read_array(stream, allow_pickle=False)
            return result
    except (BadZipFile, EOFError, NotImplementedError, RuntimeError) as error:
        raise ValueError(f"Invalid NPZ archive: {error}") from error


def describe(arrays):
    return {key: {"shape": list(a.shape), "dtype": a.dtype.str}
            for key, a in sorted(arrays.items())}


def import_observation(adapter: str, source: Path, output: Path, *, fps=None,
                       checkpoint=None, source_kind="provided", capture=None):
    """Record one upstream export; checkpoint and capture identifiers are caller-supplied."""
    if adapter not in ADAPTERS or source_kind not in ("provided", "published", "synthetic"):
        raise ValueError("Unknown adapter or source kind")
    if fps is not None and (not math.isfinite(fps) or fps <= 0):
        raise ValueError("FPS must be positive and finite")
    if output.exists() or output.is_symlink():
        raise ValueError(f"Choose a new output directory: {output}")
    if source.stat().st_size > MAX_BYTES + MAX_MANIFEST:
        raise ValueError("Input exceeds the observation size budget")
    source_hash = digest(source)
    provider = importlib.import_module("." + adapter, __package__)
    meta, arrays = provider.adapt(source, fps=fps)
    if digest(source) != source_hash:
        raise ValueError("Input changed during import")
    # The serialized payload must fit the same admission budget on readback.
    if sum(a.nbytes + 256 for a in arrays.values()) > MAX_BYTES:
        raise ValueError("Normalized arrays exceed the 256 MiB observation budget")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent) as temp:
        stage = Path(temp) / "observation"
        stage.mkdir()
        payload = stage / "arrays.npz"
        np.savez_compressed(payload, **arrays)
        manifest = {"schema": SCHEMA, "adapter": adapter, "writer_contract_revision": provider.ADAPTER_REVISION,
                    "source": {"name": source.name, "sha256": source_hash, "kind": source_kind,
                               "capture": capture, "checkpoint": checkpoint},
                    "observation": meta, "arrays": describe(arrays), "arrays_sha256": digest(payload)}
        manifest_file = stage / "manifest.json"
        manifest_file.write_text(json.dumps(manifest, allow_nan=False, indent=2, sort_keys=True) + "\n",
                                 encoding="utf-8")
        if manifest_file.stat().st_size > MAX_MANIFEST:
            raise ValueError("Observation manifest exceeds 4 MiB")
        if output.exists() or output.is_symlink():
            raise ValueError("Output directory appeared during import")
        stage.rename(output)
    return manifest


def load_observation(directory: Path):
    """Check a stored bundle's schema, hash, array inventory, and recorded dimensions."""
    manifest_file = directory / "manifest.json"
    if manifest_file.stat().st_size > MAX_MANIFEST:
        raise ValueError("Observation manifest exceeds 4 MiB")
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    if (not isinstance(manifest, dict) or manifest.get("schema") != SCHEMA
            or manifest.get("adapter") not in ADAPTERS):
        raise ValueError("Unsupported observation schema or adapter")
    source, meta, arrays = (manifest.get(k) for k in ("source", "observation", "arrays"))
    if (not isinstance(meta, dict) or type(meta.get("sample_count")) is not int
            or meta["sample_count"] <= 0 or not isinstance(meta.get("coordinate_system"), str)
            or not isinstance(meta.get("units"), str) or not isinstance(meta.get("capabilities"), list)
            or not isinstance(source, dict) or not isinstance(source.get("sha256"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", source["sha256"])
            or not isinstance(arrays, dict) or not 0 < len(arrays) <= 128
            or any(not KEY.fullmatch(k) for k in arrays)):
        raise ValueError("Invalid observation manifest")
    payload = directory / "arrays.npz"
    if payload.stat().st_size > MAX_BYTES + MAX_MANIFEST or digest(payload) != manifest.get("arrays_sha256"):
        raise ValueError("Observation payload digest or size mismatch")
    result = read_arrays(payload, arrays, exact=True)
    if describe(result) != arrays:
        raise ValueError("Observation array inventory mismatch")
    return manifest, result
