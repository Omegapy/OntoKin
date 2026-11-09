# Example inputs

`flowhmr_demo.npz` is the unmodified motion capture published by the FlowHMR authors, copyright 2025–2026 FlowHMR authors, under Apache License 2.0. The authors identify it as a video capture. It contains model-estimated human motion. Body-model files, weights and source video are separate. [Original file](https://github.com/flowhmr/flowhmr/blob/87ebb483ce9da32be72c67971bc8fd76f27251f3/data/rendering_data/examples/motions/flowhmr_demo.npz) · [Credits](https://github.com/flowhmr/flowhmr/blob/87ebb483ce9da32be72c67971bc8fd76f27251f3/data/rendering_data/README.md#license) · [License](LICENSE-Apache-2.0)

`solve-synthetic.npz` contains two synthetic views of 3 × 4 pixels written through the pinned Solv3R offline NPZ writer. It provides known camera poses, pixel intrinsics, depth and confidence for checking coordinate conversion. The corresponding upstream function is [save_solve](https://github.com/ubc-vision/solv3r/blob/ef8da34f3736d6c241b3ba3cd074073c06e90b8f/solv3r/export.py).

| Input | SHA-256 |
| --- | --- |
| `flowhmr_demo.npz` | `f70e90e2acc5b938a5dab9d3bbafa0f2098a7f9cf1d44d26172f1cc316954e39` |
| `solve-synthetic.npz` | `e9aeaa642b077aace18aeb880a78f12177df6e5d53015232189d434c158b0aac` |
