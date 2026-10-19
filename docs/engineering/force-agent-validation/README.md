# Agent/0.5 checkpoint verification

This checkpoint connects the adopted finite-force source kernel to the versioned
agent interface. It does not implement GLB/0.5 or close F01–F12. The authoritative
scope and acceptance remain in [OK-AGENT-005](../OK-AGENT-005-finite-force-program-workflows.md)
and [OK-LANG-005](../../language-design/OK-LANG-005-finite-center-of-mass-force-intervals.md).

The [current local integration evidence](../force-agent-local-validation-2026-10-19/README.md)
retains the full passing run, earlier failures, storage investigation and resulting-main record.
Historical hosted evidence remains separate.

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
the inherited regression roles and the dedicated Agent/0.5 checks locally,
first prepare the pinned verification packages in an isolated environment:

```sh
python3 -m venv /tmp/ontokin-force-verification
. /tmp/ontokin-force-verification/bin/activate
python -m pip install -r tools/force-agent-verification-requirements.txt
python tools/check_local.py --force-agent
```

The optional `--force-agent` role checks every pinned package version, requires
the dedicated Agent cohort to execute without skips, records a fresh source
workflow and runs the independent auditor. Its logs, reports and source/message
artifacts stay in the runner's new evidence directory. The default core checks
and `--full` visual option retain their existing scopes; `--force-agent` can be
combined with `--full`. Missing verification packages are a failed prerequisite,
not a passed Agent checkpoint. To execute individual checks directly:

```sh
PYTHONPATH=.:tests python3 -m unittest discover -s tests -p 'test_force_agent*.py' -v
python3 -m unittest discover -s tests -v
python3 -m ontokin conformance --output /tmp/ontokin-core-conformance.json
python3 docs/maintenance/reorganization-2026-10-17/verify_reorganization.py
```

Direct unittest discovery may explicitly skip the schema-auditor class when
optional verification libraries are absent. Such a run cannot satisfy the
checkpoint's zero-skip gate. Under [OK-ENG-006](../OK-ENG-006-local-validation-and-hosted-ci-policy.md),
identified local execution is the integration default. The retained
`Force Agent checkpoint checks` workflow offers the same dedicated checks only
through manual dispatch with `enable_hosted_ci` explicitly true; that option
defaults to false. No push or pull-request trigger remains. Ordinary runtime
dependencies remain unchanged.

The original [CHECKPOINT.json](CHECKPOINT.json) preserves the earlier hosted
run and its then-pending actions. Its old instructions do not supersede the
adopted local policy or certify a later implementation. Fresh integration and
historical recovery records are maintained separately.

## Historical archive recovery

The [retained archive](historical-39246541254.tar.xz), [member manifest](historical-39246541254-manifest.json)
and [recovery report](historical-recovery.json) preserve evidence downloaded from
artifact `12183769150`, run `39246541254`. Its ZIP and complete Git source bundle
were verified against their recorded hashes and commit/tree identities. The
compact container holds 870 original immutable evidence files plus one newly
identified re-audit; it is not the unavailable 873-member conversation archive.
Mutable stores, Git history and publication transport payloads are excluded.

The retained original execution is 733 passing tests on Python 3.11.17, including
ten A01–A10 unittest cases. A separate standalone Agent conformance report is
absent from that artifact. The October 19 recovery re-audit ran on Python 3.12.14
and passed all 418 exchanges, 25 source snapshots, 334 predetermined samples and
411 force projections. It rechecks historical messages; it does not represent
a fresh service execution on the integration candidate.

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
