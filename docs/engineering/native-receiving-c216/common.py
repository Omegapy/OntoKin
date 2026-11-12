"""Read-only binding helpers shared by the C216 host and native capture."""

from __future__ import annotations

import base64
import hashlib
import io
import json
from pathlib import Path
import tarfile


PROFILE = "c210-blender-corner-adapter-c215/0.1"
SOURCE_NAMES = ("README.md", "CONTRACT.md", "common.py", "capture.py", "run.py", "build_bindings.json")
ARTIFACT_NAMES = {
    "receiver_source": "receiver-source.json",
    "importer_source": "importer-source.tar",
    "build_record": "build-record.json",
    "import_settings": "import-settings.json",
}
TEXT_NAMES = {
    "after.glb": "C216 accepted GLB base64",
    "after.program.bundle.json": "C216 accepted source bundle",
    "after.semantic.json": "C216 semantic sidecar",
    "source-payload.json": "C216 exact source normal authority",
}
TIMES = (0, 0.25, 0.5, 0.75, 1, 1.5, 2)


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def descriptor(data):
    return {"bytes": len(data), "sha256": digest(data)}


def read_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "Duplicate JSON member: " + key)
            result[key] = value
        return result
    def bad_constant(value):
        raise RuntimeError("Nonfinite JSON token: " + value)
    return json.loads(Path(path).read_bytes(), object_pairs_hook=pairs, parse_constant=bad_constant)


def write_json(path, value, exclusive=False):
    with Path(path).open("xb" if exclusive else "wb") as stream:
        stream.write(canonical(value) + b"\n")
        stream.flush()
        import os
        os.fsync(stream.fileno())


def importer_archive(root):
    """Retain exact installed importer source without launching or importing it."""
    root = Path(root)
    data = io.BytesIO()
    with tarfile.open(fileobj=data, mode="w", format=tarfile.PAX_FORMAT) as archive:
        for path in sorted(root.rglob("*.py")):
            raw = path.read_bytes()
            entry = tarfile.TarInfo(path.relative_to(root).as_posix())
            entry.size, entry.mode = len(raw), 0o644
            entry.uid = entry.gid = entry.mtime = 0
            archive.addfile(entry, io.BytesIO(raw))
    return data.getvalue()


def verify_installed(build):
    exe = build["executable"]
    raw = Path(exe["path"]).read_bytes()
    require(len(raw) == exe["bytes"] and hashlib.sha256(raw).hexdigest() == exe["sha256"], "Installed executable bytes differ")
    root = Path(build["importer_root"])
    cached = sorted(str(path) for suffix in ("*.pyc", "*.pyo") for path in root.rglob(suffix))
    require(not cached, "Installed importer bytecode cache must be absent: " + repr(cached))
    actual = sorted(str(path) for path in root.rglob("*.py"))
    require(actual == sorted(item["path"] for item in build["importer_python_files"]), "Installed importer file inventory differs")
    for item in build["importer_python_files"]:
        raw = Path(item["path"]).read_bytes()
        require(len(raw) == item["bytes"] and hashlib.sha256(raw).hexdigest() == item["sha256"], "Installed importer bytes differ: " + item["path"])


def verify_run(run, here):
    run, here = Path(run).resolve(), Path(here).resolve()
    plan = read_json(run / "plan.json")
    require(plan["schema"] == "ontokin.c216.native-plan/0.1", "Unknown native plan")
    require(plan["runDirectory"] == str(run), "Run location changed")
    require(plan["captureSourceDirectory"] == str(here), "Capture source location changed")
    for name, binding in plan["files"].items():
        require(descriptor((run / name).read_bytes()) == binding, "Prepared input bytes differ: " + name)
    source = read_json(run / ARTIFACT_NAMES["receiver_source"])
    repo = here.parents[2]
    for name, entry in source["files"].items():
        raw = (repo / name).read_bytes()
        require(base64.b64encode(raw).decode("ascii") == entry, "Capture/helper source bytes differ: " + name)
    build = read_json(here / "build_bindings.json")
    verify_installed(build)
    require(importer_archive(build["importer_root"]) == (run / ARTIFACT_NAMES["importer_source"]).read_bytes(), "Importer artifact differs from installation")
    return plan, build


def final_lock(run, plan):
    run = Path(run)
    artifacts = {name: descriptor((run / filename).read_bytes()) for name, filename in ARTIFACT_NAMES.items()}
    artifacts["scene"] = descriptor((run / "received.blend").read_bytes())
    return {"schema_version": "ontokin.receiving-input-lock/0.1", "profile": PROFILE,
            "sourcePayloadSha256": plan["sourcePayloadSha256"], "sourceInputs": plan["sourceInputs"],
            "receiverRevision": plan["sourceRevision"], "receiverDisposition": "future-proposed-source", "artifacts": artifacts}
