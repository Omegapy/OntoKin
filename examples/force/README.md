# Record force-driven source as GLB

`ontokin.glb/0.5` records the motion of a `force-0.1` program in a self-contained binary glTF file. A GLB viewer plays the recorded poses. It does not apply forces or run OntoKin physics. The editable `.ok` source and its exact pinned dependencies remain authoritative.

[OK-ENG-007](../../docs/engineering/OK-ENG-007-native-force-glb-export.md) defines the export contract. [OK-LANG-005](../../docs/language-design/OK-LANG-005-finite-center-of-mass-force-intervals.md) defines force behavior. This component does not establish contacts, continuous torque, general rigid dynamics, or complete F01–F12 acceptance; see [STATUS](../../STATUS.md) for verified scope and pending gates.

## Command-line export

From the repository root, export the unchanged single-interval fixture:

```bash
python3 -m ontokin export \
  docs/language-design/force-v0.1/p01-single-interval.files.json \
  --bundle --target ontokin.glb/0.5 \
  --end 2.5 --fps 60 --no-helpers \
  --output /tmp/ontokin-force/interval.glb
```

This writes `interval.glb` and `interval.export.json`. The report identifies the complete source program, the exported byte hash, the recording interval, sampling limits, and decoded validation results. A source file with no imports can be passed directly without `--bundle`. Imported programs require an `ontokin.files/0.1` manifest that identifies every exact offline dependency.

`--end` is an exact decimal number of seconds from zero through the authored scene duration. Export evaluates that prefix only. A valid short recording can succeed even if a later force activation would fail. Omitting `--end` requests the complete authored duration. Source, type, and profile checks still apply to the complete source program.

The requested frame rate is a minimum. The exporter adds exact in-interval boundaries and increases sampling when the conservative acceleration and angular bounds require it. The defaults are 60 frames per second, a position tolerance of 0.001 m, a rotation tolerance of 0.001 rad, and a time tolerance of 0.000001 s. A valid evaluated state can exceed the bounded GLB representation. Such a request fails visibly rather than silently increasing tolerances or substituting another target.

Acceleration subdivision uses free-sphere force intervals. Prescribed curved motion, such as an offset body following a rotating carrier, can require a higher requested frame rate. The byte reader checks the resulting poses and rejects a recording whose interpolation exceeds the chosen tolerance.

Older command defaults are unchanged. Force programs require the explicit `--target ontokin.glb/0.5`; selecting GLB/0.1 through GLB/0.4 does not migrate their source semantics.

## Agent delivery and retrieval

Start the explicit force service:

```bash
python3 -m ontokin agent --protocol ontokin.agent/0.5 \
  --store /tmp/ontokin-force-agent --wait
```

Use the existing [Agent/0.5 request schema](../../docs/language-design/agent-v0.5/request.schema.json). After a successful `create` or `edit`, an `export` request names that accepted `program_revision`, `destination: "ontokin.glb/0.5"`, and optional `options`. The same destination and options can be supplied to `create`, `edit`, or `validate` with `requested_level: "delivered"`.

| Field | Meaning |
| --- | --- |
| `options.end` | Exact decimal endpoint, such as `"2.5"`; omitted means the scene duration |
| `options.fps` | Minimum recording rate; the adapter can add samples within its resource limits |
| `options.position_tolerance_m` | Maximum permitted position error for the supported recording checks |
| `options.rotation_tolerance_rad` | Maximum permitted rotation error for the supported recording checks |
| `options.time_tolerance_s` | Maximum permitted exact-clock to float32 time displacement |
| `options.helpers` | Include or omit display-only assembly and joint markers |

A successful response contains a fresh run for the requested interval, an `artifact_id`, `sha256`, `total_bytes`, and the conversion report. Send `artifact` requests for that identifier with `offset` and `max_bytes` (at most 65,536). Decode each `data_base64` chunk, advance to `next_offset`, concatenate the chunks, and verify the complete byte length and SHA-256. Retrieval identifies the original program revision and exporter implementation.

Only accepted snapshots permit ordinary export. A failed delivered edit preserves the previously accepted source. Cancellation and final-response budget failures commit no new source acceptance, run, or artifact. A numerical failure may retain its valid evaluated prefix for diagnosis; that is not delivered output. An exact request-ID retry returns its retained receipt, while changing the payload under that identifier is rejected.

Discovery advertises GLB/0.5 as available within its bounded profile. The protocol number, store schema, source-bundle schema, request fields, and older catalogs remain unchanged. There is no host `apply_force` operation; force edits change the authorized source and produce a new immutable program revision.

## Verification

The interface tests execute real exports and chunk retrieval, short-prefix delivery, failed candidate preservation, request retries, lowered final-response budgets, and cancellation after artifact preparation. The CLI checks verify exact source bytes, complete GLB/report pairs, explicit target selection, prefix behavior, and staging failures.

From a clean, identified checkout with the pinned verification-only schema packages prepared, retain and audit the actual delivery workflow:

```bash
python3 tools/build_force_delivery_demo.py \
  --output-dir /tmp/ontokin-force-delivery
python3 tools/verify_force_delivery_workflow.py \
  --workflow-dir /tmp/ontokin-force-delivery \
  --output /tmp/ontokin-force-delivery-audit.json
```

Use a new empty recording directory. The writer exercises seven fixed cases, including atomic generated-instance mass, force and duration repairs, source evaluation, explicit low-rate GLB/0.5 export, and complete artifact retrieval. It also records invalid and stale edits, exact export retries, project isolation, cancellation, a lowered final-response budget, and the valid P21 prefix followed by its failing full-horizon request. Package, tool, fixture and source revision identities must remain unchanged throughout recording.

The separately versioned `ontokin.force-delivery-workflow/0.1` retains every request and response. Each `cases/Pxx` directory includes exact accepted source units, the source bundle and manifest, the retrieved `scene.glb`, its actual conversion report, and reference samples obtained through Agent inspections of that export's retained run. The independent audit reconstructs all transported bytes and checks fixed source expectations, boundary histories, intermediate decoded poses, unchanged sibling motion and unchanged geometry/materials across physical repairs. Its focused malformed-evidence tests run without a service, compiler, evaluator or exporter.

Write the audit outside the recording directory to preserve its complete file inventory. A passed delivery audit reports `destination_validated: false`: the native geometry checker and reviewed browser captures must consume these same retrieved artifacts as separate validation roles. The historical source-only workflow and its versioned evidence retain their original scope.

With the policy's pinned Node.js 22 verification tools and Chromium prepared, run both destination roles over the retrieved bytes:

```bash
node tools/verify_force_native.mjs \
  --demo-dir /tmp/ontokin-force-delivery \
  --agent-workflow --agent-audit /tmp/ontokin-force-delivery-audit.json \
  --output /tmp/ontokin-force-delivery-native.json
node tools/verify_force_viewer.mjs \
  --demo-dir /tmp/ontokin-force-delivery \
  --agent-workflow --agent-audit /tmp/ontokin-force-delivery-audit.json \
  --output-dir /tmp/ontokin-force-delivery-browser
```

The explicit Agent mode requires the separately passed audit and verifies its workflow, tool, source and artifact hashes. It uses the seven retrieved GLBs directly. Its report schemas distinguish Agent delivery from the independently built source corpus. The browser produces front, side and animated captures for all seven Agent cases; review those actual images and retain the identified visual assessment.

To exercise the broader source corpus, use `tools/build_force_demo.py --output-dir NEW_DIR`, followed by the same native and browser tools without the Agent options. That corpus contains 23 successful artifacts and five explicit delivery failures. The native checker covers all 23; the default browser selection covers nine representative cases and produces 27 captures. Each role reports its actual selection.

Use the repository's [local validation policy](../../docs/engineering/OK-ENG-006-local-validation-and-hosted-ci-policy.md) and the current instructions in [AGENTS](../../AGENTS.md). Source-to-destination numerical checks and reviewed browser captures establish separate evidence from an Agent success receipt. Neither a receipt nor this guide declares the full product complete.

## Record and audit complete release evidence

[OK-ENG-008](../../docs/engineering/OK-ENG-008-force-release-conformance.md) defines the complete F01–F12 evidence contract. The separately versioned runner records the actual command, interpreter, dependency pins, source commit/tree, eligible input bytes, output hashes and measured results:

```bash
python3 tools/run_force_conformance.py execute --role source --output-dir /tmp/ontokin-force-source-execution
python3 tools/run_force_conformance.py record --role source-build --output-dir /tmp/ontokin-force-build-execution --report /tmp/ontokin-force-source-artifacts/workflow.json -- python3 tools/build_force_demo.py --output-dir /tmp/ontokin-force-source-artifacts
```

Prepare the [six pinned Python verification packages](../../tools/force-agent-verification-requirements.txt) before recording acceptance roles. All execution and primary report destinations must be new. Source, mapped tests, the three complete CPython compatibility runs, both actual Agent workflows and audits, native/browser checks, and current inherited core/Agent/construction/surface/impulse roles remain distinct requirements. Node 22 and the locked viewer tools are required for the native/browser and complete inherited visual roles.

`tools/build_force_release_evidence.py --plan PLAN.json --output-dir NEW_DIR` collects explicitly named immutable files without changing raw results. Its plan names copy sources and relative destinations, optional new reference manifests, and role records. A `{"$file": "relative/path"}` placeholder inserts that collected file's measured path, SHA-256 and byte length. Mutable stores and caches are excluded and disclosed. The collector does not execute checks or provide a visual review.

After all required actual captures have been inspected and their identified reviews collected, audit the complete retained evidence:

```bash
python3 tools/run_force_conformance.py audit --evidence /tmp/ontokin-force-release/evidence.json --evidence-root /tmp/ontokin-force-release --output /tmp/ontokin-force-release/audit.json
```

The audit rechecks current source identities, execution inventories, raw source observations, complete retrieved bytes, independently decoded motion, inherited evidence readers and each required PNG review. `--allow-pending` changes only the exit policy; it cannot turn missing evidence into a pass. Historical CI-shaped reports retain their original pending reasons, while the new contract reconciles only their execution-provider role with actual current local runs.
