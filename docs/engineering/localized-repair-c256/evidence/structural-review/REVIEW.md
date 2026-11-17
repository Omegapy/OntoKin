# C256 reader structural review

**Current disposition: approved for the corrected static scope.** See the corrected-source disposition below and `correction-review.json`. The original findings are retained as history.

**Changes requested.** This narrow static review inspected reader SHA-256 `6e7cce4fc2b40d3e1a2bf119f9d6c2ce4d5ec95f83de739ae270ed528768b1a8` and contract SHA-256 `e4fc10e2e35cf5e31d33f9e03ace623ca3a2e2df1235db638d0e7357da41ab9e`. The initial reader was reconstructed by reversing the subsequent single `AttributeError` exception-list insertion; its SHA-256 exactly matches the source observed during inspection. Both that reconstruction and the subsequent captured source are retained beside the machine-readable findings. No reader code was executed or edited.

## Findings

1. **Malformed inputs can escape the refusal boundary.** `_profile` assumes `asset` is a dictionary before calling `.get`. An `asset` list or scalar therefore causes `AttributeError`; `_public` does not normalize that exception, and the CLI catches only `Fault` and `OSError`. Other metadata `.get` calls have the same structural assumption. Separately, Python's JSON integer digit limit can produce a plain `ValueError` not included in `_public`'s normalized exceptions. Explicit object checks or carefully normalized parser failures should return the declared refusal, supported by concrete malformed-input controls.
2. **The file-read path admits sizes after allocation.** `read_bound_endpoint` uses `read_bytes()` before hashing and before `_GLB` applies the 4 MiB ceiling. Source-map admission also hashes source buffers before a length check. Bounded reads and source length checks would make the resource boundary apply before allocation/hash work while retaining exact digest admission.
3. **Accessor aliases can amplify decoded memory.** Different accessor IDs can reference the same bytes but produce separate cached value arrays. The 100,000-row per-accessor ceiling is much larger than this finite proof family's largest accessor (2,880 rows); both bound endpoints have 52 accessors and 21,859 declared scalar components. Animation's stricter 4,096-row check occurs after decoding. A cumulative decoded-component budget and role-specific pre-decode row limits would control this amplification. This is a static finding; no stress execution or measured memory claim is made.

All three findings were sent directly to the author and parent. The author has since added `AttributeError` to the normalized exceptions (subsequent captured reader SHA-256 `7acb03816b2d7def718ad6abc95a34f7af5338ab90f2dded824743f87e786cf9`). Other findings and concrete controls remain pending; no final acceptance is claimed.

## What the source establishes clearly

Imports are limited to Python's standard library. The reader contains no product imports, subprocess calls, native starts, model trials or rebuild path. Raw labels, frozen source identity associations and exact historical artifact admission are separately named. Measurement origins identify the actual binary offsets, raw animation samples and derived matrix operation. The contract explicitly keeps ownership, physical and semantic parameters, revision authority, rebuild evidence, invalid-edit atomicity and trial scores outside qualification.

The parser already checks GLB headers/chunk boundaries, table limits, accessor range/alignment, finite values, complete channel coverage and quaternion admission. These strengths do not resolve the exception and resource findings above. Independent numerical and identity tests belong to the separate main review.

## Corrected-source disposition

All three findings are **resolved within this static review** at author commit `97e8942071502044cb3baedac71622c151e52283`, reader SHA-256 `5993d1a9ca1cbccd4518ed6f113238d18f6b71ba02befd59900b93fe47ef6e6a`. The checked working files exactly match that commit. `correction-review.json` records the precise changes, hashes and approval limits. Concrete exception, size and alias controls are present in the authored tests; this reviewer did not execute them. Independent numerical and identity verification remains owned by the main reviewer. No static-scope blockers remain.
