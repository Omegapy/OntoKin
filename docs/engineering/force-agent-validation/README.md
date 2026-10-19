# Agent/0.5 checkpoint verification

This checkpoint connects the adopted finite-force source kernel to the versioned
agent interface. It does not implement GLB/0.5 or close F01–F12. The authoritative
scope and acceptance remain in [OK-AGENT-005](../OK-AGENT-005-finite-force-program-workflows.md)
and [OK-LANG-005](../../language-design/OK-LANG-005-finite-center-of-mass-force-intervals.md).

## Source and protocol evidence

`tools/build_force_agent_demo.py` records real service operations. The current
fixed workflow contains 418 exchanges, 25 immutable source snapshots and 334
predetermined state samples across 22 positive source programs. The original
acceptance bytes and their explicitly adopted additive errata remain unchanged.
A recorder count is not an acceptance result; the independent audit must pass.

`tools/verify_force_agent_workflow.py` uses only bundle identity code from the
implementation. It does not call the compiler, evaluator or exporter. It checks
closed-registry JSON Schemas, exact source bytes and writable patch authority,
canonical start/completion clocks, complete active/recent force histories,
fixed numerical states, source manifests, initial and last-valid snapshots,
unique run identities, request-ID retries, frame meaning, cursor linkage and
unchanged source siblings. Unknown schema references cannot cause a network fetch.

Adversarial tests change retained messages and recompute their hashes. This
checks more than stale checksums. Examples alter position, acceleration, source
spans, statement indices, force completion, authority spans, request/run IDs,
source manifests and immutable snapshots. Separate actual-service tests cancel
requests after computation and immediately before commit, then verify that
accepted source, runs and artifacts were not changed. Subprocess tests exercise
selected-protocol JSONL errors, store failures and unavailable delivery.

## Reproduction

Use the [example commands](../../../examples/force-agent/README.md). To execute
all force agent tests with the verification packages installed:

```sh
PYTHONPATH=.:tests python3 -m unittest discover -s tests -p 'test_force_agent*.py' -v
python3 -m unittest discover -s tests -v
python3 -m ontokin conformance --output /tmp/ontokin-core-conformance.json
python3 docs/maintenance/reorganization-2026-10-17/verify_reorganization.py
```

The standard-library regression matrix may explicitly skip the schema-auditor
class when optional verification libraries are absent. The dedicated
`Force Agent checkpoint checks` workflow installs the pinned verification-only
packages and requires all discovered agent tests to execute with zero skips.
It retains the package-download provenance, test results, exact checked-out
revision, actual source/message recording and independent audit as one GitHub
Actions artifact. Ordinary runtime dependencies remain unchanged.

## Reproduced audit corrections

The continuation from `db50d4641264cdf69c01fbd7c73b2e39f15b3f45` demonstrated five
rehashed evidence counterexamples accepted by the older reader: a false last
position, incorrect initial force history, reused run identity, substituted
inspection frame and changed source manifest. The corrected reader binds those
values to actual request source and predetermined states. It also checks the
request-ID receipt ledger and object/frame agreement in complete snapshots.
These were evidence-audit defects, not a demonstrated force-integrator defect.
No physical expectation, source fixture or numerical tolerance was changed.

## Limits

This small source corpus is not evidence of arbitrary rigid-body accuracy,
contacts, continuous torque, locomotion or other full-product domains. The
retained mesh pages show source/repair continuity; they do not independently
certify a new delivery target. Complete force-release acceptance still needs
actual GLB/0.5 construction, decoded geometry/PBR/intermediate-motion checks,
reviewed browser captures, current inherited gates and durable F01–F12 evidence.
