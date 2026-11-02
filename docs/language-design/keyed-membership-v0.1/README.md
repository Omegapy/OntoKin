# Experimental bounded keyed membership

The [reviewed specification](SPECIFICATION.md) defines `has_key(collection, query) -> Bool` for explicit source `0.21` / `keyed-membership-0.1`, Agent/0.21 and recorded GLB/0.21. The separate adoption record and frozen input manifest establish the implementation preconditions. Validation and integration are subsequent observations; this guide does not certify complete feature release or the full product.

## Optional component overrides

Membership lets a reusable component select a sparse per-instance override before performing the existing indexed lookup:

```ontokin
public param widths @ "widths": Keyed<Length> = keyed<Length>{};
public derive panel_width @ "panel-width": Length =
    if has_key(self.widths, "left") then self.widths["left"] else 1[m];
```

The ordinary conditional evaluates only its selected branch dynamically. A valid absent key returns false, so the fallback is selected. An unguarded absent lookup keeps its existing name error. Both arguments to `has_key` are still evaluated eagerly, left to right. Invalid entries cannot be hidden by an early matching key.

The same Boolean question for an authored leaf collection can already be expressed with `reduce_keyed` and a conditional. The new operation provides a direct signature and read-only membership in existing generated `Keyed<Ref<C>>` views, while retaining access, dependency and generated-shape restrictions. No measured performance or authoring-effort improvement is claimed.

## Types, key domain and bounded work

The first argument is an immutable admitted Keyed collection; the second is exactly String. Queries retain the stable-key grammar `[A-Za-z0-9][A-Za-z0-9._-]{0,63}`. Invalid queries fail explicitly. Membership compares canonical keys without recomputing or comparing payloads, and validates every input entry before scanning.

At most 256 entries are admitted. A successful known call adds `n + k + 3` dynamic operations: one admission, `n` input checks, one query check, `k` canonical comparisons and one publication. Empty input costs 3; a last or absent query in 256 entries costs 515. Each stage uses the original admitted shared execution ledger, original deadline, current host authority, caller caps and cancellation callback. The operation does not consume computed String byte reservations.

Abstract or unknown well-typed calls return unknown Bool without a dynamic membership scan or literal query-domain check. Static syntax, access, type, purity and cycle checking remains mandatory. Actual invocations are not folded into constant or parameter caches. Existing immutable binding reuse retains its established meaning.

## Declaring versions, provenance and delivery

Only a declaring `.21` unit reserves bare `has_key`. Earlier user functions, locals and import aliases keep their original meaning; qualified older helpers remain available. `.21` inherits the explicit `.20` bounded String addition. Earlier source versions and ordinary defaults retain their own semantics.

True and false results preserve actual collection and query dependencies, generated taints, and inherited map/reduction/filter/merge/zip/rekey contributor records. No new writable identity, lineage family, mutable container, type constructor or physical authority is added.

Agent/0.21 retains the twelve operation shapes and immutable bundle/files `0.2` transport. Its independent store is `keyed-membership-program-agent.sqlite3`, schema `ontokin.keyed-membership-program-agent-store/0.1`. Recorded GLB/0.21 retains geometry, materials, images and recorded motion; explicit source and revision metadata identify the new binding. Actual engine import, live destination physics and measured authoring benefit remain separate requirements.

The [utility review](review/UTILITY-REVIEW.md), [contract review](review/CONTRACT-REVIEW.md), [full project goal](../../../GOAL.md) and [retained gates](../../engineering/keyed-membership-2026-11-02-c088/RETAINED-GATES.md) retain the decision's scope and limitations.
