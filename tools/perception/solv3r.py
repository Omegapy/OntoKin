"""Import an offline or streaming Solv3R export into an observation sequence."""

from pathlib import Path

import numpy as np

from .observation import read_arrays


# Pinned writers: solv3r/export.py::save_solve and examples/streaming.py.
ADAPTER_REVISION = "ef8da34f3736d6c241b3ba3cd074073c06e90b8f"


FRAME = "right-handed first-view reference, +X right, +Y up, -Z forward"
UNITS = "model_units"


def validate_cameras(raw, count, field):
    if raw.dtype.kind != "f" or raw.dtype.itemsize > 8 or raw.shape != (count, 4, 4) or not np.isfinite(raw).all():
        raise ValueError(f"{field} must contain one finite 4x4 camera-to-world matrix per view")
    if not np.all(raw[:, 3, :] == (0, 0, 0, 1)):
        raise ValueError(f"{field} must contain affine homogeneous transforms")
    rotation = raw[:, :3, :3].astype(np.float64)
    if (np.any(np.abs(rotation) > 1.0001)
            or not np.allclose(rotation.transpose(0, 2, 1) @ rotation, np.eye(3), rtol=0, atol=1e-4)
            or not np.allclose(np.linalg.det(rotation), 1, rtol=0, atol=1e-4)):
        raise ValueError(f"{field} must contain proper rotations")



def _camera_to_world(raw, count, field):
    validate_cameras(raw, count, field)
    # Flip both the camera and first-view world bases, preserving handedness.
    signs = np.array([1, -1, -1, 1], dtype=raw.dtype)
    return raw * signs[:, None] * signs[None, :]


def validate_intrinsics(intrinsic, count):
    if (intrinsic.shape != (count, 3, 3) or intrinsic.dtype.kind != "f"
            or intrinsic.dtype.itemsize > 8 or not np.isfinite(intrinsic).all()):
        raise ValueError("K must contain one finite 3x3 intrinsic matrix per view")
    if (np.any(intrinsic[:, (0, 1), (0, 1)] <= 0)
            or not np.all(intrinsic[:, 2] == (0, 0, 1))
            or np.any(intrinsic[:, (0, 1), (1, 0)] != 0)):
        raise ValueError("K must use positive focal lengths and zero skew in pixels")


def adapt(source: Path, *, fps: float | None = None) -> tuple[dict, dict[str, np.ndarray]]:
    data = read_arrays(source, ("c2w", "K", "depth", "depth_conf"), optional=("c2w_exit", "names"))
    depth, confidence = data["depth"], data["depth_conf"]
    if depth.ndim != 3 or min(depth.shape) < 1 or depth.dtype.kind != "f" or depth.dtype.itemsize > 8:
        raise ValueError("depth must be a nonempty floating [views,height,width] array")
    count, height, width = depth.shape
    if confidence.shape != depth.shape or confidence.dtype.kind != "f" or confidence.dtype.itemsize > 8:
        raise ValueError("depth_conf must be a floating array matching depth")
    intrinsic = data["K"]
    validate_intrinsics(intrinsic, count)

    # Upstream casts dense predictions to float16, which can overflow.
    valid = np.isfinite(depth) & (depth > 0) & np.isfinite(confidence) & (confidence >= 0)
    if not np.any(valid):
        raise ValueError("export has no usable depth-confidence pairs")
    all_valid = valid.all()
    payload = {
        "camera_to_world": _camera_to_world(data["c2w"], count, "c2w"),
        "intrinsics_px": intrinsic,
        "depth": depth if all_valid else np.where(valid, depth, 0),
        "depth_confidence": confidence if all_valid else np.where(valid, confidence, 0),
        "depth_valid": valid,
    }
    stream = "c2w_exit" in data
    if stream:
        payload["camera_to_world_exit"] = _camera_to_world(data["c2w_exit"], count, "c2w_exit")
    metadata = {
        "coordinate_system": FRAME,
        "units": UNITS,
        "sample_count": count,
        "capabilities": ["camera_poses", "intrinsics", "depth", "depth_confidence"],
        "scale": "uncalibrated; depth and camera translations share the same scale",
        "resolution_hw": [height, width],
        "camera_convention": "camera_to_world maps camera column vectors into the first-view reference",
        "pixel_convention": "origin top-left; +u right, +v down; intrinsics in model-resolution pixels",
        "depth_convention": "positive optical-axis depth along camera -Z; use depth_valid",
        "confidence_convention": "model scores; higher is better; invalid pairs have zero depth and score",
        "pose_stage": "arrival (exit poses stored separately)" if stream else "solve",
        "timing": "view order only",
    }
    if "names" in data:
        names = data["names"]
        if names.shape != (count,) or names.dtype.kind != "U" or not all(names.tolist()):
            raise ValueError("names must contain one nonempty Unicode view name per view")
        metadata["view_names"] = names.tolist()
    if fps is not None:
        if not np.isfinite(fps) or fps <= 0:
            raise ValueError("fps must be positive and finite")
        with np.errstate(over="ignore"):
            times = np.arange(count, dtype=np.float64) / fps
        if not np.isfinite(times).all():
            raise ValueError("fps produces unrepresentable timestamps")
        payload["timestamps_s"] = times
        metadata.update(fps=fps, timing="caller asserts uniformly sampled chronological view order")
    return metadata, payload
