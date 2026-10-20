# Combined review of the reconstructed planar reach proposal

This record identifies fresh preparation and review of the recovered and reconstructed Draft 2 proposal. It does not establish runtime implementation or release acceptance. The [recovery inventory](../draft2-recovery-20261020-14.json) separates byte-for-byte recovered inputs from work reconstructed after the executor rollback. The [release contract](../release-contract.md) retains all actual source, Agent, destination, browser, compatibility and inherited obligations.

## Reproduction and preserved attempts

Run the combined checker from the repository root with the pinned verification environment and a new output directory:

```sh
python3 docs/language-design/planar-reach-v0.1/contract-review/check_combined.py \
  --output-dir docs/language-design/planar-reach-v0.1/contract-review/checks-new-attempt
```

The checker records commands, raw logs, Python identity, source commit/tree and input hashes before and after execution. It verifies the original 103-file proposal inventory: 99 files remain byte-identical and four prose files carry the explicit Draft 2 amendments. The original source, generated expectations, oracle and verifier are unchanged. Generated check directories are evidence outputs and are excluded from the input inventory; this exclusion does not apply to the checks or reviewed contract themselves.

The retained [first combined attempt](checks-reconstruction14-001/report.json) passed eight of nine stages. Its original-fixture verifier rejected new README links that pointed to directories rather than files. Those navigation links were corrected to concrete files; the original verifier and expected corpus were not modified. The earlier [preflight](preflight-001.json) records a missing reconstructed numeric document before worker integration. Neither unsuccessful preparation attempt is a runtime result.

The nine combined stages reproduce explicit amendments, preserve/rebuild the original corpus, verify bounded rounding, check exact quantization examples, reproduce lifecycle/protocol supplements, check lifecycle/protocol expectations and recording-probe bindings, validate Agent schemas and verify documentation preservation. They do not execute OntoKin source evaluation, Agent stores, GLB export or browser playback.

## Independent review and remaining scope

The numeric worker and the independent Agent reviewer examined the bounded numeric derivation and exact rounding-cell implementation separately. The numeric worker also independently reviewed the stored-motion bound and direct binary32 conversion using a distinct integer exponent/significand algorithm. Review records bind the exact reviewed file hashes and keep finite numerical probes separate from mathematical derivation.

| Review | Scope and result |
| --- | --- |
| [Independent numeric review](../agent-review/numeric-peer-review/review.json) | No blocking finding in the bounded mathematical contract. Separate focused probes passed 1,204 rounding cases, 1,204 cell-membership cases, 16 axis/quadrant solutions, bounded inconclusive admission and cancellation. |
| [Independent quantization review](../numeric-review/quantization-peer-review.json) | No blocking finding after clarifying exact ideal slopes and matrix/vertex error. A separate integer algorithm agreed on 3,052 rational binary32 clock cases; 30 author checks passed. |
| [Combined contract and lifecycle review](../draft2-supplements/peer-review/combined-contract-review14-001.json) | No remaining blocker in the reviewed identities after the explicitly recorded LP05.09 clarification, conditional on fresh combined checks of the integrated files. |

The [LP05.09 clarification](../draft2-supplements/peer-review/lp05-candidate-identity-clarification14-001.json), recorded as D27, names current-source and historical-run acceptance separately. Later acceptance sets the current source projection's `candidate_only` to false; the immutable earlier candidate run retains true. The source corpus, lifecycle coordinates and all 42 request templates remain unchanged. Regenerated protocol and effective recording-probe bindings receive new hashes rather than inheriting an old passing result.

Actual source/destination uniform numerical error bounds, runtime shared-budget charging, interruption, atomic coordinate claims, actual protocol results and complete delivered artifacts remain implementation and acceptance obligations. A separately published adoption record must freeze the reviewed contract before runtime implementation begins. The full project GOAL remains open.
