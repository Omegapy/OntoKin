# Animate a cart passing through a sliding gate

A teal gate slides to the right. A gold service cart waits for the opening, travels two metres through it, then parks while the gate closes. The animation runs for 3.25 seconds. X runs across the opening, Y points up, and the cart moves along +Z.

## Build and check the animation

Use Git and CPython 3.12. Run these commands from the **repository root**. The first line checks for the tested runtime commit. A shallow or single-branch clone may need to fetch it from the repository’s `origin` remote. When Git already has the commit, the sequence works offline. Choose unused sibling paths for the runtime and the output.

```sh
git cat-file -e '3a1cd5785a9dd0c64d9b74ef97cdc5e6b609b117^{commit}' || git fetch --depth=1 --no-tags origin 3a1cd5785a9dd0c64d9b74ef97cdc5e6b609b117
git worktree add --detach ../ontokin-service-runtime 3a1cd5785a9dd0c64d9b74ef97cdc5e6b609b117
python3.12 -IB examples/service-entrance/build.py ../ontokin-service-runtime ../service-entrance-output --operations 450000 --elapsed-ms 80000
python3.12 -IB examples/service-entrance/checks/check_passage.py examples/service-entrance/src/main.ok ../service-entrance-output/accepted-bundle.json ../service-entrance-output/sliding-gate.glb --width 0.58
```

Open `../service-entrance-output/sliding-gate.glb` in a glTF viewer and play its timeline. The builder creates an empty project store for each run and records every public create, export and artifact-read exchange in the output directory. It checks the runtime commit, tree and clean Git status before importing OntoKin. Keep the runtime directory clean and make scene edits in your original checkout. You can reuse the runtime for later builds by running the last two commands with a new output path.

## Change the cart width

In [src/main.ok](src/main.ok), find `class Cart`. The first coordinate of each `planar_point` is its X position in metres. The four outer corners named `base-left`, `deck-left`, `base-right` and `deck-right` put the deck edges at −0.29 m and +0.29 m. The distance between the two edges is the cart's 0.58 m width. Keep the left and right edges equally far from zero to center the cart. The narrower bin has its own coordinates of ±0.23 m. The 0.62 m extrusion sets the cart's length along Z.

After editing, pass your target width to the checker's `--width` option. The checker reads the accepted source and the triangles in the exported animation. In its JSON output, `crossing.minimum_lateral_clearance_m` gives the gap to the post and to the gate panel while the cart passes through. A positive value is free space. The default cart leaves 0.46 m on each side. Collision response is disabled in this example, so an oversized cart can export successfully and still fail the passage check.
