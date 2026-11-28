"""W2 exploration: does a logging 'git' wrapper placed first on PATH, which execs the PATH Git found
before it, recurse through the macOS dispatcher? Runs Git only, in a fresh temporary directory."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

real = os.path.abspath(shutil.which("git"))
facts = {}
with tempfile.TemporaryDirectory(prefix="w2-path-") as temporary:
    base = Path(os.path.realpath(temporary))
    log = base / "log.txt"
    bindir = base / "bin"
    bindir.mkdir()
    wrapper = bindir / "git"
    wrapper.write_text("#!/bin/sh\nprintf '%%s\\n' \"$*\" >> '%s'\nexec '%s' \"$@\"\n" % (log, real))
    os.chmod(wrapper, 0o755)
    env = dict(os.environ, PATH=str(bindir) + ":" + os.environ["PATH"])
    found = shutil.which("git", path=env["PATH"])
    facts["which_finds_wrapper"] = found == str(wrapper)
    repo = base / "repo"
    repo.mkdir()
    for args in (["--version"], ["-C", str(repo), "init", "--quiet", "--template="], ["-C", str(repo), "status", "--porcelain=v1"]):
        p = subprocess.run([found, *args], capture_output=True, env=env, timeout=30)
        facts.setdefault("exits", []).append(p.returncode)
    facts["log_lines"] = len(log.read_text().splitlines())
json.dump(facts, sys.stdout)
print()
