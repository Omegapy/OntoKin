# W4: driver selection rule (S8), unit environment and Git binding (S9)

Worker W4 of gate MI, C271-P33. The assignment named base `a23761919e92`. During the work the
checkout's head moved to `5dc76ccf` and then `86a0e750`. The added commits carry amendment 001,
W2's checkpoint and the Director's decisions, and none of them touches W4's files.
This note covers development work only. It is not frozen and not reviewed. It implements
[plan sections 4.5 to 4.7](../IMPLEMENTATION-PLAN.md#45-git-binding-w4-implements-w5-calls) under
[contract section 8](../../macos-contract-design-p31/CONTRACT.md#8-selection-rule-s8) and the
Environment and Git rows of
[contract section 7](../../macos-contract-design-p31/CONTRACT.md#7-host-observation-in-place-of-h0-and-h1-s3-s7-s9).
Changed source: [`tools/check_local.py`](../../../../../tools/check_local.py).
Sections 7 and 8 record two findings: a part of MC23 and a part of plan section 4.5 that this work
does not meet.

## 1. The `readback_selection` records

| Run | Arguments | Record | Outcome |
| --- | --- | --- | --- |
| Ordinary | neither | exactly `{"status": "absent", "run_kind": "ordinary"}` | every stage runs; no selection reaches any step |
| Partial | exactly one | as before, with no `run_kind` | preparation fails before any Git start |
| Qualifying | both | as before, plus `"run_kind": "qualifying"` | every existing rule, then the Git binding |

- **Ordinary:**
  - The record is written for every run without arguments, whatever the plan holds.
  - Nothing prepares a selection or calls the provider's facade.
  - A later run error is not attached to this record.
  - The readback class then fails at setup inside the unit process, and the driver reports that
    stage as failed. The driver does not mask that error or turn it into a skip.
- **Partial:** the keys are as before: `status`, `config_path`, `expected_config_sha256`,
  `approval_source` and, on failure, `preparation_or_execution_error`. The error text starts
  `Partial readback selection:` and still names `EXPECTED_DIGEST`.
- **Qualifying:** `run_kind` is the record's second key. The statuses are unchanged:
  `preparation_pending`, `original_verified`, `workspace_bound`.
- **Summary keys:**
  - `git` is `null` until it is read. It is now read after the selection preparation, and it
    stays `null` when that preparation fails.
  - `git_binding` is new (section 3).

## 2. Removal list and its scope

`UNIT_REMOVED_ENVIRONMENT` holds the existing eleven names, then `DYLD_*`, then
`__PYVENV_LAUNCHER__` and `PYTHONEXECUTABLE`:
- the existing names are `PYTHONPATH`, `PYTHONHOME`, `PYTHONSTARTUP`, `PYTHONINSPECT`,
  `PYTHONBREAKPOINT`, `PYTHONUSERBASE`, `PYTHONPYCACHEPREFIX`, `LD_PRELOAD`, `LD_LIBRARY_PATH`,
  `NODE_OPTIONS` and `NODE_PATH`;
- `DYLD_*` means every name that starts with `DYLD_`, matched case-sensitively.

`unit_environment_removals(environment)` returns the names present, in the list's order, with
the `DYLD_` names sorted. The step record keeps its key `removed_injection_environment_names`.

**Scope, unchanged.** The list applies only in `execute_step`, only to the step `unit-tests`, and
only when the run passes a derived selection. That is the unit process of a qualifying run, after
the derived configuration's digest check. Ordinary runs and every other step do not apply it.
Around it, nothing changed:
- every step loses the two selection variables;
- `git_environment` replaces every `GIT_*` name;
- every step gets `PYTHONDONTWRITEBYTECODE=1`;
- where the list applies, the driver also sets the derived selection pair and `PYTHONNOUSERSITE=1`.

CPython removes `__PYVENV_LAUNCHER__` from its own environment at startup; this was observed with
the worktree's `.venv` interpreter. A child therefore cannot show that variable's removal, so the
test checks the mapping that the driver passes.

## 3. Git binding API

- **`bind_git(path, sha256) -> dict`.** It binds the executable that every later driver Git start
  in this process uses. The checks run in this order:

  | Check | Refusal |
  | --- | --- |
  | `sha256` is 64 lowercase hexadecimal characters, without a prefix | malformed digest |
  | `path` is a `str` or path object, and absolute | relative path |
  | `path` is not `GIT_DISPATCHER`, which is `/usr/bin/git` | dispatcher path |
  | `lstat` succeeds | missing or unreadable |
  | not a symbolic link | symbolic link |
  | a regular file | non-regular file |
  | `normpath(path) == path` and `realpath(path) == path` | non-canonical path, including a linked ancestor |
  | its device and inode differ from the dispatcher's | the dispatcher under another name |
  | its SHA-256, read with `O_NOFOLLOW` and stable during the read, equals `sha256` | digest mismatch |
  | that digest differs from the dispatcher's | a copy of the dispatcher's bytes |
  | no other executable is already bound | second binding |

  Binding the same path and digest again changes nothing. The result, which is also the summary
  record, is `{"path", "sha256", "bound": true, "source": "selection"}`. The dispatcher rules
  follow the macOS meaning of `/usr/bin/git`. Only 0.2.0 selections bind Git, and they exist only
  on macOS arm64.
- **`git_executable() -> str`.**
  - **Bound:** every call checks the path rules and the SHA-256 again. A failure raises
    `GitBindingError` and never falls back to `PATH`.
  - **Unbound:** the first call resolves `git` once with `shutil.which`, makes it absolute with
    `os.path.abspath`, and records `{"path", "sha256", "bound": false, "source": "PATH"}`.
    - The digest is `null` if the file cannot be read.
    - If no `git` is found, it raises `FileNotFoundError` and caches nothing. The summary then
      records `"path": null` with a `reason`.
- **`GitBindingError`** is a `ValueError`. `git_metadata` catches only `OSError` and
  `SubprocessError`. A refused or changed binding therefore fails the run. It never reads as
  "Git metadata unavailable". An unbound missing `git` keeps today's unavailable result.
- **State:** the module global `_GIT_STATE` holds it for the whole process. There is no public
  unbind. Tests isolate it with `patch.object(check_local, "_GIT_STATE", None)`.
- **`bind_selection_git(config_path, config_sha256)`:**
  - It imports `git_binding_from_selection` from `prototypes.static_tray_v01.current_host_readback_v01`
    by name, and calls it with the same two arguments.
  - It binds a returned object that holds exactly `path` and `sha256`. For `None`, the 0.1.0 case,
    it binds nothing.
  - Any other shape is refused. Any exception, including the missing name before W5 lands,
    becomes `GitBindingError("Cannot read the selection's Git binding: …")`.
- **Git starts in `check_local.py`:** the only one is `git_read`, which uses `git_executable()`.
  Its callers are `git_metadata`, `prepare_workspace_git`, the provider's `_verify_source` and the
  0.1.0 inspector's `_check_git`. `git_environment` and the signature of `git_read` are unchanged.
- **For W5:** in the unit process, call `tools.check_local.bind_git(path, sha256)` before the
  provider's own source reads. The driver's binding is the same one, so a repeat is harmless.

## 4. The qualifying-run call sequence

1. `prepare_output`. The first summary is written with `"git": null`.
2. `build_plan`, then the `readback_selection` record with `run_kind`.
3. `prepare_readback_selection`:
   1. both arguments, an absolute path and the digest format, as before;
   2. `readback_config_identity` and the comparison with the expected digest, as before;
   3. `bind_selection_git`: the facade, then `bind_git`;
   4. the provider's `validate_selection`, which makes the run's first Git start, now bound;
   5. the evidence-root check.
4. `summary["git_binding"]`, then `summary["git"] = git_metadata(root)`.
5. Unchanged from here: the inventory, the workspace copy, `workspace_git`,
   `bind_readback_workspace`, the steps with the removal list, and `git_after`.

## 5. Changed existing tests

| Test, in `tests/test_current_host_readback_driver.py` | Change | Rule |
| --- | --- | --- |
| `test_missing_explicit_selection_cannot_use_ambient_approval` | **Expectation.** It used to expect refusal at preparation. It now expects an ordinary run that proceeds, records `absent`/`ordinary`, and whose unit child sees neither ambient selection variable. | S8 ordinary run; the existing removal of the selection variables |
| `test_failed_prelaunch_is_recorded_unexecuted_even_if_later_inventory_fails` | **Harness adaptation.** It now passes the selection pair to `run()`; its mocks and assertions are unchanged. No facade mock is needed, because the binding sits inside the mocked `prepare_readback_selection`. | S8: a selection is prepared only when the caller gives both arguments |

Nothing else changed:
- **`tests/test_local_checks.py`:** unchanged. Its `execute()` helper gives no selection, so its
  runs are now ordinary. Its patches of `prepare_readback_selection` and `bind_readback_workspace`
  are no longer reached, and all 33 tests pass as they are.
- **The driver test module:** only its docstring changed.
- **`tests/test_static_tray_readback_v01.py`:** only the module docstring changed. The bytes
  outside it and the AST without it are identical, and the nine `ORIGINAL_BODIES` digests match.

## 6. New tests

All 17 are in `tests/test_current_host_readback_driver.py`. They add to the default inventory, and
MH's execution plan must approve them (MC28). "Stand-in" means a `/bin/sh` script in a temporary
directory that logs its arguments.

| Class.method | Covers | Starts |
| --- | --- | --- |
| `SelectionRuleTests.test_ordinary_run_proceeds_and_the_readback_setup_error_stays_visible` | MC22 | one synthetic unittest discovery, two trivial Python stages, read-only Git metadata reads of temporary directories |
| `SelectionRuleTests.test_qualifying_preparation_refuses_missing_partial_malformed_mismatched_and_unapproved_selections` | MC21, partial rule | nothing |
| `SelectionRuleTests.test_qualifying_run_binds_git_before_its_first_git_start` | 4.5 order | the bound stand-in, 3 times |
| `SelectionRuleTests.test_qualifying_0_1_0_selection_keeps_the_path_git_resolved_once` | 4.5, 0.1.0 | the `PATH` stand-in, 3 times |
| `SelectionRuleTests.test_qualifying_run_fails_closed_before_any_git_start_when_git_cannot_be_bound` | fail-closed facade call | nothing |
| `UnitEnvironmentTests.test_removal_list_is_the_existing_names_every_dyld_name_and_two_launcher_names` | 4.7 | nothing |
| `UnitEnvironmentTests.test_each_new_removal_name_is_stripped_from_the_qualifying_unit_process` | MC07, driver part | one synthetic Python unittest child |
| `UnitEnvironmentTests.test_removal_list_keeps_its_present_scope` | scope | nothing; the start is mocked |
| `DriverGitBindingTests.test_bound_absolute_git_is_what_every_driver_git_start_runs` | absolute bound path | the bound stand-in, once |
| `DriverGitBindingTests.test_bind_refuses_relative_noncanonical_linked_nonregular_dispatcher_and_mismatched_paths` | refusals, `/usr/bin/git` | nothing |
| `DriverGitBindingTests.test_bind_refuses_the_dispatcher_file_under_another_name_and_a_copy_of_its_bytes` | dispatcher identity and bytes | nothing |
| `DriverGitBindingTests.test_bound_git_is_checked_again_at_every_start_and_never_falls_back_to_path` | re-check | the bound stand-in, once |
| `DriverGitBindingTests.test_a_second_binding_to_another_executable_is_refused` | single binding | nothing |
| `DriverGitBindingTests.test_unbound_git_is_resolved_once_on_path_to_an_absolute_path` | unbound resolution | nothing |
| `DriverGitBindingTests.test_unbound_git_absent_from_path_leaves_git_metadata_unavailable` | unbound absence | nothing |
| `QualifyingUnitDecisionTests.test_any_skip_error_failure_or_expected_failure_fails_the_qualifying_unit_stage` | MC23, in part | one synthetic unittest discovery for each of 10 cases |
| `QualifyingUnitDecisionTests.test_qualifying_run_with_an_expected_failure_in_its_unit_stage_fails` | MC23, run level | one synthetic unittest discovery, read-only Git metadata reads of temporary directories |

None of them starts Node, `ldd` or `codesign`.

## 7. MC23: the driver's rule, and its gap

The rule exists in `execute_step`, as `complete_regression_passed`:
- a skip of a method or of a class fails the stage;
- so does an expected failure, although its exit status is 0;
- an error, a failure, an unexpected success or a class-level setup or teardown error fails it
  through the non-zero exit;
- no test fails it through the zero count, and exit status 5 on Python 3.12.

The first new MC23 test proves each of these cases on synthetic unit results.

The rule covers the complete unit stage of every run. It is not specific to the readback cohort.

**Missing method: no driver rule exists, and none was added.** A qualifying run fails on a
missing method only when the unit process reports it as an error. The provider does that at setup
(`_verify_methods`) and at teardown (`finish_cpu_cohort`). A cohort that lacks a method without
any error passes the driver's unit stage (evidence F1, section 9). A readback class that is never
discovered at all is not detected by the driver either. MC28, at MH and MR, is the control for that.

## 8. Finding outside W4's files: storage Git starts are unbound

`tools/storage_identity.py` starts `git` by name, using `PATH`. `check_local.prepare_workspace`
reaches it through `prepare_offline_workspace` in every run whose source has Git:
- four starts each time: `rev-parse` three times and `ls-tree`;
- more with committed attributes (`init`, `cat-file`, `check-attr`) or LFS files (`rev-parse`,
  `config`).

In a qualifying 0.2.0 run, those starts bypass `git_executable()`. Evidence F2 shows 21 driver
starts through the binding and 4 storage starts from `PATH`. Plan section 4.5's "every Git start in
the driver" is therefore unmet for them. The file is outside W4's writes.

There are two ways to resolve it, and the choice is the Director's:
- route `storage_identity.git()` through `check_local.git_executable()`, imported inside the
  function, because `check_local` imports `storage_identity`;
- record an exception.

## 9. Checks and evidence

The evidence is in `../OntoKin-local/c271-p33/workers/W4/`, beside the clone. Every command ran
from the worktree root with `.venv/bin/python -B` and a resolved `TMPDIR`.

| Check | Before | After |
| --- | --- | --- |
| `tests.test_local_checks tests.test_current_host_readback_driver` | 43 tests, OK | 60 tests, OK; also OK under the unresolved default `TMPDIR` |
| `tests.test_static_tray_readback_v01` | 4 ok, 1 class-level setup error (no selection) | identical |
| `tools.storage_tests.test_storage_identity` | 7 ok, 8 errors (no `git-lfs` client) | identical |
| Docstring-only comparison | | passed (`docstring-only-check.json`) |
| Mutations M1 to M5 of the new behaviour | | each one detected (`mutation-sensitivity.json`) |
| The new tests against the committed driver | | the S8 test fails, and the other new tests error (`new-tests-against-head-driver.txt`) |
| F1 and F2 | | `driver-rule-findings.json` |

No test of the two required modules fails, before or after, for a missing package or for the
readback provider. The one setup error of `tests.test_static_tray_readback_v01` comes from the
absent selection, and the eight storage errors from the missing `git-lfs` client; both are
unchanged. The provider and inspector test modules were not run. They import W2's preparer, and
the assignment keeps W2's work out of W4's checks. Plan section 7 assigns them to the Director.
