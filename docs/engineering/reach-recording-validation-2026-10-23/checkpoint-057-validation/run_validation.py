"""Run only the C057 documentation or metadata check with stable input receipts."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import platform
import subprocess
import sys

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
ROOT = HERE.parents[3]
role, attempt = sys.argv[1:]
assert role in ("documentation", "metadata") and attempt.isdigit()
out = HERE / (role + "-" + attempt)
out.mkdir(exist_ok=False)


def now():
    return datetime.now(timezone.utc).isoformat()


def inventory():
    rows = []
    for p in sorted(ROOT.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(ROOT).as_posix()
        if p.name in ("checkpoint-057.json", "checkpoint-057-validation.json"):
            continue
        if HERE in p.parents and any(part.startswith(("documentation-", "metadata-")) for part in p.relative_to(HERE).parts):
            continue
        raw = p.read_bytes()
        rows.append({"path": rel, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
    return rows


before = inventory()
(out / "input-manifest.json").write_text(json.dumps(before, indent=2) + "\n")
cmd = ([sys.executable, "docs/maintenance/reorganization-2026-10-17/verify_reorganization.py"] if role == "documentation"
       else [sys.executable, str((HERE / "verify_metadata.py").relative_to(ROOT))])
start = now()
run = subprocess.run(cmd, cwd=ROOT, capture_output=True)
(out / "stdout.txt").write_bytes(run.stdout)
(out / "stderr.txt").write_bytes(run.stderr)
after = inventory()
end = now()
stable = before == after
try:
    result = json.loads(run.stdout)
except (ValueError, UnicodeDecodeError):
    result = {"unparsed_stdout": True}
(out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
record = {"schema": "ontokin.checkpoint057-validation-command/0.1", "role": role, "attempt": attempt,
          "command": cmd, "cwd": str(ROOT), "source_parent_commit": "8287be55a21c28320aa11895cadd29c68ae18f90",
          "source_parent_tree": "274acc026f2e0d5dee3eb4a754790cc420a354a0", "provider": "local",
          "interpreter": sys.executable, "python": sys.version, "platform": platform.platform(),
          "started_utc": start, "ended_utc": end, "exit_code": run.returncode,
          "inputs": len(before), "input_bytes": sum(x["bytes"] for x in before), "inputs_stable": stable,
          "input_manifest_sha256": hashlib.sha256((out / "input-manifest.json").read_bytes()).hexdigest(),
          "summary_exclusions": ["checkpoint-057.json", "checkpoint-057-validation.json", "C057 validation command output directories"],
          "product_execution": False}
(out / "command.json").write_text(json.dumps(record, indent=2) + "\n")
if not stable:
    (out / "inputs-after.json").write_text(json.dumps(after, indent=2) + "\n")
print(json.dumps({"role": role, "attempt": attempt, "exit_code": run.returncode, "inputs": len(before),
                  "inputs_stable": stable, "output": str(out)}))
raise SystemExit(run.returncode if stable else 2)
