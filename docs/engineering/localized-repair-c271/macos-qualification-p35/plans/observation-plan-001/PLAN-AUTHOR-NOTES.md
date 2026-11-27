# Observation plan 001 for M0 and M1: author's notes

W2, the independent author of gate MH (phase C271-P35, Director `c271-p35-e38e3aa82ade`), stage
S4 of MH-PLAN, local mode, on the owner's Mac (macOS 26.6.2, arm64), 2026-11-27 UTC. W2 is a
Claude Code subagent in a fresh context. It wrote none of the observer, the contract, its
amendment, MP's preparation, the tooling or the tooling's reviews.

The plan is bound at commit C, `0eb9a5517f4e19705178a2c59b8d8d33fb87867a`, tree
`ea10cd94c05a2ebbb44b3f83d4c96cb0a59baa2b`. It lies outside Git with its real paths. These notes
name places by label only.

| Label | Place |
| --- | --- |
| `<worktree>` | the C271 worktree at commit C |
| `<local>` | the working directory beside the clone |
| `<prefix>` | the installation prefix that holds the interpreter's framework and its non-system libraries |
| `<package-manager>` | the package manager that owns `<prefix>` |
| `<common-dir>` | the main repository's Git directory, the common directory of `<git-dir>` = `<common-dir>/worktrees/c271`, which `<worktree>/.git` names |

`OUT` below is `<local>/c271-p35/workers/W2-plan-001/`.

## 1. Result

| Item | Value |
| --- | --- |
| Plan | `OUT/observation-plan-001.json`: SHA-256 `b8cd6449aba958373f68715158402ed2e0e233e08213f3521bbc3d80cfe4c152`, 9,017 bytes, mode `0o644`, canonical JSON |
| `static` | exit 0, `STATIC_READY`, empty stderr, zero starts, `facts_sha256` `3867d3e8e2e6863b4cb657f67b1a33d5ac7dee32041250c6754389b86fc8b1dc` (`records/static-001.*`) |
| Source inventory | `OUT/source-inventory-001.json`: `95abd300edbb9930e67c569b726015964ab98f4ed0ede389da122bbb3f145c4c`, 96,238 bytes |
| Python inventory | `OUT/python-inventory-001.json`: `c277bdd3ac6aa73105df3924707a271a402a0dc7c722be27a6834f2c78605633`, 776,209 bytes. It equals MP's after-snapshot and N34-M's figure. |
| Dependency inventory | `OUT/dependencies-inventory-001.json`: `3545d5f920ac840804a9e25d28a87d623f96af71537fd3f020a0c1d743f82fb4`, 4,543 bytes (section 4) |
| Launch record | `OUT/M0-LAUNCH.json`, the exact command of the single `observe` |

No refusal occurred. There is no earlier plan and no refused plan.

## 2. Method

1. **Read.** MH-PLAN (all, sections 5 to 8 and 10 above all); W3-OBSERVER (all; section 2 for the
   schema and section 6 as the implemented Mach-O rule set, N-05); CONTRACT.md sections 3, 4, 7
   and 10; P07 QUALIFICATION-PLAN sections 2 to 4; MP's OUTCOME.json, CLOSING.json,
   EXACT-RECEIPTS-SHA256SUMS.txt and `plans/EXACT-PLANS-SHA256SUMS.txt`; N34-M-DISPOSITION.json
   and the N34-M review's sections on Git (2.9, N-07) and D-16 (2.1, (b), N-04); the tooling's
   README.md and FAILURE-CAPTURE.md; W5-PROVIDER section 2.1 for `dependencies/0.2.0` and
   `amendment_adoption`. In the observer's source: `_plan_shape`, `validate_plan`, `_resolved`,
   `static_check`, `static_observation`, `expected_commands`, `output_paths`, `LIMITS`,
   `canonical_path`, `python_inventory`, `source_inventory`, `source_paths`, `git_head`,
   `check_source`, `check_runtime`, `_install_receipts`, `check_dependencies`, `check_git_binding`,
   `check_launcher`, `check_loaded_modules`, `load_darwin_supervisor`, `write_new` and `main`.
2. **The two inventories**, through the observer's own commands, each launched as W3-OBSERVER
   section 1 requires: `env -i` with exactly the declared five variables, then
   `<worktree>/.venv/bin/python -I -S -B <worktree>/prototypes/static_tray_v01/current_host_observation_v02.py`.
   The Python inventory's digest was compared with `c277bdd3…` before anything else was done.
3. **A static read of Git's files** by my own script, `scripts/w2_git_static.py`, to verify the
   commit, the tree and the clean state without starting Git (section 3, `source`).
4. **The plan** by my own script, `scripts/w2_author_plan.py`, first in `preview` mode, which
   writes nothing, then in `write` mode. The script loads the observer by its path with
   `importlib.util.spec_from_file_location`, because `-I` puts no script directory on `sys.path`;
   under `-B` the load writes no bytecode. Every value that the schema derives from the
   observer comes from the observer's own helpers (section 3). Before the plan is written, the
   observer's own checks run on it in the script's process: `_resolved`, `_plan_shape`,
   `check_source`, `check_runtime`, `check_dependencies` and `check_git_binding`, the Python
   inventory recomputation with `compare_inventory`, and `verify_packages`; after it is written,
   `validate_plan` with its digest. The preview's canonical plan digest equals the written plan's
   (`b8cd6449…`), so no fact changed between the two runs.
5. **`static`**, once, exactly as `observe` will be launched (same interpreter, flags, observer,
   plan, digest, cwd and environment; only the subcommand differs, and its stdout and stderr went
   to `OUT/records/`). What the script's process cannot check for the observer, its environment,
   launcher, loaded modules and the supervisor import, only `static` checks.
6. **M0-LAUNCH.json** by `scripts/w2_launch_record.py`, from the plan after its digest was checked,
   the observer's constants and the retained static result, so that no path or digest was
   retyped.
7. **Final rechecks:** a second Python inventory and a second static Git read after `static` had
   imported the supervisor (section 8).

Every script refuses to run without `-I -S -B` and installs an audit hook that refuses every
process-creation event. None recorded one.

## 3. Each key: where its value comes from and how it was verified

| Key | Value | Source | Verification |
| --- | --- | --- | --- |
| `schema`, `contract`, `profile`, `executor` | `…observation-plan/0.2.0`, `ontokin.current-host-readback/0.2.0`, `darwin-arm64-v1`, `macos-arm64-local` | `PLAN_SCHEMA`, `CONTRACT`, `PROFILE`, `EXECUTOR` | `_plan_shape`; `static` |
| `environment` | the five declared variables | `dict(ENVIRONMENT)` | `_plan_shape` (PLAN-ENVIRONMENT) |
| `platform` | Darwin, release `25.6.0`, arm64, `proc_translated` 0, boot `C90010BA-4DA9-475D-BBAB-CF1A9C40175A` | `os.uname()`, `read_proc_translated()`, `read_boot_session_uuid()` | the boot read again at the end of each authoring run, equal; `static` (`check_platform`) |
| `os.system_version` | `/System/Library/CoreServices/SystemVersion.plist`, `6151cb88…04a1`, 603 bytes, `0o444` | `read_os_identity()` | macOS 26.6.2, build 25G83, no `ProductVersionExtra`; `static` (OS-SYSTEM-VERSION) |
| `os.cryptex` | present, at the copy's canonical path `/System/Volumes/Preboot/Cryptexes/OS/System/Library/CoreServices/SystemVersion.plist`, same bytes as the system file | `read_os_identity()` | one recorded hop, `/System/Cryptexes/OS` → `../../System/Volumes/Preboot/Cryptexes/OS` (finding F1, decision D-10); `canonical_path` equality; `static` (OS-CRYPTEX) |
| `source.root` | `<worktree>` | argument | `canonical_path` equality |
| `source.commit` | C | the brief | HEAD read twice from Git's files: by the observer's `git_head`, and by my reader. `<worktree>/.git` names `<git-dir>`; its `HEAD` is `ref: refs/heads/work/c271-missing-import-digest-control`; `<common-dir>/refs/heads/…` holds C. No per-worktree ref and no `packed-refs` entry exist. `check_source` (SOURCE-COMMIT); `static` |
| `source.tree` | `ea10cd94…` | the brief (the Director's Git read) | see "The tree" below |
| `source.inventory` | `OUT/source-inventory-001.json` | the observer's `source-inventory` | 644 files, 13,588,394 bytes. A fresh `source_inventory(<worktree>)` in the author process equals it. Every listed file equals its blob at C (my reader). `check_source`; `static` |
| `observer` | `<worktree>/prototypes/static_tray_v01/current_host_observation_v02.py`, `471a9547…2788`, 162,557 bytes, `0o644` | `read_file` | equals the source inventory's binding of the entry point, and the file N34-M reviewed (its section 7) |
| `python.venv`, `framework`, `version` | `<worktree>/.venv`; `<prefix>/Cellar/python@3.12/3.12.13/Frameworks/Python.framework/Versions/3.12`; `3.12.13` | arguments; `sys.version_info` of the same interpreter | `canonical_path` equality; `pyvenv.cfg`'s `version` and `executable`; `_plan_shape`; `static` (`check_launcher`) |
| `python.inventory` | `OUT/python-inventory-001.json`, `c277bdd3…` | the observer's `python-inventory` | equals the brief's figure (MP's after-snapshot and N34-M's). A fresh `python_inventory` in the author process gives no `compare_inventory` row and identical canonical bytes. The seven packages verify. The observer's command, run again after `static`, gives the same digest (section 8). |
| `runtime.directory` | `<local>/c271-macos/node-v24.22.1-darwin-arm64` | `destination` of MP's exact Node apply plan | exact layout `{bin/, bin/node, NODE-SOURCE.json}` by `tree_entries` (private files, no link, no `.DS_Store`) |
| `runtime.version` | `v24.22.1` | `NODE_VERSION` | `_plan_shape` (RUNTIME-VERSION, MC33) |
| `runtime.root_mode`, `bin_mode` | `0o755`, `0o755` | `lstat` | equal to the apply plan's `root_mode` and `directories` |
| `runtime.executable` | `6f320694…f329`, 122,545,856 bytes, `0o755` | `tree_entries` | equals the apply plan's `files`, MP's OUTCOME.json and N34-M. `check_runtime`: thin, `MH_MAGIC_64`, cputype `0x0100000c`, cpusubtype 0, `MH_EXECUTE`, 21 commands, four system dylibs with CoreFoundation among them (D-16; N34-M found it a plain `LC_LOAD_DYLIB`); the receipt rule passes |
| `runtime.node_source` | `e928a8ec…9ea2c`, 976 bytes, `0o644` | `tree_entries` | equals MP's OUTCOME.json; `check_node_source`. Its signature check is `not_performed`, which is recorded, not refused (D-02). |
| `runtime.archive` | `<local>/c271-p34/downloads/node/node-v24.22.1-darwin-arm64.tar.gz`, `89c68259…c0a7`, 53,062,778 bytes, `0o444` | `archive` of MP's apply plan | rehashed; equal to the adopted pin (RUNTIME-ARCHIVE); mode `0o444` as retained |
| `runtime.install` | plan `<local>/c271-p34/plans/node-install-plan.json` (`1fee042d…`, 956,650 bytes, `0o644`); result `<local>/c271-p34/receipts/node-install-result.json` (`65caf77a…`, 2,897 bytes, `0o600`) | the exact apply plan and receipt, not the portable or dry-run files | digests equal MP's EXACT-PLANS-SHA256SUMS.txt, `<local>/c271-p34/plans/SHA256SUMS` and EXACT-RECEIPTS-SHA256SUMS.txt; the plan's `report` names this receipt; `INSTALLED_EXACT`; `check_runtime` |
| `dependencies.root` | `<local>/c271-macos/reader-c195` | `destination` of MP's exact reader apply plan | `tree_entries`: 24 files, 13 directories, no link, no `.DS_Store` |
| `dependencies.inventory` | `OUT/dependencies-inventory-001.json` | written by W2 (section 4) | `check_dependencies`; `static` |
| `dependencies.install` | plan `<local>/c271-p34/plans/reader-install-plan.json` (`ff5a95da…`, 158,115 bytes, `0o644`); result `<local>/c271-p34/receipts/reader-install-result.json` (`03222a85…`, 4,116 bytes, `0o600`) | the exact apply plan and receipt | as for the runtime; `INSTALLED_EXACT`; `check_dependencies` |
| `git` | `/Library/Developer/CommandLineTools/usr/bin/git`, `be4afb2b…6bcae`, 7,604,272 bytes, `0o755` | `read_file` | section 7 (N-07); `check_git_binding` |
| `commands` | `git_version`, then `node_version` | `expected_commands(plan)` | equality checked in the script, by `_plan_shape` (PLAN-COMMANDS) and by `static` |
| `evidence.parent` | `<local>/c271-p35/evidence` | argument | canonical, a directory, empty at authoring, after `static` and at the end |
| `evidence.ancestors` | seven rows: `/` and `/Volumes` on device 16777234 (inodes 2 and 18343, `0o755`); the volume's mount point (inode 2, `0o775`), its child (inode 7019967), `<local>` (inode 14022344), `<local>/c271-p35` (inode 15728058) and the parent (inode 15728417), all on device 16777244 and `0o755` except the mount point | `_ancestors(parent)`, the observer's own function | `static` (EVIDENCE-ANCESTORS). None is a link. |
| `evidence.attempt` | `<local>/c271-p35/evidence/observe-001` | chosen by W2 | an absent direct child; `canonical_path(…, allow_absent=True)` equality; `static` (EVIDENCE-FRESH) |
| `evidence.outputs` | the fixed topology | `output_paths(attempt)` | `_plan_shape` |
| `failure_capture.procedure` | `<worktree>/docs/engineering/localized-repair-c271/macos-qualification-p35/tooling/FAILURE-CAPTURE.md`, `f387fb3e…c99c`, 13,147 bytes, `0o644` | `read_file` | equals `authoring/TOOLING-SHA256SUMS.txt` at C and its blob at C; outside the attempt |
| `limits` | the fixed limits | `dict(LIMITS)` | `_plan_shape` |

**The tree.** M0 reads HEAD's commit from Git's files, but checks neither the tree object nor
the absence of untracked files (W3-OBSERVER Q8). HOST therefore records the tree as a planned
value with its `tree_check` text, and the provider's bound Git reads verify it later (MC19). The
plan binds the tree only as a value that I checked statically, from the object store's files,
without starting Git:

- Commit C's object is a loose object, and its name recomputes from its bytes. It names tree
  `ea10cd94…` and one parent, `c81cf07b5386ea7eba7904f3ef5700709b84b366`. Its committer time is
  2026-11-27T04:17:03Z.
- The tree, read from the loose objects and the one pack, has 2,550 trees and 22,490 entries:
  22,482 regular files `100644`, 2 executable files and 6 links. Every object name was recomputed
  from its bytes.
- The worktree, without `.git` and `.venv` at its root, holds 22,484 files and 6 links in 2,549
  directories. Every one equals its tree entry by blob name and mode. No file is missing, extra or
  changed, and none is bytecode or `.DS_Store`.
- The index (version 2, 22,490 entries, valid checksum) equals the tree, has no conflict stage and
  no flagged entry, and its cache-tree root is `ea10cd94…`. It also carries a `REUC` (resolve-undo)
  extension, which records earlier conflict resolutions and does not make it differ from the tree.
- The static read ran twice, before the plan (`records/git-static-001.json`) and after `static`
  (`records/git-static-002-final.json`), with the same result.

## 4. The dependency inventory, a document W2 wrote

The schema needs `dependencies.inventory`, a `dependencies/0.2.0` document `{schema, files,
directories, archive}` (W3-OBSERVER section 2, W5-PROVIDER section 2.1). MP left none, only the
reader apply plan and its receipt, so I wrote it with the observer's `write_new`, in canonical
form. It carries no value of its own:

- `files` and `directories` come from `tree_entries` over the installed reader tree: 24 files and
  13 directories.
- The 24 names, SHA-256 values and sizes equal the C199 pins, which `_historical_dependencies`
  reads from `EXTERNAL-INPUTS.json`. The directories are exactly the necessary set.
- `archive` is the C195 archive's descriptor from MP's reader apply plan:
  `<worktree>/docs/engineering/ownership-recovery-c195/evidence/recorded-evidence.tar.xz`, SHA-256
  `b1e54a6c…a0c9` (the contract's pin), 2,611,764 bytes, `0o644`, rehashed. The archive lies in the
  worktree but outside the source set, so the source inventory does not bind it; its own descriptor
  does, and the clean-worktree check shows it equals its blob at C.
- `files`, `directories`, `archive` and the root mode equal the reader apply plan's, and
  `check_dependencies` accepts the plan with this inventory.

The review should check this document like the plan, since no earlier review covered it.

## 5. The adoption record of amendment 001

`docs/engineering/localized-repair-c271/macos-implementation-p33/ADOPTION-AMENDMENT-001.json` lies
outside the source set: `SOURCE_FILES` names the P31 adoption record, not this one, and the
source inventory does not list it (MH-PLAN section 6; W5's Q2). The plan's closed schema has no
member for it, and M0 never reads it. So the plan binds it only through `source.commit` and
`source.tree`, whose tree names its blob. That binding is as strong as the tree check, which M0
does not make and I made statically above:

| Property | Value |
| --- | --- |
| SHA-256, size, mode | `872312ed80a63fbb196c17ace42e786b7fe757b710eff41139b125dfaa507937`, 5,396 bytes, `0o644` |
| Git blob, in the worktree and in tree `ea10cd94…` | `0431fab527c6bb69d52e224cac73c524ea6f70a3`, mode `100644`, in the tree `61abde500dfb7283e22495b2759f459f26eea15e` of `macos-implementation-p33/` |

The configuration binds its bytes directly at S6, through `amendment_adoption` (W5-PROVIDER
section 2.1). Its descriptor there should equal the first row.

## 6. Frozen inventory figures (N-08)

These are the figures of the frozen documents, not those that W3-OBSERVER section 5 measured
before MP.

- **Python inventory** `c277bdd3…`, 776,209 canonical bytes:
  - framework version directory: 3,478 files (414 of them bytecode), 5 links and 305
    directories, 72,433,430 file bytes;
  - `.venv`: 297 files (no bytecode), 3 links and 45 directories, 13,983,870 file bytes;
  - 111 closure images, 5 external libraries under `<prefix>/Cellar` (`<package-manager>`'s
    libraries), 6 closure link hops, and a selection chain of 4 hops;
  - the seven pinned packages, with hashed RECORD rows: Pillow 139, attrs 36, jsonschema 45,
    jsonschema-specifications 29, referencing 20, rpds-py 10, typing_extensions 6, each with one
    unhashed row, RECORD itself.

  These agree with N34-M: 3,788 and 345 entries, and 111 images. W3-OBSERVER section 5 counted 84
  images and 5 `.venv` files, before MP installed the packages.
- **Source inventory** `95abd300…`: 644 files, 13,588,394 bytes. W3-OBSERVER section 5 measured
  639 files and 13,033,943 bytes at an earlier commit.

## 7. N-07: the bound Git is the file that N34-M read

The plan binds `/Library/Developer/CommandLineTools/usr/bin/git`, the path of N34-M's section 2.9.
The observer's `read_file` gives SHA-256 `be4afb2b003904725826250de9fb76567bbacf82323457b5a1ec26706b66bcae`
and 7,604,272 bytes, N34-M's figures. Its first bytes are a fat magic (`macho_magic_kind` gives
`fat`), as N34-M found: an x86_64 and an arm64 slice. No other candidate exists, so no load
commands had to be re-read. `check_git_binding` accepts it: it is not the `/usr/bin/git`
dispatcher, a link, a hard link of the dispatcher or the dispatcher's bytes. The plan freezes only
the version grammar (Q6). M0-LAUNCH.json records N34-M's static prediction,
`git version 2.50.1 (Apple Git-155)\n`, for the HOST review to compare with the recorded line.

## 8. Every start I made

**Forbidden starts:** none. No Git of any kind, no Node, no `ldd`, `codesign` or `otool`, and no
`observe`.

**Python starts: 9.** Each was `<worktree>/.venv/bin/python -I -S -B`, from `env -i` with exactly
the declared five variables. The framework launcher executed its `Python.app` image within the
same process. Times are UTC on 2026-11-27, and every exit status is recorded in
`records/*.exit.txt`.

| # | Start | Command | Exit | PID |
| ---: | --- | --- | ---: | ---: |
| 1 | 04:28:59 | observer `source-inventory` | 0 | not recorded |
| 2 | 04:29:07 | observer `python-inventory` | 0 | not recorded |
| 3 | 04:29:20 | `w2_git_static.py`, run 001 | 0 | 4326 |
| 4 | 04:33:59 | `w2_author_plan.py preview` | 0 | 4533 |
| 5 | 04:34:48 | `w2_author_plan.py write` | 0 | 4571 |
| 6 | 04:35:11 | observer `static` (cwd: the evidence parent) | 0 | not recorded |
| 7 | 04:36:54 | `w2_launch_record.py` | 0 | 4745 |
| 8 | 04:37:20 | observer `python-inventory`, final recheck | 0 | not recorded |
| 9 | 04:37:20 | `w2_git_static.py`, run 002, final recheck | 0 | 4783 |

So the observer's commands ran four times: `static` once, `source-inventory` once and
`python-inventory` twice.

**Other starts.**

- Until these notes were written, 21 shell commands through the agent's Bash tool, each one
  `zsh`. Command substitution in one of them forked one subshell.
- Inside those shells, 43 utility processes besides the nine Python starts, all read-only apart
  from the two `mkdir` that made `OUT`, `OUT/scripts` and `OUT/records`: `grep` 12, `cat` 9, `ls`
  8, `head` 8, `wc` 2, `mkdir` 2, `tr` 1 and `tail` 1. Each Python start went through `env -i`,
  which `exec`s the interpreter in the same process.
- Shell built-ins (`cd`, `echo`, `umask`, `kill -0`, `zmodload`) started nothing.
- After these notes, four more shell commands:
  - one `grep` that found no machine path or personal name in these notes;
  - one attempt to write SHA256SUMS.txt that the shell refused before starting anything, because
    it did not accept a recursive glob with qualifiers. No process started and nothing was
    written;
  - one `shasum -a 256` (a perl script) that wrote SHA256SUMS.txt, with plain globs for the file
    list;
  - one `shasum -a 256 -c` to verify it, and one `ls` listing.
- The agent harness's own wrapper around each shell command may start processes that I cannot
  see. The harness also attached a Git status summary of the main clone to my initial context,
  labelled as taken at the start of the conversation. No command of mine produced it.

**Nothing of mine remains.** Every start ran in the foreground, and its shell recorded its exit
status, so the parent waited for it. My scripts' audit hooks recorded no process-creation event,
and the observer's three commands start nothing. `kill -0` fails for every PID my scripts recorded
(4326, 4533, 4571, 4745, 4783), so none of them is a process of mine.

**Effect on bound state.** The second Python inventory, after `static` had imported the
supervisor from `<worktree>`, equals the frozen one (`c277bdd3…`). The second static Git read
finds the worktree still equal to tree `ea10cd94…`, with no bytecode file and no untracked file.
`OUT` is the only directory I wrote in. The evidence parent was still empty at the end.

## 9. Deviations and open questions

**Deviations from the brief**, each without effect on a bound input:

- **D1.** I authored one more bound input, the dependency inventory (section 4), because the
  schema needs it and MP left none.
- **D2.** `static`'s stdout and stderr went to `OUT/records/`, not beside the attempt. The
  observer's process was the planned one apart from its subcommand.
- **D3.** I added a preview run of the author script and two final rechecks: a Python inventory
  and a static Git read. All are of the allowed kinds.
- **D4.** In the preview, `_plan_shape` ran on a copy whose dependency-inventory path named the
  existing source inventory, because the inventory did not yet exist. The write run applied it to
  the plan itself.

**Open questions for the reviewer and the Director:**

- **Q-A. Git's stderr is predicted, not observed.** The plan's environment has no `HOME`. N34-M
  predicted the version line statically, but nothing shows statically that this Git writes nothing
  to stderr under that environment. If it writes anything, M0 refuses with OUTPUT-STDERR after one
  counted start. That would be a fact of the host, and MH-PLAN section 8 applies. Node's
  `--version` is in the same position.
- **Q-B. The observer's cwd and the capture paths are my choice.** The cwd is the evidence parent;
  the observer does not constrain it, and `static` ran from it. The capture files are
  `<local>/c271-p35/evidence/observe-001.observe.{stdout,stderr,exit}.txt`, siblings of the
  attempt (FAILURE-CAPTURE FC-K2). The reviewer may prefer others.
- **Q-C. Several facts that the plan binds can change without a file edit.** The ancestors' device
  numbers change if the volume that holds the worktree, `<local>` and the evidence is remounted,
  and the plan binds the boot. Either change makes M0 refuse, which fails closed (MH-PLAN section
  5).
- **Q-D. MP's receipts and plans are bound with their modes.** The receipts are `0o600`, the plans
  `0o644` and the Node archive `0o444`; none may be touched, `chmod` included, until MH ends.
- **Q-E. The `REUC` extension** in the worktree's index is informational (section 3).

## 10. Files delivered

All under `OUT`. `SHA256SUMS.txt` lists each one with its SHA-256, except itself.

| File | Role |
| --- | --- |
| `observation-plan-001.json` | the plan, bound by path; its digest goes on `observe`'s command line |
| `source-inventory-001.json`, `python-inventory-001.json`, `dependencies-inventory-001.json` | the plan's bound inventories |
| `M0-LAUNCH.json` | the exact `observe` command, the expected starts and the expected outputs |
| `PLAN-AUTHOR-NOTES.md` | this file |
| `scripts/w2_git_static.py`, `scripts/w2_author_plan.py`, `scripts/w2_launch_record.py` | my scripts, standard library only |
| `records/` | each run's stdout, stderr, exit status and times; `git-static-001.json` and `git-static-002-final.json`; `author-preview-001.stdout.txt` (the preview's facts); `author-facts-001.json` (the write run's facts and every check); `static-001.*`; `python-inventory-002-final.json` (the final recheck) |
