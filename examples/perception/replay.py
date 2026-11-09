"""Replay the observation prototypes without a model installation."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.perception.articulation import articulate
from tools.perception.ballistic import fit_ballistic
from tools.perception.geometry import inspect_point
from tools.perception.observation import digest, import_observation
from tools.perception.synthesis import synthesize


def replay(output):
    output.mkdir(parents=True, exist_ok=False)
    data = Path(__file__).resolve().parent / "data"
    motion = data / "flowhmr_demo.npz"
    solve = data / "solve-synthetic.npz"
    if (digest(motion) != "f70e90e2acc5b938a5dab9d3bbafa0f2098a7f9cf1d44d26172f1cc316954e39"
            or digest(solve) != "e9aeaa642b077aace18aeb880a78f12177df6e5d53015232189d434c158b0aac"):
        raise ValueError("Reference inputs have changed")
    human = output / "human"
    meta = import_observation("flowhmr", motion, human, source_kind="published", capture="flowhmr_demo")
    root = synthesize(human, output / "root-action", start_frame=30, stop_frame=60)
    try:
        synthesize(human, output / "whole-clip")
    except ValueError as error:
        if "held-out maximum" not in str(error) or (output / "whole-clip").exists():
            raise
        refusal = str(error)
    else:
        raise ValueError("Full-clip negative control was incorrectly accepted")
    knee = articulate(human, output / "left-knee")
    world = output / "world"
    import_observation("solv3r", solve, world, source_kind="synthetic")
    point = inspect_point(world, 0, 1, 1, target_view=1)
    if point["world_xyz"] != [0, 0, -0.875] or point["projection"]["status"] != "behind_camera":
        raise ValueError("Unexpected point or visibility for known cameras")
    time_s = np.linspace(0., 1.8, 20)
    position_m = [2., 8., -4.] + time_s[:, None] * [0.7, 3.2, -0.25]
    position_m[:, 1] -= 4.1 * time_s**2
    track = output / "calibrated.npz"
    np.savez(track, timestamps_s=time_s, position_m=position_m, coordinate_system="right_handed_y_up")
    import_observation("metric-track", track, output / "object", source_kind="synthetic", capture="known-free-flight")
    flight = fit_ballistic(output / "object", output / "flight")
    if not np.isclose(flight["gravity_y_m_per_s2"], -8.2, rtol=0, atol=1e-10):
        raise ValueError("Reference downward acceleration was not recovered")
    report = {"result": "passed", "capture_frames": meta["observation"]["sample_count"],
              "root_fit": root, "full_root_refusal": refusal, "knee_fit": knee,
              "synthetic_scene_point": point, "synthetic_free_flight": flight}
    (output / "replay.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(f"Passed. Open {output / 'replay.json'} for the measurements.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="new output directory")
    replay(parser.parse_args().output)
