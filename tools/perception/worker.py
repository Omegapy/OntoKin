"""Run a local, separately installed model worker and import its saved observation."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile

from .flowhmr import ADAPTER_REVISION as FLOW_REVISION
from .observation import digest, import_observation
from .solv3r import ADAPTER_REVISION as SOLV_REVISION


REVISIONS = {"flowhmr": FLOW_REVISION, "solv3r": SOLV_REVISION}
VIDEOS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}


def _verify_checkout(checkout, expected):
    def git(*args):
        try:
            result = subprocess.run(["git", "-C", str(checkout), *args], text=True, capture_output=True, timeout=20)
        except subprocess.TimeoutExpired as exc:
            raise ValueError("Timed out inspecting worker checkout") from exc
        if result.returncode:
            raise ValueError(f"Cannot inspect worker checkout: {result.stderr.strip()}")
        return result.stdout.strip()

    if Path(git("rev-parse", "--show-toplevel")) != checkout or git("rev-parse", "HEAD") != expected:
        raise ValueError(f"Worker checkout must be at repository root and revision {expected}")
    if git("status", "--porcelain", "--untracked-files=no", "--ignore-submodules=untracked"):
        raise ValueError("Worker checkout has tracked changes")


def _capture_identity(adapter, media):
    if media.is_file() and media.suffix.lower() in VIDEOS:
        return {"kind": "video", "path": str(media), "sha256": digest(media)}
    if adapter != "solv3r" or not media.is_dir():
        raise ValueError("Supply a video file, or a Solv3R folder of JPG/JPEG/PNG images")
    files = {p.name: digest(p) for p in sorted(media.iterdir())
             if not p.name.startswith(".") and p.suffix.lower() in {".jpg", ".jpeg", ".png"} and p.is_file()}
    if not files:
        raise ValueError("Solv3R image folder has no supported images")
    encoded = json.dumps(files, sort_keys=True, separators=(",", ":")).encode()
    return {"kind": "image_directory", "path": str(media), "sha256": hashlib.sha256(encoded).hexdigest(),
            "files_sha256": files}


def _run(command, checkout, log, timeout):
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.update(HF_HUB_OFFLINE="1", PYTHONNOUSERSITE="1",
               PATH=str(Path(command[0]).parent) + os.pathsep + env.get("PATH", ""))
    with log.open("ab") as stream:
        proc = subprocess.Popen(command, cwd=checkout, env=env, stdout=stream, stderr=subprocess.STDOUT,
                                stdin=subprocess.DEVNULL, start_new_session=True)
        try:
            status = proc.wait(timeout=timeout)
        finally:
            # FFmpeg, trackers and data loaders may still belong to this group
            # even if their parent has already failed or received an interrupt.
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.wait()
    if status:
        raise ValueError(f"Model worker exited with status {status}; inspect {log}")


def run_worker(adapter: str, media: Path, output: Path, *, checkout: Path, python: Path,
               checkpoint: Path, timeout_s: int = 1800, static_camera: bool = False, device=None) -> dict:
    """Execute the pinned worker in its own process group; retain raw output, log and import receipt."""
    if os.name != "posix":
        raise ValueError("Worker execution requires a POSIX host with process groups")
    if adapter not in REVISIONS or (static_camera and adapter != "flowhmr"):
        raise ValueError("Select a supported worker; static_camera requires FlowHMR")
    if device not in (None, "auto", "cpu", "cuda") or (device == "cpu" and adapter != "solv3r"):
        raise ValueError("CPU mode is available for Solv3R only; choose auto, cuda or cpu")
    if type(timeout_s) is not int or not 1 <= timeout_s <= 86400:
        raise ValueError("Worker timeout must be between 1 and 86400 seconds")
    # Preserve the virtual-environment executable path even if it is a symlink.
    python = python.absolute()
    checkout, media, checkpoint = checkout.resolve(), media.resolve(), checkpoint.resolve()
    if not python.is_file() or not os.access(python, os.X_OK) or not checkpoint.is_file():
        raise ValueError("Worker requires an executable local Python and a local checkpoint file")
    _verify_checkout(checkout, REVISIONS[adapter])
    capture = _capture_identity(adapter, media)
    checkpoint_hash = digest(checkpoint)
    output = output.absolute()
    output.mkdir(parents=True, exist_ok=False)
    raw = output / "raw"
    raw.mkdir()
    log = output / "worker.log"
    log.touch()
    summary = {"schema": "ontokin.perception_worker/1", "adapter": adapter, "revision": REVISIONS[adapter],
               "checkout": str(checkout), "python": str(python), "capture": capture,
               "checkpoint": {"path": str(checkpoint), "sha256": checkpoint_hash},
               "timeout_s": timeout_s, "device_request": device or "auto", "status": "running"}
    receipt = output / "worker.json"

    def record():
        temp = receipt.with_suffix(".tmp")
        temp.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temp.replace(receipt)

    record()
    try:
        if adapter == "flowhmr":
            # The upstream CLI hardcodes <checkout>/output/<input stem>. Reserve
            # that exact directory atomically before supplying its unique stem.
            upstream = checkout / "output"
            upstream.mkdir(exist_ok=True)
            with tempfile.TemporaryDirectory(dir=upstream, prefix="ontokin_") as reservation:
                reserved = Path(reservation)
                alias = output / (reserved.name + media.suffix.lower())
                alias.symlink_to(media)
                try:
                    command = [str(python), "run_v2m_demo_generation.py", str(alias), "--ckpt", str(checkpoint)]
                    if static_camera:
                        command.append("--static_camera")
                    summary["command"] = command
                    record()
                    _run(command, checkout, log, timeout_s)
                    result = raw / (checkpoint.stem + ".npz")
                    produced = reserved / result.name
                    if not produced.is_file():
                        raise ValueError(f"FlowHMR exited without producing {result.name}")
                    shutil.copyfile(produced, result)
                finally:
                    alias.unlink(missing_ok=True)
        else:
            script = str(Path(__file__).with_name("solv3r_cpu.py").resolve()) if device == "cpu" else "examples/offline.py"
            command = [str(python), script, "--images", str(media), "--out", str(raw),
                       "--checkpoint", str(checkpoint)]
            summary["command"] = command
            record()
            _run(command, checkout, log, timeout_s)
            result = raw / "solve.npz"
            if not result.is_file():
                raise ValueError("Solv3R exited without producing solve.npz")

        if _capture_identity(adapter, media) != capture or digest(checkpoint) != checkpoint_hash:
            raise ValueError("Capture or checkpoint changed while the worker was running")
        _verify_checkout(checkout, REVISIONS[adapter])
        manifest = import_observation(adapter, result, output / "observation", source_kind="provided",
                                      checkpoint="sha256:" + checkpoint_hash, capture="sha256:" + capture["sha256"])
        summary.update(status="complete", raw_npz=str(result.relative_to(output)),
                       raw_sha256=manifest["source"]["sha256"], observation="observation",
                       sample_count=manifest["observation"]["sample_count"])
    except BaseException as exc:
        summary.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        record()
        if isinstance(exc, subprocess.TimeoutExpired):
            raise ValueError(f"Worker exceeded {timeout_s} seconds; inspect {log}") from exc
        raise
    record()
    return summary
