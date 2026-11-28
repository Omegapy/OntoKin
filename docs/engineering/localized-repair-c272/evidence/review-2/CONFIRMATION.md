# C272 confirmation of `48d35db9..a526d147`

- **Reviewer:** the Claude Code subagent that wrote review-1 and review-2.
- **Commit checked:** `a526d147aba038ace95f5664a56d07ad7b5c7658`, the worktree HEAD, with a clean tracked tree.
- **Date:** 2026-11-28 UTC.

## Checks and outcomes

1. **The change is records-only: confirmed.**
   - `git diff --stat 48d35db9 a526d147` lists eight files:
     - `CONTROLS.md`, `README.md` and `REPORT.md`;
     - `evidence/CANDIDATE-CHECKS.json`, `evidence/CHECKS.json` and `evidence/MANIFEST.json`;
     - the new `evidence/review-2/REVIEW.md`;
     - `docs/workflow/tasks/C272/task.json`.
   - No code, test or run-evidence file changed. That covers `*.py`, `*.mjs`, `evidence/runs/`, `gltf-validation/`, `playback/`, `ontokin/`, `tools/` and `tests/`.
2. **The manifest matches the committed tree: confirmed.**
   - I compared `probes/manifest_check_a526d147.py` against `git show` of `a526d147`.
   - All 224 listed files are committed, each with a matching size and SHA-256.
   - No tracked evidence file is missing from the list.
3. **The edits are accurate: confirmed, with two minor wording points below.**
   - **N1.** The new P03 note in CONTROLS.md is accurate. The signs cancel within each hinge pair, and the unit test negates individual nodes (two blades and `first`), so it would catch M2.
   - **N2.** The count of 100 rows is correct: 74 semantic, 18 geometry and 8 check rows.
   - **N3.** The README table is whole again, and the paragraph now follows it.
   - **N4.** REPORT's statements are true:
     - REQ-026 is met;
     - R11 is met after one round of changes;
     - the oracle, its formulas and its controls were reviewed and accepted;
     - the readers are accepted "on this family".

     Both rows keep "Partly addressed", and the readers stay limited to this family.
   - **N5.** Each added command matches its tool's interface. The `observer-candidate-2` output is byte-identical to `observer-candidate-bfa9e8ff.json`. The `pending` key was dropped because those checks are now recorded.
   - `evidence/review-2/REVIEW.md` is my review byte for byte, apart from one sanitized line.

## Minor problems (not blocking)

- **A garbled sentence from sanitizing.** In the retained review-2, row 13 now reads "differs only by replacing `<parent>` with `<parent>`". It should say "replacing the local parent path with `<parent>`".
- **Ledger wording.** `task.json`'s "independent review" check row describes the worker as a "separate Claude subagent with fresh context". That is true of review 1. Review 2 was done by the same subagent, which carried review 1's context; it was still separate from the author.
