"""Execute frozen impulse source oracles and audit identified release evidence.

The accepted corpus is an input, never a report. This runner independently
checks actual compiler/evaluator results; source tests are not counted from a
manifest. Missing external executions remain pending, and no finite release
certifies the complete product. The audit never reruns external applications.
"""
from __future__ import annotations

import argparse
import base64
from bisect import bisect_right
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import time

from . import construction_conformance as legacy
from . import surface_conformance as surface
from .bundle import ProgramBundle, load_bundle, load_file_manifest
from .construction import compile_construction
from .diagnostics import OntoKinError
from .evaluator import construct, evaluate, evaluate_prefix, preflight
from .program_diagnostics import diagnostic_dict

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "docs/language-design/impulse-v0.1"
ACCEPTANCE_SHA256 = "sha256:3b5c22b5a6c9a70b8e33ff568a0b4af963d530405d22f37dbe41516bea20b1f4"
MAPPING_SHA256 = "sha256:c6ae5083d94d9b2d018804499dff9f4a459a51c4f7342176f87cefc0524d3a63"
GATES = ("workflow", "destination", "browser", "regression", "ci")
SOURCE_IDS = tuple([f"P{i:02}" for i in range(1, 17)] + [f"N{i:02}" for i in range(1, 25)])
_require = legacy._require
_json_file = legacy._json_file
file_identity = legacy.file_identity
implementation_identity = legacy.implementation_identity
_canonical = surface._canonical
_identified = surface._identified
_nested = surface._nested
_gate = surface._gate
_NUMBER = r"-?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?"
_VECTORS = (
    "impulse_world_n_s", "application_point_self_m", "lever_arm_world_m",
    "application_point_world_m", "angular_impulse_world_n_m_s",
    "linear_velocity_before_world_m_per_s", "linear_velocity_after_world_m_per_s",
    "angular_velocity_before_world_rad_per_s", "angular_velocity_after_world_rad_per_s",
)
_RECORD_FIELDS = set(_VECTORS) | {"sequence_index", "source_location", "target_element_id", "target_path"}
_A03_TESTS = (
    "test_impulse_agent_protocol.ImpulseAgentProtocolTests.test_all_four_stores_keep_identical_request_ids_independent",
    "test_impulse_agent_protocol.ImpulseAgentProtocolTests.test_wrong_store_version_rejects_before_journal_or_ddl_changes",
    "test_impulse_agent.ImpulseAgentTests.test_run_provenance_rejects_wrong_revision_and_implementation",
    "test_impulse_cli.ImpulseCLITests.test_corrupt_or_directory_store_reports_controlled_selected_protocol_error",
)
_TIMES = tuple(Fraction(i, 4) for i in range(9))
_SPIN_BOUNDS = {"P01": 0, "P02": 5, "P03": 5, "P04": 7, "P07": 0,
                "P08": 7.5, "P09": 5, "P10": 3.75, "P11": 40}


def digest(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def load_manifest(directory: Path = FIXTURES) -> dict:
    directory = Path(directory)
    acceptance_path = directory / "acceptance.json"
    _require(file_identity(acceptance_path) == ACCEPTANCE_SHA256,
             "The adopted impulse expectations changed; do not retrofit the oracle.")
    acceptance = _json_file(acceptance_path)
    adoption = _json_file(directory / "adoption.json")
    _require(adoption["decision"] == "adopted-before-implementation"
             and adoption["acceptance_sha256"] == ACCEPTANCE_SHA256
             and adoption["execution_status"] == "unexecuted-at-adoption",
             "The exact impulse corpus lacks its prior adoption decision.")
    _require(tuple(c["id"] for c in acceptance["source_cases"]) == SOURCE_IDS
             and [g["id"] for g in acceptance["gates"]] == [f"I{i:02}" for i in range(1, 13)],
             "All 40 frozen source cases and I01-I12 must remain present exactly once.")
    mapping_path = directory / "conformance.json"
    _require(file_identity(mapping_path) == MAPPING_SHA256,
             "The reviewed impulse coverage mapping changed its versioned identity.")
    mapping = _json_file(mapping_path)
    _require(mapping["schema_version"] == "ontokin.impulse-conformance-map/0.1"
             and mapping["status"] == "predetermined_expectations_not_execution_results"
             and mapping["acceptance_sha256"] == ACCEPTANCE_SHA256,
             "Unknown impulse mapping or changed acceptance identity.")
    _require([g["id"] for g in mapping["cases"]] == [g["id"] for g in acceptance["gates"]],
             "The mapping omitted or reordered an adopted gate.")
    for actual, frozen in zip(mapping["cases"], acceptance["gates"]):
        _require(actual["source_case_ids"] == frozen["source_case_ids"]
                 and actual["operational_case_ids"] == frozen["operational_case_ids"],
                 "A mapped gate changed the frozen source or operational coverage.")
        names = actual["required_tests"]
        _require(isinstance(names, list) and len(names) == len(set(names))
                 and all(isinstance(n, str) and legacy._TEST_ID.fullmatch(n) for n in names),
                 "Mapped tests must be distinct concrete unittest methods.")
        _require(not set(actual["external_gates"]) - set(GATES), "Unknown impulse evidence gate.")
    _require(mapping["mandatory_native_fixtures"] == [c["id"] for c in acceptance["source_cases"] if c["delivery_required"]]
             and mapping["mandatory_browser_fixtures"] == ["P02", "P04", "P08", "P11"],
             "The mandatory native or browser corpus changed.")
    browser = next(c for c in acceptance["operational_cases"] if c["id"] == "D02")
    _require(mapping["mandatory_browser_captures"] == browser["captures"]
             and mapping["mandatory_browser_fixtures"] == browser["fixtures"]
             and mapping["mandatory_workflow_checks"] == [f"A{i:02}" for i in range(1, 6)],
             "The reviewed mapping removed a frozen capture or operational workflow requirement.")
    return {"mapping": mapping, "acceptance": acceptance, "directory": directory}


def fixture_bundle(case: dict, directory: Path = FIXTURES) -> ProgramBundle:
    path = legacy._repository_file(case["file_manifest"], directory)
    bundle = load_file_manifest(path)
    _require(bundle.program_revision == case["program_revision"]
             and bundle.manifest()["units"] == case["sources"],
             "Fixture bytes or program revision changed: " + case["id"])
    for event in case.get("source_impulse_statements", []):
        source = event["source_location"]
        _require(source["source_id"] == "entry" and source["source_revision"] == bundle.entry.revision
                 and bundle.entry.raw[source["start_byte"]:source["end_byte"]].decode("utf-8") == event["expected_text"],
                 "A frozen impulse statement lost its exact source span.")
    return bundle


def _finite_tree(value):
    if type(value) is float:
        _require(math.isfinite(value), "Successful output contains a nonfinite number.")
    elif isinstance(value, dict):
        for item in value.values():
            _finite_tree(item)
    elif isinstance(value, (tuple, list)):
        for item in value:
            _finite_tree(item)


def _finite(value, label):
    try:
        valid = type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        valid = False
    _require(valid, label + " must be a finite number.")
    return value


def _vector(value, count, label):
    _require(isinstance(value, (list, tuple)) and len(value) == count, label + " has the wrong vector shape.")
    return [_finite(v, label) for v in value]


def _close(actual, expected, tolerance: float, label: str, *, exact=False):
    if isinstance(expected, (list, tuple)):
        _require(isinstance(actual, (list, tuple)) and len(actual) == len(expected), label + " has the wrong shape.")
        for index, (a, b) in enumerate(zip(actual, expected)):
            _close(a, b, tolerance, f"{label}[{index}]", exact=exact)
    elif isinstance(expected, (int, float)) and not isinstance(expected, bool):
        a = _finite(actual, label)
        _require(a == expected if exact else abs(a - expected) <= tolerance,
                 f"{label}: expected {expected!r}, observed {actual!r}.")
    else:
        _require(actual == expected, f"{label}: expected {expected!r}, observed {actual!r}.")


def _orientation(actual, expected, tolerance=1e-9):
    a = _vector(actual, 4, "orientation")
    b = _vector(expected, 4, "reference orientation")
    na, nb = math.hypot(*a), math.hypot(*b)
    _require(abs(na - 1) <= 1e-12 and nb > 0, "Orientation must be a finite unit quaternion.")
    a, b = [x / na for x in a], [x / nb for x in b]
    if sum(x*y for x, y in zip(a, b)) < 0:
        b = [-x for x in b]
    error = 4*math.atan2(math.hypot(*(x-y for x, y in zip(a,b))), math.hypot(*(x+y for x,y in zip(a,b))))
    _require(error <= tolerance, f"Orientation geodesic error {error} exceeds {tolerance} radians.")


def _axis_quaternion(axis, angle):
    result = [math.cos(angle/2), 0., 0., 0.]
    result[axis+1] = math.sin(angle/2)
    return result


def _physical_inputs(case: dict, bundle: ProgramBundle, path: str):
    """Read only the fixed corpus's authored scalar literals, not compiled mass."""
    if path in {"carrier", "rack"}:
        return None
    source = bundle.entry.text
    mass, radius = 2., .5  # Exact pinned SphereProp defaults.
    if path.startswith('rack.props['):
        key = json.loads(path[path.index("[")+1:-1])
        for field, unit in (("masses", "kg"), ("radii", "m")):
            entries = re.findall(rf'{field}\s*=\s*keyed<[^>]+>\s*\{{([^}}]+)\}}', source)
            _require(entries, "The generated fixture lost its explicit scalar override.")
            match = re.search(rf'"{key}"\s*:\s*({_NUMBER})\[{unit}\]', entries[-1])
            _require(match is not None, "The generated scalar key is missing.")
            if field == "masses":
                mass = float(match[1])
            else:
                radius = float(match[1])
    else:
        for field, unit in (("body_mass", "kg"), ("body_radius", "m")):
            values = re.findall(rf'{field}\s*=\s*({_NUMBER})\[{unit}\]', source)
            if values:
                if field == "body_mass":
                    mass = float(values[-1])
                else:
                    radius = float(values[-1])
    inertia = float(Fraction(2,5)*Fraction(mass)*Fraction(radius)**2)
    return mass, radius, inertia


def _authored_vectors(event: dict):
    source = event["expected_text"]
    point = re.search(r'\bat\s+point\([^,]+,\s*(' + _NUMBER + r')\[m\],\s*(' + _NUMBER + r')\[m\],\s*(' + _NUMBER + r')\[m\]\)', source)
    _require(point is not None, "The fixed positive point is not its authored three-literal form.")
    p = [float(x) for x in point.groups()]
    vector = re.search(r'vector\(world,\s*(' + _NUMBER + r')\[N\*s\],\s*(' + _NUMBER + r')\[N\*s\],\s*(' + _NUMBER + r')\[N\*s\]\)', source)
    if vector:
        impulse = [float(x) for x in vector.groups()]
    else:
        helper = re.search(r'vectors\.along_y\((' + _NUMBER + r')\[N\*s\]\)', source)
        _require(helper is not None, "The fixed positive impulse helper changed.")
        impulse = [0., float(helper[1]), 0.]
    return impulse, p


def _check_projection(case, bundle, sample):
    time_value = Fraction(sample["time_seconds"])
    active = [e for e in case.get("source_impulse_statements", [])
              if Fraction(e["event_time_seconds"]) < time_value or
              (Fraction(e["event_time_seconds"]) == time_value and sample["side"] == "after")]
    for path, obj in sample["objects"].items():
        state = obj["impulses"]
        _require(set(state) == {"applied_count", "last_application_time_seconds", "last_applications"},
                 "The impulse projection omitted or added fields.")
        events = [e for e in active if e["target_path_spelling"] == path]
        latest = events[-1]["event_time_seconds"] if events else None
        last = [e for e in events if e["event_time_seconds"] == latest]
        _require(type(state["applied_count"]) is int and state["applied_count"] == len(events)
                 and state["last_application_time_seconds"] == latest
                 and len(state["last_applications"]) == len(last),
                 "An object lost or invented latest-boundary applications: " + path)
        for record, event in zip(state["last_applications"], last):
            _require(set(record) == _RECORD_FIELDS and record["sequence_index"] == event["sequence_index"]
                     and record["source_location"] == event["source_location"]
                     and record["target_element_id"] == obj["element_id"] and record["target_path"] == path,
                     "An application record lost exact statement/occurrence identity.")
            for name in _VECTORS:
                _vector(record[name], 3, name)
            impulse, point = _authored_vectors(event)
            _close(record["impulse_world_n_s"], impulse, 0, "authored impulse", exact=True)
            _close(record["application_point_self_m"], point, 0, "authored self point", exact=True)
            physical = _physical_inputs(case, bundle, path)
            _require(physical is not None, "An impulse record targets an object without its own sphere.")
            mass, _, inertia = physical
            lever, angular = record["lever_arm_world_m"], record["angular_impulse_world_n_m_s"]
            wanted_l = [float(Fraction(lever[(i+1)%3])*Fraction(impulse[(i+2)%3])
                              - Fraction(lever[(i+2)%3])*Fraction(impulse[(i+1)%3])) for i in range(3)]
            _close(angular, wanted_l, 1e-9, "world angular impulse")
            for before, after, applied, divisor in (
                ("linear_velocity_before_world_m_per_s", "linear_velocity_after_world_m_per_s", impulse, mass),
                ("angular_velocity_before_world_rad_per_s", "angular_velocity_after_world_rad_per_s", angular, inertia),
            ):
                expected = [float(Fraction(a)+Fraction(j)/Fraction(divisor)) for a,j in zip(record[before],applied)]
                _close(record[after], expected, 1e-9, after, exact=case["id"] == "P12")


def _verify_history_samples(case, samples):
    """Tie each retained application to its original pose and staged state."""
    for sample in samples.values():
        for path, state in sample["objects"].items():
            history = state["impulses"]
            records = history["last_applications"]
            if not records:
                continue
            time_value = Fraction(history["last_application_time_seconds"])
            _require((time_value, "after") in samples,
                     "Retained impulse history lacks its actual application-boundary inspection.")
            applied = samples[(time_value, "after")]["objects"][path]
            _require(_canonical(records) == _canonical(applied["impulses"]["last_applications"]),
                     "A retained impulse history copy changed after its application boundary.")
            before = samples.get((time_value, "before"))
            previous = None if before is None else before["objects"][path]
            for record in records:
                if previous is not None:
                    _close(record["linear_velocity_before_world_m_per_s"], previous["velocity_m_per_s"],
                           1e-9, "Retained staged incoming linear velocity", exact=case["id"] == "P12")
                    _close(record["angular_velocity_before_world_rad_per_s"], previous["angular_velocity_rad_per_s"],
                           1e-9, "Retained staged incoming angular velocity")
                lever = surface._rotate(record["application_point_self_m"], applied["orientation_wxyz"])
                point = [float(Fraction(a)+Fraction(b)) for a, b in zip(applied["position_m"], lever)]
                _close(record["lever_arm_world_m"], lever, 1e-9, "Retained application-time world lever")
                _close(record["application_point_world_m"], point, 1e-9,
                       "Retained application-time world point", exact=case["id"] == "P12")
                previous = {"velocity_m_per_s": record["linear_velocity_after_world_m_per_s"],
                            "angular_velocity_rad_per_s": record["angular_velocity_after_world_rad_per_s"]}
            # Some evaluation-only fixtures need no before-side inspection. The
            # fixed final state, each momentum equation and this complete chain
            # still constrain the first incoming velocity without inventing it.
            _close(previous["velocity_m_per_s"], applied["velocity_m_per_s"], 1e-9,
                   "Retained committed linear velocity", exact=case["id"] == "P12")
            _close(previous["angular_velocity_rad_per_s"], applied["angular_velocity_rad_per_s"], 1e-9,
                   "Retained committed angular velocity")


def compare_sample(actual: dict, expected: dict, *, exact_extreme=False):
    _require(actual["time_seconds"] == expected["time_seconds"] and actual["side"] == expected["side"],
             "The evaluator changed an exact requested timestamp or boundary side.")
    for path, fields in expected["objects"].items():
        obj = actual["objects"][path]
        for key, value in fields.items():
            if key == "orientation_wxyz":
                _orientation(obj[key], value)
            elif key == "impulses":
                _require(obj[key]["applied_count"] == value["applied_count"]
                         and obj[key]["last_application_time_seconds"] == value["last_application_time_seconds"]
                         and [r["sequence_index"] for r in obj[key]["last_applications"]] == value["sequence_indices"],
                         "A fixed count, retained boundary or statement order changed.")
            elif key == "pose_authority":
                _require(obj[key] == value, "Dynamic origin and trajectory anchor were conflated.")
            else:
                _close(obj[key], value, 1e-9, path + "." + key, exact=exact_extreme)


def _error_check(error, case, bundle):
    expected = case["expected"]
    result = diagnostic_dict(error.diagnostic, bundle)
    _require(result["code"] == expected["diagnostic_code"],
             f'{case["id"]}: expected {expected["diagnostic_code"]}, observed {result["code"]}.')
    _require(result["schema_version"] == "ontokin.diagnostic/0.2"
             and result["program_revision"] == bundle.program_revision
             and result["primary"] is not None, "A rejected source lost its diagnostic revision/span.")
    source = next(u for u in bundle.units if u.source_id == result["source_id"])
    primary = result["primary"]
    _require(result["source_revision"] == source.revision
             and 0 <= primary["start_byte"] < primary["end_byte"] <= len(source.raw),
             "A diagnostic identifies a stale or empty source span.")
    if expected["phase_group"] == "event_admission":
        event = next(e for e in case["source_impulse_statements"]
                     if e["event_time_seconds"] == expected["event_time_seconds"]
                     and e["sequence_index"] == expected["sequence_index"])
        _require(result["time"] == {"seconds": expected["event_time_seconds"], "side": "after"}
                 and result["details"]["sequence_index"] == expected["sequence_index"]
                 and primary["element_id"] == expected["target_element_id"]
                 and {k:primary[k] for k in event["source_location"]} == event["source_location"],
                 "An application failure lost its actual event time, sequence index, target or exact span.")
        if "diagnostic_category" in expected:
            _require(result["category"] == expected["diagnostic_category"], "A numerical failure changed category.")
    _finite_tree(result)
    return result


def _reported_sample(sample):
    # Raw compiler geometry retains typed immutable recipe leaves. The source
    # oracle report records physical state; independent destination evidence
    # checks the separately retained native geometry and exact source bytes.
    result={"time_seconds":sample["time_seconds"],"side":sample["side"],
            "objects":{path:{k:v for k,v in obj.items() if k not in {"geometry","physical"}}
                       for path,obj in sample["objects"].items()},
            "joints":sample["joints"],"actions":sample["actions"]}
    _finite_tree(result)
    _canonical(result)
    return result


def execute_source_case(case: dict, directory: Path = FIXTURES) -> dict:
    """Run one exact source fixture; no compiler-derived value is an oracle."""
    started = time.monotonic()
    record = {"id": case["id"], "status": "failed", "executed": False,
              "program_revision": case["program_revision"], "checks": [], "issues": []}
    try:
        bundle = fixture_bundle(case, directory)
        record["executed"] = True
        record["checks"].append("exact_source_manifest_and_statement_spans")
        is_negative = case["kind"] == "negative"
        try:
            compiler = compile_construction(bundle, level="constructed")
        except OntoKinError as error:
            _require(is_negative and case["expected"]["phase_group"] != "event_admission",
                     "The fixture failed construction before its required runtime behavior: " + str(error))
            record["diagnostic"] = _error_check(error, case, bundle)
            record["checks"].append("frozen_compile_diagnostic")
        else:
            model = compiler.model
            _require(model.profile == "impulse-0.1" and model.program_revision == bundle.program_revision
                     and model.source_manifest == bundle.manifest(), "The actual compiler selected another profile or source.")
            initial = construct(model)["initial_state"]
            if is_negative:
                _require(case["expected"]["phase_group"] == "event_admission",
                         "The compiler accepted a frozen compile-time rejection.")
                boundary = case["expected"]["event_time_seconds"]
                before = evaluate_prefix(model, boundary, side="before")
                actual = evaluate_prefix(model, model.duration)
                _require(before["failure"] is None and actual["failure"] is not None,
                         "The runtime negative did not fail at the admitted boundary.")
                record["diagnostic"] = _error_check(actual["failure"], case, bundle)
                _require(actual["valid_until_seconds"] == boundary and actual["valid_until_side"] == "before"
                         and actual["last_valid_state"] == before["last_valid_state"],
                         "A failed sequence leaked tentative changes or discarded its valid incoming state.")
                _check_projection(case, bundle, actual["last_valid_state"])
                try:
                    preflight(model)
                except OntoKinError as error:
                    _error_check(error, case, bundle)
                else:
                    raise ValueError("Timeline admission accepted a failing source sequence.")
                record["valid_until"] = {"time_seconds": boundary, "side": "before"}
                record["checks"] += ["frozen_event_diagnostic", "whole_boundary_rollback", "repeatable_admission_failure"]
            else:
                _check_projection(case, bundle, initial)
                expected = case["expected"]
                requests = [{"time_seconds": s["time_seconds"], "side": s["side"]} for s in expected["samples"]]
                boundaries = sorted({e["event_time_seconds"] for e in case.get("source_impulse_statements",[])}, key=Fraction)
                requests += [{"time_seconds": t, "side": side} for t in boundaries for side in ("before", "after")]
                output = evaluate(model, requests)
                _require(output["outcome"] == "valid" and output["profile"] == "impulse-0.1"
                         and len(output["samples"]) == len(requests), "The evaluator omitted requested source state.")
                _finite_tree(output)
                for sample, wanted in zip(output["samples"], expected["samples"]):
                    compare_sample(sample, wanted, exact_extreme=case["id"] == "P12")
                for sample in output["samples"]:
                    _require(set(sample["objects"]) == set(model.objects), "A snapshot omitted a source object.")
                    _check_projection(case, bundle, sample)
                    if case["id"] == "P03":
                        t = float(Fraction(sample["time_seconds"]))
                        after = max(0., t-1.)
                        q = surface._multiply_quaternions(_axis_quaternion(0,5*after), _axis_quaternion(1,math.pi/2))
                        _orientation(sample["objects"]["ball"]["orientation_wxyz"],q)
                extra = output["samples"][len(expected["samples"]):]
                for before, after in zip(extra[::2], extra[1::2]):
                    for path in model.objects:
                        b, a = before["objects"][path], after["objects"][path]
                        _close(a["position_m"],b["position_m"],1e-9,"impulse position continuity",exact=case["id"]=="P12")
                        _orientation(a["orientation_wxyz"], b["orientation_wxyz"])
                        current = a["impulses"]["last_applications"]
                        if a["impulses"]["last_application_time_seconds"] != after["time_seconds"]:
                            continue
                        previous_v, previous_w = b["velocity_m_per_s"], b["angular_velocity_rad_per_s"]
                        for applied in current:
                            _close(applied["linear_velocity_before_world_m_per_s"], previous_v, 1e-9,"staged incoming linear velocity",exact=case["id"]=="P12")
                            _close(applied["angular_velocity_before_world_rad_per_s"], previous_w, 1e-9,"staged incoming angular velocity")
                            lever = surface._rotate(applied["application_point_self_m"], a["orientation_wxyz"])
                            _close(applied["lever_arm_world_m"],lever,1e-9,"rotated authored self lever")
                            point = [float(Fraction(x)+Fraction(y)) for x,y in zip(a["position_m"],lever)]
                            _close(applied["application_point_world_m"],point,1e-9,"resolved world point",exact=case["id"]=="P12")
                            previous_v, previous_w = applied["linear_velocity_after_world_m_per_s"], applied["angular_velocity_after_world_rad_per_s"]
                        if current:
                            _close(a["velocity_m_per_s"],previous_v,1e-9,"committed linear velocity",exact=case["id"]=="P12")
                            _close(a["angular_velocity_rad_per_s"],previous_w,1e-9,"committed angular velocity")
                if "stable_element_ids" in expected:
                    _require([list(model.objects[p].element_id) for p in ('rack.props["first"]','rack.props["second"]')]
                             == expected["stable_element_ids"], "A generated occurrence was relabelled.")
                for path,obj in initial["objects"].items():
                    physical = _physical_inputs(case,bundle,path)
                    if physical is not None:
                        _close(obj["own_mass_kg"],physical[0],0,"authored own mass",exact=True)
                        _close(obj["inertia_kg_m2"],physical[2],0,"authored canonical sphere inertia",exact=True)
                if "kinetic_energy_after_j" in expected:
                    obj = extra[1]["objects"]["ball"]
                    mass,_,inertia = _physical_inputs(case,bundle,"ball")
                    energy = .5*mass*sum(v*v for v in obj["velocity_m_per_s"])+.5*inertia*sum(w*w for w in obj["angular_velocity_rad_per_s"])
                    _close(energy,expected["kinetic_energy_after_j"],1e-12,"independent kinetic energy")
                if case["id"] == "P05":
                    b,a = extra[0]["objects"]["ball"],extra[1]["objects"]["ball"]
                    for field in expected["exact_identity_fields"]:
                        keys=field.split(".")
                        bv,av=b,a
                        for key in keys:
                            bv,av=bv[key],av[key]
                        _require(_canonical(bv)==_canonical(av),"A zero impulse changed its exact state/anchor.")
                if "after_boundary" in expected:
                    sample = extra[1]
                    for path in ("carry","turn"):
                        _require(sample["actions"][path]["status"] == expected["after_boundary"][path], "Natural completion changed.")
                    _require(sample["joints"]["hold"]["status"] == expected["after_boundary"]["hold"],"Release did not commit.")
                    for field in ("velocity_m_per_s","angular_velocity_rad_per_s"):
                        _close(sample["objects"]["carrier"][field],expected["after_boundary"]["carrier_"+field],1e-9,"completed carrier "+field)
                record["samples"] = [_reported_sample(s) for s in output["samples"][:len(expected["samples"])]]
                record["boundary_times_seconds"] = output["boundary_times_seconds"]
                record["checks"] += ["predetermined_analytic_samples", "exact_latest_boundary_records", "source_driven_impulse_arithmetic",
                                     "pose_continuity_and_staged_order", "own_sphere_mass_inertia", "finite_json_state"]
        record["status"] = "passed"
    except (AssertionError, OSError, ValueError, TypeError, KeyError, IndexError, StopIteration, OverflowError, OntoKinError) as error:
        record["issues"].append(type(error).__name__ + ": " + str(error))
    record["elapsed_seconds"] = round(time.monotonic()-started,6)
    return record


def _inventory_path(value: str) -> bool:
    if surface._inventory_path(value):
        return True
    path = Path(value)
    return (len(path.parts)>=4 and path.parts[:2]==("docs","language-design")
            and path.parts[2] in {"impulse-v0.1","agent-v0.4"}
            and not {"evidence","validation","__pycache__","node_modules"}.intersection(path.parts)
            and path.suffix in {".py",".ok",".json",".md",".html",".mjs",".ebnf"})


def evidence_inventory() -> list[dict]:
    records={r["path"]:r for r in surface.evidence_inventory()}
    for directory in (ROOT/"docs/language-design/impulse-v0.1",ROOT/"docs/language-design/agent-v0.4"):
        if directory.is_dir():
            for path in directory.rglob("*"):
                relative=path.relative_to(ROOT).as_posix()
                if path.is_file() and _inventory_path(relative):
                    records[relative]={"path":relative,"sha256":file_identity(path)}
    return [records[k] for k in sorted(records)]


def run_full_suite() -> dict:
    contract=load_manifest()
    before,implementation=evidence_inventory(),implementation_identity()
    names=surface.discover_test_ids()
    execution=legacy._run_tests(names)
    stable=before==evidence_inventory() and implementation==implementation_identity()
    missing=sorted(set(contract["mapping"]["regression_required_test_ids"])-set(names))
    passed=surface._execution_passes(execution,names) and stable and not missing
    return {"schema_version":"ontokin.unittest-execution/0.1","executed":True,
            "generated_at_utc":datetime.now(timezone.utc).isoformat(),"implementation":implementation,
            "evidence_files":before,"evidence_inventory_sha256":surface.inventory_identity(before),
            "expected_test_ids":names,"test_execution":execution,"evidence_stable_during_run":stable,
            "missing_frozen_regression_test_ids":missing,
            "summary":{"total":len(names),"passed":sum(r["status"]=="passed" for r in execution["tests"]),"all_passed":passed},
            "full_product_conformance_certified":False}


def _execution_passes(execution, names):
    if names:
        return surface._execution_passes(execution, names)
    return (execution.get("unique_required") == execution.get("tests_run") == 0
            and execution.get("tests") == [] and execution.get("outcomes") == {}
            and not execution.get("loader_errors") and not execution.get("fixture_errors")
            and not execution.get("unexpected_test_records"))


def _expected_objects(fixture):
    """Fixed visible scalars from the adopted library, never exporter input."""
    generated = fixture in {"P08", "P09", "P10"}
    paths = ['rack.props["first"]', 'rack.props["second"]'] if generated else ["ball"]
    shapes = []
    for path in paths:
        keys = ["rack", "props", "first" if "first" in path else "second"] if generated else ["ball"]
        second = generated and keys[-1] == "second"
        shapes.append({"path": path, "element_id": ["impulse-demo", "demo", *keys],
            "physical_kind": "sphere_body", "body_mass_kg": 4. if second or fixture == "P09" else 2.,
            "body_radius_m": 1. if fixture == "P10" and not second else .5,
            "sections": [
                {"key": "foot", "station_m": 0., "center_xy_m": [0., 0.], "radii_xy_m": [.5, .35], "region": "clay"},
                {"key": "neck", "station_m": 1., "center_xy_m": [.15, 0.], "radii_xy_m": [.3, .2], "region": "paint"},
                {"key": "tip", "station_m": 1.5, "center_xy_m": [.15, 0.], "radii_xy_m": [.2, .1], "region": "paint"}],
            "facets": 16, "caps": "flat", "local_position_m": [0., 0., .1],
            "local_rotation_wxyz": [1., 0., 0., 0.],
            "materials": {"clay": {"rgba": [.6, .3, .2, 1.], "metallic": 0., "roughness": .8},
                          "paint": {"rgba": [.1, .4, .8, 1.], "metallic": .2, "roughness": .4}},
            "expected": {"triangles": 96, "vertices": 288, "triangles_per_region": {"clay": 48, "paint": 48}},
            "motion": {"kind": "impulse_fixture", "fixture": fixture}})
    empty = []
    for path in (["rack"] if generated else ["carrier"] if fixture == "P04" else []):
        empty.append({"path": path, "element_id": ["impulse-demo", "demo", path],
                      "motion": {"kind": "impulse_fixture", "fixture": fixture}})
    return {"shapes": shapes, "empty_objects": empty}


def _expected_pose(fixture, path, seconds):
    """Closed-form world pose; no evaluator or retained oracle values enter."""
    t, dt = float(seconds), max(0., float(seconds)-1.)
    p, q = [0., 0., 0.], [1., 0., 0., 0.]
    if fixture == "P04":
        if path == "carrier":
            p, q = [min(t, 1.), 0., 0.], _axis_quaternion(2, -2+2*min(t, 1.))
        elif t < 1:
            a = -2+2*t
            p, q = [t+.5*math.cos(a), .5*math.sin(a), 0.], _axis_quaternion(2, a)
        else:
            p, q = [1.5+dt, 2*dt-5*dt*dt, 0.], _axis_quaternion(2, 7*dt)
    elif fixture in {"P08", "P09", "P10"}:
        if path != "rack":
            first = path == 'rack.props["first"]'
            speed = (.5 if fixture == "P09" else 1.) if first else .5
            spin = {"P08": 5., "P09": 2.5, "P10": 1.25}[fixture] if first else 2.5
            p, q = [0. if first else 3., speed*dt, 0.], _axis_quaternion(2, spin*dt)
    elif fixture == "P01":
        p = [3*dt, 0., 0.]
    elif fixture == "P02":
        p, q = [0., dt, 0.], _axis_quaternion(2, 5*dt)
    elif fixture == "P03":
        p, q = [0., dt, 0.], surface._multiply_quaternions(_axis_quaternion(0, 5*dt), _axis_quaternion(1, math.pi/2))
    elif fixture == "P07":
        p = [0., 5-5*t*t if t < 1 else -5*dt*dt, 0.]
    else:
        _require(fixture == "P11", "No independent delivery motion was adopted for " + fixture)
        p, q = [0., 8*dt, 0.], _axis_quaternion(2, 40*dt)
    return {"position_m": p, "orientation_wxyz": q}


def _workflow_snapshots(report, root):
    snapshots = {}
    _require(isinstance(report["snapshots"], list) and len(report["snapshots"]) <= 1000,
             "The retained workflow snapshot set exceeds its fixed audit bound.")
    for snapshot in report["snapshots"]:
        program = load_bundle(_json_file(_nested(snapshot["bundle_file"], snapshot["bundle_sha256"], root)))
        key = (snapshot["project_id"], snapshot["program_revision"])
        _require(key not in snapshots and key[1] == program.program_revision,
                 "Workflow snapshots must identify unique actual program bytes.")
        source_manifest = _nested(snapshot["source_manifest_file"], snapshot["source_manifest_sha256"], root)
        _require(_json_file(source_manifest) == program.manifest(), "A workflow source manifest changed.")
        units = {u["source_id"]: u for u in snapshot["units"]}
        _require(len(units) == len(snapshot["units"]) == len(program.units), "A snapshot lost or duplicated a source unit.")
        for unit in program.units:
            item = units[unit.source_id]
            source = _nested(item["file"], item["sha256"], root)
            _require(source.read_bytes() == unit.raw and item["source_revision"] == unit.revision
                     and item["filename"] == unit.filename and item["byte_length"] == len(unit.raw)
                     and item.get("package_id") == unit.package_id and item.get("version") == unit.version,
                     "Retained source identities disagree with their exact UTF-8 bytes.")
        _require(type(snapshot["accepted_once"]) is bool, "accepted_once must be an observed Boolean.")
        snapshots[key] = (program, snapshot["accepted_once"])
    return snapshots


def _cursor_payload(token):
    _require(isinstance(token, str) and 0 < len(token) <= 65536, "A retained native cursor exceeds its wire bound.")
    raw = base64.b64decode(token + "="*(-len(token) % 4), altchars=b"-_", validate=True)
    _require(len(raw) > 32, "A cursor lacks its signature and complete context.")
    result = json.loads(raw[32:].decode("utf-8"))
    _require(set(result) == {"context", "offset"} and type(result["offset"]) is int and result["offset"] >= 0,
             "A retained cursor lost its versioned context or offset.")
    return result


def _has_code(response, code):
    return ((response.get("protocol_error") or {}).get("code") == code
            or any(d.get("code") == code for d in response.get("diagnostics", [])))


def _collect_mesh_page(request, response, pages, implementation):
    page = response["result"]
    _require(page["schema_version"] == "ontokin.surface-mesh-page/0.1" and page["profile"] == "surface-0.1"
             and "entry_profile" not in page and page["program_revision"] == request["program_revision"]
             and page["element_id"] == request["element_id"]
             and page["coordinate_system"] == "carrier_local_after_placement/0.1"
             and page["ordering"] == "native_triangle_ordinal/0.1"
             and response["requested_level"] is None and response["achieved_level"] == "constructed"
             and response["run_id"] is None, "A mesh page changed its inherited capability or source identity.")
    count = page["returned_triangles"]
    _require(type(count) is int and 0 <= count <= request["count"] <= 256
             and len(page["positions_m"]) == len(page["normals"]) == 3*count
             and len(page["region_keys"]) == len(page["source_triangle_ordinals"]) == len(page["triangles"]) == count
             and page["triangles"] == [[3*i, 3*i+1, 3*i+2] for i in range(count)],
             "A mesh page split, omitted or silently shortened its complete triangles.")
    expected_context = {"project_id": request["project_id"], "operation": "surface.mesh_page",
        **{k: page[k] for k in ("program_revision", "element_id", "profile", "region", "geometry_sha256", "ordering", "coordinate_system")},
        "implementation": implementation, "protocol": "ontokin.agent/0.4", "entry_profile": "impulse-0.1"}
    _require(page["region"] == request.get("region") and surface.SHA.fullmatch(page["geometry_sha256"]),
             "A page changed its fixed filter or geometry identity.")
    if request.get("cursor") is not None:
        cursor = _cursor_payload(request["cursor"])
        _require(cursor == {"context": expected_context, "offset": page["offset"]}, "A successful page crossed its signed context.")
    else:
        _require(page["offset"] == 0, "A first page skipped native triangles.")
    more = page["offset"]+count < page["filtered_triangles"]
    _require(response["truncated"] is more and bool(response["next_cursor"]) is more,
             "Native mesh continuation hides incomplete output.")
    if more:
        _require(count > 0 and _cursor_payload(response["next_cursor"]) == {
            "context": expected_context, "offset": page["offset"]+count}, "The next cursor changed context or failed to advance.")
    if page["region"] is None:
        key = (request["project_id"], request["program_revision"], tuple(page["element_id"]))
        collected = pages.setdefault(key, {"triangles": {}, "total": page["total_triangles"], "digest": page["geometry_sha256"]})
        _require(collected["total"] == page["total_triangles"] == page["filtered_triangles"]
                 and collected["digest"] == page["geometry_sha256"]
                 and page["source_triangle_ordinals"] == list(range(page["offset"], page["offset"]+count)),
                 "An immutable native page changed count, topology order or digest.")
        for i, ordinal in enumerate(page["source_triangle_ordinals"]):
            face = (page["region_keys"][i], page["positions_m"][3*i:3*i+3], page["normals"][3*i:3*i+3])
            previous = collected["triangles"].setdefault(ordinal, face)
            _require(previous == face, "A repeated immutable mesh triangle changed.")


def _verify_workflow(record, evidence_root, implementation, contract, context, test_execution):
    path = _identified(record, evidence_root)
    report, root = _json_file(path), path.parent
    _require(report["schema_version"] == "ontokin.impulse-agent-demo/0.1" and report["status"] == "passed"
             and report["implementation"] == implementation and report.get("error") is None,
             "The retained impulse workflow did not finish under the current implementation.")
    _require(report["builder_sha256"] == file_identity(ROOT/"tools/build_impulse_agent_demo.py")
             and report["oracle_builder_sha256"] == file_identity(ROOT/"tools/impulse_oracles.py")
             and report["acceptance_manifest_sha256"] == ACCEPTANCE_SHA256,
             "The workflow builder or frozen source corpus is stale.")
    snapshots = _workflow_snapshots(report, root)
    from .program_protocol import bind
    from .agent_protocol import ProtocolError
    protocol = bind("ontokin.agent/0.4")
    exchanges, attempts, accepted, accepted_once, pages, runs = {}, [], {}, set(), {}, {}
    previous_sequence = -1
    _require(isinstance(report["exchanges"], list) and 0 < len(report["exchanges"]) <= 10000,
             "The workflow requires a finite actual exchange ledger.")
    for item in report["exchanges"]:
        _require(type(item["sequence"]) is int and item["sequence"] > previous_sequence, "Exchange sequence is missing or ambiguous.")
        previous_sequence = item["sequence"]
        request = _json_file(_nested(item["request_file"], item["request_sha256"], root))
        response = _json_file(_nested(item["response_file"], item["response_sha256"], root))
        try:
            protocol.validate_request(request)
        except ProtocolError as error:
            raise ValueError("A retained request violates the actual selected Agent/0.4 protocol: "+str(error)) from error
        project, operation = request["project_id"], request["operation"]
        key = (project, request["request_id"])
        _require((project, request["request_id"], operation) == (item["project_id"], item["request_id"], item["operation"])
                 and response["schema_version"] == "ontokin.agent/0.4" and response["operation"] == operation
                 and response["project_id"] == project and response["request_id"] == request["request_id"],
                 "An exchange relabelled its selected protocol, project, request or operation.")
        attempts.append((item["sequence"], request, response))
        if key in exchanges:
            old_request, old_response = exchanges[key]
            if request == old_request:
                _require(response == old_response, "An identical request retry changed its cached result.")
            else:
                _require(response["status"] in {"failed", "rejected"}
                         and _has_code(response, "OKL-E-REQUEST-ID")
                         and response.get("accepted_program_revision") == accepted.get(project),
                         "Changed-payload request reuse did not preserve the accepted source.")
            continue  # A retry cannot replay its old source/head transaction.
        exchanges[key] = (request, response)
        candidate = None
        if operation == "create":
            candidate = load_bundle(request["bundle"])
        elif operation == "edit" and request["expected_program_revision"] == accepted.get(project):
            _require(not request.get("module_changes"), "The fixed source workflow cannot replace its pinned libraries.")
            candidate = surface._patched_program(snapshots[(project, request["expected_program_revision"])][0], request["patches"])
        if candidate is not None and response.get("program_revision") is not None:
            _require(candidate.program_revision == response["program_revision"]
                     and snapshots[(project, candidate.program_revision)][0].to_payload() == candidate.to_payload(),
                     "An acceptance/rejection names source bytes different from the requested patch.")
        if response["status"] == "succeeded":
            _require(response["result"].get("implementation") == implementation, "A successful response uses stale runtime bytes.")
            if operation in {"create", "edit"}:
                _require(candidate is not None and request["expected_program_revision"] == accepted.get(project),
                         "A stale or absent source candidate advanced the accepted head.")
                accepted[project] = candidate.program_revision
                accepted_once.add((project, candidate.program_revision))
            elif operation in {"surface.mesh_page", "export", "evaluate", "inspect"}:
                _require((project, request["program_revision"]) in accepted_once,
                         "A never-accepted source acquired readable state, mesh or delivery.")
            run = response["result"].get("run_state")
            if run is not None:
                _require(run["implementation"] == implementation and run["program_revision"] == response["program_revision"]
                         and run["status"] == "ready" and run.get("failure") is None,
                         "A successful run has stale provenance or a failed prefix.")
                runs[(project, response["run_id"])] = run
            if operation == "surface.mesh_page":
                _collect_mesh_page(request, response, pages, implementation)
            if operation == "inspect" and request.get("run_id"):
                run = runs[(project, request["run_id"])]
                _require(run["program_revision"] == request["program_revision"]
                         and response["run_id"] == request["run_id"], "Inspection reused a run from another source revision.")
                for item_ in response["result"]["items"]:
                    if "state" not in item_:
                        continue
                    state = item_["state"]
                    wanted_time = request.get("time")
                    if wanted_time is not None:
                        _require(Fraction(state["time_seconds"]) == Fraction(wanted_time["seconds"])
                                 and state["side"] == wanted_time["side"], "An inspection changed its exact clock or side.")
                    _require(state["available"] is True and state["program_revision"] == run["program_revision"]
                             and state["run_id"] == request["run_id"] and state["element_id"] == item_["element_id"]
                             and (Fraction(state["time_seconds"]), state["side"] == "after") <=
                                 (Fraction(run["valid_until_seconds"]), run["valid_until_side"] == "after"),
                             "A state inspection exceeds its valid run or loses occurrence identity.")
        _require(response.get("accepted_program_revision") == accepted.get(project), "A response changed the observed accepted head.")
    _require(set(snapshots) >= accepted_once, "A successful accepted source snapshot is missing.")
    for key, (_, claimed) in snapshots.items():
        _require(claimed is (key in accepted_once), "accepted_once was inferred from retention instead of actual successful admission.")

    cases = {c["id"]: c for c in contract["acceptance"]["source_cases"]}
    fixtures = {f["fixture"]: f for f in report["fixtures"]}
    _require(len(fixtures) == len(report["fixtures"]) == 16 and set(fixtures) == set(SOURCE_IDS[:16]),
             "Every one of the 16 positive source fixtures requires its actual Agent workflow.")
    samples = {}
    for fixture, item in fixtures.items():
        case, project, revision = cases[fixture], item["project_id"], item["program_revision"]
        program = fixture_bundle(case, contract["directory"])
        _require(revision == program.program_revision and snapshots[(project, revision)][0].to_payload() == program.to_payload()
                 and (project, revision) in accepted_once, "A workflow fixture differs from the adopted source closure.")
        created, create_response = exchanges[(project, item["create_request_id"])]
        base_case = cases["P08"] if fixture in {"P09", "P10"} else case
        base = fixture_bundle(base_case, contract["directory"])
        _require(created["operation"] == "create" and create_response["status"] == "succeeded"
                 and load_bundle(created["bundle"]).to_payload() == base.to_payload(), "A fixture was not created from its exact fixed source.")
        accepted_request, accepted_response = exchanges[(project, item["accepted_request_id"])]
        _require(accepted_response["status"] == "succeeded" and accepted_response["program_revision"] == revision,
                 "The claimed accepted fixture lacks actual successful admission.")
        if fixture in {"P09", "P10"}:
            _require(item["edit_request_ids"] == [item["accepted_request_id"]] and accepted_request["operation"] == "edit"
                     and accepted_request["expected_program_revision"] == base.program_revision
                     and len(accepted_request["patches"]) == 1, "A01 requires a single actual scoped source patch from P08.")
            patch = accepted_request["patches"][0]
            old, new = ("2", "4") if fixture == "P09" else ("0.5", "1")
            _require(patch["source_id"] == "entry" and patch["source_revision"] == base.entry.revision
                     and patch["element_id"] == ["impulse-demo", "demo", "rack"]
                     and patch["expected_text"] == old and patch["replacement"] == new
                     and surface._patched_program(base, [patch]).to_payload() == program.to_payload(),
                     "A mass/radius repair changed a sibling, event, library or more than its one fixed scalar.")
            accepted_sequence = min(sequence for sequence, request, result in attempts
                                    if request == accepted_request and result == accepted_response)
            scoped = [result for sequence, request, result in attempts if sequence < accepted_sequence
                      and request["project_id"] == project
                      and request["operation"] == "inspect" and request["program_revision"] == base.program_revision
                      and result["status"] == "succeeded" and request["request_id"] in item["inspect_request_ids"]]
            source_identity = {"source_id": "entry", "source_revision": base.entry.revision}
            _require(any(entry.get("element_id") == patch["element_id"]
                and entry.get("source", {}).get("program_revision") == base.program_revision
                and all(entry.get("source", {}).get(k) == v for k, v in source_identity.items())
                and any(all(span.get(k) == v for k, v in source_identity.items())
                        and span.get("file") == base.entry.filename
                        and span["start_byte"] <= patch["start_byte"] < patch["end_byte"] <= span["end_byte"]
                        for span in entry.get("source", {}).get("writable_spans", []))
                for result in scoped for entry in result["result"]["items"]),
                "The source repair lacks an exact-source writable occurrence inspection before its patch.")
        else:
            _require(item["accepted_request_id"] == item["create_request_id"] and item["edit_request_ids"] == [],
                     "A direct fixed fixture acquired an undocumented source edit.")
        evaluated = [exchanges[(project, identity)] for identity in item["evaluate_request_ids"]]
        _require(any(q["operation"] == "evaluate" and q["program_revision"] == revision and r["status"] == "succeeded"
                     for q, r in evaluated), "A fixture was not actually evaluated by its selected Agent.")
        observed = {}
        for identity in item["inspect_request_ids"]:
            request, response = exchanges[(project, identity)]
            _require(request["operation"] == "inspect", "A state evidence ID names another operation.")
            if request["program_revision"] != revision or "state" not in request["fields"] or request.get("frame", "world") != "world":
                continue
            _require(response["status"] == "succeeded" and not response["truncated"]
                     and response["result"]["total"] == len(response["result"]["items"]), "A fixed state inspection was rejected or truncated.")
            key = (Fraction(request["time"]["seconds"]), request["time"]["side"])
            sample = {"time_seconds": request["time"]["seconds"], "side": key[1],
                      "objects": {e["path"]: e["state"] for e in response["result"]["items"]}}
            paths = {o["path"] for group in _expected_objects(fixture).values() for o in group}
            _require(len(sample["objects"]) == len(response["result"]["items"]) and set(sample["objects"]) == paths,
                     "A fixed state inspection omitted an actual carrier or source object.")
            _check_projection(case, program, sample)
            _require(observed.setdefault(key, sample) == sample, "An immutable run returned contradictory state.")
        for expected in case["expected"]["samples"]:
            key = (Fraction(expected["time_seconds"]), expected["side"])
            _require(key in observed, "A workflow omitted a frozen exact-time state inspection: " + fixture)
            compare_sample(observed[key], expected, exact_extreme=fixture == "P12")
        _verify_history_samples(case, observed)
        if case["delivery_required"]:
            _require({(t, "after") for t in _TIMES} <= set(observed), "A delivered source lacks the fixed quarter-second pose probes.")
            for sample in observed.values():
                for path_, state in sample["objects"].items():
                    expected = _expected_pose(fixture, path_, Fraction(sample["time_seconds"]))
                    _close(state["position_m"], expected["position_m"], 1e-9, "Independent Agent world pose")
                    _orientation(state["orientation_wxyz"], expected["orientation_wxyz"])
            for shape in _expected_objects(fixture)["shapes"]:
                page = pages[(project, revision, tuple(shape["element_id"]))]
                faces = surface._analytic_triangles(shape)
                _require(page["total"] == len(faces) and set(page["triangles"]) == set(range(len(faces))),
                         "A delivered occurrence lacks complete native source mesh-page evidence.")
                for ordinal, (region, points, normal) in enumerate(faces):
                    actual_region, actual_points, normals = page["triangles"][ordinal]
                    _require(actual_region == region, "A source mesh page changed a material region.")
                    _close(actual_points, points, 1e-10, "Independent binary64 surface-page positions")
                    _close(normals, [normal]*3, 1e-10, "Independent binary64 surface-page normals")
                if fixture in {"P09", "P10"}:
                    _require(pages[(project, base.program_revision, tuple(shape["element_id"]))]["triangles"] == page["triangles"],
                             "A physical scalar repair changed its visual native triangles.")
        samples[fixture] = observed
    checks = {c["id"]: c for c in report["checks"]}
    _require(len(checks) == len(report["checks"]) == 5 and set(checks) == set(contract["mapping"]["mandatory_workflow_checks"]),
             "A required operational workflow scenario is absent or duplicated.")
    for name, check in checks.items():
        _require(check["evidence_request_ids"] and set(check["evidence_request_ids"]) <= {q["request_id"] for _, q, _ in attempts},
                 "A workflow scenario cites no actual retained exchange.")
        _require(check["status"] == ("partial" if name == "A03" else "passed"),
                 "A workflow step did not complete its declared part, or claimed unexecuted A03 store/CLI evidence.")
    _verify_operational_workflow(checks, attempts, exchanges, snapshots, fixtures, samples, implementation, test_execution, cases)
    artifacts = _workflow_artifacts(report, exchanges, snapshots, root, contract["mapping"])
    context["workflow"] = {"artifacts": artifacts, "snapshots": snapshots, "exchanges": exchanges,
                           "fixtures": fixtures, "samples": samples}
    return {"workflow_sha256": file_identity(path), "exchange_attempts": len(attempts), "unique_requests": len(exchanges),
            "snapshots": len(snapshots), "accepted_revisions": len(accepted_once), "positive_fixtures": len(fixtures),
            "retrieved_artifacts": len(artifacts), "checks": list(checks),
            "A03_basis": {"workflow_status": "partial", "current_executed_test_ids": list(_A03_TESTS)}}


def _workflow_artifacts(report, exchanges, snapshots, root, mapping):
    artifacts = {}
    for item in report["artifacts"]:
        fixture, project, revision = item["fixture"], item["project_id"], item["program_revision"]
        _require(fixture not in artifacts and snapshots[(project, revision)][1] is True,
                 "A delivered artifact is duplicated or belongs to a never-accepted source.")
        request, response = exchanges[(project, item["export_request_id"])]
        exported = response["result"]
        _require(request["operation"] == "export" and request["program_revision"] == revision
                 and request["destination"] == "ontokin.glb/0.4" and response["status"] == "succeeded"
                 and response["program_revision"] == revision and exported["artifact_id"] == item["artifact_id"]
                 and exported["sha256"] == item["artifact_sha256"] and exported["total_bytes"] == item["byte_length"],
                 "The delivered artifact lacks its exact successful Agent/0.4 export.")
        raw = bytearray()
        _require(item["retrieval_request_ids"] and len(item["retrieval_request_ids"]) == len(set(item["retrieval_request_ids"])),
                 "Artifact retrieval is absent or repeats a chunk request.")
        for identity in item["retrieval_request_ids"]:
            request, response = exchanges[(project, identity)]
            part = response["result"]
            chunk = base64.b64decode(part["data_base64"], validate=True)
            _require(request["operation"] == "artifact" and request["artifact_id"] == item["artifact_id"]
                     and response["status"] == "succeeded" and part["offset"] == request.get("offset", 0) == len(raw)
                     and len(chunk) <= request.get("max_bytes", 65536)
                     and part["next_offset"] == (None if len(raw)+len(chunk) == item["byte_length"] else len(raw)+len(chunk))
                     and part["total_bytes"] == item["byte_length"] and part["sha256"] == item["artifact_sha256"]
                     and response["program_revision"] == revision and part["artifact_provenance"]["program_revision"] == revision,
                     "Artifact chunks crossed source identity or lost bytes/order.")
            raw.extend(chunk)
            _require(len(raw) <= 67108864, "The retained artifact exceeds its fixed audit byte cap.")
        _require(len(raw) == item["byte_length"] and digest(raw) == item["artifact_sha256"]
                 and legacy._repository_file(fixture+"/scene.glb", root).read_bytes() == raw,
                 "The independently validated GLB is not the exact retrieved Agent artifact.")
        artifacts[fixture] = item
    _require(set(artifacts) == set(mapping["mandatory_native_fixtures"]), "Every adopted delivery fixture must be exported and retrieved once.")
    return artifacts


def _verify_operational_workflow(checks, attempts, exchanges, snapshots, fixtures, samples, implementation, test_execution, cases):
    """Require concrete source edits, failed candidates, cursors and frames."""
    for name in ("P09", "P10"):
        _require(fixtures[name]["accepted_request_id"] in checks["A01"]["evidence_request_ids"],
                 "A01 did not cite its actual scoped mass/radius patch.")
    project, original = fixtures["P01"]["project_id"], cases["P01"]["program_revision"]
    invalid = cases["N19"]["program_revision"]
    _require((project, invalid) in snapshots and snapshots[(project, invalid)][1] is False
             and snapshots[(project, invalid)][0].to_payload() == fixture_bundle(cases["N19"]).to_payload(),
             "A02 omitted or accepted the exact frozen N19 candidate.")
    chosen = [a for a in attempts if a[1]["project_id"] == project and a[1]["request_id"] in checks["A02"]["evidence_request_ids"]]
    rejected = [a for a in chosen if a[1]["operation"] == "edit" and a[2].get("program_revision") == invalid
                and a[2]["status"] in {"failed", "rejected"} and a[1].get("requested_level") == "evaluated"]
    _require(len(rejected) == 2 and rejected[0][1:] == rejected[1][1:], "A02 lacks the exact identical failed-admission retry.")
    response = rejected[0][2]
    expected = cases["N19"]["expected"]
    event = next(e for e in cases["N19"]["source_impulse_statements"] if e["sequence_index"] == expected["sequence_index"])
    _require(any(d["code"] == expected["diagnostic_code"] and d["program_revision"] == invalid
                 and d["time"] == {"seconds": "1", "side": "after"}
                 and d["details"]["sequence_index"] == expected["sequence_index"]
                 and {k: d["primary"][k] for k in event["source_location"]} == event["source_location"]
                 and d["primary"]["element_id"] == expected["target_element_id"] for d in response["diagnostics"]),
             "A02 lacks the frozen source-local failed-sequence diagnostic.")
    run = response["result"]["run_state"]
    _require(run["candidate_only"] is True and run["status"] == "failed" and run["implementation"] == implementation
             and (run["valid_until_seconds"], run["valid_until_side"]) == ("1", "before")
             and response["accepted_program_revision"] == original, "A02 published a failed candidate prefix as accepted state.")
    ball = run["last_valid_state"]["objects"]["ball"]
    _require(ball["velocity_m_per_s"] == [0, 0, 0] and ball["angular_velocity_rad_per_s"] == [0, 0, 0]
             and ball["impulses"] == {"applied_count": 0, "last_application_time_seconds": None, "last_applications": []}
             and ball["pose_authority"]["trajectory_anchor_seconds"] == "0", "A02 failed to roll back the earlier staged impulse.")
    model = compile_construction(snapshots[(project, invalid)][0], level="constructed").model
    before = evaluate_prefix(model, "1", side="before")["last_valid_state"]
    _require(_reported_sample(run["last_valid_state"]) == _reported_sample(before),
             "A02 changed another object, action or joint while rolling back the failed sequence.")
    _require(any(a[1]["request_id"] == rejected[0][1]["request_id"] and a[1] != rejected[0][1]
                 and _has_code(a[2], "OKL-E-REQUEST-ID") for a in chosen),
             "A02 omitted changed-payload request-ID conflict handling.")
    for operation in ("surface.mesh_page", "evaluate", "export"):
        _require(any(q["operation"] == operation and q.get("program_revision") == invalid
                     and r["status"] in {"failed", "rejected"} and _has_code(r, "OKL-E-REVISION")
                     for _, q, r in chosen), "A never-accepted source lacks its concrete read/delivery rejection.")
    later = [(s, q, r) for s, q, r in chosen if q["operation"] == "edit" and r["status"] == "succeeded"]
    _require(len(later) == 1 and later[0][2]["program_revision"] != original, "A02 omitted a later accepted source revision.")
    later_sequence = later[0][0]
    for operation in ("inspect", "surface.mesh_page"):
        _require(any(s > later_sequence and q["operation"] == operation and q["program_revision"] == original and r["status"] == "succeeded"
                     for s, q, r in chosen), "A02 omitted successful historical accepted-once inspection.")
    detail = checks["A03"]["details"]
    _require(detail["protocol"] == "ontokin.agent/0.4" and detail["store_filename"] == "impulse-program-agent.sqlite3"
             and detail["store_schema"] == "ontokin.impulse-program-agent-store/0.1"
             and detail["required_test_ids"] == list(_A03_TESTS), "A03 changed its mandatory versioned store/CLI test bindings.")
    _require_a03_execution(test_execution)
    _require(any(q["request_id"] in checks["A03"]["evidence_request_ids"] and q["operation"] == "inspect"
                 and q.get("run_id") and r["status"] in {"failed", "rejected"}
                 and _has_code(r, "OKL-E-SAMPLE")
                 for _, q, r in attempts), "A03 has no actual wrong-revision run provenance rejection.")
    context_requests = [(q, r) for _, q, r in attempts if q["request_id"] in checks["A04"]["evidence_request_ids"]]
    good = [(q, r) for q, r in context_requests if q["operation"] == "surface.mesh_page" and r["status"] == "succeeded" and r["next_cursor"]]
    _require(good, "A04 never obtained an actual signed native cursor.")
    base = _cursor_payload(good[0][1]["next_cursor"])
    changed = set()
    for request, response in context_requests:
        if request["operation"] != "surface.mesh_page" or not request.get("cursor") or response["status"] == "succeeded":
            continue
        probe = _cursor_payload(request["cursor"])
        differences = {k for k in base["context"] if probe["context"].get(k) != base["context"][k]}
        _require(len(differences) == 1 and probe["offset"] == base["offset"]
                 and (response.get("protocol_error") or {}).get("code") == "OKL-E-REVISION",
                 "A04 did not retain a concrete rejection for its individually changed cursor context.")
        changed |= differences
    _require(changed == {"program_revision", "element_id", "region", "protocol", "entry_profile", "implementation"},
             "A04 omitted a mandatory immutable cursor context variation.")
    discovery = [r for q, r in context_requests if q["operation"] == "discover" and r["status"] == "succeeded"]
    expected_profiles = {"entry": ("0.4", "impulse-0.1"), "package:fixture.impulse-parts@1.0.0": ("0.4", "impulse-0.1"),
        "package:fixture.surface-parts@1.0.0": ("0.3", "surface-0.1"), "package:fixture.impulse-vectors@1.0.0": ("0.2", "construction-0.1")}
    _require(len(discovery) == 1 and not discovery[0]["truncated"], "A04 lacks complete actual mixed-module discovery.")
    declarations = [i for i in discovery[0]["result"]["items"] if "source_id" in i]
    _require({i["source_id"] for i in declarations} == set(expected_profiles)
             and all((i["language_version"], i["profile"]) == expected_profiles[i["source_id"]] for i in declarations),
             "A04 relabelled the actual 0.2/0.3/0.4 declaring-module profiles.")
    frame_requests = [(q, r) for _, q, r in attempts if q["request_id"] in checks["A05"]["evidence_request_ids"]]
    _require(len(frame_requests) == 2 and all(q["operation"] == "inspect" and r["status"] == "succeeded" for q, r in frame_requests),
             "A05 requires both actual frame-relative inspection exchanges.")
    framed = {q.get("frame", "world"): (q, r["result"]["items"][0]["state"]) for q, r in frame_requests}
    _require(set(framed) == {"world", "ball.frame"}, "A05 omitted its valid nonworld expression frame.")
    world_request, world = framed["world"]
    local_request, local = framed["ball.frame"]
    _require({k: v for k, v in world_request.items() if k not in {"request_id", "frame"}} ==
             {k: v for k, v in local_request.items() if k not in {"request_id", "frame"}}
             and world_request["program_revision"] == cases["P03"]["program_revision"]
             and world_request["project_id"] == fixtures["P03"]["project_id"]
             and world_request["selector"] == {"path": "ball"},
             "A05 relabelled the source, occurrence, run, time or side of its frame inspection.")
    key = (Fraction(world_request["time"]["seconds"]), world_request["time"]["side"])
    _require(_canonical(world) == _canonical(samples["P03"][key]["objects"]["ball"]),
             "A05 world state differs from the actual independently checked P03 sample.")
    converted = {"position_m", "orientation_wxyz", "velocity_m_per_s", "angular_velocity_rad_per_s",
                 "pose_frame", "velocity_expressed_in"}
    _require(_canonical({k: v for k, v in world.items() if k not in converted}) ==
             _canonical({k: v for k, v in local.items() if k not in converted})
             and world["pose_frame"] == world["velocity_expressed_in"] == world["velocity_measured_in"] == "world"
             and local["pose_frame"] == local["velocity_expressed_in"] == "ball.frame"
             and local["velocity_measured_in"] == "world",
             "A05 altered explicit world/self impulse records or inherited frame labels.")
    _close(local["position_m"], [0, 0, 0], 1e-9, "A05 ordinary self-frame position")
    _orientation(local["orientation_wxyz"], [1, 0, 0, 0])
    inverse = [world["orientation_wxyz"][0], *[-v for v in world["orientation_wxyz"][1:]]]
    for field in ("velocity_m_per_s", "angular_velocity_rad_per_s"):
        _close(local[field], surface._rotate(world[field], inverse), 1e-9, "A05 ordinary self-frame "+field)


def _require_a03_execution(test_execution):
    records = [] if test_execution is None else test_execution.get("tests", [])
    for name in _A03_TESTS:
        found = [r for r in records if r.get("test_id") == name]
        _require(len(found) == 1 and found[0]["status"] == "passed" and not found[0].get("failures"),
                 "A03 remains partial until its current named store/provenance/CLI test actually executes: " + name)


def _sample_keys(samples):
    keys = [(Fraction(s["time_seconds"]), s["side"]) for s in samples]
    _require(len(keys) == len(set(keys)) and all(side in {"before", "after"} for _, side in keys),
             "A retained numerical sample is duplicated or has no exact boundary side.")
    return keys


def _verify_poses(objects, fixture, seconds, *, reference=None, direct_metrics=False):
    expected_objects = _expected_objects(fixture)
    paths = {o["path"] for group in expected_objects.values() for o in group}
    _require(set(objects) == paths, "A destination sample omitted or added a source carrier.")
    for path in paths:
        actual, wanted = objects[path], _expected_pose(fixture, path, seconds)
        _require(abs(math.hypot(*_vector(actual["orientation_xyzw"], 4, "Destination rotation"))-1) <= 1e-6,
                 "A destination orientation exceeds the decoded float32 unit-quaternion tolerance.")
        position, rotation = legacy._pose_error(actual, wanted, xyzw=True)
        legacy._metric(position, .001, "Independent source-driven world position")
        legacy._metric(rotation, .001, "Independent source-driven world rotation")
        metrics = actual if direct_metrics else actual["independent"]
        legacy._same_metric(metrics["position_error_m"], position, "Recorded independent position error")
        legacy._same_metric(metrics["rotation_error_rad"], rotation, "Recorded independent rotation error")
        if reference is not None:
            p, q = legacy._pose_error(actual, reference[path], xyzw=True)
            legacy._metric(p, .001, "Agent reference position")
            legacy._metric(q, .001, "Agent reference rotation")
            legacy._same_metric(actual["evaluator"]["position_error_m"], p, "Recorded reference position error")
            legacy._same_metric(actual["evaluator"]["rotation_error_rad"], q, "Recorded reference rotation error")
        for point in actual.get("landmarks", actual.get("probes", [])):
            if "local_m" in point and "world_m" in point:
                world = [x+y for x, y in zip(surface._rotate(point["local_m"], wanted["orientation_wxyz"]), wanted["position_m"])]
                error = surface._vector_error(point["world_m"], world, .001, "Source-driven world geometry landmark")
                if "error_m" in point:
                    legacy._same_metric(point["error_m"], error, "Recorded world landmark error")
    return len(paths)


def _slerp(a, b, ratio):
    a = [x/math.hypot(*a) for x in a]
    b = [x/math.hypot(*b) for x in b]
    dot = sum(x*y for x, y in zip(a, b))
    if dot < 0:
        b, dot = [-x for x in b], -dot
    dot = min(1., max(-1., dot))
    if dot > .999999999999:
        result = [(1-ratio)*x+ratio*y for x, y in zip(a, b)]
    else:
        angle = math.acos(dot)
        result = [(math.sin((1-ratio)*angle)*x+math.sin(ratio*angle)*y)/math.sin(angle) for x, y in zip(a, b)]
    norm = math.hypot(*result)
    return [x/norm for x in result]


def _read_tracks(document, binary, fixture):
    paths = {o["path"] for group in _expected_objects(fixture).values() for o in group}
    nodes = document["nodes"]
    _require(len(nodes) == len(paths) and {n["extras"]["ontokin"]["path"] for n in nodes} == paths
             and document.get("scene", 0) == 0 and len(document["scenes"]) == 1
             and sorted(document["scenes"][0]["nodes"]) == list(range(len(nodes)))
             and all(not n.get("children") and "matrix" not in n and n.get("scale", [1, 1, 1]) == [1, 1, 1] for n in nodes),
             "The actual source artifact acquired a hidden parent, scale or extra motion authority.")
    _require(len(document["animations"]) == 1, "The actual artifact must expose one complete recorded animation.")
    animation = document["animations"][0]
    _require(len(animation["channels"]) == 2*len(nodes), "A source carrier lost a translation or rotation track.")
    tracks, common_times = {}, None
    for channel in animation["channels"]:
        target = channel["target"]
        _require(type(target["node"]) is int and 0 <= target["node"] < len(nodes)
                 and target["path"] in {"translation", "rotation"}, "A recorded channel does not target a source pose.")
        key = (nodes[target["node"]]["extras"]["ontokin"]["path"], target["path"])
        _require(key not in tracks, "An artifact has competing pose channels.")
        sampler = animation["samplers"][channel["sampler"]]
        _require(sampler.get("interpolation", "LINEAR") == "LINEAR", "The native clock unexpectedly changed interpolation semantics.")
        times = surface._accessor(document, binary, sampler["input"])
        values = surface._accessor(document, binary, sampler["output"])
        _require(len(values) == len(times) and times[0] == 0 and times[-1] == 2 and 1 in times
                 and all(a < b for a, b in zip(times, times[1:])), "A recorded clock lost ordering, duration or the exact impulse boundary.")
        _require(common_times is None or times == common_times, "Source carriers were baked on contradictory clocks.")
        common_times = times
        for value in values:
            _vector(value, 3 if key[1] == "translation" else 4, "Decoded GLB pose")
            if key[1] == "rotation":
                _require(abs(math.hypot(*value)-1) <= 1e-6, "A decoded float32 orientation is not a unit quaternion.")
        tracks[key] = values
    _require(set(tracks) == {(p, field) for p in paths for field in ("translation", "rotation")},
             "The actual artifact is missing a source world-pose channel.")
    bound = _SPIN_BOUNDS[fixture]
    _require(all((b-a)*bound < math.pi/2 for a, b in zip(common_times, common_times[1:])),
             "The decoded GLB clock aliases the conservative authored impulse spin bound.")
    return common_times, tracks


def _track_pose(times, tracks, path, seconds):
    time_value = float(seconds)
    index = max(0, min(len(times)-2, bisect_right(times, time_value)-1))
    ratio = (time_value-times[index])/(times[index+1]-times[index])
    positions, rotations = tracks[(path, "translation")], tracks[(path, "rotation")]
    return {"position_m": [(1-ratio)*x+ratio*y for x, y in zip(positions[index], positions[index+1])],
            "orientation_xyzw": _slerp(rotations[index], rotations[index+1], ratio)}


def _motion_probe_times(times):
    probes = set(times)
    for a, b in zip(times, times[1:]):
        probes.update(a+(b-a)*ratio for ratio in (.25, .5, .75))
    return sorted(probes)


def _verify_decoded_motion(times, tracks, fixture, tolerances, *, three=None):
    """Check each actual stored key and its three interior interpolation probes."""
    probes = _motion_probe_times(times)
    paths = {path for path, _ in tracks}
    if three is not None:
        samples = three["decoded_clock_samples"]
        _require(isinstance(samples, list) and len(samples) == len(probes)
                 and all(type(s["time_seconds"]) in (int, float) for s in samples)
                 and [s["time_seconds"] for s in samples] == probes,
                 "Three.js omitted or relabelled an actual decoded-key/interior interpolation probe.")
        _require(three["decoded_clock_pose_comparisons"] == len(probes)*len(paths),
                 "Three.js inferred its decoded-key/interior comparison count.")
    for index, seconds in enumerate(probes):
        if three is not None:
            _verify_poses(samples[index]["objects"], fixture, seconds)
        for path in paths:
            actual = _track_pose(times, tracks, path, seconds)
            position, rotation = legacy._pose_error(actual, _expected_pose(fixture, path, seconds), xyzw=True)
            legacy._metric(position, tolerances["position_m"], "Every decoded key/interval source position")
            legacy._metric(rotation, tolerances["rotation_rad"], "Every decoded key/interval source rotation")
            if three is not None:
                readback = samples[index]["objects"][path]
                _close(readback["position_m"], actual["position_m"], 1e-6, "Dense Three.js versus actual decoded translation")
                # The independent interpolation is normalized; Three.js may
                # retain the admitted float32 key's small norm error. Its norm
                # is checked above under the same bound as the actual GLB.
                _orientation([actual["orientation_xyzw"][3], *actual["orientation_xyzw"][:3]],
                             [readback["orientation_xyzw"][3], *readback["orientation_xyzw"][:3]], 1e-6)
    return len(probes)*len(paths)


def _verify_impulse_boundaries(metadata, case, program, samples, record):
    boundaries = metadata["boundary_states"]
    _require([b["source_seconds"] for b in boundaries] == ["0", "1", "2"],
             "The GLB omitted a source boundary or the after-side duration state.")
    expected_profiles = {"source_impulses": "instantaneous_world_momentum_at_target_self_point",
                         "continuous_external_torques": "absent"}
    _require(all(metadata["impulse_profile"][k] == v for k, v in expected_profiles.items()),
             "The artifact misstates instantaneous versus continuous physical influences.")
    # This source compilation only resolves the inherited joint/action metadata;
    # the motion and impulse record checks below use fixed source mathematics.
    model = compile_construction(program, level="constructed").model
    source_states = evaluate(model, [{"time_seconds": t, "side": "after"} for t in ("0", "1", "2")])["samples"]
    comparisons = 0
    for boundary, source in zip(boundaries, source_states):
        sample = samples[(Fraction(boundary["source_seconds"]), "after")]
        wanted = {p: s["impulses"] for p, s in sample["objects"].items()}
        _require(boundary["impulse_states_after"] == wanted
                 and boundary["impulse_states_after"] == {p: s["impulses"] for p, s in source["objects"].items()},
                 "The delivered GLB lost, changed or truncated a complete source impulse projection.")
        _require(boundary["pose_authorities_after"] == {p: s["pose_authority"] for p, s in sample["objects"].items()}
                 and boundary["joint_states_after"] == source["joints"] and boundary["action_states_after"] == source["actions"],
                 "A boundary changed dynamic origin, analytic anchor or inherited joint/action state.")
        _check_projection(case, program, sample)
        for path, state in sample["objects"].items():
            history = state["impulses"]
            if not history["last_applications"]:
                continue
            application = samples[(Fraction(history["last_application_time_seconds"]), "after")]["objects"][path]
            for impulse in history["last_applications"]:
                lever = surface._rotate(impulse["application_point_self_m"], application["orientation_wxyz"])
                world = [x+y for x, y in zip(application["position_m"], lever)]
                _close(impulse["lever_arm_world_m"], lever, 1e-9, "Application-time world lever")
                _close(impulse["application_point_world_m"], world, 1e-9, "Application-time world point")
                comparisons += 1
    _require(record == {"status": "passed", "boundary_count": 3, "retained_application_comparisons": comparisons},
             "The independent source influence count contradicts actual complete boundary records.")
    return comparisons


def _verify_destination(native, evidence_root, implementation, contract, context):
    _require("workflow" in context, "Native impulse delivery requires the verified accepted Agent workflow first.")
    build_path = _identified(native["build"], evidence_root)
    report_path = _identified(native["destination"], evidence_root)
    build, report, root = _json_file(build_path), _json_file(report_path), build_path.parent
    _require(build["schema_version"] == "ontokin.impulse-native-build/0.1" and build["status"] == "built"
             and build["implementation"] == implementation and build["acceptance_manifest_sha256"] == ACCEPTANCE_SHA256
             and build["builder_sha256"] == file_identity(ROOT/"tools/build_impulse_agent_demo.py")
             and build["oracle_builder_sha256"] == file_identity(ROOT/"tools/impulse_oracles.py"),
             "Native build is incomplete or identifies stale source/compiler tooling.")
    _require(report["schema_version"] == "ontokin.impulse-native-destination-validation/0.1" and report["status"] == "passed"
             and report["implementation"] == implementation and report["build_sha256"] == file_identity(build_path)
             and report["acceptance_manifest_sha256"] == ACCEPTANCE_SHA256,
             "Independent validation is absent or describes another source build.")
    _require(report["verifier_sha256"] == file_identity(ROOT/"tools/verify_impulse_native.mjs")
             and report["surface_verifier_sha256"] == file_identity(ROOT/"tools/verify_surface_native.mjs")
             and report["tooling_lock_sha256"] == file_identity(ROOT/"tools/package-lock.json"),
             "Native independent checker, imported geometry checker or pinned tooling is stale.")
    lock = _json_file(ROOT/"tools/package-lock.json")["packages"]
    khronos_version = lock["node_modules/gltf-validator"]["version"]
    three_version = lock["node_modules/three"]["version"]
    _require(report["environment"]["three"] == three_version
             and report["environment"]["khronos_gltf_validator"] == khronos_version
             and all(report["environment"].get(k) for k in ("node", "platform", "architecture")),
             "The native report lacks the actual pinned destination runtime identity.")
    artifacts, results = ({f["fixture"]: f for f in values} for values in (build["fixtures"], report["fixtures"]))
    mandatory = set(contract["mapping"]["mandatory_native_fixtures"])
    _require(len(artifacts) == len(build["fixtures"]) == len(results) == len(report["fixtures"])
             and set(artifacts) == set(results) == mandatory, "A mandatory source artifact or independent result is absent or duplicated.")
    cases = {c["id"]: c for c in contract["acceptance"]["source_cases"]}
    verified, count, decoded_count = {}, 0, 0
    for fixture in contract["mapping"]["mandatory_native_fixtures"]:
        case, entry, result = cases[fixture], artifacts[fixture], results[fixture]
        directory = legacy._repository_file(fixture+"/program.bundle.json", root).parent
        program = surface._source_bundle(directory/"program.bundle.json")
        _require(program.to_payload() == fixture_bundle(case, contract["directory"]).to_payload(),
                 "The decoded destination program differs from its exact frozen source closure.")
        oracle = _json_file(directory/"oracle.json")
        expected = _expected_objects(fixture)
        _require(oracle["schema_version"] == "ontokin.impulse-fixture-oracle/0.1" and oracle["fixture"] == fixture
                 and oracle["acceptance_manifest_sha256"] == ACCEPTANCE_SHA256 and oracle["program_revision"] == program.program_revision
                 and oracle["frozen_expected"] == case["expected"] and all(oracle[k] == expected[k] for k in expected),
                 "A retained numerical/geometry oracle changed its predetermined source scalars.")
        files = {"bundle": "program.bundle.json", "glb": "scene.glb", "export": "scene.export.json",
                 "reference": "scene.reference.json", "oracle": "oracle.json"}
        files.update({"source_"+str(i): u.filename for i, u in enumerate(program.units)})
        _require(set(result["provenance"]) == set(files), "The native provenance closure omitted an actual source or artifact file.")
        for role, name in files.items():
            item = result["provenance"][role]
            file = _nested(item["file"], item["sha256"], directory)
            _require(item["file"] == name and item["byte_length"] == file.stat().st_size, "Native file provenance changed its path or byte length.")
        glb = directory/"scene.glb"
        artifact_sha, revision = file_identity(glb), program.program_revision
        surface._verify_delivery_link(fixture, program, artifact_sha, glb.stat().st_size, context)
        _require(entry["program_revision"] == result["program_revision"] == revision
                 and entry["artifact_sha256"] == result["artifact_sha256"] == artifact_sha
                 and entry["glb_bytes"] == glb.stat().st_size and result["status"] == "passed",
                 "Native source, delivered artifact and destination result identities disagree.")
        export, reference = _json_file(directory/"scene.export.json"), _json_file(directory/"scene.reference.json")
        source_digest = implementation["source_code_sha256"].removeprefix("sha256:")
        _require(export["schema_version"] == "ontokin.glb-report/0.4" and export["target_contract"] == "ontokin.glb/0.4"
                 and export["validation"]["status"] == "passed" and export["source_code_sha256"] == result["exporter_source_code_sha256"] == source_digest
                 and export["program_revision"] == revision and export["program"]["manifest"] == program.manifest()
                 and export["artifact"]["sha256"] == artifact_sha and export["artifact"]["byte_length"] == glb.stat().st_size,
                 "The successful exporter report describes other source/runtime/artifact bytes.")
        _require(reference["schema_version"] == "ontokin.impulse-native-reference/0.1" and reference["implementation"] == implementation
                 and reference["program_revision"] == revision and reference["source_manifest"] == program.manifest()
                 and reference["artifact_sha256"] == artifact_sha and reference["tolerances"] == export["tolerances"],
                 "The retained source state reference is disconnected from the actual source delivery.")
        legacy._check_tolerances(reference["tolerances"])
        state_samples = context["workflow"]["samples"][fixture]
        reference_keys = _sample_keys(reference["samples"])
        _require(set(reference_keys) == set(state_samples) and all(s == state_samples[k] for k, s in zip(reference_keys, reference["samples"])),
                 "The source reference is not the complete state read back through the identified Agent workflow.")
        document, binary = surface._glb(glb)
        metadata = document["extras"]["ontokin"]
        _require(metadata["target_contract"] == "ontokin.glb/0.4" and metadata["profile"] == "impulse-0.1"
                 and metadata["program"]["revision"] == revision and metadata["program"]["manifest"] == program.manifest()
                 and metadata["transform_policy"] == "all_nodes_are_roots_with_baked_world_poses",
                 "The real GLB changed source identity, profile or placement authority.")
        geometry = {g["path"]: g for g in result["geometry"]}
        _require(len(geometry) == len(result["geometry"]) == len(expected["shapes"]), "Native geometry evidence is missing or duplicated.")
        for shape in expected["shapes"]:
            surface._verify_geometry(document, binary, shape, geometry[shape["path"]], revision, program)
            physical = next(n["extras"]["ontokin"]["physical"] for n in document["nodes"] if n["extras"]["ontokin"]["path"] == shape["path"])
            _require(physical["radius"] == shape["body_radius_m"] and physical["mass"] == shape["body_mass_kg"],
                     "The artifact attached different physical sphere parameters to unchanged visible geometry.")
        khronos = result["khronos"]
        _require(khronos["version"] == khronos_version and khronos["errors"] == khronos["warnings"] == 0
                 and not any(m.get("severity") in (0, 1) for m in khronos.get("messages", [])),
                 "The actual pinned Khronos run reported an error/warning or changed its identity.")
        three = result["three_js"]
        _require(three["version"] == three_version.split(".")[1], "The Three.js report uses another pinned destination version.")
        wanted_materials = [{"path": s["path"], "region": key, "triangles": 48, **s["materials"][key]}
                            for s in expected["shapes"] for key in ("clay", "paint")]
        _require(sorted(three["materials"], key=lambda r: (r["path"], r["region"])) ==
                 sorted(wanted_materials, key=lambda r: (r["path"], r["region"])), "Three.js material readback changed an actual PBR region.")
        keys = _sample_keys(three["samples"])
        _require(keys == reference_keys, "Three.js omitted or relabelled a fixed source time/side sample.")
        times, tracks = _read_tracks(document, binary, fixture)
        decoded_count += _verify_decoded_motion(times, tracks, fixture, reference["tolerances"], three=three)
        comparisons = 0
        for key, sample in zip(keys, three["samples"]):
            comparisons += _verify_poses(sample["objects"], fixture, key[0], reference=state_samples[key]["objects"])
            for path_ in sample["objects"]:
                decoded = _track_pose(times, tracks, path_, key[0])
                p, q = legacy._pose_error(decoded, _expected_pose(fixture, path_, key[0]), xyzw=True)
                legacy._metric(p, .001, "Independently decoded GLB animation position")
                legacy._metric(q, .001, "Independently decoded GLB animation rotation")
                actual = sample["objects"][path_]
                _close(decoded["position_m"], actual["position_m"], 1e-6, "Three.js versus actual decoded translation")
                _orientation([decoded["orientation_xyzw"][3], *decoded["orientation_xyzw"][:3]],
                             [actual["orientation_xyzw"][3], *actual["orientation_xyzw"][:3]], 1e-6)
        _require(three["world_pose_comparisons"] == comparisons, "Three.js inflated or inferred its completed comparison count.")
        _verify_impulse_boundaries(metadata, case, program, state_samples, result["impulse_boundaries"])
        clock = result["clock"]
        _require(clock["key_count"] == len(times) and clock["authored_angular_speed_bound_rad_per_s"] == _SPIN_BOUNDS[fixture]
                 and clock["source_boundaries_retained"] is True, "The recorded destination clock contradicts actual source bound or keys.")
        legacy._same_metric(clock["maximum_interval_seconds"], max(b-a for a, b in zip(times, times[1:])), "Actual maximum decoded clock gap")
        if fixture == "P11":
            _require(entry["options"]["fps"] == case["expected"]["export_options"]["fps"] == 1,
                     "The high-spin delivery avoided its fixed low requested FPS.")
            coarse = result["coarsened_track_rejected"]
            a, b = (_track_pose(times, tracks, "ball", t)["orientation_xyzw"] for t in (1, 2))
            pose = _expected_pose(fixture, "ball", Fraction(5, 4))
            candidate = {"position_m": pose["position_m"], "orientation_xyzw": _slerp(a, b, .25)}
            _, error = legacy._pose_error(candidate, pose, xyzw=True)
            _require(coarse["status"] == "passed" and coarse["clock_alias_rejected"] is True
                     and coarse["coarse_rotation_rejected"] is True and coarse["removed_intermediate_keys"] is True
                     and coarse["probe_time_seconds"] == "1.25" and error > reference["tolerances"]["rotation_rad"]
                     and coarse["tolerance_rad"] == reference["tolerances"]["rotation_rad"],
                     "The high-spin trap lacks an actual rejected coarse clock and independent quarter-time pose.")
            legacy._same_metric(coarse["coarse_rotation_error_rad"], error, "Actual coarse high-spin rotation error")
        verified[fixture] = {"program_revision": revision, "artifact_sha256": artifact_sha,
            "provenance": result["provenance"], "oracle": oracle, "sample_keys": keys}
        count += comparisons
    repairs = report["physical_repairs"]
    _require(len(repairs) == 2 and {r["after_fixture"] for r in repairs} == {"P09", "P10"}, "A physical repair destination comparison is missing.")
    for repaired in repairs:
        _require(repaired["before_fixture"] == "P08" and repaired["status"] == "passed"
                 and repaired["target_path"] == 'rack.props["first"]' and repaired["sibling_path"] == 'rack.props["second"]'
                 and all(repaired[k] is True for k in ("geometry_and_pbr_unchanged", "sibling_pose_unchanged", "target_angular_response_changed")),
                 "The destination repair report contradicts the adopted single-occurrence change.")
    context["destination"] = verified
    return {"build_sha256": file_identity(build_path), "destination_sha256": file_identity(report_path),
            "fixtures": len(verified), "world_pose_comparisons": count, "decoded_key_interval_pose_checks": decoded_count,
            "khronos_errors": 0, "khronos_warnings": 0}


@lru_cache(maxsize=4)
def _camera_bounds(fixture):
    low, high = [math.inf]*3, [-math.inf]*3
    for shape in _expected_objects(fixture)["shapes"]:
        points = {tuple(p) for _, face, _ in surface._analytic_triangles(shape) for p in face}
        for seconds in _TIMES:
            pose = _expected_pose(fixture, shape["path"], seconds)
            for point in points:
                world = [p+v for p, v in zip(pose["position_m"], surface._rotate(point, pose["orientation_wxyz"]))]
                low = [min(a, b) for a, b in zip(low, world)]
                high = [max(a, b) for a, b in zip(high, world)]
    return low, high


def _verify_camera(camera, fixture):
    _finite_tree(camera)
    _require(camera["up"] == [0, 1, 0] and camera["fit_sample_times_seconds"] == [float(t) for t in _TIMES]
             and camera["fit_policy"] == "union_of_actual_geometry_over_quarter_seconds/0.1"
             and 0 < camera["near_m"] < camera["far_m"] and 0 < camera["fov_degrees"] < 180
             and camera["aspect"] > 0, "The browser camera lost its actual Y-up bounded projection settings.")
    for name, length in (("position_m", 3), ("target_m", 3), ("orientation_xyzw", 4), ("bounds_min_m", 3), ("bounds_max_m", 3)):
        _vector(camera[name], length, "Browser camera "+name)
    low, high = _camera_bounds(fixture)
    _close(camera["bounds_min_m"], low, 1e-5, "Camera union lower bounds")
    _close(camera["bounds_max_m"], high, 1e-5, "Camera union upper bounds")
    _close(camera["target_m"], [(a+b)/2 for a, b in zip(low, high)], 1e-5, "Camera union center")


def _verify_browser_materials(objects, fixture):
    for shape in _expected_objects(fixture)["shapes"]:
        actual = objects[shape["path"]]["primitives"]
        wanted = [{"region": region, "triangles": 48, **shape["materials"][region]} for region in ("clay", "paint")]
        _require(sorted(actual, key=lambda p: p["region"]) == wanted, "The browser did not render every exact source PBR region.")
    for empty in _expected_objects(fixture)["empty_objects"]:
        _require(objects[empty["path"]]["primitives"] == [], "The browser gave an empty carrier visible geometry.")


def _verify_browser(native, evidence_root, implementation, contract, context):
    _require("destination" in context, "Browser validation requires the verified source-delivered GLBs first.")
    path = _identified(native["browser"], evidence_root)
    report = _json_file(path)
    _require(report["schema_version"] == "ontokin.impulse-browser-validation/0.1" and report["status"] == "passed"
             and report["implementation"] == implementation and report["acceptance_manifest_sha256"] == ACCEPTANCE_SHA256
             and report["workflow_sha256"] == context["workflow_sha256"]
             and report["native_build_sha256"] == native["build"]["sha256"],
             "The actual browser run belongs to another source workflow/build or did not pass.")
    for field, file in (("verifier_sha256", "verify_impulse_viewer.mjs"), ("native_verifier_sha256", "verify_impulse_native.mjs"),
                        ("surface_verifier_sha256", "verify_surface_native.mjs"), ("tooling_lock_sha256", "package-lock.json")):
        _require(report[field] == file_identity(ROOT/"tools"/file), "A browser checker dependency or pinned tool lock changed.")
    _require(report["harness_file"] == "impulse-viewer.html", "The browser report lost its explicit retained harness.")
    _nested(report["harness_file"], report["harness_sha256"], path.parent)
    lock = _json_file(ROOT/"tools/package-lock.json")["packages"]
    for name in ("playwright", "three", "esbuild"):
        _require(report["environment"][name] == lock["node_modules/"+name]["version"], "The browser executed a different pinned tool version.")
    _require(report.get("browser") and report.get("webgl") and report["environment"]["camera_up"] == [0, 1, 0]
             and all(report["environment"].get(k) for k in ("node", "platform", "architecture", "renderer", "viewport")),
             "The browser lacks actual renderer, viewport or runtime identity.")
    for key in ("page_errors", "console_errors", "failed_requests", "network_requests"):
        _require(report[key] == [], "The browser run reported "+key+".")
    mandatory = set(contract["mapping"]["mandatory_browser_fixtures"])
    fixtures = {f["fixture"]: f for f in report["source_fixtures"]}
    _require(len(fixtures) == len(report["source_fixtures"]) == len(mandatory) and set(fixtures) == mandatory,
             "A mandatory browser fixture is absent or duplicated.")
    for group in ("samples", "captures", "playback"):
        _require({r["fixture"] for r in report[group]} == mandatory, "Browser evidence added or omitted a fixed fixture.")
    review_value = native["visual_reviews"]
    reviews_list = _json_file(_identified(review_value, evidence_root)) if isinstance(review_value, dict) else review_value
    _require(isinstance(reviews_list, list), "Visual reviews must be an identified list of capture observations.")
    reviews = {r["capture_sha256"]: r for r in reviews_list}
    _require(len(reviews) == len(reviews_list), "A visual review duplicates its capture identity.")
    count, captures_count = 0, 0
    for fixture in contract["mapping"]["mandatory_browser_fixtures"]:
        source, destination = fixtures[fixture], context["destination"][fixture]
        _require(source["program_revision"] == destination["program_revision"] and source["artifact_sha256"] == destination["artifact_sha256"]
                 and source["provenance"] == destination["provenance"]
                 and source["exporter_source_code_sha256"] == implementation["source_code_sha256"].removeprefix("sha256:"),
                 "The browser rendered an artifact other than the independently validated accepted source delivery.")
        samples = [s for s in report["samples"] if s["fixture"] == fixture]
        _require(_sample_keys(samples) == destination["sample_keys"], "The browser omitted or changed a fixed source sample time/side.")
        front_camera = None
        for sample in samples:
            count += _verify_poses(sample["objects"], fixture, Fraction(sample["time_seconds"]), direct_metrics=True)
            _verify_browser_materials(sample["objects"], fixture)
            _verify_camera(sample["camera"], fixture)
            _require(front_camera is None or sample["camera"] == front_camera, "Seeking changed the fixed browser camera framing.")
            front_camera = sample["camera"]
        captures = [c for c in report["captures"] if c["fixture"] == fixture]
        required = {(c["view"], Fraction(c["time_seconds"])) for c in contract["mapping"]["mandatory_browser_captures"]}
        _require(len(captures) == len(required) and {(c["view"], Fraction(str(c["time_seconds"]))) for c in captures} == required,
                 "The required front, side and animated captures are incomplete or duplicated.")
        for capture in captures:
            file = _nested(capture["file"], capture["sha256"], path.parent)
            dimensions = surface._verify_png(file)
            viewport = report["environment"]["viewport"]
            _require(dimensions["width"] == viewport["width"] and dimensions["height"] >= viewport["height"],
                     "The PNG dimensions do not match the actual full-page browser viewport.")
            _require(capture["program_revision"] == source["program_revision"] and capture["artifact_sha256"] == source["artifact_sha256"]
                     and capture["camera_view"] == ("side" if capture["view"] == "side" else "front"),
                     "A browser capture lost source/artifact or camera identity.")
            _verify_camera(capture["camera"], fixture)
            if capture["view"] != "side":
                _require(capture["camera"] == front_camera, "The front/animated capture silently reframed the same source motion.")
            _verify_poses(capture["objects"], fixture, Fraction(str(capture["time_seconds"])), direct_metrics=True)
            _verify_browser_materials(capture["objects"], fixture)
            review = reviews.get(capture["sha256"], {})
            _require(review.get("status") == "reviewed" and isinstance(review.get("reviewer"), str) and review["reviewer"].strip()
                     and isinstance(review.get("observation"), str) and review["observation"].strip(),
                     "A mandatory actual PNG has no identified visual observation.")
            captures_count += 1
        playback = [p for p in report["playback"] if p["fixture"] == fixture]
        _require(len(playback) == 1 and playback[0]["stable_across_frames"] is True
                 and playback[0]["started_at_seconds"] == 1.05
                 and 1.05 < _finite(playback[0]["paused_at_seconds"], "Observed playback time") < 2,
                 "The browser lacks its actual successful play/pause observation.")
        _verify_camera(playback[0]["camera"], fixture)
        _verify_poses(playback[0]["objects"], fixture, playback[0]["paused_at_seconds"], direct_metrics=True)
    _require(report["world_pose_comparisons"] == count
             and report["capture_pose_comparisons"] == sum(len(c["objects"]) for c in report["captures"]),
             "Browser comparison totals contradict its retained numerical readback.")
    return {"browser_sha256": file_identity(path), "fixtures": len(fixtures), "world_pose_comparisons": count,
            "reviewed_captures": captures_count}


def _verify_surface_report(report, implementation, current_inventory, mapping):
    names = sorted({name for c in mapping["cases"] for name in c["required_tests"]})
    _require(report["schema_version"] == "ontokin.surface-conformance/0.1" and report["executed"] is True
             and report["implementation"] == report["implementation_after_run"] == implementation
             and report["evidence_stable_during_run"] is True and not report["run_issues"]
             and report["evidence_files"] == current_inventory
             and report["evidence_inventory_sha256"] == surface.inventory_identity(current_inventory)
             and report["manifest"]["sha256"] == surface.MAPPING_SHA256,
             "Current M01-M12 is unexecuted, stale, or identifies a changed mapping/inventory.")
    _require(surface._execution_passes(report["test_execution"], names), "Current M01-M12 mapped methods did not all execute exactly once and pass.")
    actual = {c["id"]: c for c in report["cases"]}
    _require(len(actual) == len(report["cases"]) == 12 and set(actual) == {c["id"] for c in mapping["cases"]},
             "Current native conformance omitted an adopted M01-M12 requirement.")
    for case in mapping["cases"]:
        found = actual[case["id"]]
        _require(found["status"] == "passed" and found["required_tests"] == case["required_tests"]
                 and found["external_gates"] == case["external_gates"] and not found["pending_reasons"],
                 "An inherited native requirement remains pending or changed its reviewed coverage.")
    _require(report["summary"]["full_gate_complete"] is True and report["summary"]["passed"] == 12
             and report["summary"]["failed"] == report["summary"]["pending"] == 0,
             "Historical or partial native evidence cannot close the current impulse regression gate.")


def _verify_regression(records, evidence_root, implementation, inventory, contract):
    inherited = surface._verify_regression(records, evidence_root, implementation, inventory, contract["mapping"])
    paths = {key: _identified(records[key], evidence_root) for key in ("surface", "surface_external")}
    report = _json_file(paths["surface"])
    mapping, current_inventory = surface.load_manifest(), surface.evidence_inventory()
    _verify_surface_report(report, implementation, current_inventory, mapping)
    _require(report["external_evidence"]["manifest_sha256"] == file_identity(paths["surface_external"]),
             "The current M12 result used a different independently validated external evidence set.")
    audit = surface.verify_external_evidence(paths["surface_external"], implementation=implementation, inventory=current_inventory,
                                            manifest=mapping, evidence_root=evidence_root)
    _require(all(g["status"] == "passed" for g in audit["gates"]),
             "Current inherited native external evidence remains pending: " + "; ".join(
                 g["id"]+": "+"; ".join(g["issues"]) for g in audit["gates"] if g["status"] != "passed"))
    return {**inherited, "surface_cases": 12, "current_M12": "passed", "surface_report_sha256": file_identity(paths["surface"]),
            "surface_external_sha256": file_identity(paths["surface_external"])}


def _verify_commit_inventory(commit, inventory):
    process = subprocess.run(["git", "ls-tree", "-r", "--full-tree", "-z", commit], cwd=ROOT,
                             capture_output=True, check=False, timeout=30)
    _require(process.returncode == 0, "The CI commit is not locally available for an exact implementation/input tree check.")
    tree = {}
    for row in process.stdout.split(b"\0"):
        if row:
            descriptor, path = row.split(b"\t", 1)
            mode, kind, identity = descriptor.decode("ascii").split()
            if kind == "blob":
                tree[path.decode("utf-8")] = (mode, identity)
    paths = {r["path"] for r in inventory}
    _require(len(paths) == len(inventory) and paths == {p for p in tree if _inventory_path(p)},
             "The CI Git tree omitted, added or renamed current runtime/test/spec/tool inputs.")
    for record in inventory:
        raw = legacy._repository_file(record["path"], ROOT).read_bytes()
        _require(digest(raw) == record["sha256"], "The current input changed during its CI inventory check.")
        blob = hashlib.sha1(b"blob "+str(len(raw)).encode("ascii")+b"\0"+raw).hexdigest()
        _require(tree.get(record["path"]) in (("100644", blob), ("100755", blob)),
                 "The CI commit did not contain current bytes: "+record["path"])


def _verify_ci(record, evidence_root, implementation, inventory):
    path = _identified(record, evidence_root)
    ci = _json_file(path)
    _require(ci["schema_version"] == "ontokin.impulse-ci/0.1" and ci["implementation"] == implementation
             and ci["evidence_inventory_sha256"] == surface.inventory_identity(inventory),
             "The CI report does not identify this exact broader impulse implementation/input inventory.")
    commit, run = ci["implementation_commit"], ci["workflow_run"]
    _require(isinstance(commit, str) and surface.COMMIT.fullmatch(commit), "CI must identify a complete immutable Git commit.")
    _require(type(run["id"]) is int and run["id"] > 0 and run["head_sha"] == commit
             and run["status"] == "completed" and run["conclusion"] == "success"
             and run["html_url"] == f'https://github.com/Omegapy/OntoKin/actions/runs/{run["id"]}',
             "CI did not actually complete successfully on the identified OntoKin commit.")
    jobs, versions, visual = ci["jobs"], set(), 0
    _require(isinstance(jobs, list) and len({j["id"] for j in jobs}) == len(jobs), "CI job IDs are absent or duplicated.")
    for job in jobs:
        _require(type(job["id"]) is int and job["id"] > 0 and job["run_id"] == run["id"]
                 and isinstance(job["name"], str) and job["name"].strip()
                 and job["status"] == "completed" and job["conclusion"] == "success", "A required current CI job did not pass.")
        if job["role"] == "python":
            _require(job["python_version"] in {"3.11", "3.12", "3.13"} and job["python_version"] not in versions,
                     "A required supported Python CI job is missing or duplicated.")
            versions.add(job["python_version"])
        elif job["role"] == "visual":
            _require(job["python_version"] is None, "The visual CI job has inconsistent role metadata.")
            visual += 1
        else:
            raise ValueError("Unknown required CI job role.")
    _require(versions == {"3.11", "3.12", "3.13"} and visual == 1,
             "Three supported Python CI jobs and one independent 3D job remain mandatory.")
    _verify_commit_inventory(commit, inventory)
    return {"ci_sha256": file_identity(path), "implementation_commit": commit, "workflow_run_id": run["id"],
            "python_versions": sorted(versions), "visual_jobs": visual}


def verify_external_evidence(path=None, *, implementation=None, inventory=None, contract=None, evidence_root=ROOT, test_execution=None):
    """Audit retained executions; no browser, Node validator or GitHub run is started."""
    implementation = implementation or implementation_identity()
    inventory = evidence_inventory() if inventory is None else inventory
    contract = load_manifest() if contract is None else contract
    result = {"schema_version": "ontokin.impulse-evidence-audit/0.1", "executed_external_tools": False,
        "manifest": None if path is None else str(path), "gates": [],
        "basis": "Exact source/exchange/binary/numerical/capture/current-regression/CI-tree audit; external tools were not rerun."}
    message = "No identified impulse release evidence manifest was supplied."
    if path is None:
        result["gates"] = [{"id": name, "status": "pending", "executed_external_tools": False, "issues": [message]} for name in GATES]
        return result
    try:
        value = _json_file(Path(path))
        _require(value["schema_version"] == "ontokin.impulse-release-evidence/0.1" and value["implementation"] == implementation,
                 "The evidence identifies another schema or implementation.")
        result["manifest_sha256"] = file_identity(Path(path))
    except (OSError, ValueError, TypeError, KeyError) as error:
        result["gates"] = [{"id": name, "status": "pending", "executed_external_tools": False, "issues": [str(error)]} for name in GATES]
        return result
    root, context = Path(evidence_root), {}
    def workflow():
        verified = _verify_workflow(value["workflow"], root, implementation, contract, context, test_execution)
        context["workflow_sha256"] = verified["workflow_sha256"]
        return verified
    actions = {
        "workflow": workflow,
        "destination": lambda: _verify_destination(value["native"], root, implementation, contract, context),
        "browser": lambda: _verify_browser(value["native"], root, implementation, contract, context),
        "regression": lambda: _verify_regression(value["legacy"], root, implementation, inventory, contract),
        "ci": lambda: _verify_ci(value["ci"], root, implementation, inventory),
    }
    def protected(action):
        def check():
            try:
                return action()
            except OntoKinError as error:
                raise ValueError("Actual retained source cannot satisfy this evidence gate: "+str(error)) from error
        return check
    result["gates"] = [_gate(name, protected(actions[name])) for name in GATES]
    return result


def run_conformance(*, case_ids=None, external_evidence=None, evidence_root=ROOT):
    contract=load_manifest()
    mapping,acceptance=contract["mapping"],contract["acceptance"]
    all_ids={c["id"] for c in mapping["cases"]}
    selected=all_ids if case_ids is None else set(case_ids)
    _require(selected and selected<=all_ids,"Select one or more adopted impulse gates I01-I12.")
    cases=[c for c in mapping["cases"] if c["id"] in selected]
    names=sorted({n for c in cases for n in c["required_tests"]})
    source_ids={s for c in cases for s in c["source_case_ids"]}
    before,implementation=evidence_inventory(),implementation_identity()
    sources=[execute_source_case(c,contract["directory"]) for c in acceptance["source_cases"] if c["id"] in source_ids]
    execution=legacy._run_tests(names)
    external=verify_external_evidence(external_evidence,implementation=implementation,inventory=before,contract=contract,
                                      evidence_root=evidence_root,test_execution=execution)
    stable=before==evidence_inventory() and implementation==implementation_identity()
    issues=[] if stable else ["Implementation or verification inputs changed during execution."]
    if not _execution_passes(execution,names):
        issues.append("One or more required unittest methods did not execute exactly once and pass.")
    source_map={c["id"]:c for c in sources}
    test_map={r["test_id"]:r for r in execution["tests"]}
    external_map={g["id"]:g for g in external["gates"]}
    results=[]
    for case in cases:
        pending=list(issues)
        pending += case.get("implementation_checks_pending", [])
        failed=any(source_map[n]["status"]=="failed" for n in case["source_case_ids"])
        for name in case["required_tests"]:
            status=test_map.get(name,{}).get("status","not_run")
            failed|=status in {"failed","error","expected_failure","unexpected_success"}
        for name in case["external_gates"]:
            if external_map[name]["status"]!="passed":
                pending.append(name+": "+"; ".join(external_map[name]["issues"]))
        results.append({**case,"status":"failed" if failed else "pending" if pending else "passed","pending_reasons":pending})
    counts=Counter(c["status"] for c in results)
    return {"schema_version":"ontokin.impulse-conformance/0.1","executed":True,
            "generated_at_utc":datetime.now(timezone.utc).isoformat(),"implementation":implementation,
            "implementation_after_run":implementation_identity(),"evidence_stable_during_run":stable,
            "profile":"impulse-0.1","language_version":"0.4","agent_contract":"ontokin.agent/0.4","export_contract":"ontokin.glb/0.4",
            "acceptance_sha256":ACCEPTANCE_SHA256,"mapping_sha256":MAPPING_SHA256,
            "evidence_files":before,"evidence_inventory_sha256":surface.inventory_identity(before),
            "source_execution":{"required_ids":[c["id"] for c in sources],"cases":sources,"passed":sum(c["status"]=="passed" for c in sources)},
            "test_execution":execution,"external_evidence":external,"run_issues":issues,"cases":results,
            "summary":{"total":len(results),"passed":counts["passed"],"failed":counts["failed"],"pending":counts["pending"],
                       "all_adopted_cases_selected":selected==all_ids,"full_gate_complete":selected==all_ids and counts["passed"]==12 and not issues},
            "unselected_case_ids":sorted(all_ids-selected),"full_product_conformance_certified":False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case",action="append",dest="case_ids")
    parser.add_argument("--external-evidence",type=Path)
    parser.add_argument("--evidence-root",type=Path,default=ROOT)
    parser.add_argument("--full-suite-only",action="store_true")
    parser.add_argument("--allow-pending",action="store_true")
    parser.add_argument("--output",type=Path)
    args=parser.parse_args(argv)
    try:
        result=run_full_suite() if args.full_suite_only else run_conformance(case_ids=args.case_ids,external_evidence=args.external_evidence,evidence_root=args.evidence_root)
    except (OSError,ValueError,TypeError,KeyError) as error:
        result={"schema_version":"ontokin.impulse-conformance/0.1","executed":False,"status":"failed","error":str(error),"full_product_conformance_certified":False}
        code=1
    else:
        if args.full_suite_only:
            code=0 if result["summary"]["all_passed"] else 1
        else:
            code=1 if result["summary"]["failed"] or result["run_issues"] else 2 if result["summary"]["pending"] else 0
            if code==2 and args.allow_pending:
                code=0
    raw=json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(raw)
    else:
        print(raw,end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
