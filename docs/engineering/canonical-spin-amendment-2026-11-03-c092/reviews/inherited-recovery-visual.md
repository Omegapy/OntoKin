# Candidate03 inherited captures and separate surface recovery

**All 35 current captures were directly inspected in two distinct groups: 23 from the failed original full run, and 12 from the single fresh surface recovery.** No visible blocking rendering or UI defect was observed in these stills. Every image is individually bound by path, byte count, SHA-256, mode and dimensions, and its bytes were rechecked at closure.

The original full invocation remains **failed: 30 passed roles, 2 failed roles and 2 blocked roles**. Its surface-agent build failed, and the dependent format/browser roles were blocked. The separate fresh invocation passed those three roles under the unchanged commands, inputs, environment construction and 3,600-second supervision. Its results supplement the retained evidence; they do not change the original outcomes.

## Recovery output and store integrity

The recovery produced **1,225 files totaling 34,682,562 bytes**. This review independently checked the complete file membership, bytes, hashes, modes and directory modes against both the private execution output and the closed selected evidence. Recorded source inventories match before and after. All 718 original failed artifact files still match the first retained inventory.

The recovery database is 12,791,808 bytes, SHA-256 `f364e308956d2a534aee4655ba509d2ef60cb80208c88a04936a31c2a76a1455`. No WAL, SHM or journal companion was present in the closed recovery output. Only a new private byte-exact inspection copy was opened through SQLite, using `mode=ro&immutable=1` and `query_only=ON`. Both quick_check and integrity_check returned **ok**. All **22** workflow artifact records matched the stored blob, stored hash, source revision and retrieved scene file exactly. The inspection copy and both output trees remained unchanged afterward.

These checks do not explain the original database corruption or show that it cannot recur. The original failed store, log, diagnostics and complete artifact tree remain preserved. The final torque A08 deadline blocker also remains open.

## Direct observations of the 12 recovery captures

| Recovery capture | Direct observation |
| --- | --- |
| `composition-generated-animated.png` | At 1.500 s, the three separated tapers retain the same apparent front-view arrangement, and all three blue regions remain visible. The full scene, wrapped material text and playback controls remain readable. |
| `composition-generated-front.png` | At 0.000 s, three separated clay-and-blue tapers are visible across the scene, with increasing width from left to right. All three complete outlines fit the viewport. The longer material row wraps within the page without covering the identity labels. |
| `composition-generated-side.png` | At 0.000 s, the three objects align in depth; the nearest taper is visible in front and smaller blue tips extend behind it. The visible silhouettes and color transition are coherent. Depth overlap limits inspection of the rear surfaces. |
| `composition-ordinary-animated.png` | At 1.500 s, both objects remain in the same apparent front-view arrangement as at 0.000 s, with clear outlines and the left blue region. This still supplies visible-state evidence only; it does not establish a motion requirement or continuous playback. |
| `composition-ordinary-front.png` | At 0.000 s, two large faceted tapers are clearly separated: a smaller blue-topped left object and a larger clay-colored right object. Both complete silhouettes, the grid and the controls are visible. |
| `composition-ordinary-side.png` | At 0.000 s, the side projection shows the foreground clay-colored taper centered and fully in frame. The aligned rear object is occluded; this view cannot by itself confirm both separate surfaces. |
| `palette-repaired-animated.png` | The 1.500 s still shows both tapers separately with the left blue region intact. Their displayed positions/profile differ slightly from the initial front still, with neither object clipped and no apparent disconnected surface. |
| `palette-repaired-front.png` | At 0.000 s, two separated faceted clay-colored tapers are fully visible, with a blue upper region on the smaller left object. Their outlines and material boundary appear coherent. Fixture, time, material and artifact-identity labels are readable. |
| `palette-repaired-side.png` | At 0.000 s, the side view aligns the objects, leaving a central clay-colored taper visible in front. Its silhouette is continuous and fully framed. Occlusion prevents independent inspection of the rear object or its blue region in this frame alone. |
| `rotated-release-animated.png` | At 1.500 s, the two tapers remain separately visible with changed relative position/orientation compared with the initial front still. Both blue ends and full silhouettes stay within the viewport; no visible tearing, detached material region or blank render is apparent. |
| `rotated-release-front.png` | At 0.000 s, two horizontal clay-and-blue tapers are separated across the middle of the viewport, both with blue narrow ends pointing right. Both complete silhouettes and material boundaries are visible. |
| `rotated-release-side.png` | At 0.000 s, the end-on projection overlaps the pair, showing a blue cap and band in front of the clay sections. The cap is filled and the visible outline is continuous; the view cannot independently expose every rear surface. |

## Review limits and exact records

The original 23-image observations remain in `ORIGINAL-VISUAL-REVIEW.json` and `.md`. The new images are separately listed in `RECOVERY-CAPTURES-MANIFEST.json`; all 12 are bound with their observations in `INHERITED-RECOVERY-VISUAL.json`. `RECOVERY-INTEGRITY.json` and `RECOVERY-SQLITE-DIAGNOSTICS.json` retain the independent output and copied-store checks.

These images support visible geometry, material, framing and UI observations. They cannot establish exact numerical bounds, source semantics, continuous playback or durability. Side views sometimes occlude objects, and the original P04/P11 objects are too small for fine surface-detail inspection. No historical image was substituted, and no current image was modified or regenerated during this review.
