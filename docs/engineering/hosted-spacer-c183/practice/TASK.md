# Public practice • machine spacer

A shop needs a longer, deeper spacer. Your starter is a single rectangular solid centered on the origin. The exported glTF uses metres. In glTF world coordinates the starter measures 40 mm along X, 12 mm along Y and 20 mm along Z.

1. Inspect the editable design. Use the native tool for your route to export the starter. Measure the GLB using the supplied independent reader. Verify the starting dimensions and center.
2. Run the supplied reader against this starting GLB with the **target** dimensions. Keep the failed check in your log. A nonzero exit is expected at this point.
3. Edit the source so the spacer measures **50 × 12 × 24 mm** in glTF X, Y and Z. Keep a single centered solid. Leave the native export path in place.
4. Export again from the edited source. Inspect the resulting GLB with the same reader. Each dimension must be within 0.05 mm of its target, and each component of the center must be within 0.05 mm of zero.
5. Submit into the named submission directory. Include the full editable source needed to reproduce the export, the baseline and repaired GLBs under distinct filenames, and a short log of commands, return codes, actual measurements and any retries or help. Use relative paths or variable names in the log where practical. Send the coordinator the submission path and the actual dimensions.

Use the native coding tools in your session. Work only in your assigned working directory. You can read your assigned starter, runtime and the public measurement script. Use the same reader invocation before and after the edit:

```bash
python3 measure_glb.py FILE --expect-mm X Y Z
```

Completion requires files on disk and a message to the coordinator. Save the work you have if a step fails.
