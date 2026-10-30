# Next task: implement configurable language execution budgets

**C073 is an implementation task.** Start from the latest reviewed C072 main and [OK-LANG-007/0.1.0-proposal.1](../../language-design/OK-LANG-007-configurable-execution-budgets.md). Apply the owner's priority: language capability and more complex authored scenes, with efficiency improvements continuing alongside development.

## Required first increment

Implement one explicit experimental **source/CLI execution path** in which the entry `.ok` source requests operations and computation time, a trusted host policy authorizes those values, and one budget covers construction, evaluation, recording, export and independent supplied-byte verification. Keep omitted values at 100,000 operations and 30,000 ms. Exercise authorized 200,000/60,000, 400,000/75,000 and 400,000/80,000 requests. Do not change the original tests, fixtures or legacy maxima.

Use the proposed source `0.7` / `planar-reach-budget-0.1` boundary; publish a concrete versioned implementation/adoption decision with synchronized parser rules, examples, diagnostics and tests before enabling it. The design review is preparation for code, not a reason to restart broad feasibility investigation. If a narrow implementation detail requires a correction, document that correction and proceed with the bounded feature.

The separately reserved Agent/0.7 lifecycle can follow in the next increment. Until its actual create/edit/evaluate/export/cancel/retry cases run, leave that interface unavailable and say so. The first direct path must still produce and independently validate its recorded output under an explicit destination contract; metadata alone is insufficient.

## Implementation work

1. **Separate defaults from authorization.** Add a small explicit host-policy/resolved-budget model. Ordinary host policy retains the current defaults. The program and per-call fields request resources; neither supplies the host ceiling. Reject unknown fields, invalid/oversized literals, unapproved increases and conflicting caps. Keep the current legacy constructors and routes at their existing maxima.
2. **Parse the entry declaration safely.** Add the versioned header grammar and bounded prefix admission. Start provisional time/work accounting before header processing; carry its consumption and original monotonic start into execution. Only the entry source may declare a budget. Importers and modules never create new allowances. Keep prior lexer keywords, source hashes and original parser behavior intact.
3. **Make inherited capabilities explicit.** Audit exact-profile dispatch in linker, compiler, validator/evaluator, surfaces, impulses, forces, reach, scene building and output. The current profile lookup is not an inheritance mechanism. Bind each required capability explicitly; do not use numerical version comparisons, relabel 0.6 sources or change global legacy dispatch to make a new profile appear supported.
4. **Propagate one resolved context.** Thread it through all participating stages and adapters listed in [SOURCE-MAP](SOURCE-MAP.md). Audit the outer and nested checks, callback charging, per-admission guards and export fallback. Preserve cancellation/error order and valid-prefix behavior. Independent readback must use the actual remaining work rather than a new default meter or a value trusted from the artifact.
5. **Add reporting and an actual host entry.** Expose current defaults, permitted ceilings and the requested/effective/consumed limits through the new path. Establish how the trusted embedding API or operator-controlled launcher supplies policy. An agent-controlled flag is not proof of authorization. Preserve artifact/source identities and bounded failure diagnostics.
6. **Execute new conformance and inherited regression checks.** Use new test files for the C073-labelled [EB cases](../../language-design/execution-budgets-v0.1/conformance-plan.json); retain the original test files and expected outcomes. C074-labelled cases cover the deferred Agent lifecycle and are not C073 completion gates. Freeze one representative source workload and expected geometry/physics before its larger-budget acceptance run. Run a default-limit control and authorized higher-budget attempt with complete input and result identities.

## Evidence that completes the increment

- The actual source path parses and honors a requested budget only under sufficient host policy; declaration omission remains 100,000 / 30,000 even on a larger host.
- A higher-budget program completes through source execution, recorded export and independent readback. Its control fails specifically at the original operation allowance. No geometry, accuracy, numerical tolerance, fixture horizon or independent oracle is weakened.
- Exhaustion, cancellation, invalid authority, CLI failure atomicity/no uncommitted output, exact operation boundaries and nested accounting are exercised. Fake-clock tests cover deadline selection and expiry without waiting for 60–80 seconds. Accepted-revision rollback, Agent create/edit, saved-run service resumption and idempotent retries belong to the later Agent/0.7 increment.
- Earlier source/API/Agent/destination selections and legacy rejection of larger budgets remain unchanged. The relevant full inherited regression cohort and conformance driver run on the exact candidate; preserve every actual failure, timeout and recovery.
- A reviewed increment is integrated under [OK-ENG-009](../OK-ENG-009-development-integration-and-branch-lifecycle.md), with resulting-main checks and a concise handoff. Remaining Agent and complete-release obligations stay explicit.

Follow [AGENTS](../../../AGENTS.md) and the [local validation policy](../OK-ENG-006-local-validation-and-hosted-ci-policy.md). Reconcile fresh main, STATUS, branches, PRs and the explicit C072 scope closure before editing. Use one bounded branch from current main; do not resurrect an archived runtime candidate. Runtime changes normally require the full unittest cohort, `python3 -m ontokin conformance` and relevant local-driver roles. Export changes additionally need source-to-GLB, independent native/browser and visual checks applicable to the claims made. Do not dispatch hosted jobs or infer release acceptance from documentation checks.

## Scope boundaries

The original 28 recordings and their 100,000-operation/30,000-ms gate remain unchanged; the recorded result is still 24/28 failed. Larger-budget results form a separately identified cohort. A new success does not close the old gate. C035's hold, C057, rejected/unadopted proposals, remaining reach obligations and historical LFS migration remain recorded.

Keep existing operand-bit, cache, cursor, source/object/output, JSON/GLB, sample/key and local admission caps. Do not replace every occurrence of 100000 or 30000: several limits count different resources. The feature changes computation allowance, not `scene.duration`, physical equations or simulation accuracy.

Do not require C071's deferred native-decoder optimization investigation, a new cache proof, or a positive operation-saving premise before implementing these budgets. Optimization can be scheduled when a measured workload identifies a useful bottleneck. After the budget path works, choose the next concrete modeling, animation or simulation capability from GOAL and validate it on representative authored programs.
