# C243: source-node mapping design and precise blocker

C243 resolves the C241 design question to a concrete boundary: **the prescribed
loader route has no established safe caller-visible window for preserving the
source-node map through mesh replacement**. The reviewed upstream code stores
raw node pointers, converts and deletes mesh nodes before returning to the
ordinary caller, and does not update that map in the inspected conversion path.
This is source evidence, not an observed defect in the installed Godot build.

The [design](DESIGN.md) identifies the affected fixture path, rejects ambiguous
identity substitutes, and describes one **unadopted** callback/signal route. That
route requires a separately versioned decision permitting a narrow observer
extension. C220's no-custom-extension boundary remains unchanged here.

The [results](RESULTS.md) retain 18 passing read-only verification groups: exact
upstream sources, all eight original authority files, six prior contracts, the
18-node fixture, source call order and the unchanged installed binary. No native
process, fixture regeneration, observer implementation or aggregate occurred.
Independent review and publication are recorded separately by the integrator.

R07 remains pending. After verified saved handoff delivery, follow the
[next bounded task](NEXT-TASK.md): decide and review that specific capture-hook
exception without starting Godot or implementing another feature.
