# C253: localized-repair protocol and fixture bindings

C253 prepares a comparison of how an agent changes one named component while
preserving the rest of an assembly. It follows the [C252 investment
decision](../review-integration-c252/DECISION.md) and
[next-task contract](../review-integration-c252/NEXT-TASK.md). It contains no
runner, trial result, new language feature or native execution.

The selected material is the existing C210 keyed-rack proof: two racks with
18 named objects. A requested edit changes one finger's length. The other
rack and unrelated parts must stay unchanged. Its two valid directions and
one invalid candidate belong to **one public, previously used assembly
family**. They can qualify a future test harness. They cannot constitute an
unseen comparative corpus or establish general authoring advantage.

## Read in order

1. [Protocol](PROTOCOL.md): research question, cases, applicability and limits.
2. [Corpus manifest](corpus.json): exact source/dependency hashes and edit rules.
3. [Scoring specification](SCORING.md): independent formulas, evidence and failures.
4. [Run and analysis plan](RUN-PLAN.json): fixed budgets/order and blocked inputs.
5. [Independent review](REVIEW.md) and [decision](DECISION.md).
6. [Next bounded task](NEXT-TASK.md): an offline oracle and manifest component.

Run only the static manifest check and the repository documentation check for
this increment. The manifest check reads bytes; it does not parse or execute
OntoKin, import native bindings, run a model, or score a submission.

```sh
python3 -IB docs/engineering/localized-repair-c253/verify_manifest.py
python3 -IB docs/maintenance/reorganization-2026-10-17/verify_reorganization.py
```

The source baseline is published main
`ce19b8c313da9c87050dfa2a8ba4f32470fb1f6f`, tree
`ffb6a1761c43c44a4b145946e9e3045fbd5c4bb4`.
[Scope #235](https://github.com/Omegapy/OntoKin/issues/235) owns this increment.
Publication and executed checks are recorded in [RESULTS.md](RESULTS.md).
No historical fixture, tolerance, C221 criterion or held Godot branch changes.

