# C250 results: held detached playback preparation

This increment implements one precursor to native pose observation. The held
source keeps the original imported scene detached and its player stopped,
selects MANUAL processing, then assigns the already inventoried animation. The
mixer is active at all four observation boundaries; the MANUAL setter briefly
toggles active internally before restoring it. Four live boundaries surround the
two setters.
The complete C249/material/mesh/identity receipt chain remains available.

**Held source is reviewable source, not observed Godot behavior.** No GDScript
parsing, Godot/version/native start, playback, seek, tree attachment, pose
comparison, product execution or aggregate run occurred.

## Exact source and checks

- Initial author: `4f2bd9301cbbd8aea283316b2fd87643328825e2`.
- Corrected executable source: `251a9d1fa204f85061b3011665d551962e430651`,
  tree `c120e3ca66d7defbd1c38d4c8b1be7ab1c6553c2`.
- Final author: `553782d76e72f02758ce3cc1585c94fac2650aca`,
  tree `e633d173dc11e053306bb3a0a085c48e0c0197c9`.
- Base: held C249 `44edaf062f413f2496d2bbddf0811b315106cdc4`.

The final author changes README wording only after the corrected execution.
All five GDScript/model/test/binding files remain byte-identical. The independent
reviews bind those hashes and the exact final author revision. Published commit
identity is recorded separately in the draft PR and handoff; equal trees do not
turn local author commits into published ancestry.

| Check | Result and scope |
| --- | --- |
| Author Python model controls | 22 methods passed on corrected source |
| C250 source/API bindings | 145 assertions passed; 28 primary files and 17 authority/dependency files |
| Inherited C249 bindings | 371 assertions passed on unchanged dependency source |
| Independent native-source review | 113 static pin/API/scope/source-structure checks passed; manual review recorded separately |
| Independent executable model review | 119 scenarios / 2,251 assertions passed; initial defects and limitation witnesses retained |
| Initial API feasibility inspection | 48 static evidence assertions passed |

[REVIEW.md](REVIEW.md) explains the roles and links the exact receipts. Full
commands, source hashes, platform details, controls and logs are retained in the
C250 handoff under `evidence/c250/`. Checks ran in the actual shared Linux x86-64
environment with CPython 3.12.14. They are not additional platform attestations.

## Observed corrections

Independent review identified three receipt-retention omissions in the initial
source: a late blocking-signals value was checked without being retained; late
signal receivers lacked an explicit omitted-Callable marker; and a synthetic
inherited-scene refusal could lose the partial final-scene observation. The
corrected source retains these observations and adds final guarded position and
length readbacks. Original source, initial probes and findings remain preserved.

The component records ATTEMPTED before a setter and its returned/readback state
afterward. Setter no-ops, observed drift, incomplete reads and repeated or
reentrant calls refuse without rollback, corrective mutation or registry
reconsumption. A partial change remains explicit even when completion fails.

## Limits and next gate

The Python models fabricate native identities, NodePaths, getter values and
setter effects. The source has not been parsed or executed by Godot. Passing
controls do not establish installed-build lineage, native lifetime safety,
complete diagnostic coverage or atomic capture.

Stability checks cover the recorded inventory, identities, track associations,
mesh/material selectors and playback-control fields. They do not reread earlier
mesh-array or material-parameter payloads, exclude transient concurrent changes,
or prove unchanged native data between observations. The independent model
includes an in-place material-value change as an explicit limitation witness.

The pinned world-transform getter requires SceneTree membership. Its detached
error fallback is not a captured pose. A separately reviewed attachment stage
must account for actual parent/frame identity and tree-entry signals and
notifications. All 126 world-pose observations remain pending, as do raw sealing,
serialization, useful rendering, persistence and hard process/reservation limits.
R07, native admission and the original strict Blender-normal failure retain
their previous meanings. [NEXT-TASK.md](NEXT-TASK.md) defines the next separate
bounded source step. Close C250 with its verified saved handoff, then stop.
