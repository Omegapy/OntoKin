"""The sole authorized entrypoint for the independently approved C200 cohort."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

if not sys.flags.isolated or not sys.flags.no_site or not sys.dont_write_bytecode:
    raise SystemExit("C200 requires the locked interpreter with -IBS")
ROOT = Path(__file__).resolve().parents[3]
# -B prevents cache creation, not cache reads. Reject every local source cache
# before importing the locked repository or its new standalone gate.
parent = ROOT / "prototypes"
parent_caches = [parent / "__init__.pyc", parent / "__init__.pyo", *(parent / "__pycache__").glob("__init__.*")]
if any(path.is_file() and path.suffix in {".pyc", ".pyo"} for path in parent_caches):
    raise SystemExit("Unbound parent bytecode prevents C200 source-only bootstrap")
for relative in ("ontokin", "prototypes/static_tray_v01", "tools/static_tray_reader_v01",
                 "docs/engineering/static-tray-exporter-c200"):
    if any(path.suffix in {".pyc", ".pyo"} for path in (ROOT / relative).rglob("*")):
        raise SystemExit("Unbound bytecode prevents C200 source-only bootstrap: " + relative)
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from prototypes.static_tray_v01.lock import verify_lock
from prototypes.static_tray_v01.qualification import run_qualification
from prototypes.static_tray_v01.supervisor import Clock, Stop, sha256_file
from prototypes.static_tray_v01.transaction import alarm_until, write_new
from qualification_gate import REVISION, verify_revision


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", required=True)
    args = parser.parse_args()
    lock_path = Path(args.lock).resolve()
    preflight = Clock(total_ms=30000)
    with alarm_until(preflight, preflight.end):
        lock, digest = verify_lock(lock_path, runtime=True, check=preflight.check)
        definition = verify_revision(lock, lock_path, approval=True, fresh=True, check=preflight.check)
    revision = lock["qualification_revision"]
    invocation = {"schema": "ontokin.c200.coordinator-invocation/0.1", "qualification_revision": REVISION,
                  "input_lock_sha256": digest, "approval_sha256": sha256_file(lock_path.with_suffix(".approval.json")),
                  "implementation": lock["implementation"], "actual_argv": [sys.executable, *sys.orig_argv[1:]],
                  "cwd": str(Path.cwd()), "environment": dict(os.environ),
                  "started_at_utc": datetime.now(timezone.utc).isoformat(),
                  "preserved_c199": definition["preserved_c199"], "allowance": definition["allowance"],
                  "read_only_preflight_elapsed_ms": preflight.elapsed_ms(),
                  "native_starts_before_entry": 0, "receiving_starts_before_entry": 0}
    # An exclusive receipt precedes the shared runner. Even an unknown outcome
    # before its first native start cannot authorize another coordinator call.
    write_new(revision["invocation_receipt"], invocation)
    try:
        result = run_qualification(lock_path, progress=lambda row: print(json.dumps(row, sort_keys=True), flush=True))
    except BaseException as exc:
        receipt = {"schema": "ontokin.c200.coordinator-result/0.1", "qualification_revision": REVISION,
                   "input_lock_sha256": digest, "status": "COORDINATOR_STOPPED_RECONCILIATION_REQUIRED",
                   "error": exc.as_dict() if isinstance(exc, Stop) else {"type": type(exc).__name__, "reason": str(exc)},
                   "automatic_retry_permitted": False, "native_counts": "Read append-only process/attempt evidence; never infer zero from this exception"}
        write_new(revision["result_receipt"], receipt)
        raise
    receipt = {"schema": "ontokin.c200.coordinator-result/0.1", "qualification_revision": REVISION,
               "input_lock_sha256": digest, "status": result["status"],
               "c200_native_starts": result["native_starts"], "c200_receiving_starts": result["receiving_starts"],
               "c200_read_only_checker_starts": result["read_only_checker_starts"],
               "cumulative_c199_c200_native_starts": 1 + result["native_starts"],
               "preserved_c199_native_starts": 1, "measured_gates_passed": result["measured_gates_passed"],
               "qualified": False, "visual_and_independent_review": "PENDING",
               "automatic_retry_permitted": False, "result": str(Path(lock["schedule_root"]) / "qualification-result.json")}
    write_new(revision["result_receipt"], receipt)
    print(json.dumps(receipt, sort_keys=True), flush=True)
    return 0 if result["measured_gates_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
