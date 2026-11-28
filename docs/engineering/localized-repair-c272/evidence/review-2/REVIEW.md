# C272 independent review 2 (REQ-026, TASK-032 re-review)

## Reviewer, candidate and scope

- **Reviewer.** The same Claude Code subagent (model Opus 5.5) that wrote review 1
  (`review-1/REVIEW.md`). It was launched for this review by Director `c272-4d816b3c0468`. It
  did not author the changes, and it changed no repository file or Git state.
- **Candidate reviewed.** `48d35db9ff8bf42f0c5b37983661c50244b231dc` on
  `work/c272-edit-rebuild-qualification` (worktree `OntoKin-worktrees/c272`). Since review 1's
  `d275baa4`, the branch has three commits:
  - `3c206ac7`: code fixes;
  - `bfa9e8ff`: evidence and records;
  - `48d35db9`: candidate checks.

  The tracked working tree was clean, at that HEAD, at the start and end of the review.
- **Date.** 2026-11-28 UTC (finished 06:54Z).
- **Criteria.**
  - The resolution of review 1's mandatory findings M1 to M3.
  - The disposition of its optional findings O1 to O12.
  - Whether the changes introduced any new problem. The criteria otherwise match review 1: the TRD requirements, SCORING.md and the raw `.ok` source.

## Commands run and outcomes

Outputs are in this directory; probes and their outputs are in `probes/`.

| # | Command | Outcome |
| --- | --- | --- |
| 1 | `git log d275baa4..HEAD`; `git diff d275baa4 48d35db9` (code and records); `git diff --stat 3c206ac7 48d35db9 -- '*.py' '*.mjs' ontokin tools tests pyproject.toml` | Code changed only in `semantic_observe.py`, `score.py`, `controls.py`, `rebuild.py` and two test files. `3c206ac7..48d35db9` changes no code |
| 2 | `export TMPDIR=<resolved>; .venv/bin/python docs/engineering/localized-repair-c272/qualify.py --output-dir …/review-2/qualify-run` (`qualify-run.log`) | exit 0 in 184.8 s; V1, V2 and N1 passed; 24 of 24 controls; revision `48d35db9` |
| 3 | `probes/compare_runs.py` | `delivered-3` and `replay-3` `RESULTS.json` are equal. The review-2 run differs only in the wheel SHA-256 and `SOURCE_DATE_EPOCH`, which a different commit is expected to change. Every `score.json`, `semantic-final.json` and `rebuild.json` is equal apart from those volatile fields. All 34 retained record files and all 14 rebuilt outputs are byte-identical across the three runs, and the GLBs equal those of the d10c9f62 runs |
| 4 | `probes/compare_committed.py` | 101 of 101 files in `evidence/runs/delivered-3c206ac7` and 1 of 1 in `replay-3c206ac7` are byte-identical to the local `delivered-3` and `replay-3` |
| 5 | `probes/manifest_check.py`: `MANIFEST.json` against the tree of `48d35db9` | 223 listed, all committed with matching size and SHA-256. No tracked evidence file is unlisted. Both `.log` files are in the index (`git ls-files -s`) |
| 6 | `probes/probe_sign.py`, against the candidate's code and against `d275baa4`'s `semantic_observe`, `score` and `controls` (taken with `git show`, kept in `probes/old/`) | See M2 |
| 7 | `probes/test_without_fix.py`: the new `test_negated_stored_rotations_are_the_same_motion`, run with the old and the new `semantic_observe` | With the old code it fails, with `('cross-check', 'decoded angles stay within…')`; with the new code it passes |
| 8 | `cd docs/engineering/localized-repair-c272 && ../../../.venv/bin/python -B -m unittest test_observe test_semantic_observe test_score test_runner` | 27 tests, OK |
| 9 | `probes/probe_imports.py` on the review-2 run | The evaluator modules import only the standard library. V1, V2 and N1 are accepted with every `ontokin` import blocked; 0 product modules loaded |
| 10 | `probes/probe_poses.py` on the review-2 run | The seven hand-computed poses of review 1 still agree. C255 `pose_for` differs by 0 (5.6e-17 for one); the delivered GLB by at most 4.8e-8 m |
| 11 | `git diff --name-only 38ee8d18 48d35db9 -- ontokin <C253, C255–C268, C210 proof, keyed-rack fixture> pyproject.toml tests tools examples .gitignore` | Empty |
| 12 | `cmp` of committed `gltf-validation/*` and `playback/capture-3c206ac7.json` with `checks/gltf-delivered-3` and `checks/playback-delivered-3`; `shasum` of the frames; viewed `playback-paused.png` | Identical. The five stepped frames are byte-identical to the `delivered-2` frames. The paused frame shows 0.650 s with `first` at Y 0.130, as PLAYBACK.md states. Six files and two distinct GLBs; 0 errors and 0 warnings; 126 of 126 Three.js comparisons |
| 13 | `diff` of `evidence/review-1/{REVIEW,ASSIGNMENT}.md` with the originals | REVIEW.md is unchanged. ASSIGNMENT.md differs only by replacing `<parent>` with `<parent>` |

**Side effect.** As in review 1, the run in command 2 made the package-smoke setup tool write an
ignored report, `build/local-environment/run-20261128T064940339207Z.json`, into the
worktree. No tracked file changed.

## Resolution of review 1's findings

### Mandatory

**M1: resolved.**
- `gltf-validation/verify_gltf-truncated.log` and `runs/earlier-f0e4148f/replay-refused.log` are now committed (force-added).
- The manifest matches the committed tree exactly, with 223 of 223 files.

**M2: resolved in the evaluator.** The control finding is recorded below as N1 (optional).
- `semantic_observe.py` now negates the relative quaternion when w < 0, before `atan2`. With w ≥ 0, θ lies in [−π, π]. A wrong direction or wrong magnitude is still detected, because only q and −q are identified.
- Probe 6 on the candidate's code accepts every sign variant end to end: C256 valid, C255 `componentPass`, locality passed, 0 failed cross-checks. The variants are:
  - the selected blade negated;
  - the selected finger (the hinge's parent) negated;
  - an unselected blade negated;
  - `first` negated;
  - all 18 nodes negated.
- On `d275baa4`'s code, the blade and finger variants are still rejected, as review 1 found.
- The new unit test discriminates: it fails without the fix and passes with it (command 7).

**M3: resolved.**
- Every per-property row now carries `observed`, `origin`, `expected`, `derivation` and `outcome`. That covers the 74 semantic rows (4 field rows, 18 objects, 34 sites, 8 follows, 8 hinges and 2 actions) and the 18 new per-object geometry rows.
- The origins are concrete pointers to the actual GLB or sidecar, or C256 accessor locations. No row has an empty origin, and no pointer contains `*` or `,`.
- The eight aggregate check rows carry `origin` and `derivation`. Pose values have their own 126-row table.
- The observed values come only from the observation. Expected values are used only for the row and are never written into the C255 observation.
- REPORT's REQ-016 row now describes this table correctly.

### Optional

All of review 1's optional findings are resolved or disclosed:
- **O1, replay revision.** The replay is at `3c206ac7`. REPORT says "met at the code revision `3c206ac7`". `3c206ac7..48d35db9` changes no code, and command 2 reproduced the results at `48d35db9`.
- **O2, sidecar origin.** REPORT, COVERAGE.md and README now state that the harness builds the sidecar.
- **O3, controls.** E04d now uses the delivered GLB with a sidecar that claims the start program, and `STALE_SIDECAR` fires. Control reasons now carry observer and G3 fault codes.
- **O4, O5, reader rules.** The tween value and event time literals, site `kind` and `axisFrame` are disclosed and listed as derived (60 derived entries). The pointers are concrete.
- **O6, provenance.** The circular provenance fields are stated in REPORT and in the rows' origin text.
- **O7, locality counts.** They are now measured (16 and 11), and a test changes them to 15 and 10.
- **O8, rebuild tools.** The interpreter binary's SHA-256 is recorded. `setuptools>=77` remains unpinned but is disclosed with its resolved version.
- **O9, readiness wording.** It now reads "subject to the independent review".
- **O10, GLB and C210 citations.**
  - The six files are named as two distinct GLBs.
  - The C210 citation now gives `bb7e831a`, CPython 3.12.14 and Linux x86-64, which `proof.json` confirms.
- **O11, output inside the checkout.** It is disclosed.
- **O12, the crash without a traceback.** It is disclosed in CONTROLS.md.

## New findings

No new mandatory finding.

### Optional

**N1. P03 would also have passed before the M2 fix.**
- P03 negates the stored rotations of all 18 nodes. A hinge's relative quaternion is conj(−p)·(−c) = conj(p)·c, so the signs cancel and the defect never shows.
- Executed: `d275baa4`'s code accepts P03's exact input (probe 6, old code, "all 18 nodes").
- P03 is still a true end-to-end positive control, and its stated claim is accurate. The discriminating evidence for the fix is the new unit test, which covers only part of the motion.
- CONTROLS.md's "The fix … P03 now negates the stored keyframes" can be read as if P03 demonstrated the fix.
- Suggested change: negate only the blades, or one node of each hinge pair, in P03 so that the end-to-end control would have caught M2. Alternatively, state that the unit test is the discriminating check.

**N2. A stale row count in REPORT.** REPORT line 35 still says "Each per-property table has
82 rows". The tables now have 100: 74 semantic rows, 18 per-object geometry rows and 8 check
rows.

**N3. The README table is broken.** The paragraph about the sidecar and `build/local-environment`
was inserted inside the "What a run writes" table. The four rows after it (`score.json`,
`rebuild.json`, `semantic-final.json` and `controls/`) lose their header and no longer render
as a table. Move the paragraph below the table.

**N4. REPORT cites a review record that does not exist yet.** The REQ-026 row cites
`evidence/review-2/REVIEW.md`, which is absent at `48d35db9`. It needs adding (sanitized, like
review 1) when this review is retained.

**N5. The check records lost their command strings.**
- The new entries in `CHECKS.json` (`scope_checks.qualification`) and `CANDIDATE-CHECKS.json` (documentation verifier, workflow check and the `bfa9e8ff` observer regression) no longer carry the commands that the earlier entries had.
- The regression record keeps its per-group commands, and README documents the qualification command.
- `CANDIDATE-CHECKS.json`'s `routine_driver_reuse` still argues only up to `f955dafd`. `CHECKS.json`'s `routine_driver_applies_to` carries the correct argument for `3c206ac7`. I verified it: the driver's steps read nothing in the scope directory except through the documents step, which was rerun at `bfa9e8ff`.

## Verdict

**accept.**
- M1, M2 and M3 are resolved and verified by execution. The candidate passes the qualification at its exact revision, reproducing the delivered and replay evidence byte for byte.
- The optional findings N1 to N5 are records-level or control-strength improvements. N2 to N4 are cheap and are recommended before integration. None blocks it.
