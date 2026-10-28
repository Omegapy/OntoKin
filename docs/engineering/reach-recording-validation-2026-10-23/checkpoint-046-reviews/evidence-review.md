# C046 independent retained-evidence review

Reviewer: `/root/evidence_review`. Date: October 26, 2026, America/Denver.

**The retained evidence establishes a precise historical retirement sequence and a narrower cache-lifetime result. It does not establish the current C035 cursor sequence or a profitable optimization.** The current C035 failure does reach the same coefficient-construction division expression, after a completed coefficient lookup returned no reusable value. Its current exponent, degree, index, source frame and clock were not captured.

## Method and independence

This review reads the actual restored C033/C035 files, their published manifests, the complete C033 capture source, the current runtime and exact historical source files. The reviewer did not author the runtime, original captures, root C046 audit or C046 main report. No OntoKin module, archived driver, product request, candidate calculation or archive extraction was executed by this reviewer. The independent `review_evidence.py` reads bytes, JSON, source ASTs and trace metadata only. Its final result passes **51 checks**. The checks are metadata assertions, not product test methods.

All **727 restored members** were independently checked against their manifests by byte length and SHA-256: C033 has 87 members / 69,084,895 bytes; C035 has 640 members / 122,611,161 bytes. Root performed archive joining, CRC verification and extraction separately; this review does not relabel those operations as its own. Selected input hashes and actual source identities are retained in `result.json`.

The 65 current recovered runtime modules exactly match the C035 full-request input inventory at `4ca73909f861fe4bef9694787473621c1d21c140`, tree `87c949b238055af1ce368c694e1d5683c8aeacde`. C033 executed `a7af3ee6ad0a22869b3b26fc45ad4f42f0191c41`, tree `28c6b319686c19faba4d468634dfba52b18e037d`. Only `reach_reference.py` and `reach_reference_center.py` differ between their runtime inventories. Historical copies of those files and `reach_reference_plan.py` match the C033 inventory hashes. Complete `_orientation`, `_seed`, `_Guard.lookup`, `_Guard.remember`, `_Arithmetic.lookup`, `_Arithmetic.remember`, `_sync_cache_operand_limit`, `_series_coefficients` and `_series_integer` bodies match the current versions byte for byte. Broader source/authority differences receive the separate source review.

## Historical cursor sequence

The original C033 L03 ledger contains 154 consecutive key calls: keys 0–152 returned provisionally and key 153 raised. All 308 source-cache boundary category sums agree with recorded occupancy. Every adjacent exit-to-next-entry source-cache summary and full cursor vector agrees. All key-level and whole-capture identity assertions are true, and the observation-error list is empty.

| Historical key and exact time | Retained observation | Publication meaning |
| --- | --- | --- |
| Key 0, `0` | No centered cursor at entry or exit. | Its source-batch ledger includes ordinary cursor work, not a centered seed. |
| Key 1, `2/87` | Upper and forearm phase-0 cursors first appear with zero updates. | Two completed, published initial centered seeds. |
| Key 66, `44/29` | Both phase-0 cursors replace prior cursors at `130/87`, each with 64 updates. | Two completed, published retirements followed by direct seeds. |
| Key 88, `179/89` | Upper and forearm phase-1 cursors first appear with zero updates. | Two completed, published new-phase seeds. |
| Key 152, `243/89` | Both phase-1 cursors have reached 64 updates. | These remain the published phase-1 cursors through the failed next key. |
| Key 153, `244/89` | A new zero-update upper cursor is in `evaluate.pending_values`; the forearm direct-source calculation fails. | The upper result is pending only. Neither replacement cursor is published. |

The returned-key snapshots show **296 one-step cursor advances**: 168 in phase 0 and 128 in phase 1. Together with the six published zero-update seeds, they establish **302 published cursor changes**. These are observations of this historical request, not a universal count or a current-run measurement.

The original source and failure locals support eight selections of the direct-seed branch: two each at keys 1, 66, 88 and 153. Seven produce completed centered cursors: six are published and one upper cursor remains pending at failure. The forearm's eighth direct-source reconstruction fails while evaluating the argument to `_seed`; `_seed` itself has not yet been entered for that attempt. Four branch selections are caused by the 64-update retirement condition, at keys 66 and 153. Only the two key-66 replacement cursors are published.

At the failed historical forearm branch, witness, axis, rate and increasing-clock predicates pass. The previous cursor has 64 updates, so the strict `<64` condition fails. The exact refused integer division is `8841761993739701954543616000000 / 1307674368000` while constructing exponent 129, degree 14, coefficient index 7. The shared-budget callback refuses before this division or its prospective integer guard executes. It is not a completed arithmetic operation.

## The two caches must remain distinct

The full-request work record reports **256 entries in `ReachExecutionWork._cache`**. The series coefficients are stored instead in the independent reader's **`_Arithmetic.cache`**, a separate plain dictionary with the unchanged 256-entry maximum. The C033 snapshots place this source cache between **112 and 165 entries**. A full work cache is therefore not evidence that the coefficient cache was full.

At key boundaries the source `series_coefficients` category starts at seven entries. Its only increases are key 1: seven to nine; key 66: nine to eleven; and key 88: eleven to twelve. The category remains twelve at key 153. The capture records only these category counts and centered-cursor keys/values. It does not record coefficient keys, coefficient payloads, the complete dictionary order, individual coefficient lookup results, or individual mutation events.

### Narrow historical lifetime inference

I independently checked the proposed lifetime inference against the native mutation paths and the actual ledger. It is supportable **from key-1 entry through the key-153 exception-exit snapshot, before outer source-batch cleanup**. It does not extend to key 0 or earlier request work.

The inference needs all of the following evidence and source facts:

1. The historical external callback is native `ConstructionBudget.tick`, its construction check is `None`, and no trace/profile hook is installed. Captured callback/owner identities and limits remain unchanged. The native request has no source path that changes the operand cap or replaces the arithmetic cache. The arithmetic domain reset consequently does not clear this cache in the selected interval.
2. `_key_comparisons` invokes the centered reader at most once for a key. A centered optional-domain fallback calls `discard_cursors()` and returns `None`. Its following ordinary reader cannot construct `_CenteredCursor` values. Every selected key exit retains the owned centered cursor values; their identities and fields continue through the recorded sequence. Thus that fallback/discard route cannot have completed secretly within those keys.
3. On key 153 the actual exception is `OntoKinError` from the shared construction budget. It propagates directly through `_Guard.original` and `evaluate`; their `_OriginalFailure`/`ReferenceError` handling applies to different exception types. The snapshot occurs before the outer `_SourceBatch.__exit__` discards owned values. The pending upper cursor is not installed into the dictionary and cannot stand in for the unchanged published cursors.
4. The remaining native cache mutations are promotions, replacements and bounded insertions. Promotions and replacements preserve cardinality; insertions increase it until capacity, after which an eviction/replacement preserves capacity. No remaining mutation can take a dictionary that reached 256 back down to the observed maximum 165.

These combined facts exclude a capacity eviction in that bounded historical interval. **Occupancy alone would not prove this.** Key 0 lacks both centered cursors and the centered stationary namespace, so it cannot use the same no-discard argument and is deliberately excluded. Failure cleanup after the final snapshot is also excluded.

Under this native closure, the three coefficient-category increases establish **five new distinct completed coefficient entries** in the selected interval: two at key 1, two at key 66 and one at key 88. The failed key `("series_coefficients",32768,129,14)` was not retained at key-1 entry and was not successfully published during the reviewed interval. Its construction is not explained by a capacity eviction during that interval. No conclusion follows about its pre-key-1 history. The identities of the twelve retained coefficient entries, total hit count, and exact association between individual seed branches and coefficient lookups remain absent.

## Current C035 facts and missing data

Four actual L03 reports were compared: historical C033 stock and capture, and current C035 `complete-p11-l03-002` and `original28-002`. They agree exactly on source-file list, source manifest, program revision, original options, cap, failure object, diagnostic, shared count and the complete work object. All retain failure at **100,001 shared / 95,767 completed reach operations**, 288 reach categories and 256 work-cache entries. The current stock filename/function traceback route has the same 27 frames as the historical stock route; the historical capture adds only its two approved wrappers. Line numbers change with the source revisions. Request elapsed values differ, so this is no timing-neutrality finding.

The current trace reaches the integer division inside `_series_coefficients`. That method first performs its lookup and returns any non-`None` completed value. Therefore the current trace proves that the lookup completed and returned no reusable value before coefficient construction started. Under the native producer contract this is a miss. It is **not** a refusal before membership. The later division is refused before being performed.

| Datum | Evidence status |
| --- | --- |
| Current L03 complete-request failure, counters, complete category map and original options | Directly retained in two current C035 results. |
| Current failure route through direct source reconstruction, series coefficients and integer division | Directly retained in the current trace; bound to current source. |
| Current coefficient lookup completed without a reusable value | Inference from the retained trace and complete method body. |
| Current key index, exact time, source-frame identity, previous cursor steps and gate predicates | Not retained. Historical values must not be relabeled current. |
| Current exponent, degree, coefficient index and exact refused operands | Not retained. The current source statement does not disclose their values. |
| Current source-cache occupancy, complete keys/order/payloads, seed sequence and coefficient lifetime | Not retained. The work-cache occupancy and aggregate counts do not supply these values. |
| Historical full coefficient-key sequence and lookup/promote/publication events | Not directly retained. The narrower native lifetime inference above establishes only its stated interval result. |
| Candidate savings or the full original request's unexecuted cost | Not established. |

## Next capture requirements

A later current-L03 capture should preserve the original full request and exact current source. Capture complete bounded native source-cache key/order metadata at reader/key boundaries, centered cursor fields, pending-publication state and the active failure locals. Keep the two caches separately identified. Retain exact exponent/degree/operand-limit keys, and label `lookup entered`, `lookup returned no reusable value`, `lookup returned value`, `publication completed` and `refusal before membership` only when the selected observations establish them.

Passive two-wrapper boundary snapshots cannot automatically provide every internal cache event. If the next design does not directly observe those events, report the remaining gap and apply only a separately reviewed native mutation-closure inference. It must not claim an unobserved exact event trace. Preserve original callbacks/observers, forwards and exception identity; do not install a trace/profile hook or replace participating arithmetic/cache methods. Pair the capture with a fresh stock request and compare the full original counters, categories, source and settings, failures and underlying frames before drawing conclusions. Snapshot timing must distinguish values before cleanup, pending values and post-cleanup state.

This is capture preparation only. Execution still needs the exact complete source closure, independent review and an actually active exclusive window. The 64-update limit, required direct seed, independent equations, coefficient/remainder proof, budgets and original fixtures remain unchanged. Original28 stays 24/28, C035 stays held, and no release or complete saving is established here.
