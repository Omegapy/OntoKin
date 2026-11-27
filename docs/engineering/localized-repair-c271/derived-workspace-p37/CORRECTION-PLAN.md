# C271-P37 plan: correction of the derived workspace's source check

Phase C271-P37-derived-workspace-correction, Director `c271-p37-08beec34eb0a`, local mode. Gate MR
stopped at its operational freeze on FZ-01, a blocker in the implementation
([MR's outcome](../macos-routine-p36/OUTCOME.json)). The owner selected this correction: "Start the
correction". The [declaration](PHASE.json) quotes the direction. Times are UTC. Machine paths are left
out; places beside the clone are named relative to it.

This plan fixes the stages, the workers, their files, the checks and the records. It decides no rule.
An independent author decides the rule, and a fresh reviewer reviews it before the phase closes.

## 1. What the correction must establish

**The blocker (FZ-01).** It comes from [freeze review 001](../macos-routine-p36/reviews/freeze-review-001/FREEZE-REVIEW-001.md),
and the [Director confirmed it](../macos-routine-p36/reviews/FREEZE-REVIEW-DISPOSITION-001.json) by
reading.
- In a qualifying run, `tools/check_local.py` copies only its `SOURCE_DIRS` and `ROOT_FILES` into the
  isolated workspace, and leaves out names that `ignored()` matches. But `read-tree` gives the
  workspace's index the commit's whole tree.
- Every tracked path outside the copied set therefore shows as deleted in the workspace. At gate MR's
  commit these were seven `.claude/` entries: a `.gitignore` and six symbolic links.
- The 0.2.0 provider's derived source check refuses every status line that is not a generated
  example (`current_host_readback_v02.py`, `_verify_source`). So R1 refuses before the unit stage.
- Main's own baseline summaries record the same seven deletions.

**The rule that governs it.** The 0.2.0 contract keeps
[P05's](../current-host-p05/CONTRACT.md) isolated-workspace derivation
([contract section 1](../macos-contract-design-p31/CONTRACT.md#1-what-stays-and-what-changes)).
P05 section 3 says:
- preparation must fail on dirty or untracked **executable** source, extra executable inputs,
  missing source, or a change after the inventory was frozen;
- the derivation records the equality of "the complete copied immutable-source inventory";
- any approved generated-file exclusion must be exactly the existing driver's exclusion, and is not
  a new executable-source exception.

MC19 refuses "dirty or untracked executable source".

**What the phase must deliver:**
1. **A decision record** by an independent author.
   - It states the exact rule for status lines in the derived workspace, and its basis.
   - It states whether the rule stays within P05 section 3 and MC19, or needs a versioned amendment of
     the 0.2.0 contract. If it needs one, the phase stops before the implementation, and the
     amendment follows P33's process: an independent author, reviews, and the Director's adoption.
2. **The implementation** in the shared driver and the 0.2.0 provider.
   - The copied set has one definition, the driver's, so the provider introduces no second set of
     exceptions (P05 section 3, and the provider's own comment at the check).
   - The original route keeps refusing every status line. The derived route keeps refusing every
     dirty or untracked path inside the copied set, apart from the existing generated examples.
3. **Controls frozen by an independent author** before the Director executes them, as contract
   section 9 requires.
   - They exercise the derived route with real Git on a fixture tree that tracks paths outside the
     copied set, a symbolic link among them.
   - They keep every unchanged refusal.
4. **FZ-02, the derived route's Git timing.** The Director first measures it at the real tree's scale on
   this host (stage S2).
   - The concern is that `read-tree` leaves the workspace's index without stat data, so each status
     read hashes the copied files again.
   - The limits are the provider's 5 s allowance for each Git read, and the 28 s stage clock in which
     each start's preflight runs the selection twice.
   - If the measurement leaves too little margin, the decision corrects that too, with its own
     controls.
5. **The inventory additions** of the new test methods, by exact ID, for the next MR attempt's MC28.

**What stays unchanged:**
- the generated-example exclusion and the untracked-input refusal;
- the 0.1.0 provider, whose same check (`current_host_readback_v01.py`, `_verify_source`) is recorded
  as a follow-up of the Linux route, which does not run in local mode (P30-EXECUTOR-001);
- the driver's ordinary behaviour, its summary fields and their meanings, and main's recorded
  baseline.

**What this phase does not establish:** MR or R03. It runs no qualifying route against a real HOST.
The next MR attempt does that at the corrected commit, with a new observation plan, HOST and freeze.

## 2. Stages

| Stage | Who | What | Acceptance |
| --- | --- | --- | --- |
| S1 | Director | This plan and the declaration, pushed | A1 |
| S2 | Director | FZ-02's measurement at the declaration commit, outside the checkout (section 5) | A2 |
| S3 | W1 | The decision record, the implementation, focused tests and an interface note | A3 |
| S4 | W2 | Frozen controls for the corrected derived route | A4 |
| S5 | Director | The focused tests, the frozen controls, MI's frozen control module and the existing modules of the changed files; then the candidate commit C, pushed | A5 |
| S6 | Director | The complete ordinary routine at C (section 6), and the discovery of C's default inventory | A6 |
| S7 | W3 | The independent review of C | A7 |
| S8 | Director | Records, portable copies, checks, push, readback, comments | A8 |

Each stage starts only after the one before it is complete. S3's decision is read by the Director
before S4 starts. If it needs an amendment, the phase stops there (section 7). A mandatory finding of
S7 holds S8 until it is resolved and the affected stages are repeated.

## 3. Workers

All three are Claude Code subagents in fresh contexts, with the session's model. W2 and W3 wrote none
of the implementation, and W3 wrote none of the controls.

| Worker | Role | Exclusive writes |
| --- | --- | --- |
| W1 | Author of the decision and the implementation | `tools/check_local.py`; `prototypes/static_tray_v01/current_host_readback_v02.py`; focused tests in `tests/test_local_checks.py` and `tests/test_current_host_readback_provider_v02.py`; this directory's `DECISION-001.md` and `interfaces/W1-CORRECTION.md` |
| W2 | Independent control author | one new test module under `tests/`, which W2 names, and this directory's `CONTROLS-FROZEN.json` |
| W3 | Independent reviewer | its review beside the clone; S8 copies it here |

- **Shared checkout.** The workers share this checkout for disjoint files under the Director's
  commits, as PROTOCOL section 4 allows.
- **What no worker does:**
  - a Git command that writes (`add`, `commit`, `stash`, `checkout`, `reset`, `switch`, `restore`,
    `merge`, `rebase`, `push`);
  - installing or downloading anything;
  - starting Node, `ldd`, `codesign` or the routine driver.
- **Tests.** W1 and W2 may run their own focused test modules with `.venv/bin/python -B` and a resolved
  temporary directory. Their fixtures may start Git.
- **Evidence.** Each worker writes its detailed evidence under `../OntoKin-local/c271-p37/workers/<id>/`.

## 4. Checks (AGENTS' table)

- **Routine development:** the complete driver, `tools/check_local.py`, once at C as an ordinary run
  (section 6).
- **Tool changes:** the focused tests of the changed files. Among them are the existing modules
  `tests.test_local_checks`, `tests.test_current_host_readback_provider_v02`,
  `tests.test_current_host_readback_driver_v02` and `tests.test_current_host_readback_controls_v02`, which
  is MI's frozen control module, unchanged, together with the new control module. The 0.1.0 modules
  `tests.test_current_host_readback_provider` and `tests.test_current_host_readback_driver` keep their
  recorded outcomes. D-18's two failures stay visible.
- **Records:** `tools/chat_workflow.py check`, the documentation verifier and a whitespace check.
- **Not applicable:** the Agent/0.5 cohort and the exporter and viewer checks, since no such file
  changes, and the conformance command, since no OntoKin runtime or language semantics change.
- **How commands run:** with `.venv/bin/python -B` and a resolved temporary directory, writing output
  outside the checkout.

## 5. The measurement of FZ-02 (S2)

1. The Director copies the worktree, clean at the declaration commit, with the driver's own
   `prepare_workspace` into a fresh directory under `../OntoKin-local/c271-p37/measure/`.
2. It binds HOST's Git implementation through the driver's `bind_git`.
3. In that workspace it times the provider's exact reads: `status --porcelain=v1 --untracked-files=no`
   and `ls-files --others --exclude-standard -z`, through the driver's `git_read`, five times each.
4. It then refreshes the index with `update-index -q --refresh`, and times the two reads five times
   again.
5. It records each time, the file count and byte count of the copy, and the status lines.

No Node starts. The only Git started is HOST's. The measurement changes nothing in the checkout.

## 6. The ordinary routine at C (S6)

The command:

```sh
/usr/bin/env -i HOME=… LOGNAME=… USER=… PATH=/usr/bin:/bin TMPDIR=<resolved>/ \
  <worktree>/.venv/bin/python -B tools/check_local.py --timeout 7200 --output-dir ../OntoKin-local/c271-p37/routine/ordinary-001
```

- **Launch.** In the shell tool's background mode, beside a bound timer with an outer bound of
  10,800 s, as gate MH and MR planned it. At the bound the outcome is UNKNOWN, and only processes of
  established identity are stopped.
- **`PATH`.** It reaches no Node (MR's D-P1), so the routine starts none, and it starts no `ldd` or
  `codesign`.
- **Python inventory.** The observer's `python-inventory` runs before and after. It starts nothing, and
  a difference is recorded for the next HOST.
- **Outcomes** are recorded, not accepted.
  - MR's reviewed comparator lists every difference from main's resolved-directory run.
  - Every failure stays visible. None is attributed or classified here; the R03 review does that.
- **Discovery.** MH's collector, which starts no test, gives C's default inventory. The additions
  against commit B's 5,994 IDs are listed by exact ID.

## 7. Failure policy

- **A decision that needs an amendment** stops the phase before S4. The decision is kept, and the
  amendment follows as its own work.
- **A test or control that fails at S5** goes back to its author.
  - An implementation defect is corrected in the implementation, never in a frozen expectation.
  - A defect in a frozen control is recorded and refrozen by W2, and the original is kept.
- **Routine failures** do not stop the routine. They are recorded.
- **An unknown outcome** blocks success and any automatic retry.
- **A mandatory review finding** holds S8 until it is resolved and the affected stages are repeated.

## 8. Records

All of these are in this directory:
- `PHASE.json` and this plan;
- `DECISION-001.md` and `interfaces/`;
- `CONTROLS-FROZEN.json`;
- `measure/`, the FZ-02 records;
- `checks/`;
- `routine/`, the portable summaries and comparisons;
- `reviews/`;
- `INVENTORY-ADDITIONS.json`;
- `OUTCOME.json`, `LEARNING-DECISION.md` and `CLOSING.json`.

The exact files stay beside the clone under `../OntoKin-local/c271-p37/`, recorded by digest. Large
raw logs and the routine's isolated workspace stay there too.
