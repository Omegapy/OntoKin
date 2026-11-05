"""Verify the cart crossing from the accepted source and downloaded glTF binary."""

import argparse
from bisect import bisect_right
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import re
import sys

# Isolated mode (-I) omits the script directory from the normal import path.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gate_checks as gate
from gate_checks import require


def vector_components(text, unit):
    pattern = gate.NUMBER + r"\[" + re.escape(unit) + r"\]"
    matches = [re.fullmatch(pattern, part.strip()) for part in text.split(",")]
    require(len(matches) == 3 and all(matches), "invalid three-component vector")
    return [Fraction(match[1]) for match in matches]


def cart_source(source, name):
    """Read this accepted program's cart body and integrate its force schedule."""
    object_pattern = (
        r'object\s+(\w+)\s+@\s+"' + re.escape(name)
        + r'"\s*:\s*(\w+)\s*\{([^}]*)\}'
    )
    identifier, class_name, body = re.search(object_pattern, source, re.S).groups()
    declaration = re.search(r"class\s+" + class_name + r"\b(.*?)\n}", source, re.S)[1]
    require(
        "motion = dynamic;" in declaration and "geometry =" in declaration,
        "cart must be visible and dynamic",
    )
    mass_pattern = r"sphere_body\([^,]+,\s*" + gate.NUMBER + r"\[kg\]\)"
    mass = Fraction(re.search(mass_pattern, declaration)[1])
    require(mass > 0, "cart mass")
    for field, unit in [("velocity", "m/s"), ("omega", "rad/s")]:
        vector = re.search(field + r"\s*=\s*vector\(world,\s*([^)]*)\)", body)[1]
        require(vector_components(vector, unit) == [0, 0, 0], "cart initially at rest")
    pose = re.search(r"pose\(world,\s*vec3\(([^)]*)\)", body)[1]
    position = vector_components(pose, "m")

    sequence_pattern = r"at\s+" + gate.NUMBER + r"\[s\]\s+sequence\s*\{([^}]*)\}"
    force_target = r"\bforce\s+" + identifier + r"\b"
    force_pattern = (
        force_target + r'\s+@\s*"[^"]+"\s+using\s+vector\(world,\s*([^)]*)\)'
        + r"\s+for\s+" + gate.NUMBER + r"\[s\]\s*;"
    )
    forces = []
    for start_text, events in re.findall(sequence_pattern, source):
        start = Fraction(start_text)
        for vector, duration in re.findall(force_pattern, events):
            end = start + Fraction(duration)
            force_x, force_y, force_z = vector_components(vector, "N")
            require(
                force_x == force_y == 0 and force_z != 0 and 1 <= start < end <= 2,
                "cart loads along Z during open hold",
            )
            forces.append((start, end, force_z))
    require(
        len(forces) >= 2
        and len(forces) == len(re.findall(force_target, source))
        and not re.search(r"\b(?:torque|impulse)\s+" + identifier + r"\b", source),
        "cart center-of-mass forces only",
    )

    boundaries = {Fraction(0), Fraction(13, 4)}
    for start, end, _ in forces:
        boundaries.update((start, end))
    times = sorted(boundaries)
    phases = []
    z = position[2]
    velocity = Fraction(0)
    for left, right in zip(times, times[1:]):
        force = sum(value for start, end, value in forces if start <= left < end)
        acceleration = force / mass
        dt = right - left
        phases.append(dict(
            t0=float(left), t1=float(right), z0=float(z), v0=float(velocity),
            a=float(acceleration), force_N=float(force),
        ))
        z += velocity * dt + acceleration * dt**2 / 2
        velocity += acceleration * dt
        if right >= 2:
            require(velocity == 0, "cart final velocity")
    require(velocity == 0 and z != position[2], "cart final pose and speed")
    return dict(mass_kg=float(mass), initial_m=list(map(float, position)), phases=phases)


def sample(times, rows, time):
    index = min(len(times) - 2, max(0, bisect_right(times, time) - 1))
    left, right = times[index:index + 2]
    return gate.lerp(rows[index], rows[index + 1], (time - left) / (right - left))


def score_geometry(times, tracks, local_bounds, cart):
    def bounds_at(name, time):
        translation = sample(times, tracks[name, "translation"], time)
        return [gate.add(corner, translation) for corner in local_bounds[name]]

    translations = tracks[cart, "translation"]
    direction = 1 if translations[-1][2] > translations[0][2] else -1
    require(
        all(direction * (b[2] - a[2]) >= 0 for a, b in zip(translations, translations[1:])),
        "cart changed direction",
    )
    # LINEAR tracks attain their greatest displacement at interval ends.
    waiting_times = [1] + [time for time in times if time < 1]
    parked_times = [2] + [time for time in times if time > 2]
    waiting = max(math.dist(translations[0], sample(times, translations, time))
                  for time in waiting_times)
    parked = max(math.dist(translations[-1], sample(times, translations, time))
                 for time in parked_times)
    require(waiting == parked == 0, "cart moved during stationary interval")

    leading, trailing = (1, 0) if direction == 1 else (0, 1)

    def signed_gaps(time):
        cart_bounds = bounds_at(cart, time)
        panel_bounds = bounds_at("gate", time)
        entry_gap = cart_bounds[leading][2] - panel_bounds[trailing][2]
        exit_gap = cart_bounds[trailing][2] - panel_bounds[leading][2]
        return direction * entry_gap, direction * exit_gap

    require(signed_gaps(1)[0] < 0 and signed_gaps(2)[1] > 0,
            "whole cart must pass through gate slab")

    def crossing_time(gap_index):
        gaps = [signed_gaps(time)[gap_index] for time in times]
        require(all(b >= a for a, b in zip(gaps, gaps[1:])),
                "relative travel must be monotone")
        for index, (before, after) in enumerate(zip(gaps, gaps[1:])):
            if before < 0 <= after:
                duration = times[index + 1] - times[index]
                return times[index] - before * duration / (after - before)
        raise ValueError("unbracketed crossing")

    entry = crossing_time(0)
    exit_time = crossing_time(1)
    require(1 <= entry < exit_time <= 2, "crossing outside open hold")
    crossing_times = [entry] + [t for t in times if entry < t < exit_time] + [exit_time]
    widths = []
    post_clearances = []
    panel_clearances = []
    vertical_overlaps = []
    center_offsets = []
    for time in crossing_times:
        cart_low, cart_high = bounds_at(cart, time)
        _, post_high = bounds_at("post", time)
        panel_low, panel_high = bounds_at("gate", time)
        widths.append(panel_low[0] - post_high[0])
        center_offsets.append((cart_low[0] + cart_high[0] - post_high[0] - panel_low[0]) / 2)
        post_clearances.append(cart_low[0] - post_high[0])
        panel_clearances.append(panel_low[0] - cart_high[0])
        vertical_overlaps.append(
            min(cart_high[1], panel_high[1]) - max(cart_low[1], panel_low[1])
        )

    post_clearance = min(post_clearances)
    panel_clearance = min(panel_clearances)
    require(min(vertical_overlaps) > 0, "cart passes above or below gate")
    return dict(
        z_direction=direction,
        panel_slab_z_m=[corner[2] for corner in bounds_at("gate", entry)],
        first_surface_entry_s=entry,
        last_surface_exit_s=exit_time,
        minimum_open_width_m=min(widths),
        max_abs_center_offset_m=max(map(abs, center_offsets)),
        minimum_lateral_clearance_m=dict(post=post_clearance, panel=panel_clearance),
        cart_bounds_at_entry_m=bounds_at(cart, entry),
        cart_bounds_at_exit_m=bounds_at(cart, exit_time),
        cart_bounds_at_2s_m=bounds_at(cart, 2),
        far_face_clearance_at_2s_m=signed_gaps(2)[1],
        minimum_y_overlap_with_gate_m=min(vertical_overlaps),
        continuous_crossing_intervals=len(crossing_times) - 1,
        waiting_displacement_m=waiting,
        parked_displacement_m=parked,
    )


def trajectory(times, rows, physical):
    position = physical["initial_m"]
    require(math.dist(rows[0], position) <= gate.POSITION_TOL, "cart initial pose")
    off_axis = max(math.dist(row[:2], position[:2]) for row in rows)
    worst_z_error = 0
    for index, (left, right) in enumerate(zip(times, times[1:])):
        initial_z = rows[index][2]
        slope = (rows[index + 1][2] - initial_z) / (right - left)
        for phase in physical["phases"]:
            start = max(left, phase["t0"])
            end = min(right, phase["t1"])
            if end <= start:
                continue
            # The linear-minus-quadratic error also has an extremum where
            # the exported slope equals the velocity predicted by the forces.
            candidates = [start, end]
            if phase["a"]:
                extremum = phase["t0"] + (slope - phase["v0"]) / phase["a"]
                candidates.append(max(start, min(end, extremum)))
            for time in candidates:
                dt = time - phase["t0"]
                expected = phase["z0"] + dt * phase["v0"] + 0.5 * phase["a"] * dt**2
                actual = initial_z + slope * (time - left)
                worst_z_error = max(worst_z_error, abs(actual - expected))

    bound = math.hypot(off_axis, worst_z_error)
    require(bound <= gate.POSITION_TOL, "cart continuous trajectory exceeds one millimetre")
    return dict(max_off_axis_m=off_axis, max_continuous_error_bound_m=bound)


def negative_controls(times, tracks, local_bounds, cart):
    rows = tracks[cart, "translation"]
    early = [sample(times, rows, min(t + 0.25, times[-1])) for t in times]
    beside = [(x - 2, y, z) for x, y, z in rows]
    controls = {}
    for label, positions, expected in [
        ("early_start", early, "cart moved during stationary interval"),
        ("beside", beside, "cart outside aperture or intersecting side"),
    ]:
        changed = dict(tracks)
        changed[cart, "translation"] = positions
        try:
            altered = score_geometry(times, changed, local_bounds, cart)
            require(min(altered["minimum_lateral_clearance_m"].values()) > 0,
                    "cart outside aperture or intersecting side")
        except ValueError as error:
            require(str(error) == expected, "wrong negative-control failure")
            controls[label] = str(error)
        else:
            raise ValueError("negative control passed")
    return controls


def surface_witnesses(times, tracks, triangles, crossing, cart):
    """Find actual opposing surfaces at the signed minima of this rectilinear entrance."""
    def side(a, b, p):
        return (b[1] - a[1]) * (p[2] - a[2]) - (b[2] - a[2]) * (p[1] - a[1])

    def world(name, key, point):
        return gate.add(point, tracks[name, "translation"][key])

    def find_witness(key, time, name, sign, gap):
        obstacle = [world(name, key, p) for mesh in triangles[name] for p in mesh]
        cart_vertices = sorted({world(cart, key, p) for mesh in triangles[cart] for p in mesh})
        x_extent = (min(p[0] for p in obstacle), max(p[0] for p in obstacle))
        inside_face_x = x_extent[1 if sign == 1 else 0]
        for i in range(0, len(obstacle), 3):
            a, b, c = obstacle[i:i + 3]
            if not a[0] == b[0] == c[0] == inside_face_x or not side(a, b, c):
                continue
            for point in cart_vertices:
                signed = sign * (point[0] - inside_face_x)
                if abs(signed - gap) > 1e-8:
                    continue
                signs = [side(a, b, point), side(b, c, point), side(c, a, point)]
                if min(signs) < 0 < max(signs):
                    continue
                return dict(time_s=time, signed_gap_m=signed,
                            cart_vertex_world_m=point, projection_world_m=[a[0], *point[1:]],
                            obstacle_triangle_world_m=[a, b, c], obstacle_x_extent_m=x_extent,
                            vertex_inside_obstacle_x=x_extent[0] < point[0] < x_extent[1])

    gaps = crossing["minimum_lateral_clearance_m"]
    witnesses = {}
    for key, time in enumerate(times):
        if not crossing["first_surface_entry_s"] < time < crossing["last_surface_exit_s"]:
            continue
        for name, label, sign in [("post", "post", 1), ("gate", "panel", -1)]:
            if label not in witnesses:
                witness = find_witness(key, time, name, sign, gaps[label])
                if witness is not None:
                    witnesses[label] = witness
        if len(witnesses) == 2:
            break
    return witnesses


def main(source, bundle, glb, width=None):
    src = source.read_text()
    require(src == json.loads(bundle.read_text())["entry"]["source"], "accepted source mismatch")
    raw = glb.read_bytes()
    graph, data = gate.read_glb(raw)
    times, tracks, _ = gate.read_tracks(graph, data)
    original = gate.measure(raw, gate.source_dynamics(src))
    cart, = {node["name"] for node in graph["nodes"]} - {"gate", "post"}
    physics = cart_source(src, cart)
    local_bounds = {}
    triangles = {}
    obstacle_hashes = {}
    for node in graph["nodes"]:
        name = node["name"]
        rotations = tracks[name, "rotation"]
        require(all(gate.align(rotations[0], q) == rotations[0] for q in rotations),
                "rigid translation only")
        primitives = gate.surfaces(graph, data, node)
        require(all(len(points) % 3 == 0 for points in primitives), "incomplete triangle")
        triangles[name] = [[gate.rotate(rotations[0], point) for point in primitive]
                           for primitive in primitives]
        if name in ("post", "gate"):
            obstacle_hashes[name] = hashlib.sha256(json.dumps(primitives).encode()).hexdigest()
        points = {point for primitive in triangles[name] for point in primitive}
        require(len(points) >= 8, "expected solid mesh")
        bounds = [list(map(op, zip(*points))) for op in (min, max)]
        require(all(high > low for low, high in zip(*bounds)), "zero-thickness mesh")
        local_bounds[name] = bounds

    crossing = score_geometry(times, tracks, local_bounds, cart)
    witnesses = surface_witnesses(times, tracks, triangles, crossing, cart)
    low, high = local_bounds[cart]
    mesh = dict(local_bounds_m=local_bounds[cart], width_m=high[0] - low[0],
                length_m=high[2] - low[2], height_m=high[1] - low[1])
    rows = tracks[cart, "translation"]
    gaps = crossing["minimum_lateral_clearance_m"]
    diagnostics = []
    if min(gaps.values()) <= 0:
        diagnostics.append("cart outside aperture or intersecting side")
    if crossing["max_abs_center_offset_m"] > gate.POSITION_TOL:
        diagnostics.append("cart is off center")
    if width is not None and (not math.isfinite(width) or abs(mesh["width_m"] - width) > 1e-6):
        diagnostics.append("cart mesh width differs from requested width")
    if len(witnesses) != 2:
        diagnostics.append("could not establish both side gaps on actual mesh faces")
    return dict(
        result="REJECTED" if diagnostics else "PASS",
        diagnostics=diagnostics,
        cart_mesh=mesh,
        cart_travel_z_m=rows[-1][2]-rows[0][2],
        surface_witnesses=witnesses,
        obstacle_mesh_sha256=obstacle_hashes,
        animation_tracks_sha256=hashlib.sha256(json.dumps(
            [times, [(k, tracks[k]) for k in sorted(tracks)]]).encode()).hexdigest(),
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        glb_sha256=hashlib.sha256(raw).hexdigest(),
        cart_source=physics,
        gate=original,
        cart_trajectory=trajectory(times, tracks[cart, "translation"], physics),
        crossing=crossing,
        controls=negative_controls(times, tracks, local_bounds, cart),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ["source", "bundle", "glb"]:
        parser.add_argument(key, type=Path)
    parser.add_argument("--width", type=float, help="expected full cart mesh width in metres")
    result = main(**vars(parser.parse_args()))
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["result"] == "PASS" else 1)
