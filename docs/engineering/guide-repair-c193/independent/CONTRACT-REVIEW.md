# C193 contract and implementation review

**Approve candidate `61d20e9a941b14cea091dc38ed1e43232280ecb5` for separately
published adoption and bounded qualification.** This is not delivery acceptance.
The [exact review receipt](evidence/candidate-review.json) records every module
hash, the source examples, constructor/projection checks and unchanged history.

The new source selector is `c193-experimental-0.1`; the backend selector is
`blender-bullet-c193-0.1`. The profile and output meanings remain unchanged.
The new package and contract occupy separate `v02` and `v0.2` paths. All eleven
Python modules equal the previous implementation after only reviewed namespace,
path and manifest-hash substitutions. Seventeen constructor, capture and
projection function comparisons have identical abstract syntax trees. The
native validation and process supervisor are byte-identical to their originals.

The sole physical change is the GENERIC guide override count, 100 to 400 on both
lanes. World and MOTOR counts remain 100. Source geometry, the two 1 kg owners,
body and guide frames, motors, collision shapes, all 481 capture keys and
projection rules retain their prior meanings. The 1,000,000-operation and
80,000 ms qualification ceilings remain unchanged. The host counts scheduled
substeps; it does not observe Bullet's actual internal solver-iteration count.
The increased configured iteration work is explicitly disclosed and bounded by
the pinned settings and the original supervised deadline.

| Reviewed item | SHA-256 |
| --- | --- |
| New backend | `9ce64fd758b4e7f659ddd9d4bb3bcf7a0faa6a1883cc018c673e10536fe0aefe` |
| New contract manifest | `d5ce5afa4e1a548f493b9b0184798bfe8e88f954a2f57771e2d20e0256037037` |

## Provenance correction before adoption

The first exact-byte review rejected the candidate because its new `source.py`
retained the old contract-manifest hash in a fallback used by every source
manifest. The physical solver code was unaffected, but emitted provenance would
have named the wrong contract. The repairer corrected only the new package and
added an explicit source-manifest assertion. The old candidate and
[failed review record](evidence/candidate-review-attempts.json) remain preserved.
No formal C193 native build had started.

The corrected parser now emits the new contract hash for all six examples.
Direct-Python source manifests and build receipts also identify the verified
contract and backend; both routes retain the actual dependency closure. A
[supplemental artifact auditor](audit_provenance.py) will check those fields and
the exact executed implementation on every formal artifact. Its three guard
controls accept the current contract and reject stale contract identity and an
altered dependency hash. [Supplemental freeze](frozen/SUPPLEMENTAL-REVIEW-FREEZE.json)
preserves this new gate separately from the first checker freeze.

## Remaining mandatory gates

Execute the frozen fourteen-build, fourteen-replay plan. Preserve every original
numerical tolerance and require exact canonical/native/raw/final equality across
repeats and the two routes at E/F. Complete native causality and receiving checks.

The new store/result namespace also requires the inherited lifecycle cohort.
The separately frozen translation retains all 42 controlled cases, nineteen
failure methods, original budgets, diagnostic spans, cancellation and rollback
assertions. Only prefixes, paths and the formal-input bridge change. The bridge
requires all fourteen builds to finish successfully before selecting the actual
A store. The fault worker is byte-identical and copies retained native results;
it performs no new native physics. Two additional namespace checks verify that
each prototype rejects the other store schema without changing accepted bytes.
The repairer owns execution, and the reviewer will inspect its results.

All 474 pinned historical files still match. The old C191/C192 failures and
tolerances are preserved, and the separate legacy torque driver remains failed.
