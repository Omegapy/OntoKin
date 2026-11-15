# C244/0.2.0 adoption: finite observation-chain identity boundary

**Decision: adopt the independently reviewed design for the prospective finite
experiment. Effectiveness requires verified integration of this record into main.**
The actual merge and checks are recorded in [RESULTS.md](RESULTS.md) and its
integration receipt. A draft branch alone does not amend a contract.

This record governs the current disposition of the unchanged [proposal](DECISION.md).
The proposal's historical draft status and statement that its author lacked an
independent subagent remain preserved as evidence of that earlier stage. C245
supplies the missing independent review and integration; it adds no native implementation.

## Exact decision adopted

Reviewed draft: `8264db6e36b0c6118cf5b7ab2e41724569f72d90`, tree
`c62c61d0287d5d006d53f653a3df8267289d547c`.

| Reviewed file | SHA-256 |
| --- | --- |
| DECISION.md | `75fa47604060598bbc803dbec3bf464699e3e363fabcb2712c19bb7998d0b8e1` |
| test_decision.py | `73acb9680e75148d875d441ea2aace4505cec7985ad282f9792240d77006cb67` |

The following amendments take effect together for the original 18-node fixture:

1. [C220 section 3](../second-target-c220/PLAN.md) and
   [C241 section 3](../second-target-c241/CONTRACT.md) permit exactly one
   observer-only `GLTFDocumentExtension._import_node` override. Other virtual
   methods retain their pinned defaults. The built-in converter and original
   source/GLB inputs remain required. Direct, nonpersistent `Node.replacing_by`
   subscriptions record identity transitions; mutable state belongs to an
   external session keyed to the exact `GLTFState`. No product-node script,
   source identity injection, geometry/resource change or alternative converter
   is permitted.
2. C241 section 4 checks both directions of the live original loader map before
   conversion, then requires a complete observed replacement chain and final
   live scene membership. For this fixture the chain has exactly one descendant
   replacement per original node. Postconversion calls into the stale map are
   prohibited. The external registry does not repair `GLTFState`, and
   process-local instance identities are not a reopen identity contract.

Every additional requirement in the reviewed proposal remains mandatory:
phase-local native snapshots before observer connections; exactly 18 distinct
original nodes with the locked mesh associations; direct flags zero; complete
event accounting; refusal of a product mesh root or root replacement; final
observations only after generation returns; no retired-node dereference; and an
external fatal latch with independently established engine/extension diagnostic
coverage. Unknown coverage blocks execution admission. Source-retained metadata
may be added only after sealing raw native observations.

The original C220/C241 files stay unchanged as historical authority. This
versioned record supplies only the two explicit exceptions above. Their other
requirements, all C221–C239 schemas, tolerances, source bindings, useful images,
resource limits, two-start ceiling and the strict Blender-normal failure retain
their exact meanings.

## Why this decision is eligible

Two actual independent subagents reviewed nonoverlapping aspects in the same
Linux environment. The design reviewer verified the source-supported observation
window, all nine pinned engine sources, six unchanged authority documents and
the original fixture. The controls reviewer passed the exact 44 author methods
and 319 independent cases: 14 valid traces and 305 expected refusals. Detailed
[review and immutable evidence](REVIEW.md) distinguish those results from the
earlier author's self-audit.

This evidence supports a finite design choice. The embedded candidate revision
still differs from the examined engine revision, and the pinned executable is
absent in this review environment. Callback execution, native metadata truth,
installed binding, rendering, persistence, hard resource enforcement and R07
are not established. No native/version/import/export/render/save/reopen,
source evaluation, product run or aggregate was started.

## Following boundary

Only after verified integration and saved handoff delivery may a separate scope
implement the narrow hook and external session registry as held source.
[NEXT-TASK.md](NEXT-TASK.md) fixes that boundary. No native reservation or
execution authorization follows from this design adoption.
