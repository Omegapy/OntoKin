"""Bounded production arithmetic for the explicitly adopted reach profile.

This module imports no preparation oracle, evaluator, renderer or service. Every
arithmetic helper precharges the caller's shared work callback. Dyadic interval
endpoints are integers, independently of the retained Fraction-based oracle.
"""
from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from fractions import Fraction
from math import isqrt
import struct
from time import monotonic
from typing import Callable

PRECISIONS = (96, 192, 384, 768, 1536)
MAX_OPERATIONS = 100000
MAX_OPERAND_BITS = 32768
MAX_SERIES_TERMS = 12000
MAX_INTERVAL_OPERATIONS = 100000
SIGN = 1 << 63
MAX_FINITE = 0x7FEFFFFFFFFFFFFF
PI64_BITS = 0x400921FB54442D18


class ReachAdmissionError(Exception):
    def __init__(self, reach_code: str, message: str, **details):
        super().__init__(message)
        self.reach_code = reach_code
        self.details = {"reach_code": reach_code, **details}


class _Refine(Exception):
    """The current enclosure is insufficient; only the fixed schedule retries."""


class ReachExecutionWork:
    """One request's bounded numeric work and immutable-result cache.

    ``check`` must charge one unit to the inherited remaining work budget and
    check cancellation. Direct callers may use this object's tick for all their
    semantic work. A callback exception is never translated or annotated here.
    """
    def __init__(self, check: Callable[[], None] | None = None, *,
                 max_operations=MAX_OPERATIONS, max_elapsed_ms=30000,
                 max_operand_bits=MAX_OPERAND_BITS, max_cache_entries=256):
        limits = ((max_operations, MAX_OPERATIONS), (max_elapsed_ms, 30000),
                  (max_operand_bits, MAX_OPERAND_BITS), (max_cache_entries, 256))
        if any(type(value) is not int or not 1 <= value <= maximum for value, maximum in limits):
            raise ValueError("Reach work limits may only lower the fixed positive maxima")
        self.external_check = check
        self.max_operations = max_operations
        self.max_elapsed_ms = max_elapsed_ms
        self.max_operand_bits = max_operand_bits
        self.max_cache_entries = max_cache_entries
        self.operations = 0
        self.started = monotonic()
        self.counts: dict[str, int] = {}
        self.callback_error: BaseException | None = None
        self._cache: OrderedDict[tuple, object] = OrderedDict()
        self._cache_operand_bits = max_operand_bits
        # A callback may reenter the same bounded cache. This bookkeeping
        # serial prevents an outer insertion from undoing that completed work.
        self._cache_generation = 0
        # A scoped source traversal can observe an existing callback boundary
        # without replacing the caller's callback or adding a work operation.
        # The ordinary path leaves this private observer unset.
        self._source_after_charge = None

    def charge(self, kind="checkpoint", amount=1):
        if type(amount) is not int or amount < 0:
            raise ValueError("Invalid work charge")
        for _ in range(amount):
            observer = self._source_after_charge
            if self.external_check is not None:
                try:
                    self.external_check()
                except BaseException as error:
                    self.callback_error = error
                    raise
            if self.operations >= self.max_operations:
                self.resource("max_operations", self.max_operations, self.operations + 1)
            if (monotonic() - self.started) * 1000 > self.max_elapsed_ms:
                self.resource("max_elapsed_ms", self.max_elapsed_ms,
                              (monotonic() - self.started) * 1000)
            self.operations += 1
            self.counts[kind] = self.counts.get(kind, 0) + 1
            # Capture before the unchanged callback, then observe only after
            # its normal return and the original resource/counter checks.
            # A callback replacement cannot hide from the captured observer;
            # an original callback/resource failure never runs this hook.
            if observer is not None:
                observer()

    def tick(self):
        self.charge()

    check = tick

    def resource(self, budget, limit, consumed):
        raise ReachAdmissionError("reach_resource", "Reach arithmetic exhausted its bounded work.",
                                  budget=budget, limit=limit, consumed=consumed)

    def guard_bits(self, bits):
        if bits > self.max_operand_bits:
            self.resource("numeric_operand_bits", self.max_operand_bits, bits)

    def guard(self, *values):
        for value in values:
            if isinstance(value, Fraction):
                self.guard_bits(max(value.numerator.bit_length(), value.denominator.bit_length()))
            else:
                self.guard_bits(value.bit_length())

    def admission(self):
        self.charge("admission")
        return AdmissionWork(self)

    def lookup(self, key):
        self.charge("cache_lookup")
        self._sync_cache_operand_limit()
        if key not in self._cache:
            return None
        operand_bits = self.max_operand_bits
        self.charge("cache_promote")
        # The promotion callback can change the domain after the first
        # synchronization. Never return its now-stale completed proof.
        if self._sync_cache_operand_limit() or operand_bits != self.max_operand_bits:
            return None
        # A nested callback can have synchronized the domain already, or
        # evicted this key without a domain change. Neither is a cache hit.
        if key not in self._cache:
            return None
        self._cache.move_to_end(key)
        self._cache_generation += 1
        return self._cache[key]

    def remember(self, key, value, *, admission=None):
        operand_bits = self.max_operand_bits
        generation = self._cache_generation
        self.charge("cache_insert")
        # A caller may return a proof completed before this callback, but it
        # cannot publish that proof as reusable under a different domain.
        if (self._sync_cache_operand_limit() or operand_bits != self.max_operand_bits
                or generation != self._cache_generation):
            return False if admission is not None else None
        present = key in self._cache
        # All required bookkeeping is precharged before changing values/order.
        # A cancelled promotion or eviction leaves the previous cache intact.
        if present:
            self.charge("cache_promote")
        elif len(self._cache) >= self.max_cache_entries:
            self.charge("cache_evict")
        # Promotion and eviction have callbacks of their own. A successful
        # reset discards this pending insertion; cancellation before the reset
        # still preserves the original values and order.
        if (self._sync_cache_operand_limit() or operand_bits != self.max_operand_bits
                or generation != self._cache_generation):
            return False if admission is not None else None
        # Optional source receipts are precharged by their caller. Their final
        # callback-free comparison runs after every insertion/promotion/eviction
        # callback and before any value or order changes. A defensive recheck
        # also protects against an admission hook that reenters this cache.
        if admission is not None:
            if admission() is not True:
                return False
            if operand_bits != self.max_operand_bits or generation != self._cache_generation:
                return False
        if not present and len(self._cache) >= self.max_cache_entries:
            self._cache.popitem(last=False)
        self._cache[key] = value
        if present:
            self._cache.move_to_end(key)
        self._cache_generation += 1
        return True if admission is not None else None

    def remember_batch(self, entries, *, admission):
        """Publish a bounded group only after every callback and one receipt.

        Pending entries are already completed immutable calculations, not a
        second retained cache. Only keys are copied for prospective LRU order;
        each insertion, promotion and eviction keeps its existing unit charge.
        Cancellation, rejection, or reentrant cache work publishes no prefix.
        """
        if (type(entries) is not tuple or not callable(admission)
                or type(self.max_cache_entries) is not int
                or not 1 <= self.max_cache_entries <= 256
                or type(self.max_operand_bits) is not int
                or not 1 <= self.max_operand_bits <= MAX_OPERAND_BITS
                or len(entries) > self.max_cache_entries
                or any(type(entry) is not tuple or len(entry) != 2
                       or type(entry[0]) is not tuple for entry in entries)):
            raise ValueError("A cache publication batch must fit its current bounded cache.")
        operand_bits = self.max_operand_bits
        generation = self._cache_generation
        capacity = self.max_cache_entries
        self.charge("cache_batch_domain")

        def unchanged():
            return (not self._sync_cache_operand_limit()
                    and type(self.max_operand_bits) is int
                    and type(self.max_cache_entries) is int
                    and operand_bits == self.max_operand_bits
                    and generation == self._cache_generation
                    and capacity == self.max_cache_entries
                    and len(self._cache) <= capacity)

        if not unchanged():
            return False
        # This transient ordering contains no numeric results. The real cache
        # remains untouched until the complete final admission has succeeded.
        order = OrderedDict.fromkeys(self._cache)
        for key, _ in entries:
            self.charge("cache_insert")
            if not unchanged():
                return False
            present = key in order
            if present:
                self.charge("cache_promote")
            elif len(order) >= capacity:
                self.charge("cache_evict")
            if not unchanged():
                return False
            if not present and len(order) >= capacity:
                order.popitem(last=False)
            order[key] = None
            if present:
                order.move_to_end(key)
        if admission() is not True:
            return False
        # Admission is normally callback-free. A defensive check also keeps a
        # caller-supplied reentrant hook from undoing its own completed work.
        if (type(self.max_operand_bits) is not int or type(self.max_cache_entries) is not int
                or operand_bits != self.max_operand_bits or generation != self._cache_generation
                or capacity != self.max_cache_entries or len(self._cache) > capacity):
            return False
        for key, value in entries:
            present = key in self._cache
            if not present and len(self._cache) >= capacity:
                self._cache.popitem(last=False)
            self._cache[key] = value
            if present:
                self._cache.move_to_end(key)
            self._cache_generation += 1
        return True

    def _sync_cache_operand_limit(self):
        # A completed proof under a wider cap cannot stand in for arithmetic
        # that the current narrower domain would reject. Clear all nested
        # reusable results together; ordinary requests keep one fixed cap.
        if self._cache_operand_bits != self.max_operand_bits:
            self.charge("cache_operand_scope_reset")
            # A nested callback may already have reset and populated the
            # current domain. Preserve those independently completed entries.
            if self._cache_operand_bits != self.max_operand_bits:
                self._cache.clear()
                self._cache_operand_bits = self.max_operand_bits
                self._cache_generation += 1
            return True
        return False

    def record(self):
        return {"operations": self.operations, "counts": dict(self.counts),
                "cache_entries": len(self._cache)}


class AdmissionWork:
    """Counters accumulate across all five passes of one admission."""
    def __init__(self, parent):
        self.parent = parent
        self.series_terms = 0
        self.interval_operations = 0
        self.exact_operations = 0
        self.started_operations = parent.operations

    def charge(self, kind="exact", amount=1):
        self.parent.charge(kind, amount)
        self.exact_operations += amount

    def interval(self):
        if self.interval_operations >= MAX_INTERVAL_OPERATIONS:
            self.parent.resource("numeric_interval_operations", MAX_INTERVAL_OPERATIONS,
                                 self.interval_operations + 1)
        self.parent.charge("interval")
        self.interval_operations += 1

    def term(self):
        if self.series_terms >= MAX_SERIES_TERMS:
            self.parent.resource("numeric_series_recurrence_steps", MAX_SERIES_TERMS,
                                 self.series_terms + 1)
        self.parent.charge("series_recurrence")
        self.series_terms += 1

    def guard(self, *values):
        self.parent.guard(*values)

    def guard_bits(self, bits):
        self.parent.guard_bits(bits)

    def record(self):
        return {"series_terms": self.series_terms,
                "interval_operations": self.interval_operations,
                "exact_operations": self.exact_operations,
                "operations": self.parent.operations - self.started_operations}


def rational(value, work):
    work.charge("exact_decode")
    if isinstance(value, bool) or not isinstance(value, (int, float, Fraction)):
        raise ReachAdmissionError("reach_domain", "Expected a finite real numeric operand.")
    if isinstance(value, float):
        bits = float_bits(value)
        if bits & 0x7FF0000000000000 == 0x7FF0000000000000:
            raise ReachAdmissionError("reach_domain", "A reach operand must be finite.")
        return bits_fraction(bits, work)
    work.guard(value)
    return Fraction(value)


def exact(left, right, operation, work):
    work.charge("exact_" + operation)
    work.guard(left, right)
    an, ad = left.numerator.bit_length(), left.denominator.bit_length()
    bn, bd = right.numerator.bit_length(), right.denominator.bit_length()
    if operation in ("add", "sub"):
        width = max(an + bd, bn + ad) + 1
        denominator = ad + bd
    elif operation == "mul":
        width, denominator = an + bn, ad + bd
    elif operation == "div":
        if not right:
            raise ZeroDivisionError("Exact zero divisor")
        width, denominator = an + bd, ad + bn
    else:
        raise ValueError("Unknown exact arithmetic operation")
    work.guard_bits(max(width, denominator))
    result = {"add": Fraction.__add__, "sub": Fraction.__sub__,
              "mul": Fraction.__mul__, "div": Fraction.__truediv__}[operation](left, right)
    work.guard(result)
    return result


def compare(left, right, work):
    work.charge("exact_compare")
    work.guard(left, right)
    work.guard_bits(max(left.numerator.bit_length() + right.denominator.bit_length(),
                        right.numerator.bit_length() + left.denominator.bit_length()))
    return (left > right) - (left < right)


def _quotient_even(numerator, denominator, work):
    work.charge("integer_round")
    work.guard(numerator, denominator)
    work.guard_bits(max(abs(numerator).bit_length(), denominator.bit_length()) + 1)
    q, r = divmod(numerator, denominator)
    return q + int(2*r > denominator or (2*r == denominator and q % 2))


def round_dyadic(value, bits, *, work):
    work.charge("dyadic_round")
    work.guard(value)
    work.guard_bits(value.numerator.bit_length() + bits + 1)
    return Fraction(_quotient_even(value.numerator << bits, value.denominator, work), 1 << bits)


def float_bits(value):
    return struct.unpack(">Q", struct.pack(">d", value))[0]


def bits_float(bits):
    return struct.unpack(">d", struct.pack(">Q", bits))[0]


def bits_fraction(bits, work):
    work.charge("binary64_decode")
    exponent, trailing = (bits >> 52) & 2047, bits & ((1 << 52) - 1)
    if exponent == 2047:
        raise ReachAdmissionError("reach_numeric", "A finite binary64 value is required.")
    significand = trailing if exponent == 0 else (1 << 52) | trailing
    shift = -1074 if exponent == 0 else exponent - 1075
    work.guard_bits(max(significand.bit_length() + max(shift, 0), 1 + max(-shift, 0)))
    value = Fraction(significand << shift) if shift >= 0 else Fraction(significand, 1 << -shift)
    return -value if bits & SIGN else value


def _exponent(value, work):
    work.charge("binary_exponent")
    work.guard(value)
    n, d = value.numerator, value.denominator
    exponent = n.bit_length() - d.bit_length()
    work.guard_bits(max(n.bit_length() + max(-exponent, 0), d.bit_length() + max(exponent, 0)))
    if (n < d << exponent) if exponent >= 0 else (n << -exponent < d):
        exponent -= 1
    return exponent


def round_bits(value, work):
    work.charge("binary64_round")
    work.guard(value)
    if not value:
        return 0
    negative, value = value < 0, abs(value)
    exponent = _exponent(value, work)
    shift = 1074 if exponent < -1022 else 52 - exponent
    work.guard_bits(max(value.numerator.bit_length() + max(shift, 0),
                        value.denominator.bit_length() + max(-shift, 0)) + 1)
    n, d = value.numerator, value.denominator
    n, d = (n << shift, d) if shift >= 0 else (n, d << -shift)
    significant = _quotient_even(n, d, work)
    if exponent < -1022:
        result = significant
    else:
        if significant == 1 << 53:
            significant >>= 1
            exponent += 1
        if exponent > 1023:
            raise ReachAdmissionError("reach_numeric", "An exposed value exceeds finite binary64.")
        result = ((exponent + 1023) << 52) | (significant - (1 << 52))
    return result | SIGN if negative and result else result


def round_binary64(value, *, work):
    return bits_float(round_bits(value, work))


def sqrt_rational_binary64(value, *, work):
    work.charge("sqrt_binary64")
    work.guard(value)
    if value < 0:
        raise ValueError("Negative square root")
    if not value:
        return 0.0
    exponent = _exponent(value, work) // 2
    shift = 1074 if exponent < -1022 else 52 - exponent
    work.guard_bits(max(value.numerator.bit_length() + max(2*shift, 0),
                        value.denominator.bit_length() + max(-2*shift, 0)) + 4)
    n, d = value.numerator, value.denominator
    n, d = (n << (2*shift), d) if shift >= 0 else (n, d << (-2*shift))
    work.charge("integer_sqrt")
    q = isqrt(n // d)
    work.charge("integer_sqrt_return")
    # Compare sqrt(n/d) with q+1/2 using exact squares, including exact ties.
    work.guard_bits(max(n.bit_length() + 2, d.bit_length() + 2*q.bit_length() + 3))
    work.charge("sqrt_midpoint")
    left, right = 4*n, d*(2*q+1)**2
    q += int(left > right or (left == right and q % 2))
    if exponent < -1022:
        return bits_float(q)
    if q == 1 << 53:
        q >>= 1
        exponent += 1
    if exponent > 1023:
        raise ReachAdmissionError("reach_numeric", "Square root exceeds finite binary64.")
    return bits_float(((exponent + 1023) << 52) | (q - (1 << 52)))


@dataclass(frozen=True)
class Interval:
    lo: int
    hi: int


class DyadicContext:
    """Outward fixed-point interval arithmetic; no host float operations."""
    def __init__(self, precision, work):
        if precision not in PRECISIONS:
            raise ValueError("Unsupported precision pass")
        self.p, self.scale, self.work = precision, 1 << precision, work
        self._pi = None

    def _op(self, *values, width=None, units=1):
        if isinstance(self.work, AdmissionWork):
            self.work.interval()
        else:
            self.work.charge("interval")
        self.work.guard(*values)
        if width is not None:
            self.work.guard_bits(width)
        self.work.charge("interval_constituent", units)
        # A constituent checkpoint can narrow the live domain. Admission of
        # the original complete operand/preflight set must still hold before
        # any integer allocation, including when a monotone corner is omitted.
        self.work.guard(*values)
        if width is not None:
            self.work.guard_bits(width)

    @staticmethod
    def _canonical_cells(*values):
        return all(type(value) is Interval and type(value.lo) is int
                   and type(value.hi) is int and value.lo <= value.hi
                   for value in values)

    def bounds(self, value):
        self.work.charge("interval_extract", 2)
        return Fraction(value.lo, self.scale), Fraction(value.hi, self.scale)

    def point(self, value):
        native = type(value) in (int, float, Fraction)
        value = Fraction(value)
        precision, meter = self.p, self.work
        width = value.numerator.bit_length()+precision+1
        domain = meter.parent if type(meter) is AdmissionWork else meter
        if (native and type(self) is DyadicContext and type(precision) is int
                and precision in PRECISIONS
                and type(getattr(domain, "max_operand_bits", None)) is int
                and domain.max_operand_bits == MAX_OPERAND_BITS):
            # Retain the original shift-width admission before classifying a
            # denominator. An exact grid point needs only its one final shift.
            self._op(value, width=width, units=0)
            numerator, denominator = value.numerator, value.denominator

            def same_domain():
                return (self.work is meter and type(self.p) is int and self.p == precision
                    and (type(meter) is not AdmissionWork or meter.parent is domain)
                    and type(domain.max_operand_bits) is int
                    and domain.max_operand_bits == MAX_OPERAND_BITS)

            direct = (same_domain() and type(numerator) is int and type(denominator) is int
                and denominator > 0 and denominator.bit_length() <= precision+1
                and not denominator & (denominator-1))
            charged = self.work
            units = 1 if direct else 3
            admission = charged if direct and type(charged) is AdmissionWork else None
            # AdmissionWork records a whole successful charge batch. Retain
            # that boundary even if a callback requires the old constituents.
            charge = admission.parent.charge if admission is not None else charged.charge
            charge("interval_constituent", units)
            if direct:
                direct = (same_domain() and type(value.numerator) is int
                    and type(value.denominator) is int
                    and value.numerator == numerator and value.denominator == denominator)
                if not direct:
                    # A retained callback changed the optional proof. Complete
                    # the old three constituents before its ordinary arithmetic.
                    charge("interval_constituent", 2)
                    units = 3
            if admission is not None:
                admission.exact_operations += units
            self.work.guard(value)
            self.work.guard_bits(width)
            if direct:
                cell = numerator << (precision-denominator.bit_length()+1)
                return Interval(cell, cell)
        else:
            self._op(value, width=width, units=3)
        n, d = value.numerator << self.p, value.denominator
        return Interval(n//d, -((-n)//d))

    def add(self, a, b):
        self._op(a.lo,a.hi,b.lo,b.hi, width=max(abs(v).bit_length() for v in (a.lo,a.hi,b.lo,b.hi))+1, units=2)
        return Interval(a.lo+b.lo, a.hi+b.hi)

    def neg(self, value):
        self._op(value.lo,value.hi,units=2)
        return Interval(-value.hi,-value.lo)

    def sub(self, a, b):
        self._op(a.lo,a.hi,b.lo,b.hi, width=max(abs(v).bit_length() for v in (a.lo,a.hi,b.lo,b.hi))+1, units=2)
        return Interval(a.lo-b.hi,a.hi-b.lo)

    def mul(self, a, b):
        width=max(abs(a.lo).bit_length(),abs(a.hi).bit_length())+max(abs(b.lo).bit_length(),abs(b.hi).bit_length())+1
        if self._canonical_cells(a, b):
            if a.lo == a.hi == 0 or b.lo == b.hi == 0:
                self._op(a.lo,a.hi,b.lo,b.hi,width=width,units=0)
                return Interval(0, 0)
            if a.lo == a.hi == self.scale or b.lo == b.hi == self.scale:
                self._op(a.lo,a.hi,b.lo,b.hi,width=width,units=0)
                return b if a.lo == a.hi == self.scale else a
            # A one-cell interval touching zero is a fixed point of outward
            # multiplication by a positive factor no larger than one. This
            # omits only integer products/quotients with an already proved
            # result; all original operands and prospective widths remain
            # admitted. In particular the fixed atan degree is unchanged.
            tiny = ((a.lo,a.hi) if type(self.scale) is int and (a.lo,a.hi) in ((0,1),(-1,0)) and 0<=b.lo<=b.hi<=self.scale and b.hi>0 else
                    (b.lo,b.hi) if type(self.scale) is int and (b.lo,b.hi) in ((0,1),(-1,0)) and 0<=a.lo<=a.hi<=self.scale and a.hi>0 else None)
            if tiny is not None:
                operands=(a.lo,a.hi,b.lo,b.hi)
                scale=self.scale
                al,ah,bl,bh=operands
                pairs=(((al,bl),(ah,bh)) if tiny==(0,1) else
                       ((al,bh),(ah,bl)) if ah==0 else ((ah,bl),(al,bh)))
                self._op(*operands,width=width,units=0)
                # The ordinary monotone path captures both endpoint pairs
                # before callbacks. Return their fresh result, not a private
                # input cell a callback could replace via object.__setattr__.
                if type(self.scale) is int and self.scale==scale:
                    return Interval(*tiny)
                # A changed scale invalidates only the fixed-cell identity.
                # Finish the same captured ordinary pairs and its original
                # four constituents, retaining every post-callback guard.
                self.work.charge("interval_constituent",4)
                self.work.guard(*operands)
                self.work.guard_bits(width)
                (x,y),(z,w)=pairs
                low,high=x*y,z*w
                return Interval(low//self.scale,-((-high)//self.scale))
            if a.lo == a.hi and b.lo == b.hi:
                self._op(a.lo,a.hi,b.lo,b.hi,width=width,units=3)
                product = a.lo*b.lo
                return Interval(product//self.scale, -((-product)//self.scale))
            if a.lo >= 0:
                pairs = (((a.lo,b.lo),(a.hi,b.hi)) if b.lo >= 0 else
                         ((a.hi,b.lo),(a.lo,b.hi)) if b.hi <= 0 else
                         ((a.hi,b.lo),(a.hi,b.hi)))
            elif a.hi <= 0:
                pairs = (((a.lo,b.hi),(a.hi,b.lo)) if b.lo >= 0 else
                         ((a.hi,b.hi),(a.lo,b.lo)) if b.hi <= 0 else
                         ((a.lo,b.hi),(a.lo,b.lo)))
            elif b.lo >= 0:
                pairs = ((a.lo,b.hi),(a.hi,b.hi))
            elif b.hi <= 0:
                pairs = ((a.hi,b.lo),(a.lo,b.lo))
            else:
                pairs = None
            if pairs is not None:
                # Monotonicity fixes the exact two extremal products. The
                # original four-corner width guard still precedes both of them.
                self._op(a.lo,a.hi,b.lo,b.hi,width=width,units=4)
                (x,y),(z,w) = pairs
                low, high = x*y, z*w
                return Interval(low//self.scale, -((-high)//self.scale))
        self._op(a.lo,a.hi,b.lo,b.hi,width=width,units=8)
        products=(a.lo*b.lo,a.lo*b.hi,a.hi*b.lo,a.hi*b.hi)
        return Interval(min(products)//self.scale,-((-max(products))//self.scale))

    def div(self, a, b):
        width=max(abs(a.lo).bit_length(),abs(a.hi).bit_length())+self.p+1
        if self._canonical_cells(a, b) and not b.lo <= 0 <= b.hi:
            if a.lo == a.hi == 0 or b.lo == b.hi == self.scale:
                self._op(a.lo,a.hi,b.lo,b.hi,width=width,units=0)
                return a
            if b.lo > 0:
                pairs = (((a.lo,b.hi),(a.hi,b.lo)) if a.lo >= 0 else
                         ((a.lo,b.lo),(a.hi,b.hi)) if a.hi <= 0 else
                         ((a.lo,b.lo),(a.hi,b.lo)))
            else:
                pairs = (((a.hi,b.hi),(a.lo,b.lo)) if a.lo >= 0 else
                         ((a.hi,b.lo),(a.lo,b.hi)) if a.hi <= 0 else
                         ((a.hi,b.hi),(a.lo,b.hi)))
            precision, scale, meter = self.p, self.scale, self.work
            domain = meter.parent if type(meter) is AdmissionWork else meter
            if (b.lo == b.hi and type(self) is DyadicContext
                    and type(precision) is int and precision in PRECISIONS
                    and type(scale) is int and scale > 0
                    and type(getattr(domain, "max_operand_bits", None)) is int
                    and domain.max_operand_bits == MAX_OPERAND_BITS):
                operands = a.lo,a.hi,b.lo,b.hi
                self._op(*operands,width=width,units=0)

                def same_domain():
                    return (self.work is meter and type(self.p) is int and self.p == precision
                        and type(self.scale) is int and self.scale == scale
                        and (type(meter) is not AdmissionWork or meter.parent is domain)
                        and type(domain.max_operand_bits) is int
                        and domain.max_operand_bits == MAX_OPERAND_BITS)

                direct = (same_domain() and scale.bit_length() == precision+1
                    and not scale & (scale-1) and not operands[2] & (scale-1))
                if (direct and operands[2] > 0
                        and (operands[:2] == (0,1) or operands[:2] == (-1,0))):
                    # A positive integral divisor cannot move either directed
                    # endpoint of a one-cell interval adjacent to zero. Keep
                    # the pre-callback cells, just as the selected pairs do.
                    return Interval(operands[0],operands[1])
                charged = self.work
                units = 3 if direct else 4
                admission = charged if direct and type(charged) is AdmissionWork else None
                charge = admission.parent.charge if admission is not None else charged.charge
                charge("interval_constituent", units)
                if direct:
                    direct = same_domain()
                    if not direct:
                        charge("interval_constituent")
                        units = 4
                if admission is not None:
                    admission.exact_operations += units
                self.work.guard(*operands)
                self.work.guard_bits(width)
                if direct:
                    # Cancel the common positive scale exactly. One denominator
                    # shift and two directed quotients replace two products and
                    # two quotients; the original complete width guard remains.
                    denominator = operands[2] >> precision
                    (x,_),(z,_) = pairs
                    return Interval(x//denominator, -((-z)//denominator))
            else:
                self._op(a.lo,a.hi,b.lo,b.hi,width=width,units=4)
            (x,y),(z,w) = pairs
            # Python's integer floor division already has the correct sign
            # for a negative denominator; -floor(-q) supplies the upper end.
            return Interval((x*self.scale)//y, -((-(z*self.scale))//w))
        self._op(a.lo,a.hi,b.lo,b.hi,width=width,units=8)
        if b.lo<=0<=b.hi:
            raise _Refine("Interval denominator contains zero")
        lower=[]; upper=[]
        for x in (a.lo,a.hi):
            for y in (b.lo,b.hi):
                n,d=x*self.scale,y
                if d<0: n,d=-n,-d
                lower.append(n//d); upper.append(-((-n)//d))
        return Interval(min(lower),max(upper))

    def square(self, a):
        width=2*max(abs(a.lo).bit_length(),abs(a.hi).bit_length())+1
        if self._canonical_cells(a):
            if a.lo == a.hi == 0:
                self._op(a.lo,a.hi,width=width,units=0)
                return Interval(0, 0)
            if a.lo <= 0 <= a.hi:
                self._op(a.lo,a.hi,width=width,units=2)
                largest = max(abs(a.lo), abs(a.hi))
                upper = largest*largest
                return Interval(0, -((-upper)//self.scale))
            if a.lo == a.hi:
                self._op(a.lo,a.hi,width=width,units=3)
                value = a.lo*a.lo
                return Interval(value//self.scale, -((-value)//self.scale))
        self._op(a.lo,a.hi,width=width,units=4)
        lower=0 if a.lo<=0<=a.hi else min(a.lo*a.lo,a.hi*a.hi)
        upper=max(a.lo*a.lo,a.hi*a.hi)
        return Interval(lower//self.scale,-((-upper)//self.scale))

    def widen(self, a, error):
        extra=self.point(error).hi
        self._op(a.lo,a.hi,extra,width=max(abs(a.lo).bit_length(),abs(a.hi).bit_length(),extra.bit_length())+1,units=2)
        return Interval(a.lo-extra,a.hi+extra)

    def sqrt_point(self, value):
        self._op(value,width=value.numerator.bit_length()+2*self.p+2,units=3)
        if value<0: raise ValueError("Negative radicand")
        n,d=value.numerator<<(2*self.p),value.denominator
        self.work.charge("integer_sqrt")
        root=isqrt(n//d)
        self.work.charge("integer_sqrt_return")
        self.work.guard_bits(2*root.bit_length()+d.bit_length()+1)
        self.work.charge("sqrt_exactness")
        return Interval(root,root if root*root*d==n else root+1)

    def atan_small(self, value):
        if abs(value)>Fraction(1,2): raise ValueError("Unreduced arctangent")
        if value==0: return Interval(0,0)
        count=(self.p+5)//2
        z=self.point(value); z2=self.square(z); power=z; result=Interval(0,0)
        for k in range(count):
            if isinstance(self.work,AdmissionWork): self.work.term()
            else: self.work.charge("series_recurrence")
            term=self.div(power,self.point(2*k+1))
            result=self.add(result,term) if k%2==0 else self.sub(result,term)
            if k+1<count: power=self.mul(power,z2)
        self.work.guard_bits(2*count+2)
        return self.widen(result,Fraction(1,(1<<(2*count+1))*(2*count+1)))

    def pi(self):
        if self._pi is None:
            self._pi=self.sub(self.mul(self.point(16),self.atan_small(Fraction(1,5))),
                              self.mul(self.point(4),self.atan_small(Fraction(1,239))))
        return self._pi

    def atan_point(self, value):
        if value<0: return self.neg(self.atan_point(-value))
        if value>1:
            return self.sub(self.div(self.pi(),self.point(2)),
                            self.atan_point(exact(Fraction(1),value,"div",self.work)))
        if value>Fraction(1,2):
            reduced=exact(exact(value,Fraction(1),"sub",self.work),
                          exact(value,Fraction(1),"add",self.work),"div",self.work)
            return self.add(self.div(self.pi(),self.point(4)),self.atan_small(reduced))
        return self.atan_small(value)

    def atan(self, value):
        lo,hi=self.bounds(value)
        left=self.atan_point(lo); right=left if lo==hi else self.atan_point(hi)
        return Interval(left.lo,right.hi)

    def atan2(self, y, x, sy, sx, *, negative_axis=True):
        if sy==0:
            return Interval(0,0) if sx>0 else (self.neg(self.pi()) if negative_axis else self.pi())
        if sx==0:
            half=self.div(self.pi(),self.point(2))
            return half if sy>0 else self.neg(half)
        ax=x if sx>0 else self.neg(x); ay=y if sy>0 else self.neg(y)
        if ax.lo>0:
            angle=self.atan(self.div(ay,ax))
        elif ay.lo>0:
            angle=self.sub(self.div(self.pi(),self.point(2)),self.atan(self.div(ax,ay)))
        else:
            raise _Refine("Direction cannot yet be separated from zero")
        if sx<0: angle=self.sub(self.pi(),angle)
        return angle if sy>0 else self.neg(angle)

    def sincos_point(self, value):
        if abs(value)>8:
            raise ReachAdmissionError("reach_numeric", "IK residual angle exceeds its proved range.")
        if value==0:
            return self.point(0),self.point(1)
        # Fixed degrees, independently checked against the exact Lagrange tail.
        count={96:48,192:64,384:96,768:160,1536:272}[self.p]
        self.work.guard_bits(6*count+1)
        self.work.charge("taylor_tail_precharge",4*count+2)
        factorial=1
        for k in range(2,2*count+2):
            self.work.guard_bits(factorial.bit_length()+k.bit_length())
            factorial*=k
        sine_error=Fraction(1<<(3*(2*count+1)),factorial)
        cosine_error=Fraction(1<<(6*count),factorial//(2*count+1))
        if max(sine_error,cosine_error)>Fraction(1,1<<(self.p+8)):
            raise AssertionError("Fixed Taylor degree is insufficient")
        x=self.point(value); x2=self.square(x)
        sine=sin_term=x; cosine=cos_term=self.point(1)
        for k in range(1,count):
            if isinstance(self.work,AdmissionWork): self.work.term()
            else: self.work.charge("series_recurrence")
            sin_term=self.neg(self.div(self.mul(sin_term,x2),self.point((2*k)*(2*k+1))))
            cos_term=self.neg(self.div(self.mul(cos_term,x2),self.point((2*k-1)*(2*k))))
            sine=self.add(sine,sin_term); cosine=self.add(cosine,cos_term)
        return self.widen(sine,sine_error),self.widen(cosine,cosine_error)


def certify_rounding(context, enclosure):
    lo,hi=context.bounds(enclosure)
    left,right=round_bits(lo,context.work),round_bits(hi,context.work)
    if left!=right:
        raise _Refine("Enclosure does not fit a single binary64 rounding cell")
    # Monotonic exact endpoint rounding includes all midpoint/tie cases.
    return left
