# C234: CPU material observation checker

This finite R07 component adds a separately versioned material-observation
schema and checker for the existing C210 assembly: 18 parts and two materials.
It binds every observed material to freshly admitted source and the exact
geometry observations checked by C222. Raw values, the fixed color conversion,
normalized values and parameter errors remain separately inspectable.

Read the [contract](CONTRACT.md) for the schema, safe input rules, unchanged
0.000002 component limit, exact culling/opacity meaning and report stages.
The [checker](../../../tools/second_target_c234/check_materials.py) runs on the
CPU and starts no destination application. Its explicit
[controls](../../../tools/second_target_c234/tests/run_controls.py) require the
preserved handoff inputs; they are not part of broad product-test discovery.

A successful check establishes neither native capture provenance nor Godot
support. Native execution, normal/pose comparison, rendering, persistence,
cross-target semantics and the remaining C220 prerequisites retain their own
uncompleted gates. The [C220 plan](../second-target-c220/PLAN.md), frozen
[C221 admission](../second-target-c221/CONTRACT.md), and
[C222 correspondence](../second-target-c222/CONTRACT.md) remain unchanged.
