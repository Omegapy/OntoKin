# Independent review 001 of gate MI (C271-P33)

- **Reviewer:** W7, a fresh-context independent reviewer launched by the Director. It wrote none of
  the implementation, the controls or the decisions, and worked read-only in the checkout.
- **Candidate:** commit `2d8d6d15cd04725e0d29050253e22768f58e2c78` on
  `work/c271-missing-import-digest-control`. The phase started at `1c2f25ba`.
- **Reviewed against:** `ontokin.current-host-readback/0.2.0`, profile `darwin-arm64-v1`, design
  revision 4: CONTRACT.md and CONTRACT.json of C271-P31 as amended by P33-AMENDMENT-001.
- **Verdict: ACCEPT_WITH_NONMANDATORY_FINDINGS.** There is no mandatory finding. The eight
  nonmandatory findings I-01 to I-08 are listed at the end. I-01 should be resolved before MH.

Scratch work and logs are beside the clone in `../OntoKin-local/c271-p33/reviews/mi-001/`. The
log of `tests.test_current_host_readback_driver` was redacted with the Director's script. This
review quotes no environment value.

## Method

- **Read:** AGENTS.md, PROTOCOL section 5, PHASE.json, the implementation plan, D-01 to D-19,
  the contract, the amendment and its adoption record, CONTROLS-FROZEN.json, the refreeze record,
  CHECKS.json, INVENTORY-ADDITIONS.json, the interface notes, and the phase diff. The diff covers
  44 files and 28,634 insertions.
- **Implementation read:**
  - the Darwin supervisor, the 0.2.0 preparer route and the observer;
  - the 0.2.0 provider and probe, and the facade appended to the 0.1.0 provider;
  - the driver and `storage_identity`, with their development tests.
- **Reproduced:**
  - the identity checks;
  - an independent MC14 token comparison;
  - an independent derivation of the probe's scientific body;
  - all sixteen modules that CHECKS.json lists, one process each, with `.venv/bin/python -B` and
    a resolved TMPDIR;
  - the log and record digests;
  - one demonstration script for I-01, which started no process.
- **Not run:** Node, `ldd` or `codesign`; any other test module or discovery; the workflow check
  and the documentation verifier, which are not among the sixteen modules (final-002 records
  them as passed); downloads and installs.

## 1. Conformance

| Change | Assessment |
| --- | --- |
| S1 Node pin | Conforms. The preparer, the observer, the provider and the probe all carry the archive pin `89c68259…bc0a7`, the checksum-file identity and `v24.22.1`. The executable pin comes only from the frozen plan and HOST. The probe hashes `process.execPath` against HOST's pin. |
| S2 Python inventory | Conforms. Both trees are inventoried as exact entry maps, with files by SHA-256, size and mode, links by target and directories by mode. The inventory also holds the selection chain from `.venv/bin/python` through `pyvenv.cfg`'s `home`, and the transitive Mach-O closure with every link hop. It is compared as exact sets by M0 and again by the provider at every `_selection`. Package metadata is read by path, and RECORD rows are checked against the bytes. |
| S3, S7 M0 and M1 | Conform. The Node allow-list holds exactly the contract's 16 commands, and the Node and Python refusals are as written. The Python side adds `LC_ID_DYLIB` and `LC_RPATH`, and `@`-relative loads must resolve to bound files. The OS identity binds `SystemVersion.plist` and the cryptex copy (see D-10). `sysctl.proc_translated` and `kern.bootsessionuuid` are read through `sysctlbyname`. The provider reads the boot, OS build and cryptex identity before the cohort and before and after each start (`_check_state`). M1 is one `node --version` through the Darwin supervisor within the 5,000 ms command clock. The probe checks `os.type()`, `os.release()`, `os.machine()` and the OS files, and no longer checks the boot: the stated weakening of E19. |
| S4 Darwin supervisor | Conforms. The imports are exactly `Clock`, `Stop`, `LIMITS`, `inventory`, `json_bytes` and `_reap`. My own token comparison (section 2) finds exactly the five change sites of the amendment's section 3.2. The precondition checks `sys.platform`, `os.uname().machine` and `sysctl.proc_translated`, fails closed when the value cannot be read, and raises `Stop("OTRAY-E-BACKEND", …)` before any start. |
| S6 preparer | Conforms. The archive is hashed against the pin before `tarfile` opens it. Member names must be relative and normalized; a duplicate refuses. Hard links, devices, FIFOs, sparse and undeclared members refuse, and so does a link target that leaves the archive root. Only `bin/node` is read, and its header must be thin, 64-bit, arm64 and `MH_EXECUTE`; the header is read again before publication. `NODE-SOURCE.json` is built from the plan alone and must equal its frozen bytes. Publication is `renamex_np(staged, destination, RENAME_EXCL)` from libSystem, with no fallback. The flag value `0x00000004` and the prototype `(const char *, const char *, unsigned int)` agree with the installed macOS SDK headers, whose digests match W2's note. EEXIST, ENOTSUP and every other failure refuse, with a readback of the destination. The CLI never passes the synthetic pin seam, and M0 refuses a receipt made through it (`pins.origin` must be `adopted-contract`). |
| S8 selection | Conforms. An ordinary run records `{"status": "absent", "run_kind": "ordinary"}`, passes no selection and proceeds. The readback class then fails at `setUpClass` with the fixed reason, which I reproduced: one class-level error, the three methods neither run nor reported, the four seams `ok`. A partial selection fails in the driver and at setup. A qualifying run keeps every rule. |
| S9 removal list, Git | Conforms. `UNIT_REMOVED_ENVIRONMENT` is the existing 11 names plus every `DYLD_*`, `__PYVENV_LAUNCHER__` and `PYTHONEXECUTABLE`. `bind_git` refuses a relative, non-canonical or linked path, the `/usr/bin/git` dispatcher, its file under another name, a copy of its bytes and a second binding. `git_executable()` re-hashes a bound Git at every start and never falls back to `PATH`. A qualifying run binds Git before its first Git start, and the 0.2.0 provider binds the same Git in the unit process. |
| S10 `__CF_USER_TEXT_ENCODING` | Conforms. The one predicate admits exactly the declared map, or that map plus the variable with the recorded, non-empty value. It is applied by M0, by the provider's HOST comparison and, in the probe, to `process.env`. The supervisor passes exactly the declared environment. |
| Section 1 schemas | Conform. The provider's config, lock, host, source, dependencies, methods, discovery, workspace, inspection, attempt, setup, cohort, refusal and preserved-cohort documents are at `/0.2.0`, and so are the probe's result, `node-source`, the preparer's install and install-result, and M0's observation plan. Each entry point refuses the other version's documents. One path breaks this rule: after a configuration change between setup and teardown, the 0.1.0 accounting writes a `cohort/0.1.0` document into a 0.2.0 cohort (I-01). |
| Section 10 labels | Conform. Results and refusals carry the executor, the contract, `design_revision` 4, `amendments` `["P33-AMENDMENT-001"]`, the profile, the OS label with the cryptex, the Node pins, the Python inventory digest, the Git binding, the run kind and the boundary. A substituted boundary labels a result `mocked`. The provider accepts only a HOST whose `labels.boundary` is `real`. |

## 2. Preservation

- **Byte-identical to the phase start:** `supervisor.py`, the 0.1.0 probe, the inspector,
  `readback.mjs` and `tests/test_current_host_readback_driver.py`. The last is P29's companion,
  at `cb103f55…`.
- **The 0.1.0 provider:** its first 65,533 bytes are exactly the committed file. The facade is
  appended after them.
- **The readback test module:** only the docstring differs. The bytes after the docstring are
  identical, and so is the AST without it.
- **0.1.0 behaviour of the shared files:** unchanged apart from the sanctioned changes.
  - The facade sends every call that is not a digest-matching 0.2.0 configuration to the
    original functions. Their internal calls pass through the dispatch, at the cost of one more
    configuration read.
  - The existing 0.1.0 provider module keeps exactly its phase-start outcome: 22 of 25 pass.
  - The driver's S8 and S9 changes apply to every run, as plan section 2 states.
  - `git_metadata` now resolves the `PATH` Git once per process and records it as unbound. This
    is equivalent behaviour, and other importers of `git_metadata` inherit it.
- **Probe scientific body (re-derived):** I aligned `readback.mjs` with both probes by exact
  lines, independently of W5's map. The body is identical in both probes: SHA-256 `5d72ac44…`,
  with the same order and contiguity.
  - Its 0.1.0 lines are 1–38, 679, 683–691 and 695–809, matching W5's
    `scientific_body_origin`.
  - Its 0.2.0 lines are 1–38, 703, 708–716 and 720–834.
  - The adaptations are confined to bootstrap lines, and every helper they call is defined in
    the file.
  - A crude structural pass, a heuristic and not a parser, finds all three files balanced. The
    syntax start at MH remains the first execution of the file.
- **MC14 (re-run):** an independent tokenize comparison of `run_process`, `group_exists` and
  `terminate_group` finds exactly five statement-level sites:
  - the precondition, original lines 171–173;
  - `except PermissionError: return True`, inserted before `except ProcessLookupError:`;
  - three sends that become `except (ProcessLookupError, PermissionError):`.

  Nothing else differs, comments and docstrings included.

## 3. Controls

- **Faithful to the contract:** each of the 149 methods maps to its contract row. That covers
  MC01–MC10, MC12–MC22, MC29, MC31–MC35 and MC37–MC39, with MC11, MC23 and MC30 in part, as
  plan section 6 and D-12 assign.
  - The expected outcomes are the contract's. The supervisor controls apply the amended rule:
    EPERM means present. MC37 to MC39 assert their premises, so a build that answers otherwise
    fails visibly.
  - I found no expectation tuned to the implementation. W6's findings F-01 to F-09 state the
    coverage limits honestly, for example MC10's substituted static facts and MC09's simulated
    `host_state`.
  - One small coverage gap remains (I-08).
- **Ran as frozen:**
  - `65c54179` was committed at 18:09:02Z, and final-001 started at 18:09:23Z, on a clean tree.
  - `574dc196` was committed at 18:42:33Z, and final-002 started at 18:42:42Z.
  - CONTROLS-FROZEN.json is byte-identical to its first commit.
  - No implementation file changed after `65c54179`. Every digest in the freeze and the
    refreeze matches the candidate.
- **Outcomes:** final-002 supports each claimed result.
  - All 31 log digests in CHECKS.json match the retained logs.
  - My run gave non-passing sets identical to final-002 for all sixteen modules: the six new
    modules and `test_local_checks` OK with zero skips; 149 controls OK.
- **Labels:** every method's docstring starts with its label. The counts are real 60, simulated
  67 and mocked 22. CONTROLS-FROZEN.json and the refreeze record the boundaries, and the
  provider's own records say `mocked` when a boundary is substituted.

## 4. Baselines

Every existing module's non-passing set is identical to its phase-start baseline, with one
exception: D-18's three entries in `tests.test_current_host_readback_driver`, two failures and one
error. I reproduced that. The readback module's `setUpClass` error keeps its identifier. Its
message was "Set both … from the independently reviewed execution plan" at the phase start, and is
now S8's fixed reason.

## 5. Decisions

- **D-10 (cryptex path): a sound reading.**
  - On this host `/System/Cryptexes/OS` is one link, and the realpath of the copy has no other
    link.
  - The copy is bound by its canonical path. The conventional name and the hop are recorded, and
    they are followed again by M0's post-start recheck, by the provider's `host_state`
    comparison and by the probe's `verifyOsIdentity`. A retargeted hop refuses.
  - Paths that a plan or configuration supplies keep the strict rule.
- **D-17 (preparer source binding): a sound reading.**
  - P05 section 5 requires authenticated archive bytes, a predeclared member inventory, the
    refusals, staging and no-replace publication, and trees kept outside Git with their source
    identity and reproduction receipt. It does not require a check of the checkout's commit.
  - The 0.2.0 route meets every one of these and starts no Git.
  - The substitute binding is narrower than D-17's wording suggests (I-03).
- **D-18 (P29's frozen companion): the right choice.**
  - It keeps P29's 116 controls loading, with only their two phase-start errors. It keeps S8's
    change visible and changes no expectation.
  - W4's units moved unchanged. An AST comparison of every unit of W4's file at `65c54179`
    against the new module found them identical, apart from the class that now holds only the
    two S8 versions.
  - Both failures are exactly S8's change:
    - `test_missing_explicit_selection_cannot_use_ambient_approval` expects refusal at
      preparation for a run without arguments, which is now an ordinary run that proceeds.
    - `test_failed_prelaunch_…` relies on the pre-S8 driver preparing a selection without
      arguments. Its mocked `prepare_readback_selection` is no longer reached, so the ordinary
      run calls its mocked `Popen`. The `TypeError` (a MagicMock is not JSON serializable) is an
      artifact of that mock.
  - D-18 says both tests "assert the ordinary-run refusal". That is exact for the first and
    loose for the second.
  - The failures will confront MR's complete routine as well as R04 (I-05).
- **D-19 and refreeze 001: two genuine control defects.**
  - C-01: real facts always hold the full inventory document that `observe_host` reads. Only the
    synthetic facts lacked `framework`.
  - C-02: Python caches `platform.platform()`, which starts `uname -p` and `file -b` in the
    first driver run of a process, so the count depended on test order.
  - The original is retained, and the refreeze touches exactly six methods.
  - No assertion was removed, and MC10 gained a premise assertion.
  - No contract expectation is weaker. MC21's driver cases now mock the platform leaf and are
    labelled `mocked`, so their zero-start assertion no longer covers those two metadata starts.
    The original freeze asserted that property beyond the contract's Node and other columns.
    D-19 keeps the qualifying-run question open for MR.
- **Other decisions:** none is a hidden contract change.
  - D-06, and the observer's refusal of universal files and of any CPU subtype other than
    `CPU_SUBTYPE_ARM64_ALL`, are stricter than the contract and fail closed. MP and N34-M
    confirm the real files.
  - D-02, D-04, D-14 and D-15 stay within the contract's text.
- **W6's F-07, referred to this review:** a refusal of an unverifiable 0.2.0 selection is raised
  by the 0.1.0 code and is not written as a document. It fails closed and claims nothing, so
  written results do not breach section 10. Naming the 0.1.0 contract on the 0.2.0 executor is
  still misleading, and I-01 covers it.

## 6. Safety

- **Node or `ldd`:** no path starts either during MI.
  - The audit records 877 starts by the test processes: Git, stand-ins, Python, `uname`, `file`
    and `git-lfs`. None is Node, `ldd` or `codesign`.
  - The 22 "git" starts of the provider tests are temporary `/bin/sh` stand-ins.
  - The child programs I read are:
    - Python `-c` codes;
    - synthetic discoveries in temporary workspaces;
    - the observer's CLI on refused plans;
    - the readback module's refused ordinary setup.
  - Every MI test of the provider's start path mocks the Darwin supervisor.
  - Node processes that belong to other software ran on the host throughout. They started hours
    before these runs, and no run started one.
- **A refusal that passes:** none found.
  - The synthetic pin seam is reachable only by a direct call, labels its results
    `synthetic-test-seam` and is refused by M0.
  - A mocked HOST cannot pass `_check_host_labels`.
  - The facade routes only a digest-matching 0.2.0 configuration to 0.2.0.
- **Hidden skip:** none. The drivers count every skip as a failure. W3's module adds conditional
  skips, which are visible but environment-dependent (I-02).
- **Process left running:** none.
  - After my run, no test process remained.
  - MC39 (a) asserts its own teardown.
  - A lasting EPERM fails the Darwin supervisor at the cleanup ceiling.
  - O-01, the `stop_process` EPERM window that the adoption record names, stays recorded (I-05).
- **Writes into the source tree:** none. The tree was clean before and after, with no new
  `__pycache__`. MC16 targets a never-created name beside the checkout, and the call fails with
  EXDEV.
- **A weakened 0.1.0 rule:** none. Section 2 lists the changes, all sanctioned.

## 7. Records

- **CHECKS.json:** accurate.
  - It states what ran and what did not, and its limits: "they qualify nothing".
  - It keeps environment readiness (`python-verification` missing until MP), test qualification,
    integration (main not written) and product completion (`parent_complete: false`) apart.
  - Its counts, digests and outcomes reproduce.
- **Inventory listing:** its "nothing is run" means that no test ran. The listing imported every
  module.
- **Session checkpoint:** still the declaration version, as expected before A9's closing records.
- **Nonmandatory record items:** I-04, I-05 and I-06.

## Findings

| ID | Severity | Location | Issue | Required change |
| --- | --- | --- | --- | --- |
| I-01 | nonmandatory, before MH | `prototypes/static_tray_v01/current_host_readback_v01.py`, the facade's `setup_cpu_cohort`, `guarded_run_process` and `finish_cpu_cohort` | The version is decided again at every call from the configuration's current bytes. Once a 0.2.0 configuration changes between setup and teardown, `finish_cpu_cohort` runs the 0.1.0 accounting. That accounting refuses, then writes `cohort/0.1.0` into the 0.2.0 cohort root, without design revision or labels; with an owned temporary cohort it also writes `preserved-cohort/0.1.0`. `mi-001/dispatch_finish_demo.py` reproduces this, starting no process. The run still fails closed. Related: refusals of unverifiable selections and the ordinary-run refusal name `refusal/0.1.0` and `setup/0.1.0` in memory (W6 F-07, W5 Q4), and a refused probe result can carry unverified manifest labels (W5 Q5). | Bind the version chosen at setup to the class, and dispatch `guarded_run_process` and `finish_cpu_cohort` by it, so that a 0.2.0 cohort is always reconciled by the 0.2.0 accounting, which refuses and writes `cohort/0.2.0` with labels. Consider a version-neutral refusal for unverifiable selections, and mark the labels of a refused probe result as unverified. Add a control. |
| I-02 | nonmandatory | `tests/test_current_host_observation_v02.py`, `CanonicalPathTests.test_mc20_system_link_ancestor_is_admitted_and_resolved`; also `needs_darwin` and `PlatformTests.test_real_readers_return_their_shapes` | The first test skips unless the resolved TMPDIR lies under `/private/var`; the others skip off Darwin. With the executor's default TMPDIR nothing skips. A qualifying run with another resolved TMPDIR would report a skip and fail its unit stage. The other new modules fail visibly instead of skipping. | Build the `/var` case from a fixed `/private/var` location, independent of TMPDIR, or turn the skips into visible failures. Otherwise record the TMPDIR premise for MH and MR. |
| I-03 | nonmandatory | `tools/prepare_current_host_readback.py` `PREPARER_FILES_V02`; D-17 | `preparer_source` records four files. The preparer also executes `errors.py`, `format_check.py`, `lock.py`, `supervisor.py` and the package `__init__` files, and no commit or clean-state check runs. The check that D-17 assigns to MP's reviewer therefore covers only those four files. | Record the preparer's import closure, or a source inventory, in `preparer_source`. Otherwise have MP's plan state the receipt's limit and require a separately verified clean checkout at the bound commit. |
| I-04 | nonmandatory | `interfaces/W2-PREPARER.md`, sections 11 (D2) and 12 (Q1) | The note still says that D-01's source check will be added and is "not implemented yet". D-17 replaced D-01, and the route starts no Git by design. | Mark D2 and Q1 as superseded by D-17, in the note or in the closing record. |
| I-05 | nonmandatory | phase closing records | MI's obligations for later gates are scattered across D-16, D-19, O-01, W6 F-01, F-03, F-04 and F-05, D-02, D-06, W3 F4 and Q1/Q3, and the frozen record's MC16 note. Two are not stated where the next gates will look. First, inside the driver's unit stage the controls run from the isolated workspace under the evidence root, so MC16's real cases need the evidence root and TMPDIR on different volumes. Second, D-18's two failing 0.1.0 driver tests also confront MR's complete routine, not only R04. | List the carried obligations for MP, MH, MR and R04 in one place in the closing record, with these two added. |
| I-06 | nonmandatory, minor | `docs/workflow/tasks/C271/task.json`, the P10 and P16 entries | The declaration's rewrite re-encoded two historical strings (`–` became `–`). The values are unchanged, but the historical bytes changed. | Keep historical entries byte-stable in later writes, or note the re-encoding. |
| I-07 | nonmandatory, low, inherited | `current_host_readback_v02.finish_cpu_cohort` (and the 0.1.0 function) | The cohort accounting reads each attempt ledger without checking its schema. The risk is low, because the directory is fresh and owned. | Require `attempt/0.2.0`, with the contract, design revision and amendments, in the 0.2.0 accounting. |
| I-08 | nonmandatory, low | `tests/test_current_host_readback_controls_v02.py`, MC06 | No control shows that the allow-listed `LC_DYLD_INFO_ONLY` is accepted: the baseline executable uses chained fixups. The implementation admits it (`0x80000022`). | Add an accepting variant at the next refreeze, or at N34-M or MH. |

## Reproduction

Commands ran from the checkout root unless stated. Scratch files are in
`../OntoKin-local/c271-p33/reviews/mi-001/`.

| Check | Outcome |
| --- | --- |
| `shasum -a 256` of CONTRACT.md and .json, AMENDMENT-001.md and .json, both amendment reviews and the evidence files | equal to ADOPTION-AMENDMENT-001.json; `git diff 1c2f25ba 2d8d6d15 --` over the P05, P29 and P31 directories is empty |
| `git --no-optional-locks diff --quiet 1c2f25ba 2d8d6d15 -- supervisor.py, the 0.1.0 .mjs, the inspector, readback.mjs, the 0.1.0 driver test` | exit 0 |
| Python byte comparison of the 0.1.0 provider | the first 65,533 bytes are identical |
| AST and byte comparison of the readback test module | only the docstring differs |
| `python3 -I -S -B mi-001/mc14_tokens.py` | five sites (`mc14_tokens.out.txt`) |
| `python3 -I -S -B mi-001/probe_body.py` | body identical, `5d72ac44…` (`probe_body.out.txt`) |
| `python3 -I -S -B mi-001/js_balance.py` | all balanced; a heuristic only |
| `zsh mi-001/run_modules.sh mi-001/run-001` (`.venv/bin/python -B -m unittest -v <module>`, resolved TMPDIR, each log redacted) | sixteen modules; non-passing sets identical to final-002; identical to the baselines except D-18; zero skips; tree clean and no new `__pycache__` afterwards |
| Log digests in CHECKS.json | 31 of 31 match final-001 and final-002 |
| `git diff 65c54179 2d8d6d15` for implementation files; CONTROLS-FROZEN.json; the last two commits | no implementation change; the freeze byte-identical; only CHECKS.json and INVENTORY-ADDITIONS.json added |
| P29 COMPANIONS.json digests against the candidate | 24 of 24 match |
| AST unit comparison of W4's file at `65c54179` with the v02 module | identical units |
| `final-002-audit/starts.jsonl` | 877 `subprocess.Popen` events, no Node, `ldd` or `codesign`; the provider tests' 22 Git starts are temporary stand-ins |
| `.venv/bin/python -I -B mi-001/dispatch_finish_demo.py <checkout>` | `cohort/0.1.0` written after a configuration change (I-01) |
| `git --no-optional-locks diff --check 1c2f25ba 2d8d6d15` | clean |
| The SDK's `sys/stdio.h` | `RENAME_EXCL` `0x00000004`, prototype as bound |
| Python `lstat` and `readlink` of the cryptex link | one hop; the realpath has no other link |
| Process listing after the runs | no test process left |

## Evidence

- My scratch: `../OntoKin-local/c271-p33/reviews/mi-001/` (run-001 and the scripts).
- The Director's runs: `../OntoKin-local/c271-p33/checks/final-001/`, `final-002/`,
  `final-002-audit/` and `d18-split/`.
- Baselines: `../OntoKin-local/c271-p33/baseline-1c2f25ba/`.

**Limits.** This review covers only the executed Python on this host. It qualifies nothing. MP,
N34-M, MH, MR, R04 and R05 remain separate gates.
