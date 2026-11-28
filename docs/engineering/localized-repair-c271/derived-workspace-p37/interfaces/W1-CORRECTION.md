# W1: the derived workspace's source check (FZ-01) and the workspace index refresh (FZ-02)

Worker W1 of C271-P37, stage S3, for Director `c271-p37-08beec34eb0a`. Base: the declaration commit
`2f728998456c829f3cdc13bbf72d6dd805fefa36`. This note implements [DECISION-001](../DECISION-001.md) and
is written for the independent control author of S4. It covers development work only: nothing here is
frozen or reviewed. The tests named here are the author's focused tests, not controls. `<local>` is the
data root beside the clone.

## 1. Changed files

| File | Change | SHA-256 at this note |
| --- | --- | --- |
| `tools/check_local.py` | `copied_source_path`, `refresh_workspace_index`; `git_metadata` and `prepare_workspace` call them | `3136f52cef8ca4492e06f6c12898ea9f6e9f101eb5b34e4fed5c61b8b9be5ab8` |
| `prototypes/static_tray_v01/current_host_readback_v02.py` | `_copied_names`; rule B in `_verify_source`; `_verify_parent` returns the record; `_selection` passes it on | `bab89614c9ceeeaae56e9e264937cae482feda5bf08bda13c5972ad7412f902b` |
| `tests/test_local_checks.py` | one new class, `CopiedSetAndWorkspaceIndexTests` (6 tests) | `0ceb6b8342178322d3253e7e1c733add498564a43f521b6ec8653ee56f7e6125` |
| `tests/test_current_host_readback_provider_v02.py` | three new classes (15 tests), one import and one docstring paragraph | `95e04a46ad8a3a0691b40e7a2809154040a7a272c0a25c60e86c48540dbafc83` |

No other file changed. In both test modules, every existing class and method is unchanged.

## 2. Functions and their contracts

### 2.1 `tools/check_local.py`

- **`copied_source_path(name: str) -> bool`** says whether a repository-relative path, in Git's
  `/`-separated form, lies in the driver's copied set.
  - **The rule:** `(parts[0] in SOURCE_DIRS or name in ROOT_FILES) and not any(ignored(part) for part in parts)`,
    where `parts = name.split("/")`.
  - **Its standing:** it is the copied set's one path-level definition. `prepare_workspace`'s copy and
    `source_files`' inventory select the same files by walking the same constants with `ignored()`.
  - **It starts nothing**, and it raises nothing for a string.
  - **Examples:** true for `tests`, `README.md`, `docs/README.md` and `tools/Build/x.py`. False for
    `.claude`, `.claude/.gitignore`, `Makefile`, `Tests/x.py`, `readme.md`, `tools/build/x.py`, a
    `.pyc` file and an `.env` file. The comparison is case-sensitive.
- **`git_metadata(root)`:** its `untracked_source_files` is
  `[name for name in <ls-files --others -z> if name and copied_source_path(name)]`, the same
  expression as before, now named. Its output is unchanged.
- **`refresh_workspace_index(workspace: Path) -> None`** runs
  `git_read(workspace, "update-index", "-q", "--refresh", timeout=120)`: one Git start, through
  `git_executable()`.
  - On `OSError` or `SubprocessError` it raises
    `ValueError("Cannot record the isolated workspace's index stat data: <error>")`.
  - A `GitBindingError` from `git_executable()` propagates unchanged.
- **`prepare_workspace(root, output, full, *, source_git=None) -> Path`**, unchanged apart from one
  step: when `source_git["available"]`, it calls `refresh_workspace_index(workspace)`. That call comes
  after `prepare_offline_workspace` and the write of `workspace-storage.json`, and before the
  `node_modules` link of `--full`. Without Git nothing changes.
- **Its effect:** every run whose source has Git makes one more Git start. Summary fields and values
  are unchanged.

### 2.2 `prototypes/static_tray_v01/current_host_readback_v02.py`

- **`_verify_parent(config, *, check=...)`** returns `None` for an original configuration (`parent` is
  null). For a derived one it returns the workspace binding's `source_before` document, after the
  unchanged proof. That document is the driver's `inventory()` record
  `{"sha256", "file_count", "files": [{"path", "sha256", "bytes"}]}`.
- **`_selection(...)`** calls
  `_verify_source(config["source"], git=..., derived=config["parent"] is not None, own_root=..., check=..., copied=<what _verify_parent returned>)`.
  Nothing else in it changed.
- **`_copied_names(copied) -> set[str]`** gives the case-folded `path` of every record entry. It refuses
  with `CH-WORKSPACE`, `The copied-source inventory record is malformed`, unless `copied` is a `dict`
  whose `files` member is a `list` of `dict`s with a `str` `path`.
- **`_verify_source(source, *, git, derived=False, own_root=True, check=lambda: None, copied=None)`:**
  - **Unchanged order:** the root and identity checks; the Git binding; the source set's file-by-file
    binding; then the five Git reads.
  - **New:** with `derived` true and `copied` not `None`, it calls `_copied_names(copied)` right after
    the binding of the source set and before the first Git read.
  - **Status lines:** each line is `line`, with `name = line[3:]`. It is admitted when
    `(generated or uncopied) and " -> " not in name and not name.startswith('"')`:
    - `generated` is `derived` and `immutable_workspace_inputs` drops `name`. This is unchanged.
    - `uncopied` needs a record, `line[:3] == " D "`, no component of `name` that is `""`, `.` or `..`,
      `not copied_source_path(name)`, and `name.casefold()` absent from the record's folded names.
  - **Refusal:** `CH-SOURCE`, `Dirty source: ` followed by the whole line.
  - **Untracked names:** unchanged. A name is admitted only when `derived` holds and the name is a
    generated example. Otherwise the check refuses with `CH-SOURCE`, `Untracked source input: `
    followed by the name.
  - **Callers that pass no `copied`,** such as MI's frozen MC19 controls with `derived=False`, behave
    exactly as before. A derived call without `copied` admits no deletion.
- **Unchanged:** the 0.1.0 provider, `current_host_readback_v01.py`. Its `_verify_source` still refuses
  these deletions, which is the recorded follow-up for the Linux route.

## 3. How to build a derived workspace with real Git in a test

This is the recipe of `DerivedWorkspaceTests` in `tests/test_current_host_readback_provider_v02.py`.

1. **A canonical temporary base:** `Path(os.path.realpath(tempfile.TemporaryDirectory(...).name))`.
   `bind_git` and the provider refuse non-canonical paths and linked ancestors.
2. **Isolated Git state:** `patch.object(check_local, "_GIT_STATE", None)`, started in `setUp` and
   stopped in cleanup.
3. **A bindable Git.**
   - Write a `/bin/sh` wrapper, mode `0o755`, that logs `"$*"` and runs `exec '<shutil.which("git")>' "$@"`.
   - Bind it with `check_local.bind_git(path, sha256)`.
   - Do this before the fixture's Git commands, so that every driver, storage and provider Git start
     runs it.
   - Under `PATH=/usr/bin:/bin`, `shutil.which("git")` is `/usr/bin/git`, the macOS dispatcher, which
     `bind_git` refuses to bind directly.
4. **The checkout.**
   - **Inside the copied set:**
     - every path of `v02.SOURCE_FILES` and a file in each of `v02.SOURCE_TREES`, which the source
       set's binding requires;
     - `v02.PROVIDER` and `v02.PROBE`; `README.md`; and `docs/notes.md`, a copied file outside the
       source set, whose changes therefore reach the status rule;
     - `.agents/skills/alpha/SKILL.md`, and the generated example `examples/visual/demo-data.js`.
   - **Outside it:** `.claude/.gitignore`, and the link `.claude/skills/alpha -> ../../.agents/skills/alpha`.
   - **Old modification times:** set every file to now minus 120 s with `os.utime`. The copy keeps
     them, so no workspace index entry is racy.
   - **The commit:** through `check_local.git_read(root, ...)`, run `init --quiet --template=`, then
     `add -A`, then `-c user.name=<name> -c user.email=<address>@example.invalid commit --quiet -m <message>`.
5. **The record:** `copied = check_local.inventory(root)`, the derivation's `source_before`.
6. **The workspace:** make a fresh `output` directory, then call
   `workspace = check_local.prepare_workspace(root, output, False)`. This is the driver's own copy,
   followed by the workspace Git (`init`, `fetch`, `update-ref`, `read-tree`), storage and the refresh.
   `check_local.inventory(workspace) == copied` holds, and the status is
   `[" D .claude/.gitignore", " D .claude/skills/alpha"]`.
7. **The source record.**
   - Write `canonical(v02.source_inventory(workspace))` to a file outside the workspace, mode `0o644`,
     with one link only.
   - The record is `{"root": str(workspace), "commit": <rev-parse HEAD>, "tree": <rev-parse HEAD^{tree}>, "inventory": descriptor(file)}`.
8. **The check:** `v02._verify_source(source, git={"path", "sha256"}, derived=True, own_root=False, copied=copied)`.
   It makes five Git starts, each logged as `-c core.fsmonitor=false -C <workspace> <arguments>`. The same call
   with `derived=False` is the original route.

**Making each status form.**
- `D ` (a staged deletion): `git rm --quiet --cached -- <path>` in the workspace.
- `R  a -> b`: `git mv a b`.
- ` M` at an uncopied path: write that path with other bytes.
- ` T` at the link's path: write a regular file there.
- ` T` at a copied file: replace it with a link.
- ` D`: unlink the file.
- A same-size ` M`: write the same number of bytes and restore the old `atime` and `mtime` with
  `os.utime(ns=...)`. Wait more than one second after the copy first; a Git that compares whole seconds
  of change time needs it.
- Quoted names: track an uncopied path with a `"` or a non-ASCII letter. Take the expected line from
  the workspace's own status.
- A link inside the copied set: the driver's `prepare_workspace` and `inventory` refuse it. To obtain
  its ` D` line, copy `SOURCE_DIRS` and `ROOT_FILES` without the link, then call
  `check_local.prepare_workspace_git(root, workspace, check_local.git_metadata(root))` and
  `check_local.refresh_workspace_index(workspace)`. Use `check_local.inventory(workspace)` as the record.

**Things to avoid.**
- The account's global Git ignore file applies to `ls-files --others` (Q-10 of MR's freeze review).
  Choose untracked fixture names that it cannot ignore.
- A stand-in Git that answers from files is needed only for exact lines that real Git cannot be made to
  print: unmerged forms, `C`, unsafe names. `DerivedStatusLineTests` uses W5's stand-in pattern.
- A full `derive_workspace_binding` needs a HOST, dependencies and methods. W1's tests check the parent
  proof's return value, and the passing of `copied` with patched boundaries, instead.

## 4. Cases, with codes and reasons

Accepted means `_verify_source` returns the source document.

**Derived route, accepted:**
- with real Git: the workspace above, whose status is ` D .claude/.gitignore` and ` D .claude/skills/alpha`;
- with real Git: the same, with `.claude/.gitignore` present again with the commit's bytes, which
  leaves no line for it;
- with real Git: a generated example changed (` M examples/visual/demo-data.js`) or deleted
  (` D examples/visual/demo-data.js`), and an untracked generated product `examples/visual/scene.glb`;
- exact lines: ` D P` for P in `.claude/.gitignore`, `.claude/skills/alpha`, `Makefile`,
  `outside/notes.txt`, `tools/build/out.py`, `docs/_build/page.html`,
  `tests/__pycache__/fixture.cpython-312.pyc`, `ontokin/.env`, `tools/node_modules/package/index.js`
  and `TRDs/.env.local`;
- exact lines: ` D Docs/variant.md`, when the record holds no `docs/variant.md` up to case;
- generated examples: ` M examples/visual/demo-data.js`, `M  examples/visual/demo-data.js` and
  ` D examples/agent/workflow.json`, even without a record, and the untracked name
  `examples/visual/fresh.glb`.

**Refused with `CH-SOURCE`, `Dirty source: <line>`:**

| Case | Lines |
| --- | --- |
| other forms for an uncopied path (exact) | `XY .claude/.gitignore` for `XY` in `D `, ` M`, `M `, `MM`, ` T`, `T `, `A `, ` A`, `AD`, `AM`, `MD`, `DD`, `AU`, `UD`, `UA`, `DU`, `AA`, `UU` |
| other forms for an uncopied path (real Git) | ` M .claude/.gitignore`; ` T .claude/skills/alpha`; `D  .claude/.gitignore` |
| inside the copied set (exact) | ` D P` for P in `README.md`, `pyproject.toml`, `.gitignore`, `tests/test_fixture.py`, `tools/fixture.py`, `.agents/skills/alpha/SKILL.md`, `TRDs/INDEX.md`, `docs/notes.md`, `tests` |
| inside the copied set (real Git) | ` D docs/notes.md`; ` M docs/notes.md` (a change, and a same-size change with the old modification time); ` T docs/notes.md`; `D  docs/notes.md`; `R  docs/notes.md -> docs/renamed.md` |
| a link inside the copied set (real Git) | ` D tools/linked.py` |
| renames and copies (exact) | `R  .claude/a -> .claude/b`, `C  .claude/a -> .claude/b`, ` R .claude/a -> .claude/b`, `RD .claude/a -> .claude/b`, `R  docs/a.md -> .claude/b`, ` D .claude/a -> b`, `R  examples/visual/a.glb -> examples/visual/b.glb` |
| quoted (exact) | ` D ".claude/two words"`, ` D ".claude/na\303\257ve.txt"`, ` D ".claude/quote\"mark"` |
| quoted (real Git) | the line Git prints for a tracked `.claude/quote"mark.txt`, and for `.claude/na\u00efve.txt`, a non-ASCII letter |
| unsafe names (exact) | ` D ../escape`, ` D ./outside`, ` D outside//notes`, ` D /outside/notes`, ` D outside/`, ` D ` |
| case variants of recorded copied files (exact) | ` D Docs/variant.md`, ` D DOCS/VARIANT.MD`, ` D readme.md`, ` D Tests/test_copied.py`, when the record holds `docs/variant.md`, `README.md` and `tests/test_copied.py` |
| no record (`copied=None`) | ` D .claude/.gitignore` |
| the original route (exact) | ` D .claude/.gitignore`, ` D .claude/skills/alpha`, ` M examples/visual/demo-data.js`, with or without a record |
| the original route (real Git) | the derived workspace above, which refuses at ` D .claude/.gitignore` |

**Other refusals:**
- `CH-SOURCE`, `Untracked source input: <name>`: with real Git, `.claude/new_input.py`,
  `outside/new_input.py` and `tools/new_input.py`. With exact names, also `Makefile`, and
  `examples/visual/fresh.glb` on the original route.
- `CH-WORKSPACE`, `The copied-source inventory record is malformed`, with no Git start: the records
  `[]`, `{"files": "README.md"}`, `{"files": [{"path": 1}]}`, `{"files": [["README.md"]]}` and
  `{"sha256": "x"}`.
- **The driver's refusals** (`ValueError`):
  - `Cannot copy a source symbolic link: <path>` from `prepare_workspace`, for a link inside the copied
    set;
  - `Source file is a symbolic link: <path>` from `inventory`;
  - `Cannot record the isolated workspace's index stat data: <error>` from a failed refresh, which
    fails `run` before any step.

## 5. The new test IDs (default discovery, `-s tests`)

`tests/test_local_checks.py`, class `CopiedSetAndWorkspaceIndexTests`:
- `test_local_checks.CopiedSetAndWorkspaceIndexTests.test_copied_source_path_is_the_scope_of_the_copy_and_of_the_inventory`
- `test_local_checks.CopiedSetAndWorkspaceIndexTests.test_failed_index_refresh_fails_the_run_before_any_step`
- `test_local_checks.CopiedSetAndWorkspaceIndexTests.test_ordinary_run_records_the_uncopied_tracked_paths_with_unchanged_fields`
- `test_local_checks.CopiedSetAndWorkspaceIndexTests.test_refreshed_index_still_reports_every_change_of_a_copied_file`
- `test_local_checks.CopiedSetAndWorkspaceIndexTests.test_untracked_source_record_lists_exactly_the_copied_set_names`
- `test_local_checks.CopiedSetAndWorkspaceIndexTests.test_workspace_index_records_stat_data_once_and_status_reports_the_same_lines`

`tests/test_current_host_readback_provider_v02.py`:
- `test_current_host_readback_provider_v02.DerivedSelectionTests.test_the_parent_proof_returns_the_drivers_recorded_copied_inventory`
- `test_current_host_readback_provider_v02.DerivedSelectionTests.test_the_selection_gives_the_source_check_the_parent_proofs_record`
- `test_current_host_readback_provider_v02.DerivedStatusLineTests.test_a_case_variant_of_a_recorded_copied_file_is_refused`
- `test_current_host_readback_provider_v02.DerivedStatusLineTests.test_a_derived_check_without_its_copied_record_admits_no_deletion`
- `test_current_host_readback_provider_v02.DerivedStatusLineTests.test_generated_examples_and_untracked_names_keep_their_rules`
- `test_current_host_readback_provider_v02.DerivedStatusLineTests.test_only_the_unstaged_deletion_of_an_uncopied_tracked_path_is_admitted`
- `test_current_host_readback_provider_v02.DerivedStatusLineTests.test_renames_copies_quoted_and_unsafe_names_are_refused`
- `test_current_host_readback_provider_v02.DerivedStatusLineTests.test_the_copied_set_decides_by_the_drivers_own_definition`
- `test_current_host_readback_provider_v02.DerivedStatusLineTests.test_the_original_route_still_refuses_every_line`
- `test_current_host_readback_provider_v02.DerivedWorkspaceTests.test_a_link_inside_the_copied_set_is_refused_by_the_copy_and_by_the_derived_check`
- `test_current_host_readback_provider_v02.DerivedWorkspaceTests.test_an_uncopied_path_whose_name_git_quotes_is_refused`
- `test_current_host_readback_provider_v02.DerivedWorkspaceTests.test_every_change_inside_the_copied_set_is_refused_in_the_derived_workspace`
- `test_current_host_readback_provider_v02.DerivedWorkspaceTests.test_every_other_change_to_an_uncopied_tracked_path_is_refused`
- `test_current_host_readback_provider_v02.DerivedWorkspaceTests.test_generated_examples_keep_their_exclusion_beside_the_uncopied_paths`
- `test_current_host_readback_provider_v02.DerivedWorkspaceTests.test_uncopied_tracked_paths_and_a_link_are_accepted_in_the_derived_workspace`

These 21 IDs add to the default inventory, and the next MR attempt's MC28 must approve them.

## 6. What the tests start

- **`CopiedSetAndWorkspaceIndexTests`:** real Git through the `PATH` Git resolved once: the fixture
  commits, the driver's workspace Git, storage and refresh, and `diff-files` and `ls-files` reads. The
  failed-refresh test plans one Python step, which never starts. The two tests that call `run` read
  `platform.platform()` as every run does; on its first call in a process it starts `uname` and
  `file` (MI's decision D-19).
- **`DerivedWorkspaceTests`:** real Git through the bound wrapper.
- **`DerivedStatusLineTests`:** the `/bin/sh` stand-in, up to five starts per check.
- **`DerivedSelectionTests`:** nothing.

None starts Node, `ldd`, `codesign` or `otool`.

## 7. Checks and evidence

The evidence is in `<local>/c271-p37/workers/W1-correction/`:
- `runs/RUNS.jsonl` and the logs in `runs/`: each run's command, times, result, log and log digest.
  The logs of the mutation runs hold machine paths in their tracebacks, so a portable record cites
  only their digests;
- `STARTS.md`: every start and two recorded deviations;
- `CHANGES.diff` and `COMPARISON.json`: the diff against the base bytes, and the member comparison;
- `MUTATIONS.json`: ten mutations on the final bytes, each detected and restored. Two earlier rounds
  had the same outcome and are kept: `MUTATIONS-draft-before-docstring-edit.json` preceded one edit of
  a docstring in `tools/check_local.py`, and `MUTATIONS-round2-before-escape-edit.json` preceded the
  provider test module's writing one non-ASCII letter as its escape sequence;
- `index-scope-declaration-commit.json` and `parent-proof-timing.json`.

The `last-` runs below are on the final bytes of section 1. The earlier `final-` and `closing-` runs
preceded those two edits and passed in the same way.

| Run | Result |
| --- | --- |
| `base-`: the four modules alone, before any change | 33, 49, 22 and 151 tests, OK |
| `last-local-checks`: `tests.test_local_checks` | 39 tests, OK |
| `last-provider-v02`: `tests.test_current_host_readback_provider_v02` | 64 tests, OK |
| `last-driver-v02`: `tests.test_current_host_readback_driver_v02` | 22 tests, OK |
| `last-controls-v02`: `tests.test_current_host_readback_controls_v02`, MI's frozen controls, unchanged | 151 tests, OK |
| `last-combined`: the four together | 276 tests, OK |

## 8. Open questions for S4 and S5

- **Q1.** Modules that W1 may not run, and that the Director runs at S5:
  - `tools/storage_tests/test_storage_identity.py` drives `check_local.run` on an LFS fixture. Without
    a `git-lfs` client it errors before the refresh, as at the base. With one, the refresh runs the
    configured clean filter.
  - `tests/test_current_host_readback_driver.py` mocks the workspace preparation.
- **Q2.** The case-folded comparison covers regular files, the only entries that the record lists.
  Controls may add a case variant at the real file system's level, but on a case-sensitive volume that
  case differs, and a control must not skip.
- **Q3.** The decision measures the per-read margin after the refresh on one host only. The next MR
  freeze states that time with its basis (FZ-02 as carried).
