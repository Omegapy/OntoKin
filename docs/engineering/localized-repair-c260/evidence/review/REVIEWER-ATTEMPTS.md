# Preserved reviewer inspection attempts

These are audit-tool mistakes, not product failures.

1. An initial read-only GLB probe attempted `extras.ontokin.objects` and raised
   `KeyError: 'objects'`. The actual occurrence mapping is
   `extras.ontokin.program.occurrences`, with corresponding object nodes.
2. A follow-up probe treated that mapping as a list and raised `KeyError: 0`.
   Inspecting its type showed a dictionary keyed by display path. No input
   file was written or modified by either probe.
3. The first complete fixed-input inspection zipped the source-derived rows in
   canonical key order against the author's explanatory row list in literal
   order. It stopped at `second.fingers["upper"].flex`. Row order is explicitly
   not identity in the contract, so this was a reviewer assertion error. The
   corrected audit compares those records by complete path and requires a
   unique, complete set. Its original script, failure report and logs remain
   under `attempt01/`. The author files were unchanged by this correction.

The corrected inspection passes 242 assertions. A separate source-span audit
passes 142 assertions. Neither executes a hinge implementation or the planned
future control matrix.

