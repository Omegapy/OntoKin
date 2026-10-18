"""Small indexed triangle meshes for the experimental GLB adapter.

Geometry is visual data. These meshes never determine mass, collision shape,
joint behavior, or the trajectory calculated by the reference evaluator.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .model import Vec


SPHERE_SEGMENTS = 32
SPHERE_RINGS = 16


@dataclass(frozen=True)
class Mesh:
    name: str
    positions: tuple[Vec, ...]
    normals: tuple[Vec, ...]
    indices: tuple[int, ...]


def box_mesh(size: Vec) -> Mesh:
    """Center a box at the origin; ``size`` contains its full XYZ lengths."""
    x, y, z = (value / 2 for value in size)
    faces = (
        ((1., 0., 0.), ((x, -y, -z), (x, y, -z), (x, y, z), (x, -y, z))),
        ((-1., 0., 0.), ((-x, -y, z), (-x, y, z), (-x, y, -z), (-x, -y, -z))),
        ((0., 1., 0.), ((-x, y, -z), (-x, y, z), (x, y, z), (x, y, -z))),
        ((0., -1., 0.), ((-x, -y, z), (-x, -y, -z), (x, -y, -z), (x, -y, z))),
        ((0., 0., 1.), ((-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z))),
        ((0., 0., -1.), ((x, -y, -z), (-x, -y, -z), (-x, y, -z), (x, y, -z))),
    )
    vertices, normals, indices = [], [], []
    for normal, corners in faces:
        offset = len(vertices)
        vertices.extend(corners)
        normals.extend([normal] * 4)
        indices.extend(offset + index for index in (0, 1, 2, 0, 2, 3))
    return Mesh("box", tuple(vertices), tuple(normals), tuple(indices))


def sphere_mesh(radius: float, segments: int = SPHERE_SEGMENTS,
                rings: int = SPHERE_RINGS) -> Mesh:
    """Create a closed Y-up sphere without duplicated or degenerate poles."""
    if not math.isfinite(radius) or radius <= 0 or segments < 3 or rings < 2:
        raise ValueError("A sphere requires a positive radius and at least 3 segments/2 bands.")
    normals: list[Vec] = [(0., 1., 0.)]
    for latitude in range(1, rings):
        theta = math.pi * latitude / rings
        for longitude in range(segments):
            phi = 2 * math.pi * longitude / segments
            normals.append((math.sin(theta) * math.cos(phi), math.cos(theta),
                            math.sin(theta) * math.sin(phi)))
    bottom = len(normals)
    normals.append((0., -1., 0.))
    indices: list[int] = []
    for longitude in range(segments):
        following = (longitude + 1) % segments
        indices.extend((0, 1 + following, 1 + longitude))
    for latitude in range(rings - 2):
        upper, lower = 1 + latitude * segments, 1 + (latitude + 1) * segments
        for longitude in range(segments):
            following = (longitude + 1) % segments
            indices.extend((upper + longitude, upper + following, lower + longitude,
                            upper + following, lower + following, lower + longitude))
    last = 1 + (rings - 2) * segments
    for longitude in range(segments):
        indices.extend((last + longitude, last + (longitude + 1) % segments, bottom))
    return Mesh("sphere", tuple(tuple(radius * v for v in normal) for normal in normals),
                tuple(normals), tuple(indices))


def _combine(name: str, meshes: list[Mesh]) -> Mesh:
    vertices, normals, indices = [], [], []
    for mesh in meshes:
        offset = len(vertices)
        vertices.extend(mesh.positions)
        normals.extend(mesh.normals)
        indices.extend(index + offset for index in mesh.indices)
    return Mesh(name, tuple(vertices), tuple(normals), tuple(indices))


def assembly_marker() -> Mesh:
    """A deliberately small origin cross, unrelated to the assembly's shape."""
    return _combine("visual helper: assembly origin", [
        box_mesh((.14, .012, .012)), box_mesh((.012, .14, .012)),
        box_mesh((.012, .012, .14)),
    ])


def joint_marker(axis: Vec | None) -> Mesh:
    """Mark a parent attachment site, and the prescribed axis when it has one."""
    sphere = sphere_mesh(.025, 12, 6)
    if axis is None:
        return Mesh("visual helper: joint parent site", sphere.positions, sphere.normals, sphere.indices)
    # Form an orthonormal basis whose local Y axis is the joint axis.
    reference = (1., 0., 0.) if abs(axis[0]) < .8 else (0., 0., 1.)
    cross = (axis[1] * reference[2] - axis[2] * reference[1],
             axis[2] * reference[0] - axis[0] * reference[2],
             axis[0] * reference[1] - axis[1] * reference[0])
    norm = math.hypot(*cross)
    u = tuple(value / norm for value in cross)
    v = (u[1] * axis[2] - u[2] * axis[1], u[2] * axis[0] - u[0] * axis[2],
         u[0] * axis[1] - u[1] * axis[0])
    def orient(vector: Vec) -> Vec:
        return tuple(vector[0] * u[i] + vector[1] * axis[i] + vector[2] * v[i]
                     for i in range(3))
    bar = box_mesh((.012, .18, .012))
    bar = Mesh(bar.name, tuple(map(orient, bar.positions)), tuple(map(orient, bar.normals)), bar.indices)
    return _combine("visual helper: joint parent site and axis", [sphere, bar])
