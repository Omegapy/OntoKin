# Bounded pure keyed filtering inputs

These independently authored inputs define C083 before runtime implementation.
They select source `0.16` / `keyed-filter-0.1`, explicit Agent/0.16 and recorded
GLB/0.16. Bundle/files remain 0.2. The corpus contains 141 source cases:
75 intended successes and 66 intended refusals. These are requirements, not
executed C083 results.

```ontokin
filter_keyed<Length>(widths, (key, value) -> value >= self.minimum_width)
```

The input is evaluated once. Its admitted keys are visited in canonical ASCII
order, including entries ultimately dropped. A strict Boolean predicate selects
the original typed values without changing their keys. Static checking remains
required for empty input, and actual dependencies and forbidden construction
taints remain even when every entry is dropped.

`expected.json` binds exact program/source identities, independently calculated
membership and values, refusal codes, original UTF-8 source locations, public
provenance obligations and explicit .15 controls. `DERIVATION.json` identifies
inherited constructor literals, exact PNG bytes and ordinary scene boilerplate.
The filtering expressions, membership expectations, controls and repair contract
are newly authored. No C083 runtime supplied an expected answer.

The representative pinned PanelGroup has two independent occurrences. Both
initially contain a 1 m left panel and 2 m right panel. Repair changes only the
first occurrence's `minimum_width` from 0 m to 1.5 m, removing its left panel.
Its right panel retains the same source key, identity, dimensions and recorded
motion. The sibling, pinned library, PNG and independently moving marker remain
unchanged. A further drop-all example removes both first-occurrence panels while
preserving the sibling and declared image closure.

The .15 controls explicitly spell out each selected keyed value. The panel
control uses a direct conditional over literal keyed dimensions. Rectangular
prism formulas independently determine corners, volume and surface area; fixed
authored placements and velocities determine the five recorded pose times.

`workflows.json` specifies ten actual Agent workflows: scoped repair, rollback,
stale cursors/revisions, durable reopen/retry, current host authority, caller
reductions, cancellation at actual filtering work, interrupted publication,
complete attachment retrieval and delivered-control comparison. Raw requests,
stores and actual supplied bytes are required. `delivery-comparison.json` names
the narrow allowed metadata differences; `supplied-byte-adversaries.json`
requires actual corrupted artifacts and unchanged positive controls.

Read the [adoption](../../docs/language-design/keyed-filter-v0.1/ADOPTION.md) for
the complete bounded semantics. The input freeze and independent review have
separate identities. Full feature release and full-product acceptance remain
false until their own requirements are satisfied.
