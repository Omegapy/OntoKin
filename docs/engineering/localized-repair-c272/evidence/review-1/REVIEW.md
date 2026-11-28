# C272 independent review (REQ-026, TASK-032)

## Reviewer, candidate and criteria

- **Reviewer.** A Claude Code subagent (model Opus 5.5) with fresh context, launched by Director
  `c272-4d816b3c0468` for this review only. It inherited no conversation history, wrote none of
  the candidate, and changed no repository file. This is not a self-review.
- **Candidate reviewed.** Commit `d275baa460c50f07b3f4917af0f50da04f332dc3` (tree
  `a13344e9212f7209fe710fc008a0057939418350`) on `work/c272-edit-rebuild-qualification`, in the
  worktree `OntoKin-worktrees/c272`; base main `38ee8d18a6cd67245acf8b21d755e979b84153c1`
  (confirmed as the merge base). The working tree was clean at the start and end of the review.
- **Date.** 2026-11-28 UTC (review finished 06:33Z).
- **Criteria applied.**
  - The eight checks of `ASSIGNMENT.md`.
  - REQ-006, REQ-010, REQ-012 to REQ-022, REQ-028, REQ-029 and REQ-031 to REQ-033 of
    TRD-20261127-7B80B30A revision 3. Its SHA-256 `9102a137…7222db` matches in both the main
    checkout and the worktree.
  - The equations, tolerances and required controls of `docs/engineering/localized-repair-c253/SCORING.md`.
  - The raw source `before.main.ok`, `after.main.ok` and `hinges.ok` in
    `docs/engineering/semantic-export-c210/evidence/proof/`, with SHA-256 values equal to the
    TRD's.
  - OK-LANG-001's tween rule (line 520: `q = q_start + (target - q_start) × local_elapsed / duration`).
  - Formulas and controls were reviewed from the source and the equations, and then executed.

## Commands run and outcomes

All output is in this directory. Probe scripts and their outputs are in `probes/`. The
evaluator side was always run with `-I -B` and `sys.dont_write_bytecode`, so no bytecode
was written into the checkout.

| # | Command (from the worktree unless stated) | Outcome |
| --- | --- | --- |
| 1 | `git rev-parse HEAD`, `git status --short --ignored`, `git log`, `git merge-base 38ee8d18 d275baa4` | HEAD `d275baa4…`; clean; merge base `38ee8d18…` |
| 2 | `export TMPDIR="$(cd "${TMPDIR:-/tmp}" && pwd -P)"; .venv/bin/python docs/engineering/localized-repair-c272/qualify.py --output-dir …/review-1/qualify-run` (log: `qualify-run.log`) | exit 0 in 197.2 s; V1, V2 and N1 passed; 24 of 24 controls passed; `RESULTS.json` revision `d275baa4…` |
| 3 | `probes/compare_runs.py`: delivered-2 compared with replay-2 and with this review's run | delivered-2 and replay-2 `RESULTS.json` are equal apart from timing. The review run at `d275baa4` differs only in the wheel SHA-256 and `SOURCE_DATE_EPOCH`, which a different commit is expected to change. All 34 retained record files and all 14 rebuilt outputs are byte-identical across the three runs |
| 4 | `probes/compare_committed.py`: committed `evidence/runs/*-d10c9f62` compared with local delivered-2 and replay-2 | 93 of 93 committed run files, plus the 8 control files, are byte-identical to the local runs |
| 5 | `probes/manifest_check.py`: `MANIFEST.json` compared with the tree of `d275baa4` (`git show`, not the working tree) | 115 listed files match their size and SHA-256. **Two listed files are not in the commit** (finding M1) |
| 6 | `git diff --name-status 38ee8d18 d275baa4`; `git diff --name-only 38ee8d18 d275baa4 -- ontokin docs/engineering/localized-repair-c253 …-c255 … -c26* docs/engineering/semantic-export-c210 docs/language-design/construction-v0.1/01-keyed-rack pyproject.toml tests tools` | Only the scope's directory, `TRDs/` (DEC-004), `STATUS.md`, `CURRENT.json` and `tasks/C272/` changed. The preservation list is empty: 0 files under `ontokin/` or any frozen path |
| 7 | `git diff --stat d10c9f62 d275baa4 -- '*.py' '*.mjs' ontokin pyproject.toml tools` | Empty: the run revision and the candidate have identical code |
| 8 | `probes/probe_poses.py`: hand-derived poses compared with C255 `pose_for` and the delivered GLB | See "Hand-computed poses" |
| 9 | `probes/probe_imports.py`: an AST import listing of the C272 modules, then V1/V2/N1 judged with every `ontokin` import blocked by a meta-path hook | Evaluator modules import only the standard library and each other; all three cases are accepted with the product blocked; 0 `ontokin` modules loaded |
| 10 | `probes/probe_sign.py`: stored rotation keyframes in the V1 GLB negated, sidecar rebound, judged by `score.score_case` | **Correct, sign-equivalent bytes are rejected** (finding M2) |
| 11 | `probes/probe_controls.py`: the observer faults behind E04b and E04d | Both rejected by C256 `PROGRAM_BINDING`; G3 never runs (finding O3) |
| 12 | `cd docs/engineering/localized-repair-c272 && ../../../.venv/bin/python -B -m unittest test_observe test_semantic_observe test_score test_runner` (log: `scope-tests.log`) | 25 tests, OK |
| 13 | `cd docs/engineering/localized-repair-c255 && ../../../.venv/bin/python -B -m unittest test_oracle` (log: `c255-tests.log`) | 31 tests, OK |
| 14 | `shasum -a 256` of the six playback PNGs; `cmp` of the local and committed `capture.json`; viewed `frame-0.00s.png` and `frame-1.00s.png` | Hashes match `capture.json`; the files are identical; the frames show what PLAYBACK.md describes: the longer middle blade at 0 s, about 45° at 1 s with the rack at Y 0.200, and the right rack still |
| 15 | `shasum -a 256` of the TRD in both checkouts and of the four proof `.ok` files | All equal to the TRD's bindings |

**Side effect.** Command 2 ran `tools/bootstrap_local.py` through `rebuild.prepare`. That
tool wrote an ignored report, `build/local-environment/run-20261128T061937073045Z.json`, inside
the worktree, as the scope's own runs did before. No tracked file changed, and this review did
not delete the report (see O11).

## Hand-computed poses

Derivation from the raw source:
- `first` is placed at (−1, 0, 0) with identity rotation and moved by `move(first, vector(world, 0, 0.2 m/s, 0), 2 s)` from 0 s. Its centre is therefore (−1, 0.2t, 0).
- Each finger follows `self.frame` of its rack at `mount_offset`. `three_mounts(0.6[m])` gives Y offsets −0.6, 0 and 0.6; `second` overrides them with −1.2, −0.6, 0, 0.6 and 1.2.
- The blade's `base` site is at (−L/2, 0, 0) in the blade frame. Hinge `flex` joins the finger's `pivot` (its origin) to `blade.base` about +Z with initial angle 0.
- `bend_to(45[deg], 1[s])` is a linear tween (OK-LANG-001). It gives θ(t) = (π/4)·min(t, 1). The blade centre is then the finger centre + (L cosθ/2, L sinθ/2, 0), with rotation (cos θ/2, 0, 0, sin θ/2).
- Unselected blades have L = 0.6 (`finger_length`) and θ = 0.

| Case, object, time | Hand result | C255 `pose_for` difference | Delivered GLB difference |
| --- | --- | --- | --- |
| V1 (L = 0.75), selected blade, 0.5 s | θ = π/8; cos θ = 0.923880, sin θ = 0.382683. x = −1 + 0.75·0.923880/2 = −0.653545; y = 0.1 + 0.75·0.382683/2 = 0.243506; q = (0.980785, 0, 0, 0.195090) | 0 m, 0 rad | 2.6e-8 m, 1.5e-8 rad |
| V2 (L = 0.65), selected blade, 1.5 s | θ = π/4; x = −1 + 0.65·0.707107/2 = −0.770190; y = 0.3 + 0.229810 = 0.529810; q = (0.923880, 0, 0, 0.382683) | 0 m, 0 rad | 9.5e-9 m, 1.0e-8 rad |
| V1, `first.fingers["upper"].blade`, 2 s | (−1 + 0.3, 0.6 + 0.4, 0) = (−0.7, 1.0, 0); identity | 0 | 1.2e-8 m, 0 rad |
| V2, `second.fingers["bottom"]`, 0.75 s | (1, −1.2, 0); identity | 0 | 4.8e-8 m (binary32 of 1.2) |
| N1, `first.fingers["lower"]`, 1 s | (−1, −0.4, 0); identity | 5.6e-17 m | 6.0e-9 m |
| V1, `first`, 0.25 s | (−1, 0.05, 0); identity | 0 | 7.5e-10 m |
| V1, selected blade, 0 s | (−0.625, 0, 0); identity | 0 | 0 |

The 0.5 s result also equals the blade position that the viewer recorded in `capture.json`:
(−0.6535452, 0.2435063, 0).

## Results by check

1. **Oracle independence: holds.**
   - `observe`, `semantic_observe`, `score`, `controls`, `glb_edit` and `validate_glbs` import only the standard library and each other.
   - The observers loaded through `observe.pinned` (C255, C256, C257, C258 and C267 with its C261, C265 and C266 dependencies) are standard-library only, and each is loaded by SHA-256 pin.
   - With every `ontokin` import blocked, all three cases are still judged and accepted.
   - Only `runner.py` and `rebuild_entry.py` import the product.

2. **Expected values: hold.**
   - C255's `semantic_state`, `pose_for` and `expected_state` (unchanged; pinned `b7275bd4…`) agree with the raw source and with SCORING:
     - 18 objects;
     - 34 sites: 8 pivots, 8 bases at −L/2 and 18 system origins;
     - 8 follows with the offsets above and 8 hinges about +Z with limits ±π/4 and initial angle 0;
     - rack boxes (0.1, 1.8, 0.1) and (0.1, 3.0, 0.1), blades (L, 0.08, 0.08) and spheres of radius 0.06;
     - the tween of 45 deg in 1 s and the move of (0, 0.2, 0) m/s in `world` for 2 s;
     - one `sequence` block at 0 s; zero gravity in `world`; duration 2 s.
   - The seven poses above agree.
   - C255's constants equal SCORING's (1e-12 m; 0.001 m, 0.001 rad and 1e-6 s; 1e-9 m and 1e-9 rad), and no C272 code passes a tolerance to C255.
   - C272's own cross-checks reuse C255's delivery constants, apart from one stricter C272 constant (O4).

3. **Observation honesty: holds for the verdict, with limits.**
   - `score.assemble` builds the C255 observation from C256's geometry and poses, G3's semantic record and the authority record.
   - `localize_semantic` uses expected records only to build the per-row table.
   - The verdict is `ORACLE.evaluate` on the fully observed record, and the case passes only if `componentPass` and every workflow check are true.
   - No observation field is filled from an expected value.
   - The provenance row's revisions and source hashes are copied from the authority record (O6).
   - G3 reads actual bytes and records pointers. Its literal and rule-derived reads go slightly beyond GAPS.md's description (O4, O5).

4. **Accepted-state record: holds within its stated limits.**
   - `authority.json` is built from the `create`, `edit` and `artifact` responses, from `read_program`, from `accepted_revision` read after every request, and from the retrieved bytes.
   - N1's translation requires exactly one `OKL-E-UNIT` with `{"expected": "Length", "actual": "Mass"}` in phase `type`. Otherwise it refuses.
   - Limits:
     - `mechanism: compiler` is the harness's mapping rule, not a statement by the service.
     - The accepted-revision identity is `agent0.2-accepted:` plus the content-derived program revision, so it is not an acceptance-event identity.
     - `invalidEverAccepted` is sampled only at request boundaries, as `accepted-state.json` discloses, and is constant `false` for V1 and V2.
     - `boundary` is a constant written by the runner.
     - The candidate's parent is taken from the request's `expected_program_revision`.
   - None of these limits changes a verdict on the three cases.

5. **Rebuild: holds.**
   - The wheel is built from `git archive` of the committed revision.
   - It is installed alone into a fresh environment without system site-packages.
   - The entry runs as `python -I -B` in an empty workspace whose listing shows exactly `hinges.ok`, `main.ok` and `rebuild_entry.py`. Its environment is only `HOME` and `PATH`.
   - All 51 `ontokin` modules load from the install environment. Neither `sys.path` nor any import lies in a checkout.
   - The bytes are compared exactly, with no exemption, by `compare`, C255 `REBUILD_BYTES` and qualify's two-run check.
   - Tool identities are partly recorded (O8).

6. **Controls: mostly hold.**
   - Each fault control was rejected and its clean twin accepted.
   - E01, E02, E03, E04a, E04c, E05, E07a, E07b and E08 fail on reasons relevant to their faults.
   - E04b, E06a, R01 and R02 are rejected through the observers, but the retained reasons show only generic workflow-check names (O3).
   - E04d does not exercise the fault it names (O3).
   - **P03 does not show what it claims** (M2).
   - CONTROLS.md maps every fault that SCORING lists and names the open items: no end-to-end change of a global or shared default; timeout and infrastructure-incident denominators only as inert accounting; boundary controls only at record level. This satisfies REQ-019's third criterion.

7. **Evidence: partly holds.**
   - Delivered and replay `RESULTS.json` agree, and the review rerun at the exact candidate reproduces them.
   - **The manifest lists two files that the commit lacks** (M1).
   - REPORT's REQ-016 evidence does not meet that requirement's table criterion (M3).
   - The replay revision is `d10c9f62`, not the candidate (O1).
   - REPORT makes no excluded claim (no A1 completion, C260 qualification, product acceptance, authoring advantage, destination support, physics or continuous-time accuracy). Its route, executor, family and scripted-client statements are present. Minor wording points are O9 and O10.

8. **Preservation: holds.** C253, C255 to C268, the C210 proof, the keyed-rack fixture,
   `ontokin/`, `tests/`, `tools/` and `pyproject.toml` are byte-identical to `38ee8d18`.

## Findings

### Mandatory

**M1. Two evidence files listed in the manifest are not in the candidate commit.**
- `evidence/MANIFEST.json` says it holds the "SHA-256 of every committed evidence file" and lists:
  - `gltf-validation/verify_gltf-truncated.log`, the truncated-copy refusal behind REQ-022 and SUMMARY's `truncated_copy_refused`;
  - `runs/earlier-f0e4148f/replay-refused.log`, the retained refused replay behind REQ-033 and REPLAY.json's `earlier_attempt`.
- The `.gitignore` rule `*.log` (line 318) excludes both. They exist only as ignored files in the worktree. Their bytes match the manifest (`f5d6f38a…`, `5b07594c…`).
- REQUIREMENTS-AUDIT.md states that each "met" rests on a retained file, which is false for these two.
- **Fix:** `git add -f` both files, or rename them, and recheck the manifest against the committed tree.

**M2. The workflow rejects a correct, sign-equivalent artifact, and P03 does not exercise its claim.**
- `semantic_observe.py` (`motion_checks`) extracts the hinge angle as `theta = 2*atan2(<v, axis>, w)` from the relative quaternion without fixing its sign. A negated quaternion, which is the same rotation, yields θ − 2π.
- Executed (probe 10): the stored rotation keyframes of one blade in the actual V1 GLB were negated and the sidecar was rebound. The result:
  - C256 decodes the GLB as valid;
  - C255's `componentPass` is true and the locality check passes;
  - `score_case` rejects the case with "delivered semantics cross-checked against decoded motion", through the limits, initial-angle and tween-goal checks (maxError 6.283).
- Negating an unselected blade (`second.fingers["top"]`) is also rejected.
- P03 and `test_score.test_an_equivalent_quaternion_sign_is_not_a_change` negate C256's pose records only after G3 has already run on the unflipped poses. G3 is therefore never shown sign-invariant.
- This contradicts SCORING ("Quaternion angle comparison is sign-invariant…"; "Positive controls must include quaternion sign equivalence"), REQ-019's second criterion, and REPORT's "4 positive controls … passed" as evidence for it.
- **Fix:**
  - canonicalize the relative quaternion's sign (for example, negate it when w < 0) before `atan2`;
  - make P03 negate the stored rotations in the GLB bytes, or re-run G3 on the flipped poses, so that it is end to end;
  - rerun the qualification and the replay;
  - have the change re-reviewed.

**M3. REPORT marks REQ-016 met, but the cited table lacks three of the four required columns.**
- REQ-016's first criterion asks for a table, for each case, that lists every property with:
  - the observation used;
  - its origin in the actual bytes;
  - the independent derivation of the expected value;
  - the outcome.
- `cases/*/score.json` rows hold only `property`, `outcome` and, on failure, `fault`.
- The other columns exist only in other records: observed values and pointers in `semantic-final.json`, and derivations by field in COVERAGE.md. REPORT cites only `score.json` and GAPS.md.
- **Fix:** attach each row's origin pointers and derivation reference, or amend REPORT to name the three records that together form the table and explain how they join. The second is a records-only change.

### Optional

**O1. The replay was not run at the candidate's exact revision.**
- REPLAY.json records the replay at `d10c9f62`. REQ-021 asks for "the candidate's exact revision".
- `git diff d10c9f62 d275baa4` changes no code, and this review's own run at `d275baa4` (command 2) reproduced every retained file and rebuilt output byte for byte. The substance is therefore met.
- REPORT's REQ-021 row should name the revision and the code-identity argument, as CANDIDATE-CHECKS.json does. After M2's fix, a fresh replay at the new candidate settles it.

**O2. REPORT does not say that the harness itself produces the semantic sidecar.**
- `runner.py` and `rebuild_entry.py` call `ontokin.semantic_export.build_semantic_manifest` in process, on the program read through `read_program`. No Agent/0.2 operation delivers the sidecar.
- REPORT and README describe it only as part of the delivery. COVERAGE.md mentions `build_semantic_manifest` but not who calls it. One sentence would disclose it.

**O3. Some controls do not show their fault being detected, or their reasons are generic.**
- E04d ("self-asserted acceptance in the artifact") is rejected solely because the pre-edit GLB fails C256 `PROGRAM_BINDING` against the new source, exactly like E04b (probe 11). G3's `STALE_SIDECAR` check never runs.
- When judged against the source it was built for, the same sidecar does produce `STALE_SIDECAR`, so the check itself works.
- REQ-015's self-asserted acceptance is still covered by E04c.
- Suggested changes:
  - rebuild E04d so that `STALE_SIDECAR` is the fault that fires;
  - include the observers' fault codes in each control's `reasons` instead of only workflow-check names (E04b, E06a, R01, R02).

**O4. G3 reads more source literals than GAPS.md and REPORT state.**
- GAPS.md and REPORT state "four" literals (`deg`, the two `world` frames and `sequence`). G3 also takes the tween's numeric value, 45, from the source literal and only cross-checks the delivered `hinge_goal_rad` against it, at a C272 constant of 1e-12 rad (stricter than C253, so nothing is widened). It also reads the event time literal as a cross-check.
- The record should say so.

**O5. Two G3 fields come from reader rules, not delivered fields.**
- A site's `kind` (`system` or `authored`) is inferred from `@system` in its element ID.
- A hinge's `axisFrame` is inferred from the sidecar key name `axis_in_parent_site`.
- Some origins are wildcard or composite strings rather than concrete pointers: `/nodes/*/…`, `/joints/*/axis_in_parent_site` and `/coordinates/length,time,angle,mass`. SCORING asks for "its concrete native path".

**O6. The observation's provenance is copied from the authority record.**
- Its `acceptedRevision`, `programRevision` and `sourceHashes` come from the authority record, so C255's `provenance_check` of those fields is circular.
- The GLB's program revision is checked independently through C256's origins. The accepted revision is observed nowhere except in the authority record.
- This limit should be stated.

**O7. Two locality fields are constants.**
- `locality.unrelatedObjectsUnchanged` (16) and `secondRackObjects` (11) are counted from C255's expected objects. They would read 16 and 11 even when locality fails.
- REPORT's statement is still supported by `passed`. The fields should be measured or renamed.

**O8. The rebuild's tool identities are recorded only in part.**
- REQ-018 asks for the tools' identities and their hashes. The interpreter is recorded by version and path only, with no binary hash.
- `setuptools>=77` is resolved from the index at run time (84.2.1 here) and is not pinned. The wheel SHA-256 and the implementation's `source_code_sha256` are recorded.

**O9. The readiness table calls the readers "qualified" before the review.**
- It says "The GLB and sidecar readers and the scripted runner are qualified on this family" while the independent oracle review is pending. M2 shows a reader defect.
- Use "pending independent review", as the oracle row does.

**O10. Two REPORT citations need precision.**
- "All six delivered GLBs" are two distinct byte sequences: d009… for 0.65 m and 05eb… for 0.75 m.
- The C210 comparison names Linux but not the C210 revision. REQ-031 asks that a cited historical result keep its revision and environment.

**O11. `qualify.py` writes inside the checkout.**
- Through `tools/bootstrap_local.py`, it writes a report into the checkout's ignored `build/local-environment/`. The scope's constraint says run output goes outside every checkout.
- It is harmless and ignored, but it should be disclosed or redirected.

**O12. The `cad34f35` crash kept no traceback.**
- Its partial output remains in `runs/qualify-dev-1`, and CONTROLS.md describes the cause. No traceback or log was retained.

## Verdict

**changes required.**
- M1, M2 and M3 must be resolved.
- M2 changes evaluator code. The qualification and replay must then be rerun at the new candidate, and the change reviewed again (REQ-026).
- M1 and M3 can be resolved in the records alone.
- The optional findings are recommendations.
