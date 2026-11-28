"""C271-P37 stage S2: measure the derived route's Git reads (FZ-02) in a driver-prepared workspace.

Run from env -i as: <worktree>/.venv/bin/python -B measure_fz02.py OUT_DIR
It copies the clean worktree with the driver's own prepare_workspace into OUT_DIR/prep-001, binds HOST's Git
through the driver's bind_git, and times the provider's status and untracked-file reads through the driver's
git_read, five times each, before and after `update-index -q --refresh`. It writes OUT_DIR/MEASURE-001.json.
"""
import json, os, platform, subprocess, sys, time
from pathlib import Path

WT = Path("<worktree>")
OUT = Path(sys.argv[1])
assert OUT.is_dir() and not any(OUT.iterdir()), "the output directory must exist and be empty"
sys.path.insert(0, str(WT))
from tools import check_local  # noqa: E402

GIT = {"path": "/Library/Developer/CommandLineTools/usr/bin/git",
       "sha256": "be4afb2b003904725826250de9fb76567bbacf82323457b5a1ec26706b66bcae"}
STATUS = ("status", "--porcelain=v1", "--untracked-files=no")
UNTRACKED = ("ls-files", "--others", "--exclude-standard", "-z")
record = {"schema": "ontokin.c271.p37-fz02-measurement/1", "stage": "S2", "director": "c271-p37-08beec34eb0a",
          "started_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "python": sys.version.split()[0],
          "platform": platform.platform(), "interpreter_flags": {"dont_write_bytecode": sys.dont_write_bytecode},
          "environment_names": sorted(os.environ), "git_binding": None, "source": {}, "copy": {}, "reads": {}}


def timed(root, args, timeout):
    started = time.monotonic()
    try:
        out = check_local.git_read(root, *args, timeout=timeout)
        return {"seconds": round(time.monotonic() - started, 4), "exit": 0, "output": out}
    except subprocess.CalledProcessError as exc:
        return {"seconds": round(time.monotonic() - started, 4), "exit": exc.returncode,
                "output": (exc.output or "").rstrip("\n"), "stderr": (exc.stderr or "")[:2000]}


record["git_binding"] = check_local.bind_git(GIT["path"], GIT["sha256"])
source = check_local.git_metadata(WT)
record["source"] = {"head": source.get("local_head"), "tree": source.get("local_tree"),
                    "tracked_worktree_status": source.get("tracked_worktree_status"),
                    "untracked_source_files": source.get("untracked_source_files")}
assert source["available"] and source["tracked_worktree_status"] == "" and not source["untracked_source_files"], source

# The original checkout, which has stat data in its index, for comparison.
record["reads"]["original_status"] = [{k: v for k, v in timed(WT, STATUS, 60).items() if k != "output"} for _ in range(3)]

output = OUT / "prep-001"
output.mkdir()
started = time.monotonic()
workspace = check_local.prepare_workspace(WT, output, False, source_git=source)
record["copy"]["prepare_workspace_seconds"] = round(time.monotonic() - started, 3)
files = size = 0
for parent, dirs, names in os.walk(workspace):
    if Path(parent).name == ".git" or "/.git/" in parent + "/":
        continue
    dirs[:] = [d for d in dirs if d != ".git"]
    for name in names:
        files += 1
        size += os.lstat(os.path.join(parent, name)).st_size
record["copy"].update(workspace=str(workspace), files_outside_git=files, bytes_outside_git=size)

rows = []
for i in range(5):
    status, untracked = timed(workspace, STATUS, 120), timed(workspace, UNTRACKED, 120)
    rows.append({"status_seconds": status["seconds"], "status_exit": status["exit"],
                 "status_lines": status["output"].splitlines(), "untracked_seconds": untracked["seconds"],
                 "untracked_exit": untracked["exit"], "untracked_names": [n for n in untracked["output"].split("\0") if n]})
record["reads"]["workspace_before_refresh"] = rows
refresh = timed(workspace, ("update-index", "-q", "--refresh"), 600)
record["reads"]["refresh"] = {k: v for k, v in refresh.items() if k != "output"} | {"output_lines": refresh["output"].splitlines()[:20]}
rows = []
for i in range(5):
    status, untracked = timed(workspace, STATUS, 120), timed(workspace, UNTRACKED, 120)
    rows.append({"status_seconds": status["seconds"], "status_exit": status["exit"],
                 "status_lines": status["output"].splitlines(), "untracked_seconds": untracked["seconds"],
                 "untracked_exit": untracked["exit"], "untracked_names": [n for n in untracked["output"].split("\0") if n]})
record["reads"]["workspace_after_refresh"] = rows
record["git_binding_after"] = check_local.git_binding() if hasattr(check_local, "git_binding") else None
record["ended_at_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
target = OUT / "MEASURE-001.json"
fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
with os.fdopen(fd, "w", encoding="utf-8") as handle:
    handle.write(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
summary = {key: [r["status_seconds"] for r in record["reads"][key]] for key in ("workspace_before_refresh", "workspace_after_refresh")}
print(json.dumps({"copy_seconds": record["copy"]["prepare_workspace_seconds"], "files": files, "bytes": size,
                  "original_status": [r["seconds"] for r in record["reads"]["original_status"]], **summary,
                  "refresh": record["reads"]["refresh"]["seconds"], "refresh_exit": record["reads"]["refresh"]["exit"],
                  "status_lines_before": len(record["reads"]["workspace_before_refresh"][0]["status_lines"])}))
