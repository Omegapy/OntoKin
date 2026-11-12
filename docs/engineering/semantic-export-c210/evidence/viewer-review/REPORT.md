# C210 browser-checker review and scope-review closure

## Reviewed identity and result

Reviewed `tools/verify_semantic_export_viewer.mjs` at SHA-256
`224adc41d466a33ca06886072779c07ea632d5a966ceb1101c36bb6bb62efca3`.
`INPUTS.json` records exact hashes of the new checker, legacy checker, actual
viewer source/bundle/HTML, pinned tooling, the original independent oracle, and
the two revised scope documents. `reviewed-viewer.mjs.txt` preserves the exact
reviewed draft.

The checker passes `node --check`. No browser or product process was executed
by this review. The actual browser result remains pending.

No current API mismatch was found. The viewer exposes the used `ready` and
`state` fields; state objects use position_m and orientation_xyzw. All addressed
controls and status strings match the current HTML/source. The pinned
Playwright injected implementation explicitly supports `fill()` on a range
input, sets its value and dispatches input/change events; the timeline handler
pauses playback and updates world transforms synchronously.

## Tighten before execution

### 1. Pin the observation set and retain declared numeric limits

The new checker accepts any seven samples. Repeated samples could produce the
advertised 126 comparisons per artifact without seven distinct observations.
Require the exact finite fixture times `[0, 0.25, 0.5, 0.75, 1, 1.5, 2]`, in
order, and a two-second clip. Both sources use that same planned interval.

Validate position vectors as exactly three finite numbers and quaternions as
exactly four finite numbers with positive norms. The original checker performed
these shape/finite/nonzero checks; the new checker checks only actual-component
finiteness. Malformed references should fail before comparisons.

The new checker uses a hard-coded 1e-6 time limit without inspecting
`reference.tolerances.time_seconds`. Require all three declared tolerances to
be finite, positive and within the original caps, then use the declared time
tolerance. This prevents weakening a stricter supplied reference.

### 2. Preserve or explicitly assign the omitted independent obligations

The legacy construction checker binds actual source bundle/unit bytes, the
accepted workflow, export report, GLB target/profile, frozen independent oracle
and source manifest. It compares browser poses against both evaluator samples
and the independent analytic expectations. The new wrapper currently binds
only GLB bytes, reference bytes and their metadata agreement.

The new wrapper also checks eighteen path-keyed browser objects but omits the
legacy exact metadata-object count, uniqueness and stable element_id checks.
The viewer uses Object.fromEntries, so duplicate metadata paths can collapse in
its exposed state. The unchanged independent oracle already supplies the
eighteen expected paths/element IDs for both revisions; these identity checks
can be retained directly.

These obligations may be satisfied by a separately executed independent
checker bound to the exact before/after artifact and source hashes. If so,
identify that evidence explicitly and do not describe this wrapper as the
same independent-oracle gate as the original verifier. The after revision
matches the frozen repaired fixture; the before revision's changed blade
requires the correctly derived 0.65 m expectation rather than the frozen
0.75 m geometry/offset. A fresh evaluator reference alone is not an independent
analytic oracle.

Khronos structural validation, independent Three.js geometry checks and the
semantic/source-binding checker remain separate required evidence. Screenshots
and successful playback do not replace them.

### 3. Keep actual visual inspection separate

The planned four screenshots and playback checks are appropriate bounded
observations. Inspect every resulting image before claiming visual acceptance.
The checker appropriately does not claim Unreal, UEFN, Blender, live physics,
continuous-time accuracy or authoring advantage.

## Confirmed retained behavior

The checker opens the actual local before/after GLBs through the existing
custom file input, waits for the ready local state, pauses at sample times,
compares browser world poses, checks active playback and stable pause, captures
both initial and moving states, verifies WebGL2, and rejects page/console/
network/resource failures. The badges remain honest about custom-import
source/conformance status.

## Scope-review closure

Both prior scope clarifications are resolved:

- GOAL and DECISION now identify the actual old restriction: general importer,
  capture pipeline or new production backend. The bounded receiving/second-
  target exceptions are explicit without claiming that all experiments were
  formerly prohibited.
- DECISION explicitly defers unfinished terrain/building, appearance/texture,
  transition/live-engine and scale/performance extensions while preserving
  already implemented profiles.

No remaining direction issue was found in those changed paragraphs. Their
exact reviewed hashes are included in `INPUTS.json`.

