"""Bounded read-only membership for the explicitly declared .21 profile.

The evaluator owns eager arguments, signature/abstract checking and generated
dependency guards. This private operation admits known native metadata before
scanning keys, using only the caller's original admitted request ledger.
"""
from __future__ import annotations

import re

from .diagnostics import OntoKinError
from .execution_budget import SharedExecutionBudget
from .values import UNKNOWN, KeyedValue, Type, Value


MAX_ENTRIES = 256
MAX_KEY_CHARS = 64
MAX_REF_NAME_CHARS = 278
STAGES = ("keyed_membership_admission", "keyed_membership_input",
          "keyed_membership_query", "keyed_membership_scan",
          "keyed_membership_publication")
_KEY_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
_SIMPLE_KINDS = frozenset({
    "Int", "Real", "Bool", "String", "FrameRef", "Rotation", "Pose", "Color",
    "LoftSection", "SurfaceMaterial", "TextureImage", "PlanarUV", "TextureBinding",
    "PolygonPocket", "FramedPolygonSection", "PolygonSection", "PolygonRing",
    "PlanarPoint", "PolygonVertex",
})
_COLLECTION_MESSAGE = "has_key requires an immutable Keyed value."
_LEAF_MESSAGE = "has_key input entry has a different resolved leaf type."
_KEY_MESSAGE = ("Stable keys must contain 1–64 ASCII letters, digits, '.', '_', or '-', "
                "and begin with a letter or digit.")


def _type_descriptor(value, *, scalar_only=False):
    """Return only bounded native scalar fields, never raw dataclass equality.

    There is at most one recursive call, for a numeric child. Its scalar-only
    branch rejects every container before inspecting another child, including
    cyclic or deliberately deep native metadata.
    """
    if type(value) is not Type:
        return None
    kind = getattr(value, "kind", None)
    if type(kind) is not str or len(kind) > 32:
        return None
    dimension, element, name = value.dimension, value.element, value.name
    if kind in _SIMPLE_KINDS:
        if (scalar_only and kind not in {"Int", "Real"}
                or dimension is not None or element is not None or name is not None):
            return None
        return (kind,)
    if kind == "Quantity":
        if (type(dimension) is not tuple or len(dimension) != 4
                or element is not None or name is not None):
            return None
        if any(type(exponent) is not int or not -16 <= exponent <= 16
               for exponent in dimension):
            return None
        if not any(dimension):
            return None
        return (kind, *dimension)
    if scalar_only:
        return None
    if kind in {"Vec3", "Vector3", "Range", "Point3"}:
        if dimension is not None or name is not None:
            return None
        child = _type_descriptor(element, scalar_only=True)
        if child is None:
            return None
        if kind == "Point3" and child != ("Quantity", 1, 0, 0, 0):
            return None
        return (kind, *child)
    if kind == "Ref":
        if (dimension is not None or element is not None or type(name) is not str
                or not 1 <= len(name) <= MAX_REF_NAME_CHARS):
            return None
        return (kind, name)
    return None


def _type_error(message, node):
    raise OntoKinError("OKL-E-TYPE", message, node, phase="type")


def _key_domain(key, node):
    # Exact native String shape is checked by the caller before any length or
    # content operation. Oversized input is never copied, encoded or echoed.
    if not 1 <= len(key) <= MAX_KEY_CHARS or _KEY_RE.fullmatch(key) is None:
        raise OntoKinError("OKL-E-ID", _KEY_MESSAGE, node, phase="binding")


def has_key(collection, query, *, expected_type: Type, node,
            ledger: SharedExecutionBudget) -> bool:
    """Execute one known membership invocation, adding exactly n + k + 3 ticks.

    Complete input admission precedes query validation and scanning. No leaf
    payload is evaluated or compared, and no sorting, index or collection copy
    is created. An opaque known payload is sufficient after its exact wrapper
    and resolved type metadata have been admitted.
    """
    if (not isinstance(ledger, SharedExecutionBudget) or ledger.resolved is None
            or ledger.admitted_entry_revision is None):
        raise OntoKinError("OKL-E-RESOURCE", "Construction requires one admitted execution context.",
                           node, phase="support",
                           details={"budget_reason": "execution_context_required"})
    previous_stage = ledger.stage
    try:
        ledger.stage = "keyed_membership_admission"
        ledger.tick(node)
        if type(collection) is not KeyedValue:
            _type_error(_COLLECTION_MESSAGE, node)
        entries = getattr(collection, "entries", None)
        if type(entries) is not tuple:
            _type_error(_COLLECTION_MESSAGE, node)
        count = len(entries)
        if count > MAX_ENTRIES:
            raise OntoKinError("OKL-E-RESOURCE", "Keyed membership input exceeds 256 entries.",
                               node, phase="support",
                               details={"budget": "keyed_entries", "limit": MAX_ENTRIES,
                                        "consumed": count})
        expected = _type_descriptor(expected_type)
        if expected is None:
            _type_error(_COLLECTION_MESSAGE, node)

        previous_key = None
        for index in range(count):
            ledger.stage = "keyed_membership_input"
            ledger.tick(node)
            entry = entries[index]
            if type(entry) is not tuple or len(entry) != 2:
                _type_error(_COLLECTION_MESSAGE, node)
            key, value = entry
            if type(key) is not str:
                _type_error(_COLLECTION_MESSAGE, node)
            _key_domain(key, node)
            if previous_key is not None and key <= previous_key:
                raise OntoKinError("OKL-E-ID", "has_key input keys must be unique canonical stable keys.",
                                   node, phase="binding")
            if type(value) is not Value:
                _type_error(_LEAF_MESSAGE, node)
            actual = _type_descriptor(getattr(value, "type", None))
            if actual is None or actual != expected or value.value is UNKNOWN:
                _type_error(_LEAF_MESSAGE, node)
            previous_key = key

        ledger.stage = "keyed_membership_query"
        ledger.tick(node)
        if type(query) is not str:
            _type_error("has_key query requires exactly String.", node)
        _key_domain(query, node)

        result = False
        for index in range(count):
            ledger.stage = "keyed_membership_scan"
            ledger.tick(node)
            if entries[index][0] == query:
                result = True
                break
        ledger.stage = "keyed_membership_publication"
        ledger.tick(node)
        return result
    finally:
        ledger.stage = previous_stage
