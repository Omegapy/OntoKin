# Pure keyed-value transformation

C081 adopts one finite construction expression for explicit source `0.14` / `keyed-transform-0.1`. A transformation computes one new value per existing key while preserving the collection's keys and size. Implementation and measured evidence remain separate from this decision.

```ontokin
map_keyed<Length>(lengths, (key, value) -> value * 2)
```

The example doubles lengths under their original stable keys. `key` is a String and `value` has the input element type. The body is a pure expression; it cannot filter entries, create keys, mutate values or add physical authority. The maximum remains 256 entries per flat keyed value, and all work consumes the current execution budget.

Read the [versioned decision](ADOPTION.md), [grammar](ontokin-keyed-transform.ebnf), [independent acceptance inputs](acceptance.json) and [exact freeze](INPUT-FREEZE.json). Implementation, executed evidence and integration will be recorded separately. Earlier source and Agent versions retain their behavior.
