"""Actual recorded endpoints retain independent stored-to-ideal obligations."""
from copy import deepcopy
from fractions import Fraction as F
import json
import math
import struct
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.gltf import export_glb, read_glb
from ontokin import reach_conformance
from ontokin.reach_numeric import ReachExecutionWork
from ontokin.scene import ExportOptions
from reach_agent_support import source_case


def replace_document(document, binary):
    encoded = json.dumps(document, ensure_ascii=False, separators=(",", ":"),
                         allow_nan=False).encode("utf-8")
    encoded += b" " * (-len(encoded) % 4)
    return (struct.pack("<III", 0x46546c67, 2, 28 + len(encoded) + len(binary))
            + struct.pack("<II", len(encoded), 0x4e4f534a) + encoded
            + struct.pack("<II", len(binary), 0x004e4942) + binary)


class ReachRecurringEndpointClaimTests(unittest.TestCase):
    def test_actual_recurrence_cannot_understate_independently_measured_endpoint_errors(self):
        built = compile_construction(source_case("P01"))
        options = ExportOptions(end=F(1, 4), fps=60, helpers=False)
        observed = []
        add = reach_conformance._CertificateBatch.add
        def observe(batch, record, width, stored_width, minima, magnitude):
            # The reader supplies these direct interval-reference measurements.
            # No producer endpoint bound is used as an expected value.
            observed.append((deepcopy(record), dict(minima)))
            return add(batch, record, width, stored_width, minima, magnitude)
        with patch.object(reach_conformance._CertificateBatch, "add", observe):
            result = export_glb(built.model, options=options,
                                target_contract="ontokin.glb/0.6", work=built.reach_work)
        self.assertEqual(result.report["validation"]["status"], "passed")
        self.assertGreater(built.reach_work.counts.get("recording_rotation_step", 0), 0)
        self.assertLessEqual(built.reach_work.operations, 100000)
        self.assertEqual(built.reach_work.max_operations, 100000)
        decoded = read_glb(result.data, target_contract="ontokin.glb/0.6")
        source = decoded.document["extras"]["ontokin"]["reach_quantization"]["source_numeric_bound_basis"]
        self.assertEqual(source["version"], "0.2")
        self.assertEqual(source["method"], "ontokin.source-pose-projective-dyadic/0.2")
        for quantity in ("max_endpoint_position_error_m", "max_endpoint_unit_quaternion_error"):
            with self.subTest(quantity=quantity):
                candidates = [(record, minima[quantity]) for record, minima in observed
                              if record["left_key_index"] > 0 and minima[quantity] > 0]
                self.assertTrue(candidates)
                original, minimum = max(candidates, key=lambda pair: pair[1])
                self.assertGreaterEqual(F(original[quantity]), minimum)
                document = deepcopy(decoded.document)
                certificates = document["extras"]["ontokin"]["reach_quantization"]["interval_certificates"]
                selected = [record for record in certificates
                            if record["left_key_index"] == original["left_key_index"]
                            and record["carrier"] == original["carrier"]]
                self.assertEqual(len(selected), 1)
                lower = math.nextafter(float(minimum), 0.)
                self.assertGreaterEqual(lower, 0.)
                self.assertLess(F(lower), minimum)
                selected[0][quantity] = lower
                changed = replace_document(document, decoded.binary)
                # All geometry and stored pose buffers stay exactly unchanged;
                # only one claimed endpoint error was made insufficient.
                self.assertEqual(read_glb(changed, target_contract="ontokin.glb/0.6").binary,
                                 decoded.binary)
                work = ReachExecutionWork()
                with self.assertRaises(OntoKinError) as caught:
                    reach_conformance.validate_reach_export(changed, built.model,
                                                           options=options, work=work)
                self.assertEqual(caught.exception.diagnostic.details["export_code"], "OKE-E-CERTIFICATE")
                self.assertEqual(caught.exception.diagnostic.details["quantity"], quantity)
                self.assertLessEqual(work.operations, 100000)


if __name__ == "__main__":
    unittest.main()
