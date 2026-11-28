# Bounded worker assignment: independent review of the C272 candidate

## Identity and objective

- Task and requirement IDs: C272; REQ-026 (independent review), covering REQ-006, REQ-010, REQ-012 to REQ-022, REQ-028, REQ-029 and REQ-031 to REQ-033 of TRD-20261127-7B80B30A.
- Assigning Director and actual worker identity: Director `c272-4d816b3c0468`. The worker is a separate Claude Code subagent with fresh context; its identity is the subagent the Director launches.
- Role: Reviewer under ROLE.md. Independently challenge the candidate's acceptance claims and record findings. Review neither edits nor merges.
- One bounded objective: decide whether the exact candidate commit d275baa460c50f07b3f4917af0f50da04f332dc3 and its evidence meet the requirements named above. In particular, check whether the evaluator's formulas and fault controls are right against the raw `.ok` source and the equations of the C253 scoring specification, not only whether the code runs.
- Completion criteria and stopping condition: a written review with a verdict (`accept`, or `changes required` with numbered mandatory findings) and the separately labelled optional observations. Stop after writing it.
- Context mode: fresh; no conversation history is inherited.
- Applicable current user instructions: the owner approved PLAN-20261128-AC17E7E0 and instructed its execution. For the delivered-semantic reader, the owner chose option A of GAPS.md. A self-review does not meet REQ-026.
- Governing instructions to read: AGENTS.md, ROLE.md, docs/workflow/PROTOCOL.md section 5, and docs/workflow/tasks/C272/REQUIREMENTS.md. In TRDs/trd_c253-fresh-edit-animation-and-clean-rebuild-qualification_2026-11-27.md, read the requirements named above.

## Inputs and ownership

- Repository: worktree <parent>/OntoKin-worktrees/c272 (branch `work/c272-edit-rebuild-qualification`). The base is main `38ee8d18a6cd67245acf8b21d755e979b84153c1`.
- Candidate commit: d275baa460c50f07b3f4917af0f50da04f332dc3.
- Allowed reads: the whole repository; the qualification output directories <parent>/OntoKin-local/c272/runs/delivered-2 and <parent>/OntoKin-local/c272/runs/replay-2; the validation directory <parent>/OntoKin-local/c272/checks/gltf-delivered-2; the playback directory <parent>/OntoKin-local/c272/checks/playback-delivered-2.
- Exclusive allowed writes: <parent>/OntoKin-local/c272/review-1, outside the checkout. Write nothing inside any checkout and change no file of the repository.
- Protected: everything in the repository, the main checkout, Git refs, GitHub state, CURRENT, STATUS.
- Available tools: reading files, running read-only commands, and running the scope's tests and its qualification command into new directories under <parent>/OntoKin-local/c272/review-1.

## What to check

1. **Oracle independence.** `docs/engineering/localized-repair-c272/{observe,semantic_observe,score,controls,glb_edit,validate_glbs}.py` import no OntoKin product module. Only `runner.py`, `rebuild_entry.py` and `qualify.py` (through `runner`) drive the product.
2. **Expected values.** C255's `semantic_state`, `pose_for` and `expected_state` (unchanged) agree with the raw `.ok` source in `docs/engineering/semantic-export-c210/evidence/proof/` and with SCORING.md's equations. Compute at least three poses by hand. Confirm that no tolerance is supplied by C272 code.
3. **Observation honesty.**
   - No field of the C255 observation is filled from an expected value. `score.localize_semantic` uses expected records only to localize faults for reporting, and the verdict is C255's `evaluate` on the fully observed record; check that this holds.
   - Check that `semantic_observe.py` reads actual bytes with pointers, and that its source-literal reads and rule-derived masses are as GAPS.md option A states.
4. **Accepted-state record.** `runner.py` derives `authority.json` from the service's responses and the retrieved bytes. Check the N1 diagnostic translation, the accepted-revision identity and the `invalidEverAccepted` derivation, and state their limits.
5. **Rebuild.** `rebuild.py` and `rebuild_entry.py` build the wheel from the committed revision and run in an empty workspace with `-I`. Check that nothing of a checkout is imported and that the bytes are compared without exemptions.
6. **Controls.** Each control in `controls.py` presents the fault it claims and is rejected for a relevant reason, and its clean twin is accepted. Check CONTROLS.md's mapping of SCORING's listed faults, including the open items it names.
7. **Evidence.** <parent>/OntoKin-local/c272/runs/delivered-2's RESULTS.json and <parent>/OntoKin-local/c272/runs/replay-2's agree. Every committed evidence file in `docs/engineering/localized-repair-c272/evidence/` matches its manifest. Check REPORT.md's requirement states and readiness table against the evidence, and that it makes no excluded claim (REQ-029, REQ-031).
8. **Preservation.** The C253, C255 to C268, C210-proof and keyed-rack fixture files are byte-identical to main `38ee8d18`, and nothing under `ontokin/` changed (`git diff --stat 38ee8d18 d275baa460c50f07b3f4917af0f50da04f332dc3`).

## Worker return

Write <parent>/OntoKin-local/c272/review-1/REVIEW.md with:
- the reviewer, the commit reviewed, the criteria applied and the commands run;
- the findings, numbered as mandatory or optional;
- the verdict.

Return at most about 250 words: the verdict, the mandatory findings, and what was executed.
