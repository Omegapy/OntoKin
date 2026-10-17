"""Independent numerical and event-boundary oracles for the core evaluator.

These scenes are built from normalized records, independently of parsing. The
source-level conformance suite separately checks the four authored .ok programs.
"""

from __future__ import annotations

import copy
from decimal import Decimal
from fractions import Fraction as F
import json
import math
import unittest

from ontokin.diagnostics import OntoKinError, Source
from ontokin.evaluator import construct, evaluate, inspect_in_frame, preflight, time_text
from ontokin.model import (ActionModel, Event, EventBlock, FollowModel, JointModel,
                           ObjectModel, Pose, SceneModel, SiteModel)


def rotation_z(angle):
    return (math.cos(angle / 2), 0.0, 0.0, math.sin(angle / 2))


def scene(duration=3):
    return SceneModel("Example", "example", "Demo", "demo", duration=F(duration),
                      gravity=(0.0, -9.81, 0.0))


def object_in(model, path, *, position=(0.0, 0.0, 0.0), rotation=(1.0, 0.0, 0.0, 0.0),
              owner=None, mode="prescribed", mass=0.0, radius=0.1, velocity=(0.0, 0.0, 0.0),
              omega=(0.0, 0.0, 0.0)):
    physical = ({"kind": "sphere_body", "mass": mass, "radius": radius, "inertia": .4 * mass * radius ** 2}
                if mass else {"kind": "no_body"})
    model.objects[path] = ObjectModel(path, path.rsplit(".", 1)[-1], "Object",
        (model.module_key, model.scene_key, *path.split(".")), owner=owner,
        placement=Pose("world", position, rotation), motion=mode, physical=physical,
        velocity=velocity, omega=omega)
    site_in(model, path + ".origin", path)


def site_in(model, path, owner, position=(0.0, 0.0, 0.0), rotation=(1.0, 0.0, 0.0, 0.0)):
    model.sites[path] = SiteModel(path, (model.module_key, model.scene_key, *path.split(".")), owner,
                                  Pose(owner + ".frame", position, rotation))


def joint_in(model, path, kind, parent, child, *, axis=None, limits=None, initial=None):
    model.joints[path] = JointModel(path, path.rsplit(".", 1)[-1], (model.module_key, model.scene_key, *path.split(".")),
                                    kind, parent, child, axis=axis, limits=limits, initial=initial)


def action_in(model, path, kind, target, duration, *, vector=None, goal=None):
    model.actions[path] = ActionModel(path, path, (model.module_key, model.scene_key, path),
                                      kind, target, F(duration), vector=vector, goal=goal)


def at(model, time, *events):
    model.events.append(EventBlock(F(time), [Event(kind, target) for kind, target in events]))


def independent_parts():
    model = scene()
    object_in(model, "rig")
    object_in(model, "rig.head", owner="rig")
    object_in(model, "rig.arm", owner="rig")
    object_in(model, "rig.arm.hand", owner="rig.arm")
    site_in(model, "rig.neck", "rig", (0.0, 1.0, 0.0))
    site_in(model, "rig.shoulder", "rig", (0.0, .5, 0.0))
    joint_in(model, "rig.yaw", "hinge", "rig.neck", "rig.head.origin", axis=(0.0, 1.0, 0.0),
             limits=(-math.pi / 2, math.pi / 2), initial=0.0)
    joint_in(model, "rig.mount", "fixed", "rig.shoulder", "rig.arm.origin")
    joint_in(model, "rig.arm.extension", "slider", "rig.arm.origin", "rig.arm.hand.origin",
             axis=(1.0, 0.0, 0.0), limits=(.25, .75), initial=.25)
    action_in(model, "advance", "move", "rig", 2, vector=(1.0, 0.0, 0.0))
    action_in(model, "look", "tween", "rig.yaw", 1, goal=math.pi / 2)
    action_in(model, "reach", "tween", "rig.arm.extension", 2, goal=.75)
    at(model, 0, ("start", "advance"), ("start", "look"), ("start", "reach"))
    return model


def gravity_release(*, rotating=False, release_time=1):
    model = scene(2)
    object_in(model, "carrier", position=(0.0, 2.0, 0.0),
              rotation=rotation_z(-2) if rotating else (1.0, 0.0, 0.0, 0.0))
    object_in(model, "payload", mass=1)
    if rotating:
        site_in(model, "carrier.tip", "carrier", (.5, 0.0, 0.0))
    joint_in(model, "hold", "grip", "carrier.tip" if rotating else "carrier.origin", "payload.origin")
    action_in(model, "carry", "move", "carrier", 2, vector=(1.0, 0.0, 0.0))
    events = [("start", "carry")]
    if rotating:
        action_in(model, "turn", "spin", "carrier", 2, vector=(0.0, 0.0, 2.0))
        events.append(("start", "turn"))
    at(model, 0, *events)
    at(model, release_time, ("release", "hold"))
    return model


def ownership_follow():
    model = scene(1)
    object_in(model, "first")
    object_in(model, "second")
    object_in(model, "first.ball", owner="first", position=(0.0, 2.0, 0.0), mode="dynamic", mass=1, radius=.2)
    object_in(model, "second.ball", owner="second", position=(0.0, 2.0, 0.0), mode="dynamic", mass=1, radius=.3)
    object_in(model, "label")
    model.follows["caption"] = FollowModel("caption", "caption", ("example", "demo", "caption"),
        "first.ball.frame", "label", Pose("first.ball.frame", (0.0, .5, 0.0)))
    action_in(model, "shift_group", "move", "first", 1, vector=(1.0, 0.0, 0.0))
    at(model, 0, ("start", "shift_group"))
    return model


class EvaluatorTests(unittest.TestCase):
    def assertVector(self, actual, expected, tolerance=1e-9):
        self.assertEqual(len(actual), len(expected))
        self.assertLessEqual(max(abs(a - e) for a, e in zip(actual, expected)), tolerance,
                             f"{actual} differs from {expected}")

    def assertRotation(self, actual, expected, tolerance=1e-9):
        # The atan2 form avoids arccos precision loss close to the identity.
        actual = tuple(x / math.hypot(*actual) for x in actual)
        expected = tuple(x / math.hypot(*expected) for x in expected)
        if sum(a * e for a, e in zip(actual, expected)) < 0:
            expected = tuple(-x for x in expected)
        chord = math.hypot(*(a - e for a, e in zip(actual, expected)))
        angle = 4 * math.asin(min(1.0, chord / 2))
        self.assertLessEqual(angle, tolerance)

    def sample(self, model, time, side="after"):
        return evaluate(model, [{"time_seconds": time, "side": side}])["samples"][0]

    def test_p01_independent_parts_and_completion_derivatives(self):
        model = independent_parts()
        result = evaluate(model, ["0", ".5", "1", "1.5", "2", "3"])
        expected_x = [.25, .875, 1.5, 2.125, 2.75, 2.75]
        for sample, x in zip(result["samples"], expected_x):
            self.assertVector(sample["objects"]["rig.arm.hand"]["position_m"], (x, .5, 0))
        before = self.sample(model, "1", "before")
        after = self.sample(model, "1")
        self.assertVector(before["objects"]["rig.head"]["angular_velocity_rad_per_s"], (0, math.pi / 2, 0))
        self.assertVector(after["objects"]["rig.head"]["angular_velocity_rad_per_s"], (0, 0, 0))
        self.assertEqual(before["actions"]["look"]["status"], "running")
        self.assertEqual(after["actions"]["look"]["status"], "completed")
        self.assertVector(after["objects"]["rig.arm.hand"]["velocity_m_per_s"], (1.25, 0, 0))
        self.assertEqual(after["objects"]["rig.arm.hand"]["element_id"], ["example", "demo", "rig", "arm", "hand"])

    def test_p02_release_is_continuous_and_later_carrier_stop_is_independent(self):
        model = gravity_release()
        before, after, later, endpoint = evaluate(model, [
            {"time": "1", "side": "before"}, "1", "1.5", "2"])["samples"]
        for key in ("position_m", "orientation_wxyz", "velocity_m_per_s", "angular_velocity_rad_per_s"):
            self.assertEqual(before["objects"]["payload"][key], after["objects"]["payload"][key])
        self.assertEqual(before["objects"]["payload"]["motion"], "prescribed")
        self.assertEqual(after["objects"]["payload"]["motion"], "dynamic")
        self.assertEqual(after["joints"]["hold"]["status"], "inactive")
        self.assertVector(later["objects"]["payload"]["position_m"], (1.5, .77375, 0))
        self.assertVector(endpoint["objects"]["payload"]["velocity_m_per_s"], (1, -9.81, 0))
        self.assertVector(endpoint["objects"]["carrier"]["velocity_m_per_s"], (0, 0, 0))
        self.assertEqual(after["objects"]["payload"]["own_mass_kg"], 1)
        self.assertEqual(after["objects"]["carrier"]["owned_aggregate_mass_kg"], 0)
        self.assertEqual(endpoint["objects"]["payload"]["gravity_participation"], "active_dynamic")

    def test_p03_rotating_release_retains_offset_velocity_and_spin(self):
        model = gravity_release(rotating=True)
        half, before, after, later, endpoint = evaluate(model, [".5", {"time": "1", "side": "before"},
                                                             "1", "1.5", "2"])["samples"]
        self.assertVector(half["objects"]["payload"]["position_m"], (.5 + .5 * math.cos(-1), 2 + .5 * math.sin(-1), 0))
        self.assertVector(before["objects"]["payload"]["velocity_m_per_s"], (1, 1, 0))
        self.assertVector(after["objects"]["payload"]["velocity_m_per_s"], (1, 1, 0))
        self.assertVector(later["objects"]["payload"]["position_m"], (2, 1.27375, 0))
        self.assertVector(endpoint["objects"]["payload"]["position_m"], (2.5, -1.905, 0))
        self.assertVector(endpoint["objects"]["payload"]["angular_velocity_rad_per_s"], (0, 0, 2))
        self.assertRotation(later["objects"]["payload"]["orientation_wxyz"], rotation_z(1))
        self.assertRotation(endpoint["objects"]["payload"]["orientation_wxyz"], rotation_z(2))

    def test_p04_ownership_adds_neither_pose_nor_duplicate_mass(self):
        sample = self.sample(ownership_follow(), ".5")
        self.assertVector(sample["objects"]["first"]["position_m"], (.5, 0, 0))
        for path in ("first.ball", "second.ball"):
            self.assertVector(sample["objects"][path]["position_m"], (0, .77375, 0))
        self.assertVector(sample["objects"]["label"]["position_m"], (0, 1.27375, 0))
        self.assertEqual(sample["scene_mass_kg"], 2)
        self.assertEqual(sample["objects"]["first"]["owned_aggregate_mass_kg"], 1)
        self.assertAlmostEqual(sample["objects"]["first.ball"]["inertia_kg_m2"], .016)
        self.assertAlmostEqual(sample["objects"]["second.ball"]["inertia_kg_m2"], .036)
        local = inspect_in_frame(sample, "first.ball", "first.frame")
        self.assertVector(local["position_m"], (-.5, .77375, 0))
        self.assertVector(local["velocity_m_per_s"], (0, -4.905, 0))
        self.assertEqual(local["velocity_measured_in"], "world")

    def test_pause_holds_only_its_action_and_horizon_does_not_force_completion(self):
        model = gravity_release()
        at(model, F(5, 4), ("pause", "carry"))
        at(model, F(7, 4), ("resume", "carry"))
        half, endpoint = evaluate(model, ["1.5", "2"])["samples"]
        self.assertVector(half["objects"]["carrier"]["position_m"], (1.25, 2, 0))
        self.assertVector(half["objects"]["carrier"]["velocity_m_per_s"], (0, 0, 0))
        self.assertVector(half["objects"]["payload"]["position_m"], (1.5, .77375, 0))
        self.assertEqual(half["actions"]["carry"]["status"], "paused")
        self.assertVector(endpoint["objects"]["carrier"]["position_m"], (1.5, 2, 0))
        self.assertEqual(endpoint["actions"]["carry"]["status"], "running")
        self.assertEqual(endpoint["actions"]["carry"]["local_elapsed_seconds"], "1.5")

    def test_natural_completion_precedes_release_but_not_its_incoming_snapshot(self):
        sample = self.sample(gravity_release(release_time=2), "2")
        self.assertVector(sample["objects"]["carrier"]["velocity_m_per_s"], (0, 0, 0))
        self.assertVector(sample["objects"]["payload"]["velocity_m_per_s"], (1, 0, 0))
        self.assertVector(sample["objects"]["payload"]["position_m"], (2, 2, 0))
        self.assertEqual(sample["actions"]["carry"]["status"], "completed")

    def test_release_then_stop_then_replacement_captures_current_coordinate(self):
        model = gravity_release()
        action_in(model, "replacement", "move", "carrier", F(1, 2), vector=(2.0, 0.0, 0.0))
        model.events[-1].events += [Event("stop", "carry"), Event("start", "replacement")]
        sample = self.sample(model, "1.5")
        self.assertVector(sample["objects"]["carrier"]["position_m"], (2, 2, 0))
        self.assertVector(sample["objects"]["payload"]["position_m"], (1.5, .77375, 0))
        self.assertEqual(sample["actions"]["carry"]["status"], "stopped")
        self.assertEqual(sample["actions"]["replacement"]["status"], "completed")

    def test_stopping_root_preserves_local_reach_and_completed_yaw(self):
        model = independent_parts()
        at(model, 1, ("stop", "advance"))
        sample = self.sample(model, "1.5")
        self.assertVector(sample["objects"]["rig.arm.hand"]["position_m"], (1.625, .5, 0))
        self.assertVector(sample["objects"]["rig.arm.hand"]["velocity_m_per_s"], (.25, 0, 0))
        self.assertAlmostEqual(sample["joints"]["rig.yaw"]["coordinate"], math.pi / 2)
        self.assertEqual(sample["actions"]["reach"]["status"], "running")

    def test_joint_chain_and_nonzero_child_site_transfer_all_derivatives(self):
        model = scene(2)
        object_in(model, "root", position=(0.0, 2.0, 0.0), rotation=rotation_z(-1))
        object_in(model, "link")
        object_in(model, "hand")
        object_in(model, "payload", mass=1)
        object_in(model, "label")
        site_in(model, "link.tip", "link", (.5, 0.0, 0.0))
        site_in(model, "payload.mount", "payload", (.2, 0.0, 0.0))
        joint_in(model, "yaw", "hinge", "root.origin", "link.origin", axis=(0.0, 0.0, 1.0), limits=(-2, 2), initial=0)
        joint_in(model, "reach", "slider", "link.tip", "hand.origin", axis=(1.0, 0.0, 0.0), limits=(0, 1), initial=.25)
        joint_in(model, "hold", "grip", "hand.origin", "payload.mount")
        model.follows["caption"] = FollowModel("caption", "caption", ("caption",), "payload.frame", "label",
                                               Pose("payload.frame", (0.0, .5, 0.0)))
        action_in(model, "translate", "move", "root", 2, vector=(1.0, 0.0, 0.0))
        action_in(model, "rotate", "spin", "root", 2, vector=(0.0, 0.0, 2.0))
        action_in(model, "turn", "tween", "yaw", 1, goal=1)
        action_in(model, "extend", "tween", "reach", 1, goal=.75)
        at(model, 0, *(("start", key) for key in model.actions))
        at(model, 1, ("release", "hold"))
        before, after, later = evaluate(model, [{"time": "1", "side": "before"}, "1", "1.5"])["samples"]
        c, s = math.cos(2), math.sin(2)
        position = (1 + 1.05 * c, 2 + 1.05 * s, 0)
        velocity = (1 - 3.15 * s + .5 * c, 3.15 * c + .5 * s, 0)
        self.assertVector(before["objects"]["payload"]["position_m"], position)
        self.assertVector(before["objects"]["payload"]["velocity_m_per_s"], velocity)
        self.assertVector(after["objects"]["payload"]["velocity_m_per_s"], velocity)
        self.assertEqual(before["objects"]["payload"]["orientation_wxyz"], after["objects"]["payload"]["orientation_wxyz"])
        self.assertVector(after["objects"]["payload"]["angular_velocity_rad_per_s"], (0, 0, 3))
        self.assertVector(later["objects"]["payload"]["position_m"],
                           (position[0] + velocity[0] / 2, position[1] + velocity[1] / 2 - 9.81 / 8, 0))
        self.assertVector(after["objects"]["label"]["velocity_m_per_s"],
                           (velocity[0] - 1.5 * c, velocity[1] - 1.5 * s, 0))

    def test_world_angular_velocity_multiplies_rotation_on_the_left(self):
        model = scene(1)
        model.gravity = (0.0, 0.0, 0.0)
        q = math.sqrt(.5)
        object_in(model, "ball", mode="dynamic", mass=1, rotation=(q, q, 0.0, 0.0), omega=(0.0, math.pi / 2, 0.0))
        sample = self.sample(model, "1")
        self.assertRotation(sample["objects"]["ball"]["orientation_wxyz"], (.5, .5, .5, -.5))

    def test_velocity_inspection_changes_axes_without_subtracting_frame_motion(self):
        model = scene(1)
        object_in(model, "owner", rotation=rotation_z(math.pi / 2))
        object_in(model, "ball", mode="dynamic", mass=1, velocity=(2.0, 0.0, 0.0))
        action_in(model, "shift", "move", "owner", 1, vector=(1.0, 0.0, 0.0))
        at(model, 0, ("start", "shift"))
        sample = self.sample(model, "0")
        local = inspect_in_frame(sample, "ball", "owner.frame")
        self.assertVector(local["velocity_m_per_s"], (0, -2, 0))
        self.assertEqual(local["velocity_measured_in"], "world")
        self.assertEqual(local["velocity_expressed_in"], "owner.frame")

    def test_zero_spin_has_a_valid_orientation_and_still_claims_its_channel(self):
        model = scene(1)
        object_in(model, "root")
        action_in(model, "spin", "spin", "root", 1, vector=(0.0, 0.0, 0.0))
        at(model, 0, ("start", "spin"))
        sample = self.sample(model, ".5")
        self.assertRotation(sample["objects"]["root"]["orientation_wxyz"], (1, 0, 0, 0))
        self.assertEqual(sample["objects"]["root"]["pose_authority"]["orientation_action"], "spin")

    def test_protocol_decimal_and_source_binary64_are_distinct_instants(self):
        model = scene(1)
        object_in(model, "root")
        action_in(model, "move", "move", "root", .2, vector=(1.0, 0.0, 0.0))
        at(model, F.from_float(.1), ("start", "move"))
        decimal, binary = evaluate(model, ["0.1", F.from_float(.1)])["samples"]
        self.assertEqual(decimal["actions"]["move"]["status"], "pending")
        self.assertEqual(binary["actions"]["move"]["status"], "running")
        self.assertIn(time_text(F.from_float(.1)), preflight(model)["boundary_times_seconds"])
        endpoint = F.from_float(.1) + F.from_float(.2)
        before, after = evaluate(model, [{"time": endpoint, "side": "before"}, endpoint])["samples"]
        self.assertEqual(before["actions"]["move"]["status"], "running")
        self.assertEqual(after["actions"]["move"]["status"], "completed")

    def test_exact_sum_endpoint_must_not_be_rounded_to_authored_timestamp(self):
        model = scene(1)
        object_in(model, "root")
        action_in(model, "first", "move", "root", .2, vector=(1.0, 0.0, 0.0))
        action_in(model, "next", "move", "root", .1, vector=(2.0, 0.0, 0.0))
        at(model, F.from_float(.1), ("start", "first"))
        at(model, F.from_float(.3), ("start", "next"))
        with self.assertRaises(OntoKinError) as context:
            preflight(model)
        self.assertEqual(context.exception.code, "OKL-E-CONTROL-CONFLICT")
        self.assertEqual(context.exception.diagnostic.time, F.from_float(.3))

    def test_pause_keeps_channel_claim_and_restart_checks_state_first(self):
        model = gravity_release()
        action_in(model, "other", "move", "carrier", 1, vector=(0.0, 1.0, 0.0))
        at(model, F(1, 2), ("pause", "carry"), ("start", "other"))
        with self.assertRaises(OntoKinError) as context:
            preflight(model)
        self.assertEqual(context.exception.code, "OKL-E-CONTROL-CONFLICT")
        model.events[-1].events[-1] = Event("start", "carry")
        with self.assertRaises(OntoKinError) as context:
            preflight(model)
        self.assertEqual(context.exception.code, "OKL-E-ACTION-STATE")

    def test_natural_completion_before_explicit_pause_rejects_completed_action(self):
        model = independent_parts()
        at(model, 1, ("pause", "look"))
        with self.assertRaises(OntoKinError) as context:
            preflight(model)
        self.assertEqual(context.exception.code, "OKL-E-ACTION-STATE")
        self.assertEqual(context.exception.diagnostic.phase, "transition")

    def test_stop_before_release_fails_without_persisting_partial_event_changes(self):
        model = gravity_release()
        model.events[-1].events.insert(0, Event("stop", "carry"))
        with self.assertRaises(OntoKinError) as context:
            evaluate(model, ["1"])
        self.assertEqual(context.exception.code, "OKL-E-EVENT-CONFLICT")
        self.assertEqual(context.exception.diagnostic.category, "conflict")
        # Repairing statement order starts a fresh run. The failed stop did not
        # mutate the normalized definition or leak state into the new request.
        model.events[-1].events.reverse()
        sample = self.sample(model, "1")
        self.assertEqual(sample["actions"]["carry"]["status"], "stopped")
        self.assertVector(sample["objects"]["payload"]["velocity_m_per_s"], (1, 0, 0))

    def test_release_twice_and_prescribed_action_on_dynamic_body_reject(self):
        model = gravity_release()
        at(model, F(3, 2), ("release", "hold"))
        with self.assertRaises(OntoKinError) as context:
            preflight(model)
        self.assertEqual(context.exception.code, "OKL-E-RELEASE-STATE")
        model = ownership_follow()
        model.actions["shift_group"].target = "first.ball"
        with self.assertRaises(OntoKinError) as context:
            preflight(model)
        self.assertEqual(context.exception.code, "OKL-E-MOTION-MODE")
        self.assertEqual(context.exception.diagnostic.phase, "admission")

    def test_joint_limit_error_is_an_admission_failure(self):
        model = independent_parts()
        model.actions["look"].goal = math.pi
        with self.assertRaises(OntoKinError) as context:
            preflight(model)
        self.assertEqual(context.exception.code, "OKL-E-JOINT-LIMIT")
        self.assertEqual(context.exception.diagnostic.phase, "admission")

    def test_repeated_and_unsorted_samples_are_read_only_and_reset(self):
        model = gravity_release()
        original = copy.deepcopy(model)
        times = ["1.5", {"time": "0", "side": "before"}, "1", "1.5", "0"]
        first, second = evaluate(model, times), evaluate(model, times)
        self.assertEqual(first, second)
        self.assertEqual(first["samples"][0], first["samples"][3])
        self.assertEqual(first["samples"][1]["actions"]["carry"]["status"], "pending")
        self.assertEqual(first["samples"][4]["actions"]["carry"]["status"], "running")
        self.assertEqual(model, original)
        json.dumps(first, allow_nan=False)

    def test_dynamic_interior_extremum_cannot_hide_overflow_between_samples(self):
        model = scene(2)
        model.gravity = (-1.6e308, 0.0, 0.0)
        object_in(model, "ball", mode="dynamic", mass=1, position=(1e308, 0.0, 0.0),
                  velocity=(1.6e308, 0.0, 0.0))
        with self.assertRaises(OntoKinError) as context:
            evaluate(model, ["0", "2"])
        self.assertEqual(context.exception.code, "OKL-E-NUMERIC")
        self.assertEqual(context.exception.diagnostic.category, "numerical_failure")
        self.assertEqual(context.exception.diagnostic.blocks, ["evaluated", "delivered"])
        self.assertIn("last_valid_boundary_seconds", context.exception.diagnostic.details)

    def test_finite_affine_state_survives_large_intermediate_cancellation(self):
        model = scene(2)
        object_in(model, "root", position=(1.6e308, 0.0, 0.0))
        action_in(model, "move", "move", "root", 2, vector=(-1.6e308, 0.0, 0.0))
        at(model, 0, ("start", "move"))
        sample = self.sample(model, "2")
        self.assertEqual(sample["objects"]["root"]["position_m"][0], -1.6e308)
        self.assertTrue(math.isfinite(sample["objects"]["root"]["position_m"][0]))

    def test_invalid_sample_requests_produce_schema_compatible_time_fields(self):
        for request in ("-1", "3", "nan", "Infinity", "1/2", "0_1", F(1, 3),
                        float("nan"), float("inf"), float("-inf"), None, True, [], {},
                        "1e1000000", Decimal("1e1000000"), Decimal("NaN"),
                        {"time": "1", "side": "left"}, {"time": "-1", "side": "left"}):
            with self.subTest(request=request):
                with self.assertRaises(OntoKinError) as context:
                    evaluate(gravity_release(), [request])
                self.assertEqual(context.exception.code, "OKL-E-SAMPLE")
                diagnostic = context.exception.diagnostic.to_dict(Source(""))
                self.assertIsNone(diagnostic["time"])
                json.dumps(diagnostic, allow_nan=False)

    def test_excessive_timestamp_precision_reports_resource_limit(self):
        for request in ("1e-1000000", Decimal("1e-1000000"), F(1, 2 ** 16385), "0." + "0" * 4096 + "1"):
            with self.subTest(kind=type(request).__name__):
                with self.assertRaises(OntoKinError) as context:
                    evaluate(gravity_release(), [request])
                self.assertEqual(context.exception.code, "OKL-E-RESOURCE")
                self.assertEqual(context.exception.diagnostic.category, "resource_limit")
                self.assertEqual(context.exception.diagnostic.phase, "inspection")
                self.assertIsNone(context.exception.diagnostic.time)

    def test_relative_coordinate_overflow_is_a_structured_inspection_failure(self):
        model = scene(1)
        object_in(model, "left", position=(-1e308, 0.0, 0.0))
        object_in(model, "right", position=(1e308, 0.0, 0.0))
        sample = self.sample(model, "0")
        with self.assertRaises(OntoKinError) as context:
            inspect_in_frame(sample, "right", "left.frame")
        diagnostic = context.exception.diagnostic
        self.assertEqual(diagnostic.code, "OKL-E-NUMERIC")
        self.assertEqual(diagnostic.category, "numerical_failure")
        self.assertEqual(diagnostic.phase, "inspection")
        self.assertEqual(diagnostic.time, F(0))
        self.assertEqual(diagnostic.blocks, [])
        self.assertEqual(sample["objects"]["right"]["position_m"], [1e308, 0.0, 0.0])

    def test_aggregate_mass_cannot_serialize_as_infinity(self):
        model = scene(1)
        object_in(model, "one", mass=1e308, radius=1e-155)
        object_in(model, "two", mass=1e308, radius=1e-155)
        with self.assertRaises(OntoKinError) as context:
            evaluate(model, ["0"])
        self.assertEqual(context.exception.code, "OKL-E-NUMERIC")
        self.assertEqual(context.exception.diagnostic.category, "numerical_failure")

    def test_construct_derives_grip_alignment_before_zero_events(self):
        model = gravity_release(rotating=True)
        result = construct(model)
        self.assertEqual(result["level"], "constructed")
        sample = result["initial_state"]
        self.assertEqual(sample["time_seconds"], "0")
        self.assertEqual(sample["side"], "before")
        self.assertVector(sample["objects"]["payload"]["position_m"], (.5 * math.cos(-2), 2 + .5 * math.sin(-2), 0))
        self.assertVector(sample["objects"]["payload"]["velocity_m_per_s"], (0, 0, 0))
        self.assertEqual(sample["actions"]["carry"]["status"], "pending")

    def test_construct_does_not_claim_timeline_admission(self):
        model = independent_parts()
        model.actions["look"].goal = math.pi
        result = construct(model)
        self.assertEqual(result["outcome"], "valid")
        self.assertEqual(result["initial_state"]["actions"]["look"]["status"], "pending")
        with self.assertRaises(OntoKinError) as context:
            preflight(model)
        self.assertEqual(context.exception.code, "OKL-E-JOINT-LIMIT")

    def test_construct_reports_invalid_initial_world_state_at_constructed_level(self):
        model = scene(1)
        object_in(model, "root", position=(1e308, 0.0, 0.0))
        object_in(model, "child")
        model.follows["offset"] = FollowModel("offset", "offset", ("offset",), "root.frame", "child",
                                              Pose("root.frame", (1e308, 0.0, 0.0)))
        with self.assertRaises(OntoKinError) as context:
            construct(model)
        self.assertEqual(context.exception.code, "OKL-E-NUMERIC")
        self.assertEqual(context.exception.diagnostic.blocks, ["constructed", "evaluated", "delivered"])
        self.assertEqual(context.exception.diagnostic.phase, "elaboration")

    def test_sample_budget_stops_an_unbounded_generator(self):
        consumed = 0
        def unlimited():
            nonlocal consumed
            while True:
                consumed += 1
                yield "0"
        with self.assertRaises(OntoKinError) as context:
            evaluate(scene(1), unlimited())
        self.assertEqual(consumed, 1001)
        self.assertEqual(context.exception.code, "OKL-E-RESOURCE")
        self.assertEqual(context.exception.diagnostic.category, "resource_limit")
        self.assertEqual(context.exception.diagnostic.blocks, [])

    def test_output_budget_counts_attachment_frames_before_evaluation(self):
        class ManySites(dict):
            def __len__(self):
                return 100000
        model = scene(1)
        object_in(model, "root")
        model.sites = ManySites(model.sites)
        with self.assertRaises(OntoKinError) as context:
            evaluate(model, ["0"])
        self.assertEqual(context.exception.code, "OKL-E-RESOURCE")
        self.assertEqual(context.exception.diagnostic.details["records_per_sample"], 100003)


if __name__ == "__main__":
    unittest.main()
