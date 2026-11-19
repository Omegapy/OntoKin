# C266 final recovery evidence audit

## Decision

**Approve reuse of the completed candidate scientific checks and retained
independent review.** Reviewer `/root/evidence_audit` inspected the recovered
candidate and executed the independent [audit](audit_candidate.py). The
[result](AUDIT.json) passes 4,016 evidence-integrity assertions with no unresolved
finding. This is a new evidence audit, not a rerun of the historical behavioral
suites and not an integration or delivery claim.

The retained candidate run identifies actual Git commit
`4986089edbd4443b05ef091d06bf4df55dfcdfa9` and tree
`f0240182b44a91e9db362f43ae90d6005b397c3b`. All 119 recorded input identities
match that commit's exact Git bytes. The implementation, controls, fixture
helper, executed predecessor code, consumed corpus and pinned dependencies
still match the recovered checkout. Later metadata differences are enumerated
in the audit; they require current workflow and documentation checks.

## Verified retained evidence

- All 16 candidate output identities match, including the ten recovered log
  files. Every log agrees with its recorded byte count, SHA-256, result and
  applicable method count. The run completed ten groups and 222 methods, with
  fourteen C253 corpus bindings and passing workflow/documentation checks.
- The C266 run retains 34 distinct methods and 748 public-API outcomes: 28
  bindings and 720 expected typed refusals. Every byte input resolves to a
  matching content-addressed archive member; all archive members are referenced.
  Successful bindings keep every wider qualification flag false.
- Every candidate checked-code snapshot matches the actual current source.
  All seven dependency/contract pins match. Implementation SHA-256 remains
  `68849dbe3339c158eac7ec43fb1defcbd2993c37c6a0a5ee813d2da71fb03dda`,
  identical to the reviewed Git implementation at
  `5454bfeb2c27aed0af23fb4dd363638ffbb10b07`.
- The original review archive matches its external identity, complete manifest,
  payload hashes and CRC. Its three reports retain 89 executions, including
  88 passes and one reviewer-fixture failure; current named dispositions retain
  87 distinct passes. The dependency supplement matches its external identity
  and full manifest and retains five passing dependency-admission experiments.
- The earlier recovery audit script matches its recorded identity, and its
  retained approval agrees with the same implementation and review evidence.
  Failed original runs and the earlier corrected reviewer fixture remain intact.

The audit also checks safe archive paths, duplicate members and symbolic links.
Its exact command, interpreter, platform, inspected revision, complete
assertions and input comparisons are in `AUDIT.json`.

## Preserved audit correction

The first audit attempt assumed that every recorded source input was a byte
identity object. A deliberate wrong-type source control records a descriptive
string. This caused an auditor `AttributeError`, not a product test failure.
[ATTEMPT-01.json](ATTEMPT-01.json) and the exact
[initial script](audit_candidate_attempt_01.py.txt) preserve that attempt.
The corrected audit checks snapshot identities only for recorded byte objects;
the wrong-type control still has to match its expected typed-refusal outcome.

## Remaining gates and limits

The Director must check later workflow/documentation changes, perform
expected-head integration, execute the applicable actual-main checks, verify
branch disposition, and confirm the saved handoff and external receipt.
This review does not waive those gates.

No hinge-field, complete joint-set or ordered-endpoint comparison is qualified.
Historical admission, full C260 groups, native/visual/model checks and other
Python compatibility remain outside this audit. The product implementation,
dependencies, fixtures, historical evidence, Git index and remote references
were not modified by this reviewer.
