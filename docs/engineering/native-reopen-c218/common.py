"""Read-only binding helpers shared by the C218 host and saved-scene observer."""

from __future__ import annotations

import base64
import hashlib
import io
import json
from pathlib import Path
import tarfile


PROFILE = "c210-blender-corner-adapter-c215/0.1"
SOURCE_NAMES = ("README.md", "CONTRACT.md", "common.py", "capture.py", "run.py", "build_bindings.json", "origin_guard.py", "test_origin_guard.py", "test_reopen.py")
ARTIFACT_NAMES = {
    "receiver_source": "receiver-source.json",
    "importer_source": "importer-source.tar",
    "build_record": "build-record.json",
    "import_settings": "reopen-settings.json",
}
TEXT_NAMES = {
    "after.glb": "C217 accepted GLB base64",
    "after.program.bundle.json": "C217 accepted source bundle",
    "after.semantic.json": "C217 semantic sidecar",
    "source-payload.json": "C217 exact source normal authority",
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


SCENE_DESCRIPTOR = {"bytes": 3864164, "sha256": "sha256:dd8a6f32e96e45ec92207ee3417af0b3c88a6f9d898cff6d07e4366ab79993c4"}
PRIOR_PLAN_SHA256 = "sha256:23d5cf5b91bd598121b5e7d7f4feb27bbc0ca6ae1eb60cd16c7d49b7eb8a2427"
PRIOR_SOURCE_REVISION = "6af212204d58fbac2a98f3cded44facd67c52528"
RENDER_RECIPE = {
    "engine": "CYCLES", "device": "CPU", "samples": 16, "resolution": [960, 720],
    "seed": 216, "use_denoising": False, "view_layer_use_denoising": False,
    "maxImagesPerPhase": 2,
    "views": [
        {"name": "overview", "time_seconds": 0, "eye_source_m": [4, 3, 7],
         "target_source_m": [0, 0, 0], "ortho_scale": 5.3},
        {"name": "sphere-detail", "time_seconds": 0, "eye_source_m": [-0.73, 0.18, 0.45],
         "target_source_m": [-1, 0, 0], "ortho_scale": 0.32},
    ],
}
REOPEN_ENVIRONMENT = {"PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1", "SDL_AUDIODRIVER": "dummy"}
ISOLATED_DIRECTORIES = ["BLENDER_USER_CONFIG", "BLENDER_USER_SCRIPTS", "BLENDER_USER_DATAFILES"]


def verify_scene(path):
    path = Path(path)
    require(path.is_absolute() and path.is_file() and not path.is_symlink(), "Source scene must be an absolute regular nonsymlink file")
    require(descriptor(path.read_bytes()) == SCENE_DESCRIPTOR, "Exact C217 saved-scene bytes differ")
    return path


def safe_relative(name):
    path = Path(name)
    require(type(name) is str and bool(path.parts) and name == path.as_posix() and not path.is_absolute()
            and all(part not in (".", "..", ".git") for part in path.parts), "Unsafe relative binding path")
    return path


def native_command(run, phase, executable, here):
    require(phase == "reopen", "C218 permits only a saved-scene reopen")
    return [executable, "--background", "--factory-startup", "--disable-autoexec", "--threads", "2",
            "--python-exit-code", "19", "--python", str(Path(here) / "capture.py"), "--", "--run", str(run), "--phase", phase]


def verify_run(run, here):
    run, here = Path(run).resolve(), Path(here).resolve()
    plan = read_json(run / "plan.json")
    require(plan["schema"] == "ontokin.c218.native-reopen-plan/0.1", "Unknown reopen plan")
    require(plan["maxNativeStarts"] == 1 and set(plan["commands"]) == {"reopen"}, "C218 allows only one reopen start")
    require(plan["sequence"] == ["reopen", "independent persistence/numeric/provenance/visual review", "handoff and stop"], "C218 sequence changed")
    require(plan["maximumSecondsPerStart"] == 240 and plan["maximumThreads"] == 2, "Finite resource budget changed")
    require(plan["render"] == RENDER_RECIPE and plan["environmentOverrides"] == REOPEN_ENVIRONMENT
            and plan["isolatedBlenderDirectories"] == ISOLATED_DIRECTORIES, "Reviewed rendering or environment changed")
    require(plan["runDirectory"] == str(run), "Run location changed")
    require(plan["captureSourceDirectory"] == str(here), "Observer source location changed")
    require(plan["scene"] == SCENE_DESCRIPTOR and plan["priorPlanSha256"] == PRIOR_PLAN_SHA256
            and plan["priorSourceRevision"] == PRIOR_SOURCE_REVISION, "Prior scene/source identity changed")
    verify_scene(plan["scenePath"])
    for name, binding in plan["files"].items():
        path = run / safe_relative(name)
        require(not path.is_symlink() and descriptor(path.read_bytes()) == binding, "Prepared input bytes differ: " + name)
    source = read_json(run / ARTIFACT_NAMES["receiver_source"])
    require(source["revision"] == plan["sourceRevision"] and source["tree"] == plan["sourceTree"], "Observer source identity differs")
    repo = here.parents[2]
    expected_source = {(here / name).relative_to(repo).as_posix() for name in SOURCE_NAMES}
    expected_source.update({"docs/engineering/receiving-adapter-c215/adapter.py", "docs/engineering/source-normals-c214/prototype.py"})
    require(set(source["files"]) == expected_source, "Observer dependency closure differs")
    for name, entry in source["files"].items():
        path = repo / safe_relative(name)
        require(not path.is_symlink(), "Observer source may not be a symlink")
        require(base64.b64encode(path.read_bytes()).decode("ascii") == entry, "Observer/helper source bytes differ: " + name)
    build = read_json(here / "build_bindings.json")
    require(plan["executable"] == build["executable"] and plan["importerRoot"] == build["importer_root"], "Native installation binding changed")
    require(plan["commands"]["reopen"] == native_command(run, "reopen", build["executable"]["path"], here), "Reopen command changed")
    settings = read_json(run / "reopen-settings.json")
    require(settings == {"operation": "reopen_saved_scene", "filepath": plan["scenePath"], "load_ui": False,
        "use_scripts": False, "renderRecipe": RENDER_RECIPE,
        "originalImportSettings": read_json(run / "prior/import-settings.json")}, "Reopen settings differ")
    verify_installed(build)
    require(importer_archive(build["importer_root"]) == (run / ARTIFACT_NAMES["importer_source"]).read_bytes(), "Importer artifact differs from installation")
    require(final_lock(run, plan) == read_json(run / "input-lock.json"), "Predeclared input lock differs")
    return plan, build


def final_lock(run, plan):
    run = Path(run)
    artifacts = {name: descriptor((run / filename).read_bytes()) for name, filename in ARTIFACT_NAMES.items()}
    artifacts["scene"] = descriptor(verify_scene(plan["scenePath"]).read_bytes())
    return {"schema_version": "ontokin.receiving-input-lock/0.1", "profile": PROFILE,
            "sourcePayloadSha256": plan["sourcePayloadSha256"], "sourceInputs": plan["sourceInputs"],
            "receiverRevision": plan["sourceRevision"], "receiverDisposition": "future-proposed-source", "artifacts": artifacts}
