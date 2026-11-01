# C085 expectation amendment 002: grouped operation spans

**State:** Proposed for independent review and publication before fresh execution.  
**Original input commit:** `92b1ee60a2b9439878b7124981d2896be858937f`.  
**Original input manifest SHA-256:** `4914fd1696bc0c441736684289a4c4422c9db30ba99091dfbbbf8d1eb1c8a2a9`.  
**Original expected JSON SHA-256:** `f6f00f0a73ce65a804650f8274c65111ea4a938394ee9e6f8aef90a36cedbad7`.

## Finding and independent basis

The first retained candidate core invocation exposed an inconsistency in five frozen operation spans. Its failed log and complete recorded source cut remain identified in the accompanying JSON. This amendment does not relabel that invocation as passed.

The correction follows from the original source and the already inherited grouping rule. In unchanged C084 `ontokin/syntax02.py`, `Parser.primary` parses an opening parenthesis, the expression and its closing parenthesis, then builds the same expression kind with a span covering that complete grouping. The C085 grammar supplements unchanged .17 lexical precedence; the adopted provenance contract requires original complete expression locations and retains inherited map origins. The frozen `nested-zip-indexed-scalar` case already includes its enclosing grouping parentheses in the outer zip expression's location.

The independent authoring scanner incorrectly excludes grouping when the preceding text ends in `>`. That guard was intended for a generic callable, but also matches the distinct `->` lambda token. An expression such as `(outer_key, outer_value) -> (zip_keyed<…>(…))["x"]` therefore has a shortened frozen zip location. The same scanner error affects one inherited map location in a zip body. The parentheses are already present in the unchanged source; no new source bytes or language rule are needed.

An independent byte scan verifies each enclosing parenthesis pair, its preceding lambda arrow, its following index operation, the original source digest, and every duplicated expectation location. A scan of all frozen entry-source locations finds exactly these five affected operation spans. No candidate value, selected origin ordering or output geometry defines the corrected answers.

## Exact coordinate corrections

All ranges are half-open UTF-8 byte offsets in the original `entry` source. Every source ID, source revision, filename-enrichment rule and other record field remains unchanged.

| Case | Operation | Original range | Corrected range | Location replacements |
| --- | --- | --- | --- | --- |
| `zip-in-map-body` | Inner zip | `[213, 300)` | `[212, 301)` | 3 |
| `zip-in-filter-body` | Inner zip | `[216, 303)` | `[215, 304)` | 3 |
| `body-nested-map` | Inner map | `[245, 294)` | `[244, 295)` | 1 |
| `zip-inside-zip-body` | Inner zip | `[253, 348)` | `[252, 349)` | 7 |
| `zip-inside-body-indexed-scalar` | Inner zip | `[247, 342)` | `[246, 343)` | 8 |

The accompanying machine-readable amendment enumerates **22 exact JSON pointers**, each with its complete original and corrected four-field frozen location object. Only 44 scalar coordinate fields change in the effective in-memory expectations. Those pointers include the source-expression inventory, required expression order and already specified aggregate, stored-leaf and indexed derivations where the same original expression is repeated. Their order and all contributor records remain unchanged.

## Application and lineage

Keep the original `expected.json` and original input manifest byte-exact. Readers and test drivers must verify those original identities, apply only the enumerated replacements to a detached copy after testing each full original object, then verify the effective expectation identity. The specified original JSON serialization produces effective SHA-256 `d418ae53105698201b79c1ef4d75de64b53c9ed7a76c722a2a84ac384cbc365a`.

Publish the independently reviewed amendment before using that effective copy in fresh verification. Each new receipt must identify the original input freeze, this amendment's publication and exact bytes, and the effective expectation hash. Preserve the first failed invocation and source cut separately; do not rewrite their inputs, logs or results.

No source or explicit-control bytes, typed values, key sets, diagnostic code or precedence, body evaluation count, dependency, taint, paired contributor, origin order, budget, geometry, material, motion, destination comparison, or runtime behavior changes under this amendment. The 160 unchanged .17 control preflights still identify their original source bytes. This amendment grants no additional metadata normalization and is separate from comparison amendment 001.

Implementation, executed evidence, integration and complete release acceptance remain separate. No passing runtime or release claim is made here.
