# Current-host CPU readback contract for the owner's macOS arm64 executor

**Identifier:** `ontokin.current-host-readback/0.2.0`, profile `darwin-arm64-node-permission-v1`
**Decision state:** design candidate of C271-P31, for independent review. Adoption is a separate
record. Implementation, preparation, qualification, R03, R04 and R05 are separate later gates.
**Scope:** the same seven methods of `tests/test_static_tray_readback_v01.py` as P05's contract,
within the complete default regression inventory, on one executor class: the owner's prepared
macOS arm64 environment.
**Basis:** route C of the [C271-P30 review](../operational-plan-review-p30/REVIEW-OUTCOME.md),
selected by the owner on 2026-11-25 ("Design macOS contract (C)"). Machine-readable form:
[CONTRACT.json](CONTRACT.json). Inputs: [read set](READ-SET.json).

This document changes nothing that exists. It specifies a new contract version beside P05's
`ontokin.current-host-readback/0.1.0`. That version stays adopted and unchanged, with its
inspection plans `/0.1.1` to `/0.1.5`, for the Linux x86-64 executor class it was written for.
Its H0 and H1 stay unmet in local mode (P30-EXECUTOR-001).

## 1. What stays, what is substituted, and why

P05 states the purpose: run the original methods with a qualified provider, and preserve "the
original test identities, scientific checks, library bytes, numerical thresholds, source budgets,
process supervision and failure accounting". This contract keeps that purpose. It substitutes
only what cannot exist on macOS, and each substitution is named and justified here.

| Kept unchanged | Source |
| --- | --- |
| The seven method identities and bodies, `check_case` and the four coordinator seam bodies | P05 contract sections 1–2 |
| The synthetic GLB construction and the independent geometry oracle | P05 section 1 |
| The 24 reader files, byte for byte: validator `2.0.0-dev.3.10`, Three.js `0.186.1` (revision 186), module loader, from the C195 archive (SHA-256 `b1e54a6cfef133f7004b1988c90bc718fc954409843c2bcac3772d42e904a0c9`). All are JavaScript, JSON or text; none is a native module. | P05 section 5; C199 `EXTERNAL-INPUTS.json` |
| The probe's scientific body and its token-equivalence obligation | P05 section 6 |
| Thresholds 5×10⁻⁶ m and 10⁻⁶; one scene, 14 nodes, 12 meshes, no animation or camera; validator zero errors and warnings | P05 section 7 |
| Limits: 30,000 ms CPU allowance, 28,000 ms child work, 2,000 ms cleanup, 8 MiB GLB, 4 MiB result and log, 1 MiB manifest, 32 KiB job, 4 MiB audit; source ceilings 100,000 operations and 30,000 ms | P05 section 7; GOAL |
| Exactly one real checker start per CPU case, three for the cohort; the intended negative with exactly one `matrix_0_3` finding; the independent recomputation of every numerical row | P05 section 7; P07 section 6 |
| Explicit selection by path and externally approved digest; source binding to a clean commit and tree; the isolated-workspace derivation; exclusive creation of fresh paths | P05 sections 2–3, 6 |
| The process adapter's single delegation, preflight and postflight, `CurrentHostBindingError` and the unchanged re-raise of a genuine supervisor `Stop` | P05 section 3 |
| Failure accounting: no retry after a timeout, unknown outcomes stay unknown, every attempt keeps its denominator | P05 section 7; P07 section 4 |

| Substituted | Linux x86-64 term (P05 and `/0.1.1`–`/0.1.5`) | macOS arm64 term (this contract) | Why |
| --- | --- | --- | --- |
| S1 Node build | the Codex runtime's `v24.22.1` executable `acbe4b8d…`, from P05's own archive | the official Node.js `v24.22.1` darwin-arm64 release (section 2) | A Linux executable cannot run on Darwin. The version stays constant, as P05 itself did when it qualified a different build. |
| S2 Qualification Python | the Codex runtime's CPython 3.12.14 image `fa674435…` and the linux-cp312 lock | the worktree's own `.venv` on the owner's CPython 3.12 (3.12.13 observed), with main's macos-arm64-cp312 lock (section 3) | The pinned image is a Linux ELF and is not retained with its closure. Both locks pin the same seven names and versions. |
| S3 Host observation | ELF closure through `/usr/bin/ldd`, loader and alias pins, procfs boot identity, `/0.1.1`–`/0.1.5` plans | a static macOS observation, M0, and one bounded version start, M1 (section 6) | macOS has no ELF loader or `ldd`, and its system libraries live in the dyld shared cache, not as files |
| S4 Process supervisor | `supervisor.run_process`, which requires Linux `PR_SET_CHILD_SUBREAPER` | a Darwin variant with the same logic and receipts, except that precondition (section 4) | Darwin has no child-subreaper. The guarantee it gave is replaced, for Node checkers, by preventing descendants. |
| S5 Node launch flags | `--no-addons`, `--max-old-space-size=256` | `--permission` with exact `--allow-fs-read` and `--allow-fs-write` paths, then the same two flags (section 4) | The permission model makes child processes, workers, addons and WASI impossible for the checker |
| S6 Preparer | `tools/prepare_current_host_readback.py`, publication with `renameat2`, Linux only | the same rules, with a macOS no-replace rename and one-member extraction (section 5) | `renameat2` does not exist on Darwin |
| S7 Host bindings of provider and probe | Linux platform, glibc, `/proc/sys/kernel/random/boot_id`, ELF interpreter, `ldd` role, Linux Node pin, linux-cp312 lock | Darwin platform and build, arm64 and not translated, `kern.bootsessionuuid`, Mach-O load-command binding, the S1 pins, the macOS lock | Same reason as S3 |
| S8 Selection rule for ordinary runs | absent selection always fails preparation | absent selection is an ordinary run; selection is required for every qualifying run (section 7) | A selection binds one clean commit and one boot. Requiring one for every ordinary run would stop main's routine after R04. |

Not applicable on macOS, and therefore not exercised under this contract: the ELF policies of
`/0.1.1` to `/0.1.5` (origin RPATH, PLT tags, `DT_FLAGS`, RTLD paths, required images), the `ldd`
literal list, and N34 for the Linux loader. They stay adopted, and their unmet gates stay unmet.

## 2. The Node build (S1)

- **Release:** Node.js `v24.22.1`, file `node-v24.22.1-darwin-arm64.tar.gz`.
- **Pinned archive SHA-256:** `89c682593d76cd44233fa53b1563264e7de9cbb189cad169135c5b4fadfbc0a7`.
  This is the value that the release's `SHASUMS256.txt` lists for that file. That checksum file
  was 3,171 bytes, SHA-256 `fdfbffc969c0f604beff0124d409b33a43b53f5c681d6220f80023e0d6df9dc4`, read
  from `https://nodejs.org/dist/v24.22.1/SHASUMS256.txt` at 2026-11-26T04:25:57Z. Its detached
  signatures `SHASUMS256.txt.sig` and `.asc` are listed beside it. No binary was downloaded in this
  phase.
- **Trust anchor:** this adopted pin. A later preparation may also verify the signature with a
  Node.js release key, and records the result either way. A verified signature adds evidence but
  is not required, and an unverifiable one does not replace the pin.
- **Retrieval:** in a separately selected preparation phase, with the owner's approval of the
  download (file name, source, about 53 MB).
- **Extraction:** exactly one member, `node-v24.22.1-darwin-arm64/bin/node`.
  - It must be a regular file. A symlink, hard link, special file, traversing name or duplicate
    member refuses the extraction.
  - No other member is extracted. npm, npx and corepack are not part of the executor.
- **Executable pin:** its SHA-256, size and mode are recorded at preparation. They are then frozen
  in the reviewed execution plan before any start. This completes "pinned by its own bytes".
  - Its Mach-O header must be thin 64-bit arm64. Anything else refuses the preparation and needs an
    amendment.
  - It is copied into an absent task-specific directory. It never replaces Homebrew's `node` or
    any other executable.
- **Version predicate:** `v24.22.1\n` from one bounded `--version` start (M1). The version is one
  predicate only, after the byte binding.

## 3. The qualification Python (S2)

- **Interpreter:** the C271 worktree's own `.venv`, created in place from main's committed local
  environment specification. Its resolved executable, version (3.12.13 observed today), build and
  the seven installed package versions are recorded in the HOST document at preparation.
- **Lock:** `tools/native-reader-verification-macos-arm64-cp312.lock` from main. It pins the same
  seven names and versions as the linux-cp312 lock (attrs 26.1.0, jsonschema 4.26.0,
  jsonschema-specifications 2025.9.1, referencing 0.37.0, rpds-py 2026.5.1, typing_extensions
  4.16.0, Pillow 13.0.0), with macOS wheel hashes. The provider and probe compare names and
  versions, as they do today.
- **Labelling:** results name this interpreter. They are never relabelled as the historical Linux
  CPython 3.12.14 qualification.

## 4. Process lifecycle (S4, S5)

**Darwin supervisor variant.** A new module, for example
`prototypes/static_tray_v01/supervisor_darwin_v01.py`, supplies `run_process` with the original
signature and receipt fields.

- It imports `Clock`, `Stop`, `LIMITS`, `inventory`, `group_exists`, `terminate_group` and
  `json_bytes` unchanged from the original `supervisor.py`.
- It re-implements only `run_process`. In it, the Linux precondition `prctl(PR_SET_CHILD_SUBREAPER)`
  is replaced by a Darwin precondition: `sys.platform == "darwin"` and machine `arm64`, not
  translated. Everything else stays as in the original:
  - a new session and process group for the one direct child;
  - capped non-blocking pipe capture and the stage inventory on every poll;
  - the deadline checks and the 2,000 ms cleanup reserve;
  - the descendant check after exit, which refuses with "Child exited while an owned descendant
    remained" when `killpg(pid, 0)` still finds the group;
  - `terminate_group`'s SIGTERM, then mandatory SIGKILL, and bounded reaping;
  - handle closing and the process receipt.
- A reviewed token-level comparison with the original `run_process` must show only that change.
- The original `supervisor.py` stays byte-identical and remains the Linux contract's supervisor.

**Guarantees, against P05 section 7:**

| Guarantee | Linux contract | This contract |
| --- | --- | --- |
| One direct child in its own session and process group | yes | yes, unchanged |
| Bounded capture, deadlines, no retry, receipts, handles closed | yes | yes, unchanged |
| A live member of the child's process group after exit refuses the run | yes | yes, unchanged |
| Cleanup by SIGTERM then SIGKILL of the group, within 2,000 ms | yes | yes, unchanged |
| Orphaned descendants are re-parented to the supervisor and reaped by it | yes (child-subreaper) | **not kept**. Darwin re-parents them to `launchd`. |
| A Node checker creates no descendant | not enforced | **enforced** by the permission model (below) |

**Node launch with the permission model.** Each Node start uses, in this order:
1. `--permission`;
2. one `--allow-fs-read` for each declared read root: the bound workspace source root, the
   dependency root, and the cohort root that holds the bound manifest, jobs, inputs and stage, as
   the lock binds them;
3. one `--allow-fs-write` for the private stage of that start only;
4. `--no-addons` and `--max-old-space-size=256`;
5. the exact module-loader entry and probe;
6. `--job FILE`.

No `--allow-child-process`, `--allow-worker`, `--allow-addons` or `--allow-wasi` is admitted. In
Node.js `v24.22.1` the permission model is stable. Spawning a child process without
`--allow-child-process`, or starting a worker without `--allow-worker`, throws `ERR_ACCESS_DENIED`.
Native addon loading is blocked.

The model has documented limits: it follows symbolic links outside granted paths, and file
descriptors that are already open bypass it. This contract therefore keeps the existing refusal
of any symlink in the dependency tree and the stage. The child receives no file descriptor beyond
its three standard streams.

The scientific body is pure computation over bound reads, so these flags do not change what the
readers compute. They do add refusals for any spawn, worker, addon or write outside the stage.
The provider's launch binding (CH12) checks this exact argv. A missing `--permission`, an extra
grant or a changed path refuses before the start.

## 5. Preparation and installation (S6)

The preparer keeps P05 section 5's rules:
- verified source bytes, a predeclared member inventory, and the refusal of absolute, traversing,
  duplicate, linked or special entries;
- staging under the same parent, and the atomic no-replace publication of a complete tree;
- reuse of an existing exact tree, and the refusal of a partial, changed, extra or inaccessible
  one;
- readback of the exact destination after a conflict or an uncertain rename, before any retry.

On Darwin, publication uses `renamex_np(staged, destination, RENAME_EXCL)` from libSystem, on the
same APFS volume. The implementation binds the flag's value from the SDK header or Apple's
documentation and proves the no-replace behaviour with a real conflict control (MC15).

The receipts keep the existing states, `INSTALLED_EXACT` and `ALREADY_PRESENT_EXACT`, with zero
Node, `ldd` and checker starts. Runtime and dependency trees stay outside Git, under task-specific
external paths.

## 6. Host observation in place of H0 and H1 (S3, S7)

**M0, static, no target start.** Records the HOST document, schema
`ontokin.current-host-readback-host/0.2.0`:

| Field | How it is observed |
| --- | --- |
| Kernel name, release, machine | `os.uname()`: `Darwin`, its release, `arm64` |
| OS product version and build | the read-only file `/System/Library/CoreServices/SystemVersion.plist` (today 26.6.2, 25G83) |
| Native execution | `sysctl.proc_translated` = 0, read through `sysctlbyname` |
| Boot identity | `kern.bootsessionuuid`, read through `sysctlbyname` |
| Python | resolved executable, version and build; the seven package versions through `importlib.metadata`; the lock's bytes |
| Node executable | path in the task-specific directory, regular and not a symlink, SHA-256, size and mode; the archive pin |
| Mach-O binding of Node | a reviewed static parser reads the header and load commands (thin arm64, executable). `LC_LOAD_DYLIB`, `LC_LOAD_WEAK_DYLIB` and `LC_REEXPORT_DYLIB` paths must lie under `/usr/lib/` or `/System/Library/`. `LC_LOAD_DYLINKER` must be `/usr/lib/dyld`. No `LC_RPATH`, no `@rpath`, `@loader_path` or `@executable_path` reference. The presence of `LC_CODE_SIGNATURE` is recorded. |
| Environment | exactly the declared clean environment; no `DYLD_*`, `NODE_OPTIONS`, `NODE_PATH` or Python startup hooks |
| Reader files and source | the exact 24-file tree; the source inventory of the clean commit and tree |

**Closure claim.** The Node executable's bytes and its load commands are bound. The system
libraries it loads come from the OS build's dyld shared cache. They are identified only by the
recorded OS product version and build, not by per-file hashes. This is weaker than the Linux
plan's file-by-file closure, and every result says so.

**M1, bounded observation.** One `node --version` start through the Darwin supervisor, under the
permission flags, with a five-second deadline, expecting `v24.22.1\n`. No `ldd` exists, so none
is started. An optional `codesign --verify --strict` of the executable may be added as a bounded
inspection process, with its own count. It is not required, because the bytes are pinned.

**Process denominators**, for one successful minimal path, before any separately frozen fault
control:

| Step | Direct Node starts | Other inspection starts |
| --- | ---: | ---: |
| M1 version | 1 | 0, or 1 if `codesign` is selected |
| Probe syntax check | 1 | 0 |
| P06-H01 direct negative | 1 | 0 |
| P06-H02 direct negative | 1 | 0 |
| Original CPU trio | 3 | 0 |
| Coordinator quartet (mocked seams) | 0 | 0 |
| **Total** | **7** | **0 or 1** |

P07's rules for counting attempted and actual starts, unknown outcomes and cleanup evidence apply
unchanged.

## 7. Selection rule for main's ordinary routine (S8)

The selection binds one exact clean commit and tree and the current boot. After R04, main's
default local routine runs on uncommitted changes and across reboots, where no approved selection
can exist. This contract therefore distinguishes two kinds of run.

- **Qualifying run.** The driver receives `--readback-config` and `--readback-config-sha256` from
  an independently reviewed execution plan. Every existing rule applies: missing, malformed,
  unapproved or mismatched selection fails preparation, and any skip, error, expected failure or
  missing method of the readback cohort fails the run. Only a qualifying run can be cited for the
  readback methods, Gate H or R03.
- **Ordinary run.** No selection is given. The driver proceeds and records
  `readback_selection: {"status": "absent", "run_kind": "ordinary"}` in its summary.
  - The CPU class reports its three methods as skipped, with the fixed reason "No approved
    current-host readback selection: ordinary run, not a qualification".
  - The coordinator seams run as before.
  - No ordinary run is evidence for the readback methods.
  - A partial selection (one of the two arguments) still fails.

This amends P05's `absent_behavior` for ordinary runs only. It keeps the visible distinction that
P05 wanted: a skip here is labelled and recorded and never counts as a pass. It matches main's
present behaviour, where these three methods are skipped.

The alternative, requiring a selection for every run, was weighed and rejected for main. It
would make the ordinary routine refuse to start on any uncommitted change.

## 8. Declarative control obligations (NOT_RUN)

Every control is an obligation for the implementation and qualification phases. None has run.
An independent author freezes exact inputs and expected outcomes before execution. The full table,
with the P05 controls each one maps, is in [CONTRACT.json](CONTRACT.json) under `controls`.

| ID | Route | Case | Expected outcome | Starts |
| --- | --- | --- | --- | ---: |
| MC01 | preparation | archive bytes differ from the pin | refused before extraction | 0 |
| MC02 | preparation | `bin/node` member missing, linked, special, traversing or duplicated | refused, nothing published | 0 |
| MC03 | preparation | extracted executable is not thin arm64 Mach-O | refused | 0 |
| MC04 | preparation | executable SHA-256, size or mode differs from the frozen plan | refused before M1 | 0 |
| MC05 | M0 | a load command outside `/usr/lib` or `/System/Library`, an `LC_RPATH`, or an `@`-relative path | refused | 0 |
| MC06 | M0 | `DYLD_*`, `NODE_OPTIONS`, `NODE_PATH` or a Python startup hook present | refused | 0 |
| MC07 | M0 | translated execution, a machine other than arm64, or a system other than Darwin | refused | 0 |
| MC08 | M0 | boot identity or OS build differs from the HOST document | refused | 0 |
| MC09 | M1 | observed version differs, simulated at the boundary and labelled mocked | failed preparation; no qualification | 0 (mocked) |
| MC10 | launch | `--permission` missing, an extra grant, or a changed read or write path | refused before the start | 0 |
| MC11 | Node | a probe variant that tries to spawn a child, start a worker or write outside the stage | `ERR_ACCESS_DENIED` or a refused write; one start; no descendant | 1 |
| MC12 | supervisor | a non-Node test child that leaves a member of its group alive after exiting | "Child exited while an owned descendant remained"; group terminated within 2,000 ms | 1 |
| MC13 | supervisor | timeout and cancellation cleanup | original limits and receipts; no retry | 1 each |
| MC14 | supervisor | token-level comparison with the original `run_process` | only the precondition differs | 0 |
| MC15 | preparer | destination appears before publication | no-replace rename refuses; the existing content is untouched | 0 |
| MC16 | dependencies | one of the 24 files missing, extra, changed or a symlink | refused | 0 |
| MC17 | source | other checkout, dirty or untracked executable source, changed provider or probe | refused | 0 |
| MC18 | selection | qualifying run with a missing, partial, malformed or mismatched selection | failed preparation | 0 |
| MC19 | selection | ordinary run without selection | three CPU methods skipped with the fixed reason; summary records the ordinary run kind | 0 |
| MC20 | selection | qualifying run whose readback cohort skips, errors or misses a method | the run is not qualified | per run |
| MC21 | original | Q01 and Q03 positive | both readers read the actual bytes; all rows pass | 2 |
| MC22 | original | Q01 changed reference | exit 1 with exactly the intended `matrix_0_3` finding | 1 |
| MC23 | original | the four coordinator seams | original outcomes, labelled mocked | 0 |
| MC24 | direct negatives | P06-H01 and P06-H02 as P07 section 5 defines them | one start each; refusal before reader imports | 2 |
| MC25 | discovery | the complete default inventory against the baseline plus approved additions | exact match; no hidden skip or missing method in a qualifying run | 0 |

P05's CH01 to CH20 keep their meaning. CH04 and CH05 (the ELF closure and `ldd` provenance) are
replaced by MC03 and MC05 to MC08. The others map one to one, as `CONTRACT.json` records.

## 9. Labels and claims

Every result carries the executor label `macos-arm64-local`, together with:
- the contract `ontokin.current-host-readback/0.2.0`;
- the OS product version and build;
- the Node archive and executable pins;
- the Python identity;
- the run kind.

Results under this contract can never support:
- a Linux x86-64 qualification;
- the historical C199/C225 replay;
- a P05 Gate H for the Codex Node build;
- any statement that the ELF policies of `/0.1.1` to `/0.1.5` were exercised on a real host;
- N34 for the Linux loader;
- the original supervisor's Linux descendant-reaping guarantee;
- a per-file closure of the macOS system libraries.

Unmet Linux-contract gates stay recorded as unmet. They are never relabelled.

## 10. Gates and sequencing

| Gate | Scope |
| --- | --- |
| D2 | This design, independently reviewed and adopted (C271-P31) |
| B | Main's local-mode files on this branch: a reviewed merge of main into the branch, resolving the six overlaps by meaning ([MAIN-CONFLICTS](../p29-local-publication-r07/MAIN-CONFLICTS.md)). It brings the macOS lock, the local environment specification and its tools. It is a separate selected phase, the first part of R04's preparation; it does not integrate into main. |
| I2 | Implementation of the 0.2.0 adaptations: Darwin supervisor variant, provider and probe host bindings, preparer route, driver selection rule. Independently frozen controls MC01–MC25 where they are not runtime; independent review. |
| P2 | Preparation: download, after the owner's approval, verification and extraction of the Node archive; the reader tree from the C195 archive; the `.venv` from the macOS lock. Receipts; independent review. |
| H2 | M0 and M1, then the qualifying cohort: the seven methods and the direct negatives on the owner's executor; independent audit |
| R | A complete default routine as a qualifying run with zero skipped obligations; R03 acceptance |
| R04, R05 | Integration with actual-main verification, then parent completion, as before |

Each gate is a separately selected phase with its own declaration, and each stops at its own
boundary.
