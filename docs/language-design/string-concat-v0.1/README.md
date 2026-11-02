# Bounded pure String concatenation

Explicit source `0.20` / `string-concat-0.1` adds exact immutable `String + String`. The [adoption](ADOPTION.md) establishes the unchanged reviewed [specification](SPECIFICATION.md); [frozen inputs](freeze/INPUTS-MANIFEST.json) were published and read back before implementation. The separate [Agent/0.20 guide](../agent-v0.20/README.md) and recorded GLB/0.20 binding preserve earlier defaults.

```ontokin
rekey_keyed<Length>(widths, (old_key, width) -> prefix + old_key)
```

A reusable library can give independently supplied part groups distinct prefixes. Source versions own their expression meanings: an imported older helper retains its old String-addition refusal. Both operands evaluate once, left then right; exact Unicode scalar order is preserved without conversion or normalization. Other operators and numeric, unit, frame and type behavior keep their inherited dispatch.

Computed results are bounded to **65,536 UTF-8 bytes each** and **4,194,304 cumulative logical result bytes per request**. A scalar scan without operand encoding or copying, allocation reservation and publication all use the existing admitted request ledger. Successful operations add `3 + ceil(left_bytes/64) + ceil(right_bytes/64) + ceil(result_bytes/64)` operations. Cancellation and elapsed-time checks retain their original authority and exception identity. Abstract checks return unknown String without performing dynamic concatenation.

String validity and stable-key validity remain separate. Rekey still admits only the existing 1–64-character ASCII key domain and refuses collisions. A computed empty or Unicode String can be valid ordinary text while remaining an invalid key. Existing source revisions, payload entries, old contributor keys, dependencies and generated-value restrictions remain the only repair authority; there is no new public lineage family.

The [corpus guide](CORPUS.md) describes independently authored input scope. [Preflight gates](freeze/PREFLIGHT-GATES.json) and the [independent adoption review](freeze/review-transport-agent02-final.json) establish input preparation. The [engineering record](../../engineering/string-concat-2026-11-01-c087/README.md) separately records actual implementation, source/Agent/native evidence, integration and retained failures. No full-product or complete experimental-feature release is implied.
