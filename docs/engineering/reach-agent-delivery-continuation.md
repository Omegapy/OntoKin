# Agent delivery continuation — 2026-10-21

This is a new development record for the adopted Agent/0.6 and GLB/0.6
implementation. It preserves the historical
[Agent handoff](../../tests/reach_agent_handoff.md) and
[release review](reach-release-review/README.md). It changes no frozen
contract, source case, expected result, operation limit or release requirement.
The complete reach release and full product goal remain open.

## Scope and code identity

The Agent worker owns branch
`work/reach06-agent-finish-20261021-0330-7of9`, starting from recovered checkpoint
`4292d51`. The integration worker owns the exporter, shared status and remote
publication. Runtime, SQLite, export and evidence executions use exclusive
windows; independent edits occur in separate worktrees.

The latest executed Agent cut in this record is
`9ecf966c351821fc542c3489df30da0938b7dde0`, a merge of the Agent changes and
integration cut `3b4d88e`. A subsequent exact-polynomial optimization is
committed as `2f0884a6f84dd370f943a73695234f6f4ac30860`; it has static checks
and independent proof review, but its runtime comparison is still pending at
this record's initial publication.

| Agent implementation change | Worker commit |
| --- | --- |
| Actual accepted P23 cancellation during recording planning | `f366c14cc91a704e50c0b4e22e0cf1d1a3f940e0` |
| Retain the checked requested prefix for the same exporter request | `ca1a7249aba522ca179104925143d6abcfebd23e` |
| Enable the implemented Agent/0.6 delivery binding | `9fb3042a3de8d41784cb611b1253554509e2bebf` |
| Reject foreign, mismatched or incomplete retained plans | `59718e6ad9a2d82370d459951561c8caf9cecce2` |
| Preserve original cancellation/resource exceptions through export | `55fb00eab6e9ab73310d402d63302765c8af13a5` |
| Thirteen-term source trig with the original error allowance | `9ecb1e9ea93092181405f09c8867adb82cdd6dca` |
| Omit exact-zero derivative-only composition work | `8776e66affd7d324e2aeb6cde6a45be0f8d5d8c4` |
| Exact internal Horner arithmetic and final grid projection | `2f0884a6f84dd370f943a73695234f6f4ac30860` |

Cherry-picked integration commits have their own identities. These worker
identities describe the implementation lineage; each executed record names
its actual integrated source cut separately.

## Requested-prefix delivery

`prepare_delivery` compiles once and evaluates the requested endpoint with
the existing request budget. The internal `ReachDeliveryCapture` observer
retains the actual before/after source observations, phase bounds and states
from that evaluation. It performs key/history preflight before retaining
each boundary. A successful complete prefix becomes a transient
`ReachPrefixPlan` on the compiler. A failed prefix never supplies a partial
plan to the exporter, and evaluating the requested prefix does not visit a
later known source failure.

The source observations and Agent projections are separate values. Agent
actions receive their inspection fields and eventual Agent context; raw
recording actions retain the source representation and null Agent identities.
The final nonsemantic endpoint is sampled on its real `before` and `after`
sides. The capture does not manufacture a `before` observation by relabeling
an `after` result.

The service passes the same model, numerical work object and retained plan
through the internal export arguments. The exporter requires the plan's model
and work identities to match the request, an origin of zero, the exact
requested endpoint and complete boundary/phase/state collections. A direct
export without a retained plan still performs its own prefix planning. The
supplied-byte validator receives no retained production plan and reconstructs
its own independent source expectations.

The implemented delivery binding was enabled only after the integrator had
observed a real P01 quarter-second export and independent supplied-byte check
within the original operation budget. Later changes still require fresh
checks; that enabling observation is not acceptance of all source artifacts
or the complete release.

## Cancellation, resource failure and atomic publication

The retained compiler's callback still belongs to the original Agent budget.
That layer wraps service cancellation and resource exceptions in `_Interrupt`
while crossing runtime helpers. Source evaluation already unwraps it; export
previously leaked the wrapper and returned `OKA-E-INTERNAL`. The service now
unwraps the same original exception around the real export call. It retains
the inherited transaction machinery for source acceptance, run publication,
artifact publication and final whole-response guards.

Executed tests now establish real cancellation during P23 recording planning
and during P01 geometry work. They use actual status/cancel operations and the
ordinary durable cancellation poll. The P23 test retains a prior artifact in
a separate project in the same store, accepts exact P23, cancels inside
bounded planning, and verifies no new run/artifact, exact retry/status,
unchanged accepted source, and unchanged earlier artifact bytes.

The retained-work budget test first delivers actual bytes, measures the
export-entry request count, then lowers a new request's operation limit so it
exhausts during retained recording work. It requires the real
`OKL-E-RESOURCE`, the exact consumed count, no new effects, and preservation of
the previously committed run/source/artifact. It does not inject a replacement
error or return a synthetic export result.

## Controlled-pose work reduction

The [numeric derivation](reach-numeric-kernel.md) proves the fixed source trig
and spatial composition changes. Target admission in `reach_numeric.py`, the
100,000-operation maximum, the 96-bit pose grid and all published error
allowances remain unchanged.

The thirteen-term sine/cosine polynomials use exact factorial coefficients.
The omitted terms are bounded uniformly on the admitted interval; the
production derivation and independent enclosure tests retain the original
`2^-80` trigonometric allowance. The subsequent exact-Horner change removes
intermediate grid projections, retains every prospective operand guard and
proves a maximum intermediate width of 2,582 bits. Its final two projections
give at most one half-grid unit of arithmetic error per function. Some private
approximation bits change within the same allowance, so implementation and
derivation hashes, source checks and regenerated artifacts must identify the
executed cut.

The zero-derivative shortcut applies only when all four input derivative
tuples are the immutable private `ZERO`. Both spatial derivative formulas are
then exactly zero before and after grid projection. Position, orientation,
error propagation, operand checks and cancellation retain their ordinary
paths. Other tuples still use the validating derivative helpers. Independent
static review confirmed the argument; executed tests compare exact pose bits
and errors, moving spatial derivatives, malformed zero-valued inputs and
interruption before publication. Recording samples still expose only poses;
complete source evaluation retains actual spatial rates.

## Executed observations

These are development observations, not a complete release audit. Raw logs,
commands, interpreter/platform details and input manifests are retained under
`reach-agent-checks/attempt-001` through `attempt-004` in the integrator's
workspace for archival publication. The later two attempts hash 672 relevant
runtime, test, source, schema and supporting inputs before and after execution;
both recorded stable bytes and clean Git identities. No older failure was
overwritten.

| Attempt and executed cut | Actual result |
| --- | --- |
| 001 — `59718e6ad9a2d82370d459951561c8caf9cecce2` | Prefix-plan tests 3/3 passed. Agent delivery 3/9 passed; six failures exposed budget exhaustion wrapped as an internal error. |
| 002 — `75f1836c6f35d0e1d6386aed511e9df812bbcee4` | Pose 16/16 and prefix-plan 3/3 passed. Agent delivery 2/11 passed; a new conservative quaternion-arc mismatch blocked several artifact prerequisites, while other requests reached 100,001 operations. Cancellation/resource exceptions had their correct service meaning. |
| 003 — `9ecf966c351821fc542c3489df30da0938b7dde0` | Pose 20/20, recording sampler 4/4 and prefix-plan 3/3 passed. Agent delivery 6/11 passed, including actual P01 bytes/retry, one compiler/work, both new real cancellation tests and retained-work resource rollback. Five requests remained blocked by operation exhaustion. |
| 003 — bounded recording probes | Both bounded-JSON tests and the warm algebra-cache rejection test passed. The recording test's quarter/full subcases both exposed a missing `work=work` argument to exact-clock serialization, before its final success assertions. |
| 004 — same executed cut | The five dependency-free Agent modules passed 29/29, including all 42 frozen LP01–LP05 protocol steps, Q03 actual whole-response N/N−1 and Q22 same-project edit/stale-run behavior. The schema-module preflight found missing verification packages and launched no schema tests; that module remains a separate pending check. |

All recorded executions above used CPython 3.12.14 on Linux. They do not
establish CPython 3.11 or 3.13 compatibility. The integration worker has since
prepared the six pinned verification-only dependencies for a fresh zero-skip
schema check; installed packages alone are not a passed verification role.

At attempt 003, the two original retained failures now passing are actual
artifact retrieval/retry and the one-compiler/work assertion. The five original
failures still blocked are the L02 post-export cancellation prerequisite,
L04 create/validate/export requested prefix, P24 final envelope prerequisite,
L04 fresh recovery export, and P17's valid two-second prefix. The P23 planning
and geometry cancellation probes and the retained-work resource probe are
additional tests. A failure creating a prerequisite artifact does not establish
failure or success of the later transaction assertion.

## Contract review and remaining gates

The worker reconciled the relevant Agent contracts with the existing
[95-document review](reach-release-review/documentation-review.md), including
OK-AGENT-001 through OK-AGENT-005, the adopted reach
[Agent operations](../language-design/planar-reach-v0.1/agent-operations.md),
[adoption](../language-design/planar-reach-v0.1/ADOPTION.md),
[release contract](../language-design/planar-reach-v0.1/release-contract.md),
[Agent schema review](../language-design/planar-reach-v0.1/agent-review/README.md)
and its numeric peer review. This continuation is a new document outside that
historical 95-document inventory. The prior handoff's syntax-only and disabled
adapter statements remain statements about its earlier checkpoint.

Material obligations remain distinct:

- Valid requested prefixes require actual delivered bytes; passing prefix
  evaluation alone does not close the five retained delivery failures.
- Q03 uses exact P24, all 128 action groups at `1.5 after`, no cursor and the
  complete published response at N/N−1. Full P24 recording is not substituted
  for or required by that bounded inspection obligation.
- Q02 requires actual accepted P23 cancellation during bounded recording;
  cancellation after all work is a separate transaction probe.
- Q22 uses one project for exact L04-to-L02 repair and stale-run rejection.
  The separate tenth L04 recovery artifact still requires real retrieval.
- The complete release requires all 28 mandatory source artifacts, nine
  ordinary Agent-retrieved artifacts plus the separate L04 recovery artifact,
  independent supplied-byte/rate checks, actual native/browser evidence,
  compatibility, inherited roles and the complete release audit. Unit tests
  and implementation notes do not replace those roles.
- The full product domains and measured direct-tool authoring advantage in
  [GOAL](../../GOAL.md) remain outside this finite completion claim.

The immediate next action is to finish the exporter budget work, rerun the
actual delivery cohort and exact-polynomial checks with stable inputs, execute
the pinned schema module without skips, then proceed through the complete
release roles. Integration and shared STATUS publication belong to the
integration worker.
