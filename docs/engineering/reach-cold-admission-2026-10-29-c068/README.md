# C068: cold-reader admission and funding

**Decision: the separately funded eager prefix admission is uneconomic at every possible entry seam. No runtime implementation is selected.** The current source also lacks a supported passive interval and authenticated producer receipt for its ordinary mutable POSITION list. [CHECKPOINT-068](CHECKPOINT-068.md) gives the source proof and its limits.

The original C067 packet and ZIP were freshly verified in full. This checkpoint starts from main `7c1bf5d32d194f2faf7f38c9f3c153089f7a7b7e`, tree `f1bfe1c770fd1fc1c0aca5fbeabf54d4ac1f0aa5`: 3,627 files, 621,973,113 bytes, zero omissions. [Preparation](PREPARATION.md) records the actual retrieval and source reconstruction, including corrected preparation failures.

## Read the result

- [Decision and derivation](CHECKPOINT-068.md)
- [Narrow versioned proposal](PROPOSAL-068.md), **OK-PROP-COLD-ADMISSION-068/0.1.0, UNADOPTED**
- [Event and funding map](funding.json)
- [Source bindings](source-binding.json), [standalone static derivation](derive_evidence.py) and [derived evidence](derived-evidence.json)
- [Independent reviews](reviews.json) and [validation](validation.json)
- [Next bounded task](NEXT-TASK.md)

For seed row 133, six separately charged source/stored leaf checks per pair cost 804 at cold entry. Even entering after the current row's three original source checks leaves a deficit of at least three units at **every** eligible seam, before all other admission costs. This rejects that explicit checking schedule, not every possible geometry optimization.

The proposed alternative carries actual producer evidence through a narrowly defined passive interval. The current implementation has no such receipt, mutation epoch or paid trusted router. The proposal does not adopt those facilities, exempt their cost, change supported foreign behavior or authorize instrumentation. C069 must first resolve a concrete producer-to-reader ownership question on the original source-artifact call path.

All runtime, tests, fixtures, contracts, limits, defaults and workflows remain unchanged. Historical original recordings remain **24/28, failed**; P11/P16/P23/L03, C057, complete reach acceptance and historical LFS migration remain open. M1 is rejected; C035 remains held including adverse timing. The full [GOAL](../../../GOAL.md) remains in progress.
