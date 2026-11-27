# Plan review 001: observation plan 001 for M0 and M1

| | |
| --- | --- |
| Reviewer | W3, the independent reviewer of observation plan 001: a Claude Code subagent in a fresh context, with no earlier review in it. W3 wrote none of the plan, its inventories, the launch record, the observer, the supervisor, the contract, the amendment, MP's preparation or the MH tooling. |
| Gate and stage | gate MH, phase `C271-P35-macos-host-qualification-mh`, stage S4 of MH-PLAN, Director `c271-p35-e38e3aa82ade`, local mode |
| Under review | W2's observation plan 001 and its companions in `<local>/c271-p35/workers/W2-plan-001/` |
| Commit C | `0eb9a5517f4e19705178a2c59b8d8d33fb87867a`, tree `ea10cd94c05a2ebbb44b3f83d4c96cb0a59baa2b` |
| Host | macOS 26.6.2 (25G83), Darwin 25.6.0, arm64, boot `C90010BA-4DA9-475D-BBAB-CF1A9C40175A` (booted 2026-11-23T12:20:29Z) |
| Written | 2026-11-27, after the final recheck at 05:15:43Z |

Places are named by labels:

- `<worktree>` is the C271 worktree at commit C.
- `<local>` is the working directory beside the clone. `<local>/..` is the directory that holds it, and `<local>/../..` is the mount point of the external volume.
- `<common-dir>` is the clone's Git directory, which `<worktree>/.git` names through `<common-dir>/worktrees/c271`.
- `<prefix>` is the installation prefix of the interpreter's framework and of its non-system libraries. `<package-manager>` is the package manager that owns it.
- `<framework>` is `<prefix>/Cellar/python@3.12/3.12.13/Frameworks/Python.framework/Versions/3.12`.
- `OUT` is `<local>/c271-p35/workers/W3-plan-001/`, the only place I wrote.

The machine-readable form is [PLAN-REVIEW-001.json](PLAN-REVIEW-001.json).

## Verdict

**ACCEPT_WITH_NONMANDATORY_FINDINGS.** There is no mandatory finding.

**The plan's SHA-256, computed from the file's bytes:**
`b8cd6449aba958373f68715158402ed2e0e233e08213f3521bbc3d80cfe4c152`. The file is
`<local>/c271-p35/workers/W2-plan-001/observation-plan-001.json`: 9,017 bytes, mode `0o644`, one
link, canonical JSON.

- **Every key of the plan equals the actual state.** I recomputed each one with my own code: 156
  checks in s02, all passed, and a final recheck in s08 at 05:15Z.
- **The Python inventory, recomputed from W3-OBSERVER section 5 by my own code, is byte-identical
  to W2's.** That code is my own walker, link resolver, Mach-O reader, closure and package check.
  The digest is `c277bdd3ac6aa73105df3924707a271a402a0dc7c722be27a6834f2c78605633`, the frozen
  figure, with 776,209 canonical bytes.
- **The other two inventories hold.** The source inventory recomputes byte-identically. W2's
  dependency inventory equals the installed reader tree, the C199 pins, MP's reader plan and
  receipt, and the contract's pins.
- **Git's files agree with commit C.** Read without Git, commit C, its tree, the worktree and the
  index agree. The adoption record of amendment 001 is exactly its blob at C.
- **N-07 holds.** The bound Git is the developer tools' file that N34-M read, and the version line
  that its arm64 slice predicts fits the plan's grammar.
- **The launch record is exact.** M0-LAUNCH.json's command is exactly W3-OBSERVER section 1's launch
  of `observe`.
- **Six nonmandatory findings, PR-01 to PR-06.** The most important are:
  - **PR-02:** an empty stderr from the two `--version` starts is predicted, not established. If
    it fails, MH stops.
  - **PR-03:** a launchd job that MH did not start uses the bound interpreter.
  - **PR-01:** MH-PLAN section 6 asks for a separate binding of the adoption record, and the closed
    plan schema cannot carry one.

## 1. Method

### 1.1 Reads

I read these with the agent's file-read tool. It reads files and starts no host process.

- **MH-PLAN.md, all of it.** Its SHA-256 now is `02da913c…`, 16,420 bytes. That version includes
  section 10. N34-M read an earlier version.
- **W3-OBSERVER.md, all of it.** Section 6 is the implemented rule set (N-05).
- **CONTRACT.md:** sections 3, 4, 7 and 10, and the rest for context.
- **P07 QUALIFICATION-PLAN.md:** sections 2 to 4.
- **From MP:** OUTCOME.json, CLOSING.json, EXACT-RECEIPTS-SHA256SUMS.txt and
  `plans/EXACT-PLANS-SHA256SUMS.txt`.
- **From N34-M:** N34-M-DISPOSITION.json, and the review's Git (section 2.9 and N-07), D-16
  (section 2.1, answer (b) and N-04) and subtype (answer (c)) facts.
- **The tooling:** FAILURE-CAPTURE.md, README.md and `authoring/TOOLING-SHA256SUMS.txt`.
- **The observer's source.** I read its constants, canonical paths, bounded reads, environment,
  platform and OS readers, its trees and links, the Python inventory and closure, `compare_inventory`
  and `verify_packages`, the launcher and loaded-module checks, the source, dependency, runtime and
  Git checks, and the receipt rule. I also read `_plan_shape`, `validate_plan`,
  `load_darwin_supervisor`, `static_observation`, `static_after_start`, the evidence store, the
  start, `static_check`, `observe_host` and `main`.
- **Both supervisor files and both package `__init__.py` files.**
- **W2's notes, records and three scripts, and MP's two receipts.**

### 1.2 My scripts

My scripts are in `OUT/scripts/` and their outputs in `OUT/outputs/`.

- **Python and nothing else.** Each script uses the standard library only and imports nothing of
  the project, except s06 (see below). Each installs an audit hook that refuses every
  process-creation event, and none recorded one.
- **No machine path in a script.** Every path is an argument or relative to one.
- **Written to absent paths only.** Each output was created with `O_EXCL`.

| Script | What it does |
| --- | --- |
| `s01_listing.py` | Lists and hashes W2's directory and checks its 49 digests. Lists the evidence parent and MP's plans, receipts, archive and prepared trees. Pretty-prints four documents for reading. |
| `s02_plan_keys.py` | Checks every key of the plan against the actual state, in 156 checks. It checks the receipt rule, the dependency inventory and M0-LAUNCH.json, and records ancestors, filesystems, extended attributes and the digests of everything read. Its constants are written from the contract and W3-OBSERVER section 2. The 15 values of `LIMITS`, which the schema names but does not list, come from the observer's source. |
| `s03_python_inventory.py` | Recomputes the Python inventory from section 5, evaluates section 6.3's rules for every image, and verifies the packages. |
| `s04_source_and_git.py` | Recomputes the source inventory, then reads HEAD, commit C, its tree, the worktree and the index without Git. |
| `s05_macho_static.py` | Reads Git's fat header and both slices, and finds the version texts in them. Checks `bin/node` against section 6.2's rules. |
| `s06_observe_only_and_processes.py` | Reproduces the loaded-module check that only `observe` makes, and lists the processes. |
| `s07_foreign_processes.py` | Identifies the processes that use the bound images. |
| `s08_final_recheck.py` | The final recheck, the digests of my files, and the final process check. |
| `s09_report_check.py` | Run after this record was written. It parses PLAN-REVIEW-001.json and checks the plan digest and the verdict in both reports. It scans both for machine paths, the user's name and the package manager's name. |

## 2. Answers

### 2.1 Every key against the actual state (question 1)

**Canonical form and P07 section 2.** The plan meets both.

- **Canonical JSON.** The plan is canonical JSON: sorted keys, compact separators, ASCII, and no
  trailing newline. It has no duplicate member, float or nonfinite constant (P-01, P-02).
- **No unresolved value.** No value is null. None holds `TODO`, `TBD`, `FIXME` or `XXX`, one of
  `* ? [ ] { } ~ $`, or a backtick. No digest is one repeated digit (P-04).
- **The 17 top-level keys are exactly the schema's (P-05).**
- **Every path equals its canonical form.** I checked each of them by lstat on every component and
  by realpath. A path inside the absent attempt counts as canonical when the attempt itself is
  canonical with an absent last component. No bound path has a linked component (P-03, P-06).

| Key | Plan value | My reading (check IDs in s02) |
| --- | --- | --- |
| `schema`, `contract`, `profile`, `executor` | `ontokin.current-host-readback-observation-plan/0.2.0`, `ontokin.current-host-readback/0.2.0`, `darwin-arm64-v1`, `macos-arm64-local` | The constants of W3-OBSERVER section 2 (K-01 to K-04). |
| `environment` | `PATH=/usr/bin:/bin`, `LANG=C.UTF-8`, `LC_ALL=C.UTF-8`, `TZ=UTC`, `UV_THREADPOOL_SIZE=2` | Exactly these five, with string values (K-05). |
| `platform` | Darwin, `25.6.0`, arm64, `proc_translated` 0, boot `C90010BA-…175A` | Read with `os.uname()`, `kern.osrelease` (`25.6.0`), and `sysctl.proc_translated` (0) and `kern.bootsessionuuid` through `sysctlbyname`, via ctypes and libSystem. These are the actual release and this boot, as P07 section 2 requires (K-07 to K-11). |
| `os.system_version` | `/System/Library/CoreServices/SystemVersion.plist`, `6151cb88…04a1`, 603, `0o444` | Rehashed. The plist reads macOS 26.6.2, build 25G83, which equals `kern.osversion`, with no `ProductVersionExtra` (K-12 to K-14, K-18). |
| `os.cryptex` | present, `/System/Volumes/Preboot/Cryptexes/OS/System/Library/CoreServices/SystemVersion.plist`, the same digest, size and mode | I resolved the conventional path myself. It takes one hop, `/System/Cryptexes/OS` → `../../System/Volumes/Preboot/Cryptexes/OS`, and ends at the plan's path, a regular file (finding F1, decision D-10). That path has no linked component. Rehashed, its bytes equal the system file's (K-15 to K-17). |
| `source.root`, `commit`, `tree` | `<worktree>`, C, `ea10cd94…` | The root is canonical, HEAD resolves to C, and C names the tree (section 2.3; K-19 to K-22). |
| `source.inventory` | W2's file, `95abd300…`, 96,238, `0o644` | Rehashed and recomputed (section 2.2; K-23, K-24). |
| `observer` | `<worktree>/prototypes/static_tray_v01/current_host_observation_v02.py`, `471a9547…2788`, 162,557, `0o644` | Rehashed. It equals the source inventory's entry and the file that N34-M reviewed (K-25, K-26). |
| `python.venv`, `framework`, `version` | `<worktree>/.venv`, `<framework>`, `3.12.13` | Both paths are canonical, and the framework is a `Python.framework/Versions/3.12` directory with no linked component. The version is pyvenv.cfg's, and that of my own interpreter, which is the same launcher: `sys.executable` is `<worktree>/.venv/bin/python`, and it resolves to `<framework>/bin/python3.12` (K-27 to K-31). |
| `python.inventory` | W2's file, `c277bdd3…`, 776,209, `0o644` | Rehashed, canonical, the frozen figure, and recomputed (section 2.2; K-32, K-33). |
| `runtime.directory`, `version`, `root_mode`, `bin_mode` | `<local>/c271-macos/node-v24.22.1-darwin-arm64`, `v24.22.1`, `0o755`, `0o755` | The directory is canonical, with exactly `{bin/, bin/node, NODE-SOURCE.json}`: no link, no `.DS_Store`, and files with one link each. The modes come from lstat (K-34 to K-39). |
| `runtime.executable` | `6f320694…f329`, 122,545,856, `0o755` | Rehashed; it equals MP's OUTCOME.json and N34-M. I checked it with W3-OBSERVER section 6.2, the implemented rules (N-05), in s05: thin `MH_MAGIC_64`, `CPU_TYPE_ARM64` with subtype exactly 0, and `MH_EXECUTE`. All 21 commands are in the closed list of 16, with one `LC_LOAD_DYLINKER` `/usr/lib/dyld` and one `LC_MAIN`, and no duplicate. The four dylibs are system paths, with CoreFoundation as a plain `LC_LOAD_DYLIB` in command 14 (D-16) (K-40, K-41). |
| `runtime.node_source` | `e928a8ec…9ea2c`, 976, `0o644` | Rehashed. It is canonical ASCII JSON with its seven keys: the pinned archive name, digest and size, the checksum-file identity, the signature check `not_performed` (recorded, not refused; D-02), and an extracted binding equal to the executable's (K-42, K-43). |
| `runtime.archive` | `<local>/c271-p34/downloads/node/node-v24.22.1-darwin-arm64.tar.gz`, `89c68259…c0a7`, 53,062,778, `0o444` | Rehashed. It is the contract's pin, retained with mode `0o444` (K-44, K-45). |
| `runtime.install` | MP's exact Node plan (`1fee042d…`, 956,650, `0o644`) and receipt (`65caf77a…`, 2,897, `0o600`) | Rehashed. They equal `EXACT-PLANS-SHA256SUMS.txt` and `EXACT-RECEIPTS-SHA256SUMS.txt`. My own implementation of the receipt rule of W3-OBSERVER section 3 passes (list below; K-46 to K-50). |
| `dependencies.root` | `<local>/c271-macos/reader-c195` | Canonical: 24 files and 13 directories (K-51, K-52). |
| `dependencies.inventory` | W2's file, `3545d5f9…`, 4,543, `0o644` | Section 2.2 (K-53 to K-61). |
| `dependencies.install` | MP's exact reader plan (`ff5a95da…`, 158,115, `0o644`) and receipt (`03222a85…`, 4,116, `0o600`) | Rehashed. Under the receipt rule with purpose `retained-dependencies`, both pass: 730 members with digest `72dc3175…`, and `node_source` null (K-62 to K-66). |
| `git` | `/Library/Developer/CommandLineTools/usr/bin/git`, `be4afb2b…`, 7,604,272, `0o755` | Rehashed. The path is canonical, is no link, and is not `/usr/bin/git`. The file is neither a hard link of the dispatcher (device and inode differ) nor the dispatcher's bytes (K-67 to K-70; section 2.4). |
| `commands` | `git_version`, then `node_version` | I built both records from W3-OBSERVER section 2's table and `LIMITS`, and they equal the plan's in order. Each has its argv, cwd `<attempt>/<id>`, label and environment: the declared five, plus the six `GIT_*` variables for Git. Each has 5,000, 3,000 and 2,000 ms, one expected start, its stdout predicate and an empty stderr predicate (K-71, K-72). |
| `evidence.parent` | `<local>/c271-p35/evidence` | Canonical, a directory, and empty at s01, s02 and s08 (K-74). |
| `evidence.ancestors` | seven rows | My own lstat walk, sorted by path, with no link (K-75): `/` (16777234, 2, `0o755`); `/Volumes` (16777234, 18343, `0o755`); `<local>/../..` (16777244, 2, `0o775`); `<local>/..` (16777244, 7019967, `0o755`); `<local>` (16777244, 14022344, `0o755`); `<local>/c271-p35` (16777244, 15728058, `0o755`); the parent (16777244, 15728417, `0o755`). |
| `evidence.attempt` | `<local>/c271-p35/evidence/observe-001` | An absent direct child (K-76). |
| `evidence.outputs` | the fixed topology | I built it from W3-OBSERVER section 2, and it is equal (K-77). |
| (roots) | — | The parent lies outside `<worktree>`, the venv, the framework, the runtime, the reader tree and Git's directory, and none of them lies inside it. The bound roots are disjoint (K-78, K-79). |
| `failure_capture.procedure` | `<worktree>/docs/engineering/localized-repair-c271/macos-qualification-p35/tooling/FAILURE-CAPTURE.md`, `f387fb3e…c99c`, 13,147, `0o644` | Rehashed and outside the attempt. It equals `TOOLING-SHA256SUMS.txt` at C. The procedure's own tool, `capture_probe.py`, equals its listed digest `db5fb525…` (K-80 to K-83; s08). |
| `limits` | 15 values | Equal to the observer's `LIMITS` (K-06). |

**The receipt rule, written independently.** The rule is W3-OBSERVER section 3, decisions D-05
and D-11. I checked each of its parts for the runtime and for the reader tree.

- **The plan:**
  - the 12 closed keys of `install/0.2.0`;
  - the schema and contract, and the purpose;
  - `source_root` = `<worktree>`;
  - the destination, root mode, files and directories, equal to the observation plan's tree;
  - the archive descriptor, exactly the plan's;
  - `report` = the receipt's path;
  - a non-empty `members` map with integer sizes.
- **The receipt's state and keys:**
  - `INSTALLED_EXACT` with `passed: true`;
  - the closed keys of its outcome;
  - design revision 4 and `["P33-AMENDMENT-001"]`;
  - zero Node, `ldd` and checker starts;
  - rows `created_owned_stage` only;
  - pins exactly `{origin: adopted-contract, node_archive_sha256, dependency_archive_sha256}`.
- **The receipt's labels and source:**
  - labels `{executor, contract, profile, design_revision, amendments, pins, os}`, with the pins of
    its purpose (Node's binding for `selected-node`) and HOST's OS-label shape;
  - `preparer_source.root` = `<worktree>`.
- **The receipt's readbacks:** before `{state: absent}`, after `{state: complete_exact, files,
  directories}`, and publication through `renamex_np` with `RENAME_EXCL` (4) from
  `/usr/lib/libSystem.B.dylib`.
- **The archive summary:**
  - keys, digest and size;
  - the member count and expanded bytes;
  - a member digest equal to `sha256` of the canonical ASCII member map: `0b2b6072…` for Node,
    which is also NODE-SOURCE.json's;
  - for Node, the extracted executable's member, path, binding and four Mach-O keys.
- **NODE-SOURCE.json against the plan.** The plan's `node_source` is exactly NODE-SOURCE.json's
  signature record, and NODE-SOURCE.json's archive size equals the archive's.

### 2.2 The inventories (question 2)

**The Python inventory.** `s03` recomputes the inventory with my own code.

- **What my code does:**
  - It lists both trees exhaustively without following a link: files by SHA-256, size and mode,
    links by target, and directories by mode.
  - It classifies every file by its first four bytes. Neither tree holds a fat, 32-bit or
    big-endian file.
  - It resolves the selection chain hop by hop.
  - It evaluates section 6.3's rules on each of the 111 images and finds no problem.
  - It builds the closure, which reaches stable spellings in 2 passes, and checks the packages by
    item 6.
- **The result.** The digest is `c277bdd3ac6aa73105df3924707a271a402a0dc7c722be27a6834f2c78605633`.
  It equals W2's file and the frozen figure, and the canonical bytes are identical. Each part is
  equal: the schema, both roots and entry maps, the selection, and the closure's images, external
  libraries and links. s08 recomputed it at the end, with the same digest.
- **The frozen figures (N-08)**, which equal PLAN-AUTHOR-NOTES section 6 and N34-M:
  - **The framework version directory:** 3,478 files, 414 of them bytecode in 37 `__pycache__`
    directories, 5 links and 305 directories, 72,433,430 file bytes.
  - **The `.venv`:** 297 files with no bytecode, 3 links and 45 directories, 13,983,870 file bytes.
  - **111 images.** The framework holds 2 `MH_EXECUTE`, 1 `MH_DYLIB` and 76 `MH_BUNDLE`, and the
    `.venv` holds 19 `MH_DYLIB` and 8 `MH_BUNDLE`. Five external dylibs lie under `<prefix>/Cellar`
    (mpdecimal, libcrypto, libssl, sqlite and xz, the `<package-manager>`'s libraries), each also
    spelled through `<prefix>/opt`.
  - **The closure:** 6 link hops, 26 `@loader_path` references and 81 `LC_RPATH` entries.
  - **The selection chain:** 4 hops from `<worktree>/.venv/bin/python` to
    `<framework>/bin/python3.12`. `home`'s launcher takes 2 hops, and `executable` none.
- **The packages:**
  - exactly the lock's seven pins, and the lock equals the contract's seven;
  - hashed RECORD rows: Pillow 139, attrs 36, jsonschema 45, jsonschema-specifications 29,
    referencing 20, rpds-py 10 and typing_extensions 6, with one unhashed row each, the RECORD
    itself;
  - no unowned file under site-packages.

**The source inventory.** `s04` recomputes it from the schema's sets: `SOURCE_TREES` (4 trees),
`SOURCE_FILES` (16 roles) and the three present `SOURCE_OPTIONAL` files.

- **Its digest:** 644 files, 13,588,394 bytes, `95abd300edbb9930e67c569b726015964ab98f4ed0ede389da122bbb3f145c4c`,
  byte-identical to W2's file.
- **Clean trees.** No link, `.DS_Store`, `__pycache__` or bytecode file lies in the trees, and
  every file has one link, which `check_source`'s private rule requires.
- **Commit content.** Every file equals its blob at C.
- **Membership.** The four supervisor files are in the set. The adoption record of amendment 001
  is not.

**W2's dependency inventory.**

- **Its shape.** It is canonical `ontokin.current-host-readback-dependencies/0.2.0` with exactly
  `{schema, files, directories, archive}`.
- **Its files.** The 24 files equal the installed tree by SHA-256, size and mode (`0o644`), and each
  has one link. They also equal the C199 pins of EXTERNAL-INPUTS.json by name, SHA-256 and size;
  that file is the pinned `21fd6bad…`.
- **Its directories.** The 13 directories equal the tree's, with mode `0o755`, and are exactly the
  necessary set.
- **Its archive.** `<worktree>/docs/engineering/ownership-recovery-c195/evidence/recorded-evidence.tar.xz`:
  `b1e54a6c…a0c9`, the contract's pin, 2,611,764 bytes, `0o644`. Rehashed, it equals its blob at C.
- **Against MP's reader plan.** The plan's files, directories, archive descriptor and root mode
  equal the inventory's, as the receipt rule requires. The receipt carries the reader-tree pins.
  The validator is `2.0.0-dev.3.10` and Three.js `0.186.1`.
- **No value of W2's own.**

### 2.3 Commit C, its tree and the adoption record (question 3)

**HEAD.** I read it from Git's files without starting Git.

- `<worktree>/.git` reads `gitdir: <common-dir>/worktrees/c271`, and `commondir` is `../..`.
- `HEAD` is `ref: refs/heads/work/c271-missing-import-digest-control`.
- The ref exists only in the common directory, where it holds C. There is no per-worktree ref and
  no `packed-refs` entry.
- The Git directory's backlink names `<worktree>/.git`. There are no alternates.

**The commit.** C is a loose object.

- I inflated it with zlib, and SHA-1 of `commit <size>\0` plus its bytes recomputes to C.
- It names tree `ea10cd94…`, the Director's tree, and one parent, `c81cf07b5386ea7eba7904f3ef5700709b84b366`.
- It is unsigned, was committed at 2026-11-27T04:17:03Z, and has the subject "C271-P35: commit C,
  the reviewed MH tooling (stage S3)".

**The packed objects.** The store has one pack of 27,674 objects.

- **The index.** I parsed the pack's version-2 index: its fan-out table, its sorted names, and its
  32-bit offsets with the 64-bit overflow table. Its checksum is valid.
- **Each object.** At each object's offset I read the type-and-size header and inflated the data
  with zlib. I rebuilt `OFS_DELTA` and `REF_DELTA` objects by applying their copy and insert
  instructions to their bases, resolved recursively.
- **Names.** I recomputed every object's name from its type, size and bytes.
- **The reads:** 78 loose and 2,473 packed.
- **The tree:** 2,550 trees and 22,490 entries, which are 22,482 `100644`, 2 `100755` and 6
  `120000`.

**The worktree.** Apart from `.git` and `.venv` at its root, it holds 22,484 files and 6 links in
2,549 directories.

- Every one equals its tree entry by blob name and mode: the user execute bit for files, and the
  target bytes for links.
- Nothing is missing, extra or changed.
- No `.DS_Store`, bytecode, special file, multi-link file or directory without tracked content
  exists.

**The index** (`<common-dir>/worktrees/c271/index`) equals the tree.

- It is version 2 with 22,490 entries, and its checksum is valid.
- It equals the tree by path, mode and blob, and its cached sizes equal the files.
- No entry has a conflict stage, an assume-valid flag or an extended flag.
- Its `TREE` extension's root is `ea10cd94…` with 22,490 entries. It also has a 516-byte `REUC`
  extension.

**The adoption record** `docs/engineering/localized-repair-c271/macos-implementation-p33/ADOPTION-AMENDMENT-001.json`:

- **At C:** blob `0431fab527c6bb69d52e224cac73c524ea6f70a3`, mode `100644`, in tree
  `61abde500dfb7283e22495b2759f459f26eea15e` of `macos-implementation-p33/`.
- **In the worktree:** the same blob. SHA-256
  `872312ed80a63fbb196c17ace42e786b7fe757b710eff41139b125dfaa507937`, 5,396 bytes, `0o644`, one
  link. Its schema is `ontokin.c271.p33-amendment-adoption/1`, with `design_revision` 4.
- **The answer: it is exactly the file at C.**
- **Is the binding through the commit and the tree sufficient?** Only as a reference.
  - The chain C → tree → blob fixes the committed bytes.
  - But M0 checks only that HEAD's ref holds C. It reads neither the commit nor the tree object,
    nor the record. HOST records the tree as a planned value (W3-OBSERVER Q8).
  - So at M0 the record is bound only by the static checks that W2 and this review made. It is not
    bound by bytes.
  - For M0 and M1 that suffices, because neither reads the record: HOST's `design_revision` and
    `amendments` are constants of the observer.
  - It does not meet MH-PLAN section 6's "bind it separately" for the observation plan, which the
    closed schema cannot carry. See PR-01.

### 2.4 N-07: the bound Git (question 4)

- **It is N34-M's file.** The plan binds `/Library/Developer/CommandLineTools/usr/bin/git`:
  SHA-256 `be4afb2b003904725826250de9fb76567bbacf82323457b5a1ec26706b66bcae`, 7,604,272 bytes,
  `0o755`. These are N34-M's path, SHA-256 and size, rehashed. No other candidate's load commands
  need to be read.
- **My own static read in s05.** The file is fat (`0xcafebabe`), with an x86_64 slice (subtype 3)
  and an arm64 slice (subtype 0).
  - Each slice is `MH_EXECUTE`, with 22 commands, dylinker `/usr/lib/dyld`, no `LC_RPATH`, no
    unknown command and a code signature, built for minimum OS 14.0 with SDK 26.4.
  - Each links only CoreServices, libz, libiconv, libSystem and CoreFoundation, all system paths.
  - This equals N34-M section 2.9. On this host the kernel runs the arm64 slice, since the file
    has no arm64e slice.
- **The version line.** Each slice embeds the format `git version %s\n` once and the version text
  `2.50.1 (Apple Git-155)` once.
  - So the predicted line, `git version 2.50.1 (Apple Git-155)\n`, follows from the file.
  - It matches `git-version-line-v1` (`git version [\x20-\x7e]{1,200}\n`).
  - It remains a static prediction, which the HOST review compares. The plan freezes only the
    grammar.

### 2.5 M0-LAUNCH.json (question 5)

- **The command is exactly W3-OBSERVER section 1's launch (L-01 to L-04).** It is `/usr/bin/env -i PATH=/usr/bin:/bin LANG=C.UTF-8 LC_ALL=C.UTF-8 TZ=UTC UV_THREADPOOL_SIZE=2 <worktree>/.venv/bin/python -I -S -B <worktree>/prototypes/static_tray_v01/current_host_observation_v02.py observe --plan <local>/c271-p35/workers/W2-plan-001/observation-plan-001.json --plan-sha256 b8cd6449aba958373f68715158402ed2e0e233e08213f3521bbc3d80cfe4c152`.
  - It runs the launcher with `-I -S -B`, the observer and `observe`, with the plan's path and the
    digest that I computed.
  - `env -i` clears the inherited environment and executes the launcher in the same process, with
    exactly the declared environment. `observer_process_argv` is the argv after `env`.
  - The recorded environment is the declared five. Its `environment_canonical_sha256`,
    `0ed78f47b1929634d65b6407b8e8daf047aeb2daa6b5c194c24e91a7b91ebcf2`, equals my digest of the
    canonical map.
- **The cwd is the evidence parent**, which exists and is canonical (L-05).
- **The shell form has the same words** (L-07). No word needs quoting. It reads `cd <parent> && … >
  <stdout> 2> <stderr>; echo $? > <exit>`.
- **The capture paths are right under FC-K2, and absent (L-06).** They are
  `<local>/c271-p35/evidence/observe-001.observe.{stdout,stderr,exit}.txt`: three distinct siblings
  of the attempt in the parent, never inside it, and absent at s02 and at s08. Creating them before
  the start changes neither the parent's device, inode and mode, which is all `_ancestors`
  compares, nor the absence of the attempt.
- **The expected starts are exactly `expected_commands` (L-08).** They are the plan's two commands
  in order, through `supervisor_darwin_v01.run_process`, with totals node 1 and other 1. These are
  MH-PLAN section 7's rows M0 and M1.
- **The expected outputs are exactly `output_paths` (L-09, L-10).** All planned paths equal the
  plan's outputs. Success means:
  - the 19 planned files without the three `failure.json` files;
  - the three directories, mode `0o700`;
  - HOST at its path, with exit status 0.

  The predicted Git line fits the grammar (L-12).

### 2.6 W2's open questions and deviations (question 6)

**Q-A. Can Git or Node write to stderr for `--version` without `HOME`?** Neither environment has
`HOME`: Git gets the declared five plus six `GIT_*` variables, and Node the declared five.

- **Git, from static facts and documented behaviour:**
  - The arm64 slice embeds `git version %s\n`.
  - The variable names `GIT_CONFIG_GLOBAL`, `GIT_CONFIG_NOSYSTEM`, `GIT_ATTR_NOSYSTEM` and
    `GIT_TERMINAL_PROMPT` are in the binary, so it reads them.
  - The message `$HOME not set` is also in it. In upstream Git it belongs to `git config` with
    global scope, not to `--version`.
  - In upstream Git, `--version` becomes the `version` builtin. That builtin runs without
    repository setup and prints with `printf` to stdout.
  - With `GIT_CONFIG_GLOBAL=/dev/null` and `GIT_CONFIG_NOSYSTEM=1`, no configuration is looked up
    through `HOME`, and `version` reads none at all.
  - I did not read Apple's changes (Apple Git-155), so this is upstream behaviour, not a verified
    property of this build.
- **Node.** `node --version` prints its version from the C++ start-up, before V8, ICU and OpenSSL
  are initialized. Nothing on that path reads `HOME`. The binary holds the standalone C string
  `v24.22.1`.
- **CoreFoundation.** Both binaries link CoreFoundation, which adds `__CF_USER_TEXT_ENCODING` to
  its own process. I know of no stderr output on that path.
- **The answer.** There is no static evidence of a stderr write, and none can be excluded
  statically.
- **The consequence under MH-PLAN section 8:**
  - A non-empty stderr refuses with `OUTPUT-STDERR` after the counted start. For Git, that is
    before Node starts: 1 other start and 0 Node starts.
  - The environment and the empty stderr predicate are the observer's constants, and `_plan_shape`
    refuses any other commands. So no corrected plan can remove the cause, short of binding another
    Git, which N-07 would then require to be re-read.
  - The cause would therefore lie in the implementation, and MH stops (PR-02).

**Q-B. The cwd and the capture paths.** I accept both.

- With `-I` the cwd is not on `sys.path`. The observer resolves nothing relative to it, and the
  children run in their own stages.
- `static` ran from the same cwd.
- The capture paths meet FC-K2 (section 2.5). The capture of the Director's own `static` run is
  covered by PR-05.

**Q-C. Facts that can change without a file edit.** I agree.

- Both a remount and a reboot fail closed.
  - **Before any start:** `check_platform` and `_ancestors` run in `static_observation`, before the
    supervisor import.
  - **During `observe`:** `check_parent` and the rechecks catch them, but after a counted start.
- **The volume.** It is APFS, mounted as removable, with ownership ignored, `nosuid` and `nodev`. It
  is mounted without `noexec`, which `bin/node` needs, and without the quarantine flag.
- **What not to do.** Do not eject or remount it, and do not let it sleep or unmount before
  `observe` ends.

**Q-D. Modes.** I confirm them, both at s02 and at s08: plans `0o644`, receipts `0o600`, archive
`0o444`, `bin/node` `0o755` and `NODE-SOURCE.json` `0o644`. Nothing may be touched, `chmod`
included, until MH ends.

**Q-E. The REUC extension.** It is informational. It records earlier conflict resolutions. The index
has no conflict stage and equals the tree, and M0 never reads the index.

**D1. The dependency inventory, which W2 wrote.** Accepted: it is fully checked in section 2.2 and
carries no value of W2's own.

**D2. `static`'s streams in W2's `records/`.** Accepted. W2's `static` was an authoring check
(MH-PLAN section 3), not a frozen command, and keeping the evidence parent empty is preferable.

**D3. The preview and the two final rechecks.** Accepted. They are starts of the allowed kinds, and
the results agree with mine.

**D4. `_plan_shape` on a substituted copy in the preview.** Without effect. The write run's
`_plan_shape` and `validate_plan`, W2's `static`, and all of my checks used the final plan.

### 2.7 Anything else that would make `observe` refuse, or start on an unchecked input (question 7)

**1. Checks that only `observe` makes.**

- **(a) The loaded-module check after the supervisor import** (`observe_host`, line 2676).
  - **What s06 did.** It imported the supervisor as `load_darwin_supervisor` does, with the bound
    root on `sys.path` for the import only.
  - **The result.** Every loaded module file is a file of the frozen framework inventory, with any
    existing bytecode also inventoried, or a source-inventory file without bytecode.
  - **The supervisor.** `run_process`'s code comes from the bound file, and `Clock` and `Stop`
    exist. No `__pycache__` appeared.
  - **The limits of the import.** Both package files are docstrings, the supervisor modules only
    define names, and nothing was called.
- **(b) Evidence creation and publication.** `observe` makes directories with mode `0o700` and
  publishes with `renamex_np` and `RENAME_EXCL` on the evidence volume. That is the same APFS volume
  (device 16777244) on which MP published both trees the same way.
- **(c) The supervisor's stage inventory.** It admits only regular single-link files.
  The observer's `intent.json` and `started.json` in the stage qualify, far below the caps.

**2. No start runs on an unchecked input.**

- Before each start, every binding is checked again.
- Inside the command's clock, the executable is bound again by its bytes.
- The environment is exact, and each child runs in its own stage.
- System libraries are identified by OS build, as contract section 7 states.

**3. The executables.**

- `bin/node` carries no quarantine attribute, only `com.apple.provenance`. So do the archive and the
  framework launcher.
- Neither the prepared `bin/node` nor the bound Git is running.
- The other `node` processes on the host are other installations.

**4. Timing.**

- W2's `static` took 0.44 s, against 60 s for static work.
- My inventory recomputation took 0.29 s, and my source and Git reads 1.6 s.
- The rechecks inside `observe` lie outside the command clocks.

**5. Two host facts that only the starts can show:** PR-03 and PR-04.

## 3. Findings

All six are nonmandatory. None holds `observe`.

### PR-01 (nonmandatory): the adoption record is bound to the observation plan by reference only

- **Location:**
  - MH-PLAN section 6, the row "The adoption record lies outside the source set";
  - the plan's `source`;
  - W3-OBSERVER Q8;
  - PLAN-AUTHOR-NOTES section 5.
- **Issue:**
  - The row asks the observation plan to bind the record separately. The plan's schema is closed,
    since `_plan_shape` refuses any other member, so it cannot.
  - The plan binds the record through C and the tree. M0 checks only HEAD's ref, never the tree or
    the record's bytes.
  - W2 explains this in its section 5, but does not list it among D1 to D4.
- **Effect:**
  - None on M0 and M1, since neither reads the record.
  - The record is exactly its blob at C (section 2.3), and this review record now carries its
    SHA-256, size, mode and blob.
- **Recommendation:**
  - The Director records that, for the observation plan, the row is met by this review's static
    binding, not by the plan.
  - The S6 configuration binds the bytes through `amendment_adoption`. Its review compares them with
    `872312ed80a63fbb196c17ace42e786b7fe757b710eff41139b125dfaa507937`, 5,396 bytes, `0o644`, blob
    `0431fab5…`.

### PR-02 (nonmandatory): the empty stderr of both `--version` starts is predicted, not established

- **Location:**
  - W3-OBSERVER section 2 (`stderr_predicate` `""`) and `_predicate` (`OUTPUT-STDERR`);
  - the fixed `GIT_ENVIRONMENT` and `ENVIRONMENT`;
  - PLAN-AUTHOR-NOTES Q-A.
- **Issue:**
  - Neither environment has `HOME`.
  - The static facts of section 2.6 show no route to a stderr write, but they cannot exclude one,
    and Apple's Git changes were not read.
- **Effect:**
  - **Costs.** A refusal costs one counted other start for Git, before Node starts, or both starts
    for Node.
  - **No plan fix.** No corrected plan can change the environments or the predicate. The cause would
    lie in the implementation, and MH stops (MH-PLAN section 8).
- **Recommendation:** The Director records this classification before the run, so that such a
  refusal is not treated as a plan error and retried with a new plan.

### PR-03 (nonmandatory): a framework-interpreter process that MH did not start runs on this host

- **Location:** MH-PLAN sections 5 and 10 (N-09); `s06` and `s07`.
- **Issue:**
  - **The process.** PID 1304 has launchd as its parent and started at 2026-11-23T12:21:13Z, 44 s
    after boot.
  - **What it runs.** It runs the bound process image
    `<framework>/Resources/Python.app/Contents/MacOS/Python`, with a file-watcher script of another
    project on the same volume, which polls every second.
  - **Its bytecode setting.** Its environment sets `PYTHONDONTWRITEBYTECODE=1`, and its argv has no
    `-B`.
  - **N-09's reach.** N-09's hand-over note reaches other sessions, not launchd jobs.
- **Effect:**
  - **So far, none.** The framework inventory is unchanged across:
    - MP's after-snapshot;
    - N34-M;
    - W2's two computations;
    - my two, at about 05:05Z and 05:15Z.

    Those all fall within this process's lifetime.
  - **If it ever wrote a bytecode file**, M0 would refuse. That could follow a restart without that
    variable, or code that clears `sys.dont_write_bytecode`.
    - If the file appears before `observe`, M0 refuses at its first binding, before any start.
    - If it appears between two rechecks inside `observe`, M0 refuses with `DRIFT`, after a counted
      start.
- **Recommendation:**
  - The Director notes the process in the run record and leaves it as it is, since it is the
    owner's job, outside the project.
  - The Director's `static` immediately before `observe` detects any change.
  - If the owner prefers, the job can be paused until MH ends.

### PR-04 (nonmandatory): M1 is the first execution of the prepared `bin/node` on this host

- **Location:** MH-PLAN section 7, row M1; W3-OBSERVER section 7, step 2.
- **Issue:**
  - **Never run before.** MP, N34-M, W2 and this review started no Node.
  - **The first launch.** Any first-launch work falls inside M1's 3,000 ms active window: the
    page-in of 122.5 MB from the external volume, code-signature validation, and any assessment that
    the system makes of a newly seen executable.
  - **The static facts.**
    - `bin/node` carries no quarantine attribute.
    - The volume allows execution.
    - The file is signed and its bytes are the pinned official ones.
- **Effect:** A timeout or a refused execution would be a counted Node start that fails. Since the
  limits are fixed, MH would stop.
- **Recommendation:** Nothing changes in the plan. Run `observe` with the volume mounted and
  awake, and with no other heavy work on it.

### PR-05 (nonmandatory): M0-LAUNCH.json names the capture of `observe` only

- **Location:**
  - FAILURE-CAPTURE section 1, which applies the procedure to `static` and to `observe`, and FC-K2
    and FC-K3;
  - M0-LAUNCH.json, `command`.
- **Issue:**
  - The Director runs `static` again immediately before `observe`.
  - The launch record names no capture paths for that run.
  - It names no FC-K3 command record for either run: the environment as a file with its SHA-256,
    the UTC times, and `kern.bootsessionuuid` before and after.
- **Recommendation:**
  - For `static`, use fresh absent siblings, distinct from `observe`'s and never the attempt, for
    example `<local>/c271-p35/evidence/observe-001.static.{stdout,stderr,exit}.txt`.
  - Write an FC-K3 record for each of the two runs, with the environment file whose canonical
    SHA-256 is `0ed78f47…`.
  - Neither changes the plan or its digest.

### PR-06 (nonmandatory): portable copies of this review

- **Issue:**
  - My scripts hold no machine path.
  - My raw outputs in `OUT/outputs/` do. Moreover, `s07-foreign-processes.json` names another
    project's path and the arguments of the watcher of PR-03.
  - `s01`, `s06` and `s07` also list processes and files of the owner's session.
- **Recommendation:**
  - Commit only PLAN-REVIEW-001.md, PLAN-REVIEW-001.json and the scripts.
  - Keep the outputs beside the clone. Section 5 lists their SHA-256 values.

## 4. Conduct and start accounting

**Allowed starts only.** All ten of my starts were shells running my own scripts under
`<worktree>/.venv/bin/python -I -S -B`.

- **No forbidden start.** None of Node, Git of any kind, `ldd`, `codesign` or `otool` started, and
  no observer command ran, not even `static`. No utility such as `ls`, `cat`, `shasum` or `grep`
  started.
- **Nothing else changed.** I downloaded and installed nothing, and used no Finder.
- **Reads and writes.** All other reads used the agent's file-read tool, and all writes its
  file-write and edit tools, which start no host process as far as I can observe.
- **The harness's Git summary.** The agent harness attached a Git status summary of the main clone
  to my initial context. No command of mine produced it.

| # | Script | Exit | Python PID | Shell PID |
| ---: | --- | ---: | ---: | ---: |
| 1 | `s01_listing.py` (04:48:20Z) | 0 | 5796 | 5795 |
| 2 | `s02_plan_keys.py`, first run (before 05:02Z) | 1 | not recorded | not recorded |
| 3 | `s02_plan_keys.py` (05:02:01Z) | 0 | 6425 | 6424 |
| 4 | `s03_python_inventory.py` | 0 | 6528 | 6527 |
| 5 | `s04_source_and_git.py` | 0 | 6620 | 6619 |
| 6 | `s05_macho_static.py` | 0 | 6690 | 6689 |
| 7 | `s06_observe_only_and_processes.py` | 0 | 6861 | 6860 |
| 8 | `s07_foreign_processes.py` | 0 | 6906 | 6905 |
| 9 | `s08_final_recheck.py` (ended 05:15:43Z) | 0 | 7030 | 7029 |
| 10 | `s09_report_check.py`, after this record was written | see its output | see its output | see its output |

- **What each row is.** Each row is one Bash call of the agent: one `/bin/zsh` wrapper, a child of
  the agent harness (PID 82154), which started one Python process.
  - The framework launcher executed its `Python.app` image within that same process.
  - In all: 10 shell starts and 10 Python starts. Every Python start carried `-B`.
  - Run 10 is the last start. Its result is in `OUT/outputs/s09-report-check.json`.
  - Whatever the harness's wrapper runs inside the shell before my command is outside my view.
- **Run 2.** It stopped with a traceback, because my reader refused the floats of
  EXTERNAL-INPUTS.json, which are legitimate there. It wrote nothing. I made the float rule apply
  to the plan only, and run 3 succeeded.
- **The imports.** Two scripts imported code without starting anything, both under `-B`:
  - `s06` imported the four supervisor modules from `<worktree>`;
  - `s08` loaded my own `s03` and `s04` by path.
- **Nothing of mine remains.** Every start ran in the foreground, and its shell waited for it.
  - At s06 and again at s08, `kill(pid, 0)` answered `ESRCH` for each of the 14 recorded PIDs of
    the earlier runs.
  - At each check, the harness's only child was my current shell.
  - No process ran the prepared `bin/node` or the bound Git.
- **No edit in `<worktree>`, bytecode included.**
  - No `__pycache__` appeared under `prototypes/`.
  - At the end, the source inventory, HEAD and the Python inventory equal the frozen values.
- **Nothing under `<local>` outside OUT.** The evidence parent is still empty, and the attempt and
  the three capture paths are absent. W2's directory still holds exactly its 49 files and
  SHA256SUMS.txt, all equal. MP's seven files keep their digests and modes.

## 5. Files

**Reviewed: the files of `<local>/c271-p35/workers/W2-plan-001/`.**

- All 49 entries of SHA256SUMS.txt equal the files, and no other file exists.
- SHA256SUMS.txt itself has SHA-256 `79decabea561f5547435f9362d95cef1b373f8b79d9f34f902c6c414996d7636`.
- The JSON form lists every file.

| File | SHA-256 | Bytes |
| --- | --- | ---: |
| `observation-plan-001.json` | `b8cd6449aba958373f68715158402ed2e0e233e08213f3521bbc3d80cfe4c152` | 9,017 |
| `source-inventory-001.json` | `95abd300edbb9930e67c569b726015964ab98f4ed0ede389da122bbb3f145c4c` | 96,238 |
| `python-inventory-001.json` | `c277bdd3ac6aa73105df3924707a271a402a0dc7c722be27a6834f2c78605633` | 776,209 |
| `dependencies-inventory-001.json` | `3545d5f920ac840804a9e25d28a87d623f96af71537fd3f020a0c1d743f82fb4` | 4,543 |
| `M0-LAUNCH.json` | `b092ea007048b7f8c1972bb02b3a9e6b9063f5d7c2bd75c06023ae29a3bc0b29` | 15,344 |
| `PLAN-AUTHOR-NOTES.md` | `e4c410e5add5c1beadac3e948302ad4ceac93bebe05646d42c7736db8d42d5b8` | 24,831 |
| `scripts/w2_author_plan.py` | `19d4d8846772e11fd10845f9ec406b585a8c96aefa2f1eeced851718d24f7a9a` | 24,532 |
| `scripts/w2_git_static.py` | `ddc80e5c6f72705de65e791f1d9976781a2f5a5514a4b465ecfa0b8e00201447` | 28,434 |
| `scripts/w2_launch_record.py` | `84e606c7f27cb48a8cab857256812e5803412dbd6b24cad8260398147e7ce08c` | 12,141 |

**Bound inputs, rehashed:**

| File | SHA-256 | Bytes | Mode |
| --- | --- | ---: | --- |
| `<local>/c271-p34/plans/node-install-plan.json` | `1fee042d5e3c809a89d4975df40f69d7a27e88abf9ba58d8cf91ca16795c5ff1` | 956,650 | `0o644` |
| `<local>/c271-p34/plans/reader-install-plan.json` | `ff5a95da6d349e0bd6ea1d2c79fc02757de48ac9cbb89dc59737b67c6d7a71c8` | 158,115 | `0o644` |
| `<local>/c271-p34/receipts/node-install-result.json` | `65caf77a967898ef2d63a3f0595f6f754fde1e7fad9a61f938a084b6717d4729` | 2,897 | `0o600` |
| `<local>/c271-p34/receipts/reader-install-result.json` | `03222a857c7a5a186f1bb30c205d10360882962a7a181d6b3659da47a0ac3fb2` | 4,116 | `0o600` |
| `<local>/c271-p34/downloads/node/node-v24.22.1-darwin-arm64.tar.gz` | `89c682593d76cd44233fa53b1563264e7de9cbb189cad169135c5b4fadfbc0a7` | 53,062,778 | `0o444` |
| `<local>/c271-macos/node-v24.22.1-darwin-arm64/bin/node` | `6f32069480ec14d52b6d7b1f3c7124cfbbc46203abf5ddf5c65b127435f3f329` | 122,545,856 | `0o755` |
| `<local>/c271-macos/node-v24.22.1-darwin-arm64/NODE-SOURCE.json` | `e928a8ec87a6fcd8f21d7bef3e080392e0bdaad3acbf2e767997dae5ead9ea2c` | 976 | `0o644` |
| `/Library/Developer/CommandLineTools/usr/bin/git` | `be4afb2b003904725826250de9fb76567bbacf82323457b5a1ec26706b66bcae` | 7,604,272 | `0o755` |
| `/System/Library/CoreServices/SystemVersion.plist` and the cryptex copy | `6151cb883e5b48d43a33d4d41956405a1cd502e0c8622319388d943e2cb804a1` | 603 | `0o444` |
| `<worktree>/prototypes/static_tray_v01/current_host_observation_v02.py` | `471a954703a1a7974638e500051a6ac538bf81dfb2a01a3944bf441e96622788` | 162,557 | `0o644` |
| `<worktree>/docs/engineering/localized-repair-c271/macos-qualification-p35/tooling/FAILURE-CAPTURE.md` | `f387fb3ec0ed306366f6d3f22820ec344f1ac843008775475258c5de9634c99c` | 13,147 | `0o644` |
| `<worktree>/docs/engineering/ownership-recovery-c195/evidence/recorded-evidence.tar.xz` | `b1e54a6cfef133f7004b1988c90bc718fc954409843c2bcac3772d42e904a0c9` | 2,611,764 | `0o644` |
| `<worktree>/docs/engineering/static-tray-qualification-c199/EXTERNAL-INPUTS.json` | `21fd6bad8738ed51d4ced8036a0fcde5dd046823f55f71de52b9b81df659ccd5` | 19,901 | `0o644` |
| `<worktree>/docs/engineering/localized-repair-c271/macos-implementation-p33/ADOPTION-AMENDMENT-001.json` | `872312ed80a63fbb196c17ace42e786b7fe757b710eff41139b125dfaa507937` | 5,396 | `0o644` |

**Documents read** (under `<worktree>/docs/engineering/localized-repair-c271/` unless stated):

| File | SHA-256 | Bytes |
| --- | --- | ---: |
| `macos-qualification-p35/MH-PLAN.md` | `02da913c198118fc356cccdb60e78a3a2fef3b7ba7115d77d794a85f9e22fc49` | 16,420 |
| `macos-implementation-p33/interfaces/W3-OBSERVER.md` | `5e936aa4b46590df710dd13da2c2a2d1ac758aa903470bb5e72ef2143a02018d` | 38,426 |
| `macos-contract-design-p31/CONTRACT.md` | `42db98dc6099ee605b0963f3734f7bff2d68c019ff6c00a0ee97bd753c03fdc9` | 42,769 |
| `host-inspection-p07/QUALIFICATION-PLAN.md` | `cfb4200ea3745cfe590d9059cd272e244a2ba3cd8c9969f8df5982dc58a69bc1` | 23,696 |
| `macos-preparation-p34/OUTCOME.json` | `c964d4d8461a662eaa1e1d7a31fe01df6f3e000484eacd80527307e3100245e0` | 9,315 |
| `macos-preparation-p34/CLOSING.json` | `772e9c52868d70f966bfbea041dfe4f20013a73e957df64dd6d38d3c3c0b028a` | 4,111 |
| `macos-preparation-p34/EXACT-RECEIPTS-SHA256SUMS.txt` | `4e333092e23db825af7dad5e430ed238eae127f553785fc0dcbd329cc767e769` | 2,031 |
| `macos-qualification-p35/n34m/N34-M-DISPOSITION.json` | `238feefeeecabab2dab8140856a9fdc5215bf8d49f68eaa8a9b245e6552f9e14` | 7,737 |
| `macos-qualification-p35/n34m/N34-M-REVIEW.md` | `55e4a0568a35201f8064b606af8bcd8eed0f5d3758f72d20a315cc75ffd17547` | 82,141 |
| `macos-qualification-p35/tooling/README.md` | `60d9298f36a4170f8a610995e2b34cdfe2f70ed806683966a6556a0f1f7c6084` | 35,797 |
| `<worktree>/prototypes/static_tray_v01/supervisor.py` | `c47b84ab464e89d4c8673d7541679a45ddf3fc4816a906aff4546e074b4c5a10` | 11,286 |
| `<worktree>/prototypes/static_tray_v01/supervisor_darwin_v01.py` | `bd4a5e3fcdfb5367994bfeeb93d211dd627b830017b17f607cd94d71ade2bd2b` | 10,621 |

**My scripts**, in `OUT/scripts/`, which hold no machine path:

| File | SHA-256 | Bytes |
| --- | --- | ---: |
| `s01_listing.py` | `7dfee760b563be8cd77e729a3a1e6614089af78c7792e3bf116fc21fa15e3831` | 8,369 |
| `s02_plan_keys.py` | `2f758509860825c1d02897075d87e44957e61f118b296bdf14fdc25c92f02ff5` | 61,363 |
| `s03_python_inventory.py` | `284c5cec0ae3c28315fd981836c8f6ec2c9d2ac387099ff860498b288526efda` | 29,836 |
| `s04_source_and_git.py` | `43096033fc08e28d0991f9ecc850c57db61291c0fb6d07d86edd601ffd7fa2ec` | 26,294 |
| `s05_macho_static.py` | `2933747ea7d582946ee1f040808a4c632010601625fcb657f8f9496972eee75b` | 12,280 |
| `s06_observe_only_and_processes.py` | `14fddf306083f69fdf79a67110fcc85c73390d6aa016aaa118ae4984eab68c1b` | 11,793 |
| `s07_foreign_processes.py` | `e265b90ab1984a61db6e2b97cb7ca4d834de196b99154b27b21c91951c1ea569` | 7,774 |
| `s08_final_recheck.py` | `446fd8652a84667e9f366b49f1dc815f07416b395591c76d3a18f791c46b7f69` | 11,300 |
| `s09_report_check.py` | written after this record; its output records its digest | — |

**My raw outputs** are in `OUT/outputs/`. They keep machine paths, and are not for copying (PR-06).

| File | SHA-256 | Bytes |
| --- | --- | ---: |
| `s01-run1.json` | `4cbdefacea9e2446d9f20d65ca854b1f9570949f96b1f18a910aae0848e89219` | 64,401 |
| `s02-plan-keys.json` | `2c83b365bc5a10c93f4722798a06b6c2ceac0c93dc4facae89bd3ce6f9c6ba08` | 65,186 |
| `s03-python-inventory.json` | `9907843d137bfcf9a279b96e313a14b9fbe0f25822c52e32b7e211a885a73b0b` | 6,219 |
| `s04-source-and-git.json` | `02d383e36fe3b4ec207a33384c557231a204ae72054536c4e56822ad4ebc16e6` | 5,589 |
| `s05-macho-static.json` | `5260b96cf3cd5e418f825014823c0a2fecc38ea312aaa250cf15dd42e716c097` | 8,136 |
| `s06-observe-only-and-processes.json` | `93077d892d77b183b453ba62a6c878631f51d8c790b3e4d7572965017b7e3bae` | 4,096 |
| `s07-foreign-processes.json` | `aa874562a3d2d9932f4d94d1f835d543d02ed4145219f4c683bfbb4c96dff257` | 9,323 |
| `s08-final-recheck.json` | written last; its digest is not in this record | — |
| `pretty/*.pretty.json` | four reading copies; see the JSON form | — |
