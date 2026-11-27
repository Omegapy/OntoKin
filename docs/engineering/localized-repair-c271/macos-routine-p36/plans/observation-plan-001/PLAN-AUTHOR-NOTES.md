# Observation plan 001 for M0 and M1 at commit B: author's notes

W2, the independent author of stage S4 of gate MR (phase C271-P36, Director
`c271-p36-14f7f8b219db`), local mode, on the owner's macOS 26.6.2 arm64 host, 2026-11-27 UTC.
W2 is a subagent in a fresh context, with the session's model. It wrote none of the observer, the
contract, its amendment, MP's preparation, MH's records or MR's tooling, and it ran no
observation.

The plan is bound at commit B, `4ca781429c5411c67c0965bc69306b42c6cc74ad`, tree
`0935162c72fd9d804681e920da6f6d6e9066ff28`. It lies outside Git with its real paths. These notes
name places by label only.

| Label | Place |
| --- | --- |
| `<worktree>` | the C271 worktree at commit B |
| `<clone>` | the main clone; `<clone>/.git` is the common directory of `<clone>/.git/worktrees/c271`, which `<worktree>/.git` names |
| `<local>` | the working directory beside the clone |
| `<volume>` | the mount point of the external volume that holds `<worktree>`, `<clone>` and `<local>` |
| `<prefix>` | the installation prefix of the interpreter's framework and of its non-system libraries |
| `<package-manager>` | the package manager that owns `<prefix>` |
| `<framework>` | `<prefix>/Cellar/python@3.12/3.12.13/Frameworks/Python.framework/Versions/3.12` |
| `OUT` | `<local>/c271-p36/workers/W2-plan-001/`, the only place I wrote |

## 1. Result

| Item | Value |
| --- | --- |
| Plan | `OUT/observation-plan-001.json`: SHA-256 `cc1c2defd73d8d1ade22a8c772308c0e3d2fad3262a83c946c1733aecf429d5e`, 9,017 bytes, mode `0o644`, canonical JSON, schema `ontokin.current-host-readback-observation-plan/0.2.0` |
| Attempt | `<local>/c271-p36/evidence/observe-001`, absent; the evidence parent is empty |
| Boot | `kern.bootsessionuuid` `C90010BA-4DA9-475D-BBAB-CF1A9C40175A`, read when the plan was frozen (start 7, 18:56:41Z), checked against the plan by `static` (start 8), and read before and after its work by each of my scripts that ran (starts 3 to 7, 9 and 13), always equal; the same boot as MH's |
| `static` | exit 0, `STATIC_READY`, empty stderr, zero starts, `facts_sha256` `3f0624318211f82e76aaf408a98e2e0a82ec2147ed681682242f37c9343c4ddf` (`records/static-001.*`) |
| Source inventory | `OUT/source-inventory-001.json`: `95abd300edbb9930e67c569b726015964ab98f4ed0ede389da122bbb3f145c4c`, 96,238 bytes, 644 files. Byte-identical to MH's. |
| Python inventory | `OUT/python-inventory-001.json`: `c277bdd3ac6aa73105df3924707a271a402a0dc7c722be27a6834f2c78605633`, 776,209 bytes. Byte-identical to MH's; `compare_inventory` gives no row. |
| Dependency inventory | `OUT/dependencies-inventory-001.json`: `3545d5f920ac840804a9e25d28a87d623f96af71537fd3f020a0c1d743f82fb4`, 4,543 bytes. Byte-identical to MH's. |
| Launch record | `OUT/M0-LAUNCH.json` (SHA-256 `8530ebd7a091d83365dbcd61dc09c971807612b3568d16846ac18c7a218de7b5`, 17,592 bytes), with no plan digest in it; `OUT/M0-ENVIRONMENT.json` (`0ed78f47b1929634d65b6407b8e8daf047aeb2daa6b5c194c24e91a7b91ebcf2`, 96 bytes) |

No refusal occurred. This phase has no earlier plan and no refused plan.

## 2. Method

1. **Read**, with the agent's file-read tool: `<worktree>`'s AGENTS.md and ROLE.md, PROTOCOL
   sections 4 and 5 (the whole file), the worker template; MR-PLAN (all, with sections 2, 3, 6, 8,
   9 and 12), PHASE.json and START-INVENTORY-DISPOSITION.json (D-P1 to D-P7); CONTRACT.md (all,
   sections 4 and 7 above all); AMENDMENT-001.md; W3-OBSERVER.md (all; sections 1, 2, 5, 6 and 7
   as the implemented rules); the observer's whole source; MH's observation plan 001, its notes
   and M0-LAUNCH.json, PLAN-REVIEW-001.md, PLAN-REVIEW-DISPOSITION-001.json, MH's HOST (portable
   copy) and HOST-REVIEW-DISPOSITION-001.json; FAILURE-CAPTURE.md; the MR tooling README's reuse
   table; N34-M's Git section. I read MH's exact inventories, plan and HOST under
   `<local>/c271-p35/` only as data.
2. **The two inventories**, through the observer's own `source-inventory` and `python-inventory`
   commands, each launched as W3-OBSERVER section 1 requires: `/usr/bin/env -i` with exactly the
   five declared variables, then `<worktree>/.venv/bin/python -I -S -B <observer> …`. Both write
   only their absent output path and start nothing.
3. **A static read of Git's files** by my own `scripts/w2p_git_static.py`, which starts no Git
   (section 4).
4. **The dependency inventory** by `scripts/w2p_author.py deps`, from the installed reader tree
   with the observer's own helpers, written with the observer's `write_new` (section 5).
5. **The comparison with MH's exact inventories** by `w2p_author.py compare`, with the observer's
   `compare_inventory` and a byte comparison (section 5).
6. **The plan** by `w2p_author.py plan`, first `--preview` (it writes only its record), then
   `--write`, bound to the preview's canonical digest so that no fact could change between the
   two runs. The script loads the observer by its path with `importlib.util.spec_from_file_location`
   (under `-B` the load writes no bytecode) and takes every value that the schema derives from
   the observer from the observer's own constants and helpers: `PLAN_SCHEMA`, `CONTRACT`,
   `PROFILE`, `EXECUTOR`, `ENVIRONMENT`, `LIMITS`, `NODE_VERSION`, `read_proc_translated`,
   `read_boot_session_uuid`, `read_os_identity`, `read_file`, `tree_entries`, `_ancestors`,
   `output_paths` and `expected_commands`. Before writing, it runs the observer's own checks in its
   process: `_resolved`, `_plan_shape`, `check_source`, `check_runtime` (with the receipt rule),
   `check_dependencies`, `check_git_binding`, the failure-capture binding, a fresh
   `python_inventory` with `compare_inventory` and a canonical-byte comparison, and
   `verify_packages`. After writing, it runs `validate_plan` with the digest of the written bytes.
7. **`static`**, once, launched exactly as `observe` will be: same interpreter, flags, observer,
   plan, cwd (the evidence parent) and environment; only the subcommand differs, and its stdout
   and stderr went to `OUT/records/`. Only `static` checks what my process cannot check for the
   observer: its environment, launcher, loaded modules and the supervisor import.
8. **The check that only `observe` makes** (`check_loaded_modules` after the supervisor import),
   reproduced by `w2p_author.py observe-only`: the real `load_darwin_supervisor`, then
   `check_loaded_modules` on every loaded module except my script's `__main__` (section 7).
9. **M0-LAUNCH.json and M0-ENVIRONMENT.json** by `scripts/w2p_launch_record.py`, from the plan
   after `validate_plan`, the observer's constants and the retained `static` result, so that no
   path or constant was retyped.
10. **Final rechecks** after `static` and the supervisor import: the Python and source inventories
    again through the observer, compared byte for byte with the frozen ones, and the static Git
    read again.

Every script of mine refuses to run without `-I -S -B`, uses the standard library only, holds no
machine path (every path is an argument), writes only absent files with exclusive creation, and
installs an audit hook that refuses every process-creation event of the runtime and every ctypes
lookup of a process-creation function. No hook recorded an event.

## 3. Each key: its value, where it comes from, how it was checked

| Key | Value | Source | Verification |
| --- | --- | --- | --- |
| `schema`, `contract`, `profile`, `executor` | `…observation-plan/0.2.0`, `ontokin.current-host-readback/0.2.0`, `darwin-arm64-v1`, `macos-arm64-local` | the observer's constants | `_plan_shape`; `static` |
| `environment` | `PATH=/usr/bin:/bin`, `LANG=C.UTF-8`, `LC_ALL=C.UTF-8`, `TZ=UTC`, `UV_THREADPOOL_SIZE=2` | `ENVIRONMENT` | `_plan_shape` (PLAN-ENVIRONMENT); `static` checked its own process against it |
| `platform` | Darwin, release `25.6.0`, arm64, `proc_translated` 0, boot `C90010BA-4DA9-475D-BBAB-CF1A9C40175A` | `os.uname()`, `read_proc_translated()`, `read_boot_session_uuid()` at the freeze | the boot read again by my later scripts (starts 9 and 13), always equal; `static` (`check_platform`) |
| `os.system_version` | `/System/Library/CoreServices/SystemVersion.plist`, `6151cb88…04a1`, 603 bytes, `0o444` | `read_os_identity()` | macOS 26.6.2, build 25G83, no `ProductVersionExtra`; `static` (OS-SYSTEM-VERSION) |
| `os.cryptex` | present, at the copy's canonical path `/System/Volumes/Preboot/Cryptexes/OS/System/Library/CoreServices/SystemVersion.plist`, the same bytes, size and mode | `read_os_identity()` | one hop, `/System/Cryptexes/OS` → `../../System/Volumes/Preboot/Cryptexes/OS` (finding F1, decision D-10); `static` (OS-CRYPTEX) |
| `source.root` | `<worktree>` | argument | `canonical_path` equality |
| `source.commit` | B | the brief | HEAD read from Git's files by the observer's `git_head` (in `check_source` and `static`) and by my reader: `<worktree>/.git` names `<clone>/.git/worktrees/c271`, whose `HEAD` is `ref: refs/heads/work/c271-missing-import-digest-control`; the ref is a loose file in the common directory holding B; no per-worktree ref and no `packed-refs` entry for it |
| `source.tree` | `0935162c…` | the brief | my static Git read (section 4); M0 does not check it (W3-OBSERVER Q8), and HOST records it as a planned value |
| `source.inventory` | `OUT/source-inventory-001.json` | the observer's `source-inventory` | `check_source` (SOURCE-SET and every binding); `static`; recomputed at the end, byte-identical |
| `observer` | `<worktree>/prototypes/static_tray_v01/current_host_observation_v02.py`, `471a9547…2788`, 162,557 bytes, `0o644` | `read_file` | equals the source inventory's binding of the entry point and its blob at B (`e59d6292…`), which is its blob at C, the file that N34-M and MH reviewed |
| `python.venv`, `framework`, `version` | `<worktree>/.venv`; `<framework>`; `3.12.13` | arguments; pyvenv.cfg's `version` | `canonical_path` equality; my interpreter's `sys.version_info` and `sys.base_prefix` agree; `_plan_shape`; `static` (`check_launcher`) |
| `python.inventory` | `OUT/python-inventory-001.json`, `c277bdd3…` | the observer's `python-inventory` | byte-identical to MH's; a fresh `python_inventory` in the author process gives no row and identical canonical bytes; the seven packages verify; recomputed at the end, byte-identical |
| `runtime.directory`, `root_mode`, `bin_mode` | `<local>/c271-macos/node-v24.22.1-darwin-arm64`, `0o755`, `0o755` | `tree_entries`, `lstat` | exactly `{bin/, bin/node, NODE-SOURCE.json}`, no link or `.DS_Store`, one link per file; equal to MP's exact Node apply plan |
| `runtime.version` | `v24.22.1` | `NODE_VERSION` | `_plan_shape` (RUNTIME-VERSION, MC33) |
| `runtime.executable` | `6f320694…f329`, 122,545,856 bytes, `0o755` | `tree_entries` | `check_runtime`: thin `MH_MAGIC_64`, cputype `0x0100000c`, subtype 0, `MH_EXECUTE`, 21 commands in the allow-list, four system dylibs (CoreFoundation, Security, `libc++`, `libSystem`); the receipt rule passes (`INSTALLED_EXACT`) |
| `runtime.node_source` | `e928a8ec…9ea2c`, 976 bytes, `0o644` | `tree_entries` | `check_node_source`; signature check `not_performed`, recorded, not refused (D-02) |
| `runtime.archive` | `<local>/c271-p34/downloads/node/node-v24.22.1-darwin-arm64.tar.gz`, `89c68259…c0a7`, 53,062,778 bytes, `0o444` | `read_file` | rehashed; the adopted pin (RUNTIME-ARCHIVE); equal to the apply plan's `archive` |
| `runtime.install` | plan `<local>/c271-p34/plans/node-install-plan.json` (`1fee042d…`, 956,650 bytes, `0o644`); result `<local>/c271-p34/receipts/node-install-result.json` (`65caf77a…`, 2,897 bytes, `0o600`) | MP's exact apply plan and receipt | listed with these digests in `<local>/c271-p34/plans/SHA256SUMS`, MP's `plans/EXACT-PLANS-SHA256SUMS.txt` and `EXACT-RECEIPTS-SHA256SUMS.txt`; `check_runtime` |
| `dependencies.root` | `<local>/c271-macos/reader-c195` | MP's exact reader apply plan | 24 files and 13 directories, no link or `.DS_Store` |
| `dependencies.inventory` | `OUT/dependencies-inventory-001.json` | written by me (section 5) | `check_dependencies`; `static` |
| `dependencies.install` | plan `<local>/c271-p34/plans/reader-install-plan.json` (`ff5a95da…`, 158,115 bytes, `0o644`); result `<local>/c271-p34/receipts/reader-install-result.json` (`03222a85…`, 4,116 bytes, `0o600`) | MP's exact apply plan and receipt | as for the runtime; `INSTALLED_EXACT`; `check_dependencies` |
| `git` | `/Library/Developer/CommandLineTools/usr/bin/git`, `be4afb2b003904725826250de9fb76567bbacf82323457b5a1ec26706b66bcae`, 7,604,272 bytes, `0o755` | `read_file` | section 6; `check_git_binding`; `static` |
| `commands` | `git_version`, then `node_version` | `expected_commands(plan)` | equality in my script, `_plan_shape` (PLAN-COMMANDS) and `static` |
| `evidence.parent` | `<local>/c271-p36/evidence` | the brief (created by the Director) | canonical, a directory, empty at every check, the last after the final recheck |
| `evidence.ancestors` | seven rows, below | `_ancestors(parent)`, the observer's function | read twice in the write run, equal; `static` (EVIDENCE-ANCESTORS); none is a link |
| `evidence.attempt` | `<local>/c271-p36/evidence/observe-001` | chosen by me, as MH's name | an absent direct child; `static` (EVIDENCE-FRESH); absent at the end |
| `evidence.outputs` | the fixed topology | `output_paths(attempt)` | `_plan_shape` |
| `failure_capture.procedure` | `<worktree>/docs/engineering/localized-repair-c271/macos-qualification-p35/tooling/FAILURE-CAPTURE.md`, `f387fb3ec0ed306366f6d3f22820ec344f1ac843008775475258c5de9634c99c`, 13,147 bytes, `0o644` | `read_file` | MH's procedure at its committed path, unchanged: its blob at B is `6ce5a793…`, the same as at C, and the worktree file equals it; the same digest as MR's tooling README and MH's records; outside the attempt |
| `limits` | the 15 fixed limits | `dict(LIMITS)` | `_plan_shape` |

**The evidence ancestors**, sorted by path (device, inode, mode):

| Path | Device | Inode | Mode |
| --- | ---: | ---: | --- |
| `/` | 16777234 | 2 | `0o755` |
| `/Volumes` | 16777234 | 18343 | `0o755` |
| `<volume>` | 16777244 | 2 | `0o775` |
| `<local>/..`, the directory that holds the clone and `<local>` | 16777244 | 7019967 | `0o755` |
| `<local>` | 16777244 | 14022344 | `0o755` |
| `<local>/c271-p36` | 16777244 | 16455187 | `0o755` |
| `<local>/c271-p36/evidence` | 16777244 | 16455190 | `0o755` |

The evidence lies on device 16777244, the external volume, as D-P6 records.

## 4. Commit B, its tree and the worktree, read without Git

`scripts/w2p_git_static.py` read Git's files directly: run 001 before the plan
(`records/git-static-001.json`) and run 002 after `static` and the supervisor import
(`records/git-static-002-final.json`), with the same result.

- **HEAD** resolves to B, as section 3 says. The Git directory's backlink names `<worktree>/.git`,
  and there are no alternates.
- **Commit B** is a loose object whose name recomputes from its bytes. It names tree `0935162c…`
  and one parent, `d3b622d61745259c3477bc94be0fb4da05c23c56`. It is unsigned, committed at
  2026-11-27T18:40:35Z, with the subject "C271-P36: commit B, the start-and-write inventory and
  the reviewed MR tooling".
- **The pack.** One pack of 27,674 objects. Its version-2 index checksum is valid, its trailer
  equals the index's pack checksum, and the SHA-1 of its whole content equals the trailer. Every
  object read (217 loose, 2,161 packed in run 001) had its name recomputed from its type, size and
  bytes, `OFS_DELTA` and `REF_DELTA` objects included.
- **The tree:** 2,655 trees and 23,012 entries: 23,004 regular files `100644`, 2 `100755` and 6
  links.
- **The worktree,** apart from `.git` and `.venv` at its root, holds 23,012 files and links (6
  links) in 2,654 directories. Each equals its tree entry by blob name and mode. No path is
  missing, extra or changed, and there is no bytecode, `.DS_Store`, special file, multi-link file
  or empty directory.
- **The index** (version 2, 23,012 entries, valid checksum) equals the tree, with no conflict stage
  and no assume-valid, skip-worktree or intent-to-add entry. Its `TREE` extension's root is
  `0935162c…`. It also carries a 516-byte `REUC` extension, as MH's did; that records earlier
  conflict resolutions and does not make it differ from the tree.
- **From C to B**, the first-parent chain is four commits, `2cd69829` (MH's outcome records),
  `47cc579f` (MH's closing record), `d3b622d6` (the declaration of gate MR) and B. The tree
  difference is 528 paths: 522 added and 6 changed, none removed, all under `docs/`: 472 under
  `macos-qualification-p35/`, 49 under `macos-routine-p36/`, and `docs/workflow/CURRENT.json`,
  `docs/workflow/memory.json` and five files under `docs/workflow/tasks/C271/`. None of them is in
  the observer's source set (its four trees, sixteen roles and three optional files).
- **Named files at B,** each equal to its worktree bytes, and each with the same blob at C:

  | File | Git blob | SHA-256, bytes, mode |
  | --- | --- | --- |
  | `…/macos-qualification-p35/tooling/FAILURE-CAPTURE.md` | `6ce5a7931c662c40cb11fe0600e7d0b12f368fda` | `f387fb3e…c99c`, 13,147, `0o644` |
  | `…/macos-qualification-p35/tooling/capture_probe.py` | `d7ca23f9489075c9ae9818083c30caa4867dedf2` | `db5fb525…048f`, 29,076, `0o644` |
  | `…/macos-implementation-p33/ADOPTION-AMENDMENT-001.json` | `0431fab527c6bb69d52e224cac73c524ea6f70a3` | `872312ed80a63fbb196c17ace42e786b7fe757b710eff41139b125dfaa507937`, 5,396, `0o644` |
  | `docs/engineering/ownership-recovery-c195/evidence/recorded-evidence.tar.xz` | `6d062bc9eefadb84c541ae5f0375c21a82c4bbca` | `b1e54a6c…a0c9`, 2,611,764, `0o644` |
  | `docs/engineering/static-tray-qualification-c199/EXTERNAL-INPUTS.json` | `64b7238e1aaf4305f090748b3b65857ecbab3fcf` | `21fd6bad…d5`, 19,901, `0o644` |
  | `tools/native-reader-verification-macos-arm64-cp312.lock` | `c29341218d876b6e0d727edcd3ac883ddccc6ca4` | `b1e3e866…a81c`, 799, `0o644` |
  | `prototypes/static_tray_v01/supervisor_darwin_v01.py` | `4765dd892785e7d3b41619a4463fd94822444b1c` | `bd4a5e3f…bd2b`, 10,621, `0o644` |
  | `prototypes/static_tray_v01/supervisor.py` | `b02086915dcf28e2e915d7e3d2b66d253688d331` | `c47b84ab…5a10`, 11,286, `0o644` |

## 5. The inventories, and their comparison with MH's

`records/compare-001.json` compares each of mine with MH's exact file under
`<local>/c271-p35/workers/W2-plan-001/`.

**Python installation inventory: no difference, so there is no file to explain.** The canonical
bytes are identical (`c277bdd3…`, 776,209 bytes), and the observer's `compare_inventory` returns
no row: no tree entry, external library, image, link hop or selection key differs. The figures are
therefore MH's:

- the framework version directory: 3,478 files, 414 of them bytecode in 37 `__pycache__`
  directories, 5 links, 305 directories and 72,433,430 file bytes;
- the `.venv`: 297 files with no bytecode, 3 links, 45 directories and 13,983,870 file bytes;
- 111 closure images (2 `MH_EXECUTE`, 25 `MH_DYLIB`, 84 `MH_BUNDLE`), 5 external libraries
  under `<prefix>/Cellar` (the `<package-manager>`'s), 6 closure link hops, 81 `LC_RPATH` entries,
  26 `@loader_path` references, 127 system references, and a selection chain of 4 hops;
- the seven pinned packages, which `verify_packages` accepts.

That nothing differs means that, since MH froze this inventory, nothing has added, removed or
changed a file in either tree, bytecode included. The inventory was computed five times in this
stage, always with the same result: by the observer's command (18:52:43Z), in the preview and
write runs (18:56:15Z and 18:56:41Z), inside `static` against the frozen file (18:56:53Z), and by
the observer's command again (18:59:48Z).

**Source inventory: identical** (`95abd300…`, 96,238 bytes; 644 files, 13,588,394 bytes). No path
was added, removed or changed. Section 4 explains why: every commit from C to B changes only
documents under `docs/` that lie outside the source set.

**Dependency inventory: identical** (`3545d5f9…`, 4,543 bytes), and its schema requires it
(`dependencies.inventory`, a `dependencies/0.2.0` document `{schema, files, directories, archive}`).
I derived it again, without reading MH's:

- `files` and `directories` come from the observer's `tree_entries` over the installed reader tree
  (24 files, all `0o644`, and 13 directories, all `0o755`; private files, no link);
- the 24 names, SHA-256 values and sizes equal the C199 pins that `_historical_dependencies` reads
  from `EXTERNAL-INPUTS.json` (`21fd6bad…`), and the directories are exactly the necessary set;
- `archive` is the C195 archive's descriptor from MP's exact reader apply plan, rehashed: it is the
  contract's pin `b1e54a6c…a0c9`, 2,611,764 bytes, `0o644`, at
  `<worktree>/docs/engineering/ownership-recovery-c195/evidence/recorded-evidence.tar.xz`;
- the apply plan's destination, files, directories, root mode, purpose and source root equal it.

## 6. The Git binding (N-07)

The plan binds `/Library/Developer/CommandLineTools/usr/bin/git`, the developer tools' Git
implementation that N34-M read (its section 2.9). Rehashed: SHA-256
`be4afb2b003904725826250de9fb76567bbacf82323457b5a1ec26706b66bcae`, 7,604,272 bytes, `0o755`, the
figures of N34-M and of MH's plan and HOST. Its first bytes are a fat magic (`macho_magic_kind`
gives `fat`), as N34-M found; it is bound by its bytes and never parsed. `check_git_binding`
accepts it: it is not the `/usr/bin/git` dispatcher, a link, a hard link of the dispatcher, or the
dispatcher's bytes. The plan freezes only the version grammar `git-version-line-v1` (Q6).
M0-LAUNCH.json records the line that MH's M0 observed for these bytes, `git version 2.50.1 (Apple
Git-155)`, as a prediction for the HOST review, not as a predicate.

## 7. `static`, and the check that only `observe` makes

- **`static`** ran once (start 8), from the evidence parent as cwd, exactly as M0-LAUNCH.json gives
  it apart from the capture paths: exit 0, `STATIC_READY`, zero starts, empty stderr, 0.44 s. The
  evidence parent stayed empty, the attempt absent, and no `__pycache__` appeared under
  `prototypes/`. Its stdout is `records/static-001.stdout.txt` (1,650 bytes).
- **The loaded-module check after the supervisor import** (start 9): `load_darwin_supervisor`
  bound and imported the four supervisor files from `<worktree>`; `run_process`'s code comes from
  `supervisor_darwin_v01.py`; `check_loaded_modules` accepted all 86 loaded modules other than my
  script's `__main__`: each is a file of the frozen framework inventory or a bound source file
  without bytecode. No bytecode directory appeared. The import added only standard-library
  modules and the four supervisor modules.

## 8. Differences from MH's plan

`records/author-preview-001.json` and `records/author-write-001.json` compare my plan with MH's
exact plan (`b8cd6449…`, the digest of MH's review record) leaf by leaf. The plans have the same
size, 9,017 bytes. There are 37 differing leaves, all of them paths, the commit and tree, or the
two new ancestors:

- `source.commit` and `source.tree`: C and `ea10cd94…` become B and `0935162c…`;
- `source.inventory.path`, `python.inventory.path` and `dependencies.inventory.path`: MH's directory
  becomes `OUT`; the three digests, sizes and modes are unchanged;
- `evidence.parent`, `evidence.attempt` and the 24 leaves of `evidence.outputs`, and the two
  commands' `cwd`: `<local>/c271-p35/evidence` becomes `<local>/c271-p36/evidence`;
- `evidence.ancestors[5]` and `[6]`: the paths and inodes of `<local>/c271-p36` (16455187) and its
  `evidence` (16455190), in place of MH's `c271-p35` directories.

Everything else is identical: the schema, contract, profile, executor and environment, the
platform with the boot, the OS identity, the observer, the Python installation, the runtime with
MP's exact plans and receipts and the Node archive, the reader tree with its plan and receipt, the
Git binding, the failure-capture procedure, the limits, and every other field of both commands.

**MR's decisions D-P1 to D-P7 and this plan.** They are for the freeze (R1 and R2), and none of
them changes M0 or M1, whose environment and commands are the observer's constants:

- the plan's `PATH` is already `/usr/bin:/bin` (D-P1's default), and both commands start their
  programs by absolute path;
- M0 is already launched from `env -i` with a closed environment (D-P2);
- M0's Git start runs with `GIT_CONFIG_NOSYSTEM=1` and `GIT_CONFIG_GLOBAL=/dev/null`, so it reads
  no global configuration (D-P3);
- every start uses `-B` (D-P4);
- this Python inventory becomes HOST's, against which the freeze compares (D-P5);
- the evidence ancestors bind device 16777244 (D-P6).

## 9. Every process I started

**Forbidden starts: none.** No Git of any kind, no Node, no `ldd`, `codesign` or `otool`, no
`observe`, no routine driver, no unit test and no `tools/check_local.py`.

**Framework-interpreter starts: 13 until these notes, and one after them (start 14).** Each ran
in the foreground from `/usr/bin/env -i` with exactly the five declared variables, so `env`
executed the interpreter in its own process; the framework launcher then executed its
`Python.app` image within that same process. Every start carried `-I -S -B`. The observer's
commands ran as `<worktree>/.venv/bin/python`, as W3-OBSERVER section 1 requires. My own scripts
ran as `python3`, as the brief names it: the `python3` on the session's `PATH`, given under
`env -i` by its absolute path `<prefix>/opt/python@3.12/libexec/bin/python3`, which resolves
through `<prefix>/opt/python@3.12` → `../Cellar/python@3.12/3.12.13` and `libexec/bin/python3` →
`../../Frameworks/Python.framework/Versions/3.12/bin/python3.12`, the same framework launcher
`<framework>/bin/python3.12`. Times are UTC on 2026-11-27, from `records/starts.log` (epoch
seconds) and the scripts' own records; each exit status is also in `records/*.exit.txt`.

| # | Start (UTC) | Command | cwd | Exit | PID |
| ---: | --- | --- | --- | ---: | ---: |
| 1 | 18:52:43 | observer `source-inventory` | `OUT` | 0 | 20997 |
| 2 | 18:52:43 | observer `python-inventory` | `OUT` | 0 | 20998 |
| 3 | 18:53:01 | `w2p_git_static.py`, run 001 | `OUT` | 0 | 21019 |
| 4 | 18:55:39 | `w2p_author.py deps` | `OUT` | 0 | 21170 |
| 5 | 18:55:50 | `w2p_author.py compare` | `OUT` | 0 | 21191 |
| 6 | 18:56:15 | `w2p_author.py plan --preview` | `OUT` | 0 | 21253 |
| 7 | 18:56:41 | `w2p_author.py plan --write` | `OUT` | 0 | 21324 |
| 8 | 18:56:53 | observer `static` | the evidence parent | 0 | 21346 |
| 9 | 18:57:33 | `w2p_author.py observe-only` | `OUT` | 0 | 21398 |
| 10 | 18:58:36 | `w2p_launch_record.py` | `OUT` | 0 | 21452 |
| 11 | 18:59:48 | observer `python-inventory`, final recheck | `OUT` | 0 | 21528 |
| 12 | 18:59:48 | observer `source-inventory`, final recheck | `OUT` | 0 | 21529 |
| 13 | 18:59:49 | `w2p_git_static.py`, run 002, final recheck | `OUT` | 0 | 21530 |
| 14 | after these notes | `w2p_sums.py`: the hygiene scan of these notes and my scripts, then `SHA256SUMS.txt` | `OUT` | in my return | in my return |

So the observer's commands ran five times: `static` once, `source-inventory` twice and
`python-inventory` twice.

**Shells and utilities.** Until these notes were written: 31 shell commands through the agent's
Bash tool, each one `zsh`. One of them started nothing, because the shell refused an unquoted glob
before starting `grep`. Inside the others, besides the 13 interpreter starts, 122 utility
processes, all read-only except the one `mkdir` that made `OUT`, `OUT/scripts` and
`OUT/records`: `ls` 26, `grep` 21, `cat` 17, `tail` 16, `sed` 13, `head` 11, `cut` 8, `wc` 4,
`cmp` 2, `mkdir` 1, `tr` 1, `sort` 1 and `uniq` 1. Shell redirections wrote my records; shell
built-ins (`cd`, `print`, `echo`, `umask`, `whence`, `wait`, `kill -0`, `zmodload`) started
nothing. After these notes: one shell with one `grep` that scans these notes for machine paths and
names, then one shell with start 14 and two `ls` listings (`OUT` and the evidence parent).

A shell's exit status is that of its last command. Some shells ended non-zero only because that
command was an `ls` of a path I expected to be absent (the package manager's `bin/python3`; the
attempt) or a `grep -c` that counted zero `__pycache__` entries. Every interpreter start exited 0
(`records/*.exit.txt`).

The agent harness's wrapper around each shell command may start processes that I cannot see. The
harness also attached a Git status summary of the main clone to my initial context; no command of
mine produced it.

**Nothing of mine remains.** Every start ran in the foreground and its shell waited for it. After
start 13, `kill -0` failed for each of the 13 recorded PIDs.

**Effect on bound state.** The final Python and source inventories equal the frozen ones byte for
byte, the final static Git read finds the worktree still equal to tree `0935162c…` with no
bytecode or untracked file, the evidence parent is empty, and the attempt is absent. Nothing was
written under `<local>/c271-p35/`, `<local>/c271-p34/`, `<local>/c271-macos/` or `<worktree>`.

## 10. Deviations from the brief

Each is without effect on a bound input:

- **D1.** `M0-ENVIRONMENT.json` is an extra file: FAILURE-CAPTURE FC-K3 asks for the environment
  as a frozen file with its SHA-256. Its bytes are the canonical declared environment, the same
  digest (`0ed78f47…`) as MH's environment file. The Director may use it or write its own.
- **D2.** `static`'s stdout and stderr went to `OUT/records/`, not beside the attempt, so that the
  evidence parent stays empty for the Director.
- **D3.** I added a preview run, the observe-only check and three final rechecks, all of the
  allowed kinds.
- **D4.** `M0-LAUNCH.json` gives the argv without its last element, the digest, and a shell form
  with `"$PLAN_SHA256"`, as the brief asks, where MH's record gave the complete argv.

## 11. Open questions for the review

- **Q-1. FAILURE-CAPTURE's literal phase paths.** The procedure is reused unchanged at its
  committed path and digest. Its text names `<local>/c271-p35/evidence/` as the place of FC-K5's
  readback record, and the capture record's schema is `ontokin.c271.p35-failure-capture/1`. MR-PLAN
  section 5 forbids editing MH's file. My reading for MR: the readback and capture records go under
  this phase's evidence parent, `<local>/c271-p36/evidence/`, never inside an attempt, with the
  schema name kept. The review should confirm or correct that reading, and the Director record it.
- **Q-2. The launch form without the digest.** Does `argv_without_digest` with exactly one digest
  argument from the review record give W3-OBSERVER section 1's launch? The launch record names no
  digest, but `records/static-001.stdout.txt` and these notes do, as author's records; the purpose
  of M0-LAUNCH.json says the digest comes from the review record only.
- **Q-3. My scripts' interpreter.** I took the brief's `python3 -I -S -B` as the framework
  interpreter by the `python3` name on the session's `PATH`, given by absolute path under `env -i`
  (section 9), where MH's author used the `.venv` launcher. Both reach the same launcher and
  `Python.app` image. The review may confirm that this meets MR-PLAN sections 3 and 6.
- **Q-4. MH's PR-03.** An owner's job outside the project ran the bound interpreter with
  `PYTHONDONTWRITEBYTECODE=1` and without `-B`. I listed no processes, so I cannot say whether it
  still runs. The inventory has stayed byte-identical to MH's. The Director's `static` before
  `observe` and M0's own checks refuse if a bytecode file appears.
- **Q-5. MH's PR-02.** The empty stderr of both `--version` starts was a prediction at MH; MH's M0
  then observed it for the same bytes and environments. Its classification (a refusal for a
  non-empty stderr has its cause in the implementation's constants, so the phase stops) fits
  MR-PLAN section 9 too; the Director may adopt it again before the run.
- **Q-6. MH's PR-01.** The adoption record of P33-AMENDMENT-001 is still bound to the observation
  plan only through the commit and the tree. Section 4 shows its blob at B equals its blob at C
  and the worktree file. The S6 configuration binds its bytes.
- **Q-7. Facts that change without a file edit.** A reboot (the plan binds the boot) or a remount
  of the external volume (the ancestors bind its device) makes M0 refuse, which fails closed. The
  value of `__CF_USER_TEXT_ENCODING` is not a plan member; HOST records it, and the HOST review can
  compare it with MH's HOST.
- **Q-8. The cwd and the capture paths are my choice.** The cwd of `static` and `observe` is the
  evidence parent; the capture files are the siblings that M0-LAUNCH.json names
  (`observe-001.static.*` and `observe-001.observe.*`), each absent now. The observer constrains
  neither.

## 12. Files

All under `OUT`. `SHA256SUMS.txt` lists every file I wrote there with its SHA-256, except itself.

| File | Role |
| --- | --- |
| `observation-plan-001.json` | the plan, bound by path; its digest goes on the command line from the review record |
| `source-inventory-001.json`, `python-inventory-001.json`, `dependencies-inventory-001.json` | the plan's bound inventories |
| `M0-LAUNCH.json`, `M0-ENVIRONMENT.json` | the launch of `static` and `observe`, the expected starts and outputs, the preconditions; the frozen environment |
| `PLAN-AUTHOR-NOTES.md` | this file |
| `scripts/w2p_git_static.py`, `scripts/w2p_author.py`, `scripts/w2p_launch_record.py`, `scripts/w2p_sums.py` | my scripts, standard library only, with no machine path |
| `records/` | each start's stdout, stderr and exit status; `starts.log`; `git-static-001.json` and `git-static-002-final.json`; `deps-001.json`; `compare-001.json`; `author-preview-001.json` and `author-write-001.json` (every fact and check); `static-001.*`; `observe-only-001.json`; `launch-001.*`; `python-inventory-002-final.json` and `source-inventory-002-final.json` |

The JSON files and records keep machine paths and are not for copying; these notes and the
scripts hold none.
