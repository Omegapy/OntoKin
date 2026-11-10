#!/usr/bin/env python3
"""Qualify one two-carriage gauge against the frozen C187 design."""
import argparse
import itertools
import json
import sys
from pathlib import Path

import numpy as np

from gltf import Scene, require

DEFAULT_DESIGN = Path(__file__).with_name("assembly.json")
SURFACE_MM = 0.0001
COVERAGE_FRACTION = 2e-6
CONTACT_MM = 0.001
RATE_MM_S = 0.025


def cross(a, b):
    return a[0]*b[1] - a[1]*b[0]


def polygon_area(p):
    if len(p) < 3:
        return 0.0
    return abs(sum(cross(p[i]-p[0], p[i+1]-p[0]) for i in range(1, len(p)-1))) / 2


def intersection_area(a, b):
    """Clip one CCW triangle by the three closed half-planes of another."""
    polygon = list(a)
    for start, end in zip(b, np.roll(b, -1, axis=0)):
        if not polygon:
            break
        edge, clipped = end-start, []
        prev = polygon[-1]
        prev_side = cross(edge, prev-start)
        for point in polygon:
            side = cross(edge, point-start)
            if (side >= 0) != (prev_side >= 0):
                clipped.append(prev + (point-prev)*(prev_side/(prev_side-side)))
            if side >= 0:
                clipped.append(point)
            prev, prev_side = point, side
        polygon = clipped
    return polygon_area(polygon)


def certify_shell(name, triangles, bounds, parity):
    """Prove rectangular surface cover using normalized per-face triangles."""
    lo, hi = bounds
    span = hi-lo
    require((span > 2*SURFACE_MM).all(), f"{name}: collapsed cuboid")
    faces = {(axis, side): [] for axis in range(3) for side in (0, 1)}
    for tri in triangles:
        faces_hit = [key for key in faces
                     if np.max(np.abs(tri[:, key[0]]-bounds[key[1], key[0]])) <= SURFACE_MM]
        require(len(faces_hit) == 1, f"{name}: triangle off cuboid faces or degenerate")
        axis, side = faces_hit[0]
        dims = [(axis+1) % 3, (axis+2) % 3]
        projected = ((tri-lo)/span)[:, dims]
        oriented_area2 = cross(projected[1]-projected[0], projected[2]-projected[0])
        outward = (2*side-1) * parity
        require(oriented_area2 * outward > 1e-14, f"{name}: inward or degenerate triangle")
        if oriented_area2 < 0:
            projected = projected[[0, 2, 1]]
        faces[axis, side].append(projected)

    area_errors, overlaps = [], []
    for key, face in faces.items():
        total, overlap = 0., 0.
        prior = []
        for tri in face:
            low, high = tri.min(0), tri.max(0)
            for other, a, b in prior:
                if np.all(np.minimum(b, high) > np.maximum(a, low)):
                    overlap += intersection_area(other, tri)
            prior.append((tri, low, high))
            total += polygon_area(tri)
        # total minus the sum of pairwise intersections is a lower bound on union area.
        # Every projection is contained in this unit rectangle by construction.
        require(overlap <= COVERAGE_FRACTION and 1 - (total-overlap) <= COVERAGE_FRACTION
                and abs(1-total) <= COVERAGE_FRACTION,
                f"{name}: incomplete or overlapping cuboid face {key}")
        area_errors.append(abs(total-1))
        overlaps.append(overlap)

    # Use a local origin to avoid cancellation. glTF reverses front-face parity
    # when an instance's world transform has negative determinant.
    a, b, c = (triangles-lo).transpose(1, 0, 2)
    volume = float(parity * np.einsum("ij,ij->i", a, np.cross(b, c)).sum()/6)
    expected = float(np.prod(span))
    require(abs(volume/expected-1) <= 1e-5, f"{name}: cuboid volume inconsistent with bounds")
    return {"triangles": len(triangles), "faceTriangleCounts": [len(x) for x in faces.values()],
            "maxFaceAreaErrorFraction": max(area_errors), "maxFaceOverlapFraction": max(overlaps),
            "orientedVolumeMm3": volume, "boundsVolumeMm3": expected}


def swept_overlap(a0, a1, b0, b1):
    """Return a witness fraction if all 6 strict slab inequalities hold together."""
    starts = np.concatenate([a0[1]-b0[0], b0[1]-a0[0]]) - CONTACT_MM
    ends = np.concatenate([a1[1]-b1[0], b1[1]-a1[0]]) - CONTACT_MM
    left, right = 0., 1.
    for x, y in zip(starts, ends):
        if max(x, y) <= 0:
            return None
        if x <= 0:
            left = max(left, float(-x/(y-x)))
        elif y <= 0:
            right = min(right, float(-x/(y-x)))
    return (left+right)/2 if right > left else None


def evaluate(path, design, report):
    rule = json.loads(Path(design).read_text())
    dims = {p["id"]: p for p in rule["parts"]}
    tolerance = rule["tolerances"]
    scene = Scene(path, set(dims))
    knots = scene.knots
    duration = rule["motion"]["durationS"]
    travel = np.asarray(rule["motion"]["travelMm"], dtype=float)
    require(knots[0] == 0 and knots[-1] == duration, "incorrect clip duration")
    probes = np.unique(np.r_[knots, (knots[1:]+knots[:-1])/2, duration*np.array([.25, .5, .75])])
    worlds, _ = scene.transforms(probes)
    kindex = np.searchsorted(probes, knots)
    report["trajectory"] = {"durationS": float(duration), "knotsS": knots.tolist(),
                            "probeTimesS": probes.tolist(), "certifiedIntervals": len(knots)-1}
    boxes, moving = {}, {}
    for name, spec in dims.items():
        node, local, colors = scene.parts[name]
        world = worlds[node]
        require(np.isfinite(world).all(), f"{name}: invalid world matrix")
        basis = world[0, :3, :3]
        det = float(np.linalg.det(basis))
        require(det != 0 and np.array_equal(world[:, :3, :3], np.broadcast_to(basis, (len(world),3,3))),
                f"{name}: singular or changing world orientation/scale")
        # With fixed ancestor bases, all vertices have this same displacement
        # regardless of the node's local basis, pivots or stacked translation tracks.
        tri = 1000*(local @ basis.T + world[0, :3, 3])
        start = np.stack([tri.min((0, 1)), tri.max((0, 1))])
        record = report["parts"][name] = {"boundsAt0Mm": start.tolist(), "linearRGB": colors.tolist()}
        err = float(np.max(np.abs(start - np.array(spec["worldBoundsAt0Mm"]))))
        require(err <= tolerance["boundsAndWorldPositionsMm"], f"{name}: world bounds error {err:.7g} mm")
        color_err = float(np.max(np.abs(colors - np.asarray(spec["baseColorLinearRGB"]))))
        require(color_err <= tolerance["colorMaxChannelError"], f"{name}: material RGB error {color_err:.7g}")
        record.update(certify_shell(name, tri, start, 1 if det > 0 else -1))
        displacement = 1000*(world[:, :3, 3] - world[0, :3, 3])
        speed = travel/duration if spec["motion"] == "translate" else np.zeros(3)
        measured = np.diff(displacement[kindex], axis=0) / np.diff(knots)[:, None]
        average = displacement[-1]/duration
        straight_rate_error = float(np.max(np.abs(measured-average)))
        nominal_rate_error = float(np.max(np.abs(measured-speed)))
        # Use the absolute nominal design at every probe as well as relative motion.
        absolute = start + displacement[:, None, :]
        expected = np.asarray(spec["worldBoundsAt0Mm"]) + probes[:, None, None]*speed
        position_err = float(np.max(np.abs(absolute-expected)))
        relative_err = float(np.max(np.abs(displacement-probes[:, None]*speed)))
        record.update({"initialBoundsErrorMm": err, "colorMaxChannelError": color_err,
                       "boundsAt2Mm": absolute[-1].tolist(), "displacementMm": displacement[-1].tolist(),
                       "maxWorldPositionErrorMm": position_err, "maxDisplacementErrorMm": relative_err,
                       "maxComponentVelocityErrorMmPerS": nominal_rate_error,
                       "maxSegmentDeviationFromMeanVelocityMmPerS": straight_rate_error,
                       "velocityMinMmPerS": measured.min(0).tolist(), "velocityMaxMmPerS": measured.max(0).tolist()})
        require(position_err <= tolerance["boundsAndWorldPositionsMm"] and
                relative_err <= tolerance["boundsAndWorldPositionsMm"],
                f"{name}: world trajectory error {max(position_err, relative_err):.7g} mm")
        require(straight_rate_error <= RATE_MM_S,
                f"{name}: segment velocity error {straight_rate_error:.7g} mm/s")
        if spec["motion"] == "translate":
            require((measured[:,0] > 0).all() and np.max(np.abs(displacement[:,1:])) <= CONTACT_MM,
                    f"{name}: travel must follow positive X only")
            moving[name] = (displacement, measured)
        else:
            require(np.max(np.abs(displacement)) <= CONTACT_MM, f"{name}: fixed body drifts")
        boxes[name] = absolute[kindex]

    common_rate_error, common_displacement_error = 0., 0.
    for a, b in itertools.combinations(moving, 2):
        disp = float(np.max(np.abs(moving[a][0]-moving[b][0])))
        rate = float(np.max(np.abs(moving[a][1]-moving[b][1])))
        common_rate_error = max(common_rate_error, rate)
        common_displacement_error = max(common_displacement_error, disp)
        require(disp <= CONTACT_MM and rate <= RATE_MM_S, f"{a} / {b}: unequal moving travel")
    report["trajectory"].update({"maxMovingPairVelocityDifferenceMmPerS": common_rate_error,
                                 "maxMovingPairDisplacementDifferenceMm": common_displacement_error})

    pairs = list(itertools.combinations(boxes, 2))
    for a, b in pairs:
        for j, (t0, t1) in enumerate(zip(knots, knots[1:])):
            u = swept_overlap(boxes[a][j], boxes[a][j+1], boxes[b][j], boxes[b][j+1])
            require(u is None, f"{a} / {b}: interior overlap on interval [{t0}, {t1}]")
    report["clearance"] = {"certifiedNonoverlapPairs": len(pairs), "allowedNumericalContactMm": CONTACT_MM}
    for lane in ("left", "right"):
        stop, shoe = boxes[lane+"_stop"], boxes[lane+"_shoe"]
        gap = stop[:, 0, 0] - shoe[:, 1, 0]
        yz = np.minimum(stop[:, 1, 1:], shoe[:, 1, 1:]) - np.maximum(stop[:, 0, 1:], shoe[:, 0, 1:])
        require((yz > 0).all(), f"{lane}: mismatched faces without positive Y/Z overlap")
        require((np.diff(gap) < 0).all(), f"{lane}: gap must decrease strictly on every interval")
        j = int(np.argmin(gap))
        report["gaps"][lane] = {"startMm": float(gap[0]), "endMm": float(gap[-1]),
                                "minimumMm": float(gap[j]), "minimumAtS": float(knots[j]),
                                "minOverlapYMm": float(yz[:, 0].min()), "minOverlapZMm": float(yz[:, 1].min())}
        g, gt = rule["gap"], tolerance["minimumGapMm"]
        require(abs(gap[0]-g["expectedAtStartMm"]) <= gt and abs(gap[j]-g["expectedAtEndMm"]) <= gt
                and knots[j] == g["minimumTimeS"], f"{lane}: incorrect gap or minimum time")


def check(path, design=DEFAULT_DESIGN):
    result = {"pass": False, "parts": {}, "gaps": {}}
    try:
        evaluate(path, design, result)
        result["pass"] = True
    except (ValueError, OSError, KeyError, IndexError, TypeError, OverflowError, ArithmeticError) as exc:
        result["reason"] = str(exc)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("glb", type=Path)
    p.add_argument("--design", type=Path, default=DEFAULT_DESIGN)
    p.add_argument("--out", type=Path)
    args = p.parse_args()
    result = check(args.glb, args.design)
    content = json.dumps(result, indent=2, allow_nan=False)+"\n"
    if args.out:
        args.out.write_text(content)
    else:
        sys.stdout.write(content)
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
