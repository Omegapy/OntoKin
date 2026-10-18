"""Native surface-0.1 pure constructors and bounded source-to-mesh lowering.

This module receives only type-checked OntoKin values. The loft recipe
remains a rigid visual geometry value. It is not a physical body and does
not introduce a node or action authority. GLB/0.3 delivery is separate.
"""
from __future__ import annotations

from .model import Pose
from .surface import LoftSection, SurfaceMaterial, SurfaceError, triangulate_loft
from .validator import fail
from .values import INT, REAL, STRING, LENGTH, Type, Value, quantity_type


SURFACE_CALLS = frozenset({"loft_section", "surface_material", "loft", "placed"})
SURFACE_TYPES = frozenset({"LoftSection", "SurfaceMaterial"})
SURFACE_PROFILE = "surface-0.1"


def _known(ctx, args):
    return not ctx.abstract and all(arg.known for arg in args)


def surface_builtin(compiler, name, args, node, ctx):
    """Evaluate a closed positional surface builtin, retaining source provenance."""
    types = {
        "loft_section": [quantity_type(LENGTH),
                         Type("Vec3", element=quantity_type(LENGTH)),
                         quantity_type(LENGTH), quantity_type(LENGTH), STRING],
        "surface_material": [Type("Color"), REAL, REAL],
        "loft": [Type("Keyed", element=Type("LoftSection")),
                 Type("Keyed", element=Type("SurfaceMaterial")), INT, STRING],
        "placed": [Type("Geometry"), Type("Pose")],
    }
    return_types = {
        "loft_section": Type("LoftSection"),
        "surface_material": Type("SurfaceMaterial"),
        "loft": Type("Geometry"),
        "placed": Type("Geometry"),
    }
    expected = types[name]
    if len(args) != len(expected):
        fail("OKL-E-TYPE", f"{name} requires {len(expected)} positional arguments.",
             node, phase="type", details={"received": len(args)})
    values = [compiler.expect(arg, typ, node.args[i])
              for i, (arg, typ) in enumerate(zip(args, expected))]
    if name == "loft" and node.args[3].kind != "string":
        fail("OKL-E-SURFACE-CAPS", "Loft cap mode must be a string literal.",
             node.args[3], phase="type")
    if not _known(ctx, values):
        return Value(return_types[name])
    raw = [v.value for v in values]
    if name == "loft_section":
        center = tuple(component.value for component in raw[1])
        return Value(Type("LoftSection"),
                     (raw[0], center, raw[2], raw[3], raw[4]))
    if name == "surface_material":
        if not all(0 <= factor <= 1 for factor in raw[1:]):
            fail("OKL-E-SURFACE-MATERIAL", "PBR factors must lie in [0,1].",
                 node, details={"metallic": raw[1], "roughness": raw[2]})
        return Value(Type("SurfaceMaterial"), (tuple(raw[0]), raw[1], raw[2]))
    if name == "loft":
        sections = tuple(LoftSection(key, *value.value)
                         for key, value in raw[0].entries)
        materials = tuple(SurfaceMaterial(key, *value.value)
                          for key, value in raw[1].entries)
        return Value(Type("Geometry"), {
            "kind": "loft", "sections": sections, "materials": materials,
            "facets": raw[2], "caps": raw[3],
            "source_id": node.source_id, "start": node.start, "end": node.end,
        })
    if name == "placed":
        geometry, pose = raw
        if not isinstance(geometry, dict) or geometry.get("kind") != "loft":
            fail("OKL-E-SURFACE-PLACEMENT",
                 "placed() requires one native loft, not a nested placement.",
                 node, phase="type")
        if ctx.self_path is None or pose.frame != ctx.self_path + ".frame":
            fail("OKL-E-SURFACE-PLACEMENT",
                 "Local visual placement must reference its own object's self.frame.",
                 node, phase="type",
                 details={"frame": pose.frame, "owner": ctx.self_path})
        return Value(Type("Geometry"), {
            "kind": "placed", "surface": geometry,
            "local_position": tuple(pose.position),
            "local_rotation": tuple(pose.rotation),
            "source_id": node.source_id, "start": node.start, "end": node.end,
        })
    raise AssertionError("Unexpected surface constructor")


def materialize_surface(recipe, *, max_vertices: int, check=None):
    """Produce actual bounded triangle geometry from a compiled .ok recipe.

    The model's local visual placement is returned separately and is never
    reinterpreted as a physical pose or an independent scene node.
    """
    if recipe["kind"] == "placed":
        surface = recipe["surface"]
        placement = Pose("self", tuple(recipe["local_position"]),
                         tuple(recipe["local_rotation"]))
    else:
        surface = recipe
        placement = Pose("self")
    if surface["kind"] != "loft":
        raise SurfaceError("OKL-E-SURFACE-SECTION", "Expected a native loft.")
    mesh = triangulate_loft(surface["sections"], surface["materials"],
                            surface["facets"], surface["caps"],
                            max_vertices=max_vertices, check=check)
    return mesh, placement
