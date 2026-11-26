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
