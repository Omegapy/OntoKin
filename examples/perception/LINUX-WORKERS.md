# Linux worker qualification

The two pretrained models ran in separate Python environments on a Linux x86-64 CPU host. A complete Solv3R run consumed photographs. For FlowHMR, the environment executed the motion generator and separately attempted the raw-video pipeline. These runs have different acceptance criteria.

## Solv3R from two photographs

The tested CPU configuration used CPython 3.12.14, PyTorch 2.8.0+cpu, NumPy 2.3.5, Pillow 13.0.0 and safetensors 0.8.0. Prepare a fresh Linux worker environment from the OntoKin checkout. The paths below are relative to a new job directory. An internet connection is needed for provisioning.

```bash
job=$(mktemp -d)
python3.12 -m venv "$job/solv-env"
"$job/solv-env/bin/python" -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.8.0+cpu
"$job/solv-env/bin/python" -m pip install numpy==2.3.5 pillow==13.0.0 safetensors==0.8.0
git clone https://github.com/ubc-vision/solv3r.git "$job/solv3r"
git -C "$job/solv3r" checkout --detach ef8da34f3736d6c241b3ba3cd074073c06e90b8f
mkdir "$job/views"
cp "$job/solv3r/examples/data/park/DJI_0737.jpg" "$job/solv3r/examples/data/park/DJI_0738.jpg" "$job/views/"
curl -fL https://huggingface.co/jgkwak/solv3r/resolve/c95998a2458e49232b2fbef7a247a2de9edb03fe/solv3r.safetensors -o "$job/solv3r.safetensors"
printf '%s  %s\n' 3cf9f215e6fee4639547cea482081be8103f7be5fdea57f58c795f552a624cb4 "$job/solv3r.safetensors" | sha256sum -c -
"$job/solv-env/bin/python" -m tools.perception run-worker solv3r "$job/views" "$job/result" \
    --checkout "$job/solv3r" --python "$job/solv-env/bin/python" --checkpoint "$job/solv3r.safetensors" \
    --device cpu --timeout-s 240
"$job/solv-env/bin/python" -m tools.perception point "$job/result/observation" 0 252 168 --target-view 1
```

The CPU option uses the original encoder, solver, decoder and writer. It accepts two to eight views, limits the worker to four Torch threads, and performs 16 solver calls. On the two 504 × 336 park views, the final worker took 14.42 s from model load through export. Two runs produced identical NPZ and PLY bytes. The first view's central pixel projected to (250.623, 196.210) in the second. The measured depth minus the prediction at the nearest pixel was −0.00077243 model units. This checks consistency between predictions from one reconstruction. Physical scale and accuracy against a surveyed scene require independent calibration. [Solv3R project](https://ubc-vision.github.io/solv3r/) · [Model card and weights license](https://huggingface.co/jgkwak/solv3r/tree/c95998a2458e49232b2fbef7a247a2de9edb03fe)

## FlowHMR motion generation and raw-video qualification

A separate Linux environment loaded all 318 checkpoint tensors and ran the original motion generator with 460,397,547 learned parameters. The control used 16 time samples, 20 Euler steps, seed zero, the upstream classifier-free zero body-image feature, and a stationary camera. It produced 52-joint rotation fields in 8.98 seconds on CPU. The handoff includes the control script, input assumptions, tensor shapes, output hash and arrays. These internal fields have no observed subject to which a fitted action can be attributed.

The official raw-video CLI was also run on the upstream example with `--static_camera`. Its preflight reported the following missing assets.

| File under the upstream checkout | Access needed |
| --- | --- |
| `ckpts/sam-3d-body-dinov3/model.ckpt` | Authorized SAM 3D Body weights |
| `ckpts/sam-3d-body-dinov3/assets/mhr_model.pt` | Authorized MHR body model from the same distribution |
| `assets/body_models/smplh/neutral/model.npz` | Licensed neutral MANO/SMPL-H body model |

The released FlowHMR checkpoint was accessible. SAM 3D Body returned HTTP 401 for both gated files. The static-camera path bypasses VGGT camera estimation. The next worker needs authorized body assets, the upstream V2M dependencies, and a compatible execution device. On that worker, run the fixed-camera video via the command in the [workflow](README.md#run-the-model-workers-on-linux), then import and test the resulting motion. Ordinary language-function work remains paused pending that fresh run. [FlowHMR installation and access requirements](https://github.com/flowhmr/flowhmr/blob/87ebb483ce9da32be72c67971bc8fd76f27251f3/docs/install.md) · [Released FlowHMR checkpoint](https://huggingface.co/fafsaf1/flowhmr-0.46B/tree/1eb105e554e0cfc1846ea5feac8c2d516a36d319)
