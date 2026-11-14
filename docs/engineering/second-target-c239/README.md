# C239: combined CPU observation checks

An observation envelope binds six files: geometry, materials, surface normals, object poses, semantic/source retention, and a declared map between observed and source triangle corners. C238 verifies that these files belong together. C239 runs the existing numerical and semantic checkers on one private, verified copy of their exact bytes.

The checker independently derives geometric correspondence and compares every one of the 23,400 declared map rows. It retains each component's original successful result, measured loss or structural refusal, including all 18 source identities, 126 pose samples, 14 feature treatments, four retained files and both source units. It does not turn a matching set of files into evidence of a native capture session.

- [Versioned contract](CONTRACT.md) fixes scope, source pins, snapshots, report meanings and controls before execution.
- [Results](RESULTS.md) identifies exact source, executed checks and known limits.
- [Independent review](REVIEW.md) records the separately constructed oracle and adverse cases.
- [Next bounded task](NEXT-TASK.md) prepares the native capture and execution protocol without starting a native process.

The unchanged [C220 second-target plan](../second-target-c220/PLAN.md) and [C238 admission contract](../second-target-c238/CONTRACT.md) remain prerequisites. A CPU pass establishes only these finite checks. Native provenance, a verified rendering route, saved-scene persistence, cross-target comparison and full R07 acceptance remain pending. The original strict Blender normal failure remains failed.
