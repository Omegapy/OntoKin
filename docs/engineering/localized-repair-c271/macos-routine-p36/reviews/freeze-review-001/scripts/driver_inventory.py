"""Recompute tools/check_local.py's inventory() of a checkout with a copy of its algorithm (read only; nothing imported).

Usage: python3 -I -S -B driver_inventory.py ROOT OUT.json
"""
import hashlib, json, os, sys
from pathlib import Path

SOURCE_DIRS = ("ontokin", "tests", "tools", "docs", "examples", "fixtures", "schemas", "prototypes", "packaging", ".github", ".agents", "TRDs")
ROOT_FILES = ("pyproject.toml", "README.md", "AGENTS.md", "GOAL.md", "STATUS.md", "CHATGPT-START-HERE.md", "ROLE.md",
              "LOCAL-START-HERE.md", "CLAUDE.md", "LICENSE", "LICENSE-CODE", "LICENSE-DOCS", "LICENSING.md", "NOTICE",
              ".gitignore", ".gitattributes", ".lfsconfig")
IGNORED = {".git", "node_modules", "__pycache__", ".venv", "venv", ".tox", ".cache",
           ".pytest_cache", ".mypy_cache", ".ruff_cache", "build", "dist", "_build"}


def ignored(name):
    return name in IGNORED or name == ".env" or name.startswith(".env.") or name.endswith((".pyc", ".pyo"))


def source_files(root):
    paths = [root / name for name in ROOT_FILES if (root / name).is_file()]
    for name in SOURCE_DIRS:
        directory = root / name
        if not directory.is_dir():
            continue
        for parent, directories, files in os.walk(directory, followlinks=False):
            directories[:] = sorted(d for d in directories if not ignored(d))
            for filename in sorted(files):
                if not ignored(filename):
                    paths.append(Path(parent) / filename)
    return sorted(paths)


def file_identity(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return {"sha256": "sha256:" + digest.hexdigest(), "bytes": path.stat().st_size}


root = Path(sys.argv[1])
files = [{"path": p.relative_to(root).as_posix(), **file_identity(p)} for p in source_files(root)]
encoded = json.dumps(files, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
result = {"root_label": "<worktree>", "sha256": "sha256:" + hashlib.sha256(encoded).hexdigest(), "file_count": len(files),
          "total_bytes": sum(f["bytes"] for f in files)}
with open(sys.argv[2], "x") as fh:
    json.dump(result, fh, indent=1)
    fh.write("\n")
print(json.dumps(result))
