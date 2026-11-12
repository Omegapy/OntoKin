# C221: CPU-only source authority checker

C221 implements the first bounded part of [C220 Godot preparation](../second-target-c220/PLAN.md): validate the exact retained inputs and the full source-part mapping before future observation work. The tool is isolated from product runtime and does not launch a destination.

- [Scope and completion boundary](SCOPE.md)
- [Versioned checker contract](CONTRACT.md)
- [Observed checks, limitations and publication](RESULTS.md)
- [Independent review](REVIEW.md)
- [Next bounded CPU task](NEXT-TASK.md)

Input validation does not complete the observer, numerical comparison, persistence or execution protocol. Godot behavior and rendering remain unverified; the original Blender normal failure remains failed.
