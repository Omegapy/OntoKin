# C271-P30 independent re-review (A7, round 2) of the corrected outcome candidate

**Reviewer:** the same fresh-context subagent that wrote REVIEW.md. It was launched by Director
`c271-p30-55a168e30426` (Claude Code, model Claude Opus 5.5).

**What was reviewed:**

| Role | Commit | Content |
| --- | --- | --- |
| Corrected candidate | `96847fae5c3f0a6d9e9d6da3095b056a8b929b62` (tree `c8de51cc498889b7dd2405a08d11dd1e1229b143`) | the corrections |
| Parent | `b17963d4` | records review 001 |
| Grandparent | `8aa4a800` | the candidate that review 001 rejected |

Main is `51223c9b94a222f29d38eb6c33808f8e55e2bff9`. Re-reviewed at 2026-11-26T04:14Z.

## 1. Scope and method

I read the complete change `git diff 8aa4a800 96847fae`: 11 files, all records. No source file
changed; the inspector is still `71e837c3…` at `96847fae`. The parts reviewed:

- `REVIEW-DISPOSITION.json` against each round-1 finding;
- each corrected record against its sources: REVIEW-OUTCOME.md, CONTRACT-REQUIREMENTS.json,
  EXECUTOR-INVENTORY.json, H0-CONSTRAINT-RECONCILIATION.json, OUTCOME.json, READ-SET-ADDITIONS.json
  and the two added lines in P30-SESSION.md;
- the new statements: E13 to E19, the revised X1 to X5, X6, route E, the restated route C, the
  claims list, the recommendation and the R04 consequence;
- the redaction of the repository copies of review 001.

The same rules as round 1 applied. Both checkouts and every Git ref were only read: the worktree is
still clean at `96847fae`, and the main checkout still holds only the owner's three items. I used:

- Git object reads;
- `ls`, `stat`, `grep`, `sed`, `awk`, `diff`, `shasum` and `wc`;
- `python3 -I` only to parse JSON and hash Git blob bytes.

For the virtualization facts I relied on the recorded supplement and did not run `sysctl` again.

I did not run Node, ldd, any loader, VM or container tool, test, driver or project tool. The
working directory beside the clone now also holds drafts and a finalization script. They are
outside the candidate, and I did not review them.

Checks:

- **Read set.** I recomputed the 61 READ-SET.json entries again from Git blobs: 61 matched. The
  file is byte-identical to round 1. I recomputed the 15 identities in READ-SET-ADDITIONS.json
  (12 files and 3 directory trees, including their file counts): 15 matched, 0 mismatched. None of
  the added inputs changed at the candidate.
- **Declaration records.** PHASE.json, READ-SET.json, CHECKS-BASELINE.json and
  R06-DOWNLOADS-COPIES.json are byte-identical at `8aa4a800` and `96847fae`.
- **Supplement.** `inventory/EXECUTORS-SUPPLEMENT.txt` has SHA-256 `b9c92d64…`, as recorded. It
  supports the three facts the record cites. I also listed `RosettaLinux` (`rosetta`, `rosettad`).
- **Record checks.** Evidence exists for each claimed run: `checks/interim/` and
  `checks/corrected/` both have a workflow check that passed and a documentation verifier with
  0 failures. The latter finished at 04:03:48Z.
- **Commit times.** `b17963d4` is 03:59:13Z and `96847fae` is 04:04:02Z.
- **Code anchors at `96847fae`.**
  - `supervisor.py`: lines 165–173.
  - Provider: lines 326–367 (`_verify_source`), 441–520 (`_python_pins`, `_verify_host`), 825
    and 869 (`guarded_run_process`).
  - Probe: lines 54 and 451–461.
  - Inspector: lines 1218, 1611–1615, 2685, 2710, 2750, 2813, 2862, 3011, 3013 and 3456.
  - `tools/prepare_current_host_readback.py` (19,788 bytes, `fd4da23d…`): lines 6, 213–221 and
    274.
- **Packages.** The Linux and macOS locks pin the same seven versions. Main's `.venv` holds those
  seven `.dist-info` directories. The worktree's `.venv` holds none.

## 2. F-01 (mandatory): resolved

Route C now states what review 001 found missing.

- **Substitutes:**
  - the process supervisor (E13), for the CPU checkers and for any replacement of H1. Its
    lifecycle guarantees must be defined and justified against P05 section 7, and Linux
    child-subreaper reaping is stated as not kept.
  - the provider's host verification, with its HOST, lock and configuration schemas, and the
    probe's bootstrap bindings (E19).
- **Unchanged:** reads "exactly three real checker starts, now through the substituted
  supervisor".
- **Known difficulties:** the changed meaning of `check_case`'s lifecycle assertions.
- **Claims list:** route C "cannot support the original supervisor's Linux descendant-reaping
  guarantees".
- **Recommendation:** restated as a design-only, independently reviewed decision between routes C
  and E. Another reviewed amendment of the selection rule is named as a candidate, and the choice
  stays with the owner.

OUTCOME.json `routes_for_owner[C]` and `never_supported_by_a_substitution` agree. A2 gains E13 and
E19, and their sources check out. One Linux-only tool is still missing from route C, the existing
preparer. It does not change the test meaning, so it is nonmandatory (F-12(a)).

## 3. Round-1 nonmandatory findings: resolution status

| Finding | Disposition says | Verified |
| --- | --- | --- |
| F-02 | X6 added; X4 widened; applications named generically | Resolved. Precision issues remain in the new text (F-13, F-14). |
| F-03 | Route E added; X2 and the disposition restated; Rosetta for Linux addressed | Resolved. Route E is not fully explicit (F-15). |
| F-04 | Whole routine refuses; R04 needs C, E or an amendment; D needs neither | Resolved as worded; the driver's call order is confirmed. Refinement in F-16. |
| F-05 | (a) X3 not observed, E7 not established; (b) X5 recorded; (c) E3 and E8 removed, Markdown and JSON agree; (d) refusal order | Resolved. (b) records the substance in P30-SESSION.md. E14, newly added to X1, is only partly supported (F-12(b)). |
| F-06 | Absent paths cite the raw output; supplement | Resolved |
| F-07 | Doctor disclosure exact; `executed_in_phase` complete | Resolved. "Started … once with `--version`; npm's version from its manifest" matches `doctor_local.py` lines 664–676 and 741. |
| F-08 | 03:28Z; corrections dated separately | Resolved for 03:40Z. The new correction dates repeat the error (F-17). |
| F-09 | Additions bound; byte-identity restated | Resolved; 15 of 15 identities recomputed |
| F-10 | E13 to E19 added; E1 is 1202–1221 | Resolved. E19's range is slightly short (F-18(a)). |
| F-11 | Route A attributes the change to E4 and to E5–E7 | Resolved |

## 4. Redaction check

I diffed my originals against the repository copies.

- **Unchanged originals.** `review/REVIEW.md` (31,098 bytes, `1a288a65…`) and `review/REVIEW.json`
  (8,798 bytes, `5c7236e2…`) still match their hashes in INDEPENDENT-REVIEW-001-PROVENANCE.json.
- **Copies.** INDEPENDENT-REVIEW-001.md (31,037 bytes, `ce12b190…`) and `.json` (8,821 bytes,
  `cb58af12…`) match their recorded identities, and they are identical at `b17963d4` and
  `96847fae`.
- **What differs.** The copies differ from the originals only where an application or cloud
  service is named:
  - In the Markdown, 8 replacements in 4 places (lines 43–45, 292–294, 300–301 and 309). The
    application names, and the bundle-internal path components that go with them, become
    "application A/B/C", and two named cloud services become "cloud agent sessions".
  - In the JSON, one summary string.
- **What does not differ.** Sizes, versions, findings, severities, line references, the read-set
  result and the verdict are unchanged.

The redaction changed nothing else.

## 5. New findings (round 2)

All seven are nonmandatory. None changes the outcome: no existing executor meets the contract,
the blocker is P30-EXECUTOR-001, no preparation is selected, the routes are left to the owner,
and no gate is relabelled.

### F-12: nonmandatory. Route C and X1: the Linux-only preparer, and E14

**Location:** REVIEW-OUTCOME.md section 2 (the host-class paragraph), section 3 (X1) and section 6
(route C); EXECUTOR-INVENTORY.json `X1.unmet`; OUTCOME.json `routes_for_owner[C]`;
CONTRACT-REQUIREMENTS.json `host_class`.

**Evidence:**

- **(a) The preparer.** The existing preparer, `tools/prepare_current_host_readback.py` (19,788
  bytes, `fd4da23d…`), stands behind E16 and P05 section 5's "atomic no-replace publication". It
  is Linux-only for installation:
  - its docstring says "Linux atomic no-replace publication" (line 6);
  - `rename_without_replacement` calls `renameat2` through ctypes (lines 213–221);
  - applying an installation requires `sys.platform == "linux"`: "Atomic installation is
    supported only on Linux" (line 274).

  Route C would install a darwin-arm64 Node build and the reader tree, but its *Substitutes* do
  not name the preparer or its publication primitive. Route E keeps them. X1 does not list E16.
  This is source inference; nothing was run.
- **(b) E14.** X1 lists E14 as unmet, and the host-class paragraph counts E14 among the
  properties of the Linux hosts. E14 is the seven package metadata pins. `_check_metadata` (line
  2813) and `_python_pins` compare names and versions only; hash lines are skipped. Main's `.venv`
  holds exactly the Linux lock's versions:

  | Package | Version |
  | --- | --- |
  | attrs | 26.1.0 |
  | jsonschema | 4.26.0 |
  | jsonschema-specifications | 2025.9.1 |
  | referencing | 0.37.0 |
  | rpds-py | 2026.5.1 |
  | typing_extensions | 4.16.0 |
  | Pillow | 13.0.0 |

  I observed its `.dist-info` directories, and main's BASELINE-CHECKS.json records the same
  versions. Only this worktree's `.venv`, which holds no package, fails E14.

**Correction:**

- add the preparer's publication primitive to route C's substitutions: either keep P05 section 5's
  absent-or-complete-exact and no-replace guarantees with a macOS mechanism, or amend them;
- record E16 as unmet on Darwin for installation;
- restate X1's E14 entry as unmet for the worktree's empty `.venv` only;
- drop E14 from the host-class list.

### F-13: nonmandatory. X4's widened class

**Location:** REVIEW-OUTCOME.md section 3 (X4); EXECUTOR-INVENTORY.json X4.

**Evidence.** X4 now also covers "another remote agent sandbox", but two of its statements still
fit only the ChatGPT hosts:

- It calls X4 "the class of host on which every pin was first observed". The pins were observed
  only on the ChatGPT/Codex hosts (P05, P23, P26).
- It says that using one "means running that phase in browser mode". Main's AGENTS.md defines
  browser mode as ChatGPT browser threads. Another remote sandbox is not local, but no mode is
  defined for it, so using one would need explicit owner direction on the mode itself.

**Correction:** split X4, or qualify both statements for the other sandboxes.

### F-14: nonmandatory. X6: attribution and precision

**Location:** REVIEW-OUTCOME.md section 3 (X6); EXECUTOR-INVENTORY.json X6.

**Evidence.** X6 attributes all its facts to me, but some came from elsewhere or were not observed:

- I observed with file(1) only the three bundled Node builds, which are Mach-O 64-bit arm64. I did
  not observe the architecture of the Node embedded through Electron, yet the text says "all
  Mach-O arm64".
- The system Python's 3.9.6 comes from main's HOST-INVENTORY.md. The Director's raw inventory
  shows that executable as a universal binary.
- The versions of two Node executables were not read, so "None is `v24.22.1`" is not established
  for them. The verdict still holds: every one of them is Mach-O, so none is the 126,951,512-byte
  Linux ELF build.

**Correction:**

- limit "Mach-O arm64" to the three bundled builds;
- cite HOST-INVENTORY.md for 3.9.6;
- base the verdict on file format and size.

### F-15: nonmandatory. Route E's A6 statement, and the claims list

**Location:** REVIEW-OUTCOME.md section 6 (route E, and "Claims that no route can support");
OUTCOME.json `routes_for_owner[E]` and `never_supported_by_a_substitution`.

**Evidence:**

- **(a) Route E.** Its *Unchanged* list names Linux, glibc, the original supervisor, the procfs and
  ldd bindings, and the ELF closure model. It does not say how the seven methods' test meaning is
  kept:
  - the method bodies, `check_case` and the seams;
  - the synthetic GLBs and the oracle;
  - the 24 reader files and the probe's scientific body;
  - the thresholds and limits;
  - the three real checker starts through the original supervisor;
  - the no-skip rule and the numerical audit.

  "Keeping more of the original test meaning" implies these but does not state them, and A6
  requires the statement for every substitution.
- **(b) Claims list.** It was narrowed from "`/0.1.1` to `/0.1.5`" to "the x86-64 ELF policies of
  `/0.1.2` to `/0.1.5`". The `/0.1.1` origin rule, as adopted, binds the x86-64 author-Python pin
  (inspector `PYTHON`, lines 142–143; `_check_origin_subject_binding`, lines 1611–1615). So no
  result from route C or E could show it exercised either.

**Correction:** give route E an explicit *Unchanged* list, and restore `/0.1.1` (or say "the
`/0.1.1` to `/0.1.5` policies as adopted").

### F-16: nonmandatory. R04's resolution and what the selection binds

**Location:** REVIEW-OUTCOME.md section 6 (the recommendation) and section 7 (R04); OUTCOME.json
`gates.R04` and `recommendation`.

**Evidence.** The selection that the branch driver requires binds one exact, clean source state
and one boot:

- `_verify_source` (provider lines 326–367) requires HEAD to equal the configured commit and tree.
  For an original selection it refuses dirty tracked files and untracked source.
- `_verify_host` compares the host document with the current procfs boot id (lines 474–478).
- `prepare_readback_selection` validates the original checkout before the workspace copy.

**Consequences:**

- **Every later run needs its own selection.** After R04, every default local routine run on main
  would need a newly observed and independently approved selection for its exact commit and the
  current boot, whatever executor is qualified. That holds for any later work, and also for runs
  on uncommitted changes.
- **Route E's selection would live only in the guest.** The routine in the owner's macOS `.venv`
  would still refuse.
- **The amendment is not an alternative.** The text presents "another reviewed amendment of the
  selection rule" as an alternative to routes C and E. For main's ordinary routine it is needed
  alongside either of them, unless the integration design says how routine runs obtain a
  selection.

My round-1 F-04 used the same alternative wording; this corrects my own framing.

**Correction:** say that R03 needs route C or E (or A or B). Say that R04 also needs a reviewed
decision on how main's routine obtains a per-commit readback selection, or on whether it still
requires one. Note route E's guest-only selection in the comparison.

### F-17: nonmandatory. New record times after the commit

**Location:**

- `corrected_at_utc` in CONTRACT-REQUIREMENTS.json, EXECUTOR-INVENTORY.json,
  H0-CONSTRAINT-RECONCILIATION.json and OUTCOME.json;
- `recorded_at_utc` in REVIEW-DISPOSITION.json.

**Evidence.** All five state 2026-11-26T04:10Z. Commit `96847fae` was authored and committed at
04:04:02Z, and its record checks finished at 04:03:48Z. This is the same kind of error as F-08.

**Correction:** use the actual time, no later than 04:04Z.

### F-18: nonmandatory. Minor precision

- **(a) E19's range.** The provider range "lines 441–488" leaves out the ELF-interpreter binding
  (line 511) and the ldd shebang and inspection checks (lines 513–520).
- **(b) Supervisor labelling.** X1 says "The original supervisor cannot run on Darwin". That is a
  source inference, but section 8's list of inferences does not include it. On Darwin the failure
  would come from the ctypes lookup of `prctl`, before the `Stop` that E13 quotes. This too is
  source inference.
- **(c) Session checkpoint.** P30-SESSION.md calls itself "the declaration version". It gained two
  lines in the correction commit, with no note that they were added later.

## 6. Verdict

**ACCEPT_WITH_NONMANDATORY_FINDINGS.**

- F-01 is resolved.
- F-02 to F-11 are resolved as their dispositions say. Residual precision points are recorded
  above.
- The corrections introduced no mandatory error: no false statement that changes a verdict, no
  claimed execution, no relabelled gate and no adoption.
- F-12 to F-18 are nonmandatory. They can be corrected or recorded as dispositions.
