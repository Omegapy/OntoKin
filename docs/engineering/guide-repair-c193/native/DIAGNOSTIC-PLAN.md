# C193 native diagnostic controls

This plan is frozen before diagnostic construction changes or fresh native runs.
The starting repository is `294d84ac5c5a15e07d042e5225646c2dab440293`.
The native worker owns this directory on branch `work/c193-native-repair`.
Historical C191/C192 sources, constructor, bindings, checks and results remain
unchanged. These controls are diagnostic outputs, not adopted backend deliveries.

## Observed failure and question

Reading the retained C192 traces reproduces both mapping failures. The largest
errors occur at outer left-shoe vertices after contact: 0.244637657 mm at frame
352 for the 362.5 mm stop, and 0.292416239 mm at frame 370 for the 372.5 mm stop.
At those frames the carriage rotation is approximately 0.00126425 and
0.00153236 radians. The right lane has no transverse or rotational guide motion.
The long source-defined shoe offset amplifies a small body rotation. This
identifies the observed geometric mechanism, not the cause inside Bullet.

The source frame is right-handed with Y up and millimetres; native Blender uses
Z up and metres. The native carriage frame is the source carriage center. The
left shoe center is 115 mm ahead and 45 mm above that frame. The compound
contains the declared shoe and the unchanged hidden carriage box. The GENERIC
guide and MOTOR both begin at the carriage center. A solver-owned 1 kg compound
is the only moving mass owner on each lane. Contact manifold/impulse and direct
native velocity are not exposed.

## Exactly four fresh diagnostic controls

All four use the retained direct-Python 372.5 mm source and the pinned Blender
4.5.3 executable, SHA-256
`5e15447670804c855fef6033ac9b8fd82696b762095becf0df79b1c2f8034397`.
Use a fresh empty scene and retain complete native configurations and all 481
samples. The shared encoder and original 0.2 mm projection checks are unchanged.

| ID | Sole deliberate change from N0 | Purpose |
| --- | --- | --- |
| N0 | None | Verify the diagnostic harness reproduces retained reuse samples. |
| N1 | Remove only the left shoe rigid-body component through its source enablement flag. | Test whether contact is required for the rotational response. |
| N2 | Increase both GENERIC guide overrides from 100 to 400 iterations. World and MOTOR remain at 100. | Test guide convergence with unchanged source, frames and contact geometry. |
| N3 | Move each GENERIC guide anchor to its source-derived shoe center. MOTOR and body frames remain at carriage center. | Test guide anchor sensitivity with unchanged geometry and solver iteration settings. |

No arbitrary stop sweep, solver combination search, motor-cap search, capture
retiming or repeated historical qualification is authorized by this plan. N2
and N3 receive distinct diagnostic backend identities and exact settings hashes.
N1 remains an admitted source variant of the original backend. N0 must match
the retained original native samples before either candidate is interpreted.

## Bounds and decision

Each run retains the original explicit 1,000,000-operation and 80,000 ms ceilings,
4,800 scheduled native substeps, 481 captures and original byte/object caps.
There are four fresh control builds and no automatic retry. Preserve every
failure, including harness failures. Any necessary correction must receive a
new attempt ID with a stated reason rather than overwrite an attempt.

For each control, measure peak vertex distance, carriage transverse and angular
residual, the contact-window trace, X/time preservation, left travel and right
lane equality. Retain original and actual source, constructor and settings
identities. The independent reviewer checks source/geometry and the unchanged
continuous playback gates separately.

Select a candidate only if the diagnostic result supports the original mapping
limit. Adopt its exact versioned backend decision before qualification. Then
qualify retained C191 A/B/C/D and both C192 witnesses with separately identified
fresh builds, saved-scene resimulation, collider-removal evidence and independent
checks. If neither bounded candidate works, publish the measured diagnosis and
precise remaining gate; do not combine or expand controls in this task.
