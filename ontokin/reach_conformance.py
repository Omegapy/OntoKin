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
from types import MethodType

from .reach_reference import Interval as _ReferenceCell
from .reach_numeric import ReachExecutionWork as _CertificateWork


TARGET = "ontokin.glb/0.6"
ARC_LIMIT = Fraction(0.7853981633974483)
_ENDPOINT_TWO = Fraction(2)
_CERTIFICATE_FOUR = Fraction(4)
_CERTIFICATE_EIGHT = Fraction(8)
_CERTIFICATE_THIRTY_TWO = Fraction(32)
MAX_KEYS = 10000
MAX_CERTIFICATES = 100000
MAX_OPERAND_BITS = 32768
MAX_INTEGER_DIGITS = 9865
_LIFT_SIGN_COMPONENT_MIN = float.fromhex("0x1p-200")
_LIFT_SIGN_COMPONENT_MAX = float.fromhex("0x1p+128")
CLOCK_CONVERSION = "binary32_rne_ties_to_even_from_exact_rational"
SOURCE_METHOD = "ontokin.source-pose-projective-dyadic/0.2"
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
    def __init__(self, work=None, *, cache_intermediates=True):
        self.work = work
        self.cache_intermediates = cache_intermediates

    def tick(self, kind="independent_bound_arithmetic"):
        _tick(self.work, kind)

    def reuse(self, key, calculate):
        """Cache only independently derived immutable arithmetic results."""
        if not self.cache_intermediates and key[0] in {
                "root", "difference", "normalize", "key_pose_comparison"}:
            # Sequential certificate checking already retains the previous
            # endpoint and shares complete orientation/arc proofs across
            # carriers. Their nested one-shot scalars need no second cache
            # lookup, insertion, promotion or eviction. Calculate them afresh;
            # the arithmetic and all current operand/cancellation checks run.
            return calculate()
        if self.work is None or not hasattr(self.work, "lookup") or not hasattr(self.work, "remember"):
            return calculate()
        # A successful proof also establishes its intermediate operand domain.
        # A later narrower request limit must re-establish that domain, even
        # when the exact external values still fit and compare equal.
        admitted_limit = getattr(self.work, "max_operand_bits", MAX_OPERAND_BITS)
        key = ("reach_independent_bounds_v1", admitted_limit, *key)
        result = self.work.lookup(key)
        if result is None:
            if getattr(self.work, "max_operand_bits", MAX_OPERAND_BITS) != admitted_limit:
                # The charged lookup can narrow the live domain after callers
                # decoded these operands. A miss may then take an exact-zero
                # shortcut and never perform another scalar operation on them.
                # Re-admit every immutable numeric key member before that proof;
                # the old-domain key cannot certify a new-domain cache hit.
                self.tick("independent_cache_miss_domain")
                self._cache_operand_domain(key[2:])
            result = calculate()
            self.work.remember(key, result)
        return result

    def _cache_operand_domain(self, value):
        """Recheck the bounded numeric shapes used by this reader's own keys."""
        if type(value) is Fraction:
            self.bits(value.numerator.bit_length(), value.denominator.bit_length())
        elif type(value) is int:
            self.bits(value.bit_length())
        elif type(value) is float:
            if not math.isfinite(value):
                _error("OKE-E-CERTIFICATE", "An independent arithmetic operand must be finite.")
            exact = Fraction(value)
            self.bits(exact.numerator.bit_length(), exact.denominator.bit_length())
        elif type(value) in (_Cell, _ReferenceCell):
            self._cache_operand_domain(value.lo)
            self._cache_operand_domain(value.hi)
            self.bits(value.lo.numerator.bit_length() + value.hi.denominator.bit_length(),
                      value.hi.numerator.bit_length() + value.lo.denominator.bit_length())
        elif type(value) is tuple:
            for member in value:
                self._cache_operand_domain(member)

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
        if not isinstance(a, Fraction):
            a = self.value(a)
        if not isinstance(b, Fraction):
            b = self.value(b)
        self.bits(a.numerator.bit_length(), a.denominator.bit_length(),
                  b.numerator.bit_length(), b.denominator.bit_length())
        self.tick("independent_exact_compare")
        self.bits(a.numerator.bit_length() + b.denominator.bit_length(),
                  b.numerator.bit_length() + a.denominator.bit_length())
        return (a > b) - (a < b)

    def total(self, values):
        def direct():
            result = Fraction(0)
            for value in values:
                result = self.add(result, value)
            return result

        # A bounded tuple of native immutable scalars can omit actual additions
        # of zero. At most sixteen 256-bit fractions have <4101-bit prospective
        # fold operands, including every omitted original zero addition. Other
        # shapes and narrower domains retain the complete original fold.
        if (type(values) is not tuple or not 1 <= len(values) <= 16
                or type(_bound_domain(self)) is not int or _bound_domain(self) != MAX_OPERAND_BITS
                or not _small_proof_values(values)):
            return direct()
        self.tick("independent_total_domain")
        self._cache_operand_domain(values)
        if _bound_domain(self) != MAX_OPERAND_BITS:
            # This added callback must not allow an original first-add width
            # failure to disappear into a later broadening callback.
            first = values[0]
            self.bits(max(first.denominator.bit_length(), first.numerator.bit_length() + 1) + 1,
                      1 + first.denominator.bit_length())
            return direct()
        result = Fraction(0)
        for value in values:
            if not value:
                continue
            if not result:
                result = value
            else:
                result = self.add(result, value)
                if _bound_domain(self) != MAX_OPERAND_BITS:
                    self._cache_operand_domain(values)
                    return direct()
        self.bits(result.numerator.bit_length(), result.denominator.bit_length())
        return result

    def square(self, value):
        return self.mul(value, value)

    def root(self, value, *, precision=96):
        value = self.value(value)
        if value < 0 or not 1 <= precision <= 2048:
            _error("OKE-E-CERTIFICATE", "An independent square-root operand or precision is invalid.")
        if not value:
            self.tick("independent_zero_root")
            return _Cell(Fraction(0), Fraction(0))
        return self.reuse(("root", value, precision), lambda: self._root(value, precision))

    def _root(self, value, precision):
        self.tick("independent_sqrt_scale")
        self.bits(value.numerator.bit_length(), value.denominator.bit_length(),
                  value.numerator.bit_length() + 2 * precision, 2 * precision + 1)
        numerator = value.numerator << (2 * precision)
        self.tick("independent_sqrt_divide")
        self.bits(numerator.bit_length(), value.denominator.bit_length())
        integer = numerator // value.denominator
        self.tick("independent_sqrt_enter")
        self.bits(integer.bit_length())
        root = math.isqrt(integer)
        self.tick("independent_sqrt_return")
        self.bits(2 * root.bit_length() + value.denominator.bit_length(), root.bit_length() + 1)
        self.tick("independent_sqrt_exactness")
        self.bits(numerator.bit_length(), value.denominator.bit_length(),
                  2 * root.bit_length() + value.denominator.bit_length(), root.bit_length() + 1,
                  precision + 1)
        upper = root + int(root * root * value.denominator != numerator)
        scale = 1 << precision
        return _Cell(Fraction(root, scale), Fraction(upper, scale))

    def norm(self, values):
        if (type(values) in (tuple, list) and len(values) <= 4
                and all(type(value) is Fraction for value in values)):
            self.tick("independent_norm_domain")
            total = Fraction(0)
            for value in values:
                self.bits(value.numerator.bit_length(), value.denominator.bit_length())
                if value:
                    squared = self.square(value)
                    total = squared if not total else self.add(total, squared)
            if not total:
                # The guarded sparse fold already proves the exact zero norm;
                # no radical, projection or repeated zero decode is required.
                return Fraction(0)
            return self.root(total).hi
        return self.root(self.total(self.square(value) for value in values)).hi

    def cell(self, value):
        if hasattr(value, "lo") and hasattr(value, "hi"):
            low, high = value.lo, value.hi
            if type(low) is Fraction and type(high) is Fraction:
                # Independent reference intervals already contain immutable
                # exact rationals. Guard them directly before comparison;
                # no repeated Fraction construction/decoding is necessary.
                self.tick("independent_interval_domain")
                self.bits(low.numerator.bit_length(), low.denominator.bit_length(),
                          high.numerator.bit_length(), high.denominator.bit_length())
                self.bits(low.numerator.bit_length() + high.denominator.bit_length(),
                          high.numerator.bit_length() + low.denominator.bit_length())
                if low > high:
                    _error("OKE-E-INDEPENDENT-VALIDATION", "An independent reference returned a reversed enclosure.")
                return value if isinstance(value, _Cell) else _Cell(low, high)
            result = _Cell(self.value(low), self.value(high))
            self.bits(result.lo.numerator.bit_length() + result.hi.denominator.bit_length(),
                      result.hi.numerator.bit_length() + result.lo.denominator.bit_length())
            if result.lo > result.hi:
                _error("OKE-E-INDEPENDENT-VALIDATION", "An independent reference returned a reversed enclosure.")
            return result
        value = self.value(value)
        return _Cell(value, value)

    def cells(self, values):
        """Admit one bounded immutable interval vector before any reuse.

        Both local cells and the independent reader's cells are frozen pairs
        of exact rationals. Their complete 3/4-component domain can therefore
        be checked at one cancellation checkpoint, without repeatedly decoding
        each endpoint or retaining another cache. Each ordered component keeps
        the same operand, cross-product and reversed-interval checks as cell().
        Other supplied shapes and duck-typed cells keep its scalar path.
        """
        if (type(values) in (tuple, list) and len(values) in (3, 4)
                and all(type(value) in (_Cell, _ReferenceCell)
                        and type(value.lo) is Fraction and type(value.hi) is Fraction
                        for value in values)):
            endpoints = tuple((value.lo, value.hi) for value in values)
            self.tick("independent_interval_vector_domain")
            result = []
            for low, high in endpoints:
                self.bits(low.numerator.bit_length(), low.denominator.bit_length(),
                          high.numerator.bit_length(), high.denominator.bit_length())
                self.bits(low.numerator.bit_length() + high.denominator.bit_length(),
                          high.numerator.bit_length() + low.denominator.bit_length())
                if low > high:
                    _error("OKE-E-INDEPENDENT-VALIDATION", "An independent reference returned a reversed enclosure.")
                result.append(_Cell(low, high))
            return tuple(result)
        return tuple(self.cell(value) for value in values)

    def difference(self, first, last):
        if len(first) != len(last) or len(first) not in (3, 4):
            _error("OKE-E-CERTIFICATE", "An independent vector comparison has incompatible dimensions.")
        first, last = self.cells(first), self.cells(last)
        def calculate():
            result = []
            for a, b in zip(first, last):
                if a.lo == a.hi and b.lo == b.hi:
                    result.append(Fraction(0) if a.lo == b.lo else abs(self.sub(a.lo, b.lo)))
                else:
                    result.append(max(abs(self.sub(a.lo, b.hi)), abs(self.sub(a.hi, b.lo))))
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
        squared = Fraction(0)
        for value in values:
            if value:
                term = self.square(value)
                squared = term if not squared else self.add(squared, term)
        length = self.root(squared)
        if length.lo <= 0:
            _error("OKE-E-QUATERNION", "A supplied quaternion cannot be normalized within the finite proof range.")
        result = []
        for value in values:
            if not value:
                result.append(_Cell(Fraction(0), Fraction(0)))
                continue
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


def rational_clock(record, *, work=None, cache_parse=True):
    """Read a reduced, nonnegative exact clock without float conversion."""
    if not isinstance(record, dict) or set(record) != {"numerator", "denominator"}:
        _error("OKE-E-CLOCK", "A recording clock must retain its exact rational identity.")
    def calculate():
        numerator = _integer(record["numerator"], work=work)
        denominator = _integer(record["denominator"], work=work)
        _tick(work, "independent_clock_reduction")
        gcd = math.gcd(numerator, denominator)
        _tick(work, "independent_clock_reduction_return")
        if denominator <= 0 or gcd != 1:
            _error("OKE-E-CLOCK", "A recording clock must be reduced with a positive denominator.")
        return Fraction(numerator, denominator)
    # Every row retains its own exact clock. Only a short, complete pair of
    # immutable supplied strings can reuse their already successful parse and
    # reduction. Longer clocks take the ordinary chunked, preguarded path.
    # Charged lookup/promotion keeps the original cancellation callback.
    texts = record["numerator"], record["denominator"]
    if all(type(text) is str and len(text) <= 128 for text in texts):
        arithmetic = _Bounds(work)
        value = (arithmetic.reuse(("rational_clock", *texts), calculate)
                 if cache_parse else calculate())
        arithmetic.bits(value.numerator.bit_length(), value.denominator.bit_length())
        return value
    return calculate()


def _integer_clock_cell_contains(value, bits, arithmetic):
    """Compare a small exact clock with the same cell on a common grid.

    Every nonnegative binary32 value is an integer N times 2^-149. Its
    midpoint numerators are therefore sums of adjacent N values at 2^-150.
    This replaces rational midpoint division/reduction with bounded bitfield
    decoding; both additions and both exact comparisons remain charged.
    """
    def full_domain():
        return getattr(arithmetic.work, "max_operand_bits", MAX_OPERAND_BITS) == MAX_OPERAND_BITS

    numerator, denominator = value.numerator, value.denominator
    if (not full_domain() or
            max(numerator.bit_length(), denominator.bit_length()) > 1024):
        return None

    # Decoding a binary32 bitfield has a fixed maximum integer width. This
    # replaces the original uncharged struct/Fraction neighbor conversion.
    # The outer clock-cell admission remains the decoding checkpoint.
    arithmetic.bits(278)
    def scaled(integer):
        exponent, trailing = integer >> 23, integer & 0x7fffff
        return trailing if not exponent else ((1 << 23) | trailing) << (exponent - 1)

    center = scaled(bits)
    if bits == 0:
        lower = 0
    else:
        previous = scaled(bits - 1)
        arithmetic.tick("independent_exact_add")
        if not full_domain():
            return None
        arithmetic.bits(previous.bit_length(), center.bit_length(),
                        max(previous.bit_length(), center.bit_length()) + 1)
        lower = previous + center
    higher = 1 << 277 if bits == 0x7f7fffff else scaled(bits + 1)
    arithmetic.tick("independent_exact_add")
    if not full_domain():
        return None
    arithmetic.bits(center.bit_length(), higher.bit_length(),
                    max(center.bit_length(), higher.bit_length()) + 1)
    upper = center + higher

    arithmetic.tick("independent_exact_compare")
    if not full_domain():
        return None
    arithmetic.bits(numerator.bit_length() + 151,
                    denominator.bit_length() + lower.bit_length())
    scaled_value = numerator << 150
    lower_product = denominator * lower
    left = (scaled_value > lower_product) - (scaled_value < lower_product)
    arithmetic.tick("independent_exact_compare")
    if not full_domain():
        return None
    arithmetic.bits(scaled_value.bit_length(),
                    denominator.bit_length() + upper.bit_length())
    upper_product = denominator * upper
    right = (scaled_value > upper_product) - (scaled_value < upper_product)
    even = not bits & 1
    return ((left > 0 or even and left == 0) and (right < 0 or even and right == 0))


def clock_cell_contains(value, bits, *, work=None):
    """Check RNE by exact adjacent-cell midpoints, independently of the writer."""
    _tick(work, "independent_clock_cell")
    arithmetic = _Bounds(work)
    value = arithmetic.value(value)
    if type(bits) is not int or not 0 <= bits <= 0x7f7fffff or value < 0:
        return False
    integer_result = _integer_clock_cell_contains(value, bits, arithmetic)
    if integer_result is not None:
        return integer_result
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
    arithmetic = _Bounds(work)
    quantities = tuple(_quantity(record, name, work=work) for name in _NUMERIC_CERTIFICATE_KEYS)
    q = dict(zip(_NUMERIC_CERTIFICATE_KEYS, quantities))
    position_tolerance, rotation_tolerance = arithmetic.value(position_tolerance), arithmetic.value(rotation_tolerance)
    # Widths are irrelevant only when every coefficient using them is zero.
    proof_ha = ha if q["angular_speed_bound_rad_per_s"] or q["carrier_acceleration_bound_m_per_s2"] else Fraction(0)
    proof_hs = hs if q["enclosing_angular_speed_bound_rad_per_s"] or q["enclosing_carrier_acceleration_bound_m_per_s2"] else Fraction(0)
    key = ("complete_inequalities", proof_ha, proof_hs, quantities, position_tolerance, rotation_tolerance)
    return dict(arithmetic.reuse(key, lambda: tuple(_complete_inequality_values(
        ha, hs, q, position_tolerance, rotation_tolerance, arithmetic, model).items())))


def _complete_inequality_values(ha, hs, quantities, position_tolerance, rotation_tolerance, arithmetic, model,
                                *, field_comparisons=None):
    """Pure exact algebra after all supplied fields and widths are decoded."""
    if (field_comparisons is not None and (type(field_comparisons) is not _CertificateFieldComparisons
            or field_comparisons.arithmetic is not arithmetic)):
        field_comparisons = None
    q = quantities.__getitem__
    add, mul, div, square = arithmetic.add, arithmetic.mul, arithmetic.div, arithmetic.square
    # These intrinsic rational coefficients need no repeated external-value
    # decoding. Every actual operation still charges and guards both operands,
    # including the coefficient, immediately after its cancellation callback.
    four, eight, thirty_two = _CERTIFICATE_FOUR, _CERTIFICATE_EIGHT, _CERTIFICATE_THIRTY_TWO
    def require(name, minimum):
        actual = q(name)
        relation = (arithmetic.compare(actual, minimum) if field_comparisons is None
                    else field_comparisons.compare(actual, minimum))
        if relation < 0:
            _error("OKE-E-CERTIFICATE", "A reported bound understates the required exact sum.",
                   model=model, details={"quantity": name})
        return actual
    radius, vertex = q("landmark_radius_m"), q("local_vertex_error_bound_m")
    angular, acceleration = q("angular_speed_bound_rad_per_s"), q("carrier_acceleration_bound_m_per_s2")
    envelope_angular = q("enclosing_angular_speed_bound_rad_per_s")
    envelope_acceleration = q("enclosing_carrier_acceleration_bound_m_per_s2")
    speed, shift = q("enclosing_carrier_speed_bound_m_per_s"), q("max_endpoint_time_shift_s")
    position_quarter, rotation_quarter = div(position_tolerance, four), div(rotation_tolerance, four)
    terms = _CertificateTermReuse.create(arithmetic, quantities,
        (ha, hs, angular, acceleration, four, eight, position_tolerance,
         rotation_tolerance, position_quarter, rotation_quarter))
    for index, (width, a, w) in enumerate(((ha, acceleration, angular), (hs, envelope_acceleration, envelope_angular))):
        if index == 0 and terms is not None:
            angle = terms.calculate("angle", mul, w, width)
            width_squared = terms.calculate("width_squared", square, width)
            angle_squared = terms.calculate("angle_squared", square, angle)
            rotation = terms.calculate("rotation", div, angle_squared, four)
            product = terms.calculate("product", mul, a, width_squared)
            chord = terms.calculate("chord", div, product, eight)
        elif (terms is not None and terms.zero_quarter(
                angular, acceleration, envelope_angular, envelope_acceleration)):
            # Canonical zero coefficients do not depend on width equality.
            # The stored square still executes, with its own original guards.
            angle = terms.zero("angle", "mul", w, width)
            if angle is None:
                angle = mul(w, width)
            width_squared = square(width)
            angle_squared = terms.zero("angle_squared", "mul", angle, angle)
            if angle_squared is None:
                angle_squared = square(angle)
            rotation = terms.zero("rotation", "div", angle_squared, four)
            if rotation is None:
                rotation = div(angle_squared, four)
            product = terms.zero("product", "mul", a, width_squared)
            if product is None:
                product = mul(a, width_squared)
            chord = terms.zero("chord", "div", product, eight)
            if chord is None:
                chord = div(product, eight)
        else:
            angle, width_squared = mul(w, width), square(width)
            rotation, chord = div(square(angle), four), div(mul(a, width_squared), eight)
        if (arithmetic.compare(angle, ARC_LIMIT) > 0 or arithmetic.compare(rotation, rotation_quarter) > 0
                or arithmetic.compare(add(chord, mul(radius, rotation)), position_quarter) > 0):
            _error("OKE-E-CERTIFICATE", "The supplied key interval violates the mandatory quarter-allocation plan.", model=model)
    arc = q("stored_quaternion_arc_upper_rad")
    if arc > ARC_LIMIT:
        _error("OKE-E-CERTIFICATE", "The supplied stored quaternion arc exceeds the proved local range.", model=model)
    borrowed = terms.borrow("angle", "angle_squared", "width_squared") if terms is not None else None
    if borrowed is None:
        angular_width_squared, width_squared = square(mul(angular, ha)), square(ha)
    else:
        _, angular_width_squared, width_squared = borrowed
    difference = require("unit_quaternion_difference_bound", arithmetic.total((
        q("max_endpoint_unit_quaternion_error"), div(angular_width_squared, thirty_two), div(square(arc), eight))))
    if difference > Fraction(1, 2):
        _error("OKE-E-CERTIFICATE", "The supplied quaternion comparison exceeds its proved local range.", model=model)
    borrowed = terms.borrow("rotation") if terms is not None else None
    require("ideal_rotation_bound_rad", div(angular_width_squared, four) if borrowed is None else borrowed[0])
    borrowed = terms.borrow("product", "chord") if terms is not None else None
    chord = div(mul(acceleration, width_squared), eight) if borrowed is None else borrowed[1]
    require("ideal_position_bound_m", chord)
    rotation = require("total_rotation_bound_rad", arithmetic.total((mul(four, difference),
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
        # The complete common axis is parsed in order and retained below.
        # Every valid authored clock is distinct; these one-shot decodes need
        # no numerical-LRU lookup, insertion or eviction. Canonical parsing,
        # reduction, cancellation and the final live result guard still run.
        # Repeated interval widths keep rational_clock's ordinary cache path.
        source = rational_clock(source_record, work=work, cache_parse=False)
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
             "ontokin/reach_phase.py", "ontokin/reach_runtime.py", "ontokin/reach_export.py",
             "ontokin/reach_recording_fast.py", "ontokin/reach_recording_capture.py",
             "ontokin/reach_transfer_bounds.py")
    entries = [(name, _identified_digest(root / name, work=work)) for name in names]
    _tick(work, "independent_basis_aggregate")
    implementation = hashlib.sha256("".join(name + "\0" + digest + "\n" for name, digest in entries).encode("ascii")).hexdigest()
    derivation_names = ("docs/engineering/reach-numeric-kernel.md", "docs/engineering/reach-source-kernel.md",
                        "docs/engineering/reach-coaxial-phase-bounds.md",
                        "docs/engineering/reach-carrier-rotation-cursors.md",
                        "docs/engineering/reach-recording-certified-planar.md",
                        "docs/engineering/reach-deferred-phase-locations.md",
                        "docs/engineering/reach-planning-reuse.md",
                        "docs/engineering/reach-release-cell-envelope.md")
    derivations = [(name, _identified_digest(root / name, work=work)) for name in derivation_names]
    _tick(work, "independent_basis_aggregate")
    derivation = hashlib.sha256("".join(name + "\0" + digest + "\n" for name, digest in derivations).encode("ascii")).hexdigest()
    source = {"name": "OntoKin controlled source poses", "version": "0.2",
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


@dataclass(frozen=True)
class _VertexExtremaProof:
    source_positions: tuple
    stored_positions: tuple
    radius: Fraction
    vertex_error: Fraction


def _vertex_extrema(source_positions, stored_positions, *, work):
    """Reuse pure extrema only after checking this occurrence's actual vertices.

    The source mesh is an immutable native float tuple retained by the proof.
    Its identity therefore cannot be recycled while the proof is cached. The
    supplied accessor is deliberately not an identity key: every warm use
    compares all of its current entries with the independently proved single
    binary32 conversion. Bounded blocks keep cancellation responsive without
    repeating exact radius and error arithmetic for identical source meshes.
    """
    from .scene import MAX_MESH_VERTICES, float32

    def direct():
        return _vertex_extrema_uncached(source_positions, stored_positions, work=work)

    # Small or non-native inputs keep the original complete scalar path. In
    # particular no wider-cap proof substitutes for a narrowed operand domain.
    if (type(source_positions) is not tuple or type(stored_positions) not in (tuple, list)
            or not 128 <= len(source_positions) <= MAX_MESH_VERTICES
            or len(source_positions) != len(stored_positions)
            or work is None or not hasattr(work, "lookup") or not hasattr(work, "remember")
            or getattr(work, "max_operand_bits", None) != MAX_OPERAND_BITS):
        return direct()
    cap = work.max_operand_bits
    key = ("reach_independent_vertex_extrema_v1", cap, id(source_positions))
    proof = work.lookup(key)
    if work.max_operand_bits != cap:
        return direct()
    if isinstance(proof, _VertexExtremaProof) and proof.source_positions is source_positions:
        for start in range(0, len(source_positions), 128):
            _tick(work, "independent_geometry_reuse_block")
            if work.max_operand_bits != cap:
                return direct()
            actual = stored_positions[start:start + 128]
            expected = proof.stored_positions[start:start + 128]
            if (len(actual) != len(expected)
                    or any(type(row) is not tuple or len(row) != 3
                           or any(type(value) is not float for value in row) for row in actual)
                    or tuple(actual) != expected):
                return direct()
        _Bounds(work).bits(proof.radius.numerator.bit_length(), proof.radius.denominator.bit_length(),
                           proof.vertex_error.numerator.bit_length(), proof.vertex_error.denominator.bit_length())
        return proof.radius, proof.vertex_error

    radius, vertex_error = direct()
    if work.max_operand_bits != cap:
        return direct()
    snapshot = []
    for start in range(0, len(source_positions), 128):
        _tick(work, "independent_geometry_proof_block")
        if work.max_operand_bits != cap:
            return direct()
        source = source_positions[start:start + 128]
        actual = stored_positions[start:start + 128]
        if (len(actual) != len(source)
                or any(type(row) is not tuple or len(row) != 3
                       or any(type(value) is not float for value in row) for row in (*source, *actual))):
            return direct()
        # A callback may have changed a mutable accessor since the scalar
        # proof. Never bind that earlier proof to unchecked replacement bytes.
        if any(tuple(float32(value) for value in point) != stored
               for point, stored in zip(source, actual)):
            return direct()
        snapshot.extend(actual)
    proof = _VertexExtremaProof(source_positions, tuple(snapshot), radius, vertex_error)
    work.remember(key, proof)
    if work.max_operand_bits != cap:
        return direct()
    return radius, vertex_error


def _vertex_extrema_uncached(source_positions, stored_positions, *, work):
    """Find the same exact extrema without decoding every float as a rational.

    The actual source-to-binary32 comparison remains per vertex. On that
    admitted float path, source minus stored is exact in binary64: either the
    stored value is zero, or the two same-sign magnitudes differ by at most a
    factor of two. This also covers the first binary32 subnormal and ties.
    Only the three maximum errors then need exact rational decoding.

    Upward binary64 sums merely screen L1 candidates. Every possible new
    maximum still receives the original exact rational sum; the incumbent is
    rounded downward for screening, so neither rounding direction can hide a
    larger radius. Non-float source inputs retain the exact fallback.
    """
    from .scene import float32
    arithmetic = _Bounds(work)
    radius, radius_floor, radius_components = Fraction(0), 0., None
    float_errors, exact_errors = [0.] * 3, [Fraction(0)] * 3
    for point, stored in zip(source_positions, stored_positions):
        _tick(work, "independent_geometry_point")
        if len(point) != 3 or len(stored) != 3 or tuple(float32(value) for value in point) != tuple(stored):
            _error("OKE-E-GEOMETRY", "Every actual vertex must match the source's single binary32 conversion.")
        if all(type(value) is float for value in point):
            x, y, z = (abs(value) for value in point)
            upper = math.nextafter(math.nextafter(x + y, math.inf) + z, math.inf)
            # The current maximum already proves the exact L1 sum of these
            # same three finite float operands. Keep its attaining point as
            # a bounded witness, not another numeric cache. Every actual
            # vertex conversion and error maximum still executes above/below.
            # Narrowed domains retain the original scalar admission path.
            repeated_maximum = (_bound_domain(arithmetic) == MAX_OPERAND_BITS
                                and (x, y, z) == radius_components)
            if upper > radius_floor and not repeated_maximum:
                candidate = arithmetic.total(arithmetic.value(value) for value in (x, y, z))
                if candidate > radius:
                    radius = candidate
                    radius_floor = math.nextafter(float(radius), -math.inf)
                if candidate == radius:
                    radius_components = (x, y, z)
            float_errors = [max(previous, abs(value - actual))
                            for previous, value, actual in zip(float_errors, point, stored)]
        else:
            source = tuple(arithmetic.value(value) for value in point)
            radius = max(radius, arithmetic.total(abs(value) for value in source))
            radius_floor = math.nextafter(float(radius), -math.inf)
            exact_errors = [max(previous, abs(arithmetic.sub(value, actual)))
                            for previous, value, actual in zip(exact_errors, source, stored)]
    errors = [max(exact, arithmetic.value(value)) for exact, value in zip(exact_errors, float_errors)]
    return radius, arithmetic.norm(errors)


def _geometry_bounds(decoded, model, options, *, work):
    """Reconstruct source occurrence vertices independently of baked motion.

    The inherited, identified geometry constructors remain the native geometry
    contract. No reach writer, pose sampler, timeline or certificate routine is
    called. Every repeated occurrence consumes the aggregate vertex allowance.
    """
    from .geometry import assembly_marker, joint_marker
    from .scene import (MAX_MESH_VERTICES, SurfaceMesh, _source_primitive_mesh,
                        _source_surface_mesh, float32)
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
                mesh = _source_surface_mesh(obj.geometry, max_vertices=remaining,
                                            work=work, namespace="reach_independent_source")
            elif kind in ("box", "sphere"):
                mesh = _source_primitive_mesh(obj.geometry, work=work,
                                              namespace="reach_independent_source")
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
        radius, vertex_error = _vertex_extrema(source_positions, stored_positions, work=work)
        if owner is not None:
            for site in model.sites.values():
                if site.owner == owner:
                    radius = max(radius, arithmetic.total(abs(arithmetic.value(value))
                                                          for value in site.pose.position))
        result[index] = {"identity": identity, "frame": frame,
                         "radius": radius, "vertex_error": vertex_error}
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
_NUMERIC_CERTIFICATE_KEYS = tuple(sorted(_CERTIFICATE_KEYS - {"left_key_index", "right_key_index", "carrier",
    "source_phase_indices", "h_authored_seconds", "h_stored_seconds"}))


def _verify_metadata(decoded, model, options, program, boundary_records, *, work, target_contract=TARGET):
    from .scene import force_profile_metadata, relationship_metadata, checked_contract
    from .values import bounded_data
    metadata = decoded.document["extras"]["ontokin"]
    expected = {"target_contract": target_contract, "schema_version": checked_contract(model, target_contract), "module": model.module_name,
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
        "reach_profile": {"schema_version": "ontokin.reach-recording/0.1", "source_profile": model.profile,
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
    if animation_metadata.get("target_contract") != target_contract:
        _error("OKE-E-PROVENANCE", "Animation metadata must preserve the requested delivery contract.")
    # Formatting a boundary is independent of the writer's time formatter.
    expected_times = [record["source_seconds"] for record in boundary_records]
    if animation_metadata.get("boundary_times_seconds") != expected_times:
        _error("OKE-E-BOUNDARY-HISTORY", "Animation metadata omits or changes an independently reconstructed boundary.")
    return quantization


def _plain_projection_leaf(actual, expected):
    """Match the complete scalar type rule before a bounded native equality."""
    kind = type(expected)
    if kind is float:
        return (math.isfinite(expected) and type(actual) in (int, float)
                and (type(actual) is int or math.isfinite(actual)))
    return kind in (str, int, bool, type(None)) and type(actual) is kind


def _plain_projection_block(pairs):
    """One bounded identity comparison, retaining every scalar type guard."""
    return (all(_plain_projection_leaf(actual, expected) for actual, expected in pairs)
            and tuple(actual for actual, _ in pairs) == tuple(expected for _, expected in pairs))


def _plain_projection_tree(actual, expected):
    """Compare a complete small identity subtree without recursive paths.

    At most 64 container/leaf occurrences are visited. Every container shape and
    scalar type is checked, then one native tuple comparison covers the scalar
    values. Numerical enclosures, larger trees and mismatches take the ordinary
    recursive path, preserving its detailed diagnostics and numerical policy.
    The caller charges and polls before this bounded operation.
    """
    stack, first, last, entries = [(actual, expected)], [], [], 1
    while stack:
        observed, source = stack.pop()
        if type(source) is dict:
            if type(observed) is not dict or len(observed) != len(source):
                return False
            entries += len(source)
            if entries > 64 or set(observed) != set(source):
                return False
            stack.extend((observed[key], value) for key, value in source.items())
        elif type(source) in (list, tuple):
            if type(observed) is not list or len(observed) != len(source):
                return False
            entries += len(source)
            if entries > 64:
                return False
            stack.extend(zip(observed, source))
        else:
            if not _plain_projection_leaf(observed, source):
                return False
            first.append(observed)
            last.append(source)
    return tuple(first) == tuple(last)


def _history_allowance(path, allowances):
    labels = " ".join(str(value) for value in path)
    impulse_fields = {
        "lever_arm_world_m", "application_point_world_m", "angular_impulse_world_n_m_s",
        "linear_velocity_before_world_m_per_s", "linear_velocity_after_world_m_per_s",
        "angular_velocity_before_world_rad_per_s", "angular_velocity_after_world_rad_per_s",
    }
    source_impulse = (len(path) >= 2 and path[-2] in impulse_fields and "last_applications" in path)
    if source_impulse:
        # The ledger already encloses public rounding and dimensional propagation.
        return Fraction(0), True
    if "orientation" in labels or "angular" in labels or "omega" in labels:
        return allowances["angular_velocity"] if "velocity" in labels or "omega" in labels else allowances["rotation"], False
    if "velocity" in labels or "speed" in labels:
        return allowances["velocity"], False
    if any(label in labels for label in ("position", "residual", "world_target", "tip_pose")):
        return allowances["position"], False
    _error("OKE-E-INDEPENDENT-VALIDATION", "An independent numerical history leaf has no identified allowance.", details={"path": list(path)})


def _history_vector_key(actual, expected, arithmetic):
    """Guard every member before reusing one fixed numerical vector proof.

    Raw binary64 ratios are bounded before hashing, including on cache hits.
    Only the repeated Fraction construction and predicate evaluation are omitted.
    Unsupported shapes/types retain the ordinary recursive validation path.
    """
    from .reach_reference import Interval
    if len(expected) not in (3, 4) or not all(isinstance(value, Interval)
            and type(value.lo) is Fraction and type(value.hi) is Fraction for value in expected):
        return None
    if not all(type(value) is int or type(value) is float and math.isfinite(value) for value in actual):
        return None
    result = []
    for value, interval in zip(actual, expected):
        numerator, denominator = (value, 1) if type(value) is int else value.as_integer_ratio()
        arithmetic.bits(numerator.bit_length(), denominator.bit_length(),
                        interval.lo.numerator.bit_length(), interval.lo.denominator.bit_length(),
                        interval.hi.numerator.bit_length(), interval.hi.denominator.bit_length())
        arithmetic.bits(interval.lo.numerator.bit_length() + interval.hi.denominator.bit_length(),
                        interval.hi.numerator.bit_length() + interval.lo.denominator.bit_length())
        if interval.lo > interval.hi:
            _error("OKE-E-INDEPENDENT-VALIDATION", "An independent reference returned a reversed enclosure.")
        result.append((numerator, denominator, interval.lo, interval.hi))
    return tuple(result)


def _exact_history_vector(key, *, sign=1):
    """An exact point equality needs neither interval arithmetic nor a cache."""
    return all(low == high and numerator == sign * low.numerator
               and denominator == low.denominator for numerator, denominator, low, high in key)


def _history_orientation_sufficient(actual, expected, allowance, arithmetic):
    """Prove a raw history quaternion comparison with an exact L1 bound.

    Histories compare raw quaternion values and allow either antipodal sign.
    For either chosen sign, the Euclidean norm is at most the sum of the
    componentwise maximum absolute differences. No unit normalization or
    producer error estimate enters this proof. An insufficient bound, a
    narrower operand domain or unsupported cells retain both original norms.
    """
    if (_bound_domain(arithmetic) != MAX_OPERAND_BITS
            or not _small_proof_values((allowance,)) or allowance < 0):
        return False
    arithmetic.tick("independent_history_orientation_domain")
    if _bound_domain(arithmetic) != MAX_OPERAND_BITS:
        return False
    exact = arithmetic.cells(expected)
    aligned = _aligned_reference(actual, exact, arithmetic)
    bound = _optional_endpoint_l1(actual, aligned, arithmetic)
    return (bound is not None and _bound_domain(arithmetic) == MAX_OPERAND_BITS
            and arithmetic.compare(bound, allowance) <= 0
            and _bound_domain(arithmetic) == MAX_OPERAND_BITS)


def _assert_projection(actual, expected, *, arithmetic, allowances, path=()):
    """Compare complete histories; interval leaves retain their units/meaning."""
    from .reach_reference import Interval
    arithmetic.tick("independent_projection_entry")
    if isinstance(expected, Interval):
        if type(actual) not in (int, float):
            _error("OKE-E-BOUNDARY-HISTORY", "A numerical source history has a nonnumeric leaf.", details={"path": list(path)})
        allowance, source_impulse = _history_allowance(path, allowances)
        value = arithmetic.value(actual)
        low = expected.lo if type(expected.lo) is Fraction else arithmetic.value(expected.lo)
        high = expected.hi if type(expected.hi) is Fraction else arithmetic.value(expected.hi)
        allowance = allowance if type(allowance) is Fraction else arithmetic.value(allowance)
        arithmetic.bits(low.numerator.bit_length(), low.denominator.bit_length(),
                        high.numerator.bit_length(), high.denominator.bit_length(),
                        allowance.numerator.bit_length(), allowance.denominator.bit_length())
        def within():
            bound = allowance
            if not source_impulse:
                rounding = arithmetic.add(arithmetic.mul(max(abs(low), abs(high)), Fraction(1, 1 << 53)), Fraction(1, 1 << 1075))
                bound = arithmetic.add(bound, rounding)
            return (arithmetic.compare(value, arithmetic.sub(low, bound)) >= 0
                    and arithmetic.compare(value, arithmetic.add(high, bound)) <= 0)
        if not arithmetic.reuse(("history_interval", value, low, high, allowance, source_impulse), within):
            _error("OKE-E-BOUNDARY-HISTORY", "A recorded numerical state lies outside the independent source enclosure.", details={"path": list(path)})
    elif isinstance(expected, dict):
        if type(actual) is not dict or set(actual) != set(expected):
            _error("OKE-E-BOUNDARY-HISTORY", "A recorded source history omits or adds fields.", details={"path": list(path)})
        if _plain_projection_tree(actual, expected):
            return
        # The scalar members of a fixed record form one identity block even
        # when that record also contains numerical vectors or nested identities.
        # Compare every scalar type/value before descending into the remaining
        # fields; a failed block keeps the precise ordinary diagnostic path.
        if len(expected) <= 64:
            scalars = {key for key, value in expected.items() if type(value) in (str, int, float, bool, type(None))}
            if _plain_projection_block([(actual[key], expected[key]) for key in scalars]):
                for key, value in expected.items():
                    if key not in scalars:
                        _assert_projection(actual[key], value, arithmetic=arithmetic, allowances=allowances, path=(*path, key))
                return
        for key, value in expected.items():
            _assert_projection(actual[key], value, arithmetic=arithmetic, allowances=allowances, path=(*path, key))
    elif isinstance(expected, (tuple, list)):
        if type(actual) is not list or len(actual) != len(expected):
            _error("OKE-E-BOUNDARY-HISTORY", "A recorded source history omits or reorders entries.", details={"path": list(path)})
        if _plain_projection_tree(actual, expected):
            return
        if path and path[-1] == "orientation_wxyz" and len(expected) == 4:
            # Quaternion sign is a representation choice, not physical state.
            def compare_orientation():
                if key is not None and _history_orientation_sufficient(
                        actual, expected, allowance, arithmetic):
                    return True
                exact = [arithmetic.cell(value) for value in expected]
                positive = arithmetic.difference(actual, exact)
                negative = arithmetic.difference(actual, [_Cell(-value.hi, -value.lo) for value in exact])
                return min(positive, negative) <= allowances["rotation"]
            key = _history_vector_key(actual, expected, arithmetic)
            allowance = allowances["rotation"]
            if type(allowance) is not Fraction:
                allowance = arithmetic.value(allowance)
            arithmetic.bits(allowance.numerator.bit_length(), allowance.denominator.bit_length())
            if (key is not None and allowance >= 0 and
                    (_exact_history_vector(key) or _exact_history_vector(key, sign=-1))):
                return
            valid = (compare_orientation() if key is None else
                     arithmetic.reuse(("history_orientation", key, allowance), compare_orientation))
            if not valid:
                _error("OKE-E-BOUNDARY-HISTORY", "A recorded orientation differs from the independent source state.", details={"path": list(path)})
        else:
            key = _history_vector_key(actual, expected, arithmetic)
            if key is not None:
                # This exact scalar predicate is independent of action identity.
                # Resolve the dimensional policy before every lookup, including
                # the impulse ledger's stricter no-extra-rounding rule.
                allowance, source_impulse = _history_allowance((*path, 0), allowances)
                if type(allowance) is not Fraction:
                    allowance = arithmetic.value(allowance)
                arithmetic.bits(allowance.numerator.bit_length(), allowance.denominator.bit_length())
                if allowance >= 0 and _exact_history_vector(key):
                    return
                def compare_vector():
                    for index, (first, last) in enumerate(zip(actual, expected)):
                        _assert_projection(first, last, arithmetic=arithmetic, allowances=allowances, path=(*path, index))
                    return True
                arithmetic.reuse(("history_vector", key, allowance, source_impulse), compare_vector)
                return
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


def _aligned_reference(quaternion, expected, arithmetic):
    """Choose one antipodal representative; either gives a valid upper bound.

    For the required small endpoint error, the largest stored component has a
    decisive sign in the ideal interval. If that interval contains zero, keep
    the positive representative: an ambiguous choice may reject an unproved
    bound, but cannot understate physical rotation error. No second norm is
    needed merely to select the smaller of two valid upper bounds.
    """
    arithmetic.tick("independent_quaternion_sign")
    # The sign checkpoint can narrow the live domain after source-cell
    # admission. Check it before native Fraction comparisons or antipodal
    # negations, including on the optional sufficient-bound path.
    quaternion = _recording_vector(quaternion, 4, arithmetic)
    arithmetic._cache_operand_domain(tuple(expected))
    axis = max(range(4), key=lambda index: abs(quaternion[index]))
    value, interval = quaternion[axis], expected[axis]
    if value < 0 < interval.lo or value > 0 > interval.hi:
        return tuple(_Cell(-value.hi, -value.lo) for value in expected)
    return expected


def _same_recording_vector(first, last, size):
    # Exact typed supplied values are required. In particular, bool/int equality
    # cannot borrow a previously admitted floating-point endpoint comparison.
    return (type(first) in (tuple, list) and type(last) in (tuple, list)
            and len(first) == len(last) == size
            and all(type(a) is type(b) and a == b for a, b in zip(first, last)))


def _recording_vector(value, size, arithmetic):
    if type(value) not in (tuple, list) or len(value) != size:
        _error("OKE-E-CERTIFICATE", "A supplied recording endpoint has incompatible dimensions.")
    wide = arithmetic.work is None or getattr(arithmetic.work, "max_operand_bits", MAX_OPERAND_BITS) >= 1075
    if wide:
        # A finite binary64's reduced numerator needs at most 1024 bits and
        # its denominator at most 1075. This proves the fixed operand domain
        # without allocating the same exact ratio again on every reuse hit.
        arithmetic.bits(1075)
    for component in value:
        if type(component) not in (int, float) or (type(component) is float and not math.isfinite(component)):
            _error("OKE-E-CERTIFICATE", "A supplied recording endpoint must contain finite numbers.")
        if type(component) is int:
            arithmetic.bits(component.bit_length())
        elif not wide:
            # Lower request limits need the actual exact numerator/denominator
            # check, through the ordinary charged decoder, before any reuse.
            arithmetic.value(component)
    return tuple(value)


def _recording_orientation_comparison(quaternion, expected, arithmetic, *, before_error=None):
    """Share one independent orientation proof across translated carriers.

    Every actual stored quaternion and all four source interval cells are
    admitted before reuse. Position never enters this calculation; the raw
    quaternion sign and ordered exact source cells remain in its complete key.
    The bounded work cache returns only immutable normalized cells and error.
    A caller's position comparison still executes between normalization/sign
    selection and the orientation error on a miss, preserving cold failure
    order. That current comparison executes on a hit too and is never cached.
    """
    arithmetic.tick("independent_orientation_comparison_domain")
    quaternion = _recording_vector(quaternion, 4, arithmetic)
    if type(expected) not in (tuple, list) or len(expected) != 4:
        _error("OKE-E-CERTIFICATE", "An independent orientation comparison requires four source cells.")
    expected = arithmetic.cells(expected)
    compared_position = False
    def compare():
        nonlocal compared_position
        normalized = arithmetic.normalize(quaternion)
        aligned = _aligned_reference(quaternion, expected, arithmetic)
        if before_error is not None:
            before_error()
            compared_position = True
        return normalized, arithmetic.difference(normalized, aligned)
    result = arithmetic.reuse(("recording_orientation_comparison", quaternion, expected), compare)
    if before_error is not None and not compared_position:
        before_error()
    return result


def _bound_domain(arithmetic):
    return getattr(arithmetic.work, "max_operand_bits", MAX_OPERAND_BITS)


def _small_proof_values(values):
    # This is metadata of already admitted exact values, not a new arithmetic
    # operation. The deliberately small sufficient-proof domain also fits every
    # intermediate of the original normalization/difference proof at the full
    # 32,768-bit limit. Narrower live limits always keep that original path.
    return all(type(value) is Fraction and value.numerator.bit_length() <= 256
               and value.denominator.bit_length() <= 256 for value in values)


def _recording_uniform_lift_sign(first, last, arithmetic):
    """Prove a uniform exact raw-dot sign without decoding or multiplying.

    The caller has freshly admitted both actual recording vectors. This
    additional charged check establishes the sufficient proof's smaller
    exact-ratio domain after its own cancellation callback. Nonzero binary64
    values in [2**-200, 2**128] have at most 129 numerator bits and 253
    denominator bits, so the original 256-bit preflight would succeed.
    Mixed product signs and all other domains retain the exact dot proof.
    """
    arithmetic.tick("independent_stored_lift_sign")
    if _bound_domain(arithmetic) != MAX_OPERAND_BITS:
        return None
    if type(first) is not tuple or type(last) is not tuple or len(first) != 4 or len(last) != 4:
        return None
    for component in (*first, *last):
        if (type(component) is not float or not math.isfinite(component)
                or (component and not _LIFT_SIGN_COMPONENT_MIN <= abs(component) <= _LIFT_SIGN_COMPONENT_MAX)):
            return None
    relation = 0
    for a, b in zip(first, last):
        if a == 0 or b == 0:
            continue
        sign = 1 if (a < 0) == (b < 0) else -1
        if relation and sign != relation:
            return None
        relation = sign
    return relation


class _PositionOperands:
    """One endpoint's completed coordinate decodes, discarded after its proof.

    Only the two existing position helpers receive this view. Each has already
    polled its own domain checkpoint and admits the current stored coordinates
    before requesting a decode. All arithmetic, interval admission and cache
    operations still belong to the original independent reader. This is not a
    retained endpoint proof or another request cache.
    """
    def __init__(self, arithmetic, position):
        self.arithmetic = arithmetic
        self.owner = arithmetic.work
        self.position = tuple(position)
        self.exact = (None,) * len(self.position)

    def __getattr__(self, name):
        return getattr(self.arithmetic, name)

    def value(self, value):
        indices = ()
        if (len(self.position) == 3 and type(value) in (int, float)
                and self.arithmetic.work is self.owner
                and _bound_domain(self) == MAX_OPERAND_BITS):
            indices = tuple(index for index, raw in enumerate(self.position)
                            if type(raw) is type(value) and raw == value)
            for index in indices:
                if self.exact[index] is not None:
                    result = self.exact[index]
                    self.arithmetic._cache_operand_domain(result)
                    return result
        result = self.arithmetic.value(value)
        if (indices and self.arithmetic.work is self.owner
                and _bound_domain(self) == MAX_OPERAND_BITS
                and _small_proof_values((result,))):
            # Publication occurs only after the real decoder and its callback
            # complete successfully. A nested callback cannot publish a partial
            # ratio, and narrower/wider values keep their ordinary decoder.
            self.exact = tuple(result if index in indices else previous
                               for index, previous in enumerate(self.exact))
        return result


def _optional_endpoint_l1(actual, expected, arithmetic, *, admitted_cells=False):
    """An optional exact L1 enclosure, never a replacement on insufficiency."""
    arithmetic.tick("independent_sufficient_endpoint_domain")
    if len(actual) != len(expected) or len(actual) not in (3, 4):
        _error("OKE-E-CERTIFICATE", "An independent vector comparison has incompatible dimensions.")
    if _bound_domain(arithmetic) != MAX_OPERAND_BITS:
        return None
    # Exact typed zeros need no new Fraction decoding. The enclosing domain
    # checkpoint and the following complete interval admission still execute;
    # foreign zero-like values keep their original scalar rejection path.
    actual = tuple(Fraction(0) if type(value) in (int, float, Fraction) and value == 0
                   else arithmetic.value(value) for value in actual)
    if (admitted_cells and type(expected) is tuple
            and all(type(cell) is _Cell and type(cell.lo) is Fraction
                    and type(cell.hi) is Fraction for cell in expected)):
        # The caller already converted these frozen exact cells. Its result
        # survives no unchecked callback: the endpoint checkpoint and scalar
        # decoders above are followed by the full current width/order guards.
        # No new cells or redundant vector-admission checkpoint are necessary.
        arithmetic._cache_operand_domain(expected)
        for cell in expected:
            if cell.lo > cell.hi:
                _error("OKE-E-INDEPENDENT-VALIDATION", "An independent reference returned a reversed enclosure.")
    else:
        expected = arithmetic.cells(expected)
    if (_bound_domain(arithmetic) != MAX_OPERAND_BITS
            or not _small_proof_values((*actual, *(value for cell in expected for value in (cell.lo, cell.hi))))):
        return None

    def receipt(value, cell):
        if (type(value) is not Fraction or type(cell) is not _Cell
                or type(cell.lo) is not Fraction or type(cell.hi) is not Fraction):
            return None
        integers = (value.numerator, value.denominator, cell.lo.numerator,
                    cell.lo.denominator, cell.hi.numerator, cell.hi.denominator)
        if (all(type(integer) is int for integer in integers)
                and all(integers[index] > 0 for index in (1, 3, 5))):
            return integers
        return None

    # The source order above proves x-lo >= x-hi. Keep that proof only while
    # the exact admitted operands and live work domain survive each existing
    # subtraction callback. Capture all components now: an earlier component's
    # callback can also change a later frozen cell through object.__setattr__.
    owner = arithmetic.work
    admitted = tuple(receipt(value, cell) for value, cell in zip(actual, expected))
    def unchanged(value, cell, proof):
        domain = _bound_domain(arithmetic)
        return (proof is not None and arithmetic.work is owner
                and type(domain) is int and domain == MAX_OPERAND_BITS
                and receipt(value, cell) == proof)

    result = Fraction(0)
    for value, cell, proof in zip(actual, expected, admitted):
        if cell.lo == cell.hi:
            error = Fraction(0) if value == cell.lo else abs(arithmetic.sub(value, cell.lo))
        else:
            ordered = unchanged(value, cell, proof)
            signed = arithmetic.sub(value, cell.lo)
            first = abs(signed)
            nonpositive = type(signed) is Fraction and signed.numerator <= 0
            ordered = ordered and unchanged(value, cell, proof)
            signed = arithmetic.sub(value, cell.hi)
            last = abs(signed)
            nonnegative = type(signed) is Fraction and signed.numerator >= 0
            ordered = ordered and unchanged(value, cell, proof)
            if ordered and (nonnegative or nonpositive):
                # Outside the ordered source cell, the farthest endpoint follows
                # from the already computed signs. No rational cross products
                # are needed, but retain both original comparison width guards.
                arithmetic.bits(first.numerator.bit_length(), first.denominator.bit_length(),
                                last.numerator.bit_length(), last.denominator.bit_length())
                arithmetic.bits(first.numerator.bit_length() + last.denominator.bit_length(),
                                last.numerator.bit_length() + first.denominator.bit_length())
                error = first if nonnegative else last
            else:
                error = first if arithmetic.compare(first, last) >= 0 else last
        if error:
            result = arithmetic.add(result, error) if result else error
    return result


def _recording_orientation_bound(quaternion, expected, limit, arithmetic, *, before_error=None):
    """Prove the actual endpoint claim without normalization when sufficient.

    The expected cells come from the independent ideal rigid-pose reference;
    its true enclosed quaternion is unit, including source event transfers.
    For that q and nonzero raw x, the reverse triangle inequality gives
    ||x/||x||-q|| <= |1-||x||||+||x-q|| <= 2||x-q|| <= 2 L1.
    A bound at most 1/2 also proves ||x|| >= 3/4, so a zero or near-zero raw
    quaternion cannot enter this shortcut. The source interval need not consist
    solely of unit points. See reach-independent-endpoint-bounds.md.

    The supplied claim is only a threshold for this independently computed
    bound. A tighter claim retains the original normalization and norm proof.
    """
    if _bound_domain(arithmetic) == MAX_OPERAND_BITS:
        arithmetic.tick("independent_sufficient_orientation_domain")
        quaternion = _recording_vector(quaternion, 4, arithmetic)
        if type(expected) not in (tuple, list) or len(expected) != 4:
            _error("OKE-E-CERTIFICATE", "An independent orientation comparison requires four source cells.")
        expected = arithmetic.cells(expected)
        def calculate_bound():
            aligned = _aligned_reference(quaternion, expected, arithmetic)
            distance = _optional_endpoint_l1(quaternion, aligned, arithmetic, admitted_cells=True)
            domain = _bound_domain(arithmetic)
            factor = _ENDPOINT_TWO
            if (type(domain) is int and domain == MAX_OPERAND_BITS
                    and type(factor) is Fraction and type(factor.numerator) is int
                    and type(factor.denominator) is int and factor.numerator == 2
                    and factor.denominator == 1):
                # Copy the already exact native ratio without decoding or
                # reduction. A mul callback cannot mutate this local operand
                # through an alias to the module's constant Fraction.
                factor = Fraction(factor)
            else:
                factor = 2
            return () if distance is None else (arithmetic.mul(factor, distance),)
        def sufficient(candidate):
            if not candidate or _bound_domain(arithmetic) != MAX_OPERAND_BITS:
                return False
            # For these native finite thresholds E <= limit already implies
            # E <= 1/2. No rational arithmetic or conversion is performed by
            # this bounded classification. The actual supplied threshold is
            # still decoded/guarded by the ordinary comparison below. Foreign,
            # nonfinite, large and exact-Fraction claims keep the old order.
            small_claim = (type(limit) is int and limit == 0 or
                           type(limit) is float and math.isfinite(limit) and 0 <= limit <= .5)
            if not small_claim:
                if (arithmetic.compare(candidate[0], Fraction(1, 2)) > 0
                        or _bound_domain(arithmetic) != MAX_OPERAND_BITS):
                    return False
            return (arithmetic.compare(candidate[0], limit) <= 0
                    and _bound_domain(arithmetic) == MAX_OPERAND_BITS)
        if type(limit) in (int, float, Fraction):
            # Translated siblings often have the same complete orientation
            # operands. Keep one threshold-independent bound and, when its
            # first claim succeeds, that exact typed threshold in the same
            # existing cache entry. Equal claims reuse the completed pair of
            # inequalities; changed claims compare against the same bound.
            # No position proof or writer bound is inherited. The threshold
            # is first admitted by compare(), before it can enter a receipt;
            # no supplied threshold is hashed before scalar admission.
            calculated, proved = False, False
            def calculate_claim():
                nonlocal calculated, proved
                calculated = True
                candidate = calculate_bound()
                proved = bool(sufficient(candidate))
                return (*candidate, type(limit).__name__, limit) if proved else candidate
            candidate = arithmetic.reuse(("recording_orientation_sufficient_claim", quaternion,
                                         expected), calculate_claim)
            same_claim = (len(candidate) == 3 and candidate[1] == type(limit).__name__
                          and type(candidate[2]) is type(limit) and candidate[2] == limit)
            admitted = (bool(candidate) and _bound_domain(arithmetic) == MAX_OPERAND_BITS
                        and (same_claim or (proved if calculated else sufficient(candidate))))
        else:
            # Foreign values retain their original charged scalar decoder and
            # rejection path; coercive equality cannot borrow a native claim.
            candidate = arithmetic.reuse(("recording_orientation_sufficient_bound", quaternion,
                                         expected), calculate_bound)
            admitted = sufficient(candidate)
        if admitted:
            if before_error is not None:
                before_error()
            # A position callback or cache callback can narrow the live cap.
            # It cannot make this shortcut stand in for a narrower root proof.
            if _bound_domain(arithmetic) == MAX_OPERAND_BITS:
                return None, candidate[0]
    return _recording_orientation_comparison(quaternion, expected, arithmetic, before_error=before_error)


def _recording_position_bound(position, expected, limit, arithmetic):
    bound = _optional_endpoint_l1(position, expected, arithmetic)
    if (bound is not None and _bound_domain(arithmetic) == MAX_OPERAND_BITS
            and arithmetic.compare(bound, limit) <= 0
            and _bound_domain(arithmetic) == MAX_OPERAND_BITS):
        return bound
    return arithmetic.difference(position, expected)


def _endpoint_claim_limits(rows, carrier, index, arithmetic):
    """Admit both actual adjacent-row claims; retain only their current minimum."""
    arithmetic.tick("independent_endpoint_claims")
    records = tuple(rows[key, carrier] for key in (index - 1, index) if (key, carrier) in rows)
    limits = []
    for name in ("max_endpoint_position_error_m", "max_endpoint_unit_quaternion_error"):
        values = []
        for record in records:
            value = record[name]
            if type(value) not in (int, float) or (type(value) is float and not math.isfinite(value)) or value < 0:
                _error("OKE-E-CERTIFICATE", "A certificate quantity must be a finite nonnegative number.",
                       details={"quantity": name})
            if type(value) is int:
                arithmetic.bits(value.bit_length())
            values.append(value)
        # Full certificate coverage was already established. An isolated key
        # with no positive-width intervals has no claim to use as a shortcut.
        if not values:
            return None
        first = values[0]
        if len(values) == 2 and values[1] != first and arithmetic.compare(values[1], first) < 0:
            first = values[1]
        limits.append(first)
    return tuple(limits)


def _previous_position_comparison(previous, position, expected, limit, arithmetic):
    """Reuse an unchanged position proof in the required preceding-key map.

    A changing orientation does not change a position error or the supplied
    position's magnitude. The independent source cells are evaluated afresh
    before this helper runs. Only their exact complete equality, the actual
    typed buffer values, the same claim and the same live domain admit reuse.
    This retains no additional cache or source-state shortcut.
    """
    if previous is None:
        return None
    receipt = previous.get("_position_receipt")
    if (type(receipt) is not tuple or len(receipt) != 3
            or not _same_recording_vector(position, receipt[0], 3)
            or type(limit) is not type(receipt[2]) or limit != receipt[2]
            or previous.get("_proof_cap") != _bound_domain(arithmetic)):
        return None
    # A source cell containing zero is not an exact zero, and coercive
    # bool/int or foreign-cell equality cannot borrow an admitted proof.
    if (type(expected) not in (tuple, list) or len(expected) != 3
            or any(type(cell) not in (_Cell, _ReferenceCell)
                   or type(cell.lo) is not Fraction or type(cell.hi) is not Fraction
                   for cell in expected)
            or tuple((cell.lo, cell.hi) for cell in expected) != receipt[1]):
        return None
    arithmetic.tick("independent_position_key_reuse")
    position = _recording_vector(position, 3, arithmetic)
    arithmetic.cells(expected)
    if previous.get("_proof_cap") != _bound_domain(arithmetic):
        return None
    values = previous["position_error"], previous["magnitude"]
    arithmetic._cache_operand_domain(values)
    return values


def _recording_position_magnitude(position, arithmetic):
    """Sum current supplied magnitudes without decoding or adding exact zeros.

    Three finite binary64 operands and integers of at most 1,024 bits keep
    every original zero-addition and partial-sum preflight below 3,228 bits.
    Only that sufficient domain at the full cap may omit those operations;
    larger integers and any narrower live cap retain the original fold.
    """
    def direct():
        return arithmetic.total(abs(arithmetic.value(value)) for value in position)
    if _bound_domain(arithmetic) != MAX_OPERAND_BITS:
        return direct()
    arithmetic.tick("independent_position_magnitude")
    position = _recording_vector(position, 3, arithmetic)
    if (_bound_domain(arithmetic) != MAX_OPERAND_BITS
            or any(type(value) is int and value.bit_length() > 1024 for value in position)):
        return direct()
    result = Fraction(0)
    for value in position:
        if not value:
            continue
        term = abs(arithmetic.value(value))
        if _bound_domain(arithmetic) != MAX_OPERAND_BITS:
            return direct()
        result = arithmetic.add(result, term) if result else term
        if _bound_domain(arithmetic) != MAX_OPERAND_BITS:
            return direct()
    return result


class _CenteredEndpointDomain(Exception):
    """A compact sufficient proof needs the ordinary current-domain path."""


def _centered_claim_sufficient(value, claim, arithmetic):
    """Prove a strict local inequality from fresh native field metadata.

    This does not decode the claim or replace the independent endpoint bound.
    The complete original decode/comparison domain fits before either actual
    operation can be omitted. Unsupported or tight operands keep that path.
    """
    if (type(arithmetic) is not _Bounds or _tick is not _CERTIFICATE_TICK
            or type(_bound_domain(arithmetic)) is not int
            or _bound_domain(arithmetic) != MAX_OPERAND_BITS
            or type(claim) is not float or not math.isfinite(claim) or claim <= 0):
        return False
    # Check dispatch at this actual omission point, after every preceding
    # surviving callback. A custom or newly replaced operation must execute
    # through the existing exact fallback, including its original exception.
    dispatches = ((arithmetic, _CERTIFICATE_BOUNDS_DISPATCH),)
    owner = arithmetic.work
    if owner is not None:
        if type(owner) is not _CertificateWork:
            return False
        dispatches += ((owner, _CERTIFICATE_WORK_DISPATCH),)
    for target, entries in dispatches:
        for name, original in entries:
            method = getattr(target, name, None)
            if type(method) is not MethodType or method.__self__ is not target or method.__func__ is not original:
                return False
    fields = _certificate_fraction_fields(value)
    if fields is None or fields[0] < 0:
        return False
    numerator, denominator = fields
    encoded = struct.unpack(">Q", struct.pack(">d", claim))[0]
    exponent = (encoded >> 52) & 0x7ff
    # For a positive normal q, q >= 2**(E-1023). A positive subnormal
    # q=M*2**-1074 instead has q >= 2**(bits(M)-1075). No power, exact
    # float ratio or rational cross product is constructed by this proof.
    lower = (exponent - 1023 if exponent else
             (encoded & ((1 << 52) - 1)).bit_length() - 1075)
    if numerator and numerator.bit_length() - denominator.bit_length() + 1 > lower:
        return False
    # A native finite binary64 decode has <=1024 numerator and <=1075
    # denominator bits. With the fresh <=2048-bit fraction, every original
    # scalar and prospective comparison guard is therefore <=3123 bits.
    # These native guard methods have no cancellation callback; snapshots
    # cannot be redirected between this admission and the strict proof.
    arithmetic.bits(numerator.bit_length(), denominator.bit_length(), 1075,
                    numerator.bit_length() + 1075, 1024 + denominator.bit_length())
    return _certificate_fraction_fields(value) == fields


def _recording_centered_comparison(ideal, position, quaternion, limits, arithmetic, *,
                                   previous=None, completed=()):
    """Compare actual supplied values to a private center AND its radius.

    Only completed sufficient inequalities return a proof. The caller obtains
    ordinary independent intervals on this same work if either inequality is
    insufficient or this optional full-cap domain changes. No center is
    normalized or treated as an exact source observation.
    """
    from .reach_reference import _recording_source_signature
    from .reach_reference_center import _CenteredPose, _integers, _native

    if (limits is None or type(ideal) is not _CenteredPose
            or type(arithmetic) is not _Bounds or _bound_domain(arithmetic) != MAX_OPERAND_BITS):
        return None
    fields = (ideal.position, ideal.orientation, ideal.position_radius, ideal.orientation_radius, ideal.axis)
    if (type(ideal.position) is not tuple or len(ideal.position) != 3
            or type(ideal.orientation) is not tuple or len(ideal.orientation) != 4
            or any(not _native(value) for value in ideal.position)
            or any(not _native(value, magnitude=2) for value in ideal.orientation)
            or not _native(ideal.position_radius, magnitude=1)
            or not _native(ideal.orientation_radius, magnitude=1)
            or _integers(fields) != ideal.seal
            or not 0 <= ideal.position_radius <= Fraction(1, 1 << 94)
            or not 0 <= ideal.orientation_radius <= Fraction(1, 1 << 104)):
        _error("OKE-E-INDEPENDENT-VALIDATION", "A private centered reference proof changed.")
    owner, owner_kind = arithmetic.work, type(arithmetic.work)
    external = getattr(owner, "external_check", None)
    saved_seal = ideal.seal
    live = (*ideal.position, *ideal.orientation, ideal.position_radius, ideal.orientation_radius)
    integers = tuple((value.numerator, value.denominator) for value in live)
    # Fraction copies are made from saved native integer fields before any
    # callback. A mutate-and-restore callback cannot redirect point arithmetic
    # through an alias to the center, its radius or the preceding proof.
    values = tuple(Fraction(numerator, denominator) for numerator, denominator in integers)
    source_position, source_rotation = values[:3], values[3:7]
    position_radius, rotation_radius = values[7:]
    invalidated = False

    def current():
        nonlocal invalidated
        observed = (ideal.position, ideal.orientation, ideal.position_radius, ideal.orientation_radius, ideal.axis)
        if (type(ideal) is not _CenteredPose or ideal.seal is not saved_seal
                or any(observed[index] is not fields[index] for index in range(4))
                or type(observed[4]) is not type(fields[4]) or observed[4] != fields[4]
                or any(type(value) is not Fraction or type(value.numerator) is not int
                       or type(value.denominator) is not int
                       or (value.numerator, value.denominator) != saved
                       for value, saved in zip(live, integers))
                or arithmetic.work is not owner or type(owner) is not owner_kind
                or getattr(owner, "external_check", None) is not external):
            _error("OKE-E-INDEPENDENT-VALIDATION", "A private centered endpoint operand or owner changed.")
        invalidated = invalidated or _bound_domain(arithmetic) != MAX_OPERAND_BITS
        return not invalidated

    def checked(operation, *args):
        result = operation(*args)
        if not current():
            raise _CenteredEndpointDomain()
        return result

    def l1(actual, expected, decoder):
        distance = Fraction(0)
        for raw, point in zip(actual, expected):
            value = (Fraction(0) if raw == 0 else checked(decoder.value, raw))
            if not _small_proof_values((value, point)):
                raise _CenteredEndpointDomain()
            error = Fraction(0) if value == point else abs(checked(arithmetic.sub, value, point))
            if error:
                distance = error if not distance else checked(arithmetic.add, distance, error)
        return distance

    def compare_claim(value, claim):
        if not current():
            raise _CenteredEndpointDomain()
        if _centered_claim_sufficient(value, claim, arithmetic):
            if not current():
                raise _CenteredEndpointDomain()
            return -1
        # A raw claim decode and the following native comparison have
        # separate original callbacks. Check both before the next can restore
        # a narrowed domain or changed operand owner.
        if type(claim) is not Fraction:
            claim = checked(arithmetic.value, claim)
        return checked(arithmetic.compare, value, claim)

    def sealed(payload):
        return payload, _recording_source_signature(payload)

    def reused(proof, actual, center, radius, limit):
        if type(proof) is not tuple or len(proof) != 2:
            return None
        payload, signature = proof
        if (type(payload) is not tuple or len(payload) != 7
                or _recording_source_signature(payload) != signature
                or not _same_recording_vector(actual, payload[0], len(actual))
                or center != payload[1] or radius != payload[2]
                or type(limit) is not type(payload[3]) or limit != payload[3]
                or payload[6] != MAX_OPERAND_BITS
                or type(payload[4]) is not Fraction
                or payload[5] is not None and type(payload[5]) is not Fraction):
            return None
        result = (Fraction(payload[4].numerator, payload[4].denominator),
                  None if payload[5] is None else Fraction(payload[5].numerator, payload[5].denominator))
        checked(arithmetic.tick, "independent_centered_endpoint_reuse")
        arithmetic._cache_operand_domain(payload)
        if _recording_source_signature(payload) != signature:
            _error("OKE-E-INDEPENDENT-VALIDATION", "A completed centered endpoint proof changed.")
        if not current():
            raise _CenteredEndpointDomain()
        return result

    try:
        checked(arithmetic.tick, "independent_centered_endpoint_domain")
        position = _recording_vector(position, 3, arithmetic)
        quaternion = _recording_vector(quaternion, 4, arithmetic)
        arithmetic._cache_operand_domain(values)
        if not current():
            raise _CenteredEndpointDomain()
        position_arithmetic = _PositionOperands(arithmetic, position)
        position_error = magnitude = None
        if previous is not None:
            value = reused(previous.get("_centered_position_proof"), position,
                           source_position, position_radius, limits[0])
            if value is not None:
                position_error, magnitude = value
        if position_error is None:
            position_error = l1(position, source_position, position_arithmetic)
            if position_radius:
                position_error = checked(arithmetic.add, position_error, position_radius)
            if compare_claim(position_error, limits[0]) > 0:
                return None

        # Either antipodal representative gives a valid Euclidean bound. The
        # radius does not change when choosing the center's representative.
        expected = (source_rotation[1], source_rotation[2], source_rotation[3], source_rotation[0])
        checked(arithmetic.tick, "independent_centered_quaternion_sign")
        axis = max(range(4), key=lambda index: abs(quaternion[index]))
        if quaternion[axis] < 0 < expected[axis] or quaternion[axis] > 0 > expected[axis]:
            expected = tuple(-value for value in expected)
        quaternion_error = None
        for result in completed:
            value = reused(result.get("_centered_orientation_proof"), quaternion,
                           expected, rotation_radius, limits[1])
            if value is not None:
                quaternion_error = value[0]
                break
        if quaternion_error is None:
            distance = l1(quaternion, expected, arithmetic)
            if rotation_radius:
                distance = checked(arithmetic.add, distance, rotation_radius)
            quaternion_error = checked(arithmetic.mul, Fraction(2), distance)
            # A claim no larger than 1/2 establishes both inequalities with
            # one actual threshold comparison, as in the interval shortcut.
            small = (type(limits[1]) is int and limits[1] == 0 or
                     type(limits[1]) is float and math.isfinite(limits[1]) and 0 <= limits[1] <= .5)
            if not small and checked(arithmetic.compare, quaternion_error, Fraction(1, 2)) > 0:
                return None
            if compare_claim(quaternion_error, limits[1]) > 0:
                return None
        if magnitude is None:
            # The source/actual vectors already passed their complete native
            # admission. Keep every remaining magnitude callback visible to
            # this proof's live receipt, including reused coordinate decodes.
            checked(arithmetic.tick, "independent_position_magnitude")
            magnitude = Fraction(0)
            for raw in position:
                if raw:
                    term = abs(checked(position_arithmetic.value, raw))
                    magnitude = term if not magnitude else checked(arithmetic.add, magnitude, term)
        if not current():
            return None
        return {"position_error": position_error, "quaternion_error": quaternion_error,
                "normalized": None, "magnitude": magnitude, "_proof_cap": MAX_OPERAND_BITS,
                "_quaternion_operand": quaternion, "_normalized_cap": None,
                "_endpoint_limit_receipt": limits,
                "_centered_position_proof": sealed((position, source_position, position_radius,
                                                     limits[0], position_error, magnitude, MAX_OPERAND_BITS)),
                "_centered_orientation_proof": sealed((quaternion, expected, rotation_radius,
                                                        limits[1], quaternion_error, None, MAX_OPERAND_BITS))}
    except _CenteredEndpointDomain:
        return None


def _key_comparisons(reference, geometry, tracks, time, index, arithmetic, *, previous=None, previous_time=None,
                     recording_context=None, endpoint_rows=None):
    result, pending, observed, candidates = {}, [], [], []
    for carrier, item in geometry.items():
        arithmetic.tick("independent_key_pose")
        position = _recording_vector(tracks[carrier]["translation"][index], 3, arithmetic)
        quaternion = _recording_vector(tracks[carrier]["rotation"][index], 4, arithmetic)
        limits = (_endpoint_claim_limits(endpoint_rows, carrier, index, arithmetic)
                  if endpoint_rows is not None else None)
        same = (previous is not None
                and previous[carrier].get("_proof_cap") == _bound_domain(arithmetic)
                and _same_recording_vector(position, tracks[carrier]["translation"][index - 1], 3)
                and _same_recording_vector(quaternion, tracks[carrier]["rotation"][index - 1], 4))
        observed.append((carrier, item, position, quaternion, same, limits))
        if same:
            candidates.append(item["frame"])
    stationary = (reference.recording_stationary_frames(candidates, previous_time, time, side="after")
                  if candidates else frozenset())
    for carrier, item, position, quaternion, same, limits in observed:
        if same and item["frame"] in stationary:
            # The existing preceding-endpoint map is required by the interval
            # proof. Reuse its result only after independently proving unchanged
            # source operands and checking these actual supplied buffer values.
            # No additional numeric cache or history is retained.
            arithmetic.tick("independent_stationary_key_comparison")
            receipt = previous[carrier].get("_endpoint_limit_receipt")
            if (previous[carrier].get("_proof_cap") == _bound_domain(arithmetic)
                    and (limits is None or _same_recording_vector(limits, receipt, 2) or (
                        arithmetic.compare(previous[carrier]["position_error"], limits[0]) <= 0
                        and arithmetic.compare(previous[carrier]["quaternion_error"], limits[1]) <= 0))
                    and previous[carrier].get("_proof_cap") == _bound_domain(arithmetic)):
                result[carrier] = dict(previous[carrier])
                if limits is not None:
                    # These same inequalities have succeeded in this domain.
                    # Retain their actual typed thresholds only in the already
                    # required preceding-endpoint map. Fresh row admission and
                    # source stationarity still run at every later endpoint.
                    result[carrier]["_endpoint_limit_receipt"] = limits
                continue
        pending.append((carrier, item, position, quaternion, limits))
    centered_reader = getattr(reference, "_recording_centered_poses", None)
    centered = (centered_reader(tuple(item["frame"] for _, item, _, _, _ in pending), time,
                               side="after", recording_context=recording_context)
                if pending and callable(centered_reader) and all(limits is not None for *_, limits in pending)
                else None)
    if centered is not None:
        remaining = []
        for carrier, item, position, quaternion, limits in pending:
            comparison = _recording_centered_comparison(
                centered[item["frame"]], position, quaternion, limits, arithmetic,
                previous=None if previous is None else previous[carrier], completed=tuple(result.values()))
            if comparison is None:
                remaining.append((carrier, item, position, quaternion, limits))
            else:
                result[carrier] = comparison
        pending = remaining
    ideals = (reference.recording_pose_enclosures(
        tuple(item["frame"] for _, item, _, _, _ in pending), time, side="after",
        recording_context=recording_context) if pending else {})
    for carrier, item, position, quaternion, limits in pending:
        ideal = ideals[item["frame"]]
        def compare():
            admitted_cap = _bound_domain(arithmetic)
            expected = (ideal.orientation[1], ideal.orientation[2], ideal.orientation[3], ideal.orientation[0])
            position_error = magnitude = None
            position_arithmetic = _PositionOperands(arithmetic, position)
            def compare_position():
                nonlocal position_error, magnitude
                reused = _previous_position_comparison(
                    None if previous is None else previous[carrier], position, ideal.position,
                    None if limits is None else limits[0], arithmetic)
                if reused is not None:
                    position_error, magnitude = reused
                    return
                position_error = (arithmetic.difference(position, ideal.position) if limits is None
                                  else _recording_position_bound(position, ideal.position, limits[0], position_arithmetic))
            if limits is None:
                normalized, quaternion_error = _recording_orientation_comparison(
                    quaternion, expected, arithmetic, before_error=compare_position)
            else:
                normalized, quaternion_error = _recording_orientation_bound(
                    quaternion, expected, limits[1], arithmetic, before_error=compare_position)
            if magnitude is None:
                magnitude = _recording_position_magnitude(position, position_arithmetic)
            cap = admitted_cap if admitted_cap == _bound_domain(arithmetic) else None
            return (("position_error", position_error),
                    ("quaternion_error", quaternion_error), ("normalized", normalized),
                    ("magnitude", magnitude), ("_proof_cap", cap),
                    ("_position_receipt", (position, tuple((cell.lo, cell.hi) for cell in ideal.position),
                                           None if limits is None else limits[0])),
                    ("_quaternion_operand", quaternion),
                    ("_normalized_cap", cap if normalized is not None else None))
        result[carrier] = dict(arithmetic.reuse(("key_pose_comparison", tuple(position), tuple(quaternion),
                                                ideal.position, ideal.orientation, limits), compare))
    return result


def _arc_bound(first, last, arithmetic):
    chord = arithmetic.difference(first, last)
    if chord > Fraction(1, 2):
        _error("OKE-E-QUATERNION-LIFT", "The actual stored endpoints exceed the proved short-arc domain.")
    return arithmetic.div(chord, arithmetic.sub(1, arithmetic.div(arithmetic.square(chord), 4)))


def _stored_arc(raw_first, raw_last, first, last, arithmetic):
    """Independently check the lift and arc for these actual stored endpoints."""
    def calculate():
        dot = arithmetic.total(arithmetic.mul(a, b) for a, b in zip(raw_first, raw_last))
        if dot < 0:
            _error("OKE-E-QUATERNION-LIFT", "Actual stored endpoint signs do not form a coherent short-path lift.")
        return _arc_bound(first, last, arithmetic)
    return arithmetic.reuse(("stored_endpoint_arc", tuple(raw_first), tuple(raw_last), first, last), calculate)


def _source_arc_endpoints_current(raw_first, raw_last, first, last):
    return (first.get("_proof_cap") == last.get("_proof_cap") == MAX_OPERAND_BITS
            and _same_recording_vector(raw_first, first.get("_quaternion_operand"), 4)
            and _same_recording_vector(raw_last, last.get("_quaternion_operand"), 4))


def _previous_source_arc(raw_first, raw_last, first, last, source, limit, arithmetic):
    """Reuse one completed source-arc inequality from the preceding endpoint.

    The old proof uses the same independent speed and interval width and an
    independently computed endpoint-error sum. Fresh actual raw vectors still
    need a nonnegative lift; the new error sum must not exceed the old one.
    The old nonnegative chord at most 1/2 implies its error sum is at most
    1/4, so nonnegative current errors also meet the original individual 1/2
    precondition. No source state or writer bound establishes those facts,
    and no further cache or history is retained.
    """
    receipt = first.get("_source_arc_receipt")
    if (type(receipt) is not tuple or len(receipt) != 5
            or any(type(value) is not Fraction for value in receipt[:4])
            or source[:2] != receipt[:2]
            or not _source_arc_endpoints_current(raw_first, raw_last, first, last)):
        return None
    arithmetic.tick("independent_source_arc_reuse")
    if _bound_domain(arithmetic) != MAX_OPERAND_BITS:
        return None
    raw_first = _recording_vector(raw_first, 4, arithmetic)
    raw_last = _recording_vector(raw_last, 4, arithmetic)
    arithmetic._cache_operand_domain((source, receipt))
    if _bound_domain(arithmetic) != MAX_OPERAND_BITS:
        return None
    dot = _recording_uniform_lift_sign(raw_first, raw_last, arithmetic)
    # Ambiguous signs and other scalar domains keep the exact dot proof in
    # the ordinary calculation below. No lift result is inherited across keys.
    if dot is None:
        return None
    if dot < 0:
        _error("OKE-E-QUATERNION-LIFT", "Actual stored endpoint signs do not form a coherent short-path lift.")
    total_error = arithmetic.add(*source[2:])
    if (_bound_domain(arithmetic) != MAX_OPERAND_BITS
            or arithmetic.compare(total_error, receipt[2]) > 0
            or _bound_domain(arithmetic) != MAX_OPERAND_BITS):
        return None
    if not (type(limit) is type(receipt[4]) and limit == receipt[4]):
        if arithmetic.compare(receipt[3], limit) > 0:
            return None
    if _bound_domain(arithmetic) != MAX_OPERAND_BITS:
        return None
    return (*receipt[:4], limit)


def _certified_stored_arc(raw_first, raw_last, first, last, angular_speed, width, limit, arithmetic,
                          *, source_path_valid=True):
    """A sufficient arc proof from independent endpoints and source path length.

    Exact normalization preserves raw dot-product sign. With a nonnegative dot,
    the stored lift is the short quaternion-sphere lift. The independent ideal
    physical angular-speed bound W gives source arc at most W*h/2. Each proved
    endpoint unit-chord error e <= 1/2 contributes at most 2e in that metric.
    Thus c=W*h/2+2*(e0+e1) bounds the stored chord, and for c<=1/2 the monotone
    envelope c/(1-c*c/4) bounds its actual short arc. No writer bound is used.
    The caller admits this source path only when both endpoints use the same
    retained phase. An outgoing semantic-boundary endpoint instead obtains the
    original normalized-cell proof, as does any insufficient result.
    """
    arithmetic.tick("independent_sufficient_arc_domain")
    raw_first = _recording_vector(raw_first, 4, arithmetic)
    raw_last = _recording_vector(raw_last, 4, arithmetic)
    errors = (first["quaternion_error"], last["quaternion_error"])
    source = (angular_speed, width, *errors)
    arithmetic._cache_operand_domain(source)
    if (_bound_domain(arithmetic) == MAX_OPERAND_BITS
            and _same_recording_vector(raw_first, raw_last, 4)
            and first.get("_proof_cap") == last.get("_proof_cap") == MAX_OPERAND_BITS
            and _same_recording_vector(raw_first, first.get("_quaternion_operand"), 4)
            and _same_recording_vector(raw_last, last.get("_quaternion_operand"), 4)):
        # Each completed current-domain endpoint proof already established
        # that this exact raw operand has a valid nonzero normalization.
        # Identical raw operands denote the identical normalized quaternion,
        # whose literal lift has positive dot and exactly zero arc. This
        # statement needs no source path, including at an outgoing boundary.
        return Fraction(0)
    if (source_path_valid and _bound_domain(arithmetic) == MAX_OPERAND_BITS and _small_proof_values(source)
            and all(value >= 0 for value in source)):
        receipt = _previous_source_arc(raw_first, raw_last, first, last, source, limit, arithmetic)
        if receipt is not None:
            last["_source_arc_receipt"] = receipt
            return receipt[3]
        def calculate():
            if _bound_domain(arithmetic) != MAX_OPERAND_BITS:
                return ()
            dot = _recording_uniform_lift_sign(raw_first, raw_last, arithmetic)
            if dot is None:
                a = tuple(arithmetic.value(value) for value in raw_first)
                b = tuple(arithmetic.value(value) for value in raw_last)
                if not _small_proof_values((*a, *b)):
                    return ()
                dot = arithmetic.total(arithmetic.mul(x, y) for x, y in zip(a, b) if x and y)
            if dot < 0:
                _error("OKE-E-QUATERNION-LIFT", "Actual stored endpoint signs do not form a coherent short-path lift.")
            if any(arithmetic.compare(error, Fraction(1, 2)) > 0 for error in errors):
                return ()
            source_chord = arithmetic.div(arithmetic.mul(angular_speed, width), 2)
            total_error = arithmetic.add(*errors)
            chord = arithmetic.add(source_chord, arithmetic.mul(2, total_error))
            if arithmetic.compare(chord, Fraction(1, 2)) > 0:
                return ()
            return (arithmetic.div(chord, arithmetic.sub(1, arithmetic.div(arithmetic.square(chord), 4))),
                    total_error)
        candidate = arithmetic.reuse(("stored_endpoint_sufficient_arc", raw_first, raw_last, *source), calculate)
        if (candidate and _bound_domain(arithmetic) == MAX_OPERAND_BITS
                and arithmetic.compare(candidate[0], limit) <= 0
                and _bound_domain(arithmetic) == MAX_OPERAND_BITS):
            if _source_arc_endpoints_current(raw_first, raw_last, first, last):
                # The completed nonnegative chord <= 1/2 already proves
                # candidate[1] <= 1/4. No additional scalar inequality is
                # needed to retain that independent error envelope.
                last["_source_arc_receipt"] = (angular_speed, width, candidate[1], candidate[0], limit)
            return candidate[0]
    normalized = []
    for raw, endpoint in ((raw_first, first), (raw_last, last)):
        if endpoint["normalized"] is None or endpoint.get("_normalized_cap") != _bound_domain(arithmetic):
            admitted_cap = _bound_domain(arithmetic)
            value = arithmetic.normalize(raw)
            endpoint["normalized"] = value
            endpoint["_normalized_cap"] = admitted_cap if admitted_cap == _bound_domain(arithmetic) else None
        normalized.append(endpoint["normalized"])
    return _stored_arc(raw_first, raw_last, *normalized, arithmetic)


def _certificate_fraction_fields(value, *, bits=2048):
    """A small native field receipt, without rational arithmetic or callbacks."""
    if type(value) is not Fraction:
        return None
    numerator, denominator = value.numerator, value.denominator
    if (type(numerator) is not int or type(denominator) is not int or denominator <= 0
            or numerator.bit_length() > bits or denominator.bit_length() > bits):
        return None
    return numerator, denominator


def _certificate_raw_fields(record):
    if type(record) is not dict:
        return None
    fields = []
    for name in _NUMERIC_CERTIFICATE_KEYS:
        value = record.get(name)
        if type(value) is int and 0 <= value and value.bit_length() <= 2048:
            fields.append((int, value))
        elif type(value) is float and math.isfinite(value) and value >= 0:
            # Typed binary64 bits also distinguish an altered signed zero.
            fields.append((float, struct.pack(">d", value)))
        else:
            return None
    return tuple(fields)


def _certificate_native_dispatch(batch):
    """Only the original finite comparison/decode dispatch admits omission."""
    arithmetic = batch.arithmetic
    if type(batch) is not _CertificateBatch or type(arithmetic) is not _Bounds or _tick is not _CERTIFICATE_TICK:
        return False
    dispatches = ((arithmetic, _CERTIFICATE_BOUNDS_DISPATCH),
                  (batch, (("maximum", _CERTIFICATE_MAXIMUM),)))
    owner = arithmetic.work
    if owner is not None:
        if type(owner) is not _CertificateWork:
            return False
        dispatches += ((owner, _CERTIFICATE_WORK_DISPATCH),)
    for target, entries in dispatches:
        for name, original in entries:
            method = getattr(target, name, None)
            if type(method) is not MethodType or method.__self__ is not target or method.__func__ is not original:
                return False
    return True


class _CertificateMember:
    """One charged row's native operands; discarded when add() returns.

    The optional proof reads saved native integer fields. Each remaining exact
    maximum has one original comparison callback, followed immediately by a
    check of its actual operands and this row. No callback is replaced, and
    an original callback/resource exception escapes before these checks.
    """
    def __init__(self, batch, record, widths, minima, magnitude):
        self.batch, self.arithmetic = batch, batch.arithmetic
        self.owner, self.owner_type = self.arithmetic.work, type(self.arithmetic.work)
        self.external = getattr(self.owner, "external_check", None)
        self.record, self.raw = record, _certificate_raw_fields(record)
        self.minima, self.names = minima, tuple(minima)
        self.values = (*widths, magnitude, *(minima[name] for name in self.names))
        self.fields = tuple(_certificate_fraction_fields(value) for value in self.values)
        self.enabled = (type(_bound_domain(self.arithmetic)) is int
                        and _bound_domain(self.arithmetic) == MAX_OPERAND_BITS)
        self.thresholds = None

    @classmethod
    def capture(cls, batch, record, width, stored_width, minima, magnitude):
        if (not _certificate_native_dispatch(batch) or type(minima) is not dict
                or len(minima) > len(_NUMERIC_CERTIFICATE_KEYS)
                or any(type(name) is not str or name not in _NUMERIC_CERTIFICATE_KEYS for name in minima)):
            return None
        member = cls(batch, record, (width, stored_width), minima, magnitude)
        return member if member.raw is not None and all(field is not None for field in member.fields) else None

    def current(self):
        if (self.batch.arithmetic is not self.arithmetic
                or self.arithmetic.work is not self.owner or type(self.owner) is not self.owner_type
                or getattr(self.owner, "external_check", None) is not self.external
                or _certificate_raw_fields(self.record) != self.raw
                or type(self.minima) is not dict or len(self.minima) != len(self.names)
                or tuple(self.minima) != self.names
                or any(self.minima[name] is not value for name, value in zip(self.names, self.values[3:]))
                or any(_certificate_fraction_fields(value) != fields
                       for value, fields in zip(self.values, self.fields))):
            _error("OKE-E-INDEPENDENT-VALIDATION", "A certificate member operand or arithmetic owner changed.")
        self.enabled = (self.enabled and type(_bound_domain(self.arithmetic)) is int
                        and _bound_domain(self.arithmetic) == MAX_OPERAND_BITS
                        and _certificate_native_dispatch(self.batch))
        if self.thresholds is not None:
            self.enabled = self.thresholds.current(self.arithmetic) and self.enabled
        return self.enabled

    def checked(self, operation, *args):
        result = operation(*args)
        self.current()
        return result

    def maximum(self, first, last):
        fields = (_certificate_fraction_fields(first), _certificate_fraction_fields(last))
        result = self.batch.maximum(first, last)
        self.current()
        if (all(value is not None for value in fields)
                and (_certificate_fraction_fields(first), _certificate_fraction_fields(last)) != fields):
            _error("OKE-E-INDEPENDENT-VALIDATION", "An exact certificate maximum operand changed.")
        return result


class _CertificateThresholdRestart(Exception):
    """An inconclusive optional continuation needs the complete exact reader."""


class _CertificateThresholds:
    """Sealed reported quantities inside one existing bounded input group.

    These are receipts for already decoded fields, not independent minima or
    another result cache. Every sufficient inequality is proved anew from the
    current member. Only the non-discharged minima need an exact maximum.
    """
    def __init__(self, batch, group, restart):
        arithmetic = batch.arithmetic
        self.batch = batch
        self.arithmetic = arithmetic
        self.restart = restart
        self.group = group
        quantities = group["quantities"]
        self.quantities = quantities
        self.values = tuple(quantities[name] for name in _NUMERIC_CERTIFICATE_KEYS)
        self.fields = tuple(_certificate_fraction_fields(value) for value in self.values)
        self.owner, self.owner_type = arithmetic.work, type(arithmetic.work)
        self.external = getattr(self.owner, "external_check", None)
        self.used = False
        self.enabled = True
        self.domains = {}
        self.minima = group["minima"]
        self.minimum_fields = {name: (value, _certificate_fraction_fields(value, bits=MAX_OPERAND_BITS))
                               for name, value in self.minima.items()}
        self.extent_fields = {name: (group[name], _certificate_fraction_fields(group[name], bits=MAX_OPERAND_BITS))
                              for name in ("width", "stored_width", "magnitude")}

    def current(self, arithmetic):
        if (arithmetic is not self.arithmetic
                or self.batch.arithmetic is not self.arithmetic
                or arithmetic.work is not self.owner or type(self.owner) is not self.owner_type
                or getattr(self.owner, "external_check", None) is not self.external
                or self.group.get("quantities") is not self.quantities
                or self.group.get("minima") is not self.minima
                or type(self.minima) is not dict or len(self.minima) != len(self.minimum_fields)
                or any(self.minima.get(name) is not value
                       or _certificate_fraction_fields(value, bits=MAX_OPERAND_BITS) != fields
                       for name, (value, fields) in self.minimum_fields.items())
                or any(self.group.get(name) is not value
                       or _certificate_fraction_fields(value, bits=MAX_OPERAND_BITS) != fields
                       for name, (value, fields) in self.extent_fields.items())
                or type(self.quantities) is not dict
                or len(self.quantities) != len(_NUMERIC_CERTIFICATE_KEYS)
                or tuple(self.quantities) != _NUMERIC_CERTIFICATE_KEYS
                or any(self.quantities[name] is not value
                       for name, value in zip(_NUMERIC_CERTIFICATE_KEYS, self.values))
                or any(_certificate_fraction_fields(value) != fields
                       for value, fields in zip(self.values, self.fields))):
            _error("OKE-E-INDEPENDENT-VALIDATION", "A reported certificate threshold or its owner changed.")
        self.enabled = self.enabled and _certificate_native_dispatch(self.batch)
        if not self.enabled and self.used:
            self.restart()
        return self.enabled

    def sufficient(self, name, first, last, arithmetic, member):
        if not member.current():
            return False
        previous, fresh = _certificate_fraction_fields(first), _certificate_fraction_fields(last)
        actual = self.quantities[name]
        claim = _certificate_fraction_fields(actual)
        if previous is None or fresh is None or claim is None:
            return False
        an, ad = previous
        bn, bd = fresh
        qn, qd = claim
        if an < 0 or bn < 0 or qn <= 0 or qd.bit_count() != 1:
            return False
        # The omitted old/fresh maximum must fit its complete original
        # prospective comparison domain, not merely each scalar separately.
        # Admit the direct fresh/claim comparison too. All domains are smaller
        # than the unchanged 32,768-bit cap; narrower requests keep the exact
        # path. guard_bits itself does not replace a cancellation checkpoint.
        arithmetic.bits(an.bit_length(), ad.bit_length(), bn.bit_length(), bd.bit_length(),
                        qn.bit_length(), qd.bit_length(), an.bit_length() + bd.bit_length(),
                        bn.bit_length() + ad.bit_length(), qn.bit_length() + bd.bit_length(),
                        bn.bit_length() + qd.bit_length())
        if (not member.current() or _certificate_fraction_fields(first) != previous
                or _certificate_fraction_fields(last) != fresh
                or _certificate_fraction_fields(actual) != claim):
            return False
        # q is a positive exact binary64/integer decode. Its denominator is a
        # power of two, so q >= 2**(bits(qn)-bits(qd)). For positive m,
        # m < 2**(bits(bn)-bits(bd)+1). Comparing exponents proves m < q
        # without allocating either power or any rational cross product.
        proved = not bn or bn.bit_length() - bd.bit_length() + 1 <= qn.bit_length() - qd.bit_length()
        if proved:
            if name not in self.domains:
                self.domains[name] = (0, 1, 0, 1)
                self.observe_continuation(name, first)
            self.observe_continuation(name, last)
        self.used = self.used or proved
        return proved

    def admit_continuation(self, name, value, arithmetic, *, will_compare=True,
                           compared=False, equality_shortcut=True):
        """Retain every discarded operand's possible future comparison width.

        The original running maximum is either the retained exact maximum or
        one previously discharged member. An envelope of native field widths
        covers every such member without retaining its numeric value. This
        check also runs on wider/unsupported incoming members and at flush.
        Lower widths establish definite original failures; an inconclusive
        upper envelope requests complete exact replay on the same work.
        """
        if name not in self.domains:
            return
        self.current(arithmetic)
        if (type(value) is not Fraction or type(value.numerator) is not int
                or type(value.denominator) is not int or value.denominator <= 0):
            self.restart()
        numerator, denominator = value.numerator.bit_length(), value.denominator.bit_length()
        low_n, low_d, high_n, high_d = self.domains[name]
        limit = _bound_domain(arithmetic)
        if type(limit) is not int:
            self.restart()
        limit = min(limit, MAX_OPERAND_BITS)
        upper = max(numerator, denominator, high_n, high_d, high_n + denominator,
                    numerator + high_d)
        if upper <= limit:
            return
        # maximum() skips all guards for exact equality. Width metadata can
        # exclude equality, but cannot establish a different actual value
        # when both fields lie inside its envelope. Replay those cases; flush
        # always compares and therefore has no equality exception.
        equality_possible = (equality_shortcut and value.numerator > 0
                             and low_n <= numerator <= high_n and low_d <= denominator <= high_d)
        lower_fields = max(numerator, denominator, low_n, low_d)
        lower_products = max(low_n + denominator, numerator + low_d)
        if equality_possible or max(lower_fields, lower_products) <= limit:
            self.restart()
        # A definite original scalar failure precedes its callback. A
        # prospective product failure follows that callback, which must keep
        # its exception identity and opportunity to change the live domain.
        if compared:
            arithmetic.bits(low_n + denominator, numerator + low_d)
        else:
            arithmetic.bits(numerator, denominator, low_n, low_d)
            self.current(arithmetic)
            if not will_compare:
                self.restart()

    def observe_continuation(self, name, value):
        if name not in self.domains or value.numerator <= 0:
            return
        numerator, denominator = value.numerator.bit_length(), value.denominator.bit_length()
        low_n, low_d, high_n, high_d = self.domains[name]
        # Once a positive value occurs, zero cannot be an original maximum.
        # This makes a single discarded positive maximum's width obligation
        # exact without retaining its numeric value or another result cache.
        if not high_n:
            self.domains[name] = (numerator, denominator, numerator, denominator)
        else:
            self.domains[name] = (min(low_n, numerator), min(low_d, denominator),
                                  max(high_n, numerator), max(high_d, denominator))

    def retain(self, name, value):
        self.minimum_fields[name] = (value, _certificate_fraction_fields(value, bits=MAX_OPERAND_BITS))

    def retain_extent(self, name, value):
        self.extent_fields[name] = (value, _certificate_fraction_fields(value, bits=MAX_OPERAND_BITS))

    def copied_quantities(self, arithmetic):
        self.current(arithmetic)
        # Detach the complete algebra from mutable Fraction aliases held in
        # the group. The retained integer receipts still bind final admission
        # to the originally decoded actual reported quantities.
        return dict(zip(_NUMERIC_CERTIFICATE_KEYS,
                        (Fraction(numerator, denominator) for numerator, denominator in self.fields)))

    def copied_extents(self, arithmetic):
        self.current(arithmetic)
        result = {}
        for name, (_, fields) in self.extent_fields.items():
            if fields is None:
                self.restart()
            result[name] = Fraction(*fields)
        return result


class _CertificateBatch:
    """Check identical supplied quantities against every member's exact bounds.

    This is bounded input aggregation, separate from the shared numeric cache:
    at most 64 groups are retained and then discharged. Every actual row still
    supplies its independently calculated minima, widths and magnitude. A
    sufficient proof can discharge a fresh minimum against the actual reported
    quantity; the remaining minima retain their exact maxima. Width, stored
    width and magnitude always retain exact maxima for the complete nonlinear
    inequalities. No writer group is consulted.
    """
    MAX_GROUPS = 64

    def __init__(self, arithmetic, position_tolerance, rotation_tolerance, *, thresholds=True):
        self.arithmetic = arithmetic
        self.position_tolerance = arithmetic.value(position_tolerance)
        position_fields = _certificate_fraction_fields(self.position_tolerance, bits=MAX_OPERAND_BITS)
        self.rotation_tolerance = arithmetic.value(rotation_tolerance)
        self.groups = {}
        self.max_position = self.max_rotation = Fraction(0)
        self.thresholds_enabled = thresholds
        self.restart = _CertificateThresholdRestart("A certificate continuation needs exact maxima.")
        self.restart_requested = False
        self._threshold_arithmetic = arithmetic
        self._threshold_work = arithmetic.work
        self._threshold_external = getattr(arithmetic.work, "external_check", None)
        self._threshold_tolerances = (self.position_tolerance, self.rotation_tolerance)
        self._threshold_tolerance_fields = (position_fields,
            _certificate_fraction_fields(self.rotation_tolerance, bits=MAX_OPERAND_BITS))

    def _restart_thresholds(self):
        self.restart_requested = True
        raise self.restart

    def _prepare_exact_replay(self):
        # Keep actual instance dispatch and the already decoded tolerances.
        # Replacing these owners during replay could hide a changed-operation
        # exception or silently recapture different mutable option inputs.
        if (self.arithmetic is not self._threshold_arithmetic
                or self.arithmetic.work is not self._threshold_work
                or getattr(self._threshold_work, "external_check", None) is not self._threshold_external
                or self.position_tolerance is not self._threshold_tolerances[0]
                or self.rotation_tolerance is not self._threshold_tolerances[1]
                or any(_certificate_fraction_fields(value, bits=MAX_OPERAND_BITS) != fields
                       for value, fields in zip(self._threshold_tolerances, self._threshold_tolerance_fields))):
            _error("OKE-E-INDEPENDENT-VALIDATION", "A certificate replay owner or admitted tolerance changed.")
        for value in self._threshold_tolerances:
            self.arithmetic.bits(value.numerator.bit_length(), value.denominator.bit_length())
        self.groups.clear()
        self.max_position = self.max_rotation = Fraction(0)
        self.thresholds_enabled = self.restart_requested = False

    def maximum(self, first, last):
        # Equality of reduced fractions compares their integer components and
        # does not need cross products. A changed value keeps guarded rational
        # comparison and its original request/cancellation charge.
        if first == last:
            return first
        return first if self.arithmetic.compare(first, last) >= 0 else last

    def add(self, record, width, stored_width, minima, magnitude):
        arithmetic = self.arithmetic
        member = (_CertificateMember.capture(self, record, width, stored_width, minima, magnitude)
                  if self.thresholds_enabled else None)
        arithmetic.tick("independent_certificate_member")
        if member is not None:
            member.current()
        if width <= 0 or stored_width <= 0:
            _error("OKE-E-CERTIFICATE", "Every interval certificate requires positive authored and stored widths.")
        values = []
        for name in _NUMERIC_CERTIFICATE_KEYS:
            value = record.get(name)
            if type(value) not in (int, float) or (type(value) is float and not math.isfinite(value)) or value < 0:
                _error("OKE-E-CERTIFICATE", "A certificate quantity must be a finite nonnegative number.",
                       details={"quantity": name})
            if type(value) is int:
                arithmetic.bits(value.bit_length())
            values.append(value)
        key = tuple(values)
        group = self.groups.get(key)
        if group is None:
            if len(self.groups) >= self.MAX_GROUPS:
                self.flush()
            arithmetic.tick("independent_certificate_group")
            if member is not None:
                member.current()
            decodes = _CertificateFieldDecodes.create(arithmetic, key)
            quantities = dict(zip(_NUMERIC_CERTIFICATE_KEYS,
                                  (member.checked(arithmetic.value if decodes is None else decodes.value, value)
                                   if member is not None else
                                   arithmetic.value(value) if decodes is None else decodes.value(value)
                                   for value in key)))
            group = {"quantities": quantities, "minima": dict(minima),
                     "width": width, "stored_width": stored_width, "magnitude": magnitude}
            if member is not None and member.enabled:
                thresholds = _CertificateThresholds(self, group, self._restart_thresholds)
                if all(fields is not None for fields in thresholds.fields):
                    group["thresholds"] = thresholds
            self.groups[key] = group
        else:
            thresholds = group.get("thresholds")
            if thresholds is not None and group["quantities"] is not thresholds.quantities:
                _error("OKE-E-INDEPENDENT-VALIDATION", "A certificate group's reported quantities changed.")
            if thresholds is not None:
                thresholds.current(arithmetic)
            if member is not None:
                member.thresholds = thresholds
                member.current()
            maximum = member.maximum if member is not None else self.maximum
            for name, fresh in (("width", width), ("stored_width", stored_width), ("magnitude", magnitude)):
                group[name] = maximum(group[name], fresh)
                if thresholds is not None:
                    thresholds.retain_extent(name, group[name])
            for name, minimum in minima.items():
                previous = group["minima"][name]
                different = previous != minimum
                if thresholds is not None:
                    thresholds.admit_continuation(name, minimum, arithmetic, will_compare=different)
                if (thresholds is not None and member is not None and different
                        and thresholds.sufficient(name, previous, minimum, arithmetic, member)):
                    continue
                value = maximum(previous, minimum)
                if thresholds is not None:
                    thresholds.admit_continuation(name, minimum, arithmetic,
                                                  will_compare=different, compared=different)
                    thresholds.observe_continuation(name, minimum)
                group["minima"][name] = value
                if thresholds is not None:
                    thresholds.retain(name, value)

    def flush(self):
        arithmetic = self.arithmetic
        for group in self.groups.values():
            arithmetic.tick("independent_certificate_group_check")
            thresholds = group.get("thresholds")
            if thresholds is not None and group["quantities"] is not thresholds.quantities:
                _error("OKE-E-INDEPENDENT-VALIDATION", "A certificate group's reported quantities changed.")
            if thresholds is not None:
                thresholds.current(arithmetic)
            quantities = (thresholds.copied_quantities(arithmetic) if thresholds is not None and thresholds.used
                          else group["quantities"])
            extents = thresholds.copied_extents(arithmetic) if thresholds is not None and thresholds.used else group
            comparisons = _CertificateFieldComparisons.create(arithmetic)
            def require(name, minimum):
                actual = quantities[name]
                if thresholds is not None:
                    thresholds.admit_continuation(name, actual, arithmetic, equality_shortcut=False)
                relation = (arithmetic.compare(actual, minimum) if comparisons is None
                            else comparisons.compare(actual, minimum))
                if thresholds is not None:
                    thresholds.current(arithmetic)
                    thresholds.admit_continuation(name, actual, arithmetic,
                                                  compared=True, equality_shortcut=False)
                if relation < 0:
                    _error("OKE-E-CERTIFICATE", "A reported certificate quantity understates an independently derived bound.",
                           details={"quantity": name})
                return actual
            for name, minimum in group["minima"].items():
                require(name, minimum)
            domain = arithmetic.total((extents["magnitude"], quantities["landmark_radius_m"],
                                       quantities["local_vertex_error_bound_m"]))
            if domain > 1 << 400:
                _error("OKE-E-DESTINATION-NUMERIC-BASIS", "The source and stored geometry exceed the identified destination's magnitude domain.")
            require("destination_numeric_position_bound_m", arithmetic.div(arithmetic.add(domain, 1), 1 << 38))
            require("destination_numeric_rotation_bound_rad", arithmetic.add(
                arithmetic.square(quantities["stored_quaternion_arc_upper_rad"]), Fraction(1, 1 << 44)))
            arguments = (extents["width"], extents["stored_width"], quantities,
                         self.position_tolerance, self.rotation_tolerance, arithmetic, None)
            if (_complete_inequality_values is _FIELD_COMPLETE_ALGEBRA
                    and _complete_inequality_values.__code__ is _FIELD_COMPLETE_CODE):
                totals = _complete_inequality_values(*arguments, field_comparisons=comparisons)
            else:
                # A replaced algebra function retains its original positional
                # interface and gets no optional context it did not request.
                totals = _complete_inequality_values(*arguments)
            if thresholds is not None:
                thresholds.current(arithmetic)
            self.max_position = self.maximum(self.max_position, totals["position_bound_m"])
            self.max_rotation = self.maximum(self.max_rotation, totals["rotation_bound_rad"])
        self.groups.clear()


_CERTIFICATE_TICK = _tick
_CERTIFICATE_BOUNDS_DISPATCH = tuple((name, getattr(_Bounds, name))
                                   for name in ("compare", "bits", "value", "tick"))
_CERTIFICATE_WORK_DISPATCH = tuple((name, getattr(_CertificateWork, name))
                                 for name in ("charge", "guard_bits"))
_CERTIFICATE_MAXIMUM = _CertificateBatch.maximum
_FIELD_COMPLETE_ALGEBRA = _complete_inequality_values
_FIELD_COMPLETE_CODE = _complete_inequality_values.__code__


# This optional local reuse admits only scalar paths with no foreign callback.
# A native construction budget still receives every performed work charge.
from . import construction as _term_construction
from . import reach_numeric as _term_numeric
import fractions as _term_fractions
import sys as _term_sys
import abc as _term_abc
import numbers as _term_numbers
from types import FunctionType as _TermFunction, ModuleType as _TermModule


_TERM_ABSENT = object()
_TERM_STORAGE = ("__getattribute__", "__getattr__", "__setattr__", "__delattr__", "__dict__")
_TERM_BOUNDS_METHODS = ("add", "mul", "div", "square", "op", "bits", "tick", "value", "compare", "total",
                        "_cache_operand_domain")
_TERM_WORK_METHODS = ("charge", "guard_bits", "resource")
_TERM_BUDGET_METHODS = ("tick", "exceeded")
_TERM_CLASS_FIELDS = tuple((kind, tuple((name, type.__getattribute__(kind, "__dict__").get(name, _TERM_ABSENT))
    for name in dict.fromkeys((*_TERM_STORAGE, *names)))) for kind, names in (
        (_Bounds, (*_TERM_BOUNDS_METHODS, "work")),
        (_CertificateWork, (*_TERM_WORK_METHODS, "external_check", "_source_after_charge", "counts",
            "operations", "max_operations", "max_operand_bits", "max_elapsed_ms", "started")),
        (_term_construction.ConstructionBudget, (*_TERM_BUDGET_METHODS, "check", "operations", "limits", "started")),
        (Fraction, ("__new__", "__init__", "__mul__", "__truediv__", "_mul", "_div", "_from_coprime_ints",
            "__add__", "_add", "__bool__", "__eq__", "__lt__", "__gt__", "__le__", "__ge__", "_richcmp",
            "numerator", "denominator", "_numerator", "_denominator")),
        (_term_abc.ABCMeta, ("__instancecheck__", "__subclasscheck__")),
        (_term_numbers.Rational, ("__subclasshook__",)),
        (_term_numbers.Real, ("__subclasshook__",)),
        (_term_numbers.Complex, ("__subclasshook__",)),
        (_term_numbers.Number, ("__subclasshook__",))))


def _term_functions():
    # Native arithmetic forwarders retain the monomorphic function in a
    # closure. Its object and code are part of admission, not just __mul__.
    functions = [_tick, _bound_domain, _certificate_fraction_fields, _small_proof_values]
    for kind, fields in _TERM_CLASS_FIELDS:
        for _, member in fields:
            if type(member) in (classmethod, staticmethod):
                member = member.__func__
            elif type(member) is property:
                member = member.fget
            if type(member) is _TermFunction:
                functions.append(member)
                if member.__closure__ is not None:
                    functions.extend(cell.cell_contents for cell in member.__closure__
                                     if type(cell.cell_contents) is _TermFunction)
    return tuple(dict.fromkeys(functions))


def _term_function_state(function):
    namespace = function.__globals__
    builtins = function.__builtins__
    return (function.__code__, function.__defaults__, function.__kwdefaults__,
            tuple((function.__kwdefaults__ or {}).items()),
            tuple(cell.cell_contents for cell in function.__closure__ or ()),
            tuple((name, namespace.get(name, _TERM_ABSENT), builtins.get(name, _TERM_ABSENT))
                  for name in function.__code__.co_names))


_TERM_FUNCTIONS = tuple((function, _term_function_state(function)) for function in _term_functions())
_TERM_FIELD_READER = _certificate_fraction_fields
_TERM_GLOBALS = ((_term_numeric, "monotonic", _term_numeric.monotonic),
                 (_term_construction, "time", _term_construction.time),
                 (_term_construction.time, "monotonic", _term_construction.time.monotonic),
                 (_term_fractions, "Fraction", Fraction), (_term_fractions, "math", math),
                 (_term_fractions, "numbers", _term_numbers),
                 (_term_numbers, "Rational", _term_numbers.Rational),
                 (_term_numbers, "Real", _term_numbers.Real),
                 (_term_numbers, "Complex", _term_numbers.Complex),
                 (_term_numbers, "Number", _term_numbers.Number),
                 (math, "gcd", math.gcd),
                 (_term_sys, "getprofile", _term_sys.getprofile), (_term_sys, "gettrace", _term_sys.gettrace))


def _certificate_term_native(arithmetic):
    """Admit only original scalar dispatch and a native, non-reentrant budget.

    Custom callbacks and preexisting observers take the untouched calculation.
    This does not replace, wrap or clear either callback. Class descriptors
    are checked before reading potentially overridden instance properties.
    """
    if type(arithmetic) is not _Bounds or _certificate_fraction_fields is not _TERM_FIELD_READER:
        return False
    if any(type.__getattribute__(kind, "__dict__").get(name, _TERM_ABSENT) is not saved
           for kind, fields in _TERM_CLASS_FIELDS for name, saved in fields):
        return False
    if any(type(module) is not _TermModule
           or _TermModule.__getattribute__(module, "__dict__").get(name, _TERM_ABSENT) is not saved
           for module, name, saved in _TERM_GLOBALS):
        return False
    if _term_sys.gettrace() is not None or _term_sys.getprofile() is not None:
        return False
    for function, (code, defaults, kwdefaults, kwfields, closure, globals_) in _TERM_FUNCTIONS:
        if (function.__code__ is not code or function.__defaults__ is not defaults
                or function.__kwdefaults__ is not kwdefaults
                or len(function.__kwdefaults__ or {}) != len(kwfields)
                or any(type(name) is not str or name != saved_name or value is not saved
                       for (name, value), (saved_name, saved) in zip(
                           (function.__kwdefaults__ or {}).items(), kwfields))
                or len(function.__closure__ or ()) != len(closure)
                or any(cell.cell_contents is not saved
                       for cell, saved in zip(function.__closure__ or (), closure))
                or any(function.__globals__.get(name, _TERM_ABSENT) is not saved
                       or function.__builtins__.get(name, _TERM_ABSENT) is not builtin
                       for name, saved, builtin in globals_)):
            return False
    own = object.__getattribute__(arithmetic, "__dict__")
    if any(name in own for name in _TERM_BOUNDS_METHODS):
        return False
    owner = own.get("work")
    if owner is None:
        return True
    if type(owner) is not _CertificateWork:
        return False
    state = object.__getattribute__(owner, "__dict__")
    if (any(name in state for name in _TERM_WORK_METHODS)
            or state.get("_source_after_charge") is not None
            or type(state.get("max_operand_bits")) is not int or state["max_operand_bits"] != MAX_OPERAND_BITS
            or any(type(state.get(name)) is not int or state[name] < 0
                   for name in ("operations", "max_operations", "max_elapsed_ms"))
            or type(state.get("started")) is not float
            # This bounds inspection of diagnostic categories only. It does
            # not change the separate 256-entry numerical cache maximum.
            or type(state.get("counts")) is not dict or len(state["counts"]) > 512
            or any(type(name) is not str or type(value) is not int
                   for name, value in state["counts"].items())):
        return False
    callback = state.get("external_check")
    if callback is None:
        return True
    if (type(callback) is not MethodType or callback.__func__ is not _term_construction.ConstructionBudget.tick
            or type(callback.__self__) is not _term_construction.ConstructionBudget):
        return False
    budget = object.__getattribute__(callback.__self__, "__dict__")
    return (not any(name in budget for name in _TERM_BUDGET_METHODS)
            and budget.get("check") is None and type(budget.get("operations")) is int
            and type(budget.get("started")) is float and type(budget.get("limits")) is dict
            and len(budget["limits"]) == 5
            and all(type(name) is str and type(value) is int and value > 0
                    for name, value in budget["limits"].items())
            and "max_operations" in budget["limits"] and "max_elapsed_ms" in budget["limits"])


def _certificate_field_key(value):
    """Native input identity, retaining signed zero and integer/float type."""
    if type(value) is int and 0 <= value and value.bit_length() <= 2048:
        return int, value
    if type(value) is float and math.isfinite(value) and value >= 0:
        return float, struct.pack(">d", value)
    return None


_FIELD_TERM_NATIVE = _certificate_term_native
_FIELD_RAW_READER = _certificate_raw_fields
_FIELD_KEY_READER = _certificate_field_key
_FIELD_FUNCTIONS = tuple((function, _term_function_state(function)) for function in
    (_certificate_term_native, _certificate_raw_fields, _certificate_field_key, _term_function_state))
_FIELD_GLOBALS = ((math, "isfinite", math.isfinite), (struct, "pack", struct.pack))
_FIELD_FRACTION_CLASS = Fraction
_FIELD_NATIVE_TYPE, _FIELD_NATIVE_INT = type, int
_FIELD_CLASS_READ, _FIELD_SLOT_READ = type.__getattribute__, object.__getattribute__
_FIELD_GETTRACE, _FIELD_GETPROFILE = _term_sys.gettrace, _term_sys.getprofile
_FIELD_FRACTION_ACCESS = tuple((name, saved) for kind, fields in _TERM_CLASS_FIELDS
    if kind is Fraction for name, saved in fields
    if name in (*_TERM_STORAGE, "numerator", "denominator", "_numerator", "_denominator"))


def _certificate_fields_native(arithmetic):
    """Strengthen scalar admission for the newly omitted decode paths."""
    if (_certificate_term_native is not _FIELD_TERM_NATIVE
            or _certificate_raw_fields is not _FIELD_RAW_READER
            or _certificate_field_key is not _FIELD_KEY_READER):
        return False
    if any(type(module) is not _TermModule
           or _TermModule.__getattribute__(module, "__dict__").get(name, _TERM_ABSENT) is not saved
           for module, name, saved in _FIELD_GLOBALS):
        return False
    for function, (code, defaults, kwdefaults, kwfields, closure, globals_) in _FIELD_FUNCTIONS:
        if (function.__code__ is not code or function.__defaults__ is not defaults
                or function.__kwdefaults__ is not kwdefaults
                or len(function.__kwdefaults__ or {}) != len(kwfields)
                or any(type(name) is not str or name != saved_name or value is not saved
                       for (name, value), (saved_name, saved) in zip(
                           (function.__kwdefaults__ or {}).items(), kwfields))
                or len(function.__closure__ or ()) != len(closure)
                or any(cell.cell_contents is not saved
                       for cell, saved in zip(function.__closure__ or (), closure))
                or any(function.__globals__.get(name, _TERM_ABSENT) is not saved
                       or function.__builtins__.get(name, _TERM_ABSENT) is not builtin
                       for name, saved, builtin in globals_)):
            return False
    return _certificate_term_native(arithmetic)


class _CertificateFieldDecodes:
    """Completed input decodes retained only while constructing one group."""
    @classmethod
    def create(cls, arithmetic, values):
        if (not _certificate_fields_native(arithmetic) or type(values) is not tuple
                or not 1 <= len(values) <= len(_NUMERIC_CERTIFICATE_KEYS)):
            return None
        keys = tuple(_certificate_field_key(value) for value in values)
        if any(key is None for key in keys) or len(set(keys)) == len(keys):
            return None
        return cls(arithmetic, values, keys)

    def __init__(self, arithmetic, values, keys):
        self.arithmetic, self.owner = arithmetic, arithmetic.work
        self.external = getattr(self.owner, "external_check", None)
        self.values, self.keys = values, keys
        self.repeated = frozenset(key for key in keys if keys.count(key) > 1)
        self.index = 0
        self.results = {}
        self._completed = ()
        self.valid, self.admitted = True, False

    def current(self):
        self.valid = (self.valid and _certificate_fields_native(self.arithmetic)
            and self.arithmetic.work is self.owner
            and getattr(self.owner, "external_check", None) is self.external)
        return self.valid

    def value(self, value):
        arithmetic = self.arithmetic
        index = self.index
        self.index += 1
        # A field with no later typed match cannot supply reuse. Preserve its
        # ordinary dynamic decode without an unnecessary native-state scan.
        if index < len(self.keys) and self.keys[index] not in self.repeated:
            return arithmetic.value(value)
        if not self.current():
            return arithmetic.value(value)
        key = _certificate_field_key(value)
        if index >= len(self.keys) or key is None or key != self.keys[index]:
            self.valid = False
            return arithmetic.value(value)
        receipt = self.results.get(key)
        if receipt is None:
            # The native gate ran before the original decode. A foreign path
            # that restores itself during the call cannot supply a receipt.
            result = arithmetic.value(value)
            if self.current():
                fields = _certificate_fraction_fields(result)
                if fields is not None:
                    receipt = (value, result, fields)
                    self.results[key] = receipt
                    self._completed += ((key, receipt),)
            return result

        def current_fields(*, check_native=True):
            if ((check_native and not self.current()) or type(receipt) is not tuple or len(receipt) != 3
                    or self.results.get(key) is not receipt
                    or not any(saved_key == key and saved_receipt is receipt
                               for saved_key, saved_receipt in self._completed)):
                return None
            original, result, saved = receipt
            if (type(saved) is not tuple or len(saved) != 2
                    or any(type(field) is not int for field in saved)
                    or _certificate_field_key(original) != key
                    or _certificate_field_key(value) != key
                    or _certificate_fraction_fields(result) != saved):
                self.valid = False
                return None
            return saved

        # Only pinned pure native key/receipt reads have occurred since the
        # entry gate. Repeat the full gate after the actual admission below.
        fields = current_fields(check_native=False)
        if fields is None:
            return arithmetic.value(value)
        if not self.admitted:
            arithmetic.tick("independent_certificate_decode_admission")
            self.admitted = True
            if current_fields() != fields:
                return arithmetic.value(value)
        if type(value) is int:
            arithmetic.bits(value.bit_length())
        arithmetic.bits(fields[0].bit_length(), fields[1].bit_length())
        # Copy the already completed exact decode, without reduction or an
        # alias to a prior reported field. No result survives this group.
        result = object.__new__(Fraction)
        object.__setattr__(result, "_numerator", fields[0])
        object.__setattr__(result, "_denominator", fields[1])
        return result


class _CertificateFieldComparisons:
    """Fresh equal-field proofs sharing one actual admission within a group."""
    @classmethod
    def create(cls, arithmetic):
        if not _certificate_fields_native(arithmetic):
            return None
        return cls(arithmetic)

    def __init__(self, arithmetic):
        self.arithmetic, self.owner = arithmetic, arithmetic.work
        self.external = getattr(self.owner, "external_check", None)
        self.valid, self.admitted = True, False

    def current(self):
        self.valid = (self.valid and _certificate_fields_native(self.arithmetic)
            and self.arithmetic.work is self.owner
            and getattr(self.owner, "external_check", None) is self.external)
        return self.valid

    def compare(self, actual, minimum):
        arithmetic = self.arithmetic
        # Hooks installed after context creation must reach ordinary dispatch
        # before optional slot reads can expose a new observable event.
        if _FIELD_GETTRACE() is not None or _FIELD_GETPROFILE() is not None:
            return arithmetic.compare(actual, minimum)
        # This filter only declines work; it cannot establish a claim. Check
        # native access descriptors before bounded native slot reads, without
        # invoking a possibly replaced public property or module field reader.
        if (Fraction is not _FIELD_FRACTION_CLASS or _FIELD_NATIVE_TYPE(actual) is not _FIELD_FRACTION_CLASS
                or _FIELD_NATIVE_TYPE(minimum) is not _FIELD_FRACTION_CLASS):
            return arithmetic.compare(actual, minimum)
        for name, saved in _FIELD_FRACTION_ACCESS:
            if _FIELD_CLASS_READ(_FIELD_FRACTION_CLASS, "__dict__").get(name, _TERM_ABSENT) is not saved:
                return arithmetic.compare(actual, minimum)
        try:
            rn, rd = _FIELD_SLOT_READ(actual, "_numerator"), _FIELD_SLOT_READ(actual, "_denominator")
            mn, md = _FIELD_SLOT_READ(minimum, "_numerator"), _FIELD_SLOT_READ(minimum, "_denominator")
        except AttributeError:
            return arithmetic.compare(actual, minimum)
        if (_FIELD_NATIVE_TYPE(rn) is not _FIELD_NATIVE_INT or _FIELD_NATIVE_TYPE(rd) is not _FIELD_NATIVE_INT
                or _FIELD_NATIVE_TYPE(mn) is not _FIELD_NATIVE_INT or _FIELD_NATIVE_TYPE(md) is not _FIELD_NATIVE_INT
                or rd <= 0 or md <= 0 or rn.bit_length() > 2048 or rd.bit_length() > 2048
                or mn.bit_length() > 2048 or md.bit_length() > 2048 or (rn, rd) != (mn, md)):
            return arithmetic.compare(actual, minimum)
        # Potential equality still needs the full gate and fresh original
        # field reads. No result from the early filter admits an omission.
        if not self.current():
            return arithmetic.compare(actual, minimum)
        left, right = _certificate_fraction_fields(actual), _certificate_fraction_fields(minimum)
        if left is None or right is None or left != right:
            return arithmetic.compare(actual, minimum)
        an, ad, bn, bd = (left[0].bit_length(), left[1].bit_length(),
                          right[0].bit_length(), right[1].bit_length())
        arithmetic.bits(an, ad, bn, bd)
        if not self.admitted:
            arithmetic.tick("independent_certificate_compare_admission")
            self.admitted = True
            if (not self.current() or _certificate_fraction_fields(actual) != left
                    or _certificate_fraction_fields(minimum) != right):
                return arithmetic.compare(actual, minimum)
        # Equality does not waive the original prospective cross products.
        arithmetic.bits(an + bd, bn + ad)
        return 0


class _CertificateTermReuse:
    """Six completed scalar operations, retained only within one invocation."""
    @classmethod
    def create(cls, arithmetic, quantities, operands):
        if (not _certificate_term_native(arithmetic) or type(quantities) is not dict
                or len(quantities) != len(_NUMERIC_CERTIFICATE_KEYS)
                or any(type(name) is not str for name in quantities)
                or set(quantities) != set(_NUMERIC_CERTIFICATE_KEYS)
                or any(_certificate_fraction_fields(value) is None
                       for value in (*operands, *quantities.values()))):
            return None
        return cls(arithmetic, operands)

    def __init__(self, arithmetic, operands):
        self.arithmetic, self.owner = arithmetic, arithmetic.work
        self.external = getattr(self.owner, "external_check", None)
        self.operands, self.fields = operands, tuple(_certificate_fraction_fields(value) for value in operands)
        self.results = {}
        self.valid, self.admitted = True, False
        self.zero_coefficients = None

    def current(self):
        self.valid = (self.valid and _certificate_term_native(self.arithmetic)
            and self.arithmetic.work is self.owner
            and getattr(self.owner, "external_check", None) is self.external
            and tuple(_certificate_fraction_fields(value) for value in self.operands) == self.fields)
        return self.valid

    def calculate(self, name, operation, *args):
        before = self.current()
        fields = tuple(_certificate_fraction_fields(value, bits=8195) for value in args) if before else ()
        result = operation(*args)
        # An original scalar/callback/resource exception escapes untouched.
        if (before and self.current() and all(value is not None for value in fields)
                and fields == tuple(_certificate_fraction_fields(value, bits=8195) for value in args)):
            result_fields = _certificate_fraction_fields(result, bits=8195)
            if result_fields is not None:
                self.results[name] = (args, fields, result, result_fields)
        return result

    def borrow(self, *names):
        if not self.current() or any(name not in self.results for name in names):
            return None
        records = tuple(self.results[name] for name in names)
        for operands, fields, result, result_fields in records:
            if (tuple(_certificate_fraction_fields(value, bits=8195) for value in operands) != fields
                    or _certificate_fraction_fields(result, bits=8195) != result_fields):
                self.valid = False
                return None
        if not self.admitted:
            # If no earlier zero omission admitted the proof, charge here
            # after both mandatory quarter plans retain their failure order.
            self.arithmetic.tick("independent_certificate_term_admission")
            self.admitted = True
            if not self.current():
                return None
        for name, (operands, fields, result, result_fields) in zip(names, records):
            first, last = (fields[0], fields[0]) if len(fields) == 1 else fields
            an, ad, bn, bd = first[0].bit_length(), first[1].bit_length(), last[0].bit_length(), last[1].bit_length()
            # The operation names describe original mul/square or div guards.
            divide = name in ("rotation", "chord")
            self.arithmetic.bits(an, ad, bn, bd, an + (bd if divide else bn),
                                 ad + (bn if divide else bd),
                                 result_fields[0].bit_length(), result_fields[1].bit_length())
        # Copy already admitted native integer fields without new reduction or
        # numerical arithmetic. The caller receives its own result objects.
        copies = []
        for _, _, _, fields in records:
            value = object.__new__(Fraction)
            object.__setattr__(value, "_numerator", fields[0])
            object.__setattr__(value, "_denominator", fields[1])
            copies.append(value)
        return tuple(copies)

    def zero_quarter(self, angular, acceleration, envelope_angular, envelope_acceleration):
        """Admit the separate all-four-zero identity for the stored quarter.

        Saved primitive fields cheaply reject ordinary nonzero groups. The
        enclosing coefficients are the original local objects, not fresh
        dictionary reads that could change the calculation's binding order.
        """
        if self.fields[2:4] != ((0, 1), (0, 1)) or not self.current():
            return False
        coefficients = (angular, acceleration, envelope_angular, envelope_acceleration)
        if any(_certificate_fraction_fields(value) != (0, 1) for value in coefficients):
            return False
        for name in ("angle", "angle_squared", "rotation", "product", "chord"):
            record = self.results.get(name)
            if record is None or record[3] != (0, 1):
                return False
            operands, fields, result, result_fields = record
            if (tuple(_certificate_fraction_fields(value, bits=8195) for value in operands) != fields
                    or _certificate_fraction_fields(result, bits=8195) != result_fields):
                self.valid = False
                return False
        self.zero_coefficients = coefficients
        return True

    def zero(self, name, operation, first, last):
        """Copy a completed zero after guarding this actual omitted operation."""
        expected = {"angle": "mul", "angle_squared": "mul", "rotation": "div",
                    "product": "mul", "chord": "div"}
        if expected.get(name) != operation or self.zero_coefficients is None:
            return None

        def admitted_fields():
            if (not self.current() or any(_certificate_fraction_fields(value) != (0, 1)
                    for value in self.zero_coefficients)):
                return None
            record = self.results.get(name)
            if record is None or record[3] != (0, 1):
                return None
            operands, saved, result, result_fields = record
            if (tuple(_certificate_fraction_fields(value, bits=8195) for value in operands) != saved
                    or _certificate_fraction_fields(result, bits=8195) != result_fields):
                self.valid = False
                return None
            a = _certificate_fraction_fields(first, bits=8195)
            b = _certificate_fraction_fields(last, bits=8195)
            if (a != (0, 1) or b is None or operation == "div" and b[0] == 0
                    or name == "angle_squared" and b != (0, 1)):
                return None
            return a, b, result_fields

        fields = admitted_fields()
        if fields is None:
            return None
        if not self.admitted:
            # Share the existing admission with later authored-term reuse.
            # This is real performed work at the first actual zero omission.
            self.arithmetic.tick("independent_certificate_term_admission")
            self.admitted = True
            if admitted_fields() != fields:
                return None
        a, b, result_fields = fields
        an, ad, bn, bd = a[0].bit_length(), a[1].bit_length(), b[0].bit_length(), b[1].bit_length()
        divide = operation == "div"
        self.arithmetic.bits(an, ad, bn, bd, an + (bd if divide else bn),
                             ad + (bn if divide else bd),
                             result_fields[0].bit_length(), result_fields[1].bit_length())
        value = object.__new__(Fraction)
        object.__setattr__(value, "_numerator", result_fields[0])
        object.__setattr__(value, "_denominator", result_fields[1])
        return value


_ADJACENT_BOUNDS_DISPATCH = tuple((name, getattr(_Bounds, name))
                                for name in ("value", "sub", "op", "bits", "tick"))


@dataclass(frozen=True)
class _AdjacentClockReceipt:
    arithmetic: _Bounds
    index: int
    authored: Fraction
    authored_fields: tuple
    raw: bytes
    stored: Fraction
    stored_fields: tuple
    difference: Fraction
    difference_fields: tuple


class _AdjacentClockOperands:
    """One preceding endpoint's completed operands, never an extra cache.

    Adjacent intervals already share an authored/stored endpoint. Only its
    native float decode and exact signed difference may be borrowed. The two
    widths, fresh right endpoint and ordinary abs/max still run in order.
    """
    def __init__(self, arithmetic):
        self.arithmetic, self.owner = arithmetic, arithmetic.work
        self.external = getattr(self.owner, "external_check", None)
        self.previous, self.generation = None, 0

    def native(self):
        arithmetic = self.arithmetic
        if (type(arithmetic) is not _Bounds or arithmetic.work is not self.owner
                or getattr(self.owner, "external_check", None) is not self.external
                or _tick is not _CERTIFICATE_TICK
                or type(_bound_domain(arithmetic)) is not int
                or _bound_domain(arithmetic) != MAX_OPERAND_BITS):
            return False
        dispatches = ((arithmetic, _ADJACENT_BOUNDS_DISPATCH),)
        if self.owner is not None:
            if type(self.owner) is not _CertificateWork:
                return False
            dispatches += ((self.owner, _CERTIFICATE_WORK_DISPATCH),)
        for target, entries in dispatches:
            for name, original in entries:
                method = getattr(target, name, None)
                if type(method) is not MethodType or method.__self__ is not target or method.__func__ is not original:
                    return False
        return True

    @staticmethod
    def raw(value):
        return struct.pack(">d", value) if type(value) is float and math.isfinite(value) else None

    def reuse(self, previous, key, authored, raw):
        if (not self.native() or type(previous) is not _AdjacentClockReceipt
                or previous.arithmetic is not self.arithmetic
                or type(key) is not int or not 1 <= key < MAX_KEYS
                or key != previous.index + 1 or authored is not previous.authored
                or self.raw(raw) != previous.raw
                or _certificate_fraction_fields(authored) != previous.authored_fields
                or _certificate_fraction_fields(previous.stored, bits=1075) != previous.stored_fields
                or _certificate_fraction_fields(previous.difference, bits=3124) != previous.difference_fields):
            return None
        return previous

    def calculate(self, key, left, right, raw_left, raw_right):
        arithmetic, previous = self.arithmetic, self.previous
        self.previous = None
        self.generation += 1
        generation = self.generation
        source_fields = (_certificate_fraction_fields(left), _certificate_fraction_fields(right),
                         self.raw(raw_left), self.raw(raw_right))
        capture = (self.native() and type(key) is int and 0 <= key < MAX_KEYS
                   and all(value is not None for value in source_fields))
        borrowed, stored_right, stored_fields = None, None, None

        def checked(operation, *args):
            nonlocal capture
            result = operation(*args)
            # An original callback/resource failure escapes before this check.
            # Checking fields adds no callback and never guards an operand at
            # an earlier point than the original finite arithmetic would.
            if borrowed is not None and (
                    self.arithmetic is not arithmetic or arithmetic.work is not self.owner
                    or getattr(self.owner, "external_check", None) is not self.external
                    or _certificate_fraction_fields(borrowed.stored, bits=1075) != borrowed.stored_fields):
                _error("OKE-E-INDEPENDENT-VALIDATION", "A borrowed adjacent clock operand or owner changed.")
            capture = (capture and self.arithmetic is arithmetic and self.native()
                       and source_fields == (_certificate_fraction_fields(left), _certificate_fraction_fields(right),
                                             self.raw(raw_left), self.raw(raw_right))
                       and (stored_fields is None
                            or _certificate_fraction_fields(stored_right, bits=1075) == stored_fields))
            return result

        candidate = self.reuse(previous, key, left, raw_left) if capture else None
        if candidate is None:
            stored_left = checked(arithmetic.value, raw_left)
        else:
            # The original binary64 decode has at most 1075-bit fields. Native
            # full-domain guards cannot call back or fail within that bound.
            arithmetic.bits(*(value.bit_length() for value in candidate.stored_fields))
            stored_left, borrowed = candidate.stored, candidate
        stored_right = checked(arithmetic.value, raw_right)
        stored_fields = _certificate_fraction_fields(stored_right, bits=1075)
        capture = capture and stored_fields is not None
        width = checked(arithmetic.sub, right, left)
        stored_width = checked(arithmetic.sub, stored_right, stored_left)
        candidate = self.reuse(previous, key, left, raw_left) if borrowed is not None else None
        if candidate is None:
            left_difference = checked(arithmetic.sub, left, stored_left)
        else:
            # <=2048-bit authored fields and a finite binary64 ratio imply
            # <=3124-bit prospective subtraction/result guards. Only this
            # actual omission point may discharge them under the full cap.
            an, ad = (value.bit_length() for value in candidate.authored_fields)
            bn, bd = (value.bit_length() for value in candidate.stored_fields)
            arithmetic.bits(an, ad, bn, bd, max(an + bd, bn + ad) + 1, ad + bd,
                            *(value.bit_length() for value in candidate.difference_fields))
            left_difference = candidate.difference
        # abs() remains at the original position and creates the current
        # interval's own absolute result before the next surviving callback.
        left_shift = abs(left_difference)
        difference = checked(arithmetic.sub, right, stored_right)
        shift = max(left_shift, abs(difference))
        difference_fields = _certificate_fraction_fields(difference, bits=3124)
        if capture and difference_fields is not None and self.generation == generation:
            self.previous = _AdjacentClockReceipt(arithmetic, key, right, source_fields[1], source_fields[3],
                                                  stored_right, stored_fields, difference, difference_fields)
        return stored_left, stored_right, width, stored_width, shift


class _IntervalCertificateClaims:
    """Validate every supplied row against one interval's common source facts.

    Only the last admitted immutable strings and phase-index tuple are retained.
    They are bounded current-input proof state, not a numeric result cache. All
    carriers share the independently checked boundary axis, but their numeric
    phase bounds and endpoint comparisons remain separate and unconditional.
    """
    def __init__(self, boundaries, low, high, required, width, stored_width, work):
        self.boundaries, self.low, self.high = boundaries, low, high
        self.required, self.widths, self.work = frozenset(required), (width, stored_width), work
        self.clocks, self.selected = (None, None), None

    def check(self, record):
        _tick(self.work, "independent_interval_claim")
        selected = record["source_phase_indices"]
        count = len(self.boundaries) - 1
        if (type(selected) is not list or len(selected) > count
                or any(type(value) is not int or not 0 <= value < count for value in selected)):
            _error("OKE-E-PHASE-COVERAGE", "A certificate omits a positive-width source phase or names an unrelated phase.")
        selected = tuple(selected)
        if selected != self.selected:
            _tick(self.work, "independent_interval_phase_claim")
            if (len(selected) != len(set(selected)) or not self.required.issubset(selected)
                    or any(max(self.low, self.boundaries[value]) > min(self.high, self.boundaries[value + 1])
                           for value in selected)):
                _error("OKE-E-PHASE-COVERAGE", "A certificate omits a positive-width source phase or names an unrelated phase.")
            self.selected = selected
        clocks = []
        arithmetic = _Bounds(self.work)
        for index, name in enumerate(("h_authored_seconds", "h_stored_seconds")):
            width = self.widths[index]
            arithmetic.bits(width.numerator.bit_length(), width.denominator.bit_length())
            value = record[name]
            texts = (tuple(value[key] for key in ("numerator", "denominator"))
                     if type(value) is dict and set(value) == {"numerator", "denominator"} else None)
            if (texts is None or not all(type(text) is str for text in texts)
                    or texts != self.clocks[index]):
                if rational_clock(value, work=self.work) != width:
                    _error("OKE-E-CLOCK", "Certificate widths do not match actual retained clocks.")
            clocks.append(texts)
        self.clocks = tuple(clocks)
        return selected


def _verify_certificates(decoded, reference, geometry, tables, endpoint_phases, authored, times, quantization, options, *, work,
                         finalize=None):
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

    threshold_batch = None

    def compare_certificates(recording_context, source_batch=None, *, thresholds=True, replay_batch=None):
        nonlocal threshold_batch
        # A replay recreates every endpoint/comparison/certificate accumulator
        # on the same request work. It never resets or replaces the allowance.
        arithmetic = replay_batch.arithmetic if replay_batch is not None else _Bounds(work, cache_intermediates=False)
        previous = _key_comparisons(reference, geometry, tracks, authored[0], 0, arithmetic,
                                    recording_context=recording_context, endpoint_rows=rows)
        batch = (replay_batch if replay_batch is not None else
                 _CertificateBatch(arithmetic, options.position_tolerance_m, options.rotation_tolerance_rad,
                                   thresholds=thresholds))
        threshold_batch = batch
        clocks = _AdjacentClockOperands(arithmetic)
        for key, (left, right) in enumerate(zip(authored, authored[1:])):
            following = _key_comparisons(reference, geometry, tracks, right, key + 1, arithmetic,
                                         previous=previous, previous_time=left, recording_context=recording_context,
                                         endpoint_rows=rows)
            stored_left, stored_right, width, stored_width, shift = clocks.calculate(
                key, left, right, times[key], times[key + 1])
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
            claims = _IntervalCertificateClaims(reference.boundaries, low, high, required, width, stored_width, work)
            for carrier, item in geometry.items():
                record, phases = rows[key, carrier], tables[item["frame"]]
                selected = claims.check(record)
                phase = phases[source_index]
                source_position = max(phases[value].source_numeric_position_error for value in numeric_selected)
                source_rotation = max(phases[value].source_numeric_rotation_error for value in numeric_selected)
                if right == reference.end:
                    final_phase = endpoint_phases[item["frame"]]
                    source_position = max(source_position, final_phase.source_numeric_position_error)
                    source_rotation = max(source_rotation, final_phase.source_numeric_rotation_error)
                first, last = previous[carrier], following[carrier]
                raw_first, raw_last = tracks[carrier]["rotation"][key], tracks[carrier]["rotation"][key + 1]
                arc = _certified_stored_arc(raw_first, raw_last, first, last, phase.angular_speed, width,
                                           record["stored_quaternion_arc_upper_rad"], arithmetic,
                                           source_path_valid=right < reference.boundaries[source_index + 1])
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
                magnitude = max(first["magnitude"], last["magnitude"])
                batch.add(record, width, stored_width, minima, magnitude)
            previous = following
        if source_batch is not None:
            source_batch.prepare_admission()
        batch.flush()
        return {"max_position_bound_m": batch.max_position, "max_rotation_bound_rad": batch.max_rotation,
                "interval_certificates_checked": expected_count, "key_pose_comparisons": len(authored) * len(geometry)}

    from .reach_reference_plan import _SourceBatchRestart
    recording_context, source_batch, replay_batch = object(), None, None
    source_batch_enabled, thresholds_enabled = True, True
    while True:
        threshold_batch = None
        try:
            if source_batch_enabled:
                with reference.recording_source_batch(recording_context) as source_batch:
                    try:
                        result = compare_certificates(recording_context, source_batch,
                                                      thresholds=thresholds_enabled, replay_batch=replay_batch)
                    except _CertificateThresholdRestart as error:
                        if (source_batch is not None and threshold_batch is not None
                                and threshold_batch.restart_requested
                                and threshold_batch.restart is error
                                and getattr(work, "callback_error", None) is not error):
                            # Do not recapture a changed source as the basis
                            # of the exact replay. Admit the original receipt
                            # ledger before this provisional batch is dropped.
                            source_batch.prepare_admission()
                            source_batch.admit()
                        raise
                    if finalize is not None:
                        result = finalize(result)
                return result
            result = compare_certificates(recording_context, thresholds=thresholds_enabled,
                                          replay_batch=replay_batch)
            return finalize(result) if finalize is not None else result
        except _SourceBatchRestart as error:
            # A caller can raise any exception, including a private type.
            # Only this exact final-admission signal permits source replay.
            if (not source_batch_enabled or source_batch is None
                    or source_batch.restart is not error
                    or getattr(work, "callback_error", None) is error):
                raise
            if (threshold_batch is not None
                    and (threshold_batch.restart_requested or replay_batch is threshold_batch)):
                # Final source admission can report its own narrower-domain
                # restart while discharging a requested threshold replay.
                thresholds_enabled = False
                threshold_batch._prepare_exact_replay()
                replay_batch = threshold_batch
            source_batch_enabled = False
            recording_context = object()
        except _CertificateThresholdRestart as error:
            # A distinct, actually requested signal belongs to this batch.
            # Rebuild all accumulators with exact maxima, retaining the same
            # work, callbacks, operand/cache caps and final source admission.
            if (not thresholds_enabled or threshold_batch is None
                    or not threshold_batch.restart_requested or threshold_batch.restart is not error
                    or getattr(work, "callback_error", None) is error):
                raise
            thresholds_enabled = False
            threshold_batch._prepare_exact_replay()
            replay_batch = threshold_batch
            recording_context = object()


def validate_reach_export(data, model, *, options=None, check=None, work=None, target_contract=TARGET):
    """Verify the complete source/byte proof with the caller's existing work.

    Missing independent source behavior rejects delivery. Additional fixed,
    interior, native-player and browser observations belong to the release
    workflow and remain distinct from this continuous supplied-byte proof.
    """
    from .gltf import read_glb, _validate_geometry
    from .reach_reference import ReferenceError, build_reference
    from .scene import ExportOptions, MAX_BAKED_POSES, checked_contract, program_metadata, BUDGET_REACH_TARGET, REACH_TARGETS
    if target_contract not in REACH_TARGETS:
        raise ValueError("A reach recording requires an explicit reach destination")
    if target_contract == BUDGET_REACH_TARGET:
        from .reach_numeric import require_execution_work
        require_execution_work(work)
    if work is None:
        raise ValueError("Reach supplied-byte validation requires the existing request work context")
    checked_contract(model, target_contract)
    decoded = read_glb(data, check=work.tick, target_contract=target_contract, work=work)
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
        quantization = _verify_metadata(decoded, model, options, program, boundary_records, work=work,
                                        target_contract=target_contract)
        authored, times, shift = verify_retained_clocks(decoded, quantization, authored_records,
            reference.boundaries, end, time_tolerance=options.time_tolerance_s, work=work)
        geometry, meshes = _geometry_bounds(decoded, model, options, work=work)
        frames, geometry_error, surface_error = _validate_geometry(decoded, model, options, target_contract, program,
            check=work.tick, source_meshes=meshes)
        if any(frames[index] != value["frame"] for index, value in geometry.items()):
            _error("OKE-E-PROVENANCE", "The native geometry and independent source carrier frames disagree.")
        tables = _phase_tables(reference, geometry, work=work)
        endpoint_phases = {frame: reference.point_phase(frame, end, side="after") for frame in tables}
        allowances = _boundary_allowances(tables, endpoint_phases, geometry, model, _Bounds(work))
        _assert_projection(metadata.get("boundary_states"), boundary_records,
            arithmetic=_Bounds(work), allowances=allowances, path=("boundary_states",))
        def finalize(proof):
            # Report conversion has its own checked callbacks. Keep those
            # inside the provisional source batch so the callback-free source
            # admission is the final action before returning a passed report.
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
        return _verify_certificates(decoded, reference, geometry, tables, endpoint_phases,
                                    authored, times, quantization, options, work=work, finalize=finalize)
    except ReferenceError as error:
        _error("OKE-E-INDEPENDENT-VALIDATION", "The independent source reference could not establish the requested recording: " + str(error),
            model=model, kind="resource" if error.code == "resource" else "unsupported",
            details={"reference_code": error.code, **error.details})
