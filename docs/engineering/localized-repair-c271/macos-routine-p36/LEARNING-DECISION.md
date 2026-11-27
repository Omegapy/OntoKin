# C271-P36 learning checkpoint

Assessed under the ontokin-learning skill on 2026-11-27 (UTC), when gate MR stopped at stage S6.

**One supported lesson, captured** in [memory](../../../workflow/memory.json). The record names its
evidence and its limits.

- **`memory-c271-derived-workspace-tracked-paths`.** Before a qualifying run of the routine driver
  is frozen, someone must check by reading that every path tracked at the candidate reaches the
  driver's isolated workspace, or that the provider's derived source check admits its absence.
  - **The case.**
    - The driver copies only `SOURCE_DIRS` and `ROOT_FILES`, but `read-tree` gives the workspace's
      index the candidate's whole tree.
    - At B, seven tracked `.claude/` entries are therefore deleted in the workspace.
    - The provider refuses every status line there that is not a generated example.
    - Main's own baseline summaries already recorded those seven deletions.
  - **Why it was missed until the freeze review.** The controls ran on fixture repositories, MH's
    cohort ran at the worktree itself, and the freeze author's validation stopped before the first
    Git read.
  - **Evidence:** [freeze review 001](reviews/freeze-review-001/FREEZE-REVIEW-001.md) (FZ-01),
    its [disposition](reviews/FREEZE-REVIEW-DISPOSITION-001.json) with the Director's confirmation,
    and [the outcome](OUTCOME.json).
  - **Limits:** `tools/check_local.py` and the 0.2.0 provider at commit B. No run showed the refusal;
    it is established by reading the code together with main's records.

**Considered and not captured:**
- **MI's per-module records of the branch's own tests.** They show 93 tests not passing on this host.
  The Director's brief to the freeze author said that the branch's own tests had never run as a
  suite here, and so expected them to pass. The author found MI's records and attributed 91 of them
  by exact record. That was a slip in one brief, corrected inside the stage. The outcome records
  the 93 as open for the R03 review, and the freeze review's FZ-04 carries the rule that an
  attribution is not an acceptance.
- **The truncated temporary directory in unittest reasons.** unittest shortens long values before
  `[N chars]`, so a path label does not match them. This phase's copy builder labels the shortened
  forms too ([README-PORTABLE.md](README-PORTABLE.md)). It is a detail of this phase's records,
  already covered by `memory-c271-privacy-scan-scripts-stay-local`'s rule to search every portable
  copy before it is committed.

No lesson claims anything beyond this executor, this contract, or the inputs that MR examined.
