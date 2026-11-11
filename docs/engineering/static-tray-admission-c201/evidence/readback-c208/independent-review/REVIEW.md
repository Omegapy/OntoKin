# C208 independent component review

Reviewer: `/root/live_state`. Implementation worker: `/root/readback_component`.

## Decision

**APPROVE_READBACK_BINDING_COMPONENT_ONLY** for exact candidate
`a645731147e4ce95ddaab8132c5a261cc3a9f44a`, tree `77679024f09a647905c2d97331fc751c5d0ce73b`.

The separately scoped `readback_binding.py` is acceptable as CPU consistency
checking between a retained C201 accepted transaction and proposed readback
observations. This decision does not approve an executable Node job, probe,
wrapper, native readiness, schedule advancement or family admission.

## Observed evidence

The independent public-API suite passed **63 methods**, with **zero
failures, errors or skips** and **zero attempted process launches**. It used
`/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3`, CPython 3.12.14 on
`Linux-6.18.57-x86_64-with-glibc2.41`. Every fixture represented native containers, receiving
observations and Node results synthetically; no external-stage process existed.
The real C201 transaction and readback APIs still performed their file, closure,
source, job and result checks.

Full results are in [candidate-1/RESULT.json](candidate-1/RESULT.json) and
[candidate-1/controls.log](candidate-1/controls.log). The review controls and
fixture builder are [independent_controls.py](independent_controls.py) and
[fixture_support.py](fixture_support.py). They do not call the new private
numerical or result validators in place of its public API. One interruption
control injects a failure at the retained-output read seam, then observes the
public API's UNKNOWN and stopped-state behavior.

The review exercised:

- All four accepted slot identities and the strictly false execution/readiness/
  admission/next-slot fields; immutable accepted pointers on success.
- Source, tree, slot, route, revision, GLB, audit, lock and job-hash mismatches;
  foreign reconstructed handles, changed source bytes, job commands and outputs.
- Missing and extra files, symbolic links, hard links, FIFOs and byte limits;
  stale log lengths, wrong commands/environments/cwd and false process records.
- Failed exits, open handles, unknown/failed cleanup, explicit UNKNOWN, interrupted
  verification and blocked retries; preservation of the partial stage record.
- Khronos wrong versions, warnings hidden behind a passing flag, inconsistent
  issue messages/counts, truncation and boolean count substitution.
- Three.js wrong inventory/version/scene/texture claims, relationship and material
  changes, boolean indices and matrices, NaN/overflow, incomplete measurements,
  contradictory local/world geometry and forged self-reported expected values.
- A within-tolerance position perturbation remains consistent with the historical
  numeric semantics; an apparently successful 29-second child is rejected instead
  of borrowing the 30-second outer budget.

## Historical preservation and scope

The read-only preservation audit passed **301 locked inputs**, **four frozen
protocol documents**, and **1,033 historical files**; these sets overlap and must
not be summed as distinct files. It also observed no shared runtime, conformance,
grammar, schema, tool or workflow changes. No C199/C200 cohort was rerun.
[candidate-1/PRESERVATION.json](candidate-1/PRESERVATION.json) retains every binding.

The candidate differs from C207 by only three additions:
`prototypes/static_tray_admission_c201/readback_binding.py`,
`tests/test_static_tray_admission_c201_readback_binding.py`, and
`docs/engineering/static-tray-admission-c201/READBACK-BINDING-C208.md`.

The full inspection inventory has 69 files. This decision
binds **66 component, dependency, test and contract files** separately
from the **3 context files** AGENTS, GOAL and STATUS. The latter record
which project instructions and state were inspected; a later verified lease or
STATUS publication is not a changed product input. Root must compare the
immutable binding set on the integrated revision before reusing these controls.

## Findings resolved before the frozen candidate

Source review of the uncommitted draft identified that the 28,000 ms child-work
limit was only echoed while the process check admitted durations up to the
30,000 ms outer ceiling. The implementer corrected it before freezing this
candidate: a passing record's entire supervisor duration must fit within 28,000
ms and its termination-cleanup duration must match the qualified success value of
zero. The independent 29-second adversarial control passes by observing rejection.
The supervisor has no separate exit timestamp; actual enforcement of the original
outer clock remains the future wrapper's responsibility.

The proposed job initially lacked explicit treatment of dependency-entry
resolution. The frozen contract now clearly states that this is not a complete
executable probe job. A future versioned contract must bind the validator entry,
Three.js entry, GLTFLoader entry and package metadata to exact reviewed paths and
bytes in the sealed closure. C205's generic `node_packages` inventory is
insufficient to choose those targets. Ambient imports and historical twelve-slot
manifest substitution remain forbidden. This gap is retained as the next task;
it is not covered by this approval.

## Limits and next action

Self-consistent synthetic observations intentionally pass only the binding
consistency boundary. This module cannot authenticate that the claimed Node,
Khronos or Three.js execution occurred. The fixtures prove that limitation as
well as checking the always-false authority flags. The future trusted wrapper
and coordinator must establish real process provenance, complete dependency
sealing, deadlines, durable one-use reservations, slot/control order and cleanup.

The next coherent task is the separately reviewed named-package resolution and
versioned executable job contract, using CPU-only controls. The eventual wrapper
and Node probe, complete coordinator, trusted bootstrap/current-host closure,
independent native readiness, sole bounded four/four/four invocation, image
reviews and final admission remain pending. The historical full regression stays
**FAILED** (4,239 distinct passing methods and 13 torque-read methods not run after
the unchanged 30,000 ms setup timeout). This review claims no full-regression,
hosted, destination or comparative-authoring pass.

## Review harness setup receipts

An initial fixture-shape inspection omitted `-B`; Python generated ignored cache
files and the historical independent reader correctly refused them. A second
`-B` inspection still encountered those existing caches. The reviewer identified
and removed only the 18 generated `.pyc` files from that exact one-second creation
window, recording their paths/hashes in
[initial-import-cache-cleanup.json](initial-import-cache-cleanup.json). No tracked
source was modified. Subsequent fixture inspection and all 63 formal controls used
`python3 -B`. The original setup failure is retained in
[fixture-inspection-first-attempt.txt](fixture-inspection-first-attempt.txt); it is
not represented as a product test result.
