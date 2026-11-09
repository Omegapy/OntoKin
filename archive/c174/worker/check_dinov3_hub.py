#!/usr/bin/env python3
"""Test a staged DINOv3 Torch Hub entry point in a fresh worker Python process."""
import json
import sys
from pathlib import Path
from urllib.error import HTTPError

REPO = "facebookresearch/dinov3"
ENTRY = "dinov3_vith16plus"


def allow_branch_lookup(event, args):
    # PyTorch queries main even with a warm cache. Keep all source/weight downloads
    # out of this standalone diagnostic. The production worker is unchanged.
    if event == "urllib.Request" and args[0].rstrip("/") != f"https://github.com/{REPO}/tree/main":
        raise RuntimeError("Network request outside the Torch Hub branch lookup refused")


def check(torch):
    hub = torch.hub
    cache = Path(hub.get_dir())
    result = {"torch": str(torch.__version__), "repo": REPO, "entrypoint": ENTRY,
              "hub_directory": str(cache)}
    candidates = [cache / f"facebookresearch_dinov3_{ref}" for ref in ("main", "master")]
    if not any((candidate / "hubconf.py").is_file() for candidate in candidates):
        return dict(result, status="source_not_staged")
    try:
        # The same repository and entry-point lookup as load(), up to the
        # constructor. help() imports hubconf and checks its declared dependencies.
        hub.help(REPO, ENTRY)
    except HTTPError as exc:
        return dict(result, status="branch_lookup_refused", http_status=exc.code)
    except ModuleNotFoundError as exc:
        return dict(result, status="import_failed", missing_module=exc.name)
    except Exception as exc:
        return dict(result, status="lookup_failed", error=type(exc).__name__, detail=str(exc)[:300])
    return dict(result, status="entrypoint_available")


def main():
    sys.addaudithook(allow_branch_lookup)
    try:
        import torch
    except ImportError as exc:
        report = {"status": "import_failed", "missing_module": exc.name}
    else:
        report = check(torch)
    print(json.dumps(report, indent=2))
    return int(report["status"] != "entrypoint_available")


if __name__ == "__main__":
    raise SystemExit(main())
