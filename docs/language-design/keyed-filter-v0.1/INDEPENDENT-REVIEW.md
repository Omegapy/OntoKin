# Independent C083 decision and input review

**Reviewer:** `c083_review`, assigned separately from input authoring, runtime implementation and producer tooling.  
**Date:** October 31, 2026.  
**Disposition:** Accept the exact reviewed decision and independently authored inputs for experimental implementation after publication of their freeze. Runtime behavior, destination checks, integration and complete release acceptance remain later gates.

## Exact reviewed content

The decision is `OK-DEC-KEYED-FILTER/0.1.0`, based on C082 main `753bed5ff53c5a11bffe1913b9ceddb9b9624011`, tree `4577451cde3552da35d163d9278cbce9eba12339`.

| Reviewed file | SHA256 |
| --- | --- |
| `ADOPTION.md` | `b8addbbacebe6966ec309ddde275ebaf96639d8365c27815fda844f81fd9b925` |
| `ontokin-keyed-filter.ebnf` | `f583533989cceb1c047d77d5172360abfd5fe43114ff4faa07033dc3a0e1e2c4` |
| `examples/keyed-filter/expected.json` | `9096ec9b97e0d038609a46746da751fa77b7141247476c72523c256433e21120` |
| `examples/keyed-filter/workflows.json` | `0518966f5ab87a0dadc88cb8d665e552018aae23013627c7eb29e924f524026c` |
| `examples/keyed-filter/delivery-comparison.json` | `b168977b7c67866f7e9587ab7769e155aa8f57248d7a763efba186539570e01d` |
| `examples/keyed-filter/supplied-byte-adversaries.json` | `fd8dd7de89670b7686fbe80e31a6c9ffa12da1b1b650c9b2c3cf7cef7a7e5fc7` |
| `agent-v0.16/request.schema.json` | `a8698d63693d369ae59bc13c7c9451ba4943a3ae876e1669a1e7e8e9d7cc1339` |
| `agent-v0.16/response.schema.json` | `2348857bd64db17ac263db12bf01a66e9ba85d9bc707ef2bfa49b2b14884e213` |
| `agent-v0.16/diagnostic.schema.json` | `f03ca251bd71ad09a113695f34121d92a225332671bdf661a72358abde696838` |

The review's external exact-input record inventories all 452 substantive files / 953,684 bytes present before adding this review and the self-excluded freeze manifest. Its inventory digest is `8b5ccf04a4e48652254a6696ab98a4b3d7a9969c9c0998f33188ebbc347e2181`, calculated over the recorded sorted file array with compact sorted-key JSON. The final freeze must preserve these bytes. This review does not authorize silently changing a frozen input after implementation begins.

## Semantic review

I reviewed the complete decision and grammar, the exact C082 continuation requirements, and relevant inherited parser, compiler, dependency, cache and inspection paths. `filter_keyed<T>` has an explicit, exact resolved `Keyed<T>` input/output contract. Alias-equivalent types remain equivalent; filtering adds no Int/Real widening or leaf conversion. The predicate returns strict Bool. The two read-only locals are scoped to that predicate and cannot shadow existing visible names.

The input is evaluated once and admitted before predicate traversal. Every admitted key is visited in canonical ASCII order, including keys whose predicates return false. Empty input performs static checking with unknown typed locals but executes no dynamic predicate. Captured local payloads are masked for static checking. Global names, access, units, constructor signatures and pure-call-cycle checks remain in force. Static checking does not invent a sample value or execute an empty predicate's value-dependent domain.

The output is an immutable subset. Surviving keys, typed values and original input-entry origins remain unchanged. Source reordering preserves mathematical membership and stable identities, while source hashes still identify the actual authored bytes. Missing generated keys retain ordinary reference/override failures after shape resolution. Existing runs and artifacts stay bound to their original revision.

The important new obligation is retaining every executed predicate's actual dependencies, forbidden generated-view taints and derivations even when its entry is dropped. Aggregate origins must reach generated occurrences when the filter appears only in a condition selecting an unchanged plain keyed value. Detached wrappers must prevent contamination of the original input, another property or an equal-valued sibling occurrence. Nested map/reduce operations must retain filter origins even if their later bodies ignore the original values. The reviewed decision states these obligations explicitly.

Per-entry traversal, fresh bindings, predicate work, surviving-value copies, final materialization, static masking and provenance work share current cumulative authority. `keyed_filter_iteration` is a real cancellation checkpoint. No persistent membership cache is added. Defaults, independent host ceilings, reducing caller caps, inherited resource limits and failure atomicity remain unchanged.

The .16 source, Agent and recorded destination bindings are explicit. Earlier declaring units and defaults keep their meanings. The three .16 schemas preserve the rebound .15 structures and existing map/reduction fields. Their new filter record is closed and requires exactly `expression`, `input`, `predicate` and canonical resolved `element_type`. Only the corresponding read-only derived-value and generated-source projections are added. Schema validity is separately recorded with the pinned verification environment; it is not an executed Agent claim.

## Independent input review

The source inventory fixes **141 expected outcomes: 75 intended successes and 66 intended refusals**. These are predetermined requirements, not .16 execution results. I reviewed the authored case definitions and representative concrete source, the complete operation/dependency expectations, all lifecycle requirements and the complete delivery comparison/adversary contracts.

The corpus covers empty/singleton/256/257 inputs; keep-all/drop-all/mixed membership; reordered, case-sensitive and boundary keys; all 24 inherited leaf families; exact type/alias behavior; non-Bool predicates; unknown locals and selected domains; names, access, units, frames and cycles; imported helpers and declaring-unit limits; missing generated keys; invalid resulting geometry; source/image closure; and current resource authority.

High-risk composition cases include dropped-entry map/reduction origins, filter-then-map/reduce with discarded values, empty downstream collections, a conditional selecting plain input, generated conditional origins, equal-valued plain/filtered occurrences, repeated helper/guarded reads and forbidden generated inputs despite drop-all. Imported reduction provenance is anchored to its original module. The nested-filter expectation orders the inner derivation before the outer derivation, separately from the lexical source inventory.

A separate reviewer script imported neither the product parser nor the author's scanner. It passed **4,122 checks** over all 141 source identities and 75 control identities, **574 source-location references**, and **76 filter-record span/type checks**. It recomputed canonical bundle revisions from the actual file bytes, checked UTF-8 span boundaries/source revisions, and independently tokenized valid filter expressions to verify their exact expression/input/predicate spans. Repeated references are included in these check counts; they are not unique test or release totals.

All 75 valid cases have independently authored explicit .15 controls. I reconciled each current control's complete canonical manifest and program revision with the successful unchanged-C082 preflight records: 72 controls in attempt02 and three added controls in additional03. Both records identify the exact clean baseline before and after execution. Current control bytes therefore match executed controls even though the later expectation document also adds .16-specific requirements. No .16 candidate runtime was used to derive the expected results.

The representative panel mathematics is direct. Before repair, each group has widths 1 m and 2 m, with total 3 m. Raising only `first.minimum_width` to 1.5 m removes `first.panels["left"]`; its surviving right panel remains 2 m wide and the sibling remains unchanged. Raising that parameter to 3 m removes both first-group panels. Rectangular-prism bounds, triangle counts, areas, volumes, UV corners and five recorded pose times follow the authored dimensions and motion. Library and exact PNG bytes remain pinned. The .15 controls spell out the same memberships without filtering.

The ten workflow contracts require actual scoped repair, rollback, stale revisions/cursors, reopen/retry, changed-payload refusal, current host policy, caller/output reductions, cancellation during real filtering, interrupted artifact publication and bounded complete source/asset/artifact retrieval. Complete BIN and raw JSON/framing comparisons permit only enumerated independently validated metadata paths. Twelve supplied-byte adversaries cover geometry, UVs, images, material/sampler values, identity, motion, revision/provenance, unknown metadata and framing. Pinned native readers and direct capture inspection remain required.

## Review corrections and remaining gates

The initial authoring attempt and review findings remain preserved. Before freeze, corrections fixed a reserved-name test whose invalid syntax masked the intended binding error, numeric diagnostic anchors that selected the version header, a control that supplied a PNG after removing its declaration, and canonical Point3/quantity type spelling. Added expectations make imported reduction origins, nested evaluation order and aggregate-to-generated propagation explicit. The initial control preflight's two failures and the original draft archive remain evidence; they are not relabeled as passes.

No blocking semantic or input defect remains in the exact content identified above. Publish the independent freeze before runtime edits. Then implement the adopted scope and run all required source, Agent, supplied-byte, native/browser, immediate-predecessor and applicable inherited checks. Actual runtime failures must remain visible; a future defective frozen case requires a separately identified correction.

This approval closes only decision/input preparation for the bounded experimental increment. It does not establish implemented filtering, successful Agent or destination behavior, integration, complete feature release, compatibility roles or full-product acceptance. Original28 remains failed overall at 24/28, the recorded remaining gates stay open, and all GOAL domains remain part of the project.
