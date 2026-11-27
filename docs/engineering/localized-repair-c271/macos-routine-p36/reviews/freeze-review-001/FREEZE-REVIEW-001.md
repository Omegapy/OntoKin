# Freeze review 001 of gate MR (C271-P36, stage S6)

Reviewer: W3 (freeze review 001), a subagent in a fresh context with the session's model, for Director
`c271-p36-14f7f8b219db`. I took no part in any earlier stage and reviewed none of them. I ran nothing
that the freeze is about. Times are UTC.

Labels: `<worktree>` the C271 worktree at B; `<clone>` the owner's clone; `<local>` the data root beside
the clone; `<E>` = `<local>/c271-p36/evidence`; `<F>` = `<local>/c271-p36/workers/W2-freeze-001`;
`<A1>` = `<E>/mr-001-r1`; `<home>` the account's home; `<tmp>` the per-user temporary directory;
`<framework>` the framework interpreter's version directory. The JSON record is
[FREEZE-REVIEW-001.json](FREEZE-REVIEW-001.json).

## Verdict

**REJECT_WITH_MANDATORY_FINDINGS.** The Director may not run S7 as frozen.

R1, as frozen, refuses in the driver's preparation at B. That happens before the unit stage, and it
happens every time (FZ-01). No change to the freeze can avoid it. Its cause lies in the
implementation, so MR-PLAN section 9 stops MR before S7. The rest of the freeze is carefully built.
Integrity, the configuration, the commands, the checker steps and the attributions all check out,
and I recomputed them from the bytes. FZ-02 to FZ-09 are nonmandatory inputs for the next freeze.

## Digests, computed from the bytes

| File | SHA-256 | Bytes |
| --- | --- | ---: |
| `<F>/FREEZE-001.json` | `11555730a5d153d4155bd730f288d8478fff2933a4587c4fef0a35940592ab66` | 641,427 |
| `<F>/SHA256SUMS.txt` | `a4fd0dc3ddfe2cd1657923ec7a20211cae3440ccdc94518a98d8490d751325d4` | 13,619 |
| `<F>/config/readback-config-001.json` | `e700edefb0a933f784d9fcf180770ef6d4675ae2cf8b7d6008ea0a126f5f916d` | 2,295 |
| `<local>/c271-p36/director/run/run_once_p36.sh` | `9154f181cfa7c8648c21b31a1f309af43f9b2b5046df1656a124a4b6b55e07a7` | 3,629 |

The JSON record carries the freeze's and the configuration's digests at the pointers that the freeze's
`deferred_arguments` name, `/freeze/sha256` and `/configuration/sha256`. They are records, not an
approval: `/s7_may_run_as_frozen` is `false`.

## Findings

### FZ-01 (mandatory): R1 cannot pass its preparation at B

**What happens.**
1. In a qualifying run the driver copies only `SOURCE_DIRS` and `ROOT_FILES` into its workspace
   (`tools/check_local.py:47-50`, `:340-346`).
2. It then builds the workspace's Git index from B's whole tree (`:298-318`, `git read-tree B`).
3. It derives the workspace binding (`:779-782`, `:609-612`). The provider validates the derived
   selection there (`current_host_readback_v02.py:913`, `:943`), with `_verify_source(derived=True)`
   (`:866`).
4. That check refuses every `git status --porcelain=v1 --untracked-files=no` line, except a path
   that `immutable_workspace_inputs` drops, which means only the generated examples (`:471-474`;
   `check_local.py:127-132`).

B tracks seven entries that the copy leaves out: `.claude/.gitignore` and six symbolic links under
`.claude/skills/`. In the workspace they are deleted. So the first status line is
` D .claude/.gitignore`, and the provider raises CH-SOURCE "Dirty source:  D .claude/.gitignore". The
alternative is CH-SOURCE "Bounded source Git inspection failed", if the status takes longer than its
5 s allowance (`:461`).

**Evidence.**
- **B's tree, read from Git's files.** B's loose commit names tree `0935162c` (I hashed the object
  bytes and checked them). The tree's root has an entry `.claude`.
- **The index.** It has version 2 and 23,012 entries, and its cache-tree root is `0935162c` with
  23,012 entries. Exactly 7 entries lie outside the copied set: the seven above
  ([b-tree-check](outputs/b-tree-check.json), [index paths](outputs/index-paths-b-2.json)).
- **The driver's inventory of B,** which I recomputed with a copy of its algorithm:
  `sha256:e7f1c4b5…`, 23,005 files ([driver-inventory-b](outputs/driver-inventory-b.json)).
- **Main's own record of the same copy.** Both baseline summaries record
  `/workspace_git/tracked_worktree_status` as exactly these seven ` D` lines. The `.claude/` subtree
  is the same in main 8e847c15 and in B ([tree diff](outputs/tree-diff-main8e847c15-vs-b.json)).
- **The run's end.** `run()` catches the refusal (`check_local.py:816-819`). The summary then has:
  - status `failed` and an `error` member;
  - `readback_selection.status` `original_verified`, with `preparation_or_execution_error`;
  - `steps: []`, with all seven steps not executed;
  - exit 1.

  R1.X is then NOT_MET. Under stop rule 4, R2 never starts, and S7 ends after R1.Y and R1.Z. The
  freeze's own classification is IMPLEMENTATION, and MR-PLAN section 9 then stops MR.
- **Why no earlier stage caught it.**
  - The author's validation stopped at the first Git read, and its `not_run` names the derivation.
  - MH's cohort ran at the worktree, with `parent` null.
  - MI's driver tests use fixture repositories.
  - Gate MB's review noted that `.claude` is not copied, but did not connect it to the provider's
    status check.
  - W1's inventory cites main's workspaces as clean of bytecode, but not their status.

**Required change.**
- Do not run S7 under freeze 001. Record the blocker under MR-PLAN section 9: the cause is the
  implementation, so MR stops at S6.
- The correction belongs to a later phase. It decides, under contract section 7 and MC19, how a
  derived workspace treats tracked paths that the driver does not copy. For example, the check could
  admit the deletion of exactly those paths, or the copy could account for them. Its controls must
  exercise the derived route on a tree that tracks such paths.
- A corrected commit needs a new observation plan, HOST and freeze, and their reviews.
- If the Director wants this refusal executed as evidence, that needs a revised freeze whose R1
  expects this refusal and its reason, and which states how R2 is handled. That freeze needs its own
  review, and it cannot meet MR.
- R2 does not take the selection route, so this finding does not affect it. But under MR-PLAN
  section 1 and stop rule 4, R2 follows R1. Whether to run R2 alone is a plan decision, outside this
  review.

### FZ-02 to FZ-09 (nonmandatory)

- **FZ-02. The derived route's Git timing is not established.**
  - The cost:
    - `read-tree` leaves the workspace's index without stat data.
    - Every Git read runs with `GIT_OPTIONAL_LOCKS=0`.
    - So each provider status in the workspace hashes every copied tracked file again:
      1,169,653,662 bytes in 23,005 files.
  - The allowance:
    - Each provider Git read gets `min(5 s, remaining)` (`:456-466`).
    - The unit process makes 12 selection checks, and 9 of them fall inside the case clock.
    - The case clock leaves 28 s for two full selections before each start (`:1019-1030`,
      `:1089-1105`).
  - The evidence: MH's 0.57 s per selection was measured at the worktree, whose index has stat data.
    No record times a status in a workspace.
  - The next freeze states that time with its basis, or states the margin as a risk.
- **FZ-03. No independent check of the checker's bytes comes before P01.**
  - P00 verifies only `<F>`'s own sums.
  - At P01 the checker (`eb96aa1a…`) checks its own binding. MH's FR-07 called that circular.
  - MH's freeze 002 carried FR-07 with a second sums file at P00. This freeze cites FR-07 for P00 but
    does not carry it.
  - Add the checker and the other tools that live in the worktree to a P00-level `shasum -c`, or add
    them to the `before_p00` comparison.
- **FZ-04. An attribution is not an acceptance.**
  - MI's 89 tests and D-18's two do not pass, and none of them exists on main.
  - Under MR-PLAN section 9, an attributed failure is not a finding, so R1.Y MET no longer signals
    them.
  - The comparator still lists them as not passing, so nothing is silent in the records.
  - State in `attributions.rules` that each one still needs the R03 review's classification under
    OK-ENG-009 section 3 item 4. Have the audit list them as "attributed by record; classification
    required".
- **FZ-05. A preparation refusal does not make R1's Node starts unknown.**
  - When the summary records `steps: []` with nothing started, the Node count is 0. The driver's
    record establishes it, so it is not UNKNOWN as R1.F's exit-1 class says.
  - Distinguish this case.
- **FZ-06. The limits leave out two differences between MI's records and R1.**
  - MI ran each module alone, without any selection variable.
  - R1's unit process sets the derived selection pair for all 5,994 tests
    (`check_local.py:651-665`), in one process.
  - Add both to the limits.
- **FZ-07. The shell tool's own conditions are not recorded.**
  - The launch rule handles approvals and refusals, but not whether the tool runs the command in a
    sandbox.
  - The whole suite has never run through the tool, and main's baseline was not run under it.
  - Record the tool's mode for R1 and R2, and treat a denial by the tool as a possible cause of an
    unattributed failure.
- **FZ-08. Three of R2's 307 main-derived rows rest on inputs that changed.**
  - Two are in `test_local_checks`:
    - the two methods' ASTs are equal on main and at B;
    - their helper `execute` changed, and they exercise `tools/check_local.py`, which changed too.
  - One is in `test_force_conformance`, which imports `check_local.inventory`.
  - Label these three "same record expected; inputs changed".
- **FZ-09. The privacy rule for S10 should name the raw logs and the command records.**
  - When a 0.1.0 driver test fails, its mocked call list prints the parent environment. MI redacted
    one such line in each run. D-18's tests fail in R1 and R2, so both raw logs will hold the home and
    account values.
  - The command records hold `HOME`, `LOGNAME` and `USER`.
  - State the rule:
    - raw logs are never copied, only their digests;
    - every argv and environment value is replaced by its label;
    - each portable file is searched before S10 publishes it.

## The thirteen points

1. **Integrity: MET.**
   - The sums file: 126 of 126 lines check, and they cover every file in `<F>`.
   - The bindings, as they are now: 83 of 83 bindings and the 3 host facts match, and `.config/git`'s
     `config` and `attributes` are absent ([verify-bindings](outputs/verify-bindings-2.json)).
   - The 5 trees hold no bytecode and no `.DS_Store`, and both attempt roots are still absent.
   - The 7 ancestors match, and the 162 absent paths are absent.
   - The wrapper's bytes equal the freeze's binding.
   - `<E>` holds only `observe-001` and its eight capture files.
   - The fixed state:
     - the boot is `C90010BA-…` and the umask 022;
     - my own walk shows the framework tree (3,788 entries, 414 `.pyc`) and the `.venv` (345 entries,
       none) equal to HOST's frozen inventory;
     - the 644 source bindings equal the worktree's bytes;
     - the worktree holds exactly its 23,012 tracked entries, with no bytecode and nothing newer than
       the freeze.
2. **The configuration: MET as a configuration** ([config-check](outputs/config-check.json)).
   - Keys: it has the closed config/0.2.0 keys, and `parent` is null.
   - HOST: bound by path, `858ef72a…`, 18,420 bytes, mode `0o600`.
   - Descriptors (HR-02): the source and reader-tree descriptors equal HOST's, path included.
   - Runtime: it equals HOST's, `v24.22.1`.
   - Contract and adoption (PR-06): both are bound at their worktree paths. The adoption record is
     `872312ed…`, 5,396 bytes, `0o644`, the value in PLAN-REVIEW-001.
   - Methods: their nine bodies equal the provider's `ORIGINAL_BODIES`.
   - Discovery (MC28): 5,994 sorted unique IDs, the seven included. That is B's discovery, which
     equals MH's 5,587 IDs plus exactly the 407 additions ([discovery-check](outputs/discovery-check.json)).
   - Evidence root: `<A1>`, which is absent now and lies outside the source.
   - HR-01 is met in `bindings`: HOST, `completion.json` (OBSERVED_UNAPPROVED, finalized) and
     `result.json`.
   - Using this configuration in R1 fails for FZ-01.
3. **What can refuse R1: FINDING FZ-01.**
   - These checks hold now, in order:
     - the configuration's identity and digest (MC21);
     - the Git binding, by bytes;
     - HOST's state and boot;
     - HOST's environment record (MC31 reads that record only);
     - the Python inventory (MC32);
     - the runtime, the inspections, the labels and the claims;
     - the source at the worktree, whose five Git reads see a clean tree with exactly the tracked
       files;
     - the dependencies and the methods;
     - the output beneath `<A1>`.
   - The derived selection then refuses (FZ-01). The author's validation did not run the Git reads,
     the derivation or the cohort, and those leave open exactly this path, plus FZ-02's timing.
4. **Environment and `PATH`: MET, with the stated limits.**
   - The declared lists are as frozen. R1 gets `HOME`, `LOGNAME`, `PATH=/usr/bin:/bin`, `TMPDIR`
     (`<tmp>` in resolved form, with the final slash) and `USER`. R2 gets the same with `<tmp>` in its
     `/var` form.
   - Under the frozen `PATH`:
     - `git` resolves to `/usr/bin/git`, the dispatcher;
     - `uname`, `file` and `sh` resolve to the system's own;
     - `node`, `python3.12` and Git's `lfs` helper resolve to nothing.
   - No record of main's baseline `PATH` exists. Under this session's `PATH`, `git`, `uname` and
     `file` resolve the same. `node` (the package manager's), `python3.12` (a link to the same
     interpreter) and `git-lfs` are found there. D-P1's reading of U-28 and U-30 covers that
     difference.
   - Nothing can reach another Node, `ldd` (absent) or `codesign`/`otool` (present, but no start names
     them).
   - This kind of session sets none of the `LANG`, `LC_*`, `TZ`, `XDG_*` and `PLAYWRIGHT_*` variables.
     It does set `PYTHONDONTWRITEBYTECODE` and `GIT_EDITOR`, which `env -i` removes. The declared
     five do not depend on the session (Q-6).
5. **R1 and R2: MET as written.**
   - All 36 commands agree in their argv, cwd, environment files and digests, output paths, and the
     timer's exit file and bound ([commands-check](outputs/commands-check.json)).
   - `--timeout 7200` and the 10,800 s bound suit a unit stage of 1,000 to 1,500 s, and no bound rests
     on Node timing.
   - The launch is MH's: a background command beside its frozen bound timer. See FZ-07.
6. **The checker steps and the order: MET, with FZ-03.**
   - D02 evaluates P00 to P03 before R1, and P02 is HR-04's recheck immediately before R1.
   - R1.X, R1.Y and R1.Z run before R2.
   - Each of these is a frozen predicate:
     - MC22, in R2.C and R2.Y;
     - MC23: the seven methods, no fixture record, the cohort, the reader and the audit;
     - MC28: R1.C's join with discovery `c9e8fbec…`;
     - TR-09: R1.F's one-preserved-root rule, and R1.M;
     - TR2-01: the footer, the collector and `test_execution`;
     - D-P4: the trees at P01, D02, R1.Z and Q04;
     - D-P5: the inventory at P02, R1.I and R2.I.
   - The checker's phases fit MR's commands (Q-4).
7. **Expected outcomes and attributions: MET as exact records, with FZ-04 and FZ-08.**
   - **Recomputed.** I ran MR's collector on the retained logs:
     - all 94 MI-derived statements equal the frozen rows: 89 + 2 in R1, and 2 + MC22's 1 in R2
       ([mi-attribution-check](outputs/mi-attribution-check.json));
     - all 308 main-derived statements equal them too: 1 raw and 307 normalized
       ([main-attribution-check](outputs/main-attribution-check-2.json)).
   - **TR2-04 and TR2-03.** All 402 rows are not passing and agree with their own events. No ID
     repeats, in the rows or in the discovery.
   - **Coverage.** Every baseline record that does not pass is attributed, and so is every MI one
     except RI_L07 and RI_L08.
   - **The records' inputs.**
     - MI's logs carry CHECKS.json's digests.
     - MI's final-003 commit `7b759de0` and B have identical blobs and modes for all 5,511 files under
       `tests/`, `prototypes/`, `tools/`, `ontokin/`, `fixtures/`, `examples/`, `schemas/` and
       `pyproject.toml` ([tree diff](outputs/tree-diff-mi-final003-vs-b.json)).
     - The first lines hold no run path, module prefix or line number.
   - **Counts.** R1 has 92 rows: 1 unchanged and 91 new. R2 has 310: 307 + 3.
   - **S8's changes:** R1 runs the trio, and R2 has one setup error where main has three skips.
   - **R2's `/var` class** is applied by the audit and the R03 review, and stays visible.
   - Nothing is exempt, and every attributed failure stays listed as not passing.
8. **Starts: MET as planned.**
   - R1 makes 3 Node starts, all through the provider with receipts, and R2 makes none.
   - There is no other bounded start, and the uncounted starts are given as magnitudes.
   - Nothing starts `ldd`, `codesign`, `otool` or another Node.
   - Under FZ-01, R1 makes no Node start at all (FZ-05).
9. **Stop rules, the overrun procedure and failure capture: MET.**
   - Launch and overrun follow MH's rules, with its six overrun steps.
   - Only processes of established identity are stopped.
   - FAILURE-CAPTURE stays unchanged and is read as PR-01's disposition says.
   - The FC-K4 additions read the procedure's kinds; they do not edit it.
   - Q-7 is agreed.
10. **Carried findings and decisions: MET.** PR-01, PR-06, HR-01 to HR-08, TR-09, TR2-01, TR2-03,
    TR2-04, D-P1 to D-P7 and F-1 to F-5 are applied where the freeze says. MH's FR-07 is cited but
    not carried (FZ-03).
11. **The author's starts and deviations: MET.** None of them could change a bound tree, the
    worktree, the evidence or a frozen input. The live trees, the worktree and `<E>` confirm it.
12. **The open questions:** answered below.
13. **Privacy: MET for the notes,** which use labels only. FZ-09 covers S10.

## Answers to Q-1 to Q-12

- **Q-1.** Attribute them by exact record. The retained logs were made on this host, at code and test
  bytes equal to B's, and all 89 recompute exactly. But an attribution is not an acceptance, so the
  R03 review must classify each one (FZ-04).
- **Q-2.** Agreed. R2's `/var` directory can change them, so R2.V's comparison with R1's own records is
  the right source.
- **Q-3.** Agreed: leave both unattributed.
  - MI's `ModuleNotFoundError` comes from its per-module invocation.
  - RI_L08 requires the rtld-paths suite to pass in process. MI recorded 38 failures and 2 errors
    there, so RI_L08 will probably not pass.
  - RI_L07 depends on `test_current_host_libc_static_tls_flags_v01`, which has no record on this host.
  - Either one not passing is a finding.
- **Q-4.** Admissible.
  - The checker is committed at B and was reviewed by MH's freeze reviews 001 and 002.
  - It is bound by path, SHA-256, size and mode, and it starts nothing, so P07 section 3 is met.
  - MR-PLAN section 5 names three reused pieces, so the Director should record the fourth as a plan
    decision.
  - Carry FR-07 (FZ-03).
- **Q-5.** Adequate. T bounds each step only, and no test reads it. The outer bound exceeds one hung
  step plus the rest. No bound rests on Node timing. FZ-02 covers the provider's fixed 30 s case
  clock.
- **Q-6.** Acceptable as a stated limit. No code reads these variables by name, this kind of session
  sets none of them, and CPython's C-locale coercion applies the same way in both.
- **Q-7.** Agreed. Findings never stop S7. R2 after an unqualified R1 (with R1.X and R1.Z MET) starts no
  Node, and it still gives MC22 and the `/var` comparison.
- **Q-8.** Agreed. `<A1>` keeps the cohort and the driver output in one directory, which R1.L lists
  whole. P07 section 2's ancestors stay those of `<E>`.
- **Q-9.** Sufficient. I recomputed the comparison from the bound documents. B is fixed, and R1.C joins
  R1's log with the same list.
- **Q-10.** Agreed. Git reads `<home>/.config/git/ignore` by default, and `GIT_CONFIG_GLOBAL=/dev/null`
  does not switch that off. The file feeds the untracked listings of both the driver and the provider.
- **Q-11.** Keep the exact count. A different count is exactly the signal of a finding, and R1.Y records
  it without stopping S7.
- **Q-12.** Sufficient, with FZ-09.

## What I started, and my deviations

- **Shells.** One zsh per tool call, about 85 in all. They ran read-only utilities. The only exceptions
  were `mkdir`, `sed -i` on my own scripts and `rm` of my own files, all in this directory. They also
  ran `/usr/sbin/sysctl -n kern.bootsessionuuid` once, and `/usr/bin/env -i` with `shasum` once.
- **The framework interpreter.** About 65 starts as `python3 -I -S -B`, for my scripts and short
  readers. They read Git's object and index files directly, and loaded MR's collector from its
  committed path.
- **Deviation 1.** One start as `python3 -`, with an empty program and without `-B` on its command
  line. `PYTHONDONTWRITEBYTECODE=1` was set in the inherited session environment. My walk afterwards
  shows both Python trees still equal to HOST's inventory
  ([after the deviation](outputs/python-trees-after-deviation.json)).
- **Deviation 2.** I edited three of my scripts after their first run. Two now write labels instead of
  machine values; the third reads the temporary directories from the freeze. I ran each again into a
  `-2` output, with the same results. I then removed the first outputs that held machine values,
  together with my convenience copies of the freeze's parts.
- **Never started:** Git of any kind, Node, `ldd`, `codesign`, `otool`, the observer, the routine
  driver, a unit test, MR's tooling suite, a download or install, Finder, or a child agent.

[SHA256SUMS.txt](SHA256SUMS.txt) covers every file I wrote.
