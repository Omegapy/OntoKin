"""Current-code C20 may be pending only for exact implementation identity drift."""
import copy
import unittest

from tools.verify_construction_ci import IDENTITY_MISMATCH, assess


class VerifyConstructionCITests(unittest.TestCase):
    def setUp(self):
        self.original = {"name": "ontokin-reference", "version": "0.4.0", "source_code_sha256": "sha256:old"}
        self.current = {
            "implementation": {**self.original, "source_code_sha256": "sha256:new"},
            "summary": {"total": 20, "passed": 19, "failed": 0, "pending": 1},
            "run_issues": [],
            "cases": [{"id": f"C{n:02}", "status": "passed" if n < 20 else "pending",
                       "pending_reasons": [] if n < 20 else [
                           "The identified independent visual-delivery gate is pending."]}
                      for n in range(1, 21)],
            "external_evidence": {"issues": [IDENTITY_MISMATCH]},
        }
        self.historic = {"status": "passed", "issues": []}

    def test_only_identity_drift_can_be_reported_as_pending(self):
        result = assess(self.current, self.historic, self.original)
        self.assertIn("C20 pending", result["current_gate"])
        self.assertEqual(result["historical_external_gate"], "passed")

    def test_same_implementation_must_pass_complete_gate(self):
        self.current["implementation"] = self.original
        with self.assertRaises(ValueError):
            assess(self.current, self.historic, self.original)
        self.current["cases"][-1]["status"] = "passed"
        self.current["cases"][-1]["pending_reasons"] = []
        self.current["summary"]["passed"] = 20
        self.current["summary"]["pending"] = 0
        self.assertEqual(assess(self.current, self.historic, self.original)["current_gate"], "passed")

    def test_any_nonidentity_external_issue_fails(self):
        self.current["external_evidence"]["issues"].append("GLB hash mismatch")
        with self.assertRaises(ValueError):
            assess(self.current, self.historic, self.original)

    def test_failure_pending_or_corrupted_history_fails(self):
        for changed in ("failed", "pending"):
            with self.subTest(changed=changed):
                candidate = copy.deepcopy(self.current)
                candidate["cases"][5]["status"] = changed
                with self.assertRaises(ValueError):
                    assess(candidate, self.historic, self.original)
        with self.assertRaises(ValueError):
            assess(self.current, {"status": "pending", "issues": [IDENTITY_MISMATCH]}, self.original)

    def test_partial_or_miscounted_gate_fails(self):
        partial = copy.deepcopy(self.current)
        partial["cases"].pop(0)
        with self.assertRaises(ValueError):
            assess(partial, self.historic, self.original)
        partial = copy.deepcopy(self.current)
        partial["summary"]["failed"] = 1
        with self.assertRaises(ValueError):
            assess(partial, self.historic, self.original)


if __name__ == "__main__":
    unittest.main()
