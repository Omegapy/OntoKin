"""Fit one measured root-translation segment to a reusable prescribed OntoKin action."""

from __future__ import annotations

import hashlib
import json
import math
import tempfile
from pathlib import Path

import numpy as np

from ontokin.diagnostics import OntoKinError
from ontokin.evaluator import MAX_SAMPLES, evaluate
from ontokin.gltf import export_glb
from ontokin.scene import ExportOptions
from ontokin.syntax import parse
from ontokin.validator import validate

from .observation import load_observation


def _source(origin, velocity, duration, pace):
    x, y, z = (repr(float(value)) for value in origin)
    vx, vy, vz = (repr(float(value)) for value in velocity)
    return f'''ontokin "0.1";
module ObservedRoot @ "observed-root";
profile "core-0.1";

// A marker for the observed model translation in its clip-local Y-up frame
class RootMarker @ "root-marker" {{
    public param vx @ "vx": Speed = {vx}[m/s];
    public param vy @ "vy": Speed = {vy}[m/s];
    public param vz @ "vz": Speed = {vz}[m/s];
    public param pace @ "pace": Real = 1.0;
    geometry = sphere(0.05[m]);
    motion = prescribed;
    public method advance @ "advance"(duration: Time) -> Action {{
        return move(self, vector(world, self.vx * self.pace, self.vy * self.pace, self.vz * self.pace), duration);
    }}
}}

scene Reproduction @ "reproduction" {{
    duration = {duration}[s];
    gravity = vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2]);
    object root @ "root": RootMarker {{
        placement = pose(world, vec3({x}[m], {y}[m], {z}[m]), quat(1, 0, 0, 0));
        pace = {pace};
    }}
    action travel @ "travel" = root.advance({duration}[s]);
    at 0[s] sequence {{ start travel; }}
}}
'''


def _replay(source, times):
    model = validate(parse(source), level="evaluated")
    # The evaluator reads binary64 time arguments the same way it reads source literals.
    samples = evaluate(model, times.tolist())["samples"]
    return model, np.array([sample["objects"]["root"]["position_m"] for sample in samples])


def _metrics(errors):
    return {"frames": len(errors), "position_rmse_m": float(np.sqrt(np.mean(errors**2))),
            "max_position_error_m": float(errors.max())}


def synthesize(observation_dir: Path, output_dir: Path, *, start_frame=0, stop_frame=None, max_error_m=0.025):
    """Accept a straight, constant-speed segment with a chronological holdout; write only on acceptance."""
    output_dir = Path(output_dir)
    if output_dir.exists() or output_dir.is_symlink():
        raise ValueError("Choose a new synthesis output directory")
    if isinstance(max_error_m, bool) or not math.isfinite(max_error_m) or max_error_m <= 0:
        raise ValueError("max_error_m must be positive and finite")
    manifest, arrays = load_observation(observation_dir)
    observation = manifest["observation"]
    if not (manifest["adapter"] == "flowhmr" and observation.get("units") == "m"
            and observation.get("coordinate_system") == "flowhmr_export_y_up"
            and "root_translation" in observation.get("capabilities", [])):
        raise ValueError("Root synthesis needs FlowHMR world-space model translation in estimated meters")
    if not {"root_translation", "timestamps_s"} <= arrays.keys():
        raise ValueError("Observation is missing root_translation or timestamps_s")
    positions = arrays["root_translation"]
    times = arrays["timestamps_s"]
    if (times.shape != (observation["sample_count"],) or positions.shape != (len(times), 3)
            or times.dtype.kind != "f" or positions.dtype.kind != "f"):
        raise ValueError("Expected one translation triple per timestamp")
    if stop_frame is None:
        stop_frame = len(times)
    if type(start_frame) is not int or type(stop_frame) is not int or not 0 <= start_frame < stop_frame <= len(times):
        raise ValueError("Select a valid half-open frame range")
    if not 6 <= stop_frame - start_frame <= MAX_SAMPLES:
        raise ValueError(f"Select 6 to {MAX_SAMPLES} consecutive frames")
    times = times[start_frame:stop_frame].astype(np.float64)
    positions = positions[start_frame:stop_frame].astype(np.float64)
    if not (np.isfinite(positions).all() and np.isfinite(times).all() and (np.diff(times) > 0).all()):
        raise ValueError("A fit needs finite translations and strictly increasing finite timestamps")
    time_origin = float(times[0])
    times -= time_origin
    duration = float(times[-1])
    count = len(times)
    if duration > 60:
        raise ValueError("Select a segment of at most 60 seconds")

    # Fit on the earlier frames only. The final quarter measures extrapolation error.
    split = count - max(2, (count + 3) // 4)
    relative = times / duration
    design = np.column_stack((np.ones(split), relative[:split]))
    coefficients, _, rank, _ = np.linalg.lstsq(design, positions[:split], rcond=None)
    if rank != 2 or not np.isfinite(coefficients).all():
        raise ValueError("The selected timestamps cannot constrain a linear trajectory")
    origin, displacement = coefficients
    if np.linalg.norm(displacement) <= max_error_m:
        raise ValueError("The fitted movement is smaller than or equal to the error tolerance")
    velocity = displacement / duration
    if not np.isfinite(velocity).all():
        raise ValueError("The fitted velocity exceeds the supported numeric range")
    source = _source(origin, velocity, duration, 1.0)
    faster = _source(origin, velocity, duration, 1.2)
    try:
        model, replay = _replay(source, times)
        errors = np.linalg.norm(replay - positions, axis=1)
        if not np.isfinite(errors).all() or errors.max() > max_error_m:
            raise ValueError(f"Constant velocity exceeds {max_error_m:g} m: training maximum "
                             f"{errors[:split].max():.6g} m, held-out maximum {errors[split:].max():.6g} m")
        _, changed = _replay(faster, times)
        expected = origin + 1.2 * (replay - origin)
        counter_error = float(np.linalg.norm(changed - expected, axis=1).max())
        if not math.isfinite(counter_error) or counter_error > 1e-8 or np.array_equal(changed[-1], replay[-1]):
            raise ValueError("Changing pace did not produce the expected 1.2x displacement")
        digest = hashlib.sha256(source.encode()).hexdigest()
        glb = export_glb(model, options=ExportOptions(fps=12, helpers=False),
                         source_uri="root-motion.ok", source_sha256="sha256:" + digest).data
    except OntoKinError as exc:
        raise ValueError(f"OntoKin rejected the generated trajectory ({exc.code}): {exc}") from exc

    result = {
        "schema": "ontokin.root_translation_fit/1", "outcome": "accepted", "model": "prescribed_constant_velocity",
        "subject": "FlowHMR model translation marker", "coordinate_system": observation["coordinate_system"],
        "source_sha256": manifest["source"]["sha256"], "arrays_sha256": manifest["arrays_sha256"],
        "frames": {"start": start_frame, "holdout_start": start_frame + split, "stop_exclusive": stop_frame},
        "time_origin_s": time_origin, "duration_s": duration, "initial_position_m": origin.tolist(),
        "velocity_m_per_s": velocity.tolist(), "max_error_limit_m": max_error_m,
        "training": _metrics(errors[:split]), "held_out": _metrics(errors[split:]),
        "counterfactual": {"pace": 1.2, "max_displacement_error_m": counter_error,
                           "endpoint_m": changed[-1].tolist()},
        "root_motion_ok_sha256": digest, "root_motion_glb_sha256": hashlib.sha256(glb).hexdigest(),
        "faster_ok_sha256": hashlib.sha256(faster.encode()).hexdigest(),
    }
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output_dir.parent) as temp:
        stage = Path(temp) / "synthesis"
        stage.mkdir()
        (stage / "root-motion.ok").write_text(source, encoding="utf-8")
        (stage / "faster.ok").write_text(faster, encoding="utf-8")
        (stage / "root-motion.glb").write_bytes(glb)
        (stage / "fit.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        if output_dir.exists() or output_dir.is_symlink():
            raise ValueError("Output directory appeared during synthesis")
        stage.rename(output_dir)
    return result
