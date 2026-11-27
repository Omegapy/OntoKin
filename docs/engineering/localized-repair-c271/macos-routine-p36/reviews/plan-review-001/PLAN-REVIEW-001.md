# Plan review 001: observation plan 001 for M0 and M1 at commit B

## Verdict

**ACCEPT_WITH_NONMANDATORY_FINDINGS.** There is no mandatory finding.

**The plan's SHA-256, computed by my own code from the file's bytes:**
`cc1c2defd73d8d1ade22a8c772308c0e3d2fad3262a83c946c1733aecf429d5e`. The file is
`<local>/c271-p36/workers/W2-plan-001/observation-plan-001.json`: 9,017 bytes, mode `0o644`, one
link, canonical JSON. The Director passes this digest as the last argument of `static` and
`observe`.

**My recomputed inventory digests, each byte-identical to W2's file and to MH's:**

| Inventory | SHA-256 | Canonical bytes |
| --- | --- | ---: |
| Python installation | `c277bdd3ac6aa73105df3924707a271a402a0dc7c722be27a6834f2c78605633` | 776,209 |
| Source of B | `95abd300edbb9930e67c569b726015964ab98f4ed0ede389da122bbb3f145c4c` | 96,238 |
| Dependencies | `3545d5f920ac840804a9e25d28a87d623f96af71537fd3f020a0c1d743f82fb4` | 4,543 |

- **Every key of the plan equals the actual state.** My checks: 33 in s02, 9 in s01, 7 in s04, 3 in
  s06 and 8 in s07, all passed, with final rechecks up to 19:40:47Z.
- **The Python inventory needs no explanation.** My own walker, link resolver, Mach-O parser, closure
  and package check give the frozen bytes, so every file, link, directory, image, external library,
  link hop and selection key equals MH's. I computed it four times, the last at 19:40:47Z.
- **Git's files agree with commit B.** Read without Git, HEAD is B, B names tree `0935162c…`, and the
  worktree and the index equal that tree.
- **The launch record is exact.** M0-LAUNCH.json gives W3-OBSERVER section 1's launch from `env -i`
  with the five declared variables, and leaves the digest as the one final argument.
- **The differences from MH's plan are exactly the ones W2 reports.** 37 leaves differ: the commit,
  the tree, three inventory paths, the evidence paths, and the paths and inodes of two ancestors.
- **Six nonmandatory findings.** The ones the Director should act on before S5:
  - **PR-01 (Q-1):** record how MR reads FAILURE-CAPTURE's MH paths, and name the exact readback
    paths.
  - **PR-02:** another agent application on this host starts the bound interpreter. The runs I could
    inspect carried `-B`.
  - **PR-03:** guard the digest variable in the shell forms.

## Context

| | |
| --- | --- |
| Reviewer | W3, the reviewer of plan review 001 of gate MR: a Claude Code subagent in a fresh context, with no earlier review in it. I wrote none of the plan, its inventories, the launch record, the observer, the supervisor, the contract, the amendment, MP's preparation, MH's records or MR's tooling. |
| Gate and stage | gate MR, phase `C271-P36-macos-complete-routine-mr`, stage S4, Director `c271-p36-14f7f8b219db`, local mode |
| Under review | W2's observation plan 001 and its companions in `<local>/c271-p36/workers/W2-plan-001/`, whose 60 listed digests all verify, with no unlisted file |
| Commit B | `4ca781429c5411c67c0965bc69306b42c6cc74ad`, tree `0935162c72fd9d804681e920da6f6d6e9066ff28` |
| Host | macOS 26.6.2 (25G83), Darwin 25.6.0, arm64, boot `C90010BA-4DA9-475D-BBAB-CF1A9C40175A`, the same boot as MH's |
| Written | 2026-11-27, after the final recheck at 19:40:47Z |

Places are named by labels:

- `<worktree>` is the C271 worktree at commit B.
- `<clone>` is the main clone. `<clone>/.git` is the common Git directory, which `<worktree>/.git`
  names through `<clone>/.git/worktrees/c271`.
- `<local>` is the working directory beside the clone, and `<local>/..` holds both.
- `<volume>` is the mount point of the external volume that holds all three.
- `<prefix>` is the installation prefix of the interpreter's framework and of its non-system
  libraries. `<package-manager>` is the package manager that owns it.
- `<framework>` is `<prefix>/Cellar/python@3.12/3.12.13/Frameworks/Python.framework/Versions/3.12`.
- `OUT` is `<local>/c271-p36/workers/W3-plan-001/`, the only place I wrote.

The machine-readable form is [PLAN-REVIEW-001.json](PLAN-REVIEW-001.json).

## 1. Method

**Reads.** I read these with the agent's file-read tool:

- `<worktree>`'s AGENTS.md and ROLE.md, PROTOCOL sections 4 and 5, and the worker template;
- MR-PLAN.md (all of it, sections 2, 3, 6, 8, 9 and 12 closely), PHASE.json and
  START-INVENTORY-DISPOSITION.json;
- CONTRACT.md sections 4 and 7, AMENDMENT-001.md and its adoption record;
- W3-OBSERVER.md (all of it) and the observer's source: its constants, paths, reads, environment,
  platform, Mach-O, trees, Python inventory, packages, launcher, loaded modules, source, Git,
  dependency, runtime and receipt checks, the plan rules, the evidence store, the start, `static`,
  `observe` and `main`;
- both supervisor files;
- FAILURE-CAPTURE.md, and the parts of `capture_probe.py` that govern its paths;
- MR's tooling README (its reuse table);
- MH's plan review 001 and its disposition, MH's HOST disposition and command record, and MH's two
  inspection receipts, as data;
- W2's notes, M0-LAUNCH.json, start log, `static` result and scripts.

**My scripts** are in `OUT/scripts/`, and their outputs in `OUT/outputs/`.

- **What they import.** Each uses the standard library and my own `w3_common.py`, nothing of the
  project, and runs as `python3 -I -S -B`.
- **Their paths.** Each refuses to run without those flags and holds no machine path: every path is
  an argument.
- **Their outputs.** Each writes one absent output by exclusive creation, with every machine place
  replaced by its label.
- **The audit hook.** Each installs one that refuses process creation and ctypes process lookups.
  No event was recorded.

| Script | What it does |
| --- | --- |
| `w3_show_plan.py` | Digests the plan, tests its canonical form, and writes an indented reading copy |
| `s01_files.py` | Verifies W2's 60 digests and that no other file exists; compares W2's plan and inventories with MH's exact files; checks that the evidence parent is empty and the attempt and capture paths absent |
| `s02_plan_keys.py` | Every key: form, constants, environment, limits, platform and boot, OS identity, source, observer, Python, runtime with my Mach-O parser and my receipt rule, the reader tree, Git, commands, evidence, failure capture, canonical paths, the leaf-by-leaf difference from MH's plan, and M0-LAUNCH.json and M0-ENVIRONMENT.json. My constants come from the documents. The observer's own constants are evaluated from its source with `ast`, without running it, and compared with mine. |
| `s03_python_inventory.py` | Recomputes the Python inventory from W3-OBSERVER section 5, applies section 6.3's rules to every image, and verifies the packages against the lock |
| `s04_source_and_git.py` | Recomputes the source inventory. Then it reads HEAD, commit B, the pack, the tree, the worktree, the index, the chain back to MH's commit C and named blobs, all without Git. |
| `s05_git_static.py` | Reads the bound Git's fat header and both slices, and its embedded version text |
| `s06_imports_static.py` | Lists, with `ast`, the modules that `observe`'s loaded-module check will see, and locates each in the frozen inventory |
| `s07_final_recheck.py` | Builds the dependency inventory as a document, and rechecks the plan, W2's files, the evidence parent and the boot |
| `s08_report_check.py` | Run after these records. It parses the JSON record, checks the digest and verdict in both records, scans OUT for private terms, and writes `SHA256SUMS.txt` |

## 2. Every key of the plan (question 1)

**Form (K-01, K-02).**

- The plan is canonical JSON: sorted keys, compact separators, ASCII, and no trailing newline.
- It has no duplicate member, float, non-finite constant or null.
- No value or key holds `TODO`, `TBD`, `FIXME`, `XXX`, a wildcard, a shell character or a backtick,
  and no digest is one repeated digit.
- The 17 top-level keys are exactly the schema's.
- All 55 absolute paths are canonical (K-30). A path inside the absent attempt counts as canonical
  when the attempt itself is canonical with an absent last component.

| Key | Plan value | My reading |
| --- | --- | --- |
| `schema`, `contract`, `profile`, `executor` | `…observation-plan/0.2.0`, `ontokin.current-host-readback/0.2.0`, `darwin-arm64-v1`, `macos-arm64-local` | Equal to W3-OBSERVER section 2. They also equal the observer's constants at lines 57-69, evaluated statically (K-03, K-05). |
| `environment` | `PATH=/usr/bin:/bin`, `LANG=C.UTF-8`, `LC_ALL=C.UTF-8`, `TZ=UTC`, `UV_THREADPOOL_SIZE=2` | Exactly these five (K-04), the observer's lines 102-103 |
| `limits` | 15 values | Equal to my values and to the observer's `LIMITS`, lines 127-131 (K-05) |
| `platform` | Darwin, `25.6.0`, arm64, 0, boot `C90010BA-…175A` | `os.uname()`, and `sysctlbyname` and `sysctl -n` now. These are the actual release and this boot (K-06). |
| `os.system_version` | the canonical SystemVersion.plist, `6151cb88…04a1`, 603, `0o444` | Rehashed. It reads macOS 26.6.2, 25G83, which equals `kern.osversion`, with no `ProductVersionExtra` (K-07). |
| `os.cryptex` | present, `/System/Volumes/Preboot/Cryptexes/OS/…/SystemVersion.plist`, the same bytes | My resolver takes one hop, `/System/Cryptexes/OS` → `../../System/Volumes/Preboot/Cryptexes/OS`, to the plan's canonical path. Rehashed (K-08). |
| `source.root`, `commit`, `tree` | `<worktree>`, B, `0935162c…` | Section 3 of this record (K-09). |
| `source.inventory` | W2's file, `95abd300…` | Rehashed, and recomputed byte-identically (K-10, G-01) |
| `observer` | `<worktree>/prototypes/static_tray_v01/current_host_observation_v02.py`, `471a9547…2788`, 162,557, `0o644` | Rehashed. It equals the source inventory's entry and its blob `e59d6292…`, which is the same at B and at C (K-11, G-07). |
| `python` | `<worktree>/.venv`, `<framework>`, `3.12.13`, W2's file `c277bdd3…` | Both paths are canonical. The version is pyvenv.cfg's and my interpreter's. The inventory recomputes byte-identically (K-12; s03). |
| `runtime.directory`, `version`, modes | `<local>/c271-macos/node-v24.22.1-darwin-arm64`, `v24.22.1`, `0o755`, `0o755` | The directory holds exactly `{bin/, bin/node, NODE-SOURCE.json}`, single-link files, no link or `.DS_Store`; the modes come from lstat (K-13, K-14). |
| `runtime.executable` | `6f320694…f329`, 122,545,856, `0o755` | Rehashed. My parser applies W3-OBSERVER section 6.2: thin `MH_MAGIC_64`, cputype `0x0100000c`, subtype 0, `MH_EXECUTE`, and 21 commands, all in the closed list of 16. It finds one `/usr/lib/dyld`, one `LC_MAIN`, no duplicate, and four system dylibs: CoreFoundation, Security, `libc++` and `libSystem` (K-15, K-16). |
| `runtime.node_source` | `e928a8ec…ea2c`, 976, `0o644` | Rehashed. It is canonical with its seven keys: the pinned archive, the checksum-file identity, a recorded `not_performed` signature status, and the executable's binding (K-17). |
| `runtime.archive` | `<local>/c271-p34/downloads/node/node-v24.22.1-darwin-arm64.tar.gz`, `89c68259…c0a7`, 53,062,778, `0o444` | Rehashed; the contract's pin (CONTRACT.md line 109) (K-18) |
| `runtime.install` | MP's exact plan `1fee042d…` and receipt `65caf77a…` | Rehashed and listed in MP's sums. My receipt rule (W3-OBSERVER section 3) passes: `INSTALLED_EXACT`, 5,888 members with digest `0b2b6072…`, equal to NODE-SOURCE.json's, whose signature record is the plan's `node_source` (K-19). |
| `dependencies.root` | `<local>/c271-macos/reader-c195` | Canonical: 24 single-link files and 13 directories, with no link, special file or `.DS_Store` (K-20) |
| `dependencies.inventory` | W2's file, `3545d5f9…` | The files equal the installed tree and the C199 pins of EXTERNAL-INPUTS.json (`21fd6bad…`). The directories are exact and necessary. The archive is the contract's pin `b1e54a6c…a0c9`, and the versions are `2.0.0-dev.3.10` and `0.186.1`. Rebuilt byte-identically (K-21, R-01). |
| `dependencies.install` | MP's exact plan `ff5a95da…` and receipt `03222a85…` | Rehashed and listed. My receipt rule passes: `INSTALLED_EXACT`, 730 members with digest `72dc3175…`, and `node_source` null (K-22). |
| `git` | `/Library/Developer/CommandLineTools/usr/bin/git`, `be4afb2b…bcae`, 7,604,272, `0o755` | Rehashed. It is N34-M's file (N34-M-REVIEW.md line 317): canonical, no link, not `/usr/bin/git`, neither its hard link nor its bytes (K-23). |
| `commands` | `git_version`, then `node_version` | Built from W3-OBSERVER section 2's table, and equal (K-24). Each has its argv and cwd `<attempt>/<id>`, its label and its environment: the five, plus the six `GIT_*` variables for Git. Each has 5,000, 3,000 and 2,000 ms, one expected start, its stdout predicate and an empty stderr predicate. |
| `evidence.parent` | `<local>/c271-p36/evidence` | Canonical, a directory, and empty at every check, the last at 19:39:04Z (K-25, F-07, R-05) |
| `evidence.ancestors` | seven rows | Equal to my lstat walk, with no link (K-26). See the table below. |
| `evidence.attempt`, `outputs` | `<local>/c271-p36/evidence/observe-001`, the fixed topology | An absent direct child, and the outputs equal (K-27). The six capture paths and the two suggested command records are absent too (F-09). |
| (roots) | | The parent overlaps no bound root, and the bound roots are disjoint (K-29). |
| `failure_capture.procedure` | `<worktree>/…/macos-qualification-p35/tooling/FAILURE-CAPTURE.md`, `f387fb3e…c99c`, 13,147, `0o644` | Rehashed. It equals MH's tooling sums and MR's tooling README line 399, is outside the attempt, and its blob `6ce5a793…` is the same at B and C (K-28, G-07). See PR-01. |

**The evidence ancestors**, sorted by path:

| Path | Device | Inode | Mode |
| --- | ---: | ---: | --- |
| `/` | 16777234 | 2 | `0o755` |
| `/Volumes` | 16777234 | 18343 | `0o755` |
| `<volume>` | 16777244 | 2 | `0o775` |
| `<local>/..` | 16777244 | 7019967 | `0o755` |
| `<local>` | 16777244 | 14022344 | `0o755` |
| `<local>/c271-p36` | 16777244 | 16455187 | `0o755` |
| `<local>/c271-p36/evidence` | 16777244 | 16455190 | `0o755` |

The volume is APFS, local, `nodev`, `nosuid`, journaled and `noowners`, not `noexec`. `bin/node` has
only the `com.apple.provenance` attribute.

## 3. The inventories, B, its tree and the index

**The Python installation inventory.** s03 recomputes it with my own code: `c277bdd3…`, 776,209
bytes, byte-identical to W2's file and to MH's.

- **The framework:** 3,478 files, 414 of them bytecode in 37 `__pycache__` directories, 5 links and
  305 directories, 72,433,430 bytes.
- **The `.venv`:** 297 files with no bytecode, 3 links and 45 directories, 13,983,870 bytes.
- **The images:** 111 in all. The framework holds 2 `MH_EXECUTE`, 1 `MH_DYLIB` and 76 `MH_BUNDLE`. The
  `.venv` holds 19 `MH_DYLIB` and 8 `MH_BUNDLE`. Five external dylibs lie under `<prefix>/Cellar`.
- **The closure:** 6 link hops, 81 `LC_RPATH` entries, 26 `@loader_path` references and 127 system
  references, stable after 2 passes.
- **The selection chain:** 4 hops.
- **The packages:** the seven pins of the lock, which equal the contract's. Their hashed RECORD rows
  number Pillow 139, attrs 36, jsonschema 45, jsonschema-specifications 29, referencing 20, rpds-py
  10 and typing_extensions 6. No file is unowned.

There is no difference to explain. W2's file equals MH's byte for byte, and my recomputation, done
at 19:22:45Z, 19:32:38Z, 19:38:59Z and 19:40:47Z, equals both.

**The source inventory.** It has 644 files, 13,588,394 bytes, `95abd300…`, and is byte-identical.

- The four supervisor files are in it.
- No link, `.DS_Store`, `__pycache__`, bytecode or multi-link file exists in its trees.

**The dependency inventory.** s07 builds the document from the installed tree and the retained C195
archive: `3545d5f9…`, byte-identical (section 2).

**HEAD, from Git's files without a Git start.**

- `<worktree>/.git` names `<clone>/.git/worktrees/c271`, and `commondir` is `../..`.
- `HEAD` is `ref: refs/heads/work/c271-missing-import-digest-control`.
- The ref is a loose file of the common directory, and it holds B. There is no per-worktree ref and
  no `packed-refs` entry.
- The backlink names `<worktree>/.git`, and there are no alternates.

**Commit B.** It is a loose object whose name recomputes from its bytes.

- It names tree `0935162c…` and one parent, `d3b622d6…`.
- It is unsigned and was committed at 2026-11-27T18:40:35Z.

**The pack.** It has 27,674 objects. Its version-2 index checksum is valid, its trailer equals the
index's pack checksum, and the SHA-1 of its content equals the trailer.

**The tree.** It has 2,655 trees and 23,012 entries: 23,004 `100644`, 2 `100755` and 6 links. Every
blob is in the store.

**The worktree.** Apart from `.git` and `.venv` at its root, it holds 23,012 entries, 6 of them links,
in 2,654 directories.

- Each equals its tree entry by blob and mode.
- Nothing is missing, extra or changed.
- There is no untracked directory, special file, multi-link file, bytecode or `.DS_Store`.

**The index.**

- It is version 2 with 23,012 entries, and its checksum is valid.
- It equals the tree by path, mode and blob, and its cached sizes equal the files.
- It has no conflict stage, assume-valid, skip-worktree or intent-to-add entry.
- Its `TREE` extension's root is `0935162c…`. It also has a 516-byte `REUC` extension, which records
  earlier conflict resolutions; M0 never reads the index.

**From C to B.** The first-parent chain is B, `d3b622d6`, `47cc579f` and `2cd69829`, then MH's C
(`0eb9a551…`, tree `ea10cd94…`).

- The trees differ in 528 paths: 522 added, 6 changed, none removed.
- All of them lie under `docs/`: 472 under `macos-qualification-p35/`, 49 under `macos-routine-p36/`,
  and 7 under `docs/workflow/`.
- None is in the observer's source set.

The second run, at 19:39:04Z, gave the same result.

**N-07, the bound Git.** I read the file statically, in s05. It is fat, with an x86_64 slice (subtype
3) and an arm64 slice (subtype 0).

- Each slice is `MH_EXECUTE` with 22 commands, `/usr/lib/dyld`, no `LC_RPATH` and no unknown command.
- Each links CoreServices, libz, libiconv, libSystem and CoreFoundation.
- Each is built for minimum OS 14.0 with SDK 26.4, and has no arm64e slice.
- Each embeds the format `git version %s\n` once and the text `2.50.1 (Apple Git-155)`. So the arm64
  slice would print `git version 2.50.1 (Apple Git-155)\n`, which fits `git-version-line-v1`, as at
  MH.

## 4. M0-LAUNCH.json and M0-ENVIRONMENT.json (question 2)

**The launch is exact (K-32).**

- **The command.** `argv_without_digest`, followed by the digest of this record, gives
  `/usr/bin/env -i PATH=/usr/bin:/bin LANG=C.UTF-8 LC_ALL=C.UTF-8 TZ=UTC UV_THREADPOOL_SIZE=2 <worktree>/.venv/bin/python -I -S -B <worktree>/prototypes/static_tray_v01/current_host_observation_v02.py observe --plan <local>/c271-p36/workers/W2-plan-001/observation-plan-001.json --plan-sha256 cc1c2defd73d8d1ade22a8c772308c0e3d2fad3262a83c946c1733aecf429d5e`.
- **The rules it meets.** These are W3-OBSERVER section 1's launch and the observer's launcher rules
  (lines 1477-1493).
  - `env -i` leaves exactly the declared five variables and executes the `.venv` launcher in the same
    process, so `sys.executable` is `<venv>/bin/python`.
  - The flags are `-I -S -B`.
  - The digest comes only as the final argument, from outside the plan.
- **`static`.** It is the same with `static` in place of `observe`.
- **The record carries no plan digest.** `observer_process_argv_without_digest` is the argv after
  `env`'s words.

**The cwd and capture paths.**

- The cwd is the evidence parent, which exists and is canonical.
- The six capture paths, `observe-001.{static,observe}.{stdout,stderr,exit}.txt`, are fresh, absent,
  distinct siblings of the attempt, outside it and distinct from the two suggested FC-K3 records.
- The shell forms have the same words as the argv, and none of them needs quoting.

**The expectations (K-33).**

- The expected starts are the plan's two commands in order through
  `supervisor_darwin_v01.run_process`, with totals node 1 and other 1.
- The success outputs are the 19 planned files without the three `failure.json` files, and the three
  `0o700` directories.
- The predicted Git line fits the grammar.
- M0-ENVIRONMENT.json is the canonical declared environment: 96 bytes, `0ed78f47…`.

**Nothing else would be started.**

- The shell's `cd` and `echo` are built-ins, and `env` executes the interpreter in its own process.
- In the observer, the only start route is `supervisor.run_process` (line 2533). It is called once for
  each of the two commands (lines 2696-2706), with no retry.
- `run_process` makes one `subprocess.Popen` (supervisor_darwin_v01.py lines 155-156).
- `git --version` and `node --version` start no descendant. MH found both groups absent at exit.

## 5. Differences from MH's plan (question 4)

**Confirmed.** My leaf-by-leaf comparison with MH's exact plan (`b8cd6449…`, 9,017 bytes) finds the
same size and the same leaves, and 37 leaves that differ, each explained:

- `/source/commit` and `/source/tree`: C and `ea10cd94…` become B and `0935162c…`.
- `/source/inventory/path`, `/python/inventory/path` and `/dependencies/inventory/path`: MH's W2
  directory becomes MR's. Their digests, sizes and modes are unchanged.
- `/evidence/parent`, `/evidence/attempt`, the 24 leaves of `/evidence/outputs`, and the two commands'
  `cwd`: `<local>/c271-p35/evidence` becomes `<local>/c271-p36/evidence`.
- `/evidence/ancestors/5` and `/6`: the paths of `<local>/c271-p36` and its `evidence`, with inodes
  16455187 and 16455190 in place of 15728058 and 15728417. Their devices and modes are unchanged.

Nothing else differs. That includes the boot, which is still MH's and is this boot.

## 6. W2's open questions (question 3)

**Q-1. FAILURE-CAPTURE's literal phase paths.** Reading them as MR's evidence parent is sound for M0
and M1, on PR-01's conditions.

- **Why it is sound.** The observer binds the procedure by its bytes only (lines 2253-2254) and never
  reads its text. `capture_probe.py` names no phase path: it writes any absent canonical path in an
  existing canonical directory (lines 107-124 and 199-205).
- **Where MR's records go.** MR's FC-K5 readback and any capture record belong in
  `<local>/c271-p36/evidence/`, as fresh absent siblings of the attempt, never inside it. MR-PLAN
  section 6 puts MR's evidence there and keeps MH's exact records unchanged, so nothing may be
  written under `<local>/c271-p35/`.
- **What the Director records first.** Before S5, the Director records this reading, with
  "MH-PLAN section 8" read as "MR-PLAN section 9" and the schema name kept, and names the exact paths.

**Q-2. The launch without the digest.** Yes; see section 4. The one final argument is
`cc1c2defd73d8d1ade22a8c772308c0e3d2fad3262a83c946c1733aecf429d5e`, from this record. PR-03 adds a
guard.

**Q-3. The scripts' interpreter.** Confirmed.

- **The same interpreter.** `python3` on the session's `PATH` resolves through
  `<prefix>/opt/python@3.12` and `libexec/bin/python3` to `<framework>/bin/python3.12`. That is the
  same launcher and `Python.app` image as the `.venv`'s.
- **The rules it meets.** MR-PLAN section 3 allows W2 its own scripts under `-I -S -B`. Section 6
  requires `-B` for every start of that interpreter, whatever its name.
- **No write followed.** I ran mine the same way. My four byte-identical inventory recomputations show
  that no start of W2's or mine added a file.

**Q-4. MH's PR-03.** The job still runs.

- It is PID 1304, under launchd since 2026-11-23T12:21:13Z, running the bound `Python.app` image
  with another project's watcher script. Its argv has no `-B`. This is the process of MH's PR-03.
- I did not read its environment.
- The inventory stayed byte-identical at each of my four recomputations.

A further user of the interpreter appeared during this review (PR-02).

**Q-5. MH's PR-02.** Agree. MH's M0 observed both stderr streams empty for the same bytes and
environments, which is one observation. A refusal for a non-empty stderr cannot be corrected by a plan,
so under MR-PLAN section 9 MR stops. The Director adopts the classification again before the run
(PR-05).

**Q-6. MH's PR-01.** Agree.

- **The binding, read from Git's files.** The adoption record's blob is `0431fab5…` at B and at C,
  and the worktree file equals it: SHA-256 `872312ed…7937`, 5,396 bytes, `0o644`, one link.
- **No effect on M0 and M1.** Neither reads it. The S6 configuration binds its bytes (PR-06).

**Q-7. Facts that change without a file edit.** Agree that a reboot and a remount fail closed before
any start. More such facts:

- **A package-manager operation on `<prefix>`.** It fails closed before any start, because the
  selection chain, the closure's hops and the external libraries are bound.
- **Another session's interpreter start without `-B`** (PR-02).
- **The language and region settings.** M0 admits their CoreFoundation value and records it, but the
  plan does not bind it. Only `static`'s `facts_sha256` can show a change before `observe` (PR-04).
- **A remount with `noexec`.** M1's exec of `bin/node` would then fail, with an `UNKNOWN` start
  count.
- **Sleep, or unmounting the volume, during `observe`.**

**Q-8. The cwd and the capture paths.** Accepted.

- With `-I` the cwd is not on `sys.path`, the observer resolves no path against it, and each child
  runs in its own stage.
- Creating the capture files changes neither the parent's device, inode and mode, which are all
  that `_ancestors` compares (lines 1983-1993 and 2364-2365), nor the attempt's absence.

## 7. What could make M0 or M1 refuse, or start more than one Git and one Node (question 5)

**In the plan and the launch record: nothing.** No key would make `static` or `observe` refuse on the
present state.

**The loaded-module check** that only `observe` makes, after the supervisor import, passes on the
present state (s06).

- Every standard-library module on the path to it is a frozen framework file or built in, and any of
  their bytecode that exists is inventoried.
- The only project modules are the four supervisor files.
- No bytecode or `__pycache__` exists under `prototypes/`.
- No entry of the worktree root shadows a standard module while the root is on `sys.path` for the
  import.

**The start count.** It is exactly one Git and one Node start (section 4). `ldd`, `codesign`,
`otool`, `/usr/bin/git` and any other Node are never started.

**Host conditions that fail closed**, with no plan change:

- **Before any start:**
  - a reboot or remount;
  - a file added to the framework tree or the `.venv` before `observe`'s static phase (PR-02);
  - a package-manager change;
  - a Git write that moves the ref or touches the source set;
  - a change of any bound file;
  - a umask that clears owner bits (this shell's is `022`);
  - an unset or mistyped digest (PR-03).
- **After a counted start:**
  - a file added between `observe`'s rechecks, refused with `DRIFT`;
  - a non-empty stderr (PR-05);
  - `noexec`, with an `UNKNOWN` count.

## 8. Findings

All six are nonmandatory. None holds `observe`.

### PR-01 (nonmandatory): FAILURE-CAPTURE names MH's evidence parent and MH-PLAN

- **Location:**
  - FAILURE-CAPTURE.md lines 83-93 (FC-K5's readback "under `<local>/c271-p35/evidence/`"), 167 and
    183 (MH-PLAN section 8), and 195-199 (the schema);
  - MR-PLAN.md line 160 and lines 187-196;
  - the plan's `/failure_capture/procedure`;
  - M0-LAUNCH.json `/fc_k3` and `/expected_outputs/refusal_or_failure/then`;
  - PLAN-AUTHOR-NOTES.md lines 362-367.
- **Statement:**
  - The bound procedure, reused unchanged, places FC-K5's readback in MH's evidence parent, and it
    refers to MH-PLAN section 8 after a refusal.
  - The observer binds only its bytes, so M0 and M1 do not depend on this wording, and
    `capture_probe.py` accepts any absent canonical path.
  - Read literally, FC-K5 would put MR's readback into MH's evidence parent, which MR-PLAN section 6
    keeps unchanged.
- **Required change (before S5, in the plan-review disposition; the plan and its digest stay
  unchanged):**
  - **The paths.** `<local>/c271-p35/evidence/` reads `<local>/c271-p36/evidence/`.
  - **The references.** "MH-PLAN section 8" reads "MR-PLAN section 9", and "an MH plan" and "MH
    tool" include MR's plans and the reused tools.
  - **The record and its tool.** The capture record keeps the schema
    `ontokin.c271.p35-failure-capture/1`. `capture_probe.py` runs from its committed path under its
    bound SHA-256 `db5fb525…048f`.
  - **The names.** The Director names the fresh absent paths of the FC-K5 readback, with its command
    record and streams, and of FC-P3's probe record if one is made. They are siblings of the attempt,
    distinct from M0-LAUNCH.json's six capture paths and two command records.
  - **Nothing is written under `<local>/c271-p35/`.**

### PR-02 (nonmandatory): another agent application on this host starts the bound interpreter

- **Location:**
  - MR-PLAN.md lines 174-178, whose `-B` rule includes other sessions on this host;
  - M0-LAUNCH.json `/preconditions_for_the_director/3`;
  - MH's PR-03.
- **Statement:**
  - **Who.** An agent application other than this Claude Code session runs on this host. Its
    controlling process has run since 2026-11-26T00:30:42Z.
  - **What it started.** Three times during this review, it started the bound framework image, each
    time a parent and a child:
    - at 19:31:28Z, still present at 19:32:09Z and gone moments later;
    - at 19:37:20Z, gone by 19:39:04Z;
    - at 19:39:18Z, still running at 19:40:54Z.
  - **What I saw of them.** For the second and third pairs, both argvs carried `-B` and named nothing
    of this project. The first pair ended before I read its argv, and I read no environment.
  - **The effect so far.** The Python inventory stayed byte-identical throughout.
  - **The limit.** The Director cannot enforce MR-PLAN section 6 on that application.
- **Required change:**
  - None in the plan.
  - The Director records it, and asks the owner to keep that application from starting the framework
    interpreter without `-B`, or to pause it, from S5 to the end of S8.
  - `static` immediately before `observe` detects an added file before any start. A file added
    between `observe`'s rechecks refuses with `DRIFT`, after a counted start.

### PR-03 (nonmandatory): the digest variable in the shell forms is unguarded

- **Location:**
  - M0-LAUNCH.json `/observe/shell_form`, `/static_before_observe/shell_form` and
    `/observe/shell_form_variable`;
  - FAILURE-CAPTURE.md lines 161-168 (FC-R2 and FC-R3);
  - the plan's `/evidence/attempt`.
- **Statement:**
  - **What happens.** If `PLAN_SHA256` is unset, empty or mistyped, the shell creates the capture
    files, and the observer starts and refuses at `PLAN` with zero bounded starts.
  - **What it costs.** For `observe`, FC-R2 and FC-R3 then call for fresh paths and a new attempt ID.
    The plan binds `observe-001`, so the corrected attempt would need a new plan and review.
- **Required change:**
  - **The value.** Set the variable to this record's digest in the same shell.
  - **The guard.** Write the argument as `"${PLAN_SHA256:?}"`. zsh then stops at the expansion,
    before any redirection or start: my probe exited with status 1 and created no file.
  - **The check.** Immediately before each launch, compare the plan file's SHA-256 with the
    variable, using a utility that starts no interpreter, for example `shasum -a 256`.
  - **The argv.** The observer's argv is unchanged.

### PR-04 (nonmandatory): `static`'s `facts_sha256` is the only early signal for unplanned facts

- **Location:**
  - M0-LAUNCH.json `/static_before_observe/expected/facts_sha256_if_nothing_changed`;
  - the observer's lines 2265-2271 and 2653-2664;
  - MR-PLAN.md lines 179-180.
- **Statement:**
  - `static` refuses only on a binding that the plan makes.
  - Its fingerprint also covers facts that the plan does not bind: the observed
    `__CF_USER_TEXT_ENCODING`, the kernel's version string, and the bytes of the Git pointer files.
  - W2's run gave `3f0624318211f82e76aaf408a98e2e0a82ec2147ed681682242f37c9343c4ddf`.
- **Required change:** The Director compares its `static`'s value with W2's. On a difference, it
  stops before `observe` and reconciles: no bounded start has then been made.

### PR-05 (nonmandatory): an empty stderr is observed once, not established

- **Location:**
  - the plan's `/commands/0/stderr_predicate` and `/commands/1/stderr_predicate`;
  - the observer's lines 102-107 and 2483-2490;
  - MR-PLAN.md lines 239-245;
  - MH's inspection receipts.
- **Statement:**
  - **What MH saw.** For the same bytes and environments, MH's M0 saw Git print
    `git version 2.50.1 (Apple Git-155)` in 0.007 s, and Node `v24.22.1` in 1.11 s. Both stderr
    streams were empty, and both groups were absent at exit.
  - **Why no plan can correct it.** `_plan_shape` refuses any other commands.
- **Required change:** The Director adopts MH's classification again before S5. A refusal with
  `OUTPUT-STDERR` has its cause in the implementation's constants, so MR stops with it kept, and no
  corrected plan or new attempt follows in this phase.

### PR-06 (nonmandatory): the adoption record is bound to the plan by reference only

- **Location:**
  - the plan's `/source`, a closed schema (the observer's lines 2027-2033);
  - W3-OBSERVER.md Q8;
  - PLAN-AUTHOR-NOTES.md lines 384-386.
- **Statement:**
  - **The reference.** The plan binds the record only through B and its tree, and M0 checks only
    HEAD's ref.
  - **This review's static binding.** Blob `0431fab527c6bb69d52e224cac73c524ea6f70a3` at B and C, and
    SHA-256 `872312ed80a63fbb196c17ace42e786b7fe757b710eff41139b125dfaa507937`, 5,396 bytes, `0o644`,
    one link.
- **Required change:** None for M0 and M1. The S6 configuration binds the bytes, and its review
  compares them with this binding.

## 9. Conduct and starts

**Forbidden starts: none.** I started no Git of any kind, no Node, `ldd`, `codesign` or `otool`, no
observer command (not even `static`), no routine driver, no `tools/check_local.py` and no unit test.

**Framework-interpreter starts: 18 before these records, all `python3 -I -S -B`.**

| Script | Starts |
| --- | ---: |
| `w3_show_plan.py` | 1 |
| `s01` | 1 |
| `s02` | 1 |
| `s03` | 4 |
| `s04` | 2 |
| `s05` | 1 |
| `s06` | 1 |
| `s07` | 2 |
| `-c` reads that printed my own outputs or MH's two inspection receipts | 5 |

`s08_report_check.py` is start 19, after these records.

**Shells and utilities.**

- **Shells.** There were 50 Bash calls before these records, each one `zsh`, and one more follows
  for `s08` and a listing.
- **Utilities.** About 140 utility processes, all read-only: `ls`, `cat`, `grep`, `sed`, `head`,
  `tail`, `cut`, `wc`, `tr`, `awk`, `ps`, `lsof`, `mount`, `stat`, `xattr`, `sysctl` and `date`.
  Besides those: one `mkdir` for OUT, and one nested `zsh -f` probe of the guard in PR-03, which
  wrote nothing. Command substitutions add a few subshells.
- **Process listings.** `ps` and `lsof` identified the users of the bound image. Their arguments and
  environments are not recorded, apart from whether `-B` appeared.

**Nothing else.**

- No project module was imported or run.
- Nothing was downloaded or installed, and Finder was not used.
- I wrote only under OUT.
- The harness's wrapper may start processes I cannot see. It also attached a Git status summary of
  the main clone to my context; no command of mine produced it.

## 10. Files

All of these are in OUT, and `SHA256SUMS.txt` lists every file except itself.

- **The records:** `PLAN-REVIEW-001.md` and `PLAN-REVIEW-001.json`.
- **The scripts:** `scripts/w3_common.py`, `w3_show_plan.py`, and `s01` to `s08`.
- **The outputs:** `outputs/s01-…` to `outputs/s08-…`. They use labels, not machine paths; the JSON
  form lists their digests.
- **The exception:** `outputs/plan-indented.json` is an indented reading copy of the plan, with its
  machine paths, and is not for copying.
