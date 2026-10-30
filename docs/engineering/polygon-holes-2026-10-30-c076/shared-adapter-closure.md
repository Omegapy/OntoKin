# C076-SHARED-001 closure readback

**Closed at source readback:** candidate `15c45f3ee3ed39883188e71bbde0e4d1482f8757`, tree `1eda7611fdd1294aaf7d9764e881dfdd8f41725e`.

This supplements `shared-adapter-review.md` and `shared-adapter-review.json`. Those original records remain unchanged and continue to describe the missing-counts finding at `e114f9bf3a99d27f5655c43cd2240a09d198cbe9`.

## Verified repair

`holes_inspection.holes_summary` now returns:

- `cap_triangle_count = n + 2h - 2`, the number of triangles on each cap.
- `palette_count = len(counts)`, including valid unused palette entries.
- `used_region_count = len(regions)`, counting only regions with emitted triangles.

The region construction loop retains a cooperative callback for each palette entry. The `.9` response schema requires all three fields, with finite bounds of 1–78 for cap triangles and 1–16 for palette/used-region counts. The `.9` README explains their distinct meanings. The actual Agent summary test now asserts values 8, 4 and 4 for the frozen square opening.

The original request for a targeted unused-palette assertion was a verification recommendation. The repaired formulas distinguish total and used palette entries directly, and existing native geometry tests retain unused-material behavior. This readback identifies no remaining source defect in those fields. It does not claim that an additional unused-palette Agent test was executed.

All other previously reviewed adapter files retain the same bytes as the original review. The frozen adoption also retains its exact bytes. Earlier loft/simple-extrusion summary code was not changed to add these fields.

## Boundary

No product test was executed during this closure review. This closes the specific source/schema/documentation gap; actual candidate execution and integration evidence retain their separate source identities. Root's recorded Agent and acceptance results are not reattributed to this readback.
