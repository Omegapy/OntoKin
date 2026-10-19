"""Source-defined GLB/0.5 acceptance, independent playback, and hostile bytes.

The frozen corpus supplies numerical expectations. The test decoder does not
call the production reader or sampler; mutations retain otherwise valid GLB
structure so source-history and interpolation checks must detect the damage.
No Agent store, SQLite database, or destination application is used here.
"""

import copy
from fractions import Fraction
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import unittest
from unittest.mock import patch

from ontokin.bundle import ProgramBundle, SourceUnit, load_file_manifest
from ontokin.construction import compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.evaluator import _records_per_sample, evaluate
from ontokin import force_runtime, gltf, scene
from ontokin.gltf import _encode, export_glb, validate_export
from ontokin.json_limits import measure_json
from ontokin.scene import ExportOptions, build_scene
from tests.test_export import DecodedGLB, encode_glb
from tests.test_surface_export import change_accessor, mesh_content


FIXTURES = Path(__file__).resolve().parents[1] / "docs/language-design/force-v0.1"
CASES = {case["id"]: case for case in json.loads((FIXTURES / "acceptance.json").read_text())["source_cases"]}
SUPPLEMENTS = {case["id"]: case for case in json.loads((FIXTURES / "reviewed-acceptance.json").read_text())["source_cases"]}
ERRATA = json.loads((FIXTURES / "source-errata.json").read_text())
CONTRACT = "ontokin.glb/0.5"
REQUIRED_CASES = tuple(f"P{index:02d}" for index in range(1, 18)) + ("P21", "P22")


def rational(value):
    return Fraction(int(value["numerator"]), int(value["denominator"]))


def expected_samples(case_id):
    """Apply adopted additive sample corrections with their old-value guard."""
    samples = copy.deepcopy(CASES[case_id]["expected_samples"])
    for correction in ERRATA["sample_corrections"]:
        if correction["id"] != case_id:
            continue
        matches = [sample for sample in samples
                   if sample["target"] == correction["target"] and sample["side"] == correction["side"]
                   and rational(sample["time"]) == rational(correction["time"])]
        if len(matches) != 1 or {key: matches[0][key] for key in correction["old"]} != correction["old"]:
            raise AssertionError("The adopted source-sample erratum's original-value precondition changed")
        matches[0].update(copy.deepcopy(correction["new"]))
    return samples


def compile_case(case_id):
    case = (CASES | SUPPLEMENTS)[case_id]
    bundle = load_file_manifest(FIXTURES / case["file_manifest"])
    # Full evaluation would incorrectly reject P21 before its requested prefix
    # reaches the exporter. Source construction is the adapter's input level.
    return bundle, compile_construction(bundle, level="constructed").model


def changed_case(case_id, transform):
    bundle, _ = compile_case(case_id)
    text = transform(bundle.entry.text)
    if text == bundle.entry.text:
        raise AssertionError("The test's explicit source edit did not change bytes")
    changed = ProgramBundle(SourceUnit("entry", bundle.entry.filename, text.encode()), bundle.modules)
    return changed, compile_construction(changed, level="constructed").model


def add_scene_events(text, events):
    before, closing = text.rsplit("}", 1)
    return before + events + "}\n" + closing


@lru_cache(maxsize=None)
def delivered_case(case_id):
    bundle, model = compile_case(case_id)
    # P09 includes prescribed offset rotation before release; its successful
    # corpus recording uses the default 60 FPS for that inherited trajectory.
    # The other cases keep low FPS to exercise free-sphere force refinement.
    options = ExportOptions(helpers=False, fps=60 if case_id == "P09" else 1,
                            end=rational(CASES[case_id]["request_horizon"]))
    result = export_glb(model, target_contract=CONTRACT, options=options)
    return bundle, model, options, result, DecodedGLB(result.data)


def metadata(decoded):
    return decoded.document["extras"]["ontokin"]


def aliased_accessors(decoded, rows, copies):
    """Small binary storage with independently declared overlapping accessors."""
    document, binary = copy.deepcopy(decoded.document), bytearray(decoded.binary)
    binary.extend(b"\0" * (-len(binary) % 4))
    view = len(document["bufferViews"])
    document["bufferViews"].append({"buffer": 0, "byteOffset": len(binary), "byteLength": 4 * rows})
    binary.extend(b"\0" * (4 * rows))
    document["buffers"][0]["byteLength"] = len(binary)
    for _ in range(copies):
        document["accessors"].append({"bufferView": view, "count": rows,
                                      "componentType": 5126, "type": "SCALAR"})
    return document, binary


def quaternion_error(actual, expected_wxyz):
    expected = (expected_wxyz[1], expected_wxyz[2], expected_wxyz[3], expected_wxyz[0])
    actual = tuple(value / math.hypot(*actual) for value in actual)
    expected = tuple(value / math.hypot(*expected) for value in expected)
    chord = min(math.hypot(*(a - sign * b for a, b in zip(actual, expected))) for sign in (-1, 1))
    return 4 * math.asin(min(1, chord / 2))


def p01_position(seconds):
    """Frozen P01: a=2 during [1,2], followed by velocity 2 m/s."""
    if seconds <= 1:
        return (0., 0., 0.)
    return (((seconds - 1) ** 2 if seconds <= 2 else 1 + 2 * (seconds - 2)), 0., 0.)


class ForceExportTests(unittest.TestCase):
    def assertPose(self, decoded, path, seconds, position, orientation=(1, 0, 0, 0), *, tolerance=.001):
        pose = decoded.node_pose(path, float(seconds))
        self.assertLessEqual(max(abs(a - b) for a, b in zip(pose["translation"], position)), tolerance)
        self.assertLessEqual(quaternion_error(pose["rotation"], orientation), .001)

    def assertInvalid(self, data, model, *, options=None):
        try:
            report = validate_export(data, model, target_contract=CONTRACT, options=options)
        except OntoKinError as error:
            self.assertEqual(error.diagnostic.details["target_contract"], CONTRACT)
            return error
        self.assertEqual(report["status"], "failed", "Source-invalid bytes were accepted")
        return report

    def test_required_frozen_source_cases_deliver_predetermined_poses(self):
        for case_id in REQUIRED_CASES:
            with self.subTest(case=case_id):
                bundle, model, options, result, decoded = delivered_case(case_id)
                self.assertEqual(result.report["outcome"], "valid")
                self.assertEqual(result.report["target_contract"], CONTRACT)
                self.assertEqual(result.report["schema_version"], "ontokin.glb-report/0.5")
                self.assertEqual(result.report["program_revision"], CASES[case_id]["program_revision"])
                self.assertEqual(result.report["program"]["manifest"], bundle.manifest())
                self.assertEqual(result.report["artifact"]["sha256"], "sha256:" + hashlib.sha256(result.data).hexdigest())
                self.assertEqual(metadata(decoded)["profile"], "force-0.1")
                self.assertEqual(result.report["geometry"]["surface_profile"]["name"], "surface-0.1")
                self.assertEqual(metadata(decoded)["transform_policy"], "all_nodes_are_roots_with_baked_world_poses")
                self.assertTrue(all(not node.get("children") for node in decoded.document["nodes"]))
                for sample in expected_samples(case_id):
                    self.assertPose(decoded, sample["target"], rational(sample["time"]),
                                    sample["position_m"], sample["orientation_wxyz"])

    def test_every_boundary_retains_complete_fresh_force_and_impulse_projections(self):
        for case_id in ("P02", "P07", "P09", "P10", "P16", "P17"):
            with self.subTest(case=case_id):
                bundle, model, _, _, decoded = delivered_case(case_id)
                records = metadata(decoded)["boundary_states"]
                states = evaluate(model, [row["source_seconds"] for row in records])["samples"]
                for row, sample in zip(records, states):
                    self.assertEqual(row["force_states_after"], {path: obj["forces"] for path, obj in sample["objects"].items()})
                    self.assertEqual(row["impulse_states_after"], {path: obj["impulses"] for path, obj in sample["objects"].items()})
                    self.assertEqual(row["pose_authorities_after"], {path: obj["pose_authority"] for path, obj in sample["objects"].items()})
                    for history in row["force_states_after"].values():
                        for record in history["active"] + history["last_changes"]:
                            span = record["source_location"]
                            self.assertEqual(span["source_id"], "entry")
                            actual_text = bundle.entry.raw[span["start_byte"]:span["end_byte"]].decode()
                            self.assertIn(actual_text, [statement["text"] for statement in CASES[case_id]["force_statements"]])
                            self.assertEqual(record["program_revision"], bundle.program_revision)

    def test_zero_and_replacement_forces_preserve_mode_origin_and_trajectory_anchors(self):
        for case_id in ("P03", "P04", "P05", "P06"):
            with self.subTest(case=case_id):
                *_, decoded = delivered_case(case_id)
                rows = {Fraction(row["source_seconds"]): row for row in metadata(decoded)["boundary_states"]}
                for sample in CASES[case_id]["expected_samples"]:
                    seconds = rational(sample["time"])
                    if sample["side"] != "after" or seconds not in rows:
                        continue
                    authority = rows[seconds]["pose_authorities_after"][sample["target"]]
                    self.assertEqual(Fraction(authority["since_seconds"]), rational(sample["dynamic_since"]))
                    self.assertEqual(Fraction(authority["trajectory_anchor_seconds"]), rational(sample["anchor_time"]))
                    force = rows[seconds]["force_states_after"][sample["target"]]
                    self.assertEqual(force["net_force_world_n"], sample["net_force_world_n"])
                    self.assertEqual(force["acceleration_world_m_per_s2"], sample["acceleration_world_m_s2"])
                    self.assertEqual((force["started_count"], force["completed_count"]),
                                     (sample["started_count"], sample["completed_count"]))

    def test_nondecimal_completion_and_source_clocks_are_not_replaced_by_point_three(self):
        *_, result, decoded = delivered_case("P16")
        activation, duration = Fraction.from_float(.1), Fraction.from_float(.2)
        completion = activation + duration
        frozen = next(sample for sample in CASES["P16"]["expected_samples"] if "push" in sample["active_ends"])
        self.assertEqual(activation, rational(frozen["last_boundary"]))
        self.assertEqual(completion, rational(frozen["active_ends"]["push"]))
        self.assertNotEqual(activation, Fraction(1, 10))
        self.assertNotEqual(completion, Fraction(3, 10))
        self.assertNotEqual(completion, Fraction.from_float(.3))
        boundaries = {Fraction(value) for value in result.report["sampling"]["boundary_times_seconds"]}
        authored = {Fraction(value) for value in decoded.document["animations"][0]["extras"]["ontokin"]["exact_times_seconds"]}
        self.assertIn(completion, boundaries)
        self.assertIn(completion, authored)
        row = next(row for row in metadata(decoded)["boundary_states"] if Fraction(row["source_seconds"]) == activation)
        force = row["force_states_after"]["ball"]["active"][0]
        self.assertEqual(Fraction(force["activation_time_seconds"]), activation)
        self.assertEqual(Fraction(force["duration_seconds"]), duration)
        self.assertEqual(Fraction(force["completion_time_seconds"]), completion)

    def test_prescribed_offset_motion_at_insufficient_fps_fails_measured_tolerance(self):
        _, model = compile_case("P09")
        options = ExportOptions(helpers=False, fps=1)
        with self.assertRaises(OntoKinError) as caught:
            export_glb(model, target_contract=CONTRACT, options=options)
        self.assertEqual(caught.exception.diagnostic.details["export_code"], "OKE-E-ANIMATION-PRECISION")
        validation = caught.exception.diagnostic.details["validation"]
        self.assertEqual(validation["status"], "failed")
        self.assertGreater(validation["max_position_error_m"], options.position_tolerance_m)
        self.assertEqual(validation["worst_position"]["node"], "ball")
        self.assertLess(Fraction(validation["worst_position"]["time_seconds"]), 1)

    def test_force_ending_after_requested_prefix_retains_its_original_completion(self):
        _, model = compile_case("P17")
        result = export_glb(model, target_contract=CONTRACT, options=ExportOptions(helpers=False, fps=1, end="1.5"))
        decoded = DecodedGLB(result.data)
        rows = metadata(decoded)["boundary_states"]
        self.assertEqual([Fraction(row["source_seconds"]) for row in rows], [Fraction(0), Fraction(1), Fraction(3, 2)])
        force = rows[-1]["force_states_after"]["ball"]
        self.assertEqual(force["completed_count"], 0)
        self.assertEqual(force["active"][0]["completion_time_seconds"], "6")
        self.assertPose(decoded, "ball", Fraction(3, 2), (.25, 0, 0))

    def test_valid_short_prefix_does_not_simulate_later_force_failure(self):
        _, model = compile_case("P21")
        options = ExportOptions(helpers=False, fps=1, end="1")
        for callback in (None, lambda: None):
            with self.subTest(callback=callback is not None):
                result = export_glb(model, target_contract=CONTRACT, options=options, check=callback)
                self.assertEqual(validate_export(result.data, model, target_contract=CONTRACT, options=options,
                                                 check=callback)["status"], "passed")
                self.assertPose(DecodedGLB(result.data), "ball", 1, (1, 0, 0))
        with self.assertRaises(OntoKinError) as caught:
            export_glb(model, target_contract=CONTRACT, options=ExportOptions(end="2", helpers=False))
        self.assertEqual(caught.exception.code, "OKL-E-NUMERIC")

    def test_future_huge_impulse_does_not_inflate_prefix_sampling(self):
        _, model = changed_case("P07", lambda text: text.replace("at 1[s] sequence", "at 2[s] sequence")
                                .replace("2[N*s]", "1e200[N*s]"))
        options = ExportOptions(helpers=False, fps=1, end="1")
        result = export_glb(model, target_contract=CONTRACT, options=options)
        decoded = DecodedGLB(result.data)
        self.assertLess(len(decoded.animation_times()), 100)
        for i in range(17):
            seconds = i / 16
            self.assertPose(decoded, "ball", seconds, (seconds * seconds, 0, 0))
        self.assertTrue(all(not row["impulse_states_after"]["ball"]["last_applications"]
                            for row in metadata(decoded)["boundary_states"]))

    def test_acceleration_refines_low_fps_by_the_quarter_tolerance_chord_bound(self):
        _, _, options, _, decoded = delivered_case("P01")
        animation = decoded.document["animations"][0]
        authored = [Fraction(value) for value in animation["extras"]["ontokin"]["exact_times_seconds"]]
        stored = sorted(decoded.animation_times())
        self.assertGreater(len(stored), 30)
        for clocks in (authored, [Fraction(value) for value in stored]):
            for first, last in zip(clocks, clocks[1:]):
                if 1 <= first < last <= 2:
                    self.assertLessEqual(Fraction(2) * (last - first) ** 2 / 8,
                                         Fraction(options.position_tolerance_m) / 4)
        for first, last in zip(stored, stored[1:]):
            for fraction in (.25, .5, .75):
                seconds = first + fraction * (last - first)
                self.assertPose(decoded, "ball", seconds, p01_position(seconds))

    def test_coarsened_track_below_full_tolerance_still_violates_chord_allocation(self):
        _, model, options, _, decoded = delivered_case("P01")
        document, binary = copy.deepcopy(decoded.document), bytearray(decoded.binary)
        exact = ["0", "1"] + [f"{1 + index / 20:.2f}" for index in range(1, 21)] + ["3"]
        seconds = [float(value) for value in exact]
        animation = document["animations"][0]
        clock = animation["samplers"][0]["input"]
        for row, value in enumerate(seconds):
            change_accessor(binary, document, clock, row, [value])
        document["accessors"][clock].update(count=len(seconds), min=[0.], max=[3.])
        for channel in animation["channels"]:
            output = animation["samplers"][channel["sampler"]]["output"]
            for row, value in enumerate(seconds):
                pose = p01_position(value) if channel["target"]["path"] == "translation" else (0, 0, 0, 1)
                change_accessor(binary, document, output, row, pose)
            document["accessors"][output]["count"] = len(seconds)
        animation["extras"]["ontokin"]["exact_times_seconds"] = exact
        mutated = encode_glb(document, binary)
        independent = DecodedGLB(mutated)
        # Each chord is wrong by at most 0.000625 m, strictly inside 0.001 m.
        # A reader that checks finite poses but omits the quarter allocation
        # would accept this artifact, despite the adopted recording contract.
        for first, last in zip(seconds, seconds[1:]):
            for fraction in (.25, .5, .75):
                value = first + fraction * (last - first)
                self.assertPose(independent, "ball", value, p01_position(value))
        self.assertInvalid(mutated, model, options=options)

    def test_huge_opposite_forces_use_canonical_net_acceleration(self):
        _, model = changed_case("P03", lambda text: text.replace("4[N]", "1e308[N]"))
        result = export_glb(model, target_contract=CONTRACT, options=ExportOptions(helpers=False, fps=1))
        decoded = DecodedGLB(result.data)
        self.assertLess(len(decoded.animation_times()), 20)
        for row in metadata(decoded)["boundary_states"]:
            self.assertEqual(row["force_states_after"]["ball"]["acceleration_world_m_per_s2"], [0, 0, 0])
        for sample in CASES["P03"]["expected_samples"]:
            self.assertPose(decoded, sample["target"], rational(sample["time"]), sample["position_m"], sample["orientation_wxyz"])

    def test_generated_mass_force_and_duration_edits_preserve_sibling_mesh_and_pbr(self):
        variants = [delivered_case(case_id) for case_id in ("P10", "P11", "P12", "P13")]
        initial_bundle, _, _, _, initial = variants[0]
        for path in ('rack.props["first"]', 'rack.props["second"]'):
            expected = mesh_content(initial, path)
            for bundle, _, _, _, decoded in variants[1:]:
                self.assertEqual(mesh_content(decoded, path), expected)
                self.assertEqual(bundle.modules, initial_bundle.modules)
        for _, _, _, _, decoded in variants[1:]:
            for sample in CASES["P10"]["expected_samples"]:
                if sample["target"] == 'rack.props["second"]':
                    self.assertPose(decoded, sample["target"], rational(sample["time"]),
                                    sample["position_m"], sample["orientation_wxyz"])
            self.assertNotEqual(decoded.node_pose('rack.props["first"]', 3),
                                initial.node_pose('rack.props["first"]', 3))

    def test_force_profile_discloses_recorded_com_world_forces_and_no_contacts_or_torque(self):
        _, model, _, _, decoded = delivered_case("P01")
        profile = metadata(decoded)["force_profile"]
        self.assertEqual(profile["name"], "force-0.1")
        self.assertEqual(profile["continuous_external_torques"], "absent")
        self.assertEqual(profile["contacts"], "disabled")
        self.assertIn("world", profile["source_forces"])
        self.assertTrue("center_of_mass" in profile["source_forces"] or "com" in profile["source_forces"])
        self.assertIn("recorded", profile["destination_behavior"])
        document = copy.deepcopy(decoded.document)
        document["extras"]["ontokin"]["force_profile"]["contacts"] = "enabled"
        self.assertInvalid(encode_glb(document, decoded.binary), model)

    def test_missing_or_forged_complete_force_history_is_rejected(self):
        _, model, _, _, decoded = delivered_case("P02")
        modes = ("missing", "empty-active", "source", "span", "target", "identity", "sequence", "activation",
                 "duration", "completion", "net-force", "acceleration", "started-count", "completed-count", "changes")
        for mode in modes:
            with self.subTest(mode=mode):
                document = copy.deepcopy(decoded.document)
                row = next(row for row in document["extras"]["ontokin"]["boundary_states"] if row["source_seconds"] == "1")
                history = row["force_states_after"]["ball"]
                active = history["active"][0]
                if mode == "missing": del row["force_states_after"]
                elif mode == "empty-active": history["active"] = []
                elif mode == "source": active["source_location"]["source_revision"] = "sha256:" + "0" * 64
                elif mode == "span": active["source_location"]["start_byte"] += 1
                elif mode == "target": active["target_element_id"][-1] = "not-ball"
                elif mode == "identity": active["force_element_id"][-1] = "not-a"
                elif mode == "sequence": active["sequence_index"] += 1
                elif mode == "activation": active["activation_time_seconds"] = "0.5"
                elif mode == "duration": active["duration_seconds"] = "3"
                elif mode == "completion": active["completion_time_seconds"] = "3"
                elif mode == "net-force": history["net_force_world_n"][0] = 0
                elif mode == "acceleration": history["acceleration_world_m_per_s2"][0] = 0
                elif mode == "started-count": history["started_count"] = 0
                elif mode == "completed-count": history["completed_count"] = 1
                else: history["last_changes"] = []
                self.assertInvalid(encode_glb(document, decoded.binary), model)

    def test_empty_object_force_projection_cannot_be_omitted(self):
        _, model, _, _, decoded = delivered_case("P10")
        document = copy.deepcopy(decoded.document)
        row = document["extras"]["ontokin"]["boundary_states"][0]
        self.assertEqual(row["force_states_after"]["rack"]["active"], [])
        del row["force_states_after"]["rack"]
        self.assertInvalid(encode_glb(document, decoded.binary), model)

    def test_impulse_history_remains_required_in_force_delivery(self):
        _, model, _, _, decoded = delivered_case("P07")
        document = copy.deepcopy(decoded.document)
        row = next(row for row in document["extras"]["ontokin"]["boundary_states"] if row["source_seconds"] == "1")
        self.assertTrue(row["impulse_states_after"]["ball"]["last_applications"])
        row["impulse_states_after"]["ball"]["last_applications"] = []
        self.assertInvalid(encode_glb(document, decoded.binary), model)

    def test_corrupted_serialized_position_is_detected_against_source(self):
        _, model, _, _, decoded = delivered_case("P01")
        document, binary = copy.deepcopy(decoded.document), bytearray(decoded.binary)
        index, _ = decoded.source_node("ball")
        animation = document["animations"][0]
        channel = next(channel for channel in animation["channels"]
                       if channel["target"] == {"node": index, "path": "translation"})
        accessor = animation["samplers"][channel["sampler"]]["output"]
        row = document["accessors"][accessor]["count"] // 2
        values = list(decoded.accessor(accessor)[row])
        values[0] += .1
        change_accessor(binary, document, accessor, row, values)
        self.assertInvalid(encode_glb(document, binary), model)

    def test_distinct_exact_force_completion_and_authored_boundary_cannot_collapse(self):
        _, model = changed_case("P16", lambda text: add_scene_events(text, "    at 0.3[s] sequence { }\n"))
        with self.assertRaises(OntoKinError) as caught:
            export_glb(model, target_contract=CONTRACT, options=ExportOptions(helpers=False, fps=1))
        self.assertEqual(caught.exception.diagnostic.details["export_code"], "OKE-E-TIMES-COLLAPSED")

    def test_smallest_positive_force_completion_cannot_be_erased_at_zero(self):
        _, model = compile_case("S09")
        with self.assertRaises(OntoKinError) as caught:
            export_glb(model, target_contract=CONTRACT, options=ExportOptions(helpers=False, fps=1))
        self.assertEqual(caught.exception.diagnostic.details["export_code"], "OKE-E-TIMES-COLLAPSED")

    def test_source_valid_positions_beyond_float32_fail_explicitly(self):
        _, model = changed_case("P05", lambda text: text.replace("3[m/s]", "1e39[m/s]"))
        self.assertTrue(math.isfinite(evaluate(model, ["3"])["samples"][0]["objects"]["ball"]["position_m"][0]))
        with self.assertRaises(OntoKinError) as caught:
            export_glb(model, target_contract=CONTRACT, options=ExportOptions(helpers=False, fps=1))
        self.assertEqual(caught.exception.diagnostic.details["export_code"], "OKE-E-FLOAT32")

    def test_huge_finite_planning_inputs_produce_bounded_diagnostics_not_python_overflow(self):
        for case_id, options in (("P18", ExportOptions(helpers=False, fps=1e-308)),
                                 ("P20", ExportOptions(helpers=False, fps=1, end="0.25"))):
            with self.subTest(case=case_id):
                _, model = compile_case(case_id)
                with patch("ontokin.scene._nodes", side_effect=AssertionError("Unbounded planning reached geometry")):
                    with self.assertRaises(OntoKinError) as caught:
                        export_glb(model, target_contract=CONTRACT, options=options)
                self.assertIn(caught.exception.code, ("OKL-E-RESOURCE", "OKL-E-NUMERIC"))
                self.assertEqual(caught.exception.diagnostic.details["target_contract"], CONTRACT)

    def test_insufficient_key_and_pose_budgets_reject_before_mesh_allocation(self):
        _, model = compile_case("P01")
        for name, limit in (("MAX_KEYFRAMES", 4), ("MAX_BAKED_POSES", 1)):
            with self.subTest(budget=name), patch("ontokin.scene." + name, limit), \
                    patch("ontokin.scene._nodes", side_effect=AssertionError("Unbudgeted mesh allocation")):
                with self.assertRaises(OntoKinError) as caught:
                    export_glb(model, target_contract=CONTRACT, options=ExportOptions(helpers=False, fps=1))
                self.assertEqual(caught.exception.code, "OKL-E-RESOURCE")

    def test_complete_nested_force_history_budget_cannot_be_bypassed_by_supplied_bytes(self):
        statement = CASES["P01"]["force_statements"][0]["text"]
        forces = "\n".join(f'force ball @ "f{index}" using vector(world, 0[N], 0[N], 0[N]) for 1[s];'
                           for index in range(260))
        events = "".join(f"    at 1.{index:02d}[s] sequence {{ }}\n" for index in range(1, 10))
        _, model = changed_case("P01", lambda text: add_scene_events(text.replace(statement, forces), events))
        self.assertLess(_records_per_sample(model), 100000)
        options = ExportOptions(helpers=False, fps=1)
        # Build source-correct supplied bytes under an explicit larger publisher
        # limit. Individual evaluator batches still fit the unchanged kernel cap.
        with patch("ontokin.scene.MAX_OUTPUT_RECORDS", 1000000), patch("ontokin.scene.MAX_SAMPLES", 5):
            baked = build_scene(model, target_contract=CONTRACT, options=options)
            data, _ = _encode(baked)
        actual_entries = sum(measure_json(row["force_states_after"])["entries"] for row in baked.metadata["boundary_states"])
        self.assertGreater(actual_entries, 100000)
        with patch("ontokin.scene._nodes", side_effect=AssertionError("Unbudgeted mesh allocation")):
            with self.assertRaises(OntoKinError) as caught:
                export_glb(model, target_contract=CONTRACT, options=options)
        self.assertEqual(caught.exception.diagnostic.details["export_code"], "OKE-E-BOUNDARY-BUDGET")
        with patch("ontokin.gltf._validate_surface", side_effect=AssertionError("Unbudgeted geometry validation")), \
                patch("ontokin.gltf.sampled_states", side_effect=AssertionError("Unbudgeted output evaluation")):
            with self.assertRaises(OntoKinError) as caught:
                validate_export(data, model, target_contract=CONTRACT, options=options)
        self.assertEqual(caught.exception.diagnostic.details["export_code"], "OKE-E-BOUNDARY-BUDGET")

    def test_glb_byte_budget_is_enforced_by_writer_and_serialized_reader(self):
        _, model, options, result, _ = delivered_case("P01")
        with patch("ontokin.gltf.MAX_GLB_BYTES", 1024):
            with self.assertRaises(OntoKinError) as caught:
                export_glb(model, target_contract=CONTRACT, options=options)
            self.assertEqual(caught.exception.code, "OKL-E-RESOURCE")
            with self.assertRaises(OntoKinError) as caught:
                validate_export(result.data, model, target_contract=CONTRACT, options=options)
            self.assertEqual(caught.exception.diagnostic.details["target_contract"], CONTRACT)

    def test_shared_accessor_expansion_is_bounded_before_any_decoded_copy(self):
        _, model, options, _, decoded = delivered_case("P01")
        document, binary = aliased_accessors(decoded, 4096, gltf.MAX_DECODED_COMPONENTS // 4096 + 1)
        data = encode_glb(document, binary)
        self.assertLess(len(data), 200000)
        # Each accessor would get a separate decoded Python cache. The BIN
        # remains small, so the ordinary file-byte limit cannot stop expansion.
        for operation in (lambda: gltf.read_glb(data),
                          lambda: validate_export(data, model, target_contract=CONTRACT, options=options)):
            with self.subTest(reader=operation), patch.object(gltf.DecodedGLB, "accessor",
                    side_effect=AssertionError("Unbudgeted decoded allocation")):
                with self.assertRaises(OntoKinError) as caught:
                    operation()
                self.assertEqual(caught.exception.code, "OKL-E-RESOURCE")
                self.assertEqual(caught.exception.diagnostic.details["export_code"], "OKE-E-ACCESSOR-BUDGET")

    def test_shared_storage_is_charged_per_accessor_at_the_exact_budget(self):
        _, model, options, _, decoded = delivered_case("P01")
        document, binary = aliased_accessors(decoded, 1000, 100)
        components = sum(accessor["count"] * {"SCALAR": 1, "VEC3": 3, "VEC4": 4}[accessor["type"]]
                         for accessor in document["accessors"])
        data = encode_glb(document, binary)
        with patch.object(gltf, "MAX_DECODED_COMPONENTS", components):
            self.assertEqual(validate_export(data, model, target_contract=CONTRACT, options=options)["status"], "passed")
        with patch.object(gltf, "MAX_DECODED_COMPONENTS", components - 1), \
                patch.object(gltf.DecodedGLB, "accessor", side_effect=AssertionError("Unbudgeted decoded allocation")):
            with self.assertRaises(OntoKinError) as caught:
                validate_export(data, model, target_contract=CONTRACT, options=options)
            self.assertEqual(caught.exception.diagnostic.details["export_code"], "OKE-E-ACCESSOR-BUDGET")

    def test_declared_key_pose_and_native_vertex_limits_precede_decoding(self):
        _, model, options, result, decoded = delivered_case("P01")
        primitive = decoded.document["meshes"][0]["primitives"][0]
        vertices = decoded.document["accessors"][primitive["attributes"]["POSITION"]]["count"]
        keys = len(decoded.animation_times())
        for budget, limit in (("MAX_KEYFRAMES", keys - 1), ("MAX_BAKED_POSES", keys - 1),
                              ("MAX_MESH_VERTICES", vertices - 1)):
            for forged_contract in (False, True):
                document = copy.deepcopy(decoded.document)
                if forged_contract:
                    document["extras"]["ontokin"]["target_contract"] = "ontokin.glb/0.1"
                data = encode_glb(document, decoded.binary) if forged_contract else result.data
                with self.subTest(budget=budget, forged=forged_contract), patch.object(gltf, budget, limit), \
                        patch.object(gltf.DecodedGLB, "accessor", side_effect=AssertionError("Late role budget")):
                    with self.assertRaises(OntoKinError) as caught:
                        validate_export(data, model, target_contract=CONTRACT, options=options)
                    self.assertEqual(caught.exception.code, "OKL-E-RESOURCE")

    def test_negative_and_boolean_layout_references_cannot_alias_valid_indices(self):
        _, model, options, _, decoded = delivered_case("P01")
        for role in ("mesh", "position", "normal", "indices", "material", "sampler", "input", "view", "target"):
            with self.subTest(role=role):
                document = copy.deepcopy(decoded.document)
                primitive = document["meshes"][0]["primitives"][0]
                animation = document["animations"][0]
                if role == "mesh":
                    record, key, table = document["nodes"][0], "mesh", document["meshes"]
                elif role in ("position", "normal"):
                    record, key, table = primitive["attributes"], role.upper(), document["accessors"]
                elif role in ("indices", "material"):
                    record, key = primitive, role
                    table = document["accessors"] if role == "indices" else document["materials"]
                elif role == "sampler":
                    record, key, table = animation["channels"][0], "sampler", animation["samplers"]
                elif role == "input":
                    record, key, table = animation["samplers"][0], "input", document["accessors"]
                elif role == "view":
                    record, key, table = document["accessors"][0], "bufferView", document["bufferViews"]
                else:
                    record, key, table = animation["channels"][0]["target"], "node", document["nodes"]
                record[key] -= len(table)  # Same Python lookup, invalid glTF reference.
                self.assertInvalid(encode_glb(document, decoded.binary), model, options=options)
        document = copy.deepcopy(decoded.document)
        document["animations"][0]["channels"][0]["target"]["node"] = False
        self.assertInvalid(encode_glb(document, decoded.binary), model, options=options)

    def test_nested_supplied_json_obeys_the_writer_depth_limit_before_decoding(self):
        _, model, options, _, decoded = delivered_case("P01")
        document = copy.deepcopy(decoded.document)
        nested = 0
        for _ in range(150):
            nested = [nested]
        document["unused_nested_data"] = nested
        with patch.object(gltf.DecodedGLB, "accessor", side_effect=AssertionError("Unbounded JSON reached decode")):
            with self.assertRaises(OntoKinError) as caught:
                validate_export(encode_glb(document, decoded.binary), model, target_contract=CONTRACT, options=options)
        self.assertEqual(caught.exception.diagnostic.details["export_code"], "OKE-E-METADATA-BUDGET")

    def test_cancellation_preserves_original_exception_through_each_recording_stage(self):
        _, model, options, result, _ = delivered_case("P01")
        phases = ((force_runtime.ForceSimulator, "advance", "export"),
                  (force_runtime, "force_record_bound", "export"),
                  (scene, "_nodes", "export"), (gltf, "_encode", "export"),
                  (gltf, "read_glb", "validate"), (gltf, "_preflight_accessor_layout", "validate"),
                  (gltf, "_preflight_scene_layout", "validate"), (gltf, "_validate_surface", "validate"),
                  (gltf, "sampled_states", "validate"))
        for owner, name, operation in phases:
            for kind in ("plain", "diagnostic"):
                with self.subTest(stage=name, operation=operation, exception=kind):
                    entered = False
                    original = getattr(owner, name)
                    interruption = (RuntimeError("Caller cancelled force delivery") if kind == "plain" else
                                    OntoKinError("OKL-E-RESOURCE", "Caller budget exhausted", details={"caller": True}))
                    def entering(*args, **kwargs):
                        nonlocal entered
                        entered = True
                        return original(*args, **kwargs)
                    def cancel():
                        if entered:
                            raise interruption
                    with patch.object(owner, name, entering):
                        with self.assertRaises(type(interruption)) as caught:
                            if operation == "export":
                                export_glb(model, target_contract=CONTRACT, options=options, check=cancel)
                            else:
                                validate_export(result.data, model, target_contract=CONTRACT, options=options, check=cancel)
                    self.assertTrue(entered)
                    self.assertIs(caught.exception, interruption)
                    if kind == "diagnostic":
                        self.assertEqual(interruption.diagnostic.details, {"caller": True})

    def test_older_delivery_contracts_cannot_silently_export_force_semantics(self):
        _, model = compile_case("P01")
        for version in range(1, 5):
            target = f"ontokin.glb/0.{version}"
            with self.subTest(target=target), self.assertRaises(OntoKinError) as caught:
                export_glb(model, target_contract=target)
            self.assertEqual(caught.exception.code, "OKL-E-CAPABILITY-UNSUPPORTED")
            self.assertEqual(caught.exception.diagnostic.details["target_contract"], target)


if __name__ == "__main__":
    unittest.main()
