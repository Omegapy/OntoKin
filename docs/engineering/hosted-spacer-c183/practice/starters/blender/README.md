# Blender spacer

`build_spacer.py` builds one box at the origin. Its three dimensions use millimetres in glTF X, Y and Z order. The script converts them to metres and maps glTF Y to Blender Z before using Blender’s native glTF exporter.

From your copy of this starter, set `BLENDER` to the Blender executable and `OUT` to an absolute output directory for this export. Run:

```bash
"$BLENDER" -b -t 2 --factory-startup --python-exit-code 1 \
  --python build_spacer.py -- "$OUT"
```

Inspect `$OUT/spacer.glb` to measure the exported box. The Python script is the editable source.
