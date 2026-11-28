# Gate MR plan, attempt 2: the complete default routine at the corrected code, and R03 acceptance

Phase C271-P38, Director `c271-p38-1e501e005f79`, local mode. This is the second attempt at gate MR of
the adopted contract `ontokin.current-host-readback/0.2.0`, at design revision 4 (P33-AMENDMENT-001),
which is R03 of C271 on this executor.
- **The first attempt,** C271-P36, stopped at its operational freeze on FZ-01, a blocker in the
  implementation ([its outcome](../macos-routine-p36/OUTCOME.json)).
- **C271-P37 corrected FZ-01 and FZ-02** at candidate commit `5a3502e2`, and an independent review
  accepted it ([its outcome](../derived-workspace-p37/OUTCOME.json)).
- **The owner's selection.** Asked whether to start gate MR again, the owner selected "Start gate MR".
  The [declaration](PHASE.json) quotes the direction.

**This attempt follows [P36's MR plan](../macos-routine-p36/MR-PLAN.md) unchanged**: its sections 1 to
12, its stages, workers, fixed state, start accounting, failure policy, R03 review and records. This
document states only what differs and what the attempt carries. Times are UTC. Machine paths are left
out; places beside the clone are named relative to it.

## 1. What differs from the first attempt

| Item | First attempt (P36) | This attempt |
| --- | --- | --- |
| Bound commit | B `4ca78142` | B2: the commit that carries this phase's inventory addendum (section 2). Its code is candidate C's, unchanged |
| S2, the start-and-write inventory | W1's complete inventory at B | an **addendum** by a fresh W1: every start and write that C's changes add or change, read against P36's inventory, whose D-P1 to D-P7 stay |
| S3, the tooling | written and reviewed, committed at B | **reused unchanged** at its committed path (tooling review 002 accepted it). The freeze binds each tool by digest, with an independent sums check at P00 (FZ-03) |
| S4 to S10 | as planned | as planned, at B2 |

S2's addendum and its disposition are committed at B2, pushed and read back. No other stage of the first
attempt is reused: its observation plan, HOST, freeze and their reviews bind B.

## 2. The inventory addendum (S2)

A fresh W1 reads P37's changes at C, recorded in P37's [outcome](../derived-workspace-p37/OUTCOME.json)
and its review's RV-06 (a). Among them:
- **The driver's index refresh,** one `update-index -q --refresh` per run. In R1 it runs through the
  bound Git.
- **The 67 new tests' starts:** Git through the `PATH` dispatcher in fixtures and wrappers, `/bin/sh`
  stand-ins, `cat`, and `uname` and `file` through `platform.platform()`.
- **The LFS case:** with LFS files, the clean filter moves from the first status read to the refresh.

For each new or changed start, W1 records the program, the argv pattern, the environment and the `-B`
question, as P36's plan section 4 asks. It also says whether the start can reach a Node other than the
pinned runtime, `ldd`, `codesign` or a bound tree, and what changes in R1's and R2's expected starts.

The Director's disposition states what the freeze must carry.

## 3. What the attempt carries

**Into the observation plan (S4) and HOST (S5):**
- a new plan, HOST and review at B2. P36's HOST `858ef72a` binds B, so it is a record of P36 only;
- the host rules of P36's plan section 6, which apply again from the observation plan's freeze to the
  end of the audit.

**Into the operational freeze (S6) and its review:**
- **from gate MR's first freeze review:**
  - FZ-02 to FZ-09, as [its disposition](../macos-routine-p36/reviews/FREEZE-REVIEW-DISPOSITION-001.json)
    carried them;
  - the review's answers to Q-1 to Q-12;
  - freeze 001's method and its attribution rows, each derived again at B2;
- **from P37's review:** RV-06 (a) to (e):
  - (a) the new starts, through S2;
  - (b) MC28's 474 additions in [INVENTORY-ADDITIONS.json](../derived-workspace-p37/INVENTORY-ADDITIONS.json),
    which the freeze approves or refuses;
  - (c) FZ-06 extended to P37's 67 tests;
  - (d) FZ-02's margin, stated again from this attempt's own records;
  - (e) the derived checks after the source check, which R1 exercises for the first time;
- **RV-04:** P37-C34 counts under MC19;
- **the expected outcomes from P37's ordinary run at C,** which are evidence for the freeze, not
  attributions:
  - the 92 tests that do not pass: MI's 91 records on this host and RI_L08;
  - MC22's setup error.

**For the R03 review (S9):** RI_L08 has no record that establishes it, so it stays a finding. Every
attributed failure still needs the review's classification under OK-ENG-009 section 3 item 4 (FZ-04).

## 4. Start accounting

As P36's plan section 8:

| Run | Node | Other |
| --- | ---: | ---: |
| M0 | 0 | 1 |
| M1 | 1 | 0 |
| R1, the CPU trio | 3 | 0 |
| R2 | 0 | 0 |
| **Expected for MR** | **4** | **1** |

The inventory addendum adds only starts that are recorded but not counted, unless W1 finds otherwise.

## 5. Acceptance

[PHASE.json](PHASE.json) restates P36's acceptance items A1 to A11 for this attempt. A1 now also covers
this plan, and A3 covers the addendum and the tooling's unchanged reuse.

## 6. Records

This directory holds the declaration, this plan, `inventory-addendum/`, and then the records of P36's plan
section 11 for this attempt. The exact files stay beside the clone under `../OntoKin-local/c271-p38/`.
