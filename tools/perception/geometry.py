"""Unproject a Solv3R pixel and optionally check its projection in another view."""
from pathlib import Path

import numpy as np

from .observation import load_observation
from .solv3r import FRAME, UNITS, validate_cameras, validate_intrinsics


def inspect_point(observation: Path, view: int, u: int, v: int, *, target_view=None):
    manifest, data = load_observation(observation)
    meta = manifest["observation"]
    if (manifest["adapter"] != "solv3r" or meta.get("coordinate_system") != FRAME
            or meta.get("units") != UNITS):
        raise ValueError("Point inspection requires Solv3R first-view geometry at model scale")
    fields = {"camera_to_world", "intrinsics_px", "depth", "depth_valid", "depth_confidence"}
    if not fields <= data.keys():
        raise ValueError("Solv3R observation is missing camera or depth arrays")
    depths, scores, valid = data["depth"], data["depth_confidence"], data["depth_valid"]
    if (depths.ndim != 3 or min(depths.shape) < 1 or depths.dtype.kind != "f" or depths.dtype.itemsize > 8
            or valid.shape != depths.shape or valid.dtype.kind != "b"
            or scores.shape != depths.shape or scores.dtype.kind != "f" or scores.dtype.itemsize > 8):
        raise ValueError("Invalid Solv3R depth, confidence or validity arrays")
    count, height, width = depths.shape
    if meta.get("sample_count") != count or meta.get("resolution_hw") != [height, width]:
        raise ValueError("Solv3R view count or resolution does not match the recorded dimensions")
    cameras, intrinsics = data["camera_to_world"], data["intrinsics_px"]
    if cameras.shape != (count, 4, 4) or intrinsics.shape != (count, 3, 3):
        raise ValueError("Expected one camera pose and one intrinsic matrix per view")
    if not all(type(i) is int for i in (view, u, v)) or not (0 <= view < count and 0 <= u < width and 0 <= v < height):
        raise ValueError("Source view or pixel outside the observed array")
    selected = [view]
    if target_view is not None:
        if type(target_view) is not int or not 0 <= target_view < count:
            raise ValueError("Target view outside the observed array")
        selected.append(target_view)
    validate_cameras(cameras[selected], len(selected), "camera_to_world")
    validate_intrinsics(intrinsics[selected], len(selected))
    if not valid[view, v, u]:
        raise ValueError("Source pixel has no usable depth")
    depth, score = float(depths[view, v, u]), float(scores[view, v, u])
    if not (np.isfinite(depth) and depth > 0 and np.isfinite(score) and score >= 0):
        raise ValueError("Source pixel marked valid contains invalid depth or confidence")
    k = intrinsics[view].astype(float)
    source_pose = cameras[view].astype(float)
    with np.errstate(over="ignore", invalid="ignore"):
        camera = [(u - k[0, 2]) * depth / k[0, 0],
                  -(v - k[1, 2]) * depth / k[1, 1], -depth]
        world = source_pose[:3, :3] @ camera + source_pose[:3, 3]
    if not np.isfinite(world).all():
        raise ValueError("Unprojected point exceeds the supported numeric range")
    result = {"view": view, "pixel_uv": [u, v], "world_xyz": world.tolist(),
              "units": UNITS, "optical_depth": depth, "depth_score": score}
    if target_view is None:
        return result
    target_pose = cameras[target_view].astype(float)
    with np.errstate(over="ignore", invalid="ignore"):
        pos = target_pose[:3, :3].T @ (world - target_pose[:3, 3])
    if not np.isfinite(pos).all():
        raise ValueError("Target camera coordinates exceed the supported numeric range")
    z = -pos[2]
    target = {"view": target_view}
    result["projection"] = target
    if z <= 0:
        target["status"] = "behind_camera"
        return result
    k = intrinsics[target_view].astype(float)
    with np.errstate(over="ignore", invalid="ignore"):
        px = float(k[0, 0] * pos[0] / z + k[0, 2])
        py = float(-k[1, 1] * pos[1] / z + k[1, 2])
    if not (np.isfinite(px) and np.isfinite(py)):
        raise ValueError("Target pixel exceeds the supported numeric range")
    target.update(pixel_uv=[px, py], predicted_optical_depth=float(z))
    x, y = int(np.floor(px + 0.5)), int(np.floor(py + 0.5))
    if not (0 <= x < width and 0 <= y < height):
        target["status"] = "outside_image"
    elif not valid[target_view, y, x]:
        target["status"] = "missing_target_depth"
    else:
        measured = float(depths[target_view, y, x])
        if not np.isfinite(measured) or measured <= 0:
            raise ValueError("Target pixel marked valid contains invalid depth")
        target.update(status="compared", nearest_pixel_uv=[x, y], observed_optical_depth=measured,
                      observed_minus_predicted_depth=float(measured - z))
    return result
