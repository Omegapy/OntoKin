# C047 current-source reader-cache lifetime review

Reviewer: `/root/lifetime_review`. Scope: static source review and preparation for current L03 evidence, without product imports, requests, tests, archive execution or repository edits.

Source is authentic C046 final `48b5d381a0f86d9706a109b78e2ce52eb0d287f0`, tree `33ac0caa77528432d18132a1e606d1e4fbd7ab80`. C035's held runtime is the current source. No historical C033 local is treated as a current observation.

## Question and mutation closure

The coefficient cache is the native `ReachReference.a.cache` dictionary. It is distinct from `ReachExecutionWork._cache`; the work report's cache occupancy cannot substitute for the reader dictionary's occupancy. Taylor coefficients use `("series_coefficients", operand_limit, exponent, degree)`. They are distinct from the centered Hamilton offset coefficients and C035 product receipts.

The current source exposes these reader-cache mutation paths:

| Path | Source location | Completed effect |
| --- | --- | --- |
| Domain reset | `reach_reference.py`, `_Arithmetic._sync_cache_operand_limit`, 102–108 | Charges, clears the entire reader dictionary, then installs the new operand limit. Must be excluded on the analyzed interval. |
| Ordinary lookup | `reach_reference.py`, `_Arithmetic.lookup`, 358–368 | A hit deletes and reinserts the same value, preserving occupancy while promoting its order. No callback occurs between those two operations. |
| Ordinary publication | `reach_reference.py`, `_Arithmetic.remember`, 346–356 | Replacement preserves size; new insertion grows size below 256; at 256, oldest-key eviction plus insertion preserves size. An admission may decline insertion. |
| Inline Cartesian lookup/publication | `reach_reference.py`, `_PoseArithmetic._recording_cartesian`, local `calculate`, 1343–1400 | Same promotion/replacement/insertion/capacity rules, surrounded by current receipt checks. |
| Centered lookup/publication | `reach_reference_center.py`, `_Guard.lookup` and `remember`, 318–352 | Same ordinary rules. A pending write only stages an entry; staging does not mutate the reader dictionary. |
| Pending cursor publication | `reach_reference_plan.py`, `_PendingCursors.publish`, 341–355 | First checks nested-writer identity; then replacement/insertion/capacity rules. |
| C035 product publication | `reach_reference_center.py`, `_ProductSession.publish`, 1086–1105 | Replaces only a still-retained exact previous center-coefficient value. Same key and dictionary position; occupancy is unchanged. It does not restore an evicted slot. |
| Center/batch discard | `reach_reference_plan.py`, `_SourceBatch.discard_cursors`, 157–161 | Deletes tracked entries still identical to their batch-owned value. This can reduce size and conceal earlier capacity unless ruled out. |

`_ProductSession.close` (1107–1115) changes the session and restores its observer; it does not delete reader entries. `_SourceBatch.check_cursors`, `completed_ordinary_request`, and successful batch exit may shrink their private ownership ledger, not the reader dictionary. `_phase_cache` and `_basis_cache` are separate dictionaries.

## Conditions needed for a current no-capacity-eviction theorem

The historical C046 theorem is a useful proof pattern, not current evidence. A current proof must independently discharge all of these conditions:

1. Identify an exact starting boundary and the final pre-cleanup snapshot. Observe complete ordered reader keys and occupancies at every entry/exit in that executed interval. Validate the diagnostic itself before drawing source conclusions.
2. Bind native request, work, source, cache, method, callback and observer owners. The ordinary `ConstructionBudget.tick` has `check=None` in this original request; its only live effects are budget/timing accounting and the ordinary refusal. Inspect the actual capture to establish that native domain rather than assuming it from a historical request.
3. Verify the live work operand cap, reader `_cache_operand_limit`, `bits` and `scale` remain the original native values. Review the entire reachable source for assignments. Under fixed native owners and no external callback, `_sync_cache_operand_limit` cannot clear the dictionary. Boundary agreement alone is insufficient if effectful callbacks or reentrant mutation remain possible.
4. Exclude an effectful `discard_cursors` in each enclosed key. `_key_comparisons` has one centered-reader invocation (1957 onward); a centered domain rejection discards owned entries and returns `None`, then ordinary interval fallback cannot manufacture `_CenteredCursor` or `reference_centered_stationary_pose` entries. Continuing surviving centered cursor history at each exit can exclude that route. Check actual cursors/ledger and source control flow, including the final exception exit; do not use total occupancy alone.
5. Exclude the outer `_SourceBatch.__exit__` failure cleanup from the interval. It runs after the wrapped `_key_comparisons` exception snapshot and intentionally discards owned entries. A later post-request snapshot is not interchangeable with that pre-cleanup endpoint.
6. Account for C035's product publication. It is a size-preserving existing-key replacement, so it does not defeat the monotonic-size argument. Its separately installed native product observer must be bound in current evidence.

Once reset and effectful discard are excluded, every completed remaining native mutation preserves or increases occupancy until 256; once 256 is reached, completed mutations preserve 256. Lookup's transient delete-and-reinsert has no intervening callback/snapshot. Therefore a later boundary below 256 rules out capacity being reached earlier in that closed interval. With every boundary below 256, capacity eviction cannot have occurred there.

This is a source-and-data inference. Boundary snapshots do not directly observe individual lookups, promotions, insertions or evictions. Exact ordered keys can establish their boundary presence; they cannot by themselves assign every coefficient construction to a particular direct seed or count intermediate hits. Opaque IDs can be recycled, and coefficient bit widths are not payload equality.

For a final exact coefficient lookup that returned `None`, no-capacity-eviction plus no reset/discard implies that key was absent at the interval's start and was not successfully published during it. Successful lookup membership is distinct from failure before dictionary access. Entering the coefficient-construction loop establishes the completed lookup miss.

## Retirement and arithmetic opportunities

`_orientation` (536–598) advances only when witness/axis/rate/clock/domain match and `previous.steps < 64`. A retired cursor requires `guard.original(body.direct, clock)` before `_seed`. Pending cursor publication follows full plan/owner/domain checks. Neither changing the retirement limit nor seeding from a previous approximate center is within this diagnostic scope.

`_series_coefficients` (471–493) publishes only its complete immutable tuple. For positive degree `d` on its standard factorial sequence, the original helper's construction has two initial shifts, `d` divisions, `d` coefficient shifts, `d+1` packed additions and `d` packed multiplications: `4d+3` construction charges. Add lookup and publication for `4d+5` complete miss charges, versus one eligible hit charge. Degree 14 gives 59/61/1 and a 60-charge gross counterfactual; these remain source-derived counts until current locals bind the actual degree and route.

If the current failed key is new within the independently proved interval, preserving an allegedly evicted coefficient is unsupported there. A separate arithmetic-construction design may still be investigated, but requires exact equations, prospective-width guards, callbacks/owners, complete added/removed charge accounting and bounded storage/lifetime. No runtime optimization is selected by this preparation.

## Review disposition

Ready to examine the current retained capture after root closes its exclusive execution window. This note does not establish current L03 locals, neutrality, elapsed behavior, numerical improvement, a successful product request, or release acceptance.
