# C192 recovery protocol and source review

## Decision and scope

**APPROVE integration of the recovered experiment evidence. No delivery is
approved.** No protocol or source defect in the reviewed candidate requires a
new author trial, a changed gate, or a changed physical result. All six retained
participant builds remain rejected. Publication closure and the outgoing
handoff must still identify the actual merge and retained histories.

The reviewed candidate is `0dd0e1fb44abb73d2fef65bc3a318c54ca2ea13f`, against
merged C191 `afae5f59558bc90200691f6727709124d2e119ea`. This reviewer did not
author either original route or participate in the earlier cross-reviews. The
review used a separate branch and worktree. The prior workspace was read only.
No native simulation, receiving application, original participant trial, C193
repair, remote write, or additional delegation was performed.

[receipt.json](receipt.json) contains the independent checks, exact hashes,
timestamps, command arguments and results. [review_protocol.py](review_protocol.py)
reproduces those checks. [findings.json](findings.json) records the review's
interpretation, publication obligations and evidence limits;
[verification.json](verification.json) records execution and documentation checks.

## Freeze, equivalent preparation and authorship evidence

The manifest timestamp is **14:52:35.280298 UTC**. Git commit
`9d1118f63195c8458aa804f2a99922cc780365aa` records that freeze at **14:52:45 UTC**.
Dispatch preparation is recorded at **14:53:03.090593 UTC**; the first participant
observations are **14:54:02 UTC** for `.ok` and **14:54:15 UTC** for Python.
All **116 frozen files** match both the freeze commit and the recovered candidate,
including size and SHA-256. This supports a pre-dispatch source/protocol freeze.

The original Git objects, inspected in the old repository, independently show
both first-submission commits have the freeze commit as their direct parent.
Each reuse commit directly follows its route's first submission. The participant
histories change only their assigned participant directory. All **37 `.ok` and
26 Python first-phase files** remain byte-identical in the reuse commits and the
recovered candidate.

The saved dispatch record requests exactly two fresh default agents with
`fork_turns="none"`. Participant records attest to those settings, no further
delegation and no human intervention. **No raw launcher transcript or provider
telemetry is retained.** Git ancestry proves the starting source state; it does
not independently prove empty conversational histories, exact model identity,
or the absence of other provider activity. Those claims must retain their
recorded-attestation status. The existing public/shared-environment limitation
is appropriate.

The two prepared baseline builds and their reopens completed before the freeze.
Both baseline commands succeeded. Their canonical inputs, native transforms,
native trace CSV, raw GLBs and final GLBs match exactly. Each saved reopen matches
all 481 baseline samples. The direct route's starter is a docstring plus one
literal `DESIGN` dictionary; the runner sends this data to the retained native
constructor without parsing `.ok`. That runner is explicitly reusable setup.

For all six participant builds, each of the **11 retained implementation files**
matches the frozen C191 implementation. The backend bytes match, and the direct
runner copies match the frozen C192 runner. Both routes retain requests and host
ceilings of **1,000,000 operations and 80,000 ms**. A whole-tree comparison finds
no changes outside C192 and the authorized README/STATUS scope. Historical
runtime, tests, contracts, checkers, ordinary budgets and workflows are unchanged.

## Localized edits, reuse and failure preservation

Exact byte comparisons establish the following changes in each authoring route:

| Phase | Only changed source value | Before | After |
| --- | --- | ---: | ---: |
| First edit | Left-stop X coordinate | 380 mm | 362.5 mm |
| Reuse | Same coordinate | 362.5 mm | 372.5 mm |

Python abstract-syntax-tree inspection additionally verifies one literal
dictionary assignment and no source-level calls. The retained starter copies,
editable sources, submitted-source snapshots and archived artifact sources all
agree. Each canonical input equals the original design with only that coordinate
changed. First-score hashes match the retained first sources. The coordinator
score at **14:58:24.794769 UTC** precedes both recorded reuse starts.

Across each target's two routes, canonical inputs, native transforms, native
trace CSV and raw/final GLBs match exactly. The first-source regeneration also
reproduces those first-target bytes. This establishes literal-source reuse and
reproducibility of the same failures. It does not establish successful delivered
reuse, general classes, parameters or libraries.

Every participant delivery receipt has exit status **1**, `successful: false`
and a null accepted artifact path. All six original saved delivery receipts
match the archive. The final evidence archive verifies **801 manifest entries**
plus its manifest. The separate first-phase archive verifies **86 files** against
its external manifest; all **78 participant files** in that earlier archive are
unchanged in the final archive. Rejected outputs and their original first-phase
receipts have survived the recovery.

The consolidated results retain zero accepted first-edit deliveries and zero
accepted second-target deliveries. They distinguish passing final playback from
the failed 0.2 mm mapping gate. The sample maxima, approximately **0.244638 and
0.292416 mm**, already exceed the gate; the larger continuous bounds cannot be
made acceptable by appearance or by changing how a conservative bound is
reported. Fresh numerical rescoring and receiving execution are outside this
protocol review; the existing complementary reviews identify their own scopes.

## Time, attempts and interpretation

Independent timestamp subtraction reproduces all four reported phase durations
to less than 0.00001 seconds:

| Route | First phase | Reuse phase | Recorded native builds | Formal submissions |
| --- | ---: | ---: | ---: | ---: |
| `.ok` | 302.047489 s | 229.609662 s | 1 + 2 | 1 per phase |
| Python | 283.171448 s | 218.203328 s | 1 + 2 | 1 per phase |

The durations are within the frozen 20-minute allowance, and counts are within
the three-submission/six-build limits. Both routes record zero repair rounds.
The original saved run directory contains exactly the six archived delivery
receipts. That checks recorded attempts; it is not an independent provider audit.

Start times are first observations after dispatch, not provider launch times.
The `.ok` endpoint is commit confirmation; Python's endpoint is submission
readiness after commit. Reporting and inspection are included. The optional
`.ok` reopen, one unsuccessful read-only search per route, and two Python
transport failures before process creation are disclosed. No authoring-only
speed comparison is supported.

Provider tokens, cost, exact model snapshot and hidden internal turns remain
null/unavailable. Reusable C191 preparation and C192 starter/runner/control work
are separated from participant effort. Total setup time is explicitly incomplete.
The narrative correctly declines to infer comparative advantage or broad
reliability from this public pair.

## Publication closure and next task

At the reviewed candidate, STATUS contains the prior conditional lease/merge
wording. `NEXT-TASK.md` names outgoing `CHECKPOINT-C192.json` and
`README-START-HERE.md`, which are not files in that candidate tree. The final
narrative review also explicitly says it does not establish a merge. These are
**unfinished publication steps**, not evidence that C192 was already integrated.
The integrator must publish the actual observed main/PR/lease result, run the
applicable resulting-main checks, and include the named files in the handoff.

The four original participant commits were initially absent from the restored
repository's object database, although their source/receipt copies were present.
All four remain recoverable in the read-only old repository and were inspected
here. The integrator has undertaken to retain them under checkpoint references
in the outgoing Git bundle. Verify that retention when sealing the package;
this review does not claim it was already completed.

The proposed C193 task is appropriately bounded: diagnose the shared guide and
mapping residual, preserve the failure witnesses and original tolerances, and
use a separately versioned construction/mapping decision for any change. It
keeps solver contact, source authority, two 1 kg mass owners, native X samples
and times, and independent saved-scene and receiving checks. Capture-frame
alignment is correctly described as a hypothesis lead. C193 must follow actual
C192 integration; no C193 work was performed in this review.

The inherited legacy driver remains **FAILED**, with 4,239 passing methods and
thirteen torque artifact-read methods not run after the original setup deadline.
This evidence-only recovery neither repeats nor relabels that gate. The existing
external-role, compatibility, general-contact, live-physics and full-GOAL limits
remain open.

One preliminary reviewer inventory command assumed both archives had an internal
manifest. It exited with `KeyError` on the first-phase archive. Its manifest is
the retained `evidence/phase1-archive.json`; using that documented external
inventory passes all checks. The reviewer error is recorded in `findings.json`
and changes no source, archive or acceptance result.
