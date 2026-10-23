"""Final after-state allowances are part of every retained endpoint proof."""
from copy import deepcopy
from fractions import Fraction as F
import math
import unittest
from unittest.mock import patch

from ontokin import reach_conformance as reader, reach_export as writer
from ontokin.construction import compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.gltf import export_glb, read_glb
from ontokin.reach_numeric import ReachExecutionWork
from ontokin.scene import ExportOptions
from reach_agent_support import source_case
from test_reach_phase import changed
from test_reach_recurring_endpoint_claims import replace_document


END = F(1, 8)


def completing_spin():
    return changed(source_case("P05"), "0.25[rad/s]), 3[s]);", "0.25[rad/s]), 0.125[s]);")


def record(bundle, *, endpoint_control=False):
    built = compile_construction(bundle)
    options = ExportOptions(end=END, fps=1, helpers=False)
    phase_calls, comparisons = [], []
    phase_bounds, add = writer.recording_phase_bounds, reader._CertificateBatch.add

    def bounds(simulator, start, end, *, recording_proof=False, state=None):
        if endpoint_control and start == end and state is not None:
            return phase_calls[-1][2]
        result = phase_bounds(simulator, start, end, recording_proof=recording_proof, state=state)
        frames = result[0] if recording_proof else result
        phase_calls.append((start, end, frames, state))
        return result

    def compare(batch, row, width, stored_width, minima, magnitude):
        comparisons.append((deepcopy(row), dict(minima)))
        return add(batch, row, width, stored_width, minima, magnitude)

    with patch.object(writer, "recording_phase_bounds", bounds), \
            patch.object(reader._CertificateBatch, "add", compare):
        artifact = export_glb(built.model, options=options,
            target_contract="ontokin.glb/0.6", work=built.reach_work)
    return built, options, artifact, phase_calls, comparisons


class ReachFinalSourceBoundTests(unittest.TestCase):
    def assert_final_coverage(self, outcome):
        built, options, artifact, phase_calls, comparisons = outcome
        self.assertEqual(artifact.report["validation"]["status"], "passed")
        self.assertLessEqual(built.budget.operations, 100000)
        self.assertEqual(built.reach_work.max_operations, 100000)
        self.assertEqual(built.reach_work.max_operand_bits, 32768)
        self.assertEqual(built.reach_work.max_cache_entries, 256)
        self.assertLessEqual(len(built.reach_work._cache), 256)
        point = [call for call in phase_calls if call[0] == call[1]]
        self.assertEqual(len(point), 1)
        self.assertEqual(point[0][:2], (END, END))
        self.assertIsNotNone(point[0][3])
        data = read_glb(artifact.data, target_contract="ontokin.glb/0.6")
        quantization = data.document["extras"]["ontokin"]["reach_quantization"]
        final_key = len(quantization["retained_keys"]) - 1
        final_rows = [row for row in quantization["interval_certificates"] if row["right_key_index"] == final_key]
        self.assertEqual(len(final_rows), len(built.model.objects))
        for row in final_rows:
            bound = point[0][2][row["carrier"]["path"] + ".frame"]
            self.assertGreaterEqual(F(row["source_numeric_position_bound_m"]), bound.position_error_m)
            self.assertGreaterEqual(F(row["source_numeric_rotation_bound_rad"]), bound.rotation_error_rad)
            self.assertEqual(row["source_phase_indices"], [0])
        # These minima are derived by the independent reader from source;
        # neither the producer's final point nor its certificate is an input.
        for row, minima in comparisons:
            for name in ("source_numeric_position_bound_m", "source_numeric_rotation_bound_rad"):
                self.assertGreaterEqual(F(row[name]), minima[name])
        self.assertTrue(comparisons)
        return point[0], final_rows

    def test_natural_root_completion_includes_the_transferred_exposure_error(self):
        outcome = record(completing_spin())
        point, rows = self.assert_final_coverage(outcome)
        prior = outcome[3][0][2]["rig.frame"].rotation_error_rad
        self.assertEqual(point[2]["rig.frame"].rotation_error_rad - prior,
                         F(1, 1 << 50) + F(1, 1 << 91))
        self.assertEqual(point[3].actions["turn"].status, "completed")
        self.assertNotIn(("rig", "orientation"), point[3].claims)
        self.assertGreater(F(rows[0]["source_numeric_rotation_bound_rad"]), prior)

    def test_final_release_selects_the_actual_after_state_source_maxima(self):
        # This tests producer endpoint selection only. The complete short
        # release export has a separately retained, pre-existing independent
        # anchor-enclosure discrepancy; do not turn it into a passing export.
        bundle = changed(source_case("P16"), "at 2[s] sequence", "at 0.125[s] sequence")
        built = compile_construction(bundle)
        captured, points = {}, []
        original, phase_bounds = writer.interval_certificates, writer.recording_phase_bounds

        class ProducerCertificatesComplete(Exception):
            pass

        def bounds(simulator, start, end, *, recording_proof=False, state=None):
            result = phase_bounds(simulator, start, end, recording_proof=recording_proof, state=state)
            if start == end:
                points.append((start, end, result, state))
            return result

        def certificates(model, options, plan, *args, **kwargs):
            captured["plan"] = plan
            captured["rows"] = original(model, options, plan, *args, **kwargs)
            raise ProducerCertificatesComplete

        with patch.object(writer, "interval_certificates", certificates), \
                patch.object(writer, "recording_phase_bounds", bounds):
            with self.assertRaises(ProducerCertificatesComplete):
                export_glb(built.model, options=ExportOptions(end=END, fps=1, helpers=False),
                           target_contract="ontokin.glb/0.6", work=built.reach_work)
        self.assertEqual(len(points), 1)
        point, plan, rows = points[0], captured["plan"], captured["rows"]
        self.assertEqual(point[:2], (END, END))
        self.assertIs(point[3], plan.final_state)
        self.assertIn("payload", point[3].dynamic)
        self.assertEqual(point[3].dynamic["payload"].time, END)
        self.assertGreater(point[2]["payload.frame"].anchor_position_error_m, 0)
        self.assertGreater(point[2]["payload.frame"].anchor_rotation_error_rad, 0)
        self.assertEqual(len(plan.phases), 1)
        last = max(row["right_key_index"] for row in rows)
        final_rows = [row for row in rows if row["right_key_index"] == last]
        self.assertEqual(len(final_rows), len(built.model.objects))
        for row in final_rows:
            frame = row["carrier"]["path"] + ".frame"
            self.assertEqual(row["source_phase_indices"], [0])
            for quantity, field in (("source_numeric_position_bound_m", "position_error_m"),
                                    ("source_numeric_rotation_bound_rad", "rotation_error_rad")):
                expected = max(getattr(plan.phases[0].source[frame], field), getattr(point[2][frame], field))
                self.assertGreaterEqual(F(row[quantity]), expected)
                self.assertLess(F(math.nextafter(row[quantity], -math.inf)), expected)

    def test_final_authored_stop_uses_after_state_without_an_extra_motion_phase(self):
        bundle = changed(source_case("P05"),
            "at 0[s] sequence { start travel; start turn; start reach; }",
            "at 0[s] sequence { start travel; start turn; start reach; }\n"
            "    at 0.125[s] sequence { stop turn; stop travel; }")
        point, _ = self.assert_final_coverage(record(bundle))
        self.assertEqual(point[3].actions["turn"].status, "stopped")
        self.assertEqual(point[3].actions["travel"].status, "stopped")
        self.assertNotIn(("rig", "orientation"), point[3].claims)
        self.assertNotIn(("rig", "translation"), point[3].claims)

    def test_an_unchanged_endpoint_keeps_the_preceding_complete_artifact_bytes(self):
        expected = record(source_case("P01"), endpoint_control=True)
        actual = record(source_case("P01"))
        self.assert_final_coverage(actual)
        self.assertEqual(actual[2].data, expected[2].data)

    def test_final_bounds_read_the_retained_state_even_if_the_live_state_differs(self):
        built = compile_construction(completing_spin())
        plan = writer.reach_prefix_plan(built.model, END, work=built.reach_work)
        simulator, final_state = plan.simulator, deepcopy(plan.final_state)
        simulator.state = deepcopy(plan.phase_states[0])
        live = deepcopy(simulator.state)
        actual = writer.recording_phase_bounds(simulator, END, END, state=final_state)
        self.assertEqual(final_state, plan.final_state)
        self.assertEqual(simulator.state, live)
        self.assertEqual(actual["rig.frame"].anchor_rotation_error_rad,
                         final_state.root_rotation_errors["rig"])
        self.assertGreater(actual["rig.frame"].anchor_rotation_error_rad,
                           simulator.state.root_rotation_errors.get("rig", F(0)))
        # The selected endpoint proof still excludes unrelated source sites.
        complete = simulator.phase_bounds(END, END, final_state)["frames"]
        self.assertLess(len(actual), len(complete))
        self.assertEqual(actual, {path: complete[path] for path in actual})

    def test_final_point_work_preserves_cancellation_and_live_operand_limits(self):
        for cancel in (False, True):
            built = compile_construction(completing_spin())
            original, entered = writer.recording_phase_bounds, []
            marker = RuntimeError("cancel required final point proof")

            def interrupt(simulator, start, end, *, recording_proof=False, state=None):
                if start == end and state is not None:
                    entered.append(True)
                    def check():
                        if cancel:
                            raise marker
                        simulator.work.max_operand_bits = 128
                    simulator.work.external_check = check
                return original(simulator, start, end, recording_proof=recording_proof, state=state)

            with self.subTest(cancel=cancel), patch.object(writer, "recording_phase_bounds", interrupt):
                with self.assertRaises(RuntimeError if cancel else OntoKinError) as caught:
                    export_glb(built.model, options=ExportOptions(end=END, fps=1, helpers=False),
                               target_contract="ontokin.glb/0.6", work=built.reach_work)
            self.assertEqual(entered, [True])
            if cancel:
                self.assertIs(caught.exception, marker)
                self.assertIs(built.reach_work.callback_error, marker)
            else:
                self.assertEqual(caught.exception.diagnostic.details["budget"], "numeric_operand_bits")
                self.assertEqual(caught.exception.diagnostic.details["limit"], 128)

    def test_independent_reader_rejects_both_understated_final_allowances(self):
        outcome = record(completing_spin())
        self.assert_final_coverage(outcome)
        built, options, artifact, _, comparisons = outcome
        decoded = read_glb(artifact.data, target_contract="ontokin.glb/0.6")
        for quantity in ("source_numeric_position_bound_m", "source_numeric_rotation_bound_rad"):
            row, minima = max(comparisons, key=lambda value: value[0]["right_key_index"])
            if quantity == "source_numeric_position_bound_m":
                row, minima = next((record, minimum) for record, minimum in comparisons
                    if record["right_key_index"] == row["right_key_index"] and record["carrier"]["path"] == "rig.tool")
            document = deepcopy(decoded.document)
            rows = document["extras"]["ontokin"]["reach_quantization"]["interval_certificates"]
            forged = next(value for value in rows if value["carrier"] == row["carrier"]
                          and value["left_key_index"] == row["left_key_index"])
            minimum = minima[quantity]
            forged[quantity] = math.nextafter(float(minimum), 0.)
            self.assertLess(F(forged[quantity]), minimum)
            changed_bytes = replace_document(document, decoded.binary)
            work = ReachExecutionWork()
            with self.subTest(quantity=quantity), self.assertRaises(OntoKinError) as caught:
                reader.validate_reach_export(changed_bytes, built.model, options=options, work=work)
            self.assertEqual(caught.exception.diagnostic.details["export_code"], "OKE-E-CERTIFICATE")
            self.assertEqual(caught.exception.diagnostic.details["quantity"], quantity)
            self.assertLessEqual(work.operations, 100000)


if __name__ == "__main__":
    unittest.main()
