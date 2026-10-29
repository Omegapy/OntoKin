# Proposed C065: shared nonzero offset arithmetic

**Status: proposed, not started or scheduled.** Resume from live main after reading C064's final release and reconciling current source, branches, ownership and outstanding work.

## Bounded target

Design one source-compiled, per-key expression graph for **nonzero planar attachment offsets** in the independent centered evaluator. Begin with `reach_reference_center._offset` and `evaluate`, the preparation-time orientation groups, and the existing `_coefficients` reuse. Examine whether multiple offsets under one actual orientation can share exact products or sums while preserving every original floor operation and resulting center/radius. Keep this a source-only feasibility task until it has a positive complete-request premise.

C064 established that deleting moving zero-offset identity nodes has no opportunity in original P11/L03. Their remaining moving paths contain real nonzero offsets or orientation changes. The retained plans and source tables identify those paths without new product attribution. An expression graph is a hypothesis for reducing actual arithmetic on them, not an accepted algorithm or a claim of an available saving.

## Required proof before implementation or requests

1. Identify an actual shared arithmetic expression in the pinned original source recipes. Existing coefficient caching and topological plan reuse must remain in the baseline; do not count their savings again.
2. Preserve the order of exact rational operations where it affects results, every `floor` location, independent source authority, current operand bounds, output identities and final source admission. Naively merging translations across floor operations is not equivalent.
3. Specify bounded temporary lifetimes. Do not introduce an uncounted second numerical cache or retain completed poses outside the existing cache/accounting rules. Count every new lookup, copy, type/limit/claim check and fallback. Direct temporary reuse is not automatically free.
4. Preserve recipe, parent and operand mutation checks and first-exception behavior around callbacks. C064's authority counterexample remains relevant even where the mathematical expression is equal.
5. Derive a positive net saving over the complete original request, including preparation, every key/phase, reseeds, fallbacks, cache effects and finalization. Completing the request within 100,000 operations is a separate stronger result that still needs original-request evidence.

If no candidate meets these requirements, close its exact failed premise with a counterexample or finite source bound. Do not instrument the same absent alias opportunity, rerun completed archive recovery, or weaken the original limits. A surviving design may proceed in a separately scoped implementation with meaningful positive, negative, mutation/callback and operation-accounting controls, followed by the applicable regression and original-request checks under OK-ENG-009.

Git LFS migration, hosted execution and branch-history cleanup are outside this runtime design task. All unresolved release requirements and the complete OntoKin goal remain in scope.
