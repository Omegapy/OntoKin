"""Proposed, pointwise derived-rate audit; this is not adopted release acceptance.

The independent source reference supplies an interval box and a derived source
arithmetic allowance. Exact squared-distance extrema preserve the distinction
between a proof, a contradiction and an unresolved interval. Frozen binary64
preparation values remain measurements, not exact mathematical expectations.
"""
from __future__ import annotations

from fractions import Fraction as F
import hashlib
import json
import math
from pathlib import Path
import re
import struct

from ontokin import reach_reference as reference_module
from ontokin.reach_reference import Interval, ReachReference, ReferenceError, build_reference


PROFILE = "planar-reach-0.1"
OBSERVATION_SCHEMA = "ontokin.reach-rate-observation/0.1"
FROZEN_SCHEMA = "ontokin.reach-frozen-rate-observation/0.1"
REPORT_SCHEMA = "ontokin.reach-rate-audit-proposal/0.1"
MAX_OPERAND_BITS = 32768
MAX_OPERATIONS = 100000
MAX_CARRIERS = 4096
MAX_SOURCES = 256
MAX_TEXT_BYTES = 4096
MAX_INPUT_BYTES = 262144
FIELDS = ("velocity_m_per_s", "angular_velocity_rad_per_s")
ROOT = Path(__file__).resolve().parents[1]
INPUT_GROUPS = {
    "source_numeric_implementation": (
        "ontokin/reach_numeric.py", "ontokin/reach_kinematics.py",
        "ontokin/reach_pose.py", "ontokin/reach_phase.py", "ontokin/reach_runtime.py"),
    "source_numerical_derivation": (
        "docs/engineering/reach-numeric-kernel.md", "docs/engineering/reach-source-kernel.md"),
    "independent_source_reference": ("ontokin/reach_reference.py",),
    "proposed_rate_audit": (
        "tools/reach_source_rates.py", "docs/engineering/reach-rate-acceptance.md"),
}


class RateAuditError(ValueError):
    """Malformed, mismatched or unbounded audit input; never an accepted rate."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


class _Exact:
    """Checked rational operations charged to the caller's existing context."""

    def __init__(self, work):
        bits = getattr(work, "max_operand_bits", None)
        operations = getattr(work, "max_operations", None)
        if (type(bits) is not int or not 1 <= bits <= MAX_OPERAND_BITS or
                type(operations) is not int or not 1 <= operations <= MAX_OPERATIONS or
                not callable(getattr(work, "tick", None))):
            raise RateAuditError("work", "A bounded existing request work context is required")
        self.work, self.bits = work, bits

    def tick(self):
        # Preserve the original cancellation/resource exception and object.
        self.work.tick()

    def value(self, value):
        self.tick()
        if type(value) not in (F, int):
            raise RateAuditError("rational", "Expected an exact Fraction or integer, not a float or boolean")
        value = F(value)
        if max(abs(value.numerator).bit_length(), value.denominator.bit_length()) > self.bits:
            raise RateAuditError("operand_limit", "Exact audit operand exceeds the current request limit")
        return value

    def op(self, first, second, kind):
        first, second = self.value(first), self.value(second)
        self.tick()
        an, ad = abs(first.numerator).bit_length(), first.denominator.bit_length()
        bn, bd = abs(second.numerator).bit_length(), second.denominator.bit_length()
        size = max(an + bn, ad + bd) if kind == "mul" else max(an + bd, bn + ad, ad + bd) + 1
        if size > self.bits:
            raise RateAuditError("operand_limit", "Exact audit intermediate exceeds the current request limit")
        result = {"add": F.__add__, "sub": F.__sub__, "mul": F.__mul__}[kind](first, second)
        return self.value(result)

    def add(self, a, b):
        return self.op(a, b, "add")

    def sub(self, a, b):
        return self.op(a, b, "sub")

    def square(self, value):
        return self.op(value, value, "mul")

    def le(self, a, b):
        return self.sub(a, b).numerator <= 0

    def binary64(self, value):
        self.tick()
        if type(value) is int:
            if abs(value).bit_length() > min(self.bits, 1024):
                raise RateAuditError("binary64", "Integer rate cannot be represented as finite binary64")
            try:
                number = float(value)
            except OverflowError as error:
                raise RateAuditError("binary64", "Integer rate cannot be represented as finite binary64") from error
            if not math.isfinite(number) or F.from_float(number) != value:
                raise RateAuditError("binary64", "Integer rate is not exactly representable as binary64")
        elif type(value) is float and math.isfinite(value):
            number = value
        else:
            raise RateAuditError("binary64", "Rates must be finite binary64 values, never booleans")
        exact = self.value(F.from_float(number))
        return number, exact, struct.pack(">d", number).hex()

    def text(self, value):
        self.tick()
        if type(value) is not str or not value or len(value) > MAX_TEXT_BYTES:
            raise RateAuditError("text", "Expected a nonempty bounded string")
        try:
            encoded = value.encode("utf-8")
        except UnicodeEncodeError as error:
            raise RateAuditError("text", "Audit strings must contain valid UTF-8 text") from error
        if len(encoded) > MAX_TEXT_BYTES:
            raise RateAuditError("text", "UTF-8 string exceeds the audit limit")
        return value

    def clock(self, value):
        if type(value) in (F, int):
            result = self.value(value)
        else:
            value = self.text(value)
            # Do not allow an exponent to trigger an unbounded Fraction allocation.
            if not re.fullmatch(r"-?(?:[0-9]+(?:\.[0-9]+)?|[0-9]+/[0-9]+)", value):
                raise RateAuditError("clock", "Clock must be an exact decimal or integer fraction")
            if 4 * sum(character.isdigit() for character in value) > self.bits:
                raise RateAuditError("operand_limit", "Clock text exceeds the exact operand limit")
            try:
                result = self.value(F(value))
            except ZeroDivisionError as error:
                raise RateAuditError("clock", "Clock denominator is zero") from error
        if result < 0:
            raise RateAuditError("clock", "Source time must be nonnegative")
        return result

    def record(self, value):
        value = self.value(value)
        # Hexadecimal avoids Python's configurable decimal-integer digit limit.
        return {"numerator_hex": hex(value.numerator), "denominator_hex": hex(value.denominator)}


def _vector(value, arithmetic):
    arithmetic.tick()
    if type(value) not in (list, tuple) or len(value) != 3:
        raise RateAuditError("vector", "A rate vector must contain exactly three components")
    return tuple(arithmetic.binary64(component) for component in value)


def _box(value, arithmetic):
    arithmetic.tick()
    if type(value) not in (list, tuple) or len(value) != 3:
        raise RateAuditError("interval", "A reference box must contain exactly three intervals")
    result = []
    for interval in value:
        if type(interval) is not Interval or type(interval.lo) is not F or type(interval.hi) is not F:
            raise RateAuditError("interval", "Reference endpoints must be exact Fraction intervals")
        lo, hi = arithmetic.value(interval.lo), arithmetic.value(interval.hi)
        if not arithmetic.le(lo, hi):
            raise RateAuditError("interval", "Reference interval is reversed")
        result.append((lo, hi))
    return tuple(result)


def _distances(vector, box, arithmetic):
    lower = upper = F(0)
    components = []
    for (_, exact, _), (lo, hi) in zip(vector, box):
        left, right = arithmetic.sub(exact, lo), arithmetic.sub(exact, hi)
        if arithmetic.le(exact, lo):
            nearest = abs(left)
        elif arithmetic.le(hi, exact):
            nearest = abs(right)
        else:
            nearest = F(0)
        farthest = abs(right) if arithmetic.le(abs(left), abs(right)) else abs(left)
        low, high = arithmetic.square(nearest), arithmetic.square(farthest)
        lower, upper = arithmetic.add(lower, low), arithmetic.add(upper, high)
        components.append({"minimum_squared": arithmetic.record(low), "maximum_squared": arithmetic.record(high)})
    return lower, upper, components


def compare_rate_vector(actual, ideal_intervals, allowance, *, work, frozen=None):
    """Apply the proposed Euclidean rule to one vector with exact arithmetic.

    This low-level mathematical check establishes no source identity. A frozen
    vector only receives distance/difference measurements; it never affects the
    proposed verdict or acquires the actual implementation's error allowance.
    """
    arithmetic = _Exact(work)
    vector, box = _vector(actual, arithmetic), _box(ideal_intervals, arithmetic)
    allowance = arithmetic.value(allowance)
    if allowance < 0:
        raise RateAuditError("allowance", "A source arithmetic allowance cannot be negative")
    square = arithmetic.square(allowance)
    lower, upper, components = _distances(vector, box, arithmetic)
    status = ("proved" if arithmetic.le(upper, square) else
              "contradicted" if not arithmetic.le(lower, square) else "unresolved")
    result = {
        "status": status, "actual_binary64_hex": [value[2] for value in vector],
        "actual": [value[0] for value in vector],
        "ideal_intervals": [{"lo": arithmetic.record(lo), "hi": arithmetic.record(hi)} for lo, hi in box],
        "source_arithmetic_allowance": arithmetic.record(allowance),
        "allowance_squared": arithmetic.record(square),
        "minimum_squared_error": arithmetic.record(lower), "maximum_squared_error": arithmetic.record(upper),
        "component_squared_distances": components,
    }
    if frozen is not None:
        frozen_vector = _vector(frozen, arithmetic)
        frozen_lo, frozen_hi, _ = _distances(frozen_vector, box, arithmetic)
        differences = [arithmetic.sub(a[1], b[1]) for a, b in zip(vector, frozen_vector)]
        result["frozen_measurement"] = {
            "basis": "supplied_binary64_preparation_values_with_unproved_oracle_error",
            "acceptance_status": "not_established", "used_for_verdict": False,
            "values": [value[0] for value in frozen_vector],
            "binary64_hex": [value[2] for value in frozen_vector],
            "exact_binary64_equal": all(a[2] == b[2] for a, b in zip(vector, frozen_vector)),
            "actual_minus_frozen": [arithmetic.record(value) for value in differences],
            "minimum_squared_distance_to_ideal_box": arithmetic.record(frozen_lo),
            "maximum_squared_distance_to_ideal_box": arithmetic.record(frozen_hi),
        }
    return result


def _identity(value, arithmetic):
    keys = {"profile", "program_revision", "module_key", "scene_key", "sources"}
    if type(value) is not dict or len(value) != len(keys) or set(value) != keys or value["profile"] != PROFILE:
        raise RateAuditError("source_identity", "Exact planar-reach source identity is required")
    result = {key: arithmetic.text(value[key]) for key in keys - {"sources"}}
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", result["program_revision"]):
        raise RateAuditError("source_identity", "Program revision must be a complete SHA-256 identity")
    sources = value["sources"]
    if type(sources) is not dict or not 1 <= len(sources) <= MAX_SOURCES:
        raise RateAuditError("source_identity", "Source revision inventory is absent or too large")
    result["sources"] = {}
    for key, revision in sources.items():
        arithmetic.text(key)
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", arithmetic.text(revision)):
            raise RateAuditError("source_identity", "Source revision must be a complete SHA-256 identity")
        result["sources"][key] = revision
    return result


def source_identity(model, *, work):
    """Identify the complete compiled source closure, not merely its entry file."""
    arithmetic = _Exact(work)
    if type(model.source_provenance) is not dict or not 1 <= len(model.source_provenance) <= MAX_SOURCES:
        raise RateAuditError("source_identity", "Compiled source provenance is missing or excessive")
    sources = {}
    for source_id, record in model.source_provenance.items():
        arithmetic.tick()
        if type(record) is not dict or record.get("source_id") != source_id:
            raise RateAuditError("source_identity", "Compiled source provenance has a mismatched source ID")
        sources[source_id] = record.get("source_revision")
    return _identity({"profile": model.profile, "program_revision": model.program_revision,
                      "module_key": model.module_key, "scene_key": model.scene_key, "sources": sources}, arithmetic)


def observation_from_snapshot(model, snapshot, *, carriers, work):
    """Extract supplied observations; this helper alone proves no live execution."""
    arithmetic = _Exact(work)
    if type(snapshot) is not dict or type(snapshot.get("frames")) is not dict:
        raise RateAuditError("observation", "Expected an actual source snapshot with frame records")
    if type(carriers) not in (list, tuple) or not 1 <= len(carriers) <= MAX_CARRIERS:
        raise RateAuditError("carrier", "A nonempty bounded carrier list is required")
    records = {}
    for carrier in carriers:
        arithmetic.text(carrier)
        if carrier in records:
            raise RateAuditError("carrier", "Duplicate requested carrier")
        row = snapshot["frames"].get(carrier)
        if type(row) is not dict or any(field not in row for field in FIELDS):
            raise RateAuditError("carrier", "Requested canonical carrier has no complete source rates")
        records[carrier] = {field: [item[0] for item in _vector(row[field], arithmetic)] for field in FIELDS}
    return {"schema_version": OBSERVATION_SCHEMA, "source": source_identity(model, work=work),
            "time_seconds": snapshot.get("time_seconds"), "side": snapshot.get("side"), "carriers": records}


def _observation(value, arithmetic, *, frozen=False):
    keys = {"schema_version", "source", "time_seconds", "side", "carriers"}
    schema = FROZEN_SCHEMA if frozen else OBSERVATION_SCHEMA
    if type(value) is not dict or len(value) != len(keys) or set(value) != keys or value["schema_version"] != schema:
        raise RateAuditError("observation", "Unexpected rate observation schema or fields")
    identity = _identity(value["source"], arithmetic)
    if type(value["time_seconds"]) not in (str, int):
        raise RateAuditError("clock", "Observation clocks must be JSON strings or integers")
    time, side = arithmetic.clock(value["time_seconds"]), value["side"]
    if type(side) is not str or side not in {"before", "after"}:
        raise RateAuditError("side", "An exact before/after observation side is required")
    records = value["carriers"]
    if type(records) is not dict or not 1 <= len(records) <= MAX_CARRIERS:
        raise RateAuditError("carrier", "A nonempty bounded carrier inventory is required")
    normalized = {}
    for carrier, row in records.items():
        arithmetic.text(carrier)
        if (type(row) is not dict or not 1 <= len(row) <= len(FIELDS) or
                not set(row) <= set(FIELDS) or (not frozen and set(row) != set(FIELDS))):
            raise RateAuditError("vector", "Rate record has missing or unexpected fields")
        normalized[carrier] = {field: [item[0] for item in _vector(vector, arithmetic)] for field, vector in row.items()}
    return identity, time, side, normalized


def _frozen_records(frozen, identity, time, side, records, arithmetic):
    if frozen is None:
        return {}
    frozen_identity, frozen_time, frozen_side, values = _observation(frozen, arithmetic, frozen=True)
    if frozen_identity != identity or frozen_time != time or frozen_side != side or not set(values) <= set(records):
        raise RateAuditError("frozen_identity", "Frozen measurements do not match the observed source/time/side/carriers")
    return values


def _json_hash(value, arithmetic):
    digest, size = hashlib.sha256(), 0
    encoder = json.JSONEncoder(sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    for chunk in encoder.iterencode(value):
        arithmetic.tick()
        raw = chunk.encode("ascii")
        size += len(raw)
        if size > MAX_INPUT_BYTES:
            raise RateAuditError("input_limit", "Selected audit observation exceeds its byte limit")
        digest.update(raw)
    return {"bytes": size, "sha256": "sha256:" + digest.hexdigest()}


def _fingerprints(arithmetic):
    if Path(reference_module.__file__).resolve() != ROOT / "ontokin/reach_reference.py":
        raise RateAuditError("implementation_identity", "Imported reference comes from another checkout")
    groups = {}
    for name, paths in INPUT_GROUPS.items():
        rows, aggregate = [], hashlib.sha256()
        for name_in_repo in paths:
            arithmetic.tick()
            path = ROOT / name_in_repo
            if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(ROOT):
                raise RateAuditError("implementation_identity", "Missing or escaping audit implementation input")
            digest, size = hashlib.sha256(), 0
            with path.open("rb") as stream:
                while True:
                    arithmetic.tick()
                    chunk = stream.read(min(4096, MAX_INPUT_BYTES + 1 - size))
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > MAX_INPUT_BYTES:
                        raise RateAuditError("input_limit", "Audit implementation input exceeds its byte limit")
                    digest.update(chunk)
            hexadecimal = digest.hexdigest()
            rows.append({"path": name_in_repo, "bytes": size, "sha256": "sha256:" + hexadecimal})
            aggregate.update((name_in_repo + "\0" + hexadecimal + "\n").encode("ascii"))
        groups[name] = {"sha256": "sha256:" + aggregate.hexdigest(), "inputs": rows}
    return groups


def audit_source_rates(reference, observation, *, work, frozen=None):
    """Audit supplied rates against an actual independently built source reference.

    The source/profile/revision closure and same request-work object must match.
    This validates an asserted observation identity, not the provenance of a
    caller-supplied snapshot. Use execute_source_rate_audit for fresh execution.
    """
    arithmetic = _Exact(work)
    if type(reference) is not ReachReference or reference.a.work is not work:
        raise RateAuditError("work", "Reference and comparison must share the identical existing request context")
    identity, time, side, records = _observation(observation, arithmetic)
    if identity != source_identity(reference.model, work=work):
        raise RateAuditError("source_identity", "Observed profile/program/source closure differs from the reference")
    if not arithmetic.le(time, reference.end):
        raise RateAuditError("clock", "Observed time is outside the certified source prefix")
    frozen_records = _frozen_records(frozen, identity, time, side, records, arithmetic)
    before = _fingerprints(arithmetic)
    observed_digest = _json_hash(observation, arithmetic)
    frozen_digest = None if frozen is None else _json_hash(frozen, arithmetic)
    results = []
    for carrier, record in records.items():
        arithmetic.tick()
        stem = carrier.removesuffix(".frame")
        if carrier != "world" and (not carrier.endswith(".frame") or
                stem not in reference.model.objects and stem not in reference.model.sites):
            raise RateAuditError("carrier", "Unknown or noncanonical source carrier")
        pose = reference.pose_enclosure(carrier, time, side, ideal=True)
        phase = reference.point_phase(carrier, time, side)
        if phase.carrier != carrier or phase.start != time or phase.end != time:
            raise RateAuditError("reference_identity", "Independent phase does not match the exact requested state")
        intervals = (pose.velocity, pose.omega)
        allowances = (phase.source_numeric_velocity_error, phase.source_numeric_angular_velocity_error)
        for field, interval, allowance in zip(FIELDS, intervals, allowances):
            comparison = compare_rate_vector(record[field], interval, allowance, work=work,
                frozen=frozen_records.get(carrier, {}).get(field))
            results.append({"carrier": carrier, "field": field,
                            "units": "m/s" if field == FIELDS[0] else "rad/s",
                            "reference_source_path": list(phase.path), **comparison})
    after = _fingerprints(arithmetic)
    if after != before:
        raise RateAuditError("unstable_inputs", "An identified implementation/derivation input changed during the audit")
    states = {row["status"] for row in results}
    status = "contradicted" if "contradicted" in states else "unresolved" if "unresolved" in states else "proved"
    return {"schema_version": REPORT_SCHEMA, "status": status,
            "criterion_status": "proposed_not_adopted", "release_acceptance": False,
            "source_execution_role": "pending", "full_product_goal_completed": False,
            "observation_provenance": "supplied_identity_assertion",
            "scope": "selected_carriers_at_one_exact_source_time_and_side",
            "source": identity, "time": arithmetic.record(time), "side": side,
            "reference_end": arithmetic.record(reference.end), "selected_observation": observed_digest,
            "frozen_measurement_input": frozen_digest, "input_hashes": before,
            "identified_inputs_stable_during_comparison": True,
            "methods": {"reference_pose": "ReachReference.pose_enclosure(ideal=True)",
                        "source_allowance": "ReachReference.point_phase",
                        "comparison": "exact_Euclidean_interval_box_squared_distance_extrema"},
            "results": results}


def execute_source_rate_audit(bundle, *, time, side, carriers, frozen=None, budgets=None, check=None):
    """Compile, observe and audit one fresh source request without a new budget.

    No source or independent-reference failure is turned into a successful
    sample. A reference unable to reconstruct a valid incoming side, including
    the before-side of a failed boundary, is explicitly unresolved.
    """
    from ontokin.construction import compile_construction
    from ontokin.reach_runtime import ReachSimulator

    compiler = compile_construction(bundle, budgets=budgets, check=check)
    compilation_operations = compiler.budget.operations
    work = compiler.reach_work
    arithmetic = _Exact(work)
    exact_time = arithmetic.clock(time)
    if type(side) is not str or side not in {"before", "after"}:
        raise RateAuditError("side", "An exact before/after observation side is required")
    if compiler.model.program_revision != bundle.program_revision:
        raise RateAuditError("source_identity", "Fresh compiled program revision differs from its supplied bundle")
    before = _fingerprints(arithmetic)
    snapshot = ReachSimulator(compiler.model, work=work).advance(exact_time, side)
    observation = observation_from_snapshot(compiler.model, snapshot, carriers=carriers, work=work)
    identity, observed_time, observed_side, records = _observation(observation, arithmetic)
    if observed_time != exact_time or observed_side != side:
        raise RateAuditError("observation", "Fresh source sample returned another time or side")
    _frozen_records(frozen, identity, exact_time, side, records, arithmetic)
    try:
        reference = build_reference(compiler.model, end=exact_time, work=work)
        report = audit_source_rates(reference, observation, work=work, frozen=frozen)
    except ReferenceError as error:
        if error is getattr(work, "callback_error", None) or error.code == "resource":
            raise
        report = {"schema_version": REPORT_SCHEMA, "status": "unresolved",
                  "criterion_status": "proposed_not_adopted", "release_acceptance": False,
                  "source_execution_role": "pending", "full_product_goal_completed": False,
                  "scope": "selected_carriers_at_one_exact_source_time_and_side",
                  "reason": "reference_unavailable", "reference_error": {"code": error.code, "message": str(error)},
                  "source": identity,
                  "time": arithmetic.record(exact_time), "side": side,
                  "selected_observation": _json_hash(observation, arithmetic), "input_hashes": before,
                  "frozen_measurement_input": None if frozen is None else _json_hash(frozen, arithmetic),
                  "results": []}
    if _fingerprints(arithmetic) != before:
        raise RateAuditError("unstable_inputs", "Identified inputs changed during source observation/reference/audit")
    report.update(observation_provenance="fresh_compile_and_source_snapshot_in_this_call",
                  identified_inputs_stable_during_observation_and_reference=True,
                  compilation_preceded_hash_window=True,
                  compilation_request_operations=compilation_operations,
                  request_operations=compiler.budget.operations,
                  request_operation_limit=compiler.budget.limits["max_operations"],
                  reach_work_operations=work.operations,
                  reach_work_operation_limit=work.max_operations)
    return report
