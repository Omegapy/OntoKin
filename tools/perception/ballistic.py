"""Identify one constant downward acceleration from a calibrated free-flight point track."""

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

from .metric_track import FRAME
from .observation import digest, load_observation


def _source(origin, velocity, acceleration, duration):
    pos = ", ".join(f"{float(v)!r}[m]" for v in origin)
    speed = ", ".join(f"{float(v)!r}[m/s]" for v in velocity)
    return f'''ontokin "0.1";
module ObservedFlight @ "observed-flight";
profile "core-0.1";

// The marker's radius and mass are author defaults for visualizing one tracked point
class FlightMarker @ "flight-marker" {{
    public param radius @ "radius": Length = 0.05[m];
    public param mass @ "mass": Mass = 1[kg];
    geometry = sphere(self.radius);
    physical = sphere_body(self.radius, self.mass);
    motion = dynamic;
    collision = disabled;
}}

scene Flight @ "flight" {{
    duration = {duration!r}[s];
    gravity = vector(world, 0[m/s^2], {acceleration!r}[m/s^2], 0[m/s^2]);
    object marker @ "marker": FlightMarker {{
        placement = pose(world, vec3({pos}), quat(1, 0, 0, 0));
        velocity = vector(world, {speed});
    }}
}}
'''


def _replay(source, times):
    model = validate(parse(source), level="evaluated")
    states = evaluate(model, times.tolist())["samples"]
    return model, np.array([s["objects"]["marker"]["position_m"] for s in states])


def _metrics(errors):
    return {"position_rmse_m": float(np.sqrt(np.mean(errors**2))),
            "max_position_error_m": float(errors.max()), "frames": len(errors)}


def fit_ballistic(observation_dir: Path, output_dir: Path, *, max_error_m=0.01) -> dict:
    """Fit on the first three quarters and replay all samples under a gravity-only hypothesis."""
    if isinstance(max_error_m, bool) or not math.isfinite(max_error_m) or max_error_m <= 0:
        raise ValueError("max_error_m must be positive and finite")
    output_dir = Path(output_dir)
    if output_dir.exists() or output_dir.is_symlink():
        raise ValueError("Choose a new ballistic output directory")
    manifest, arrays = load_observation(Path(observation_dir))
    metadata = manifest["observation"]
    if (manifest["adapter"] != "metric-track" or metadata["coordinate_system"] != FRAME or metadata["units"] != "m"
            or "point_trajectory" not in metadata["capabilities"]):
        raise ValueError("Need a calibrated metric-track observation in the declared right-handed Y-up frame")
    if not {"timestamps_s", "position_m"} <= arrays.keys():
        raise ValueError("Observation is missing timestamps_s or position_m")
    if (arrays["timestamps_s"].dtype.kind != "f" or arrays["position_m"].dtype.kind != "f"
            or arrays["timestamps_s"].shape != (metadata["sample_count"],)):
        raise ValueError("Track arrays disagree with the observation contract")
    t = arrays["timestamps_s"].astype(np.float64)
    pos = arrays["position_m"].astype(np.float64)
    if (t.ndim != 1 or not 8 <= len(t) <= MAX_SAMPLES or pos.shape != (len(t), 3)
            or not np.isfinite(pos).all() or not np.isfinite(t).all() or not np.all(t[1:] > t[:-1])):
        raise ValueError(f"Need 8 to {MAX_SAMPLES} time-ordered finite 3D measurements")
    time_origin = float(t[0])
    t -= time_origin
    duration = float(t[-1])
    if not 0 < duration <= 60:
        raise ValueError("Select a free-flight segment up to 60 seconds")
    split = len(t) - max(2, (len(t) + 3) // 4)
    # Center spatial data and scale the training interval to condition the fit.
    elapsed = float(t[split - 1])
    u = t[:split] / elapsed
    linear = np.column_stack((np.ones(split), u))
    quadratic = np.column_stack((linear, u**2))
    relative = pos[:split] - pos[0]
    straight = np.linalg.lstsq(linear, relative, rcond=None)[0]
    yfit, _, rank, singular = np.linalg.lstsq(quadratic, relative[:, 1], rcond=None)
    if rank < 3 or singular[-1] < singular[0] * 1e-8:
        raise ValueError("Training timestamps do not constrain vertical curvature")
    linear_y_rmse = float(np.sqrt(np.mean((linear @ straight[:, 1] - relative[:, 1])**2)))
    if linear_y_rmse <= max_error_m:
        raise ValueError("Constant velocity already explains training height within the measurement tolerance")
    origin = pos[0] + straight[0]
    origin[1] = pos[0, 1] + yfit[0]
    velocity = straight[1] / elapsed
    velocity[1] = yfit[1] / elapsed
    g = float(2 * yfit[2] / elapsed / elapsed)
    if not np.isfinite(origin).all() or not np.isfinite(velocity).all() or not math.isfinite(g) or g >= 0:
        raise ValueError("Fit must identify finite downward acceleration in the declared Y-up frame")
    source = _source(origin, velocity, g, duration)
    variant = _source(origin, velocity, g / 2, duration)
    try:
        model, replay = _replay(source, t)
        error = np.linalg.norm(replay - pos, axis=1)
        if not np.isfinite(error).all() or error.max() > max_error_m:
            raise ValueError(f"Gravity-only replay exceeds {max_error_m:g} m: training maximum "
                             f"{error[:split].max():.6g} m, held-out maximum {error[split:].max():.6g} m")
        _, changed = _replay(variant, t)
        delta = changed - replay
        delta[:, 1] += 0.25 * g * t**2
        check = float(np.linalg.norm(delta, axis=1).max())
        if not math.isfinite(check) or check > 1e-8 or changed[-1, 1] <= replay[-1, 1]:
            raise ValueError("Half-gravity experiment did not produce the predicted change")
        sha = hashlib.sha256(source.encode()).hexdigest()
        glb = export_glb(model, options=ExportOptions(helpers=False, position_tolerance_m=min(0.001, max_error_m)),
                         source_uri="ballistic.ok", source_sha256="sha256:" + sha).data
    except OntoKinError as exc:
        raise ValueError(f"OntoKin rejected the fitted scene ({exc.code}): {exc}") from exc

    result = {"schema": "ontokin.ballistic_fit/1", "outcome": "accepted",
              "hypothesis": "gravity-only free flight in a stationary calibrated Y-up frame",
              "source_sha256": manifest["source"]["sha256"], "arrays_sha256": manifest["arrays_sha256"],
              "gravity_y_m_per_s2": g, "initial_velocity_m_per_s": velocity.tolist(),
              "initial_position_m": origin.tolist(), "time_origin_s": time_origin, "duration_s": duration,
              "mass": "unidentified; visualization marker uses 1 kg",
              "max_error_limit_m": max_error_m, "training_linear_height_rmse_m": linear_y_rmse,
              "holdout_start_frame": split, "training": _metrics(error[:split]), "held_out": _metrics(error[split:]),
              "counterfactual": {"gravity_multiplier": 0.5, "max_position_change_error_m": check}}
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output_dir.parent) as temp:
        stage = Path(temp) / "result"
        stage.mkdir()
        (stage / "ballistic.ok").write_text(source, encoding="utf-8")
        (stage / "half-gravity.ok").write_text(variant, encoding="utf-8")
        (stage / "ballistic.glb").write_bytes(glb)
        result["output_sha256"] = {p.name: digest(p) for p in sorted(stage.iterdir())}
        (stage / "fit.json").write_text(json.dumps(result, allow_nan=False, indent=2) + "\n", encoding="utf-8")
        if output_dir.exists() or output_dir.is_symlink():
            raise ValueError("Output directory appeared during fit")
        stage.rename(output_dir)
    return result
