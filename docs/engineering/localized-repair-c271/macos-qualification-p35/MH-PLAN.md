# Gate MH plan: N34-M, M0 and M1, and the qualifying cohort

Phase C271-P35, Director `c271-p35-e38e3aa82ade`, local mode. This is gate MH of the adopted
contract `ontokin.current-host-readback/0.2.0`, at design revision 4, which is the contract as
amended by P33-AMENDMENT-001 ([contract section 11](../macos-contract-design-p31/CONTRACT.md#11-gates-and-sequencing)).
The [declaration](PHASE.json) quotes the owner's direction.

This plan fixes the stages, the workers, the fixed state and the start accounting. It holds no
execution values. The independent author freezes those in the observation plan and the
operational freeze, and a fresh reviewer reviews each one before it runs. Times are UTC. Machine
paths are left out; places beside the clone are named relative to it.

## 1. What MH must establish

The contract's gate row reads: N34-M, then M0 and M1, then the qualifying cohort, which is the
seven methods and the direct negatives on the owner's executor, then an independent audit.

- **N34-M** ([contract section 7](../macos-contract-design-p31/CONTRACT.md#7-host-observation-in-place-of-h0-and-h1-s3-s7-s9)).
  An independent reviewer examines the Mach-O parser's source and the closure claim against the
  actual load commands, before a macOS execution plan is adopted.
- **M0 and M1.** One run of the observer's `observe` command
  ([W3-OBSERVER section 1](../macos-implementation-p33/interfaces/W3-OBSERVER.md#1-launch-and-command-line))
  makes one Git `--version` start and one Node `--version` start, both through the Darwin
  supervisor. It writes HOST in state `OBSERVED_UNAPPROVED`. An independent review accepts HOST
  before any configuration binds it.
- **The cohort**, from [P07](../host-inspection-p07/QUALIFICATION-PLAN.md) sections 3 to 6 as
  contract section 7 adapts them. It contains:
  - the probe syntax check;
  - the direct negatives P06-H01 and P06-H02;
  - the original seven methods, run as the complete module `tests.test_static_tray_readback_v01`
    through the reviewed harness;
  - the controls assigned to MH (section 6).
- **The audit:** P07 section 6's list, recomputed by an auditor who did not author the freeze.

If MH passes, it qualifies the seven methods and the direct negatives on this executor, with
contract section 10's labels. It is not MR, R03 or a release. Contract section 10 lists what no
result under this contract can support.

## 2. Stages

| Stage | Who | What | Acceptance |
| --- | --- | --- | --- |
| S1 | Director | This plan and the declaration, pushed | A1 |
| S2 | W1 | N34-M, a static review; it must end before S4's plan is adopted | A2 |
| S3 | W2, then W3 | The tooling of section 4 and its review. Committed with the N34-M records at one commit C, pushed and read back | A3 |
| S4 | W2, then W3 | The observation plan at C, outside Git. The Director takes its digest from the review record, not from the plan | A4 |
| S5 | Director, then W3 | M0 and M1 through `observe`, then the HOST review | A5 |
| S6 | W2, then W3 | The operational freeze and its review | A6 |
| S7 | Director | The cohort and the MH controls, exactly as frozen | A7 |
| S8 | W4 | The independent audit | A8 |
| S9 | Director | Records, portable copies, push, readback, comments | A9, A10 |

S2 and S3 run at the same time. Each later stage starts only after the stage before it has a
review without mandatory findings, or after its findings are resolved and the review is repeated.
A refusal, a failure or an unknown outcome stops its stage, and section 8 applies.

## 3. Workers

| Worker | Role | Starts allowed |
| --- | --- | --- |
| W1 | N34-M reviewer | static reads; its own scripts under `-I -S -B` |
| W2 | independent author of the tooling, the observation plan and the operational freeze | as W1, plus the observer's `static`, `python-inventory` and `source-inventory` commands, which start nothing |
| W3 | independent reviewer: a fresh agent for each of the four reviews | as W1 |
| W4 | independent auditor | as W1 |

- **Who they are.** All four are Claude Code subagents started in fresh contexts, with the
  session's model. No review agent has an earlier review in its context.
- **What they never do.** No worker makes a Git write, edits the worktree, downloads or installs
  anything, or opens a prepared tree in Finder.
- **Where they write.** Each worker writes only under `../OntoKin-local/c271-p35/workers/`, in its
  own directory.
- **Node and Git.** No worker starts Node, `ldd`, `codesign`, Git's `--version` or the observer's
  `observe`. Only the Director runs a command that starts Node or the bound Git, and only as frozen.
- **The `.venv`.** Its interpreter runs only with `-B`, whoever starts it (section 5).

**W1's N34-M brief:**
- Read the Mach-O part of `prototypes/static_tray_v01/current_host_observation_v02.py`, and
  contract sections 4 and 7.
- With a reader of its own, read the header and every load command of the prepared `bin/node` and
  of each Mach-O file of the interpreter installation that contract section 4 binds.
- Compare the files with the contract's rules on each of these points:
  - thin or fat, the CPU type and subtype (W3's Q3), and the file type;
  - the allow-list, and `LC_LOAD_DYLINKER`;
  - the dylib paths, the `@`-relative references and their resolution (W3's open questions);
  - CoreFoundation (D-16).
- State whether the closure claim, with its stated limits, holds for these files, and whether the
  parser's source decides each rule as the contract says.

## 4. Tooling (S3)

The tooling lives in `docs/engineering/localized-repair-c271/macos-qualification-p35/tooling/`.
It uses the standard library only.
- It lies outside the source inventory's trees and outside the unit stage's start directory. It
  therefore changes neither the default inventory (MC28) nor the provider's source set.
- Every plan that uses a tool binds it by path, SHA-256, size and mode.
- P07 section 3 admits no untracked harness and no unbound result synthesizer.

| Piece | What it does |
| --- | --- |
| Failure-capture procedure | States what is kept on a refusal, a failure or an unknown outcome, and how the absence of a process is established, never by matching a process name alone. It allows no retry. The observation plan's `failure_capture.procedure` binds it. |
| Runtime-discovery collector | Lists the default inventory as `tools/check_local.py`'s unit stage discovers it, without running it. It compares the list with the baseline and the approved additions (section 6, MC28). |
| Unittest outcome collector | Runs the complete module `tests.test_static_tray_readback_v01`, and separately the frozen controls that MH reruns. It records each raw test ID with its outcome. It normalizes no ID except through P07 section 6's declared prefix alias. |
| Direct-probe runner | Runs the syntax check, P06-H01, P06-H02 and MC36, each one start through the Darwin supervisor's `run_process`, under the frozen argv, cwd, environment and limits. It keeps stdout, stderr, the exit status and the receipt. It does not pass through the provider's parent guard (P07 section 5). |
| Numerical-audit harness | Recomputes every row's difference, threshold and decision from the retained reference and report values. It checks that the row set is complete and has no duplicates, and that the negative has its one intended `matrix_0_3` finding (P07 section 6). |
| MC11 scanner | A reviewed static scan of the probe, the module loader and the 24 reader files for process-creation calls. |
| Control harness | Covers MI's findings F-01, F-03 and F-04. MC10 runs with the real static bindings, and only the command boundary is simulated and labelled mocked. MC29 runs with the real detectors. The provider's real `host_state` runs on this host. Each row substitutes only what it states. |

Tooling observes. It does not change the implementation, the tests, the adopted contract, the
amendment or MI's frozen controls. If a rerun needs such a change, that is a finding, and the
control stays `NOT_RUN` at MH.

## 5. The fixed state from S4 to S8

- **One commit.** From the freeze of the observation plan to the end of the audit, HEAD is C and
  the worktree is clean, with only `.venv/` ignored. Nothing is committed, checked out, merged or
  edited in the worktree. The plans, HOST, the freeze and the evidence stay beside the clone. S9
  commits their portable copies after the audit.
- **One boot.** The plan binds `kern.bootsessionuuid`. A reboot ends the attempt: the plan, HOST
  and the freeze no longer apply, and S4 starts again with new records. The earlier records are
  kept.
- **`-B`.** Every start of the `.venv`'s interpreter uses `-B`, before M0 and after it. HOST binds
  the Python inventory, and an added bytecode file would change it (MC32).
- **No Finder** on the prepared trees, the evidence or the worktree, because of `.DS_Store` files.
- **Retained unchanged,** at their paths and with their modes:
  - the Node archive, mode 0o444;
  - the committed C195 archive;
  - MP's exact apply plans and install receipts.
- **Nothing installed or downloaded.** The doctor's advice to rebuild the `.venv` is not followed
  (D-21).
- **Evidence.**
  - It goes under `../OntoKin-local/c271-p35/evidence/`, which is created before S4.
  - Each attempt's paths stay absent until that attempt.
  - Temporary directories are resolved paths (contract section 7).

## 6. Obligations carried into MH

| Obligation | Source | How MH meets it |
| --- | --- | --- |
| N34-M | contract section 7 | S2 |
| Whether `bin/node` links CoreFoundation | D-16; MP W1's F2 | Read from HOST's load commands before MC36. If it does not, MC36 is not run and needs an amendment (W5's Q1). |
| MC10 with real static bindings | MI F-01 | control harness, 0 starts |
| MC11 on the module loader and the 24 reader files | MI F-09 | scanner, 0 starts |
| MC24, MC25 and MC26 | contract section 9 | the cohort module: the CPU trio and the mocked quartet |
| MC27 | contract section 9; P07 section 5 | direct-probe runner |
| MC28, with the cohort's missing-method accounting | contract section 9; MI F-05 | discovery and outcome collectors. The baseline is the 5,587 IDs at `1c2f25ba`; the approved additions are exactly the 407 IDs of [INVENTORY-ADDITIONS.json](../macos-implementation-p33/INVENTORY-ADDITIONS.json) (note below). |
| MC29 with the real detectors | MI F-03 | control harness; zero new starts |
| MC30 for the probe | contract section 9 | The positive starts cover it if HOST records `__CF_USER_TEXT_ENCODING`; the freeze states how. |
| MC36 | contract section 9 | direct-probe runner, after D-16 |
| MC37 again | AMENDMENT-001 | the frozen control, run on this host; 1 other start |
| The provider's real `host_state` | MI F-04 | control harness, or the cohort's own reads; the freeze states which |
| W3's open questions (fat files; `@rpath` stricter than dyld; `MH_OBJECT`; the Git version checked by grammar only) and Q3 (only `CPU_SUBTYPE_ARM64_ALL`) | MI | N34-M, and M0 on the real files |
| A refused probe result's labels are unverified | MI, W5's Q5 | The freeze and the audit read a refusal from stderr, the exit status and the receipt. They report the labels of a refused result as unverified. |
| The adoption record lies outside the source set | MI, W5's Q2 | The observation plan and the configuration bind it separately; the review checks that. |
| `-B` until the inventory is frozen and M0 has run | MI, MP; W3's F4 | section 5 |

**Note on the number of additions.** In its list of MR obligations, MI's
[OUTCOME.json](../macos-implementation-p33/OUTCOME.json) says "the 401 additions".
INVENTORY-ADDITIONS.json lists 407: 109, 151, 22, 49, 59 and 17 in its six modules. No file
under `tests/`, `ontokin/`, `prototypes/` or `tools/` has changed since its candidate commit
`7b759de0`. MH uses 407. MI's record stays unchanged, and MH's outcome records the correction.

## 7. Start accounting

| Row | Node | Other |
| --- | ---: | ---: |
| M0, Git `--version` | 0 | 1 |
| M1, Node `--version` | 1 | 0 |
| Probe syntax check | 1 | 0 |
| P06-H01 | 1 | 0 |
| P06-H02 | 1 | 0 |
| CPU trio (MC24, MC25) | 3 | 0 |
| Coordinator quartet (MC26), mocked | 0 | 0 |
| **The contract's minimal path** | **7** | **1** |
| MC36 | 1 | 0 |
| MC37 | 0 | 1 |
| **Expected for MH** | **8** | **2** |

- **The freeze decides.** The operational freeze fixes the exact rows and totals before S7. A
  start that the freeze does not list is a deviation. If the freeze needs more starts than this
  table expects, it states the reason, and its review checks it.
- **Counting** follows P07 section 4 unchanged:
  - an audit event of `subprocess.Popen` shows an attempt;
  - a receipt with a positive PID establishes a start;
  - an interrupted attempt is `UNKNOWN`, and it blocks success and any automatic retry.
- **Not counted** as bounded starts: the tooling's Python launchers and the Director's own Git
  reads. Every command is recorded all the same.
- **Never started:** `ldd`, and `codesign`, which is optional and not selected.

## 8. Failure policy

- **A refusal at M0 or M1 on the real host** is kept with its refusal record. What follows
  depends on its cause.
  - If the cause is a fact of the host or the inputs that the plan stated wrongly, a corrected
    plan is frozen and reviewed. The new attempt uses a new attempt directory, and the Director
    records the reason.
  - If the cause lies in the implementation or the contract, MH stops. An example is a load
    command outside the allow-list. A change to the implementation belongs to a later phase, and
    a change to the contract needs an amendment.
- **A cohort row whose outcome differs from its frozen expectation** is kept, and the gate is unmet
  for that row. Nothing is relabelled. The remaining Node starts stop, unless the freeze declares
  the remaining rows independent.
- **An unknown outcome** blocks success and any automatic retry (P07 section 4).
- **A mandatory review finding** holds the next stage until the finding is resolved and the review
  is repeated.

## 9. Records

All of these are in this directory:
- `PHASE.json` and this plan;
- the N34-M review;
- `tooling/`;
- `reviews/`: the four reviews and their dispositions;
- `plans/`: portable copies of the observation plan, the inventories, the configuration, the
  fixtures, the control table and the commands;
- `host/`, a portable HOST, and `cohort/`, the portable outcomes;
- the audit;
- `OUTCOME.json`, `LEARNING-DECISION.md` and `CLOSING.json`.

The exact files stay beside the clone, and their SHA-256 values are recorded.

## 10. Changes after N34-M

W1's [N34-M review](n34m/N34-M-REVIEW.md) accepted with nine nonmandatory findings. The
[disposition](n34m/N34-M-DISPOSITION.json) adopts these changes. The sections above keep their
first wording.

- **N-09, the `-B` rule (section 5).** On this host, `python3` on `PATH` is the framework
  interpreter that HOST binds. The rule therefore covers every start of that interpreter, whatever
  its name, the Director's own workflow and documentation checks included: `-B` on the command
  line, or `PYTHONDONTWRITEBYTECODE=1` in the environment and recorded. The starts of M0 and of the
  cohort carry `-B` on their command lines, because their environment admits no Python variable.
  The shared hand-over note asks the other sessions on this host to follow the same rule until MH
  ends.
- **N-04, MC36.** The operational freeze ties MC36 to a positive probe start of the same freeze
  that observed `__CF_USER_TEXT_ENCODING` with HOST's value (MC30). If none observed it, MC36 stays
  `NOT_RUN` pending an amendment of D-16. Its expected outcome is not weakened.
- **N-05.** The observation plan's review cites W3-OBSERVER section 6 as the implemented rule set,
  which is stricter than the contract's text.
- **N-07.** The observation plan's review confirms that the bound Git is the developer tools' Git
  that N34-M read, or re-reads the load commands of another candidate. The HOST review compares the
  recorded version line with the version text embedded in that file.
- **N-06.** The HOST review notes the unused `LC_RPATH` entries, among them an absent build path.
- **N-08.** The observation plan and its review use the frozen inventory's figures, not those that
  W3-OBSERVER section 5 measured before MP.
- **Carried to a later implementation phase, not needed for this host:** N-01, N-02 and N-03.
