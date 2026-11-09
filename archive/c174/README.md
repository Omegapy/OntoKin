# Archived model-assisted development work

On November 9, 2026, the owner deferred FlowHMR and Solv3R until the project has suitable persistent hardware and an approved budget. Use main for language development. This archive is a reference for a separate future experiment.

## What this branch preserves

The [model integration](https://github.com/Omegapy/OntoKin/commit/038370794d828972cf5a06cdceac50275eda65f0) contains the [observation tools](../../tools/perception/) and the [recorded examples](../../examples/perception/README.md). This directory adds the C174 capture, qualification and Runpod scripts in their original form.

The complete C174 handoff is in the owner's OntoKin folder under the name `OntoKin_C174_Runpod_Preview_Handoff_2026-11-08.zip`. Its SHA-256 digest is `28f7d2e813d4be9b43cf7b6679b5cf1d71ec1c5abc8ba28c4f9d24c0c43d4c53`. The handoff includes the fixed-camera video, controller restore materials, V2M worker instructions, timeline, verified run records and checksums. Use its `README-START-HERE.md` and `NEXT-TASK.md` if the owner reopens this work. The capture wrappers expect the complete extracted package.

## Results to date

Solv3R ran on Linux CPU. The FlowHMR generator ran on prior motion data, and a person was tracked in all 300 analysis frames of the greenhouse clip. The input has 250 original frames at 25 Hz. The model pipeline uses a 30 Hz timeline, which repeats some source images. Fresh 3D body motion, root translation and left-knee fits on that clip are pending. The C174 check verified the four public files. The worker reported zero CUDA devices and lacked the four provider files. [Linux experiments](../../examples/perception/LINUX-WORKERS.md) · [Capture record](https://github.com/Omegapy/OntoKin/issues/109)

## Conditions for a future run

1. Obtain the owner's explicit decision to reopen the experiment. The [pinned FlowHMR pipeline](https://github.com/flowhmr/flowhmr/tree/87ebb483ce9da32be72c67971bc8fd76f27251f3) needs an appropriate Linux CUDA worker and the approved provider files. A physical project worker can use the package's direct route. A paid cloud allocation would require fresh spending approval.
2. Stage Meta's SAM 3D Body files under `ckpts/sam-3d-body-dinov3/` as `model.ckpt`, `model_config.yaml` and `assets/mhr_model.pt`. Stage the registered neutral SMPL-H model at `assets/body_models/smplh/neutral/model.npz`. All four paths are relative to the FlowHMR checkout. Follow the providers' access conditions. [Meta SAM 3D Body](https://huggingface.co/facebook/sam-3d-body-dinov3) · [MANO / SMPL-H](https://mano.is.tue.mpg.de/)
3. If the owner selects Runpod, use a persistent, authenticated Linux control host. The [preview](runpod/create-pod.sh) prints the proposed A40 configuration without making a provider call. Live allocation requires a separate explicit launch option and billing approval. The control host must keep running to request a stop at four hours and deletion at 24 hours. Retrieve and verify the evidence before releasing the Pod.
4. In the complete package follow the [worker preflight](worker/worker_preflight.py), [capture](run-capture.sh) and [capture checks](qualification/verify-capture.py). Review subject identity, frame mapping, axes, units and any contact estimates before accepting either fit.

The root fit uses observation frames 0–21 for fitting and 22–29 for testing, with a maximum 0.025 m error and a 20% speed-increase test. The left-knee fit allows at most 16 phases and a maximum 10° angular error, followed by a 20% amplitude-reduction test. Evaluate held-out frames whose source image was absent from fitting separately from repeated source images. Retain both outcomes, including any refusals. [Evaluator](qualification/evaluate-stretch.py)

For a no-charge review of just the archived controller, the [scheduler controls](runpod/test-setup.sh) use mock commands, and the [wrapper tests](runpod/test-run-c174.py) use local fixtures. The full C174 ZIP contains the historic receipts and original runbook.
