# C271 P25: finite RTLD path implementation

The adopted inspection-plan `/0.1.4` implementation is accepted at a bounded technical boundary. RTLD is the dynamic loader path used by the inspected runtime. The new policy proves a fixed set of loader paths through two bounded descriptor-based traversals, including the declared parent transition and missing candidates. Earlier profiles, public P06 output, pins and limits retain their prior meanings.

Start with `PHASE.json`, `OUTCOME.json` and `ACCEPTANCE.json`. Production review is in `reviews/controls/REVIEW-FINAL.json`; independent adapter review is in `reviews/delivery/ADAPTER-REVIEW-002.json`. The applicable runs are baseline (385), attempt002 (385 inherited candidate methods) and attempt005 (51 frozen controls plus ten supplements). All applicable runs have zero failures, errors and skips. Earlier attempts and findings remain as superseded evidence, not silently replaced successes.

N34 remains an unmet external source-completeness gate for an actual operational plan. No H0/H1, actual Node/ldd/direct-loader execution, host reconstruction, installation, original full routine or main integration occurred in P25. C271 stays open, R03-R05 stay not_done, and P02 stays in_progress. Source-time pending delivery fields are resolved only by the later separate `P25-DELIVERY.json`, saved external receipt and matching live PR274/issue273 terminal records.

The initial recovery archive was saved and byte-verified before substantial work. Its historical path namespace needed an explicit clarification; the original archive remains unchanged, and `EARLY-PACKAGE-CLARIFICATION.json` plus its separately saved receipt preserve the correction.

## First remaining action

After verified P25 delivery, in a fresh bounded phase, bind the newly published /0.1.4 inspector and complete source inventory, construct and independently review the current-host H0 inspection plan, and satisfy the external N34 actual loader/script source-completeness gate before operational plan adoption. Reconstruct only necessary pinned inputs in the fresh host. Stop at an accepted plan or a concrete blocker; H1, the original full routine and main integration remain later gates.
