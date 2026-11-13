# C223 / R01: complete validation inputs and explicit bytecode policy

The local validation driver copied an incomplete input set and allowed child Python processes to write bytecode caches. Those two defects caused failures in the historical [C210 aggregate run](../semantic-export-c210/REGRESSION.md). C223 repairs the driver without changing product behavior or weakening the frozen independent readers.

The shared input inventory now includes top-level `fixtures/`, so the same files enter both the isolated workspace and its source-stability checks. Every planned Python command receives `-B`. The step environment also sets `PYTHONDONTWRITEBYTECODE=1`, which reaches ordinary Python descendants. A parent-only `-B` does not propagate to a new interpreter.

[Results](RESULTS.md) identify the exact source, original reproductions and focused checks. [Independent review](REVIEW.md) tests actual copies, child launches and frozen-reader refusals. The [owner tracker](../review-integration-c221/RECOMMENDATIONS.json) retains all nine records and 41 acceptance criteria.

This is the bounded R01 maintenance repair. Full aggregate regression is R02 and has not run here. Historical failed regressions, the strict Blender normal failure, Godot lineage/rendering limits and every release obligation remain unchanged. No native application, product-source evaluation, export, import, render or scene write was part of this step. After verified publication and the saved C223 handoff, follow [R02 next steps](NEXT-TASK.md).
