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

## Check a parked sibling

To park a second cart beside the entrance, add the following declaration to the `Entrance` scene in [src/main.ok](src/main.ok). Place it after the original cart and before the first `at 0[s] sequence`. The parked cart uses the same mesh and starts at a separate world position.

```text
    object parked @ "parked-cart": Cart {
        placement = pose(world, vec3(-1.55[m], 0.16[m], -0.60[m]), quat(1, 0, 0, 0));
        velocity = vector(world, 0[m/s], 0[m/s], 0[m/s]);
        omega = vector(world, 0[rad/s], 0[rad/s], 0[rad/s]);
    }
```

From the repository root, reuse the pinned runtime and build into a new output directory. Supply both selectors when checking the two-cart export.

```sh
python3.12 -IB examples/service-entrance/build.py ../ontokin-service-runtime ../service-entrance-two-carts --operations 450000 --elapsed-ms 80000
python3.12 -IB examples/service-entrance/checks/check_passage.py examples/service-entrance/src/main.ok ../service-entrance-two-carts/accepted-bundle.json ../service-entrance-two-carts/sliding-gate.glb --moving-cart cart --parked-cart parked-cart --width 0.58
```

Each selector accepts the source identifier or the quoted stable element ID, so `--parked-cart parked` selects the same object. The single-cart command above still selects its only cart automatically. The checker matches each selection to its delivered node and checks the passing cart's trajectory and aperture clearances. It also checks that the parked cart holds its authored world pose throughout playback. `parked_cart.separation` gives a conservative minimum gap in metres to the moving cart, gate and post, including the intervals between stored poses. An intersecting or touching pair of bounding boxes fails this check. A rejected check exits with status 1 and gives the cause in `diagnostics`.

The checker rejects meshes that use `EXT_mesh_gpu_instancing` because individual instances can have additional transforms that change their clearance.
