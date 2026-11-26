# C271-P31 re-review: revision 2 of the macOS arm64 contract design

**Candidate:** commit `90e8a5fbff6a43a1ed08284662e16f9aa5e96a83`, tree
`5373f0ca42045ec307327c5150a781cb654105df`, parent `4ee691ae…` (revision 1, rejected by
INDEPENDENT-REVIEW-001). Branch `work/c271-missing-import-digest-control`, worktree head at
`90e8a5fb`, no tracked changes. Main observed at `51223c9b…`. Reviewed 2026-11-26, about
05:15–05:30Z.

**Files reviewed** (`git show 90e8a5fb:<path>`, SHA-256 of the blob):

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| CONTRACT.md | 35,257 | `0cefe6de…7e06` |
| CONTRACT.json | 33,538 | `88ddcbee…4225` |
| READ-SET.json | 8,998 | `c355449d…cd99` |
| REVIEW-DISPOSITION.json | 5,252 | `499f1a8e…9cec` |

The full change is `git diff 4ee691ae 90e8a5fb`.

## 1. Checks run

| # | Check | Result |
| --- | --- | --- |
| K1 | Commit, tree, parent and diff stat | As above. Seven files change: CONTRACT.md and CONTRACT.json rewritten; READ-SET.json extended; REVIEW-DISPOSITION.json and the three INDEPENDENT-REVIEW-001 files added. PHASE.json is unchanged. |
| K2 | INDEPENDENT-REVIEW-001.md and `.json` against my originals in this directory | **Byte-identical** (`b4d3ff32…` and `feeddf53…`). |
| K3 | READ-SET recomputation: `git show`, SHA-256 and length; branch entries at `af6340de`, main entries at `51223c9b` | **28 of 28 match**: 22 branch entries, among them the five added (P29 inspector, EXECUTOR-INVENTORY.json, P07 ADOPTION.json, `format_check.py`, `tests/test_local_checks.py`), and 6 main entries, among them main's `tools/check_local.py`. Every branch entry is also unchanged at `90e8a5fb`. |
| K4 | CONTRACT.md control table against CONTRACT.json `controls` and `p05_control_map` (scripted) | Same 29 IDs, routes and Node and other start counts; the two map views agree; CH01 to CH20, CH11-P and CH11-C are mapped. |
| K5 | Read-only Mach-O parse (bytes read, nothing run) of the qualification Python's files | The launcher `bin/python3.12` (52,448 bytes) links the framework library and libSystem. The `Resources/Python.app/Contents/MacOS/Python` executable (51,392 bytes) links CoreFoundation, the framework library and libSystem, and has `LC_RPATH <prefix>/lib`. The framework library (MH_DYLIB, `LC_ID_DYLIB`) also has `LC_RPATH <prefix>/lib`. All 76 lib-dynload modules are MH_BUNDLE files with `LC_RPATH <prefix>/lib`. Their non-system dependencies are OpenSSL (libssl, libcrypto), sqlite, liblzma and mpdecimal. In the recursive closure, libmpdec has `LC_RPATH @loader_path/../lib` and libsqlite3 has an absolute `LC_RPATH`. No `@`-relative load name was seen. `<prefix>` stands for a package manager's install prefix. |
| K6 | Byte-string search of the launcher and of the Python.app executable | The launcher contains `Python.app`, `Contents/MacOS`, `posix_spawn`, `_NSGetExecutablePath` and `__PYVENV_LAUNCHER__`, and not `Py_BytesMain`. The Python.app executable contains `Py_BytesMain`. This fits a launcher that re-executes the Python.app executable (inference). |
| K7 | Clean launch, environment exactly the five ENVIRONMENT variables (`env -i`) | `/usr/bin/env`, which does not reference CoreFoundation, reports exactly those five. The qualification interpreter (`.venv/bin/python -I -S -B`, worktree and main venvs) reports six: the five plus **`__CF_USER_TEXT_ENCODING`**. `__PYVENV_LAUNCHER__` is absent, and `sys.flags.isolated` and `no_site` are 1. |
| K8 | Read-only load-command parse of a different Node build on this host (not the official build; not run) | It links `/System/Library/Frameworks/CoreFoundation.framework` and `Security.framework`, among others. |
| K9 | Read-only load-command parse of the developer-tools Git that the `/usr/bin/git` dispatcher selects | 7,604,272 bytes, universal (x86_64, arm64). It links only `/usr/lib` and `/System/Library` libraries, which is consistent with E18's "its system libraries identified by OS build". |
| K10 | `/System/Cryptexes/OS/System/Library/CoreServices/SystemVersion.plist`; format of `/System/Library/CoreServices/SystemVersion.plist` | The cryptex copy exists (603 bytes, read-only). The main file is an XML plist, so the probe needs a plist reader to check the OS build. |
| K11 | Main at `51223c9b`: `tools/check_local.py`; `docs/engineering/local-migration-20261124/` RESULTS.md, CANDIDATE-CHECKS.json, BASELINE-CHECKS.json | Main's driver has **no readback selection** (the word "readback" does not occur). Main's records show every step executed with the three methods skipped. With a resolved TMPDIR the unit stage shows failures=1 (a last-digit difference in a regenerated fixture) and skipped=3. With the default, symlinked TMPDIR it shows failures=103, errors=311 and skipped=3. This **supports** the contract's TMPDIR and fixture statements (sections 7 and 11). |
| K12 | OK-ENG-009 at main, sections 3 and 4 | Section 4 is "Integrate through short, owned scopes": branches, checkpoints and the integration lease. Failure accounting is section 3, item 4. |
| K13 | Main's PROTOCOL.md: rules on merging main into a work branch | Nothing forbids it. OK-ENG-009 section 4 asks a successor branch to reconcile against actual main. |

## 2. Status of INDEPENDENT-REVIEW-001's findings

| Finding | Status | Note |
| --- | --- | --- |
| G-01 (M) | **Resolved** | S5 is withdrawn. The 0.1.0 argv and the probe's `fs.fsyncSync` are kept, and no enforcement against descendants is claimed. Residual wording issue: G-17. |
| G-02 (M) | **Resolved** | There are no grants. The boot check moves to the provider, and the probe-side weakening of E19 is stated. |
| G-03 (M) | **Resolved** | The argv includes `--experimental-loader` and `--expected-config-sha256` (section 1; JSON `argv`; MC27). |
| G-04 (M) | **Resolved** | The member policy for the official archive is sound: pin first, normalized names, a frozen complete inventory, contained relative links declared and never extracted or followed, only `bin/node` extracted, and P05 section 5 amended explicitly. Residual: G-18. |
| G-05 (M) | **Resolved in form** | E1 to E19 are classified with reasons and effects. S9 adds the `DYLD_*` removal and the Git binding, and K9 supports the latter. E9, E17 and N34-M are restated or defined, and N57 is placed correctly as a Linux-contract control obligation. But keeping E15 for M0 is not feasible on this host: **G-13**. |
| G-06 (M) | **Resolved** | Section 5 states the narrowed meanings of the four receipt fields and leaves the zombie question explicitly open. |
| G-07 (N) | **Not resolved; now a false claim** | See **G-14**. |
| G-08 (N) | **Resolved in substance** | No skip is added, CH13 is kept, and both direct invocation and the zero-skip stage rule are stated. But section 8 contains new false statements: **G-15**. |
| G-09 (N) | **Resolved** | The M-prefixed gates do not collide. MB's move is explicit, and its reason holds: MI and MP need main's lock and environment specification, and nothing in PROTOCOL or OK-ENG-009 forbids the merge (K13). MR keeps main's recorded macOS outcomes visible, which K11 supports. Residual: G-16. |
| G-10 (N) | **Resolved** | The cryptex version is bound, and SSV and SIP are stated as assumptions. The Node load-command allow-list is closed; both executables observed in K5 use only allow-listed commands, apart from `LC_RPATH` in Python.app. ENOTSUP is refused without fallback, canonical paths are required, the fsync durability limit is stated, and `.DS_Store` is refused. |
| G-11 (N) | **Mostly resolved** | Counts are now consistent (K4), and new controls exist. Residual: G-19. |
| G-12 (N) | **Mostly resolved** | The read-set additions are verified (K3), the wording is corrected and N57 is listed. Residual: G-19. |

## 3. New findings

### G-13 — mandatory — CoreFoundation adds an environment variable, so the exact-environment predicates fail on macOS

**Location:** CONTRACT.md section 2 (E15 "kept for M0", E8, E19), section 7 (M0 "Environment |
exactly the declared clean environment"), MC07; CONTRACT.json `executor_requirements.E15`,
`host_observation.M0.fields` ("exact clean environment"), `environment.m0_refuses`. In the source,
the probe's `same(process.env, ENVIRONMENT, 'actual Node environment')` at probe line 450, which
S7 leaves unchanged.

**Evidence.**
- **The variable is real (K7).** With exactly the five declared variables, a tool that does not
  load CoreFoundation sees five. The qualification interpreter under `-I -S -B` sees a sixth,
  `__CF_USER_TEXT_ENCODING`. Its executables and framework library load CoreFoundation (K5).
- **M0 would refuse every time.** E15, as P30 defines it and the P29 `_check_launcher`
  implements it, requires `dict(os.environ) == ENVIRONMENT`. Revision 2 keeps E15 for M0 and
  makes M0 refuse anything but exactly the declared environment. On this host, M0 would
  therefore refuse on every run.
- **The probe would likely fail every start.** It requires `process.env` to equal ENVIRONMENT
  exactly. A different Node build on this host links CoreFoundation and Security (K8). By
  general knowledge, Node's own macOS build configuration links CoreFoundation. That is not
  verified for the official binary, since nothing was downloaded. If the official `node` loads
  CoreFoundation, every checker fails its host binding before the readers: Q01 and Q03 fail, and
  the negative method errors on a missing `khronos` report. MC24, MC25 and MC27 could not pass.

The contract never names this variable or the CoreFoundation behaviour. It is a term of E8, E15
and E19 that must change on macOS, and it is left out.

**Correction.** Define the macOS environment predicate explicitly, for M0, the probe and the
provider's HOST comparison. Either compare the environment passed to `exec`, as the supervisor
receipt records it, or admit exactly `__CF_USER_TEXT_ENCODING` (with its observed value recorded
in HOST) and nothing else. Add a positive control, where only the admitted variable is present,
and a refusal control, where any other extra variable is present. Establish at MP whether the
official binary loads CoreFoundation.

### G-14 — mandatory — The Python binding claims more than its inventory binds

**Location:** CONTRACT.md section 4 ("Identity bound by M0"; the claim that it "binds the files the
interpreter loads from outside the OS"), section 1 S2 row and section 2 E4 row, section 7 closure
claim ("and so are the interpreter files of section 4"), section 10 label "the Python file
inventory digest"; CONTRACT.json `python.bound_by_m0`, `python.claim`,
`host_observation.closure_claim`, `labels`.

**Evidence.**
1. **The running executable is not bound.** By the strings (K6), the launcher re-executes
   `Resources/Python.app/Contents/MacOS/Python`, which then becomes the process image. The
   inventory binds "the resolved launcher and the framework library", not that executable.
2. **The standard library is not bound.** Its pure-Python modules, and their `__pycache__`
   bytecode, are loaded from outside the OS and are not in the inventory; `-B` stops writing
   bytecode, not reading it. Neither is the venv's `pyvenv.cfg`, which is read at start-up.
3. **No rules are given for the Python files.** The Python.app executable, the framework library
   and all 76 lib-dynload modules carry `LC_RPATH <prefix>/lib`, and the recursive closure
   includes `@loader_path/../lib` (K5). Section 7's rules cannot apply to these files: a thin
   executable, a closed list that refuses `LC_RPATH`, and system-only dylib paths. "The same
   static Mach-O parser, recursively" leaves open which file types (MH_DYLIB, MH_BUNDLE) and
   commands (`LC_ID_DYLIB`, `LC_RPATH`) are accepted, and how `@`-relative names would be
   resolved or refused.
4. **Run-time loads are not covered** (inference). Libraries such as OpenSSL can load further
   files at run time, for example their configuration and the provider modules it names.

As specified, the claim is false, and the label would overstate what results bind.

**Correction.** Do one of two things. Either:
- add the Python.app executable, the standard library with its bytecode, and `pyvenv.cfg` to the
  inventory;
- define the Python-side Mach-O rules: accepted types and commands, how `LC_RPATH` entries are
  recorded, and refusal of any `@`-relative load unless a reviewed rule resolves it;
- state run-time-loaded files as unbound.

Or reduce the claim to "binds the listed files" and say what is not bound.

### G-15 — mandatory — The selection rule's statements about main and R04 are false

**Location:** CONTRACT.md section 8 (line 310 "Today, both drivers refuse to start any step without
one"; lines 340-342 "R04 consequence"); CONTRACT.json `selection_rule.r04_consequence`.

**Evidence.**
- **Main's driver has no readback selection** (K11). Main's recorded routines ran every step,
  with the three methods skipped. Only the branch's driver refuses.
- **The R04 consequence cites the wrong section.** It cites "OK-ENG-009 section 4", but section 4
  covers branches, checkpoints and leases (K12). The applicable rule is section 3, item 4. It
  requires the integrator to distinguish an unchanged failure of an explicitly incomplete feature
  from an introduced regression, using exact input identities and observed evidence. Section 3,
  item 2 requires the legacy cohort to pass without failures, errors or skipped obligations.
- **It calls a changed outcome "unchanged".** Its own first clause says the outcome changes.
- **It pre-records R04's classification** ("not as a regression"), which OK-ENG-009 leaves to the
  integrator.
- **It misdescribes the outcome.** Per general knowledge of unittest, a failing `setUpClass` is
  one class-level error, and the class's methods are neither run nor reported. P05 already notes
  that `tearDownClass` may not run. Main's ordinary runs would therefore change from "3 skipped"
  to "1 error, 3 methods not executed": tests run −3, skipped −3, errors +1. They would not change
  to three method-level errors.

**Correction.**
- Correct the statement about main.
- Replace the R04 consequence with an obligation. R04 classifies this change under OK-ENG-009
  section 3, items 2 and 4, with exact inputs, and states whether the readback methods belong to
  released behaviour.
- Describe the unittest outcome exactly.

### G-16 — nonmandatory — CONTRACT.md and CONTRACT.json disagree, and one P05 term narrows

**Evidence.**
- JSON `preparer.rules` says "P05 section 5 unchanged", against section 6 and
  `node.extraction.policy_amends`.
- JSON `host_observation.M0.starts: 0`, against M0's Git `--version` start
  (`process_denominators.M0_git_version.other: 1`, and section 7's table).
- JSON `executor.bound_at_preparation` omits the cryptex version that M0 binds.
- MR requires "zero skipped obligations in the readback cohort" (section 11; JSON `gates`). P05's
  Gate R requires zero missing or skipped obligations overall, and the narrowing is unstated.
  Today the only skips in the resolved-TMPDIR baseline are those three (K11).

**Correction.** Align the JSON fields with CONTRACT.md. State the MR narrowing as an amendment, or
restore P05's wording.

### G-17 — nonmandatory — The "no descendant" property is worded as already verified

**Location:** CONTRACT.md section 5, "No descendant"; CONTRACT.json
`supervisor.guarantees.source_backed_property`.

**Evidence.**
- The contract states as present fact that the probe, the loader and the 24 reader files "contain
  no process-creation call", "verified by a reviewed static check (MC11)". MC11 is NOT_RUN, and
  the 24 files were not examined in this phase.
- A scan for literal API names cannot exclude dynamic constructs: a computed `require` or
  `import()`, `eval`, or `Function`.
- "worker_threads process spawn" and "--allow-* facility" are not code constructs.

**Correction.** Write "to be shown by MC11", and define the scan's patterns and its stated limits.

### G-18 — nonmandatory — `NODE-SOURCE.json` and the preparer's plan model

**Location:** CONTRACT.md section 3 (provenance record, layout); CONTRACT.json
`node.extraction.layout`.

**Evidence.** The runtime directory's exact tree is `{bin/node, NODE-SOURCE.json}`, and
`NODE-SOURCE.json` is written by the preparer, not taken from the archive. The existing preparer
stages only archive members, and requires every planned target file to map to one (`_plan_shape`,
lines 116-122).

**Correction.** State who writes `NODE-SOURCE.json`, how its exact bytes are frozen in the plan,
and how the exact-tree checks and the no-replace publication cover a non-archive file.

### G-19 — nonmandatory — The dispositions of G-11 and G-12 overstate, and the read set is incomplete

**Evidence.**
- **G-11.** Section 9 says "Every other CH: kept". Yet three P05 cases have no MC: CH03's
  declared-version mutation, CH07's C195-archive extraction checks, and CH08's partial, changed,
  linked or inaccessible existing destination.
- **G-12.** The disposition says every document schema is versioned. Only the design, config,
  lock, host, result and node-source schemas are. The provider's other documents still carry
  `/0.1.0`: source, dependencies, methods, discovery, workspace, inspection, attempt, setup,
  cohort, refusal and preserved-cohort. Yet the contract keeps "each version's entry points
  refuse the other's documents".
- **Read set.** It omits OK-ENG-009 and main's local-migration records (BASELINE-CHECKS.json,
  CANDIDATE-CHECKS.json, RESULTS.md), on which sections 7, 8 and 11 rely.

**Correction.** List the partial CH coverage, version the remaining schemas, and add those inputs
with their identities.

## 4. Acceptance claims A1 to A8 on revision 2

| Claim | Assessment | Findings |
| --- | --- | --- |
| A1 | 28 of 28 identities. Two relied-on inputs are missing. | G-19 |
| A2 | E1 to E19 are classified. E15's "kept" is infeasible, and S2's effect is overstated. | G-13, G-14 |
| A3 | Node is defined. The Python identity claim is false. | G-14 |
| A4 | Met. The property's wording is premature. | G-17 |
| A5 | Met. The provenance-file mechanics are open. | G-18 |
| A6 | M0, M1 and the denominators are defined. M0's environment predicate is infeasible, and the closure claim overstates on the Python side. | G-13, G-14 |
| A7 | Decided without a skip. Its statements about main and R04 are false. | G-15 |
| A8 | Controls are consistent. Some coverage and the gate wording are residual. | G-16, G-19 |

## 5. Verdict

**REJECT_WITH_MANDATORY_FINDINGS.**

- New mandatory findings: **G-13, G-14, G-15**.
- Nonmandatory: G-16 to G-19.
- Of the earlier findings, G-01 to G-06, G-09 and G-10 are resolved. G-07 is replaced by G-14.
  G-08, G-11 and G-12 are resolved apart from G-15 and G-19.

## 6. Command and write policy

- Never started: node, npm, ldd, codesign, any VM tool, any test, or the driver. Nothing was
  downloaded or installed, and no network read was needed.
- Git use was read-only, always with `--no-optional-locks` (`show`, `cat-file`, `ls-tree`,
  `rev-parse`, `log`, `diff`, `grep`, and `status --porcelain`). No ref, index or working file
  changed.
- Mach-O files (K5, K8, K9) were read as bytes by an inline script. No such file was executed.
- To list its own environment (K7), the qualification interpreter was started twice, once from
  main's venv and once from the worktree's, as `.venv/bin/python -I -S -B -c …` under `env -i`.
  Neither run writes anything. `/usr/bin/env` was run once for comparison.
- Writes: only `REVIEW-002.md` and `REVIEW-002.json` in this directory. No scratch files.
- These files name no application installed on the owner's computer. `<prefix>` stands for a
  package manager's install prefix.
