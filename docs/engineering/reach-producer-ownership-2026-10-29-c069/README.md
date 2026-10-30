# C069 producer-to-reader ownership review

C069 rejects the proposed receipt for borrowing the existing mutable POSITION list under the unchanged execution semantics. The original source request has a native shared-budget callback, but the current source has no independently grounded router or owner that can protect the list through the required interval. The numerical-cache generation belongs to a different cache. A decoder-only generation would miss direct list writes.

This is a bounded source-design decision. It establishes no runtime optimization, actual hostile failure, complete-request saving or new recording success.

Read these records in order:

1. [Decision and exact scope](CHECKPOINT-069.md).
2. [Producer, alias and callback trace](SOURCE-TRACE.md).
3. [Rejected receipt and paid-event design](RECEIPT-069.md), with [machine-readable funding](funding.json).
4. [Bound source and static checks](source-binding.json), [derivation](derive_evidence.py), [derived evidence](derived-evidence.json), [validation](validation.json) and [independent reviews](reviews.json).
5. [Recovery and preparation](PREPARATION.md), [integration](integration.json) and [next task](NEXT-TASK.md).

The full [GOAL](../../../GOAL.md) and all unchanged reach acceptance requirements remain open. Historical recordings remain **24/28, failed**, with P11/P16/P23/L03 unresolved. C068's proposal remains unadopted. C069 does not change runtime, tests, fixtures, contracts, defaults, limits or workflows.
