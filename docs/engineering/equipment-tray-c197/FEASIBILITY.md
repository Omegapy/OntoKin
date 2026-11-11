# C197 equipment-tray feasibility map

**Decision:** `FEASIBILITY_PROPOSAL_REQUIRED`. The language can express the
minimal static geometry. Admission is blocked by the absence of an existing
qualified common construction path for this family. No tray baseline was
exported. This is the second valid closing outcome in the
[frozen C197 task](../accepted-revision-c196/NEXT-TASK.md).

The inspected baseline is actual main
`6cbcf9c8c136659def1aac94829330cb81872511`, tree
`13eb2463217d3021c7783c6c6d8be749e8c2e145`. C196 integration and its fresh
resulting-main checks are recorded in [C196-INTEGRATION.md](C196-INTEGRATION.md).
The semantic and backend reports retain exact file hashes, Git blob identities
and line references. Existing tests and historical results were inspected; they
were not rerun or relabeled as tray qualification.

## Feature-to-implementation map

| Required capability | Existing specification and implementation | Finding and remaining gate |
| --- | --- | --- |
| Typed dimensions and frames | [OK-LANG-001](../../language-design/OK-LANG-001-core-language-specification.md), `ontokin/values.py`, `ontokin/validator.py` | `Length`, `Vec3<Length>`, dimensional arithmetic and explicit frame identities exist. The world is right-handed and Y-up; `box` uses centered full side lengths. Actual tray dimensions, frame poses and tolerances remain unfrozen. |
| Reusable tray definition | [OK-LANG-002](../../language-design/OK-LANG-002-pinned-modules-and-keyed-assembly-construction.md), `ontokin/bundle.py`, `ontokin/linker.py`, [keyed-rack source](../../language-design/construction-v0.1/01-keyed-rack/main.ok) | A local class is sufficient for two trays. Existing `construction-0.1` additionally supports a package/version/digest-pinned reusable module. No new language semantics are identified. The tray source and dependency closure remain uncreated. |
| Independent instances | `ontokin/validator.py`, `ontokin/construction.py`, `ontokin/program_runtime.py`, `tests/test_construction.py` | Occurrence paths and per-instance overrides distinguish left and right children. A source edit can target one instance. Actual delivered sibling geometry and identity preservation still require a frozen checker and measured outputs. |
| Derived geometry | Typed parameters and arithmetic in `ontokin/values.py` and construction/validation; ordinary box geometry and explicit follow offsets | The five-box partition below derives base, walls and cavity from a few lengths without duplicated corner volume. This is a mathematical/source feasibility inference, not an executed tray. |
| Common delivery | `ontokin/program_bindings.py`; [C193 contract](../../language-design/guided-contact-v0.2/SPECIFICATION.md); `prototypes/guided_contact_v02/source.py` and `native_worker.py` | **Missing for trays.** Ordinary construction selects native `ontokin.glb/0.2`. C193's same-Blender-constructor promise applies to its exact seven-part carriage gauge. Its parser/schema enforce that finite assembly. Adding tray representation or identity mapping is substantial under C197's stop rule. |
| Independent checking | Existing construction GLB tests and finite independent readers; C191 receiving/render path | Actual vertices, transforms and IDs can be decoded. No inspected reader is already a qualified tray clearance/sibling oracle through a common constructor. A later mapping must qualify such a checker and real delivered-content failure controls. |

The supporting [semantic report](evidence/semantics/REPORT.md) and
[backend report](evidence/backend/REPORT.md) distinguish current implementation
from inference and future obligations. [FEASIBILITY-INPUTS.json](FEASIBILITY-INPUTS.json)
binds the inspected files to the baseline.

## Why the existing delivery paths do not pass this gate

C193's contract preserves exactly seven visible boxes, two 1 kg carriage bodies,
four contact boxes and two massless follow relationships. The only admitted
design edits are the left stop's X coordinate and one collider toggle. The source
validator checks the exact declaration-ID sets against its schema and requires
exactly fifteen declarations. Its native worker constructs the fixed carriage,
guide and motor roles. Those explicit limits are part of the qualified result.

Earlier rotary and carriage comparisons use OntoKin's native exporter for one
route and Blender/Python for the other, followed by common GLB readers or viewers.
They do not establish a common construction backend for a reusable tray.
Blender import of an existing GLB is receiving validation. The inspected gauge
renderer checks its seven fixed IDs; it does not define a source-to-Blender tray
mapping or qualify identity preservation through a re-export.

Using either path for C197 would require a new representation/relationship
mapping or interpretation of unsupported constructs. The task explicitly calls
that substantial, even if the eventual implementation is small. Renaming tray
walls as carriage roles would violate the existing contract. The correct stop
is before the input freeze, baseline exports and author dispatch.

## Minimal static geometry that remains feasible

Let cavity width, depth and wall height be positive lengths `W`, `D`, `H`, with
wall thickness `t` and base thickness `b`. Use X for width, Y for height and Z
for depth; put the cavity floor at Y = 0. The following full sizes and centers
form a disjoint solid partition except for shared faces:

| Part | Full box size (X, Y, Z) | Center (X, Y, Z) |
| --- | --- | --- |
| Base | `(W + 2t, b, D + 2t)` | `(0, -b/2, 0)` |
| Front wall | `(W + 2t, H, t)` | `(0, H/2, (D + t)/2)` |
| Back wall | `(W + 2t, H, t)` | `(0, H/2, -(D + t)/2)` |
| Left wall | `(t, H, D)` | `(-(W + t)/2, H/2, 0)` |
| Right wall | `(t, H, D)` | `((W + t)/2, H/2, 0)` |

Front and back walls own the corner strips. Left and right walls end at the
cavity's front/back planes. The base occupies `-b <= Y <= 0`; walls occupy
`0 <= Y <= H`. Their interiors therefore do not overlap. A named payload
measurement proxy can derive `W = payload_width + 2 * clearance` and the analogous
depth. The later contract must define vertical clearance and placement.

This formulation represents geometry and measurement proxies. It does not add
box mass, inertia or contact behavior. A tray container and followed children
use supported `no_body`/`prescribed` meaning with constant poses and explicit
follow offsets. Ownership alone does not position a child, and a follow-controlled
child must not receive a second placement authority. Static output does not mean
silently changing those source modes.

## Outcome

The blocking requirement is common delivery and its independently qualified
measurement path, not evidence of a missing class or dimension type. The
[versioned proposal](PROPOSAL.md) defines the narrow next decision. It is not an
adopted adapter, successful tray delivery, comparative result or general backend.
There are zero C197 native exports, simulations, receiving jobs and timed authors.
The inherited failed regression and all broader GOAL gates remain unchanged.
