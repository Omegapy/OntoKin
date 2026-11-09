"""Fit a parent-relative FlowHMR knee orientation with an editable core-0.1 hinge."""
import hashlib
import json
import math
from pathlib import Path
import tempfile

import numpy as np

from ontokin.diagnostics import OntoKinError
from ontokin.evaluator import MAX_SAMPLES, evaluate
from ontokin.gltf import export_glb
from ontokin.scene import ExportOptions
from ontokin.syntax import parse
from ontokin.validator import validate

from .observation import digest, load_observation


JOINTS = {"left_knee": 4, "right_knee": 5}


def _quaternions(vectors):
    """Rotation vectors to unit quaternions in scalar-first order."""
    angles = np.linalg.norm(vectors, axis=1)
    if not np.isfinite(angles).all():
        raise ValueError("Joint rotation exceeds the supported numeric range")
    return np.column_stack((np.cos(angles / 2), vectors * (0.5 * np.sinc(angles / (2 * np.pi)))[:, None]))


def _error_deg(predicted, observed):
    dots = np.abs(np.sum(predicted * observed, axis=1))
    return np.degrees(2 * np.arccos(np.clip(dots, 0, 1)))


def _fit(times, q, limit, max_phases):
    # On a fixed hinge, quaternions lie in a plane through the 4D origin.
    # Only fitting frames participate in choosing the plane and phase knots.
    _, singular, plane = np.linalg.svd(q, full_matrices=False)
    if singular[1] < 1e-8:
        raise ValueError("A stationary knee does not identify a hinge axis")
    a = (q[0] @ plane[:2].T) @ plane[:2]
    if np.linalg.norm(a) < 1e-8:
        raise ValueError("Initial knee orientation cannot define a reference pose")
    a /= np.linalg.norm(a)
    c = a @ plane[:2].T
    b = np.array([-c[1], c[0]]) @ plane[:2]
    # b * inverse(a) is a pure quaternion whose vector is the parent-frame axis.
    axis = a[0] * b[1:] - b[0] * a[1:] - np.cross(b[1:], a[1:])
    if axis[np.abs(axis).argmax()] < 0:
        b, axis = -b, -axis
    angles = np.unwrap(2 * np.arctan2(q @ b, q @ a))
    angles -= angles[0]
    if np.rad2deg(np.ptp(angles)) <= limit:
        raise ValueError("Knee excursion is smaller than the angular tolerance")
    keys = [0, len(times) - 1]
    for count in range(1, max_phases + 1):
        phase_angle = np.interp(times, times[keys], angles[keys])[:, None] / 2
        errors = _error_deg(np.cos(phase_angle) * a + np.sin(phase_angle) * b, q)
        if errors.max() <= limit:
            return a, b, axis, angles, keys
        worst = int(np.argmax(errors))
        if worst in keys or count == max_phases:
            break
        keys = sorted([*keys, worst])
    raise ValueError("A single hinge does not fit training rotations within the phase and angular limits")


def _phase_times(times):
    # Binary-fraction event times and durations have identical boundaries in
    # the evaluator and GLB exporter. The final event covers the last sample.
    ticks = 2**20
    points = np.rint(times * ticks) / ticks
    points[-1] = math.ceil(times[-1] * ticks) / ticks
    if np.any(np.diff(points) <= 0):
        raise ValueError("Hinge phase durations are too short for the timing grid")
    return points


def _source(points, angles, axis, reference, amplitude):
    axis_text = ", ".join(repr(float(v)) for v in axis)
    inverse = reference * [1, -1, -1, -1]
    orientation = ", ".join(repr(float(v)) for v in inverse)
    declarations, schedule = [], []
    for i in range(len(points) - 1):
        duration = float(points[i+1] - points[i])
        declarations.append(f'    action p{i} @ "phase-{i}" = rig.bend({float(angles[i+1])!r}[rad], {duration!r}[s]);')
        schedule.append(f'    at {float(points[i])!r}[s] sequence {{ start p{i}; }}')
    extent = float(np.max(np.abs(angles))) + 0.1
    return f'''ontokin "0.1";
module KneeOrientation @ "knee-orientation";
profile "core-0.1";

// The bar shows orientation only. Its dimensions are display settings
class Pointer @ "pointer" {{
    geometry = box(vec3(0.3[m], 0.04[m], 0.06[m]));
    public site mount @ "mount" {{
        pose = pose(self.frame, vec3(0[m], 0[m], 0[m]), quat({orientation}));
        interface = "rigid.origin";
        size = 0[m];
    }}
}}

class KneeRig @ "knee-rig" {{
    public param amplitude @ "amplitude": Real = 1.0;
    geometry = sphere(0.025[m]);
    public part pointer @ "pointer": Pointer {{}}
    public joint flex @ "flex": hinge {{
        parent = self.origin;
        child = self.pointer.mount;
        axis = vec3({axis_text});
        limits = range(-{extent!r}[rad], {extent!r}[rad]);
        initial = 0[rad];
    }}
    public method bend @ "bend"(angle: Angle, duration: Time) -> Action {{
        return tween(self.flex, self.amplitude * angle, duration);
    }}
}}

scene Example @ "example" {{
    duration = {float(points[-1])!r}[s];
    gravity = vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2]);
    object rig @ "rig": KneeRig {{ amplitude = {amplitude}; }}
''' + "\n".join(declarations + schedule) + "\n}\n"


def _evaluate(source, times):
    model = validate(parse(source), level="evaluated")
    records = evaluate(model, times.tolist())["samples"]
    return model, np.array([r["objects"]["rig.pointer"]["orientation_wxyz"] for r in records])


def _metrics(errors):
    return {"frames": len(errors), "rmse_deg": float(np.sqrt(np.mean(errors**2))),
            "max_error_deg": float(errors.max())}


def articulate(observation_dir, output_dir, *, joint="left_knee", max_error_deg=10.0, max_phases=16):
    """Fit and execute a hinge hypothesis, accepting only after independent held-out checks."""
    if joint not in JOINTS or type(max_phases) is not int or not 1 <= max_phases <= 32:
        raise ValueError("Choose a supported knee and a phase limit from 1 to 32")
    if isinstance(max_error_deg, bool) or not math.isfinite(max_error_deg) or not 0 < max_error_deg < 90:
        raise ValueError("Angular tolerance must be positive and below 90 degrees")
    output_dir = Path(output_dir)
    if output_dir.exists() or output_dir.is_symlink():
        raise ValueError("Choose a new articulation output directory")
    manifest, data = load_observation(Path(observation_dir))
    meta = manifest["observation"]
    if (manifest["adapter"] != "flowhmr" or meta.get("coordinate_system") != "flowhmr_export_y_up"
            or "joint_rotations" not in meta["capabilities"] or not {"joint_rotvec", "timestamps_s"} <= data.keys()):
        raise ValueError("Articulation requires parent-relative FlowHMR SMPL-H rotations")
    count = meta["sample_count"]
    times, rotations = data["timestamps_s"], data["joint_rotvec"]
    if (not 8 <= count <= MAX_SAMPLES or times.shape != (count,) or rotations.shape != (count, 52, 3)
            or times.dtype.kind != "f" or rotations.dtype.kind != "f" or not np.isfinite(times).all()
            or np.any(times[1:] <= times[:-1])):
        raise ValueError(f"Expected 8 to {MAX_SAMPLES} strictly time-ordered joint observations")
    times = times.astype(float) - float(times[0])
    if not 0 < times[-1] <= 60:
        raise ValueError("Select a clip of at most 60 seconds")
    q = _quaternions(rotations[:, JOINTS[joint]].astype(float))
    held = np.zeros(count, dtype=bool)
    held[3:-1:4] = True
    a, b, axis, angles, knots = _fit(times[~held], q[~held], max_error_deg, max_phases)
    frames = np.flatnonzero(~held)[knots]
    knot_times, knot_angles = _phase_times(times[frames]), angles[knots]
    source = _source(knot_times, knot_angles, axis, a, 1.0)
    variant = _source(knot_times, knot_angles, axis, a, 0.8)
    try:
        model, replay = _evaluate(source, times)
        errors = _error_deg(replay, q)
        if not np.isfinite(errors).all() or errors.max() > max_error_deg:
            raise ValueError(f"Hinge replay exceeds {max_error_deg:g} degrees: training maximum "
                             f"{errors[~held].max():.6g}, held-out maximum {errors[held].max():.6g}")
        half_angles = 0.4 * np.interp(times, knot_times, knot_angles)[:, None]
        _, reduced = _evaluate(variant, times)
        changed = _error_deg(reduced, np.cos(half_angles) * a + np.sin(half_angles) * b)
        if not np.isfinite(changed).all() or changed.max() > 0.001:
            raise ValueError("Native amplitude change failed its rotation check")
        exported = export_glb(model, options=ExportOptions(fps=12, helpers=False),
                              source_uri="knee.ok", source_sha256="sha256:" + hashlib.sha256(source.encode()).hexdigest())
    except OntoKinError as exc:
        raise ValueError(f"OntoKin rejected the fitted hinge ({exc.code}): {exc}") from exc
    result = {"schema": "ontokin.knee_hinge_fit/1", "outcome": "accepted", "joint": joint,
              "smplh_index": JOINTS[joint], "subject": "parent-relative knee orientation marker",
              "source_sha256": manifest["source"]["sha256"], "arrays_sha256": manifest["arrays_sha256"],
              "parent_axis_xyz": axis.tolist(), "reference_wxyz": a.tolist(),
              "phases": len(knots)-1, "knot_frames": frames.tolist(), "knot_angles_rad": knot_angles.tolist(),
              "excursion_deg": float(np.degrees(np.ptp(knot_angles))), "max_error_limit_deg": max_error_deg,
              "held_out_frames": np.flatnonzero(held).tolist(), "training": _metrics(errors[~held]),
              "held_out": _metrics(errors[held]), "counterfactual": {"amplitude": 0.8,
                  "max_error_deg": float(changed.max())}}
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output_dir.parent) as temp:
        stage = Path(temp) / "action"
        stage.mkdir()
        (stage / "knee.ok").write_text(source, encoding="utf-8")
        (stage / "reduced.ok").write_text(variant, encoding="utf-8")
        (stage / "knee.glb").write_bytes(exported.data)
        (stage / "export.json").write_text(json.dumps(exported.report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        result["output_sha256"] = {p.name: digest(p) for p in sorted(stage.iterdir())}
        (stage / "fit.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        if output_dir.exists() or output_dir.is_symlink():
            raise ValueError("Output directory appeared during fitting")
        stage.rename(output_dir)
    return result
