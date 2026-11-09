"""Import a single FlowHMR SMPL-H motion NPZ without loading the body model."""

from pathlib import Path

import numpy as np

from .observation import read_arrays


# flowhmr/pipeline/v2m_inference.py::save_fbx and data/rendering_data/examples.
ADAPTER_REVISION = "87ebb483ce9da32be72c67971bc8fd76f27251f3"


def _floats(data, key, shape):
    value = data[key]
    if value.shape != shape or value.dtype.kind != "f" or value.dtype.itemsize > 8 or not np.isfinite(value).all():
        raise ValueError(f"{key} must be a finite floating array of shape {shape}")
    return value


def adapt(source: Path, *, fps: float | None = None) -> tuple[dict, dict[str, np.ndarray]]:
    data = read_arrays(source, ("poses", "trans", "betas"), optional=(
        "mocap_framerate", "num_frames", "gender", "Rh", "foot_contacts",
        "local_joints_positions", "smooth_root_pos", "pelvis_world",
    ))
    trans = data["trans"]
    if trans.ndim != 2 or len(trans) == 0:
        raise ValueError("trans must contain at least one 3D translation")
    count = len(trans)
    trans = _floats(data, "trans", (count, 3))
    pose_shape = (count, 156) if data["poses"].ndim == 2 else (count, 52, 3)
    rotations = _floats(data, "poses", pose_shape).reshape(count, 52, 3)
    shape = _floats(data, "betas", (1, 16))
    if "num_frames" in data:
        n = data["num_frames"]
        if n.shape != () or n.dtype.kind not in "iu" or n.item() != count:
            raise ValueError("num_frames must match the motion length")
    if "Rh" in data:
        root_rotation = _floats(data, "Rh", (count, 3))
        if not np.array_equal(root_rotation, rotations[:, 0]):
            raise ValueError("Rh disagrees with the SMPL-H root rotation")
    if "gender" in data:
        gender = data["gender"]
        if gender.shape != () or gender.dtype.kind != "U" or gender.item() != "neutral":
            raise ValueError("this adapter supports the neutral SMPL-H model")

    stored = data.get("mocap_framerate")
    if stored is not None:
        if stored.shape != () or stored.dtype.kind not in "fiu":
            raise ValueError("mocap_framerate must be a numeric scalar")
        if fps is not None and fps != stored.item():
            raise ValueError("fps conflicts with the stored mocap_framerate")
        fps = float(stored)
    if fps is None or not np.isfinite(fps) or fps <= 0:
        raise ValueError("a finite positive motion frame rate is required")
    with np.errstate(over="ignore"):
        times = np.arange(count, dtype=np.float64) / fps
    if not np.isfinite(times).all():
        raise ValueError("fps produces unrepresentable timestamps")

    payload = {
        "timestamps_s": times, "root_translation": trans,
        "joint_rotvec": rotations, "shape_coefficients": shape,
    }
    metadata = {
        "coordinate_system": "flowhmr_export_y_up",
        "units": "m",
        "sample_count": count,
        "capabilities": ["root_translation", "joint_rotations", "body_shape"],
        "fps": fps,
        "timing": ("stored mocap_framerate" if stored is not None else "caller supplied fps")
                  + ", seconds from first exported sample",
        "translation_convention": "model-estimated metres, clip-local right-handed Y-up export frame; "
                                  "SMPL-H translation parameter, distinct from pelvis position",
        "rotation_convention": "SMPL-H order, 52 rotation vectors in radians; global root then parent-relative joints",
        "shape_convention": "16 dimensionless SMPL-H shape coefficients",
    }
    if "gender" in data:
        metadata["body_model_gender"] = "neutral"
    if "foot_contacts" in data:
        payload["foot_contact_scores"] = _floats(data, "foot_contacts", (count, 4))
        metadata["capabilities"].append("foot_contact_scores")
        metadata["contact_convention"] = "model scores for left ankle, left toe, right ankle, right toe"
    # The writer rotates trans and the root pose before saving. It does not
    # rotate these network outputs or apply the optional floor correction to them.
    diagnostics = {
        "local_joints_positions": (count, 52, 3),
        "smooth_root_pos": (count, 3),
        "pelvis_world": (count, 3),
    }
    for key, dims in diagnostics.items():
        if key in data:
            payload["internal_" + key] = _floats(data, key, dims)
    if any(key in data for key in diagnostics):
        metadata["internal_frame"] = ("internal_ arrays retain the network frame before export yaw and floor adjustment. "
                                      "local_joints_positions has smoothed root X/Z removed.")
    return metadata, payload
