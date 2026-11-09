# Build the two-carriage linear gauge starter

Build an editable seven-part assembly from the accompanying `assembly.json`. It has two identical sliding carriages with one shoe and one fixed stop per lane. The design table gives world-space bounds at time zero in millimetres. Deliver a standalone animated GLB in metres, the editable design and an exact clean build command. Use the native tool assigned by the coordinator.

Give each mesh-bearing node and mesh its specified stable ID. Use closed cuboids and the linear RGB base colors in the table. Name each shoe separately and define their common geometry once in the editable source so a later agent can change one instance. Both carriages and their shoes translate 300 mm along +X over 2 seconds, at constant speed. The base and the two stops stay fixed.

Report each shoe's minimum gap to its own stop and when it occurs. Document the geometry definition shared by the two shoes, how source parameters select one instance, and any export processing, failed attempts or assistance. Supply the native and final artifacts with a field-level comparison if an export needs a naming step. Keep the submitted starter intact for the next agent.
