"""Independent supplied-byte checks for the bounded recorded reach contract.

Expected source motion is supplied by the independent reach reference, never
by the production solver, pose sampler, key planner or certificate generator.
This module uses rounding-cell membership rather than the writer's quotient
algorithm to verify exact rational-to-binary32 clock conversion.
"""
from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from fractions import Fraction
import hashlib
import math
from pathlib import Path
import re
import struct


TARGET = "ontokin.glb/0.6"
ARC_LIMIT = Fraction(0.7853981633974483)
MAX_KEYS = 10000
MAX_CERTIFICATES = 100000
MAX_OPERAND_BITS = 32768
MAX_INTEGER_DIGITS = 9865
CLOCK_CONVERSION = "binary32_rne_ties_to_even_from_exact_rational"
SOURCE_METHOD = "ontokin.source-pose-projective-dyadic/0.1"
DESTINATION_METHOD = ("Exact rational time and translation; integer RNE quaternion normalization; "
    "bounded normalized-chord approximation to short SLERP; separately bounded Three CPU matrix and vertex arithmetic.")


def _error(code, message, *, model=None, details=None, kind="numeric"):
    from .scene import export_error
    export_error(code, message, model, kind=kind, details=details)


def _tick(work, kind="independent_recording_check"):
    if work is not None:
        work.charge(kind)


@dataclass(frozen=True)
class _Cell:
    lo: Fraction
    hi: Fraction


class _Bounds:
    """Independent, allocation-guarded rational certificate arithmetic.

    The supplied-byte checker deliberately does not call the writer's numeric
    helpers. Native integer operations are bounded before allocation and
    cancellation is polled on both sides of integer square root and reduction.
    """
    def __init__(self, work=None):
        self.work = work

    def tick(self, kind="independent_bound_arithmetic"):
        _tick(self.work, kind)

    def reuse(self, key, calculate):
        """Cache only independently derived immutable arithmetic results."""
        if self.work is None or not hasattr(self.work, "lookup") or not hasattr(self.work, "remember"):
            return calculate()
        key = ("reach_independent_bounds_v1", *key)
        result = self.work.lookup(key)
        if result is None:
            result = calculate()
            self.work.remember(key, result)
        return result

    def bits(self, *sizes):
        if self.work is not None:
            self.work.guard_bits(max(sizes, default=0))
        if max(sizes, default=0) > MAX_OPERAND_BITS:
            _error("OKE-E-NUMERIC-BUDGET", "Independent certificate arithmetic exceeds its finite operand limit.", kind="resource")

    def value(self, value):
        self.tick("independent_bound_decode")
        if type(value) is int:
            self.bits(value.bit_length())
        elif type(value) is float:
            if not math.isfinite(value):
                _error("OKE-E-CERTIFICATE", "An independent arithmetic operand must be finite.")
        elif not isinstance(value, Fraction):
            _error("OKE-E-CERTIFICATE", "An independent arithmetic operand must be rational.")
        value = Fraction(value)
        self.bits(value.numerator.bit_length(), value.denominator.bit_length())
        return value

    def op(self, a, b, operation):
        # Internal callers pass already bounded fractions; external values are
        # decoded once. Each actually executed scalar operation still charges.
        if not isinstance(a, Fraction):
            a = self.value(a)
        if not isinstance(b, Fraction):
            b = self.value(b)
        self.tick("independent_exact_" + operation)
        an, ad = a.numerator.bit_length(), a.denominator.bit_length()
        bn, bd = b.numerator.bit_length(), b.denominator.bit_length()
        self.bits(an, ad, bn, bd)
        if operation in ("add", "sub"):
            self.bits(max(an + bd, bn + ad) + 1, ad + bd)
            result = a + b if operation == "add" else a - b
        elif operation == "mul":
            self.bits(an + bn, ad + bd)
            result = a * b
        elif operation == "div":
            if not b:
                _error("OKE-E-CERTIFICATE", "An independent certificate denominator is zero.")
            self.bits(an + bd, ad + bn)
            result = a / b
        else:
            raise ValueError("Unknown independent arithmetic operation")
        self.bits(result.numerator.bit_length(), result.denominator.bit_length())
        return result

    def add(self, a, b): return self.op(a, b, "add")
    def sub(self, a, b): return self.op(a, b, "sub")
    def mul(self, a, b): return self.op(a, b, "mul")
    def div(self, a, b): return self.op(a, b, "div")

    def compare(self, a, b):
        a, b = self.value(a), self.value(b)
        self.tick("independent_exact_compare")
        self.bits(a.numerator.bit_length() + b.denominator.bit_length(),
                  b.numerator.bit_length() + a.denominator.bit_length())
        return (a > b) - (a < b)

    def total(self, values):
        result = Fraction(0)
        for value in values:
            result = self.add(result, value)
        return result

    def square(self, value):
        return self.mul(value, value)

    def root(self, value, *, precision=96):
        value = self.value(value)
        if value < 0 or not 1 <= precision <= 2048:
            _error("OKE-E-CERTIFICATE", "An independent square-root operand or precision is invalid.")
        return self.reuse(("root", value, precision), lambda: self._root(value, precision))

    def _root(self, value, precision):
        self.bits(value.numerator.bit_length() + 2 * precision, 2 * precision + 1)
        self.tick("independent_sqrt_scale")
        numerator = value.numerator << (2 * precision)
        self.tick("independent_sqrt_divide")
        integer = numerator // value.denominator
        self.tick("independent_sqrt_enter")
        root = math.isqrt(integer)
        self.tick("independent_sqrt_return")
        self.bits(2 * root.bit_length() + value.denominator.bit_length(), root.bit_length() + 1)
        self.tick("independent_sqrt_exactness")
        upper = root + int(root * root * value.denominator != numerator)
        scale = 1 << precision
        return _Cell(Fraction(root, scale), Fraction(upper, scale))

    def norm(self, values):
        return self.root(self.total(self.square(value) for value in values)).hi

    def cell(self, value):
        if hasattr(value, "lo") and hasattr(value, "hi"):
            result = _Cell(self.value(value.lo), self.value(value.hi))
            if result.lo > result.hi:
                _error("OKE-E-INDEPENDENT-VALIDATION", "An independent reference returned a reversed enclosure.")
            return result
        value = self.value(value)
        return _Cell(value, value)

    def difference(self, first, last):
        if len(first) != len(last) or len(first) not in (3, 4):
            _error("OKE-E-CERTIFICATE", "An independent vector comparison has incompatible dimensions.")
        first, last = tuple(self.cell(value) for value in first), tuple(self.cell(value) for value in last)
        def calculate():
            result = [max(abs(self.sub(a.lo, b.hi)), abs(self.sub(a.hi, b.lo)))
                      for a, b in zip(first, last)]
            return self.norm(result)
        return self.reuse(("difference", first, last), calculate)

    def normalize(self, values):
        if hasattr(values, "__len__") and len(values) != 4:
            _error("OKE-E-QUATERNION", "A supplied quaternion must have four components.")
        components = []
        for index, value in enumerate(values):
            if index >= 4:
                _error("OKE-E-QUATERNION", "A supplied quaternion must have four components.")
            components.append(self.value(value))
        values = tuple(components)
        if len(values) != 4:
            _error("OKE-E-QUATERNION", "A supplied quaternion must have four components.")
        return self.reuse(("normalize", values), lambda: self._normalize(values))

    def _normalize(self, values):
        squared = self.total(self.square(value) for value in values)
        length = self.root(squared)
        if length.lo <= 0:
            _error("OKE-E-QUATERNION", "A supplied quaternion cannot be normalized within the finite proof range.")
        result = []
        for value in values:
            first, last = self.div(value, length.lo), self.div(value, length.hi)
            result.append(_Cell(min(first, last), max(first, last)))
        return tuple(result)


def _integer(text, *, work=None):
    if (not isinstance(text, str) or len(text) > MAX_INTEGER_DIGITS
            or re.fullmatch(r"0|[1-9][0-9]*", text, flags=re.ASCII) is None):
        _error("OKE-E-CLOCK", "Exact recording clocks require bounded canonical decimal integers.")
    # Avoid depending on the interpreter's configurable decimal-string limit.
    value, arithmetic = 0, _Bounds(work)
    for index in range(0, len(text), 256):
        _tick(work, "independent_clock_integer")
        part = text[index:index + 256]
        factor = 10 ** len(part)  # The fixed chunk has at most 851 bits.
        arithmetic.bits(value.bit_length() + factor.bit_length() + 1)
        value = value * factor + int(part)
        arithmetic.bits(value.bit_length())
    return value


def rational_clock(record, *, work=None):
    """Read a reduced, nonnegative exact clock without float conversion."""
    if not isinstance(record, dict) or set(record) != {"numerator", "denominator"}:
        _error("OKE-E-CLOCK", "A recording clock must retain its exact rational identity.")
    numerator = _integer(record["numerator"], work=work)
    denominator = _integer(record["denominator"], work=work)
    _tick(work, "independent_clock_reduction")
    gcd = math.gcd(numerator, denominator)
    _tick(work, "independent_clock_reduction_return")
    if denominator <= 0 or gcd != 1:
        _error("OKE-E-CLOCK", "A recording clock must be reduced with a positive denominator.")
    return Fraction(numerator, denominator)


def clock_cell_contains(value, bits, *, work=None):
    """Check RNE by exact adjacent-cell midpoints, independently of the writer."""
    _tick(work, "independent_clock_cell")
    arithmetic = _Bounds(work)
    value = arithmetic.value(value)
    if type(bits) is not int or not 0 <= bits <= 0x7f7fffff or value < 0:
        return False
    def decoded(integer):
        return Fraction(struct.unpack("<f", struct.pack("<I", integer))[0])
    center = decoded(bits)
    lower = Fraction(0) if bits == 0 else arithmetic.div(arithmetic.add(decoded(bits - 1), center), 2)
    higher = Fraction(1 << 128) if bits == 0x7f7fffff else decoded(bits + 1)
    upper = arithmetic.div(arithmetic.add(center, higher), 2)
    even = not bits & 1
    left, right = arithmetic.compare(value, lower), arithmetic.compare(value, upper)
    return ((left > 0 or even and left == 0) and (right < 0 or even and right == 0))


def _quantity(record, name, *, work=None):
    value = record.get(name)
    if type(value) not in (int, float) or (type(value) is float and not math.isfinite(value)) or value < 0:
        _error("OKE-E-CERTIFICATE", "A certificate quantity must be a finite nonnegative number.", details={"quantity": name})
    return _Bounds(work).value(value)


def _requires_upper(record, name, minimum, *, model=None, work=None):
    actual = _quantity(record, name, work=work)
    if _Bounds(work).compare(actual, minimum) < 0:
        _error("OKE-E-CERTIFICATE", "A reported certificate quantity understates an independently derived bound.",
               model=model, details={"quantity": name})
    return actual


def check_complete_inequalities(record, *, position_tolerance, rotation_tolerance, work=None, model=None):
    """Verify every reported sum and both mandatory quarter-allocation plans."""
    _tick(work, "independent_certificate_algebra")
    ha = rational_clock(record["h_authored_seconds"], work=work)
    hs = rational_clock(record["h_stored_seconds"], work=work)
    if ha <= 0 or hs <= 0:
        _error("OKE-E-CERTIFICATE", "Every interval certificate requires positive authored and stored widths.", model=model)
    arithmetic, quantities = _Bounds(work), {}
    def q(name):
        if name not in quantities:
            quantities[name] = _quantity(record, name, work=work)
        return quantities[name]
    add, mul, div, square = arithmetic.add, arithmetic.mul, arithmetic.div, arithmetic.square
    def require(name, minimum):
        actual = q(name)
        if arithmetic.compare(actual, minimum) < 0:
            _error("OKE-E-CERTIFICATE", "A reported bound understates the required exact sum.",
                   model=model, details={"quantity": name})
        return actual
    radius, vertex = q("landmark_radius_m"), q("local_vertex_error_bound_m")
    angular, acceleration = q("angular_speed_bound_rad_per_s"), q("carrier_acceleration_bound_m_per_s2")
    envelope_angular = q("enclosing_angular_speed_bound_rad_per_s")
    envelope_acceleration = q("enclosing_carrier_acceleration_bound_m_per_s2")
    speed, shift = q("enclosing_carrier_speed_bound_m_per_s"), q("max_endpoint_time_shift_s")
    position_tolerance, rotation_tolerance = arithmetic.value(position_tolerance), arithmetic.value(rotation_tolerance)
    position_quarter, rotation_quarter = div(position_tolerance, 4), div(rotation_tolerance, 4)
    for width, a, w in ((ha, acceleration, angular), (hs, envelope_acceleration, envelope_angular)):
        angle, width_squared = mul(w, width), square(width)
        rotation, chord = div(square(angle), 4), div(mul(a, width_squared), 8)
        if (arithmetic.compare(angle, ARC_LIMIT) > 0 or arithmetic.compare(rotation, rotation_quarter) > 0
                or arithmetic.compare(add(chord, mul(radius, rotation)), position_quarter) > 0):
            _error("OKE-E-CERTIFICATE", "The supplied key interval violates the mandatory quarter-allocation plan.", model=model)
    arc = q("stored_quaternion_arc_upper_rad")
    if arc > ARC_LIMIT:
        _error("OKE-E-CERTIFICATE", "The supplied stored quaternion arc exceeds the proved local range.", model=model)
    angular_width_squared, width_squared = square(mul(angular, ha)), square(ha)
    difference = require("unit_quaternion_difference_bound", arithmetic.total((
        q("max_endpoint_unit_quaternion_error"), div(angular_width_squared, 32), div(square(arc), 8))))
    if difference > Fraction(1, 2):
        _error("OKE-E-CERTIFICATE", "The supplied quaternion comparison exceeds its proved local range.", model=model)
    require("ideal_rotation_bound_rad", div(angular_width_squared, 4))
    chord = div(mul(acceleration, width_squared), 8)
    require("ideal_position_bound_m", chord)
    rotation = require("total_rotation_bound_rad", arithmetic.total((mul(4, difference),
        q("source_numeric_rotation_bound_rad"), q("destination_numeric_rotation_bound_rad"),
        mul(envelope_angular, shift))))
    carrier = require("carrier_position_bound_m", arithmetic.total((q("max_endpoint_position_error_m"),
        chord, q("source_numeric_position_bound_m"), q("destination_numeric_position_bound_m"), mul(speed, shift))))
    total = require("total_position_bound_m", arithmetic.total((carrier, mul(radius, rotation), vertex)))
    if carrier > position_tolerance or total > position_tolerance or rotation > rotation_tolerance:
        _error("OKE-E-NUMERIC-BOUND", "The complete independently checked bound exceeds the requested tolerance.", model=model)
    return {"position_bound_m": total, "rotation_bound_rad": rotation}


def verify_retained_clocks(decoded, quantization, authored_records, boundaries, end, *, time_tolerance, work):
    """Bind every clock label to the actual common input accessor and its cell."""
    animation = decoded.document["animations"][0]
    retained = quantization["retained_keys"]
    if not isinstance(retained, list) or not 1 <= len(retained) <= MAX_KEYS or len(retained) != len(authored_records):
        _error("OKE-E-CLOCK", "Retained exact clocks must cover the complete bounded common time axis.")
    arithmetic = _Bounds(work)
    times = decoded.clock(animation["samplers"][0]["input"])
    if len(times) != len(retained):
        _error("OKE-E-CLOCK", "Retained clock records must match the actual accessor length.")
    for sampler in animation["samplers"]:
        _tick(work, "independent_common_clock")
        if decoded.clock(sampler["input"]) != times:
            _error("OKE-E-CLOCK", "Every animation channel must use the same actual stored clocks.")
    authored = []
    semantic = set(boundaries)
    maximum_shift = Fraction(0)
    for index, (record, source_record, actual) in enumerate(zip(retained, authored_records, times)):
        _tick(work, "independent_retained_clock")
        if not isinstance(record, dict) or set(record) != {"authored_seconds", "stored_seconds", "stored_binary32_bits", "semantic_boundary"}:
            _error("OKE-E-CLOCK", "A retained key must contain exactly its required identity fields.")
        source = rational_clock(source_record, work=work)
        if record["authored_seconds"] != source_record:
            _error("OKE-E-CLOCK", "Animation and quantization metadata disagree on the exact authored clock.")
        bits = struct.unpack("<I", struct.pack("<f", actual))[0]
        if not clock_cell_contains(source, bits, work=work):
            _error("OKE-E-CLOCK-ROUNDING", "The supplied accessor is not direct binary32 ties-to-even rounding of its exact rational clock.",
                   details={"key_index": index, "actual_binary32_bits": f"{bits:08x}"})
        if (type(record["stored_seconds"]) not in (int, float)
                or record["stored_seconds"] != actual or record["stored_binary32_bits"] != f"{bits:08x}"
                or type(record["semantic_boundary"]) is not bool
                or record["semantic_boundary"] != (source in semantic)):
            _error("OKE-E-CLOCK", "Retained key labels disagree with actual bytes or independently derived semantic boundaries.")
        maximum_shift = max(maximum_shift, abs(arithmetic.sub(source, actual)))
        authored.append(source)
    if (authored[0] != 0 or authored[-1] != end
            or any(arithmetic.compare(a, b) >= 0 for a, b in zip(authored, authored[1:]))
            or not semantic.issubset(authored) or arithmetic.compare(maximum_shift, time_tolerance) > 0):
        _error("OKE-E-CLOCK", "The common clock omits required source boundaries or exceeds the requested time tolerance.")
    return tuple(authored), tuple(times), maximum_shift


def _identified_digest(path, *, work):
    _tick(work, "independent_basis_open")
    digest, size = hashlib.sha256(), 0
    with path.open("rb") as stream:
        while True:
            _tick(work, "independent_basis_read")
            part = stream.read(16384)
            _tick(work, "independent_basis_read_return")
            if not part:
                break
            size += len(part)
            if size > 262144:
                _error("OKE-E-NUMERIC-BUDGET", "A numerical basis input exceeds the identified bounded file size.", kind="resource")
            digest.update(part)
    return digest.hexdigest()


def verify_numeric_bases(quantization, *, work):
    """Resolve the two numerical claims to the actual bounded implementation."""
    root = Path(__file__).resolve().parents[1]
    names = ("ontokin/reach_numeric.py", "ontokin/reach_kinematics.py", "ontokin/reach_pose.py",
             "ontokin/reach_phase.py", "ontokin/reach_runtime.py")
    entries = [(name, _identified_digest(root / name, work=work)) for name in names]
    _tick(work, "independent_basis_aggregate")
    implementation = hashlib.sha256("".join(name + "\0" + digest + "\n" for name, digest in entries).encode("ascii")).hexdigest()
    derivation_names = ("docs/engineering/reach-numeric-kernel.md", "docs/engineering/reach-source-kernel.md")
    derivations = [(name, _identified_digest(root / name, work=work)) for name in derivation_names]
    _tick(work, "independent_basis_aggregate")
    derivation = hashlib.sha256("".join(name + "\0" + digest + "\n" for name, digest in derivations).encode("ascii")).hexdigest()
    source = {"name": "OntoKin controlled source poses", "version": "0.1",
        "implementation_sha256": "sha256:" + implementation, "method": SOURCE_METHOD,
        "derivation_sha256": "sha256:" + derivation}
    destination = {"name": "ontokin-controlled-three-recording", "version": "0.1.0",
        "implementation_sha256": "sha256:" + _identified_digest(root / "tools/reach_destination.mjs", work=work),
        "derivation_sha256": "sha256:" + _identified_digest(root / "docs/engineering/reach-destination-numerics.md", work=work),
        "method": DESTINATION_METHOD}
    if quantization.get("source_numeric_bound_basis") != source:
        _error("OKE-E-SOURCE-NUMERIC-BASIS", "The source numerical bound does not identify the complete current controlled algorithm and derivation.")
    if quantization.get("destination_numeric_bound_basis") != destination:
        _error("OKE-E-DESTINATION-NUMERIC-BASIS", "The destination numerical bound does not identify the current controlled player and derivation.")


def _geometry_bounds(decoded, model, options, *, work):
    """Reconstruct source occurrence vertices independently of baked motion.

    The inherited, identified geometry constructors remain the native geometry
    contract. No reach writer, pose sampler, timeline or certificate routine is
    called. Every repeated occurrence consumes the aggregate vertex allowance.
    """
    from .geometry import assembly_marker, box_mesh, joint_marker, sphere_mesh
    from .scene import MAX_MESH_VERTICES, SurfaceMesh, build_surface_mesh, float32
    arithmetic = _Bounds(work)
    result, meshes, remaining = {}, {}, MAX_MESH_VERTICES
    for index, node in enumerate(decoded.document["nodes"]):
        _tick(work, "independent_source_geometry")
        metadata = node["extras"]["ontokin"]
        owner = None
        if metadata.get("kind") == "object":
            owner = metadata.get("path")
            if owner not in model.objects or node.get("name") != owner:
                _error("OKE-E-PROVENANCE", "Every delivered carrier must identify an actual source occurrence.")
            obj = model.objects[owner]
            identity = {"path": owner, "element_id": list(obj.element_id)}
            frame = owner + ".frame"
            kind = obj.geometry["kind"]
            if kind == "empty":
                mesh = None
            elif kind in ("loft", "placed"):
                mesh = build_surface_mesh(obj.geometry, max_vertices=remaining, check=work.tick)
            elif kind == "box":
                mesh = box_mesh(obj.geometry["size"])
            elif kind == "sphere":
                mesh = sphere_mesh(obj.geometry["radius"])
            else:
                _error("OKE-E-GEOMETRY", "The source geometry is outside the identified recorded contract.", kind="unsupported")
        elif metadata.get("kind") == "visual_helper" and options.helpers:
            if metadata.get("helper_kind") == "assembly_origin":
                path = metadata.get("object_path")
                if path not in model.objects or model.objects[path].geometry["kind"] != "empty":
                    _error("OKE-E-GEOMETRY", "An origin helper must belong to a source assembly.")
                identity = {"path": "[visual helper] " + path + " origin", "element_id": list(model.objects[path].element_id)}
                frame, mesh, color = path + ".frame", assembly_marker(), [.1, .7, .8, 1.]
            elif metadata.get("helper_kind") == "joint_parent_site":
                path = metadata.get("joint_path")
                if path not in model.joints:
                    _error("OKE-E-GEOMETRY", "A joint helper must belong to a source connection.")
                identity = {"path": "[visual helper] " + path + " parent site", "element_id": list(model.joints[path].element_id)}
                frame, mesh, color = model.joints[path].parent + ".frame", joint_marker(model.joints[path].axis), [.9, .65, .08, 1.]
            else:
                _error("OKE-E-GEOMETRY", "The supplied visual helper has no source role.")
            if (node.get("name") != identity["path"] or metadata.get("frame_path") != frame
                    or metadata.get("related_element_id") != identity["element_id"]
                    or metadata.get("physical_participation") != "none"):
                _error("OKE-E-PROVENANCE", "Visual helper identity, frame and participation must match source.")
        else:
            _error("OKE-E-GEOMETRY", "Every carrier must preserve a requested source or helper occurrence.")
        source_positions = () if mesh is None else mesh.positions
        remaining -= len(source_positions)
        if remaining < 0:
            _error("OKE-E-MESH-BUDGET", "Independent repeated source geometry exceeds the aggregate vertex cap.", kind="resource")
        if mesh is None:
            if "mesh" in node:
                _error("OKE-E-GEOMETRY", "An empty source object acquired an undeclared mesh.")
            stored_positions = ()
        else:
            meshes[index] = mesh
            primitives = decoded.document["meshes"][node["mesh"]]["primitives"]
            primitive = primitives[0]
            stored_positions = decoded.accessor(primitive["attributes"]["POSITION"])
            if len(stored_positions) != len(source_positions):
                _error("OKE-E-GEOMETRY", "Stored vertex coverage does not match the complete source occurrence.")
            if not isinstance(mesh, SurfaceMesh):
                if len(primitives) != 1:
                    _error("OKE-E-GEOMETRY", "A native primitive or helper has unexpected material partitions.")
                normals = decoded.accessor(primitive["attributes"]["NORMAL"])
                indices = tuple(row[0] for row in decoded.accessor(primitive["indices"]))
                if len(normals) != len(mesh.normals) or indices != mesh.indices:
                    _error("OKE-E-GEOMETRY", "Stored primitive topology differs from its source construction.")
                for normal, expected in zip(normals, mesh.normals):
                    if normal != tuple(float32(value) for value in expected):
                        _error("OKE-E-GEOMETRY", "Stored primitive normals differ from source.")
                if owner is None:
                    pbr = decoded.document["materials"][primitive["material"]].get("pbrMetallicRoughness", {})
                    if pbr != {"baseColorFactor": color, "metallicFactor": 0., "roughnessFactor": .7}:
                        _error("OKE-E-GEOMETRY", "Visual helper material must preserve its explicit role.")
        radius_squared, error_squared = Fraction(0), Fraction(0)
        for point, stored in zip(source_positions, stored_positions):
            _tick(work, "independent_geometry_point")
            if tuple(float32(value) for value in point) != stored:
                _error("OKE-E-GEOMETRY", "Every actual vertex must match the source's single binary32 conversion.")
            def moments():
                source = tuple(arithmetic.value(value) for value in point)
                return (arithmetic.total(arithmetic.square(value) for value in source),
                        arithmetic.total(arithmetic.square(arithmetic.sub(value, actual))
                                         for value, actual in zip(source, stored)))
            point_radius, point_error = arithmetic.reuse(
                ("geometry_point", tuple(point), tuple(stored)), moments)
            radius_squared = max(radius_squared, point_radius)
            error_squared = max(error_squared, point_error)
        if owner is not None:
            for site in model.sites.values():
                if site.owner == owner:
                    radius_squared = max(radius_squared, arithmetic.total(arithmetic.square(arithmetic.value(value))
                                                                          for value in site.pose.position))
        result[index] = {"identity": identity, "frame": frame,
                         "radius": arithmetic.root(radius_squared).hi,
                         "vertex_error": arithmetic.root(error_squared).hi}
    return result, meshes


_QUANTIZATION_KEYS = {"schema_version", "rotation_interpolation", "clock_conversion",
    "position_tolerance_m", "rotation_tolerance_rad", "time_tolerance_s", "source_numeric_bound_basis",
    "destination_numeric_bound_basis", "retained_keys", "interval_certificates",
    "all_values_independently_recomputed", "unknown_error_bound_policy", "certificate_scope"}
_CERTIFICATE_KEYS = {"left_key_index", "right_key_index", "carrier", "source_phase_indices",
    "h_authored_seconds", "h_stored_seconds", "landmark_radius_m", "local_vertex_error_bound_m",
    "angular_speed_bound_rad_per_s", "carrier_acceleration_bound_m_per_s2",
    "enclosing_carrier_speed_bound_m_per_s", "enclosing_carrier_acceleration_bound_m_per_s2",
    "enclosing_angular_speed_bound_rad_per_s", "max_endpoint_time_shift_s", "max_endpoint_position_error_m",
    "max_endpoint_unit_quaternion_error", "stored_quaternion_arc_upper_rad",
    "source_numeric_position_bound_m", "source_numeric_rotation_bound_rad",
    "destination_numeric_position_bound_m", "destination_numeric_rotation_bound_rad",
    "unit_quaternion_difference_bound", "ideal_rotation_bound_rad", "ideal_position_bound_m",
    "carrier_position_bound_m", "total_position_bound_m", "total_rotation_bound_rad"}


def _verify_metadata(decoded, model, options, program, boundary_records, *, work):
    from .scene import force_profile_metadata, relationship_metadata
    from .values import bounded_data
    metadata = decoded.document["extras"]["ontokin"]
    expected = {"target_contract": TARGET, "schema_version": "0.6", "module": model.module_name,
        "scene": model.scene_name, "profile": model.profile, "gravity_m_per_s2": list(model.gravity),
        "coordinates": {"handedness": "right", "up": "+Y", "length_unit": "m", "time_unit": "s"},
        "transform_policy": "all_nodes_are_roots_with_baked_world_poses", "program": program,
        "force_profile": force_profile_metadata(),
        "surface_profile": {"name": "surface-0.1", "local_loft_axis": "+Z",
            "local_placement": "baked_once_into_vertices_and_normals_in_carrier_frame",
            "regional_materials": "explicit_linear_rgba_metallic_roughness",
            "physical_participation": "visual_meshes_add_no_matter_or_motion_authority",
            "quantization_tolerance_m": min(1e-5, options.position_tolerance_m),
            "limitations": ["flat_shading", "polygonal_elliptical_sections", "no_textures_or_skin_deformation",
                            "no_automatic_collision_or_mass", "recorded_rigid_animation_only"]},
        "motion_authority": "OntoKin semantic evaluator; playback contains no live solver",
        "reach_profile": {"schema_version": "ontokin.reach-recording/0.1", "source_profile": "planar-reach-0.1",
            "motion_model": "two_prescribed_planar_hinges", "rotation_interpolation": "shortest_arc_slerp",
            "goal_residual_max_m": 1e-9, "bound_chain_tuple_max": 32,
            "named_reach_action_max": 128, "live_solver_embedded": False}}
    for key, value in expected.items():
        _tick(work, "independent_metadata_identity")
        if metadata.get(key) != value:
            _error("OKE-E-PROVENANCE", "Scene metadata does not match the immutable source or recorded contract.",
                   details={"field": key})
    source = metadata.get("source", {})
    if (source.get("entry_source_id") != "entry"
            or source.get("entry_revision") != program["sources"]["entry"]["source_revision"]
            or source.get("editable_source_of_truth") != "pinned .ok source bundle"):
        _error("OKE-E-PROVENANCE", "The artifact does not preserve its distinct entry-source identity.")
    for key, value in bounded_data(relationship_metadata(model), check=work.tick).items():
        if metadata.get(key) != value:
            _error("OKE-E-PROVENANCE", "Declared source relationships differ from the supplied metadata.", details={"field": key})
    quantization = metadata.get("reach_quantization")
    if type(quantization) is not dict or set(quantization) != _QUANTIZATION_KEYS:
        _error("OKE-E-CERTIFICATE", "Reach quantization must contain exactly the complete adopted fields.")
    fixed = {"schema_version": "ontokin.reach-quantization/0.1", "rotation_interpolation": "shortest_arc_slerp",
        "clock_conversion": CLOCK_CONVERSION, "position_tolerance_m": options.position_tolerance_m,
        "rotation_tolerance_rad": options.rotation_tolerance_rad, "time_tolerance_s": options.time_tolerance_s,
        "all_values_independently_recomputed": True, "unknown_error_bound_policy": "reject",
        "certificate_scope": "specified source and supplied bytes; separately identified destination numeric behavior"}
    if any(quantization.get(key) != value for key, value in fixed.items()):
        _error("OKE-E-CERTIFICATE", "The supplied certificate changes the requested tolerance or required numerical policy.")
    if type(quantization["all_values_independently_recomputed"]) is not bool:
        _error("OKE-E-CERTIFICATE", "The independent-recomputation assertion must be Boolean.")
    animation_metadata = decoded.document["animations"][0]["extras"]["ontokin"]
    if animation_metadata.get("target_contract") != TARGET:
        _error("OKE-E-PROVENANCE", "Animation metadata must preserve the requested delivery contract.")
    # Formatting a boundary is independent of the writer's time formatter.
    expected_times = [record["source_seconds"] for record in boundary_records]
    if animation_metadata.get("boundary_times_seconds") != expected_times:
        _error("OKE-E-BOUNDARY-HISTORY", "Animation metadata omits or changes an independently reconstructed boundary.")
    return quantization


def _assert_projection(actual, expected, *, arithmetic, allowances, path=()):
    """Compare complete histories; interval leaves retain their units/meaning."""
    from .reach_reference import Interval
    arithmetic.tick("independent_projection_entry")
    if isinstance(expected, Interval):
        if type(actual) not in (int, float):
            _error("OKE-E-BOUNDARY-HISTORY", "A numerical source history has a nonnumeric leaf.", details={"path": list(path)})
        labels = " ".join(str(value) for value in path)
        if "orientation" in labels or "angular" in labels or "omega" in labels:
            allowance = allowances["angular_velocity"] if "velocity" in labels or "omega" in labels else allowances["rotation"]
        elif "velocity" in labels or "speed" in labels:
            allowance = allowances["velocity"]
        elif any(label in labels for label in ("position", "residual", "world_target", "tip_pose")):
            allowance = allowances["position"]
        else:
            _error("OKE-E-INDEPENDENT-VALIDATION", "An independent numerical history leaf has no identified allowance.", details={"path": list(path)})
        value = arithmetic.value(actual)
        rounding = arithmetic.add(arithmetic.mul(max(abs(expected.lo), abs(expected.hi)), Fraction(1, 1 << 53)), Fraction(1, 1 << 1075))
        allowance = arithmetic.add(allowance, rounding)
        if (arithmetic.compare(value, arithmetic.sub(expected.lo, allowance)) < 0
                or arithmetic.compare(value, arithmetic.add(expected.hi, allowance)) > 0):
            _error("OKE-E-BOUNDARY-HISTORY", "A recorded numerical state lies outside the independent source enclosure.", details={"path": list(path)})
    elif isinstance(expected, dict):
        if type(actual) is not dict or set(actual) != set(expected):
            _error("OKE-E-BOUNDARY-HISTORY", "A recorded source history omits or adds fields.", details={"path": list(path)})
        for key, value in expected.items():
            _assert_projection(actual[key], value, arithmetic=arithmetic, allowances=allowances, path=(*path, key))
    elif isinstance(expected, (tuple, list)):
        if type(actual) is not list or len(actual) != len(expected):
            _error("OKE-E-BOUNDARY-HISTORY", "A recorded source history omits or reorders entries.", details={"path": list(path)})
        if path and path[-1] == "orientation_wxyz" and len(expected) == 4:
            # Quaternion sign is a representation choice, not physical state.
            exact = [arithmetic.cell(value) for value in expected]
            positive = arithmetic.difference(actual, exact)
            negative = arithmetic.difference(actual, [_Cell(-value.hi, -value.lo) for value in exact])
            if min(positive, negative) > allowances["rotation"]:
                _error("OKE-E-BOUNDARY-HISTORY", "A recorded orientation differs from the independent source state.", details={"path": list(path)})
        else:
            for index, (first, last) in enumerate(zip(actual, expected)):
                _assert_projection(first, last, arithmetic=arithmetic, allowances=allowances, path=(*path, index))
    else:
        if ((type(expected) is bool and type(actual) is not bool)
                or (type(expected) is int and type(actual) is not int)
                or (type(expected) is float and type(actual) not in (int, float))
                or actual != expected):
            _error("OKE-E-BOUNDARY-HISTORY", "A recorded source identity, control or invariant value differs from source.", details={"path": list(path)})


def _phase_tables(reference, geometry, *, work):
    result = {}
    for value in geometry.values():
        frame = value["frame"]
        _tick(work, "independent_phase_table")
        if frame not in result:
            phases = reference.phases(frame, Fraction(0), reference.end)
            if len(phases) != len(reference.boundaries) - 1 or any(
                    (phase.start, phase.end) != (left, right)
                    for phase, left, right in zip(phases, reference.boundaries, reference.boundaries[1:])):
                _error("OKE-E-PHASE-COVERAGE", "The independent reference cannot prove every source phase for this carrier.")
            result[frame] = phases
    return result


def _boundary_allowances(phase_tables, endpoint_phases, geometry, model, arithmetic):
    phases = (*tuple(phase for values in phase_tables.values() for phase in values),
              *endpoint_phases.values())
    maximum = lambda name: max((getattr(phase, name) for phase in phases), default=Fraction(0))
    rotation = maximum("source_numeric_rotation_error")
    radius = max((item["radius"] for item in geometry.values()), default=Fraction(0))
    for action in model.actions.values():
        if action.kind == "reach_planar":
            radius = max(radius, arithmetic.total(arithmetic.value(value) for value in action.reach.lengths_m))
    return {"position": arithmetic.mul(4, arithmetic.add(maximum("source_numeric_position_error"), arithmetic.mul(radius, rotation))),
            "rotation": arithmetic.mul(4, rotation),
            "velocity": arithmetic.mul(4, maximum("source_numeric_velocity_error")),
            "angular_velocity": arithmetic.mul(4, maximum("source_numeric_angular_velocity_error"))}


def _tracks(decoded, geometry, *, work):
    result = {index: {} for index in geometry}
    animation = decoded.document["animations"][0]
    for channel in animation["channels"]:
        _tick(work, "independent_carrier_track")
        sampler = animation["samplers"][channel["sampler"]]
        result[channel["target"]["node"]][channel["target"]["path"]] = decoded.accessor(sampler["output"])
    return result


def _key_comparisons(reference, geometry, tracks, time, index, arithmetic):
    result = {}
    for carrier, item in geometry.items():
        arithmetic.tick("independent_key_pose")
        ideal = reference.recording_pose_enclosure(item["frame"], time, side="after")
        position, quaternion = tracks[carrier]["translation"][index], tracks[carrier]["rotation"][index]
        def compare():
            normalized = arithmetic.normalize(quaternion)
            expected = (ideal.orientation[1], ideal.orientation[2], ideal.orientation[3], ideal.orientation[0])
            positive = arithmetic.difference(normalized, expected)
            negative = arithmetic.difference(normalized, [_Cell(-value.hi, -value.lo) for value in expected])
            return (("position_error", arithmetic.difference(position, ideal.position)),
                    ("quaternion_error", min(positive, negative)), ("normalized", normalized),
                    ("magnitude", arithmetic.total(abs(arithmetic.value(value)) for value in position)))
        result[carrier] = dict(arithmetic.reuse(("key_pose_comparison", tuple(position), tuple(quaternion),
                                                ideal.position, ideal.orientation), compare))
    return result


def _arc_bound(first, last, arithmetic):
    chord = arithmetic.difference(first, last)
    if chord > Fraction(1, 2):
        _error("OKE-E-QUATERNION-LIFT", "The actual stored endpoints exceed the proved short-arc domain.")
    return arithmetic.div(chord, arithmetic.sub(1, arithmetic.div(arithmetic.square(chord), 4)))


def _verify_certificates(decoded, reference, geometry, tables, endpoint_phases, authored, times, quantization, options, *, work):
    arithmetic = _Bounds(work)
    certificates = quantization["interval_certificates"]
    expected_count = (len(authored) - 1) * len(geometry)
    if type(certificates) is not list or len(certificates) != expected_count or expected_count > MAX_CERTIFICATES:
        _error("OKE-E-CERTIFICATE-COVERAGE", "There must be exactly one certificate per carrier and adjacent retained key pair.")
    identities = {value["identity"]["path"]: (index, value["identity"]) for index, value in geometry.items()}
    rows = {}
    for record in certificates:
        _tick(work, "independent_certificate_identity")
        if type(record) is not dict or set(record) != _CERTIFICATE_KEYS:
            _error("OKE-E-CERTIFICATE-COVERAGE", "Every certificate must contain exactly the adopted complete fields.")
        left, right, carrier = record["left_key_index"], record["right_key_index"], record["carrier"]
        if (type(left) is not int or type(right) is not int or not 0 <= left < len(authored) - 1
                or right != left + 1 or type(carrier) is not dict or carrier.get("path") not in identities):
            _error("OKE-E-CERTIFICATE-COVERAGE", "A certificate has an invalid carrier or nonadjacent key pair.")
        index, identity = identities[carrier["path"]]
        if carrier != identity or (left, index) in rows:
            _error("OKE-E-CERTIFICATE-COVERAGE", "A certificate duplicates or changes a source carrier identity.")
        rows[left, index] = record
    tracks = _tracks(decoded, geometry, work=work)
    previous = _key_comparisons(reference, geometry, tracks, authored[0], 0, arithmetic)
    max_position = max_rotation = Fraction(0)
    for key, (left, right) in enumerate(zip(authored, authored[1:])):
        following = _key_comparisons(reference, geometry, tracks, right, key + 1, arithmetic)
        stored_left, stored_right = arithmetic.value(times[key]), arithmetic.value(times[key + 1])
        width, stored_width = arithmetic.sub(right, left), arithmetic.sub(stored_right, stored_left)
        shift = max(abs(arithmetic.sub(left, stored_left)), abs(arithmetic.sub(right, stored_right)))
        low, high = max(Fraction(0), min(left, stored_left)), min(reference.end, max(right, stored_right))
        required = [index for index, (a, b) in enumerate(zip(reference.boundaries, reference.boundaries[1:]))
                    if max(a, low) < min(b, high)]
        source_index = bisect_right(reference.boundaries, left) - 1
        if not reference.boundaries[source_index] <= left < right <= reference.boundaries[source_index + 1]:
            _error("OKE-E-PHASE-COVERAGE", "An authored pair crosses an unretained source boundary.")
        endpoint_index = bisect_right(reference.boundaries, right) - 1
        numeric_selected = set(required)
        if endpoint_index < len(reference.boundaries) - 1:
            numeric_selected.add(endpoint_index)
        for carrier, item in geometry.items():
            record, phases = rows[key, carrier], tables[item["frame"]]
            selected = record["source_phase_indices"]
            if (type(selected) is not list or any(type(value) is not int or not 0 <= value < len(phases) for value in selected)
                    or len(selected) != len(set(selected)) or not set(required).issubset(selected)
                    or any(max(low, phases[value].start) > min(high, phases[value].end) for value in selected)):
                _error("OKE-E-PHASE-COVERAGE", "A certificate omits a positive-width source phase or names an unrelated phase.")
            if rational_clock(record["h_authored_seconds"], work=work) != width or rational_clock(record["h_stored_seconds"], work=work) != stored_width:
                _error("OKE-E-CLOCK", "Certificate widths do not match actual retained clocks.")
            phase = phases[source_index]
            source_position = max(phases[value].source_numeric_position_error for value in numeric_selected)
            source_rotation = max(phases[value].source_numeric_rotation_error for value in numeric_selected)
            if right == reference.end:
                final_phase = endpoint_phases[item["frame"]]
                source_position = max(source_position, final_phase.source_numeric_position_error)
                source_rotation = max(source_rotation, final_phase.source_numeric_rotation_error)
            first, last = previous[carrier], following[carrier]
            raw_first, raw_last = tracks[carrier]["rotation"][key], tracks[carrier]["rotation"][key + 1]
            dot = arithmetic.total(arithmetic.mul(a, b) for a, b in zip(raw_first, raw_last))
            if dot < 0:
                _error("OKE-E-QUATERNION-LIFT", "Actual stored endpoint signs do not form a coherent short-path lift.")
            arc = _arc_bound(first["normalized"], last["normalized"], arithmetic)
            minima = {"landmark_radius_m": item["radius"], "local_vertex_error_bound_m": item["vertex_error"],
                "angular_speed_bound_rad_per_s": phase.angular_speed,
                "carrier_acceleration_bound_m_per_s2": phase.acceleration,
                "enclosing_carrier_speed_bound_m_per_s": max(phases[value].speed for value in selected),
                "enclosing_carrier_acceleration_bound_m_per_s2": max(phases[value].acceleration for value in selected),
                "enclosing_angular_speed_bound_rad_per_s": max(phases[value].angular_speed for value in selected),
                "max_endpoint_time_shift_s": shift,
                "max_endpoint_position_error_m": max(first["position_error"], last["position_error"]),
                "max_endpoint_unit_quaternion_error": max(first["quaternion_error"], last["quaternion_error"]),
                "stored_quaternion_arc_upper_rad": arc,
                "source_numeric_position_bound_m": source_position, "source_numeric_rotation_bound_rad": source_rotation}
            checked = {name: _requires_upper(record, name, minimum, work=work) for name, minimum in minima.items()}
            magnitude = max(first["magnitude"], last["magnitude"])
            domain = arithmetic.total((magnitude, checked["landmark_radius_m"], checked["local_vertex_error_bound_m"]))
            if domain > 1 << 400:
                _error("OKE-E-DESTINATION-NUMERIC-BASIS", "The source and stored geometry exceed the identified destination's magnitude domain.")
            _requires_upper(record, "destination_numeric_position_bound_m", arithmetic.div(arithmetic.add(domain, 1), 1 << 38), work=work)
            _requires_upper(record, "destination_numeric_rotation_bound_rad",
                arithmetic.add(arithmetic.square(checked["stored_quaternion_arc_upper_rad"]), Fraction(1, 1 << 44)), work=work)
            totals = check_complete_inequalities(record, position_tolerance=options.position_tolerance_m,
                rotation_tolerance=options.rotation_tolerance_rad, work=work)
            max_position = max(max_position, totals["position_bound_m"])
            max_rotation = max(max_rotation, totals["rotation_bound_rad"])
        previous = following
    return {"max_position_bound_m": max_position, "max_rotation_bound_rad": max_rotation,
            "interval_certificates_checked": expected_count, "key_pose_comparisons": len(authored) * len(geometry)}


def validate_reach_export(data, model, *, options=None, check=None, work=None):
    """Verify the complete source/byte proof with the caller's existing work.

    Missing independent source behavior rejects delivery. Additional fixed,
    interior, native-player and browser observations belong to the release
    workflow and remain distinct from this continuous supplied-byte proof.
    """
    from .gltf import read_glb, _validate_geometry
    from .reach_reference import ReferenceError, build_reference
    from .scene import ExportOptions, MAX_BAKED_POSES, checked_contract, program_metadata
    if work is None:
        raise ValueError("Reach supplied-byte validation requires the existing request work context")
    checked_contract(model, TARGET)
    decoded = read_glb(data, check=work.tick, target_contract=TARGET)
    nodes = decoded.document["nodes"]
    metadata = decoded.document.get("extras", {}).get("ontokin", {})
    animation = decoded.document["animations"][0]
    authored_records = animation.get("extras", {}).get("ontokin", {}).get("exact_times_seconds")
    if type(authored_records) is not list or not 1 <= len(authored_records) <= MAX_KEYS:
        _error("OKE-E-CLOCK", "Every supplied recording requires a bounded exact authored time axis.")
    if len(authored_records) * len(nodes) > MAX_BAKED_POSES:
        _error("OKE-E-POSE-BUDGET", "Repeated supplied carrier poses exceed the recording cap.", kind="resource")
    supplied_end = rational_clock(authored_records[-1], work=work)
    options = options or ExportOptions(end=supplied_end, helpers=any(
        node.get("extras", {}).get("ontokin", {}).get("kind") == "visual_helper" for node in nodes))
    end = options.checked_end(model)
    if options.time_tolerance_s > 1e-6:
        _error("OKE-E-OPTIONS", "Reach time tolerance must be positive and at most 1e-6 seconds.", model=model, kind="options")
    quantization = metadata.get("reach_quantization")
    if type(quantization) is not dict or set(quantization) != _QUANTIZATION_KEYS:
        _error("OKE-E-CERTIFICATE", "The complete adopted quantization object is required.")
    certificates = quantization["interval_certificates"]
    expected_count = (len(authored_records) - 1) * len(nodes)
    if type(certificates) is not list or len(certificates) != expected_count or expected_count > MAX_CERTIFICATES:
        _error("OKE-E-CERTIFICATE-COVERAGE", "The certificate count must cover every carrier and adjacent key pair exactly once.")
    verify_numeric_bases(quantization, work=work)
    program = program_metadata(model, check=work.tick)
    try:
        reference = build_reference(model, end=end, work=work)
        boundary_records = reference.boundary_states()
        quantization = _verify_metadata(decoded, model, options, program, boundary_records, work=work)
        authored, times, shift = verify_retained_clocks(decoded, quantization, authored_records,
            reference.boundaries, end, time_tolerance=options.time_tolerance_s, work=work)
        geometry, meshes = _geometry_bounds(decoded, model, options, work=work)
        frames, geometry_error, surface_error = _validate_geometry(decoded, model, options, TARGET, program,
            check=work.tick, source_meshes=meshes)
        if any(frames[index] != value["frame"] for index, value in geometry.items()):
            _error("OKE-E-PROVENANCE", "The native geometry and independent source carrier frames disagree.")
        tables = _phase_tables(reference, geometry, work=work)
        endpoint_phases = {frame: reference.point_phase(frame, end, side="after") for frame in tables}
        allowances = _boundary_allowances(tables, endpoint_phases, geometry, model, _Bounds(work))
        _assert_projection(metadata.get("boundary_states"), boundary_records,
            arithmetic=_Bounds(work), allowances=allowances, path=("boundary_states",))
        proof = _verify_certificates(decoded, reference, geometry, tables, endpoint_phases,
                                     authored, times, quantization, options, work=work)
    except ReferenceError as error:
        _error("OKE-E-INDEPENDENT-VALIDATION", "The independent source reference could not establish the requested recording: " + str(error),
            model=model, kind="resource" if error.code == "resource" else "unsupported",
            details={"reference_code": error.code, **error.details})
    surface_tolerance = min(options.position_tolerance_m, 1e-5)
    expected_surface = {"local_vertex_tolerance_m": surface_tolerance,
        "max_vertex_quantization_error_m": surface_error, "normal_policy": "flat_shaded_triangle_corners",
        "material_policy": "one_primitive_per_used_source_region",
        "placement_policy": "baked_once_in_carrier_local_vertices_and_normals"}
    if metadata.get("surface_delivery") != expected_surface:
        _error("OKE-E-GEOMETRY", "Native surface conversion metadata must describe the independently checked actual buffers.")
    if geometry_error > options.position_tolerance_m or surface_error > surface_tolerance:
        _error("OKE-E-GEOMETRY-PRECISION", "Actual geometry conversion exceeds the requested native tolerance.")
    def outward(value):
        arithmetic = _Bounds(work)
        value = arithmetic.value(value)
        arithmetic.tick("independent_report_rounding")
        result = float(value)
        if not math.isfinite(result):
            _error("OKE-E-NUMERIC-BOUND", "An independently established report bound is not representable.")
        if arithmetic.compare(Fraction(result), value) < 0:
            result = math.nextafter(result, math.inf)
        return result
    return {"status": "passed", "structure": "passed_bounded_glb_reader",
        "method": "Independent exact-sign admission, interval source event/pose reference, exact clock cells and complete supplied-byte continuous inequalities.",
        "reach_continuous_bounds": "passed_independent_source_and_bytes",
        "reach_boundary_histories": "passed_complete_both_sides_and_incoming_releases",
        "position_metric": "conservative uniform Euclidean carrier and native-landmark bound in metres",
        "rotation_metric": "conservative uniform physical rotation-angle bound in radians",
        "probe_policy": "every actual stored key endpoint plus every complete source boundary; continuous per-interval proof",
        "sample_count": len(authored), "node_pose_comparisons": proof["key_pose_comparisons"],
        "interval_certificates_checked": proof["interval_certificates_checked"],
        "max_position_error_bound_m": outward(proof["max_position_bound_m"]),
        "max_rotation_error_bound_rad": outward(proof["max_rotation_bound_rad"]),
        "max_time_error_seconds": outward(shift), "max_geometry_dimension_error_m": geometry_error,
        "max_surface_vertex_error_m": surface_error, "surface_vertex_tolerance_m": surface_tolerance,
        "surface_geometry_materials_and_provenance": "passed_source_comparison", "failures": [],
        "scope": "Continuous proof for this source, actual bytes and identified controlled destination algorithm; actual native/browser execution and visual review remain separate release obligations."}
