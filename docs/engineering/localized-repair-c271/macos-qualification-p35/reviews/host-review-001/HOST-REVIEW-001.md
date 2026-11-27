# HOST review 001: HOST of attempt observe-001 (M0 and M1)

| | |
| --- | --- |
| Reviewer | W3, the independent HOST reviewer: a Claude Code subagent in a fresh context, with no earlier review in it. W3 wrote none of HOST, the observer, the supervisor, the plan, its review, the contract, the amendment, MP's preparation, the MH tooling or the Director's wrappers. |
| Gate and stage | gate MH, phase `C271-P35-macos-host-qualification-mh`, end of stage S5 of MH-PLAN, local mode |
| Under review | `<local>/c271-p35/evidence/observe-001/HOST.json`, written by the observer's `observe` under observation plan 001, and the evidence of that run |
| Commit C | `0eb9a5517f4e19705178a2c59b8d8d33fb87867a`, tree `ea10cd94c05a2ebbb44b3f83d4c96cb0a59baa2b` |
| Host | macOS 26.6.2 (25G83), Darwin 25.6.0, arm64, boot `C90010BA-4DA9-475D-BBAB-CF1A9C40175A` (booted 2026-11-23T12:20:29Z) |
| Written | 2026-11-27, after this review's checks of 05:55Z to 06:05Z |

Places are named by labels:

- `<worktree>` is the C271 worktree at commit C.
- `<local>` is the working directory beside the clone; `<local>/../..` is the external volume's mount point.
- `<common-dir>` is the clone's Git directory, which `<worktree>/.git` names through `<common-dir>/worktrees/c271`.
- `<prefix>` is the installation prefix of the interpreter's framework and of its non-system libraries, and
  `<package-manager>` the package manager that owns it.
- `<framework>` is `<prefix>/Cellar/python@3.12/3.12.13/Frameworks/Python.framework/Versions/3.12`.
- `<home>` is the owner's home directory.
- `OUT` is `<local>/c271-p35/workers/W3-host-001/`, the only place I wrote.

The machine-readable form is [HOST-REVIEW-001.json](HOST-REVIEW-001.json).

## Verdict

**ACCEPT_WITH_NONMANDATORY_FINDINGS.** There is no mandatory finding. HOST may be bound as observed.

**HOST's SHA-256, computed from the file's bytes:**
`34e94f29ea1b7d9d60b389598b4ce5bc7eaf6fcaa58f3798fc3df021a8f28a92`. The file is 18,420 bytes, mode
`0o600`, one link, canonical JSON. It equals the host descriptor in `result.json`, in `completion.json` and
in observe's stdout.

- **HOST is exactly W3-OBSERVER section 3's document.** Every key is present at every level, and no
  object has an extra member.
- **Every value I could recompute agrees.** I recomputed the descriptors, the OS identity, the platform,
  Node's Mach-O header and all 21 load commands, and the source and HEAD facts with my own code. The
  Python inventory I recomputed is byte-identical to the frozen one, digest `c277bdd3…`. The interpreter
  facts match those of a process launched exactly as the observer was.
- **HOST agrees with plan 001 on every bound value.** That covers 23 groups of values.
- **The two starts are exact.** There is one start each, with the planned argv, cwd, environment and
  limits. Each has full cleanup proof, and the predicates hold. Git printed `git version 2.50.1 (Apple Git-155)\n`
  and Node `v24.22.1\n`, and both stderr logs are empty. The counts are `{node: 1, other: 1}`.
- **N-07 holds.** The recorded Git line is exactly `git version ` + the text embedded in the bound file's
  arm64 slice.
- **D-16 holds.** HOST's command 14 is a plain `LC_LOAD_DYLIB` of CoreFoundation. HOST records
  `__CF_USER_TEXT_ENCODING` as `0x1F5:0x0:0x0`.
- **N-06 and N-03.** No `LC_RPATH` entry is used, and the absent build path fails closed. The shared-cache
  facts are N34-M's, and they fit HOST's OS identity.
- **The capture records are consistent.** They agree with the attempt as it now is, and both started
  processes are absent by `ESRCH`.
- **Seven nonmandatory findings, HR-01 to HR-07.** The most important are:
  - **HR-01:** the static run's FC-K3 record is hand-written under a second name;
  - **HR-02:** the CF value depends on an unbound file in the owner's home directory;
  - **HR-03:** PR-03's job still runs on the bound interpreter.

## 1. Method

### 1.1 Reads

I read these with the agent's file-read tool, which starts no host process:
- **The plan of the gate:** MH-PLAN.md, all of it.
- **The observer's interface:** W3-OBSERVER.md, all of it.
- **The contract:** CONTRACT.md, all of it, sections 3, 4, 7 and 10 above all.
- **P07:** QUALIFICATION-PLAN.md sections 2 to 4.
- **N34-M:** N34-M-REVIEW.md (sections 1 to 3, N-01 to N-09 and section 6) and N34-M-DISPOSITION.json.
- **The tooling:** FAILURE-CAPTURE.md.
- **The code:** all of `current_host_observation_v02.py`, both supervisor files, and the HOST consumer
  in `current_host_readback_v02.py`, lines 487 to 713.
- **The plan and its review:** the plan, M0-LAUNCH.json, PLAN-REVIEW-001.md (verdict, method, sections
  2.4 to 5) and its disposition.
- **The Director's two wrappers.**
- **The evidence:** every file in the evidence parent and in the attempt.

### 1.2 Scripts

My scripts are in `OUT/scripts/` and their outputs in `OUT/outputs/`.
- **No dependencies.** They use the standard library only and import nothing of the project.
- **No process creation.** Each installs an audit hook that refuses every process-creation event, and
  every ctypes lookup of libc's process-creation functions. No script recorded such an event.
- **No machine path.** Every path is an argument, or read from HOST or the plan.
- **Absent outputs only.** Each output is written to an absent path with `O_EXCL`.
- **Their own code.** The reader, the link resolver and the Mach-O parser in `h_common.py` are mine. So
  are the inventory closure in h02 and the Git object, pack and index readers in h03.

| Script | What it does |
| --- | --- |
| `h00_explore.py` | The structure of the frozen inventories and receipts, read only to learn their shapes |
| `h_common.py` | Shared helpers: bounded hashing, the link resolver, the thin Mach-O parser, exact birth times through `getattrlist` |
| `h01_host_bindings.py` | 173 checks of HOST's bytes, closed shape and constants. It recomputes every descriptor and binding, the OS identity, the platform, the runtime layout, `NODE-SOURCE.json`, Node's Mach-O, Git's fat file and embedded version, the reader tree, the receipts, the shared cache and dyld. It also compares HOST with the plan. |
| `h02_python_inventory.py` | The Python inventory recomputed from W3-OBSERVER section 5: both trees, the selection chain and the closure. Also the packages and RECORD rows, the interpreter facts of its own process, and every `LC_RPATH` entry. |
| `h03_source_and_head.py` | The source inventory, then HEAD from the Git files. Commit C's object and its whole tree come from the loose objects and the pack, the index is compared with the tree, and every tracked worktree file with its index blob. Untracked files, bytecode and `.DS_Store` are looked for. |
| `h04_evidence.py` | Questions 2 and 7: every start record, receipt, predicate, time and count. Also the readback listing against the attempt now, the probes, the four command records, the static record and the wrappers, the evidence parent and its ancestors, the CF value against the owner's text-encoding file, and the processes that run the bound images. |
| `h04b_declared_launch.py` | A process launched as the observer was (`/usr/bin/env -i` with the declared five, then `<worktree>/.venv/bin/python -I -S -B`). It compares its own environment and interpreter facts with HOST. |
| `h05_report_json.py` | Writes HOST-REVIEW-001.json, with every reviewed file's SHA-256 computed at that time, after a scan of both reports for machine paths and names |
| `h06_final_check.py` | The final recheck of HOST, the evidence, both inventories and my processes, and the scan of both reports again |

**Superseded runs.** These outputs are kept beside the later ones:
- `h04-evidence.json`. Two of its checks were mine and too strict: they compared birth times through
  floats, and the wrapper's second-resolution UTC strings with the floor of its epochs. Run 2,
  `h04-evidence-run2.json`, reads exact birth times through `getattrlist` and checks a window. Its 49
  checks all passed.
- `h04b-declared-launch.json`. My helper sliced the `proc_pidpath` buffer before the call filled it. Run 2
  corrects that.
- `h02`'s check P11. It failed only on `utf8_mode`, because my shell's locale is not the declared one. h04b
  run 2 settles it (section 2.1).
- h05's runs 1 and 2. They wrote nothing: their scan took `/Users/runner;` (the Pillow build path, with
  its semicolon) for a user's path. Run 3's scan stops at characters that cannot be in a user name.

## 2. Answers

### 2.1 HOST's shape and content (question 1)

**HOST is exactly W3-OBSERVER section 3's document, closed at every level** (h01 B01 to B42).
- **The top level.** It has the 21 keys of section 3, including `design_revision` 4 and `amendments`
  `["P33-AMENDMENT-001"]` (W3-C1).
- **Every sub-object has exactly its listed members.** These are:
  - `platform`'s six, and `os.system_version`'s nine;
  - `os.cryptex`'s eleven, with `link_path` and `hops`;
  - `python`'s ten, `python.interpreter`'s ten, its 18 flags and `selection`'s eight;
  - `runtime`'s nine, `macho`'s eight, and each `install`'s four;
  - `source`'s six and `head`'s five;
  - `labels`' eleven, with `os.cryptex`'s `state` (W3-C3);
  - the four `claims`.
- **The form.** HOST is canonical JSON, with no duplicate member. `starts` is `{node: 1, other: 1}`.
  `labels.run_kind` is `host-observation` and `labels.boundary` is `real`.

**Every recomputable value agrees with my own static reads:**
- **Descriptors and bindings.** I rehashed each of these and found HOST's SHA-256, size and mode:
  - the plan and the observer;
  - the frozen Python inventory, the lock and the source inventory;
  - the Node archive, `NODE-SOURCE.json` and `bin/node`, which has one link;
  - both install plans and both receipts;
  - the dependency inventory and the C195 archive;
  - Git and both SystemVersion.plist files;
  - the four Git files of `head`, and both inspection receipts.

  The Node archive's digest is the contract's pin, and the C195 archive's is its pin.
- **OS identity and cryptex.** Both plists read as macOS 26.6.2, build 25G83, with no `ProductVersionExtra`.
  The two files are byte-identical (`6151cb88…`, 603 bytes, `0o444`).
  - **The cryptex path.** My own resolver walks `/System/Cryptexes/OS/...` through the one hop
    `/System/Cryptexes/OS → ../../System/Volumes/Preboot/Cryptexes/OS`. The canonical copy has no linked
    component (F1, D-10).
  - **The label.** `labels.os` equals the recomputed identity.
- **The platform.** `os.uname()` gives Darwin, release 25.6.0, the recorded kernel version string, and
  arm64. `sysctlbyname` gives `proc_translated` 0 and the plan's boot session. `kern.boottime` is
  2026-11-23T12:20:29Z.
- **The Python inventory's digest.** My own walk, selection chain and closure give a canonical document
  byte-identical to the frozen file. It has 776,209 bytes and the SHA-256
  `c277bdd3ac6aa73105df3924707a271a402a0dc7c722be27a6834f2c78605633`, which is HOST's `inventory_sha256` and
  its label. The figures are N-08's frozen ones:
  - **framework:** 3,478 files, 414 of them bytecode, 305 directories and 5 links;
  - **venv:** 297 files, 45 directories and 3 links;
  - **images:** 111, of which 79 in the framework, 27 in the venv and 5 external;
  - **closure:** 6 link hops; it reached its fixed point in two passes.

  No tree entry, image, dependency, hop or selection key differs. HOST's `selection` is my selection.
  - **Packages.** The seven pins are installed at their versions, and every RECORD row matches. Every file
    under site-packages has one owner, and HOST's `packages` and `records` equal mine.
- **The interpreter facts.** In h04b run 2, under exactly the declared environment, every member of
  `python.interpreter` equals HOST's, `sys.flags` included. That process ran as `<worktree>/.venv/bin/python
  -I -S -B`, with process image `<framework>/Resources/Python.app/Contents/MacOS/Python`.
  - **`utf8_mode` depends on the locale.** In my first launch, with my shell's locale, `utf8_mode` was 1.
    Under `LC_ALL=C.UTF-8` it is 0, as HOST records (HR-05).
- **Node's binding, Mach-O header and load commands.**
  - **The file.** `bin/node` is `6f320694…`, 122,545,856 bytes, `0o755`, with one link. The runtime
    directory holds exactly `{bin, bin/node, NODE-SOURCE.json}` with modes `0o755`. `NODE-SOURCE.json` is
    canonical, equals `runtime.node_source.content`, and describes that executable and the pinned archive.
  - **My parse.** My parser gives thin `MH_MAGIC_64`, `0x0100000c`, cpusubtype `0x00000000`, `MH_EXECUTE`,
    flags `0x00a18085`, 21 commands and 2,416 bytes. HOST's `runtime.macho` equals my parse field for field
    in all 21 commands.
  - **The rules.** Every command lies in the 16-command allow-list, with exactly one `LC_LOAD_DYLINKER`
    (`/usr/lib/dyld`) and one `LC_MAIN`. The four dylibs lie under `/System/Library/` or `/usr/lib/`, and
    there is no `@` path and no `LC_RPATH`. The code signature ends exactly at the end of the file.
- **Source and HEAD facts.**
  - **The source inventory.** My recomputation is byte-identical to the frozen one, `95abd300…`, with 644
    files. It has no bytecode, `.DS_Store`, link or file with a second link.
  - **HEAD.** Read from the files, `head` is HOST's exactly. `<worktree>/.git` names `<common-dir>/worktrees/c271`,
    whose `commondir` is `../..`. HEAD is `ref: refs/heads/work/c271-missing-import-digest-control`, and the
    loose ref in `<common-dir>` holds commit C.
  - **Commit C, read without Git.** Its loose object names tree `ea10cd94…`, which is HOST's planned
    `source.tree`. It has one parent, `c81cf07b…`, and was committed at 04:17:03Z.
  - **Index and worktree.** The index (version 2, 22,490 entries, no conflict stage) equals that tree in
    paths, modes and blobs. Every tracked worktree file equals its index blob, executable bit included.
    Nothing is untracked outside `.venv`, and no bytecode or `.DS_Store` lies outside it. No tracked file is
    newer than the index.

**HOST agrees with plan 001 on every bound value** (h01 E01 to E23). The groups are:
- the environment, the platform's five planned fields, and both OS descriptors with the cryptex state and
  path;
- the source root, commit, tree and inventory, and HEAD's commit;
- the observer;
- the venv, framework, version and frozen inventory, with `inventory_sha256` equal to its digest;
- the runtime directory, version, executable pin, archive, `NODE-SOURCE.json` binding, modes and both install
  descriptors;
- the dependency root, inventory and install descriptors;
- the Git binding, and the inspection paths;
- the labels' Git, Node and inventory values;
- the starts, against the plan's expected direct starts by kind.

### 2.2 The two starts (question 2)

**Exactly one start each, with the planned argv, cwd, environment and limits, and cleanup proof.**

| | Git `--version` (M0) | Node `--version` (M1) |
| --- | --- | --- |
| argv | `[<git>, "--version"]` | `[<local>/c271-macos/node-v24.22.1-darwin-arm64/bin/node, "--version"]` |
| cwd | `<attempt>/git_version` | `<attempt>/node_version` |
| environment | the declared five and the six `GIT_*` names | the declared five |
| PID = process group | 7994 | 7995 |
| intent.json | before the start: `UNKNOWN`, observed 0, `actual_direct_starts` null | the same |
| preflight recheck | 05:34:38.605766Z | 05:34:39.312705Z |
| inspection start / end | 05:34:38.608891Z / 05:34:38.615764Z | 05:34:39.358106Z / 05:34:40.468141Z |
| receipt duration | 6.654 ms | 1,109.748 ms |
| postflight recheck | 05:34:38.962889Z | 05:34:40.837624Z |
| stdout | `git version 2.50.1 (Apple Git-155)\n`, 35 bytes | `v24.22.1\n`, 9 bytes |
| stderr | 0 bytes | 0 bytes |

Here `<git>` is `/Library/Developer/CommandLineTools/usr/bin/git`, and `<attempt>` is
`<local>/c271-p35/evidence/observe-001`.

For each start, h04 run 2 verifies these records:
- **`started.json`.** The `on_started` record: one positive PID leading its own group, with the planned
  argv, cwd, environment and label. It has no return code and no cleanup yet.
- **The supervisor's `<label>.process.json`.** Exactly the 14 receipt fields, in canonical bytes. It has
  the same PID, group, argv, cwd, environment, label and `start_monotonic` as `started.json`, and return
  code 0. It records `handles_closed` true and no error, with `cleanup` `{passed, process_group_absent,
  reaped}` all true. `observed_log_bytes` = `retained_log_bytes` = stdout plus stderr.
- **`inspection.json`.** The closed 12-key 0.2.0 receipt, with `timeout_ms` 5000. Its `process` is the
  supervisor's receipt, and its stdout and stderr are the logs' bytes. `started.json`'s time lies between
  its start and end.
- **`postflight.json`.**
  - **The outcome.** `COMPLETED` and `OBSERVED_ONE`, with actual and observed starts 1, no failure and no
    supervisor failure.
  - **The bindings.** Its `start` and its four artifacts are the files' descriptors.
  - **The rechecks.** Both passed, with `facts_sha256` `3867d3e8…`. That is also `preflight.json`'s value
    and the Director's `static` run's.
- **No `failure.json`.** None exists, for either start or for the attempt.

**The limits.** The plan gives 5,000 ms in all, 3,000 ms of work and the 2,000 ms cleanup reserve. Both
durations lie inside the 3,000 ms of work.

**Cleanup proof.** On the success path the supervisor waited for the child (reaped), and found its group
absent: `killpg(pid, 0)` gave `ESRCH`. It then closed its handles, and the FC-P3 probe later found both
PIDs and groups absent (section 2.7).

**Order.** The records run in order:
- Git's intent, start and postflight;
- then Node's;
- then HOST, observed at 05:34:41.185023Z and published 1 ms later;
- then `result.json` and `completion.json`.

**The outcome predicates hold.**
- **Git.** The line matches `git-version-line-v1`.
- **Node.** stdout is exactly `v24.22.1\n`.
- **stderr.** Both are empty. PR-02's predicted risk did not occur.

**The start counts are exactly `{node: 1, other: 1}`** under P07 section 4's rules. Each command has one
receipt with a positive PID, so node_version (kind `node`) gives 1 and git_version (kind `other`) gives 1.
These are MH-PLAN section 7's rows M0 (other 1) and M1 (node 1).
- **The records agree.** HOST's `starts`, `reserved.json`'s expected starts and the computed `exact` and
  `observed_lower_bound` counts all agree. Those counts are in `result.json` and `completion.json`.
- **The limit of this evidence.** The count rests on the receipts and on the observer's source, which
  calls `run_process` exactly twice (HR-07).

### 2.3 N-07: the recorded Git line and the bound file's embedded text (question 3)

**They agree exactly.**
- **The file.** My static read of `/Library/Developer/CommandLineTools/usr/bin/git` gives N34-M's file:
  `be4afb2b…`, 7,604,272 bytes, `0o755`.
  - **Not the dispatcher.** It is not a link, nor `/usr/bin/git`. Its inode and bytes differ from the
    dispatcher's.
  - **Two slices.** It is fat, with an x86_64 slice (subtype 3, at offset 16,384) and an arm64 slice
    (subtype 0, at offset 3,899,392). There is no arm64e slice, so this host runs the arm64 slice.
- **Each slice:**
  - `MH_EXECUTE`, 22 commands, dylinker `/usr/lib/dyld`, built for minimum OS 14.0 with SDK 26.4;
  - links only CoreServices, libz, libiconv, libSystem and CoreFoundation, all cache images, with no
    `LC_RPATH`;
  - embeds the version text `2.50.1 (Apple Git-155)` once and the format `git version %s\n` once.
- **The comparison.** The recorded stdout, `git version 2.50.1 (Apple Git-155)\n`, is exactly `git version ` +
  the arm64 slice's embedded text + newline. HOST's `git.version` is that line without its newline. This
  confirms N34-M's and the plan review's static prediction.

### 2.4 D-16 and N-04 (question 4)

- **D-16.** HOST's `runtime.macho.commands[14]` is `cmd 0x0000000c`, `LC_LOAD_DYLIB`. Its path is
  `/System/Library/Frameworks/CoreFoundation.framework/Versions/A/CoreFoundation`, current 3038.1.255,
  compatibility 150.0.0. It is not a weak, lazy, upward or re-export command, and my own parse gives the
  same row.
- **The variable.** HOST records `__CF_USER_TEXT_ENCODING` with the value `0x1F5:0x0:0x0`, in
  `environment.cf_user_text_encoding`.
  - **Whose value.** It is the observer's own (Python) process value.
  - **Reproduced.** A process I launched exactly as the observer was (h04b run 2) sees exactly the declared
    five plus this variable with this value.
  - **Its parts.** The value is `0x` + the UID 501 in hex + `:` + the 7-byte content `0x0:0x0` of
    `<home>/.CFUserTextEncoding` (HR-02).
- **N-04 still applies.** M1 shows nothing of Node's `process.env`: the supervisor passed exactly the five
  declared names, and `--version` prints no environment. MH-PLAN section 10's tie stands. MC36 needs a
  positive probe start of the same freeze that observed `__CF_USER_TEXT_ENCODING` with HOST's value,
  `0x1F5:0x0:0x0` (MC30). If none observes it, MC36 stays `NOT_RUN`.

### 2.5 N-06: the unused `LC_RPATH` entries (question 5)

The closure records **81 `LC_RPATH` entries**:
- `<prefix>/lib` in 78 framework images, a directory;
- the sqlite library's own lib directory;
- libmpdec's `@loader_path/../lib`, which resolves to `<prefix>/Cellar/mpdecimal/4.0.1/lib` from both of
  its spellings;
- in Pillow's `.dylibs/libjpeg.62.4.0.dylib`, the absent build path
  `/Users/runner/work/Pillow/Pillow/build/deps/darwin/lib`. It is recorded as `state: absent` at its first
  missing component, `/Users/runner`.

**None of them is used at load time.** The 162 references are 127 system, 9 absolute bound and 26
`@loader_path`, with **no `@rpath` and no `@executable_path` reference**.

**They fail closed.** Each entry's resolution is part of the inventory's canonical bytes. If
`/Users/runner` appeared, for example through an account of that name, the resolution would change. Every
inventory recheck would then refuse (M0's, the provider's `_check_python`, MC32). No unbound load can
follow from it. The entries remain search paths for run-time `dlopen("@rpath/…")` calls, which the
contract does not bind (N34-M (f)).

### 2.6 N-03: HOST's OS identity and the shared-cache facts (question 6)

**They agree where they can be compared statically.** My own read of the cryptex's main cache file
`/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld/dyld_shared_cache_arm64e` gives:
- **N34-M's file.** SHA-256 `7a024959…` and 573,440 bytes. The magic is `dyld_v1  arm64e`, the UUID
  `F2E86C53-6052-388B-BA71-5A0C9B569413`, and the platform 1. There are 3,649 images and 12 subcaches, and
  `dyldInCacheMH` is `0x180114000`.
- **The OS version.** `osVersion` is 26.6.0. It agrees with HOST's 26.6.2 (25G83) on the major and minor
  release. The cache field neither confirms nor refutes the patch level or the build.
- **The system references.** Node's four are CoreFoundation, Security, `libc++.1` and `libSystem.B`. Git's
  five are CoreServices, CoreFoundation, libz, libiconv and libSystem. Each is absent from disk and present
  in the image table.
- **The dynamic linker.** `/usr/lib/dyld` is on disk with N34-M's bytes (`373fce2b…`, 2,562,000 bytes). It
  is also in the image table.

**Unchanged since N34-M.** The cache file, dyld and both SystemVersion.plist files are byte-identical to
those that N34-M and the plan recorded, in the same boot session. HOST itself still records neither the
cache's identity nor dyld's (HR-05).

### 2.7 The capture records (question 7)

**The readback listing is the attempt as it now is.**
- **The listing.** My listing of `<attempt>` equals `observe-001.readback.json`'s exactly. It holds the root
  (`0o700`), the 2 stage directories (`0o700`) and 19 files, with the same kinds, sizes, modes and
  SHA-256 values.
- **The per-path record.** It covers exactly the 24 planned output paths: 19 present files, 2
  directories, and the 3 `failure.json` paths absent. All equal the files now.
- **The listing tool.** The listing was made by the bound `capture_probe.py` (`db5fb525…`), under
  `-I -S -B`, with no process event and no project file loaded, in the plan's boot.

**The probe shows both started processes absent by `ESRCH`.**
- **Absent.** For PID and group 7994 (Git) and 7995 (Node), both `kill(P, 0)` and `killpg(G, 0)` answered
  `ESRCH`. Both states are `absent`, and the record states FC-P5's descendant limit.
- **The pairs.** Each pair is the attempt's `intent.json` and `started.json`, whose recorded digests,
  sizes, modes and `mtime_ns` equal the files now. The recorded `argv0`, PID and group equal `started.json`.

**The order.** The listing (05:35:11.034Z to 05:35:11.071Z) was the first command after observe ended
(05:34:41.199Z), as FC-K5 requires. The probe followed (05:35:18.962Z to 05:35:18.998Z). Section 6
requires it only after an outcome other than a completed success, so here it was an addition.

**The command records hold what FC-K3 requires.** The four records are those of observe, the listing,
the probe and the hand-written static record. Each holds:
- **the command:** the exact argv, beginning `/usr/bin/env -i` with the five declared assignments, which
  equal the frozen environment file, then `<worktree>/.venv/bin/python -I -S -B`. The cwd is the evidence
  parent;
- **the environment:** `observe-001.environment.json`, canonical, 96 bytes. Its SHA-256 `0ed78f47…` is
  M0-LAUNCH's `environment_canonical_sha256`;
- **the times:** start and end in UTC, epoch start and end, and the wall time;
- **the boot:** before and after, both the plan's;
- **the outputs:** the exit status 0, which equals the exit file, the stdout and stderr streams with
  their digests and sizes, which equal the files, and 0 retries.

Each record's argv and window agree with what it records:
- **Observe's.** Its argv and cwd are exactly M0-LAUNCH's. Its window, 05:34:37.820261Z to
  05:34:41.198741Z (3.378480 s), holds the attempt directory's creation and HOST's observation.
- **The listing's and the probe's.** Each argv is that tool's recorded invocation, and each window holds
  the tool's own start and end.
- **All four.** The epoch start precedes the stdout file's creation, and the epoch end precedes the exit
  file's.

**The hand-written static record is faithful to the facts it cites** (HR-01).
- **Its times.** `start_epoch_s` and `end_epoch_s` equal, to the nanosecond, the birth times of the
  stdout file (05:32:56.252278032Z) and of the exit file (05:32:56.724821017Z).
- **Its streams and exit.** The digests and sizes are right, and the exit status is 0.
- **Its argv.** It is M0-LAUNCH's, with `static` in place of `observe`.
- **The run itself.** Static's stdout is byte-identical to W2's `static-001.stdout.txt` (`4e44510d…`). It
  reports `STATIC_READY`, zero starts and the facts digest `3867d3e8…`. The observer reaches that state
  only under `-I -S -B`, from the venv's launcher, in the declared environment, with the plan's digest.
- **Its wall time and boot readings.** It takes these from the wrapper's printed line, which is not kept
  as a file. They are consistent: the wall time 0.469473 s is 3.07 ms shorter than the birth interval
  0.472543 s, as the wrapper's order predicts. The boot is the plan's in every other record and now.
- **When it was written.** It was created at 05:33:41.580Z, after static and before observe.
  `run_once.sh` was last written at 05:32:35.679Z, before static. `run_once_v2.sh` was created at
  05:34:01.466Z, after static and before observe.

**Keeping the empty first record is right under FC-K1.** `observe-001.static.command.json` is 0 bytes, mode
`0o644`, created at 05:32:56.751860636Z. That is 27 ms after the exit file, by the first wrapper's
noclobber redirect before its `jq` call failed.
- **Why it stays.** FC-K1 forbids deleting, editing, re-creating or repairing anything in the evidence
  parent.
- **Why a new name.** Writing the reconstruction to a different, absent name was the only way to add the
  record without breaking FC-K1.

**The evidence parent** holds exactly 21 entries, the attempt and its 20 sibling files, and nothing else.
The description of my check Q7-parent says "21 sibling records", but the list it compares is these 21
entries. Its ancestors keep the plan's device, inode and mode. The attempt holds no temporary publication file.
Its modes are:
- `0o700` for the directories;
- `0o600` for the observer's documents;
- `0o644` for the supervisor's six files, under the S4 umask `0o022`.

### 2.8 Anything else the freeze must know (question 8)

- **The `__CF_USER_TEXT_ENCODING` value.** It is `0x1F5:0x0:0x0`, built from the UID and an unbound file
  in the owner's home directory (HR-02).
- **The owner's launchd job (PR-03).** It is still running, and the inventory is still unchanged (HR-03).
- **HOST's finality.** It rests on `completion.json`. `result.json` inside the attempt says
  `PENDING_COMPLETION` by design (HR-04).
- **Recorded but not decided.**
  - the tree, which is a planned value, and HEAD's ref files;
  - the interpreter's `utf8_mode`;
  - the shared cache's identity;
  - Node's signature check, and its Mach-O flags and segments.

  This review settles the tree statically and records the cache facts. HR-05 also says which fields the
  provider re-checks.
- **The labels.** They are complete for contract section 10 and equal their bindings.
- **The claims.** They are the observer's four fixed texts, and the provider requires them byte for byte.
  They do not restate every section 10 limit that applies to M0 and M1 (HR-06).
- **M1's timing and the start-count evidence.** Node's first execution took 1.110 s. The count rests on
  the receipts, and the observer has no audit hook (HR-07).
- **The provider's HOST consumer** (`current_host_readback_v02.py`, `_verify_host` and `_cross_bindings`)
  re-checks:
  - the platform and OS identity in full, the kernel version string and the cryptex hops included;
  - the environment record through the observer's predicate;
  - the interpreter's implementation, version, build string, launcher and process image, and the inventory;
  - the lock and packages, the runtime in full, and the Git binding and version grammar;
  - both inspection receipts, and the labels;
  - `starts`, and `claims` byte for byte;
  - the source root, commit, tree and inventory, the observer, and the reader tree.

  Every value of HOST that it re-checks agrees with the host now.

## 3. Findings

All seven are nonmandatory. None prevents binding HOST as observed.

### HR-01 (nonmandatory): the static run's FC-K3 record is hand-written under a second name, and the wrappers are not bound

- **Location:**
  - `<local>/c271-p35/evidence/observe-001.static.command.json` (0 bytes) and
    `observe-001.static.command-record.json`;
  - `<local>/c271-p35/director/run/run_once.sh` and `run_once_v2.sh`;
  - FAILURE-CAPTURE FC-K1 and FC-K3.
- **Issue:**
  - **The first wrapper.** `run_once.sh` left an empty `.command.json` and still exited 0.
  - **What the hand record transcribes.** Its wall time and both boot readings come from the wrapper's
    printed terminal line, which is not retained.
  - **The UTC strings.** The second wrapper takes its UTC strings from `date` calls separate from its epoch
    readings, so they can differ by a second. The probe record ends at epoch 05:35:18.998Z but says
    `ended_at_utc` 05:35:19Z.
  - **No binding.** Neither wrapper is bound by a reviewed plan, although the records' shape depends on
    them.
- **Effect:**
  - **None on HOST.** The record is faithful to every fact that can be checked (section 2.7), and its
    transcribed values are corroborated.
  - **FC-K1.** Keeping the empty file is what FC-K1 requires.
- **Recommendation:**
  - **Name the right file.** The freeze, the audit and S9's portable copies name
    `observe-001.static.command-record.json` as the static run's FC-K3 record. They list the empty
    `.command.json` as retained unchanged, and say that the static record's wall time and boot readings are
    transcribed.
  - **Bind the wrapper.** If S7 uses a wrapper, the freeze binds it by path and SHA-256 (`run_once_v2.sh` is
    `3c24f923…`, 3,601 bytes) and treats its epoch fields as the authoritative times.

### HR-02 (nonmandatory): HOST's `__CF_USER_TEXT_ENCODING` value depends on an unbound file in the owner's home directory

- **Location:**
  - HOST `environment.cf_user_text_encoding`;
  - contract S10 and section 12;
  - MC30, MC31 and MC36; N-04.
- **Issue:**
  - **Its parts.** The value `0x1F5:0x0:0x0` is `0x` + the UID 501 in hex + `:` + the 7-byte content
    `0x0:0x0` of `<home>/.CFUserTextEncoding`. That file has mode `0o400` and SHA-256 `bd605d2e…`, and was
    last modified on 2026-02-15. The value is consistent with CoreFoundation building it from the UID and
    that file.
  - **Where the file is found.** The declared environment has no `HOME`, so the file is found through the
    user database.
  - **Reproducible.** My launch in the declared environment, and my own shell's environment, show the same
    value.
  - **Node's value is not observed.** M1 cannot show it.
- **Effect:**
  - **None on HOST.**
  - **A change would refuse every start.** Suppose the file changes before S7 or the cohort ends, for
    example through a language or region change by the owner, or the file vanishes. The value in a new
    process would then differ, and the probe's binding would refuse every positive start under MC31's rule.
    Only a new HOST would recover. This fails closed.
- **Recommendation:**
  - **Record the file.** The freeze records that file's SHA-256 as an unbound host fact.
  - **Keep the settings.** It asks that the owner's language and region settings stay unchanged until MH
    ends.
  - **Keep N-04's tie.** MC36 waits for a positive probe start that observed the variable with HOST's value.

### HR-03 (nonmandatory): PR-03's launchd job still runs on the bound interpreter

- **Location:** PLAN-REVIEW-001 PR-03 and its disposition; MH-PLAN sections 5 and 10 (N-09).
- **Issue:**
  - **The process.** It is PID 1304, whose parent is launchd (PID 1), started 2026-11-23T12:21:13.98Z and
    owned by the same user. It still runs `<framework>/Resources/Python.app/Contents/MacOS/Python`.
  - **What I read.** Only its image, parent, group and start time: not its arguments or environment.
- **Effect:**
  - **So far, none.** The installation inventory recomputed byte-identically after M0, and again in the
    final check (h06).
  - **The risk continues through S6 to S8.** If the job ever writes bytecode, the cohort's recheck refuses
    (MC32). This fails closed, but at the cost of a counted attempt.
- **Recommendation:**
  - **Restate it.** The freeze restates PR-03's disposition.
  - **Check before S7.** It makes the inventory recheck immediately before S7 a stated precondition.
  - **The owner's choice.** The owner may pause the job until MH ends.

### HR-04 (nonmandatory): HOST's finality rests on `completion.json`, not on `result.json`

- **Location:** `observe_host`; `<attempt>/result.json`, `completion.json` and `HOST.json`.
- **Issue:**
  - **`result.json` is written first.** It is written inside the attempt before the completion marker, with
    `state: PENDING_COMPLETION` and `evidence_finalized: false`. Only `completion.json` and observe's stdout
    say `OBSERVED_UNAPPROVED` and finalized.
  - **HOST's `starts` is a constant.** `host_document` writes it. The computed counts are checked only
    after HOST is published.
  - **In this run.** Every record agrees.
- **Effect:**
  - **None here.**
  - **A risk of misreading.** A reader of `result.json` alone could take a completed attempt for an
    unfinished one. A reader of HOST alone could miss a failure after its publication.
- **Recommendation:** The freeze binds HOST together with:
  - `completion.json`: `fd1a035065e758825ddff81671fec29380720ed03d20c9571a17d993089488fe`, 981 bytes;
  - `result.json`: `1b4cae0f80cce491b200b5a24a1b5a75660af7889bb7120e98cec0a7080b2e1d`, 2,621 bytes.

  It cites `completion.json`'s state.

### HR-05 (nonmandatory): what HOST records without deciding, and what its consumer re-checks

- **Location:** HOST `source`, `python.interpreter`, `runtime`, `labels.node`; N-02, N-03, D-02;
  `current_host_readback_v02.py` lines 487 to 713.
- **Issue:**
  - **`source.tree`.** It is a planned value (`tree_check`), which M0 does not verify. This review verified
    it statically (section 2.1).
  - **`source.head.files`.** It binds the loose ref file in `<common-dir>`, which Git maintenance in the
    main clone (`pack-refs`) could remove without changing commit C. The provider does not re-compare
    `head`: its source check is MC19's bound Git reads. So this matters only for a re-run of the observer.
  - **`python.interpreter.flags.utf8_mode`.** It is 0 only because `LC_ALL=C.UTF-8`. The same interpreter
    reports 1 under an unset or C locale. The provider does not compare flags.
  - **No cache identity.** HOST does not record the shared cache's identity, nor dyld's (N-03). This
    review's static values are:
    - the cache: `7a024959…`, UUID `F2E86C53-6052-388B-BA71-5A0C9B569413`;
    - dyld: `373fce2b…`.
  - **Recorded, not decided:**
    - `labels.node.signature_check` is `not_performed` (D-02);
    - `runtime.macho`'s flags, segments and code-signature range (N-02);
    - `platform.version`, which the provider compares in full.
- **Effect:** None. Every field agrees with the host now.
- **Recommendation:**
  - **Cite this review.** The freeze cites this review for commit C's tree, the index and the cache facts.
  - **Launch in the declared environment.** Any consumer that compares interpreter flags launches in the
    declared environment.
  - **HEAD's ref files.** No action is needed for the provider. A new attempt of `observe` would bind
    whatever ref files then exist.

### HR-06 (nonmandatory): HOST's four claims do not restate every limit that applies to M0 and M1

- **Location:** HOST `claims`; the observer's `CLAIMS`; contract sections 5, 7 and 10; FC-P5.
- **Issue:** The four fixed texts state the closure, Python, boot and status limits. They do not restate
  three others:
  - **Descendants.** The Darwin supervisor's descendant limit: orphans are re-parented to launchd, and no
    enforcement is claimed. The probe record states FC-P5.
  - **Durability.** HOST and its receipts were published with `fsync`, not `F_FULLFSYNC`.
  - **Git.** It is bound by bytes and a version grammar only. It is never parsed, and its system libraries
    are identified by OS build alone (E18, N-07).
- **Effect:** None. The provider requires exactly these four texts, so changing them is an implementation
  change.
- **Recommendation:** The freeze and the audit cite contract section 10 for the full list of what results
  built on HOST cannot support, and do not read `claims` as complete.

### HR-07 (nonmandatory): the start-count evidence is receipts and source; M1's first execution took 1.110 s

- **Location:**
  - `_run_start`;
  - the attempt's receipts;
  - MH-PLAN section 7 and P07 section 4;
  - PR-04.
- **Issue:**
  - **No audit hook.** The observer installs none (P07's attempt evidence), and its own PID is recorded
    nowhere. So the count `{node: 1, other: 1}` rests on the two receipts with positive PIDs, and on the
    source, which calls `run_process` exactly twice. Its other host reads are syscalls and ctypes calls.
  - **The PIDs.** The two are consecutive, 7994 and 7995. That is consistent with no other process creation
    on the host in the 0.75 s between the two forks, since XNU assigns PIDs in sequence.
  - **Node's time.** It took 1,109.748 ms, 37% of the 3,000 ms of work, against 6.654 ms for Git. This is
    consistent with PR-04's first-launch work.
- **Effect:** None on HOST. Every P07 rule is met, and both durations lie within the limits.
- **Recommendation:**
  - **The audit.** S8 states this basis for M0's and M1's counts.
  - **The freeze.** It may cite M1's duration as the only timing evidence for `bin/node` on this host so
    far.

## 4. Starts and conduct

**Allowed starts only.** These were:
- one shell for each of my Bash calls;
- read-only utilities in those shells: `grep`, `wc`, `head`, `ls`, `od` and `mkdir`;
- my own scripts under `<worktree>/.venv/bin/python -I -S -B`. Twice that launch was prefixed with
  `/usr/bin/env -i` and the declared five, which `env` executes in the same process.

**No forbidden start.** No Node, no Git of any kind, no `ldd`, `codesign`, `otool`, observer, MH tool or
wrapper started. No `python3` from `PATH` started. Every Python start carried `-B`.

| # | Call | Processes |
| ---: | --- | --- |
| 1 | `grep` the contract's headings, `wc` | shell, grep, wc |
| 2 | `grep` P07's headings, `ls` three record directories | shell, grep, ls |
| 3 | `grep` N34-M's findings | shell, grep, head |
| 4 | `ls -laR` the evidence, `ls` the worker and Director directories | shell, ls, ls |
| 5 | `od -c` six small stream and exit files | shell, od ×6 |
| 6 | `wc` and `grep` the observer's definitions | shell, wc, grep |
| 7 | `mkdir OUT/outputs`, then h00 | shell, mkdir, Python |
| 8 | h01 | shell, Python |
| 9 | `wc`, `grep` h01's output | shell, wc, grep |
| 10 | h02 | shell, Python |
| 11 | `grep` h02's output | shell, grep, grep, head |
| 12 | `grep` h02's output | shell, grep |
| 13 | h03 | shell, Python |
| 14 | `grep` h03's output | shell, grep |
| 15 | h04, run 1 (superseded) | shell, Python |
| 16 | `grep` h04's output | shell, grep, grep |
| 17 | h04, run 2 | shell, Python |
| 18 | `grep`, `wc` h04 run 2's output | shell, grep, wc |
| 19 | `grep` the source with an unquoted `--include=*.py`: the shell refused the glob | shell; the pipeline may also have forked up to three short-lived processes (a shell child stopped at the glob, `grep -v`, `head`) |
| 20 | the same, quoted | shell, grep, grep, head |
| 21 | `grep` the provider's HOST functions | shell, grep, head |
| 22 | `env -i` … h04b, run 1 (superseded) | shell, one env-then-Python process |
| 23 | `grep` h04b's output | shell, grep, grep |
| 24 | `env -i` … h04b, run 2 | shell, one env-then-Python process |
| 25 | h05, run 1: its own scan blocked the write (a false positive on `/Users/runner;`), nothing written | shell, Python |
| 26 | h05, run 2: the same block, printed with its context, nothing written | shell, Python |
| 27 | h05, run 3, which writes the JSON report | shell, Python |
| 28 | h06, the final check | shell, Python |

**Totals, rows 1 to 28.** There were 28 shells, 12 Python processes (two of them entered through `env`) and
35 utility processes: 75 in all, plus row 19's up to three.
- **The utilities:** 17 `grep`, 4 `wc`, 4 `head`, 3 `ls`, 6 `od` and 1 `mkdir`.
- **Recorded PIDs.** Each Python process recorded its PID and its shell's PID in its output.

**Limits of this count.**
- **The harness.** Each shell is started by the agent harness, which evaluates my command inside it after
  its own set-up. Whatever that set-up runs is outside my view.
- **The file tools.** The file-read, file-write and edit tools start no host process that I can observe.
- **The Git summary.** The harness attached a Git status summary of the main clone to my initial context.
  No command of mine produced it.

**Nothing of mine remains.** Every start ran in the foreground, and its shell waited for it. The final
check (h06) asks `kill(pid, 0)` for every recorded PID and parent PID of mine, and records the answers.

**Nothing else changed.**
- **The worktree.** I made no edit in `<worktree>`. At h03, every tracked file equalled its index blob, and
  no bytecode existed outside `.venv`. h06 repeats the source inventory and the Python inventory.
- **The evidence.** I made no change to the evidence: the readback listing still equals the attempt, and
  the parent holds exactly its 21 entries.
- **Under `<local>`.** I wrote nothing outside OUT.
- **Downloads, installs and Finder.** I downloaded and installed nothing, and used no Finder.

## 5. Files

**The documents of the run**, under `<local>/c271-p35/evidence/`:

| File | SHA-256 | Bytes |
| --- | --- | ---: |
| `observe-001/HOST.json` | `34e94f29ea1b7d9d60b389598b4ce5bc7eaf6fcaa58f3798fc3df021a8f28a92` | 18,420 |
| `observe-001/result.json` | `1b4cae0f80cce491b200b5a24a1b5a75660af7889bb7120e98cec0a7080b2e1d` | 2,621 |
| `observe-001/completion.json` | `fd1a035065e758825ddff81671fec29380720ed03d20c9571a17d993089488fe` | 981 |
| `observe-001/preflight.json` | `bc3feb604d7d23f785a68e6a3bdcf790f2125af33de5c5af09cec48455679cdb` | 586 |
| `observe-001/reserved.json` | `b5129461fbdbb646dee2d1c042ff16c110d31e43ec38876a1b0ce74064874bce` | 785 |
| `observe-001/git_version/inspection.json` | `d736f86f077169cc9d4b6420b4e831761b49859c805f793c119acc7afb248f21` | 1,441 |
| `observe-001/node_version/inspection.json` | `7a1095fa906166c80c8df2453211134e6489b048f1e0baccbe09df6401efb222` | 1,163 |
| `observe-001.readback.json` | listed in the JSON form | 18,288 |
| `observe-001.probes.json` | listed in the JSON form | 5,299 |

**The full list.** The JSON form lists every file I reviewed with its SHA-256, size and mode, computed by
h05:
- every file of the attempt and of the evidence parent;
- the plan, its inventories, M0-LAUNCH.json and W2's static output;
- the plan review and its disposition, and the wrappers;
- the documents read and the observer and supervisor sources;
- every bound input that I recomputed.

The same list holds my scripts and outputs.
