"""Independent .22 certificate algebra and supplied-byte minima.

The source trajectory comes from torque_reference. All scalar proof work
uses the independent reader arithmetic. Producer plans and reported minima
are never used as the authority for a primitive requirement.
"""
from bisect import bisect_right
from fractions import Fraction as F
import hashlib
import math
from pathlib import Path
import re

from . import reach_conformance as rc

TARGET = "ontokin.glb/0.22"
ACCELERATION_FIELDS = ("angular_acceleration_bound_rad_per_s2",
                       "enclosing_angular_acceleration_bound_rad_per_s2")
CERTIFICATE_KEYS = rc._CERTIFICATE_KEYS | set(ACCELERATION_FIELDS)
NUMERIC_KEYS = tuple(sorted(set(rc._NUMERIC_CERTIFICATE_KEYS) | set(ACCELERATION_FIELDS)))
SOURCE_METHOD = "ontokin.source-pose-projective-dyadic-torque/0.1"
SOURCE_PATHS = (
    "ontokin/reach_numeric.py", "ontokin/reach_kinematics.py", "ontokin/reach_pose.py",
    "ontokin/reach_phase.py", "ontokin/reach_runtime.py", "ontokin/reach_export.py",
    "ontokin/reach_recording_fast.py", "ontokin/reach_recording_capture.py",
    "ontokin/reach_transfer_bounds.py", "ontokin/torque_runtime.py",
    "ontokin/torque_phase.py", "ontokin/torque_recording.py", "ontokin/torque_transfer_bounds.py",
)
DERIVATION_PATHS = (
    "docs/engineering/reach-numeric-kernel.md", "docs/engineering/reach-source-kernel.md",
    "docs/engineering/reach-coaxial-phase-bounds.md", "docs/engineering/reach-carrier-rotation-cursors.md",
    "docs/engineering/reach-recording-certified-planar.md", "docs/engineering/reach-deferred-phase-locations.md",
    "docs/engineering/reach-planning-reuse.md", "docs/engineering/reach-release-cell-envelope.md",
    "docs/language-design/torque-v0.1/SPECIFICATION.md",
    "docs/language-design/torque-v0.1/RECORDING.md",
)


def verify_error_requirement(actual, minimum, arithmetic, path):
    """Read a reduced nonnegative rational without unbounded decimal parsing."""
    if (type(actual) is not dict or set(actual) != {"numerator", "denominator"}
            or type(actual["numerator"]) is not str or type(actual["denominator"]) is not str
            or not 1 <= len(actual["numerator"]) <= 9866
            or not 1 <= len(actual["denominator"]) <= 9865
            or re.fullmatch(r"(?:0|[1-9][0-9]*)", actual["numerator"]) is None
            or re.fullmatch(r"[1-9][0-9]*", actual["denominator"]) is None):
        rc._error("OKE-E-BOUNDARY-HISTORY", "A torque error bound requires canonical bounded rational fields.",
                  details={"path": list(path)})
    def integer(text):
        value = 0
        for index in range(0, len(text), 9):
            arithmetic.tick("independent_torque_rational_digit_block")
            block = text[index:index + 9]
            arithmetic.bits(value.bit_length() + len(block) * 4 + 1)
            value = value * 10 ** len(block) + int(block)
        arithmetic.bits(value.bit_length())
        return value
    numerator, denominator = integer(actual["numerator"]), integer(actual["denominator"])
    first, last = numerator, denominator
    while last:
        arithmetic.tick("independent_torque_rational_reduce")
        first, last = last, first % last
    if first != 1:
        rc._error("OKE-E-BOUNDARY-HISTORY", "A torque error bound is not a reduced canonical rational.",
                  details={"path": list(path)})
    if arithmetic.compare(F(numerator, denominator), minimum) < 0:
        rc._error("OKE-E-BOUNDARY-HISTORY", "A torque error bound omits independently required angular history.",
                  details={"path": list(path)})


def profile_metadata():
    return {"schema_version": "ontokin.torque-recording/0.1", "source_profile": "torque-0.1",
        "motion_model": "finite_cartesian_world_axis_external_couple_on_free_own_sphere",
        "axis_domain": ["world_x", "world_y", "world_z"],
        "descendants": "fixed_rigid_massless_visual_markers",
        "transform_policy": "all_nodes_are_roots_with_baked_world_poses",
        "quantization_contract": "ontokin.torque-quantization/0.1", "live_solver_embedded": False}


def verify_numeric_bases(quantization, *, work):
    root = Path(__file__).resolve().parents[1]
    def aggregate(paths, prefix=""):
        rows = [(name, rc._identified_digest(root / name, work=work)) for name in paths]
        rc._tick(work, "independent_basis_aggregate")
        return hashlib.sha256((prefix + "".join(name + "\0" + digest + "\n"
                                               for name, digest in rows)).encode("utf-8")).hexdigest()
    source = {"name": "OntoKin controlled source poses", "version": "0.3", "method": SOURCE_METHOD,
        "implementation_sha256": "sha256:" + aggregate(SOURCE_PATHS),
        "derivation_sha256": "sha256:" + aggregate(DERIVATION_PATHS)}
    destination = {"name": "ontokin-controlled-three-recording", "version": "0.2.0",
        "implementation_sha256": "sha256:" + aggregate(
            ("tools/reach_destination.mjs", "tools/torque_destination.mjs"),
            "ontokin-controlled-three-recording/0.2.0\n"),
        "derivation_sha256": "sha256:" + rc._identified_digest(
            root / "docs/language-design/torque-v0.1/RECORDING.md", work=work),
        "method": rc.DESTINATION_METHOD}
    if quantization.get("source_numeric_bound_basis") != source:
        rc._error("OKE-E-SOURCE-NUMERIC-BASIS", "The torque source basis does not identify the current complete implementation and derivation.")
    if quantization.get("destination_numeric_bound_basis") != destination:
        rc._error("OKE-E-DESTINATION-NUMERIC-BASIS", "The torque destination basis does not identify the current .22 controlled wrapper and derivation.")


def check_complete_inequalities(record, *, position_tolerance, rotation_tolerance, work=None, model=None):
    """Direct alpha-aware algebra; no inherited constant-rate omission path."""
    rc._tick(work, "independent_certificate_algebra")
    if type(record) is not dict or set(record) != CERTIFICATE_KEYS:
        rc._error("OKE-E-CERTIFICATE-COVERAGE", "Every torque certificate requires exactly the adopted 29 fields.")
    ha = rc.rational_clock(record["h_authored_seconds"], work=work)
    hs = rc.rational_clock(record["h_stored_seconds"], work=work)
    if ha <= 0 or hs <= 0:
        rc._error("OKE-E-CERTIFICATE", "Every torque certificate requires positive authored and stored widths.")
    arithmetic = rc._Bounds(work, cache_intermediates=False)
    quantities = {name: rc._quantity(record, name, work=work) for name in NUMERIC_KEYS}
    return complete_values(ha, hs, quantities, arithmetic.value(position_tolerance),
                           arithmetic.value(rotation_tolerance), arithmetic, model)


def complete_values(ha, hs, quantities, ptol, rtol, arithmetic, model=None):
    q = quantities.__getitem__
    add, mul, div, square = arithmetic.add, arithmetic.mul, arithmetic.div, arithmetic.square
    def require(name, minimum):
        if arithmetic.compare(q(name), minimum) < 0:
            rc._error("OKE-E-CERTIFICATE", "A torque certificate understates a required exact sum.",
                      model=model, details={"quantity": name})
        return q(name)
    radius, vertex = q("landmark_radius_m"), q("local_vertex_error_bound_m")
    omega = q("angular_speed_bound_rad_per_s")
    alpha = q(ACCELERATION_FIELDS[0])
    acceleration = q("carrier_acceleration_bound_m_per_s2")
    enclosing_omega = q("enclosing_angular_speed_bound_rad_per_s")
    enclosing_alpha = q(ACCELERATION_FIELDS[1])
    enclosing_acceleration = q("enclosing_carrier_acceleration_bound_m_per_s2")
    for width, a, w, aa in ((ha, acceleration, omega, alpha),
                             (hs, enclosing_acceleration, enclosing_omega, enclosing_alpha)):
        width2 = square(width)
        rotation = div(mul(add(aa, square(w)), width2), 4)
        position = div(mul(a, width2), 8)
        if (arithmetic.compare(mul(w, width), rc.ARC_LIMIT) > 0
                or arithmetic.compare(rotation, div(rtol, 4)) > 0
                or arithmetic.compare(add(position, mul(radius, rotation)), div(ptol, 4)) > 0):
            rc._error("OKE-E-CERTIFICATE", "The torque interval violates the mandatory acceleration-aware quarter plan.", model=model)
    arc = q("stored_quaternion_arc_upper_rad")
    if arithmetic.compare(arc, rc.ARC_LIMIT) > 0:
        rc._error("OKE-E-CERTIFICATE", "The torque stored quaternion arc exceeds its proved local range.")
    width2 = square(ha)
    difference = require("unit_quaternion_difference_bound", arithmetic.total((
        q("max_endpoint_unit_quaternion_error"), div(mul(alpha, width2), 16),
        div(mul(square(omega), width2), 32), div(square(arc), 8))))
    if arithmetic.compare(difference, F(1, 2)) > 0:
        rc._error("OKE-E-CERTIFICATE", "The torque quaternion comparison exceeds its proved range.")
    require("ideal_rotation_bound_rad", div(mul(add(alpha, square(omega)), width2), 4))
    chord = div(mul(acceleration, width2), 8)
    require("ideal_position_bound_m", chord)
    shift = q("max_endpoint_time_shift_s")
    rotation = require("total_rotation_bound_rad", arithmetic.total((mul(4, difference),
        q("source_numeric_rotation_bound_rad"), q("destination_numeric_rotation_bound_rad"),
        mul(enclosing_omega, shift))))
    carrier = require("carrier_position_bound_m", arithmetic.total((q("max_endpoint_position_error_m"), chord,
        q("source_numeric_position_bound_m"), q("destination_numeric_position_bound_m"),
        mul(q("enclosing_carrier_speed_bound_m_per_s"), shift))))
    position = require("total_position_bound_m", arithmetic.total((carrier, mul(radius, rotation), vertex)))
    if (arithmetic.compare(rotation, rtol) > 0 or arithmetic.compare(carrier, ptol) > 0
            or arithmetic.compare(position, ptol) > 0):
        rc._error("OKE-E-NUMERIC-BOUND", "The complete torque bound exceeds the requested tolerance.")
    return {"position_bound_m": position, "rotation_bound_rad": rotation}


class _TorqueCertificateBatch:
    """At most 64 identical claim sets, proved against every exact member.

    All 23 numerical claims, including both acceleration fields, form the
    group key. Every row still supplies independently derived endpoint,
    source, geometry, phase-coverage and width requirements. Only identical
    claims share one final algebra evaluation, at the greatest required
    minima, magnitude and positive widths. All inequalities are monotone in
    these nonnegative quantities. No producer grouping or plan is read.
    """
    MAX_GROUPS = 64

    def __init__(self, arithmetic, options):
        self.a = arithmetic
        self.ptol = arithmetic.value(options.position_tolerance_m)
        self.rtol = arithmetic.value(options.rotation_tolerance_rad)
        self.groups = {}
        self.maximum_position = self.maximum_rotation = F(0)

    def maximum(self, first, last):
        self.a._cache_operand_domain((first, last))
        if first == last:
            return first
        return first if self.a.compare(first, last) >= 0 else last

    def add(self, record, width, stored_width, minima, magnitude):
        self.a.tick("independent_torque_certificate_member")
        values = []
        for name in NUMERIC_KEYS:
            value = record[name]
            if (type(value) not in (int, float)
                    or type(value) is float and not math.isfinite(value) or value < 0):
                rc._error("OKE-E-CERTIFICATE", "A torque certificate quantity must be finite and nonnegative.",
                          details={"quantity": name})
            if type(value) is int:
                self.a.bits(value.bit_length())
            values.append(value)
        key = tuple(values)
        group = self.groups.get(key)
        if group is None:
            if len(self.groups) == self.MAX_GROUPS:
                self.flush()
            self.a.tick("independent_torque_certificate_group")
            quantities = {name: self.a.value(value) for name, value in zip(NUMERIC_KEYS, key)}
            group = {"quantities": quantities, "minima": dict(minima), "width": width,
                     "stored_width": stored_width, "magnitude": magnitude,
                     "fields": tuple((quantities[name].numerator, quantities[name].denominator)
                                     for name in NUMERIC_KEYS)}
            self.groups[key] = group
        else:
            for name, value in (("width", width), ("stored_width", stored_width), ("magnitude", magnitude)):
                group[name] = self.maximum(group[name], value)
            for name, minimum in minima.items():
                group["minima"][name] = self.maximum(group["minima"][name], minimum)
        # The member's native claims are still the values whose immutable
        # decoded copies supplied this group after all performed callbacks.
        if tuple(record[name] for name in NUMERIC_KEYS) != key:
            rc._error("OKE-E-INDEPENDENT-VALIDATION", "Torque certificate fields changed during admission.")

    def flush(self):
        for key, group in self.groups.items():
            self.a.tick("independent_torque_certificate_group_check")
            quantities = group["quantities"]
            self.a._cache_operand_domain(tuple(quantities.values()))
            # Decode receipts are exact native integers rather than mutable
            # references to producer records. Recheck their binding before
            # the combined proof, including after a live operand-cap change.
            for name, fields in zip(NUMERIC_KEYS, group["fields"]):
                if (quantities[name].numerator, quantities[name].denominator) != fields:
                    rc._error("OKE-E-INDEPENDENT-VALIDATION", "An independent torque claim group changed.")
            def require(name, minimum):
                if self.a.compare(quantities[name], minimum) < 0:
                    rc._error("OKE-E-CERTIFICATE", "A torque certificate understates an independent source or stored-byte primitive.",
                              details={"quantity": name})
            for name, minimum in group["minima"].items():
                require(name, minimum)
            domain = self.a.total((group["magnitude"], quantities["landmark_radius_m"],
                                   quantities["local_vertex_error_bound_m"]))
            if self.a.compare(domain, F(1 << 400)) > 0:
                rc._error("OKE-E-DESTINATION-NUMERIC-BASIS", "The torque artifact exceeds the controlled destination magnitude domain.")
            require("destination_numeric_position_bound_m", self.a.div(self.a.add(domain, 1), 1 << 38))
            require("destination_numeric_rotation_bound_rad", self.a.add(
                self.a.square(quantities["stored_quaternion_arc_upper_rad"]), F(1, 1 << 44)))
            totals = complete_values(group["width"], group["stored_width"], quantities,
                                     self.ptol, self.rtol, self.a)
            self.maximum_position = self.maximum(self.maximum_position, totals["position_bound_m"])
            self.maximum_rotation = self.maximum(self.maximum_rotation, totals["rotation_bound_rad"])
        self.groups.clear()


def verify_certificates(decoded, reference, geometry, tables, endpoint_phases, authored, times,
                        quantization, options, *, work, finalize=None):
    certificates = quantization["interval_certificates"]
    expected_count = (len(authored) - 1) * len(geometry)
    if type(certificates) is not list or len(certificates) != expected_count or expected_count > rc.MAX_CERTIFICATES:
        rc._error("OKE-E-CERTIFICATE-COVERAGE", "Torque certificate coverage is incomplete.")
    identities = {item["identity"]["path"]: (index, item["identity"]) for index, item in geometry.items()}
    rows = {}
    previous_order = None
    for record in certificates:
        rc._tick(work, "independent_certificate_identity")
        if type(record) is not dict or set(record) != CERTIFICATE_KEYS:
            rc._error("OKE-E-CERTIFICATE-COVERAGE", "Every torque certificate must contain exactly the adopted complete fields.")
        left, right, carrier = record["left_key_index"], record["right_key_index"], record["carrier"]
        if (type(left) is not int or type(right) is not int or not 0 <= left < len(authored) - 1
                or right != left + 1 or type(carrier) is not dict or carrier.get("path") not in identities):
            rc._error("OKE-E-CERTIFICATE-COVERAGE", "A torque certificate has invalid interval or carrier identity.")
        index, identity = identities[carrier["path"]]
        if carrier != identity or (left, index) in rows:
            rc._error("OKE-E-CERTIFICATE-COVERAGE", "A torque certificate duplicates or changes a source carrier.")
        # The producer's existing source-node order is the canonical row order.
        order = (left, index)
        if previous_order is not None and order <= previous_order:
            rc._error("OKE-E-CERTIFICATE-COVERAGE", "Torque certificates are not in canonical interval/carrier order.")
        previous_order = order
        rows[order] = record
    tracks = rc._tracks(decoded, geometry, work=work)
    arithmetic = rc._Bounds(work, cache_intermediates=False)
    previous = rc._key_comparisons(reference, geometry, tracks, authored[0], 0, arithmetic,
                                   recording_context=None, endpoint_rows=rows)
    batch = _TorqueCertificateBatch(arithmetic, options)
    for key, (left, right) in enumerate(zip(authored, authored[1:])):
        following = rc._key_comparisons(reference, geometry, tracks, right, key + 1, arithmetic,
            previous=previous, previous_time=left, recording_context=None, endpoint_rows=rows)
        stored_left, stored_right = arithmetic.value(times[key]), arithmetic.value(times[key + 1])
        width, stored_width = arithmetic.sub(right, left), arithmetic.sub(stored_right, stored_left)
        shift = max(abs(arithmetic.sub(stored_left, left)), abs(arithmetic.sub(stored_right, right)))
        low, high = max(F(0), min(left, stored_left)), min(reference.end, max(right, stored_right))
        required = [i for i, (a, b) in enumerate(zip(reference.boundaries, reference.boundaries[1:]))
                    if max(a, low) < min(b, high)]
        source_index = bisect_right(reference.boundaries, left) - 1
        if not reference.boundaries[source_index] <= left < right <= reference.boundaries[source_index + 1]:
            rc._error("OKE-E-PHASE-COVERAGE", "A torque certificate crosses an unretained semantic boundary.")
        numeric_selected = set(required)
        endpoint_index = bisect_right(reference.boundaries, right) - 1
        if endpoint_index < len(reference.boundaries) - 1:
            numeric_selected.add(endpoint_index)
        claims = rc._IntervalCertificateClaims(reference.boundaries, low, high, required, width, stored_width, work)
        for carrier, item in geometry.items():
            record, phases = rows[key, carrier], tables[item["frame"]]
            selected = claims.check(record)
            phase = phases[source_index]
            first, last = previous[carrier], following[carrier]
            numeric_phases = [phases[value] for value in numeric_selected]
            if right == reference.end:
                numeric_phases.append(endpoint_phases[item["frame"]])
            raw_first, raw_last = tracks[carrier]["rotation"][key], tracks[carrier]["rotation"][key + 1]
            # Source lift admission uses full interval maximum speed. Reversal
            # endpoints cannot erase acceleration or interior travel.
            arc = rc._certified_stored_arc(raw_first, raw_last, first, last, phase.angular_speed, width,
                record["stored_quaternion_arc_upper_rad"], arithmetic, source_path_valid=False)
            minima = {"landmark_radius_m": item["radius"], "local_vertex_error_bound_m": item["vertex_error"],
                "angular_speed_bound_rad_per_s": phase.angular_speed,
                ACCELERATION_FIELDS[0]: phase.angular_acceleration,
                "carrier_acceleration_bound_m_per_s2": phase.acceleration,
                "enclosing_carrier_speed_bound_m_per_s": max(phases[value].speed for value in selected),
                "enclosing_carrier_acceleration_bound_m_per_s2": max(phases[value].acceleration for value in selected),
                "enclosing_angular_speed_bound_rad_per_s": max(phases[value].angular_speed for value in selected),
                ACCELERATION_FIELDS[1]: max(phases[value].angular_acceleration for value in selected),
                "max_endpoint_time_shift_s": shift,
                "max_endpoint_position_error_m": max(first["position_error"], last["position_error"]),
                "max_endpoint_unit_quaternion_error": max(first["quaternion_error"], last["quaternion_error"]),
                "stored_quaternion_arc_upper_rad": arc,
                "source_numeric_position_bound_m": max(p.source_numeric_position_error for p in numeric_phases),
                "source_numeric_rotation_bound_rad": max(p.source_numeric_rotation_error for p in numeric_phases)}
            batch.add(record, width, stored_width, minima, max(first["magnitude"], last["magnitude"]))
        previous = following
    batch.flush()
    result = {"max_position_bound_m": batch.maximum_position, "max_rotation_bound_rad": batch.maximum_rotation,
              "interval_certificates_checked": expected_count, "key_pose_comparisons": len(authored) * len(geometry)}
    if finalize is not None:
        result = finalize(result)
    rc._tick(work, "independent_torque_final_admission")
    return result
