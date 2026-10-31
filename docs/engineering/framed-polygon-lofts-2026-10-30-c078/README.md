# C078: explicit rigid frames for polygon loft sections

This increment adds authored rigid section frames for bent solid bodies, hollow elbows and finite handles. Explicit source, Agent and recorded GLB `.11` preserve the earlier station-loft, polygon-hole and extrusion meanings. Candidate `853b369a6de2a123d5ef679b99c69f1f0c6aea23`, tree `beb291f518fc575a965d84f3ae304b7a89ba1656`, has the measured checks below. Evidence publication, integration, final-main checks and portable delivery have separate identities. Complete feature and product release acceptance remain false.

## Decision, independent inputs and source roles

| Role | Actual commit | Actual tree |
| --- | --- | --- |
| C077 final baseline | `cac8b9f81a39ff8a9343caf6e8881bdc67e3ea93` | `7d49603ceb506bb979d5bff96c32e0c64b8d957d` |
| Published adoption | `69b80f683073b0c9b75f06014933f0e9939c1f5d` | `06fddd5c41d2de34fd43188301c057b1faf345d5` |
| Published independent freeze | `da56cc3b57469c8a01546e4a3ac7cc8467ddccbb` | `1015147ac8fffbf707f9a38dd4e96d88d93767ee` |
| Development acceptance author source | `e4f39fe903af7695611d669a4e034fc49f7020d1` | `6f9cd36af42ff6170a7b588823a0f1b049358513` |
| Initial runtime publication | `b33775bee88819aed02157a5edf4c15f59eb71cb` | `6f9cd36af42ff6170a7b588823a0f1b049358513` |
| Complete tested candidate | `853b369a6de2a123d5ef679b99c69f1f0c6aea23` | `beb291f518fc575a965d84f3ae304b7a89ba1656` |

[OK-LANG-011 / OK-AGENT-011](../../language-design/framed-polygon-loft-v0.1/ADOPTION.md) and the independent [fixture freeze](../../../examples/framed-polygon-lofts/acceptance-freeze.json) were published before runtime implementation. The freeze SHA256 is `70e4d7fd47fa40efde961c0c859f96845a4f566979238a194d2e67f03bc48be4`. It identifies 80 input files, including 76 `.ok` files, and 69 cases: 26 expected successes, 40 source refusals and three source-valid delivery refusals. The manifest itself is the eighty-first frozen path. The adoption remains a separate exact published input.

Worker branches separate geometry, Agent lifecycle, independent geometry/destination checking, acceptance workflow and independent raw-evidence reconciliation. Author commits remain distinct from published commits. The [source review record](source-review.json) and complete raw evidence identify actual changes, checks, failures and byte boundaries. The tested candidate adds the evidence auditor to the already verified implementation tree; the later exact-candidate executions have their own receipts.

## Implemented meaning

The two new constructors are `framed_polygon_section(order, frame, rings)` and `loft_framed_rings(sections, palette, bottom_region, top_region)`. `FramedPolygonSection` carries an explicit order, a rigid `Pose` and keyed polygon rings. Every pose must reference the consuming carrier's `self.frame`. The check applies at section construction, loft consumption and final object materialization. Pure reusable functions retain caller carrier authority without changing their lexical `self` rules. Borrowing either foreign sections or a complete foreign geometry cannot bypass ownership.

Each section has one counterclockwise outer ring and zero through eight clockwise holes in its own XY plane. Ring keys, roles and orders, and vertex keys and orders, match across all sections. Coordinates and outgoing material regions may vary. Lower-section outgoing vertices own the fixed strip triangle materials. Both cap names and terminal strip region names are validated even when a valid terminal region emits no strip.

| Bound | Value |
| --- | --- |
| Sections | 2–8 |
| Holes per section | 0–8 |
| Authored vertices | At most 64 per section and 256 total |
| Origin and authored XY components | ±100 meters |
| Rounded transformed source components | ±256 meters |
| Adjacent origin separation | At least canonical binary64 0.001 meter |
| Order | Unique integer in 0–65535 within its scope |
| Materials | 1–16 |
| Derived geometry | At most 540 triangles / 1,620 flat corners |

No common station axis is inferred. The exact displacement between adjacent origins must have a strictly positive dot product with each neighboring section's exact positive Z axis. There is no replacement angle cutoff. A near half turn is admitted only if all actual mesh predicates also pass.

Existing source quaternion construction retains its semantics. The new section transform uses the stored canonical quaternion without a second normalization. It forms an exact rational proper rotation divided by the exact squared quaternion norm and rounds each complete translated coordinate once to canonical binary64. This matters when a canonical quaternion's stored squared norm differs slightly from one. Native quaternion admission uses the exact inherited 1e-12 envelope; sign and zero canonicalization do not replace the transform rule.

Fixed diagonal strips and independently triangulated endpoint XY domains define the authoritative surface. The first cap is reversed; the last faces forward; intermediate sections have no caps. Rounded caps can be slightly nonplanar: coverage is checked in authored XY by source identity, while actual triangles are checked in three dimensions. Complete admission requires distinct identities at distinct positions, nonzero faces, opposite closed edge incidence, only explicitly shared-simplex contacts, positive signed volume and proper endpoint cap orientation. Crossing, pinching, overlap and nonadjacent touching fail without repair or welding.

The actual placed binary32 positions undergo independent complete checks again. Outer `placed` arithmetic retains its earlier normalization, rational rotation and separate binary64 translation; it is not reinterpreted as the new R/D section transform. Exact section axes pass through the exact inherited placement matrix for cap-sign guards. Source-quantized positions and normals, full triangle indices, regional PBR identities and the unchanged local geometric tolerance remain checked. Visual geometry introduces no physical mass, inertia, collision body or motion authority.

## Agent and execution behavior

`FramedLoftAgentService` selects Agent/0.11 and a separate `framed-loft-program-agent.sqlite3` store. All twelve operations execute: discover, create, edit, validate, inspect, evaluate, reset, status, cancel, export, artifact and surface.mesh_page. The [schemas](../../language-design/agent-v0.11/README.md) preserve all older summary definitions and add `ontokin.framed-polygon-loft-summary/0.1`, exposing section origins, canonical wxyz orientation and owning frame instead of a station range.

Exact UTF-8 file patches preserve immutable revisions and failed-edit rollback. The frozen repair changes only the first instance's `end_x = 4[m];` to `end_x = 5[m];`, raising its independently calculated volume from 12 to 13.5 cubic meters. Its sibling remains at 12 cubic meters, and the pinned library bytes and nominal identities remain unchanged. Revision/query/occurrence/geometry/implementation/protocol bound cursors, 256-triangle page limits, current host reauthorization, cumulative work/deadline accounting, cancellation and atomic artifacts retain their earlier meanings. Identical retries return the original durable receipts across service reopen.

Omitted limits remain 100,000 operations and 30,000 ms on every host. The repaired export consumes 46,027 operations. The maximum cases explicitly request and receive separately authorized 2,000,000 operations / 80,000 ms; measured counts are 984,597 and 1,290,760. Computation elapsed time is separate from authored animation duration. Those larger requests do not retroactively pass older fixed-budget gates. Exact new arithmetic is charged and retains the 32,768-bit operand bound without adding a new cache.

## Actual candidate validation

| Check | Observed result |
| --- | --- |
| Full inherited unit inventory | 3,585 methods; zero failures, errors or skips; CPython 3.12.14 |
| Complete local driver | 34/34 selected steps passed, including full visual and separate Agent/0.5 roles |
| Original source conformance | 43 cases / 694 assertions passed |
| Separate Agent/0.5 cohort | 106 tests passed; overlaps the complete unit inventory |
| Frozen C078 source acceptance | 69 cases / 1,036 assertions passed |
| Actual Agent workflow | 127 schema-valid exchanges / 123 durable request identities; all twelve operations |
| Independent raw evidence audit | 21,348 consistency checks passed, zero failed |
| New source-built GLBs | 29 pass independent geometry, identity, material and motion checks |
| Legacy equivalence companions | Two old-profile exports retain exact decoded triangles, normals and PBR values |
| Khronos validation | 29 artifacts; zero errors or warnings |
| Recorded playback | 170 native and 70 browser occurrence/time observations |
| Actual image review | 20 new-profile captures, plus complete inherited capture disposition in visual-review.json |

The immediate predecessor .10 acceptance also passed 74 cases / 418 assertions and 68 actual Agent exchanges. All 25 GLBs retain exact binary geometry and animation streams and all JSON except the truthful implementation fingerprint.

The [local-check summary](candidate-local-checks.json), [acceptance summary](candidate-acceptance-summary.json), [Agent evidence audit](agent-evidence-review.json), [destination record](candidate-destinations.json) and [visual review](visual-review.json) separate these scopes. Counts overlap where a focused cohort is also included in the complete inventory. Consistency-check counts are not product-test counts. Only the executed interpreter and selected roles are established; the inherited pending external cases and unexecuted compatibility versions remain open.

The independent geometry oracle imports no production transform, triangulator or contact predicate. It recomputes frozen source positions, authored cap domains, prescribed strip triangles, actual three-dimensional contacts, complete incidence, positive volume, normal direction, material ownership and recorded motion from supplied bytes. Fifty hostile oracle methods use independent controls. A separate evidence auditor checks raw schemas, request and source identities, SQLite ownership, exact patch rollback, saved runs, page ordinals and complete artifact chunk reconstruction. Its twelve hostile methods use hand-encoded bytes and no product imports. The auditor reconciles the separately executed complete topology proofs and does not claim to rerun them.

One development source diagnostic failed before correction: a Length passed as a section Pose produced UNIT instead of the frozen TYPE result. Only the new constructor's categorical Pose check changed; the frozen inputs and inherited `expect()` semantics remained exact. The original failure is retained. A mistaken targeted unittest method name executed no assertion before the discovered correct method passed. Early evidence-reader failures exposed reader assumptions about ordering, retained run IDs and endpoint/reset velocity; their original receipts and exact reader texts remain available. None was hidden by rewriting a successful result or expectation.

## Preservation, publication and integration

Every one of the 4,213 C077 tracked paths remains. The stronger C077 protected set contains 1,140 exact paths; it includes the 1,046 inherited protected paths. All 85 C077 frozen/adoption paths, 81 C078 frozen paths and the separately published C078 adoption retain exact modes and bytes. Candidate changes are 20 explicitly allowed older files and 103 additions, with zero removals. The [preservation record](source-preservation.json) is independently derived from actual Git trees and blob bytes.

The complete raw candidate/development archive is identified by [evidence-archive.json](evidence-archive.json). It contains original failed preparation/audit attempts and completed candidate evidence; later evidence publication, main lease, merge, final-main checks and packet/delivery receipts have separate boundaries. No archive is presented as including records created after it was frozen.

PR #76 merged evidence publication `c5d60d1d6cd27b94cd833feed6db2932ea3308b4` as actual main merge `1a2ea0203d0fa6c1996719bf02e41b2c42a51c71`, tree `174b53ff7e8458289a1b27375af654b2a83ea28e`. The ordered parents are lease `8dd9249ebff6ac34a567d17798002b310b485ca1` and the evidence publication. The actual tree matches an independently calculated merge tree. [integration.json](integration.json) binds these observations and the [fresh resulting-main checks](resulting-main-checks.json): 137 focused methods; 43 original source cases / 694 assertions; 69 C078 cases / 1,036 assertions and 127 actual Agent exchanges; documentation; and exact equality of all 4,315 eligible inputs. This final publication releases the bounded lease. Exact-final documentation/equality and complete packet delivery have later separate receipts. Only STATUS and this exact engineering directory are excluded from candidate-to-main equality. Equality supports attribution; it is not another complete regression or browser execution. Work-branch removal follows verified history retention. Final packet and delivery scope closure occurs only after their actual receipts.

No hosted job was dispatched. Workflows remain manual-only with default-false opt-in; repository-wide Actions disablement is not asserted without observing that setting. Runtime dependencies remain Python standard library. Pinned verification tools and their actual versions are recorded separately. Historical LFS migration remains unfinished, with no unuploaded pointer substitution or history rewrite.

## Remaining requirements and continuation

C078 is an experimental development increment. Earlier finite releases and source/Agent/GLB defaults keep their meanings; .6–.11 remain explicit experimental capabilities. Unreal import and live destination physics remain unverified. Original28 remains 24/28, failed, with P11/P16/P23/L03 unresolved. M1 remains rejected and comparison accounting/passive authority open. C035 remains held with adverse timing. C057, complete reach, all R01–R12/Q01–Q22, required compatibility and independent external roles remain open. C068 remains unadopted, C069 rejected, C070 unselected and C071 rejected. C059's exact storage cause remains unestablished.

Preserve all of [GOAL](../../../GOAL.md): richer typed algorithms/libraries, textures/UVs and skin, general rigid dynamics/contact/mechanisms, purposeful creatures, flight/swimming, vegetation/wind, terrain/buildings, liquids/deformables, clips/live engines, measured scale/performance and direct-tool authoring comparison. [C079's next bounded task](NEXT-TASK.md) proposes source-authored blind polygon pockets after C078 closure, beginning with its own explicit decision and independent freeze. No C079 runtime or continuation schedule is started by this record.
