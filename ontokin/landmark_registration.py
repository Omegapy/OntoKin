"""Fit an environment-to-world transform from a pinned landmark plan and independent picks."""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path

from .composite_manifest import _cross, _json, _keys, _read, _span_plane, _vector, check_registration, require
from .external_gltf import preflight_splat_glb


def _largest_eigenvector(matrix):
    """Jacobi rotations for Horn's real symmetric 4 by 4 quaternion matrix."""
    vectors = [[float(i == j) for j in range(4)] for i in range(4)]
    pairs = list(itertools.combinations(range(4), 2))
    threshold = 1e-15 * max(abs(value) for row in matrix for value in row)
    for _ in range(80):
        p, q = max(pairs, key=lambda pair: abs(matrix[pair[0]][pair[1]]))
        off = matrix[p][q]
        if abs(off) <= threshold:
            k = max(range(4), key=lambda i: matrix[i][i])
            return [row[k] for row in vectors]
        pp, qq = matrix[p][p], matrix[q][q]
        angle = 0.5 * math.atan2(2 * off, qq - pp)
        c, s = math.cos(angle), math.sin(angle)
        for i in range(4):
            if i not in (p, q):
                a, b = matrix[i][p], matrix[i][q]
                matrix[i][p] = matrix[p][i] = c * a - s * b
                matrix[i][q] = matrix[q][i] = s * a + c * b
            a, b = vectors[i][p], vectors[i][q]
            vectors[i][p], vectors[i][q] = c * a - s * b, s * a + c * b
        matrix[p][p] = c*c*pp - 2*c*s*off + s*s*qq
        matrix[q][q] = s*s*pp + 2*c*s*off + c*c*qq
        matrix[p][q] = matrix[q][p] = 0.0
    raise ValueError("Landmark rotation solver did not converge")


def _dot(a, b):
    return math.fsum(x * y for x, y in zip(a, b))


def _center(points):
    mean = [math.fsum(axis) / len(points) for axis in zip(*points)]
    return mean, [[x - y for x, y in zip(p, mean)] for p in points]


def _fit(src, dst, kind):
    # Horn (1987), doi:10.1364/JOSAA.4.000629. Maximize the correspondence
    # dot products over proper rotations. Scale minimizes errors in world metres.
    cs, a = _center(src)
    cd, b = _center(dst)
    (xx, xy, xz), (yx, yy, yz), (zx, zy, zz) = [
        [math.fsum(u[i] * v[j] for u, v in zip(a, b)) for j in range(3)]
        for i in range(3)]
    quaternion = _largest_eigenvector([
        [xx+yy+zz, yz-zy, zx-xz, xy-yx],
        [yz-zy, xx-yy-zz, xy+yx, zx+xz],
        [zx-xz, xy+yx, yy-xx-zz, yz+zy],
        [xy-yx, zx+xz, yz+zy, zz-xx-yy]])
    w, x, y, z = (v / math.hypot(*quaternion) for v in quaternion)
    rotation = [
        [1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
        [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
        [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]]
    scale = 1.0
    if kind == "similarity":
        rotated = [[_dot(row, u) for row in rotation] for u in a]
        numerator = math.fsum(_dot(u, v) for u, v in zip(rotated, b))
        scale = numerator / math.fsum(_dot(u, u) for u in a)
    require(1e-6 <= scale <= 1e6, "Fitted scale outside the positive C177 range")
    translation = [v - scale * _dot(row, cs) for v, row in zip(cd, rotation)]
    # glTF and Three.js both consume the affine transform in column-major order.
    matrix = []
    for column in zip(*rotation):
        matrix.extend(scale * value for value in column)
        matrix.append(0)
    return scale, [*matrix, *translation, 1]


def _altitude(points):
    """Largest perpendicular distance from the longest baseline, in this frame."""
    a, b = max(itertools.combinations(points, 2), key=lambda pair: math.dist(*pair))
    length = math.dist(a, b)
    axis = [(x - y) / length for x, y in zip(a, b)]
    return max(math.hypot(*_cross(axis, [x-y for x, y in zip(p, a)])) for p in points)


def _errors(anchors, matrix, tolerance):
    values = {}
    for point in anchors:
        loc = point["environment"]
        predicted = [math.fsum(matrix[4*j+i]*loc[j] for j in range(3)) + matrix[12+i] for i in range(3)]
        values[point["name"]] = math.dist(predicted, point["world"])
    return {"count": len(values), "anchorResidualsM": values,
            "rmsResidualM": math.hypot(*values.values()) / math.sqrt(len(values)) if values else None,
            "maxResidualM": max(values.values(), default=None),
            "passesTolerance": max(values.values()) <= tolerance if values else None}


def register(plan_path, picks_path, environment_path):
    plan_bytes = _read(Path(plan_path), 65536)
    picks_bytes = _read(Path(picks_path), 65536)
    plan, picks = _json(plan_bytes), _json(picks_bytes)
    _keys(plan, "schema", "kind", "environmentSha256", "referenceMethod", "scaleBasis",
          "referenceUncertaintyM", "toleranceM", "toleranceBasis", "minimumAltitudeM", "landmarks")
    _keys(picks, "schema", "planSha256", "environmentMethod", "environment")
    require(plan["schema"] == "ontokin-landmark-plan/1" and picks["schema"] == "ontokin-landmark-picks/1",
            "Unknown plan or picks schema")
    plan_hash = hashlib.sha256(plan_bytes).hexdigest()
    require(picks["planSha256"] == plan_hash, "Frozen plan SHA-256 mismatch")
    require(plan["kind"] in ("rigid", "similarity"), "Expected rigid or similarity")
    require(all(isinstance(v, str) and v.strip() for v in
                [plan["referenceMethod"], plan["scaleBasis"], plan["toleranceBasis"], picks["environmentMethod"]]),
            "Document the world measurement, scale, tolerance and environment picking methods")
    tolerance, uncertainty, minimum = (plan[k] for k in ("toleranceM", "referenceUncertaintyM", "minimumAltitudeM"))
    require(all(type(v) in (int, float) for v in (tolerance, uncertainty, minimum))
            and 0 <= uncertainty <= tolerance <= 1 and tolerance < minimum <= 1e6,
            "Expected 0 <= reference uncertainty <= tolerance <= 1 metre and a larger minimum landmark altitude")
    landmarks = plan["landmarks"]
    require(isinstance(landmarks, list) and 3 <= len(landmarks) <= 64, "Expected 3 to 64 landmarks")
    observed = picks["environment"]
    require(isinstance(observed, dict), "Expected named environment picks")
    fit, holdout, names = [], [], set()
    for landmark in landmarks:
        _keys(landmark, "name", "role", "world")
        name, role = landmark["name"], landmark["role"]
        require(isinstance(name, str) and 1 <= len(name.strip()) <= 128 and name not in names and name in observed,
                "Expected unique declared names with corresponding environment picks")
        require(role in ("fit", "holdout"), "Unknown landmark role")
        names.add(name)
        _vector(landmark["world"], 3)
        _vector(observed[name], 3)
        (fit if role == "fit" else holdout).append(
            {"name": name, "world": landmark["world"], "environment": observed[name]})
    require(names == observed.keys(), "Unexpected environment picks")
    require(len(fit) >= 3, "At least three fit landmarks are required")
    for frame in ("world", "environment"):
        require(len({tuple(a[frame]) for a in fit + holdout}) == len(names),
                "Duplicated physical point within or across roles")
    source = [a["environment"] for a in fit]
    target = [a["world"] for a in fit]
    require(_span_plane(source) and _span_plane(target), "Fit landmarks must span a plane in both frames")
    asset = preflight_splat_glb(environment_path, plan["environmentSha256"])
    scale, matrix = _fit(source, target, plan["kind"])
    _vector(matrix, 16)
    altitude = {"environmentInMetres": scale * _altitude(source), "worldM": _altitude(target)}
    require(min(altitude.values()) >= minimum, "Fit landmarks do not meet the frozen minimum altitude")
    train, test = _errors(fit, matrix, tolerance), _errors(holdout, matrix, tolerance)
    passed = train["passesTolerance"] and test["passesTolerance"] is not False
    registration = None
    if passed:
        registration = {"kind": plan["kind"], "worldUnit": "metre", "toleranceM": tolerance,
                        "matrix": matrix, "anchors": fit + holdout}
        check_registration(registration)
    return {"schema": "ontokin-landmark-fit/1", "passesTolerance": passed, "planSha256": plan_hash,
            "picksSha256": hashlib.sha256(picks_bytes).hexdigest(), "environment": asset,
            "direction": "environment scene coordinates to authored world metres", "kind": plan["kind"],
            "scale": scale, "matrixColumnMajor": matrix, "toleranceM": tolerance, "altitude": altitude,
            "fit": train, "holdout": test, "registration": registration}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for param in ("plan", "picks", "environment_glb"):
        parser.add_argument(param, type=Path)
    args = parser.parse_args()
    try:
        result = register(args.plan, args.picks, args.environment_glb)
        print(json.dumps(result, indent=2, allow_nan=False))
        raise SystemExit(0 if result["passesTolerance"] else 1)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Invalid landmark registration: {exc}\n")
