# N57 mapping question before implementation

Status: raised to the Director and independent reviewer; no adjudication claimed.

## Observed inputs

The authenticated candidate is `docs/engineering/localized-repair-c271/loader-path-p11/design/candidate004` at supplied source revision `79292cf456df6e0f49524fcb1fcfd1fd2f7b08ae`. Its candidate-manifest SHA-256 is `e7b505aa768d0656db6c4dfaf7541e796aefee7148878a6fdf380d6ab0b911de`. All candidate payloads, 97 case records and 131 fixture files were verified and privately copied. See `MATERIALIZATION-RECEIPT.json` and `MATERIALIZATION-ATTEMPT001.json`.

`N57_source_variant_unknown.json` differs from `P01_nonselecting_base.json` in exactly one field: `variant_review.completeness` changes from `synthetic_declared_complete` to `unsupported`. Its loader identity, source-review identity, suffix list, external digest-match observation and every filesystem/kernel/image observation remain identical.

The frozen expected refusal is `CHI-UNSUPPORTED`, stage `variant_review`, rule `LP-VARIANT-SEMANTICS`. The route is `origin_rule`, which the control contract defines as a future production private raw-metadata/origin/nonselecting helper exercised through explicit observation seams. It is not an external reviewer workflow.

## Relevant adopted boundary

`DECISION.md` section 3 closes the operational variant document to exactly `schema`, `loader`, `source_review`, and `suffixes`. It contains no completeness field. The source review must justify the actual loader's alternatives and the completeness of that suffix union. The implementation checks the exact reviewed inventory and facts; it does not infer implementation semantics from an assertion in JSON.

Section 5 explicitly retains source-backed suffix completeness as an independent-review obligation. Section 7 and `FUTURE-SURFACE.json` authorize only the bounded inspection implementation and new focused adapter/tests. They do not introduce a loader semantic whitelist, review-result schema, or automated source-review mechanism.

## Inference requiring adjudication

The production predicate corresponding to N57's sole synthetic mutation is not yet identified. Both a positive and a negative control must reach the actual production helper through a faithful adapter. Adding an operational completeness flag would change the closed schema. Having the adapter itself reject this field, fabricate a different document/schema/digest, or construct its expected refusal would not exercise the accepted implementation with the frozen observation.

A private helper may legitimately require an already admitted policy, but its production caller still needs a specified source of that admission. A plan whose externally approved digest and all referenced identities agree does not give the implementation a separate observable distinction for the N57 mutation under the currently specified fields.

The Director has requested independent adjudication before any N57-dependent patch. This file documents the concrete question, not a final defect verdict. No production/test source has been edited, no adapter has been constructed, and no product behavior or test has run at the time of this record. No operational runtime was inspected or changed.

## Decision needed

Identify an already specified production predicate and a faithful mapping for N57, or record that the accepted design/control surface is insufficient and stop this phase with preserved evidence. The implementer will not change the oracle, add a schema field, substitute an easier input, or implement an undocumented semantic gate to obtain a pass.
