# Core source and command reference

[User guides](README.md) · [Project overview](../../README.md) · [Current status](../../STATUS.md)

Run command examples from the repository root with Python 3.11 or later. Each named profile keeps its own contract and evidence; the examples do not select a new default or establish a comparative authoring advantage.

## Run the core prototype

Use **Python 3.11 or later** from this repository's root. No external runtime dependency or installation is required.

```bash
python3 -m ontokin check docs/language-design/core-v0.1/01-independent-parts.ok
python3 -m ontokin evaluate docs/language-design/core-v0.1/01-independent-parts.ok --times 0 1 2 3
python3 -m ontokin evaluate docs/language-design/core-v0.1/02-gravity-and-release.ok --times 1 1.5 2
```

`check` reads the source, validates its static definitions, and checks the complete authored timeline. `evaluate` returns JSON samples containing object positions, orientations, velocities, ownership, physical assumptions, joint coordinates, and action status. The source file is unchanged. A SHA-256 source revision ties the results and diagnostic byte spans to the exact input.

The independently moving parts example produces these world positions:

| Time | Head position, m | Hand position, m |
| --- | --- | --- |
| 1 s | (1, 1, 0) | (1.5, 0.5, 0) |
| 2 s | (2, 1, 0) | (2.75, 0.5, 0) |
| 3 s | (2, 1, 0) | (2.75, 0.5, 0) |

The head retains its 90-degree local yaw when that action completes. The hand continues its independent slider motion while the root moves. The [executed conformance report](../../docs/engineering/conformance-results.json) checks these values and the other published expectations.

## Commands and failure results

The `check` and `evaluate` file commands, and default `export`, retain the existing single-source `core-0.1` contract. Export can explicitly select GLB/0.2 or GLB/0.3 with `--target`; `--bundle` reads a pinned offline file manifest. Program-agent operations retain their separately selected protocol.

| Command | Purpose |
| --- | --- |
| `python3 -m ontokin capabilities` | Inspect implemented operations, output levels, physical assumptions, and numerical limits. |
| `python3 -m ontokin agent --store DIR` | Serve versioned JSONL agent requests with durable local source, request, run, and artifact state. |
| `python3 -m ontokin agent --store DIR --request request.json --wait` | Execute one request and return its terminal result; omit `--wait` for a retained queued receipt. |
| `python3 -m ontokin agent --protocol ontokin.agent/0.2 --store DIR` | Serve program-bundle JSONL requests in a separate durable store, with exact dependency and per-file source identities. |
| `python3 -m ontokin agent --protocol ontokin.agent/0.2 --store DIR --request request.json --wait` | Execute one versioned program request and return its terminal response. |
| `python3 -m ontokin agent --protocol ontokin.agent/0.3 --store DIR` | Serve native surface source workflows and bounded triangle inspection in a separate durable store. |
| `python3 -m ontokin check FILE.ok` | Validate and preflight the declared timeline. |
| `python3 -m ontokin check FILE.ok --level represented` | Check source representation while disclosing unresolved support requests. |
| `python3 -m ontokin check FILE.ok --level constructed` | Derive the initial world state before time-zero actions, without requiring later actions to be admissible. |
| `python3 -m ontokin evaluate FILE.ok --times 1 1.5 2 --side before` | Sample the incoming side of an event or natural completion. The default side is `after`. |
| `python3 -m ontokin evaluate FILE.ok --times 0.5 --object first.ball --frame first.frame` | Inspect one object in another frame. Velocity remains measured relative to world and is expressed in the requested axes. |
| `python3 -m ontokin export FILE.ok --output FILE.glb` | Bake, encode, and numerically verify a GLB under the named `ontokin.glb/0.1` contract; write a JSON sidecar. |
| `python3 -m ontokin export FILE.ok --output FILE.glb --fps 120 --end 1.5 --no-helpers` | Export a shorter interval with denser sampling and no display-only assembly/joint markers. |
| `python3 -m ontokin export PROGRAM.files.json --bundle --target ontokin.glb/0.3 --output MODEL.glb` | Compile pinned native surface source and export regional PBR geometry plus rigid animation. |
| `python3 -m ontokin conformance --output /tmp/ontokin-conformance.json` | Execute all 43 published source cases and write their measured results. |
| `python3 tools/run_surface_conformance.py --output /tmp/ontokin-surface-conformance.json` | Execute the fixed M01–M12 tests and report any pending identified external gates. |

JSON diagnostics contain the stable error code, failure phase, source revision, original UTF-8 byte span, governing rules, and repair guidance. Admission and transition failures found during preflight retain the time and phase of the authored failure. Receiving a suggested repair does not apply it.

For the core file commands, exit status is `0` for success, `1` for I/O failure, `2` for an invalid/conflicting source, unavailable sample, numerical failure, or resource limit, and `3` for an unsupported requested capability/level. Core conformance returns `1` when its run fails. Agent one-request mode returns `1` for a rejected, failed, or unknown result; JSONL clients inspect each response's status and diagnostics. Generic `check --level delivered` still returns unsupported because it names no destination contract. Use `export` for the selected GLB contract, or name the compatible `ontokin.glb/0.2` or `ontokin.glb/0.3` destination in a program-agent export request. The separate surface conformance runner uses `1` for executed failures or an unstable run and `2` for pending selected requirements.

Sample times written on the command line are exact decimal seconds. Source time quantities first become canonical binary64 values, and event scheduling preserves those values exactly. A decimal sample of `0.1` is therefore slightly earlier than an event authored as `0.1[s]`. Returned `boundary_times_seconds` gives the exact event and completion times; use those strings for exact boundary inspection.

For an optional installed `ontokin` command, install the checkout in a Python environment with `python3 -m pip install -e .`. The conformance command expects this repository's fixture directory; a packaged installation can specify it with `--fixtures PATH`.
