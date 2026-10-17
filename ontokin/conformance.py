"""Execute the published source cases and compare their stated observations.

Fixture-specific mappings belong here, outside the parser, validator, and
evaluator. The expected source files and manifest remain unchanged.
"""

from __future__ import annotations

from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import math
from pathlib import Path
import platform
from typing import Any

from . import __version__
from .diagnostics import OntoKinError, Source
from .fixtures import DEFAULT_FIXTURES, load_manifest, materialize
from .syntax import parse


def _close(actual: Any, expected: Any, tolerance: float = 0.0) -> bool:
    if isinstance(expected, (tuple, list)):
        return isinstance(actual, (tuple, list)) and len(actual) == len(expected) and all(
            _close(a, b, tolerance) for a, b in zip(actual, expected))
    if isinstance(expected, (int, float)) and not isinstance(expected, bool):
        return isinstance(actual, (int, float)) and math.isfinite(actual) and abs(actual - expected) <= tolerance
    return actual == expected


def _rotation_error(actual: list[float], expected: list[float]) -> float:
    """Geodesic orientation error, stable near equal quaternions and either sign."""
    a = [x / math.hypot(*actual) for x in actual]
    b = [x / math.hypot(*expected) for x in expected]
    difference = math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))
    sum_norm = math.sqrt(sum((x + y) ** 2 for x, y in zip(a, b)))
    return 4 * math.atan2(min(difference, sum_norm), max(difference, sum_norm))


class Checks:
    def __init__(self):
        self.items: list[dict] = []

    def add(self, name: str, actual: Any, expected: Any, tolerance: float = 0.0) -> None:
        record = {"check": name, "passed": _close(actual, expected, tolerance),
                  "expected": expected, "actual": actual}
        if tolerance:
            record["absolute_tolerance"] = tolerance
        self.items.append(record)

    def rotation(self, name: str, actual: list[float], expected: list[float]) -> None:
        error = _rotation_error(actual, expected)
        self.items.append({"check": name, "passed": error <= 1e-9,
                           "expected_wxyz": expected, "actual_wxyz": actual,
                           "geodesic_error_rad": error, "absolute_tolerance_rad": 1e-9})


def _observation(checks: Checks, sample: dict, expected: dict) -> None:
    prefix = sample["time_seconds"] + "s/" + sample["side"] + "/"
    objects = sample["objects"]
    for field, value in expected.items():
        if field in {"time_seconds", "side", "element_id"}:
            continue
        if field == "world_position_m":
            obj = next(o for o in objects.values() if o["element_id"] == expected["element_id"])
            checks.add(prefix + "element_id", obj["element_id"], expected["element_id"])
            checks.add(prefix + field, obj["position_m"], value, 1e-9)
        elif field in {"joint_yaw_rad", "head_yaw_rad"}:
            checks.add(prefix + field, sample["joints"]["rig.yaw"]["coordinate"], value, 1e-12)
        elif field.endswith("_status"):
            action = field.removesuffix("_status")
            checks.add(prefix + field, sample["actions"][action]["status"], value)
        else:
            object_name, suffix = None, None
            for ending in ("_position_m", "_velocity_m_per_s", "_omega_rad_per_s"):
                if field.endswith(ending):
                    object_name, suffix = field[:-len(ending)], ending
                    break
            if object_name is None:
                raise ValueError(f"An observation field has no conformance mapping: {field}")
            paths = {
                "root": ["rig"], "head": ["rig.head"], "hand": ["rig.arm.hand"],
                "first_group": ["first"], "either_ball": ["first.ball", "second.ball"],
            }.get(object_name, [object_name])
            key = {"_position_m": "position_m", "_velocity_m_per_s": "velocity_m_per_s",
                   "_omega_rad_per_s": "angular_velocity_rad_per_s"}[suffix]
            for path in paths:
                checks.add(prefix + path + "/" + key, objects[path][key], value, 1e-9)


def _extra_observations(case_id: str, model: Any, checks: Checks, baseline: Any) -> None:
    from .evaluator import evaluate, inspect_in_frame

    def sample(time: str, side: str = "after") -> dict:
        return evaluate(model, [time], side=side)["samples"][0]

    if case_id == "P01":
        final = sample("3")
        for path, position in {"rig": [2, 0, 0], "rig.head": [2, 1, 0],
                               "rig.arm.hand": [2.75, 0.5, 0]}.items():
            checks.add("completed hold/" + path, final["objects"][path]["position_m"], position, 1e-9)
            checks.add("completed velocity/" + path, final["objects"][path]["velocity_m_per_s"], [0, 0, 0], 1e-9)
        checks.rotation("retained head yaw", final["objects"]["rig.head"]["orientation_wxyz"],
                        [math.sqrt(0.5), 0, math.sqrt(0.5), 0])
    if case_id in {"P02", "P03", "P05", "P06", "P07"}:
        release_time = "2" if case_id == "P06" else "1"
        after = sample(release_time)
        payload = after["objects"]["payload"]
        checks.add("release mode", payload["motion"], "dynamic")
        checks.add("release authority", payload["pose_authority"]["kind"], "free_sphere")
        checks.add("released grip inactive", after["joints"]["hold"]["status"], "inactive")
        checks.add("scene ownership retained", payload["owner"], None)
        checks.add("gravity participation", payload["gravity_participation"], "active_dynamic")
        before = sample(release_time, "before")
        checks.add("release identity continuity", payload["element_id"], before["objects"]["payload"]["element_id"])
        checks.rotation("release orientation continuity", payload["orientation_wxyz"],
                        before["objects"]["payload"]["orientation_wxyz"])
    if case_id in {"P04", "P10"}:
        state = sample("0.5")
        for path, radius in (("first.ball", 0.2), ("second.ball", 0.3)):
            checks.add(path + " independent radius", model.objects[path].radius, radius, 1e-12)
        for path in ("first", "second"):
            checks.add(path + " owned mass", state["objects"][path]["owned_aggregate_mass_kg"], 1, 1e-12)
        checks.add("scene mass counted once", state["scene_mass_kg"], 2, 1e-12)
        checks.add("label own mass", state["objects"]["label"]["own_mass_kg"], 0)
        checks.add("all collision response disabled", all(o["collision"] == "disabled" for o in state["objects"].values()), True)
        local = inspect_in_frame(state, "first.ball", "first.frame")
        checks.add("local pose conversion", local["position_m"], [-0.5, 0.77375, 0], 1e-9)
        checks.add("world measurement frame preserved", local["velocity_measured_in"], "world")
        checks.add("local axes velocity", local["velocity_m_per_s"], [0, -4.905, 0], 1e-9)
        try:
            evaluate(model, ["1.01"])
        except OntoKinError as exc:
            checks.add("source horizon enforced", exc.code, "OKL-E-SAMPLE")
        else:
            checks.add("source horizon enforced", "accepted", "OKL-E-SAMPLE")
    if case_id == "P03":
        final = sample("2")
        checks.add("released motion outlives carrier", final["actions"]["carry"]["status"], "completed")
        checks.rotation("free angular progression", final["objects"]["payload"]["orientation_wxyz"],
                        [math.cos(1), 0, 0, math.sin(1)])
    if case_id == "P05":
        checks.add("repeat sampling is side effect free", sample("1.5"), sample("1.5"))
    if case_id in {"P08", "P09", "P11"}:
        times = ["0", "0.5", "1", "2", "3"]
        for actual, reference in zip(evaluate(model, times)["samples"], evaluate(baseline, times)["samples"]):
            by_identity = {tuple(obj["element_id"]): obj for obj in actual["objects"].values()}
            for ref in reference["objects"].values():
                obj = by_identity.get(tuple(ref["element_id"]))
                checks.add("preserved occurrence/" + "/".join(ref["element_id"]), obj is not None, True)
                if obj is None:
                    continue
                for key in ("position_m", "velocity_m_per_s", "angular_velocity_rad_per_s"):
                    checks.add(actual["time_seconds"] + "s/" + "/".join(ref["element_id"]) + "/" + key,
                               obj[key], ref[key], 1e-9)
                checks.rotation("equivalent orientation", obj["orientation_wxyz"], ref["orientation_wxyz"])
        if case_id == "P09":
            checks.add("renamed display symbol", model.objects["rig.arm.palm"].name, "palm")


def run_conformance(directory: Path = DEFAULT_FIXTURES) -> dict:
    from .evaluator import evaluate, preflight
    from .validator import validate

    manifest = load_manifest(directory)
    cases, baseline = [], None
    for case in manifest["cases"]:
        source = Source(materialize(case, directory), case["id"] + ".ok")
        expected = case["expected"]
        checks = Checks()
        diagnostic = None
        model = None
        phase = code = None
        syntax = "accept"
        try:
            ast = parse(source.text, source.filename)
            model = validate(ast, level=expected["requested_level"])
            preflight(model)
            outcome = "valid"
            if case["id"] == "P01":
                baseline = model
        except OntoKinError as exc:
            diagnostic = exc.diagnostic.to_dict(source)
            code = diagnostic["code"]
            phase = diagnostic["phase"]
            outcome = diagnostic["category"]
            if phase in {"lexical", "syntax"}:
                syntax = "reject"
        checks.add("source syntax", syntax, expected["syntax"])
        checks.add("result category", outcome, expected["outcome"])
        checks.add("diagnostic phase", phase, expected["phase"])
        checks.add("diagnostic code", code, expected["diagnostic_code"])
        if outcome == "valid" and expected["outcome"] == "valid":
            try:
                for observation in expected["observations"]:
                    if not isinstance(observation, dict):
                        continue  # These are checked explicitly below or by authored assertions.
                    sides = ["before", "after"] if observation["side"] == "before_and_after" else [observation["side"]]
                    for side in sides:
                        sample = evaluate(model, [observation["time_seconds"]], side=side)["samples"][0]
                        _observation(checks, sample, observation)
                _extra_observations(case["id"], model, checks, baseline)
            except OntoKinError as exc:
                checks.add("requested observations evaluate", exc.code, "success")
            except (KeyError, ValueError, StopIteration, TypeError) as exc:
                checks.add("observation mapping", str(exc), "all required fields available")
        if expected["outcome"] == "unsupported":
            try:
                retained = validate(parse(source.text), level="represented")
                checks.add("represented description retained", bool(retained.objects), True)
            except OntoKinError as exc:
                checks.add("represented description retained", exc.code, "valid")
        if diagnostic is not None:
            span = diagnostic["primary"]
            checks.add("diagnostic span ordered", 0 <= span["start_byte"] <= span["end_byte"] <= len(source.raw), True)
            try:
                source.raw[:span["start_byte"]].decode("utf-8")
                source.raw[:span["end_byte"]].decode("utf-8")
                boundary_valid = True
            except UnicodeDecodeError:
                boundary_valid = False
            checks.add("diagnostic span UTF-8 boundaries", boundary_valid, True)
            checks.add("diagnostic has repair guidance", bool(diagnostic["repair"] and diagnostic["repair"]["summary"]), True)
            if phase in {"admission", "transition"}:
                checks.add("preflight retains authored failure time", diagnostic["time"] is not None, True)
        cases.append({"id": case["id"], "title": case["title"], "source_revision": source.revision,
                      "status": "passed" if all(c["passed"] for c in checks.items) else "failed",
                      "requested_level": expected["requested_level"], "actual_outcome": outcome,
                      "checks": checks.items, "diagnostic": diagnostic})
    source_root = Path(__file__).resolve().parent
    digest = hashlib.sha256()
    for path in sorted(source_root.glob("*.py")):
        digest.update(path.name.encode() + b"\0" + path.read_bytes() + b"\0")
    passed = sum(c["status"] == "passed" for c in cases)
    return {
        "schema_version": "ontokin.conformance-report/0.1",
        "implementation_version": __version__, "profile": manifest["profile"],
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {"python": platform.python_version(),
                        "python_implementation": platform.python_implementation(),
                        "operating_system": platform.system()},
        "source_code_sha256": digest.hexdigest(),
        "fixture_manifest_sha256": hashlib.sha256((directory / "validation-cases.json").read_bytes()).hexdigest(),
        "scope": "Published 43 source cases, numerical/discrete observations, and explicit checks for the prose observations. This is bounded prototype evidence.",
        "full_core_conformance_certified": False,
        "summary": {"passed": passed, "failed": len(cases) - passed, "total": len(cases),
                    "assertions": sum(len(c["checks"]) for c in cases),
                    "expected_valid": manifest["case_counts"]["valid"],
                    "expected_invalid_or_conflicting": manifest["case_counts"]["invalid_or_conflicting"],
                    "expected_unsupported": manifest["case_counts"]["unsupported"]},
        "cases": cases,
        "agent_protocol_checks": {"executed": False,
                                  "deferred_case_ids": [c["id"] for c in manifest["agent_contract_checks"]],
                                  "reason": "No persistent agent editing/retry/transport service is implemented."},
        "numerical_limits": [
            "Fixture tolerances do not certify all correctly rounded transcendental operations.",
            "Binary64 spatial rotations approximate the language's exact represented rotations.",
            "Continuous trajectory overflow certification for arbitrary rotating mechanisms remains limited.",
        ],
    }
