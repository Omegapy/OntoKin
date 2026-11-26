# C271-P34, gate MP: independent review 001 of the preparation plans

**Reviewer:** W2, the fresh-context independent reviewer of phase `C271-P34-macos-preparation-mp`
(Director `c271-p34-ec1a7de2360d`), local mode, read-only. W2 wrote none of the implementation, the
plans or the decisions.
**Reviewed base:** `work/c271-missing-import-digest-control` at
`6d08e0266623507786e991d8617a4a6a0d72e171`, clean; the only ignored entry is `.venv/`.
**Contract:** `ontokin.current-host-readback/0.2.0`, design revision 4 (P33-AMENDMENT-001).
**Date:** 2026-11-26.

Places are named relative to the clone: `<worktree>` is `../OntoKin-worktrees/c271` and `<local>` is
`../OntoKin-local`. The machine-readable form is [PLAN-REVIEW-001.json](PLAN-REVIEW-001.json); the
scratch work is in `plan-001/`.

## Verdict

**ACCEPT_WITH_NONMANDATORY_FINDINGS.** There is no mandatory finding.

- The four install/0.2.0 plans, the `NODE-SOURCE.json` bytes and the `.venv` expectation agree with
  W2's independent derivations, exactly.
- The `.venv` procedure of PREPARATION-PLAN.md section 3 is sound against M0's exact package rule.
- The Director's proposed `--no-cache-dir` is **accepted** (section 4).
- Ten nonmandatory findings, P-01 to P-10 (section 5), concern the procedure's statements,
  environment and records. P-01, P-06 and P-07 should be settled before step 6.

## 1. What W2 reproduced

Every archive and wheel was read into memory once. Its SHA-256 was compared with the pin before any
member was parsed. Nothing was extracted, installed or executed.

| Item | W2's own result | Equal to |
| --- | --- | --- |
| Node archive | SHA-256 `89c68259…bc0a7`, 53,062,778 bytes, one gzip member, no trailing bytes | adopted pin; download record |
| Node inventory | 5,888 members: 4,797 files (4,734 `0o644`, 63 `0o755`), 1,088 directories (`0o755`), 3 links (`0o755`); 197,423,496 expanded bytes; ustar headers only, 1,405 using the prefix field; only zeros (1,024 bytes) from the end marker on | the plan's `members`, exactly |
| Inventory digest | `0b2b6072fd2e6b22fd4d2715d9db9429adf17d960825b0048411d1a1d4c0f27d` | `member_inventory_sha256_v02` |
| `bin/node` | SHA-256 `6f32069480ec14d52b6d7b1f3c7124cfbbc46203abf5ddf5c65b127435f3f329`, 122,545,856 bytes, header mode `0o755`; `cffaedfe`, cputype `0x0100000c`, cpusubtype `0`, `MH_EXECUTE`, 21 load commands | `files["bin/node"]` |
| `NODE-SOURCE.json` | 976 bytes, SHA-256 `e928a8ec87a6fcd8f21d7bef3e080392e0bdaad3acbf2e767997dae5ead9ea2c`, built from W2-PREPARER.md section 4 | W1's expected bytes; `files["NODE-SOURCE.json"]`; `node_source_bytes_v02(plan)`; the observer's `check_node_source` accepts it |
| C195 archive | SHA-256 `b1e54a6c…e904a0c9`, 2,611,764 bytes, one xz stream; 730 files, each after a pax header holding only `path` and `mtime`; no directory member; modes `0o644` ×726, `0o444` ×3, `0o600` ×1 | the pin; the plan's `members` (digest `72dc3175953b29edce2e2343613c08fb2f0bfb2b40e72faaaa5c9d457d67cb8a`) |
| 24-file mapping | `c195-validation/receiving/<rel>` → `<rel>`, from the C199 manifest's `dependencies_root`; each member has the pinned bytes | the plan's `files`; `dependency_inventory(ROOT)` |
| Wheels | 7 files, each SHA-256 equal to the lock; every zip file is in its RECORD, and every hashed row matches | venv-expectation.json, file by file |

Static validation (question 5): `validate_plan_v02` accepts all four plans, the two exact ones and
their dry-run variants. `member_inventory_sha256_v02` returns W2's two digests.

## 2. Answers to the questions of the brief

1. **Downloads.** All 8 files were hashed again. The Node archive matches the adopted pin, the
   approved source URL (`https://nodejs.org/dist/v24.22.1/`) and size, with HTTP 200. It is a private
   (one-link) regular file, mode `0o444`, as the plan freezes. Each wheel matches the lock's hash and
   its provenance record's URL, size and version. The lock's SHA-256 equals its provenance record.
   Each download directory holds exactly its files. The 7 wheels total 5,447,056 bytes. The rows
   are sequential, from 21:04:13Z to 21:04:15Z. The declaration commit `6d08e026` was pushed at
   21:03:39Z (local reflog), before them.
2. **The Node plan.**
   - `members` equals the inventory that W2's own header walk and Python's `tarfile` both give. The
     two views agree row by row: name, type, size, mode, link target and data offset.
   - **Member policy:** every name is relative, normalized, unique and under
     `node-v24.22.1-darwin-arm64`. There are only files, directories and links. There is no hard
     link, device, FIFO or sparse member, and no member below a link or a file. Each of the three
     links (`bin/corepack`, `bin/npm`, `bin/npx`) resolves lexically inside the root to a declared
     regular file.
   - **D-06 confirmed:** every name and link target is ASCII. The highest mode is `0o755`, with no
     special bit.
3. **NODE-SOURCE.json.** Re-derived from note section 4: the pin, size and checksum-file constants
   of contract section 3; the plan's `signature_check` (`not_performed`, ASCII detail of 203
   characters); W2's inventory digest; and `bin/node`'s binding. The bytes equal W1's 976 bytes,
   the plan's frozen digest and size, and `node_source_bytes_v02(plan)`. The status is not
   `failed`, so D-02 raises no finding.
4. **The reader plan.** The re-derived inventory and the 24 targets equal `members`. `files` equals
   `dependency_inventory(ROOT)` by digest and size, with each member's mode (all `0o644`). The 13
   `directories` are exactly the files' parents. They and `root_mode` are `0o755`, implicit parents
   as P05 section 5 allows. The archive binding (path in the checkout, pin, size, mode `0o644`, one
   link) matches the file.
5. **Static validation.** As in section 1. W2 did not call `install_plan_v02` or the CLI.
6. **Places.**
   - Both destinations and all four report paths are absent, normalized, outside the checkout and
     free of link components. Their parents exist. The `.preflight.json` and `.publication.json`
     side files are absent, and each report lies outside its destination.
   - `../OntoKin-local/c271-macos/` and `receipts/` are empty.
   - The destination parent, both archives, the reports and the checkout are on one volume. Its
     file system is APFS, and its capabilities report `VOL_CAP_INT_RENAME_EXCL` valid and set.
   - Only the stage and the destination must share a volume: the preparer creates the stage under
     the destination's parent and checks `st_dev`. The archives' volume does not matter, and is the
     same in fact.
7. **The `.venv` procedure.**
   - **Pip stays out of the `.venv`.** pip 26.0 handles `--python` by running the base installation's
     own `__pip-runner__.py` under `.venv/bin/python`. A meta-path finder imports `pip` from the base
     installation's site-packages. With `--no-deps`, only the lock's seven requirements are
     installed, and nothing installs pip.
   - **Package rule preview.** W2 predicted the resulting site-packages from the seven verified
     wheels and pip's install code. The observer's `verify_packages`, with its file reads served
     from memory, accepts the prediction, and refuses it once a pip distribution is added.
   - **Hash enforcement:** `--require-hashes` on the committed lock. **Offline:** `--no-index` and
     `--find-links`. **Binary only:** `--only-binary=:all:`.
   - **Bytecode:** `--no-compile` stops pip from compiling; `-B` covers the parent; and
     `PYTHONDONTWRITEBYTECODE=1` covers the child, which inherits it and runs without `-I` (see P-10).
   - **venv-expectation.json is complete** for what pip 26.0 writes:
     - the wheels' files;
     - per distribution, `INSTALLER` (`pip\n`), an empty `REQUESTED` (named requirements are
       user-supplied) and a rewritten `RECORD`;
     - one console script, `bin/jsonschema`.

     There is no `direct_url.json` (not direct URLs), no GUI script, no `.data`, header or `.pth`
     file. Not predicted: the `RECORD` and script bytes (W1's F3), the file modes (which follow the
     umask) and the implied directories.
   - **The framework-unchanged check is meaningful.**
     - The framework tree is owner-writable, and holds 414 cached bytecode files for 1,969
       standard-library sources. A run without `-B` would almost certainly add files there, and
       the before-and-after comparison would show them.
     - The check is computable: the observer's `python_inventory` of the current `.venv` and
       framework succeeded, read-only (3,788 framework entries).
     - The after state should also be computable. All 27 Mach-O files of the two binary wheels
       pass `parse_macho` and `check_python_macho` in memory, and their `@loader_path` references
       resolve within the wheel.
     - **Limit:** the framework's `site-packages` is a link out of the framework tree, so the
       running pip lies outside the check and outside M0's binding. Neither the `.venv` nor the
       qualification uses it.
   - **The doctor's pip check:** reported as not checked, as the plan says. Its consequences and the
     check it replaces are not stated (P-01).
   - **Risks:** P-02 to P-05 and P-10.
8. **Commit binding.** The install plans cannot carry a commit: their schema is a closed 12-key set,
   and D-15 adds no field. MP binds B by procedure:
   - step 5 defines B as the commit of the reviewed plans;
   - step 6 requires `git status` empty and HEAD equal to B before each run (I-03);
   - step 7 compares `preparer_source` with B's files and states I-03's four-file limit, which
     section 6 repeats.

   This meets D-17 and I-03 as written. P-06 and P-07 close two gaps: B's relation to the reviewed
   base, and the plan digest.
9. **Portable copies.** Each of the four restores to its exact plan, byte for byte, when `<worktree>`
   and `<local>` are replaced. No portable copy, and no other W1 file, holds a machine path or user
   name. The exact plans are canonical JSON: sorted keys, compact separators, ASCII and no trailing
   newline.

Plan digests reviewed, the values for `--plan-sha256` (P-07):

| Plan | SHA-256 |
| --- | --- |
| `node-install-plan.json` | `1fee042d5e3c809a89d4975df40f69d7a27e88abf9ba58d8cf91ca16795c5ff1` |
| `node-install-plan.dry-run.json` | `869b6414d42f6ced4ee4ad017ceff7cc63c33b563fcdffcc5999cebebae01d48` |
| `reader-install-plan.json` | `ff5a95da6d349e0bd6ea1d2c79fc02757de48ac9cbb89dc59737b67c6d7a71c8` |
| `reader-install-plan.dry-run.json` | `a81897783b9df86bb216eb5c371a1191de0a89762e6cd88360c8cc7b7fecf10e` |

## 3. W1's findings

- **F1, correct.** A dry run writes `<report>` and `<report>.preflight.json`, and every run requires
  an absent report. The dry-run variants differ from the exact plans only in `report`, and both pass
  `validate_plan_v02`. They are the right remedy. Any further variant that differs only in a fresh,
  absent `report` under `receipts/` (a repeat, for example) keeps every other check of this review,
  but its digest must be recorded before its run.
- **F2, correct as a static fact.** `bin/node` has a plain (not weak) `LC_LOAD_DYLIB` of
  CoreFoundation, beside Security, `libc++` and `libSystem`. This does not establish that a start adds
  `__CF_USER_TEXT_ENCODING`. D-16's determination stays with MH, from M0's own parse, and it points to
  MC36 standing as written.
- **F3, correct.** pip 26.0's code confirms each predicted file, and that nothing else is written
  (question 7).
- **F4, correct.** `source_root` must equal the running preparer's resolved root. The reader archive
  is read inside the checkout. The Node archive must stay a private regular file with mode
  `0o444`. P-09 adds that both archives must stay unchanged until MH.

## 4. The proposed `--no-cache-dir`

**Accepted, unchanged.** In pip 26.0 it is a general option, valid after `install`. It sets
`cache_dir` to false, so pip neither reads nor writes the HTTP or wheel cache. For local wheels with
`--no-index`, pip would not use the cache anyway, but the flag makes that true by construction and
removes the user's cache from the step's inputs and outputs. It changes nothing in the installed
result.

## 5. Findings

All ten are nonmandatory.

| ID | Location | Issue | Change |
| --- | --- | --- | --- |
| P-01 | PREPARATION-PLAN.md section 3 "The doctor", step 7; `tools/doctor_local.py` | The pip check's state is reported correctly, but not its consequences. `combine` makes the `python-verification` profile `not_checked`, so the doctor exits 1. Because `pip_check` is null, `rebuild_reasons` is not empty, and the next action recommends `tools/bootstrap_local.py … --rebuild`, the route that installs pip (D-21). The plan also omits what `pip check` verifies: the installed distributions' Requires-Dist. Read from the seven METADATA files, these are lower bounds that the pins meet (typing-extensions applies on 3.12). | State the expected result: lock, packages, imports and native-reader `ready`; pip-check `not_checked`; profile `not_checked`; exit 1; the rebuild advice deliberately not followed. Keep the doctor's JSON report, and record a metadata-level requirement check in place of `pip check`. |
| P-02 | Step 7; `visual_section` | `node` resolves on this host's default PATH, so without `--node` the doctor starts `node --version`. With `--node` naming an absent path, it still calls `subprocess.run` once. The call fails (no such file) before any image runs, but the audit records a start event. | Keep the absent `--node` path in the command, with a minimal PATH. Record that audit row as a failed attempt on a non-existent path, not a Node start (A7). |
| P-03 | Section 3 command | The pip child runs `.venv/bin/python` without `-I` or `-E`, with the ambient environment, so it honours every PYTHON* variable. `PYTHONEXECUTABLE` would even change the script's first line. `--isolated` still lets pip read global and site configuration files and `PIP_CONFIG_FILE`. None exists at review time. The plan does not record its environment, its working directory (the lock path is relative), its umask (installed modes follow it), or the installer's identity. The base pip has a METADATA (26.0), but no RECORD. | Run under a declared environment: for example `env -i` with HOME, `PATH=/usr/bin:/bin`, the resolved TMPDIR, LANG and LC_ALL, `PYTHONDONTWRITEBYTECODE=1` and `PIP_CONFIG_FILE=/dev/null`. Run from the worktree root with umask 022. Record the variable names, pip's version and a digest of its files. |
| P-04 | Step 6 "Audit"; A7 | The hook sees the parent's single start, the child interpreter. The child's own starts are outside it. By pip 26.0's code, the child starts none for this install. packaging's tag code would start one only if the interpreter reported macOS 10.16; it reports 26.6.2. | State this limit, and the code reading that covers it, in the receipts. |
| P-05 | Section 3 "only the planned files may be added"; the Director's draft `venv_snapshot.py` | The draft comparison reports additions only as a count and top-level names. `verify_packages` checks ownership only inside site-packages, so nothing fails on an unexpected file elsewhere in the `.venv`. | Compare the additions exactly with venv-expectation.json: 291 site-packages files (270 by the wheels' digest and size; `INSTALLER` and `REQUESTED` by digest; `RECORD` by name), their directories, and `bin/jsonschema`, and nothing else. Prediction for the script, from pip 26.0's template: 207 bytes, SHA-256 `1cdcd273309e7172baf9d6dc83f3f6b8e79f3d79c750077a564bb2bc7ec867cc`. It holds if the child's `sys.executable` is `<worktree>/.venv/bin/python`, which the interpreter reports today. |
| P-06 | Steps 5 to 8; D-17, I-03 | This review validated the plans against the preparer, provider, observer, C199 manifest, C195 archive and lock at `6d08e026`. Step 5 does not require B to leave those unchanged. "`git status` empty" omits ignored files, and `-B` stops writing bytecode, not reading it. Today the only ignored entry is `.venv/`, and there is no `__pycache__` in the checkout. | Require B to descend from `6d08e026` with no change to the preparer's ten-file import closure, the C199 manifest, the C195 archive, the lock or its provenance; otherwise repeat the static validation at B. Before and after each run, require `git status --porcelain --ignored` to show only `.venv/`. At A8, compare `preparer_source` with B's blobs. |
| P-07 | Step 6 `--plan-sha256 D`; the Director's draft `run_preparation.sh` | D is undefined. The exact plans live outside Git, so their reviewed digests are the only binding between the plans applied and the plans reviewed. The draft computes D from the plan file at run time, so the CLI's frozen-digest check cannot fail. | Define D as the four reviewed digests (section 2), committed at B. Pass those recorded values, and record them in the receipts. |
| P-08 | The Director's draft `audited_run.py` | Module mode sets `sys.path[0]` to the working directory, which `-I -m pip` never does; script mode puts `tools/` on the preparer's path. pip's `__main__` drops the first entry. No name in the root or `tools/` collides with the standard library or `pip` today. | Leave `sys.path` as `-I` sets it. |
| P-09 | Section 2; W1's F4; the observer's `_install_receipts` | M0's receipt rule binds each plan's archive again by path, SHA-256, size and mode. Contract section 7's `.DS_Store` rule applies to the prepared trees once published. | State that both archives stay unchanged at their paths until MH, and the `.DS_Store` rule. |
| P-10 | Section 3 "No bytecode" | It says the variable is "needed because pip starts the `.venv` interpreter without `-I`". The variable is needed because the child runs without `-B`, and it takes effect because the child also runs without `-I` and `-E`. | Reword. |

## 6. Observations for later gates

These are not MP findings.

- **MH, W3's Q3:** the cpusubtype is `CPU_SUBTYPE_ARM64_ALL` (0) for `bin/node` and for all 27 Mach-O
  files of the binary wheels. The observer's `parse_macho` and `check_node_macho` accept `bin/node`
  in memory, preview only.
- **MH, N34-M:** one dylib bundled in the Pillow wheel carries an absolute `LC_RPATH`. It names a
  directory of the wheel's builder that does not exist here. The image has no `@rpath` reference,
  and the observer records the entry as an absent search directory.

## 7. Conduct and limits

- **Starts:** no Node, `ldd` or `codesign` start; no download; no Git write (Git ran with
  `--no-optional-locks`, read commands only); no edit in the repository.
- **Writes:** only in `reviews/`.
- **Python:** the worktree's `.venv` interpreter (CPython 3.12.13), with `-I -S -B` and the standard
  library only, under an audit hook. The hook refused every process start and every write outside
  `reviews/plan-001/`, as its self-test showed. It refused nothing during the runs.
- **The checkout at the end:** still clean, with no `__pycache__`, and the `.venv` unchanged at 15
  entries.
- **What was read:** pip 26.0's source in the base installation, and the Director's draft scripts in
  `../OntoKin-local/c271-p34/director/`. Those scripts are outside the reviewed set; P-05, P-07 and
  P-08 describe them for information.
- **Not done:** pip and the preparer were not run. The `.venv` predictions rest on pip's code and on
  the in-memory preview, not on an installation.

## 8. Reproduction

Run from `reviews/`, with `PY=<worktree>/.venv/bin/python` and absolute paths in place of the
labels. Each command writes one new file in `plan-001/`. PART is each of `downloads`, `node`,
`reader`, `wheels`, `places` and `portable` in turn:

```sh
$PY -I -S -B plan-001/w2_parts.py PART <worktree> <local> plan-001/result-PART.json
$PY -I -S -B plan-001/w2_static.py <worktree> <local> plan-001/result-static.json --inventory
$PY -I -S -B plan-001/w2_simulate_packages.py <worktree> <local> plan-001/result-simulated-packages.json
$PY -I -S -B plan-001/w2_digests.py <worktree> <local> <base-site-packages> plan-001/reviewed-files.json
```

`w2_write_json.py` assembled PLAN-REVIEW-001.json, which lists the SHA-256 of every reviewed file and
of the scratch results.

The first `portable` run (`result-portable.json`) kept two false positives: an over-broad pattern for
the base installation's link directory matched a labelled path in venv-expectation.json and a string
literal in W1's script. `result-portable-r2.json` repeats the check with the actual prefix and the
other machine roots, and passes all 20 checks. Both files are kept.
