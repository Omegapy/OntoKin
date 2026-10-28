# Reach source repair and complete documentation review

**All 45 frozen source-corpus cases now pass, including the 32-arm P23 case at
the unchanged 100,000-operation request limit. The complete local regression
still fails on seven actual reach-delivery methods.** This is a development
checkpoint for [PR #25](https://github.com/Omegapy/OntoKin/pull/25), with scope
and coordination in [issue #24](https://github.com/Omegapy/OntoKin/issues/24).
The finite reach release and the complete product goal remain open.

The [machine-readable checkpoint](checkpoint.json),
[full documentation ledger](documentation-review.md),
[remote branch snapshot](branches-before-publication.json),
[execution archive](execution-001.tar.xz) and
[archive manifest](execution-001.json) retain the exact boundaries of these claims.

## What changed and why

P23 previously exhausted its shared request budget during admission, repeated
pose construction, terminal latching or final projection. The corrections reuse
bounded pure numerical results with matching canonical inputs and proof methods:
rotation products, rotated vectors, hinge values, relative-composition
arithmetic and exposed vector values. They avoid filling the 256-entry cache
with one-use world translations and oversized dependency slots. The generic
vector helper is no longer called twice when composition has already established
the same private-vector preconditions.

Natural reach completion may reuse incoming endpoint position/orientation for
its terminal measurement. The incoming graph is **not** reused as the outgoing
kinematic graph: running endpoint rates can be nonzero, whereas completed held
rates become zero. Final staged validation rebuilds the outgoing graph. Temporary
terminal state is cleared on success, failure and cancellation, and excluded
mutations invalidate eligibility. Caller-specific error bounds, input-width
guards, exact arithmetic, grid rounding, cancellation and fresh logical output
work remain checked. The [pose reuse note](../reach-pose-operation-reuse.md)
documents the mechanism and its restrictions.

The source-assertion branch is included with its stronger checks for adopted
lifecycle, joint ownership, target projection, failure context and free
orientation fields. Frozen expected inputs and acceptance limits were preserved.
Two independent verification components are also included:

- [World-rate comparison and proposed criterion](../reach-rate-acceptance.md):
  exact source clock/side, independent interval values, derived Euclidean
  allowances and explicit proved/contradicted/unresolved outcomes. The criterion
  remains a proposal; this checkpoint does not adopt it.
- [Native GLB verification component](../reach-native-verification.md): actual
  supplied bytes, source identities, resource checks, geometry/PBR and controlled
  playback comparisons. Its helper probes are exercised; a successful actual
  reach GLB and the complete native/browser roles remain required.

Neither the reserved `ontokin/reach_export.py` nor
`ontokin/reach_reference.py` changed in this branch. No workflow, frozen language
fixture or shared budget changed.

## Actual executions

The source and focused runs used CPython 3.12.14 on Linux. The official local
plan used a CPython 3.12.14 environment with all six exact verification-package
pins. Every run below has its own source identity and receipt; results are not
combined into a fictional all-green release.

| Receipt inside the archive | Actual result | Source commit |
| --- | --- | --- |
| `current-continuation/pose-009/` | 71/71 focused numeric, pose, cache, terminal and rate checks passed; zero skips or expected failures. | `f3dd5432b3eb1e26374b267dd5636feee2bde193` |
| `current-continuation/p23-010/` | P23 passed all of its asserted sample requests at the original limit. | `f3dd5432b3eb1e26374b267dd5636feee2bde193` |
| `current-continuation/source-004/` | 45/45 original and supplementary source cases passed. All 1,170 tracked inputs were available and stable. | `f3dd5432b3eb1e26374b267dd5636feee2bde193` |
| `current-continuation/export-003/` | P01 prefix `1/4` and full `3` seconds, 2 fps, helpers false: both failed at shared operation 100,001; no artifact. | `f3dd5432b3eb1e26374b267dd5636feee2bde193` |
| `current-continuation/native-003/` | All nine named native helper/resource probes passed on Node 24.19.0. This does not establish the required Node 22 or actual-GLB roles. | `cc33240b12b6b343fbaae776e497807990a4cd4e` |
| `current-continuation/local-001/` | All eleven planned stages executed: ten passed; the complete regression stage failed on seven reach-delivery methods. All 1,173 eligible inputs and Git identities stayed stable. | `da04b5d733872664cab3e15f9a71cba5eb5276fc` |

The only changes between the successful source-corpus implementation and the
full local run were two additional edge-case tests and the branch/documentation
records. Both new cancellation/domain tests passed within the full suite, as
did P23. Production inputs were unchanged between those cuts.

### Complete local plan

The literal command was:

```bash
PYTHONDONTWRITEBYTECODE=1 /tmp/ontokin-reach14-verification/bin/python \
  tools/check_local.py --force-agent \
  --output-dir /workspace/scratch/75d7831053fa/reach-checks/local-001 \
  --timeout 900
```

The driver preserved actual commit `da04b5d733872664cab3e15f9a71cba5eb5276fc`
and tree `d706b8c8a1682dae9780309cec7620b167e1a7bd` in its isolated workspace.
It executed from 2026-10-21T00:27:47Z to 00:37:06Z. Its overall result is
**failed**, with exit code 1.

| Stage | Observed result |
| --- | --- |
| Pinned verification dependencies | Passed all six exact pins and import readiness. |
| Complete Python suite | 1,110 executed: 1,103 passed, seven failed, zero errors, skips or expected failures. |
| Original source conformance | 43/43 cases and 694 assertions passed. |
| Original Agent conformance | A01–A10 passed. |
| Construction check | Command passed; C20's external visual gate remains pending in this selected run. |
| Surface check | Command passed with 11 external-evidence rows still pending. |
| Impulse check | Command passed with four external-evidence rows still pending. |
| Documentation preservation/navigation | Passed. |
| Dedicated Agent/0.5 cohort | 106/106 passed, zero skips or expected failures. |
| Fresh Agent/0.5 workflow | Passed. |
| Independent Agent/0.5 workflow audit | Passed; it does not claim full force-release or destination certification. |

The seven failures are exactly the delivery methods listed in
`checkpoint.json`: actual retrieval/retry, L04 recovery, requested-prefix
create/validate/export, shared-work delivery, P17/Q08 prefix recovery,
cancellation after delivery, and final delivery-envelope rollback. The raw
responses retain unavailable-adapter and future-failure/prefix diagnostics.
They have not been skipped, relabeled expected failures or repaired by changing
assertions. The separate direct exporter probe establishes the continuing
operation-budget failure even without the Agent adapter.

Passing the 45 source assertions still leaves `source_execution` pending.
The report records 724 derived world-rate measurements, of which 673 match the
frozen values exactly. Their remaining acceptance criterion is not inferred
from the preparation-only libm tolerance. Independent complete geometry/PBR,
all Agent transactions and the other release roles retain separate obligations.

## Documentation and branch findings

The [reading ledger](documentation-review.md) covers all **95 narrative
documents** at the fixed implementation cut and all **15 foundational diagram
assets**, with exact hashes, reviewer attribution and reading modes. It preserves
the earlier 90-document structural review and explains the added full-body
coverage. The newly authored ledger and this checkpoint are outside that fixed
95-document inventory. Reading documentation does not newly certify all
historical execution JSON, archives or destination artifacts.

Current AGENTS, GOAL, STATUS, explicit adoption records and versioned contracts
govern support claims. Historical proposal labels, preparation evidence and
archived STATUS snapshots retain their original meaning. The adopted planar
reach action contributes to the larger manipulation goal; grasp, move, release
and the other product domains still require their own implemented evidence.
No measured direct-tool authoring advantage has been established.

The remote snapshot observed **52 branches** and four existing draft PRs before
this publication. PR #25 is the fifth draft, stacked on #23; #23 targets #22,
which targets #21. PR #20 remains a separate delivery draft. The observed main
was `edf2412e5ea993b369e0204194921e4976504811`, with its prior integration lease
released. Source checkpoint `b46bbd2591f8dc5ed0393d566cfb38f2cd3e75b6` was
published by an expected-head, nonforce update and read back successfully. Its
tree exactly matches local `de39689993a143bdad31c993c9878198bb9ab16c`:
`7f286cb9f594be96a6537ed85bb209326540757e`.

API publication commits are recorded separately from the original local
development commits. Main runtime integration has not occurred. The latest
observed hosted runs were historical October 19 failures; no hosted execution
was dispatched or retried for this work. A branch or unchanged head does not
establish whether another worker is executing.

## Evidence preservation and recovery

`execution-001.tar.xz` contains **1,109 members**: 1,107 exact receipt/history
files and two packaging records. It includes 40 indexed development attempts
across this continuation and the previous one. Earlier P23 failures, the
internal cache-test failure, the native wrapper failure and malformed-fixture
failure, both export failures, the old missing-blob preflight, and the complete
current failed regression are retained separately from their later outcomes.
The original previous-continuation files were read without modification.

The archive is 920,596 bytes, SHA-256:

```text
a8d934921450ee73b7168a0d6ae2b05f2aa4ce0f4426d0c1fcc741b27df8026e
```

Every member was verified by SHA-256 after decompression. The intermediate ZIP
also passed every CRC and member-hash check. The compact archive preserves its
manifest and the conversion script. Copied validation workspaces and bytecode
caches are excluded; before/after source inventories, literal commands, logs,
generated workflow artifacts and source history are retained. Archive headers
use a fixed packaging date; actual execution clocks remain in the reports.

After checking the archive hash, extract it into a new directory. The original
local source history is at:

```text
current-continuation/source-history-001/local-source-history.bundle
```

This verified incremental Git bundle requires commit
`767a1d7e88a946d4936122fe21d5abf769488f81`. It retains the root development
history through `da04b5d`, the rate/documentation worker through `4e2497a`, and
the native worker through `8406a1f`. `git bundle verify` reports the prerequisite
and all three refs. Fetch a recovered ref into a newly named branch; preserve
existing working branches and unpublished changes. Archive integrity does not
change any recorded execution outcome.

## Next unmet gates

1. Reconcile the existing recording-budget worker's changes and complete actual
   GLB/0.6 recording within the adopted shared budget. Its reserved branch is
   `work/reach06-recording-budget-20261020-2044-7of9`.
2. Reconcile the independent impulse-history allowance work on
   `work/reach06-reference-impulses-20261020-2105-7of9`.
3. Complete actual Agent/0.6 delivery and valid requested-prefix behavior, then
   pass all seven delivery methods, the complete 42-step protocol and the
   required Q03, Q22 and L04 transactions without exclusions.
4. Resolve the explicit derived-world-rate criterion and execute the actual
   independent comparisons; complete the literal R01–R12/Q01–Q22 mapping and
   independent release auditor.
5. Produce all required source and retrieved Agent artifacts, complete native
   and browser checks and actual visual review, run the three Python versions
   and mandatory inherited roles, then perform serialized main integration and
   fresh resulting-main verification under a new verified lease.

The [complete release contract](../../language-design/planar-reach-v0.1/release-contract.md)
continues to govern exact selections, bounds and evidence. All broader
[GOAL](../../../GOAL.md) domains and the empirical authoring comparison remain
visible and open.
