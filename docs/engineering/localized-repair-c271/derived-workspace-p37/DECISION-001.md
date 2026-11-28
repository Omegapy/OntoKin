# C271-P37 decision 001: the derived workspace's source check and its Git timing

**Identifier:** C271-P37-DECISION-001.
**Author:** W1, the independent author of stage S3 of the [correction plan](CORRECTION-PLAN.md), for Director
`c271-p37-08beec34eb0a`. W1 is a Claude Code subagent in a fresh context. It wrote none of MI's
implementation, the contracts, gate MR's records or the freeze review.
**Base:** the declaration commit `2f728998456c829f3cdc13bbf72d6dd805fefa36`, tree
`36e2950b67a859f8b1ab04fc901627497f31cad7`.
**Decision state:** the author's decision for this phase. The Director reads it before S4, and the
phase's independent review (S7) reviews it with the candidate. It is not an amendment of
`ontokin.current-host-readback/0.2.0` (section 2).
**Labels:** `<local>` is the data root beside the clone. Times are UTC.

## Decision in brief

- **FZ-01.** In a derived workspace, the 0.2.0 provider's source check admits one more kind of status
  line beside the driver's generated examples: ` D <path>`, the unstaged deletion of a tracked path that
  lies outside the driver's copied set, by the driver's own definition. It is refused when a file of
  the driver's recorded copied inventory has the same name up to case. Every other status line and
  every untracked name still refuses there, and the original route still refuses every line.
- **Basis.** The rule stays within P05 section 3 and MC19. Such a path is neither source of the
  workspace nor executable there, and the set it is measured against is the driver's. **No amendment
  is needed.**
- **FZ-02.** In the derived workspace, each status read used about half of its 5 s allowance, and a
  qualifying run makes 13 of them. That margin is not adequate. The driver therefore refreshes the
  workspace's index once, after its copy, with `git update-index -q --refresh`. Status reads then took
  0.07 to 0.09 s. The ordinary driver makes one more Git start. Its outcomes, its summary fields and
  their values stay as they are.

## 1. The rule

### 1.1 Where it applies

`_verify_source` in `prototypes/static_tray_v01/current_host_readback_v02.py` runs with `derived=True`
when `_selection` checks a configuration whose `parent` is not null:
- once at the driver's derivation, in `derive_workspace_binding`;
- in the unit process for every derived selection: twice at setup, three times in each of the three
  cases (preflight, launch and postflight), and once in the cohort's accounting.

Each time, `_verify_parent` first proves the parent. It now also returns the driver's recorded
copied inventory, the workspace binding's `source_before` document. That document is the driver's
`inventory()` of the original checkout. `_selection` passes it to `_verify_source` as `copied`.

The five Git reads are unchanged: `rev-parse --show-toplevel`, `rev-parse --verify HEAD^{commit}`,
`rev-parse --verify <commit>^{tree}`, `status --porcelain=v1 --untracked-files=no` and
`ls-files --others --exclude-standard -z`. Each runs the bound Git, with `min(5 s, remaining)`.

### 1.2 Status lines

**The format.** Porcelain v1 prints each line as two status letters `XY`, a space and the path. A
rename or a copy prints `XY ORIG -> PATH`. Git quotes a path C-style, in double quotes, when it holds
a double quote, a backslash or a control character, and under the default `core.quotePath` also a
byte from 0x80 on. The workspace's repository has its own fresh configuration, so the default applies
there. The check reads each line's path as `line[3:]`.

**What is admitted.** In a derived workspace a line is admitted in exactly two cases:
- **Rule A, unchanged.** The path is one of the driver's generated examples, which
  `immutable_workspace_inputs` drops, whatever its `XY`. It must not be quoted or contain ` -> `.
- **Rule B, new.** All of these hold:
  1. the line starts with exactly ` D `: the index entry equals the commit's, and the file is absent
     from the workspace;
  2. the path is not quoted and contains no ` -> `;
  3. no component of the path is empty, `.` or `..`;
  4. `tools.check_local.copied_source_path(path)` is false, so the path lies outside the copied set;
  5. the check holds the recorded copied inventory; without it no deletion is admitted;
  6. no file of that inventory has the path's name under case folding (`str.casefold`).

**What is refused.** Every other line refuses with `CurrentHostBindingError`, code `CH-SOURCE`, reason
`Dirty source: ` followed by the whole line.

| Line | Derived route | Original route |
| --- | --- | --- |
| ` D P`, with P outside the copied set (rule B) | admitted | refused |
| any `XY` for a generated example, not quoted, no ` -> ` (rule A) | admitted | refused |
| ` D P`, with P inside the copied set | refused | refused |
| ` D P`, with P outside, when a recorded copied file is P up to case | refused | refused |
| a staged change: `D ` (a staged deletion), `M `, `A `, `T `, `MM`, `AD`, `MD` and the other staged forms | refused | refused |
| an unstaged change other than a deletion: ` M`, ` T`, ` A`, outside the copied set included | refused | refused |
| unmerged: `DD`, `AU`, `UD`, `UA`, `DU`, `AA`, `UU` | refused | refused |
| a rename or a copy: `R` or `C` in either column, and any line holding ` -> ` | refused | refused |
| a quoted path, which starts with `"` | refused | refused |
| a path with an empty, `.` or `..` component | refused | refused |

The rows after the first two concern paths that are not generated examples. Rule A admits a
generated example's line in any form, unquoted and without ` -> `, as before.

A malformed record refuses with code `CH-WORKSPACE`, reason
`The copied-source inventory record is malformed`, before any Git read. A record is malformed unless
it is an object whose `files` member is a list of objects with a string `path`.

### 1.3 Untracked names (unchanged)

Every name from `ls-files --others --exclude-standard -z` refuses with code `CH-SOURCE`, reason
`Untracked source input: ` followed by the name. That includes names outside the copied set. The only
exception, unchanged, is a generated example in a derived workspace. The `-z` form gives raw names, so
quoting does not arise there.

### 1.4 The original route (unchanged)

With `derived=False` every status line and every untracked name refuses, whatever record is given. The
driver checks the original selection at the original checkout before it copies anything
(`prepare_readback_selection`). A qualifying run therefore derives only from a clean checkout.

## 2. The basis

**P05 section 3** ([contract](../current-host-p05/CONTRACT.md#3-source-identity-and-isolated-workspace)) says
that preparation "must fail on dirty or untracked executable source, extra executable inputs, missing
source or changes after the inventory was frozen". A line that rule B admits is none of these:
- **Not source of the workspace.** The path lies outside the copied set. It is therefore not in "the
  complete copied immutable-source inventory" whose equality the derivation records:
  `derive_workspace_binding` requires `source_before == workspace_inventory == inventory(workspace) ==
  inventory(source_root)`, and `_verify_parent` proves it again at each check.
- **Not executable there.** The file is absent from the workspace, so nothing there can run or read it.
- **Not dirty.** `X` is a space, so the workspace's index still holds the commit's entry. The original
  checkout's own check, which refuses every line, found the path unchanged.
- **Not an extra input.** An absent path adds nothing. A path present with other bytes or another type
  (` M`, ` T`) refuses, and so does every untracked file.
- **Not missing source.** The source that the configuration identifies is its complete
  execution-relevant inventory, the 0.2.0 source set. `_verify_source` binds it file by file in the
  workspace before any Git read, so a missing file of the source set always refuses through that
  binding (`CH-SOURCE`, `Complete CPU source inventory differs`).
  - When the file lies inside the copied set, rule B's condition 4 would refuse its deletion line as
    well.
  - A file of the source set can lie outside the copied set, under a name that `ignored()` matches,
    such as `ontokin/.env`. The copy leaves it out, and rule B alone would admit its deletion line. It
    refuses through the binding alone, which control P37-C24 of the
    [frozen controls](CONTROLS-FROZEN.json) freezes.

  The check fails closed either way. The Director found all 644 files of HOST's source inventory at
  gate MR's commit inside the copied set, so the second case does not arise there.

P05 section 3 also defines the derivation: "`check_local.py` copies its source into an isolated
workspace", and the driver records "the identical commit/tree, equality of the complete copied
immutable-source inventory". The workspace keeps the commit's identity in its own repository, through
`read-tree` of the whole commit in `prepare_workspace_git`. The deletion lines follow from these two
required facts together. They do not change any copied byte.

Its last rule reads: "Any approved generated-file exclusion must be exactly the existing driver's
exclusion, with original source bytes preserved; it is not a new executable-source exception." Rule A
stays exactly the driver's exclusion. Rule B is no exclusion of source. It admits nothing inside the
copied set and no file that exists in the workspace. It admits only the absence of tracked paths that
the driver's existing definition never copies.

**MC19** of the 0.2.0 contract refuses "other checkout, dirty or untracked executable source, changed
provider or probe, or an unbound Git executable". Each case stays refused:
- another checkout: the provider's own root and `rev-parse --show-toplevel`;
- dirty executable source: every line for a path inside the copied set apart from the generated
  examples, every form other than ` D `, and the file-by-file binding of the source set;
- untracked executable source: every untracked name apart from a generated example;
- a changed provider or probe: the source set's binding;
- an unbound Git: the binding before any read.

**The contract's other terms.** Contract section 1 keeps "the isolated-workspace derivation" of P05
sections 2 and 3. The contract names no rule for status lines; the line rule is the implementation's.
Before this decision that rule was stricter than the contract, in a way that made the contract's own
derivation impossible for any tree that tracks a path outside the copied set. Gate MR's commit and the
declaration commit both do, with seven `.claude/` entries, and main's baseline summaries record the
same seven deletions. MC21 and MC29 are unaffected: the selection rules are unchanged, and the checks
run at the same moments.

**Conclusion.** The rule stays within P05 section 3 and MC19, and **no versioned amendment is
needed.** An amendment would be needed to admit any change inside the copied set or any untracked
name, to widen the generated-example exclusion, to relax the original route, or to change what the
copied set means. This decision does none of these.

## 3. One definition of the copied set

- **The definition.** A repository-relative path, in Git's `/`-separated form, lies in the copied set
  when its first component is one of `SOURCE_DIRS` and no component is matched by `ignored()`, or
  when it is one of `ROOT_FILES`. `tools/check_local.py` states this once, as
  `copied_source_path(name)`. It is the expression that `git_metadata` already used for its
  `untracked_source_files` record. `git_metadata` now calls the function, so that field is unchanged.
- **The driver's uses.** `prepare_workspace` copies, and `source_files` inventories, by walking
  `SOURCE_DIRS` and `ROOT_FILES` with `ignored()` applied to each name. They use the same constants
  and the same predicate. A focused test checks on one fixture tree that the function, the inventory
  and the copy select exactly the same files.
- **The provider's use.** `_verify_source` imports `copied_source_path` from the driver, as it already
  imported `git_read` and `immutable_workspace_inputs`, and calls it at the check. In the unit process
  that is the workspace's copy of the driver, which the 0.2.0 source set binds by its bytes
  (`tools/check_local.py` is one of `SOURCE_FILES`). Its case-folded comparison uses the driver's own
  record of the copy, the derivation's `source_before`. The provider names no directory, file, pattern
  or path of its own.
- **No second set of exceptions.** The provider admits only rule A, the driver's generated exclusion,
  and rule B, the complement of the driver's copied set. The comparison with the record can only
  refuse. The comment at the check now reads: "Do not introduce a second set of generated exceptions,
  or of copied paths, here."
- **A path that the copy refuses is still refused.** A symbolic link inside `SOURCE_DIRS` lies inside
  the copied set: `copied_source_path` is true for it.
  - The driver refuses it before any derivation, so no workspace exists. `source_files` raises "Source
    file is a symbolic link", and the copy raises "Cannot copy a source symbolic link".
  - If a workspace that lacks it ever reached the provider, its ` D` line would refuse through
    condition 4. A refusal by the copy is not an exclusion from the copied set.
  - The same holds for any other entry inside the copied set that is not a regular file, such as a
    submodule.
  - The six links that rule B admits lie outside the copied set, under `.claude/skills/`, which the copy
    never reaches.

## 4. FZ-02: the derived route's Git timing

### 4.1 The measurement

The Director's S2 record `<local>/c271-p37/measure/MEASURE-001.json` (SHA-256
`753415b5e390303ad060d433c01365742bce1419f37e91b70b42307c98660c69`) holds:

| Read | Original checkout | Workspace, before the refresh | Workspace, after the refresh |
| --- | --- | --- | --- |
| status | 0.049, 0.064, 0.074 s | 2.548, 2.502, 2.455, 2.500, 2.495 s | 0.075, 0.083, 0.092, 0.092, 0.067 s |
| untracked names | not timed | 0.079 to 0.086 s | 0.069 to 0.091 s |
| `update-index -q --refresh` | none | none | one run: 2.456 s, exit 0, no output |

- **The copy:** 13.1 s, 23,145 files and 1,173,504,904 bytes outside `.git`. The workspace's status
  showed exactly the seven `.claude/` deletions and no untracked name.
- **The cost:** without stat data, each status read hashes every copied byte again, at about
  0.47 GB/s here.
- **W1's reading of the measured workspace's index** (read directly, without Git): version 2 and 23,152
  entries, exactly seven of them outside the copied set (`.claude/.gitignore` and six links under
  `.claude/skills/`). No entry is a case variant of a copied root, has an ignored component, needs
  quoting, is inside the copied set without being a regular file, or collides with another entry up
  to case.

### 4.2 The limits

- **Each Git read:** `min(5 s, remaining)`.
- **Reads per qualifying run:** 13 derived status reads. One is at the derivation. The unit process
  makes 12: 2 at setup, 9 inside the case clocks and 1 in the cohort's accounting. The driver's own
  status reads of the workspace, for `workspace_git` and for the derivation's Git identity check, have
  the driver's 10 s each.
- **The case clock:** for each case, the preflight and launch selections run against the 28 s stage
  end, and the checker must finish by then too. The postflight runs against the 30 s clock end.
  - MH measured each case's ledger at the worktree, whose index has stat data: 1.94 to 1.96 s, of
    which the checker took 0.24 s and each selection about 0.57 s.
  - In a derived workspace without stat data, each selection adds about 2.50 s of status and about
    0.04 s for the two inventory documents of the parent proof. W1 timed the parent proof
    synthetically with the real tree's 23,145 paths: 0.042 to 0.045 s.
  - That gives about 3.1 s per selection: about 6.2 s before each start, and about 9.6 s per case.

### 4.3 The judgment

- **The case clock** leaves about a threefold margin (9.6 s against 28 s and 30 s). That alone would be
  adequate.
- **The setup and cohort selections** have no clock of their own; each of their reads has 5 s.
- **The per-read allowance:** each status read takes 2.46 to 2.55 s of its 5 s, about half, and a run
  makes 13 of them. **That is not adequate:**
  1. It rests on one measurement, taken right after the copy, while the copied bytes were in the page
     cache. In a qualifying run the readback cohort runs inside a unit stage of 1,000 to 1,500 s, and
     the workspace lies on the external volume beside the clone.
  2. The cost grows with the copied bytes: 1,169,653,662 at gate MR's commit and 1,173,504,904 at the
     declaration.
  3. The hashing depends on the processor's load and speed, and on any background indexing of a fresh
     copy. Nothing in the run controls these.
  4. A read that exceeds 5 s refuses (`CH-SOURCE`, `Bounded source Git inspection failed`), and P05
     section 7 admits no automatic retry. Any one of the 13 reads would fail the qualifying run.

### 4.4 The correction

- **What.** `tools/check_local.py` gains `refresh_workspace_index(workspace)`, one
  `git update-index -q --refresh` in the workspace. It runs through `git_read`, that is, the bound Git
  or the `PATH` Git resolved once, with a 120 s allowance like the fetch.
- **When.** `prepare_workspace` calls it when the source has Git. It comes after
  `prepare_offline_workspace`, which configures any LFS filters "before status checks", and before the
  first status read.
- **On failure.** It raises `ValueError("Cannot record the isolated workspace's index stat data: <error>")`.
  The run's preparation then fails before any step, as for every other workspace Git failure.
- **Why the check keeps its strength:**
  1. the refresh records stat data only for entries whose copied bytes hash to the commit's objects;
  2. it changes no entry's path, mode, object or stage (`ls-files --stage` is identical);
  3. a changed, missing or retyped file stays unrefreshed and shows as before;
  4. later reads compare stat data, including the change time, which programs cannot set directly, and
     hash again on any mismatch. Status works this way in the original checkout, on the original route.
- **The margin after it:** 0.067 to 0.092 s of 5 s, more than fiftyfold. By the same estimate as in
  section 4.2, a derived selection then costs about 0.7 s, and a case about 2.3 s.

### 4.5 Its effect on the ordinary driver and on main's recorded fields

- **Starts.** Every run whose source has Git makes one more Git start:
  `<git> -c core.fsmonitor=false -C <workspace> update-index -q --refresh`. Runs without Git are
  unchanged. The next MR attempt's start inventory counts the added start.
- **Time.** About 2.46 s at this tree. The driver's own `workspace_git` status read falls from about
  2.50 s to about 0.08 s, so a run takes about as long as before.
- **A new failure.** Only a failed refresh itself, which fails preparation visibly.
- **The summary.** No field is added, removed or renamed, and `workspace_git` keeps its values:
  - `available`, `local_head` and `local_tree`;
  - `tracked_worktree_status`, with the same ` D` lines. At the declaration commit these are the seven
    `.claude/` deletions that main's baseline summaries record;
  - `untracked_source_files`, `head_is_base_revision`, `source_inventory_includes_untracked_files` and
    `remote_head_verified`;
  - `index_basis: "source_commit_tree"`, `copied_worktree_changes_preserved: true` and
    `source_staging_preserved: false`.

  `workspace_storage`, `source_inventory`, the steps, the end gate and every outcome are unchanged. A
  focused test compares a refreshed and an unrefreshed workspace and finds the same entries and the
  same `git_metadata` record.

## 5. What stays unchanged

- **The generated-example exclusion:** `GENERATED_EXAMPLES`, its patterns, `immutable_workspace_inputs`,
  its use at the driver's end gate and rule A in the provider, which still refuses renames and quoted
  names.
- **The untracked-input refusal**, on both routes, apart from a generated example in a derived workspace.
- **The original route:** every status line and every untracked name refuses.
- **The provider's other checks:** the five Git reads and their order, their allowance and the mapping
  of their errors; the binding of the 0.2.0 source set; the parent proof; and the commit and tree
  checks.
- **The 0.1.0 provider.** `current_host_readback_v01.py` is unchanged, and its `_verify_source` still
  refuses these deletions in a derived workspace. This is a **recorded follow-up of the Linux route**,
  which does not run in local mode (P30-EXECUTOR-001). When that route resumes, it needs the same
  correction, under the 0.1.0 contract's own process. Until then it shares only the driver's faster
  status reads.
- **The driver:** its copied set (`SOURCE_DIRS`, `ROOT_FILES`, `IGNORED`, `ignored()`), its copy, its
  inventory, its summary fields and their meanings, and its ordinary outcomes. The one exception is
  FZ-02's added Git start.
- **MI's frozen controls:** `CONTROLS-FROZEN.json`, its refreezes and
  `tests/test_current_host_readback_controls_v02.py` are untouched. Their MC19 cases exercise the
  original route (`derived=False`), which is unchanged, and the module passes all 151 tests.
- **Every existing test:** no expectation changed. In both test modules, every member that existed
  before is unchanged (W1's evidence `COMPARISON.json`).
- **The contract, P33-AMENDMENT-001 and the adoption records.**

## 6. Risks and limits

- **macOS's case-insensitive file system.** On such a volume the driver's copy can reach a tracked
  path that is a case variant of a copied one: `Tests/x.py` through `tests`, or `readme.md` through
  `README.md`. Its later deletion in the workspace would show as ` D Tests/x.py`, outside the copied
  set by name.
  - Rule B's condition 6 refuses it, because the driver's record holds a file with that name up to
    case. The driver's end gate over the whole copied set would also catch it, and so would the
    provider's binding when the file belongs to its source set.
  - The comparison covers regular files only, since the record lists only those. A case-variant entry
    that is not a regular file is not compared.
  - At the declaration commit no tracked name is such a case variant. Unicode normalization does not
    arise: every non-ASCII name is quoted, and quoted names refuse.
- **Paths with special characters.** Git quotes names with a double quote, a backslash, a control
  character or a byte from 0x80 on, and some versions also quote spaces. Quoted names refuse, and
  this decision does not decode them. A tree that tracked such a path outside the copied set would
  refuse on the derived route, which fails closed. At the declaration commit no tracked name needs
  quoting. An unquoted name with a space is read whole, and a name holding ` -> ` refuses. The
  provider splits lines with `splitlines()`; the Unicode line breaks that it also splits on occur
  only in names that Git quotes.
- **A staged change.** Any `X` other than a space means that the workspace's index no longer holds
  the commit's entry, so it refuses for every path. Rule A still admits a generated example's staged
  change, as before.
- **A deleted copied file.** ` D` for a path inside the copied set refuses. So does one for a case
  variant of a recorded copied file.
- **A tracked file that the copy cannot reach.**
  - Outside `SOURCE_DIRS` and `ROOT_FILES`, as the seven `.claude/` entries are: admitted, as ` D` only.
  - Inside a source directory under a name that `ignored()` matches, such as `tools/build/x.py`,
    `docs/_build/page.html`, a tracked `.pyc` or a `.env` file: outside the copied set, so rule B
    admits its line as ` D` only. That is the same `ignored()` that the copy applies. When such a file
    also belongs to the 0.2.0 source set, as `ontokin/.env` would, the check still refuses, through the
    source set's binding alone (P37-C24; section 2). The declaration commit tracks none.
  - A symbolic link inside the copied set: the driver refuses the run (section 3).
  - A submodule entry inside the copied set: its ` D` line refuses.
- **The record.** Rule B depends on the driver's recorded inventory, which the parent proof
  authenticates through the workspace binding's digests. A derived check without the record admits no
  deletion, and a malformed record refuses.
- **The status format.** The rule relies on porcelain v1's stable `XY PATH` form.
- **Ignore files.** Since `.claude/.gitignore` is not copied, its patterns do not apply in the
  workspace. An untracked file under `.claude/` there is listed and refused, which is stricter.
  The account's global ignore file applies in both checkouts, as before (Q-10 of MR's freeze review).
- **The limits of stat data (FZ-02).** After the refresh, status relies on stat data, as it does in any
  ordinary checkout. A change that keeps a file's size, modification time and inode, made within the
  second of its last change time, can escape status on a Git that compares whole seconds; this is
  Git's racy-entry limit. Two checks do not use stat data and stay unchanged: the provider's
  file-by-file SHA-256 binding of its source set before each checker, and the driver's end gate over
  the whole copied set.
- **The measurements.** Both were taken once, on one host, at one tree size. The margin after the
  refresh is large, but a different host must still be timed. The refresh with LFS filters, where
  Git runs the configured clean filter, is not exercised: the tree has no LFS file and the host no
  client.
- **Test time.** The new real-Git tests add about 18 s to the provider module, and the driver module
  takes about 10 s, against 6 s before.

## 7. Implementation and tests

- **`tools/check_local.py`:**
  - `copied_source_path(name)`, which `git_metadata` now calls;
  - `refresh_workspace_index(workspace)`, which `prepare_workspace` calls.
- **`prototypes/static_tray_v01/current_host_readback_v02.py`:**
  - `_copied_names(copied)`;
  - `_verify_source(..., copied=None)` with rules A and B;
  - `_verify_parent`, which now returns the recorded copied inventory;
  - `_selection`, which passes that inventory on;
  - a paragraph in the module docstring.

  [interfaces/W1-CORRECTION.md](interfaces/W1-CORRECTION.md) gives the contracts, the fixture recipe,
  every case with its code and reason, and the 21 new test IDs. Six of them are in
  `tests/test_local_checks.py` and 15 in `tests/test_current_host_readback_provider_v02.py`.
- **The runs,** each with the prescribed command from the worktree root:
  - The four allowed modules, first at the base and then on the final code:
    `tests.test_local_checks` went from 33 to 39 tests, `tests.test_current_host_readback_provider_v02`
    from 49 to 64, `tests.test_current_host_readback_driver_v02` stayed at 22, and
    `tests.test_current_host_readback_controls_v02` at 151. Every run passed, and so did one run of all
    four together, with 276 tests.
  - Ten single-text mutations of the two implementation files, each followed by one test run. Each
    mutation was detected, and each file was restored and checked by its SHA-256.

  The evidence is in `<local>/c271-p37/workers/W1-correction/`.

## 8. What this decision does not establish

- It establishes no qualifying run, no gate MR and no R03. The next MR attempt does that at the
  corrected commit, with a new observation plan, HOST and freeze.
- It is not an independent review; S7 is.
- It provides no frozen controls; S4's independent author freezes those.
- Its tests are the author's focused tests.
