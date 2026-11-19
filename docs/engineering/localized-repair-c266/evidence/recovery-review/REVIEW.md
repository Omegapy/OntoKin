# C266 recovery review

## Decision

Approve reuse of the recovered implementation and retained independent review
for the declared input-binding scope. No mandatory source defect or evidence
integrity finding remains. The Director must still complete the declared fresh
candidate checks, integration, resulting-main checks and saved handoff delivery.
This review does not mark those separate gates complete.

Reviewer: actual subagent `/root/candidate_review`, independent of the
implementation author and Director. Inspected recovered candidate
`e808af1403411960ebf360aa4588c9e358d2035a`. The implementation is 17,639 bytes,
SHA-256 `68849dbe3339c158eac7ec43fb1defcbd2993c37c6a0a5ee813d2da71fb03dda`,
Git blob `9c9b4bb3105ff13c3dd684d56c89faa3ec621e15`. It equals the original
reviewed implementation at `5454bfeb2c27aed0af23fb4dd363638ffbb10b07`.

## Scope and source review

Read root AGENTS, ROLE, the workflow protocol, complete session and delivery
skills, C266 requirements and plan, C260 contract, component README, coverage,
source, independent control suite and fixture helper. The checkout contains
only the root AGENTS.md. All writes by this reviewer are confined to this
`recovery-review` directory; no implementation, dependency, prior evidence,
Git index or remote reference was changed.

The implementation validates the independently derived canonical source
manifest and program revision, the complete object identity/path sets and
both retained object provenance maps. Exact primitive type matching prevents
Boolean/integer and integral-float substitutions in mapping fields. Generated
input-entry witnesses cover the complete keyed entry. The path renderer keeps
quoted key steps distinct from member steps. Every public call checks the
exact dependency bytes and rejects symbolic-link dependency paths before
loading them. Standard-library imports remain the only direct imports.

Source, artifact and identity readers remain pinned to their original bytes.
The implementation uses the source occurrence utility to derive object facts;
it does not use product parsers, evaluators, exporters or a comparator to
supply expected hinge values. The independently authored fixture helper
constructs expected mappings from explicit source recipes and does not import
implementation helpers or a product producer.

These observations support R01-R05 within the declared finite input-binding
boundary. R06's retained review evidence is consistent and reusable on these
exact bytes; its fresh applicable cohort is the Director's separate run.

## Executed evidence audit

The [audit script](audit_recovery.py) and [structured result](AUDIT.json) record
the exact command, environment, identities and checks. The audit passed with
no errors on CPython 3.12.14 in the assistant's hosted Linux environment.

- All seven records in C266 INPUTS.json match actual byte counts and hashes.
- Both independent-control input ZIPs pass CRC, safe-path, duplicate-name and
  content-addressed hash checks. Every recorded byte input resolves to an
  exact matching ZIP payload, with no unreferenced payload.
- Run 02 contains 34 distinct methods and 748 recorded API calls: 28 binding
  returns and 720 typed refusals, all matching expectations. Checked source,
  test and helper snapshots equal the current candidate. Dependency pins match.
- Run 01 retains its two failed positive-fixture expectations and original
  test/helper snapshots. Its implementation is unchanged. It is not relabeled
  as a successful run.
- The original review archive matches its external byte/hash receipt; all
  453 payloads match the internal manifest. Its retained scripts, reports,
  case sources and artifacts agree with their declared identities.
- The review reports preserve 89 executions: 88 passing attempts and one
  failed reviewer fixture. Their final per-name dispositions contain 87
  distinct passing controls. The corrected insertion fixture replaces only
  its disposition; the earlier failed evidence remains present.
- The dependency supplement matches its external receipt and all 18 manifest
  payloads. All five retained experiments have an initial successful call
  followed by the expected typed INPUT_BINDING refusal after dependency
  mutation, removal or symbolic-link substitution. Their original code and
  executed script identities match.

These are fresh evidence-integrity checks, not a claim that the historical
behavioral suites were freshly executed by this reviewer. The Director runs
the declared candidate and resulting-main cohorts separately.

The first audit script assumed that every reviewer case had an artifact.glb
payload. The deliberate nonbyte-artifact control has no byte payload and
correctly records a null hash/size plus a typed refusal. That audit assumption
was corrected. [ATTEMPT-01.json](ATTEMPT-01.json) and the exact first script
retain the failed audit attempt. No candidate code changed.

## Preserved limits

Successful input association does not compare hinge values, the hinge set or
ordered endpoints. The implementation exposes those agreement flags as false
and returns no qualified hinge set. Independent controls intentionally permit
changed or omitted hinge rows while checking that limit. Top-level
module/scene, program collections omitted by the raw reader, unrelated node
metadata and source prose remain explicitly unobserved.

No complete C260 H group, historical endpoint admission, site-pose evaluation,
full source/glTF validity, accepted-revision/edit atomicity/rebuild result,
native execution or comparative authoring benefit is established. No broad
product regression or alternate Python role was run by this review.
