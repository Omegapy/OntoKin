# C088 bounded keyed membership

The [adopted decision](../../language-design/keyed-membership-v0.1/ADOPTION.md) adds `has_key(collection, query) -> Bool` through explicit experimental source/Agent/recorded-GLB `.21`. It supports sparse component overrides and read-only membership in existing generated views while preserving eager arguments, full input admission, stable keys, exact dependencies and current request authority. The [language guide](../../language-design/keyed-membership-v0.1/README.md), [Agent guide](../../language-design/agent-v0.21/README.md) and [examples](../../../examples/keyed-membership/README.md) describe its public scope.

## Adoption before runtime work

Adoption `a4d16331f720671548d125f2fcf3e1745277f631`, tree `8e3f6e650733943414e86354833afbb5234ca1ef`, contains the independently reviewed specification and 904 inventoried input files, plus their exact manifest and review/preflight records. The actual remote branch, native commit and tree matched. [Complete byte readback](INPUT-FREEZE-READBACK.json) verified all 927 adopted paths / 3,681,253 bytes through 816 unique actual blob reads. [Actual recursive mode readback](INPUT-FREEZE-MODES.json) verified the full 925-file language/input subtree. The source was clean and production, inherited tests/tools/workflows and shared status remained unchanged before the [implementation grant](IMPLEMENTATION-GRANT.json).

The effective predecessor input cohort is 256. Its third run passed all 256; the fourth separately passed the eight literal controls revised after the property-shape review. The earlier failed 207/230 run and all other drafts/preflights retain their original outcomes in the complete handoff. No candidate result supplied an expected answer.

## First implementation checkpoint

The new private operation uses closed shallow native metadata descriptors, immutable captured entries and all five real ledger stages. The compiler retains declaring-unit resolution, ordinary eager calls, abstract checking, generated guards, dependency/provenance flow and cache exclusions. The explicit Agent service, independent store, discovery, schemas, CLI and recorded destination inherit the existing transport and twelve operation shapes. Earlier profiles and ordinary defaults remain unchanged.

The [core static receipt](review/CORE-STATIC-COMPILATION-01.json), [core handoff](review/CORE-IMPLEMENTATION-HANDOFF-01.md), [independent integration review](review/ROOT-INTEGRATION-STATIC-REVIEW-01.md) and [focused test preparation](review/INTERFACE-STATIC-COMPILATION-01.json) record the pre-execution review. Static compilation alone is not product validation. The first runtime checkpoint still requires actual frozen source/native/resource/Agent execution, independent and hostile readers, complete artifact comparisons, native views, all inherited checks and independent candidate review before integration.

The [working scope](SCOPE.md) identifies the owner and branch. Main integration remains serialized under an observed-head lease. This record starts no hosted job, worker or schedule and grants no release acceptance. All [retained gates](RETAINED-GATES.md), historical failures and every domain of [GOAL](../../../GOAL.md) remain binding.
