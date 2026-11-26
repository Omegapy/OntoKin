# Current-host CPU readback contract for the owner's macOS arm64 executor

**Identifier:** `ontokin.current-host-readback/0.2.0`, profile `darwin-arm64-v1`
**Decision state:** design of C271-P31, revision 3 with the nonmandatory corrections after its accepting re-review; adopted by the separate [adoption record](ADOPTION.json) for later bounded phases only. Adoption is a
separate record. Implementation, preparation, qualification, R03, R04 and R05 are separate later
gates.
**Scope:** the same seven methods of `tests/test_static_tray_readback_v01.py` as P05's contract,
within the complete default regression inventory, on one executor class: the owner's prepared
macOS arm64 environment.
**Basis:** route C of the [C271-P30 review](../operational-plan-review-p30/REVIEW-OUTCOME.md),
selected by the owner on 2026-11-25 ("Design macOS contract (C)"). Machine-readable form:
[CONTRACT.json](CONTRACT.json). Inputs: [read set](READ-SET.json).

**Revision history.**
- **Revision 1**, commit `4ee691aedc30dac1e3ec9a63917d7e6ac7493912`, was rejected by the independent
  review on six mandatory findings, G-01 to G-06. Among them: its permission-model launch could not
  start, its read grants left out documents the probe reads, it dropped an argv element, its
  archive rules conflicted with the official tarball, it never classified E1 to E19, and it did not
  state the narrowed meaning of the lifecycle assertions.
- **Revision 2**, commit `90e8a5fbff6a43a1ed08284662e16f9aa5e96a83`, withdrew the permission model
  and kept the 0.1.0 argv. The re-review rejected it on three mandatory findings, G-13 to G-15. macOS
  adds `__CF_USER_TEXT_ENCODING` to the environment, the Python binding claimed more than it bound,
  and the statements about main's driver and R04 were wrong.
- **Revision 3**, commit `dd98e9830fffc0da96bf1cfc408c7f246867a20a`, resolved G-13 to G-19. The
  re-review accepted it with nonmandatory findings G-20 to G-22.
- **This final version** resolves G-20 to G-22 after that re-review, without a further review.

[REVIEW-DISPOSITION](REVIEW-DISPOSITION.json) maps every finding to its change.

This document changes nothing that exists. It specifies a new contract version beside P05's
`ontokin.current-host-readback/0.1.0`. That version stays adopted and unchanged, with its
inspection plans `/0.1.1` to `/0.1.5`, for the Linux x86-64 executor class it was written for.
Its H0 and H1 stay unmet in local mode (P30-EXECUTOR-001).

## 1. What stays, and what changes

P05 states the purpose: run the original methods with a qualified provider, and preserve "the
original test identities, scientific checks, library bytes, numerical thresholds, source budgets,
process supervision and failure accounting". This contract keeps that purpose on another
executor. Each change below is either a term that cannot exist on macOS or a rule this contract
changes deliberately (S8). Each is named, with its reason and its effect on meaning.

| Kept unchanged | Source |
| --- | --- |
| The seven method identities and bodies, `check_case` and the four coordinator seam bodies | P05 contract sections 1–2 |
| The synthetic GLB construction and the independent geometry oracle | P05 section 1 |
| The 24 reader files, byte for byte: validator `2.0.0-dev.3.10`, Three.js `0.186.1` (revision 186), module loader, from the C195 archive (SHA-256 `b1e54a6cfef133f7004b1988c90bc718fc954409843c2bcac3772d42e904a0c9`). All are JavaScript, JSON or text; none is a native module. | P05 section 5; C199 `EXTERNAL-INPUTS.json` |
| The probe's scientific body, its result write with `fs.fsyncSync`, and its token-equivalence obligation | P05 section 6 |
| The exact Node argv of 0.1.0, apart from the executable: `--no-addons`, `--max-old-space-size=256`, `--experimental-loader <module loader>`, the probe, `--expected-config-sha256 <digest>`, `--job <file>` | provider lines 747–749; probe line 659 |
| Thresholds 5×10⁻⁶ m and 10⁻⁶; one scene, 14 nodes, 12 meshes, no animation or camera; validator zero errors and warnings | P05 section 7 |
| Limits: 30,000 ms CPU allowance, 28,000 ms child work, 2,000 ms cleanup, 8 MiB GLB, 4 MiB result and log, 1 MiB manifest, 32 KiB job, 4 MiB audit; source ceilings 100,000 operations and 30,000 ms | P05 section 7; GOAL |
| Exactly one real checker start per CPU case, three for the cohort; the intended negative with exactly one `matrix_0_3` finding; the independent recomputation of every numerical row | P05 section 7; P07 section 6 |
| Explicit selection by path and externally approved digest for qualifying runs; source binding to a clean commit and tree; the isolated-workspace derivation; exclusive creation of fresh paths | P05 sections 2–3, 6 |
| The process adapter's single delegation, preflight and postflight, `CurrentHostBindingError` and the unchanged re-raise of a genuine supervisor `Stop` | P05 section 3 |
| Failure accounting: no retry after a timeout, unknown outcomes stay unknown, every attempt keeps its denominator | P05 section 7; P07 section 4 |

| ID | Changed | Linux x86-64 term | macOS arm64 term | Reason | Effect on meaning |
| --- | --- | --- | --- | --- | --- |
| S1 | Node build | the Codex runtime's `v24.22.1` executable `acbe4b8d…` | the official Node.js `v24.22.1` darwin-arm64 release (section 3) | a Linux executable cannot run on Darwin | same version and same JavaScript; a different build of V8 and libuv, bound by its own bytes |
| S2 | Qualification Python | the Codex runtime's CPython 3.12.14 image and the linux-cp312 lock | the worktree's `.venv` on the owner's CPython 3.12, with main's macos-arm64-cp312 lock (section 4) | the pinned image is a Linux ELF, not retained with its closure | same seven package versions; a different interpreter build, bound by its installation-tree inventory, not by one image hash |
| S3 | Host observation | ELF closure, `ldd`, loader and alias pins, plans `/0.1.1`–`/0.1.5` | M0, static, and M1, one version start (section 7) | no ELF loader or `ldd`; system libraries live in the dyld shared cache | a weaker closure claim, stated in section 7 |
| S4 | Process supervisor | `supervisor.run_process`, requiring `PR_SET_CHILD_SUBREAPER` | a Darwin variant with the same logic except that precondition (section 5) | Darwin has no child-subreaper | the lifecycle assertions keep their text with a narrowed meaning (section 5) |
| S5 | Node launch flags | — | **withdrawn in revision 2**; the argv stays as in 0.1.0 | — | none |
| S6 | Preparer | `renameat2`, Linux-only installation, archive layout `{bin/node, SOURCE.json}` | `renamex_np` with `RENAME_EXCL`, the official archive's member policy, layout `{bin/node, NODE-SOURCE.json}` (section 6) | `renameat2` does not exist on Darwin; the official tarball contains links | same no-replace and exact-tree rules; P05 section 5's link refusal is amended for this archive only |
| S7 | Host bindings of provider and probe | Linux platform, glibc, procfs boot identity, ELF interpreter, `ldd` role, Linux Node pin, linux-cp312 lock | Darwin platform and build, arm64, not translated, Mach-O binding, the S1 pins, the macOS lock. The boot identity is checked by the provider, not by the probe (section 7). | the probe cannot read `kern.bootsessionuuid` without a child process or an addon | the probe can no longer bind the boot itself, which is a stated weakening |
| S8 | Selection rule | absent selection fails driver preparation before any step | absent selection makes an ordinary run: the driver proceeds, and the readback class fails visibly at setup (section 8) | a selection binds one clean commit and one boot, and main's ordinary routine must still run its other stages | a deliberate rule change; no skip is added; qualifying runs keep every rule |
| S9 | Driver environment and Git binding | removal of `LD_*`, `NODE_*` and seven `PYTHON*` variables; Git from the ambient `PATH` | the same list plus every `DYLD_*` variable, `__PYVENV_LAUNCHER__` and `PYTHONEXECUTABLE`; Git bound by absolute path (section 7) | dyld honours `DYLD_*`; `/usr/bin/git` on macOS is a dispatcher | none on the methods; stronger binding of the source reads |
| S10 | OS-supplied environment variable | — | exactly `__CF_USER_TEXT_ENCODING`, which CoreFoundation adds to a process that loads it, admitted with the value recorded in HOST (section 7) | macOS adds it even under an exact clean launch (observed for the qualification Python) | none on the methods; any other extra variable still refuses |

Not applicable on macOS, and therefore never exercised under this contract: the ELF policies of
`/0.1.1` to `/0.1.5` (origin RPATH, PLT tags, `DT_FLAGS`, RTLD paths, required images), the `ldd`
literal list, N34 for the Linux loader and N57. They stay adopted and open for the Linux contract.

**Document schemas.** Under this contract, every document schema of the provider is versioned
`/0.2.0`: config, lock, host, result and node-source, and also source, dependencies, methods,
discovery, workspace, inspection, attempt, setup, cohort, refusal and preserved-cohort. The entry
points of each version refuse the other version's documents. The preparer's plan and result
schemas, `ontokin.current-host-readback-install/0.2.0` and `install-result/0.2.0`, and M0's plan
schema, `ontokin.current-host-readback-observation-plan/0.2.0`, which replaces the inspector's, are
versioned in the same way.

## 2. The executor requirements E1 to E19 of C271-P30

| ID | P30 requirement | Under 0.2.0 | Reason and effect on meaning |
| --- | --- | --- | --- |
| E1 | Linux with glibc | substituted (S3, S7): Darwin, arm64, native | the inspector's Linux checks are not used; M0 binds the Darwin identity |
| E2 | Codex Node build `acbe4b8d…` | substituted (S1) | same version; different build |
| E3 | exact 24 reader files | kept | unchanged bytes |
| E4 | Codex author Python `fa674435…` | substituted (S2) | installation-tree inventory instead of one image pin |
| E5 | libc and loader pins | not applicable | no glibc; the dyld shared cache is identified by OS build |
| E6 | five catalog images | not applicable | ELF images do not exist on Darwin |
| E7 | `/usr/bin/ldd` and RTLD paths | not applicable | no `ldd`; M0's Mach-O rules replace the inspection |
| E8 | clean environment | kept, extended (S9) and amended (S10) | `DYLD_*`, `__PYVENV_LAUNCHER__` and `PYTHONEXECUTABLE` are added to the driver's removal list and refused by M0; the one OS-supplied variable of S10 is admitted |
| E9 | P07 section 2's real fields | kept, restated for the macOS plan (section 7) | literal argv, canonical macOS paths, no unresolved field |
| E10 | N34 | not applicable; replaced by N34-M (section 7) | an independent review of the Mach-O parser and of the closure claim before the macOS plan is adopted |
| E11 | N57 | not applicable | stays open, unchanged, for the Linux contract |
| E12 | fixed obligations of the seven methods | kept | unchanged |
| E13 | original supervisor | substituted (S4) | narrowed meaning of the lifecycle assertions (section 5) |
| E14 | seven package pins | kept | same names and versions, macOS lock |
| E15 | launcher `-I -S -B` | kept for M0, amended by S10 | M0 reads package metadata by path; its environment predicate admits the S10 variable |
| E16 | Linux preparer | substituted (S6) | same rules; amended link policy for the official archive |
| E17 | outer capture descriptors | kept, restated (section 7) | existing evidence parent, absent per-attempt paths, approved failure capture, canonical paths |
| E18 | admitted Git closure | substituted (S9) | Git bound by absolute path, SHA-256 and version; its system libraries identified by OS build |
| E19 | provider and probe host bindings | substituted (S7) | boot identity moves to the provider |

## 3. The Node build (S1)

- **Release:** Node.js `v24.22.1`, file `node-v24.22.1-darwin-arm64.tar.gz`.
- **Pinned archive SHA-256:** `89c682593d76cd44233fa53b1563264e7de9cbb189cad169135c5b4fadfbc0a7`.
  This is the value that the release's `SHASUMS256.txt` lists for that file. That checksum file
  was 3,171 bytes, SHA-256 `fdfbffc969c0f604beff0124d409b33a43b53f5c681d6220f80023e0d6df9dc4`, read
  from `https://nodejs.org/dist/v24.22.1/SHASUMS256.txt` at 2026-11-26T04:25:57Z. The independent
  review read it again and found it identical. Its detached signatures `SHASUMS256.txt.sig` and
  `.asc` are listed beside it. No binary was downloaded in this phase.
- **Trust anchor:** this adopted pin. A signature check with a Node.js release key is optional
  additional evidence, and is recorded either way.
- **Retrieval:** a separately selected preparation phase, after the owner's approval of the
  download (file name, source, about 53 MB).
- **Archive member policy.** This policy amends P05 section 5's refusal of linked entries, for
  this archive only.
  1. The archive's SHA-256 must equal the pin before any member is read.
  2. Every member name must be relative and normalized. An absolute or traversing name, or a
     duplicate name, refuses the whole archive.
  3. An independent author freezes the complete member inventory at preparation, before
     extraction: name, type, size, mode, and for a symbolic link its target.
  4. Members may be regular files, directories, or symbolic links whose relative targets stay
     inside the archive root (for example `bin/npm`, `bin/npx`, `bin/corepack`). A hard link, a
     device, a FIFO, an undeclared member or an escaping link target refuses the archive.
  5. Only `node-v24.22.1-darwin-arm64/bin/node` is extracted, and it must be a declared regular
     file. No link is ever extracted or followed.
- **Provenance record:** `NODE-SOURCE.json` replaces P05's `SOURCE.json`. It holds:
  - the archive name, pin, checksum-file identity and signature-check result;
  - the frozen member-inventory digest;
  - the extracted member and its SHA-256, size and mode.

  The preparer writes it at MP; it is not taken from the archive. Its exact bytes are frozen in the
  reviewed preparation plan before publication. The exact-tree check and the no-replace publication
  cover it as a planned non-archive file. MP's independent reviewer checks it, and the provider
  reads it at preflight.
- **Layout and receipt:** the task-specific runtime directory holds exactly `{bin/node,
  NODE-SOURCE.json}`. The inspector-side receipt rule of `_check_installation` adapts to that
  layout under the 0.2.0 schemas.
- **Executable pin:** the SHA-256, size and mode of `bin/node` are recorded at preparation and
  frozen in the reviewed execution plan before any start.
  - The executable must be a thin 64-bit arm64 Mach-O executable.
  - It is copied into an absent task-specific directory, and never replaces another executable.
- **Version predicate:** `v24.22.1\n` from one bounded `--version` start (M1), after the byte
  binding.

## 4. The qualification Python (S2)

- **Interpreter:** the C271 worktree's own `.venv`, created in place from main's committed local
  environment specification. On this host its `python3.12` is Homebrew's framework launcher, about
  52 KB. The interpreter's code lives in the framework's Python library.
- **Identity bound by M0:** an installation-tree inventory, by path and SHA-256, with each symlink
  recorded by its target. It covers:
  - every regular file of the framework version directory `…/Python.framework/Versions/3.12/`. That
    includes `Resources/Python.app/Contents/MacOS/Python`, which the launcher re-executes and which
    becomes the process image, the `Python` library, `bin/python3.12`, the standard library with
    its `__pycache__` bytecode (`-B` stops writing bytecode, not reading it), and `lib-dynload`;
  - every file of the `.venv`, among them `pyvenv.cfg` and `site-packages`, with the seven
    packages' `RECORD` files verified against their contents;
  - every Mach-O dependency outside `/usr/lib/` and `/System/Library/` of every Mach-O file in
    those trees, for example Homebrew's OpenSSL libraries;
  - the version, build string and `sys.flags`.
- **Exact sets.** Both trees are compared as exact sets at every check, so an extra or missing
  file refuses, not only a changed one. Bytecode files belong to the set. An added `__pycache__`
  file refuses (MC32); the tree is writable by its owner, and another use of the interpreter
  without `-B` could add bytecode that would then be loaded.
- **Dependencies and links.** Dependencies are bound transitively, by each referenced path. Every
  symbolic-link hop on the way is recorded, for example `<prefix>/opt/openssl@3` to its Cellar
  directory, and is followed again at each check.
- **Interpreter selection.** The selection chain is bound the same way, and the resolved launcher
  path is checked again at each use. The chain runs from `.venv/bin/python` to `python3.12`, through
  the `<prefix>/opt/python@3.12/…` links, and includes `pyvenv.cfg`'s `home`.
- **Python-side Mach-O rules.** These files have their own rules, separate from Node's:
  - accepted file types are `MH_EXECUTE`, `MH_DYLIB` and `MH_BUNDLE`;
  - `LC_ID_DYLIB` and `LC_RPATH` are accepted in addition to Node's allow-list, and every
    `LC_RPATH` entry is recorded. An `LC_RPATH` entry that is itself `@`-relative, such as
    libmpdec's `@loader_path/../lib`, is a search directory. It is resolved as a directory, and a
    reference found through it must still resolve to a bound file;
  - an `@rpath`, `@loader_path` or `@executable_path` reference is accepted only if, by dyld's
    rules with the recorded rpaths, it resolves to a bound file;
  - any other `@`-relative reference, `LC_DYLD_ENVIRONMENT`, `LC_LOAD_UPWARD_DYLIB` and unknown
    commands refuse.
- **Lock:** `tools/native-reader-verification-macos-arm64-cp312.lock` from main. It pins the same
  seven names and versions as the linux-cp312 lock: attrs 26.1.0, jsonschema 4.26.0,
  jsonschema-specifications 2025.9.1, referencing 0.37.0, rpds-py 2026.5.1, typing_extensions
  4.16.0 and Pillow 13.0.0.
- **Claim:** this binds the files of the interpreter installation and the non-system libraries
  that its Mach-O files reference. It does not bind their runtime behaviour, nor files that
  libraries load at run time by their own logic (for example OpenSSL's configuration and provider
  modules). The OS libraries are identified by OS build, as in section 7. This is weaker than E4's
  single image pin, and the results say so.

## 5. Process lifecycle (S4)

**Darwin supervisor variant.** A new module, for example
`prototypes/static_tray_v01/supervisor_darwin_v01.py`, supplies `run_process` with the original
signature and receipt fields.

- It imports `Clock`, `Stop`, `LIMITS`, `inventory`, `group_exists`, `terminate_group` and
  `json_bytes` unchanged from the original `supervisor.py`.
- It re-implements only `run_process`. In it, the Linux precondition `prctl(PR_SET_CHILD_SUBREAPER)`
  is replaced by a Darwin precondition: `sys.platform == "darwin"`, machine `arm64`, and
  `sysctl.proc_translated` equal to 0, read through `sysctlbyname`. If the precondition fails, it
  raises the same kind of `Stop`. Everything else stays as in the original:
  - one direct child in a new session and process group;
  - capped non-blocking capture and the stage inventory on every poll;
  - the deadline checks and the 2,000 ms cleanup reserve;
  - the group check after exit;
  - `terminate_group`'s SIGTERM, mandatory SIGKILL and bounded reaping;
  - handle closing and the process receipt.
- A reviewed token-level comparison with the original `run_process` must show only that change.
- The original `supervisor.py` stays byte-identical and remains the Linux contract's supervisor.

**Meaning of the lifecycle assertions under 0.2.0.** `check_case` asserts `cleanup.passed` and
`handles_closed`, and the receipt records `reaped` and `process_group_absent`. Their text is
unchanged; under this contract they mean exactly this:

| Receipt field | Linux contract | 0.2.0 on Darwin |
| --- | --- | --- |
| `reaped` | the direct child was reaped. Orphaned descendants are re-parented to the supervisor, and so are reapable by it. | the direct child was reaped. Orphaned descendants are re-parented to `launchd`, **not** to the supervisor. |
| `process_group_absent` | `killpg(pid, 0)` finds no member of the child's group | the same probe. Whether Darwin counts a zombie member is not established here. |
| `cleanup.passed` | the group was gone within the cleanup ceiling | the same, with the two meanings above |
| `handles_closed` | the supervisor closed its pipes and logs | unchanged |

**No descendant.** The contract claims no enforcement against descendants. It records one
property of the bound code, which the reviewed static check MC11 (NOT_RUN) is to show. The
property: the probe, the module loader and the 24 reader files make no use of `child_process`,
`cluster`, `worker_threads` or `process.dlopen`.

The scan looks for these module names and calls. It also looks for the dynamic constructs that
could hide them: a computed `require` or `import()`, `eval`, and `Function`. Every dynamic construct
it finds must be reviewed. A scan of names cannot exclude every dynamic route, and its result states
that limit.

That property, the unchanged group check after exit, and the result labels together state the
Darwin lifecycle. It is weaker than Linux's, and results never claim the Linux guarantee. A
dynamic Darwin descendant monitor, for example a libproc enumeration on every poll, is a possible
later amendment. This contract does not adopt one.

**Result durability.** The probe's `fs.fsyncSync` call is unchanged. On macOS, `fsync` does not
force the data to permanent storage the way `F_FULLFSYNC` does. Results therefore claim no
durability beyond what `fsync` gives on this OS.

## 6. Preparation and installation (S6)

The preparer keeps P05 section 5's rules, except for the archive member policy of section 3:
- verified source bytes and a frozen member inventory;
- staging under the same parent, and atomic no-replace publication of a complete tree;
- reuse of an existing exact tree, and refusal of a partial, changed, extra or inaccessible one;
- readback of the exact destination after a conflict or an uncertain rename, before any retry.

On Darwin, publication uses `renamex_np(staged, destination, RENAME_EXCL)` from libSystem, within
one volume. The implementation binds the flag's value from the SDK header or Apple's
documentation.
- If the volume does not support the flag (`ENOTSUP`) or the call fails, the publication is
  refused. There is never a fallback to a plain rename.
- A real conflict control (MC15) and an unsupported-volume control (MC16) prove the behaviour.

The receipts keep their states, `INSTALLED_EXACT` and `ALREADY_PRESENT_EXACT`, with zero Node,
`ldd` and checker starts. Runtime and dependency trees stay outside Git, under task-specific
external paths.

## 7. Host observation in place of H0 and H1 (S3, S7, S9)

**Canonical paths.** On macOS, `/tmp`, `/var` and `/etc` are symbolic links into `/private`.
- Every bound path is recorded in its canonical form, the `realpath` taken once and checked again
  before use.
- Apart from these three system links, a symlinked ancestor refuses the path.
- Main's local baseline recorded failures under the default symlinked temporary directory.
  Qualifying runs therefore use a resolved temporary directory, as main's resulting-main run did.
- A `.DS_Store` file, or any other untracked file, in a source, evidence or dependency tree
  refuses that tree. Finder must not be used on those directories during a run.

**M0, static.** M0 starts no Node process; its only bounded start is Git's `--version`. The observer runs under the launcher `-I -S -B` (E15). It reads
package metadata from the files under the `.venv`'s `site-packages` by explicit path, not through
`importlib.metadata`. It records the HOST document, schema `ontokin.current-host-readback-host/0.2.0`:

| Field | How it is observed |
| --- | --- |
| Kernel name, release, machine | `os.uname()`: `Darwin`, its release, `arm64` |
| OS product version, build and any `ProductVersionExtra` | `/System/Library/CoreServices/SystemVersion.plist`, and the OS cryptex's copy of that file if present. A security update to the cryptex can change the dyld shared cache, so both are bound. |
| Native execution | `sysctl.proc_translated` = 0, through `sysctlbyname` |
| Boot identity | `kern.bootsessionuuid`, through `sysctlbyname` |
| Python | section 4 |
| Node executable | path in the task-specific directory, regular and not a symlink, SHA-256, size and mode; `NODE-SOURCE.json` |
| Mach-O binding of Node | a reviewed static parser reads the header and every load command (see below) |
| Git | the absolute path of the Git implementation used for source reads (not the `/usr/bin/git` dispatcher), its SHA-256 and its version string from one bounded `--version` start, counted separately |
| Environment | exactly the declared clean environment, plus `__CF_USER_TEXT_ENCODING` when CoreFoundation has added it (S10). Its value is recorded and compared. Nothing else is admitted: no `DYLD_*`, `__PYVENV_LAUNCHER__`, `PYTHONEXECUTABLE`, `NODE_OPTIONS`, `NODE_PATH` or Python startup variable. |
| Reader files and source | the exact 24-file tree; the source inventory of the clean commit and tree |

**Load commands.** The executable must be thin 64-bit arm64, file type executable. Its load
commands follow a closed allow-list: `LC_SEGMENT_64`, `LC_SYMTAB`, `LC_DYSYMTAB`,
`LC_LOAD_DYLINKER`, `LC_UUID`, `LC_BUILD_VERSION`, `LC_SOURCE_VERSION`, `LC_MAIN`,
`LC_LOAD_DYLIB`, `LC_LOAD_WEAK_DYLIB`, `LC_FUNCTION_STARTS`, `LC_DATA_IN_CODE`,
`LC_CODE_SIGNATURE`, `LC_DYLD_INFO_ONLY`, `LC_DYLD_CHAINED_FIXUPS` and `LC_DYLD_EXPORTS_TRIE`.
- `LC_LOAD_DYLINKER` must be `/usr/lib/dyld`.
- Every dylib path must lie under `/usr/lib/` or `/System/Library/`.
- `LC_RPATH`, `LC_DYLD_ENVIRONMENT`, `LC_LOAD_UPWARD_DYLIB`, `LC_REEXPORT_DYLIB`, any
  `@rpath`, `@loader_path` or `@executable_path` reference, and any unknown command refuse the
  executable. A needed addition is an amendment.

**Environment predicate (S10).** Three checks use the same predicate: M0, the provider's HOST
comparison, and the probe's `process.env` check, which is a bootstrap binding and not the
scientific body. Each accepts exactly the declared environment, optionally plus that one variable,
`__CF_USER_TEXT_ENCODING`, with the value recorded in HOST. None of them checks whether the
process loaded CoreFoundation.

The supervisor still passes exactly the declared environment to the child, and its receipt records
what was passed. Whether the official `node` loads CoreFoundation is not established in this
phase. The predicate admits the variable either way, and MC30 and MC31 test both directions.

**Closure claim.** The Node executable's bytes and load commands are bound, and so is the
interpreter installation of section 4, within the limits stated there. The system libraries come
from the OS build's dyld shared cache,
in the signed system volume and the OS cryptex. They are identified only by the recorded OS
product version, build and cryptex version, not by per-file hashes. The contract assumes, and does
not verify, Apple's sealed system volume and System Integrity Protection. This claim is weaker than
the Linux plan's file-by-file closure, and every result says so.

**N34-M.** Before a macOS execution plan is adopted, an independent reviewer must examine the
Mach-O parser's source and this closure claim against the actual load commands. This is N34's
analogue. It is an external review obligation, not a runtime pass.

**Boot binding.** The probe can read the OS identity files, but not `kern.bootsessionuuid`.
- The provider therefore reads the boot identity before the cohort, and before and after each
  start. A change fails the attempt.
- The probe checks `os.type()`, `os.release()` and `os.machine()` and the OS build file. It no
  longer checks the boot itself; that is the stated weakening of E19.
- The darwin-arm64 Node build runs natively by construction, since Rosetta translates only x86-64
  code.

**M1, bounded observation.** One `node --version` start through the Darwin supervisor, with a
five-second deadline, expecting `v24.22.1\n`, plus the one Git `--version` start of M0. No `ldd`
exists, so none is started. A `codesign --verify --strict` inspection is optional, counted
separately, and not required, since the bytes are pinned.

**Execution plan (E9, E17).** P07 section 2's rules apply to the macOS execution plan: literal
argv arrays with cwd, environment and limits; canonical paths; no `TODO`, null, wildcard, guessed
hash or unresolved field; an existing external evidence parent with its ancestor identities;
absent per-attempt output paths; an approved failure-capture procedure; an independent review with
an externally supplied digest.

**Process denominators**, for one successful minimal path, before any separately frozen fault
control:

| Step | Direct Node starts | Other bounded starts |
| --- | ---: | ---: |
| M0 Git version | 0 | 1 |
| M1 Node version | 1 | 0, or 1 with `codesign` |
| Probe syntax check | 1 | 0 |
| P06-H01 direct negative | 1 | 0 |
| P06-H02 direct negative | 1 | 0 |
| Original CPU trio | 3 | 0 |
| Coordinator quartet (mocked seams) | 0 | 0 |
| **Total** | **7** | **1 or 2** |

P07's rules for counting attempted and actual starts, unknown outcomes and cleanup evidence apply
unchanged.

## 8. Selection rule (S8)

The selection binds one exact clean commit and tree and the current boot. After R04, main's
default local routine runs on uncommitted changes and across reboots, where no approved selection
can exist. Today the branch's driver refuses to start any step without one. Main's driver has no
readback selection, and main's version of the test skips the three CPU methods. This contract
distinguishes two kinds of run.

- **Qualifying run.** The driver receives `--readback-config` and `--readback-config-sha256` from
  an independently reviewed execution plan. Every existing rule applies: missing, partial,
  malformed, unapproved or mismatched selection fails preparation, and any skip, error, expected
  failure or missing method of the readback cohort fails the run. Only a qualifying run can be
  cited for the readback methods, the macOS qualification or R03.
- **Ordinary run.** Neither argument is given.
  - The driver proceeds with every stage. It records
    `readback_selection: {"status": "absent", "run_kind": "ordinary"}`, and passes no selection
    to the unit process.
  - The readback CPU class's `setUpClass` fails visibly with "No approved current-host readback
    selection: ordinary run, not a qualification". unittest reports one class-level error, and the
    class's three methods are neither run nor reported. It is never a skip. The coordinator seams
    run.
  - Both drivers fail a stage with any skip, error or failure, so the unit stage of an ordinary
    run is failed for this reason. Main's unit stage is failed today too, among other reasons for
    its three skips.
  - No ordinary run is evidence for the readback methods.
- **Partial selection** (one of the two arguments) fails in either kind of run.
- **Direct invocation** of the module without the driver behaves as an ordinary run (a visible
  setup error) unless both selection variables are set, as P05 section 2 already provides.

This amends one behaviour: the driver's refusal to start without a selection, for ordinary runs
only. P05's no-skip rule and CH13's "fails visibly; no skip" stay.

Revision 1 proposed a labelled skip for ordinary runs. It is rejected here: it adds a skip, which
P05 forbids, and it changes no stage outcome under the drivers' zero-skip rule. Requiring a
selection for every run is also rejected, because main's ordinary routine would then run no stage
at all without one.

**R04 obligation.** After integration, main's ordinary runs would change from three skipped
methods to one class-level `setUpClass` error, with the three methods not executed: tests run −3,
skipped −3, errors +1. R04 classifies this change under OK-ENG-009 section 3, items 2 and 4, with
exact inputs. It also states whether the readback methods belong to released behaviour. This
contract does not decide that classification.

## 9. Declarative control obligations (NOT_RUN)

Every control is an obligation for the implementation, preparation and qualification phases.
None has run. An independent author freezes exact inputs and expected outcomes before execution.
The full table, with the P05 controls each one covers, is in [CONTRACT.json](CONTRACT.json) under
`controls`. "Node" counts direct Node starts; "other" counts other bounded starts.

| ID | Route | Case | Expected outcome | Node | Other |
| --- | --- | --- | --- | ---: | ---: |
| MC01 | preparation | archive bytes differ from the pin | refused before any member is read | 0 | 0 |
| MC02 | preparation | member policy: an absolute, traversing or duplicate name; a hard link, device or FIFO; an undeclared member; an escaping link target | refused; nothing extracted | 0 | 0 |
| MC03 | preparation | a declared in-archive link member (for example `bin/npm`) | accepted, not extracted or followed | 0 | 0 |
| MC04 | preparation | `bin/node` missing, or not a declared regular file | refused | 0 | 0 |
| MC05 | preparation | extracted executable not thin arm64 Mach-O, or its SHA-256, size or mode differs from the frozen plan | refused before M1 | 0 | 0 |
| MC06 | M0 | a load command outside the allow-list, a dylib outside `/usr/lib` or `/System/Library`, or an `@`-relative path | refused | 0 | 0 |
| MC07 | M0 | a `DYLD_*`, `__PYVENV_LAUNCHER__`, `PYTHONEXECUTABLE`, `NODE_*` or Python startup variable present | refused; the driver removes them for the unit process | 0 | 0 |
| MC08 | M0 | translated execution, a machine other than arm64, or a system other than Darwin | refused | 0 | 0 |
| MC09 | provider | boot identity, OS build or cryptex version changes between the HOST document and a start, or across a start | the attempt fails | 0 | 0 |
| MC10 | M1 | observed Node version differs, simulated at the command boundary and labelled mocked | failed preparation; no qualification | 0 | 0 |
| MC11 | static | reviewed scan of the probe, loader and 24 reader files for process-creation calls | none found | 0 | 0 |
| MC12 | supervisor | a non-Node test child leaves a member of its process group alive after exiting | "Child exited while an owned descendant remained"; group terminated within 2,000 ms | 0 | 1 |
| MC13 | supervisor | timeout cleanup, and cancellation cleanup | original limits and receipts; no retry | 0 | 2 |
| MC14 | supervisor | token-level comparison with the original `run_process` | only the precondition differs | 0 | 0 |
| MC15 | preparer | destination appears before publication | no-replace rename refuses; existing content untouched | 0 | 0 |
| MC16 | preparer | volume without `RENAME_EXCL` support, or a failing call | refused; no fallback rename | 0 | 0 |
| MC17 | supervisor | Darwin precondition fails (translated, or a non-Darwin platform) | `Stop` before any start | 0 | 0 |
| MC18 | dependencies | one of the 24 files missing, extra, changed, a symlink, or a `.DS_Store` present | refused | 0 | 0 |
| MC19 | source | other checkout, dirty or untracked executable source, changed provider or probe, or an unbound Git executable | refused | 0 | 0 |
| MC20 | paths | a bound path with a symlinked ancestor other than `/tmp`, `/var` or `/etc` | refused | 0 | 0 |
| MC21 | selection | qualifying run with a missing, partial, malformed or mismatched selection | failed preparation | 0 | 0 |
| MC22 | selection | ordinary run without selection | the driver proceeds; `setUpClass` fails visibly with the fixed reason; no skip; summary records the ordinary run kind | 0 | 0 |
| MC23 | selection | qualifying run whose readback cohort skips, errors or misses a method | the run is not qualified | per run | 0 |
| MC24 | original | Q01 and Q03 positive, under the unchanged argv and the result fsync | both readers read the actual bytes; all rows pass; result written and synced | 2 | 0 |
| MC25 | original | Q01 changed reference | exit 1 with exactly the intended `matrix_0_3` finding | 1 | 0 |
| MC26 | original | the four coordinator seams | original outcomes, labelled mocked | 0 | 0 |
| MC27 | direct negatives | P06-H01 and P06-H02 as P07 section 5 defines them, with `--expected-config-sha256` | one start each; refusal before reader imports | 2 | 0 |
| MC28 | discovery | the complete default inventory against the baseline plus approved additions | exact match; no hidden skip or missing method in a qualifying run | 0 | 0 |
| MC29 | time of use | a change of source, runtime, dependency, configuration or OS build after preflight | the current attempt is invalid; zero new starts before launch | 0 | 0 |
| MC30 | environment | only the declared variables, plus `__CF_USER_TEXT_ENCODING` with the recorded value; the case without the variable is a simulated boundary, labelled mocked | accepted by M0, the provider and the probe | 1 | 0 |
| MC31 | environment | an extra variable other than `__CF_USER_TEXT_ENCODING`, or that variable with a value other than the recorded one | refused | 0 | 0 |
| MC32 | Python | a changed, added or missing file in either tree (among them an added bytecode file and a changed `pyvenv.cfg`), a retargeted symbolic-link hop, or an `@`-relative load that does not resolve to a bound file | refused | 0 | 0 |
| MC33 | configuration | declared Node version other than `v24.22.1` | refused before any start | 0 | 0 |
| MC34 | dependencies | C195 archive with an absolute, traversing, duplicate, linked or special entry, or an unexpected mode | refused before extraction | 0 | 0 |
| MC35 | installation | existing destination partial, changed, extra, linked or inaccessible | refused; nothing repaired or replaced | 0 | 0 |
| MC36 | direct negative | a probe start whose frozen HOST input carries an altered `__CF_USER_TEXT_ENCODING` value | the probe refuses at its environment binding, before reader imports | 1 | 0 |

P05's CH01 to CH20 are covered as follows; `CONTRACT.json` gives the map.
- **CH04 and CH05** (the ELF closure and `ldd` provenance): replaced by MC05 to MC09.
- **CH13:** keeps its meaning for qualifying runs (MC21). For ordinary runs, the driver's refusal
  to start becomes a visible setup error (MC22).
- **CH03, CH07 and CH08:** fully covered only with MC33 (declared version), MC34 (the C195
  archive's extraction checks) and MC35 (an existing destination), next to the controls the map
  lists.
- **Every other CH:** kept, with the macOS controls named in the map.

## 10. Labels and claims

Every result carries the executor label `macos-arm64-local`, together with:
- the contract `ontokin.current-host-readback/0.2.0`;
- the OS product version, build and cryptex version;
- the Node archive and executable pins;
- the Python installation inventory digest;
- the Git binding;
- the run kind.

Results under this contract can never support:
- a Linux x86-64 qualification;
- the historical C199/C225 replay;
- a P05 Gate H for the Codex Node build;
- any statement that the ELF policies of `/0.1.1` to `/0.1.5` were exercised on a real host;
- N34 for the Linux loader, or N57;
- the original supervisor's Linux descendant-reaping guarantee, or any enforcement against
  descendants;
- a per-file closure of the macOS system libraries;
- durable storage beyond what `fsync` gives on macOS;
- a binding of files that libraries load at run time by their own logic.

Unmet Linux-contract gates stay recorded as unmet. They are never relabelled.

## 11. Gates and sequencing

The macOS gates take an `M` prefix, so they do not collide with P07's H0 to H3, P05's Gate R or
the plan step P02.

| Gate | Scope |
| --- | --- |
| MD | This design, independently reviewed and adopted (C271-P31) |
| MB | Main's local-mode files on this branch, through a reviewed merge of main into the branch that resolves the six overlaps by meaning ([MAIN-CONFLICTS](../p29-local-publication-r07/MAIN-CONFLICTS.md)). It brings the macOS lock, the local environment specification and its tools. It does not integrate into main. MAIN-CONFLICTS places that resolution after R03, inside R04. This contract moves the branch-side merge earlier, because MI and MP need main's files. Integration into main, and its checks, stay in R04. |
| MI | Implementation of the 0.2.0 adaptations: Darwin supervisor variant, provider and probe host bindings, preparer route, driver environment, Git binding and selection rule. Independently frozen controls where they are not runtime; independent review. |
| MP | Preparation, after the owner's download approval: the Node archive with its frozen member inventory, the reader tree from the C195 archive, and the `.venv` from the macOS lock. Receipts; independent review. |
| MH | N34-M, then M0 and M1, then the qualifying cohort: the seven methods and the direct negatives on the owner's executor. Independent audit. |
| MR | A complete default routine as a qualifying run, with zero missing or skipped obligations, as P05's Gate R requires. Main's recorded macOS baseline outcomes stay visible and are compared, under OK-ENG-009, with exact inputs. That includes the test with a last-digit fixture difference, and the failures that occur only under a symlinked temporary directory. R03 acceptance follows. |
| R04, R05 | Integration with actual-main verification, then parent completion, as before |

Each gate is a separately selected phase with its own declaration, and each stops at its own
boundary.

## 12. Trust assumptions and limits

- **Apple's platform:** the signed system volume, System Integrity Protection, and the cryptex
  delivery of the dyld shared cache are assumed, not verified.
- **Bound files only:** the static Mach-O parser binds files and load commands, not runtime
  behaviour.
- **Zombies:** whether Darwin's `killpg(pid, 0)` counts a zombie group member is not established.
- **Node behaviour:** this contract assumes that Node `v24.22.1` on darwin-arm64 computes the same
  JavaScript results as on Linux x86-64, within the unchanged thresholds. The qualification
  observes it; this design does not prove it.
- **Run-time loads:** files that libraries load at run time by their own logic, for example
  OpenSSL's configuration and provider modules, are not bound.
- **`__CF_USER_TEXT_ENCODING`:** its value depends on the user and the text encoding. HOST records
  it, and a different value refuses (MC31).
- **Test file:** its module docstring still mentions `ldd`. MI updates the docstring only; no
  method body changes.
