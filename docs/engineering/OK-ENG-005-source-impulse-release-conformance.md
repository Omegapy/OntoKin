---
project: OntoKin
document_id: OK-ENG-005
title: Source Impulse Release Conformance
version: 0.2
date: 2026-10-18
status: implemented-release-evidence-required
---

# Source impulse execution and release evidence

This procedure implements the finite release gate of [OK-LANG-004](../language-design/OK-LANG-004-source-impulses-and-free-sphere-dynamics.md). The [adopted corpus](../language-design/impulse-v0.1/acceptance.json) has 16 positive/boundary programs and 24 negative programs whose source bytes and independent expectations were fixed before implementation. Its status records that historical fact; it is not a result file. The [mapping](../language-design/impulse-v0.1/conformance.json) binds I01–I12 to those exact cases, concrete additional test methods and external evidence.

The runner compiles and evaluates each selected source fixture once, compares the prescribed states and diagnostic failures, and retains actual execution records. It independently checks sphere inertia, momentum updates, rotated lever arms, source spans, exact boundary sides, ordered accumulation, zero-impulse identity and complete failed-boundary rollback. It does not derive the expected velocity or source identity from an implementation report. Extreme cancellation checks retain exact canonical results rather than using a large relative tolerance that could hide failure to cancel to zero.

## Execute the source gate

```bash
python3 tools/run_impulse_conformance.py --output build/impulse-release/impulse-pending.json
python3 tools/run_impulse_conformance.py --case I03 --output build/impulse-release/rotation.json
python3 tools/run_impulse_conformance.py --full-suite-only --output build/impulse-release/full-suite.json
```

Exit 0 means the selected gate passed. Exit 1 records actual failure or unstable verification inputs. Exit 2 means required evidence is pending. `--allow-pending` changes only the exit status for a pending preparation run; it never changes JSON gate outcomes or permits a failed execution. Selecting a subset cannot set `full_gate_complete` true.

All full-suite reports must name every actually discovered and executed unittest method, including the fixed inherited floor recorded in the mapping. Missing, skipped, duplicate, failed or undiscovered required methods cannot satisfy a gate. The runner records both the current runtime identity and a stable inventory of runtime, tests, tools, workflows, specifications and source fixtures. Generated reports and archival evidence are excluded so writing a result does not invalidate itself.

The reviewed mapping identifies concrete methods for every operational case A01–A05, R01–R03, D01–D02 and L01. It retains the 464 inherited test IDs fixed when this profile was adopted, and requires all currently discovered tests in a full-suite execution. New profile requirements also bind named source, evaluator, Agent, catalog, CLI, exporter, workflow and reader tests. Shared methods execute once per conformance invocation; the reader checks their exact execution records rather than summing case-level counts. Resource and cancellation requirements have actual implementation tests and no longer use an implementation-pending placeholder.

| Gate | Required implementation evidence |
| --- | --- |
| I01 | Exact native syntax, type/frame errors, source target spans and mixed declaring profiles |
| I02 | COM momentum and independently calculated kinetic energy |
| I03 | Off-center angular impulse, world orientation and an external self point |
| I04 | Gravity continuation and release at natural action completion |
| I05 | Zero/repeated impulses, retained history, separate dynamic origin and analytic anchor, inherited frame inspection |
| I06 | Exact binary64 source clock, before/after sides, written order and whole-boundary rollback |
| I07 | Actual accepted P08 source edits to P09 and P10, with one pre-inspected writable occurrence |
| I08 | Frozen compile/runtime diagnostic phases and numerical cancellation/overflow domain |
| I09 | Complete retained Agent workflow, immutable revisions, retries, store isolation, cursor contexts and frames |
| I10 | Complete nested output accounting, sparse/dense sampling, cancellation and atomic delivery publication |
| I11 | The same retrieved nine GLBs through independent numerical and browser validation |
| I12 | Current complete inherited gates, full suite and required CI jobs bound to actual Git blobs |

## Connect actual external executions

The external evidence manifest uses `ontokin.impulse-release-evidence/0.1`. Each file reference is `{path, sha256}` with an exact `sha256:` hash and a relative POSIX path beneath `--evidence-root`. Retained nested files are similarly identified beneath their report directory. The top-level fields are:

- `implementation`: the actual current reference implementation identity.
- `workflow`: the actual Agent/0.4 exchanges, immutable source snapshots and retrieved artifact records.
- `native`: `build`, `destination`, `browser` and `visual_reviews`, identifying the same delivered source/artifacts.
- `legacy`: current `core`, `agent`, `full_suite`, `construction`, `construction_external`, `surface` and `surface_external` reports.
- `ci`: actual successful GitHub run and required job records for the exact current Git tree and verification inventory.

The workflow must contain real source operations for the frozen positive programs, including the evaluation-only extreme case, actual generated-occurrence patches from P08 to P09 and P10, rejected candidates, retries and frame-relative inspection. Compiling separate repaired source files cannot satisfy I07's Agent repair requirement. Accepted snapshots, each source unit, source edits, complete retrieved bytes, report samples and visual captures must agree on the same program/artifact identities.

The `ontokin.impulse-agent-demo/0.1` report retains every request attempt in increasing sequence order, including repeated request IDs. An identical retry must reproduce its original receipt without replaying the source transaction; changed-payload reuse must retain the real conflict response. Each successful source admission establishes `accepted_once`; retaining an invalid candidate in a snapshot directory cannot establish acceptance. Artifact chunks must cover the complete identified byte interval, decode successfully and reproduce the delivered GLB exactly.

The P09/P10 source repair scope must precede the patch in the actual exchange ledger. The inspected occurrence, program revision, entry source ID, source revision and writable span's file identity must agree with the exact P08 base source. Byte containment alone cannot authorize a stale or library-labelled source edit. Each fixture's returned latest-boundary impulse records must form a complete staged velocity chain ending at its actual after-side state. Rotated levers and resolved points are checked at the original application pose, and later retained copies must remain byte-equivalent. These requirements also apply to evaluation-only fixtures that have no GLB.

The A05 readbacks must use the same P03 project, revision, run, target, time and side. The world readback must equal the independently checked state sample. Ordinary position/orientation and velocity axes must follow the inherited frame conversion, with velocity still measured in world; explicitly world/self impulse fields and all unconverted state remain unchanged. An arbitrary local quaternion or unchanged world velocity cannot pass merely because impulse-record bytes match.

A03 is deliberately `partial` in the workflow report because the builder does not execute every store/CLI startup scenario. The conformance invocation itself must execute the four precise test methods listed in `workflow_requires_actual_test_complements`, covering independent stores, wrong-version startup before mutation, run provenance and malformed SQLite paths through the selected CLI. A list of those names or an aggregate success count is insufficient. Every gate that depends on the full workflow maps these actual complement tests.

I11 requires all nine `delivery_required` fixtures and front, side and animated browser captures for P02, P04, P08 and P11. The high-spin source requests low regular FPS and must receive sufficient actual quaternion samples. Independent decode checks geometry, winding, normals, PBR, local placement, fixed analytic world poses and `impulse_states_after` source-influence metadata; a reported pass flag alone is insufficient. Each capture requires an actual human or agent visual observation tied to its exact valid PNG bytes.

The native reports are `ontokin.impulse-native-build/0.1` and `ontokin.impulse-native-destination-validation/0.1`. The destination report identifies the actual native checker, its imported surface checker and the pinned tooling lock. Its source/artifact hashes must match the verified Agent snapshots and retrieved byte records. The audit reads actual GLB accessors and recomputes analytic geometry and motion. Every decoded animation key and each interval's quarter, midpoint and three-quarter probes must match the independent source trajectory. The retained Three.js `decoded_clock_samples` must contain that complete exact clock, actual per-object poses and independently recomputed error metrics; `decoded_clock_pose_comparisons` must equal the observed total. The separate fixed `samples` and `world_pose_comparisons` retain all adopted before/after reference observations.

P11 must preserve its requested one FPS option while supplying enough actual keys for the conservative authored angular-speed bound. The report must retain the actual rejected coarse-clock proof and the incorrect coarsened pose at 1.25 seconds. Merely checking complete-turn endpoints or the regular quarter-second samples cannot establish intermediate key correctness. Every GLB boundary's complete `impulse_states_after`, origin/anchor and inherited joint/action fields must also match the source and Agent state.

The browser report uses `ontokin.impulse-browser-validation/0.1`. It identifies the exact retained harness, browser/native/surface checker sources, pinned lock, workflow and native build. It must render the already verified artifacts with Y-up cameras fitted to the union of actual source geometry over the fixed quarter-second schedule. Required front/side captures use time zero; the animated capture uses 1.5 seconds. Numerical browser poses, region materials, camera geometry and completed playback must agree with the same source. Each PNG is parsed for real dimensions, chunk CRCs, complete bounded decompression and legal scanline data; rehashing invalid image bytes cannot produce valid evidence. Each visual observation must identify the capture hash, reviewer and concrete observation. Synthetic test fixtures are never release observations.

I12 requires the complete current inherited core/Agent, C01–C20 and M01–M12 gates, with freshly generated independent destination evidence. Historical release files cannot certify modified runtime bytes. CI must include the current Python 3.11, 3.12, 3.13 and 3D validation jobs, and the locally available named commit's complete eligible file set and blob contents must match the observed inventory.

The fresh M12 gate retains its existing surface-format inventory and full-suite report. I12 uses a separate current full-suite execution with the broader impulse inventory, including new `.ok`, JSON, Markdown and `.ebnf` contract files and Agent/0.4 schemas. The audit checks M12's complete mapped execution and reruns its retained-evidence readers under the current implementation before accepting that inherited gate. It does not reinterpret the historical surface inventory or reuse an archived release report.

The CI record uses `ontokin.impulse-ci/0.1` and requires actual successful, completed jobs for all three supported Python versions plus independent 3D validation. The declared implementation commit must exist locally. The reader compares its exact eligible Git tree path set and every regular blob with the current inventory, detecting both changed content and missing checkout files. Root-level metadata-only integration changes may use a later commit when the complete eligible implementation and verification tree remains byte-identical.

```bash
python3 tools/run_impulse_conformance.py \
  --external-evidence build/impulse-release/release-evidence.json \
  --evidence-root . --output build/impulse-release/impulse-conformance.json
```

This final audit reads retained evidence; it does not launch Khronos, Three.js, a browser or GitHub. It explicitly records `executed_external_tools: false`. Missing, stale, contradictory or unsupported evidence remains pending, including when a report claims success. Reader unit tests include actual source/service workflows and clearly marked synthetic private-reader inputs for deliberate malformed records; their success establishes the reader's behavior, not completion of unexecuted external tools. A release passes only when the current complete source, mapped tests and all identified external relationships pass together.

Follow [AGENTS](../../AGENTS.md) for branch ownership, test evidence, integration and recovery. All I01–I12 gates must pass together for this finite milestone. Every report retains `full_product_conformance_certified: false`; finite forces, contact, continuous torque, general dynamics and the remaining [GOAL](../../GOAL.md) requirements stay open.
