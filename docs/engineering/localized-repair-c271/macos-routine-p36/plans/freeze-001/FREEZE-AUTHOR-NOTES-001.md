# Operational freeze 001 of gate MR: the author's notes

C271-P36, gate MR, stage S6, for S7 (R1 and R2). Director `c271-p36-14f7f8b219db`. Author: W2 (freeze 001), a
subagent in a fresh context with the session's model. I wrote none of the implementation, the contract, MP's
preparation, MH's records, MR's tooling, the observation plan or HOST. Times are UTC.

Labels: `<worktree>` the C271 worktree at B; `<local>` the data root beside the clone; `<E>` =
`<local>/c271-p36/evidence`; `<F>` = `<local>/c271-p36/workers/W2-freeze-001` (this directory); `<A1>` =
`<E>/mr-001-r1`; `<home>` the owner's home; `<prefix>` the package manager's prefix; `<framework>` the framework
interpreter's version directory under `<prefix>`; `<tmp>` the per-user temporary directory. The JSON documents keep
their real paths and this host's account values; see section 12.

## 1. Identity and status

| Item | Value |
| --- | --- |
| Freeze | `<F>/FREEZE-001.json`, 641,427 bytes, SHA-256 `11555730a5d153d4155bd730f288d8478fff2933a4587c4fef0a35940592ab66` as I computed it. The Director takes it from the freeze review record (placeholder `<FREEZE-001.json SHA-256>`). |
| Configuration | `<F>/config/readback-config-001.json`, 2,295 bytes, `0o644`, SHA-256 `e700edefb0a933f784d9fcf180770ef6d4675ae2cf8b7d6008ea0a126f5f916d` as I computed it, for the reviewer's comparison only. It is not in the freeze (A6): R1's argv carries `<readback-config-001.json SHA-256>`, and the Director takes the value from the freeze review record. |
| Status | `FROZEN_NOT_RUN`; attempt `mr-001`; no S7 path exists (P01's dry run below: 162 paths absent). |
| Candidate | B `4ca78142…`, tree `0935162c…`; boot `C90010BA-4DA9-475D-BBAB-CF1A9C40175A`. |

## 2. What the freeze holds

`FREEZE-001.json` uses the keys of MH's reviewed S7 checker (section 6), and adds the prose sections: `places`,
`evidence` (the parent's seven ancestors and the two devices), `wrapper`, `environments`, `configuration`,
`bindings` (83 files, each with SHA-256, size, mode and the one-link rule where the provider needs it), `host_facts`
(3), `trees` (5), `absent_paths`, `deferred_inputs` (the configuration, by requirements, not by digest),
`preparation` (`<A1>`, empty, `0o755`), `order` (31 commands), `commands` (36, with the 5 overrun commands),
`deferred_arguments`, `launch`, `overrun`, `stop_rules`, `failure_capture`, `starts`, `expected_outcomes`,
`attributions`, `decisions`, `carried_findings`, `fixed_state`, `limits` and `open_questions`.

The files it binds and that live here: `config/` (the configuration, `methods-001.json` `e8489f04…`,
`discovery-001.json` `46f375df…`), `discovery/` (MH's collector's discovery of B `c9e8fbec…` and its comparison
`28a67372…`), `attributions/` (R1 `9425ab4e…`, 92 rows; R2 `e3938c31…`, 310 rows), `env/` (R1 `1790146f…`, R2
`38ed5cb3…`, tools `34befb91…`, PATH only `12254e77…`; and the discovery environment `e3d0bc67…`).

## 3. The configuration (config/0.2.0), value by value

| Key | Value | Source |
| --- | --- | --- |
| `schema`, `contract` | `ontokin.current-host-readback-config/0.2.0`, `ontokin.current-host-readback/0.2.0` | the provider's constants |
| `source` | root `<worktree>`, commit B, tree `0935162c…`, inventory = HOST's `/source/inventory` descriptor exactly, path included (`95abd300…`, 96,238 bytes, `0o644`) | HOST; HR-02 |
| `host` | `<E>/observe-001/HOST.json`, `858ef72a…`, 18,420 bytes, `0o600` | the HOST review record's `/host/sha256` |
| `dependencies` | root `<local>/c271-macos/reader-c195`, inventory = HOST's descriptor (`3545d5f9…`) | HOST; HR-02 |
| `runtime` | the pinned `bin/node`, `v24.22.1` | HOST |
| `methods` | `methods-001.json`: the readback test file and the nine original bodies (read from the provider's AST), binding `discovery-001.json`: the 5,994 IDs of B, sorted, unique, and the baseline map | MH's collector at B (section 7) |
| `contract_source` | `CONTRACT.md` of the worktree, `42db98dc…` | the file |
| `amendment_adoption` | `ADOPTION-AMENDMENT-001.json`, `872312ed…`, 5,396 bytes, `0o644` | PR-06; equal to PLAN-REVIEW-001's binding |
| `evidence_root` | `<A1>`, which D01 creates; R1's driver output is `<A1>/driver` | F-2 |
| `parent` | `null` | an original selection |

The provider's own read-only checks accept it (section 7, `records/config-validation-001.json`).

## 4. Environments, PATH and temporary directories (D-P1, D-P2, D-P3, D-P6)

- **PATH `/usr/bin:/bin`, no directory of links.** By reading, no test differs from main's baseline only because
  `python3.12` or Git's `lfs` helper is missing (the freeze's `decisions` D-P1 cites the lines): U-28 asserts an exit of
  1 and a state in {missing, unsupported}, and the core checks do not depend on node, the LFS client or a base
  interpreter on PATH; U-30 passes the base interpreter by absolute path and then reuses the environment; the LFS
  client matters only for LFS-selected files, which the fixture has none of; and Git by name is `/usr/bin/git` on the
  owner's PATH as well. Under this PATH no `node` exists, so the doctor's tests start none.
- **The declared environment.** `/usr/bin/env -i` with exactly `HOME`, `LOGNAME`, `PATH`, `TMPDIR` and `USER`, this
  host's values. My AST scan (`records/env-reads.json`) finds these reads by name: the test-only `ONTOKIN_*` retain
  roots, the selection pair, `STATIC_TRAY_READBACK_CPU_OUTPUT`, `PATH`, and the doctor's `PLAYWRIGHT_BROWSERS_PATH`
  and `XDG_CACHE_HOME`; the standard library adds `HOME` and `TMPDIR`. The Director's session, the same kind of
  session that ran main's baseline, sets no `LANG`, `LC_*`, `TZ`, `XDG_*` or `PLAYWRIGHT_*` variable, so none is
  declared. `STATIC_TRAY_READBACK_CPU_OUTPUT` is left out on purpose (F-1). Limit: main recorded only the absence of
  `PYTHON*`, `PIP_*` and `GIT_*`.
- **TMPDIR.** R1: `<tmp>` in its resolved `/private/var/...` form with the final slash, as main's resolved run; R2:
  macOS's default `/var/...` form.
- **Host facts, by digest only.** `<home>/.gitconfig` (237 bytes), `<home>/.config/git/ignore` (31 bytes, Git's default
  excludes file, an addition to D-P3's wording), `<home>/.CFUserTextEncoding` (`bd605d2e…`, 7 bytes, `0o400`; HR-03).
  `<home>/.config/git/config` and `attributes` are absent and checked absent.
- **Devices.** The evidence on 16777244, the temporary directory on 16777234 (I-05).

## 5. R1 and R2

| | R1 (qualifying) | R2 (ordinary) |
| --- | --- | --- |
| cwd | `<worktree>` | `<worktree>` |
| argv | `env -i` the five, `<worktree>/.venv/bin/python -B tools/check_local.py --timeout 7200 --output-dir <A1>/driver --readback-config <F>/config/readback-config-001.json --readback-config-sha256 <digest>` | the same without the two selection arguments, `--output-dir <E>/mr-001-r2` |
| launch | the Director's wrapper `run_once_p36.sh` (`9154f181…`), background, MH's timer beside it | the same |
| bounds | steps 7,200 s each; outer 10,800 s | the same |

**T and the bound (F-3).** Main's unit stage took 957 to 1,149 s, and the two 8e847c15 runs ran at the same time. The
branch's 1,005 added tests took about 34 s in MI's per-module runs, so about 1,000 to 1,500 s is expected. 7,200 s
leaves a margin of about five; a hung step is stopped by the driver within the outer bound. No bound rests on the warm
Node timing (HR-06).

## 6. The checker and the order of S7

The checker is MH's `w2f_s7_check.py`, unchanged, from its committed path at B (`eb96aa1a…`, 16,612 bytes; byte-equal to
MH's reviewed original beside the clone). `expect` evaluates a run's stop predicates, `--audit` its outcome predicates.

| Step | What |
| --- | --- |
| P00 | `shasum -a 256 --strict -c SHA256SUMS.txt` in `<F>` (MH's FR-07); before it, the Director compares the freeze's, the sums' and the wrapper's digests with the review record (FR2-05) |
| P01 | checker `pre`: 83 bindings, 3 host facts, 5 trees, ancestors, boot, umask, the configuration's requirements, 162 paths absent |
| D01 | `mkdir -m 0755 <A1>` |
| P02, P03 | the observer's python-inventory and source-inventory, each required byte-equal to HOST's (`c277bdd3…`, `95abd300…`); HR-04's precondition |
| D02 | checker `prepared`: all of P01 again, `<A1>` empty, 143 paths absent, and the predicates of P00 to P03 |
| R1 | the qualifying run |
| R1.L | FC-K5: a listing of all of `<A1>` (driver output and cohort) |
| R1.I | python-inventory between the runs (D-P5) |
| R1.F | the cohort root by the frozen rule: exactly one `current-host-cpu-<8>-preserved-<32 hex>` in `<A1>`, nothing else of that prefix |
| R1.P | FC-P3 probes of the three Node starts' pairs; each target must be absent |
| R1.C | the collector: the seven methods passed once each, the six fixture IDs of the module missing (MC23), the log against the discovery list (MC28) |
| R1.K | the comparator against main's resolved-directory run, with R1's attributions |
| R1.A, R1.R | MH's numerical audit on the cohort; the readback evidence reader joined with it |
| R1.M | FC-K5 listing of the six checker outputs (binds the reader's `cohort_bindings` for the audit; TR-09) |
| R1.X, R1.Y, R1.Z | stop predicates (251), outcome predicates (129), the state between the runs (checker `post`: bindings, host facts, trees with bytecode, D-P4) |
| R2 and R2.L, .I, .C, .K, .V, .M, .X, .Y | the same for R2, with MC22's expectations; R2.K against main's default-directory run; R2.V compares R1 with R2 |
| Q01, Q01.X, Q04 | the source inventory after S7, its predicates, the final checker `post` |

A command's allowed exit statuses and classification decide each step; the sequence after a run continues where its
inputs exist (`stop_rules` 3a). Outcome predicates (R1.Y, R2.Y) record findings and never stop S7.

## 7. What I established, and how

- **Discovery at B (MC28's first half).** MH's collector, `discover` from `env -i` with MH's discovery environment
  (TMPDIR in `<F>/tmp-discovery-001`, which stayed empty), `-B`, root `<worktree>`: COMPLETE, 5,994 unique IDs, 388
  modules, no failed import, loader error, bytecode or process event; equal to MH's discovery of C. Its `compare` with
  MH's baseline (5,587 at `1c2f25ba`, `8d53b1c9…`) and `INVENTORY-ADDITIONS.json` (`f710dbb5…`): `exact_match` true,
  missing 0, extra 0. No file in the worktree was newer than my marker afterwards.
- **Inventories now.** The observer's python-inventory and source-inventory: byte-identical to HOST's at 20:55Z.
- **The configuration.** `scripts/w2f_validate.py`, run as `<worktree>/.venv/bin/python -I -S -B` from `env -i`, loaded
  the provider of B and ran every read-only part of `_selection`: digest, closed schema, contract and adoption
  bindings, evidence-root form, HOST's Git by bytes, `_verify_host` in full (state, environment, the Python inventory
  recomputed, runtime with receipts, Git, inspections, labels, starts, claims), the source inventory with all 644
  bindings, `_cross_bindings`, `_verify_dependencies` and `_verify_methods`. `_verify_source` was stopped at its first
  Git read by a sentinel, after every file binding passed. An audit hook refused every process creation and write;
  none occurred. Not run: the Git reads, the workspace derivation, the cohort.
- **The driver's inventory of B.** `tools/check_local.py`'s own `inventory()` on the worktree: `sha256:e7f1c4b5…`,
  23,005 files, which both summaries must record. Against main 8e847c15's: 11 files changed (`STATUS.md`, 5 under
  `docs/`, `tests/test_local_checks.py`, `tests/test_static_tray_readback_v01.py`, `tools/check_local.py`,
  `tools/storage_identity.py`, `tools/storage_tests/test_storage_identity.py`), 4,329 added (4,303 under `docs/`, 17
  under `tests/`, 7 under `prototypes/`, 1 under `tools/`, 1 under `TRDs/`), none removed; nothing under `ontokin/`,
  `examples/`, `fixtures/` or `schemas/`. The conformance stages' code is unchanged, so their report summaries are
  expected equal to main's.
- **The step argvs.** The driver's `--list` for both output paths (it wrote nothing).
- **The attributions.** `scripts/w2f_attributions.py` loads the reviewed collector from its file and builds every
  statement with its own `collect_log`, `Normalizer` and `record_statement`. Self-tests with the comparator on main's
  own runs: all 307 rows of the default run and the one row of the resolved run match; every MI-derived row equals the
  collector's statement of MI's collected record. TR2-04 is checked for each row.
- **The freeze.** `scripts/w2f_selfcheck.py`: 423 checks, none failed (shell members split back to the wrapper argv,
  MH's timer template, deferred placeholders, environment lists, predicate forms, files, bindings now, absent paths);
  every collector and comparator pointer resolves on outputs of the same tools for main's runs. The checker itself,
  on this freeze: `pre` MET and `post` MET; `expect` NOT_MET for every predicate, as nothing of S7 exists.
- **The shell texts.** `sh -n` and `zsh -n` pass for the timer, R1's shell member and both cohort scripts; the two
  cohort scripts give the intended result on eleven synthetic roots in `records/shell-tests/world/`.

## 8. Expected outcomes and attributions

**The finding that changes the brief's expectation.** MI's `CHECKS.json` at B binds MI's final per-module runs on this
host (final-003, commit `7b759de0`), and records five of the branch's own modules failing there, each identical to the
phase-start baseline: the 0.1.0 driver (D-18's 2), the 0.1.0 provider (3), the inspection module (47 test IDs), the
required-images module (2) and the rtld-paths module (39). They are Linux-route tests. So "the freeze expects each of
the branch's own tests to pass" does not hold for these 93. Applying the brief's own rule, outcomes that a record
establishes, I attribute 91 of them in R1, raw, from MI's retained logs, each with its source. The two required-images
tests `test_RI_L07` and `test_RI_L08` recorded `ModuleNotFoundError`, an artifact of MI's per-module invocation (it
leaves `tests/` off `sys.path`); in the routine they import their sibling modules and run those suites in process, so
no record establishes their outcome, and they are not attributed. By reading, `test_RI_L08` runs the rtld-paths suite
and requires it to pass, so it will probably not pass: a finding. Q-1 to Q-3 ask the review.

| | R1 | R2 |
| --- | --- | --- |
| Ran | 5,994, each once, in discovery order | 5,991 (the three CPU methods neither run nor reported) |
| Skips, expected failures, unexpected successes | 0 (footer, collector, driver: TR2-01) | 0 |
| Readback | 7 passed; no fixture record; 3 Node starts with receipts; the matrix_0_3 negative; every row | setUpClass error with the fixed reason (MC22); 4 seams passed |
| Attributed not passing | 92: main's last-digit fixture test, D-18's two, MI's 89 | 310: main's 307 (normalized), D-18's two, MC22's record |
| Against main | unchanged 4,985 passed, 1 failure; different_outcome exactly the trio (skipped to passed, S8); added 1,005, of which 91 not passing, all attributed; removed 0 | main's 307 unchanged; removed exactly the trio; added 1,006; every step's status equal |
| Not established | the other ~5,900 tests: expected to pass; any that does not is a finding | the branch's tests under the `/var` link: `stop_rules.r2_classification` (main's class, attributed, unchanged from R1, the `/var`-alias class, or a finding) |

S8's change is recorded, not classified (R04). D-18's two are attributed in R2 too: their first lines name no
temporary path. MI's 89 are not attributed in R2 (their record is under a resolved directory); R2.V compares them with
R1's own records.

## 9. Starts

Bounded in S7: Node 3 (R1's trio through the provider), other 0; for MR with S5: Node 4, other 1, as MR-PLAN section 8
expects. Recorded, not counted (D-P7): about 4 `uname` and 4 `file` per run; driver Git reads 49 (R1, the bound Git)
and 29 (R2, `/usr/bin/git`); provider Git reads about 60 (R1); the tests' Git starts by name, not enumerated; the
interpreter starts of the driver, its steps and the tests' children; each tool command's one start; `mkdir`, two
`/bin/sh` scripts, `shasum`; the wrapper's and the timers' utilities. Never: `ldd`, `codesign`, `otool`, another Node,
Git's `--version`, `observe`.

## 10. Stop rules, overrun, failure capture

The freeze's `launch`, `overrun`, `stop_rules` and `failure_capture` hold them. In short: MH's launch (FR-01, FR2-03,
FR2-05); MH's six overrun steps, where only R1 has recorded pairs (R1.N finds the cohort root, temporary or preserved;
R1.O probes; R1.S<k> stops only an established identity; nothing is ever sent to the wrapper, the driver or its steps);
FAILURE-CAPTURE unchanged, read as PR-01's disposition says (`<E>` for MH's evidence parent, MR-PLAN section 9 for
MH-PLAN section 8, the schema kept, `capture_probe.py` only from its committed path), with two FC-K4 kinds added for the
driver and the provider in a driver run, and FC-R5's S4 read as MR's.

## 11. Carried findings and decisions

PR-01, PR-06, HR-01 to HR-08, TR-09, TR2-01, TR2-03, TR2-04, TR-10, D-18, O-01, I-05, AU-07 and D-19: `carried_findings`
says where and how each is applied. D-P1 to D-P7 and F-1 to F-5: `decisions`, each with its basis. F-1: the provider's
default cohort route (no `STATIC_TRAY_READBACK_CPU_OUTPUT`, which tests read and main's baseline did not have). F-2: the
evidence root is `<A1>`. F-3: T and the bounds. F-4: MH's checker reused. F-5: no discovery rerun in S7.

## 12. Privacy

This file uses labels only. Exact files, which stay beside the clone:
- **The account's name and home** occur in `FREEZE-001.json` (`places`, R1's and R2's argv and shell members, the host
  facts' paths), `env/r1.environment.json`, `env/r2.environment.json`, the checker's dry-run records
  `records/author-check-*.json`, and `records/shell-tests/shell-r1.zsh`. R1 and R2 need them (D-P2).
- **Machine paths** (the volume, the package manager's prefix, the per-user temporary directory) occur in the JSON
  documents, in `scripts/w2f_build.py`, and, truncated by unittest, in five reasons of R2's attribution file, which must
  stay exact for the comparator. `discovery/discovery-b-001.json` also holds the admitted CoreFoundation value that
  MH's collector records.

A portable copy (S10) replaces each by its label. No application name occurs in any file of this directory apart from
the system's own programs.

## 13. Open questions for the review

Q-1 to Q-12 in the freeze's `open_questions`. The most important: Q-1 (attributing MI's 89), Q-2 (not attributing them in
R2), Q-3 (RI_L07 and RI_L08), Q-4 (MH's checker as a fourth reused piece), Q-5 (T and the bound), Q-11 (the exact count
of 91).

## 14. Every process I started

- **Shells.** One zsh per tool call (about 110), with read-only utilities: `ls`, `cat`, `sed`, `grep`, `head`, `tail`,
  `wc`, `cut`, `tr`, `sort`, `uniq`, `jq`, `shasum`, `stat`, `find`, `cmp`, `du`, `id`, `getconf`, `readlink`,
  `sysctl -n kern.bootsessionuuid` (once), `date`, `env`. Writes in `<F>` only: `mkdir`, `touch`, `sleep 1` (once),
  `sed -i` on my own scripts, `ln -s` (once, a test symlink, removed), `rm` of my own files only.
- **The framework interpreter, `-I -S -B`.** About 35 starts of `python3` from my PATH (it resolves to
  `<framework>/bin/python3.12`): my scripts and short readers. Ten starts by its absolute path from `env -i`: the MR
  collector on MI's six retained logs and on main's two logs with R1's and R2's arguments, and the comparator twice on
  main's own runs.
- **`<worktree>/.venv/bin/python`.** MH's `discover` (`-B`, one) and `compare` (one); the observer's python-inventory and
  source-inventory (one each); `w2f_validate.py` (three); `w2f_driver_inventory.py` (one); `tools/check_local.py --list`
  (`-B`, two); MH's checker (twenty-two dry runs).
- **Shell tests.** `/bin/sh -n` (3), `zsh -n` (2), and 30 `/bin/sh -c` runs of the two cohort scripts on synthetic roots.
- **Never started:** Git of any kind, Node, `ldd`, `codesign`, `otool`, the observer's `observe` or `static`, the routine,
  a unit test, a download or install, Finder, a child agent.

**Deviations, all without effect on bound trees.** (1) Six starts of `/usr/bin/python3`, the operating system's
launcher of the developer tools' Python, because `python3` under `PATH=/usr/bin:/bin` resolves there; each started the
collector, which failed in its own invocation record before writing anything; I then used the framework interpreter by
its absolute path. (2) `w2f_validate.py` failed twice on my own errors (an uncaught sentinel; an audit hook that
mishandled `os.fdopen`, which left an empty output that I removed). (3) The builder ran six times: the first failed on an assertion (the
dispatcher's link count) after writing the four environment files, which I removed; each later run, after a correction,
first removed my own environment files and the previous freeze; the environment files' bytes are the same each time. (4) Four checker dry runs got a malformed argument from my harness and were refused by argparse. (5) One
`rm -rf` in a test harness was refused by the tool's safety check and never ran. (6) One file list of this directory's
relative names was written by mistake to the system's `/tmp` (outside my writable place) and removed at once; it held
nothing else. Afterwards: no file in the worktree
newer than my first marker, no `__pycache__`, `.pyc` or `.DS_Store` there, 414 `.pyc` in `<framework>`, and `<E>` still
holds exactly its nine entries.
