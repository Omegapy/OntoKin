"""CPU inference entry point launched inside the verified external Solv3R checkout."""
import argparse
import json
import os
from pathlib import Path
import platform
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--images", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--checkpoint", required=True)
    args = parser.parse_args()

    # The launcher sets cwd to the verified upstream repository and supplies
    # its separate interpreter. Model dependencies stay inside this process.
    sys.path.insert(0, str(Path.cwd()))
    import numpy as np
    import torch
    from solv3r import Solv3R, list_images, load_images
    from solv3r.export import save_solve

    paths = list_images(args.images, max_images=9)
    if not 2 <= len(paths) <= 8:
        parser.error("CPU reconstruction requires 2 to 8 views; select a shorter image or frame sequence")
    threads = min(4, os.cpu_count() or 1)
    torch.set_num_threads(threads)
    torch.set_num_interop_threads(1)
    start = time.monotonic()
    model = Solv3R.from_pretrained(args.checkpoint, device="cpu")
    with torch.inference_mode():
        frames = load_images(paths)
        ctx = model.encode(frames)
        state = model.solve(ctx, calls=16)
        predictions = model.decode(state, ctx)
        names = [Path(path).name for path in paths]
        save_solve(str(args.out / "solve"), frames, predictions, names, sky=False, html=False)
    receipt = {"device": "cpu", "threads": threads, "solver_calls": 16, "view_names": names,
               "preprocessing": "upstream load_images: EXIF transpose, RGB, bilinear antialiasing, "
                                "first image long side 504 with dimensions rounded to multiples of 14",
               "resolution_hw": [ctx.H, ctx.W], "sky_mask": False, "torch": torch.__version__,
               "numpy": np.__version__, "python": platform.python_version(), "platform": platform.platform(),
               "model_load_through_export_seconds": time.monotonic() - start}
    (args.out / "cpu-run.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
