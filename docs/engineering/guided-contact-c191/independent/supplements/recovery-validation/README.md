# Independent recovery review

The original semantic, checker and source freezes remain unchanged. Recovery
verified every sealed file before reading candidate outputs: 6 semantic inputs,
16 checker inputs and 62 source-freeze inputs matched their SHA-256 records.
Git history places the semantic/checker freeze at `23069a5`, source/contract
freeze at `a1cde0a`, source validator at `61d14d3` and native adapter at `270d658`.
The analytic contact expectations follow the source's 180 mm shoe face and
125 mm/s feed. This establishes traceable ordering and unchanged published
inputs; it does not independently observe the previous reviewer's private work.

The recovered `f610812` implementation passed the original checks: 32 source
cases, 7 admission checks, 5 lexical/resource checks, 34 lifecycle attempts,
8 positive and 54 negative playback controls plus 3 continuous slab controls,
and 9 fresh builds with 9 saved-scene replays. Repeated final GLBs were identical;
the renamed/reordered case retained A's canonical and final bytes. Every
reopened native sample equalled its original capture. Those records are retained
as baseline evidence, separate from the corrections below.

## Additional review findings

Source review found three gaps in enforcing existing obligations. Initial world
matrices of hidden helpers and constraints were not compared to their declared
frames. Raw GLB transverse translations and rotations could differ from the
native captures while retaining a small projection bound and a matching receipt.
Auxiliary receipt IO failures could raise after the actual transaction outcome
was already known, including after a successful commit.

The additional probes were written after inspecting the recovered candidate.
They are supplementary recovery checks, not a new claim of pre-candidate
independence. [The first manifest](manifest.json) identifies the extra native and
mapping cases. [The harness correction](harness-correction.json) preserves a
failed quaternion probe and two probes that initially reached only receipt-hash
checking. The corrected probes mutate raw data before the real projection and
therefore exercise native correspondence. All six malformed-frame/raw-pose
mutations were committed by the baseline. Missing and truncated native results
already rejected correctly.

[Four receipt probes](receipt-probes.json) require a structured return that
agrees with the sole atomic state-pointer commit. All four baseline attempts
raised an IO exception; two had already committed. Previous accepted artifact
bytes remained unchanged. The author correction is separately identified and
must pass the fresh qualification before acceptance.

## Supplementary tools

`checker/audit_recovered_batch.py` verifies complete source/dependency identity,
all 13 source/native mapping rows, exact helper/constraint frames, inactive
constraint settings, raw/native carriage pose agreement, and equality of every
reopened native sample. The rotation comparison uses 32 float32 epsilons as a
codec roundoff guard. It does not change any physical or projection tolerance.

`checker/run_lifecycle.py` retains every original failure case and adds S02–S09.
Its optional `--only` selects an explicit subset, reported as a subset. Full
qualification still requires all 19 frozen failure methods. Each isolated
baseline probe receives its own copied accepted store so an incorrectly
committed mutation cannot contaminate later probes.

`checker/run_receipt_failures.py` exercises actual transaction paths with a
supervised copying worker and controlled receipt failures. These are lifecycle
checks, not new native-solve evidence. Run it against the formal batch for the
same implementation revision. Retain the exact returned results, state changes,
stderr warnings and old-artifact inventories.

The coordinator's final checkpoint binds the corrected implementation, fresh
commands and reports, artifact hashes, compatibility checks and destination
review. These tools do not qualify unrecorded Bullet substeps, direct contact
impulses, general dynamics, a production adapter or an authoring advantage.
