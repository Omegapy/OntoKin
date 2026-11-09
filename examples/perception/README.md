# Develop OntoKin actions from observations

This experimental tool lets a language developer turn a measured movement into an editable OntoKin action and check the result against the original observations. The first examples use a published human-motion capture and a small camera reconstruction with known geometry. Run the commands from an OntoKin checkout. Use a new directory for each output.

## Try the included human capture

Use a Linux development environment with Python 3.11 or later. The tested environment uses CPython 3.12.14 and NumPy 2.3.5. The optional observation tools use NumPy. Normal OntoKin programs use their existing runtime.

```bash
python3 -m venv /tmp/ontokin-observe-env
source /tmp/ontokin-observe-env/bin/activate
python -m pip install -r tools/perception/requirements.txt
python -m tools.perception import flowhmr examples/perception/data/flowhmr_demo.npz /tmp/observed-human --source-kind published --capture flowhmr_demo
python -m tools.perception synthesize /tmp/observed-human /tmp/root-action --start-frame 30 --stop-frame 60
```

Open `/tmp/root-action/root-motion.ok` to see the fitted velocity, starting position and reusable `advance(duration)` method. `root-motion.glb` animates a sphere at the estimated SMPL-H model translation. `fit.json` records the observed error in metres and the result of executing the action 20% faster. The example window was selected after inspecting the capture. Frames 30–51 supply the fit. Frames 52–59 test it. All 155 frames together fail the same 25 mm tolerance. A refused fit leaves its output directory absent.

## Fit a joint action on the full capture

```bash
python -m tools.perception articulate /tmp/observed-human /tmp/left-knee --joint left_knee
```

The method fits a hinge axis in the parent frame and a short sequence of angular targets. The editable `knee.ok` uses OntoKin's native hinge and `tween` operation. Open `knee.glb` to view the exported action. The exporter checked 5,877 sample times against the native program. The bar represents joint orientation. Its dimensions are display settings. In the published capture, 13 phases reproduced the left knee to within 9.84° across 38 held-out frames. The counterfactual source reduces the angular excursion by 20%. The comparison uses the angle between orientations, which accounts for equivalent quaternion signs. A fit that exceeds either the phase budget or the error limit is refused.

For a single command that replays the capture, camera example and free-flight experiment, run `python examples/perception/replay.py /tmp/observation-examples`. The output directory contains editable source, fit reports and the recorded refusal for the full-clip constant-velocity hypothesis.

## Inspect a reconstructed point

```bash
python -m tools.perception import solv3r examples/perception/data/solve-synthetic.npz /tmp/observed-room --source-kind synthetic
python -m tools.perception point /tmp/observed-room 0 1 1 --target-view 1
python -m tools.perception inspect /tmp/observed-room
```

The arguments after the observation directory are the view number, pixel column and pixel row. In this fixture the result is `[0, 0, -0.875]` in the first-view coordinate system. The point falls behind the second camera. When a point is visible in both views, the tool reports its projected pixel and the observed minus predicted optical depth at the nearest pixel. The unit is the model's reconstruction scale. A measurement in metres requires independent scale calibration. [Sample sources and licenses](data/NOTICE.md)

## Recover downward acceleration from a calibrated object track

The `metric-track` adapter accepts `position_m` triples, strictly increasing `timestamps_s` and the scalar string `coordinate_system="right_handed_y_up"`. The producer must establish a stationary metric frame independently. Solv3R's native scale alone is insufficient. Run `python -m tools.perception import metric-track track.npz /tmp/flight-obs`, then `python -m tools.perception ballistic /tmp/flight-obs /tmp/flight-fit`.

The tool fits starting velocity and a constant downward acceleration using the earlier samples. It simulates the native dynamic body against a held-out final quarter, then halves gravity and checks the predicted change. A straight trajectory with too little measurable curvature, a significant sideways acceleration, or a bad holdout refuses the hypothesis. Mass cannot be identified from this experiment. The synthetic replay includes a known −8.2 m/s² trajectory.

## Run the model workers on Linux

The [Linux worker record](LINUX-WORKERS.md) includes a reproducible pretrained Solv3R CPU run and the scope of the separate FlowHMR execution. Run each model in its own provisioned Linux environment. The controlling environment invokes the worker's Python executable, verifies the tracked Git checkout, records the capture and checkpoint hashes, and imports the resulting NPZ. Each job has its own output directory, log and finite process-group deadline. A successful observation import from an existing NPZ is independent of worker qualification.

| Worker | Checkout revision | Input | Environment preparation |
| --- | --- | --- | --- |
| FlowHMR | `87ebb483ce9da32be72c67971bc8fd76f27251f3` | One video | Use the upstream V2M environment and separately authorized body-model assets. [Installation](https://github.com/flowhmr/flowhmr/blob/87ebb483ce9da32be72c67971bc8fd76f27251f3/docs/install.md) |
| Solv3R | `ef8da34f3736d6c241b3ba3cd074073c06e90b8f` | One video or a folder of views | Prepare the upstream inference environment and its local safetensors checkpoint. [Code and weights](https://github.com/ubc-vision/solv3r/tree/ef8da34f3736d6c241b3ba3cd074073c06e90b8f) |

Set the paths to installed checkouts, environment interpreters and local checkpoints on the worker host. The command can be launched by a development agent on that host.

```bash
python -m tools.perception run-worker flowhmr /captures/walk.mp4 /jobs/human-001 \
  --checkout /workers/flowhmr --python /envs/flowhmr/bin/python \
  --checkpoint /weights/flowhmr_latest.ckpt --timeout-s 1800
python -m tools.perception run-worker solv3r /captures/room /jobs/scene-001 \
  --checkout /workers/solv3r --python /envs/solv3r/bin/python \
  --checkpoint /weights/solv3r.safetensors --device cpu --timeout-s 1800
```

Use `--static-camera` for FlowHMR only when the capture used a fixed camera. Inspect `worker.json` and `worker.log` for the exit status. A successful run saves the raw export under `raw/` and the observation under `observation/`. The wrapper expects upstream dependencies, auxiliary assets and access permissions to be in place. Each model's licenses apply separately.

## Observation format

An observation directory contains `manifest.json` and `arrays.npz`. The manifest identifies `ontokin.observation/1`, the adapter and its pinned writer contract, the source NPZ hash, the normalized array hash, and each array's dtype and shape. Capture identifiers, checkpoint labels and the source kind on a manual import are caller declarations. An absent value means unknown. The file reader accepts non-pickled NPZs up to 256 MiB uncompressed and checks member sizes before allocating the arrays. Split larger exports at the producer while retaining capture identifiers and the original frame indices in your experiment record.

| Evidence | Coordinates and time | Suitable use |
| --- | --- | --- |
| FlowHMR | Clip-local right-handed Y-up, estimated metres. The 52 SMPL-H rotation vectors are in radians. Time starts at the first exported sample. Internal pose diagnostics retain their distinct network frame. | Estimate body or joint motion. Optional foot-contact scores are model outputs. |
| Solv3R | First-view reference, +X right, +Y up, −Z forward. Camera intrinsics use model-resolution pixels with the origin at the upper left. Depth and camera translation share an uncalibrated scale. | Inspect geometry and cross-view consistency. Offline views have no implied timestamps. Streaming exit poses are kept separately from the arrival poses that correspond to depth. |

An explicit `--fps` supplies a uniformly sampled timeline when the source lacks one. For unordered photos, leave it unset. Cross-model fusion requires evidence for timing, scale and spatial registration. The two example inputs describe different scenes.

Run the development suite with `python -m unittest discover -s tools/perception/tests -v`. [FlowHMR export writer](https://github.com/flowhmr/flowhmr/blob/87ebb483ce9da32be72c67971bc8fd76f27251f3/flowhmr/pipeline/v2m_inference.py) · [Solv3R export writer](https://github.com/ubc-vision/solv3r/blob/ef8da34f3736d6c241b3ba3cd074073c06e90b8f/solv3r/export.py)
