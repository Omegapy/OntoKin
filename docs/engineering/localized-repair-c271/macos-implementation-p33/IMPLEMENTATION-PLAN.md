# C271-P33: implementation plan of gate MI

Gate MI of the adopted contract `ontokin.current-host-readback/0.2.0`, profile
`darwin-arm64-v1` ([CONTRACT](../macos-contract-design-p31/CONTRACT.md),
[CONTRACT.json](../macos-contract-design-p31/CONTRACT.json), adopted design only by
[ADOPTION](../macos-contract-design-p31/ADOPTION.json)). This plan belongs to the
[phase declaration](PHASE.json). It fixes the files, owners, shared interfaces and control
assignment that the workers follow. Where this plan and the contract differ, the contract wins
and the difference is a defect to report, not to work around.

## 1. Scope

MI implements, in source, contract sections 3 to 8: the Darwin supervisor variant (S4), the
preparer route (S6), the host observation M0 and M1 (S3, S7, S10), the provider and probe host
bindings with all provider documents at `/0.2.0` (S7, S10), the driver environment and Git
binding (S9) and the selection rule (S8). The M0 observer is part of MI because the provider
and probe bindings consume its HOST document, MH executes it, and N34-M reviews its Mach-O
parser before MH; no other gate implements it.

MI executes only the controls that need no prepared runtime (section 6). It starts no Node
process, no `ldd` and no `codesign`. It downloads and installs nothing. It does not prepare
the Node runtime, the reader tree or the `.venv` packages (MP). It does not run M0 or M1 on
the real host, the qualifying cohort or N34-M (MH), nor the routine driver or the complete
default routine (MR). Non-Node child processes start only inside focused tests (supervisor
controls, Git metadata, synthetic test children), and each test says what it starts.

## 2. Version separation

- **Byte-identical:** `prototypes/static_tray_v01/supervisor.py`, the 0.1.0 probe
  `current_host_readback_v01.mjs`, the inspector `current_host_inspection_v01.py`, every 0.1.0
  adopted document, and the seven method bodies, `check_case` and the four seam bodies of
  `tests/test_static_tray_readback_v01.py`.
- **Shared files changed:**
  - `current_host_readback_v01.py`: a dispatch by the selected configuration's schema, and the
    fixed ordinary-run reason of S8. Its 0.1.0 functions keep their behaviour.
  - `tools/prepare_current_host_readback.py`: the 0.2.0 route beside the 0.1.0 route, whose
    plans keep their behaviour.
  - `tools/check_local.py`: S8 and S9, which apply to every run of the shared driver.
  - `tests/test_static_tray_readback_v01.py`: its module docstring only.
- **Version refusal:** each version's entry points refuse the other version's documents.
- **Probe body:** the 0.2.0 probe copies the scientific body of the 0.1.0 probe without semantic
  change. The preserved segments are kept byte-identical, and a reviewed token-equivalence
  check covers them, as P05 section 6 requires for preserved JavaScript segments.
- **Expectation changes:** an existing test whose expectation S8 or S9 changes is updated only to
  the adopted rule, and each such change is listed with the rule in the worker's interface note.
  No other existing expectation changes.

## 3. Files and owners

Workers share this checkout for disjoint files under the Director's commits, as PROTOCOL
section 4 allows. No worker runs a Git command that writes (`add`, `commit`, `stash`,
`checkout`, `reset`, `switch`, `restore`, `merge`, `rebase`, `push`) or installs a package.
Each writes its detailed evidence under `../OntoKin-local/c271-p33/workers/<id>/` beside the
clone, and its interface note in this directory's `interfaces/`.

| Worker | Component | Exclusive writes |
| --- | --- | --- |
| W1 | Darwin supervisor (S4) | `prototypes/static_tray_v01/supervisor_darwin_v01.py`, `tests/test_supervisor_darwin_v01.py`, `interfaces/W1-SUPERVISOR.md` |
| W2 | Preparer route (S6) | `tools/prepare_current_host_readback.py`, `tests/test_prepare_current_host_readback_v02.py`, `interfaces/W2-PREPARER.md` |
| W3 | M0 and M1 observer (S3, S7, S10) | `prototypes/static_tray_v01/current_host_observation_v02.py`, `tests/test_current_host_observation_v02.py`, `interfaces/W3-OBSERVER.md` |
| W4 | Driver (S8, S9) | `tools/check_local.py`, `tests/test_local_checks.py`, `tests/test_current_host_readback_driver.py`, the docstring of `tests/test_static_tray_readback_v01.py`, `interfaces/W4-DRIVER.md` |
| W5 | Provider and probe (S7, S8, S10) | `prototypes/static_tray_v01/current_host_readback_v02.py`, `prototypes/static_tray_v01/current_host_readback_v02.mjs`, the dispatch in `prototypes/static_tray_v01/current_host_readback_v01.py`, `tests/test_current_host_readback_provider_v02.py`, `interfaces/W5-PROVIDER.md` |
| W6 | Independent control author | `tests/test_current_host_readback_controls_v02.py`, `CONTROLS-FROZEN.json` |
| W7 | Independent reviewer | `INDEPENDENT-REVIEW-001.md` and `.json` |

Order: W1, W2 and W3 in parallel; W4 after W1; W5 after W2, W3 and W4; W6 after W5; the
Director executes the frozen controls and the focused tests; W7 last. W6 and W7 have fresh
context and wrote none of the implementation.

## 4. Shared interfaces

### 4.1 Darwin supervisor (W1)

`supervisor_darwin_v01.run_process` has the original signature and receipt fields. It imports
`Clock`, `Stop`, `LIMITS`, `inventory`, `group_exists`, `terminate_group` and `json_bytes`
unchanged from `supervisor.py`. Its only change replaces the `prctl(PR_SET_CHILD_SUBREAPER)`
precondition with the Darwin precondition: `sys.platform == "darwin"`, machine `arm64`, and
`sysctl.proc_translated` equal to 0 through `sysctlbyname`. An unreadable value fails closed.
A failed precondition raises `Stop("OTRAY-E-BACKEND", …)` before any start.

### 4.2 Runtime directory and `NODE-SOURCE.json` (W2 writes; W3 and W5 read)

The task-specific runtime directory holds exactly `bin/`, `bin/node` and `NODE-SOURCE.json`.
`NODE-SOURCE.json` holds these canonical JSON bytes (`prototypes/static_tray_v01/canonical.json_bytes`):

```json
{
  "schema": "ontokin.current-host-readback-node-source/0.2.0",
  "contract": "ontokin.current-host-readback/0.2.0",
  "archive": {"name": "node-v24.22.1-darwin-arm64.tar.gz",
              "sha256": "89c682593d76cd44233fa53b1563264e7de9cbb189cad169135c5b4fadfbc0a7",
              "size_bytes": 0},
  "checksum_file": {"url": "https://nodejs.org/dist/v24.22.1/SHASUMS256.txt",
                    "sha256": "fdfbffc969c0f604beff0124d409b33a43b53f5c681d6220f80023e0d6df9dc4",
                    "size_bytes": 3171},
  "signature_check": {"status": "not_performed", "detail": "…"},
  "member_inventory_sha256": "…",
  "extracted": {"member": "node-v24.22.1-darwin-arm64/bin/node", "path": "bin/node",
                "sha256": "…", "size_bytes": 0, "mode": "0o755"}
}
```

- **Sizes:** the zeros stand for the observed integers.
- **Signature check:** `status` is one of `not_performed`, `verified` or `failed`.
- **`member_inventory_sha256`:** the SHA-256 of the canonical JSON bytes of the frozen member
  inventory, as W2 defines it.
- **Frozen bytes:** the preparation plan freezes the document's exact bytes. The preparer
  builds the document from the plan and refuses if the bytes differ.

### 4.3 HOST document (W3 writes; W5 reads)

`ontokin.current-host-readback-host/0.2.0` holds the fields of contract section 7. Among them
are the executor label `macos-arm64-local` and the Git binding: an absolute canonical path
that is not `/usr/bin/git`, with its SHA-256, size, mode and version. The environment record
holds the declared environment and `cf_user_text_encoding`, a string or null. W3 documents the
exact shape in `interfaces/W3-OBSERVER.md`, and W5 consumes that shape unchanged.

### 4.4 Python helpers in the observer (W3 exports; W5 imports)

The observer is one file that uses only the standard library. Its main path runs under
`-I -S -B` (E15), so it adds the bound source root to `sys.path` explicitly, as needed for the
Darwin supervisor of M1. It exports at least these helpers:
- `environment_admitted(observed, declared, recorded_cf)`: true exactly when `observed` equals
  `declared`, or equals `declared` plus `__CF_USER_TEXT_ENCODING` with the value `recorded_cf`,
  a non-empty string. `declared` never contains that name.
- `canonical_path(value)`: an absolute path whose only symbolic-link ancestors are `/tmp`,
  `/var` and `/etc`, returned as its `realpath`. Any other symbolic-link ancestor refuses.
- The OS identity reader (`SystemVersion.plist`, and the cryptex copy if present).
- `sysctlbyname` readers for `sysctl.proc_translated` and `kern.bootsessionuuid`.
- The Python installation-tree inventory and its exact-set comparison.
- The Mach-O parser, with its Node rules and its Python rules.

The 0.2.0 probe reimplements `environment_admitted` with the same meaning.

### 4.5 Git binding (W4 implements; W5 calls)

`tools/check_local.py` exposes two functions, and every Git start in the driver and the
providers goes through `git_executable()`:
- **`bind_git(path, sha256)`:** binds an absolute canonical regular file other than
  `/usr/bin/git`. It refuses a mismatching digest.
- **`git_executable()`:** returns the bound path, after checking its SHA-256 again. Unbound
  ordinary runs resolve `git` on `PATH` once to an absolute path; the summary records it as
  unbound.

A qualifying run binds Git before its first Git start, from
`current_host_readback_v01.git_binding_from_selection(config_path, config_sha256)`. That
function reads the digest-checked configuration and its HOST document, starts no Git, and
returns `{"path", "sha256"}` for a 0.2.0 selection and `None` for a 0.1.0 selection. The 0.2.0
provider binds Git the same way in the unit process before its own source reads.

### 4.6 Selection rule (W4 and W5)

- **Ordinary run** (neither argument): the driver proceeds, records
  `readback_selection: {"status": "absent", "run_kind": "ordinary"}`, and passes no selection.
  `setup_cpu_cohort` raises a visible error whose text contains exactly
  `No approved current-host readback selection: ordinary run, not a qualification`. It is never
  a skip.
- **Partial selection:** fails preparation in the driver, and fails at setup on direct
  invocation.
- **Qualifying run** (both arguments): every existing rule applies, the record adds
  `"run_kind": "qualifying"`, and the facade dispatches on the schema of the
  digest-checked configuration.

### 4.7 Driver environment (W4)

Where the driver applies its removal list to the unit process, the list is: `PYTHONPATH`,
`PYTHONHOME`, `PYTHONSTARTUP`, `PYTHONINSPECT`, `PYTHONBREAKPOINT`, `PYTHONUSERBASE`,
`PYTHONPYCACHEPREFIX`, `LD_PRELOAD`, `LD_LIBRARY_PATH`, `NODE_OPTIONS`, `NODE_PATH`, every
variable whose name starts with `DYLD_`, `__PYVENV_LAUNCHER__` and `PYTHONEXECUTABLE`.

### 4.8 Facade dispatch (W5)

The entry points of `current_host_readback_v01` dispatch by the schema of the digest-checked
configuration: `/0.1.0` to the unchanged 0.1.0 code, `/0.2.0` to `current_host_readback_v02`,
anything else refuses. The entry points are `validate_selection`, `derive_workspace_binding`,
`prepare_case_manifest`, `verify_case_manifest`, `guarded_run_process`, `setup_cpu_cohort`,
`finish_cpu_cohort` and `git_binding_from_selection`.

## 5. Results and labels

Every 0.2.0 result and refusal document carries the labels of contract section 10:
- the executor label `macos-arm64-local`;
- the contract;
- the OS product version, build and cryptex version;
- the Node archive and executable pins;
- the Python installation inventory digest;
- the Git binding;
- the run kind.

A simulated or mocked boundary is labelled as such wherever its result is recorded.

## 6. Control assignment

An independent author (W6) freezes the exact inputs and expected outcomes of every control
that MI executes, before the Director executes them. Expectations come from the contract. An
implementation defect is corrected in the implementation, never in a frozen expectation. A
defect in a frozen control is recorded and refrozen by the independent author, and the
original stays retained.

| Gate | Controls |
| --- | --- |
| MI, executed | MC01 to MC10, MC12 to MC22, MC29, MC31 to MC35 |
| MI, in part | MC11: the scanner, run on the 0.2.0 probe (the reader files exist only after MP). MC23: the driver's decision on synthetic unit results. MC30: the Python-side predicate of M0 and the provider. |
| MH | MC11 on the module loader and the 24 reader files, MC24 to MC28, MC30 for the probe, MC36 |
| MR | MC23 on a real qualifying run, and MC28 on the complete default inventory |

Labels:
- **Simulated at a boundary and labelled:** MC08, MC09, MC10 (mocked, as the contract states),
  MC17, MC29, and the `ENOTSUP` case of MC16.
- **Real:** MC15 and MC16's failing call (a cross-volume `renamex_np`).

## 7. Checks

All commands run from the worktree root with `.venv/bin/python -B` and a resolved temporary
directory, `TMPDIR="$(cd "$TMPDIR" && pwd -P)/"`.

- the new focused test modules and the frozen control module;
- the existing modules that cover the changed shared files, which keep their 0.1.0
  expectations apart from the changes listed under section 2:
  - `tests.test_current_host_readback_provider`;
  - `tests.test_current_host_readback_driver`;
  - `tests.test_local_checks`;
  - the inspector's five modules;
- `tools/chat_workflow.py check`, the documentation verifier and a scoped whitespace check.

The routine driver is not run: its complete routine is gate MR's, and the `python-verification`
profile is missing in this worktree until MP. The test methods that MI adds change the default
inventory. The outcome lists them as additions that MH's execution plan must approve (MC28).
