"""Independent binding of the recording algorithm and its numerical proof."""
import hashlib
from pathlib import Path
import unittest
from unittest.mock import patch

from ontokin.diagnostics import OntoKinError
from ontokin import reach_conformance
from ontokin.reach_numeric import ReachExecutionWork
from tools import reach_source_rates


ROOT = Path(__file__).resolve().parents[1]
SOURCE_INPUTS = (
    "ontokin/reach_numeric.py", "ontokin/reach_kinematics.py",
    "ontokin/reach_pose.py", "ontokin/reach_phase.py",
    "ontokin/reach_runtime.py", "ontokin/reach_export.py",
    "ontokin/reach_recording_fast.py",
)
DERIVATION_INPUTS = (
    "docs/engineering/reach-numeric-kernel.md",
    "docs/engineering/reach-source-kernel.md",
    "docs/engineering/reach-coaxial-phase-bounds.md",
    "docs/engineering/reach-carrier-rotation-cursors.md",
    "docs/engineering/reach-recording-certified-planar.md",
)


def sha(name):
    return hashlib.sha256((ROOT / name).read_bytes()).hexdigest()


def aggregate(names):
    content = "".join(name + "\0" + sha(name) + "\n" for name in names)
    return "sha256:" + hashlib.sha256(content.encode("ascii")).hexdigest()


def current_basis():
    # Expected source identity is assembled from the literal reviewed closure,
    # independently of the production writer's source_numeric_basis helper.
    return {
        "source_numeric_bound_basis": {
            "name": "OntoKin controlled source poses", "version": "0.2",
            "implementation_sha256": aggregate(SOURCE_INPUTS),
            "method": "ontokin.source-pose-projective-dyadic/0.2",
            "derivation_sha256": aggregate(DERIVATION_INPUTS),
        },
        "destination_numeric_bound_basis": {
            "name": "ontokin-controlled-three-recording", "version": "0.1.0",
            "implementation_sha256": "sha256:" + sha("tools/reach_destination.mjs"),
            "derivation_sha256": "sha256:" + sha("docs/engineering/reach-destination-numerics.md"),
            "method": reach_conformance.DESTINATION_METHOD,
        },
    }


class ReachRecordingBasisTests(unittest.TestCase):
    def reject_source(self, value):
        with self.assertRaises(OntoKinError) as caught:
            reach_conformance.verify_numeric_bases(value, work=ReachExecutionWork())
        self.assertEqual(caught.exception.diagnostic.details["export_code"],
                         "OKE-E-SOURCE-NUMERIC-BASIS")

    def test_versioned_basis_identifies_the_complete_recording_implementation(self):
        work = ReachExecutionWork()
        reach_conformance.verify_numeric_bases(current_basis(), work=work)
        self.assertEqual(work.counts["independent_basis_open"], 14)
        self.assertEqual(work.max_operations, 100000)
        self.assertLessEqual(work.operations, 100000)

    def test_old_method_version_or_unidentified_name_cannot_relabel_current_bytes(self):
        for key, value in (("version", "0.1"),
                           ("method", "ontokin.source-pose-projective-dyadic/0.1"),
                           ("name", "unidentified source poses")):
            with self.subTest(field=key):
                basis = current_basis()
                basis["source_numeric_bound_basis"][key] = value
                self.reject_source(basis)

    def test_old_five_file_hash_cannot_omit_recording_endpoint_certification(self):
        basis = current_basis()
        basis["source_numeric_bound_basis"]["implementation_sha256"] = aggregate(SOURCE_INPUTS[:-1])
        self.reject_source(basis)

    def test_changed_exporter_bytes_invalidate_an_otherwise_current_basis(self):
        basis = current_basis()
        original = reach_conformance._identified_digest
        changed = hashlib.sha256((ROOT / "ontokin/reach_export.py").read_bytes() + b"\n").hexdigest()
        def read(path, *, work):
            actual = original(path, work=work)
            return changed if path == ROOT / "ontokin/reach_export.py" else actual
        with patch.object(reach_conformance, "_identified_digest", side_effect=read):
            self.reject_source(basis)

    def test_rate_fingerprints_use_the_same_complete_exact_source_inputs(self):
        work = ReachExecutionWork()
        groups = reach_source_rates._fingerprints(reach_source_rates._Exact(work))
        source = groups["source_numeric_implementation"]
        self.assertEqual(tuple(row["path"] for row in source["inputs"]), SOURCE_INPUTS)
        self.assertEqual(source["sha256"], aggregate(SOURCE_INPUTS))
        for row in source["inputs"]:
            self.assertEqual(row["sha256"], "sha256:" + sha(row["path"]))
            self.assertEqual(row["bytes"], (ROOT / row["path"]).stat().st_size)
        self.assertLessEqual(work.operations, 100000)

    def test_new_exporter_identity_read_preserves_the_current_cancellation(self):
        marker = RuntimeError("cancel at the recording implementation input")
        work = ReachExecutionWork()
        def cancel():
            if work.counts.get("independent_basis_open", 0) == 6:
                raise marker
        work.external_check = cancel
        with self.assertRaises(RuntimeError) as caught:
            reach_conformance.verify_numeric_bases(current_basis(), work=work)
        self.assertIs(caught.exception, marker)
        self.assertIs(work.callback_error, marker)


if __name__ == "__main__":
    unittest.main()
