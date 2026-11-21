# Proposed versioned current-host readback qualification

**Status: proposal only; unimplemented and not adopted.** This document is a possible next phase after C271 P04. It grants no execution authority, changes no acceptance rule, and supplies no current-host or routine-validation result. P04 remains limited to exact historical-runtime recovery and a verified partial handoff. R03–R05 remain unmet.

## Problem and decision required

The historical C225 helper deliberately authenticates the C199 environment. It requires the original Node executable at its original absolute path, ten runtime/configuration file bindings, ten alias records, six source bindings, the exact 24 dependency files, and the unchanged historical HOST document. Recovering the executable elsewhere does not satisfy those guards. Replacing only a manifest's hashes would describe different inputs without qualifying them.

The operational CPU tests also hardcode the Node, dependency and HOST paths in `tests/test_static_tray_readback_v01.py`. Their `setUpClass` calls `format_check.build_manifest`; both `build_manifest` and `verify_manifest` require the historical Node version. A separate passing host suite cannot make these original default-discovery methods pass or establish that their assertions executed.

The next bounded phase should therefore produce and independently review an explicit **versioned operational execution contract**, together with a complete method/predicate map and implementation design. A possible new identifier is `ontokin.current-host-readback/0.1`; that name is illustrative, not an adopted schema. The decision must explain precisely which operational environment requirement would change and which scientific, dependency, failure-handling and resource requirements remain identical. It must explicitly reconcile the historical hardcoded methods with the default routine. Without that decision, current-host results remain supplemental evidence and R03 stays blocked.

## Preserve the historical case

Keep C199 `EXTERNAL-INPUTS.json`, its HOST inventory, the C225 helper and `SOURCE_HASHES`, historical preparation approvals, original source/test bytes, P02 failures and P03 refusal immutable at their identified published revisions. Retain exact byte copies when needed for recovery, with commit, tree, path, size and SHA-256. Record all later operational revisions separately. Do not overwrite old pins, relabel the historical refusal, regenerate old results, or claim the historical host has been restored.

The original source/test expectations must remain inspectable against the same Git objects even if an explicitly approved future operational revision changes setup resolution. Such a revision must not cause C225's old helper to accept different bytes: that helper remains the historical exact-recovery mechanism. A new operational preparer and manifest need their own version, provenance and review.

No shared runtime replacement, global symlink change, mount namespace installation, or implicit test-variable monkeypatch is proposed. Select an external task-specific runtime and dependency location only through the new, explicit contract.

## Bind and qualify the actual host

The new contract must declare the supported runtime version before any qualifying execution. This proposal selects no version and assumes no equivalence between available builds. It must record the actual executable's digest, size, mode, resolved path and alias; required shared libraries and loader configuration; relevant platform/interpreter identities; and how runtime closure is observed without treating the old HOST document as a current attestation.

Keep the retained Khronos validator, Three.js, loader, readback source, fixtures, numerical thresholds, result limits, environment variables, Node flags, and process/cleanup behavior unless a separate explicit requirement justifies a change. Their exact identities must appear in the new manifest. Record observed host data in a new file with a new identity. Preserve the C199/C225 records as references, not editable templates whose old identity is reused.

A reviewable candidate needs a clean source commit/tree; deterministic, safe dependency recovery from an authenticated source; refusal of partial, extra, changed or symlinked installation states; fresh external output paths; and no-replacement installation semantics. Recheck all execution-relevant inputs before and after the bounded verification. Save complete commands, attempted and observed process starts, outputs, artifacts, cleanup outcomes, and any unknown operations.

## Preserve method identity and every predicate

Before implementation, enumerate the actual default test-discovery inventory at the chosen source revision. Create a machine-readable mapping from every original method ID and assertion to its proposed operational location. Include imported helpers and transitive predicates, not only the visible `assert` lines. Record the original and proposed source hashes and a reviewed diff explaining each change.

The following source-derived map is the starting point; it is not a completed transitive audit:

| Original element | Required preservation in any operational design |
| --- | --- |
| `ReadbackCPUControls` availability gate and `setUpClass` | Preserve the requirement for qualified runtime, dependencies and host inputs. An unavailable or unqualified selected operational environment must fail preparation visibly; it cannot become a successful skip. Use a new explicit setup interface only after adoption. Preserve fresh manifest/output paths, absent unused native-schedule path, and manifest verification. |
| `test_q01_actual_synthetic_meshes_load_in_both_libraries` | Execute the same Q01 synthetic artifact and reference audit through both retained readers. Preserve every `check_case` assertion and exact positive outcome. |
| `test_q03_actual_synthetic_rotations_load_in_both_libraries` | Execute the same Q03 synthetic rotations and reference audit through both retained readers. Preserve every `check_case` assertion and exact positive outcome. |
| `test_three_rejects_changed_synthetic_reference` | Retain the exact Q01 negative mutation: add `0.001` to the designated left/base world-matrix translation. Require the corresponding rejection and `matrix_0_3` finding; do not change fixture bytes or tolerance to accommodate a new runtime. |
| Shared `check_case` predicates | Preserve successful independent synthetic reference audit, artifact/reference/manifest hash binding, exactly one observed checker start per case, successful cleanup, closed handles, actual reader version assertions, 14 nodes and 12 meshes, the required positive/negative result, and input preservation. Retain diagnostic and failure paths, including the negative process-stop handling. |
| `format_check` manifest and reader predicates | Preserve the complete dependency inventory, source ownership, executable-in-closure requirement, aliases and file binding, profile/scope, retained library versions, options, slot mapping and output paths. Any runtime-version/path adaptation must occur through a newly adopted entry point or explicit versioned branch; old guards must retain their historical meaning. |
| Readback numerical and resource limits | Preserve the original position and matrix tolerances, expected static scene/animation characteristics, `--no-addons`, bounded memory, 30,000-ms outer readback budget, 28,000-ms child allowance and 2,000-ms cleanup allowance, output/log limits, and rejection of external resources. Preserve the separate 100,000-operation/30,000-ms source budgets. |
| `ReadbackCoordinatorSeams` methods | Keep the existing write-failure, supervisor-cleanup, remaining-outer-alarm and uncertain-marker-removal controls in the actual default inventory. Their outcomes are independent requirements; do not replace them with a host smoke test. |

A future operational revision can be considered only if the review shows how the original method identities and full predicates execute under the adopted provider. Merely adding differently named passing cases while the original hardcoded cases skip or fail is insufficient. Renaming, moving, splitting, sharing or versioning setup must have an explicit one-to-one or fully explained mapping; aggregate counts cannot substitute for per-method outcomes.

The design must also state how historical exact replay is reported separately. Preserving its old files or evidence does not establish a new historical execution. If the proposed operational design cannot preserve the required predicates or cannot truthfully reconcile the original default-discovery methods, stop at that unresolved design blocker.

## Required refusal and change controls

Before qualifying the positive host, predeclare negative controls for the new execution boundary:

- Wrong executable digest, size, mode, selected version, path/alias or source binding must refuse before checker execution.
- Missing or changed shared-library/loader inputs, incomplete/extra/changed dependency files, symlink surprises, and a manifest belonging to another source checkout must refuse explicitly.
- Inputs changed between preparation and execution must invalidate qualification. Missing prerequisites must not produce a green skipped cohort.
- Preserve the actual changed-reference negative case and all existing coordinator/lifecycle controls, including timeout, output limits and cleanup consequences where already required by their source contracts.
- An uncompleted or unknown child/process outcome must remain failed, interrupted or unknown as observed. Retrying requires an explicitly recorded new attempt; earlier results remain intact.

Bind each negative input and expected refusal before execution. Independent review must examine complete actual outputs and process/artifact identities. A schema-valid manifest or a matching version string is insufficient.

## Gates before a full default routine

1. Adopt the separately versioned operational decision after independent source and predicate review. It must explicitly reconcile the hardcoded historical methods and preserve the original historical records; this proposal alone does not do so.
2. Implement only that reviewed design in a newly identified candidate. Freeze inputs and expectations, then complete its required positive and refusal controls with zero hidden skips/xfails or replacement-only acceptance. Review all changed execution boundaries and the complete method/predicate map independently.
3. Verify the entire default-discovery inventory at the actual candidate. Every required existing method must have a mapped execution and outcome. Do not exclude files/classes, reduce discovery, substitute totals, or call a supplemental suite the default routine.
4. Only then select a separate bounded full-routine phase. Run the required `tools/check_local.py` invocation with declared environment and justified outer timeout, preserving all required stages and per-source budgets. Preserve the original failures and any new failure. Independent R03 acceptance must evaluate the complete result and remaining limitations.

R04 integration and R05 final parent closure retain their separate gates. An approved current-host design, successful prerequisite preparation, or a focused cohort result does not complete them.

## Sources inspected

Source baseline: `6d4324e8fd835351da2db165bf0907a3bf1916bc`, tree `48b90d77723a40fa8b5b591203bb10b048e5ea6f`.

- `docs/engineering/readback-prerequisites-c225/README.md`, `PREPARATION.md`, `restore_readback_prerequisites.py`, `REVIEW.md`, and historical approval/outcome evidence.
- Runtime portion of `docs/engineering/static-tray-qualification-c199/EXTERNAL-INPUTS.json`.
- Full `tests/test_static_tray_readback_v01.py`; manifest construction/verification and constants in `prototypes/static_tray_v01/format_check.py`.
- C271 P03 `PHASE-OUTCOME.json`, `EXECUTION-CHECKS.json`, `FINAL-ACCEPTANCE.json` and `RESULTS.md`.
- Current P04 `session/PHASE.json`, the independent `INITIAL-REQUIREMENTS.json`, and Director's static `runtime-observation/CURRENT-BINDINGS.json`.

This document reports no test run, runtime installation, portability implementation, new acceptance, integration or parent completion.
