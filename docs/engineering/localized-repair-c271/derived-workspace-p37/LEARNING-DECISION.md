# C271-P37 learning checkpoint

Assessed under the ontokin-learning skill on 2026-11-28 (UTC), after the reviewed correction.

**Two supported lessons, captured** in [memory](../../../workflow/memory.json). Each record names its
evidence and its limits.

- **`memory-c271-read-tree-index-refresh`.** An index that `git read-tree` builds has no stat data, so
  every later `git status` there hashes every tracked file again. With `GIT_OPTIONAL_LOCKS=0`, as the
  driver's Git reads use, status never writes the index back, so it pays that cost each time.
  - **The case:** in the driver's isolated workspace of this tree, about 1.17 GB in 23,145 files, each
    status read took about 2.5 s against the provider's 5 s allowance. After one `update-index -q
    --refresh`, it took about 0.08 s.
  - **The correction:** the driver now refreshes the workspace's index once after its copy. Status still
    reports exactly what it did before.
  - **Evidence:** [the measurement](measure/MEASURE-001.json), [the decision](DECISION-001.md)
    section 4, and [the review](reviews/review-001/REVIEW-001.md).
  - **Limits:** this host and this tree. One measurement, taken after a manual refresh; RV-06 (d) carries
    it to the next freeze.
- **`memory-c271-scratchpad-scripts-beside-the-clone`.** A script whose output becomes cited evidence
  must be copied beside the clone, with its SHA-256, before a record cites it.
  - **Why:** the session's scratchpad can be cleared by a reboot or a cleanup, so evidence that depends on
    it is not durable (PROTOCOL section 5). This holds for the Director's own scripts and for the
    workers'.
  - **The case:** review 001's RV-02 found that the measurement script, S5's run and comparison scripts
    and W1's scripts lived only there. They were copied at S8.
  - **Evidence:** [the review](reviews/review-001/REVIEW-001.md) (RV-02), [its disposition](reviews/REVIEW-DISPOSITION-001.json)
    and [EXACT-RECORDS.json](EXACT-RECORDS.json).
  - **Limits:** a working rule for local phases; it adds no tool.

**Considered and not captured:**
- **The correction itself.** `copied_source_path`, and the derived check's one admitted line, are
  recorded in the code, the decision and the frozen controls. P36's
  `memory-c271-derived-workspace-tracked-paths` already holds the lesson that led to them.
- **The storage module's environment-dependent outcome class.** It depends on whether a Git LFS client
  is reachable, and is recorded in [S5's comparison](checks/s5-001/S5-COMPARE.json) and its
  [baseline run](checks/s5-storage-baseline/COMMAND.json). It is a fact of this host, not a general
  lesson.
- **The builder refusing its own copy.** That is P35's `memory-c271-privacy-scan-scripts-stay-local`
  again, and it behaved as that record says it should.

No lesson claims anything beyond this executor, this contract, or the inputs that the phase examined.
