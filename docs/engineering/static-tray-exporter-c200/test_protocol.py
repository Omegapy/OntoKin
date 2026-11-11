"""Child-free C200 gate controls; mocks never stand in for full lock approval."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT), str(Path(__file__).resolve().parent)]
from prototypes.static_tray_v01.supervisor import Stop
from qualification_gate import (DIRECTORY, EXPECTED_ALLOWANCE, REQUIRED_PROTOCOL, REVISION,
                                revision_binding, verify_definition, verify_revision)


class ProtocolControls(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="c200-gate-control-")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.definition, self.old = verify_definition(ROOT)

    def fixture(self):
        path = self.directory / "input-lock.json"
        schedule = self.directory / "new-c200-schedule"
        required = {DIRECTORY + "/" + name for name in REQUIRED_PROTOCOL} | set(self.definition["preserved_files"])
        lock = {"repo_root": str(ROOT), "schedule_root": str(schedule),
                "implementation": {"commit": "seam-only", "tree": "seam-only"},
                "host": {"python": sys.executable}, "host_environment": {}, "coordinator_environment": {},
                "repository_files": {relative: {} for relative in required}}
        lock["qualification_revision"] = revision_binding(ROOT, path, schedule, self.definition)
        lock["coordinator_command"] = [sys.executable, "-IBS", str(ROOT / DIRECTORY / "run_qualification.py"),
                                       "--lock", str(path)]
        approval = {"qualification_revision_id": REVISION,
                    "qualification_revision_sha256": lock["qualification_revision"]["definition"]["sha256"],
                    "preserved_c199_input_lock_sha256": self.definition["preserved_c199"]["input_lock_sha256"],
                    "authorization_scope": EXPECTED_ALLOWANCE}
        return lock, path, approval

    def gate(self, lock, path, *, approval=True, fresh=True):
        # Full byte checks are exercised by the production lock verifier and
        # separate real preserved-evidence tests below. This seam isolates the
        # additional C200 provenance/one-invocation decisions without children.
        with patch("qualification_gate.verify_definition", return_value=(self.definition, self.old)), \
                patch("qualification_gate.check_file"):
            return verify_revision(lock, path, approval=approval, fresh=fresh)

    def test_real_preserved_failure_has_one_consumed_start(self):
        self.assertEqual(self.definition["preserved_c199"]["native_construction_starts"], 1)
        self.assertEqual(self.definition["preserved_c199"]["receiving_starts"], 0)
        self.assertFalse(self.definition["preserved_c199"]["resume_permitted"])

    def test_changed_old_ledger_fails_its_real_hash(self):
        root = self.directory / "copy"
        names = set(self.definition["preserved_files"]) | {DIRECTORY + "/QUALIFICATION.json"}
        for relative in names:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        ledger = root / "docs/engineering/static-tray-qualification-c199/evidence/native-execution/receipts/attempts.jsonl"
        ledger.write_bytes(ledger.read_bytes() + b"\n")
        with self.assertRaisesRegex(Stop, "Locked file"):
            verify_definition(root)

    def test_old_schedule_is_never_reused(self):
        lock, path, _ = self.fixture()
        lock["schedule_root"] = self.old["schedule_root"]
        with self.assertRaisesRegex(Stop, "stopped schedule"):
            self.gate(lock, path, approval=False)

    def test_new_directory_alone_is_not_revision_authority(self):
        lock, path, _ = self.fixture()
        del lock["qualification_revision"]
        with self.assertRaisesRegex(Stop, "authority"):
            self.gate(lock, path, approval=False)

    def test_existing_schedule_blocks_resume(self):
        lock, path, _ = self.fixture()
        Path(lock["schedule_root"]).mkdir()
        with self.assertRaisesRegex(Stop, "cannot be resumed"):
            self.gate(lock, path, approval=False)

    def test_existing_invocation_blocks_unknown_outcome_retry(self):
        lock, path, _ = self.fixture()
        Path(lock["qualification_revision"]["invocation_receipt"]).write_text("uncertain prior invocation")
        with self.assertRaisesRegex(Stop, "already invoked"):
            self.gate(lock, path, approval=False)

    def test_historical_approval_cannot_authorize_new_cohort(self):
        lock, path, approval = self.fixture()
        del approval["qualification_revision_id"]
        path.with_suffix(".approval.json").write_text(json.dumps(approval))
        with self.assertRaisesRegex(Stop, "does not authorize"):
            self.gate(lock, path)

    def test_changed_start_allowance_is_rejected(self):
        lock, path, approval = self.fixture()
        approval = deepcopy(approval)
        approval["authorization_scope"]["native_construction_starts"] = 13
        path.with_suffix(".approval.json").write_text(json.dumps(approval))
        with self.assertRaisesRegex(Stop, "changes the new allowance"):
            self.gate(lock, path)

    def test_coordinator_script_must_be_bound(self):
        lock, path, _ = self.fixture()
        del lock["repository_files"][DIRECTORY + "/run_qualification.py"]
        with self.assertRaisesRegex(Stop, "not input-bound"):
            self.gate(lock, path, approval=False)

    def test_exact_new_authority_passes_only_this_metadata_seam(self):
        lock, path, approval = self.fixture()
        path.with_suffix(".approval.json").write_text(json.dumps(approval))
        self.assertEqual(self.gate(lock, path)["revision_id"], REVISION)


if __name__ == "__main__":
    unittest.main(verbosity=2)
