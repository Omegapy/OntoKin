# Independent reach Agent delivery evidence audit

This record defines the finite read-only evidence role implemented by
[audit_reach_agent_delivery.py](../../tools/audit_reach_agent_delivery.py).
The [adopted reach release contract](../language-design/planar-reach-v0.1/release-contract.md),
[Agent operations](../language-design/planar-reach-v0.1/agent-operations.md),
[42 frozen protocol steps](../language-design/planar-reach-v0.1/draft2-supplements/protocol-cases.json)
and [additional release probes](../language-design/planar-reach-v0.1/draft2-supplements/release-probes.json)
remain authoritative. This reader changes no runtime budget, expected result,
frozen input, acceptance limit, historical evidence or source behavior.

## Status and scope

The reader and thirteen adversarial component tests are prepared. No execution
or passing Agent workflow is claimed by this preparation record. Tests that use
small transport fixtures explicitly do not represent actual source evaluation,
valid GLB files or delivery acceptance. An executed audit must name its exact
source cut, producer directory, package versions, observed file identities and
result. Failed attempts must be retained separately.

The audit checks every actual LP01–LP05 request against its frozen template,
including the original **9 + 9 + 5 + 7 + 12 = 42** steps. It derives bindings from
the preceding recorded responses. It independently counts Q03's complete JSON
envelope and verifies the actual Q02 accepted-work cancellation and Q22 repair.
It additionally checks the ten required Agent deliveries, full-prefix failures,
retrieval isolation, idempotent retries, immutable histories, and the final
closed SQLite transaction inventory. Producer `passed`, `complete`, count and
closure flags cannot establish these results.

This role does not execute source or claim numerical-rate, Khronos, Three.js,
browser, compatibility, inherited-release or complete R01–R12/Q01–Q22
acceptance. Those remain distinct gates. Recorded GLBs do not provide live
destination action behavior. The [full product goal](../../GOAL.md) remains
broader than this finite release.

## Required retained inputs

The input is the complete output directory of the actual
`ontokin.reach-agent-delivery-workflow/0.1` producer, including:

- `producer-record.json` and all linked request/response, workflow-role,
  source-snapshot, retained-run, delivery-result and export-report files.
- `protocol-bindings.json`, the Q03 transparent-observation record and Q02
  planning/cancellation record.
- All ten saved artifact files and every actual artifact chunk response,
  including complete retained-artifact retrieval after failures and cancellation.
- `inputs-before.json` and `inputs-after.json`, identifying every tracked file
  and the exact clean Git commit/tree used for execution.
- The closed `service-store/planar-reach-program-agent.sqlite3` database. Its
  schema must remain `ontokin.planar-reach-program-agent-store/0.1`, all service
  sessions must be closed, and no nonempty WAL or journal may remain.

The reader verifies relative paths, rejects traversal and symlink members,
checks byte counts and SHA-256 values, and rechecks every consumed member after
auditing. It requires the producer and auditor to use the same identified clean
source cut. A later source cut requires fresh evidence or a separately defined
eligible-input equivalence audit; this tool does not infer equivalence from a
branch name or a reported passing result.

## Independent checks

| Area | Evidence required by the reader |
| --- | --- |
| Protocol and schemas | Actual echo-bound request/response pairs, unique ordered exchange roles and a closed offline registry of every exact schema-manifest member. The deliberately unsupported LP04.07 request must match its frozen negative template and receive the specified rejection. |
| Source and edits | Frozen manifest and complete bundle bytes; independently applied UTF-8 byte patches; unchanged library units; source/accepted-head distinction; all four untouched generated siblings and the two full source reads. |
| Runs and transactions | A canonical request ledger, exact retry receipts, changed-payload rejection, observed accepted-source transitions, retained run descriptors/versions and complete final database reconciliation. Extra or missing source, request, run or artifact rows fail. |
| LP01 recovery | The failed L04 run remains at `0.5 before`; reset creates a distinct run; the valid `0.25 after` prefix uses that reset run; a separate fresh delivery run supplies the tenth artifact while L04 remains accepted. |
| Q03 envelope boundary | All 128 complete named P24 action groups, with current/source/run context, no truncation, and exact complete-response entry count N derived by the auditor. Actual N succeeds; N−1 reaches the final guard after successful preparation; observed constructor/materializer counts remain below N. The tiny-budget negative may fail at its actual inherited resource guard and retains no new effects. |
| Q22 repair | Exact frozen Q22.01 expression patch on the existing LP01 project, producing the complete L02 bytes; Q22.02 uses L02 with the old LP01 failed run at `0.5 before` and rejects stale context; Q22.03 succeeds on the old L04 source/run with its unchanged failed-boundary history and the current L02 accepted head. |
| Actual delivery | P01, P11, P13, P20, P16, P17, L01, L02, L03 and L04. Every request explicitly records 1 fps, `helpers=false`, its required full/prefix endpoint and the adopted or tighter tolerances. Each successful response supplies the named GLB/0.6 contract and a distinct fresh run with the exact requested valid endpoint. |
| Retrieval | Actual base64 chunks decode strictly, stay in the same project/artifact/source provenance, cover every byte in contiguous order, report the correct next offset/EOF, and reproduce both the export receipt hash and saved artifact bytes. A boolean closure claim is insufficient. |
| Failure retention | Full P17 and L04 requests fail at their exact reach boundaries without artifacts; selected-branch N06 fails for the adopted reach-limit reason; earlier complete prefix artifacts are retrieved unchanged after failure. |
| Accepted-work cancellation | Actual P23 export reaches planning after boundary preflight. Nested status observes the export running; the actual cancel request sets the durable cancellation flag; the terminal response, status and retry agree and contain no new run/artifact. The complete prior P01 artifact and run remain unchanged. |

### JSON counting

The audit has its own iterative walker. Every value or container occurrence
counts once; repeated references count repeatedly, while cycles are rejected.
Object keys contribute encoded bytes but do not add logical entries. Strict
Unicode, finite numbers, the bounded integer representation, maximum 128 nested
containers, 100,000 logical entries and the complete compact UTF-8 4 MiB envelope
limit remain enforced. It does not import the production JSON measurement
function or copy the producer's value N.

Q03 intermediate and cancellation-stage observations still identify the exact
instrumented producer source. Their role is to retain observations made by
transparent wrappers around unchanged production guards, with actual service
messages and final store effects cross-checked independently. The audit does
not turn these records into an external execution-provider attestation.

### SQLite reconciliation

The reader opens the closed store with `mode=ro&immutable=1` and never imports
the production Agent/store API. It checks SQLite integrity, the isolated schema,
closed sessions, canonical request digests and payloads, final terminal
receipts, engine identities, cancellation flags, accepted heads and immutable
source bytes. It derives the final run/version inventory from the observed
operations and compares every retained run. It reads each stored artifact and
checks its actual bytes, report and source against the corresponding delivery.
The complete artifact set must contain exactly the ten successful deliveries;
the Q02 project must contain no committed run or artifact.

Rejecting an active WAL is necessary before immutable reading, because ignoring
uncheckpointed committed rows would defeat this transaction check. The original
producer store is retained unchanged; the audit only writes its fresh report
outside the producer directory and checkout.

## Execution

Install the exact verification-only package versions in
[force-agent-verification-requirements.txt](../../tools/force-agent-verification-requirements.txt).
They are not runtime dependencies. Unknown schema references are rejected
offline, and a missing or mismatched verification package fails the audit
explicitly.

Use the repository's granted exclusive runtime window and a clean common cut:

```bash
python3 -m unittest discover -s tests -p test_reach_agent_delivery_audit.py -v
python3 tools/audit_reach_agent_delivery.py /absolute/actual-agent-workflow --output /absolute/fresh-reach-agent-audit.json
```

Preserve the command, interpreter/platform, source/input hashes, stdout/stderr
and audit result. A successful report sets `agent_transport_audited=true` for
its explicitly listed finite scope and keeps `release_acceptance=false` and
`full_product_goal_completed=false`. Link that report and the unchanged actual
artifact identities into the separately executed
[native/browser destination workflow](reach-destination-checklist.md).
