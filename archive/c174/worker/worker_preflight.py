#!/usr/bin/env python3
"""Screen the pinned, fixed-camera FlowHMR worker using its own Python interpreter."""

import argparse
import hashlib
import importlib
import importlib.metadata
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

UPSTREAM = "87ebb483ce9da32be72c67971bc8fd76f27251f3"
CHECKPOINT = "b7eb06b119feaf5ad7287bafdb2fff38d42dfc22ea9d256f8cdd2ada26dfc53a"
CONFIG = "5deae01800c031975558bf9675819e8d1e24803414f692b8b5c2196b266c64d7"
PUBLIC = {
    "ckpts/yolox/yolox_l.pth": "1e6b7fa6240375370b2a8a8eab9066b3cdd43fd1d0bfa8d2027fd3a51def2917",
    "assets/body_models/smpl_neutral_J_regressor.pt": "70e3213bd30fe8d8ce37b54675282745e406f915a51511a003aeff99b6da04cf",
}
RESTRICTED = (
    "ckpts/sam-3d-body-dinov3/model.ckpt",
    "ckpts/sam-3d-body-dinov3/assets/mhr_model.pt",
    "ckpts/sam-3d-body-dinov3/model_config.yaml",
    "assets/body_models/smplh/neutral/model.npz",
)


def inspect_file(path, expected=None):
    """Hash pinned public files. For provider assets check only for a readable payload."""
    try:
        info = path.stat()
        if not stat.S_ISREG(info.st_mode) or not info.st_size:
            return {"status": "invalid", "reason": "empty or not a regular file"}
        with path.open("rb") as stream:
            if stream.read(64).startswith(b"version https://git-lfs.github.com/spec/v1"):
                return {"status": "invalid", "reason": "Git LFS pointer"}
            result = {"status": "pass", "bytes": info.st_size}
            if expected:
                stream.seek(0)
                digest = hashlib.sha256()
                for chunk in iter(lambda: stream.read(2**20), b""):
                    digest.update(chunk)
                result["sha256"] = digest.hexdigest()
                if result["sha256"] != expected:
                    result.update(status="mismatch", expected_sha256=expected)
            return result
    except FileNotFoundError:
        return {"status": "missing"}
    except OSError as exc:
        return {"status": "unknown", "reason": type(exc).__name__}


def git(checkout, *args):
    return subprocess.run(["git", "-C", str(checkout), *args], check=True,
                          capture_output=True, text=True, timeout=30).stdout


def generator_assets(checkpoint):
    # OntoKin resolves the checkpoint before FlowHMR looks for its sibling config.
    try:
        target = checkpoint.resolve()
    except (OSError, RuntimeError) as exc:
        unknown = {"status": "unknown", "reason": type(exc).__name__}
        return {"generator_checkpoint": unknown.copy(), "generator_config.yml": unknown.copy()}
    config = target.parent / "config.yml"
    return {
        "generator_checkpoint": {**inspect_file(target, CHECKPOINT), "path": str(target)},
        "generator_config.yml": {**inspect_file(config, CONFIG), "path": str(config)},
    }


def source(checkout):
    try:
        head = git(checkout, "rev-parse", "HEAD").strip()
        dirty = bool(git(checkout, "status", "--porcelain", "--untracked-files=no").strip())
        subs = git(checkout, "submodule", "status", "--recursive").splitlines()
        return {"status": "pass" if head == UPSTREAM and not dirty and subs
                and all(line.startswith(" ") for line in subs) else "mismatch",
                "revision": head, "tracked_changes": dirty, "recursive_submodule_status": subs}
    except (OSError, subprocess.SubprocessError) as exc:
        return {"status": "unknown", "reason": type(exc).__name__}


def cuda():
    try:
        import torch
        available = torch.cuda.is_available()
        count = torch.cuda.device_count()
        result = {"status": "unavailable", "torch": str(torch.__version__),
                  "build_cuda": torch.version.cuda, "available": available, "device_count": count}
        if available and count > 0:
            # is_available() can see a driver even if a small kernel cannot run.
            if torch.ones(1, device="cuda").add_(1).item() == 2:
                result.update(status="pass", device=torch.cuda.get_device_name())
        return result
    except Exception as exc:
        return {"status": "unknown", "reason": type(exc).__name__}


def ffmpeg(checkout):
    # Use the same three choices as FlowHMR's runtime_video_processing.find_ffmpeg.
    exe = os.environ.get("FFMPEG") or shutil.which("ffmpeg")
    if not exe:
        try:
            import imageio_ffmpeg
            exe = imageio_ffmpeg.get_ffmpeg_exe()
        except ModuleNotFoundError:
            return {"status": "missing"}
        except Exception as exc:
            return {"status": "unknown", "reason": type(exc).__name__}
    try:
        version = subprocess.run([exe, "-version"], cwd=checkout, check=True, text=True,
                                 capture_output=True, timeout=10).stdout.splitlines()
        if not version or not version[0].startswith("ffmpeg version "):
            return {"status": "invalid", "executable": exe}
        return {"status": "pass", "executable": exe, "version": version[0]}
    except FileNotFoundError:
        return {"status": "missing" if checkout.is_dir() else "unknown", "executable": exe}
    except (OSError, subprocess.SubprocessError) as exc:
        return {"status": "unknown", "executable": exe, "reason": type(exc).__name__}


def dependencies(checkout):
    # These three imports follow the upstream search paths and do not load model weights.
    sys.path[:0] = [str(checkout), str(checkout / "third_party/YOLOX"),
                    str(checkout / "third_party/sam-3d-body")]
    imports = {}
    for name in ("yolox", "sam_3d_body", "supervision"):
        try:
            importlib.import_module(name)
            imports[name] = "pass"
        except Exception as exc:
            imports[name] = type(exc).__name__
    versions = {}
    try:
        from packaging.requirements import Requirement
        for relative in ("requirements.txt", "tools/web/requirements.txt"):
            for raw in (checkout / relative).read_text().splitlines():
                line = raw.partition("#")[0].strip()
                if not line or line.startswith("-"):
                    continue
                req = Requirement(line)
                try:
                    installed = importlib.metadata.version(req.name)
                    ok = installed in req.specifier
                    versions[str(req)] = {"installed": installed, "status": "pass" if ok else "mismatch"}
                except importlib.metadata.PackageNotFoundError:
                    versions[str(req)] = {"status": "missing"}
    except Exception as exc:
        return {"status": "unknown", "reason": type(exc).__name__, "imports": imports,
                "requirements": versions}
    ok = bool(versions) and all(v["status"] == "pass" for v in versions.values())
    return {"status": "pass" if ok and all(v == "pass" for v in imports.values()) else "mismatch",
            "requirements": versions, "imports": imports}


def screen(checkout, checkpoint):
    checks = {"platform": {"status": "pass" if platform.system() == "Linux" else "mismatch",
                           "system": platform.system(), "machine": platform.machine()},
              "python": {"status": "pass" if sys.version_info[:2] == (3, 10) else "mismatch",
                         "version": platform.python_version(), "executable": sys.executable},
              "source": source(checkout), "cuda": cuda(), "ffmpeg": ffmpeg(checkout),
              "dependencies": dependencies(checkout)}
    public = {rel: inspect_file(checkout / rel, digest) for rel, digest in PUBLIC.items()}
    public.update(generator_assets(checkpoint))
    restricted = {rel: inspect_file(checkout / rel) for rel in RESTRICTED}
    passed = all(c["status"] == "pass" for group in (checks, public, restricted) for c in group.values())
    return {"schema": "ontokin.handoff.flowhmr_worker_preflight/1",
            "collected_utc": datetime.now(timezone.utc).isoformat(),
            "decision": "prerequisites_passed" if passed else "blocked",
            "checkout": str(checkout), "generator_checkpoint": str(checkpoint),
            "checks": checks, "public_assets": public, "provider_assets": restricted,
            "provider_authorization": "not assessed by this local screen"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path)
    parser.add_argument("checkpoint", type=Path)
    args = parser.parse_args()
    os.environ["PATH"] = str(Path(sys.executable).parent) + os.pathsep + os.environ.get("PATH", "")
    os.environ["HF_HUB_OFFLINE"] = "1"
    # Python and native imports can write status messages to stdout. Keep JSON on its own stream.
    sys.stdout.flush()
    with os.fdopen(os.dup(sys.stdout.fileno()), "w") as report:
        os.dup2(sys.stderr.fileno(), sys.stdout.fileno())
        result = screen(args.checkout.absolute(), args.checkpoint.absolute())
        print(json.dumps(result, indent=2), file=report)
    return 0 if result["decision"] == "prerequisites_passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
