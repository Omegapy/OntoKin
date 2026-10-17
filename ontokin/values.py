"""Typed core values and explicit dimensional arithmetic.

The reference implementation keeps dimension and frame information until static
validation finishes. Python numbers alone are deliberately insufficient to stand
for an OntoKin value.
"""

from __future__ import annotations

import math
import re
from dataclasses import asdict, dataclass, is_dataclass
from fractions import Fraction
from typing import Any, Callable

from .diagnostics import OntoKinError


Dim = tuple[int, int, int, int]
ZERO: Dim = (0, 0, 0, 0)
LENGTH: Dim = (1, 0, 0, 0)
MASS: Dim = (0, 1, 0, 0)
TIME: Dim = (0, 0, 1, 0)
ANGLE: Dim = (0, 0, 0, 1)
SPEED: Dim = (1, 0, -1, 0)
ACCELERATION: Dim = (1, 0, -2, 0)
ANGULAR_SPEED: Dim = (0, 0, -1, 1)

ALIASES: dict[str, Dim] = {
    "Length": LENGTH, "Area": (2, 0, 0, 0), "Volume": (3, 0, 0, 0),
    "Mass": MASS, "Time": TIME, "Angle": ANGLE, "Speed": SPEED,
    "Acceleration": ACCELERATION, "AngularSpeed": ANGULAR_SPEED,
    "Force": (1, 1, -2, 0), "Torque": (2, 1, -2, 0),
    "Density": (-3, 1, 0, 0), "Inertia": (2, 1, 0, 0),
}


@dataclass(frozen=True)
class Type:
    kind: str
    dimension: Dim | None = None
    element: Type | None = None
    name: str | None = None

    def __str__(self) -> str:
        if self.kind == "Quantity":
            for name, dim in ALIASES.items():
                if dim == self.dimension:
                    return name
            powers = "*".join(f"{u}^{e}" if e != 1 else u
                              for u, e in zip(("m", "kg", "s", "rad"), self.dimension or ZERO) if e)
            return f"Quantity[{powers}]"
        if self.kind == "Ref":
            return f"Ref<{self.name}>"
        if self.element is not None:
            return f"{self.kind}<{self.element}>"
        return self.kind


INT, REAL, BOOL, STRING = Type("Int"), Type("Real"), Type("Bool"), Type("String")
UNKNOWN = object()


@dataclass(frozen=True)
class Value:
    type: Type
    value: Any = UNKNOWN
    frame: str | None = None
    hint: str | None = None

    @property
    def known(self) -> bool:
        return self.value is not UNKNOWN

    def to_data(self) -> Any:
        """Small JSON-compatible inspection record; never serializes host objects."""
        if not self.known:
            return {"type": str(self.type), "value": None}
        def plain(value: Any) -> Any:
            if isinstance(value, Value):
                return value.to_data()
            if isinstance(value, Fraction):
                return {"numerator": value.numerator, "denominator": value.denominator}
            if isinstance(value, (tuple, list)):
                return [plain(v) for v in value]
            if isinstance(value, dict):
                return {k: plain(v) for k, v in value.items()}
            if is_dataclass(value):
                return plain(asdict(value))
            return value
        data = {"type": str(self.type), "value": plain(self.value)}
        if self.frame is not None:
            data["frame"] = self.frame
        return data


def quantity_type(dim: Dim) -> Type:
    return REAL if dim == ZERO else Type("Quantity", dimension=dim)


def scalar(value: float, dim: Dim = ZERO) -> Value:
    return Value(quantity_type(dim), canonical(value))


def canonical(value: float) -> float:
    return 0.0 if value == 0 else value


def error(code: str, message: str, node: Any = None, *, phase: str = "type",
          expected: Any = None, actual: Any = None) -> None:
    details = {}
    if expected is not None:
        details["expected"] = str(expected)
    if actual is not None:
        details["actual"] = str(actual)
    category = "unsupported" if code == "OKL-E-CAPABILITY-UNSUPPORTED" else "resource_limit" if code == "OKL-E-RESOURCE" else "invalid"
    raise OntoKinError(code, message, node, phase=phase, category=category, details=details,
                      repair="Use a value with the required type, dimension, and frame." if phase == "type" else
                             "Revise the expression so that its result is finite and inside the required domain.")


def finite(value: float | int, node: Any = None) -> float:
    try:
        result = float(value)
    except (OverflowError, ValueError):
        error("OKL-E-NUMERIC", "Numeric result exceeds the finite binary64 range.", node, phase="elaboration")
    if not math.isfinite(result):
        error("OKL-E-NUMERIC", "Numeric result is not finite.", node, phase="elaboration")
    return canonical(result)


def rounded(value: Fraction, node: Any = None,
            warn: Callable[[Any], None] | None = None) -> float:
    result = finite(value, node)
    if value and abs(result) < float.fromhex("0x1p-1022") and warn is not None:
        warn(node)
    return result


def checked_int(value: int, node: Any = None) -> int:
    if not -(1 << 63) <= value < (1 << 63):
        error("OKL-E-NUMERIC", "Integer value is outside the signed 64-bit range.", node, phase="elaboration")
    return value


UNITS: dict[str, tuple[Dim, Fraction]] = {
    "m": (LENGTH, Fraction(1)), "cm": (LENGTH, Fraction(1, 100)),
    "mm": (LENGTH, Fraction(1, 1000)), "kg": (MASS, Fraction(1)),
    "g": (MASS, Fraction(1, 1000)), "s": (TIME, Fraction(1)),
    "ms": (TIME, Fraction(1, 1000)), "rad": (ANGLE, Fraction(1)),
    "deg": (ANGLE, Fraction.from_float(math.pi) / 180),
    "N": ((1, 1, -2, 0), Fraction(1)),
}

# These are explicit prototype work budgets, not limits on the language's
# numeric grammar. Check them before Python constructs arbitrary-size integers.
MAX_NUMERIC_DIGITS = 4096
MAX_DECIMAL_EXPONENT = 4096
MAX_UNIT_TOKENS = 4096


def units(text: str, node: Any = None) -> tuple[Dim, Fraction]:
    if len(text) > MAX_UNIT_TOKENS * 16:
        error("OKL-E-RESOURCE", "Unit expression exceeds the prototype's 65,536-character budget.", node, phase="elaboration")
    parts = re.findall(r"[A-Za-z_][A-Za-z0-9_]*|[0-9]+|[*/^\-]", text)
    if len(parts) > MAX_UNIT_TOKENS:
        error("OKL-E-RESOURCE", "Unit expression exceeds the prototype's 4,096-token budget.", node, phase="elaboration")
    compact = re.sub(r"\s+", "", text)
    if "".join(parts) != compact or not parts:
        error("OKL-E-UNIT", "Malformed unit expression.", node)
    dim = [0, 0, 0, 0]
    factor = Fraction(1)
    i, sign = 0, 1
    while i < len(parts):
        name = parts[i]
        i += 1
        if name not in UNITS:
            error("OKL-E-UNIT", f"Unknown unit '{name}'.", node)
        power = 1
        if i < len(parts) and parts[i] == "^":
            i += 1
            negative = i < len(parts) and parts[i] == "-"
            i += int(negative)
            if i >= len(parts) or not parts[i].isdigit():
                error("OKL-E-UNIT", "A unit exponent must be an integer.", node)
            if len(parts[i]) > 2:
                error("OKL-E-CAPABILITY-UNSUPPORTED", "Unit exponents outside [-16,16] are outside core support.", node, phase="support")
            power = int(parts[i]) * (-1 if negative else 1)
            i += 1
        if not -16 <= power <= 16:
            error("OKL-E-CAPABILITY-UNSUPPORTED", "Unit exponents outside [-16,16] are outside core support.", node, phase="support")
        udim, ufactor = UNITS[name]
        for d in range(4):
            dim[d] += udim[d] * power * sign
        factor *= ufactor ** (power * sign)
        if i < len(parts):
            if parts[i] not in ("*", "/"):
                error("OKL-E-UNIT", "Expected '*' or '/' between units.", node)
            sign = 1 if parts[i] == "*" else -1
            i += 1
            if i == len(parts):
                error("OKL-E-UNIT", "Unit expression ends with an operator.", node)
    if any(not -16 <= d <= 16 for d in dim):
        error("OKL-E-CAPABILITY-UNSUPPORTED", "Normalized unit exponents exceed core support.", node, phase="support")
    return tuple(dim), factor


def literal(text: str, unit: str | None, node: Any = None, *, negative: bool = False,
            warn: Callable[[Any], None] | None = None) -> Value:
    sign = -1 if negative else 1
    integer_token = "." not in text and "e" not in text.lower()
    if unit is None and integer_token and len(text) > 19:
        error("OKL-E-NUMERIC", "Integer literal is outside the signed 64-bit range.", node, phase="elaboration")
    if len(text) > MAX_NUMERIC_DIGITS:
        error("OKL-E-RESOURCE", "Numeric literal exceeds the prototype's 4,096-character conversion budget.", node, phase="elaboration")
    if "e" in text.lower():
        exponent_text = text.lower().split("e", 1)[1]
        exponent_digits = exponent_text.lstrip("+-").lstrip("0") or "0"
        if len(exponent_digits) > 4 or int(exponent_digits) > MAX_DECIMAL_EXPONENT:
            error("OKL-E-RESOURCE", "Decimal exponent magnitude exceeds the prototype's 4,096 conversion budget.", node, phase="elaboration")
    if unit is not None:
        dim, factor = units(unit, node)
        return scalar(rounded(Fraction(text) * factor * sign, node, warn), dim)
    if integer_token:
        return Value(INT, checked_int(sign * int(text), node))
    return Value(REAL, rounded(Fraction(text) * sign, node, warn))


def numeric(t: Type) -> bool:
    return t.kind in ("Int", "Real", "Quantity")


def dimension(t: Type) -> Dim:
    return t.dimension if t.kind == "Quantity" else ZERO


def widen(value: Value, node: Any = None, *, explicit: bool = False) -> Value:
    if value.type != INT:
        return value
    if not value.known:
        return Value(REAL)
    result = float(value.value)
    if not explicit and int(result) != value.value:
        error("OKL-E-TYPE", "Implicit Int-to-Real conversion would round; use real(value) explicitly.", node,
              expected=REAL, actual=INT)
    return Value(REAL, canonical(result))


def common(a: Value, b: Value, node: Any = None) -> tuple[Value, Value, Type]:
    if a.type == b.type:
        return a, b, a.type
    if a.type == INT and b.type == REAL:
        return widen(a, node), b, REAL
    if a.type == REAL and b.type == INT:
        return a, widen(b, node), REAL
    if a.type.kind == "Quantity" or b.type.kind == "Quantity":
        error("OKL-E-UNIT", f"Incompatible dimensions: {a.type} and {b.type}.", node,
              expected=a.type, actual=b.type)
    error("OKL-E-TYPE", f"Incompatible types: {a.type} and {b.type}.", node,
          expected=a.type, actual=b.type)


def coerce(value: Value, target: Type, node: Any = None,
           subtype: Callable[[str, str], bool] | None = None) -> Value:
    if value.type == target:
        return value
    if value.type == INT and target == REAL:
        return widen(value, node)
    if value.type.kind == target.kind == "Ref" and subtype and subtype(value.type.name, target.name):
        return Value(target, value.value, value.frame)
    if value.type.kind == target.kind and target.kind in ("Vec3", "Vector3", "Range"):
        if value.known:
            values = tuple(coerce(v, target.element, node, subtype) for v in value.value)
            return Value(target, values, value.frame)
        coerce(Value(value.type.element), target.element, node, subtype)
        return Value(target, frame=value.frame)
    unit_related = value.type.kind == "Quantity" or target.kind == "Quantity"
    error("OKL-E-UNIT" if unit_related else "OKL-E-TYPE",
          f"Expected {target}, received {value.type}.", node, expected=target, actual=value.type)


def same_frame(a: Value, b: Value, node: Any = None) -> None:
    if a.frame is not None and b.frame is not None and a.frame != b.frame:
        error("OKL-E-FRAME", f"Spatial frames differ: '{a.frame}' and '{b.frame}'.", node)


def unary(op: str, value: Value, node: Any = None) -> Value:
    if op == "not":
        coerce(value, BOOL, node)
        return Value(BOOL, not value.value) if value.known else Value(BOOL)
    if op != "-":
        error("OKL-E-TYPE", f"Unknown unary operator '{op}'.", node)
    if value.type.kind in ("Vec3", "Vector3"):
        return Value(value.type, tuple(unary(op, v, node) for v in value.value), value.frame) if value.known else value
    if not numeric(value.type):
        error("OKL-E-TYPE", f"Unary '-' is not defined for {value.type}.", node)
    if not value.known:
        return value
    result = -value.value
    return Value(value.type, checked_int(result, node) if value.type == INT else canonical(result))


def binary(op: str, a: Value, b: Value, node: Any = None,
           warn: Callable[[Any], None] | None = None) -> Value:
    if op in ("and", "or"):
        coerce(a, BOOL, node); coerce(b, BOOL, node)
        if not a.known or not b.known:
            return Value(BOOL)
        return Value(BOOL, a.value and b.value if op == "and" else a.value or b.value)
    ak, bk = a.type.kind, b.type.kind
    vectors = ("Vec3", "Vector3", "Point3")
    if ak in vectors or bk in vectors:
        if ak in vectors and bk in vectors:
            same_frame(a, b, node)
            if op in ("==", "!=") and ak == bk:
                common(Value(a.type.element), Value(b.type.element), node)
                if not a.known or not b.known:
                    return Value(BOOL)
                equal = all(binary("==", x, y, node).value for x, y in zip(a.value, b.value))
                return Value(BOOL, equal if op == "==" else not equal)
            if op not in ("+", "-"):
                error("OKL-E-TYPE", "Only compatible vector addition/subtraction or scalar multiplication is defined.", node)
            if ak == bk == "Point3" and op == "-":
                result_kind = "Vector3"
            elif ak == "Point3" and bk == "Vector3":
                coerce(b, Type("Vector3", element=quantity_type(LENGTH)), node)
                result_kind = "Point3"
            elif ak == bk and ak != "Point3":
                result_kind = ak
            else:
                error("OKL-E-TYPE", "This point/vector operation is not defined.", node)
            element = common(Value(a.type.element), Value(b.type.element), node)[2]
            result_type = Type(result_kind, element=element)
            if not a.known or not b.known:
                return Value(result_type, frame=a.frame)
            return Value(result_type, tuple(binary(op, x, y, node, warn) for x, y in zip(a.value, b.value)), a.frame)
        if op not in ("*", "/") or ak == "Point3" or bk == "Point3":
            error("OKL-E-TYPE", "A tuple/vector supports multiplication or division by a scalar only.", node)
        if ak not in vectors:
            if op != "*":
                error("OKL-E-TYPE", "Scalar divided by vector is not defined.", node)
            a, b = b, a
        if not numeric(b.type):
            error("OKL-E-TYPE", "Vector scaling requires a numeric scalar.", node)
        element = binary(op, Value(a.type.element), Value(b.type), node, warn).type
        typ = Type(a.type.kind, element=element)
        if not a.known or not b.known:
            return Value(typ, frame=a.frame)
        return Value(typ, tuple(binary(op, x, b, node, warn) for x in a.value), a.frame)
    if op in ("==", "!=") and ak in ("Bool", "String", "Ref", "FrameRef", "SiteRef", "JointRef", "MotionMode", "CollisionMode", "Range"):
        a, b, _ = common(a, b, node)
        if not a.known or not b.known:
            return Value(BOOL)
        if ak == "Range":
            eq = all(binary("==", x, y, node).value for x, y in zip(a.value, b.value))
        else:
            eq = a.value == b.value
        return Value(BOOL, eq if op == "==" else not eq)
    if not numeric(a.type) or not numeric(b.type):
        error("OKL-E-TYPE", f"Operator '{op}' is not defined for {a.type} and {b.type}.", node)
    if op in ("+", "-", "<", "<=", ">", ">=", "==", "!="):
        a, b, typ = common(a, b, node)
        if op in ("<", "<=", ">", ">=", "==", "!="):
            if not a.known or not b.known:
                return Value(BOOL)
            ops = {"<": lambda: a.value < b.value, "<=": lambda: a.value <= b.value,
                   ">": lambda: a.value > b.value, ">=": lambda: a.value >= b.value,
                   "==": lambda: a.value == b.value, "!=": lambda: a.value != b.value}
            return Value(BOOL, ops[op]())
    elif op in ("*", "/"):
        if a.type == b.type == INT:
            typ = INT if op == "*" else REAL
        else:
            a = widen(a, node) if a.type == INT else a
            b = widen(b, node) if b.type == INT else b
            dim = tuple(x + (y if op == "*" else -y) for x, y in zip(dimension(a.type), dimension(b.type)))
            if any(not -16 <= x <= 16 for x in dim):
                error("OKL-E-CAPABILITY-UNSUPPORTED", "Normalized result dimensions exceed core support.", node, phase="support")
            typ = quantity_type(dim)
    else:
        error("OKL-E-TYPE", f"Unknown operator '{op}'.", node)
    if not a.known or not b.known:
        return Value(typ)
    if op == "/" and b.value == 0:
        error("OKL-E-NUMERIC", "Division by zero.", node, phase="elaboration")
    if typ == INT:
        result = a.value + b.value if op == "+" else a.value - b.value if op == "-" else a.value * b.value
        return Value(INT, checked_int(result, node))
    x, y = Fraction(a.value), Fraction(b.value)
    exact = x + y if op == "+" else x - y if op == "-" else x * y if op == "*" else x / y
    return Value(typ, rounded(exact, node, warn))

