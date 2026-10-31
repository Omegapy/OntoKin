# C081 independent keyed transformation inputs

This directory fixes the intended inputs and answers before C081 runtime implementation. It contains **97 source cases: 50 intended successes and 47 intended refusals**, plus **10 Agent workflow requirements**. These counts are requirements, not measured C081 passes.

The [decision](../../docs/language-design/keyed-transform-v0.1/ADOPTION.md) selects source `0.14`, profile `keyed-transform-0.1`, Agent/0.14 and GLB/0.14. The [acceptance inventory](../../docs/language-design/keyed-transform-v0.1/acceptance.json) maps every source case to its required group. [expected.json](expected.json) contains exact program identities, scalar answers and geometry/appearance/motion expectations. [workflows.json](workflows.json) defines the actual Agent operations and their required effects.

## Representative source task

`panel-task.files.json` selects a pinned reusable panel library and two independent PanelGroup occurrences. Each transforms supplied numeric coefficients into typed lengths, then uses those lengths to construct two textured panels. The first group moves upward; the sibling stays still. A separate untextured cube moves to the right.

`panel-task-repaired.files.json` changes only the first group's public `scale` input from 1 m to 1.5 m. Its two panel widths change from 1/2 m to 1.5/3 m. The sibling, pinned library, PNG bytes, generated keys and unrelated cube motion must remain exact. The actual repair must use the Agent source-edit operation with the current program and source-file preconditions.

`panel-identity.files.json` applies an identity transform to explicitly supplied lengths. Its paired `control-panel-identity.files.json` is an independently authored C080 program with those same explicit lengths. Their complete GLB BIN chunks, accessor layouts/data, materials, image/sampler graph and motion streams must match. The newer source contract and source provenance have different, independently checked JSON metadata.

## Independent answers

Every panel is a rectangular prism with width `w`, height 2 m and thickness 0.25 m. Its volume is `0.5w` m³ and its surface area is `2(2w + 0.25w + 0.5)` m². Each has 12 triangles and eight distinct local corners. Its top image mapping is `U = 0.5x`, `V = 1 - 0.5y` using recipe-local coordinates. The separate cube has side 0.5 m, volume 0.125 m³ and surface area 1.5 m².

For times 0 through 1 s, the first group's Y position is `0.5t` m. The cube's X position is `0.25t` m and its Y position is -3 m. The sibling stays fixed. The machine-readable expectations preserve these formulas' values at 0, 0.25, 0.5, 0.75 and 1 s, together with stable occurrence identities, input key locations and separate transform-expression locations.

The generator imports only the Python standard library. It authors these expectations from the selected source definitions and geometry; it does not execute or import the C081 runtime. The 50 explicit C080 controls were separately checked against the unchanged C080 runtime to find fixture syntax errors. Those checks are input-development evidence and do not establish a C081 pass.

## Freeze and changes

The [exact freeze](../../docs/language-design/keyed-transform-v0.1/INPUT-FREEZE.json) inventories this directory and the reviewed acceptance records. After publication, do not regenerate or overwrite frozen inputs. A defective input needs an explicitly named correction and a preserved original failure, as in the retained C080 correction lineage.

The sole failed pre-freeze control attempt used the unsupported `parallel` token in four scene event blocks. The supported `sequence` spelling was selected before freezing; the initial generator and raw diagnostics are retained separately. No C081 acceptance execution occurred during that correction.

Original28 remains failed at 24/28, with P11, P16, P23 and L03 unresolved. The inherited external, compatibility, authority, reach, timing, LFS, Unreal and live-physics gates remain open. This input corpus does not narrow the complete OntoKin goal.
