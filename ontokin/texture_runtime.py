"""Lexical texture closure, typed constructors and exact local planar UVs.

Recipes retain immutable references and mapping metadata only.  Original PNG
bytes live once on the model's texture_assets map, never in geometry values.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
import math
from typing import Any, Callable

from .bundle import BundleError
from .diagnostics import OntoKinError
from .profile_capabilities import TEXTURE_PROFILES
from .surface import SurfaceError
from .syntax import Node
from .texture_bundle import TextureBundle, validate_asset_digest, validate_asset_id
from .texture_png import MAX_TOTAL_PIXEL_BYTES, validate_png
from .validator import fail
from .values import LENGTH, REAL, STRING, Type, Value, quantity_type


TEXTURE_PROFILE = "textured-surfaces-0.1"
TEXTURE_CALLS = frozenset({"png_asset", "planar_uv", "texture_binding", "texture_surface"})
TEXTURE_TYPES = frozenset({"TextureImage", "PlanarUV", "TextureBinding"})
MAX_TEXTURE_BINDINGS = 16
MAX_OPERAND_BITS = 32_768
MAX_UV_ABS = 4096
MAPPING_DOMAIN = b"ontokin.planar-uv/0.1\0"
_NATIVE_SURFACES = frozenset({"loft", "extrusion", "holes", "ring_loft", "framed_loft", "pockets"})
_INVERSE_LENGTH = (-1, 0, 0, 0)


@dataclass(frozen=True)
class TextureImageData:
    asset_id: str
    sha256: str


@dataclass(frozen=True)
class PlanarUVData:
    origin_m: tuple[float, float, float]
    u_per_m: tuple[float, float, float]
    v_per_m: tuple[float, float, float]
    offset: tuple[float, float]
    mapping_id: str
    source_id: str
    start: int
    end: int


@dataclass(frozen=True)
class TextureBindingData:
    image: TextureImageData
    mapping: PlanarUVData
    source_id: str
    start: int
    end: int


def _error(code: str, message: str, **details: Any) -> None:
    raise SurfaceError(code, message, details=details)


def _is_callback_error(compiler, error: BaseException) -> bool:
    execution = getattr(compiler.budget, "execution_budget", None)
    return (error is getattr(compiler.budget, "callback_error", None)
            or execution is not None and error is getattr(execution, "callback_error", None))


def _walk_ast(root: Node, charge: Callable[[Any], None]):
    """Traverse lexical nodes once, including uninstantiated definitions."""
    stack: list[Any] = [root]
    seen: set[int] = set()
    while stack:
        item = stack.pop()
        if isinstance(item, Node):
            if id(item) in seen:
                continue
            seen.add(id(item))
            charge(item)
            yield item
            stack.extend(reversed(tuple(item.data.values())))
        elif isinstance(item, dict):
            if id(item) in seen:
                continue
            seen.add(id(item))
            charge(root)
            stack.extend(reversed(tuple(item.values())))
        elif isinstance(item, (list, tuple)):
            if id(item) in seen:
                continue
            seen.add(id(item))
            charge(root)
            stack.extend(reversed(item))


def _literal_requirement(node: Node) -> tuple[str, str]:
    if len(node.args) != 2 or any(arg.kind != "string" for arg in node.args):
        fail("OKL-E-ASSET-CLOSURE", "png_asset requires two literal strings for its ID and digest.",
             node, phase="binding")
    asset_id, digest = (arg.value for arg in node.args)
    try:
        validate_asset_id(asset_id)
        validate_asset_digest(digest)
    except BundleError as exc:
        fail("OKL-E-ASSET-CLOSURE", exc.message, node, phase="binding", details=exc.details)
    return asset_id, digest


def validate_texture_closure(compiler) -> dict[str, tuple[Node, ...]]:
    """Admit all declared assets once before this compiler evaluates values.

    The compiler invokes this once for its linked snapshot.  Repeated lexical
    declarations share a single image decode.  No validity or authority cache
    survives the compilation.  Returns declaration nodes by stable asset ID.
    """
    entry = compiler.linked.entry.ast
    if entry.profile not in TEXTURE_PROFILES:
        if isinstance(compiler.bundle, TextureBundle):
            fail("OKL-E-ASSET-CLOSURE", "A texture bundle requires an explicit textured-surfaces-0.1 entry.",
                 entry, phase="binding")
        return {}
    if not isinstance(compiler.bundle, TextureBundle):
        fail("OKL-E-ASSET-CLOSURE", "textured-surfaces-0.1 requires immutable bundle/0.2, even without assets.",
             entry, phase="binding")
    execution = getattr(compiler.budget, "execution_budget", None)
    if (execution is None or getattr(execution, "resolved", None) is None
            or getattr(execution, "admitted_entry_revision", None) != compiler.bundle.entry.revision):
        fail("OKL-E-RESOURCE", "PNG admission requires this entry's current admitted execution ledger.",
             entry, phase="support", details={"budget_reason": "execution_context_required"})
    requirements: dict[str, tuple[str, list[Node]]] = {}
    for source_id in sorted(compiler.linked.modules):
        module = compiler.linked.modules[source_id]
        if module.ast.profile not in TEXTURE_PROFILES:
            continue
        for node in _walk_ast(module.ast, compiler.budget.tick):
            if (node.kind != "call" or node.callee.kind != "name"
                    or node.callee.name != "png_asset"):
                continue
            ident, digest = _literal_requirement(node)
            if ident in requirements:
                previous, nodes = requirements[ident]
                if previous != digest:
                    fail("OKL-E-ASSET-CLOSURE", "One asset ID has conflicting literal digest requirements.",
                         node, phase="binding", details={"asset_id": ident})
                nodes.append(node)
            else:
                requirements[ident] = digest, [node]
    assets = compiler.bundle.asset_map
    missing, extra = sorted(set(requirements) - set(assets)), sorted(set(assets) - set(requirements))
    if missing or extra:
        location = requirements[missing[0]][1][0] if missing else entry
        fail("OKL-E-ASSET-CLOSURE", "Supplied images must exactly equal the lexical asset closure.",
             location, phase="binding", details={"missing_assets": missing, "extra_assets": extra})
    for ident, (digest, nodes) in requirements.items():
        if assets[ident].sha256 != digest:
            fail("OKL-E-ASSET-CLOSURE", "An attached image does not match its literal digest requirement.",
                 nodes[0], phase="binding", details={"asset_id": ident,
                                                    "expected_sha256": digest,
                                                    "actual_sha256": assets[ident].sha256})
    info = {}
    decoded_bytes = 0
    for ident in sorted(assets):
        location = requirements[ident][1][0]
        try:
            png = validate_png(assets[ident].raw,
                               charge=lambda amount: compiler.budget.tick(location, amount=amount),
                               check=execution.checkpoint)
        except SurfaceError as exc:
            if _is_callback_error(compiler, exc):
                raise
            fail(exc.code, str(exc), location, details={"asset_id": ident, **exc.details})
        decoded_bytes += png.decoded_bytes
        if decoded_bytes > MAX_TOTAL_PIXEL_BYTES:
            fail("OKL-E-PNG", "Aggregate reconstructed image byte bound exceeded.", location,
                 details={"limit": MAX_TOTAL_PIXEL_BYTES, "consumed": decoded_bytes})
        info[ident] = png
    # Publish complete admission metadata only after every image succeeds.
    declarations = {ident: tuple(nodes) for ident, (_, nodes) in sorted(requirements.items())}
    compiler.texture_requirements = declarations
    compiler.model.texture_assets = assets
    compiler.model.texture_info = info
    compiler.model.texture_declarations = {
        ident: tuple({"source_id": node.source_id, "start": node.start, "end": node.end}
                     for node in nodes)
        for ident, nodes in declarations.items()
    }
    return declarations


class _ExactWork:
    """Small exact rational operations with bounded operands and precharges."""

    def __init__(self, charge=None, check=None):
        self.charge, self.check = charge, check

    def tick(self, amount=1):
        if self.charge is not None:
            self.charge(amount)
        if self.check is not None:
            self.check()

    @staticmethod
    def guard_bits(bits):
        if bits > MAX_OPERAND_BITS:
            _error("OKL-E-RESOURCE", "Texture arithmetic exceeds the numeric operand bound.",
                   budget="numeric_operand_bits", limit=MAX_OPERAND_BITS, consumed=bits)

    def guard(self, value):
        self.guard_bits(max(value.numerator.bit_length(), value.denominator.bit_length()))

    def fraction(self, number):
        self.tick()
        value = Fraction(number)
        self.guard(value)
        return value

    def add(self, a, b, *, subtract=False):
        self.tick()
        self.guard(a)
        self.guard(b)
        self.guard_bits(max(a.numerator.bit_length() + b.denominator.bit_length(),
                            b.numerator.bit_length() + a.denominator.bit_length()) + 1)
        self.guard_bits(a.denominator.bit_length() + b.denominator.bit_length())
        value = a - b if subtract else a + b
        self.guard(value)
        return value

    def multiply(self, a, b):
        self.tick()
        self.guard(a)
        self.guard(b)
        self.guard_bits(a.numerator.bit_length() + b.numerator.bit_length())
        self.guard_bits(a.denominator.bit_length() + b.denominator.bit_length())
        value = a * b
        self.guard(value)
        return value


def _number(value, field: str, bound: float | None = None) -> float:
    if type(value) not in (int, float):
        _error("OKL-E-TEXTURE-MAPPING", "Mapping values must be finite binary64 numbers.", field=field)
    if isinstance(value, int):
        _ExactWork.guard_bits(value.bit_length())
    try:
        result = float(value)
    except (ValueError, OverflowError):
        _error("OKL-E-TEXTURE-MAPPING", "Mapping value exceeds finite binary64 range.", field=field)
    if not math.isfinite(result) or bound is not None and abs(result) > bound:
        _error("OKL-E-TEXTURE-MAPPING", "Mapping value is nonfinite or outside its component bound.",
               field=field, bound=bound)
    return 0.0 if result == 0 else result


def _vector(values, field: str, bound: float, work: _ExactWork) -> tuple[float, float, float]:
    work.tick()
    if not isinstance(values, (tuple, list)) or len(values) != 3:
        _error("OKL-E-TEXTURE-MAPPING", "A planar mapping vector requires three components.", field=field)
    return tuple(_number(value, field, bound) for value in values)


def _mapping_numbers(origin, u, v, offset, work: _ExactWork):
    origin = _vector(origin, "origin_m", 256, work)
    u = _vector(u, "u_per_m", 1024, work)
    v = _vector(v, "v_per_m", 1024, work)
    if not isinstance(offset, (tuple, list)) or len(offset) != 2:
        _error("OKL-E-TEXTURE-MAPPING", "A planar mapping requires two offsets.")
    work.tick()
    offset = tuple(_number(value, "offset", 1024) for value in offset)
    exact_u = tuple(work.fraction(value) for value in u)
    exact_v = tuple(work.fraction(value) for value in v)
    cross = tuple(work.add(work.multiply(exact_u[a], exact_v[b]),
                           work.multiply(exact_u[b], exact_v[a]), subtract=True)
                  for a, b in ((1, 2), (2, 0), (0, 1)))
    if not any(cross):
        _error("OKL-E-TEXTURE-MAPPING", "Planar UV basis rows must have exact rank two.")
    return origin, u, v, offset


def _mapping_record(origin, u, v, offset) -> dict:
    return {"origin_m": list(origin), "u_per_m": list(u),
            "v_per_m": list(v), "offset": list(offset)}


def _make_mapping(origin, u, v, offset, node, work: _ExactWork) -> PlanarUVData:
    origin, u, v, offset = _mapping_numbers(origin, u, v, offset, work)
    work.tick()
    canonical = json.dumps(_mapping_record(origin, u, v, offset), sort_keys=True,
                           separators=(",", ":"), allow_nan=False).encode("utf-8")
    ident = "sha256:" + hashlib.sha256(MAPPING_DOMAIN + canonical).hexdigest()
    return PlanarUVData(origin, u, v, offset, ident, node.source_id, node.start, node.end)


def texture_builtin(compiler, name, args, node, ctx) -> Value:
    """Evaluate the four closed typed signatures under the declaring profile."""
    signatures = {
        "png_asset": (STRING, STRING),
        "planar_uv": (Type("Vec3", element=quantity_type(LENGTH)),
                      Type("Vec3", element=quantity_type(_INVERSE_LENGTH)),
                      Type("Vec3", element=quantity_type(_INVERSE_LENGTH)), REAL, REAL),
        "texture_binding": (Type("TextureImage"), Type("PlanarUV")),
        "texture_surface": (Type("Geometry"), Type("Keyed", element=Type("TextureBinding"))),
    }
    returns = {"png_asset": Type("TextureImage"), "planar_uv": Type("PlanarUV"),
               "texture_binding": Type("TextureBinding"), "texture_surface": Type("Geometry")}
    expected = signatures[name]
    if len(args) != len(expected):
        fail("OKL-E-TYPE", f"{name} requires {len(expected)} positional arguments.",
             node, phase="type", details={"received": len(args)})
    values = []
    for index, (arg, typ) in enumerate(zip(args, expected)):
        compiler.budget.tick(node)
        try:
            values.append(compiler.expect(arg, typ, node.args[index]))
        except OntoKinError as exc:
            if _is_callback_error(compiler, exc) or exc.code != "OKL-E-UNIT":
                raise
            # C080 assigns nominal and dimensional signature mismatches to
            # OKL-E-TYPE.  Retain inherited expectation details without
            # changing the diagnostic family of any older constructor.
            fail("OKL-E-TYPE", str(exc), node.args[index], phase="type",
                 details=exc.diagnostic.details)
    requirement = _literal_requirement(node) if name == "png_asset" else None
    if ctx.abstract or not all(value.known for value in values):
        return Value(returns[name])
    raw = [value.value for value in values]
    if name == "png_asset":
        ident, digest = requirement
        asset = getattr(compiler.model, "texture_assets", {}).get(ident)
        if asset is None or asset.sha256 != digest:
            fail("OKL-E-ASSET-CLOSURE", "Image reference does not resolve to this compiled asset closure.",
                 node, phase="binding", details={"asset_id": ident})
        return Value(returns[name], TextureImageData(ident, digest))
    if name == "planar_uv":
        origin, u, v = (tuple(component.value for component in row) for row in raw[:3])
        try:
            mapping = _make_mapping(origin, u, v, tuple(raw[3:]), node,
                                    _ExactWork(charge=lambda amount: compiler.budget.tick(node, amount=amount)))
        except SurfaceError as exc:
            if _is_callback_error(compiler, exc):
                raise
            fail(exc.code, str(exc), node, details=exc.details)
        return Value(returns[name], mapping)
    if name == "texture_binding":
        if not isinstance(raw[0], TextureImageData) or not isinstance(raw[1], PlanarUVData):
            fail("OKL-E-TYPE", "texture_binding requires typed image and planar-map values.", node, phase="type")
        return Value(returns[name], TextureBindingData(raw[0], raw[1], node.source_id, node.start, node.end))

    geometry, keyed = raw
    if (not isinstance(geometry, dict) or geometry.get("kind") not in _NATIVE_SURFACES
            or "texture_bindings" in geometry):
        fail("OKL-E-TEXTURE-REGION", "texture_surface requires one unplaced, previously untextured native surface.", node)
    if not 1 <= len(keyed.entries) <= MAX_TEXTURE_BINDINGS:
        fail("OKL-E-TEXTURE-REGION", "texture_surface requires one through 16 region bindings.",
             node, details={"count": len(keyed.entries)})
    palette = {material.key: material for material in geometry["materials"]}
    bindings = []
    seen = set()
    for key, value in keyed.entries:
        compiler.budget.tick(node)
        if key in seen or key not in palette:
            fail("OKL-E-TEXTURE-REGION", "Texture binding keys must be distinct authored material-region keys.",
                 node, details={"region": key})
        seen.add(key)
        if palette[key].rgba[3] != 1:
            fail("OKL-E-TEXTURE-REGION", "A textured material's alpha factor must equal one.",
                 node, details={"region": key})
        if not isinstance(value.value, TextureBindingData):
            fail("OKL-E-TYPE", "Each texture region requires a TextureBinding value.", node, phase="type")
        bindings.append((key, value.value))
    result = dict(geometry)
    result["texture_bindings"] = tuple(sorted(bindings, key=lambda item: item[0]))
    return Value(returns[name], result)


def _bindings(geometry) -> tuple[tuple[str, TextureBindingData], ...]:
    if not isinstance(geometry, dict):
        return ()
    surface = geometry.get("surface", geometry) if geometry.get("kind") == "placed" else geometry
    if not isinstance(surface, dict):
        return ()
    bindings = surface.get("texture_bindings", ())
    if not isinstance(bindings, tuple) or len(bindings) > MAX_TEXTURE_BINDINGS:
        _error("OKL-E-TEXTURE-REGION", "Compiled texture bindings must be an immutable bounded tuple.")
    for item in bindings:
        if (not isinstance(item, tuple) or len(item) != 2 or not isinstance(item[0], str)
                or not isinstance(item[1], TextureBindingData)):
            _error("OKL-E-TEXTURE-REGION", "Compiled texture binding is malformed.")
    return bindings


def texture_metadata(geometry, *, check: Callable[[], None] | None = None) -> dict[str, dict]:
    """Detached JSON-safe records by region; source spans name binding calls."""
    result = {}
    for key, binding in _bindings(geometry):
        if check is not None:
            check()
        mapping = binding.mapping
        result[key] = {
            "asset_id": binding.image.asset_id, "sha256": binding.image.sha256,
            **_mapping_record(mapping.origin_m, mapping.u_per_m, mapping.v_per_m, mapping.offset),
            "source_id": binding.source_id, "start": binding.start, "end": binding.end,
            "mapping_id": mapping.mapping_id,
        }
    return result


def texture_coordinates(geometry, raw_mesh, *, charge: Callable[[int], None] | None = None,
                        check: Callable[[], None] | None = None) -> dict[str, tuple[tuple[float, float], ...]]:
    """Map only a region's referenced raw corners, before every rigid placement.

    Emitted regions receive full-size UV arrays; unrelated corners are (0,0).
    Unused palette bindings emit no rows.  Binary32 conversion belongs solely
    to the exporter, after this once-rounded binary64 calculation.
    """
    bindings = _bindings(geometry)
    if not bindings:
        return {}
    work = _ExactWork(charge, check)
    work.tick()
    regions = {region.key: region for region in raw_mesh.regions}
    count = len(raw_mesh.positions)
    result = {}
    for key, binding in bindings:
        work.tick()
        region = regions.get(key)
        if region is None or not region.indices:
            continue
        mapping = binding.mapping
        origin, u, v, offset = _mapping_numbers(mapping.origin_m, mapping.u_per_m,
                                               mapping.v_per_m, mapping.offset, work)
        exact_origin = tuple(work.fraction(value) for value in origin)
        rows = tuple(tuple(work.fraction(value) for value in row) for row in (u, v))
        exact_offset = tuple(work.fraction(value) for value in offset)
        work.tick(count)
        coordinates = [(0.0, 0.0)] * count
        referenced = set()
        for ordinal, index in enumerate(region.indices):
            if ordinal % 128 == 0:
                work.tick(min(128, len(region.indices) - ordinal))
            if type(index) is not int or not 0 <= index < count:
                _error("OKL-E-TEXTURE-MAPPING", "A region references an invalid raw mesh corner.", region=key)
            referenced.add(index)
        for index in sorted(referenced):
            work.tick()
            position = raw_mesh.positions[index]
            if not isinstance(position, (tuple, list)) or len(position) != 3:
                _error("OKL-E-TEXTURE-MAPPING", "A raw mesh corner requires three finite coordinates.", region=key)
            point = tuple(work.fraction(_number(value, "position_m")) for value in position)
            delta = tuple(work.add(p, o, subtract=True) for p, o in zip(point, exact_origin))
            uv = []
            for row, base in zip(rows, exact_offset):
                exact = base
                for basis, component in zip(row, delta):
                    exact = work.add(exact, work.multiply(basis, component))
                work.tick()
                try:
                    rounded = float(exact)
                except (ValueError, OverflowError):
                    _error("OKL-E-TEXTURE-MAPPING", "A referenced UV exceeds finite binary64 range.", region=key)
                if not math.isfinite(rounded) or abs(rounded) > MAX_UV_ABS:
                    _error("OKL-E-TEXTURE-MAPPING", "A referenced UV exceeds the affine output bound.",
                           region=key, vertex=index, limit=MAX_UV_ABS)
                uv.append(0.0 if rounded == 0 else rounded)
            coordinates[index] = tuple(uv)
        result[key] = tuple(coordinates)
    return result
