# OntoKin user guides

[Project overview](../../README.md) · [Current status](../../STATUS.md) · [Specifications and evidence](../README.md)

These pages collect the working examples and reference details formerly held in the root README. Commands run from the repository root. A named source, Agent or GLB profile is an explicit compatibility contract; a higher number does not replace the earlier default.

| Task | Guide |
| --- | --- |
| Edit one part, reject an invalid edit and preserve a sibling | [Agent workflows](agent-workflows.md) |
| Reuse a pinned library or construct a keyed assembly | [Agent workflows](agent-workflows.md#build-an-assembly-from-a-pinned-component-library) |
| Select, combine, pair and reduce keyed values | [Keyed construction](keyed-construction.md) |
| Author polygon forms, lofts, pockets, materials and labels | [Geometry and appearance](geometry-and-appearance.md) |
| Apply impulses/forces or understand execution budgets | [Motion and budgets](motion-and-budgets.md) |
| Export recorded motion and inspect a GLB | [Export and view](export-and-view.md) |
| Check source, inspect state or understand command failures | [Core and CLI](core-and-cli.md) |
| Run development checks or inspect language limits | [Development and scope](development-and-scope.md) |

## Choose a profile deliberately

For a first source-edit example, use the existing Agent/0.1 workflow. For a pinned multi-file assembly, follow Agent/0.2. Later geometry, appearance and motion examples identify their required source, Agent and GLB profiles explicitly. The default CLI Agent and export contracts remain `ontokin.agent/0.1` and `ontokin.glb/0.1`.

Release acceptance, integrated experimental behavior and held work have different evidence requirements. [STATUS.md](../../STATUS.md) records actual publication and unresolved gates; [GOAL.md](../../GOAL.md) defines what to invest in next. The [November 16 review integration](../engineering/review-integration-c252/README.md) prioritizes a comparative benchmark protocol before further feature expansion. No benchmark trials or measured advantage are claimed by these guides.
