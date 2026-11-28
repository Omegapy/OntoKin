# C272 playback observation (TASK-026, REQ-022, DEC-009)

**What was played.** This was V1's regenerated GLB, the 0.75 m state:
- the delivered run's `delivery/cases/V1/record/files/retained/scene.glb`, also committed as `runs/delivered-d10c9f62/cases/V1/record/files/retained/scene.glb`;
- SHA-256 `05ebe856d3fdb96dce4b6aa55906be5ae67501bcaede9112abc30b703905b5d8`, 185,236 bytes.

The viewer loaded that file from its actual bytes, and [capture.json](playback/capture.json) records the digest of the file it loaded.

**Viewer configuration.**
- The project's offline viewer, `examples/visual/viewer.html`, with its committed bundle (digests in capture.json). The file was loaded through the viewer's local-file input.
- Headless Chromium 141.0.7390.37 from Playwright 1.56.1, WebGL 2 on ANGLE/SwiftShader, viewport 1440 × 1060.
- Joint markers, motion paths and the reference grid on; network requests blocked. None was attempted, and no page or console error occurred.
- Driven by [`inspect_playback.mjs`](../inspect_playback.mjs) under Node.js 22.23.5, on the owner's Mac, on 2026-11-28.

**Times looked at.**
- Stepped frames at 0, 0.5, 1, 1.5 and 2 s.
- One frame after real playback: Play from 0 s, then Pause, which held at 0.65 s.

The six PNG frames are working evidence beside the clone (DEC-013). Their SHA-256 values are in capture.json.

## What was seen

I looked at each of the six frames.

- **0 s.** Two grey racks stand upright on the grid. The left rack (`first`) carries three blue blades, all horizontal and pointing right. The middle blade is visibly longer than the upper and lower ones. The right rack (`second`) carries five horizontal blades of equal length. A dot marks each blade's pivot at the rack. The inspector shows `first` at (−1.000, 0.000, 0.000) m.
- **0.5 s.** The left rack has moved up; the inspector reads Y 0.100. Its middle blade has turned upward about its pivot, to roughly a quarter of a right angle. The upper and lower blades are still horizontal. The right rack looks exactly as at 0 s.
- **0.65 s (after Play and Pause).** The middle blade has turned a little further than at 0.5 s; the inspector reads Y 0.130. Playback stopped where Pause was pressed.
- **1 s.** The middle blade points up and to the right at about 45°, and its tip comes close to the outer end of the upper blade. From this viewpoint the two appear to meet; no contact or collision response is shown, and none exists in this file. The rack reads Y 0.200.
- **1.5 s.** The middle blade holds its 45° pose, the rack keeps rising (Y 0.300), and the right rack and its five blades are unchanged.
- **2 s.** The same 45° pose. The rack reads Y 0.400, the end of the clip; the timeline shows 2.000 / 2.000 s.

Throughout, only the left rack translates and only its middle blade rotates. The other two blades of that rack move with it without turning. The whole right rack stays still.

## What this establishes and what it does not

It establishes that this regenerated GLB loads and plays in the named viewer configuration and
that the motion looks as the source describes it. That is the meaning of actual playback in
OK-ENG-002.

It does not establish numerical correctness. The numerical result comes separately from the
C255 pose check and from the Three.js comparison of all 126 poses in `gltf-validation/`. It
does not establish live constraint solving, collision, physics or action execution in any
destination, and it is no statement about Blender, Unreal, Godot or OpenUSD.

The animation is source-defined and delivered as recorded playback: the GLB holds sampled
motion only. Its sites, actions and events are carried only by the semantic sidecar.
