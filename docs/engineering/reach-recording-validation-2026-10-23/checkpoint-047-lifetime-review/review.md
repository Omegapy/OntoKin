# C047 current L03 coefficient-cache lifetime review

**The current failure is a completed lookup miss for a coefficient key that was never retained during the captured interval. Protecting an allegedly evicted entry is unsupported for this interval.** The source-and-data proof covers **key 0 entry through key 153's exception snapshot before outer cleanup**, on the exact original native request. It selects no runtime change.

This is an independent source and retained-JSON analysis. The reviewer did not author the C046 capture, C047 pair runner, product outcomes or independent pair audit. The earlier [source preparation](source-checklist.md) remains unchanged. The [reproducible census](census.py) imports no OntoKin code and executes no product request, archived driver, solver, test or failed tail.

## Evidence and source binding

Actual source is `48b5d381a0f86d9706a109b78e2ce52eb0d287f0`, tree `33ac0caa77528432d18132a1e606d1e4fbd7ab80`. The separate independent pair audit establishes that both original requests failed on identical complete work maps, diagnostics and underlying traceback frames, with unchanged inputs, owners and original limits. Its admissibility conclusion is a prerequisite here; this review does not replace that audit or claim elapsed neutrality.

The [census result](census-001/result.json) passes **27 aggregate checks** over **325 exact inputs**. Before/after input manifests agree. These are metadata assertions, not product tests. It verifies all **311 cache snapshots / 122,526,082 bytes**, the key ledger, failure locals, eight current source files and the independent comparison records. Every snapshot's descriptor, length and SHA-256 matches; no coefficient entry is omitted. Complete function bodies and their exact source locations are bound in [source-bindings.json](census-001/source-bindings.json). The final source binding resolves the preparation note's abbreviated Cartesian helper label to `_PoseArithmetic._recording_cartesian_rotate`.

There are **154 consecutive calls**, key indices **0–153**, with entry and exit snapshots for each. The first 153 return provisionally; key 153 raises. Three additional failure-frame snapshots equal the final pre-cleanup cache snapshot by bytes. Filename numbers use the one-based call ordinal: `key-154-exit.json` belongs to key index 153.

The reader cache is `ReachReference.a.cache`, a native dictionary. Its recorded occupancy rises from **112** at key 0 entry to **165** at the final failure boundary, with no decreasing boundary count and no boundary reaching the **256-entry** capacity. The separate `ReachExecutionWork._cache` reports 256 entries; that report says nothing about reader-cache fullness.

## Exact coefficient-key census

All twelve distinct keys have category `series_coefficients` and operand limit **32768**. The table abbreviates only these two fixed fields; exponent and degree are exact captured native integers.

| First retained boundary | Exact `(exponent, degree)` keys | Coefficient entries after boundary |
| --- | --- | ---: |
| Key 0 entry, clock 0 | `(50,17)`, `(52,16)`, `(53,13)`, `(127,16)`, `(128,2)`, `(128,13)`, `(128,16)` | 7 |
| Key 1 exit, clock `2/87` | `(129,7)`, `(129,8)` | 9 |
| Key 66 exit, clock `44/29` | `(129,13)`, `(129,17)` | 11 |
| Key 88 exit, clock `179/89` | `(129,16)` | 12 |

No coefficient key disappears from any subsequent captured boundary. The failed key, **`("series_coefficients", 32768, 129, 14)`**, is absent from **all 311 snapshots**, including the three exact failure-frame cache states. The census retains each key's first/last boundary and observation count in [coefficient-census.json](census-001/coefficient-census.json); the complete small per-key timeline is in [boundary-census.json](census-001/boundary-census.json).

These are boundary observations. The proof below turns the five new distinct keys into five completed coefficient constructions within the interval. Their exact publication order inside each key, intervening hit counts and assignment to particular direct-seed invocations are not established by a before/after snapshot. The seven initial keys belong to prior setup; their construction chronology is outside this interval. Integer widths and object IDs do not establish numerical payload equality.

## Why no coefficient entry could have been evicted in this interval

### 1. The complete current native mutation set is closed

`_Arithmetic.remember` and `lookup` in `reach_reference.py` (346–368), inline Cartesian lookup/publication in `_recording_cartesian_rotate` (1210–1417), `_Guard.lookup`/`remember` in `reach_reference_center.py` (318–352), and `_PendingCursors.publish` in `reach_reference_plan.py` (341–355) preserve the original bounded dictionary semantics. A hit deletes/reinserts without an intervening callback. Replacement preserves size. A new insertion increases size below capacity, or evicts the oldest entry and preserves size at 256. Staging a pending cursor does not mutate the dictionary.

C035 adds `_ProductSession.publish` (1084–1105). It replaces a center-coefficient value only when the current dictionary still contains the exact prior value under that key. It neither inserts a missing key nor restores an evicted one, and replacement preserves both size and order. `_ProductSession.close` restores its own observer and changes session state; it does not remove reader entries. This current-source path is included explicitly, rather than assuming the older C033 mutation set still suffices.

The only relevant size-reducing routes are `_Arithmetic._sync_cache_operand_limit`'s whole-cache clear and `_SourceBatch.discard_cursors`'s removal of owned entries. Other phase/basis caches and the batch's private cursor ledger are separate structures.

### 2. No domain clear is available on this native request

Every snapshot records `bits=128`, `scale=2**128`, reader `_cache_operand_limit=32768` and live work operand cap 32768. The six selected failure frames preserve those same current fields where present. All 18 outer and 12 per-key ownership/dispatch checks pass. The external callback is the native `ConstructionBudget.tick`, with `check=None`; the work observer is absent and both source observers are restored at each boundary.

The source closes what boundary equality alone cannot: after construction, the native execution path does not assign a different operand cap or precision. The normal construction callback only accounts for work/time and raises the original refusal. The source readmission observer and C035 product observer check or latch their own receipts; they do not alter these fields or clear the reader cache. The unchanged driver reads detached native values and changes only the two approved outer dispatch targets. There is no custom/reentrant callback or trace/profile route in the admitted request. Consequently `_sync_cache_operand_limit` cannot enter its differing-domain clear branch during this interval.

### 3. Current evidence excludes an effectful discard, including key 0

For keys **1–153**, every exit retains centered cursors, including their continuing phase/frame/clock/update histories. `_key_comparisons` (1957–2051) makes at most one centered-reader call. A centered domain rejection calls `discard_cursors` and returns `None`; its subsequent ordinary interval fallback cannot create `_CenteredCursor` or centered stationary-pose values. The batch's owned values would be removed, and there is no later centered invocation in that key to reconstruct them. Continuing published centered values therefore exclude an effectful discard on those calls. At key 87 the old phase's centered values remain while a separate ordinary plan is added; they are not relabeled as current phase values.

Current capture also closes **key 0**, which C046's historical theorem excluded. Its entry batch has **zero plans and zero owned cursors**. Its exit has one eight-node plan over all six carrier targets with the exact field **`centered=False`**, and two ordinary cursor-ledger entries. In `_phase_poses` (862–934), `prepare`'s false recipe is retained and returns before centered `evaluate`; ordinary fallback can register that false plan. A plan actually evaluated as centered has a tuple recipe. Ordinary evaluation does not convert it to false, and discard does not remove registered plans. The single retained false plan therefore establishes that key 0 did not execute the centered discard route. This argument uses the current exact recipe field and source control flow, not the absence of centered cursors alone.

There is no earlier batch exit/restart within the captured interval: the complete wrapper ledger has exactly one unbroken sequence 0–153. Inter-key certificate work does not call centered evaluation or discard. The final outer `_SourceBatch.__exit__` cleanup runs after the wrapper's exception snapshot and is expressly excluded.

### 4. Occupancy and exact key absence complete the proof

With clear and effectful discard excluded, completed native mutations cannot decrease size before 256 and preserve 256 after capacity is reached. The temporary deletion in a hit promotion has no intervening callback and ends with reinsertion. If capacity had been reached at any time in the analyzed interval, no later boundary could have fewer than 256 entries. The final pre-cleanup boundary has **165**, contradicting that possibility.

Thus no capacity eviction occurred from current key 0 entry through key 153's pre-cleanup snapshot. The exact failed key is absent at the initial boundary and at the completed lookup, and no permitted remaining mutation can remove a successfully published coefficient key. It was therefore **not successfully constructed and retained earlier in this interval**. Each of the five newly observed keys was constructed and published once; a later call with that still-retained key would take the original cache hit.

The result is a source-bound inference, not a recorded mutation-event trace. It does not cover setup before key 0, final outer cleanup, the unexecuted tail, or arbitrary hostile/reentrant requests. It does not assert that the failed key never existed before the captured interval.

## Current retirement and partial-failure facts

The cursor census uses copied native phase/frame fields and full retained cursor values, without relying on recycled object IDs. It records **296 published advances** and **six published zero-step cursors**. Current failure locals add one complete but unpublished upper replacement and one forearm direct reconstruction that fails before `_seed` begins.

| Key / clock | Direct-branch selections | Complete replacement cursors | Published replacements | Current reason |
| --- | ---: | ---: | ---: | --- |
| 1 / `2/87` | 2 | 2 | 2 | First centered pair in phase 0 |
| 66 / `44/29` | 2 | 2 | 2 | Both preceding cursors reached 64 updates |
| 88 / `179/89` | 2 | 2 | 2 | First centered pair in phase 1 |
| 153 / `244/89` | 2 | 1 | 0 | Required retirement; upper pending, forearm fails |
| **Total** | **8** | **7** | **6** | Four selections follow the 64-update limit |

These are direct-cursor branch counts, not all calls to the internal `_seed` helper, which can also occur in increment calculations. Published boundary changes and the two retained failure-path facts establish the table under the reviewed one-evaluation control flow.

At the failure, the previous forearm cursor is at `243/89` with 64 updates; `advance=False`. The current local `steps=0` belongs to the pending reconstruction and does not replace the old cursor's 64. `_series_coefficients` has `cached=None`, exponent **129**, degree **14**, index **7**, odd factorial index **15**, and seven prior packed coefficients. `_series_integer` is about to divide `common` by `factorials[15]`; its leading shared charge refuses before the division. Both published cursor lists remain unchanged across the failed key. The upper zero-step cursor at `244/89` remains in the pending list and is not published.

The original positive-degree helper has `4d+3` construction charges and `4d+5` complete miss charges including lookup and publication. At degree 14 this is **59 construction / 61 complete miss / one eligible hit**. The current partial helper has executed **29 construction operations** before its refused index-7 division. These are source-derived executed-prefix counts; the failed tail and total successful-request work remain unknown. No saving is measured or accepted.

## Concrete next scope

Preserving an allegedly evicted coefficient cannot explain or repair this observed miss within the proved interval. The supported next bounded task is a **source-level feasibility review of exact coefficient construction on a genuine miss**. Use the captured `(129,14)` partial construction and the five newly completed keys as explicit evidence. Preserve the original independent midpoint, first strict stopping degree, factorial values, coefficient equations, outward bounds, prospective operand guards, callbacks, exact request limits and required direct reseeding.

Before selecting code, write a complete added/removed charge ledger for a concrete algebraic construction, including its screening, guards, fallback and any storage/authority work. A positive local helper estimate would still need independent numerical/authority review and fresh unchanged complete requests. No coefficient pinning, added numerical cache, reset allowance, raised retirement limit or failed-tail continuation is selected here. Original28 remains 24/28, C035 remains held, and the full release gates remain open.
