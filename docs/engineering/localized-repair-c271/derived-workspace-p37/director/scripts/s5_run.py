"""C271-P37 stage S5: run the focused modules once each and compare them with MI's final-003 logs.

Run as: python3 -I -S -B s5_run.py OUT_DIR NEW_CONTROL_MODULE
Each module runs in its own process from the worktree root, as
  /usr/bin/env -i HOME LOGNAME USER PATH=/usr/bin:/bin TMPDIR=<resolved>/ .venv/bin/python -B -m unittest -v <module>
The logs stay in OUT_DIR (they may hold account values); the record holds digests and collected outcomes.
"""
import hashlib, json, os, subprocess, sys, tempfile, time
from pathlib import Path

WT = Path("<worktree>")
MI = Path("<local>/c271-p33/checks/final-003")
COLLECTOR = WT / "docs/engineering/localized-repair-c271/macos-routine-p36/tooling/unit_log_outcomes.py"
OUT = Path(sys.argv[1])
NEW = sys.argv[2]
assert OUT.is_dir() and not any(OUT.iterdir())
MODULES = ["tests.test_local_checks", "tests.test_current_host_readback_provider_v02",
           "tests.test_current_host_readback_driver_v02", "tests.test_current_host_readback_controls_v02", NEW,
           "tests.test_current_host_readback_driver", "tests.test_current_host_readback_provider",
           "tests.test_prepare_current_host_readback_v02", "tests.test_static_tray_readback_v01",
           "tests.test_force_conformance", "tools.storage_tests.test_storage_identity"]
CHANGED = ["tools/check_local.py", "prototypes/static_tray_v01/current_host_readback_v02.py",
           "tests/test_local_checks.py", "tests/test_current_host_readback_provider_v02.py",
           NEW.replace(".", "/") + ".py"]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


tmp = os.path.realpath(tempfile.gettempdir()) + "/"
env = {"HOME": os.environ["HOME"], "LOGNAME": os.environ["LOGNAME"], "USER": os.environ["USER"],
       "PATH": "/usr/bin:/bin", "TMPDIR": tmp}
record = {"schema": "ontokin.c271.p37-s5-run/1", "stage": "S5", "director": "c271-p37-08beec34eb0a",
          "started_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
          "command": "/usr/bin/env -i HOME LOGNAME USER PATH=/usr/bin:/bin TMPDIR=<resolved>/ .venv/bin/python -B -m unittest -v <module>, from the worktree root, one process per module",
          "environment_names": sorted(env), "changed_files_at_run": {p: sha(WT / p) for p in CHANGED}, "modules": []}
for module in MODULES:
    log = OUT / (module + ".txt")
    started = time.time()
    with open(log, "wb") as handle:
        result = subprocess.run(["/usr/bin/env", "-i", *[f"{k}={v}" for k, v in env.items()],
                                 str(WT / ".venv/bin/python"), "-B", "-m", "unittest", "-v", module],
                                cwd=WT, stdout=handle, stderr=subprocess.STDOUT, timeout=1800)
    ended = time.time()
    row = {"module": module, "exit": result.returncode, "seconds": round(ended - started, 2),
           "log": log.name, "log_sha256": sha(log)}
    collected = OUT / (module + ".collect.json")
    c = subprocess.run([sys.executable, "-I", "-S", "-B", str(COLLECTOR), "collect", "--log", str(log),
                        "--log-sha256", row["log_sha256"], "--output", str(collected)], capture_output=True, text=True)
    row["collect_exit"] = c.returncode
    if c.returncode == 0 or collected.exists():
        doc = json.loads(collected.read_text(encoding="utf-8"))
        row["collect_sha256"] = sha(collected)
        row["counts"] = doc.get("counts") or doc.get("footer")
    else:
        row["collect_stderr"] = c.stderr[-2000:]
    base = MI / (module + ".txt")
    if base.exists():
        bc = OUT / (module + ".mi-final-003.collect.json")
        b = subprocess.run([sys.executable, "-I", "-S", "-B", str(COLLECTOR), "collect", "--log", str(base),
                            "--log-sha256", sha(base), "--output", str(bc)], capture_output=True, text=True)
        row["mi_log_sha256"] = sha(base)
        row["mi_collect_exit"] = b.returncode
        if b.returncode == 0 or bc.exists():
            row["mi_collect_sha256"] = sha(bc)
        else:
            row["mi_collect_stderr"] = b.stderr[-2000:]
    record["modules"].append(row)
    print(module, "exit", result.returncode, "collect", c.returncode, round(ended - started, 1), "s", flush=True)
record["changed_files_after_run"] = {p: sha(WT / p) for p in CHANGED}
record["ended_at_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
(OUT / "S5-RUN.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("written", sha(OUT / "S5-RUN.json"))
