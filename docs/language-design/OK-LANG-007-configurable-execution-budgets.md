# Configurable execution budgets

**Identity:** OK-LANG-007/0.1.0-proposal.1

**Date:** October 29, 2026

**State:** Selected design for the next implementation task. The owner has adopted the product priority; this document does not make new syntax or runtime support available. C072 changes documentation only.

## 1. Purpose and authority

OntoKin programs should be able to request enough computational work for their 3D scenes, animations and simulations. The execution environment decides how much work it authorizes. The ordinary defaults remain **100,000 operations and 30,000 milliseconds**. A deployment can authorize a larger ceiling, such as 400,000 operations and 80,000 milliseconds, without increasing the budget of programs that omit a request.

This implements the owner's October 29 direction to prioritize language capability and increasingly complex authored scenes. Efficiency work remains useful, but a positive optimization result or completion of the existing 100,000-operation reach gate is not a prerequisite for implementing this separately versioned capability. [GOAL](../../GOAL.md) remains the full product objective.

The existing source, Agent and destination contracts retain their meanings. In particular, [the adopted reach contract](planar-reach-v0.1/ADOPTION.md) and its original acceptance inputs keep their original limits. The new feature does not retroactively pass a failed request.

## 2. Separate three values

For each configurable resource, distinguish:

| Value | Authority and meaning |
| --- | --- |
| Default `D` | The language binding supplies 100,000 operations or 30,000 ms when the entry source omits that field. |
| Source request `S` | The entry `.ok` program requests a positive finite limit; an omitted field uses `D`. |
| Host ceiling `H` | The trusted launcher or service supplies an independently configured maximum for this execution environment. Ordinary policy sets `H = D`. |

An optional per-call cap `R` is a caller's explicit request to spend less than the source requests. It is not permission to spend more. For each field, require `R <= S` when `R` is supplied; otherwise report a request conflict. Set the effective limit `E` to `R` when supplied and to `S` otherwise. Require `E <= H`. Reject an excessive request before body evaluation; do not silently clamp, increase, retry or replenish it.

Host configuration uses checked positive finite integer values within the implementation's documented representable range. There is no unlimited mode or special zero, negative, null or infinity value. The initial conformance policy includes 400,000 operations and 80,000 ms. Those values are an authorized test configuration, not a new universal language maximum. Each deployment chooses and advertises its own finite ceilings; support claims remain bounded by tested workloads and the other resource limits.

| Entry request | Per-call cap | Host ceiling | Required result |
| --- | --- | --- | --- |
| Omitted | Omitted | 400,000 / 80,000 ms | Use 100,000 / 30,000 ms. |
| 200,000 / 60,000 ms | Omitted | 400,000 / 80,000 ms | Accept exactly 200,000 / 60,000 ms. |
| 400,000 / 75,000 ms | Omitted | 400,000 / 80,000 ms | Accept exactly 400,000 / 75,000 ms. |
| 400,000 / 80,000 ms | Omitted | 100,000 / 30,000 ms | Reject as exceeding host authority. |
| 400,000 / 80,000 ms | 200,000 / 60,000 ms | 200,000 / 60,000 ms | Accept the explicit smaller per-call limits. |
| Omitted | 200,000 operations | 400,000 / 80,000 ms | Reject: the caller cap cannot enlarge the default source request. |
| Omitted | Omitted | 50,000 / 10,000 ms | Reject; the caller or source must explicitly request smaller limits. |

Fields resolve independently. A larger operation allowance does not imply a longer deadline or more output, memory, objects or concurrent requests.

## 3. Proposed source declaration and version boundary

Reserve source version `0.7` and profile `planar-reach-budget-0.1` for the first experimental binding. It inherits the explicitly enumerated modeling, force, impulse and planar-reach semantics of the current development profile and adds this execution contract. It is not a claim that the complete planar-reach release has passed.

The following is **proposed syntax, not executable on C072**:

```ontokin
ontokin "0.7";
module Workshop @"workshop";
profile "planar-reach-budget-0.1";

execution {
    max_operations = 400000;
    max_elapsed = 80[s];
}

// Existing imports, definitions and scene follow here
```

The optional block appears in the entry module's header after any `requires` declarations and before imports, definitions or a scene. There is at most one block. It contains one or both fields, each at most once, in either order. An empty block, unknown field, misplaced block or duplicate field is an error. [The proposed grammar](execution-budgets-v0.1/grammar.ebnf) makes this placement explicit.

`max_operations` accepts a decimal positive integer literal. `max_elapsed` accepts a positive decimal literal in seconds using `[s]`, converted exactly to whole milliseconds. Thus `60[s]`, `75[s]`, `80[s]` and `0.5[s]` mean 60,000, 75,000, 80,000 and 500 ms. A value below 1 ms or not representable as a whole number of milliseconds is invalid. Do not round a requested deadline. These header fields admit no arithmetic expressions, names, function calls, exponent notation or runtime-dependent values. Literal length and conversion work must be bounded before allocating an arbitrary-size integer.

Only the immutable bundle entry source may request an execution budget. Imported modules cannot declare one, even a smaller one. They inherit the caller's accepted context. The declaration contributes to the ordinary source/program revision hash. Host policy and per-call caps are execution context and do not change the source hash.

Recognize `execution` contextually in the new header parser. Do not add a reserved word to legacy lexers or accept the block under old headers. Do not rewrite a user's 0.6 header automatically. Explicit source, Agent and destination dispatch must preserve old bindings. In particular, the current one-entry-per-profile lookup and exact profile comparisons require an explicit capability mapping; adding a profile string alone must not skip physical semantics.

Reserve `ontokin.agent/0.7` and `ontokin.glb/0.7` as distinct extension bindings. They remain unavailable until their actual paths and contracts are implemented and tested. Recorded output inherits the existing geometry and motion obligations; any new metadata is descriptive and cannot grant resource authority. Earlier GLB readers must reject unsupported contracts rather than silently accept a different source meaning.

## 4. Execution time and modeled time

`max_elapsed` limits wall-clock computation time for one execution attempt. It does not set `scene.duration`, the simulation horizon, export end time or playback duration. Existing source validates `scene.duration` separately as positive modeled time and constrains export end to that duration. There is no 30-second scene-duration restriction in those checks.

For example, a program can describe a 10-second animation while requesting 80 seconds to compute and validate it. A program can also describe a longer animation without needing that much computation time. Both still have to satisfy the existing sampling, output-size and numerical constraints. This feature changes execution budgets only.

## 5. Admission and the trusted host boundary

Host ceilings enter through a launcher/service policy configured by the execution environment. Source declarations, Agent request JSON, imported libraries, GLB metadata and fields such as `trusted: true` cannot create or enlarge that policy. A CLI flag is an administrative control only when the host actually controls its use; an untrusted caller's command arguments are not an authorization boundary.

The default policy authorizes only the existing defaults. An operator can explicitly configure, for example, ceilings of 400,000 operations and 80,000 ms. The program still chooses its requested amount. Reject invalid policy at startup. Freeze the policy identity and effective limits for each admitted execution. A later policy change applies to new admissions; explicit host cancellation handles revocation of running work.

Authority here concerns an untrusted OntoKin program inside an environment-controlled interpreter. An arbitrary Python caller with permission to mutate the interpreter or its process is outside that boundary. This feature does not establish a Python sandbox, adopt C068's proposed native boundary, or require the rejected C069 mutable-list receipt.

### Bounded bootstrap

Transport byte/depth guards remain the first ingress protection. When the worker begins source admission, record its monotonic start time and create a provisional shared work ledger. Bound this initial phase by the minimum of the ordinary defaults, current host ceilings and already known explicit per-call caps. Queue waiting is separate from execution time.

Read only the bounded entry header needed to resolve the literal declaration, using a grammar-aware prefix parser. Do not evaluate an expression, import a module, compile the body, or use an unbounded whole-source regular expression to discover authority. Long comments, strings containing fake declarations and oversized literal tokens must stay bounded. Normal source byte/token limits remain in force.

After resolving the declaration and host policy, promote the ledger once to `E`, retaining every consumed operation and the original start time. If consumed work is above `E` or elapsed time is above its accepted limit, fail immediately. Equality alone is not an excess; the next operation beyond `E` fails. Do not start a second clock, refund header work or recreate a full allowance. Any header reparsing is real work and must be charged. The implementation must specify and test header charges for the new profile without changing legacy operation counts.

## 6. One request, one allowance

The accepted context covers header admission, linking, construction, numerical admission, simulation, recording, export and independent supplied-byte verification performed within that top-level execution attempt. Internal stages, recursive calls, frames, imported modules and helper workers share the same remaining allowance and original deadline. A stage may add a stricter local bound; it cannot replace the request ledger with a new full budget.

Keep the current semantic operation units and precharge/callback rules. A numerical subcounter can report categories, but it does not grant another allowance. Preserve interruption identity, cancellation ordering, failure atomicity, valid-prefix rules and source ownership. The implementation must inventory existing callback chains so that shared work is neither omitted nor accidentally charged twice at an adapter boundary.

If a caller starts a genuinely separate validation request, the host authorizes a new request and reports it separately. It must not call split requests a single-budget source-to-export execution. A fresh top-level evaluate/resume request similarly obtains fresh authorization; an internal resume cannot reset accounting. Unchanged idempotent retries return their original receipts and do not rerun; changing a budget under the same request identity is a payload conflict. No hidden retry with a larger allowance is permitted.

Current time checks are cooperative: they run at defined work checkpoints. A host that needs a strict process kill deadline must enforce it outside the interpreter and retain honest cancelled/unknown-outcome semantics. Do not claim that a Python clock check can preempt an arbitrary blocking callback. Process isolation is an optional host mechanism, not a new optimization prerequisite.

The host remains responsible for aggregate concurrency, total work across requests and process memory. Per-request limits do not promise a lifetime quota or reserve a number of CPU instructions. Other existing object, source, result, JSON, GLB, numeric-operand, cache, cursor, precision and local admission limits remain in force.

## 7. Source lifecycle, diagnostics and reporting

On candidate creation or edit, resolve the candidate entry source's declaration before its execution; the previously accepted source cannot authorize the candidate. Rejection preserves the accepted revision. A stored program or previous receipt never transfers authorization to another environment. Reevaluate host policy when a new worker attempt admits the saved program.

Discovery should separately expose defaults, permitted ceiling values, supported budget fields and implementation status. Metadata-only inspection may describe a source request without claiming that it has been authorized. Every new-profile execution receipt should identify source revision, implementation/binding, policy identity, source request, explicit per-call caps, authorized ceilings, effective limits, consumed operations, elapsed time and terminal status. Admission failures can occur before those values resolve: report the admission stage and explicit null/unavailable fields rather than inventing an accepted budget. Bound all receipts under the existing output guards; a tiny requested success-output budget must not prevent a bounded failure diagnostic.

Use the existing resource diagnostic family with proposed stable `budget_reason` values:

| Reason | Meaning |
| --- | --- |
| `invalid_declaration` | Invalid, duplicate, misplaced or imported declaration/value. |
| `request_cap_exceeds_source` | A per-call cap attempts to raise the source request. |
| `host_ceiling_exceeded` | The explicit effective request exceeds current authorization. |
| `operation_budget_exhausted` | The next charged operation exceeds the accepted limit. |
| `execution_deadline_exceeded` | A checkpoint observes elapsed time above the accepted limit. |

Diagnostics distinguish invalid requests, refused authorization, exhausted resources and cancellation. Include the relevant requested/effective/ceiling value and source location when applicable, without changing legacy diagnostic codes or payloads. A timeout or exhaustion cannot publish an uncommitted artifact or mark an invalid later state valid.

An artifact's recorded budget explains how it was produced. It does not authorize the reader or certify geometry, motion or numerical accuracy. The independent reader must establish supplied-byte claims under its actual authorized context.

## 8. Compatibility and acceptance

Keep every existing test and fixture byte, old default, old API/protocol selection, numerical tolerance and independent oracle unchanged. Existing explicit request reductions retain their old behavior. The original 28-recording gate remains 24/28 failed at C071; higher-budget results are a separate cohort with explicit source and policy identities.

The [conformance plan](execution-budgets-v0.1/conformance-plan.json) defines new positive, boundary, negative, composition and lifecycle cases. It is a plan, not executed evidence. Required cases include all three example timeouts, omitted declarations under a larger host ceiling, rejected unapproved increases, explicit reductions, invalid literal types, exact boundary exhaustion, shared nested accounting, bounded bootstrap, deterministic fake-clock checks and preservation of cancellation/rollback.

At least one new representative workload must fail because of the old operation budget and pass under an explicitly authorized larger budget through source execution, recorded export and independent readback. Freeze that workload and its expected physical/geometry claims before acceptance execution. Record both attempts, retain original fixtures, and do not weaken equations or tolerances to obtain a pass. Larger budgets do not establish faster execution or make unsupported physical features available.

## 9. Concrete implementation sequence

The [next task](../engineering/language-execution-budgets-2026-10-29-c072/NEXT-TASK.md) starts implementation of the explicit source/CLI path, with host policy, bounded header admission, shared ledger and export/readback plumbing. Agent/0.7 lifecycle and full new-feature acceptance follow as identified increments. Each increment must preserve inherited regressions and honestly state what is callable. No new source-only arithmetic investigation is required before starting this feature.

The [source map](../engineering/language-execution-budgets-2026-10-29-c072/SOURCE-MAP.md) identifies actual fixed-limit boundaries and exact-profile dispatch points. C072 makes no runtime change, imports no product module, and claims no executed higher-budget request or complete release.
