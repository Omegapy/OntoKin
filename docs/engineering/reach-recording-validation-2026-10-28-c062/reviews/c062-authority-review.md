# C062 independent source authority review

Reviewer: `handoff_audit`  
Scope: static review of shared ordered ancestry descriptors in `ReachReference._phase` -> `_ancestry`.  
Source: verified C061 partial checkout, final commit `e5e99b92e4efa541b434abcdda5c2ec31dda6a39`, tree `fb17897b2de27b79cf1b9aa790c7c354e17855d3`; executed runtime unchanged from `bd5a09618c123a0b1d3339df3a944cfd6ed63b56`.  
Method: source inspection and standard-library parsing of the retained C061 JSON evidence. No product module was imported, no product request or test was run, and no packet file was changed.

## Decision and finite scope

Reject an isolated replacement of the ordered parent walk, with `_incoming` and downstream control/cache behavior unchanged, as a complete P11 or L03 remedy. The retained successful phase paths bound the removable parent-loop charges by 171 for P11 and 68 for L03. These amounts are below the separately derived minimum future work of 1,260 and 594 respectively. This conclusion grants free, perfectly correct descriptors and therefore does not depend on pessimistic authority overhead.

The source also rejects an unguarded descriptor cache keyed only by reference/model/state identity or `_incoming_graph_identity`: those identities do not attest the live fields that the original walk reads. This is a rejection of that authority premise, not a proof that all bounded descriptor sharing is impossible. A broader candidate that also changes `_incoming`, downstream work, or cache effects needs its own complete bound and authority analysis. The phase-path inference alone does not measure `_incoming` cost.

## Independent evidence check

I parsed the original `evidence/round-001/P11/capture/reader-setup.json` and `evidence/round-001/L03/capture/reader-setup.json` from the ten C061 evidence parts in memory. There are exactly 60 and 24 returned `reference._phase` spans. Their returned paths contain 171 and 68 non-world strings ending in `.frame` respectively.

This is a valid upper bound without having to classify every string as an object frame or site frame. Each successful `_ancestry` loop performs one tick at `reach_reference.py:4220` and appends exactly one `stem + ".frame"` at line 4224. The optional initial site frame (4213–4217), or an unusually named relation, can only add extra counted strings. All examined phase calls returned, so no failed terminal visit is missing from a successful path. `_phase` passes the returned path unchanged into `ReferencePhase` at 4841–4846.

These are source-derived ceilings on this specific charged loop, not measured ancestry-span costs, complete-request costs, or proof that replacement work is free. No entire 6,006/3,300-operation phase body is attributed to ancestry.

## Exact source dependencies and evaluation order

All following line references are to `ontokin/reach_reference.py` unless a different file is named.

| Stage | Live dependencies and order | Consequence for reuse |
| --- | --- | --- |
| Incoming relation selection, 2436–2459 | Iterate `state.grips`, tick for each grip, build a frozenset, then call `self.a.lookup`. The key includes `_incoming_graph_identity`. On a miss, visit joints in dictionary order and tick before reading `joint.kind`, `joint.child`, and the child site's `owner`; then visit follows and tick before reading `follow.child`. | Reuse of this map already exists. A new descriptor must not claim these existing savings again. Grip identity alone is insufficient. Cold-build overwrite order matters: later joint entries overwrite an earlier child entry, then follow entries can overwrite joint entries. |
| Entry, 4209–4212 | Call `self._incoming(state)` first; then call `carrier.removesuffix`; only then handle `carrier == "world"`. | An early world return would bypass original callbacks, cache effects and possible errors. |
| Initial site, 4213–4217 | Check membership in `self.model.sites`; read that site, then `site.pose.position`, append the carrier, and finally read `site.owner`. | A site-to-owner edge and its offset remain dependencies even though `_phase` discards the offsets result. |
| Each parent visit, 4219–4228 | Tick; reject a repeated stem or an already-overlarge visited set; add the stem; append its frame; test membership in the admitted incoming map; return a root or read the relation and append its name. | Preserve cancellation-before-cycle/depth-error ordering and exact ordered output. A cached suffix must respect the total prefix-plus-suffix depth, not just its own length. |
| Follow edge, 4229–4239 | Read `self.model.follows[relation]`, then `follow.offset.position`; read the parent and return if it is world; otherwise remove the suffix, test current site membership, optionally read parent-site position, and read its owner. | Root, source path and offsets depend on more than the relation tuple. The offset read precedes even the special world-parent return. |
| Joint edge, 4241–4245 | Read the joint, then child-site position and parent-site position in that order; inspect `joint.kind`; append the joint only for hinge/slider; read the parent site's owner. | A cached joint list can become wrong without changing the incoming map. Skipping the child-site read changes possible first errors. |
| Phase consumer, 4821–4846 | Run ancestry before identity/root poses, acceleration, source basis, optional axial derivatives, coordinate laws and final distances. | A later basis read is not an equivalent replacement for an omitted earlier ancestry read or error. |

The depth guard uses `len(visited) > 128`, not `>= 128` (4221). A path can therefore append 129 distinct object stems successfully before termination; a subsequent visit fails. A proposed optional bound may fall back earlier, but must not replace the ordinary limit with a stricter failure.

## Who can change the relevant records

The constructor copies the model and deep-copies the objects, sites, joints, follows, actions and provenance collections (2253–2260). It also copies events (2261–2265). This separates the captured records from ordinary later mutations of the original input records. It does not freeze the captured graph or install mutation tracking.

The captured model remains exposed as `reference.model`. `SceneModel`, `SiteModel`, `JointModel`, and `FollowModel` are mutable dataclasses (`ontokin/model.py:59–92,172–196`). Their maps are native dictionaries. A caller holding the reference, or a callback closing over it, can replace maps, entries or fields. `Pose` is frozen (`model.py:19–23`), but a mutable Site/Follow record can replace its whole pose/offset. Frozen dataclass status alone is also not a defense against deliberate `object.__setattr__` mutation; the existing runtime explicitly recognizes this issue for frozen numeric cells at 4671–4678 and 4800–4803.

`_State.grips` is a mutable set (2114–2129). Ordinary initialization adds grip relations (2326–2332); a release removes its grip after computing incoming kinematics (3615–3643). Full state copies deep-copy it (2358–2366). Coordinate-only copies share unchanged fields and can return the same state when no action changes (2402–2434). Thus neither a state identity nor a new boundary necessarily represents a new or immutable topology domain.

`_incoming_graph_identity` is a plain object created once at 2266. No generation update or setter interception accompanies later source mutations. Its actual role is to separate references that share an arithmetic cache (2437–2441), not to certify all source fields on every use.

The cached incoming map is a `MappingProxyType` over a private local dictionary (2459), with relation tuples as values. That result has stronger immutability than the mutable Site/Joint/Follow records read by ancestry afterward. These authorities must remain distinct. In particular, changing a live joint's `kind` or a parent's site owner can change ancestry while the original cached incoming relation map remains the same. A replacement must not silently rebuild a fresh relation map and call that equivalent to the original cached-map behavior.

## Callback and dispatch obligations

`_Arithmetic.tick` snapshots its observer, calls the current `self.check`, and only after normal return calls the observer (107–111). `_Arithmetic.check` initially binds the supplied work tick (72–84). `ReachExecutionWork.charge` invokes its external callback before resource checks and counter increments, preserves the same raised exception object, and does not run the observer on callback/resource failure (`ontokin/reach_numeric.py:71–94`). These are mutation and failure boundaries even when the source data was native at entry.

An implementation must preserve the live dispatch it continues to use. `_phase` currently calls `self._ancestry`; ancestry calls `self._incoming`, `self.a.tick`, and, through incoming, dynamic cache methods. If a new call site bypasses an overridden method or directly invokes a captured unbound implementation, it needs an explicit native-dispatch premise with a correct fallback. If it retains the original dynamic call, it need not invent a separate check for dispatch that it has not bypassed.

Native container and record shape are also relevant. Foreign string/key/hash/equality implementations, model attribute accessors, and replaced class methods can execute user code while a purportedly passive signature is read. Exact model object identity does not certify their dispatch. A sufficient domain can reject such shapes and retain the ordinary path; it should enumerate the methods and fields it actually bypasses rather than claim an unbounded global hostile-code proof.

The existing numeric `_recording_body_domain` (2564–2566) only checks precision, operand limit, work presence and `callback_error` availability. It is not a seal for source graph fields, class/function dispatch, or incoming cache contents.

## Concrete first-error counterexamples

These are source-order counterexamples, not executed tests.

1. **Ignored offsets still carry required reads.** Consider an object with a cached incoming follow relation whose parent is world. Replace the live native `FollowModel.offset` with an object lacking `position`. Ordinary ancestry raises `AttributeError` at 4231 before testing the world parent at 4232. A cached root/path-only answer skips that error. Because `_phase` immediately performs identity/root arithmetic afterward, a later cancellation or resource error can become first instead. The discarded offsets value does not authorize removing the read.
2. **Unchanged map identity does not preserve the joint list.** A cached incoming tuple can continue to name a joint while that joint's live `kind` changes from hinge to fixed. Ordinary ancestry rereads `kind` at 4243 and omits it from the joint list. A descriptor keyed only by map identity returns the old list and causes `_joint_path` to process an obsolete coordinate dependency at 4833.
3. **Terminal checks have ordered callbacks.** A cycle/depth failure occurs only after the parent-loop tick at 4220. Raising from a cached invalidity marker before that tick can replace a callback's original exception with a ReferenceError. Conversely, a fast path for world that returns before `_incoming` skips the original callback entirely.

For the first counterexample, a native-shape precheck can choose fallback. Its placement still matters: adding a new cache callback before the original offset read can itself change which exception occurs first. Restarting all of `_ancestry` after `_incoming` already ran repeats its callback/cache effects; a fallback design must account for that explicitly rather than call it a free replay.

## Fair assessment of possible authority strategies

**Dependency-local readmission is possible in principle.** It need not scan all unrelated object geometry or every graph field on every carrier. If the original incoming map remains authoritative for the call, the descriptor needs the traversed source fields, relevant site-membership decisions and their exact ordered dependencies. A whole-graph scan on every use is not an automatic lower bound.

For a pathwise cache that separately rereads and funds every replaced parent step, however, the saving in this charged loop is consumed by its own admission before lookup/insertion/eviction costs. Moving a multi-record loop into one uncharged signature comparison is not a proved saving; the adopted M1 rejection explicitly forbids hiding optional work in an existing group tick (`docs/engineering/OK-DEC-COMPARE-M1-0.1.0.md`, consequence section). This is conditional on that particular admission strategy, not an independent universal lower bound on all descriptor algorithms.

**A genuinely immutable or write-tracked graph could change the premise.** No such authority exists in the current source model. Adding it would require defining what remains authoritative when the exposed model changes, how setters/collection replacement/native bypasses are handled, how class dispatch is admitted, and how fallback preserves existing first errors. A new immutable tuple of graph fields proves its own contents, not agreement with the still-live model.

**Existing deferred source batching is not already available to setup.** Phase tables and endpoint phases are built at `reach_conformance.py:3555–3556`, before the certificate/key verification call at 3598. `_SourceBatch` in `reach_reference_plan.py` is a distinct provisional protocol with captured owners (61–97), precharged final receipt reads (172–186), final source and domain admission (188–239), and discard on failure (241–258). Moving setup under a similar protocol would require a fresh proof of early-error behavior, intermediate uses, temporary mutation/restoration and publication cleanup. It cannot be assumed from the existing per-key batch.

**Storage and replacement are real costs.** A source-only graph is not automatically a forbidden numeric cache, but it needs an explicit node/path/receipt bound and accounting for copied source fields and descriptor lengths. Existing `_Arithmetic.lookup/remember` charge, synchronize the live operand domain, promote entries, and evict from the 256-entry shared cache (340–362). Using that cache for descriptors can displace numeric entries and change downstream work; a fixed-downstream bound must state that assumption, or bound those consequences separately. A separate numeric-result cache is outside C062.

## Recommended closure

The narrow parent-walk proposal is a source-only NO-GO as a complete original-request remedy, even with ideal authority and zero replacement cost. Combine this review with the cost review's separately justified `_incoming` ceiling before claiming rejection of the broader ancestry helper. If that broader optimistic ceiling is also below the necessary future work, no conditional four-request attribution round is justified: further measurement cannot repair the established ceiling for that finite target.

Preserve the distinction between historical observations, derived upper/lower bounds, and unimplemented authority proposals. Do not claim all structural sharing is impossible, that source mutation always demands a full-graph scan, that callbacks are harmless, or that an implementation was executed. C061's independent axial rejection, original budget limits, unaccepted recordings, M1 rejection, held C035, and unresolved release/integration gates remain unchanged.

## Supplemental review: complete ancestry-helper ceiling

This supplement resolves the earlier request for a separate `_incoming` bound. It concerns the exact recorded native C061 setup executions, including their unchanged source, callbacks and operand domain. It does not assert that arbitrary future callbacks cannot mutate the cache or domain.

**Accepted: the complete ancestry-helper ceilings of 711 P11 ticks and 236 L03 ticks are conservative and sufficient for the finite NO-GO.** The conclusion remains conditional on a candidate preserving exact setup outputs and the downstream control paths, charge behavior and cache effects used by the future-work lower bound.

### Independently checked inputs

| Quantity | P11 | L03 | Basis |
| --- | ---: | ---: | --- |
| Returned phase calls, N | 60 | 24 | Original `reader-setup.json` phase spans |
| Parent-loop upper bound, V | 171 | 68 | Returned path argument proved above |
| Joints, J | 11 | 2 | Native source expansion, cross-checked against retained GLB metadata |
| Follows, F | 8 | 3 | Native source expansion, cross-checked against retained GLB metadata |
| Grips, g | 0 | 0 | All authored/retained joints are hinges; boundary metadata agrees |
| First phase entry shared tick | 76,329 | 66,749 | Earliest phase span entry |
| Last phase exit shared tick | 82,413 | 70,077 | Latest phase span exit |
| Enclosing interval, W | 6,084 | 3,328 | Last exit minus first entry |
| Precision / operand cap | 128 / 32,768 | 128 / 32,768 | Every phase input and coarse cache snapshot |

Source expansion is straightforward without executing the compiler. Each PlanarArm contributes two hinges and one mounting follow (`libraries/reach-parts.ok:22–25,41–53`). P11 uses two arms and three legs, one look hinge, and three eyes with one follow each (`libraries/reach-assets.ok:42–65,73–122`): J = 5*2 + 1 = 11 and F = 5 + 3 = 8. L03 uses one BenchArm, which adds the column and tool follows to its PlanarArm (`reach-assets.ok:10–39`): J = 2 and F = 3. The corresponding fixtures introduce actions but no extra joints/follows/grips. Exterior classes introduce no joints or follows. The retained reader-input metadata independently contains 11/8 and 2/3 joint/follow entries, with hinge-only joint states at every retained boundary. That cross-check does not accept either GLB as a valid recording.

The original capture records identify the external callback as native `ConstructionBudget.tick`, with its own `check` equal to null, and both source/work observers null at the reader entry. All recorded identity checks passed, including native dispatch, callback ownership, unchanged work limits and unchanged budget limits. `ConstructionBudget.tick` only increments the shared operation count and checks its limits when `check` is null (`construction.py:75–87`); it cannot temporarily narrow the independent operand cap. The native runtime's write to `ReachExecutionWork.max_operand_bits` is its initialization (`reach_numeric.py:55`), and no setup path mutates it. Thus constant-cap observations are supported by the exact callback/source path, not merely by equal endpoint samples.

### Complete `_incoming` cost for this native domain

For each ancestry invocation, `_incoming` charges g grip visits and one lookup. A miss additionally charges J + F relation visits and one remember. The sole additional reset charge in `_Arithmetic._sync_cache_operand_limit` occurs only if the stored operand cap differs (99–105). It does not occur in this unchanged domain.

Consequently, with M ancestry-owned incoming misses:

`complete ancestry ticks <= V + N*(g + 1) + M*(J + F + 1)`.

This includes the full called `_incoming` helper as well as the parent walk. It does not charge the candidate any construction, admission, lookup, storage or replacement overhead; granting all of it for free makes the rejection more generous.

### LRU writer review and P11 miss bound

The independent arithmetic cache has the constant capacity `MAX_CACHE = 256` (`reach_reference.py:28`). It is distinct from the production work object's `_cache`; the recorded work cache size/limit cannot substitute for this source fact.

The incoming key is constant across these calls because the same reference token is used and both grip sets remain empty. A successful incoming lookup moves that entry to the newest dictionary position; a miss followed by remember inserts it as newest (340–362). Starting from newest, eviction requires updates to at least 256 other distinct keys. Promotions of old entries count as updates: the proof is not restricted to fresh insertions. Duplicate updates can increase the work but cannot lower this distinct-key requirement.

All relevant direct mutations of the independent arithmetic cache were inspected:

| Writer | Charge and setup relevance |
| --- | --- |
| `_Arithmetic.lookup`, 352–362 | One tick at 354 precedes each hit promotion. |
| `_Arithmetic.remember`, 340–350 | One tick at 341 precedes each insertion/replacement/eviction. |
| Cartesian rotation direct lookup, 1336–1348 | Tick at 1341 precedes the promotion at 1345–1346; the additional key tick at 1337 is not needed for this lower bound. |
| Cartesian rotation direct remember, 1383–1392 | Tick at 1386 precedes the direct replacement/eviction/insertion. |
| `_PendingCursors.publish`, `reach_reference_plan.py:341–354` | This delayed writer is reached through plan evaluation, not the setup phase call graph. It cannot introduce writes precharged before the measured phase window. |
| Centered `_Guard.lookup/remember`, `reach_reference_center.py:282–315` | These belong to centered key proofs and are outside the setup phase call graph; they also contain their own charged boundaries. |
| `_SourceBatch.discard_cursors`, `reach_reference_plan.py:157–161` | Source-batch cleanup is outside this phase-table/endpoint setup interval. |
| `_Arithmetic` cache clear, 99–105 | Requires a cap change, excluded for these exact native calls. |

The setup sequence calls `_phase_tables` and `point_phase` before `_verify_certificates` enters `recording_source_batch` (`reach_conformance.py:3555–3556,3598;3456`). `_phase` itself calls ancestry, root poses, source basis, optional axial derivatives and joint laws (4821–4846); none enters the recording pose-plan cursor protocol. Ordinary `_pose_map` enters `recording_phase_poses` only when it has a non-null recording context (`reach_reference.py:2959–2967`). The setup phase path does not supply such a context. The collector observes high-level boundaries and restores its wrappers before original key work; it neither publishes source-cache values nor runs a nested product request.

There is no uncharged cache deletion, reset, bulk writer or pending publication reachable in this window under the recorded native callbacks. Each relevant LRU update therefore costs at least one shared tick. For every ancestry miss after the first, its necessary eviction updates lie in a disjoint interval after a previous incoming insertion/promotion and before that miss. All such intervals fit within W = 6,084. Other `_incoming` calls during phase work may promote or reinsert the key, which only makes the ceiling more generous.

`M <= min(60, 1 + floor(6084 / 256)) = 24`.

Thus P11's complete ancestry helper satisfies:

`V + N + M*(J + F + 1) <= 171 + 60 + 24*20 = 711`.

This is an upper bound, not a claim that 24 misses or 711 ancestry ticks occurred. The coarse snapshots' arithmetic occupancies remain below 256, but the adopted bound does not need a stronger inference from those occupancies.

### L03 bound without LRU assumptions

Grant a miss on every one of L03's 24 calls. With g = 0 and J + F = 5:

`complete ancestry ticks <= 68 + 24 + 24*6 = 236`.

This count does not require the P11 eviction argument. The same constant-domain premise excludes extra cap-reset ticks.

### Consequence

Starting from the 100,000 successfully admitted original ticks, and granting complete free removal of the bounded helper work, the unchanged downstream paths still require at least:

- P11: `100000 - 711 + 1260 = 100549`.
- L03: `100000 - 236 + 594 = 100358`.

The 1,260 and 594 future ticks are the separate mandatory key/interval charges from the retained refusal frontiers, not a claim about full tail cost. Both conservative lower bounds exceed the unchanged cap. No new ancestry capture round is necessary to decide this finite isolated setup remedy: even the optimistic complete-helper ceiling is insufficient.

This supplement supersedes only the earlier pending `_incoming` caveat. It does not certify an authority implementation, estimate actual complete-request cost, combine this target with other optimizations, or reject algorithms that change downstream work or cache effects. The source authority and first-error objections above remain applicable to any separately proposed implementation.
