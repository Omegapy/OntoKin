# Meter the rotary comparison on the operator's machine

Every model request and participant tool command must pass through the same serial `Gate`. The operator runs the model. The worker receives only the command and its own staged data. A stop callback terminates the entire guest process group. The application must also terminate the guest on its normal completion, controller exception or external termination. A partial trace invalidates the attempt and must never be resumed with a new allowance.

The first request to the local model hashes the supplied GGUF file. Every later request repeats that check and creates a fresh llama.cpp context. The adapter formats the transcript as a Qwen2.5 Instruct user message. It recognizes control markers only in the adapter's own message envelope. The exact IDs passed to evaluation and sampled by the model appear in each receipt. A freshly created context has zero cross-request cached tokens. The final stop token counts if one was sampled. Greedy decoding uses seed 42, four CPU threads and a 16,384-token context by default. Each invocation limits output to the smaller of the requested maximum, remaining context and remaining aggregate allowance after the full input. With less room than one output token, the adapter exits before evaluating the prompt.

For other operator-supplied clients, a request consists of `requestId`, `snapshot`, `prompt`, `maxOutput` and `remainingTokens` in one JSON object on stdin. Return a single JSON object on stdout with the same ID and snapshot, a string `text`, a nonempty `source` and a `usage` object. Supply `cachedInput`, `output` and **either** the inclusive `fullInput` **or** the disjoint `uncachedInput`. Include native accounting evidence as `native`. The operator trusts and pins the client outside the worker. A receipt supplied by the participant has no evidentiary value. A failing client, missing counters, invalid record, identity mismatch, or an overshoot closes the gate. The local adapter reports a verified pre-inference capacity refusal separately when the actual tokenized input leaves no space for an output. An exhausted aggregate allowance and an exhausted context window have distinct stop reasons. The `check_capacity.py` command accepts the same output, snapshot and client arguments as the model preflight. Any realized overshoot must be recorded as a failed admission. Client applications must bound actual inference before dispatch, as the local adapter does.

Run from this directory in an operator environment with the model file present and llama-cpp-python 0.3.36 installed. On the C181 Linux machine the source wheel built with GCC and G++, `CMAKE_BUILD_PARALLEL_LEVEL=5` and the settings in the runtime evidence. A native CPU build can depend on the host's instruction set. Compare the wheel and shared-object hashes before claiming an exact replay. Supply the same model, context, thread count and runtime for both timed arms.

```bash
python3 -B test_gate.py
python3 -B preflight.py --output /tmp/new-wall-run
python3 -B preflight.py --output /tmp/new-model-run \
  --snapshot gguf-sha256:cc324af070c2ecbfd324a30884d2f951a7ff756aba85cb811a6ec436933bb046 \
  -- python3 -B local_gguf.py /models/qwen2.5-coder-1.5b-instruct-q4_k_m.gguf
```

The standalone preflight times out an active local tool. It calibrates one real request containing a tool result, then runs two identical requests under a single aggregate cap. After each cutoff it attempts another model call and another tool call. The fixture tests supply synthetic usage to check accounting branches. The live invocation uses the local model. Each invocation writes a new JSON Lines trace and result into a new directory.

To recheck a recorded live trace without loading the model, run `python3 -B audit_receipts.py PATH/TO/events.jsonl --snapshot gguf-sha256:…`. It recounts the actual input and generated token ID arrays, compares the totals with each receipt and budget, and detects dispatch after a recorded cutoff.

The combined `vm_preflight.py` repeats the critical controls through the actual guest. Supply the guest script, extracted QEMU dependencies, kernel/initramfs configuration, a pristine harmless ext4 seed disk and the model client from above. See `--help` and the checkpoint evidence for the exact invocation. The active guest writes a marker and calls sync before sleeping. After the deadline, the controller kills the guest and checks the raw disk for the start marker and the absence of both forbidden writes. The token test consumes actual guest output and tears down a separate guest at its exact aggregate cap. The standalone probe alone does not demonstrate guest isolation.

The gate keeps its deadline in monotonic time. It rejects a late return, closes both dispatch paths, and kills the active local process group on timeout. For a model interrupted before a receipt arrives, usage is unknown and the attempt remains unscored. The supplied local client has no independently running remote request. A future client with an external service must demonstrate server-side cancellation and reconcile any late usage before admission.

[llama-cpp-python project documentation](https://llama-cpp-python.readthedocs.io/en/latest/) · [Qwen model and license](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF)
