# Bounded pure keyed reduction inputs

These inputs specify C082 before its runtime implementation. They select source
`0.15` / `keyed-reduction-0.1`, explicit Agent/0.15 and recorded GLB/0.15.
The corpus contains 128 independently authored source cases: 62 intended
successes and 66 intended refusals. Counts describe frozen requirements, not
executed product results.

```ontokin
reduce_keyed<Length>(lengths, 0[m], (acc, key, value) -> acc + value)
```

The expression evaluates the input and seed once, then carries an accumulator
through the input's canonical ASCII key order. Each step must retain the
declared accumulator type. An empty input returns its seed after static body
checks. This is pure construction work, and every step uses the current
execution budget.

`expected.json` records exact program/source identities, positive and negative
outcomes, independently calculated numeric results, required provenance
locations and separately authored `.14` controls. Compound leaf controls use
explicit existing constructors. Numeric controls use direct arithmetic or
literal independently calculated answers. No candidate runtime output supplies
an expectation.

The representative pinned PanelGroup uses a reduction over scaled segments to
compute one aggregate length. Two occurrences share the same library and PNG.
Changing only the first occurrence's scale from 1 m to 1.5 m changes its panel
widths from 1/2 m to 1.5/3 m. The sibling's dimensions, all surviving identities,
library/PNG bytes and independent marker motion remain unchanged. The explicit
`.14` control spells out the same two-term arithmetic. Geometry, volume,
surface area, texture coordinates and five recorded pose times have separately
authored exact expectations.

`workflows.json` requires ten actual Agent workflows, including scoped repair,
rollback, stale revisions/cursors, durable reopen/retry, current host authority,
caller caps, cancellation during reduction, interrupted artifact publication,
complete attachment retrieval and destination comparison. Source acceptance,
Agent evidence, independent supplied-byte readers and real pinned destination
checks remain distinct requirements.

The exact input freeze and independent review live under
`docs/language-design/keyed-reduction-v0.1/`. Full feature-release and
full-product acceptance remain false until their separate requirements are
satisfied.
