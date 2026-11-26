# C271-P31 re-review: revision 3 of the macOS arm64 contract design

**Candidate:** commit `dd98e9830fffc0da96bf1cfc408c7f246867a20a`, tree
`8638ea3419ce325c04426fe819e56dbb6f1b7100`, parent `90e8a5fb…` (revision 2, rejected by
INDEPENDENT-REVIEW-002). The worktree head is at `dd98e983` with no tracked changes. Main was
observed at `51223c9b…`. Reviewed 2026-11-26, about 05:35–05:45Z. The full change is
`git diff 90e8a5fb dd98e983`.

| File at `dd98e983` | Bytes | SHA-256 |
| --- | ---: | --- |
| CONTRACT.md | 40,740 | `62f48248…c513` |
| CONTRACT.json | 41,371 | `e03cdc1b…8623` |
| READ-SET.json | 10,637 | `844cd486…e545` |
| REVIEW-DISPOSITION.json | 8,635 | `ad4f362c…07c6` |

## 1. Checks run

| # | Check | Result |
| --- | --- | --- |
| K1 | Commit, tree, parent and diff stat | Seven files change: CONTRACT.md, CONTRACT.json, READ-SET.json and REVIEW-DISPOSITION.json, plus the three new INDEPENDENT-REVIEW-002 files. |
| K2 | INDEPENDENT-REVIEW-002.md and `.json` against my originals | **Byte-identical** (`956bfe11…`, `d4568dd9…`). |
| K3 | READ-SET recomputation from Git blobs: branch entries at `af6340de`, main entries at `51223c9b` | **32 of 32 match.** The four entries added in revision 3 are OK-ENG-009, BASELINE-CHECKS.json, CANDIDATE-CHECKS.json and RESULTS.md. |
| K4 | CONTRACT.md control table against CONTRACT.json `controls` and `p05_control_map` (scripted) | All 35 IDs, routes and Node and other start counts agree. The two maps agree, with CH03 → MC10 and MC33, CH07 → MC02, MC03, MC04, MC18 and MC34, and CH08 → MC15, MC16 and MC35. The process denominators are unchanged. |
| K5 | Read-only scan of the qualification Python's trees against section 4's Mach-O rules (bytes read, nothing run) | **Framework version directory:** 3,478 regular files, 5 symlinks, 72,433,430 bytes. Its Mach-O files are 2 MH_EXECUTE, 1 MH_DYLIB and 76 MH_BUNDLE, with no fat file, no load command outside the extended allow-list and no `@`-relative load. One symlink, `lib/python3.12/site-packages`, leads out of the tree, but that path is not on the venv's search path. **Main's venv:** 1,348 files, 26,766,077 bytes, 19 MH_DYLIB and 8 MH_BUNDLE, with no command outside the list. Its 26 `@loader_path` references all resolve inside the venv, and it has no `@rpath` reference and no non-system absolute dependency. **The worktree's venv:** 5 files and 3 symlinks, not yet populated. **Conclusion:** the rules are **feasible** on this installation. |
| K6 | The non-system dependency closure, scanned the same way | There are five direct dependencies: OpenSSL's libssl and libcrypto, sqlite, liblzma and mpdecimal. None has a command outside the list. Each is referenced through a `<prefix>/opt/<name>` symbolic link that points into a versioned directory outside both trees. libmpdec has `LC_RPATH @loader_path/../lib`, and libsqlite3 has an absolute `LC_RPATH`. libssl references libcrypto by its versioned path; this is the only transitive-only path, and it leads to a file that is already bound. |
| K7 | S10's value: two clean launches with exactly the five variables (main's and the worktree's venv), compared without printing the value | The variable is present in both, and the two values are equal to each other and to the session's own value. The format is `0x<uid>:0x0:0x0`. S10's "recorded and compared" is therefore workable. |
| K8 | Bytecode of the standard library | Of 1,804 standard-library `.py` files, 1,390 have no `cpython-312.pyc`. The directory is writable by the owner's account. |
| K9 | Statements re-checked against the sources | Each holds: main's driver has no selection and main's test skips the three methods (section 8); unittest reports one class-level error and does not run the three methods; R04 is an obligation under OK-ENG-009 section 3, items 2 and 4; MR again has Gate R's wording. |
| K10 | JSON alignment | Each holds: `preparer.rules` names both amendments; M0's `starts` is `{node: 0, other: 1}`; `bound_at_preparation` includes ProductVersionExtra and the cryptex file; `schemas` lists all 17 document schemas at `/0.2.0`. |

## 2. Status of INDEPENDENT-REVIEW-002's findings

| Finding | Status | Basis |
| --- | --- | --- |
| G-13 (M) | **Resolved** | S10 is one predicate shared by M0, the provider's HOST comparison and the probe's bootstrap check. It admits exactly `__CF_USER_TEXT_ENCODING` with the value recorded in HOST, and refuses anything else. The supervisor still passes, and records, exactly the declared environment. The value is stable (K7). MC30 and MC31 cover it. Residual: G-20. |
| G-14 (M) | **Resolved** | The inventory now covers the Python.app executable, the standard library with its bytecode, `pyvenv.cfg` and the whole `.venv`. The Python-side Mach-O rules are stated, are feasible on this host (K5, K6), and run-time loads are declared unbound. Residual: G-21. |
| G-15 (M) | **Resolved** | The statement about main is correct. The unittest outcome is exact. R04 is an obligation under the right items, with no classification decided in advance. |
| G-16 (N) | **Resolved** | K10; and MR again says "zero missing or skipped obligations, as P05's Gate R requires". |
| G-17 (N) | **Resolved** | MC11 is "to be shown" and NOT_RUN. Its patterns include the dynamic constructs, and its limit is stated. |
| G-18 (N) | **Resolved** | The preparer writes `NODE-SOURCE.json` at MP. Its bytes are frozen in the reviewed plan before publication, and the exact-tree check, the no-replace publication and the provider's preflight all cover it. |
| G-19 (N) | **Resolved** | MC33 to MC35 cover CH03, CH07 and CH08. Every provider schema is versioned. The read set has the missing inputs (K3). Residual: G-22. |

## 3. New findings (all nonmandatory)

### G-20 — nonmandatory — S10's controls and wording

**Location:** CONTRACT.md section 7 ("Environment predicate (S10)"), MC30 and MC31; CONTRACT.json
`environment.os_supplied_allowance`, `controls`.

**Evidence.**
- MC30 also accepts the case "separately, without" the variable. A process that loads
  CoreFoundation always has the variable (K7), so for any one process only one of the two
  branches can be produced for real. The other branch is a simulation. Under P05's rule, a
  simulation must be labelled as mocked boundary evidence. MC30 does not label it.
- MC31 counts no Node start. The provider's launch binding refuses any other child environment
  before a start, so the probe's own refusal branch (a wrong recorded value, or an extra variable)
  is never run in a real probe. That is unlike P06-H01 and P06-H02, which test probe-side
  refusals with one start each.
- CONTRACT.md says "If the process has loaded CoreFoundation, it also accepts…". That reads as a
  check, but the JSON predicate contains none ("admits the variable either way").

**Correction.**
- Label MC30's second branch as a simulated boundary.
- Add a direct-probe refusal case, one Node start, with an altered recorded value.
- Word the predicate as "exactly the declared environment, optionally plus that one variable with
  the recorded value".

### G-21 — nonmandatory — The installation-tree binding needs four precisions

**Location:** CONTRACT.md section 4 ("Identity bound by M0", "Python-side Mach-O rules"), MC32;
CONTRACT.json `python.bound_by_m0`, `python.mach_o_rules`.

**Evidence.**
1. **Exact set.** The contract does not say whether later checks compare the tree as an exact set
   (no extra or missing file). MC32 tests only *changed* files. 1,390 of 1,804 standard-library
   modules have no bytecode, and the tree is writable by the owner (K8). Any other use of this
   interpreter without `-B` therefore adds bytecode files, which the interpreter would then load
   in preference to compiling the source. Unless additions refuse, those files are loaded unbound.
2. **Dependencies.** Every non-system dependency is reached through a `<prefix>/opt/…` symbolic
   link outside both trees (K6). libssl also reaches libcrypto by a second path. Since revision 3
   no longer says "recursively", neither the transitive closure nor the recording of each
   referenced path's symbolic-link hops is stated. If only resolved paths were recorded, a
   retargeted link could load other bytes while the check still passes.
3. **Interpreter selection.** The venv's `bin/python3.12` points to `<prefix>/opt/python@3.12/…`,
   and `pyvenv.cfg`'s `home` names the same linked path. The hops that select the installation lie
   outside both trees. A retarget would be caught only indirectly, by the version and build string,
   unless the resolved launcher path is checked at each use. Revision 3 no longer says so.
4. **`@`-relative rpaths.** An `LC_RPATH` entry that is itself `@`-relative, such as libmpdec's
   `@loader_path/../lib` (K6), is a search directory, not a reference that "resolves to a bound
   file". If it were read as such a reference, M0 would refuse a real dependency of `_decimal`.

**Correction.**
- State exact-set comparison of both trees, and add an "added bytecode file" case to MC32.
- Bind dependencies transitively, by referenced path, with every symbolic-link hop, re-followed at
  each check.
- Bind the interpreter-selection chain, or restate the resolved-path check.
- Say that `@`-relative `LC_RPATH` entries are recorded and resolved as directories.

### G-22 — nonmandatory — Two record details

**Evidence.**
- READ-SET.json's new host fact describes a launch with five declared variables, but lists only
  four (LANG, LC_ALL, PATH and TZ). UV_THREADPOOL_SIZE is missing.
- "Every document schema of the provider is versioned" leaves out two sets of documents:
  - the preparer's plan and result schemas, `ontokin.current-host-readback-install/0.1.0` and
    `install-result/0.1.0`, although their meaning changes under 0.2.0 (declared link members, a
    planned non-archive file);
  - M0's plan schema, which replaces the inspector's.

  Without them, "each version's entry points refuse the other's documents" does not reach the
  preparer or M0.

**Correction.** Correct the fact, and version those schemas.

## 4. Acceptance claims A1 to A8 on revision 3

| Claim | Assessment |
| --- | --- |
| A1 | Met. All 32 identities match, and the external and host facts carry sources and times. The small inaccuracy is G-22. |
| A2 | Met. E1 to E19 and the substitutions S1 to S10 are each stated with reason and effect. |
| A3 | Met. The Node and Python identities are defined, with precisions open in G-21. |
| A4 | Met. |
| A5 | Met. |
| A6 | Met. M0, M1, the denominators and the closure claims are stated honestly (G-20, G-21). |
| A7 | Met. The selection rule is decided without a skip, and R04 gets an obligation. |
| A8 | Met. All 35 controls are NOT_RUN and consistent across both files; labels and never-supported claims are stated (G-20). |

## 5. Verdict

**ACCEPT_WITH_NONMANDATORY_FINDINGS.** G-13 to G-19 are resolved, and no mandatory finding
remains. The new findings G-20, G-21 and G-22 are nonmandatory precisions for MD's adoption
record, or for MI to carry. None of them states something false, claims an unsupported
guarantee, relabels a gate or implies execution authority.

## 6. Command and write policy

- Never started: node, npm, ldd, codesign, any VM tool, any test or the driver. Nothing was
  downloaded or installed, and there was no network read.
- Git use was read-only, always with `--no-optional-locks`. No ref, index or working file changed.
- Mach-O and other installation files were read as bytes; none was executed. To compare S10's
  value (K7), each venv's interpreter was started once, as `-I -S -B -c …` under `env -i`, and
  the value was never printed or recorded.
- Writes: only `REVIEW-003.md` and `REVIEW-003.json` in this directory. No scratch files.
- These files name no application installed on the owner's computer. `<prefix>` stands for a
  package manager's install prefix.
