# OntoKin spacer

`main.ok` defines one box at the origin. Its three dimensions use millimetres in glTF X, Y and Z order. OntoKin’s core exporter converts the lengths to metres.

From your copy of this starter, set `JOB` to the absolute path of the restored OntoKin environment and `OUT` to an absolute output directory for this export. Run:

```bash
SOURCE="$PWD/main.ok"
mkdir -p "$OUT"
(cd "$JOB/checkout" && "$JOB/venv/bin/python" -B -m ontokin export "$SOURCE" \
  --no-helpers --fps 1 --output "$OUT/spacer.glb")
```

Inspect `$OUT/spacer.glb` to measure the exported box. The `.ok` file is the editable source.
