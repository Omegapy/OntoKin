# Measuring a coding agent inside an isolated Linux worker

The [rotary repair pilot](../rotary-indexer-c179/README.md) compares edits to one moving assembly in Blender/Python and OntoKin. Both routes have the same initial interference between the rotating shoe and a fixed guard. The agent receives an editable starting design for its route, the common viewer and its task. The operator holds the checker, the other starting design and the model's usage ledger.

## What happened in the timed repair

| Route | Full input | Cached input | Output | Total tokens | Wall time | Model replies | Rejected formats |
| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| Blender/Python | 57,431 | 0 | 1,290 | 58,721 | 11 min 01 s | 27 | 26 |
| OntoKin | 49,029 | 0 | 7,589 | 56,618 | 16 min 13 s | 14 | 13 |

Each worker read its assignment successfully. Each agent then copied the assignment text into a shell block. The guest shell returned exit code 2. Neither agent invoked its native exporter. The Blender agent sent `SUBMIT` in an unlabelled Markdown code block 25 times. The registered controller accepts a bare `SUBMIT` or a labelled final block. The OntoKin agent repeated the assignment inside an unlabelled block 13 times. Both agents stopped when their remaining allowance could no longer fit the next input and one output token. VM startup took 8.93 seconds for Blender and 8.13 seconds for OntoKin, measured separately. No human intervened in a timed session.

The operator recovered the original and final disks and examined the submission directories. Both were empty. There was no submitted GLB, editable design or measurement to rebuild or view. The original frozen starters remain available as reference material. The masked scorer awarded **0/100 to each route**, with both the geometry and reusable-delivery gates failed. The [machine-readable result](results.json) identifies the registered run and the locked scoring evidence.

The pilot reproduced the failure at the boundary between the model and its tools. Its token and elapsed-time totals describe two unsuccessful attempts. They cannot establish the cost of a successful repair or whether typed physical intent improves one. Before a larger comparison, qualify a candidate coding agent on a public multi-step inspection, edit, native export and readback. Use that practice task to test command formatting, retries and submission handling. Reserve a fresh unseen repair for the next scored pair.

## The worker and the meter

The operator runs a CPU-only Qwen2.5-Coder-1.5B-Instruct model in a fresh llama.cpp context for every turn. The weights, prompt format, inference library, seed and settings are pinned. Each receipt lists the token IDs that the runtime evaluated and generated. Each call charges its entire input and the generated output, including a sampled stop token. The new context gives each call zero cross-request cache credit.

An unprivileged process in a software-emulated Linux VM runs each shell command. The VM has a loopback interface for its viewer, a read-only tool volume and a private writable work disk. The model and its ledger remain on the operator side. The controller sends commands over the VM's serial console. A cutoff disables model and tool dispatch and terminates the VM. The operator can examine work already written to its disk after termination.

On harmless fixtures, two calls containing a real guest tool result used 75 input and one output token apiece. The controller stopped at exactly 152 tokens and refused the next model call and shell command. In a deadline test, the worker wrote a start marker. The controller stopped it during a sleep, before a second marker could be written. The operator recovered the first marker from disk and verified termination of the VM and controller-side worker service.

An early model interaction reproduced a controller defect. A reply with several fenced shell blocks could be taken as one command. The revised loop presents the assigned task to the model, runs only its first fenced action, and lets it submit explicitly. On a fresh harmless task the model read a file, converted its text to uppercase, and submitted the correct file in two model turns. It consumed 553 input-plus-output tokens.

## What the starter checks establish

All 420 files listed in the C180 archive manifest matched their recorded sizes and hashes. The staged workspaces matched the frozen 28-file Blender and 237-file OntoKin inventories. Two independent Blender 4.5.3 LTS builds and two independent OntoKin builds each reproduced their own starter GLB byte for byte. The common checker measured 7.047 mm of north-guard penetration at 1.857360 seconds in all three starting GLBs. The 95 focused product tests and all 18 geometry, motion and score controls passed.

The study's interpretation still follows the [C180 comparison design](../semantic-physical-scope-c180/README.md). Results for this model and native toolchains are one case study. A claim about the value of the language across tasks also needs a common backend and a broader set of independent repairs.

## Inspect the controller

The [agent loop](pilot/agent_loop.py) and [session driver](pilot/session.py) connect the [token meter](controller/gate.py) to the [worker transport](vm/guest.py). The [model adapter](controller/local_gguf.py) reads pinned local weights. The [receipt auditor](controller/audit_receipts.py) recounts the stored IDs independently. The [collector](pilot/collect.py) recovers submitted regular files from a copy of a stopped disk. The original disk is preserved.

From this directory, run the following tests on Linux with Python 3.12.

```bash
python3.12 -B controller/test_gate.py
PYTHONPATH="$PWD/controller" python3.12 -B pilot/test_session.py
```

The C181 operator ZIP contains the frozen evaluator, raw receipts, guest bootstrap and native tool inventories. It also includes the offline source checkout and the prepared viewer. Keep the full operator package outside all participant machines. The [registration record](registration.json) identifies the execution card frozen before the first participant received the task.
