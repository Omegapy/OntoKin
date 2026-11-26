# C271-P30 independent review (A7) of the outcome candidate

Reviewer: one fresh-context subagent launched by Director `c271-p30-55a168e30426` (Claude Code, model
Claude Opus 5.5). Candidate: local commit `8aa4a80012a14a521a441b306635c4fad68ca573`, tree
`f3f8fcd703a36e82a68b87dabff3069031bd9672`, parent `7a4ab16248ed071a211ded3e24e1558ec064f0b1`.
Main: `51223c9b94a222f29d38eb6c33808f8e55e2bff9`.

## 1. Independent answer, written before reading the candidate's verdicts

Written at 2026-11-26T03:36Z, after reading the sources named in the assignment and before
opening OUTCOME.json, EXECUTOR-INVENTORY.json, CONTRACT-REQUIREMENTS.json,
H0-CONSTRAINT-RECONCILIATION.json or REVIEW-OUTCOME.md. Disclosure: before forming it I saw the
candidate's commit message (through `git show --stat`), whose summary line states the headline
outcome (no existing executor; blocker P30-EXECUTOR-001; no preparation selected). The answer
below rests on the sources and observations listed, not on that line.

**Question: does any executor available to a local session on this host meet the adopted
contract?** **No.**

Reasons, each from a source or an observation:

1. *The contract is bound to one Linux x86-64 glibc host image.* P05 `CONTRACT.md` §4 admits
   only Node `v24.22.1` with SHA-256 `acbe4b8d…31aa`, 126,951,512 bytes, mode `0o755` ("No range,
   nearest version or fallback"; "adopting another build or version needs a separately reviewed
   versioned amendment before execution"), and requires `HOST.json` with ELF interpreter,
   shared-library resolution and `/usr/bin/ldd`. The P29 inspector (249,393 bytes, SHA-256
   `71e837c3…1758`) refuses anything but Linux with glibc (`_platform`, `_check_host_static`:
   `system == "Linux"`, `machine in ("x86_64", "aarch64")`, `os.confstr("CS_GNU_LIBC_VERSION")`,
   `/proc/sys/kernel/random/boot_id`), and the `/0.1.5` profile adds x86-64-only facts: the
   `debian-glibc-2.41-12+deb13u4-amd64` required-image catalog with five pinned images, the
   pinned libc and loader, the pinned author Python ELF (30,894,944 bytes, `$ORIGIN/../lib`
   RPATH), the literal `/lib64/ld-linux-x86-64.so.2` RTLD path model and the pinned
   `/usr/bin/ldd` script (5,356 bytes, `#!/bin/bash`). The branch provider
   `current_host_readback_v01.py` `_verify_host` also requires `platform.system() == "Linux"` and
   the procfs boot id, so the branch driver's mandatory `--readback-config` selection can never
   validate on a non-Linux host.
2. *This host is macOS 26.6.2 (build 25G83), Darwin 25.6.0, arm64 (Apple M3 Ultra)*, observed
   now with `uname`, `sw_vers`, `sysctl`, `arch`. It has no glibc, no ELF loader, no `/proc`, no
   `/usr/bin/ldd`. Every platform predicate above fails before any pin is compared.
3. *Node executables present are all Mach-O arm64 and none is the pinned build or version.*
   Observed with `command -v`, `ls`, `file` and static reads of version headers or manifests
   (nothing launched): Homebrew `node` 25.9.0 (the only one on PATH);
   application A's bundled `…/bin/node` 24.14.0 darwin-arm64 (119,131,584 bytes);
   application B's bundled `…/bin/node` 24.22.3 darwin-arm64 (116,285,408 bytes);
   application C's bundled `…/node` (122,545,856 bytes, version not read); Electron-embedded Node in
   several applications. None has 126,951,512 bytes; none is `v24.22.1`.
4. *Python interpreters present are not the pinned author Python.* Homebrew CPython 3.12.13
   (the `.venv` base of both checkouts), uv-managed 3.12.11 and 3.11.14 (macos-aarch64), and
   the system 3.9.6. The pin is a Linux ELF image.
5. *No container or virtual-machine executor exists locally.* `command -v` finds none of docker,
   podman, colima, orb/orbctl, lima/limactl, nerdctl, finch, Apple `container`, qemu, utmctl,
   prlctl, vmrun, VBoxManage, multipass, vagrant, tart, vfkit, krunvm, rdctl; `/Applications`
   holds no VM or container application. Rosetta 2 (including its `RosettaLinux` component)
   and hypervisor support (`kern.hv_support: 1`) are present as operating-system facilities,
   but using them needs a VM manager, a Linux image and the pinned inputs, which is host
   tooling this phase excludes. Main's `tools/local-environment.json` keeps `linux-container`
   `unconfigured` and states that "An emulated amd64 container is never native Linux
   qualification"; its `historical-native` profile is established only by the owning contract.
6. *Remote executors are not executors of a local session.* The disposable ChatGPT/Codex hosts
   on which P05, P23 and P26 observed the pins are browser-mode hosts: AGENTS.md says a session
   on a disposable or remote host is not local, and mode changes need explicit owner direction;
   each browser thread is a different host whose pins would have to be observed again. Hosted
   GitHub Actions is excluded as an executor by OK-ENG-006 and AGENTS.md (manual opt-in only,
   no waiting on hosted CI, no paid execution), and a standard hosted runner would not carry
   the Debian `2.41-12+deb13u4` pins in any case (not observed; inference).
7. *Even the reader inputs are not present locally.* The pinned Node archive is recorded in the
   ChatGPT Library (P05 `RUNTIME-CANDIDATE-LOCATION.json`); no local copy was found among the
   handoff copies beside the clone, and no `tools/node_modules` exists in either checkout. (The
   main `visual-verification` profile is not an equivalent: Node 22 with Three.js 0.180.0,
   not the C195 Three.js 0.186.1.)

Consequences I expect a correct candidate to state:

- R03 cannot be reached on this host under the adopted contract; on main's original test the
  three CPU methods skip here (`skipUnless` on absent `/opt/codex/…` and `/workspace/…` paths),
  and the driver counts a skip as an incomplete regression; on the branch the driver refuses to
  run at all without a selection, and no selection can validate on macOS.
- No preparation (executable `/0.1.5` inspection plan, host tooling, input reconstruction,
  environment profile) has a concrete reason on this host, because each presupposes a Linux
  x86-64 host carrying the pins.
- The routes that remain are owner decisions: a conforming Linux x86-64 host under an explicit
  mode decision (for example a browser-mode thread, with fresh observation), a separately
  versioned contract amendment admitting a different executor (for example a darwin-arm64 Node
  build) with a new host-inspection design, a Linux VM or container profile (needs installation,
  a profile decision, and never yields native-Linux qualification if emulated), or retaining the
  blocker. None can be adopted by P30, and none may relabel H0, H1, Gate H or R03.
- Integration consequence: if R04 carries the branch driver's mandatory selection into main, the
  whole routine driver (not only the unit stage) would refuse to start on the owner's Mac.

## 2. Checks run

Everything below was read-only. On the C271 worktree (candidate `8aa4a800`, declaration
`7a4ab162`, inputs revision `4ee55b03`) and on main `51223c9b` I used only Git object reads
(`git show`, `ls-tree`, `rev-parse`, `diff --name-only`, `log`, `grep`). No ref, index or working
file changed: at the end the worktree was still clean at `8aa4a800`, and the main checkout still
held only the owner's three items. Host identification used `uname -a`, `sw_vers`, `sysctl`,
`arch`, `command -v` for 33 tool names, `ls` and `file` on executables and loader paths,
`find -maxdepth 6 -name node` inside application bundles, and plain reads of Node version headers
and manifests inside two bundles. For analysis I used `python3 -I` only to parse JSON from
`git show` pipes and hash blob bytes (no project module was imported), plus `shasum`, `wc`, `grep`,
`sed`, `awk` and `date -u`. I did not run node, npm, ldd, any loader, any container or VM tool, any
test suite, `tools/check_local.py`, the doctor or any other project tool.

- **C1 (A1).** I recomputed the size and SHA-256 of all 61 READ-SET entries from Git blobs: 20 main
  entries at `51223c9b` and 41 branch entries at `4ee55b03`. Result: 61 matched, 0 mismatched,
  0 unreadable. The published READ-SET equals the working copy `read/READ-SET.raw.json` row for
  row. Four branch entries differ at the candidate (`task.json`, the branch `CURRENT.json`,
  `REQUIREMENTS.md` and `PLAN.md`). The declaration changed them, and READ-SET states `4ee55b03`
  as its revision.
- **C2 (A2).** I checked E1 to E12 against their cited sources at `7a4ab162`. The inspector is
  249,393 bytes with SHA-256 `71e837c3…` at both `7a4ab162` and `8aa4a800`.
  - Correct line anchors: E2 (147–150), E4 (138–143), E5 (135–138), E7 (111–131; `RTLD_SCRIPT`
    ends on 132) and E8 (145–146).
  - E1 (1202–1219) is approximate: the refusal text is on line 1220, and the comparison with the
    live platform is on line 1221.
  - The contract sections, the cited adoption fields, `RUNTIME-CANDIDATE-LOCATION.json`,
    `EXTERNAL-INPUTS.json`, P23 `run001.stdout.json` and REQUIREMENTS.md "P25 accepted technical
    boundary" (line 424) each support their row.
- **C3 (A3).** I observed the host facts again and compared X1 to X5 with them and with the
  sources. I checked the five claims named in the assignment (section 3).
- **C4 (A4).** I compared each reconciliation field with `remaining_h0_constraint`:
  - The field is unchanged: its canonical-JSON SHA-256 `d4985696…` is identical at `4ee55b03`,
    `7a4ab162` and `8aa4a800`.
  - P29 `VERIFICATION.json`: the baseline production is `eea3e634…`.
  - The inspector applies `RI-ARCH` on line 2111 and admits libm `DT_FLAGS` 24 and librt
    `DT_FLAGS_1` 9 only for those images (lines 2144–2145).
  - The counterexample blob `h0-plan-p26/libdl.so.2.inert` is 14,408 bytes, `295fa521…`. P29's
    control contexts reference it.
  - The inspector at `dbf20bee` and at `4a9585a0` is `71e837c3…`.
- **C5 (A5, A6).** I checked each disposition and route against these sources:
  - P05 sections 3 to 5 and 7, and P07 sections 1, 2 and 6;
  - `tools/local-environment.json`, OK-ENG-006, P09 `EVIDENCE-LOCATION.json` and P24
    `ADOPTION.json`;
  - the Linux dependencies of the code that the contract requires to stay unchanged: the
    original supervisor, the branch provider and its probe.
- **C6 (consistency).** I compared OUTCOME.json, REVIEW-OUTCOME.md and the JSON records:
  - the execution claims against CHECKS-BASELINE.json and the working evidence under `checks/`;
  - the raw inventory `inventory/EXECUTORS.txt`, whose SHA-256 `74ee47e5…` equals the recorded
    one;
  - the record times against the commit times;
  - the doctor disclosure against main's `tools/doctor_local.py`;
  - the R06 copies in `handoffs/` beside the clone, which I hashed again (both equal the recorded
    identities).

## 3. Results by acceptance claim

**A1: holds.** All identities match. See F-09 for the read set's unmet promise to list inputs
added later, and for the directories it binds only in part.

**A2: holds in substance.** Every row is supported, and no omitted requirement changes a verdict,
because E1 already fails on every local executor. Some executor and input requirements for H0
and H1 are missing (F-10). One requirement matters for the substitution routes: the original
supervisor, which is Linux-only (F-01).

**A3: the verdicts hold.** My independent answer in section 1 matches the candidate's outcome:
no existing executor available to a local session meets the adopted contract. The five named
claims:

1. *P23 observed all three Python/libc/loader pins matching.* **Supported.**
   `h0-plan-p23/readiness/run001.stdout.json` has `state` `NECESSARY_IMAGE_PINS_MATCH` and
   `matched: true` for python (`/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3.12`),
   libc and loader, with the same values as the P29 pins. That file says these are "Necessary
   image-pin predicates only; not H0 plan validation", and the candidate does not claim more.
2. *The 24 C195 reader files are all JavaScript, JSON or text, with no native module.*
   **Supported.** `EXTERNAL-INPUTS.json` lists 26 files: 24 under the C195 `receiving` root
   (14 Three.js, the loader `tools/three_loader.mjs` and 9 validator files: `.js`, `.mjs`,
   `.json`, `.md`, LICENSE and NOTICES) and the two OntoKin source files. None is a `.node` addon,
   and every slot's argv carries `--no-addons`.
3. *Main's test skips through `skipUnless`, and the three CPU methods were skipped in main's local
   runs.* **Supported.** Main's test has `@unittest.skipUnless(NODE.is_file() and DEPS.is_dir() and
   HOST.is_file(), …)` on `ReadbackCPUControls`. Those paths are absent here. BASELINE-CHECKS
   records `skipped: 3` with that reason in both runs, at base `6b346b1e`, where the test file is
   unchanged. CANDIDATE-CHECKS lists the three method IDs as skipped in both runs.
4. *The branch driver refuses the unit stage without `--readback-config`.* **Supported, and
   understated.** `prepare_readback_selection` raises the quoted message (lines 427–428). It runs
   before the workspace copy and before every step, so no stage runs at all (F-04).
5. *After R04, main's local unit stage would refuse to start without a qualified selection.*
   **Supported as source inference, and understated.** MAIN-CONFLICTS.md ("What must survive")
   keeps C271's readback-configuration bindings in the driver. On macOS no selection can validate:
   `validate_selection` calls `_verify_host`, which requires Linux. The whole driver run would
   refuse, not only its unit stage (F-04).

Executor classes the candidate did not inventory are in F-02. Precision issues are in F-05 and
F-06.

**A4: holds.** Every field is supported, and P26's record is unchanged.

**A5: the dispositions hold.** Each reason is supported. The VM reason covers only an emulated
amd64 guest (F-03).

**A6: route C's statement is incomplete (F-01, mandatory).** Routes A, B and D are explicit; route
A has one misattribution (F-11).

- No route relabels an unmet gate.
- The claims that no route can support are stated.
- Nothing is adopted, and the recommendation is left to the owner.
- The recommendation's basis is partly overstated (F-04).

**Consistency.**

- No record claims execution beyond read-only inspection and the record checks.
- *Source inference* is labelled throughout.
- OUTCOME.json, REVIEW-OUTCOME.md and the JSON records agree, apart from F-05(c).
- The doctor disclosure is accurate for Node but not for npm, and the machine-readable execution
  record is incomplete (F-07).
- Three record times fall after the commit (F-08).

## 4. Findings

### F-01: mandatory. Route C leaves out the Linux-only original supervisor and the Linux bindings of the provider and probe

**Location:** REVIEW-OUTCOME.md section 6, route C (lines 164–187), and the recommendation (lines
203–208); OUTCOME.json `routes_for_owner[id=C].substitutes` and `recommendation`.

**What the contract requires:**

- P05 CONTRACT.md section 3 (line 44): the provider checks its bindings "before calling the
  original `supervisor.run_process` exactly once".
- Section 7, Lifecycle row (line 115): "Original supervisor, process groups, reaping, closed
  handles, cleanup and uncertain-outcome handling".
- Line 117: "Preserve the original Python `run_process` … The three CPU checkers provide real Node
  start/exit/cleanup receipts."
- P07 section 1, H1 row (line 13): H1 runs its commands "using the new module and bounded original
  supervisor". The inspector does so: `_load_helpers` imports it (line 2691) and `_run_command`
  calls it (line 3496).

**Why the original supervisor cannot run on this host:**

- `prototypes/static_tray_v01/supervisor.py` is 11,286 bytes, SHA-256 `c47b84ab…`, identical on
  main.
- Its first line reads "Bounded Linux process groups…".
- Lines 171–173 call `prctl(36, 1, 0, 0, 0)` (PR_SET_CHILD_SUBREAPER). If that fails, they raise
  `Stop` "Cannot establish Linux descendant reaping".
- macOS has no `prctl`. On X1 no CPU checker could start through the original supervisor. This is
  source inference; I did not run it.

**The branch provider and probe are Linux-bound too:**

- The provider `current_host_readback_v01.py` is 65,533 bytes, `2a814462…`.
  - `guarded_run_process` (line 825) delegates to `supervisor.run_process` (line 869).
  - `_verify_host` (line 458) requires `platform.system() == "Linux"` and the procfs boot id
    (lines 475–478), the `/usr/bin/ldd` role (488), an ELF interpreter for Node (511), and the
    linux-cp312 lock (`_python_pins`, lines 441–443).
- The probe `current_host_readback_v01.mjs` is 55,792 bytes, `218d22e8…`.
  - It requires `host.platform.system === 'Linux'`, glibc and the procfs boot id (lines 451–457).
  - It pins `NODE_SHA` to the Linux build (line 54).
  - It reads the linux-cp312 lock (line 461).

**What the candidate says.** Route C's *Substitutes* names only three items: the Node build, the
qualification Python and the host inspection. Its *Unchanged* list includes "exactly three real
checkers". None of the nine P30 records mentions the supervisor (I searched all of them).

**Why it matters.** A6 requires each substitution to state which contract terms change and how
the original test meaning is kept.

- Under route C, the mechanism that produces the real checkers' start, exit and cleanup receipts
  must itself be replaced. `check_case` asserts those receipts:
  `process["cleanup"]["passed"]` and `process["handles_closed"]`.
- The current source has no Darwin equivalent of Linux descendant reaping.
- This changes a fixed obligation of the contract (P05 section 7). It also changes what the three
  CPU methods' lifecycle assertions mean.
- It affects the scope and feasibility of the route the candidate recommends.

**Correction:**

1. In REVIEW-OUTCOME section 6 and OUTCOME.json route C, add two items to *Substitutes*:
   - the process supervisor for the CPU checkers, and for any observation that replaces H1, with
     the lifecycle guarantees that the new contract must define and justify against P05
     section 7. State that the Linux PR_SET_CHILD_SUBREAPER descendant-reaping guarantee is not
     kept.
   - the provider's host verification and its HOST, lock and configuration schemas, and the
     probe's bootstrap bindings: Linux platform, glibc, boot id, ELF interpreter, ldd role, Node
     pin and linux-cp312 lock.
2. Reword the *Unchanged* item as "exactly three real checker starts, through the substituted
   supervisor".
3. Add the original supervisor's Linux lifecycle guarantees to the claims that route C can never
   support.
4. Restate the recommendation's basis in this light. It remains the owner's decision.
5. Optionally, add the supervisor as an executor requirement in A2. For the Linux route, E1
   implies it.

### F-02: nonmandatory. Executor classes not inventoried (A3)

**Location:** EXECUTOR-INVENTORY.json `host` and `executors`; REVIEW-OUTCOME section 3.

**Evidence** (observed read-only; nothing launched):

- Node executables bundled in applications, all Mach-O arm64:

  | Executable | Bytes | Version |
  | --- | --- | --- |
  | application A, bundled `…/bin/node` | 119,131,584 | 24.14.0 darwin-arm64 (manifest) |
  | application B, bundled `…/bin/node` | 116,285,408 | `24.22.3-cua.1`, binary 24.22.3 (manifest) |
  | application C, bundled `…/node` | 122,545,856 | not read |

  Several other applications embed Node through Electron.
- Other Python interpreters: uv-managed CPython 3.12.11 and 3.11.14 (macos-aarch64), and
  `/usr/bin/python3`. Main's HOST-INVENTORY.md gives the latter as CPython 3.9.6, and the raw
  inventory shows its universal-binary header, but no verdict covers it. I did not run it.
- Remote agent sandboxes that installed applications can start, for example cloud agent
  sessions. I did not observe these. They are hosts of X4's kind: disposable or
  remote, so not local, and their pins are unobserved.
- Operating-system facilities: `kern.hv_support: 1`, and
  `/Library/Apple/usr/libexec/oah/RosettaLinux` is present. No VM manager is installed.

**Effect:** no verdict changes. None of these Node executables is `v24.22.1` or 126,951,512 bytes,
none of the interpreters is the pinned Python, and a remote sandbox is not a local executor.

**Correction:** add these classes to the inventory with their verdicts. Note that the application B
build (24.22.3) is not `v24.22.1`, so it is not a route C candidate as route C is worded.

### F-03: nonmandatory. The VM disposition and X2 consider only an emulated amd64 guest

**Location:** OUTCOME.json `preparation_dispositions[3]`; REVIEW-OUTCOME section 3 (X2), section
5 (row 4) and section 6.

**Evidence.** The stated reason is "an amd64 guest … would be emulated". An arm64 glibc Linux
guest on this host would run under native virtualization, not emulation.

- What it would keep: Linux, glibc and procfs, and with them the original supervisor's subreaper
  (relevant to F-01). This is source inference; nothing was tried. The inspector's generic host check also admits `aarch64` (line 1218).
- What it would fail: every x86-64 pin and profile (E4 to E7; `RI-ARCH` on line 2111; `PLT-ARCH`).
- What it would need: installed VM tooling, a Linux image and the owner's profile decision. The
  `linux-container` profile is unconfigured.

**Correction:** state this variant as a further route, or record why it is excluded. As a route it
is a substitution with versioned amendments of the x86-64 pins, and it never yields x86-64
qualification. Not selecting VM tooling in this phase stays correct.

### F-04: nonmandatory. The R04 consequence is understated and the recommendation's basis overstated

**Location:** REVIEW-OUTCOME section 3 (lines 101–105), section 6 route C (lines 185–187) and the
recommendation (lines 205–206); OUTCOME.json `recommendation`.

**Evidence: why the whole run refuses.** In the branch `tools/check_local.py`:

- `build_plan` always includes `unit-tests` (line 312).
- `run()` calls `prepare_readback_selection` (lines 576–583) before the source inventory, the
  workspace copy and every step.
- Without a selection it raises (lines 427–428), and no stage runs.
- With a selection, `validate_selection` calls `_verify_host`, which refuses any host that is not
  Linux.
- MAIN-CONFLICTS.md requires these bindings to survive R04.

So after R04 the entire local routine on the owner's Mac would refuse to start, all seven stages
and not only the unit stage.

**Evidence: why "the integration gate needs it in any case" is too strong.** In local mode, R04
needs one of two things: a selection that can validate on the local executor (route C), or another
separately reviewed amendment of the selection rule. An R04 carried out outside local mode would
leave main's local routine refusing. Route D, too, needs neither a new machine nor a change of
mode.

**Correction:**

- say "the whole local driver run";
- say "route C, or another reviewed amendment of the selection rule for the local executor";
- say "the only route toward R03 that needs neither…".

### F-05: nonmandatory. Some executor facts are unobserved, unsupported or imprecise

**Location:** EXECUTOR-INVENTORY.json X1, X3 and X5; REVIEW-OUTCOME section 3.

**Evidence:**

- **(a) X3.** Its technical reasons (Ubuntu images, no Codex Python) were not observed in this
  phase: there was no network, as the inventory's `limits` field states. Its unmet set E4 to E6
  would also include E7 if the ldd script bytes differ. Label these as unobserved inference.
- **(b) X5.** The statement that the startup report asked about a Linux machine or VM is in no
  record I could read. PHASE.json records only the selection question and the reply, and
  P30-SESSION.md does not mention it. Record its wording or drop it.
- **(c) X1.**
  - E8 is listed as unmet without a reason. E8's environment can be declared on macOS
    (`/usr/share/locale/C.UTF-8` exists).
  - REVIEW-OUTCOME says X1 "does not meet E1 to E8", but the JSON leaves out E3.
- **(d) "The inspector would refuse it at its first host check."** For plans of `/0.1.1` and later,
  `_validate` runs `_check_author_runtime` (line 3011) before `_check_host_static` (line 3013).
  `_check_author_runtime` covers the launcher, the author-Python binding and the RTLD proof (line
  2773). The first refusal on X1 would come there (source inference).

None changes a verdict.

### F-06: nonmandatory. An absent path that the raw evidence does not show

**Location:** EXECUTOR-INVENTORY.json `host.absent_paths`; REVIEW-OUTCOME section 3, X1.

**Evidence.** The records list `/usr/lib/x86_64-linux-gnu`. The raw output they bind
(`EXECUTORS.txt`, `74ee47e5…`) shows `ls: /lib/x86_64-linux-gnu: No such file or directory`, and no
observation of `/usr/lib/x86_64-linux-gnu`. Both paths are in fact absent: I observed them again
with `ls`.

**Correction:** cite what the raw output shows, or add the missing observation.

### F-07: nonmandatory. Accuracy and completeness of the execution disclosure

**Location:** REVIEW-OUTCOME section 8 (lines 226–228); OUTCOME.json `executed_in_phase`;
EXECUTOR-INVENTORY.json `host.node`.

**Evidence.** Main's `tools/doctor_local.py` is 72,988 bytes, `acf4947b…`, identical in the
checkout.

- **Node: accurate.** `collect` always calls `visual_section` (line 1038). That function runs
  `[node, "--version"]` (line 741) whenever `which("node")` finds one, so the startup doctor did
  start Homebrew Node 25.9.0 once.
- **npm: inaccurate.** npm is not started. `npm_version` (lines 664–676) reads npm's own
  `package.json`, because "running npm would write a log". The disclosure "It started Homebrew's
  Node.js and npm" therefore over-discloses for npm.
- **Machine-readable record: incomplete.** OUTCOME.json `executed_in_phase` lists only inspection
  commands. It omits:
  - the workflow check and documentation verifier, run at baseline, declaration and candidate
    (CHECKS-BASELINE.json and `checks/`);
  - the pre-declaration doctor run with its Node start.

**Correction:** write "It started Homebrew's Node.js once with `--version`; npm's version was read
from its manifest". Add the record checks and the pre-declaration doctor to `executed_in_phase`,
marked as outside the phase boundary, with a Node start count of 1.

### F-08: nonmandatory. Record times after the commit

**Location:** `recorded_at_utc` of CONTRACT-REQUIREMENTS.json, H0-CONSTRAINT-RECONCILIATION.json
and OUTCOME.json.

**Evidence.** Each states 2026-11-26T03:40Z. Commit `8aa4a800` was authored and committed at
2026-11-26T03:28:47Z (`git log`), so these records cannot have been written at that time.

**Correction:** use the actual time, no later than 03:28Z, as the candidate itself did for the
declaration's 03:20Z.

### F-09: nonmandatory. The read set's promise and its directory inputs

**Location:** READ-SET.json `state_at_declaration`; the outcome records.

**The promise.** READ-SET says "the outcome records state which other entries were opened during
the phase. Any input added later is listed in the outcome records." The outcome records do
neither.

**Inputs the outcome cites without identity** (my recomputation at `4ee55b03` for the branch and
`51223c9b` for main):

| Input | Bytes | SHA-256 (prefix) |
| --- | ---: | --- |
| `h0-plan-p23/readiness/run001.stdout.json` | 3,004 | `20c75289…` |
| branch `tools/check_local.py` | 41,254 | `76705ca4…` |
| `static-tray-qualification-c199/EXTERNAL-INPUTS.json` | 19,901 | `21fd6bad…` |
| `current-host-p05/RUNTIME-CANDIDATE-LOCATION.json` | 1,256 | `dc14eb95…` |
| `host-preparation-p09/EVIDENCE-LOCATION.json` | 1,670 | `e7f8138a…` |
| `h0-plan-p26/libdl.so.2.inert` | 14,408 | `295fa521…` |
| main `tests/test_static_tray_readback_v01.py` | 9,812 | `2f0abd81…` |
| main `tools/doctor_local.py` | 72,988 | `acf4947b…` |

**The directories.** PHASE.json and R07's Continuation name the directories `h0-plan-p21/`,
`h0-plan-p23/` and `h0-plan-p26/`, of 59, 187 and 22 files. READ-SET binds 2, 1 and 3 of their
files. Their tree IDs at `4ee55b03` are `0168a5f2…`, `f967e9a8…` and `2088886f…`.

**"Byte-identical" is not quite true.** REVIEW-OUTCOME's header says that at `7a4ab162` "every
input is byte-identical to `4ee55b03`", and each record's `inputs_identical_to` says the same.
Four READ-SET inputs were changed by the declaration itself: `task.json`, the branch
`CURRENT.json`, `REQUIREMENTS.md` and `PLAN.md`. The parts the outcome relies on are unchanged:

- `remaining_h0_constraint` (canonical hash `d4985696…` at both revisions);
- the requirement and plan states;
- the task status.

The commit identity keeps all of this recoverable, so the finding is nonmandatory.

**Correction:**

- list the added inputs with their identities;
- state which entries were opened;
- either bind the three directory trees or state the selection;
- write "every input except the four workflow records that the declaration updated".

### F-10: nonmandatory. A2 completeness and anchors

**Location:** CONTRACT-REQUIREMENTS.json; REVIEW-OUTCOME section 2.

**Evidence.** These requirements on the executor and its inputs for H0 and H1 are not in E1 to
E12:

- the exact seven package metadata pins from `tools/native-reader-verification-linux-cp312.lock`
  (`_check_metadata`);
- the exact launcher: `-I -S -B`, with `dict(os.environ) == ENVIRONMENT` (`_check_launcher`);
- the existing preparer's installation receipts (`_check_installation`: `INSTALLED_EXACT` or
  `ALREADY_PRESENT_EXACT`, with zero Node, ldd and checker counts);
- the outer capture's authority and log descriptors;
- the admitted Git closure for the five source commands (`_check_git`);
- H1's use of the original supervisor (F-01).

E1's line range should be 1202–1221.

**Effect:** none changes a verdict here, because E1 fails first.

### F-11: nonmandatory. Route A attributes a dependency to the wrong requirement

**Location:** REVIEW-OUTCOME section 6, route A (line 151).

**Evidence.** The text says "a changed Codex runtime would itself stop the plan (E2, E4)". E2's
Node comes from the retained Library archive, copied into a task-specific directory (P05 section
4, and E2's own text), not from the Codex runtime. A changed Codex runtime affects E4. A changed
host image affects E5 to E7.

**Correction:** "(E4; and E5 to E7 if the host image changes)".

## 5. Verdict

**REJECT_WITH_MANDATORY_FINDINGS.** There is one mandatory finding, F-01.

Its correction is limited to the A6 statement of route C and the recommendation's basis. It does
not change the outcome itself, which I reached independently:

- no existing executor available to this local session meets the adopted contract;
- the blocker is P30-EXECUTOR-001;
- no preparation is selected;
- the routes are left to the owner, and no gate is relabelled.

Once F-01 is resolved and re-reviewed, the candidate would be acceptable. The ten nonmandatory
findings can be corrected or recorded as dispositions.
