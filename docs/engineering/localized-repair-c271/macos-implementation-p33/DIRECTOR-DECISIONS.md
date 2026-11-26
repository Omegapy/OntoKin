# C271-P33: Director's decisions during gate MI

Director `c271-p33-a99647756bed`. These decisions settle questions raised by the workers. They
stay within the adopted contract and the [implementation plan](IMPLEMENTATION-PLAN.md). A
decision that would change the contract goes through an amendment instead, as
[AMENDMENT-001](AMENDMENT-001.md) does.

## D-01: the 0.2.0 preparer checks its source (W2 Q1)

Yes. The 0.2.0 route verifies the checkout's commit, tree and clean state, as the 0.1.0 route
does. It uses Git through `git_executable()` (plan section 4.5) and the `/0.2.0` source document
of the 0.2.0 provider. Both of these arrive with W4 and W5, so the source check is added after
them, as an integration step of W2's file.

## D-02: a failed signature check does not refuse in the preparer (W2 Q2)

The contract (section 3) makes the adopted pin the trust anchor. A signature check with a
Node.js release key is optional additional evidence, "recorded either way". The preparer
therefore records `failed` and does not refuse. MP's plan and its independent review treat a
`failed` status as a mandatory finding to resolve before MP closes.

## D-03: the design revision in results (W2 Q3)

If AMENDMENT-001 is adopted, every document that a 0.2.0 component writes carries
`"design_revision": 4`:
- the install result;
- HOST;
- every readback result, refusal, setup, attempt and cohort document.

The field goes beside the existing contract field. The field is added only after the
amendment's adoption.

## D-04: which labels a preparation receipt carries (W2 Q4)

Plan section 5 said that "every 0.2.0 result and refusal document" carries all labels of
contract section 10. Contract section 10 states the labels of readback results. Plan section 5
is narrowed to that meaning:
- **Readback results and refusals** carry the full set of labels.
- **A preparation receipt** carries what preparation can observe before M0:
  - the executor label, the contract, the profile and the design revision;
  - the pins it binds;
  - the OS product version, build and cryptex version, read through the observer's exported
    reader.
- **Not in a receipt:** the Python inventory digest and the Git binding. They are M0's
  bindings.

## D-05: the inspector-side receipt rule (W2 Q5)

M0 replaces the inspector under 0.2.0. The adaptation of `_check_installation` to the layout
`{bin/node, NODE-SOURCE.json}` and to the install/0.2.0 result therefore belongs to the observer
(W3). It compares the same fields as the 0.1.0 rule, `source_root` included.

## D-06: member names and modes of the official archive (W2 Q6)

The 0.2.0 route refuses a non-ASCII member name and a mode above `0o7777`. Whether the official
archive contains either is not verified. MP's independent author confirms it when freezing the
real member inventory. A refusal there is a finding for MP, not a reason to weaken the rule.

## D-07: a 0.1.0 preparer finding left unchanged (W2 F1)

The 0.1.0 `install_plan` writes its report even to a path it refuses, a path inside the
checkout included. MI keeps 0.1.0 behaviour unchanged, so this stays as it is. It is recorded
as a finding for any later work under the Linux contract. The 0.2.0 route does not have it.
During development an early 0.2.0 draft wrote one synthetic report to the checkout root. W2
preserved it in its evidence and removed it; the checkout holds no such file.

## D-08: the missing-method rule of a qualifying run (W4 F1)

Contract section 8 says that, in a qualifying run, "any skip, error, expected failure or missing
method of the readback cohort fails the run". The shared driver fails a stage on any skip, error
or failure. It has no rule of its own for a method that is missing without an error. In 0.1.0
that case is caught by the provider, through the original-body and discovery checks, and by
the discovery control. Under 0.2.0:
- **Provider (W5):** the cohort accounting of `finish_cpu_cohort` must fail the run when one of
  the three CPU methods did not run, as the 0.1.0 accounting does. If the 0.1.0 accounting
  does not, W5 reports that instead of inventing a rule.
- **Discovery:** MC28, at MH and MR, checks the complete default inventory.

The driver does not change for this.

## D-09: Git starts of `tools/storage_identity.py` (W4 F2)

The driver's workspace preparation reaches `tools/storage_identity.py`, which starts `git` by
name from `PATH`: four starts per run. Plan section 4.5 requires every Git start that the
driver reaches to go through `git_executable()`. W4 routes them, as a follow-up within its
ownership. The other callers of `storage_identity` keep their behaviour unless they bind Git.

## D-10: the cryptex copy of `SystemVersion.plist` (W3 F1)

On this host `/System/Cryptexes/OS` is a symbolic link. Contract section 7 asks for "the OS
cryptex's copy of that file if present", without a path form. The canonical-path rule asks that
every bound path be "recorded in its canonical form, the realpath taken once and checked again
before use".
- **Path form:** the cryptex copy is an OS-provided file located by its conventional name, and
  is bound by its canonical path.
- **Hops:** the conventional name and each symbolic-link hop are recorded beside the binding and
  followed again at each check, as contract section 4 does for the Python selection chain. A
  retargeted hop refuses.
- **Scope:** this admits no symbolic-link ancestor for any path that a plan or configuration
  supplies; those keep the rule as written.
- **Review:** this is a reading of the contract, not an amendment. The independent reviewer is
  asked to confirm it.

## D-11: the install receipt that M0 checks (W3 F2)

W3 wrote M0's receipt rule from W2's interface note. W2 confirms that its preparer writes exactly
the shapes its note states, or corrects the note or the code, whichever differs from the
contract, and lists the correction. This follow-up is W2's, together with D-03 and D-04 for the
install result. W3's rule then follows the confirmed shape.

## D-12: after the adoption of P33-AMENDMENT-001

The amendment is adopted ([ADOPTION-AMENDMENT-001](ADOPTION-AMENDMENT-001.json)).
- **D-03 and D-04:** every document that a 0.2.0 component writes carries
  `"design_revision": 4` and `"amendments": ["P33-AMENDMENT-001"]`, beside its contract field.
- **Plan section 6:** the control assignment extends to MC37, MC38 and MC39. MI executes all
  three. MC37 runs again on each qualifying host at MH.
- **Superseded:** from revision 4 on, the amendment's section 3 supersedes these records, and they
  stay as written:
  - PHASE.json's acceptance A2, which says that only the precondition differs;
  - plan section 4.1, which imports `group_exists` and `terminate_group` unchanged.

## D-13: the documents that carry the design revision (W2's follow-up)

D-12's "every document that a 0.2.0 component writes" means these documents:
- the result, receipt, refusal, setup, attempt and cohort documents;
- HOST, and the observer's inspection receipts;
- the publication intent records.

It does not reach `NODE-SOURCE.json`. Contract section 3 lists that provenance record's content,
and plan section 4.2 fixes its keys. The install result that publishes it carries the design
revision and the amendments.
- **M0's receipt check** admits the install result's two new fields (W3's follow-up).
- **Concurrency:** W2's follow-up runs imported the 0.1.0 provider while W5 was editing it. The
  Director's final verification runs every test on the committed tree.

## D-14: the supervisor's process receipt carries no labels (W1's follow-up)

D-13's "receipt" means the preparer's install receipts. The supervisor's `<label>.process.json`
is the original process receipt. The contract keeps its fields unchanged (CONTRACT.json
`schemas.process_receipt`), and the amendment keeps `run_process`'s tokens apart from the
precondition (section 3.2). It therefore carries no labels and no design revision. The documents
that contain such a receipt carry them: the inspection receipts of M0 and M1, and the provider's
attempt and result documents.

## D-15: plans and the receipt's OS label (W3's follow-up, Q14 and Q15)

- **Plans:** the observation plan and the preparation and execution plans carry no
  design-revision field. They are frozen inputs. A reviewed execution plan binds them by digest,
  and that plan's review names the design revision it follows.
- **The receipt's OS label:** M0 checks the install receipt's OS label for shape only. That label
  records the OS at preparation. M0 binds the current OS itself in HOST, and the provider checks
  HOST against the host at every start. An OS update between MP and MH therefore shows in HOST
  and in the provider's checks, not as a receipt refusal.

## D-16: W5's findings and one integration correction

- **D-08 confirmed:** the cohort accounting fails the run when a CPU method did not run. The
  0.1.0 accounting already does this, and the 0.2.0 provider keeps it. No new rule is added.
- **The adoption-record digest:** the probe constant `AMENDMENT_ADOPTION_SHA` is filled with the
  SHA-256 of `ADOPTION-AMENDMENT-001.json` as committed in `3ffabb3f`. The Director checked it
  against the committed bytes.
- **`SOURCE_FILES`** does not list the adoption record. The configuration binds that record
  separately, as it binds CONTRACT.md, and the source inventory keeps 0.1.0's trees.
- **The provider's environment check (W5 F3):** it can test only HOST's recorded environment and
  the declared map. The probe tests its own `process.env`, as contract section 7 assigns.
- **For MH, MC36:** an altered `__CF_USER_TEXT_ENCODING` value in HOST makes the probe refuse
  only if the variable is present in the probe's environment. The predicate admits its absence.
  Whether the official `node` loads CoreFoundation is not established. Before MH's execution
  plan is adopted, MH establishes from M0's load commands whether the Node build links
  CoreFoundation:
  - If it links CoreFoundation, MC36 stands as written.
  - If it does not, MC36's expected outcome needs an amendment before it runs. The expectation
    is never weakened silently.
- **Integration correction:** W3's follow-up replaced the observer constant
  `INSTALL_RESULT_KEYS` with `INSTALL_RECEIPT_KEYS`, which is keyed by state. One assertion of
  W2's test module still named the old constant. The Director rewrote that single line to
  compare W3's `ALREADY_PRESENT_EXACT` key set, the shape the old constant stood for. No
  expectation changed, and the module's 59 tests pass.

## D-17: D-01 revised, how the 0.2.0 preparer binds its source

D-01 asked the 0.2.0 route to verify its checkout's commit, tree and clean state "as the 0.1.0
route does". A reading of P05 section 5 shows that this is not one of its rules. Section 5
requires:
- authenticated source bytes and a predeclared member inventory;
- the refusals;
- staging and no-replace publication;
- that runtime and dependency trees stay outside Git, "preserve their authenticated source
  identity and full reproduction receipt instead".

The 0.1.0 route's check of the checkout is an implementation choice tied to the 0.1.0 source
document. The 0.2.0 route meets section 5's rule. Its result records `preparer_source`: the root
and the identity of each preparer file at start. Under contract section 6 it keeps every rule of
P05 section 5.

D-17 therefore replaces D-01:
- The 0.2.0 route does not start Git, and it does not verify the checkout's commit.
- MP's reviewed preparation plan binds the commit of the preparing checkout.
- MP's independent review checks the receipt's `preparer_source` against that commit's files.

The final independent review of MI is asked to assess this.
