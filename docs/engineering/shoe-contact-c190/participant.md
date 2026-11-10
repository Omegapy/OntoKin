# C190 · Can contact at the shoe stop its carriage?

Use your native C189 design at 125 mm/s on the left and 150 mm/s on the right. The seven visible solids, initial poses, IDs and colors stay as drawn, except for the left stop. Move the left stop towards the shoe and make contact at the shoe halt the left carriage and its attached shoe. Both travel along X. The right lane continues through the full two seconds. Render each case from the same initial state.

The left shoe's leading face starts at X = 180 mm. Set the near face of the left stop to X = 380 mm for case A and 355 mm for case B. Keep the stop 30 mm thick. The right stop stays at X = 495 mm. With a 125 mm/s initial feed, ideal first contact occurs at 1.600 s and 1.400 s respectively. Use a fixed stop, frictionless guided translation and zero restitution, or document the closest supported native behavior. Give the second build only a change of stop location.

Make the causal chain inspectable. Identify the shape that collides, the part that owns its mass, the attachment, and how the solver responds to contact. A rigidly attached collision shape may belong to the carriage if it matches the visible shoe at the contact face. Keep each shoe fixed relative to its carriage. A timed animation or a position limit can illustrate the intended motion and must be identified as such. Collision credit requires solver evidence.

Deliver editable native sources, both raw and final GLBs, build commands, native diagnostics or contact records and a one-setting diff. If this profile cannot solve the contact, preserve a minimal reproducer and its exact diagnostic or observed pass-through. Report what the profile can represent separately from what it actually simulated.
