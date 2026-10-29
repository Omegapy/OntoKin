# C065 nonzero offset expression review

**Decision:** reject the selected detached four-product bridge. P11 contains a real signed arithmetic identity, but the chosen safe-copy schedule cannot produce a positive complete-request saving. No runtime improvement or new recording success is claimed.

Read [CHECKPOINT-065](CHECKPOINT-065.md) for the decision, then the independent [mathematics](reviews/math.md), [authority](reviews/authority.md), and [cost](reviews/cost.md) reviews. [Source bindings](source-binding.json), [derived evidence](derived-evidence.json), [review record](reviews.json), and [validation](validation.json) identify the evidence and its limits. [HANDOFF-065](HANDOFF-065.md) preserves continuation instructions; [NEXT-TASK](NEXT-TASK.md) proposes a different bounded source-design target.

The signed eye schedule retains exact left products `p=DZ`, `n=C(-A)`, `q=CZ`, `m=D(-A)`. Left floors stay `floor128(p-n),floor128(q+m)`; right floors become `floor128(p+n),floor128(q-m)`. Up to four right multiplications disappear in the nondegenerate case. Four charged detached producer copies already exhaust that ceiling, before any other new work. The proof applies per completed bridge, including replay. It does not prove all reference-only representations impossible.

To reproduce the offline derivation from repository root:

```bash
python3 -B docs/engineering/reach-offset-expression-design-2026-10-29-c065/derive_evidence.py
```

The output must match `derived-evidence.json` byte-for-byte. The script verifies pinned source and retained data and performs symbolic arithmetic. It imports no OntoKin runtime and executes no product request.

The original C064 packet was reverified in full. All runtime source and original budgets remain unchanged. Historical original28 remains **24/28, failed**; P11/P16/P23/L03, complete reach acceptance, C057 and historical LFS migration remain open. Keep the complete [GOAL](../../../GOAL.md). Development integration and release acceptance remain separate under [OK-ENG-009](../OK-ENG-009-development-integration-and-branch-lifecycle.md).
