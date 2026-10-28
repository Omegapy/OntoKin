"""Real recording budget and immutable proof-reuse regressions."""
from fractions import Fraction
from pathlib import Path
import json
import math
import unittest
from unittest.mock import patch

from ontokin.bundle import load_file_manifest
from ontokin.construction import compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.gltf import export_glb
from ontokin.json_limits import JSONLimitError, measure_json
from ontokin.reach_conformance import check_complete_inequalities
from ontokin.reach_numeric import ReachExecutionWork
from ontokin.scene import ExportOptions
from test_reach_conformance import algebra_record


ROOT = Path(__file__).resolve().parents[1]


class RecordingBudgetTests(unittest.TestCase):
    def test_real_prefix_and_full_recording_share_the_original_budget(self):
        for end, fps in ((Fraction(1, 4), 60), (Fraction(3), 2)):
            with self.subTest(end=end, fps=fps):
                compiler = compile_construction(load_file_manifest(
                    ROOT / "docs/language-design/planar-reach-v0.1/p01.files.json"))
                with patch("ontokin.reach_export._LocalArithmeticWork",
                           side_effect=AssertionError("recording replenished arithmetic work")):
                    result = export_glb(compiler.model, options=ExportOptions(end=end, fps=fps, helpers=False),
                                        target_contract="ontokin.glb/0.6", work=compiler.reach_work)
                self.assertEqual(result.report["validation"]["status"], "passed")
                self.assertGreater(result.report["validation"]["interval_certificates_checked"], 0)
                self.assertLessEqual(compiler.budget.operations, 100000)
                self.assertEqual(compiler.reach_work.max_operations, 100000)

    def test_warm_algebra_cache_cannot_hide_a_changed_bound(self):
        record, work = algebra_record(), ReachExecutionWork()
        expected = check_complete_inequalities(record, position_tolerance=.001,
                                              rotation_tolerance=.001, work=work)
        self.assertEqual(check_complete_inequalities(dict(record), position_tolerance=.001,
                                                    rotation_tolerance=.001, work=work), expected)
        for name in ("unit_quaternion_difference_bound", "ideal_rotation_bound_rad", "ideal_position_bound_m",
                     "total_rotation_bound_rad", "carrier_position_bound_m", "total_position_bound_m"):
            changed = {**record, name: math.nextafter(record[name], 0.)}
            with self.subTest(quantity=name), self.assertRaises(OntoKinError):
                check_complete_inequalities(changed, position_tolerance=.001,
                                            rotation_tolerance=.001, work=work)


class BoundedSchemaReuseTests(unittest.TestCase):
    def test_cached_schema_retains_exact_bytes_entries_and_repeated_occurrences(self):
        shape = {"field_" + str(index) + "_é": index / 8 for index in range(24)}
        value, work = [dict(shape) for _ in range(48)], ReachExecutionWork()
        expected_bytes = len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode())
        expected_entries = 1 + len(value) * (1 + len(shape))
        result = measure_json(value, check=work.tick, work=work)
        self.assertEqual(result, {"bytes": expected_bytes, "entries": expected_entries})
        self.assertEqual(measure_json(value, max_bytes=expected_bytes, max_entries=expected_entries,
                                      check=work.tick, work=work), result)
        with self.assertRaises(JSONLimitError):
            measure_json(value, max_bytes=expected_bytes - 1, check=work.tick, work=work)
        with self.assertRaises(JSONLimitError):
            measure_json(value, max_entries=expected_entries - 1, check=work.tick, work=work)
        self.assertLessEqual(work.record()["cache_entries"], 256)
        value[-1]["field_0_é"] = float("nan")
        with self.assertRaises(ValueError):
            measure_json(value, check=work.tick, work=work)

    def test_cached_keys_preserve_cancellation_and_value_validation(self):
        stopped = False
        interruption = RuntimeError("original request cancelled")
        def check():
            if stopped:
                raise interruption
        work = ReachExecutionWork(check=check)
        value = {str(index): index for index in range(8)}
        measure_json(value, check=work.tick, work=work)
        stopped = True
        with self.assertRaises(RuntimeError) as caught:
            measure_json(value, check=work.tick, work=work)
        self.assertIs(caught.exception, interruption)
        stopped = False
        value["0"] = "\ud800"
        with self.assertRaises(ValueError):
            measure_json(value, check=work.tick, work=work)
        value["0"] = value
        with self.assertRaises(ValueError):
            measure_json(value, check=work.tick, work=work)


if __name__ == "__main__":
    unittest.main()
