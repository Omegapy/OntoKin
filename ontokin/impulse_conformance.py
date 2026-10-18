"""Execute frozen impulse source oracles and audit identified release evidence.

The accepted corpus is an input, never a report. This runner independently
checks actual compiler/evaluator results; source tests are not counted from a
manifest. Missing external executions remain pending, and no finite release
certifies the complete product. The audit never reruns external applications.
"""
from __future__ import annotations

import argparse
import base64
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
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
MAPPING_SHA256 = "sha256:e9f283668560edf404cac7176c8aace479880e2d76f46ca38b046e3a3c6b7363"
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
            and path.suffix in {".py",".ok",".json",".md",".html",".mjs"})


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


def verify_external_evidence(path=None, *, implementation=None, inventory=None, contract=None, evidence_root=ROOT):
    """Readers are added with the concrete independently executed report shapes."""
    result={"schema_version":"ontokin.impulse-evidence-audit/0.1","executed_external_tools":False,
            "manifest":None if path is None else str(path),"gates":[]}
    message="No identified impulse release evidence manifest was supplied."
    if path is not None:
        try:
            value=_json_file(Path(path))
            _require(value["schema_version"]=="ontokin.impulse-release-evidence/0.1"
                     and value["implementation"]==(implementation or implementation_identity()),
                     "The evidence identifies another schema or implementation.")
            result["manifest_sha256"]=file_identity(Path(path))
            message="Independent impulse evidence readers are not yet implemented; no external gate can pass."
        except (OSError,ValueError,TypeError,KeyError) as error:
            message=str(error)
    result["gates"]=[{"id":name,"status":"pending","executed_external_tools":False,"issues":[message]} for name in GATES]
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
    external=verify_external_evidence(external_evidence,implementation=implementation,inventory=before,contract=contract,evidence_root=evidence_root)
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
