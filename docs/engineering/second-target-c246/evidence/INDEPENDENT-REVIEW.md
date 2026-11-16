# C246 independent review — held source approved

**Disposition: APPROVE_HELD_SOURCE_STATIC_AND_INERT_ONLY.**

Reviewed clean commit: `55e7d2576dd29e65a22db79f2207303570e5a1e3`.  
Tree: `62197aa149025af8c8e2b849af8f0b386203c433`.  
Environment: Linux x86-64, CPython 3.12.14. No separate machine or operating system is implied by the independent agent role.

This approves the finite source component selected by adopted C244. It does not approve native execution, certify GDScript parsing, or complete R07. Exact file hashes and the final clean-source observation are in `FINAL-REVIEW.json`.

## Evidence and executed checks

| Check | Result | What it establishes |
| --- | --- | --- |
| Independent CPU-model adversarial cases | **730 passed; 18,357 assertions; zero failures** | The modeled identity/phase/failure predicates for the supplied fabricated records |
| Binding checker independently rerun on the frozen source | **122 passed** | Exact bytes/SHA-256/Git blobs for 21 upstream source/API files, nine authority documents, original GLB associations and selected lexical boundaries |
| Original independent pin review | **Nine engine sources and six unchanged authority documents matched** | Historical source argument and preservation before implementation review |
| Independent original GLB decoding | **18 mesh-bearing roots, five meshes, exact locked tuple, no extensions or skins** | The same read-only 185,236-byte fixture and SHA-256, without re-export or native import |
| Native-facts specialist static review | **APPROVE_HELD_SOURCE_STATIC_ONLY** | Reviewed helper hash `1fb4caeb9e36756c03b4cec0072c8a3a1decde0a554798c87a0895cf8ccd29f9`, selected API/loop boundaries, and explicit limits |
| GDScript parser/native/product/aggregate | **Not run; zero starts** | No native behavior claim follows |

The final model run records the exact commit, clean status, interpreter/platform, runner hash, complete case results and unchanged source hashes before/after. The provisional earlier run remains preserved separately and is explicitly identified as an evolving worktree run; it is not substituted for this final result. The binding checker is authored code rerun independently. Its lexical checks supplement manual review; they are neither a GDScript parser nor a complete static analyzer.

## Source boundary reviewed

`observer.gd` extends `GLTFDocumentExtension`, has no mutable instance observation state, and declares only `_import_node`. Its four native arguments and Error result match the pinned dispatch source and XML. It delegates to the external registry. No project, loader call, extension registration, process launch or auto-running native entry point was added.

`registry.gd` keeps one terminally bound session keyed by state instance ID while retaining and comparing the exact `GLTFState` object. Unknown, duplicate, reused or poisoned bindings fail. A global fault poisons active sessions, and unknown callbacks before binding prevent later binding. The single-use limit is stricter than accepting arbitrary concurrent/reused states; it matches this one finite experiment. Neither callback return codes nor a returned root are accepted as sufficient evidence.

`session.gd` guards all loader-map access within the preconversion capture phase. It checks exactly 18 GLTF nodes, the inverse and forward map, the actual GLTFNode association, each locked mesh index, distinct original native identities and native class. It records a root snapshot before its direct root guard, then each product snapshot before that node's direct flags-zero subscription. The root guard is separately recorded from the 18 product subscriptions and has only a fatal outcome.

Replacement callbacks use the bound source index and original integer identity; they do not recover an old node pointer or call the loader map. Every known old identity is marked retired before later phase/edge refusal, so cleanup cannot resolve an observed retiring original even on a failure path. All original captures/subscriptions must complete before replacement. Unknown/cross-index/repeated edges, duplicate new identities, old/new intersections and root aliases refuse. Arbitrary callback and replacement ordering is allowed.

Only the explicit synchronous caller-return notification enters final capture. The source requires the same live nonmesh root with no parent, complete 18-edge accounting and a final traversal with 18 distinct live `MeshInstance3D` identities matching the observed new-ID map. Traversal supplies membership; the original live map plus replacement edges supply source identity. The code rejects unconverted or scripted scene members and performs final fact snapshots after return. It has no stale postconversion map access.

The strongest successful state is `CHAIN_COMPLETE_RAW_PENDING`. Receipts keep execution admission and native acceptance false and diagnostic coverage unestablished. Any recorded failure permanently blocks that component state. Cleanup begins only after caller return, skips observed retired originals/root, and resolves only still-valid unretired IDs to remove its own connection if present. This is inspected cleanup source and modeled ID eligibility, not a native cleanup attestation or child-process cleanup implementation.

`native_facts.gd` captures typed detached metadata, node/native identity, parent/owner, scripts, outgoing and incoming connections, and resource identity/metadata. Unsupported Variant types/custom or invalid callables and unexpected scripts refuse instead of being omitted or turned into apparent equality. Native resource arrays/material values/evaluated poses remain outside this component. The shared first-error/counter logic stops recursive and outer inventory traversal; the stated bound is visited records, not string bytes or allocation performed inside a native API. The specialist review independently inspected this helper and its exact pinned APIs.

## Independent adversarial coverage

The 730 cases include 24 deterministic randomized callback/replacement/final orders with independently relabeled disjoint identities, checking every source-edge association, final inventory, phase barrier, detached metadata and receipt behavior. Per-node mutations cover wrong map directions/GLTFNode, mesh/count/class/script, native JSON integer/Boolean/string/fractional/nonfinite values, invalid IDs, failed subscriptions, signal flags, missing originals, cross-index edges, aliases/cycles, repeated/missing edges, wrong/dead/outside final nodes, duplicate finals and incomplete censuses.

Further controls check terminal poison before/after binding, two distinct state objects with deliberately equal Python values, late callbacks without additional modeled map reads, premature cleanup, failure-path retirement, root replacement, duplicate return and permanently false admission/acceptance. Metadata controls distinguish Boolean/integer/float values, refuse unsupported/cyclic/nonfinite data, prove detachment and observe immediate small-budget recursive unwinding.

The model receives fabricated liveness and membership facts. It does not obtain them from Godot. Its synthetic metadata types are narrower than GDScript Variant, and its cleanup function computes modeled eligible IDs rather than disconnecting real signals. These limits prevent the test count from being presented as native implementation proof.

## Findings corrected before approval

1. **Native JSON mesh type.** The initial TYPE_INT-only check contradicted the pinned parser's double numeric representation. Exact parser/GLB/source inspection established the mismatch. The corrected source requires finite exact TYPE_FLOAT mesh values and preserves their native type/value without truncation. Full pinned `json.cpp` and `JSON.xml` plus retrieval and hash evidence are retained under `upstream/`.
2. **Failure-path retirement.** Known originals are now marked retired before any subsequent replacement guard/refusal, including callbacks arriving after a fatal event.
3. **Original connection completeness.** Both incoming and outgoing connections are now captured. This matters because pinned `Node::_replace_connections_target` operates on incoming persistent connections.
4. **Snapshot traversal cap.** The initial implementation could append refusal markers while continuing the rest of a large container. The corrected shared first-error/counter logic stops traversal and retains explicit partial refusal; failed dictionary keys do not cause value reads.

Detailed initial findings remain in `FINDINGS.md`. The helper reviewer separately retains initial/refused and corrected source hashes, API extracts and its final receipt.

## Publication note and remaining gates

Root identified one documentation correction in `RESULTS.md`: replace “no product/root replacement” with “no product mesh root or synthetic-root replacement.” Eighteen descendant product replacements are required. This wording fix does not change the approved code; root owns the publication candidate and must preserve the reviewed code hashes while applying it.

No residual code blocker was found for **held-source publication**. Actual GDScript syntax/binding, installed callback delivery, native signal/pointer behavior, original metadata truth, complete engine/extension diagnostic capture, exact candidate lineage, full raw arrays/materials/poses, envelope emission, rendering, persistence, hard resource limits and durable reservation remain open. Current binary-presence evidence is root's separate read-only observation and grants no execution authority. The source remains incapable of claiming native acceptance through its receipt fields.

The next scope may implement one separately bounded held mesh-array snapshot component only after root completes verified publication and saved handoff delivery. This reviewer starts no next component and makes no remote writes.
