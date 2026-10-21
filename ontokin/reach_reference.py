"""Independent source reference for the recorded planar reach profile.

This module deliberately imports no evaluator, reach solver, pose sampler,
planner, certifier, exporter, or preparation oracle.  It reads the immutable
constructed source records and interprets their equations and event clocks.
Fraction enclosures, rather than host transcendental answers, supply expected
poses.  A supplied request work context is shared throughout; this verifier
never creates another execution allowance.

The public numeric leaves are ``Interval`` instances where an exact binary64
answer is not a source invariant.  A consumer must check containment (including
the independently propagated source arithmetic allowance), not compare a
chosen interval midpoint as an exact expected answer.
"""
from __future__ import annotations

from bisect import bisect_left, bisect_right
import copy
from dataclasses import dataclass, field, fields, is_dataclass
from fractions import Fraction as F
import math
import struct
from types import MappingProxyType


MAX_OPERAND_BITS = 32768
MAX_BOUNDARIES = 10000
MAX_CACHE = 256
PRECISIONS = (128, 256, 512, 1024, 2048)
PI64 = F(3.141592653589793)
ZERO = (F(0), F(0), F(0))
UNIT = (F(1), F(0), F(0), F(0))


class ReferenceError(Exception):
    """The independent reference cannot certify the requested source prefix."""
    def __init__(self, code, message, **details):
        super().__init__(message)
        self.code = code
        self.details = details


@dataclass(frozen=True)
class Interval:
    lo: F
    hi: F

    def __post_init__(self):
        if self.lo > self.hi:
            raise ValueError("Reversed reference interval")

    @property
    def magnitude(self):
        return max(abs(self.lo), abs(self.hi))

    def contains(self, value):
        return self.lo <= F(value) <= self.hi


class _Uncertain(Exception):
    pass


class _Arithmetic:
    """Outward Fraction arithmetic with a bounded dyadic endpoint grid.

    The integer-grid representation is deliberately not the production
    numerical kernel: each operation first forms exact Fraction extrema and
    rounds its endpoints outward.  All constituent scalar operations charge
    the caller, and operand growth is checked before multiplication/division.
    """
    def __init__(self, work=None, check=None, *, bits=128):
        if work is None and check is None:
            raise ValueError("Independent verification requires shared work or a bounded check callback")
        self.work = work
        self.check = work.tick if work is not None else check
        self.bits = bits
        self.scale = 1 << bits
        self.cache = {}

    def tick(self):
        self.check()

    def guard(self, *values):
        for value in values:
            value = F(value)
            if max(abs(value.numerator).bit_length(), value.denominator.bit_length()) > MAX_OPERAND_BITS:
                raise ReferenceError("resource", "Independent reference operand limit exceeded")

    def exact(self, a, b, kind):
        self.tick()
        a, b = F(a), F(b)
        self.guard(a, b)
        an, ad = abs(a.numerator).bit_length(), a.denominator.bit_length()
        bn, bd = abs(b.numerator).bit_length(), b.denominator.bit_length()
        if kind in ("add", "sub"):
            extent = max(an + bd, bn + ad) + 1
            denominator = ad + bd
        elif kind == "mul":
            extent, denominator = an + bn, ad + bd
        elif kind == "div":
            if not b:
                raise _Uncertain("Reference division includes zero")
            extent, denominator = an + bd, ad + bn
        else:
            raise ValueError(kind)
        if max(extent, denominator) > MAX_OPERAND_BITS:
            raise ReferenceError("resource", "Independent reference intermediate operand limit exceeded")
        return {"add": F.__add__, "sub": F.__sub__, "mul": F.__mul__, "div": F.__truediv__}[kind](a, b)

    def exact_sum(self, *values):
        """Fold bounded exact scalars without allocating additions of zero."""
        self.tick()
        values = tuple(F(value) for value in values)
        self.guard(*values)
        result = F(0)
        for value in values:
            if value:
                result = value if not result else self.exact(result, value, "add")
        return result

    def exact_product(self, *values):
        """Guard every operand before omitting exact zero/identity products."""
        self.tick()
        values = tuple(F(value) for value in values)
        self.guard(*values)
        if any(not value for value in values):
            return F(0)
        result = F(1)
        for value in values:
            if value != 1:
                result = value if result == 1 else self.exact(result, value, "mul")
        return result

    def point(self, value):
        self.tick()
        value = F(value)
        self.guard(value)
        return Interval(value, value)

    def grid(self, low, high):
        self.tick()
        self.guard(low, high)
        if max(abs(low.numerator).bit_length(), abs(high.numerator).bit_length()) + self.bits > MAX_OPERAND_BITS:
            raise ReferenceError("resource", "Reference endpoint grid exceeds operand limit")
        low_n = (low.numerator << self.bits) // low.denominator
        high_n = -((-high.numerator << self.bits) // high.denominator)
        return Interval(F(low_n, self.scale), F(high_n, self.scale))

    def interval(self, value):
        return value if isinstance(value, Interval) else self.point(value)

    def add(self, a, b):
        a, b = self.interval(a), self.interval(b)
        self.tick()
        if a.lo == a.hi == 0:
            return b
        if b.lo == b.hi == 0:
            return a
        return self.grid(self.exact(a.lo, b.lo, "add"), self.exact(a.hi, b.hi, "add"))

    def neg(self, a):
        self.tick()
        a = self.interval(a)
        return Interval(-a.hi, -a.lo)

    def sub(self, a, b):
        return self.add(a, self.neg(b))

    def mul(self, a, b):
        a, b = self.interval(a), self.interval(b)
        self.tick()
        if a.lo == a.hi == 0 or b.lo == b.hi == 0:
            return Interval(F(0), F(0))
        if a.lo == a.hi == 1:
            return b
        if b.lo == b.hi == 1:
            return a
        if a.lo == a.hi and b.lo == b.hi:
            value = self.exact(a.lo, b.lo, "mul")
            return self.grid(value, value)
        products = [self.exact(x, y, "mul") for x in (a.lo, a.hi) for y in (b.lo, b.hi)]
        return self.grid(min(products), max(products))

    def div(self, a, b):
        a, b = self.interval(a), self.interval(b)
        if b.lo <= 0 <= b.hi:
            raise _Uncertain("Reference interval divisor contains zero")
        self.tick()
        if a.lo == a.hi == 0:
            return a
        if b.lo == b.hi == 1:
            return a
        if a.lo == a.hi and b.lo == b.hi:
            value = self.exact(a.lo, b.lo, "div")
            return self.grid(value, value)
        quotients = [self.exact(x, y, "div") for x in (a.lo, a.hi) for y in (b.lo, b.hi)]
        return self.grid(min(quotients), max(quotients))

    def sqrt(self, value):
        value = self.interval(value)
        if value.lo < 0:
            raise _Uncertain("Reference radical is not certified nonnegative")
        result = []
        for endpoint in (value.lo, value.hi):
            self.tick()
            if abs(endpoint.numerator).bit_length() + 2 * self.bits > MAX_OPERAND_BITS:
                raise ReferenceError("resource", "Reference radical operand limit exceeded")
            scaled = (endpoint.numerator << (2 * self.bits)) // endpoint.denominator
            root = math.isqrt(scaled)
            low = F(root, self.scale)
            high = low if self.exact(low, low, "mul") == endpoint else F(root + 1, self.scale)
            result.append((low, high))
        return Interval(result[0][0], result[1][1])

    def total(self, values):
        result = self.point(0)
        for value in values:
            result = self.add(result, value)
        return result

    def remember(self, key, value):
        self.tick()
        if key in self.cache:
            del self.cache[key]
        elif len(self.cache) >= MAX_CACHE:
            del self.cache[next(iter(self.cache))]
        self.cache[key] = value
        return value

    def lookup(self, key):
        """Reuse pure work within the same bounded independent context."""
        self.tick()
        value = self.cache.get(key)
        if value is not None:
            # Dictionary insertion order supplies bounded least-recent use;
            # no source state, allowance or external callback is cached.
            del self.cache[key]
            self.cache[key] = value
        return value

    def _atan_small(self, value):
        """Alternating atan series for an exact |x| <= 1/2, with next-term enclosure."""
        value = F(value)
        if value < 0:
            return self.neg(self._atan_small(-value))
        if value > F(1, 2):
            raise _Uncertain("Reference atan reduction did not reach its bounded series")
        square = self.exact(value, value, "mul")
        power, total = value, F(0)
        for k in range(self.bits + 8):
            term = self.exact(power, 2 * k + 1, "div")
            total = self.exact(total, term, "add" if k % 2 == 0 else "sub")
            power = self.exact(power, square, "mul")
            following = self.exact(power, 2 * k + 3, "div")
            if following < F(1, 1 << (self.bits + 8)):
                other = self.exact(total, following, "sub" if k % 2 == 0 else "add")
                return self.grid(min(total, other), max(total, other))
        raise _Uncertain("Finite reference atan series did not converge")

    def pi(self):
        key = ("pi", self.bits)
        cached = self.lookup(key)
        if cached is not None:
            return cached
        return self.remember(key, self.sub(self.mul(16, self._atan_small(F(1, 5))),
                                          self.mul(4, self._atan_small(F(1, 239)))))

    def _atan_point(self, value):
        if value < 0:
            return self.neg(self._atan_point(-value))
        if value > 1:
            return self.sub(self.div(self.pi(), 2), self._atan_point(self.exact(1, value, "div")))
        if value > F(1, 2):
            reduced = self.exact(self.exact(value, 1, "sub"), self.exact(value, 1, "add"), "div")
            return self.add(self.div(self.pi(), 4), self._atan_small(reduced))
        return self._atan_small(value)

    def atan(self, value):
        value = self.interval(value)
        low, high = self._atan_point(value.lo), self._atan_point(value.hi)
        return Interval(low.lo, high.hi)

    def atan2(self, y, x):
        y, x = self.interval(y), self.interval(x)
        if x.lo == x.hi == 0:
            if y.lo > 0:
                return self.div(self.pi(), 2)
            if y.hi < 0:
                return self.neg(self.div(self.pi(), 2))
            raise _Uncertain("Unresolved reference atan2 origin")
        if x.lo > 0:
            return self.atan(self.div(y, x))
        if x.hi < 0:
            base = self.atan(self.div(y, x))
            if y.lo >= 0:
                return self.add(base, self.pi())
            if y.hi <= 0:
                return self.sub(base, self.pi())
        if y.lo > 0:
            return self.sub(self.div(self.pi(), 2), self.atan(self.div(x, y)))
        if y.hi < 0:
            return self.sub(self.neg(self.div(self.pi(), 2)), self.atan(self.div(x, y)))
        raise _Uncertain("Reference atan2 quadrant is unresolved")

    def _series_sincos(self, value):
        """Exact midpoint Taylor sums, with interval width and alternating tails.

        Both functions are globally 1-Lipschitz.  Evaluating one exact rational
        midpoint and adding its half-width is a rigorous interval calculation
        with far fewer repeated endpoint products than interval Horner powers.
        """
        value = self.interval(value)
        if value.magnitude > 1:
            raise _Uncertain("Reference sine reduction exceeds its proved range")
        middle = self.exact(self.exact(value.lo, value.hi, "add"), 2, "div")
        width = max(self.exact(middle, value.lo, "sub"), self.exact(value.hi, middle, "sub"))
        squared = self.exact(middle, middle, "mul")
        sine, cosine = middle, F(1)
        sine_term, cosine_term = middle, F(1)
        threshold = F(1, 1 << (self.bits + 8))
        for k in range(1, self.bits // 5 + 12):
            sine_term = -self.exact(self.exact(sine_term, squared, "mul"), (2 * k) * (2 * k + 1), "div")
            cosine_term = -self.exact(self.exact(cosine_term, squared, "mul"), (2 * k - 1) * (2 * k), "div")
            sine, cosine = self.exact(sine, sine_term, "add"), self.exact(cosine, cosine_term, "add")
            self.tick()
            tail = max(abs(sine_term), abs(cosine_term))
            if tail < threshold:
                # For |middle| <= 1 each alternating series decreases in
                # absolute term size. Its tail after the included term is no
                # larger than the following term, hence no larger than this
                # computed term. The half-width covers every original input
                # by the global 1-Lipschitz bound of both sine and cosine.
                error = self.exact(tail, width, "add")
                return (self.grid(self.exact(sine, error, "sub"), self.exact(sine, error, "add")),
                        self.grid(self.exact(cosine, error, "sub"), self.exact(cosine, error, "add")))
        raise _Uncertain("Finite reference sine series did not converge")

    def sincos(self, value):
        value = self.interval(value)
        key = ("sincos", self.bits, value.lo, value.hi)
        cached = self.lookup(key)
        if cached is not None:
            return cached
        if value.lo == value.hi == 0:
            return self.point(0), self.point(1)
        pi = self.pi()
        midpoint = self.exact(value.lo, value.hi, "add")
        quotient = self.exact(midpoint, self.exact(pi.lo, pi.hi, "add"), "div")
        self.tick()
        quadrant = round(quotient * 2)
        reduced = self.sub(value, self.mul(F(quadrant, 2), pi))
        sine, cosine = self._series_sincos(reduced)
        result = ((sine, cosine), (cosine, self.neg(sine)),
                  (self.neg(sine), self.neg(cosine)), (self.neg(cosine), sine))[quadrant % 4]
        return self.remember(key, result)

    def round64(self, value):
        """Use monotonic correctly rounded Fraction conversion to prove one cell."""
        value = self.interval(value)
        self.tick()
        try:
            low, high = float(value.lo), float(value.hi)
        except OverflowError as error:
            raise ReferenceError("numeric", "Independent reference result exceeds binary64") from error
        if not math.isfinite(low) or not math.isfinite(high):
            raise ReferenceError("numeric", "Independent reference requires finite binary64")
        if low != high:
            raise _Uncertain("Reference enclosure crosses a binary64 rounding cell")
        return 0.0 if low == 0 else low


def _time_text(value):
    value = F(value)
    if value.denominator == 1:
        return str(value.numerator)
    # Exact clocks in this profile are dyadic and therefore have finite decimals.
    denominator, twos, fives = value.denominator, 0, 0
    while denominator % 2 == 0:
        denominator //= 2
        twos += 1
    while denominator % 5 == 0:
        denominator //= 5
        fives += 1
    if denominator != 1:
        return str(value)
    places = max(twos, fives)
    scaled = abs(value.numerator) * 2 ** (places - twos) * 5 ** (places - fives)
    digits = str(scaled).rjust(places + 1, "0")
    return ("-" if value < 0 else "") + (digits[:-places] + "." + digits[-places:]).rstrip("0").rstrip(".")


def _canonical_targets(payload, arithmetic):
    """Solve the defining signed-radical equations independently of production."""
    lengths = tuple(F(x) for x in payload.lengths_m)
    x, y, z = (F(v) for v in payload.target_m)
    a, b = lengths
    op = arithmetic.exact
    radius = op(op(x, x, "mul"), op(y, y, "mul"), "add")
    minimum = op(op(a, b, "sub"), op(a, b, "sub"), "mul")
    maximum = op(op(a, b, "add"), op(a, b, "add"), "mul")
    if z or radius < minimum or radius > maximum:
        raise ReferenceError("source_admission", "Independent reach is outside its exact annulus")
    if not radius:
        raise ReferenceError("source_admission", "Independent reach has a singular origin")
    if payload.branch not in {"elbow_positive", "elbow_negative"}:
        raise ReferenceError("source_admission", "Unknown independent reach branch")
    cosine = op(op(op(radius, op(a, a, "mul"), "sub"), op(b, b, "mul"), "sub"),
                op(op(2, a, "mul"), b, "mul"), "div")
    sign = 1 if payload.branch == "elbow_positive" else -1
    radical = op(1, op(cosine, cosine, "mul"), "sub")
    k = op(a, op(b, cosine, "mul"), "add")

    def radical_sign(constant, factor):
        # Sign of A+B*sqrt(r), including exact zeros, without a rounded
        # transcendental.  This prevents a true zero shoulder from becoming
        # an interval spanning many subnormal rounding cells.
        if not radical or not factor:
            return (constant > 0) - (constant < 0)
        if not constant or (constant > 0) == (factor > 0):
            return (factor > 0) - (factor < 0)
        squared = op(op(constant, constant, "mul"), op(op(factor, factor, "mul"), radical, "mul"), "sub")
        return ((constant > 0) - (constant < 0)) * ((squared > 0) - (squared < 0))

    shoulder_x = (op(x, k, "mul"), op(op(y, b, "mul"), sign, "mul"))
    shoulder_y = (op(y, k, "mul"), op(op(-x, b, "mul"), sign, "mul"))
    xsign, ysign = radical_sign(*shoulder_x), radical_sign(*shoulder_y)
    for precision in PRECISIONS:
        ar = _Arithmetic(arithmetic.work, arithmetic.check, bits=precision)
        try:
            if cosine == 1:
                elbow = ar.point(0)
            elif cosine == -1:
                elbow = ar.mul(sign, ar.pi())
            else:
                sine = ar.mul(sign, ar.sqrt(radical))
                elbow = ar.atan2(sine, cosine)
            root = ar.sqrt(radical)
            cartesian = []
            for (constant, factor), exact_sign in ((shoulder_x, xsign), (shoulder_y, ysign)):
                value = ar.point(0) if exact_sign == 0 else ar.add(constant, ar.mul(factor, root))
                if exact_sign and value.lo <= 0 <= value.hi:
                    raise _Uncertain("Reference signed radical needs refinement")
                cartesian.append(value)
            shoulder = ar.atan2(cartesian[1], cartesian[0])
            first, second = ar.round64(shoulder), ar.round64(elbow)
            if first == float(PI64):
                first = -float(PI64)
            if any(not low <= value <= high for value, (low, high) in zip((first, second), payload.limits_rad)):
                raise ReferenceError("source_admission", "Independent selected branch violates a closed limit")
            return (first, second)
        except _Uncertain:
            continue
    raise ReferenceError("numeric", "Finite independent admission could not establish canonical targets")


@dataclass(frozen=True)
class PoseEnclosure:
    position: tuple[Interval, ...]
    orientation: tuple[Interval, ...]
    velocity: tuple[Interval, ...]
    omega: tuple[Interval, ...]


@dataclass(frozen=True)
class RecordingPoseEnclosure:
    """Position/orientation only; no uncomputed derivative is exposed."""
    position: tuple[Interval, ...]
    orientation: tuple[Interval, ...]


@dataclass(frozen=True)
class CoordinatePath:
    joint: str
    action: str | None
    initial: F
    target: F
    local_elapsed_at_start: F
    duration: F | None
    slope: F
    actual_start: F
    actual_end: F
    ideal_initial: F
    ideal_start: F
    ideal_end: F
    actual_slope: F
    coordinate_error: F


@dataclass(frozen=True)
class ReferencePhase:
    start: F
    end: F
    carrier: str
    speed: F
    acceleration: F
    angular_speed: F
    coordinates: tuple[CoordinatePath, ...]
    root_position: tuple[Interval, ...]
    root_velocity: tuple[Interval, ...]
    root_acceleration: tuple[F, ...]
    root_orientation: tuple[Interval, ...]
    root_omega: tuple[Interval, ...]
    ideal_root_position: tuple[Interval, ...]
    ideal_root_velocity: tuple[Interval, ...]
    ideal_root_orientation: tuple[Interval, ...]
    ideal_root_omega: tuple[Interval, ...]
    offset_radius: F
    max_position_l1: F
    anchor_position_error: F
    anchor_rotation_error: F
    anchor_velocity_error: F
    anchor_angular_velocity_error: F
    source_numeric_position_error: F
    source_numeric_rotation_error: F
    source_numeric_velocity_error: F
    source_numeric_angular_velocity_error: F
    trig_count: int
    product_count: int
    vector_round_count: int
    coordinate_angle_error: F
    path: tuple[str, ...]


def build_reference(model, *, end, end_side="after", mode="recording", work=None, check=None):
    """Build a source-derived reference, sharing the caller's remaining work.

    ``work`` takes precedence over ``check`` to avoid charging the same request
    twice.  Supplying neither is an error: a verifier must not silently acquire
    another budget after compilation, source evaluation, or byte decoding.
    Explicit ``mode="observation"`` reconstructs requested source state without
    claiming complete H06 recording capacity; ``boundary_states`` is unavailable.
    """
    return ReachReference(model, end=F(end), end_side=end_side, mode=mode, arithmetic=_Arithmetic(work, check))


class _PoseArithmetic:
    def __init__(self, arithmetic):
        self.a = arithmetic

    def vector(self, value):
        if value is ZERO:
            key = self._key("zero_vector")
            cached = self.a.lookup(key)
            if cached is not None:
                return cached
            return self.a.remember(key, tuple(self.a.point(x) for x in ZERO))
        return tuple(self.a.interval(x) for x in value)

    @staticmethod
    def _zero(vector):
        return all(value.lo == value.hi == 0 for value in vector)

    def _key(self, operation, *values):
        return ("reference_pose", self.a.bits, operation, *values)

    def add(self, left, right):
        left, right = self.vector(left), self.vector(right)
        self.a.tick()
        if self._zero(left):
            return right
        if self._zero(right):
            return left
        return tuple(self.a.add(a, b) for a, b in zip(left, right))

    def scale(self, vector, scalar):
        vector, scalar = self.vector(vector), self.a.interval(scalar)
        self.a.tick()
        if self._zero(vector) or scalar.lo == scalar.hi == 0:
            return (Interval(F(0), F(0)),) * len(vector)
        if scalar.lo == scalar.hi == 1:
            return vector
        return tuple(self.a.mul(value, scalar) for value in vector)

    def cross(self, a, b):
        a, b = self.vector(a), self.vector(b)
        self.a.tick()
        if self._zero(a) or self._zero(b):
            return (Interval(F(0), F(0)),) * 3
        return tuple(self.a.sub(self.a.mul(a[j], b[k]), self.a.mul(a[k], b[j]))
                     for j, k in ((1, 2), (2, 0), (0, 1)))

    def norm(self, vector):
        # Squaring the whole interval loses correlation at zero; endpoint
        # squares supply the exact nonnegative range of each component.
        vector = self.vector(vector)
        key = self._key("norm", vector)
        cached = self.a.lookup(key)
        if cached is not None:
            return cached
        squares = []
        for value in vector:
            low = 0 if value.lo <= 0 <= value.hi else min(abs(value.lo), abs(value.hi))
            squares.append(Interval(self.a.exact(low, low, "mul"),
                                    self.a.exact(value.magnitude, value.magnitude, "mul")))
        return self.a.remember(key, self.a.sqrt(self.a.total(squares)))

    def quaternion(self, values):
        values = self.vector(values)
        key = self._key("quaternion", values)
        cached = self.a.lookup(key)
        if cached is not None:
            return cached
        if len(values) == 4 and self._zero(values[1:]) and (values[0].lo > 0 or values[0].hi < 0):
            sign = F(1) if values[0].lo > 0 else F(-1)
            return self.a.remember(key, (Interval(sign, sign), *(Interval(F(0), F(0)),) * 3))
        denominator = self.norm(values)
        if denominator.lo <= 0:
            raise ReferenceError("numeric", "Independent quaternion normalization includes zero")
        return self.a.remember(key, tuple(self.a.div(value, denominator) for value in values))

    def multiply(self, left, right):
        a, b = left, right
        self.a.tick()
        if all(value.lo == value.hi == expected for value, expected in zip(a, UNIT)):
            return b
        if all(value.lo == value.hi == expected for value, expected in zip(b, UNIT)):
            return a
        key = self._key("multiply", tuple(a), tuple(b))
        cached = self.a.lookup(key)
        if cached is not None:
            return cached
        if self._zero((a[1], a[2], b[1], b[2])):
            # The exact Hamilton product of two world-Z representatives has
            # only scalar/Z components. Omit the twelve products proved zero;
            # interval-zero tests never treat an uncertain zero as exact.
            zero = self.a.point(0)
            return self.a.remember(key, (
                self.a.sub(self.a.mul(a[0], b[0]), self.a.mul(a[3], b[3])), zero, zero,
                self.a.add(self.a.mul(a[0], b[3]), self.a.mul(a[3], b[0]))))
        return self.a.remember(key, (
            self.a.sub(self.a.mul(a[0], b[0]), self.a.total(self.a.mul(a[i], b[i]) for i in (1, 2, 3))),
            self.a.total((self.a.mul(a[0], b[1]), self.a.mul(a[1], b[0]), self.a.mul(a[2], b[3]), self.a.neg(self.a.mul(a[3], b[2])))),
            self.a.total((self.a.mul(a[0], b[2]), self.a.neg(self.a.mul(a[1], b[3])), self.a.mul(a[2], b[0]), self.a.mul(a[3], b[1]))),
            self.a.total((self.a.mul(a[0], b[3]), self.a.mul(a[1], b[2]), self.a.neg(self.a.mul(a[2], b[1])), self.a.mul(a[3], b[0]))),
        ))

    def conjugate(self, q):
        return (q[0], *(self.a.neg(x) for x in q[1:]))

    def rotate(self, q, vector):
        # Quaternion-vector multiplication follows a different arithmetic
        # expression from the source implementation's homogeneous matrix rows.
        vector = self.vector(vector)
        self.a.tick()
        if self._zero(vector):
            return vector
        if (len(q) == 4 and q[0].lo == q[0].hi and abs(q[0].lo) == 1
                and self._zero(q[1:])):
            return vector
        key = self._key("rotate", tuple(q), vector)
        cached = self.a.lookup(key)
        if cached is not None:
            return cached
        if self._zero((q[1], q[2])):
            # Expand q*(0,v)*conjugate(q) directly for scalar/Z q. This is
            # valid even for nonunit q: the Z component keeps w*w+z*z rather
            # than silently replacing it by one. No production rotation
            # matrix or homogeneous normalisation supplies this enclosure.
            ww, zz = self.a.mul(q[0], q[0]), self.a.mul(q[3], q[3])
            diagonal = self.a.sub(ww, zz)
            off_diagonal = self.a.mul(2, self.a.mul(q[0], q[3]))
            x, y, z = vector
            return self.a.remember(key, (
                self.a.sub(self.a.mul(diagonal, x), self.a.mul(off_diagonal, y)),
                self.a.add(self.a.mul(off_diagonal, x), self.a.mul(diagonal, y)),
                self.a.mul(self.a.add(ww, zz), z)))
        pure = (self.a.point(0), *vector)
        result = self.multiply(self.multiply(q, pure), self.conjugate(q))[1:]
        return self.a.remember(key, result)

    def spin(self, omega, elapsed):
        values = self.vector(omega)
        if not elapsed or all(value.lo == value.hi == 0 for value in values):
            return self.vector(UNIT)
        norm = self.norm(values)
        if norm.lo <= 0:
            raise ReferenceError("numeric", "Independent spin norm is unresolved")
        sine, cosine = self.a.sincos(self.a.mul(norm, F(elapsed) / 2))
        return (cosine, *(self.a.mul(self.a.div(value, norm), sine) for value in values))

    def hinge(self, axis, coordinate, rate, *, ideal=False):
        axis = self.vector(axis)
        coordinate, rate = self.a.interval(coordinate), self.a.interval(rate)
        key = self._key("hinge", axis, coordinate, rate, ideal)
        cached = self.a.lookup(key)
        if cached is not None:
            return cached
        norm = self.norm(axis)
        normalized_axis = tuple(self.a.div(value, norm) for value in axis)
        sine, cosine = self.a.sincos(self.a.div(coordinate, 2))
        rotation = (cosine, *(self.a.mul(value, sine) for value in normalized_axis))
        # The rotation's mathematical derivative uses a unit axis. The
        # inherited source inspection deliberately retains the canonical raw
        # axis, whose small norm defect is covered by the independent basis.
        omega = self.scale(normalized_axis if ideal else axis, rate)
        return self.a.remember(key, self.make(orientation=rotation, omega=omega, normalized=True))

    def make(self, position=ZERO, orientation=UNIT, velocity=ZERO, omega=ZERO, *, normalized=False):
        return PoseEnclosure(self.vector(position), self.vector(orientation) if normalized else self.quaternion(orientation),
                             self.vector(velocity), self.vector(omega))

    def identity(self):
        key = self._key("identity")
        cached = self.a.lookup(key)
        if cached is not None:
            return cached
        return self.a.remember(key, self.make())

    def constant(self, pose):
        key = self._key("constant", tuple(pose.position), tuple(pose.rotation))
        cached = self.a.lookup(key)
        if cached is not None:
            return cached
        return self.a.remember(key, self.make(pose.position, pose.rotation))

    def compose(self, parent, local):
        key = self._key("compose", parent, local)
        cached = self.a.lookup(key)
        if cached is not None:
            return cached
        offset = self.rotate(parent.orientation, local.position)
        position = self.add(parent.position, offset)
        orientation = self.multiply(parent.orientation, local.orientation)
        rates = (parent.velocity, parent.omega, local.velocity, local.omega)
        if all(len(vector) == 3 and self._zero(vector) for vector in rates):
            # Every cross-product and rotated rate in the spatial derivative
            # equations is exactly zero, even for a nonunit raw quaternion.
            # An interval merely containing zero never takes this path.
            return self.a.remember(key, PoseEnclosure(position, orientation, parent.velocity, parent.omega))
        return self.a.remember(key, PoseEnclosure(position, orientation,
                             self.add(self.add(parent.velocity, self.cross(parent.omega, offset)),
                                      self.rotate(parent.orientation, local.velocity)),
                             self.add(parent.omega, self.rotate(parent.orientation, local.omega))))

    def inverse(self, pose):
        key = self._key("inverse", pose)
        cached = self.a.lookup(key)
        if cached is not None:
            return cached
        orientation = self.conjugate(pose.orientation)
        return self.a.remember(key, self.make(self.rotate(orientation, tuple(self.a.neg(x) for x in pose.position)),
                                             orientation, normalized=True))


@dataclass
class _Action:
    status: str = "pending"
    elapsed: F = F(0)
    since: F = F(0)
    started: F | None = None
    initial: object = None
    ideal_initial: object = None
    targets: tuple[float, float] | None = None
    terminal: dict | None = None
    rotation_error: F = F(0)

    def elapsed_at(self, time):
        return self.elapsed + (time - self.since if self.status == "running" else 0)


@dataclass
class _Anchor:
    time: F
    since: F
    actual: PoseEnclosure
    ideal: PoseEnclosure
    position_error: F = F(0)
    rotation_error: F = F(0)
    velocity_error: F = F(0)
    omega_error: F = F(0)
    source_time: F | None = None


@dataclass
class _ForceHistory:
    active: dict = field(default_factory=dict)
    net: tuple = (0.0, 0.0, 0.0)
    acceleration: tuple | None = None
    ideal_acceleration: tuple | None = None
    started: int = 0
    completed: int = 0
    last_time: F | None = None
    changes: list = field(default_factory=list)


@dataclass
class _State:
    modes: dict = field(default_factory=dict)
    positions: dict = field(default_factory=dict)
    orientations: dict = field(default_factory=dict)
    ideal_positions: dict = field(default_factory=dict)
    ideal_orientations: dict = field(default_factory=dict)
    coordinates: dict = field(default_factory=dict)
    ideal_coordinates: dict = field(default_factory=dict)
    actions: dict = field(default_factory=dict)
    claims: dict = field(default_factory=dict)
    grips: set = field(default_factory=set)
    dynamic: dict = field(default_factory=dict)
    forces: dict = field(default_factory=dict)
    impulses: dict = field(default_factory=dict)
    rotation_errors: dict = field(default_factory=dict)


@dataclass(frozen=True)
class _SourceBound:
    extent: F = F(0)
    offset: F = F(0)
    trig: int = 0
    products: int = 0
    vectors: int = 0
    coordinate: F = F(0)
    anchor_position: F = F(0)
    anchor_rotation: F = F(0)
    position_error: F = F(0)
    rotation_error: F = F(0)
    velocity_error: F = F(0)
    omega_error: F = F(0)
    speed: F = F(0)
    acceleration: F = F(0)
    omega: F = F(0)
    alpha: F = F(0)
    actual_speed: F = F(0)
    actual_omega: F = F(0)


def _plain(value, arithmetic):
    arithmetic.tick()
    if value is None or isinstance(value, (str, bool, int, float, F, Interval)):
        return value
    if is_dataclass(value):
        return {entry.name: _plain(getattr(value, entry.name), arithmetic) for entry in fields(value)}
    if isinstance(value, dict):
        return {key: _plain(item, arithmetic) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item, arithmetic) for item in value]
    raise ReferenceError("unsupported", "Independent reference encountered an unsupported source record",
                         value_type=type(value).__name__)


class ReachReference:
    """A bounded event ledger plus independent mathematical pose evaluation.

    The captured model is private.  Returned phase records are frozen and all
    returned source projections are fresh values, so consumer changes cannot
    alter later independent expectations.
    """
    def __init__(self, model, *, end, arithmetic, end_side="after", mode="recording"):
        if (model.profile != "planar-reach-0.1" or end < 0 or end > model.duration
                or end_side not in ("before", "after") or mode not in ("recording", "observation")):
            raise ReferenceError("unsupported", "Independent reference requires a valid planar reach prefix")
        self.a, self.p = arithmetic, _PoseArithmetic(arithmetic)
        self.end, self.end_side, self.mode = end, end_side, mode
        self.model = copy.copy(model)
        for name in ("objects", "sites", "joints", "follows", "actions", "source_provenance"):
            collection = getattr(model, name)
            captured = {}
            for key, value in collection.items():
                arithmetic.tick()
                captured[key] = copy.deepcopy(value)
            setattr(self.model, name, captured)
        self.model.events = []
        for block in model.events:
            arithmetic.tick()
            self.model.events.append(copy.deepcopy(block))
        self.model.events.sort(key=lambda block: block.time)
        self._targets, self._poses, self._phase_cache, self._basis_cache = {}, {}, {}, {}
        self._state, self._records, self._before, self._after = _State(), [], [], []
        self._times, self._release_records = [], {}
        self._event_index = 0
        self._initialize()
        self._reach_history_weight = self._maximum_reach_weight() if mode == "recording" else None
        self._inherited_history_cache = {}
        self._history_weight = 0
        self._geometry = self._capture_geometry() if mode == "recording" else None
        self._build()
        self.boundaries = tuple(self._times)

    def _capture_geometry(self):
        return tuple({"path": path, "element_id": list(obj.element_id), "owner": obj.owner,
                      "geometry": _plain(obj.geometry, self.a), "appearance": list(obj.appearance),
                      "physical": _plain(obj.physical, self.a), "placement": _plain(obj.placement, self.a)}
                     for path, obj in self.model.objects.items())

    def _geometry_values(self):
        self.a.tick()
        if self._geometry is None:
            self._geometry = self._capture_geometry()
        return self._geometry

    @property
    def geometry_expectations(self):
        return copy.deepcopy(self._geometry_values())

    def _initialize(self):
        state = self._state
        for path, obj in self.model.objects.items():
            self.a.tick()
            state.modes[path] = obj.motion
            state.positions[path] = self.p.vector(obj.placement.position)
            state.orientations[path] = self.p.quaternion(obj.placement.rotation)
            state.ideal_positions[path] = state.positions[path]
            state.ideal_orientations[path] = state.orientations[path]
            state.rotation_errors[path] = F(0)
            state.forces[path] = _ForceHistory(acceleration=tuple(self.model.gravity) if obj.motion == "dynamic" else None,
                ideal_acceleration=tuple(F(x) for x in self.model.gravity) if obj.motion == "dynamic" else None)
            state.impulses[path] = {"applied_count": 0, "last_application_time_seconds": None, "last_applications": []}
            if obj.motion == "dynamic":
                pose = self.p.make(obj.placement.position, obj.placement.rotation, obj.velocity, obj.omega)
                state.dynamic[path] = _Anchor(F(0), F(0), pose, pose)
        for path, joint in self.model.joints.items():
            self.a.tick()
            if joint.initial is not None:
                state.coordinates[path] = joint.initial
                state.ideal_coordinates[path] = F(joint.initial)
            if joint.kind == "grip":
                state.grips.add(path)
        state.actions = {path: _Action() for path in self.model.actions}
        for action in self.model.actions.values():
            if action.kind == "reach_planar":
                self._validate_chain(action)

    def _validate_chain(self, action):
        self.a.tick()
        payload = action.reach
        shoulder, elbow = (self.model.joints[path] for path in (payload.shoulder, payload.elbow))
        parent, upper, hinge, forearm, tip = (self.model.sites[path] for path in
            (shoulder.parent, shoulder.child, elbow.parent, elbow.child, payload.tip))
        identity = (1.0, 0.0, 0.0, 0.0)
        conditions = (
            shoulder.kind == elbow.kind == "hinge", shoulder.axis == elbow.axis == (0.0, 0.0, 1.0),
            len({parent.owner, upper.owner, forearm.owner}) == 3, upper.owner == hinge.owner,
            forearm.owner == tip.owner, upper.pose.position == forearm.pose.position == (0.0, 0.0, 0.0),
            upper.pose.rotation == hinge.pose.rotation == forearm.pose.rotation == tip.pose.rotation == identity,
            hinge.pose.position[1:] == tip.pose.position[1:] == (0.0, 0.0),
            tuple(payload.lengths_m) == (hinge.pose.position[0], tip.pose.position[0]),
            tuple(payload.limits_rad) == (shoulder.limits, elbow.limits),
            payload.base_frame == shoulder.parent + ".frame" == payload.target_frame,
        )
        if not all(conditions):
            raise ReferenceError("source_identity", "Independent source geometry does not establish the claimed planar chain")

    def _copy_state(self, state):
        # Account for the actual retained state closure before allocating it.
        entries = (len(state.modes) * 11 + len(state.coordinates) + len(state.claims)
                   + len(state.actions) * 9 + sum(len(x.active) + len(x.changes) for x in state.forces.values()))
        if entries * (len(self._times) + 1) > 100000:
            raise ReferenceError("resource", "Independent reference retained-state limit exceeded")
        for _ in range(entries):
            self.a.tick()
        return copy.deepcopy(state)

    def _incoming(self, state):
        result = {}
        for path, joint in self.model.joints.items():
            self.a.tick()
            if joint.kind != "grip" or path in state.grips:
                result[self.model.sites[joint.child].owner] = ("joint", path)
        for path, follow in self.model.follows.items():
            self.a.tick()
            result[follow.child] = ("follow", path)
        return result

    def _owner(self, frame):
        if frame == "world":
            return None
        path = frame.removesuffix(".frame")
        return path if path in self.model.objects else self.model.sites[path].owner

    def _channel(self, action):
        return (action.target, {"move": "translation", "spin": "orientation", "tween": "coordinate"}[action.kind])

    def _coordinate(self, joint, time, state, *, ideal=False):
        self.a.tick()
        owner = state.claims.get((joint, "coordinate"))
        if owner is None:
            return F((state.ideal_coordinates if ideal else state.coordinates)[joint]), F(0)
        action, active = self.model.actions[owner], state.actions[owner]
        index = (action.reach.shoulder, action.reach.elbow).index(joint) if action.kind == "reach_planar" else None
        start = active.ideal_initial if ideal else active.initial
        initial = F(start[index] if index is not None else start)
        target = F(active.targets[index] if index is not None else action.goal)
        slope = self.a.exact(self.a.exact(target, initial, "sub"), action.duration, "div")
        coordinate = self.a.exact(initial, self.a.exact(slope, active.elapsed_at(time), "mul"), "add")
        if not ideal:
            coordinate = F(self.a.round64(coordinate))
        return coordinate, slope if active.status == "running" else F(0)

    def _root_pose(self, path, time, state, *, ideal, pose_only=False):
        if state.modes[path] == "dynamic":
            anchor = state.dynamic[path]
            saved = anchor.ideal if ideal else anchor.actual
            dt = time - anchor.time
            acceleration = ((state.forces[path].ideal_acceleration if ideal else state.forces[path].acceleration)
                            or self.model.gravity)
            position = self.p.add(self.p.add(saved.position, self.p.scale(saved.velocity, dt)),
                                  self.p.scale(acceleration, dt * dt / 2))
            rotation = self.p.multiply(self.p.spin(saved.omega, dt), saved.orientation)
            if pose_only:
                zero = self.p.vector(ZERO)
                return PoseEnclosure(position, rotation, zero, zero)
            return PoseEnclosure(position, rotation, self.p.add(saved.velocity, self.p.scale(acceleration, dt)), saved.omega)
        position = (state.ideal_positions if ideal else state.positions)[path]
        orientation = (state.ideal_orientations if ideal else state.orientations)[path]
        velocity, omega = self.p.vector(ZERO), self.p.vector(ZERO)
        move = state.claims.get((path, "translation"))
        if move is not None:
            action, active = self.model.actions[move], state.actions[move]
            initial = active.ideal_initial if ideal else active.initial
            position = self.p.add(initial, self.p.scale(action.vector, active.elapsed_at(time)))
            if not pose_only and active.status == "running":
                velocity = self.p.vector(action.vector)
        spin = state.claims.get((path, "orientation"))
        if spin is not None:
            action, active = self.model.actions[spin], state.actions[spin]
            initial = active.ideal_initial if ideal else active.initial
            orientation = self.p.multiply(self.p.spin(action.vector, active.elapsed_at(time)), initial)
            if not pose_only and active.status == "running":
                omega = self.p.vector(action.vector)
        return PoseEnclosure(position, orientation, velocity, omega)

    def _pose_map(self, time, state, *, ideal, pose_only=False, selected=None):
        key = (id(state), time, ideal, pose_only)
        targets = (tuple(path + ".frame" for path in (*self.model.objects, *self.model.sites))
                   if selected is None else tuple(selected))
        self.a.tick()
        cached = self._poses.get(key)
        if cached is not None and cached[0] is state:
            frames = cached[1]
            if all(path in frames for path in targets):
                return frames
        else:
            frames = {"world": self.p.identity()}
        incoming = self._incoming(state)
        visiting = set()

        def frame(path):
            self.a.tick()
            if path in frames:
                return frames[path]
            stem = path.removesuffix(".frame")
            if stem in self.model.sites:
                site = self.model.sites[stem]
                value = self.p.compose(frame(site.owner + ".frame"), self.p.constant(site.pose))
            else:
                if stem in visiting or len(visiting) > 128:
                    raise ReferenceError("unsupported", "Independent source frame graph is cyclic or too deep")
                visiting.add(stem)
                if stem in incoming:
                    kind, relation = incoming[stem]
                    if kind == "follow":
                        follow = self.model.follows[relation]
                        value = self.p.compose(frame(follow.parent), self.p.constant(follow.offset))
                    else:
                        joint = self.model.joints[relation]
                        value = frame(joint.parent + ".frame")
                        if joint.kind in {"hinge", "slider"}:
                            coordinate, rate = self._coordinate(relation, time, state, ideal=ideal)
                            if pose_only:
                                rate = F(0)
                            motion = (self.p.hinge(joint.axis, coordinate, rate, ideal=ideal) if joint.kind == "hinge" else
                                      self.p.make(self.p.scale(joint.axis, coordinate), velocity=self.p.scale(joint.axis, rate)))
                            value = self.p.compose(value, motion)
                        value = self.p.compose(value, self.p.inverse(self.p.constant(self.model.sites[joint.child].pose)))
                else:
                    value = self._root_pose(stem, time, state, ideal=ideal, pose_only=pose_only)
                visiting.remove(stem)
            frames[path] = value
            return value

        for path in targets:
            frame(path)
        if len(self._poses) < MAX_CACHE:
            self._poses[key] = (state, frames)
        return frames

    def _state_at(self, time, side):
        time = F(time)
        if side not in {"before", "after"} or not 0 <= time <= self.end:
            raise ReferenceError("unsupported", "Reference sample is outside its certified prefix")
        if time == self.end and side == "after" and self.end_side == "before":
            raise ReferenceError("unsupported", "The final after-side is outside this incoming-only reference")
        index = bisect_left(self.boundaries, time)
        if index < len(self.boundaries) and self.boundaries[index] == time:
            return (self._before if side == "before" else self._after)[index]
        return self._after[index - 1]

    def pose_enclosure(self, carrier, time, side="after", *, ideal=True):
        """Return the independent mathematical pose, without source roundoff inflation."""
        carrier = carrier if carrier == "world" or carrier.endswith(".frame") else carrier + ".frame"
        state = self._state_at(F(time), side)
        try:
            return self._pose_map(F(time), state, ideal=ideal, selected=(carrier,))[carrier]
        except KeyError as error:
            raise ReferenceError("identity", "Unknown independent source carrier", carrier=carrier) from error

    def recording_pose_enclosure(self, carrier, time, side="after", *, ideal=True):
        """Return one independent recording pose through the bounded batch API."""
        values = self.recording_pose_enclosures((carrier,), time, side, ideal=ideal)
        return next(iter(values.values()))

    def recording_pose_enclosures(self, carriers, time, side="after", *, ideal=True):
        """Evaluate independent p/q once for the selected carrier ancestries.

        The p/q expressions are identical to full pose evaluation. Spatial
        derivatives do not enter those expressions. A separate cache namespace
        and a two-field return type prevent unused private zeros from becoming
        source velocity or release-state evidence. The returned fresh mapping
        uses canonical carrier names and contains no unrequested ancestry rows.
        """
        self.a.tick()
        if not isinstance(carriers, (tuple, list)):
            raise ReferenceError("unsupported", "Recording carriers require a bounded list or tuple")
        if len(carriers) > 1 + len(self.model.objects) + len(self.model.sites):
            raise ReferenceError("resource", "Recording carrier selection exceeds the captured source inventory")
        selected = []
        for carrier in carriers:
            self.a.tick()
            if not isinstance(carrier, str):
                raise ReferenceError("identity", "Unknown independent source carrier", carrier=carrier)
            carrier = carrier if carrier == "world" or carrier.endswith(".frame") else carrier + ".frame"
            stem = carrier.removesuffix(".frame")
            if carrier != "world" and stem not in self.model.objects and stem not in self.model.sites:
                raise ReferenceError("identity", "Unknown independent source carrier", carrier=carrier)
            selected.append(carrier)
        time = F(time)
        state = self._state_at(time, side)
        frames = self._pose_map(time, state, ideal=ideal, pose_only=True, selected=selected)
        return {carrier: RecordingPoseEnclosure(frames[carrier].position, frames[carrier].orientation)
                for carrier in selected}

    def _next(self, state, current):
        times = [self.end]
        if self._event_index < len(self.model.events):
            times.append(self.model.events[self._event_index].time)
        for path, active in state.actions.items():
            self.a.tick()
            if active.status == "running":
                times.append(active.since + self.model.actions[path].duration - active.elapsed)
        for history in state.forces.values():
            for force in history.active.values():
                self.a.tick()
                times.append(force[1] + force[0].duration)
        later = [time for time in times if time > current]
        return min(later) if later else None

    def _build(self):
        time = F(0)
        while True:
            self.a.tick()
            if len(self._times) >= MAX_BOUNDARIES:
                raise ReferenceError("resource", "Independent semantic boundary cap exceeded")
            incoming_only = time == self.end and self.end_side == "before"
            if self.mode == "recording":
                weight = (1 + self._inherited_weight(time, "before") + self._reach_history_weight
                          if incoming_only else self._boundary_weight(time))
                self._history_weight += weight
                if self._history_weight > 100000:
                    raise ReferenceError("resource", "Independent complete H06 source histories exceed 100000 weighted records",
                                         budget="boundary_state_records", consumed=self._history_weight)
            # Every transition below writes only the staged deep copy. The
            # incoming state is the already retained immutable prior state;
            # copying it again repeats a whole source traversal and allocation
            # without creating a distinct semantic value. H06 still counts
            # each repeated before/after record separately.
            before = self._state
            if incoming_only:
                # No natural completion, force change, authored event or
                # staged validation belongs to the requested final side.
                # Retain an explicit unavailable sentinel, never a fabricated
                # after-state that a later query could mistake for evidence.
                self._times.append(time)
                self._before.append(before)
                self._after.append(None)
                self._release_records[time] = ()
                break
            staged = self._copy_state(self._state)
            releases = []
            for path, active in staged.actions.items():
                self.a.tick()
                if active.status == "running" and active.elapsed_at(time) == self.model.actions[path].duration:
                    self._finish(path, time, staged, "completed")
            for path, history in staged.forces.items():
                for key in sorted(tuple(history.active)):
                    self.a.tick()
                    payload, start = history.active[key]
                    if start + payload.duration == time:
                        del history.active[key]
                        history.completed += 1
                        self._force_change(history, time, "completed", (payload, start))
            touched = set()
            if self._event_index < len(self.model.events) and self.model.events[self._event_index].time == time:
                for index, event in enumerate(self.model.events[self._event_index].events):
                    self.a.tick()
                    self._event(event, index, time, staged, before, touched, releases)
                self._event_index += 1
            for path in staged.forces:
                self._aggregate(path, time, staged)
            self._state = staged
            self._times.append(time)
            self._before.append(before)
            self._after.append(staged)
            self._release_records[time] = tuple(releases)
            if time == self.end:
                break
            following = self._next(staged, time)
            if following is None or following > self.end:
                following = self.end
            if following <= time:
                raise ReferenceError("source_admission", "Independent event ledger failed to advance")
            time = following

    def _round_vector(self, vector):
        result = []
        for value in vector:
            self.a.tick()
            # An interval may enclose more than one materialized float.  Keep
            # that uncertainty rather than selecting an unproved midpoint.
            lo, hi = float(value.lo), float(value.hi)
            if not math.isfinite(lo) or not math.isfinite(hi):
                raise ReferenceError("numeric", "Independent materialized source vector is nonfinite")
            result.append(Interval(F(lo), F(hi)))
        return tuple(result)

    def _finish(self, path, time, state, status):
        action, active = self.model.actions[path], state.actions[path]
        if action.kind in {"reach_planar", "tween"}:
            joints = (action.reach.shoulder, action.reach.elbow) if action.kind == "reach_planar" else (action.target,)
            coordinates = tuple(self._coordinate(joint, time, state)[0] for joint in joints)
            ideal_coordinates = tuple(self._coordinate(joint, time, state, ideal=True)[0] for joint in joints)
            for joint, coordinate, ideal in zip(joints, coordinates, ideal_coordinates):
                state.coordinates[joint] = float(coordinate)
                state.ideal_coordinates[joint] = ideal
                del state.claims[(joint, "coordinate")]
            if action.kind == "reach_planar":
                tip = self._base_tip(action, coordinates)
                residual = self._residual(tip.position, action.reach.target_m)
                if status == "completed" and residual.hi > F(1, 10**9):
                    raise ReferenceError("numeric", "Independent completed reach fails the source residual bound")
                active.terminal = {"outcome": "satisfied" if status == "completed" else "interrupted",
                                   "time_seconds": _time_text(time), "position_residual_m": residual,
                                   "joint_coordinates_rad": [float(x) for x in coordinates],
                                   "tip_pose_base": self._pose_record(tip)}
        elif action.kind == "move":
            elapsed = active.elapsed_at(time)
            state.positions[action.target] = self._round_vector(self.p.add(active.initial, self.p.scale(action.vector, elapsed)))
            state.ideal_positions[action.target] = self.p.add(active.ideal_initial, self.p.scale(action.vector, elapsed))
            del state.claims[self._channel(action)]
        elif action.kind == "spin":
            elapsed = active.elapsed_at(time)
            state.rotation_errors[action.target] = self._source_basis(action.target + ".frame", time, time, state).rotation_error
            state.orientations[action.target] = self.p.multiply(self.p.spin(action.vector, elapsed), active.initial)
            state.ideal_orientations[action.target] = self.p.multiply(self.p.spin(action.vector, elapsed), active.ideal_initial)
            del state.claims[self._channel(action)]
        else:
            raise ReferenceError("unsupported", "Independent action kind is unsupported", kind=action.kind)
        active.elapsed = active.elapsed_at(time)
        active.status = status
        self._poses.clear()
        self._basis_cache.clear()

    def _event(self, event, sequence_index, time, state, incoming, touched, releases):
        self._poses.clear()
        self._basis_cache.clear()
        if event.kind == "release":
            self._release(event, sequence_index, time, state, incoming, touched, releases)
            return
        if event.kind == "force":
            self._dynamic_admission(event.target, state)
            payload = event.force
            if payload is None:
                raise ReferenceError("source_admission", "Independent force has no source payload")
            history = state.forces[event.target]
            if payload.key in history.active:
                raise ReferenceError("source_admission", "Independent force key is already active")
            history.active[payload.key] = (payload, time)
            history.started += 1
            self._force_change(history, time, "started", (payload, time))
            return
        if event.kind == "impulse":
            self._impulse(event, time, state, touched)
            return
        if event.kind not in {"start", "pause", "resume", "stop"} or event.target not in state.actions:
            raise ReferenceError("unsupported", "Unknown independent lifecycle event")
        action, active = self.model.actions[event.target], state.actions[event.target]
        allowed = {"start": {"pending"}, "pause": {"running"}, "resume": {"paused"}, "stop": {"running", "paused"}}
        if active.status not in allowed[event.kind]:
            raise ReferenceError("source_admission", "Independent lifecycle transition is invalid")
        if action.kind == "reach_planar":
            channels = ((action.reach.shoulder, "coordinate"), (action.reach.elbow, "coordinate"))
        else:
            channels = (self._channel(action),)
        if event.kind == "start":
            if any(channel in state.claims for channel in channels):
                raise ReferenceError("source_admission", "Independent action admission conflicts with an active owner")
            if action.kind == "reach_planar":
                payload = action.reach
                key = (tuple(payload.lengths_m), tuple(payload.target_m), payload.branch, tuple(payload.limits_rad))
                self.a.tick()
                if key not in self._targets:
                    self._targets[key] = _canonical_targets(payload, self.a)
                active.targets = self._targets[key]
                residual = self._residual(self._base_tip(action, active.targets).position, payload.target_m)
                if residual.hi > F(1, 10**9):
                    raise ReferenceError("numeric", "Independent admitted targets fail their residual bound")
                active.initial = tuple(state.coordinates[joint] for joint, _ in channels)
                active.ideal_initial = tuple(state.ideal_coordinates[joint] for joint, _ in channels)
            elif action.kind == "tween":
                joint = self.model.joints[action.target]
                if not joint.limits[0] <= action.goal <= joint.limits[1]:
                    raise ReferenceError("source_admission", "Independent tween target exceeds closed limits")
                active.initial = state.coordinates[action.target]
                active.ideal_initial = state.ideal_coordinates[action.target]
            else:
                if state.modes[action.target] != "prescribed" or action.target in self._incoming(state):
                    raise ReferenceError("source_admission", "Independent root action has no free prescribed authority")
                active.initial = (state.positions if action.kind == "move" else state.orientations)[action.target]
                active.ideal_initial = (state.ideal_positions if action.kind == "move" else state.ideal_orientations)[action.target]
                if action.kind == "spin":
                    active.rotation_error = state.rotation_errors[action.target]
            active.started, active.since, active.elapsed, active.status = time, time, F(0), "running"
            for channel in channels:
                state.claims[channel] = event.target
        elif event.kind == "pause":
            active.elapsed, active.status = active.elapsed_at(time), "paused"
        elif event.kind == "resume":
            active.since, active.status = time, "running"
        else:
            self._finish(event.target, time, state, "stopped")
        for target, channel in channels:
            touched.add(("joint" if channel == "coordinate" else "object", target))

    def _force_change(self, history, time, kind, force):
        if history.last_time != time:
            history.last_time, history.changes = time, []
        history.changes.append((kind, force))

    def _aggregate(self, path, time, state):
        self.a.tick()
        history = state.forces[path]
        if state.modes[path] != "dynamic":
            history.acceleration = None
            return
        sums = [F(0), F(0), F(0)]
        for key in sorted(history.active):
            payload, _ = history.active[key]
            sums = [self.a.exact(value, component, "add") for value, component in zip(sums, payload.force_world_n)]
        net = tuple(self.a.round64(value) for value in sums)
        mass = F(self.model.objects[path].mass)
        acceleration = tuple(self.a.round64(self.a.exact(gravity, self.a.exact(force, mass, "div"), "add"))
                             for gravity, force in zip(self.model.gravity, net))
        ideal_acceleration = tuple(self.a.exact(gravity, self.a.exact(force, mass, "div"), "add")
                                   for gravity, force in zip(self.model.gravity, sums))
        previous = history.acceleration or tuple(self.model.gravity)
        previous_ideal = history.ideal_acceleration or tuple(F(x) for x in self.model.gravity)
        changed = history.last_time == time or history.acceleration is None
        if changed or acceleration != previous or ideal_acceleration != previous_ideal:
            original = state.dynamic[path]
            actual, ideal = self._root_pose(path, time, state, ideal=False), self._root_pose(path, time, state, ideal=True)
            # Capture the *old* phase before installing its new acceleration.
            # Its point basis includes Ea*T and Ea*T^2/2 as well as incoming
            # anchor errors; keeping only the original errors loses the force
            # arithmetic discrepancy at every completion or replacement.
            before = self._source_basis(path + ".frame", time, time, state)
            position_error, rotation_error = before.position_error, before.rotation_error
            velocity_error, omega_error = before.velocity_error, before.omega_error
            if acceleration != previous:
                # A changed canonical acceleration freezes the current public
                # source tuple. The orientation then denotes that tuple's
                # projective rotation, rather than an unnormalised unit q.
                actual = PoseEnclosure(self._round_vector(actual.position),
                    self.p.quaternion(self._expand_vector(ideal.orientation, rotation_error, rounded=True)),
                    self._round_vector(actual.velocity), self._round_vector(actual.omega))
            else:
                # Equal canonical acceleration retains the private trajectory.
                # Convert the old public-point error back to it using a proved
                # binary64 publication bound. Source and proof clocks differ.
                def publication(vector):
                    return self.a.exact(self.a.exact(self._l1(vector), F(1, 1 << 53), "mul"),
                                        F(3, 1 << 1075), "add")
                position_error = self.a.exact(position_error, publication(actual.position), "add")
                velocity_error = self.a.exact(velocity_error, publication(actual.velocity), "add")
                rotation_error = self.a.exact(rotation_error, F(1, 1 << 50), "add")
            state.dynamic[path] = _Anchor(time, original.since, actual, ideal,
                position_error, rotation_error, velocity_error, omega_error,
                time if acceleration != previous else (original.time if original.source_time is None else original.source_time))
        history.net, history.acceleration, history.ideal_acceleration = net, acceleration, ideal_acceleration
        self._poses.clear()
        self._basis_cache.clear()

    def _dynamic_admission(self, path, state):
        self.a.tick()
        obj = self.model.objects.get(path)
        if (obj is None or state.modes[path] != "dynamic" or path in self._incoming(state)
                or obj.physical.get("kind") != "sphere_body" or obj.mass <= 0 or not obj.inertia or obj.inertia <= 0):
            raise ReferenceError("source_admission", "Independent influence requires a free positive-mass dynamic sphere")

    def _occurrence(self, path):
        for collection in (self.model.actions, self.model.joints, self.model.sites, self.model.objects):
            if path in collection:
                return {"path": path, "element_id": list(collection[path].element_id)}
        raise ReferenceError("identity", "Independent source occurrence is unknown", path=path)

    def _dependencies(self, child, state):
        incoming, result = self._incoming(state), set()
        while child is not None:
            self.a.tick()
            if ("object", child) in result:
                raise ReferenceError("unsupported", "Independent release dependency graph contains a cycle")
            result.add(("object", child))
            if child not in incoming:
                break
            kind, relation = incoming[child]
            result.add((kind, relation))
            child = (self.model.sites[self.model.joints[relation].parent].owner if kind == "joint" else
                     self._owner(self.model.follows[relation].parent))
        return result

    def _expand_vector(self, vector, error, *, rounded=False):
        result = tuple(self.a.add(value, Interval(-error, error)) for value in vector)
        return self._round_vector(result) if rounded else result

    def _release(self, event, index, time, state, incoming, touched, releases):
        joint = self.model.joints.get(event.target)
        if joint is None or joint.kind != "grip" or event.target not in state.grips:
            raise ReferenceError("source_admission", "Independent release requires an active grip")
        child = self.model.sites[joint.child].owner
        dependencies = self._dependencies(child, incoming)
        if dependencies & touched:
            raise ReferenceError("source_admission", "Earlier statements changed independent incoming release dependencies")
        obj = self.model.objects[child]
        if state.modes[child] != "prescribed" or obj.physical.get("kind") != "sphere_body":
            raise ReferenceError("source_admission", "Independent grip child is not a prescribed physical sphere")
        actual = self._pose_map(time, incoming, ideal=False)[child + ".frame"]
        ideal = self._pose_map(time, incoming, ideal=True)[child + ".frame"]
        bound = self._phase(child + ".frame", time, time, incoming)
        materialized = PoseEnclosure(
            self._expand_vector(actual.position, bound.source_numeric_position_error, rounded=True),
            self.p.quaternion(self._expand_vector(actual.orientation,
                bound.source_numeric_rotation_error, rounded=True)),
            self._expand_vector(actual.velocity, bound.source_numeric_velocity_error, rounded=True),
            self._expand_vector(actual.omega, bound.source_numeric_angular_velocity_error, rounded=True))
        state.dynamic[child] = _Anchor(time, time, materialized, ideal,
            bound.source_numeric_position_error, bound.source_numeric_rotation_error,
            bound.source_numeric_velocity_error, bound.source_numeric_angular_velocity_error)
        state.grips.remove(event.target)
        state.modes[child] = "dynamic"
        contributors = []
        for path, action in self.model.actions.items():
            self.a.tick()
            active = incoming.actions[path]
            if action.kind != "reach_planar" or active.status != "running":
                continue
            payload = action.reach
            if not dependencies.intersection({("joint", payload.shoulder), ("joint", payload.elbow)}):
                continue
            pair = [self._coordinate(name, time, incoming) for name in (payload.shoulder, payload.elbow)]
            contributors.append({"action": self._occurrence(path), "shoulder": self._occurrence(payload.shoulder),
                "elbow": self._occurrence(payload.elbow), "joint_coordinates_rad": [float(item[0]) for item in pair],
                "joint_rates_rad_per_s": [self.a.round64(item[1]) for item in pair]})
        node = event.span
        source = self.model.source_provenance[node.source_id]
        releases.append({"program_revision": self.model.program_revision,
            "source_location": {"source_id": node.source_id, "source_revision": source["source_revision"],
                                "start_byte": node.start, "end_byte": node.end},
            "sequence_index": index, "time_seconds": _time_text(time), "grip": self._occurrence(event.target),
            "target": self._occurrence(child), "reach_contributors": contributors,
            "incoming_pose_world": self._pose_record(actual),
            "incoming_linear_velocity_world_m_per_s": list(actual.velocity),
            "incoming_angular_velocity_world_rad_per_s": list(actual.omega)})
        touched.update({("joint", event.target), ("object", child)})
        self._poses.clear()
        self._basis_cache.clear()

    def _impulse(self, event, time, state, touched):
        self._dynamic_admission(event.target, state)
        obj, payload = self.model.objects[event.target], event.impulse
        if payload is None:
            raise ReferenceError("source_admission", "Independent impulse has no source operands")
        ideal = self._root_pose(event.target, time, state, ideal=True)
        bound = self._phase(event.target + ".frame", time, time, state)
        # These are source-output enclosures, in each field's physical units.
        # A current controlled pose differs from the independent ideal pose
        # even when the exact mathematical rotation would round identically.
        # Propagate its proved errors before the impulse operations rather
        # than adding an unrelated global position/angle tolerance afterward.
        position = self._expand_vector(ideal.position, bound.source_numeric_position_error, rounded=True)
        orientation = self._expand_vector(ideal.orientation, bound.source_numeric_rotation_error, rounded=True)
        before_velocity = self._expand_vector(ideal.velocity, bound.source_numeric_velocity_error, rounded=True)
        before_omega = self._expand_vector(ideal.omega, bound.source_numeric_angular_velocity_error, rounded=True)
        ideal_lever = self.p.rotate(ideal.orientation, payload.point_self_m)
        lever_error = self.a.exact(self.a.exact(bound.source_numeric_rotation_error,
            self._l1(payload.point_self_m), "mul"), F(1, 1 << 96), "add")
        lever = self._expand_vector(ideal_lever, lever_error, rounded=True)
        point = self._round_vector(self.p.add(position, lever))
        angular = self._round_vector(self.p.cross(lever, self.p.vector(payload.impulse_world_n_s)))
        inverse_mass = self.a.exact(1, obj.mass, "div")
        inverse_inertia = self.a.exact(1, obj.inertia, "div")
        delta = self.p.scale(payload.impulse_world_n_s, inverse_mass)
        velocity = self._round_vector(self.p.add(before_velocity, delta))
        omega = self._round_vector(self.p.add(before_omega, self.p.scale(angular, inverse_inertia)))
        ideal_velocity = self.p.add(ideal.velocity, delta)
        ideal_omega = self.p.add(ideal.omega,
            self.p.scale(self.p.cross(ideal_lever, self.p.vector(payload.impulse_world_n_s)), inverse_inertia))
        if any(payload.impulse_world_n_s):
            original = state.dynamic[event.target]
            state.dynamic[event.target] = _Anchor(time, original.since,
                PoseEnclosure(position, self.p.quaternion(orientation), velocity, omega),
                PoseEnclosure(ideal.position, ideal.orientation, ideal_velocity, ideal_omega),
                bound.source_numeric_position_error, bound.source_numeric_rotation_error,
                self._distance(velocity, ideal_velocity), self._distance(omega, ideal_omega))
            touched.add(("object", event.target))
        history = state.impulses[event.target]
        if history["last_application_time_seconds"] != _time_text(time):
            history["last_application_time_seconds"] = _time_text(time)
            history["last_applications"] = []
        history["applied_count"] += 1
        history["last_applications"].append({"sequence_index": payload.sequence_index,
            "source_location": dict(payload.source), "target_element_id": list(obj.element_id), "target_path": event.target,
            "impulse_world_n_s": list(payload.impulse_world_n_s), "application_point_self_m": list(payload.point_self_m),
            "lever_arm_world_m": list(lever), "application_point_world_m": list(point),
            "angular_impulse_world_n_m_s": list(angular), "linear_velocity_before_world_m_per_s": list(before_velocity),
            "linear_velocity_after_world_m_per_s": list(velocity), "angular_velocity_before_world_rad_per_s": list(before_omega),
            "angular_velocity_after_world_rad_per_s": list(omega)})
        self._poses.clear()
        self._basis_cache.clear()

    def _base_tip(self, action, coordinates):
        coordinates = tuple(coordinates)
        key = self.p._key("base_tip", tuple(action.reach.lengths_m), coordinates)
        cached = self.a.lookup(key)
        if cached is not None:
            return cached
        first, second = coordinates
        sine1, cosine1 = self.a.sincos(first)
        sine2, cosine2 = self.a.sincos(self.a.exact(first, second, "add"))
        a, b = action.reach.lengths_m
        position = (self.a.add(self.a.mul(a, cosine1), self.a.mul(b, cosine2)),
                    self.a.add(self.a.mul(a, sine1), self.a.mul(b, sine2)), self.a.point(0))
        rotation = self.p.hinge((0, 0, 1), self.a.exact(first, second, "add"), 0).orientation
        return self.a.remember(key, self.p.make(position, rotation, normalized=True))

    def _residual(self, position, target):
        position, target = tuple(position), tuple(target)
        key = self.p._key("residual", position, target)
        cached = self.a.lookup(key)
        if cached is not None:
            return cached
        difference = tuple(self.a.sub(value, expected) for value, expected in zip(position, target))
        return self.a.remember(key, self.p.norm(difference))

    def _world_target(self, base, target):
        """Reuse only the immutable numerical operands of a world target."""
        target = tuple(target)
        key = self.p._key("world_target", base, target)
        cached = self.a.lookup(key)
        if cached is not None:
            return cached
        return self.a.remember(key, self.p.compose(base, self.p.make(target)))

    def _joint_observation(self, path, time, state, observations):
        """One sample's exact joint value and its public binary64 projection."""
        self.a.tick()
        cached = observations.get(path)
        if cached is not None:
            return cached
        coordinate, rate = self._coordinate(path, time, state)
        value = (coordinate, rate, float(coordinate), self.a.round64(rate))
        if len(observations) < MAX_CACHE:
            self.a.tick()
            observations[path] = value
        return value

    @staticmethod
    def _pose_record(pose):
        return {"position_m": list(pose.position), "orientation_wxyz": list(pose.orientation)}

    def sample(self, time, side="after"):
        time = F(time)
        state = self._state_at(time, side)
        if self._reach_history_weight is None:
            # Rate-only callers never request this complete reach projection.
            # A later sample must still pass its original capacity guard before
            # constructing any public sample rows.
            self._reach_history_weight = self._maximum_reach_weight()
        frames, incoming = self._pose_map(time, state, ideal=False), self._incoming(state)
        objects = {}
        geometry = {entry["path"]: entry for entry in
                    (self._geometry_values() if self._geometry is None else self._geometry)}
        for path, obj in self.model.objects.items():
            self.a.tick()
            pose, mode = frames[path + ".frame"], state.modes[path]
            if path in incoming:
                kind, relation = incoming[path]
                authority = {"kind": kind, "relation": relation}
            elif mode == "dynamic":
                anchor = state.dynamic[path]
                authority = {"kind": "free_sphere", "since_seconds": _time_text(anchor.since),
                             "trajectory_anchor_seconds": _time_text(anchor.time if anchor.source_time is None else anchor.source_time)}
            else:
                authority = {"kind": mode, "translation_action": state.claims.get((path, "translation")),
                             "orientation_action": state.claims.get((path, "orientation"))}
            mass = self.a.exact(0, 0, "add")
            for owned in self.model.objects.values():
                if owned.path == path or owned.path.startswith(path + "."):
                    mass = self.a.exact(mass, owned.mass, "add")
            gravity = ("active_dynamic" if mode == "dynamic" else
                       "inactive_prescribed" if mode == "prescribed" and obj.mass else
                       "inactive_static" if mode == "static" and obj.mass else "no_body")
            objects[path] = {"element_id": list(obj.element_id), "kind": "object", "name": obj.name,
                "class_name": obj.class_name, "owner": obj.owner, "motion": mode,
                "position_m": list(pose.position), "orientation_wxyz": list(pose.orientation),
                "velocity_m_per_s": list(pose.velocity), "angular_velocity_rad_per_s": list(pose.omega),
                "pose_frame": "world", "velocity_measured_in": "world", "velocity_expressed_in": "world",
                "velocity_reference_point": "center_of_mass" if obj.mass else "origin", "pose_authority": authority,
                "own_mass_kg": obj.mass, "owned_aggregate_mass_kg": self.a.round64(mass), "inertia_kg_m2": obj.inertia,
                "geometry": copy.deepcopy(geometry[path]["geometry"]), "physical": copy.deepcopy(geometry[path]["physical"]),
                "gravity_participation": gravity, "collision": obj.collision,
                "impulses": copy.deepcopy(state.impulses[path]), "forces": self._forces(path, state)}
        joints, joint_observations = {}, {}
        for path, joint in self.model.joints.items():
            self.a.tick()
            record = {"element_id": list(joint.element_id), "kind": joint.kind,
                "status": "inactive" if joint.kind == "grip" and path not in state.grips else "active",
                "parent_site": joint.parent, "child_site": joint.child,
                "coupling": "externally_prescribed_no_load_solution"}
            if joint.kind in {"hinge", "slider"}:
                physical = self._joint_observation(path, time, state, joint_observations)
                record.update(coordinate=physical[2], coordinate_rate=physical[3],
                    unit="rad" if joint.kind == "hinge" else "m", limits=list(joint.limits),
                    action=state.claims.get((path, "coordinate")))
            joints[path] = record
        actions = {path: {"element_id": list(action.element_id), "kind": action.kind, "target": action.target,
                         "status": state.actions[path].status, "local_elapsed_seconds": _time_text(state.actions[path].elapsed_at(time)),
                         "duration_seconds": _time_text(action.duration)} for path, action in self.model.actions.items()}
        frame_records = {path: {"position_m": list(value.position), "orientation_wxyz": list(value.orientation),
            "velocity_m_per_s": list(value.velocity), "angular_velocity_rad_per_s": list(value.omega)} for path, value in frames.items()}
        total_mass = F(0)
        for obj in self.model.objects.values():
            total_mass = self.a.exact(total_mass, obj.mass, "add")
        result = {"time_seconds": _time_text(time), "side": side, "objects": objects, "joints": joints,
                  "actions": actions, "frames": frame_records, "scene_mass_kg": self.a.round64(total_mass),
                  "reaches": {path: self._reach(path, time, side, state, frames, joint_observations)
                              for path, action in self.model.actions.items() if action.kind == "reach_planar"}}
        if self.mode == "observation":
            self._logical_entries(result)
        return result

    def _force_record(self, path, force):
        payload, start = force
        return {"force_key": payload.key,
            "force_element_id": [self.model.module_key, self.model.scene_key, "force", payload.key],
            "target_path": path, "target_element_id": list(self.model.objects[path].element_id),
            "program_revision": self.model.program_revision, "source_location": dict(payload.source),
            "sequence_index": payload.sequence_index, "force_world_n": list(payload.force_world_n),
            "activation_time_seconds": _time_text(start), "duration_seconds": _time_text(payload.duration),
            "completion_time_seconds": _time_text(start + payload.duration)}

    def _forces(self, path, state):
        history = state.forces[path]
        return {"active": [self._force_record(path, history.active[key]) for key in sorted(history.active)],
            "net_force_world_n": list(history.net),
            "acceleration_world_m_per_s2": None if history.acceleration is None else list(history.acceleration),
            "started_count": history.started, "completed_count": history.completed,
            "last_change_time_seconds": None if history.last_time is None else _time_text(history.last_time),
            "last_changes": [{"kind": kind, **self._force_record(path, force)} for kind, force in history.changes]}

    def _reach(self, path, time, side, state, frames, joint_observations):
        self.a.tick()
        action, active = self.model.actions[path], state.actions[path]
        payload = action.reach
        physical = [self._joint_observation(joint, time, state, joint_observations)
                    for joint in (payload.shoulder, payload.elbow)]
        coordinates = tuple(value[0] for value in physical)
        tip_base = self._base_tip(action, coordinates)
        target_world = self._world_target(frames[payload.base_frame], payload.target_m)
        admitted = active.targets is not None
        own_rates = [0.0, 0.0]
        if active.status == "running":
            own_rates = [self.a.round64(self.a.exact(self.a.exact(target, initial, "sub"), action.duration, "div"))
                         for target, initial in zip(active.targets, active.initial)]
        completion = (active.since + action.duration - active.elapsed if active.status == "running" else
                      F(active.terminal["time_seconds"]) if active.status == "completed" else None)
        current = {"observation": {"time_seconds": _time_text(time), "side": side, "run_id": None, "context_kind": "recorded_prefix"},
            "lifecycle": active.status,
            "goal_outcome": {"pending": "pending", "running": "active", "paused": "active", "stopped": "interrupted", "completed": "satisfied"}[active.status],
            "resolved_joint_targets_rad": list(active.targets) if admitted else None,
            "start_coordinates_rad": list(active.initial) if admitted else None,
            "start_time_seconds": _time_text(active.started) if admitted else None,
            "elapsed_seconds": _time_text(active.elapsed_at(time)) if admitted else None,
            "completion_time_seconds": None if completion is None else _time_text(completion),
            "joint_coordinates_rad": [value[2] for value in physical],
            "joint_rates_rad_per_s": [value[3] for value in physical],
            "action_joint_rates_rad_per_s": own_rates,
            "claimed_joint_ids": [list(self.model.joints[joint].element_id) for joint in (payload.shoulder, payload.elbow)]
                if active.status in {"running", "paused"} else [],
            "current_residual_m": self._residual(tip_base.position, payload.target_m) if admitted else None,
            "tip_pose_base": self._pose_record(tip_base), "tip_pose_world": self._pose_record(frames[payload.tip + ".frame"]),
            "current_world_target_m": list(target_world.position), "terminal_result": copy.deepcopy(active.terminal)}
        return self._description(path, current)

    def _description(self, path, current):
        action = self.model.actions[path]
        payload = action.reach
        base_site = self.model.sites[payload.base_frame.removesuffix(".frame")]
        frame = {"path": payload.base_frame, "site_element_id": list(base_site.element_id)}
        return {"kind": "reach_planar", "element_id": list(action.element_id),
            "description_identity": list(payload.description_identity), "program_revision": self.model.program_revision,
            "accepted_program_revision": None, "candidate_only": None, "context_origin": "source_recording",
            "source_location": self._source_location(payload.source_location), "channel": "joint_coordinates",
            "chain": {"shoulder": self._occurrence(payload.shoulder), "elbow": self._occurrence(payload.elbow),
                      "tip": self._occurrence(payload.tip), "base_frame": frame, "lengths_m": list(payload.lengths_m),
                      "closed_limits_rad": {"shoulder": list(payload.limits_rad[0]), "elbow": list(payload.limits_rad[1])}},
            "target": {"type": "Point3", "frame": copy.deepcopy(frame), "coordinates_m": list(payload.target_m)},
            "branch": payload.branch, "duration_seconds": _time_text(action.duration),
            "current": {"available": True, "reason": None, "value": current}}

    def _source_location(self, value):
        """Reuse one fixed immutable source projection, never a mutable row.

        An action alias may share its frozen four-field source location with
        many independently identified action occurrences. The complete scalar
        values form the key in the existing bounded pure cache; all occurrences
        still receive a fresh dictionary and retain their full H06 weight.
        Other source-record shapes retain the ordinary recursive conversion.
        """
        names = ("source_id", "source_revision", "start_byte", "end_byte")
        if (not is_dataclass(value)
                or not getattr(type(value), "__dataclass_params__").frozen
                or tuple(entry.name for entry in fields(value)) != names):
            return _plain(value, self.a)
        values = tuple(getattr(value, name) for name in names)
        if tuple(type(item) for item in values) != (str, str, int, int):
            return _plain(value, self.a)
        self.a.guard(values[2], values[3])
        key = ("source_location_projection", values)
        cached = self.a.lookup(key)
        if cached is None:
            projected = _plain(value, self.a)
            cached = self.a.remember(key, tuple(projected.items()))
        return dict(cached)

    def _logical_entries(self, value):
        """Independent JSON logical count; every repeated occurrence counts.

        Counts and cancellation checkpoints follow the bounded output walker,
        separately from numerical arithmetic units and H06 row weights.
        """
        count, stack = 0, [(value, 0)]
        while stack:
            item, depth = stack.pop()
            count += 1
            if count % 128 == 0:
                self.a.tick()
            if count > 100000 or depth > 128:
                raise ReferenceError("resource", "Independent JSON counting exceeds its finite entry/depth bound")
            if isinstance(item, dict):
                stack.extend((entry, depth + 1) for entry in item.values())
            elif isinstance(item, (tuple, list)):
                stack.extend((entry, depth + 1) for entry in item)
            elif item is not None and not isinstance(item, (str, bool, int, float, F, Interval)):
                raise ReferenceError("unsupported", "Independent JSON counter encountered an unsupported leaf")
        self.a.tick()
        return count

    def _maximum_reach_weight(self):
        total = 1
        pose = {"position_m": [0.0] * 3, "orientation_wxyz": [1.0, 0.0, 0.0, 0.0]}
        for path, action in self.model.actions.items():
            self.a.tick()
            if action.kind != "reach_planar":
                continue
            payload = action.reach
            current = {"observation": {"time_seconds": "0", "side": "before", "run_id": None, "context_kind": "recorded_prefix"},
                "lifecycle": "completed", "goal_outcome": "satisfied", "resolved_joint_targets_rad": [0.0, 0.0],
                "start_coordinates_rad": [0.0, 0.0], "start_time_seconds": "0", "elapsed_seconds": "0",
                "completion_time_seconds": "0", "joint_coordinates_rad": [0.0, 0.0],
                "joint_rates_rad_per_s": [0.0, 0.0], "action_joint_rates_rad_per_s": [0.0, 0.0],
                "claimed_joint_ids": [list(self.model.joints[joint].element_id) for joint in (payload.shoulder, payload.elbow)],
                "current_residual_m": 0.0, "tip_pose_base": pose, "tip_pose_world": pose, "current_world_target_m": [0.0] * 3,
                "terminal_result": {"outcome": "satisfied", "time_seconds": "0", "position_residual_m": 0.0,
                                    "joint_coordinates_rad": [0.0, 0.0], "tip_pose_base": pose}}
            total += self._logical_entries(self._description(path, current))
            if total > 100000:
                raise ReferenceError("resource", "Independent complete reach projection weight exceeds its limit")
        return total

    def _inherited_weight(self, horizon, side):
        key = (horizon, side)
        if key in self._inherited_history_cache:
            return self._inherited_history_cache[key]
        # H05 omits the frame map and duplicate object row.  The remaining
        # ordinary rows plus empty impulse/force histories weigh 19*O+J+A.
        base = 19 * len(self.model.objects) + len(self.model.joints) + len(self.model.actions)
        impulse_groups, force_changes = {}, {}
        for block in self.model.events:
            self.a.tick()
            if block.time > horizon or block.time == horizon and side == "before":
                break
            for event in block.events:
                self.a.tick()
                if event.kind == "impulse":
                    target = self.model.objects[event.target]
                    group = impulse_groups.setdefault(block.time, {})
                    group[event.target] = group.get(event.target, 0) + 45 + len(target.element_id)
                if event.kind == "force":
                    payload = event.force
                    weight = self._logical_entries(self._force_record(event.target, (payload, block.time)))
                    force_changes.setdefault(block.time, []).append(("start", event.target, payload.key, weight))
                    end = block.time + payload.duration
                    if end < horizon or end == horizon and side == "after":
                        force_changes.setdefault(end, []).append(("end", event.target, payload.key, weight))
        retained, impulse_maximum = {}, 0
        for _, values in sorted(impulse_groups.items()):
            retained.update(values)
            impulse_maximum = max(impulse_maximum, sum(retained.values()))
        active, latest, maximum = {}, {}, 0
        for _, changes in sorted(force_changes.items()):
            group = {}
            for kind, target, force, weight in changes:
                self.a.tick()
                if kind == "end":
                    active.pop((target, force), None)
                else:
                    active[(target, force)] = weight
                group[target] = group.get(target, 0) + weight + 1
            latest.update(group)
            maximum = max(maximum, sum(active.values()) + sum(latest.values()))
        result = base + impulse_maximum + maximum
        self._inherited_history_cache[key] = result
        return result

    def _release_weight(self, time):
        total = 1
        for block in self.model.events:
            self.a.tick()
            if block.time != time:
                continue
            for index, event in enumerate(block.events):
                if event.kind != "release":
                    continue
                joint = self.model.joints[event.target]
                child = self.model.sites[joint.child].owner
                dependencies = self._dependencies(child, self._state)
                contributors = []
                for path, action in self.model.actions.items():
                    self.a.tick()
                    if action.kind != "reach_planar":
                        continue
                    payload = action.reach
                    if dependencies.intersection({("joint", payload.shoulder), ("joint", payload.elbow)}):
                        contributors.append({"action": self._occurrence(path), "shoulder": self._occurrence(payload.shoulder),
                            "elbow": self._occurrence(payload.elbow), "joint_coordinates_rad": [0.0, 0.0],
                            "joint_rates_rad_per_s": [0.0, 0.0]})
                node = event.span
                source = self.model.source_provenance[node.source_id]
                shape = {"program_revision": self.model.program_revision,
                    "source_location": {"source_id": node.source_id, "source_revision": source["source_revision"],
                                        "start_byte": node.start, "end_byte": node.end},
                    "sequence_index": index, "time_seconds": _time_text(time),
                    "grip": self._occurrence(event.target), "target": self._occurrence(child),
                    "reach_contributors": contributors,
                    "incoming_pose_world": {"position_m": [0.0] * 3, "orientation_wxyz": [1.0, 0.0, 0.0, 0.0]},
                    "incoming_linear_velocity_world_m_per_s": [0.0] * 3,
                    "incoming_angular_velocity_world_rad_per_s": [0.0] * 3}
                total += self._logical_entries(shape)
        return total

    def _boundary_weight(self, time):
        return (2 + self._inherited_weight(time, "before") + self._inherited_weight(time, "after")
                + 2 * self._reach_history_weight + self._release_weight(time))

    def boundary_states(self):
        # The full conservative H06 sum was checked before retaining each
        # state pair.  Projection allocation cannot precede that preflight.
        if self.mode != "recording":
            self.a.tick()
            raise ReferenceError("unsupported", "Observation-only references cannot provide complete recording histories")
        if self.end_side != "after":
            raise ReferenceError("unsupported", "Complete recording histories require the final after-side")
        if self._history_weight > 100000:
            raise ReferenceError("resource", "Independent boundary history preflight was exceeded")
        result, actual_weight = [], 0
        for time in self.boundaries:
            self.a.tick()
            record = {"source_seconds": _time_text(time), "incoming_releases": copy.deepcopy(list(self._release_records[time]))}
            for side in ("before", "after"):
                sample = self.sample(time, side)
                record["joint_states_" + side] = sample["joints"]
                record["action_states_" + side] = sample["actions"]
                record["pose_authorities_" + side] = {path: value["pose_authority"] for path, value in sample["objects"].items()}
                record["impulse_states_" + side] = {path: value["impulses"] for path, value in sample["objects"].items()}
                record["force_states_" + side] = {path: value["forces"] for path, value in sample["objects"].items()}
                record["reach_states_" + side] = sample["reaches"]
                actual_weight += self._inherited_weight(time, side) + self._logical_entries(sample["reaches"])
            actual_weight += 2 + self._logical_entries(record["incoming_releases"])
            if actual_weight > self._history_weight or actual_weight > 100000:
                raise ReferenceError("resource", "Independent actual H06 history exceeds its preflight bound")
            result.append(record)
        return result

    def phases(self, carrier, start, end):
        """Return all positively overlapping independently derived phases.

        Endpoint-only contact never selects the next phase.  Clipped actual
        binary32 gaps can ask for every phase they touch using the same rule.
        """
        start, end = F(start), F(end)
        if not 0 <= start <= end <= self.end:
            raise ReferenceError("unsupported", "Independent phase interval is outside its source prefix")
        carrier = carrier if carrier == "world" or carrier.endswith(".frame") else carrier + ".frame"
        result = []
        for index, (left, right) in enumerate(zip(self.boundaries, self.boundaries[1:])):
            self.a.tick()
            if max(left, start) >= min(right, end):
                continue
            key = (carrier, max(left, start), min(right, end), index)
            if key not in self._phase_cache:
                value = self._phase(carrier, key[1], key[2], self._after[index])
                if len(self._phase_cache) < MAX_CACHE:
                    self._phase_cache[key] = value
            else:
                value = self._phase_cache[key]
            result.append(value)
        return tuple(result)

    def point_phase(self, carrier, time, side="after"):
        """Bound one exact state, including newly materialized final anchors.

        A point does not add a positive-width phase.  It independently supplies
        the numerical basis for an inclusive endpoint or either boundary side.
        """
        self.a.tick()
        time = F(time)
        state = self._state_at(time, side)
        carrier = carrier if carrier == "world" or carrier.endswith(".frame") else carrier + ".frame"
        key = ("point", carrier, time, side)
        if key not in self._phase_cache:
            value = self._phase(carrier, time, time, state)
            if len(self._phase_cache) < MAX_CACHE:
                self._phase_cache[key] = value
            return value
        return self._phase_cache[key]

    def _l1(self, vector):
        result = F(0)
        for value in vector:
            interval = self.a.interval(value)
            result = self.a.exact(result, interval.magnitude, "add")
        return result

    def _distance(self, first, last):
        return self._l1(tuple(self.a.sub(a, b) for a, b in zip(first, last)))

    def _ancestry(self, carrier, state):
        """Source edges and offsets, independently reconstructed from topology."""
        incoming, offsets, joints, path = self._incoming(state), [], [], []
        stem = carrier.removesuffix(".frame")
        if carrier == "world":
            return None, (), (), ("world",)
        if stem in self.model.sites:
            site = self.model.sites[stem]
            offsets.append(site.pose.position)
            path.append(carrier)
            stem = site.owner
        visited = set()
        while True:
            self.a.tick()
            if stem in visited or len(visited) > 128:
                raise ReferenceError("unsupported", "Independent derivative path is cyclic or too deep")
            visited.add(stem)
            path.append(stem + ".frame")
            if stem not in incoming:
                return stem, tuple(offsets), tuple(joints), tuple(path)
            kind, relation = incoming[stem]
            path.append(relation)
            if kind == "follow":
                follow = self.model.follows[relation]
                offsets.append(follow.offset.position)
                if follow.parent == "world":
                    return None, tuple(offsets), tuple(joints), tuple(path)
                parent = follow.parent.removesuffix(".frame")
                if parent in self.model.sites:
                    offsets.append(self.model.sites[parent].pose.position)
                    stem = self.model.sites[parent].owner
                else:
                    stem = parent
            else:
                joint = self.model.joints[relation]
                offsets.extend((self.model.sites[joint.child].pose.position, self.model.sites[joint.parent].pose.position))
                if joint.kind in {"hinge", "slider"}:
                    joints.append(relation)
                stem = self.model.sites[joint.parent].owner

    def _joint_path(self, joint, start, end, state):
        owner = state.claims.get((joint, "coordinate"))
        active = None if owner is None else state.actions[owner]
        action = None if owner is None else self.model.actions[owner]
        if action is not None and action.kind == "reach_planar":
            index = (action.reach.shoulder, action.reach.elbow).index(joint)
            initial, target, ideal_initial = F(active.initial[index]), F(active.targets[index]), F(active.ideal_initial[index])
        elif action is not None:
            initial, target, ideal_initial = F(active.initial), F(action.goal), F(active.ideal_initial)
        else:
            initial = target = F(state.coordinates[joint])
            ideal_initial = F(state.ideal_coordinates[joint])
        op = self.a.exact
        actual_slope = F(0) if active is None else op(op(target, initial, "sub"), action.duration, "div")
        ideal_slope = F(0) if active is None else op(op(target, ideal_initial, "sub"), action.duration, "div")
        elapsed = (F(0), F(0)) if active is None else (active.elapsed_at(start), active.elapsed_at(end))
        actual = tuple(op(initial, op(actual_slope, time, "mul"), "add") for time in elapsed)
        ideal = tuple(op(ideal_initial, op(ideal_slope, time, "mul"), "add") for time in elapsed)
        error = max(abs(op(x, y, "sub")) for x, y in zip(actual, ideal))
        if active is not None:
            error = op(error, op(op(max(abs(x) for x in actual), F(1, 1 << 53), "mul"), F(3, 1 << 1075), "add"), "add")
        if active is not None and active.status != "running":
            actual_slope = ideal_slope = F(0)
        return CoordinatePath(joint, owner, initial, target, elapsed[0], None if action is None else action.duration,
            ideal_slope, *actual, ideal_initial, *ideal, actual_slope, error)

    def _source_basis(self, carrier, start, end, state):
        """Reconstruct the documented uniform basis from source topology.

        This independently applies the constant/inverse/composition derivative
        rules.  Neither production phase records nor certificate fields are
        inputs.  Counts describe helper paths, so geometry and stopped/restarted
        coordinates cannot disappear from a claimed whole-phase bound.
        """
        key = (id(state), start, end)
        self.a.tick()
        cached = self._basis_cache.get(key)
        if cached is None or cached[0] is not state:
            cache = {"world": _SourceBound()}
            if len(self._basis_cache) < MAX_CACHE:
                self._basis_cache[key] = (state, cache)
        else:
            cache = cached[1]
            if carrier in cache:
                return cache[carrier]
        incoming = self._incoming(state)
        active_path = set()
        exact = self.a.exact

        add, mul = self.a.exact_sum, self.a.exact_product

        def rounding(extent):
            return add(mul(extent, F(1, 1 << 53)), F(3, 1 << 1075))

        def finish(**values):
            b = _SourceBound(**values)
            rotation = add(b.anchor_rotation, b.coordinate, mul(b.trig, F(1, 1 << 74)), mul(b.products, F(1, 1 << 91)))
            position = add(b.anchor_position, mul(b.offset, rotation), mul(b.vectors, F(1, 1 << 96)), rounding(b.extent))
            values.update(position_error=position, rotation_error=add(rotation, F(1, 1 << 50)))
            return _SourceBound(**values)

        def constant(pose, inverse=False):
            key = ("source_bound_constant", self.a.bits, tuple(pose.position), inverse)
            cached = self.a.lookup(key)
            if cached is not None:
                return cached
            extent = self._l1(pose.position)
            return self.a.remember(key, finish(
                extent=add(mul(2, extent), F(2, 1 << 96)) if inverse else extent,
                offset=extent if inverse else F(0), products=1, vectors=int(inverse)))

        def compose(parent, local):
            key = ("source_bound_compose", self.a.bits, parent, local)
            cached = self.a.lookup(key)
            if cached is not None:
                return cached
            radius = local.extent
            ideal_radius = add(radius, local.position_error)
            speed = add(parent.speed, mul(parent.omega, ideal_radius), local.speed)
            acceleration = add(parent.acceleration,
                mul(add(parent.alpha, mul(parent.omega, parent.omega)), ideal_radius),
                mul(2, parent.omega, local.speed), local.acceleration)
            omega = add(parent.omega, local.omega)
            alpha = add(parent.alpha, mul(parent.omega, local.omega), local.alpha)
            actual_speed = add(parent.actual_speed, mul(parent.actual_omega, add(radius, F(1, 1 << 96))),
                               local.actual_speed, F(2, 1 << 96))
            actual_omega = add(parent.actual_omega, local.actual_omega, F(2, 1 << 96))
            offset_error = add(local.position_error, mul(parent.rotation_error, radius), F(1, 1 << 96))
            velocity_error = add(parent.velocity_error, mul(parent.omega_error, ideal_radius),
                mul(parent.actual_omega, offset_error), local.velocity_error,
                mul(parent.rotation_error, local.actual_speed), F(4, 1 << 96), rounding(mul(2, actual_speed)))
            omega_error = add(parent.omega_error, local.omega_error,
                mul(parent.rotation_error, local.actual_omega), F(2, 1 << 96), rounding(mul(2, actual_omega)))
            return self.a.remember(key, finish(extent=add(parent.extent, mul(2, radius), F(4, 1 << 96)),
                offset=add(parent.offset, local.offset, radius), trig=parent.trig + local.trig,
                products=parent.products + local.products + 1, vectors=parent.vectors + local.vectors + 2,
                coordinate=add(parent.coordinate, local.coordinate),
                anchor_position=add(parent.anchor_position, local.anchor_position),
                anchor_rotation=add(parent.anchor_rotation, local.anchor_rotation),
                velocity_error=velocity_error, omega_error=omega_error, speed=speed,
                acceleration=acceleration, omega=omega, alpha=alpha,
                actual_speed=actual_speed, actual_omega=actual_omega))

        def root(path):
            actual_position, ideal_position = state.positions[path], state.ideal_positions[path]
            extent = self._l1(actual_position)
            position_error = self._distance(actual_position, ideal_position)
            speed = omega = F(0)
            rotation_error = state.rotation_errors[path]
            trig, products = 0, 1
            translation = state.claims.get((path, "translation"))
            if translation is not None:
                action, active = self.model.actions[translation], state.actions[translation]
                elapsed = max(abs(active.elapsed_at(start)), abs(active.elapsed_at(end)))
                extent = add(self._l1(active.initial), mul(self._l1(action.vector), elapsed))
                position_error = self._distance(active.initial, active.ideal_initial)
                speed = self._l1(action.vector) if active.status == "running" else F(0)
            orientation = state.claims.get((path, "orientation"))
            if orientation is not None:
                action, active = self.model.actions[orientation], state.actions[orientation]
                elapsed = max(abs(active.elapsed_at(start)), abs(active.elapsed_at(end)))
                rotation_error = active.rotation_error
                if any(action.vector) and elapsed:
                    trig, products = 1, 3
                omega = self._l1(action.vector) if active.status == "running" else F(0)
            return finish(extent=extent, trig=trig, products=products, anchor_position=position_error,
                anchor_rotation=rotation_error, speed=speed, omega=omega, actual_speed=speed, actual_omega=omega)

        def dynamic(path):
            anchor = state.dynamic[path]
            elapsed = max(abs(start - anchor.time), abs(end - anchor.time))
            acceleration = tuple(F(x) for x in (state.forces[path].acceleration or self.model.gravity))
            ideal_acceleration = state.forces[path].ideal_acceleration or tuple(F(x) for x in self.model.gravity)
            acceleration_error = sum((abs(exact(x, y, "sub")) for x, y in zip(acceleration, ideal_acceleration)), F(0))
            velocity, acceleration_size = self._l1(anchor.actual.velocity), self._l1(acceleration)
            extent = add(self._l1(anchor.actual.position), mul(velocity, elapsed), mul(acceleration_size, elapsed, elapsed, F(1, 2)))
            actual_speed = add(velocity, mul(acceleration_size, elapsed))
            position_error = add(anchor.position_error, mul(anchor.velocity_error, elapsed),
                                 mul(acceleration_error, elapsed, elapsed, F(1, 2)))
            velocity_error = add(anchor.velocity_error, mul(acceleration_error, elapsed), rounding(actual_speed))
            actual_omega = self._l1(anchor.actual.omega)
            moving = bool(actual_omega and elapsed)
            return finish(extent=extent, trig=int(moving), products=3 if moving else 1,
                anchor_position=position_error, anchor_rotation=add(anchor.rotation_error, mul(anchor.omega_error, elapsed)),
                velocity_error=velocity_error, omega_error=anchor.omega_error,
                speed=add(actual_speed, velocity_error), acceleration=self._l1(ideal_acceleration),
                omega=add(actual_omega, anchor.omega_error), actual_speed=actual_speed, actual_omega=actual_omega)

        def visit(frame):
            self.a.tick()
            if frame in cache:
                return cache[frame]
            if frame in active_path or len(active_path) > 128:
                raise ReferenceError("unsupported", "Independent uniform-basis graph is cyclic or too deep")
            active_path.add(frame)
            stem = frame.removesuffix(".frame")
            if stem in self.model.sites:
                site = self.model.sites[stem]
                value = compose(visit(site.owner + ".frame"), constant(site.pose))
            elif stem in incoming:
                kind, relation = incoming[stem]
                if kind == "follow":
                    follow = self.model.follows[relation]
                    value = compose(visit(follow.parent), constant(follow.offset))
                else:
                    joint = self.model.joints[relation]
                    motion = _SourceBound()
                    if joint.kind in {"hinge", "slider"}:
                        scalar = self._joint_path(relation, start, end, state)
                        axis = tuple(F(x) for x in joint.axis)
                        size = self._l1(axis)
                        rate_error = abs(exact(scalar.actual_slope, scalar.slope, "sub"))
                        if joint.kind == "hinge":
                            defect = abs(exact(add(*(mul(x, x) for x in axis)), F(1), "sub"))
                            motion = finish(trig=1, products=1, coordinate=scalar.coordinate_error,
                                omega_error=add(mul(size, rate_error), mul(defect, abs(scalar.slope))),
                                omega=abs(scalar.slope), actual_omega=mul(size, abs(scalar.actual_slope)))
                        else:
                            motion = finish(extent=mul(size, max(abs(scalar.actual_start), abs(scalar.actual_end))), products=1,
                                anchor_position=mul(size, scalar.coordinate_error), velocity_error=mul(size, rate_error),
                                speed=mul(size, abs(scalar.slope)), actual_speed=mul(size, abs(scalar.actual_slope)))
                    value = compose(compose(visit(joint.parent + ".frame"), motion),
                                    constant(self.model.sites[joint.child].pose, inverse=True))
            elif state.modes[stem] == "dynamic":
                value = dynamic(stem)
            else:
                value = root(stem)
            active_path.remove(frame)
            cache[frame] = value
            return value

        return visit(carrier)

    def _phase(self, carrier, start, end, state):
        root, _, joints, path = self._ancestry(carrier, state)
        identity = self.p.identity()
        actual_root = identity if root is None else self._root_pose(root, start, state, ideal=False)
        ideal_root = identity if root is None else self._root_pose(root, start, state, ideal=True)
        acceleration = tuple(F(x) for x in ((state.forces[root].acceleration or self.model.gravity)
                             if root is not None and state.modes[root] == "dynamic" else ZERO))
        basis = self._source_basis(carrier, start, end, state)
        coordinates = tuple(self._joint_path(joint, start, end, state) for joint in joints)
        anchor_velocity = self._distance(actual_root.velocity, ideal_root.velocity)
        anchor_omega = self._distance(actual_root.omega, ideal_root.omega)
        if root is not None and state.modes[root] == "dynamic":
            anchor_velocity = max(anchor_velocity, state.dynamic[root].velocity_error)
            anchor_omega = max(anchor_omega, state.dynamic[root].omega_error)
        return ReferencePhase(start, end, carrier, basis.speed, basis.acceleration, basis.omega, coordinates,
            actual_root.position, actual_root.velocity, acceleration, actual_root.orientation, actual_root.omega,
            ideal_root.position, ideal_root.velocity, ideal_root.orientation, ideal_root.omega,
            basis.offset, basis.extent, basis.anchor_position, basis.anchor_rotation, anchor_velocity, anchor_omega,
            basis.position_error, basis.rotation_error, basis.velocity_error, basis.omega_error,
            basis.trig, basis.products, basis.vectors, basis.coordinate, path)
