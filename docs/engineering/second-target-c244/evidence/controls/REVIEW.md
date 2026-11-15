# C245 independent review of C244 inert controls

**Outcome: APPROVE for the finite synthetic-control scope.** No blocking defect
was found in the identity, inventory or phase predicates exercised here. This is
an independent review of the exact published C244 draft. It is not permission to
run Godot or a claim that the proposed observer has been implemented. Integration
also requires the separate design review and the repository's main lease rules.

## Source and review boundary

| Binding | Value |
| --- | --- |
| Reviewed commit | `8264db6e36b0c6118cf5b7ab2e41724569f72d90` |
| Reviewed tree | `c62c61d0287d5d006d53f653a3df8267289d547c` |
| `test_decision.py` SHA-256 | `73acb9680e75148d875d441ea2aace4505cec7985ad282f9792240d77006cb67` |
| `DECISION.md` SHA-256 | `75fa47604060598bbc803dbec3bf464699e3e363fabcb2712c19bb7998d0b8e1` |
| Execution | Linux x86-64, CPython 3.12.14 |
| Source state | Clean before and after; both reviewed file hashes unchanged |
| Native, product or aggregate starts | Zero |

The reviewer read repository `AGENTS.md`, the current GOAL/STATUS sections and
the relevant C241 and C243 capture contracts. The review was performed by the
separate `controls_review` subagent in the same available Linux environment.
It does not imply a separate machine or operating system.

The proposed contract requires exactly one observed replacement for each of the
18 locked source nodes. A complete chain in this fixture therefore has an
original identity, one old-to-new edge and one completed live final observation.
The predicate is deliberately not a general multiple-replacement observer.

## Executed checks

The author's exact 44 methods pass with no skips or failures. The independent
[review runner](adversarial_review.py) adds **319 cases: 14 valid traces and
305 expected refusals**, all passing without exceptions. The complete case
records and source/environment bindings are in [RESULT.json](RESULT.json).
The [author log](author-controls.log) and [independent log](adversarial.log)
retain actual execution output.

The additional cases address risks that a successful example or an isolated
field change could miss:

- Twelve deterministic permutations change actual capture, replacement and
  final-observation sequence values independently. The resulting valid traces
  pass even when source indices arrive out of order. Reordering only the stored
  arrays, as the author's reverse-order test does, would not establish this.
- A complete bijective relabeling of original and replacement IDs passes.
  Numeric ID order is not a source-identity rule; the observed edges are.
- For every source index, coordinated edits make two source occurrences share
  an original ID or a final ID while keeping individual edge/final records
  superficially consistent. Every such trace refuses. The same holds when a
  replacement is made to alias any other original identity.
- All 18 source positions refuse cross-index old-ID edges, incorrect inverse
  map joins, a replacement before another node has subscribed, and final
  observations before `generate_scene` returns.
- Each of the three inventories rejects Boolean indices at every position.
  Additional malformed JSON-like values cover numeric fields, flags, origins,
  root markers, live/member markers, native class, return phase and fatal status.
- Missing, empty, mapping-shaped and text-shaped inventories refuse.

The runner independently decodes the JSON chunk of the original GLB; it does not
evaluate source or regenerate/export a fixture. Its 185,236 bytes reproduce
SHA-256 `05ebe856d3fdb96dce4b6aa55906be5ae67501bcaede9112abc30b703905b5d8`.
All 18 node-to-mesh pairs equal the model's tuple, the source scene lists all
18 nodes and there are five distinct mesh indices. The full decoded pair list
is retained in the result.

## Predicate assessment

The source-index checks in `test_decision.py` lines 48–59 require exactly the
complete index set in each inventory. Lines 63–77 bind the locked mesh pair,
both original map directions, one original edge and the final node identity.
They also require the direct/nonpersistent flag value, permitted root marker,
positive original/replacement IDs and explicit final live/member conditions.

Lines 78–87 establish local capture-before-subscription order, replacement
before return and final observation after return. The global condition requires
all subscriptions before the first replacement, and unique sequence values
prevent ambiguous simultaneous event positions. The old and new identity sets
are each injective and disjoint. Under this fixture's one-edge-per-index rule,
those conditions also exclude cycles and reused retired identities.

These checks provide a coherent consistency model for the decision. They do
not infer source identity from traversal, geometry, mesh sharing or numeric ID
order. Nothing in the tested finite model requires a contract change or repair
before integrating this documentation/inert-control increment.

## Limits retained for implementation review

The function accepts fabricated Python dataclass records. It is not an input
decoder, security boundary or native evidence verifier. The adversarial domain
here uses ordinary Python/JSON-like scalar and container values; custom Python
objects with overloaded comparison behavior are outside this finite record
model. A later implementation must separately enforce its concrete serialized
schema and native API boundaries.

The model does not establish that an original node was actually live, that
the recorded loader/mesh associations came from the installed engine, that
`replacing_by` ran with the declared connection flags, or that final metadata,
geometry, materials and poses were captured faithfully. It also does not
implement stateless extension registration, session binding, diagnostic
coverage, a persistent fatal latch, resource enforcement, bounded cleanup or
raw-capture sealing. Those omissions are explicit in the draft; they remain
execution gates rather than being counted as passed tests.

The existing unproved build lineage, rendering route, persistence contract,
two-start admission protocol, R07 and strict Blender-normal failure retain
their prior dispositions. No repository file, source binding, tolerance or
historical evidence was changed during this review.

## Reproduce

With a fresh copy of the exact repository revision and the extracted supplied
C244 handoff, run the following. Keep the output directory outside both inputs.

```sh
python3 -IB adversarial_review.py /absolute/OntoKin /absolute/source-handoff /absolute/review-output
```

The runner verifies the exact commit/tree, reviewed hashes, original fixture,
clean source state and source stability while retaining all results. It calls
only Python for the author's inert test suite and read-only Git commands.
