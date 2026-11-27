# Gate MR plan: the complete default routine as a qualifying run, and R03 acceptance

Phase C271-P36, Director `c271-p36-14f7f8b219db`, local mode. This is gate MR of the adopted
contract `ontokin.current-host-readback/0.2.0`, at design revision 4, which is the contract as
amended by P33-AMENDMENT-001 ([contract section 11](../macos-contract-design-p31/CONTRACT.md#11-gates-and-sequencing)).
It is also R03 of C271 on this executor. The [declaration](PHASE.json) quotes the owner's direction.

This plan fixes the stages, the workers, the fixed state, the start accounting and the comparison
rules. It holds no execution values. The independent author freezes those in the observation plan
and the operational freeze, and a fresh reviewer reviews each one before it runs. Times are UTC.
Machine paths are left out; places beside the clone are named relative to it.

## 1. What MR must establish

The contract's gate row asks for three things:
- a complete default routine as a qualifying run, with zero missing or skipped obligations, as
  P05's Gate R requires;
- main's recorded macOS baseline outcomes, kept visible and compared under OK-ENG-009 with exact
  inputs, among them the test with a last-digit fixture difference and the failures that occur
  only under a symlinked temporary directory;
- R03's acceptance after that.

[R03](../../../workflow/tasks/C271/REQUIREMENTS.md#r03--required-checks-and-independent-review)
asks for an independent review of the exact candidate and its evidence, with its mandatory
findings resolved. Before integration, it also asks for the complete affected regression
inventory, the required local driver and the applicable documentation and workflow checks, with
every failure, interruption and environment limit retained.

**The routine.** It is `tools/check_local.py` without `--full` or `--force-agent`. Its seven stages
are `unit-tests`, `source`, `agent`, `construction`, `surface`, `impulse` and `documents`.
- C271 changes no exporter, viewer or Agent/0.5 file, so AGENTS' check table selects neither the
  visual job nor the Agent/0.5 cohort.
- The visual profile is not prepared on this host.
- Main's recorded baseline ran the same core profile.

If W1 or a review finds an affected file that needs either profile, that is a finding.

**Two runs, in this order.**
- **R1, qualifying.** Both selection arguments come from the reviewed freeze, and the temporary
  directory is resolved (contract section 7). R1 is the only run that can be cited for the readback
  methods, for MR or for R03.
- **R2, ordinary.** Neither selection argument is given, and the temporary directory is macOS's
  default, which runs through the `/var` link.
  - It compares the failures that occur only under that directory with main's run under the same
    directory, with exact inputs.
  - It runs MC22 on a real run.
  - It is no evidence for the readback methods (contract section 8).

**The baseline.** It is the two resulting-main runs of main `8e847c15`, recorded in
[INTEGRATION.json](../../local-migration-20261124/INTEGRATION.json):
- the resolved-directory run, with 4,989 tests, one failure and three skips;
- the default-directory run, with 307 tests that do not pass.

Their logs and summaries are kept beside the clone under `../OntoKin-local/checks/`, with the
digests that record gives. From `8e847c15` to `51223c9b`, main changed no file under `tests/`,
`tools/`, `ontokin/`, `prototypes/`, `fixtures/`, `schemas/` or `examples/`. W2 confirms this, and
the documents that the `documents` stage reads, with exact inputs.

**If MR passes,** R03 is accepted for this executor and this profile: macOS arm64 with CPython
3.12.13, and the core profile. It is not R04 or a release. Contract section 10 lists what no
result under this contract can support.

## 2. Stages

| Stage | Who | What | Acceptance |
| --- | --- | --- | --- |
| S1 | Director | This plan and the declaration, pushed | A1 |
| S2 | W1 | The static start-and-write inventory of section 4, read only | A2 |
| S3 | W2, then W3 | The tooling of section 5 and its review. Committed with W1's records at one commit B, pushed and read back | A3 |
| S4 | W2, then W3 | The observation plan at B, outside Git. The Director takes its digest from the review record, not from the plan | A4 |
| S5 | Director, then W3 | M0 and M1 through `observe`, then the HOST review | A5 |
| S6 | W2, then W3 | The operational freeze and its review | A6 |
| S7 | Director | R1, then R2, exactly as frozen, with the frozen checker and comparison steps | A7 |
| S8 | W4 | The independent audit | A8 |
| S9 | W3 | The R03 acceptance review of section 10 | A9 |
| S10 | Director | Records, portable copies, checks, push, readback, comments | A10, A11 |

S2 and S3 run at the same time, and S2 must end before S4's plan is adopted. Each later stage starts
only after the stage before it has a review without mandatory findings, or after its findings are
resolved and the review is repeated. A refusal, a failure to run as frozen or an unknown outcome
stops its stage, and section 9 applies.

## 3. Workers

| Worker | Role | Starts allowed |
| --- | --- | --- |
| W1 | start-and-write inventory reviewer | static reads; its own scripts under `-I -S -B` |
| W2 | independent author of the tooling, the observation plan and the operational freeze | as W1, plus the tooling's own tests, the observer's `static`, `python-inventory` and `source-inventory` commands, MH's discovery collector and the driver's `--list`, none of which starts Node or the bound Git's `--version` |
| W3 | independent reviewer: a fresh agent for each of the five reviews | as W1, plus the tooling's own tests |
| W4 | independent auditor | as W1 |

- **Who they are.** All four are Claude Code subagents started in fresh contexts, with the
  session's model. No review agent has an earlier review in its context.
- **What they never do.** No worker makes a Git write, edits the worktree, downloads or installs
  anything, or opens a prepared tree, the evidence or the worktree in Finder.
- **Where they write.** Each worker writes only under `../OntoKin-local/c271-p36/workers/`, in its
  own directory.
- **Node, Git and the routine.** No worker starts Node, `ldd`, `codesign`, Git's `--version`, the
  observer's `observe`, the routine driver (apart from `--list`) or the unit suite. Only the
  Director runs a command that starts Node, the bound Git or the routine, and only as frozen.
- **The interpreter.** Every start of the framework interpreter uses `-B` (section 6).

## 4. The start-and-write inventory (S2)

The complete routine runs about six thousand tests. Many of them start processes, and the branch's
own tests have never run as one suite on this host. MH ran only the readback module and its own
tooling. So before anything is frozen, W1 establishes by reading, without running anything:

- **Every start the routine can make, in either run kind.** That means the driver's own (D-19's
  `uname` and `file` among them), each stage's command, and every start inside the unit stage's
  modules:
  - `subprocess`;
  - `os.exec*`, `os.spawn*`, `os.posix_spawn*`, `os.system` and `os.popen`;
  - `multiprocessing` and `pty`;
  - `ctypes` routes to `fork` or `exec`;
  - any program resolved through `PATH`.

  For each one, W1 records the program, the argv pattern, the environment (inherited or replaced),
  and whether `-B` or `PYTHONDONTWRITEBYTECODE` reaches a Python child. An isolated (`-I`) child
  ignores that variable.
- **Foreign programs.** Whether any start can reach any of these:
  - a Node.js executable other than the pinned runtime;
  - `ldd` or `codesign`;
  - a program outside the operating system's own directories, the developer tools' Git, and the
    framework interpreter with its `.venv`.

  Another Node.js installation, which belongs to other software, is on `PATH` on this host. The
  doctor, for example, starts the first `node` on `PATH` unless it is given `--node`.
- **Writes into bound trees.** Whether any start, or the routine itself, can write into these:
  - the Python installation trees that HOST binds;
  - the pinned runtime;
  - the reader tree;
  - the worktree.

  An example is the bytecode of a Python child that has neither `-B` nor the variable. For each
  such start, W1 lists the modules it imports, and states by reading whether their cached bytecode
  already exists in the bound trees. MC32 refuses an added file, so a write before the readback
  module runs would fail R1.
- **The expected Node starts.** For each run: R1 is expected to make the CPU trio's three, through
  the provider, and R2 none. W1 also records where the readback module falls in the unit stage's
  order.

W1 writes a report and a machine-readable list, with a verdict on each point. Its findings go to the
observation plan and the freeze.

## 5. Tooling (S3)

The tooling lives in `docs/engineering/localized-repair-c271/macos-routine-p36/tooling/`. It uses
the standard library only.
- It lies outside the unit stage's start directory and outside the provider's source set. It
  therefore changes neither the default inventory (MC28) nor what the provider binds.
- Every plan that uses a tool binds it by path, SHA-256, size and mode.
- P07 section 3 admits no untracked harness and no unbound result synthesizer.

| Piece | What it does |
| --- | --- |
| Unit-log outcome collector | Reads a unit-stage log, the `unittest -v` output that the driver keeps. It gives one record for each raw test ID: the outcome (passed, failure, error, skipped, expected failure or unexpected success), the first line of the reason for a failure or error, and any failing subtests. It checks that the parsed counts equal the log's own `Ran` and result lines, and it refuses a log that it cannot parse completely. |
| Baseline comparator | Applies OK-ENG-009 section 3 item 4 with exact inputs. Each log and summary is bound by SHA-256. From a baseline log and a candidate log, it lists the unchanged results; the new tests that do not pass and the tests that no longer fail; any different outcome, reason or subtest; and the added and removed IDs. It classifies no test as exempt. From the two summaries, it compares each stage's status, its report summaries and its pending external cases. An attribution, such as D-18's, comes only from the freeze, by exact test ID and reason. |
| Readback evidence reader | Reads R1's provider records under the driver's output: the selection, the derived workspace binding, the three CPU attempts with their starts and receipts, and their reports. It hands the rows to MH's numerical-audit harness. |
| Reused from MH | The [failure-capture procedure](../macos-qualification-p35/tooling/FAILURE-CAPTURE.md), the runtime-discovery collector (MC28) and the numerical-audit harness, unchanged and bound by digest. A needed change is a new tool here, not an edit of MH's. |

The tooling observes. It changes nothing in the implementation, the tests, the adopted contract,
the amendment or MI's frozen controls.

## 6. The fixed state from S4 to S8

- **One commit.** From the freeze of the observation plan to the end of the audit, HEAD is B and
  the worktree is clean, with only `.venv/` ignored. Nothing is committed, checked out, merged or
  edited in the worktree. The plans, HOST, the freeze and the evidence stay beside the clone. S10
  commits their portable copies after the R03 review.
- **One boot.** The plan binds `kern.bootsessionuuid`. A reboot ends the attempt: the plan, HOST
  and the freeze no longer apply, and S4 starts again with new records. The earlier records are
  kept.
- **`-B` (MH's N-09).** On this host, `python3` on `PATH` is the framework interpreter that HOST
  binds. Every start of that interpreter, whatever its name, uses `-B` on its command line or runs
  with `PYTHONDONTWRITEBYTECODE=1` recorded. That includes the routine, the Director's own checks
  and other sessions on this host. An added bytecode file changes the inventory, and MC32 refuses
  it.
- **The language and region settings stay unchanged.** HOST records `__CF_USER_TEXT_ENCODING`,
  and a different value refuses (MC31).
- **No Finder** on the prepared trees, the evidence or the worktree, because of `.DS_Store` files.
- **Temporary directories.**
  - R1 uses the resolved form of the default temporary directory. The freeze records it.
  - R2 uses the default form, as main's default-directory run did.
  - The evidence lies on the clone's volume and the temporary directory on the system volume. MI's
    I-05 needs them on different volumes. The freeze records both device numbers.
- **Retained unchanged,** at their paths and with their modes:
  - the Node archive;
  - the committed C195 archive;
  - MP's exact apply plans and install receipts;
  - MH's exact records.
- **Nothing installed or downloaded.** The doctor's advice to rebuild the `.venv` is not followed
  (D-21).
- **Evidence.**
  - It goes under `../OntoKin-local/c271-p36/evidence/`, which is created before S4.
  - Each attempt's paths stay absent until that attempt.

## 7. Obligations carried into MR

| Obligation | Source | How MR meets it |
| --- | --- | --- |
| A complete default routine as a qualifying run, with zero missing or skipped obligations | contract section 11; P05's Gate R | R1 |
| Main's baseline outcomes compared with exact inputs, including the last-digit fixture test and the symlinked-directory failures | contract section 11; OK-ENG-009 section 3 | the comparator, R1 against main's resolved-directory run and R2 against its default-directory run |
| MC23 on a real qualifying run | contract section 9; MI | R1's readback cohort: any skip, error, expected failure or missing method leaves R1 not qualified |
| MC28 on the complete default inventory, the additions included | contract section 9; MI | Discovery at B against the baseline of 5,587 IDs at `1c2f25ba`, plus exactly the 407 IDs of [INVENTORY-ADDITIONS.json](../macos-implementation-p33/INVENTORY-ADDITIONS.json) (MH's correction of MI's "401"), and R1's log against the same list |
| MC22 on a real ordinary run | contract sections 8 and 9 | R2: the driver proceeds, the readback class fails at setup with the fixed reason, there is no skip, and the summary records the ordinary run kind |
| D-19: the driver's environment record starts `uname` and `file` through `PATH` in every run | MI | W1's inventory; they are recorded, not counted as bounded starts |
| O-01: the driver's `stop_process` lets a Darwin `EPERM` escape at a timeout | MI's amendment review | The freeze's per-command timeout exceeds the expected durations, so no stage timeout is expected. If one occurs, it is recorded. The driver's owner is a later phase. |
| I-05: MC16's real cases need the evidence root and the temporary directory on different volumes | MI | section 6 |
| D-18: two 0.1.0 driver tests that assert the refusal S8 removes fail visibly | MI | Recorded with their reasons, and attributed by exact ID in the freeze; R04 classifies them |
| S8's outcome changes | contract section 8 | Recorded and compared: R1 runs the trio that main skips, and in R2 the readback class has one setup error where main has three skips. R04 classifies them. |
| AU-07: Node warns that `--experimental-loader` may be removed | MH's audit | Recorded from R1's evidence; the argv stays unchanged; a note for R04 |
| HOST is observed again | MH's outcome | S4 and S5; MH's HOST stays a record of MH |

## 8. Start accounting

| Row | Node | Other |
| --- | ---: | ---: |
| M0, Git `--version` | 0 | 1 |
| M1, Node `--version` | 1 | 0 |
| R1, the readback CPU trio through the provider | 3 | 0 |
| R2, none: the readback class fails at setup | 0 | 0 |
| **Expected for MR** | **4** | **1** |

- **The freeze decides.** The operational freeze fixes the exact rows and totals before S7, from
  W1's inventory. A start that the freeze does not list is a deviation. If the freeze needs more
  starts than this table expects, it states the reason, and its review checks it.
- **Counting** follows P07 section 4 unchanged:
  - an audit event or a provider record shows an attempt;
  - a receipt with a positive PID establishes a start;
  - an interrupted attempt is `UNKNOWN`, and it blocks success and any automatic retry.
- **Not counted** as bounded starts, but listed by W1 and recorded: the starts of the framework
  interpreter, Git, `uname` and `file` that the driver and the tests make, the provider's Git source
  reads, and the Director's own Git reads.
- **Never started:** `ldd`, `codesign`, and any Node other than the pinned runtime.

## 9. Failure policy

- **A refusal at M0 or M1 on the real host** is kept with its refusal record. What follows depends
  on its cause.
  - If the cause is a fact of the host or the inputs that the plan stated wrongly, a corrected
    plan is frozen and reviewed. The new attempt uses a new attempt directory, and the Director
    records the reason.
  - If the cause lies in the implementation or the contract, MR stops. A change to the
    implementation belongs to a later phase, and a change to the contract needs an amendment.
- **A run that does not run as frozen** is kept and not retried. That covers a preparation refusal,
  a driver error, an interruption or the outer bound. A corrected attempt follows the same rule as
  a refusal at M0.
- **Test failures do not stop the routine.** The driver runs every stage, and the comparator
  compares the results.
  - A test that does not pass, and that the freeze does not attribute by exact ID and reason, is a
    finding. MR records it.
  - R03 then stays unmet unless the R03 review accepts the failure with a stated reason under
    OK-ENG-009 section 3 item 4.
  - A change to the implementation or the tests belongs to a later phase.
- **R1's readback cohort** must have no skip, error, expected failure or missing method. Otherwise
  R1 is not qualified (MC23), and MR is unmet.
- **An unknown outcome** blocks success and any automatic retry (P07 section 4).
- **A mandatory review or audit finding** holds the next stage until the finding is resolved and
  the review is repeated.
- **Pending external cases** stay pending. They are neither passes nor failures. They are compared
  with the baseline's 16, and MR claims nothing for them.

## 10. The R03 acceptance review (S9)

A fresh W3, which took no part in an earlier stage, reviews the exact candidate B against main
`51223c9b`, together with MR's evidence, under OK-ENG-009 section 3 items 1 to 5. It covers:

- **Identity and scope.**
  - the base and candidate commits and trees;
  - the changed files by class;
  - the dependencies and held changes;
  - the cumulative change, including the inherited runtime and workflow changes.
- **Each changed file outside `docs/`.**
  - The reviewer establishes that its bytes at B are the bytes its accepting review examined, or
    that a later accepting review covered the change.
  - It deep-reads every file for which neither holds.
  - It also deep-reads the shared files that change existing behaviour against main:
    `tools/check_local.py`, `tools/storage_identity.py`, `tests/test_local_checks.py` and
    `tests/test_static_tray_readback_v01.py`.
- **MR's evidence:** R1 and R2, the comparison, the attributions and the audit.
- **The failure accounting and the honest limits** (items 4 and 5): the interpreter, the platform,
  the core profile, and the pending external cases.
- **The checks:** the documentation and workflow checks.

Its verdict accepts or rejects R03. Any mandatory finding names what must change. A change to the
implementation or tests belongs to a later phase.

## 11. Records

All of these are in this directory:
- `PHASE.json` and this plan;
- `inventory/`, W1's start-and-write inventory;
- `tooling/`;
- `reviews/`: the five reviews and their dispositions;
- `plans/`: portable copies of the observation plan, the inventories, the configuration, the
  commands and the expected outcomes;
- `host/`, a portable HOST;
- `routine/`: the portable summaries, outcome lists and comparisons of R1 and R2;
- the audit;
- `OUTCOME.json`, `LEARNING-DECISION.md` and `CLOSING.json`.

The exact files stay beside the clone, and their SHA-256 values are recorded. Large raw logs and the
isolated workspaces stay beside the clone, recorded by digest.

## 12. Changes after the inventory and the tooling reviews

W1's [start-and-write inventory](inventory/START-INVENTORY.md) answered section 4. Its
[disposition](inventory/START-INVENTORY-DISPOSITION.json) gives the freeze seven decisions, D-P1 to
D-P7. The sections above keep their first wording.

- **D-P1, `PATH`.** Two unit tests run the real doctor, which starts the first `node` on `PATH`. On
  this host, that is the package manager's Node. The freeze therefore fixes `PATH` for R1 and R2 so
  that no Node other than the pinned runtime can be reached by name. The default is MH's
  `/usr/bin:/bin`. If a test would then differ from the baseline only because `python3.12` or Git's
  `lfs` helper cannot be found, a directory beside the clone that holds links to exactly those
  programs goes first on `PATH`. It never holds `node`.
- **D-P2, the environment.** R1 and R2 start from `env -i` with a declared environment that the
  freeze lists in full. It holds no `PYTHON*`, `PIP_*`, `GIT_*`, `NODE_*` or `DYLD_*` variable.
  Main's baseline recorded only that its caller set no `PYTHON*`, `PIP_*` or `GIT_*` variable, so the
  difference is a stated limit.
- **D-P3.** The global Git configuration that the doctor's Git children read is recorded by digest
  only.
- **D-P4.** The driver always runs with `-B`, and the freeze checks for bytecode before and after each
  run.
- **D-P5.** The Python installation inventory is compared with HOST's before R1, between the runs
  and after R2.
- **D-P6.** The two volumes of MC16 (I-05) are recorded.
- **D-P7.** The starts that are recorded but not counted are given as expected magnitudes. Per run,
  these are about four each of `uname` and `file`, and tens of Git reads.

The tooling was rejected once. [Review 001](reviews/TOOLING-REVIEW-001.md) found that an attribution
matched when any one of a test's reasons matched (TR-01, mandatory). [Revision 2](tooling/README.md)
adopted TR-01 to TR-11, and [review 002](reviews/TOOLING-REVIEW-002.md) accepted it with
nonmandatory findings. Its [disposition](reviews/TOOLING-REVIEW-DISPOSITION-002.json) carries three
of them to the freeze as rules:
- the zero-skip checks also use the log's own counts (TR2-01);
- no attribution is frozen for an ID that is listed more than once (TR2-03);
- every attribution states a consistent not-passing outcome (TR2-04).

TR-09's binding of the reader's cohort root is carried to the freeze as well. Before commit B, the
Director ran the suite once at its committed place: 90 of 90 passed, and the worktree's status did not
change ([check record](checks/commit-b/CHECKS.json)).
