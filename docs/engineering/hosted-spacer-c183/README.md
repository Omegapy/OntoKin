# Public spacer repair with hosted subagents

Two fresh coding subagents each inspected one editable spacer, exported its baseline, observed the expected target failure, changed two dimensions and submitted a measured native repair. They worked unaided through separate disposable Linux guests. The [registration](registration.json) fixed the six input hashes, acceptance dimensions, tolerance and limits before either assignment. This C183 rehearsal follows the hosted protocol issued with the C182 handoff.

| Native route | Baseline X × Y × Z | Repaired X × Y × Z | Center | Clean rebuild |
| --- | --- | --- | --- | --- |
| Blender 4.5.3 LTS | 40 × 12 × 20 mm | 50 × 12 × 24 mm | Origin | Byte-identical |
| OntoKin | 40 × 12 × 20 mm | 50 × 12 × 24 mm | Origin | Byte-identical at the same source URI |

Dimensions are rounded to the nearest millimetre. The independent reader found one mesh and twelve triangles in each submission. The largest dimensional error in either repair was below 0.000001 mm. A first OntoKin rebuild placed the editable file at a different path. Its binary chunk matched, and only the source URI differed in its JSON. Rebuilding with the original source path reproduced the complete submitted GLB. Both participants used six relay replies. The hosted service exposed no auditable per-worker token totals.

The [Blender submission](submissions/blender/build_spacer.py) and [OntoKin submission](submissions/ontokin/main.ok) retain the two editable sources alongside their baseline GLBs, repaired GLBs and participant logs. [Independent checks and file hashes](results.json) · [Blender transcript](evidence/blender/transcript.jsonl) · [OntoKin transcript](evidence/ontokin/transcript.jsonl) · [Worker reproduction](worker/README-worker.md)

## Before an unseen comparison

A separate fresh hosted child used its host shell to read a harmless marker kept outside both guests and returned its exact SHA-256 digest. It could also see a delegation tool. The guest shell confines the native commands. The hosted child still has tools outside that shell. Keep the unseen repair sealed until a route-scoped participant interface denies the same read and prevents additional delegation. Then qualify cancellation and masked custody before dispatch. This public case establishes that both authoring workflows can complete a two-dimension repair. A comparative cost or reliability claim needs a preregistered study. [Boundary test](evidence/host-boundary.json) · [Hosted study protocol](protocol/HOSTED-SUBAGENTS.md)
