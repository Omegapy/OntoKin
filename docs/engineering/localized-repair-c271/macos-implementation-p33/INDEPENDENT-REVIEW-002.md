# Independent review 002 of gate MI (C271-P33): re-review of D-20 and refreeze 002

- **Reviewer:** W7, the same fresh-context, read-only reviewer as review 001. It wrote none of the
  implementation, the controls or the decisions.
- **Candidate:** commit `c534e7b72201dbf0ed6b366f5b0ec631415dedb0`. The change under review is
  `git diff 2d8d6d15 c534e7b7`, in three commits:
  - `df9420f2`: D-20, its implementation and test changes, review 001 and
    REVIEW-DISPOSITION-001.json;
  - `7b759de0`: W6's refreeze 002;
  - `c534e7b7`: CHECKS.json with final-003, and INVENTORY-ADDITIONS.json.
- **Reviewed against:** `ontokin.current-host-readback/0.2.0`, profile `darwin-arm64-v1`, design
  revision 4 (P33-AMENDMENT-001).
- **Verdict: ACCEPT_WITH_NONMANDATORY_FINDINGS.** There is no mandatory finding.
  - D-20 resolves I-01, I-07 and I-08, and the observed part of I-02.
  - Its other dispositions are sound.
  - Two new nonmandatory record findings, I-09 and I-10, concern the closing records.

Scratch work and logs are beside the clone in `../OntoKin-local/c271-p33/reviews/mi-002/`. The
0.1.0 driver log was redacted with the Director's script. This review quotes no environment value.

## Scope and method

- **What changed:** 12 files.
  - **Implementation:** the facade appended to the 0.1.0 provider (45 lines added, 8 removed)
    and the 0.2.0 accounting (4 added).
  - **Tests:** W3's MC20 system-link case, W5's development tests, and W6's two added controls.
  - **Records:** D-20, REVIEW-DISPOSITION-001.json, CONTROLS-REFREEZE-002.json, CHECKS.json,
    INVENTORY-ADDITIONS.json, and the published copy of review 001.
- **Unchanged since review 001:** every other implementation file, including the Darwin
  supervisor, the observer, both probes, the driver, `storage_identity` and the preparer.
  Review 001's MC14 comparison and its probe-body derivation therefore still apply.
- **Reproduced:**
  - all sixteen modules, run as before;
  - the observer module run again with TMPDIR on the checkout's own volume;
  - two scratch scripts, which started no process: one exercises the facade's binding through
    its three seams, the other checks the new ledger predicate against the adapter's ledger;
  - the digest, identity and audit checks.
- **Not run:** Node, `ldd` or `codesign`; any other test module or discovery; the workflow check
  and the documentation verifier, which final-003 records as passed; downloads.

## 1. I-01: the facade's version binding

- **A 0.2.0 cohort is always reconciled by the 0.2.0 code.**
  - `setup_cpu_cohort` binds the version it selects: to the class as `readback_dispatch_version`
    and to the module's `_COHORT_BINDING`.
  - The readback class calls the facade's three seams. `setUpClass` calls `setup_cpu_cohort`,
    `check_case` calls `guarded_run_process`, which it imports as `run_process`, and
    `tearDownClass` calls `finish_cpu_cohort`.
  - Inside a cohort, `guarded_run_process` follows the module binding, and `finish_cpu_cohort`
    follows the class's binding.
  - My `binding_demo.py`, case A, used a stand-in for the work of a passed 0.2.0 setup and the
    candidate's own facade, adapter and accounting.
    - After the configuration changed, the selection alone gave 0.1.0, while the bound version
      stayed 0.2.0.
    - The attempt was refused by the 0.2.0 provider: `CH-SELECTION`, `refusal/0.2.0`, zero starts.
    - The accounting was refused by the 0.2.0 provider.
    - The only document written was `cohort/0.2.0`, with design revision 4 and labels.
  - W6's frozen case shows the same with the real 0.2.0 setup, under mocked verifications. Its
    evidence line lists `setup/0.2.0`, `lock/0.2.0`, `cohort/0.2.0` and `preserved-cohort/0.2.0`,
    and no 0.1.0 document.
- **The binding's lifetime is right.**
  - It ends in `finish_cpu_cohort`'s `finally`, whether the accounting passes or refuses (case B:
    the binding is empty, the class attribute is gone, and dispatch follows the selection again).
  - It ends at once when the setup raises (case C: the real 0.2.0 setup refused a one-field
    configuration, and no binding remained).
  - An ordinary run raises before any binding is made.
  - unittest brackets each class with its setup and teardown and never interleaves classes, and
    every test that calls the seams ends or restores the binding: W5's `DispatchTests` reset it
    in a cleanup, and W6's case patches it. A binding therefore cannot leak into a later class or
    into calls outside a cohort.
  - Outside a cohort, every call follows the selection, as D-20 states. Case D shows the
    boundary: an accounting called on a class that the facade never set up follows the selection,
    and with a changed configuration that is the 0.1.0 accounting. The readback class cannot reach
    this path, because unittest runs `tearDownClass` only after a successful `setUpClass`, which
    binds.
- **0.1.0 behaviour is unchanged.**
  - A 0.1.0 cohort binds 0.1.0 and dispatches exactly as before. A 0.1.0 configuration's bytes
    cannot turn into a digest-matching 0.2.0 configuration.
  - The partial and ordinary cases are as before, and the existing 0.1.0 provider module keeps its
    phase-start outcome (22 of 25).
  - The first 65,533 bytes of the 0.1.0 provider are still exactly the committed file. The common
    prefix with `2d8d6d15` is 71,544 bytes, as the refreeze record states.

## 2. I-07: the ledger check

- **It matches the real ledger.**
  - `guarded_run_process` writes `{"schema": PREFIX + "attempt" + VERSION, **_identity(), …}`
    through `_write_new`'s canonical JSON.
  - My `ledger_check.py` read that literal from the source, round-tripped the ledger's head
    through `_canonical`, and found the accounting's predicate accepts it (`amendments` is a list
    on both sides).
  - The check runs before any other field is read, so a non-dict row now refuses cleanly.
- **W5's changed fixture is faithful and weakens nothing.**
  - A unit-by-unit source comparison shows that only `CohortAccountingTests.ledgers` and
    `DispatchTests.setUp` changed; four tests were added and none removed.
  - The fixture now writes the schema and identity that the adapter writes, and every existing
    expectation is unchanged.
  - The new test refuses five variants: another schema, no schema, another contract, another
    design revision, and no amendment.

## 3. I-02: MC20's system-link case

- **Assertions kept:** only this method changed in W3's module, and its three assertions are
  unchanged.
  - The `/var` spelling starts with `/var/`.
  - `canonical_path` resolves it to the `/private` form.
  - `_canonical_value` refuses the non-canonical spelling.
- **Runs whatever TMPDIR resolves to:** the fixture now lies under the fixed `/private/var/tmp`.
  It passed under the default TMPDIR, and also with TMPDIR resolved on the checkout's own volume:
  109 tests OK, no skip.
- **Leaves nothing behind:** a cleanup removes the fixture. No `ontokin-mc20-*` entry remained in
  `/private/var/tmp` after my runs or the Director's.
- **What remains:** the module's skips off Darwin. D-20 places them at R04, which is right: on
  another system both drivers count each of them as a stage failure.

## 4. D-20's other dispositions

- **Sound:**
  - I-03: MP's plan states the receipt's limit and requires a separately verified clean checkout.
  - I-04: recorded in D-20 as superseded; the note stays as written.
  - I-06: noted. I confirmed that `task.json` round-trips exactly with `indent=2` and
    `ensure_ascii=False`.
  - W5's Q5: carried to MH, where the probe first runs.
  - The version-neutral refusal is declined. No document is written for such a refusal, and the
    contract defines none.
- **Placement:** D-20 places the carried obligations in the outcome record's `for_later_gates`.
  That record is not in the candidate: it is written at closing. I read the Director's draft
  builder, `../OntoKin-local/c271-p33/director/drafts/build_outcome.py`.
  - Its MP, MH, MR and R04 lists place correctly the items of review 001's I-05 and the two added
    ones: MC16's two-volume premise and D-18's effect on MR.
  - Three items of I-05 are missing, and one is misplaced (I-09).
- **Superseded note:** W5's interface note still describes the old dispatch of the three seams
  (I-10).

## 5. Refreeze 002

- **Additive.**
  - The module's diff from `2d8d6d15` holds insertions only.
  - A unit comparison finds no changed unit, and five added ones: two test methods and three
    Mach-O helpers.
  - CONTROLS-FROZEN.json (`cd7ae80f…`) and CONTROLS-REFREEZE-001.json (`fb01cd4a…`) are
    byte-identical.
  - The module (`3b8c91b7…`) and the two changed implementation files (`cb3f0c7f…`,
    `d34ea2f9…`) match the refreeze record.
  - The counts are 151 methods: real 61, simulated 67, mocked 23.
- **Faithful to the contract.**
  - MC06's added case accepts the allow-listed `LC_DYLD_INFO_ONLY`, from section 7.
  - MC29's added case expects:
    - the refusal of a configuration changed after setup, with zero starts (MC29);
    - no 0.1.0 document, and only `/0.2.0` provider schemas under the evidence parent
      (section 1);
    - section 10's labels on the cohort record;
    - the end of D-20's binding.
  - It also pins two implementation details. One is the provider's category `CH-SELECTION`,
    which is consistent with earlier frozen cases. The other is the binding, observed through the
    facade's private names; W6 records these names, and a rename fails visibly.
  - None of this weakens an expectation.
  - The label is `mocked`, correctly: the verifications and the supervisor are substituted, and
    the change itself is real.
- **Committed before execution:** `7b759de0` was committed at 19:44:51Z. final-003 started at
  19:45:05Z on that commit, on a clean tree.

## 6. final-003

- **Outcomes:** they support every claim, and my run reproduced them exactly. The non-passing sets
  of all sixteen modules are identical to final-003's.
  - The new modules and `test_local_checks` are OK with zero skips. That includes the 151
    controls, 49 provider tests and 109 observer tests.
  - Every existing module is identical to its phase-start baseline, except D-18's three entries
    in the 0.1.0 driver module.
- **Logs:** all 16 final-003 log digests in CHECKS.json match, and the earlier 31 still match.
- **Audit:** 877 `subprocess.Popen` events and no hook error. None is Node, `ldd` or `codesign`.
- **Redaction:** the 0.1.0 driver logs of final-003 and of its audit are redacted, one line each.
  No retained log or review holds an environment value.
- **INVENTORY-ADDITIONS.json:** 407 added and 0 removed; 5,587 + 407 = 5,994. The six new
  identifiers match the added methods.

## 7. Anything new

- **Safety path:** none. The new module-global binding exists only from a facade setup to its
  accounting, or until the setup fails.
- **Hidden skip:** none. The skip condition of MC20's case was narrowed to Darwin, and the skip
  stays visible.
- **Process left running:** none, after my runs.
- **Writes into the source tree:** none. The tree was clean before and after, with no new
  `__pycache__`.
- **Outside the evidence and temporary directories:** MC20's case now writes into the shared
  `/private/var/tmp`, and removes what it writes.

## Findings

| ID | Severity | Location | Issue | Required change |
| --- | --- | --- | --- | --- |
| I-09 | nonmandatory, records, check at closing | REVIEW-DISPOSITION-001.json (I-05); the outcome record's `for_later_gates`, drafted in `../OntoKin-local/c271-p33/director/drafts/build_outcome.py` | The disposition says the obligations are "consolidated in OUTCOME.json", but that record is not in the candidate. The draft omits three items of review 001's I-05. MP: M0's exact package rule, under which no distribution other than the seven pins (for example pip) may be in the venv's site-packages. MP and MH: W3's F4, under which the qualification interpreter must not run without `-B` between the freezing of the Python inventory and M0. N34-M and MH: W3's Q3 and its assumption that only `CPU_SUBTYPE_ARM64_ALL` is admitted. The draft also places I-07's inherited half, the 0.1.0 accounting, under MH, though a 0.2.0 cohort no longer reaches it. | Commit the outcome record at closing with the three items added, and move the inherited half to "Linux contract work". The closing check confirms that the record exists. |
| I-10 | nonmandatory, records | `interfaces/W5-PROVIDER.md`, section 4, the dispatch table | It still says that `guarded_run_process`, `setup_cpu_cohort` and `finish_cpu_cohort` dispatch on the environment's selection. After D-20, the adapter and the accounting follow the version that the cohort's setup bound. | Record that section 4 is superseded by D-20 for these seams, as D-20 does for W2's note. |

The findings of review 001 stand resolved, as follows:
- I-01, I-07 and I-08 are fixed and covered by tests and frozen controls.
- I-02 is fixed for the TMPDIR case, and its off-Darwin skips are placed at R04.
- I-03 to I-06 are carried or noted as D-20 states.

## Reproduction

Commands ran from the checkout root unless stated. Scratch files are in
`../OntoKin-local/c271-p33/reviews/mi-002/`.

| Check | Outcome |
| --- | --- |
| `git --no-optional-locks diff --stat 2d8d6d15 c534e7b7`, with each commit's `--stat` | 12 files. `7b759de0` adds only the refreeze record and the controls module; `c534e7b7` adds only CHECKS.json and INVENTORY-ADDITIONS.json |
| Python prefix comparison of the 0.1.0 provider | the first 65,533 bytes are identical to `1c2f25ba`; the common prefix with `2d8d6d15` is 71,544 bytes |
| `git diff --quiet` from `1c2f25ba` for `supervisor.py`, the 0.1.0 probe, the inspector, `readback.mjs` and the driver companion; from `2d8d6d15` for the other implementation files | exit 0 for both |
| `python3 -I -S -B mi-002/units_diff.py` on the three changed test modules | controls: 5 added, 0 changed; provider: `ledgers` and `DispatchTests.setUp` changed, 4 added; observer: only the MC20 case changed |
| `shasum -a 256` of the refreeze inputs | CONTROLS-FROZEN.json and REFREEZE-001 unchanged; the module and the implementation digests match refreeze 002; 151 methods, labelled 61, 67 and 23 |
| `git log -1` of `7b759de0` against final-003's start | 19:44:51Z before 19:45:05Z |
| `zsh mi-002/run_modules.sh mi-002/run-001` (the sixteen modules, `.venv/bin/python -B`, resolved TMPDIR, logs redacted) | identical to final-003; identical to the baselines except D-18; zero skips; tree clean; no `__pycache__`; nothing left in `/private/var/tmp`; no process left |
| `tests.test_current_host_observation_v02` with TMPDIR resolved on the checkout's volume | 109 OK, the MC20 case `ok`, no skip, nothing left |
| `.venv/bin/python -I -B mi-002/binding_demo.py <checkout>` | A: attempt and accounting both 0.2.0, only `cohort/0.2.0` written. B: binding ended. C: binding ended after a failed setup. D: an un-set-up class follows the selection. No process started |
| `.venv/bin/python -I -B mi-002/ledger_check.py <checkout>` | the accounting's predicate accepts the adapter's ledger head |
| Digest check of CHECKS.json's `log_sha256` values | final-003 16 of 16; earlier runs 31 of 31 |
| Summary of `final-003-audit/starts.jsonl` | 877 Popen events, 0 hook errors, no Node, `ldd` or `codesign` |
| Marker scan of `checks/` and `reviews/` | no environment value; one redaction line in each 0.1.0 driver log |
| `json` round-trip of `docs/workflow/tasks/C271/task.json` | byte-identical with `indent=2`, `ensure_ascii=False` |
| `cmp` of the published INDEPENDENT-REVIEW-001 copies | byte-identical to the originals; the digests match the disposition |
| `git --no-optional-locks diff --check`, from `2d8d6d15` and from `1c2f25ba` | clean |

## Evidence

- My scratch: `../OntoKin-local/c271-p33/reviews/mi-002/`, including run-001, the scripts and
  their outputs.
- The Director's runs: `../OntoKin-local/c271-p33/checks/final-003/`, `final-003-audit/` and
  `d20-dev/`.
- Review 001: `../OntoKin-local/c271-p33/reviews/mi-001/`.

**Limits.** This review covers only the executed Python on this host. It qualifies nothing. MP,
N34-M, MH, MR, R04 and R05 remain separate gates.
