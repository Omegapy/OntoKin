# C186 · Reuse of a rotary indexer design

Two fresh subagents independently added a 220 mm wide gauge shoe to an existing editable assembly. Each kept the 180 mm and 260 mm selections working. The independent GLB decoder verified all five part identities and colors, shoe and guard geometry, the two-second quarter turn and the clearance to each guard. Both routes passed on their first formal submission. [Measurements and hashes](results.json)

| 220 mm export | East minimum | Time | North minimum | Time |
| --- | ---: | ---: | ---: | ---: |
| Blender/Python | 14.999980 mm | 0.154850 s | 14.999980 mm | 1.845150 s |
| OntoKin | 15.000024 mm | 0.154850 s | 15.000002 mm | 1.845150 s |

Blender needed one new entry in its width table. The older Blender exports matched C185 byte for byte. OntoKin needed a named half-width in the program and a selection in the build script. Its older exports retained their embedded binary data and all standard glTF fields. The updated source revision and source locations changed 104 custom metadata fields in each file. [Editable designs, six exports and author reports](deliveries.zip)

The coordinator rebuilt all six GLBs twice in fresh directories. All twelve matched their submitted files byte for byte and passed the checker. All six opened in the fixed Delft viewer at the start, midpoint and end of the turn. [Viewer comparison](comparison.png)

Both agents worked in separate directories in a shared environment under matched allowances. The result shows that another agent can reuse either design for this parameter change. Cost and general reliability remain open. [Dispatch conditions](dispatch.json)

## Next assembly

C187 qualifies two reference starters for a two-carriage gauge. The common source definition for both shoes sets up a later test of changing one instance while preserving its sibling. Spawn one fresh Blender/Python subagent and one fresh OntoKin subagent in the current conversation’s execution environment. Give them the same [starter brief](starter-brief.md) and [numeric design](assembly.json). The coordinator independently verifies the seven part IDs, decoded dimensions, constant translation, fixed stops, per-lane gaps and clean rebuilds. The C186 handoff ZIP includes the full dispatch and control requirements.
