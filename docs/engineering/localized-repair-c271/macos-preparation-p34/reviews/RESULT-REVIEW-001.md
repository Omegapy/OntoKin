# C271-P34, gate MP: independent review 001 of the preparation's results

**Reviewer:** W2, the fresh-context independent reviewer of phase `C271-P34-macos-preparation-mp`
(Director `c271-p34-ec1a7de2360d`), local mode, read-only. W2 also wrote
[PLAN-REVIEW-001](PLAN-REVIEW-001.md), and wrote none of the implementation, the plans or the run.
**Bound commit B:** `601f39361940422179ff7683aa602c2b36622944`, a child of the reviewed `6d08e026`.
**Contract:** `ontokin.current-host-readback/0.2.0`, design revision 4 (P33-AMENDMENT-001).
**Date:** 2026-11-26.

Places are named relative to the clone: `<worktree>` is `../OntoKin-worktrees/c271`, `<local>` is
`../OntoKin-local`, and `<prefix>` is the base installation named by `pyvenv.cfg`'s `home`. The
machine-readable form is [RESULT-REVIEW-001.json](RESULT-REVIEW-001.json); the scratch work is in
`result-001/`.

## Verdict

**ACCEPT_WITH_NONMANDATORY_FINDINGS.** There is no mandatory finding.

- The four receipts, the two published trees and the `.venv` are exactly what the reviewed plans and
  the expectation predict. W2 re-derived each of them independently.
- Conduct matches PREPARATION-PLAN.md section 7: B clean at every check, the declared environment,
  no Node, `ldd` or `codesign` start.
- The doctor's result is exactly the predicted one, and its rebuild advice was not followed.
- Three nonmandatory findings, R-01 to R-03, concern the records. They are for the outcome and for MH.

## 1. Receipts

All four receipts pass, as do their sidecars and CLI lines.

- **States and counts:** `DRY_RUN_READY`, then `INSTALLED_EXACT`, each `passed`; zero Node, `ldd` and
  checker starts.
- **Shape:** each holds the closed key set of its outcome, with schema `install-result/0.2.0`,
  `design_revision: 4` and `amendments: ["P33-AMENDMENT-001"]`.
- **Pins and labels:** the adopted pins, origin `adopted-contract`. The labels hold `macos-arm64-local`,
  `darwin-arm64-v1`, the bound pins of their purpose (for Node, `bin/node`'s binding), and an OS label
  that the observer's `check_os_label` accepts. That label (26.6.2, 25G83, cryptex present with the
  same) equals the host's identity now.
- **`preparer_source`:** each names this checkout and the four files. Each binding equals B's blob
  (`git show B:…`): SHA-256 and size, mode `0o644`. The run's closure record also shows all ten
  import-closure files equal on disk and at B. They equal the files that PLAN-REVIEW-001 validated.
- **Archive summaries:** each equals its plan. Member counts are 5,888 and 730; expanded bytes
  197,423,496 and 42,685,553; 3 links and none. The inventory digests are `0b2b6072…` and `72dc3175…`,
  and the extracted members are `bin/node` and the 24 mapped files. For Node, the executable carries
  magic `0xfeedfacf`, cputype `0x0100000c`, cpusubtype `0` and `MH_EXECUTE`.
- **Publication.** Each `--apply` created one owned stage under the destination's parent, on its
  device, and that stage no longer exists. Its intent record names that stage, the destination and
  `renamex_np` with `RENAME_EXCL`. The receipt records the call from libSystem with `flag_value: 4`,
  the destination absent before, and `complete_exact` after (2 files and 1 directory; 24 and 13).
- **Sidecars:** each preflight file is the report at preflight (`PREFLIGHT_RECORDED`, not passed, no
  operations). The dry runs have no stage and no intent record.
- **Run:** each run used its plan's reviewed digest, equal to the file's own; stderr is empty.
- **MH preview:** the observer's `_install_receipts`, M0's receipt rule, accepts both `INSTALLED_EXACT`
  receipts with their exact plans. This includes reading the archives again.

## 2. Trees

The trees' parent holds exactly the two trees, with no leftover stage.

- **`node-v24.22.1-darwin-arm64/`:**
  - The tree is exactly the plan, with root `0o755`:
    - `bin/` (`0o755`);
    - `bin/node` (`6f320694…`, 122,545,856 bytes, `0o755`);
    - `NODE-SOURCE.json` (`0o644`).
  - `NODE-SOURCE.json` is byte for byte W1's frozen file and B's committed `NODE-SOURCE.expected.json`
    (976 bytes, `e928a8ec…`).
  - Previews for MH: the observer's `check_node_source` accepts the published file, and
    `read_macho` with `check_node_macho` accepts the published `bin/node`.
- **`reader-c195/`:**
  - The tree is exactly the plan: 24 files (`0o644`) and 13 directories (`0o755`), root `0o755`.
  - The 24 files also equal the C199 manifest's pins, independently of the plan.
  - The package versions are `2.0.0-dev.3.10` (validator) and `0.186.1` (Three.js).
- **Both trees:**
  - There is no link, special file or `.DS_Store`, and every file has one link.
  - M0's `tree_entries`, with `.DS_Store` refused, files private and no links, gives the same map as
    W2's own walk.

## 3. The `.venv`

W2 re-derived the additions from the seven verified wheels and pip 26.0's install code, independently
of venv-expectation.json and of the Director's check.

- **Unchanged since the run:** the `.venv` now equals the after-snapshot exactly. The before-snapshot
  equals W1's frozen `observed_before` (14 entries). Nothing was removed or changed, the launcher
  links and `pyvenv.cfg` included.
- **The 292 added files:**
  - They are exactly the 291 `site-packages` files and `bin/jsonschema`.
  - Each has the re-derived bytes. That includes all seven `RECORD` files, whose bytes W2 rebuilt
    with pip's row algorithm, and the console script (207 bytes, `1cdcd273…`, as predicted).
  - venv-expectation.json holds: 284 files match by digest, and the 7 `RECORD` names and
    `bin_additions` exist.
- **The 39 added directories** are exactly the files' parents.
- **Modes** follow umask 022: 264 files `0o644`; 28 `0o755`, the 27 executable wheel members and
  the script; all directories `0o755`.
- **Nothing else:**
  - There is no bytecode anywhere in the `.venv`.
  - There is no pip, setuptools, wheel, `_distutils_hack`, `.pth` or `.egg-info`.
  - There is no record of the setup tool (`ontokin-environment.json`).
- **Package rule:** the observer's `verify_packages` accepts the `.venv` as it is now.
- **Requires-Dist:** W2's own evaluation of the installed METADATA finds 8 applicable requirements, all
  met, with no unsupported marker. `typing-extensions>=4.4.0; python_version < '3.13'` applies.
- **Framework:** its part is identical before and after (3,788 entries, still 414 bytecode files).
  The before-snapshot's digest `fd8a86d5…` equals the one PLAN-REVIEW-001 computed before the run.
  The observer's `python_inventory` now, Mach-O closure included (111 images, 5 external), has the
  after-snapshot's digest `c277bdd3…`.
- **The parser fix and the rerun are sound in effect.**
  - The fix accepts either quote style, as PEP 508 allows.
  - The rerun read the retained snapshots, which W2 found equal to the live state.
  - Every check the script makes, W2 reproduced independently, with the same result.
  - The record of the failure is incomplete (R-01).

## 4. Conduct

- **Clean at B.** B descends from `6d08e026` and leaves the closure and the inputs unchanged; this
  review also checked that with Git. The step log records the clean state before the runs and after
  them, with no "NOT CLEAN" or "REFUSED" line. The checkout is still clean now: HEAD is B, and the
  only ignored entry is `.venv/`, with no `__pycache__` in the source.
- **The declared environment:**
  - pip ran with exactly the seven declared variables, umask 022 and the worktree root as cwd.
  - The fresh HOME stayed empty, and pip ended with exit 0.
  - The installer record (pip 26.0, 758 files, tree `b58b9187…`) equals W2's recomputation over the
    same tree.
- **The audit** holds 25 starts, and none of them is Node, `ldd` or `codesign`.
  - **pip, 1 start:** the `.venv` interpreter running the base pip's runner.
  - **The doctor, 24 starts:** 18 Git, 5 interpreter starts (each with `-B`), and the one attempt on
    `/nonexistent/node-not-started`. That path does not exist, so the attempt failed before any image
    ran, and the doctor reports that Node did not report a version. It is a failed attempt on an
    absent path, not a Node start.
  - **Others, 0 starts:** the four preparer runs and the preflight.
  - **Limit (P-04):** starts made by pip's child are outside the hook, as section 7 and the staged audit
    summary state.
- **Environment of the preflight.** The separate native-reader preflight ran with `-I -B` in the
  ambient environment, not the declared one. The doctor's own native-reader check, under the declared
  environment, also passed.

## 5. The doctor

The result is exactly the predicted one.
- **`core`:** `ready`.
- **`python-verification`:** `not_checked`, from `pip-check: not_checked` ("pip is not installed"). The
  lock, packages (7), imports (7) and native-reader checks are `ready`.
- **Exit status:** 1.
- **Next action:** the rebuild through `tools/bootstrap_local.py --rebuild`. It was not followed: the
  `.venv` has no pip and no setup-tool record, and it is unchanged since the snapshot.
- **Other profiles:** the visual profile is out of scope. Its `node mismatch` comes from the absent
  path, and `npm missing` from the minimal PATH.

## 6. Retention

Both archives are unchanged at their paths: the Node archive (`89c68259…`, `0o444`, one link) and the
committed C195 archive (`b1e54a6c…`, `0o644`, one link). R-03 extends what must be kept.

## 7. Findings

All three are nonmandatory.

| ID | Location | Issue | Change |
| --- | --- | --- | --- |
| R-01 | `run-001/venv-verify.txt`, `00-steps.txt`; `director/venv_verify.py` | The failed first check is kept as its output only. The failed script was overwritten by the fix and is not preserved, as no copy or digest. The rerun, at 22:17:58Z, came 47 s after the run's last step and its final clean check, and is not in the step log: no command, flags or digest of the fixed script (`ef6cc0f5…`). The traceback's line numbers (55, 67, 144, 171, now 56, 68, 145, 172) fit the stated one-line fix, but cannot exclude another change of equal length. | In the outcome, state that the failed version was not kept. Record the fixed script's SHA-256 and the rerun's command, flags and time, and a clean check after it. W2's independent reproduction of every check supports the result. |
| R-02 | `run-001/doctor.json` and its staged portable copy, `outcome-staging/run-001/doctor.json` | The doctor's `--portable-paths` leaves nine distinct paths of the base installation, under `<prefix>`, which also names its package manager. A9 requires portable copies without machine paths, and the review rules exclude installed-application names. | Label the base prefix (for example `<prefix>`) in the portable copy before commit. |
| R-03 | PREPARATION-PLAN.md section 7, "Retention (P-09)"; the observer's `_install_receipts` | M0's receipt rule reads each `INSTALLED_EXACT` receipt and its exact plan by path and digest, and requires the plan's `report` to equal the receipt's path. The retention statement covers only the archives. | Also keep, unchanged at their paths until MH: the two exact apply plans in `../OntoKin-local/c271-p34/plans/` and the two install receipts in `receipts/` (mode `0o600`). Keep the dry-run receipts and sidecars as evidence. |

## 8. For MH

- **Previews:** M0's receipt rule, tree rule, `NODE-SOURCE.json` rule, Node Mach-O rules, package
  rule and Python inventory all accept the present state. These are previews, not M0.
- **D-16:** the published `bin/node` has a plain `LC_LOAD_DYLIB` of CoreFoundation, which points to MC36
  standing as written. MH decides from M0's own parse.
- **W3's F4:**
  - The framework tree is owner-writable and holds only 414 bytecode files for its 1,969 sources,
    and the `.venv` holds none.
  - Every start of the qualification interpreter until M0 must keep `-B`, and
    `PYTHONDONTWRITEBYTECODE=1` for its children.
  - A slip would change the inventory, and after freezing M0 refuses it (MC32).
- **Report paths:** the exact plans' report paths now exist. Any further preparer run, such as a
  repeat showing `ALREADY_PRESENT_EXACT`, needs report-only variants (W1's F1).
- **Closure:** it records one absent `LC_RPATH` search directory, in a dylib bundled with Pillow. The
  image has no `@rpath` reference (PLAN-REVIEW-001, section 6).

## 9. Conduct of this review and reproduction

- **Starts:** no Node, `ldd` or `codesign` start; pip was not run; no download; no Git write. Git ran
  with `--no-optional-locks`, read commands only.
- **Writes:** only in `reviews/`. Nothing was written into the trees, the `.venv`, the receipts or the
  repository.
- **Python:** the `.venv` interpreter with `-I -S -B`, standard library only, under plan review 001's
  audit hook. The hook refused nothing during the runs, and its self-test passed.
- **Not checked:** A7's workflow, documentation and whitespace checks, and `docs-check-B.txt`, which
  were outside the questions.

Run from `reviews/`, with `PY=<worktree>/.venv/bin/python` and absolute paths in place of the labels.
PART is each of `receipts`, `trees`, `venv`, `conduct` and `retention` in turn:

```sh
$PY -I -S -B result-001/rr_check.py PART <worktree> <local> <prefix>/lib/python3.12/site-packages/pip result-001/rr-PART.json
$PY -I -S -B result-001/rr_digests.py <worktree> <local> result-001/reviewed-files.json
```

`result-001/b-blobs.json` holds B's blob digests, from `git --no-optional-locks show B:<path>`.
RESULT-REVIEW-001.json lists every reviewed file and result with its SHA-256.
