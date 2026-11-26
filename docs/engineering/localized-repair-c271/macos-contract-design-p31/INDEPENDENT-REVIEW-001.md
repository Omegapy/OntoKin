# C271-P31 independent review of the macOS arm64 contract candidate

Candidate: commit `4ee691aedc30dac1e3ec9a63917d7e6ac7493912` (tree `728d4e8ebe77d9fafde1fa1b29377b13e29739d4`),
branch `work/c271-missing-import-digest-control`, files under
`docs/engineering/localized-repair-c271/macos-contract-design-p31/`. Main observed at
`51223c9b94a222f29d38eb6c33808f8e55e2bff9`.

## 1. Independent list, written before reading CONTRACT.md

Written at 2026-11-26T04:40Z, after reading only the sources named in the procedure (P05 CONTRACT.md
and CONTRACT.json, P30 CONTRACT-REQUIREMENTS.json and REVIEW-OUTCOME.md section 6, `supervisor.py`,
`current_host_readback_v01.py` and `.mjs`, `prepare_current_host_readback.py`, `check_local.py`,
`tests/test_static_tray_readback_v01.py`), plus `format_check.py`, `transaction.py` helpers used by the
seams, and the inspector's `_platform`, `_check_host_static`, `_load_helpers`, `_check_git`,
`_check_launcher`, `_check_metadata` and `_check_installation`, all at the candidate commit. Line
numbers below are at that commit.

### A. Host identity (E1, E19; P05 section 4 HOST.json)

1. Platform predicate: `system == "Linux"` (provider line 477; probe 452) and the inspector's
   Linux/glibc refusal become Darwin arm64. "Native" needs its own predicate: a translated process
   (`sysctl.proc_translated` 1) reports x86_64, so Python and Node must both be shown untranslated.
2. libc identity: `platform.libc_ver()` (provider 476), `confstr(CS_GNU_LIBC_VERSION)` (inspector)
   and Node's `report.header.glibcVersionRuntime` (probe 454) have no macOS value. libSystem lives in
   the dyld shared cache, so it can only be identified through the OS version and build.
3. Boot identity: `/proc/sys/kernel/random/boot_id` (provider 476, probe 456, inspector) has no file
   equivalent. `kern.bootsessionuuid` is a sysctl that Python can read, but the probe cannot read it
   without a child process or an addon. The probe's boot binding must be redesigned or dropped, and
   the drop must be stated.
4. Host roles `ldd`, `inspector_interpreter` (the ldd shebang), `elf_interpreter`,
   `loader_configuration`, `shared_libraries` and `inspector_runtime` (provider 485-523, probe
   479-511) have no Mach-O meaning. The Mach-O equivalents are the dynamic linker
   (`LC_LOAD_DYLINKER`, `/usr/lib/dyld`), the `LC_LOAD_DYLIB` list and any `LC_RPATH`. System
   libraries are in the dyld shared cache rather than in files, so the file-by-file closure claim
   must be restated.
5. Inspection commands: `/usr/bin/ldd node` is gone. Either a static Mach-O parse replaces it (no
   process), or a new tool with its own closure does. P07 section 4's process denominators (one
   ldd launch) and the `inspections` schema change accordingly.
6. Both ELF `PT_INTERP` readers (provider `_elf_interpreter`, probe `elfInterpreter`) become
   Mach-O header and load-command checks: thin arm64 or universal binary, `MH_EXECUTE`, dylinker.
7. Code signing: arm64 code must carry a valid signature. The pinned bytes include it. The design
   must say whether signature validity, quarantine or provenance attributes, or the platform's
   execution policy are claimed, observed with a new tool, or explicitly not claimed.

### B. Node build (E2; P05 section 4)

8. `v24.22.1` kept. The darwin-arm64 build is pinned by its own archive digest (from the official
   checksum file) and by its executable's bytes, size and mode. The executable's digest cannot be
   known before extraction, so it must not be invented. The archive's authenticity rests on HTTPS
   and the checksum file, unless its signature is verified. P05 explicitly made no
   vendor-authentication claim.
9. The official darwin archive contains symbolic-link members (the npm, npx and corepack entry
   points) and many unrelated files. The preparer refuses any link member (`_plan_shape`,
   `verify_archive`) and requires `files == {"bin/node", "SOURCE.json"}` with the P05 archive digest
   (`_source`). Both rules need a reviewed substitute.
10. Every constant that pins the Linux build changes: provider `NODE_SHA256`, `NODE_BYTES` and
    `NODE_ARCHIVE_*`; probe `NODE_SHA`, `NODE_SIZE`, `NODE_ARCHIVE_SHA` and the literal 45186132;
    inspector `NODE` and `NODE_ARCHIVE_*`; preparer `_source`.

### C. Python (E4, E14, E15, E8)

11. The qualification Python, CPython 3.12.13 on macOS, pinned by bytes. On a framework build, the
    path in `sys.executable` is a small launcher. The interpreter runs from
    `Resources/Python.app/Contents/MacOS/Python` and the framework's `Python` library. Its standard
    library extension modules and any non-system libraries they load (for example OpenSSL) are real
    files outside the shared cache. Pinning only `Path(sys.executable).resolve()` would not pin the
    interpreter.
12. The `$ORIGIN/../lib` RPATH rule (P11) does not apply. Mach-O uses `@rpath`, `@loader_path` and
    `@executable_path`, so a new rule is needed, or the design must say none is applied.
13. E14: the `linux-cp312` lock pins manylinux wheel hashes. On macOS the binary wheels (rpds-py,
    Pillow) differ. The provider compares only names and versions (`_python_pins`). A darwin lock
    or an explicit name-and-version-only statement is required.
14. E8 and E15: the clean-environment rule names `LD_PRELOAD` and `LD_LIBRARY_PATH` (driver lines
    489-491; P05 section 4). On macOS the injection variables are `DYLD_INSERT_LIBRARIES`,
    `DYLD_LIBRARY_PATH`, `DYLD_FRAMEWORK_PATH`, the `DYLD_FALLBACK_*` pair and similar, plus
    `__PYVENV_LAUNCHER__` and `PYTHONEXECUTABLE` for framework Pythons. The Node child gets only
    ENVIRONMENT, but the unit-test Python inherits the driver's environment minus that list.
15. ENVIRONMENT (`PATH=/usr/bin:/bin`, `C.UTF-8`, and so on) can stay, since the probe requires
    `process.env` to equal it exactly. Under that PATH, `/usr/bin/git` on macOS is a
    developer-tools shim that dispatches to another executable, which affects E18.

### D. Supervisor (E13; P05 sections 3 and 7)

16. `run_process` lines 171-173: on Darwin, the `prctl` lookup through `ctypes.CDLL(None)` raises
    `AttributeError`, which is not a `Stop`, before the `try`. A Darwin variant must omit or replace
    these lines. It must keep raising the original `supervisor.Stop` class, because `check_case`
    catches `Stop` imported from `supervisor` (test line 22) and the provider tests
    `isinstance(delegated, supervisor.Stop)`. It must also keep accepting the original `Clock`,
    which the provider's `_job` tests by `isinstance`. The provider calls `supervisor.run_process`
    by name (line 869), so the provider must change, and so must the inspector's `_load_helpers`
    binding.
17. Guarantees: without a subreaper, orphaned descendants are reparented to launchd. `_reap`
    (`waitpid(-pid)`) reaches only direct children. `cleanup.reaped` and `process_group_absent`
    then mean "the direct child was reaped and its group is absent", not "every descendant was
    reaped". `check_case` asserts `cleanup.passed` and `handles_closed`, so the meaning of those
    assertions narrows. Darwin offers no equivalent of PR_SET_CHILD_SUBREAPER. Kqueue process
    filters and libproc enumeration are partial substitutes.
18. `selectors.DefaultSelector` is kqueue on Darwin and epoll on Linux. The `time.monotonic` clock
    sources differ. Neither should change the outcome, but both are substitutions to name.

### E. Preparer (E16; P05 section 5)

19. `renameat2(RENAME_NOREPLACE)` becomes `renamex_np` or `renameatx_np` with `RENAME_EXCL`. Its
    support depends on the filesystem (APFS and HFS+), so the destination parent's filesystem must
    be bound and ENOTSUP must be a refusal. The `sys.platform == "linux"` gate changes.
20. `fsync` on macOS does not force data to stable storage (`F_FULLFSYNC` does). Any durability
    wording inherited from Linux must be qualified.
21. `/tmp` and `/var` are symbolic links on macOS. The provider's and preparer's refusal of
    symlinked path components (`_absolute`, `_parent_identity`) requires canonical `/private/...`
    paths. Python's default temporary directory lies under `/var/folders`.

### F. Provider and probe (E19; P05 sections 2, 4 and 6)

22. A new contract identifier and schemas, with the probe's `CONTRACT_SHA` and `CONTRACT_RELATIVE`,
    the provider's `CONTRACT_PATH`, `SOURCE_FILES`, and the inspector's source-inventory parity.
23. If the Node permission model is added, the flags change. NODE_FLAGS comes from the protected
    historical `format_check.py`, so it cannot be edited. The provider requires `len(argv) == 10`
    (`_job` 784, `guarded_run_process` 838). The probe requires `process.execArgv` to equal exactly
    `[--no-addons, --max-old-space-size=256, --experimental-loader, loader]` (659). The manifest
    slot argv (748) changes too. P05 section 6 ("no unbound extra flag") is amended, and the design
    must say so.
24. Grants must cover every probe read: the probe itself; the module loader; the dependency root;
    the job, manifest, configuration and (derived) parent configuration; the workspace binding,
    `source_before` and `workspace_inventory`; the source inventory and contract source; every
    immutable file in the copied workspace (`verifyWorkspace`); the source trees and required
    files; the dependency inventory and archive; the host document and inspection receipts; the
    saved Node archive (`host.runtime.source_archive.path`); every `host.files` entry and alias
    (`aliasesFor`); the methods and discovery documents; the baseline map in both the workspace
    and the original checkout (`config.parent.source_root`); and the GLB and audit. The one write
    is `probe.json` in the stage (`wx` plus fsync). Undecided points: whether `--experimental-loader`
    hooks, which run off-thread, work under `--permission` without a worker grant;
    whether `realpathSync` of deep paths needs ancestor grants; and the symlink and
    file-descriptor caveats.
25. `_python_pins` reads the Linux lock. `host.python` binds `Path(sys.executable).resolve()` and
    `platform.python_version()`.

### G. Driver and selection (P30 section 7)

26. The driver requires a selection whenever the unit stage is planned, which is always (lines
    576-583). After R04, main's ordinary routine would refuse to start. Any rule that lets an
    ordinary run proceed without the three CPU checkers is a change to P05 section 2 ("absent ...
    configuration is a failed preparation"), which forbids skips, exclusions and fallback suites.
    Such a rule must be explicit, must not report an ordinary run as R03 or as a complete
    regression, and must not count unexecuted CPU methods as passed.
27. The driver's injection-variable removal list needs the DYLD_* names. `git_read` uses the
    ambient PATH's `git`, so the Git closure (E18) must be redefined on macOS.

### H. Tests, meaning and gates

28. The test's import adaptation (`guarded_run_process as run_process` from the v01 provider) may
    need to point at a new provider, through a reviewed setup and import diff only. The nine
    `ORIGINAL_BODIES` stay unchanged. The module docstring's mention of ldd becomes stale.
29. The four coordinator seams (setitimer, SIGALRM and mocks) are platform-neutral. Their meaning
    is unchanged.
30. Numerical: V8 arithmetic is IEEE-754 double. The Python oracle uses the platform libm, so its
    results may differ from Linux in the last place, within the 10^-6 thresholds. Results are
    therefore labelled, not claimed bit-identical to Linux.
31. Labels and gates: macOS results are labelled with the executor and never satisfy H0 or H1 under
    `/0.1.5`, P05 Gate H for the Codex build, a Linux x86-64 qualification, the C199/C225 replay, or
    N34 for the Linux loader. N34's macOS analogue is unmet or newly defined. N57 stays external.
    The direct-probe controls P06-H01, H02 and H03 and the P07 section 4 denominators must be
    restated for this executor. E9, E10, E11 and E17 carry over with macOS paths.

### How the candidate compares with this list

How the candidate's substitutions S1 to S8 and its kept and not-applicable lists cover this list:

- **Covered:** items 1, 2, 5, 6, 8, 10, 12, 13, 16, 19, 26 and 29, and most of 31 (labels,
  never-supported claims, Linux gates unmet).
- **Covered only on the provider side** (G-02): items 3 and 4.
- **Addressed:** item 7 (`LC_CODE_SIGNATURE` recorded, `codesign` optional).
- **Substituted explicitly but incompletely:** item 23 (S5, see G-03) and item 22 (only four of the
  schemas, G-12).
- **Missing or contradicted:**
  - item 9 (G-04);
  - item 11 (G-07);
  - item 14 on the driver side (G-05);
  - items 15 and 27, the Git closure (G-05);
  - item 17, the receipt meaning (G-06);
  - items 20 and 21 (G-10);
  - item 24 (G-01, G-02);
  - from item 31: E9, E10, E11, E15, E17 and E18 (G-05, G-12).
- **Not mentioned, immaterial:** items 18, 25, 28 and 30.

Items 23 and 24 turn out to be decisive. The documented Node behaviour checked in section 2 goes
further than this list anticipated: the module loader needs `--allow-worker`, and fsync on a
descriptor is disabled.

## 2. Checks run

All Git reads used `--no-optional-locks`. Times are UTC, 2026-11-26.

| # | Check | Result |
| --- | --- | --- |
| C1 | Candidate identity: `git cat-file -p 4ee691ae` and `git ls-tree`; diff from `af6340de` | Tree `728d4e8e…`, parent `af6340de`. It adds CONTRACT.md (23,502 bytes, SHA-256 `9bc72c99…a4`), CONTRACT.json (23,196, `4528d53a…77`) and READ-SET.json (6,909, `d3a3603c…88`). PHASE.json (8,293, `57d866ba…34`) is unchanged from `af6340de`. The worktree is at `4ee691ae` with no tracked changes. |
| C2 | READ-SET recomputation: `git show <rev>:<path>`, SHA-256 and length of the blob bytes. Branch entries at `af6340de…`, main entries at `51223c9b…` read from the main checkout | **22 of 22 match** (17 branch, 5 main). Each branch entry is also byte-identical at the candidate commit. |
| C3 | `https://nodejs.org/dist/v24.22.1/SHASUMS256.txt`, read twice over HTTPS to standard output (about 04:43Z and 04:59:55Z) | 3,171 bytes, SHA-256 `fdfbffc969c0f604beff0124d409b33a43b53f5c681d6220f80023e0d6df9dc4`. The darwin-arm64 `.tar.gz` line reads `89c682593d76cd44233fa53b1563264e7de9cbb189cad169135c5b4fadfbc0a7`; the `.tar.xz` line reads `654ba79d…a628`. Both **match the candidate**. Not checked: the dist listing (signature files, "53 MB", dates), which is outside this review's allowed reads. |
| C4 | `https://nodejs.org/docs/v24.22.1/api/permissions.html` (HTTP 200, 44,271 bytes, title names v24.22.1), read to standard output at 04:44Z | Stable since v23.5.0. `--permission` restricts the file system, child processes, workers, addons, WASI and the inspector, and denials raise `ERR_ACCESS_DENIED`. A directory grant extends to its contents. The application's entry points are readable implicitly. Symbolic links are followed outside the grants, and relative links can expose arbitrary files. Using an existing descriptor bypasses the model. **Also documented:** descriptor-only operations (fsync, fdatasync, fchmod, fchown and their synchronous forms) are disabled and throw `ERR_ACCESS_DENIED`. **Also documented:** the model is not inherited by worker threads, and it is a "seat belt" for trusted code, not a guarantee against malicious code. |
| C5 | `https://nodejs.org/docs/v24.22.1/api/cli.html` (title names v24.22.1), read to standard output at 04:46Z | Without `--allow-child-process` or `--allow-worker`, the restricted operation throws `ERR_ACCESS_DENIED`. `--no-addons` exists. **`--experimental-loader`: since v23.6.1, v22.13.1 and v20.18.2, using it with the permission model requires `--allow-worker`. The flag's own text repeats this.** |
| C6 | Host, read-only, at 04:51:35Z: `sysctl -n kern.bootsessionuuid` and `sysctl -n sysctl.proc_translated`; `plutil` reads of `/System/Library/CoreServices/SystemVersion.plist` | Boot session UUID present in UUID form (value not recorded). `proc_translated` = 0. ProductVersion 26.6.2, ProductBuildVersion 25G83, and no ProductVersionExtra. **Matches the candidate.** |
| C7 | ctypes attribute lookups, no call made, through `CDLL(None)` and `/usr/lib/libSystem.B.dylib` | `renamex_np`, `renameatx_np` and `sysctlbyname` are present. `renameat2` and **`prctl` are absent**, so `supervisor.run_process` line 172 raises `AttributeError` here before its `try`. The value of `RENAME_EXCL` was not bound, as the candidate also states. |
| C8 | Read-only `ls` and `file` | `/usr/bin/git` is a 118,640-byte universal (x86_64, arm64e) executable, consistent with the developer-tools dispatcher (inference). `/tmp`, `/var` and `/etc` are symbolic links into `/private`. Both venvs link `python3.12` to the framework launcher `bin/python3.12` (52,448 bytes). The interpreter runs as `Resources/Python.app/Contents/MacOS/Python` (51,392 bytes), with its code in the framework library `Python` (5,984,672 bytes). |
| C9 | CONTRACT.md control table against CONTRACT.json `controls` and `p05_control_map` (scripted) | Same 25 IDs and routes. Every one of CH01 to CH20, CH11-P and CH11-C is mapped, and both mapping views agree. Start counts differ for MC13 (MD "1 each", JSON `null`) and MC20 ("per run", `null`). MC12, which uses a non-Node child, has `expected_node_starts: 1`. |
| C10 | E1 to E19 in the candidate: grep of all four files | No E identifier appears in CONTRACT.md or CONTRACT.json. Only PHASE.json mentions E1 to E19, in A2's own text and in its inputs. |
| C11 | Main at `51223c9b`: `tools/check_local.py` lines 425-438, `BASELINE-CHECKS.json`, the macOS lock and `local-environment.json` | Main's driver also marks the unit step failed on any skip. Main's local baseline unit stage ran 4,740 methods with failures=103, errors=311 and skipped=3; the three skips are the readback CPU methods, and `complete_regression_passed` is false. The macOS lock pins the same seven names and versions with macOS wheel hashes, as the candidate says. |
| C12 | Source tracing of the probe's reads and writes, the provider's paths, the driver's workspace and selection flow, and the preparer's archive rules | Cited per finding below. |

## 3. Acceptance claims A1 to A8

| Claim | Assessment | Findings |
| --- | --- | --- |
| A1 read set and external facts | The 22 identities are correct, and the facts carry sources and times. Declared inputs are missing, and the recorded Node facts omit the decisive ones. | G-12, G-01 |
| A2 substitution map | **Not met.** E1 to E19 are not classified, terms that change on macOS are left out, and no effect on test meaning is stated. | G-05, G-06, G-08 |
| A3 executor | Met for the Node pins, the verification route and the 24 files. The Python identity is weak. | G-07 |
| A4 supervisor and guarantees | **Not met.** The stated replacement for descendant reaping is unsupported. | G-01, G-06 |
| A5 preparer | **Not met as written.** The kept member rules refuse the official archive. | G-04, G-10 |
| A6 host observation | M0, M1 and the denominators are defined, and the closure claim is honest for Node. It is silent for Python, and the denominators rest on a launch that cannot run. | G-01, G-07, G-10 |
| A7 selection rule | Decided and explicit about `absent_behavior`. Its scope is understated, and one alternative was not weighed. | G-08 |
| A8 controls, labels, never-supported claims | Present and NOT_RUN. Some counts are inconsistent, coverage is partial, and gate names collide. | G-11, G-09 |

## 4. Findings

### G-01 — mandatory — The permission-model launch cannot run as specified, and its added guarantee is unsupported

**Location:** CONTRACT.md section 1 (S5 "Why"), section 4 ("Node launch with the permission
model"; guarantees row "A Node checker creates no descendant"); CONTRACT.json
`launch.forbidden_grants`, `launch.node_facts`, `supervisor.guarantees.added`; READ-SET.json
`external` entries for `permissions.html` and `cli.html`.

**Evidence.**
1. The launch keeps the module loader (section 4 item 5; JSON `<module-loader entry>`). The
   provider passes it as `--experimental-loader` (provider lines 748-749), and the probe requires
   exactly that flag in `process.execArgv` (probe line 659). Under C5, that flag requires
   `--allow-worker` when the permission model is on. The contract forbids `--allow-worker`.
   Every checker start would therefore be refused at start-up: the three original CPU checkers
   (MC21, MC22), P06-H01 and P06-H02 (MC24), and the syntax check if it loads the hooks. None of
   them would reach the probe's own logic, and MC24's expected boundary (`approvedEnvelope`,
   `CH-SELECTION`) would not be reached. This is inferred from the documented requirement. No
   Node process was run.
2. Admitting `--allow-worker` would not rescue the design. Under C4 the model is not inherited by
   worker threads, so the loader thread, which runs a bound reader file and what it imports, would
   run unrestricted. Both "makes child processes, workers, addons and WASI impossible" (S5) and
   "A Node checker creates no descendant: enforced" would be false.
3. Under C4, fsync on a descriptor is disabled. The probe's preserved `output()` (probe lines
   28-33) writes the report through the descriptor and then calls `fs.fsyncSync(fd)`. It runs
   outside every `try` (line 806). Suppose a start got past the loader, for example with
   `--allow-worker`. It would then write `probe.json` and exit 1 on an uncaught `ERR_ACCESS_DENIED`
   (inferred from the documentation; not executed). Q01 and Q03 would fail. The changed-reference
   method would still see exit 1 and a readable report, so its expected exit no longer shows that
   the intended rejection produced it. P05 section 6 preserves "exclusive write/fsync behavior",
   and the contract keeps the probe's token-equivalence obligation. The fsync therefore cannot be
   dropped silently.
4. C4 also describes the model as a seat belt for trusted code that gives no guarantee against
   malicious code. "Enforced" overstates it.
5. Section 4 and `launch.node_facts` give only the symlink and descriptor-bypass limits. The three
   documented facts above are absent, so "these flags do not change what the readers compute"
   rests on an incomplete reading of the very pages cited.

**Correction.** Re-decide S5 against the v24.22.1 documentation. One option admits
`--allow-worker` for the loader and restates the guarantee: the loader thread is outside the
model. Another is a worker-free loader route, which changes a bound file and needs its own
decision. A third drops the permission model and records the descendant guarantee as lost.
Decide the result write explicitly: either amend P05 section 6 and the token-equivalence
obligation for the probe's fsync, or keep the fsync and not use `--permission`. Record the
omitted facts in the read set. Add a control that shows a positive start under the exact flags,
writing and syncing its result as designed.

### G-02 — mandatory — The read grants omit roots the probe must read, and some S7 bindings are unobservable by the probe

**Location:** CONTRACT.md section 4 item 2, section 1 S7 row; CONTRACT.json `launch.read_roots`,
`launch.mitigations`, `substitutions.S7`.

**Evidence.** The grants are the workspace source root, the dependency root and the cohort root.
Before importing a reader, the current probe also reads:
- the configuration (lines 606-607);
- the evidence root itself, through `lstat` and `realpath` (612);
- the source inventory (296);
- the dependency inventory (321) and its archive (326);
- the host document (446);
- the saved Node archive (477);
- every `host.files` entry with alias realpaths (`aliasesFor`, 410-417), including the Node
  executable in its task-specific runtime directory and the Python executable;
- `realpath(process.execPath)` (496);
- both inspection receipts (504-506);
- the methods and discovery documents (518, 523);
- the baseline map in the original checkout, `config.parent.source_root` (534);
- the parent configuration, workspace binding, `source_before` and `workspace_inventory` (559,
  568, 577-578).

None of these can lie in a granted root:
- In a driver run, the derived configuration is written to `<output>/readback-binding/selection.json`
  (driver line 453; provider lines 705 and 721).
- The cohort is a fresh `mkdtemp` directly under the evidence root (provider lines 933 and 987),
  so the configuration can never be inside it.
- The frozen plan documents, and the archive path inside the dependency inventory, are fixed
  before the run. So they can be in neither the fresh cohort nor the fresh workspace. The
  workspace derivation rewrites only the source root and the contract path (provider lines
  717-720).
- The dependency root must hold exactly the 24 files (probe 338-339).

The first such read, of the configuration, happens outside any `try`. **Every start would fail.**
P05 section 6 also requires the probe itself to check the actual executable's path, bytes and
mode, which needs a grant for the runtime directory.

S7 lists `kern.bootsessionuuid`, "not translated" and the OS build among the provider's and the
probe's bindings. Node has no sysctl interface, and the contract excludes child processes and
addons, so the probe cannot read the boot session UUID. Reading the OS build needs
`SystemVersion.plist`, which is not granted. The probe's procfs boot check (line 456) therefore
has no feasible probe-side substitute. That is a weakening of E19, and it is not stated.

Two related gaps. The contract does not establish whether `fs.realpathSync`, used by
`canonicalDirectory`, by `fileBytes` and in module resolution, needs grants on each root's
ancestors. The stated symlink mitigation covers only the dependency tree and the stage. Under
`--full`, the granted workspace root holds the driver's absolute `tools/node_modules` link
(driver line 217).

**Correction.** Derive the grant list from the probe's actual read set, path by path, or move
those documents into granted roots through an explicit amendment. State which host bindings
become provider-only (boot identity, translation, OS build) as an amendment of P05 section 6 and
E19. Settle the ancestor question with a control. Refuse symbolic links in every granted root.
Add a positive grant-sufficiency control.

### G-03 — mandatory — The normative argv drops the external approval digest

**Location:** CONTRACT.md section 4 items 1-6 ("The provider's launch binding (CH12) checks this
exact argv"); CONTRACT.json `launch.order`.

**Evidence.** Both files end the order with `<module-loader entry>`, `<probe>`, `--job` and
`<FILE>`. The implemented argv is `[node, --no-addons, --max-old-space-size=256,
--experimental-loader, LOADER, PROBE, --expected-config-sha256, DIGEST, --job, JOB]` (provider
lines 748-749). `approvedEnvelope` accepts exactly `--expected-config-sha256 DIGEST --job FILE`
(probe 590-596). P07 section 5 defines P06-H01 by keeping argv's expected digest D0. The
contract keeps "explicit selection by path and external digest" and MC24 (P06-H01 "as P07
section 5 defines them"), yet its exact argv leaves the digest out. The `--experimental-loader`
flag is not written either.

**Correction.** Write the complete argv in both files, including `--experimental-loader LOADER`
and `--expected-config-sha256 DIGEST`, in their positions, together with whatever G-01 decides.

### G-04 — mandatory — The kept preparer rules conflict with the official archive's members

**Location:** CONTRACT.md section 2 ("Extraction") and section 5 (first list); CONTRACT.json
`node.extraction`, `preparer.rules`.

**Evidence.** Section 5 keeps P05 section 5's predeclared member inventory and its "refusal of
... linked or special entries". The existing preparer enforces this across the whole archive:
- every member must be declared (`verify_archive`, line 171);
- declared members may only be files or directories (`_plan_shape`, line 105; line 173);
- the selected-Node layout must be `{"bin/node", "SOURCE.json"}` under the P05 archive digest
  (`_source`, lines 241-246).

Section 2 says "A symlink ... member refuses the extraction". It also acknowledges that npm, npx
and corepack are in the archive. Node's official tarballs are generally known to carry `bin/npm`,
`bin/npx` and `bin/corepack` as symbolic links; this review did not observe it, since nothing was
downloaded. Read as written, the rules refuse the official archive as a whole. Read as applying
only to `bin/node`, they silently amend P05 section 5. The replacement for `SOURCE.json`, and the
inspector's selected-Node receipt rule (`_check_installation`), are also unstated.

**Correction.** State the member policy for this archive. For example: a complete predeclared
inventory in which each link member is recorded with its target and never extracted; other
members verified and not extracted; only `bin/node` extracted. Amend P05 section 5 for it
explicitly, define the provenance record and the receipt layout, and add MC02 variants with a
declared and an undeclared link member.

### G-05 — mandatory — The map omits executor requirements that change on macOS (A2)

**Location:** CONTRACT.md section 1; CONTRACT.json `substitutions`, `kept`, `not_applicable`.

**Evidence.** Neither CONTRACT.md nor CONTRACT.json classifies E1 to E19 (C10). Most of them are
covered implicitly by S1 to S8. These are not:
- **E8.** M0 and MC06 refuse `DYLD_*` only in M0's environment. The qualifying unit-test process,
  which runs the provider and the independent oracle, inherits the driver's environment. Only
  `LD_PRELOAD`, `LD_LIBRARY_PATH`, `NODE_OPTIONS`, `NODE_PATH` and seven `PYTHON*` startup
  variables are removed (driver lines 489-491).
- **E18.** The Git closure. The P29 inspector binds `/usr/bin/git` under `PATH=/usr/bin:/bin`
  (`_check_git`). On this host that is a dispatcher-sized universal binary (C8), and the driver's
  `git_read` uses the ambient PATH. The clean commit and tree binding rests on Git output whose
  executable is not bound.
- **E15.** The launcher `-I -S -B` (`_check_launcher`). M0 reads the package versions "through
  importlib.metadata", and with `-S` a venv's site-packages is not on `sys.path`. Either E15 is
  dropped, or M0 must read metadata by path. The contract says neither.
- **E9 and E17.** P07 section 2's operational-plan fields and outer-capture authority change on
  macOS: one or two literal commands, no P29 inspector, canonical macOS paths. The contract
  restates only P07's counting rules.
- **E10 and E11.** N34's macOS analogue (independent review of the Mach-O parser and the
  closure claim) is not decided. N57 is not mentioned.

A2 also requires each term's effect on the original test meaning. No row states one (see G-06).

**Correction.** Add an E1-E19 table, and a table of P05 terms, marking each kept, substituted or
not applicable, with its reason and its effect on meaning. Also:
- Specify the driver's macOS removal list: `DYLD_INSERT_LIBRARIES`, `DYLD_LIBRARY_PATH`,
  `DYLD_FRAMEWORK_PATH`, `DYLD_FALLBACK_LIBRARY_PATH`, `DYLD_FALLBACK_FRAMEWORK_PATH`,
  `DYLD_VERSIONED_*`, `DYLD_IMAGE_SUFFIX`, `__PYVENV_LAUNCHER__` and `PYTHONEXECUTABLE`.
- Define the macOS Git closure for M0 and for the provider's source reads.
- State M0's launcher.
- Restate E9 and E17 for M0 and M1.
- Decide N34's analogue, and record N57 as open.

### G-06 — mandatory — The meaning of `check_case`'s lifecycle assertions changes, and this is not stated

**Location:** CONTRACT.md section 4 (guarantees table) and S4 "Why"; CONTRACT.json
`supervisor.guarantees`; section 1, "preserve ... process supervision".

**Evidence.** `check_case` asserts `process["cleanup"]["passed"]` and `handles_closed` (test lines
148-149). On Darwin, the imported `terminate_group` and the re-implemented `run_process` body
still write `"reaped": True` and `"process_group_absent": True` (supervisor lines 150-151 and
225-226). Without a subreaper,
`_reap` (`waitpid(-pid)`) reaches only the direct child, and orphaned descendants are reaped by
launchd. Per general knowledge of the XNU source (not verified here), Darwin's process-group
probe also skips zombies.

P30 section 6 route C names exactly this as a known difficulty: the assertions would be backed by
a different mechanism, which changes their meaning. The contract answers it with "preventing
descendants", and that answer is unsupported (G-01). The objective is to keep the original test
meaning, yet no statement of the narrowed meaning appears.

**Correction.** In the guarantees table and the labels, state what `cleanup.passed`, `reaped` and
`process_group_absent` mean under 0.2.0: the direct child was reaped, no live member of its group
remains, and descendants are not reaped by the supervisor. Keep "no descendant" only as a
seat-belt property of bound code, or add a reviewed Darwin descendant check, for example libproc
enumeration before and after, with its own controls.

### G-07 — nonmandatory — The qualification Python's identity and closure are unstated

**Location:** CONTRACT.md section 3 and section 6 (M0 "Python" row, closure claim); CONTRACT.json
`python`, `host_observation.closure_claim`.

**Evidence.** Recording the "resolved executable" identifies the 52,448-byte framework launcher,
not the interpreter (C8). The interpreter's code is in the framework library. The standard
library's extension modules, and non-system libraries such as the OpenSSL that `hashlib` can use
for every binding digest, are real files outside the shared cache. E4 pinned the Linux image by
bytes, and the closure claim speaks only of Node.

**Correction.** Either bind the launcher, the `Python.app` executable, the framework library, the
standard library with its extension modules, and the non-system libraries, or state that the
Python is identified by path, version and build only. If the latter, say this is weaker than E4
and carry it in the closure claim and the labels.

### G-08 — nonmandatory — The selection rule's scope is understated

**Location:** CONTRACT.md section 7 and section 8, last paragraph ("P05's CH01 to CH20 keep their
meaning"); CONTRACT.json `selection_rule`, MC19.

**Evidence.**
- P05 section 2 forbids replacing the old skip "with another skip" and requires direct
  invocation's setup to fail visibly. CH13 expects no skip. MC19 inverts CH13 for ordinary runs,
  so "keep their meaning" is false for CH13.
- A CPU class that skips when the variables are absent also changes direct invocation.
- Both drivers mark the unit step failed on any skip (C11). The contract does not say that an
  ordinary run's unit stage stays failed.
- It weighed only "always require a selection". It did not weigh "proceed, and let the CPU class
  fail visibly", which needs no skip and no amendment of P05's no-skip rule.

**Correction.** Name every amended P05 term: section 2's text, `absent_behavior` and CH13. State
the behaviour of direct invocation, and the status of an ordinary run's unit step. Weigh the
visible-error alternative.

### G-09 — nonmandatory — Gate names and sequencing

**Location:** CONTRACT.md section 10; CONTRACT.json `gates`.

**Evidence.**
- "H2" is P07's operational-freeze stage, "R" is P05's and P07's Gate R, and "P2" sits next to the
  task's plan step P02.
- MAIN-CONFLICTS.md says R04 resolves the overlaps "after R03". Gate B moves that resolution
  before R03 without saying so.
- On this executor, main's local unit baseline has 103 failures and 311 errors (C11). Gate R does
  not say how R03 treats these pre-existing failures under OK-ENG-009's legacy-failure rule.

**Correction.** Give the 0.2.0 gates distinct names, and state that the 0.1.0 Gates H and R stay
unmet. Justify gate B's change of order. Define R03's treatment of the recorded macOS legacy
failures.

### G-10 — nonmandatory — M0, closure and filesystem details for macOS

**Location:** CONTRACT.md sections 5 and 6; CONTRACT.json `preparer`, `host_observation`.

**Evidence.**
- The OS build comes from `SystemVersion.plist` alone. The shared cache can change through OS
  cryptex security updates, and SIP and the sealed system volume are unstated assumptions.
- The load-command rule names three dylib commands, so `LC_LOAD_UPWARD_DYLIB`,
  `LC_DYLD_ENVIRONMENT` and unknown commands are not refused.
- `RENAME_EXCL` depends on the volume's capability. ENOTSUP would reach the preparer's UNKNOWN
  path rather than a clean refusal.
- `/tmp`, `/var` and `/etc` are links (C8), and the provider and preparer refuse linked path
  components.
- `fsync` on macOS is weaker than `F_FULLFSYNC`.
- Git ignores `.DS_Store`, but the provider's and the probe's source walks do not. A stray one
  appearing in a walked tree after the inventory is frozen would therefore refuse the source
  binding.

**Correction.** Also record `kern.osversion` or the cryptex version, and state SIP and the seal as
trust boundaries. Use a closed load-command allow-list. Bind the volume's filesystem and its
rename capability in M0, and refuse on ENOTSUP. Require canonical `/private` or volume paths.
Qualify the durability wording.

### G-11 — nonmandatory — Control-table consistency and coverage

**Location:** CONTRACT.md section 8; CONTRACT.json `controls`, `p05_control_map`.

**Evidence.**
- MC12's non-Node child is counted as a Node start (`expected_node_starts: 1`).
- MC13 and MC20 are `null` in JSON but "1 each" and "per run" in CONTRACT.md.
- Section 8 says the mapping is "one to one", but several CH controls map to two or more MCs.
- Coverage is partial for CH02 (alias and resolved path), CH03 (declared version), CH07 (C195
  archive extraction), CH08 (partial, changed or linked existing destination) and CH10
  (time-of-use synchronization).
- No control covers grant sufficiency, the loader under the flags, ENOTSUP, or the Darwin
  supervisor's own precondition.

**Correction.** Count Node and non-Node starts separately, and align the two files. Reword "one
to one". Add the missing controls, or state what each partially mapped CH loses.

### G-12 — nonmandatory — Read set and wording

**Location:** READ-SET.json; CONTRACT.md sections 1 and 9; CONTRACT.json `schemas`.

**Evidence.**
- PHASE.json declares as inputs the P29 inspector, main's `tools/check_local.py`, P30's
  EXECUTOR-INVENTORY.json and P07's ADOPTION.json. None is in the read set, and neither is
  `format_check.py`, whose NODE_FLAGS and ENVIRONMENT the design reuses.
- "Substitutes only what cannot exist on macOS" does not fit S5 or S8.
- Section 9 omits N57.
- Only four schemas are versioned, although "each version's entry points refuse the other's
  documents". That also covers the source, dependencies, methods, discovery, workspace,
  inspection, attempt, setup and cohort documents.
- The test module's docstring still names ldd.

**Correction.** Add those inputs with their identities and fix the wording. List N57 as open.
Version every document schema. Include the docstring in the reviewed setup diff.

## 5. What holds

- **Inputs and pins.** All 22 read-set identities, the darwin-arm64 archive pin, and the checksum
  file's size and digest recompute. So do the host facts the contract cites: the boot session
  UUID, untranslated execution, 26.6.2 (25G83), and `renamex_np` present. The macOS lock pins the
  same seven names and versions.
- **Supervisor variant.** It imports `Clock` and `Stop` from the original module. That keeps the
  class identities that `check_case` (`except Stop`) and the provider
  (`isinstance(delegated, supervisor.Stop)`, `isinstance(clock, supervisor.Clock)`) depend on.
- **The "only change" claim.** Lines 171-173 are the only Linux-specific code in `run_process`, so
  the claim holds at the code level. The imported helpers use POSIX calls available on Darwin;
  their changed semantics are G-06.
- **Gates, labels and status.** The Linux gates stay unmet, the never-supported list includes
  P30's, and the results carry the executor label. Nothing claims execution, adoption or
  implementation. The amendment of `absent_behavior` is explicit.

## 6. Verdict

**REJECT_WITH_MANDATORY_FINDINGS.** G-01 to G-06 are mandatory. G-01 and G-02 each show that,
under the contract's own launch, no checker start can succeed. Both rest on the v24.22.1
documentation and on tracing the source; nothing was run. G-07 to G-12 are nonmandatory.

## 7. Command and write policy

- Never started: node, npm, ldd, codesign, any container or VM tool, any test, or the driver.
- Nothing was downloaded or installed. The only network reads were the checksum file and two
  documentation pages, over HTTPS to standard output.
- Git use was read-only (`show`, `ls-tree`, `cat-file`, `rev-parse`, `log`, `diff`, and one
  `status --porcelain --untracked-files=no`), always with `--no-optional-locks`. No ref, index or
  working file was changed.
- Host facts were limited to the reads listed in C6 to C8.
- Write scope: these two files. Temporary `git show` copies and two small helper scripts were
  also written to the session's private scratchpad, outside both checkouts, and removed after
  use. This is a disclosed departure from "write only in review/".
- The review files do not name applications installed on the owner's computer.
