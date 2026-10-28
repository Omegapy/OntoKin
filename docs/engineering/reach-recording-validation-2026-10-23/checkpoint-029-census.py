#!/usr/bin/env python3
"""Census captured, unvalidated full P09 bytes without importing OntoKin.

This extends the independently decoded quarter-operand census archived in
checkpoint 027 (driver SHA-256 693b0e03b8906710567c33f7f676cb3e29c57f78db84150e25fafaae49f3d487).
Its conclusions concern supplied bytes, observed reader state, and conditional
static algebra. It never executes the product or certifies source minima,
successful export, destination behavior, measured savings, or release acceptance.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import re
import struct
import sys
import traceback


NUMERIC_KEYS = tuple(sorted((
    "landmark_radius_m", "local_vertex_error_bound_m",
    "angular_speed_bound_rad_per_s", "carrier_acceleration_bound_m_per_s2",
    "enclosing_carrier_speed_bound_m_per_s",
    "enclosing_carrier_acceleration_bound_m_per_s2",
    "enclosing_angular_speed_bound_rad_per_s", "max_endpoint_time_shift_s",
    "max_endpoint_position_error_m", "max_endpoint_unit_quaternion_error",
    "stored_quaternion_arc_upper_rad", "source_numeric_position_bound_m",
    "source_numeric_rotation_bound_rad", "destination_numeric_position_bound_m",
    "destination_numeric_rotation_bound_rad", "unit_quaternion_difference_bound",
    "ideal_rotation_bound_rad", "ideal_position_bound_m",
    "carrier_position_bound_m", "total_position_bound_m", "total_rotation_bound_rad",
)))
ROW_KEYS = set(NUMERIC_KEYS) | {
    "left_key_index", "right_key_index", "carrier", "source_phase_indices",
    "h_authored_seconds", "h_stored_seconds",
}
ARC_LIMIT = Fraction(0.7853981633974483)
MAX_BITS = 32768
CHECKS = 0
PREDECESSOR_SHA256 = "693b0e03b8906710567c33f7f676cb3e29c57f78db84150e25fafaae49f3d487"


def require(condition, message):
    global CHECKS
    CHECKS += 1
    if not condition:
        raise ValueError(message)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError(f"Nonfinite JSON constant: {value}")


def decode_json(raw):
    return json.loads(raw, object_pairs_hook=unique_object, parse_constant=reject_constant)


class Inputs:
    def __init__(self):
        self.data = {}

    def read(self, path):
        path = Path(path).resolve()
        if path not in self.data:
            self.data[path] = path.read_bytes()
        return self.data[path]

    def json(self, path):
        return decode_json(self.read(path))

    def receipts(self):
        result = []
        for path, before in sorted(self.data.items(), key=lambda item: str(item[0])):
            after = path.read_bytes()
            result.append({"path": str(path), "bytes": len(before), "sha256": sha256(before),
                           "bytes_after": len(after), "sha256_after": sha256(after),
                           "unchanged": before == after})
        return result


def ratio(value):
    return {"numerator": str(value.numerator), "denominator": str(value.denominator)}


def ratio_with_bits(value):
    return {**ratio(value), "numerator_bits": value.numerator.bit_length(),
            "denominator_bits": value.denominator.bit_length()}


def read_ratio(record):
    require(type(record) is dict and set(record) == {"numerator", "denominator"},
            "Unexpected rational record fields")
    require(type(record["numerator"]) is str and type(record["denominator"]) is str,
            "Rational record fields must be decimal strings")
    n, d = int(record["numerator"]), int(record["denominator"])
    require(str(n) == record["numerator"] and str(d) == record["denominator"] and d > 0,
            "Noncanonical rational integers")
    value = Fraction(n, d)
    require((value.numerator, value.denominator) == (n, d), "Unreduced rational record")
    return value


def numeric(value):
    require(type(value) in (int, float) and (type(value) is int or math.isfinite(value)) and value >= 0,
            "Certificate scalar must be a finite nonnegative native JSON number")
    return Fraction(value)


def typed_number(value):
    numeric(value)
    result = {"type": type(value).__name__, "value": value, "exact": ratio_with_bits(Fraction(value))}
    if type(value) is float:
        result["binary64_hex"] = value.hex()
        result["binary64_bits"] = struct.pack(">d", value).hex()
    return result


def parse_glb(raw):
    require(len(raw) >= 20, "GLB is too short")
    magic, version, length = struct.unpack_from("<4sII", raw)
    require(magic == b"glTF" and version == 2 and length == len(raw), "Invalid complete GLB header")
    offset, chunks = 12, []
    while offset < len(raw):
        require(offset + 8 <= len(raw), "Truncated GLB chunk header")
        size, kind = struct.unpack_from("<II", raw, offset)
        offset += 8
        require(size % 4 == 0 and offset + size <= len(raw), "Invalid GLB chunk extent")
        chunks.append((kind, raw[offset:offset + size]))
        offset += size
    require(len(chunks) == 2 and [kind for kind, _ in chunks] == [0x4E4F534A, 0x004E4942],
            "Expected exactly one JSON chunk followed by one BIN chunk")
    document, binary = decode_json(chunks[0][1].decode("utf-8")), chunks[1][1]
    require(document.get("asset", {}).get("version") == "2.0", "Unexpected glTF asset version")
    buffers = document["buffers"]
    require(len(buffers) == 1 and "uri" not in buffers[0], "Expected one embedded buffer")
    require(type(buffers[0]["byteLength"]) is int and 0 <= len(binary) - buffers[0]["byteLength"] <= 3,
            "BIN length differs from embedded buffer length")
    return document, binary, chunks[0][1]


def binary32_ratio(bits):
    require(type(bits) is int and 0 <= bits <= 0x7f7fffff, "Clock bits must be finite and nonnegative")
    exponent, significand = (bits >> 23) & 255, bits & 0x7fffff
    if exponent == 0:
        return Fraction(significand, 1 << 149)
    significand |= 1 << 23
    power = exponent - 150
    return Fraction(significand << power) if power >= 0 else Fraction(significand, 1 << -power)


def clock_cell_contains(value, bits):
    center = binary32_ratio(bits)
    lower = Fraction(0) if bits == 0 else (binary32_ratio(bits - 1) + center) / 2
    next_value = Fraction(1 << 128) if bits == 0x7f7fffff else binary32_ratio(bits + 1)
    upper = (center + next_value) / 2
    even = not bits & 1
    return (value > lower or even and value == lower) and (value < upper or even and value == upper)


def scalar_clock(document, binary, index):
    require(type(index) is int and 0 <= index < len(document["accessors"]), "Invalid clock accessor index")
    accessor = document["accessors"][index]
    require(accessor.get("componentType") == 5126 and accessor.get("type") == "SCALAR",
            "Clock accessor must contain binary32 scalars")
    require("sparse" not in accessor and not accessor.get("normalized", False), "Unsupported clock accessor form")
    count = accessor["count"]
    require(type(count) is int and 2 <= count <= 10000, "Invalid bounded clock count")
    view_index = accessor["bufferView"]
    require(type(view_index) is int and 0 <= view_index < len(document["bufferViews"]), "Invalid clock view index")
    view = document["bufferViews"][view_index]
    require(view["buffer"] == 0, "Clock buffer must be embedded buffer zero")
    stride, base = view.get("byteStride", 4), accessor.get("byteOffset", 0)
    start, view_length = view.get("byteOffset", 0), view["byteLength"]
    require(type(stride) is int and stride >= 4 and stride % 4 == 0, "Invalid binary32 stride")
    require(type(base) is int and base >= 0 and base % 4 == 0 and type(view_length) is int
            and base + (count - 1) * stride + 4 <= view_length, "Clock exceeds its buffer view")
    require(type(start) is int and start >= 0 and start % 4 == 0
            and start + view_length <= document["buffers"][0]["byteLength"], "Clock view exceeds embedded buffer")
    words = tuple(struct.unpack_from("<I", binary, start + base + key * stride)[0] for key in range(count))
    values = tuple(binary32_ratio(word) for word in words)
    return values, words, {"accessor": index, "buffer_view": view_index, "count": count,
                           "buffer_view_offset": start, "accessor_offset": base, "byte_stride": stride}


def histogram(values):
    counts = Counter(values)
    return [{"value": str(value), "count": counts[value]} for value in sorted(counts)]


def features(ha, hs, q):
    angular, acceleration = q["angular_speed_bound_rad_per_s"], q["carrier_acceleration_bound_m_per_s2"]
    enclosing_angular = q["enclosing_angular_speed_bound_rad_per_s"]
    enclosing_acceleration = q["enclosing_carrier_acceleration_bound_m_per_s2"]
    return {"exact_width_match": ha == hs, "exact_angular_match": angular == enclosing_angular,
            "exact_acceleration_match": acceleration == enclosing_acceleration,
            "exact_triple_match": ha == hs and angular == enclosing_angular and acceleration == enclosing_acceleration,
            "all_four_coefficients_zero": angular == acceleration == enclosing_angular == enclosing_acceleration == 0,
            "authored_width_dyadic": ha.denominator.bit_count() == 1,
            "stored_width_dyadic": hs.denominator.bit_count() == 1}


class StaticArithmetic:
    """An independent category ledger, never a product work owner or runtime.

    Counters follow inspected scalar calls under the original native/default
    branch assumptions. The observed flush prefix must agree before the
    unexecuted tail estimate is reported as reconciled.
    """
    def __init__(self):
        self.events = []
        self.group = 0
        self.maximum_guard_bits = 0

    def tick(self, category, site):
        self.events.append({"group": self.group, "site": site, "category": category})

    def guard(self, *bits):
        self.maximum_guard_bits = max(self.maximum_guard_bits, *bits)
        require(max(bits, default=0) <= MAX_BITS, "Static scalar domain exceeds original operand limit")

    def value(self, value, site):
        if type(value) is Fraction:
            return value
        self.tick("independent_bound_decode", site + ".decode")
        value = Fraction(value)
        self.guard(value.numerator.bit_length(), value.denominator.bit_length())
        return value

    def op(self, kind, first, last, site):
        a, b = self.value(first, site + ".left"), self.value(last, site + ".right")
        self.tick("independent_exact_" + kind, site)
        an, ad = a.numerator.bit_length(), a.denominator.bit_length()
        bn, bd = b.numerator.bit_length(), b.denominator.bit_length()
        self.guard(an, ad, bn, bd)
        if kind == "add":
            self.guard(max(an + bd, bn + ad) + 1, ad + bd)
            result = a + b
        elif kind == "mul":
            self.guard(an + bn, ad + bd)
            result = a * b
        elif kind == "div":
            require(bool(b), "Static division has a zero denominator")
            self.guard(an + bd, ad + bn)
            result = a / b
        else:
            raise ValueError("Unknown static operation")
        self.guard(result.numerator.bit_length(), result.denominator.bit_length())
        self.events[-1].update({
            "operation": kind, "operand_fields": [ratio(a), ratio(b)], "result_fields": ratio(result),
            "operand_result_flags": {"left_zero": not a, "right_zero": not b,
                "left_one": a == 1, "right_one": b == 1, "result_zero": not result, "result_one": result == 1},
            "exact_identity_candidates": {
                "zero_multiplication": kind == "mul" and (not a or not b),
                "zero_dividend": kind == "div" and not a,
                "multiplication_by_one": kind == "mul" and (a == 1 or b == 1),
                "division_by_one": kind == "div" and b == 1,
                "addition_of_zero": kind == "add" and (not a or not b)},
        })
        return result

    def add(self, a, b, site):
        return self.op("add", a, b, site)

    def mul(self, a, b, site):
        return self.op("mul", a, b, site)

    def div(self, a, b, site):
        return self.op("div", a, b, site)

    def square(self, value, site):
        return self.mul(value, value, site)

    def compare(self, a, b, site):
        a, b = self.value(a, site + ".left"), self.value(b, site + ".right")
        self.guard(a.numerator.bit_length(), a.denominator.bit_length(),
                   b.numerator.bit_length(), b.denominator.bit_length())
        self.tick("independent_exact_compare", site)
        self.guard(a.numerator.bit_length() + b.denominator.bit_length(),
                   b.numerator.bit_length() + a.denominator.bit_length())
        return (a > b) - (a < b)

    def total(self, values, site):
        small = all(type(value) is Fraction and value.numerator.bit_length() <= 256
                    and value.denominator.bit_length() <= 256 for value in values)
        result = Fraction(0)
        if small:
            self.tick("independent_total_domain", site + ".domain")
            for index, value in enumerate(values):
                if not value:
                    continue
                result = value if not result else self.add(result, value, site + f".add{index}")
        else:
            for index, value in enumerate(values):
                result = self.add(result, value, site + f".add{index}")
        return result

    def maximum(self, first, last, site):
        if first == last:
            return first
        return first if self.compare(first, last, site) >= 0 else last


def algebra_group(group, snapshot, tolerances, arithmetic, running):
    """Compute reported-field implications, retaining observed minima labels."""
    a, q, h = arithmetic, group["q"], (group["ha"], group["hs"])
    a.group = group["ordinal"]
    begin, checks = len(a.events), []

    def check(label, lhs, relation, rhs, *, charged=False, observed=False):
        comparison = a.compare(lhs, rhs, label) if charged else (lhs > rhs) - (lhs < rhs)
        passed = comparison >= 0 if relation == ">=" else comparison <= 0
        checks.append({"name": label, "actual": ratio(lhs), "relation": relation,
                       "required": ratio(rhs), "passed": passed,
                       "basis": "observed_reader_minimum_not_independently_certified" if observed else "reported_fields_and_actual_clock_widths"})
        return lhs

    def claim(name, minimum):
        return check(name, q[name], ">=", minimum, charged=True)

    a.tick("independent_certificate_group_check", "group_check")
    for name in snapshot["minima_order"]:
        check("source_minimum." + name, q[name], ">=", read_ratio(snapshot["minima"][name]), charged=True, observed=True)
    magnitude = read_ratio(snapshot["magnitude"])
    radius, vertex = q["landmark_radius_m"], q["local_vertex_error_bound_m"]
    domain = a.total((magnitude, radius, vertex), "destination_domain")
    check("destination_domain_limit", domain, "<=", Fraction(1 << 400), observed=True)
    claim("destination_numeric_position_bound_m", a.div(a.add(domain, 1, "destination_position.add"), 1 << 38, "destination_position.div"))
    arc = q["stored_quaternion_arc_upper_rad"]
    claim("destination_numeric_rotation_bound_rad", a.add(a.square(arc, "destination_rotation.square"), Fraction(1, 1 << 44), "destination_rotation.add"))
    angular, acceleration = q["angular_speed_bound_rad_per_s"], q["carrier_acceleration_bound_m_per_s2"]
    envelope_angular, envelope_acceleration = q["enclosing_angular_speed_bound_rad_per_s"], q["enclosing_carrier_acceleration_bound_m_per_s2"]
    position_tolerance, rotation_tolerance = tolerances
    position_quarter = a.div(position_tolerance, Fraction(4), "position_quarter")
    rotation_quarter = a.div(rotation_tolerance, Fraction(4), "rotation_quarter")
    operands = (*h, angular, acceleration, Fraction(4), Fraction(8), position_tolerance,
                rotation_tolerance, position_quarter, rotation_quarter, *q.values())
    native_terms = all(value.numerator.bit_length() <= 2048 and value.denominator.bit_length() <= 2048 for value in operands)
    all_zero = group["features"]["all_four_coefficients_zero"]
    quarters, authored_terms, admitted = [], {}, False
    for index, (width, acc, omega) in enumerate(((h[0], acceleration, angular), (h[1], envelope_acceleration, envelope_angular))):
        prefix = "authored" if index == 0 else "stored"
        zero_reuse = index == 1 and native_terms and all_zero
        if zero_reuse:
            if not admitted:
                a.tick("independent_certificate_term_admission", "stored.zero_admission")
                admitted = True
            angle = angle_squared = rotation = product = chord = Fraction(0)
            width_squared = a.square(width, prefix + ".width_square")
        else:
            angle = a.mul(omega, width, prefix + ".angle")
            width_squared = a.square(width, prefix + ".width_square")
            angle_squared = a.square(angle, prefix + ".angle_square")
            rotation = a.div(angle_squared, Fraction(4), prefix + ".rotation")
            product = a.mul(acc, width_squared, prefix + ".product")
            chord = a.div(product, Fraction(8), prefix + ".chord")
        if index == 0:
            authored_terms = {"angle_squared": angle_squared, "width_squared": width_squared,
                              "rotation": rotation, "chord": chord}
        check(prefix + ".arc_limit", angle, "<=", ARC_LIMIT, charged=True)
        check(prefix + ".rotation_quarter", rotation, "<=", rotation_quarter, charged=True)
        position = a.add(chord, a.mul(radius, rotation, prefix + ".radius_rotation"), prefix + ".position")
        check(prefix + ".position_quarter", position, "<=", position_quarter, charged=True)
        quarters.append({"role": prefix, "width": ratio_with_bits(width), "angular": ratio_with_bits(omega),
                         "acceleration": ratio_with_bits(acc), "angle": ratio_with_bits(angle),
                         "width_square": ratio_with_bits(width_squared), "rotation": ratio_with_bits(rotation),
                         "chord": ratio_with_bits(chord), "position": ratio_with_bits(position),
                         "accepted_zero_reuse_applicable_under_native_assumptions": zero_reuse,
                         "actual_stored_width_square_retained": index == 1})
    check("stored_arc_limit", arc, "<=", ARC_LIMIT)
    if native_terms:
        if not admitted:
            a.tick("independent_certificate_term_admission", "authored.borrow_admission")
            admitted = True
        angular_width_squared, width_squared = authored_terms["angle_squared"], authored_terms["width_squared"]
    else:
        angular_width_squared = a.square(a.mul(angular, h[0], "late.angle"), "late.angle_square")
        width_squared = a.square(h[0], "late.width_square")
    difference = claim("unit_quaternion_difference_bound", a.total((q["max_endpoint_unit_quaternion_error"],
        a.div(angular_width_squared, Fraction(32), "difference.angle_div"),
        a.div(a.square(arc, "difference.arc_square"), Fraction(8), "difference.arc_div")), "difference.total"))
    check("quaternion_difference_local_range", difference, "<=", Fraction(1, 2))
    claim("ideal_rotation_bound_rad", authored_terms["rotation"] if native_terms else a.div(angular_width_squared, Fraction(4), "late.ideal_rotation"))
    chord = authored_terms["chord"] if native_terms else a.div(a.mul(acceleration, width_squared, "late.chord_product"), Fraction(8), "late.chord")
    claim("ideal_position_bound_m", chord)
    rotation = claim("total_rotation_bound_rad", a.total((a.mul(Fraction(4), difference, "rotation.difference"),
        q["source_numeric_rotation_bound_rad"], q["destination_numeric_rotation_bound_rad"],
        a.mul(envelope_angular, q["max_endpoint_time_shift_s"], "rotation.shift")), "rotation.total"))
    carrier = claim("carrier_position_bound_m", a.total((q["max_endpoint_position_error_m"], chord,
        q["source_numeric_position_bound_m"], q["destination_numeric_position_bound_m"],
        a.mul(q["enclosing_carrier_speed_bound_m_per_s"], q["max_endpoint_time_shift_s"], "carrier.shift")), "carrier.total"))
    total = claim("total_position_bound_m", a.total((carrier, a.mul(radius, rotation, "total.radius_rotation"), vertex), "position.total"))
    check("carrier_tolerance", carrier, "<=", position_tolerance)
    check("position_tolerance", total, "<=", position_tolerance)
    check("rotation_tolerance", rotation, "<=", rotation_tolerance)
    running[0] = a.maximum(running[0], total, "maximum_position")
    running[1] = a.maximum(running[1], rotation, "maximum_rotation")
    return {"all_reported_field_and_observed_minimum_checks_pass": all(item["passed"] for item in checks),
            "observed_minima_independently_certified": False,
            "native_term_numeric_domain": native_terms,
            "native_dispatch_and_ownership_assumed_for_static_cost": True,
            "quarter_plans": quarters, "checks": checks,
            "static_events_start": begin, "static_events_end": len(a.events),
            "static_category_counts": dict(sorted(Counter(item["category"] for item in a.events[begin:]).items())),
            "static_operations": len(a.events) - begin,
            "reported_result": {"position_bound_m": ratio(total), "rotation_bound_rad": ratio(rotation)}}


def reconcile_snapshot(group, snapshot):
    require(snapshot["ordinal"] == group["ordinal"], "Snapshot group order differs from reconstructed first appearance")
    require(set(snapshot["quantities"]) == set(NUMERIC_KEYS), "Snapshot quantity inventory differs")
    require(len(snapshot["key"]) == len(NUMERIC_KEYS), "Snapshot numeric key has wrong length")
    for name, raw, captured in zip(NUMERIC_KEYS, group["key"], snapshot["key"]):
        require(set(captured) == {"type", "value"} and captured["type"] == type(raw).__name__, "Snapshot key numeric type differs")
        require(type(captured["value"]) is type(raw) and captured["value"] == raw, "Snapshot key value differs")
        if type(raw) is float:
            require(struct.pack(">d", captured["value"]) == struct.pack(">d", raw), "Snapshot key float bits differ")
        require(read_ratio(snapshot["quantities"][name]) == group["q"][name], "Snapshot quantity differs from actual JSON numeric decode")
    require(read_ratio(snapshot["width"]) == group["ha"] and read_ratio(snapshot["stored_width"]) == group["hs"],
            "Snapshot width maxima differ from actual decoded clock gaps")
    require(type(snapshot["minima_order"]) is list and len(snapshot["minima_order"]) == len(snapshot["minima"])
            and set(snapshot["minima_order"]) == set(snapshot["minima"])
            and set(snapshot["minima"]).issubset(NUMERIC_KEYS),
            "Snapshot minima order/inventory differs")
    read_ratio(snapshot["magnitude"])
    thresholds = snapshot["thresholds"]
    if thresholds is not None:
        require(type(thresholds["used"]) is bool and type(thresholds["enabled"]) is bool, "Invalid threshold-state flags")
        require(len(thresholds["fields"]) == len(NUMERIC_KEYS), "Threshold quantity receipt length differs")
        for name, fields in zip(NUMERIC_KEYS, thresholds["fields"]):
            require(fields is not None and read_ratio(fields) == group["q"][name], "Threshold reported quantity receipt differs")
        require(set(thresholds["extent_fields"]) == {"width", "stored_width", "magnitude"}, "Threshold extent receipt inventory differs")
        for name, record in thresholds["extent_fields"].items():
            value = read_ratio(snapshot[name])
            require(read_ratio(record["value"]) == value and record["fields"] is not None
                    and read_ratio(record["fields"]) == value, "Threshold extent fields differ")
        require(set(thresholds["minimum_fields"]) == set(snapshot["minima"]), "Threshold minima inventory differs")
        for name, record in thresholds["minimum_fields"].items():
            value = read_ratio(snapshot["minima"][name])
            require(read_ratio(record["value"]) == value and record["fields"] is not None
                    and read_ratio(record["fields"]) == value, "Threshold retained minimum receipt differs")
        for name, widths in thresholds["domains"].items():
            require(name in snapshot["minima"] and type(widths) is list and len(widths) == 4
                    and all(type(value) is int and value >= 0 for value in widths), "Invalid threshold discarded-domain receipt")
    return {"numeric_key_and_quantities_match": True, "actual_width_maxima_match": True,
            "threshold_receipts_match_when_present": True,
            "thresholds_used": None if thresholds is None else thresholds["used"],
            "thresholds_enabled": None if thresholds is None else thresholds["enabled"],
            "observed_minima_independently_certified": False,
            "observed_magnitude_independently_certified": False}


def source_receipts(repo, document, inputs):
    base = repo / "docs/language-design/planar-reach-v0.1"
    manifest = inputs.json(base / "p09.files.json")
    records = [manifest["entry"], *manifest["modules"]]
    sources = document["extras"]["ontokin"]["program"]["sources"]
    require(type(sources) is dict and "entry" in sources, "Missing supplied program source identities")
    by_filename = {value["filename"]: value for value in sources.values()}
    require(len(by_filename) == len(sources) == len(records), "Source closure filename coverage differs")
    result = []
    for item in records:
        path = (base / item["path"]).resolve()
        require(path.is_relative_to(base.resolve()), "Source manifest path escapes fixture directory")
        raw = inputs.read(path)
        require(item["filename"] in by_filename and by_filename[item["filename"]]["source_revision"] == "sha256:" + sha256(raw),
                "Supplied program source digest differs from unchanged fixture bytes")
        result.append({"path": str(path), "filename": item["filename"], "bytes": len(raw), "sha256": sha256(raw)})
    entry = inputs.read(base / manifest["entry"]["path"]).decode("utf-8")
    require(re.search(r"duration\s*=\s*3\[s\]\s*;", entry) is not None
            and re.search(r"reach_to\([^;]+,\s*2\[s\]\s*,\s*elbow_positive\)", entry) is not None
            and re.search(r"at\s+0\[s\]\s+sequence\s*\{\s*start\s+reach\s*;\s*\}", entry) is not None,
            "P09 declared request/action clocks differ from inspected original fixture")
    for relative in ("ontokin/reach_conformance.py", "ontokin/gltf.py", "ontokin/reach_numeric.py", "ontokin/reach_reference_plan.py"):
        inputs.read(repo / relative)
    return result


def repeated_operand_inventory(groups, tolerances):
    keys = {
        "authored_width_square": lambda g: (g["ha"],),
        "stored_width_square": lambda g: (g["hs"],),
        "authored_angle": lambda g: (g["q"]["angular_speed_bound_rad_per_s"], g["ha"]),
        "stored_angle": lambda g: (g["q"]["enclosing_angular_speed_bound_rad_per_s"], g["hs"]),
        "arc_square": lambda g: (g["q"]["stored_quaternion_arc_upper_rad"],),
    }
    result = {}
    for name, get_key in keys.items():
        occurrences = {}
        for group in groups:
            occurrences.setdefault(get_key(group), []).append(group["ordinal"])
        result[name] = [{"operands": [ratio_with_bits(value) for value in key], "groups": ordinals}
                        for key, ordinals in occurrences.items()]
    result["tolerance_divisions"] = {"position": ratio(tolerances[0]), "rotation": ratio(tolerances[1]),
        "equal_tolerances": tolerances[0] == tolerances[1], "uses_per_tolerance": len(groups),
        "measured_savings": None}
    return result


def exact_scalar_site_inventory(events, failure_index, deficit):
    """Enumerate remaining exact identities in the accepted scalar ledger.

    Already omitted/borrowed operations do not occur in this ledger. Candidate
    counts are optimistic omission ceilings before new overhead, never measured
    savings or proof that a particular combined implementation is valid.
    """
    classes = ("zero_multiplication", "zero_dividend", "multiplication_by_one",
               "division_by_one", "addition_of_zero")
    candidate_indices, by_class = set(), {}
    for name in classes:
        selected = [(index, event) for index, event in enumerate(events)
                    if event.get("exact_identity_candidates", {}).get(name, False)]
        candidate_indices.update(index for index, _ in selected)
        expressions = {}
        for index, event in selected:
            row = expressions.setdefault(event["site"], {"site": event["site"], "category": event["category"],
                "groups": [], "event_indices": [], "within_reconciled_prefix": 0, "unexecuted_tail": 0})
            row["groups"].append(event["group"])
            row["event_indices"].append(index)
            row["within_reconciled_prefix" if index < failure_index else "unexecuted_tail"] += 1
        by_class[name] = {"sites": len(selected), "expressions": list(expressions.values())}
    pairs = {}
    for index, event in enumerate(events):
        if "operation" not in event:
            continue
        key = (event["group"], event["operation"],
               tuple((item["numerator"], item["denominator"]) for item in event["operand_fields"]))
        pairs.setdefault(key, []).append(index)
    duplicate_indices, duplicates = set(), []
    for (group, kind, fields), indices in pairs.items():
        if len(indices) < 2:
            continue
        duplicates.append({"group": group, "operation": kind,
            "operand_fields_after_native_decode": [{"numerator": n, "denominator": d} for n, d in fields],
            "event_indices": indices, "sites": [events[index]["site"] for index in indices],
            "later_occurrence_sites": len(indices) - 1,
            "later_occurrences_not_already_scalar_identity_sites": sum(index not in candidate_indices for index in indices[1:])})
        duplicate_indices.update(indices[1:])
    extra_duplicates = duplicate_indices - candidate_indices
    combined = candidate_indices | duplicate_indices
    zero_mul_div = {index for index, event in enumerate(events)
                   if event.get("operation") in ("mul", "div") and event["operand_result_flags"]["result_zero"]}
    per_group = []
    for group in sorted({event["group"] for event in events}):
        indices = {index for index, event in enumerate(events) if event["group"] == group}
        per_group.append({"group": group, "zero_result_mul_div_sites": len(zero_mul_div & indices),
            "unique_scalar_identity_sites": len(candidate_indices & indices),
            "additional_exact_duplicate_sites": len(extra_duplicates & indices),
            "combined_optimistic_omission_ceiling": len(combined & indices)})
    return {"scope": "Static actual-expression ledger for complete final flush on captured reported values; no product execution",
        "counts_are_measured_savings": False, "new_guard_or_admission_overhead_included": False,
        "existing_omitted_zero_quarter_and_borrowed_terms_excluded": True,
        "class_counts_overlap": True, "classes": by_class,
        "zero_result_mul_div_sites": len(zero_mul_div),
        "unique_scalar_identity_sites": len(candidate_indices),
        "same_order_exact_operand_duplicates_within_group": duplicates,
        "additional_duplicate_sites_after_identity_overlap_removed": len(extra_duplicates),
        "combined_optimistic_scalar_omission_ceiling": len(combined),
        "conditional_deficit": deficit,
        "combined_optimistic_ceiling_can_cover_conditional_deficit": len(combined) >= deficit,
        "optimistic_margin_before_new_overhead": len(combined) - deficit,
        "per_group": per_group,
        "required_proof": "Every omitted scalar operation must retain original operand/prospective/result guards, current native owners and operand fields, failure ordering, callback fallback and every claim comparison; any receipt/admission overhead must be measured on the complete request."}


def analyze(capture_dir, repo, inputs):
    capture = inputs.json(capture_dir / "capture.json")
    snapshots = inputs.json(capture_dir / "flush-snapshots.json")
    request = inputs.json(capture_dir / "stock/P09/request-result.json")
    report = inputs.json(capture_dir / "stock/report.json")
    require(capture["status"] == "captured_failed_request" and request["status"] == report["status"] == "failed",
            "Evidence must retain the actually failed exporter request and command")
    require(capture["source_commit"] == report["source_commit"] and capture["source_tree"] == report["source_tree"]
            and capture["inputs_stable"] is True and report["inputs_stable"] is True,
            "Capture and unchanged builder source identities differ or inputs changed")
    require(bool(capture["identity_checks"]) and all(value is True for value in capture["identity_checks"].values()),
            "Capture identity/restoration checks are not all true")
    require(capture["work_limits"] == {"max_operations": 100000, "max_elapsed_ms": 30000,
            "max_operand_bits": 32768, "max_cache_entries": 256}
            and capture["budget_limits"] == {"max_objects": 1000, "max_operations": 100000,
                "max_result_items": 1000, "max_elapsed_ms": 30000, "max_value_entries": 100000},
            "Capture does not retain all original resource limits")
    require([frame["function"] for frame in capture["exception"]["frames"][-11:]] ==
            ["flush", "_complete_inequality_values", "calculate", "mul", "op", "tick", "_tick", "charge", "tick", "exceeded", "fail"],
            "Captured exception does not retain the inspected underlying first-angle failure suffix")
    require(request["case_id"] == capture["original_request"]["case_id"] == "P09", "Unexpected captured case")
    original = capture["original_request"]
    require(original["end"] == "3" and original["fps"] == 1 and original["helpers"] is False,
            "Captured request is not the unchanged original full P09 settings")
    require({key: value for key, value in original.items() if key != "case_id"} == request["options"]
            and request["max_operations"] == 100000,
            "Captured options or operation cap differ from the actual failed request receipt")
    require(capture["reader_calls"] == capture["flush_calls"] == 1 and len(snapshots["snapshots"]) == 1,
            "Expected exactly one reader call and one final flush")
    require(capture["artifact"]["path"] == "unvalidated-reader-input.glb", "Capture must retain unvalidated filename")
    raw = inputs.read(capture_dir / "unvalidated-reader-input.glb")
    require(capture["artifact"]["sha256"] == sha256(raw) and capture["artifact"]["bytes"] == len(raw),
            "Captured byte identity differs from its receipt")
    require(capture["work_after_request"] == request["work"]
            and capture["shared_operations_after_request"] == request["operations"] == 100001,
            "Failed-request work or unchanged shared refusal differs")
    document, binary, json_chunk = parse_glb(raw)
    fixture_sources = source_receipts(repo, document, inputs)
    quantization = document["extras"]["ontokin"]["reach_quantization"]
    require(quantization["schema_version"] == "ontokin.reach-quantization/0.1", "Unexpected quantization schema")
    require(len(document["animations"]) == 1, "Expected one recorded animation")
    animation = document["animations"][0]
    samplers = animation["samplers"]
    require(bool(samplers), "Animation has no samplers")
    stored, words, clock_layout = scalar_clock(document, binary, samplers[0]["input"])
    layouts = [clock_layout]
    for index in sorted({sampler["input"] for sampler in samplers} - {samplers[0]["input"]}):
        values, bits, layout = scalar_clock(document, binary, index)
        require((values, bits) == (stored, words), "Animation samplers do not share complete actual clocks")
        layouts.append(layout)
    exact_records = animation["extras"]["ontokin"]["exact_times_seconds"]
    authored = tuple(read_ratio(item) for item in exact_records)
    retained = quantization["retained_keys"]
    require(len(authored) == len(retained) == len(stored) == 205, "Original P09 clock coverage differs")
    require(authored[0] == stored[0] == 0 and authored[-1] == stored[-1] == 3, "Original request endpoints differ")
    require(all(a < b for a, b in zip(authored, authored[1:])) and all(a < b for a, b in zip(stored, stored[1:])),
            "Actual clock axis is not strictly increasing")
    boundaries = tuple(Fraction(item["source_seconds"]) for item in document["extras"]["ontokin"]["boundary_states"])
    require(boundaries == (Fraction(0), Fraction(2), Fraction(3)), "Supplied P09 phase boundaries differ from inspected source clocks")
    require(tuple(Fraction(value) for value in animation["extras"]["ontokin"]["boundary_times_seconds"]) == boundaries,
            "Animation and supplied state-boundary labels differ")
    clock_records = []
    for index, (authored_value, stored_value, word, item, authored_record) in enumerate(zip(authored, stored, words, retained, exact_records)):
        require(set(item) == {"authored_seconds", "stored_seconds", "stored_binary32_bits", "semantic_boundary"}, "Retained clock fields differ")
        require(item["authored_seconds"] == authored_record and numeric(item["stored_seconds"]) == stored_value
                and item["stored_binary32_bits"] == f"{word:08x}", "Retained labels differ from actual clocks")
        require(type(item["semantic_boundary"]) is bool and item["semantic_boundary"] == (authored_value in boundaries),
                "Semantic boundary label differs")
        require(clock_cell_contains(authored_value, word), "Actual binary32 clock fails independent ties-to-even midpoint test")
        clock_records.append({"index": index, "authored": ratio(authored_value), "stored": ratio(stored_value),
                              "binary32_bits": f"{word:08x}", "shift": ratio(abs(authored_value - stored_value)),
                              "semantic_boundary": item["semantic_boundary"]})
    nodes = document["nodes"]
    node_order, identities = {}, {}
    for index, node in enumerate(nodes):
        metadata = node["extras"]["ontokin"]
        require(metadata["kind"] == "object" and node["name"] == metadata["path"], "Unexpected helper or carrier path")
        require(node["name"] not in node_order, "Duplicate carrier path")
        node_order[node["name"]] = index
        identities[node["name"]] = {"path": metadata["path"], "element_id": metadata["element_id"]}
    rows = {}
    for record in quantization["interval_certificates"]:
        require(type(record) is dict and set(record) == ROW_KEYS, "Certificate row fields differ")
        left, right, identity = record["left_key_index"], record["right_key_index"], record["carrier"]
        require(type(left) is int and type(right) is int and 0 <= left < len(authored) - 1 and right == left + 1,
                "Invalid certificate interval")
        require(type(identity) is dict and identity.get("path") in identities and identity == identities[identity["path"]],
                "Certificate carrier identity differs from actual node metadata")
        carrier = identity["path"]
        row_id = (left, node_order[carrier])
        require(row_id not in rows, "Duplicate carrier/interval certificate")
        ha, hs = authored[right] - authored[left], stored[right] - stored[left]
        require(ha == read_ratio(record["h_authored_seconds"]) and hs == read_ratio(record["h_stored_seconds"]),
                "Certificate width label differs from actual authored/stored gap")
        low, high = max(Fraction(0), min(authored[left], stored[left])), min(Fraction(3), max(authored[right], stored[right]))
        required = tuple(index for index, (a, b) in enumerate(zip(boundaries, boundaries[1:])) if max(a, low) < min(b, high))
        selected = record["source_phase_indices"]
        require(type(selected) is list and all(type(value) is int and 0 <= value < len(boundaries) - 1 for value in selected)
                and len(selected) == len(set(selected)) and set(required).issubset(selected)
                and all(max(low, boundaries[value]) <= min(high, boundaries[value + 1]) for value in selected),
                "Supplied phase indices omit positive overlap or name an unrelated phase")
        q = {name: numeric(record[name]) for name in NUMERIC_KEYS}
        rows[row_id] = {"left": left, "right": right, "node": node_order[carrier], "carrier": carrier,
                        "ha": ha, "hs": hs, "q": q, "key": tuple(record[name] for name in NUMERIC_KEYS),
                        "selected": tuple(selected), "required": required}
    require(len(nodes) == 6 and len(rows) == (len(authored) - 1) * len(nodes) == 1224,
            "Complete original P09 interval/carrier coverage differs")
    groups, mapping = [], {}
    for row_id in sorted(rows):
        row = rows[row_id]
        key = row["key"]
        if key not in mapping:
            require(len(groups) < 64, "This final-flush census requires one bounded reader batch")
            group = {"ordinal": len(groups) + 1, "key": key, "q": row["q"], "ha": row["ha"], "hs": row["hs"], "rows": []}
            groups.append(group)
            mapping[key] = group
        group = mapping[key]
        group["ha"], group["hs"] = max(group["ha"], row["ha"]), max(group["hs"], row["hs"])
        group["rows"].append(row)
    snapshot = snapshots["snapshots"][0]
    require(snapshot["ordinal"] == 1 and tuple(snapshot["numeric_keys"]) == NUMERIC_KEYS, "Unexpected flush or numeric key order")
    require(len(groups) == len(snapshot["groups"]) == 12, "Full-input group count differs from captured final batch")
    require(snapshot["thresholds_enabled"] is True and snapshot["restart_requested"] is False,
            "Captured flush is not the original unrestarted threshold path")
    tolerances = (read_ratio(snapshot["position_tolerance"]), read_ratio(snapshot["rotation_tolerance"]))
    require(tolerances == (numeric(quantization["position_tolerance_m"]), numeric(quantization["rotation_tolerance_rad"])),
            "Captured tolerances differ from supplied byte labels")
    final_work, entry_work = capture["work_after_request"], snapshot["work_at_entry"]
    counts = final_work["counts"]
    for name, expected in {"independent_retained_clock": 205, "independent_certificate_member": 1224,
                           "independent_certificate_group": 12, "independent_certificate_group_check": 11,
                           "independent_certificate_term_admission": 10}.items():
        require(counts.get(name, 0) == expected, f"Observed original P09 work count differs: {name}")
    running = [read_ratio(snapshot["max_position"]), read_ratio(snapshot["max_rotation"])]
    require(running == [Fraction(0), Fraction(0)], "Unexpected prior flush maxima")
    arithmetic, output_groups = StaticArithmetic(), []
    for group, captured in zip(groups, snapshot["groups"]):
        group["features"] = features(group["ha"], group["hs"], group["q"])
        reconciliation = reconcile_snapshot(group, captured)
        algebra = algebra_group(group, captured, tolerances, arithmetic, running)
        member_records = [{"left_key_index": row["left"], "right_key_index": row["right"], "carrier": row["carrier"],
                           "node_index": row["node"], "selected_source_phases": list(row["selected"]),
                           "required_positive_overlap_phases": list(row["required"])} for row in group["rows"]]
        output_groups.append({"ordinal": group["ordinal"], "member_count": len(group["rows"]),
            "first_appearance": member_records[0], "last_appearance": member_records[-1],
            "carriers": dict(Counter(row["carrier"] for row in group["rows"])),
            "members": member_records, "numeric_key": [typed_number(value) for value in group["key"]],
            "quantities": {name: ratio_with_bits(value) for name, value in group["q"].items()},
            "maximum_authored_width": ratio_with_bits(group["ha"]), "maximum_stored_width": ratio_with_bits(group["hs"]),
            "authored_width_histogram": histogram(row["ha"] for row in group["rows"]),
            "stored_width_histogram": histogram(row["hs"] for row in group["rows"]),
            "features": group["features"], "snapshot_reconciliation": reconciliation,
            "observed_reader_minima": captured["minima"], "observed_reader_magnitude": captured["magnitude"],
            "algebra": algebra})
    failure_indices = [index for index, event in enumerate(arithmetic.events) if event["group"] == 11 and event["site"] == "authored.angle"]
    require(len(failure_indices) == 1, "Static ledger lacks the known refused first authored-angle operation")
    failed_index = failure_indices[0]
    observed_delta = {name: counts.get(name, 0) - entry_work["counts"].get(name, 0)
                      for name in set(counts) | set(entry_work["counts"])}
    observed_delta = {name: value for name, value in observed_delta.items() if value}
    modeled_prefix = dict(Counter(event["category"] for event in arithmetic.events[:failed_index]))
    prefix_equal = modeled_prefix == observed_delta and final_work["operations"] - entry_work["operations"] == failed_index
    shared_equal = capture["shared_operations_after_request"] - snapshot["shared_operations_at_entry"] == failed_index + 1
    tail_events = arithmetic.events[failed_index:]
    final_report_events = {"independent_bound_decode": 3, "independent_report_rounding": 3,
                           "independent_exact_compare": 3, "checkpoint": 1}
    projected_total = snapshot["shared_operations_at_entry"] + len(arithmetic.events) + sum(final_report_events.values())
    equal_groups = [group["ordinal"] for group in groups if group["features"]["exact_triple_match"]]
    zero_equal = [group["ordinal"] for group in groups if group["features"]["exact_triple_match"] and group["features"]["all_four_coefficients_zero"]]
    # The held equal-triple identity could omit six stored scalar operations;
    # accepted canonical-zero reuse already omits five in zero groups. This
    # upper bound excludes any new admission/guard overhead and is not savings.
    equal_width_incremental_ceiling = sum(1 if group["features"]["all_four_coefficients_zero"] else 6
                                          for group in groups if group["features"]["exact_triple_match"])
    scalar_sites = exact_scalar_site_inventory(arithmetic.events, failed_index, max(0, projected_total - 100000))
    all_algebra = all(group["algebra"]["all_reported_field_and_observed_minimum_checks_pass"] for group in output_groups)
    cost = {"kind": "conditional_static_estimate_not_measured_full_cost", "observed_prefix_categories": dict(sorted(observed_delta.items())),
        "modeled_prefix_categories": dict(sorted(modeled_prefix.items())), "observed_prefix_category_and_work_totals_match": prefix_equal,
        "shared_refused_charge_accounting_matches": shared_equal,
        "failed_attempt_is_not_counted_in_work_record": True,
        "first_refused_static_event": {"index": failed_index, **arithmetic.events[failed_index]},
        "completed_flush_prefix_operations": failed_index, "modeled_complete_flush_operations": len(arithmetic.events),
        "remaining_flush_operations_including_refused_attempt_once": len(tail_events),
        "remaining_flush_categories": dict(sorted(Counter(event["category"] for event in tail_events).items())),
        "conditional_final_report_and_return_categories": final_report_events,
        "conditional_final_report_and_return_operations": sum(final_report_events.values()),
        "conditional_complete_shared_operations": projected_total,
        "conditional_reduction_needed_for_100000": max(0, projected_total - 100000),
        "maximum_modeled_prospective_or_result_bits": arithmetic.maximum_guard_bits,
        "all_static_predicates_pass_on_reported_fields_and_observed_minima": all_algebra,
        "source_minima_and_final_source_admission_independently_certified": False,
        "assumptions": ["Original native dispatch and callback owners remain admitted with the default operand domain.",
            "All remaining predicates and source ownership/receipt checks succeed without replay or cancellation.",
            "Final source admission is callback-free; this census does not execute or certify it.",
            "Three outward report conversions each decode, charge report rounding and compare; the final exporter check charges checkpoint.",
            "Surface/geometry verification, report copying/hashing/environment reads and successful ExportResult construction still must complete."],
        "events": arithmetic.events}
    result = {"case_id": "P09", "captured_request_status": "failed", "export_result_returned": False,
        "source_commit": capture["source_commit"], "source_tree": capture["source_tree"],
        "artifact": {"path": "unvalidated-reader-input.glb", "bytes": len(raw), "sha256": sha256(raw),
                     "validation_status": "unvalidated_reader_input", "json_chunk_sha256": sha256(json_chunk)},
        "unchanged_fixture_sources": fixture_sources, "clock_count": len(stored), "carrier_count": len(nodes),
        "certificate_count": len(rows), "group_count": len(groups), "clock_accessors": layouts,
        "actual_binary32_clock_cells_verified": True, "width_labels_verified_against_actual_clock_gaps": True,
        "phase_boundary_source_basis": "Original P09 declares start 0, reach duration 2 and scene duration 3; observed labels agree.",
        "supplied_phase_boundaries": [ratio(value) for value in boundaries], "clocks": clock_records,
        "grouping": "21-key native numeric tuple equality, traversed by adjacent interval then decoded node order; first appearance assigns ordinal",
        "numeric_keys": list(NUMERIC_KEYS), "groups": output_groups,
        "groups_11_and_12": [group for group in output_groups if group["ordinal"] in (11, 12)],
        "raw_counter_reconciliation": {"retained_clocks": 205, "certificate_members": 1224, "created_groups": 12,
            "begun_group_checks": 11, "completed_term_admissions": 10, "shared_operations_at_refusal": 100001,
            "numerical_cache_entries_after_unwind": final_work["cache_entries"]},
        "static_remaining_work": cost, "repeated_operands": repeated_operand_inventory(groups, tolerances),
        "exact_scalar_identity_inventory": scalar_sites,
        "optimization_screen": {"equal_triple_groups": equal_groups, "equal_triple_zero_groups": zero_equal,
            "equal_triple_incremental_omitted_operation_ceiling": equal_width_incremental_ceiling,
            "ceiling_includes_new_overhead": False, "measured_savings": None,
            "ceiling_can_cover_conditional_remaining_deficit": equal_width_incremental_ceiling >= max(0, projected_total - 100000),
            "next_bounded_proposal": "Derive a bounded native scalar identity and exact-operand reuse proof for the enumerated final-flush sites, retaining all guards and claims; compare its complete-request savings including admission overhead against the conditional deficit before adoption.",
            "selection_status": "Census-supported proposal only; no optimization implemented or accepted.",
            "required_followup": "Separate derivation, hostile/equivalence tests, positive complete-request savings and acceptable elapsed controls; then related cohort and all original 28."},
        "census_required_checks": {"all_groups_reconcile_with_snapshot": True,
            "observed_flush_prefix_matches_independent_static_ledger": prefix_equal,
            "shared_refused_charge_accounting_matches": shared_equal}}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    inputs = Inputs()
    driver = inputs.read(Path(__file__).resolve())
    result = {"schema_version": "ontokin.p09-full-input-census/0.1", "status": "pending",
        "started_at": datetime.now(timezone.utc).isoformat(), "command": [sys.executable, *sys.argv],
        "driver_sha256": sha256(driver), "predecessor_driver_sha256": PREDECESSOR_SHA256,
        "method": "Independent standard-library GLB/BIN decode, exact rational clock/group reconstruction and conditional final-flush scalar ledger",
        "imports_ontokin": False, "product_runtime_executed": False, "release_acceptance": False,
        "successful_export_claimed": False, "measured_full_cost_claimed": False, "measured_savings_claimed": False,
        "captured_source_minima_independently_certified": False,
        "operation_neutrality_certified_by_this_census": False,
        "limitations": ["The failed request returned no successful ExportResult; retained bytes remain unvalidated.",
            "Neutral capture comparison is separate execution evidence, not supplied by this byte census.",
            "Observed source minima, magnitude receipts and discarded-threshold domains are not independent source proofs.",
            "Reported-field algebra and observed-prefix reconciliation do not execute the unvisited tail or final source admission.",
            "No original recording pass, elapsed neutrality, performance improvement or release gate is established here."],
        "errors": []}
    try:
        result["census"] = analyze(args.capture_dir.resolve(), args.repo.resolve(), inputs)
        failed = [name for name, passed in result["census"]["census_required_checks"].items() if not passed]
        if failed:
            result["errors"].append({"type": "CensusReconciliationFailure", "failed_checks": failed})
    except Exception as error:
        result["errors"].append({"type": type(error).__name__, "message": str(error), "traceback": traceback.format_exc()})
    result["inputs"] = inputs.receipts()
    result["inputs_unchanged"] = all(item["unchanged"] for item in result["inputs"])
    require(args.output.resolve() not in inputs.data, "Output must not replace any evidence or source input")
    result["checks_executed"] = CHECKS
    result["status"] = "passed" if not result["errors"] and result["inputs_unchanged"] else "failed"
    result["finished_at"] = datetime.now(timezone.utc).isoformat()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    census = result.get("census", {})
    print(json.dumps({"status": result["status"], "output": str(args.output),
        "clock_count": census.get("clock_count"), "certificate_count": census.get("certificate_count"),
        "group_count": census.get("group_count"), "errors": result["errors"]}, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
