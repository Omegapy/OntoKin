# Pure keyed reduction

C082 adopts a finite construction expression for explicit source `0.15` / `keyed-reduction-0.1` after its separate independent review and input freeze:

```ontokin
reduce_keyed<Length>(lengths, 0[m], (total, key, value) -> total + value)
```

The explicit seed starts the accumulator. The pure body combines each input value with that accumulator in canonical ASCII key order. Empty input returns the seed after static body checks. The input remains bounded to 256 entries and every operation uses the current request budget.

Read the [versioned decision](ADOPTION.md), [grammar](ontokin-keyed-reduction.ebnf), [independent acceptance inventory](acceptance.json), [input freeze](INPUT-FREEZE.json) and [independent design review](INDEPENDENT-REVIEW.md). Adoption, implementation, evidence and integration have separate identities. Earlier source and Agent versions keep their meanings; complete feature and product release acceptance remain false.
