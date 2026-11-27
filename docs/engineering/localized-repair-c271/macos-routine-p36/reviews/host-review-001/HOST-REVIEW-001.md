# HOST review 001: HOST of attempt observe-001 (M0 and M1 of gate MR)

| | |
| --- | --- |
| Reviewer | W3, the independent HOST reviewer of C271-P36: a Claude Code subagent in a fresh context, with no earlier review in it. W3 wrote none of HOST, the observer, the supervisor, the observation plan, its launch record or review, the contract, the amendment, MP's preparation, MH's records, MR's tooling or the Director's wrapper. |
| Gate and stage | gate MR, phase `C271-P36-macos-complete-routine-mr`, end of stage S5 of MR-PLAN (acceptance A5), local mode; Director `c271-p36-14f7f8b219db` |
| Under review | `<local>/c271-p36/evidence/observe-001/HOST.json`, written by the observer's `observe` under observation plan 001, and the evidence of that run |
| Commit B | `4ca781429c5411c67c0965bc69306b42c6cc74ad`, tree `0935162c72fd9d804681e920da6f6d6e9066ff28` |
| Host | macOS 26.6.2 (25G83), Darwin 25.6.0, arm64, not translated, boot `C90010BA-4DA9-475D-BBAB-CF1A9C40175A` (booted 2026-11-23T12:20:29Z) |
| Written | 2026-11-27, after this review's checks of 20:11Z to 20:18Z |

Places are named by labels:

- `<worktree>` is the C271 worktree at commit B; `<clone>` is the main clone, whose `.git` is the common Git
  directory that `<worktree>/.git` names through `<clone>/.git/worktrees/c271`.
- `<local>` is the working directory beside the clone; `<parent>` is the directory that holds `<clone>`,
  `<local>` and the worktrees directory; `<volume>` is the external volume's mount point.
- `<prefix>` is the installation prefix of the interpreter's framework and of its non-system libraries;
  `<framework>` is `<prefix>/Cellar/python@3.12/3.12.13/Frameworks/Python.framework/Versions/3.12`.
- `<home>` is the owner's home directory; `<attempt>` is `<local>/c271-p36/evidence/observe-001`.
- `OUT` is `<local>/c271-p36/workers/W3-host-001/`, the only place I wrote.

The machine-readable form is [HOST-REVIEW-001.json](HOST-REVIEW-001.json).

## Verdict

**ACCEPT_WITH_NONMANDATORY_FINDINGS.** There is no mandatory finding. The operational freeze may bind
this HOST as observed.

**HOST's SHA-256, computed from the file's bytes:**
`858ef72a949ce7575787290601ae70d117090a460781b2e660a3b0d4f0162666`. The file is 18,420 bytes, mode `0o600`,
one link, canonical JSON without a duplicate member. It equals the host descriptor in `result.json`, in
`completion.json` and in observe's stdout, and it was unchanged at the end of the review (20:18Z).

- **HOST is exactly W3-OBSERVER section 3's document.** All 32 of its objects are closed with exactly their
  listed members, and the top level, platform, python, runtime and label key lists are the provider's too.
- **Every value I could recompute agrees** (h01: 71 of 71 checks). That covers the descriptors, the
  platform, the boot, native execution, the OS identity and cryptex hop, the environment record, the
  runtime with `bin/node`'s Mach-O header and all 21 load commands, `NODE-SOURCE.json`, both install
  receipts, the reader tree, Git, the inspections, the labels and the claims.
- **The three inventories, recomputed by my own code, are byte-identical to the frozen files** that the
  plan and HOST bind:
  - Python installation: `c277bdd3ac6aa73105df3924707a271a402a0dc7c722be27a6834f2c78605633`, 776,209
    bytes, at 20:11:06Z and again at 20:16:19Z;
  - source: `95abd300edbb9930e67c569b726015964ab98f4ed0ede389da122bbb3f145c4c`, 644 files, at 20:11:47Z
    and 20:16:19Z;
  - reader tree: `3545d5f920ac840804a9e25d28a87d623f96af71537fd3f020a0c1d743f82fb4`, 24 files and 13
    directories.
- **The starts are exact: one Git and one Node start, and no other process of the observer's.**
  - Git `--version`: PID 30441, 7.919 ms. Node `--version`: PID 30442, 41.926 ms. The PIDs are consecutive.
  - Both have full cleanup proof, and both are absent now (`ESRCH`). Both predicates hold, and both stderr
    logs are empty. The counts are `{node: 1, other: 1}`, and the static run made none.
- **N-07 holds.** The recorded line is exactly `git version ` + the one version text embedded in the
  bound file's arm64 slice. **N-06** is unchanged: 81 `LC_RPATH` entries, none used at load time.
- **The attempt is complete.** It holds the 3 planned directories (`0o700`) and M0-LAUNCH's 19 files, none of
  the 3 failure files, and nothing else. The eight capture files and both command records agree with it.
- **Against MH's HOST, 16 leaves differ, and all are expected.** They are the source commit and tree, the
  ref file that holds the commit, the observation time, the plan, the two inspection receipts, and the
  paths of MR's copies of the three inventories. Every host fact, inventory digest, the runtime, the reader
  tree, Git, the CoreFoundation value, the labels and the claims are equal.
- **Nothing found should stop a configuration from binding this HOST.** HR-02 states what the configuration
  must reproduce for the provider to accept it.
- **Eight nonmandatory findings, HR-01 to HR-08.** The most important are:
  - **HR-02:** the configuration must carry HOST's inventory descriptors exactly, and HOST makes W2's
    three inventories and the attempt's two receipts bound inputs of every R1 start;
  - **HR-04:** the other agent application of PR-02 started the bound interpreter again during this
    review, and PR-03's job still runs it without `-B`; the inventory was still unchanged afterwards.

## 1. Method

### 1.1 Reads

I read these with the agent's file-read tool, which starts no host process:
- **Governing instructions:** AGENTS.md, ROLE.md, PROTOCOL.md (all of it, sections 4 and 5 above all) and
  the worker template.
- **The gate:** MR-PLAN.md (all of it, sections 2, 6, 8, 9 and 12 above all) and PHASE.json (A5).
- **The contract:** CONTRACT.md (all of it, sections 4, 5 and 7 above all) and AMENDMENT-001.md.
- **The observer's interface:** W3-OBSERVER.md, all of it.
- **The code:** all of `current_host_observation_v02.py` and `supervisor_darwin_v01.py`; `json_bytes`,
  `_reap` and `LIMITS` of `supervisor.py`; the HOST consumer of `current_host_readback_v02.py`, lines 90 to 105
  and 487 to 713.
- **The plan and its review:** the plan, M0-LAUNCH.json, M0-ENVIRONMENT.json, PLAN-REVIEW-001.json, the
  disposition PLAN-REVIEW-DISPOSITION-001.json and the worker log WORKERS.md.
- **The precedent:** MH's HOST-REVIEW-001.md (all of it) and the start of its JSON form, its disposition,
  and N34-M-REVIEW.md sections 2.7 to 2.9, answers (a) to (d) and findings N-01 to N-09.
- **The evidence:** every file in the attempt and every capture file beside it; MP's two install receipts.

### 1.2 Scripts

My scripts are in `OUT/scripts/` and their outputs in `OUT/outputs/`.
- **Standard library only.** They import nothing of the project. The observer's constants are read by
  parsing its source with `ast`, never by importing it.
- **No process creation.** Each installs an audit hook that refuses every process-creation event and every
  ctypes lookup of a process-creation function, and admits `os.kill` and `os.killpg` only with signal 0.
  No script recorded a refused event. The ctypes lookups were `sysctlbyname` and `proc_pidpath` only.
- **No machine path.** Paths are arguments, and outputs carry the labels above.
- **Absent outputs only.** Each output is written to an absent path with `O_EXCL`.
- **Their own code.** The hashing, the link resolver, the thin and fat Mach-O parsers, the tree walks, the
  inventory closure, the RECORD check, the Git index and loose-object readers and the comparisons are mine.

| Script | What it does |
| --- | --- |
| `w3h_common.py` | Shared helpers: the audit hook, bounded reads through one descriptor, canonical JSON, the link resolver, the Mach-O parsers, the AST reader of the observer's constants, the labeller |
| `w3h_01_host.py` | 71 checks of HOST's bytes, closed shape, constants and every static binding, against the plan, the observer's source and the host now |
| `w3h_02_python.py` | The Python inventory rebuilt from W3-OBSERVER section 5 (both trees, the selection chain, the Mach-O closure), the packages and RECORD rows, N-06, and HOST's python facts |
| `w3h_03_source.py` | The source inventory, HEAD from the Git files, commit B's loose object, and the index (checksum, cached root tree, the blob of every source file) |
| `w3h_04_evidence.py` | The attempt's tree and records, both starts, the order of the records, the two PIDs now, the observer's start routes, the capture records, the evidence parent and the wrapper |
| `w3h_05_compare_mh.py` | This HOST against MH's, leaf by leaf, and the inspection receipts each binds |
| `w3h_06_declared.py` | A process launched as the observer was, apart from the launcher's name: its environment and interpreter facts against HOST's |
| `w3h_07_final.py` | The final recheck: HOST and the evidence files, the boot, the shared cache and dyld (N-03), my own PIDs, and the digest of every reviewed file |
| `w3h_08_seal.py` | The privacy scan of my records, the strict parse of the JSON record, and `SHA256SUMS.txt` |

**Superseded runs.** Two outputs are kept beside the later one:
- `h04-evidence-run1.json`: my check O04 counted `_run_start(context, command)` in the definition line as
  well as in the call, so it failed on a correct source.
- `h04-evidence-run2.json`: the same check then counted `Popen` in a comment of supervisor line 158.
- `h04-evidence-run3.json` scans code only. All 25 of its checks pass; its other 24 results equal run 1's.

## 2. Answers

### 2.1 HOST against the plan and the observer's rules, field by field (question 1)

**Schema and state.** `/schema` is `ontokin.current-host-readback-host/0.2.0`, with the contract,
`/design_revision` 4, `/amendments` `["P33-AMENDMENT-001"]`, `/profile` `darwin-arm64-v1` and `/executor`
`macos-arm64-local`. The state is `OBSERVED_UNAPPROVED`, in `/claims/status` and in `completion.json`. The
four `/claims` are the observer's fixed texts byte for byte, and `/starts` is `{node: 1, other: 1}`.

| Group (HOST pointer) | What I recomputed or compared | Result |
| --- | --- | --- |
| `/plan`, `/observer` | the plan's bytes (`cc1c2def…`, the review record's and the disposition's digest); the observer's bytes (`471a9547…`, 162,557 bytes, `0o644`, one link), the plan's descriptor, the source inventory's entry, its blob `e59d6292…` in the index | equal |
| `/platform` | `os.uname()` now: Darwin, 25.6.0, the kernel version string, arm64; `sysctl.proc_translated` 0 and `kern.bootsessionuuid` through `sysctlbyname`; the plan's release and boot | equal; `kern.osversion` 25G83 |
| `/os/system_version` | the file's bytes (`6151cb88…`, 603 bytes, `0o444`), no linked component, and its four plist fields: macOS, 26.6.2, 25G83, no `ProductVersionExtra` | equal to HOST and the plan |
| `/os/cryptex` | my resolver: one hop `/System/Cryptexes/OS → ../../System/Volumes/Preboot/Cryptexes/OS` to the canonical copy; its bytes (the same `6151cb88…`) and fields | equal; `/labels/os` derived from both |
| `/environment` | `declared` is exactly the five, equal to the plan and the observer's constant; M0-ENVIRONMENT.json (`0ed78f47…`) is their canonical form; the CoreFoundation value: see below | equal |
| `/python` | my inventory (byte-identical, `c277bdd3…`); `selection` (launcher chain 4 hops, home 1, home launcher 2, executable 0); the seven packages and every RECORD row; the lock (`b1e3e866…`, 799 bytes); `interpreter` against my own processes | equal; see below |
| `/runtime` | the directory: exactly `bin/`, `bin/node`, `NODE-SOURCE.json`, modes `0o755`; `bin/node` (`6f320694…`, 122,545,856 bytes, `0o755`, one link); my parse of its Mach-O; `NODE-SOURCE.json` (`e928a8ec…`, 976 bytes, canonical); the archive (`89c68259…`, the pin, 53,062,778 bytes, `0o444`); MP's plan and receipt under the receipt rule | equal; `INSTALLED_EXACT` |
| `/dependencies` | the reader tree walked now: 24 files and 13 directories, no link, `.DS_Store` or multi-link file, equal to C199's pins (`EXTERNAL-INPUTS.json` `21fd6bad…`); validator 2.0.0-dev.3.10 and Three.js 0.186.1; the C195 archive (`b1e54a6c…`, the pin); the rebuilt inventory document; MP's reader plan and receipt | equal; byte-identical document; `INSTALLED_EXACT` |
| `/git` | `/Library/Developer/CommandLineTools/usr/bin/git`: `be4afb2b…`, 7,604,272 bytes, `0o755`; canonical, not a link, not the dispatcher, its hard link or its bytes; the version line against the embedded text (N-07) | equal |
| `/source` | root, B, the tree, the source inventory's descriptor, the observer's `tree_check` text; HEAD from the Git files; B's object; the index | equal; see below |
| `/inspections`, `/observed_at_utc` | both receipts' descriptors at the planned paths; HOST observed at 19:49:16.722051Z, after the later receipt (19:49:15.957465Z) and inside observe's window (19:49:14.197371Z to 19:49:16.736380Z) | equal; in order |
| `/labels` | executor, contract, revision 4 and the amendment, profile, OS, Node (`not_performed` signature check), the inventory digest, Git `{path, sha256}`, `host-observation`, `real` | equal to their bindings |

**The runtime's Mach-O.** My parser gives thin `MH_MAGIC_64`, cputype `0x0100000c`, cpusubtype
`0x00000000`, `MH_EXECUTE`, flags `0x00a18085`, 21 commands in 2,416 bytes. `/runtime/macho` equals my parse
field for field in all 21 commands.
- **The rules.** Every command is in the 16-command list, with one `LC_LOAD_DYLINKER` (`/usr/lib/dyld`) and
  one `LC_MAIN`. The four dylibs are CoreFoundation, Security, `libc++.1` and `libSystem.B`, all under
  `/System/Library/` or `/usr/lib/`. There is no `@` path and no `LC_RPATH`.
- **The signature.** The code signature ends exactly at the end of the file.
- **D-16.** Command 14 is still a plain `LC_LOAD_DYLIB` of CoreFoundation.

**The receipts.** Each satisfies my statement of the receipt rule (D-05, D-11).
- **The plans.** Both have the closed `install/0.2.0` keys, this source root, the destination, mode, files,
  directories and archive, and the result's path.
- **The results.** Each is a passed `INSTALLED_EXACT` receipt with the closed keys of that state, revision 4
  and the amendment, zero starts and the adopted pins. Its labels carry the pins of its purpose and HOST's
  OS-label shape. `before` is absent, and `after` and `publication` are as required.
- **The archive summaries.** Each equals its plan. The member-inventory digest is `0b2b6072…` over 5,888
  members for Node, which `NODE-SOURCE.json` carries, and `72dc3175…` over 730 members for the reader tree.

**The Python binding.**
- **My inventory.** It is byte-identical to the frozen file, with N-08's figures:
  - **framework:** 3,478 files (414 bytecode), 305 directories, 5 links, 72,433,430 bytes;
  - **venv:** 297 files, 45 directories, 3 links, 13,983,870 bytes;
  - **images:** 111. The framework holds 2 `MH_EXECUTE`, 1 `MH_DYLIB` and 76 `MH_BUNDLE`, the venv 19 `MH_DYLIB`
    and 8 `MH_BUNDLE`, and 5 external `MH_DYLIB` lie under `<prefix>/Cellar`;
  - **closure:** 6 link hops, stable after 2 passes, with 5 images reached by a second spelling.
- **The packages.** The seven pins are installed at their versions. RECORD's hashed rows number 139 (Pillow),
  36, 45, 29, 20, 10 and 6, each package with its one unhashed RECORD row, and no file under site-packages is
  unowned. HOST's `packages` and `records` equal mine.
- **The interpreter facts.** Two of my processes check `/python/interpreter`:
  - **h01** checks the recorded values: CPython 3.12.13 with my interpreter's own build string, the venv's
    launcher as `executable`, the framework's `bin/python3.12` as `base_executable`, the framework as both
    prefixes, Python.app as the process image, the isolated three-entry `sys.path`, and the flags of
    `-I -S -B`.
  - **h06**, launched in exactly the declared environment (see the environment below), reproduces the
    implementation, version, build string, all 18 `sys.flags` (`utf8_mode` 0 under `LC_ALL=C.UTF-8`), both
    prefixes, `sys.path` and the process image. Only its launcher's name differs.

**The environment.** `/environment/cf_user_text_encoding` is a non-empty string (not quoted here).
- **Reproduced.** It equals the value of my own processes now, and of a process I launched in exactly the
  declared environment. That process sees exactly the declared five plus `__CF_USER_TEXT_ENCODING`, with
  this value, and no `__PYVENV_LAUNCHER__`.
- **Its parts.** It is `0x` + the UID in hex + `:` + the content of `<home>/.CFUserTextEncoding`. That file
  still has the bytes recorded under MH's HR-02 (`bd605d2e…`, 7 bytes, `0o400`, modified 2026-02-15). HR-03
  follows from this.
- **MH's value.** It equals MH's HOST's value.

**The source binding.**
- **The source inventory.** My recomputation from the observer's four trees, sixteen roles and three optional
  files, taken from its AST, is byte-identical: 644 files, 13,588,394 bytes. There is no link, `.DS_Store`,
  `__pycache__`, bytecode, special or multi-link file in it, and none under `<worktree>/prototypes`.
- **HEAD.** `/source/head` equals my reading of the Git files exactly, all four files' bindings included.
  `<worktree>/.git` names `<clone>/.git/worktrees/c271`, whose `commondir` leads to `<clone>/.git`. HEAD is
  `ref: refs/heads/work/c271-missing-import-digest-control`, and the loose ref holds B.
- **Commit B's loose object.** Its name recomputes, it names tree `0935162c…`, and its parent is `d3b622d6…`.
- **The index.** It is version 2, with 23,012 entries, a valid checksum and no conflict stage. Its TREE
  extension caches the whole index (23,012 entries) as tree `0935162c…`. Every one of the 644 source files is
  tracked and equals its index blob and executable bit. So the source set is tree B's, which M0's
  `tree_check` leaves to the provider (HR-05).

### 2.2 The two starts (question 2)

**Exactly one start each, with the planned argv, cwd, environment and limits, and cleanup proof.**

| | Git `--version` (M0) | Node `--version` (M1) |
| --- | --- | --- |
| argv | `[/Library/Developer/CommandLineTools/usr/bin/git, "--version"]` | `[<local>/c271-macos/node-v24.22.1-darwin-arm64/bin/node, "--version"]` |
| cwd | `<attempt>/git_version` | `<attempt>/node_version` |
| environment | the declared five and the six `GIT_*` names | the declared five |
| PID = process group | 30441 | 30442 |
| intent.json created | 19:49:14.688491Z: `UNKNOWN`, observed 0, `actual_direct_starts` null | 19:49:15.483483Z, the same |
| preflight recheck | 19:49:15.081048Z | 19:49:15.867068Z |
| inspection start / end | 19:49:15.085323Z / 19:49:15.093466Z | 19:49:15.915310Z / 19:49:15.957465Z |
| start observed (`started.json`) | 19:49:15.088403Z | 19:49:15.924604Z |
| receipt duration | 7.919 ms | 41.926 ms |
| postflight recheck | 19:49:15.482545Z | 19:49:16.339073Z |
| stdout | `git version 2.50.1 (Apple Git-155)\n`, 35 bytes | `v24.22.1\n`, 9 bytes |
| stderr | 0 bytes | 0 bytes |
| now | `kill` and `killpg` with signal 0: `ESRCH` | the same |

For each start, h04 run 3 verifies these records:
- **`intent.json`.** The 21 attempt keys, before the start: `UNKNOWN`, `artifacts` empty, and the plan's
  descriptor.
- **`started.json`.** The `on_started` record: one positive PID leading its own group, with the planned argv,
  cwd, environment and label. It has no return code or cleanup yet.
- **The supervisor's `<label>.process.json`.** Exactly the 14 receipt fields, in canonical bytes. It has the
  same PID, group, argv, cwd, environment, label and `start_monotonic` as `started.json`, and return code 0.
  It records `handles_closed` true and no error, with `cleanup` `{passed, process_group_absent, reaped}` all
  true and `elapsed_ms` 0. `observed_log_bytes` = `retained_log_bytes` = stdout plus stderr.
- **`inspection.json`.** The closed 12-key receipt, with `timeout_ms` 5000. Its `process` is the
  supervisor's receipt, its stdout and stderr are the logs' bytes, and `started.json`'s time lies inside it.
- **`postflight.json`.**
  - **The outcome.** `COMPLETED` and `OBSERVED_ONE`, with one actual and one observed start, no failure and
    no supervisor failure.
  - **The bindings.** Its `start` and its four artifacts are the files' descriptors.
  - **The rechecks.** Both passed, with the stages `before <id>` and `after <id>` and `facts_sha256`
    `3f062431…`. That is also `preflight.json`'s value and the Director's static run's.
- **The revision fields** are in all four records.

**The limits.** Each command has 5,000 ms in all, 3,000 ms of work and the 2,000 ms cleanup reserve. Both
durations lie inside the 3,000 ms of work.

**The order of the records** is strictly the planned one: the attempt directory (19:49:14.687468Z), Git's
intent, recheck, start and postflight, then Node's, then HOST (observed 19:49:16.722051Z, created 0.2 ms
later), `result.json` and `completion.json` (19:49:16.723914Z).

**Exactly one Git and one Node start, and no other process of the observer's.**
- **The records.** Each command has one receipt with a positive PID. node_version (kind `node`) gives 1 and
  git_version (kind `other`) gives 1, which are MR-PLAN section 8's rows M0 and M1. HOST's `starts`,
  `reserved.json`'s expected starts, and the exact counts in `result.json` and `completion.json` agree.
- **The source.** Statically, the observer has no process-creation call of its own. Its one start route is
  `supervisor.run_process` inside `_run_start`. `observe_host` calls `_run_start` once for each of the plan's
  commands, and `_plan_shape` admits exactly the two. `run_process` makes one `subprocess.Popen`
  (supervisor line 155). The static route calls no `run_process`.
- **The PIDs.** 30441 and 30442 are consecutive. That is consistent with no other process creation on the
  host in the 0.83 s between the two forks, since XNU assigns PIDs in sequence.
- **The limit of this evidence.** The observer installs no audit hook and records no PID of its own (HR-06).

**The static run before observe** printed `STATIC_READY` with zero starts and `facts_sha256` `3f062431…`
(PR-04's value). Its stdout is byte-identical to W2's static run.

### 2.3 The attempt's completeness and the capture records (question 3)

**The attempt is exactly M0-LAUNCH's success topology.**
- **Its entries.** It holds the three directories (`0o700`) and the 19 listed files. None of the three
  `failure.json` files exists, and there is no temporary, hidden or `.DS_Store` entry.
- **Its modes.** The observer's 13 documents are `0o600`, and the supervisor's six files `0o644` (umask 022).
  Every file has one link.
- **Its descriptors.** Every descriptor that `result.json`, `completion.json`, HOST, the postflights and
  observe's stdout give is the file's own. 17 of the 19 files are described that way; the two
  `intent.json` files are described by none, by design.
- **The result and the completion.** `result.json` is `PENDING_COMPLETION`, not finalized, by design (HR-01).
  `completion.json` is `OBSERVED_UNAPPROVED`, finalized, boundary `real`. Observe's stdout is exactly
  `result.json` completed by the result and completion descriptors, with that state.
- **`reserved.json` and `preflight.json`.** The first names the attempt, its three owned directories and the
  expected starts. The second carries the facts digest and the inventory digest `c277bdd3…`.

**The capture files and command records hold what FC-K2 and FC-K3 require.** There are eight files beside
the attempt, never inside it: `observe-001.{static,observe}.{stdout.txt,stderr.txt,exit.txt,command.json}`.
Each command record holds:
- **the command:** the argv `/usr/bin/env -i` with the five declared assignments, then
  `<worktree>/.venv/bin/python -I -S -B <observer> static|observe --plan <plan> --plan-sha256`, then exactly
  one digest. That is M0-LAUNCH's `argv_without_digest` followed by the plan review record's `/plan/sha256`,
  `cc1c2def…`. The cwd is the evidence parent;
- **the environment file:** M0-ENVIRONMENT.json by path, with its SHA-256 `0ed78f47…` as it is now;
- **the boot:** before and after, both the plan's;
- **the outputs:** exit 0, equal to the exit file `0\n`. The stdout digest and size equal the file, stderr is
  empty (`e3b0c442…`, 0 bytes), and there are 0 retries. Each stdout is one canonical line;
- **the writer:** `director/run/run_once_p36.sh`.

**The windows agree with what the records cite.**
- **The static run.** Its window is 19:49:01.403718Z to 19:49:02.421844Z (1.018126 s).
- **Observe.** Its window is 19:49:14.197371Z to 19:49:16.736380Z (2.539009 s). It holds the attempt
  directory's creation, every attempt entry's creation, and HOST's observation time.
- **Both.** Each stdout file was created inside its window, and each exit file after it. The record names end
  in `.command.json`, as PR-01's disposition names them; M0-LAUNCH had suggested `.command-record.json`.

**The evidence parent** holds exactly these nine entries. It and its six ancestors keep the plan's device,
inode and mode, and none is a link.

**The wrapper** is `run_once_p36.sh`, `9154f181…`, 3,629 bytes, `0o644`. Apart from comment lines, it is MH's
`run_once_v2.sh` (`3c24f923…`) with only the evidence parent, the message prefix and the record schema and
writer names replaced. Both have 43 code lines; 18 differ, and none differs after those substitutions. It
starts no Python of its own, and it executes the argv once in a subshell (HR-08).

### 2.4 Comparison with MH's HOST (question 4)

MH's HOST is unchanged: `34e94f29…`, 18,420 bytes, `0o600`. Its 16 differing leaves:

| Pointer | MH | This HOST | Why |
| --- | --- | --- | --- |
| `/source/commit`, `/source/head/commit` | C `0eb9a551…` | B `4ca78142…` | the commit under observation |
| `/source/tree` | `ea10cd94…` | `0935162c…` | C's tree and B's |
| `/source/head/files/<clone>/.git/refs/heads/work/c271-missing-import-digest-control/sha256` | `e76beaf7…` | `88eb2e8e…` | the loose ref file holds the other commit (41 bytes in both) |
| `/observed_at_utc` | 2026-11-27T05:34:41.185023Z | 2026-11-27T19:49:16.722051Z | the time of the observation |
| `/plan/path`, `/plan/sha256` | MH's plan `b8cd6449…` | MR's plan `cc1c2def…` | MR's own plan (9,017 bytes in both; 37 leaves differ, as the plan review lists them) |
| `/inspections/{git,node}_version/{path,sha256,size_bytes}` | MH's receipts, 1,441 and 1,163 bytes | MR's receipts, 1,443 and 1,165 bytes | another evidence parent, other times, and PIDs with five digits instead of four (two more bytes each) |
| `/source/inventory/path`, `/python/inventory/path`, `/dependencies/inventory/path` | `<local>/c271-p35/workers/W2-plan-001/…` | `<local>/c271-p36/workers/W2-plan-001/…` | MR's own copies; SHA-256, size and mode equal MH's |

**Must be equal, and are.**
- **The host.** The platform, boot included, the OS identity with the cryptex hop, and the environment with
  the CoreFoundation value.
- **The observer.** Its descriptor.
- **The interpreter and its inventory.** The whole `python` group (interpreter, selection, inventory digest,
  packages, RECORD rows, lock), apart from the inventory's path.
- **The runtime and the reader tree.** All of `runtime`, and `dependencies` apart from its inventory's path.
- **Git.** Its binding and its version line.
- **The rest.** The labels, the claims, the starts and the identifiers.

**The inspection receipts each HOST binds** differ only in times, PID and group, the monotonic times and the
stage path. Their argv, environment, timeout, return code, cleanup, log sizes, stdout and stderr are equal.
- **Git.** It took 7.919 ms here, against MH's 6.654 ms.
- **Node.** It took 41.926 ms here, against MH's first execution of 1,109.748 ms (HR-06).

No other difference exists.

### 2.5 Anything that should stop a configuration from binding this HOST (question 5)

**Nothing.** I read the provider's HOST consumer (`_verify_host`, `_cross_bindings` and the checks they
call). Every value it re-checks agrees with the host now:
- **The state.** Platform, kernel version string, boot, OS identity and cryptex hop equal HOST's exactly.
- **The environment record.** It is exactly the declared five, optionally plus the variable.
- **The unit process.** It must be the bound CPython build launched as `<worktree>/.venv/bin/python`, with
  HOST's process image.
- **The Python inventory.** It is recomputed and must be byte-equal to the frozen file at HOST's path.
- **The runtime.** It is re-observed in full, the install plan and receipt included.
- **Git.** It is checked by its bytes.
- **The inspection receipts.** They are re-read through HOST's descriptors.
- **The rest.** The labels, the starts and the claims.
- **The cross-bindings.** The configuration's source root, commit, tree and source-inventory descriptor, and
  its reader-tree root and inventory descriptor, must equal HOST's.

**What this means for S6** (HR-02):
- **Exact descriptors.** The configuration must carry HOST's two inventory descriptors exactly, paths
  included.
- **Retained inputs.** W2's three inventories, the attempt's two inspection receipts, MP's four plan and
  receipt files and both archives become inputs of every R1 start. They must stay unchanged at their paths
  and modes.

**Conditions that would refuse later, fail closed.** None of them is present now:
- a reboot or an OS update;
- a change of `<home>/.CFUserTextEncoding` or of the language and region settings (HR-03);
- an added bytecode file in the framework tree or the venv (HR-04);
- a change of any bound file.

### 2.6 Privacy (question 6)

These records use the labels above. They quote no user name, home directory, volume name or
CoreFoundation value. The boot UUID, commit names and digests already stand in committed records.
- **Comparisons, not values.** The CoreFoundation value and the text-encoding file are compared, never
  printed.
- **Listings.** The process listings printed only PIDs, parents, start times, image paths and interpreter
  option flags, never arguments or environments.
- **The scan.** `w3h_08_seal.py` scans every file in OUT before it writes `SHA256SUMS.txt`. It looks for the
  owner's account name, full name and home directory, the volume's and the parent directory's machine
  paths, the package prefix and the CoreFoundation value, all derived at run time. It reports only counts.
- **Kept.** `/Users/runner` appears in the N-06 rows: it is the Pillow wheel's build path, not an account of
  this host.

## 3. Findings

All eight are nonmandatory. None prevents binding HOST as observed.

### HR-01 (nonmandatory): HOST's finality rests on `completion.json`, not on `result.json`

- **Location:** `<attempt>/result.json`, `completion.json` and `HOST.json`; observer `observe_host` (lines
  2707 to 2722) and `host_document` (line 2645).
- **Issue:**
  - **The order.** `result.json` is written inside the attempt before the completion marker, with
    `PENDING_COMPLETION` and `evidence_finalized` false. Only `completion.json` and observe's stdout say
    `OBSERVED_UNAPPROVED` and finalized.
  - **The counts.** HOST's `starts` is a constant of `host_document`, and the computed counts are checked
    after HOST is published.
  - **Here.** Every record agrees.
- **Recommended change:** The freeze binds HOST together with `completion.json` (`9db0900a1d8af90eebd3c73dac1f65791c7091723637064e544f74c7dc8469b0`,
  981 bytes) and `result.json` (`ec9fd08f3b0a33a5e081d2559149894085434e762d7cddc226c5b934c9c5d4e7`, 2,621
  bytes), and cites `completion.json`'s state. This is MH's HR-04 again.

### HR-02 (nonmandatory): what a configuration must reproduce, and the files HOST makes inputs of every R1 start

- **Location:** `current_host_readback_v02.py` `_cross_bindings` (lines 695 to 712), `_check_python` (534 to
  562), `_check_runtime` (565 to 587) and `_check_inspections` (647 to 658); HOST `/source/inventory`,
  `/dependencies/inventory`, `/python/inventory`, `/inspections` and `/runtime/install`; MR-PLAN section 6,
  "Retained unchanged".
- **Issue:**
  - **Exact descriptors.** The provider refuses unless the configuration's `source.inventory` and
    `dependencies.inventory` descriptors equal HOST's, path included. The files are W2's copies in
    `<local>/c271-p36/workers/W2-plan-001/`: byte-identical to MH's, at new paths.
  - **Files re-read at each check.** The provider re-reads, through HOST's paths:
    - the frozen Python inventory, in the same directory;
    - MP's plans and receipts and the Node archive;
    - the attempt's two inspection receipts.
  - **The unit process.** It must be exactly `<worktree>/.venv/bin/python`, with HOST's version, build
    string and process image.
  - **What MR-PLAN names.** Section 6 names the Node and C195 archives, MP's records and MH's records as
    retained unchanged. It does not name W2's three inventories or the attempt's receipts.
- **Effect:** None on HOST. A moved or changed file refuses every start, which fails closed.
- **Recommended change:**
  - **Bind the descriptors.** The freeze binds the configuration's source and reader-tree inventories to
    HOST's descriptors.
  - **List the files.** It lists W2's three inventories (`95abd300…`, `c277bdd3…`, `3545d5f9…`) and the
    attempt's two inspection receipts (`bbbb832f…`, `009fbd06…`) among the files retained unchanged through
    S8.
  - **The launcher.** It launches R1's unit stage through `<worktree>/.venv/bin/python`.

### HR-03 (nonmandatory): the CoreFoundation value still depends on an unbound file in the owner's home directory

- **Location:** HOST `/environment/cf_user_text_encoding`; contract S10 and section 12; MC30 and MC31; MH's
  HR-02 and its disposition.
- **Issue:**
  - **Its parts.** The value is built from the UID and `<home>/.CFUserTextEncoding`. That file is unchanged
    since MH: `bd605d2e…`, 7 bytes, `0o400`, modified 2026-02-15.
  - **Reproduced.** The value equals MH's HOST, my processes now, and a declared-environment launch.
- **Effect:** None on HOST. A language or region change before or during R1 would make the probe's
  environment binding refuse every positive start until a new HOST. This fails closed.
- **Recommended change:**
  - **Record the file.** The freeze records that file's SHA-256 again as an unbound host fact.
  - **Keep the settings.** The owner keeps the language and region settings unchanged through S8, as MR-PLAN
    section 6 already requires.

### HR-04 (nonmandatory): users of the bound interpreter continue during MR

- **Location:** MR-PLAN section 6 (`-B` for every start, other sessions included); PLAN-REVIEW-001 PR-02 and
  PR-03 and their dispositions; MH's HR-03; MC32.
- **Issue:**
  - **PR-03's launchd job.** PID 1304 still runs `<framework>/Resources/Python.app/Contents/MacOS/Python`.
    Its parent is launchd, it started 2026-11-23T12:21:13Z, and it has no interpreter option (no `-B`).
  - **PR-02's application.** At 20:14:42Z, during this review, the other agent application (its
    controlling process has run since 2026-11-26T00:30:42Z) started a parent and a child of the same image.
    The parent's options were `-B -`, reading from stdin. Its child had ended before I could read its
    options.
  - **What I read.** Only PIDs, parents, start times, images and option flags.
- **Effect:**
  - **None so far.** The Python inventory recomputed byte-identical at 20:11:06Z, before that pair, and at
    20:16:19Z, after it.
  - **The risk continues.** A bytecode file added by a start without `-B` would refuse R1 at the provider's
    inventory check (MC32). That fails closed, at the cost of an attempt.
- **Recommended change:**
  - **Keep the precondition.** The freeze's D-P5 recheck immediately before R1 stays a stated precondition.
  - **Tell the owner.** The Director tells the owner again. The owner may pause the job and that
    application until S8 ends.

### HR-05 (nonmandatory): what HOST records without deciding

- **Location:** HOST `/source/tree`, `/source/tree_check`, `/source/head`,
  `/python/interpreter/flags/utf8_mode`; N-02, N-03; `_cross_bindings`.
- **Issue:**
  - **`/source/tree`.** It is a planned value, which M0 does not check. This review checked it statically.
    B's loose object names `0935162c…`, the index caches its whole content as `0935162c…`, and all 644
    source files equal their index blobs (section 2.1).
  - **`/source/head/files`.** It binds the loose ref file in `<clone>/.git`. Git maintenance there
    (`pack-refs`) could remove that file without changing B. The provider does not re-compare `head`, so
    this matters only for a new observe.
  - **`utf8_mode`.** It is 0 because `LC_ALL=C.UTF-8`, and my declared-environment launch reproduced it.
  - **No cache identity.** HOST records neither the shared cache's identity nor dyld's (N-03). At 20:18Z
    both still had N34-M's bytes: the cache `7a024959…` (UUID `F2E86C53-6052-388B-BA71-5A0C9B569413`) and
    dyld `373fce2b…`.
- **Effect:** None. Every field agrees with the host now.
- **Recommended change:** The freeze cites this review for the tree, the index and the cache facts.

### HR-06 (nonmandatory): the start-count evidence, and Node's warm start time

- **Location:** `_run_start`; the attempt's receipts; MR-PLAN section 8; P07 section 4; MH's HR-07.
- **Issue:**
  - **No audit hook.** The observer installs none and records no PID of its own. So the count rests on the
    two receipts with positive PIDs, on the source's single start route, and on the consecutive PIDs.
  - **Node's time.** Node took 41.926 ms here, against MH's first execution of 1,109.748 ms: this was not
    the first execution.
- **Effect:** None. Every P07 rule is met, and both durations lie within the limits.
- **Recommended change:**
  - **The audit.** S8 states this basis for M0's and M1's counts.
  - **The freeze.** Its bounds do not rest on the warm figure. The 1.11 s of a first execution is the only
    other timing evidence for `bin/node` on this host.

### HR-07 (nonmandatory): HOST's claims do not restate every limit that applies to M0 and M1

- **Location:** HOST `/claims`; the observer's `CLAIMS`; contract sections 5, 7 and 10; MH's HR-06.
- **Issue:** The four fixed texts state the closure, Python, boot and status limits. They do not restate
  three others:
  - **Descendants.** The Darwin supervisor's descendant limit: there is no enforcement against descendants.
  - **Durability.** HOST and the receipts were published with `fsync`, not `F_FULLFSYNC`.
  - **Git.** It is bound by bytes and a version grammar only.
- **Effect:** None. The provider requires exactly these texts.
- **Recommended change:** The freeze and the audit cite contract section 10 for the full list, and do not
  read `/claims` as complete.

### HR-08 (nonmandatory): the wrapper and its records

- **Location:** `<local>/c271-p36/director/run/run_once_p36.sh`; the two command records; WORKERS.md line 9;
  PR-01's disposition; MH's HR-01.
- **Issue:**
  - **No binding.** No reviewed plan binds the wrapper, although the records' shape depends on it.
  - **Its times.** Its UTC strings come from separate `date` calls with second resolution, and its epoch
    fields are the precise times.
  - **The log.** The worker log dates the wrapper's writing at 15:58Z, but its modification time is
    15:51:54Z.
  - **Here.** Every value I could check in both records is right (section 2.3).
- **Effect:** None on HOST.
- **Recommended change:** If S7 uses the wrapper, the freeze binds it by path and SHA-256 (`9154f181…`,
  3,629 bytes) and treats its epoch fields as the authoritative times, as MH's HR-01 disposition did.

## 4. Starts and conduct

**Allowed starts only.**
- **Shells.** One for each of my 24 Bash calls.
- **Utilities.** Read-only ones in those shells: `ls`, `head`, `grep`, `cut`, `ps`, `sed`, `awk`, and `mkdir`
  once for OUT.
- **My own scripts.** 12 starts of `python3 -I -S -B`, which resolves to `<framework>/bin/python3.12`, the
  bound framework interpreter (h02 check P14). One of them was entered through `/usr/bin/env -i` with the
  declared five, which executes the interpreter in its own process.

**No forbidden start.** I started no Git of any kind, no Node, `ldd`, `codesign` or `otool`, no observer
command, no driver and no unit test. Every interpreter start carried `-B`.

| # | Call | Processes |
| ---: | --- | --- |
| 1 | `ls` the review directories and the evidence, `head` | shell, ls, head |
| 2 | `ls` the contract, implementation and MH directories | shell, ls |
| 3 | `ls` the plan, review, run and evidence directories | shell, ls |
| 4 | `grep` that listing, `head` | shell, grep, head |
| 5 | `grep` N34-M's headings and findings, `head` | shell, grep, head |
| 6 | `mkdir` OUT, `command -v python3`, `umask` | shell, mkdir, one forked subshell |
| 7 | `grep` `supervisor.py`, `head` | shell, grep, head |
| 8 | h02 run 1 | shell, Python |
| 9 | h01 run 1 | shell, Python |
| 10 | h03 run 1 | shell, Python |
| 11 | h04 run 1 (superseded) | shell, Python |
| 12 | `grep` the two sources for process-creation names, `cut` | shell, grep, cut |
| 13 | h04 run 2 (superseded) | shell, Python |
| 14 | `grep` h04 run 2's output twice, `head` twice | shell, grep, head, grep, head |
| 15 | h04 run 3 | shell, Python |
| 16 | h05 | shell, Python |
| 17 | `env -i` … h06 | shell, one env-then-Python process |
| 18 | `ps` and `grep` the images, `sed` the labels; `ps` and `grep -c` for observer processes | shell, ps, grep, sed, ps, grep, one forked subshell |
| 19 | `ps` and `awk` for three processes' option flags | shell, ps, awk |
| 20 | h02 run 2 and h03 run 2, the rechecks | shell, Python, Python |
| 21 | h07, the final recheck | shell, Python |
| 22 | `grep` the rechecks' times | shell, grep |
| 23 | `ps` for one process's short name and this shell | shell, ps |
| 24 | h08, the seal | shell, Python |

**Totals.** 24 shells, 12 Python processes and 26 utility processes, 62 in all, plus 2 forked subshells.
- **The utilities:** 9 `grep`, 6 `head`, 4 `ps`, 3 `ls`, 1 `cut`, 1 `sed`, 1 `awk` and 1 `mkdir`.
- **Recorded PIDs.** Each Python process recorded its PID and its shell's PID in its output. h07 found the
  ten earlier ones absent.

**Limits of this count.**
- **The harness.** Each shell is started by the agent harness, which evaluates my command inside it after its
  own set-up. Whatever that set-up runs is outside my view.
- **The file tools.** The file-read and file-write tools start no host process that I can observe.
- **The Git summary.** The harness attached a Git status summary of the main clone to my initial context.
  No command of mine produced it.

**Nothing else changed.**
- **Bound trees.** I made no edit in `<worktree>`, `<clone>`, the prepared trees, MP's or MH's records, W2's
  directory or the evidence. My two inventory rechecks found both installation trees and the source set
  unchanged.
- **The evidence.** h07 found the attempt and the evidence parent as observe left them.
- **Downloads, installs and Finder.** I downloaded and installed nothing, and used no Finder.

## 5. Files

**The documents of the run**, under `<local>/c271-p36/evidence/`:

| File | SHA-256 | Bytes |
| --- | --- | ---: |
| `observe-001/HOST.json` | `858ef72a949ce7575787290601ae70d117090a460781b2e660a3b0d4f0162666` | 18,420 |
| `observe-001/completion.json` | `9db0900a1d8af90eebd3c73dac1f65791c7091723637064e544f74c7dc8469b0` | 981 |
| `observe-001/result.json` | `ec9fd08f3b0a33a5e081d2559149894085434e762d7cddc226c5b934c9c5d4e7` | 2,621 |
| `observe-001/preflight.json` | `8e919a2bd7510884d3d5a1a7879e042e71944932e69229a2d8c77a70aac4d8dd` | 586 |
| `observe-001/reserved.json` | `63750c8c762e7ee9ab5617d97ac5050061f9a1001a551eaa84a5c5f759ef0b1e` | 785 |
| `observe-001/git_version/inspection.json` | `bbbb832fb9e81356b7ad06df8f71f79df1860758cebc198e9d7999cdf3311448` | 1,443 |
| `observe-001/node_version/inspection.json` | `009fbd0658b57e7360d4269097472ed173b108a4f9a93b9687323fdacbb6cd65` | 1,165 |
| `observe-001/git_version/postflight.json` | `50de248809a506bdbc8b3b3e8e43d575ea2566578f5ed3024e8c7e52cd276042` | 2,999 |
| `observe-001/node_version/postflight.json` | `c33ed62353d8910bca5501056547c5ef9d5e77c18d20c38aed006c2382683b2e` | 2,918 |
| `observe-001.static.stdout.txt` | `f62c062cddd780426e260c54c97d9af60c81f766b684da2c57b34e5e29dd25c7` | 1,650 |
| `observe-001.observe.stdout.txt` | `a32afe99f88741417b7db384e4c18b745b8e52fd0f37b18207a024f9a14eeadd` | 3,045 |

**The full list.** `outputs/h07-final-run1.json` lists the SHA-256, size and mode of all 75 files I reviewed:
the attempt and the capture files, the plan and its inventories and launch records, the plan review and its
disposition, the wrapper and MH's, MH's HOST and receipts, the governing documents and sources, and every
bound input I recomputed. `SHA256SUMS.txt` lists every file in OUT except itself.
