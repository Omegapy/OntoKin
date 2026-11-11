# C201 public static-tray admission preparation

**C201 admission protocol prepared; coordinator and execution gates pending.**
This directory defines the separate public Q01 baseline and regeneration task.
It contains preparation documents, not an implemented coordinator, an
executable input lock, native-readiness approval or an admission result.
Independent review of these exact documents is a distinct preparation gate.

C200 is integrated through [PR #137](https://github.com/Omegapy/OntoKin/pull/137)
at `2b2f3e7de7595099ad5f9e0176c5596220c0c2dc`, tree
`7e1ab341160cf5b86807e8ffec2cc3bb7b47db92`. Its
[historical finite qualification](../static-tray-exporter-c200/RESULTS.md)
remains bound to executed source `62b2316cc3f88db187f69fbd7fdb2cf0997a97de`.
Those identities serve different purposes. C199's one failed construction and
C200's twelve accepted constructions remain separate closed schedules.

Read the [admission protocol](ADMISSION.md) and
[machine-readable rules and input bindings](ADMISSION.json), then
[the implementation gate](IMPLEMENTATION-NEXT.md). The new schedule permits at
most one baseline and one clean regeneration per route, four native starts in
total, only after the pending executable and independent approval gates pass.
Its separate receiving and actual-delivery Node ceilings are four each. Failures
consume starts. There are zero timed authors, simulations or automatic retries.
No process start is authorized by these preparation documents alone.

The known Q01 geometry is intentionally public. A later admission would show
that the qualified two-tray family is available through both complete workflows;
it would not establish unseen-task success or comparative authoring advantage.
[Issue #138](https://github.com/Omegapy/OntoKin/issues/138) records this bounded
preparation scope. General physics, external compatibility, full regression,
full release and the wider [GOAL](../../../GOAL.md) remain open.
