# C271-P30: review of the /0.1.5 operational plan

Phase C271-P30-operational-plan-review, Director `c271-p30-55a168e30426`, local mode
([declaration](PHASE.json)). Reviewed on branch revision `7a4ab16248ed071a211ded3e24e1558ec064f0b1`
(the declaration) and current main `51223c9b94a222f29d38eb6c33808f8e55e2bff9`. At that revision every
input is byte-identical to `4ee55b037b909b36cb8a6330aa07ccc78071af88` except the four workflow
records that the declaration updated (`task.json`, the branch `CURRENT.json`, `REQUIREMENTS.md` and
`PLAN.md`). In those four, the parts this review relies on are unchanged: `remaining_h0_constraint`,
the requirement and plan states, and the task status. Inputs and their identities:
[read set](READ-SET.json) and [additions](READ-SET-ADDITIONS.json). Times are UTC. Machine paths of
this host are left out.

**Corrected version.** The first version, commit `8aa4a80012a14a521a441b306635c4fad68ca573`, was
rejected by the [independent review](INDEPENDENT-REVIEW-001.md) on one mandatory finding, F-01:
route C omitted the Linux-only original supervisor and the provider's and probe's Linux host
bindings. The corrected version, commit `96847fae5c3f0a6d9e9d6da3095b056a8b929b62`, resolves F-01
and the ten nonmandatory findings. The [re-review](INDEPENDENT-REVIEW-002.md) accepted it with
seven nonmandatory findings, F-12 to F-18. This final version resolves those after the re-review,
without a further review. [REVIEW-DISPOSITION](REVIEW-DISPOSITION.json) maps every finding to its
change.

Nothing in this review ran H0, H1, Node, `ldd`, a loader, the routine driver, the unit suite or a
behavioural test. Host facts were gathered read-only (platform identification and tool presence).
Statements marked *source inference* come from reading source, not from running it.

## Outcome

**No existing executor available to this local session meets the adopted contract.** The
`/0.1.5` operational plan can be neither prepared nor executed here. This is concrete blocker
**P30-EXECUTOR-001**. No further preparation work is selected: each candidate item, with the
reason, is in section 5. How C271 continues is the owner's decision. Section 6 states the routes
that remain, each with what it would substitute and what it can never show.

The blocker concerns where the plan can run. It finds no defect in the published P29 candidate,
changes no adopted design and qualifies no host.

## 1. What was reviewed

The operational plan is P07's staged qualification plan
([QUALIFICATION-PLAN](../host-inspection-p07/QUALIFICATION-PLAN.md)): HI authoring, H0 static
preparation and review, H1 host observation, H2 operational freeze, H3 actual Gate H, and R, the
complete routine for R03. Its [adoption record](../host-inspection-p07/ADOPTION.json) accepts it as
a nonexecutable design only (`accepted_design_only`, `executable_authority` false).

Read with it as adopted supplements:

| Record | Adds |
| --- | --- |
| [P05](../current-host-p05/ADOPTION.json), adopted before P07 | The contract `ontokin.current-host-readback/0.1.0`: the explicit provider, one exact Node build, the exact 24 reader files, the HOST observation, the original supervisor and the fixed scientific and process obligations, and Gates D, I, H and R ([contract](../current-host-p05/CONTRACT.md)) |
| [P11](../loader-path-p11/ADOPTION.json) | `/0.1.1`: a guarded `$ORIGIN/../lib` derivation for the exact selected author-Python image only |
| [P13](../review-boundary-p13/ADOPTION.json) | Actual-loader suffix completeness (N34) is an external independent-review prerequisite for adopting or executing an operational plan; N57 stays external review only |
| [P16](../libc-tags-p16/ADOPTION.json) | `/0.1.2`: three x86-64 PLT dynamic tags for the bound libc only |
| [P17](../libc-flags-p17/ADOPTION.json) | `/0.1.3`: exact `DT_FLAGS` value 24 for the bound libc only |
| [P24](../path-design-p24/ADOPTION.json) | `/0.1.4`: the finite RTLD path policy (the literal `ldd` candidate list, two absence witnesses, nine physical components) |
| [P27](../required-image-design-p27/ADOPTION.json) | `/0.1.5`: the five catalog images libdl, libm, libpthread, librt and libutil, and their common loader |

The published P29 inspector implements `/0.1.1` to `/0.1.5`: 249,393 bytes, SHA-256
`71e837c31df06df7ce10262683c5d28a72bdb3c039f09b97eec58839f4121758`. Its acceptance rests on inert unit
evidence: 116 focused obligations and 481 inherited methods passed
([verification](../required-images-p29/VERIFICATION.json)).

**Where the supplements differ from P07.** P07 planned one HI implementation and then H0. Instead,
five versioned plan schemas and profiles followed. Each came after a blocker found on a disposable
host, or deduced from what one retained: the Python RPATH token (after P10), the libc PLT tags (P15),
the libc flags (inferred in P16), the RTLD paths (P23) and the required images (P26). P13 adds a
precondition, N34, that P07 does not name. None of them changes P07's stage order, its rule that
no unresolved host field may enter an executable plan (section 2), its process denominators
(section 4), the seven-method acceptance (section 6) or Gate R (section 7).

## 2. What the adopted contract requires of the executor (A2)

The plan runs on the executor that its own fields describe. These requirements come from the
adopted records and the published sources; [CONTRACT-REQUIREMENTS](CONTRACT-REQUIREMENTS.json)
gives each with its source and lines.

| ID | Requirement | Source |
| --- | --- | --- |
| E1 | Linux kernel with glibc. The inspector's static host check refuses any other system as `UNSUPPORTED` ("Unsupported platform/architecture/libc") and reads the boot identity from `/proc/sys/kernel/random/boot_id`. The pins below are x86-64 images. | P29 inspector `_platform`, `_check_host_static` (lines 1202–1221); P05 contract section 4 |
| E2 | Node `v24.22.1`, exactly the build with SHA-256 `acbe4b8d9153b841ed0697cbfc4f93e767386620edb745ab9358306c0a6f31aa`, 126,951,512 bytes, mode 0755. It comes from the retained archive `OntoKin_C271_P05_Node_Candidate_2026-11-20.tar.gz` (SHA-256 `100ae976555b388472c3e875aeda67bd7d8c9229a968a11661fb852624adaeb5`), saved in the owner's ChatGPT Library, and is copied into an absent task-specific directory. A different build or version "needs a separately reviewed versioned amendment before execution". | P05 contract section 4; `RUNTIME-CANDIDATE-LOCATION.json`; inspector `NODE` |
| E3 | The exact 24 C195 reader files: validator `2.0.0-dev.3.10`, Three.js `0.186.1` (revision 186) and the module loader, from the authenticated C195 archive. Neither the general tools lock nor an npm install may substitute. | P05 contract section 5 |
| E4 | The exact author-Python image: SHA-256 `fa67443527ed9647f760d807e2a38f26340757123e643c4639cf273ed15d5ea7`, 30,894,944 bytes, the Codex runtime's CPython 3.12.14, with raw `DT_RPATH` `$ORIGIN/../lib` | P11 accepted rule; inspector `PYTHON`; P23 readiness observation |
| E5 | libc SHA-256 `9792e3cbb541c8f44c7acf5f14f4022ea62998ecc787d326bed4d8b6547dfd92` (1,995,216 bytes) and loader SHA-256 `c8438e4fde1934e61c88311633f00949ff645d5c04cdb8671fa3d78164d2f307` (225,672 bytes), at `/usr/lib/x86_64-linux-gnu/` | P16, P17; P23 readiness observation; inspector |
| E6 | The five catalog images with their exact SHA-256 (libdl `295fa521…`, libm `6d567d53…`, libpthread `85e21f7d…`, librt `7b7b84d1…`, libutil `e3981d10…`), from glibc `2.41-12+deb13u4` | P27 adoption and design; `remaining_h0_constraint` |
| E7 | `/usr/bin/ldd`, pinned, with its literal RTLD candidate list, including the absent `/libx32` candidate and parent and the `/lib64/ld-linux-x86-64.so.2` alias to `../lib/x86_64-linux-gnu/ld-linux-x86-64.so.2` | P23 blocker; P24 design; inspector `RTLD_*` constants |
| E8 | A declared clean environment: `PATH=/usr/bin:/bin`, `C.UTF-8`, `TZ=UTC`, no `NODE_OPTIONS`, `NODE_PATH`, `LD_PRELOAD`, `LD_LIBRARY_PATH` or startup hooks; five seconds per preparation command | P05 contract section 4; inspector `ENVIRONMENT` |
| E9 | A clean candidate commit and tree containing the P29 inspector, a complete immutable source inventory, fresh external evidence paths, the two literal command arrays, and a separate independent review with an expected digest supplied outside the plan. No `TODO`, null, wildcard, guessed hash or unresolved host field. | P07 section 2 |
| E10 | N34: independent review of actual-loader and script source completeness before the operational plan is adopted or executed | P13; P25 acceptance (evidence absent, adoption withheld) |
| E11 | N57: unchanged historical obligation, external review only | P13 |
| E12 | The fixed obligations of the seven methods: 30,000 ms CPU allowance, 28,000/2,000 ms child and cleanup, 8 MiB GLB, the 5×10⁻⁶ m and 10⁻⁶ thresholds, exactly three real checkers, no skip | P05 contract section 7; P07 sections 4 and 6 |
| E13 | The original supervisor `prototypes/static_tray_v01/supervisor.py` for H1's commands and for the three CPU checkers, called once per checker through the provider. It is Linux-only: it sets `prctl(PR_SET_CHILD_SUBREAPER)` and otherwise stops with "Cannot establish Linux descendant reaping". | P05 contract sections 3 and 7; P07 section 1 (H1); supervisor lines 171–173; inspector `_load_helpers`, `_run_command` |
| E14 | The seven package metadata pins of `tools/native-reader-verification-linux-cp312.lock` | inspector `_check_metadata`; provider `_python_pins` |
| E15 | The exact launcher `-I -S -B`, whose environment equals the declared one | inspector `_check_launcher` |
| E16 | The existing preparer `tools/prepare_current_host_readback.py` and its installation receipts (`INSTALLED_EXACT` or `ALREADY_PRESENT_EXACT`, with zero Node, `ldd` and checker starts). The preparer is Linux-only: it publishes with `renameat2` and installs only when `sys.platform == "linux"`. | inspector `_check_installation`; preparer lines 215 and 274; P05 contract section 5; P07 section 2 |
| E17 | The outer capture's authority and log descriptors: an existing external evidence parent, absent per-attempt output paths and an approved failure capture | P07 section 2 |
| E18 | The admitted Git closure of the source commands | inspector `_check_git` |
| E19 | The provider's and probe's host bindings: Linux platform, glibc, the procfs boot identity, the `ldd` role, an ELF interpreter for Node, the Linux Node pin and the linux-cp312 lock | provider `_verify_host`, `_python_pins` (lines 441–520); probe lines 54 and 451–461 |

E1 to E8, E13, E16 and E19 are properties of one class of host: the disposable Linux x86-64 hosts
of the ChatGPT browser threads, whose Codex runtime supplied the Node build and the author Python.
P23 observed all three Python, libc and loader pins matching on such a host
(`h0-plan-p23/readiness/run001.stdout.json`). P26's observations ran on the same kind of host:
the Codex runtime's Python is in its command arrays.

## 3. Existing executors compared with it (A3)

[EXECUTOR-INVENTORY](EXECUTOR-INVENTORY.json) holds the observations, made at 2026-11-26T03:20:05Z,
with a supplement at 04:01:12Z.

| ID | Executor | Observed or recorded | Verdict |
| --- | --- | --- | --- |
| X1 | The owner's persistent local environment: the main checkout's and this worktree's `.venv` | Darwin 25.6.0, macOS 26.6.2 (25G83), arm64 (Apple M3 Ultra), native; CPython 3.12.13 (Homebrew), Mach-O arm64; Homebrew Node.js, Mach-O arm64 (v25.9.0 by main's doctor); no `/usr/bin/ldd`, `/lib64`, `/lib/x86_64-linux-gnu`, `/usr/lib/x86_64-linux-gnu` or `/etc/ld.so.cache` | **Does not meet** E1, E2, E4 to E7, E13, E16 and E19. For `/0.1.1` and later plans, the inspector's author-runtime check (E4) runs before its static host check (E1); either refuses this host (*source inference*). The E2 build is a Linux x86-64 executable. The original supervisor cannot run on Darwin: its `prctl` lookup through `ctypes` fails there (*source inference*). E14 compares package names and versions; main's `.venv` holds the seven pinned versions, and only the worktree's empty `.venv` fails it. |
| X2 | A container or virtual machine on this host | None installed: Docker, Podman, nerdctl, Colima, Lima, OrbStack, Multipass, Vagrant, QEMU, UTM, Parallels, VMware Fusion, VirtualBox and Apple's `container` are all absent. The OS supports hardware virtualization (`kern.hv_support` 1), and Rosetta for Linux is present. Main's `linux-container` profile is unconfigured and records that "an emulated amd64 container is never native Linux qualification". | **None exists.** An amd64 guest here would be emulated. Rosetta for Linux translates x86-64 code inside an arm64 guest, which is translation, not native execution: the main rule applies by inference. An arm64 Linux guest would run natively but fails the x86-64 pins (route E). Either needs new host tooling. |
| X3 | GitHub's hosted runners | Hosted jobs are optional, manual-only and default-false under the owner's no-payment direction (OK-ENG-006). In local mode, checks run on the owner's prepared environment or a dedicated machine that the check names. Not observed in this phase, but general knowledge: GitHub's Linux runners are Ubuntu images, while the pinned libc and loader bytes are those of Debian's glibc `2.41-12+deb13u4`, and they lack the Codex runtime's Python image. | **Does not meet** E4 to E6 (*inference*; E7 not established), and is outside the local-mode executor rule without a separate owner decision |
| X4 | A disposable ChatGPT browser-thread host, or another remote agent sandbox | The ChatGPT hosts are the class on which every pin was first observed and on which P23 observed them matching. Other remote agent sandboxes are not local, have no defined execution mode in this project, and have had no pin observed. | **Not an executor of this local session.** Using a ChatGPT host means running that phase in browser mode, on explicit owner direction, under the ephemeral-host rule. Each pin must be observed afresh there, because a match on an earlier host does not carry over. |
| X5 | Another machine of the owner | None named. This session's startup report asked whether a Linux x86-64 machine or VM should be considered, as the [session checkpoint](../../../workflow/tasks/C271/P30-SESSION.md) records; the owner's reply selected the phase and named none. | Nothing to compare |
| X6 | Other Node and Python executables on this host | Observed by the independent reviewer (F-02), not re-observed by the Director. Node builds are bundled inside three installed applications: Mach-O arm64, 119,131,584, 116,285,408 and 122,545,856 bytes. Their applications' manifests state 24.14.0 and 24.22.3 for two of them; no version was read from a binary. Several applications also embed Node through Electron (architecture not observed). The Python interpreters are uv-managed CPython 3.12.11 and 3.11.14, and the system `/usr/bin/python3`, a universal binary that main's HOST-INVENTORY gives as CPython 3.9.6. | **Does not meet** E2 or E4. No bundled build has 126,951,512 bytes or the Linux file format, and none of the interpreters is the pinned Linux image. |

Two further host facts bear on later gates:

- On main's local runs, the three readback CPU methods are **skipped**. Main's version of the test
  keeps the old `skipUnless` on the historical C199 inputs: "Retained exact Node/readback
  dependencies are unavailable" (main's `BASELINE-CHECKS.json` and `CANDIDATE-CHECKS.json`).
- On this branch, the driver resolves the readback selection before its source inventory,
  workspace copy and every step, whenever the unit stage is planned, as it is in the default
  routine. Without `--readback-config` and `--readback-config-sha256` "from the reviewed execution
  plan" it raises an error (`tools/check_local.py`, `prepare_readback_selection` and its call
  before `prepare_workspace`). The CPU class reports missing prerequisites as visible setup
  errors, never as skips. So under the adopted contract, the branch's default local routine
  cannot start on X1 (*source inference*).

## 4. P26's `remaining_h0_constraint` and the published candidate (A4)

[H0-CONSTRAINT-RECONCILIATION](H0-CONSTRAINT-RECONCILIATION.json) relates each field to the
published candidate. P26's record stays unchanged in `task.json`.

| Field | P26 value | Relation now |
| --- | --- | --- |
| `status`, `classification` | `P26-LIBDL-NONLIBC-PLT`, a source-deduced required-image policy incompatibility | Addressed by design (P27) and by implementation (P29), on inert unit evidence only. It has not been observed on a host under `/0.1.5`. |
| `selected_implementation` | The P25 inspector, 233,502 bytes, `eea3e634…` | Superseded in code by the P29 inspector, 249,393 bytes, `71e837c3…`, published at `dbf20bee`. P29's corrected baseline ran on exactly the P25 bytes (`VERIFICATION.json`, `baseline.production_sha256`), so the lineage is direct. |
| `source_commit` | `ed2fc453042a9f0bc4808c2aea7f015baf1ff73e` | Superseded. An H0 plan must bind a clean commit and tree that contain the P29 inspector, for example a descendant of `4a9585a0`. |
| `source_inventory` | A 93,409-byte file on a disposable host (`/workspace/scratch/…`) | Not available; its SHA-256 is history only. E9 requires a fresh complete inventory. |
| `necessary_counterexample` | `libdl.so.2.inert`, 14,408 bytes, `295fa521…` | Retained in the repository (`h0-plan-p26/` and P27's package images); a frozen input of P29's controls |
| `additional_observed_limits_to_preserve` | libpthread and libutil tag trios, libm `DT_FLAGS` 24, librt `DT_FLAGS_1` 9 | Covered by P27's finite rules for the five bound images, as implemented in P29; unchanged for any other image |
| `predicted_source_diagnostic` | `CHI-UNSUPPORTED` at the ordinary dynamic-tag predicate | Still the prediction for plan versions `/0.1.4` and earlier. Under `/0.1.5`, the five bound images take the private route when their pins match. No product refusal or admission has been observed. |
| `external_gate`, `whole_N34_accepted` | N34, false | Unchanged and open |
| `historical_N57_unchanged` | true | Unchanged |
| `remaining_gates` | Complete closure, N34, N57, H0 plan acceptance and execution, H1 and the parent gates | All still open. P30-EXECUTOR-001 is a further precondition in local mode. |
| `next_phase_action` | A compatibility decision for the non-libc tags and the libm and librt flags | Fulfilled by P27 (decision) and P29 (implementation); superseded by this review's outcome |

## 5. Further preparation (A5)

Every candidate item needs a concrete reason tied to an acceptance requirement. None has one in
this local session.

| Item | Disposition | Reason |
| --- | --- | --- |
| Prepare the executable `/0.1.5` inspection plan (the next action in P29's summary) | Not selected | Its host fields can be filled only on an eligible executor. On X1 they would have to be invented, which P07 section 2 forbids. |
| Retrieve the P05 Node archive or P09's Python snapshot to this host | Not selected | Both are Linux x86-64 executables that cannot run here. P09's snapshot is the bare executable, not its `../lib` closure, and is inert evidence. |
| Prepare the 24 C195 reader files on this host | Not selected | They would serve no executor that meets the contract |
| Configure `linux-container` or install a virtualization tool | Not selected | It is new host tooling. An amd64 guest here would be emulated or translated, which is never native Linux qualification. An arm64 guest needs new pins (route E). |
| Prepare main's `visual-verification` profile (Node 22, Three.js 0.180.0) | Not selected | It is a different Node build and a different Three.js version; P05 section 5 rules out the general tools lock |
| Build host tooling for macOS or for an arm64 Linux guest | Not selected in this phase | It becomes justified only if the owner selects route C or E below. It then starts with a reviewed design, not with implementation. |
| Run H0 on a disposable browser-thread host | Not selected | A change of execution mode needs explicit owner direction (route A) |

## 6. Routes that remain, and executor substitutions (A6)

This phase adopts none of these routes. Each is a separate later decision of the owner.

**A: The unchanged contract, in browser mode.** H0, and later H1, run on a disposable ChatGPT
host, the only class of host on which the pins have been observed to match.

- *Substitutes:* the execution mode for those phases, not the executor class of the contract.
- *Unchanged:* every term of the contract and of `/0.1.5`.
- *Costs and limits:* browser delivery rules apply to each phase. Every pin must be observed afresh.
  A changed Codex runtime would itself stop the plan through E4, and a changed host image through
  E5 to E7. E2's Node comes from the retained archive, not from the runtime. Evidence size is
  limited by the transfer routes that produced P29-PUBLICATION-SIZE-001.

**B: An owner-supplied native Linux x86-64 machine.**

- *Substitutes:* the host. In practice it also needs a versioned amendment of the author-Python pin
  (E4), because the Codex runtime's Python and its `../lib` closure are not retained, and an
  amendment of any RTLD path that differs from P24's literal list (E7).
- *Unchanged:* the Node build (E2, retrievable from the owner's Library), the 24 reader files, the
  original supervisor, the libc, loader and catalog pins, provided that the machine's glibc
  `2.41-12+deb13u4` bytes match them (not established), and all of E9 to E12.
- *Concrete reason it would have:* an owner-named machine that can be observed.

**C: An explicit substitution to the owner's macOS arm64 environment.** This is the local-mode
executor of OK-ENG-006. It needs a new, separately reviewed, versioned contract, as P05 section 4
requires for another build.

- *Substitutes:*
  - the Node build: `v24.22.1` kept, an identified darwin-arm64 build pinned by its own bytes.
    This follows P05's own pattern, which kept the version constant while qualifying a different
    build and host.
  - the qualification Python: CPython 3.12.13 instead of the Codex runtime's 3.12.14.
  - the host inspection: the Linux ELF closure stages of `/0.1.1` to `/0.1.5` do not apply on
    macOS and would be replaced by a new reviewed observation.
  - the process supervisor (E13), both for the three CPU checkers and for any observation that
    replaces H1. The new contract must define and justify its lifecycle guarantees against P05
    section 7. Darwin has no equivalent of Linux's child-subreaper descendant reaping, so that
    guarantee is not kept.
  - the host bindings (E19): the provider's host verification and its HOST, lock and
    configuration schemas, and the probe's bootstrap bindings (Linux platform, glibc, boot
    identity, ELF interpreter, `ldd` role, Node pin and linux-cp312 lock).
  - the existing preparer (E16), which publishes with `renameat2` and installs only on Linux. P05
    section 5's atomic no-replace installation needs a reviewed macOS equivalent.
- *Unchanged:*
  - the seven method bodies, `check_case` and the seam bodies;
  - the synthetic GLBs and the independent geometry oracle;
  - the 24 reader files, byte for byte: all JavaScript, JSON or text, with no native module;
  - the probe's scientific body, the thresholds and limits;
  - exactly three real checker starts, now through the substituted supervisor;
  - the no-skip rule and the independent numerical audit.
- *Known difficulties:*
  - macOS keeps its system libraries in the dyld shared cache, not as individual files. The Linux
    plan's file-by-file closure model therefore does not transfer, and the new design must state
    a different closure claim explicitly.
  - The lifecycle assertions of `check_case` (cleanup passed, handles closed) would be backed by
    a different mechanism. That changes what those assertions mean.
- *Concrete reason it would have:* R03 requires the seven methods to execute, with no skipped
  obligation, on the executor of the routine (P05 Gate R; P07 sections 6 and 7). In local mode
  that executor is the owner's prepared environment, where the adopted contract cannot run (X1).

**D: Retain the refusal.** H0, H1 and R03 stay unmet and C271 stays open. The published P29
candidate remains an accepted, inert implementation. Like route C, it needs neither a new machine
nor a change of mode. P24's adoption already records that "retaining current refusal remains
valid on this unqualified host".

**E: A native arm64 Linux guest on this host.** It runs under the host's hardware
virtualization, which is not emulation.

- *Unchanged:*
  - Linux and glibc, the procfs and `ldd` bindings, and the ELF closure model. The inspector's
    platform check already accepts `aarch64`.
  - the original supervisor and its child-subreaper reaping (E13), and the Linux preparer (E16);
  - the seven method bodies, `check_case` and the seam bodies;
  - the synthetic GLBs and the independent geometry oracle;
  - the 24 reader files, byte for byte;
  - the probe's scientific body, the thresholds and limits;
  - exactly three real checker starts through the original supervisor;
  - the no-skip rule and the independent numerical audit.
- *Substitutes, by versioned amendment:*
  - every architecture-bound pin: the Node build (linux-arm64), the author Python, the libc,
    loader and catalog images, the RTLD path list, the `ldd` script and the linux-cp312 lock
    (E2, E4 to E7, E14, E19);
  - P16, P17 and P27's x86-64 image rules, which do not apply to arm64 images; a new
    required-image design would be needed.
- *Needs:* a virtualization tool and a guest image (none installed), and a profile decision.
  Main's `linux-container` profile is unconfigured and requires a later profile to state its
  purpose and carry its own acceptance.
- *Concrete reason it would have:* the same as route C, while keeping more of the original test
  meaning.

**Claims that no route can support.** Routes C and E, or any other substitution, can never support:
- a Linux x86-64 qualification;
- the historical C199/C225 replay;
- a P05 Gate H for the Codex Node build;
- any statement that the ELF policies of `/0.1.1` to `/0.1.5`, all bound to the x86-64 Codex
  images, were exercised on a real host;
- N34 for the Linux x86-64 loader.

Route C cannot support the original supervisor's Linux descendant-reaping guarantees either.
Results of a substituted executor are labelled with that executor. They never replace or relabel
the unmet Linux-contract gates, which stay recorded as unmet.

**Recommendation (for the owner to decide).** If C271 is to reach R03 and R04 in local mode, the
next phase should be design only: an independently reviewed decision between route C and route E,
made before any host tooling is built. It should also decide the driver's selection rule for
main's ordinary local routine (section 7).

- Route E keeps more of the original test meaning: Linux, glibc, the original supervisor and the
  ELF closure model. It needs a virtualization tool, an arm64 guest and new arm64 pins and image
  rules.
- Route C needs no virtualization tool. It substitutes the supervisor's lifecycle mechanism and
  the host bindings, and it gives up the Linux reaping guarantee.

If further investment in C271 is not wanted, take route D. Routes A and B keep the contract in its
Linux x86-64 form, but they depend on a disposable host or on a machine that has not been named.

## 7. Consequences for the later gates

- **H0 and H1 under `/0.1.5`:** blocked in local mode by P30-EXECUTOR-001.
- **R03:** needs the seven methods, with no skip, on the executor that runs the routine.
- **R04:** integration brings this branch's driver and test into main ([MAIN-CONFLICTS](../p29-local-publication-r07/MAIN-CONFLICTS.md)
  keeps C271's readback bindings). Without a qualified selection, main's default local routine on
  the owner's executor would then refuse to start, where it now skips three methods (*source
  inference*).
  - The selection binds one exact clean commit and tree (provider `_verify_source`) and the current
    boot (`_verify_host`). So after integration, every routine run on main, including a run on
    uncommitted changes, would need a new approved selection, whichever executor is qualified.
  - Under route E, the selection would exist only inside the guest.
  - R04 therefore needs a reviewed decision on the selection rule alongside route C or E, not
    instead of them.
- **N34 and N57:** open in every route.
- **R05:** follows R03 and R04, unchanged.

## 8. Limits

- The executor inventory covers platform identity, the presence of common container and
  virtualization tools, and (through the reviewer) other Node and Python executables. No network or
  remote host was probed, and no SSH configuration was read. The owner named no other machine.
- The following are source inferences, none of them executed:
  - the inspector's refusal of this host;
  - the driver's refusal to start;
  - the original supervisor's failure on Darwin, where its `prctl` lookup through `ctypes` fails
    before the quoted `Stop`;
  - the preparer's Linux-only installation;
  - the statements about Rosetta for Linux and about an arm64 guest.
- No statement is made about the current contents of the Codex runtime.
- Main's doctor ran before the declaration, as step 5 of LOCAL-START-HERE requires. It started
  Homebrew's Node.js once with `--version` and read npm's version from npm's own manifest; npm was
  not started. That Node build is not the contract's and touched no C271 input. No Node process ran
  in this phase.
- The declaration states `declared_at_utc` 03:20Z, but its commit time, 2026-11-26T03:19:02Z, is
  the correct one. The first version of these records stated 03:40Z, but their commit time,
  03:28:47Z, is the correct one. The corrected version stated 04:10Z for its corrections, but its
  commit time, 04:04:02Z, is the correct one; the records now say 04:04Z.
