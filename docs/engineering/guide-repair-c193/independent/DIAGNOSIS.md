# Independent diagnosis before C193 qualification

The retained failures come from a short angular residual in the native guide.
Projection removes that rotation, which moves the distant left-shoe vertices
by more than the unchanged 0.2 mm allowance. The body-center transverse drift is
much smaller. This is an observed geometric mechanism; the native interface
does not expose contact impulses or Bullet's internal iteration history.

## Retained witnesses

The source places the left shoe center 115 mm forward and 45 mm above its
carriage center. The far top corners are approximately `(180, 70, ±40)` mm in
the carriage frame, 197.231 mm from the body origin. A small body rotation thus
has a larger effect at those shoe corners than at the body center.

| Stop | Peak frame and time | Native-to-final peak | Continuous bound | Maximum body rotation | Maximum body-center transverse drift |
| --- | --- | ---: | ---: | ---: | ---: |
| 362.5 mm | 352; 1.466666667 s | 0.244637657 mm | 0.271961075 mm | 0.072435944° | 0.004388392 mm |
| 372.5 mm | 370; 1.541666667 s | 0.292416239 mm | 0.322647313 mm | 0.087797959° | 0.006765127 mm |

Both maxima are on `left_shoe`. At the 372.5 mm witness, the native-minus-final
vertex displacement is `(-0.114663, 0.266484, -0.036685)` mm in source XYZ.
The body rotation contributes approximately `(-0.114668, 0.273256, -0.036680)`
mm, and transverse body translation contributes `(0, -0.006765, 0)` mm. Their
remaining difference is below 0.00001 mm per component. The direct measurement
therefore agrees with the source-frame rotational explanation.

At 362.5 mm, maximum body translation occurs at frame 351, whereas the vertex
and rotation peak occurs at frame 352. The table's independent maxima must not
be treated as simultaneous observations. All detailed coordinates, source-frame
axes and near-contact samples are in [the edit audit](evidence/retained-edit.json)
and [the reuse audit](evidence/retained-reuse.json).

## Frozen controls

The repairer executed exactly the [four predeclared controls](frozen/diagnostic-controls.json),
all at the retained 372.5 mm stop. Independent decoding retained the original
mapping algorithm and limits.

| Control | Only physical change | Native peak | Continuous bound | Mapping result |
| --- | --- | ---: | ---: | --- |
| N0 | None | 0.292416239 mm | 0.322647313 mm | Fail |
| N1 | Remove left-shoe collision component | 0.000016660 mm | approximately 0 mm | Pass |
| N2 | Both GENERIC guides: 100 → 400 override iterations | 0.165544488 mm | 0.181935687 mm | Pass |
| N3 | Both GENERIC anchors at source shoe centers | 0.249242746 mm | 0.404395628 mm | Fail |

N0 reproduces every retained native sample exactly. N1 travels the full 250 mm,
passes through the stop, and has zero body angular and transverse residual.
This ties the stopping response and residual to the enabled shoe collision in
this controlled scene. N2 reduces the maximum angular residual to 0.050932698°.
It leaves 0.018064313 mm of margin under the continuous mapping limit. That is
enough to justify qualification of this correction, but does not establish
success for the other required cases. N3 remains rejected and is not combined
with N2.

Independent configuration comparison confirms the prescribed single physical
change in each control and exact unchanged native trajectories for the right
lane, base and stops. The source design, compound mass ownership, motors,
collision boxes, capture times and native X projection rules remain unchanged.
The initial guide/body frames of N2 and the moved guide frames of N3 were also
read directly from their saved Blender scenes without resimulation.

N2's first diagnostic postprocessor rejected the order of two named left-stop
driver variables. Serialization had sorted their names, while the validator
used the earlier dictionary order. The variables retained the same names,
targets and expression. The failed receipt is preserved. Separate postprocessing
against the exact serialized backend completed without native execution;
the original native result, scene, canonical input, backend and constructor
hashes all match. [Control and preservation review](evidence/diagnostic-review.json)

The nonaligned ideal contact times remain a possible explanation for why these
two positions excite a larger transient. The frozen controls do not establish
capture phase as the cause. No stop-position sweep was performed.

## Correction recommended for qualification

Select only the guide-iteration change under separately versioned source and
backend bindings. Preserve the prior implementation and contract unchanged.
World and motor iteration settings remain 100; each GENERIC guide uses 400.
The capture remains 481 samples over two seconds, with ten configured substeps
per frame. The original elapsed-time and operation ceilings remain in force.
Configured solver iteration work is increased and must be disclosed; the host
operation counter does not measure Bullet's internal iterations.

Both new `.ok` and direct-Python routes must execute the same identified
constructor. Before acceptance, run the frozen full case matrix, replay every
saved scene, compare the two routes' actual canonical inputs and outputs, and
complete all original numerical and receiving-application gates. None of these
diagnostic outputs is a qualified delivery or a new participant comparison.
