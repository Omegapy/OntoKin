# Independent source and numerical review 01

**Outcome: changes required on the identified initial draft.** This review is independent of the root author of the source specification and grammar. It is a design review, not a torque runtime test. Root amendments already in progress are assessed separately; this record preserves the initial findings.

## Exact reviewed inputs

| Input | SHA-256 |
| --- | --- |
| SPECIFICATION.md | `2492bc98b7306264a02f3e61add649d73f0bc2a811bd825767c9f5a3c6e8416c` |
| ontokin-torque.ebnf | `01818c3ad1c6d1bb703a8ae8cb42c3ed88dc6ce40be1c37b1e7971424b0f26fc` |

The accompanying JSON records all C089 and inherited implementation inputs by exact SHA-256. Initial input copies are retained in `source-numeric-review-01-inputs/`.

## Blocking findings

### SRC-NUM-01 — SPECIFICATION.md §7 (initial draft)

The discrepancy inequality lacks the explicit stale-anchor smooth-law recurrence, initialization, and pre-split underflow error transport required for an independent implementation. The inequality alone does not identify which unrounded speed is compared at a newer error origin; alpha_c=0 is explicitly allowed without changing the legacy route.

**Required resolution:** Define the reference/error origin independently of the canonical anchor, use exact wc(e)=w_anchor+alpha_c*(e-tr), propagate full-vector Eomega and Etheta, initialize at latch from inherited error, and carry actual legacy/canonical anchor rounding without creating neutral anchors.

### SRC-NUM-02 — SPECIFICATION.md §9, runtime diagnostics sentence

The blanket requirement side="after" mislabels incoming-segment or phase-domain failures reached by before-side requests.

**Required resolution:** Restrict after-side diagnostics to staged boundary changes. Retain actual requested side and inherited requested-time/last-valid-prefix fields for incoming segment failures.

### SRC-NUM-03 — SPECIFICATION.md §§2 and 9, operand/type precedence

Source-order checks and child-evaluation-before-signature-checks permit incompatible outcomes for a wrong-dimension torque operand followed by a failing duration expression. The inherited force helper evaluates and type-checks each operand before proceeding.

**Required resolution:** Choose and state one exact sequence. The inherited sequence is structural/name checks, torque child/type, duration child/type, axis-name, positive duration. Freeze a dual-defect example.

## Independent mathematical witnesses

The calculations use Python standard-library exact fractions only. No OntoKin runtime is imported or executed.

1. **Underflow while the canonical route remains legacy.** Set canonical torque to the minimum binary64 subnormal, `2^-1074`, inherited inertia to `2`, initial speed to zero, and request time `2^537`. Canonical alpha rounds to zero (the exact quotient is the half-minimum-subnormal tie); reference alpha is `2^-1075`. Canonical phase remains zero, while reference phase is exactly `1/4` radian and reference speed is `2^-538`. The split-domain phase cap does not apply. A zero torque-free angular-error record is therefore unsound despite the required unchanged canonical legacy motion.

2. **A newer reference origin with an older canonical anchor.** Let canonical anchor time be zero, initial speed zero, canonical alpha `2`, and error-origin time `1/3`. Canonical smooth speed at that origin is `2/3`. Change only the reference acceleration to `1` and query at time `1`. Canonical phase is `1`; reference phase is `7/9`; required incremental discrepancy is `2/9`, exactly `|2-1|*(2/3)^2/2`. The error-origin recurrence must use the old canonical polynomial evaluated at the new origin. This is an exact recurrence witness; source-authored clocks need not expose its derived `1/3` clock.

3. **A before-side phase failure.** With zero initial speed and canonical alpha `1`, requesting time `2^11` gives exact phase `2^21`, above the `2^20` limit. A before-side request requires a before-side incoming-segment diagnostic. No boundary event has been staged at that requested time.

## Clarifications before freezing

- **SRC-NUM-N01:** Assign shadow-origin initialization/update/materialization explicitly to structural stages or an existing bounded stage, including cases with no canonical anchor change. State that empty torque projection headers on every .22 object are counted. Provide an explicit charge mapping and add the selected stage to cancellation/deadline/operation-cap cases; retain separately charged arithmetic.
- **SRC-NUM-N02:** Define Ephase as a bound on the unwrapped angular phase/work integral. A shortest quaternion angle by itself cannot bound work over complete turns. Define canonical/reference unwrapped increments and derive Ephase from the speed-error recurrence and actual phase rounding, retaining sums over reference intervals and separate impulse work.

## Requirements already satisfied

- Source/Agent/GLB/store binding scope and ordinary Angle dimension are explicit.
- Ordered completion, source events, force-before-torque aggregation and all-body atomic rollback satisfy the C089 staging obligation.
- Axis latch is independent of route; every impulse is checked; completion can trigger the first nonzero canonical alpha.
- Exact source clock addition and single-round canonical P/W graph are explicit; no gratuitous sample anchor or phase wrapping.
- The requested-only phase limit includes the exact interior vertex and preserves short prefixes.
- SharedExecutionBudget cancellation/operation/deadline order matches the inherited source.
- The additive EBNF matches the chosen torque statement and retains contextual keywords.

## Scope and limits

This review checks the full source specification and EBNF, the C089 decision/next-task/addendum, actual inherited force/reach anchor and source operand ordering, and original budget tick order. It does not certify an implementation, Agent schemas, supplied-byte decoder, complete input corpus or final publication. The exact-reference witnesses validate the identified mathematical risks; they are not claims that a candidate runtime already exhibits these defects.
