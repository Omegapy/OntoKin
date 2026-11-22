# P13: completeness is an independent review gate

Decision: `ontokin.c271.review-runtime-boundary-decision/1` (`P13-RB-001`).
State: proposed; frozen for independent review. Only a separate Director adoption record tied to the accepted candidate manifest can adopt it.

## 1. The precise defect

P12 stopped at `P12-N57-POLICY-BINDING-001`. In P11 candidate004, `P01_nonselecting_base` and `N57_source_variant_unknown` differ only at `/variant_review/completeness`: `synthetic_declared_complete` versus `unsupported`. Their other logical observations and bindings are identical. Neither supplies actual operational plan bytes, an actual expected plan digest, actual loader/source-review descriptors or a source-completeness argument. N57's unchanged oracle nevertheless requests `CHI-UNSUPPORTED / variant_review / LP-VARIANT-SEMANTICS`. [E01–E03, E07, E10, E11]

The proposed operational variant document has exactly four keys: `schema`, `loader`, `source_review`, `suffixes`. P11 assigns suffix completeness to independent source review and explicitly says that no field constitutes approval. Existing source checks a nonempty, hash-bound rationale without interpreting its contents as a completeness verdict. Authenticating particular review bytes therefore does not establish that those bytes justify a complete suffix set. [E04 §§3,5,7; E05; E12; E13]

These observations do not define a production predicate that can distinguish P01 from N57. Creating such a predicate from their synthetic label would invent authority outside the specified operational input.

## 2. Selected boundary

**Actual-loader suffix completeness is an independent-review-only prerequisite for adopting and attempting an operational plan.** It is not a runtime approval/refusal selector. A reviewer must assess the source-backed argument for the exact loader and platform; the Director must withhold the operational plan's adoption and execution when that evidence is missing, rejected or unresolved.

The consequence is a workflow decision: the proposed host/profile is not eligible to proceed. It is not a fabricated product exception, `policy=None`, a `REJECTED` product-state observation or a successful runtime test. P11's statements that unjustified completeness makes the profile unsupported are read at this external gate. Its machine checks for mismatched inventory, changed bindings, candidate entries and other observable faults retain their original runtime refusal obligations. [E04 §§3,5–8]

The future private policy constructor remains limited to machine-checkable, plan-dependent subject/context conditions. It must not parse the rationale for an approval word, consume a completeness flag, receive a review-status Boolean, or interpret a caller-supplied synthetic label as authorization. Both author-runtime parser sites and resolution checks still use the same machine-bound policy under the P11 ordering. This clarification does not propose an executable policy constructor. [E04 §7; E06]

Runtime alone cannot establish or enforce the honesty or sufficiency of this independent review. The expected plan digest identifies the intended bytes; it does not prove a reviewer approved their meaning. If a later requirement demands a runtime-enforced approval boundary, it needs a separately reviewed source-bound contract. This decision supplies none. The existing source explicitly treats independent review honesty as a trust boundary. [E12]

## 3. What a real independent review must establish

The existing review obligation remains strict. Before an actual operational plan can proceed, its independent record must identify the reviewer and exact reviewed inputs, explain how the exact loader bytes relate to the inspected source/build or implementation evidence, and justify the complete finite suffix union for the supported platform. The argument must address compiled/default, hardware and TLS alternatives, including why any omitted alternative is impossible in the admitted setting. It must bind that conclusion to the actual variant inventory, the exact rationale and the corresponding plan identity. Changed inputs require a new review. [E04 §§3,5; E14]

A generic glibc reference, a version string, matching descriptors, a nonempty rationale, a synthetic positive or a record that merely says “complete” cannot satisfy that obligation. The reviewer must inspect the source argument and its bindings. Missing evidence keeps this gate unmet. These are review requirements for future evidence, not a new operational JSON schema, a machine-readable approval protocol or evidence supplied by P13.

Both supplied P01/N57 contexts lack that actual evidence. P01 remains useful as a finite synthetic private-rule positive; its positive expectation is not an independent source review. N57 illustrates the unresolved review obligation. Neither context is an eligible operational plan, and P13 does not invent a real positive completeness-review case. Actual H0 source/loader/closure reconstruction remains a later unmet gate. [E03, E05, E10, E11, E14]

## 4. Explicit version and applicability change

P11's decision, original control contract, all 97 original expectations and all fixture bytes remain immutable historical records. P12's blocker and both author/reviewer findings also remain unchanged.

On adoption, this P13 decision and `ontokin.c271.p13-control-mapping/1` supersede only the **future runtime applicability of N57's source-completeness refusal**. They do not rewrite that oracle or declare it satisfied. The new mapping has 96 unchanged future runtime-primitive obligations and one independent-review-only obligation. [E07, E08]

| Original case | Original record retained | P13 applicability after adoption |
| --- | --- | --- |
| P01 | Synthetic private-rule acceptance; no host qualification. | Same future private-rule expectation under its declared finite synthetic model. No source-completeness approval is inferred. |
| N57 | Refusal with `CHI-UNSUPPORTED`, `variant_review`, `LP-VARIANT-SEMANTICS`; all other fields unchanged. | Historical runtime oracle, not executable as a distinct refusal under this boundary. Review completeness must be assessed externally; the supplied synthetic context does not establish it. |
| Other 95 | Exact original inputs, routes and expectations. | Unchanged future runtime-primitive obligations, subject to all existing scope limits and later faithful-adapter review. |

All 97 cases must remain accounted for. A future report must distinguish runtime results from the external review obligation. It must not describe N57 as passed, turn a skip into a pass, claim the original unamended 97-runtime-oracle criterion was met, or combine static review checks with a runtime pass count. An implementation that claims P11 alone must still report the old N57 obligation unresolved. A later implementation using P13 must cite its exact adopted version and the 96-plus-one applicability change.

The independent design review must expressly accept this changed allocation of responsibility. Director adoption must identify the decision/mapping versions, accepted manifest hash, actual independent reviewer and resolution of mandatory findings. Until then, P12's unresolved blocker remains the operative disposition. Design adoption can make a later implementation phase eligible for selection; it cannot itself authorize that phase, qualify a host or close C271.

## 5. Preserved operational and verification boundaries

No operational schema gains an approval or completeness field. P11's exact new plan/profile pair, four-field variant object, old plan/profile behavior, selected Python and Node pins, source/consumer contracts, default parser refusals, command shapes, caller order, callbacks and rechecks remain as specified. No descriptor, suffix, path, rationale identity or other unrelated observation may be changed to manufacture N57's old refusal.

The variant reader remains the existing `_document` path with the 16 MiB `LIMITS['document_bytes']` ceiling and its identity, canonical JSON, duplicate-key and callback checks. The existing source ceilings remain 100,000 operations and 30,000 ms; all other P11/P07 limits remain unchanged. This clarification adds no reader, decoder, limit, approval field or broader loader behavior. [E04 §6; E06; E12]

Author validation covers source identities, exact structural differences, finite mapping and preservation only. No product module is imported, no runtime policy is implemented, and no product tests or target process run. H0/H1, runtime preparation, Node/ldd, the original seven outcomes, full routine/R03, main integration and R04/R05 remain outside this phase. The original inherited 175 inspection/mapping methods and all later independent implementation, host and release checks remain obligations for the appropriate later phase. [E05, E06]

Sources E01–E14 are exact repository inputs in [INPUTS.json](INPUTS.json); [SOURCE-EVIDENCE.json](SOURCE-EVIDENCE.json) records the inspected anchors and the P01/N57 comparison.
