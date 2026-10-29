# Proposed C066: cold native-sphere radius candidates

**Status: proposed, not started or scheduled.** Reconcile fresh main, STATUS, branches/PRs, workflows and the latest explicit C065 scope/window release in Issue #26 before claiming this task. Start from actual current main; the archive-retention branch is never a development base.

## One bounded question

Can a finite, source-bound shortlist of native-sphere vertices replace actual cold exact L1-radius candidate work in the independent supplied-byte reader, preserve the exact returned radius and vertex error, and pay for its complete selection and admission cost?

Begin with the 32-segment, 16-band sphere constructor in `ontokin/geometry.py` and `_vertex_extrema_uncached` in `ontokin/reach_conformance.py`. The target is the exact rational maximum of `abs(x)+abs(y)+abs(z)` over the **actual generated binary64 vertices**. An ideal Euclidean radius or `radius*sqrt(3)` is not the same result. A small set near the discrete latitude/longitude extrema is a hypothesis; actual constructor rounding and ties require proof.

Keep this a source-only feasibility task until a positive complete-request premise is established. C065 found at most four removable arithmetic units per signed eye pair and rejected its four-copy bridge. This sphere question addresses a different cost pool; it must not reopen that rejected copy schedule under a new name.

## Preserve the actual baseline

- Keep every `independent_geometry_point` charge and every actual source-to-binary32 vertex comparison in `_vertex_extrema_uncached`.
- Keep all per-component error accumulation and the same exact final vertex-error result.
- Preserve the existing `_vertex_extrema` cache and all warm occurrence checks, including its source identity, stored accessor checks, operand-limit changes and rejection behavior.
- Preserve independent source-mesh construction, site-radius additions, current limits, source authority and original request options.
- Do not count existing upward floating screens, repeated-maximum witnesses, three-component error decoding, repeated-mesh reuse or repeated loft-corner placement as new savings.

Relevant current source: `reach_conformance.py` 728–796 for cache reuse, 799–847 for the cold path, 850–939 for geometry and site-radius construction; `geometry.py` 15–16 and 47–75 for the sphere; `scene.py` 349–416 for native mesh recipe capture and independent mesh caching. Re-resolve these locations against the new pinned head.

## Proof required before implementation or requests

1. Derive a finite candidate set from actual source recipe and generated-coordinate semantics, including all rounding-sensitive ties. Python `math.sin`/`math.cos` calls alone are not a certified error enclosure. State the exact supported domain and why excluded vertices cannot attain a larger exact L1 sum.
2. Preserve the original exact radius and error outputs. A looser conservative radius changes downstream proof costs and is a different proposal requiring its own behavior analysis.
3. Keep original evaluation positions or prove a supported restriction that preserves callback and first-exception behavior. Computing a future vertex's exact radius before earlier supplied vertices are validated can reorder a failure.
4. Define live authority for the constructor recipe, mesh coordinates, arithmetic/dispatch domain and shortlist lifetime. A frozen tuple is not automatically sufficient protection or a funding mechanism.
5. Charge construction, source/leaf/type/limit/claim checks, temporary copies, lookups, selections, rejections and fallback. Count only cold exact candidate operations actually removed beyond the current screens, including all keys/occurrences, cache effects and later request work.

C064's aggregate geometry counts include other work and omit source binary64 coordinate arrays and the incumbent-radius progression. They cannot establish shortlist hits or savings. If new observation is needed, first state exactly which source-backed premise survives and what bounded observation would resolve; no product instrumentation follows merely from the size of a cost pool.

If this candidate cannot meet the proof and accounting obligations, close the exact failed premise. Preserve all original failures and requirements. Completing a positive increment remains separate from completing the original request below 100,000 operations.

Git LFS migration, hosted execution and branch-history cleanup are outside this design task. All original reach, Agent, compatibility, independent destination/visual/hostile/inherited and full-product obligations remain open as recorded. No worker, schedule, experiment or acceptance claim is created by this proposal.
