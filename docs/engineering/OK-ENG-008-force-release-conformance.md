# OK-ENG-008: provider-neutral finite force release conformance

Status: adopted implementation contract, October 19, 2026. Execution results are
separate evidence. This document makes no claim that the release has passed.

This contract binds the unchanged F01–F12 requirements of
[OK-LANG-005](../language-design/OK-LANG-005-finite-center-of-mass-force-intervals.md)
to the owner's [local validation policy](OK-ENG-006-local-validation-and-hosted-ci-policy.md).
It introduces `ontokin.force-local-conformance/0.1`,
`ontokin.force-release-evidence/0.1`, and `ontokin.local-execution/0.1`.
It does not change historical CI schemas, adoption records, source fixtures,
expected values, delivery tolerances, or the meaning of a historical pass.

## Finite promise and mandatory roles

The named release combines force-0.1 source, the explicit `ontokin.agent/0.5`
service and store, and recorded `ontokin.glb/0.5` delivery. Finite world forces
act at the center of mass of supported free homogeneous spheres. The existing
gravity, impulse, release, source identity, geometry and PBR rules remain in
effect. GLB output records transforms and explanatory metadata. It does not
execute live physics in a destination.

The additive [local mapping](../language-design/force-v0.1/conformance-local-v0.1.json)
contains requirements, literal test IDs and source case IDs, never measured
statuses. A gate passes only when all its mapped source cases, measured methods
and required external roles pass for the current eligible input bytes.

| Gate | Required meaning |
| --- | --- |
| F01 | Typed native force authoring, contextual identifiers, stable keys, occurrence identities and pinned imports. |
| F02 | Independent center-of-mass acceleration, position, velocity, momentum and work checks. |
| F03 | Overlap, cancellation and order-independent canonical final force/acceleration aggregation. |
| F04 | Exact completion, replacement, zero force and unchanged-acceleration anchors. |
| F05 | Gravity, off-center impulses, release at action completion, ordering and atomic rollback. |
| F06 | Zero time, durations, exact binary64-derived rational clocks, and ends beyond the requested horizon. |
| F07 | Physical/type/frame/numeric admission, interior extrema, failure boundaries and valid short prefixes. |
| F08 | Generated composition and exact source repairs with unchanged siblings, geometry, materials and libraries. |
| F09 | Actual Agent authoring/inspection/repair, retries, stale revisions, cancellation and independent stores. |
| F10 | Complete nested history accounting, cancellation and source/Agent/delivery budget parity. |
| F11 | Actual component and Agent-retrieved GLBs, source geometry/PBR, independent fixed and dense motion, and reviewed real browser captures. |
| F12 | Current core, A01–A10, C01–C20, M01–M12 and I01–I12 roles; every current regression test; the complete compatibility and visual execution roles. |

All 56 adopted force source cases execute independently of unittest counts.
Original `acceptance.json` and `reviewed-acceptance.json` hashes are fixed. The
runner independently applies `source-errata.json`, checking original source
hashes, exact replacement spans, unchanged imported units and old sample values
before applying the adopted S10/S11 and P09 corrections. It compares actual
states to those adopted expectations, including exact force histories and source
locations. A copied expectation is not an execution result.

F11 requires the complete 23-case component corpus: P01–P17, P19, P21, P22 and
three held-out source programs. It also requires the five predetermined delivery
failure records and absence of their GLB artifacts. The separate actual Agent
delivery corpus is P01/P07/P10/P11/P12/P13/P21; exports and complete chunk
retrieval must identify exactly the bytes independently decoded and rendered.
The component workflow and Agent workflow retain different schema identities.
Browser coverage is nine component cases with 27 captures and all seven Agent
cases with 21 captures. Every decoded binary32 key, interval quarter/mid/three-
quarter probe, and the independent prime-denominator dense schedule remain
required. Passing selected examples is not complete corpus coverage.

The retained-byte reader independently checks the complete source force and
impulse projections, occurrence identity, mass, velocity, angular velocity and
pose authority for every component case, including held-out programs. It binds
failed deliveries to their actual raw source units and bundle/manifest bytes.
Before decoding accessors it checks the fixed source geometry declarations,
10,000-key, 250,000-carrier-pose, 250,000-vertex, aggregate accessor and 64 MiB
limits. The selected scene must include every flat carrier; matrices, hierarchy,
skins and other unmodeled transform authorities cannot override those tracks.

Position and rotation tolerances remain at most 0.001 m/rad, and the exact source
clock tolerance remains at most 0.000001 s. Source quaternion comparisons retain
their 1e-9 rad bound. The independent binary reader normalizes binary32
quaternions before shortest-arc interpolation. Both its decoded poses and the
retained Three.js observations must independently meet the unchanged source
motion tolerances. Their additional reader-to-reader rotation comparison allows
at most eight binary32 half-ULPs (approximately 4.77e-7 rad), further limited to
twice the declared rotation tolerance, for Three.js world-matrix decomposition
roundoff. This separate numerical comparison cannot relax either source check.

## Actual execution and compatibility

`tools/run_force_conformance.py execute` executes a named Python role and writes
a fresh directory containing `execution.json`, `report.json` and `execution.log`.
It supports source, mapped-tests, regression, core, agent, construction, surface
and impulse roles. The mapped and regression roles measure each actual unittest
ID, status and duration and retain loader, fixture, skip and unexpected results.
Skipped, expected-failure, absent, duplicated or unexecuted methods do not pass.
Regression inventories come from actual current discovery. The additive mapping
also preserves the earlier regression inventory. Previously published method
identities remain substantive guards when new delivery behavior is added. New
discovered tests are mandatory, not excluded by the earlier inventory.
The published baseline is 753 methods at `f901b1ac3b09fcb20842285f12d407dc919f9632`;
the five additional destination oracle methods at
`f05684d42c9ab8112efa2b137f5274fd70bd6754` are a separately identified preserved
cohort. The local checker tests are also explicit mapped requirements.

The complete compatibility role requires separate actual **CPython 3.11, 3.12
and 3.13** full-suite executions. One interpreter, three differently labeled
files, a configured matrix or historical green jobs cannot satisfy it. Each
execution must retain the same current eligible source/test/fixture inventory.
The force native/browser and inherited complete visual executions use **Node 22**, the current locked
Three.js 0.180.0, gltf-validator 2.0.0-dev.3.10, Playwright 1.56.1 and esbuild
0.25.10, and an identified actual Chromium/WebGL environment. Additional
platforms, interpreters or destinations are supported only to their measured
scope; these finite roles make no unexecuted platform promise.

`record` executes an explicitly requested, directly named repository tool and
captures its actual exit code, log and newly created primary report. Its
allowlist includes force component/workflow builders, independent workflow
auditors, source/Agent native and browser verifiers, and the complete local
visual driver. Source/Agent workflow execution and its independent audit have
separate envelopes. This is not retrospective attestation: the primary output
must be absent before execution. `audit` only reads retained evidence. It never
runs argv or commands obtained from an evidence file.

Every envelope records the real provider, argv, working directory, interpreter,
platform, dependency versions, timezone-bearing start/end timestamps, exit code,
log and output hashes. It captures the exact Git commit and tree, disclosed
worktree changes, implementation identity and eligible input inventory before
and after execution. The eligible bytes must remain stable. To close a release,
they must match the actual blobs in the captured commit. Git reads disable
ambient `GIT_*` overrides, global/system configuration, hooks and fsmonitor;
replacement objects, lazy fetching and interactive Git authentication are also
disabled. Every actual Python execution identifies the six installed verification
packages against the exact committed requirements, including each matrix member.
These Git reads do not fetch, change refs, stage files, rewrite source or alter an index.
A later metadata-only commit can refer to an earlier execution only when every
eligible blob still matches. Dirty or untracked eligible inputs remain visible
and cannot be represented as committed release inputs.
The inventory includes executable scripts, tests, normative grammars and
contracts, fixture inputs, dependency pins and the mandatory documentation
verifier with its source map. Generated engineering evidence and the measured
progress prose in STATUS/GOAL are excluded, so publication of measured results
does not change the identity of the implementation that produced them.

## Retained evidence and inherited-provider reconciliation

The release evidence manifest identifies a confined evidence root, current
implementation/input inventory, named execution envelopes and a complete
SHA-256/byte-length inventory of retained artifacts. References are relative
POSIX regular-file paths. Traversal, symlinks, duplicate JSON members, nonfinite
JSON numbers, ambiguous identities and changed hashes are rejected. Mutable
SQLite databases, WAL/SHM files and process-local caches are not release
artifacts. Immutable requests/responses, accepted source snapshots, manifests,
source reports, GLBs, independent reports, browser harnesses, PNGs and logs
retain their actual bytes and hashes. Hash closure is a reproducibility check,
not a cryptographic assertion about an unobserved external executor.

The historical C/M/I schemas are not rewritten to contain invented hosted run
or job IDs. Current legacy source/method reports are retained verbatim, including
their original pending reasons. The new auditor independently checks their
current implementation/input identities and executed method inventories, then
re-audits the existing raw C20, M and I workflow/destination/browser readers.
Current core and A01–A10 observations are also checked. Missing non-provider
evidence remains pending until the corresponding raw role is independently
verified. The new local matrix and visual execution replace only the historical
execution-provider requirement. They do not excuse another missing source,
protocol, geometry, motion, visual, regression or compatibility role.
The complete visual role retains its exact current step arguments, working
directory, prerequisite order, every expected raw report and log, copied source
inventory and Git identity. A passed wrapper cannot excuse a failed raw browser,
format, numerical-comparison or validator result. Genuine pending C/M/I provider
reasons remain visible for the separate role reconciliation.

Reports distinguish `passed`, `pending` and `failed`, with explicit reasons for
missing, stale, blocked or contradictory evidence. `--allow-pending` only changes
the command exit policy. It cannot change a gate to passed. A complete finite
force release requires all F01–F12, every source case and every mandatory role;
the report always keeps `full_product_conformance_certified: false`.

## Identified visual review

`ontokin.force-visual-review/0.1` has `status: reviewed`, a nonempty `reviewer`,
`reviewed_at_utc`, `browser_report_sha256`, and `source_kind` equal to
`source_component` or `agent_retrieved_artifact`. `captures` contains one row per
actual required PNG with `fixture`, `view`, `time_seconds`, `capture_sha256`,
`program_revision`, `artifact_sha256`, `status: reviewed`, a concrete
`observation`, and an empty `defects` array for an accepted image. All digests use
the `sha256:` prefix. The reviewer must actually inspect the images. A numerical
pass, generated image, contact-sheet filename or empty assurance is not review.
The auditor checks PNG signatures/chunk CRCs/decompression/dimensions and binds
every observation to its browser report and exact source/artifact/capture bytes.
Any regenerated capture requires its own identified review.

## Scope limits

The broader [GOAL](../../GOAL.md) remains open after any finite force pass. This
contract does not establish contacts, continuous torque, friction, flexible or
deformable matter, liquids, locomotion, wing/fin control, vegetation response,
terrain scale, textures, live game execution, Blender or other unrun engines.
The authoring benefit still requires an adopted direct-tool baseline, unseen
variants and measured repair/preparation/cost/quality comparisons. No percentage
benefit or full-product completion can be inferred from this corpus.

During execution environments where unrelated filesystem operations can replace
files beneath a live SQLite connection, run Agent/full-suite/workflow roles in an
exclusive executor window. This is an execution isolation requirement; it does
not change store semantics, journal mode, runtime behavior or acceptance limits.
