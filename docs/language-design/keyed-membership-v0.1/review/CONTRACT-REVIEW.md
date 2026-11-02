# Independent review of C088 contract v02

Reviewer: `/root/membership_review`.

Reviewed specification: `c088-work/contract-drafts/v02/SPECIFICATION.md`, exactly 23,909 bytes, SHA-256 `e9a55ae015b1892453217deea38ea85e269e2551608ab5ed7aa7d21bea337d0b`.

## Disposition

**Acceptable for separate adoption and independent input freeze. No remaining contract blocker was found within this review's scope.** This is approval of the exact specification's design. It is not approval of unwritten code, an incomplete oracle, execution evidence, integration or release.

The v01 native Type-metadata blocker is closed by a fixed-depth closed-family admission rule. The correction rejects unvalidated host fields before equality/hash/string conversion; it creates only bounded metadata descriptors; and it preserves every .20 authored leaf family, including empty containers with Int scalar children. Generated references retain the existing compiler/linker authority and a source-derived 278-character nominal bound. Keys remain bounded independently. The revised paid-step wording correctly distinguishes a defined semantic operation from hardware character work.

The new diagnostic table and precedence text also close the malformed-leaf ambiguity: non-Value leaves, non-Type/malformed/mismatched leaf descriptors and UNKNOWN use the leaf-type error. Malformed expected descriptors and container/entry/key shapes use the collection error. These meanings are now specific enough to freeze independent hostile native inputs.

## Review checks

- The full draft was read and its byte count/hash checked. The differences from preserved v01 were reviewed against the earlier findings.
- The 19 simple native kinds match the exact .20 `_keyed_leaf` admission and its imported type sets. Scalar/container children have depth at most two. Quantity ZERO correctly becomes Real, and legal dimension exponents remain bounded in [-16,16]. Point3 uses Length metadata. Bool is excluded from native int metadata.
- No arbitrary recursive Type traversal or foreign equality/hash is authorized. Bounds precede inspection, comparison and hashing. Exact tuple shape/cardinality precedes entry traversal. Each entry key and its metadata are admitted under its own charged stage.
- Capturing the exact entry tuple and expected descriptor prevents later callbacks from swapping the scanned tuple by replacing a wrapper field. Leaf payloads are not evaluated, compared or reread. A future implementation must actually capture these values as specified.
- The `n+k+3` formula remains correct: admission/query/publication add three; each input entry is admitted once; equality examination costs one per actual position. Empty input costs three, first of256 costs260, and last/absent of256 costs515. Existing evaluator/provenance work remains separate.
- Missing context, callback identity, current ledger operation/deadline order and stage restoration remain consistent with C087. Host policy, caller caps, source limits, String-result quotas and old release gates are unchanged.
- Ordinary callee/argument order, source-sensitive name reservation, earlier qualified helper bindings, unknown static Bool, and inactive dynamic query-domain behavior remain coherent with current source. Generated-view access/shape taints and inherited binding memoization remain explicit.
- .21 inherits .20 String concatenation while preserving original String diagnostic profile and limits. The contract requires independent source, Agent, native, hostile and inherited observations before integration and makes no measured performance/authoring claim.

## Evidence and limits

Source basis remains C087 commit `a969a668f9fdf021793366ac5f5b9a8f9cd0fa56`, tree `2000393ec35ebc50d1517e71c7c1e630227b3a47`. All nine previously inspected exact production files recorded in `SOURCE-BASIS.json` were compared again with the independently recovered source at `/tmp/ontokin-c088-c087-recovered01/OntoKin`; all nine matched their recorded SHA-256 identities. The exact nominal-bound derivation and additional .20 protocol/type observations remain in the earlier review and supplemental observations.

No runtime, expectation, source, specification or preserved v01 document was modified. No product workload was executed. Actual candidate code must still satisfy this exact design and the independent frozen expectations; this review does not predict those results.
