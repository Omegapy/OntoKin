# C194 fixed-target qualification preparation

This directory freezes the proposed 365 mm and 375 mm target checks before
running the public edit-and-reuse pair. Read [PROTOCOL.md](PROTOCOL.md) and the
[C193 next task](../guide-repair-c193/NEXT-TASK.md). At the initial preparation
commit no target build, saved-scene replay or author trial has run.

The source pair starts at 380 mm in [starters/gauge.ok](starters/gauge.ok) and
[starters/gauge.py](starters/gauge.py). [The G/H expectations](frozen/expectations.json)
preserve the historical numerical rules. New wrappers inject only G/H case data
into the unchanged C193 artifact reader and scene inspector.

## Review, seal and execute

From the repository root, with NumPy available:

```sh
python3 -B docs/engineering/contact-preparation-c194/static_check.py
python3 -B docs/engineering/contact-preparation-c194/seal.py --review /absolute/path/to/review.json
python3 -B docs/engineering/contact-preparation-c194/run_preparation.py \
  --blender /absolute/path/to/blender-4.5.3-linux-x64/blender \
  --out /absolute/path/to/new-c194-preparation
```

The independent review must contain `passed: true` and
`input_manifest_sha256` matching `INPUTS.json`. Commit the sealed preparation
before the native command. The runner verifies the exact executable hash, all
frozen inputs and its execution ledger. It reserves only the fixed four builds,
retains failed outputs, independently reopens each available scene and checks
the actual receiving artifacts. A second runner invocation is refused.

After viewing all twelve original PNGs, save a visual receipt with `pass`,
observations and `panels` entries containing paths relative to the receiving
directory, exact `bytes` and `sha256`. Then join it to the automated record:

```sh
python3 -B docs/engineering/contact-preparation-c194/finalize.py \
  --results /absolute/path/to/new-c194-preparation/RESULTS.json \
  --visual-review /absolute/path/to/visual-review.json
```

Any failed preparation gate requires a stop before author dispatch. Raw and
final files retained from a failed transaction remain diagnostic outputs.
`RESULTS.json` never by itself authorizes the author pair; final qualification
also needs the observed visual receipt. The new public comparison protocol is
a later conditional step.

