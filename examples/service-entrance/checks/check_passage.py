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


def example_source(text):
    """Keep stable keys and exclude comments and free text from the example's pattern checks."""
    # The language accepts // line comments, non-nested /* blocks */ and escaped quotes.
    tokens = r'"(?:\\.|[^"\\])*"|//[^\r\n]*|/\*[\s\S]*?\*/'

    def replace(match):
        token = match[0]
        if token.startswith('"'):
            # Only stable keys are significant strings for these scene checks.
            return token if re.fullmatch(r'"[A-Za-z0-9][A-Za-z0-9._-]{0,63}"', token) else '""'
        return ' '

    return re.sub(tokens, replace, text)


def select_carts(source, graph, revision, accepted, moving_cart, parked_cart):
    objects = re.findall(r'\bobject\s+(\w+)\s+@\s*"([^"]+)"\s*:\s*(\w+)\s*\{([^}]*)\}', source)
    nodes = graph['nodes']
    names = [n.get('name') for n in nodes]
    require(len(set(names)) == len(names), 'ambiguous delivered node names')
    candidates = [o for o in objects if o[0] not in ('gate', 'post')]
    require(len(candidates) in (1, 2), 'expected one passing cart and at most one parked cart')
    if len(candidates) == 2:
        require(moving_cart and parked_cart, 'specify both --moving-cart and --parked-cart for a two-cart scene')
    require(parked_cart is None or len(candidates) == 2, 'no parked sibling in this scene')
    classes = dict(re.findall(r'\bclass\s+(\w+)\s+@\s*"([^"]+)"', source))
    scope = [re.search(r'\b' + kind + r'\s+\w+\s+@\s*"([^"]+)"', source)[1]
             for kind in ('module', 'scene')]
    exported = graph.get('extras', {}).get('ontokin', {})
    entry = exported.get('source', {})
    program = exported.get('program', {})
    entry_record = program.get('sources', {}).get('entry', {})

    filename = accepted['entry']['filename']
    unit = dict(source_id='entry', filename=filename, source_revision=revision, package_id=None, version=None)
    manifest = dict(schema_version=accepted['schema_version'], entry_source_id='entry', units=[unit], assets=[])
    canonical = json.dumps(manifest, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()
    program_revision = 'sha256:' + hashlib.sha256(b'ontokin.bundle/0.2\0' + canonical).hexdigest()
    require(program.get('manifest') == manifest and program.get('revision') == program_revision,
            'GLB program manifest or revision differs from accepted bundle')

    def matches_source(record):
        return (record.get('source_id') == 'entry' and record.get('filename') == filename
                and record.get('source_revision') == revision)

    require(entry.get('entry_source_id') == program.get('entry_source_id') == 'entry'
            and entry.get('entry_revision') == revision and matches_source(entry_record),
            'GLB entry source identity or revision differs from accepted source')

    def select(selector, role):
        matches = [o for o in objects if selector in o[:2]]
        require(matches, f'{role} selector {selector!r} missing from accepted source')
        require(len(matches) == 1, f'ambiguous {role} selector {selector!r}')
        obj, = matches
        name, stable_id, cls, _ = obj
        require(obj in candidates, f'{role} selector {selector!r} selects an obstacle')
        require(name in names, f'{role} node {name!r} missing from delivered GLB')
        meta = nodes[names.index(name)].get('extras', {}).get('ontokin', {})
        mapping = meta.get('source_mapping', {})
        expected_id = scope + [stable_id]
        class_id = '/'.join(['entry', scope[0], 'definitions', classes[cls]])
        require(meta.get('kind') == 'object' and meta.get('path') == mapping.get('path') == name
                and meta.get('element_id') == mapping.get('element_id') == expected_id
                and meta.get('class_name') == mapping.get('class_id') == class_id
                and mapping.get('definition_id') == class_id.split('/')
                and matches_source(mapping.get('declaration', {})) and matches_source(mapping.get('definition', {}))
                and mapping == program.get('occurrences', {}).get(name)
                and meta.get('program_revision') == program.get('revision'),
                f'{role} node {name!r} does not match accepted source identity or revision')
        require(sum(n.get('extras', {}).get('ontokin', {}).get('element_id') == expected_id
                    for n in nodes) == 1, f'ambiguous delivered element ID {stable_id!r}')
        return obj

    moving = select(moving_cart or candidates[0][0], 'moving cart')
    parked = select(parked_cart, 'parked cart') if parked_cart else None
    if parked:
        require(moving != parked, 'moving cart and parked cart must select different objects')
        require(moving[2] == parked[2], 'parked cart must be a sibling of the moving cart class')
    require(re.search(r'\bforce\s+' + moving[0] + r'\b', source),
            f'selected moving cart {moving[0]!r} has no driving force')
    require(all(isinstance(name, str) and name for name in names), 'missing delivered GLB node name')
    return moving, parked


def parked_clearance(times, tracks, bounds, parked, other):
    # For rigid boxes with fixed orientation, six signed axis gaps are affine in time.
    # Their maximum is a lower bound on surface distance. Its minimum occurs at an
    # endpoint or where two of the six lines intersect.
    def gaps(i):
        offset = gate.subtract(tracks[parked, 'translation'][i], tracks[other, 'translation'][i])
        p_lo, p_hi = bounds[parked]
        o_lo, o_hi = bounds[other]
        return [gap for a, d in enumerate(offset)
                for gap in (d + p_lo[a] - o_hi[a], o_lo[a] - p_hi[a] - d)]

    minimum = (math.inf, None)
    left = gaps(0)
    for i, (start, end) in enumerate(zip(times, times[1:]), 1):
        right = gaps(i)
        slopes = [b - a for a, b in zip(left, right)]
        fractions = [0., 1.]
        for j, slope in enumerate(slopes):
            for k in range(j):
                if slope != slopes[k]:
                    u = (left[k] - left[j]) / (slope - slopes[k])
                    if 0 < u < 1:
                        fractions.append(u)
        for u in fractions:
            lower = max(x + u * slope for x, slope in zip(left, slopes))
            minimum = min(minimum, (lower, start + u * (end - start)))
        left = right
    lower, time = minimum
    require(lower > 0, f'parked cart {parked!r} lacks positive separation from {other!r} at {time:.9g} s')
    return dict(separation_lower_bound_m=lower, time_of_min_s=time)


def check_parked(source, obj, moving, times, tracks, bounds):
    name, stable_id, _, body = obj
    require(not re.search(r'\b(?:force|torque|impulse)\s+' + name + r'\b', source),
            f'selected parked cart {name!r} has an authored load')
    for field, unit in [('velocity', 'm/s'), ('omega', 'rad/s')]:
        vector = re.search(field + r'\s*=\s*vector\(world,\s*([^)]*)\)', body)
        require(vector and vector_components(vector[1], unit) == [0, 0, 0], 'parked cart must start at rest')
    pose = re.search(r'pose\(world,\s*vec3\(([^)]*)\),\s*quat\(([^)]*)\)\)', body)
    require(pose, 'expected an authored world pose for parked cart')
    position = list(map(float, vector_components(pose[1], 'm')))
    w, x, y, z = map(float, pose[2].split(','))
    rows = tracks[name, 'translation']
    require(math.dist(rows[0], position) <= 1e-6, 'parked cart translation differs from authored pose')
    require(all(row == rows[0] for row in rows), 'parked cart drifts from fixed position')
    require(gate.angle(tracks[name, 'rotation'][0], gate.unit((x, y, z, w))) <= 1e-6,
            'parked cart rotation differs from authored pose')
    return dict(identifier=name, element_id=stable_id, position_m=rows[0],
                separation={other: parked_clearance(times, tracks, bounds, name, other)
                            for other in (moving, 'gate', 'post')})


def main(source, bundle, glb, width=None, moving_cart=None, parked_cart=None):
    source_bytes = source.read_bytes()
    text = source_bytes.decode("utf-8")
    accepted = json.loads(bundle.read_bytes())
    require(accepted.get('schema_version') == 'ontokin.bundle/0.2'
            and accepted.get('modules') == [] and accepted.get('assets') == [],
            'expected a single-file accepted bundle with empty modules and assets')
    entry = accepted.get('entry', {})
    require(isinstance(entry.get('filename'), str) and text == entry.get('source'), "accepted source mismatch")
    digest = hashlib.sha256(source_bytes).hexdigest()
    src = example_source(text)
    raw = glb.read_bytes()
    graph, data = gate.read_glb(raw)
    moving, parked = select_carts(src, graph, 'sha256:' + digest, accepted, moving_cart, parked_cart)
    cart = moving[0]
    times, tracks, _ = gate.read_tracks(graph, data)
    require(set(tracks) == {(node['name'], path) for node in graph['nodes']
                            for path in ('rotation', 'translation')}, 'missing delivered pose tracks')
    original = gate.measure(raw, gate.source_dynamics(src), root_count=4 if parked else 3)
    physics = cart_source(src, moving[1])
    local_bounds = {}
    triangles = {}
    obstacle_hashes = {}
    for node in graph["nodes"]:
        name = node["name"]
        rotations = tracks[name, "rotation"]
        require(all(gate.align(rotations[0], q) == rotations[0] for q in rotations),
                f"{name!r} rotation drifts; expected rigid translation only")
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

    parked_result = check_parked(src, parked, cart, times, tracks, local_bounds) if parked else None
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
        moving_cart=dict(identifier=cart, element_id=moving[1]),
        parked_cart=parked_result,
        cart_mesh=mesh,
        cart_travel_z_m=rows[-1][2]-rows[0][2],
        surface_witnesses=witnesses,
        obstacle_mesh_sha256=obstacle_hashes,
        animation_tracks_sha256=hashlib.sha256(json.dumps(
            [times, [(k, tracks[k]) for k in sorted(tracks)]]).encode()).hexdigest(),
        source_sha256=digest,
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
    parser.add_argument('--moving-cart', help='passing cart source identifier or stable element ID')
    parser.add_argument('--parked-cart', help='parked sibling source identifier or stable element ID')
    try:
        result = main(**vars(parser.parse_args()))
    except ValueError as error:
        result = dict(result='REJECTED', diagnostics=[str(error)])
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["result"] == "PASS" else 1)
