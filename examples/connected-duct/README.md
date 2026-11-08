# Join and repair a hollow duct

An elbow and a straight duct meet at (4, 0, 4) m. Their 2 m square exteriors line up even when the straight duct’s bore is offset. The editable example shows how an agent can detect that hidden obstruction in the delivered GLB, change one parameter and verify the repair.

![Offset inner opening with both outer rims aligned](offset.png)

## Run the example

From the repository root, choose new output directories. Use Python 3.12 with the repository’s verification dependencies. The [nominal assembly](assembly.ok) and [wider variant](assembly-wide.ok) import the same [pinned parts module](parts.ok).

```sh
python3 examples/connected-duct/export_cases.py /tmp/duct-cases
python3 examples/connected-duct/agent_repair.py examples/connected-duct/assembly.files.json /tmp/duct-agent
python3 tools/verify_connected_duct.py /tmp/duct-agent/repaired.glb
```

Inspect the six direct exports and their measured results in `/tmp/duct-cases/cases.json`. The Agent run writes its request/response pairs under `exchanges/` alongside each accepted source bundle and GLB. The checker returns a nonzero exit status for the deliberately defective export.

## What changes at the seam

Both parts use the adopted framed polygon loft. A shared function constructs their outer and inner rings. The straight duct’s `bore_shift` moves only its opening. A 2 m shift puts that opening outside the exterior and the Agent rejects the edit. A 0.25 m shift produces a valid individual part but leaves only 0.75 m² open where the two 1 m square bores meet. Restoring the shift to zero reproduces the original artifact.

![Repaired opening with both inner and outer rims aligned](repaired.png)

The independent [checker](../../tools/verify_connected_duct.py) reads the delivered triangles, checks both complete boundary loops, looks for triangles crossing the opening, and verifies the two opposite face directions and plane spacing. The [joint contract](joint-contract.md) specifies the tolerances. The wider opening measures 1.5625 m². A quarter-turn about the straight duct’s own axis preserves the square opening. Tilting the axis 90° or shrinking only one bore fails.

Both parts remain stationary and retain separate annular end faces on the same plane. The checker measures the cross-section at this joint and the centerline of the straight segment. The two meshes remain separately editable. Airflow and wall integrity away from the joint require separate checks.

## Move the assembly and repair the same opening

The [oblique assembly](assembly-oblique.ok) rotates both parts about the axis (0, 0.6, 0.8) and then translates them by (3, −2, 5) m. The elbow outlet and straight inlet now meet at (6.424, 2.4544, 5.6592) m. The [placement contract](oblique-contract.json) gives both port normals and both boundary polygons in world coordinates.

![A quarter-metre offset leaves the outside rims flush but blocks a strip of the opening](oblique-offset.png)

Run these commands from the repository root with fresh output directories. The Agent workflow first rejects an edit that would put the opening outside the duct, then exports the valid offset and its repair.

```sh
python3 examples/connected-duct/export_oblique.py /tmp/duct-oblique-direct
python3 examples/connected-duct/agent_repair.py examples/connected-duct/assembly-oblique.files.json /tmp/duct-oblique-agent
python3 tools/verify_connected_duct.py /tmp/duct-oblique-agent/defective.glb --placement oblique
python3 tools/verify_connected_duct.py /tmp/duct-oblique-agent/repaired.glb --placement oblique
```

The defective check exits with status 1. Its measured world displacement is approximately (−0.144, −0.0864, −0.1852) m. The two square bores overlap by 0.75 m². Setting `bore_shift` back to zero restores the full 1.00 m² opening and the original source revision and GLB bytes. The checker projects the delivered triangles into the selected port frame. The `fixed` and `oblique` settings correspond to the two authored placements in this example. [View the repaired joint](oblique-repaired.png)

## Place the straight duct from its exported geometry

The [misplaced assembly](assembly-misplaced.ok) starts with the inlet 0.375 m away from the elbow outlet and tilted 12°. The authoring script gives the [placement solver](fit_placement.py) the GLB bytes. The solver uses end-face triangle winding to recover each outward normal and boundary edges to locate the square rims. Four rotations can match a square. It chooses the one that moves the straight duct through the smallest angle.

Run these commands in the repository root with the verification dependencies and fresh output directories.

```sh
ex=examples/connected-duct
python3 "$ex/agent_place.py" "$ex/assembly-misplaced.files.json" /tmp/duct-placement
python3 tools/verify_duct_placement.py /tmp/duct-placement/defective.glb /tmp/duct-placement/repaired.glb
python3 "$ex/placement_controls.py" /tmp/duct-placement/defective.glb /tmp/duct-placement-controls
```

The Agent changes the straight occurrence’s placement in the accepted source and retrieves the new GLB in chunks. Inspect the two `.ok` files, `fit.json`, `summary.json` and the protocol records under `exchanges/`. The [independent reference](third-contract.json) fixes the expected world positions and directions before the repair. The verifier compares both complete rims, the straight axis and the 1.00 m² opening to that reference. The controls exercise a straight duct with its opposite end at the seam and a flush joint with a half-turn of unnecessary roll.

This example selects the two stationary root occurrences named `elbow` and `straight`. It uses the rectangular, concentric ports of this parts module.

[See the gap and tilt before repair](placement-before.png) · [See the flush joint after repair](placement-after.png)

## C164 · Select one of two identical elbow outlets

The straight duct `link` starts 0.375 m from the outlet of `bypass` and 4.018 m from the requested `outbound` outlet. Both elbows use the same imported part and expose a region named `top`. The authoring script accepts an occurrence name and a region name for each side of the joint. It fits the selected rims from their exported triangles and sends one Agent/0.11 edit to the placement of `link`. [Assembly source](assembly-selection.ok) · [Frozen joint contract](selection-contract.json)

| Initial placement | Requested joint | Flush decoy control |
| --- | --- | --- |
| [View the gap and tilt near bypass](selection-before.png) | [View link fitted to outbound](selection-after.png) | [View link fitted to bypass](selection-decoy.png) |

From the repository root, run these commands with the verification dependencies installed. Each invocation writes the source, delivered artifacts and Agent exchanges into its own directory.

```sh
ex=examples/connected-duct
out=$(mktemp -d)
fit_joint() {
    python3 "$ex/agent_select.py" "$ex/assembly-selection.files.json" "$out/$1" \
        --elbow "$2" --elbow-region top --straight link --straight-region bottom
}

fit_joint target outbound
fit_joint decoy bypass
python3 tools/verify_duct_selection.py "$out/target/defective.glb" "$out/target/repaired.glb" \
    --decoy-control "$out/decoy/repaired.glb" > "$out/measurements.json"
```

The independent verifier measures both rims, the opposing face normals, the straight axis and the shared opening. Four rotations align the square profiles. The shortest correction is 12°. The repaired target has a maximum rim-corner separation of 0.56 μm against a 10 μm tolerance, and the opening measures 0.99999970 m². The control is flush against `bypass`, 4 m from the requested joint.

The next two runs exit with status 2. An unknown name has no matching occurrence. The shared elbow class matches both. Each run saves the rejection reason in `summary.json`. The two `cmp` commands verify that the accepted source bundle is byte-identical after rejection.

```sh
fit_joint unknown missing || test "$?" -eq 2
fit_joint ambiguous package/example.connected-duct-parts/duct-parts/definitions/elbow || test "$?" -eq 2
cmp "$out/unknown/defective-bundle.json" "$out/unknown/after-rejection-bundle.json"
cmp "$out/ambiguous/defective-bundle.json" "$out/ambiguous/after-rejection-bundle.json"
```

## C165 · Fit both ends of a straight duct

The request joins `outbound/top` to `link/bottom` and `link/top` to `inbound/bottom`. The straight starts 4 m long, off-axis, and facing the wrong direction. The separately pinned [1.1.0 parts module](parts-span.ok) makes its length editable. The fitter measures the two stationary port frames in the starting GLB, sizes the straight to 5.75 m, and submits its placement and span in one revision-guarded Agent edit. The elbows remain stationary. [Starting source](span-achievable.ok) · [Fitted assembly and joint close-ups](span-fitted.png)

From the repository root, use the same verification environment as for C164. Each run needs a fresh output directory.

```sh
ex=examples/connected-duct
out=$(mktemp -d)
fit_span() {
    python3 "$ex/agent_span.py" "$ex/span-$1.files.json" "$out/$2" \
        --upstream outbound/top --inlet link/bottom --outlet link/top --downstream "$3" "${@:4}"
}
fit_span achievable target inbound/bottom
python3 tools/verify_duct_span.py "$out/target/defective.glb" "$out/target/repaired.glb"
fit_span incompatible offset inbound/bottom || test "$?" -eq 2
cmp "$out/offset/defective-bundle.json" "$out/offset/after-rejection-bundle.json"
```

Run the snippet in Bash. The verifier uses both complete square rims, triangle winding and the common opening at each joint. The [frozen limits](span-contract.json) allow 10 µm of rim separation and 1.00 ± 0.00005 m² of open area. The [incompatible scene](span-incompatible.ok) shifts the downstream center sideways by 0.25 m. The script returns status 2 before submitting an edit.

To exercise the negative controls, substitute a different named downstream port or ask the driver to export a deliberate error in its own run.

```sh
fit_span achievable bypass bypass/bottom
fit_span achievable short inbound/bottom --control incorrect-length
fit_span achievable reversed inbound/bottom --control wrong-end
```

Scored against the original request, the bypass fit overshoots by 5 m and the short connector falls 1.75 m short. The reversed straight occupies the correct space with its two signed ends in the wrong order. The example supports stationary root occurrences from the supplied parts and a straight growing along its local positive Z axis. Each scene explicitly requests up to 200,000 operations and 30 seconds for the four-occurrence export.

## C166 · Route a 90° elbow between two straight ducts

The [starting scene](route-achievable.ok) has two stationary ports with perpendicular axes. The router locates both ports in the exported triangles, measures the rigid elbow’s inlet-to-outlet displacement, and solves for the length of each straight along its own axis. In the [frozen case](route-contract.json), the first straight runs 2.75 m in +Z and the second runs 4.5 m in +X. One Agent/0.11 transaction changes the three placements and two lengths. [Fitted route and four cap close-ups](route-fitted.png)

From the repository root, run the driver and the independent four-joint checker with the verification dependencies installed. The five names are the ordered source, first straight, bend, second straight and sink. Every connection joins the upstream `top` to the next occurrence’s `bottom`.

```bash
ex=examples/connected-duct
out=$(mktemp -d)
route() {
    python3 "$ex/agent_route.py" "$ex/route-$1.files.json" "$out/$2" \
        --chain outbound lead turn tail inbound "${@:3}"
}
route achievable target
python3 tools/verify_duct_route.py "$out/target/defective.glb" "$out/target/repaired.glb"
route incompatible incompatible || test "$?" -eq 2
route achievable wrong-turn --control wrong-turn
route achievable one-sided --control one-sided
route achievable rollback --control rollback
python3 tools/audit_duct_route_exchanges.py "$out" "$ex"
```

The router checks that each measured straight length falls within the framed-loft profile’s constructible range of 0.001–100 m before it submits an edit. The checker measures both rims, opposing cap normals, and the open area at each of the four joints. The allowed corner separation is 10 µm and the required opening is 1.00 ± 0.00005 m². In the [skew scene](route-incompatible.ok), the fixed axes miss each other by 0.25 m. The driver records this refusal before sending an edit. The wrong-turn control reverses the direction of the elbow, and the one-sided control shortens the final straight by 1 m. The rollback control submits five patches with a stale final precondition and retrieves the accepted source and export again.

This example uses stationary root occurrences of the supplied square-bore parts. It checks a specified single-bend route. Collision avoidance, physical attachment and flow simulation are outside its scope.
