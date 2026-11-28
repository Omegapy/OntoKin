"""W2 exploration: Git behaviours the frozen controls rely on. Runs Git only, in a fresh temporary directory.

Imports no project code. Prints facts, never machine paths.
"""
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

GIT = shutil.which("git")
facts = {"git_on_path_is_absolute": bool(GIT and os.path.isabs(GIT))}


def env(root):
    e = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    e.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT="0", GIT_ATTR_NOSYSTEM="1",
             GIT_OPTIONAL_LOCKS="0", GIT_NO_REPLACE_OBJECTS="1", GIT_NO_LAZY_FETCH="1",
             GIT_CEILING_DIRECTORIES=str(Path(root).resolve().parent))
    return e


def git(root, *args, check=True):
    p = subprocess.run([GIT, "-c", "core.fsmonitor=false", "-C", str(root), *args], capture_output=True,
                       env=env(root), timeout=60)
    if check and p.returncode:
        raise SystemExit("git %s failed: %s" % (args, p.stderr.decode(errors="replace")))
    return p


def index_entries(root):
    raw = (Path(root) / ".git/index").read_bytes()
    assert raw[:4] == b"DIRC", raw[:4]
    version, count = struct.unpack(">II", raw[4:12])
    offset, rows, previous = 12, [], b""
    for _ in range(count):
        fields = struct.unpack(">10I20sH", raw[offset:offset + 62])
        flags = fields[11]
        extended = bool(flags & 0x4000)
        start = offset + 62 + (2 if extended else 0)
        if version == 4:
            strip, pos = 0, start
            shift = 0
            # offset varint of git's v4 encoding
            byte = raw[pos]; pos += 1
            strip = byte & 0x7F
            while byte & 0x80:
                byte = raw[pos]; pos += 1
                strip = ((strip + 1) << 7) | (byte & 0x7F)
            end = raw.index(b"\0", pos)
            name = previous[:len(previous) - strip] + raw[pos:end]
            offset = end + 1
        else:
            end = raw.index(b"\0", start)
            name = raw[start:end]
            length = end - offset
            offset = offset + ((length + 8) // 8) * 8
        previous = name
        rows.append({"path": name.decode("utf-8", "surrogateescape"), "ctime": fields[0], "mtime": fields[2],
                     "size": fields[9], "mode": oct(fields[6])})
    return version, rows


with tempfile.TemporaryDirectory(prefix="w2-explore-") as temporary:
    base = Path(os.path.realpath(temporary))
    facts["git_version"] = git(base, "--version", check=False).stdout.decode().strip()
    home = os.environ.get("HOME", "")
    facts["xdg_config_home_set"] = "XDG_CONFIG_HOME" in os.environ
    facts["account_global_ignore_file_exists"] = os.path.exists(os.path.join(home, ".config/git/ignore"))
    root = base / "source"
    root.mkdir()
    files = {".claude/.gitignore": b"local-only\n", "Makefile": b"all:\n", "tools/build/out.py": b"print(1)\n",
             "docs/_build/page.html": b"<p>x</p>\n", "tools/node_modules/pkg/index.js": b"x\n",
             "docs/.env": b"A=1\n", "fixtures/__pycache__/x.cpython-312.pyc": b"\0\0", "tools/stale.pyc": b"\0",
             ".claude/hooks/check.sh": b"#!/bin/sh\n", ".claude/two words.txt": b"space\n",
             ".claude/quote\"mark.txt": b"q\n", ".claude/naïve.txt": b"n\n", "README.md": b"readme\n",
             ".agents/skills/alpha/SKILL.md": b"skill\n", "docs/notes.md": b"notes\n"}
    for rel, data in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    os.chmod(root / ".claude/hooks/check.sh", 0o755)
    (root / ".claude/skills").mkdir(parents=True)
    os.symlink("../../.agents/skills/alpha", root / ".claude/skills/alpha")
    os.symlink("../pkg/index.js", (root / "tools/node_modules/.bin").mkdir(parents=True) or root / "tools/node_modules/.bin/tool")
    os.symlink("../README.md", root / "docs/.env.local")
    git(root, "init", "--quiet", "--template=")
    git(root, "add", "-A", "--force")
    git(root, "-c", "user.name=W2 explore", "-c", "user.email=explore@example.invalid", "commit", "--quiet", "-m", "x")
    facts["ls_files"] = git(root, "ls-files").stdout.decode().splitlines()
    facts["status_clean"] = git(root, "status", "--porcelain=v1", "--untracked-files=no").stdout.decode()
    # A workspace like the driver's: only some paths copied, then read-tree of the whole commit.
    ws = base / "workspace"
    (ws / "docs").mkdir(parents=True)
    shutil.copy2(root / "docs/notes.md", ws / "docs/notes.md")
    shutil.copy2(root / "README.md", ws / "README.md")
    (ws / ".agents/skills/alpha").mkdir(parents=True)
    shutil.copy2(root / ".agents/skills/alpha/SKILL.md", ws / ".agents/skills/alpha/SKILL.md")
    head = git(root, "rev-parse", "HEAD").stdout.decode().strip()
    git(ws, "init", "--quiet", "--template=")
    git(ws, "-c", "protocol.allow=never", "-c", "protocol.file.allow=always", "fetch", "--quiet", "--depth=1",
        "--no-tags", "--no-write-fetch-head", "--", str(root), head)
    git(ws, "update-ref", "--no-deref", "HEAD", head)
    git(ws, "read-tree", head)
    version, rows = index_entries(ws)
    facts["index_version_after_read_tree"] = version
    facts["zero_stat_after_read_tree"] = sorted(r["path"] for r in rows if r["ctime"] == 0 and r["mtime"] == 0 and r["size"] == 0)
    facts["status_before_refresh"] = git(ws, "status", "--porcelain=v1", "--untracked-files=no").stdout.decode("utf-8", "replace").splitlines()
    refresh = git(ws, "update-index", "-q", "--refresh", check=False)
    facts["refresh_exit"] = refresh.returncode
    facts["refresh_output"] = (refresh.stdout + refresh.stderr).decode("utf-8", "replace")
    version, rows = index_entries(ws)
    facts["index_version_after_refresh"] = version
    facts["zero_stat_after_refresh"] = sorted(r["path"] for r in rows if r["ctime"] == 0 and r["mtime"] == 0 and r["size"] == 0)
    facts["status_after_refresh"] = git(ws, "status", "--porcelain=v1", "--untracked-files=no").stdout.decode("utf-8", "replace").splitlines()
    # A file replaced by an empty directory, and by a directory holding one file.
    (ws / "Makefile").mkdir()
    facts["status_file_replaced_by_empty_directory"] = [l for l in git(ws, "status", "--porcelain=v1", "--untracked-files=no").stdout.decode().splitlines() if "Makefile" in l]
    (ws / "Makefile/inner.txt").write_bytes(b"x\n")
    facts["status_file_replaced_by_directory_with_file"] = [l for l in git(ws, "status", "--porcelain=v1", "--untracked-files=no").stdout.decode().splitlines() if "Makefile" in l]
    facts["untracked_file_replaced_by_directory_with_file"] = git(ws, "ls-files", "--others", "--exclude-standard", "-z").stdout.decode().split("\0")
    shutil.rmtree(ws / "Makefile")
    # Intent to add an uncopied path.
    (ws / "outside").mkdir()
    (ws / "outside/new.txt").write_bytes(b"new\n")
    git(ws, "add", "-N", "--", "outside/new.txt")
    facts["status_intent_to_add"] = [l for l in git(ws, "status", "--porcelain=v1", "--untracked-files=no").stdout.decode().splitlines() if "outside" in l]
    git(ws, "rm", "--quiet", "--cached", "--", "outside/new.txt")
    shutil.rmtree(ws / "outside")
    # Staged deletion of an uncopied path; staged addition of a new copied path.
    git(ws, "rm", "--quiet", "--cached", "--", ".claude/.gitignore")
    facts["status_staged_deletion_uncopied"] = [l for l in git(ws, "status", "--porcelain=v1", "--untracked-files=no").stdout.decode().splitlines() if ".gitignore" in l]
    git(ws, "reset", "--quiet", "--", ".claude/.gitignore")
    # A gitlink entry, as ls-tree -r prints it.
    sub = base / "sub"
    sub.mkdir()
    git(sub, "init", "--quiet", "--template=")
    (sub / "f").write_bytes(b"f\n")
    git(sub, "add", "-A")
    git(sub, "-c", "user.name=W2", "-c", "user.email=e@example.invalid", "commit", "--quiet", "-m", "s")
    subhead = git(sub, "rev-parse", "HEAD").stdout.decode().strip()
    git(root, "update-index", "--add", "--cacheinfo", "160000,%s,vendor/sub" % subhead)
    git(root, "-c", "user.name=W2 explore", "-c", "user.email=explore@example.invalid", "commit", "--quiet", "-m", "gitlink")
    facts["ls_tree_gitlink"] = [l for l in git(root, "ls-tree", "-r", "HEAD").stdout.decode().splitlines() if "vendor" in l]
    facts["status_original_with_absent_gitlink_dir"] = git(root, "status", "--porcelain=v1", "--untracked-files=no").stdout.decode().splitlines()

json.dump(facts, sys.stdout, indent=1, ensure_ascii=True)
print()
