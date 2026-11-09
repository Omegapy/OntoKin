"""Import one calibrated object's position samples in a gravity-aligned world frame."""

from pathlib import Path

import numpy as np

from .observation import read_arrays


ADAPTER_REVISION = "ontokin.metric_track/1"
FRAME = "right_handed_y_up"


def adapt(source: Path, *, fps: float | None = None) -> tuple[dict, dict[str, np.ndarray]]:
    if fps is not None:
        raise ValueError("A calibrated track uses its explicit timestamps_s")
    data = read_arrays(source, ("timestamps_s", "position_m", "coordinate_system"))
    declaration = data["coordinate_system"]
    if declaration.shape != () or declaration.dtype.kind != "U" or declaration.item() != FRAME:
        raise ValueError(f"coordinate_system must explicitly declare {FRAME!r}")
    t, pos = data["timestamps_s"], data["position_m"]
    if (t.ndim != 1 or len(t) == 0 or pos.shape != (len(t), 3) or t.dtype.kind != "f"
            or pos.dtype.kind != "f" or max(t.dtype.itemsize, pos.dtype.itemsize) > 8
            or not np.isfinite(pos).all() or not np.isfinite(t).all()
            or np.any(t[1:] <= t[:-1])):
        raise ValueError("Need finite floating timestamps_s in increasing order and matching position_m triples")
    return {"coordinate_system": FRAME, "units": "m", "sample_count": len(t),
            "capabilities": ["point_trajectory"],
            "scale": "absolute metres asserted by the track producer",
            "timing": "per-sample seconds from the producer's time origin"}, {
                "timestamps_s": t, "position_m": pos,
            }
